"""
FastAPI Notification Emitter.

Module này generate FastAPI code cho CP12 Notification Emitter:
- NotificationService: Service class cho notification dispatch
- NotificationController: API routes cho notification operations
- Pydantic models: Request/Response schemas
- Background tasks: Async dispatch tasks
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GeneratedFile:
    """File đã generate từ emitter."""
    path: Path
    content: str
    template: str
    capability: str = "CP12"


class FastAPINotificationEmitter:
    """
    Emitter generate FastAPI code cho notification.

    Generate:
    - notification_service.py: Service class
    - notification_router.py: API routes
    - notification_models.py: Pydantic models
    - notification_tasks.py: Background tasks
    """

    def generate(self) -> dict[str, str]:
        """
        Generate toàn bộ FastAPI notification code.

        Returns:
            Dict mapping file_path -> code content
        """
        return {
            "app/services/notification_service.py": self.generate_service(),
            "app/api/v1/notification_router.py": self.generate_router(),
            "app/schemas/notification_models.py": self.generate_models(),
            "app/tasks/notification_tasks.py": self.generate_tasks(),
        }

    def generate_service(self, templates: list[Any] | None = None) -> str:
        """Generate NotificationService class."""
        return textwrap.dedent('''\
            """
            Notification Service — CP12: Notification & Communication Generator.

            Service này xử lý notification dispatch cho đa kênh (email, SMS, push).
            """

            from __future__ import annotations

            import logging
            import re
            from dataclasses import dataclass, field
            from datetime import datetime
            from enum import Enum
            from typing import Any

            logger = logging.getLogger(__name__)


            class NotificationChannel(str, Enum):
                """Các kênh notification được hỗ trợ."""
                EMAIL = "email"
                SMS = "sms"
                PUSH = "push"
                WEBHOOK = "webhook"
                IN_APP = "in_app"


            @dataclass
            class NotificationTemplate:
                """Notification template với variable interpolation."""
                template_id: str
                channel: NotificationChannel
                subject: str = ""
                body_html: str = ""
                body_text: str = ""
                variables: list[str] = field(default_factory=list)
                locale: str = "en"

                def render(self, data: dict[str, Any]) -> dict[str, Any]:
                    """Render template với variable values."""
                    result = {
                        "subject": self.subject,
                        "body_html": self.body_html,
                        "body_text": self.body_text,
                    }
                    pattern = re.compile(r"\\{\\{(\\w+)\\}\\}")
                    for key in ["subject", "body_html", "body_text"]:
                        text = result[key]
                        def _replace(match: re.Match) -> str:
                            var_name = match.group(1)
                            return str(data[var_name]) if var_name in data else match.group(0)
                        result[key] = pattern.sub(_replace, text)
                    return result


            @dataclass
            class RateLimiter:
                """Rate limiter cho notification dispatch."""
                default_limit: int = 10
                window_seconds: float = 3600.0
                _records: dict = field(default_factory=dict)

                def check_limit(self, recipient: str, channel: str) -> bool:
                    """Kiểm tra rate limit per recipient per channel."""
                    key = f"{recipient}:{channel}"
                    now = datetime.now().timestamp()
                    if key not in self._records or now - self._records[key]["start"] >= self.window_seconds:
                        self._records[key] = {"count": 1, "start": now}
                        return True
                    if self._records[key]["count"] >= self.default_limit:
                        raise ValueError(
                            f"MDC-CP12-006: Vượt rate limit cho {recipient} trên {channel}"
                        )
                    self._records[key]["count"] += 1
                    return True


            class NotificationService:
                """
                Service chính cho notification dispatch.

                Xử lý:
                - Template management (CRUD)
                - Multi-channel dispatch (email, SMS, push)
                - Rate limiting per recipient
                - Template rendering với variable interpolation
                """

                def __init__(self) -> None:
                    """Khởi tạo NotificationService với template registry và rate limiter."""
                    self._templates: dict[str, NotificationTemplate] = {}
                    self._rate_limiter = RateLimiter()
                    self._dispatch_log: list[dict[str, Any]] = []

                def register_template(self, template: NotificationTemplate) -> None:
                    """Đăng ký notification template."""
                    self._templates[template.template_id] = template

                def get_template(self, template_id: str) -> NotificationTemplate | None:
                    """Lấy template theo ID."""
                    return self._templates.get(template_id)

                def list_templates(self) -> list[dict[str, Any]]:
                    """Liệt kê tất cả templates."""
                    return [t.to_dict() if hasattr(t, 'to_dict') else {
                        "template_id": t.template_id,
                        "channel": t.channel.value,
                        "subject": t.subject,
                    } for t in self._templates.values()]

                async def send_email(
                    self,
                    recipient: str,
                    template_id: str,
                    payload: dict[str, Any] | None = None,
                ) -> dict[str, Any]:
                    """
                    Gửi email notification.

                    Args:
                        recipient: Email address người nhận
                        template_id: ID của template
                        payload: Variable values cho template rendering

                    Returns:
                        Dispatch result với status

                    Raises:
                        ValueError: Nếu template không tìm thấy hoặc vượt rate limit
                    """
                    template = self._templates.get(template_id)
                    if not template:
                        raise ValueError(f"MDC-CP12-002: Template not found: {template_id}")

                    # Kiểm tra rate limit
                    self._rate_limiter.check_limit(recipient, "email")

                    # Render template
                    data = payload or {}
                    rendered = template.render(data)

                    # Dispatch email
                    result = await self._dispatch_email(recipient, rendered)

                    # Log dispatch
                    self._dispatch_log.append({
                        "template_id": template_id,
                        "recipient": recipient,
                        "channel": "email",
                        "status": result.get("status", "unknown"),
                        "timestamp": datetime.now().isoformat(),
                    })

                    return result

                async def send_sms(
                    self,
                    recipient: str,
                    template_id: str,
                    payload: dict[str, Any] | None = None,
                ) -> dict[str, Any]:
                    """
                    Gửi SMS notification.

                    Args:
                        recipient: Số điện thoại người nhận
                        template_id: ID của template
                        payload: Variable values cho template rendering

                    Returns:
                        Dispatch result với status
                    """
                    template = self._templates.get(template_id)
                    if not template:
                        raise ValueError(f"MDC-CP12-002: Template not found: {template_id}")

                    self._rate_limiter.check_limit(recipient, "sms")

                    data = payload or {}
                    rendered = template.render(data)

                    result = await self._dispatch_sms(recipient, rendered)

                    self._dispatch_log.append({
                        "template_id": template_id,
                        "recipient": recipient,
                        "channel": "sms",
                        "status": result.get("status", "unknown"),
                        "timestamp": datetime.now().isoformat(),
                    })

                    return result

                async def send_push(
                    self,
                    user_id: str,
                    template_id: str,
                    payload: dict[str, Any] | None = None,
                ) -> dict[str, Any]:
                    """
                    Gửi push notification.

                    Args:
                        user_id: User/device ID
                        template_id: ID của template
                        payload: Variable values cho template rendering

                    Returns:
                        Dispatch result với status
                    """
                    template = self._templates.get(template_id)
                    if not template:
                        raise ValueError(f"MDC-CP12-002: Template not found: {template_id}")

                    self._rate_limiter.check_limit(user_id, "push")

                    data = payload or {}
                    rendered = template.render(data)

                    result = await self._dispatch_push(user_id, rendered)

                    self._dispatch_log.append({
                        "template_id": template_id,
                        "recipient": user_id,
                        "channel": "push",
                        "status": result.get("status", "unknown"),
                        "timestamp": datetime.now().isoformat(),
                    })

                    return result

                async def _dispatch_email(
                    self,
                    recipient: str,
                    rendered: dict[str, Any],
                ) -> dict[str, Any]:
                    """Dispatch email notification (placeholder)."""
                    logger.info("Dispatching email to %s", recipient)
                    # TODO: Integrate với email provider (SMTP/SendGrid/SES)
                    return {"status": "sent", "recipient": recipient, "channel": "email"}

                async def _dispatch_sms(
                    self,
                    recipient: str,
                    rendered: dict[str, Any],
                ) -> dict[str, Any]:
                    """Dispatch SMS notification (placeholder)."""
                    logger.info("Dispatching SMS to %s", recipient)
                    # TODO: Integrate với SMS provider (Twilio)
                    return {"status": "sent", "recipient": recipient, "channel": "sms"}

                async def _dispatch_push(
                    self,
                    user_id: str,
                    rendered: dict[str, Any],
                ) -> dict[str, Any]:
                    """Dispatch push notification (placeholder)."""
                    logger.info("Dispatching push to %s", user_id)
                    # TODO: Integrate với push provider (Firebase FCM)
                    return {"status": "sent", "recipient": user_id, "channel": "push"}

                def get_dispatch_log(self) -> list[dict[str, Any]]:
                    """Lấy log dispatch gần đây."""
                    return self._dispatch_log[-100:]
            ''')

    def generate_router(self) -> str:
        """Generate API routes cho notification."""
        return textwrap.dedent('''\
            """
            Notification Router — CP12: API routes cho notification operations.

            Routes:
            - POST /notifications/dispatch: Dispatch notification
            - GET /notifications/templates: List templates
            - POST /notifications/templates: Register template
            - GET /notifications/log: Get dispatch log
            """

            from __future__ import annotations

            from fastapi import APIRouter, HTTPException
            from pydantic import BaseModel
            from typing import Any


            router = APIRouter(prefix="/notifications", tags=["notifications"])


            class DispatchRequest(BaseModel):
                """Schema cho dispatch request."""
                template_id: str
                recipient: str
                channel: str = "email"
                payload: dict[str, Any] | None = None


            class DispatchResponse(BaseModel):
                """Schema cho dispatch response."""
                status: str
                recipient: str
                channel: str
                message: str = ""


            class TemplateRequest(BaseModel):
                """Schema cho template registration."""
                template_id: str
                channel: str
                subject: str = ""
                body_html: str = ""
                body_text: str = ""
                variables: list[str] | None = None
                locale: str = "en"


            # Dependency injection cho NotificationService
            def get_notification_service():
                """Lấy instance của NotificationService."""
                from app.services.notification_service import NotificationService
                return NotificationService()


            @router.post("/dispatch", response_model=DispatchResponse)
            async def dispatch_notification(request: DispatchRequest):
                """
                Dispatch notification qua channel cụ thể.

                Support: email, sms, push
                """
                service = get_notification_service()
                try:
                    if request.channel == "email":
                        result = await service.send_email(
                            request.recipient,
                            request.template_id,
                            request.payload,
                        )
                    elif request.channel == "sms":
                        result = await service.send_sms(
                            request.recipient,
                            request.template_id,
                            request.payload,
                        )
                    elif request.channel == "push":
                        result = await service.send_push(
                            request.recipient,
                            request.template_id,
                            request.payload,
                        )
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=f"MDC-CP12-001: Channel không được hỗ trợ: {request.channel}",
                        )
                    return DispatchResponse(
                        status=result.get("status", "sent"),
                        recipient=request.recipient,
                        channel=request.channel,
                        message="Dispatch thành công",
                    )
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=str(e))


            @router.get("/templates")
            async def list_templates():
                """Liệt kê tất cả notification templates."""
                service = get_notification_service()
                return service.list_templates()


            @router.post("/templates")
            async def register_template(request: TemplateRequest):
                """Đăng ký notification template mới."""
                service = get_notification_service()
                from app.services.notification_service import NotificationTemplate, NotificationChannel
                template = NotificationTemplate(
                    template_id=request.template_id,
                    channel=NotificationChannel(request.channel),
                    subject=request.subject,
                    body_html=request.body_html,
                    body_text=request.body_text,
                    variables=request.variables or [],
                    locale=request.locale,
                )
                service.register_template(template)
                return {"status": "registered", "template_id": request.template_id}


            @router.get("/log")
            async def get_dispatch_log(limit: int = 50):
                """Lấy dispatch log gần đây."""
                service = get_notification_service()
                log = service.get_dispatch_log()
                return {"log": log[-limit:], "total": len(log)}
            ''')

    def generate_models(self) -> str:
        """Generate Pydantic models cho notification."""
        return textwrap.dedent('''\
            """
            Notification Models — CP12: Pydantic schemas cho notification API.

            Schemas:
            - DispatchRequest: Schema cho dispatch request
            - DispatchResponse: Schema cho dispatch response
            - TemplateRequest: Schema cho template registration
            - TemplateResponse: Schema cho template response
            """

            from __future__ import annotations

            from enum import Enum
            from typing import Any

            from pydantic import BaseModel, Field


            class ChannelType(str, Enum):
                """Các loại channel được hỗ trợ."""
                EMAIL = "email"
                SMS = "sms"
                PUSH = "push"
                WEBHOOK = "webhook"
                IN_APP = "in_app"


            class DispatchRequest(BaseModel):
                """Schema cho dispatch request."""
                template_id: str = Field(..., description="ID của template")
                recipient: str = Field(..., description="Người nhận (email, phone, user_id)")
                channel: ChannelType = Field(default=ChannelType.EMAIL, description="Channel gửi")
                payload: dict[str, Any] | None = Field(default=None, description="Variable values")

                class Config:
                    json_schema_extra = {
                        "example": {
                            "template_id": "welcome_email",
                            "recipient": "user@example.com",
                            "channel": "email",
                            "payload": {"name": "Minh"},
                        }
                    }


            class DispatchResponse(BaseModel):
                """Schema cho dispatch response."""
                status: str = Field(..., description="Status kết quả (sent, failed)")
                recipient: str = Field(..., description="Người nhận")
                channel: str = Field(..., description="Channel đã sử dụng")
                message: str = Field(default="", description="Message bổ sung")


            class TemplateRequest(BaseModel):
                """Schema cho template registration."""
                template_id: str = Field(..., description="ID duy nhất của template")
                channel: ChannelType = Field(..., description="Channel của template")
                subject: str = Field(default="", description="Subject line")
                body_html: str = Field(default="", description="HTML body")
                body_text: str = Field(default="", description="Plain text body")
                variables: list[str] | None = Field(default=None, description="Variable names")
                locale: str = Field(default="en", description="Locale code")


            class TemplateResponse(BaseModel):
                """Schema cho template response."""
                template_id: str
                channel: str
                subject: str
                locale: str
            ''')

    def generate_tasks(self) -> str:
        """Generate background tasks cho async dispatch."""
        return textwrap.dedent('''\
            """
            Notification Background Tasks — CP12: Async dispatch tasks.

            Tasks:
            - send_notification_task: Dispatch notification async
            - retry_failed_dispatches: Retry các dispatch thất bại
            - cleanup_old_logs: Xóa dispatch log cũ
            """

            from __future__ import annotations

            import asyncio
            import logging
            from datetime import datetime, timedelta
            from typing import Any

            logger = logging.getLogger(__name__)


            async def send_notification_task(
                template_id: str,
                recipient: str,
                channel: str,
                payload: dict[str, Any] | None = None,
            ) -> dict[str, Any]:
                """
                Background task cho async notification dispatch.

                Args:
                    template_id: ID của template
                    recipient: Người nhận
                    channel: Channel gửi
                    payload: Variable values

                Returns:
                    Dispatch result
                """
                try:
                    from app.services.notification_service import NotificationService
                    service = NotificationService()

                    if channel == "email":
                        result = await service.send_email(recipient, template_id, payload)
                    elif channel == "sms":
                        result = await service.send_sms(recipient, template_id, payload)
                    elif channel == "push":
                        result = await service.send_push(recipient, template_id, payload)
                    else:
                        logger.error("Channel không được hỗ trợ: %s", channel)
                        return {"status": "failed", "error": f"Channel không hợp lệ: {channel}"}

                    logger.info(
                        "Notification dispatched: template=%s, recipient=%s, channel=%s, status=%s",
                        template_id, recipient, channel, result.get("status"),
                    )
                    return result

                except Exception as e:
                    logger.error(
                        "Notification dispatch failed: template=%s, recipient=%s, error=%s",
                        template_id, recipient, str(e),
                    )
                    return {"status": "failed", "error": str(e)}


            async def retry_failed_dispatches(max_retries: int = 3) -> int:
                """
                Retry các dispatch đã thất bại.

                Args:
                    max_retries: Số lần retry tối đa

                Returns:
                    Số dispatch đã retry thành công
                """
                logger.info("Starting retry for failed dispatches...")
                # TODO: Implement retry logic với dispatch log
                return 0


            async def cleanup_old_logs(days: int = 30) -> int:
                """
                Xóa dispatch log cũ.

                Args:
                    days: Số ngày giữ log

                Returns:
                    Số log đã xóa
                """
                logger.info("Cleaning up dispatch logs older than %d days...", days)
                # TODO: Implement log cleanup
                return 0
            ''')
