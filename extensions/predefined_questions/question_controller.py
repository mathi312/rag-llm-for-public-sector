from extensions.predefined_questions.question_repository import QuestionRepository
from extensions.predefined_questions.question_service import QuestionService
from extensions.predefined_questions.question import Question
from extensions.predefined_questions.exceptions import (
    QuestionFetchError,
    QuestionCreateError,
    QuestionUpdateError,
)
from extensions.logger import Logger
from extensions.pocketbase.pocketbase_client import get_pocketbase_client

logger = Logger()

client = get_pocketbase_client()
repo = QuestionRepository(client=client)
service = QuestionService(repo)


def get_questions(random: bool = False) -> list[Question]:
    """
    Api to retrieve the saved questions.

    If random is True: return 6 random questions.

    Otherwise: return 4 most asked + 2 random (excluding the top ones).
    """
    try:
        return service.get_questions(random)
    except ValueError as e:
        logger.log_warning(f"No questions available: {e}")
        return []
    except QuestionFetchError as e:
        logger.log_error(f"Failed to retrieve questions: {e}")
        return []

def generate_questions(document_name: str, provider: str, model_name: str) -> list[str]:
    """
    Api to geneerate example questions for the provided document.
    """
    try:
        return service.generate_example_questions(document_name, provider, model_name)
    except (ValueError, FileNotFoundError) as e:
        logger.log_warning(f"Invalid input for question generation: {e}")
        return []
    except RuntimeError as e:
        logger.log_error(f"LLM invocation failed during question generation: {e}")
        return []

def save_questions(questions: list[str]) -> bool:
    """
    Api to save the provided questions.
    """
    try:
        return service.save_questions(questions)
    except ValueError as e:
        logger.log_warning(f"Invalid input for saving questions: {e}")
        return False
    except (QuestionFetchError, QuestionCreateError) as e:
        logger.log_error(f"Failed to save questions: {e}")
        return False

def update_times_asked_of_question(question_id: str) -> bool:
    """
    Api to update the number of times the question was asked.
    """
    try:
        return service.increment_times_asked(question_id)
    except ValueError as e:
        logger.log_warning(f"Invalid question ID provided: {e}")
        return False
    except QuestionUpdateError as e:
        logger.log_error(f"Failed to update times_asked for question {question_id}: {e}")
        return False
