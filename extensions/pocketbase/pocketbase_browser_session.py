from __future__ import annotations

import base64
import json

import streamlit as st
import streamlit.components.v1 as components


COOKIE_NAME = "pb_auth"
COOKIE_MAX_AGE_SECONDS = 60 * 60 * 8
COMPONENT_COUNTER_KEY = "_pb_browser_auth_component_counter"
CLEAR_FLAG_KEY = "_pb_clear_browser_auth"


def _next_component_marker(prefix: str) -> str:
    counter = int(st.session_state.get(COMPONENT_COUNTER_KEY, 0)) + 1
    st.session_state[COMPONENT_COUNTER_KEY] = counter
    return f"{prefix}_{counter}"


def _encode_auth_data(auth_data: dict) -> str:
    # Store a compact JSON payload in the cookie to keep the Javascript integration simple.
    payload = json.dumps(auth_data, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii")


def _decode_auth_data(value: str | None) -> dict | None:
    if not value:
        return None

    try:
        decoded = base64.urlsafe_b64decode(value.encode("ascii")).decode("utf-8")
        auth_data = json.loads(decoded)
    except Exception:
        return None

    if not isinstance(auth_data, dict):
        return None

    token = auth_data.get("token")
    model = auth_data.get("model")
    if not token or not isinstance(model, dict):
        return None

    return auth_data


def load_auth_from_cookies() -> dict | None:
    # Streamlit exposes request cookies via st.context on the next app run.
    context = getattr(st, "context", None)
    cookies = getattr(context, "cookies", None)
    if cookies is None:
        return None

    try:
        value = cookies.get(COOKIE_NAME)
    except Exception:
        return None

    return _decode_auth_data(value)


def sync_browser_auth(auth_data: dict | None) -> None:
    """Keep the browser cookie in sync with the server-side session state."""
    if not isinstance(auth_data, dict):
        return

    encoded = _encode_auth_data(auth_data)
    marker = _next_component_marker("pb_auth_cookie_sync")
    components.html(
        f"""
        <!-- {marker} -->
        <script>
        // Keep the browser cookie aligned with the server-side session state.
        const name = {json.dumps(COOKIE_NAME)};
        const value = {json.dumps(encoded)};
        const maxAge = {COOKIE_MAX_AGE_SECONDS};
        const secure = window.parent.location.protocol === "https:" ? "; Secure" : "";
        window.parent.document.cookie =
          `${{name}}=${{value}}; path=/; max-age=${{maxAge}}; SameSite=Lax${{secure}}`;
        </script>
        """,
        height=0,
    )


def mark_browser_auth_for_clear() -> None:
    # Cookie deletion happens in the next render pass via the Javascript integration.
    st.session_state[CLEAR_FLAG_KEY] = True


def browser_auth_clear_pending() -> bool:
    return bool(st.session_state.get(CLEAR_FLAG_KEY, False))


def flush_browser_auth_clear() -> None:
    """Flush the pending browser auth clear action, if any."""
    if not st.session_state.pop(CLEAR_FLAG_KEY, False):
        return

    marker = _next_component_marker("pb_auth_cookie_clear")
    components.html(
        f"""
        <!-- {marker} -->
        <script>
        // Expire the auth cookie in the browser after logout or invalid restore.
        const name = {json.dumps(COOKIE_NAME)};
        const secure = window.parent.location.protocol === "https:" ? "; Secure" : "";
        window.parent.document.cookie =
          `${{name}}=; path=/; max-age=0; SameSite=Lax${{secure}}`;
        </script>
        """,
        height=0,
    )
