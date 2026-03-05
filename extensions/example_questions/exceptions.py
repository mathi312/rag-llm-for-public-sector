
class QuestionRepositoryError(Exception):
    """Base exception for QuestionRepository errors."""


class QuestionFetchError(QuestionRepositoryError):
    """Raised when fetching questions from PocketBase fails."""


class QuestionCreateError(QuestionRepositoryError):
    """Raised when creating a question in PocketBase fails."""


class QuestionUpdateError(QuestionRepositoryError):
    """Raised when updating a question in PocketBase fails."""
