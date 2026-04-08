
class IndexLoadAndBuildError(Exception):
    """Base exception for Indexing errors."""


class IndexLoadError(IndexLoadAndBuildError):
    """Raised when loading the index fails."""


class IndexBuildError(IndexLoadAndBuildError):
    """Raised when building the index fails."""


class IndexDoesntExistError(IndexLoadAndBuildError):
    """Raised when the index folder doesnt exist."""
