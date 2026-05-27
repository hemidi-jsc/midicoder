# coding: utf-8
"""
Template verification tests cho CP27 Plugin System Generator.

Kiểm tra:
- Tất cả Jinja2 templates tồn tại và render được
- Context variables đúng (entities, commands, policies)
- Output chứa các keyword quan trọng

Tự động sinh bởi CP27 — Plugin System Generator.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import jinja2
import pytest

from midicoder.pipeline.emitter import Emitter


# Đường dẫn đến template directories
STACKS_DIR = Path(__file__).parents[4] / "stacks"

# ============================================================================
# Template directories dict và danh sách templates (cho Rule V1/V2)
# ============================================================================

STACK_DIRS = {
    "fastapi": STACKS_DIR / "fastapi" / "core" / "cp27_plugin_system",
    "nestjs": STACKS_DIR / "nestjs" / "core" / "cp27_plugin_system",
    "angular": STACKS_DIR / "angular" / "core" / "cp27_plugin_system",
    "react": STACKS_DIR / "react" / "core" / "cp27_plugin_system",
}

FASTAPI_TEMPLATES = [
    "__init__.py.jinja2",
    "api.py.jinja2",
    "contracts.py.jinja2",
    "example_plugin.py.jinja2",
    "loader.py.jinja2",
    "manager.py.jinja2",
    "middleware.py.jinja2",
    "plugin.json.jinja2",
    "policies.py.jinja2",
    "registry.py.jinja2",
    "slots.py.jinja2",
]

NESTJS_TEMPLATES = [
    "contracts.ts.jinja2",
    "example.plugin.ts.jinja2",
    "plugin-loader.ts.jinja2",
    "plugin-manager.service.ts.jinja2",
    "plugin-registry.service.ts.jinja2",
    "plugin.controller.ts.jinja2",
    "plugin.json.jinja2",
    "plugin.middleware.ts.jinja2",
    "plugins.module.ts.jinja2",
    "policies.ts.jinja2",
    "slots.ts.jinja2",
]

ANGULAR_TEMPLATES = [
    "example.plugin.ts.jinja2",
    "plugin-api.service.ts.jinja2",
    "plugin-contracts.ts.jinja2",
    "plugin-loader.ts.jinja2",
    "plugin-registry.ts.jinja2",
    "plugin-slots.ts.jinja2",
    "plugin.interceptor.ts.jinja2",
    "plugin.json.jinja2",
    "plugin.module.ts.jinja2",
]

REACT_TEMPLATES = [
    "example.plugin.ts.jinja2",
    "plugin-api.ts.jinja2",
    "plugin-contracts.ts.jinja2",
    "plugin-loader.ts.jinja2",
    "plugin-registry.ts.jinja2",
    "plugin-slots.ts.jinja2",
    "plugin.json.jinja2",
]

ALL_TEMPLATES = {
    "fastapi": FASTAPI_TEMPLATES,
    "nestjs": NESTJS_TEMPLATES,
    "angular": ANGULAR_TEMPLATES,
    "react": REACT_TEMPLATES,
}


def _render_template_j2(stack: str, template_name: str) -> str:
    """Render template với context cơ bản sử dụng Jinja2 trực tiếp (cho Rule V1/V2)."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(STACK_DIRS[stack])),
        undefined=jinja2.ChainableUndefined,
    )
    # Context tối thiểu: các template CP27 dùng entities, commands, queries, policies
    ctx = {
        "entities": [],
        "commands": [],
        "queries": [],
        "policies": [],
    }
    template = env.get_template(template_name)
    return template.render(**ctx)


def _get_template_dir(stack: str) -> Path:
    """Lấy đường dẫn template directory cho stack."""
    return STACKS_DIR / stack / "core" / "cp27_plugin_system"


def _get_templates(stack: str) -> list[Path]:
    """Lấy danh sách template files cho stack."""
    template_dir = _get_template_dir(stack)
    if not template_dir.exists():
        return []
    return sorted(template_dir.glob("*.jinja2"))


def _render_template(stack: str, template_name: str, context: dict[str, Any]) -> str:
    """Render template và trả về content."""
    emitter = Emitter(stack=stack)
    template_path = f"cp27_plugin_system/{template_name}"
    return emitter.render(template_path, context)


# ===========================================================================
# Test FastAPI templates
# ===========================================================================


class TestFastAPITemplates:
    """Kiểm tra templates FastAPI."""

    @pytest.fixture()
    def context(self) -> dict[str, Any]:
        """Context mẫu cho test."""
        return {
            "entities": [
                {"id": "Product", "fields": [{"name": "name"}, {"name": "price"}]},
                {"id": "Order", "fields": [{"name": "total"}]},
            ],
            "commands": [
                {"id": "CreateOrder", "input": [{"name": "product_id"}, {"name": "quantity"}]},
                {"id": "CancelOrder", "input": [{"name": "order_id"}]},
            ],
            "queries": [{"id": "GetProductList", "returns": "Product"}],
            "policies": [],
        }

    def test_templates_exist(self) -> None:
        """Kiểm tra templates FastAPI tồn tại."""
        templates = _get_templates("fastapi")
        assert len(templates) >= 8, f"Ít nhất 8 templates, tìm thấy {len(templates)}"

    def test_init_template(self, context: dict) -> None:
        """Kiểm tra __init__.py.jinja2 render được."""
        content = _render_template("fastapi", "__init__.py.jinja2", context)
        assert "plugin" in content.lower() or "__all__" in content or '"""' in content

    def test_slots_template(self, context: dict) -> None:
        """Kiểm tra slots.py.jinja2 render được."""
        content = _render_template("fastapi", "slots.py.jinja2", context)
        assert "on_init" in content or "ON_INIT" in content
        # Kiểm tra command hooks được generate
        assert "CREATEORDER" in content or "createorder" in content or "create_order" in content

    def test_contracts_template(self, context: dict) -> None:
        """Kiểm tra contracts.py.jinja2 render được."""
        content = _render_template("fastapi", "contracts.py.jinja2", context)
        assert "Protocol" in content or "protocol" in content.lower()
        assert "PluginContext" in content or "plugin_context" in content

    def test_policies_template(self, context: dict) -> None:
        """Kiểm tra policies.py.jinja2 render được."""
        content = _render_template("fastapi", "policies.py.jinja2", context)
        assert "policy" in content.lower()
        assert "signature" in content.lower() or "version" in content.lower()

    def test_loader_template(self, context: dict) -> None:
        """Kiểm tra loader.py.jinja2 render được."""
        content = _render_template("fastapi", "loader.py.jinja2", context)
        assert "loader" in content.lower() or "load" in content.lower()
        assert "discover" in content.lower() or "import" in content.lower()

    def test_registry_template(self, context: dict) -> None:
        """Kiểm tra registry.py.jinja2 render được."""
        content = _render_template("fastapi", "registry.py.jinja2", context)
        assert "registry" in content.lower() or "register" in content.lower()

    def test_manager_template(self, context: dict) -> None:
        """Kiểm tra manager.py.jinja2 render được."""
        content = _render_template("fastapi", "manager.py.jinja2", context)
        assert "manager" in content.lower() or "enable" in content.lower()

    def test_api_template(self, context: dict) -> None:
        """Kiểm tra api.py.jinja2 render được."""
        content = _render_template("fastapi", "api.py.jinja2", context)
        assert "plugin" in content.lower()
        # Kiểm tra endpoints
        assert "/plugins" in content or "@router" in content or "APIRouter" in content

    def test_middleware_template(self, context: dict) -> None:
        """Kiểm tra middleware.py.jinja2 render được."""
        content = _render_template("fastapi", "middleware.py.jinja2", context)
        assert "middleware" in content.lower()

    def test_example_plugin_template(self, context: dict) -> None:
        """Kiểm tra example_plugin.py.jinja2 render được."""
        content = _render_template("fastapi", "example_plugin.py.jinja2", context)
        assert "example" in content.lower() or "plugin" in content.lower()

    def test_plugin_json_template(self, context: dict) -> None:
        """Kiểm tra plugin.json.jinja2 render được."""
        content = _render_template("fastapi", "plugin.json.jinja2", context)
        assert "id" in content or "name" in content
        assert "{" in content  # Valid JSON


# ===========================================================================
# Test NestJS templates
# ===========================================================================


class TestNestJSTemplates:
    """Kiểm tra templates NestJS."""

    @pytest.fixture()
    def context(self) -> dict[str, Any]:
        """Context mẫu cho test."""
        return {
            "entities": [{"id": "Product", "fields": [{"name": "name"}]}],
            "commands": [{"id": "CreateOrder", "input": []}],
            "queries": [],
            "policies": [],
        }

    def test_templates_exist(self) -> None:
        """Kiểm tra templates NestJS tồn tại."""
        templates = _get_templates("nestjs")
        assert len(templates) >= 8, f"Ít nhất 8 templates, tìm thấy {len(templates)}"

    def test_module_template(self, context: dict) -> None:
        """Kiểm tra plugins.module.ts.jinja2 render được."""
        content = _render_template("nestjs", "plugins.module.ts.jinja2", context)
        assert "@Module" in content or "Module" in content
        assert "plugins" in content.lower() or "import" in content

    def test_slots_template(self, context: dict) -> None:
        """Kiểm tra slots.ts.jinja2 render được."""
        content = _render_template("nestjs", "slots.ts.jinja2", context)
        assert "enum" in content
        assert "PluginSlot" in content or "plugin" in content.lower()

    def test_contracts_template(self, context: dict) -> None:
        """Kiểm tra contracts.ts.jinja2 render được."""
        content = _render_template("nestjs", "contracts.ts.jinja2", context)
        assert "interface" in content or "IPlugin" in content

    def test_loader_template(self, context: dict) -> None:
        """Kiểm tra plugin-loader.ts.jinja2 render được."""
        content = _render_template("nestjs", "plugin-loader.ts.jinja2", context)
        assert "loader" in content.lower() or "load" in content.lower()

    def test_registry_template(self, context: dict) -> None:
        """Kiểm tra plugin-registry.service.ts.jinja2 render được."""
        content = _render_template("nestjs", "plugin-registry.service.ts.jinja2", context)
        assert "registry" in content.lower() or "register" in content.lower()

    def test_manager_template(self, context: dict) -> None:
        """Kiểm tra plugin-manager.service.ts.jinja2 render được."""
        content = _render_template("nestjs", "plugin-manager.service.ts.jinja2", context)
        assert "manager" in content.lower() or "enable" in content.lower()

    def test_controller_template(self, context: dict) -> None:
        """Kiểm tra plugin.controller.ts.jinja2 render được."""
        content = _render_template("nestjs", "plugin.controller.ts.jinja2", context)
        assert "@Controller" in content or "Controller" in content

    def test_middleware_template(self, context: dict) -> None:
        """Kiểm tra plugin.middleware.ts.jinja2 render được."""
        content = _render_template("nestjs", "plugin.middleware.ts.jinja2", context)
        assert "middleware" in content.lower()


# ===========================================================================
# Test Angular templates
# ===========================================================================


class TestAngularTemplates:
    """Kiểm tra templates Angular."""

    @pytest.fixture()
    def context(self) -> dict[str, Any]:
        """Context mẫu cho test."""
        return {
            "entities": [{"id": "Product", "fields": []}],
            "commands": [{"id": "CreateOrder", "input": []}],
            "queries": [],
            "policies": [],
        }

    def test_templates_exist(self) -> None:
        """Kiểm tra templates Angular tồn tại."""
        templates = _get_templates("angular")
        assert len(templates) >= 5, f"Ít nhất 5 templates, tìm thấy {len(templates)}"

    def test_module_template(self, context: dict) -> None:
        """Kiểm tra plugin.module.ts.jinja2 render được."""
        content = _render_template("angular", "plugin.module.ts.jinja2", context)
        assert "@NgModule" in content or "NgModule" in content

    def test_contracts_template(self, context: dict) -> None:
        """Kiểm tra plugin-contracts.ts.jinja2 render được."""
        content = _render_template("angular", "plugin-contracts.ts.jinja2", context)
        assert "interface" in content or "IPlugin" in content

    def test_api_service_template(self, context: dict) -> None:
        """Kiểm tra plugin-api.service.ts.jinja2 render được."""
        content = _render_template("angular", "plugin-api.service.ts.jinja2", context)
        assert "service" in content.lower() or "HttpClient" in content

    def test_registry_template(self, context: dict) -> None:
        """Kiểm tra plugin-registry.ts.jinja2 render được."""
        content = _render_template("angular", "plugin-registry.ts.jinja2", context)
        assert "registry" in content.lower() or "register" in content.lower()


# ===========================================================================
# Test React templates
# ===========================================================================


class TestReactTemplates:
    """Kiểm tra templates React."""

    @pytest.fixture()
    def context(self) -> dict[str, Any]:
        """Context mẫu cho test."""
        return {
            "entities": [{"id": "Product", "fields": []}],
            "commands": [{"id": "CreateOrder", "input": []}],
            "queries": [],
            "policies": [],
        }

    def test_templates_exist(self) -> None:
        """Kiểm tra templates React tồn tại."""
        templates = _get_templates("react")
        assert len(templates) >= 4, f"Ít nhất 4 templates, tìm thấy {len(templates)}"

    def test_contracts_template(self, context: dict) -> None:
        """Kiểm tra plugin-contracts.ts.jinja2 render được."""
        content = _render_template("react", "plugin-contracts.ts.jinja2", context)
        assert "interface" in content or "IPlugin" in content

    def test_registry_template(self, context: dict) -> None:
        """Kiểm tra plugin-registry.ts.jinja2 render được."""
        content = _render_template("react", "plugin-registry.ts.jinja2", context)
        assert "registry" in content.lower() or "createContext" in content

    def test_api_template(self, context: dict) -> None:
        """Kiểm tra plugin-api.ts.jinja2 render được."""
        content = _render_template("react", "plugin-api.ts.jinja2", context)
        assert "fetch" in content or "api" in content.lower()


# ===========================================================================
# Cross-stack tests
# ===========================================================================


class TestCrossStackTemplates:
    """Kiểm tra templates xuyên stack."""

    def test_all_stacks_have_templates(self) -> None:
        """Kiểm tra cả 4 stacks có templates."""
        for stack in ["fastapi", "nestjs", "angular", "react"]:
            templates = _get_templates(stack)
            assert len(templates) > 0, f"Stack {stack} không có template nào"

    def test_backend_has_more_templates_than_frontend(self) -> None:
        """Kiểm tra backend stacks có nhiều templates hơn frontend."""
        fastapi_count = len(_get_templates("fastapi"))
        nestjs_count = len(_get_templates("nestjs"))
        angular_count = len(_get_templates("angular"))
        react_count = len(_get_templates("react"))
        # Backend nên có >= 10 templates mỗi stack
        assert fastapi_count >= 10, f"FastAPI nên có >= 10 templates, có {fastapi_count}"
        assert nestjs_count >= 10, f"NestJS nên có >= 10 templates, có {nestjs_count}"
        # Frontend nên có >= 5 templates mỗi stack
        assert angular_count >= 5, f"Angular nên có >= 5 templates, có {angular_count}"
        assert react_count >= 4, f"React nên có >= 4 templates, có {react_count}"

    def test_total_template_count(self) -> None:
        """Kiểm tra tổng số templates."""
        total = sum(
            len(_get_templates(s))
            for s in ["fastapi", "nestjs", "angular", "react"]
        )
        assert total >= 30, f"Tổng templates nên >= 30, có {total}"


# ===========================================================================
# Test Rule V1 & V2 (P2-17)
# ===========================================================================

class TestRuleV1NoMidicoderImport:
    """Rule V1: Output của template KHÔNG chứa 'from midicoder'."""

    def test_fastapi_no_midicoder_import(self) -> None:
        """FastAPI templates không chứa 'from midicoder' trong output."""
        for template in FASTAPI_TEMPLATES:
            result = _render_template_j2("fastapi", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_nestjs_no_midicoder_import(self) -> None:
        """NestJS templates không chứa 'from midicoder' trong output."""
        for template in NESTJS_TEMPLATES:
            result = _render_template_j2("nestjs", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_angular_no_midicoder_import(self) -> None:
        """Angular templates không chứa 'from midicoder' trong output."""
        for template in ANGULAR_TEMPLATES:
            result = _render_template_j2("angular", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_react_no_midicoder_import(self) -> None:
        """React templates không chứa 'from midicoder' trong output."""
        for template in REACT_TEMPLATES:
            result = _render_template_j2("react", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"


class TestRuleV2NoPostInit:
    """Rule V2: Output của template KHÔNG chứa '__post_init__'."""

    def test_fastapi_no_post_init(self) -> None:
        """FastAPI templates không chứa __post_init__ trong output."""
        for template in FASTAPI_TEMPLATES:
            result = _render_template_j2("fastapi", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_nestjs_no_post_init(self) -> None:
        """NestJS templates không chứa __post_init__ trong output."""
        for template in NESTJS_TEMPLATES:
            result = _render_template_j2("nestjs", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_angular_no_post_init(self) -> None:
        """Angular templates không chứa __post_init__ trong output."""
        for template in ANGULAR_TEMPLATES:
            result = _render_template_j2("angular", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_react_no_post_init(self) -> None:
        """React templates không chứa __post_init__ trong output."""
        for template in REACT_TEMPLATES:
            result = _render_template_j2("react", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"
