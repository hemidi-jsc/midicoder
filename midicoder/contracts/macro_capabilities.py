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
# Macro Capabilities Registry (50+ macros)
# ============================================================================


@dataclass
class MacroCapabilitiesRegistry:
    """
    Registry của 50+ Macro Capabilities.
    
    Đây là single source of truth cho macro capability patterns.
    Mỗi macro expand về 17 core capabilities.
    
    Total: 50+ macro capabilities
    - Base: 6 macros
    - Mutation: 8 macros
    - Query: 6 macros
    - Workflow: 6 macros
    - Domain: 12 macros
    - Regulatory: 10 macros
    """
    
    base: BaseMacroCapabilities = field(default_factory=BaseMacroCapabilities)
    mutation: MutationMacroCapabilities = field(default_factory=MutationMacroCapabilities)
    query: QueryMacroCapabilities = field(default_factory=QueryMacroCapabilities)
    workflow: WorkflowMacroCapabilities = field(default_factory=WorkflowMacroCapabilities)
    domain: DomainMacroCapabilities = field(default_factory=DomainMacroCapabilities)
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
    "RegulatoryMacroCapabilities",
    # Registry
    "MacroCapabilitiesRegistry",
]