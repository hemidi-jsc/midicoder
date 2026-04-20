"""
Unit Tests cho Core Capabilities Registry.

Kiểm tra:
- 17 core capabilities được định nghĩa đầy đủ
- Mỗi capability có params_schema hợp lệ
- Default obligations được set đúng
- Core capability categories đầy đủ (auth, data, transaction, event, audit)
- Serialization/deserialization hoạt động đúng

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.contracts.core_capabilities import (
    CoreCapabilitiesRegistry,
    AuthorizationCoreCapabilities,
    DataOperationsCoreCapabilities,
    TransactionCoreCapabilities,
    EventIntegrationCoreCapabilities,
    AuditObservabilityCoreCapabilities,
)
from midicoder.contracts.graph import CoreCapability


class TestAuthorizationCoreCapabilities:
    """Tests cho Authorization & Security Core Capabilities (3 capabilities)."""

    def test_authorize_permission_exists(self):
        """Kiểm tra authorize_permission capability tồn tại."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("authorize_permission")

        assert cap is not None
        assert cap.id == "authorize_permission"
        assert cap.name == "Authorize Permission"
        assert "permission" in cap.params_schema
        assert "principal" in cap.params_schema
        assert "permission_check_required" in cap.default_obligations

    def test_authorize_permission_schema_valid(self):
        """Kiểm tra schema của authorize_permission hợp lệ."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("authorize_permission")

        # Kiểm tra permission field
        assert cap.params_schema["permission"]["type"] == "string"
        assert cap.params_schema["permission"]["required"] is True

        # Kiểm tra principal field
        assert cap.params_schema["principal"]["type"] == "object"
        assert cap.params_schema["principal"]["required"] is True

    def test_enforce_tenant_scope_exists(self):
        """Kiểm tra enforce_tenant_scope capability tồn tại."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("enforce_tenant_scope")

        assert cap is not None
        assert cap.id == "enforce_tenant_scope"
        assert cap.name == "Enforce Tenant Scope"
        assert "tenant_id" in cap.params_schema
        assert "scope" in cap.params_schema
        assert "tenant_filter_required" in cap.default_obligations

    def test_enforce_tenant_scope_scope_enum(self):
        """Kiểm tra scope enum của enforce_tenant_scope."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("enforce_tenant_scope")

        scope_enum = cap.params_schema["scope"]["enum"]
        assert "tenant_isolated" in scope_enum
        assert "tenant_inclusive" in scope_enum
        assert "cross_tenant" in scope_enum

    def test_validate_input_exists(self):
        """Kiểm tra validate_input capability tồn tại."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("validate_input")

        assert cap is not None
        assert cap.id == "validate_input"
        assert cap.name == "Validate Input"
        assert "input_data" in cap.params_schema
        assert "schema" in cap.params_schema
        assert "input_validation_required" in cap.default_obligations


class TestDataOperationsCoreCapabilities:
    """Tests cho Data Operations Core Capabilities (5 capabilities)."""

    def test_create_record_exists(self):
        """Kiểm tra create_record capability tồn tại."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("create_record")

        assert cap is not None
        assert cap.id == "create_record"
        assert cap.name == "Create Record"
        assert "entity" in cap.params_schema
        assert "data" in cap.params_schema
        assert "transaction_required" in cap.default_obligations
        assert "database" in cap.write_access
        assert "record_created" in cap.effects

    def test_create_record_expressive_params(self):
        """Kiểm tra expressive params của create_record."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("create_record")

        # Kiểm tra validation_rules
        assert "validation_rules" in cap.params_schema
        assert cap.params_schema["validation_rules"]["type"] == "array"

        # Kiểm tra business_rules
        assert "business_rules" in cap.params_schema
        assert cap.params_schema["business_rules"]["type"] == "array"

        # Kiểm tra audit_config
        assert "audit_config" in cap.params_schema
        assert cap.params_schema["audit_config"]["type"] == "object"

        # Kiểm tra transaction_config
        assert "transaction_config" in cap.params_schema

        # Kiểm tra hooks
        assert "hooks" in cap.params_schema

    def test_update_record_exists(self):
        """Kiểm tra update_record capability tồn tại."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("update_record")

        assert cap is not None
        assert cap.id == "update_record"
        assert cap.name == "Update Record"
        assert "entity" in cap.params_schema
        assert "id" in cap.params_schema
        assert "data" in cap.params_schema
        assert "transaction_required" in cap.default_obligations
        assert "record_updated" in cap.effects

    def test_update_record_optimistic_locking(self):
        """Kiểm tra optimistic locking của update_record."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("update_record")

        assert "optimistic_locking" in cap.params_schema
        assert cap.params_schema["optimistic_locking"]["type"] == "object"

    def test_update_record_conditional_update(self):
        """Kiểm tra conditional update của update_record."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("update_record")

        assert "conditional_update" in cap.params_schema
        assert cap.params_schema["conditional_update"]["type"] == "object"

    def test_delete_record_exists(self):
        """Kiểm tra delete_record capability tồn tại."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("delete_record")

        assert cap is not None
        assert cap.id == "delete_record"
        assert cap.name == "Delete Record"
        assert "entity" in cap.params_schema
        assert "id" in cap.params_schema
        assert "transaction_required" in cap.default_obligations
        assert "audit_log_required" in cap.default_obligations
        assert "record_deleted" in cap.effects

    def test_delete_record_soft_delete(self):
        """Kiểm tra soft delete params của delete_record."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("delete_record")

        assert "soft_delete" in cap.params_schema
        assert "cascade" in cap.params_schema
        assert "cascade_rules" in cap.params_schema
        assert "retention_days" in cap.params_schema
        assert "soft_delete_mode" in cap.params_schema

    def test_query_records_exists(self):
        """Kiểm tra query_records capability tồn tại."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("query_records")

        assert cap is not None
        assert cap.id == "query_records"
        assert cap.name == "Query Records"
        assert "entity" in cap.params_schema
        assert "tenant_filter_required" in cap.default_obligations
        assert "database" in cap.read_access

    def test_query_records_pagination_strategy(self):
        """Kiểm tra pagination strategy của query_records."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("query_records")

        assert "pagination_strategy" in cap.params_schema
        strategy = cap.params_schema["pagination_strategy"]
        assert strategy["properties"]["type"]["enum"] == ["offset", "cursor", "keyset"]

    def test_query_records_cache_hint(self):
        """Kiểm tra cache hint của query_records."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("query_records")

        assert "cache_hint" in cap.params_schema

    def test_query_records_read_preference(self):
        """Kiểm tra read preference của query_records."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("query_records")

        assert "read_preference" in cap.params_schema

    def test_load_entity_exists(self):
        """Kiểm tra load_entity capability tồn tại."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("load_entity")

        assert cap is not None
        assert cap.id == "load_entity"
        assert cap.name == "Load Entity"
        assert "entity" in cap.params_schema
        assert "id" in cap.params_schema
        assert "include" in cap.params_schema
        assert "tenant_filter_required" in cap.default_obligations


class TestTransactionCoreCapabilities:
    """Tests cho Transaction Management Core Capabilities (3 capabilities)."""

    def test_begin_transaction_exists(self):
        """Kiểm tra begin_transaction capability tồn tại."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("begin_transaction")

        assert cap is not None
        assert cap.id == "begin_transaction"
        assert cap.name == "Begin Transaction"
        assert "isolation_level" in cap.params_schema
        assert "read_only" in cap.params_schema
        assert "transaction_started" in cap.effects

    def test_begin_transaction_isolation_levels(self):
        """Kiểm tra isolation levels của begin_transaction."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("begin_transaction")

        isolation_enum = cap.params_schema["isolation_level"]["enum"]
        assert "read_uncommitted" in isolation_enum
        assert "read_committed" in isolation_enum
        assert "repeatable_read" in isolation_enum
        assert "serializable" in isolation_enum

    def test_commit_transaction_exists(self):
        """Kiểm tra commit_transaction capability tồn tại."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("commit_transaction")

        assert cap is not None
        assert cap.id == "commit_transaction"
        assert cap.name == "Commit Transaction"
        assert "transaction_committed" in cap.effects

    def test_rollback_transaction_exists(self):
        """Kiểm tra rollback_transaction capability tồn tại."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("rollback_transaction")

        assert cap is not None
        assert cap.id == "rollback_transaction"
        assert cap.name == "Rollback Transaction"
        assert "rollback_transaction" in cap.id
        assert "transaction_rolled_back" in cap.effects


class TestEventIntegrationCoreCapabilities:
    """Tests cho Event & Integration Core Capabilities (3 capabilities)."""

    def test_publish_event_exists(self):
        """Kiểm tra publish_event capability tồn tại."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("publish_event")

        assert cap is not None
        assert cap.id == "publish_event"
        assert cap.name == "Publish Event"
        assert "event_type" in cap.params_schema
        assert "payload" in cap.params_schema
        assert "event_bus" in cap.write_access
        assert "event_published" in cap.effects

    def test_call_external_service_exists(self):
        """Kiểm tra call_external_service capability tồn tại."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("call_external_service")

        assert cap is not None
        assert cap.id == "call_external_service"
        assert cap.name == "Call External Service"
        assert "service" in cap.params_schema
        assert "method" in cap.params_schema
        assert "error_handler_required" in cap.default_obligations
        assert "timeout_required" in cap.default_obligations
        assert "retry_policy_required" in cap.default_obligations

    def test_send_notification_exists(self):
        """Kiểm tra send_notification capability tồn tại."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("send_notification")

        assert cap is not None
        assert cap.id == "send_notification"
        assert cap.name == "Send Notification"
        assert "channel" in cap.params_schema
        assert "recipient" in cap.params_schema
        assert "template" in cap.params_schema
        assert "error_handler_required" in cap.default_obligations

    def test_send_notification_channels(self):
        """Kiểm tra notification channels."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("send_notification")

        channel_enum = cap.params_schema["channel"]["enum"]
        assert "email" in channel_enum
        assert "sms" in channel_enum
        assert "push" in channel_enum
        assert "in_app" in channel_enum


class TestAuditObservabilityCoreCapabilities:
    """Tests cho Audit & Observability Core Capabilities (2 capabilities)."""

    def test_write_audit_log_exists(self):
        """Kiểm tra write_audit_log capability tồn tại."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("write_audit_log")

        assert cap is not None
        assert cap.id == "write_audit_log"
        assert cap.name == "Write Audit Log"
        assert "action" in cap.params_schema
        assert "actor" in cap.params_schema
        assert "immutable_evidence_required" in cap.default_obligations
        assert "audit_log" in cap.write_access
        assert "audit_logged" in cap.effects

    def test_write_audit_log_fields(self):
        """Kiểm tra các fields của write_audit_log."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("write_audit_log")

        assert "action" in cap.params_schema
        assert "entity" in cap.params_schema
        assert "entity_id" in cap.params_schema
        assert "actor" in cap.params_schema
        assert "before" in cap.params_schema
        assert "after" in cap.params_schema
        assert "metadata" in cap.params_schema

    def test_record_metric_exists(self):
        """Kiểm tra record_metric capability tồn tại."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("record_metric")

        assert cap is not None
        assert cap.id == "record_metric"
        assert cap.name == "Record Metric"
        assert "metric_name" in cap.params_schema
        assert "metric_type" in cap.params_schema
        assert "value" in cap.params_schema
        assert "metrics" in cap.write_access
        assert "metric_recorded" in cap.effects

    def test_record_metric_types(self):
        """Kiểm tra metric types."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("record_metric")

        type_enum = cap.params_schema["metric_type"]["enum"]
        assert "counter" in type_enum
        assert "gauge" in type_enum
        assert "histogram" in type_enum
        assert "summary" in type_enum


class TestCoreCapabilitiesRegistry:
    """Tests cho CoreCapabilitiesRegistry."""

    def test_registry_has_all_categories(self):
        """Kiểm tra registry có đầy đủ categories."""
        registry = CoreCapabilitiesRegistry()

        assert registry.auth is not None
        assert registry.data is not None
        assert registry.transaction is not None
        assert registry.event is not None
        assert registry.audit is not None

    def test_get_all_capabilities_returns_16(self):
        """Kiểm tra registry trả về đúng 16 capabilities."""
        capabilities = CoreCapabilitiesRegistry.get_all_capabilities()

        assert len(capabilities) == 16

    def test_get_capability_by_id_finds_capability(self):
        """Kiểm tra get_capability_by_id tìm thấy capability."""
        cap = CoreCapabilitiesRegistry.get_capability_by_id("authorize_permission")

        assert cap is not None
        assert isinstance(cap, CoreCapability)

    def test_get_capability_by_id_returns_none_for_unknown(self):
        """Kiểm tra get_capability_by_id trả về None cho ID không tồn tại."""
        cap = CoreCapabilitiesRegistry.get_capability_by_id("nonexistent_capability")

        assert cap is None

    def test_get_capability_ids_returns_all_ids(self):
        """Kiểm tra get_capability_ids trả về danh sách 16 IDs."""
        ids = CoreCapabilitiesRegistry.get_capability_ids()

        assert len(ids) == 16
        assert "authorize_permission" in ids
        assert "create_record" in ids
        assert "write_audit_log" in ids

    def test_get_statistics_returns_correct_structure(self):
        """Kiểm tra get_statistics trả về cấu trúc đúng."""
        stats = CoreCapabilitiesRegistry.get_statistics()

        assert "total" in stats
        assert "by_category" in stats
        assert stats["total"] == 16
        assert stats["by_category"]["authorization"] == 3
        assert stats["by_category"]["data_operations"] == 5
        assert stats["by_category"]["transaction"] == 3
        assert stats["by_category"]["event_integration"] == 3
        assert stats["by_category"]["audit_observability"] == 2

    def test_all_16_capabilities_present(self):
        """Kiểm tra tất cả 16 core capabilities đều có mặt."""
        expected_ids = [
            "authorize_permission",
            "enforce_tenant_scope",
            "validate_input",
            "create_record",
            "update_record",
            "delete_record",
            "query_records",
            "load_entity",
            "begin_transaction",
            "commit_transaction",
            "rollback_transaction",
            "publish_event",
            "call_external_service",
            "send_notification",
            "write_audit_log",
            "record_metric",
        ]

        ids = CoreCapabilitiesRegistry.get_capability_ids()

        for expected_id in expected_ids:
            assert expected_id in ids, f"Missing capability: {expected_id}"


class TestCoreCapabilitySerialization:
    """Tests cho serialization của CoreCapability."""

    def test_to_dict_contains_required_fields(self):
        """Kiểm tra to_dict chứa các fields bắt buộc."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("authorize_permission")
        cap_dict = cap.to_dict()

        assert "id" in cap_dict
        assert "name" in cap_dict
        assert "description" in cap_dict
        assert "params_schema" in cap_dict
        assert "default_obligations" in cap_dict
        assert "read_access" in cap_dict
        assert "write_access" in cap_dict
        assert "effects" in cap_dict

    def test_from_dict_creates_capability(self):
        """Kiểm tra from_dict tạo capability đúng."""
        cap_data = {
            "id": "test_capability",
            "name": "Test Capability",
            "description": "A test capability",
            "params_schema": {"test_field": {"type": "string"}},
            "default_obligations": ["test_obligation"],
            "read_access": [],
            "write_access": [],
            "effects": [],
        }

        cap = CoreCapability.from_dict(cap_data)

        assert cap.id == "test_capability"
        assert cap.name == "Test Capability"
        assert cap.description == "A test capability"
        assert "test_field" in cap.params_schema
        assert "test_obligation" in cap.default_obligations

    def test_roundtrip_serialization(self):
        """Kiểm tra serialization roundtrip."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("authorize_permission")

        cap_dict = cap.to_dict()
        reconstructed = CoreCapability.from_dict(cap_dict)

        assert reconstructed.id == cap.id
        assert reconstructed.name == cap.name
        assert reconstructed.description == cap.description
        assert reconstructed.params_schema == cap.params_schema
        assert reconstructed.default_obligations == cap.default_obligations
        assert reconstructed.read_access == cap.read_access
        assert reconstructed.write_access == cap.write_access
        assert reconstructed.effects == cap.effects


class TestCoreCapabilityObligations:
    """Tests cho obligations của core capabilities."""

    def test_authorize_permission_has_permission_check_obligation(self):
        """Kiểm tra authorize_permission có permission_check_required."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("authorize_permission")

        assert "permission_check_required" in cap.default_obligations

    def test_delete_record_has_audit_obligation(self):
        """Kiểm tra delete_record có audit_log_required."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("delete_record")

        assert "audit_log_required" in cap.default_obligations

    def test_write_audit_log_has_immutable_obligation(self):
        """Kiểm tra write_audit_log có immutable_evidence_required."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("write_audit_log")

        assert "immutable_evidence_required" in cap.default_obligations

    def test_call_external_service_has_error_handler_obligation(self):
        """Kiểm tra call_external_service có error_handler_required."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("call_external_service")

        assert "error_handler_required" in cap.default_obligations

    def test_query_records_has_tenant_filter_obligation(self):
        """Kiểm tra query_records có tenant_filter_required."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("query_records")

        assert "tenant_filter_required" in cap.default_obligations

    def test_load_entity_has_tenant_filter_obligation(self):
        """Kiểm tra load_entity có tenant_filter_required."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("load_entity")

        assert "tenant_filter_required" in cap.default_obligations


class TestCoreCapabilityAccessPatterns:
    """Tests cho access patterns (read_access, write_access, effects) của core capabilities."""

    def test_create_record_write_access(self):
        """Kiểm tra create_record có write_access database."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("create_record")

        assert "database" in cap.write_access

    def test_query_records_read_access(self):
        """Kiểm tra query_records có read_access database."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("query_records")

        assert "database" in cap.read_access

    def test_publish_event_write_access(self):
        """Kiểm tra publish_event có write_access event_bus."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("publish_event")

        assert "event_bus" in cap.write_access

    def test_write_audit_log_write_access(self):
        """Kiểm tra write_audit_log có write_access audit_log."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("write_audit_log")

        assert "audit_log" in cap.write_access

    def test_create_record_effect(self):
        """Kiểm tra create_record có effect record_created."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("create_record")

        assert "record_created" in cap.effects

    def test_begin_transaction_effect(self):
        """Kiểm tra begin_transaction có effect transaction_started."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("begin_transaction")

        assert "transaction_started" in cap.effects

    def test_commit_transaction_effect(self):
        """Kiểm tra commit_transaction có effect transaction_committed."""
        registry = CoreCapabilitiesRegistry()
        cap = registry.get_capability_by_id("commit_transaction")

        assert "transaction_committed" in cap.effects