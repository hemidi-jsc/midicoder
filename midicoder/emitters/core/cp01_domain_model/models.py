"""
Mô-đun models thống nhất cho CP01 Domain Model.

Định nghĩa tất cả dataclass và enum cho:
- Entity (EntityField, Relationship, Constraint, Index, LifecycleHook)
- Command (CommandField, CommandGuard, CommandEffect, ValidationResult)
- Query (QueryField, QueryGuard, QueryEffect, FilterExpression, PaginationConfig, ...)
- Value Object (VOField, ValueObject)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Entity Models
# ===========================================================================


class EntityFieldType(str, Enum):
    """
    Các loại field được hỗ trợ cho Entity.

    Mapping sang SQLAlchemy:
    - string → String
    - integer → Integer
    - float → Float
    - boolean → Boolean
    - datetime → DateTime
    - text → Text
    - uuid → UUID
    - json → JSON
    - decimal → Decimal
    - enum → Enum
    - largebinary → LargeBinary
    - array → ARRAY
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
    LARGE_BINARY = "largebinary"
    ARRAY = "array"


class RelationshipType(str, Enum):
    """
    Các loại relationship được hỗ trợ.

    - one-to-one: Mỗi thực thể quan hệ với nhiều nhất 1 thực thể khác
    - one-to-many: Một thực thể quan hệ với nhiều thực thể khác
    - many-to-many: Quan hệ nhiều-nhiều qua bảng trung gian
    - self-referencing: Entity quan hệ với chính nó
    - polymorphic: Relationship có thể trỏ đến multiple types
    """
    ONE_TO_ONE = "one-to-one"
    ONE_TO_MANY = "one-to-many"
    MANY_TO_MANY = "many-to-many"
    SELF_REFERENCING = "self-referencing"
    POLYMORPHIC = "polymorphic"


class ConstraintType(str, Enum):
    """
    Các loại constraint được hỗ trợ.

    - unique: Unique constraint
    - check: Check constraint
    - foreign_key: Foreign key constraint
    """
    UNIQUE = "unique"
    CHECK = "check"
    FOREIGN_KEY = "foreign_key"


class LifecycleEvent(str, Enum):
    """
    Các lifecycle events được hỗ trợ.

    SQLAlchemy event listeners:
    - before_insert: Trước khi insert
    - after_insert: Sau khi insert
    - before_update: Trước khi update
    - after_update: Sau khi update
    - before_delete: Trước khi delete
    - after_delete: Sau khi delete
    """
    BEFORE_INSERT = "before_insert"
    AFTER_INSERT = "after_insert"
    BEFORE_UPDATE = "before_update"
    AFTER_UPDATE = "after_update"
    BEFORE_DELETE = "before_delete"
    AFTER_DELETE = "after_delete"


@dataclass
class EntityField:
    """
    Đại diện cho một field của Entity.

    Attributes:
        name: Tên field (snake_case)
        field_type: Loại field (EntityFieldType enum)
        nullable: Có cho phép null không (default: True)
        unique: Có unique không (default: False)
        primary_key: Có phải primary key không (default: False)
        index: Có tạo index không (default: False)
        default: Giá trị mặc định
        server_default: Server default expression
        length: Độ dài (cho string)
        precision: Precision (cho decimal)
        scale: Scale (cho decimal)
        enum_values: Danh sách enum values (cho enum type)
        description: Mô tả field

    Ví dụ:
        >>> f = EntityField(
        ...     name="email",
        ...     field_type=EntityFieldType.STRING,
        ...     nullable=False,
        ...     unique=True,
        ...     length=255,
        ... )
    """
    name: str
    field_type: EntityFieldType
    nullable: bool = True
    unique: bool = False
    primary_key: bool = False
    index: bool = False
    default: Any = None
    server_default: str | None = None
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
    enum_values: list[str] | None = None
    description: str | None = None


@dataclass
class Relationship:
    """
    Đại diện cho một relationship giữa entities.

    Attributes:
        rel_type: Loại relationship
        target: Tên entity target
        local_field: Field name ở local entity (foreign key field)
        foreign_field: Field name ở target entity
        back_populates: Back-reference field name
        cascade: Cascade options (ví dụ: "all, delete-orphan")
        secondary: Secondary table name (cho many-to-many)
        polymorphic: Có phải polymorphic relationship không
        description: Mô tả relationship

    Ví dụ:
        >>> rel = Relationship(
        ...     rel_type=RelationshipType.ONE_TO_MANY,
        ...     target="Order",
        ...     back_populates="user",
        ...     cascade="all, delete-orphan",
        ... )
    """
    rel_type: RelationshipType
    target: str
    local_field: str | None = None
    foreign_field: str | None = None
    back_populates: str | None = None
    cascade: str | None = None
    secondary: str | None = None
    polymorphic: bool = False
    description: str | None = None


@dataclass
class Constraint:
    """
    Đại diện cho một constraint của Entity.

    Attributes:
        constraint_type: Loại constraint
        name: Tên constraint (cho check constraint)
        fields: Danh sách fields (cho unique constraint)
        condition: Condition expression (cho check constraint)
        description: Mô tả constraint

    Ví dụ:
        >>> constraint = Constraint(
        ...     constraint_type=ConstraintType.CHECK,
        ...     name="check_balance_non_negative",
        ...     condition="balance >= 0",
        ... )
    """
    constraint_type: ConstraintType
    name: str | None = None
    fields: list[str] | None = None
    condition: str | None = None
    description: str | None = None


@dataclass
class Index:
    """
    Đại diện cho một index của Entity.

    Attributes:
        name: Tên index
        fields: Danh sách fields
        unique: Có phải unique index không

    Ví dụ:
        >>> index = Index(
        ...     name="idx_user_status_created",
        ...     fields=["status", "created_at"],
        ...     unique=False,
        ... )
    """
    name: str | None = None
    fields: list[str] = field(default_factory=list)
    unique: bool = False


@dataclass
class LifecycleHook:
    """
    Đại diện cho một lifecycle hook.

    Attributes:
        event: Lifecycle event (before_insert, after_insert, etc.)
        hook_name: Tên hook function
        params: Parameters cho hook

    Ví dụ:
        >>> hook = LifecycleHook(
        ...     event=LifecycleEvent.BEFORE_INSERT,
        ...     hook_name="set_default_tenant",
        ...     params={"field": "tenant_id"},
        ... )
    """
    event: LifecycleEvent
    hook_name: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Entity:
    """
    Đại diện cho một Entity trong domain model.

    Attributes:
        id: Entity ID (PascalCase, ví dụ: "User")
        description: Mô tả entity
        fields: Danh sách fields
        relationships: Danh sách relationships
        constraints: Danh sách constraints
        indexes: Danh sách indexes
        lifecycle_hooks: Danh sách lifecycle hooks

    Ví dụ:
        >>> entity = Entity(
        ...     id="User",
        ...     description="User entity",
        ...     fields=[
        ...         EntityField(name="id", field_type=EntityFieldType.UUID, primary_key=True),
        ...         EntityField(name="email", field_type=EntityFieldType.STRING, unique=True),
        ...     ],
        ...     relationships=[
        ...         Relationship(
        ...             rel_type=RelationshipType.ONE_TO_MANY,
        ...             target="Order",
        ...             back_populates="user",
        ...         ),
        ...     ],
        ... )
    """
    id: str
    description: str | None = None
    fields: list[EntityField] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    indexes: list[Index] = field(default_factory=list)
    lifecycle_hooks: list[LifecycleHook] = field(default_factory=list)


# Backward-compatible aliases for entity models
Field = EntityField
FieldType = EntityFieldType


# ===========================================================================
# Advanced Domain Patterns
# ===========================================================================


class DomainEventType(str, Enum):
    """
    Loại sự kiện domain.

    - fact: Đã xảy ra, không thể undo (ví dụ: OrderPlaced, PaymentReceived)
    - intention: 의도, có thể bị hủy (ví dụ: OrderCancelled, PaymentRefunded)
    - state_change: Thay đổi trạng thái (ví dụ: OrderShipped, UserDeactivated)
    """
    FACT = "fact"
    INTENTION = "intention"
    STATE_CHANGE = "state_change"


@dataclass
class DomainEvent:
    """
    Đại diện cho một Domain Event — thứ gì đó đã xảy ra trong domain.

    immutability: Domain event một khi đã emit thì không thể thay đổi.

    Attributes:
        id: Event name (PascalCase, Past Tense, ví dụ: "OrderPlaced")
        event_type: Loại sự kiện (fact, intention, state_change)
        aggregate_id: Tên aggregate root emit event này
        fields: Danh sách fields mang dữ kiện của event
        description: Mô tả event

    Ví dụ:
        >>> event = DomainEvent(
        ...     id="OrderPlaced",
        ...     event_type=DomainEventType.FACT,
        ...     aggregate_id="Order",
        ...     fields=[
        ...         EntityField(name="order_id", field_type=EntityFieldType.UUID),
        ...         EntityField(name="total_amount", field_type=EntityFieldType.DECIMAL),
        ...     ],
        ... )
    """
    id: str
    event_type: DomainEventType = DomainEventType.FACT
    aggregate_id: str | None = None
    fields: list[EntityField] = field(default_factory=list)
    description: str | None = None


class ConsistencyLevel(str, Enum):
    """
    Mức độ consistency của Aggregate Root.

    - strict: Tất cả operations trong aggregate phải atomic (ACID)
    - eventual: Cho phép eventual consistency giữa các aggregate
    - relaxed: Chỉ consistency ở level business rule
    """
    STRICT = "strict"
    EVENTUAL = "eventual"
    RELAXED = "relaxed"


@dataclass
class AggregateRoot:
    """
    Boundary cho một consistency domain — nhóm entities phải được thao tác cùng nhau.

    Aggregate Root quy định:
    - Chỉ root có thể được truy cập trực tiếp từ bên ngoài
    - Các entities con chỉ truy cập qua root
    - Tất cả changes trong aggregate phải atomic
    - Root publish domain events khi state thay đổi

    Attributes:
        id: Aggregate name (PascalCase, ví dụ: "Order")
        root_entity: Tên entity là root của aggregate
        child_entities: Danh sách entities nằm trong aggregate boundary
        events: Danh sách domain events mà aggregate này emit
        consistency: Mức độ consistency (strict, eventual, relaxed)
        invariants: Danh sách business rules phải luôn đúng
        description: Mô tả aggregate

    Ví dụ:
        >>> agg = AggregateRoot(
        ...     id="Order",
        ...     root_entity="Order",
        ...     child_entities=["OrderItem"],
        ...     events=["OrderPlaced", "OrderCancelled", "OrderShipped"],
        ...     consistency=ConsistencyLevel.STRICT,
        ...     invariants=["total_price >= 0", "items must not be empty"],
        ... )
    """
    id: str
    root_entity: str
    child_entities: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    consistency: ConsistencyLevel = ConsistencyLevel.STRICT
    invariants: list[str] = field(default_factory=list)
    description: str | None = None


class ProjectionType(str, Enum):
    """
    Loại projection cho CQRS read model.

    - denormalized: Dữ liệu đã được flatten, optimized cho read
    - materialized_view: View được compute trước và cache
    - search_index: Projection phục vụ tìm kiếm (Elasticsearch, v.v.)
    - graph: Projection phục vụ query graph/relationship
    """
    DENORMALIZED = "denormalized"
    MATERIALIZED_VIEW = "materialized_view"
    SEARCH_INDEX = "search_index"
    GRAPH = "graph"


@dataclass
class Projection:
    """
    CQRS read model — bản chiếu của write model, tối ưu cho query.

    Projection subscribe vào domain events và update read model.

    Attributes:
        id: Projection name (PascalCase, ví dụ: "OrderSummary")
        projection_type: Loại projection
        source_aggregate: Aggregate root mà projection subscribe vào
        source_events: Danh sách events trigger projection update
        fields: Danh sách fields trong read model
        description: Mô tả projection

    Ví dụ:
        >>> proj = Projection(
        ...     id="OrderSummary",
        ...     projection_type=ProjectionType.DENORMALIZED,
        ...     source_aggregate="Order",
        ...     source_events=["OrderPlaced", "OrderCancelled"],
        ...     fields=[
        ...         EntityField(name="order_id", field_type=EntityFieldType.UUID),
        ...         EntityField(name="status", field_type=EntityFieldType.STRING),
        ...         EntityField(name="total", field_type=EntityFieldType.DECIMAL),
        ...     ],
        ... )
    """
    id: str
    projection_type: ProjectionType = ProjectionType.DENORMALIZED
    source_aggregate: str | None = None
    source_events: list[str] = field(default_factory=list)
    fields: list[EntityField] = field(default_factory=list)
    description: str | None = None


class EventTypeingStrategy(str, Enum):
    """
    Chiến lược lưu trữ events cho Event-Sourced Aggregate.

    - append_only: chỉ append, không ever xóa/update
    - snapshot: Periodic snapshot + events từ snapshot
    - compression: Compress events cũ thành snapshot
    """
    APPEND_ONLY = "append_only"
    SNAPSHOT = "snapshot"
    COMPRESSION = "compression"


@dataclass
class EventSourcedAggregate:
    """
    Aggregate root lưu state thông qua sequence của domain events.

    Thay vì lưu current state, lưu tất cả events → replay để tái tạo state.

    Attributes:
        id: Aggregate name (PascalCase, ví dụ: "BankAccount")
        root_entity: Tên entity là root
        events: Danh sách domain events mà aggregate emit
        eventing_strategy: Chiến lược lưu trữ events
        snapshot_interval: Số events giữa các snapshots (0 = không snapshot)
        versioned: Có optimistic concurrency control qua version không
        description: Mô tả aggregate

    Ví dụ:
        >>> esa = EventSourcedAggregate(
        ...     id="BankAccount",
        ...     root_entity="BankAccount",
        ...     events=["Deposited", "Withdrawn", "Transferred"],
        ...     eventing_strategy=EventTypeingStrategy.SNAPSHOT,
        ...     snapshot_interval=100,
        ...     versioned=True,
        ... )
    """
    id: str
    root_entity: str
    events: list[str] = field(default_factory=list)
    eventing_strategy: EventTypeingStrategy = EventTypeingStrategy.APPEND_ONLY
    snapshot_interval: int = 0
    versioned: bool = True
    description: str | None = None


class TemporalGranularity(str, Enum):
    """
    Mức độ granularity của temporal tracking.

    - second: Tracking chính xác đến giây
    - minute: Tracking theo phút
    - day: Tracking theo ngày
    - month: Tracking theo tháng
    """
    SECOND = "second"
    MINUTE = "minute"
    DAY = "day"
    MONTH = "month"


@dataclass
class TemporalEntity:
    """
    Entity có khả năng tracking state theo thời gian.

    Hỗ trợ query "state tại thời điểm T", "lịch sử thay đổi", v.v.

    Attributes:
        id: Entity name (PascalCase, ví dụ: "PriceHistory")
        fields: Danh sách fields hiện tại
        valid_from_field: Field name cho thời điểm bắt đầu有效
        valid_to_field: Field name cho thời điểm kết thúc有效
        granularity: Mức độ granularity của temporal tracking
        current_predicate: Cách xác định bản ghi hiện tại ("valid_to IS NULL", v.v.)
        description: Mô tả entity

    Ví dụ:
        >>> temporal = TemporalEntity(
        ...     id="PriceHistory",
        ...     fields=[
        ...         EntityField(name="product_id", field_type=EntityFieldType.UUID),
        ...         EntityField(name="price", field_type=EntityFieldType.DECIMAL),
        ...     ],
        ...     valid_from_field="valid_from",
        ...     valid_to_field="valid_to",
        ...     granularity=TemporalGranularity.DAY,
        ...     current_predicate="valid_to IS NULL",
        ... )
    """
    id: str
    fields: list[EntityField] = field(default_factory=list)
    valid_from_field: str = "valid_from"
    valid_to_field: str = "valid_to"
    granularity: TemporalGranularity = TemporalGranularity.SECOND
    current_predicate: str = "valid_to IS NULL"
    description: str | None = None


class PolymorphismType(str, Enum):
    """
    Loại polymorphism.

    - single_table: Tất cả types trong cùng 1 bảng, discriminator column
    - joined_table: Mỗi type 1 bảng, join qua primary key
    - concrete_table: Mỗi type 1 bảng độc lập, không inherit columns
    """
    SINGLE_TABLE = "single_table"
    JOINED_TABLE = "joined_table"
    CONCRETE_TABLE = "concrete_table"


@dataclass
class PolymorphicEntity:
    """
    Entity có thể tồn tại ở nhiều subtype — inherit fields từ base.

    Attributes:
        id: Base entity name (PascalCase, ví dụ: "Payment")
        polymorphism_type: Loại polymorphism (single_table, joined_table, concrete_table)
        discriminator_field: Column dùng để phân biệt subtype
        base_fields: Fields của base entity
        subtypes: Danh sách subtype definitions
        description: Mô tả entity

    Ví dụ:
        >>> poly = PolymorphicEntity(
        ...     id="Payment",
        ...     polymorphism_type=PolymorphismType.SINGLE_TABLE,
        ...     discriminator_field="payment_type",
        ...     base_fields=[
        ...         EntityField(name="amount", field_type=EntityFieldType.DECIMAL),
        ...     ],
        ...     subtypes=[
        ...         {"name": "CreditCardPayment", "fields": ["card_number", "expiry"]},
        ...         {"name": "BankTransferPayment", "fields": ["account_number", "bank_code"]},
        ...     ],
        ... )
    """
    id: str
    polymorphism_type: PolymorphismType = PolymorphismType.SINGLE_TABLE
    discriminator_field: str = "type"
    base_fields: list[EntityField] = field(default_factory=list)
    subtypes: list[dict[str, Any]] = field(default_factory=list)
    description: str | None = None


class SagaOrchestration(str, Enum):
    """
    Chế độ điều phối saga.

    - choreography: Mỗi event trigger step tiếp theo (decentralized)
    - orchestration: Orchestrator trung tâm điều khiển sequence (centralized)
    """
    CHOREOGRAPHY = "choreography"
    ORCHESTRATION = "orchestration"


class CompensatingActionType(str, Enum):
    """
    Loại compensating action khi saga rollback.

    - undo: Undo thay đổi đã làm (reverse operation)
    - noop: Không làm gì (idempotent, không cần undo)
    - notify: Gửi notification về failure
    """
    UNDO = "undo"
    NOOP = "noop"
    NOTIFY = "notify"


@dataclass
class SagaStep:
    """
    Một bước trong saga workflow.

    Attributes:
        name: Tên bước (ví dụ: "ReserveInventory")
        action: Command để thực hiện (ví dụ: "reserve_inventory")
        compensating_action: Command để rollback (ví dụ: "release_inventory")
        compensating_type: Loại compensating action
        on_success_event: Event emit khi bước thành công
        on_failure_event: Event emit khi bước thất bại
        description: Mô tả bước
    """
    name: str
    action: str
    compensating_action: str = ""
    compensating_type: CompensatingActionType = CompensatingActionType.UNDO
    on_success_event: str = ""
    on_failure_event: str = ""
    description: str | None = None


@dataclass
class Saga:
    """
    Long-running business transaction spanning multiple aggregates.

    Saga đảm bảo eventual consistency khi 1 operation cần modify nhiều aggregate.

    Attributes:
        id: Saga name (PascalCase, ví dụ: "OrderFulfillment")
        orchestration: Chế độ điều phối (choreography, orchestration)
        steps: Sequence của các bước trong saga
        timeout_seconds: Timeout tối đa cho toàn bộ saga
        retry_policy: Policy retry khi bước thất bại (ví dụ: "3x, exponential")
        description: Mô tả saga

    Ví dụ:
        >>> saga = Saga(
        ...     id="OrderFulfillment",
        ...     orchestration=SagaOrchestration.ORCHESTRATION,
        ...     steps=[
        ...         SagaStep(name="ReserveInventory", action="reserve_inventory",
        ...                   compensating_action="release_inventory"),
        ...         SagaStep(name="ProcessPayment", action="charge_payment",
        ...                   compensating_action="refund_payment"),
        ...         SagaStep(name="ShipOrder", action="ship_order",
        ...                   compensating_action="cancel_shipment"),
        ...     ],
        ...     timeout_seconds=3600,
        ... )
    """
    id: str
    orchestration: SagaOrchestration = SagaOrchestration.ORCHESTRATION
    steps: list[SagaStep] = field(default_factory=list)
    timeout_seconds: int = 3600
    retry_policy: str = ""
    description: str | None = None


# ===========================================================================
# Command Models
# ===========================================================================


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
# CommandFieldType Enum
# ============================================================================

class CommandFieldType(str, Enum):
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
# CommandField Model
# ============================================================================

@dataclass
class CommandField:
    """
    Field definition trong Command/Query input/output.

    Attributes:
        name: Tên field
        field_type: Loại dữ liệu (CommandFieldType enum)
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
        >>> f = CommandField(
        ...     name="order_id",
        ...     field_type=CommandFieldType.STRING,
        ...     required=True
        ... )
    """

    name: str
    field_type: CommandFieldType
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
        Chuyển CommandField sang dictionary.

        Returns:
            Dictionary representation của CommandField
        """
        # Handle both CommandFieldType enum and string
        field_type_value = self.field_type.value if isinstance(self.field_type, CommandFieldType) else self.field_type
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
    def from_dict(cls, data: dict[str, Any]) -> "CommandField":
        """
        Tạo CommandField từ dictionary.

        Args:
            data: Dictionary chứa field data

        Returns:
            CommandField instance
        """
        type_str = data.get("type", "string")
        field_type = CommandFieldType(type_str) if isinstance(type_str, str) else type_str

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
        ...     input=[CommandField(name="order_data", field_type=CommandFieldType.OBJECT)],
        ...     writes_to=["Order", "OrderItem"],
        ...     category="create",
        ...     transaction=True
        ... )
    """

    id: str
    description: str = ""
    input: list[CommandField] = field(default_factory=list)
    fetches: list[str] = field(default_factory=list)
    guards: list[CommandGuard] = field(default_factory=list)
    effects: list[CommandEffect] = field(default_factory=list)
    errors: list[CommandError] = field(default_factory=list)
    returns: list[CommandField] = field(default_factory=list)
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
        input: list[CommandField] | None = None,
        fetches: list[str] | None = None,
        guards: list[CommandGuard] | None = None,
        effects: list[CommandEffect] | None = None,
        errors: list[CommandError] | None = None,
        returns: list[CommandField] | None = None,
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
            input=[CommandField.from_dict(f) for f in data.get("input", [])],
            fetches=data.get("fetches", []),
            guards=data.get("guards", []),
            effects=data.get("effects", []),
            errors=data.get("errors", []),
            returns=[CommandField.from_dict(r) for r in data.get("returns", [])],
            category=data.get("category", "custom"),
            emits=data.get("emits", []),
            required_roles=data.get("required_roles", []),
            required_permissions=data.get("required_permissions", []),
            writes_to=data.get("writes_to", []),
            transaction_required=bool(data.get("transaction", False)) or bool(data.get("transaction_required", False)),
            tenant_scope=data.get("tenant_scope", "global"),
            on_error=data.get("on_error", "rollback"),
        )


# Backward-compatible aliases for command models
CommandFieldTypeAlias = CommandFieldType


# ===========================================================================
# Query Models
# ===========================================================================


class FilterOp(str, Enum):
    """
    Filter operators cho Query.

    Supports 13 operators:
    - Comparison: eq, ne, gt, gte, lt, lte
    - Membership: in, not_in
    - Pattern: like, ilike
    - Range: between
    - Null check: is_null, is_not_null
    """
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    LIKE = "like"
    ILIKE = "ilike"
    BETWEEN = "between"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class PaginationType(str, Enum):
    """
    Pagination types cho Query.

    - OFFSET: Page-based pagination (page, page_size)
    - CURSOR: Cursor-based pagination (cursor, limit)
    """
    OFFSET = "offset"
    CURSOR = "cursor"


class SortDirection(str, Enum):
    """
    Sort direction cho Query.

    - ASC: Ascending (tăng dần)
    - DESC: Descending (giảm dần)
    """
    ASC = "asc"
    DESC = "desc"


class AggFunction(str, Enum):
    """
    Aggregation functions cho Query.

    - COUNT: Đếm số lượng records
    - SUM: Tổng giá trị
    - AVG: Trung bình
    - MIN: Giá trị nhỏ nhất
    - MAX: Giá trị lớn nhất
    """
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"


class QueryGuardType(str, Enum):
    """
    Guard types cho Query.

    Theo SoT E06:
    - AUTH: Permission check (authorize_permission)
    - TENANT_SCOPE: Tenant isolation (enforce_tenant_scope)
    """
    AUTH = "auth"
    TENANT_SCOPE = "tenant_scope"


class QueryEffectType(str, Enum):
    """
    Effect types cho Query (subset of Command effects).

    Theo clarification Q1:
    - WRITE_AUDIT_LOG: Audit trail (RX11: Immutable Audit Evidence)
    - RECORD_METRIC: Metrics (CP15: Observability)
    """
    WRITE_AUDIT_LOG = "write_audit_log"
    RECORD_METRIC = "record_metric"


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class QueryField:
    """
    Query input field definition.

    Attributes:
        name: Tên field
        field_type: Type của field (str, int, uuid, etc.)
        required: Có bắt buộc không
        description: Mô tả field
        default: Giá trị mặc định (optional)
    """
    name: str
    field_type: str
    required: bool = False
    description: str = ""
    default: Any = None


@dataclass
class QueryGuard:
    """
    Query guard definition.

    Attributes:
        guard_type: Loại guard (AUTH, TENANT_SCOPE)
        permission: Permission cho AUTH guard (optional)
        mode: Mode cho TENANT_SCOPE (tenant_isolated, cross_tenant)
    """
    guard_type: QueryGuardType
    permission: str | None = None
    mode: str = "tenant_isolated"


@dataclass
class QueryEffect:
    """
    Query effect definition.

    Attributes:
        effect_type: Loại effect (WRITE_AUDIT_LOG, RECORD_METRIC)
        audit_action: Audit action name (cho WRITE_AUDIT_LOG)
        metric_name: Metric name (cho RECORD_METRIC)
        metric_value: Metric value (cho RECORD_METRIC)
    """
    effect_type: QueryEffectType
    audit_action: str | None = None
    metric_name: str | None = None
    metric_value: float = 1.0


@dataclass
class FilterExpression:
    """
    Filter expression cho Query.

    Attributes:
        field: Tên field cần filter
        operator: Operator (FilterOp enum)
        value: Giá trị để so sánh
    """
    field: str
    operator: FilterOp
    value: Any

    def to_sqlalchemy(self) -> Any:
        """
        Chuyển filter expression sang SQLAlchemy condition.

        Returns:
            SQLAlchemy condition expression
        """
        from sqlalchemy import column

        col = column(self.field)

        if self.operator == FilterOp.EQ:
            return col == self.value
        elif self.operator == FilterOp.NE:
            return col != self.value
        elif self.operator == FilterOp.GT:
            return col > self.value
        elif self.operator == FilterOp.GTE:
            return col >= self.value
        elif self.operator == FilterOp.LT:
            return col < self.value
        elif self.operator == FilterOp.LTE:
            return col <= self.value
        elif self.operator == FilterOp.IN:
            return col.in_(self.value)
        elif self.operator == FilterOp.NOT_IN:
            return col.notin_(self.value)
        elif self.operator == FilterOp.LIKE:
            return col.like(self.value)
        elif self.operator == FilterOp.ILIKE:
            return col.ilike(self.value)
        elif self.operator == FilterOp.BETWEEN:
            return col.between(self.value[0], self.value[1])
        elif self.operator == FilterOp.IS_NULL:
            return col.is_(None)
        elif self.operator == FilterOp.IS_NOT_NULL:
            return col.isnot(None)
        else:
            EM.raise_error(
                ErrorCode.CP01_QUERY_INVALID_FILTER,
                operator=self.operator.value,
            )


@dataclass
class FilterGroup:
    """
    Nhóm filters với AND/OR logic (nested support).

    Theo clarification: Cần support complex filters với AND/OR nested.

    Attributes:
        operator: Operator nhóm ("and" hoặc "or")
        filters: Danh sách FilterExpression hoặc FilterGroup con (nested)

    Example:
        # (status = 'active' AND created_at > '2026-01-01') OR tenant_id = 'abc'
        FilterGroup(
            operator="or",
            filters=[
                FilterGroup(
                    operator="and",
                    filters=[
                        FilterExpression("status", FilterOp.EQ, "active"),
                        FilterExpression("created_at", FilterOp.GT, "2026-01-01"),
                    ]
                ),
                FilterExpression("tenant_id", FilterOp.EQ, "abc"),
            ]
        )
    """
    operator: Literal["and", "or"]
    filters: list[FilterExpression | "FilterGroup"]

    def to_sqlalchemy(self) -> Any:
        """
        Chuyển filter group sang SQLAlchemy condition.

        Returns:
            SQLAlchemy condition expression với AND/OR logic
        """
        if not self.filters:
            # Empty group returns True (no filter)
            from sqlalchemy import true
            return true()

        # Convert first filter to start the condition
        first_filter = self.filters[0]
        if isinstance(first_filter, FilterGroup):
            result = first_filter.to_sqlalchemy()
        else:
            result = first_filter.to_sqlalchemy()

        # Combine remaining filters with AND/OR
        for flt in self.filters[1:]:
            if isinstance(flt, FilterGroup):
                condition = flt.to_sqlalchemy()
            else:
                condition = flt.to_sqlalchemy()

            if self.operator == "and":
                result = result & condition
            else:  # "or"
                result = result | condition

        return result


@dataclass
class PHIMaskingConfig:
    """
    Configuration cho PHI (Protected Health Information) masking.

    Theo RX04 HIPAA compliance: Cần mask sensitive healthcare data.

    Attributes:
        enabled: Có bật PHI masking không
        mask_patterns: Danh sách patterns để mask (regex)
        allowed_fields: Danh sách fields được phép expose không mask
        default_mask_value: Giá trị mặc định để thay thế (default: "***")

    Example:
        config = PHIMaskingConfig(
            enabled=True,
            mask_patterns=["^SSN$", "^medicaid_id"],
            allowed_fields=["patient_name", "diagnosis"],
            default_mask_value="[REDACTED]"
        )
    """
    enabled: bool = True
    mask_patterns: list[str] = field(default_factory=list)
    allowed_fields: list[str] = field(default_factory=list)
    default_mask_value: str = "***"

    def should_mask(self, field_name: str) -> bool:
        """
        Kiểm tra field có cần mask không.

        Args:
            field_name: Tên field cần kiểm tra

        Returns:
            True nếu field cần được mask
        """
        if not self.enabled:
            return False

        # Allowed fields are not masked
        if field_name in self.allowed_fields:
            return False

        # Check if field matches any mask pattern
        import re
        for pattern in self.mask_patterns:
            if re.match(pattern, field_name, re.IGNORECASE):
                return True

        # Check common PHI fields
        phi_fields = [
            "ssn", "social_security", "medicaid_id", "medicare_id",
            "patient_id", "mrn", "medical_record_number"
        ]
        if field_name.lower() in phi_fields:
            return True

        return False

    def mask_value(self, field_name: str, value: str) -> str:
        """
        Mask giá trị của field nếu cần.

        Args:
            field_name: Tên field
            value: Giá trị gốc

        Returns:
            Giá trị đã mask hoặc gốc
        """
        if self.should_mask(field_name):
            return self.default_mask_value
        return value


@dataclass
class SortExpression:
    """
    Sort expression cho Query (multi-field support).

    Attributes:
        field: Tên field cần sort
        direction: Sort direction (ASC/DESC)
    """
    field: str
    direction: SortDirection = SortDirection.ASC


@dataclass
class PaginationConfig:
    """
    Pagination configuration cho Query.

    Attributes:
        type: Loại pagination (OFFSET/CURSOR)
        page_size: Số records mỗi page (cho OFFSET)
        page: Page number (cho OFFSET)
        offset: Offset (cho OFFSET)
        limit: Limit records (cho CURSOR)
        cursor: Cursor string (cho CURSOR)
    """
    type: PaginationType = PaginationType.OFFSET
    page_size: int = 20
    page: int = 1
    offset: int = 0
    limit: int = 20
    cursor: str | None = None

    def __post_init__(self) -> None:
        """Validate và tính toán offset từ page."""
        if self.type == PaginationType.OFFSET and self.offset == 0 and self.page > 1:
            self.offset = (self.page - 1) * self.page_size


@dataclass
class ProjectionConfig:
    """
    Projection configuration cho Query (field selection).

    Attributes:
        include: Danh sách fields cần include
        exclude: Danh sách fields cần exclude
    """
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)

    def get_sensitive_fields_to_exclude(self) -> list[str]:
        """
        Lấy danh sách sensitive fields cần exclude tự động.

        Returns:
            Danh sách sensitive field names
        """
        return [
            "password", "secret_key", "token", "api_key",
            "private_key", "credential", "auth_token"
        ]


@dataclass
class AggregationConfig:
    """
    Aggregation configuration cho Query.

    Attributes:
        function: Aggregation function (COUNT, SUM, AVG, MIN, MAX)
        agg_field: Field để aggregate (None cho COUNT)
        group_by: Danh sách fields để group by
    """
    function: AggFunction
    agg_field: str | None = None
    group_by: list[str] = field(default_factory=list)


# ============================================================================
# Query Models
# ============================================================================


@dataclass
class Query:
    """
    Query model cho CP01 Domain Model DSL.

    Theo SoT E03, authorized_query pattern:
    - authorize_permission (AUTH guard)
    - enforce_tenant_scope (TENANT_SCOPE guard)
    - query_records

    Theo SoT E06:
    - Every authorized_query must have enforce_tenant_scope
    - Query must filter by tenant_id

    Attributes:
        id: Query ID (PascalCase, ví dụ: GetOrder)
        description: Mô tả query
        reads_from: Entity mà query đọc từ
        input: Danh sách input fields
        filters: Danh sách filter expressions
        pagination: Pagination configuration
        projection: Projection configuration
        sort: Danh sách sort expressions (multi-field)
        guards: Danh sách query guards
        effects: Danh sách query effects
    """
    id: str
    description: str
    reads_from: str
    input: list[QueryField] = field(default_factory=list)
    filters: list[FilterExpression] = field(default_factory=list)
    pagination: PaginationConfig = field(default_factory=PaginationConfig)
    projection: ProjectionConfig = field(default_factory=ProjectionConfig)
    sort: list[SortExpression] = field(default_factory=list)
    guards: list[QueryGuard] = field(default_factory=list)
    effects: list[QueryEffect] = field(default_factory=list)

    def has_auth_guard(self) -> bool:
        """
        Kiểm tra query có AUTH guard không.

        Returns:
            True nếu có AUTH guard
        """
        return any(g.guard_type == QueryGuardType.AUTH for g in self.guards)

    def has_tenant_guard(self) -> bool:
        """
        Kiểm tra query có TENANT_SCOPE guard không.

        Returns:
            True nếu có TENANT_SCOPE guard
        """
        return any(g.guard_type == QueryGuardType.TENANT_SCOPE for g in self.guards)

    def has_audit_effects(self) -> bool:
        """
        Kiểm tra query có audit effects không.

        Returns:
            True nếu có WRITE_AUDIT_LOG effect
        """
        return any(
            e.effect_type == QueryEffectType.WRITE_AUDIT_LOG
            for e in self.effects
        )

    def get_required_permissions(self) -> list[str]:
        """
        Lấy danh sách required permissions từ AUTH guards.

        Returns:
            Danh sách permission strings
        """
        return [
            g.permission for g in self.guards
            if g.guard_type == QueryGuardType.AUTH and g.permission
        ]

    def get_audit_actions(self) -> list[str]:
        """
        Lấy danh sách audit actions từ effects.

        Returns:
            Danh sách audit action names
        """
        return [
            e.audit_action for e in self.effects
            if e.effect_type == QueryEffectType.WRITE_AUDIT_LOG and e.audit_action
        ]

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển query sang dict.

        Returns:
            Dictionary representation của query
        """
        return {
            "id": self.id,
            "description": self.description,
            "reads_from": self.reads_from,
            "input": [
                {
                    "name": f.name,
                    "field_type": f.field_type,
                    "required": f.required,
                    "description": f.description,
                    "default": f.default,
                }
                for f in self.input
            ],
            "filters": [
                {
                    "field": f.field,
                    "operator": f.operator.value,
                    "value": f.value,
                }
                for f in self.filters
            ],
            "pagination": {
                "type": self.pagination.type.value,
                "page_size": self.pagination.page_size,
                "page": self.pagination.page,
                "offset": self.pagination.offset,
                "limit": self.pagination.limit,
                "cursor": self.pagination.cursor,
            },
            "projection": {
                "include": self.projection.include,
                "exclude": self.projection.exclude,
            },
            "sort": [
                {
                    "field": s.field,
                    "direction": s.direction.value,
                }
                for s in self.sort
            ],
            "guards": [
                {
                    "guard_type": g.guard_type.value,
                    "permission": g.permission,
                    "mode": g.mode,
                }
                for g in self.guards
            ],
            "effects": [
                {
                    "effect_type": e.effect_type.value,
                    "audit_action": e.audit_action,
                    "metric_name": e.metric_name,
                    "metric_value": e.metric_value,
                }
                for e in self.effects
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Query":
        """
        Tạo Query từ dict.

        Args:
            data: Dictionary với query data

        Returns:
            Query instance
        """
        # Parse input fields
        input_fields = [
            QueryField(
                name=f["name"],
                field_type=f["field_type"],
                required=f.get("required", False),
                description=f.get("description", ""),
                default=f.get("default"),
            )
            for f in data.get("input", [])
        ]

        # Parse filters
        filters = [
            FilterExpression(
                field=f["field"],
                operator=FilterOp(f["operator"]),
                value=f["value"],
            )
            for f in data.get("filters", [])
        ]

        # Parse pagination
        pagination_data = data.get("pagination", {})
        pagination = PaginationConfig(
            type=PaginationType(pagination_data.get("type", "offset")),
            page_size=pagination_data.get("page_size", 20),
            page=pagination_data.get("page", 1),
            offset=pagination_data.get("offset", 0),
            limit=pagination_data.get("limit", 20),
            cursor=pagination_data.get("cursor"),
        )

        # Parse projection
        projection_data = data.get("projection", {})
        projection = ProjectionConfig(
            include=projection_data.get("include", []),
            exclude=projection_data.get("exclude", []),
        )

        # Parse sort
        sort = [
            SortExpression(
                field=s["field"],
                direction=SortDirection(s.get("direction", "asc")),
            )
            for s in data.get("sort", [])
        ]

        # Parse guards
        guards = [
            QueryGuard(
                guard_type=QueryGuardType(g["guard_type"]),
                permission=g.get("permission"),
                mode=g.get("mode", "tenant_isolated"),
            )
            for g in data.get("guards", [])
        ]

        # Parse effects
        effects = [
            QueryEffect(
                effect_type=QueryEffectType(e["effect_type"]),
                audit_action=e.get("audit_action"),
                metric_name=e.get("metric_name"),
                metric_value=e.get("metric_value", 1.0),
            )
            for e in data.get("effects", [])
        ]

        return cls(
            id=data["id"],
            description=data["description"],
            reads_from=data["reads_from"],
            input=input_fields,
            filters=filters,
            pagination=pagination,
            projection=projection,
            sort=sort,
            guards=guards,
            effects=effects,
        )


@dataclass
class AggregationQuery:
    """
    Aggregation Query model cho COUNT, SUM, AVG, GROUP BY.

    Theo clarification Q4: Cần full aggregation model.

    Attributes:
        id: Query ID (PascalCase, ví dụ: CountOrders)
        description: Mô tả query
        reads_from: Entity mà query đọc từ
        aggregation: Aggregation configuration
        filters: Danh sách filter expressions (before aggregation)
        pagination: Pagination configuration
        guards: Danh sách query guards
        effects: Danh sách query effects
    """
    id: str
    description: str
    reads_from: str
    aggregation: AggregationConfig
    filters: list[FilterExpression] = field(default_factory=list)
    pagination: PaginationConfig = field(default_factory=PaginationConfig)
    guards: list[QueryGuard] = field(default_factory=list)
    effects: list[QueryEffect] = field(default_factory=list)

    def has_auth_guard(self) -> bool:
        """Kiểm tra aggregation query có AUTH guard không."""
        return any(g.guard_type == QueryGuardType.AUTH for g in self.guards)

    def has_tenant_guard(self) -> bool:
        """Kiểm tra aggregation query có TENANT_SCOPE guard không."""
        return any(g.guard_type == QueryGuardType.TENANT_SCOPE for g in self.guards)

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển aggregation query sang dict.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "description": self.description,
            "reads_from": self.reads_from,
            "aggregation": {
                "function": self.aggregation.function.value,
                "field": self.aggregation.agg_field,
                "group_by": self.aggregation.group_by,
            },
            "filters": [
                {
                    "field": f.field,
                    "operator": f.operator.value,
                    "value": f.value,
                }
                for f in self.filters
            ],
            "pagination": {
                "type": self.pagination.type.value,
                "page_size": self.pagination.page_size,
                "page": self.pagination.page,
                "offset": self.pagination.offset,
            },
            "guards": [
                {
                    "guard_type": g.guard_type.value,
                    "permission": g.permission,
                    "mode": g.mode,
                }
                for g in self.guards
            ],
            "effects": [
                {
                    "effect_type": e.effect_type.value,
                    "audit_action": e.audit_action,
                }
                for e in self.effects
            ],
        }


# ===========================================================================
# Value Object Models
# ===========================================================================


class VOFieldType(Enum):
    """
    Enum cho các field types trong Value Object.

    Types:
        STRING: String type
        INTEGER: Integer type
        FLOAT: Float type
        BOOLEAN: Boolean type
        DATETIME: DateTime type
        TEXT: Text type
        UUID: UUID type
        JSON: JSON type
        DECIMAL: Decimal type
        ENUM: Enum type

    Note: Value Objects thường không cần LARGE_BINARY, ARRAY, OBJECT
    vì chúng là primitive/immutable values.
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


# ============================================================================
# VOField Model
# ============================================================================

@dataclass
class VOField:
    """
    Field definition trong Value Object.

    Attributes:
        name: Tên field
        field_type: Loại dữ liệu (VOFieldType enum)
        required: Có bắt buộc không
        default: Giá trị mặc định
        description: Mô tả field
        precision: Precision (cho decimal)
        scale: Scale (cho decimal)
        min_length: Min length (cho string)
        max_length: Max length (cho string)
        pattern: Regex pattern (cho string)
        enum_values: Enum values (cho enum type)

    Example:
        >>> f = VOField(
        ...     name="amount",
        ...     field_type=VOFieldType.DECIMAL,
        ...     precision=10,
        ...     scale=2,
        ...     required=True
        ... )
    """

    name: str
    field_type: VOFieldType
    required: bool = False
    default: Any = None
    description: str = ""
    precision: int | None = None
    scale: int | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    enum_values: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển VOField sang dictionary.

        Returns:
            Dictionary representation của VOField
        """
        result: dict[str, Any] = {
            "name": self.name,
            "type": self.field_type.value,
            "required": self.required,
        }

        # Add optional fields only if set
        if self.default is not None:
            result["default"] = self.default
        if self.description:
            result["description"] = self.description
        if self.precision is not None:
            result["precision"] = self.precision
        if self.scale is not None:
            result["scale"] = self.scale
        if self.min_length is not None:
            result["min_length"] = self.min_length
        if self.max_length is not None:
            result["max_length"] = self.max_length
        if self.pattern is not None:
            result["pattern"] = self.pattern
        if self.enum_values is not None:
            result["enum_values"] = self.enum_values

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VOField":
        """
        Tạo VOField từ dictionary.

        Args:
            data: Dictionary chứa field data

        Returns:
            VOField instance
        """
        type_str = data.get("type", "string")
        field_type = VOFieldType(type_str) if isinstance(type_str, str) else type_str

        return cls(
            name=data.get("name", ""),
            field_type=field_type,
            required=bool(data.get("required", False)),
            default=data.get("default"),
            description=data.get("description", ""),
            precision=data.get("precision"),
            scale=data.get("scale"),
            min_length=data.get("min_length"),
            max_length=data.get("max_length"),
            pattern=data.get("pattern"),
            enum_values=data.get("enum_values"),
        )


# ============================================================================
# ValueObject Model
# ============================================================================

@dataclass
class ValueObject:
    """
    Value Object definition trong DSL.

    Value Object là immutable object đại diện cho một concept domain
    với identity dựa trên attributes thay vì ID.

    Attributes:
        id: Định danh duy nhất của VO
        description: Mô tả VO
        fields: Danh sách fields
        immutable: Có bất biến không (default: False)
        comparable: Có thể so sánh không (default: False)
        extends: Parent VO ID (cho inheritance)

    Example:
        >>> vo = ValueObject(
        ...     id="Money",
        ...     description="Giá tiền với currency",
        ...     fields=[
        ...         VOField(name="amount", field_type=VOFieldType.DECIMAL, required=True),
        ...         VOField(name="currency", field_type=VOFieldType.STRING, required=True)
        ...     ],
        ...     immutable=True
        ... )
    """

    id: str
    description: str = ""
    fields: list[VOField] = field(default_factory=list)
    immutable: bool = False
    comparable: bool = False
    extends: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển ValueObject sang dictionary.

        Returns:
            Dictionary representation của ValueObject
        """
        result: dict[str, Any] = {
            "id": self.id,
            "fields": [f.to_dict() for f in self.fields],
            "immutable": self.immutable,
            "comparable": self.comparable,
        }

        # Add optional fields only if set
        if self.description:
            result["description"] = self.description
        if self.extends is not None:
            result["extends"] = self.extends

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ValueObject":
        """
        Tạo ValueObject từ dictionary.

        Args:
            data: Dictionary chứa VO data

        Returns:
            ValueObject instance
        """
        return cls(
            id=data.get("id", ""),
            description=data.get("description", ""),
            fields=[VOField.from_dict(f) for f in data.get("fields", [])],
            immutable=bool(data.get("immutable", False)),
            comparable=bool(data.get("comparable", False)),
            extends=data.get("extends"),
        )


# ===========================================================================
# Exports
# ===========================================================================

__all__ = [
    # -- Entity Models (canonical names) --
    "EntityFieldType",
    "EntityField",
    "RelationshipType",
    "ConstraintType",
    "LifecycleEvent",
    "Relationship",
    "Constraint",
    "Index",
    "LifecycleHook",
    "Entity",
    # -- Entity Models (backward-compatible aliases) --
    "Field",
    "FieldType",
    # -- Advanced Domain Patterns --
    "DomainEventType",
    "DomainEvent",
    "ConsistencyLevel",
    "AggregateRoot",
    "ProjectionType",
    "Projection",
    "EventTypeingStrategy",
    "EventSourcedAggregate",
    "TemporalGranularity",
    "TemporalEntity",
    "PolymorphismType",
    "PolymorphicEntity",
    "SagaOrchestration",
    "CompensatingActionType",
    "SagaStep",
    "Saga",
    # -- Command Models (canonical names) --
    "EffectType",
    "GuardType",
    "CommandFieldType",
    "CommandField",
    "CommandGuard",
    "CommandEffect",
    "CommandError",
    "ValidationResult",
    "Command",
    # -- Query Models --
    "FilterOp",
    "PaginationType",
    "SortDirection",
    "AggFunction",
    "QueryGuardType",
    "QueryEffectType",
    "QueryField",
    "QueryGuard",
    "QueryEffect",
    "FilterExpression",
    "FilterGroup",
    "PHIMaskingConfig",
    "SortExpression",
    "PaginationConfig",
    "ProjectionConfig",
    "AggregationConfig",
    "Query",
    "AggregationQuery",
    # -- Value Object Models --
    "VOFieldType",
    "VOField",
    "ValueObject",
]
