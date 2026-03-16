from __future__ import annotations

import json
from pathlib import Path

from midicoder.runtime.fix.analyzer import ErrorAnalysis, analyze_error_logs
from midicoder.runtime.fix.business_guard import validate_runtime_fix_operations
from midicoder.runtime.fix.generator import FixConfig, RuntimeFixGenerator
from midicoder.runtime.fix.prompter import build_fix_prompt


def test_analyze_error_logs_enriches_runtime_metadata(tmp_path: Path) -> None:
    working_dir = tmp_path / "repo"
    working_dir.mkdir(parents=True, exist_ok=True)
    app_dir = working_dir / "app"
    app_dir.mkdir(parents=True, exist_ok=True)
    (app_dir / "main.py").write_text("print('ok')\n", encoding="utf-8")

    log_dir = tmp_path / "logs" / "20260314T010000Z"
    log_dir.mkdir(parents=True, exist_ok=True)

    file_abs = (app_dir / "main.py").resolve()
    summary = {
        "success": False,
        "errors": [
            {
                "type": "import_error",
                "message": "ImportError: cannot import name X",
                "file": str(file_abs),
                "line": 3,
                "traceback": "",
            }
        ],
    }
    (log_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (log_dir / "error.log").write_text(
        f'Traceback (most recent call last):\n  File "{file_abs}", line 3, in <module>\nImportError: cannot import name X\n',
        encoding="utf-8",
    )

    analysis = analyze_error_logs(log_dir, working_dir=working_dir)

    assert isinstance(analysis, ErrorAnalysis)
    assert "app/main.py" in analysis.normalized_project_files
    assert any(item.get("file") == "app/main.py" for item in analysis.traceback_focus)
    assert "import_error" in analysis.runtime_keywords


def test_build_fix_prompt_uses_stack_adapter_nest(tmp_path: Path) -> None:
    working_dir = tmp_path / "repo"
    working_dir.mkdir(parents=True, exist_ok=True)
    src_dir = working_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "app.service.ts").write_text("export class AppService {}\n", encoding="utf-8")

    analysis = ErrorAnalysis()
    runtime_context = {
        "profile_summary": {"stack": "nest", "framework": "nest"},
        "traceback_focus": [{"file": "src/app.service.ts", "line": 1, "source": "traceback"}],
        "relevant_files": ["src/app.service.ts"],
        "symbols_by_file": {"src/app.service.ts": ["class:AppService@1"]},
        "entrypoints": [],
        "seams": [],
        "contracts_focus": [],
        "ir_focus": [],
    }

    prompt = build_fix_prompt(analysis=analysis, runtime_context=runtime_context, working_dir=working_dir)
    assert "STACK ADAPTER (NestJS):" in prompt.user_prompt
    assert "FastAPI Convention" not in prompt.user_prompt


def test_business_guard_rejects_empty_and_external_ops(tmp_path: Path) -> None:
    working_dir = tmp_path / "repo"
    working_dir.mkdir(parents=True, exist_ok=True)
    outside_file = (tmp_path / "outside" / "app" / "main.py").resolve()

    ops = [
        {
            "operation_type": "upsert_region",
            "ir_ref": "runtime_fix:test:001",
            "merge_mode": "patch",
            "region_start": "# region runtime_fix:test:001",
            "region_end": "# endregion runtime_fix:test:001",
            "region_content": "pass",
            "file_path": "app/main.py",
        },
        {
            "operation_type": "upsert_region",
            "ir_ref": "runtime_fix:test:002",
            "merge_mode": "patch",
            "region_start": "# region runtime_fix:test:002",
            "region_end": "# endregion runtime_fix:test:002",
            "region_content": "print('fix')",
            "file_path": str(outside_file),
        },
    ]

    valid, issues = validate_runtime_fix_operations(ops, working_dir=working_dir)
    assert not valid
    assert any("empty or no-op" in issue for issue in issues)
    assert any("outside working_dir" in issue for issue in issues)


def test_runtime_fix_canonicalize_ops_stable_ir_ref_and_import_split(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    working_dir = workspace / "apprepo"
    working_dir.mkdir(parents=True, exist_ok=True)
    generator = RuntimeFixGenerator(
        FixConfig(
            workspace_root=workspace,
            working_dir=working_dir,
            version="1.0.1",
            stack_hint="fastapi",
        )
    )

    ops = [
        {
            "operation_type": "upsert_region",
            "ir_ref": "runtime_fix:import_order:001",
            "merge_mode": "patch",
            "region_start": "# region runtime_fix:import_order:001",
            "region_end": "# endregion runtime_fix:import_order:001",
            "region_content": (
                "from __future__ import annotations\n"
                "from typing import TYPE_CHECKING\n\n"
                "x = 1"
            ),
            "imports": [],
            "file_path": "app/main.py",
        },
        {
            "operation_type": "upsert_region",
            "ir_ref": "runtime_fix:import_order:999",
            "merge_mode": "patch",
            "region_start": "# region runtime_fix:import_order:999",
            "region_end": "# endregion runtime_fix:import_order:999",
            "region_content": "y = 2",
            "imports": ["from typing import TYPE_CHECKING"],
            "file_path": "app/main.py",
        },
    ]

    canonical_ops, warnings = generator._canonicalize_runtime_operations(ops)
    assert warnings == []
    assert len(canonical_ops) == 1
    op = canonical_ops[0]
    assert op["ir_ref"] == "runtime_fix:import_order:app_main_py"
    assert op["region_start"] == "# region runtime_fix:import_order:app_main_py"
    assert op["region_end"] == "# endregion runtime_fix:import_order:app_main_py"
    assert "from __future__ import annotations" in op["imports"]
    assert "from typing import TYPE_CHECKING" in op["imports"]
    assert "from __future__ import annotations" not in op["region_content"]
