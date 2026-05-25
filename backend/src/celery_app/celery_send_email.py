import smtplib
from email.mime.text import MIMEText

import resend

from src.celery_app.celery_main import celery_app
from src.core.config import config
from src.logger import logger


def _log_email_body(provider: str, email: str, subject: str, body: str) -> None:
    """Always log the outgoing email body to the worker logs.

    This makes development without a configured email provider painless --
    the dev can copy the confirmation link out of the worker logs.
    """
    logger.info(
        "[email/%s] to=%s subject=%r\n--- body ---\n%s\n--- end body ---",
        provider, email, subject, body,
    )


@celery_app.task
def send_confirm_email(email: str, subject: str, body: str):
    """Send confirmation email via SMTP (Gmail).

    Falls back to a log-only delivery if SMTP fails so registration always
    succeeds from the API's point of view.
    """
    _log_email_body("smtp", email, subject, body)
    sender_email = config.get_sender_email()
    email_app_password = config.get_email_app_password()

    if not sender_email or not email_app_password:
        logger.warning("SMTP not configured -- skipping send (body already logged)")
        return

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.login(sender_email, email_app_password)
            server.sendmail(sender_email, [email], msg.as_string())
    except Exception as exc:
        # Don't crash the worker on a provider misconfiguration -- the
        # email body is already in the logs above for the dev to use.
        logger.warning("SMTP send failed: %s (body already logged)", exc)


@celery_app.task
def send_confirm_email_resend(email: str, subject: str, body: str):
    """Send confirmation email via Resend API.

    Falls back to a log-only delivery if Resend rejects the request (e.g.
    unverified sender domain) so registration always succeeds.
    """
    _log_email_body("resend", email, subject, body)
    api_key = config.get_resend_api_key()
    sender = config.get_sender_email()

    if not api_key or not sender:
        logger.warning("Resend not configured -- skipping send (body already logged)")
        return

    try:
        resend.api_key = api_key
        params: resend.Emails.SendParams = {
            "from": sender,
            "to": [email],
            "subject": subject,
            "text": body,
        }
        resend.Emails.send(params)
    except Exception as exc:
        # Don't crash the worker on a provider misconfiguration -- the
        # email body is already in the logs above for the dev to use.
        logger.warning("Resend send failed: %s (body already logged)", exc)
