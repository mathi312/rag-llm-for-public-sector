"""Question-answering chain construction and execution module.

This module defines the RAG pipeline, including the system prompt template
and answer generation logic.
""" 

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_core.language_models import BaseLanguageModel

SYSTEM_PROMPT = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer the question. "
    "If the answer is not in the context, say that you don't know. "
    "Keep the answer concise.\n\n{context}"
)

DOCUMENT_KEYWORDS = ["führungszeugnis", "dokument", "bescheinigung", "auszug", "urkunde"]

def needs_id_prompt(question: str, id_uploaded: bool) -> bool:
    """Detect if the user is requesting an official document and should show ID prompt."""
    q = question.lower()
    return any(keyword in q for keyword in DOCUMENT_KEYWORDS) and not id_uploaded

def create_rag_chain(vector_store: FAISS, llm: BaseLanguageModel):
    """Construct a retrieval-augmented generation chain."""
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{input}")
        ]
    )

    qa_chain = create_stuff_documents_chain(llm, prompt_template)
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 6, "score_threshold": 0.3}
    )
    rag_chain = create_retrieval_chain(retriever, qa_chain)
    
    return rag_chain


def answer_question(rag_chain, question: str, id_document: dict | None = None, id_uploaded: bool = False) -> str:
    """Execute the RAG chain with a user question and extract the answer."""
    if id_uploaded and id_document:
        question += (
            "\n\n[Citizen ID provided]\n"
            f"Type: {id_document.get('type')}\n"
            f"Data: {id_document.get('data')}"
        )


    result = rag_chain.invoke({"input": question})
    answer = result["answer"]

    if needs_id_prompt(question, id_uploaded):
        answer += (
            "\n\nZur weiteren Bearbeitung benötige ich eine Ausweisbestätigung. "
            "Bitte laden Sie Ihren Ausweis hoch, in dem Sie auf die Schaltfläche \"Ausweis hochladen\" klicken."
            f"{'' if id_uploaded else ' (Derzeit kein Ausweis hochgeladen)'}"
        )

    return answer
