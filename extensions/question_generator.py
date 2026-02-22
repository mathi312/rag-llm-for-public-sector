from pathlib import Path
from typing import List
import os

from extensions.documentupload import extract_text_from_file
from models import get_llm

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from pocketbase import PocketBase


PB_URL = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8080")
CLIENT = PocketBase(PB_URL)

CLIENT.admins.auth_with_password(
    os.getenv("POCKETBASE_ADMIN_USERNAME"), os.getenv("POCKETBASE_ADMIN_PASSWORD")
)


class PocketBaseSaveError(Exception):
    """Custom exception for failures when communicating with PocketBase."""


def generate_example_questions(document_name: str, provider: str, model_name: str) -> List[str]:
    """
    Read the document from the data directory, hand its text to a LangChain LLM and
    return a list of example questions a user could ask about the document.
    """
    if not document_name or not provider or not model_name:
        raise ValueError("document_name, provider and model_name must all be provided")

    data_dir = Path(__file__).resolve().parent.parent / "data"
    file_path = data_dir / document_name

    if not file_path.exists():
        raise FileNotFoundError(f"document not found: {file_path}")

    text = extract_text_from_file(file_path)

    prompt_template = PromptTemplate(
        input_variables=["text"],
        template=(
            "You are a helpful assistant."
            "Given the following document content, come up with five concise, "
            "varied example questions a user might ask about it.  "
            "Return ONLY the questions, one per line. Do not include introductory text.\n\n"
            "Document:\n{text}"
        ),
    )

    llm = get_llm(provider=provider, model_name=model_name)
    chain = LLMChain(llm=llm, prompt=prompt_template)

    try:
        output = chain.run(text=text)
    except Exception as exc:
        raise RuntimeError("LLM invocation failed") from exc

    # split into a list of questions
    return [q.strip() for q in output.strip().splitlines() if q.strip()]


def save_questions_to_pb(questions: List[str]) -> bool:
    """
    Saves each question as a new record in the PocketBase 'questions' collection.
    """
    if not questions:
        raise ValueError("The questions list cannot be empty or None.")

    try:
        for q in questions:
            clean_q = q.strip()
            # Skip empty strings or whitespace
            if not q or not clean_q:
                continue

            try:
                existing = CLIENT.collection("questions").get_first_list_item(
                        f'question = "{clean_q}"'
                    )
                if existing:
                    # Question exists, skip to the next one
                    continue
            except Exception:
                # PocketBase throws an error (usually 404) if no item matches the filter.
                # This is what we want, it means it's safe to create.
                pass

            CLIENT.collection("questions").create(
                {
                    "question": q.strip(),
                    "times_asked": 0,
                }
            )
        return True

    except Exception as e:
        raise PocketBaseSaveError(f"Failed to save questions due to: {e}") from e
