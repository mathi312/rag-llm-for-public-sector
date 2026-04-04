import pytest
from unittest.mock import patch, MagicMock
from email.message import EmailMessage

from extensions.report_generator.report_generator import *
from domain.report.report import Report

def test_print_report_raises_error_when_report_is_none():
    with pytest.raises(EmptyReportError):
        print_report(report=None)

def test_print_report_raises_error_when_printer_is_broken():
    report = Report(llm="llama3.2")

    with pytest.raises(PrinterBrokenError):
        print_report(report=report, is_printer_broken=True)

def test_print_report_succeeds_when_printer_works():
    report = Report(llm="llama3.2")

    # Should not raise
    print_report(report=report, is_printer_broken=False)

def test_send_report_raises_error_when_report_is_none():
    with pytest.raises(EmptyReportError):
        send_report_via_email(report=None, to_email="test@example.com")

def test_send_report_raises_error_when_email_is_empty():
    report = Report(llm="llama3.2")

    with pytest.raises(EmptyEmailAddressError):
        send_report_via_email(report=report, to_email="")

@patch("extensions.report_generator.report_generator.send_message_via_smtp_server")
def test_send_report_sends_email(smtp_mock):
    smtp_mock.return_value = None
    report = Report(llm="llama3.2")
    report.add_entry("Q", "A")
    report.to_pdf = MagicMock(return_value=b"%PDF-dummy")

    send_report_via_email(report=report, to_email="test@test.com")

    smtp_mock.assert_called_once()
