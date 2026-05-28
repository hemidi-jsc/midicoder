# coding: utf-8
"""
Mô-đun models cho CP47 — Data Retention & Lifecycle Management + CP65 Backup & Recovery.

Định nghĩa các dataclass biểu diễn:
- RetentionAction: Hành động khi hết retention period (archive, purge, anonymize)
- RetentionPolicyType: Loại policy (time_based, event_based, status_based)
- RetentionPolicyStatus: Trạng thái policy (active, paused, expired)
- ArchiveStatus: Trạng thái archive (pending, archiving, archived, failed)
- ErasureStatus: Trạng thái erasure (pending, processing, completed, failed, partially_completed)
- RetentionPolicy: Chính sách retention cho entity type
- ArchivedRecord: Record đã được archive sang cold storage
- ErasureRequest: Yêu cầu xóa dữ liệu PII (GDPR)
- RetentionEngine: Engine xử lý retention operations (in-memory simulation)
- BackupType: Loại backup (FULL, INCREMENTAL, DIFFERENTIAL, POINT_IN_TIME) [CP65]
- StorageBackend: Backend lưu trữ (LOCAL, S3, GCS, AZURE_BLOB, K8S_VOLUME) [CP65]
- ScheduleType: Loại lịch trình (CRON, FIXED_INTERVAL, ON_DEMAND, EVENT_TRIGGERED) [CP65]
- BackupPolicy: Chính sách backup với loại, storage, lịch, retention [CP65]
- RestorePoint: Điểm khôi phục từ backup [CP65]
- RecoveryPlan: Kế hoạch disaster recovery với RTO/RPO [CP65]
- RecoveryStep: Bước trong recovery plan [CP65]
- BackupMonitor: Giám sát backup với cảnh báo [CP65]

KPI-005: CP Obligations Coverage (>= 2 obligations cho CP47).

Tác giả: Midicoder Team
Version: 2.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class RetentionAction(str, Enum):
    """Hành động khi hết retention period.

    - ARCHIVE: Chuyển sang cold storage
    - PURGE: Xóa (soft/hard delete)
    - ANONYMIZE: Giữ record, anonymize PII fields
    - ARCHIVE_THEN_PURGE: Archive trước, purge sau
    """
    ARCHIVE = "archive"
    PURGE = "purge"
    ANONYMIZE = "anonymize"
    ARCHIVE_THEN_PURGE = "archive_then_purge"


class RetentionPolicyType(str, Enum):
    """Loại retention policy.

    - TIME_BASED: Theo số ngày
    - EVENT_BASED: Theo trigger event
    - STATUS_BASED: Theo trạng thái record
    """
    TIME_BASED = "time_based"
    EVENT_BASED = "event_based"
    STATUS_BASED = "status_based"


class RetentionPolicyStatus(str, Enum):
    """Trạng thái retention policy.

    - ACTIVE: Đang hoạt động
    - PAUSED: Tạm ngưng
    - EXPIRED: Hết hạn
    """
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"


class ArchiveStatus(str, Enum):
    """Trạng thái archive.

    State machine: pending → archiving → archived | failed

    - PENDING: Đang chờ
    - ARCHIVING: Đang archive
    - ARCHIVED: Đã archive thành công
    - FAILED: Thất bại
    """
    PENDING = "pending"
    ARCHIVING = "archiving"
    ARCHIVED = "archived"
    FAILED = "failed"


class ErasureStatus(str, Enum):
    """Trạng thái erasure request.

    - PENDING: Đang chờ
    - PROCESSING: Đang xử lý
    - COMPLETED: Đã xóa thành công
    - FAILED: Thất bại
    - PARTIALLY_COMPLETED: Xóa một phần
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


# ===========================================================================
# RetentionPolicy
# ===========================================================================


@dataclass
class RetentionPolicy:
    """Chính sách retention cho entity type.

    Định nghĩa bao lâu giữ dữ liệu và hành động khi hết period.
    Mỗi policy áp dụng cho một entity type cụ thể.

    Attributes:
        policy_id: ID duy nhất của policy
        entity_type: Loại entity (vd: "Order", "User", "Transaction")
        retention_days: Số ngày giữ (0 = vô hạn)
        action: Hành động khi hết retention period
        policy_type: Loại policy (time_based, event_based, status_based)
        status: Trạng thái hiện tại của policy
        exemptions: Danh sách entity IDs không áp dụng policy
        description: Mô tả policy
        created_by: Người tạo policy
        tenant_id: ID tenant
        metadata: Dữ liệu bổ sung
        created_at: Thời điểm tạo
        updated_at: Thời điểm cập nhật cuối
    """
    policy_id: str
    entity_type: str
    retention_days: int = 365
    action: RetentionAction = RetentionAction.ARCHIVE
    policy_type: RetentionPolicyType = RetentionPolicyType.TIME_BASED
    status: RetentionPolicyStatus = RetentionPolicyStatus.ACTIVE
    exemptions: list[str] = field(default_factory=list)
    description: str = ""
    created_by: str = ""
    tenant_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate policy sau khi khởi tạo."""
        if not self.policy_id or not self.policy_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F29_RETENTION_POLICY_NOT_FOUND,
                reason="policy_id bắt buộc và không được để trống",
            )

        if not self.entity_type or not self.entity_type.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F29_RETENTION_POLICY_NOT_FOUND,
                reason="entity_type bắt buộc và không được để trống",
            )

        if self.retention_days < 0:
            raise EM.raise_error(
                ErrorCode.MDC-F29_RETENTION_DAYS_INVALID,
                reason=f"retention_days phải lớn hơn hoặc bằng 0, nhận được: {self.retention_days}",
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    @property
    def is_active(self) -> bool:
        """Trả về True nếu policy đang hoạt động."""
        return self.status == RetentionPolicyStatus.ACTIVE

    @property
    def is_unlimited(self) -> bool:
        """Trả về True nếu retention period vô hạn."""
        return self.retention_days == 0

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RetentionPolicy sang dict."""
        return {
            "policy_id": self.policy_id,
            "entity_type": self.entity_type,
            "retention_days": self.retention_days,
            "action": self.action.value,
            "policy_type": self.policy_type.value,
            "status": self.status.value,
            "exemptions": self.exemptions,
            "description": self.description,
            "created_by": self.created_by,
            "tenant_id": self.tenant_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RetentionPolicy":
        """Tạo RetentionPolicy từ dict."""
        return cls(
            policy_id=data["policy_id"],
            entity_type=data["entity_type"],
            retention_days=data.get("retention_days", 365),
            action=RetentionAction(data.get("action", "archive")),
            policy_type=RetentionPolicyType(data.get("policy_type", "time_based")),
            status=RetentionPolicyStatus(data.get("status", "active")),
            exemptions=data.get("exemptions", []),
            description=data.get("description", ""),
            created_by=data.get("created_by", ""),
            tenant_id=data.get("tenant_id", ""),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# ArchivedRecord
# ===========================================================================


@dataclass
class ArchivedRecord:
    """Record đã được archive sang cold storage.

    Lưu metadata và snapshot của record tại thời điểm archive.
    Cold storage location chứa dữ liệu đầy đủ.

    Attributes:
        archive_id: ID duy nhất của archive entry
        original_entity_type: Loại entity gốc
        original_entity_id: ID của entity gốc
        archive_reason: Lý do archive (retention_exceeded, manual)
        data_snapshot: Snapshot dữ liệu tại thời điểm archive
        archive_status: Trạng thái archive
        cold_storage_location: Path/URI trong cold storage
        tenant_id: ID tenant
        metadata: Dữ liệu bổ sung
        archived_at: Thời điểm archive
        restored_at: Thời điểm restore (nếu có)
    """
    archive_id: str
    original_entity_type: str
    original_entity_id: str
    archive_reason: str = "retention_exceeded"
    data_snapshot: dict[str, Any] = field(default_factory=dict)
    archive_status: ArchiveStatus = ArchiveStatus.PENDING
    cold_storage_location: str = ""
    tenant_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    archived_at: datetime | None = None
    restored_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate archived record sau khi khởi tạo."""
        if not self.archive_id or not self.archive_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F29_ARCHIVE_FAILED,
                reason="archive_id bắt buộc và không được để trống",
            )

        if not self.original_entity_type or not self.original_entity_type.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F29_ARCHIVE_FAILED,
                reason="original_entity_type bắt buộc và không được để trống",
            )

        if not self.original_entity_id or not self.original_entity_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F29_ARCHIVE_FAILED,
                reason="original_entity_id bắt buộc và không được để trống",
            )

        now = datetime.now(timezone.utc)
        if self.archived_at is None:
            self.archived_at = now

    @property
    def is_restorable(self) -> bool:
        """Trả về True nếu record có thể restore."""
        return self.archive_status == ArchiveStatus.ARCHIVED and self.restored_at is None

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ArchivedRecord sang dict."""
        return {
            "archive_id": self.archive_id,
            "original_entity_type": self.original_entity_type,
            "original_entity_id": self.original_entity_id,
            "archive_reason": self.archive_reason,
            "data_snapshot": self.data_snapshot,
            "archive_status": self.archive_status.value,
            "cold_storage_location": self.cold_storage_location,
            "tenant_id": self.tenant_id,
            "metadata": self.metadata,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "restored_at": self.restored_at.isoformat() if self.restored_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArchivedRecord":
        """Tạo ArchivedRecord từ dict."""
        return cls(
            archive_id=data["archive_id"],
            original_entity_type=data["original_entity_type"],
            original_entity_id=data["original_entity_id"],
            archive_reason=data.get("archive_reason", "retention_exceeded"),
            data_snapshot=data.get("data_snapshot", {}),
            archive_status=ArchiveStatus(data.get("archive_status", "pending")),
            cold_storage_location=data.get("cold_storage_location", ""),
            tenant_id=data.get("tenant_id", ""),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# ErasureRequest
# ===========================================================================


@dataclass
class ErasureRequest:
    """Yêu cầu xóa dữ liệu PII (GDPR Right to Erasure).

    Quét tất cả entities chứa PII của subject và anonymize/erase.
    Giữ full audit trail của erasure request.

    Attributes:
        request_id: ID duy nhất của erasure request
        subject_id: ID của subject cần xóa (user/email)
        request_reason: Lý do (gdpr_right_to_erasure, account_closure)
        entities_found: Danh sách entities chứa PII đã tìm thấy
        entities_erased: Danh sách entities đã xóa thành công
        entities_failed: Danh sách entities xóa thất bại
        erasure_status: Trạng thái hiện tại
        requested_by: Người yêu cầu
        tenant_id: ID tenant
        metadata: Dữ liệu bổ sung
        requested_at: Thời điểm yêu cầu
        completed_at: Thời điểm hoàn thành
    """
    request_id: str
    subject_id: str
    request_reason: str = "gdpr_right_to_erasure"
    entities_found: list[dict[str, Any]] = field(default_factory=list)
    entities_erased: list[dict[str, Any]] = field(default_factory=list)
    entities_failed: list[dict[str, Any]] = field(default_factory=list)
    erasure_status: ErasureStatus = ErasureStatus.PENDING
    requested_by: str = ""
    tenant_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    requested_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate erasure request sau khi khởi tạo."""
        if not self.request_id or not self.request_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F29_ERASURE_REQUEST_NOT_FOUND,
                reason="request_id bắt buộc và không được để trống",
            )

        if not self.subject_id or not self.subject_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F29_ERASURE_REQUEST_NOT_FOUND,
                reason="subject_id bắt buộc và không được để trống",
            )

        now = datetime.now(timezone.utc)
        if self.requested_at is None:
            self.requested_at = now

    @property
    def completion_percentage(self) -> float:
        """Trả về phần trăm hoàn thành."""
        if not self.entities_found:
            return 0.0
        return len(self.entities_erased) / len(self.entities_found) * 100

    @property
    def is_in_progress(self) -> bool:
        """Trả về True nếu erasure đang chạy."""
        return self.erasure_status in (
            ErasureStatus.PENDING,
            ErasureStatus.PROCESSING,
        )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ErasureRequest sang dict."""
        return {
            "request_id": self.request_id,
            "subject_id": self.subject_id,
            "request_reason": self.request_reason,
            "entities_found": self.entities_found,
            "entities_erased": self.entities_erased,
            "entities_failed": self.entities_failed,
            "erasure_status": self.erasure_status.value,
            "requested_by": self.requested_by,
            "tenant_id": self.tenant_id,
            "metadata": self.metadata,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ErasureRequest":
        """Tạo ErasureRequest từ dict."""
        return cls(
            request_id=data["request_id"],
            subject_id=data["subject_id"],
            request_reason=data.get("request_reason", "gdpr_right_to_erasure"),
            entities_found=data.get("entities_found", []),
            entities_erased=data.get("entities_erased", []),
            entities_failed=data.get("entities_failed", []),
            erasure_status=ErasureStatus(data.get("erasure_status", "pending")),
            requested_by=data.get("requested_by", ""),
            tenant_id=data.get("tenant_id", ""),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# RetentionEngine
# ===========================================================================


class RetentionEngine:
    """Engine xử lý retention operations (in-memory simulation).

    Quản lý retention policies, archive records, purge data,
    và xử lý GDPR erasure requests. Đây là in-memory simulation
    để testing và demonstration.

    Attributes:
        policies: Từ điển retention policies (policy_id -> RetentionPolicy)
        archives: Từ điển archived records (archive_id -> ArchivedRecord)
        erasures: Từ điển erasure requests (request_id -> ErasureRequest)
        exemptions: Từ điển exemptions (entity_id -> exemption_type)
    """

    def __init__(self) -> None:
        """Khởi tạo RetentionEngine."""
        self.policies: dict[str, RetentionPolicy] = {}
        self.archives: dict[str, ArchivedRecord] = {}
        self.erasures: dict[str, ErasureRequest] = {}
        self.exemptions: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Policy Management
    # ------------------------------------------------------------------

    def register_policy(self, policy: RetentionPolicy) -> RetentionPolicy:
        """Đăng ký retention policy mới.

        Args:
            policy: Policy cần đăng ký

        Returns:
            RetentionPolicy đã đăng ký
        """
        self.policies[policy.policy_id] = policy
        return policy

    def get_policy(self, policy_id: str) -> RetentionPolicy:
        """Lấy retention policy theo ID.

        Args:
            policy_id: ID của policy

        Returns:
            RetentionPolicy

        Raises:
            MidicoderError: Nếu policy không tồn tại
        """
        if policy_id not in self.policies:
            raise EM.raise_error(
                ErrorCode.MDC-F29_RETENTION_POLICY_NOT_FOUND,
                reason=f"Retention policy '{policy_id}' không tồn tại",
            )
        return self.policies[policy_id]

    def get_policy_for_entity(self, entity_type: str) -> RetentionPolicy | None:
        """Lấy policy active cho entity type.

        Args:
            entity_type: Loại entity (vd: "Order")

        Returns:
            RetentionPolicy hoặc None nếu không có
        """
        for policy in self.policies.values():
            if policy.entity_type == entity_type and policy.is_active:
                return policy
        return None

    def get_active_policies(self) -> list[RetentionPolicy]:
        """Lấy danh sách policies đang hoạt động.

        Returns:
            Danh sách RetentionPolicy đang active
        """
        return [p for p in self.policies.values() if p.is_active]

    def pause_policy(self, policy_id: str) -> RetentionPolicy:
        """Tạm ngưng retention policy.

        Args:
            policy_id: ID của policy

        Returns:
            RetentionPolicy đã pause
        """
        policy = self.get_policy(policy_id)
        policy.status = RetentionPolicyStatus.PAUSED
        policy.updated_at = datetime.now(timezone.utc)
        return policy

    # ------------------------------------------------------------------
    # Exemption Management
    # ------------------------------------------------------------------

    def add_exemption(self, entity_id: str, exemption_type: str) -> None:
        """Thêm exemption cho entity (không bị purge).

        Args:
            entity_id: ID của entity
            exemption_type: Loại exemption (legal_hold, compliance, audit_trail, manual)

        Raises:
            MidicoderError: Nếu exemption đã tồn tại
        """
        if entity_id in self.exemptions:
            raise EM.raise_error(
                ErrorCode.MDC-F29_EXEMPTION_ALREADY_EXISTS,
                reason=f"Exemption cho entity '{entity_id}' đã tồn tại",
            )
        self.exemptions[entity_id] = exemption_type

    def remove_exemption(self, entity_id: str) -> str:
        """Xóa exemption cho entity.

        Args:
            entity_id: ID của entity

        Returns:
            Loại exemption đã xóa

        Raises:
            MidicoderError: Nếu entity không có exemption
        """
        if entity_id not in self.exemptions:
            raise EM.raise_error(
                ErrorCode.MDC-F29_PURGE_NOT_ALLOWED,
                reason=f"Entity '{entity_id}' không có exemption để xóa",
            )
        return self.exemptions.pop(entity_id)

    def is_exempted(self, entity_id: str) -> bool:
        """Kiểm tra entity có exemption không.

        Args:
            entity_id: ID của entity

        Returns:
            True nếu entity có exemption
        """
        return entity_id in self.exemptions

    # ------------------------------------------------------------------
    # Archive Operations
    # ------------------------------------------------------------------

    def archive_record(
        self,
        entity_type: str,
        entity_id: str,
        data_snapshot: dict[str, Any],
        reason: str = "retention_exceeded",
    ) -> ArchivedRecord:
        """Archive record sang cold storage.

        Args:
            entity_type: Loại entity
            entity_id: ID của entity
            data_snapshot: Snapshot dữ liệu
            reason: Lý do archive

        Returns:
            ArchivedRecord đã tạo
        """
        archive = ArchivedRecord(
            archive_id=f"arc-{entity_type.lower()}-{entity_id}",
            original_entity_type=entity_type,
            original_entity_id=entity_id,
            archive_reason=reason,
            data_snapshot=data_snapshot,
            archive_status=ArchiveStatus.ARCHIVED,
            cold_storage_location=f"cold://{entity_type}/{entity_id}",
        )
        self.archives[archive.archive_id] = archive
        return archive

    def get_archive(self, archive_id: str) -> ArchivedRecord:
        """Lấy archived record theo ID.

        Args:
            archive_id: ID của archive

        Returns:
            ArchivedRecord

        Raises:
            MidicoderError: Nếu archive không tồn tại
        """
        if archive_id not in self.archives:
            raise EM.raise_error(
                ErrorCode.MDC-F29_RESTORE_FAILED,
                reason=f"Archive '{archive_id}' không tồn tại",
            )
        return self.archives[archive_id]

    def restore_record(self, archive_id: str) -> ArchivedRecord:
        """Restore record từ cold storage.

        Args:
            archive_id: ID của archive

        Returns:
            ArchivedRecord đã restore

        Raises:
            MidicoderError: Nếu archive không tồn tại hoặc không thể restore
        """
        archive = self.get_archive(archive_id)
        if not archive.is_restorable:
            raise EM.raise_error(
                ErrorCode.MDC-F29_RESTORE_FAILED,
                reason=f"Archive '{archive_id}' không thể restore (status: {archive.archive_status.value})",
            )
        archive.restored_at = datetime.now(timezone.utc)
        return archive

    # ------------------------------------------------------------------
    # Erasure Operations
    # ------------------------------------------------------------------

    def create_erasure_request(
        self,
        subject_id: str,
        reason: str = "gdpr_right_to_erasure",
        requested_by: str = "",
    ) -> ErasureRequest:
        """Tạo erasure request mới.

        Args:
            subject_id: ID của subject cần xóa
            reason: Lý do erasure
            requested_by: Người yêu cầu

        Returns:
            ErasureRequest đã tạo

        Raises:
            MidicoderError: Nếu đã có request đang chạy cho subject này
        """
        # Kiểm tra xem đã có request đang chạy không
        for req in self.erasures.values():
            if req.subject_id == subject_id and req.is_in_progress:
                raise EM.raise_error(
                    ErrorCode.MDC-F29_ERASURE_IN_PROGRESS,
                    reason=f"Erasure request đang chạy cho subject '{subject_id}'",
                )

        request = ErasureRequest(
            request_id=f"erase-{subject_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            subject_id=subject_id,
            request_reason=reason,
            requested_by=requested_by,
        )
        self.erasures[request.request_id] = request
        return request

    def get_erasure_request(self, request_id: str) -> ErasureRequest:
        """Lấy erasure request theo ID.

        Args:
            request_id: ID của request

        Returns:
            ErasureRequest

        Raises:
            MidicoderError: Nếu request không tồn tại
        """
        if request_id not in self.erasures:
            raise EM.raise_error(
                ErrorCode.MDC-F29_ERASURE_REQUEST_NOT_FOUND,
                reason=f"Erasure request '{request_id}' không tồn tại",
            )
        return self.erasures[request_id]

    def complete_erasure(
        self,
        request_id: str,
        status: ErasureStatus = ErasureStatus.COMPLETED,
    ) -> ErasureRequest:
        """Hoàn thành erasure request.

        Args:
            request_id: ID của request
            status: Trạng thái hoàn thành

        Returns:
            ErasureRequest đã hoàn thành
        """
        request = self.get_erasure_request(request_id)
        request.erasure_status = status
        request.completed_at = datetime.now(timezone.utc)
        return request

    # ------------------------------------------------------------------
    # Scan Operations
    # ------------------------------------------------------------------

    def scan_expiring_records(
        self,
        current_time: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Scan các records sắp hết retention period.

        Args:
            current_time: Thời gian hiện tại (mặc định: now)

        Returns:
            Danh sách records sắp hết retention với thông tin policy
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        expiring = []
        for policy in self.get_active_policies():
            if policy.is_unlimited:
                continue
            expiring.append({
                "policy_id": policy.policy_id,
                "entity_type": policy.entity_type,
                "retention_days": policy.retention_days,
                "action": policy.action.value,
            })
        return expiring

    def get_user_total_archived(self) -> int:
        """Đếm tổng số records đã archive.

        Returns:
            Số lượng records đã archive
        """
        return sum(1 for a in self.archives.values() if a.archive_status == ArchiveStatus.ARCHIVED)

    def get_user_total_erased(self) -> int:
        """Đếm tổng số erasure requests đã hoàn thành.

        Returns:
            Số lượng erasure requests completed
        """
        return sum(
            1 for e in self.erasures.values()
            if e.erasure_status in (ErasureStatus.COMPLETED, ErasureStatus.PARTIALLY_COMPLETED)
        )


# ===========================================================================
# CP65: Data Backup & Recovery — Models (merged)
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
