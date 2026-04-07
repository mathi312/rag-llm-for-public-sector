import pytest

from unittest.mock import MagicMock, patch
from pathlib import Path

from domain.predefined_questions.question import Question
from domain.predefined_questions.exceptions import (
    QuestionCreateError,
    QuestionFetchError,
    QuestionUpdateError
)
from application.predefined_questions.question_service import QuestionService


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def service(mock_repo):
    return QuestionService(repo=mock_repo)


def make_questions(n: int, prefix: str = "q") -> list[Question]:
    return [Question(id=f"{prefix}{i}", question=f"Question {i}?") for i in range(n)]


class TestGenerateExampleQuestions:

    def test_raises_value_error_if_document_name_is_empty(self, service):
        with pytest.raises(ValueError, match="document_name, provider and model_name must all be provided"):
            service.generate_example_questions("", "Local (Ollama)", "llama3.2")

    def test_raises_value_error_if_provider_is_empty(self, service):
        with pytest.raises(ValueError):
            service.generate_example_questions("doc.pdf", "", "llama3.2")

    def test_raises_value_error_if_model_name_is_empty(self, service):
        with pytest.raises(ValueError):
            service.generate_example_questions("doc.pdf", "Local (Ollama)", "")

    def test_raises_value_error_if_all_args_are_none(self, service):
        with pytest.raises(ValueError):
            service.generate_example_questions(None, None, None)

    @patch("application.predefined_questions.question_service.DATA_DIR", new=Path("/nonexistent_dir"))
    def test_raises_file_not_found_if_document_missing(self, service):
        with pytest.raises(FileNotFoundError, match="document not found"):
            service.generate_example_questions("nonexistent.pdf", "Local (Ollama)", "llama3.2")

    @patch("application.predefined_questions.question_service.DATA_DIR", new=Path("/fake_dir"))
    @patch("application.predefined_questions.question_service.LLMChain")
    @patch("application.predefined_questions.question_service.get_llm")
    @patch("application.predefined_questions.question_service.extract_text_from_file", return_value="document text")
    @patch("application.predefined_questions.question_service.Path.exists", return_value=True)
    def test_raises_runtime_error_if_llm_invocation_fails(self, mock_exists, mock_extract, mock_get_llm, mock_llm_chain, service):
        mock_chain = MagicMock()
        mock_chain.run.side_effect = RuntimeError("API error")
        mock_llm_chain.return_value = mock_chain

        with pytest.raises(RuntimeError, match="LLM invocation failed"):
            service.generate_example_questions("doc.pdf", "Local (Ollama)", "llama3.2")

    @patch("application.predefined_questions.question_service.DATA_DIR", new=Path("/fake_dir"))
    @patch("application.predefined_questions.question_service.LLMChain")
    @patch("application.predefined_questions.question_service.get_llm")
    @patch("application.predefined_questions.question_service.extract_text_from_file", return_value="text")
    @patch("application.predefined_questions.question_service.Path.exists", return_value=True)
    def test_returns_list_of_questions_from_llm_output(self, mock_exists, mock_extract, mock_get_llm, mock_llm_chain, service):
        mock_chain = MagicMock()
        mock_chain.run.return_value = "Q1?\nQ2?\nQ3?\nQ4?\nQ5?\n"
        mock_llm_chain.return_value = mock_chain

        result = service.generate_example_questions("doc.pdf", "Local (Ollama)", "llama3.2")

        assert result == ["Q1?", "Q2?", "Q3?", "Q4?", "Q5?"]


    @patch("application.predefined_questions.question_service.DATA_DIR", new=Path("/fake_dir"))
    @patch("application.predefined_questions.question_service.LLMChain")
    @patch("application.predefined_questions.question_service.get_llm")
    @patch("application.predefined_questions.question_service.extract_text_from_file", return_value="text")
    @patch("application.predefined_questions.question_service.Path.exists", return_value=True)
    def test_passes_provider_and_model_to_get_llm(self, mock_exists, mock_extract, mock_get_llm, mock_llm_chain, service):
        mock_chain = MagicMock()
        mock_chain.run.return_value = "Q1?"
        mock_llm_chain.return_value = mock_chain

        service.generate_example_questions("doc.pdf", "Local (Ollama)", "llama3.2")

        mock_get_llm.assert_called_once_with(provider="Local (Ollama)", model_name="llama3.2")


class TestSaveQuestions:
    """
    Tests for save_questions.
    """

    def test_raises_value_error_for_empty_list(self, service):
        with pytest.raises(ValueError, match="cannot be empty or None"):
            service.save_questions([])

    def test_raises_value_error_for_none(self, service):
        with pytest.raises(ValueError):
            service.save_questions(None)

    def test_saves_new_questions(self, service, mock_repo):
        mock_repo.exists_by_text.return_value = False

        service.save_questions(["Q1?", "Q2?"])

        assert mock_repo.create_question.call_count == 2
        mock_repo.create_question.assert_any_call("Q1?")
        mock_repo.create_question.assert_any_call("Q2?")

    def test_skips_duplicate_questions(self, service, mock_repo):
        mock_repo.exists_by_text.side_effect = lambda q: q == "Q1?"

        service.save_questions(["Q1?", "Q2?"])

        mock_repo.create_question.assert_called_once_with("Q2?")

    def test_skips_empty_strings(self, service, mock_repo):
        mock_repo.exists_by_text.return_value = False

        service.save_questions(["Q1?", "", "   "])

        mock_repo.create_question.assert_called_once_with("Q1?")

    def test_strips_whitespace_before_saving(self, service, mock_repo):
        mock_repo.exists_by_text.return_value = False

        service.save_questions(["  Q1?  "])

        mock_repo.create_question.assert_called_once_with("Q1?")

    def test_strips_whitespace_before_duplicate_check(self, service, mock_repo):
        mock_repo.exists_by_text.return_value = True

        service.save_questions(["  Q1?  "])

        mock_repo.exists_by_text.assert_called_once_with("Q1?")
        mock_repo.create_question.assert_not_called()

    def test_returns_true_on_success(self, service, mock_repo):
        mock_repo.exists_by_text.return_value = False

        assert service.save_questions(["Q1?"]) is True

    def test_propagates_question_fetch_error(self, service, mock_repo):
        mock_repo.exists_by_text.side_effect = QuestionFetchError("PB error")

        with pytest.raises(QuestionFetchError):
            service.save_questions(["Q1?"])

    def test_propagates_question_create_error(self, service, mock_repo):
        mock_repo.exists_by_text.return_value = False
        mock_repo.create_question.side_effect = QuestionCreateError("write failed")

        with pytest.raises(QuestionCreateError):
            service.save_questions(["Q1?"])

    def test_all_duplicates_saves_nothing(self, service, mock_repo):
        mock_repo.exists_by_text.return_value = True

        service.save_questions(["Q1?", "Q2?"])

        mock_repo.create_question.assert_not_called()

class TestGetQuestions:
    """
    Tests for get_questions.
    """

    def test_random_only_returns_six_random_questions(self, service, mock_repo):
        questions = make_questions(6)
        mock_repo.get_random_questions.return_value = questions

        result = service.get_questions(random_only=True)

        assert result == questions
        mock_repo.get_random_questions.assert_called_once_with(exclude=[], num_of_questions=6)

    def test_random_only_raises_value_error_when_empty(self, service, mock_repo):
        mock_repo.get_random_questions.return_value = []

        with pytest.raises(ValueError, match="No questions found in PocketBase"):
            service.get_questions(random_only=True)

    def test_random_only_does_not_call_most_asked(self, service, mock_repo):
        mock_repo.get_random_questions.return_value = make_questions(6)

        service.get_questions(random_only=True)

        mock_repo.get_most_asked_question_from_pb.assert_not_called()

    def test_mixed_mode_returns_four_most_asked_plus_two_random(self, service, mock_repo):
        most_asked = make_questions(4, prefix="top")
        random_qs = make_questions(2, prefix="rnd")
        mock_repo.get_most_asked_question_from_pb.return_value = most_asked
        mock_repo.get_random_questions.return_value = random_qs

        result = service.get_questions()

        assert result == most_asked + random_qs
        assert len(result) == 6

    def test_mixed_mode_passes_most_asked_as_exclude(self, service, mock_repo):
        most_asked = make_questions(4, prefix="top")
        mock_repo.get_most_asked_question_from_pb.return_value = most_asked
        mock_repo.get_random_questions.return_value = make_questions(2, prefix="rnd")

        service.get_questions()

        mock_repo.get_random_questions.assert_called_once_with(
            exclude=most_asked, num_of_questions=2
        )

    def test_mixed_mode_raises_value_error_when_no_most_asked(self, service, mock_repo):
        mock_repo.get_most_asked_question_from_pb.return_value = []

        with pytest.raises(ValueError, match="No questions found in PocketBase"):
            service.get_questions()

    def test_mixed_mode_default_is_not_random_only(self, service, mock_repo):
        mock_repo.get_most_asked_question_from_pb.return_value = make_questions(4)
        mock_repo.get_random_questions.return_value = make_questions(2)

        service.get_questions()

        mock_repo.get_most_asked_question_from_pb.assert_called_once()

    def test_mixed_mode_remaining_count_adjusts_to_most_asked(self, service, mock_repo):
        """If fewer than 4 most-asked are returned, remaining random count increases."""
        most_asked = make_questions(2, prefix="top")
        mock_repo.get_most_asked_question_from_pb.return_value = most_asked
        mock_repo.get_random_questions.return_value = make_questions(4, prefix="rnd")

        service.get_questions()

        mock_repo.get_random_questions.assert_called_once_with(
            exclude=most_asked, num_of_questions=4
        )

    def test_mixed_mode_propagates_question_fetch_error(self, service, mock_repo):
        mock_repo.get_most_asked_question_from_pb.side_effect = QuestionFetchError("DB error")

        with pytest.raises(QuestionFetchError):
            service.get_questions()

    def test_random_only_propagates_question_fetch_error(self, service, mock_repo):
        mock_repo.get_random_questions.side_effect = QuestionFetchError("DB error")

        with pytest.raises(QuestionFetchError):
            service.get_questions(random_only=True)

class TestIncrementTimesAsked:
    """
    Tests for increment_times_asked.
    """

    def test_raises_value_error_for_empty_id(self, service):
        with pytest.raises(ValueError, match="id cannot be empty"):
            service.increment_times_asked("")

    def test_raises_value_error_for_none_id(self, service):
        with pytest.raises(ValueError):
            service.increment_times_asked(None)

    def test_delegates_to_repo(self, service, mock_repo):
        service.increment_times_asked("q123")

        mock_repo.increment_times_asked.assert_called_once_with("q123")

    def test_returns_true_on_success(self, service, mock_repo):
        assert service.increment_times_asked("q123") is True

    def test_propagates_question_update_error(self, service, mock_repo):
        mock_repo.increment_times_asked.side_effect = QuestionUpdateError("update failed")

        with pytest.raises(QuestionUpdateError):
            service.increment_times_asked("q123")
