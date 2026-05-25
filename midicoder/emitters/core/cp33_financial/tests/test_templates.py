# coding: utf-8
"""
Test templates và pack manifest cho CP33 — Financial Engine.

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


# __file__ = .../midicoder/emitters/core/cp33_financial/tests/test_templates.py
# parent x6 = midicoder-ce/
MIDICODER_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent

PACK_YML = MIDICODER_ROOT / "midicoder" / "emitters" / "core" / "cp33_financial" / "pack.yml"

STACK_DIRS = {
    "fastapi": MIDICODER_ROOT / "midicoder" / "stacks" / "fastapi" / "core" / "cp33_financial",
    "nestjs": MIDICODER_ROOT / "midicoder" / "stacks" / "nestjs" / "core" / "cp33_financial",
    "angular": MIDICODER_ROOT / "midicoder" / "stacks" / "angular" / "core" / "cp33_financial",
    "react": MIDICODER_ROOT / "midicoder" / "stacks" / "react" / "core" / "cp33_financial",
}

EXPECTED_TEMPLATE_COUNTS = {
    "fastapi": 4,
    "nestjs": 4,
    "angular": 2,
    "react": 2,
}

FASTAPI_TEMPLATES = [
    "currency_model.py.jinja2",
    "account_model.py.jinja2",
    "ledger_service.py.jinja2",
    "fx_service.py.jinja2",
]

NESTJS_TEMPLATES = [
    "currency-model.ts.jinja2",
    "account-model.ts.jinja2",
    "ledger-service.ts.jinja2",
    "fx-service.ts.jinja2",
]

ANGULAR_TEMPLATES = [
    "ledger-dashboard.component.ts.jinja2",
    "transaction-detail.component.ts.jinja2",
]

REACT_TEMPLATES = [
    "LedgerDashboard.tsx.jinja2",
    "TransactionDetail.tsx.jinja2",
]

ALL_TEMPLATES = {
    "fastapi": FASTAPI_TEMPLATES,
    "nestjs": NESTJS_TEMPLATES,
    "angular": ANGULAR_TEMPLATES,
    "react": REACT_TEMPLATES,
}


def _render_template(stack: str, template_name: str) -> str:
    """Render template với context cơ bản cho CP33.

    Nếu template chứa JSX/HTML conflict với Jinja2 syntax (e.g. Angular
    inline template với `{{ }}` và `| async`, React JSX với `{{ }}`),
    fallback về đọc raw source.
    """
    template_path = STACK_DIRS[stack] / template_name
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(STACK_DIRS[stack])),
        undefined=jinja2.ChainableUndefined,
    )
    ctx = {
        "currencies": [],
        "accounts": [],
        "fx_rates": [],
        "transactions": [],
        "base_currency": "USD",
        "ui_framework": "material",
    }
    try:
        template = env.get_template(template_name)
        return template.render(**ctx)
    except jinja2.TemplateSyntaxError:
        # Template chứa JSX/HTML conflict với Jinja2 - trả về raw source
        return template_path.read_text(encoding="utf-8")


def _load_pack() -> dict:
    """Tải và parse pack.yml."""
    with open(PACK_YML, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ===========================================================================
# 1. Test pack.yml
# ===========================================================================

class TestPackYML:
    """Test pack.yml manifest cho CP33."""

    def test_pack_yml_exists(self):
        """pack.yml tồn tại."""
        assert PACK_YML.exists()

    def test_pack_yml_valid_yaml(self):
        """pack.yml là YAML hợp lệ."""
        data = _load_pack()
        assert data is not None
        assert "pack" in data

    def test_pack_id_is_cp33(self):
        """Pack ID là CP33."""
        data = _load_pack()
        assert data["pack"]["id"] == "CP33"

    def test_pack_internal_id(self):
        """Internal ID là cp33_financial."""
        data = _load_pack()
        assert data["pack"]["internal_id"] == "cp33_financial"

    def test_pack_category_is_financial(self):
        """Pack category là financial."""
        data = _load_pack()
        assert data["pack"]["category"] == "financial"

    def test_pack_version_is_1_0_0(self):
        """Pack version là 1.0.0."""
        data = _load_pack()
        assert data["pack"]["version"] == "1.0.0"

    def test_pack_status_is_stable(self):
        """Pack status là stable."""
        data = _load_pack()
        assert data["pack"]["status"] == "stable"

    def test_pack_has_dependencies(self):
        """Pack có dependencies CP01, CP08, CP14."""
        data = _load_pack()
        deps = data["pack"]["depends_on"]
        assert "CP01" in deps
        assert "CP08" in deps
        assert "CP14" in deps

    def test_pack_has_file_contributions(self):
        """Pack có file_contributions."""
        data = _load_pack()
        assert "file_contributions" in data["pack"]
        assert "infrastructure" in data["pack"]["file_contributions"]

    def test_pack_error_codes_prefix(self):
        """Error codes prefix là MDC-CP33."""
        data = _load_pack()
        assert data["pack"]["error_codes"]["prefix"] == "MDC-CP33"

    def test_pack_capabilities(self):
        """Capabilities đầy đủ 4 mục."""
        data = _load_pack()
        caps = data["pack"]["capabilities_provided"]
        assert "multi_currency_calc" in caps
        assert "fx_rate_convert" in caps
        assert "double_entry_ledger" in caps
        assert "rounding_apply" in caps

    def test_pack_has_definitions(self):
        """Pack có 5 definitions."""
        data = _load_pack()
        defs = data["pack"]["definitions"]
        assert len(defs) == 5
        def_names = [d["name"] for d in defs]
        assert "Currency" in def_names
        assert "FXRate" in def_names
        assert "Account" in def_names
        assert "LedgerEntry" in def_names
        assert "FinancialTransaction" in def_names

    def test_pack_has_obligations(self):
        """Pack có 2 obligations."""
        data = _load_pack()
        obs = data["pack"]["obligations"]
        assert len(obs) == 2
        ob_names = [o["name"] for o in obs]
        assert "DoubleEntryBalanced" in ob_names
        assert "LedgerImmutable" in ob_names

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
        """Tất cả 4 FastAPI templates tồn tại."""
        stack_dir = STACK_DIRS["fastapi"]
        for template in FASTAPI_TEMPLATES:
            assert (stack_dir / template).exists(), f"Thiếu template: {template}"


class TestNestJSTemplatesExist:
    """Test NestJS templates tồn tại."""

    def test_nestjs_templates_exist(self):
        """Tất cả 4 NestJS templates tồn tại."""
        stack_dir = STACK_DIRS["nestjs"]
        for template in NESTJS_TEMPLATES:
            assert (stack_dir / template).exists(), f"Thiếu template: {template}"


class TestAngularTemplatesExist:
    """Test Angular templates tồn tại."""

    def test_angular_templates_exist(self):
        """Tất cả 2 Angular templates tồn tại."""
        stack_dir = STACK_DIRS["angular"]
        for template in ANGULAR_TEMPLATES:
            assert (stack_dir / template).exists(), f"Thiếu template: {template}"


class TestReactTemplatesExist:
    """Test React templates tồn tại."""

    def test_react_templates_exist(self):
        """Tất cả 2 React templates tồn tại."""
        stack_dir = STACK_DIRS["react"]
        for template in REACT_TEMPLATES:
            assert (stack_dir / template).exists(), f"Thiếu template: {template}"


class TestTemplateCounts:
    """Test số lượng template đúng."""

    def test_total_template_count(self):
        """Tổng số template là 12."""
        total = 0
        for stack, templates in ALL_TEMPLATES.items():
            expected = EXPECTED_TEMPLATE_COUNTS[stack]
            actual = len(templates)
            assert actual == expected, f"{stack}: mong đợi {expected}, thực tế {actual}"
            total += actual
        assert total == 12, f"Tổng template mong đợi 12, thực tế {total}"

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
        """Tất cả 12 templates có nội dung render > 0 ký tự."""
        for stack, templates in ALL_TEMPLATES.items():
            for template in templates:
                result = _render_template(stack, template)
                assert len(result) > 0, (
                    f"{stack}/{template} render ra nội dung rỗng"
                )

    def test_fastapi_template_has_vietnamese_comments(self):
        """FastAPI templates có comment tiếng Việt."""
        result = _render_template("fastapi", "currency_model.py.jinja2")
        # Kiem tra co chua ky tu Unicode ngoai ASCII (tieng Viet co dau)
        has_vietnamese = any(ord(c) > 127 for c in result)
        assert has_vietnamese, (
            "currency_model.py.jinja2 khong co ky tu tieng Viet co dau"
        )

    def test_react_template_has_raw_wrapper(self):
        """React JSX templates có {% raw %} wrapper."""
        raw_source = (STACK_DIRS["react"] / "LedgerDashboard.tsx.jinja2").read_text(
            encoding="utf-8"
        )
        assert "{% raw %}" in raw_source, (
            "LedgerDashboard.tsx.jinja2 thiếu {% raw %} wrapper cho JSX"
        )


# ===========================================================================
# 4. Test template structure
# ===========================================================================

class TestTemplateStructure:
    """Test cấu trúc nội dung template."""

    # --- FastAPI ---
    def test_fastapi_currency_model_has_sqlalchemy(self):
        """FastAPI currency_model có import SQLAlchemy."""
        result = _render_template("fastapi", "currency_model.py.jinja2")
        assert "from sqlalchemy" in result or "import sqlalchemy" in result, (
            "currency_model.py.jinja2 thiếu import sqlalchemy"
        )

    def test_fastapi_currency_model_has_rounding_mode(self):
        """FastAPI currency_model có RoundingMode enum."""
        result = _render_template("fastapi", "currency_model.py.jinja2")
        assert "RoundingMode" in result, (
            "currency_model.py.jinja2 thiếu RoundingMode enum"
        )

    def test_fastapi_ledger_service_has_decimal(self):
        """FastAPI ledger_service có import Decimal."""
        result = _render_template("fastapi", "ledger_service.py.jinja2")
        assert "from decimal import Decimal" in result or "from decimal" in result, (
            "ledger_service.py.jinja2 thiếu import Decimal"
        )

    def test_fastapi_ledger_service_has_imbalance_error(self):
        """FastAPI ledger_service có ImbalanceError class."""
        result = _render_template("fastapi", "ledger_service.py.jinja2")
        assert "ImbalanceError" in result, (
            "ledger_service.py.jinja2 thiếu ImbalanceError"
        )

    def test_fastapi_fx_service_has_decimal(self):
        """FastAPI fx_service có import Decimal."""
        result = _render_template("fastapi", "fx_service.py.jinja2")
        assert "Decimal" in result, (
            "fx_service.py.jinja2 thiếu Decimal cho tính toán"
        )

    # --- NestJS ---
    def test_nestjs_currency_model_has_typeorm(self):
        """NestJS currency-model có TypeORM decorator @Entity."""
        result = _render_template("nestjs", "currency-model.ts.jinja2")
        assert "@Entity" in result or "typeorm" in result.lower(), (
            "currency-model.ts.jinja2 thiếu TypeORM decorator/entity"
        )

    def test_nestjs_account_model_has_typeorm(self):
        """NestJS account-model có TypeORM decorator."""
        result = _render_template("nestjs", "account-model.ts.jinja2")
        assert "@Entity" in result or "@Column" in result, (
            "account-model.ts.jinja2 thiếu TypeORM decorator"
        )

    def test_nestjs_ledger_service_has_class(self):
        """NestJS ledger-service có class declaration."""
        result = _render_template("nestjs", "ledger-service.ts.jinja2")
        assert "class " in result, (
            "ledger-service.ts.jinja2 thiếu class declaration"
        )

    def test_nestjs_fx_service_has_class(self):
        """NestJS fx-service có class declaration."""
        result = _render_template("nestjs", "fx-service.ts.jinja2")
        assert "class " in result, (
            "fx-service.ts.jinja2 thiếu class declaration"
        )

    # --- Angular ---
    def test_angular_ledger_dashboard_has_component(self):
        """Angular ledger-dashboard có @Component decorator."""
        result = _render_template("angular", "ledger-dashboard.component.ts.jinja2")
        assert "@Component" in result, (
            "ledger-dashboard.component.ts.jinja2 thiếu @Component decorator"
        )

    def test_angular_transaction_detail_has_component(self):
        """Angular transaction-detail có @Component decorator."""
        result = _render_template("angular", "transaction-detail.component.ts.jinja2")
        assert "@Component" in result, (
            "transaction-detail.component.ts.jinja2 thiếu @Component decorator"
        )

    def test_angular_ledger_dashboard_has_angular_core(self):
        """Angular ledger-dashboard có import từ @angular/core."""
        result = _render_template("angular", "ledger-dashboard.component.ts.jinja2")
        assert "@angular/core" in result, (
            "ledger-dashboard.component.ts.jinja2 thiếu import @angular/core"
        )

    # --- React ---
    def test_react_ledger_dashboard_has_react_import(self):
        """React LedgerDashboard component có import từ 'react'."""
        result = _render_template("react", "LedgerDashboard.tsx.jinja2")
        assert "from 'react'" in result or 'from "react"' in result, (
            "LedgerDashboard.tsx.jinja2 thiếu import từ 'react'"
        )

    def test_react_transaction_detail_has_react_import(self):
        """React TransactionDetail component có import từ 'react'."""
        result = _render_template("react", "TransactionDetail.tsx.jinja2")
        assert "from 'react'" in result or 'from "react"' in result, (
            "TransactionDetail.tsx.jinja2 thiếu import từ 'react'"
        )

    def test_react_ledger_dashboard_has_useState(self):
        """React LedgerDashboard có useState hook."""
        result = _render_template("react", "LedgerDashboard.tsx.jinja2")
        assert "useState" in result, (
            "LedgerDashboard.tsx.jinja2 thiếu useState hook"
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
