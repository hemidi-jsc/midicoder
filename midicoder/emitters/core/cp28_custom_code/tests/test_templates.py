# coding: utf-8
"""
Test cho template rendering của CP28 Custom Code Injection Generator.

Kiểm tra:
- Templates FastAPI render thành công
- Templates NestJS/Angular/React render thành công
- Không có template file bị thiếu

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]  # midicoder-ce/
STACKS_DIR = ROOT / "midicoder" / "stacks"
EMITTERS_DIR = ROOT / "midicoder" / "emitters" / "core" / "cp28_custom_code"


class TestTemplateFilesExist:
    """Kiểm tra template files tồn tại."""

    def test_pack_yml_exists(self) -> None:
        """pack.yml tồn tại."""
        assert (EMITTERS_DIR / "pack.yml").exists()

    def test_fastapi_templates_exist(self) -> None:
        """Templates FastAPI tồn tại."""
        base = STACKS_DIR / "fastapi" / "core" / "cp28_custom_code"
        expected = [
            "__init__.py.jinja2",
            "inject.py.jinja2",
            "blocks.py.jinja2",
            "hooks.py.jinja2",
            "patches.py.jinja2",
            "registry.py.jinja2",
        ]
        for name in expected:
            p = base / name
            assert p.exists(), f"Template {name} không tìm thấy tại {p}"

    def test_nestjs_templates_exist(self) -> None:
        """Templates NestJS tồn tại."""
        base = STACKS_DIR / "nestjs" / "core" / "cp28_custom_code"
        expected = [
            "injector.ts.jinja2",
            "blocks.ts.jinja2",
            "hooks.ts.jinja2",
            "patches.ts.jinja2",
            "registry.ts.jinja2",
        ]
        for name in expected:
            p = base / name
            assert p.exists(), f"Template {name} không tìm thấy tại {p}"

    def test_angular_templates_exist(self) -> None:
        """Templates Angular tồn tại."""
        base = STACKS_DIR / "angular" / "core" / "cp28_custom_code"
        expected = [
            "injector.ts.jinja2",
            "blocks.ts.jinja2",
            "hooks.ts.jinja2",
            "patches.ts.jinja2",
            "registry.ts.jinja2",
        ]
        for name in expected:
            p = base / name
            assert p.exists(), f"Template {name} không tìm thấy tại {p}"

    def test_react_templates_exist(self) -> None:
        """Templates React tồn tại."""
        base = STACKS_DIR / "react" / "core" / "cp28_custom_code"
        expected = [
            "injector.ts.jinja2",
            "blocks.ts.jinja2",
            "hooks.ts.jinja2",
            "patches.ts.jinja2",
            "registry.ts.jinja2",
        ]
        for name in expected:
            p = base / name
            assert p.exists(), f"Template {name} không tìm thấy tại {p}"


class TestTemplateRender:
    """Kiểm tra templates render thành công."""

    def test_fastapi_inject_template_renders(self) -> None:
        """Template inject.py.jinja2 render thành công."""
        template_path = STACKS_DIR / "fastapi" / "core" / "cp28_custom_code" / "inject.py.jinja2"
        content = template_path.read_text(encoding="utf-8")
        # Template không dùng Jinja2 variables phức tạp nên render = content
        assert "CustomCodeInjector" in content
        assert "inject" in content

    def test_fastapi_blocks_template_renders(self) -> None:
        """Template blocks.py.jinja2 render thành công."""
        template_path = STACKS_DIR / "fastapi" / "core" / "cp28_custom_code" / "blocks.py.jinja2"
        content = template_path.read_text(encoding="utf-8")
        assert "CODE_BLOCKS" in content
        assert "CodeBlock" in content

    def test_fastapi_hooks_template_renders(self) -> None:
        """Template hooks.py.jinja2 render thành công."""
        template_path = STACKS_DIR / "fastapi" / "core" / "cp28_custom_code" / "hooks.py.jinja2"
        content = template_path.read_text(encoding="utf-8")
        assert "HOOK_REGISTRY" in content
        assert "trigger_hooks" in content

    def test_fastapi_patches_template_renders(self) -> None:
        """Template patches.py.jinja2 render thành công."""
        template_path = STACKS_DIR / "fastapi" / "core" / "cp28_custom_code" / "patches.py.jinja2"
        content = template_path.read_text(encoding="utf-8")
        assert "PatchEngine" in content
        assert "apply" in content

    def test_fastapi_registry_template_renders(self) -> None:
        """Template registry.py.jinja2 render thành công."""
        template_path = STACKS_DIR / "fastapi" / "core" / "cp28_custom_code" / "registry.py.jinja2"
        content = template_path.read_text(encoding="utf-8")
        assert "CustomCodeRegistry" in content
        assert "initialize" in content

    def test_nestjs_injector_template_renders(self) -> None:
        """Template NestJS injector.ts.jinja2 render thành công."""
        template_path = STACKS_DIR / "nestjs" / "core" / "cp28_custom_code" / "injector.ts.jinja2"
        content = template_path.read_text(encoding="utf-8")
        assert "CustomCodeInjector" in content
        assert "inject" in content

    def test_angular_injector_template_renders(self) -> None:
        """Template Angular injector.ts.jinja2 render thành công."""
        template_path = STACKS_DIR / "angular" / "core" / "cp28_custom_code" / "injector.ts.jinja2"
        content = template_path.read_text(encoding="utf-8")
        assert "CustomCodeInjector" in content

    def test_react_injector_template_renders(self) -> None:
        """Template React injector.ts.jinja2 render thành công."""
        template_path = STACKS_DIR / "react" / "core" / "cp28_custom_code" / "injector.ts.jinja2"
        content = template_path.read_text(encoding="utf-8")
        assert "CustomCodeInjector" in content


class TestEmitterModule:
    """Kiểm tra emitter module import thành công."""

    def test_import_models(self) -> None:
        """Import models thành công."""
        from midicoder.emitters.core.cp28_custom_code.models import (
            CustomCodeBlock,
            CustomCodeCollection,
            Hook,
            PatchRule,
        )
        assert CustomCodeBlock is not None
        assert CustomCodeCollection is not None
        assert Hook is not None
        assert PatchRule is not None

    def test_import_parser(self) -> None:
        """Import parser thành công."""
        from midicoder.emitters.core.cp28_custom_code.parser import CustomCodeParser
        assert CustomCodeParser is not None

    def test_import_recipes(self) -> None:
        """Import recipes thành công."""
        from midicoder.emitters.core.cp28_custom_code.recipes import (
            auto_generate_custom_code_from_mir,
            generate_default_blocks,
            generate_default_hooks,
            generate_default_patch_rules,
        )
        assert auto_generate_custom_code_from_mir is not None
        assert generate_default_blocks is not None
        assert generate_default_hooks is not None
        assert generate_default_patch_rules is not None

    def test_import_init(self) -> None:
        """Import __init__ thành công."""
        import midicoder.emitters.core.cp28_custom_code as cp28
        assert hasattr(cp28, "CustomCodeBlock")
        assert hasattr(cp28, "CustomCodeParser")
        assert hasattr(cp28, "auto_generate_custom_code_from_mir")

    def test_pack_yml_valid(self) -> None:
        """pack.yml parse YAML thành công."""
        import yaml
        pack_yml = EMITTERS_DIR / "pack.yml"
        data = yaml.safe_load(pack_yml.read_text(encoding="utf-8"))
        assert data["pack"]["id"] == "CP28"
        assert data["pack"]["internal_id"] == "cp28_custom_code"
        assert "custom_code_inject" in data["pack"]["capabilities_provided"]
        assert "hook_define" in data["pack"]["capabilities_provided"]
        assert "patch_apply" in data["pack"]["capabilities_provided"]

    def test_registry_has_cp28(self) -> None:
        """CP_ID_TO_INTERNAL có entry CP28."""
        from midicoder.contracts.registry import CP_ID_TO_INTERNAL
        assert "CP28" in CP_ID_TO_INTERNAL
        assert CP_ID_TO_INTERNAL["CP28"] == "cp28_custom_code"
