"""DSL v1 Models - Re-exports from projection.py.

This module provides v1-compatible model exports from the projection module.
All models now use ProjectionNode with NodeKind enum for type safety.

REPLACES: v0 Pydantic models from schemas/*_model
"""

from __future__ import annotations

# ============================================================================
# Core Projection Models
# ============================================================================

from midicoder.dsl.projection import (
    NodeBuilder,
    NodeKind,
    NodeParams,
    ProjectionNode,
    ProjectionTree,
)

# ============================================================================
# Typed Parameter Models (for type hints)
# ============================================================================

from midicoder.dsl.projection import (
    # Domain Layer
    AggregateParams,
    EntityParams,
    EnumParams,
    ErrorParams,
    EventParams,
    EventSourcedAggregateParams,
    PolymorphicEntityParams,
    SagaParams,
    TemporalEntityParams,
    ValueObjectParams,

    # Application Layer
    AggregationQueryParams,
    CommandParams,
    EffectParams,
    GuardParams,
    QueryParams,
    RuleParams,
    WorkflowParams,
    
    # API Layer
    GraphQLResolverParams,
    HTTPRouteParams,
    WebhookParams,
    
    # Access Control
    PermissionParams,
    PolicyParams,
    RoleParams,
    
    # Infrastructure
    AuthProviderParams,
    CacheParams,
    DataSourceParams,
    IndexParams,
    IntegrationParams,
    QueueParams,
    TableParams,
    
    # Observability
    AlertParams,
    LogParams,
    MetricParams,
    TraceParams,
    
    # P0: Reporting
    DashboardParams,
    ExportParams,
    ReportParams,
    ScheduledReportParams,
    
    # P0: Notifications
    MessageQueueParams,
    NotificationChannelParams,
    NotificationRuleParams,
    NotificationTemplateParams,
    
    # P0: Compliance
    AuditEventParams,
    ComplianceRuleParams,
    CorrelationStrategyParams,
    DataRetentionParams,
    PIIClassificationParams,
    RegulatoryOverlayParams,
    
    # P0: Integration Contracts
    APIContractParams,
    DataMapperParams,
    EventSchemaParams,
    
    # P1: Workflow Enhancement
    HumanTaskParams,
    WorkflowCompensationParams,
    WorkflowGatewayParams,
    WorkflowSubprocessParams,
    WorkflowTimerParams,
    
    # P1: Event-Driven
    CQRSProjectionParams,
    EventBusParams,
    EventPublisherParams,
    EventSourcingStreamParams,
    EventSubscriberParams,
    
    # P1: Search
    FacetedSearchParams,
    FullTextFieldParams,
    GeoSearchParams,
    SearchIndexParams,
    SearchQueryParams,
    VectorSearchParams,
    
    # P2: Pagination & Versioning
    APIVersionParams,
    DeprecationNoticeParams,
    PaginationSpecParams,
    
    # P2: E-commerce
    OrderFulfillmentParams,
    PaymentGatewayParams,
    ProductCatalogParams,
    ShoppingCartParams,
    
    # P2: Finance
    CurrencyExchangeParams,
    FinancialInstrumentParams,
    GeneralLedgerParams,
    TaxRuleParams,
    
    # P2: Healthcare
    ClinicalWorkflowParams,
    MedicationParams,
    PatientRecordParams,
    
    # P2: Education
    CourseParams,
    GradebookParams,
    
    # P2: Trading
    FIXProtocolParams,
    OrderBookParams,
    TradingSessionParams,
    
    # P2: Logistics
    RouteOptimizationParams,
    WarehouseZoneParams,
    
    # P2: Advanced
    BatchJobParams,
    CacheStrategyParams,
    DataMigrationParams,
    DeadLetterQueueParams,
    EncryptionKeyParams,
    MessageSchemaParams,
    QualityGateParams,
    RateLimiterParams,
    SecurityPolicyParams,
    TestSuiteParams,
    
    # P1/P3: Enhanced Rule & Scoring
    RuleMatcherParams,
    RuleScoringParams,
    
    # P2/P3: Enhanced Integration
    DeviceIntegrationParams,
    FIXMessageTypesParams,
    HL7FHIRSchemaParams,
    VideoConferencingIntegrationParams,
    
    # P3: Advanced
    CalendarScheduleParams,
    CircuitBreakerParams,
    ExternalServiceParams,
    LocalizationParams,
    SubledgerParams,

    # CP18: Frontend Framework
    FrontendAppParams,
    FrontendRouteParams,
    FrontendStoreParams,

    # CP27: Plugin System
    PluginSlotParams,
    PluginContractParams,
    PluginPolicyParams,
)

__all__ = [
    # Core
    "ProjectionNode",
    "ProjectionTree",
    "NodeKind",
    "NodeParams",
    "NodeBuilder",
    
    # Domain Layer Params
    "EntityParams",
    "ValueObjectParams",
    "AggregateParams",
    "EnumParams",
    "ErrorParams",
    "EventParams",
    "EventSourcedAggregateParams",
    "PolymorphicEntityParams",
    "SagaParams",
    "TemporalEntityParams",

    # Application Layer Params
    "AggregationQueryParams",
    "CommandParams",
    "QueryParams",
    "WorkflowParams",
    "RuleParams",
    "GuardParams",
    "EffectParams",
    
    # API Layer Params
    "HTTPRouteParams",
    "GraphQLResolverParams",
    "WebhookParams",
    
    # Access Control Params
    "RoleParams",
    "PermissionParams",
    "PolicyParams",
    
    # Infrastructure Params
    "DataSourceParams",
    "TableParams",
    "IndexParams",
    "CacheParams",
    "QueueParams",
    "IntegrationParams",
    "AuthProviderParams",
    
    # Observability Params
    "MetricParams",
    "LogParams",
    "AlertParams",
    "TraceParams",
    
    # P0: Reporting Params
    "ReportParams",
    "DashboardParams",
    "ExportParams",
    "ScheduledReportParams",
    
    # P0: Notification Params
    "NotificationChannelParams",
    "NotificationTemplateParams",
    "NotificationRuleParams",
    "MessageQueueParams",
    
    # P0: Compliance Params
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
    
    # P1: Event-Driven Params
    "EventPublisherParams",
    "EventSubscriberParams",
    "EventBusParams",
    "CQRSProjectionParams",
    "EventSourcingStreamParams",
    
    # P1: Search Params
    "FacetedSearchParams",
    "FullTextFieldParams",
    "GeoSearchParams",
    "SearchIndexParams",
    "SearchQueryParams",
    "VectorSearchParams",
    
    # P2: Pagination & Versioning Params
    "PaginationSpecParams",
    "APIVersionParams",
    "DeprecationNoticeParams",
    
    # P2: E-commerce Params
    "ShoppingCartParams",
    "ProductCatalogParams",
    "PaymentGatewayParams",
    "OrderFulfillmentParams",
    
    # P2: Finance Params
    "GeneralLedgerParams",
    "FinancialInstrumentParams",
    "CurrencyExchangeParams",
    "TaxRuleParams",
    
    # P2: Healthcare Params
    "PatientRecordParams",
    "ClinicalWorkflowParams",
    "MedicationParams",
    
    # P2: Education Params
    "CourseParams",
    "GradebookParams",
    
    # P2: Trading Params
    "OrderBookParams",
    "TradingSessionParams",
    "FIXProtocolParams",
    
    # P2: Logistics Params
    "WarehouseZoneParams",
    "RouteOptimizationParams",
    
    # P2: Advanced Params
    "CacheStrategyParams",
    "RateLimiterParams",
    "TestSuiteParams",
    "QualityGateParams",
    "DataMigrationParams",
    "BatchJobParams",
    "MessageSchemaParams",
    "DeadLetterQueueParams",
    "EncryptionKeyParams",
    "SecurityPolicyParams",
    
    # P1/P3: Enhanced Rule & Scoring Params
    "RuleScoringParams",
    "RuleMatcherParams",
    
    # P2/P3: Enhanced Integration Params
    "DeviceIntegrationParams",
    "HL7FHIRSchemaParams",
    "FIXMessageTypesParams",
    "VideoConferencingIntegrationParams",
    
    # P3: Advanced Params
    "ExternalServiceParams",
    "LocalizationParams",
    "CircuitBreakerParams",
    "CalendarScheduleParams",
    "SubledgerParams",

    # CP18: Frontend Framework Params
    "FrontendAppParams",
    "FrontendRouteParams",
    "FrontendStoreParams",

    # CP27: Plugin System Params
    "PluginSlotParams",
    "PluginContractParams",
    "PluginPolicyParams",
]