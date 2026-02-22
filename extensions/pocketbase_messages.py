from enum import Enum


class PBError(Enum):
    """Error messages for PocketBase operations."""

    AUTHENTICATION_FAILED: str = "Authentication failed. Please check your credentials."
    RECORD_NOT_FOUND: str = "Record Not Found"


class PBWarning(Enum):
    """Warning messages for PocketBase operations."""

    INCORRECT_EMAIL_FORMAT: str = "Incorrect email format."
    MISSING_CREDENTIALS: str = "Please fill in both email and password."


class PBSuccess(Enum):
    """Success messages for PocketBase operations."""

    AUTHENTICATION_SUCCESS: str = "Logged in successfully."


class PBInfo(Enum):
    """Info messages for PocketBase operations."""

    NOT_AUTHENTICATED: str = "Not authenticated"
    LOGGED_IN: str = "Logged in as:"
    UNKNOWN_USER: str = "Unknown User"

class PBSaveError(Enum):
    """Error messages for PocketBase save operations."""