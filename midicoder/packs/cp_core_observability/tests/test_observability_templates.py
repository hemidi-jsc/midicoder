"""
Ki?m tra templates CP15 — Observability Stack Generator.

Test t?t c? templates t?n t?i và có n?i dung h?p l?.
"""

import os
import sys

import pytest

# File lives at: .../midicoder/packs/cp_core_observability/tests/test_observability_templates.py
# 5 levels up = d:\hemidi-labs\midicoder-ce\midicoder
# 6 levels up = d:\hemidi-labs\midicoder-ce (repo root, where midicoder/stacks/... lives)
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
MIDICODER_ROOT = os.path.join(REPO_ROOT, "midicoder")
if MIDICODER_ROOT not in sys.path:
    sys.path.insert(0, MIDICODER_ROOT)


# Ð?nh nghia danh sách templates mong d?i
EXPECTED_TEMPLATES = [
    # FastAPI (2 templates)
    "midicoder/stacks/fastapi/cp_core_observability/observability_service.py.jinja2",
    "midicoder/stacks/fastapi/cp_core_observability/observability_middleware.py.jinja2",
    # NestJS (3 templates)
    "midicoder/stacks/nestjs/cp_core_observability/observability.module.ts.jinja2",
    "midicoder/stacks/nestjs/cp_core_observability/observability.service.ts.jinja2",
    "midicoder/stacks/nestjs/cp_core_observability/observability.interceptor.ts.jinja2",
    # Angular (2 templates)
    "midicoder/stacks/angular/cp_core_observability/logging_service.ts.jinja2",
    "midicoder/stacks/angular/cp_core_observability/log_viewer.component.ts.jinja2",
    # React (3 templates)
    "midicoder/stacks/react/cp_core_observability/types.ts.jinja2",
    "midicoder/stacks/react/cp_core_observability/useLogging.ts.jinja2",
    "midicoder/stacks/react/cp_core_observability/LogViewer.tsx.jinja2",
]


class TestTemplateExistence:
    """Ki?m tra t?t c? templates t?n t?i."""

    @pytest.mark.parametrize("template_path", EXPECTED_TEMPLATES)
    def test_template_file_exists(self, template_path):
        """M?i template file ph?i t?n t?i."""
        full_path = os.path.join(REPO_ROOT, template_path)
        assert os.path.isfile(full_path), f"Template missing: {template_path}"

    def test_total_template_count(self):
        """S? lu?ng templates ph?i d? 10 (2 FastAPI + 3 NestJS + 2 Angular + 3 React)."""
        existing = 0
        for tpl in EXPECTED_TEMPLATES:
            full = os.path.join(REPO_ROOT, tpl)
            if os.path.isfile(full):
                existing += 1
        assert existing == len(EXPECTED_TEMPLATES), f"Ch? có {existing}/{len(EXPECTED_TEMPLATES)} templates t?n t?i"


class TestTemplateContent:
    """Ki?m tra n?i dung templates h?p l?."""

    def _read_template(self, rel_path):
        """Ð?c n?i dung template file."""
        full = os.path.join(REPO_ROOT, rel_path)
        with open(full, "r", encoding="utf-8") as f:
            return f.read()

    def test_fastapi_service_has_observability_class(self):
        """FastAPI service template ph?i có ObservabilityService class."""
        content = self._read_template("midicoder/stacks/fastapi/cp_core_observability/observability_service.py.jinja2")
        assert "ObservabilityService" in content, "Thi?u class ObservabilityService"
        assert "record_metric" in content or "counter" in content or "metric" in content.lower()

    def test_fastapi_middleware_has_middleware_class(self):
        """FastAPI middleware template ph?i có middleware class."""
        content = self._read_template("midicoder/stacks/fastapi/cp_core_observability/observability_middleware.py.jinja2")
        assert "Middleware" in content or "middleware" in content.lower()
        assert "__call__" in content or "request" in content.lower()

    def test_nestjs_module_has_module_decorator(self):
        """NestJS module template ph?i có @Module decorator."""
        content = self._read_template("midicoder/stacks/nestjs/cp_core_observability/observability.module.ts.jinja2")
        assert "@Module" in content, "Thi?u @Module decorator"
        assert "ObservabilityModule" in content or "Module" in content

    def test_nestjs_service_has_injectable(self):
        """NestJS service template ph?i có @Injectable."""
        content = self._read_template("midicoder/stacks/nestjs/cp_core_observability/observability.service.ts.jinja2")
        assert "@Injectable" in content, "Thi?u @Injectable decorator"
        assert "ObservabilityService" in content or "Service" in content

    def test_nestjs_interceptor_has_interceptor(self):
        """NestJS interceptor template ph?i có interceptor."""
        content = self._read_template("midicoder/stacks/nestjs/cp_core_observability/observability.interceptor.ts.jinja2")
        assert "Interceptor" in content or "intercept" in content.lower()
        assert "Observable" in content

    def test_angular_logging_service_has_injectable(self):
        """Angular LoggingService ph?i có @Injectable."""
        content = self._read_template("midicoder/stacks/angular/cp_core_observability/logging_service.ts.jinja2")
        assert "@Injectable" in content, "Thi?u @Injectable decorator"
        assert "LoggingService" in content or "Service" in content

    def test_angular_log_viewer_has_component(self):
        """Angular LogViewer component ph?i có @Component."""
        content = self._read_template("midicoder/stacks/angular/cp_core_observability/log_viewer.component.ts.jinja2")
        assert "@Component" in content, "Thi?u @Component decorator"
        assert "LogViewer" in content or "Component" in content

    def test_templates_not_empty(self):
        """Không có template nào r?ng."""
        for tpl in EXPECTED_TEMPLATES:
            content = self._read_template(tpl)
            assert len(content.strip()) > 0, f"Template r?ng: {tpl}"

    def test_templates_have_content(self):
        """M?i template ph?i có n?i dung th?c (ít nh?t 50 ký t?)."""
        for tpl in EXPECTED_TEMPLATES:
            content = self._read_template(tpl)
            assert len(content.strip()) >= 50, f"Template quá ng?n: {tpl} ({len(content)} ký t?)"


class TestEmittersGenerateCorrectFiles:
    """Ki?m tra emitters generate dúng file paths."""

    def test_fastapi_emitter_files(self):
        """FastAPI emitter ph?i generate dúng 2 file."""
        from midicoder.packs.cp_core_observability.fastapi import FastAPIObservabilityEmitter
        emitter = FastAPIObservabilityEmitter()
        result = emitter.generate()
        assert len(result) >= 2, f"FastAPI emitter ch? generate {len(result)} file"
        assert any("observability_service" in k for k in result.keys()), "Thi?u observability_service"
        assert any("middleware" in k for k in result.keys()), "Thi?u middleware"

    def test_nestjs_emitter_files(self):
        """NestJS emitter ph?i generate dúng 3 file."""
        from midicoder.packs.cp_core_observability.nestjs import NestJSObservabilityEmitter
        emitter = NestJSObservabilityEmitter()
        result = emitter.generate()
        assert len(result) >= 3, f"NestJS emitter ch? generate {len(result)} file"
        assert any("module" in k for k in result.keys()), "Thi?u module"
        assert any("service" in k for k in result.keys()), "Thi?u service"
        assert any("interceptor" in k for k in result.keys()), "Thi?u interceptor"

    def test_angular_emitter_files(self):
        """Angular emitter ph?i generate dúng 2 file."""
        from midicoder.packs.cp_core_observability.angular import AngularObservabilityEmitter
        emitter = AngularObservabilityEmitter()
        result = emitter.generate()
        assert len(result) >= 2, f"Angular emitter ch? generate {len(result)} file"
        assert any("service" in k for k in result.keys()), "Thi?u service"
        assert any("component" in k.lower() or "viewer" in k.lower() for k in result.keys()), "Thi?u component"

    def test_react_emitter_files(self):
        """React emitter ph?i generate dúng 3 file."""
        from midicoder.packs.cp_core_observability.react import ReactObservabilityEmitter
        emitter = ReactObservabilityEmitter()
        result = emitter.generate()
        assert len(result) >= 3, f"React emitter ch? generate {len(result)} file"
        assert any("type" in k.lower() for k in result.keys()), "Thi?u types"
        assert any("useLogging" in k or "hook" in k.lower() for k in result.keys()), "Thi?u hook"
        assert any("viewer" in k.lower() or "Viewer" in k for k in result.keys()), "Thi?u component"


class TestEmitterContentQuality:
    """Ki?m tra ch?t lu?ng n?i dung t? emitters."""

    def test_fastapi_service_has_metric_method(self):
        """FastAPI service ph?i có method ghi metric."""
        from midicoder.packs.cp_core_observability.fastapi import FastAPIObservabilityEmitter
        emitter = FastAPIObservabilityEmitter()
        result = emitter.generate_service()
        code = list(result.values())[0]
        assert "metric" in code.lower() or "counter" in code.lower()

    def test_nestjs_service_has_logging(self):
        """NestJS service ph?i có logging."""
        from midicoder.packs.cp_core_observability.nestjs import NestJSObservabilityEmitter
        emitter = NestJSObservabilityEmitter()
        result = emitter.generate_service()
        code = list(result.values())[0]
        assert "log" in code.lower()

    def test_emitters_return_dicts(self):
        """T?t c? emitters ph?i tr? v? Dict[str, str]."""
        from midicoder.packs.cp_core_observability.fastapi import FastAPIObservabilityEmitter
        from midicoder.packs.cp_core_observability.nestjs import NestJSObservabilityEmitter
        from midicoder.packs.cp_core_observability.angular import AngularObservabilityEmitter
        from midicoder.packs.cp_core_observability.react import ReactObservabilityEmitter

        for emitter_cls in [FastAPIObservabilityEmitter, NestJSObservabilityEmitter,
                            AngularObservabilityEmitter, ReactObservabilityEmitter]:
            emitter = emitter_cls()
            result = emitter.generate()
            assert isinstance(result, dict), f"{emitter_cls.__name__}.generate() ph?i tr? v? dict"
            for k, v in result.items():
                assert isinstance(k, str), f"Key ph?i là string: {k}"
                assert isinstance(v, str), f"Value ph?i là string: {k}"
