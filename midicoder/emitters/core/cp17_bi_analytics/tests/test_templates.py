"""
Kiểm tra templates CP17 — Analytics Stack Generator.

Test tất cả templates tồn tại và có nội dung hợp lệ.
"""

import os
import sys
from pathlib import Path

import pytest
import jinja2

# Paths relative to this file (tests/ dir):
# test_templates.py → tests/ → cp17_bi_analytics/ → core/ → emitters/ → midicoder/ → midicoder-ce/
_ROOT = Path(__file__).resolve()
# 5 up: midicoder/ (for sys.path / imports)
_PACKAGE_ROOT = str(_ROOT.parent.parent.parent.parent.parent)
# 6 up: midicoder-ce/ (repo root — template paths start with "midicoder/...")
REPO_ROOT = str(_ROOT.parent.parent.parent.parent.parent.parent)
if _PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, _PACKAGE_ROOT)


# Định nghĩa danh sách templates mong đợi
EXPECTED_TEMPLATES = [
    # FastAPI (2 templates)
    "midicoder/stacks/fastapi/core/cp17_bi_analytics/analytics_service.py.jinja2",
    "midicoder/stacks/fastapi/core/cp17_bi_analytics/analytics_router.py.jinja2",
    # NestJS (3 templates)
    "midicoder/stacks/nestjs/core/cp17_bi_analytics/analytics.module.ts.jinja2",
    "midicoder/stacks/nestjs/core/cp17_bi_analytics/analytics.service.ts.jinja2",
    "midicoder/stacks/nestjs/core/cp17_bi_analytics/analytics.controller.ts.jinja2",
    # Angular (2 templates)
    "midicoder/stacks/angular/core/cp17_bi_analytics/analytics_widget.component.ts.jinja2",
    "midicoder/stacks/angular/core/cp17_bi_analytics/report_viewer.component.ts.jinja2",
    # React (3 templates)
    "midicoder/stacks/react/core/cp17_bi_analytics/types.ts.jinja2",
    "midicoder/stacks/react/core/cp17_bi_analytics/AnalyticsChart.tsx.jinja2",
    "midicoder/stacks/react/core/cp17_bi_analytics/ReportTable.tsx.jinja2",
]


class TestTemplateExistence:
    """Kiểm tra tất cả templates tồn tại."""

    @pytest.mark.parametrize("template_path", EXPECTED_TEMPLATES)
    def test_template_file_exists(self, template_path):
        """Mỗi template file phải tồn tại."""
        full_path = os.path.join(REPO_ROOT, template_path)
        assert os.path.isfile(full_path), f"Template missing: {template_path}"

    def test_total_template_count(self):
        """Số lượng templates phải đủ 10 (2 FastAPI + 3 NestJS + 2 Angular + 3 React)."""
        existing = 0
        for tpl in EXPECTED_TEMPLATES:
            full = os.path.join(REPO_ROOT, tpl)
            if os.path.isfile(full):
                existing += 1
        assert existing == len(EXPECTED_TEMPLATES), f"Chỉ có {existing}/{len(EXPECTED_TEMPLATES)} templates tồn tại"


class TestTemplateContent:
    """Kiểm tra nội dung templates hợp lệ."""

    def _read_template(self, rel_path):
        """Đọc nội dung template file."""
        full = os.path.join(REPO_ROOT, rel_path)
        with open(full, "r", encoding="utf-8") as f:
            return f.read()

    # --- FastAPI ---

    def test_fastapi_service_has_analytics_class(self):
        """FastAPI service template phải có AnalyticsService class."""
        content = self._read_template("midicoder/stacks/fastapi/core/cp17_bi_analytics/analytics_service.py.jinja2")
        assert len(content) > 10, "Template quá ngắn hoặc rỗng"
        assert "AnalyticsService" in content, "Thiếu class AnalyticsService"
        assert "def " in content, "Thiếu method definition"
        assert "class " in content, "Thiếu class definition"

    def test_fastapi_router_has_router(self):
        """FastAPI router template phải có APIRouter và route handlers."""
        content = self._read_template("midicoder/stacks/fastapi/core/cp17_bi_analytics/analytics_router.py.jinja2")
        assert len(content) > 10, "Template quá ngắn hoặc rỗng"
        assert "APIRouter" in content, "Thiếu APIRouter"
        assert "router" in content, "Thiếu router variable"
        assert "def " in content, "Thiếu route handler"

    # --- NestJS ---

    def test_nestjs_module_has_module_decorator(self):
        """NestJS module template phải có @Module và @Global decorator."""
        content = self._read_template("midicoder/stacks/nestjs/core/cp17_bi_analytics/analytics.module.ts.jinja2")
        assert len(content) > 10, "Template quá ngắn hoặc rỗng"
        assert "@Module" in content, "Thiếu @Module decorator"
        assert "AnalyticsModule" in content, "Thiếu AnalyticsModule class"
        assert "@Global" in content, "Thiếu @Global decorator"

    def test_nestjs_service_has_injectable(self):
        """NestJS service template phải có @Injectable."""
        content = self._read_template("midicoder/stacks/nestjs/core/cp17_bi_analytics/analytics.service.ts.jinja2")
        assert len(content) > 10, "Template quá ngắn hoặc rỗng"
        assert "@Injectable" in content, "Thiếu @Injectable decorator"
        assert "AnalyticsService" in content, "Thiếu AnalyticsService class"

    def test_nestjs_controller_has_controller_decorator(self):
        """NestJS controller template phải có @Controller."""
        content = self._read_template("midicoder/stacks/nestjs/core/cp17_bi_analytics/analytics.controller.ts.jinja2")
        assert len(content) > 10, "Template quá ngắn hoặc rỗng"
        assert "@Controller" in content, "Thiếu @Controller decorator"
        assert "AnalyticsController" in content, "Thiếu AnalyticsController class"

    # --- Angular ---

    def test_angular_widget_has_component(self):
        """Angular AnalyticsWidgetComponent phải có @Component."""
        content = self._read_template("midicoder/stacks/angular/core/cp17_bi_analytics/analytics_widget.component.ts.jinja2")
        assert len(content) > 10, "Template quá ngắn hoặc rỗng"
        assert "@Component" in content, "Thiếu @Component decorator"
        assert "AnalyticsWidgetComponent" in content or "analytics-widget" in content, "Thiếu component identifier"

    def test_angular_report_viewer_has_component(self):
        """Angular ReportViewerComponent phải có @Component."""
        content = self._read_template("midicoder/stacks/angular/core/cp17_bi_analytics/report_viewer.component.ts.jinja2")
        assert len(content) > 10, "Template quá ngắn hoặc rỗng"
        assert "@Component" in content, "Thiếu @Component decorator"
        assert "ReportViewerComponent" in content or "report-viewer" in content, "Thiếu component identifier"

    # --- React ---

    def test_react_types_has_interfaces(self):
        """React types template phải có exported interfaces."""
        content = self._read_template("midicoder/stacks/react/core/cp17_bi_analytics/types.ts.jinja2")
        assert len(content) > 10, "Template quá ngắn hoặc rỗng"
        assert "interface" in content, "Thiếu interface declaration"
        assert "export" in content, "Thiếu export statement"

    def test_react_chart_has_component(self):
        """React AnalyticsChart phải có exported React.FC component."""
        content = self._read_template("midicoder/stacks/react/core/cp17_bi_analytics/AnalyticsChart.tsx.jinja2")
        assert len(content) > 10, "Template quá ngắn hoặc rỗng"
        assert "AnalyticsChart" in content, "Thiếu AnalyticsChart component"
        assert "function" in content or "React.FC" in content or "=> {" in content, "Thiếu function component declaration"
        assert "export" in content, "Thiếu export statement"

    def test_react_table_has_component(self):
        """React ReportTable phải có exported React.FC component."""
        content = self._read_template("midicoder/stacks/react/core/cp17_bi_analytics/ReportTable.tsx.jinja2")
        assert len(content) > 10, "Template quá ngắn hoặc rỗng"
        assert "ReportTable" in content, "Thiếu ReportTable component"
        assert "function" in content or "React.FC" in content or "=> {" in content, "Thiếu function component declaration"
        assert "export" in content, "Thiếu export statement"

    # --- General ---

    def test_templates_not_empty(self):
        """Không có template nào rỗng."""
        for tpl in EXPECTED_TEMPLATES:
            content = self._read_template(tpl)
            assert len(content.strip()) > 0, f"Template rỗng: {tpl}"

    def test_templates_have_content(self):
        """Mỗi template phải có nội dung thực (ít nhất 50 ký tự)."""
        for tpl in EXPECTED_TEMPLATES:
            content = self._read_template(tpl)
            assert len(content.strip()) >= 50, f"Template quá ngắn: {tpl} ({len(content)} ký tự)"


class TestEmittersGenerateCorrectFiles:
    """Kiểm tra emitters generate đúng file paths."""

    def test_fastapi_emitter_files(self):
        """FastAPI emitter phải generate đúng 2 file."""
        from midicoder.emitters.core.cp17_bi_analytics.fastapi import FastAPIAnalyticsEmitter
        emitter = FastAPIAnalyticsEmitter()
        result = emitter.generate()
        assert len(result) >= 2, f"FastAPI emitter chỉ generate {len(result)} file"
        assert any("analytics_service" in k for k in result.keys()), "Thiếu analytics_service"
        assert any("router" in k for k in result.keys()), "Thiếu router"

    def test_nestjs_emitter_files(self):
        """NestJS emitter phải generate đúng 3 file."""
        from midicoder.emitters.core.cp17_bi_analytics.nestjs import NestJSAnalyticsEmitter
        emitter = NestJSAnalyticsEmitter()
        result = emitter.generate()
        assert len(result) >= 3, f"NestJS emitter chỉ generate {len(result)} file"
        assert any("module" in k for k in result.keys()), "Thiếu module"
        assert any("service" in k for k in result.keys()), "Thiếu service"
        assert any("controller" in k for k in result.keys()), "Thiếu controller"

    def test_angular_emitter_files(self):
        """Angular emitter phải generate đúng 2 file."""
        from midicoder.emitters.core.cp17_bi_analytics.angular import AngularAnalyticsEmitter
        emitter = AngularAnalyticsEmitter()
        result = emitter.generate()
        assert len(result) >= 2, f"Angular emitter chỉ generate {len(result)} file"
        assert any("widget" in k.lower() or "analytics_widget" in k for k in result.keys()), "Thiếu widget"
        assert any("report" in k.lower() or "viewer" in k.lower() for k in result.keys()), "Thiếu report viewer"

    def test_react_emitter_files(self):
        """React emitter phải generate đúng 3 file."""
        from midicoder.emitters.core.cp17_bi_analytics.react import ReactAnalyticsEmitter
        emitter = ReactAnalyticsEmitter()
        result = emitter.generate()
        assert len(result) >= 3, f"React emitter chỉ generate {len(result)} file"
        assert any("type" in k.lower() for k in result.keys()), "Thiếu types"
        assert any("chart" in k.lower() or "Chart" in k for k in result.keys()), "Thiếu chart"
        assert any("table" in k.lower() or "Table" in k for k in result.keys()), "Thiếu table"


class TestEmitterContentQuality:
    """Kiểm tra chất lượng nội dung từ emitters."""

    def test_fastapi_service_has_analytics_method(self):
        """FastAPI service phải có method analytics."""
        from midicoder.emitters.core.cp17_bi_analytics.fastapi import FastAPIAnalyticsEmitter
        emitter = FastAPIAnalyticsEmitter()
        result = emitter.generate_service()
        code = list(result.values())[0]
        assert "AnalyticsService" in code or "analytics" in code.lower()

    def test_nestjs_service_has_analytics(self):
        """NestJS service phải có analytics service content."""
        from midicoder.emitters.core.cp17_bi_analytics.nestjs import NestJSAnalyticsEmitter
        emitter = NestJSAnalyticsEmitter()
        result = emitter.generate_service()
        code = list(result.values())[0]
        assert "AnalyticsService" in code or "analytics" in code.lower()

    def test_emitters_return_dicts(self):
        """Tất cả emitters phải trả về Dict[str, str]."""
        from midicoder.emitters.core.cp17_bi_analytics.fastapi import FastAPIAnalyticsEmitter
        from midicoder.emitters.core.cp17_bi_analytics.nestjs import NestJSAnalyticsEmitter
        from midicoder.emitters.core.cp17_bi_analytics.angular import AngularAnalyticsEmitter
        from midicoder.emitters.core.cp17_bi_analytics.react import ReactAnalyticsEmitter

        for emitter_cls in [FastAPIAnalyticsEmitter, NestJSAnalyticsEmitter,
                            AngularAnalyticsEmitter, ReactAnalyticsEmitter]:
            emitter = emitter_cls()
            result = emitter.generate()
            assert isinstance(result, dict), f"{emitter_cls.__name__}.generate() phải trả về dict"
            for k, v in result.items():
                assert isinstance(k, str), f"Key phải là string: {k}"
                assert isinstance(v, str), f"Value phải là string: {k}"

# ===========================================================================
# Dữ liệu và helper cho Rule V1/V2 (P2-17)
# ===========================================================================

_STACKS_DIR = Path(__file__).resolve().parents[4] / "stacks"

FASTAPI_TEMPLATES = [
    "analytics_service.py.jinja2",
    "analytics_router.py.jinja2",
]

NESTJS_TEMPLATES = [
    "analytics.module.ts.jinja2",
    "analytics.service.ts.jinja2",
    "analytics.controller.ts.jinja2",
]

ANGULAR_TEMPLATES = [
    "analytics_widget.component.ts.jinja2",
    "report_viewer.component.ts.jinja2",
]

REACT_TEMPLATES = [
    "types.ts.jinja2",
    "AnalyticsChart.tsx.jinja2",
    "ReportTable.tsx.jinja2",
]


def _render_template(stack: str, template_name: str) -> str:
    """Render template với context cơ bản; fallback đọc raw nếu render lỗi."""
    template_path = _STACKS_DIR / stack / "core" / "cp17_bi_analytics"
    try:
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_path)),
            undefined=jinja2.ChainableUndefined,
        )
        template = env.get_template(template_name)
        return template.render()
    except Exception:
        # Fallback: đọc nội dung raw nếu Jinja2 parse lỗi (JS/Angular syntax conflict)
        raw_file = template_path / template_name
        if raw_file.exists():
            return raw_file.read_text(encoding="utf-8")
        raise


# ===========================================================================
# Test Rule V1 & V2 (P2-17)
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
