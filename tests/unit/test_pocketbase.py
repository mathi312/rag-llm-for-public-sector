import pytest

from extensions import pocketbase as pb
from extensions.pocketbase import pocketbase_browser_session


"""
These are Unit-Tests with pytest under usage of Mocks/Stubs for PocketBase and Streamlit implementation.
"""

class MockAuthStore:
    """A mock authentication store for testing purposes."""
    def __init__(self):
        self.token = ""
        self.model = None
        self.cleared = False
        self.saved = []

    def save(self, token, model):
        self.token = token
        self.model = model
        self.saved.append((token, model))

    def clear(self):
        self.token = ""
        self.model = None
        self.cleared = True


class MockCollection:
    """A mock collection to simulate PocketBase collection behavior."""
    def __init__(self, auth_with_password):
        self._auth_with_password = auth_with_password

    def auth_with_password(self, email, password):
        return self._auth_with_password(email, password)


class MockClient:
    """A mock PocketBase client for testing purposes."""
    def __init__(self, collection_obj=None):
        self.auth_store = MockAuthStore()
        self._collection_obj = collection_obj or MockCollection(
            lambda email, password: {"token": "ok"}
        )

    def collection(self, name):
        assert name == "users"
        return self._collection_obj


class StubStreamlit:
    """A stub for the Streamlit module to capture session state and messages."""
    def __init__(self):
        self.session_state = {}
        self.success_calls = []
        self.warning_calls = []
        self.text_calls = []

    def success(self, msg):
        self.success_calls.append(msg)

    def warning(self, msg):
        self.warning_calls.append(msg)

    def text(self, msg):
        self.text_calls.append(msg)


class DummyRecord:
    """Simple object that mimics a PocketBase record."""

    def __init__(self, id="1", email="user@example.org", name="Max", admin=False):
        self.id = id
        self.email = email
        self.name = name
        self.admin = admin


@pytest.fixture(autouse=True)
def browser_auth_stub(monkeypatch):
    browser_auth = {"value": None, "clear_marked": False, "restore_blocked": False}

    class FakeBrowserSession:
        def __init__(self, streamlit_module):
            self.streamlit_module = streamlit_module

        def load_auth(self):
            return browser_auth["value"]

        def mark_for_clear(self):
            browser_auth["clear_marked"] = True
            browser_auth["restore_blocked"] = True

        def clear_pending(self):
            return browser_auth["clear_marked"]

        def flush_clear(self):
            browser_auth["clear_marked"] = False

        def restore_blocked(self):
            return browser_auth["restore_blocked"]

        def unblock_restore(self):
            browser_auth["restore_blocked"] = False

        def sync_auth(self, auth_data):
            browser_auth["synced"] = auth_data

    monkeypatch.setattr(pb, "PocketBaseBrowserSession", FakeBrowserSession)
    return browser_auth


@pytest.fixture
def mock_client(monkeypatch):
    client = MockClient()
    monkeypatch.setattr(pb, "client", client) # Inject the mock client into the pocketbase module
    return client


@pytest.fixture
def stub_st(monkeypatch):
    stub = StubStreamlit()
    monkeypatch.setattr(pb, "st", stub) # Inject the stub Streamlit into the pocketbase module
    return stub


def test_restore_session_no_auth(mock_client, stub_st, browser_auth_stub):
    """Test restoring session when no auth data is present."""
    pb.restore_session()
    assert mock_client.auth_store.token == ""
    assert mock_client.auth_store.model is None
    assert "pb_auth" not in stub_st.session_state


def test_restore_session_with_valid_data(mock_client, stub_st):
    """Test restoring session with valid auth data."""
    record = DummyRecord()
    stub_st.session_state["pb_auth"] = {"token": "t123", "model": record}
    pb.restore_session()
    assert "user" in stub_st.session_state
    assert stub_st.session_state["user"].email == "user@example.org"


def test_restore_session_from_cookies(mock_client, stub_st, browser_auth_stub):
    """Test restoring session from browser cookies after a reload."""
    browser_auth_stub["value"] = {
        "token": "t123",
        "model": {"id": "1", "email": "user@example.org", "name": "Max", "admin": False},
    }
    pb.restore_session()
    assert stub_st.session_state["pb_auth"] == {
        "token": "t123",
        "model": {"id": "1", "email": "user@example.org", "name": "Max", "admin": False},
    }
    assert stub_st.session_state["user"].email == "user@example.org"
    assert browser_auth_stub["clear_marked"] is False


def test_restore_session_with_invalid_data(stub_st):
    """Test restoring session with invalid auth data."""
    stub_st.session_state["pb_auth"] = {"token": "bad", "model": {}}  # Invalid data
    pb.restore_session()
    assert "pb_auth" not in stub_st.session_state
    assert "user" not in stub_st.session_state


def test_authenticate_user_success(monkeypatch, mock_client, stub_st, browser_auth_stub):
    """Test successful user authentication."""
    record = DummyRecord()
    data = type("AuthResult", (), {"token": "abc", "record": record})()
    collection = MockCollection(lambda e, p: data)
    mock_client._collection_obj = collection
    result = pb.authenticate_user("a@b.c", "pass")
    assert result is data
    assert stub_st.session_state["pb_auth"] == {
        "token": "abc",
        "model": {"id": "1", "email": "user@example.org", "name": "Max", "admin": False},
    }
    assert mock_client.auth_store.token == ""
    log_path = pb.logger._get_today_logfile()
    assert log_path.exists()
    assert "logged in successfully" in log_path.read_text(encoding="utf-8")


def test_authenticate_user_failure(monkeypatch):
    """Test failed user authentication."""
    def raiser(email, password):
        raise ValueError("bad")

    client = MockClient(collection_obj=MockCollection(raiser))
    monkeypatch.setattr(pb, "client", client)
    result = pb.authenticate_user("a@b.c", "pass") # Purposely bad credentials
    assert result == pb.PBError.AUTHENTICATION_FAILED.name


def test_logout_user(mock_client, stub_st, browser_auth_stub):
    """Test user logout functionality."""
    stub_st.session_state["pb_auth"] = {"token": "t"} # Set up session state
    stub_st.session_state["user"] = {"id": 1} # Set up user state
    mock_client.auth_store.token = "t" # Set up auth store
    pb.logout_user() 
    assert mock_client.auth_store.token == "" # Auth store should be cleared
    assert "pb_auth" not in stub_st.session_state
    assert "user" not in stub_st.session_state
    assert mock_client.auth_store.cleared is True # Auth store clear method should be called
    assert browser_auth_stub["clear_marked"] is True
    assert browser_auth_stub["restore_blocked"] is True


def test_restore_session_ignores_cookie_while_logout_clear_is_pending(
    mock_client, stub_st, browser_auth_stub
):
    """A stale auth cookie must not re-authenticate the user right after logout."""
    browser_auth_stub["restore_blocked"] = True
    browser_auth_stub["value"] = {
        "token": "t123",
        "model": {"id": "1", "email": "user@example.org", "name": "Max", "admin": False},
    }

    pb.restore_session()

    assert "pb_auth" not in stub_st.session_state
    assert "user" not in stub_st.session_state
    assert browser_auth_stub["clear_marked"] is True
    assert browser_auth_stub["restore_blocked"] is True


def test_restore_session_unblocks_cookie_restore_after_cookie_is_gone(
    mock_client, stub_st, browser_auth_stub
):
    """Once the browser cookie is gone, normal session restore may resume."""
    browser_auth_stub["restore_blocked"] = True
    browser_auth_stub["value"] = None

    pb.restore_session()

    assert browser_auth_stub["restore_blocked"] is False


def test_sync_browser_auth_renders_component(monkeypatch):
    """Browser auth sync should inject the client-side persistence script."""
    captured = {}

    def fake_html(body, height):
        captured["body"] = body
        captured["height"] = height

    monkeypatch.setattr(pocketbase_browser_session.components, "html", fake_html)
    stub_streamlit = type("StubSt", (), {"session_state": {}})()

    auth_data = {
        "token": "abc",
        "model": {"id": "1", "email": "user@example.org", "name": "Max", "admin": False},
    }
    pocketbase_browser_session.PocketBaseBrowserSession(stub_streamlit).sync_auth(auth_data)

    assert "document.cookie" in captured["body"]
    assert captured["height"] == 0


def test_is_authenticated(stub_st):
    """Test authentication status check."""
    stub_st.session_state.pop("pb_auth", None)
    assert pb.is_authenticated() is False
    stub_st.session_state["pb_auth"] = {"token": "token", "model": DummyRecord()}
    assert pb.is_authenticated() is True


def test_show_logged_in_status_authenticated(stub_st):
    """Test displaying logged-in status for an authenticated user."""
    stub_st.session_state["pb_auth"] = {
        "token": "t",
        "model": DummyRecord(name="Max", admin=True),
    }
    pb.show_logged_in_status()
    assert stub_st.success_calls == [
        f"{pb.PBInfo.LOGGED_IN.value} Max"
    ]
    assert stub_st.text_calls == ["Admin: Yes"]
    assert stub_st.warning_calls == []


def test_show_logged_in_status_not_authenticated(stub_st):
    """Test displaying logged-in status for a not authenticated user."""
    stub_st.session_state.pop("pb_auth", None)
    pb.show_logged_in_status()
    assert stub_st.warning_calls == [pb.PBInfo.NOT_AUTHENTICATED.value]
    assert stub_st.success_calls == []


def test_user_is_admin_variants(stub_st):
    """Test checking if the user is an admin under various conditions."""
    stub_st.session_state.pop("pb_auth", None)
    assert pb.user_is_admin() is False

    class WithGet(dict):
        """A mock model with a get method."""
        def get(self, key, default=None):
            return True

    stub_st.session_state["pb_auth"] = {"token": "t", "model": WithGet()}
    assert pb.user_is_admin() is True

    stub_st.session_state["pb_auth"] = {"token": "t", "model": type("AFalse", (), {"admin": False})()}  # Admin attribute false
    assert pb.user_is_admin() is False

    stub_st.session_state["pb_auth"] = {"token": "t", "model": type("ATrue", (), {"admin": True})()}  # Admin attribute true
    assert pb.user_is_admin() is True


def test_get_user_from_auth_store_returns_user(monkeypatch, stub_st):
    """Test getting a user from the auth store when token and model are present."""
    class DummyUser:
        @classmethod
        def from_pb_record(cls, record):
            return {"user": record}

    monkeypatch.setattr(pb, "User", DummyUser)
    stub_st.session_state["pb_auth"] = {
        "token": "t",
        "model": {"id": 1, "email": "user@example.org"},
    }
    assert pb.get_user_from_auth_store() == {
        "user": {"id": 1, "email": "user@example.org"}
    }


def test_get_user_from_auth_store_missing_token_or_model(stub_st):
    """Test getting a user from the auth store when token or model is missing."""
    stub_st.session_state["pb_auth"] = {"token": "", "model": {"id": 1}}
    assert pb.get_user_from_auth_store() is None

    stub_st.session_state["pb_auth"] = {"token": "t", "model": None}
    assert pb.get_user_from_auth_store() is None


def test_restore_session_missing_token_or_model(mock_client, stub_st):
    """Test restoring session when token or model is missing."""
    stub_st.session_state["pb_auth"] = {"token": "", "model": {"id": 1}}
    pb.restore_session()
    assert "pb_auth" not in stub_st.session_state
    stub_st.session_state["pb_auth"] = {"token": "t123", "model": None}
    pb.restore_session()
    assert "pb_auth" not in stub_st.session_state


def test_show_logged_in_status_unknown_user(stub_st):
    """Test displaying logged-in status when user name is unknown."""
    stub_st.session_state["pb_auth"] = {
        "token": "t",
        "model": type("Model", (), {"admin": False})(),
    }
    pb.show_logged_in_status()
    assert stub_st.success_calls == [
        f"{pb.PBInfo.LOGGED_IN.value} {pb.PBInfo.UNKNOWN_USER.value}"
    ]
    assert stub_st.text_calls == ["Admin: No"]


def test_user_is_admin_no_attr(stub_st):
    """Test user admin status when model has no admin attribute."""
    stub_st.session_state["pb_auth"] = {"token": "t", "model": object()}
    assert pb.user_is_admin() is False


def test_get_user_from_auth_store_attribute_error(monkeypatch, stub_st):
    """Test getting a user from the auth store when an AttributeError occurs."""
    class FaultyUser:
        @classmethod
        def from_pb_record(cls, record):
            raise AttributeError("Attribute Error")

    monkeypatch.setattr(pb, "User", FaultyUser)
    stub_st.session_state["pb_auth"] = {"token": "t", "model": {"id": 1}}
    assert pb.get_user_from_auth_store() is None


def test_get_user_from_auth_store_unexpected_error(monkeypatch, stub_st):
    """Test getting a user from the auth store when an Unexpected Error occurs."""
    class FaultyUser:
        @classmethod
        def from_pb_record(cls, record):
            raise Exception("Unexpected Error")

    monkeypatch.setattr(pb, "User", FaultyUser)
    stub_st.session_state["pb_auth"] = {"token": "t", "model": {"id": 1}}
    assert pb.get_user_from_auth_store() is None
