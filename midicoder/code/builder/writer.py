"""Serialize and write code-plan artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .constants import CODE_PLAN_SCHEMA_VERSION, GROUP_MAP
from .models import CodePlanItem


def slug_from_ir_ref(ir_ref: str) -> str:
    return ir_ref.strip().lower().replace(".", "-").replace("_", "-")


def group_from_ir_ref(ir_ref: str) -> str:
    type_name = ir_ref.split(".", 1)[0]
    return GROUP_MAP.get(type_name, "misc")


def write_plan_file(plans_dir: Path, plan: CodePlanItem) -> str:
    slug = slug_from_ir_ref(plan.ir_ref)
    group = group_from_ir_ref(plan.ir_ref)
    relative_path = f"{group}/{slug}.code-plan.json"
    output_path = plans_dir / relative_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(plan.to_dict(), indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    return relative_path


def build_index_payload(
    version: str,
    plan_paths: list[str],
    *,
    plans: list[CodePlanItem],
    stack: str,
) -> dict[str, Any]:
    file_ownership: dict[str, list[str]] = {}
    merge_mode: dict[str, str] = {}
    for plan in plans:
        if isinstance(plan.merge_contract, dict):
            mode = str(plan.merge_contract.get("mode", "")).strip()
            if mode:
                merge_mode[plan.ir_ref] = mode
            ownership = plan.merge_contract.get("ownership", [])
            if isinstance(ownership, list):
                for path in ownership:
                    path_value = str(path).strip()
                    if not path_value:
                        continue
                    file_ownership.setdefault(path_value, []).append(plan.ir_ref)

    generation_order = [
        "entities",
        "workflows",
        "queries",
        "commands",
        "bootstrap",
    ]
    return {
        "version": version,
        "schema_version": CODE_PLAN_SCHEMA_VERSION,
        "plans": sorted(plan_paths),
        "generation_order": generation_order,
        "file_ownership": {key: sorted(set(value)) for key, value in sorted(file_ownership.items())},
        "merge_mode": dict(sorted(merge_mode.items())),
        "bootstrap_contract": {
            "stack": stack,
            "entrypoint": "app/main.py" if stack == "fastapi" else "src/main.ts",
            "notes": "code build is deterministic metadata planning; runtime materialization happens in code gen",
        },
        "verification_pipeline": {
            "enabled": False,
            "notes": "verification runs in downstream phases (code gen/apply)",
            "steps": ["lint", "typecheck", "unit", "smoke"],
        },
    }


def write_plan_index(plans_dir: Path, index_payload: dict[str, Any]) -> None:
    index_path = plans_dir / "index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index_payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
