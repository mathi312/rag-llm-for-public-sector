import pytest
import smtplib
from email.message import EmailMessage
from unittest.mock import MagicMock, patch, call
import os

from infrastructure.smtp_server import send_message_via_smtp_server
from infrastructure.smtp_server.smtp_server import _send_mail_via_mailhog, _send_via_smtp

MODULE = "infrastructure.smtp_server.smtp_server"


@pytest.fixture
def sample_email():
    msg = EmailMessage()
    msg["From"] = "sender@test.com"
    msg["To"] = "recipient@test.com"
    msg["Subject"] = "Test Subject"
    msg.set_content("Test body")
    return msg


class TestSendMessageViaSmtpServer:

    def test_routes_to_mailhog_in_development(self, sample_email):
        with patch.dict(os.environ, {"APP_ENV": "development"}):
            with patch(f"{MODULE}._send_mail_via_mailhog") as mock_mailhog:
                send_message_via_smtp_server(sample_email)
                mock_mailhog.assert_called_once_with(msg=sample_email)

    def test_routes_to_smtp_in_production(self, sample_email):
        with patch.dict(os.environ, {"APP_ENV": "production"}):
            with patch(f"{MODULE}._send_via_smtp") as mock_smtp:
                send_message_via_smtp_server(sample_email)
                mock_smtp.assert_called_once_with(msg=sample_email)

    def test_routes_to_smtp_when_app_env_not_set(self, sample_email):
        env = {k: v for k, v in os.environ.items() if k != "APP_ENV"}
        with patch.dict(os.environ, env, clear=True):
            with patch(f"{MODULE}._send_via_smtp") as mock_smtp:
                send_message_via_smtp_server(sample_email)
                mock_smtp.assert_called_once_with(msg=sample_email)

    def test_does_not_call_smtp_in_development(self, sample_email):
        with patch.dict(os.environ, {"APP_ENV": "development"}):
            with patch(f"{MODULE}._send_mail_via_mailhog"):
                with patch(f"{MODULE}._send_via_smtp") as mock_smtp:
                    send_message_via_smtp_server(sample_email)
                    mock_smtp.assert_not_called()

    def test_does_not_call_mailhog_in_production(self, sample_email):
        with patch.dict(os.environ, {"APP_ENV": "production"}):
            with patch(f"{MODULE}._send_via_smtp"):
                with patch(f"{MODULE}._send_mail_via_mailhog") as mock_mailhog:
                    send_message_via_smtp_server(sample_email)
                    mock_mailhog.assert_not_called()


class TestSendMailViaMailhog:

    @patch("smtplib.SMTP")
    def test_sends_message_successfully(self, mock_smtp_cls, sample_email):
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server

        _send_mail_via_mailhog(sample_email)

        mock_smtp_cls.assert_called_once_with("mailhog", 1025)
        mock_server.send_message.assert_called_once_with(sample_email)

    @patch("smtplib.SMTP")
    def test_quits_server_after_success(self, mock_smtp_cls, sample_email):
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server

        _send_mail_via_mailhog(sample_email)

        mock_server.quit.assert_called_once()

    @patch("smtplib.SMTP")
    def test_quits_server_even_on_smtp_exception(self, mock_smtp_cls, sample_email):
        mock_server = MagicMock()
        mock_server.send_message.side_effect = smtplib.SMTPException("send failed")
        mock_smtp_cls.return_value = mock_server

        with pytest.raises(RuntimeError):
            _send_mail_via_mailhog(sample_email)

        mock_server.quit.assert_called_once()

    @patch("smtplib.SMTP")
    def test_raises_runtime_error_on_smtp_exception(self, mock_smtp_cls, sample_email):
        mock_server = MagicMock()
        mock_server.send_message.side_effect = smtplib.SMTPException("boom")
        mock_smtp_cls.return_value = mock_server

        with pytest.raises(RuntimeError, match="Failed to send email via MailHog: boom"):
            _send_mail_via_mailhog(sample_email)

    @patch("smtplib.SMTP")
    def test_sets_debug_level(self, mock_smtp_cls, sample_email):
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server

        _send_mail_via_mailhog(sample_email)

        mock_server.set_debuglevel.assert_called_once_with(1)


class TestSendViaSmtp:

    @pytest.fixture
    def smtp_env(self):
        return {
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user@gmail.com",
            "SMTP_PASSWORD": "secret",
        }

    @patch("smtplib.SMTP")
    def test_sends_message_successfully(self, mock_smtp_cls, sample_email, smtp_env):
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server

        with patch.dict(os.environ, smtp_env):
            _send_via_smtp(sample_email)

        mock_server.send_message.assert_called_once_with(sample_email)

    @patch("smtplib.SMTP")
    def test_connects_with_correct_host_and_port(self, mock_smtp_cls, sample_email, smtp_env):
        mock_smtp_cls.return_value = MagicMock()

        with patch.dict(os.environ, smtp_env):
            _send_via_smtp(sample_email)

        mock_smtp_cls.assert_called_once_with("smtp.gmail.com", 587)

    @patch("smtplib.SMTP")
    def test_uses_custom_host_and_port_from_env(self, mock_smtp_cls, sample_email):
        mock_smtp_cls.return_value = MagicMock()
        env = {"SMTP_HOST": "smtp.custom.com", "SMTP_PORT": "465",
               "SMTP_USER": "u", "SMTP_PASSWORD": "p"}

        with patch.dict(os.environ, env):
            _send_via_smtp(sample_email)

        mock_smtp_cls.assert_called_once_with("smtp.custom.com", 465)

    @patch("smtplib.SMTP")
    def test_calls_starttls_and_login(self, mock_smtp_cls, sample_email, smtp_env):
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server

        with patch.dict(os.environ, smtp_env):
            _send_via_smtp(sample_email)

        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user@gmail.com", "secret")

    @patch("smtplib.SMTP")
    def test_quits_server_after_success(self, mock_smtp_cls, sample_email, smtp_env):
        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server

        with patch.dict(os.environ, smtp_env):
            _send_via_smtp(sample_email)

        mock_server.quit.assert_called_once()

    @patch("smtplib.SMTP")
    def test_quits_server_even_on_exception(self, mock_smtp_cls, sample_email, smtp_env):
        mock_server = MagicMock()
        mock_server.send_message.side_effect = smtplib.SMTPException("fail")
        mock_smtp_cls.return_value = mock_server

        with patch.dict(os.environ, smtp_env):
            with pytest.raises(RuntimeError):
                _send_via_smtp(sample_email)

        mock_server.quit.assert_called_once()

    @patch("smtplib.SMTP")
    def test_raises_permission_error_on_auth_failure(self, mock_smtp_cls, sample_email, smtp_env):
        mock_server = MagicMock()
        mock_server.send_message.side_effect = smtplib.SMTPAuthenticationError(535, b"auth failed")
        mock_smtp_cls.return_value = mock_server

        with patch.dict(os.environ, smtp_env):
            with pytest.raises(PermissionError, match="SMTP authentication failed"):
                _send_via_smtp(sample_email)

    @patch("smtplib.SMTP")
    def test_raises_runtime_error_on_smtp_exception(self, mock_smtp_cls, sample_email, smtp_env):
        mock_server = MagicMock()
        mock_server.send_message.side_effect = smtplib.SMTPException("network error")
        mock_smtp_cls.return_value = mock_server

        with patch.dict(os.environ, smtp_env):
            with pytest.raises(RuntimeError, match="Failed to send email via SMTP: network error"):
                _send_via_smtp(sample_email)

    def test_raises_value_error_when_user_missing(self, sample_email):
        env = {"SMTP_PASSWORD": "secret"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="SMTP_USER and SMTP_PASSWORD"):
                _send_via_smtp(sample_email)

    def test_raises_value_error_when_password_missing(self, sample_email):
        env = {"SMTP_USER": "user@gmail.com"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="SMTP_USER and SMTP_PASSWORD"):
                _send_via_smtp(sample_email)
