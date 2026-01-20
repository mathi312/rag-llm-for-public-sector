import pytest

from extensions import pocketbase as pb


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


def test_restore_session_no_auth(monkeypatch, mock_client, stub_st):
    """Test restoring session when no auth data is present."""
    pb.restore_session()
    assert mock_client.auth_store.token == ""
    assert mock_client.auth_store.model is None
    assert "pb_auth" not in stub_st.session_state


def test_restore_session_with_valid_data(mock_client, stub_st):
    """Test restoring session with valid auth data."""
    stub_st.session_state["pb_auth"] = {"token": "t123", "model": {"id": 1}}
    pb.restore_session()
    assert mock_client.auth_store.token == "t123"
    assert mock_client.auth_store.model == {"id": 1}


def test_restore_session_with_invalid_data(monkeypatch, stub_st):
    """Test restoring session with invalid auth data."""
    class FailingAuthStore(MockAuthStore):
        """An auth store that fails on save."""
        def save(self, token, model):
            raise RuntimeError("fail")

    client = MockClient()
    client.auth_store = FailingAuthStore()
    monkeypatch.setattr(pb, "client", client)
    stub_st.session_state["pb_auth"] = {"token": "bad", "model": {}} # Invalid data
    pb.restore_session()
    assert "pb_auth" not in stub_st.session_state


def test_authenticate_user_success(monkeypatch, mock_client):
    """Test successful user authentication."""
    data = {"token": "abc"}
    collection = MockCollection(lambda e, p: data)
    mock_client._collection_obj = collection
    result = pb.authenticate_user("a@b.c", "pass")
    assert result is data


def test_authenticate_user_failure(monkeypatch):
    """Test failed user authentication."""
    def raiser(email, password):
        raise ValueError("bad")

    client = MockClient(collection_obj=MockCollection(raiser))
    monkeypatch.setattr(pb, "client", client)
    result = pb.authenticate_user("a@b.c", "pass") # Purposely bad credentials
    assert result == pb.PBError.AUTHENTICATION_FAILED.name


def test_logout_user(mock_client, stub_st):
    """Test user logout functionality."""
    stub_st.session_state["pb_auth"] = {"token": "t"} # Set up session state
    stub_st.session_state["user"] = {"id": 1} # Set up user state
    mock_client.auth_store.token = "t" # Set up auth store
    pb.logout_user() 
    assert mock_client.auth_store.token == "" # Auth store should be cleared
    assert "pb_auth" not in stub_st.session_state
    assert "user" not in stub_st.session_state
    assert mock_client.auth_store.cleared is True # Auth store clear method should be called


def test_is_authenticated(mock_client):
    """Test authentication status check."""
    mock_client.auth_store.token = ""
    assert pb.is_authenticated() is False
    mock_client.auth_store.token = "token"
    assert pb.is_authenticated() is True


def test_show_logged_in_status_authenticated(mock_client, stub_st):
    """Test displaying logged-in status for an authenticated user."""
    mock_client.auth_store.token = "t"
    mock_client.auth_store.model = type(
        "Model", (), {"name": "Max", "admin": True}
    )()
    pb.show_logged_in_status()
    assert stub_st.success_calls == [
        f"{pb.PBInfo.LOGGED_IN.value} Max"
    ]
    assert stub_st.text_calls == ["Admin: Yes"]
    assert stub_st.warning_calls == []


def test_show_logged_in_status_not_authenticated(mock_client, stub_st):
    """Test displaying logged-in status for a not authenticated user."""
    mock_client.auth_store.token = ""
    mock_client.auth_store.model = None
    pb.show_logged_in_status()
    assert stub_st.warning_calls == [pb.PBInfo.NOT_AUTHENTICATED.value]
    assert stub_st.success_calls == []


def test_user_is_admin_variants(mock_client):
    """Test checking if the user is an admin under various conditions."""
    mock_client.auth_store.model = None
    assert pb.user_is_admin() is False

    class WithGet(dict):
        """A mock model with a get method."""
        def get(self, key, default=None):
            return True

    mock_client.auth_store.model = WithGet()
    assert pb.user_is_admin() is True

    mock_client.auth_store.model = type("AFalse", (), {"admin": False})() # Admin attribute false
    assert pb.user_is_admin() is False

    mock_client.auth_store.model = type("ATrue", (), {"admin": True})() # Admin attribute true
    assert pb.user_is_admin() is True


def test_get_user_from_auth_store_returns_user(monkeypatch, mock_client):
    """Test getting a user from the auth store when token and model are present."""
    class DummyUser:
        @classmethod
        def from_pb_record(cls, record):
            return {"user": record}

    monkeypatch.setattr(pb, "User", DummyUser)
    mock_client.auth_store.token = "t"
    mock_client.auth_store.model = {"id": 1}
    assert pb.get_user_from_auth_store() == {"user": {"id": 1}}


def test_get_user_from_auth_store_missing_token_or_model(mock_client):
    """Test getting a user from the auth store when token or model is missing."""
    mock_client.auth_store.token = ""
    mock_client.auth_store.model = {"id": 1}
    assert pb.get_user_from_auth_store() is None

    mock_client.auth_store.token = "t"
    mock_client.auth_store.model = None
    assert pb.get_user_from_auth_store() is None


def test_restore_session_missing_token_or_model(mock_client, stub_st):
    """Test restoring session when token or model is missing."""
    stub_st.session_state["pb_auth"] = {"token": "", "model": {"id": 1}}
    pb.restore_session()
    assert mock_client.auth_store.token == ""
    stub_st.session_state["pb_auth"] = {"token": "t123", "model": None}
    pb.restore_session()
    assert mock_client.auth_store.token == ""


def test_show_logged_in_status_unknown_user(mock_client, stub_st):
    """Test displaying logged-in status when user name is unknown."""
    mock_client.auth_store.token = "t"
    mock_client.auth_store.model = type("Model", (), {"admin": False})()
    pb.show_logged_in_status()
    assert stub_st.success_calls == [
        f"{pb.PBInfo.LOGGED_IN.value} {pb.PBInfo.UNKNOWN_USER.value}"
    ]
    assert stub_st.text_calls == ["Admin: No"]


def test_user_is_admin_no_attr(mock_client):
    """Test user admin status when model has no admin attribute."""
    mock_client.auth_store.model = object()
    assert pb.user_is_admin() is False


def test_get_user_from_auth_store_attribute_error(monkeypatch, mock_client):
    """Test getting a user from the auth store when an AttributeError occurs."""
    class FaultyUser:
        @classmethod
        def from_pb_record(cls, record):
            raise AttributeError("Attribute Error")

    monkeypatch.setattr(pb, "User", FaultyUser)
    mock_client.auth_store.token = "t"
    mock_client.auth_store.model = {"id": 1}
    assert pb.get_user_from_auth_store() is None