from pathlib import Path

from .document_management_controller import DocumentManagementController
from .documentupload_controller import DocumentController
from .documentupload_repository import DocumentRepository
from .documentupload_service import DocumentStorageService


def build_document_controller(client, data_dir: Path) -> DocumentController:
    repository = DocumentRepository(client)
    storage = DocumentStorageService(data_dir)
    return DocumentController(repository, storage)


__all__ = [
    "DocumentManagementController",
    "DocumentController",
    "DocumentRepository",
    "DocumentStorageService",
    "build_document_controller",
]
