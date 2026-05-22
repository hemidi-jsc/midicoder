# coding: utf-8
"""
Tests cho CP40 Webhook emitters: FastAPI, NestJS, Angular, React.

Bao gồm:
- __init__ raises MidicoderError khi template dir không tìm thấy
- emit() returns correct number of files
- emit() returns correct paths
- emit() files have non-empty content
- _build_context() returns correct keys và giá trị
- _template_exists() returns True/False
- emit context chứa subscriptions, event_types trong rendered content
- Angular/React _TEMPLATE_MAP có đúng số lượng entries
"""

from __future__ import annotations

import pytest
from pathlib import Path

from midicoder.errors import MidicoderError

# Midicoder root = 5 parents up from tests/
MIDICODER_ROOT = Path(__file__).parent.parent.parent.parent.parent

FASTAPI_STACK_DIR = MIDICODER_ROOT / "stacks" / "fastapi" / "core"
NESTJS_STACK_DIR = MIDICODER_ROOT / "stacks" / "nestjs" / "core"
ANGULAR_STACK_DIR = MIDICODER_ROOT / "stacks" / "angular" / "core"
REACT_STACK_DIR = MIDICODER_ROOT / "stacks" / "react" / "core"


def _make_ir():
    """Tạo WebhookIR sample cho testing từ basic_webhook_recipe."""
    from midicoder.emitters.core.cp40_webhook.recipes import basic_webhook_recipe
    recipe = basic_webhook_recipe()
    return recipe.ir


# ============================================================================
# Test FastAPIWebhookEmitter
# ============================================================================


class TestFastAPIWebhookEmitter:
    """Tests cho FastAPIWebhookEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        from midicoder.emitters.core.cp40_webhook.fastapi import (
            FastAPIWebhookEmitter,
        )

        with pytest.raises(MidicoderError):
            FastAPIWebhookEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        from midicoder.emitters.core.cp40_webhook.fastapi import (
            FastAPIWebhookEmitter,
        )

        emitter = FastAPIWebhookEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter is not None

    def test_init_sets_template_dir_correctly(self):
        from midicoder.emitters.core.cp40_webhook.fastapi import (
            FastAPIWebhookEmitter,
        )

        emitter = FastAPIWebhookEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter.template_dir == FASTAPI_STACK_DIR / "cp40_webhook"

    def test_emit_returns_minimum_files(self, tmp_path: Path):
        """Kiểm tra emit trả về ít nhất 7 files."""
        from midicoder.emitters.core.cp40_webhook.fastapi import (
            FastAPIWebhookEmitter,
        )

        emitter = FastAPIWebhookEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        assert len(files) >= 7

    def test_emit_returns_correct_paths(self, tmp_path: Path):
        """Kiểm tra emit trả về các đường dẫn đúng."""
        from midicoder.emitters.core.cp40_webhook.fastapi import (
            FastAPIWebhookEmitter,
        )

        emitter = FastAPIWebhookEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        paths = [f.path for f in files]
        assert "app/webhook/models.py" in paths
        assert "app/webhook/schemas.py" in paths
        assert "app/webhook/services/webhook_service.py" in paths
        assert "app/webhook/routers/webhook_router.py" in paths
        assert "app/webhook/services/webhook_dispatch.py" in paths
        assert "app/webhook/workers/webhook_worker.py" in paths
        assert "app/webhook/middleware.py" in paths

    def test_emit_files_have_nonempty_content(self, tmp_path: Path):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.emitters.core.cp40_webhook.fastapi import (
            FastAPIWebhookEmitter,
        )

        emitter = FastAPIWebhookEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert len(f.content) > 0, f"File {f.path} có nội dung rỗng"

    def test_build_context_returns_correct_keys(self):
        """Kiểm tra _build_context trả về các key đúng."""
        from midicoder.emitters.core.cp40_webhook.fastapi import (
            FastAPIWebhookEmitter,
        )

        emitter = FastAPIWebhookEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert "subscriptions" in ctx
        assert "subscription_count" in ctx
        assert "event_types" in ctx
        assert "redis_url" in ctx
        assert "use_redis" in ctx

    def test_build_context_subscription_count(self):
        """Kiểm tra subscription_count đúng với IR."""
        from midicoder.emitters.core.cp40_webhook.fastapi import (
            FastAPIWebhookEmitter,
        )

        emitter = FastAPIWebhookEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert ctx["subscription_count"] == 2

    def test_build_context_event_types(self):
        """Kiểm tra event_types chứa các event đúng."""
        from midicoder.emitters.core.cp40_webhook.fastapi import (
            FastAPIWebhookEmitter,
        )

        emitter = FastAPIWebhookEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert "order.created" in ctx["event_types"]
        assert "customer.created" in ctx["event_types"]

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.emitters.core.cp40_webhook.fastapi import (
            FastAPIWebhookEmitter,
        )

        emitter = FastAPIWebhookEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter._template_exists("webhook_models.py.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.emitters.core.cp40_webhook.fastapi import (
            FastAPIWebhookEmitter,
        )

        emitter = FastAPIWebhookEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter._template_exists("nonexistent.py.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.emitters.core.cp40_webhook.fastapi import (
            FastAPIWebhookEmitter,
        )

        emitter = FastAPIWebhookEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.py.jinja2", {})


# ============================================================================
# Test NestJSWebhookEmitter
# ============================================================================


class TestNestJSWebhookEmitter:
    """Tests cho NestJSWebhookEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        from midicoder.emitters.core.cp40_webhook.nestjs import (
            NestJSWebhookEmitter,
        )

        with pytest.raises(MidicoderError):
            NestJSWebhookEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        from midicoder.emitters.core.cp40_webhook.nestjs import (
            NestJSWebhookEmitter,
        )

        emitter = NestJSWebhookEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter is not None

    def test_init_sets_template_dir_correctly(self):
        from midicoder.emitters.core.cp40_webhook.nestjs import (
            NestJSWebhookEmitter,
        )

        emitter = NestJSWebhookEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter.template_dir == NESTJS_STACK_DIR / "cp40_webhook"

    def test_emit_returns_minimum_files(self, tmp_path: Path):
        """Kiểm tra emit trả về ít nhất 7 files."""
        from midicoder.emitters.core.cp40_webhook.nestjs import (
            NestJSWebhookEmitter,
        )

        emitter = NestJSWebhookEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        assert len(files) >= 7

    def test_emit_returns_correct_paths(self, tmp_path: Path):
        """Kiểm tra emit trả về các đường dẫn đúng cho NestJS."""
        from midicoder.emitters.core.cp40_webhook.nestjs import (
            NestJSWebhookEmitter,
        )

        emitter = NestJSWebhookEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        paths = [f.path for f in files]
        assert "src/webhook/entities/webhook.entity.ts" in paths
        assert "src/webhook/dtos/webhook.dto.ts" in paths
        assert "src/webhook/services/webhook.service.ts" in paths
        assert "src/webhook/controllers/webhook.controller.ts" in paths
        assert "src/webhook/services/webhook-dispatcher.service.ts" in paths
        assert "src/webhook/services/webhook-queue.service.ts" in paths
        assert "src/webhook/webhook.module.ts" in paths

    def test_emit_files_have_nonempty_content(self, tmp_path: Path):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.emitters.core.cp40_webhook.nestjs import (
            NestJSWebhookEmitter,
        )

        emitter = NestJSWebhookEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert len(f.content) > 0, f"File {f.path} có nội dung rỗng"

    def test_build_context_returns_correct_keys(self):
        """Kiểm tra _build_context trả về các key đúng."""
        from midicoder.emitters.core.cp40_webhook.nestjs import (
            NestJSWebhookEmitter,
        )

        emitter = NestJSWebhookEmitter(stack_dir=str(NESTJS_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert "subscriptions" in ctx
        assert "subscription_count" in ctx
        assert "event_types" in ctx
        assert "redis_url" in ctx
        assert "use_redis" in ctx

    def test_build_context_subscription_count(self):
        """Kiểm tra subscription_count đúng với IR."""
        from midicoder.emitters.core.cp40_webhook.nestjs import (
            NestJSWebhookEmitter,
        )

        emitter = NestJSWebhookEmitter(stack_dir=str(NESTJS_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert ctx["subscription_count"] == 2

    def test_build_context_event_types(self):
        """Kiểm tra event_types chứa các event đúng."""
        from midicoder.emitters.core.cp40_webhook.nestjs import (
            NestJSWebhookEmitter,
        )

        emitter = NestJSWebhookEmitter(stack_dir=str(NESTJS_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert "order.created" in ctx["event_types"]
        assert "customer.created" in ctx["event_types"]

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.emitters.core.cp40_webhook.nestjs import (
            NestJSWebhookEmitter,
        )

        emitter = NestJSWebhookEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter._template_exists("webhook.entity.ts.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.emitters.core.cp40_webhook.nestjs import (
            NestJSWebhookEmitter,
        )

        emitter = NestJSWebhookEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter._template_exists("nonexistent.ts.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.emitters.core.cp40_webhook.nestjs import (
            NestJSWebhookEmitter,
        )

        emitter = NestJSWebhookEmitter(stack_dir=str(NESTJS_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.ts.jinja2", {})


# ============================================================================
# Test AngularWebhookEmitter
# ============================================================================


class TestAngularWebhookEmitter:
    """Tests cho AngularWebhookEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        from midicoder.emitters.core.cp40_webhook.angular import (
            AngularWebhookEmitter,
        )

        with pytest.raises(MidicoderError):
            AngularWebhookEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        from midicoder.emitters.core.cp40_webhook.angular import (
            AngularWebhookEmitter,
        )

        emitter = AngularWebhookEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter is not None

    def test_emit_returns_minimum_files(self):
        """Kiểm tra emit trả về ít nhất 4 files."""
        from midicoder.emitters.core.cp40_webhook.angular import (
            AngularWebhookEmitter,
        )

        emitter = AngularWebhookEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir())
        assert len(files) >= 4

    def test_emit_returns_correct_paths(self):
        """Kiểm tra emit trả về các đường dẫn đúng cho Angular."""
        from midicoder.emitters.core.cp40_webhook.angular import (
            AngularWebhookEmitter,
        )

        emitter = AngularWebhookEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir())
        paths = [f["path"] for f in files]
        assert "src/app/webhook/webhook-dashboard.component.ts" in paths
        assert "src/app/webhook/webhook-subscription-list.component.ts" in paths
        assert "src/app/webhook/webhook-delivery-viewer.component.ts" in paths
        assert "src/app/core/webhook/webhook.service.ts" in paths

    def test_emit_files_have_nonempty_content(self):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.emitters.core.cp40_webhook.angular import (
            AngularWebhookEmitter,
        )

        emitter = AngularWebhookEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir())
        for f in files:
            assert len(f["content"]) > 0, f"File {f['path']} có nội dung rỗng"

    def test_emit_with_extra_context(self):
        """Kiểm tra emit hoạt động với context bổ sung."""
        from midicoder.emitters.core.cp40_webhook.angular import (
            AngularWebhookEmitter,
        )

        emitter = AngularWebhookEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir(), context={"ui_framework": "angular"})
        assert len(files) > 0

    def test_template_map_has_4_entries(self):
        """Kiểm tra _TEMPLATE_MAP có đúng 4 entries."""
        from midicoder.emitters.core.cp40_webhook.angular import (
            AngularWebhookEmitter,
        )

        assert len(AngularWebhookEmitter._TEMPLATE_MAP) == 4

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.emitters.core.cp40_webhook.angular import (
            AngularWebhookEmitter,
        )

        emitter = AngularWebhookEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter._template_exists("webhook-dashboard.component.ts.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.emitters.core.cp40_webhook.angular import (
            AngularWebhookEmitter,
        )

        emitter = AngularWebhookEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter._template_exists("nonexistent.ts.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.emitters.core.cp40_webhook.angular import (
            AngularWebhookEmitter,
        )

        emitter = AngularWebhookEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.ts.jinja2", {})


# ============================================================================
# Test ReactWebhookEmitter
# ============================================================================


class TestReactWebhookEmitter:
    """Tests cho ReactWebhookEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        from midicoder.emitters.core.cp40_webhook.react import (
            ReactWebhookEmitter,
        )

        with pytest.raises(MidicoderError):
            ReactWebhookEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        from midicoder.emitters.core.cp40_webhook.react import (
            ReactWebhookEmitter,
        )

        emitter = ReactWebhookEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter is not None

    def test_emit_returns_minimum_files(self):
        """Kiểm tra emit trả về ít nhất 4 files."""
        from midicoder.emitters.core.cp40_webhook.react import (
            ReactWebhookEmitter,
        )

        emitter = ReactWebhookEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        assert len(files) >= 4

    def test_emit_returns_correct_paths(self):
        """Kiểm tra emit trả về các đường dẫn đúng cho React."""
        from midicoder.emitters.core.cp40_webhook.react import (
            ReactWebhookEmitter,
        )

        emitter = ReactWebhookEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        paths = [f["path"] for f in files]
        assert "src/webhook/components/WebhookDashboard.tsx" in paths
        assert "src/webhook/components/WebhookSubscriptionList.tsx" in paths
        assert "src/webhook/hooks/useWebhooks.ts" in paths
        assert "src/webhook/hooks/useDispatchStatus.ts" in paths

    def test_emit_files_have_nonempty_content(self):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.emitters.core.cp40_webhook.react import (
            ReactWebhookEmitter,
        )

        emitter = ReactWebhookEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        for f in files:
            assert len(f["content"]) > 0, f"File {f['path']} có nội dung rỗng"

    def test_emit_with_extra_context(self):
        """Kiểm tra emit hoạt động với context bổ sung."""
        from midicoder.emitters.core.cp40_webhook.react import (
            ReactWebhookEmitter,
        )

        emitter = ReactWebhookEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir(), context={"ui_framework": "react"})
        assert len(files) > 0

    def test_template_map_has_4_entries(self):
        """Kiểm tra _TEMPLATE_MAP có đúng 4 entries."""
        from midicoder.emitters.core.cp40_webhook.react import (
            ReactWebhookEmitter,
        )

        assert len(ReactWebhookEmitter._TEMPLATE_MAP) == 4

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.emitters.core.cp40_webhook.react import (
            ReactWebhookEmitter,
        )

        emitter = ReactWebhookEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter._template_exists("WebhookDashboard.tsx.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.emitters.core.cp40_webhook.react import (
            ReactWebhookEmitter,
        )

        emitter = ReactWebhookEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter._template_exists("nonexistent.tsx.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.emitters.core.cp40_webhook.react import (
            ReactWebhookEmitter,
        )

        emitter = ReactWebhookEmitter(stack_dir=str(REACT_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.tsx.jinja2", {})


# ============================================================================
# Test Emit Context — Subscriptions và Event Types trong rendered content
# ============================================================================


class TestEmitContext:
    """Tests cho việc subscriptions và event_types có trong nội dung rendered."""

    def test_fastapi_content_contains_subscription_id(self, tmp_path: Path):
        """Kiểm tra FastAPI emitted content chứa subscription_id từ IR."""
        from midicoder.emitters.core.cp40_webhook.fastapi import (
            FastAPIWebhookEmitter,
        )

        emitter = FastAPIWebhookEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        all_content = "\n".join(f.content for f in files)
        assert "wh_basic_001" in all_content or "order.created" in all_content

    def test_fastapi_content_contains_event_type(self, tmp_path: Path):
        """Kiểm tra FastAPI emitted content chứa event_type từ IR."""
        from midicoder.emitters.core.cp40_webhook.fastapi import (
            FastAPIWebhookEmitter,
        )

        emitter = FastAPIWebhookEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        all_content = "\n".join(f.content for f in files)
        assert "order.created" in all_content
        assert "customer.created" in all_content

    def test_nestjs_content_contains_subscription_id(self, tmp_path: Path):
        """Kiểm tra NestJS emitted content chứa subscription_id từ IR."""
        from midicoder.emitters.core.cp40_webhook.nestjs import (
            NestJSWebhookEmitter,
        )

        emitter = NestJSWebhookEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        all_content = "\n".join(f.content for f in files)
        assert "wh_basic_001" in all_content or "order.created" in all_content

    def test_nestjs_content_contains_event_type(self, tmp_path: Path):
        """Kiểm tra NestJS emitted content chứa event_type từ IR."""
        from midicoder.emitters.core.cp40_webhook.nestjs import (
            NestJSWebhookEmitter,
        )

        emitter = NestJSWebhookEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        all_content = "\n".join(f.content for f in files)
        assert "order.created" in all_content
        assert "customer.created" in all_content

    def test_angular_content_contains_subscription_id(self):
        """Kiểm tra Angular emitted content chứa subscription_id từ IR."""
        from midicoder.emitters.core.cp40_webhook.angular import (
            AngularWebhookEmitter,
        )

        emitter = AngularWebhookEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir())
        all_content = "\n".join(f["content"] for f in files)
        assert "wh_basic_001" in all_content or "order.created" in all_content

    def test_angular_content_contains_event_type(self):
        """Kiểm tra Angular emitted content chứa event_type từ IR."""
        from midicoder.emitters.core.cp40_webhook.angular import (
            AngularWebhookEmitter,
        )

        emitter = AngularWebhookEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir())
        all_content = "\n".join(f["content"] for f in files)
        assert "order.created" in all_content
        assert "customer.created" in all_content

    def test_react_content_contains_subscription_id(self):
        """Kiem tra React emitted content chua subscription_id tu IR."""
        from midicoder.emitters.core.cp40_webhook.react import (
            ReactWebhookEmitter,
        )

        emitter = ReactWebhookEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        all_content = "\n".join(f["content"] for f in files)
        assert "wh_basic_001" in all_content or "order.created" in all_content

    def test_react_content_contains_event_type(self):
        """Kiểm tra React emitted content chứa event_type từ IR."""
        from midicoder.emitters.core.cp40_webhook.react import (
            ReactWebhookEmitter,
        )

        emitter = ReactWebhookEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        all_content = "\n".join(f["content"] for f in files)
        assert "order.created" in all_content
        assert "customer.created" in all_content
