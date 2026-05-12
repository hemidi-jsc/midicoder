"""
SMTP Email Gateway Provider.

Provider chính cho email notification, gửi email qua SMTP server native.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any

from midicoder.emitters.core.cp12_notification.models import DispatchResult
from midicoder.emitters.core.cp12_notification.providers.base import EmailGateway
from midicoder.errors import ErrorCode, MidicoderErrorManager

logger = logging.getLogger(__name__)


class SmtpEmailGateway(EmailGateway):
    """
    SMTP native email gateway.

    Gửi email qua SMTP server, hỗ trợ TLS authentication.

    Attributes:
        host: SMTP server hostname
        port: SMTP server port (default: 587)
        username: Authentication username
        password: Authentication password
        use_tls: Bật/tắt TLS encryption
        from_email: Default sender email address
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 587,
        username: str = "",
        password: str = "",
        use_tls: bool = True,
        from_email: str = "noreply@midicoder.dev",
    ) -> None:
        """
        Khởi tạo SMTP email gateway.

        Args:
            host: SMTP server hostname
            port: SMTP server port
            username: Authentication username
            password: Authentication password
            use_tls: Bật/tắt TLS encryption
            from_email: Default sender email address
        """
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._use_tls = use_tls
        self._from_email = from_email

    def send(
        self,
        recipient: str,
        subject: str,
        body_html: str,
        body_text: str = "",
        **kwargs: Any,
    ) -> DispatchResult:
        """
        Gửi email qua SMTP server.

        Args:
            recipient: Email address người nhận
            subject: Subject line
            body_html: HTML body content
            body_text: Plain text body content
            **kwargs: Additional parameters (from_email, cc, bcc)

        Returns:
            DispatchResult với status và provider response
        """
        dispatch_id = kwargs.pop("dispatch_id", "unknown")

        # Override from_email nếu có trong kwargs
        from_email = kwargs.pop("from_email", self._from_email)

        try:
            # Tạo email message
            msg = MIMEMultipart("alternative")
            msg["From"] = from_email
            msg["To"] = recipient
            msg["Subject"] = subject

            if body_text:
                msg.attach(MIMEText(body_text, "plain"))
            if body_html:
                msg.attach(MIMEText(body_html, "html"))

            # Kết nối SMTP server
            if self._use_tls:
                server = smtplib.SMTP(self._host, self._port, timeout=30)
                server.ehlo()
                server.starttls()
                server.ehlo()
            else:
                server = smtplib.SMTP(self._host, self._port, timeout=30)

            # Auth nếu có credentials
            if self._username and self._password:
                server.login(self._username, self._password)

            # Gửi email
            server.sendmail(from_email, [recipient], msg.as_string())
            server.quit()

            return DispatchResult(
                dispatch_id=dispatch_id,
                status="sent",
                provider_response={"to": recipient, "from": from_email},
            )

        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP auth failed for %s", self._username)
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-004",
            )
        except smtplib.SMTPRecipientsRefused:
            logger.error("Recipient refused: %s", recipient)
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-007",
            )
        except (smtplib.SMTPException, ConnectionError, OSError) as e:
            logger.error("SMTP send failed: %s", str(e))
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-005",
            )
