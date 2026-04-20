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


class TestDomainMacroCapabilitiesExtended:
    """
    Tests cho extended domain macro capabilities (Layer 2 - Priority Industries).
    
    Theo MACRO_CAPABILITIES_GAP.md, coverage 20 priority industries.
    """

    # ==================== ECOMMERCE D2C ====================

    def test_ecommerce_apply_promotion_exists(self):
        """Kiểm tra apply_promotion (Ecommerce D2C) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("apply_promotion")
        
        assert macro is not None
        assert macro.id == "apply_promotion"
        assert "validate_input" in macro.expands_to
        assert "update_record" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    def test_ecommerce_process_refund_exists(self):
        """Kiểm tra process_refund (Ecommerce D2C) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("process_refund")
        
        assert macro is not None
        assert macro.id == "process_refund"
        assert "authorize_permission" in macro.expands_to
        assert "begin_transaction" in macro.expands_to
        assert "commit_transaction" in macro.expands_to
        assert "transaction_required" in macro.default_obligations
        assert "audit_log_required" in macro.default_obligations
        assert "pci_dss_compliant" in macro.default_obligations

    def test_ecommerce_manage_subscription_exists(self):
        """Kiểm tra manage_subscription (Ecommerce D2C) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("manage_subscription")
        
        assert macro is not None
        assert macro.id == "manage_subscription"
        # State machine transition đã được expand về core capabilities
        assert "update_record" in macro.expands_to
        assert "send_notification" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    def test_ecommerce_recommend_products_exists(self):
        """Kiểm tra recommend_products (Ecommerce D2C) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("recommend_products")
        
        assert macro is not None
        assert macro.id == "recommend_products"
        assert "query_records" in macro.expands_to
        assert "call_external_service" in macro.expands_to
        assert "tenant_filter_required" in macro.default_obligations

    # ==================== MARKETPLACE B2C ====================

    def test_marketplace_onboard_seller_exists(self):
        """Kiểm tra onboard_seller (Marketplace B2C) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("onboard_seller")
        
        assert macro is not None
        assert macro.id == "onboard_seller"
        assert "validate_input" in macro.expands_to
        assert "call_external_service" in macro.expands_to
        assert "kyc_verified" in macro.default_obligations
        assert "audit_log_required" in macro.default_obligations

    def test_marketplace_hold_escrow_payment_exists(self):
        """Kiểm tra hold_escrow_payment (Marketplace B2C) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("hold_escrow_payment")
        
        assert macro is not None
        assert macro.id == "hold_escrow_payment"
        assert "begin_transaction" in macro.expands_to
        assert "double_entry_balanced" in macro.default_obligations
        assert "audit_log_required" in macro.default_obligations

    def test_marketplace_split_payment_exists(self):
        """Kiểm tra split_payment (Marketplace B2C) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("split_payment")
        
        assert macro is not None
        assert macro.id == "split_payment"
        assert "call_external_service" in macro.expands_to
        assert "double_entry_balanced" in macro.default_obligations
        assert "pci_dss_compliant" in macro.default_obligations

    def test_marketplace_resolve_dispute_exists(self):
        """Kiểm tra resolve_dispute (Marketplace B2C) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("resolve_dispute")
        
        assert macro is not None
        assert macro.id == "resolve_dispute"
        # approval_workflow đã expand về core
        assert "update_record" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    def test_marketplace_rate_review_exists(self):
        """Kiểm tra rate_review (Marketplace B2C) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("rate_review")
        
        assert macro is not None
        assert macro.id == "rate_review"
        assert "authorize_permission" in macro.expands_to
        assert "create_record" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    # ==================== MARKETPLACE B2B ====================

    def test_marketplace_rfp_exists(self):
        """Kiểm tra create_rfp (Marketplace B2B) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("create_rfp")
        
        assert macro is not None
        assert macro.id == "create_rfp"
        assert "authorize_permission" in macro.expands_to
        assert "create_record" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    def test_marketplace_credit_terms_exists(self):
        """Kiểm tra manage_credit_terms (Marketplace B2B) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("manage_credit_terms")
        
        assert macro is not None
        assert macro.id == "manage_credit_terms"
        assert "authorize_permission" in macro.expands_to
        assert "call_external_service" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    def test_marketplace_bulk_pricing_exists(self):
        """Kiểm tra apply_bulk_pricing (Marketplace B2B) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("apply_bulk_pricing")
        
        assert macro is not None
        assert macro.id == "apply_bulk_pricing"
        assert "validate_input" in macro.expands_to
        assert "tenant_filter_required" in macro.default_obligations

    def test_marketplace_po_integration_exists(self):
        """Kiểm tra process_purchase_order (Marketplace B2B) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("process_purchase_order")
        
        assert macro is not None
        assert macro.id == "process_purchase_order"
        assert "validate_input" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    # ==================== FOOD DELIVERY ====================

    def test_food_delivery_assign_driver_exists(self):
        """Kiểm tra assign_delivery_driver (Food Delivery) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("assign_delivery_driver")
        
        assert macro is not None
        assert macro.id == "assign_delivery_driver"
        assert "authorize_permission" in macro.expands_to
        assert "query_records" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    def test_food_delivery_calculate_route_exists(self):
        """Kiểm tra calculate_delivery_route (Food Delivery) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("calculate_delivery_route")
        
        assert macro is not None
        assert macro.id == "calculate_delivery_route"
        assert "call_external_service" in macro.expands_to
        assert "tenant_filter_required" in macro.default_obligations

    def test_food_delivery_track_location_exists(self):
        """Kiểm tra track_realtime_location (Food Delivery) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("track_realtime_location")
        
        assert macro is not None
        assert macro.id == "track_realtime_location"
        assert "update_record" in macro.expands_to
        assert "publish_event" in macro.expands_to
        assert "tenant_filter_required" in macro.default_obligations

    def test_food_delivery_process_tip_exists(self):
        """Kiểm tra process_tip (Food Delivery) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("process_tip")
        
        assert macro is not None
        assert macro.id == "process_tip"
        assert "create_record" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    # ==================== WAREHOUSE MANAGEMENT ====================

    def test_warehouse_receive_inventory_exists(self):
        """Kiểm tra receive_inventory (Warehouse) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("receive_inventory")
        
        assert macro is not None
        assert macro.id == "receive_inventory"
        assert "begin_transaction" in macro.expands_to
        assert "transaction_required" in macro.default_obligations
        assert "audit_log_required" in macro.default_obligations

    def test_warehouse_pick_pack_ship_exists(self):
        """Kiểm tra pick_pack_ship (Warehouse) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("pick_pack_ship")
        
        assert macro is not None
        assert macro.id == "pick_pack_ship"
        assert "authorize_permission" in macro.expands_to
        assert "transaction_required" in macro.default_obligations
        assert "audit_log_required" in macro.default_obligations

    def test_warehouse_cycle_count_exists(self):
        """Kiểm tra cycle_count (Warehouse) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("cycle_count")
        
        assert macro is not None
        assert macro.id == "cycle_count"
        assert "authorize_permission" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    def test_warehouse_bin_transfer_exists(self):
        """Kiểm tra bin_transfer (Warehouse) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("bin_transfer")
        
        assert macro is not None
        assert macro.id == "bin_transfer"
        assert "begin_transaction" in macro.expands_to
        assert "transaction_required" in macro.default_obligations
        assert "audit_log_required" in macro.default_obligations

    def test_warehouse_manage_bin_location_exists(self):
        """Kiểm tra manage_bin_location (Warehouse) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("manage_bin_location")
        
        assert macro is not None
        assert macro.id == "manage_bin_location"
        assert "create_record" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    # ==================== PROCUREMENT SRM ====================

    def test_procurement_create_rfq_exists(self):
        """Kiểm tra create_rfq (Procurement) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("create_rfq")
        
        assert macro is not None
        assert macro.id == "create_rfq"
        assert "authorize_permission" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    def test_procurement_evaluate_vendor_exists(self):
        """Kiểm tra evaluate_vendor (Procurement) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("evaluate_vendor")
        
        assert macro is not None
        assert macro.id == "evaluate_vendor"
        # aggregate_query là macro, đã expand về core
        assert "query_records" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    def test_procurement_manage_contract_exists(self):
        """Kiểm tra manage_contract (Procurement) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("manage_contract")
        
        assert macro is not None
        assert macro.id == "manage_contract"
        assert "authorize_permission" in macro.expands_to
        assert "immutable_evidence_required" in macro.default_obligations

    def test_procurement_spend_analysis_exists(self):
        """Kiểm tra spend_analysis (Procurement) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("spend_analysis")
        
        assert macro is not None
        assert macro.id == "spend_analysis"
        # aggregate_query là macro, đã expand về core
        assert "query_records" in macro.expands_to
        assert "tenant_filter_required" in macro.default_obligations

    def test_procurement_supplier_onboarding_exists(self):
        """Kiểm tra supplier_onboarding (Procurement) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("supplier_onboarding")
        
        assert macro is not None
        assert macro.id == "supplier_onboarding"
        assert "validate_input" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    # ==================== CRM PLATFORM ====================

    def test_crm_create_lead_exists(self):
        """Kiểm tra create_lead (CRM) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("create_lead")
        
        assert macro is not None
        assert macro.id == "create_lead"
        assert "validate_input" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    def test_crm_convert_opportunity_exists(self):
        """Kiểm tra convert_opportunity (CRM) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("convert_opportunity")
        
        assert macro is not None
        assert macro.id == "convert_opportunity"
        assert "authorize_permission" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    def test_crm_log_activity_exists(self):
        """Kiểm tra log_activity (CRM) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("log_activity")
        
        assert macro is not None
        assert macro.id == "log_activity"
        assert "create_record" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    def test_crm_run_campaign_exists(self):
        """Kiểm tra run_campaign (CRM) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("run_campaign")
        
        assert macro is not None
        assert macro.id == "run_campaign"
        assert "authorize_permission" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    def test_crm_case_escalation_exists(self):
        """Kiểm tra case_escalation (CRM) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("case_escalation")
        
        assert macro is not None
        assert macro.id == "case_escalation"
        assert "sla_breach_check" in macro.default_obligations

    # ==================== ERP FINANCE ====================

    def test_erp_post_journal_entry_exists(self):
        """Kiểm tra post_journal_entry (ERP Finance) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("post_journal_entry")
        
        assert macro is not None
        assert macro.id == "post_journal_entry"
        assert "authorize_permission" in macro.expands_to
        assert "transaction_required" in macro.default_obligations
        assert "double_entry_balanced" in macro.default_obligations

    def test_erp_reconcile_accounts_exists(self):
        """Kiểm tra reconcile_accounts (ERP Finance) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("reconcile_accounts")
        
        assert macro is not None
        assert macro.id == "reconcile_accounts"
        assert "authorize_permission" in macro.expands_to
        assert "double_entry_balanced" in macro.default_obligations

    def test_erp_close_period_exists(self):
        """Kiểm tra close_period (ERP Finance) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("close_period")
        
        assert macro is not None
        assert macro.id == "close_period"
        assert "authorize_permission" in macro.expands_to
        assert "immutable_evidence_required" in macro.default_obligations

    def test_erp_consolidate_entities_exists(self):
        """Kiểm tra consolidate_entities (ERP Finance) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("consolidate_entities")
        
        assert macro is not None
        assert macro.id == "consolidate_entities"
        # aggregate_query là macro, đã expand về core
        assert "query_records" in macro.expands_to
        assert "double_entry_balanced" in macro.default_obligations

    def test_erp_fixed_asset_capitalization_exists(self):
        """Kiểm tra fixed_asset_capitalization (ERP Finance) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("fixed_asset_capitalization")
        
        assert macro is not None
        assert macro.id == "fixed_asset_capitalization"
        # create_ledger_entry là macro, đã expand về core
        assert "validate_input" in macro.expands_to
        assert "create_record" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    # ==================== ITSM HELPDESK ====================

    def test_itsm_create_ticket_exists(self):
        """Kiểm tra create_ticket (ITSM) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("create_ticket")
        
        assert macro is not None
        assert macro.id == "create_ticket"
        assert "validate_input" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    def test_itsm_approve_change_exists(self):
        """Kiểm tra approve_change (ITSM) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("approve_change")
        
        assert macro is not None
        assert macro.id == "approve_change"
        assert "audit_log_required" in macro.default_obligations

    def test_itsm_publish_kb_article_exists(self):
        """Kiểm tra publish_kb_article (ITSM) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("publish_kb_article")
        
        assert macro is not None
        assert macro.id == "publish_kb_article"
        assert "authorize_permission" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    def test_itsm_escalate_ticket_exists(self):
        """Kiểm tra escalate_ticket (ITSM) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("escalate_ticket")
        
        assert macro is not None
        assert macro.id == "escalate_ticket"
        assert "sla_breach_check" in macro.default_obligations

    # ==================== EXCHANGE TRADING ====================

    def test_exchange_match_orders_exists(self):
        """Kiểm tra match_orders (Exchange Trading) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("match_orders")
        
        assert macro is not None
        assert macro.id == "match_orders"
        assert "validate_input" in macro.expands_to
        assert "begin_transaction" in macro.expands_to
        assert "double_entry_balanced" in macro.default_obligations
        assert "audit_log_required" in macro.default_obligations

    def test_exchange_clear_settlement_exists(self):
        """Kiểm tra clear_settlement (Exchange Trading) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("clear_settlement")
        
        assert macro is not None
        assert macro.id == "clear_settlement"
        assert "begin_transaction" in macro.expands_to
        assert "commit_transaction" in macro.expands_to
        assert "double_entry_balanced" in macro.default_obligations
        assert "audit_log_required" in macro.default_obligations

    def test_exchange_calculate_margin_exists(self):
        """Kiểm tra calculate_margin (Exchange Trading) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("calculate_margin")
        
        assert macro is not None
        assert macro.id == "calculate_margin"
        # aggregate_query là macro, đã expand về core
        assert "query_records" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    def test_exchange_surveillance_check_exists(self):
        """Kiểm tra surveillance_check (Exchange Trading) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("surveillance_check")
        
        assert macro is not None
        assert macro.id == "surveillance_check"
        assert "query_records" in macro.expands_to
        assert "immutable_evidence_required" in macro.default_obligations

    # ==================== PAYROLL BENEFITS ====================

    def test_payroll_process_run_exists(self):
        """Kiểm tra process_payroll_run (Payroll) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("process_payroll_run")
        
        assert macro is not None
        assert macro.id == "process_payroll_run"
        assert "authorize_permission" in macro.expands_to
        assert "transaction_required" in macro.default_obligations
        assert "tax_calculation_required" in macro.default_obligations

    def test_payroll_file_tax_returns_exists(self):
        """Kiểm tra file_tax_returns (Payroll) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("file_tax_returns")
        
        assert macro is not None
        assert macro.id == "file_tax_returns"
        assert "authorize_permission" in macro.expands_to
        assert "immutable_evidence_required" in macro.default_obligations

    def test_payroll_enroll_benefits_exists(self):
        """Kiểm tra enroll_benefits (Payroll) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("enroll_benefits")
        
        assert macro is not None
        assert macro.id == "enroll_benefits"
        assert "validate_input" in macro.expands_to
        assert "audit_log_required" in macro.default_obligations

    def test_payroll_process_garnishment_exists(self):
        """Kiểm tra process_garnishment (Payroll) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("process_garnishment")
        
        assert macro is not None
        assert macro.id == "process_garnishment"
        assert "authorize_permission" in macro.expands_to
        assert "immutable_evidence_required" in macro.default_obligations

    # ==================== HEALTHCARE HOSPITAL IS ====================

    def test_healthcare_admit_patient_exists(self):
        """Kiểm tra admit_patient (Healthcare) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("admit_patient")
        
        assert macro is not None
        assert macro.id == "admit_patient"
        assert "authorize_permission" in macro.expands_to
        assert "create_record" in macro.expands_to
        # State machine transition đã được expand về core capabilities
        assert "update_record" in macro.expands_to
        assert "hipaa_encryption" in macro.default_obligations

    def test_healthcare_enter_medical_order_exists(self):
        """Kiểm tra enter_medical_order (Healthcare) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("enter_medical_order")
        
        assert macro is not None
        assert macro.id == "enter_medical_order"
        assert "authorize_permission" in macro.expands_to
        assert "create_record" in macro.expands_to
        assert "call_external_service" in macro.expands_to
        assert "hipaa_encryption" in macro.default_obligations

    def test_healthcare_document_clinical_note_exists(self):
        """Kiểm tra document_clinical_note (Healthcare) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("document_clinical_note")
        
        assert macro is not None
        assert macro.id == "document_clinical_note"
        assert "authorize_permission" in macro.expands_to
        assert "create_record" in macro.expands_to
        assert "hipaa_encryption" in macro.default_obligations
        assert "phi_access_logged" in macro.default_obligations

    def test_healthcare_manage_bed_exists(self):
        """Kiểm tra manage_bed (Healthcare) macro tồn tại."""
        registry = MacroCapabilitiesRegistry()
        macro = registry.get_macro_by_id("manage_bed")
        
        assert macro is not None
        assert macro.id == "manage_bed"
        # State machine transition đã được expand về core capabilities
        assert "update_record" in macro.expands_to
        assert "publish_event" in macro.expands_to


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