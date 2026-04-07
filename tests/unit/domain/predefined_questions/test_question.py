import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace

from domain.predefined_questions.question import Question


def test_creates_instance_with_correct_fields():
    q = Question(id="123", question="What is Python?")

    assert q.id == "123"
    assert q.question == "What is Python?"


def test_quesion_from_pb_record():
    record = SimpleNamespace(
        id="abc",
        question="This is a test question",
    )

    question = Question.from_pb_record(record)

    assert question.id == "abc"
    assert question.question == "This is a test question"


def test_returns_question_instance():
    record = SimpleNamespace(
        id="abc",
        question="What is Python?"
    )

    result = Question.from_pb_record(record)

    assert isinstance(result, Question)


def test_question_none_when_attribute_missing():
    record = MagicMock(spec=["id"])
    record.id = "x"

    result = Question.from_pb_record(record)

    assert result.question is None
