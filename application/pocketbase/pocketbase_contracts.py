from __future__ import annotations

from typing import Any, Protocol


class AuthRepositoryProtocol(Protocol):
    """Contract for auth repositories behind the BaaS boundary."""

    def authenticate_user(self, email: str, password: str) -> Any:
        ...
