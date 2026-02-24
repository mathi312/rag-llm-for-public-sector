from extensions.question_repository import QuestionRepository
from extensions.question_service import QuestionService
from extensions.question import Question


repo = QuestionRepository()
service = QuestionService(repo)

def get_questions(random: bool = False) -> list[Question]:
    """
    Api to retrieve the saved questions.

    If random is True: return 6 random questions.

    Otherwise: return 4 most asked + 2 random (excluding the top ones).
    """
    questions = service.get_questions(random)

    return questions

def generate_questions(document_name: str, provider: str, model_name: str) -> list[str]:
    """
    Api to geneerate example questions for the provided document.
    """
    questions = service.generate_example_questions(document_name, provider, model_name)

    return questions

def save_questions(questions: list[str]) -> bool:
    """
    Api to save the provided questions.
    """
    return service.save_questions(questions)

def update_times_asked_of_question(question_id: str) -> bool:
    """
    Api to update the number of times the question was asked.
    """
    return service.increment_times_asked(question_id)
