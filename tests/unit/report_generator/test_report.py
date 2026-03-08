import pytest
import re

from typing import Any
from unittest.mock import patch, MagicMock
from extensions.report_generator.report import Report
from extensions.user import User


def test_report_initialization():
    report = Report(llm="llama3.2")

    assert report.llm == "llama3.2"
    assert report.chat_history == {}

def test_add_entry_adds_to_chat_history():
    report = Report(llm="llama3.2")

    report.add_entry("What is AI?", "Artificial Intelligence")

    assert len(report.chat_history) == 1
    assert report.chat_history["What is AI?"] == "Artificial Intelligence"

def test_add_entry_overwrites_existing_question():
    report = Report(llm="llama3.2")

    report.add_entry("Q", "A1")
    report.add_entry("Q", "A2")

    assert len(report.chat_history) == 1
    assert report.chat_history["Q"] == "A2"

def test_timestamp_format():
    report = Report(llm="llama3.2")

    timestamp = report.timestamp()

    # Expected format: YYYY-MM-DD HH:MM:SS
    assert isinstance(timestamp, str)
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", timestamp)

def test_none_does_not_set_id_type():
    report = Report(llm="llama3.2")
    report.add_id_type(None)
    assert report.id_type is None

def test_sets_id_type_with_valid_string():
    report = Report(llm="llama3.2")
    report.add_id_type("passport")
    assert report.id_type == "passport"

def test_none_does_not_overwrite_existing_id_type():
    report = Report(llm="llama3.2")
    report.add_id_type("passport")
    report.add_id_type(None)
    assert report.id_type == "passport"

def test_overwrites_existing_id_type():
    report = Report(llm="llama3.2")
    report.add_id_type("passport")
    report.add_id_type("drivers_license")
    assert report.id_type == "drivers_license"

@patch("extensions.report_generator.report.FPDF")
def test_to_pdf_returns_bytes_without_user(mock_fpdf):
    mock_pdf = MagicMock()
    mock_pdf.output.return_value = b"%PDF-1.4"

    mock_fpdf.return_value = mock_pdf

    report = Report(llm="llama3.2")
    report.add_entry("What is AI?", "Artificial Intelligence")

    pdf_bytes = report.to_pdf()

    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 0
    mock_pdf.add_page.assert_called_once()

@patch("extensions.report_generator.report.FPDF")
def test_to_pdf_returns_bytes_with_user(mock_fpdf):
    mock_pdf = MagicMock()
    mock_pdf.output.return_value = b"%PDF-1.4"

    mock_fpdf.return_value = mock_pdf

    report = Report(llm="llama3.2")
    report.add_entry("What is AI?", "Artificial Intelligence")

    user = User(
        id="123456",
        email="alice@example.com",
        name="alice",
        is_admin=True,
    )

    pdf_bytes = report.to_pdf(user=user)

    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 0
    mock_pdf.add_page.assert_called_once()

@patch("extensions.report_generator.report.FPDF")
def test_to_pdf_returns_bytes_with_id_type(mock_fpdf):
    mock_pdf = MagicMock()
    mock_pdf.output.return_value = b"%PDF-1.4"

    mock_fpdf.return_value = mock_pdf

    report = Report(llm="llama3.2")
    report.add_entry("What is AI?", "Artificial Intelligence")
    report.add_id_type("ID Card")

    pdf_bytes = report.to_pdf()

    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 0
    mock_pdf.add_page.assert_called_once()
