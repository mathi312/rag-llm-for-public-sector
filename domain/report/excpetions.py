
class PrinterBrokenError(Exception):
    """Raised when the printer is broken"""


class EmptyReportError(Exception):
    """Raised when the report is empty"""


class EmptyEmailAddressError(Exception):
    """Raised when the passed email address is empty"""
