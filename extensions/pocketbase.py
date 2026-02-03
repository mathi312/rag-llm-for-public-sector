import os
import streamlit as st
from pocketbase import PocketBase
from extensions.pocketbase_messages import PBError, PBInfo
from extensions.user import User

def get_pocketbase_client():
    use_fake = os.getenv("MOCK_POCKETBASE", "false").lower() == "true"

    if use_fake:
        from tests.integration.pocketbase_mock import PocketBaseMock
        return PocketBaseMock()

    pb_url = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8080")
    return PocketBase(pb_url)

client = get_pocketbase_client()

def restore_session() -> None:
    """Restore the user session from the auth store."""
    auth_data = st.session_state.get("pb_auth")
    if not auth_data:
        # no session to restore
        return
    try:
        # validate stored session
        token = auth_data.get("token")
        model = auth_data.get("model")
        if not token or model is None:
            # invalid stored session, clear it
            st.session_state.pop("pb_auth", None)
            return
        client.auth_store.save(token, model)
    except Exception:
        # if invalid, clear session
        st.session_state.pop("pb_auth", None)


def authenticate_user(email: str, password: str) -> dict | str:
    """Authenticate a user with PocketBase."""
    try:
        auth_data = client.collection("users").auth_with_password(email, password)
        return auth_data
    except Exception as e:
        return PBError.AUTHENTICATION_FAILED.name


def logout_user() -> None:
    """Logout the current authenticated user."""
    client.auth_store.clear()
    st.session_state.pop("pb_auth", None)
    st.session_state.pop("user", None)


def is_authenticated() -> bool:
    """Check if a user is authenticated."""
    return bool(client.auth_store.token)


def show_logged_in_status() -> None:
    """Display the authenticated status of the user."""
    is_logged_in = bool(client.auth_store.token)
    if is_logged_in and client.auth_store.model:
        # Try to get the user's name from the model
        name = getattr(client.auth_store.model, "name", None)
        st.success(f"{PBInfo.LOGGED_IN.value} {name or PBInfo.UNKNOWN_USER.value}")
        st.text(f"Admin: {'Yes' if user_is_admin() else 'No'}")
    else:
        st.warning(PBInfo.NOT_AUTHENTICATED.value)


def user_is_admin() -> bool:
    """Check if the authenticated user is an admin."""
    model = client.auth_store.model

    if model is None:
        return False

    if hasattr(model, "get"):
        return bool(model.get("admin"))

    return bool(getattr(model, "admin", False))


def get_user_from_auth_store() -> User | None:
    """Restore the user from the auth store."""
    try:
        if not client.auth_store.token:
            return None

        if not client.auth_store.model:
            return None

        user = User.from_pb_record(client.auth_store.model)
        return user

    except AttributeError as e:
        print(f"Attribute error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None