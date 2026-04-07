import pytest
from unittest.mock import MagicMock, patch
import os

from infrastructure.pocketbase import get_pocketbase_client

MODULE = "infrastructure.pocketbase.pocketbase_client"


@pytest.fixture(autouse=True)
def reset_pb_client():
    """Reset the singleton before each test to ensure isolation."""
    with patch(f"{MODULE}._pb_client", None):
        yield


@pytest.fixture
def mock_pocketbase_class():
    with patch(f"{MODULE}.PocketBase") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        yield mock_cls, mock_instance


def test_creates_client_on_first_call(mock_pocketbase_class):
    mock_cls, mock_instance = mock_pocketbase_class
    mock_instance.auth_store.token = "valid-token"

    with patch.dict(os.environ, {"POCKETBASE_URL": "http://127.0.0.1:8080"}):
        with patch(f"{MODULE}.PB_URL", "http://127.0.0.1:8080"):
            result = get_pocketbase_client()

    mock_cls.assert_called_once_with("http://127.0.0.1:8080")
    assert result is mock_instance


def test_reuses_existing_client_on_second_call(mock_pocketbase_class):
    _, mock_instance = mock_pocketbase_class
    mock_instance.auth_store.token = "valid-token"

    first = get_pocketbase_client()
    second = get_pocketbase_client()

    assert first is second


def test_authenticates_when_token_is_missing(mock_pocketbase_class):
    _, mock_instance = mock_pocketbase_class
    mock_instance.auth_store.token = None

    with patch.dict(os.environ, {
        "POCKETBASE_ADMIN_USERNAME": "admin",
        "POCKETBASE_ADMIN_PASSWORD": "secret",
    }):
        get_pocketbase_client()

    mock_instance.admins.auth_with_password.assert_called_once_with("admin", "secret")


def test_authenticates_when_token_is_empty_string(mock_pocketbase_class):
    _, mock_instance = mock_pocketbase_class
    mock_instance.auth_store.token = ""  # Empty string is also falsy

    with patch.dict(os.environ, {
        "POCKETBASE_ADMIN_USERNAME": "admin",
        "POCKETBASE_ADMIN_PASSWORD": "secret",
    }):
        get_pocketbase_client()

    mock_instance.admins.auth_with_password.assert_called_once_with("admin", "secret")


def test_skips_auth_when_token_is_present(mock_pocketbase_class):
    _, mock_instance = mock_pocketbase_class
    mock_instance.auth_store.token = "still-valid-token"

    get_pocketbase_client()

    mock_instance.admins.auth_with_password.assert_not_called()


def test_uses_custom_pocketbase_url_from_env(mock_pocketbase_class):
    mock_cls, mock_instance = mock_pocketbase_class
    mock_instance.auth_store.token = "valid-token"

    with patch.dict(os.environ, {"POCKETBASE_URL": "http://custom-host:9090"}):
        with patch(f"{MODULE}.PB_URL", "http://custom-host:9090"):
            get_pocketbase_client()

    mock_cls.assert_called_once_with("http://custom-host:9090")


def test_returns_pocketbase_client_instance(mock_pocketbase_class):
    _, mock_instance = mock_pocketbase_class
    mock_instance.auth_store.token = "valid-token"

    result = get_pocketbase_client()

    assert result is mock_instance
