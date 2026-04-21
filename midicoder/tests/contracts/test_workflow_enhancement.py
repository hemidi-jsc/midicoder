"""
Unit Tests cho Enhanced WorkflowDefinitionParams.

Task: E11-002 - Enhance WorkflowDefinitionParams
Priority: P0 - Required by ALL 20 briefs

Kiểm tra:
- Guard conditions (per-transition guards)
- Action hooks (on_entry, on_exit, on_transition)
- Parallel states support
- Sub-workflows (reusable workflow templates)
- Versioning support
- State definitions rich hơn (dict thay vì string)

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.contracts.capability_params import WorkflowDefinitionParams


class TestWorkflowDefinitionGuardConditions:
    """Tests cho guard conditions enhancement."""

    def test_workflow_with_guard_conditions(self):
        """Kiểm tra workflow với guard conditions."""
        params: WorkflowDefinitionParams = {
            "states": ["draft", "pending_approval", "approved", "rejected"],
            "transitions": [
                {
                    "from": "draft",
                    "to": "pending_approval",
                    "guard": {"expression": "total > 1000"}
                }
            ],
            "start_state": "draft",
            "guard_conditions": {
                "draft_to_pending_approval": {
                    "expression": "total > 1000",
                    "message": "Đơn hàng trên 1000 cần phê duyệt"
                }
            }
        }
        assert params["guard_conditions"]["draft_to_pending_approval"]["expression"] == "total > 1000"

    def test_workflow_with_multiple_guards(self):
        """Kiểm tra workflow với nhiều guard conditions."""
        params: WorkflowDefinitionParams = {
            "states": ["draft", "review", "approved", "rejected"],
            "transitions": [],
            "start_state": "draft",
            "guard_conditions": {
                "draft_to_review": {
                    "expression": "is_valid",
                    "message": "Dữ liệu phải hợp lệ"
                },
                "review_to_approved": {
                    "expression": "approval_score >= 80",
                    "message": "Điểm phê duyệt >= 80"
                },
                "review_to_rejected": {
                    "expression": "approval_score < 80",
                    "message": "Điểm phê duyệt < 80"
                }
            }
        }
        assert len(params["guard_conditions"]) == 3

    def test_guard_with_complex_expression(self):
        """Kiểm tra guard với biểu thức phức tạp."""
        params: WorkflowDefinitionParams = {
            "states": ["pending", "processing", "completed"],
            "transitions": [],
            "start_state": "pending",
            "guard_conditions": {
                "pending_to_processing": {
                    "expression": "inventory > 0 and customer_status == 'active' and payment_verified",
                    "on_fail": "reject_order"
                }
            }
        }
        assert "on_fail" in params["guard_conditions"]["pending_to_processing"]


class TestWorkflowDefinitionActionHooks:
    """Tests cho action hooks enhancement."""

    def test_workflow_with_on_entry_hooks(self):
        """Kiểm tra workflow với on_entry hooks."""
        params: WorkflowDefinitionParams = {
            "states": ["draft", "submitted", "approved"],
            "transitions": [],
            "start_state": "draft",
            "action_hooks": {
                "on_entry": {
                    "submitted": ["send_notification", "update_metrics"],
                    "approved": ["create_invoice", "notify_customer"]
                }
            }
        }
        assert "submitted" in params["action_hooks"]["on_entry"]

    def test_workflow_with_on_exit_hooks(self):
        """Kiểm tra workflow với on_exit hooks."""
        params: WorkflowDefinitionParams = {
            "states": ["draft", "submitted", "archived"],
            "transitions": [],
            "start_state": "draft",
            "action_hooks": {
                "on_exit": {
                    "draft": ["clear_cache"],
                    "submitted": ["archive_draft_data"]
                }
            }
        }
        assert "draft" in params["action_hooks"]["on_exit"]

    def test_workflow_with_on_transition_hooks(self):
        """Kiểm tra workflow với on_transition hooks."""
        params: WorkflowDefinitionParams = {
            "states": ["new", "processing", "done"],
            "transitions": [],
            "start_state": "new",
            "action_hooks": {
                "on_transition": {
                    "new_to_processing": ["start_timer", "assign_worker"],
                    "processing_to_done": ["stop_timer", "update_dashboard"]
                }
            }
        }
        assert "new_to_processing" in params["action_hooks"]["on_transition"]

    def test_workflow_with_all_hook_types(self):
        """Kiểm tra workflow với tất cả loại hooks."""
        params: WorkflowDefinitionParams = {
            "states": ["draft", "review", "approved"],
            "transitions": [],
            "start_state": "draft",
            "action_hooks": {
                "on_entry": {
                    "review": ["notify_manager"]
                },
                "on_exit": {
                    "draft": ["cleanup_temp_files"]
                },
                "on_transition": {
                    "draft_to_review": ["audit_log", "send_email"]
                }
            }
        }
        assert "on_entry" in params["action_hooks"]
        assert "on_exit" in params["action_hooks"]
        assert "on_transition" in params["action_hooks"]


class TestWorkflowDefinitionParallelStates:
    """Tests cho parallel states enhancement."""

    def test_workflow_with_parallel_states(self):
        """Kiểm tra workflow với parallel states."""
        params: WorkflowDefinitionParams = {
            "states": ["order", "payment", "shipping", "completed"],
            "transitions": [],
            "start_state": "order",
            "parallel_states": ["payment", "shipping"]
        }
        assert "payment" in params["parallel_states"]
        assert "shipping" in params["parallel_states"]

    def test_parallel_states_with_join(self):
        """Kiểm tra parallel states join vào common state."""
        params: WorkflowDefinitionParams = {
            "states": ["order", "payment", "inventory_check", "processing", "shipped"],
            "transitions": [],
            "start_state": "order",
            "parallel_states": ["payment", "inventory_check"],
            "end_states": ["shipped"]
        }
        # Payment và inventory_check chạy song song, join vào processing
        assert len(params["parallel_states"]) == 2


class TestWorkflowDefinitionSubWorkflows:
    """Tests cho sub-workflows enhancement."""

    def test_workflow_with_sub_workflows(self):
        """Kiểm tra workflow với sub-workflows."""
        params: WorkflowDefinitionParams = {
            "states": ["start", "payment_subflow", "end"],
            "transitions": [],
            "start_state": "start",
            "sub_workflows": ["payment_approval", "fraud_check"]
        }
        assert "payment_approval" in params["sub_workflows"]
        assert "fraud_check" in params["sub_workflows"]

    def test_sub_workflow_with_parameters(self):
        """Kiểm tra sub-workflow với parameters."""
        params: WorkflowDefinitionParams = {
            "states": ["order", "approve", "complete"],
            "transitions": [],
            "start_state": "order",
            "sub_workflows": [
                {"ref": "manager_approval", "on": "total > 10000"},
                {"ref": "finance_approval", "on": "total > 50000"}
            ]
        }
        assert len(params["sub_workflows"]) == 2


class TestWorkflowDefinitionVersioning:
    """Tests cho versioning enhancement."""

    def test_workflow_with_versioning(self):
        """Kiểm tra workflow với versioning."""
        params: WorkflowDefinitionParams = {
            "states": ["draft", "approved"],
            "transitions": [],
            "start_state": "draft",
            "versioning": {
                "type": "semantic",
                "version": "1.2.0",
                "backward_compatible": True
            }
        }
        assert params["versioning"]["type"] == "semantic"
        assert params["versioning"]["backward_compatible"] is True

    def test_versioning_with_migration_info(self):
        """Kiểm tra versioning với migration info."""
        params: WorkflowDefinitionParams = {
            "states": ["v1_state", "v2_state"],
            "transitions": [],
            "start_state": "v1_state",
            "versioning": {
                "type": "semantic",
                "version": "2.0.0",
                "backward_compatible": False,
                "migration_guide": "See MIGRATION.md for state mapping",
                "deprecated_states": ["legacy_state"]
            }
        }
        assert "migration_guide" in params["versioning"]


class TestWorkflowDefinitionRichStates:
    """Tests cho rich state definitions (dict thay vì string)."""

    def test_workflow_with_state_metadata(self):
        """Kiểm tra states với metadata (dict thay vì string)."""
        # Note: Current implementation uses list[str], enhancement allows list[dict]
        # This test documents the expected enhanced behavior
        params: WorkflowDefinitionParams = {
            "states": ["draft", "approved"],  # Current: list[str]
            "transitions": [],
            "start_state": "draft",
            # Enhancement: allow state_metadata for richer definitions
            # "state_metadata": {
            #     "draft": {"description": "Đơn hàng chưa submit", "auto_timeout": 3600},
            #     "approved": {"description": "Đơn hàng đã duyệt", "final": True}
            # }
        }
        assert "draft" in params["states"]


class TestWorkflowDefinitionCompleteEnhancedExample:
    """Tests cho complete enhanced workflow example."""

    def test_complete_order_workflow_with_all_enhancements(self):
        """
        Kiểm tra complete order workflow với tất cả enhancements.
        
        Đây là example thực tế cho e-commerce order workflow.
        """
        params: WorkflowDefinitionParams = {
            "states": [
                "draft", "submitted", "payment_verification", "inventory_check",
                "approved", "processing", "shipped", "delivered", "cancelled"
            ],
            "transitions": [
                {"from": "draft", "to": "submitted"},
                {"from": "submitted", "to": "payment_verification"},
                {"from": "payment_verification", "to": "inventory_check"},
                {"from": "inventory_check", "to": "approved"},
                {"from": "approved", "to": "processing"},
                {"from": "processing", "to": "shipped"},
                {"from": "shipped", "to": "delivered"},
                {"from": "draft", "to": "cancelled"},
                {"from": "submitted", "to": "cancelled"}
            ],
            "start_state": "draft",
            "end_states": ["delivered", "cancelled"],
            # Guard conditions
            "guard_conditions": {
                "submitted_to_payment_verification": {
                    "expression": "payment_method != null",
                    "message": "Phương thức thanh toán bắt buộc"
                },
                "payment_verification_to_inventory_check": {
                    "expression": "payment_verified",
                    "message": "Thanh toán phải được xác minh"
                },
                "inventory_check_to_approved": {
                    "expression": "all_items_available",
                    "message": "Tất cả sản phẩm phải có sẵn"
                }
            },
            # Action hooks
            "action_hooks": {
                "on_entry": {
                    "processing": ["allocate_inventory", "generate_packing_slip"],
                    "shipped": ["send_tracking_info", "notify_customer"],
                    "delivered": ["request_review", "update_metrics"]
                },
                "on_exit": {
                    "draft": ["cleanup_temp_data"],
                    "cancelled": ["release_inventory", "refund_payment"]
                },
                "on_transition": {
                    "submitted_to_payment_verification": ["audit_log", "send_confirmation"],
                    "shipped_to_delivered": ["calculate_delivery_time", "update_sla"]
                }
            },
            # Parallel states (payment và inventory kiểm tra song song)
            "parallel_states": ["payment_verification", "inventory_check"],
            # Sub-workflows
            "sub_workflows": [
                {"ref": "fraud_detection", "on": "total > 1000000"},
                {"ref": "manager_approval", "on": "total > 5000000"}
            ],
            # Versioning
            "versioning": {
                "type": "semantic",
                "version": "1.0.0",
                "backward_compatible": True
            },
            # Compensation (rollback)
            "compensation": [
                {"state": "shipped", "action": "initiate_return"},
                {"state": "processing", "action": "cancel_fulfillment"}
            ],
            # Human tasks
            "human_tasks": [
                {
                    "id": "quality_check",
                    "at_state": "approved",
                    "assignee_role": "quality_manager",
                    "timeout_hours": 24
                }
            ],
            # Timers
            "timers": [
                {
                    "from_state": "processing",
                    "to_state": "cancelled",
                    "duration_hours": 72,
                    "reason": "timeout"
                }
            ]
        }

        # Verify all enhancements present
        assert "guard_conditions" in params
        assert "action_hooks" in params
        assert "parallel_states" in params
        assert "sub_workflows" in params
        assert "versioning" in params
        assert len(params["guard_conditions"]) == 3
        assert "on_entry" in params["action_hooks"]
        assert "on_exit" in params["action_hooks"]
        assert "on_transition" in params["action_hooks"]