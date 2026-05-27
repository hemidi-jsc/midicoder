# coding: utf-8
"""
Tests cho CP38 emitters: FastAPI, NestJS, Angular, React.

Bao gồm:
- __init__ raises MidicoderError khi template dir không tìm thấy
- emit() returns correct number of files
- emit() returns correct paths
- _build_context() returns correct keys
- _template_exists() returns True/False
- Angular _TEMPLATE_MAP has 5 entries
- React _TEMPLATE_MAP has 7 entries
"""

from __future__ import annotations

import pytest
from pathlib import Path

from midicoder.errors import MidicoderError

# Real template directory paths
# tests/ is at: midicoder/packs/cp38_data_etl/tests/
# 4 parents up = midicoder/ (which contains both packs/ and stacks/)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
FASTAPI_TEMPLATE_DIR = PROJECT_ROOT / "stacks" / "fastapi" / "cp38_data_etl"
NESTJS_TEMPLATE_DIR = PROJECT_ROOT / "stacks" / "nestjs" / "cp38_data_etl"
ANGULAR_TEMPLATE_DIR = PROJECT_ROOT / "stacks" / "angular" / "cp38_data_etl"
REACT_TEMPLATE_DIR = PROJECT_ROOT / "stacks" / "react" / "cp38_data_etl"

# stack_dir = parent of template_dir (e.g. stacks/fastapi/)
FASTAPI_STACK_DIR = FASTAPI_TEMPLATE_DIR.parent
NESTJS_STACK_DIR = NESTJS_TEMPLATE_DIR.parent
ANGULAR_STACK_DIR = ANGULAR_TEMPLATE_DIR.parent
REACT_STACK_DIR = REACT_TEMPLATE_DIR.parent


def _make_ir():
    """Tạo ETLIR sample cho testing."""
    from midicoder.packs.cp38_data_etl.models import (
        ImportFormat,
        ImportJob,
        ExportJob,
        ETLJob,
        ETLStep,
        JobStatus,
    )
    from midicoder.packs.cp38_data_etl.parser import ETLIR

    jobs = [ImportJob(job_key="test_import", target_entity="users", format=ImportFormat.CSV)]
    exports = [ExportJob(job_key="test_export", entity="orders", format=ImportFormat.CSV)]
    steps = [
        ETLStep(step_key="ext", step_type="extract", order=0),
        ETLStep(step_key="load", step_type="load", order=1),
    ]
    etl_jobs = [ETLJob(job_key="test_etl", steps=steps)]
    return ETLIR(import_jobs=jobs, export_jobs=exports, etl_jobs=etl_jobs)


# ============================================================================
# Test FastAPIETLEmitter
# ============================================================================


class TestFastAPIETLEmitter:
    """Tests cho FastAPIETLEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        from midicoder.packs.cp38_data_etl.fastapi import FastAPIETLEmitter

        with pytest.raises(MidicoderError):
            FastAPIETLEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        from midicoder.packs.cp38_data_etl.fastapi import FastAPIETLEmitter

        emitter = FastAPIETLEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter is not None

    def test_emit_returns_files(self, tmp_path: Path):
        from midicoder.packs.cp38_data_etl.fastapi import FastAPIETLEmitter

        emitter = FastAPIETLEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        # 11 templates on disk: __init__, import_models, import_schemas, import_service,
        # export_service, etl_service, import_router, export_router, bulk_worker,
        # csv_parser, json_parser
        assert len(files) == 11

    def test_emit_files_have_content(self, tmp_path: Path):
        from midicoder.packs.cp38_data_etl.fastapi import FastAPIETLEmitter

        emitter = FastAPIETLEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert len(f.content) > 0

    def test_emit_returns_correct_paths(self, tmp_path: Path):
        from midicoder.packs.cp38_data_etl.fastapi import FastAPIETLEmitter

        emitter = FastAPIETLEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        paths = [f.path for f in files]
        assert "app/etl/__init__.py" in paths
        assert "app/etl/models/import_models.py" in paths
        assert "app/etl/schemas/import_schemas.py" in paths
        assert "app/etl/services/import_service.py" in paths
        assert "app/etl/services/export_service.py" in paths
        assert "app/etl/services/etl_service.py" in paths
        assert "app/etl/routers/import_router.py" in paths
        assert "app/etl/routers/export_router.py" in paths
        assert "app/etl/workers/bulk_worker.py" in paths
        assert "app/etl/parsers/csv_parser.py" in paths
        assert "app/etl/parsers/json_parser.py" in paths

    def test_build_context_returns_correct_keys(self):
        from midicoder.packs.cp38_data_etl.fastapi import FastAPIETLEmitter

        emitter = FastAPIETLEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert "import_jobs" in ctx
        assert "export_jobs" in ctx
        assert "etl_jobs" in ctx
        assert "import_job_count" in ctx
        assert "export_job_count" in ctx
        assert "etl_job_count" in ctx
        assert "import_formats" in ctx
        assert "job_statuses" in ctx
        assert "transform_types" in ctx
        assert "extract_sources" in ctx
        assert "load_modes" in ctx

    def test_template_exists_true(self):
        from midicoder.packs.cp38_data_etl.fastapi import FastAPIETLEmitter

        emitter = FastAPIETLEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter._template_exists("__init__.py.jinja2") is True

    def test_template_exists_false(self):
        from midicoder.packs.cp38_data_etl.fastapi import FastAPIETLEmitter

        emitter = FastAPIETLEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        assert emitter._template_exists("nonexistent.py.jinja2") is False

    def test_render_raises_on_missing_template(self):
        from midicoder.packs.cp38_data_etl.fastapi import FastAPIETLEmitter

        emitter = FastAPIETLEmitter(stack_dir=str(FASTAPI_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.py.jinja2", {})


# ============================================================================
# Test NestJSETLEmitter
# ============================================================================


class TestNestJSETLEmitter:
    """Tests cho NestJSETLEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        from midicoder.packs.cp38_data_etl.nestjs import NestJSETLEmitter

        with pytest.raises(MidicoderError):
            NestJSETLEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        from midicoder.packs.cp38_data_etl.nestjs import NestJSETLEmitter

        emitter = NestJSETLEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter is not None

    def test_emit_returns_files(self, tmp_path: Path):
        from midicoder.packs.cp38_data_etl.nestjs import NestJSETLEmitter

        emitter = NestJSETLEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        # 9 templates on disk: import.entity, import.dto, import.service,
        # export.service, etl.service, import.controller, export.controller,
        # bulk-processor.service, etl.module
        assert len(files) == 9

    def test_emit_files_have_content(self, tmp_path: Path):
        from midicoder.packs.cp38_data_etl.nestjs import NestJSETLEmitter

        emitter = NestJSETLEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        for f in files:
            assert len(f.content) > 0

    def test_emit_returns_correct_paths(self, tmp_path: Path):
        from midicoder.packs.cp38_data_etl.nestjs import NestJSETLEmitter

        emitter = NestJSETLEmitter(stack_dir=str(NESTJS_STACK_DIR))
        files = emitter.emit(_make_ir(), tmp_path)
        paths = [f.path for f in files]
        assert "src/etl/entities/import.entity.ts" in paths
        assert "src/etl/dtos/import.dto.ts" in paths
        assert "src/etl/services/import.service.ts" in paths
        assert "src/etl/services/export.service.ts" in paths
        assert "src/etl/services/etl.service.ts" in paths
        assert "src/etl/controllers/import.controller.ts" in paths
        assert "src/etl/controllers/export.controller.ts" in paths
        assert "src/etl/services/bulk-processor.service.ts" in paths
        assert "src/etl/etl.module.ts" in paths

    def test_build_context_returns_correct_keys(self):
        from midicoder.packs.cp38_data_etl.nestjs import NestJSETLEmitter

        emitter = NestJSETLEmitter(stack_dir=str(NESTJS_STACK_DIR))
        ctx = emitter._build_context(_make_ir())
        assert "import_jobs" in ctx
        assert "export_jobs" in ctx
        assert "etl_jobs" in ctx
        assert "import_job_count" in ctx
        assert "export_job_count" in ctx
        assert "etl_job_count" in ctx
        assert "import_formats" in ctx
        assert "job_statuses" in ctx
        assert "transform_types" in ctx
        assert "extract_sources" in ctx
        assert "load_modes" in ctx

    def test_template_exists_true(self):
        from midicoder.packs.cp38_data_etl.nestjs import NestJSETLEmitter

        emitter = NestJSETLEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter._template_exists("import.entity.ts.jinja2") is True

    def test_template_exists_false(self):
        from midicoder.packs.cp38_data_etl.nestjs import NestJSETLEmitter

        emitter = NestJSETLEmitter(stack_dir=str(NESTJS_STACK_DIR))
        assert emitter._template_exists("nonexistent.ts.jinja2") is False

    def test_render_raises_on_missing_template(self):
        from midicoder.packs.cp38_data_etl.nestjs import NestJSETLEmitter

        emitter = NestJSETLEmitter(stack_dir=str(NESTJS_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.ts.jinja2", {})


# ============================================================================
# Test AngularETLEmitter
# ============================================================================


class TestAngularETLEmitter:
    """Tests cho AngularETLEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        from midicoder.packs.cp38_data_etl.angular import AngularETLEmitter

        with pytest.raises(MidicoderError):
            AngularETLEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        from midicoder.packs.cp38_data_etl.angular import AngularETLEmitter

        emitter = AngularETLEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter is not None

    def test_emit_raises_on_broken_template(self):
        """import-wizard.component.ts.jinja2 contains JavaScript ternary `? :`
        inside `{{ }}` that conflicts with Jinja2 delimiters, causing
        a TemplateSyntaxError. The emitter wraps this into MidicoderError
        CP38_RENDER_FAILED."""
        from midicoder.packs.cp38_data_etl.angular import AngularETLEmitter

        emitter = AngularETLEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter.emit(_make_ir())

    def test_emit_returns_correct_paths_template_map(self):
        """Verify the _TEMPLATE_MAP output paths are correct."""
        from midicoder.packs.cp38_data_etl.angular import AngularETLEmitter

        expected_paths = {
            "src/app/etl/components/import-wizard.component.ts",
            "src/app/etl/components/export-dialog.component.ts",
            "src/app/etl/services/import.service.ts",
            "src/app/etl/services/export.service.ts",
            "src/app/etl/components/job-status.component.ts",
        }
        actual_paths = set(AngularETLEmitter._TEMPLATE_MAP.values())
        assert actual_paths == expected_paths

    def test_emit_with_extra_context(self):
        from midicoder.packs.cp38_data_etl.angular import AngularETLEmitter

        emitter = AngularETLEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        # emit() will still fail due to broken template, but with extra context
        with pytest.raises(MidicoderError):
            emitter.emit(_make_ir(), context={"ui_framework": "angular"})

    def test_template_map_has_5_entries(self):
        from midicoder.packs.cp38_data_etl.angular import AngularETLEmitter

        assert len(AngularETLEmitter._TEMPLATE_MAP) == 5

    def test_template_exists_true(self):
        from midicoder.packs.cp38_data_etl.angular import AngularETLEmitter

        emitter = AngularETLEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter._template_exists("import-wizard.component.ts.jinja2") is True

    def test_template_exists_false(self):
        from midicoder.packs.cp38_data_etl.angular import AngularETLEmitter

        emitter = AngularETLEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        assert emitter._template_exists("nonexistent.ts.jinja2") is False

    def test_render_raises_on_missing_template(self):
        from midicoder.packs.cp38_data_etl.angular import AngularETLEmitter

        emitter = AngularETLEmitter(stack_dir=str(ANGULAR_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.ts.jinja2", {})


# ============================================================================
# Test ReactETLEmitter
# ============================================================================


class TestReactETLEmitter:
    """Tests cho ReactETLEmitter."""

    def test_init_raises_error_when_template_dir_not_found(self):
        from midicoder.packs.cp38_data_etl.react import ReactETLEmitter

        with pytest.raises(MidicoderError):
            ReactETLEmitter(stack_dir="/nonexistent/path/to/core")

    def test_init_succeeds_with_real_template_dir(self):
        from midicoder.packs.cp38_data_etl.react import ReactETLEmitter

        emitter = ReactETLEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter is not None

    def test_emit_raises_on_broken_template(self):
        """ImportWizard.tsx.jinja2 contains unescaped JSX {{ }} that
        conflicts with Jinja2 delimiters, causing a TemplateSyntaxError.
        The emitter wraps this into MidicoderError CP38_RENDER_FAILED."""
        from midicoder.packs.cp38_data_etl.react import ReactETLEmitter

        emitter = ReactETLEmitter(stack_dir=str(REACT_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter.emit(_make_ir())

    def test_emit_returns_correct_paths_template_map(self):
        """Verify the _TEMPLATE_MAP output paths are correct."""
        from midicoder.packs.cp38_data_etl.react import ReactETLEmitter

        expected_paths = {
            "src/etl/components/ImportWizard.tsx",
            "src/etl/components/ExportDialog.tsx",
            "src/etl/hooks/useImportJob.ts",
            "src/etl/hooks/useExportJob.ts",
            "src/etl/components/JobStatusPanel.tsx",
            "src/etl/services/import.service.ts",
            "src/etl/services/export.service.ts",
        }
        actual_paths = set(ReactETLEmitter._TEMPLATE_MAP.values())
        assert actual_paths == expected_paths

    def test_emit_with_extra_context(self):
        from midicoder.packs.cp38_data_etl.react import ReactETLEmitter

        emitter = ReactETLEmitter(stack_dir=str(REACT_STACK_DIR))
        # emit() will still fail due to broken template, but with extra context
        with pytest.raises(MidicoderError):
            emitter.emit(_make_ir(), context={"ui_framework": "react"})

    def test_template_map_has_7_entries(self):
        from midicoder.packs.cp38_data_etl.react import ReactETLEmitter

        assert len(ReactETLEmitter._TEMPLATE_MAP) == 7

    def test_template_exists_true(self):
        from midicoder.packs.cp38_data_etl.react import ReactETLEmitter

        emitter = ReactETLEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter._template_exists("ImportWizard.tsx.jinja2") is True

    def test_template_exists_false(self):
        from midicoder.packs.cp38_data_etl.react import ReactETLEmitter

        emitter = ReactETLEmitter(stack_dir=str(REACT_STACK_DIR))
        assert emitter._template_exists("nonexistent.tsx.jinja2") is False

    def test_render_raises_on_missing_template(self):
        from midicoder.packs.cp38_data_etl.react import ReactETLEmitter

        emitter = ReactETLEmitter(stack_dir=str(REACT_STACK_DIR))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.tsx.jinja2", {})
