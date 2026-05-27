# coding: utf-8
"""
Mô-đun models cho CP65 — Data Backup & Recovery.

Định nghĩa các dataclass biểu diễn:
- BackupType: Loại backup (FULL, INCREMENTAL, DIFFERENTIAL, POINT_IN_TIME)
- StorageBackend: Backend lưu trữ (LOCAL, S3, GCS, AZURE_BLOB, K8S_VOLUME)
- ScheduleType: Loại lịch trình (CRON, FIXED_INTERVAL, ON_DEMAND, EVENT_TRIGGERED)
- BackupPolicy: Chính sách backup với loại, storage, lịch, retention
- RestorePoint: Điểm khôi phục từ backup
- RecoveryPlan: Kế hoạch disaster recovery với RTO/RPO
- RecoveryStep: Bước trong recovery plan
- BackupMonitor: Giám sát backup với cảnh báo

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class BackupType(str, Enum):
    """Loại backup.

    Attributes:
        FULL: Backup toàn bộ dữ liệu
        INCREMENTAL: Backup chỉ phần thay đổi kể từ backup cuối cùng
        DIFFERENTIAL: Backup phần thay đổi kể từ full backup cuối cùng
        POINT_IN_TIME: Backup để khôi phục đến thời điểm cụ thể
    """
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    POINT_IN_TIME = "point_in_time"


class StorageBackend(str, Enum):
    """Backend lưu trữ backup.

    Attributes:
        LOCAL: Lưu trữ cục bộ
        S3: Amazon S3
        GCS: Google Cloud Storage
        AZURE_BLOB: Azure Blob Storage
        K8S_VOLUME: Kubernetes Persistent Volume
    """
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"
    AZURE_BLOB = "azure_blob"
    K8S_VOLUME = "k8s_volume"


class ScheduleType(str, Enum):
    """Loại lịch trình backup.

    Attributes:
        CRON: Lịch theo biểu thức CRON
        FIXED_INTERVAL: Khoảng thời gian cố định
        ON_DEMAND: Theo yêu cầu
        EVENT_TRIGGERED: Kích hoạt bởi sự kiện
    """
    CRON = "cron"
    FIXED_INTERVAL = "fixed_interval"
    ON_DEMAND = "on_demand"
    EVENT_TRIGGERED = "event_triggered"


# ===========================================================================
# RecoveryStep
# ===========================================================================


@dataclass
class RecoveryStep:
    """Bước trong kế hoạch disaster recovery.

    Attributes:
        id: ID duy nhất của bước
        order: Thứ tự thực hiện
        action: Hành động thực hiện (restore_db, restore_files, restart_service)
        target: Target của hành động
        timeout_minutes: Thời gian timeout (phút)
        rollback_on_failure: Có rollback khi thất bại không
        dependencies: Danh sách ID của các bước phụ thuộc
    """
    id: str
    order: int
    action: str
    target: str
    timeout_minutes: int = 30
    rollback_on_failure: bool = True
    dependencies: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate RecoveryStep."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                entity="RecoveryStep",
                reason="id không được để trống",
            )
        if not self.action or not self.action.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                entity="RecoveryStep",
                reason="action không được để trống",
            )
        if self.order < 0:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                entity="RecoveryStep",
                reason="order phải >= 0",
            )
        if self.timeout_minutes < 1:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                entity="RecoveryStep",
                reason="timeout_minutes phải >= 1",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecoveryStep sang dict."""
        return {
            "id": self.id,
            "order": self.order,
            "action": self.action,
            "target": self.target,
            "timeout_minutes": self.timeout_minutes,
            "rollback_on_failure": self.rollback_on_failure,
            "dependencies": self.dependencies,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RecoveryStep":
        """Tạo RecoveryStep từ dict."""
        return cls(
            id=data["id"],
            order=data.get("order", 0),
            action=data.get("action", ""),
            target=data.get("target", ""),
            timeout_minutes=data.get("timeout_minutes", 30),
            rollback_on_failure=data.get("rollback_on_failure", True),
            dependencies=data.get("dependencies", []),
        )


# ===========================================================================
# BackupPolicy
# ===========================================================================


@dataclass
class BackupPolicy:
    """Chính sách backup.

    Attributes:
        id: ID duy nhất của chính sách
        name: Tên chính sách
        backup_type: Loại backup
        target: Target cần backup (database, file_path, volume)
        storage_backend: Backend lưu trữ
        schedule_type: Loại lịch trình
        schedule_cron: Biểu thức CRON (cho CRON schedule)
        retention_days: Số ngày giữ backup
        compression_enabled: Có nén không
        encryption_enabled: Có mã hóa không
        max_backup_size_mb: Kích thước tối đa backup (MB, 0 = không giới hạn)
        parallel_workers: Số worker song song
        metadata: Metadata bổ sung
    """
    id: str
    name: str
    backup_type: BackupType = BackupType.FULL
    target: str = ""
    storage_backend: StorageBackend = StorageBackend.LOCAL
    schedule_type: ScheduleType = ScheduleType.CRON
    schedule_cron: str = "0 2 * * *"
    retention_days: int = 30
    compression_enabled: bool = True
    encryption_enabled: bool = False
    max_backup_size_mb: int = 0
    parallel_workers: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate BackupPolicy."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                entity="BackupPolicy",
                reason="id không được để trống",
            )
        if not self.name or not self.name.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                entity="BackupPolicy",
                reason="name không được để trống",
            )
        if self.retention_days < 1:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                entity="BackupPolicy",
                reason="retention_days phải >= 1",
            )
        if self.parallel_workers < 1:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                entity="BackupPolicy",
                reason="parallel_workers phải >= 1",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển BackupPolicy sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "backup_type": self.backup_type.value,
            "target": self.target,
            "storage_backend": self.storage_backend.value,
            "schedule_type": self.schedule_type.value,
            "schedule_cron": self.schedule_cron,
            "retention_days": self.retention_days,
            "compression_enabled": self.compression_enabled,
            "encryption_enabled": self.encryption_enabled,
            "max_backup_size_mb": self.max_backup_size_mb,
            "parallel_workers": self.parallel_workers,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BackupPolicy":
        """Tạo BackupPolicy từ dict."""
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            backup_type=BackupType(data.get("backup_type", "full")),
            target=data.get("target", ""),
            storage_backend=StorageBackend(data.get("storage_backend", "local")),
            schedule_type=ScheduleType(data.get("schedule_type", "cron")),
            schedule_cron=data.get("schedule_cron", "0 2 * * *"),
            retention_days=data.get("retention_days", 30),
            compression_enabled=data.get("compression_enabled", True),
            encryption_enabled=data.get("encryption_enabled", False),
            max_backup_size_mb=data.get("max_backup_size_mb", 0),
            parallel_workers=data.get("parallel_workers", 1),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# RestorePoint
# ===========================================================================


@dataclass
class RestorePoint:
    """Điểm khôi phục từ backup.

    Attributes:
        id: ID duy nhất của restore point
        backup_policy_id: ID của chính sách backup
        timestamp: Thời điểm backup (ISO 8601 string)
        size_bytes: Kích thước backup (bytes)
        checksum: Checksum SHA256 của backup
        status: Trạng thái (completed, failed, in_progress, expired)
        storage_path: Đường dẫn lưu trữ backup
        metadata: Metadata bổ sung
    """
    id: str
    backup_policy_id: str
    timestamp: str = ""
    size_bytes: int = 0
    checksum: str = ""
    status: str = "completed"
    storage_path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate RestorePoint."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                entity="RestorePoint",
                reason="id không được để trống",
            )
        if not self.backup_policy_id or not self.backup_policy_id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                entity="RestorePoint",
                reason="backup_policy_id không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RestorePoint sang dict."""
        return {
            "id": self.id,
            "backup_policy_id": self.backup_policy_id,
            "timestamp": self.timestamp,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
            "status": self.status,
            "storage_path": self.storage_path,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RestorePoint":
        """Tạo RestorePoint từ dict."""
        return cls(
            id=data["id"],
            backup_policy_id=data.get("backup_policy_id", ""),
            timestamp=data.get("timestamp", ""),
            size_bytes=data.get("size_bytes", 0),
            checksum=data.get("checksum", ""),
            status=data.get("status", "completed"),
            storage_path=data.get("storage_path", ""),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# RecoveryPlan
# ===========================================================================


@dataclass
class RecoveryPlan:
    """Kế hoạch disaster recovery.

    Attributes:
        id: ID duy nhất của kế hoạch
        name: Tên kế hoạch
        rto_minutes: Recovery Time Objective (phút)
        rpo_minutes: Recovery Point Objective (phút)
        priority: Mức ưu tiên (critical, high, medium, low)
        steps: Danh sách RecoveryStep
        auto_trigger: Có tự động kích hoạt không
        notification_channels: Danh sách kênh thông báo
    """
    id: str
    name: str
    rto_minutes: int = 60
    rpo_minutes: int = 15
    priority: str = "high"
    steps: list[RecoveryStep] = field(default_factory=list)
    auto_trigger: bool = False
    notification_channels: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate RecoveryPlan."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                entity="RecoveryPlan",
                reason="id không được để trống",
            )
        if not self.name or not self.name.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                entity="RecoveryPlan",
                reason="name không được để trống",
            )
        if self.rto_minutes < 1:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                entity="RecoveryPlan",
                reason="rto_minutes phải >= 1",
            )
        if self.rpo_minutes < 1:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                entity="RecoveryPlan",
                reason="rpo_minutes phải >= 1",
            )
        valid_priorities = {"critical", "high", "medium", "low"}
        if self.priority not in valid_priorities:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                entity="RecoveryPlan",
                reason=f"priority phải là một trong: {', '.join(valid_priorities)}",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecoveryPlan sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "rto_minutes": self.rto_minutes,
            "rpo_minutes": self.rpo_minutes,
            "priority": self.priority,
            "steps": [s.to_dict() for s in self.steps],
            "auto_trigger": self.auto_trigger,
            "notification_channels": self.notification_channels,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RecoveryPlan":
        """Tạo RecoveryPlan từ dict."""
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            rto_minutes=data.get("rto_minutes", 60),
            rpo_minutes=data.get("rpo_minutes", 15),
            priority=data.get("priority", "high"),
            steps=[RecoveryStep.from_dict(s) for s in data.get("steps", [])],
            auto_trigger=data.get("auto_trigger", False),
            notification_channels=data.get("notification_channels", []),
        )


# ===========================================================================
# BackupMonitor
# ===========================================================================


@dataclass
class BackupMonitor:
    """Giám sát backup với cảnh báo.

    Attributes:
        id: ID duy nhất của monitor
        policy_ids: Danh sách ID của các chính sách cần giám sát
        alert_on_failure: Có cảnh báo khi backup thất bại không
        alert_on_lag_minutes: Cảnh báo khi backup chậm hơn số phút này
        slack_webhook: URL webhook Slack
        email_recipients: Danh sách email nhận cảnh báo
    """
    id: str
    policy_ids: list[str] = field(default_factory=list)
    alert_on_failure: bool = True
    alert_on_lag_minutes: int = 60
    slack_webhook: str = ""
    email_recipients: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate BackupMonitor."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.INVALID_ID,
                entity="BackupMonitor",
                reason="id không được để trống",
            )
        if self.alert_on_lag_minutes < 1:
            raise EM.raise_error(
                ErrorCode.INVALID_INPUT,
                entity="BackupMonitor",
                reason="alert_on_lag_minutes phải >= 1",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển BackupMonitor sang dict."""
        return {
            "id": self.id,
            "policy_ids": self.policy_ids,
            "alert_on_failure": self.alert_on_failure,
            "alert_on_lag_minutes": self.alert_on_lag_minutes,
            "slack_webhook": self.slack_webhook,
            "email_recipients": self.email_recipients,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BackupMonitor":
        """Tạo BackupMonitor từ dict."""
        return cls(
            id=data["id"],
            policy_ids=data.get("policy_ids", []),
            alert_on_failure=data.get("alert_on_failure", True),
            alert_on_lag_minutes=data.get("alert_on_lag_minutes", 60),
            slack_webhook=data.get("slack_webhook", ""),
            email_recipients=data.get("email_recipients", []),
        )
