# coding: utf-8
"""
Mô-đun parser cho CP65 — Data Backup & Recovery.

Parse DSL dict (từ contract YAML) sang BackupIR — Intermediate Representation
cho backup policies, restore points, recovery plans, và monitors.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp65_backup_recovery.models import (
    BackupMonitor,
    BackupPolicy,
    RecoveryPlan,
    RestorePoint,
)


@dataclass
class BackupIR:
    """Intermediate Representation cho CP65.

    Gom tập tất cả cấu hình backup và recovery từ DSL, bao gồm
    backup policies, restore points, recovery plans, và monitors.

    Attributes:
        backup_policies: Danh sách chính sách backup
        restore_points: Danh sách điểm khôi phục
        recovery_plans: Danh sách kế hoạch recovery
        monitors: Danh sách backup monitors
        default_retention_days: Số ngày retention mặc định
        enable_encryption: Có bật mã hóa mặc định không
    """
    backup_policies: list[BackupPolicy] = field(default_factory=list)
    restore_points: list[RestorePoint] = field(default_factory=list)
    recovery_plans: list[RecoveryPlan] = field(default_factory=list)
    monitors: list[BackupMonitor] = field(default_factory=list)
    default_retention_days: int = 30
    enable_encryption: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Chuyển BackupIR sang dict."""
        return {
            "backup_policies": [p.to_dict() for p in self.backup_policies],
            "restore_points": [r.to_dict() for r in self.restore_points],
            "recovery_plans": [p.to_dict() for p in self.recovery_plans],
            "monitors": [m.to_dict() for m in self.monitors],
            "default_retention_days": self.default_retention_days,
            "enable_encryption": self.enable_encryption,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BackupIR":
        """Tạo BackupIR từ dict."""
        return cls(
            backup_policies=[BackupPolicy.from_dict(p) for p in data.get("backup_policies", [])],
            restore_points=[RestorePoint.from_dict(r) for r in data.get("restore_points", [])],
            recovery_plans=[RecoveryPlan.from_dict(p) for p in data.get("recovery_plans", [])],
            monitors=[BackupMonitor.from_dict(m) for m in data.get("monitors", [])],
            default_retention_days=data.get("default_retention_days", 30),
            enable_encryption=data.get("enable_encryption", False),
        )


def parse_backup_policies(data: dict[str, Any]) -> list[BackupPolicy]:
    """Parse danh sách backup policies từ DSL dict.

    Args:
        data: DSL dict với key 'backup_policies'

    Returns:
        Danh sách BackupPolicy
    """
    raw = data.get("backup_policies", [])
    return [BackupPolicy.from_dict(p) for p in raw]


def parse_restore_points(data: dict[str, Any]) -> list[RestorePoint]:
    """Parse danh sách restore points từ DSL dict.

    Args:
        data: DSL dict với key 'restore_points'

    Returns:
        Danh sách RestorePoint
    """
    raw = data.get("restore_points", [])
    return [RestorePoint.from_dict(r) for r in raw]


def parse_recovery_plans(data: dict[str, Any]) -> list[RecoveryPlan]:
    """Parse danh sách recovery plans từ DSL dict.

    Args:
        data: DSL dict với key 'recovery_plans'

    Returns:
        Danh sách RecoveryPlan
    """
    raw = data.get("recovery_plans", [])
    return [RecoveryPlan.from_dict(p) for p in raw]


def parse_monitors(data: dict[str, Any]) -> list[BackupMonitor]:
    """Parse danh sách backup monitors từ DSL dict.

    Args:
        data: DSL dict với key 'monitors'

    Returns:
        Danh sách BackupMonitor
    """
    raw = data.get("monitors", [])
    return [BackupMonitor.from_dict(m) for m in raw]


def parse_to_ir(data: dict[str, Any]) -> BackupIR:
    """Parse DSL dict thành BackupIR.

    Args:
        data: DSL dict với backup_policies, restore_points,
              recovery_plans, monitors

    Returns:
        BackupIR gom tập tất cả parsed data
    """
    return BackupIR(
        backup_policies=parse_backup_policies(data),
        restore_points=parse_restore_points(data),
        recovery_plans=parse_recovery_plans(data),
        monitors=parse_monitors(data),
        default_retention_days=data.get("default_retention_days", 30),
        enable_encryption=data.get("enable_encryption", False),
    )


__all__ = [
    "BackupIR",
    "parse_backup_policies",
    "parse_restore_points",
    "parse_recovery_plans",
    "parse_monitors",
    "parse_to_ir",
]
