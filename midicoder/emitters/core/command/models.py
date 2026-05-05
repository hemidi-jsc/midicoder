"""
Command Models Module.

Module này định nghĩa các models cho Command DSL:
- Command: Định nghĩa command với input, output, guards, effects
- Field: Định nghĩa field trong input/output
- FieldType: Enum cho field types

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ============================================================================
# FieldType Enum
# ============================================================================

# ============================================================================
# EffectType Enum (Command-specific)
# ============================================================================

class EffectType(str, Enum):
    """
    Các loại effects cho Command.

    Core CRUD:
        CREATE_RECORD: Tạo record mới
        UPDATE_RECORD: Cập nhật record
        DELETE_RECORD: Xóa record
        PUBLISH_EVENT: Publish event

    Transaction:
        BEGIN_TRANSACTION: Begin transaction
        COMMIT_TRANSACTION: Commit transaction
        ROLLBACK_TRANSACTION: Rollback transaction

    Extended:
        QUERY_RECORDS: Query records
        UPSERT_RECORD: Upsert record

    Integration:
        CALL_EXTERNAL_API: Gọi external API
        SEND_EMAIL: Gửi email
        SEND_SMS: Gửi SMS
        WEBHOOK: Gọi webhook

    Observability:
        WRITE_AUDIT_LOG: Write audit log
        RECORD_METRIC: Record metric

    Compliance:
        CHECK_COMPLIANCE: Check compliance
        MASK_PII: Mask PII data
    """
    # Core CRUD
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

    # Integration
    CALL_EXTERNAL_API = "call_external_api"
    SEND_EMAIL = "send_email"
    SEND_SMS = "send_sms"
    WEBHOOK = "webhook"

    # Observability
    WRITE_AUDIT_LOG = "write_audit_log"
    RECORD_METRIC = "record_metric"

    # Compliance
    CHECK_COMPLIANCE = "check_compliance"
    MASK_PII = "mask_pii"

    # Domain-Specific Effects (DP05, DP09, DP11, DP12)
    DOUBLE_ENTRY_LEDGER = "double_entry_ledger"    # DP11 Banking: Double-entry bookkeeping
    INVENTORY_RESERVATION = "inventory_reservation"  # DP05 Manufacturing: Inventory reservation
    PAYMENT_PROCESS = "payment_process"              # DP12 Payments: Payment gateway processing
    CLINICAL_TRANSITION = "clinical_transition"      # DP09 Healthcare: Clinical workflow transition


# ============================================================================
# GuardType Enum (Command-specific)
# ============================================================================

class GuardType(str, Enum):
    """
    Các loại guards cho Command.

    AUTH: Authentication & Authorization
    TENANT_SCOPE: Tenant isolation (KPI-029)
    RATE_LIMIT: Rate limiting
    KYC_CHECK: KYC compliance check (RX03)
    AML_SCREENING: AML screening (RX03)
    HIPAA_ACCESS: HIPAA access check (RX04)
    GDPR_CONSENT: GDPR consent check (RX05)
    PCI_RESTRICT: PCI restriction check (RX06)
    FRAUD_DETECTION: Fraud detection for payments (DP12)
    SAFETY_CHECK: Safety check for manufacturing (DP05)
    CLAIMS_VALIDATION: Claims validation for insurance (DP14)
    """
    AUTH = "auth"
    TENANT_SCOPE = "tenant_scope"
    RATE_LIMIT = "rate_limit"
    KYC_CHECK = "kyc_check"
    AML_SCREENING = "aml_screening"
    HIPAA_ACCESS = "hipaa_access"
    GDPR_CONSENT = "gdpr_consent"
    PCI_RESTRICT = "pci_restrict"
    FRAUD_DETECTION = "fraud_detection"
    SAFETY_CHECK = "safety_check"
    CLAIMS_VALIDATION = "claims_validation"


# ============================================================================
# FieldType Enum
# ============================================================================

class FieldType(str, Enum):
    """
    Enum cho các field types trong Command/Query.

    Types:
        STRING: String type (varchar)
        INTEGER: Integer type (int)
        FLOAT: Float type (float)
        BOOLEAN: Boolean type (bool)
        DATETIME: DateTime type (timestamp)
        TEXT: Text type (text)
        UUID: UUID type (uuid)
        JSON: JSON type (json/jsonb)
        DECIMAL: Decimal type (decimal)
        ENUM: Enum type (custom enum)
        LARGE_BINARY: Large binary type (blob)
        ARRAY: Array type (array)
        OBJECT: Object type (nested object)
    """

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    TEXT = "text"
    UUID = "uuid"
    JSON = "json"
    DECIMAL = "decimal"
    ENUM = "enum"
    LARGE_BINARY = "large_binary"
    ARRAY = "array"
    OBJECT = "object"


# ============================================================================
# Field Model
# ============================================================================

@dataclass
class Field:
    """
    Field definition trong Command/Query input/output.

    Attributes:
        name: Tên field
        field_type: Loại dữ liệu (FieldType enum)
        required: Có bắt buộc không
        default: Giá trị mặc định
        description: Mô tả field
        nullable: Có thể null không
        unique: Có unique constraint không
        primary_key: Có phải primary key không
        index: Có index không
        server_default: Server default value
        length: Max length (cho string)
        precision: Precision (cho decimal)
        scale: Scale (cho decimal)
        enum_values: Enum values (cho enum type)
        pattern: Regex pattern cho validation
        min_length: Min length (cho string)
        max_length: Max length (cho string)
        min_value: Min value (cho numeric)
        max_value: Max value (cho numeric)
        min_items: Min items (cho array)
        max_items: Max items (cho array)

    Example:
        >>> f = Field(
        ...     name="order_id",
        ...     field_type=FieldType.STRING,
        ...     required=True
        ... )
    """

    name: str
    field_type: FieldType
    required: bool = False
    default: Any = None
    description: str = ""
    nullable: bool = True
    unique: bool = False
    primary_key: bool = False
    index: bool = False
    server_default: str = ""
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
    enum_values: list[str] | None = None
    # Validation attributes
    pattern: str | None = None
    min_length: int | None = None
    max_length: int | None = None
    min_value: float | None = None
    max_value: float | None = None
    min_items: int | None = None
    max_items: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển Field sang dictionary.

        Returns:
            Dictionary representation của Field
        """
        # Handle both FieldType enum and string
        field_type_value = self.field_type.value if isinstance(self.field_type, FieldType) else self.field_type
        return {
            "name": self.name,
            "type": field_type_value,
            "required": self.required,
            "default": self.default,
            "description": self.description,
            "nullable": self.nullable,
            "unique": self.unique,
            "primary_key": self.primary_key,
            "index": self.index,
            "server_default": self.server_default,
            "length": self.length,
            "precision": self.precision,
            "scale": self.scale,
            "enum_values": self.enum_values,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Field":
        """
        Tạo Field từ dictionary.

        Args:
            data: Dictionary chứa field data

        Returns:
            Field instance
        """
        type_str = data.get("type", "string")
        field_type = FieldType(type_str) if isinstance(type_str, str) else type_str

        return cls(
            name=data.get("name", ""),
            field_type=field_type,
            required=bool(data.get("required", False)),
            default=data.get("default"),
            description=data.get("description", ""),
            nullable=bool(data.get("nullable", True)),
            unique=bool(data.get("unique", False)),
            primary_key=bool(data.get("primary_key", False)),
            index=bool(data.get("index", False)),
            server_default=data.get("server_default", ""),
            length=data.get("length"),
            precision=data.get("precision"),
            scale=data.get("scale"),
            enum_values=data.get("enum_values"),
        )


# ============================================================================
# CommandGuard Model (for tests compatibility)
# ============================================================================

@dataclass
class CommandGuard:
    """
    Guard cho Command (tương thích với tests).

    Attributes:
        guard_type: Loại guard (GuardType enum)
        permission: Permission string
        condition: Business condition
        mode: Mode (cho tenant_scope guard)
        limit: Rate limit
        window: Rate limit window

    Example:
        >>> guard = CommandGuard(
        ...     guard_type=GuardType.AUTH,
        ...     permission="order.create"
        ... )
    """
    guard_type: GuardType
    permission: str | None = None
    condition: str | None = None
    mode: str | None = None
    limit: int | None = None
    window: str | None = None


# CommandError Model
# ============================================================================

@dataclass
class CommandError:
    """
    Error định nghĩa cho Command.

    Attributes:
        code: Error code (unique identifier)
        message: Error message
        http_status: HTTP status code
        retryable: Có thể retry không
        compensation: Compensation action

    Example:
        >>> error = CommandError(
        ...     code="ORDER_INVALID_ITEMS",
        ...     message="Đơn hàng phải có ít nhất một sản phẩm",
        ...     http_status=400
        ... )
    """
    code: str
    message: str
    http_status: int = 400
    retryable: bool = False
    compensation: str | None = None


# ============================================================================
# CommandEffect Model (for tests compatibility)
# ============================================================================

@dataclass
class CommandEffect:
    """
    Effect cho Command (tương thích với tests).

    Attributes:
        effect_type: Loại effect (EffectType enum)
        entity: Entity name
        event: Event name
        condition: Condition expression
        email_template: Email template name
        sms_template: SMS template name
        audit_action: Audit action name

    Example:
        >>> effect = CommandEffect(
        ...     effect_type=EffectType.CREATE_RECORD,
        ...     entity="Order"
        ... )
    """
    effect_type: EffectType
    entity: str | None = None
    event: str | None = None
    condition: str | None = None
    email_template: str | None = None
    sms_template: str | None = None
    audit_action: str | None = None


# ============================================================================
# ValidationResult Model
# ============================================================================

@dataclass
class ValidationResult:
    """
    Kết quả validation cho Command data.

    Attributes:
        is_valid: Kết quả validation (True/False)
        errors: Danh sách lỗi validation
        warnings: Danh sách cảnh báo validation

    Example:
        >>> result = ValidationResult(is_valid=False)
        >>> result.add_error("Email không hợp lệ")
        >>> result.add_warning("Mật khẩu yếu")
    """
    is_valid: bool = True
    errors: list[str] = None
    warnings: list[str] = None

    def __post_init__(self):
        """Initialize lists if None."""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

    def add_error(self, error: str) -> None:
        """
        Thêm lỗi validation.

        Args:
            error: Lỗi validation
        """
        self.is_valid = False
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """
        Thêm cảnh báo validation.

        Args:
            warning: Cảnh báo validation
        """
        self.warnings.append(warning)


# ============================================================================
# Command Model
# ============================================================================

@dataclass
class Command:
    """
    Command definition trong DSL.

    Command đại diện cho một write operation trong hệ thống.
    Mỗi command có input, guards, effects, và errors.

    Attributes:
        id: Định danh duy nhất của command
        description: Mô tả command
        input: Danh sách input fields
        fetches: Danh sách entities cần load trước khi execute
        guards: Danh sách guards cần check
        effects: Danh sách effects sau khi execute
        errors: Danh sách errors có thể phát sinh
        returns: Danh sách return fields
        category: Phân loại command (create, update, delete, custom)
        emits: Danh sách events sẽ emit
        required_roles: Roles cần thiết để execute
        required_permissions: Permissions cần thiết
        writes_to: Danh sách entities sẽ được modify
        transaction: Có cần transaction không
        tenant_scope: Phạm vi multi-tenancy

    Example:
        >>> cmd = Command(
        ...     id="CreateOrder",
        ...     description="Tạo đơn hàng mới",
        ...     input=[Field(name="order_data", field_type=FieldType.OBJECT)],
        ...     writes_to=["Order", "OrderItem"],
        ...     category="create",
        ...     transaction=True
        ... )
    """

    id: str
    description: str = ""
    input: list[Field] = field(default_factory=list)
    fetches: list[str] = field(default_factory=list)
    guards: list[CommandGuard] = field(default_factory=list)
    effects: list[CommandEffect] = field(default_factory=list)
    errors: list[CommandError] = field(default_factory=list)
    returns: list[Field] = field(default_factory=list)
    category: str = "custom"
    emits: list[str] = field(default_factory=list)
    required_roles: list[str] = field(default_factory=list)
    required_permissions: list[str] = field(default_factory=list)
    writes_to: list[str] = field(default_factory=list)
    transaction_required: bool = False
    tenant_scope: str = "global"
    on_error: str = "rollback"

    def __init__(
        self,
        id: str,
        description: str = "",
        input: list[Field] | None = None,
        fetches: list[str] | None = None,
        guards: list[CommandGuard] | None = None,
        effects: list[CommandEffect] | None = None,
        errors: list[CommandError] | None = None,
        returns: list[Field] | None = None,
        category: str = "custom",
        emits: list[str] | None = None,
        required_roles: list[str] | None = None,
        required_permissions: list[str] | None = None,
        writes_to: list[str] | None = None,
        transaction_required: bool = False,
        transaction: bool | None = None,  # Alias for backward compatibility
        tenant_scope: str = "global",
        on_error: str = "rollback",
    ) -> None:
        """
        Initialize Command.

        Args:
            id: Command ID
            description: Command description
            input: Input fields
            fetches: Entities to fetch before execute
            guards: Guards to check
            effects: Effects after execute
            errors: Possible errors
            returns: Return fields
            category: Command category
            emits: Events to emit
            required_roles: Required roles
            required_permissions: Required permissions
            writes_to: Entities to modify
            transaction_required: Whether transaction is needed
            transaction: Alias for transaction_required (backward compatibility)
            tenant_scope: Multi-tenancy scope
            on_error: Error handling mode
        """
        # Handle backward compatibility: transaction -> transaction_required
        if transaction is not None:
            transaction_required = transaction

        self.id = id
        self.description = description
        self.input = input if input is not None else []
        self.fetches = fetches if fetches is not None else []
        self.guards = guards if guards is not None else []
        self.effects = effects if effects is not None else []
        self.errors = errors if errors is not None else []
        self.returns = returns if returns is not None else []
        self.category = category
        self.emits = emits if emits is not None else []
        self.required_roles = required_roles if required_roles is not None else []
        self.required_permissions = required_permissions if required_permissions is not None else []
        self.writes_to = writes_to if writes_to is not None else []
        self.transaction_required = transaction_required
        self.tenant_scope = tenant_scope
        self.on_error = on_error

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển Command sang dictionary.

        Returns:
            Dictionary representation của Command
        """
        # Serialize CommandGuard objects
        guards_dict = []
        for g in self.guards:
            if isinstance(g, CommandGuard):
                guards_dict.append({
                    "guard_type": g.guard_type.value,
                    "permission": g.permission,
                    "condition": g.condition,
                    "mode": g.mode,
                    "limit": g.limit,
                    "window": g.window,
                })
            else:
                guards_dict.append(g)

        # Serialize CommandEffect objects
        effects_dict = []
        for e in self.effects:
            if isinstance(e, CommandEffect):
                effects_dict.append({
                    "effect_type": e.effect_type.value,
                    "entity": e.entity,
                    "event": e.event,
                    "condition": e.condition,
                    "email_template": e.email_template,
                    "sms_template": e.sms_template,
                    "audit_action": e.audit_action,
                })
            else:
                effects_dict.append(e)

        # Serialize CommandError objects
        errors_dict = []
        for err in self.errors:
            if isinstance(err, CommandError):
                errors_dict.append({
                    "code": err.code,
                    "message": err.message,
                    "http_status": err.http_status,
                    "retryable": err.retryable,
                    "compensation": err.compensation,
                })
            else:
                errors_dict.append(err)

        return {
            "id": self.id,
            "description": self.description,
            "input": [f.to_dict() for f in self.input],
            "fetches": self.fetches,
            "guards": guards_dict,
            "effects": effects_dict,
            "errors": errors_dict,
            "returns": [r.to_dict() for r in self.returns],
            "category": self.category,
            "emits": self.emits,
            "required_roles": self.required_roles,
            "required_permissions": self.required_permissions,
            "writes_to": self.writes_to,
            "transaction": self.transaction_required,
            "transaction_required": self.transaction_required,
            "tenant_scope": self.tenant_scope,
            "on_error": self.on_error,
        }

    def has_auth_guard(self) -> bool:
        """
        Kiểm tra Command có AUTH guard không.

        Returns:
            True nếu có AUTH guard
        """
        return any(
            isinstance(g, CommandGuard) and g.guard_type == GuardType.AUTH
            for g in self.guards
        )

    def has_tenant_guard(self) -> bool:
        """
        Kiểm tra Command có TENANT_SCOPE guard không.

        Returns:
            True nếu có TENANT_SCOPE guard
        """
        return any(
            isinstance(g, CommandGuard) and g.guard_type == GuardType.TENANT_SCOPE
            for g in self.guards
        )

    def has_transaction_effects(self) -> bool:
        """
        Kiểm tra Command có transaction effects không.

        Returns:
            True nếu có BEGIN_TRANSACTION hoặc COMMIT_TRANSACTION effects
        """
        transaction_effects = {
            EffectType.BEGIN_TRANSACTION,
            EffectType.COMMIT_TRANSACTION,
            EffectType.ROLLBACK_TRANSACTION,
        }
        return any(
            isinstance(e, CommandEffect) and e.effect_type in transaction_effects
            for e in self.effects
        )

    def get_required_permissions(self) -> list[str]:
        """
        Lấy danh sách permissions cần thiết từ AUTH guards.

        Returns:
            Danh sách permission strings
        """
        permissions = list(self.required_permissions)
        for g in self.guards:
            if isinstance(g, CommandGuard) and g.guard_type == GuardType.AUTH:
                if g.permission and g.permission not in permissions:
                    permissions.append(g.permission)
        return permissions

    def get_create_effects(self) -> list[CommandEffect]:
        """
        Lấy danh sách create effects.

        Returns:
            Danh sách CommandEffect với effect_type = CREATE_RECORD
        """
        return [
            e for e in self.effects
            if isinstance(e, CommandEffect) and e.effect_type == EffectType.CREATE_RECORD
        ]

    def get_update_effects(self) -> list[CommandEffect]:
        """
        Lấy danh sách update effects.

        Returns:
            Danh sách CommandEffect với effect_type = UPDATE_RECORD
        """
        return [
            e for e in self.effects
            if isinstance(e, CommandEffect) and e.effect_type == EffectType.UPDATE_RECORD
        ]

    def get_delete_effects(self) -> list[CommandEffect]:
        """
        Lấy danh sách delete effects.

        Returns:
            Danh sách CommandEffect với effect_type = DELETE_RECORD
        """
        return [
            e for e in self.effects
            if isinstance(e, CommandEffect) and e.effect_type == EffectType.DELETE_RECORD
        ]

    def get_event_effects(self) -> list[CommandEffect]:
        """
        Lấy danh sách event effects.

        Returns:
            Danh sách CommandEffect với effect_type = PUBLISH_EVENT
        """
        return [
            e for e in self.effects
            if isinstance(e, CommandEffect) and e.effect_type == EffectType.PUBLISH_EVENT
        ]

    @property
    def transaction(self) -> bool:
        """
        Alias cho transaction_required (backward compatibility).

        Returns:
            Giá trị transaction_required
        """
        return self.transaction_required

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Command":
        """
        Tạo Command từ dictionary.

        Args:
            data: Dictionary chứa command data

        Returns:
            Command instance
        """
        return cls(
            id=data.get("id", ""),
            description=data.get("description", ""),
            input=[Field.from_dict(f) for f in data.get("input", [])],
            fetches=data.get("fetches", []),
            guards=data.get("guards", []),
            effects=data.get("effects", []),
            errors=data.get("errors", []),
            returns=[Field.from_dict(r) for r in data.get("returns", [])],
            category=data.get("category", "custom"),
            emits=data.get("emits", []),
            required_roles=data.get("required_roles", []),
            required_permissions=data.get("required_permissions", []),
            writes_to=data.get("writes_to", []),
            transaction_required=bool(data.get("transaction", False)) or bool(data.get("transaction_required", False)),
            tenant_scope=data.get("tenant_scope", "global"),
            on_error=data.get("on_error", "rollback"),
        )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "EffectType",
    "GuardType",
    "FieldType",
    "Field",
    "CommandGuard",
    "CommandEffect",
    "CommandError",
    "Command",
]
