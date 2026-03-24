"""Question-answering chain construction and execution module.

This module defines the RAG pipeline, including the system prompt template
and answer generation logic.
"""

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_core.language_models import BaseLanguageModel

from extensions.report_generator.report import Report

SYSTEM_PROMPT = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer the question. "
    "If the answer is not in the context, say that you don't know. "
    "Keep the answer concise.\n\n{context}"
)

DOCUMENT_KEYWORDS = [
    "führungszeugnis",
    "dokument",
    "bescheinigung",
    "auszug",
    "urkunde",
]


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


def answer_question(
    rag_chain,
    question: str,
    id_document: dict | None = None,
    id_uploaded: bool = False,
    report: Report | None = None,
) -> str:
    """Execute the RAG chain with a user question and extract the answer."""
    retriever, qa_chain = rag_chain

    docs = retriever.invoke(question)
    augmented_question = question

    if id_uploaded and id_document:
        augmented_question += (
            "\n\n[Citizen ID provided]\n"
            f"Type: {id_document.get('type')}\n"
            f"Data: {id_document.get('data')}"
        )

    result = qa_chain.invoke({"input": augmented_question, "context": docs})
    answer = result.get("answer", result) if isinstance(result, dict) else result
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
