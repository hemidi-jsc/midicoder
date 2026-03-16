from __future__ import annotations

from types import SimpleNamespace

from midicoder.code.builder.integration import _build_merge_contract
from midicoder.code.builder.models import IRPlanItem, RequiredFile, SuggestedPath
from midicoder.code.generator.models import IndexManifest
from midicoder.code.generator.pipeline import _collect_generation_validation_errors
from midicoder.code.generator.plan_loader import _resolve_runtime_paths


def _make_item(*, type_name: str = "Command") -> IRPlanItem:
    return IRPlanItem(
        raw_id="check_in_command",
        type_name=type_name,
        id=f"{type_name}.check_in_command",
        kind="controller",
        module="attendance",
        source={},
        payload={},
        source_order=0,
    )


def test_merge_contract_runtime_scope_and_ownership_expansion() -> None:
    item = _make_item(type_name="Command")
    suggested_paths = [SuggestedPath(file="app/attendance/controller.py", anchor="route:POST:/attendance/check-in")]
    required_files = [
        RequiredFile(
            path_pattern="app/attendance/service.py",
            required=True,
            role="business_service",
            reason="runtime business logic",
        ),
        RequiredFile(
            path_pattern="app/attendance/schema.py",
            required=True,
            role="dto_schema",
            reason="request/response contract",
        ),
        RequiredFile(
            path_pattern="app/attendance/migrations/*.py",
            required=False,
            role="migration_stub",
            reason="optional",
        ),
    ]

    merge_contract = _build_merge_contract(
        item=item,
        target="fastapi_endpoint",
        suggested_paths=suggested_paths,
        required_files=required_files,
    )

    assert merge_contract["write_scope"] == "runtime"
    assert "app/attendance/controller.py" in merge_contract["ownership"]
    assert "app/attendance/service.py" in merge_contract["ownership"]
    assert "app/attendance/schema.py" in merge_contract["ownership"]
    assert all("*" not in path for path in merge_contract["ownership"])


def test_resolve_runtime_paths_keeps_required_files_when_file_ownership_exists() -> None:
    manifest = IndexManifest(
        version="0.1.0",
        plans=[],
        generation_order=[],
        merge_mode={},
        file_ownership={"app/attendance/controller.py": ["Command.check_in_command"]},
        bootstrap_entrypoint=None,
    )
    payload = {
        "target": "fastapi_endpoint",
        "required_files": [
            {"path_pattern": "app/attendance/controller.py", "role": "endpoint_controller"},
            {"path_pattern": "app/attendance/service.py", "role": "business_service"},
            {"path_pattern": "app/attendance/schema.py", "role": "dto_schema"},
        ],
    }

    runtime_paths = _resolve_runtime_paths(
        manifest=manifest,
        payload=payload,
        ir_ref="Command.check_in_command",
    )

    assert runtime_paths == [
        "app/attendance/schema.py",
        "app/attendance/service.py",
        "app/attendance/controller.py",
    ]


def test_generation_validation_rejects_simulated_db_content() -> None:
    plan_item = SimpleNamespace(
        ir_ref="Command.check_in_command",
        payload={
            "pseudo_struct": {
                "intent": {"kind": "controller"},
                "steps": [
                    {
                        "type": "persist",
                        "effects": [{"id": "db.insert", "params": {"entity": "AttendanceRecord"}}],
                    }
                ],
            },
            "integration_contract": {},
        },
    )
    block = """# region Command.check_in_command
from fastapi import APIRouter
router = APIRouter()

@router.post("/attendance/check-in")
async def check_in_command():
    # Simulated repository method for fetching attendance records
    # In a real implementation, this would query the database
    return []
# endregion Command.check_in_command
"""

    errors = _collect_generation_validation_errors(
        item=plan_item,
        runtime_path="app/attendance/controller.py",
        block=block,
        allowed_modules=set(),
        generated_symbol_index={},
    )

    assert any("simulated/mock wording" in err.lower() for err in errors)
    assert any("no persistence signal" in err.lower() for err in errors)
