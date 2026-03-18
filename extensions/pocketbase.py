import os
import streamlit as st
from pocketbase import PocketBase
from extensions.pocketbase_messages import PBError, PBInfo
from extensions.user import User
from extensions.logger import Logger

logger = Logger()

pb_url = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8080")
client = PocketBase(pb_url)


def _get_session_auth() -> dict | None:
    """Return validated auth payload from Streamlit session state."""
    auth_data = st.session_state.get("pb_auth")
    if not isinstance(auth_data, dict):
        return None

    token = auth_data.get("token")
    model = auth_data.get("model")
    if not token or model is None:
        return None

    return auth_data

def restore_session() -> None:
    """Restore the user session from session state data."""
    auth_data = _get_session_auth()
    if auth_data is None:
        st.session_state.pop("pb_auth", None)
        st.session_state.pop("user", None)
        return

    try:
        st.session_state["user"] = User.from_pb_record(auth_data.get("model"))
    except Exception:
        st.session_state.pop("pb_auth", None)
        st.session_state.pop("user", None)


def authenticate_user(email: str, password: str) -> dict | str:
    """Authenticate a user with PocketBase."""
    try:
        auth_data = client.collection("users").auth_with_password(email, password)
        return auth_data
    except Exception as e:
        return PBError.AUTHENTICATION_FAILED.name


def logout_user() -> None:
    """Logout the current authenticated user."""
    current_user = get_user_from_auth_store()
    logger.log_info(f"User '{current_user.email if current_user else 'Unknown'}' logged out successfully.")
    client.auth_store.clear()
    st.session_state.pop("pb_auth", None)
    st.session_state.pop("user", None)


def is_authenticated() -> bool:
    """Check if a user is authenticated."""
    return _get_session_auth() is not None


def show_logged_in_status() -> None:
    """Display the authenticated status of the user."""
    auth_data = _get_session_auth()
    if auth_data is not None:
        # Try to get the user's name from the model
        model = auth_data.get("model")
        if isinstance(model, dict):
            name = model.get("name")
        else:
            name = getattr(model, "name", None)
        st.success(f"{PBInfo.LOGGED_IN.value} {name or PBInfo.UNKNOWN_USER.value}")
        st.text(f"Admin: {'Yes' if user_is_admin() else 'No'}")
    else:
        st.warning(PBInfo.NOT_AUTHENTICATED.value)


def user_is_admin() -> bool:
    """Check if the authenticated user is an admin."""
    auth_data = _get_session_auth()
    model = auth_data.get("model") if auth_data else None

    if model is None:
        return False

    if hasattr(model, "get"):
        return bool(model.get("admin"))

    return bool(getattr(model, "admin", False))


def get_user_from_auth_store() -> User | None:
    """Restore the user from the auth store."""
    try:
        auth_data = _get_session_auth()
        if auth_data is None:
            return None

        user = User.from_pb_record(auth_data.get("model"))
        return user

    except AttributeError as e:
        print(f"Attribute error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None