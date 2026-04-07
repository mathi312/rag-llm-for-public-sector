from __future__ import annotations

import base64
import json

import streamlit.components.v1 as components


class PocketBaseBrowserSession:
    """Synchronize auth state between Streamlit session_state and a browser cookie."""

    COOKIE_NAME = "pb_auth"
    COOKIE_MAX_AGE_SECONDS = 60 * 60 * 8
    COMPONENT_COUNTER_KEY = "_pb_browser_auth_component_counter"
    CLEAR_FLAG_KEY = "_pb_clear_browser_auth"
    BLOCK_RESTORE_KEY = "_pb_block_browser_auth_restore"

    def __init__(self, streamlit_module) -> None:
        self._st = streamlit_module

    def _next_component_marker(self, prefix: str) -> str:
        counter = int(self._st.session_state.get(self.COMPONENT_COUNTER_KEY, 0)) + 1
        self._st.session_state[self.COMPONENT_COUNTER_KEY] = counter
        return f"{prefix}_{counter}"

    @staticmethod
    def _encode_auth_data(auth_data: dict) -> str:
        # Store a compact JSON payload in the cookie to keep the Javascript bridge simple.
        payload = json.dumps(auth_data, separators=(",", ":")).encode("utf-8")
        return base64.urlsafe_b64encode(payload).decode("ascii")

    @staticmethod
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

    def load_auth(self) -> dict | None:
        # Streamlit exposes request cookies via st.context on the next app run.
        context = getattr(self._st, "context", None)
        cookies = getattr(context, "cookies", None)
        if cookies is None:
            return None

        try:
            value = cookies.get(self.COOKIE_NAME)
        except Exception:
            return None

        return self._decode_auth_data(value)

    def sync_auth(self, auth_data: dict | None) -> None:
        """Keep the browser cookie aligned with the server-side session state."""
        if not isinstance(auth_data, dict):
            return

        encoded = self._encode_auth_data(auth_data)
        marker = self._next_component_marker("pb_auth_cookie_sync")
        components.html(
            f"""
            <!-- {marker} -->
            <script>
            const name = {json.dumps(self.COOKIE_NAME)};
            const value = {json.dumps(encoded)};
            const maxAge = {self.COOKIE_MAX_AGE_SECONDS};
            const secure = window.parent.location.protocol === "https:" ? "; Secure" : "";
            window.parent.document.cookie =
              `${{name}}=${{value}}; path=/; max-age=${{maxAge}}; SameSite=Lax${{secure}}`;
            </script>
            """,
            height=0,
        )

    def mark_for_clear(self) -> None:
        # Cookie deletion happens in the next render pass via the Javascript bridge.
        self._st.session_state[self.CLEAR_FLAG_KEY] = True
        self._st.session_state[self.BLOCK_RESTORE_KEY] = True

    def restore_blocked(self) -> bool:
        return bool(self._st.session_state.get(self.BLOCK_RESTORE_KEY, False))

    def unblock_restore(self) -> None:
        self._st.session_state.pop(self.BLOCK_RESTORE_KEY, None)

    def clear_pending(self) -> bool:
        return bool(self._st.session_state.get(self.CLEAR_FLAG_KEY, False))

    def flush_clear(self) -> None:
        """Flush the pending browser auth clear action, if any."""
        if not self._st.session_state.pop(self.CLEAR_FLAG_KEY, False):
            return

        marker = self._next_component_marker("pb_auth_cookie_clear")
        components.html(
            f"""
            <!-- {marker} -->
            <script>
            const name = {json.dumps(self.COOKIE_NAME)};
            const secure = window.parent.location.protocol === "https:" ? "; Secure" : "";
            window.parent.document.cookie =
              `${{name}}=; path=/; max-age=0; SameSite=Lax${{secure}}`;
            </script>
            """,
            height=0,
        )
