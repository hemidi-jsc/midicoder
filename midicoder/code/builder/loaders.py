"""Load input artifacts for code build plan."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_ir(ir_path: str | Path) -> dict[str, Any]:
    path = Path(ir_path)
    return json.loads(path.read_text(encoding="utf-8"))


def load_seams(context_dir: str | Path) -> list[dict[str, Any]]:
    payload = _read_json_file(Path(context_dir) / "seams.json")
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        items = payload.get("seams")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    return []


def load_virtual_seams(context_dir: str | Path) -> list[dict[str, Any]]:
    payload = _read_json_file(Path(context_dir) / "virtual_seams.json")
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        items = payload.get("virtual_seams")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    return []


def load_profile(context_dir: str | Path) -> dict[str, Any] | None:
    profile_path = Path(context_dir) / "profile.json"
    if not profile_path.exists():
        return None
    payload = _read_json_file(profile_path)
    if isinstance(payload, dict):
        return payload
    return None


def preflight_check(ir_path: Path, context_dir: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not ir_path.exists():
        errors.append(f"missing required input: {ir_path}")
    # Context artifacts are optional for code-build.
    # When index has not run yet, planner can still resolve convention paths.
    _ = context_dir
    return not errors, errors


def _read_json_file(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

