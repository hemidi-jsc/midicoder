# coding: utf-8
"""
Mô-đun parser cho CP47 — Data Retention & Lifecycle Management.

Biến đổi raw dict (từ contract YAML) thành typed RetentionIR dataclass.
IR này là đầu vào cho các emitters (FastAPI, NestJS, Angular, React).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp_full_data_lifecycle.models import (
    RetentionAction,
    RetentionPolicy,
    RetentionPolicyType,
)


# ===========================================================================
# RetentionIR — Intermediate Representation
# ===========================================================================


@dataclass
class RetentionIR:
    """Intermediate Representation cho data retention & lifecycle.

    Chứa toàn bộ thông tin cần thiết để generate code:
    - policies: danh sách retention policies
    - enable_archival: có bật archive sang cold storage không
    - enable_purge: có bật purge không
    - enable_erasure: có bật GDPR erasure không
    - enable_scheduler: có bật scheduled scan không
    - default_retention_days: số ngày giữ mặc định
    - batch_size: số records xử lý mỗi batch

    Attributes:
        policies: Danh sách retention policies
        enable_archival: Bật archive sang cold storage
        enable_purge: Bật purge data
        enable_erasure: Bật GDPR erasure
        enable_scheduler: Bật scheduled scan
        default_retention_days: Số ngày giữ mặc định
        batch_size: Số records mỗi batch
    """
    policies: list[dict[str, Any]] = field(default_factory=list)
    enable_archival: bool = True
    enable_purge: bool = False
    enable_erasure: bool = True
    enable_scheduler: bool = True
    default_retention_days: int = 365
    batch_size: int = 1000

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RetentionIR sang dict."""
        return {
            "policies": self.policies,
            "enable_archival": self.enable_archival,
            "enable_purge": self.enable_purge,
            "enable_erasure": self.enable_erasure,
            "enable_scheduler": self.enable_scheduler,
            "default_retention_days": self.default_retention_days,
            "batch_size": self.batch_size,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RetentionIR":
        """Tạo RetentionIR từ dict."""
        return cls(
            policies=data.get("policies", []),
            enable_archival=data.get("enable_archival", True),
            enable_purge=data.get("enable_purge", False),
            enable_erasure=data.get("enable_erasure", True),
            enable_scheduler=data.get("enable_scheduler", True),
            default_retention_days=data.get("default_retention_days", 365),
            batch_size=data.get("batch_size", 1000),
        )


# ===========================================================================
# Parser Functions
# ===========================================================================


def parse_policies(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse retention policies từ raw dict.

    Args:
        data: Raw dict chứa policies

    Returns:
        Danh sách policy dicts
    """
    policies = []
    raw = data.get("policies", data.get("retention_policies", []))

    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                policies.append({
                    "policy_id": item.get("policy_id", item.get("id", "")),
                    "entity_type": item.get("entity_type", item.get("entity", "")),
                    "retention_days": item.get("retention_days", 365),
                    "action": item.get("action", "archive"),
                    "policy_type": item.get("policy_type", "time_based"),
                })

    return policies


def parse_retention_config(data: dict[str, Any]) -> dict[str, Any]:
    """Parse retention config từ raw dict.

    Args:
        data: Raw dict chứa retention config

    Returns:
        Config dict với default values
    """
    config = data.get("retention_config", data.get("config", {}))
    return {
        "enable_archival": config.get("enable_archival", data.get("enable_archival", True)),
        "enable_purge": config.get("enable_purge", data.get("enable_purge", False)),
        "enable_erasure": config.get("enable_erasure", data.get("enable_erasure", True)),
        "enable_scheduler": config.get("enable_scheduler", data.get("enable_scheduler", True)),
        "default_retention_days": config.get("default_retention_days", data.get("default_retention_days", 365)),
        "batch_size": config.get("batch_size", 1000),
    }


def parse_to_ir(data: dict[str, Any]) -> RetentionIR:
    """Parse raw dict thành RetentionIR.

    Entry point chính cho parser. Nhận raw dict từ contract YAML
    và trả về typed IR cho emitters.

    Args:
        data: Raw dict từ contract YAML

    Returns:
        RetentionIR typed
    """
    policies = parse_policies(data)
    config = parse_retention_config(data)

    return RetentionIR(
        policies=policies,
        enable_archival=config["enable_archival"],
        enable_purge=config["enable_purge"],
        enable_erasure=config["enable_erasure"],
        enable_scheduler=config["enable_scheduler"],
        default_retention_days=config["default_retention_days"],
        batch_size=config["batch_size"],
    )


# ===========================================================================
# CP65: Data Backup & Recovery — Parser (merged)
# ===========================================================================


from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp_full_data_lifecycle.models import (
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


def parse_backup_to_ir(data: dict[str, Any]) -> BackupIR:
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
