"""
Capability Validator for Midicoder v1.0.0

Module này cung cấp runtime validation cho capability params.
Validation xảy ra khi:
1. Load contract graph từ JSON
2. Compile DSL → Contract
3. Before code generation

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from ..errors import ErrorCode, MidicoderErrorManager as EM
from .capability_params import (
    AuthorizedMutationParams,
    AuthorizedQueryParams,
    AuditLogParams,
    BatchJobParams,
    CacheStrategyParams,
    DataExportParams,
    DataImportParams,
    DataRetentionParams,
    EventHandlerParams,
    InboundIntegrationParams,
    MessageQueueParams,
    MonitoringParams,
    NotificationParams,
    OutboundIntegrationParams,
    RateLimitingParams,
    ScheduledTaskParams,
    WorkflowDefinitionParams,
)


# ============================================================================
# Validation Protocol
# ============================================================================


class Validator(Protocol):
    """Protocol cho validator functions."""

    def __call__(self, params: dict[str, Any]) -> list[str]:
        """
        Validate params.

        Args:
            params: Params để validate

        Returns:
            Danh sách error messages (rỗng nếu valid)
        """
        ...


# ============================================================================
# Core Capability Validators
# ============================================================================


def validate_authorized_mutation(params: dict[str, Any]) -> list[str]:
    """
    Validate AuthorizedMutationParams.

    Required fields:
        - actor_role (str)
        - permission (str)
        - writes (list[str])
        - tenant_scope (str)

    Optional fields:
        - reads (list[str])
        - transaction (str): "required" | "allowed" | "forbidden"
        - input_schema (dict)
        - output_schema (dict)
        - errors (list[str])
        - guards (list[dict])
        - effects (list[dict])
        - emits (list[str])

    Business Rules:
        1. permission không được rỗng
        2. writes phải có ít nhất 1 entity
        3. tenant_scope phải là giá trị hợp lệ
        4. transaction phải là giá trị hợp lệ nếu có
    """
    errors: list[str] = []

    # Required: actor_role
    if "actor_role" not in params:
        errors.append("Missing required field: actor_role")
    elif not isinstance(params["actor_role"], str) or not params["actor_role"]:
        errors.append("actor_role must be a non-empty string")

    # Required: permission
    if "permission" not in params:
        errors.append("Missing required field: permission")
    elif not isinstance(params["permission"], str) or not params["permission"]:
        errors.append("permission must be a non-empty string")

    # Required: writes (at least one entity)
    if "writes" not in params:
        errors.append("Missing required field: writes")
    elif not isinstance(params["writes"], list):
        errors.append("writes must be a list")
    elif len(params["writes"]) == 0:
        errors.append("writes must have at least one entity")
    elif not all(isinstance(w, str) and w for w in params["writes"]):
        errors.append("writes must contain non-empty strings only")

    # Required: tenant_scope
    if "tenant_scope" not in params:
        errors.append("Missing required field: tenant_scope")
    elif params["tenant_scope"] not in ("global", "tenant_isolated", "tenant_leaked"):
        errors.append(
            "tenant_scope must be one of: global, tenant_isolated, tenant_leaked"
        )

    # Optional: transaction
    if "transaction" in params:
        valid_values = ("required", "allowed", "forbidden")
        if params["transaction"] not in valid_values:
            errors.append(f"transaction must be one of: {', '.join(valid_values)}")

    # Optional: reads
    if "reads" in params and not isinstance(params["reads"], list):
        errors.append("reads must be a list")

    # Optional: emits
    if "emits" in params and not isinstance(params["emits"], list):
        errors.append("emits must be a list")

    # Optional: errors
    if "errors" in params and not isinstance(params["errors"], list):
        errors.append("errors must be a list")

    return errors


def validate_authorized_query(params: dict[str, Any]) -> list[str]:
    """
    Validate AuthorizedQueryParams.

    Required fields:
        - reads (list[str])

    Optional fields:
        - required_permission (str)
        - tenant_scope (str)
        - input_schema (dict)
        - output_schema (dict)
        - cache_config (dict)
    """
    errors: list[str] = []

    # Required: reads (at least one entity)
    if "reads" not in params:
        errors.append("Missing required field: reads")
    elif not isinstance(params["reads"], list):
        errors.append("reads must be a list")
    elif len(params["reads"]) == 0:
        errors.append("reads must have at least one entity")
    elif not all(isinstance(r, str) and r for r in params["reads"]):
        errors.append("reads must contain non-empty strings only")

    # Optional: tenant_scope
    if "tenant_scope" in params:
        valid_values = ("global", "tenant_isolated", "tenant_leaked")
        if params["tenant_scope"] not in valid_values:
            errors.append(
                f"tenant_scope must be one of: {', '.join(valid_values)}"
            )

    return errors


def validate_event_handler(params: dict[str, Any]) -> list[str]:
    """
    Validate EventHandlerParams.

    Required fields:
        - event_type (str)
        - handler_id (str)

    Optional fields:
        - retry_policy (dict)
        - timeout_ms (int)
        - async_processing (bool)
        - dead_letter_queue (dict)
    """
    errors: list[str] = []

    # Required: event_type
    if "event_type" not in params:
        errors.append("Missing required field: event_type")
    elif not isinstance(params["event_type"], str) or not params["event_type"]:
        errors.append("event_type must be a non-empty string")

    # Required: handler_id
    if "handler_id" not in params:
        errors.append("Missing required field: handler_id")
    elif not isinstance(params["handler_id"], str) or not params["handler_id"]:
        errors.append("handler_id must be a non-empty string")

    # Optional: timeout_ms
    if "timeout_ms" in params:
        if not isinstance(params["timeout_ms"], int) or params["timeout_ms"] <= 0:
            errors.append("timeout_ms must be a positive integer")

    # Optional: async_processing
    if "async_processing" in params and not isinstance(
        params["async_processing"], bool
    ):
        errors.append("async_processing must be a boolean")

    return errors


def validate_scheduled_task(params: dict[str, Any]) -> list[str]:
    """
    Validate ScheduledTaskParams.

    Required fields:
        - task_id (str)
        - cron_expression (str)

    Optional fields:
        - timezone (str)
        - max_duration_ms (int)
        - retry_policy (dict)
        - concurrency (dict)
    """
    errors: list[str] = []

    # Required: task_id
    if "task_id" not in params:
        errors.append("Missing required field: task_id")
    elif not isinstance(params["task_id"], str) or not params["task_id"]:
        errors.append("task_id must be a non-empty string")

    # Required: cron_expression
    if "cron_expression" not in params:
        errors.append("Missing required field: cron_expression")
    elif not isinstance(params["cron_expression"], str) or not params[
        "cron_expression"
    ]:
        errors.append("cron_expression must be a non-empty string")

    return errors


def validate_workflow_definition(params: dict[str, Any]) -> list[str]:
    """
    Validate WorkflowDefinitionParams.

    Required fields:
        - states (list[str])
        - transitions (list[dict])
        - start_state (str)

    Optional fields:
        - end_states (list[str])
        - compensation (list[dict])
        - human_tasks (list[dict])
        - timers (list[dict])
    """
    errors: list[str] = []

    # Required: states
    if "states" not in params:
        errors.append("Missing required field: states")
    elif not isinstance(params["states"], list):
        errors.append("states must be a list")
    elif len(params["states"]) == 0:
        errors.append("states must have at least one state")

    # Required: transitions
    if "transitions" not in params:
        errors.append("Missing required field: transitions")
    elif not isinstance(params["transitions"], list):
        errors.append("transitions must be a list")

    # Required: start_state
    if "start_state" not in params:
        errors.append("Missing required field: start_state")
    elif not isinstance(params["start_state"], str) or not params["start_state"]:
        errors.append("start_state must be a non-empty string")
    elif "states" in params and params["start_state"] not in params["states"]:
        errors.append("start_state must be one of the defined states")

    return errors


def validate_rule_engine(params: dict[str, Any]) -> list[str]:
    """
    Validate RuleEngineParams.

    Required fields:
        - rules (list[dict])

    Optional fields:
        - priority (int)
        - eval_order (str): "sequential" | "parallel"
        - short_circuit (bool)
    """
    errors: list[str] = []

    # Required: rules
    if "rules" not in params:
        errors.append("Missing required field: rules")
    elif not isinstance(params["rules"], list):
        errors.append("rules must be a list")
    elif len(params["rules"]) == 0:
        errors.append("rules must have at least one rule")

    # Optional: eval_order
    if "eval_order" in params:
        valid_values = ("sequential", "parallel")
        if params["eval_order"] not in valid_values:
            errors.append(f"eval_order must be one of: {', '.join(valid_values)}")

    return errors


def validate_aggregation(params: dict[str, Any]) -> list[str]:
    """
    Validate AggregationParams.

    Required fields:
        - source_entities (list[str])
        - group_by (list[str])
        - aggregations (list[dict])
    """
    errors: list[str] = []

    if "source_entities" not in params:
        errors.append("Missing required field: source_entities")
    elif not isinstance(params["source_entities"], list):
        errors.append("source_entities must be a list")
    elif len(params["source_entities"]) == 0:
        errors.append("source_entities must have at least one entity")

    if "group_by" not in params:
        errors.append("Missing required field: group_by")
    elif not isinstance(params["group_by"], list):
        errors.append("group_by must be a list")

    if "aggregations" not in params:
        errors.append("Missing required field: aggregations")
    elif not isinstance(params["aggregations"], list):
        errors.append("aggregations must be a list")
    elif len(params["aggregations"]) == 0:
        errors.append("aggregations must have at least one aggregation")

    return errors


def validate_search_index(params: dict[str, Any]) -> list[str]:
    """
    Validate SearchIndexParams.

    Required fields:
        - indexed_entities (list[str])
        - search_fields (list[str])
    """
    errors: list[str] = []

    if "indexed_entities" not in params:
        errors.append("Missing required field: indexed_entities")
    elif not isinstance(params["indexed_entities"], list):
        errors.append("indexed_entities must be a list")

    if "search_fields" not in params:
        errors.append("Missing required field: search_fields")
    elif not isinstance(params["search_fields"], list):
        errors.append("search_fields must be a list")

    return errors


def validate_cache_strategy(params: dict[str, Any]) -> list[str]:
    """
    Validate CacheStrategyParams.

    Required fields:
        - cache_type (str)
        - ttl_seconds (int)
    """
    errors: list[str] = []

    if "cache_type" not in params:
        errors.append("Missing required field: cache_type")
    elif not isinstance(params["cache_type"], str) or not params["cache_type"]:
        errors.append("cache_type must be a non-empty string")

    if "ttl_seconds" not in params:
        errors.append("Missing required field: ttl_seconds")
    elif not isinstance(params["ttl_seconds"], int) or params["ttl_seconds"] <= 0:
        errors.append("ttl_seconds must be a positive integer")

    return errors


def validate_notification(params: dict[str, Any]) -> list[str]:
    """
    Validate NotificationParams.

    Required fields:
        - channels (list[str])
    """
    errors: list[str] = []

    if "channels" not in params:
        errors.append("Missing required field: channels")
    elif not isinstance(params["channels"], list):
        errors.append("channels must be a list")
    elif len(params["channels"]) == 0:
        errors.append("channels must have at least one channel")

    return errors


# ============================================================================
# Integration Capability Validators
# ============================================================================


def validate_outbound_integration(params: dict[str, Any]) -> list[str]:
    """
    Validate OutboundIntegrationParams.

    Required fields:
        - target_system (str)
        - endpoint (str)
        - auth_type (str)
    """
    errors: list[str] = []

    if "target_system" not in params:
        errors.append("Missing required field: target_system")
    elif not isinstance(params["target_system"], str) or not params["target_system"]:
        errors.append("target_system must be a non-empty string")

    if "endpoint" not in params:
        errors.append("Missing required field: endpoint")
    elif not isinstance(params["endpoint"], str) or not params["endpoint"]:
        errors.append("endpoint must be a non-empty string")

    if "auth_type" not in params:
        errors.append("Missing required field: auth_type")
    elif params["auth_type"] not in ("bearer", "basic", "api_key", "signature"):
        errors.append(
            "auth_type must be one of: bearer, basic, api_key, signature"
        )

    return errors


def validate_inbound_integration(params: dict[str, Any]) -> list[str]:
    """
    Validate InboundIntegrationParams.

    Required fields:
        - path (str)
        - method (str)
        - auth_type (str)
        - handler_id (str)
    """
    errors: list[str] = []

    if "path" not in params:
        errors.append("Missing required field: path")
    elif not isinstance(params["path"], str) or not params["path"]:
        errors.append("path must be a non-empty string")

    if "method" not in params:
        errors.append("Missing required field: method")
    elif params["method"] not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
        errors.append(
            "method must be one of: GET, POST, PUT, DELETE, PATCH"
        )

    if "auth_type" not in params:
        errors.append("Missing required field: auth_type")

    if "handler_id" not in params:
        errors.append("Missing required field: handler_id")

    return errors


def validate_message_queue(params: dict[str, Any]) -> list[str]:
    """
    Validate MessageQueueParams.

    Required fields:
        - queue_type (str)
        - topic (str)
    """
    errors: list[str] = []

    if "queue_type" not in params:
        errors.append("Missing required field: queue_type")
    elif params["queue_type"] not in ("kafka", "rabbitmq", "sqs", "redis"):
        errors.append(
            "queue_type must be one of: kafka, rabbitmq, sqs, redis"
        )

    if "topic" not in params:
        errors.append("Missing required field: topic")
    elif not isinstance(params["topic"], str) or not params["topic"]:
        errors.append("topic must be a non-empty string")

    return errors


def validate_audit_log(params: dict[str, Any]) -> list[str]:
    """
    Validate AuditLogParams.

    Required fields:
        - log_events (list[str])
    """
    errors: list[str] = []

    if "log_events" not in params:
        errors.append("Missing required field: log_events")
    elif not isinstance(params["log_events"], list):
        errors.append("log_events must be a list")
    elif len(params["log_events"]) == 0:
        errors.append("log_events must have at least one event")

    return errors


def validate_rate_limiting(params: dict[str, Any]) -> list[str]:
    """
    Validate RateLimitingParams.

    Required fields:
        - limits (list[dict])
    """
    errors: list[str] = []

    if "limits" not in params:
        errors.append("Missing required field: limits")
    elif not isinstance(params["limits"], list):
        errors.append("limits must be a list")
    elif len(params["limits"]) == 0:
        errors.append("limits must have at least one limit")

    return errors


def validate_data_export(params: dict[str, Any]) -> list[str]:
    """
    Validate DataExportParams.

    Required fields:
        - source_entities (list[str])
        - format (str)
    """
    errors: list[str] = []

    if "source_entities" not in params:
        errors.append("Missing required field: source_entities")
    elif not isinstance(params["source_entities"], list):
        errors.append("source_entities must be a list")

    if "format" not in params:
        errors.append("Missing required field: format")
    elif params["format"] not in ("csv", "json", "parquet", "xml"):
        errors.append(
            "format must be one of: csv, json, parquet, xml"
        )

    return errors


def validate_data_import(params: dict[str, Any]) -> list[str]:
    """
    Validate DataImportParams.

    Required fields:
        - source (dict)
        - format (str)
        - target_entities (list[str])
    """
    errors: list[str] = []

    if "source" not in params:
        errors.append("Missing required field: source")
    elif not isinstance(params["source"], dict):
        errors.append("source must be a dictionary")

    if "format" not in params:
        errors.append("Missing required field: format")

    if "target_entities" not in params:
        errors.append("Missing required field: target_entities")
    elif not isinstance(params["target_entities"], list):
        errors.append("target_entities must be a list")

    return errors


def validate_batch_job(params: dict[str, Any]) -> list[str]:
    """
    Validate BatchJobParams.

    Required fields:
        - job_id (str)
    """
    errors: list[str] = []

    if "job_id" not in params:
        errors.append("Missing required field: job_id")
    elif not isinstance(params["job_id"], str) or not params["job_id"]:
        errors.append("job_id must be a non-empty string")

    return errors


def validate_data_retention(params: dict[str, Any]) -> list[str]:
    """
    Validate DataRetentionParams.

    Required fields:
        - entities (list[str])
        - retention_period (dict)
    """
    errors: list[str] = []

    if "entities" not in params:
        errors.append("Missing required field: entities")
    elif not isinstance(params["entities"], list):
        errors.append("entities must be a list")

    if "retention_period" not in params:
        errors.append("Missing required field: retention_period")
    elif not isinstance(params["retention_period"], dict):
        errors.append("retention_period must be a dictionary")

    return errors


def validate_monitoring(params: dict[str, Any]) -> list[str]:
    """
    Validate MonitoringParams.

    Required fields:
        - metrics (list[dict])
    """
    errors: list[str] = []

    if "metrics" not in params:
        errors.append("Missing required field: metrics")
    elif not isinstance(params["metrics"], list):
        errors.append("metrics must be a list")
    elif len(params["metrics"]) == 0:
        errors.append("metrics must have at least one metric")

    return errors


# ============================================================================
# E11-005: Audit Enforcement Validator (Compliance Audit Validation)
# ============================================================================


@dataclass
class ValidationResult:
    """
    Kết quả validation.
    
    Fields:
        is_valid: Validation pass hay fail
        error_messages: Danh sách error messages (rỗng nếu valid)
    """
    is_valid: bool
    error_messages: list[str] = None
    
    def __post_init__(self):
        if self.error_messages is None:
            self.error_messages = []
    
    @classmethod
    def pass_(cls) -> "ValidationResult":
        """Tạo validation result pass."""
        return cls(is_valid=True)
    
    @classmethod
    def fail(cls, *messages: str) -> "ValidationResult":
        """Tạo validation result fail với messages."""
        return cls(is_valid=False, error_messages=list(messages))


class AuditEnforcementValidator:
    """
    Validate audit trail enforcement cho compliance-critical operations.
    
    Task: E11-005 - Add AuditEnforcementValidator
    Priority: P1 - Required by Banking, Healthcare, ERP
    
    Validator này kiểm tra:
    - Compliance entities yêu cầu audit trail enabled
    - Audit level phải là "detailed" cho financial/healthcare
    - Retention period phải đáp ứng compliance requirements (SOX: 7 years, HIPAA: 6 years)
    
    Compliance Entities:
        Financial: LedgerEntry, FinancialTransaction, Payment, JournalEntry
        Healthcare: PatientRecord, MedicalPrescription, LabResult, PHIRecord
        ERP: InventoryAdjustment, PurchaseOrder
    
    Example:
        validator = AuditEnforcementValidator()
        result = validator.validate({"entity": "LedgerEntry", "audit_config": {...}})
        if not result.is_valid:
            print(result.error_messages)
    """
    
    # Compliance entity patterns (financial, healthcare, ERP)
    FINANCIAL_ENTITIES = {
        "LedgerEntry", "FinancialTransaction", "Payment", "JournalEntry",
        "Account", "BalanceSheet", "IncomeStatement", "CashFlow"
    }
    
    HEALTHCARE_ENTITIES = {
        "PatientRecord", "MedicalPrescription", "LabResult", "PHIRecord",
        "ClinicalNote", "Diagnosis", "Treatment", "Medication"
    }
    
    ERP_ENTITIES = {
        "InventoryAdjustment", "PurchaseOrder", "SalesOrder", "GoodsReceipt",
        "Invoice", "Supplier", "Asset"
    }
    
    # Minimum retention days by compliance standard
    MIN_RETENTION_DAYS = {
        "sox": 2555,  # 7 years for financial
        "hipaa": 2190,  # 6 years for healthcare
        "gdpr": 1825,  # 5 years minimum
    }
    
    def validate(self, params: dict[str, Any]) -> ValidationResult:
        """
        Validate audit enforcement cho compliance entities.
        
        Args:
            params: Params với entity và audit_config
            
        Returns:
            ValidationResult với is_valid và error_messages
        """
        errors: list[str] = []
        
        # Get entity from params
        entity = params.get("entity", "")
        
        # Check if this is a compliance entity
        if not self._is_compliance_entity(entity):
            # Non-compliance entities don't require audit enforcement
            return ValidationResult.pass_()
        
        # Check audit_config exists
        audit_config = params.get("audit_config") or params.get("audit_diff_config", {})
        
        if not audit_config:
            errors.append(
                f"Audit trail is required for compliance entity: {entity}"
            )
            return ValidationResult.fail(*errors)
        
        if not isinstance(audit_config, dict):
            errors.append(
                f"audit_config must be a dictionary for entity: {entity}"
            )
            return ValidationResult.fail(*errors)
        
        # Check audit enabled
        if not audit_config.get("enabled"):
            errors.append(
                f"Audit trail must be enabled for compliance entity: {entity}"
            )
        
        # Check audit level is "detailed"
        audit_level = audit_config.get("level", "")
        if audit_level != "detailed":
            errors.append(
                f"Audit level must be 'detailed' for compliance entity: {entity} "
                f"(got: '{audit_level}')"
            )
        
        # Check retention period
        retention_days = audit_config.get("retention_days", 0)
        min_retention = self._get_min_retention_days(entity)
        
        if retention_days < min_retention:
            errors.append(
                f"Audit retention must be at least {min_retention} days "
                f"({min_retention // 365} years) for compliance entity: {entity} "
                f"(got: {retention_days} days)"
            )
        
        if errors:
            return ValidationResult.fail(*errors)
        
        return ValidationResult.pass_()
    
    def _is_compliance_entity(self, entity: str) -> bool:
        """
        Kiểm tra entity có phải là compliance entity không.
        
        Args:
            entity: Entity name
            
        Returns:
            True nếu là compliance entity
        """
        all_compliance_entities = (
            self.FINANCIAL_ENTITIES |
            self.HEALTHCARE_ENTITIES |
            self.ERP_ENTITIES
        )
        
        # Check exact match
        if entity in all_compliance_entities:
            return True
        
        # Check partial match (e.g., "LedgerEntryV2" matches "LedgerEntry")
        for compliance_entity in all_compliance_entities:
            if entity.startswith(compliance_entity):
                return True
        
        return False
    
    def _get_min_retention_days(self, entity: str) -> int:
        """
        Lấy minimum retention days cho entity.
        
        Args:
            entity: Entity name
            
        Returns:
            Minimum retention days theo compliance standard
        """
        # Financial entities: SOX (7 years = 2555 days)
        if entity in self.FINANCIAL_ENTITIES or any(
            entity.startswith(e) for e in self.FINANCIAL_ENTITIES
        ):
            return self.MIN_RETENTION_DAYS["sox"]
        
        # Healthcare entities: HIPAA (6 years = 2190 days)
        if entity in self.HEALTHCARE_ENTITIES or any(
            entity.startswith(e) for e in self.HEALTHCARE_ENTITIES
        ):
            return self.MIN_RETENTION_DAYS["hipaa"]
        
        # ERP entities: default to 5 years (GDPR minimum)
        return self.MIN_RETENTION_DAYS["gdpr"]


# ============================================================================
# Validator Registry
# ============================================================================

# Mapping capability type → validator function
CAPABILITY_VALIDATORS: dict[str, Validator] = {
    "authorized_mutation": validate_authorized_mutation,
    "authorized_query": validate_authorized_query,
    "event_handler": validate_event_handler,
    "scheduled_task": validate_scheduled_task,
    "workflow_definition": validate_workflow_definition,
    "rule_engine": validate_rule_engine,
    "aggregation": validate_aggregation,
    "search_index": validate_search_index,
    "cache_strategy": validate_cache_strategy,
    "notification": validate_notification,
    "outbound_integration": validate_outbound_integration,
    "inbound_integration": validate_inbound_integration,
    "message_queue": validate_message_queue,
    "audit_log": validate_audit_log,
    "rate_limiting": validate_rate_limiting,
    "data_export": validate_data_export,
    "data_import": validate_data_import,
    "batch_job": validate_batch_job,
    "data_retention": validate_data_retention,
    "monitoring": validate_monitoring,
}


def validate_capability_params(
    capability_type: str,
    params: dict[str, Any],
    capability_id: str | None = None,
    raise_on_error: bool = True,
) -> list[str]:
    """
    Validate capability params theo type.

    Args:
        capability_type: Loại capability (e.g., "authorized_mutation")
        params: Params để validate
        capability_id: ID của capability (optional, cho context trong error message)
        raise_on_error: Nếu True, throw MidicoderError khi validation fail
                       Nếu False, trả về list errors

    Returns:
        Danh sách error messages (rỗng nếu valid)

    Raises:
        MidicoderError: Nếu raise_on_error=True và có validation errors
    """
    # Check if capability type is known
    validator = CAPABILITY_VALIDATORS.get(capability_type)
    if not validator:
        errors = [f"Unknown capability type: {capability_type}"]
        if raise_on_error:
            EM.raise_error(
                ErrorCode.CAPABILITY_TYPE_UNKNOWN,
                capability_type=capability_type,
                capability_id=capability_id,
                known_types=get_known_capability_types(),
            )
        return errors

    # Run validation
    errors = validator(params)

    # Add context to errors
    if errors and capability_id:
        errors = [f"{capability_id}: {err}" for err in errors]

    # Raise error if needed
    if errors and raise_on_error:
        EM.raise_error(
            ErrorCode.CAPABILITY_PARAMS_INVALID,
            capability_type=capability_type,
            capability_id=capability_id,
            params=params,
            validation_errors=errors,
        )

    return errors


def get_known_capability_types() -> list[str]:
    """
    Lấy danh sách capability types đã biết.

    Returns:
        Danh sách capability types
    """
    return list(CAPABILITY_VALIDATORS.keys())


__all__ = [
    "CAPABILITY_VALIDATORS",
    "validate_capability_params",
    "get_known_capability_types",
    # E11-005: Audit enforcement
    "ValidationResult",
    "AuditEnforcementValidator",
]
