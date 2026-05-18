"""
DSL v1 Projection Module

Module này cung cấp các lớp để biểu diễn và thao tác với cây projection DSL v1.
Sử dụng typed models thay vì dict[str, Any] để đảm bảo type safety.

Các thành phần chính:
- TypedDict models: 100+ loại tham số cho các node types khác nhau
- NodeKind enum: 101 loại node trong DSL kernel
- ProjectionNode: Node đơn lẻ trong cây projection
- ProjectionTree: Cây projection hoàn chỉnh với indexing
- NodeBuilder: Protocol cho factory pattern

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from typing import Any, Callable, Optional, Protocol, TypedDict


# ============================================================================
# Typed Parameter Models (thay thế dict[str, Any])
# ============================================================================
# Các TypedDict này định nghĩa cấu trúc tham số cho mỗi loại node.
# Sử dụng total=False để tất cả fields đều optional (flexible cho YAML loading).


class EntityParams(TypedDict, total=False):
    """
    Tham số cho Entity nodes.

    Entity đại diện cho các đối tượng domain chính trong hệ thống.
    Mỗi entity có các fields, constraints, và tenant scope.

    Fields:
        id: Định danh duy nhất của entity
        description: Mô tả entity (tiếng Việt hoặc tiếng Anh)
        fields: Danh sách các trường của entity
        primary_key: Tên trường làm primary key (mặc định: "id")
        indexes: Danh sách các index để tối ưu query
        constraints: Danh sách các constraints (foreign_key, unique, etc.)
        tags: Danh sách tags để categorization
        tenant_scope: Phạm vi multi-tenancy (global, tenant_isolated, etc.)
        source: Nguồn định nghĩa (filename yaml)

    Ví dụ:
        {
            "id": "Order",
            "fields": [{"name": "order_id", "type": "string"}],
            "tenant_scope": "tenant_isolated"
        }
    """

    id: str
    description: str
    fields: list[dict[str, Any]]
    primary_key: str
    indexes: list[dict[str, Any]]
    constraints: list[dict[str, Any]]
    tags: list[str]
    tenant_scope: str
    source: str


# ============================================================================
# Extended Value Object DSL
# ============================================================================
# Extensions cho Value Object để support 100 industries với:
# - Complex field types (object, array, map, ref)
# - Computed/derived fields
# - Inheritance hierarchy
# - Behavior/methods
# - Validation rules
# - Compliance tags


class FieldDefinition(TypedDict, total=False):
    """
    Định nghĩa một field trong Value Object.
    
    Support cả basic types và complex types.
    
    Basic Types:
        - string, integer, decimal, boolean, datetime, uuid, enum
    
    Complex Types:
        - object: Nested object với fields
        - array: Mảng với item_type hoặc item_fields
        - map: Dictionary với key_type và value_type
        - ref: Reference đến Entity hoặc Value Object khác
    
    Computed Fields:
        - computed: True để đánh dấu field là computed
        - formula: Công thức tính toán
        - depends_on: Danh sách fields mà computed field phụ thuộc
    
    Validation:
        - required: Có bắt buộc không
        - default: Giá trị mặc định
        - min, max: Range validation (number/decimal)
        - min_length, max_length: String length validation
        - pattern: Regex pattern cho string
        - precision, scale: Decimal precision/scale
    
    Fields:
        name: Tên field
        type: Loại dữ liệu
        required: Có bắt buộc không
        default: Giá trị mặc định
        description: Mô tả field
        
        # Type-specific
        precision: int  # decimal precision
        scale: int  # decimal scale
        min_length: int  # string min length
        max_length: int  # string max length
        pattern: str  # string regex pattern
        min: Any  # number min value
        max: Any  # number max value
        enum_values: list[str]  # enum values
        enum_class: str  # enum class reference
        
        # Complex types
        fields: list["FieldDefinition"]  # object type fields
        key_type: str  # map key type
        value_type: str  # map value type
        item_type: str  # array item type (simple)
        item_fields: list["FieldDefinition"]  # array item fields (complex)
        
        # References
        ref_type: str  # "entity" or "value_object"
        ref_to: str  # ID of referenced entity/VO
        
        # Computed
        computed: bool  # Is computed field
        formula: str  # Computation formula
        depends_on: list[str]  # Dependent field names
    """
    
    name: str
    type: str
    required: bool
    default: Any
    description: str
    
    # Type-specific
    precision: int
    scale: int
    min_length: int
    max_length: int
    length: int  # alias for max_length
    pattern: str
    min: Any
    max: Any
    enum_values: list[str]
    enum_class: str
    
    # Complex types
    fields: list["FieldDefinition"]
    key_type: str
    value_type: str
    item_type: str
    item_fields: list["FieldDefinition"]
    
    # References
    ref_type: str
    ref_to: str
    
    # Computed
    computed: bool
    formula: str
    depends_on: list[str]


class MethodDefinition(TypedDict, total=False):
    """
    Định nghĩa một method trong Value Object.
    
    Methods cho phép Value Object có behavior với business logic.
    
    Ví dụ:
        Money.add(other: Money) -> Money
        Money.convert_to(currency: str) -> Money
    
    Fields:
        name: Tên method
        description: Mô tả method
        params: Danh sách parameters
        returns: Return type
        logic: Mô tả business logic
        side_effects: Danh sách side effects (optional)
        async_: Có phải async method không
    """
    
    name: str
    description: str
    params: list[FieldDefinition]
    returns: str
    logic: str
    side_effects: list[str]
    async_: bool


class ValidationRule(TypedDict, total=False):
    """
    Validation rule cho Value Object.
    
    Support cross-field validation với error codes chuẩn.
    
    Fields:
        name: Tên rule
        condition: Điều kiện validation (expression)
        error_code: Error code chuẩn (MDC-VO-XXX-XXX)
        error_message: Message hiển thị (tiếng Việt)
        severity: Mức độ (warning, error)
    """
    
    name: str
    condition: str
    error_code: str
    error_message: str
    severity: str


class ExtendedValueObjectParams(TypedDict, total=False):
    """
    Extended Value Object DSL cho 100 industries.
    
    Mở rộng ValueObjectParams với:
    - Inheritance (extends)
    - Methods
    - Validation rules
    - Compliance
    
    Fields:
        id: Định danh VO
        description: Mô tả VO
        extends: Parent VO ID (cho inheritance)
        fields: Danh sách FieldDefinition
        methods: Danh sách MethodDefinition
        validation_rules: Danh sách ValidationRule
        immutable: Có bất biến không
        comparable: Có thể so sánh không
        tags: Danh sách tags (pii, healthcare, etc.)
        compliance: Danh sách compliance requirements
        source: Nguồn định nghĩa
    """
    
    id: str
    description: str
    extends: str  # Parent VO ID for inheritance
    fields: list[FieldDefinition]
    methods: list[MethodDefinition]
    validation_rules: list[ValidationRule]
    immutable: bool
    comparable: bool
    tags: list[str]
    compliance: list[dict[str, Any]]
    source: str


class AggregateParams(TypedDict, total=False):
    """
    Tham số cho Aggregate nodes.

    Aggregate là ranh giới consistency chứa các entities và value objects.
    Mỗi aggregate có một root entity và các invariants cần enforce.

    Fields:
        id: Định danh của aggregate
        description: Mô tả aggregate
        entity_id: ID của root entity
        invariants: Danh sách các business invariants cần enforce
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    entity_id: str
    invariants: list[dict[str, Any]]
    tags: list[str]
    source: str


class EnumParams(TypedDict, total=False):
    """
    Tham số cho Enum nodes.

    Enum định nghĩa một tập hợp các giá trị cố định.
    Dùng cho status, type, category, etc.

    Fields:
        id: Định danh của enum
        description: Mô tả enum
        values: Danh sách các giá trị enum
        underlying_type: Loại dữ liệu cơ sở (string, int, etc.)
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    values: list[dict[str, Any]]
    underlying_type: str
    tags: list[str]
    source: str


class ErrorParams(TypedDict, total=False):
    """
    Tham số cho Error nodes.

    Error định nghĩa các lỗi business với error codes, severity, và category.
    Dùng cho error handling nhất quán trong toàn hệ thống.

    Fields:
        id: Định danh của error
        code: Error code duy nhất (ví dụ: "ORDER_NOT_FOUND")
        description: Mô tả lỗi
        severity: Mức độ nghiêm trọng (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        category: Phân loại lỗi (VALIDATION, NOT_FOUND, CONFLICT, etc.)
        http_status: HTTP status code tương ứng
        recoverable: Có thể tự phục hồi không
        fields: Các trường thông tin lỗi bổ sung
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    code: str
    description: str
    severity: str
    category: str
    http_status: int
    recoverable: bool
    fields: list[dict[str, Any]]
    tags: list[str]
    source: str


class EventParams(TypedDict, total=False):
    """
    Tham số cho Event nodes.

    Event đại diện cho các sự kiện đã xảy ra trong hệ thống.
    Dùng cho event-driven architecture và audit trails.

    Fields:
        id: Định danh của event
        description: Mô tả event
        type: Loại event (domain_event, integration_event, etc.)
        source_entity: Entity phát sinh event
        fields: Các trường dữ liệu của event
        version: Version của event schema
        tags: Danh sách tags
        tenant_scope: Phạm vi multi-tenancy
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    type: str
    source_entity: str
    fields: list[dict[str, Any]]
    version: str
    tags: list[str]
    tenant_scope: str
    source: str


class CommandParams(TypedDict, total=False):
    """
    Tham số cho Command nodes.

    Command đại diện cho các thao tác write trong hệ thống.
    Mỗi command có input, guards, effects, và errors.

    Fields:
        id: Định danh của command
        description: Mô tả command
        input: Các tham số đầu vào
        fetches: Danh sách entities cần load trước khi execute
        guards: Các guards cần kiểm tra (auth, permission, validation)
        effects: Các side effects sau khi execute
        errors: Danh sách errors có thể phát sinh
        returns: Dữ liệu trả về
        category: Phân loại command (create, update, delete, etc.)
        emits: Danh sách events sẽ emit
        required_roles: Roles cần thiết để execute
        required_permissions: Permissions cần thiết
        writes_to: Danh sách entities sẽ được modify
        datasource: Datasource để lưu trữ
        transaction: Có cần transaction không
        tenant_scope: Phạm vi multi-tenancy
        source: Nguồn định nghĩa
        tags: Danh sách tags
    """

    id: str
    description: str
    input: list[dict[str, Any]]
    fetches: list[str]
    guards: list[dict[str, Any]]
    effects: list[dict[str, Any]]
    errors: list[str]
    returns: list[dict[str, Any]]
    category: str
    emits: list[str]
    required_roles: list[str]
    required_permissions: list[str]
    writes_to: list[str]
    datasource: str
    transaction: bool
    transaction_required: bool
    on_error: str
    tenant_scope: str
    source: str
    tags: list[str]


class QueryParams(TypedDict, total=False):
    """
    Tham số cho Query nodes.

    Query đại diện cho các thao tác read trong hệ thống.
    Mỗi query có input, fetches, guards, effects, và returns.

    Fields:
        id: Định danh của query
        description: Mô tả query
        input: Các tham số đầu vào (filters, pagination)
        fetches: Danh sách entities cần load
        guards: Các guards cần kiểm tra
        effects: Side effects (audit_log, record_metric, v.v.)
        returns: Dữ liệu trả về
        category: Phân loại query (find_by_id, list, search, etc.)
        reads_from: Danh sách entities sẽ đọc
        required_roles: Roles cần thiết để execute
        required_permissions: Permissions cần thiết
        datasource: Datasource để đọc
        tenant_scope: Phạm vi multi-tenancy
        source: Nguồn định nghĩa
        tags: Danh sách tags
    """

    id: str
    description: str
    input: list[dict[str, Any]]
    fetches: list[str]
    guards: list[dict[str, Any]]
    effects: list[dict[str, Any]]
    returns: list[dict[str, Any]]
    category: str
    reads_from: list[str]
    required_roles: list[str]
    required_permissions: list[str]
    datasource: str
    tenant_scope: str
    source: str
    tags: list[str]


class WorkflowParams(TypedDict, total=False):
    """
    Tham số cho Workflow nodes.

    Workflow định nghĩa các state machines cho business processes.
    Bao gồm states, transitions, guards, và effects.

    Fields:
        id: Định danh của workflow
        description: Mô tả workflow
        states: Danh sách các states
        transitions: Danh sách các transitions giữa states
        guards: Các guards cho transitions
        effects: Các effects khi transition
        tenant_scope: Phạm vi multi-tenancy
        tags: Danh sách tags
        gateway_types: Các loại gateways (parallel, exclusive, etc.)
        sub_workflows: Danh sách sub-workflows
        compensation: Các compensation actions cho rollback
        human_tasks: Các human tasks/approvals
        timers: Các timers và delays
    """

    id: str
    description: str
    states: list[dict[str, Any]]
    transitions: list[dict[str, Any]]
    guards: list[dict[str, Any]]
    effects: list[dict[str, Any]]
    tenant_scope: str
    tags: list[str]
    gateway_types: list[str]
    sub_workflows: list[str]
    compensation: list[dict[str, Any]]
    human_tasks: list[dict[str, Any]]
    timers: list[dict[str, Any]]


class RuleParams(TypedDict, total=False):
    """
    Tham số cho Rule nodes.

    Rule định nghĩa các business rules với condition và action.
    Dùng cho rule engines và decision tables.

    Fields:
        id: Định danh của rule
        description: Mô tả rule
        type: Loại rule (validation, calculation, decision, etc.)
        condition: Điều kiện để rule được apply
        action: Hành động khi condition đúng
        priority: Prioriry của rule (cao hơn = apply trước)
        enabled: Rule có active không
        tags: Danh sách tags
    """

    id: str
    description: str
    type: str
    condition: dict[str, Any]
    action: dict[str, Any]
    priority: int
    enabled: bool
    tags: list[str]


class GuardParams(TypedDict, total=False):
    """
    Tham số cho Guard nodes.

    Guard là các kiểm tra pre-condition cho commands/workflows.
    Ví dụ: auth check, permission check, input validation.

    Fields:
        id: Định danh của guard
        description: Mô tả guard
        type: Loại guard (auth, permission, validation, etc.)
        condition: Điều kiện guard
        error: Error ID khi guard fail
        tags: Danh sách tags
    """

    id: str
    description: str
    type: str
    condition: dict[str, Any]
    error: str
    tags: list[str]


class EffectParams(TypedDict, total=False):
    """
    Tham số cho Effect nodes.

    Effect là các side effects xảy ra sau khi command execute.
    Ví dụ: send email, publish event, update cache.

    Fields:
        id: Định danh của effect
        description: Mô tả effect
        type: Loại effect (db_write, event_publish, notification, etc.)
        target: Target của effect
        payload: Dữ liệu truyền cho effect
        async_: Có execute async không
        retry_policy: Policy cho retry khi fail
        tags: Danh sách tags
    """

    id: str
    description: str
    type: str
    target: str
    payload: dict[str, Any]
    async_: bool
    retry_policy: dict[str, Any]
    tags: list[str]


# ============================================================================
# CP01-aligned TypedDicts — advanced domain patterns
# ============================================================================
# These TypedDicts correspond to CP01 definitions that previously had no
# canonical DSL representation.  Added so that the DSL parser can produce
# typed ProjectionNode.params for every definition declared in pack.yml.


class ValueObjectParams(TypedDict, total=False):
    """
    Tham số cho Value Object nodes (canonical).

    Value Object là immutable, equality-by-value domain primitive.
    Đây là TypedDict canonical — ExtendedValueObjectParams vẫn giữ cho
    backward compatibility nhưng ValueObjectParams là default.

    Fields:
        id: Định danh của VO
        description: Mô tả VO
        extends: Parent VO ID (cho inheritance)
        fields: Danh sách FieldDefinition
        methods: Danh sách MethodDefinition
        validation_rules: Danh sách ValidationRule
        immutable: Có bất biến không (default: True)
        comparable: Có thể so sánh không
        tags: Danh sách tags
        compliance: Compliance requirements
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    extends: str
    fields: list[FieldDefinition]
    methods: list[MethodDefinition]
    validation_rules: list[ValidationRule]
    immutable: bool
    comparable: bool
    tags: list[str]
    compliance: list[dict[str, Any]]
    source: str


class EventSourcedAggregateParams(TypedDict, total=False):
    """
    Tham số cho Event-Sourced Aggregate nodes.

    Aggregate reconstructs state từ sequence của domain events.
    Không lưu current state — chỉ lưu event log.

    Fields:
        id: Định danh của aggregate
        description: Mô tả aggregate
        root_entity: Entity là root của aggregate
        events: Danh sách event IDs mà aggregate emit
        eventing_strategy: Chiến lược lưu trữ ("append_only"|"snapshot"|"compression")
        snapshot_interval: Số events giữa các snapshots (0 = no snapshot)
        versioned: Optimistic concurrency control qua version column
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    root_entity: str
    events: list[str]
    eventing_strategy: str
    snapshot_interval: int
    versioned: bool
    tags: list[str]
    source: str


class TemporalEntityParams(TypedDict, total=False):
    """
    Tham số cho Temporal Entity nodes.

    Entity tracking state theo thời gian (SCD Type 2).
    Hỗ trợ query "state tại thời điểm T" và "lịch sử thay đổi".

    Fields:
        id: Định danh của entity
        description: Mô tả entity
        fields: Danh sách fields
        valid_from_field: Tên field cho start of validity period
        valid_to_field: Tên field cho end of validity period
        granularity: Mức độ granularity ("second"|"minute"|"day"|"month")
        current_predicate: Predicate để xác định bản ghi hiện tại
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    fields: list[dict[str, Any]]
    valid_from_field: str
    valid_to_field: str
    granularity: str
    current_predicate: str
    tags: list[str]
    source: str


class PolymorphicEntityParams(TypedDict, total=False):
    """
    Tham số cho Polymorphic Entity nodes.

    Entity có thể tồn tại ở nhiều subtype — inherit fields từ base.
    Support Single-table, Joined-table, Concrete-table inheritance.

    Fields:
        id: Định danh của base entity
        description: Mô tả entity
        polymorphism_type: Chiến lược inheritance ("single_table"|"joined_table"|"concrete_table")
        discriminator_field: Column dùng để phân biệt subtype
        base_fields: Fields của base entity
        subtypes: Danh sách subtype definitions ({name, fields})
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    polymorphism_type: str
    discriminator_field: str
    base_fields: list[dict[str, Any]]
    subtypes: list[dict[str, Any]]
    tags: list[str]
    source: str


class SagaParams(TypedDict, total=False):
    """
    Tham số cho Saga nodes.

    Long-running business transaction spanning multiple aggregates.
    Mỗi step có action + compensating action cho rollback.

    Fields:
        id: Định danh của saga
        description: Mô tả saga
        orchestration: Chế độ điều phối ("choreography"|"orchestration")
        steps: Danh sách saga step definitions
        timeout_seconds: Timeout tối đa cho toàn bộ saga
        retry_policy: Policy retry khi step thất bại
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    orchestration: str
    steps: list[dict[str, Any]]
    timeout_seconds: int
    retry_policy: str
    tags: list[str]
    source: str


class AggregationQueryParams(TypedDict, total=False):
    """
    Tham số cho Aggregation Query nodes.

    Query với group-by, having, và aggregate functions (SUM, AVG, COUNT).
    Mở rộng QueryParams với aggregation-specific fields.

    Fields:
        id: Định danh của query
        description: Mô tả query
        aggregation: Danh sách aggregate functions ({function, field, alias})
        group_by: Danh sách group-by fields
        having: Danh sách having conditions
        reads_from: Danh sách entities sẽ đọc
        filters: Pre-aggregation filters
        pagination: Pagination config
        required_permissions: Permissions cần thiết
        tenant_scope: Phạm vi multi-tenancy
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    aggregation: list[dict[str, Any]]
    group_by: list[str]
    having: list[dict[str, Any]]
    reads_from: list[str]
    filters: list[dict[str, Any]]
    pagination: dict[str, Any]
    required_permissions: list[str]
    tenant_scope: str
    tags: list[str]
    source: str


class HTTPRouteParams(TypedDict, total=False):
    """
    Tham số cho HTTP Route nodes.

    HTTP Route ánh xạ REST endpoints đến commands/queries.
    Định nghĩa method, path, auth requirements, và schemas.

    Fields:
        id: Định danh của route
        method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        path: URL path pattern
        command_id: ID của command (cho write operations)
        query_id: ID của query (cho read operations)
        auth_required: Có cần auth không
        required_roles: Roles cần thiết
        required_permissions: Permissions cần thiết
        request_schema: Schema cho request body
        response_schema: Schema cho response body
        tags: Danh sách tags
    """

    id: str
    method: str
    path: str
    command_id: str
    query_id: str
    auth_required: bool
    required_roles: list[str]
    required_permissions: list[str]
    request_schema: dict[str, Any]
    response_schema: dict[str, Any]
    tags: list[str]


class GraphQLResolverParams(TypedDict, total=False):
    """
    Tham số cho GraphQL Resolver nodes.

    GraphQL Resolver ánh xạ GraphQL operations đến commands/queries.
    Định nghĩa type, field, args, và return schema.

    Fields:
        id: Định danh của resolver
        description: Mô tả resolver
        operation: Loại operation (query, mutation, subscription)
        type_name: Tên GraphQL type
        field_name: Tên field trong type
        command_id: ID của command (cho mutations)
        query_id: ID của query (cho queries)
        args: Danh sách các arguments
        returns: Return schema
        auth_required: Có cần auth không
        tags: Danh sách tags
    """

    id: str
    description: str
    operation: str
    type_name: str
    field_name: str
    command_id: str
    query_id: str
    args: list[dict[str, Any]]
    returns: dict[str, Any]
    auth_required: bool
    tags: list[str]


class WebhookParams(TypedDict, total=False):
    """
    Tham số cho Webhook nodes.

    Webhook định nghĩa các incoming webhooks từ external systems.
    Bao gồm path, auth, payload schema, và handler.

    Fields:
        id: Định danh của webhook
        description: Mô tả webhook
        path: URL path để receive webhook
        event_type: Loại event từ webhook
        handler_id: ID của handler/command để process
        auth_type: Loại authentication (signature, token, etc.)
        verify_signature: Có verify signature không
        payload_schema: Schema cho payload
        tags: Danh sách tags
    """

    id: str
    description: str
    path: str
    event_type: str
    handler_id: str
    auth_type: str
    verify_signature: bool
    payload_schema: dict[str, Any]
    tags: list[str]


class RoleParams(TypedDict, total=False):
    """
    Tham số cho Role nodes.

    Role định nghĩa các roles trong RBAC (Role-Based Access Control).
    Mỗi role có các permissions và có thể kế thừa từ parent roles.

    Fields:
        id: Định danh của role
        description: Mô tả role
        permissions: Danh sách permission IDs
        parent_roles: Danh sách parent role IDs (inheritance)
        tenant_scope: Phạm vi multi-tenancy
        tags: Danh sách tags
    """

    id: str
    description: str
    permissions: list[str]
    parent_roles: list[str]
    tenant_scope: str
    tags: list[str]


class PermissionParams(TypedDict, total=False):
    """
    Tham số cho Permission nodes.

    Permission định nghĩa các permissions cho RBAC.
    Mỗi permission có resource và action.

    Fields:
        id: Định danh của permission
        description: Mô tả permission
        resource: Resource mà permission áp dụng
        action: Action được phép (read, write, delete, etc.)
        conditions: Các điều kiện bổ sung
        tags: Danh sách tags
    """

    id: str
    description: str
    resource: str
    action: str
    conditions: list[dict[str, Any]]
    tags: list[str]


class PolicyParams(TypedDict, total=False):
    """
    Tham số cho Policy nodes.

    Policy định nghĩa các access policies cho ABAC (Attribute-Based Access Control).
    Bao gồm subject, action, resource, và conditions.

    Fields:
        id: Định danh của policy
        description: Mô tả policy
        effect: Effect của policy (ALLOW, DENY)
        subject: Subject conditions (roles, attributes)
        action: Danh sách actions
        resource: Resource conditions
        conditions: Các điều kiện bổ sung
        tags: Danh sách tags
    """

    id: str
    description: str
    effect: str
    subject: dict[str, Any]
    action: list[str]
    resource: dict[str, Any]
    conditions: list[dict[str, Any]]
    tags: list[str]


class DataSourceParams(TypedDict, total=False):
    """
    Tham số cho DataSource nodes.

    DataSource định nghĩa các database connections.
    Bao gồm type, connection string, và schema.

    Fields:
        id: Định danh của datasource
        type: Loại datasource (postgresql, mysql, mongodb, etc.)
        name: Tên datasource
        connection_string: Connection string
        schema: Database schema name
        config: Các config options bổ sung
    """

    id: str
    type: str
    name: str
    connection_string: str
    schema: str
    config: dict[str, Any]


class CacheParams(TypedDict, total=False):
    """
    Tham số cho Cache nodes.

    Cache định nghĩa các cache configurations.
    Bao gồm backend, TTL, serialization, tenant isolation, CDN, stampede prevention.

    Fields:
        id: Định danh duy nhất của cache profile
        backend: Loại cache (redis, memcached, memory)
        name: Tên cache (alias)
        ttl: Time-to-live mặc định (giây)
        max_size: Kích thước tối đa của cache
        serializer: Serializer cho cache data (json, pickle)
        key_prefix: Prefix cho cache keys
        tenant_isolated: Có enforce tenant isolation không (KPI-029)
        strategy: Strategy caching (read_through, write_through, cache_aside)
        invalidation_strategy: Invalidation strategy (pattern, tag, event)
        cdn_enabled: Có enable CDN cache không
        cdn_provider: CDN provider (cloudflare, cloudfront, fastly, akamai)
        stampede_prevention: Có enable stampede prevention không
        stampede_strategy: Stampede strategy (mutex, early_update, probabilistic, lease)
        multi_tier: Có enable multi-tier cache không
        warmup_enabled: Có enable cache warmup không
        config: Cache configuration (legacy, backward compat)
        tags: Danh sách tags
    """

    id: str
    backend: str
    name: str
    ttl: int
    max_size: int
    serializer: str
    key_prefix: str
    tenant_isolated: bool
    strategy: str
    invalidation_strategy: str
    cdn_enabled: bool
    cdn_provider: str
    stampede_prevention: bool
    stampede_strategy: str
    multi_tier: bool
    warmup_enabled: bool
    config: dict[str, Any]
    tags: list[str]


class QueueParams(TypedDict, total=False):
    """
    Tham số cho Queue nodes.

    Queue định nghĩa các message queues cho async processing.
    Bao gồm type, configuration, và retry policies.

    Fields:
        id: Định danh của queue
        type: Loại queue (rabbitmq, sqs, kafka)
        name: Tên queue
        config: Queue configuration
        tags: Danh sách tags
    """

    id: str
    type: str
    name: str
    config: dict[str, Any]
    tags: list[str]


class IntegrationParams(TypedDict, total=False):
    """
    Tham số cho Integration nodes.

    Integration định nghĩa các external integrations.
    Bao gồm provider, auth type, và configuration.

    Fields:
        id: Định danh của integration
        name: Tên integration
        type: Loại integration (payment, email, sms, etc.)
        provider: Provider name (stripe, sendgrid, etc.)
        auth_type: Authentication type
        config: Integration configuration
        required: Có bắt buộc không
    """

    id: str
    name: str
    type: str
    provider: str
    auth_type: str
    config: dict[str, Any]
    required: bool


class AuthProviderParams(TypedDict, total=False):
    """
    Tham số cho AuthProvider nodes.

    AuthProvider định nghĩa các authentication providers.
    Bao gồm OAuth2, OIDC, SAML configurations.

    Fields:
        id: Định danh của auth provider
        type: Loại provider (oauth2, oidc, saml)
        provider: Provider name
        config: Provider configuration
        scopes: OAuth scopes
        token_endpoint: Token endpoint URL
        auth_endpoint: Authorization endpoint URL
        jwks_uri: JWKS URI cho key discovery
    """

    id: str
    type: str
    provider: str
    config: dict[str, Any]
    scopes: list[str]
    token_endpoint: str
    auth_endpoint: str
    jwks_uri: str


class TableParams(TypedDict, total=False):
    """
    Tham số cho Table nodes.

    Table định nghĩa các database tables mapping từ entities.
    Bao gồm columns, indexes, và constraints.

    Fields:
        id: Định danh của table
        name: Tên table trong database
        entity_id: ID của entity được map
        datasource: ID của datasource
        schema: Schema name
        columns: Danh sách các columns
        indexes: Danh sách các indexes
        constraints: Danh sách các constraints
    """

    id: str
    name: str
    entity_id: str
    datasource: str
    schema: str
    columns: list[dict[str, Any]]
    indexes: list[dict[str, Any]]
    constraints: list[dict[str, Any]]


class IndexParams(TypedDict, total=False):
    """
    Tham số cho Index nodes.

    Index định nghĩa các database indexes.
    Bao gồm columns, type, và uniqueness.

    Fields:
        id: Định danh của index
        name: Tên index
        table_id: ID của table
        columns: Danh sách các columns
        unique: Có unique index không
        type: Loại index (btree, hash, etc.)
        config: Các config options
    """

    id: str
    name: str
    table_id: str
    columns: list[str]
    unique: bool
    type: str
    config: dict[str, Any]


class MetricParams(TypedDict, total=False):
    """
    Tham số cho Metric nodes.

    Metric định nghĩa các application metrics cho monitoring.
    Bao gồm type, name, labels, và aggregation.

    Fields:
        id: Định danh của metric
        description: Mô tả metric
        type: Loại metric (counter, gauge, histogram, summary)
        name: Tên metric
        unit: Đơn vị đo lường
        labels: Danh sách các labels
        aggregation: Aggregation method
        config: Các config options
    """

    id: str
    description: str
    type: str
    name: str
    unit: str
    labels: list[str]
    aggregation: str
    config: dict[str, Any]


class LogParams(TypedDict, total=False):
    """
    Tham số cho Log nodes.

    Log định nghĩa các structured logging configurations.
    Bao gồm level, format, và output destinations.

    Fields:
        id: Định danh của log config
        description: Mô tả
        name: Tên logger
        level: Log level (DEBUG, INFO, WARN, ERROR)
        format: Log format (json, text)
        fields: Các fields để include trong log
        output: Output destination
        config: Các config options
    """

    id: str
    description: str
    name: str
    level: str
    format: str
    fields: list[dict[str, Any]]
    output: str
    config: dict[str, Any]


class AlertParams(TypedDict, total=False):
    """
    Tham số cho Alert nodes.

    Alert định nghĩa các alerting rules.
    Bao gồm condition, severity, và notification channels.

    Fields:
        id: Định danh của alert
        description: Mô tả alert
        name: Tên alert
        condition: Điều kiện để trigger alert
        severity: Mức độ nghiêm trọng
        channels: Danh sách notification channels
        cooldown: Cooldown period giữa các alerts
        config: Các config options
    """

    id: str
    description: str
    name: str
    condition: dict[str, Any]
    severity: str
    channels: list[str]
    cooldown: str
    config: dict[str, Any]


class TraceParams(TypedDict, total=False):
    """
    Tham số cho Trace nodes.

    Trace định nghĩa distributed tracing configurations.
    Bao gồm sampling rate và exporter.

    Fields:
        id: Định danh của trace config
        description: Mô tả
        name: Tên tracer
        sampling_rate: Tỷ lệ sampling (0.0 - 1.0)
        exporter: Exporter type (jaeger, zipkin, otel)
        config: Các config options
    """

    id: str
    description: str
    name: str
    sampling_rate: float
    exporter: str
    config: dict[str, Any]


# ============================================================================
# P0: Reporting & Analytics Params
# ============================================================================


class ReportParams(TypedDict, total=False):
    """
    Tham số cho Report nodes.

    Report định nghĩa các business reports.
    Bao gồm data sources, fields, filters, groupings, và aggregations.

    Fields:
        id: Định danh của report
        description: Mô tả report
        name: Tên report hiển thị
        data_sources: Danh sách data source IDs
        fields: Các fields trong report
        filters: Các filters
        groupings: Các group by fields
        aggregations: Các aggregations (sum, avg, count)
        format: Format export (CSV, PDF, Excel)
        schedule: Schedule cho auto-generation
        recipients: Danh sách recipients
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    data_sources: list[str]
    fields: list[dict[str, Any]]
    filters: list[dict[str, Any]]
    groupings: list[str]
    aggregations: list[dict[str, Any]]
    format: str
    schedule: str
    recipients: list[str]
    tags: list[str]


class DashboardParams(TypedDict, total=False):
    """
    Tham số cho Dashboard nodes.

    Dashboard định nghĩa các monitoring dashboards.
    Bao gồm widgets, refresh intervals, và permissions.

    Fields:
        id: Định danh của dashboard
        description: Mô tả dashboard
        name: Tên dashboard hiển thị
        widgets: Danh sách các widgets (charts, tables, metrics)
        refresh_interval: Thời gian tự refresh
        filters: Các filters áp dụng cho toàn dashboard
        permissions: Permissions để view dashboard
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    widgets: list[dict[str, Any]]
    refresh_interval: str
    filters: list[dict[str, Any]]
    permissions: list[str]
    tags: list[str]


class ExportParams(TypedDict, total=False):
    """
    Tham số cho Export nodes.

    Export định nghĩa các data export configurations.
    Bao gồm source, format, template, và destination.

    Fields:
        id: Định danh của export
        description: Mô tả export
        name: Tên export
        source_id: ID của data source
        format: Format export (CSV, Excel, PDF, JSON)
        template: Template cho formatting
        fields: Các fields để export
        schedule: Schedule cho auto-export
        destination: Destination (S3, email, SFTP)
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    source_id: str
    format: str
    template: str
    fields: list[dict[str, Any]]
    schedule: str
    destination: str
    tags: list[str]


class ScheduledReportParams(TypedDict, total=False):
    """
    Tham số cho ScheduledReport nodes.

    ScheduledReport định nghĩa các auto-generated reports.
    Bao gồm frequency, time, và recipients.

    Fields:
        id: Định danh của scheduled report
        description: Mô tả
        report_id: ID của report để generate
        frequency: Tần suất (daily, weekly, monthly)
        time: Thời điểm generate
        recipients: Danh sách recipients
        format: Format gửi
        enabled: Có active không
        tags: Danh sách tags
    """

    id: str
    description: str
    report_id: str
    frequency: str
    time: str
    recipients: list[str]
    format: str
    enabled: bool
    tags: list[str]


# ============================================================================
# P0: Notification Params
# ============================================================================


class NotificationChannelParams(TypedDict, total=False):
    """
    Tham số cho NotificationChannel nodes.

    NotificationChannel định nghĩa các channels để send notifications.
    Ví dụ: email, SMS, push, in-app.

    Fields:
        id: Định danh của channel
        description: Mô tả
        name: Tên channel
        type: Loại channel (email, sms, push, in_app)
        config: Channel configuration
        enabled: Có active không
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    type: str
    config: dict[str, Any]
    enabled: bool
    tags: list[str]


class NotificationTemplateParams(TypedDict, total=False):
    """
    Tham số cho NotificationTemplate nodes.

    NotificationTemplate định nghĩa các templates cho notifications.
    Bao gồm subject, body, và variables.

    Fields:
        id: Định danh của template
        description: Mô tả
        name: Tên template
        channel_type: Loại channel áp dụng
        subject: Subject cho email/push
        body: Body message với template variables
        variables: Danh sách các variables
        locale: Locale (vi_VN, en_US)
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    channel_type: str
    subject: str
    body: str
    variables: list[dict[str, Any]]
    locale: str
    tags: list[str]


class NotificationRuleParams(TypedDict, total=False):
    """
    Tham số cho NotificationRule nodes.

    NotificationRule định nghĩa các rules để trigger notifications.
    Bao gồm event type, condition, và priority.

    Fields:
        id: Định danh của rule
        description: Mô tả
        name: Tên rule
        event_type: Loại event trigger
        condition: Điều kiện để send
        template_id: ID của template
        channel_ids: Danh sách channel IDs
        priority: Priority (critical, high, medium, low)
        enabled: Có active không
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    event_type: str
    condition: dict[str, Any]
    template_id: str
    channel_ids: list[str]
    priority: str
    enabled: bool
    tags: list[str]


class MessageQueueParams(TypedDict, total=False):
    """
    Tham số cho MessageQueue nodes.

    MessageQueue định nghĩa các queues cho async messaging.
    Dùng cho notification delivery và event processing.

    Fields:
        id: Định danh của queue
        description: Mô tả
        name: Tên queue
        type: Loại queue (rabbitmq, kafka, sqs)
        config: Queue configuration
        retry_policy: Policy cho retry
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    type: str
    config: dict[str, Any]
    retry_policy: dict[str, Any]
    tags: list[str]


# ============================================================================
# P0: Compliance & Regulatory Params
# ============================================================================


class ComplianceRuleParams(TypedDict, total=False):
    """
    Tham số cho ComplianceRule nodes.

    ComplianceRule định nghĩa các regulatory requirements.
    Bao gồm framework, control type, và validation rules.

    Fields:
        id: Định danh của rule
        description: Mô tả
        name: Tên rule
        framework: Regulatory framework (HIPAA, PCI-DSS, GDPR, SOX)
        requirement_id: ID của requirement trong framework
        control_type: Loại control (preventive, detective, corrective)
        validation: Validation rules
        evidence: Danh sách evidence IDs
        enabled: Có active không
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    framework: str
    requirement_id: str
    control_type: str
    validation: dict[str, Any]
    evidence: list[str]
    enabled: bool
    tags: list[str]


class RegulatoryOverlayParams(TypedDict, total=False):
    """
    Tham số cho RegulatoryOverlay nodes.

    RegulatoryOverlay áp dụng regulatory requirements lên DSL.
    Bao gồm framework version và jurisdictions.

    Fields:
        id: Định danh của overlay
        description: Mô tả
        name: Tên overlay
        framework: Regulatory framework name
        version: Version của framework
        rules: Danh sách rule IDs
        jurisdictions: Danh sách jurisdictions áp dụng
        effective_date: Ngày có hiệu lực
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    framework: str
    version: str
    rules: list[str]
    jurisdictions: list[str]
    effective_date: str
    tags: list[str]


class DataRetentionParams(TypedDict, total=False):
    """
    Tham số cho DataRetention nodes.

    DataRetention định nghĩa retention policies cho data.
    Bao gồm retention period, disposal actions, và legal basis.

    Fields:
        id: Định danh của retention policy
        description: Mô tả
        name: Tên policy
        entity_id: ID của entity áp dụng
        retention_period: Thời gian giữ (30d, 1y, 7y)
        retention_type: Loại retention (hard, soft)
        disposal_action: Hành động sau khi expire (delete, archive, anonymize)
        legal_basis: Cơ sở pháp lý cho retention
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    entity_id: str
    retention_period: str
    retention_type: str
    disposal_action: str
    legal_basis: str
    tags: list[str]


class PIIClassificationParams(TypedDict, total=False):
    """
    Tham số cho PIIClassification nodes.

    PIIClassification phân loại PII (Personally Identifiable Information).
    Bao gồm sensitivity levels và masking rules.

    Fields:
        id: Định danh của classification
        description: Mô tả
        name: Tên classification
        field_id: ID của field được phân loại
        pii_type: Loại PII (email, phone, ssn, credit_card)
        sensitivity: Mức độ nhạy cảm (low, medium, high, critical)
        masking_rule: Rule cho masking
        encryption_required: Có cần encrypt không
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    field_id: str
    pii_type: str
    sensitivity: str
    masking_rule: str
    encryption_required: bool
    tags: list[str]


class AuditEventParams(TypedDict, total=False):
    """
    Tham số cho AuditEvent nodes.

    AuditEvent định nghĩa các events cần audit logging.
    Bao gồm event type, fields, và retention period.

    Fields:
        id: Định danh của audit event
        description: Mô tả
        name: Tên event
        event_type: Loại event (create, update, delete, access)
        entity_id: ID của entity
        fields: Các fields cần log
        retention_period: Thời gian giữ audit logs
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    event_type: str
    entity_id: str
    fields: list[dict[str, Any]]
    retention_period: str
    tags: list[str]


class CorrelationStrategyParams(TypedDict, total=False):
    """
    Tham số cho CorrelationStrategy nodes.

    CorrelationStrategy định nghĩa trace correlation cho distributed systems.
    Bao gồm strategy type và header propagation.

    Fields:
        id: Định danh của strategy
        description: Mô tả
        name: Tên strategy
        strategy: Loại strategy (trace_id, correlation_id, request_id)
        header_name: Header name cho correlation
        propagation: Danh sách services để propagate
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    strategy: str
    header_name: str
    propagation: list[str]
    tags: list[str]


# ============================================================================
# P0: Integration Contract Params
# ============================================================================


class APIContractParams(TypedDict, total=False):
    """
    Tham số cho APIContract nodes.

    APIContract định nghĩa external API specifications.
    Bao gồm protocol, endpoints, auth, và rate limits.

    Fields:
        id: Định danh của contract
        description: Mô tả
        name: Tên contract
        protocol: Protocol (REST, GraphQL, gRPC, SOAP)
        version: API version
        base_url: Base URL
        endpoints: Danh sách các endpoints
        auth_type: Authentication type
        rate_limit: Rate limit configuration
        schema: API schema (OpenAPI, etc.)
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    protocol: str
    version: str
    base_url: str
    endpoints: list[dict[str, Any]]
    auth_type: str
    rate_limit: dict[str, Any]
    schema: dict[str, Any]
    tags: list[str]


class EventSchemaParams(TypedDict, total=False):
    """
    Tham số cho EventSchema nodes.

    EventSchema định nghĩa schemas cho domain events.
    Bao gồm version, type, và subscribers.

    Fields:
        id: Định danh của schema
        description: Mô tả
        name: Tên schema
        version: Schema version
        type: Loại event type
        schema: Event schema (JSON Schema)
        publisher: Publisher ID
        subscribers: Danh sách subscriber IDs
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    version: str
    type: str
    schema: dict[str, Any]
    publisher: str
    subscribers: list[str]
    tags: list[str]


class DataMapperParams(TypedDict, total=False):
    """
    Tham số cho DataMapper nodes.

    DataMapper định nghĩa field-level transformations giữa schemas.
    Dùng cho data integration và migration.

    Fields:
        id: Định danh của mapper
        description: Mô tả
        name: Tên mapper
        source_schema: Schema nguồn
        target_schema: Schema đích
        mappings: Danh sách field mappings
        transformation: Transformation rules
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    source_schema: str
    target_schema: str
    mappings: list[dict[str, Any]]
    transformation: str
    tags: list[str]


# ============================================================================
# P1: Workflow Enhancement Params
# ============================================================================


class WorkflowGatewayParams(TypedDict, total=False):
    """
    Tham số cho WorkflowGateway nodes.

    WorkflowGateway định nghĩa gateways trong BPMN workflows.
    Bao gồm parallel, exclusive, và inclusive gateways.

    Fields:
        id: Định danh của gateway
        description: Mô tả
        name: Tên gateway
        type: Loại gateway (parallel, exclusive, inclusive)
        conditions: Danh sách conditions
        branches: Danh sách branch IDs
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    type: str
    conditions: list[dict[str, Any]]
    branches: list[str]
    tags: list[str]


class WorkflowTimerParams(TypedDict, total=False):
    """
    Tham số cho WorkflowTimer nodes.

    WorkflowTimer định nghĩa timers và delays trong workflows.
    Bao gồm duration và cron expressions.

    Fields:
        id: Định danh của timer
        description: Mô tả
        name: Tên timer
        duration: Thời gian delay (PT1H, P1D)
        cron: Cron expression cho recurring timers
        action: Action khi timer trigger
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    duration: str
    cron: str
    action: str
    tags: list[str]


class WorkflowSubprocessParams(TypedDict, total=False):
    """
    Tham số cho WorkflowSubprocess nodes.

    WorkflowSubprocess định nghĩa nested workflows.
    Bao gồm input/output mappings.

    Fields:
        id: Định danh của subprocess
        description: Mô tả
        name: Tên subprocess
        workflow_id: ID của nested workflow
        input_mapping: Mapping từ parent input
        output_mapping: Mapping đến parent output
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    workflow_id: str
    input_mapping: dict[str, Any]
    output_mapping: dict[str, Any]
    tags: list[str]


class WorkflowCompensationParams(TypedDict, total=False):
    """
    Tham số cho WorkflowCompensation nodes.

    WorkflowCompensation định nghĩa compensation actions cho saga patterns.
    Dùng cho rollback khi workflow fail.

    Fields:
        id: Định danh của compensation
        description: Mô tả
        name: Tên compensation
        trigger: Điều kiện trigger compensation
        actions: Danh sách compensation actions
        order: Order của execution (reverse, sequential)
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    trigger: str
    actions: list[dict[str, Any]]
    order: str
    tags: list[str]


class HumanTaskParams(TypedDict, total=False):
    """
    Tham số cho HumanTask nodes.

    HumanTask định nghĩa các human approvals trong workflows.
    Bao gồm assignee, form, và deadline.

    Fields:
        id: Định danh của task
        description: Mô tả
        name: Tên task
        assignee_type: Loại assignee (role, user, group)
        assignee: Assignee ID
        form_id: ID của form
        deadline: Deadline cho completion
        approval_required: Có cần approval không
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    assignee_type: str
    assignee: str
    form_id: str
    deadline: str
    approval_required: bool
    tags: list[str]


# ============================================================================
# P1: Event-Driven Architecture Params
# ============================================================================


class EventPublisherParams(TypedDict, total=False):
    """
    Tham số cho EventPublisher nodes.

    EventPublisher định nghĩa các event publishers.
    Bao gồm trigger và payload templates.

    Fields:
        id: Định danh của publisher
        description: Mô tả
        name: Tên publisher
        event_type: Loại event
        trigger: Điều kiện trigger publish
        payload_template: Template cho payload
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    event_type: str
    trigger: str
    payload_template: dict[str, Any]
    tags: list[str]


class EventSubscriberParams(TypedDict, total=False):
    """
    Tham số cho EventSubscriber nodes.

    EventSubscriber định nghĩa các event subscribers.
    Bao gồm handler, filters, và retry policies.

    Fields:
        id: Định danh của subscriber
        description: Mô tả
        name: Tên subscriber
        event_type: Loại event để subscribe
        handler_id: ID của handler
        filter: Filter conditions
        retry_policy: Retry configuration
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    event_type: str
    handler_id: str
    filter: dict[str, Any]
    retry_policy: dict[str, Any]
    tags: list[str]


class EventBusParams(TypedDict, total=False):
    """
    Tham số cho EventBus nodes.

    EventBus định nghĩa event bus infrastructure.
    Bao gồm topics và configuration.

    Fields:
        id: Định danh của event bus
        description: Mô tả
        name: Tên bus
        type: Loại bus (kafka, rabbitmq, sqs)
        config: Bus configuration
        topics: Danh sách topics
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    type: str
    config: dict[str, Any]
    topics: list[str]
    tags: list[str]


class CQRSProjectionParams(TypedDict, total=False):
    """
    Tham số cho CQRSProjection nodes.

    CQRSProjection định nghĩa read models cho CQRS patterns.
    Bao gồm source events và transformations.

    Fields:
        id: Định danh của projection
        description: Mô tả
        name: Tên projection
        source_events: Danh sách source event types
        target_entity: Entity để materialize
        transformation: Transformation rules
        materialization: Loại materialization (read_model, view)
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    source_events: list[str]
    target_entity: str
    transformation: dict[str, Any]
    materialization: str
    tags: list[str]


class EventSourcingStreamParams(TypedDict, total=False):
    """
    Tham số cho EventSourcingStream nodes.

    EventSourcingStream định nghĩa event streams cho event sourcing.
    Bao gồm aggregate, versioning, và snapshots.

    Fields:
        id: Định danh của stream
        description: Mô tả
        name: Tên stream
        aggregate_id: ID của aggregate
        events: Danh sách event types
        versioning: Versioning strategy (optimistic, concurrent)
        snapshot_interval: Interval cho snapshots
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    aggregate_id: str
    events: list[str]
    versioning: str
    snapshot_interval: int
    tags: list[str]


# ============================================================================
# P1: Search & Indexing Params
# ============================================================================


class SearchIndexParams(TypedDict, total=False):
    """
    Tham số cho SearchIndex nodes.

    SearchIndex định nghĩa full-text search indexes.
    Bao gồm engine, fields, và configurations.

    Fields:
        id: Định danh của index
        description: Mô tả
        name: Tên index
        engine: Search engine (elasticsearch, opensearch)
        entity_id: Entity để index
        fields: Danh sách các fields
        config: Index configuration
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    engine: str
    entity_id: str
    fields: list[dict[str, Any]]
    config: dict[str, Any]
    tags: list[str]


class SearchQueryParams(TypedDict, total=False):
    """
    Tham số cho SearchQuery nodes.

    SearchQuery định nghĩa search queries với filters.
    Bao gồm query types và field specifications.

    Fields:
        id: Định danh của query
        description: Mô tả
        name: Tên query
        index_id: ID của search index
        query_type: Loại query (full_text, faceted, hybrid)
        fields: Danh sách search fields
        filters: Danh sách filters
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    index_id: str
    query_type: str
    fields: list[str]
    filters: list[dict[str, Any]]
    tags: list[str]


class FullTextFieldParams(TypedDict, total=False):
    """
    Tham số cho FullTextField nodes.

    FullTextField định nghĩa các fields có full-text search.
    Bao gồm analyzers và searchability settings.

    Fields:
        id: Định danh của field
        description: Mô tả
        name: Tên field
        entity_id: ID của entity
        field_name: Tên field trong entity
        analyzer: Analyzer type (standard, keyword, ngram)
        searchable: Có searchable không
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    entity_id: str
    field_name: str
    analyzer: str
    searchable: bool
    tags: list[str]


class VectorSearchParams(TypedDict, total=False):
    """
    Tham số cho Vector Search Index nodes.

    Vector Search Index định nghĩa các index cho similarity search trên embedding vectors.
    Hỗ trợ hybrid search (vector + fulltext) và multi-tenancy.

    Fields:
        id: Định danh của index
        description: Mô tả index
        provider: Search engine provider (elasticsearch, meilisearch, qdrant, etc.)
        dimensions: Số chiều của vector (768, 1536, etc.)
        similarity_metric: Hàm tính khoảng cách (cosine, euclidean, dot_product)
        index_type: Loại index structure (hnsw, ivf_flat, ivf_pq, flat)
        vector_column: Tên column chứa vector
        text_columns: Danh sách text columns cho hybrid search
        top_k: Số lượng kết quả mặc định
        tenant_isolated: Có cách ly theo tenant không
        tags: Danh sách tags
    """

    id: str
    description: str
    provider: str
    dimensions: int
    similarity_metric: str
    index_type: str
    vector_column: str
    text_columns: list[str]
    top_k: int
    tenant_isolated: bool
    tags: list[str]


class GeoSearchParams(TypedDict, total=False):
    """
    Tham số cho Geospatial Search Index nodes.

    Geospatial Search Index định nghĩa các index cho tìm kiếm dựa trên vị trí địa lý.
    Hỗ trợ point, polygon, line geometry và các geospatial operations.

    Fields:
        id: Định danh của index
        description: Mô tả index
        provider: Search engine provider (elasticsearch, meilisearch, postgis, etc.)
        geo_column: Tên column chứa dữ liệu địa lý
        geo_type: Loại hình học (point, polygon, line)
        operations: Danh sách geospatial operations (circle, bounding_box, polygon, distance)
        text_columns: Danh sách text columns cho kết hợp với text search
        tenant_isolated: Có cách ly theo tenant không
        tags: Danh sách tags
    """

    id: str
    description: str
    provider: str
    geo_column: str
    geo_type: str
    operations: list[str]
    text_columns: list[str]
    tenant_isolated: bool
    tags: list[str]


class FacetedSearchParams(TypedDict, total=False):
    """
    Tham số cho Faceted Search Index nodes.

    Faceted Search Index định nghĩa các index cho tìm kiếm có phân loại theo nhiều facet.
    Hỗ trợ navigation và filtering theo nhiều chiều dữ liệu.

    Fields:
        id: Định danh của index
        description: Mô tả index
        provider: Search engine provider (elasticsearch, meilisearch, etc.)
        columns: Danh sách column definitions
        facets: Danh sách facet definitions ({id, type, source_column})
        tenant_isolated: Có cách ly theo tenant không
        tags: Danh sách tags
    """

    id: str
    description: str
    provider: str
    columns: list[dict]
    facets: list[dict]
    tenant_isolated: bool
    tags: list[str]


# ============================================================================
# P2: Pagination & API Versioning Params
# ============================================================================


class PaginationSpecParams(TypedDict, total=False):
    """
    Tham số cho PaginationSpec nodes.

    PaginationSpec định nghĩa pagination configurations.
    Bao gồm page size, cursor support, và sort fields.

    Fields:
        id: Định danh của spec
        description: Mô tả
        name: Tên spec
        page_size: Mặc định page size
        max_page_size: Tối đa page size
        cursor_enabled: Có support cursor pagination không
        sort_fields: Danh sách các sortable fields
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    page_size: int
    max_page_size: int
    cursor_enabled: bool
    sort_fields: list[str]
    tags: list[str]


class APIVersionParams(TypedDict, total=False):
    """
    Tham số cho APIVersion nodes.

    APIVersion định nghĩa API versions cho versioning strategy.
    Bao gồm release dates, deprecation, và sunset dates.

    Fields:
        id: Định danh của version
        description: Mô tả
        name: Tên version
        version: Version string (v1, v2)
        api_id: ID của API
        status: Status (active, deprecated, sunset)
        release_date: Ngày release
        deprecation_date: Ngày deprecate
        sunset_date: Ngày sunset
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    version: str
    api_id: str
    status: str
    release_date: str
    deprecation_date: str
    sunset_date: str
    tags: list[str]


class DeprecationNoticeParams(TypedDict, total=False):
    """
    Tham số cho DeprecationNotice nodes.

    DeprecationNotice định nghĩa deprecation notifications.
    Bao gồm reason, migration guide, và sunset date.

    Fields:
        id: Định danh của notice
        description: Mô tả
        name: Tên notice
        api_version_id: ID của API version bị deprecate
        reason: Lý do deprecation
        migration_guide: Link đến migration guide
        sunset_date: Ngày sunset
        tags: Danh sách tags
    """

    id: str
    description: str
    name: str
    api_version_id: str
    reason: str
    migration_guide: str
    sunset_date: str
    tags: list[str]


# ============================================================================
# P2: Domain-Specific Patterns - E-commerce
# ============================================================================


class ShoppingCartParams(TypedDict, total=False):
    """
    Tham số cho ShoppingCart nodes.

    ShoppingCart định nghĩa shopping cart cho e-commerce.
    Bao gồm items, currency, và discount rules.

    Fields:
        id: Định danh của cart
        description: Mô tả
        customer_id: ID của customer
        items: Danh sách cart items
        currency: Currency code (USD, VND)
        discount_rules: Danh sách discount rule IDs
        tags: Danh sách tags
        tenant_scope: Phạm vi multi-tenancy
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    customer_id: str
    items: list[dict[str, Any]]
    currency: str
    discount_rules: list[str]
    tags: list[str]
    tenant_scope: str
    source: str


class ProductCatalogParams(TypedDict, total=False):
    """
    Tham số cho ProductCatalog nodes.

    ProductCatalog định nghĩa product catalog management.
    Bao gồm categories, products, và inventory.

    Fields:
        id: Định danh của catalog
        description: Mô tả
        categories: Danh sách categories
        products: Danh sách product IDs
        inventory_tracking: Có track inventory không
        multi_warehouse: Có multi-warehouse không
        tags: Danh sách tags
        tenant_scope: Phạm vi multi-tenancy
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    categories: list[dict[str, Any]]
    products: list[str]
    inventory_tracking: bool
    multi_warehouse: bool
    tags: list[str]
    tenant_scope: str
    source: str


class PaymentGatewayParams(TypedDict, total=False):
    """
    Tham số cho PaymentGateway nodes.

    PaymentGateway định nghĩa payment processing integrations.
    Bao gồm provider, supported methods, và currencies.

    Fields:
        id: Định danh của gateway
        description: Mô tả
        provider: Provider name (stripe, paypal, midtrans)
        supported_methods: Danh sách payment methods
        currencies: Danh sách supported currencies
        webhook_url: Webhook URL cho callbacks
        sandbox_mode: Có sandbox mode không
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    provider: str
    supported_methods: list[str]
    currencies: list[str]
    webhook_url: str
    sandbox_mode: bool
    tags: list[str]
    source: str


class OrderFulfillmentParams(TypedDict, total=False):
    """
    Tham số cho OrderFulfillment nodes.

    OrderFulfillment định nghĩa order fulfillment processes.
    Bao gồm shipping methods và tracking.

    Fields:
        id: Định danh của fulfillment
        description: Mô tả
        order_id: ID của order
        fulfillment_type: Loại fulfillment (shipping, pickup, delivery)
        shipping_method: Shipping method
        tracking_number: Tracking number
        status: Status (pending, shipped, delivered)
        tags: Danh sách tags
        tenant_scope: Phạm vi multi-tenancy
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    order_id: str
    fulfillment_type: str
    shipping_method: str
    tracking_number: str
    status: str
    tags: list[str]
    tenant_scope: str
    source: str


# ============================================================================
# P2: Domain-Specific Patterns - Finance
# ============================================================================


class GeneralLedgerParams(TypedDict, total=False):
    """
    Tham số cho GeneralLedger nodes.

    GeneralLedger định nghĩa general ledger cho accounting.
    Bao gồm chart of accounts, fiscal year, và accounting standard.

    Fields:
        id: Định danh của ledger
        description: Mô tả
        chart_of_accounts: Danh sách account IDs
        fiscal_year_start: Ngày bắt đầu năm tài chính
        currency: Base currency
        accounting_standard: Chuẩn kế toán (IFRS, GAAP, VAS)
        tags: Danh sách tags
        tenant_scope: Phạm vi multi-tenancy
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    chart_of_accounts: list[str]
    fiscal_year_start: str
    currency: str
    accounting_standard: str
    tags: list[str]
    tenant_scope: str
    source: str


class FinancialInstrumentParams(TypedDict, total=False):
    """
    Tham số cho FinancialInstrument nodes.

    FinancialInstrument định nghĩa các financial instruments.
    Bao gồm symbol, type, và exchange.

    Fields:
        id: Định danh của instrument
        description: Mô tả
        symbol: Trading symbol
        type: Loại instrument (stock, bond, derivative)
        exchange: Exchange name
        currency: Trading currency
        lot_size: Lot size
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    symbol: str
    type: str
    exchange: str
    currency: str
    lot_size: float
    tags: list[str]
    source: str


class CurrencyExchangeParams(TypedDict, total=False):
    """
    Tham số cho CurrencyExchange nodes.

    CurrencyExchange định nghĩa currency exchange rates.
    Bao gồm base/quote currencies và effective dates.

    Fields:
        id: Định danh của exchange rate
        description: Mô tả
        base_currency: Base currency code
        quote_currency: Quote currency code
        exchange_rate: Tỷ giá hối đoái
        effective_date: Ngày có hiệu lực
        source_type: Nguồn rate (manual, api, manual)
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    base_currency: str
    quote_currency: str
    exchange_rate: float
    effective_date: str
    source_type: str
    tags: list[str]
    source: str


class TaxRuleParams(TypedDict, total=False):
    """
    Tham số cho TaxRule nodes.

    TaxRule định nghĩa tax calculation rules.
    Bao gồm tax type, rate, và jurisdiction.

    Fields:
        id: Định danh của rule
        description: Mô tả
        tax_type: Loại tax (VAT, sales_tax, income_tax)
        rate: Tax rate
        jurisdiction: Jurisdiction áp dụng
        applicable_items: Danh sách applicable items
        effective_date: Ngày có hiệu lực
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    tax_type: str
    rate: float
    jurisdiction: str
    applicable_items: list[str]
    effective_date: str
    tags: list[str]
    source: str


# ============================================================================
# P2: Domain-Specific Patterns - Healthcare
# ============================================================================


class PatientRecordParams(TypedDict, total=False):
    """
    Tham số cho PatientRecord nodes.

    PatientRecord định nghĩa patient medical records (EMR/EHR).
    Bao gồm medical history, allergies, và medications.

    Fields:
        id: Định danh của record
        description: Mô tả
        patient_id: ID của patient
        medical_history: Danh sách medical history IDs
        allergies: Danh sách allergies
        medications: Danh sách current medications
        hipaa_compliant: Có HIPAA compliant không
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    patient_id: str
    medical_history: list[str]
    allergies: list[str]
    medications: list[str]
    hipaa_compliant: bool
    tags: list[str]
    source: str


class ClinicalWorkflowParams(TypedDict, total=False):
    """
    Tham số cho ClinicalWorkflow nodes.

    ClinicalWorkflow định nghĩa clinical care workflows.
    Bao gồm clinical decision rules và FHIR mappings.

    Fields:
        id: Định danh của workflow
        description: Mô tả
        workflow_type: Loại workflow (triage, diagnosis, treatment)
        clinical_decision_rules: Danh sách CDR IDs
        patient_safety_checks: Danh sách safety check IDs
        fhir_mappings: Danh sách FHIR resource mappings
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    workflow_type: str
    clinical_decision_rules: list[str]
    patient_safety_checks: list[str]
    fhir_mappings: list[dict[str, Any]]
    tags: list[str]
    source: str


class MedicationParams(TypedDict, total=False):
    """
    Tham số cho Medication nodes.

    Medication định nghĩa medication master data.
    Bao gồm drug name, dosage, và interaction checks.

    Fields:
        id: Định danh của medication
        description: Mô tả
        drug_name: Tên thuốc
        dosage_form: Dạng bào chế
        strength: Liều lượng
        route: Đường dùng
        interaction_checks: Danh sách drug interactions
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    drug_name: str
    dosage_form: str
    strength: str
    route: str
    interaction_checks: list[str]
    tags: list[str]
    source: str


# ============================================================================
# P2: Domain-Specific Patterns - Education
# ============================================================================


class CourseParams(TypedDict, total=False):
    """
    Tham số cho Course nodes.

    Course định nghĩa course structures cho LMS.
    Bao gồm modules, prerequisites, và enrollment.

    Fields:
        id: Định danh của course
        description: Mô tả
        title: Tiêu đề course
        prerequisites: Danh sách prerequisite course IDs
        modules: Danh sách modules
        credits: Số tín chỉ
        enrollment_capacity: Capacity tối đa
        tags: Danh sách tags
        tenant_scope: Phạm vi multi-tenancy
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    title: str
    prerequisites: list[str]
    modules: list[dict[str, Any]]
    credits: float
    enrollment_capacity: int
    tags: list[str]
    tenant_scope: str
    source: str


class GradebookParams(TypedDict, total=False):
    """
    Tham số cho Gradebook nodes.

    Gradebook định nghĩa grading systems.
    Bao gồm grading scales và calculation rules.

    Fields:
        id: Định danh của gradebook
        description: Mô tả
        course_id: ID của course
        grading_scale: Grading scale configuration
        assessment_types: Danh sách assessment type IDs
        calculation_rules: Danh sách calculation rules
        tags: Danh sách tags
        tenant_scope: Phạm vi multi-tenancy
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    course_id: str
    grading_scale: dict[str, Any]
    assessment_types: list[str]
    calculation_rules: list[dict[str, Any]]
    tags: list[str]
    tenant_scope: str
    source: str


# ============================================================================
# P2: Domain-Specific Patterns - Trading/Exchange
# ============================================================================


class OrderBookParams(TypedDict, total=False):
    """
    Tham số cho OrderBook nodes.

    OrderBook định nghĩa order book cho trading systems.
    Bao gồm bids, asks, và matching algorithm.

    Fields:
        id: Định danh của order book
        description: Mô tả
        instrument_id: ID của financial instrument
        bids: Danh sách bid orders
        asks: Danh sách ask orders
        matching_algorithm: Matching algorithm type
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    instrument_id: str
    bids: list[dict[str, Any]]
    asks: list[dict[str, Any]]
    matching_algorithm: str
    tags: list[str]
    source: str


class TradingSessionParams(TypedDict, total=False):
    """
    Tham số cho TradingSession nodes.

    TradingSession định nghĩa trading sessions và hours.
    Bao gồm session type, calendar, và time zones.

    Fields:
        id: Định danh của session
        description: Mô tả
        session_type: Loại session (regular, pre_market, after_hours)
        start_time: Giờ bắt đầu
        end_time: Giờ kết thúc
        time_zone: Time zone
        trading_calendar: Trading calendar ID
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    session_type: str
    start_time: str
    end_time: str
    time_zone: str
    trading_calendar: str
    tags: list[str]
    source: str


class FIXProtocolParams(TypedDict, total=False):
    """
    Tham số cho FIXProtocol nodes.

    FIXProtocol định nghĩa FIX protocol configurations.
    Bao gồm version và message types.

    Fields:
        id: Định danh của protocol config
        description: Mô tả
        version: FIX version (4.4, 5.0)
        message_types: Danh sách supported message types
        session_settings: Session configuration
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    version: str
    message_types: list[str]
    session_settings: dict[str, Any]
    tags: list[str]
    source: str


# ============================================================================
# P2: Domain-Specific Patterns - Logistics
# ============================================================================


class WarehouseZoneParams(TypedDict, total=False):
    """
    Tham số cho WarehouseZone nodes.

    WarehouseZone định nghĩa warehouse zone management.
    Bao gồm zone types, capacity, và location rules.

    Fields:
        id: Định danh của zone
        description: Mô tả
        warehouse_id: ID của warehouse
        zone_type: Loại zone (receiving, storage, picking, shipping)
        capacity: Capacity tối đa
        location_rules: Danh sách location rules
        tags: Danh sách tags
        tenant_scope: Phạm vi multi-tenancy
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    warehouse_id: str
    zone_type: str
    capacity: int
    location_rules: list[dict[str, Any]]
    tags: list[str]
    tenant_scope: str
    source: str


class RouteOptimizationParams(TypedDict, total=False):
    """
    Tham số cho RouteOptimization nodes.

    RouteOptimization định nghĩa delivery route optimization.
    Bao gồm algorithms, constraints, và delivery windows.

    Fields:
        id: Định danh của optimization config
        description: Mô tả
        algorithm: Algorithm type (greedy, genetic, OR-Tools)
        constraints: Danh sách constraints
        delivery_windows: Danh sách delivery windows
        optimization_criteria: Danh sách optimization criteria
        tags: Danh sách tags
        tenant_scope: Phạm vi multi-tenancy
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    algorithm: str
    constraints: list[dict[str, Any]]
    delivery_windows: list[dict[str, Any]]
    optimization_criteria: list[str]
    tags: list[str]
    tenant_scope: str
    source: str


# ============================================================================
# P2: Advanced Patterns - Caching & Performance
# ============================================================================


class CacheStrategyParams(TypedDict, total=False):
    """
    Tham số cho CacheStrategy nodes.

    CacheStrategy định nghĩa caching strategies và policies.
    Bao gồm eviction policies, TTL, và invalidation rules.

    Fields:
        id: Định danh của strategy
        description: Mô tả
        cache_type: Loại cache (distributed, local, hybrid)
        eviction_policy: Eviction policy (LRU, LFU, FIFO)
        ttl_seconds: Time-to-live mặc định
        max_size: Max cache size
        invalidation_rules: Danh sách invalidation rules
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    cache_type: str
    eviction_policy: str
    ttl_seconds: int
    max_size: int
    invalidation_rules: list[dict[str, Any]]
    tags: list[str]
    source: str


class RateLimiterParams(TypedDict, total=False):
    """
    Tham số cho RateLimiter nodes.

    RateLimiter định nghĩa rate limiting configurations.
    Bao gồm algorithm, limits, và scope.

    Fields:
        id: Định danh của limiter
        description: Mô tả
        algorithm: Algorithm type (token_bucket, sliding_window, fixed_window)
        requests_per_second: Số requests tối đa mỗi giây
        burst_size: Burst size
        scope: Scope của rate limit (global, user, ip)
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    algorithm: str
    requests_per_second: int
    burst_size: int
    scope: str
    tags: list[str]
    source: str


# ============================================================================
# P2: Advanced Patterns - Testing & Quality
# ============================================================================


class TestSuiteParams(TypedDict, total=False):
    """
    Tham số cho TestSuite nodes.

    TestSuite định nghĩa test suites cho automated testing.
    Bao gồm test types, cases, và coverage requirements.

    Fields:
        id: Định danh của test suite
        description: Mô tả
        test_type: Loại test (unit, integration, e2e, contract)
        test_cases: Danh sách test cases
        coverage_requirements: Coverage requirements
        execution_order: Execution order
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    test_type: str
    test_cases: list[dict[str, Any]]
    coverage_requirements: dict[str, Any]
    execution_order: list[str]
    tags: list[str]
    source: str


class QualityGateParams(TypedDict, total=False):
    """
    Tham số cho QualityGate nodes.

    QualityGate định nghĩa quality gates cho CI/CD.
    Bao gồm criteria, thresholds, và actions on failure.

    Fields:
        id: Định danh của quality gate
        description: Mô tả
        gate_type: Loại gate (code_quality, security, performance)
        criteria: Danh sách criteria
        thresholds: Threshold values
        action_on_failure: Hành động khi fail (block, warn, notify)
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    gate_type: str
    criteria: list[dict[str, Any]]
    thresholds: dict[str, Any]
    action_on_failure: str
    tags: list[str]
    source: str


# ============================================================================
# P2: Advanced Patterns - Data Management
# ============================================================================


class DataMigrationParams(TypedDict, total=False):
    """
    Tham số cho DataMigration nodes.

    DataMigration định nghĩa data migration strategies.
    Bao gồm source/target schemas, mappings, và rollback plans.

    Fields:
        id: Định danh của migration
        description: Mô tả
        source_schema: Source schema
        target_schema: Target schema
        mapping_rules: Danh sách mapping rules
        validation_rules: Danh sách validation rule IDs
        rollback_plan: Rollback plan ID
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    source_schema: str
    target_schema: str
    mapping_rules: list[dict[str, Any]]
    validation_rules: list[str]
    rollback_plan: str
    tags: list[str]
    source: str


class BatchJobParams(TypedDict, total=False):
    """
    Tham số cho BatchJob nodes.

    BatchJob định nghĩa batch processing jobs.
    Bao gồm job type, schedule, và error handling.

    Fields:
        id: Định danh của batch job
        description: Mô tả
        job_type: Loại job (etl, aggregation, report_generation)
        schedule: Schedule (cron expression)
        input_sources: Danh sách input source IDs
        output_destinations: Danh sách output destination IDs
        error_handling: Error handling configuration
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    job_type: str
    schedule: str
    input_sources: list[str]
    output_destinations: list[str]
    error_handling: dict[str, Any]
    tags: list[str]
    source: str


# ============================================================================
# P2: Advanced Patterns - Messaging
# ============================================================================


class MessageSchemaParams(TypedDict, total=False):
    """
    Tham số cho MessageSchema nodes.

    MessageSchema định nghĩa schemas cho message payloads.
    Bao gồm schema type, fields, và validation rules.

    Fields:
        id: Định danh của schema
        description: Mô tả
        schema_type: Loại schema (json_schema, avro, protobuf)
        fields: Danh sách các fields
        version: Schema version
        validation_rules: Danh sách validation rules
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    schema_type: str
    fields: list[dict[str, Any]]
    version: str
    validation_rules: list[dict[str, Any]]
    tags: list[str]
    source: str


class DeadLetterQueueParams(TypedDict, total=False):
    """
    Tham số cho DeadLetterQueue nodes.

    DeadLetterQueue định nghĩa DLQ cho failed messages.
    Bao gồm max deliveries, retention, và replay policies.

    Fields:
        id: Định danh của DLQ
        description: Mô tả
        source_queue: ID của source queue
        max_deliveries: Số lần try tối đa trước khi send to DLQ
        retention_period: Thời gian giữ messages
        replay_policy: Policy cho replay (manual, automatic, scheduled)
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    source_queue: str
    max_deliveries: int
    retention_period: str
    replay_policy: str
    tags: list[str]
    source: str


# ============================================================================
# P2: Advanced Patterns - Security
# ============================================================================


class EncryptionKeyParams(TypedDict, total=False):
    """
    Tham số cho EncryptionKey nodes.

    EncryptionKey định nghĩa encryption key management.
    Bao gồm algorithm, key size, và rotation policies.

    Fields:
        id: Định danh của key
        description: Mô tả
        algorithm: Encryption algorithm (AES-256, RSA-2048)
        key_size: Key size in bits
        key_usage: Usage type (encrypt, sign, derive)
        rotation_policy: Rotation policy (30d, 90d, 1y)
        kms_provider: KMS provider (aws_kms, azure_keyvault, hashicorp_vault)
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    algorithm: str
    key_size: int
    key_usage: str
    rotation_policy: str
    kms_provider: str
    tags: list[str]
    source: str


class SecurityPolicyParams(TypedDict, total=False):
    """
    Tham số cho SecurityPolicy nodes.

    SecurityPolicy định nghĩa security policies.
    Bao gồm policy type, rules, và enforcement modes.

    Fields:
        id: Định danh của policy
        description: Mô tả
        policy_type: Loại policy (network, data, access, compliance)
        rules: Danh sách security rules
        enforcement_mode: Enforcement mode (enforce, audit, permissive)
        exceptions: Danh sách exception IDs
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    policy_type: str
    rules: list[dict[str, Any]]
    enforcement_mode: str
    exceptions: list[str]
    tags: list[str]
    source: str


# ============================================================================
# P1/P3: Enhanced Rule & Scoring Params (GAP-P1-01, GAP-P3-02)
# ============================================================================


class RuleScoringParams(TypedDict, total=False):
    """
    Tham số cho RuleScoring nodes (lead scoring, supplier rating).

    RuleScoring định nghĩa scoring models cho decision support.
    Bao gồm features, weights, thresholds, và ML models.

    Fields:
        id: Định danh của scoring model
        description: Mô tả
        name: Tên model
        scoring_model: Loại model (weighted_sum, ml_model, rule_based)
        features: Danh sách scoring features
        weights: Danh sách feature weights
        thresholds: Score thresholds
        output_scale: Output scale (0-100, 1-5 stars)
        ml_model_id: ID của ML model (nếu dùng ML)
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    name: str
    scoring_model: str
    features: list[dict[str, Any]]
    weights: list[dict[str, Any]]
    thresholds: dict[str, Any]
    output_scale: str
    ml_model_id: str
    tags: list[str]
    source: str


class RuleMatcherParams(TypedDict, total=False):
    """
    Tham số cho RuleMatcher nodes (complex condition matching).

    RuleMatcher định nghĩa complex condition matching.
    Bao gồm matcher type, conditions, và combination logic.

    Fields:
        id: Định danh của matcher
        description: Mô tả
        name: Tên matcher
        matcher_type: Loại matcher (regex, semantic, fuzzy)
        conditions: Danh sách conditions
        combination: Combination logic (AND, OR, XOR)
        negation: Có negate không
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    name: str
    matcher_type: str
    conditions: list[dict[str, Any]]
    combination: str
    negation: bool
    tags: list[str]
    source: str


# ============================================================================
# P2/P3: Enhanced Integration & Protocol Params
# ============================================================================


class DeviceIntegrationParams(TypedDict, total=False):
    """
    Tham số cho DeviceIntegration nodes (barcode, RFID, instruments).

    DeviceIntegration định nghĩa hardware device integrations.
    Bao gồm device type, protocol, và polling configurations.

    Fields:
        id: Định danh của integration
        description: Mô tả
        name: Tên integration
        device_type: Loại device (barcode_scanner, rfid_reader, medical_instrument)
        protocol: Communication protocol (usb, bluetooth, rs232, http)
        connection_type: Connection type (direct, gateway, cloud)
        poll_interval: Polling interval
        data_mapping: Data mapping configuration
        calibration: Calibration settings
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    name: str
    device_type: str
    protocol: str
    connection_type: str
    poll_interval: str
    data_mapping: dict[str, Any]
    calibration: dict[str, Any]
    tags: str
    source: str


class HL7FHIRSchemaParams(TypedDict, total=False):
    """
    Tham số cho HL7FHIRSchema nodes (healthcare message standards).

    HL7FHIRSchema định nghĩa HL7/FHIR message schemas.
    Bao gồm standard type, version, và profile URLs.

    Fields:
        id: Định danh của schema
        description: Mô tả
        name: Tên schema
        standard: Standard type (HL7v2, HL7v3, FHIR_R4, FHIR_R5)
        version: Standard version
        resource_type: FHIR resource type (Patient, Observation, etc.)
        profile_url: FHIR profile URL
        mapping_rules: Danh sách mapping rules
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    name: str
    standard: str
    version: str
    resource_type: str
    profile_url: str
    mapping_rules: list[dict[str, Any]]
    tags: list[str]
    source: str


class FIXMessageTypesParams(TypedDict, total=False):
    """
    Tham số cho FIXMessageTypes nodes (trading protocol messages).

    FIXMessageTypes định nghĩa FIX message type specifications.
    Bao gồm version, message types, và tag definitions.

    Fields:
        id: Định danh của message type spec
        description: Mô tả
        name: Tên spec
        fix_version: FIX version (4.4, 5.0)
        message_types: Danh sách message types (NewOrderSingle, ExecutionReport)
        tag_definitions: Danh sách tag definitions
        validation_rules: Danh sách validation rules
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    name: str
    fix_version: str
    message_types: list[str]
    tag_definitions: list[dict[str, Any]]
    validation_rules: list[dict[str, Any]]
    tags: list[str]
    source: str


class VideoConferencingIntegrationParams(TypedDict, total=False):
    """
    Tham số cho VideoConferencingIntegration nodes (Telehealth video).

    VideoConferencingIntegration định nghĩa video conferencing integrations.
    Bao gồm provider, features, và recording settings.

    Fields:
        id: Định danh của integration
        description: Mô tả
        name: Tên integration
        provider: Provider name (zoom, twilio, whereby)
        api_endpoint: API endpoint URL
        auth_type: Authentication type
        features: Danh sách supported features
        recording_enabled: Có enable recording không
        max_participants: Max số participants
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    name: str
    provider: str
    api_endpoint: str
    auth_type: str
    features: list[str]
    recording_enabled: bool
    max_participants: int
    tags: list[str]
    source: str


# ============================================================================
# P3: Advanced Pattern Params
# ============================================================================


class ExternalServiceParams(TypedDict, total=False):
    """
    Tham số cho ExternalService nodes (ML/AI services).

    ExternalService định nghĩa external service integrations.
    Bao gồm service type, endpoints, và retry policies.

    Fields:
        id: Định danh của service
        description: Mô tả
        name: Tên service
        service_type: Loại service (ml_inference, ai_api, third_party_api)
        endpoint: Service endpoint URL
        auth_type: Authentication type
        request_schema: Request schema
        response_schema: Response schema
        timeout_ms: Timeout milliseconds
        retry_policy: Retry configuration
        fallback: Fallback action
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    name: str
    service_type: str
    endpoint: str
    auth_type: str
    request_schema: dict[str, Any]
    response_schema: dict[str, Any]
    timeout_ms: int
    retry_policy: dict[str, Any]
    fallback: str
    tags: list[str]
    source: str


class LocalizationParams(TypedDict, total=False):
    """
    Tham số cho Localization nodes (multi-language support).

    Localization định nghĩa multi-language configurations.
    Bao gồm locales, field mappings, và fallback strategies.

    Fields:
        id: Định danh của localization config
        description: Mô tả
        entity_id: ID của entity để localize
        locales: Danh sách supported locales (vi_VN, en_US, zh_CN)
        default_locale: Default locale
        field_mappings: Danh sách field mappings cho each locale
        fallback_strategy: Fallback strategy (default_locale, empty, error)
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    entity_id: str
    locales: list[str]
    default_locale: str
    field_mappings: list[dict[str, Any]]
    fallback_strategy: str
    tags: list[str]
    source: str


class CircuitBreakerParams(TypedDict, total=False):
    """
    Tham số cho CircuitBreaker nodes (resilience patterns).

    CircuitBreaker định nghĩa circuit breaker patterns cho resilience.
    Bao gồm thresholds, timeouts, và fallback actions.

    Fields:
        id: Định danh của circuit breaker
        description: Mô tả
        name: Tên circuit breaker
        target_service: Target service name
        failure_threshold: Số failures để open circuit
        success_threshold: Số successes để close circuit
        timeout_ms: Timeout milliseconds
        half_open_max_calls: Max calls trong half-open state
        fallback_action: Fallback action khi circuit open
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    name: str
    target_service: str
    failure_threshold: int
    success_threshold: int
    timeout_ms: int
    half_open_max_calls: int
    fallback_action: str
    tags: list[str]
    source: str


class CalendarScheduleParams(TypedDict, total=False):
    """
    Tham số cho CalendarSchedule nodes (academic/business calendars).

    CalendarSchedule định nghĩa calendar systems.
    Bao gồm calendar type, periods, holidays, và recurrence rules.

    Fields:
        id: Định danh của calendar
        description: Mô tả
        name: Tên calendar
        calendar_type: Loại calendar (academic, business, fiscal)
        periods: Danh sách periods (semesters, quarters, months)
        holidays: Danh sách holiday dates
        recurrence_rule: Recurrence rule (RRULE format)
        timezone: Time zone
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    name: str
    calendar_type: str
    periods: list[dict[str, Any]]
    holidays: list[str]
    recurrence_rule: str
    timezone: str
    tags: list[str]
    source: str


class SubledgerParams(TypedDict, total=False):
    """
    Tham số cho Subledger nodes (complex accounting patterns).

    Subledger định nghĩa subledger structures.
    Bao gồm ledger type, parent ledger, và reconciliation rules.

    Fields:
        id: Định danh của subledger
        description: Mô tả
        name: Tên subledger
        ledger_type: Loại subledger (accounts_receivable, accounts_payable, inventory)
        parent_ledger_id: ID của parent general ledger
        account_mapping: Account mapping configuration
        reconciliation_rules: Danh sách reconciliation rules
        posting_schedule: Posting schedule (real_time, daily, monthly)
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    description: str
    name: str
    ledger_type: str
    parent_ledger_id: str
    account_mapping: dict[str, Any]
    reconciliation_rules: list[dict[str, Any]]
    posting_schedule: str
    tags: list[str]
    source: str


# ============================================================================
# CP06: API Gateway & Service Mesh Params (Kong + Consul)
# ============================================================================


class KongGatewayParams(TypedDict, total=False):
    """
    Tham số cho KongGateway nodes (CP06: API Gateway).

    KongGateway định nghĩa Kong Gateway configuration.
    Bao gồm version, global plugins, và tenant scope.

    Fields:
        id: Định danh của gateway
        version: Kong declarative config version (3.0)
        global_plugins: Danh sách global plugin names
        tenant_scope: Phạm vi multi-tenancy (global, tenant_isolated)
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    version: str
    global_plugins: list[str]
    tenant_scope: str
    tags: list[str]
    source: str


class KongServiceParams(TypedDict, total=False):
    """
    Tham số cho KongService nodes (CP06: API Gateway).

    KongService định nghĩa Kong Service cho backend services.
    Bao gồm protocol, host, port, upstream reference, và timeouts.

    Fields:
        id: Định danh của service
        name: Tên service trong Kong
        protocol: Protocol (http, https, grpc, grpcs)
        host: Host của backend service
        port: Port của backend service
        upstream_id: ID của Kong upstream (optional)
        connect_timeout: Connect timeout (ms)
        write_timeout: Write timeout (ms)
        read_timeout: Read timeout (ms)
        retries: Số lần retry
        tenant_scope: Phạm vi multi-tenancy
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    name: str
    protocol: str
    host: str
    port: int
    upstream_id: str
    connect_timeout: int
    write_timeout: int
    read_timeout: int
    retries: int
    tenant_scope: str
    tags: list[str]
    source: str


class KongRouteParams(TypedDict, total=False):
    """
    Tham số cho KongRoute nodes (CP06: API Gateway).

    KongRoute định nghĩa Kong Route cho API endpoints.
    Bao gồm paths, methods, plugins, và rate limiter references.

    Fields:
        id: Định danh của route
        name: Tên route trong Kong
        paths: Danh sách URL paths
        methods: Danh sách HTTP methods
        strip_path: Có strip path prefix không
        plugin_ids: Danh sách plugin IDs để apply
        rate_limiter_id: ID của rate limiter (optional)
        circuit_breaker_id: ID của circuit breaker (optional)
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    name: str
    paths: list[str]
    methods: list[str]
    strip_path: bool
    plugin_ids: list[str]
    rate_limiter_id: str
    circuit_breaker_id: str
    tags: list[str]
    source: str


class KongUpstreamParams(TypedDict, total=False):
    """
    Tham số cho KongUpstream nodes (CP06: API Gateway).

    KongUpstream định nghĩa Kong Upstream cho load balancing.
    Bao gồm load balancing type, health checks, và hashing config.

    Fields:
        id: Định danh của upstream
        name: Tên upstream trong Kong
        type: Load balancing type (round_robin, least_conn, consistent_hash)
        hashes: Danh sách hashing config (cho consistent_hash)
        healthchecks: Health check configuration
        tenant_scope: Phạm vi multi-tenancy
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    name: str
    type: str
    hashes: list[dict[str, Any]]
    healthchecks: dict[str, Any]
    tenant_scope: str
    tags: list[str]
    source: str


class KongPluginParams(TypedDict, total=False):
    """
    Tham số cho KongPlugin nodes (CP06: API Gateway).

    KongPlugin định nghĩa Kong Plugin configuration.
    Bao gồm plugin name và config parameters.

    Fields:
        id: Định danh của plugin
        name: Tên plugin trong Kong (rate-limiting, cors, jwt, etc.)
        config: Plugin configuration parameters
        tenant_scope: Phạm vi multi-tenancy
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    name: str
    config: dict[str, Any]
    tenant_scope: str
    tags: list[str]
    source: str


class ConsulServiceMeshParams(TypedDict, total=False):
    """
    Tham số cho ConsulServiceMesh nodes (CP06: Service Mesh).

    ConsulServiceMesh định nghĩa Consul Service Mesh configuration.
    Bao gồm datacenter, services, và multi-datacenter support.

    Fields:
        id: Định danh của service mesh
        datacenter: Primary datacenter ID
        datacenters: Danh sách tất cả datacenters (multi-DC support)
        services: Danh sách service IDs
        tenant_scope: Phạm vi multi-tenancy
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    datacenter: str
    datacenters: list[str]
    services: list[str]
    tenant_scope: str
    tags: list[str]
    source: str


class ConsulServiceParams(TypedDict, total=False):
    """
    Tham số cho ConsulService nodes (CP06: Service Mesh).

    ConsulService định nghĩa Consul Service registration.
    Bao gồm port, address, tags, health checks, và Connect config.

    Fields:
        id: Định danh của service
        name: Tên service trong Consul
        port: Service port
        address: Service address
        tags: Danh sách Consul tags
        health_checks: Danh sách health check configs
        connect_enabled: Có enable Consul Connect không
        tenant_scope: Phạm vi multi-tenancy
        source: Nguồn định nghĩa
    """

    id: str
    name: str
    port: int
    address: str
    tags: list[str]
    health_checks: list[dict[str, Any]]
    connect_enabled: bool
    tenant_scope: str
    source: str


class ConsulConnectParams(TypedDict, total=False):
    """
    Tham số cho ConsulConnect nodes (CP06: Service Mesh).

    ConsulConnect định nghĩa Consul Connect sidecar proxy configuration.
    Bao gồm mTLS, rate limiting, và upstream definitions.

    Fields:
        id: Định danh của connect config
        service_id: ID của service để attach connect
        proxy_port: Sidecar proxy port
        mtls_enabled: Có enable mTLS không
        verify_server_name: Có verify server name không
        rate_limit: Rate limiting configuration (optional)
        upstreams: Danh sách upstream definitions (optional)
        tenant_scope: Phạm vi multi-tenancy
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    service_id: str
    proxy_port: int
    mtls_enabled: bool
    verify_server_name: bool
    rate_limit: dict[str, Any]
    upstreams: list[dict[str, Any]]
    tenant_scope: str
    tags: list[str]
    source: str


class ConsulHealthCheckParams(TypedDict, total=False):
    """
    Tham số cho ConsulHealthCheck nodes (CP06: Service Mesh).

    ConsulHealthCheck định nghĩa Consul health check configuration.
    Bao gồm check type, path, interval, và thresholds.

    Fields:
        id: Định danh của health check
        service_id: ID của service để attach health check
        type: Check type (http, grpc, tcp, script)
        path: Path cho http checks
        address: Address cho grpc checks
        interval: Check interval (ví dụ: "10s")
        timeout: Check timeout (ví dụ: "5s")
        healthy_threshold: Threshold cho healthy state
        unhealthy_threshold: Threshold cho unhealthy state
        tags: Danh sách tags
        source: Nguồn định nghĩa
    """

    id: str
    service_id: str
    type: str
    path: str
    address: str
    interval: str
    timeout: str
    healthy_threshold: int
    unhealthy_threshold: int
    tags: list[str]
    source: str


# ============================================================================
# Generic Params Union (Tất cả 116 Node Types với CP06)
# ============================================================================

# Union type cho tất cả các loại node params
# Cho phép type-safe handling của arbitrary node types
NodeParams = (
    # Domain Layer
    EntityParams
    | ExtendedValueObjectParams  # VO với complex fields
    | AggregateParams
    | EnumParams
    | ErrorParams
    | EventParams
    # Application Layer
    | CommandParams
    | QueryParams
    | WorkflowParams
    | RuleParams
    | GuardParams
    | EffectParams
    # API Layer
    | HTTPRouteParams
    | GraphQLResolverParams
    | WebhookParams
    # Access Control
    | RoleParams
    | PermissionParams
    | PolicyParams
    # Infrastructure
    | DataSourceParams
    | TableParams
    | IndexParams
    | CacheParams
    | QueueParams
    # Integration
    | IntegrationParams
    | AuthProviderParams
    # Observability
    | MetricParams
    | LogParams
    | AlertParams
    | TraceParams
    # P0: Reporting
    | ReportParams
    | DashboardParams
    | ExportParams
    | ScheduledReportParams
    # P0: Notifications
    | NotificationChannelParams
    | NotificationTemplateParams
    | NotificationRuleParams
    | MessageQueueParams
    # P0: Compliance
    | ComplianceRuleParams
    | RegulatoryOverlayParams
    | DataRetentionParams
    | PIIClassificationParams
    | AuditEventParams
    | CorrelationStrategyParams
    # P0: Integration Contracts
    | APIContractParams
    | EventSchemaParams
    | DataMapperParams
    # P1: Workflow Enhancement
    | WorkflowGatewayParams
    | WorkflowTimerParams
    | WorkflowSubprocessParams
    | WorkflowCompensationParams
    | HumanTaskParams
    # P1: Event-Driven
    | EventPublisherParams
    | EventSubscriberParams
    | EventBusParams
    | CQRSProjectionParams
    | EventSourcingStreamParams
    # P1: Search
    | SearchIndexParams
    | SearchQueryParams
    | FullTextFieldParams
    # P2: Pagination & Versioning
    | PaginationSpecParams
    | APIVersionParams
    | DeprecationNoticeParams
    # P2: E-commerce Domain
    | ShoppingCartParams
    | ProductCatalogParams
    | PaymentGatewayParams
    | OrderFulfillmentParams
    # P2: Finance Domain
    | GeneralLedgerParams
    | FinancialInstrumentParams
    | CurrencyExchangeParams
    | TaxRuleParams
    # P2: Healthcare Domain
    | PatientRecordParams
    | ClinicalWorkflowParams
    | MedicationParams
    # P2: Education Domain
    | CourseParams
    | GradebookParams
    # P2: Trading/Exchange Domain
    | OrderBookParams
    | TradingSessionParams
    | FIXProtocolParams
    # P2: Logistics Domain
    | WarehouseZoneParams
    | RouteOptimizationParams
    # P2: Advanced - Caching & Performance
    | CacheStrategyParams
    | RateLimiterParams
    # P2: Advanced - Testing & Quality
    | TestSuiteParams
    | QualityGateParams
    # P2: Advanced - Data Management
    | DataMigrationParams
    | BatchJobParams
    # P2: Advanced - Messaging
    | MessageSchemaParams
    | DeadLetterQueueParams
    # P2: Advanced - Security
    | EncryptionKeyParams
    | SecurityPolicyParams
    # P1/P3: Enhanced Rule & Scoring
    | RuleScoringParams
    | RuleMatcherParams
    # P2/P3: Enhanced Integration & Protocol
    | DeviceIntegrationParams
    | HL7FHIRSchemaParams
    | FIXMessageTypesParams
    | VideoConferencingIntegrationParams
    # P3: Advanced Patterns
    | ExternalServiceParams
    | LocalizationParams
    | CircuitBreakerParams
    | CalendarScheduleParams
    | SubledgerParams
    # Fallback cho other types
    | dict[str, Any]
)


# ============================================================================
# Node Kind Enum (109 Node Types Tổng cộng)
# ============================================================================


class NodeKind(Enum):
    """
    Enum cho các loại node trong projection tree.

    Tổ chức theo layer/domain để dễ hiểu.

    Layer 1: Foundation
    Layer 2: Domain (6 types)
    Layer 3: Application (6 types)
    Layer 4: Infrastructure (5 types)
    Layer 5: Platform/Access Control (3 types)
    Layer 6: Integration/API (5 types)
    Layer 7: Ops/Observability (4 types)
    P0: Reporting, Notification, Compliance, Integration Contracts (17 types)
    P1: Workflow Enhancement, Event-Driven, Search (16 types)
    P2: Pagination, Versioning, Domain-Specific (25 types)
    P3: Advanced Patterns (7 types)

    Tổng: 109 loại node
    """

    # =========================================================================
    # Layer 2: Domain Layer (6 loại)
    # =========================================================================
    ENTITY = "domain.entity"
    VALUE_OBJECT = "domain.value_object"
    AGGREGATE = "domain.aggregate"
    ENUM = "domain.enum"
    ERROR = "domain.error"
    EVENT = "domain.event"

    # =========================================================================
    # Layer 3: Application Layer (6 loại)
    # =========================================================================
    COMMAND = "app.command"
    QUERY = "app.query"
    WORKFLOW = "app.workflow"
    RULE = "app.rule"
    GUARD = "app.guard"
    EFFECT = "app.effect"

    # =========================================================================
    # Layer 6: API/Interface Layer (3 loại)
    # =========================================================================
    HTTP_ROUTE = "api.http_route"
    GRAPHQL_RESOLVER = "api.graphql_resolver"
    WEBHOOK = "api.webhook"

    # =========================================================================
    # Layer 5: Access Control Layer (3 loại)
    # =========================================================================
    ROLE = "access.role"
    PERMISSION = "access.permission"
    POLICY = "access.policy"

    # =========================================================================
    # Layer 4: Infrastructure Layer (5 loại)
    # =========================================================================
    DATASOURCE = "infra.datasource"
    TABLE = "infra.table"
    INDEX = "infra.index"
    CACHE = "infra.cache"
    QUEUE = "infra.queue"

    # =========================================================================
    # Layer 6: Integration Layer (2 loại)
    # =========================================================================
    INTEGRATION = "integration.external"
    AUTH_PROVIDER = "integration.auth_provider"

    # =========================================================================
    # Layer 7: Observability (4 loại)
    # =========================================================================
    METRIC = "ops.metric"
    LOG = "ops.log"
    TRACE = "ops.trace"
    ALERT = "ops.alert"

    # =========================================================================
    # P0: Reporting & Analytics (4 loại) - GAP-002
    # =========================================================================
    REPORT = "report.definition"
    DASHBOARD = "report.dashboard"
    EXPORT = "report.export"
    SCHEDULED_REPORT = "report.scheduled"

    # =========================================================================
    # P0: Notification (4 loại) - GAP-003
    # =========================================================================
    NOTIFICATION_CHANNEL = "notify.channel"
    NOTIFICATION_TEMPLATE = "notify.template"
    NOTIFICATION_RULE = "notify.rule"
    MESSAGE_QUEUE = "notify.queue"

    # =========================================================================
    # P0: Compliance & Regulatory (6 loại) - GAP-004
    # =========================================================================
    COMPLIANCE_RULE = "compliance.rule"
    REGULATORY_OVERLAY = "compliance.overlay"
    DATA_RETENTION = "compliance.retention"
    PII_CLASSIFICATION = "compliance.pii"
    AUDIT_EVENT = "compliance.audit"
    CORRELATION_STRATEGY = "compliance.correlation"

    # =========================================================================
    # P0: Integration Contracts (3 loại) - GAP-005
    # =========================================================================
    API_CONTRACT = "integration.contract"
    EVENT_SCHEMA = "integration.event_schema"
    DATA_MAPPER = "integration.mapper"

    # =========================================================================
    # P1: Workflow Enhancement (5 loại) - GAP-006
    # =========================================================================
    WORKFLOW_GATEWAY = "workflow.gateway"
    WORKFLOW_TIMER = "workflow.timer"
    WORKFLOW_SUBPROCESS = "workflow.subprocess"
    WORKFLOW_COMPENSATION = "workflow.compensation"
    HUMAN_TASK = "workflow.human_task"

    # =========================================================================
    # P1: Event-Driven Architecture (5 loại) - GAP-008
    # =========================================================================
    EVENT_PUBLISHER = "event.publisher"
    EVENT_SUBSCRIBER = "event.subscriber"
    EVENT_BUS = "event.bus"
    CQRS_PROJECTION = "event.cqrs"
    EVENT_SOURCING_STREAM = "event.sourcing"

    # =========================================================================
    # P1: Search & Indexing (6 loại) - GAP-009
    # =========================================================================
    SEARCH_INDEX = "search.index"
    SEARCH_QUERY = "search.query"
    FULL_TEXT_FIELD = "search.field"
    VECTOR_SEARCH_INDEX = "search.vector_index"
    GEO_SEARCH_INDEX = "search.geo_index"
    FACETED_SEARCH_INDEX = "search.faceted_index"

    # =========================================================================
    # P2: Pagination & API Versioning (3 loại) - GAP-013, GAP-014
    # =========================================================================
    PAGINATION_SPEC = "pagination.spec"
    API_VERSION = "api.version"
    DEPRECATION_NOTICE = "api.deprecation"

    # =========================================================================
    # P2: Domain-Specific - E-commerce (4 loại)
    # =========================================================================
    SHOPPING_CART = "ecommerce.cart"
    PRODUCT_CATALOG = "ecommerce.catalog"
    PAYMENT_GATEWAY = "ecommerce.payment"
    ORDER_FULFILLMENT = "ecommerce.fulfillment"

    # =========================================================================
    # P2: Domain-Specific - Finance (4 loại)
    # =========================================================================
    GENERAL_LEDGER = "finance.ledger"
    FINANCIAL_INSTRUMENT = "finance.instrument"
    CURRENCY_EXCHANGE = "finance.exchange"
    TAX_RULE = "finance.tax"

    # =========================================================================
    # P2: Domain-Specific - Healthcare (3 loại)
    # =========================================================================
    PATIENT_RECORD = "healthcare.patient"
    CLINICAL_WORKFLOW = "healthcare.workflow"
    MEDICATION = "healthcare.medication"

    # =========================================================================
    # P2: Domain-Specific - Education (2 loại)
    # =========================================================================
    COURSE = "education.course"
    GRADEBOOK = "education.gradebook"

    # =========================================================================
    # P2: Domain-Specific - Trading/Exchange (3 loại)
    # =========================================================================
    ORDER_BOOK = "trading.orderbook"
    TRADING_SESSION = "trading.session"
    FIX_PROTOCOL = "trading.fix"

    # =========================================================================
    # P2: Domain-Specific - Logistics (2 loại)
    # =========================================================================
    WAREHOUSE_ZONE = "logistics.warehouse"
    ROUTE_OPTIMIZATION = "logistics.route"

    # =========================================================================
    # P2: Advanced - Caching & Performance (2 loại)
    # =========================================================================
    CACHE_STRATEGY = "advanced.cache"
    RATE_LIMITER = "advanced.ratelimit"

    # =========================================================================
    # P2: Advanced - Testing & Quality (2 loại)
    # =========================================================================
    TEST_SUITE = "advanced.test"
    QUALITY_GATE = "advanced.quality"

    # =========================================================================
    # P2: Advanced - Data Management (2 loại)
    # =========================================================================
    DATA_MIGRATION = "advanced.migration"
    BATCH_JOB = "advanced.batch"

    # =========================================================================
    # P2: Advanced - Messaging (2 loại)
    # =========================================================================
    MESSAGE_SCHEMA = "advanced.schema"
    DEAD_LETTER_QUEUE = "advanced.dlq"

    # =========================================================================
    # P2: Advanced - Security (2 loại)
    # =========================================================================
    ENCRYPTION_KEY = "advanced.encryption"
    SECURITY_POLICY = "advanced.security"

    # =========================================================================
    # P1/P3: Enhanced Rule & Scoring (2 loại) - GAP-P1-01, GAP-P3-02
    # =========================================================================
    RULE_SCORING = "rule.scoring"
    RULE_MATCHER = "rule.matcher"

    # =========================================================================
    # P2/P3: Enhanced Integration & Protocol (4 loại)
    # =========================================================================
    DEVICE_INTEGRATION = "integration.device"  # GAP-P2-03, P3-03 (Barcode/RFID)
    HL7_FHIR_SCHEMA = "integration.hl7fhir"  # GAP-P2-01 (Healthcare HL7/FHIR)
    FIX_MESSAGE_TYPES = "trading.fix_messages"  # GAP-P2-02 (FIX protocol messages)
    VIDEO_CONFERENCING = "integration.video"  # GAP-P2-04 (Telehealth video)

    # =========================================================================
    # P3: Advanced Patterns (5 loại) - GAP-P3-04 đến P3-08
    # =========================================================================
    EXTERNAL_SERVICE = "advanced.external"  # GAP-P3-04 (ML/AI services)
    LOCALIZATION = "advanced.localization"  # GAP-P3-07 (Multi-language)
    CIRCUIT_BREAKER = "advanced.circuit"  # GAP-P3-08 (Resilience patterns)
    CALENDAR_SCHEDULE = "advanced.calendar"  # GAP-P1-02 (Academic calendar)
    SUBLEDGER = "finance.subledger"  # GAP-P3-06 (Complex accounting)

    # =========================================================================
    # CP06: Kong Gateway (5 loại) - API Gateway & Service Mesh
    # =========================================================================
    KONG_GATEWAY = "gateway.kong"  # Kong Gateway configuration
    KONG_SERVICE = "kong.service"  # Kong Service definition
    KONG_ROUTE = "kong.route"  # Kong Route definition
    KONG_UPSTREAM = "kong.upstream"  # Kong Upstream/load balancer
    KONG_PLUGIN = "kong.plugin"  # Kong Plugin configuration

    # =========================================================================
    # CP06: Consul Service Mesh (4 loại) - Service Mesh
    # =========================================================================
    CONSUL_SERVICE_MESH = "mesh.consul"  # Consul Service Mesh configuration
    CONSUL_SERVICE = "consul.service"  # Consul Service definition
    CONSUL_CONNECT = "consul.connect"  # Consul Connect sidecar proxy
    CONSUL_HEALTH_CHECK = "consul.healthcheck"  # Consul Health check




# ============================================================================
# Projection Node
# ============================================================================


@dataclass
class ProjectionNode:
    """
    Node trong projection tree.

    Đại diện cho một khái niệm DSL (entity, command, query, etc.)
    với strong typing cho parameters.

    Attributes:
        id: Định danh duy nhất trong projection
        kind: Loại node (từ NodeKind enum)
        params: Typed parameters cho loại node cụ thể
        metadata: Metadata bổ sung cho documentation/provenance
        source_kind: Original DSL kind nếu transform từ v0
        children: Child nodes (cho hierarchical structures)
        dependencies: Danh sách node IDs mà node này phụ thuộc

    Example:
        node = ProjectionNode(
            id="CreateOrder",
            kind=NodeKind.COMMAND,
            params={
                "description": "Tạo đơn hàng mới",
                "input": [...],
                "guards": [...],
            }
        )
    """

    id: str
    kind: NodeKind
    params: NodeParams
    metadata: dict[str, Any] = field(default_factory=dict)
    source_kind: Optional[str] = None
    children: list["ProjectionNode"] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        Validate node sau khi khởi tạo.

        Kiểm tra:
        - id không được rỗng
        - params có các required fields cho node kind
        """
        if not self.id:
            raise ValueError("ProjectionNode.id là bắt buộc")

        # Validate params theo kind
        self._validate_params()

    def _validate_params(self) -> None:
        """
        Validate params có các required fields cho node kind.

        Raises:
            ValueError: Nếu thiếu required field
        """
        required_fields = self._get_required_fields()
        for field_name in required_fields:
            if field_name not in self.params:
                raise ValueError(
                    f"ProjectionNode {self.kind} '{self.id}' "
                    f"cần field: {field_name}"
                )

    def _get_required_fields(self) -> list[str]:
        """
        Lấy danh sách required fields cho node kind này (106 types).

        Returns:
            Danh sách field names bắt buộc
        """
        required_map: dict[NodeKind, list[str]] = {
            # =========================================================================
            # Layer 2: Domain Layer
            # =========================================================================
            NodeKind.ENTITY: ["id", "fields"],
            NodeKind.VALUE_OBJECT: ["id", "fields"],
            NodeKind.AGGREGATE: ["id", "entity_id"],
            NodeKind.ENUM: ["id", "values"],
            NodeKind.ERROR: ["id", "code", "severity", "category"],
            NodeKind.EVENT: ["id", "type", "source_entity"],

            # =========================================================================
            # Layer 3: Application Layer
            # =========================================================================
            NodeKind.COMMAND: ["id", "input"],
            NodeKind.QUERY: ["id", "returns"],
            NodeKind.WORKFLOW: ["id", "states"],
            NodeKind.RULE: ["id", "type", "condition"],
            NodeKind.GUARD: ["id", "type", "condition"],
            NodeKind.EFFECT: ["id", "type", "target"],

            # =========================================================================
            # Layer 6: API/Interface Layer
            # =========================================================================
            NodeKind.HTTP_ROUTE: ["id", "method", "path"],
            NodeKind.GRAPHQL_RESOLVER: ["id", "operation", "type_name"],
            NodeKind.WEBHOOK: ["id", "path", "event_type"],

            # =========================================================================
            # Layer 5: Access Control Layer
            # =========================================================================
            NodeKind.ROLE: ["id", "permissions"],
            NodeKind.PERMISSION: ["id", "resource", "action"],
            NodeKind.POLICY: ["id", "effect", "action"],

            # =========================================================================
            # Layer 4: Infrastructure Layer
            # =========================================================================
            NodeKind.DATASOURCE: ["id", "type"],
            NodeKind.TABLE: ["id", "entity_id", "datasource"],
            NodeKind.INDEX: ["id", "table_id", "columns"],
            NodeKind.CACHE: ["id", "type"],
            NodeKind.QUEUE: ["id", "type"],

            # =========================================================================
            # Layer 6: Integration Layer
            # =========================================================================
            NodeKind.INTEGRATION: ["id", "type", "provider"],
            NodeKind.AUTH_PROVIDER: ["id", "type", "provider"],

            # =========================================================================
            # Layer 7: Observability
            # =========================================================================
            NodeKind.METRIC: ["id", "type", "name"],
            NodeKind.LOG: ["id", "name", "level"],
            NodeKind.TRACE: ["id", "name"],
            NodeKind.ALERT: ["id", "name", "condition"],

            # =========================================================================
            # P0: Reporting & Analytics
            # =========================================================================
            NodeKind.REPORT: ["id", "data_sources", "fields"],
            NodeKind.DASHBOARD: ["id", "widgets"],
            NodeKind.EXPORT: ["id", "source_id", "format"],
            NodeKind.SCHEDULED_REPORT: ["id", "report_id", "frequency"],

            # =========================================================================
            # P0: Notification
            # =========================================================================
            NodeKind.NOTIFICATION_CHANNEL: ["id", "type"],
            NodeKind.NOTIFICATION_TEMPLATE: ["id", "channel_type", "body"],
            NodeKind.NOTIFICATION_RULE: ["id", "event_type", "condition"],
            NodeKind.MESSAGE_QUEUE: ["id", "type"],

            # =========================================================================
            # P0: Compliance & Regulatory
            # =========================================================================
            NodeKind.COMPLIANCE_RULE: ["id", "framework", "requirement_id"],
            NodeKind.REGULATORY_OVERLAY: ["id", "framework", "version"],
            NodeKind.DATA_RETENTION: ["id", "entity_id", "retention_period"],
            NodeKind.PII_CLASSIFICATION: ["id", "field_id", "pii_type"],
            NodeKind.AUDIT_EVENT: ["id", "event_type", "entity_id"],
            NodeKind.CORRELATION_STRATEGY: ["id", "strategy"],

            # =========================================================================
            # P0: Integration Contracts
            # =========================================================================
            NodeKind.API_CONTRACT: ["id", "protocol", "version"],
            NodeKind.EVENT_SCHEMA: ["id", "version", "type"],
            NodeKind.DATA_MAPPER: ["id", "source_schema", "target_schema"],

            # =========================================================================
            # P1: Workflow Enhancement
            # =========================================================================
            NodeKind.WORKFLOW_GATEWAY: ["id", "type"],
            NodeKind.WORKFLOW_TIMER: ["id", "action"],
            NodeKind.WORKFLOW_SUBPROCESS: ["id", "workflow_id"],
            NodeKind.WORKFLOW_COMPENSATION: ["id", "trigger"],
            NodeKind.HUMAN_TASK: ["id", "assignee_type"],

            # =========================================================================
            # P1: Event-Driven Architecture
            # =========================================================================
            NodeKind.EVENT_PUBLISHER: ["id", "event_type"],
            NodeKind.EVENT_SUBSCRIBER: ["id", "event_type", "handler_id"],
            NodeKind.EVENT_BUS: ["id", "type"],
            NodeKind.CQRS_PROJECTION: ["id", "source_events", "target_entity"],
            NodeKind.EVENT_SOURCING_STREAM: ["id", "aggregate_id"],

            # =========================================================================
            # P1: Search & Indexing
            # =========================================================================
            NodeKind.SEARCH_INDEX: ["id", "engine", "entity_id"],
            NodeKind.SEARCH_QUERY: ["id", "index_id", "query_type"],
            NodeKind.FULL_TEXT_FIELD: ["id", "entity_id", "field_name"],

            # =========================================================================
            # P2: Pagination & API Versioning
            # =========================================================================
            NodeKind.PAGINATION_SPEC: ["id"],
            NodeKind.API_VERSION: ["id", "version", "api_id"],
            NodeKind.DEPRECATION_NOTICE: ["id", "api_version_id"],

            # =========================================================================
            # P2: E-commerce Domain
            # =========================================================================
            NodeKind.SHOPPING_CART: ["id", "customer_id"],
            NodeKind.PRODUCT_CATALOG: ["id"],
            NodeKind.PAYMENT_GATEWAY: ["id", "provider"],
            NodeKind.ORDER_FULFILLMENT: ["id", "order_id"],

            # =========================================================================
            # P2: Finance Domain
            # =========================================================================
            NodeKind.GENERAL_LEDGER: ["id"],
            NodeKind.FINANCIAL_INSTRUMENT: ["id", "symbol", "type"],
            NodeKind.CURRENCY_EXCHANGE: ["id", "base_currency", "quote_currency"],
            NodeKind.TAX_RULE: ["id", "tax_type", "rate"],

            # =========================================================================
            # P2: Healthcare Domain
            # =========================================================================
            NodeKind.PATIENT_RECORD: ["id", "patient_id"],
            NodeKind.CLINICAL_WORKFLOW: ["id", "workflow_type"],
            NodeKind.MEDICATION: ["id", "drug_name"],

            # =========================================================================
            # P2: Education Domain
            # =========================================================================
            NodeKind.COURSE: ["id", "title"],
            NodeKind.GRADEBOOK: ["id", "course_id"],

            # =========================================================================
            # P2: Trading/Exchange Domain
            # =========================================================================
            NodeKind.ORDER_BOOK: ["id", "instrument_id"],
            NodeKind.TRADING_SESSION: ["id", "session_type"],
            NodeKind.FIX_PROTOCOL: ["id", "version"],

            # =========================================================================
            # P2: Logistics Domain
            # =========================================================================
            NodeKind.WAREHOUSE_ZONE: ["id", "warehouse_id"],
            NodeKind.ROUTE_OPTIMIZATION: ["id", "algorithm"],

            # =========================================================================
            # P2: Advanced - Caching & Performance
            # =========================================================================
            NodeKind.CACHE_STRATEGY: ["id", "cache_type"],
            NodeKind.RATE_LIMITER: ["id", "algorithm"],

            # =========================================================================
            # P2: Advanced - Testing & Quality
            # =========================================================================
            NodeKind.TEST_SUITE: ["id", "test_type"],
            NodeKind.QUALITY_GATE: ["id", "gate_type"],

            # =========================================================================
            # P2: Advanced - Data Management
            # =========================================================================
            NodeKind.DATA_MIGRATION: ["id", "source_schema", "target_schema"],
            NodeKind.BATCH_JOB: ["id", "job_type"],

            # =========================================================================
            # P2: Advanced - Messaging
            # =========================================================================
            NodeKind.MESSAGE_SCHEMA: ["id", "schema_type"],
            NodeKind.DEAD_LETTER_QUEUE: ["id", "source_queue"],

            # =========================================================================
            # P2: Advanced - Security
            # =========================================================================
            NodeKind.ENCRYPTION_KEY: ["id", "algorithm"],
            NodeKind.SECURITY_POLICY: ["id", "policy_type"],

            # =========================================================================
            # P1/P3: Enhanced Rule & Scoring (GAP-P1-01, GAP-P3-02)
            # =========================================================================
            NodeKind.RULE_SCORING: ["id", "scoring_model"],
            NodeKind.RULE_MATCHER: ["id", "matcher_type", "conditions"],

            # =========================================================================
            # P2/P3: Enhanced Integration & Protocol
            # =========================================================================
            NodeKind.DEVICE_INTEGRATION: ["id", "device_type", "protocol"],  # GAP-P2-03, P3-03
            NodeKind.HL7_FHIR_SCHEMA: ["id", "standard", "resource_type"],  # GAP-P2-01
            NodeKind.FIX_MESSAGE_TYPES: ["id", "fix_version"],  # GAP-P2-02
            NodeKind.VIDEO_CONFERENCING: ["id", "provider"],  # GAP-P2-04

            # =========================================================================
            # P3: Advanced Patterns (GAP-P3-04 đến P3-08)
            # =========================================================================
            NodeKind.EXTERNAL_SERVICE: ["id", "service_type", "endpoint"],  # GAP-P3-04
            NodeKind.LOCALIZATION: ["id", "entity_id", "locales"],  # GAP-P3-07
            NodeKind.CIRCUIT_BREAKER: ["id", "target_service"],  # GAP-P3-08
            NodeKind.CALENDAR_SCHEDULE: ["id", "calendar_type"],  # GAP-P1-02
            NodeKind.SUBLEDGER: ["id", "ledger_type"],  # GAP-P3-06

            # =========================================================================
            # CP06: Kong Gateway
            # =========================================================================
            NodeKind.KONG_GATEWAY: ["id", "version"],
            NodeKind.KONG_SERVICE: ["id", "name", "protocol", "host", "port"],
            NodeKind.KONG_ROUTE: ["id", "name", "paths"],
            NodeKind.KONG_UPSTREAM: ["id", "name", "type"],
            NodeKind.KONG_PLUGIN: ["id", "name"],

            # =========================================================================
            # CP06: Consul Service Mesh
            # =========================================================================
            NodeKind.CONSUL_SERVICE_MESH: ["id", "datacenter"],
            NodeKind.CONSUL_SERVICE: ["id", "name", "port"],
            NodeKind.CONSUL_CONNECT: ["id", "service_id"],
            NodeKind.CONSUL_HEALTH_CHECK: ["id", "type"],
        }
        return required_map.get(self.kind, ["id"])

    def get_param(self, key: str, default: Any = None) -> Any:
        """
        Lấy giá trị param với default.

        Args:
            key: Key của param
            default: Giá trị mặc định nếu không tìm thấy

        Returns:
            Giá trị param hoặc default
        """
        return self.params.get(key, default)

    def add_child(self, child: "ProjectionNode") -> None:
        """
        Thêm child node.

        Args:
            child: Node con để thêm
        """
        self.children.append(child)

    def add_dependency(self, dependency_id: str) -> None:
        """
        Thêm dependency cho node khác.

        Args:
            dependency_id: ID của node được phụ thuộc
        """
        if dependency_id not in self.dependencies:
            self.dependencies.append(dependency_id)

    def get_tenant_scope(self) -> Optional[str]:
        """
        Lấy tenant scope cho node này.

        Returns:
            Tenant scope hoặc None
        """
        return self.params.get("tenant_scope")

    def get_category(self) -> Optional[str]:
        """
        Lấy category cho node này.

        Returns:
            Category hoặc None
        """
        return self.params.get("category")

    def get_tags(self) -> list[str]:
        """
        Lấy tags cho node này.

        Returns:
            Danh sách tags (trống nếu không có)
        """
        return self.params.get("tags", [])


# ============================================================================
# Projection Tree
# ============================================================================


@dataclass
class ProjectionTree:
    """
    Projection tree hoàn chỉnh cho DSL composition.

    Chứa tất cả nodes được tổ chức theo kind với metadata.
    Cung cấp indexing cho fast lookups.

    Attributes:
        root: Root node (optional, cho hierarchical projections)
        nodes: Tất cả nodes indexed by ID
        nodes_by_kind: Nodes được group theo kind
        manifest_id: Reference cho manifest mà tree thuộc về
        metadata: Tree-level metadata

    Example:
        tree = ProjectionTree()
        tree.add_node(entity_node)
        tree.add_node(command_node)
        entities = tree.get_entities()
    """

    root: Optional[ProjectionNode] = None
    nodes: dict[str, ProjectionNode] = field(default_factory=dict)
    nodes_by_kind: dict[NodeKind, list[ProjectionNode]] = field(default_factory=dict)
    manifest_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_node(self, node: ProjectionNode) -> None:
        """
        Thêm node vào tree.

        Node được indexed theo ID và kind cho fast lookups.

        Args:
            node: Node để thêm
        """
        self.nodes[node.id] = node

        # Index theo kind
        if node.kind not in self.nodes_by_kind:
            self.nodes_by_kind[node.kind] = []
        self.nodes_by_kind[node.kind].append(node)

    def get_node(self, node_id: str) -> Optional[ProjectionNode]:
        """
        Lấy node theo ID.

        Args:
            node_id: ID của node để tìm

        Returns:
            Node hoặc None nếu không tìm thấy
        """
        return self.nodes.get(node_id)

    def get_nodes_by_kind(self, kind: NodeKind) -> list[ProjectionNode]:
        """
        Lấy tất cả nodes của một kind cụ thể.

        Args:
            kind: Node kind để filter

        Returns:
            Danh sách nodes
        """
        return self.nodes_by_kind.get(kind, [])

    def get_entities(self) -> list[ProjectionNode]:
        """Lấy tất cả entity nodes."""
        return self.get_nodes_by_kind(NodeKind.ENTITY)

    def get_commands(self) -> list[ProjectionNode]:
        """Lấy tất cả command nodes."""
        return self.get_nodes_by_kind(NodeKind.COMMAND)

    def get_queries(self) -> list[ProjectionNode]:
        """Lấy tất cả query nodes."""
        return self.get_nodes_by_kind(NodeKind.QUERY)

    def get_workflows(self) -> list[ProjectionNode]:
        """Lấy tất cả workflow nodes."""
        return self.get_nodes_by_kind(NodeKind.WORKFLOW)

    def get_http_routes(self) -> list[ProjectionNode]:
        """Lấy tất cả HTTP route nodes."""
        return self.get_nodes_by_kind(NodeKind.HTTP_ROUTE)

    # --- Infrastructure getters ---

    def get_datasources(self) -> list[ProjectionNode]:
        """Lấy tất cả datasource nodes."""
        return self.get_nodes_by_kind(NodeKind.DATASOURCE)

    def get_tables(self) -> list[ProjectionNode]:
        """Lấy tất cả table nodes."""
        return self.get_nodes_by_kind(NodeKind.TABLE)

    def get_indexes(self) -> list[ProjectionNode]:
        """Lấy tất cả index nodes."""
        return self.get_nodes_by_kind(NodeKind.INDEX)

    def get_value_objects(self) -> list[ProjectionNode]:
        """Lấy tất cả value object nodes."""
        return self.get_nodes_by_kind(NodeKind.VALUE_OBJECT)

    def get_enums(self) -> list[ProjectionNode]:
        """Lấy tất cả enum nodes."""
        return self.get_nodes_by_kind(NodeKind.ENUM)

    def get_errors(self) -> list[ProjectionNode]:
        """Lấy tất cả error nodes."""
        return self.get_nodes_by_kind(NodeKind.ERROR)

    def get_events(self) -> list[ProjectionNode]:
        """Lấy tất cả event nodes."""
        return self.get_nodes_by_kind(NodeKind.EVENT)

    def get_rules(self) -> list[ProjectionNode]:
        """Lấy tất cả rule nodes."""
        return self.get_nodes_by_kind(NodeKind.RULE)

    def get_guards(self) -> list[ProjectionNode]:
        """Lấy tất cả guard nodes."""
        return self.get_nodes_by_kind(NodeKind.GUARD)

    def get_effects(self) -> list[ProjectionNode]:
        """Lấy tất cả effect nodes."""
        return self.get_nodes_by_kind(NodeKind.EFFECT)

    # =========================================================================
    # P0: Reporting Getters
    # =========================================================================

    def get_reports(self) -> list[ProjectionNode]:
        """Lấy tất cả report nodes."""
        return self.get_nodes_by_kind(NodeKind.REPORT)

    def get_dashboards(self) -> list[ProjectionNode]:
        """Lấy tất cả dashboard nodes."""
        return self.get_nodes_by_kind(NodeKind.DASHBOARD)

    def get_exports(self) -> list[ProjectionNode]:
        """Lấy tất cả export nodes."""
        return self.get_nodes_by_kind(NodeKind.EXPORT)

    def get_scheduled_reports(self) -> list[ProjectionNode]:
        """Lấy tất cả scheduled report nodes."""
        return self.get_nodes_by_kind(NodeKind.SCHEDULED_REPORT)

    # =========================================================================
    # P0: Notification Getters
    # =========================================================================

    def get_notification_channels(self) -> list[ProjectionNode]:
        """Lấy tất cả notification channel nodes."""
        return self.get_nodes_by_kind(NodeKind.NOTIFICATION_CHANNEL)

    def get_notification_templates(self) -> list[ProjectionNode]:
        """Lấy tất cả notification template nodes."""
        return self.get_nodes_by_kind(NodeKind.NOTIFICATION_TEMPLATE)

    def get_notification_rules(self) -> list[ProjectionNode]:
        """Lấy tất cả notification rule nodes."""
        return self.get_nodes_by_kind(NodeKind.NOTIFICATION_RULE)

    def get_message_queues(self) -> list[ProjectionNode]:
        """Lấy tất cả message queue nodes."""
        return self.get_nodes_by_kind(NodeKind.MESSAGE_QUEUE)

    # =========================================================================
    # P0: Compliance Getters
    # =========================================================================

    def get_compliance_rules(self) -> list[ProjectionNode]:
        """Lấy tất cả compliance rule nodes."""
        return self.get_nodes_by_kind(NodeKind.COMPLIANCE_RULE)

    def get_regulatory_overlays(self) -> list[ProjectionNode]:
        """Lấy tất cả regulatory overlay nodes."""
        return self.get_nodes_by_kind(NodeKind.REGULATORY_OVERLAY)

    def get_data_retentions(self) -> list[ProjectionNode]:
        """Lấy tất cả data retention nodes."""
        return self.get_nodes_by_kind(NodeKind.DATA_RETENTION)

    def get_pii_classifications(self) -> list[ProjectionNode]:
        """Lấy tất cả PII classification nodes."""
        return self.get_nodes_by_kind(NodeKind.PII_CLASSIFICATION)

    def get_audit_events(self) -> list[ProjectionNode]:
        """Lấy tất cả audit event nodes."""
        return self.get_nodes_by_kind(NodeKind.AUDIT_EVENT)

    def get_correlation_strategies(self) -> list[ProjectionNode]:
        """Lấy tất cả correlation strategy nodes."""
        return self.get_nodes_by_kind(NodeKind.CORRELATION_STRATEGY)

    # =========================================================================
    # P0: Integration Contract Getters
    # =========================================================================

    def get_api_contracts(self) -> list[ProjectionNode]:
        """Lấy tất cả API contract nodes."""
        return self.get_nodes_by_kind(NodeKind.API_CONTRACT)

    def get_event_schemas(self) -> list[ProjectionNode]:
        """Lấy tất cả event schema nodes."""
        return self.get_nodes_by_kind(NodeKind.EVENT_SCHEMA)

    def get_data_mappers(self) -> list[ProjectionNode]:
        """Lấy tất cả data mapper nodes."""
        return self.get_nodes_by_kind(NodeKind.DATA_MAPPER)

    # =========================================================================
    # P1: Workflow Enhancement Getters
    # =========================================================================

    def get_workflow_gateways(self) -> list[ProjectionNode]:
        """Lấy tất cả workflow gateway nodes."""
        return self.get_nodes_by_kind(NodeKind.WORKFLOW_GATEWAY)

    def get_workflow_timers(self) -> list[ProjectionNode]:
        """Lấy tất cả workflow timer nodes."""
        return self.get_nodes_by_kind(NodeKind.WORKFLOW_TIMER)

    def get_workflow_subprocesses(self) -> list[ProjectionNode]:
        """Lấy tất cả workflow subprocess nodes."""
        return self.get_nodes_by_kind(NodeKind.WORKFLOW_SUBPROCESS)

    def get_workflow_compensations(self) -> list[ProjectionNode]:
        """Lấy tất cả workflow compensation nodes."""
        return self.get_nodes_by_kind(NodeKind.WORKFLOW_COMPENSATION)

    def get_human_tasks(self) -> list[ProjectionNode]:
        """Lấy tất cả human task nodes."""
        return self.get_nodes_by_kind(NodeKind.HUMAN_TASK)

    # =========================================================================
    # P1: Event-Driven Getters
    # =========================================================================

    def get_event_publishers(self) -> list[ProjectionNode]:
        """Lấy tất cả event publisher nodes."""
        return self.get_nodes_by_kind(NodeKind.EVENT_PUBLISHER)

    def get_event_subscribers(self) -> list[ProjectionNode]:
        """Lấy tất cả event subscriber nodes."""
        return self.get_nodes_by_kind(NodeKind.EVENT_SUBSCRIBER)

    def get_event_buses(self) -> list[ProjectionNode]:
        """Lấy tất cả event bus nodes."""
        return self.get_nodes_by_kind(NodeKind.EVENT_BUS)

    def get_cqrs_projections(self) -> list[ProjectionNode]:
        """Lấy tất cả CQRS projection nodes."""
        return self.get_nodes_by_kind(NodeKind.CQRS_PROJECTION)

    def get_event_sourcing_streams(self) -> list[ProjectionNode]:
        """Lấy tất cả event sourcing stream nodes."""
        return self.get_nodes_by_kind(NodeKind.EVENT_SOURCING_STREAM)

    # =========================================================================
    # P1: Search Getters
    # =========================================================================

    def get_search_indexes(self) -> list[ProjectionNode]:
        """Lấy tất cả search index nodes."""
        return self.get_nodes_by_kind(NodeKind.SEARCH_INDEX)

    def get_search_queries(self) -> list[ProjectionNode]:
        """Lấy tất cả search query nodes."""
        return self.get_nodes_by_kind(NodeKind.SEARCH_QUERY)

    def get_full_text_fields(self) -> list[ProjectionNode]:
        """Lấy tất cả full text field nodes."""
        return self.get_nodes_by_kind(NodeKind.FULL_TEXT_FIELD)

    # =========================================================================
    # P2: Pagination & Versioning Getters
    # =========================================================================

    def get_pagination_specs(self) -> list[ProjectionNode]:
        """Lấy tất cả pagination spec nodes."""
        return self.get_nodes_by_kind(NodeKind.PAGINATION_SPEC)

    def get_api_versions(self) -> list[ProjectionNode]:
        """Lấy tất cả API version nodes."""
        return self.get_nodes_by_kind(NodeKind.API_VERSION)

    def get_deprecation_notices(self) -> list[ProjectionNode]:
        """Lấy tất cả deprecation notice nodes."""
        return self.get_nodes_by_kind(NodeKind.DEPRECATION_NOTICE)

    # =========================================================================
    # P2: E-commerce Domain Getters
    # =========================================================================

    def get_shopping_carts(self) -> list[ProjectionNode]:
        """Lấy tất cả shopping cart nodes."""
        return self.get_nodes_by_kind(NodeKind.SHOPPING_CART)

    def get_product_catalogs(self) -> list[ProjectionNode]:
        """Lấy tất cả product catalog nodes."""
        return self.get_nodes_by_kind(NodeKind.PRODUCT_CATALOG)

    def get_payment_gateways(self) -> list[ProjectionNode]:
        """Lấy tất cả payment gateway nodes."""
        return self.get_nodes_by_kind(NodeKind.PAYMENT_GATEWAY)

    def get_order_fulfillments(self) -> list[ProjectionNode]:
        """Lấy tất cả order fulfillment nodes."""
        return self.get_nodes_by_kind(NodeKind.ORDER_FULFILLMENT)

    # =========================================================================
    # P2: Finance Domain Getters
    # =========================================================================

    def get_general_ledgers(self) -> list[ProjectionNode]:
        """Lấy tất cả general ledger nodes."""
        return self.get_nodes_by_kind(NodeKind.GENERAL_LEDGER)

    def get_financial_instruments(self) -> list[ProjectionNode]:
        """Lấy tất cả financial instrument nodes."""
        return self.get_nodes_by_kind(NodeKind.FINANCIAL_INSTRUMENT)

    def get_currency_exchanges(self) -> list[ProjectionNode]:
        """Lấy tất cả currency exchange nodes."""
        return self.get_nodes_by_kind(NodeKind.CURRENCY_EXCHANGE)

    def get_tax_rules(self) -> list[ProjectionNode]:
        """Lấy tất cả tax rule nodes."""
        return self.get_nodes_by_kind(NodeKind.TAX_RULE)

    # =========================================================================
    # P2: Healthcare Domain Getters
    # =========================================================================

    def get_patient_records(self) -> list[ProjectionNode]:
        """Lấy tất cả patient record nodes."""
        return self.get_nodes_by_kind(NodeKind.PATIENT_RECORD)

    def get_clinical_workflows(self) -> list[ProjectionNode]:
        """Lấy tất cả clinical workflow nodes."""
        return self.get_nodes_by_kind(NodeKind.CLINICAL_WORKFLOW)

    def get_medications(self) -> list[ProjectionNode]:
        """Lấy tất cả medication nodes."""
        return self.get_nodes_by_kind(NodeKind.MEDICATION)

    # =========================================================================
    # P2: Education Domain Getters
    # =========================================================================

    def get_courses(self) -> list[ProjectionNode]:
        """Lấy tất cả course nodes."""
        return self.get_nodes_by_kind(NodeKind.COURSE)

    def get_gradebooks(self) -> list[ProjectionNode]:
        """Lấy tất cả gradebook nodes."""
        return self.get_nodes_by_kind(NodeKind.GRADEBOOK)

    # =========================================================================
    # P2: Trading/Exchange Domain Getters
    # =========================================================================

    def get_order_books(self) -> list[ProjectionNode]:
        """Lấy tất cả order book nodes."""
        return self.get_nodes_by_kind(NodeKind.ORDER_BOOK)

    def get_trading_sessions(self) -> list[ProjectionNode]:
        """Lấy tất cả trading session nodes."""
        return self.get_nodes_by_kind(NodeKind.TRADING_SESSION)

    def get_fix_protocols(self) -> list[ProjectionNode]:
        """Lấy tất cả FIX protocol nodes."""
        return self.get_nodes_by_kind(NodeKind.FIX_PROTOCOL)

    # =========================================================================
    # P2: Logistics Domain Getters
    # =========================================================================

    def get_warehouse_zones(self) -> list[ProjectionNode]:
        """Lấy tất cả warehouse zone nodes."""
        return self.get_nodes_by_kind(NodeKind.WAREHOUSE_ZONE)

    def get_route_optimizations(self) -> list[ProjectionNode]:
        """Lấy tất cả route optimization nodes."""
        return self.get_nodes_by_kind(NodeKind.ROUTE_OPTIMIZATION)

    # =========================================================================
    # P2: Advanced - Caching & Performance Getters
    # =========================================================================

    def get_cache_strategies(self) -> list[ProjectionNode]:
        """Lấy tất cả cache strategy nodes."""
        return self.get_nodes_by_kind(NodeKind.CACHE_STRATEGY)

    def get_rate_limiters(self) -> list[ProjectionNode]:
        """Lấy tất cả rate limiter nodes."""
        return self.get_nodes_by_kind(NodeKind.RATE_LIMITER)

    # =========================================================================
    # P2: Advanced - Testing & Quality Getters
    # =========================================================================

    def get_test_suites(self) -> list[ProjectionNode]:
        """Lấy tất cả test suite nodes."""
        return self.get_nodes_by_kind(NodeKind.TEST_SUITE)

    def get_quality_gates(self) -> list[ProjectionNode]:
        """Lấy tất cả quality gate nodes."""
        return self.get_nodes_by_kind(NodeKind.QUALITY_GATE)

    # =========================================================================
    # P2: Advanced - Data Management Getters
    # =========================================================================

    def get_data_migrations(self) -> list[ProjectionNode]:
        """Lấy tất cả data migration nodes."""
        return self.get_nodes_by_kind(NodeKind.DATA_MIGRATION)

    def get_batch_jobs(self) -> list[ProjectionNode]:
        """Lấy tất cả batch job nodes."""
        return self.get_nodes_by_kind(NodeKind.BATCH_JOB)

    # =========================================================================
    # P2: Advanced - Messaging Getters
    # =========================================================================

    def get_message_schemas(self) -> list[ProjectionNode]:
        """Lấy tất cả message schema nodes."""
        return self.get_nodes_by_kind(NodeKind.MESSAGE_SCHEMA)

    def get_dead_letter_queues(self) -> list[ProjectionNode]:
        """Lấy tất cả dead letter queue nodes."""
        return self.get_nodes_by_kind(NodeKind.DEAD_LETTER_QUEUE)

    # =========================================================================
    # P2: Advanced - Security Getters
    # =========================================================================

    def get_encryption_keys(self) -> list[ProjectionNode]:
        """Lấy tất cả encryption key nodes."""
        return self.get_nodes_by_kind(NodeKind.ENCRYPTION_KEY)

    def get_security_policies(self) -> list[ProjectionNode]:
        """Lấy tất cả security policy nodes."""
        return self.get_nodes_by_kind(NodeKind.SECURITY_POLICY)

    def node_count(self) -> int:
        """
        Lấy tổng số nodes.

        Returns:
            Số lượng nodes
        """
        return len(self.nodes)

    def kind_count(self, kind: NodeKind) -> int:
        """
        Lấy số nodes cho một kind cụ thể.

        Args:
            kind: Node kind

        Returns:
            Số lượng nodes
        """
        return len(self.get_nodes_by_kind(kind))

    def all_kinds(self) -> list[NodeKind]:
        """
        Lấy tất cả node kinds có trong tree.

        Returns:
            Danh sách NodeKind
        """
        return list(self.nodes_by_kind.keys())


# ============================================================================
# Protocol cho Node Builders
# ============================================================================


class NodeBuilder(Protocol):
    """
    Protocol cho node builders (factory pattern).

    Dùng để create ProjectionNode instances một cách type-safe.
    """

    def build(self) -> ProjectionNode:
        """
        Build một projection node.

        Returns:
            ProjectionNode đã build
        """
        ...


# ============================================================================
# T03-001: Lazy Loading Implementation - Performance Optimization
# ============================================================================


@dataclass
class LazyNodeLoader:
    """
    Lazy loader cho nodes.

    Chỉ load node khi được truy cập, không phải upfront.
    Giúp giảm memory usage và startup time cho large DSLs.

    Attributes:
        loader_func: Function để load node
        node_id: ID của node sẽ load
        kind: Node kind
        loaded: Đã load chưa
        _node: Cached node sau khi load
    """

    loader_func: Callable[[], ProjectionNode]
    node_id: str
    kind: NodeKind
    loaded: bool = False
    _node: Optional[ProjectionNode] = None

    def get_node(self) -> ProjectionNode:
        """
        Lấy node, load nếu chưa load.

        Returns:
            ProjectionNode (load nếu cần)
        """
        if not self.loaded:
            self._node = self.loader_func()
            self.loaded = True
        return self._node

    def is_loaded(self) -> bool:
        """Check if node đã được load."""
        return self.loaded


@dataclass
class LazyProjectionTree:
    """
    Projection tree với lazy loading support.

    Extensions của ProjectionTree để support lazy loading:
    - Nodes được load on-demand thay vì upfront
    - Caching results để tránh re-loading
    - Statistics tracking cho performance monitoring

    Usage:
        tree = LazyProjectionTree()
        tree.add_lazy_node("Order", NodeKind.ENTITY, load_order_entity)
        order = tree.get_node("Order")  # Load chỉ khi gọi
        order2 = tree.get_node("Order")  # Return cached result

    Attributes:
        nodes: Regular nodes (eager loading)
        lazy_nodes: Lazy-loaded nodes
        loaders: Mapping từ node_id → LazyNodeLoader
        _load_count: Số lần load
        _cache_hits: Số lần hit cache
    """

    nodes: dict[str, ProjectionNode] = field(default_factory=dict)
    lazy_nodes: dict[str, LazyNodeLoader] = field(default_factory=dict)
    nodes_by_kind: dict[NodeKind, list[ProjectionNode]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    _load_count: int = field(default=0, repr=False)
    _cache_hits: int = field(default=0, repr=False)

    def add_lazy_node(
        self,
        node_id: str,
        kind: NodeKind,
        loader_func: Callable[[], ProjectionNode]
    ) -> None:
        """
        Thêm lazy node vào tree.

        Node sẽ không được load cho đến khi get_node() được gọi.

        Args:
            node_id: ID của node
            kind: Node kind
            loader_func: Function để load node khi cần
        """
        self.lazy_nodes[node_id] = LazyNodeLoader(
            loader_func=loader_func,
            node_id=node_id,
            kind=kind,
        )

    def add_node(self, node: ProjectionNode) -> None:
        """
        Thêm eager node vào tree (regular behavior).

        Args:
            node: Node để thêm
        """
        self.nodes[node.id] = node
        if node.kind not in self.nodes_by_kind:
            self.nodes_by_kind[node.kind] = []
        self.nodes_by_kind[node.kind].append(node)

    def get_node(self, node_id: str) -> Optional[ProjectionNode]:
        """
        Lấy node, tự động load nếu là lazy node.

        Args:
            node_id: ID của node

        Returns:
            Node hoặc None
        """
        # Check eager nodes first
        if node_id in self.nodes:
            return self.nodes[node_id]

        # Check lazy nodes
        if node_id in self.lazy_nodes:
            loader = self.lazy_nodes[node_id]
            node = loader.get_node()

            # Move from lazy to eager after first load
            del self.lazy_nodes[node_id]
            self.nodes[node_id] = node

            # Index by kind
            if node.kind not in self.nodes_by_kind:
                self.nodes_by_kind[node.kind] = []
            self.nodes_by_kind[node.kind].append(node)

            self._load_count += 1
            return node

        return None

    def ensure_loaded(self, node_id: str) -> bool:
        """
        Đảm bảo node được load (nếu là lazy node).

        Args:
            node_id: ID của node

        Returns:
            True nếu node tồn tại và đã được load
        """
        if node_id in self.nodes:
            self._cache_hits += 1
            return True

        if node_id in self.lazy_nodes:
            loader = self.lazy_nodes[node_id]
            if loader.loaded:
                self._cache_hits += 1
                return True

        return False

    def load_all(self) -> None:
        """
        Force load tất cả lazy nodes.

        Convert tree từ lazy sang eager mode.
        """
        for node_id in list(self.lazy_nodes.keys()):
            self.get_node(node_id)

    def get_nodes_by_kind(self, kind: NodeKind) -> list[ProjectionNode]:
        """
        Lấy tất cả nodes của một kind, bao gồm lazy nodes.

        Lazy nodes sẽ được load nếu cần.

        Args:
            kind: Node kind

        Returns:
            Danh sách nodes
        """
        result = list(self.nodes_by_kind.get(kind, []))

        # Check lazy nodes
        for loader in self.lazy_nodes.values():
            if loader.kind == kind:
                node = loader.get_node()
                result.append(node)

        return result

    def node_count(self) -> int:
        """
        Lấy tổng số nodes (eager + lazy).

        Returns:
            Tổng số nodes
        """
        return len(self.nodes) + len(self.lazy_nodes)

    def lazy_count(self) -> int:
        """
        Lấy số lazy nodes chưa load.

        Returns:
            Số lazy nodes
        """
        return len(self.lazy_nodes)

    def eager_count(self) -> int:
        """
        Lấy số nodes đã load.

        Returns:
            Số eager nodes
        """
        return len(self.nodes)

    def get_stats(self) -> dict[str, Any]:
        """
        Lấy performance statistics.

        Returns:
            Stats dictionary với load counts, cache hits, etc.
        """
        return {
            "total_nodes": self.node_count(),
            "eager_nodes": self.eager_count(),
            "lazy_nodes": self.lazy_count(),
            "load_count": self._load_count,
            "cache_hits": self._cache_hits,
            "cache_hit_rate": (
                self._cache_hits / (self._load_count + self._cache_hits)
                if (self._load_count + self._cache_hits) > 0 else 0.0
            ),
            "kinds": list(set(
                [kind for loader in self.lazy_nodes.values() for kind in [loader.kind]]
                + list(self.nodes_by_kind.keys())
            )),
        }

    def to_dict(self) -> dict[str, Any]:
        """
        Convert tree to dictionary representation.

        Returns:
            Dictionary với nodes và metadata
        """
        return {
            "nodes": {
                node_id: {
                    "id": node.id,
                    "kind": node.kind.value,
                    "params": node.params,
                }
                for node_id, node in self.nodes.items()
            },
            "lazy_nodes": list(self.lazy_nodes.keys()),
            "metadata": self.metadata,
            "stats": self.get_stats(),
        }
