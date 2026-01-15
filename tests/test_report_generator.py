import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from zoneinfo import ZoneInfo

from extensions.report_generator import *

def test_report_init():
    report = Report(llm="gpt-4o")

    assert report.llm == "gpt-4o"
    assert report.date is None
    assert report.chat_map == {}

def test_generate_date_sets_date():
    report = Report(llm="gpt-4o")
    report.generate_date()

    assert report.date is not None


def test_get_date_generates_if_missing(monkeypatch):
    fixed_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("Europe/Berlin"))

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_dt

    monkeypatch.setattr("extensions.report_generator.datetime", FixedDatetime)

    report = Report(llm="gpt-4o")
    date = report.get_date()

    assert date == "2024-01-01 12:00:00"

def test_add_entry():
    report = Report(llm="gpt-4o")

    report.add_entry("What is AI?", "Artificial Intelligence")

    assert report.chat_map == {
        "What is AI?": "Artificial Intelligence"
    }

@patch("extensions.report_generator.FPDF")
def test_generate_pdf_returns_bytes(mock_fpdf):
    mock_pdf = MagicMock()
    mock_pdf.output.return_value = b"%PDF-1.4"

    mock_fpdf.return_value = mock_pdf

    report = Report(llm="gpt-4o")
    report.add_entry("Q1", "A1")

    pdf_bytes = report.generate_pdf()

    assert isinstance(pdf_bytes, bytes)
    mock_pdf.add_page.assert_called_once()

@patch("extensions.report_generator.smtplib.SMTP")
@patch.object(Report, "generate_pdf")
def test_send_via_email(mock_generate_pdf, mock_smtp):
    mock_generate_pdf.return_value = b"pdf-bytes"
    mock_server = MagicMock()
    mock_smtp.return_value = mock_server

    report = Report(llm="gpt-4o")

    report.send_via_email(
        from_email="from@test.com",
        to_email="to@test.com",
    )

    mock_generate_pdf.assert_called_once()
    mock_server.send_message.assert_called_once()
    mock_server.quit.assert_called_once()

def test_print_raises_printer_broken_error():
    report = Report(llm="gpt-4o")

    with pytest.raises(PrinterBrokenError):
        report.print(is_printer_broken=True)

def test_print_report_none():
    with pytest.raises(EmptyReportError):
        print_report(None)
    
def test_send_report_via_email_none_report():
    with pytest.raises(EmptyReportError):
        send_report_via_email(None, "test@example.com")
    
def test_send_report_via_email_empty_address():
    report = Report(llm="gpt-4o")

    with pytest.raises(EmptyEmailAddressError):
        send_report_via_email(report, "")

@patch.object(Report, "send_via_email")
def test_send_report_via_email_success(mock_send):
    report = Report(llm="gpt-4o")

    send_report_via_email(report, "user@example.com")

    mock_send.assert_called_once_with(
        "report@ragllm.uni-ulm.de",
        "user@example.com",
        user=None,
    )
