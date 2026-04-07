from __future__ import annotations

from pocketbase import PocketBase
from pocketbase.client import FileUpload


class DocumentRepository:
    """Encapsulates PocketBase persistence for document records."""

    def __init__(self, client: PocketBase) -> None:
        self._client = client

    def list_all(self):
        return self._client.collection("documents").get_full_list()

    def create(
        self,
        title: str,
        version: str,
        needed_id: list[str],
        original_name: str,
        local_path: str,
        mime_type: str,
        file_upload=None,
    ) -> None:
        upload = file_upload or FileUpload((local_path, original_name, mime_type))
        self._client.collection("documents").create(
            {
                "title": title,
                "version": version,
                "needed_id": needed_id,
                "original_name": original_name,
                "document": upload,
            }
        )

    def update(self, record_id: str, payload: dict) -> None:
        self._client.collection("documents").update(record_id, payload)

    def delete(self, record_id: str) -> None:
        self._client.collection("documents").delete(record_id)
