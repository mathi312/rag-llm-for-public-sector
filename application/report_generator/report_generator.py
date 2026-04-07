import os

from email.message import EmailMessage
from domain.user.user import User
from domain.report.report import Report
from domain.report.excpetions import (
    EmptyReportError,
    PrinterBrokenError,
    EmptyEmailAddressError,
)
from infrastructure.smtp_server.smtp_server import send_message_via_smtp_server


def print_report(
    report: Report, user: User | None = None, is_printer_broken: bool = True
):
    """
    Prints the given report.

    Args:
        report (Report): The report to be printed.

    Raises:
        EmptyReportError: If the report is None or contains no content.
        PrinterBrokenError: If the printer fails during printing.
    """
    if report is None:
        raise EmptyReportError(
            "No content available for this report. Please start a conversation and try again."
        )

    if is_printer_broken:
        raise PrinterBrokenError(
            "Printer currently not available. Alternatively you can send the report per mail"
        )


def send_report_via_email(report: Report, to_email: str, user: User | None = None):
    """
    Sends an email to the given address containing the report as a pdf.

    Args:
        report (Report): The report to be sent.
        to_email (str): Recipient email address.

    Raises:
        EmptyReportError: If the report is None or contains no content.
        EmptyEmailAddressError: If the recipient email address is empty.
    """
    if report is None:
        raise EmptyReportError(
            "No content available for this report. Please start a conversation and try again."
        )
    if not to_email:
        raise EmptyEmailAddressError(
            "The email address is empty. Please enter a email address!"
        )

    pdf = report.to_pdf(user)

    # Create email
    msg = EmailMessage()
    msg["Subject"] = "LLM Chat Report"
    # msg["From"] = "report@ragllm.uni-ulm.de"
    msg["From"] = os.getenv("APP_ENV") == "production" and os.getenv("SMTP_USER") or "report@ragllm.uni-ulm.de"
    msg["To"] = to_email
    msg.set_content(
        "This is an automated email. LLM Chat Report can be found in the attachment."
    )
    msg.add_attachment(
        pdf, maintype="application", subtype="pdf", filename="report.pdf"
    )

    send_message_via_smtp_server(msg=msg)
