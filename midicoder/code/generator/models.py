from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PlanRef:
    rel_path: str
    group: str


@dataclass(frozen=True)
class IndexManifest:
    version: str
    plans: list[PlanRef]
    generation_order: list[str]
    merge_mode: dict[str, str]
    file_ownership: dict[str, list[str]]
    bootstrap_entrypoint: str | None


@dataclass(frozen=True)
class PlanItemRuntime:
    source_path: Path
    rel_path: str
    group: str
    ir_ref: str
    payload: dict[str, Any]
    merge_mode: str
    runtime_paths: list[str]


@dataclass
class MergeAction:
    ir_ref: str
    runtime_path: str
    mode: str
    status: str
    detail: str = ""


@dataclass
class BuildRuntimeCodeResult:
    generated_patch_plans: list[str]
    generated_runtime_files: list[str]
    runtime_enabled: bool
    generated_items: int
    warnings: list[str]
    errors: list[str]
    report_path: str
    index_path: str
    merge_actions: list[MergeAction] = field(default_factory=list)
