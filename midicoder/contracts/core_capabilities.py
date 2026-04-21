"""
Core Capabilities Registry cho Midicoder v1.0.0

Module này định nghĩa registry của 17 Core Capabilities.

Core capability language phải nhỏ, đóng và có semantics chặt:
- Là primitive operations mà system có thể thực thi
- 17 core capabilities là baseline bắt buộc
- Các capabilities bổ sung cần architectural decision

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .graph import CoreCapability


# ============================================================================
# Core Capabilities (17 Total)
# ============================================================================
# - Authorization & Security: 3
# - Data Operations: 5
# - Transaction Management: 3
# - Event & Integration: 3
# - Audit & Observability: 2
# ============================================================================


@dataclass
class AuthorizationCoreCapabilities:
    """
    Authorization & Security Core Capabilities (3 capabilities).
    
    Các capabilities này đảm bảo:
    - Permission checking trước khi access resources
    - Tenant scope enforcement cho multi-tenant isolation
    - Input validation để prevent injection attacks
    """
    AUTHORIZE_PERMISSION: CoreCapability = field(
        default_factory=lambda: CoreCapability(
            id="authorize_permission",
            name="Authorize Permission",
            description="Kiểm tra người dùng có permission để thực hiện action không",
            params_schema={
                "permission": {
                    "type": "string",
                    "required": True,
                    "description": "Permission string cần check (vd: 'order.create')"
                },
                "principal": {
                    "type": "object",
                    "required": True,
                    "description": "Principal information (user_id, roles, tenant_id)"
                },
                "resource": {
                    "type": "object", 
                    "required": False,
                    "description": "Resource context nếu có (resource_type, resource_id)"
                }
            },
            default_obligations=[
                "auth_guard_required",
                "permission_check_required"
            ],
            read_access=["user", "role", "permission"],
            write_access=[],
            effects=[]
        )
    )
    
    # SoT: ENFORCE_TENANT_SCOPE = "enforce_tenant_scope"
    ENFORCE_TENANT_SCOPE: CoreCapability = field(
        default_factory=lambda: CoreCapability(
            id="enforce_tenant_scope",
            name="Enforce Tenant Scope",
            description="Đảm bảo operation chỉ access data của tenant hiện tại",
            params_schema={
                "tenant_id": {
                    "type": "string",
                    "required": True,
                    "description": "Tenant ID cần enforce"
                },
                "scope": {
                    "type": "string",
                    "required": True,
                    "enum": ["tenant_isolated", "tenant_inclusive", "cross_tenant"],
                    "description": "Scope mode: isolated (chỉ tenant), inclusive (tenant + system), cross_tenant (multi-tenant)"
                },
                "auto_filter": {
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "description": "Tự động thêm tenant_id filter vào queries"
                }
            },
            default_obligations=[
                "tenant_filter_required",
                "tenant_scope_valid"
            ],
            read_access=["tenant", "tenant_membership"],
            write_access=[],
            effects=[]
        )
    )
    
    # SoT: VALIDATE_INPUT = "validate_input"
    VALIDATE_INPUT: CoreCapability = field(
        default_factory=lambda: CoreCapability(
            id="validate_input",
            name="Validate Input",
            description="Validate input data để prevent injection và data corruption",
            params_schema={
                "input_data": {
                    "type": "object",
                    "required": True,
                    "description": "Input data cần validate"
                },
                "schema": {
                    "type": "object",
                    "required": True,
                    "description": "Validation schema (JSON Schema format)"
                },
                "sanitize": {
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "description": "Tự động sanitize input"
                },
                "rules": {
                    "type": "array",
                    "required": False,
                    "description": "Custom validation rules"
                }
            },
            default_obligations=[
                "input_validation_required"
            ],
            read_access=[],
            write_access=[],
            effects=[]
        )
    )


@dataclass
class DataOperationsCoreCapabilities:
    """
    Data Operations Core Capabilities (5 capabilities).
    
    Các capabilities này cung cấp CRUD operations cho entities.
    """
    CREATE_RECORD: CoreCapability = field(
        default_factory=lambda: CoreCapability(
            id="create_record",
            name="Create Record",
            description="Tạo mới một record trong database với expressive params",
            params_schema={
                # Core params
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name (vd: 'Order', 'Customer', 'LedgerEntry')"
                },
                "data": {
                    "type": "object",
                    "required": True,
                    "description": "Record data"
                },
                "upsert": {
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "description": "Upsert mode: tạo mới hoặc update nếu tồn tại"
                },
                "return_created": {
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "description": "Trả về record đã tạo"
                },
                # Expressive params - Validation Rules
                "validation_rules": {
                    "type": "array",
                    "required": False,
                    "description": "In-line validation rules",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"enum": ["required", "range", "pattern", "custom"]},
                            "fields": {"type": "array"},
                            "min": {"type": "number"},
                            "max": {"type": "number"},
                            "pattern": {"type": "string"},
                            "expression": {"type": "string"}
                        }
                    },
                    "example": [
                        {"type": "required", "fields": ["id", "amount"]},
                        {"type": "range", "field": "amount", "min": 0, "max": 1000000},
                        {"type": "custom", "expression": "amount <= available_balance"}
                    ]
                },
                # Expressive params - Business Rules
                "business_rules": {
                    "type": "array",
                    "required": False,
                    "description": "Business logic hooks",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"enum": ["audit", "notify", "workflow", "calculate"]},
                            "action": {"type": "string"},
                            "level": {"type": "string"},
                            "channel": {"type": "string"},
                            "template": {"type": "string"},
                            "trigger": {"type": "string"}
                        }
                    },
                    "example": [
                        {"type": "audit", "action": "create", "level": "detailed"},
                        {"type": "notify", "channel": "email", "template": "order.created"},
                        {"type": "workflow", "trigger": "approval_required"}
                    ]
                },
                # Expressive params - Audit Config
                "audit_config": {
                    "type": "object",
                    "required": False,
                    "description": "Audit trail configuration",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "level": {"enum": ["minimal", "standard", "detailed"]},
                        "include_before": {"type": "boolean"},
                        "include_after": {"type": "boolean"},
                        "retention_days": {"type": "integer"}
                    },
                    "example": {
                        "enabled": True,
                        "level": "detailed",
                        "include_before": False,
                        "include_after": True,
                        "retention_days": 2555
                    }
                },
                # Expressive params - Transaction Config
                "transaction_config": {
                    "type": "object",
                    "required": False,
                    "description": "Transaction semantics configuration",
                    "properties": {
                        "isolation": {"enum": ["read_uncommitted", "read_committed", "repeatable_read", "serializable"]},
                        "timeout": {"type": "integer"},
                        "compensation": {"type": "string"}
                    },
                    "example": {
                        "isolation": "serializable",
                        "timeout": 30,
                        "compensation": "create_refund_order"
                    }
                },
                # Expressive params - Lifecycle Hooks
                "hooks": {
                    "type": "object",
                    "required": False,
                    "description": "Before/after lifecycle hooks",
                    "properties": {
                        "before_create": {"type": "array", "items": {"type": "string"}},
                        "after_create": {"type": "array", "items": {"type": "string"}},
                        "on_error": {"type": "array", "items": {"type": "string"}}
                    },
                    "example": {
                        "before_create": ["validate_inventory", "check_quota"],
                        "after_create": ["send_confirmation", "update_metrics"],
                        "on_error": ["log_error", "notify_admin"]
                    }
                }
            },
            default_obligations=[
                "transaction_required"
            ],
            read_access=[],
            write_access=["database"],
            effects=["record_created"]
        )
    )
    
    # SoT: UPDATE_RECORD = "update_record"
    UPDATE_RECORD: CoreCapability = field(
        default_factory=lambda: CoreCapability(
            id="update_record",
            name="Update Record",
            description="Cập nhật một record trong database với optimistic locking, conditional update và audit config",
            params_schema={
                # Core params
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "id": {
                    "type": "string",
                    "required": True,
                    "description": "Record ID cần update"
                },
                "data": {
                    "type": "object",
                    "required": True,
                    "description": "Update data (partial)"
                },
                # Standard params
                "upsert": {
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "description": "Upsert mode: tạo mới nếu không tồn tại"
                },
                "return_updated": {
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "description": "Trả về record đã update"
                },
                # Optimalistic Locking
                "optimistic_locking": {
                    "type": "object",
                    "required": False,
                    "description": "Cấu hình optimistic locking để tránh conflicts",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "version_field": {"type": "string"},
                        "expected_version": {"type": "integer"}
                    },
                    "example": {
                        "enabled": True,
                        "version_field": "version",
                        "expected_version": 5
                    }
                },
                # Conditional Update
                "conditional_update": {
                    "type": "object",
                    "required": False,
                    "description": "Điều kiện để update chỉ thực hiện khi thỏa mãn",
                    "properties": {
                        "conditions": {"type": "array", "items": {"type": "object"}},
                        "if_exists": {"type": "boolean"},
                        "status_check": {"type": "object"}
                    },
                    "example": {
                        "conditions": [
                            {"field": "status", "operator": "=", "value": "draft"},
                            {"field": "updated_at", "operator": "<", "value": "2024-01-01"}
                        ],
                        "if_exists": True,
                        "status_check": {"field": "status", "not_in": ["deleted", "archived"]}
                    }
                },
                # Audit Diff Config
                "audit_diff_config": {
                    "type": "object",
                    "required": False,
                    "description": "Cấu hình audit trail cho update operation",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "track_changes": {"type": "boolean"},
                        "include_diff": {"type": "boolean"},
                        "sensitive_fields": {"type": "array", "items": {"type": "string"}},
                        "retention_days": {"type": "integer"}
                    },
                    "example": {
                        "enabled": True,
                        "track_changes": True,
                        "include_diff": True,
                        "sensitive_fields": ["password", "ssn"],
                        "retention_days": 2555
                    }
                }
            },
            default_obligations=[
                "transaction_required"
            ],
            read_access=["database"],
            write_access=["database"],
            effects=["record_updated"]
        )
    )
    
    # SoT: DELETE_RECORD = "delete_record"
    DELETE_RECORD: CoreCapability = field(
        default_factory=lambda: CoreCapability(
            id="delete_record",
            name="Delete Record",
            description="Xóa một record trong database với cascade rules, retention policy và soft delete mode",
            params_schema={
                # Core params
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "id": {
                    "type": "string",
                    "required": True,
                    "description": "Record ID cần xóa"
                },
                # Standard params
                "soft_delete": {
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "description": "Soft delete (đánh dấu deleted thay vì xóa hẳn)"
                },
                "cascade": {
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "description": "Cascade delete các records liên quan"
                },
                # Cascade Rules
                "cascade_rules": {
                    "type": "object",
                    "required": False,
                    "description": "Cấu hình cascade delete rules cho các relationships",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "relationships": {"type": "array", "items": {"type": "object"}},
                        "orphan_action": {"type": "string", "enum": ["delete", "set_null", "restrict"]}
                    },
                    "example": {
                        "enabled": True,
                        "relationships": [
                            {"entity": "OrderItem", "action": "delete"},
                            {"entity": "OrderAudit", "action": "restrict"}
                        ],
                        "orphan_action": "set_null"
                    }
                },
                # Retention Days
                "retention_days": {
                    "type": "integer",
                    "required": False,
                    "description": "Số ngày giữ record trước khi permanent delete (cho soft delete)",
                    "example": 2555
                },
                # Soft Delete Mode
                "soft_delete_mode": {
                    "type": "object",
                    "required": False,
                    "description": "Cấu hình chi tiết cho soft delete",
                    "properties": {
                        "mode": {"type": "string", "enum": ["timestamp", "flag", "archive"]},
                        "timestamp_field": {"type": "string"},
                        "flag_field": {"type": "string"},
                        "archive_table": {"type": "string"},
                        "preserve_data": {"type": "boolean"}
                    },
                    "example": {
                        "mode": "timestamp",
                        "timestamp_field": "deleted_at",
                        "preserve_data": True
                    }
                }
            },
            default_obligations=[
                "transaction_required",
                "audit_log_required"
            ],
            read_access=[],
            write_access=["database"],
            effects=["record_deleted"]
        )
    )
    
    # SoT: QUERY_RECORDS = "query_records"
    QUERY_RECORDS: CoreCapability = field(
        default_factory=lambda: CoreCapability(
            id="query_records",
            name="Query Records",
            description="Query records từ database với pagination strategy, cache hint, read preference và geospatial filters",
            params_schema={
                # Core params
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Entity name"
                },
                "filter": {
                    "type": "object",
                    "required": False,
                    "description": "Filter conditions (supports geospatial: geo_within_radius, geo_nearest, geo_bounding_box)",
                    "example": {
                        "geo_within_radius": {
                            "field": "location",
                            "center": {"lat": 10.8231, "lng": 106.6297},
                            "radius_km": 5
                        }
                    }
                },
                "sort": {
                    "type": "array",
                    "required": False,
                    "description": "Sort order: [{field, direction}]"
                },
                # Standard pagination params
                "page": {
                    "type": "integer",
                    "required": False,
                    "default": 1,
                    "description": "Page number (cho offset-based pagination)"
                },
                "per_page": {
                    "type": "integer",
                    "required": False,
                    "default": 20,
                    "description": "Records per page"
                },
                "fields": {
                    "type": "array",
                    "required": False,
                    "description": "Fields to select (projection)"
                },
                # Pagination Strategy
                "pagination_strategy": {
                    "type": "object",
                    "required": False,
                    "description": "Cấu hình pagination strategy",
                    "properties": {
                        "type": {"type": "string", "enum": ["offset", "cursor", "keyset"]},
                        "cursor_field": {"type": "string"},
                        "cursor_value": {"type": "string"},
                        "limit": {"type": "integer"},
                        "include_total": {"type": "boolean"}
                    },
                    "example": {
                        "type": "cursor",
                        "cursor_field": "created_at",
                        "cursor_value": "MTY5ODc2NTQzMA==",
                        "limit": 20,
                        "include_total": False
                    }
                },
                # Cache Hint
                "cache_hint": {
                    "type": "object",
                    "required": False,
                    "description": "Gợi ý caching cho query",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "ttl_seconds": {"type": "integer"},
                        "cache_key_prefix": {"type": "string"},
                        "stale_while_revalidate": {"type": "boolean"},
                        "bypass_cache": {"type": "boolean"}
                    },
                    "example": {
                        "enabled": True,
                        "ttl_seconds": 300,
                        "cache_key_prefix": "orders:list",
                        "stale_while_revalidate": True
                    }
                },
                # Read Preference
                "read_preference": {
                    "type": "object",
                    "required": False,
                    "description": "Cấu hình read preference cho replica sets",
                    "properties": {
                        "mode": {"type": "string", "enum": ["primary", "primary_preferred", "secondary", "secondary_preferred", "nearest"]},
                        "tag_sets": {"type": "array", "items": {"type": "object"}},
                        "max_staleness_seconds": {"type": "integer"}
                    },
                    "example": {
                        "mode": "secondary_preferred",
                        "tag_sets": [{"dc": "us-east-1"}],
                        "max_staleness_seconds": 60
                    }
                }
            },
            default_obligations=[
                "tenant_filter_required"
            ],
            read_access=["database"],
            write_access=[],
            effects=[]
        )
    )
    
    # SoT: LOAD_ENTITY = "load_entity"
    LOAD_ENTITY: CoreCapability = field(
        default_factory=lambda: CoreCapability(
            id="load_entity",
            name="Load Entity",
            description="Load một entity theo ID với relations",
            params_schema={
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
                    "required": False,
                    "description": "Relations to include"
                },
                "fields": {
                    "type": "array",
                    "required": False,
                    "description": "Fields to select"
                }
            },
            default_obligations=[
                "tenant_filter_required"
            ],
            read_access=["database"],
            write_access=[],
            effects=[]
        )
    )


@dataclass
class TransactionCoreCapabilities:
    """
    Transaction Management Core Capabilities (3 capabilities).
    
    Đảm bảo ACID properties cho data operations.
    """
    BEGIN_TRANSACTION: CoreCapability = field(
        default_factory=lambda: CoreCapability(
            id="begin_transaction",
            name="Begin Transaction",
            description="Bắt đầu một database transaction mới với isolation level, savepoint và timeout",
            params_schema={
                # Core params
                "isolation_level": {
                    "type": "string",
                    "required": False,
                    "enum": ["read_uncommitted", "read_committed", "repeatable_read", "serializable"],
                    "default": "read_committed",
                    "description": "Transaction isolation level theo ANSI SQL standard"
                },
                "read_only": {
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "description": "Read-only transaction (tối ưu cho query-heavy workloads)"
                },
                "timeout_seconds": {
                    "type": "integer",
                    "required": False,
                    "description": "Transaction timeout theo giây (auto rollback nếu quá hạn)",
                    "example": 30
                },
                # Savepoint support
                "savepoint_id": {
                    "type": "string",
                    "required": False,
                    "description": "Savepoint ID để rollback partial transaction",
                    "example": "sp_create_order_items"
                }
            },
            default_obligations=[],
            read_access=[],
            write_access=[],
            effects=["transaction_started"]
        )
    )
    
    # SoT: COMMIT_TRANSACTION = "commit_transaction"
    COMMIT_TRANSACTION: CoreCapability = field(
        default_factory=lambda: CoreCapability(
            id="commit_transaction",
            name="Commit Transaction",
            description="Commit transaction hiện tại",
            params_schema={
                "force": {
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "description": "Force commit nếu có errors"
                }
            },
            default_obligations=[],
            read_access=[],
            write_access=["database"],
            effects=["transaction_committed"]
        )
    )
    
    # SoT: ROLLBACK_TRANSACTION = "rollback_transaction"
    ROLLBACK_TRANSACTION: CoreCapability = field(
        default_factory=lambda: CoreCapability(
            id="rollback_transaction",
            name="Rollback Transaction",
            description="Rollback transaction hiện tại",
            params_schema={
                "reason": {
                    "type": "string",
                    "required": False,
                    "description": "Reason cho rollback"
                }
            },
            default_obligations=[],
            read_access=[],
            write_access=[],
            effects=["transaction_rolled_back"]
        )
    )


@dataclass
class EventIntegrationCoreCapabilities:
    """
    Event & Integration Core Capabilities (3 capabilities).
    
    Cung cấp event publishing và external integration.
    """
    PUBLISH_EVENT: CoreCapability = field(
        default_factory=lambda: CoreCapability(
            id="publish_event",
            name="Publish Event",
            description="Publish một event vào event bus",
            params_schema={
                "event_type": {
                    "type": "string",
                    "required": True,
                    "description": "Event type (vd: 'OrderCreated')"
                },
                "payload": {
                    "type": "object",
                    "required": True,
                    "description": "Event payload data"
                },
                "correlation_id": {
                    "type": "string",
                    "required": False,
                    "description": "Correlation ID cho distributed tracing"
                },
                "async": {
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "description": "Publish async"
                }
            },
            default_obligations=[],
            read_access=[],
            write_access=["event_bus"],
            effects=["event_published"]
        )
    )
    
    # SoT: CALL_EXTERNAL_SERVICE = "call_external_service"
    CALL_EXTERNAL_SERVICE: CoreCapability = field(
        default_factory=lambda: CoreCapability(
            id="call_external_service",
            name="Call External Service",
            description="Call một external service/API",
            params_schema={
                "service": {
                    "type": "string",
                    "required": True,
                    "description": "Service name/identifier"
                },
                "method": {
                    "type": "string",
                    "required": True,
                    "description": "API method"
                },
                "payload": {
                    "type": "object",
                    "required": False,
                    "description": "Request payload"
                },
                "timeout": {
                    "type": "integer",
                    "required": False,
                    "default": 30,
                    "description": "Timeout in seconds"
                },
                "retry_policy": {
                    "type": "object",
                    "required": False,
                    "description": "Retry policy config"
                }
            },
            default_obligations=[
                "error_handler_required",
                "timeout_required",
                "retry_policy_required"
            ],
            read_access=[],
            write_access=["external_api"],
            effects=["external_call_completed"]
        )
    )
    
    # SoT: SEND_NOTIFICATION = "send_notification"
    SEND_NOTIFICATION: CoreCapability = field(
        default_factory=lambda: CoreCapability(
            id="send_notification",
            name="Send Notification",
            description="Send notification đến user",
            params_schema={
                "channel": {
                    "type": "string",
                    "required": True,
                    "enum": ["email", "sms", "push", "in_app"],
                    "description": "Notification channel"
                },
                "recipient": {
                    "type": "string",
                    "required": True,
                    "description": "Recipient identifier"
                },
                "template": {
                    "type": "string",
                    "required": True,
                    "description": "Notification template name"
                },
                "data": {
                    "type": "object",
                    "required": False,
                    "description": "Template data"
                },
                "async": {
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "description": "Send async"
                }
            },
            default_obligations=[
                "error_handler_required"
            ],
            read_access=["notification_preferences"],
            write_access=["notification_queue"],
            effects=["notification_sent"]
        )
    )


@dataclass
class AuditObservabilityCoreCapabilities:
    """
    Audit & Observability Core Capabilities (2 capabilities).
    
    Cung cấp audit logging và metrics recording.
    """
    WRITE_AUDIT_LOG: CoreCapability = field(
        default_factory=lambda: CoreCapability(
            id="write_audit_log",
            name="Write Audit Log",
            description="Viết audit log entry immutable",
            params_schema={
                "action": {
                    "type": "string",
                    "required": True,
                    "description": "Action performed (vd: 'order.created')"
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
                    "description": "Actor information (user_id, ip, user_agent)"
                },
                "before": {
                    "type": "object",
                    "required": False,
                    "description": "State before change"
                },
                "after": {
                    "type": "object",
                    "required": False,
                    "description": "State after change"
                },
                "metadata": {
                    "type": "object",
                    "required": False,
                    "description": "Additional metadata"
                }
            },
            default_obligations=[
                "immutable_evidence_required"
            ],
            read_access=[],
            write_access=["audit_log"],
            effects=["audit_logged"]
        )
    )
    
    # SoT: RECORD_METRIC = "record_metric"
    RECORD_METRIC: CoreCapability = field(
        default_factory=lambda: CoreCapability(
            id="record_metric",
            name="Record Metric",
            description="Record một metric cho monitoring",
            params_schema={
                "metric_name": {
                    "type": "string",
                    "required": True,
                    "description": "Metric name"
                },
                "metric_type": {
                    "type": "string",
                    "required": True,
                    "enum": ["counter", "gauge", "histogram", "summary"],
                    "description": "Metric type"
                },
                "value": {
                    "type": "number",
                    "required": True,
                    "description": "Metric value"
                },
                "labels": {
                    "type": "object",
                    "required": False,
                    "description": "Metric labels/tags"
                }
            },
            default_obligations=[],
            read_access=[],
            write_access=["metrics"],
            effects=["metric_recorded"]
        )
    )


# ============================================================================
# Streaming Core Capabilities (1 capability - NEW E11-001)
# ============================================================================

@dataclass
class StreamingCoreCapabilities:
    """
    Streaming Core Capabilities (1 capability).
    
    Task: E11-001 - Add stream_connection core capability
    Priority: P0 - Required by Food Delivery, Exchange Trading, Telehealth
    
    Các capabilities này quản lý real-time streaming connections:
    - WebSocket cho bi-directional communication
    - SSE (Server-Sent Events) cho one-way streaming
    - gRPC streaming cho high-performance scenarios
    """
    STREAM_CONNECTION: CoreCapability = field(
        default_factory=lambda: CoreCapability(
            id="stream_connection",
            name="Stream Connection",
            description="Quản lý kết nối streaming real-time (WebSocket/SSE/gRPC)",
            params_schema={
                # Core params
                "protocol": {
                    "type": "string",
                    "required": True,
                    "enum": ["websocket", "sse", "grpc_stream"],
                    "description": "Streaming protocol: websocket (bi-directional), sse (server-to-client), grpc_stream (high-performance)"
                },
                "endpoint": {
                    "type": "string",
                    "required": True,
                    "description": "Streaming endpoint URL (vd: 'wss://api.example.com/stream')"
                },
                "subscription": {
                    "type": "string",
                    "required": True,
                    "description": "Subscription/channel name để subscribe (vd: 'order_updates:123')"
                },
                # Heartbeat config
                "heartbeat_interval": {
                    "type": "integer",
                    "required": False,
                    "default": 30,
                    "description": "Heartbeat interval theo giây để giữ kết nối sống"
                },
                # Reconnect policy
                "reconnect_policy": {
                    "type": "object",
                    "required": False,
                    "description": "Cấu hình reconnect policy cho unstable networks",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "max_retries": {"type": "integer"},
                        "initial_delay_ms": {"type": "integer"},
                        "max_delay_ms": {"type": "integer"},
                        "backoff_multiplier": {"type": "number"},
                        "jitter": {"type": "boolean"}
                    },
                    "example": {
                        "enabled": True,
                        "max_retries": 10,
                        "initial_delay_ms": 1000,
                        "max_delay_ms": 30000,
                        "backoff_multiplier": 2.0,
                        "jitter": True
                    }
                },
                # Auth mode
                "auth_mode": {
                    "type": "string",
                    "required": False,
                    "enum": ["none", "token", "sig_v4"],
                    "default": "token",
                    "description": "Authentication mode: none (no auth), token (JWT/Bearer), sig_v4 (AWS SigV4)"
                },
                "auth_token": {
                    "type": "string",
                    "required": False,
                    "description": "Auth token (cho auth_mode=token)"
                },
                "auth_headers": {
                    "type": "object",
                    "required": False,
                    "description": "Custom auth headers"
                },
                # Connection config
                "compression": {
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "description": "Enable message compression (cho WebSocket)"
                },
                "subprotocols": {
                    "type": "array",
                    "required": False,
                    "description": "Supported subprotocols (cho WebSocket)",
                    "items": {"type": "string"}
                },
                "message_handler": {
                    "type": "string",
                    "required": False,
                    "description": "Reference đến message handler function"
                },
                "on_disconnect": {
                    "type": "string",
                    "required": False,
                    "description": "Reference đến disconnect handler"
                }
            },
            default_obligations=[
                "connection_auth_required",
                "heartbeat_required",
                "reconnect_policy_required"
            ],
            read_access=["connection_state"],
            write_access=["network"],
            effects=["stream_connected", "stream_data_received", "stream_disconnected"]
        )
    )


# ============================================================================
# Core Capabilities Registry (17 capabilities theo SoT)
# ============================================================================

@dataclass
class CoreCapabilitiesRegistry:
    """
    Registry của 17 Core Capabilities.
    
    Đây là single source of truth cho core capability instruction set.
    Không được thêm/sửa capabilities ở đây trừ khi có architectural decision.
    
    Total: 17 core capabilities
    - Authorization & Security: 3
    - Data Operations: 5
    - Transaction Management: 3
    - Event & Integration: 3
    - Audit & Observability: 2
    - Streaming: 1 (NEW - E11-001)
    """
    
    auth: AuthorizationCoreCapabilities = field(default_factory=AuthorizationCoreCapabilities)
    data: DataOperationsCoreCapabilities = field(default_factory=DataOperationsCoreCapabilities)
    transaction: TransactionCoreCapabilities = field(default_factory=TransactionCoreCapabilities)
    event: EventIntegrationCoreCapabilities = field(default_factory=EventIntegrationCoreCapabilities)
    audit: AuditObservabilityCoreCapabilities = field(default_factory=AuditObservabilityCoreCapabilities)
    streaming: StreamingCoreCapabilities = field(default_factory=StreamingCoreCapabilities)
    
    @classmethod
    def get_all_capabilities(cls) -> list[CoreCapability]:
        """
        Lấy danh sách tất cả 17 core capabilities.
        
        Returns:
            Danh sách CoreCapability instances
        """
        registry = cls()
        capabilities = []
        
        # Authorization capabilities (3)
        capabilities.append(registry.auth.AUTHORIZE_PERMISSION)
        capabilities.append(registry.auth.ENFORCE_TENANT_SCOPE)
        capabilities.append(registry.auth.VALIDATE_INPUT)
        
        # Data operation capabilities (5)
        capabilities.append(registry.data.CREATE_RECORD)
        capabilities.append(registry.data.UPDATE_RECORD)
        capabilities.append(registry.data.DELETE_RECORD)
        capabilities.append(registry.data.QUERY_RECORDS)
        capabilities.append(registry.data.LOAD_ENTITY)
        
        # Transaction capabilities (3)
        capabilities.append(registry.transaction.BEGIN_TRANSACTION)
        capabilities.append(registry.transaction.COMMIT_TRANSACTION)
        capabilities.append(registry.transaction.ROLLBACK_TRANSACTION)
        
        # Event capabilities (3)
        capabilities.append(registry.event.PUBLISH_EVENT)
        capabilities.append(registry.event.CALL_EXTERNAL_SERVICE)
        capabilities.append(registry.event.SEND_NOTIFICATION)
        
        # Audit capabilities (2)
        capabilities.append(registry.audit.WRITE_AUDIT_LOG)
        capabilities.append(registry.audit.RECORD_METRIC)
        
        # Streaming capabilities (1)
        capabilities.append(registry.streaming.STREAM_CONNECTION)
        
        return capabilities
    
    @classmethod
    def get_capability_by_id(cls, capability_id: str) -> CoreCapability | None:
        """
        Lấy core capability theo ID.
        
        Args:
            capability_id: ID của core capability
            
        Returns:
            CoreCapability nếu tìm thấy, None nếu không
        """
        for cap in cls.get_all_capabilities():
            if cap.id == capability_id:
                return cap
        return None
    
    @classmethod
    def get_capability_ids(cls) -> list[str]:
        """
        Lấy danh sách tất cả 17 core capability IDs.
        
        Returns:
            Danh sách capability IDs
        """
        return [cap.id for cap in cls.get_all_capabilities()]
    
    @classmethod
    def get_statistics(cls) -> dict[str, Any]:
        """
        Lấy statistics của core capabilities.
        
        Returns:
            Statistics dictionary
        """
        capabilities = cls.get_all_capabilities()
        
        return {
            "total": len(capabilities),
            "by_category": {
                "authorization": 3,
                "data_operations": 5,
                "transaction": 3,
                "event_integration": 3,
                "audit_observability": 2,
                "streaming": 1
            },
            "capability_ids": cls.get_capability_ids()
        }


# Export all capabilities
__all__ = [
    # Category classes
    "AuthorizationCoreCapabilities",
    "DataOperationsCoreCapabilities",
    "TransactionCoreCapabilities",
    "EventIntegrationCoreCapabilities",
    "AuditObservabilityCoreCapabilities",
    "StreamingCoreCapabilities",
    # Registry
    "CoreCapabilitiesRegistry",
]
