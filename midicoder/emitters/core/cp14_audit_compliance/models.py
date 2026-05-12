# coding: utf-8
"""
Mô-đun models cho Audit Trail & Compliance Generator (CP14).

Định nghĩa các dataclass biểu diễn:
- AuditActionType: Enum các loại hành động cần audit
- AuditLevel: Enum mức độ chi tiết audit
- ControlType: Enum loại compliance control
- EnforcementLevel: Enum mức độ enforce control
- StandardType: Enum compliance standards
- AuditTrail: Một audit log entry đơn lẻ
- AuditRule: Rule xác định khi nào cần ghi audit log
- ComplianceControl: Control point cho compliance enforcement
- AuditComplianceCollection: Collection chứa rules và controls

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class AuditActionType(str, Enum):
    """Enum các loại hành động cần audit."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    READ = "READ"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    CUSTOM = "CUSTOM"


class AuditLevel(str, Enum):
    """Enum mức độ chi tiết của audit log."""
    BASIC = "basic"
    DETAILED = "detailed"


class ControlType(str, Enum):
    """Enum loại compliance control."""
    PREVENTIVE = "preventive"
    DETECTIVE = "detective"
    CORRECTIVE = "corrective"


class EnforcementLevel(str, Enum):
    """Enum mức độ enforce control."""
    COMPILE = "compile"
    RUNTIME = "runtime"
    BOTH = "both"


class StandardType(str, Enum):
    """Enum compliance standards."""
    SOX = "sox"
    HIPAA = "hipaa"
    GDPR = "gdpr"
    PCI_DSS = "pci_dss"
    CUSTOM = "custom"


# ===========================================================================
# AuditTrail
# ===========================================================================


@dataclass
class AuditTrail:
    """
    Một audit log entry đơn lẻ — immutable record.

    Attributes:
        id: UUID định danh duy nhất
        timestamp: DateTime khi event xảy ra (UTC)
        action: Loại hành động (CREATE/UPDATE/DELETE/...)
        entity_type: Tên entity bị ảnh hưởng
        entity_id: ID của entity
        actor_id: User/system thực hiện hành động
        actor_type: "user" | "system" | "background_job"
        tenant_id: Multi-tenant isolation scope
        old_values: Giá trị trước khi thay đổi (optional)
        new_values: Giá trị sau khi thay đổi (optional)
        metadata: Metadata mở rộng (IP, user_agent, correlation_id...)
        immutable_hash: SHA-256 hash cho tamper-evidence (RX11)
    """
    action: AuditActionType
    entity_type: str
    entity_id: str
    actor_id: str
    actor_type: str
    tenant_id: str
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    old_values: dict[str, Any] = field(default_factory=dict)
    new_values: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    immutable_hash: str = ""

    def __post_init__(self) -> None:
        """Validate audit trail sau khi khởi tạo."""
        # Actor type phải hợp lệ
        valid_actor_types = {"user", "system", "background_job"}
        if self.actor_type not in valid_actor_types:
            EM.raise_error(
                ErrorCode.CP14_AUDIT_INVALID_ACTOR_TYPE,
                actor_type=self.actor_type,
                valid_types=list(valid_actor_types)
            )
        # Entity type không được để trống
        if not self.entity_type or not self.entity_type.strip():
            EM.raise_error(ErrorCode.CP14_AUDIT_EMPTY_ID, field="entity_type")
        # Entity id không được để trống
        if not self.entity_id or not self.entity_id.strip():
            EM.raise_error(ErrorCode.CP14_AUDIT_EMPTY_ID, field="entity_id")
        # Auto-generate immutable hash nếu chưa có
        if not self.immutable_hash:
            self.immutable_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """
        Tính toán SHA-256 hash cho entry này (tamper-evidence).

        Returns:
            SHA-256 hash string
        """
        data = {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "tenant_id": self.tenant_id,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "metadata": self.metadata,
        }
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def verify_hash(self) -> bool:
        """
        Xác minh hash entry có đúng không (tamper detection).

        Returns:
            True nếu hash khớp, False nếu bị tamper
        """
        return self.immutable_hash == self._compute_hash()

    def to_dict(self) -> dict[str, Any]:
        """Chuyển audit trail sang dict format."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "tenant_id": self.tenant_id,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "metadata": self.metadata,
            "immutable_hash": self.immutable_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditTrail":
        """Tạo AuditTrail từ dict."""
        return cls(
            id=data.get("id", str(uuid4())),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(timezone.utc),
            action=AuditActionType(data.get("action", "CREATE")),
            entity_type=data.get("entity_type", ""),
            entity_id=data.get("entity_id", ""),
            actor_id=data.get("actor_id", ""),
            actor_type=data.get("actor_type", "system"),
            tenant_id=data.get("tenant_id", ""),
            old_values=data.get("old_values", {}),
            new_values=data.get("new_values", {}),
            metadata=data.get("metadata", {}),
            immutable_hash=data.get("immutable_hash", ""),
        )


# ===========================================================================
# AuditRule
# ===========================================================================


@dataclass
class AuditRule:
    """
    Rule xác định khi nào cần ghi audit log.

    Attributes:
        id: Định danh rule
        name: Tên rule (tiếng Việt)
        enabled: Có kích hoạt rule không (default True)
        entity_types: List entity types áp dụng rule
        actions: List action types cần audit
        audit_level: Mức độ chi tiết (basic/detailed)
        retention_days: Số ngày giữ audit log hot storage
        archive_after_days: Số ngày trước khi archive sang cold
        compliance_tags: List compliance standards
        description: Mô tả rule (tiếng Việt)
    """
    id: str
    name: str
    entity_types: list[str] = field(default_factory=list)
    actions: list[AuditActionType] = field(default_factory=list)
    enabled: bool = True
    audit_level: AuditLevel = AuditLevel.BASIC
    retention_days: int = 365
    archive_after_days: int = 90
    compliance_tags: list[str] = field(default_factory=list)
    description: str = ""

    def __post_init__(self) -> None:
        """Validate audit rule sau khi khởi tạo."""
        # ID không được để trống
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.CP14_AUDIT_EMPTY_ID, field="audit_rule.id")
        # Retention phải > 0
        if self.retention_days < 1:
            EM.raise_error(ErrorCode.CP14_AUDIT_RETENTION_INVALID, days=self.retention_days)
        # Archive không được > retention
        if self.archive_after_days > self.retention_days:
            EM.raise_error(
                ErrorCode.CP14_AUDIT_ARCHIVE_EXCEEDS_RETENTION,
                archive=self.archive_after_days,
                retention=self.retention_days
            )

    def matches(self, entity_type: str, action: AuditActionType) -> bool:
        """
        Kiểm tra rule có áp dụng cho entity_type + action không.

        Args:
            entity_type: Tên entity cần kiểm tra
            action: Hành động cần kiểm tra

        Returns:
            True nếu rule áp dụng và đang enabled
        """
        if not self.enabled:
            return False
        # Nếu không có entity_types filter, áp dụng cho tất cả
        if not self.entity_types or entity_type in self.entity_types:
            # Nếu không có actions filter, áp dụng cho tất cả
            if not self.actions or action in self.actions:
                return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Chuyển rule sang dict format."""
        return {
            "id": self.id,
            "name": self.name,
            "enabled": self.enabled,
            "entity_types": self.entity_types,
            "actions": [a.value for a in self.actions],
            "audit_level": self.audit_level.value,
            "retention_days": self.retention_days,
            "archive_after_days": self.archive_after_days,
            "compliance_tags": self.compliance_tags,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditRule":
        """Tạo AuditRule từ dict."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            entity_types=data.get("entity_types", []),
            actions=[AuditActionType(a) for a in data.get("actions", [])],
            enabled=data.get("enabled", True),
            audit_level=AuditLevel(data.get("audit_level", "basic")),
            retention_days=data.get("retention_days", 365),
            archive_after_days=data.get("archive_after_days", 90),
            compliance_tags=data.get("compliance_tags", []),
            description=data.get("description", ""),
        )


# ===========================================================================
# ComplianceControl
# ===========================================================================


@dataclass
class ComplianceControl:
    """
    Control point cho compliance enforcement.

    Attributes:
        id: Định danh control
        name: Tên control (tiếng Việt)
        standard: Compliance standard (sox, hipaa, gdpr...)
        control_type: Loại control (preventive/detective/corrective)
        enforcement_level: Mức độ enforce (compile/runtime/both)
        enabled: Có kích hoạt control không (default True)
        audit_rule_id: Reference đến AuditRule (optional)
        description: Mô tả control (tiếng Việt)
    """
    id: str
    name: str
    standard: StandardType
    control_type: ControlType
    enforcement_level: EnforcementLevel
    enabled: bool = True
    audit_rule_id: Optional[str] = None
    description: str = ""

    def __post_init__(self) -> None:
        """Validate compliance control sau khi khởi tạo."""
        # ID không được để trống
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.CP14_AUDIT_EMPTY_ID, field="compliance_control.id")

    def is_active(self) -> bool:
        """Kiểm tra control có đang active không."""
        return self.enabled

    def requires_runtime_check(self) -> bool:
        """Kiểm tra control có cần runtime check không."""
        return self.enforcement_level in (EnforcementLevel.RUNTIME, EnforcementLevel.BOTH)

    def requires_compile_check(self) -> bool:
        """Kiểm tra control có cần compile-time check không."""
        return self.enforcement_level in (EnforcementLevel.COMPILE, EnforcementLevel.BOTH)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển control sang dict format."""
        return {
            "id": self.id,
            "name": self.name,
            "standard": self.standard.value,
            "control_type": self.control_type.value,
            "enforcement_level": self.enforcement_level.value,
            "enabled": self.enabled,
            "audit_rule_id": self.audit_rule_id,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComplianceControl":
        """Tạo ComplianceControl từ dict."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            standard=StandardType(data.get("standard", "custom")),
            control_type=ControlType(data.get("control_type", "preventive")),
            enforcement_level=EnforcementLevel(data.get("enforcement_level", "runtime")),
            enabled=data.get("enabled", True),
            audit_rule_id=data.get("audit_rule_id"),
            description=data.get("description", ""),
        )


# ===========================================================================
# AuditComplianceCollection
# ===========================================================================


@dataclass
class AuditComplianceCollection:
    """
    Collection chứa tất cả audit rules và compliance controls.

    Dùng làm output của AuditComplianceParser và input cho Stack Emitters.

    Attributes:
        audit_rules: Danh sách AuditRule
        compliance_controls: Danh sách ComplianceControl
    """
    audit_rules: list[AuditRule] = field(default_factory=list)
    compliance_controls: list[ComplianceControl] = field(default_factory=list)

    def add_rule(self, rule: AuditRule) -> None:
        """Thêm audit rule vào collection."""
        # Kiểm tra duplicate id
        if self.get_rule_by_id(rule.id):
            EM.raise_error(ErrorCode.DSL_DUPLICATE_NODE_ID, id=rule.id, kind="audit_rule")
        self.audit_rules.append(rule)

    def add_control(self, control: ComplianceControl) -> None:
        """Thêm compliance control vào collection."""
        # Kiểm tra duplicate id
        if self.get_control_by_id(control.id):
            EM.raise_error(ErrorCode.DSL_DUPLICATE_NODE_ID, id=control.id, kind="compliance_control")
        self.compliance_controls.append(control)

    def get_rule_by_id(self, rule_id: str) -> Optional[AuditRule]:
        """Tìm audit rule theo ID."""
        for rule in self.audit_rules:
            if rule.id == rule_id:
                return rule
        return None

    def get_control_by_id(self, control_id: str) -> Optional[ComplianceControl]:
        """Tìm compliance control theo ID."""
        for control in self.compliance_controls:
            if control.id == control_id:
                return control
        return None

    def get_active_rules(self) -> list[AuditRule]:
        """Lọc các audit rules đang active."""
        return [r for r in self.audit_rules if r.enabled]

    def get_active_controls(self) -> list[ComplianceControl]:
        """Lọc các compliance controls đang active."""
        return [c for c in self.compliance_controls if c.enabled]

    def matches_any_rule(self, entity_type: str, action: AuditActionType) -> bool:
        """
        Kiểm tra có rule nào áp dụng cho entity_type + action không.

        Args:
            entity_type: Tên entity
            action: Hành động

        Returns:
            True nếu có ít nhất 1 active rule matches
        """
        for rule in self.get_active_rules():
            if rule.matches(entity_type, action):
                return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Chuyển collection sang dict format."""
        return {
            "audit_rules": [r.to_dict() for r in self.audit_rules],
            "compliance_controls": [c.to_dict() for c in self.compliance_controls],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditComplianceCollection":
        """Tạo AuditComplianceCollection từ dict."""
        result = cls()
        result.audit_rules = [AuditRule.from_dict(r) for r in data.get("audit_rules", [])]
        result.compliance_controls = [ComplianceControl.from_dict(c) for c in data.get("compliance_controls", [])]
        return result


# ===========================================================================
# Immutable Audit Ledger
# ===========================================================================


class LedgerStorageBackend(str, Enum):
    """
    Backend cho immutable audit ledger.

    - database: Relational database (append-only table + hash chain)
    - blockchain: Permissioned blockchain (Hyperledger, Corda)
    - append_only_store: WORM storage (Write Once Read Many)
    - signed_chain: Cryptographically signed hash chain (lightweight)
    """
    DATABASE = "database"
    BLOCKCHAIN = "blockchain"
    APPEND_ONLY_STORE = "append_only_store"
    SIGNED_CHAIN = "signed_chain"


class LedgerVerificationMode(str, Enum):
    """
    Chế độ verification cho ledger.

    - hash_chain: Verify SHA-256 hash chain (prev_hash → curr_hash)
    - merkle_tree: Merkle tree proof (batch verification)
    - digital_signature: Digital signature (RSA/ECDSA)
    - combined: Hash chain + digital signature
    """
    HASH_CHAIN = "hash_chain"
    MERKLE_TREE = "merkle_tree"
    DIGITAL_SIGNATURE = "digital_signature"
    COMBINED = "combined"


@dataclass
class LedgerEntry:
    """
    Một entry trong immutable audit ledger — chained hash để detect tampering.

    Each entry links to its predecessor via prev_hash, forming an immutable
    chain. Breaking any link is detectable by recomputing hashes.

    Attributes:
        entry_id: UUID định danh duy nhất
        audit_trail_id: Reference đến audit trail entry
        sequence_number: Sequence number trong ledger (tăng dần)
        hash: SHA-256 hash của entry data
        prev_hash: Hash của entry trước đó (chain link)
        timestamp: Thời điểm ghi entry (UTC)
        data_hash: SHA-256 hash của audit trail data
        signature: Digital signature (optional, combined mode)
        metadata: Metadata mở rộng
    """
    entry_id: str = field(default_factory=lambda: str(uuid4()))
    audit_trail_id: str = ""
    sequence_number: int = 0
    hash: str = ""
    prev_hash: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data_hash: str = ""
    signature: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate ledger entry sau khi khởi tạo."""
        if self.sequence_number < 0:
            EM.raise_error(
                ErrorCode.CP14_AUDIT_EMPTY_ID,
                field="sequence_number",
                reason="Sequence number phải >= 0"
            )

    def compute_hash(self) -> str:
        """
        Tính toán SHA-256 hash cho entry này (chained).

        Hash = SHA-256(prev_hash + sequence_number + data_hash + timestamp)

        Returns:
            SHA-256 hash string
        """
        data = {
            "prev_hash": self.prev_hash,
            "sequence_number": self.sequence_number,
            "data_hash": self.data_hash,
            "timestamp": self.timestamp.isoformat(),
            "audit_trail_id": self.audit_trail_id,
        }
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def verify_chain(self) -> bool:
        """
        Xác minh hash chain entry có đúng không.

        Returns:
            True nếu hash khớp, False nếu bị tamper
        """
        if not self.hash:
            return True
        return self.hash == self.compute_hash()

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ledger entry sang dict format."""
        return {
            "entry_id": self.entry_id,
            "audit_trail_id": self.audit_trail_id,
            "sequence_number": self.sequence_number,
            "hash": self.hash,
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp.isoformat(),
            "data_hash": self.data_hash,
            "signature": self.signature,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LedgerEntry":
        """Tạo LedgerEntry từ dict."""
        return cls(
            entry_id=data.get("entry_id", ""),
            audit_trail_id=data.get("audit_trail_id", ""),
            sequence_number=data.get("sequence_number", 0),
            hash=data.get("hash", ""),
            prev_hash=data.get("prev_hash", ""),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
            data_hash=data.get("data_hash", ""),
            signature=data.get("signature", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ImmutableLedgerConfig:
    """
    Configuration cho immutable audit ledger.

    Immutable ledger ghi audit events vào chain của entries — mỗi entry
    link đến predecessor. Tampering bất kỳ entry nào là detectable.

    Attributes:
        enabled: Có enable immutable ledger không
        backend: Storage backend (database, blockchain, append_only_store, signed_chain)
        verification_mode: Verification mode (hash_chain, merkle_tree, digital_signature, combined)
        batch_size: Số entries trong 1 batch commit
        enable_merkle_root: Tính merkle root mỗi N entries
        merkle_batch_size: Số entries cho merkle tree
        retention_days: Bao lâu giữ entries trong ledger (0 = forever)
        sign_key_path: Đường dẫn đến signing key (cho digital signature mode)
        description: Mô tả ledger config
    """
    enabled: bool = True
    backend: LedgerStorageBackend = LedgerStorageBackend.DATABASE
    verification_mode: LedgerVerificationMode = LedgerVerificationMode.HASH_CHAIN
    batch_size: int = 100
    enable_merkle_root: bool = False
    merkle_batch_size: int = 1000
    retention_days: int = 0
    sign_key_path: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        """Validate ledger config sau khi khởi tạo."""
        if self.batch_size < 1:
            self.batch_size = 100
        if self.merkle_batch_size < 1:
            self.merkle_batch_size = 1000
        if self.retention_days < 0:
            self.retention_days = 0

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ledger config sang dict format."""
        return {
            "enabled": self.enabled,
            "backend": self.backend.value,
            "verification_mode": self.verification_mode.value,
            "batch_size": self.batch_size,
            "enable_merkle_root": self.enable_merkle_root,
            "merkle_batch_size": self.merkle_batch_size,
            "retention_days": self.retention_days,
            "sign_key_path": self.sign_key_path,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImmutableLedgerConfig":
        """Tạo ImmutableLedgerConfig từ dict."""
        return cls(
            enabled=data.get("enabled", True),
            backend=LedgerStorageBackend(data.get("backend", "database")),
            verification_mode=LedgerVerificationMode(data.get("verification_mode", "hash_chain")),
            batch_size=data.get("batch_size", 100),
            enable_merkle_root=data.get("enable_merkle_root", False),
            merkle_batch_size=data.get("merkle_batch_size", 1000),
            retention_days=data.get("retention_days", 0),
            sign_key_path=data.get("sign_key_path", ""),
            description=data.get("description", ""),
        )


# ===========================================================================
# Compliance Report
# ===========================================================================


class ReportFormat(str, Enum):
    """
    Định dạng compliance report.

    - pdf: PDF document
    - csv: CSV spreadsheet
    - json: JSON structured data
    - html: HTML report
    - xlsx: Excel spreadsheet
    """
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"
    HTML = "html"
    XLSX = "xlsx"


class ReportScope(str, Enum):
    """
    Phạm vi compliance report.

    - all: Toàn bộ audit events
    - entity: Lọc theo entity type
    - actor: Lọc theo actor (user)
    - time_range: Lọc theo khoảng thời gian
    - tenant: Lọc theo tenant
    - action: Lọc theo hành động
    """
    ALL = "all"
    ENTITY = "entity"
    ACTOR = "actor"
    TIME_RANGE = "time_range"
    TENANT = "tenant"
    ACTION = "action"


class ComplianceStandard(str, Enum):
    """
    Compliance standard.

    - soc2: SOC 2 Type II
    - gdpr: GDPR (General Data Protection Regulation)
    - hipaa: HIPAA (Health Insurance Portability and Accountability)
    - pci_dss: PCI DSS (Payment Card Industry)
    - iso27001: ISO/IEC 27001
    - sox: Sarbanes-Oxley
    - custom: Custom compliance framework
    """
    SOC2 = "soc2"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"
    SOX = "sox"
    CUSTOM = "custom"


@dataclass
class ComplianceReportConfig:
    """
    Configuration cho compliance report generation.

    Compliance report tổng hợp audit events, kiểm tra against controls,
    và generate report cho auditor/reviewer.

    Attributes:
        report_format: Định dạng output (pdf, csv, json, html, xlsx)
        standard: Compliance standard (soc2, gdpr, hipaa, pci_dss, ...)
        scope: Phạm vi report (all, entity, actor, time_range, tenant, action)
        scope_filter: Filter value cho scope (vd: entity type, actor_id)
        start_date: Start date cho time_range scope
        end_date: End date cho time_range scope
        include_evidence: Có include evidence (old/new values) không
        include_ledger_verification: Có include ledger chain verification không
        auto_generate: Có auto-generate report không (scheduled)
        schedule_cron: Cron expression cho auto-generate (vd: "0 0 1 * *")
        recipients: Email recipients cho auto-generated reports
        description: Mô tả report config
    """
    report_format: ReportFormat = ReportFormat.PDF
    standard: ComplianceStandard = ComplianceStandard.SOC2
    scope: ReportScope = ReportScope.ALL
    scope_filter: str = ""
    start_date: str = ""
    end_date: str = ""
    include_evidence: bool = True
    include_ledger_verification: bool = True
    auto_generate: bool = False
    schedule_cron: str = ""
    recipients: list[str] = field(default_factory=list)
    description: str = ""

    def __post_init__(self) -> None:
        """Validate compliance report config sau khi khởi tạo."""
        if self.schedule_cron and not self.auto_generate:
            self.auto_generate = True

    def to_dict(self) -> dict[str, Any]:
        """Chuyển compliance report config sang dict format."""
        return {
            "report_format": self.report_format.value,
            "standard": self.standard.value,
            "scope": self.scope.value,
            "scope_filter": self.scope_filter,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "include_evidence": self.include_evidence,
            "include_ledger_verification": self.include_ledger_verification,
            "auto_generate": self.auto_generate,
            "schedule_cron": self.schedule_cron,
            "recipients": self.recipients,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComplianceReportConfig":
        """Tạo ComplianceReportConfig từ dict."""
        return cls(
            report_format=ReportFormat(data.get("report_format", "pdf")),
            standard=ComplianceStandard(data.get("standard", "soc2")),
            scope=ReportScope(data.get("scope", "all")),
            scope_filter=data.get("scope_filter", ""),
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date", ""),
            include_evidence=data.get("include_evidence", True),
            include_ledger_verification=data.get("include_ledger_verification", True),
            auto_generate=data.get("auto_generate", False),
            schedule_cron=data.get("schedule_cron", ""),
            recipients=data.get("recipients", []),
            description=data.get("description", ""),
        )


@dataclass
class ReportSummary:
    """
    Summary statistics cho compliance report.

    Attributes:
        total_events: Tổng số audit events trong report
        events_by_action: Count events theo action type
        events_by_entity: Count events theo entity type
        events_by_actor: Count events theo actor
        violations_count: Số violations (events vi phạm control)
        violations: Danh sách violation details
        ledger_verified: Ledger chain có verified không
        ledger_breaks: Số breaks trong ledger chain
        period_start: Start period
        period_end: End period
        generated_at: Thời điểm generate report
    """
    total_events: int = 0
    events_by_action: dict[str, int] = field(default_factory=dict)
    events_by_entity: dict[str, int] = field(default_factory=dict)
    events_by_actor: dict[str, int] = field(default_factory=dict)
    violations_count: int = 0
    violations: list[dict[str, Any]] = field(default_factory=list)
    ledger_verified: bool = True
    ledger_breaks: int = 0
    period_start: str = ""
    period_end: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Chuyển report summary sang dict format."""
        return {
            "total_events": self.total_events,
            "events_by_action": self.events_by_action,
            "events_by_entity": self.events_by_entity,
            "events_by_actor": self.events_by_actor,
            "violations_count": self.violations_count,
            "violations": self.violations,
            "ledger_verified": self.ledger_verified,
            "ledger_breaks": self.ledger_breaks,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReportSummary":
        """Tạo ReportSummary từ dict."""
        return cls(
            total_events=data.get("total_events", 0),
            events_by_action=data.get("events_by_action", {}),
            events_by_entity=data.get("events_by_entity", {}),
            events_by_actor=data.get("events_by_actor", {}),
            violations_count=data.get("violations_count", 0),
            violations=data.get("violations", []),
            ledger_verified=data.get("ledger_verified", True),
            ledger_breaks=data.get("ledger_breaks", 0),
            period_start=data.get("period_start", ""),
            period_end=data.get("period_end", ""),
            generated_at=data.get("generated_at", datetime.now(timezone.utc).isoformat()),
        )