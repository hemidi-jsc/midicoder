"""
Unit Tests for Capability Validation

Test cases for capability params validation.
"""

import pytest

from midicoder.errors import MidicoderError
from midicoder.contracts import (
    validate_capability_params,
    get_known_capability_types,
    CAPABILITY_VALIDATORS,
)


class TestGetKnownCapabilityTypes:
    """Tests for get_known_capability_types function."""

    def test_returns_list(self):
        """Test that function returns a list."""
        result = get_known_capability_types()
        assert isinstance(result, list)

    def test_not_empty(self):
        """Test that there are known capability types."""
        result = get_known_capability_types()
        assert len(result) > 0

    def test_contains_core_types(self):
        """Test that core capability types are present."""
        result = get_known_capability_types()
        assert "authorized_mutation" in result
        assert "authorized_query" in result
        assert "event_handler" in result
        assert "scheduled_task" in result
        assert "workflow_definition" in result


class TestAuthorizedMutationValidation:
    """Tests for authorized_mutation validation."""

    def test_valid_params(self):
        """Test valid authorized_mutation params."""
        params = {
            "actor_role": "staff",
            "permission": "order.create",
            "writes": ["Order", "OrderItem"],
            "tenant_scope": "tenant_isolated",
        }
        errors = validate_capability_params("authorized_mutation", params)
        assert errors == []

    def test_missing_actor_role(self):
        """Test missing actor_role."""
        params = {
            "permission": "order.create",
            "writes": ["Order"],
            "tenant_scope": "tenant_isolated",
        }
        errors = validate_capability_params(
            "authorized_mutation", params, raise_on_error=False
        )
        assert any("actor_role" in e for e in errors)

    def test_missing_actor_role_raises(self):
        """Test missing actor_role raises exception with default raise_on_error=True."""
        params = {
            "permission": "order.create",
            "writes": ["Order"],
            "tenant_scope": "tenant_isolated",
        }
        with pytest.raises(MidicoderError) as exc_info:
            validate_capability_params("authorized_mutation", params)
        assert "actor_role" in str(exc_info.value)

    def test_empty_actor_role(self):
        """Test empty actor_role."""
        params = {
            "actor_role": "",
            "permission": "order.create",
            "writes": ["Order"],
            "tenant_scope": "tenant_isolated",
        }
        errors = validate_capability_params(
            "authorized_mutation", params, raise_on_error=False
        )
        assert any("actor_role" in e for e in errors)

    def test_missing_permission(self):
        """Test missing permission."""
        params = {
            "actor_role": "staff",
            "writes": ["Order"],
            "tenant_scope": "tenant_isolated",
        }
        errors = validate_capability_params(
            "authorized_mutation", params, raise_on_error=False
        )
        assert any("permission" in e for e in errors)

    def test_empty_writes(self):
        """Test empty writes list."""
        params = {
            "actor_role": "staff",
            "permission": "order.create",
            "writes": [],
            "tenant_scope": "tenant_isolated",
        }
        errors = validate_capability_params(
            "authorized_mutation", params, raise_on_error=False
        )
        assert any("writes" in e for e in errors)

    def test_invalid_tenant_scope(self):
        """Test invalid tenant_scope value."""
        params = {
            "actor_role": "staff",
            "permission": "order.create",
            "writes": ["Order"],
            "tenant_scope": "invalid_scope",
        }
        errors = validate_capability_params(
            "authorized_mutation", params, raise_on_error=False
        )
        assert any("tenant_scope" in e for e in errors)

    def test_valid_tenant_scopes(self):
        """Test all valid tenant_scope values."""
        valid_scopes = ["global", "tenant_isolated", "tenant_leaked"]
        for scope in valid_scopes:
            params = {
                "actor_role": "staff",
                "permission": "order.create",
                "writes": ["Order"],
                "tenant_scope": scope,
            }
            errors = validate_capability_params("authorized_mutation", params)
            assert "tenant_scope" not in str(errors), f"Failed for scope: {scope}"

    def test_invalid_transaction(self):
        """Test invalid transaction value."""
        params = {
            "actor_role": "staff",
            "permission": "order.create",
            "writes": ["Order"],
            "tenant_scope": "tenant_isolated",
            "transaction": "invalid",
        }
        errors = validate_capability_params(
            "authorized_mutation", params, raise_on_error=False
        )
        assert any("transaction" in e for e in errors)

    def test_valid_transactions(self):
        """Test all valid transaction values."""
        valid_transactions = ["required", "allowed", "forbidden"]
        for txn in valid_transactions:
            params = {
                "actor_role": "staff",
                "permission": "order.create",
                "writes": ["Order"],
                "tenant_scope": "tenant_isolated",
                "transaction": txn,
            }
            errors = validate_capability_params("authorized_mutation", params)
            assert errors == [], f"Failed for transaction: {txn}"


class TestAuthorizedQueryValidation:
    """Tests for authorized_query validation."""

    def test_valid_params(self):
        """Test valid authorized_query params."""
        params = {
            "reads": ["Order", "Customer"],
        }
        errors = validate_capability_params("authorized_query", params)
        assert errors == []

    def test_missing_reads(self):
        """Test missing reads."""
        params = {}
        errors = validate_capability_params(
            "authorized_query", params, raise_on_error=False
        )
        assert any("reads" in e for e in errors)

    def test_empty_reads(self):
        """Test empty reads list."""
        params = {"reads": []}
        errors = validate_capability_params(
            "authorized_query", params, raise_on_error=False
        )
        assert any("reads" in e for e in errors)

    def test_valid_tenant_scope(self):
        """Test with valid tenant_scope."""
        params = {
            "reads": ["Order"],
            "tenant_scope": "tenant_isolated",
        }
        errors = validate_capability_params("authorized_query", params)
        assert errors == []


class TestEventHandlerValidation:
    """Tests for event_handler validation."""

    def test_valid_params(self):
        """Test valid event_handler params."""
        params = {
            "event_type": "OrderCreated",
            "handler_id": "send_confirmation",
        }
        errors = validate_capability_params("event_handler", params)
        assert errors == []

    def test_missing_event_type(self):
        """Test missing event_type."""
        params = {"handler_id": "handler"}
        errors = validate_capability_params(
            "event_handler", params, raise_on_error=False
        )
        assert any("event_type" in e for e in errors)

    def test_missing_handler_id(self):
        """Test missing handler_id."""
        params = {"event_type": "OrderCreated"}
        errors = validate_capability_params(
            "event_handler", params, raise_on_error=False
        )
        assert any("handler_id" in e for e in errors)

    def test_invalid_timeout_ms(self):
        """Test invalid timeout_ms."""
        params = {
            "event_type": "OrderCreated",
            "handler_id": "handler",
            "timeout_ms": -1,
        }
        errors = validate_capability_params(
            "event_handler", params, raise_on_error=False
        )
        assert any("timeout_ms" in e for e in errors)


class TestScheduledTaskValidation:
    """Tests for scheduled_task validation."""

    def test_valid_params(self):
        """Test valid scheduled_task params."""
        params = {
            "task_id": "daily_cleanup",
            "cron_expression": "0 0 * * *",
        }
        errors = validate_capability_params("scheduled_task", params)
        assert errors == []

    def test_missing_task_id(self):
        """Test missing task_id."""
        params = {"cron_expression": "0 0 * * *"}
        errors = validate_capability_params(
            "scheduled_task", params, raise_on_error=False
        )
        assert any("task_id" in e for e in errors)

    def test_missing_cron_expression(self):
        """Test missing cron_expression."""
        params = {"task_id": "task"}
        errors = validate_capability_params(
            "scheduled_task", params, raise_on_error=False
        )
        assert any("cron_expression" in e for e in errors)


class TestWorkflowDefinitionValidation:
    """Tests for workflow_definition validation."""

    def test_valid_params(self):
        """Test valid workflow_definition params."""
        params = {
            "states": ["draft", "review", "approved", "rejected"],
            "transitions": [
                {"from": "draft", "to": "review"},
                {"from": "review", "to": "approved"},
            ],
            "start_state": "draft",
        }
        errors = validate_capability_params("workflow_definition", params)
        assert errors == []

    def test_missing_states(self):
        """Test missing states."""
        params = {
            "transitions": [],
            "start_state": "draft",
        }
        errors = validate_capability_params(
            "workflow_definition", params, raise_on_error=False
        )
        assert any("states" in e for e in errors)

    def test_invalid_start_state(self):
        """Test start_state not in states."""
        params = {
            "states": ["draft", "review"],
            "transitions": [],
            "start_state": "invalid",
        }
        errors = validate_capability_params(
            "workflow_definition", params, raise_on_error=False
        )
        assert any("start_state" in e for e in errors)


class TestIntegrationValidation:
    """Tests for integration capability validations."""

    def test_valid_outbound_integration(self):
        """Test valid outbound_integration params."""
        params = {
            "target_system": "payment_gateway",
            "endpoint": "https://api.payment.com/v1",
            "auth_type": "bearer",
        }
        errors = validate_capability_params("outbound_integration", params)
        assert errors == []

    def test_invalid_auth_type(self):
        """Test invalid auth_type."""
        params = {
            "target_system": "payment_gateway",
            "endpoint": "https://api.payment.com/v1",
            "auth_type": "invalid",
        }
        errors = validate_capability_params(
            "outbound_integration", params, raise_on_error=False
        )
        assert any("auth_type" in e for e in errors)

    def test_valid_inbound_integration(self):
        """Test valid inbound_integration params."""
        params = {
            "path": "/api/v1/orders",
            "method": "POST",
            "auth_type": "bearer",
            "handler_id": "create_order_handler",
        }
        errors = validate_capability_params("inbound_integration", params)
        assert errors == []

    def test_invalid_method(self):
        """Test invalid HTTP method."""
        params = {
            "path": "/api/v1/orders",
            "method": "INVALID",
            "auth_type": "bearer",
            "handler_id": "handler",
        }
        errors = validate_capability_params(
            "inbound_integration", params, raise_on_error=False
        )
        assert any("method" in e for e in errors)


class TestUnknownCapabilityType:
    """Tests for unknown capability type handling."""

    def test_unknown_type(self):
        """Test validation for unknown capability type."""
        params = {"some": "params"}
        errors = validate_capability_params(
            "unknown_type", params, raise_on_error=False
        )
        assert len(errors) == 1
        assert "unknown_type" in errors[0]

    def test_unknown_type_raises(self):
        """Test unknown capability type raises exception with default raise_on_error=True."""
        params = {"some": "params"}
        with pytest.raises(MidicoderError) as exc_info:
            validate_capability_params("unknown_type", params)
        assert "unknown_type" in str(exc_info.value)


class TestValidatorRegistry:
    """Tests for validator registry."""

    def test_registry_not_empty(self):
        """Test that registry has validators."""
        assert len(CAPABILITY_VALIDATORS) > 0

    def test_registry_has_core_validators(self):
        """Test that registry has core validators."""
        assert "authorized_mutation" in CAPABILITY_VALIDATORS
        assert "authorized_query" in CAPABILITY_VALIDATORS
        assert "event_handler" in CAPABILITY_VALIDATORS
        assert "scheduled_task" in CAPABILITY_VALIDATORS
        assert "workflow_definition" in CAPABILITY_VALIDATORS

    def test_consistency(self):
        """Test registry consistency with get_known_capability_types."""
        types = get_known_capability_types()
        for t in types:
            assert t in CAPABILITY_VALIDATORS