from __future__ import annotations

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("email")


class EmailService:
    def send_password_reset(self, to_email: str, reset_url: str) -> None:
        if settings.SMTP_HOST:
            self._send_smtp(to_email, reset_url)
            return
        logger.info("password_reset_link", to=to_email, url=reset_url)

    def _send_smtp(self, to_email: str, reset_url: str) -> None:
        import smtplib
        from email.message import EmailMessage

        message = EmailMessage()
        message["Subject"] = "Reset your DocuAsk password"
        message["From"] = settings.SMTP_FROM
        message["To"] = to_email
        message.set_content(
            f"Reset your DocuAsk password using this link (valid for 1 hour):\n\n{reset_url}\n"
        )
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
            smtp.starttls()
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)
