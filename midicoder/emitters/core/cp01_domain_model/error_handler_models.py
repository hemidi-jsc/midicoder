# coding: utf-8
"""
Global Error Handler models cho CP01 — Domain Model.

Định nghĩa các dataclass cho global error handling strategy:
- ErrorLevel: Mức độ lỗi (info, warning, error, critical)
- ErrorHandlingStrategy: Chiến lược xử lý lỗi (fallback, retry, circuit_breaker, graceful_degradation)
- GlobalErrorHandler: Cấu hình global error handler
- ErrorMapper: Ánh xạ exception type → HTTP status code + error response format
- ErrorLoggingConfig: Cấu hình logging cho errors
- ErrorNotificationConfig: Cấu hình thông báo khi có lỗi

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Error Handling Enums
# ===========================================================================


class ErrorLevel(str, Enum):
    """
    Mức độ severity của lỗi.

    - info: Thông tin, không phải lỗi nghiêm trọng
    - warning: Cảnh báo, có thể gây vấn đề trong tương lai
    - error: Lỗi, chức năng bị ảnh hưởng
    - critical: Lỗi nghiêm trọng, hệ thống không hoạt động
    """
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorHandlingStrategy(str, Enum):
    """
    Chiến lược xử lý lỗi khi exception xảy ra.

    - fallback: Trả về giá trị mặc định/giả lập
    - retry: Thử lại operation (với backoff)
    - circuit_breaker: Ngừng gọi service sau N lỗi liên tiếp
    - graceful_degradation: Trả về dữ liệu giảm chất lượng
    """
    FALLBACK = "fallback"
    RETRY = "retry"
    CIRCUIT_BREAKER = "circuit_breaker"
    GRACEFUL_DEGRADATION = "graceful_degradation"


# ===========================================================================
# Global ErrorHandler
# ===========================================================================


@dataclass
class GlobalErrorHandler:
    """
    Cấu hình global error handler — middleware bắt tất cả exceptions.

    Attributes:
        id: Handler ID (unique identifier)
        name: Tên mô tả handler
        strategy: Chiến lược xử lý lỗi mặc định
        log_level: Mức log khi ghi lỗi
        include_stack_trace: Có include stack trace trong response không (tắt trong production)
        custom_error_pages: Ánh xạ status_code → template path
        default_error_message: Message mặc định khi không có custom message
        sanitize_output: Có sanitize output để tránh leak sensitive data không
        cors_enabled: Có enable CORS cho error response không

    Ví dụ:
        >>> handler = GlobalErrorHandler(
        ...     id="app_error_handler",
        ...     name="Global Error Handler",
        ...     strategy=ErrorHandlingStrategy.FALLBACK,
        ...     include_stack_trace=False,
        ... )
    """
    id: str
    name: str
    strategy: ErrorHandlingStrategy = ErrorHandlingStrategy.FALLBACK
    log_level: ErrorLevel = ErrorLevel.ERROR
    include_stack_trace: bool = False
    custom_error_pages: dict[int, str] = field(default_factory=dict)
    default_error_message: str = "Internal Server Error"
    sanitize_output: bool = True
    cors_enabled: bool = True

    def __post_init__(self) -> None:
        if not self.id:
            raise EM.raise_error(
                ErrorCode.INVALID_ID, reason="GlobalErrorHandler.id required"
            )

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển thành dictionary cho serialization.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "name": self.name,
            "strategy": self.strategy.value,
            "log_level": self.log_level.value,
            "include_stack_trace": self.include_stack_trace,
            "custom_error_pages": self.custom_error_pages,
            "default_error_message": self.default_error_message,
            "sanitize_output": self.sanitize_output,
            "cors_enabled": self.cors_enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GlobalErrorHandler":
        """
        Tạo GlobalErrorHandler từ dictionary.

        Args:
            data: Dictionary representation

        Returns:
            GlobalErrorHandler instance
        """
        return cls(
            id=data["id"],
            name=data["name"],
            strategy=ErrorHandlingStrategy(data.get("strategy", "fallback")),
            log_level=ErrorLevel(data.get("log_level", "error")),
            include_stack_trace=data.get("include_stack_trace", False),
            custom_error_pages=data.get("custom_error_pages", {}),
            default_error_message=data.get("default_error_message", "Internal Server Error"),
            sanitize_output=data.get("sanitize_output", True),
            cors_enabled=data.get("cors_enabled", True),
        )


# ===========================================================================
# Error Mapper
# ===========================================================================


@dataclass
class ErrorMapper:
    """
    Ánh xạ exception type → HTTP status code + error response format.

    Dùng để translate Python exceptions sang HTTP responses có nghĩa.

    Attributes:
        id: Mapper ID (unique identifier)
        exception_type: Tên exception class (ví dụ: "ValueError", "ConnectionError")
        http_status: HTTP status code trả về (ví dụ: 400, 404, 500)
        error_code: Mã lỗi business (ví dụ: "INVALID_INPUT", "NOT_FOUND")
        user_message: Message hiển thị cho user
        retryable: Có nên retry request này không
        public: Có expose error details cho client không

    Ví dụ:
        >>> mapper = ErrorMapper(
        ...     id="mapper_value_error",
        ...     exception_type="ValueError",
        ...     http_status=400,
        ...     error_code="INVALID_INPUT",
        ...     user_message="Invalid input provided",
        ... )
    """
    id: str
    exception_type: str
    http_status: int = 500
    error_code: str = "INTERNAL_ERROR"
    user_message: str = "An unexpected error occurred"
    retryable: bool = False
    public: bool = True

    def __post_init__(self) -> None:
        if not self.id:
            raise EM.raise_error(
                ErrorCode.INVALID_ID, reason="ErrorMapper.id required"
            )

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển thành dictionary cho serialization.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "exception_type": self.exception_type,
            "http_status": self.http_status,
            "error_code": self.error_code,
            "user_message": self.user_message,
            "retryable": self.retryable,
            "public": self.public,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ErrorMapper":
        """
        Tạo ErrorMapper từ dictionary.

        Args:
            data: Dictionary representation

        Returns:
            ErrorMapper instance
        """
        return cls(
            id=data["id"],
            exception_type=data["exception_type"],
            http_status=data.get("http_status", 500),
            error_code=data.get("error_code", "INTERNAL_ERROR"),
            user_message=data.get("user_message", "An unexpected error occurred"),
            retryable=data.get("retryable", False),
            public=data.get("public", True),
        )


# ===========================================================================
# Error Logging Config
# ===========================================================================


@dataclass
class ErrorLoggingConfig:
    """
    Cấu hình logging cho errors.

    Attributes:
        id: Config ID (unique identifier)
        name: Tên mô tả config
        log_format: Format log ("structured", "plain", "json")
        log_destination: Destination log ("stdout", "file", "elasticsearch", "cloudwatch")
        log_file_path: Đường dẫn file log (nếu destination = "file")
        max_log_size_mb: Kích thước tối đa file log (MB)
        log_rotation_days: Số ngày giữ log trước khi rotate
        include_request_context: Có include request context trong log không
        include_user_context: Có include user context trong log không
        redact_fields: Danh sách fields cần redact trong log (password, token, ssn)

    Ví dụ:
        >>> config = ErrorLoggingConfig(
        ...     id="error_logger",
        ...     name="Production Error Logger",
        ...     log_format="json",
        ...     log_destination="elasticsearch",
        ...     redact_fields=["password", "token", "ssn"],
        ... )
    """
    id: str
    name: str
    log_format: str = "structured"
    log_destination: str = "stdout"
    log_file_path: str = ""
    max_log_size_mb: int = 100
    log_rotation_days: int = 30
    include_request_context: bool = True
    include_user_context: bool = True
    redact_fields: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        valid_formats = ("structured", "plain", "json")
        if self.log_format not in valid_formats:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason=f"ErrorLoggingConfig.log_format must be one of {valid_formats}",
            )
        valid_destinations = ("stdout", "file", "elasticsearch", "cloudwatch")
        if self.log_destination not in valid_destinations:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason=f"ErrorLoggingConfig.log_destination must be one of {valid_destinations}",
            )

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển thành dictionary cho serialization.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "name": self.name,
            "log_format": self.log_format,
            "log_destination": self.log_destination,
            "log_file_path": self.log_file_path,
            "max_log_size_mb": self.max_log_size_mb,
            "log_rotation_days": self.log_rotation_days,
            "include_request_context": self.include_request_context,
            "include_user_context": self.include_user_context,
            "redact_fields": self.redact_fields,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ErrorLoggingConfig":
        """
        Tạo ErrorLoggingConfig từ dictionary.

        Args:
            data: Dictionary representation

        Returns:
            ErrorLoggingConfig instance
        """
        return cls(
            id=data["id"],
            name=data["name"],
            log_format=data.get("log_format", "structured"),
            log_destination=data.get("log_destination", "stdout"),
            log_file_path=data.get("log_file_path", ""),
            max_log_size_mb=data.get("max_log_size_mb", 100),
            log_rotation_days=data.get("log_rotation_days", 30),
            include_request_context=data.get("include_request_context", True),
            include_user_context=data.get("include_user_context", True),
            redact_fields=data.get("redact_fields", []),
        )


# ===========================================================================
# Error Notification Config
# ===========================================================================


@dataclass
class ErrorNotificationConfig:
    """
    Cấu hình thông báo khi có lỗi.

    Attributes:
        id: Config ID (unique identifier)
        name: Tên mô tả config
        notify_on_level: Mức độ lỗi tối thiểu để gửi notification
        slack_webhook: Slack webhook URL
        email_recipients: Danh sách email nhận notification
        pagerduty_service_key: PagerDuty service key
        include_sentry_integration: Có tích hợp Sentry không
        sentry_dsn: Sentry DSN
        rate_limit_per_hour: Giới hạn notification mỗi giờ (chống flood)

    Ví dụ:
        >>> config = ErrorNotificationConfig(
        ...     id="error_notifier",
        ...     name="Production Alert",
        ...     notify_on_level=ErrorLevel.ERROR,
        ...     slack_webhook="https://hooks.slack.com/xxx",
        ...     include_sentry_integration=True,
        ... )
    """
    id: str
    name: str
    notify_on_level: ErrorLevel = ErrorLevel.ERROR
    slack_webhook: str = ""
    email_recipients: list[str] = field(default_factory=list)
    pagerduty_service_key: str = ""
    include_sentry_integration: bool = False
    sentry_dsn: str = ""
    rate_limit_per_hour: int = 50

    def __post_init__(self) -> None:
        if self.include_sentry_integration and not self.sentry_dsn:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                reason="ErrorNotificationConfig.sentry_dsn required when include_sentry_integration=True",
            )

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển thành dictionary cho serialization.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "name": self.name,
            "notify_on_level": self.notify_on_level.value,
            "slack_webhook": self.slack_webhook,
            "email_recipients": self.email_recipients,
            "pagerduty_service_key": self.pagerduty_service_key,
            "include_sentry_integration": self.include_sentry_integration,
            "sentry_dsn": self.sentry_dsn,
            "rate_limit_per_hour": self.rate_limit_per_hour,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ErrorNotificationConfig":
        """
        Tạo ErrorNotificationConfig từ dictionary.

        Args:
            data: Dictionary representation

        Returns:
            ErrorNotificationConfig instance
        """
        return cls(
            id=data["id"],
            name=data["name"],
            notify_on_level=ErrorLevel(data.get("notify_on_level", "error")),
            slack_webhook=data.get("slack_webhook", ""),
            email_recipients=data.get("email_recipients", []),
            pagerduty_service_key=data.get("pagerduty_service_key", ""),
            include_sentry_integration=data.get("include_sentry_integration", False),
            sentry_dsn=data.get("sentry_dsn", ""),
            rate_limit_per_hour=data.get("rate_limit_per_hour", 50),
        )


__all__ = [
    "ErrorLevel",
    "ErrorHandlingStrategy",
    "GlobalErrorHandler",
    "ErrorMapper",
    "ErrorLoggingConfig",
    "ErrorNotificationConfig",
]