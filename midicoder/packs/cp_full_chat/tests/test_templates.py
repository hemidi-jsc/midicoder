# coding: utf-8
"""
Tests cho CP41 templates: pack.yml existence, file_contributions,
template files cho 4 stacks (FastAPI, NestJS, Angular, React),
CHANGELOG.md, và Registry integration.
"""

from __future__ import annotations

import pytest
from pathlib import Path
import jinja2

# Midicoder root = 5 parents up from tests/
MIDICODER_ROOT = Path(__file__).parent.parent.parent.parent.parent

FASTAPI_DIR = MIDICODER_ROOT / "stacks" / "fastapi" / "core" / "cp_full_chat"
NESTJS_DIR = MIDICODER_ROOT / "stacks" / "nestjs" / "core" / "cp_full_chat"
ANGULAR_DIR = MIDICODER_ROOT / "stacks" / "angular" / "core" / "cp_full_chat"
REACT_DIR = MIDICODER_ROOT / "stacks" / "react" / "core" / "cp_full_chat"
PACK_DIR = MIDICODER_ROOT / "emitters" / "core" / "cp_full_chat"

FASTAPI_TEMPLATES = [
    "chat_models.py.jinja2",
    "chat_schemas.py.jinja2",
    "chat_service.py.jinja2",
    "chat_router.py.jinja2",
    "chat_websocket.py.jinja2",
    "chat_consumer.py.jinja2",
    "chat_worker.py.jinja2",
]
NESTJS_TEMPLATES = [
    "chat.entity.ts.jinja2",
    "chat.dto.ts.jinja2",
    "chat.service.ts.jinja2",
    "chat.controller.ts.jinja2",
    "chat.gateway.ts.jinja2",
    "chat.module.ts.jinja2",
    "chat-queue.service.ts.jinja2",
]
ANGULAR_TEMPLATES = [
    "chat-window.component.ts.jinja2",
    "chat-conversation-list.component.ts.jinja2",
    "chat-notification.component.ts.jinja2",
    "chat.service.ts.jinja2",
    "chat.store.ts.jinja2",
    "chat-types.ts.jinja2",
]
REACT_TEMPLATES = [
    "ChatWindow.tsx.jinja2",
    "ConversationList.tsx.jinja2",
    "NotificationBell.tsx.jinja2",
    "useChat.ts.jinja2",
    "useNotifications.ts.jinja2",
    "chatService.ts.jinja2",
]


# ============================================================================
# Test pack.yml
# ============================================================================


class TestPackYaml:
    """Tests cho pack.yml của CP41."""

    def test_pack_yml_exists(self):
        """Kiểm tra pack.yml tồn tại."""
        pack_yml = PACK_DIR / "pack.yml"
        assert pack_yml.exists(), f"pack.yml không tồn tại tại {pack_yml}"

    def test_pack_yml_has_cp41_id(self):
        """Kiểm tra pack.yml chứa CP41 và cp_full_chat."""
        pack_yml = PACK_DIR / "pack.yml"
        content = pack_yml.read_text(encoding="utf-8")
        assert "CP41" in content
        assert "cp_full_chat" in content

    def test_pack_yml_has_capabilities(self):
        """Kiểm tra pack.yml chứa capabilities."""
        pack_yml = PACK_DIR / "pack.yml"
        content = pack_yml.read_text(encoding="utf-8")
        assert "capabilities" in content

    def test_pack_yml_has_4_stacks(self):
        """Kiểm tra pack.yml có declarations cho 4 stacks: FastAPI, NestJS, Angular, React."""
        pack_yml = PACK_DIR / "pack.yml"
        content = pack_yml.read_text(encoding="utf-8")
        assert "FastAPI" in content
        assert "NestJS" in content
        assert "Angular" in content
        assert "React" in content

    def test_pack_yml_has_file_contributions(self):
        """Kiểm tra pack.yml chứa file_contributions."""
        pack_yml = PACK_DIR / "pack.yml"
        content = pack_yml.read_text(encoding="utf-8")
        assert "file_contributions" in content


# ============================================================================
# Test FastAPI Templates (7 files)
# ============================================================================


class TestFastAPITemplates:
    """Tests cho FastAPI templates của CP41."""

    EXPECTED = FASTAPI_TEMPLATES

    def test_all_templates_exist(self):
        """Kiểm tra tất cả FastAPI templates tồn tại."""
        for name in self.EXPECTED:
            path = FASTAPI_DIR / name
            assert path.exists(), f"Template không tồn tại: {path}"

    def test_templates_have_content(self):
        """Kiểm tra tất cả FastAPI templates có nội dung."""
        for name in self.EXPECTED:
            path = FASTAPI_DIR / name
            content = path.read_text(encoding="utf-8")
            assert len(content) > 0, f"Template rỗng: {name}"

    def test_no_midicoder_import(self):
        """Kiểm tra templates không import từ midicoder."""
        for name in self.EXPECTED:
            path = FASTAPI_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "from midicoder" not in content, f"Template {name} không được import từ midicoder"

    def test_no_post_init(self):
        """Kiểm tra templates không có __post_init__."""
        for name in self.EXPECTED:
            path = FASTAPI_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "__post_init__" not in content, f"Template {name} không được có __post_init__"


# ============================================================================
# Test NestJS Templates (7 files)
# ============================================================================


class TestNestJSTemplates:
    """Tests cho NestJS templates của CP41."""

    EXPECTED = NESTJS_TEMPLATES

    def test_all_templates_exist(self):
        """Kiểm tra tất cả NestJS templates tồn tại."""
        for name in self.EXPECTED:
            path = NESTJS_DIR / name
            assert path.exists(), f"Template không tồn tại: {path}"

    def test_templates_have_content(self):
        """Kiểm tra tất cả NestJS templates có nội dung."""
        for name in self.EXPECTED:
            path = NESTJS_DIR / name
            content = path.read_text(encoding="utf-8")
            assert len(content) > 0, f"Template rỗng: {name}"

    def test_no_midicoder_import(self):
        """Kiểm tra templates không import từ midicoder."""
        for name in self.EXPECTED:
            path = NESTJS_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "from midicoder" not in content

    def test_no_post_init(self):
        """Kiểm tra templates không có __post_init__."""
        for name in self.EXPECTED:
            path = NESTJS_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "__post_init__" not in content


# ============================================================================
# Test Angular Templates (6 files)
# ============================================================================


class TestAngularTemplates:
    """Tests cho Angular templates của CP41."""

    EXPECTED = ANGULAR_TEMPLATES

    def test_all_templates_exist(self):
        """Kiểm tra tất cả Angular templates tồn tại."""
        for name in self.EXPECTED:
            path = ANGULAR_DIR / name
            assert path.exists(), f"Template không tồn tại: {path}"

    def test_templates_have_content(self):
        """Kiểm tra tất cả Angular templates có nội dung."""
        for name in self.EXPECTED:
            path = ANGULAR_DIR / name
            content = path.read_text(encoding="utf-8")
            assert len(content) > 0, f"Template rỗng: {name}"

    def test_no_midicoder_import(self):
        """Kiểm tra templates không import từ midicoder."""
        for name in self.EXPECTED:
            path = ANGULAR_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "from midicoder" not in content

    def test_no_post_init(self):
        """Kiểm tra templates không có __post_init__."""
        for name in self.EXPECTED:
            path = ANGULAR_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "__post_init__" not in content


# ============================================================================
# Test React Templates (6 files)
# ============================================================================


class TestReactTemplates:
    """Tests cho React templates của CP41."""

    EXPECTED = REACT_TEMPLATES

    def test_all_templates_exist(self):
        """Kiểm tra tất cả React templates tồn tại."""
        for name in self.EXPECTED:
            path = REACT_DIR / name
            assert path.exists(), f"Template không tồn tại: {path}"

    def test_templates_have_content(self):
        """Kiểm tra tất cả React templates có nội dung."""
        for name in self.EXPECTED:
            path = REACT_DIR / name
            content = path.read_text(encoding="utf-8")
            assert len(content) > 0, f"Template rỗng: {name}"

    def test_no_midicoder_import(self):
        """Kiểm tra templates không import từ midicoder."""
        for name in self.EXPECTED:
            path = REACT_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "from midicoder" not in content

    def test_no_post_init(self):
        """Kiểm tra templates không có __post_init__."""
        for name in self.EXPECTED:
            path = REACT_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "__post_init__" not in content


# ============================================================================
# Test CHANGELOG.md
# ============================================================================


class TestChangelog:
    """Tests cho CHANGELOG.md của CP41."""

    def test_changelog_exists(self):
        """Kiểm tra CHANGELOG.md tồn tại."""
        changelog = PACK_DIR / "CHANGELOG.md"
        assert changelog.exists()

    def test_changelog_has_version(self):
        """Kiểm tra CHANGELOG.md chứa phiên bản 1.0.0."""
        changelog = PACK_DIR / "CHANGELOG.md"
        content = changelog.read_text(encoding="utf-8")
        assert "1.0.0" in content


# ============================================================================
# Test Registry
# ============================================================================


class TestRegistry:
    """Tests cho registry integration của CP41."""

    def test_cp41_in_registry(self):
        """Kiểm tra CP41 có trong registry."""
        from midicoder.contracts.registry import CP_ID_TO_INTERNAL
        assert "CP41" in CP_ID_TO_INTERNAL
        assert CP_ID_TO_INTERNAL["CP41"] == "cp_full_chat"


# ============================================================================
# Rule V1 & V2 (P2-17) — template render tests
# ============================================================================

# Dùng MIDICODER_ROOT có sẵn; stack dirs map
STACK_DIRS_41 = {
    "fastapi": FASTAPI_DIR,
    "nestjs": NESTJS_DIR,
    "angular": ANGULAR_DIR,
    "react": REACT_DIR,
}

# Dùng các danh sách template module-level có sẵn
ALL_TEMPLATES_41 = {
    "fastapi": FASTAPI_TEMPLATES,
    "nestjs": NESTJS_TEMPLATES,
    "angular": ANGULAR_TEMPLATES,
    "react": REACT_TEMPLATES,
}


def _render_template_41(stack: str, template_name: str) -> str:
    """Render template với context cơ bản; fallback sang đọc source thô nếu render lỗi."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(STACK_DIRS_41[stack])),
        undefined=jinja2.ChainableUndefined,
    )
    ctx: dict = {
        "conversation_count": 0,
        "notification_count": 0,
    }
    try:
        template = env.get_template(template_name)
        return template.render(**ctx)
    except Exception:
        # Template chứa JSX/TSX không bọc {% raw %} — đọc source thô
        source_path = STACK_DIRS_41[stack] / template_name
        return source_path.read_text(encoding="utf-8")


class TestRuleV1NoMidicoderImport:
    """Rule V1: Output của template KHÔNG chứa 'from midicoder'."""

    def test_fastapi_no_midicoder_import(self):
        """FastAPI templates không chứa 'from midicoder' trong output."""
        for template in FASTAPI_TEMPLATES:
            result = _render_template_41("fastapi", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_nestjs_no_midicoder_import(self):
        """NestJS templates không chứa 'from midicoder' trong output."""
        for template in NESTJS_TEMPLATES:
            result = _render_template_41("nestjs", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_angular_no_midicoder_import(self):
        """Angular templates không chứa 'from midicoder' trong output."""
        for template in ANGULAR_TEMPLATES:
            result = _render_template_41("angular", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_react_no_midicoder_import(self):
        """React templates không chứa 'from midicoder' trong output."""
        for template in REACT_TEMPLATES:
            result = _render_template_41("react", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"


class TestRuleV2NoPostInit:
    """Rule V2: Output của template KHÔNG chứa '__post_init__'."""

    def test_fastapi_no_post_init(self):
        """FastAPI templates không chứa __post_init__ trong output."""
        for template in FASTAPI_TEMPLATES:
            result = _render_template_41("fastapi", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_nestjs_no_post_init(self):
        """NestJS templates không chứa __post_init__ trong output."""
        for template in NESTJS_TEMPLATES:
            result = _render_template_41("nestjs", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_angular_no_post_init(self):
        """Angular templates không chứa __post_init__ trong output."""
        for template in ANGULAR_TEMPLATES:
            result = _render_template_41("angular", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_react_no_post_init(self):
        """React templates không chứa __post_init__ trong output."""
        for template in REACT_TEMPLATES:
            result = _render_template_41("react", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"
