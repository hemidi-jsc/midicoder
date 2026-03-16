from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path

import midicoder.code.generator.pipeline as pipeline_mod
from midicoder.code.applicator.pipeline import _detect_import_cycles, _run_smoke_import_main
from midicoder.code.applicator.models import ApplyOptions, LoadedPatchPlan
from midicoder.code.applicator.pipeline import _should_reset_runtime_content
from midicoder.code.generator.pipeline import (
    _build_sqlalchemy_db_provider_operation,
    _canonicalize_internal_module,
    _collect_generation_validation_errors,
    _collect_missing_internal_modules,
    _default_db_url_from_datasource,
    _detect_internal_import_cycle,
    _normalize_model_annotation_collisions,
    _payload_requires_db,
    _resolve_default_datasource,
)
from midicoder.code.generator.project_files import (
    _collect_external_modules_from_operations,
    _validate_project_file_payload,
    _validate_requirements_coverage,
)
from midicoder.code.generator.patch_ops import _should_drop_existing_import


def test_collect_external_modules_filters_stdlib() -> None:
    patch_plan_operations = {
        "app/attendance/schema.py": [
            {
                "imports": [
                    "from __future__ import annotations",
                    "import datetime",
                    "from typing import Optional",
                    "from fastapi import APIRouter",
                    "import sqlalchemy",
                ],
                "region_content": "from pydantic import BaseModel\nimport uuid\nfrom decimal import Decimal",
            }
        ]
    }

    modules = _collect_external_modules_from_operations(patch_plan_operations)

    assert modules == ["fastapi", "pydantic", "sqlalchemy"]


def test_validate_requirements_coverage_ignores_stdlib() -> None:
    context_payload = {
        "required_packages": ["fastapi", "typing", "uuid"],
    }
    region_content = "fastapi==0.115.0"

    err = _validate_requirements_coverage(region_content, context_payload)

    assert err is None


def test_validate_package_init_blocks_import_from_main() -> None:
    payload = {
        "merge_mode": "create",
        "imports": ["from .main import app"],
        "region_content": "__all__ = ['app']",
    }
    context_payload = {
        "package_export_candidates": ["app"],
        "package_module_exports": {"main": ["app"]},
        "python_runtime_files": ["app/main.py"],
        "runtime_exports_by_path": {"app/main.py": ["app"]},
    }

    _, _, err = _validate_project_file_payload(
        runtime_path="app/__init__.py",
        payload=payload,
        kind="package_init",
        context_payload=context_payload,
    )

    assert err is not None
    assert "must not import from .main" in err


def test_validate_package_init_blocks_absolute_self_imports() -> None:
    payload = {
        "merge_mode": "create",
        "imports": ["from app.shared import db"],
        "region_content": "__all__ = ['db']",
    }
    context_payload = {
        "package_export_candidates": ["db"],
        "package_module_exports": {"db": ["get_db"]},
        "python_runtime_files": ["app/shared/db.py"],
        "runtime_exports_by_path": {"app/shared/db.py": ["get_db"]},
    }

    _, _, err = _validate_project_file_payload(
        runtime_path="app/shared/__init__.py",
        payload=payload,
        kind="package_init",
        context_payload=context_payload,
    )

    assert err is not None
    assert "use relative imports" in err


def test_generation_validation_flags_missing_existing_symbol() -> None:
    plan_item = SimpleNamespace(
        ir_ref="Command.check_in_command",
        payload={"pseudo_struct": {"intent": {"kind": "controller"}}, "integration_contract": {}},
    )
    block = """# region Command.check_in_command
from app.main import get_db

def check_in_command():
    return None
# endregion Command.check_in_command
"""

    errors = _collect_generation_validation_errors(
        item=plan_item,
        runtime_path="app/attendance/service.py",
        block=block,
        allowed_modules={"app.main"},
        generated_symbol_index={},
        existing_symbol_index={"app.main": ["app", "read_root"]},
    )

    assert any("Imported symbol 'get_db' not found in generated module 'app.main'" in err for err in errors)


def test_generation_validation_flags_model_field_name_type_collision() -> None:
    plan_item = SimpleNamespace(
        ir_ref="Entity.attendance_record",
        payload={"pseudo_struct": {"intent": {"kind": "model"}}, "integration_contract": {}},
    )
    block = """# region Entity.attendance_record
class AttendanceRecord:
    date: date
# endregion Entity.attendance_record
"""
    errors = _collect_generation_validation_errors(
        item=plan_item,
        runtime_path="app/attendance_records/model.py",
        block=block,
        allowed_modules=set(),
        generated_symbol_index={},
        existing_symbol_index={},
    )
    assert any("Model field 'date: date' is unsafe" in err for err in errors)


def test_generation_validation_rejects_time_module_time_in_model() -> None:
    plan_item = SimpleNamespace(
        ir_ref="Entity.shift",
        payload={"pseudo_struct": {"intent": {"kind": "model"}}, "integration_contract": {}},
    )
    block = """# region Entity.shift
from time import time as time_type

class Shift:
    start_time: time_type
# endregion Entity.shift
"""
    errors = _collect_generation_validation_errors(
        item=plan_item,
        runtime_path="app/attendance_records/model.py",
        block=block,
        allowed_modules=set(),
        generated_symbol_index={},
        existing_symbol_index={},
    )
    assert any("Model must not import `time` from stdlib `time` module" in err for err in errors)


def test_normalize_model_annotation_collisions_rewrites_import_alias() -> None:
    block = """# region Entity.attendance_record
from datetime import date, datetime

class AttendanceRecord:
    date: date
# endregion Entity.attendance_record
"""
    normalized = _normalize_model_annotation_collisions(
        block,
        runtime_path="app/attendance_records/model.py",
        ir_ref="Entity.attendance_record",
    )
    assert "from datetime import date as date_type, datetime" in normalized
    assert "date: date_type" in normalized


def test_detect_internal_import_cycle() -> None:
    preview = {
        "app/main.py": "from app.attendance.schema import CheckInRequest\napp = object()\n",
        "app/__init__.py": "from app.main import app\n",
    }
    candidate = """# region Query.get_attendance_by_date
from app.main import app

class CheckInRequest:
    pass
# endregion Query.get_attendance_by_date
"""
    cycles = _detect_internal_import_cycle(
        patch_preview_cache=preview,
        runtime_path="app/attendance/schema.py",
        candidate_block=candidate,
    )

    assert cycles
    assert any("app.main" in cycle and "app.attendance.schema" in cycle for cycle in cycles)


def test_apply_detect_import_cycles() -> None:
    module_to_imports = {
        "app.main": {"app.attendance.schema"},
        "app.attendance.schema": {"app.main"},
    }

    cycles = _detect_import_cycles(module_to_imports)

    assert cycles
    assert any("app.main" in cycle and "app.attendance.schema" in cycle for cycle in cycles)


def test_should_reset_runtime_content_default_true() -> None:
    options = ApplyOptions(
        workspace_root=Path("."),
        version="1.0.1",
        patches_dir=Path("."),
        working_dir=Path("."),
    )
    project_target = LoadedPatchPlan(
        runtime_path="app/main.py",
        patch_plan_file="app.main.patch-plan.json",
        patch_plan_path=Path("app.main.patch-plan.json"),
        operations=[{"group": "project_file"}],
    )
    runtime_target = LoadedPatchPlan(
        runtime_path="app/attendance/controller.py",
        patch_plan_file="app.attendance.controller.patch-plan.json",
        patch_plan_path=Path("app.attendance.controller.patch-plan.json"),
        operations=[{"group": "queries"}],
    )
    requirements_target = LoadedPatchPlan(
        runtime_path="requirements.txt",
        patch_plan_file="requirements.txt.patch-plan.json",
        patch_plan_path=Path("requirements.txt.patch-plan.json"),
        operations=[{"group": "project_file"}],
    )
    assert _should_reset_runtime_content(runtime_path="app/main.py", target=project_target, options=options) is True
    assert (
        _should_reset_runtime_content(runtime_path="app/attendance/controller.py", target=runtime_target, options=options)
        is False
    )
    assert (
        _should_reset_runtime_content(runtime_path="requirements.txt", target=requirements_target, options=options)
        is True
    )


def test_db_alias_modules_are_canonicalized() -> None:
    assert _canonicalize_internal_module("app.db") == "app.shared.db"
    assert _canonicalize_internal_module("app.database") == "app.shared.db"
    assert _canonicalize_internal_module("app.core.database") == "app.shared.db"


def test_missing_module_validation_accepts_db_alias_when_canonical_allowed() -> None:
    block = "from app.db import get_db\n"
    missing = _collect_missing_internal_modules(block, allowed_modules={"app.shared.db"})
    assert missing == []


def test_payload_requires_db_from_effects() -> None:
    payload = {
        "pseudo_struct": {
            "steps": [
                {"effects": [{"id": "db.insert"}]},
            ]
        }
    }
    assert _payload_requires_db(payload) is True


def test_default_db_url_from_postgres_datasource() -> None:
    datasource = {
        "id": "main_db",
        "engine": "postgres",
        "database": "hr_system",
        "host": "localhost",
        "port": 5432,
        "default": True,
    }
    assert _default_db_url_from_datasource(datasource) == "postgresql+psycopg://postgres:postgres@localhost:5432/hr_system"


def test_build_sqlalchemy_db_provider_operation_uses_datasource_defaults() -> None:
    datasource = {
        "id": "main_db",
        "engine": "postgres",
        "database": "hr_system",
        "host": "localhost",
        "port": 5432,
        "default": True,
    }
    operation = _build_sqlalchemy_db_provider_operation(datasource=datasource)
    region_content = str(operation.get("region_content", ""))

    assert operation["ir_ref"] == "ProjectFile.db_provider.app_shared_db_py"
    assert "from sqlalchemy import create_engine" in region_content
    assert 'DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/hr_system"' in region_content
    assert 'DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)' in region_content
    assert "def get_db() -> Generator[Session, None, None]:" in region_content


def test_resolve_default_datasource_reads_modules_persistence_bucket() -> None:
    ir_payload = {
        "modules": {
            "persistence": {
                "datasources": [
                    {"id": "archive_db", "default": False},
                    {"id": "main_db", "default": True},
                ]
            }
        }
    }
    datasource = _resolve_default_datasource(ir_payload)
    assert datasource is not None
    assert datasource.get("id") == "main_db"


def test_should_drop_existing_import_for_legacy_db_aliases() -> None:
    assert _should_drop_existing_import("from app.main import get_db") is True
    assert _should_drop_existing_import("from app.main import app") is False
    assert _should_drop_existing_import("from app.db import get_db") is True
    assert _should_drop_existing_import("from app.shared.db import get_db") is False


def test_smoke_import_ignores_external_module_missing(monkeypatch, tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    app_dir.mkdir(parents=True, exist_ok=True)
    (app_dir / "main.py").write_text("x = 1\n", encoding="utf-8")

    class _Result:
        def __init__(self) -> None:
            self.returncode = 1
            self.stderr = "ModuleNotFoundError: No module named 'sqlalchemy'"
            self.stdout = ""

    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: _Result())

    err = _run_smoke_import_main(working_dir=tmp_path)
    assert err is None


def test_build_runtime_code_fails_when_all_candidates_fail_validation(monkeypatch, tmp_path: Path) -> None:
    workspace_root = tmp_path
    plans_dir = tmp_path / "plans"
    patches_root = tmp_path / "patches"
    plans_dir.mkdir(parents=True, exist_ok=True)
    patches_root.mkdir(parents=True, exist_ok=True)

    manifest = SimpleNamespace(bootstrap_entrypoint=None)
    item = SimpleNamespace(
        ir_ref="Command.check_in_command",
        rel_path="commands/check_in.yaml",
        group="command",
        merge_mode="patch",
        runtime_paths=["app/attendance/controller.py"],
        payload={"pseudo_struct": {"intent": {"kind": "controller"}}, "integration_contract": {}},
    )

    monkeypatch.setattr(pipeline_mod, "load_context_profile", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(pipeline_mod, "load_index_manifest", lambda *_args, **_kwargs: manifest)
    monkeypatch.setattr(pipeline_mod, "resolve_execution_order", lambda *_args, **_kwargs: ["Command.check_in_command"])
    monkeypatch.setattr(pipeline_mod, "load_plan_item", lambda *_args, **_kwargs: item)
    monkeypatch.setattr(
        pipeline_mod,
        "build_item_context",
        lambda *_args, **_kwargs: {"generated_symbol_index": {}, "seams": [], "virtual_seams": [], "symbols": [], "entrypoints": []},
    )
    monkeypatch.setattr(
        pipeline_mod,
        "maybe_generate_with_llm",
        lambda *_args, **_kwargs: (
            """# region Command.check_in_command
def check_in_command():
    # TODO: implement
    pass
# endregion Command.check_in_command
""",
            [],
        ),
    )
    monkeypatch.setattr(
        pipeline_mod,
        "generate_project_file_patch_operations",
        lambda *_args, **_kwargs: ([], [], []),
    )

    result = pipeline_mod.build_runtime_code(
        workspace_root=workspace_root,
        version="1.0.1",
        plans_dir=plans_dir,
        patches_root=patches_root,
        generator_version="test",
        config={"code_gen_validation_max_attempts": 1},
        runtime_enabled=False,
    )

    assert result.generated_patch_plans == []
    assert any("validation_failed_after_1_attempts" in err for err in result.errors)
