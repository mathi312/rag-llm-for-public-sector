"""Question-answering chain construction and execution module.

This module defines the RAG pipeline, including the system prompt template
and answer generation logic.
"""

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_core.language_models import BaseLanguageModel

from extensions.report_generator.report import Report

from config import (
    NO_CONTEXT_ANSWER,
    RETRIEVAL_K,
    GATE_MIN_SCORE,
    GATE_RELATIVE_FACTOR,
    GATE_MAX_DOCS,
    GATE_MAX_DOCS_PER_SOURCE,
    SYSTEM_PROMPT,
    DOCUMENT_KEYWORDS,
)


def sources_require_id(sources) -> tuple[bool, list[str]]:
    """
    Check if any of the retrieved sources indicate that an ID document is needed, and collect the types of IDs required.
    If any ID is required, return True along with a list of unique ID types. Otherwise, return False and an empty list.
    """
    needed = set()
    for doc in sources or []:
        ids = doc.metadata.get("needed_id") if hasattr(doc, "metadata") else None
        if ids:
            for x in ids:
                needed.add(str(x))
    return (len(needed) > 0), sorted(needed)


def needs_id_prompt(question: str, id_uploaded: bool, sources=None) -> bool:
    """Detect if the user is requesting an official document and should show ID prompt."""
    if id_uploaded:
        return False

    requires_id, _ = sources_require_id(sources)
    if requires_id:
        return True

    # Fallback (optional)
    q = question.lower()
    return any(keyword in q for keyword in DOCUMENT_KEYWORDS)


def create_rag_chain(vector_store: FAISS, llm: BaseLanguageModel):
    """Construct a retrieval-augmented generation chain."""
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_PROMPT), ("human", "{input}")]
    )

    qa_chain = create_stuff_documents_chain(llm, prompt_template)
    retriever = vector_store.as_retriever(
        # MMR returns relevant and diverse chunks
        search_type="mmr",
        search_kwargs={"k": 6, "fetch_k": 24, "lambda_mult": 0.25},
    )

    return retriever, qa_chain


def _doc_source(doc) -> str:
    metadata = getattr(doc, "metadata", {}) or {}
    return str(metadata.get("source", "unknown"))


def _retrieve_scored_candidates(retriever, question: str):
    """Retrieve broad candidate set with relevance scores when possible."""
    vector_store = getattr(retriever, "vectorstore", None)
    if vector_store and hasattr(vector_store, "similarity_search_with_relevance_scores"):
        return vector_store.similarity_search_with_relevance_scores(question, k=RETRIEVAL_K)

    # Fallback for mock retrievers/custom implementations without score API.
    docs = retriever.invoke(question)
    return [(doc, 1.0) for doc in docs]


def _gate_context(candidates):
    """Filter irrelevant context and keep source-diverse documents."""
    if not candidates:
        return []

    ranked = sorted(candidates, key=lambda item: item[1], reverse=True)
    best_score = ranked[0][1]
    if best_score < GATE_MIN_SCORE:
        return []

    threshold = max(GATE_MIN_SCORE, best_score * GATE_RELATIVE_FACTOR)
    filtered = [(doc, score) for doc, score in ranked if score >= threshold]
    if not filtered:
        return []

    selected = []
    per_source = {}
    for doc, _ in filtered:
        source = _doc_source(doc)
        if per_source.get(source, 0) >= GATE_MAX_DOCS_PER_SOURCE:
            continue
        selected.append(doc)
        per_source[source] = per_source.get(source, 0) + 1
        if len(selected) >= GATE_MAX_DOCS:
            break

    return selected


def answer_question(
    rag_chain,
    question: str,
    id_document: dict | None = None,
    id_uploaded: bool = False,
    report: Report | None = None,
) -> str:
    """Execute the three-stage RAG flow and return answer plus used sources."""
    retriever, qa_chain = rag_chain

    candidates = _retrieve_scored_candidates(retriever, question)
    docs = _gate_context(candidates)

    # Only generate if context quality is sufficient.
    if not docs:
        answer = NO_CONTEXT_ANSWER
        if report is not None:
            report.add_entry(question, answer)
            if report.id_type is None:
                report.add_id_type(id_document.get("type") if id_uploaded and id_document else None)
        return answer, []

    augmented_question = question

    if id_uploaded and id_document:
        augmented_question += (
            "\n\n[Citizen ID provided]\n"
            f"Type: {id_document.get('type')}\n"
            f"Data: {id_document.get('data')}"
        )

    result = qa_chain.invoke({"input": augmented_question, "context": docs})
    answer = result.get("answer", result) if isinstance(result, dict) else result
    if not str(answer).strip():
        answer = NO_CONTEXT_ANSWER
    sources = docs

    if needs_id_prompt(question, id_uploaded, sources=docs):
        _, id_types = sources_require_id(docs)
        extra = f" Benötigte Ausweisarten: {', '.join(id_types)}." if id_types else ""
        answer += (
            "\n\nZur weiteren Bearbeitung benötige ich eine Ausweisbestätigung."
            f"{extra} Bitte laden Sie Ihren Ausweis hoch, in dem Sie auf die Schaltfläche "
            '"Ausweis hochladen" klicken.'
            f"{'' if id_uploaded else ' (Derzeit kein Ausweis hochgeladen)'}"
        )

    if report is not None:
        report.add_entry(question, answer)

        if report.id_type is None:
            report.add_id_type(id_document.get("type") if id_uploaded else None)

    return answer, sources
