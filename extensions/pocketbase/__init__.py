from __future__ import annotations

import os
from typing import Callable
import streamlit as st
from pocketbase import PocketBase

from extensions.logger import Logger
from .pocketbase_messages import PBError, PBInfo
from extensions.user import User
from .pocketbase_controller import PocketBaseAuthController
from .pocketbase_repository import PocketBaseAuthRepository
from .pocketbase_service import PocketBaseAuthService
from .pocketbase_client import get_pocketbase_client

logger = Logger()
pb_url = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8080")
client = PocketBase(pb_url)
_auth_repository_factory: Callable[[object], object] = PocketBaseAuthRepository


def set_auth_repository_factory(factory: Callable[[object], object]) -> None:
    """Set a custom auth repository factory to replace PocketBase at runtime."""
    global _auth_repository_factory
    _auth_repository_factory = factory


def _build_controller() -> PocketBaseAuthController:
    repository = _auth_repository_factory(client)
    service = PocketBaseAuthService(repository, logger)
    return PocketBaseAuthController(service, st, User, logger, client=client)


def restore_session() -> None:
    _build_controller().restore_session()


def authenticate_user(email: str, password: str) -> dict | str:
    return _build_controller().authenticate_user(email, password)


def logout_user() -> None:
    _build_controller().logout_user()


def is_authenticated() -> bool:
    return _build_controller().is_authenticated()


def show_logged_in_status() -> None:
    _build_controller().show_logged_in_status()


def user_is_admin() -> bool:
    return _build_controller().user_is_admin()


def get_user_from_auth_store() -> User | None:
    return _build_controller().get_user_from_auth_store()


__all__ = [
    "PBError",
    "PBInfo",
    "client",
    "authenticate_user",
    "get_user_from_auth_store",
    "is_authenticated",
    "logout_user",
    "restore_session",
    "set_auth_repository_factory",
    "show_logged_in_status",
    "user_is_admin",
]
