from __future__ import annotations

from .pocketbase_messages import PBError, PBInfo, PBLabel, PBLog


class PocketBaseAuthController:
    """Controller for auth-related use cases and UI-facing status handling."""

    def __init__(self, service, streamlit_module, user_cls, logger, client=None) -> None:
        self._service = service
        self._st = streamlit_module
        self._user_cls = user_cls
        self._logger = logger
        self._client = client

    def _get_session_auth(self) -> dict | None:
        auth_data = self._st.session_state.get("pb_auth")
        if not isinstance(auth_data, dict):
            return None

        token = auth_data.get("token")
        model = auth_data.get("model")
        if not token or model is None:
            return None

        return auth_data

    def restore_session(self) -> None:
        # Try to get auth from session_state first
        auth_data = self._get_session_auth()
        
        # # If not in session_state, try to restore from auth_store
        # if auth_data is None and self._client is not None:
        #     auth_store = getattr(self._client, "auth_store", None)
        #     if auth_store and hasattr(auth_store, "token") and auth_store.token:
        #         # auth_store has token and model, restore them to session
        #         try:
        #             auth_data = {
        #                 "token": auth_store.token,
        #                 "model": auth_store.model
        #             }
        #             self._st.session_state["pb_auth"] = auth_data
        #         except Exception as e:
        #             self._logger.log_warning(
        #                 PBLog.RESTORE_AUTH_FROM_STORE_FAILED.value.format(error=e)
        #             )
        
        # Now proceed with restoring the user
        if auth_data is None:
            self._st.session_state.pop("pb_auth", None)
            self._st.session_state.pop("user", None)
            return

        user = self._service.restore_user(auth_data, self._user_cls)
        if user is None:
            self._st.session_state.pop("pb_auth", None)
            self._st.session_state.pop("user", None)
            return

        self._st.session_state["user"] = user

    def authenticate_user(self, email: str, password: str) -> dict | str:
        auth_data = self._service.authenticate_user(email, password)
        if auth_data is None:
            return PBError.AUTHENTICATION_FAILED.name
        return auth_data

    def logout_user(self) -> None:
        current_user = self.get_user_from_auth_store()
        self._logger.log_info(
            PBLog.USER_LOGGED_OUT_SUCCESS.value.format(
                email=current_user.email if current_user else PBInfo.UNKNOWN_USER.value
            )
        )
        auth_store = getattr(self._client, "auth_store", None)
        if auth_store is not None and hasattr(auth_store, "clear"):
            auth_store.clear()
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
