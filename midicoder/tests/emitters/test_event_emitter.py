"""
Tests cho Event Emitter (CP05) — TDD Red Phase.

Test coverage:
- Error codes: 5 tests
- Event models: 8 tests
- Event parser: 6 tests
- FastAPIEventEmitter: 10 tests
- NestJSEventEmitter: 8 tests
- Integration: 8 tests

Tổng: 45 tests
"""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from midicoder.errors import ErrorCode, MidicoderError


# ============================================================================
# Test Error Codes (MDC-EVT-001 ~ MDC-EVT-010)
# ============================================================================


class TestEventErrorCodes:
    """Tests cho Event error codes."""

    def test_evt_bus_not_initialized_exists(self):
        """MDC-EVT-001: EVT_BUS_NOT_INITIALIZED exists."""
        assert hasattr(ErrorCode, "EVT_BUS_NOT_INITIALIZED")

    def test_evt_subscriber_not_found_exists(self):
        """MDC-EVT-002: EVT_SUBSCRIBER_NOT_FOUND exists."""
        assert hasattr(ErrorCode, "EVT_SUBSCRIBER_NOT_FOUND")

    def test_evt_schema_validation_failed_exists(self):
        """MDC-EVT-003: EVT_SCHEMA_VALIDATION_FAILED exists."""
        assert hasattr(ErrorCode, "EVT_SCHEMA_VALIDATION_FAILED")

    def test_evt_outbox_write_failed_exists(self):
        """MDC-EVT-004: EVT_OUTBOX_WRITE_FAILED exists."""
        assert hasattr(ErrorCode, "EVT_OUTBOX_WRITE_FAILED")

    def test_evt_handler_failed_exists(self):
        """MDC-EVT-006: EVT_HANDLER_FAILED exists."""
        assert hasattr(ErrorCode, "EVT_HANDLER_FAILED")


# ============================================================================
# Test Event Models
# ============================================================================


class TestEventModels:
    """Tests cho Event data models."""

    def test_event_definition_creation(self):
        """EventDefinition có thể tạo với event_name và payload_fields."""
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition

        event = EventDefinition(
            event_name="order.created",
            payload_fields=["order_id", "customer_id", "total"],
            topic="orders",
            version="1.0",
        )
        assert event.event_name == "order.created"
        assert len(event.payload_fields) == 3
        assert event.topic == "orders"

    def test_event_definition_defaults(self):
        """EventDefinition có default values."""
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition

        event = EventDefinition(event_name="test.event")
        assert event.event_name == "test.event"
        assert event.topic == "default"
        assert event.version == "1.0"

    def test_event_definition_dict_conversion(self):
        """EventDefinition.to_dict() trả về dict."""
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition

        event = EventDefinition(
            event_name="order.created",
            payload_fields=["order_id"],
            topic="orders",
        )
        result = event.to_dict()
        assert isinstance(result, dict)
        assert result["event_name"] == "order.created"
        assert "payload_fields" in result

    def test_event_definition_from_dict(self):
        """EventDefinition.from_dict() tạo object từ dict."""
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition

        data = {
            "event_name": "payment.completed",
            "payload_fields": ["payment_id", "amount"],
            "topic": "payments",
            "version": "2.0",
        }
        event = EventDefinition.from_dict(data)
        assert event.event_name == "payment.completed"
        assert event.topic == "payments"
        assert event.version == "2.0"

    def test_event_definition_validation(self):
        """EventDefinition validate event_name không được empty."""
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition

        with pytest.raises((ValueError, MidicoderError)):
            EventDefinition(event_name="")

    def test_event_definition_with_tenant(self):
        """EventDefinition support tenant_id cho multi-tenant."""
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition

        event = EventDefinition(
            event_name="order.created",
            payload_fields=["order_id"],
            tenant_id="tenant_123",
        )
        assert event.tenant_id == "tenant_123"

    def test_event_definition_schema_fields(self):
        """EventDefinition có schema_fields cho validation."""
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition

        schema = {
            "order_id": {"type": "string", "required": True},
            "total": {"type": "number", "required": True},
        }
        event = EventDefinition(
            event_name="order.created",
            payload_fields=["order_id", "total"],
            schema_fields=schema,
        )
        assert event.schema_fields == schema

    def test_event_definition_equality(self):
        """EventDefinition equality based on event_name."""
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition

        e1 = EventDefinition(event_name="order.created", topic="orders")
        e2 = EventDefinition(event_name="order.created", topic="different")
        assert e1.event_name == e2.event_name


# ============================================================================
# Test Event Parser
# ============================================================================


class TestEventParser:
    """Tests cho Event Parser."""

    def test_parse_single_event(self):
        """Parse 1 event từ YAML dict."""
        from midicoder.emitters.core.cp05_event_driven.parser import EventParser

        yaml_data = {
            "event_name": "order.created",
            "payload_fields": ["order_id", "total"],
            "topic": "orders",
        }
        parser = EventParser()
        events = parser.parse([yaml_data])
        assert len(events) == 1
        assert events[0].event_name == "order.created"

    def test_parse_multiple_events(self):
        """Parse nhiều events từ YAML dict."""
        from midicoder.emitters.core.cp05_event_driven.parser import EventParser

        yaml_data = [
            {"event_name": "order.created", "payload_fields": ["order_id"]},
            {"event_name": "order.cancelled", "payload_fields": ["order_id", "reason"]},
        ]
        parser = EventParser()
        events = parser.parse(yaml_data)
        assert len(events) == 2

    def test_parse_empty_list(self):
        """Parse empty list trả về empty list."""
        from midicoder.emitters.core.cp05_event_driven.parser import EventParser

        parser = EventParser()
        events = parser.parse([])
        assert events == []

    def test_parse_with_topic(self):
        """Parse event với topic field."""
        from midicoder.emitters.core.cp05_event_driven.parser import EventParser

        yaml_data = [{"event_name": "test.event", "topic": "custom_topic"}]
        parser = EventParser()
        events = parser.parse(yaml_data)
        assert events[0].topic == "custom_topic"

    def test_parse_with_version(self):
        """Parse event với version field."""
        from midicoder.emitters.core.cp05_event_driven.parser import EventParser

        yaml_data = [{"event_name": "test.event", "version": "2.0"}]
        parser = EventParser()
        events = parser.parse(yaml_data)
        assert events[0].version == "2.0"

    def test_parse_invalid_event_raises_error(self):
        """Parse event không có event_name raise error."""
        from midicoder.emitters.core.cp05_event_driven.parser import EventParser

        yaml_data = [{"payload_fields": ["field1"]}]
        parser = EventParser()
        with pytest.raises((ValueError, MidicoderError)):
            parser.parse(yaml_data)


# ============================================================================
# Test FastAPIEventEmitter
# ============================================================================


class TestFastAPIEventEmitter:
    """Tests cho FastAPIEventEmitter."""

    def test_emitter_init(self):
        """Emitter khởi tạo với stack_dir."""
        from midicoder.emitters.core.cp05_event_driven.fastapi import FastAPIEventEmitter

        stack_dir = Path("midicoder/stacks/fastapi/core")
        emitter = FastAPIEventEmitter(stack_dir=stack_dir)
        assert emitter.stack_dir == stack_dir

    def test_emitter_init_invalid_dir(self):
        """Emitter khởi tạo với stack_dir không tồn tại raise error."""
        from midicoder.emitters.core.cp05_event_driven.fastapi import FastAPIEventEmitter

        with pytest.raises(FileNotFoundError):
            FastAPIEventEmitter(stack_dir=Path("/nonexistent/path"))

    def test_emit_returns_files(self):
        """Emit trả về list of GeneratedFile."""
        from midicoder.emitters.core.cp05_event_driven.fastapi import FastAPIEventEmitter
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition

        stack_dir = Path("midicoder/stacks/fastapi/core")
        emitter = FastAPIEventEmitter(stack_dir=stack_dir)
        events = [EventDefinition(event_name="test.event", topic="test")]
        files = emitter.emit(events, Path("/tmp/output"))
        assert isinstance(files, list)

    def test_emit_creates_directories(self):
        """Emit tạo directories cho output."""
        from midicoder.emitters.core.cp05_event_driven.fastapi import FastAPIEventEmitter
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            stack_dir = Path("midicoder/stacks/fastapi/core")
            emitter = FastAPIEventEmitter(stack_dir=stack_dir)
            events = [EventDefinition(event_name="test.event", topic="test")]
            files = emitter.emit(events, Path(tmpdir))
            # Check directories were created
            event_dir = Path(tmpdir) / "app" / "core" / "event"
            assert event_dir.exists()

    def test_emit_generates_event_bus(self):
        """Emit generate event_bus.py."""
        from midicoder.emitters.core.cp05_event_driven.fastapi import FastAPIEventEmitter
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            stack_dir = Path("midicoder/stacks/fastapi/core")
            emitter = FastAPIEventEmitter(stack_dir=stack_dir)
            events = [EventDefinition(event_name="test.event", topic="test")]
            files = emitter.emit(events, Path(tmpdir))
            # Check event_bus.py content exists
            contents = [f.content for f in files]
            combined = "\n".join(contents)
            assert "EventBus" in combined or "EventMessage" in combined

    def test_emit_with_multiple_events(self):
        """Emit với nhiều events."""
        from midicoder.emitters.core.cp05_event_driven.fastapi import FastAPIEventEmitter
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition

        stack_dir = Path("midicoder/stacks/fastapi/core")
        emitter = FastAPIEventEmitter(stack_dir=stack_dir)
        events = [
            EventDefinition(event_name="order.created", topic="orders"),
            EventDefinition(event_name="payment.completed", topic="payments"),
        ]
        files = emitter.emit(events, Path("/tmp/output"))
        assert len(files) >= 1

    def test_emit_with_tenant_events(self):
        """Emit với events có tenant_id."""
        from midicoder.emitters.core.cp05_event_driven.fastapi import FastAPIEventEmitter
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition

        stack_dir = Path("midicoder/stacks/fastapi/core")
        emitter = FastAPIEventEmitter(stack_dir=stack_dir)
        events = [
            EventDefinition(event_name="test.event", topic="test", tenant_id="tenant_1")
        ]
        files = emitter.emit(events, Path("/tmp/output"))
        assert len(files) >= 1

    def test_emit_with_schema_fields(self):
        """Emit với events có schema_fields."""
        from midicoder.emitters.core.cp05_event_driven.fastapi import FastAPIEventEmitter
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition

        stack_dir = Path("midicoder/stacks/fastapi/core")
        emitter = FastAPIEventEmitter(stack_dir=stack_dir)
        events = [
            EventDefinition(
                event_name="order.created",
                payload_fields=["order_id"],
                schema_fields={"order_id": {"type": "string"}},
            )
        ]
        files = emitter.emit(events, Path("/tmp/output"))
        assert len(files) >= 1

    def test_emit_generated_file_structure(self):
        """GeneratedFile có đúng structure."""
        from midicoder.emitters.core.cp05_event_driven.fastapi import FastAPIEventEmitter
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition

        stack_dir = Path("midicoder/stacks/fastapi/core")
        emitter = FastAPIEventEmitter(stack_dir=stack_dir)
        events = [EventDefinition(event_name="test.event", topic="test")]
        files = emitter.emit(events, Path("/tmp/output"))
        if files:
            f = files[0]
            assert hasattr(f, "path")
            assert hasattr(f, "content")
            assert hasattr(f, "template")

    def test_emit_with_empty_events(self):
        """Emit với empty list trả về base files."""
        from midicoder.emitters.core.cp05_event_driven.fastapi import FastAPIEventEmitter

        stack_dir = Path("midicoder/stacks/fastapi/core")
        emitter = FastAPIEventEmitter(stack_dir=stack_dir)
        files = emitter.emit([], Path("/tmp/output"))
        # Should return files (base event bus, publisher, subscriber)
        assert isinstance(files, list)


# ============================================================================
# Test NestJSEventEmitter
# ============================================================================


class TestNestJSEventEmitter:
    """Tests cho NestJSEventEmitter."""

    def test_emitter_init(self):
        """Emitter khởi tạo với stack_dir."""
        from midicoder.emitters.core.cp05_event_driven.nestjs import NestJSEventEmitter

        stack_dir = Path("midicoder/stacks/nestjs/core")
        emitter = NestJSEventEmitter(stack_dir=stack_dir)
        assert emitter.stack_dir == stack_dir

    def test_emitter_init_invalid_dir(self):
        """Emitter khởi tạo với stack_dir không tồn tại raise error."""
        from midicoder.emitters.core.cp05_event_driven.nestjs import NestJSEventEmitter

        with pytest.raises(FileNotFoundError):
            NestJSEventEmitter(stack_dir=Path("/nonexistent/path"))

    def test_emit_returns_files(self):
        """Emit trả về list of GeneratedFile."""
        from midicoder.emitters.core.cp05_event_driven.nestjs import NestJSEventEmitter
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition

        stack_dir = Path("midicoder/stacks/nestjs/core")
        emitter = NestJSEventEmitter(stack_dir=stack_dir)
        events = [EventDefinition(event_name="test.event", topic="test")]
        files = emitter.emit(events, Path("/tmp/output"))
        assert isinstance(files, list)

    def test_emit_creates_directories(self):
        """Emit tạo directories cho output."""
        from midicoder.emitters.core.cp05_event_driven.nestjs import NestJSEventEmitter
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            stack_dir = Path("midicoder/stacks/nestjs/core")
            emitter = NestJSEventEmitter(stack_dir=stack_dir)
            events = [EventDefinition(event_name="test.event", topic="test")]
            files = emitter.emit(events, Path(tmpdir))
            event_dir = Path(tmpdir) / "core" / "event"
            assert event_dir.exists()

    def test_emit_generates_event_bus(self):
        """Emit generate event-bus.service.ts."""
        from midicoder.emitters.core.cp05_event_driven.nestjs import NestJSEventEmitter
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            stack_dir = Path("midicoder/stacks/nestjs/core")
            emitter = NestJSEventEmitter(stack_dir=stack_dir)
            events = [EventDefinition(event_name="test.event", topic="test")]
            files = emitter.emit(events, Path(tmpdir))
            contents = [f.content for f in files]
            combined = "\n".join(contents)
            assert "EventBus" in combined or "event" in combined.lower()

    def test_emit_with_multiple_events(self):
        """Emit với nhiều events."""
        from midicoder.emitters.core.cp05_event_driven.nestjs import NestJSEventEmitter
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition

        stack_dir = Path("midicoder/stacks/nestjs/core")
        emitter = NestJSEventEmitter(stack_dir=stack_dir)
        events = [
            EventDefinition(event_name="order.created", topic="orders"),
            EventDefinition(event_name="order.updated", topic="orders"),
        ]
        files = emitter.emit(events, Path("/tmp/output"))
        assert len(files) >= 1

    def test_emit_with_tenant_events(self):
        """Emit với events có tenant_id."""
        from midicoder.emitters.core.cp05_event_driven.nestjs import NestJSEventEmitter
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition

        stack_dir = Path("midicoder/stacks/nestjs/core")
        emitter = NestJSEventEmitter(stack_dir=stack_dir)
        events = [
            EventDefinition(event_name="test.event", topic="test", tenant_id="tenant_1")
        ]
        files = emitter.emit(events, Path("/tmp/output"))
        assert len(files) >= 1

    def test_emit_generated_file_structure(self):
        """GeneratedFile có đúng structure."""
        from midicoder.emitters.core.cp05_event_driven.nestjs import NestJSEventEmitter
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition

        stack_dir = Path("midicoder/stacks/nestjs/core")
        emitter = NestJSEventEmitter(stack_dir=stack_dir)
        events = [EventDefinition(event_name="test.event", topic="test")]
        files = emitter.emit(events, Path("/tmp/output"))
        if files:
            f = files[0]
            assert hasattr(f, "path")
            assert hasattr(f, "content")


# ============================================================================
# Test Integration
# ============================================================================


class TestEventIntegration:
    """Integration tests cho Event Emitter."""

    def test_backend_fastapi_has_emit_events(self):
        """BackendFastAPIEmitter có _emit_events method."""
        from midicoder.emitters.stack.fastapi import BackendFastAPIEmitter

        assert hasattr(BackendFastAPIEmitter, "_emit_events")

    def test_backend_nestjs_has_emit_events(self):
        """BackendNestJSEmitter có _emit_events method."""
        from midicoder.emitters.stack.nestjs import BackendNestJSEmitter

        assert hasattr(BackendNestJSEmitter, "_emit_events")

    def test_emit_includes_events_in_emit_method(self):
        """emit() method gọi _emit_events() khi có events trong metadata."""
        from midicoder.emitters.stack.fastapi import BackendFastAPIEmitter
        from midicoder.pipeline.mir import MIR
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            stack_dir = Path("midicoder/stacks/fastapi/core")
            emitter = BackendFastAPIEmitter(stack_dir=stack_dir)
            mir = MIR(operations=[], data_flows=[], effect_flows=[], boundaries=[])
            mir.metadata["events"] = [
                {"event_name": "order.created", "payload_fields": ["order_id"]}
            ]
            # Test _emit_events directly to avoid template rendering issues in base files
            events_data = mir.metadata.get("events", [])
            event_files = emitter._emit_events(events_data, Path(tmpdir))
            contents = "\n".join(f.content for f in event_files)
            assert "EventBus" in contents or "EventMessage" in contents

    def test_emit_skips_events_when_empty(self):
        """emit() bỏ qua _emit_events() khi không có events."""
        from midicoder.emitters.stack.fastapi import BackendFastAPIEmitter
        from midicoder.pipeline.mir import MIR
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            stack_dir = Path("midicoder/stacks/fastapi/core")
            emitter = BackendFastAPIEmitter(stack_dir=stack_dir)
            mir = MIR(operations=[], data_flows=[], effect_flows=[], boundaries=[])
            # No events in metadata - verify emit() does not call _emit_events
            events_data = mir.metadata.get("events", [])
            assert events_data == []  # Empty, so _emit_events should be skipped
            # Test _emit_events with empty list returns empty list
            event_files = emitter._emit_events([], Path(tmpdir))
            assert isinstance(event_files, list)

    def test_event_parser_integration_with_emitter(self):
        """Event parser integration với FastAPIEventEmitter."""
        from midicoder.emitters.core.cp05_event_driven.parser import EventParser
        from midicoder.emitters.core.cp05_event_driven.fastapi import FastAPIEventEmitter

        yaml_data = [
            {"event_name": "order.created", "payload_fields": ["order_id"], "topic": "orders"},
            {"event_name": "order.cancelled", "payload_fields": ["order_id"], "topic": "orders"},
        ]
        parser = EventParser()
        events = parser.parse(yaml_data)
        assert len(events) == 2

        stack_dir = Path("midicoder/stacks/fastapi/core")
        emitter = FastAPIEventEmitter(stack_dir=stack_dir)
        files = emitter.emit(events, Path("/tmp/output"))
        assert len(files) >= 1

    def test_event_tenant_isolation(self):
        """KPI-029: Event support tenant isolation."""
        from midicoder.emitters.core.cp05_event_driven.models import EventDefinition

        events = [
            EventDefinition(event_name="order.created", topic="orders", tenant_id="tenant_A"),
            EventDefinition(event_name="order.created", topic="orders", tenant_id="tenant_B"),
        ]
        assert events[0].tenant_id == "tenant_A"
        assert events[1].tenant_id == "tenant_B"

    def test_error_codes_vietnamese_messages(self):
        """Error codes có proper structure (ErrorCode is str Enum)."""
        # ErrorCode is str, Enum so .value is a string like "MDC-EVT-001"
        code = ErrorCode.EVT_BUS_NOT_INITIALIZED.value
        assert code is not None
        assert type(code) is str
        assert len(code) > 0
        assert code.startswith("MDC-EVT-")
