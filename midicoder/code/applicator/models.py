from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ApplyOptions:
    workspace_root: Path
    version: str
    patches_dir: Path
    working_dir: Path
    force: bool = False
    dry_run: bool = False
    reindex: bool = True
    reindex_each_patch_plan: bool = True
    reset_target_files: bool = True


@dataclass(frozen=True)
class LoadedPatchPlan:
    runtime_path: str
    patch_plan_file: str
    patch_plan_path: Path
    operations: list[dict[str, Any]]


@dataclass
class ApplyFileResult:
    runtime_path: str
    status: str
    changed: bool = False
    backup_path: str | None = None
    restored: bool = False
    error: str | None = None


@dataclass
class ApplySummary:
    status: str
    version: str
    dry_run: bool
    reindex: bool
    reindex_each_patch_plan: bool
    total_files: int
    applied_count: int
    noop_count: int
    failed_count: int
    applied_files: list[str] = field(default_factory=list)
    failed_files: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    backup_paths: list[str] = field(default_factory=list)
    restored_files: list[str] = field(default_factory=list)
    report_path: str = ""
    reindex_errors: list[str] = field(default_factory=list)
    file_results: list[ApplyFileResult] = field(default_factory=list)

