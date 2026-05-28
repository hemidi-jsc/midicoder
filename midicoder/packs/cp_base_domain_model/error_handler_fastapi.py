# coding: utf-8
"""
FastAPI Error Handler Emitter.

Emitter class để generate FastAPI global error handler code:
- error_handler_middleware.py.jinja2: Middleware middleware
- error_responses.py.jinja2: Standard error response models (Pydantic)

Theo SoT E07, template-based code generation với Jinja2.
Theo pack.yml B3: Standardized Error Response — file contributions.

Usage:
    from midicoder.packs.cp_base_domain_model import FastAPIErrorHandlerEmitter

    emitter = FastAPIErrorHandlerEmitter(stack_dir=Path("midicoder/stacks/fastapi/templates"))
    files = emitter.emit(error_handler, mappers, logging_config, notification_config)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from .error_handler_models import (
    ErrorLevel,
    ErrorHandlingStrategy,
    ErrorLoggingConfig,
    ErrorMapper,
    ErrorNotificationConfig,
    GlobalErrorHandler,
)


def _to_snake_case(name: str) -> str:
    """
    Chuyển PascalCase sang snake_case.

    Args:
        name: Tên cần chuyển

    Returns:
        Snake case string
    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class FastAPIErrorHandlerEmitter:
    """
    Emitter cho FastAPI Global Error Handler code generation.

    Generate code cho:
    - Error handler middleware (error_handler_middleware.py.jinja2)
    - Error response models (error_responses.py.jinja2)

    Usage:
        emitter = FastAPIErrorHandlerEmitter(stack_dir=Path("midicoder/stacks/fastapi/templates"))
        files = emitter.emit(error_handler, mappers, output_dir=Path("app/middleware"))
    """

    def __init__(self, stack_dir: Path) -> None:
        """
        Khởi tạo FastAPIErrorHandlerEmitter.

        Args:
            stack_dir: Đường dẫn đến templates directory
        """
        self._stack_dir = stack_dir
        self._env = Environment(
            loader=FileSystemLoader(str(stack_dir)),
            autoescape=True,
        )

    def emit(
        self,
        handler: GlobalErrorHandler,
        mappers: list[ErrorMapper] | None = None,
        logging_config: ErrorLoggingConfig | None = None,
        notification_config: ErrorNotificationConfig | None = None,
    ) -> dict[str, str]:
        """
        Emit global error handler code files.

        Args:
            handler: GlobalErrorHandler definition
            mappers: Danh sách ErrorMapper (exception → HTTP mapping)
            logging_config: ErrorLoggingConfig (optional)
            notification_config: ErrorNotificationConfig (optional)

        Returns:
            Dict của file path -> content
        """
        files: dict[str, str] = {}
        mappers = mappers or []

        # Prepare context
        context = self._prepare_context(
            handler, mappers, logging_config, notification_config
        )

        # Generate error handler middleware
        files["error_handler_middleware.py"] = self._render(
            "error_handler_middleware.py.jinja2", context
        )

        # Generate error responses
        files["error_responses.py"] = self._render(
            "error_responses.py.jinja2", context
        )

        return files

    def _prepare_context(
        self,
        handler: GlobalErrorHandler,
        mappers: list[ErrorMapper],
        logging_config: ErrorLoggingConfig | None,
        notification_config: ErrorNotificationConfig | None,
    ) -> dict[str, Any]:
        """
        Prepare template context từ Error Handler models.

        Args:
            handler: GlobalErrorHandler definition
            mappers: Danh sách ErrorMappers
            logging_config: ErrorLoggingConfig (optional)
            notification_config: ErrorNotificationConfig (optional)

        Returns:
            Context dict
        """
        return {
            "handler": handler,
            "handler_id": handler.id,
            "handler_name": handler.name,
            "handler_id_snake": _to_snake_case(handler.id),
            "strategy": handler.strategy,
            "strategy_value": handler.strategy.value,
            "log_level": handler.log_level,
            "log_level_value": handler.log_level.value,
            "include_stack_trace": handler.include_stack_trace,
            "custom_error_pages": handler.custom_error_pages,
            "default_error_message": handler.default_error_message,
            "sanitize_output": handler.sanitize_output,
            "cors_enabled": handler.cors_enabled,
            "mappers": mappers,
            "mappers_dict": {
                m.exception_type: {
                    "http_status": m.http_status,
                    "error_code": m.error_code,
                    "user_message": m.user_message,
                    "retryable": m.retryable,
                    "public": m.public,
                }
                for m in mappers
            },
            "logging_config": logging_config,
            "notification_config": notification_config,
            "ErrorLevel": "ErrorLevel",
            "ErrorHandlingStrategy": "ErrorHandlingStrategy",
        }

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Render Jinja2 template.

        Args:
            template_name: Template name
            context: Template context

        Returns:
            Rendered content
        """
        try:
            template = self._env.get_template(template_name)
            return template.render(**context)
        except Exception:
            # Fallback: generate inline code nếu template chưa tồn tại
            if "middleware" in template_name:
                return self._fallback_middleware(context)
            elif "responses" in template_name:
                return self._fallback_responses(context)
            return f"# Template {template_name} not found"

    def _fallback_middleware(self, context: dict[str, Any]) -> str:
        """
        Fallback middleware code generation khi template chưa tồn tại.

        Args:
            context: Template context

        Returns:
            Generated middleware code
        """
        handler = context["handler"]
        mappers_dict = context["mappers_dict"]

        mapper_lines = ""
        for exc_type, mapping in mappers_dict.items():
            mapper_lines += (
                f'    "{exc_type}": {{"status": {mapping["http_status"]}, '
                f'"code": "{mapping["error_code"]}", '
                f'"message": "{mapping["user_message"]}"}},'
                "\n"
            )

        return f'''"""
Global Error Handler Middleware

Tự động generate từ GlobalErrorHandler DSL.
CP01: Domain Model - Error Handler

Handler: {handler.name}
Strategy: {handler.strategy.value}
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


# Exception → HTTP mapping
ERROR_MAPPING = {{
{mapper_lines}
}}


def register_error_handlers(app: FastAPI) -> None:
    """Register global error handlers vào FastAPI app."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> Response:
        """Handle Starlette HTTP exceptions."""
        logger.warning(
            "HTTP {{status}}: {{detail}}",
            status=exc.status_code,
            detail=exc.detail,
            extra={{"path": str(request.url.path)}},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={{
                "error": {{
                    "code": "HTTP_ERROR",
                    "status": exc.status_code,
                    "message": exc.detail,
                }}
            }},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> Response:
        """Handle FastAPI validation errors."""
        logger.warning(
            "Validation error: {{errors}}",
            errors=exc.errors(),
            extra={{"path": str(request.url.path)}},
        )
        return JSONResponse(
            status_code=422,
            content={{
                "error": {{
                    "code": "VALIDATION_ERROR",
                    "status": 422,
                    "message": "Validation failed",
                    "details": exc.errors(),
                }}
            }},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> Response:
        """Handle all unhandled exceptions."""
        exc_type = type(exc).__name__
        mapping = ERROR_MAPPING.get(exc_type, {{}})
        status_code = mapping.get("status", 500)
        error_code = mapping.get("code", "INTERNAL_ERROR")

        if {str(handler.include_stack_trace).lower()}:
            import traceback
            stack_trace = traceback.format_exc()
        else:
            stack_trace = None

        logger.error(
            "Unhandled {{exc_type}}: {{msg}}",
            exc_type=exc_type,
            msg=str(exc),
            exc_info=stack_trace,
            extra={{"path": str(request.url.path)}},
        )

        response_content = {{
            "error": {{
                "code": error_code,
                "status": status_code,
                "message": mapping.get("message", "{handler.default_error_message}"),
            }}
        }}
        if stack_trace:
            response_content["error"]["stack_trace"] = stack_trace

        return JSONResponse(
            status_code=status_code,
            content=response_content,
        )
'''

    def _fallback_responses(self, context: dict[str, Any]) -> str:
        """
        Fallback error responses code generation khi template chưa tồn tại.

        Args:
            context: Template context

        Returns:
            Generated error responses code
        """
        return '''"""
Standard Error Response Models

Tự động generate từ GlobalErrorHandler DSL.
CP01: Domain Model - Error Responses

Định nghĩa Pydantic models cho standardized error response.
Theo RFC 7807 (Problem Details for HTTP APIs).
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Chi tiết lỗi cụ thể (cho validation errors)."""

    field: str = Field(..., description="Tên field có lỗi")
    message: str = Field(..., description="Thông báo lỗi")
    code: Optional[str] = Field(None, description="Mã lỗi")


class ErrorResponse(BaseModel):
    """
    Standard error response.

    Theo RFC 7807 — Problem Details for HTTP APIs.
    """

    type: str = Field(
        default="about:blank",
        description="URI references to the problem type",
    )
    title: str = Field(..., description="Ngắn gọn mô tả lỗi")
    status: int = Field(..., description="HTTP status code")
    detail: str = Field(..., description="Chi tiết lỗi")
    instance: Optional[str] = Field(
        None, description="URI trỏ đến instance cụ thể có vấn đề"
    )
    error_code: Optional[str] = Field(
        None, description="Mã lỗi business"
    )
    retryable: bool = Field(
        default=False, description="Có nên retry request này không"
    )


class ValidationErrorResponse(BaseModel):
    """Error response cho validation failures."""

    type: str = Field(default="about:blank")
    title: str = Field(default="Validation Error")
    status: int = Field(default=422)
    detail: str = Field(default="Validation failed")
    errors: list[ErrorDetail] = Field(default_factory=list)


class ProblemDetails(BaseModel):
    """
    RFC 7807 Problem Details.

    Extension của ErrorResponse với support cho:
    - Custom extension fields
    - Stack trace (internal only)
    - Correlation ID
    """

    type: str = Field(default="about:blank")
    title: str = Field(...)
    status: int = Field(...)
    detail: str = Field(...)
    instance: Optional[str] = Field(None)
    correlation_id: Optional[str] = Field(
        None, description="ID để trace lỗi xuyên hệ thống"
    )
    stack_trace: Optional[str] = Field(
        None, description="Stack trace (chỉ trong development)"
    )
    extensions: dict[str, Any] = Field(
        default_factory=dict,
        description="Custom extension fields",
    )
'''

    def write_files(
        self,
        files: dict[str, str],
        output_dir: Path,
    ) -> None:
        """
        Write generated files to disk.

        Args:
            files: Dict of file path -> content
            output_dir: Output directory
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        for filename, content in files.items():
            file_path = output_dir / filename
            file_path.write_text(content, encoding="utf-8")