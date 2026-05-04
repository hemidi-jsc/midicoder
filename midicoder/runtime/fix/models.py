"""Data models for runtime fix."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PatchPlanItem:
    """A single patch plan item."""

    runtime_path: str
    operation: str  # write, edit, delete
    ir_ref: str
    patches: list[dict] = field(default_factory=list)


@dataclass
class RuntimeFixResult:
    """Result of runtime fix generation."""

    success: bool
    patch_plans: list[PatchPlanItem] = field(default_factory=list)
    patches_dir: str = ""
    errors: list[str] = field(default_factory=list)
