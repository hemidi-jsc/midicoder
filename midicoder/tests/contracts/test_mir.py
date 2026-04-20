"""
Unit Tests cho MIR (Midicoder Intermediate Representation) Contracts.

Kiểm tra behavior của:
- MIROperation class
- MIRDataFlow class
- MIREffectFlow class
- MIRBoundary class
- MIR class

Tests tuân thủ TDD, không mocks, bám sát SoT.

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.contracts.mir import (
    MIROperation,
    MIRDataFlow,
    MIREffectFlow,
    MIRBoundary,
    MIR,
)


class TestMIROperation:
    """Tests cho MIROperation class."""

    def test_operation_created_with_required_fields(self):
        """Kiểm tra MIROperation được tạo với op bắt buộc."""
        operation = MIROperation(op="authorize_permission")

        assert operation.op == "authorize_permission"
        assert operation.params == {}
        assert operation.input_refs == []
        assert operation.output_refs == []
        assert operation.effect_refs == []
        assert operation.transaction_boundary is None
        assert operation.obligation_refs == []

    def test_operation_created_with_all_fields(self):
        """Kiểm tra MIROperation được tạo với tất cả fields."""
        operation = MIROperation(
            op="create_record",
            params={"entity": "Order", "data": {"name": "Test"}},
            input_refs=["input_001"],
            output_refs=["output_001"],
            effect_refs=["effect_001"],
            transaction_boundary="tx_001",
            obligation_refs=["obligation_001"],
        )

        assert operation.op == "create_record"
        assert operation.params == {"entity": "Order", "data": {"name": "Test"}}
        assert operation.input_refs == ["input_001"]
        assert operation.output_refs == ["output_001"]
        assert operation.effect_refs == ["effect_001"]
        assert operation.transaction_boundary == "tx_001"
        assert operation.obligation_refs == ["obligation_001"]

    def test_operation_to_dict_contains_all_fields(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        operation = MIROperation(
            op="authorize_permission",
            params={"permission": "order.create"},
            obligation_refs=["perm_check_001"],
        )
        operation_dict = operation.to_dict()

        assert operation_dict["op"] == "authorize_permission"
        assert operation_dict["params"] == {"permission": "order.create"}
        assert operation_dict["obligation_refs"] == ["perm_check_001"]

    def test_operation_from_dict_creates_operation(self):
        """Kiểm tra from_dict tạo MIROperation đúng."""
        operation_data = {
            "op": "create_record",
            "params": {"entity": "Customer"},
            "input_refs": ["input_001"],
            "output_refs": ["output_001"],
            "effect_refs": ["effect_001"],
            "transaction_boundary": "tx_001",
            "obligation_refs": ["oblig_001"],
        }

        operation = MIROperation.from_dict(operation_data)

        assert operation.op == "create_record"
        assert operation.params == {"entity": "Customer"}
        assert operation.input_refs == ["input_001"]

    def test_operation_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        original = MIROperation(
            op="create_record",
            params={"entity": "Order", "data": {"id": 1}},
            input_refs=["input_001"],
            output_refs=["output_001"],
            effect_refs=["effect_001"],
            transaction_boundary="tx_001",
            obligation_refs=["oblig_001"],
        )

        operation_dict = original.to_dict()
        reconstructed = MIROperation.from_dict(operation_dict)

        assert reconstructed.op == original.op
        assert reconstructed.params == original.params
        assert reconstructed.input_refs == original.input_refs
        assert reconstructed.output_refs == original.output_refs
        assert reconstructed.effect_refs == original.effect_refs
        assert reconstructed.transaction_boundary == original.transaction_boundary
        assert reconstructed.obligation_refs == original.obligation_refs


class TestMIRDataFlow:
    """Tests cho MIRDataFlow class."""

    def test_flow_created_with_required_fields(self):
        """Kiểm tra MIRDataFlow được tạo với các fields bắt buộc."""
        flow = MIRDataFlow(
            id="flow_001",
            source_op="authorize_permission",
            source_field="principal.user_id",
            target_op="create_record",
            target_field="created_by",
        )

        assert flow.id == "flow_001"
        assert flow.source_op == "authorize_permission"
        assert flow.source_field == "principal.user_id"
        assert flow.target_op == "create_record"
        assert flow.target_field == "created_by"
        assert flow.transformation is None

    def test_flow_created_with_transformation(self):
        """Kiểm tra MIRDataFlow với transformation."""
        flow = MIRDataFlow(
            id="flow_002",
            source_op="query_records",
            source_field="results",
            target_op="send_notification",
            target_field="data",
            transformation="map_to_notification_format",
        )

        assert flow.id == "flow_002"
        assert flow.transformation == "map_to_notification_format"

    def test_flow_to_dict_contains_all_fields(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        flow = MIRDataFlow(
            id="flow_003",
            source_op="op1",
            source_field="field1",
            target_op="op2",
            target_field="field2",
            transformation="transform_func",
        )
        flow_dict = flow.to_dict()

        assert flow_dict["id"] == "flow_003"
        assert flow_dict["source_op"] == "op1"
        assert flow_dict["source_field"] == "field1"
        assert flow_dict["target_op"] == "op2"
        assert flow_dict["target_field"] == "field2"
        assert flow_dict["transformation"] == "transform_func"

    def test_flow_from_dict_creates_flow(self):
        """Kiểm tra from_dict tạo MIRDataFlow đúng."""
        flow_data = {
            "id": "flow_004",
            "source_op": "create_order",
            "source_field": "order_id",
            "target_op": "publish_event",
            "target_field": "payload.order_id",
        }

        flow = MIRDataFlow.from_dict(flow_data)

        assert flow.id == "flow_004"
        assert flow.source_op == "create_order"
        assert flow.target_op == "publish_event"
        assert flow.transformation is None

    def test_flow_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        original = MIRDataFlow(
            id="flow_005",
            source_op="op1",
            source_field="src_field",
            target_op="op2",
            target_field="tgt_field",
            transformation="my_transform",
        )

        flow_dict = original.to_dict()
        reconstructed = MIRDataFlow.from_dict(flow_dict)

        assert reconstructed.id == original.id
        assert reconstructed.source_op == original.source_op
        assert reconstructed.source_field == original.source_field
        assert reconstructed.target_op == original.target_op
        assert reconstructed.target_field == original.target_field
        assert reconstructed.transformation == original.transformation


class TestMIREffectFlow:
    """Tests cho MIREffectFlow class."""

    def test_effect_created_with_required_fields(self):
        """Kiểm tra MIREffectFlow được tạo với các fields bắt buộc."""
        effect = MIREffectFlow(
            id="effect_001",
            source_op="create_record",
            effect_type="event_publish",
            target="OrderCreated",
        )

        assert effect.id == "effect_001"
        assert effect.source_op == "create_record"
        assert effect.effect_type == "event_publish"
        assert effect.target == "OrderCreated"
        assert effect.payload_fields == []
        assert effect.async_ is False
        assert effect.retry_policy is None

    def test_effect_created_with_optional_fields(self):
        """Kiểm tra MIREffectFlow với optional fields."""
        effect = MIREffectFlow(
            id="effect_002",
            source_op="create_order",
            effect_type="notification",
            target="email_service",
            payload_fields=["order_id", "customer_email"],
            async_=True,
            retry_policy={"max_retries": 3, "backoff": "exponential"},
        )

        assert effect.id == "effect_002"
        assert effect.payload_fields == ["order_id", "customer_email"]
        assert effect.async_ is True
        assert effect.retry_policy is not None

    def test_effect_to_dict_contains_all_fields(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        effect = MIREffectFlow(
            id="effect_003",
            source_op="op1",
            effect_type="event_publish",
            target="Event1",
            payload_fields=["field1"],
            async_=True,
        )
        effect_dict = effect.to_dict()

        assert effect_dict["id"] == "effect_003"
        assert effect_dict["source_op"] == "op1"
        assert effect_dict["effect_type"] == "event_publish"
        assert effect_dict["target"] == "Event1"
        assert effect_dict["async"] is True

    def test_effect_from_dict_creates_effect(self):
        """Kiểm tra from_dict tạo MIREffectFlow đúng."""
        effect_data = {
            "id": "effect_004",
            "source_op": "create_order",
            "effect_type": "event_publish",
            "target": "OrderCreated",
            "payload_fields": ["order_id"],
            "async": True,
        }

        effect = MIREffectFlow.from_dict(effect_data)

        assert effect.id == "effect_004"
        assert effect.source_op == "create_order"
        assert effect.effect_type == "event_publish"
        assert effect.async_ is True

    def test_effect_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        original = MIREffectFlow(
            id="effect_005",
            source_op="create_order",
            effect_type="event_publish",
            target="OrderCreated",
            payload_fields=["order_id", "total"],
            async_=True,
            retry_policy={"max_retries": 3},
        )

        effect_dict = original.to_dict()
        reconstructed = MIREffectFlow.from_dict(effect_dict)

        assert reconstructed.id == original.id
        assert reconstructed.source_op == original.source_op
        assert reconstructed.effect_type == original.effect_type
        assert reconstructed.target == original.target
        assert reconstructed.payload_fields == original.payload_fields
        assert reconstructed.async_ == original.async_


class TestMIRBoundary:
    """Tests cho MIRBoundary class."""

    def test_boundary_created_with_transaction_type(self):
        """Kiểm tra MIRBoundary được tạo với transaction type."""
        boundary = MIRBoundary(
            id="boundary_001",
            boundary_type="transaction",
            enclosing_ops=["create_order", "update_inventory"],
        )

        assert boundary.id == "boundary_001"
        assert boundary.boundary_type == "transaction"
        assert boundary.enclosing_ops == ["create_order", "update_inventory"]

    def test_boundary_created_with_auth_type(self):
        """Kiểm tra MIRBoundary được tạo với auth type."""
        boundary = MIRBoundary(
            id="boundary_002",
            boundary_type="auth",
            enclosing_ops=["authorize_permission"],
            config={"role": "admin", "permission": "order.create"},
        )

        assert boundary.id == "boundary_002"
        assert boundary.boundary_type == "auth"
        assert boundary.config == {"role": "admin", "permission": "order.create"}

    def test_boundary_boundary_type_values(self):
        """Kiểm tra boundary_type string values."""
        # boundary_type là string, không phải enum
        transaction_boundary = MIRBoundary(id="b1", boundary_type="transaction")
        auth_boundary = MIRBoundary(id="b2", boundary_type="auth")
        tenant_boundary = MIRBoundary(id="b3", boundary_type="tenant")

        assert transaction_boundary.boundary_type == "transaction"
        assert auth_boundary.boundary_type == "auth"
        assert tenant_boundary.boundary_type == "tenant"

    def test_boundary_to_dict_contains_all_fields(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        boundary = MIRBoundary(
            id="boundary_003",
            boundary_type="transaction",
            enclosing_ops=["op1", "op2"],
            config={"isolation": "read_committed"},
        )
        boundary_dict = boundary.to_dict()

        assert boundary_dict["id"] == "boundary_003"
        assert boundary_dict["boundary_type"] == "transaction"
        assert boundary_dict["enclosing_ops"] == ["op1", "op2"]

    def test_boundary_from_dict_creates_boundary(self):
        """Kiểm tra from_dict tạo MIRBoundary đúng."""
        boundary_data = {
            "id": "boundary_004",
            "boundary_type": "tenant",
            "enclosing_ops": ["query_records"],
        }

        boundary = MIRBoundary.from_dict(boundary_data)

        assert boundary.id == "boundary_004"
        assert boundary.boundary_type == "tenant"
        assert boundary.enclosing_ops == ["query_records"]

    def test_boundary_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        original = MIRBoundary(
            id="boundary_005",
            boundary_type="transaction",
            enclosing_ops=["create_order", "create_item"],
            config={"isolation": "serializable"},
            scope="order_creation",
        )

        boundary_dict = original.to_dict()
        reconstructed = MIRBoundary.from_dict(boundary_dict)

        assert reconstructed.id == original.id
        assert reconstructed.boundary_type == original.boundary_type
        assert reconstructed.enclosing_ops == original.enclosing_ops
        assert reconstructed.scope == original.scope


class TestMIR:
    """Tests cho MIR class."""

    def test_mir_created_empty(self):
        """Kiểm tra MIR có thể được tạo rỗng."""
        mir = MIR()

        assert mir is not None
        assert mir.ops == []
        assert mir.data_flows == []
        assert mir.effect_flows == []
        assert mir.boundaries == []
        assert mir.ir_ref == ""

    def test_mir_created_with_ops(self):
        """Kiểm tra MIR được tạo với operations."""
        operation = MIROperation(op="authorize_permission", params={"permission": "order.create"})
        mir = MIR(ir_ref="Command.CreateOrder", ops=[operation])

        assert len(mir.ops) == 1
        assert mir.ops[0].op == "authorize_permission"
        assert mir.ir_ref == "Command.CreateOrder"

    def test_mir_add_operation(self):
        """Kiểm tra add_operation thêm operation vào MIR."""
        mir = MIR(ir_ref="Command.CreateOrder")
        operation = MIROperation(op="create_record")

        index = mir.add_operation(operation)

        assert len(mir.ops) == 1
        assert mir.ops[0].op == "create_record"
        assert index == 0

    def test_mir_get_operation(self):
        """Kiểm tra get_operation trả về operation đúng theo index."""
        mir = MIR(ir_ref="Command.CreateOrder")
        operation = MIROperation(op="create_record", params={"entity": "Order"})
        mir.add_operation(operation)

        result = mir.get_operation(0)
        assert result is not None
        assert result.op == "create_record"

    def test_mir_to_dict_contains_all_fields(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        operation = MIROperation(op="authorize_permission")
        mir = MIR(ir_ref="Command.CreateOrder", ops=[operation])

        mir_dict = mir.to_dict()

        assert "ops" in mir_dict
        assert "data_flows" in mir_dict
        assert "effect_flows" in mir_dict
        assert "boundaries" in mir_dict
        assert "ir_ref" in mir_dict
        assert len(mir_dict["ops"]) == 1

    def test_mir_from_dict_creates_mir(self):
        """Kiểm tra from_dict tạo MIR đúng."""
        mir_data = {
            "ir_ref": "Command.CreateOrder",
            "ops": [
                {"op": "authorize_permission", "params": {"permission": "order.create"}}
            ],
            "data_flows": [],
            "effect_flows": [],
            "boundaries": [],
        }

        mir = MIR.from_dict(mir_data)

        assert mir is not None
        assert len(mir.ops) == 1
        assert mir.ops[0].op == "authorize_permission"
        assert mir.ir_ref == "Command.CreateOrder"

    def test_mir_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        operation = MIROperation(op="create_record", params={"entity": "Order"})
        data_flow = MIRDataFlow(
            id="flow_001",
            source_op="create_record",
            source_field="order_id",
            target_op="publish_event",
            target_field="payload.order_id",
        )
        mir = MIR(
            ir_ref="Command.CreateOrder",
            description="Create order MIR",
            ops=[operation],
            data_flows=[data_flow],
        )

        mir_dict = mir.to_dict()
        reconstructed = MIR.from_dict(mir_dict)

        assert len(reconstructed.ops) == len(mir.ops)
        assert len(reconstructed.data_flows) == len(mir.data_flows)
        assert reconstructed.ops[0].op == mir.ops[0].op
        assert reconstructed.data_flows[0].id == mir.data_flows[0].id
        assert reconstructed.ir_ref == mir.ir_ref
        assert reconstructed.description == mir.description
