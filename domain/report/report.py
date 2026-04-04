from typing import Dict
from zoneinfo import ZoneInfo
from datetime import datetime

from fpdf import FPDF

from domain.user.user import User

class Report:
    """The report that contains the chat history of the current session and the llm used."""
    llm: str
    chat_history: Dict[str, str]
    id_type: str | None
    timezone: str = "Europe/Berlin"

    def __init__(self, llm: str):
        """Initialize a report for a given LLM."""
        self.llm: str = llm
        self.chat_history: Dict[str, str] = {}
        self.id_type: str | None = None

    def timestamp(self) -> str:
        """Return the current timestamp formatted for the report."""
        return datetime.now(ZoneInfo(self.timezone)).strftime("%Y-%m-%d %H:%M:%S")

    def add_entry(self, question: str, answer: str) -> None:
        """Adds the question and the answer to the chat history."""
        self.chat_history[question] = answer

    def add_id_type(self, id_type: str | None) -> None:
        """Adds the type of ID provided to the chat history."""
        if id_type is None:
            return
        self.id_type = id_type

    def to_pdf(self, user: User | None = None):
        """Creates a pdf from the report and returns it as a bytes to avoid temp files."""
        pdf = FPDF(format="a4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "LLM Chat Report", ln=True, align="C")
        pdf.ln(5)

        # Metadata
        pdf.set_font("Arial", size=12)
        pdf.cell(90, 8, f"LLM Model: {self.llm}", ln=False)
        pdf.cell(0, 8, f"Generated on: {self.timestamp()}", ln=True)

        if user is not None:
            name = getattr(user, "name", "")
            is_admin =  bool(getattr(user, "is_admin", False))

            pdf.cell(60, 8, f"Username: {name}", ln=False)
            pdf.cell(90, 8, f"Email: {user.email}", ln=False)
            pdf.cell(0, 8, f"Admin: {'Yes' if is_admin else 'No'}", ln=True)

        if self.id_type is not None:
            pdf.cell(0, 8, f"ID provided: {self.id_type}", ln=True)
        else:
            pdf.cell(0, 8, "No ID provided", ln=True)

        pdf.ln(10)

        # Chat History
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Chat History", ln=True)
        pdf.ln(3)

        pdf.set_font("Arial", size=12)

        for i, (question, answer) in enumerate(self.chat_history.items(), start=1):
            pdf.multi_cell(0, 8, f"Q{i}: {question}")
            pdf.ln(1)
            pdf.multi_cell(0, 8, f"A{i}: {answer}")
            pdf.ln(5)

        # Return PDF as bytes, to avoid temp files
        return bytes(pdf.output())
