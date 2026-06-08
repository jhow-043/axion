"""Tests for app.modules.notifications.tasks — e-mail delivery via SMTP."""
from __future__ import annotations

import smtplib
from unittest.mock import MagicMock, patch

import pytest

from app.modules.notifications.tasks import send_notification_email


# ── happy path ─────────────────────────────────────────────────────────────────


def test_send_email_no_auth():
    """Sends e-mail without login when SMTP credentials are absent."""
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp.__exit__ = MagicMock(return_value=False)

    with (
        patch("smtplib.SMTP", return_value=mock_smtp),
        patch("app.core.config.settings") as mock_settings,
    ):
        mock_settings.SMTP_HOST = "localhost"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = None
        mock_settings.SMTP_PASSWORD = None
        mock_settings.SMTP_FROM = "noreply@test.local"

        send_notification_email("user@example.com", "Subject", "Body text")

    mock_smtp.sendmail.assert_called_once()
    mock_smtp.starttls.assert_not_called()
    mock_smtp.login.assert_not_called()


def test_send_email_with_auth():
    """Performs starttls + login when credentials are present."""
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp.__exit__ = MagicMock(return_value=False)

    with (
        patch("smtplib.SMTP", return_value=mock_smtp),
        patch("app.core.config.settings") as mock_settings,
    ):
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "user"
        mock_settings.SMTP_PASSWORD = "pass"
        mock_settings.SMTP_FROM = "noreply@example.com"

        send_notification_email("dest@example.com", "Hello", "World")

    mock_smtp.starttls.assert_called_once()
    mock_smtp.login.assert_called_once_with("user", "pass")
    mock_smtp.sendmail.assert_called_once()


# ── error path ─────────────────────────────────────────────────────────────────


def test_send_email_smtp_error_reraises():
    """SMTP failures propagate so Celery can retry."""
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp.__exit__ = MagicMock(return_value=False)
    mock_smtp.sendmail.side_effect = smtplib.SMTPException("connection refused")

    with (
        patch("smtplib.SMTP", return_value=mock_smtp),
        patch("app.core.config.settings") as mock_settings,
    ):
        mock_settings.SMTP_HOST = "localhost"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = None
        mock_settings.SMTP_PASSWORD = None
        mock_settings.SMTP_FROM = "noreply@test.local"

        with pytest.raises(smtplib.SMTPException):
            send_notification_email("user@example.com", "Sub", "Bod")
