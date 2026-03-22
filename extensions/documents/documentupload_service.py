from __future__ import annotations

import shutil
import tempfile
from pathlib import Path


class DocumentStorageService:
    """Handles local file-system operations for document data and backups."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._backup_dir = self._data_dir / "backup"
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    @property
    def backup_dir(self) -> Path:
        return self._backup_dir

    def create_temp_copy(self, source_name: str, content: bytes) -> Path:
        suffix = Path(source_name).suffix or ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            return Path(tmp.name)

    def save_to_data_dir(self, source_path: Path, target_name: str) -> Path:
        destination = self._data_dir / target_name
        shutil.copy2(source_path, destination)
        return destination

    def delete_from_data_dir(self, names: set[str | None]) -> None:
        for name in names:
            if not name:
                continue
            path = self._data_dir / name
            if path.exists() and path.is_file():
                path.unlink()

    def move_to_backup(self, source_name: str, backup_name: str) -> None:
        source_path = self._data_dir / source_name
        if source_path.exists() and source_path.is_file():
            shutil.move(str(source_path), str(self._backup_dir / backup_name))

    def restore_backup(self, backup_file: Path, target_name: str) -> Path:
        restored_path = self._data_dir / target_name
        shutil.copy2(str(backup_file), str(restored_path))
        return restored_path
