from __future__ import annotations


class PocketBaseAuthRepository:
    """Data access for authentication-related PocketBase operations."""

    def __init__(self, client) -> None:
        self._client = client

    def authenticate_user(self, email: str, password: str):
        return self._client.collection("users").auth_with_password(email, password)
