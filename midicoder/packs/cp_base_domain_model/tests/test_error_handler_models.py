"""
Tests cho CP01 Global Error Handler Models.

Kiểm tra các dataclass:
- ErrorLevel enum
- ErrorHandlingStrategy enum
- GlobalErrorHandler (init, validation, serialization)
- ErrorMapper (init, validation, serialization)
- ErrorLoggingConfig (init, validation, serialization)
- ErrorNotificationConfig (init, validation, serialization)
- FastAPIErrorHandlerEmitter (fallback code generation)

CP01: Domain Model - Error Handler
"""

import pytest

from midicoder.packs.cp_base_domain_model.error_handler_models import (
    ErrorHandlingStrategy,
    ErrorLevel,
    ErrorLoggingConfig,
    ErrorMapper,
    ErrorNotificationConfig,
    GlobalErrorHandler,
)
from midicoder.errors import MidicoderError


# ===========================================================================
# ErrorLevel Enum
# ===========================================================================

class TestErrorLevel:
    """Tests cho ErrorLevel enum."""

    def test_all_levels_exist(self):
        assert ErrorLevel.INFO.value == "info"
        assert ErrorLevel.WARNING.value == "warning"
        assert ErrorLevel.ERROR.value == "error"
        assert ErrorLevel.CRITICAL.value == "critical"

    def test_from_string(self):
        assert ErrorLevel("error") == ErrorLevel.ERROR
        assert ErrorLevel("critical") == ErrorLevel.CRITICAL

    def test_count(self):
        assert len(ErrorLevel) == 4


# ===========================================================================
# ErrorHandlingStrategy Enum
# ===========================================================================

class TestErrorHandlingStrategy:
    """Tests cho ErrorHandlingStrategy enum."""

    def test_all_strategies_exist(self):
        assert ErrorHandlingStrategy.FALLBACK.value == "fallback"
        assert ErrorHandlingStrategy.RETRY.value == "retry"
        assert ErrorHandlingStrategy.CIRCUIT_BREAKER.value == "circuit_breaker"
        assert ErrorHandlingStrategy.GRACEFUL_DEGRADATION.value == "graceful_degradation"

    def test_from_string(self):
        assert ErrorHandlingStrategy("retry") == ErrorHandlingStrategy.RETRY

    def test_count(self):
        assert len(ErrorHandlingStrategy) == 4


# ===========================================================================
# GlobalErrorHandler
# ===========================================================================

class TestGlobalErrorHandler:
    """Tests cho GlobalErrorHandler dataclass."""

    def test_minimal_creation(self):
        handler = GlobalErrorHandler(
            id="app_error_handler",
            name="Global Error Handler",
        )
        assert handler.id == "app_error_handler"
        assert handler.name == "Global Error Handler"
        assert handler.strategy == ErrorHandlingStrategy.FALLBACK
        assert handler.log_level == ErrorLevel.ERROR
        assert handler.include_stack_trace is False
        assert handler.sanitize_output is True
        assert handler.cors_enabled is True

    def test_full_creation(self):
        handler = GlobalErrorHandler(
            id="prod_handler",
            name="Production Handler",
            strategy=ErrorHandlingStrategy.CIRCUIT_BREAKER,
            log_level=ErrorLevel.CRITICAL,
            include_stack_trace=True,
            custom_error_pages={404: "templates/404.html", 500: "templates/500.html"},
            default_error_message="Something went wrong",
            sanitize_output=False,
            cors_enabled=False,
        )
        assert handler.strategy == ErrorHandlingStrategy.CIRCUIT_BREAKER
        assert handler.log_level == ErrorLevel.CRITICAL
        assert handler.include_stack_trace is True
        assert handler.custom_error_pages[404] == "templates/404.html"
        assert handler.default_error_message == "Something went wrong"

    def test_empty_id_raises_error(self):
        with pytest.raises(MidicoderError):
            GlobalErrorHandler(id="", name="Empty ID")

    def test_to_dict(self):
        handler = GlobalErrorHandler(
            id="test_handler",
            name="Test Handler",
            strategy=ErrorHandlingStrategy.RETRY,
        )
        d = handler.to_dict()
        assert d["id"] == "test_handler"
        assert d["name"] == "Test Handler"
        assert d["strategy"] == "retry"
        assert d["log_level"] == "error"
        assert d["include_stack_trace"] is False

    def test_from_dict(self):
        data = {
            "id": "restored_handler",
            "name": "Restored",
            "strategy": "circuit_breaker",
            "log_level": "critical",
            "include_stack_trace": True,
            "custom_error_pages": {404: "/404"},
            "default_error_message": "Custom message",
            "sanitize_output": False,
            "cors_enabled": True,
        }
        handler = GlobalErrorHandler.from_dict(data)
        assert handler.id == "restored_handler"
        assert handler.strategy == ErrorHandlingStrategy.CIRCUIT_BREAKER
        assert handler.log_level == ErrorLevel.CRITICAL
        assert handler.include_stack_trace is True
        assert handler.custom_error_pages[404] == "/404"

    def test_from_dict_defaults(self):
        data = {
            "id": "minimal",
            "name": "Minimal",
        }
        handler = GlobalErrorHandler.from_dict(data)
        assert handler.strategy == ErrorHandlingStrategy.FALLBACK
        assert handler.log_level == ErrorLevel.ERROR
        assert handler.include_stack_trace is False

    def test_roundtrip(self):
        handler = GlobalErrorHandler(
            id="rt_handler",
            name="Roundtrip",
            strategy=ErrorHandlingStrategy.GRACEFUL_DEGRADATION,
            custom_error_pages={503: "/maintenance"},
        )
        restored = GlobalErrorHandler.from_dict(handler.to_dict())
        assert restored.id == handler.id
        assert restored.strategy == handler.strategy
        assert restored.custom_error_pages == handler.custom_error_pages


# ===========================================================================
# ErrorMapper
# ===========================================================================

class TestErrorMapper:
    """Tests cho ErrorMapper dataclass."""

    def test_minimal_creation(self):
        mapper = ErrorMapper(
            id="mapper_value_error",
            exception_type="ValueError",
        )
        assert mapper.id == "mapper_value_error"
        assert mapper.exception_type == "ValueError"
        assert mapper.http_status == 500
        assert mapper.error_code == "INTERNAL_ERROR"
        assert mapper.user_message == "An unexpected error occurred"
        assert mapper.retryable is False
        assert mapper.public is True

    def test_full_creation(self):
        mapper = ErrorMapper(
            id="mapper_conn",
            exception_type="ConnectionError",
            http_status=503,
            error_code="SERVICE_UNAVAILABLE",
            user_message="Service temporarily unavailable",
            retryable=True,
            public=True,
        )
        assert mapper.http_status == 503
        assert mapper.retryable is True

    def test_empty_id_raises_error(self):
        with pytest.raises(MidicoderError):
            ErrorMapper(id="", exception_type="ValueError")

    def test_common_mappings(self):
        mappers = [
            ErrorMapper(id="m1", exception_type="ValueError", http_status=400, error_code="INVALID_INPUT"),
            ErrorMapper(id="m2", exception_type="KeyError", http_status=404, error_code="NOT_FOUND"),
            ErrorMapper(id="m3", exception_type="PermissionError", http_status=403, error_code="FORBIDDEN"),
        ]
        assert mappers[0].http_status == 400
        assert mappers[1].error_code == "NOT_FOUND"
        assert mappers[2].http_status == 403

    def test_non_public_mapper(self):
        mapper = ErrorMapper(
            id="internal",
            exception_type="InternalError",
            public=False,
        )
        assert mapper.public is False

    def test_to_dict(self):
        mapper = ErrorMapper(
            id="dict_test",
            exception_type="TimeoutError",
            http_status=504,
            retryable=True,
        )
        d = mapper.to_dict()
        assert d["exception_type"] == "TimeoutError"
        assert d["http_status"] == 504
        assert d["retryable"] is True

    def test_from_dict(self):
        data = {
            "id": "from_dict",
            "exception_type": "TypeError",
            "http_status": 422,
            "error_code": "BAD_REQUEST",
            "user_message": "Bad request",
            "retryable": False,
            "public": True,
        }
        mapper = ErrorMapper.from_dict(data)
        assert mapper.id == "from_dict"
        assert mapper.exception_type == "TypeError"
        assert mapper.http_status == 422

    def test_from_dict_defaults(self):
        data = {"id": "minimal", "exception_type": "RuntimeError"}
        mapper = ErrorMapper.from_dict(data)
        assert mapper.http_status == 500
        assert mapper.error_code == "INTERNAL_ERROR"

    def test_roundtrip(self):
        mapper = ErrorMapper(
            id="rt_mapper",
            exception_type="ValidationError",
            http_status=422,
            error_code="VALIDATION_FAILED",
            retryable=False,
            public=True,
        )
        restored = ErrorMapper.from_dict(mapper.to_dict())
        assert restored.id == mapper.id
        assert restored.http_status == mapper.http_status
        assert restored.retryable == mapper.retryable


# ===========================================================================
# ErrorLoggingConfig
# ===========================================================================

class TestErrorLoggingConfig:
    """Tests cho ErrorLoggingConfig dataclass."""

    def test_minimal_creation(self):
        config = ErrorLoggingConfig(
            id="basic_logger",
            name="Basic Logger",
        )
        assert config.id == "basic_logger"
        assert config.log_format == "structured"
        assert config.log_destination == "stdout"
        assert config.max_log_size_mb == 100
        assert config.log_rotation_days == 30
        assert config.include_request_context is True
        assert config.include_user_context is True
        assert config.redact_fields == []

    def test_full_creation(self):
        config = ErrorLoggingConfig(
            id="prod_logger",
            name="Production Logger",
            log_format="json",
            log_destination="elasticsearch",
            max_log_size_mb=500,
            log_rotation_days=90,
            redact_fields=["password", "token", "ssn", "credit_card"],
        )
        assert config.log_format == "json"
        assert config.log_destination == "elasticsearch"
        assert "ssn" in config.redact_fields

    def test_file_destination(self):
        config = ErrorLoggingConfig(
            id="file_logger",
            name="File Logger",
            log_destination="file",
            log_file_path="/var/log/app/errors.log",
        )
        assert config.log_destination == "file"
        assert config.log_file_path == "/var/log/app/errors.log"

    def test_invalid_log_format_raises(self):
        with pytest.raises(MidicoderError):
            ErrorLoggingConfig(
                id="bad_format",
                name="Bad",
                log_format="xml",
            )

    def test_invalid_log_destination_raises(self):
        with pytest.raises(MidicoderError):
            ErrorLoggingConfig(
                id="bad_dest",
                name="Bad",
                log_destination="kafka",
            )

    def test_valid_formats(self):
        for fmt in ("structured", "plain", "json"):
            config = ErrorLoggingConfig(
                id=f"cfg_{fmt}",
                name=fmt,
                log_format=fmt,
            )
            assert config.log_format == fmt

    def test_valid_destinations(self):
        for dest in ("stdout", "file", "elasticsearch", "cloudwatch"):
            config = ErrorLoggingConfig(
                id=f"cfg_{dest}",
                name=dest,
                log_destination=dest,
            )
            assert config.log_destination == dest

    def test_to_dict(self):
        config = ErrorLoggingConfig(
            id="dict_cfg",
            name="Dict Config",
            redact_fields=["password"],
        )
        d = config.to_dict()
        assert d["log_format"] == "structured"
        assert d["redact_fields"] == ["password"]

    def test_from_dict(self):
        data = {
            "id": "restored",
            "name": "Restored",
            "log_format": "json",
            "log_destination": "cloudwatch",
            "redact_fields": ["token"],
        }
        config = ErrorLoggingConfig.from_dict(data)
        assert config.log_format == "json"
        assert config.log_destination == "cloudwatch"

    def test_roundtrip(self):
        config = ErrorLoggingConfig(
            id="rt_cfg",
            name="Roundtrip",
            log_format="plain",
            redact_fields=["secret"],
        )
        restored = ErrorLoggingConfig.from_dict(config.to_dict())
        assert restored.id == config.id
        assert restored.redact_fields == config.redact_fields


# ===========================================================================
# ErrorNotificationConfig
# ===========================================================================

class TestErrorNotificationConfig:
    """Tests cho ErrorNotificationConfig dataclass."""

    def test_minimal_creation(self):
        config = ErrorNotificationConfig(
            id="basic_notifier",
            name="Basic Notifier",
        )
        assert config.id == "basic_notifier"
        assert config.notify_on_level == ErrorLevel.ERROR
        assert config.slack_webhook == ""
        assert config.email_recipients == []
        assert config.include_sentry_integration is False
        assert config.rate_limit_per_hour == 50

    def test_full_creation(self):
        config = ErrorNotificationConfig(
            id="prod_notifier",
            name="Production Notifier",
            notify_on_level=ErrorLevel.WARNING,
            slack_webhook="https://hooks.slack.com/services/T00/B00/xxx",
            email_recipients=["ops@company.com", "dev@company.com"],
            pagerduty_service_key="pd-key-123",
            include_sentry_integration=True,
            sentry_dsn="https://key@sentry.io/123",
            rate_limit_per_hour=100,
        )
        assert config.notify_on_level == ErrorLevel.WARNING
        assert len(config.email_recipients) == 2
        assert config.include_sentry_integration is True

    def test_sentry_without_dsn_raises(self):
        with pytest.raises(MidicoderError):
            ErrorNotificationConfig(
                id="bad_sentry",
                name="Bad",
                include_sentry_integration=True,
                sentry_dsn="",
            )

    def test_sentry_with_dsn_ok(self):
        config = ErrorNotificationConfig(
            id="good_sentry",
            name="Good",
            include_sentry_integration=True,
            sentry_dsn="https://valid@sentry.io/1",
        )
        assert config.include_sentry_integration is True

    def test_notify_on_critical(self):
        config = ErrorNotificationConfig(
            id="critical_only",
            name="Critical Only",
            notify_on_level=ErrorLevel.CRITICAL,
        )
        assert config.notify_on_level == ErrorLevel.CRITICAL

    def test_notify_on_info(self):
        config = ErrorNotificationConfig(
            id="all_levels",
            name="All Levels",
            notify_on_level=ErrorLevel.INFO,
        )
        assert config.notify_on_level == ErrorLevel.INFO

    def test_to_dict(self):
        config = ErrorNotificationConfig(
            id="dict_notif",
            name="Dict Notif",
            notify_on_level=ErrorLevel.WARNING,
        )
        d = config.to_dict()
        assert d["notify_on_level"] == "warning"
        assert d["rate_limit_per_hour"] == 50

    def test_from_dict(self):
        data = {
            "id": "restored",
            "name": "Restored",
            "notify_on_level": "critical",
            "slack_webhook": "https://hooks.slack.com/test",
            "email_recipients": ["a@b.com"],
            "rate_limit_per_hour": 200,
        }
        config = ErrorNotificationConfig.from_dict(data)
        assert config.notify_on_level == ErrorLevel.CRITICAL
        assert config.slack_webhook == "https://hooks.slack.com/test"
        assert config.rate_limit_per_hour == 200

    def test_roundtrip(self):
        config = ErrorNotificationConfig(
            id="rt_notif",
            name="Roundtrip",
            notify_on_level=ErrorLevel.INFO,
            rate_limit_per_hour=75,
        )
        restored = ErrorNotificationConfig.from_dict(config.to_dict())
        assert restored.notify_on_level == config.notify_on_level
        assert restored.rate_limit_per_hour == config.rate_limit_per_hour


# ===========================================================================
# FastAPI ErrorHandler Emitter
# ===========================================================================

class TestFastAPIErrorHandlerEmitter:
    """Tests cho FastAPIErrorHandlerEmitter."""

    def test_emitter_import(self):
        from midicoder.packs.cp_base_domain_model.error_handler_fastapi import (
            FastAPIErrorHandlerEmitter,
        )
        assert FastAPIErrorHandlerEmitter is not None

    def test_emitter_init(self):
        from pathlib import Path
        from midicoder.packs.cp_base_domain_model.error_handler_fastapi import (
            FastAPIErrorHandlerEmitter,
        )
        emitter = FastAPIErrorHandlerEmitter(stack_dir=Path("/tmp"))
        assert emitter._stack_dir == Path("/tmp")

    def test_emit_with_minimal_handler(self):
        from pathlib import Path
        from midicoder.packs.cp_base_domain_model.error_handler_fastapi import (
            FastAPIErrorHandlerEmitter,
        )
        handler = GlobalErrorHandler(
            id="test_handler",
            name="Test Handler",
        )
        emitter = FastAPIErrorHandlerEmitter(stack_dir=Path("/tmp"))
        files = emitter.emit(handler)
        assert "error_handler_middleware.py" in files
        assert "error_responses.py" in files

    def test_emit_with_mappers(self):
        from pathlib import Path
        from midicoder.packs.cp_base_domain_model.error_handler_fastapi import (
            FastAPIErrorHandlerEmitter,
        )
        handler = GlobalErrorHandler(
            id="test_handler",
            name="Test Handler",
        )
        mappers = [
            ErrorMapper(id="m1", exception_type="ValueError", http_status=400),
            ErrorMapper(id="m2", exception_type="KeyError", http_status=404),
        ]
        emitter = FastAPIErrorHandlerEmitter(stack_dir=Path("/tmp"))
        files = emitter.emit(handler, mappers=mappers)
        # Fallback code should contain mapper entries
        middleware = files["error_handler_middleware.py"]
        assert "ValueError" in middleware
        assert "KeyError" in middleware

    def test_emit_includes_all_configs(self):
        from pathlib import Path
        from midicoder.packs.cp_base_domain_model.error_handler_fastapi import (
            FastAPIErrorHandlerEmitter,
        )
        handler = GlobalErrorHandler(
            id="full_handler",
            name="Full Handler",
            include_stack_trace=True,
        )
        logging_cfg = ErrorLoggingConfig(
            id="log_cfg",
            name="Log Config",
        )
        notif_cfg = ErrorNotificationConfig(
            id="notif_cfg",
            name="Notification Config",
        )
        emitter = FastAPIErrorHandlerEmitter(stack_dir=Path("/tmp"))
        files = emitter.emit(
            handler,
            logging_config=logging_cfg,
            notification_config=notif_cfg,
        )
        assert len(files) == 2

    def test_fallback_middleware_has_error_handling(self):
        from pathlib import Path
        from midicoder.packs.cp_base_domain_model.error_handler_fastapi import (
            FastAPIErrorHandlerEmitter,
        )
        handler = GlobalErrorHandler(
            id="fallback_test",
            name="Fallback",
            default_error_message="Custom fallback message",
        )
        emitter = FastAPIErrorHandlerEmitter(stack_dir=Path("/tmp"))
        files = emitter.emit(handler)
        middleware = files["error_handler_middleware.py"]
        assert "register_error_handlers" in middleware
        assert "Custom fallback message" in middleware

    def test_fallback_responses_has_models(self):
        from pathlib import Path
        from midicoder.packs.cp_base_domain_model.error_handler_fastapi import (
            FastAPIErrorHandlerEmitter,
        )
        handler = GlobalErrorHandler(
            id="resp_test",
            name="Response Test",
        )
        emitter = FastAPIErrorHandlerEmitter(stack_dir=Path("/tmp"))
        files = emitter.emit(handler)
        responses = files["error_responses.py"]
        assert "ErrorResponse" in responses
        assert "ValidationErrorResponse" in responses
        assert "ProblemDetails" in responses


# ===========================================================================
# Cross-model integration
# ===========================================================================

class TestErrorHandlerIntegration:
    """Integration tests cho error handler ecosystem."""

    def test_handler_with_mappers_and_logging(self):
        """Full error handler setup: handler + mappers + logging + notification."""
        handler = GlobalErrorHandler(
            id="app_global",
            name="Application Global Handler",
            strategy=ErrorHandlingStrategy.FALLBACK,
            include_stack_trace=False,
        )
        mappers = [
            ErrorMapper(id="m1", exception_type="ValueError", http_status=400, error_code="BAD_REQUEST"),
            ErrorMapper(id="m2", exception_type="ConnectionError", http_status=503, retryable=True),
            ErrorMapper(id="m3", exception_type="PermissionError", http_status=403),
        ]
        logging_cfg = ErrorLoggingConfig(
            id="app_logger",
            name="App Logger",
            log_format="json",
            log_destination="stdout",
            redact_fields=["password", "token"],
        )
        notif_cfg = ErrorNotificationConfig(
            id="app_notifier",
            name="App Notifier",
            notify_on_level=ErrorLevel.ERROR,
            rate_limit_per_hour=100,
        )

        assert len(mappers) == 3
        assert handler.strategy == ErrorHandlingStrategy.FALLBACK
        assert logging_cfg.log_format == "json"
        assert notif_cfg.notify_on_level == ErrorLevel.ERROR

    def test_all_models_serializable(self):
        """Tất cả models có to_dict và from_dict."""
        handler = GlobalErrorHandler(id="h1", name="H1")
        mapper = ErrorMapper(id="m1", exception_type="Error")
        logging = ErrorLoggingConfig(id="l1", name="L1")
        notif = ErrorNotificationConfig(id="n1", name="N1")

        # All should have to_dict
        assert isinstance(handler.to_dict(), dict)
        assert isinstance(mapper.to_dict(), dict)
        assert isinstance(logging.to_dict(), dict)
        assert isinstance(notif.to_dict(), dict)

        # All should have from_dict
        assert isinstance(GlobalErrorHandler.from_dict(handler.to_dict()), GlobalErrorHandler)
        assert isinstance(ErrorMapper.from_dict(mapper.to_dict()), ErrorMapper)
        assert isinstance(ErrorLoggingConfig.from_dict(logging.to_dict()), ErrorLoggingConfig)
        assert isinstance(ErrorNotificationConfig.from_dict(notif.to_dict()), ErrorNotificationConfig)


# ===========================================================================
# Gap-Filling Tests: error_handler_fastapi.py uncovered lines (83% -> ≥99%)
# ===========================================================================


class TestFastAPIErrorHandlerEmitter_RenderSuccess:
    """Tests cho _render() — line 182 (success template render path)."""

    def test_render_with_real_template(self, tmp_path):
        """Test: _render() render template thật từ disk — line 182."""
        from midicoder.packs.cp_base_domain_model.error_handler_fastapi import (
            FastAPIErrorHandlerEmitter,
        )

        # Create a real Jinja2 template on disk
        (tmp_path / "error_handler_middleware.py.jinja2").write_text(
            "# handler: {{ handler_name }}", encoding="utf-8"
        )
        emitter = FastAPIErrorHandlerEmitter(stack_dir=tmp_path)

        context = {
            "handler_name": "TestHandler",
        }
        result = emitter._render("error_handler_middleware.py.jinja2", context)

        assert result == "# handler: TestHandler"


class TestFastAPIErrorHandlerEmitter_RenderFallbackUnknown:
    """Tests cho _render() — line 189 (unknown template fallback)."""

    def test_render_unknown_template_returns_not_found(self, tmp_path):
        """Test: _render() trả về fallback string cho template không phải middleware/responses — line 189."""
        from midicoder.packs.cp_base_domain_model.error_handler_fastapi import (
            FastAPIErrorHandlerEmitter,
        )

        emitter = FastAPIErrorHandlerEmitter(stack_dir=tmp_path)
        result = emitter._render("unknown_template.py.jinja2", {})

        assert "Template unknown_template.py.jinja2 not found" in result


class TestFastAPIErrorHandlerEmitter_WriteFiles:
    """Tests cho write_files() — lines 438-442."""

    def test_write_files_creates_output_dir(self, tmp_path):
        """Test: write_files tạo output directory nếu chưa tồn tại."""
        from midicoder.packs.cp_base_domain_model.error_handler_fastapi import (
            FastAPIErrorHandlerEmitter,
        )

        emitter = FastAPIErrorHandlerEmitter(stack_dir=tmp_path)
        output = tmp_path / "nested" / "output"

        emitter.write_files(
            {"test.py": "# content"},
            output,
        )

        assert output.exists()
        assert (output / "test.py").read_text(encoding="utf-8") == "# content"

    def test_write_files_writes_multiple_files(self, tmp_path):
        """Test: write_files ghi nhiều files."""
        from midicoder.packs.cp_base_domain_model.error_handler_fastapi import (
            FastAPIErrorHandlerEmitter,
        )

        emitter = FastAPIErrorHandlerEmitter(stack_dir=tmp_path)

        emitter.write_files(
            {
                "error_handler_middleware.py": "# middleware",
                "error_responses.py": "# responses",
            },
            tmp_path,
        )

        assert (tmp_path / "error_handler_middleware.py").read_text() == "# middleware"
        assert (tmp_path / "error_responses.py").read_text() == "# responses"

    def test_write_files_utf8_encoding(self, tmp_path):
        """Test: write_files ghi UTF-8 encoding."""
        from midicoder.packs.cp_base_domain_model.error_handler_fastapi import (
            FastAPIErrorHandlerEmitter,
        )

        emitter = FastAPIErrorHandlerEmitter(stack_dir=tmp_path)

        emitter.write_files(
            {"test.py": "# nội dung tiếng Việt"},
            tmp_path,
        )

        content = (tmp_path / "test.py").read_text(encoding="utf-8")
        assert "tiếng Việt" in content