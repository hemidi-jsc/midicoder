from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import IndexManifest, PlanItemRuntime, PlanRef


def _normalize_fastapi_path(path_value: str) -> str:
    path_value = path_value.replace("\\", "/")
    if not path_value.startswith("app/"):
        path_value = f"app/{path_value.lstrip('/')}"
    if not path_value.endswith(".py"):
        path_value = f"{path_value.rsplit('.', 1)[0]}.py"
    return path_value


def _fallback_path(payload: dict[str, Any]) -> str:
    pseudo = (
        payload.get("pseudo_struct", {})
        if isinstance(payload.get("pseudo_struct"), dict)
        else {}
    )
    intent = pseudo.get("intent", {}) if isinstance(pseudo.get("intent"), dict) else {}
    module = str(intent.get("module", "misc"))
    kind = str(intent.get("kind", "generated"))
    return _normalize_fastapi_path(f"app/{module}/{kind}.py")


def _resolve_runtime_paths(
    *,
    manifest: IndexManifest,
    payload: dict[str, Any],
    ir_ref: str,
) -> list[str]:
    resolved: list[str] = []
    role_by_path: dict[str, str] = {}
    target = str(payload.get("target", "")).strip().lower()

    for file_path, owners in manifest.file_ownership.items():
        if ir_ref in owners:
            resolved.append(_normalize_fastapi_path(file_path))

    required_files = payload.get("required_files", [])
    if isinstance(required_files, list):
        for req in required_files:
            if not isinstance(req, dict):
                continue
            pattern = req.get("path_pattern")
            if isinstance(pattern, str) and "*" not in pattern:
                normalized = _normalize_fastapi_path(pattern)
                resolved.append(normalized)
                role = req.get("role")
                if isinstance(role, str) and role.strip():
                    role_by_path[normalized] = role.strip().lower()

    if not resolved:
        suggested = payload.get("suggested_paths", [])
        if isinstance(suggested, list) and suggested:
            first = suggested[0]
            if isinstance(first, dict) and isinstance(first.get("file"), str):
                resolved.append(_normalize_fastapi_path(first["file"]))

    if not resolved:
        resolved.append(_fallback_path(payload))

    unique_paths = list(dict.fromkeys(resolved))

    if target == "fastapi_endpoint":
        role_priority = {
            "dto_schema": 0,
            "business_service": 1,
            "endpoint_controller": 2,
        }

        def _priority(path_value: str) -> tuple[int, str]:
            role = role_by_path.get(path_value, "")
            return (role_priority.get(role, 50), path_value)

        return sorted(unique_paths, key=_priority)

    return sorted(unique_paths)


def load_plan_item(
    plans_dir: Path, ref: PlanRef, manifest: IndexManifest
) -> PlanItemRuntime:
    source_path = plans_dir / ref.rel_path
    if not source_path.exists():
        raise FileNotFoundError(f"Missing plan file: {source_path}")

    payload = json.loads(source_path.read_text(encoding="utf-8"))
    ir_ref = str(payload.get("ir_ref", "unknown.unknown"))
    merge_mode = manifest.merge_mode.get(ir_ref, "patch")
    runtime_paths = _resolve_runtime_paths(
        manifest=manifest, payload=payload, ir_ref=ir_ref
    )

    return PlanItemRuntime(
        source_path=source_path,
        rel_path=ref.rel_path,
        group=ref.group,
        ir_ref=ir_ref,
        payload=payload,
        merge_mode=merge_mode,
        runtime_paths=runtime_paths,
    )
