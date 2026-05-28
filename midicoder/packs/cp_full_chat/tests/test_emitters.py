# coding: utf-8
"""
Tests cho CP41 Chat & Messaging emitters: FastAPI, NestJS, Angular, React.

Bao gồm:
- __init__ raises MidicoderError khi template dir không tìm thấy
- emit() returns correct number of files
- emit() returns correct paths
- emit() files have non-empty content
- _build_context() returns correct keys và giá trị
- _template_exists() returns True/False
- emit context chứa conversation, messages trong rendered content
- Angular/React _TEMPLATE_MAP có đúng số lượng entries
"""

from __future__ import annotations

import pytest
from pathlib import Path

from midicoder.errors import MidicoderError

# Midicoder root = 5 parents up from tests/
# stack_dir = .../stacks/{stack}/core  (emitter tự thêm /cp_full_chat)
MIDICODER_ROOT = Path(__file__).parent.parent.parent.parent.parent

FASTAPI_STACK_DIR = MIDICODER_ROOT / "stacks" / "fastapi" / "core"
NESTJS_STACK_DIR = MIDICODER_ROOT / "stacks" / "nestjs" / "core"
ANGULAR_STACK_DIR = MIDICODER_ROOT / "stacks" / "angular" / "core"
REACT_STACK_DIR = MIDICODER_ROOT / "stacks" / "react" / "core"


def _make_ir():
    """Tạo ChatIR sample cho testing từ basic_chat_recipe."""
    from midicoder.packs.cp_full_chat.recipes import basic_chat_recipe
    recipe = basic_chat_recipe()
    return recipe.ir


# ============================================================================
# Test FastAPIChatEmitter
# ============================================================================


class TestFastAPIChatEmitter:
    """Tests cho FastAPIChatEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        """Kiểm tra __init__ raise MidicoderError khi template dir không tìm thấy."""
        from midicoder.packs.cp_full_chat.fastapi import FastAPIChatEmitter

        with pytest.raises(MidicoderError):
            FastAPIChatEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        """Kiểm tra __init__ thành công với template dir có thật."""
        from midicoder.packs.cp_full_chat.fastapi import FastAPIChatEmitter

        emitter = FastAPIChatEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter is not None

    def test_init_sets_template_dir_correctly(self):
        """Kiểm tra template_dir được đặt đúng."""
        from midicoder.packs.cp_full_chat.fastapi import FastAPIChatEmitter

        emitter = FastAPIChatEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter.template_dir == FASTAPI_STACK_DIR / "cp_full_chat"

    def test_emit_returns_minimum_files(self, tmp_path: Path):
        """Kiểm tra emit trả về ít nhất 7 files."""
        from midicoder.packs.cp_full_chat.fastapi import FastAPIChatEmitter

        emitter = FastAPIChatEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        assert len(files) >= 7

    def test_emit_returns_correct_paths(self, tmp_path: Path):
        """Kiểm tra emit trả về các đường dẫn đúng."""
        from midicoder.packs.cp_full_chat.fastapi import FastAPIChatEmitter

        emitter = FastAPIChatEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        paths = [f.path for f in files]
        assert "app/models/chat_models.py" in paths
        assert "app/services/chat_service.py" in paths
        assert "app/api/chat_router.py" in paths
        assert "app/websockets/chat_websocket.py" in paths

    def test_emit_files_have_nonempty_content(self, tmp_path: Path):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.packs.cp_full_chat.fastapi import FastAPIChatEmitter

        emitter = FastAPIChatEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert len(f.content) > 0, f"File {f.path} có nội dung rỗng"

    def test_build_context_returns_correct_keys(self):
        """Kiểm tra _build_context trả về các key đúng."""
        from midicoder.packs.cp_full_chat.fastapi import FastAPIChatEmitter

        emitter = FastAPIChatEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert "conversations" in ctx
        assert "messages" in ctx
        assert "notifications" in ctx
        assert "conversation_count" in ctx
        assert "message_count" in ctx
        assert "notification_count" in ctx
        assert "redis_url" in ctx
        assert "use_redis" in ctx
        assert "use_websocket" in ctx

    def test_build_context_conversation_count(self):
        """Kiểm tra conversation_count đúng với IR (basic_chat_recipe = 2)."""
        from midicoder.packs.cp_full_chat.fastapi import FastAPIChatEmitter

        emitter = FastAPIChatEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert ctx["conversation_count"] == 2

    def test_build_context_message_count(self):
        """Kiểm tra message_count đúng với IR (basic_chat_recipe = 3)."""
        from midicoder.packs.cp_full_chat.fastapi import FastAPIChatEmitter

        emitter = FastAPIChatEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert ctx["message_count"] == 3

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.packs.cp_full_chat.fastapi import FastAPIChatEmitter

        emitter = FastAPIChatEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter._template_exists("chat_models.py.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.packs.cp_full_chat.fastapi import FastAPIChatEmitter

        emitter = FastAPIChatEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter._template_exists("nonexistent.py.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.packs.cp_full_chat.fastapi import FastAPIChatEmitter

        emitter = FastAPIChatEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.py.jinja2", {})

    def test_emit_with_redis_context(self, tmp_path: Path):
        """Kiểm tra emit hoạt động với Redis context từ full_messaging_recipe."""
        from midicoder.packs.cp_full_chat.fastapi import FastAPIChatEmitter
        from midicoder.packs.cp_full_chat.recipes import full_messaging_recipe

        emitter = FastAPIChatEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        recipe = full_messaging_recipe()
        files = emitter.emit(recipe.ir, tmp_path)
        assert len(files) > 0
        all_content = "\n".join(f.content for f in files)
        assert "redis" in all_content.lower() or "6379" in all_content


# ============================================================================
# Test NestJSChatEmitter
# ============================================================================


class TestNestJSChatEmitter:
    """Tests cho NestJSChatEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        """Kiểm tra __init__ raise MidicoderError khi template dir không tìm thấy."""
        from midicoder.packs.cp_full_chat.nestjs import NestJSChatEmitter

        with pytest.raises(MidicoderError):
            NestJSChatEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        """Kiểm tra __init__ thành công với template dir có thật."""
        from midicoder.packs.cp_full_chat.nestjs import NestJSChatEmitter

        emitter = NestJSChatEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter is not None

    def test_init_sets_template_dir_correctly(self):
        """Kiểm tra template_dir được đặt đúng."""
        from midicoder.packs.cp_full_chat.nestjs import NestJSChatEmitter

        emitter = NestJSChatEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter.template_dir == NESTJS_STACK_DIR / "cp_full_chat"

    def test_emit_returns_minimum_files(self, tmp_path: Path):
        """Kiểm tra emit trả về ít nhất 7 files."""
        from midicoder.packs.cp_full_chat.nestjs import NestJSChatEmitter

        emitter = NestJSChatEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        assert len(files) >= 7

    def test_emit_returns_correct_paths(self, tmp_path: Path):
        """Kiểm tra emit trả về các đường dẫn đúng cho NestJS."""
        from midicoder.packs.cp_full_chat.nestjs import NestJSChatEmitter

        emitter = NestJSChatEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        paths = [f.path for f in files]
        assert "src/chat/chat.entity.ts" in paths
        assert "src/chat/chat.service.ts" in paths
        assert "src/chat/chat.controller.ts" in paths
        assert "src/chat/chat.gateway.ts" in paths

    def test_emit_files_have_nonempty_content(self, tmp_path: Path):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.packs.cp_full_chat.nestjs import NestJSChatEmitter

        emitter = NestJSChatEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert len(f.content) > 0, f"File {f.path} có nội dung rỗng"

    def test_build_context_returns_correct_keys(self):
        """Kiểm tra _build_context trả về các key đúng."""
        from midicoder.packs.cp_full_chat.nestjs import NestJSChatEmitter

        emitter = NestJSChatEmitter(stack_dir=str(NESTJS_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert "conversations" in ctx
        assert "messages" in ctx
        assert "notifications" in ctx
        assert "conversation_count" in ctx
        assert "message_count" in ctx
        assert "notification_count" in ctx
        assert "redis_url" in ctx
        assert "use_redis" in ctx
        assert "use_websocket" in ctx

    def test_build_context_conversation_count(self):
        """Kiểm tra conversation_count đúng với IR (basic_chat_recipe = 2)."""
        from midicoder.packs.cp_full_chat.nestjs import NestJSChatEmitter

        emitter = NestJSChatEmitter(stack_dir=str(NESTJS_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert ctx["conversation_count"] == 2

    def test_build_context_message_count(self):
        """Kiểm tra message_count đúng với IR (basic_chat_recipe = 3)."""
        from midicoder.packs.cp_full_chat.nestjs import NestJSChatEmitter

        emitter = NestJSChatEmitter(stack_dir=str(NESTJS_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert ctx["message_count"] == 3

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.packs.cp_full_chat.nestjs import NestJSChatEmitter

        emitter = NestJSChatEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter._template_exists("chat.entity.ts.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.packs.cp_full_chat.nestjs import NestJSChatEmitter

        emitter = NestJSChatEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter._template_exists("nonexistent.ts.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.packs.cp_full_chat.nestjs import NestJSChatEmitter

        emitter = NestJSChatEmitter(stack_dir=str(NESTJS_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.ts.jinja2", {})


# ============================================================================
# Test AngularChatEmitter
# ============================================================================


class TestAngularChatEmitter:
    """Tests cho AngularChatEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        """Kiểm tra __init__ raise MidicoderError khi template dir không tìm thấy."""
        from midicoder.packs.cp_full_chat.angular import AngularChatEmitter

        with pytest.raises(MidicoderError):
            AngularChatEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        """Kiểm tra __init__ thành công với template dir có thật."""
        from midicoder.packs.cp_full_chat.angular import AngularChatEmitter

        emitter = AngularChatEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter is not None

    def test_emit_returns_minimum_files(self, tmp_path: Path):
        """Kiểm tra emit trả về ít nhất 6 files."""
        from midicoder.packs.cp_full_chat.angular import AngularChatEmitter

        emitter = AngularChatEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        assert len(files) >= 6

    def test_emit_returns_correct_paths(self, tmp_path: Path):
        """Kiểm tra emit trả về các đường dẫn đúng cho Angular."""
        from midicoder.packs.cp_full_chat.angular import AngularChatEmitter

        emitter = AngularChatEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        paths = [f.path for f in files]
        assert "src/chat/chat-window.component.ts" in paths
        assert "src/chat/chat.service.ts" in paths
        assert "src/chat/chat.store.ts" in paths

    def test_emit_files_have_nonempty_content(self, tmp_path: Path):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.packs.cp_full_chat.angular import AngularChatEmitter

        emitter = AngularChatEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert len(f.content) > 0, f"File {f.path} có nội dung rỗng"

    def test_emit_with_extra_context(self, tmp_path: Path):
        """Kiểm tra emit hoạt động với context bổ sung."""
        from midicoder.packs.cp_full_chat.angular import AngularChatEmitter

        emitter = AngularChatEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        assert len(files) > 0

    def test_template_map_has_6_entries(self):
        """Kiểm tra _TEMPLATE_MAP có đúng 6 entries."""
        from midicoder.packs.cp_full_chat.angular import AngularChatEmitter

        assert len(AngularChatEmitter._TEMPLATE_MAP) == 6

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.packs.cp_full_chat.angular import AngularChatEmitter

        emitter = AngularChatEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter._template_exists("chat-window.component.ts.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.packs.cp_full_chat.angular import AngularChatEmitter

        emitter = AngularChatEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter._template_exists("nonexistent.ts.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.packs.cp_full_chat.angular import AngularChatEmitter

        emitter = AngularChatEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.ts.jinja2", {})


# ============================================================================
# Test ReactChatEmitter
# ============================================================================


class TestReactChatEmitter:
    """Tests cho ReactChatEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        """Kiểm tra __init__ raise MidicoderError khi template dir không tìm thấy."""
        from midicoder.packs.cp_full_chat.react import ReactChatEmitter

        with pytest.raises(MidicoderError):
            ReactChatEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        """Kiểm tra __init__ thành công với template dir có thật."""
        from midicoder.packs.cp_full_chat.react import ReactChatEmitter

        emitter = ReactChatEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter is not None

    def test_emit_returns_minimum_files(self):
        """Kiểm tra emit trả về ít nhất 6 files."""
        from midicoder.packs.cp_full_chat.react import ReactChatEmitter

        emitter = ReactChatEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        assert len(files) >= 6

    def test_emit_returns_correct_paths(self):
        """Kiểm tra emit trả về các đường dẫn đúng cho React."""
        from midicoder.packs.cp_full_chat.react import ReactChatEmitter

        emitter = ReactChatEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        paths = [f["path"] for f in files]
        assert "src/chat/ChatWindow.tsx" in paths
        assert "src/chat/ConversationList.tsx" in paths
        assert "src/chat/NotificationBell.tsx" in paths
        assert "src/chat/hooks/useChat.ts" in paths

    def test_emit_files_have_nonempty_content(self):
        """Kiểm tra nội dung file không rỗng."""
        from midicoder.packs.cp_full_chat.react import ReactChatEmitter

        emitter = ReactChatEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        for f in files:
            assert len(f["content"]) > 0, f"File {f['path']} có nội dung rỗng"

    def test_emit_with_extra_context(self):
        """Kiểm tra emit hoạt động với context bổ sung."""
        from midicoder.packs.cp_full_chat.react import ReactChatEmitter

        emitter = ReactChatEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir(), context={"ui_framework": "react"})
        assert len(files) > 0

    def test_template_map_has_6_entries(self):
        """Kiểm tra _TEMPLATE_MAP có đúng 6 entries."""
        from midicoder.packs.cp_full_chat.react import ReactChatEmitter

        assert len(ReactChatEmitter._TEMPLATE_MAP) == 6

    def test_template_exists_true(self):
        """Kiểm tra _template_exists trả về True với template có thật."""
        from midicoder.packs.cp_full_chat.react import ReactChatEmitter

        emitter = ReactChatEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter._template_exists("ChatWindow.tsx.jinja2") is True

    def test_template_exists_false(self):
        """Kiểm tra _template_exists trả về False với template không tồn tại."""
        from midicoder.packs.cp_full_chat.react import ReactChatEmitter

        emitter = ReactChatEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter._template_exists("nonexistent.tsx.jinja2") is False

    def test_render_raises_on_missing_template(self):
        """Kiểm tra _render raise MidicoderError khi template không tồn tại."""
        from midicoder.packs.cp_full_chat.react import ReactChatEmitter

        emitter = ReactChatEmitter(stack_dir=str(REACT_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.tsx.jinja2", {})


# ============================================================================
# Test Emit Context — Conversations và Messages trong rendered content
# ============================================================================


class TestEmitContext:
    """Tests cho việc conversations và messages có trong nội dung rendered."""

    def test_fastapi_content_contains_conversation(self, tmp_path: Path):
        """Kiểm tra FastAPI emitted content chứa conversation từ IR."""
        from midicoder.packs.cp_full_chat.fastapi import FastAPIChatEmitter

        emitter = FastAPIChatEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        all_content = "\n".join(f.content for f in files)
        assert "Conversation" in all_content or "conversations" in all_content

    def test_nestjs_content_contains_conversation(self, tmp_path: Path):
        """Kiểm tra NestJS emitted content chứa conversation từ IR."""
        from midicoder.packs.cp_full_chat.nestjs import NestJSChatEmitter

        emitter = NestJSChatEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        all_content = "\n".join(f.content for f in files)
        assert "Conversation" in all_content or "conversation" in all_content

    def test_angular_content_contains_conversation(self, tmp_path: Path):
        """Kiểm tra Angular emitted content chứa conversation từ IR."""
        from midicoder.packs.cp_full_chat.angular import AngularChatEmitter

        emitter = AngularChatEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        all_content = "\n".join(f.content for f in files)
        assert "Conversation" in all_content or "conversation" in all_content

    def test_react_content_contains_conversation(self):
        """Kiểm tra React emitted content chứa conversation từ IR."""
        from midicoder.packs.cp_full_chat.react import ReactChatEmitter

        emitter = ReactChatEmitter(stack_dir=str(REACT_STACK_DIR))
        files = emitter.emit(_make_ir())
        all_content = "\n".join(f["content"] for f in files)
        assert "Conversation" in all_content or "conversation" in all_content
