"""
Kiểm tra templates CP15 — Observability Stack Generator.

Test tất cả templates tồn tại và có nội dung hợp lệ.
"""

import os
import sys

import pytest

# Repo root: d:\hemidi-labs\midicoder-ce (4 levels up from this file)
# Package root: d:\hemidi-labs\midicoder-ce\midicoder (3 levels up, for imports)
PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO_ROOT = os.path.dirname(PACKAGE_ROOT)
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)


# Định nghĩa danh sách templates mong đợi
EXPECTED_TEMPLATES = [
    # FastAPI (2 templates)
    "midicoder/stacks/fastapi/core/observability/observability_service.py.jinja2",
    "midicoder/stacks/fastapi/core/observability/observability_middleware.py.jinja2",
    # NestJS (3 templates)
    "midicoder/stacks/nestjs/core/observability/observability.module.ts.jinja2",
    "midicoder/stacks/nestjs/core/observability/observability.service.ts.jinja2",
    "midicoder/stacks/nestjs/core/observability/observability.interceptor.ts.jinja2",
    # Angular (2 templates)
    "midicoder/stacks/angular/core/observability/logging_service.ts.jinja2",
    "midicoder/stacks/angular/core/observability/log_viewer.component.ts.jinja2",
    # React (3 templates)
    "midicoder/stacks/react/core/observability/types.ts.jinja2",
    "midicoder/stacks/react/core/observability/useLogging.ts.jinja2",
    "midicoder/stacks/react/core/observability/LogViewer.tsx.jinja2",
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

    def test_fastapi_service_has_observability_class(self):
        """FastAPI service template phải có ObservabilityService class."""
        content = self._read_template("midicoder/stacks/fastapi/core/observability/observability_service.py.jinja2")
        assert "ObservabilityService" in content, "Thiếu class ObservabilityService"
        assert "record_metric" in content or "counter" in content or "metric" in content.lower()

    def test_fastapi_middleware_has_middleware_class(self):
        """FastAPI middleware template phải có middleware class."""
        content = self._read_template("midicoder/stacks/fastapi/core/observability/observability_middleware.py.jinja2")
        assert "Middleware" in content or "middleware" in content.lower()
        assert "__call__" in content or "request" in content.lower()

    def test_nestjs_module_has_module_decorator(self):
        """NestJS module template phải có @Module decorator."""
        content = self._read_template("midicoder/stacks/nestjs/core/observability/observability.module.ts.jinja2")
        assert "@Module" in content, "Thiếu @Module decorator"
        assert "ObservabilityModule" in content or "Module" in content

    def test_nestjs_service_has_injectable(self):
        """NestJS service template phải có @Injectable."""
        content = self._read_template("midicoder/stacks/nestjs/core/observability/observability.service.ts.jinja2")
        assert "@Injectable" in content, "Thiếu @Injectable decorator"
        assert "ObservabilityService" in content or "Service" in content

    def test_nestjs_interceptor_has_interceptor(self):
        """NestJS interceptor template phải có interceptor."""
        content = self._read_template("midicoder/stacks/nestjs/core/observability/observability.interceptor.ts.jinja2")
        assert "Interceptor" in content or "intercept" in content.lower()
        assert "Observable" in content

    def test_angular_logging_service_has_injectable(self):
        """Angular LoggingService phải có @Injectable."""
        content = self._read_template("midicoder/stacks/angular/core/observability/logging_service.ts.jinja2")
        assert "@Injectable" in content, "Thiếu @Injectable decorator"
        assert "LoggingService" in content or "Service" in content

    def test_angular_log_viewer_has_component(self):
        """Angular LogViewer component phải có @Component."""
        content = self._read_template("midicoder/stacks/angular/core/observability/log_viewer.component.ts.jinja2")
        assert "@Component" in content, "Thiếu @Component decorator"
        assert "LogViewer" in content or "Component" in content

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
        from midicoder.emitters.core.cp15_observability.fastapi import FastAPIObservabilityEmitter
        emitter = FastAPIObservabilityEmitter()
        result = emitter.generate()
        assert len(result) >= 2, f"FastAPI emitter chỉ generate {len(result)} file"
        assert any("observability_service" in k for k in result.keys()), "Thiếu observability_service"
        assert any("middleware" in k for k in result.keys()), "Thiếu middleware"

    def test_nestjs_emitter_files(self):
        """NestJS emitter phải generate đúng 3 file."""
        from midicoder.emitters.core.cp15_observability.nestjs import NestJSObservabilityEmitter
        emitter = NestJSObservabilityEmitter()
        result = emitter.generate()
        assert len(result) >= 3, f"NestJS emitter chỉ generate {len(result)} file"
        assert any("module" in k for k in result.keys()), "Thiếu module"
        assert any("service" in k for k in result.keys()), "Thiếu service"
        assert any("interceptor" in k for k in result.keys()), "Thiếu interceptor"

    def test_angular_emitter_files(self):
        """Angular emitter phải generate đúng 2 file."""
        from midicoder.emitters.core.cp15_observability.angular import AngularObservabilityEmitter
        emitter = AngularObservabilityEmitter()
        result = emitter.generate()
        assert len(result) >= 2, f"Angular emitter chỉ generate {len(result)} file"
        assert any("service" in k for k in result.keys()), "Thiếu service"
        assert any("component" in k.lower() or "viewer" in k.lower() for k in result.keys()), "Thiếu component"

    def test_react_emitter_files(self):
        """React emitter phải generate đúng 3 file."""
        from midicoder.emitters.core.cp15_observability.react import ReactObservabilityEmitter
        emitter = ReactObservabilityEmitter()
        result = emitter.generate()
        assert len(result) >= 3, f"React emitter chỉ generate {len(result)} file"
        assert any("type" in k.lower() for k in result.keys()), "Thiếu types"
        assert any("useLogging" in k or "hook" in k.lower() for k in result.keys()), "Thiếu hook"
        assert any("viewer" in k.lower() or "Viewer" in k for k in result.keys()), "Thiếu component"


class TestEmitterContentQuality:
    """Kiểm tra chất lượng nội dung từ emitters."""

    def test_fastapi_service_has_metric_method(self):
        """FastAPI service phải có method ghi metric."""
        from midicoder.emitters.core.cp15_observability.fastapi import FastAPIObservabilityEmitter
        emitter = FastAPIObservabilityEmitter()
        result = emitter.generate_service()
        code = list(result.values())[0]
        assert "metric" in code.lower() or "counter" in code.lower()

    def test_nestjs_service_has_logging(self):
        """NestJS service phải có logging."""
        from midicoder.emitters.core.cp15_observability.nestjs import NestJSObservabilityEmitter
        emitter = NestJSObservabilityEmitter()
        result = emitter.generate_service()
        code = list(result.values())[0]
        assert "log" in code.lower()

    def test_emitters_return_dicts(self):
        """Tất cả emitters phải trả về Dict[str, str]."""
        from midicoder.emitters.core.cp15_observability.fastapi import FastAPIObservabilityEmitter
        from midicoder.emitters.core.cp15_observability.nestjs import NestJSObservabilityEmitter
        from midicoder.emitters.core.cp15_observability.angular import AngularObservabilityEmitter
        from midicoder.emitters.core.cp15_observability.react import ReactObservabilityEmitter

        for emitter_cls in [FastAPIObservabilityEmitter, NestJSObservabilityEmitter,
                            AngularObservabilityEmitter, ReactObservabilityEmitter]:
            emitter = emitter_cls()
            result = emitter.generate()
            assert isinstance(result, dict), f"{emitter_cls.__name__}.generate() phải trả về dict"
            for k, v in result.items():
                assert isinstance(k, str), f"Key phải là string: {k}"
                assert isinstance(v, str), f"Value phải là string: {k}"
