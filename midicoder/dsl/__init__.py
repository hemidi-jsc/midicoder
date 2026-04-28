"""
DSL v1 Module - Kernel cho Midicoder CE

Module này cung cấp DSL (Domain Specific Language) kernel production-level
cho việc định nghĩa, validation, và generation của enterprise software systems.

Thay thế DSL v0 legacy với strongly-typed models và comprehensive validation.

Các thành phần chính:

1. Catalogs (30+ catalogs)
   - Enum catalogs cho tất cả DSL types
   - VALIDATION: Giá trị phải nằm trong catalog để pass validation

2. Metadata
   - Version tracking và provenance
   - Source location cho error reporting

3. Manifest
   - Root DSL manifest chứa tất cả components
   - Entry point cho DSL loading

4. Projection (101 node types)
   - ProjectionNode: Node đơn lẻ trong tree
   - ProjectionTree: Cây projection với indexing
   - TypedDict params cho mỗi node type

5. Constraints (34+ validators)
   - BaseConstraint: Abstract base class
   - ConstraintRegistry: Registry pattern cho validators
   - Validate node-level constraints

6. Dependencies
   - DependencyGraph: DAG builder
   - Cycle detection: DFS-based
   - Topological sort: Kahn's algorithm

7. Validator
   - Validation pipeline
   - ValidationReport với actionable insights

Sử dụng:

    from midicoder.dsl import (
        load_projection_tree,
        validate_tree,
        ProjectionNode,
        NodeKind,
    )

    # Load DSL từ directory
    tree = load_projection_tree("dsl/brief1/")

    # Validate
    report = validate_tree(tree)
    if not report.is_valid():
        print(format_report(report))

    # Access nodes
    entities = tree.get_entities()
    commands = tree.get_commands()

Version: 1.0.0
Author: Midicoder Team
"""

from .catalogs import (
    # Core catalogs
    DSL_VERSION_CATALOG,
    FIELD_TYPE_CATALOG,
    TENANT_SCOPE_CATALOG,
    COMMAND_CATEGORY_CATALOG,
    QUERY_CATEGORY_CATALOG,
    CONSTRAINT_TYPE_CATALOG,
    HTTP_METHOD_CATALOG,
    INTEGRATION_AUTH_TYPE_CATALOG,
    INTEGRATION_TYPE_CATALOG,
    WORKFLOW_STATE_TYPE_CATALOG,
    WORKFLOW_GATEWAY_TYPE_CATALOG,
    POLICY_EFFECT_CATALOG,
    GUARD_TYPE_CATALOG,
    EFFECT_TYPE_CATALOG,
    RULE_TYPE_CATALOG,
    EVENT_TYPE_CATALOG,
    ERROR_SEVERITY_CATALOG,
    ERROR_CATEGORY_CATALOG,
    # API catalogs
    HTTP_METHOD_CATALOG,
    GRAPHQL_OPERATION_CATALOG,
    # Infrastructure catalogs
    DATASOURCE_TYPE_CATALOG,
    AUTH_PROVIDER_TYPE_CATALOG,
    INDEX_TYPE_CATALOG,
    # Observability catalogs
    METRIC_TYPE_CATALOG,
    METRIC_AGGREGATION_CATALOG,
    LOG_LEVEL_CATALOG,
    LOG_FORMAT_CATALOG,
    ALERT_SEVERITY_CATALOG,
    TRACE_EXPORTER_CATALOG,
    # Validation helpers
    validate_catalog_value,
    get_catalog_value,
)

from .metadata import (
    Version,
    SourceLocation,
    ComponentMeta,
    ValidationContext,
)

from .manifest import (
    DSLManifest,
)

from .projection import (
    NodeKind,
    NodeParams,
    # Core classes
    ProjectionNode,
    ProjectionTree,
    NodeBuilder,
    # T03-001: Lazy Loading
    LazyProjectionTree,
    LazyNodeLoader,
    # Layer 2: Domain Layer Params (VO Extensions)
    EntityParams,
    ExtendedValueObjectParams,  # Value Object với complex fields, methods, validation
    FieldDefinition,  # Extended field definitions
    MethodDefinition,  # Value Object methods
    ValidationRule,  # Cross-field validation
    EnumParams,
    ErrorParams,
    EventParams,
    # Layer 3: Application Layer Params
    CommandParams,
    QueryParams,
    WorkflowParams,
    RuleParams,
    GuardParams,
    EffectParams,
    # Layer 4: Infrastructure Layer Params
    DataSourceParams,
    TableParams,
    IndexParams,
    CacheParams,
    QueueParams,
    # Layer 5: Platform/Access Control Layer Params
    RoleParams,
    PermissionParams,
    PolicyParams,
    # Layer 6: Integration/API Layer Params
    HTTPRouteParams,
    GraphQLResolverParams,
    WebhookParams,
    IntegrationParams,
    AuthProviderParams,
    # Layer 7: Ops/Observability Layer Params
    MetricParams,
    LogParams,
    AlertParams,
    TraceParams,
    # P0: Reporting & Analytics Params
    ReportParams,
    DashboardParams,
    ExportParams,
    ScheduledReportParams,
    # P0: Notification Params
    NotificationChannelParams,
    NotificationTemplateParams,
    NotificationRuleParams,
    MessageQueueParams,
    # P0: Compliance & Regulatory Params
    ComplianceRuleParams,
    RegulatoryOverlayParams,
    DataRetentionParams,
    PIIClassificationParams,
    AuditEventParams,
    CorrelationStrategyParams,
    # P0: Integration Contract Params
    APIContractParams,
    EventSchemaParams,
    DataMapperParams,
    # P1: Workflow Enhancement Params
    WorkflowGatewayParams,
    WorkflowTimerParams,
    WorkflowSubprocessParams,
    WorkflowCompensationParams,
    HumanTaskParams,
    # P1: Event-Driven Architecture Params
    EventPublisherParams,
    EventSubscriberParams,
    EventBusParams,
    CQRSProjectionParams,
    EventSourcingStreamParams,
    # P1: Search & Indexing Params
    SearchIndexParams,
    SearchQueryParams,
    FullTextFieldParams,
    # P2: Pagination & API Versioning Params
    PaginationSpecParams,
    APIVersionParams,
    DeprecationNoticeParams,
    # Aggregate (bonus node type)
    AggregateParams,
    # P2: E-commerce Domain Params
    ShoppingCartParams,
    ProductCatalogParams,
    PaymentGatewayParams,
    OrderFulfillmentParams,
    # P2: Finance Domain Params
    GeneralLedgerParams,
    FinancialInstrumentParams,
    CurrencyExchangeParams,
    TaxRuleParams,
    # P2: Healthcare Domain Params
    PatientRecordParams,
    ClinicalWorkflowParams,
    MedicationParams,
    # P2: Education Domain Params
    CourseParams,
    GradebookParams,
    # P2: Trading Domain Params
    OrderBookParams,
    TradingSessionParams,
    FIXProtocolParams,
    # P2: Logistics Domain Params
    WarehouseZoneParams,
    RouteOptimizationParams,
    # P2: Advanced - Caching & Performance Params
    CacheStrategyParams,
    RateLimiterParams,
    # P2: Advanced - Testing & Quality Params
    TestSuiteParams,
    QualityGateParams,
    # P2: Advanced - Data Management Params
    DataMigrationParams,
    BatchJobParams,
    # P2: Advanced - Messaging Params
    MessageSchemaParams,
    DeadLetterQueueParams,
    # P2: Advanced - Security Params
    EncryptionKeyParams,
    SecurityPolicyParams,
    # P1/P3: Enhanced Rule & Scoring Params
    RuleScoringParams,
    RuleMatcherParams,
    # P2/P3: Enhanced Integration & Protocol Params
    DeviceIntegrationParams,
    HL7FHIRSchemaParams,
    FIXMessageTypesParams,
    VideoConferencingIntegrationParams,
    # P3: Advanced Pattern Params
    ExternalServiceParams,
    LocalizationParams,
    CircuitBreakerParams,
    CalendarScheduleParams,
    SubledgerParams,
    # CP06: Kong Gateway Params
    KongGatewayParams,
    KongServiceParams,
    KongRouteParams,
    KongUpstreamParams,
    KongPluginParams,
    # CP06: Consul Service Mesh Params
    ConsulServiceMeshParams,
    ConsulServiceParams,
    ConsulConnectParams,
    ConsulHealthCheckParams,
)

from .constraints import (
    ConstraintLevel,
    ConstraintResult,
    BaseConstraint,
    ConstraintRegistry,
    get_registry,
    # Domain constraints
    EntityFieldTypesValid,
    EntityPrimaryKeyDefined,
    EntityTenantScopeValid,
    EntityConstraintTypesValid,
    ForeignKeyReferencesValid,
    # Application constraints
    CommandCategoryValid,
    QueryCategoryValid,
    CommandTenantScopeValid,
    WorkflowStateMachineValid,
    # API constraints
    HTTPMethodValid,
    HTTPRouteBindsToCommandOrQuery,
    GraphQLOperationValid,
    # Access control constraints
    RolePermissionsValid,
    RoleTenantScopeValid,
    PolicyEffectValid,
    # Integration constraints
    IntegrationAuthTypeValid,
    IntegrationTypeValid,
    DataSourceConnectionStringPresent,
    DataSourceTypeValid,
    AuthProviderTypeValid,
    # Error constraints
    ErrorSeverityValid,
    ErrorCategoryValid,
    ErrorCodeUnique,
    # Guard/Effect/Rule constraints
    GuardTypeValid,
    EffectTypeValid,
    RuleTypeValid,
    EventTypeValid,
    # Infrastructure constraints
    IndexTypeValid,
    # Observability constraints
    MetricTypeValid,
    MetricAggregationValid,
    LogLevelValid,
    LogFormatValid,
    AlertSeverityValid,
    TraceExporterValid,
)

from .dependencies import (
    # Core dependency types
    DependencyType,
    Dependency,
    DependencyGraph,
    CycleInfo,
    CycleDetectionResult,
    TopologicalSortResult,
    DependencyBuilder,
    DependencyAnalysis,
    detect_cycles,
    topological_sort,
    # T03-002: Caching Support
    LRUCache,
    CachingDependencyBuilder,
    cached_detect_cycles,
    cached_topological_sort,
    # Cache management
    get_cycle_cache,
    get_topo_cache,
    get_analysis_cache,
    clear_resolution_caches,
    get_cache_stats,
)

from .validator import (
    ValidationStatus,
    ValidationReport,
    Validator,
    ValidationError,
    ValidationCache,
    ValidationCacheEntry,
    format_report,
    validate_tree,
    quick_validate,
    get_actionable_insights,
)

from .loader import (
    # Core loaders
    load_yaml,
    load_projection_tree,
    load_yaml_unsafe,
    # T03-003: YAML Caching
    YAMLCache,
    get_yaml_cache,
    clear_yaml_cache,
    get_yaml_cache_stats,
    enable_yaml_caching,
    disable_yaml_caching,
    is_yaml_caching_enabled,
)

from .benchmarks import (
    # T03-004: Benchmarks
    BenchmarkResult,
    BenchmarkReport,
    run_all_benchmarks,
    benchmark_yaml_load,
    benchmark_yaml_load_cached,
    benchmark_yaml_load_uncached,
    benchmark_validation,
    benchmark_full_pipeline,
    compare_caching_performance,
    profile_memory_usage,
)


__version__ = "1.0.0"

__all__ = [
    # Catalogs
    "DSL_VERSION_CATALOG",
    "FIELD_TYPE_CATALOG",
    "TENANT_SCOPE_CATALOG",
    "COMMAND_CATEGORY_CATALOG",
    "QUERY_CATEGORY_CATALOG",
    "CONSTRAINT_TYPE_CATALOG",
    "HTTP_METHOD_CATALOG",
    "INTEGRATION_AUTH_TYPE_CATALOG",
    "INTEGRATION_TYPE_CATALOG",
    "WORKFLOW_STATE_TYPE_CATALOG",
    "WORKFLOW_GATEWAY_TYPE_CATALOG",
    "POLICY_EFFECT_CATALOG",
    "GUARD_TYPE_CATALOG",
    "EFFECT_TYPE_CATALOG",
    "RULE_TYPE_CATALOG",
    "EVENT_TYPE_CATALOG",
    "ERROR_SEVERITY_CATALOG",
    "ERROR_CATEGORY_CATALOG",
    "GRAPHQL_OPERATION_CATALOG",
    "DATASOURCE_TYPE_CATALOG",
    "AUTH_PROVIDER_TYPE_CATALOG",
    "INDEX_TYPE_CATALOG",
    "METRIC_TYPE_CATALOG",
    "METRIC_AGGREGATION_CATALOG",
    "LOG_LEVEL_CATALOG",
    "LOG_FORMAT_CATALOG",
    "ALERT_SEVERITY_CATALOG",
    "TRACE_EXPORTER_CATALOG",
    "validate_catalog_value",
    "get_catalog_value",
    # Metadata
    "Version",
    "SourceLocation",
    "ComponentMeta",
    "ValidationContext",
    # Manifest
    "DSLManifest",
    # Projection
    "NodeKind",
    "NodeParams",
    "ProjectionNode",
    "ProjectionTree",
    "NodeBuilder",
    # T03-001: Lazy Loading
    "LazyProjectionTree",
    "LazyNodeLoader",
    # Layer 2: Domain Layer Params
    "EntityParams",
    "ExtendedValueObjectParams",  # VO với complex fields
    "FieldDefinition",  # Extended field definitions
    "MethodDefinition",  # VO methods
    "ValidationRule",  # Cross-field validation
    "EnumParams",
    "ErrorParams",
    "EventParams",
    # Layer 3: Application Layer Params
    "CommandParams",
    "QueryParams",
    "WorkflowParams",
    "RuleParams",
    "GuardParams",
    "EffectParams",
    # Layer 4: Infrastructure Layer Params
    "DataSourceParams",
    "TableParams",
    "IndexParams",
    "CacheParams",
    "QueueParams",
    # Layer 5: Platform/Access Control Layer Params
    "RoleParams",
    "PermissionParams",
    "PolicyParams",
    # Layer 6: Integration/API Layer Params
    "HTTPRouteParams",
    "GraphQLResolverParams",
    "WebhookParams",
    "IntegrationParams",
    "AuthProviderParams",
    # Layer 7: Ops/Observability Layer Params
    "MetricParams",
    "LogParams",
    "AlertParams",
    "TraceParams",
    # P0: Reporting & Analytics Params
    "ReportParams",
    "DashboardParams",
    "ExportParams",
    "ScheduledReportParams",
    # P0: Notification Params
    "NotificationChannelParams",
    "NotificationTemplateParams",
    "NotificationRuleParams",
    "MessageQueueParams",
    # P0: Compliance & Regulatory Params
    "ComplianceRuleParams",
    "RegulatoryOverlayParams",
    "DataRetentionParams",
    "PIIClassificationParams",
    "AuditEventParams",
    "CorrelationStrategyParams",
    # P0: Integration Contract Params
    "APIContractParams",
    "EventSchemaParams",
    "DataMapperParams",
    # P1: Workflow Enhancement Params
    "WorkflowGatewayParams",
    "WorkflowTimerParams",
    "WorkflowSubprocessParams",
    "WorkflowCompensationParams",
    "HumanTaskParams",
    # P1: Event-Driven Architecture Params
    "EventPublisherParams",
    "EventSubscriberParams",
    "EventBusParams",
    "CQRSProjectionParams",
    "EventSourcingStreamParams",
    # P1: Search & Indexing Params
    "SearchIndexParams",
    "SearchQueryParams",
    "FullTextFieldParams",
    # P2: Pagination & API Versioning Params
    "PaginationSpecParams",
    "APIVersionParams",
    "DeprecationNoticeParams",
    # Aggregate (bonus node type)
    "AggregateParams",
    # v2.0: Value Object Extensions
    "FieldDefinition",
    "MethodDefinition",
    "ValidationRule",
    "ExtendedValueObjectParams",
    # Loader
    "load_yaml",
    "load_projection_tree",
    "load_yaml_unsafe",
    # T03-003: YAML Caching
    "YAMLCache",
    "get_yaml_cache",
    "clear_yaml_cache",
    "get_yaml_cache_stats",
    "enable_yaml_caching",
    "disable_yaml_caching",
    "is_yaml_caching_enabled",
    # Constraints
    "ConstraintLevel",
    "ConstraintResult",
    "BaseConstraint",
    "ConstraintRegistry",
    "get_registry",
    "EntityFieldTypesValid",
    "EntityPrimaryKeyDefined",
    "EntityTenantScopeValid",
    "EntityConstraintTypesValid",
    "ForeignKeyReferencesValid",
    "CommandCategoryValid",
    "QueryCategoryValid",
    "CommandTenantScopeValid",
    "WorkflowStateMachineValid",
    "HTTPMethodValid",
    "HTTPRouteBindsToCommandOrQuery",
    "GraphQLOperationValid",
    "RolePermissionsValid",
    "RoleTenantScopeValid",
    "PolicyEffectValid",
    "IntegrationAuthTypeValid",
    "IntegrationTypeValid",
    "DataSourceConnectionStringPresent",
    "DataSourceTypeValid",
    "AuthProviderTypeValid",
    "ErrorSeverityValid",
    "ErrorCategoryValid",
    "ErrorCodeUnique",
    "GuardTypeValid",
    "EffectTypeValid",
    "RuleTypeValid",
    "EventTypeValid",
    "IndexTypeValid",
    "MetricTypeValid",
    "MetricAggregationValid",
    "LogLevelValid",
    "LogFormatValid",
    "AlertSeverityValid",
    "TraceExporterValid",
    # Dependencies
    "DependencyType",
    "Dependency",
    "DependencyGraph",
    "CycleInfo",
    "CycleDetectionResult",
    "TopologicalSortResult",
    "DependencyBuilder",
    "DependencyAnalysis",
    "detect_cycles",
    "topological_sort",
    # T03-002: Dependency Caching
    "LRUCache",
    "CachingDependencyBuilder",
    "cached_detect_cycles",
    "cached_topological_sort",
    "get_cycle_cache",
    "get_topo_cache",
    "get_analysis_cache",
    "clear_resolution_caches",
    "get_cache_stats",
    # Validator
    "ValidationStatus",
    "ValidationReport",
    "Validator",
    "ValidationError",
    "ValidationCache",
    "ValidationCacheEntry",
    "format_report",
    "validate_tree",
    "quick_validate",
    "get_actionable_insights",
    # T03-004: Benchmarks
    "BenchmarkResult",
    "BenchmarkReport",
    "run_all_benchmarks",
    "benchmark_yaml_load",
    "benchmark_yaml_load_cached",
    "benchmark_yaml_load_uncached",
    "benchmark_validation",
    "benchmark_full_pipeline",
    "compare_caching_performance",
    "profile_memory_usage",
]
