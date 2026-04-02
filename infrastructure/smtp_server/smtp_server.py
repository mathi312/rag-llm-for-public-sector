import smtplib
import os

from email.message import EmailMessage

def send_message_via_smtp_server(msg: EmailMessage):
    """Send an email message via the appropriate SMTP server based on environment."""
    if os.getenv("APP_ENV") == "development":
        #Send email via local SMTP server (via mailhog)
        _send_mail_via_mailhog(msg=msg)
    else:
        # Send email via real SMTP server (e.g. Gmail)
        _send_via_smtp(msg=msg)


def _send_mail_via_mailhog(msg: EmailMessage):
    """Send email via local MailHog SMTP server (development only)."""
    server = smtplib.SMTP("mailhog", 1025)
    server.set_debuglevel(1)
    try:
        server.send_message(msg)
    except smtplib.SMTPException as e:
        raise RuntimeError(f"Failed to send email via MailHog: {e}") from e
    finally:
        server.quit()


def _send_via_smtp(msg: EmailMessage) -> None:
    """Send email via real SMTP server using credentials from environment variables."""
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")

    if not user or not password:
        raise ValueError("SMTP_USER and SMTP_PASSWORD environment variables must be set")

    server = smtplib.SMTP(host, port)
    server.starttls()
    server.login(user, password)
    try:
        server.send_message(msg)
    except smtplib.SMTPAuthenticationError as e:
        raise PermissionError(f"SMTP authentication failed for user '{user}': {e}") from e
    except smtplib.SMTPException as e:
        raise RuntimeError(f"Failed to send email via SMTP: {e}") from e
    finally:
        server.quit()
