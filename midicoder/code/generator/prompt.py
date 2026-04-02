from __future__ import annotations

import json
from typing import Any

from .models import PlanItemRuntime


def _truncate_list(value: Any, limit: int = 50) -> Any:
    if isinstance(value, list):
        return value[:limit]
    return value


def _truncate_map(value: Any, *, item_limit: int, text_limit: int) -> Any:
    if not isinstance(value, dict):
        return value
    out: dict[str, Any] = {}
    for idx, key in enumerate(sorted(value.keys())):
        if idx >= item_limit:
            break
        raw = value.get(key)
        if isinstance(raw, str):
            text = raw.strip()
            if len(text) > text_limit:
                text = text[:text_limit] + "\n...<truncated>..."
            out[str(key)] = text
        elif isinstance(raw, list):
            out[str(key)] = raw[:80]
        else:
            out[str(key)] = raw
    return out


def _compact_context_payload(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "profile": context.get("profile"),
        "seams": _truncate_list(context.get("seams"), limit=60),
        "virtual_seams": _truncate_list(context.get("virtual_seams"), limit=60),
        "symbols": _truncate_list(context.get("symbols"), limit=120),
        "entrypoints": _truncate_list(context.get("entrypoints"), limit=80),
        "exemplars": _truncate_list(context.get("exemplars"), limit=20),
    }


def build_codegen_prompt(
    plan_item: PlanItemRuntime,
    context: dict[str, Any],
    runtime_path: str,
    *,
    attempt: int = 1,
    max_attempts: int = 1,
    validation_errors: list[str] | None = None,
) -> str:
    payload = plan_item.payload
    pseudo_struct = payload.get("pseudo_struct", {})
    integration_contract = payload.get("integration_contract", {})
    security_contract = payload.get("security_contract", {})

    compact_context = {
        "ir_ref": plan_item.ir_ref,
        "runtime_path": runtime_path,
        "merge_mode": plan_item.merge_mode,
        "pseudo_struct": pseudo_struct,
        "integration_contract": integration_contract,
        "security_contract": security_contract,
        "destination_snapshot": context.get("destination_snapshots", {}).get(
            runtime_path
        ),
        "project_context": _compact_context_payload(context),
        "allowed_internal_modules": _truncate_list(
            context.get("allowed_internal_modules"), limit=300
        ),
        "existing_internal_modules": _truncate_list(
            context.get("existing_internal_modules"), limit=300
        ),
        "generated_symbol_index": _truncate_map(
            context.get("generated_symbol_index"),
            item_limit=120,
            text_limit=2000,
        ),
        "generated_runtime_snapshots": _truncate_map(
            context.get("generated_runtime_snapshots"),
            item_limit=40,
            text_limit=2200,
        ),
    }

    ir_ref = plan_item.ir_ref
    validation_lines = validation_errors or []
    db_required = False
    if isinstance(pseudo_struct, dict):
        steps = pseudo_struct.get("steps")
        if isinstance(steps, list):
            for step in steps:
                if not isinstance(step, dict):
                    continue
                for effect in (
                    step.get("effects", [])
                    if isinstance(step.get("effects"), list)
                    else []
                ):
                    if not isinstance(effect, dict):
                        continue
                    effect_id = str(effect.get("id", "")).strip().lower()
                    if effect_id in {
                        "db.insert",
                        "db.update",
                        "db.delete",
                        "db.upsert",
                    }:
                        db_required = True
                        break
                if db_required:
                    break
                reads = step.get("reads")
                if isinstance(reads, list) and reads:
                    db_required = True
                    break
    validation_section = ""
    if validation_lines:
        validation_section = (
            "\nValidation errors from previous attempt that MUST be fixed:\n"
            + "\n".join(f"- {line}" for line in validation_lines)
            + "\n"
        )
    persistence_section = ""
    if db_required:
        persistence_section = (
            "- This item has DB persistence/read requirements from contracts.\n"
            "- Generate concrete persistence logic (repository/session/ORM calls), not simulated or in-memory data.\n"
            "- For DB dependency import, use ONLY `from app.shared.db import get_db` or `get_db_session`.\n"
            "- Forbidden DB module imports: `app.main`, `app.db`, `app.database`, `app.core.database`.\n"
            "- Forbidden phrases/patterns: 'Simulated repository', 'In a real implementation', hardcoded fake record lists for persistence paths.\n"
        )
    return (
        "You are generating production-ready FastAPI Python code from a plan contract.\n"
        "Target model profile: Claude 3.5 Haiku (follow explicit constraints, no speculation).\n"
        "Strict output contract:\n"
        "- Return ONLY a Python code region block for one item.\n"
        f"- First line MUST be exactly: # region {ir_ref}\n"
        f"- Last line MUST be exactly: # endregion {ir_ref}\n"
        "- No markdown fences (` ``` `), no prose, no comments outside region markers.\n"
        "- Do NOT return full-file boilerplate (no repeated module headers).\n"
        "- Do NOT reference undefined symbols.\n"
        "- Prefer project-local symbols that already exist in destination_snapshot or allowed_internal_modules.\n"
        "- If you need app-internal imports (`app.*`), ONLY use modules listed in allowed_internal_modules.\n"
        "- Also verify exact symbol names from generated_symbol_index before importing from app.* modules.\n"
        "- If a module exists in generated_runtime_snapshots, align imports/usages with its actual exported symbols.\n"
        "- If required symbol/module is missing from context, implement the symbol directly in this target region.\n"
        "- Do NOT move implementation to another file and then import it just to bypass missing context.\n"
        "- Only import `app.*` modules when they already exist in context or are explicitly required by contracts.\n"
        "- Put required imports at top-level import statements (not hidden inside nested function scope unless truly local).\n"
        "- If you need helper/repository behavior and no valid import exists, implement minimal local helpers in-region.\n"
        "- Never return placeholders (no `pass`, no TODO-only, no NotImplemented stubs, no empty class/function bodies).\n"
        "- Every imported symbol must be actually used and must have matching implementation semantics.\n"
        "- Implement concrete handler/service/model symbols from integration_contract and pseudo_struct.\n"
        "- Preserve business contracts from pseudo_struct: request/response field types must stay consistent.\n"
        "- Do not introduce type-changing transformations unless explicitly required by pseudo_struct/integration_contract.\n"
        "- Controller regions must define route handlers with `@router.<method>(...)` when route contracts exist.\n"
        "- Service regions must define callable business functions from service_signature when provided.\n"
        "- Model regions should define concrete model classes when the intent kind is model.\n"
        "- The generated region must be directly runnable after merge into the target file.\n"
        "- Preserve and extend existing destination_snapshot behavior; do not erase previously merged logic.\n"
        "- Keep block idempotent and compatible with existing destination_snapshot.\n"
        f"- Runtime path target: {runtime_path}\n\n"
        f"Generation attempt: {attempt}/{max_attempts}\n"
        + validation_section
        + persistence_section
        + "\n"
        "Plan context (JSON):\n"
        f"{json.dumps(compact_context, ensure_ascii=False)}\n"
    )


def build_project_file_prompt(
    *,
    project_kind: str,
    runtime_path: str,
    context_payload: dict[str, Any],
    attempt: int = 1,
    max_attempts: int = 1,
    validation_errors: list[str] | None = None,
) -> str:
    validation_lines = validation_errors or []
    validation_section = ""
    if validation_lines:
        validation_section = (
            "\nValidation errors from previous attempt that MUST be fixed:\n"
            + "\n".join(f"- {line}" for line in validation_lines)
            + "\n"
        )
    return (
        "You are generating project_file patch operation content for a FastAPI project.\n"
        "Target model profile: Claude 3.5 Haiku.\n"
        "Strict output contract:\n"
        "- Return ONLY JSON object with keys: merge_mode, imports, region_content.\n"
        "- No markdown fences, no prose.\n"
        "- merge_mode must be one of: create, append, patch.\n"
        "- imports must be a JSON array of import lines.\n"
        "- region_content must be complete runnable content for target file.\n"
        "- Do not invent dependencies/symbols outside provided context.\n"
        "- For requirements.txt, every dependency line must include version spec.\n"
        "- For requirements.txt, include all packages required by required_external_modules/required_packages.\n"
        "- Prefer pinned lines from required_packages_with_versions and context_requirements.\n"
        "- For main file, initialize FastAPI app and include routers from controller_modules when provided.\n"
        "- Keep main structure consistent with existing project style from destination_snapshot.\n"
        "- For package __init__.py, use plain assignment: __all__ = [...], never __all__: List[str] = [...].\n"
        "- For package __init__.py, export only names listed in package_export_candidates from context.\n"
        "- For package __init__.py, prefer concrete symbol exports when available; module-name exports are allowed if valid in package_export_candidates.\n"
        "- For package __init__.py, use relative imports for same-package modules (e.g. `from . import db`, `from .schema import X`).\n"
        "- For package __init__.py, never import the package itself via absolute path (e.g. `from app.shared import ...` inside `app/shared/__init__.py`).\n"
        "- If generation_feedback is provided, fix all listed previous_errors exactly in this attempt.\n"
        "- If destination_snapshot is provided, preserve working content and only apply required adjustments.\n"
        f"- project_kind: {project_kind}\n"
        f"- runtime_path: {runtime_path}\n\n"
        f"Generation attempt: {attempt}/{max_attempts}\n" + validation_section + "\n"
        "Context JSON:\n"
        f"{json.dumps(context_payload, ensure_ascii=False)}\n"
    )
