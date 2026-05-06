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

        Tạo service class với các methods:
        - send_email(): Gửi email qua provider
        - send_sms(): Gửi SMS qua provider
        - send_push(): Gửi push notification
        - send_webhook(): Gửi webhook HTTP POST
        - render_template(): Render template với variables

        Args:
            templates: List templates (optional, dùng để generate type hints)

        Returns:
            String chứa Python code cho NotificationService
        """
        code = '''"""
Notification Service Module.

Module này cung cấp NotificationService cho việc dispatch notifications
qua các kênh: Email, SMS, Push, Webhook, In-App.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import Depends
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Kênh notification."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


@dataclass
class DispatchResult:
    """Kết quả dispatch notification."""
    dispatch_id: str
    status: str  # sent, failed, bounced
    provider_response: dict[str, Any] | None = None
    error_code: str | None = None


class NotificationGateway(ABC):
    """
    Abstract gateway cho notification providers.
    
    Các concrete provider (SendGrid, Twilio, Firebase) implement interface này.
    """

    @abstractmethod
    async def send(self, recipient: str, subject: str, body: str, **kwargs: Any) -> DispatchResult:
        """Gửi notification qua provider."""
        pass


class NotificationService:
    """
    Service chính cho notification system.
    
    Quản lý templates, providers, và dispatch notifications qua các kênh.
    Support async dispatch qua Celery background tasks.
    """

    def __init__(
        self,
        gateways: dict[NotificationChannel, list[NotificationGateway]] | None = None,
        rate_limits: dict[str, int] | None = None,
    ) -> None:
        """
        Khởi tạo NotificationService.
        
        Args:
            gateways: Mapping channel -> list of gateway providers
            rate_limits: Rate limits per channel (requests per minute)
        """
        self._gateways: dict[NotificationChannel, list[NotificationGateway]] = gateways or {}
        self._rate_limits: dict[str, int] = rate_limits or {"email": 100, "sms": 10, "push": 1000, "webhook": 100, "in_app": 1000}
        self._templates: dict[str, dict[str, Any]] = {}
        self._dispatch_log: list[dict[str, Any]] = []

    def register_template(self, template_id: str, channel: NotificationChannel, subject: str = "", body_html: str = "", body_text: str = "", variables: list[str] | None = None) -> None:
        """
        Đăng ký notification template.
        
        Args:
            template_id: Định danh duy nhất của template
            channel: Channel để gửi notification
            subject: Subject line (support {{variable}})
            body_html: HTML body content
            body_text: Plain text body content
            variables: Danh sách variables trong template
        """
        self._templates[template_id] = {
            "template_id": template_id,
            "channel": channel,
            "subject": subject,
            "body_html": body_html,
            "body_text": body_text,
            "variables": variables or [],
        }

    def render_template(self, template_id: str, data: dict[str, Any]) -> dict[str, str]:
        """
        Render template với variable values.
        
        Thay thế {{variable}} trong template bằng values từ data dict.
        
        Args:
            template_id: Template ID để render
            data: Variable values
            
        Returns:
            Dict với subject, body_html, body_text đã render
            
        Raises:
            MidicoderError: Nếu template không tìm thấy
        """
        if template_id not in self._templates:
            EM.raise_error(
                ErrorCode.CP12_NOTIFICATION_TEMPLATE_NOT_FOUND,
                template_id=template_id
            )

        template = self._templates[template_id]
        pattern = re.compile(r"\\{\\{(\\w+)\\}\\}")

        result: dict[str, str] = {
            "subject": template["subject"],
            "body_html": template["body_html"],
            "body_text": template["body_text"],
        }

        for key in result:
            def _replacer(match: re.Match) -> str:
                var_name = match.group(1)
                if var_name in data:
                    return str(data[var_name])
                return match.group(0)
            result[key] = pattern.sub(_replacer, result[key])

        return result

    async def send_email(self, recipient: str, subject: str, body_html: str, **kwargs: Any) -> DispatchResult:
        """
        Gửi email notification.
        
        Dispatch email qua provider gateway (SendGrid, SES, v.v.).
        
        Args:
            recipient: Email address người nhận
            subject: Email subject
            body_html: HTML email body
            **kwargs: Additional parameters (from_email, reply_to, attachments)
            
        Returns:
            DispatchResult với status và provider response
        """
        channel = NotificationChannel.EMAIL
        dispatch_id = f"email_{datetime.utcnow().isoformat()}"

        try:
            gateways = self._gateways.get(channel, [])
            if not gateways:
                return DispatchResult(
                    dispatch_id=dispatch_id,
                    status="failed",
                    error_code="MDC-CP12-004",
                )

            # Lấy gateway có priority cao nhất
            gateway = gateways[0]
            result = await gateway.send(recipient, subject, body_html, **kwargs)
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
        Gửi SMS notification.
        
        Dispatch SMS qua provider gateway (Twilio, v.v.).
        
        Args:
            recipient: Phone number người nhận
            body_text: SMS body text
            **kwargs: Additional parameters
            
        Returns:
            DispatchResult với status và provider response
        """
        channel = NotificationChannel.SMS
        dispatch_id = f"sms_{datetime.utcnow().isoformat()}"

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
        Gửi push notification.
        
        Dispatch push notification qua provider (Firebase, APNs).
        
        Args:
            recipient: User/device ID
            title: Push notification title
            body: Push notification body
            **kwargs: Additional parameters (badge, sound, data)
            
        Returns:
            DispatchResult với status và provider response
        """
        channel = NotificationChannel.PUSH
        dispatch_id = f"push_{datetime.utcnow().isoformat()}"

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
        Gửi webhook notification.
        
        Dispatch HTTP POST request đến webhook URL.
        
        Args:
            url: Webhook URL
            payload: JSON payload
            **kwargs: Additional parameters (headers, timeout)
            
        Returns:
            DispatchResult với status và provider response
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
    ) -> DispatchResult:
        """
        Dispatch notification dựa trên template.
        
        Render template và dispatch qua channel phù hợp.
        
        Args:
            template_id: Template ID
            recipient: Người nhận
            payload: Variable values cho template
            channel: Override channel (optional)
            
        Returns:
            DispatchResult
        """
        rendered = self.render_template(template_id, payload)
        template = self._templates[template_id]
        target_channel = channel or template["channel"]

        if target_channel == NotificationChannel.EMAIL:
            return await self.send_email(recipient, rendered["subject"], rendered["body_html"])
        elif target_channel == NotificationChannel.SMS:
            return await self.send_sms(recipient, rendered["body_text"])
        elif target_channel == NotificationChannel.PUSH:
            return await self.send_push(recipient, rendered["subject"], rendered["body_text"])
        elif target_channel == NotificationChannel.WEBHOOK:
            return await self.send_webhook(recipient, payload)
        else:
            EM.raise_error(
                ErrorCode.CP12_NOTIFICATION_CHANNEL_NOT_SUPPORTED,
                channel=target_channel.value
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