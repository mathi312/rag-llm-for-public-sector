import pytest
from unittest.mock import MagicMock, patch

from domain.predefined_questions.question import Question
from domain.predefined_questions.exceptions import (
    QuestionCreateError,
    QuestionFetchError,
    QuestionUpdateError
)
from application.predefined_questions import (
    get_questions,
    generate_questions,
    save_questions,
    update_times_asked_of_question
)


@pytest.fixture
def mock_service():
    with patch("application.predefined_questions.question_service_facade.service") as mock:
        yield mock


@pytest.fixture
def mock_logger():
    with patch("application.predefined_questions.question_service_facade.logger") as mock:
        yield mock


class TestGetQuestions:
    """
    Tests for get_questons.
    """

    def test_returns_questions_when_random_false(self, mock_service, mock_logger):
        questions = [Question("1", "Q1"), Question("2", "Q2")]
        mock_service.get_questions.return_value = questions

        result = get_questions(random=False)

        assert result == questions
        mock_service.get_questions.assert_called_once_with(False)

    def test_returns_questions_when_random_true(self, mock_service, mock_logger):
        questions = [Question("1", "Q1")]
        mock_service.get_questions.return_value = questions

        result = get_questions(random=True)

        assert result == questions
        mock_service.get_questions.assert_called_once_with(True)

    def test_default_random_is_false(self, mock_service, mock_logger):
        mock_service.get_questions.return_value = []

        get_questions()

        mock_service.get_questions.assert_called_once_with(False)

    def test_returns_empty_list_on_value_error(self, mock_service, mock_logger):
        mock_service.get_questions.side_effect = ValueError("no questions")

        result = get_questions()

        assert result == []

    def test_returns_empty_list_on_question_fetch_error(self, mock_service, mock_logger):
        mock_service.get_questions.side_effect = QuestionFetchError("db error")

        result = get_questions()

        assert result == []

    def test_logs_warning_on_value_error(self, mock_service, mock_logger):
        mock_service.get_questions.side_effect = ValueError("no questions")

        get_questions()

        mock_logger.log_warning.assert_called_once()
        assert "no questions" in mock_logger.log_warning.call_args[0][0]

    def test_logs_error_on_question_fetch_error(self, mock_service, mock_logger):
        mock_service.get_questions.side_effect = QuestionFetchError("db error")

        get_questions()

        mock_logger.log_error.assert_called_once()
        assert "db error" in mock_logger.log_error.call_args[0][0]


class TestGenerateQuestions:

    def test_returns_generated_questions_on_success(self, mock_service, mock_logger):
        mock_service.generate_example_questions.return_value = ["Q1?", "Q2?"]

        result = generate_questions("doc.pdf", "Local (Ollama)", "llama3.2")

        mock_service.generate_example_questions.assert_called_once_with(
            "doc.pdf", "Local (Ollama)", "llama3.2"
        )
        assert result == ["Q1?", "Q2?"]

    def test_returns_empty_list_on_value_error(self, mock_service, mock_logger):
        mock_service.generate_example_questions.side_effect = ValueError("bad input")

        assert generate_questions("doc.pdf", "Local (Ollama)", "llama3.2") == []

    def test_logs_warning_on_value_error(self, mock_service, mock_logger):
        mock_service.generate_example_questions.side_effect = ValueError("bad input")

        generate_questions("doc.pdf", "Local (Ollama)", "llama3.2")

        mock_logger.log_warning.assert_called_once()
        assert "bad input" in mock_logger.log_warning.call_args[0][0]

    def test_returns_empty_list_on_file_not_found_error(self, mock_service, mock_logger):
        mock_service.generate_example_questions.side_effect = FileNotFoundError("missing file")

        assert generate_questions("missing.pdf", "Local (Ollama)", "llama3.2") == []

    def test_logs_warning_on_file_not_found_error(self, mock_service, mock_logger):
        mock_service.generate_example_questions.side_effect = FileNotFoundError("missing file")

        generate_questions("missing.pdf", "Local (Ollama)", "llama3.2")

        mock_logger.log_warning.assert_called_once()
        assert "missing file" in mock_logger.log_warning.call_args[0][0]

    def test_returns_empty_list_on_runtime_error(self, mock_service, mock_logger):
        mock_service.generate_example_questions.side_effect = RuntimeError("LLM failed")

        assert generate_questions("doc.pdf", "Local (Ollama)", "llama3.2") == []

    def test_logs_error_on_runtime_error(self, mock_service, mock_logger):
        mock_service.generate_example_questions.side_effect = RuntimeError("LLM failed")

        generate_questions("doc.pdf", "Local (Ollama)", "llama3.2")

        mock_logger.log_error.assert_called_once()
        assert "LLM failed" in mock_logger.log_error.call_args[0][0]


class TestSaveQuestions:

    def test_returns_true_on_success(self, mock_service, mock_logger):
        mock_service.save_questions.return_value = True
        questions = ["Q1?", "Q2?"]

        save = save_questions(questions)

        mock_service.save_questions.assert_called_once_with(questions)
        assert save is True

    def test_returns_false_on_value_error(self, mock_service, mock_logger):
        mock_service.save_questions.side_effect = ValueError("empty list")

        assert save_questions([]) is False

    def test_logs_warning_on_value_error(self, mock_service, mock_logger):
        mock_service.save_questions.side_effect = ValueError("empty list")

        save_questions([])

        mock_logger.log_warning.assert_called_once()
        assert "empty list" in mock_logger.log_warning.call_args[0][0]

    def test_returns_false_on_question_fetch_error(self, mock_service, mock_logger):
        mock_service.save_questions.side_effect = QuestionFetchError("fetch failed")

        assert save_questions(["Q1?"]) is False

    def test_logs_error_on_question_fetch_error(self, mock_service, mock_logger):
        mock_service.save_questions.side_effect = QuestionFetchError("fetch failed")

        save_questions(["Q1?"])

        mock_logger.log_error.assert_called_once()
        assert "fetch failed" in mock_logger.log_error.call_args[0][0]

    def test_returns_false_on_question_create_error(self, mock_service, mock_logger):
        mock_service.save_questions.side_effect = QuestionCreateError("create failed")

        assert save_questions(["Q1?"]) is False

    def test_logs_error_on_question_create_error(self, mock_service, mock_logger):
        mock_service.save_questions.side_effect = QuestionCreateError("create failed")

        save_questions(["Q1?"])

        mock_logger.log_error.assert_called_once()
        assert "create failed" in mock_logger.log_error.call_args[0][0]

class TestUpdateTimesAskedOfQuestion:

    def test_returns_true_on_success(self, mock_service, mock_logger):
        mock_service.increment_times_asked.return_value = True

        updated = update_times_asked_of_question("q123")

        mock_service.increment_times_asked.assert_called_once_with("q123")
        assert updated is True

    def test_returns_false_on_value_error(self, mock_service, mock_logger):
        mock_service.increment_times_asked.side_effect = ValueError("invalid id")

        assert update_times_asked_of_question("") is False

    def test_logs_warning_on_value_error(self, mock_service, mock_logger):
        mock_service.increment_times_asked.side_effect = ValueError("invalid id")

        update_times_asked_of_question("")

        mock_logger.log_warning.assert_called_once()
        assert "invalid id" in mock_logger.log_warning.call_args[0][0]

    def test_returns_false_on_question_update_error(self, mock_service, mock_logger):
        mock_service.increment_times_asked.side_effect = QuestionUpdateError("update failed")

        assert update_times_asked_of_question("q123") is False

    def test_logs_error_on_question_update_error(self, mock_service, mock_logger):
        mock_service.increment_times_asked.side_effect = QuestionUpdateError("update failed")

        update_times_asked_of_question("q123")

        mock_logger.log_error.assert_called_once()
        assert "q123" in mock_logger.log_error.call_args[0][0]
