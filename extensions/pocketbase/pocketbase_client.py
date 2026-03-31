import os

from pocketbase import PocketBase

PB_URL = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8080")

_pb_client: PocketBase | None = None

def get_pocketbase_client() -> PocketBase:
    """
    Returns a shared, authenticated PocketBase client.
    Never use this client for user auth — it will overwrite the admin token.
    """
    global _pb_client
    if _pb_client is None:
        _pb_client = PocketBase(PB_URL)

    # Re-auth if token is missing or expired
    if not _pb_client.auth_store.token:
        _pb_client.admins.auth_with_password(
            os.getenv("POCKETBASE_ADMIN_USERNAME"),
            os.getenv("POCKETBASE_ADMIN_PASSWORD"),
        )

    return _pb_client
