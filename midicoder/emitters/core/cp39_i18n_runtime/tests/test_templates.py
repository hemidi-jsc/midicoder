# coding: utf-8
"""
Tests cho CP39 templates: pack.yml existence, file_contributions,
template files cho 4 stacks.
"""

from __future__ import annotations

import pytest
from pathlib import Path

# Midicoder root = 5 parents up from tests/
MIDICODER_ROOT = Path(__file__).parent.parent.parent.parent.parent

FASTAPI_DIR = MIDICODER_ROOT / "stacks" / "fastapi" / "core" / "cp39_i18n_runtime"
NESTJS_DIR = MIDICODER_ROOT / "stacks" / "nestjs" / "core" / "cp39_i18n_runtime"
ANGULAR_DIR = MIDICODER_ROOT / "stacks" / "angular" / "core" / "cp39_i18n_runtime"
REACT_DIR = MIDICODER_ROOT / "stacks" / "react" / "core" / "cp39_i18n_runtime"

PACK_DIR = MIDICODER_ROOT / "emitters" / "core" / "cp39_i18n_runtime"


# ============================================================================
# Test pack.yml
# ============================================================================


class TestPackYaml:
    """Tests cho pack.yml."""

    def test_pack_yml_exists(self):
        pack_yml = PACK_DIR / "pack.yml"
        assert pack_yml.exists(), f"pack.yml không tồn tại tại {pack_yml}"

    def test_pack_yml_has_content(self):
        pack_yml = PACK_DIR / "pack.yml"
        content = pack_yml.read_text(encoding="utf-8")
        assert "CP39" in content
        assert "cp39_i18n_runtime" in content
        assert "file_contributions" in content

    def test_pack_yml_has_capabilities(self):
        import yaml
        pack_yml = PACK_DIR / "pack.yml"
        with open(pack_yml, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "capabilities_provided" in data["pack"]
        assert "locale_format" in data["pack"]["capabilities_provided"]
        assert "translation_manage" in data["pack"]["capabilities_provided"]
        assert "language_switch" in data["pack"]["capabilities_provided"]

    def test_pack_yml_has_file_contributions(self):
        import yaml
        pack_yml = PACK_DIR / "pack.yml"
        with open(pack_yml, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "file_contributions" in data["pack"]
        assert "infrastructure" in data["pack"]["file_contributions"]

    def test_pack_yml_has_4_stacks(self):
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

    def test_pack_yml_has_frontend_integration(self):
        import yaml
        pack_yml = PACK_DIR / "pack.yml"
        with open(pack_yml, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "frontend_integration" in data["pack"]
        assert "angular" in data["pack"]["frontend_integration"]
        assert "react" in data["pack"]["frontend_integration"]


# ============================================================================
# Test FastAPI Templates
# ============================================================================


class TestFastAPITemplates:
    """Tests cho FastAPI templates."""

    EXPECTED = [
        "i18n_models.py.jinja2",
        "i18n_schemas.py.jinja2",
        "i18n_service.py.jinja2",
        "i18n_formatter.py.jinja2",
        "i18n_router.py.jinja2",
        "i18n_cache.py.jinja2",
        "i18n_discover.py.jinja2",
        "i18n_ws.py.jinja2",
        "i18n_middleware.py.jinja2",
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
# Test NestJS Templates
# ============================================================================


class TestNestJSTemplates:
    """Tests cho NestJS templates."""

    EXPECTED = [
        "translation.entity.ts.jinja2",
        "locale.entity.ts.jinja2",
        "translation.dto.ts.jinja2",
        "translation.service.ts.jinja2",
        "translation.controller.ts.jinja2",
        "locale-formatter.service.ts.jinja2",
        "i18n-cache.service.ts.jinja2",
        "i18n.gateway.ts.jinja2",
        "i18n.interceptor.ts.jinja2",
        "i18n.module.ts.jinja2",
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
        for name in self.EXPECTED:
            path = NESTJS_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "from midicoder" not in content

    def test_no_post_init(self):
        for name in self.EXPECTED:
            path = NESTJS_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "__post_init__" not in content


# ============================================================================
# Test Angular Templates
# ============================================================================


class TestAngularTemplates:
    """Tests cho Angular templates."""

    EXPECTED = [
        "i18n-runtime.service.ts.jinja2",
        "locale-directive.ts.jinja2",
        "translation-sync.service.ts.jinja2",
        "locale-formatter.pipe.ts.jinja2",
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
        for name in self.EXPECTED:
            path = ANGULAR_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "from midicoder" not in content

    def test_no_post_init(self):
        for name in self.EXPECTED:
            path = ANGULAR_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "__post_init__" not in content


# ============================================================================
# Test React Templates
# ============================================================================


class TestReactTemplates:
    """Tests cho React templates."""

    EXPECTED = [
        "useTranslation.ts.jinja2",
        "useLocale.ts.jinja2",
        "useFormattedValue.ts.jinja2",
        "TranslationSyncWorker.ts.jinja2",
        "I18nRuntimeProvider.tsx.jinja2",
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
        for name in self.EXPECTED:
            path = REACT_DIR / name
            content = path.read_text(encoding="utf-8")
            assert "from midicoder" not in content

    def test_no_post_init(self):
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

    def test_cp39_in_registry(self):
        from midicoder.contracts.registry import CP_ID_TO_INTERNAL
        assert "CP39" in CP_ID_TO_INTERNAL
        assert CP_ID_TO_INTERNAL["CP39"] == "cp39_i18n_runtime"
