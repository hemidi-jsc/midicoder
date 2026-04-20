"""
Unit Tests cho Macro Capabilities Registry.

Kiểm tra:
- 50+ macro capabilities được định nghĩa đầy đủ
- Mỗi macro có expands_to list hợp lệ (chỉ chứa core capability IDs)
- Params schema hợp lệ cho mỗi macro
- Default obligations được set đúng
- Macro categories đầy đủ (base, mutation, query, workflow, domain, regulatory)

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.contracts.macro_capabilities import (
    MacroCapabilitiesRegistry,
    BaseMacroCapabilities,
    MutationMacroCapabilities,
    QueryMacroCapabilities,
    WorkflowMacroCapabilities,
    DomainMacroCapabilities,
    RegulatoryMacroCapabilities,
)
from midicoder.contracts.graph import MacroCapability


class TestBaseMacroCapabilities:
    """Tests cho base macro capabilities."""

    def test_authorized_mutation_exists(self):
        """Kiểm tra authorized_mutation macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("authorized_mutation")
        
        assert macro is not None
        assert macro.id == "authorized_mutation"
        assert "authorize_permission" in macro.expands_to
        assert "enforce_tenant_scope" in macro.expands_to
        assert "begin_transaction" in macro.expands_to
        assert "commit_transaction" in macro.expands_to

    def test_authorized_query_exists(self):
        """Kiểm tra authorized_query macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("authorized_query")
        
        assert macro is not None
        assert macro.id == "authorized_query"
        assert "authorize_permission" in macro.expands_to
        assert "enforce_tenant_scope" in macro.expands_to
        assert "query_records" in macro.expands_to

    def test_event_handler_exists(self):
        """Kiểm tra event_handler macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("event_handler")
        
        assert macro is not None
        assert macro.id == "event_handler"
        assert "validate_input" in macro.expands_to

    def test_workflow_definition_exists(self):
        """Kiểm tra workflow_definition macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("workflow_definition")
        
        assert macro is not None
        assert macro.id == "workflow_definition"

    def test_cascade_mutation_exists(self):
        """Kiểm tra cascade_mutation macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("cascade_mutation")
        
        assert macro is not None
        assert "begin_transaction" in macro.expands_to
        assert "commit_transaction" in macro.expands_to

    def test_aggregate_operation_exists(self):
        """Kiểm tra aggregate_operation macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("aggregate_operation")
        
        assert macro is not None
        assert macro.id == "aggregate_operation"


class TestMutationMacroCapabilities:
    """Tests cho mutation macro capabilities."""

    def test_create_with_audit_exists(self):
        """Kiểm tra create_with_audit macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("create_with_audit")
        
        assert macro is not None
        assert "write_audit_log" in macro.expands_to
        assert "create_record" in macro.expands_to

    def test_update_with_validation_exists(self):
        """Kiểm tra update_with_validation macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("update_with_validation")
        
        assert macro is not None
        assert "validate_input" in macro.expands_to
        assert "update_record" in macro.expands_to

    def test_soft_delete_with_audit_exists(self):
        """Kiểm tra soft_delete_with_audit macro tồn tại.
        
        Lưu ý: Soft delete dùng update_record để set deleted flag, không dùng delete_record.
        """
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("soft_delete_with_audit")
        
        assert macro is not None
        # Soft delete dùng update_record để set deleted_at field
        assert "update_record" in macro.expands_to
        assert "write_audit_log" in macro.expands_to

    def test_bulk_create_exists(self):
        """Kiểm tra bulk_create macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("bulk_create")
        
        assert macro is not None
        assert "begin_transaction" in macro.expands_to
        assert "create_record" in macro.expands_to

    def test_upsert_record_exists(self):
        """Kiểm tra upsert_record macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("upsert_record")
        
        assert macro is not None
        assert macro.id == "upsert_record"


class TestQueryMacroCapabilities:
    """Tests cho query macro capabilities."""

    def test_paginated_query_exists(self):
        """Kiểm tra paginated_query macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("paginated_query")
        
        assert macro is not None
        assert "query_records" in macro.expands_to

    def test_search_query_exists(self):
        """Kiểm tra search_query macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("search_query")
        
        assert macro is not None
        assert "query_records" in macro.expands_to

    def test_aggregate_query_exists(self):
        """Kiểm tra aggregate_query macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("aggregate_query")
        
        assert macro is not None
        assert macro.id == "aggregate_query"

    def test_load_with_relations_exists(self):
        """Kiểm tra load_with_relations macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("load_with_relations")
        
        assert macro is not None
        assert "load_entity" in macro.expands_to


class TestWorkflowMacroCapabilities:
    """Tests cho workflow macro capabilities."""

    def test_state_machine_transition_exists(self):
        """Kiểm tra state_machine_transition macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("state_machine_transition")
        
        assert macro is not None
        assert "update_record" in macro.expands_to
        assert "publish_event" in macro.expands_to

    def test_async_job_exists(self):
        """Kiểm tra async_job macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("async_job")
        
        assert macro is not None
        assert macro.id == "async_job"

    def test_saga_orchestration_exists(self):
        """Kiểm tra saga_orchestration macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("saga_orchestration")
        
        assert macro is not None
        assert "begin_transaction" in macro.expands_to
        assert "publish_event" in macro.expands_to

    def test_approval_workflow_exists(self):
        """Kiểm tra approval_workflow macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("approval_workflow")
        
        assert macro is not None
        assert macro.id == "approval_workflow"


class TestDomainMacroCapabilities:
    """Tests cho domain-specific macro capabilities."""

    def test_commerce_create_order_exists(self):
        """Kiểm tra create_order (Commerce) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("create_order")
        
        assert macro is not None
        assert "create_record" in macro.expands_to
        assert "publish_event" in macro.expands_to

    def test_commerce_update_inventory_exists(self):
        """Kiểm tra update_inventory (Commerce) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("update_inventory")
        
        assert macro is not None
        assert "update_record" in macro.expands_to

    def test_banking_transfer_funds_exists(self):
        """Kiểm tra transfer_funds (Banking) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("transfer_funds")
        
        assert macro is not None
        assert "begin_transaction" in macro.expands_to
        assert "create_record" in macro.expands_to
        assert "double_entry_balanced" in macro.default_obligations

    def test_banking_create_ledger_entry_exists(self):
        """Kiểm tra create_ledger_entry (Banking) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("create_ledger_entry")
        
        assert macro is not None
        assert "create_record" in macro.expands_to

    def test_healthcare_create_patient_record_exists(self):
        """Kiểm tra create_patient_record (Healthcare) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("create_patient_record")
        
        assert macro is not None
        assert "hipaa_encryption" in macro.default_obligations

    def test_healthcare_prescribe_medication_exists(self):
        """Kiểm tra prescribe_medication (Healthcare) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("prescribe_medication")
        
        assert macro is not None
        assert macro.id == "prescribe_medication"


class TestRegulatoryMacroCapabilities:
    """Tests cho regulatory compliance macro capabilities."""

    def test_kyc_verification_exists(self):
        """Kiểm tra kyc_verification (AML/KYC) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("kyc_verification")
        
        assert macro is not None
        assert "kyc_verified" in macro.default_obligations

    def test_pii_encryption_exists(self):
        """Kiểm tra pii_encryption (Privacy) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("pii_encryption")
        
        assert macro is not None
        assert "encryption_required" in macro.default_obligations

    def test_immutable_audit_exists(self):
        """Kiểm tra immutable_audit (Audit Evidence) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("immutable_audit")
        
        assert macro is not None
        assert "immutable_evidence_required" in macro.default_obligations

    def test_data_retention_exists(self):
        """Kiểm tra data_retention (Privacy) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("data_retention")
        
        assert macro is not None
        assert macro.id == "data_retention"

    def test_sanctions_screening_exists(self):
        """Kiểm tra sanctions_screening (AML/KYC) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("sanctions_screening")
        
        assert macro is not None
        assert macro.id == "sanctions_screening"


class TestMacroCapabilitiesRegistry:
    """Tests cho MacroCapabilitiesRegistry."""

    def test_registry_has_all_categories(self):
        """Kiểm tra registry có đầy đủ categories."""
        registry = MacroCapabilitiesRegistry()
        
        assert registry.base is not None
        assert registry.mutation is not None
        assert registry.query is not None
        assert registry.workflow is not None
        assert registry.domain is not None
        assert registry.regulatory is not None

    def test_get_all_macros_returns_50_plus(self):
        """Kiểm tra registry trả về ít nhất 50 macros."""
        macros = MacroCapabilitiesRegistry.get_all_macros()
        
        assert len(macros) >= 50

    def test_get_macro_by_id_finds_macro(self):
        """Kiểm tra get_macro_by_id tìm thấy macro."""
        macro = MacroCapabilitiesRegistry.get_macro_by_id("authorized_mutation")
        
        assert macro is not None
        assert isinstance(macro, MacroCapability)

    def test_get_macro_by_id_returns_none_for_unknown(self):
        """Kiểm tra get_macro_by_id trả về None cho ID không tồn tại."""
        macro = MacroCapabilitiesRegistry.get_macro_by_id("nonexistent_macro")
        
        assert macro is None

    def test_get_macro_ids_returns_all_ids(self):
        """Kiểm tra get_macro_ids trả về danh sách IDs."""
        ids = MacroCapabilitiesRegistry.get_macro_ids()
        
        assert len(ids) >= 50
        assert "authorized_mutation" in ids
        assert "authorized_query" in ids

    def test_get_statistics_returns_correct_structure(self):
        """Kiểm tra get_statistics trả về cấu trúc đúng."""
        stats = MacroCapabilitiesRegistry.get_statistics()
        
        assert "total" in stats
        assert "by_category" in stats
        assert stats["total"] >= 50

    def test_all_macros_expand_to_valid_core_capabilities(self):
        """Kiểm tra tất cả macros expand về core capabilities hợp lệ."""
        from midicoder.contracts.core_capabilities import CoreCapabilitiesRegistry
        
        core_ids = set(CoreCapabilitiesRegistry.get_capability_ids())
        macros = MacroCapabilitiesRegistry.get_all_macros()
        
        for macro in macros:
            for expand_id in macro.expands_to:
                assert expand_id in core_ids, \
                    f"Macro {macro.id} expands to unknown core capability: {expand_id}"

    def test_macro_categories_have_expected_counts(self):
        """Kiểm tra số lượng macros trong mỗi category."""
        stats = MacroCapabilitiesRegistry.get_statistics()
        by_category = stats["by_category"]
        
        # Base should have at least 4 macros
        assert by_category.get("base", 0) >= 4
        
        # Mutation should have at least 5 macros
        assert by_category.get("mutation", 0) >= 5
        
        # Query should have at least 4 macros
        assert by_category.get("query", 0) >= 4
        
        # Workflow should have at least 4 macros
        assert by_category.get("workflow", 0) >= 4
        
        # Domain should have at least 10 macros
        assert by_category.get("domain", 0) >= 10
        
        # Regulatory should have at least 8 macros
        assert by_category.get("regulatory", 0) >= 8


class TestMacroCapabilitySerialization:
    """Tests cho serialization của MacroCapability."""

    def test_to_dict_contains_required_fields(self):
        """Kiểm tra to_dict chứa các fields bắt buộc."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("authorized_mutation")
        macro_dict = macro.to_dict()
        
        assert "id" in macro_dict
        assert "name" in macro_dict
        assert "expands_to" in macro_dict
        assert "params_schema" in macro_dict
        assert "default_obligations" in macro_dict

    def test_from_dict_creates_macro(self):
        """Kiểm tra from_dict tạo macro đúng."""
        macro_data = {
            "id": "test_macro",
            "name": "Test Macro",
            "description": "A test macro",
            "expands_to": ["validate_input", "create_record"],
            "params_schema": {"test_field": {"type": "string"}},
            "default_obligations": ["test_obligation"],
        }
        
        macro = MacroCapability.from_dict(macro_data)
        
        assert macro.id == "test_macro"
        assert macro.name == "Test Macro"
        assert macro.description == "A test macro"
        assert "validate_input" in macro.expands_to
        assert "test_obligation" in macro.default_obligations

    def test_roundtrip_serialization(self):
        """Kiểm tra serialization roundtrip."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("authorized_mutation")
        
        macro_dict = macro.to_dict()
        reconstructed = MacroCapability.from_dict(macro_dict)
        
        assert reconstructed.id == macro.id
        assert reconstructed.name == macro.name
        assert reconstructed.expands_to == macro.expands_to
        assert reconstructed.default_obligations == macro.default_obligations