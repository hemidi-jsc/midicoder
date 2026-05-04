"""
DSL v1 Catalogs Module

Centralized catalogs for all enum-like values used across DSL.
These are single source of truth for validation.
"""

from __future__ import annotations

from typing import Set

# ============================================================================
# DSL Version Catalog
# ============================================================================

DSL_VERSION_CATALOG: Set[str] = frozenset({
    "1.0.0",  # Current DSL version
})

# ============================================================================
# Tenant Scope Catalog
# ============================================================================

TENANT_SCOPE_CATALOG: Set[str] = frozenset({
    "global",    # Organization-wide, no tenant isolation
    "tenant",    # Isolated per tenant
    "user",      # Isolated per user within tenant
})

# ============================================================================
# Command Category Catalog
# ============================================================================

COMMAND_CATEGORY_CATALOG: Set[str] = frozenset({
    # CRUD Operations
    "crud.create",
    "crud.update",
    "crud.delete",
    "crud.read",
    
    # Authentication
    "auth.login",
    "auth.logout",
    "auth.register",
    "auth.reset_password",
    "auth.verify_email",
    
    # Billing
    "billing.charge",
    "billing.refund",
    "billing.update_payment_method",
    "billing.invoice",
    
    # Subscription
    "subscription.activate",
    "subscription.cancel",
    "subscription.change_plan",
    "subscription.renew",
    "subscription.suspend",
    
    # Workflow
    "workflow.transition",
    "workflow.start",
    "workflow.cancel",
    
    # Notification
    "notification.send_email",
    "notification.send_sms",
    "notification.send_push",
    
    # Admin
    "admin.create_user",
    "admin.delete_user",
    "admin.update_settings",
})

# ============================================================================
# Query Category Catalog
# ============================================================================

QUERY_CATEGORY_CATALOG: Set[str] = frozenset({
    "crud.list",
    "crud.get",
    "crud.search",
    "analytics.aggregate",
    "analytics.report",
    "audit.log_query",
})

# ============================================================================
# Constraint Type Catalog
# ============================================================================

CONSTRAINT_TYPE_CATALOG: Set[str] = frozenset({
    "unique",
    "check",
    "foreign_key",
    "not_null",
    "default",
    "primary_key",
})

# ============================================================================
# Field Type Catalog
# ============================================================================

FIELD_TYPE_CATALOG: Set[str] = frozenset({
    # Basic types
    "string",
    "integer",
    "float",
    "boolean",
    "datetime",
    "date",
    "time",
    
    # Complex types
    "json",
    "array",
    "object",
    
    # Reference types
    "uuid",
    "email",
    "url",
    "phone",
    
    # Domain-specific
    "currency",
    "decimal",
    "enum",
})

# ============================================================================
# HTTP Method Catalog
# ============================================================================

HTTP_METHOD_CATALOG: Set[str] = frozenset({
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "HEAD",
    "OPTIONS",
})

# ============================================================================
# HTTP Status Code Catalog
# ============================================================================

HTTP_STATUS_CATALOG: Set[str] = frozenset({
    # Success
    "200",
    "201",
    "204",
    
    # Redirect
    "301",
    "302",
    "304",
    
    # Client Error
    "400",
    "401",
    "403",
    "404",
    "409",
    "422",
    "429",
    
    # Server Error
    "500",
    "502",
    "503",
})

# ============================================================================
# Policy Effect Catalog
# ============================================================================

POLICY_EFFECT_CATALOG: Set[str] = frozenset({
    "allow",
    "deny",
    "require_confirmation",
    "require_approval",
})

# ============================================================================
# Workflow State Type Catalog
# ============================================================================

WORKFLOW_STATE_TYPE_CATALOG: Set[str] = frozenset({
    "initial",
    "intermediate",
    "terminal",
    "error",
})

# ============================================================================
# Workflow Gateway Type Catalog
# ============================================================================

WORKFLOW_GATEWAY_TYPE_CATALOG: Set[str] = frozenset({
    "exclusive",
    "inclusive",
    "event_based",
    "complex",
})

# ============================================================================
# Integration Auth Type Catalog
# ============================================================================

INTEGRATION_AUTH_TYPE_CATALOG: Set[str] = frozenset({
    "api_key",
    "oauth2",
    "basic",
    "jwt",
    "aws_sigv4",
    "none",
})

# ============================================================================
# Error Severity Catalog
# ============================================================================

ERROR_SEVERITY_CATALOG: Set[str] = frozenset({
    "info",
    "warning",
    "error",
    "critical",
})

# ============================================================================
# Error Category Catalog
# ============================================================================

ERROR_CATEGORY_CATALOG: Set[str] = frozenset({
    "validation",
    "authorization",
    "business_rule",
    "system",
    "integration",
    "unknown",
})

# ============================================================================
# Guard Type Catalog
# ============================================================================

GUARD_TYPE_CATALOG: Set[str] = frozenset({
    "authorization",
    "validation",
    "business_rule",
    "rate_limit",
    "circuit_breaker",
})

# ============================================================================
# Effect Type Catalog
# ============================================================================

EFFECT_TYPE_CATALOG: Set[str] = frozenset({
    "persist",
    "publish_event",
    "send_notification",
    "call_integration",
    "schedule_job",
    "log_audit",
})

# ============================================================================
# Rule Type Catalog
# ============================================================================

RULE_TYPE_CATALOG: Set[str] = frozenset({
    "business_rule",
    "validation_rule",
    "calculation_rule",
    "transformation_rule",
    "routing_rule",
})

# ============================================================================
# Event Type Catalog
# ============================================================================

EVENT_TYPE_CATALOG: Set[str] = frozenset({
    "domain_event",
    "integration_event",
    "system_event",
    "audit_event",
})

# ============================================================================
# Auth Provider Type Catalog
# ============================================================================

AUTH_PROVIDER_TYPE_CATALOG: Set[str] = frozenset({
    "oauth2",
    "oidc",
    "saml",
    "ldap",
    "jwt",
    "basic",
})

# ============================================================================
# Data Source Type Catalog
# ============================================================================

DATASOURCE_TYPE_CATALOG: Set[str] = frozenset({
    "postgresql",
    "mysql",
    "mariadb",
    "sqlite",
    "mssql",
    "oracle",
    "mongodb",
    "redis",
    "elastic",
    "dynamodb",
})

# ============================================================================
# Index Type Catalog
# ============================================================================

INDEX_TYPE_CATALOG: Set[str] = frozenset({
    "btree",
    "hash",
    "gin",
    "gist",
    "brin",
    "fulltext",
})

# ============================================================================
# Cache Type Catalog
# ============================================================================

CACHE_TYPE_CATALOG: Set[str] = frozenset({
    "memory",
    "redis",
    "memcached",
    "distributed",
})

# ============================================================================
# Queue Type Catalog
# ============================================================================

QUEUE_TYPE_CATALOG: Set[str] = frozenset({
    "rabbitmq",
    "kafka",
    "sqs",
    "redis",
    "in_memory",
})

# ============================================================================
# Metric Type Catalog
# ============================================================================

METRIC_TYPE_CATALOG: Set[str] = frozenset({
    "counter",
    "gauge",
    "histogram",
    "summary",
})

# ============================================================================
# Metric Aggregation Catalog
# ============================================================================

METRIC_AGGREGATION_CATALOG: Set[str] = frozenset({
    "sum",
    "avg",
    "min",
    "max",
    "count",
    "rate",
    "percentile",
})

# ============================================================================
# Log Level Catalog
# ============================================================================

LOG_LEVEL_CATALOG: Set[str] = frozenset({
    "debug",
    "info",
    "warning",
    "error",
    "critical",
})

# ============================================================================
# Log Format Catalog
# ============================================================================

LOG_FORMAT_CATALOG: Set[str] = frozenset({
    "json",
    "text",
    "structured",
    "pretty",
})

# ============================================================================
# Alert Severity Catalog
# ============================================================================

ALERT_SEVERITY_CATALOG: Set[str] = frozenset({
    "low",
    "medium",
    "high",
    "critical",
})

# ============================================================================
# Trace Exporter Catalog
# ============================================================================

TRACE_EXPORTER_CATALOG: Set[str] = frozenset({
    "jaeger",
    "zipkin",
    "otlp",
    "datadog",
    "newrelic",
})

# ============================================================================
# Integration Type Catalog
# ============================================================================

INTEGRATION_TYPE_CATALOG: Set[str] = frozenset({
    "http",
    "grpc",
    "webhook",
    "message_queue",
    "file",
    "database",
})

# ============================================================================
# GraphQL Operation Catalog
# ============================================================================

GRAPHQL_OPERATION_CATALOG: Set[str] = frozenset({
    "query",
    "mutation",
    "subscription",
})

# ============================================================================
# Webhook Auth Type Catalog
# ============================================================================

WEBHOOK_AUTH_TYPE_CATALOG: Set[str] = frozenset({
    "none",
    "api_key",
    "basic",
    "jwt",
    "signature",
})

# ============================================================================
# Observability Type Catalog
# ============================================================================

OBSERVABILITY_TYPE_CATALOG: Set[str] = frozenset({
    "metric",
    "log",
    "trace",
    "alert",
})

# ============================================================================
# Aggregate Type Catalog
# ============================================================================

AGGREGATE_TYPE_CATALOG: Set[str] = frozenset({
    "root",
    "embedded",
})

# ============================================================================
# Utility Functions
# ============================================================================


def validate_catalog_value(
    value: str,
    catalog: Set[str],
    field_name: str
) -> None:
    """
    Validate that a value is in the given catalog.
    
    Args:
        value: Value to validate
        catalog: Catalog set to check against
        field_name: Name of the field (for error message)
        
    Raises:
        ValueError: If value is not in catalog
    """
    if value not in catalog:
        valid_values = ", ".join(sorted(catalog))
        raise ValueError(
            f"Invalid {field_name}: '{value}'. "
            f"Must be one of: {valid_values}"
        )


def get_catalog_display_name(catalog_name: str) -> str:
    """
    Get human-readable name for a catalog.
    
    Args:
        catalog_name: Name of the catalog constant
        
    Returns:
        Display name
    """
    name_map = {
        "TENANT_SCOPE_CATALOG": "Tenant Scope",
        "COMMAND_CATEGORY_CATALOG": "Command Category",
        "QUERY_CATEGORY_CATALOG": "Query Category",
        "CONSTRAINT_TYPE_CATALOG": "Constraint Type",
        "FIELD_TYPE_CATALOG": "Field Type",
        "HTTP_METHOD_CATALOG": "HTTP Method",
        "HTTP_STATUS_CATALOG": "HTTP Status Code",
        "POLICY_EFFECT_CATALOG": "Policy Effect",
        "WORKFLOW_STATE_TYPE_CATALOG": "Workflow State Type",
        "WORKFLOW_GATEWAY_TYPE_CATALOG": "Workflow Gateway Type",
        "INTEGRATION_AUTH_TYPE_CATALOG": "Integration Auth Type",
        "ERROR_SEVERITY_CATALOG": "Error Severity",
        "ERROR_CATEGORY_CATALOG": "Error Category",
        "GUARD_TYPE_CATALOG": "Guard Type",
        "EFFECT_TYPE_CATALOG": "Effect Type",
        "RULE_TYPE_CATALOG": "Rule Type",
        "EVENT_TYPE_CATALOG": "Event Type",
        "AUTH_PROVIDER_TYPE_CATALOG": "Auth Provider Type",
        "DATASOURCE_TYPE_CATALOG": "Data Source Type",
        "INDEX_TYPE_CATALOG": "Index Type",
        "CACHE_TYPE_CATALOG": "Cache Type",
        "QUEUE_TYPE_CATALOG": "Queue Type",
        "METRIC_TYPE_CATALOG": "Metric Type",
        "METRIC_AGGREGATION_CATALOG": "Metric Aggregation",
        "LOG_LEVEL_CATALOG": "Log Level",
        "LOG_FORMAT_CATALOG": "Log Format",
        "ALERT_SEVERITY_CATALOG": "Alert Severity",
        "TRACE_EXPORTER_CATALOG": "Trace Exporter",
        "INTEGRATION_TYPE_CATALOG": "Integration Type",
        "GRAPHQL_OPERATION_CATALOG": "GraphQL Operation",
        "WEBHOOK_AUTH_TYPE_CATALOG": "Webhook Auth Type",
        "OBSERVABILITY_TYPE_CATALOG": "Observability Type",
        "AGGREGATE_TYPE_CATALOG": "Aggregate Type",
    }
    return name_map.get(catalog_name, catalog_name)


def get_catalog_value(catalog_name: str) -> Set[str]:
    """
    Get a catalog by name.
    
    Args:
        catalog_name: Name of the catalog constant
        
    Returns:
        Catalog set
    """
    catalogs = {
        "dsl_version": DSL_VERSION_CATALOG,
        "tenant_scope": TENANT_SCOPE_CATALOG,
        "command_category": COMMAND_CATEGORY_CATALOG,
        "query_category": QUERY_CATEGORY_CATALOG,
        "constraint_type": CONSTRAINT_TYPE_CATALOG,
        "field_type": FIELD_TYPE_CATALOG,
        "http_method": HTTP_METHOD_CATALOG,
        "http_status": HTTP_STATUS_CATALOG,
        "policy_effect": POLICY_EFFECT_CATALOG,
        "workflow_state_type": WORKFLOW_STATE_TYPE_CATALOG,
        "workflow_gateway_type": WORKFLOW_GATEWAY_TYPE_CATALOG,
        "integration_auth_type": INTEGRATION_AUTH_TYPE_CATALOG,
        "error_severity": ERROR_SEVERITY_CATALOG,
        "error_category": ERROR_CATEGORY_CATALOG,
        "guard_type": GUARD_TYPE_CATALOG,
        "effect_type": EFFECT_TYPE_CATALOG,
        "rule_type": RULE_TYPE_CATALOG,
        "event_type": EVENT_TYPE_CATALOG,
        "auth_provider_type": AUTH_PROVIDER_TYPE_CATALOG,
        "datasource_type": DATASOURCE_TYPE_CATALOG,
        "index_type": INDEX_TYPE_CATALOG,
        "cache_type": CACHE_TYPE_CATALOG,
        "queue_type": QUEUE_TYPE_CATALOG,
        "metric_type": METRIC_TYPE_CATALOG,
        "metric_aggregation": METRIC_AGGREGATION_CATALOG,
        "log_level": LOG_LEVEL_CATALOG,
        "log_format": LOG_FORMAT_CATALOG,
        "alert_severity": ALERT_SEVERITY_CATALOG,
        "trace_exporter": TRACE_EXPORTER_CATALOG,
        "integration_type": INTEGRATION_TYPE_CATALOG,
        "graphql_operation": GRAPHQL_OPERATION_CATALOG,
        "webhook_auth_type": WEBHOOK_AUTH_TYPE_CATALOG,
        "observability_type": OBSERVABILITY_TYPE_CATALOG,
        "aggregate_type": AGGREGATE_TYPE_CATALOG,
    }
    return catalogs.get(catalog_name, frozenset())
