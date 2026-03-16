from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from .models import PlanItemRuntime


def _read_if_exists(path: Path) -> str | None:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def _read_json_if_exists(path: Path) -> Any:
    text = _read_if_exists(path)
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _runtime_path_to_module(runtime_path: str) -> str:
    normalized = runtime_path.replace("\\", "/").lstrip("./")
    if normalized.endswith(".py"):
        normalized = normalized[:-3]
    return normalized.replace("/", ".")


def _extract_python_exports(content: str) -> list[str]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []
    exports: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name and not node.name.startswith("_"):
                exports.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id and not target.id.startswith("_"):
                    exports.add(target.id)
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and target.id and not target.id.startswith("_"):
                exports.add(target.id)
    return sorted(exports)


def build_item_context(
    *,
    workspace_root: Path,
    version: str,
    plan_item: PlanItemRuntime,
    patches_root: Path,
    current_outputs: dict[str, str],
) -> dict[str, Any]:
    version_root = workspace_root / ".midicoder" / "versions" / version
    contracts_root = version_root / "contracts"
    ir_path = version_root / "irs" / "ir.json"
    context_root = workspace_root / ".midicoder" / "context"
    profile_path = context_root / "profile.json"
    seams_path = context_root / "seams.json"
    virtual_seams_path = context_root / "virtual_seams.json"
    symbols_path = context_root / "symbols.json"
    entrypoints_path = context_root / "entrypoints.json"
    exemplars_path = context_root / "exemplars.json"

    related_contracts: dict[str, str] = {}
    if contracts_root.exists():
        for path in sorted(contracts_root.rglob("*.yaml")):
            text = _read_if_exists(path)
            if text is not None:
                related_contracts[str(path.relative_to(version_root))] = text

    ir_text = _read_if_exists(ir_path)
    profile_text = _read_if_exists(profile_path)
    seams = _read_json_if_exists(seams_path)
    virtual_seams = _read_json_if_exists(virtual_seams_path)
    symbols = _read_json_if_exists(symbols_path)
    entrypoints = _read_json_if_exists(entrypoints_path)
    exemplars = _read_json_if_exists(exemplars_path)

    destination_snapshots: dict[str, str] = {}
    for runtime_path in plan_item.runtime_paths:
        content = current_outputs.get(runtime_path)
        if content is None:
            disk_path = patches_root / runtime_path
            content = _read_if_exists(disk_path)
        if content is not None:
            destination_snapshots[runtime_path] = content

    generated_runtime_snapshots: dict[str, str] = {}
    generated_symbol_index: dict[str, list[str]] = {}
    for runtime_path, content in current_outputs.items():
        if not isinstance(runtime_path, str) or not isinstance(content, str):
            continue
        normalized_path = runtime_path.replace("\\", "/").lstrip("./")
        generated_runtime_snapshots[normalized_path] = content
        if normalized_path.endswith(".py"):
            generated_symbol_index[_runtime_path_to_module(normalized_path)] = _extract_python_exports(content)

    return {
        "ir_ref": plan_item.ir_ref,
        "plan_rel_path": plan_item.rel_path,
        "plan_payload": plan_item.payload,
        "contracts": related_contracts,
        "ir": json.loads(ir_text) if ir_text else None,
        "profile": json.loads(profile_text) if profile_text else None,
        "seams": seams,
        "virtual_seams": virtual_seams,
        "symbols": symbols,
        "entrypoints": entrypoints,
        "exemplars": exemplars,
        "destination_snapshots": destination_snapshots,
        "generated_runtime_snapshots": generated_runtime_snapshots,
        "generated_symbol_index": generated_symbol_index,
    }
