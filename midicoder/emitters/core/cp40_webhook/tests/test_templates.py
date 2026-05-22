# coding: utf-8
"""
Tests cho CP40 templates: pack.yml existence, file_contributions,
template files cho 4 stacks (FastAPI, NestJS, Angular, React),
CHANGELOG.md, và Registry integration.
"""

from __future__ import annotations

import pytest
from pathlib import Path

# Midicoder root = 5 parents up from tests/
MIDICODER_ROOT = Path(__file__).parent.parent.parent.parent.parent

FASTAPI_DIR = MIDICODER_ROOT / "stacks" / "fastapi" / "core" / "cp40_webhook"
NESTJS_DIR = MIDICODER_ROOT / "stacks" / "nestjs" / "core" / "cp40_webhook"
ANGULAR_DIR = MIDICODER_ROOT / "stacks" / "angular" / "core" / "cp40_webhook"
REACT_DIR = MIDICODER_ROOT / "stacks" / "react" / "core" / "cp40_webhook"
PACK_DIR = MIDICODER_ROOT / "emitters" / "core" / "cp40_webhook"


# ============================================================================
# Test pack.yml
# ============================================================================


class TestPackYaml:
    """Tests cho pack.yml."""

    def test_pack_yml_exists(self):
        pack_yml = PACK_DIR / "pack.yml"
        assert pack_yml.exists(), f"pack.yml không tồn tại tại {pack_yml}"

    def test_pack_yml_has_cp40_id(self):
        pack_yml = PACK_DIR / "pack.yml"
        content = pack_yml.read_text(encoding="utf-8")
        assert "CP40" in content
        assert "cp40_webhook" in content

    def test_pack_yml_has_capabilities(self):
        import yaml
        pack_yml = PACK_DIR / "pack.yml"
        with open(pack_yml, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "capabilities_provided" in data["pack"]
        assert "webhook_manage" in data["pack"]["capabilities_provided"]
        assert "event_deliver" in data["pack"]["capabilities_provided"]
        assert "retry_policy" in data["pack"]["capabilities_provided"]
        assert "outbound_api" in data["pack"]["capabilities_provided"]

    def test_pack_yml_has_4_stacks(self):
        """Kiểm tra pack.yml có declarations cho 4 stacks."""
        import yaml
        pack_yml = PACK_DIR / "pack.yml"
        with open(pack_yml, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        stacks_found = set()
        for contrib in data["pack"]["file_contributions"]["infrastructure"]:
            for s in contrib.get("stacks", []):
                stacks_found.add(s)
        assert "fastapi" in stacks_found
        assert "nestjs" in stacks_found
        assert "angular" in stacks_found
        assert "react" in stacks_found

    def test_pack_yml_has_file_contributions(self):
        import yaml
        pack_yml = PACK_DIR / "pack.yml"
        with open(pack_yml, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "file_contributions" in data["pack"]
        assert "infrastructure" in data["pack"]["file_contributions"]


# ============================================================================
# Test FastAPI Templates (7 files)
# ============================================================================


class TestFastAPITemplates:
    """Tests cho FastAPI templates."""

    EXPECTED = [
        "webhook_models.py.jinja2",
        "webhook_schemas.py.jinja2",
        "webhook_service.py.jinja2",
        "webhook_router.py.jinja2",
        "webhook_dispatch.py.jinja2",
        "webhook_worker.py.jinja2",
        "webhook_middleware.py.jinja2",
    ]

    def test_all_templates_exist(self):
        for name in self.EXPECTED:
            path = FASTAPI_DIR / name
            assert path.exists(), f"Template không tồn tại: {path}"

    def test_templates_have_content(self):
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
    """Tests cho NestJS templates."""

    EXPECTED = [
        "webhook.entity.ts.jinja2",
        "webhook.dto.ts.jinja2",
        "webhook.service.ts.jinja2",
        "webhook.controller.ts.jinja2",
        "webhook-dispatcher.service.ts.jinja2",
        "webhook-queue.service.ts.jinja2",
        "webhook.module.ts.jinja2",
    ]

    def test_all_templates_exist(self):
        for name in self.EXPECTED:
            path = NESTJS_DIR / name
            assert path.exists(), f"Template không tồn tại: {path}"

    def test_templates_have_content(self):
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
# Test Angular Templates (4 files)
# ============================================================================


class TestAngularTemplates:
    """Tests cho Angular templates."""

    EXPECTED = [
        "webhook-dashboard.component.ts.jinja2",
        "webhook-subscription-list.component.ts.jinja2",
        "webhook-delivery-viewer.component.ts.jinja2",
        "webhook.service.ts.jinja2",
    ]

    def test_all_templates_exist(self):
        for name in self.EXPECTED:
            path = ANGULAR_DIR / name
            assert path.exists(), f"Template không tồn tại: {path}"

    def test_templates_have_content(self):
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
# Test React Templates (4 files)
# ============================================================================


class TestReactTemplates:
    """Tests cho React templates."""

    EXPECTED = [
        "WebhookDashboard.tsx.jinja2",
        "WebhookSubscriptionList.tsx.jinja2",
        "useWebhooks.ts.jinja2",
        "useDispatchStatus.ts.jinja2",
    ]

    def test_all_templates_exist(self):
        for name in self.EXPECTED:
            path = REACT_DIR / name
            assert path.exists(), f"Template không tồn tại: {path}"

    def test_templates_have_content(self):
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
    """Tests cho CHANGELOG.md."""

    def test_changelog_exists(self):
        changelog = PACK_DIR / "CHANGELOG.md"
        assert changelog.exists()

    def test_changelog_has_version(self):
        changelog = PACK_DIR / "CHANGELOG.md"
        content = changelog.read_text(encoding="utf-8")
        assert "1.0.0" in content


# ============================================================================
# Test Registry
# ============================================================================


class TestRegistry:
    """Tests cho registry integration."""

    def test_cp40_in_registry(self):
        from midicoder.contracts.registry import CP_ID_TO_INTERNAL
        assert "CP40" in CP_ID_TO_INTERNAL
        assert CP_ID_TO_INTERNAL["CP40"] == "cp40_webhook"
