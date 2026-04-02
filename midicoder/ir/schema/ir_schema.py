"""IR (Intermediate Representation) schema for compiled contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SourceMetadata:
    """Metadata about the source file."""

    file: str  # Relative path to source file
    checksum: str = ""  # File checksum (SHA256)
    line_start: int | None = None  # Starting line number (1-indexed)
    line_end: int | None = None  # Ending line number (1-indexed)
    source_order: int | None = None  # Original order in source file

    # Deprecated: kept for backward compatibility
    line: int | None = None  # Use line_start instead

    def __post_init__(self):
        """Ensure line_start is set from line if needed."""
        if self.line is not None and self.line_start is None:
            self.line_start = self.line


@dataclass
class RefIR:
    """Normalized reference to another object."""

    type: str  # Symbol type (Entity, Command, etc.)
    id: str  # Canonical ID


@dataclass
class IntentIR:
    """Intent metadata for an IR node."""

    kind: str
    module: str
    confidence: float
    source: str
    alternatives: list[dict[str, Any]] | None = None


@dataclass
class FieldIR:
    """Field definition in IR."""

    name: str
    type: str
    required: bool = True
    description: str | None = None
    default: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)
    source_ref: str | None = None
    introduced_in: str | None = None
    deprecated_in: str | None = None
    replaced_by: str | None = None
    status: str | None = None


@dataclass
class IndexIR:
    """Index definition in IR."""

    name: str
    fields: list[str]
    unique: bool = False


@dataclass
class ConstraintIR:
    """Constraint definition in IR."""

    type: str
    fields: list[str]
    ref: str | None = None


@dataclass
class GuardIR:
    """Guard definition in IR."""

    id: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class EffectIR:
    """Effect definition in IR."""

    id: str
    params: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Domain IR
# ============================================================================


@dataclass
class EntityIR:
    """Entity in IR."""

    id: str
    description: str | None
    fields: list[FieldIR]
    primary_key: str | None
    indexes: list[IndexIR]
    constraints: list[ConstraintIR]
    tags: list[str]
    tenant_scope: str | None
    source_ref: str | None
    source: SourceMetadata
    hash: str
    intent: IntentIR | None = None


@dataclass
class ValueObjectIR:
    """Value object in IR."""

    id: str
    description: str | None
    fields: list[FieldIR]
    tags: list[str]
    category: str | None
    source_ref: str | None
    source: SourceMetadata
    hash: str
    intent: IntentIR | None = None


@dataclass
class EnumIR:
    """Enum in IR."""

    id: str
    description: str | None
    values: list[str]
    value_labels: dict[str, str]
    tags: list[str]
    source_ref: str | None
    source: SourceMetadata
    hash: str
    intent: IntentIR | None = None


@dataclass
class ErrorIR:
    """Error in IR."""

    id: str
    description: str | None
    fields: list[FieldIR]
    category: str | None
    http_status: int | None
    code: str | None
    tags: list[str]
    source_ref: str | None
    source: SourceMetadata
    hash: str


@dataclass
class EventIR:
    """Event in IR."""

    id: str
    description: str | None
    fields: list[FieldIR]
    kind: str | None
    tags: list[str]
    source_ref: str | None
    source: SourceMetadata
    hash: str
    intent: IntentIR | None = None


@dataclass
class DomainIR:
    """Domain module IR."""

    entities: list[EntityIR] = field(default_factory=list)
    value_objects: list[ValueObjectIR] = field(default_factory=list)
    enums: list[EnumIR] = field(default_factory=list)
    errors: list[ErrorIR] = field(default_factory=list)
    events: list[EventIR] = field(default_factory=list)


# ============================================================================
# Application IR
# ============================================================================


@dataclass
class CommandIR:
    """Command in IR."""

    id: str
    description: str | None
    input: list[FieldIR]
    returns: list[FieldIR]
    fetches: list[RefIR]
    guards: list[GuardIR]
    effects: list[EffectIR]
    errors: list[RefIR]
    emits: list[RefIR]
    category: str | None
    required_roles: list[str]
    required_permissions: list[str]
    writes_to: list[str]
    datasource: str | None
    transaction: bool | None
    tenant_scope: str | None
    tags: list[str]
    source_ref: str | None
    source: SourceMetadata
    hash: str
    intent: IntentIR | None = None


@dataclass
class QueryIR:
    """Query in IR."""

    id: str
    description: str | None
    input: list[FieldIR]
    returns: list[FieldIR]
    reads: list[RefIR]
    filters: dict[str, Any] | None
    pagination: dict[str, Any] | None
    category: str | None
    required_roles: list[str]
    required_permissions: list[str]
    reads_from: list[str]
    datasource: str | None
    tags: list[str]
    source_ref: str | None
    source: SourceMetadata
    hash: str
    intent: IntentIR | None = None


@dataclass
class ProjectionIR:
    """Projection in IR."""

    id: str
    description: str | None
    source_events: list[RefIR]
    fields: list[FieldIR]
    storage: str | None
    storage_kind: str | None
    storage_ref: str | None
    tags: list[str]
    source_ref: str | None
    source: SourceMetadata
    hash: str
    intent: IntentIR | None = None


@dataclass
class ApplicationIR:
    """Application module IR."""

    commands: list[CommandIR] = field(default_factory=list)
    queries: list[QueryIR] = field(default_factory=list)
    projections: list[ProjectionIR] = field(default_factory=list)


# ============================================================================
# Workflow IR
# ============================================================================


@dataclass
class StateIR:
    """Workflow state in IR."""

    id: str
    description: str | None
    kind: str | None


@dataclass
class TransitionIR:
    """Workflow transition in IR."""

    from_state: str
    to_state: str
    on_command: RefIR | None
    on_event: RefIR | None
    guards: list[GuardIR]
    effects: list[EffectIR]
    description: str | None


@dataclass
class ErrorHandlerIR:
    """Workflow error handler in IR."""

    error: RefIR
    action: str
    transition_to: str | None


@dataclass
class WorkflowIR:
    """Workflow in IR."""

    id: str
    description: str | None
    entity: RefIR
    states: list[StateIR]
    transitions: list[TransitionIR]
    initial_state: str
    error_handlers: list[ErrorHandlerIR]
    required_roles: list[str]
    required_permissions: list[str]
    scenarios: list[str]
    tags: list[str]
    source_ref: str | None
    source: SourceMetadata
    hash: str
    intent: IntentIR | None = None


@dataclass
class WorkflowModuleIR:
    """Workflow module IR."""

    workflows: list[WorkflowIR] = field(default_factory=list)


# ============================================================================
# API IR
# ============================================================================


@dataclass
class HttpRouteIR:
    """HTTP route in IR."""

    id: str  # Generated from method:path
    method: str
    path: str
    command: RefIR | None
    query: RefIR | None
    description: str | None
    auth: str | None
    request_schema: list[FieldIR] | None
    response_schema: list[FieldIR] | None
    deprecated: bool
    tags: list[str]
    source_ref: str | None
    source: SourceMetadata
    hash: str


@dataclass
class GraphQLFieldIR:
    """GraphQL field in IR."""

    name: str
    type: str
    args: list[FieldIR]
    description: str | None


@dataclass
class GraphQLTypeIR:
    """GraphQL type in IR."""

    id: str  # Same as name, for consistency
    name: str
    kind: str
    fields: list[GraphQLFieldIR]
    description: str | None
    tags: list[str]
    source_ref: str | None
    source: SourceMetadata
    hash: str


@dataclass
class GraphQLOperationIR:
    """GraphQL query or mutation in IR."""

    id: str  # Same as name, for consistency
    name: str
    type: str  # "query" or "mutation"
    args: list[FieldIR]
    returns: list[FieldIR]
    returns_type: str | None
    command: RefIR | None
    query: RefIR | None
    description: str | None
    tags: list[str]
    source_ref: str | None
    source: SourceMetadata
    hash: str


@dataclass
class HttpApiIR:
    """HTTP API IR."""

    routes: list[HttpRouteIR] = field(default_factory=list)


@dataclass
class GraphQLApiIR:
    """GraphQL API IR."""

    types: list[GraphQLTypeIR] = field(default_factory=list)
    queries: list[GraphQLOperationIR] = field(default_factory=list)
    mutations: list[GraphQLOperationIR] = field(default_factory=list)


@dataclass
class ApiIR:
    """API module IR."""

    http: HttpApiIR | None = None
    graphql: GraphQLApiIR | None = None


# ============================================================================
# Persistence IR
# ============================================================================


@dataclass
class PersistenceDatasourceIR:
    id: str
    engine: str
    connector: str | None
    database: str | None
    host: str | None
    port: int | None
    db_schema: str | None
    default: bool
    options: dict[str, Any]
    integration: RefIR | None
    source: SourceMetadata
    hash: str


@dataclass
class PersistenceColumnIR:
    name: str
    type: str
    required: bool
    description: str | None
    constraints: dict[str, Any]


@dataclass
class PersistenceIndexIR:
    name: str
    columns: list[str]
    unique: bool


@dataclass
class PersistenceTableIR:
    id: str
    description: str | None
    datasource: str | None
    operation: RefIR | None
    columns: list[PersistenceColumnIR]
    indexes: list[PersistenceIndexIR]
    tags: list[str]
    source: SourceMetadata
    hash: str


@dataclass
class PersistenceIR:
    datasources: list[PersistenceDatasourceIR] = field(default_factory=list)
    tables: list[PersistenceTableIR] = field(default_factory=list)


# ============================================================================
# Integration IR
# ============================================================================


@dataclass
class IntegrationAuthIR:
    type: str
    secret_ref: str | None
    key_name: str | None
    token_prefix: str | None
    options: dict[str, Any]


@dataclass
class TimeoutPolicyIR:
    connect_ms: int | None
    read_ms: int | None
    total_ms: int | None


@dataclass
class RetryPolicyIR:
    max_attempts: int
    backoff_ms: int
    max_backoff_ms: int | None
    jitter: bool


@dataclass
class RateLimitPolicyIR:
    requests: int
    per_seconds: int


@dataclass
class CircuitBreakerPolicyIR:
    failure_threshold: int
    recovery_timeout_seconds: int


@dataclass
class IntegrationTargetIR:
    id: str
    type: str
    provider: str | None
    service: str | None
    base_url: str | None
    auth: IntegrationAuthIR | None
    timeouts: TimeoutPolicyIR | None
    retry: RetryPolicyIR | None
    rate_limit: RateLimitPolicyIR | None
    circuit_breaker: CircuitBreakerPolicyIR | None
    headers: dict[str, str]
    tags: list[str]
    source: SourceMetadata
    hash: str


@dataclass
class ErrorMapIR:
    source_code: str
    target_error: RefIR


@dataclass
class RestApiOperationIR:
    id: str
    integration_id: RefIR
    method: str
    path: str
    request_schema: list[FieldIR]
    response_schema: list[FieldIR]
    error_mapping: list[ErrorMapIR]
    source: SourceMetadata
    hash: str


@dataclass
class S3ResourceIR:
    integration_id: RefIR
    bucket: str
    region: str
    operations: list[str]
    path_template: str | None
    encryption: str | None
    source: SourceMetadata
    hash: str


@dataclass
class EmailProviderIR:
    id: str
    transport: str
    host: str | None
    port: int | None
    username_secret: str | None
    password_secret: str | None
    from_email: str
    from_name: str | None
    source: SourceMetadata
    hash: str


@dataclass
class OAuth2ProviderIR:
    id: str
    issuer: str
    audience: str | None
    jwks_url: str | None
    introspection_url: str | None
    client_id_secret: str | None
    client_secret_secret: str | None
    scopes: list[str]
    source: SourceMetadata
    hash: str


@dataclass
class SignaturePolicyIR:
    alg: str
    secret_ref: str
    header_name: str | None


@dataclass
class WebhookEndpointIR:
    id: str
    direction: str
    url_or_path: str
    method: str
    signature: SignaturePolicyIR | None
    retries: RetryPolicyIR | None
    events: list[str]
    source: SourceMetadata
    hash: str


@dataclass
class IntegrationsIR:
    integrations: list[IntegrationTargetIR] = field(default_factory=list)
    operations: list[RestApiOperationIR] = field(default_factory=list)
    s3_resources: list[S3ResourceIR] = field(default_factory=list)
    oauth2_providers: list[OAuth2ProviderIR] = field(default_factory=list)
    webhooks: list[WebhookEndpointIR] = field(default_factory=list)
    email_providers: list[EmailProviderIR] = field(default_factory=list)


# ============================================================================
# Ops IR
# ============================================================================


@dataclass
class EnvironmentProfileIR:
    name: str
    overrides: dict[str, Any]
    tags: list[str]
    source: SourceMetadata
    hash: str


@dataclass
class SecretRefIR:
    id: str
    provider: str
    key: str
    description: str | None
    required: bool
    tags: list[str]
    source: SourceMetadata
    hash: str


@dataclass
class CorsPolicyIR:
    allowed_origins: list[str]
    allowed_methods: list[str]
    allowed_headers: list[str]
    allow_credentials: bool


@dataclass
class RateLimitRuleIR:
    id: str
    requests: int
    per_seconds: int
    scope: str


@dataclass
class PiiMaskingRuleIR:
    field: str
    strategy: str


@dataclass
class SecurityBaselineIR:
    auth_required: bool
    authz_required: bool
    cors: CorsPolicyIR | None
    rate_limits: list[RateLimitRuleIR]
    pii_masking: list[PiiMaskingRuleIR]
    webhook_signature_required: bool
    source: SourceMetadata
    hash: str


@dataclass
class ReliabilityPolicyIR:
    id: str
    target_kind: str
    target_ref: RefIR
    timeout: TimeoutPolicyIR | None
    retry: RetryPolicyIR | None
    circuit_breaker: CircuitBreakerPolicyIR | None
    idempotency_key_field: str | None
    tags: list[str]
    source: SourceMetadata
    hash: str


@dataclass
class ObservabilityTargetIR:
    kind: str
    ref: RefIR
    log_fields: list[str]
    metrics: list[str]
    trace_enabled: bool
    alert_rules: list[str]
    source: SourceMetadata
    hash: str


@dataclass
class OpsIR:
    profiles: list[EnvironmentProfileIR] = field(default_factory=list)
    secrets: list[SecretRefIR] = field(default_factory=list)
    security: SecurityBaselineIR | None = None
    reliability_policies: list[ReliabilityPolicyIR] = field(default_factory=list)
    observability: list[ObservabilityTargetIR] = field(default_factory=list)


# ============================================================================
# Testing IR
# ============================================================================


@dataclass
class ContractTestStepIR:
    type: str
    ref: RefIR | None
    input: dict[str, Any]
    expect: dict[str, Any]


@dataclass
class ContractTestCaseIR:
    id: str
    kind: str
    framework: str | None
    description: str | None
    tags: list[str]
    steps: list[ContractTestStepIR]
    source: SourceMetadata
    hash: str
    scenario: RefIR | None = None


@dataclass
class TestingIR:
    tests: list[ContractTestCaseIR] = field(default_factory=list)


# ============================================================================
# Policy IR
# ============================================================================


@dataclass
class RoleIR:
    """Role in IR."""

    id: str
    description: str | None
    tags: list[str]
    source_ref: str | None
    source: SourceMetadata
    hash: str


@dataclass
class PermissionIR:
    """Permission in IR."""

    id: str
    description: str | None
    resource: str
    actions: list[str]
    tags: list[str]
    source_ref: str | None
    source: SourceMetadata
    hash: str


@dataclass
class BindingIR:
    """RBAC binding in IR."""

    role: str
    permissions: list[str]
    scope: str | None


@dataclass
class AccessPolicyIR:
    """Access control policy IR."""

    roles: list[RoleIR] = field(default_factory=list)
    permissions: list[PermissionIR] = field(default_factory=list)
    bindings: list[BindingIR] = field(default_factory=list)


@dataclass
class PolicyConditionIR:
    """Business policy condition in IR."""

    field: str
    operator: str
    value: Any


@dataclass
class PolicyEffectIR:
    """Business policy effect in IR."""

    type: str
    target: str | None
    params: dict[str, Any]


@dataclass
class BusinessPolicyIR:
    """Business policy in IR."""

    id: str
    description: str | None
    conditions: list[PolicyConditionIR]
    effects: list[PolicyEffectIR]
    tags: list[str]
    scope: str | None
    source_ref: str | None
    source: SourceMetadata
    hash: str


@dataclass
class PolicyIR:
    """Policy module IR."""

    access: AccessPolicyIR | None = None
    business: list[BusinessPolicyIR] = field(default_factory=list)


# ============================================================================
# Rules IR
# ============================================================================


@dataclass
class RuleRowIR:
    """Rule decision table row in IR."""

    conditions: dict[str, Any]
    result: Any


@dataclass
class RuleIR:
    """Rule in IR."""

    id: str
    description: str | None
    table: list[RuleRowIR]
    default_result: Any
    tags: list[str]
    applies_to: str | None
    applies_to_scenario: str | None
    inputs: list[str]
    outputs: list[str]
    severity: str | None
    source_ref: str | None
    source: SourceMetadata
    hash: str


@dataclass
class RulesIR:
    """Rules module IR."""

    rules: list[RuleIR] = field(default_factory=list)


# ============================================================================
# Scenarios IR
# ============================================================================


@dataclass
class ScenarioStepIR:
    """Scenario step in IR."""

    type: str  # "command", "query", "event", "assertion"
    ref: RefIR | None
    input: dict[str, Any]
    expect: dict[str, Any]
    description: str | None


@dataclass
class ScenarioIR:
    """Scenario in IR."""

    id: str
    description: str | None
    actors: list[str]
    preconditions: list[str]
    steps: list[ScenarioStepIR]
    postconditions: list[str]
    tags: list[str]
    source_ref: str | None
    source: SourceMetadata
    hash: str
    actor_roles: list[RefIR] = field(default_factory=list)


@dataclass
class ScenariosIR:
    """Scenarios module IR."""

    scenarios: list[ScenarioIR] = field(default_factory=list)


# ============================================================================
# Indexes and Metadata
# ============================================================================


@dataclass
class SymbolIndex:
    """Index entry for a symbol."""

    id: str
    type: str
    source_file: str
    hash: str


@dataclass
class RefIndex:
    """Index entry for a cross-reference."""

    source_type: str
    source_id: str
    source_field: str
    target_type: str
    target_id: str


@dataclass
class IRIndexes:
    """Global indexes for the IR."""

    symbols: dict[str, dict[str, SymbolIndex]] = field(default_factory=dict)
    refs: list[RefIndex] = field(default_factory=list)


@dataclass
class SourceFileMeta:
    """Metadata about a source file."""

    path: str
    checksum: str
    line_count: int


@dataclass
class Warning:
    """Warning from compilation."""

    stage: str
    code: str
    file: str
    message: str
    line: int | None = None


@dataclass
class IntentStats:
    """Statistics about inferred intents."""

    total: int = 0
    with_intent: int = 0
    missing: int = 0
    low_confidence: int = 0


@dataclass
class Stats:
    """Statistics about the compiled IR."""

    entities: int = 0
    value_objects: int = 0
    enums: int = 0
    errors: int = 0
    events: int = 0
    commands: int = 0
    queries: int = 0
    projections: int = 0
    workflows: int = 0
    rules: int = 0
    scenarios: int = 0
    http_routes: int = 0
    graphql_types: int = 0
    roles: int = 0
    permissions: int = 0
    policies: int = 0
    persistence_datasources: int = 0
    persistence_tables: int = 0
    integrations: int = 0
    integration_operations: int = 0
    webhooks: int = 0
    email_providers: int = 0
    oauth2_providers: int = 0
    profiles: int = 0
    secrets: int = 0
    reliability_policies: int = 0
    observability_targets: int = 0
    tests: int = 0


@dataclass
class IRMeta:
    """Metadata for the IR."""

    warnings: list[Warning] = field(default_factory=list)
    sources: list[SourceFileMeta] = field(default_factory=list)
    stats: Stats = field(default_factory=Stats)
    intent: IntentStats | None = None
    intent_summary: dict[str, Any] | None = None
    confidence_distribution: dict[str, int] | None = None


# ============================================================================
# Top-level IR
# ============================================================================


@dataclass
class IRModules:
    """All IR modules."""

    domain: DomainIR = field(default_factory=DomainIR)
    application: ApplicationIR = field(default_factory=ApplicationIR)
    workflow: WorkflowModuleIR = field(default_factory=WorkflowModuleIR)
    policy: PolicyIR = field(default_factory=PolicyIR)
    api: ApiIR = field(default_factory=ApiIR)
    persistence: PersistenceIR = field(default_factory=PersistenceIR)
    integrations: IntegrationsIR = field(default_factory=IntegrationsIR)
    ops: OpsIR = field(default_factory=OpsIR)
    rules: RulesIR = field(default_factory=RulesIR)
    scenarios: ScenariosIR = field(default_factory=ScenariosIR)
    testing: TestingIR = field(default_factory=TestingIR)


@dataclass
class IR:
    """Top-level IR structure."""

    version: str
    generated_at: str
    modules: IRModules
    indexes: IRIndexes
    meta: IRMeta
    schema_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert IR to dictionary for JSON serialization."""
        return asdict(self)
