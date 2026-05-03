import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_owner_notification(to_email: str, meeting_title: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = f"Meeting bundle ready: {meeting_title}"
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg.set_content("Your meeting bundle is ready for review/approval.")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.send_message(msg)
