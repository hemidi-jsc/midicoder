"""
Tests cho CP05 features mới — OutboxEntry, pack.yml, capabilities, outbox templates.

Test coverage:
- OutboxEntry model: 8 tests
- Pack manifest (pack.yml): 6 tests
- Core capabilities (subscribe_event, event_outbox): 9 tests
- Outbox template generation: 9 tests

Tổng: 32 tests
"""

from __future__ import annotations

from pathlib import Path

import pytest


# ============================================================================
# Test OutboxEntry Model
# ============================================================================


class TestOutboxEntryModel:
    """Tests cho OutboxEntry data model."""

    def test_outbox_entry_creation(self):
        """OutboxEntry có thể tạo với event_name và payload."""
        from midicoder.emitters.core.event.models import OutboxEntry

        entry = OutboxEntry(
            event_name="order.created",
            payload={"order_id": "123", "total": 100},
            topic="orders",
        )
        assert entry.event_name == "order.created"
        assert entry.payload["order_id"] == "123"
        assert entry.topic == "orders"
        assert entry.status == "pending"

    def test_outbox_entry_defaults(self):
        """OutboxEntry có default values."""
        from midicoder.emitters.core.event.models import OutboxEntry

        entry = OutboxEntry(event_name="test.event")
        assert entry.event_name == "test.event"
        assert entry.topic == "default"
        assert entry.status == "pending"
        assert entry.visibility_delay == 0
        assert entry.retries == 0

    def test_outbox_entry_with_transaction_id(self):
        """OutboxEntry support transaction_id."""
        from midicoder.emitters.core.event.models import OutboxEntry

        entry = OutboxEntry(
            event_name="order.created",
            payload={},
            transaction_id="txn_123",
        )
        assert entry.transaction_id == "txn_123"

    def test_outbox_entry_with_visibility_delay(self):
        """OutboxEntry support visibility_delay."""
        from midicoder.emitters.core.event.models import OutboxEntry

        entry = OutboxEntry(
            event_name="order.created",
            visibility_delay=30,
        )
        assert entry.visibility_delay == 30

    def test_outbox_entry_to_dict(self):
        """OutboxEntry.to_dict() trả về dict."""
        from midicoder.emitters.core.event.models import OutboxEntry

        entry = OutboxEntry(
            event_name="order.created",
            payload={"order_id": "123"},
            topic="orders",
            transaction_id="txn_123",
        )
        result = entry.to_dict()
        assert isinstance(result, dict)
        assert result["event_name"] == "order.created"
        assert result["topic"] == "orders"
        assert result["transaction_id"] == "txn_123"
        assert result["status"] == "pending"

    def test_outbox_entry_from_dict(self):
        """OutboxEntry.from_dict() tạo object từ dict."""
        from midicoder.emitters.core.event.models import OutboxEntry

        data = {
            "event_name": "payment.completed",
            "payload": {"payment_id": "pay_123"},
            "topic": "payments",
            "transaction_id": "txn_456",
            "visibility_delay": 10,
            "status": "published",
        }
        entry = OutboxEntry.from_dict(data)
        assert entry.event_name == "payment.completed"
        assert entry.topic == "payments"
        assert entry.transaction_id == "txn_456"
        assert entry.visibility_delay == 10
        assert entry.status == "published"

    def test_outbox_entry_status_update(self):
        """OutboxEntry có thể update status."""
        from midicoder.emitters.core.event.models import OutboxEntry

        entry = OutboxEntry(event_name="test.event")
        assert entry.status == "pending"
        entry.status = "published"
        assert entry.status == "published"

    def test_outbox_entry_published_at(self):
        """OutboxEntry có published_at khi publish thành công."""
        from midicoder.emitters.core.event.models import OutboxEntry

        entry = OutboxEntry(event_name="test.event")
        assert entry.published_at is None
        entry.published_at = "2024-01-01T00:00:00Z"
        assert entry.published_at == "2024-01-01T00:00:00Z"


# ============================================================================
# Test Pack Manifest
# ============================================================================


class TestPackManifest:
    """Tests cho pack.yml manifest của CP05."""

    def test_pack_yml_exists(self):
        """pack.yml tồn tại trong event directory."""
        pack_path = Path("midicoder/emitters/core/event/pack.yml")
        assert pack_path.exists()

    def test_pack_yml_has_correct_id(self):
        """pack.yml có id là CP05."""
        import yaml

        pack_path = Path("midicoder/emitters/core/event/pack.yml")
        with open(pack_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["id"] == "CP05"

    def test_pack_yml_has_correct_name(self):
        """pack.yml có name là Event-Driven Architecture Generator."""
        import yaml

        pack_path = Path("midicoder/emitters/core/event/pack.yml")
        with open(pack_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "Event-Driven" in data["pack"]["name"]

    def test_pack_yml_capabilities_provided(self):
        """pack.yml có capabilities_provided đúng."""
        import yaml

        pack_path = Path("midicoder/emitters/core/event/pack.yml")
        with open(pack_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        caps = data["pack"]["capabilities_provided"]
        assert "publish_event" in caps
        assert "subscribe_event" in caps
        assert "event_outbox" in caps

    def test_pack_yml_status_is_stable(self):
        """pack.yml có status là stable."""
        import yaml

        pack_path = Path("midicoder/emitters/core/event/pack.yml")
        with open(pack_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["status"] == "stable"

    def test_pack_yml_error_codes_prefix(self):
        """pack.yml có error_codes prefix là MDC-EVT."""
        import yaml

        pack_path = Path("midicoder/emitters/core/event/pack.yml")
        with open(pack_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["error_codes"]["prefix"] == "MDC-EVT"


# ============================================================================
# Test Core Capabilities (subscribe_event + event_outbox)
# ============================================================================


class TestEventCoreCapabilities:
    """Tests cho Event & Integration Core Capabilities."""

    def test_subscribe_event_capability_exists(self):
        """subscribe_event capability tồn tại trong EventIntegrationCoreCapabilities."""
        from midicoder.contracts.core_capabilities import EventIntegrationCoreCapabilities

        caps = EventIntegrationCoreCapabilities()
        assert hasattr(caps, "SUBSCRIBE_EVENT")

    def test_subscribe_event_capability_id(self):
        """subscribe_event capability có id là subscribe_event."""
        from midicoder.contracts.core_capabilities import EventIntegrationCoreCapabilities

        caps = EventIntegrationCoreCapabilities()
        assert caps.SUBSCRIBE_EVENT.id == "subscribe_event"

    def test_subscribe_event_capability_params(self):
        """subscribe_event capability có params_schema đúng."""
        from midicoder.contracts.core_capabilities import EventIntegrationCoreCapabilities

        caps = EventIntegrationCoreCapabilities()
        params = caps.SUBSCRIBE_EVENT.params_schema
        assert "event_type" in params
        assert "handler" in params
        assert "auto_ack" in params

    def test_subscribe_event_capability_obligations(self):
        """subscribe_event capability có default_obligations."""
        from midicoder.contracts.core_capabilities import EventIntegrationCoreCapabilities

        caps = EventIntegrationCoreCapabilities()
        obligations = caps.SUBSCRIBE_EVENT.default_obligations
        assert "handler_required" in obligations

    def test_event_outbox_capability_exists(self):
        """event_outbox capability tồn tại trong EventIntegrationCoreCapabilities."""
        from midicoder.contracts.core_capabilities import EventIntegrationCoreCapabilities

        caps = EventIntegrationCoreCapabilities()
        assert hasattr(caps, "EVENT_OUTBOX")

    def test_event_outbox_capability_id(self):
        """event_outbox capability có id là event_outbox."""
        from midicoder.contracts.core_capabilities import EventIntegrationCoreCapabilities

        caps = EventIntegrationCoreCapabilities()
        assert caps.EVENT_OUTBOX.id == "event_outbox"

    def test_event_outbox_capability_params(self):
        """event_outbox capability có params_schema đúng."""
        from midicoder.contracts.core_capabilities import EventIntegrationCoreCapabilities

        caps = EventIntegrationCoreCapabilities()
        params = caps.EVENT_OUTBOX.params_schema
        assert "event_type" in params
        assert "payload" in params
        assert "transaction_id" in params

    def test_event_outbox_capability_obligations(self):
        """event_outbox capability có default_obligations."""
        from midicoder.contracts.core_capabilities import EventIntegrationCoreCapabilities

        caps = EventIntegrationCoreCapabilities()
        obligations = caps.EVENT_OUTBOX.default_obligations
        assert "transaction_required" in obligations
        assert "outbox_write_required" in obligations

    def test_publish_event_capability_exists(self):
        """publish_event capability vẫn tồn tại (không bị remove)."""
        from midicoder.contracts.core_capabilities import EventIntegrationCoreCapabilities

        caps = EventIntegrationCoreCapabilities()
        assert hasattr(caps, "PUBLISH_EVENT")
        assert caps.PUBLISH_EVENT.id == "publish_event"


# ============================================================================
# Test Outbox Template Generation
# ============================================================================


class TestOutboxTemplateGeneration:
    """Tests cho outbox template generation."""

    def test_fastapi_emitter_generates_outbox_file(self):
        """FastAPIEventEmitter generate event_outbox.py."""
        from midicoder.emitters.core.event.fastapi import FastAPIEventEmitter
        from midicoder.emitters.core.event.models import EventDefinition
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            stack_dir = Path("midicoder/stacks/fastapi/core")
            emitter = FastAPIEventEmitter(stack_dir=stack_dir)
            events = [EventDefinition(event_name="test.event", topic="test")]
            files = emitter.emit(events, Path(tmpdir))
            filenames = [str(f.path) for f in files]
            combined = " ".join(filenames)
            assert "event_outbox" in combined

    def test_nestjs_emitter_generates_outbox_file(self):
        """NestJSEventEmitter generate event-outbox.service.ts."""
        from midicoder.emitters.core.event.nestjs import NestJSEventEmitter
        from midicoder.emitters.core.event.models import EventDefinition
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            stack_dir = Path("midicoder/stacks/nestjs/core")
            emitter = NestJSEventEmitter(stack_dir=stack_dir)
            events = [EventDefinition(event_name="test.event", topic="test")]
            files = emitter.emit(events, Path(tmpdir))
            filenames = [str(f.path) for f in files]
            combined = " ".join(filenames)
            assert "outbox" in combined

    def test_fastapi_outbox_template_exists(self):
        """FastAPI outbox template file tồn tại."""
        template_path = Path("midicoder/stacks/fastapi/core/event/event_outbox.py.jinja2")
        assert template_path.exists()

    def test_nestjs_outbox_template_exists(self):
        """NestJS outbox template file tồn tại."""
        template_path = Path("midicoder/stacks/nestjs/core/event/event-outbox.service.ts.jinja2")
        assert template_path.exists()

    def test_fastapi_outbox_template_content(self):
        """FastAPI outbox template có nội dung đúng."""
        template_path = Path("midicoder/stacks/fastapi/core/event/event_outbox.py.jinja2")
        content = template_path.read_text(encoding="utf-8")
        assert "EventOutbox" in content
        assert "OutboxEntry" in content

    def test_nestjs_outbox_template_content(self):
        """NestJS outbox template có nội dung đúng."""
        template_path = Path("midicoder/stacks/nestjs/core/event/event-outbox.service.ts.jinja2")
        content = template_path.read_text(encoding="utf-8")
        assert "EventOutboxService" in content
        assert "OutboxEntry" in content

    def test_outbox_in_init_exports(self):
        """__init__.py export OutboxEntry."""
        from midicoder.emitters.core.event import OutboxEntry
        assert OutboxEntry is not None

    def test_fastapi_emit_includes_5_files(self):
        """FastAPIEventEmitter.emit() trả về 5 files (bus, publisher, subscriber, outbox, init)."""
        from midicoder.emitters.core.event.fastapi import FastAPIEventEmitter
        from midicoder.emitters.core.event.models import EventDefinition

        stack_dir = Path("midicoder/stacks/fastapi/core")
        emitter = FastAPIEventEmitter(stack_dir=stack_dir)
        events = [EventDefinition(event_name="test.event")]
        files = emitter.emit(events, Path("/tmp/output"))
        assert len(files) == 5  # event_bus, event_publisher, event_subscriber, event_outbox, __init__

    def test_nestjs_emit_includes_6_files(self):
        """NestJSEventEmitter.emit() trả về 6 files (bus, publisher, subscriber, outbox, module, index)."""
        from midicoder.emitters.core.event.nestjs import NestJSEventEmitter
        from midicoder.emitters.core.event.models import EventDefinition

        stack_dir = Path("midicoder/stacks/nestjs/core")
        emitter = NestJSEventEmitter(stack_dir=stack_dir)
        events = [EventDefinition(event_name="test.event")]
        files = emitter.emit(events, Path("/tmp/output"))
        assert len(files) == 6  # bus, publisher, subscriber, outbox, module, index


# ============================================================================
# Test Coverage Gap Filling
# ============================================================================


class TestCoverageGaps:
    """Tests để đạt 100% coverage cho các conditional branches và error paths."""

    def test_event_definition_to_dict_with_tenant_and_schema(self):
        """EventDefinition.to_dict() include tenant_id và schema_fields khi có giá trị."""
        from midicoder.emitters.core.event.models import EventDefinition

        event = EventDefinition(
            event_name="order.created",
            payload_fields=["order_id"],
            tenant_id="tenant_123",
            schema_fields={"order_id": {"type": "string"}},
        )
        result = event.to_dict()
        assert result["tenant_id"] == "tenant_123"
        assert result["schema_fields"] == {"order_id": {"type": "string"}}

    def test_outbox_entry_to_dict_with_all_fields(self):
        """OutboxEntry.to_dict() include tất cả optional fields khi có giá trị."""
        from midicoder.emitters.core.event.models import OutboxEntry

        entry = OutboxEntry(
            event_name="test.event",
            payload={"id": 1},
            transaction_id="txn_123",
            visibility_delay=30,
            created_at="2024-01-01T00:00:00Z",
            published_at="2024-01-01T01:00:00Z",
        )
        result = entry.to_dict()
        assert result["transaction_id"] == "txn_123"
        assert result["visibility_delay"] == 30
        assert result["created_at"] == "2024-01-01T00:00:00Z"
        assert result["published_at"] == "2024-01-01T01:00:00Z"

    def test_outbox_entry_to_dict_with_zero_delay(self):
        """OutboxEntry.to_dict() không include visibility_delay khi = 0."""
        from midicoder.emitters.core.event.models import OutboxEntry

        entry = OutboxEntry(
            event_name="test.event",
            payload={"id": 1},
            transaction_id=None,
            visibility_delay=0,
            created_at=None,
            published_at=None,
        )
        result = entry.to_dict()
        assert "transaction_id" not in result
        assert "visibility_delay" not in result
        assert "created_at" not in result
        assert "published_at" not in result

    def test_fastapi_template_not_found_fallback(self):
        """FastAPIEventEmitter _render_file fallback khi template không tồn tại."""
        import tempfile
        from midicoder.emitters.core.event.fastapi import FastAPIEventEmitter
        from midicoder.emitters.core.event.models import EventDefinition

        with tempfile.TemporaryDirectory() as tmpdir:
            stack_dir = Path("midicoder/stacks/fastapi/core")
            emitter = FastAPIEventEmitter(stack_dir=stack_dir)
            events = [EventDefinition(event_name="test.event")]
            # Template "nonexistent.py.jinja2" không tồn tại, nên fallback
            files = emitter.emit(events, Path(tmpdir))
            # Kiểm tra _render_file xử lý TemplateNotFound
            file_path = Path(tmpdir) / "app" / "core" / "event" / "nonexistent.py"
            # Force trigger TemplateNotFound bằng cách gọi _render_file trực tiếp
            gf = emitter._render_file(
                template_name="nonexistent.py.jinja2",
                filename="nonexistent.py",
                output_dir=Path(tmpdir) / "app" / "core" / "event",
                context={"events": events},
            )
            assert "auto-generated" in gf.content

    def test_nestjs_template_not_found_fallback(self):
        """NestJSEventEmitter _render_file fallback khi template không tồn tại."""
        import tempfile
        from midicoder.emitters.core.event.nestjs import NestJSEventEmitter
        from midicoder.emitters.core.event.models import EventDefinition

        with tempfile.TemporaryDirectory() as tmpdir:
            stack_dir = Path("midicoder/stacks/nestjs/core")
            emitter = NestJSEventEmitter(stack_dir=stack_dir)
            events = [EventDefinition(event_name="test.event")]
            # Force trigger TemplateNotFound bằng cách gọi _render_file trực tiếp
            gf = emitter._render_file(
                template_name="nonexistent.ts.jinja2",
                filename="nonexistent.ts",
                output_dir=Path(tmpdir) / "core" / "event",
                context={"events": events},
            )
            assert "auto-generated" in gf.content

    def test_init_exports_all_symbols(self):
        """__init__.py export tất cả symbols."""
        from midicoder.emitters.core.event import (
            EventDefinition,
            OutboxEntry,
            EventParser,
            FastAPIEventEmitter,
            NestJSEventEmitter,
        )
        assert EventDefinition is not None
        assert OutboxEntry is not None
        assert EventParser is not None
        assert FastAPIEventEmitter is not None
        assert NestJSEventEmitter is not None
