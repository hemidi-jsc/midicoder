"""
Command DSL Models.

Định nghĩa các models cho Command pattern với đầy đủ support cho 100 industries.

Author: Midicoder Team
Version: 2.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class EffectType(str, Enum):
    """
    Loại effects được hỗ trợ.

    P0 - Core Effects:
    - CREATE_RECORD: Tạo record mới
    - UPDATE_RECORD: Cập nhật record
    - DELETE_RECORD: Xóa record
    - PUBLISH_EVENT: Publish event

    P0 - Transaction Effects:
    - BEGIN_TRANSACTION: Bắt đầu transaction
    - COMMIT_TRANSACTION: Commit transaction
    - ROLLBACK_TRANSACTION: Rollback transaction

    P1 - Extended Effects:
    - QUERY_RECORDS: Query trong command
    - UPSERT_RECORD: Upsert record
    - BATCH_CREATE: Batch create
    - BATCH_UPDATE: Batch update

    P1 - Integration Effects:
    - CALL_EXTERNAL_API: Gọi external API
    - SEND_EMAIL: Gửi email
    - SEND_SMS: Gửi SMS
    - PUSH_NOTIFICATION: Gửi push notification
    - WEBHOOK: Gọi webhook

    P1 - Observability Effects:
    - WRITE_AUDIT_LOG: Ghi audit log
    - RECORD_METRIC: Ghi metric

    P1 - Compliance Effects:
    - CHECK_COMPLIANCE: Check compliance gate
    - MASK_PII: Mask PII data

    P2 - Advanced Effects:
    - SCHEDULE_JOB: Schedule background job
    - BEGIN_SAGA: Begin SAGA pattern
    - COMPENSATE: Compensation action
    """

    # Core
    CREATE_RECORD = "create_record"
    UPDATE_RECORD = "update_record"
    DELETE_RECORD = "delete_record"
    PUBLISH_EVENT = "publish_event"

    # Transaction
    BEGIN_TRANSACTION = "begin_transaction"
    COMMIT_TRANSACTION = "commit_transaction"
    ROLLBACK_TRANSACTION = "rollback_transaction"

    # Extended
    QUERY_RECORDS = "query_records"
    UPSERT_RECORD = "upsert_record"
    BATCH_CREATE = "batch_create"
    BATCH_UPDATE = "batch_update"

    # Integration
    CALL_EXTERNAL_API = "call_external_api"
    SEND_EMAIL = "send_email"
    SEND_SMS = "send_sms"
    PUSH_NOTIFICATION = "push_notification"
    WEBHOOK = "webhook"

    # Observability
    WRITE_AUDIT_LOG = "write_audit_log"
    RECORD_METRIC = "record_metric"

    # Compliance
    CHECK_COMPLIANCE = "check_compliance"
    MASK_PII = "mask_pii"

    # Advanced
    SCHEDULE_JOB = "schedule_job"
    BEGIN_SAGA = "begin_saga"
    COMPENSATE = "compensate"


class GuardType(str, Enum):
    """
    Loại guards được hỗ trợ.

    P0 - Core Guards:
    - AUTH: Auth guard (permission check)
    - TENANT_SCOPE: Tenant isolation guard

    P1 - Extended Guards:
    - RATE_LIMIT: Rate limiting guard
    - IP_WHITELIST: IP whitelist guard
    - TIME_WINDOW: Time window guard

    P1 - Compliance Guards:
    - KYC_CHECK: KYC compliance guard
    - AML_SCREENING: AML screening guard
    - HIPAA_ACCESS: HIPAA access guard

    P2 - Advanced Guards:
    - POLICY_EVAL: Policy evaluation guard (ABAC)
    - CONCURRENT_LOCK: Concurrent lock guard
    """

    # Core
    AUTH = "auth"
    TENANT_SCOPE = "tenant_scope"

    # Extended
    RATE_LIMIT = "rate_limit"
    IP_WHITELIST = "ip_whitelist"
    TIME_WINDOW = "time_window"

    # Compliance
    KYC_CHECK = "kyc_check"
    AML_SCREENING = "aml_screening"
    HIPAA_ACCESS = "hipaa_access"

    # Advanced
    POLICY_EVAL = "policy_eval"
    CONCURRENT_LOCK = "concurrent_lock"


@dataclass
class CommandField:
    """
    Field definition cho Command.

    Attributes:
        name: Tên field
        field_type: Type của field (string, integer, uuid, etc.)
        required: Có bắt buộc không
        pattern: Regex pattern validation
        min_length: Min length cho string
        max_length: Max length cho string
        min_value: Min value cho number
        max_value: Max value cho number
        min_items: Min items cho array
        max_items: Max items cho array
        default: Default value
        description: Mô tả field
    """

    name: str
    field_type: str
    required: bool = True
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_items: Optional[int] = None
    max_items: Optional[int] = None
    default: Any = None
    description: str = ""


@dataclass
class CommandGuard:
    """
    Guard definition cho Command.

    Attributes:
        guard_type: Loại guard
        permission: Permission required (cho AUTH guard)
        mode: Mode (cho TENANT_SCOPE guard)
        limit: Limit (cho RATE_LIMIT guard)
        window: Time window (cho RATE_LIMIT guard)
        roles: Required roles
        policy: Policy expression (cho POLICY_EVAL guard)
        description: Mô tả guard
    """

    guard_type: GuardType
    permission: Optional[str] = None
    mode: Optional[str] = None
    limit: Optional[int] = None
    window: Optional[str] = None
    roles: list[str] = field(default_factory=list)
    policy: Optional[str] = None
    description: str = ""


@dataclass
class CommandEffect:
    """
    Effect definition cho Command.

    Attributes:
        effect_type: Loại effect
        entity: Entity name (cho CRUD effects)
        event: Event name (cho publish_event)
        api_endpoint: API endpoint (cho call_external_api)
        email_template: Email template (cho send_email)
        sms_template: SMS template (cho send_sms)
        webhook_url: Webhook URL
        audit_action: Audit action
        metric_name: Metric name
        compliance_rule: Compliance rule
        job_name: Job name (cho schedule_job)
        condition: Condition để execute effect
        description: Mô tả effect
    """

    effect_type: EffectType
    entity: Optional[str] = None
    event: Optional[str] = None
    api_endpoint: Optional[str] = None
    email_template: Optional[str] = None
    sms_template: Optional[str] = None
    webhook_url: Optional[str] = None
    audit_action: Optional[str] = None
    metric_name: Optional[str] = None
    compliance_rule: Optional[str] = None
    job_name: Optional[str] = None
    condition: Optional[str] = None
    description: str = ""


@dataclass
class CommandError:
    """
    Error definition cho Command.

    Attributes:
        code: Error code
        message: Error message (Vietnamese)
        http_status: HTTP status code
        retryable: Có retry được không
        max_retries: Max retry attempts
        backoff_seconds: Backoff time
        description: Mô tả error
    """

    code: str
    message: str
    http_status: int = 400
    retryable: bool = False
    max_retries: int = 0
    backoff_seconds: float = 0.0
    description: str = ""


@dataclass
class ValidationResult:
    """
    Kết quả validation.

    Attributes:
        is_valid: Có hợp lệ không
        errors: Danh sách lỗi
        warnings: Danh sách warnings
    """

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """Thêm error vào danh sách."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Thêm warning vào danh sách."""
        self.warnings.append(warning)


@dataclass
class Command:
    """
    Command definition cho CP01 Domain Model.

    Command representation cho business operations với đầy đủ:
    - Input validation
    - Guards (auth, tenant, compliance)
    - Effects (CRUD, transaction, integration, observability)
    - Error handling

    Attributes:
        id: Command ID (PascalCase, e.g., "CreateOrder")
        description: Mô tả command (Vietnamese)
        input: Danh sách input fields
        guards: Danh sách guards
        effects: Danh sách effects
        errors: Danh sách custom errors
        transaction_required: Cần transaction không
        on_error: Error handler (rollback, compensate, etc.)
        idempotency_key: Idempotency key field
        timeout_seconds: Timeout cho command
        description: Mô tả command
    """

    id: str
    description: str
    input: list[CommandField] = field(default_factory=list)
    guards: list[CommandGuard] = field(default_factory=list)
    effects: list[CommandEffect] = field(default_factory=list)
    errors: list[CommandError] = field(default_factory=list)
    transaction_required: bool = False
    on_error: Optional[str] = None
    idempotency_key: Optional[str] = None
    timeout_seconds: Optional[int] = None

    def has_auth_guard(self) -> bool:
        """Check nếu có AUTH guard."""
        return any(g.guard_type == GuardType.AUTH for g in self.guards)

    def has_tenant_guard(self) -> bool:
        """Check nếu có TENANT_SCOPE guard."""
        return any(g.guard_type == GuardType.TENANT_SCOPE for g in self.guards)

    def has_transaction_effects(self) -> bool:
        """Check nếu có transaction effects."""
        return any(
            e.effect_type in [
                EffectType.BEGIN_TRANSACTION,
                EffectType.COMMIT_TRANSACTION,
                EffectType.ROLLBACK_TRANSACTION,
            ]
            for e in self.effects
        )

    def get_required_permissions(self) -> list[str]:
        """Lấy danh sách required permissions."""
        return [
            g.permission
            for g in self.guards
            if g.guard_type == GuardType.AUTH and g.permission
        ]

    def get_create_effects(self) -> list[CommandEffect]:
        """Lấy danh sách create effects."""
        return [e for e in self.effects if e.effect_type == EffectType.CREATE_RECORD]

    def get_update_effects(self) -> list[CommandEffect]:
        """Lấy danh sách update effects."""
        return [e for e in self.effects if e.effect_type == EffectType.UPDATE_RECORD]

    def get_delete_effects(self) -> list[CommandEffect]:
        """Lấy danh sách delete effects."""
        return [e for e in self.effects if e.effect_type == EffectType.DELETE_RECORD]

    def get_event_effects(self) -> list[CommandEffect]:
        """Lấy danh sách event effects."""
        return [e for e in self.effects if e.effect_type == EffectType.PUBLISH_EVENT]

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển Command sang dict.

        Returns:
            Dict representation của Command
        """
        return {
            "id": self.id,
            "description": self.description,
            "input": [
                {
                    "name": f.name,
                    "field_type": f.field_type,
                    "required": f.required,
                    "pattern": f.pattern,
                    "min_length": f.min_length,
                    "max_length": f.max_length,
                    "min_value": f.min_value,
                    "max_value": f.max_value,
                    "min_items": f.min_items,
                    "max_items": f.max_items,
                    "default": f.default,
                    "description": f.description,
                }
                for f in self.input
            ],
            "guards": [
                {
                    "guard_type": g.guard_type.value,
                    "permission": g.permission,
                    "mode": g.mode,
                    "limit": g.limit,
                    "window": g.window,
                    "roles": g.roles,
                    "policy": g.policy,
                    "description": g.description,
                }
                for g in self.guards
            ],
            "effects": [
                {
                    "effect_type": e.effect_type.value,
                    "entity": e.entity,
                    "event": e.event,
                    "api_endpoint": e.api_endpoint,
                    "email_template": e.email_template,
                    "sms_template": e.sms_template,
                    "webhook_url": e.webhook_url,
                    "audit_action": e.audit_action,
                    "metric_name": e.metric_name,
                    "compliance_rule": e.compliance_rule,
                    "job_name": e.job_name,
                    "condition": e.condition,
                    "description": e.description,
                }
                for e in self.effects
            ],
            "errors": [
                {
                    "code": err.code,
                    "message": err.message,
                    "http_status": err.http_status,
                    "retryable": err.retryable,
                    "max_retries": err.max_retries,
                    "backoff_seconds": err.backoff_seconds,
                    "description": err.description,
                }
                for err in self.errors
            ],
            "transaction_required": self.transaction_required,
            "on_error": self.on_error,
            "idempotency_key": self.idempotency_key,
            "timeout_seconds": self.timeout_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Command:
        """
        Tạo Command từ dict.

        Args:
            data: Dict chứa Command data

        Returns:
            Command instance
        """
        return cls(
            id=data["id"],
            description=data["description"],
            input=[CommandField(**f) for f in data.get("input", [])],
            guards=[CommandGuard(**g) for g in data.get("guards", [])],
            effects=[CommandEffect(**e) for e in data.get("effects", [])],
            errors=[CommandError(**e) for e in data.get("errors", [])],
            transaction_required=data.get("transaction_required", False),
            on_error=data.get("on_error"),
            idempotency_key=data.get("idempotency_key"),
            timeout_seconds=data.get("timeout_seconds"),
        )