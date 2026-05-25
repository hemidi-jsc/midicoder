# coding: utf-8
"""
Test templates và pack manifest cho CP50 — Catalog & Taxonomy Engine.

Test:
- pack.yml tồn tại, hợp lệ, và chứa đúng thông tin
- Templates tồn tại cho 4 stacks (FastAPI, NestJS, Angular, React)
- Render template không lỗi và có nội dung đúng
- Cấu trúc template chứa các import/decorator quan trọng
"""

import pytest
from pathlib import Path
import yaml
import jinja2


# __file__ = .../midicoder/emitters/core/cp50_catalog/tests/test_templates.py
# parent x6 = midicoder-ce/
MIDICODER_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent

PACK_YML = MIDICODER_ROOT / "midicoder" / "emitters" / "core" / "cp50_catalog" / "pack.yml"

STACK_DIRS = {
    "fastapi": MIDICODER_ROOT / "midicoder" / "stacks" / "fastapi" / "core" / "cp50_catalog",
    "nestjs": MIDICODER_ROOT / "midicoder" / "stacks" / "nestjs" / "core" / "cp50_catalog",
    "angular": MIDICODER_ROOT / "midicoder" / "stacks" / "angular" / "core" / "cp50_catalog",
    "react": MIDICODER_ROOT / "midicoder" / "stacks" / "react" / "core" / "cp50_catalog",
}

EXPECTED_TEMPLATE_COUNTS = {
    "fastapi": 7,
    "nestjs": 7,
    "angular": 6,
    "react": 6,
}

FASTAPI_TEMPLATES = [
    "catalog_models.py.jinja2",
    "catalog_schemas.py.jinja2",
    "product_service.py.jinja2",
    "category_service.py.jinja2",
    "attribute_service.py.jinja2",
    "faceted_search_service.py.jinja2",
    "catalog_router.py.jinja2",
]

NESTJS_TEMPLATES = [
    "catalog.entity.ts.jinja2",
    "catalog.dto.ts.jinja2",
    "product.service.ts.jinja2",
    "category.service.ts.jinja2",
    "attribute.service.ts.jinja2",
    "catalog.controller.ts.jinja2",
    "catalog.module.ts.jinja2",
]

ANGULAR_TEMPLATES = [
    "product-list.component.ts.jinja2",
    "product-detail.component.ts.jinja2",
    "category-tree.component.ts.jinja2",
    "facet-filter.component.ts.jinja2",
    "catalog.service.ts.jinja2",
    "catalog.store.ts.jinja2",
]

REACT_TEMPLATES = [
    "ProductList.tsx.jinja2",
    "ProductDetail.tsx.jinja2",
    "CategoryTree.tsx.jinja2",
    "FacetFilter.tsx.jinja2",
    "useCatalog.ts.jinja2",
    "useFacetedSearch.ts.jinja2",
]

ALL_TEMPLATES = {
    "fastapi": FASTAPI_TEMPLATES,
    "nestjs": NESTJS_TEMPLATES,
    "angular": ANGULAR_TEMPLATES,
    "react": REACT_TEMPLATES,
}


def _render_template(stack: str, template_name: str) -> str:
    """Render template với context cơ bản."""
    template_path = STACK_DIRS[stack] / template_name
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(STACK_DIRS[stack])),
        undefined=jinja2.ChainableUndefined,
    )
    ctx = {
        "products": [],
        "categories": [],
        "variants": [],
        "attributes": [],
        "attribute_values": [],
        "use_search": True,
        "use_audit": False,
        "product_count": 0,
        "category_count": 0,
        "variant_count": 0,
        "attribute_count": 0,
    }
    template = env.get_template(template_name)
    return template.render(**ctx)


def _load_pack() -> dict:
    """Tải và parse pack.yml."""
    with open(PACK_YML, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ===========================================================================
# 1. Test pack.yml
# ===========================================================================

class TestPackYML:
    """Test pack.yml manifest cho CP50."""

    def test_pack_yml_exists(self):
        """pack.yml tồn tại."""
        assert PACK_YML.exists()

    def test_pack_yml_valid_yaml(self):
        """pack.yml là YAML hợp lệ."""
        data = _load_pack()
        assert data is not None
        assert "pack" in data

    def test_pack_id_is_cp50(self):
        """Pack ID là CP50."""
        data = _load_pack()
        assert data["pack"]["id"] == "CP50"

    def test_pack_internal_id(self):
        """Internal ID là cp50_catalog."""
        data = _load_pack()
        assert data["pack"]["internal_id"] == "cp50_catalog"

    def test_pack_category_is_commerce(self):
        """Pack category là commerce."""
        data = _load_pack()
        assert data["pack"]["category"] == "commerce"

    def test_pack_version_is_1_0_0(self):
        """Pack version là 1.0.0."""
        data = _load_pack()
        assert data["pack"]["version"] == "1.0.0"

    def test_pack_status_is_stable(self):
        """Pack status là stable."""
        data = _load_pack()
        assert data["pack"]["status"] == "stable"

    def test_pack_has_file_contributions(self):
        """Pack có file_contributions."""
        data = _load_pack()
        assert "file_contributions" in data["pack"]
        assert "infrastructure" in data["pack"]["file_contributions"]

    def test_pack_error_codes_prefix(self):
        """Error codes prefix là MDC-CP50."""
        data = _load_pack()
        assert data["pack"]["error_codes"]["prefix"] == "MDC-CP50"

    def test_pack_capabilities(self):
        """Capabilities đầy đủ 5 mục."""
        data = _load_pack()
        caps = data["pack"]["capabilities_provided"]
        assert "catalog_manage" in caps
        assert "taxonomy_hierarchy" in caps
        assert "faceted_search" in caps
        assert "attribute_manage" in caps
        assert "variant_manage" in caps

    def test_pack_frontend_integration_has_both(self):
        """Frontend integration có cả react và angular."""
        data = _load_pack()
        fe = data["pack"]["frontend_integration"]
        assert "react" in fe
        assert "angular" in fe


# ===========================================================================
# 2. Test stack templates exist
# ===========================================================================

class TestFastAPITemplatesExist:
    """Test FastAPI templates tồn tại."""

    def test_fastapi_templates_exist(self):
        """Tất cả 7 FastAPI templates tồn tại."""
        stack_dir = STACK_DIRS["fastapi"]
        for template in FASTAPI_TEMPLATES:
            assert (stack_dir / template).exists(), f"Thiếu template: {template}"


class TestNestJSTemplatesExist:
    """Test NestJS templates tồn tại."""

    def test_nestjs_templates_exist(self):
        """Tất cả 7 NestJS templates tồn tại."""
        stack_dir = STACK_DIRS["nestjs"]
        for template in NESTJS_TEMPLATES:
            assert (stack_dir / template).exists(), f"Thiếu template: {template}"


class TestAngularTemplatesExist:
    """Test Angular templates tồn tại."""

    def test_angular_templates_exist(self):
        """Tất cả 6 Angular templates tồn tại."""
        stack_dir = STACK_DIRS["angular"]
        for template in ANGULAR_TEMPLATES:
            assert (stack_dir / template).exists(), f"Thiếu template: {template}"


class TestReactTemplatesExist:
    """Test React templates tồn tại."""

    def test_react_templates_exist(self):
        """Tất cả 6 React templates tồn tại."""
        stack_dir = STACK_DIRS["react"]
        for template in REACT_TEMPLATES:
            assert (stack_dir / template).exists(), f"Thiếu template: {template}"


class TestTemplateCounts:
    """Test số lượng template đúng."""

    def test_total_template_count(self):
        """Tổng số template là 26."""
        total = 0
        for stack, templates in ALL_TEMPLATES.items():
            expected = EXPECTED_TEMPLATE_COUNTS[stack]
            actual = len(templates)
            assert actual == expected, f"{stack}: mong đợi {expected}, thực tế {actual}"
            total += actual
        assert total == 26, f"Tổng template mong đợi 26, thực tế {total}"

    def test_each_stack_count_matches(self):
        """Mỗi stack có số template đúng."""
        for stack in STACK_DIRS:
            stack_dir = STACK_DIRS[stack]
            actual_files = [f.name for f in stack_dir.glob("*.jinja2")]
            expected = EXPECTED_TEMPLATE_COUNTS[stack]
            assert len(actual_files) == expected, (
                f"{stack}: mong đợi {expected} files, "
                f"thực tế {len(actual_files)}: {actual_files}"
            )


# ===========================================================================
# 3. Test template rendering
# ===========================================================================

class TestTemplateRendering:
    """Test render template không lỗi."""

    def test_fastapi_templates_render_without_error(self):
        """Tất cả FastAPI templates render thành công."""
        for template in FASTAPI_TEMPLATES:
            result = _render_template("fastapi", template)
            assert isinstance(result, str), f"{template} không trả về chuỗi"

    def test_nestjs_templates_render_without_error(self):
        """Tất cả NestJS templates render thành công."""
        for template in NESTJS_TEMPLATES:
            result = _render_template("nestjs", template)
            assert isinstance(result, str), f"{template} không trả về chuỗi"

    def test_angular_templates_render_without_error(self):
        """Tất cả Angular templates render thành công."""
        for template in ANGULAR_TEMPLATES:
            result = _render_template("angular", template)
            assert isinstance(result, str), f"{template} không trả về chuỗi"

    def test_react_templates_render_without_error(self):
        """Tất cả React templates render thành công."""
        for template in REACT_TEMPLATES:
            result = _render_template("react", template)
            assert isinstance(result, str), f"{template} không trả về chuỗi"

    def test_rendered_content_not_empty(self):
        """Tất cả 26 templates có nội dung render > 0 ký tự."""
        for stack, templates in ALL_TEMPLATES.items():
            for template in templates:
                result = _render_template(stack, template)
                assert len(result) > 0, (
                    f"{stack}/{template} render ra nội dung rỗng"
                )

    def test_fastapi_template_has_vietnamese_comments(self):
        """FastAPI templates có comment tiếng Việt."""
        result = _render_template("fastapi", "catalog_models.py.jinja2")
        # Kiem tra co chua ky tu Unicode ngoai ASCII (tieng Viet co dau)
        has_vietnamese = any(ord(c) > 127 for c in result)
        assert has_vietnamese, (
            "catalog_models.py.jinja2 khong co ky tu tieng Viet co dau"
        )

    def test_react_template_has_raw_wrapper(self):
        """React JSX templates có {% raw %} wrapper."""
        raw_source = (STACK_DIRS["react"] / "ProductList.tsx.jinja2").read_text(
            encoding="utf-8"
        )
        assert "{% raw %}" in raw_source, (
            "ProductList.tsx.jinja2 thiếu {% raw %} wrapper cho JSX"
        )


# ===========================================================================
# 4. Test template structure
# ===========================================================================

class TestTemplateStructure:
    """Test cấu trúc nội dung template."""

    def test_fastapi_models_has_imports(self):
        """FastAPI models có import SQLAlchemy."""
        result = _render_template("fastapi", "catalog_models.py.jinja2")
        assert "from sqlalchemy" in result or "import sqlalchemy" in result, (
            "catalog_models.py.jinja2 thiếu import sqlalchemy"
        )

    def test_fastapi_schemas_has_pydantic(self):
        """FastAPI schemas có import Pydantic."""
        result = _render_template("fastapi", "catalog_schemas.py.jinja2")
        assert "from pydantic" in result, (
            "catalog_schemas.py.jinja2 thiếu import pydantic"
        )

    def test_nestjs_entity_has_typeorm(self):
        """NestJS entity có TypeORM decorator @Entity."""
        result = _render_template("nestjs", "catalog.entity.ts.jinja2")
        assert "@Entity" in result or "typeorm" in result.lower(), (
            "catalog.entity.ts.jinja2 thiếu TypeORM decorator/entity"
        )

    def test_nestjs_module_has_decorators(self):
        """NestJS module có @Module decorator."""
        result = _render_template("nestjs", "catalog.module.ts.jinja2")
        assert "@Module" in result, (
            "catalog.module.ts.jinja2 thiếu @Module decorator"
        )

    def test_angular_service_has_injectable(self):
        """Angular service có @Injectable decorator."""
        result = _render_template("angular", "catalog.service.ts.jinja2")
        assert "@Injectable" in result, (
            "catalog.service.ts.jinja2 thiếu @Injectable decorator"
        )

    def test_react_component_has_react_import(self):
        """React component có import từ 'react'."""
        result = _render_template("react", "ProductList.tsx.jinja2")
        assert "from 'react'" in result or 'from "react"' in result, (
            "ProductList.tsx.jinja2 thiếu import từ 'react'"
        )


# ===========================================================================
# 5. Test Rule V1 & V2 (P2-17)
# ===========================================================================

class TestRuleV1NoMidicoderImport:
    """Rule V1: Output của template KHÔNG chứa 'from midicoder'."""

    def test_fastapi_no_midicoder_import(self):
        """FastAPI templates không chứa 'from midicoder' trong output."""
        for template in FASTAPI_TEMPLATES:
            result = _render_template("fastapi", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_nestjs_no_midicoder_import(self):
        """NestJS templates không chứa 'from midicoder' trong output."""
        for template in NESTJS_TEMPLATES:
            result = _render_template("nestjs", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_angular_no_midicoder_import(self):
        """Angular templates không chứa 'from midicoder' trong output."""
        for template in ANGULAR_TEMPLATES:
            result = _render_template("angular", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_react_no_midicoder_import(self):
        """React templates không chứa 'from midicoder' trong output."""
        for template in REACT_TEMPLATES:
            result = _render_template("react", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"


class TestRuleV2NoPostInit:
    """Rule V2: Output của template KHÔNG chứa '__post_init__'."""

    def test_fastapi_no_post_init(self):
        """FastAPI templates không chứa __post_init__ trong output."""
        for template in FASTAPI_TEMPLATES:
            result = _render_template("fastapi", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_nestjs_no_post_init(self):
        """NestJS templates không chứa __post_init__ trong output."""
        for template in NESTJS_TEMPLATES:
            result = _render_template("nestjs", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_angular_no_post_init(self):
        """Angular templates không chứa __post_init__ trong output."""
        for template in ANGULAR_TEMPLATES:
            result = _render_template("angular", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_react_no_post_init(self):
        """React templates không chứa __post_init__ trong output."""
        for template in REACT_TEMPLATES:
            result = _render_template("react", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"
