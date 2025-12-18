from datetime import datetime
from fpdf import FPDF
import smtplib
from email.message import EmailMessage

class PrinterBrokenError(Exception):
    """Raised when the printer is broken"""
    pass


class EmptyReportError(Exception):
    """Raised when the report is empty"""
    pass


class EmptyEmailAddressError(Exception):
    """Raised when the passed email address is empty"""
    pass


class Report:
    llm: str | None = None
    date: str | None = None
    chat_map: dict[str, str] = {}

    def __init__(self, llm: str):
        self.llm = llm
        self.chat_map = {}

    def generate_date(self):
        self.date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

    def get_date(self) -> str | None:
        if self.date == None:
            self.generate_date()
        return self.date

    def add_entry(self, question: str, answer: str):
        self.chat_map[question] = answer

    def generate_pdf(self):
        pdf = FPDF(format="a4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "LLM Chat Report", ln=True, align="C")
        pdf.ln(5)

        # Metadata
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 8, f"LLM Model: {self.llm}", ln=True)
        pdf.cell(0, 8, f"Generated on: {self.get_date()}", ln=True)
        pdf.ln(10)

        # Chat History
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Chat History", ln=True)
        pdf.ln(3)

        pdf.set_font("Arial", size=12)

        for i, (question, answer) in enumerate(self.chat_map.items(), start=1):
            pdf.multi_cell(0, 8, f"Q{i}: {question}")
            pdf.ln(1)
            pdf.multi_cell(0, 8, f"A{i}: {answer}")
            pdf.ln(5)

        # Return PDF as bytes, to avoid temp files
        return bytes(pdf.output())
    
    def send_via_email(self, from_email: str, to_email: str):
        pdf = self.generate_pdf()

        # Create email
        msg = EmailMessage()
        msg['Subject'] = "LLM Chat Report"
        msg['From'] = from_email
        msg['To'] = to_email
        msg.set_content("This is an automated email. LLM Chat Report can be found in the attachment.")
        msg.add_attachment(pdf, maintype='application', subtype='pdf', filename='report.pdf')

        # Send email via local SMTP server (via mailhog)
        server = smtplib.SMTP("mailhog", 1025)
        server.set_debuglevel(1)
        server.send_message(msg)
        server.quit()

    def print(self, is_printer_broken: bool):
        if is_printer_broken:
            raise PrinterBrokenError(
                "Printer currently not available. Alternatively you can send the report per mail"
            )


def print_report(report: Report):
    """
    Prints the given report.

    Args:
        report (Report): The report to be printed.

    Raises:
        EmptyReportError: If the report is None or contains no content.
        PrinterBrokenError: If the printer fails during printing.
    """
    if report is None:
        raise EmptyReportError("No content available for this report. Please start a conversation and try again.")
    
    try:
        report.print(is_printer_broken = True)
    except PrinterBrokenError as e:
        raise(e)


def send_report_via_email(report: Report, to_email: str):
    """
    Send the given report via email.

    Args:
        report (Report): The report to be sent.
        to_email (str): Recipient email address.

    Raises:
        EmptyReportError: If the report is None or contains no content.
        EmptyEmailAddressError: If the recipient email address is empty.
    """
    if report is None:
        raise EmptyReportError("No content available for this report. Please start a conversation and try again.")
    if to_email is "":
        raise EmptyEmailAddressError("The email address is empty. Please enter a email address!")
    
    report.send_via_email('report@ragllm.uni-ulm.de', to_email)
