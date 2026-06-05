from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_notification_email(
    recipient_email: str,
    title: str,
    body: str,
) -> None:
    """Celery task: send an e-mail notification via SMTP.

    Reads SMTP config from settings (INV-05 — no hardcoded credentials).
    Retried automatically by Celery (max_retries=3, backoff) on SMTP failure.
    """
    from app.core.config import settings

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = title
    msg["From"] = settings.SMTP_FROM
    msg["To"] = recipient_email

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                smtp.starttls()
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.sendmail(settings.SMTP_FROM, [recipient_email], msg.as_string())
        logger.info("E-mail sent to %s (subject=%r)", recipient_email, title)
    except Exception:
        logger.exception("Failed to send e-mail to %s", recipient_email)
        raise


def _register_tasks() -> None:
    from app.core.celery_app import celery_app

    celery_app.task(
        name="app.modules.notifications.tasks.send_notification_email",
        bind=False,
        max_retries=3,
        default_retry_delay=60,
    )(send_notification_email)


_register_tasks()
