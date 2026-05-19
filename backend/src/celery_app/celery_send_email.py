import smtplib
from email.mime.text import MIMEText

import resend

from src.celery_app.celery_main import celery_app
from src.core.config import config


@celery_app.task
def send_confirm_email(email: str, subject: str, body: str):
    """Send confirmation email via SMTP (Gmail)."""
    sender_email = config.get_sender_email()
    email_app_password = config.get_email_app_password()

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
        server.login(sender_email, email_app_password)
        server.sendmail(sender_email, [email], msg.as_string())


@celery_app.task
def send_confirm_email_resend(email: str, subject: str, body: str):
    """Send confirmation email via Resend API."""
    resend.api_key = config.get_resend_api_key()

    params: resend.Emails.SendParams = {
        "from": config.get_sender_email(),
        "to": [email],
        "subject": subject,
        "text": body,
    }

    resend.Emails.send(params)
