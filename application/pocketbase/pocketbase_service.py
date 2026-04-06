from __future__ import annotations

from application.pocketbase.pocketbase_contracts import AuthRepositoryProtocol
from domain.auth.pocketbase_messages import PBLog


class PocketBaseAuthService:
    """Business logic for auth/session operations independent from UI widgets."""

    def __init__(self, repository: AuthRepositoryProtocol, logger) -> None:
        self._repository = repository
        self._logger = logger

    def authenticate_user(self, email: str, password: str):
        try:
            return self._repository.authenticate_user(email, password)
        except Exception as exc:
            self._logger.log_warning(
                PBLog.AUTHENTICATION_FAILED_FOR_EMAIL.value.format(email=email, error=exc)
            )
            return None

    def restore_user(self, auth_data: dict, user_cls):
        model = auth_data.get("model")
        if not self._has_required_user_fields(model):
            return None

        try:
            return user_cls.from_pb_record(model)
        except AttributeError as exc:
            self._logger.log_warning(
                PBLog.RESTORE_USER_ATTRIBUTE_FAILED.value.format(error=exc)
            )
            return None
        except Exception as exc:
            self._logger.log_error(
                PBLog.RESTORE_USER_UNEXPECTED_ERROR.value.format(error=exc)
            )
            return None

    @staticmethod
    def _has_required_user_fields(model) -> bool:
        if model is None:
            return False

        if isinstance(model, dict):
            # We check for 'id' and 'email' as they are essential for user identification and authentication.
            return bool(model.get("id")) and bool(model.get("email"))

        # Check if attributes 'id' and 'email' exist and are truthy for non-dict models.
        return bool(getattr(model, "id", None)) and bool(getattr(model, "email", None))

    @staticmethod
    def is_admin(model) -> bool:
        if model is None:
            return False
        if hasattr(model, "get"):
            return bool(model.get("admin"))
        return bool(getattr(model, "admin", False))

    @staticmethod
    def get_display_name(model) -> str | None:
        if model is None:
            return None
        if isinstance(model, dict):
            return model.get("name")
        return getattr(model, "name", None)
