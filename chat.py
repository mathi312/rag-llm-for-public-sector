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


def create_rag_chain(vector_store: FAISS, llm: BaseLanguageModel):
    """Construct a retrieval-augmented generation chain."""
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{input}")
        ]
    )

    qa_chain = create_stuff_documents_chain(llm, prompt_template)
    retriever = vector_store.as_retriever()
    rag_chain = create_retrieval_chain(retriever, qa_chain)
    
    return rag_chain


def answer_question(rag_chain, question: str) -> str:
    """Execute the RAG chain with a user question and extract the answer."""
    result = rag_chain.invoke({"input": question})
    return result["answer"]
