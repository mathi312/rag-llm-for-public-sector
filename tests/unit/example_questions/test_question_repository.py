import pytest
from unittest.mock import MagicMock, patch

from extensions.example_questions.question import Question
from extensions.example_questions.question_repository import QuestionRepository
from extensions.example_questions.exceptions import (
    QuestionCreateError,
    QuestionFetchError,
    QuestionUpdateError
)

def make_pb_record(id: str, question: str) -> MagicMock:
    record = MagicMock()
    record.id = id
    record.question = question
    return record


def make_pb_list(*records) -> MagicMock:
    result = MagicMock()
    result.items = list(records)
    return result


@pytest.fixture(autouse=True)
def reset_client():
    """Patch CLIENT before every test."""
    with patch("extensions.example_questions.question_repository.CLIENT") as mock:
        yield mock


@pytest.fixture
def repo():
    return QuestionRepository()


class TestGetMostAskedQuestionFromPb:
    """
    Tests for get_most_asked_question_from_pb
    """

    def test_returns_default_four_questions(self, reset_client, repo):
        records = [make_pb_record(str(i), f"Q{i}") for i in range(4)]
        reset_client.collection.return_value.get_list.return_value = make_pb_list(*records)

        result = repo.get_most_asked_question_from_pb()

        assert len(result) == 4
        assert all(isinstance(q, Question) for q in result)

    def test_returns_custom_number_of_questions(self, reset_client, repo):
        records = [make_pb_record(str(i), f"Q{i}") for i in range(2)]
        reset_client.collection.return_value.get_list.return_value = make_pb_list(*records)

        result = repo.get_most_asked_question_from_pb(num_of_questions=2)

        assert len(result) == 2

    def test_passes_correct_sort_param(self, reset_client, repo):
        reset_client.collection.return_value.get_list.return_value = make_pb_list()

        repo.get_most_asked_question_from_pb(num_of_questions=3)

        reset_client.collection.return_value.get_list.assert_called_once_with(
            page=1,
            per_page=3,
            query_params={"sort": "-times_asked"},
        )

    def test_maps_records_to_question_objects(self, reset_client, repo):
        record = make_pb_record("123124", "This is a question")
        reset_client.collection.return_value.get_list.return_value = make_pb_list(record)

        result = repo.get_most_asked_question_from_pb(num_of_questions=1)

        assert result[0].id == "123124"
        assert result[0].question == "This is a question"

    def test_returns_empty_list_when_no_records(self, reset_client, repo):
        reset_client.collection.return_value.get_list.return_value = make_pb_list()

        assert repo.get_most_asked_question_from_pb() == []

    def test_raises_question_fetch_error_on_exception(self, reset_client, repo):
        reset_client.collection.return_value.get_list.side_effect = RuntimeError("DB down")

        with pytest.raises(QuestionFetchError, match="Failed to fetch top 4 most asked questions"):
            repo.get_most_asked_question_from_pb()

    def test_raises_with_custom_count_in_message(self, reset_client, repo):
        reset_client.collection.return_value.get_list.side_effect = RuntimeError("DB down")

        with pytest.raises(QuestionFetchError, match="Failed to fetch top 7 most asked questions"):
            repo.get_most_asked_question_from_pb(num_of_questions=7)


class TestGetRandomQuestions:
    """
    Tests for get_random_questions
    """

    def test_returns_default_six_questions(self, reset_client, repo):
        records = [make_pb_record(str(i), f"Q{i}") for i in range(6)]
        reset_client.collection.return_value.get_list.return_value = make_pb_list(*records)

        assert len(repo.get_random_questions(exclude=[])) == 6

    def test_custom_num_of_questions(self, reset_client, repo):
        records = [make_pb_record(str(i), f"Q{i}") for i in range(3)]
        reset_client.collection.return_value.get_list.return_value = make_pb_list(*records)

        assert len(repo.get_random_questions(exclude=[], num_of_questions=3)) == 3

    def test_exclude_ids_appear_in_filter(self, reset_client, repo):
        reset_client.collection.return_value.get_list.return_value = make_pb_list()
        excluded = [Question("id1", "Q1"), Question("id2", "Q2")]

        repo.get_random_questions(exclude=excluded)

        filter_str = (
            reset_client.collection.return_value.get_list
            .call_args.kwargs["query_params"]["filter"]
        )
        assert 'id != "id1"' in filter_str
        assert 'id != "id2"' in filter_str

    def test_empty_exclude_produces_empty_filter(self, reset_client, repo):
        reset_client.collection.return_value.get_list.return_value = make_pb_list()

        repo.get_random_questions(exclude=[])

        filter_str = (
            reset_client.collection.return_value.get_list
            .call_args.kwargs["query_params"]["filter"]
        )
        assert filter_str == ""

    def test_sort_param_is_random(self, reset_client, repo):
        reset_client.collection.return_value.get_list.return_value = make_pb_list()

        repo.get_random_questions(exclude=[])

        sort = (
            reset_client.collection.return_value.get_list
            .call_args.kwargs["query_params"]["sort"]
        )
        assert sort == "@random"

    def test_maps_records_to_question_objects(self, reset_client, repo):
        record = make_pb_record("xyz", "Random question?")
        reset_client.collection.return_value.get_list.return_value = make_pb_list(record)

        result = repo.get_random_questions(exclude=[])

        assert result[0].id == "xyz"
        assert result[0].question == "Random question?"

    def test_raises_question_fetch_error_on_exception(self, reset_client, repo):
        reset_client.collection.return_value.get_list.side_effect = RuntimeError("timeout")

        with pytest.raises(QuestionFetchError, match="Failed to fetch 6 random questions"):
            repo.get_random_questions(exclude=[])


class TestExistsByText:
    """
    Tests for exists_by_text
    """

    def test_returns_true_when_record_found(self, reset_client, repo):
        reset_client.collection.return_value.get_first_list_item.return_value = MagicMock()

        assert repo.exists_by_text("This is a question") is True

    def test_returns_false_on_404_error(self, reset_client, repo):
        reset_client.collection.return_value.get_first_list_item.side_effect = Exception("404 not found")

        assert repo.exists_by_text("Missing question") is False

    def test_returns_false_on_no_records_error(self, reset_client, repo):
        reset_client.collection.return_value.get_first_list_item.side_effect = Exception("no records found")

        assert repo.exists_by_text("Missing question") is False

    def test_returns_false_on_not_found_error(self, reset_client, repo):
        reset_client.collection.return_value.get_first_list_item.side_effect = Exception("record not found")

        assert repo.exists_by_text("Missing question") is False

    def test_raises_on_unexpected_exception(self, reset_client, repo):
        reset_client.collection.return_value.get_first_list_item.side_effect = RuntimeError("connection refused")

        with pytest.raises(QuestionFetchError, match="Failed to check existence"):
            repo.exists_by_text("Some question?")

    def test_query_uses_correct_text(self, reset_client, repo):
        reset_client.collection.return_value.get_first_list_item.return_value = MagicMock()

        repo.exists_by_text("Is TDD worth it?")

        reset_client.collection.return_value.get_first_list_item.assert_called_once_with(
            'question = "Is TDD worth it?"'
        )

class TestCreateQuestion:
    """
    Tests for create_question.
    """

    def test_calls_create_with_correct_payload(self, reset_client, repo):
        repo.create_question("What is a question?")

        reset_client.collection.return_value.create.assert_called_once_with(
            {"question": "What is a question?", "times_asked": 0}
        )

    def test_times_asked_initialised_to_zero(self, reset_client, repo):
        repo.create_question("Any question?")

        payload = reset_client.collection.return_value.create.call_args[0][0]
        assert payload["times_asked"] == 0

    def test_returns_none_on_success(self, reset_client, repo):
        assert repo.create_question("New question") is None

    def test_raises_question_create_error_on_exception(self, reset_client, repo):
        reset_client.collection.return_value.create.side_effect = RuntimeError("write failed")

        with pytest.raises(QuestionCreateError, match='Failed to create question: "New question"'):
            repo.create_question("New question")

class TestIncrementTimesAsked:
    """
    Tests for increment_times_asked.
    """

    def test_calls_update_with_correct_arguments(self, reset_client, repo):
        repo.increment_times_asked("q123")

        reset_client.collection.return_value.update.assert_called_once_with(
            "q123", {"times_asked+": 1}
        )

    def test_increment_value_is_one(self, reset_client, repo):
        repo.increment_times_asked("q42")

        payload = reset_client.collection.return_value.update.call_args[0][1]
        assert payload["times_asked+"] == 1

    def test_returns_none_on_success(self, reset_client, repo):
        assert repo.increment_times_asked("q123") is None

    def test_raises_question_update_error_on_exception(self, reset_client, repo):
        reset_client.collection.return_value.update.side_effect = RuntimeError("update failed")

        with pytest.raises(QuestionUpdateError, match="Failed to increment times_asked for question ID: q123"):
            repo.increment_times_asked("q123")
