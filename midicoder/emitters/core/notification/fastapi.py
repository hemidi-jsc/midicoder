"""
FastAPI Notification Emitter Module.

Module này generate FastAPI code cho CP12 Notification Emitter:
- NotificationService: Service class với send_email, send_sms, send_push, send_webhook
- NotificationController: REST endpoints cho dispatch notifications
- Pydantic models: Request/Response schemas
- Celery tasks: Background tasks cho async dispatch

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from midicoder.emitters.core.notification.models import (
    NotificationChannel,
    NotificationTemplate,
)

# ============================================================================
# FastAPI Notification Emitter
# ============================================================================


class FastAPINotificationEmitter:
    """
    Emitter cho FastAPI notification code.

    Generate các file Python cho notification system bao gồm:
    - Service class (NotificationService)
    - Controller (FastAPI router)
    - Pydantic models
    - Celery background tasks
    """

    def generate_service(self, templates: list[NotificationTemplate] | None = None) -> str:
        """
        Generate NotificationService class code.

        Tao service class voi:
        - TemplateRenderer: Render templates voi {{variable}} interpolation
        - RateLimiter: Rate limiting per recipient per channel
        - RetryPolicy: Exponential backoff cho provider calls
        - Concrete providers: SendGrid, AWS SES, Twilio, Firebase FCM

        Args:
            templates: List templates (optional, dung de generate type hints)

        Returns:
            String chua Python code cho NotificationService
        """
        code = '''"""
Notification Service Module.

Module nay cung cap NotificationService cho viec dispatch notifications
qua cac kênh: Email, SMS, Push, Webhook, In-App.

Tich hop:
- TemplateRenderer: Render templates voi {{variable}} va filters
- RateLimiter: Rate limiting per recipient per channel
- RetryPolicy: Exponential backoff cho provider calls
- Concrete providers: SendGrid, AWS SES, Twilio, Firebase FCM

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from fastapi import Depends
from midicoder.emitters.core.notification.template_engine import (
    TemplateRenderer, TemplateValidator, RenderedTemplate,
)
from midicoder.emitters.core.notification.i18n import I18nTemplateRegistry
from midicoder.emitters.core.notification.rate_limiter import RateLimiter
from midicoder.emitters.core.notification.retry_policy import RetryPolicy
from midicoder.emitters.core.notification.providers import (
    EmailGateway, SmsGateway, PushGateway,
    SendGridEmailGateway, AwsSesEmailGateway,
    TwilioSmsGateway, FirebasePushGateway,
)
from midicoder.emitters.core.notification.models import (
    NotificationChannel, NotificationTemplate, DispatchResult,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


logger = logging.getLogger(__name__)


@dataclass
class _RateRecord:
    """Record cho rate tracking."""
    count: int = 0
    window_start: float = field(default_factory=time.time)


class NotificationGateway(ABC):
    """
    Abstract gateway cho notification providers.

    Cac concrete provider (SendGrid, Twilio, Firebase) implement interface nay.
    """

    @abstractmethod
    async def send(self, recipient: str, subject: str, body: str, **kwargs: Any) -> DispatchResult:
        """Gui notification qua provider."""
        pass


class NotificationService:
    """
    Service chinh cho notification system.

    Quan ly templates, providers, va dispatch notifications qua cac kênh.
    Tich hop TemplateRenderer, RateLimiter, RetryPolicy.
    """

    def __init__(
        self,
        gateways: dict[NotificationChannel, list[NotificationGateway]] | None = None,
        rate_limits: dict[str, int] | None = None,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> None:
        """
        Khoi tao NotificationService.

        Args:
            gateways: Mapping channel -> list of gateway providers
            rate_limits: Rate limits per channel (requests per minute)
            max_retries: So lan retry toi da (default: 3)
            base_delay: Base delay cho retry (giay, default: 1.0)
        """
        self._gateways: dict[NotificationChannel, list[NotificationGateway]] = gateways or {}
        self._rate_limits: dict[str, int] = rate_limits or {
            "email": 100, "sms": 10, "push": 1000, "webhook": 100, "in_app": 1000,
        }
        self._templates: dict[str, NotificationTemplate] = {}
        self._dispatch_log: list[dict[str, Any]] = []

        # Tich hop TemplateRenderer
        self._renderer = TemplateRenderer()

        # Tich hop I18nTemplateRegistry
        self._i18n_registry = I18nTemplateRegistry()

        # Tich hop RateLimiter (in-memory)
        self._rate_records: dict[tuple[str, str], _RateRecord] = defaultdict(_RateRecord)

        # Tich hop RetryPolicy
        self._retry_policy = RetryPolicy(
            max_retries=max_retries,
            base_delay=base_delay,
        )

    def register_provider(
        self,
        channel: NotificationChannel,
        provider_type: str,
        config: dict[str, Any],
    ) -> None:
        """
        Dang ky concrete provider cho channel.

        Su dung concrete providers tu module providers:
        - SendGridEmailGateway, AwsSesEmailGateway (Email)
        - TwilioSmsGateway (SMS)
        - FirebasePushGateway (Push)

        Args:
            channel: Notification channel
            provider_type: Loai provider (sendgrid, ses, twilio, firebase)
            config: Configuration dict cho provider
        """
        gateway: EmailGateway | SmsGateway | PushGateway | None = None

        if provider_type == "sendgrid":
            gateway = SendGridEmailGateway(config)
        elif provider_type == "ses":
            gateway = AwsSesEmailGateway(config)
        elif provider_type == "twilio":
            gateway = TwilioSmsGateway(config)
        elif provider_type == "firebase":
            gateway = FirebasePushGateway(config)

        if gateway is not None:
            if channel not in self._gateways:
                self._gateways[channel] = []
            self._gateways[channel].append(gateway)  # type: ignore

    def register_template(
        self,
        template: NotificationTemplate,
    ) -> None:
        """
        Dang ky notification template.

        Template duoc luu theo template_id va locale (i18n support).

        Args:
            template: NotificationTemplate instance
        """
        self._templates[template.template_id] = template
        self._i18n_registry.register(
            template_id=template.template_id,
            locale=template.locale,
            template=template,
        )

    def register_template_legacy(
        self,
        template_id: str,
        channel: NotificationChannel,
        subject: str = "",
        body_html: str = "",
        body_text: str = "",
        variables: list[str] | None = None,
        locale: str = "en",
    ) -> None:
        """
        Dang ky notification template (legacy API).

        Args:
            template_id: Dinh danh duy nhat cua template
            channel: Channel de gui notification
            subject: Subject line (support {{variable}})
            body_html: HTML body content
            body_text: Plain text body content
            variables: Danh sach variables trong template
            locale: Locale code (BCP 47)
        """
        template = NotificationTemplate(
            template_id=template_id,
            channel=channel,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            variables=variables or [],
            locale=locale,
        )
        self.register_template(template)

    def render_template(
        self,
        template_id: str,
        data: dict[str, Any],
        locale: str | None = None,
    ) -> RenderedTemplate:
        """
        Render template voi variable values.

        Su dung TemplateRenderer de thay the {{variable}} trong template
        bang values tu data dict. Support filters va nested variables.

        Args:
            template_id: Template ID de render
            data: Variable values
            locale: Preferred locale (BCP 47)

        Returns:
            RenderedTemplate voi subject, body_html, body_text da render

        Raises:
            MidicoderError: Neu template khong tim thay
        """
        # Resolve template voi i18n fallback chain
        template = None

        if locale:
            template = self._i18n_registry.resolve(template_id, locale)

        if template is None:
            template = self._templates.get(template_id)

        if template is None:
            EM.raise_error(
                ErrorCode.CP12_NOTIFICATION_TEMPLATE_NOT_FOUND,
                template_id=template_id,
            )

        # Su dung TemplateRenderer
        return self._renderer.render(template, data)

    def _check_rate_limit(self, recipient: str, channel: str) -> bool:
        """
        Kiem tra rate limit cho recipient.

        Args:
            recipient: Recipient identifier
            channel: Channel name

        Returns:
            True neu con quota

        Raises:
            MidicoderError: Neu vuot rate limit
        """
        limit = self._rate_limits.get(channel, 100)
        key = (recipient, channel)
        now = time.time()
        record = self._rate_records[key]

        # Reset window neu da qua 1 phut
        if now - record.window_start >= 60:
            record.count = 0
            record.window_start = now

        if record.count >= limit:
            EM.raise_error(
                ErrorCode.CP12_NOTIFICATION_RATE_LIMIT_EXCEEDED,
                recipient=recipient,
                channel=channel,
                limit=limit,
                window_seconds=60,
            )

        record.count += 1
        return True

    def _dispatch_with_retry(
        self,
        func: Callable[..., DispatchResult],
        *args: Any,
        **kwargs: Any,
    ) -> DispatchResult:
        """
        Execute dispatch voi retry policy.

        Args:
            func: Function can execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            DispatchResult
        """
        return self._retry_policy.execute_with_retry(func, *args, **kwargs)

    async def send_email(self, recipient: str, subject: str, body_html: str, body_text: str = "", **kwargs: Any) -> DispatchResult:
        """
        Gui email notification voi rate limit va retry.

        Dispatch email qua provider gateway (SendGrid, SES, v.v.).
        Kiem tra rate limit truoc khi dispatch. Retry neu that bai.

        Args:
            recipient: Email address nguoi nhan
            subject: Email subject
            body_html: HTML email body
            body_text: Plain text email body
            **kwargs: Additional parameters

        Returns:
            DispatchResult voi status va provider response
        """
        channel = NotificationChannel.EMAIL
        dispatch_id = f"email_{datetime.utcnow().isoformat()}"

        # Kiem tra rate limit
        self._check_rate_limit(recipient, channel.value)

        try:
            gateways = self._gateways.get(channel, [])
            if not gateways:
                return DispatchResult(
                    dispatch_id=dispatch_id,
                    status="failed",
                    error_code="MDC-CP12-004",
                )

            gateway = gateways[0]

            # Dispatch voi retry policy
            def _do_send() -> DispatchResult:
                import asyncio
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(
                    gateway.send(recipient, subject, body_html, body_text, **kwargs)
                )

            result = self._dispatch_with_retry(_do_send)
            result.dispatch_id = dispatch_id

            logger.info("Email sent successfully: %s to %s", dispatch_id, recipient)
            return result

        except Exception as e:
            logger.error("Email dispatch failed: %s", str(e))
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-005",
            )

    async def send_sms(self, recipient: str, body_text: str, **kwargs: Any) -> DispatchResult:
        """
        Gui SMS notification voi rate limit va retry.

        Args:
            recipient: Phone number nguoi nhan
            body_text: SMS body text
            **kwargs: Additional parameters

        Returns:
            DispatchResult voi status va provider response
        """
        channel = NotificationChannel.SMS
        dispatch_id = f"sms_{datetime.utcnow().isoformat()}"

        # Kiem tra rate limit
        self._check_rate_limit(recipient, channel.value)

        try:
            gateways = self._gateways.get(channel, [])
            if not gateways:
                return DispatchResult(
                    dispatch_id=dispatch_id,
                    status="failed",
                    error_code="MDC-CP12-004",
                )

            gateway = gateways[0]
            result = await gateway.send(recipient, "", body_text, **kwargs)
            result.dispatch_id = dispatch_id

            logger.info("SMS sent successfully: %s to %s", dispatch_id, recipient)
            return result

        except Exception as e:
            logger.error("SMS dispatch failed: %s", str(e))
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-005",
            )

    async def send_push(self, recipient: str, title: str, body: str, **kwargs: Any) -> DispatchResult:
        """
        Gui push notification voi rate limit.

        Args:
            recipient: User/device ID
            title: Push notification title
            body: Push notification body
            **kwargs: Additional parameters (badge, sound, data)

        Returns:
            DispatchResult voi status va provider response
        """
        channel = NotificationChannel.PUSH
        dispatch_id = f"push_{datetime.utcnow().isoformat()}"

        # Kiem tra rate limit
        self._check_rate_limit(recipient, channel.value)

        try:
            gateways = self._gateways.get(channel, [])
            if not gateways:
                return DispatchResult(
                    dispatch_id=dispatch_id,
                    status="failed",
                    error_code="MDC-CP12-004",
                )

            gateway = gateways[0]
            result = await gateway.send(recipient, title, body, **kwargs)
            result.dispatch_id = dispatch_id

            logger.info("Push sent successfully: %s to %s", dispatch_id, recipient)
            return result

        except Exception as e:
            logger.error("Push dispatch failed: %s", str(e))
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-005",
            )

    async def send_webhook(self, url: str, payload: dict[str, Any], **kwargs: Any) -> DispatchResult:
        """
        Gui webhook notification.

        Dispatch HTTP POST request den webhook URL.

        Args:
            url: Webhook URL
            payload: JSON payload
            **kwargs: Additional parameters (headers, timeout)

        Returns:
            DispatchResult voi status va provider response
        """
        channel = NotificationChannel.WEBHOOK
        dispatch_id = f"webhook_{datetime.utcnow().isoformat()}"

        try:
            gateways = self._gateways.get(channel, [])
            if not gateways:
                return DispatchResult(
                    dispatch_id=dispatch_id,
                    status="failed",
                    error_code="MDC-CP12-004",
                )

            gateway = gateways[0]
            result = await gateway.send(url, "", str(payload), **kwargs)
            result.dispatch_id = dispatch_id

            logger.info("Webhook sent successfully: %s to %s", dispatch_id, url)
            return result

        except Exception as e:
            logger.error("Webhook dispatch failed: %s", str(e))
            return DispatchResult(
                dispatch_id=dispatch_id,
                status="failed",
                error_code="MDC-CP12-005",
            )

    async def dispatch(
        self,
        template_id: str,
        recipient: str,
        payload: dict[str, Any],
        channel: NotificationChannel | None = None,
        locale: str | None = None,
    ) -> DispatchResult:
        """
        Dispatch notification dua tren template.

        Render template voi TemplateRenderer va dispatch qua channel phù hop.
        Kiem tra rate limit va ap dung retry policy.

        Args:
            template_id: Template ID
            recipient: Nguoi nhan
            payload: Variable values cho template
            channel: Override channel (optional)
            locale: Preferred locale (BCP 47)

        Returns:
            DispatchResult
        """
        # Render template voi TemplateRenderer + i18n
        rendered = self.render_template(template_id, payload, locale=locale)
        template = self._templates.get(template_id)
        if template is None:
            EM.raise_error(
                ErrorCode.CP12_NOTIFICATION_TEMPLATE_NOT_FOUND,
                template_id=template_id,
            )
        target_channel = channel or template.channel

        if target_channel == NotificationChannel.EMAIL:
            return await self.send_email(
                recipient, rendered.subject, rendered.body_html, rendered.body_text,
            )
        elif target_channel == NotificationChannel.SMS:
            return await self.send_sms(recipient, rendered.body_text)
        elif target_channel == NotificationChannel.PUSH:
            return await self.send_push(recipient, rendered.subject, rendered.body_text)
        elif target_channel == NotificationChannel.WEBHOOK:
            return await self.send_webhook(recipient, payload)
        else:
            EM.raise_error(
                ErrorCode.CP12_NOTIFICATION_CHANNEL_NOT_SUPPORTED,
                channel=target_channel.value,
            )


# Dependency injection
def get_notification_service() -> NotificationService:
    """Provider cho FastAPI dependency injection."""
    return NotificationService()
'''
        return code

    def generate_controller(self) -> str:
        """
        Generate FastAPI router cho notification endpoints.

        Returns:
            String chứa Python code cho FastAPI router
        """
        return '''"""
Notification Controller Module.

Module này cung cấp REST endpoints cho notification system:
- POST /api/notifications/dispatch - Dispatch single notification
- POST /api/notifications/batch - Batch dispatch notifications
- GET /api/notifications/{dispatch_id} - Get dispatch status

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .service import NotificationService, get_notification_service


router = APIRouter(prefix="/api/notifications", tags=["notifications"])


# ============================================================================
# Pydantic Models
# ============================================================================


class DispatchRequest(BaseModel):
    """Request schema cho dispatch notification."""
    template_id: str = Field(..., description="Template ID")
    recipient: str = Field(..., description="Người nhận")
    payload: dict[str, Any] = Field(default_factory=dict, description="Variable values")
    channel: str | None = Field(None, description="Override channel")


class BatchDispatchRequest(BaseModel):
    """Request schema cho batch dispatch."""
    dispatches: list[DispatchRequest] = Field(..., description="List dispatch requests")


class DispatchResponse(BaseModel):
    """Response schema cho dispatch result."""
    dispatch_id: str
    status: str
    error_code: str | None = None


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/dispatch", response_model=DispatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def dispatch_notification(
    request: DispatchRequest,
    service: NotificationService = Depends(get_notification_service),
) -> DispatchResponse:
    """
    Dispatch single notification.
    
    Gửi notification đơn qua channel phù hợp dựa trên template.
    """
    from .service import NotificationChannel

    channel = NotificationChannel(request.channel) if request.channel else None
    result = await service.dispatch(
        template_id=request.template_id,
        recipient=request.recipient,
        payload=request.payload,
        channel=channel,
    )
    return DispatchResponse(
        dispatch_id=result.dispatch_id,
        status=result.status,
        error_code=result.error_code,
    )


@router.post("/batch", response_model=list[DispatchResponse], status_code=status.HTTP_202_ACCEPTED)
async def batch_dispatch_notifications(
    request: BatchDispatchRequest,
    service: NotificationService = Depends(get_notification_service),
) -> list[DispatchResponse]:
    """
    Batch dispatch notifications.
    
    Gửi nhiều notifications cùng lúc (asynchronous).
    """
    from .service import NotificationChannel

    results: list[DispatchResponse] = []
    for item in request.dispatches:
        channel = NotificationChannel(item.channel) if item.channel else None
        result = await service.dispatch(
            template_id=item.template_id,
            recipient=item.recipient,
            payload=item.payload,
            channel=channel,
        )
        results.append(DispatchResponse(
            dispatch_id=result.dispatch_id,
            status=result.status,
            error_code=result.error_code,
        ))
    return results


@router.get("/{dispatch_id}", response_model=DispatchResponse)
async def get_dispatch_status(
    dispatch_id: str,
    service: NotificationService = Depends(get_notification_service),
) -> DispatchResponse:
    """
    Get dispatch status.
    
    Lấy status của một dispatch notification.
    """
    # TODO: Query dispatch log từ database
    return DispatchResponse(
        dispatch_id=dispatch_id,
        status="pending",
    )
'''

    def generate_models(self) -> str:
        """
        Generate Pydantic models cho notification.

        Returns:
            String chứa Python code cho Pydantic models
        """
        return '''"""
Notification Pydantic Models.

Module này định nghĩa request/response schemas cho notification endpoints.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DispatchRequest(BaseModel):
    """Request schema cho dispatch notification."""
    template_id: str = Field(..., description="Template ID")
    recipient: str = Field(..., description="Người nhận")
    payload: dict[str, Any] = Field(default_factory=dict, description="Variable values")
    channel: str | None = Field(None, description="Override channel")


class BatchDispatchRequest(BaseModel):
    """Request schema cho batch dispatch."""
    dispatches: list[DispatchRequest] = Field(..., description="List dispatch requests")


class DispatchResponse(BaseModel):
    """Response schema cho dispatch result."""
    dispatch_id: str = Field(..., description="Dispatch ID")
    status: str = Field(..., description="Status: pending, sent, failed, bounced")
    error_code: str | None = Field(None, description="Error code nếu failed")


class TemplateResponse(BaseModel):
    """Response schema cho template info."""
    template_id: str
    channel: str
    subject: str = ""
    locale: str = "en"
'''

    def generate_celery_tasks(self) -> str:
        """
        Generate Celery background tasks cho async dispatch.

        Returns:
            String chứa Python code cho Celery tasks
        """
        return '''"""
Notification Celery Tasks.

Module này định nghĩa background tasks cho async notification dispatch.
Sử dụng Celery để queue và execute notifications.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from typing import Any

from celery import Celery

logger = logging.getLogger(__name__)

# Celery app instance
celery_app = Celery("notifications")
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.timezone = "UTC"


@celery_app.task(bind=True, max_retries=3)
async def send_notification_task(
    self,
    template_id: str,
    recipient: str,
    payload: dict[str, Any],
    channel: str | None = None,
) -> dict[str, Any]:
    """
    Celery task cho async dispatch notification.
    
    Execute notification dispatch trong background worker.
    Auto-retry nếu failed (max 3 retries).
    
    Args:
        template_id: Template ID
        recipient: Người nhận
        payload: Variable values
        channel: Override channel
        
    Returns:
        Dict với dispatch result
    """
    from .service import NotificationService

    service = NotificationService()
    try:
        result = await service.dispatch(
            template_id=template_id,
            recipient=recipient,
            payload=payload,
            channel=channel,
        )
        return {
            "dispatch_id": result.dispatch_id,
            "status": result.status,
            "error_code": result.error_code,
        }
    except Exception as exc:
        logger.error("Notification task failed: %s", str(exc))
        # Retry sau 60 giây
        self.retry(exc=exc, countdown=60)


@celery_app.task
async def send_batch_task(dispatches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Celery task cho batch async dispatch.
    
    Args:
        dispatches: List của dispatch requests
        
    Returns:
        List của dispatch results
    """
    results = []
    for item in dispatches:
        result = await send_notification_task(
            template_id=item["template_id"],
            recipient=item["recipient"],
            payload=item.get("payload", {}),
            channel=item.get("channel"),
        )
        results.append(result)
    return results
'''

    def generate(self) -> dict[str, str]:
        """
        Generate toàn bộ notification files.

        Returns:
            Dictionary mapping file path -> code content
        """
        return {
            "notification/service.py": self.generate_service(),
            "notification/controller.py": self.generate_controller(),
            "notification/models.py": self.generate_models(),
            "notification/tasks.py": self.generate_celery_tasks(),
        }