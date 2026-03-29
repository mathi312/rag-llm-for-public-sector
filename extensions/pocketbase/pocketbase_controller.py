from __future__ import annotations

from .pocketbase_messages import PBError, PBInfo, PBLabel, PBLog


class PocketBaseAuthController:
    """Controller for auth-related use cases and UI-facing status handling."""

    def __init__(
        self,
        service,
        streamlit_module,
        user_cls,
        logger,
        browser_session,
        client=None,
    ) -> None:
        self._service = service
        self._st = streamlit_module
        self._user_cls = user_cls
        self._logger = logger
        self._browser_session = browser_session
        self._client = client

    def _get_session_auth(self) -> dict | None:
        # session_state is the fast path within a running Streamlit session.
        auth_data = self._st.session_state.get("pb_auth")
        if not isinstance(auth_data, dict):
            return None

        token = auth_data.get("token")
        model = auth_data.get("model")
        if not token or model is None:
            return None

        return auth_data

    def _clear_auth_store(self) -> None:
        # The shared PocketBase client must never keep auth between users.
        auth_store = getattr(self._client, "auth_store", None)
        if auth_store is not None and hasattr(auth_store, "clear"):
            auth_store.clear()

    @staticmethod
    def _serialize_model(model) -> dict | None:
        if model is None:
            return None
        if isinstance(model, dict):
            return dict(model)

        return {
            "id": getattr(model, "id", ""),
            "email": getattr(model, "email", ""),
            "name": getattr(model, "name", None),
            "admin": bool(getattr(model, "admin", False)),
        }

    def _build_auth_payload(self, token: str | None, model) -> dict | None:
        # Only persist the fields needed to reconstruct the user after a reload.
        serialized_model = self._serialize_model(model)
        if not token or serialized_model is None:
            return None

        return {
            "token": token,
            "model": serialized_model,
        }

    def restore_session(self) -> None:
        # Prefer the in-memory session for normal navigation within the same run.
        auth_data = self._get_session_auth()

        # After a browser reload, rehydrate the Streamlit session from the cookie.
        if auth_data is None:
            auth_data = self._browser_session.load_auth()
            if auth_data is not None:
                self._st.session_state["pb_auth"] = auth_data

        if auth_data is None:
            self._st.session_state.pop("pb_auth", None)
            self._st.session_state.pop("user", None)
            return

        # A malformed or stale cookie should be cleared so the next run starts clean.
        user = self._service.restore_user(auth_data, self._user_cls)
        if user is None:
            self._browser_session.mark_for_clear()
            self._st.session_state.pop("pb_auth", None)
            self._st.session_state.pop("user", None)
            return

        self._st.session_state["user"] = user

    def authenticate_user(self, email: str, password: str) -> dict | str:
        auth_data = self._service.authenticate_user(email, password)
        if auth_data is None:
            return PBError.AUTHENTICATION_FAILED.name

        # Normalize the PocketBase response before storing it in Streamlit/browser state.
        payload = self._build_auth_payload(
            getattr(auth_data, "token", None),
            getattr(auth_data, "record", None),
        )
        if payload is not None:
            self._st.session_state["pb_auth"] = payload
            user = self._service.restore_user(payload, self._user_cls)
            if user is not None:
                self._st.session_state["user"] = user
                self._logger.log_info(
                    PBLog.USER_LOGGED_IN_SUCCESS.value.format(email=user.email)
                )
            else:
                self._logger.log_info(
                    PBLog.USER_LOGGED_IN_SUCCESS.value.format(email=email)
                )

        # Never leave the shared PocketBase client authenticated across requests.
        self._clear_auth_store()
        return auth_data

    def logout_user(self) -> None:
        current_user = self.get_user_from_auth_store()
        self._logger.log_info(
            PBLog.USER_LOGGED_OUT_SUCCESS.value.format(
                email=current_user.email if current_user else PBInfo.UNKNOWN_USER.value
            )
        )
        # Clear both server-side state and the browser cookie bridge.
        self._clear_auth_store()
        self._browser_session.mark_for_clear()
        self._st.session_state.pop("pb_auth", None)
        self._st.session_state.pop("user", None)

    def is_authenticated(self) -> bool:
        return self._get_session_auth() is not None

    def show_logged_in_status(self) -> None:
        auth_data = self._get_session_auth()
        if auth_data is not None:
            model = auth_data.get("model")
            name = self._service.get_display_name(model)
            self._st.success(f"{PBInfo.LOGGED_IN.value} {name or PBInfo.UNKNOWN_USER.value}")
            self._st.text(
                PBLabel.ADMIN_STATUS.value.format(
                    status=PBLabel.ADMIN_YES.value
                    if self.user_is_admin()
                    else PBLabel.ADMIN_NO.value
                )
            )
            return
        self._st.warning(PBInfo.NOT_AUTHENTICATED.value)

    def user_is_admin(self) -> bool:
        auth_data = self._get_session_auth()
        model = auth_data.get("model") if auth_data else None
        return self._service.is_admin(model)

    def get_user_from_auth_store(self):
        auth_data = self._get_session_auth()
        if auth_data is None:
            return None
        return self._service.restore_user(auth_data, self._user_cls)
