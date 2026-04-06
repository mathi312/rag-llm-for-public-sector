from __future__ import annotations

from pathlib import Path


class DocumentController:
    """Application-facing facade that orchestrates repository and storage services."""

    def __init__(self, repository, storage_service) -> None:
        self._repository = repository
        self._storage = storage_service

    @property
    def data_dir(self) -> Path:
        return self._storage.data_dir

    @property
    def backup_dir(self) -> Path:
        return self._storage.backup_dir

    def create_temp_copy(self, source_name: str, content: bytes) -> Path:
        return self._storage.create_temp_copy(source_name, content)

    def save_to_data_dir(self, source_path: Path, target_name: str) -> Path:
        return self._storage.save_to_data_dir(source_path, target_name)

    def delete_from_data_dir(self, names: set[str | None]) -> None:
        self._storage.delete_from_data_dir(names)

    def move_to_backup(self, source_name: str, backup_name: str) -> None:
        self._storage.move_to_backup(source_name, backup_name)

    def restore_backup(self, backup_file: Path, target_name: str) -> Path:
        return self._storage.restore_backup(backup_file, target_name)

    def list_records(self):
        return self._repository.list_all()

    def create_record(
        self,
        title: str,
        version: str,
        needed_id: list[str],
        original_name: str,
        local_path: str,
        mime_type: str,
        file_upload=None,
    ) -> None:
        self._repository.create(
            title=title,
            version=version,
            needed_id=needed_id,
            original_name=original_name,
            local_path=local_path,
            mime_type=mime_type,
            file_upload=file_upload,
        )

    def update_record(self, record_id: str, payload: dict) -> None:
        self._repository.update(record_id, payload)

    def delete_record(self, record_id: str) -> None:
        self._repository.delete(record_id)
