import pytest
from types import SimpleNamespace

from domain.user.user import User

def test_user_init_is_admin_normalization():
    user1 = User(id="1", email="a@test.com", is_admin=True)
    user2 = User(id="2", email="b@test.com", is_admin=False)
    user3 = User(id="3", email="c@test.com", is_admin=None)

    assert user1.is_admin is True
    assert user2.is_admin is False
    assert user3.is_admin is False

def test_user_init_fields():
    user = User(
        id="123",
        email="test@example.com",
        name="Alice",
        is_admin=True,
    )

    assert user.id == "123"
    assert user.email == "test@example.com"
    assert user.name == "Alice"
    assert user.is_admin is True

def test_user_from_pb_record_full():
    record = SimpleNamespace(
        id="abc",
        email="user@test.com",
        name="Bob",
        admin=True,
    )

    user = User.from_pb_record(record)

    assert user.id == "abc"
    assert user.email == "user@test.com"
    assert user.name == "Bob"
    assert user.is_admin is True

def test_user_from_pb_record_missing_optional_fields():
    record = SimpleNamespace(
        id="abc",
        email="user@test.com",
    )

    user = User.from_pb_record(record)

    assert user.name is None
    assert user.is_admin is False
