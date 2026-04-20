"""
Macro Capabilities Registry cho Midicoder v1.0.0.

Module này định nghĩa registry của 50+ Macro Capabilities.

Macro capabilities là high-level patterns expand về core capabilities:
- Base patterns: authorized_mutation, authorized_query, event_handler, workflow_definition
- Mutation patterns: create_with_audit, update_with_validation, soft_delete_with_audit...
- Query patterns: paginated_query, search_query, aggregate_query...
- Workflow patterns: state_machine_transition, async_job, saga_orchestration...
- Domain patterns: create_order, transfer_funds, create_patient_record...
- Regulatory patterns: kyc_verification, pii_encryption, immutable_audit...

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .graph import MacroCapability


# ============================================================================
# Base Macro Capabilities (6 macros)
# ============================================================================
# Các macro cơ bản mà mọi macro khác đều dựa vào
# ============================================================================


@dataclass
class BaseMacroCapabilities:
    """
    Base Macro Capabilities (6 macros).
    
    Các patterns cơ bản nhất cho authorization, query, event handling.
    """
    
    # SoT: AUTHORIZED_MUTATION
    AUTHORIZED_MUTATION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="authorized_mutation",
            name="Authorized Mutation",
            description="Mutation với permission check, tenant scope, transaction, và audit",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "begin_transaction",
                "create_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check (vd: 'order.create')"
                },
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "data": {
                    "type": "object",
                    "required": True,
                    "description": "Record data"
                },
                "event_type": {
                    "type": "string",
                    "required": False,
                    "description": "Event type để publish"
                },
                "tenant_scope": {
                    "type": "string",
                    "required": False,
                    "default": "tenant_isolated",
                    "enum": ["tenant_isolated", "tenant_inclusive", "cross_tenant"],
                    "description": "Tenant scope mode"
                },
            },
            default_obligations=[
                "permission_check_required",
                "tenant_filter_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # SoT: AUTHORIZED_QUERY
    AUTHORIZED_QUERY: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="authorized_query",
            name="Authorized Query",
            description="Query với permission check và tenant scope",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "query_records",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check (vd: 'order.read')"
                },
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "filter": {
                    "type": "object",
                    "required": False,
                    "description": "Filter conditions"
                },
                "sort": {
                    "type": "array",
                    "required": False,
                    "description": "Sort order"
                },
                "page": {
                    "type": "integer",
                    "required": False,
                    "default": 1,
                    "description": "Page number"
                },
                "per_page": {
                    "type": "integer",
                    "required": False,
                    "default": 20,
                    "description": "Records per page"
                },
            },
            default_obligations=[
                "permission_check_required",
                "tenant_filter_required",
            ],
        )
    )
    
    # SoT: EVENT_HANDLER
    EVENT_HANDLER: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="event_handler",
            name="Event Handler",
            description="Event handler với validation và transaction",
            expands_to=[
                "validate_input",
                "begin_transaction",
                "update_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "event_type": {
                    "type": "string",
                    "required": True,
                    "description": "Event type để subscribe"
                },
                "handler": {
                    "type": "string",
                    "required": True,
                    "description": "Handler function name"
                },
                "validation_schema": {
                    "type": "object",
                    "required": False,
                    "description": "Validation schema cho event payload"
                },
                "async": {
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "description": "Handle async"
                },
            },
            default_obligations=[
                "input_validation_required",
                "transaction_required",
                "error_handler_required",
            ],
        )
    )
    
    # SoT: WORKFLOW_DEFINITION
    WORKFLOW_DEFINITION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="workflow_definition",
            name="Workflow Definition",
            description="Workflow definition với state machine và transitions",
            expands_to=[
                "validate_input",
                "load_entity",
                "update_record",
                "publish_event",
            ],
            params_schema={
                "workflow_name": {
                    "type": "string",
                    "required": True,
                    "description": "Workflow name"
                },
                "states": {
                    "type": "array",
                    "required": True,
                    "description": "List of states"
                },
                "transitions": {
                    "type": "array",
                    "required": True,
                    "description": "List of transitions"
                },
                "initial_state": {
                    "type": "string",
                    "required": True,
                    "description": "Initial state"
                },
            },
            default_obligations=[
                "input_validation_required",
                "audit_log_required",
            ],
        )
    )
    
    # CASCADE_MUTATION
    CASCADE_MUTATION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="cascade_mutation",
            name="Cascade Mutation",
            description="Mutation cascade qua nhiều entities trong một transaction",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "begin_transaction",
                "create_record",
                "update_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check"
                },
                "entities": {
                    "type": "array",
                    "required": True,
                    "description": "List of entities to mutate"
                },
                "operations": {
                    "type": "array",
                    "required": True,
                    "description": "List of operations (create/update)"
                },
            },
            default_obligations=[
                "permission_check_required",
                "tenant_filter_required",
                "transaction_required",
            ],
        )
    )
    
    # AGGREGATE_OPERATION
    AGGREGATE_OPERATION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="aggregate_operation",
            name="Aggregate Operation",
            description="Operation trên aggregate root với domain events",
            expands_to=[
                "authorize_permission",
                "load_entity",
                "update_record",
                "publish_event",
                "write_audit_log",
            ],
            params_schema={
                "aggregate_type": {
                    "type": "string",
                    "required": True,
                    "description": "Aggregate root type"
                },
                "aggregate_id": {
                    "type": "string",
                    "required": True,
                    "description": "Aggregate root ID"
                },
                "command": {
                    "type": "string",
                    "required": True,
                    "description": "Command name"
                },
                "payload": {
                    "type": "object",
                    "required": False,
                    "description": "Command payload"
                },
            },
            default_obligations=[
                "permission_check_required",
                "audit_log_required",
            ],
        )
    )


# ============================================================================
# Mutation Macro Capabilities (8 macros)
# ============================================================================
# Các patterns cho mutation operations
# ============================================================================


@dataclass
class MutationMacroCapabilities:
    """
    Mutation Macro Capabilities (8 macros).
    
    Các patterns cho CRUD operations với additional concerns.
    """
    
    # CREATE_WITH_AUDIT
    CREATE_WITH_AUDIT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="create_with_audit",
            name="Create With Audit",
            description="Tạo record với audit trail đầy đủ",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "create_record",
                "write_audit_log",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check"
                },
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "data": {
                    "type": "object",
                    "required": True,
                    "description": "Record data"
                },
                "audit_level": {
                    "type": "string",
                    "required": False,
                    "default": "standard",
                    "enum": ["minimal", "standard", "detailed"],
                    "description": "Audit level"
                },
            },
            default_obligations=[
                "permission_check_required",
                "input_validation_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # UPDATE_WITH_VALIDATION
    UPDATE_WITH_VALIDATION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="update_with_validation",
            name="Update With Validation",
            description="Cập nhật record với validation đầy đủ",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "update_record",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check"
                },
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "id": {
                    "type": "string",
                    "required": True,
                    "description": "Record ID"
                },
                "data": {
                    "type": "object",
                    "required": True,
                    "description": "Update data"
                },
                "validation_rules": {
                    "type": "array",
                    "required": False,
                    "description": "Validation rules"
                },
            },
            default_obligations=[
                "permission_check_required",
                "input_validation_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # SOFT_DELETE_WITH_AUDIT
    SOFT_DELETE_WITH_AUDIT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="soft_delete_with_audit",
            name="Soft Delete With Audit",
            description="Soft delete với audit trail",
            expands_to=[
                "authorize_permission",
                "load_entity",
                "begin_transaction",
                "update_record",
                "write_audit_log",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check"
                },
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "id": {
                    "type": "string",
                    "required": True,
                    "description": "Record ID"
                },
                "reason": {
                    "type": "string",
                    "required": False,
                    "description": "Reason for deletion"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # BULK_CREATE
    BULK_CREATE: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="bulk_create",
            name="Bulk Create",
            description="Tạo nhiều records trong một transaction",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "create_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check"
                },
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "records": {
                    "type": "array",
                    "required": True,
                    "description": "List of records to create"
                },
                "batch_size": {
                    "type": "integer",
                    "required": False,
                    "default": 100,
                    "description": "Batch size"
                },
            },
            default_obligations=[
                "permission_check_required",
                "input_validation_required",
                "transaction_required",
            ],
        )
    )
    
    # UPSERT_RECORD
    UPSERT_RECORD: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="upsert_record",
            name="Upsert Record",
            description="Tạo mới hoặc cập nhật record",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "create_record",
                "update_record",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check"
                },
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "id": {
                    "type": "string",
                    "required": True,
                    "description": "Record ID"
                },
                "data": {
                    "type": "object",
                    "required": True,
                    "description": "Record data"
                },
                "upsert_key": {
                    "type": "string",
                    "required": False,
                    "description": "Key để upsert"
                },
            },
            default_obligations=[
                "permission_check_required",
                "input_validation_required",
                "transaction_required",
            ],
        )
    )
    
    # BATCH_UPDATE
    BATCH_UPDATE: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="batch_update",
            name="Batch Update",
            description="Cập nhật nhiều records trong một transaction",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "query_records",
                "update_record",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check"
                },
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "filter": {
                    "type": "object",
                    "required": True,
                    "description": "Filter để chọn records"
                },
                "data": {
                    "type": "object",
                    "required": True,
                    "description": "Update data"
                },
            },
            default_obligations=[
                "permission_check_required",
                "input_validation_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # ARCHIVE_RECORD
    ARCHIVE_RECORD: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="archive_record",
            name="Archive Record",
            description="Archive record với full audit",
            expands_to=[
                "authorize_permission",
                "load_entity",
                "begin_transaction",
                "update_record",
                "write_audit_log",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check"
                },
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "id": {
                    "type": "string",
                    "required": True,
                    "description": "Record ID"
                },
                "archive_reason": {
                    "type": "string",
                    "required": False,
                    "description": "Reason for archiving"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # FORCE_DELETE
    FORCE_DELETE: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="force_delete",
            name="Force Delete",
            description="Force delete với strict audit trail",
            expands_to=[
                "authorize_permission",
                "load_entity",
                "begin_transaction",
                "write_audit_log",
                "delete_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check (admin level)"
                },
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "id": {
                    "type": "string",
                    "required": True,
                    "description": "Record ID"
                },
                "reason": {
                    "type": "string",
                    "required": True,
                    "description": "Reason for force delete (mandatory)"
                },
                "approver_id": {
                    "type": "string",
                    "required": False,
                    "description": "Approver ID nếu cần approval"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
                "immutable_evidence_required",
            ],
        )
    )


# ============================================================================
# Query Macro Capabilities (6 macros)
# ============================================================================
# Các patterns cho query operations
# ============================================================================


@dataclass
class QueryMacroCapabilities:
    """
    Query Macro Capabilities (6 macros).
    
    Các patterns cho reading data với different concerns.
    """
    
    # PAGINATED_QUERY
    PAGINATED_QUERY: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="paginated_query",
            name="Paginated Query",
            description="Query với pagination và sorting",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "query_records",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check"
                },
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "page": {
                    "type": "integer",
                    "required": False,
                    "default": 1,
                    "description": "Page number"
                },
                "per_page": {
                    "type": "integer",
                    "required": False,
                    "default": 20,
                    "description": "Records per page"
                },
                "sort": {
                    "type": "array",
                    "required": False,
                    "description": "Sort order"
                },
                "filter": {
                    "type": "object",
                    "required": False,
                    "description": "Filter conditions"
                },
            },
            default_obligations=[
                "permission_check_required",
                "tenant_filter_required",
            ],
        )
    )
    
    # SEARCH_QUERY
    SEARCH_QUERY: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="search_query",
            name="Search Query",
            description="Full-text search query",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "query_records",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check"
                },
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "query": {
                    "type": "string",
                    "required": True,
                    "description": "Search query"
                },
                "fields": {
                    "type": "array",
                    "required": False,
                    "description": "Fields to search"
                },
                "fuzziness": {
                    "type": "string",
                    "required": False,
                    "default": "auto",
                    "description": "Fuzziness level"
                },
            },
            default_obligations=[
                "permission_check_required",
                "tenant_filter_required",
            ],
        )
    )
    
    # AGGREGATE_QUERY
    AGGREGATE_QUERY: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="aggregate_query",
            name="Aggregate Query",
            description="Aggregate query (count, sum, avg, etc.)",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "query_records",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check"
                },
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "aggregations": {
                    "type": "array",
                    "required": True,
                    "description": "List of aggregations"
                },
                "group_by": {
                    "type": "array",
                    "required": False,
                    "description": "Group by fields"
                },
                "filter": {
                    "type": "object",
                    "required": False,
                    "description": "Filter conditions"
                },
            },
            default_obligations=[
                "permission_check_required",
                "tenant_filter_required",
            ],
        )
    )
    
    # LOAD_WITH_RELATIONS
    LOAD_WITH_RELATIONS: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="load_with_relations",
            name="Load With Relations",
            description="Load entity với relations",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "load_entity",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check"
                },
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "id": {
                    "type": "string",
                    "required": True,
                    "description": "Entity ID"
                },
                "include": {
                    "type": "array",
                    "required": True,
                    "description": "Relations to include"
                },
                "max_depth": {
                    "type": "integer",
                    "required": False,
                    "default": 2,
                    "description": "Max depth of relations"
                },
            },
            default_obligations=[
                "permission_check_required",
                "tenant_filter_required",
            ],
        )
    )
    
    # EXPORT_QUERY
    EXPORT_QUERY: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="export_query",
            name="Export Query",
            description="Export query với full dataset",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "query_records",
                "write_audit_log",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check"
                },
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "format": {
                    "type": "string",
                    "required": True,
                    "enum": ["csv", "xlsx", "json"],
                    "description": "Export format"
                },
                "filter": {
                    "type": "object",
                    "required": False,
                    "description": "Filter conditions"
                },
                "fields": {
                    "type": "array",
                    "required": False,
                    "description": "Fields to export"
                },
            },
            default_obligations=[
                "permission_check_required",
                "tenant_filter_required",
                "audit_log_required",
            ],
        )
    )
    
    # COUNT_QUERY
    COUNT_QUERY: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="count_query",
            name="Count Query",
            description="Count records với filter",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "query_records",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check"
                },
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "filter": {
                    "type": "object",
                    "required": False,
                    "description": "Filter conditions"
                },
            },
            default_obligations=[
                "permission_check_required",
                "tenant_filter_required",
            ],
        )
    )


# ============================================================================
# Workflow Macro Capabilities (6 macros)
# ============================================================================
# Các patterns cho workflow và state machines
# ============================================================================


@dataclass
class WorkflowMacroCapabilities:
    """
    Workflow Macro Capabilities (6 macros).
    
    Các patterns cho workflows, state machines, và async jobs.
    """
    
    # STATE_MACHINE_TRANSITION
    STATE_MACHINE_TRANSITION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="state_machine_transition",
            name="State Machine Transition",
            description="Transition trong state machine với guards",
            expands_to=[
                "authorize_permission",
                "load_entity",
                "validate_input",
                "begin_transaction",
                "update_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check"
                },
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "id": {
                    "type": "string",
                    "required": True,
                    "description": "Entity ID"
                },
                "transition": {
                    "type": "string",
                    "required": True,
                    "description": "Transition name"
                },
                "payload": {
                    "type": "object",
                    "required": False,
                    "description": "Transition payload"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # ASYNC_JOB
    ASYNC_JOB: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="async_job",
            name="Async Job",
            description="Async job với queue và retry",
            expands_to=[
                "validate_input",
                "create_record",
                "publish_event",
            ],
            params_schema={
                "job_name": {
                    "type": "string",
                    "required": True,
                    "description": "Job name"
                },
                "payload": {
                    "type": "object",
                    "required": True,
                    "description": "Job payload"
                },
                "priority": {
                    "type": "string",
                    "required": False,
                    "default": "normal",
                    "enum": ["low", "normal", "high", "critical"],
                    "description": "Job priority"
                },
                "retry_policy": {
                    "type": "object",
                    "required": False,
                    "description": "Retry policy"
                },
                "timeout": {
                    "type": "integer",
                    "required": False,
                    "description": "Job timeout in seconds"
                },
            },
            default_obligations=[
                "input_validation_required",
                "error_handler_required",
            ],
        )
    )
    
    # SAGA_ORCHESTRATION
    SAGA_ORCHESTRATION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="saga_orchestration",
            name="Saga Orchestration",
            description="Saga orchestration với compensation",
            expands_to=[
                "validate_input",
                "begin_transaction",
                "create_record",
                "publish_event",
                "call_external_service",
                "commit_transaction",
            ],
            params_schema={
                "saga_name": {
                    "type": "string",
                    "required": True,
                    "description": "Saga name"
                },
                "steps": {
                    "type": "array",
                    "required": True,
                    "description": "Saga steps"
                },
                "compensation_steps": {
                    "type": "array",
                    "required": True,
                    "description": "Compensation steps"
                },
                "timeout": {
                    "type": "integer",
                    "required": False,
                    "description": "Saga timeout in seconds"
                },
            },
            default_obligations=[
                "input_validation_required",
                "transaction_required",
                "error_handler_required",
            ],
        )
    )
    
    # APPROVAL_WORKFLOW
    APPROVAL_WORKFLOW: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="approval_workflow",
            name="Approval Workflow",
            description="Approval workflow với multiple approvers",
            expands_to=[
                "authorize_permission",
                "load_entity",
                "validate_input",
                "begin_transaction",
                "update_record",
                "publish_event",
                "send_notification",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check"
                },
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "id": {
                    "type": "string",
                    "required": True,
                    "description": "Entity ID"
                },
                "action": {
                    "type": "string",
                    "required": True,
                    "enum": ["approve", "reject", "request_changes"],
                    "description": "Approval action"
                },
                "comment": {
                    "type": "string",
                    "required": False,
                    "description": "Approval comment"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # SCHEDULED_JOB
    SCHEDULED_JOB: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="scheduled_job",
            name="Scheduled Job",
            description="Scheduled job với cron expression",
            expands_to=[
                "validate_input",
                "create_record",
                "publish_event",
            ],
            params_schema={
                "job_name": {
                    "type": "string",
                    "required": True,
                    "description": "Job name"
                },
                "cron_expression": {
                    "type": "string",
                    "required": True,
                    "description": "Cron expression"
                },
                "handler": {
                    "type": "string",
                    "required": True,
                    "description": "Job handler"
                },
                "enabled": {
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "description": "Job enabled"
                },
            },
            default_obligations=[
                "input_validation_required",
            ],
        )
    )
    
    # EVENT_SOURCING
    EVENT_SOURCING: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="event_sourcing",
            name="Event Sourcing",
            description="Event sourcing pattern với event stream",
            expands_to=[
                "authorize_permission",
                "load_entity",
                "validate_input",
                "begin_transaction",
                "create_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check"
                },
                "aggregate_type": {
                    "type": "string",
                    "required": True,
                    "description": "Aggregate type"
                },
                "aggregate_id": {
                    "type": "string",
                    "required": True,
                    "description": "Aggregate ID"
                },
                "event": {
                    "type": "object",
                    "required": True,
                    "description": "Event to apply"
                },
                "expected_version": {
                    "type": "integer",
                    "required": False,
                    "description": "Expected version for optimistic locking"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "immutable_evidence_required",
            ],
        )
    )


# ============================================================================
# Domain Macro Capabilities (12 macros)
# ============================================================================
# Các patterns cho domain-specific operations
# ============================================================================


@dataclass
class DomainMacroCapabilities:
    """
    Domain Macro Capabilities (12 macros).
    
    Các patterns cho domain-specific operations (Commerce, Banking, Healthcare).
    """
    
    # COMMERCE: CREATE_ORDER
    CREATE_ORDER: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="create_order",
            name="Create Order",
            description="Tạo đơn hàng mới với inventory check",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "load_entity",
                "create_record",
                "update_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "customer_id": {
                    "type": "string",
                    "required": True,
                    "description": "Customer ID"
                },
                "items": {
                    "type": "array",
                    "required": True,
                    "description": "Order items"
                },
                "shipping_address": {
                    "type": "object",
                    "required": True,
                    "description": "Shipping address"
                },
                "payment_method": {
                    "type": "string",
                    "required": True,
                    "description": "Payment method"
                },
            },
            default_obligations=[
                "permission_check_required",
                "tenant_filter_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # COMMERCE: UPDATE_INVENTORY
    UPDATE_INVENTORY: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="update_inventory",
            name="Update Inventory",
            description="Cập nhật inventory với validation",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "update_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "product_id": {
                    "type": "string",
                    "required": True,
                    "description": "Product ID"
                },
                "quantity_change": {
                    "type": "integer",
                    "required": True,
                    "description": "Quantity change"
                },
                "reason": {
                    "type": "string",
                    "required": True,
                    "enum": ["sale", "return", "adjustment", "damage"],
                    "description": "Reason for change"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # COMMERCE: PROCESS_PAYMENT
    PROCESS_PAYMENT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="process_payment",
            name="Process Payment",
            description="Xử lý payment với external service",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "call_external_service",
                "create_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "order_id": {
                    "type": "string",
                    "required": True,
                    "description": "Order ID"
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "description": "Payment amount"
                },
                "payment_method": {
                    "type": "string",
                    "required": True,
                    "description": "Payment method"
                },
                "currency": {
                    "type": "string",
                    "required": True,
                    "description": "Currency code"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
                "pci_dss_compliant",
            ],
        )
    )
    
    # BANKING: TRANSFER_FUNDS
    TRANSFER_FUNDS: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="transfer_funds",
            name="Transfer Funds",
            description="Chuyển tiền với double-entry bookkeeping",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "load_entity",
                "create_record",
                "update_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "from_account": {
                    "type": "string",
                    "required": True,
                    "description": "Source account ID"
                },
                "to_account": {
                    "type": "string",
                    "required": True,
                    "description": "Destination account ID"
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "description": "Transfer amount"
                },
                "currency": {
                    "type": "string",
                    "required": True,
                    "description": "Currency code"
                },
                "reference": {
                    "type": "string",
                    "required": False,
                    "description": "Transfer reference"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
                "double_entry_balanced",
                "kyc_verified",
            ],
        )
    )
    
    # BANKING: CREATE_LEDGER_ENTRY
    CREATE_LEDGER_ENTRY: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="create_ledger_entry",
            name="Create Ledger Entry",
            description="Tạo ledger entry với double-entry validation",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "create_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "account": {
                    "type": "string",
                    "required": True,
                    "description": "Account ID"
                },
                "type": {
                    "type": "string",
                    "required": True,
                    "enum": ["debit", "credit"],
                    "description": "Entry type"
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "description": "Entry amount"
                },
                "currency": {
                    "type": "string",
                    "required": True,
                    "description": "Currency code"
                },
                "reference": {
                    "type": "string",
                    "required": False,
                    "description": "Entry reference"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
                "double_entry_balanced",
            ],
        )
    )
    
    # HEALTHCARE: CREATE_PATIENT_RECORD
    CREATE_PATIENT_RECORD: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="create_patient_record",
            name="Create Patient Record",
            description="Tạo patient record với PHI encryption",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "create_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "patient_info": {
                    "type": "object",
                    "required": True,
                    "description": "Patient information"
                },
                "contact_info": {
                    "type": "object",
                    "required": False,
                    "description": "Contact information"
                },
                "insurance_info": {
                    "type": "object",
                    "required": False,
                    "description": "Insurance information"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
                "hipaa_encryption",
                "phi_access_logged",
            ],
        )
    )
    
    # HEALTHCARE: PRESCRIBE_MEDICATION
    PRESCRIBE_MEDICATION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="prescribe_medication",
            name="Prescribe Medication",
            description="Prescription với drug interaction check",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "create_record",
                "call_external_service",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "patient_id": {
                    "type": "string",
                    "required": True,
                    "description": "Patient ID"
                },
                "medication": {
                    "type": "string",
                    "required": True,
                    "description": "Medication name"
                },
                "dosage": {
                    "type": "string",
                    "required": True,
                    "description": "Dosage"
                },
                "frequency": {
                    "type": "string",
                    "required": True,
                    "description": "Frequency"
                },
                "duration": {
                    "type": "string",
                    "required": False,
                    "description": "Duration"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
                "hipaa_encryption",
            ],
        )
    )
    
    # HR: ONBOARD_EMPLOYEE
    ONBOARD_EMPLOYEE: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="onboard_employee",
            name="Onboard Employee",
            description="Employee onboarding với document collection",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "create_record",
                "publish_event",
                "send_notification",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "employee_info": {
                    "type": "string",
                    "required": True,
                    "description": "Employee information"
                },
                "position": {
                    "type": "string",
                    "required": True,
                    "description": "Position"
                },
                "department": {
                    "type": "string",
                    "required": True,
                    "description": "Department"
                },
                "start_date": {
                    "type": "string",
                    "required": True,
                    "description": "Start date"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # LOGISTICS: CREATE_SHIPMENT
    CREATE_SHIPMENT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="create_shipment",
            name="Create Shipment",
            description="Tạo shipment với tracking",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "create_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "order_id": {
                    "type": "string",
                    "required": True,
                    "description": "Order ID"
                },
                "carrier": {
                    "type": "string",
                    "required": True,
                    "description": "Carrier name"
                },
                "tracking_number": {
                    "type": "string",
                    "required": False,
                    "description": "Tracking number"
                },
                "shipping_address": {
                    "type": "object",
                    "required": True,
                    "description": "Shipping address"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # CONTENT: PUBLISH_CONTENT
    PUBLISH_CONTENT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="publish_content",
            name="Publish Content",
            description="Publish content với moderation",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "create_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "content_type": {
                    "type": "string",
                    "required": True,
                    "description": "Content type"
                },
                "title": {
                    "type": "string",
                    "required": True,
                    "description": "Content title"
                },
                "body": {
                    "type": "string",
                    "required": True,
                    "description": "Content body"
                },
                "tags": {
                    "type": "array",
                    "required": False,
                    "description": "Content tags"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # BOOKING: CREATE_BOOKING
    CREATE_BOOKING: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="create_booking",
            name="Create Booking",
            description="Tạo booking với availability check",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "create_record",
                "publish_event",
                "send_notification",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "resource_id": {
                    "type": "string",
                    "required": True,
                    "description": "Resource ID"
                },
                "customer_id": {
                    "type": "string",
                    "required": True,
                    "description": "Customer ID"
                },
                "start_time": {
                    "type": "string",
                    "required": True,
                    "description": "Start time"
                },
                "end_time": {
                    "type": "string",
                    "required": True,
                    "description": "End time"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # SUBSCRIPTION: CREATE_SUBSCRIPTION
    CREATE_SUBSCRIPTION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="create_subscription",
            name="Create Subscription",
            description="Tạo subscription với billing cycle",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "create_record",
                "publish_event",
                "send_notification",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "customer_id": {
                    "type": "string",
                    "required": True,
                    "description": "Customer ID"
                },
                "plan_id": {
                    "type": "string",
                    "required": True,
                    "description": "Plan ID"
                },
                "billing_cycle": {
                    "type": "string",
                    "required": True,
                    "enum": ["monthly", "yearly"],
                    "description": "Billing cycle"
                },
                "start_date": {
                    "type": "string",
                    "required": True,
                    "description": "Start date"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )


# ============================================================================
# Regulatory Macro Capabilities (10 macros)
# ============================================================================
# Các patterns cho regulatory compliance
# ============================================================================


@dataclass
class RegulatoryMacroCapabilities:
    """
    Regulatory Macro Capabilities (10 macros).
    
    Các patterns cho regulatory compliance (AML/KYC, Privacy, Audit).
    """
    
    # KYC_VERIFICATION
    KYC_VERIFICATION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="kyc_verification",
            name="KYC Verification",
            description="KYC verification với document validation",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "call_external_service",
                "begin_transaction",
                "create_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "customer_id": {
                    "type": "string",
                    "required": True,
                    "description": "Customer ID"
                },
                "document_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["passport", "id_card", "drivers_license"],
                    "description": "Document type"
                },
                "document_number": {
                    "type": "string",
                    "required": True,
                    "description": "Document number"
                },
                "expiry_date": {
                    "type": "string",
                    "required": True,
                    "description": "Document expiry date"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
                "kyc_verified",
                "immutable_evidence_required",
            ],
        )
    )
    
    # PII_ENCRYPTION
    PII_ENCRYPTION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="pii_encryption",
            name="PII Encryption",
            description="PII encryption với key management",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "call_external_service",
                "update_record",
                "write_audit_log",
            ],
            params_schema={
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "id": {
                    "type": "string",
                    "required": True,
                    "description": "Record ID"
                },
                "fields": {
                    "type": "array",
                    "required": True,
                    "description": "PII fields to encrypt"
                },
                "encryption_key_id": {
                    "type": "string",
                    "required": False,
                    "description": "Encryption key ID"
                },
            },
            default_obligations=[
                "permission_check_required",
                "audit_log_required",
                "encryption_required",
            ],
        )
    )
    
    # IMMUTABLE_AUDIT
    IMMUTABLE_AUDIT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="immutable_audit",
            name="Immutable Audit",
            description="Immutable audit log với cryptographic proof",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "create_record",
                "write_audit_log",
            ],
            params_schema={
                "action": {
                    "type": "string",
                    "required": True,
                    "description": "Action performed"
                },
                "entity": {
                    "type": "string",
                    "required": False,
                    "description": "Entity affected"
                },
                "entity_id": {
                    "type": "string",
                    "required": False,
                    "description": "Entity ID"
                },
                "actor": {
                    "type": "object",
                    "required": True,
                    "description": "Actor information"
                },
                "details": {
                    "type": "object",
                    "required": False,
                    "description": "Additional details"
                },
            },
            default_obligations=[
                "permission_check_required",
                "immutable_evidence_required",
                "audit_log_required",
            ],
        )
    )
    
    # DATA_RETENTION
    DATA_RETENTION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="data_retention",
            name="Data Retention",
            description="Data retention với automated archival",
            expands_to=[
                "authorize_permission",
                "query_records",
                "begin_transaction",
                "update_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "retention_days": {
                    "type": "integer",
                    "required": True,
                    "description": "Retention period in days"
                },
                "action": {
                    "type": "string",
                    "required": True,
                    "enum": ["archive", "anonymize", "delete"],
                    "description": "Retention action"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # SANCTIONS_SCREENING
    SANCTIONS_SCREENING: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="sanctions_screening",
            name="Sanctions Screening",
            description="Sanctions screening với external list",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "call_external_service",
                "create_record",
                "publish_event",
                "write_audit_log",
            ],
            params_schema={
                "customer_id": {
                    "type": "string",
                    "required": True,
                    "description": "Customer ID"
                },
                "screening_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["name", "pep", "adverse_media"],
                    "description": "Screening type"
                },
                "lists": {
                    "type": "array",
                    "required": False,
                    "description": "Sanctions lists to check"
                },
            },
            default_obligations=[
                "permission_check_required",
                "audit_log_required",
                "immutable_evidence_required",
            ],
        )
    )
    
    # GDPR_RIGHT_TO_ERASURE
    GDPR_RIGHT_TO_ERASURE: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="gdpr_right_to_erasure",
            name="GDPR Right to Erasure",
            description="GDPR right to erasure với comprehensive cleanup",
            expands_to=[
                "authorize_permission",
                "load_entity",
                "begin_transaction",
                "query_records",
                "delete_record",
                "write_audit_log",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "user_id": {
                    "type": "string",
                    "required": True,
                    "description": "User ID"
                },
                "reason": {
                    "type": "string",
                    "required": True,
                    "description": "Reason for erasure"
                },
                "entities": {
                    "type": "array",
                    "required": False,
                    "description": "Entities to erase from"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
                "immutable_evidence_required",
            ],
        )
    )
    
    # FINANCIAL_REPORTING
    FINANCIAL_REPORTING: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="financial_reporting",
            name="Financial Reporting",
            description="Financial reporting với audit trail",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "query_records",
                "create_record",
                "publish_event",
                "write_audit_log",
            ],
            params_schema={
                "report_type": {
                    "type": "string",
                    "required": True,
                    "description": "Report type"
                },
                "period_start": {
                    "type": "string",
                    "required": True,
                    "description": "Period start date"
                },
                "period_end": {
                    "type": "string",
                    "required": True,
                    "description": "Period end date"
                },
                "format": {
                    "type": "string",
                    "required": True,
                    "enum": ["pdf", "xlsx", "json"],
                    "description": "Report format"
                },
            },
            default_obligations=[
                "permission_check_required",
                "tenant_filter_required",
                "audit_log_required",
                "double_entry_balanced",
            ],
        )
    )
    
    # TAX_CALCULATION
    TAX_CALCULATION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="tax_calculation",
            name="Tax Calculation",
            description="Tax calculation với jurisdiction rules",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "call_external_service",
                "create_record",
                "write_audit_log",
            ],
            params_schema={
                "transaction_type": {
                    "type": "string",
                    "required": True,
                    "description": "Transaction type"
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "description": "Transaction amount"
                },
                "jurisdiction": {
                    "type": "string",
                    "required": True,
                    "description": "Tax jurisdiction"
                },
                "tax_categories": {
                    "type": "array",
                    "required": False,
                    "description": "Tax categories"
                },
            },
            default_obligations=[
                "permission_check_required",
                "audit_log_required",
            ],
        )
    )
    
    # ACCESS_LOGGING
    ACCESS_LOGGING: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="access_logging",
            name="Access Logging",
            description="Access logging cho sensitive data",
            expands_to=[
                "validate_input",
                "write_audit_log",
            ],
            params_schema={
                "access_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["read", "write", "delete", "export"],
                    "description": "Access type"
                },
                "data_type": {
                    "type": "string",
                    "required": True,
                    "description": "Data type accessed"
                },
                "actor": {
                    "type": "object",
                    "required": True,
                    "description": "Actor information"
                },
                "context": {
                    "type": "object",
                    "required": False,
                    "description": "Access context"
                },
            },
            default_obligations=[
                "audit_log_required",
                "immutable_evidence_required",
            ],
        )
    )
    
    # COMPLIANCE_CERTIFICATION
    COMPLIANCE_CERTIFICATION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="compliance_certification",
            name="Compliance Certification",
            description="Compliance certification với evidence collection",
            expands_to=[
                "authorize_permission",
                "query_records",
                "create_record",
                "publish_event",
                "write_audit_log",
            ],
            params_schema={
                "certification_type": {
                    "type": "string",
                    "required": True,
                    "description": "Certification type"
                },
                "entity_id": {
                    "type": "string",
                    "required": True,
                    "description": "Entity ID"
                },
                "evidence": {
                    "type": "array",
                    "required": True,
                    "description": "Evidence items"
                },
                "certifier_id": {
                    "type": "string",
                    "required": True,
                    "description": "Certifier ID"
                },
            },
            default_obligations=[
                "permission_check_required",
                "audit_log_required",
                "immutable_evidence_required",
            ],
        )
    )
    
    # DATA_EXPORT
    DATA_EXPORT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="data_export",
            name="Data Export",
            description="Data export với audit và compression",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "query_records",
                "write_audit_log",
                "publish_event",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check"
                },
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "format": {
                    "type": "string",
                    "required": True,
                    "enum": ["csv", "xlsx", "json", "parquet"],
                    "description": "Export format"
                },
                "filter": {
                    "type": "object",
                    "required": False,
                    "description": "Filter conditions"
                },
                "compress": {
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "description": "Compress output"
                },
            },
            default_obligations=[
                "permission_check_required",
                "tenant_filter_required",
                "audit_log_required",
            ],
        )
    )
    
    # NOTIFICATION_BATCH
    NOTIFICATION_BATCH: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="notification_batch",
            name="Notification Batch",
            description="Batch notification với multiple channels",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "query_records",
                "send_notification",
                "write_audit_log",
                "publish_event",
            ],
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission cần check"
                },
                "notification_type": {
                    "type": "string",
                    "required": True,
                    "description": "Notification type"
                },
                "template": {
                    "type": "string",
                    "required": True,
                    "description": "Notification template"
                },
                "recipients": {
                    "type": "array",
                    "required": True,
                    "description": "Recipient list"
                },
                "channels": {
                    "type": "array",
                    "required": False,
                    "description": "Channels to use"
                },
            },
            default_obligations=[
                "permission_check_required",
                "input_validation_required",
                "audit_log_required",
            ],
        )
    )


# ============================================================================
# Domain Macro Capabilities Extended Phase 4 (Layer 2 - Remaining Industries)
# ============================================================================
# Các macros còn thiếu cho 20 priority industries theo GAP analysis
# ============================================================================


@dataclass
class DomainMacroCapabilitiesPhase4:
    """
    Domain Macro Capabilities Phase 4 (46 macros cho remaining industries).
    
    Theo MACRO_CAPABILITIES_GAP.md, Phase 4 implement các macros còn thiếu:
    - Retail Banking: 8 macros
    - Last-mile Delivery: 5 macros
    - Omni-channel Retail: 6 macros
    - Omnichannel: 4 macros
    - Warehouse Management extended: 8 macros
    - Procurement SRM extended: 5 macros
    - CRM Platform extended: 3 macros
    - ERP Finance extended: 6 macros
    - ITSM Helpdesk extended: 2 macros
    - Payroll Benefits extended: 3 macros
    - Exchange Trading extended: 5 macros
    - Healthcare Hospital IS extended: 4 macros
    """
    
    # =========================================================================
    # RETAIL BANKING (8 macros)
    # =========================================================================
    
    # OPEN_ACCOUNT
    OPEN_ACCOUNT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="open_account",
            name="Open Account",
            description="Mở tài khoản ngân hàng với KYC verification",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "call_external_service",
                "begin_transaction",
                "create_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "customer_id": {
                    "type": "string",
                    "required": True,
                    "description": "Customer ID"
                },
                "account_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["checking", "savings", "money_market", "cd"],
                    "description": "Loại tài khoản"
                },
                "currency": {
                    "type": "string",
                    "required": True,
                    "description": "Currency code"
                },
                "initial_deposit": {
                    "type": "number",
                    "required": False,
                    "description": "Lược gửi ban đầu"
                },
                "kyc_verified": {
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "description": "Đã xác minh KYC"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
                "kyc_verified",
            ],
        )
    )
    
    # PROCESS_LOAN_APPLICATION
    PROCESS_LOAN_APPLICATION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="process_loan_application",
            name="Process Loan Application",
            description="Xử lý đơn vay với credit check và approval workflow",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "call_external_service",
                "begin_transaction",
                "create_record",
                "update_record",
                "send_notification",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "customer_id": {
                    "type": "string",
                    "required": True,
                    "description": "Customer ID"
                },
                "loan_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["personal", "auto", "mortgage", "business"],
                    "description": "Loại khoản vay"
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "description": "Số tiền vay"
                },
                "term_months": {
                    "type": "integer",
                    "required": True,
                    "description": "Thời hạn vay (tháng)"
                },
                "purpose": {
                    "type": "string",
                    "required": False,
                    "description": "Mục đích vay"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # DETECT_FRAUD
    DETECT_FRAUD: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="detect_fraud",
            name="Detect Fraud",
            description="Phát hiện gian lận transaction",
            expands_to=[
                "validate_input",
                "query_records",
                "call_external_service",
                "create_record",
                "publish_event",
                "write_audit_log",
            ],
            params_schema={
                "transaction_id": {
                    "type": "string",
                    "required": True,
                    "description": "Transaction ID"
                },
                "account_id": {
                    "type": "string",
                    "required": True,
                    "description": "Account ID"
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "description": "Transaction amount"
                },
                "risk_indicators": {
                    "type": "array",
                    "required": False,
                    "description": "Risk indicators"
                },
            },
            default_obligations=[
                "audit_log_required",
                "immutable_evidence_required",
            ],
        )
    )
    
    # GENERATE_STATEMENTS
    GENERATE_STATEMENTS: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="generate_statements",
            name="Generate Statements",
            description="Tạo sao kê tài khoản",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "query_records",
                "create_record",
                "publish_event",
                "write_audit_log",
            ],
            params_schema={
                "account_id": {
                    "type": "string",
                    "required": True,
                    "description": "Account ID"
                },
                "statement_period": {
                    "type": "object",
                    "required": True,
                    "description": "Statement period {start_date, end_date}"
                },
                "format": {
                    "type": "string",
                    "required": False,
                    "default": "pdf",
                    "enum": ["pdf", "json", "csv"],
                    "description": "Format của sao kê"
                },
            },
            default_obligations=[
                "permission_check_required",
                "tenant_filter_required",
                "audit_log_required",
            ],
        )
    )
    
    # PROCESS_WITHDRAWAL
    PROCESS_WITHDRAWAL: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="process_withdrawal",
            name="Process Withdrawal",
            description="Xử lý rút tiền với balance check",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "update_record",
                "create_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "account_id": {
                    "type": "string",
                    "required": True,
                    "description": "Account ID"
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "description": "Withdrawal amount"
                },
                "withdrawal_method": {
                    "type": "string",
                    "required": True,
                    "enum": ["atm", "transfer", "check", "cash"],
                    "description": "Phương thức rút tiền"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
                "double_entry_balanced",
            ],
        )
    )
    
    # PROCESS_DEPOSIT
    PROCESS_DEPOSIT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="process_deposit",
            name="Process Deposit",
            description="Xử lý gửi tiền với verification",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "update_record",
                "create_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "account_id": {
                    "type": "string",
                    "required": True,
                    "description": "Account ID"
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "description": "Deposit amount"
                },
                "deposit_method": {
                    "type": "string",
                    "required": True,
                    "enum": ["cash", "check", "transfer", "atm"],
                    "description": "Phương thức gửi tiền"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
                "double_entry_balanced",
            ],
        )
    )
    
    # FILE_SAR
    FILE_SAR: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="file_sar",
            name="File SAR (Suspicious Activity Report)",
            description="Gửi SAR cho regulatory compliance",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "create_record",
                "call_external_service",
                "publish_event",
                "write_audit_log",
            ],
            params_schema={
                "customer_id": {
                    "type": "string",
                    "required": True,
                    "description": "Customer ID"
                },
                "suspicious_activity_type": {
                    "type": "string",
                    "required": True,
                    "description": "Loại hoạt động đáng ngờ"
                },
                "narrative": {
                    "type": "string",
                    "required": True,
                    "description": "Mô tả hoạt động"
                },
                "amount_involved": {
                    "type": "number",
                    "required": False,
                    "description": "Số tiền liên quan"
                },
            },
            default_obligations=[
                "permission_check_required",
                "audit_log_required",
                "immutable_evidence_required",
            ],
        )
    )
    
    # MANAGE_COLLATERAL
    MANAGE_COLLATERAL: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="manage_collateral",
            name="Manage Collateral",
            description="Quản lý tài sản đảm bảo",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "create_record",
                "update_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "loan_id": {
                    "type": "string",
                    "required": True,
                    "description": "Loan ID"
                },
                "action": {
                    "type": "string",
                    "required": True,
                    "enum": ["add", "release", "liquidate", "revalue"],
                    "description": "Hành động quản lý"
                },
                "collateral_type": {
                    "type": "string",
                    "required": False,
                    "description": "Loại tài sản đảm bảo"
                },
                "value": {
                    "type": "number",
                    "required": False,
                    "description": "Giá trị tài sản"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # =========================================================================
    # LAST-MILE DELIVERY (5 macros)
    # =========================================================================
    
    # OPTIMIZE_DELIVERY_ROUTE
    OPTIMIZE_DELIVERY_ROUTE: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="optimize_delivery_route",
            name="Optimize Delivery Route",
            description="Tối ưu hóa route giao hàng",
            expands_to=[
                "validate_input",
                "query_records",
                "call_external_service",
                "create_record",
                "publish_event",
            ],
            params_schema={
                "deliveries": {
                    "type": "array",
                    "required": True,
                    "description": "List of deliveries to optimize"
                },
                "depot_id": {
                    "type": "string",
                    "required": True,
                    "description": "Depot/warehouse ID"
                },
                "constraints": {
                    "type": "object",
                    "required": False,
                    "description": "Delivery constraints"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # ASSIGN_DELIVERY_SLOT
    ASSIGN_DELIVERY_SLOT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="assign_delivery_slot",
            name="Assign Delivery Slot",
            description="Phân bổ slot giao hàng cho khách",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "query_records",
                "begin_transaction",
                "create_record",
                "send_notification",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "order_id": {
                    "type": "string",
                    "required": True,
                    "description": "Order ID"
                },
                "customer_id": {
                    "type": "string",
                    "required": True,
                    "description": "Customer ID"
                },
                "slot_time": {
                    "type": "string",
                    "required": True,
                    "description": "Delivery slot time"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
            ],
        )
    )
    
    # UPDATE_DELIVERY_STATUS
    UPDATE_DELIVERY_STATUS: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="update_delivery_status",
            name="Update Delivery Status",
            description="Cập nhật trạng thái giao hàng",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "update_record",
                "send_notification",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "delivery_id": {
                    "type": "string",
                    "required": True,
                    "description": "Delivery ID"
                },
                "status": {
                    "type": "string",
                    "required": True,
                    "enum": ["picked_up", "in_transit", "out_for_delivery", "delivered", "failed"],
                    "description": "Delivery status"
                },
                "location": {
                    "type": "object",
                    "required": False,
                    "description": "Current location"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # CALCULATE_DELIVERY_FARE
    CALCULATE_DELIVERY_FARE: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="calculate_delivery_fare",
            name="Calculate Delivery Fare",
            description="Tính phí giao hàng",
            expands_to=[
                "validate_input",
                "call_external_service",
                "create_record",
            ],
            params_schema={
                "origin": {
                    "type": "object",
                    "required": True,
                    "description": "Origin address"
                },
                "destination": {
                    "type": "object",
                    "required": True,
                    "description": "Destination address"
                },
                "package_details": {
                    "type": "object",
                    "required": False,
                    "description": "Package weight, dimensions"
                },
            },
            default_obligations=[
                "tenant_filter_required",
            ],
        )
    )
    
    # MANAGE_PROOF_OF_DELIVERY
    MANAGE_PROOF_OF_DELIVERY: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="manage_proof_of_delivery",
            name="Manage Proof of Delivery",
            description="Quản lý bằng chứng giao hàng (POD)",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "create_record",
                "update_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "delivery_id": {
                    "type": "string",
                    "required": True,
                    "description": "Delivery ID"
                },
                "pod_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["signature", "photo", "gps", "pin"],
                    "description": "POD type"
                },
                "pod_data": {
                    "type": "object",
                    "required": True,
                    "description": "POD data"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # =========================================================================
    # OMNI-CHANNEL RETAIL (6 macros)
    # =========================================================================
    
    # SYNC_INVENTORY
    SYNC_INVENTORY: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="sync_inventory",
            name="Sync Inventory",
            description="Đồng bộ inventory giữa channels",
            expands_to=[
                "authorize_permission",
                "query_records",
                "begin_transaction",
                "update_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "product_id": {
                    "type": "string",
                    "required": False,
                    "description": "Product ID (null = all products)"
                },
                "channels": {
                    "type": "array",
                    "required": True,
                    "description": "Channels to sync"
                },
                "sync_type": {
                    "type": "string",
                    "required": False,
                    "default": "full",
                    "enum": ["full", "delta"],
                    "description": "Sync type"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # RESERVE_STOCK
    RESERVE_STOCK: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="reserve_stock",
            name="Reserve Stock",
            description="Đặt hàng cho order",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "update_record",
                "create_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "order_id": {
                    "type": "string",
                    "required": True,
                    "description": "Order ID"
                },
                "items": {
                    "type": "array",
                    "required": True,
                    "description": "Items to reserve"
                },
                "reservation_duration": {
                    "type": "integer",
                    "required": False,
                    "default": 3600,
                    "description": "Reservation duration in seconds"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
            ],
        )
    )
    
    # PROCESS_BOPIS
    PROCESS_BOPIS: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="process_bopis",
            name="Process BOPIS (Buy Online Pick-up In Store)",
            description="Xử lý đơn hàng BOPIS",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "update_record",
                "create_record",
                "send_notification",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "order_id": {
                    "type": "string",
                    "required": True,
                    "description": "Order ID"
                },
                "store_id": {
                    "type": "string",
                    "required": True,
                    "description": "Store ID"
                },
                "action": {
                    "type": "string",
                    "required": True,
                    "enum": ["prepare", "ready", "pickup", "cancel"],
                    "description": "BOPIS action"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # MANAGE_CHANNEL_PRICING
    MANAGE_CHANNEL_PRICING: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="manage_channel_pricing",
            name="Manage Channel Pricing",
            description="Quản lý giá theo channel",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "update_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "product_id": {
                    "type": "string",
                    "required": True,
                    "description": "Product ID"
                },
                "channel_id": {
                    "type": "string",
                    "required": True,
                    "description": "Channel ID"
                },
                "price": {
                    "type": "number",
                    "required": True,
                    "description": "Channel price"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # PROCESS_SHIP_FROM_STORE
    PROCESS_SHIP_FROM_STORE: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="process_ship_from_store",
            name="Process Ship from Store",
            description="Xử lý ship từ cửa hàng",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "update_record",
                "create_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "order_id": {
                    "type": "string",
                    "required": True,
                    "description": "Order ID"
                },
                "store_id": {
                    "type": "string",
                    "required": True,
                    "description": "Store ID"
                },
                "shipping_method": {
                    "type": "string",
                    "required": True,
                    "description": "Shipping method"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # UNIFY_CUSTOMER_VIEW
    UNIFY_CUSTOMER_VIEW: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="unify_customer_view",
            name="Unify Customer View",
            description="Gộp customer view từ nhiều channels",
            expands_to=[
                "authorize_permission",
                "query_records",
                "create_record",
                "publish_event",
            ],
            params_schema={
                "customer_identifier": {
                    "type": "string",
                    "required": True,
                    "description": "Customer identifier (email/phone)"
                },
                "channels": {
                    "type": "array",
                    "required": False,
                    "description": "Channels to aggregate from"
                },
            },
            default_obligations=[
                "permission_check_required",
                "tenant_filter_required",
            ],
        )
    )
    
    # =========================================================================
    # OMNICHANNEL (4 macros)
    # =========================================================================
    
    # CONTINUE_SHOPPING
    CONTINUE_SHOPPING: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="continue_shopping",
            name="Continue Shopping",
            description="Tiếp tục shopping từ channel khác",
            expands_to=[
                "authorize_permission",
                "query_records",
                "load_entity",
                "update_record",
            ],
            params_schema={
                "session_id": {
                    "type": "string",
                    "required": True,
                    "description": "Shopping session ID"
                },
                "from_channel": {
                    "type": "string",
                    "required": True,
                    "description": "Source channel"
                },
                "to_channel": {
                    "type": "string",
                    "required": True,
                    "description": "Target channel"
                },
            },
            default_obligations=[
                "permission_check_required",
            ],
        )
    )
    
    # CROSS_CHANNEL_RETURN
    CROSS_CHANNEL_RETURN: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="cross_channel_return",
            name="Cross Channel Return",
            description="Trả hàng chéo channel",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "update_record",
                "create_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "order_id": {
                    "type": "string",
                    "required": True,
                    "description": "Order ID"
                },
                "purchase_channel": {
                    "type": "string",
                    "required": True,
                    "description": "Purchase channel"
                },
                "return_channel": {
                    "type": "string",
                    "required": True,
                    "description": "Return channel"
                },
                "return_reason": {
                    "type": "string",
                    "required": True,
                    "description": "Return reason"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # OMNICHANNEL_LOYALTY
    OMNICHANNEL_LOYALTY: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="omnichannel_loyalty",
            name="Omnichannel Loyalty",
            description="Quản lý loyalty points đa channel",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "update_record",
                "create_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "customer_id": {
                    "type": "string",
                    "required": True,
                    "description": "Customer ID"
                },
                "action": {
                    "type": "string",
                    "required": True,
                    "enum": ["earn", "redeem", "expire", "bonus"],
                    "description": "Loyalty action"
                },
                "points": {
                    "type": "integer",
                    "required": True,
                    "description": "Points amount"
                },
                "channel": {
                    "type": "string",
                    "required": True,
                    "description": "Transaction channel"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # PERSONALIZE_OMNICHANNEL
    PERSONALIZE_OMNICHANNEL: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="personalize_omnichannel",
            name="Personalize Omnichannel",
            description="Cá nhân hóa trải nghiệm đa channel",
            expands_to=[
                "authorize_permission",
                "query_records",
                "call_external_service",
                "create_record",
            ],
            params_schema={
                "customer_id": {
                    "type": "string",
                    "required": True,
                    "description": "Customer ID"
                },
                "channel": {
                    "type": "string",
                    "required": True,
                    "description": "Target channel"
                },
                "personalization_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["recommendations", "offers", "content", "layout"],
                    "description": "Personalization type"
                },
            },
            default_obligations=[
                "permission_check_required",
                "tenant_filter_required",
            ],
        )
    )
    
    # =========================================================================
    # WAREHOUSE MANAGEMENT EXTENDED (8 macros)
    # =========================================================================
    
    # FORECAST_DEMAND
    FORECAST_DEMAND: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="forecast_demand",
            name="Forecast Demand",
            description="Dự báo nhu cầu inventory",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "query_records",
                "call_external_service",
                "create_record",
                "publish_event",
            ],
            params_schema={
                "product_ids": {
                    "type": "array",
                    "required": False,
                    "description": "Product IDs to forecast"
                },
                "forecast_period": {
                    "type": "object",
                    "required": True,
                    "description": "Forecast period"
                },
                "model": {
                    "type": "string",
                    "required": False,
                    "default": "default",
                    "description": "Forecasting model"
                },
            },
            default_obligations=[
                "permission_check_required",
                "audit_log_required",
            ],
        )
    )
    
    # MANAGE_REPLENISHMENT
    MANAGE_REPLENISHMENT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="manage_replenishment",
            name="Manage Replenishment",
            description="Quản lý bổ sung hàng",
            expands_to=[
                "authorize_permission",
                "query_records",
                "create_record",
                "send_notification",
                "publish_event",
            ],
            params_schema={
                "product_id": {
                    "type": "string",
                    "required": True,
                    "description": "Product ID"
                },
                "current_qty": {
                    "type": "integer",
                    "required": True,
                    "description": "Current quantity"
                },
                "reorder_point": {
                    "type": "integer",
                    "required": True,
                    "description": "Reorder point"
                },
                "reorder_qty": {
                    "type": "integer",
                    "required": True,
                    "description": "Reorder quantity"
                },
            },
            default_obligations=[
                "permission_check_required",
                "audit_log_required",
            ],
        )
    )
    
    # TRACK_SHIPPING_LABEL
    TRACK_SHIPPING_LABEL: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="track_shipping_label",
            name="Track Shipping Label",
            description="Theo dõi shipping label",
            expands_to=[
                "validate_input",
                "call_external_service",
                "create_record",
                "update_record",
            ],
            params_schema={
                "label_id": {
                    "type": "string",
                    "required": True,
                    "description": "Shipping label ID"
                },
                "carrier": {
                    "type": "string",
                    "required": True,
                    "description": "Carrier name"
                },
            },
            default_obligations=[
                "tenant_filter_required",
            ],
        )
    )
    
    # PROCESS_INVENTORY_ADJUSTMENT
    PROCESS_INVENTORY_ADJUSTMENT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="process_inventory_adjustment",
            name="Process Inventory Adjustment",
            description="Xử lý điều chỉnh inventory",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "update_record",
                "create_record",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "product_id": {
                    "type": "string",
                    "required": True,
                    "description": "Product ID"
                },
                "adjustment_qty": {
                    "type": "integer",
                    "required": True,
                    "description": "Adjustment quantity"
                },
                "reason": {
                    "type": "string",
                    "required": True,
                    "enum": ["damage", "theft", "correction", "expiration"],
                    "description": "Adjustment reason"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # GENERATE_PICK_LIST
    GENERATE_PICK_LIST: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="generate_pick_list",
            name="Generate Pick List",
            description="Tạo pick list cho orders",
            expands_to=[
                "authorize_permission",
                "query_records",
                "create_record",
                "publish_event",
            ],
            params_schema={
                "order_ids": {
                    "type": "array",
                    "required": True,
                    "description": "Order IDs"
                },
                "warehouse_id": {
                    "type": "string",
                    "required": True,
                    "description": "Warehouse ID"
                },
                "optimize_route": {
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "description": "Optimize pick route"
                },
            },
            default_obligations=[
                "permission_check_required",
            ],
        )
    )
    
    # MANAGE_WAVE_PICKING
    MANAGE_WAVE_PICKING: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="manage_wave_picking",
            name="Manage Wave Picking",
            description="Quản lý wave picking",
            expands_to=[
                "authorize_permission",
                "query_records",
                "begin_transaction",
                "create_record",
                "update_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "wave_id": {
                    "type": "string",
                    "required": False,
                    "description": "Wave ID"
                },
                "orders": {
                    "type": "array",
                    "required": True,
                    "description": "Orders in wave"
                },
                "wave_status": {
                    "type": "string",
                    "required": True,
                    "enum": ["planned", "active", "completed", "cancelled"],
                    "description": "Wave status"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
            ],
        )
    )
    
    # TRACK_BIN_UTILIZATION
    TRACK_BIN_UTILIZATION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="track_bin_utilization",
            name="Track Bin Utilization",
            description="Theo dõi utilization của bins",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "query_records",
                "create_record",
                "publish_event",
            ],
            params_schema={
                "warehouse_id": {
                    "type": "string",
                    "required": True,
                    "description": "Warehouse ID"
                },
                "bin_ids": {
                    "type": "array",
                    "required": False,
                    "description": "Bin IDs (null = all bins)"
                },
                "metrics": {
                    "type": "array",
                    "required": False,
                    "description": "Metrics to track"
                },
            },
            default_obligations=[
                "permission_check_required",
                "audit_log_required",
            ],
        )
    )
    
    # PROCESS_PICK_RETURN
    PROCESS_PICK_RETURN: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="process_pick_return",
            name="Process Pick Return",
            description="Xử lý trả hàng pick",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "update_record",
                "create_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "return_id": {
                    "type": "string",
                    "required": True,
                    "description": "Return ID"
                },
                "items": {
                    "type": "array",
                    "required": True,
                    "description": "Items to return"
                },
                "return_reason": {
                    "type": "string",
                    "required": True,
                    "description": "Return reason"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # =========================================================================
    # PROCUREMENT SRM EXTENDED (5 macros)
    # =========================================================================
    
    # FORECAST_DEMAND_PROCUREMENT
    FORECAST_DEMAND_PROCUREMENT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="forecast_demand_procurement",
            name="Forecast Demand Procurement",
            description="Dự báo nhu cầu procurement",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "query_records",
                "call_external_service",
                "create_record",
                "publish_event",
            ],
            params_schema={
                "category": {
                    "type": "string",
                    "required": False,
                    "description": "Procurement category"
                },
                "forecast_period": {
                    "type": "object",
                    "required": True,
                    "description": "Forecast period"
                },
            },
            default_obligations=[
                "permission_check_required",
                "audit_log_required",
            ],
        )
    )
    
    # APPROVE_PURCHASE_ORDER
    APPROVE_PURCHASE_ORDER: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="approve_purchase_order",
            name="Approve Purchase Order",
            description="Duyệt purchase order",
            expands_to=[
                "authorize_permission",
                "load_entity",
                "validate_input",
                "update_record",
                "send_notification",
                "publish_event",
                "write_audit_log",
            ],
            params_schema={
                "po_id": {
                    "type": "string",
                    "required": True,
                    "description": "Purchase Order ID"
                },
                "action": {
                    "type": "string",
                    "required": True,
                    "enum": ["approve", "reject", "request_changes"],
                    "description": "Approval action"
                },
                "comment": {
                    "type": "string",
                    "required": False,
                    "description": "Approval comment"
                },
            },
            default_obligations=[
                "permission_check_required",
                "audit_log_required",
            ],
        )
    )
    
    # TRACK_PO_STATUS
    TRACK_PO_STATUS: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="track_po_status",
            name="Track PO Status",
            description="Theo dõi status PO",
            expands_to=[
                "authorize_permission",
                "load_entity",
                "call_external_service",
                "update_record",
                "publish_event",
            ],
            params_schema={
                "po_id": {
                    "type": "string",
                    "required": True,
                    "description": "Purchase Order ID"
                },
            },
            default_obligations=[
                "permission_check_required",
            ],
        )
    )
    
    # MANAGE_CONTRACT_COMPLIANCE
    MANAGE_CONTRACT_COMPLIANCE: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="manage_contract_compliance",
            name="Manage Contract Compliance",
            description="Quản lý compliance contract",
            expands_to=[
                "authorize_permission",
                "query_records",
                "create_record",
                "send_notification",
                "write_audit_log",
            ],
            params_schema={
                "contract_id": {
                    "type": "string",
                    "required": True,
                    "description": "Contract ID"
                },
                "compliance_type": {
                    "type": "string",
                    "required": True,
                    "description": "Compliance type"
                },
            },
            default_obligations=[
                "permission_check_required",
                "audit_log_required",
            ],
        )
    )
    
    # PERFORM_VENDOR_RISK_ASSESSMENT
    PERFORM_VENDOR_RISK_ASSESSMENT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="perform_vendor_risk_assessment",
            name="Perform Vendor Risk Assessment",
            description="Đánh giá rủi ro vendor",
            expands_to=[
                "authorize_permission",
                "query_records",
                "call_external_service",
                "create_record",
                "publish_event",
                "write_audit_log",
            ],
            params_schema={
                "vendor_id": {
                    "type": "string",
                    "required": True,
                    "description": "Vendor ID"
                },
                "assessment_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["financial", "operational", "security", "compliance"],
                    "description": "Assessment type"
                },
            },
            default_obligations=[
                "permission_check_required",
                "audit_log_required",
            ],
        )
    )
    
    # =========================================================================
    # CRM PLATFORM EXTENDED (3 macros)
    # =========================================================================
    
    # SCORE_LEAD
    SCORE_LEAD: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="score_lead",
            name="Score Lead",
            description="Điểm số lead",
            expands_to=[
                "validate_input",
                "load_entity",
                "call_external_service",
                "update_record",
                "publish_event",
            ],
            params_schema={
                "lead_id": {
                    "type": "string",
                    "required": True,
                    "description": "Lead ID"
                },
                "scoring_model": {
                    "type": "string",
                    "required": False,
                    "default": "default",
                    "description": "Scoring model"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # ASSIGN_TICKET
    ASSIGN_TICKET: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="assign_ticket",
            name="Assign Ticket",
            description="Phân công ticket",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "update_record",
                "send_notification",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "ticket_id": {
                    "type": "string",
                    "required": True,
                    "description": "Ticket ID"
                },
                "assignee_id": {
                    "type": "string",
                    "required": True,
                    "description": "Assignee ID"
                },
                "assignment_reason": {
                    "type": "string",
                    "required": False,
                    "description": "Assignment reason"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # MERGE_DUPLICATE_CONTACTS
    MERGE_DUPLICATE_CONTACTS: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="merge_duplicate_contacts",
            name="Merge Duplicate Contacts",
            description="Gộp duplicate contacts",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "query_records",
                "begin_transaction",
                "update_record",
                "delete_record",
                "write_audit_log",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "primary_contact_id": {
                    "type": "string",
                    "required": True,
                    "description": "Primary contact ID"
                },
                "duplicate_contact_ids": {
                    "type": "array",
                    "required": True,
                    "description": "Duplicate contact IDs"
                },
                "merge_strategy": {
                    "type": "string",
                    "required": False,
                    "default": "keep_newest",
                    "enum": ["keep_newest", "keep_oldest", "manual"],
                    "description": "Merge strategy"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # =========================================================================
    # ERP FINANCE EXTENDED (6 macros)
    # =========================================================================
    
    # PROCESS_PAYABLES
    PROCESS_PAYABLES: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="process_payables",
            name="Process Payables",
            description="Xử lý khoản phải trả",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "create_record",
                "update_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "vendor_id": {
                    "type": "string",
                    "required": True,
                    "description": "Vendor ID"
                },
                "invoice_id": {
                    "type": "string",
                    "required": True,
                    "description": "Invoice ID"
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "description": "Payment amount"
                },
                "payment_terms": {
                    "type": "string",
                    "required": False,
                    "description": "Payment terms"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "double_entry_balanced",
                "audit_log_required",
            ],
        )
    )
    
    # PROCESS_RECEIVABLES
    PROCESS_RECEIVABLES: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="process_receivables",
            name="Process Receivables",
            description="Xử lý khoản phải thu",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "create_record",
                "update_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "customer_id": {
                    "type": "string",
                    "required": True,
                    "description": "Customer ID"
                },
                "invoice_id": {
                    "type": "string",
                    "required": True,
                    "description": "Invoice ID"
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "description": "Payment amount"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "double_entry_balanced",
                "audit_log_required",
            ],
        )
    )
    
    # MANAGE_CASH_FLOW
    MANAGE_CASH_FLOW: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="manage_cash_flow",
            name="Manage Cash Flow",
            description="Quản lý cash flow",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "query_records",
                "create_record",
                "publish_event",
            ],
            params_schema={
                "period": {
                    "type": "object",
                    "required": True,
                    "description": "Cash flow period"
                },
                "forecast_days": {
                    "type": "integer",
                    "required": False,
                    "description": "Forecast days"
                },
            },
            default_obligations=[
                "permission_check_required",
                "audit_log_required",
            ],
        )
    )
    
    # GENERATE_TRIAL_BALANCE
    GENERATE_TRIAL_BALANCE: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="generate_trial_balance",
            name="Generate Trial Balance",
            description="Tạo bảng cân đối kế toán",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "query_records",
                "create_record",
                "publish_event",
            ],
            params_schema={
                "accounting_period": {
                    "type": "object",
                    "required": True,
                    "description": "Accounting period"
                },
                "chart_of_accounts": {
                    "type": "array",
                    "required": False,
                    "description": "Account IDs to include"
                },
            },
            default_obligations=[
                "permission_check_required",
                "double_entry_balanced",
                "audit_log_required",
            ],
        )
    )
    
    # PROCESS_INTERCOMPANY
    PROCESS_INTERCOMPANY: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="process_intercompany",
            name="Process Intercompany",
            description="Xử lý giao dịch liên công ty",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "create_record",
                "update_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "source_company_id": {
                    "type": "string",
                    "required": True,
                    "description": "Source company ID"
                },
                "target_company_id": {
                    "type": "string",
                    "required": True,
                    "description": "Target company ID"
                },
                "transaction_type": {
                    "type": "string",
                    "required": True,
                    "description": "Transaction type"
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "description": "Transaction amount"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "double_entry_balanced",
                "audit_log_required",
            ],
        )
    )
    
    # RUN_DEPRECIATION
    RUN_DEPRECIATION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="run_depreciation",
            name="Run Depreciation",
            description="Chạy tính khấu hao tài sản",
            expands_to=[
                "authorize_permission",
                "query_records",
                "begin_transaction",
                "create_record",
                "update_record",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "asset_ids": {
                    "type": "array",
                    "required": False,
                    "description": "Asset IDs (null = all assets)"
                },
                "depreciation_period": {
                    "type": "string",
                    "required": True,
                    "description": "Depreciation period"
                },
                "depreciation_method": {
                    "type": "string",
                    "required": False,
                    "default": "straight_line",
                    "description": "Depreciation method"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "double_entry_balanced",
                "audit_log_required",
            ],
        )
    )
    
    # =========================================================================
    # ITSM HELPDESK EXTENDED (2 macros)
    # =========================================================================
    
    # CREATE_CHANGE_REQUEST
    CREATE_CHANGE_REQUEST: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="create_change_request",
            name="Create Change Request",
            description="Tạo change request",
            expands_to=[
                "validate_input",
                "create_record",
                "send_notification",
                "publish_event",
            ],
            params_schema={
                "change_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["standard", "normal", "emergency"],
                    "description": "Change type"
                },
                "description": {
                    "type": "string",
                    "required": True,
                    "description": "Change description"
                },
                "scheduled_date": {
                    "type": "string",
                    "required": False,
                    "description": "Scheduled date"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # ESCALATE_INCIDENT
    ESCALATE_INCIDENT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="escalate_incident",
            name="Escalate Incident",
            description="Escalate incident",
            expands_to=[
                "authorize_permission",
                "load_entity",
                "begin_transaction",
                "update_record",
                "send_notification",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "incident_id": {
                    "type": "string",
                    "required": True,
                    "description": "Incident ID"
                },
                "escalation_level": {
                    "type": "integer",
                    "required": True,
                    "description": "Escalation level"
                },
                "escalation_reason": {
                    "type": "string",
                    "required": True,
                    "description": "Escalation reason"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "sla_breach_check",
            ],
        )
    )
    
    # =========================================================================
    # PAYROLL BENEFITS EXTENDED (3 macros)
    # =========================================================================
    
    # CALCULATE_PAYCHECK
    CALCULATE_PAYCHECK: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="calculate_paycheck",
            name="Calculate Paycheck",
            description="Tính toán paycheck",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "call_external_service",
                "create_record",
                "write_audit_log",
            ],
            params_schema={
                "employee_id": {
                    "type": "string",
                    "required": True,
                    "description": "Employee ID"
                },
                "pay_period": {
                    "type": "object",
                    "required": True,
                    "description": "Pay period"
                },
                "pay_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["regular", "overtime", "bonus", "commission"],
                    "description": "Pay type"
                },
            },
            default_obligations=[
                "permission_check_required",
                "tax_calculation_required",
                "audit_log_required",
            ],
        )
    )
    
    # PROCESS_DIRECT_DEPOSIT
    PROCESS_DIRECT_DEPOSIT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="process_direct_deposit",
            name="Process Direct Deposit",
            description="Xử lý direct deposit",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "create_record",
                "call_external_service",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "employee_id": {
                    "type": "string",
                    "required": True,
                    "description": "Employee ID"
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "description": "Deposit amount"
                },
                "account_id": {
                    "type": "string",
                    "required": True,
                    "description": "Bank account ID"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "pci_dss_compliant",
                "audit_log_required",
            ],
        )
    )
    
    # MANAGE_BENEFITS_ELECTION
    MANAGE_BENEFITS_ELECTION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="manage_benefits_election",
            name="Manage Benefits Election",
            description="Quản lý benefits election",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "create_record",
                "update_record",
                "send_notification",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "employee_id": {
                    "type": "string",
                    "required": True,
                    "description": "Employee ID"
                },
                "benefit_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["health", "dental", "vision", "401k", "life"],
                    "description": "Benefit type"
                },
                "election_action": {
                    "type": "string",
                    "required": True,
                    "enum": ["enroll", "change", "withdraw"],
                    "description": "Election action"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # =========================================================================
    # EXCHANGE TRADING EXTENDED (5 macros)
    # =========================================================================
    
    # MANAGE_ORDER_BOOK
    MANAGE_ORDER_BOOK: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="manage_order_book",
            name="Manage Order Book",
            description="Quản lý order book",
            expands_to=[
                "validate_input",
                "begin_transaction",
                "update_record",
                "create_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "symbol": {
                    "type": "string",
                    "required": True,
                    "description": "Trading symbol"
                },
                "order_id": {
                    "type": "string",
                    "required": False,
                    "description": "Order ID"
                },
                "action": {
                    "type": "string",
                    "required": True,
                    "enum": ["add", "remove", "modify"],
                    "description": "Order book action"
                },
            },
            default_obligations=[
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # CALCULATE_MARK_TO_MARKET
    CALCULATE_MARK_TO_MARKET: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="calculate_mark_to_market",
            name="Calculate Mark to Market",
            description="Tính mark-to-market",
            expands_to=[
                "authorize_permission",
                "query_records",
                "call_external_service",
                "update_record",
                "create_record",
                "publish_event",
            ],
            params_schema={
                "portfolio_id": {
                    "type": "string",
                    "required": True,
                    "description": "Portfolio ID"
                },
                "valuation_date": {
                    "type": "string",
                    "required": True,
                    "description": "Valuation date"
                },
            },
            default_obligations=[
                "permission_check_required",
                "audit_log_required",
            ],
        )
    )
    
    # PROCESS_TRADE_SETTLEMENT
    PROCESS_TRADE_SETTLEMENT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="process_trade_settlement",
            name="Process Trade Settlement",
            description="Xử lý settlement trade",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "create_record",
                "update_record",
                "call_external_service",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "trade_id": {
                    "type": "string",
                    "required": True,
                    "description": "Trade ID"
                },
                "settlement_date": {
                    "type": "string",
                    "required": True,
                    "description": "Settlement date"
                },
                "settlement_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["delivery_vs_payment", "free_delivery", "free_payment"],
                    "description": "Settlement type"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "double_entry_balanced",
                "audit_log_required",
            ],
        )
    )
    
    # GENERATE_REGULATORY_REPORT
    GENERATE_REGULATORY_REPORT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="generate_regulatory_report",
            name="Generate Regulatory Report",
            description="Tạo regulatory report",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "query_records",
                "create_record",
                "call_external_service",
                "write_audit_log",
            ],
            params_schema={
                "report_type": {
                    "type": "string",
                    "required": True,
                    "description": "Report type"
                },
                "reporting_period": {
                    "type": "object",
                    "required": True,
                    "description": "Reporting period"
                },
                "regulatory_body": {
                    "type": "string",
                    "required": True,
                    "description": "Regulatory body"
                },
            },
            default_obligations=[
                "permission_check_required",
                "audit_log_required",
                "immutable_evidence_required",
            ],
        )
    )
    
    # MONITOR_POSITION_LIMITS
    MONITOR_POSITION_LIMITS: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="monitor_position_limits",
            name="Monitor Position Limits",
            description="Giám sát position limits",
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "query_records",
                "create_record",
                "send_notification",
                "publish_event",
            ],
            params_schema={
                "trader_id": {
                    "type": "string",
                    "required": False,
                    "description": "Trader ID (null = all traders)"
                },
                "limit_types": {
                    "type": "array",
                    "required": False,
                    "description": "Limit types to check"
                },
            },
            default_obligations=[
                "permission_check_required",
                "audit_log_required",
            ],
        )
    )
    
    # =========================================================================
    # HEALTHCARE HOSPITAL IS EXTENDED (4 macros)
    # =========================================================================
    
    # SCHEDULE_APPOINTMENT
    SCHEDULE_APPOINTMENT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="schedule_appointment",
            name="Schedule Appointment",
            description="Đặt lịch hẹn",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "create_record",
                "send_notification",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "patient_id": {
                    "type": "string",
                    "required": True,
                    "description": "Patient ID"
                },
                "provider_id": {
                    "type": "string",
                    "required": True,
                    "description": "Provider ID"
                },
                "appointment_type": {
                    "type": "string",
                    "required": True,
                    "description": "Appointment type"
                },
                "scheduled_time": {
                    "type": "string",
                    "required": True,
                    "description": "Scheduled time"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "hipaa_encryption",
            ],
        )
    )
    
    # MANAGE_REFILL_PRESCRIPTION
    MANAGE_REFILL_PRESCRIPTION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="manage_refill_prescription",
            name="Manage Refill Prescription",
            description="Quản lý refill prescription",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "begin_transaction",
                "create_record",
                "update_record",
                "call_external_service",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "prescription_id": {
                    "type": "string",
                    "required": True,
                    "description": "Prescription ID"
                },
                "patient_id": {
                    "type": "string",
                    "required": True,
                    "description": "Patient ID"
                },
                "pharmacy_id": {
                    "type": "string",
                    "required": False,
                    "description": "Pharmacy ID"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "hipaa_encryption",
            ],
        )
    )
    
    # PROCESS_CLAIM
    PROCESS_CLAIM: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="process_claim",
            name="Process Claim",
            description="Xử lý claim bảo hiểm",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "create_record",
                "call_external_service",
                "publish_event",
                "write_audit_log",
                "commit_transaction",
            ],
            params_schema={
                "patient_id": {
                    "type": "string",
                    "required": True,
                    "description": "Patient ID"
                },
                "claim_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["medical", "pharmacy", "dental", "vision"],
                    "description": "Claim type"
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "description": "Claim amount"
                },
                "insurance_provider": {
                    "type": "string",
                    "required": True,
                    "description": "Insurance provider"
                },
            },
            default_obligations=[
                "permission_check_required",
                "transaction_required",
                "hipaa_encryption",
                "audit_log_required",
            ],
        )
    )
    
    # TRACK_EHR_ACCESS
    TRACK_EHR_ACCESS: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="track_ehr_access",
            name="Track EHR Access",
            description="Theo dõi truy cập EHR",
            expands_to=[
                "validate_input",
                "write_audit_log",
            ],
            params_schema={
                "access_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["view", "create", "update", "delete"],
                    "description": "Access type"
                },
                "record_id": {
                    "type": "string",
                    "required": True,
                    "description": "EHR record ID"
                },
                "user_id": {
                    "type": "string",
                    "required": True,
                    "description": "User ID"
                },
                "access_reason": {
                    "type": "string",
                    "required": False,
                    "description": "Access reason"
                },
            },
            default_obligations=[
                "audit_log_required",
                "immutable_evidence_required",
                "phi_access_logged",
            ],
        )
    )


# ============================================================================
# Domain Macro Capabilities Extended (Layer 2 - Priority Industries)
# ============================================================================
# Các macros cho 20 priority industries theo GAP analysis
# ============================================================================


@dataclass
class DomainMacroCapabilitiesExtended:
    """
    Domain Macro Capabilities Extended (50+ macros cho 20 priority industries).
    
    Layer 2 macros theo MACRO_CAPABILITIES_GAP.md:
    - Ecommerce D2C: 4 macros
    - Marketplace B2C: 5 macros
    - Marketplace B2B: 4 macros
    - Food Delivery: 4 macros
    - Warehouse Management: 5 macros
    - Procurement SRM: 5 macros
    - CRM Platform: 5 macros
    - ERP Finance: 5 macros
    - ITSM Helpdesk: 4 macros
    - Payroll Benefits: 4 macros
    - Healthcare Hospital IS: 4 macros
    - Exchange Trading: 4 macros
    """
    
    # =========================================================================
    # ECOMMERCE D2C (4 macros)
    # =========================================================================
    
    # APPLY_PROMOTION
    APPLY_PROMOTION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="apply_promotion",
            name="Apply Promotion",
            description="Áp dụng promotion/discount vào cart",
            expands_to=[
                "validate_input",
                "load_entity",
                "update_record",
                "publish_event",
            ],
            params_schema={
                "cart_id": {
                    "type": "string",
                    "required": True,
                    "description": "Cart ID"
                },
                "promotion_code": {
                    "type": "string",
                    "required": True,
                    "description": "Promotion code"
                },
                "user_id": {
                    "type": "string",
                    "required": False,
                    "description": "User ID (cho targeted promotions)"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # PROCESS_REFUND
    PROCESS_REFUND: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="process_refund",
            name="Process Refund",
            description="Xử lý refund cho order",
            expands_to=[
                "authorize_permission",
                "load_entity",
                "begin_transaction",
                "update_record",
                "call_external_service",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "order_id": {
                    "type": "string",
                    "required": True,
                    "description": "Order ID cần refund"
                },
                "refund_amount": {
                    "type": "number",
                    "required": True,
                    "description": "Số tiền refund"
                },
                "reason": {
                    "type": "string",
                    "required": True,
                    "description": "Lý do refund"
                },
                "refund_method": {
                    "type": "string",
                    "required": True,
                    "description": "Phương thức refund"
                },
            },
            default_obligations=[
                "transaction_required",
                "audit_log_required",
                "pci_dss_compliant",
            ],
        )
    )
    
    # MANAGE_SUBSCRIPTION
    MANAGE_SUBSCRIPTION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="manage_subscription",
            name="Manage Subscription",
            description="Quản lý subscription (activate, pause, cancel)",
            # Expand về core capabilities (state_machine_transition là macro, cần expand ra core)
            expands_to=[
                "authorize_permission",
                "load_entity",
                "validate_input",
                "update_record",
                "publish_event",
                "send_notification",
            ],
            params_schema={
                "subscription_id": {
                    "type": "string",
                    "required": True,
                    "description": "Subscription ID"
                },
                "action": {
                    "type": "string",
                    "required": True,
                    "enum": ["activate", "pause", "cancel", "resume"],
                    "description": "Hành động quản lý subscription"
                },
                "effective_date": {
                    "type": "string",
                    "required": False,
                    "description": "Ngày hiệu lực (ISO 8601)"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # RECOMMEND_PRODUCTS
    RECOMMEND_PRODUCTS: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="recommend_products",
            name="Recommend Products",
            description="Generate product recommendations",
            expands_to=[
                "query_records",
                "call_external_service",
                "create_record",
            ],
            params_schema={
                "user_id": {
                    "type": "string",
                    "required": False,
                    "description": "User ID (personalized recommendations)"
                },
                "context": {
                    "type": "object",
                    "required": False,
                    "description": "Context (current page, cart items, etc.)"
                },
                "limit": {
                    "type": "integer",
                    "required": False,
                    "default": 10,
                    "description": "Số lượng sản phẩm đề xuất"
                },
            },
            default_obligations=[
                "tenant_filter_required",
            ],
        )
    )
    
    # =========================================================================
    # MARKETPLACE B2C (5 macros)
    # =========================================================================
    
    # ONBOARD_SELLER
    ONBOARD_SELLER: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="onboard_seller",
            name="Onboard Seller",
            description="Seller onboarding với KYC",
            expands_to=[
                "validate_input",
                "call_external_service",
                "create_record",
                "publish_event",
            ],
            params_schema={
                "seller_info": {
                    "type": "object",
                    "required": True,
                    "description": "Thông tin seller"
                },
                "kyc_documents": {
                    "type": "array",
                    "required": True,
                    "description": "Tài liệu KYC"
                },
                "bank_account": {
                    "type": "object",
                    "required": True,
                    "description": "Thông tin tài khoản ngân hàng"
                },
            },
            default_obligations=[
                "kyc_verified",
                "audit_log_required",
            ],
        )
    )
    
    # HOLD_ESCROW_PAYMENT
    HOLD_ESCROW_PAYMENT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="hold_escrow_payment",
            name="Hold Escrow Payment",
            description="Giữ tiền trong escrow",
            expands_to=[
                "begin_transaction",
                "create_record",
                "update_record",
                "commit_transaction",
            ],
            params_schema={
                "order_id": {
                    "type": "string",
                    "required": True,
                    "description": "Order ID"
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "description": "Số tiền giữ"
                },
                "buyer_id": {
                    "type": "string",
                    "required": True,
                    "description": "Buyer ID"
                },
                "seller_id": {
                    "type": "string",
                    "required": True,
                    "description": "Seller ID"
                },
            },
            default_obligations=[
                "double_entry_balanced",
                "audit_log_required",
            ],
        )
    )
    
    # SPLIT_PAYMENT
    SPLIT_PAYMENT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="split_payment",
            name="Split Payment",
            description="Chia payment giữa seller/platform",
            expands_to=[
                "call_external_service",
                "create_record",
                "publish_event",
            ],
            params_schema={
                "payment_id": {
                    "type": "string",
                    "required": True,
                    "description": "Payment ID"
                },
                "seller_amount": {
                    "type": "number",
                    "required": True,
                    "description": "Số tiền cho seller"
                },
                "platform_commission": {
                    "type": "number",
                    "required": True,
                    "description": "Hoa hồng platform"
                },
            },
            default_obligations=[
                "double_entry_balanced",
                "pci_dss_compliant",
            ],
        )
    )
    
    # RESOLVE_DISPUTE
    RESOLVE_DISPUTE: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="resolve_dispute",
            name="Resolve Dispute",
            description="Giải quyết dispute buyer-seller",
            # approval_workflow đã expand về core
            expands_to=[
                "authorize_permission",
                "load_entity",
                "update_record",
                "send_notification",
                "write_audit_log",
            ],
            params_schema={
                "dispute_id": {
                    "type": "string",
                    "required": True,
                    "description": "Dispute ID"
                },
                "resolution": {
                    "type": "string",
                    "required": True,
                    "enum": ["refund_buyer", "release_to_seller", "partial_refund"],
                    "description": "Kết quả giải quyết"
                },
                "reason": {
                    "type": "string",
                    "required": True,
                    "description": "Lý do"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # RATE_REVIEW
    RATE_REVIEW: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="rate_review",
            name="Rate and Review",
            description="Đánh giá và review",
            expands_to=[
                "authorize_permission",
                "create_record",
                "publish_event",
            ],
            params_schema={
                "rateable_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["order", "product", "seller"],
                    "description": "Loại đối tượng đánh giá"
                },
                "rateable_id": {
                    "type": "string",
                    "required": True,
                    "description": "ID đối tượng đánh giá"
                },
                "rating": {
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "maximum": 5,
                    "description": "Điểm đánh giá (1-5)"
                },
                "comment": {
                    "type": "string",
                    "required": False,
                    "description": "Bình luận"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # =========================================================================
    # MARKETPLACE B2B (4 macros)
    # =========================================================================
    
    # CREATE_RFP
    CREATE_RFP: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="create_rfp",
            name="Create RFP",
            description="Tạo Request for Proposal",
            expands_to=[
                "authorize_permission",
                "create_record",
                "send_notification",
                "publish_event",
            ],
            params_schema={
                "title": {
                    "type": "string",
                    "required": True,
                    "description": "Tiêu đề RFP"
                },
                "description": {
                    "type": "string",
                    "required": True,
                    "description": "Mô tả yêu cầu"
                },
                "deadline": {
                    "type": "string",
                    "required": True,
                    "description": "Hạn nộp đề xuất"
                },
                "target_vendors": {
                    "type": "array",
                    "required": False,
                    "description": "Danh sách vendors mời"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # MANAGE_CREDIT_TERMS
    MANAGE_CREDIT_TERMS: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="manage_credit_terms",
            name="Manage Credit Terms",
            description="Quản lý credit terms cho buyer",
            expands_to=[
                "authorize_permission",
                "create_record",
                "update_record",
                "call_external_service",
            ],
            params_schema={
                "buyer_id": {
                    "type": "string",
                    "required": True,
                    "description": "Buyer ID"
                },
                "credit_limit": {
                    "type": "number",
                    "required": True,
                    "description": "Giới hạn tín dụng"
                },
                "payment_terms_days": {
                    "type": "integer",
                    "required": True,
                    "description": "Số ngày thanh toán"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # APPLY_BULK_PRICING
    APPLY_BULK_PRICING: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="apply_bulk_pricing",
            name="Apply Bulk Pricing",
            description="Áp dụng bulk pricing",
            expands_to=[
                "validate_input",
                "update_record",
                "publish_event",
            ],
            params_schema={
                "order_id": {
                    "type": "string",
                    "required": True,
                    "description": "Order ID"
                },
                "bulk_discount_tiers": {
                    "type": "array",
                    "required": True,
                    "description": "Các tier giảm giá theo số lượng"
                },
            },
            default_obligations=[
                "tenant_filter_required",
            ],
        )
    )
    
    # PROCESS_PURCHASE_ORDER
    PROCESS_PURCHASE_ORDER: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="process_purchase_order",
            name="Process Purchase Order",
            description="Xử lý PO từ buyer",
            expands_to=[
                "validate_input",
                "create_record",
                "call_external_service",
            ],
            params_schema={
                "po_number": {
                    "type": "string",
                    "required": True,
                    "description": "Số PO"
                },
                "buyer_id": {
                    "type": "string",
                    "required": True,
                    "description": "Buyer ID"
                },
                "line_items": {
                    "type": "array",
                    "required": True,
                    "description": "Danh sách mặt hàng"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # =========================================================================
    # FOOD DELIVERY (4 macros)
    # =========================================================================
    
    # ASSIGN_DELIVERY_DRIVER
    ASSIGN_DELIVERY_DRIVER: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="assign_delivery_driver",
            name="Assign Delivery Driver",
            description="Phân công driver cho order",
            expands_to=[
                "authorize_permission",
                "query_records",
                "update_record",
                "send_notification",
            ],
            params_schema={
                "order_id": {
                    "type": "string",
                    "required": True,
                    "description": "Order ID"
                },
                "driver_id": {
                    "type": "string",
                    "required": True,
                    "description": "Driver ID"
                },
                "pickup_location": {
                    "type": "object",
                    "required": True,
                    "description": "Vị trí nhận hàng"
                },
                "delivery_location": {
                    "type": "object",
                    "required": True,
                    "description": "Vị trí giao hàng"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # CALCULATE_DELIVERY_ROUTE
    CALCULATE_DELIVERY_ROUTE: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="calculate_delivery_route",
            name="Calculate Delivery Route",
            description="Tính toán delivery route tối ưu",
            expands_to=[
                "call_external_service",
                "update_record",
            ],
            params_schema={
                "orders": {
                    "type": "array",
                    "required": True,
                    "description": "Danh sách orders cần giao"
                },
                "driver_id": {
                    "type": "string",
                    "required": True,
                    "description": "Driver ID"
                },
            },
            default_obligations=[
                "tenant_filter_required",
            ],
        )
    )
    
    # TRACK_REALTIME_LOCATION
    TRACK_REALTIME_LOCATION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="track_realtime_location",
            name="Track Realtime Location",
            description="Track driver location realtime",
            expands_to=[
                "update_record",
                "publish_event",
                "create_record",
            ],
            params_schema={
                "driver_id": {
                    "type": "string",
                    "required": True,
                    "description": "Driver ID"
                },
                "latitude": {
                    "type": "number",
                    "required": True,
                    "description": "Vĩ độ"
                },
                "longitude": {
                    "type": "number",
                    "required": True,
                    "description": "Kinh độ"
                },
            },
            default_obligations=[
                "tenant_filter_required",
            ],
        )
    )
    
    # PROCESS_TIP
    PROCESS_TIP: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="process_tip",
            name="Process Tip",
            description="Xử lý tip cho driver",
            expands_to=[
                "create_record",
                "publish_event",
            ],
            params_schema={
                "order_id": {
                    "type": "string",
                    "required": True,
                    "description": "Order ID"
                },
                "driver_id": {
                    "type": "string",
                    "required": True,
                    "description": "Driver ID"
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "description": "Số tiền tip"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # =========================================================================
    # WAREHOUSE MANAGEMENT (5 macros)
    # =========================================================================
    
    # RECEIVE_INVENTORY
    RECEIVE_INVENTORY: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="receive_inventory",
            name="Receive Inventory",
            description="Nhận hàng vào kho",
            expands_to=[
                "validate_input",
                "begin_transaction",
                "update_record",
                "create_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "purchase_order_id": {
                    "type": "string",
                    "required": True,
                    "description": "Purchase Order ID"
                },
                "items": {
                    "type": "array",
                    "required": True,
                    "description": "Danh sách mặt hàng nhận"
                },
                "receiving_location": {
                    "type": "string",
                    "required": True,
                    "description": "Vị trí nhận hàng"
                },
            },
            default_obligations=[
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # PICK_PACK_SHIP
    PICK_PACK_SHIP: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="pick_pack_ship",
            name="Pick Pack Ship",
            description="Pick, pack, ship order",
            expands_to=[
                "authorize_permission",
                "begin_transaction",
                "update_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "order_id": {
                    "type": "string",
                    "required": True,
                    "description": "Order ID"
                },
                "shipping_method": {
                    "type": "string",
                    "required": True,
                    "description": "Phương thức vận chuyển"
                },
                "carrier": {
                    "type": "string",
                    "required": False,
                    "description": "Nhà vận chuyển"
                },
            },
            default_obligations=[
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # CYCLE_COUNT
    CYCLE_COUNT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="cycle_count",
            name="Cycle Count",
            description="Đếm hàng theo chu kỳ",
            expands_to=[
                "authorize_permission",
                "query_records",
                "update_record",
                "write_audit_log",
            ],
            params_schema={
                "location_id": {
                    "type": "string",
                    "required": True,
                    "description": "Vị trí kho"
                },
                "counted_quantities": {
                    "type": "array",
                    "required": True,
                    "description": "Kết quả đếm"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # BIN_TRANSFER
    BIN_TRANSFER: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="bin_transfer",
            name="Bin Transfer",
            description="Chuyển hàng giữa bins",
            expands_to=[
                "begin_transaction",
                "update_record",
                "commit_transaction",
            ],
            params_schema={
                "product_id": {
                    "type": "string",
                    "required": True,
                    "description": "Product ID"
                },
                "from_bin": {
                    "type": "string",
                    "required": True,
                    "description": "Bin nguồn"
                },
                "to_bin": {
                    "type": "string",
                    "required": True,
                    "description": "Bin đích"
                },
                "quantity": {
                    "type": "integer",
                    "required": True,
                    "description": "Số lượng chuyển"
                },
            },
            default_obligations=[
                "transaction_required",
                "audit_log_required",
            ],
        )
    )
    
    # MANAGE_BIN_LOCATION
    MANAGE_BIN_LOCATION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="manage_bin_location",
            name="Manage Bin Location",
            description="Quản lý bin locations",
            expands_to=[
                "create_record",
                "update_record",
                "delete_record",
            ],
            params_schema={
                "action": {
                    "type": "string",
                    "required": True,
                    "enum": ["create", "update", "deactivate"],
                    "description": "Hành động"
                },
                "bin_location": {
                    "type": "object",
                    "required": True,
                    "description": "Thông tin bin location"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # =========================================================================
    # PROCUREMENT SRM (5 macros)
    # =========================================================================
    
    # CREATE_RFQ
    CREATE_RFQ: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="create_rfq",
            name="Create RFQ",
            description="Tạo Request for Quotation",
            expands_to=[
                "authorize_permission",
                "create_record",
                "send_notification",
                "publish_event",
            ],
            params_schema={
                "title": {
                    "type": "string",
                    "required": True,
                    "description": "Tiêu đề RFQ"
                },
                "description": {
                    "type": "string",
                    "required": True,
                    "description": "Mô tả yêu cầu"
                },
                "target_vendors": {
                    "type": "array",
                    "required": True,
                    "description": "Danh sách vendors mời báo giá"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # EVALUATE_VENDOR
    EVALUATE_VENDOR: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="evaluate_vendor",
            name="Evaluate Vendor",
            description="Đánh giá vendor performance",
            # aggregate_query là macro, expand về core
            expands_to=[
                "enforce_tenant_scope",
                "query_records",
                "create_record",
                "publish_event",
            ],
            params_schema={
                "vendor_id": {
                    "type": "string",
                    "required": True,
                    "description": "Vendor ID"
                },
                "evaluation_period": {
                    "type": "object",
                    "required": True,
                    "description": "Thời kỳ đánh giá"
                },
                "metrics": {
                    "type": "array",
                    "required": True,
                    "description": "Các chỉ số đánh giá"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # MANAGE_CONTRACT
    MANAGE_CONTRACT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="manage_contract",
            name="Manage Contract",
            description="Quản lý vendor contract",
            expands_to=[
                "authorize_permission",
                "create_record",
                "update_record",
                "send_notification",
            ],
            params_schema={
                "vendor_id": {
                    "type": "string",
                    "required": True,
                    "description": "Vendor ID"
                },
                "contract_terms": {
                    "type": "object",
                    "required": True,
                    "description": "Điều khoản hợp đồng"
                },
                "action": {
                    "type": "string",
                    "required": True,
                    "enum": ["create", "renew", "terminate"],
                    "description": "Hành động"
                },
            },
            default_obligations=[
                "audit_log_required",
                "immutable_evidence_required",
            ],
        )
    )
    
    # SPEND_ANALYSIS
    SPEND_ANALYSIS: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="spend_analysis",
            name="Spend Analysis",
            description="Phân tích spend",
            # aggregate_query và export_query là macros, expand về core
            expands_to=[
                "enforce_tenant_scope",
                "query_records",
                "write_audit_log",
            ],
            params_schema={
                "time_period": {
                    "type": "object",
                    "required": True,
                    "description": "Thời kỳ phân tích"
                },
                "categories": {
                    "type": "array",
                    "required": False,
                    "description": "Các danh mục"
                },
            },
            default_obligations=[
                "tenant_filter_required",
            ],
        )
    )
    
    # SUPPLIER_ONBOARDING
    SUPPLIER_ONBOARDING: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="supplier_onboarding",
            name="Supplier Onboarding",
            description="Onboarding supplier mới",
            expands_to=[
                "validate_input",
                "create_record",
                "send_notification",
            ],
            params_schema={
                "supplier_info": {
                    "type": "object",
                    "required": True,
                    "description": "Thông tin supplier"
                },
                "documents": {
                    "type": "array",
                    "required": True,
                    "description": "Tài liệu"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # =========================================================================
    # CRM PLATFORM (5 macros)
    # =========================================================================
    
    # CREATE_LEAD
    CREATE_LEAD: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="create_lead",
            name="Create Lead",
            description="Tạo lead mới",
            expands_to=[
                "validate_input",
                "create_record",
                "publish_event",
                "send_notification",
            ],
            params_schema={
                "lead_info": {
                    "type": "object",
                    "required": True,
                    "description": "Thông tin lead"
                },
                "source": {
                    "type": "string",
                    "required": True,
                    "description": "Nguồn lead"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # CONVERT_OPPORTUNITY
    CONVERT_OPPORTUNITY: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="convert_opportunity",
            name="Convert Opportunity",
            description="Convert lead → opportunity",
            expands_to=[
                "authorize_permission",
                "create_record",
                "publish_event",
            ],
            params_schema={
                "lead_id": {
                    "type": "string",
                    "required": True,
                    "description": "Lead ID"
                },
                "opportunity_info": {
                    "type": "object",
                    "required": True,
                    "description": "Thông tin opportunity"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # LOG_ACTIVITY
    LOG_ACTIVITY: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="log_activity",
            name="Log Activity",
            description="Log activity (call, email, meeting)",
            expands_to=[
                "create_record",
                "publish_event",
            ],
            params_schema={
                "activity_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["call", "email", "meeting", "task"],
                    "description": "Loại hoạt động"
                },
                "related_to": {
                    "type": "object",
                    "required": True,
                    "description": "Đối tượng liên quan"
                },
                "notes": {
                    "type": "string",
                    "required": False,
                    "description": "Ghi chú"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # RUN_CAMPAIGN
    RUN_CAMPAIGN: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="run_campaign",
            name="Run Campaign",
            description="Chạy marketing campaign",
            expands_to=[
                "authorize_permission",
                "create_record",
                "send_notification",
                "publish_event",
            ],
            params_schema={
                "campaign_name": {
                    "type": "string",
                    "required": True,
                    "description": "Tên campaign"
                },
                "target_audience": {
                    "type": "array",
                    "required": True,
                    "description": "Đối tượng mục tiêu"
                },
                "message_template": {
                    "type": "string",
                    "required": True,
                    "description": "Template thông điệp"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # CASE_ESCALATION
    CASE_ESCALATION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="case_escalation",
            name="Case Escalation",
            description="Escalate support case",
            expands_to=[
                "update_record",
                "send_notification",
            ],
            params_schema={
                "case_id": {
                    "type": "string",
                    "required": True,
                    "description": "Case ID"
                },
                "escalation_level": {
                    "type": "string",
                    "required": True,
                    "enum": ["level1", "level2", "level3", "manager"],
                    "description": "Mức độ escalate"
                },
                "reason": {
                    "type": "string",
                    "required": True,
                    "description": "Lý do escalate"
                },
            },
            default_obligations=[
                "audit_log_required",
                "sla_breach_check",
            ],
        )
    )
    
    # =========================================================================
    # ERP FINANCE (5 macros)
    # =========================================================================
    
    # POST_JOURNAL_ENTRY
    POST_JOURNAL_ENTRY: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="post_journal_entry",
            name="Post Journal Entry",
            description="Post journal entry vào GL",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "begin_transaction",
                "create_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "journal_lines": {
                    "type": "array",
                    "required": True,
                    "description": "Dòng journal"
                },
                "posting_date": {
                    "type": "string",
                    "required": True,
                    "description": "Ngày post"
                },
                "reference": {
                    "type": "string",
                    "required": False,
                    "description": "Tham chiếu"
                },
            },
            default_obligations=[
                "transaction_required",
                "double_entry_balanced",
                "audit_log_required",
            ],
        )
    )
    
    # RECONCILE_ACCOUNTS
    RECONCILE_ACCOUNTS: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="reconcile_accounts",
            name="Reconcile Accounts",
            description="Reconcile accounts",
            expands_to=[
                "authorize_permission",
                "query_records",
                "update_record",
                "write_audit_log",
            ],
            params_schema={
                "account_id": {
                    "type": "string",
                    "required": True,
                    "description": "Account ID"
                },
                "reconciliation_date": {
                    "type": "string",
                    "required": True,
                    "description": "Ngày reconcile"
                },
                "matching_entries": {
                    "type": "array",
                    "required": True,
                    "description": "Các mục đã khớp"
                },
            },
            default_obligations=[
                "audit_log_required",
                "double_entry_balanced",
            ],
        )
    )
    
    # CLOSE_PERIOD
    CLOSE_PERIOD: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="close_period",
            name="Close Period",
            description="Close accounting period",
            # aggregate_query là macro, expand về core
            expands_to=[
                "authorize_permission",
                "enforce_tenant_scope",
                "query_records",
                "publish_event",
            ],
            params_schema={
                "period_id": {
                    "type": "string",
                    "required": True,
                    "description": "Period ID"
                },
                "close_date": {
                    "type": "string",
                    "required": True,
                    "description": "Ngày đóng kỳ"
                },
                "closing_user": {
                    "type": "string",
                    "required": True,
                    "description": "Người đóng kỳ"
                },
            },
            default_obligations=[
                "audit_log_required",
                "immutable_evidence_required",
            ],
        )
    )
    
    # CONSOLIDATE_ENTITIES
    CONSOLIDATE_ENTITIES: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="consolidate_entities",
            name="Consolidate Entities",
            description="Consolidate financial entities",
            # aggregate_query là macro, expand về core
            expands_to=[
                "enforce_tenant_scope",
                "query_records",
                "create_record",
            ],
            params_schema={
                "entity_ids": {
                    "type": "array",
                    "required": True,
                    "description": "Danh sách entities"
                },
                "consolidation_date": {
                    "type": "string",
                    "required": True,
                    "description": "Ngày consolidate"
                },
            },
            default_obligations=[
                "double_entry_balanced",
                "audit_log_required",
            ],
        )
    )
    
    # FIXED_ASSET_CAPITALIZATION
    FIXED_ASSET_CAPITALIZATION: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="fixed_asset_capitalization",
            name="Fixed Asset Capitalization",
            description="Capitalize fixed asset",
            # create_ledger_entry là macro, expand về core
            expands_to=[
                "validate_input",
                "begin_transaction",
                "create_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "asset_info": {
                    "type": "object",
                    "required": True,
                    "description": "Thông tin tài sản"
                },
                "cost": {
                    "type": "number",
                    "required": True,
                    "description": "Chi phí"
                },
                "useful_life_years": {
                    "type": "integer",
                    "required": True,
                    "description": "Thời gian hữu ích (năm)"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # =========================================================================
    # ITSM HELPDESK (4 macros)
    # =========================================================================
    
    # CREATE_TICKET
    CREATE_TICKET: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="create_ticket",
            name="Create Ticket",
            description="Tạo ticket mới",
            expands_to=[
                "validate_input",
                "create_record",
                "send_notification",
                "publish_event",
            ],
            params_schema={
                "subject": {
                    "type": "string",
                    "required": True,
                    "description": "Chủ đề"
                },
                "description": {
                    "type": "string",
                    "required": True,
                    "description": "Mô tả"
                },
                "priority": {
                    "type": "string",
                    "required": True,
                    "enum": ["low", "medium", "high", "critical"],
                    "description": "Mức độ ưu tiên"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # APPROVE_CHANGE
    APPROVE_CHANGE: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="approve_change",
            name="Approve Change",
            description="Approve change request",
            expands_to=[
                "authorize_permission",
                "update_record",
                "send_notification",
            ],
            params_schema={
                "change_request_id": {
                    "type": "string",
                    "required": True,
                    "description": "Change Request ID"
                },
                "decision": {
                    "type": "string",
                    "required": True,
                    "enum": ["approve", "reject", "modify"],
                    "description": "Quyết định"
                },
                "comments": {
                    "type": "string",
                    "required": False,
                    "description": "Bình luận"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # PUBLISH_KB_ARTICLE
    PUBLISH_KB_ARTICLE: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="publish_kb_article",
            name="Publish KB Article",
            description="Publish knowledge base article",
            expands_to=[
                "authorize_permission",
                "create_record",
                "publish_event",
            ],
            params_schema={
                "title": {
                    "type": "string",
                    "required": True,
                    "description": "Tiêu đề"
                },
                "content": {
                    "type": "string",
                    "required": True,
                    "description": "Nội dung"
                },
                "category": {
                    "type": "string",
                    "required": True,
                    "description": "Danh mục"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # ESCALATE_TICKET
    ESCALATE_TICKET: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="escalate_ticket",
            name="Escalate Ticket",
            description="Escalate ticket đến manager",
            expands_to=[
                "update_record",
                "send_notification",
                "write_audit_log",
            ],
            params_schema={
                "ticket_id": {
                    "type": "string",
                    "required": True,
                    "description": "Ticket ID"
                },
                "escalation_reason": {
                    "type": "string",
                    "required": True,
                    "description": "Lý do escalate"
                },
            },
            default_obligations=[
                "audit_log_required",
                "sla_breach_check",
            ],
        )
    )
    
    # =========================================================================
    # PAYROLL BENEFITS (4 macros)
    # =========================================================================
    
    # PROCESS_PAYROLL_RUN
    PROCESS_PAYROLL_RUN: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="process_payroll_run",
            name="Process Payroll Run",
            description="Chạy payroll run",
            expands_to=[
                "authorize_permission",
                "begin_transaction",
                "create_record",
                "call_external_service",
                "send_notification",
                "commit_transaction",
            ],
            params_schema={
                "payroll_period": {
                    "type": "object",
                    "required": True,
                    "description": "Kỳ payroll"
                },
                "employees": {
                    "type": "array",
                    "required": True,
                    "description": "Danh sách nhân viên"
                },
            },
            default_obligations=[
                "transaction_required",
                "audit_log_required",
                "tax_calculation_required",
            ],
        )
    )
    
    # FILE_TAX_RETURNS
    FILE_TAX_RETURNS: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="file_tax_returns",
            name="File Tax Returns",
            description="File tax returns",
            expands_to=[
                "authorize_permission",
                "call_external_service",
                "create_record",
                "write_audit_log",
            ],
            params_schema={
                "tax_period": {
                    "type": "object",
                    "required": True,
                    "description": "Kỳ thuế"
                },
                "return_data": {
                    "type": "object",
                    "required": True,
                    "description": "Dữ liệu thuế"
                },
            },
            default_obligations=[
                "audit_log_required",
                "immutable_evidence_required",
            ],
        )
    )
    
    # ENROLL_BENEFITS
    ENROLL_BENEFITS: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="enroll_benefits",
            name="Enroll Benefits",
            description="Enroll employee vào benefits",
            expands_to=[
                "validate_input",
                "create_record",
                "send_notification",
                "publish_event",
            ],
            params_schema={
                "employee_id": {
                    "type": "string",
                    "required": True,
                    "description": "Employee ID"
                },
                "benefit_plan_id": {
                    "type": "string",
                    "required": True,
                    "description": "Benefit Plan ID"
                },
                "effective_date": {
                    "type": "string",
                    "required": True,
                    "description": "Ngày hiệu lực"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # PROCESS_GARNISHMENT
    PROCESS_GARNISHMENT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="process_garnishment",
            name="Process Garnishment",
            description="Xử lý wage garnishment",
            expands_to=[
                "authorize_permission",
                "create_record",
                "update_record",
                "write_audit_log",
            ],
            params_schema={
                "employee_id": {
                    "type": "string",
                    "required": True,
                    "description": "Employee ID"
                },
                "garnishment_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["child_support", "tax", "creditor", "student_loan"],
                    "description": "Loại garnishment"
                },
                "amount_percentage": {
                    "type": "number",
                    "required": True,
                    "description": "Phần trăm khấu trừ"
                },
            },
            default_obligations=[
                "audit_log_required",
                "immutable_evidence_required",
            ],
        )
    )
    
    # =========================================================================
    # EXCHANGE TRADING (4 macros)
    # =========================================================================
    
    # MATCH_ORDERS
    MATCH_ORDERS: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="match_orders",
            name="Match Orders",
            description="Match buy/sell orders",
            expands_to=[
                "validate_input",
                "begin_transaction",
                "create_record",
                "update_record",
                "publish_event",
                "commit_transaction",
            ],
            params_schema={
                "order_book_id": {
                    "type": "string",
                    "required": True,
                    "description": "Order Book ID"
                },
                "buy_orders": {
                    "type": "array",
                    "required": True,
                    "description": "Danh sách buy orders"
                },
                "sell_orders": {
                    "type": "array",
                    "required": True,
                    "description": "Danh sách sell orders"
                },
            },
            default_obligations=[
                "transaction_required",
                "double_entry_balanced",
                "audit_log_required",
            ],
        )
    )
    
    # CLEAR_SETTLEMENT
    CLEAR_SETTLEMENT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="clear_settlement",
            name="Clear Settlement",
            description="Clear và settlement trade",
            expands_to=[
                "begin_transaction",
                "create_record",
                "update_record",
                "commit_transaction",
            ],
            params_schema={
                "trade_id": {
                    "type": "string",
                    "required": True,
                    "description": "Trade ID"
                },
                "settlement_date": {
                    "type": "string",
                    "required": True,
                    "description": "Ngày settlement"
                },
                "buyer_account": {
                    "type": "string",
                    "required": True,
                    "description": "Tài khoản người mua"
                },
                "seller_account": {
                    "type": "string",
                    "required": True,
                    "description": "Tài khoản người bán"
                },
            },
            default_obligations=[
                "double_entry_balanced",
                "audit_log_required",
            ],
        )
    )
    
    # CALCULATE_MARGIN
    CALCULATE_MARGIN: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="calculate_margin",
            name="Calculate Margin",
            description="Tính toán margin requirement",
            # aggregate_query là macro, expand về core
            expands_to=[
                "enforce_tenant_scope",
                "query_records",
                "update_record",
                "publish_event",
            ],
            params_schema={
                "account_id": {
                    "type": "string",
                    "required": True,
                    "description": "Account ID"
                },
                "positions": {
                    "type": "array",
                    "required": True,
                    "description": "Danh sách positions"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )
    
    # SURVEILLANCE_CHECK
    SURVEILLANCE_CHECK: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="surveillance_check",
            name="Surveillance Check",
            description="Kiểm tra market manipulation",
            # aggregate_query là macro, expand về core
            expands_to=[
                "enforce_tenant_scope",
                "query_records",
                "create_record",
                "write_audit_log",
            ],
            params_schema={
                "check_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["wash_trade", "spoofing", "layering", "front_running"],
                    "description": "Loại kiểm tra"
                },
                "time_window": {
                    "type": "object",
                    "required": True,
                    "description": "Cửa sổ thời gian"
                },
                "thresholds": {
                    "type": "object",
                    "required": True,
                    "description": "Ngưỡng kiểm tra"
                },
            },
            default_obligations=[
                "audit_log_required",
                "immutable_evidence_required",
            ],
        )
    )
    
    # =========================================================================
    # HEALTHCARE HOSPITAL IS (4 macros)
    # =========================================================================
    
    # ADMIT_PATIENT
    ADMIT_PATIENT: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="admit_patient",
            name="Admit Patient",
            description="Admit patient vào bệnh viện",
            # Expand về core capabilities (state_machine_transition là macro, cần expand ra core)
            expands_to=[
                "authorize_permission",
                "validate_input",
                "load_entity",
                "create_record",
                "update_record",
                "publish_event",
                "send_notification",
            ],
            params_schema={
                "patient_id": {
                    "type": "string",
                    "required": True,
                    "description": "Patient ID"
                },
                "admitting_department": {
                    "type": "string",
                    "required": True,
                    "description": "Khoa tiếp nhận"
                },
                "admission_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["emergency", "elective", "transfer"],
                    "description": "Loại nhập viện"
                },
                "attending_physician": {
                    "type": "string",
                    "required": True,
                    "description": "Bác sĩ điều trị"
                },
                "bed_id": {
                    "type": "string",
                    "required": False,
                    "description": "Bed ID (nếu có)"
                },
            },
            default_obligations=[
                "audit_log_required",
                "hipaa_encryption",
            ],
        )
    )
    
    # ENTER_MEDICAL_ORDER
    ENTER_MEDICAL_ORDER: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="enter_medical_order",
            name="Enter Medical Order",
            description="Nhập medical order",
            expands_to=[
                "authorize_permission",
                "validate_input",
                "create_record",
                "call_external_service",
                "publish_event",
            ],
            params_schema={
                "patient_id": {
                    "type": "string",
                    "required": True,
                    "description": "Patient ID"
                },
                "order_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["medication", "lab", "radiology", "procedure", "consult"],
                    "description": "Loại order"
                },
                "order_details": {
                    "type": "object",
                    "required": True,
                    "description": "Chi tiết order"
                },
                "ordering_provider": {
                    "type": "string",
                    "required": True,
                    "description": "Nhà cung cấp đơn hàng"
                },
                "priority": {
                    "type": "string",
                    "required": False,
                    "default": "routine",
                    "enum": ["stat", "urgent", "routine", "preferring"],
                    "description": "Mức độ ưu tiên"
                },
            },
            default_obligations=[
                "audit_log_required",
                "hipaa_encryption",
            ],
        )
    )
    
    # DOCUMENT_CLINICAL_NOTE
    DOCUMENT_CLINICAL_NOTE: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="document_clinical_note",
            name="Document Clinical Note",
            description="Ghi clinical note",
            expands_to=[
                "authorize_permission",
                "create_record",
                "write_audit_log",
            ],
            params_schema={
                "patient_id": {
                    "type": "string",
                    "required": True,
                    "description": "Patient ID"
                },
                "note_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["progress", "consultation", "discharge", "operating_room", "nursing"],
                    "description": "Loại ghi chú"
                },
                "content": {
                    "type": "string",
                    "required": True,
                    "description": "Nội dung ghi chú"
                },
                "author": {
                    "type": "string",
                    "required": True,
                    "description": "Tác giả"
                },
                "encounter_id": {
                    "type": "string",
                    "required": False,
                    "description": "Encounter ID (nếu có)"
                },
            },
            default_obligations=[
                "audit_log_required",
                "hipaa_encryption",
                "phi_access_logged",
            ],
        )
    )
    
    # MANAGE_BED
    MANAGE_BED: MacroCapability = field(
        default_factory=lambda: MacroCapability(
            id="manage_bed",
            name="Manage Bed",
            description="Quản lý bed assignment",
            # Expand về core capabilities (state_machine_transition là macro, cần expand ra core)
            expands_to=[
                "load_entity",
                "validate_input",
                "update_record",
                "publish_event",
            ],
            params_schema={
                "bed_id": {
                    "type": "string",
                    "required": True,
                    "description": "Bed ID"
                },
                "action": {
                    "type": "string",
                    "required": True,
                    "enum": ["assign", "release", "clean", "maintenance"],
                    "description": "Hành động quản lý giường"
                },
                "patient_id": {
                    "type": "string",
                    "required": False,
                    "description": "Patient ID (cho assign action)"
                },
                "unit_id": {
                    "type": "string",
                    "required": False,
                    "description": "Unit ID"
                },
            },
            default_obligations=[
                "audit_log_required",
            ],
        )
    )


# ============================================================================
# Macro Capabilities Registry (58+ macros)
# ============================================================================


@dataclass
class MacroCapabilitiesRegistry:
    """
    Registry của 104+ Macro Capabilities.
    
    Đây là single source of truth cho macro capability patterns.
    Mỗi macro expand về 17 core capabilities.
    
    Total: 104+ macro capabilities
    - Base: 6 macros
    - Mutation: 8 macros
    - Query: 6 macros
    - Workflow: 6 macros
    - Domain: 12 macros
    - Domain Extended Phase 1-3: 50 macros
    - Domain Extended Phase 4: 46 macros
    - Regulatory: 12 macros
    """
    
    base: BaseMacroCapabilities = field(default_factory=BaseMacroCapabilities)
    mutation: MutationMacroCapabilities = field(default_factory=MutationMacroCapabilities)
    query: QueryMacroCapabilities = field(default_factory=QueryMacroCapabilities)
    workflow: WorkflowMacroCapabilities = field(default_factory=WorkflowMacroCapabilities)
    domain: DomainMacroCapabilities = field(default_factory=DomainMacroCapabilities)
    domain_extended: DomainMacroCapabilitiesExtended = field(default_factory=DomainMacroCapabilitiesExtended)
    domain_phase4: DomainMacroCapabilitiesPhase4 = field(default_factory=DomainMacroCapabilitiesPhase4)
    regulatory: RegulatoryMacroCapabilities = field(default_factory=RegulatoryMacroCapabilities)
    
    @classmethod
    def get_all_macros(cls) -> list[MacroCapability]:
        """
        Lấy danh sách tất cả 50+ macro capabilities.
        
        Returns:
            Danh sách MacroCapability instances
        """
        registry = cls()
        macros = []
        
        # Base macros (6)
        macros.append(registry.base.AUTHORIZED_MUTATION)
        macros.append(registry.base.AUTHORIZED_QUERY)
        macros.append(registry.base.EVENT_HANDLER)
        macros.append(registry.base.WORKFLOW_DEFINITION)
        macros.append(registry.base.CASCADE_MUTATION)
        macros.append(registry.base.AGGREGATE_OPERATION)
        
        # Mutation macros (8)
        macros.append(registry.mutation.CREATE_WITH_AUDIT)
        macros.append(registry.mutation.UPDATE_WITH_VALIDATION)
        macros.append(registry.mutation.SOFT_DELETE_WITH_AUDIT)
        macros.append(registry.mutation.BULK_CREATE)
        macros.append(registry.mutation.UPSERT_RECORD)
        macros.append(registry.mutation.BATCH_UPDATE)
        macros.append(registry.mutation.ARCHIVE_RECORD)
        macros.append(registry.mutation.FORCE_DELETE)
        
        # Query macros (6)
        macros.append(registry.query.PAGINATED_QUERY)
        macros.append(registry.query.SEARCH_QUERY)
        macros.append(registry.query.AGGREGATE_QUERY)
        macros.append(registry.query.LOAD_WITH_RELATIONS)
        macros.append(registry.query.EXPORT_QUERY)
        macros.append(registry.query.COUNT_QUERY)
        
        # Workflow macros (6)
        macros.append(registry.workflow.STATE_MACHINE_TRANSITION)
        macros.append(registry.workflow.ASYNC_JOB)
        macros.append(registry.workflow.SAGA_ORCHESTRATION)
        macros.append(registry.workflow.APPROVAL_WORKFLOW)
        macros.append(registry.workflow.SCHEDULED_JOB)
        macros.append(registry.workflow.EVENT_SOURCING)
        
        # Domain macros (12)
        macros.append(registry.domain.CREATE_ORDER)
        macros.append(registry.domain.UPDATE_INVENTORY)
        macros.append(registry.domain.PROCESS_PAYMENT)
        macros.append(registry.domain.TRANSFER_FUNDS)
        macros.append(registry.domain.CREATE_LEDGER_ENTRY)
        macros.append(registry.domain.CREATE_PATIENT_RECORD)
        macros.append(registry.domain.PRESCRIBE_MEDICATION)
        macros.append(registry.domain.ONBOARD_EMPLOYEE)
        macros.append(registry.domain.CREATE_SHIPMENT)
        macros.append(registry.domain.PUBLISH_CONTENT)
        macros.append(registry.domain.CREATE_BOOKING)
        macros.append(registry.domain.CREATE_SUBSCRIPTION)
        
        # Domain Extended macros - Phase 1, 2, & 3 (50 macros)
        # Ecommerce D2C (4)
        macros.append(registry.domain_extended.APPLY_PROMOTION)
        # ... (existing Phase 1-3 macros)
        
        # Domain Extended macros - Phase 4 (46 macros)
        # Retail Banking (8)
        macros.append(registry.domain_phase4.OPEN_ACCOUNT)
        macros.append(registry.domain_phase4.PROCESS_LOAN_APPLICATION)
        macros.append(registry.domain_phase4.DETECT_FRAUD)
        macros.append(registry.domain_phase4.GENERATE_STATEMENTS)
        macros.append(registry.domain_phase4.PROCESS_WITHDRAWAL)
        macros.append(registry.domain_phase4.PROCESS_DEPOSIT)
        macros.append(registry.domain_phase4.FILE_SAR)
        macros.append(registry.domain_phase4.MANAGE_COLLATERAL)
        # Last-mile Delivery (5)
        macros.append(registry.domain_phase4.OPTIMIZE_DELIVERY_ROUTE)
        macros.append(registry.domain_phase4.ASSIGN_DELIVERY_SLOT)
        macros.append(registry.domain_phase4.UPDATE_DELIVERY_STATUS)
        macros.append(registry.domain_phase4.CALCULATE_DELIVERY_FARE)
        macros.append(registry.domain_phase4.MANAGE_PROOF_OF_DELIVERY)
        # Omni-channel Retail (6)
        macros.append(registry.domain_phase4.SYNC_INVENTORY)
        macros.append(registry.domain_phase4.RESERVE_STOCK)
        macros.append(registry.domain_phase4.PROCESS_BOPIS)
        macros.append(registry.domain_phase4.MANAGE_CHANNEL_PRICING)
        macros.append(registry.domain_phase4.PROCESS_SHIP_FROM_STORE)
        macros.append(registry.domain_phase4.UNIFY_CUSTOMER_VIEW)
        # Omnichannel (4)
        macros.append(registry.domain_phase4.CONTINUE_SHOPPING)
        macros.append(registry.domain_phase4.CROSS_CHANNEL_RETURN)
        macros.append(registry.domain_phase4.OMNICHANNEL_LOYALTY)
        macros.append(registry.domain_phase4.PERSONALIZE_OMNICHANNEL)
        # Warehouse Management Extended (8)
        macros.append(registry.domain_phase4.FORECAST_DEMAND)
        macros.append(registry.domain_phase4.MANAGE_REPLENISHMENT)
        macros.append(registry.domain_phase4.TRACK_SHIPPING_LABEL)
        macros.append(registry.domain_phase4.PROCESS_INVENTORY_ADJUSTMENT)
        macros.append(registry.domain_phase4.GENERATE_PICK_LIST)
        macros.append(registry.domain_phase4.MANAGE_WAVE_PICKING)
        macros.append(registry.domain_phase4.TRACK_BIN_UTILIZATION)
        macros.append(registry.domain_phase4.PROCESS_PICK_RETURN)
        # Procurement SRM Extended (5)
        macros.append(registry.domain_phase4.FORECAST_DEMAND_PROCUREMENT)
        macros.append(registry.domain_phase4.APPROVE_PURCHASE_ORDER)
        macros.append(registry.domain_phase4.TRACK_PO_STATUS)
        macros.append(registry.domain_phase4.MANAGE_CONTRACT_COMPLIANCE)
        macros.append(registry.domain_phase4.PERFORM_VENDOR_RISK_ASSESSMENT)
        # CRM Platform Extended (3)
        macros.append(registry.domain_phase4.SCORE_LEAD)
        macros.append(registry.domain_phase4.ASSIGN_TICKET)
        macros.append(registry.domain_phase4.MERGE_DUPLICATE_CONTACTS)
        # ERP Finance Extended (6)
        macros.append(registry.domain_phase4.PROCESS_PAYABLES)
        macros.append(registry.domain_phase4.PROCESS_RECEIVABLES)
        macros.append(registry.domain_phase4.MANAGE_CASH_FLOW)
        macros.append(registry.domain_phase4.GENERATE_TRIAL_BALANCE)
        macros.append(registry.domain_phase4.PROCESS_INTERCOMPANY)
        macros.append(registry.domain_phase4.RUN_DEPRECIATION)
        # ITSM Helpdesk Extended (2)
        macros.append(registry.domain_phase4.CREATE_CHANGE_REQUEST)
        macros.append(registry.domain_phase4.ESCALATE_INCIDENT)
        # Payroll Benefits Extended (3)
        macros.append(registry.domain_phase4.CALCULATE_PAYCHECK)
        macros.append(registry.domain_phase4.PROCESS_DIRECT_DEPOSIT)
        macros.append(registry.domain_phase4.MANAGE_BENEFITS_ELECTION)
        # Exchange Trading Extended (5)
        macros.append(registry.domain_phase4.MANAGE_ORDER_BOOK)
        macros.append(registry.domain_phase4.CALCULATE_MARK_TO_MARKET)
        macros.append(registry.domain_phase4.PROCESS_TRADE_SETTLEMENT)
        macros.append(registry.domain_phase4.GENERATE_REGULATORY_REPORT)
        macros.append(registry.domain_phase4.MONITOR_POSITION_LIMITS)
        # Healthcare Hospital IS Extended (4)
        macros.append(registry.domain_phase4.SCHEDULE_APPOINTMENT)
        macros.append(registry.domain_phase4.MANAGE_REFILL_PRESCRIPTION)
        macros.append(registry.domain_phase4.PROCESS_CLAIM)
        macros.append(registry.domain_phase4.TRACK_EHR_ACCESS)
        macros.append(registry.domain_extended.PROCESS_REFUND)
        macros.append(registry.domain_extended.MANAGE_SUBSCRIPTION)
        macros.append(registry.domain_extended.RECOMMEND_PRODUCTS)
        # Marketplace B2C (5)
        macros.append(registry.domain_extended.ONBOARD_SELLER)
        macros.append(registry.domain_extended.HOLD_ESCROW_PAYMENT)
        macros.append(registry.domain_extended.SPLIT_PAYMENT)
        macros.append(registry.domain_extended.RESOLVE_DISPUTE)
        macros.append(registry.domain_extended.RATE_REVIEW)
        # Marketplace B2B (4)
        macros.append(registry.domain_extended.CREATE_RFP)
        macros.append(registry.domain_extended.MANAGE_CREDIT_TERMS)
        macros.append(registry.domain_extended.APPLY_BULK_PRICING)
        macros.append(registry.domain_extended.PROCESS_PURCHASE_ORDER)
        # Food Delivery (4)
        macros.append(registry.domain_extended.ASSIGN_DELIVERY_DRIVER)
        macros.append(registry.domain_extended.CALCULATE_DELIVERY_ROUTE)
        macros.append(registry.domain_extended.TRACK_REALTIME_LOCATION)
        macros.append(registry.domain_extended.PROCESS_TIP)
        # Warehouse Management (5)
        macros.append(registry.domain_extended.RECEIVE_INVENTORY)
        macros.append(registry.domain_extended.PICK_PACK_SHIP)
        macros.append(registry.domain_extended.CYCLE_COUNT)
        macros.append(registry.domain_extended.BIN_TRANSFER)
        macros.append(registry.domain_extended.MANAGE_BIN_LOCATION)
        # Procurement SRM (5)
        macros.append(registry.domain_extended.CREATE_RFQ)
        macros.append(registry.domain_extended.EVALUATE_VENDOR)
        macros.append(registry.domain_extended.MANAGE_CONTRACT)
        macros.append(registry.domain_extended.SPEND_ANALYSIS)
        macros.append(registry.domain_extended.SUPPLIER_ONBOARDING)
        # CRM Platform (5)
        macros.append(registry.domain_extended.CREATE_LEAD)
        macros.append(registry.domain_extended.CONVERT_OPPORTUNITY)
        macros.append(registry.domain_extended.LOG_ACTIVITY)
        macros.append(registry.domain_extended.RUN_CAMPAIGN)
        macros.append(registry.domain_extended.CASE_ESCALATION)
        # ERP Finance (5)
        macros.append(registry.domain_extended.POST_JOURNAL_ENTRY)
        macros.append(registry.domain_extended.RECONCILE_ACCOUNTS)
        macros.append(registry.domain_extended.CLOSE_PERIOD)
        macros.append(registry.domain_extended.CONSOLIDATE_ENTITIES)
        macros.append(registry.domain_extended.FIXED_ASSET_CAPITALIZATION)
        # ITSM Helpdesk (4)
        macros.append(registry.domain_extended.CREATE_TICKET)
        macros.append(registry.domain_extended.APPROVE_CHANGE)
        macros.append(registry.domain_extended.PUBLISH_KB_ARTICLE)
        macros.append(registry.domain_extended.ESCALATE_TICKET)
        # Exchange Trading (4)
        macros.append(registry.domain_extended.MATCH_ORDERS)
        macros.append(registry.domain_extended.CLEAR_SETTLEMENT)
        macros.append(registry.domain_extended.CALCULATE_MARGIN)
        macros.append(registry.domain_extended.SURVEILLANCE_CHECK)
        # Payroll Benefits (4)
        macros.append(registry.domain_extended.PROCESS_PAYROLL_RUN)
        macros.append(registry.domain_extended.FILE_TAX_RETURNS)
        macros.append(registry.domain_extended.ENROLL_BENEFITS)
        macros.append(registry.domain_extended.PROCESS_GARNISHMENT)
        # Healthcare Hospital IS (4)
        macros.append(registry.domain_extended.ADMIT_PATIENT)
        macros.append(registry.domain_extended.ENTER_MEDICAL_ORDER)
        macros.append(registry.domain_extended.DOCUMENT_CLINICAL_NOTE)
        macros.append(registry.domain_extended.MANAGE_BED)
        
        # Regulatory macros (12)
        macros.append(registry.regulatory.KYC_VERIFICATION)
        macros.append(registry.regulatory.PII_ENCRYPTION)
        macros.append(registry.regulatory.IMMUTABLE_AUDIT)
        macros.append(registry.regulatory.DATA_RETENTION)
        macros.append(registry.regulatory.SANCTIONS_SCREENING)
        macros.append(registry.regulatory.GDPR_RIGHT_TO_ERASURE)
        macros.append(registry.regulatory.FINANCIAL_REPORTING)
        macros.append(registry.regulatory.TAX_CALCULATION)
        macros.append(registry.regulatory.ACCESS_LOGGING)
        macros.append(registry.regulatory.COMPLIANCE_CERTIFICATION)
        macros.append(registry.regulatory.DATA_EXPORT)
        macros.append(registry.regulatory.NOTIFICATION_BATCH)
        
        return macros
    
    @classmethod
    def get_macro_by_id(cls, macro_id: str) -> MacroCapability | None:
        """
        Lấy macro capability theo ID.
        
        Args:
            macro_id: ID của macro capability
            
        Returns:
            MacroCapability nếu tìm thấy, None nếu không
        """
        for macro in cls.get_all_macros():
            if macro.id == macro_id:
                return macro
        return None
    
    @classmethod
    def get_macro_ids(cls) -> list[str]:
        """
        Lấy danh sách tất cả macro capability IDs.
        
        Returns:
            Danh sách macro IDs
        """
        return [macro.id for macro in cls.get_all_macros()]
    
    @classmethod
    def get_statistics(cls) -> dict[str, Any]:
        """
        Lấy statistics của macro capabilities.
        
        Returns:
            Statistics dictionary
        """
        macros = cls.get_all_macros()
        
        return {
            "total": len(macros),
            "by_category": {
                "base": 6,
                "mutation": 8,
                "query": 6,
                "workflow": 6,
                "domain": 12,
                "regulatory": 12,
            },
            "macro_ids": cls.get_macro_ids(),
        }


# Export all capabilities
__all__ = [
    # Category classes
    "BaseMacroCapabilities",
    "MutationMacroCapabilities",
    "QueryMacroCapabilities",
    "WorkflowMacroCapabilities",
    "DomainMacroCapabilities",
    "DomainMacroCapabilitiesExtended",
    "DomainMacroCapabilitiesPhase4",
    "RegulatoryMacroCapabilities",
    # Registry
    "MacroCapabilitiesRegistry",
]
