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


class PBLabel(Enum):
    """UI labels/messages related to PocketBase auth state."""

    ADMIN_STATUS: str = "Admin: {status}"
    ADMIN_YES: str = "Yes"
    ADMIN_NO: str = "No"


class PBLog(Enum):
    """Log templates for PocketBase-related flows."""

    USER_LOGGED_IN_SUCCESS: str = "User '{email}' logged in successfully."
    USER_LOGGED_OUT_SUCCESS: str = "User '{email}' logged out successfully."
    AUTHENTICATION_FAILED_FOR_EMAIL: str = "Authentication failed for '{email}': {error}"
    RESTORE_AUTH_FROM_STORE_FAILED: str = "Could not restore auth from auth_store: {error}"
    SAVE_AUTH_TO_STORE_FAILED: str = "Could not save auth to auth_store: {error}"
    RESTORE_USER_ATTRIBUTE_FAILED: str = "Failed to restore user from session auth model: {error}"
    RESTORE_USER_UNEXPECTED_ERROR: str = "Unexpected user restoration error: {error}"