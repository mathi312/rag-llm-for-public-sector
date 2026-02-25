from pathlib import Path

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from extensions.question_repository import QuestionRepository
from extensions.documentupload import extract_text_from_file
from extensions.question import Question
from models import get_llm


class PocketBaseSaveError(Exception):
    """Custom exception for failures when pocketbase failes to save a question."""

class PocketBaseNoQuestionsFound(Exception):
    """Custom exception for failures when pocketbase failes to retrive questions."""

class QuestionService:
    """
    Contains the logic for the question generation and interaction with the repository. 
    Generates example questions and returns 6 questions from pocketbase.
    """

    def __init__(self, repo: QuestionRepository):
        self.repo = repo


    def generate_example_questions(self, document_name: str, provider: str, model_name: str) -> list[str]:
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
                "You are a helpful assistant that generates high-quality user questions for a document."
                "Task: Given the document below, create exactly five concise, varied, and meaningful questions a user might ask about its content."
                "The following points are the Requirements:"
                "- Questions must be in the same language as the document"
                "- Questions must be fully answerable using only information in the document."
                "- Avoid vague, generic, or overly broad questions."
                "- Ensure diversity: include factual, analytical, and clarification-style questions."
                "- Cover different sections or themes of the document."
                "- Do not invent any information not in the document."
                "- Output exactly five questions, one per line."
                "- Do NOT include numbering, headers, or explanations."
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


    def save_questions(self, questions: list[str]) -> bool:
        """
        Saves the provided questions to pocketbase.
        """
        if not questions:
            raise ValueError("The questions list cannot be empty or None.")

        try:
            for q in questions:
                clean_q = q.strip()
                # Skip empty strings or whitespace
                if not q or not clean_q:
                    continue

                # Skip duplicates
                if self.repo.exists_by_text(clean_q):
                    continue

                self.repo.create_question(clean_q)

            return True
        except Exception as e:
            raise PocketBaseSaveError(f"Failed to save questions due to: {e}") from e


    def get_questions(self, random_only: bool = False) -> list[Question]:
        """
        Get 6 example questions from PocketBase.

        If random_only is True:
            → return 6 random questions.

        Otherwise:
            → return 4 most asked + 2 random (excluding the top ones).
        """
        try:
            total = 6

            # Fully random mode
            if random_only:
                questions = self.repo.get_random_questions(
                    exclude=[],
                    num_of_questions=total,
                )

                if not questions:
                    raise ValueError(
                        "No questions found in PocketBase. Please create some questions."
                    )

                return questions

            # Mixed mode (default)
            most_asked = self.repo.get_most_asked_question_from_pb()

            if not most_asked:
                raise ValueError(
                    "No questions found in PocketBase. Please create some questions."
                )

            remaining = total - len(most_asked)

            random_questions = self.repo.get_random_questions(
                exclude=most_asked,
                num_of_questions=remaining,
            )

            return most_asked + random_questions
        except ValueError as e:
            raise PocketBaseNoQuestionsFound(f"Failed to retrieve questions: {e}")

    def increment_times_asked(self, question_id: str) -> bool:
        """
        Saves the provided questions to pocketbase.
        """
        if not question_id:
            raise ValueError("The id cannot be empty")

        try:
            self.repo.increment_times_asked(question_id)
            return True
        except Exception as e:
            raise PocketBaseSaveError(f"Failed to update the question: {question_id} due to: {e}") from e
