"""Tests for FastAPI and NestJS event emitters."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from midicoder.emitters.core.cp05_event_driven.fastapi import (
    FastAPIEventEmitter,
    GeneratedFile as FastAPIGeneratedFile,
)
from midicoder.emitters.core.cp05_event_driven.models import EventDefinition
from midicoder.emitters.core.cp05_event_driven.nestjs import (
    NestJSEventEmitter,
    GeneratedFile as NestJSGeneratedFile,
)


# ============================================================================
# FastAPI Event Emitter Tests
# ============================================================================


class TestFastAPIEventEmitter:
    def setup_method(self):
        self.stack_dir = Path("midicoder/stacks/fastapi/core")
        self.emitter = FastAPIEventEmitter(stack_dir=self.stack_dir)
        self.events = [
            EventDefinition(event_name="order.created", topic="orders"),
            EventDefinition(event_name="order.cancelled", topic="orders"),
        ]

    def test_emit_returns_5_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self.emitter.emit(self.events, Path(tmpdir))
            assert len(files) == 5

    def test_emit_file_names(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self.emitter.emit(self.events, Path(tmpdir))
            names = [f.path.name for f in files]
            assert "event_bus.py" in names
            assert "event_publisher.py" in names
            assert "event_subscriber.py" in names
            assert "event_outbox.py" in names
            assert "__init__.py" in names

    def test_emit_content_not_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self.emitter.emit(self.events, Path(tmpdir))
            for f in files:
                assert len(f.content) > 0
                assert isinstance(f.content, str)

    def test_emit_with_tenant_events(self):
        tenant_events = [
            EventDefinition(event_name="x", tenant_id="t1"),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self.emitter.emit(tenant_events, Path(tmpdir))
            assert len(files) == 5

    def test_emit_with_empty_events(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self.emitter.emit([], Path(tmpdir))
            assert len(files) == 5

    def test_render_file_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            gf = self.emitter._render_file(
                template_name="nonexistent.py.jinja2",
                filename="nonexistent.py",
                output_dir=Path(tmpdir),
                context={"events": []},
            )
            assert "auto-generated" in gf.content

    def test_template_dir_mismatch_raises(self):
        with pytest.raises(FileNotFoundError):
            FastAPIEventEmitter(stack_dir=Path("/nonexistent/path"))

    def test_generated_file_attributes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self.emitter.emit(self.events, Path(tmpdir))
            gf = files[0]
            assert isinstance(gf, FastAPIGeneratedFile)
            assert hasattr(gf, "path")
            assert hasattr(gf, "content")
            assert hasattr(gf, "template")


# ============================================================================
# NestJS Event Emitter Tests
# ============================================================================


class TestNestJSEventEmitter:
    def setup_method(self):
        self.stack_dir = Path("midicoder/stacks/nestjs/core")
        self.emitter = NestJSEventEmitter(stack_dir=self.stack_dir)
        self.events = [
            EventDefinition(event_name="order.created", topic="orders"),
            EventDefinition(event_name="payment.completed", topic="payments"),
        ]

    def test_emit_returns_6_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self.emitter.emit(self.events, Path(tmpdir))
            assert len(files) == 6

    def test_emit_file_names(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self.emitter.emit(self.events, Path(tmpdir))
            names = [f.path.name for f in files]
            assert "event-bus.service.ts" in names
            assert "event-publisher.service.ts" in names
            assert "event-subscriber.service.ts" in names
            assert "event-outbox.service.ts" in names
            assert "event.module.ts" in names
            assert "index.ts" in names

    def test_emit_content_not_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self.emitter.emit(self.events, Path(tmpdir))
            for f in files:
                assert len(f.content) > 0

    def test_emit_with_tenant_events(self):
        tenant_events = [EventDefinition(event_name="x", tenant_id="t1")]
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self.emitter.emit(tenant_events, Path(tmpdir))
            assert len(files) == 6

    def test_emit_with_empty_events(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self.emitter.emit([], Path(tmpdir))
            assert len(files) == 6

    def test_render_file_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            gf = self.emitter._render_file(
                template_name="nonexistent.ts.jinja2",
                filename="nonexistent.ts",
                output_dir=Path(tmpdir),
                context={"events": []},
            )
            assert "auto-generated" in gf.content

    def test_template_dir_mismatch_raises(self):
        with pytest.raises(FileNotFoundError):
            NestJSEventEmitter(stack_dir=Path("/nonexistent/path"))

    def test_generated_file_attributes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self.emitter.emit(self.events, Path(tmpdir))
            gf = files[0]
            assert isinstance(gf, NestJSGeneratedFile)
            assert hasattr(gf, "path")
            assert hasattr(gf, "content")
            assert hasattr(gf, "template")


# ============================================================================
# Template content verification
# ============================================================================


class TestTemplateContent:
    def test_fastapi_templates_exist(self):
        base = Path("midicoder/stacks/fastapi/core/cp05_event_driven")
        assert (base / "event_bus.py.jinja2").exists()
        assert (base / "event_publisher.py.jinja2").exists()
        assert (base / "event_subscriber.py.jinja2").exists()
        assert (base / "event_outbox.py.jinja2").exists()
        assert (base / "__init__.py.jinja2").exists()

    def test_nestjs_templates_exist(self):
        base = Path("midicoder/stacks/nestjs/core/cp05_event_driven")
        assert (base / "event-bus.service.ts.jinja2").exists()
        assert (base / "event-publisher.service.ts.jinja2").exists()
        assert (base / "event-subscriber.service.ts.jinja2").exists()
        assert (base / "event-outbox.service.ts.jinja2").exists()
        assert (base / "event.module.ts.jinja2").exists()
        assert (base / "index.ts.jinja2").exists()

    def test_fastapi_bus_has_eventbus_class(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            emitter = FastAPIEventEmitter(stack_dir=Path("midicoder/stacks/fastapi/core"))
            files = emitter.emit([EventDefinition(event_name="x")], Path(tmpdir))
            bus = [f for f in files if "bus" in f.path.name][0]
            assert "class EventBus" in bus.content

    def test_nestjs_bus_has_service_class(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            emitter = NestJSEventEmitter(stack_dir=Path("midicoder/stacks/nestjs/core"))
            files = emitter.emit([EventDefinition(event_name="x")], Path(tmpdir))
            bus = [f for f in files if "bus" in f.path.name][0]
            assert "EventBusService" in bus.content

    def test_nestjs_no_logger_warning(self):
        """Verify NestJS templates use .warn() not .warning()."""
        base = Path("midicoder/stacks/nestjs/core/cp05_event_driven")
        for f in base.glob("*.jinja2"):
            content = f.read_text(encoding="utf-8")
            assert ".warning(" not in content, f"{f.name} still uses .warning()"
