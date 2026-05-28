# coding: utf-8
"""
Tích hợp test cho CP13 — Background Job & Workflow Generator.

Test coverage cho:
- Template rendering (Jinja2 raw path) qua Emitter cho Angular, React, FastAPI, NestJS
- FileContributionsLoader tích hợp với CP13 — stack-aware loading và infrastructure
- Template Rules V1/V2 compliance verification

CP13: Background Job & Workflow Generator
"""

import pytest
from pathlib import Path
from midicoder.pipeline.emitter import Emitter
from midicoder.pipeline.file_contributions_loader import FileContributionsLoader


# ============================================================================
# Angular Template Rendering
# ============================================================================


class TestAngularTemplateRendering:
    """Kiểm tra rendering templates Angular CP13 thông qua Emitter."""

    def test_workflow_service_ts_renders_without_errors(self):
        """Template workflow.service.ts.jinja2 phải render thành công."""
        emitter = Emitter(stack="angular")
        content = emitter.render("cp_full_workflow_scheduler/workflow.service.ts.jinja2", {})
        assert isinstance(content, str)
        assert len(content) > 0

    def test_job_status_component_ts_renders_without_errors(self):
        """Template job-status.component.ts.jinja2 phải render thành công."""
        emitter = Emitter(stack="angular")
        content = emitter.render("cp_full_workflow_scheduler/job-status.component.ts.jinja2", {})
        assert isinstance(content, str)
        assert len(content) > 0


# ============================================================================
# React Template Rendering
# ============================================================================


class TestReactTemplateRendering:
    """Kiểm tra rendering templates React CP13 thông qua Emitter."""

    def test_workflow_context_tsx_renders_without_errors(self):
        """Template WorkflowContext.tsx.jinja2 phải render thành công."""
        emitter = Emitter(stack="react")
        content = emitter.render("cp_full_workflow_scheduler/WorkflowContext.tsx.jinja2", {})
        assert isinstance(content, str)
        assert len(content) > 0

    def test_use_workflow_ts_renders_without_errors(self):
        """Template useWorkflow.ts.jinja2 phải render thành công."""
        emitter = Emitter(stack="react")
        content = emitter.render("cp_full_workflow_scheduler/useWorkflow.ts.jinja2", {})
        assert isinstance(content, str)
        assert len(content) > 0

    def test_use_job_status_ts_renders_without_errors(self):
        """Template useJobStatus.ts.jinja2 (NEW) phải render thành công."""
        emitter = Emitter(stack="react")
        content = emitter.render("cp_full_workflow_scheduler/useJobStatus.ts.jinja2", {})
        assert isinstance(content, str)
        assert len(content) > 0

    def test_types_ts_renders_without_errors(self):
        """Template types.ts.jinja2 phải render thành công."""
        emitter = Emitter(stack="react")
        content = emitter.render("cp_full_workflow_scheduler/types.ts.jinja2", {})
        assert isinstance(content, str)
        assert len(content) > 0


# ============================================================================
# FastAPI Template Rendering
# ============================================================================


class TestFastAPITemplateRendering:
    """Kiểm tra rendering templates FastAPI CP13 thông qua Emitter."""

    def test_celery_app_py_renders_without_errors(self):
        """Template celery_app.py.jinja2 phải render thành công."""
        emitter = Emitter(stack="fastapi")
        content = emitter.render("cp_full_workflow_scheduler/celery_app.py.jinja2", {})
        assert isinstance(content, str)
        assert len(content) > 0

    def test_job_scheduler_py_renders_without_errors(self):
        """Template job_scheduler.py.jinja2 phải render thành công."""
        emitter = Emitter(stack="fastapi")
        content = emitter.render("cp_full_workflow_scheduler/job_scheduler.py.jinja2", {})
        assert isinstance(content, str)
        assert len(content) > 0

    def test_tasks_py_renders_without_errors(self):
        """Template tasks.py.jinja2 phải render thành công."""
        emitter = Emitter(stack="fastapi")
        content = emitter.render("cp_full_workflow_scheduler/tasks.py.jinja2", {})
        assert isinstance(content, str)
        assert len(content) > 0

    def test_workflow_service_py_renders_without_errors(self):
        """Template workflow_service.py.jinja2 phải render thành công."""
        emitter = Emitter(stack="fastapi")
        content = emitter.render("cp_full_workflow_scheduler/workflow_service.py.jinja2", {})
        assert isinstance(content, str)
        assert len(content) > 0

    def test_workflow_router_py_renders_without_errors(self):
        """Template workflow_router.py.jinja2 (NEW) phải render thành công."""
        emitter = Emitter(stack="fastapi")
        content = emitter.render("cp_full_workflow_scheduler/workflow_router.py.jinja2", {})
        assert isinstance(content, str)
        assert len(content) > 0


# ============================================================================
# NestJS Template Rendering
# ============================================================================


class TestNestJSTemplateRendering:
    """Kiểm tra rendering templates NestJS CP13 thông qua Emitter."""

    def test_queue_module_ts_renders_without_errors(self):
        """Template queue.module.ts.jinja2 phải render thành công."""
        emitter = Emitter(stack="nestjs")
        content = emitter.render("cp_full_workflow_scheduler/queue.module.ts.jinja2", {})
        assert isinstance(content, str)
        assert len(content) > 0

    def test_job_scheduler_ts_renders_without_errors(self):
        """Template job.scheduler.ts.jinja2 phải render thành công."""
        emitter = Emitter(stack="nestjs")
        content = emitter.render("cp_full_workflow_scheduler/job.scheduler.ts.jinja2", {})
        assert isinstance(content, str)
        assert len(content) > 0

    def test_worker_service_ts_renders_without_errors(self):
        """Template worker.service.ts.jinja2 phải render thành công."""
        emitter = Emitter(stack="nestjs")
        content = emitter.render("cp_full_workflow_scheduler/worker.service.ts.jinja2", {})
        assert isinstance(content, str)
        assert len(content) > 0

    def test_workflow_service_ts_renders_without_errors(self):
        """Template workflow.service.ts.jinja2 phải render thành công."""
        emitter = Emitter(stack="nestjs")
        content = emitter.render("cp_full_workflow_scheduler/workflow.service.ts.jinja2", {})
        assert isinstance(content, str)
        assert len(content) > 0

    def test_workflow_controller_ts_renders_without_errors(self):
        """Template workflow.controller.ts.jinja2 (NEW) phải render thành công."""
        emitter = Emitter(stack="nestjs")
        content = emitter.render("cp_full_workflow_scheduler/workflow.controller.ts.jinja2", {})
        assert isinstance(content, str)
        assert len(content) > 0


# ============================================================================
# FileContributionsLoader Integration
# ============================================================================


class TestFileContributionsLoader:
    """Kiểm tra FileContributionsLoader tích hợp với CP13."""

    def test_load_cp13_returns_non_empty_contributions(self):
        """Load CP13 phải trả về contributions không rỗng."""
        loader = FileContributionsLoader()
        fc = loader.load(pack_internal_id="cp_full_workflow_scheduler", pack_id="CP13")
        assert not fc.is_empty
        assert len(fc.infrastructure) > 0

    def test_load_with_fastapi_stack_returns_fastapi_files_only(self):
        """Load CP13 với stack=fastapi chỉ trả về file FastAPI."""
        loader = FileContributionsLoader()
        fc = loader.load(pack_internal_id="cp_full_workflow_scheduler", pack_id="CP13", stack="fastapi")
        assert not fc.is_empty
        for entry in fc.infrastructure:
            assert "fastapi" in entry.stacks, f"Entry {entry.path} không thuộc stack fastapi"

    def test_load_with_nestjs_stack_returns_nestjs_files_only(self):
        """Load CP13 với stack=nestjs chỉ trả về file NestJS."""
        loader = FileContributionsLoader()
        fc = loader.load(pack_internal_id="cp_full_workflow_scheduler", pack_id="CP13", stack="nestjs")
        assert not fc.is_empty
        for entry in fc.infrastructure:
            assert "nestjs" in entry.stacks, f"Entry {entry.path} không thuộc stack nestjs"

    def test_load_with_angular_stack_returns_angular_files_only(self):
        """Load CP13 với stack=angular chỉ trả về file Angular."""
        loader = FileContributionsLoader()
        fc = loader.load(pack_internal_id="cp_full_workflow_scheduler", pack_id="CP13", stack="angular")
        assert not fc.is_empty
        for entry in fc.infrastructure:
            assert "angular" in entry.stacks, f"Entry {entry.path} không thuộc stack angular"

    def test_load_with_react_stack_returns_react_files_only(self):
        """Load CP13 với stack=react chỉ trả về file React."""
        loader = FileContributionsLoader()
        fc = loader.load(pack_internal_id="cp_full_workflow_scheduler", pack_id="CP13", stack="react")
        assert not fc.is_empty
        for entry in fc.infrastructure:
            assert "react" in entry.stacks, f"Entry {entry.path} không thuộc stack react"

    def test_infrastructure_files_exist(self):
        """CP13 phải có các file infrastructure được khai báo."""
        loader = FileContributionsLoader()
        fc = loader.load(pack_internal_id="cp_full_workflow_scheduler", pack_id="CP13")
        paths = [entry.path for entry in fc.infrastructure]
        # FastAPI infrastructure
        assert any("celery_app" in p for p in paths), "Thiếu celery_app.py"
        assert any("job_scheduler" in p for p in paths), "Thiếu job_scheduler.py"
        assert any("tasks" in p for p in paths), "Thiếu tasks.py"
        assert any("workflow_service" in p for p in paths), "Thiếu workflow_service.py"

    def test_resolve_all_infrastructure_includes_cp13_files(self):
        """resolve_all_infrastructure('fastapi') phải bao gồm file CP13."""
        loader = FileContributionsLoader()
        files = loader.resolve_all_infrastructure("fastapi")
        cp13_paths = [f["path"] for f in files if "workflow" in f["path"] or "celery" in f["path"]]
        assert len(cp13_paths) > 0, "Không có file CP13 trong infrastructure FastAPI"

    def test_expand_infrastructure_produces_correct_file_plan_dicts(self):
        """expand_infrastructure phải tạo ra file plan dicts đúng cấu trúc."""
        loader = FileContributionsLoader()
        fc = loader.load(pack_internal_id="cp_full_workflow_scheduler", pack_id="CP13", stack="fastapi")
        plans = FileContributionsLoader.expand_infrastructure(fc)
        assert len(plans) > 0, "Không có file plan nào được expand"
        for plan in plans:
            assert "path" in plan, "File plan thiếu 'path'"
            assert "type" in plan, "File plan thiếu 'type'"
            assert "template" in plan, "File plan thiếu 'template'"
            assert "context" in plan, "File plan thiếu 'context'"
            assert "metadata" in plan, "File plan thiếu 'metadata'"


# ============================================================================
# Template Rules Compliance (V1 / V2)
# ============================================================================


class TestTemplateRulesCompliance:
    """Kiểm tra templates CP13 tuân thủ Template Rules V1/V2."""

    def _get_cp13_jinja_files(self):
        """Lấy tất cả file .jinja2 của CP13 từ stacks directory."""
        stacks_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "stacks"
        jinja_files = list(stacks_dir.rglob("*/cp_full_workflow_scheduler/*.jinja2"))
        return jinja_files

    def test_no_midicoder_imports_in_templates(self):
        """Rule V1: Không có 'from midicoder' trong bất kỳ template CP13 nào."""
        for jinja_file in self._get_cp13_jinja_files():
            content = jinja_file.read_text(encoding="utf-8")
            assert "from midicoder" not in content, f"Rule V1 violation in {jinja_file.name}: found 'from midicoder'"

    def test_no_midicoder_scope_imports_in_templates(self):
        """Rule V1: Không có '@midicoder/' trong bất kỳ template CP13 nào."""
        for jinja_file in self._get_cp13_jinja_files():
            content = jinja_file.read_text(encoding="utf-8")
            assert "@midicoder/" not in content, f"Rule V1 violation in {jinja_file.name}: found '@midicoder/'"

    def test_no_post_init_in_templates(self):
        """Rule V2: Không có '__post_init__' trong bất kỳ template CP13 nào."""
        for jinja_file in self._get_cp13_jinja_files():
            content = jinja_file.read_text(encoding="utf-8")
            assert "__post_init__" not in content, f"Rule V2 violation in {jinja_file.name}: found '__post_init__'"
