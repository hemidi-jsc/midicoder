"""
Tests cho MIR (Midicoder Intermediate Representation) Module.

Tests này validate:
- MIR typed models (Operation, DataFlow, EffectFlow, Boundary)
- MIR serialization/deserialization (dict, JSON)
- MIR hash computation (deterministic)
- MIR helper methods (filtering, dependency resolution)
- MIRBuilder fluent API

Theo SoT E05 và CURRENT_TASK_REQUIREMENT.md (P1-006-F).

Author: Midicoder Team
"""

import hashlib
import json
import pytest

from midicoder.pipeline.mir import (
    MIR, Operation, DataFlow, EffectFlow, Boundary, MIRBuilder
)


# ============================================================================
# Operation Tests
# ============================================================================

class TestOperation:
    """Tests cho Operation model."""

    def test_operation_creation_with_all_fields(self):
        """Test tạo Operation với đầy đủ fields."""
        op = Operation(
            op_id="create_order_001",
            op_type="create_record",
            params={"entity": "Order", "fields": ["order_id", "tenant_id"]},
            obligation_refs=["tenant_oblig_001", "perm_oblig_001"],
            input_refs=["tenant_id", "order_data"],
            output_refs=["order_entity"],
            metadata={"created_by": "test"}
        )
        
        assert op.op_id == "create_order_001"
        assert op.op_type == "create_record"
        assert op.params == {"entity": "Order", "fields": ["order_id", "tenant_id"]}
        assert op.obligation_refs == ["tenant_oblig_001", "perm_oblig_001"]
        assert op.input_refs == ["tenant_id", "order_data"]
        assert op.output_refs == ["order_entity"]
        assert op.metadata == {"created_by": "test"}

    def test_operation_default_values(self):
        """Test default values cho optional fields."""
        op = Operation(
            op_id="simple_op",
            op_type="execute_command",
            params={}
        )
        
        assert op.obligation_refs == []
        assert op.input_refs == []
        assert op.output_refs == []
        assert op.metadata == {}

    def test_operation_to_dict(self):
        """Test Operation.to_dict() serialization."""
        op = Operation(
            op_id="auth_001",
            op_type="authorize_permission",
            params={"permission": "order.create"},
            obligation_refs=["perm_oblig_001"],
            input_refs=[],
            output_refs=["user_context"],
            metadata={}
        )
        
        result = op.to_dict()
        
        assert result["op_id"] == "auth_001"
        assert result["op_type"] == "authorize_permission"
        assert result["params"] == {"permission": "order.create"}
        assert result["obligation_refs"] == ["perm_oblig_001"]
        assert result["input_refs"] == []
        assert result["output_refs"] == ["user_context"]
        assert result["metadata"] == {}

    def test_operation_from_dict(self):
        """Test Operation.from_dict() deserialization."""
        data = {
            "op_id": "query_001",
            "op_type": "query_records",
            "params": {"entity": "Order"},
            "obligation_refs": ["tenant_oblig_001"],
            "input_refs": ["tenant_id"],
            "output_refs": ["orders"],
            "metadata": {"description": "Get orders"}
        }
        
        op = Operation.from_dict(data)
        
        assert op.op_id == "query_001"
        assert op.op_type == "query_records"
        assert op.params == {"entity": "Order"}
        assert op.obligation_refs == ["tenant_oblig_001"]
        assert op.input_refs == ["tenant_id"]
        assert op.output_refs == ["orders"]
        assert op.metadata == {"description": "Get orders"}

    def test_operation_from_dict_with_defaults(self):
        """Test Operation.from_dict() với missing optional fields."""
        data = {
            "op_id": "minimal_op",
            "op_type": "execute_command",
            "params": {}
        }
        
        op = Operation.from_dict(data)
        
        assert op.op_id == "minimal_op"
        assert op.obligation_refs == []
        assert op.input_refs == []
        assert op.output_refs == []
        assert op.metadata == {}


# ============================================================================
# DataFlow Tests
# ============================================================================

class TestDataFlow:
    """Tests cho DataFlow model."""

    def test_dataflow_creation_with_all_fields(self):
        """Test tạo DataFlow với đầy đủ fields."""
        df = DataFlow(
            source_op="auth_001",
            source_field="user_id",
            target_op="create_order_001",
            target_field="created_by",
            transformation="uppercase",
            metadata={"description": "User ID flow"}
        )
        
        assert df.source_op == "auth_001"
        assert df.source_field == "user_id"
        assert df.target_op == "create_order_001"
        assert df.target_field == "created_by"
        assert df.transformation == "uppercase"
        assert df.metadata == {"description": "User ID flow"}

    def test_dataflow_default_transformation(self):
        """Test default value cho transformation field."""
        df = DataFlow(
            source_op="op1",
            source_field="id",
            target_op="op2",
            target_field="id"
        )
        
        assert df.transformation is None
        assert df.metadata == {}

    def test_dataflow_to_dict(self):
        """Test DataFlow.to_dict() serialization."""
        df = DataFlow(
            source_op="tenant_001",
            source_field="tenant_id",
            target_op="create_order_001",
            target_field="tenant_id",
            transformation=None,
            metadata={}
        )
        
        result = df.to_dict()
        
        assert result["source_op"] == "tenant_001"
        assert result["source_field"] == "tenant_id"
        assert result["target_op"] == "create_order_001"
        assert result["target_field"] == "tenant_id"
        assert result["transformation"] is None
        assert result["metadata"] == {}

    def test_dataflow_from_dict(self):
        """Test DataFlow.from_dict() deserialization."""
        data = {
            "source_op": "auth_001",
            "source_field": "tenant_id",
            "target_op": "query_001",
            "target_field": "tenant_filter",
            "transformation": None,
            "metadata": {"type": "filter"}
        }
        
        df = DataFlow.from_dict(data)
        
        assert df.source_op == "auth_001"
        assert df.source_field == "tenant_id"
        assert df.target_op == "query_001"
        assert df.target_field == "tenant_filter"
        assert df.transformation is None
        assert df.metadata == {"type": "filter"}


# ============================================================================
# EffectFlow Tests
# ============================================================================

class TestEffectFlow:
    """Tests cho EffectFlow model."""

    def test_effectflow_creation_with_all_fields(self):
        """Test tạo EffectFlow với đầy đủ fields."""
        ef = EffectFlow(
            source_op="create_order_001",
            effect_type="event_publish",
            target="OrderCreated",
            payload_fields=["order_id", "tenant_id", "total"],
            metadata={"description": "Order created event"}
        )
        
        assert ef.source_op == "create_order_001"
        assert ef.effect_type == "event_publish"
        assert ef.target == "OrderCreated"
        assert ef.payload_fields == ["order_id", "tenant_id", "total"]
        assert ef.metadata == {"description": "Order created event"}

    def test_effectflow_default_payload_fields(self):
        """Test default value cho payload_fields."""
        ef = EffectFlow(
            source_op="op1",
            effect_type="log_write",
            target="audit_log"
        )
        
        assert ef.payload_fields == []
        assert ef.metadata == {}

    def test_effectflow_to_dict(self):
        """Test EffectFlow.to_dict() serialization."""
        ef = EffectFlow(
            source_op="create_order_001",
            effect_type="event_publish",
            target="OrderCreated",
            payload_fields=["order_id", "total"],
            metadata={}
        )
        
        result = ef.to_dict()
        
        assert result["source_op"] == "create_order_001"
        assert result["effect_type"] == "event_publish"
        assert result["target"] == "OrderCreated"
        assert result["payload_fields"] == ["order_id", "total"]
        assert result["metadata"] == {}

    def test_effectflow_from_dict(self):
        """Test EffectFlow.from_dict() deserialization."""
        data = {
            "source_op": "update_inventory_001",
            "effect_type": "metric_record",
            "target": "inventory_updated",
            "payload_fields": ["sku", "quantity"],
            "metadata": {"unit": "items"}
        }
        
        ef = EffectFlow.from_dict(data)
        
        assert ef.source_op == "update_inventory_001"
        assert ef.effect_type == "metric_record"
        assert ef.target == "inventory_updated"
        assert ef.payload_fields == ["sku", "quantity"]
        assert ef.metadata == {"unit": "items"}


# ============================================================================
# Boundary Tests
# ============================================================================

class TestBoundary:
    """Tests cho Boundary model."""

    def test_boundary_transaction_type(self):
        """Test tạo transaction boundary."""
        b = Boundary(
            boundary_id="txn_001",
            boundary_type="transaction",
            enclosing_ops=["create_order_001", "create_items_001"],
            config={"isolation_level": "read_committed"},
            metadata={}
        )
        
        assert b.boundary_id == "txn_001"
        assert b.boundary_type == "transaction"
        assert b.enclosing_ops == ["create_order_001", "create_items_001"]
        assert b.config == {"isolation_level": "read_committed"}

    def test_boundary_auth_type(self):
        """Test tạo auth boundary."""
        b = Boundary(
            boundary_id="auth_admin",
            boundary_type="auth",
            enclosing_ops=[],
            config={"role_id": "admin", "permissions": ["*"]},
            metadata={}
        )
        
        assert b.boundary_id == "auth_admin"
        assert b.boundary_type == "auth"
        assert b.config["role_id"] == "admin"

    def test_boundary_tenant_type(self):
        """Test tạo tenant boundary."""
        b = Boundary(
            boundary_id="tenant_scope_001",
            boundary_type="tenant",
            enclosing_ops=["query_001"],
            config={"scope": "tenant_isolated"},
            metadata={}
        )
        
        assert b.boundary_type == "tenant"
        assert b.config["scope"] == "tenant_isolated"

    def test_boundary_default_config(self):
        """Test default value cho config field."""
        b = Boundary(
            boundary_id="minimal",
            boundary_type="transaction",
            enclosing_ops=["op1"]
        )
        
        assert b.config == {}
        assert b.metadata == {}

    def test_boundary_to_dict(self):
        """Test Boundary.to_dict() serialization."""
        b = Boundary(
            boundary_id="txn_001",
            boundary_type="transaction",
            enclosing_ops=["op1", "op2"],
            config={"workflow_id": "wf_001"},
            metadata={}
        )
        
        result = b.to_dict()
        
        assert result["boundary_id"] == "txn_001"
        assert result["boundary_type"] == "transaction"
        assert result["enclosing_ops"] == ["op1", "op2"]
        assert result["config"] == {"workflow_id": "wf_001"}

    def test_boundary_from_dict(self):
        """Test Boundary.from_dict() deserialization."""
        data = {
            "boundary_id": "auth_user",
            "boundary_type": "auth",
            "enclosing_ops": ["query_001"],
            "config": {"role_id": "user", "permissions": ["read"]},
            "metadata": {"description": "User auth"}
        }
        
        b = Boundary.from_dict(data)
        
        assert b.boundary_id == "auth_user"
        assert b.boundary_type == "auth"
        assert b.enclosing_ops == ["query_001"]
        assert b.config == {"role_id": "user", "permissions": ["read"]}
        assert b.metadata == {"description": "User auth"}


# ============================================================================
# MIR Tests
# ============================================================================

class TestMIR:
    """Tests cho MIR model."""

    def test_mir_creation_empty(self):
        """Test tạo MIR empty với default collections."""
        mir = MIR()
        
        assert mir.operations == []
        assert mir.data_flows == []
        assert mir.effect_flows == []
        assert mir.boundaries == []
        assert mir.metadata == {}

    def test_mir_add_operation(self):
        """Test MIR.add_operation()."""
        mir = MIR()
        op = Operation(op_id="op1", op_type="create_record", params={})
        
        mir.add_operation(op)
        
        assert len(mir.operations) == 1
        assert mir.operations[0].op_id == "op1"

    def test_mir_add_data_flow(self):
        """Test MIR.add_data_flow()."""
        mir = MIR()
        df = DataFlow(source_op="op1", source_field="id", target_op="op2", target_field="id")
        
        mir.add_data_flow(df)
        
        assert len(mir.data_flows) == 1
        assert mir.data_flows[0].source_op == "op1"

    def test_mir_add_effect_flow(self):
        """Test MIR.add_effect_flow()."""
        mir = MIR()
        ef = EffectFlow(source_op="op1", effect_type="event_publish", target="Event1")
        
        mir.add_effect_flow(ef)
        
        assert len(mir.effect_flows) == 1
        assert mir.effect_flows[0].target == "Event1"

    def test_mir_add_boundary(self):
        """Test MIR.add_boundary()."""
        mir = MIR()
        b = Boundary(boundary_id="txn_001", boundary_type="transaction", enclosing_ops=["op1"])
        
        mir.add_boundary(b)
        
        assert len(mir.boundaries) == 1
        assert mir.boundaries[0].boundary_id == "txn_001"

    def test_mir_to_dict(self):
        """Test MIR.to_dict() full serialization."""
        mir = MIR(metadata={"version": "1.0.0", "source": "test"})
        mir.operations.append(Operation(op_id="op1", op_type="create_record", params={}))
        mir.data_flows.append(DataFlow(source_op="op1", source_field="id", target_op="op2", target_field="id"))
        mir.effect_flows.append(EffectFlow(source_op="op1", effect_type="event_publish", target="Event1"))
        mir.boundaries.append(Boundary(boundary_id="txn_001", boundary_type="transaction", enclosing_ops=["op1"]))
        
        result = mir.to_dict()
        
        assert result["version"] == "1.0.0"
        assert len(result["operations"]) == 1
        assert len(result["data_flows"]) == 1
        assert len(result["effect_flows"]) == 1
        assert len(result["boundaries"]) == 1
        assert result["metadata"]["source"] == "test"

    def test_mir_to_json(self):
        """Test MIR.to_json() JSON output."""
        mir = MIR(metadata={"version": "1.0.0"})
        mir.operations.append(Operation(op_id="op1", op_type="create_record", params={}))
        
        json_str = mir.to_json(indent=2)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["version"] == "1.0.0"
        assert len(parsed["operations"]) == 1

    def test_mir_from_dict(self):
        """Test MIR.from_dict() full deserialization."""
        data = {
            "version": "1.0.0",
            "operations": [
                {"op_id": "op1", "op_type": "create_record", "params": {"entity": "Order"}}
            ],
            "data_flows": [
                {"source_op": "op1", "source_field": "id", "target_op": "op2", "target_field": "id"}
            ],
            "effect_flows": [],
            "boundaries": [],
            "metadata": {"source": "test"}
        }
        
        mir = MIR.from_dict(data)
        
        assert len(mir.operations) == 1
        assert mir.operations[0].op_id == "op1"
        assert len(mir.data_flows) == 1
        assert len(mir.effect_flows) == 0
        assert len(mir.boundaries) == 0
        assert mir.metadata["source"] == "test"

    def test_mir_from_json(self):
        """Test MIR.from_json() JSON parsing."""
        json_str = '''
        {
            "version": "1.0.0",
            "operations": [
                {"op_id": "op1", "op_type": "create_record", "params": {}}
            ],
            "data_flows": [],
            "effect_flows": [],
            "boundaries": [],
            "metadata": {}
        }
        '''
        
        mir = MIR.from_json(json_str)
        
        assert len(mir.operations) == 1
        assert mir.operations[0].op_id == "op1"

    def test_mir_compute_hash_deterministic(self):
        """Test MIR.compute_hash() deterministic hash."""
        mir1 = MIR(metadata={"version": "1.0.0"})
        mir1.operations.append(Operation(op_id="op1", op_type="create_record", params={}))
        
        mir2 = MIR(metadata={"version": "1.0.0"})
        mir2.operations.append(Operation(op_id="op1", op_type="create_record", params={}))
        
        # Same content should produce same hash
        assert mir1.compute_hash() == mir2.compute_hash()

    def test_mir_compute_hash_different_content(self):
        """Test MIR.compute_hash() với different content."""
        mir1 = MIR(metadata={"version": "1.0.0"})
        mir1.operations.append(Operation(op_id="op1", op_type="create_record", params={}))
        
        mir2 = MIR(metadata={"version": "1.0.0"})
        mir2.operations.append(Operation(op_id="op2", op_type="create_record", params={}))
        
        # Different content should produce different hash
        assert mir1.compute_hash() != mir2.compute_hash()

    def test_mir_compute_hash_format(self):
        """Test MIR.compute_hash() SHA256 format."""
        mir = MIR()
        hash_value = mir.compute_hash()
        
        # SHA256 produces 64 hex characters
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_mir_get_operations_by_type(self):
        """Test MIR.get_operations_by_type() filtering."""
        mir = MIR()
        mir.operations.append(Operation(op_id="op1", op_type="create_record", params={}))
        mir.operations.append(Operation(op_id="op2", op_type="query_records", params={}))
        mir.operations.append(Operation(op_id="op3", op_type="create_record", params={}))
        
        create_ops = mir.get_operations_by_type("create_record")
        
        assert len(create_ops) == 2
        assert all(op.op_type == "create_record" for op in create_ops)

    def test_mir_get_operations_with_obligation(self):
        """Test MIR.get_operations_with_obligation() filtering."""
        mir = MIR()
        mir.operations.append(Operation(
            op_id="op1", op_type="create_record", params={},
            obligation_refs=["perm_oblig_001"]
        ))
        mir.operations.append(Operation(
            op_id="op2", op_type="query_records", params={},
            obligation_refs=["tenant_oblig_001"]
        ))
        
        ops_with_perm = mir.get_operations_with_obligation("perm_oblig_001")
        
        assert len(ops_with_perm) == 1
        assert ops_with_perm[0].op_id == "op1"

    def test_mir_get_dependencies(self):
        """Test MIR.get_dependencies() dependency resolution."""
        mir = MIR()
        mir.operations.append(Operation(op_id="op1", op_type="create_record", params={}))
        mir.operations.append(Operation(op_id="op2", op_type="query_records", params={}))
        
        # op2 depends on op1 (data flows from op1 to op2)
        mir.data_flows.append(DataFlow(
            source_op="op1", source_field="id",
            target_op="op2", target_field="id"
        ))
        
        deps = mir.get_dependencies("op2")
        
        assert "op1" in deps

    def test_mir_get_dependents(self):
        """Test MIR.get_dependents() dependent resolution."""
        mir = MIR()
        mir.operations.append(Operation(op_id="op1", op_type="create_record", params={}))
        mir.operations.append(Operation(op_id="op2", op_type="query_records", params={}))
        
        # op2 depends on op1
        mir.data_flows.append(DataFlow(
            source_op="op1", source_field="id",
            target_op="op2", target_field="id"
        ))
        
        dependents = mir.get_dependents("op1")
        
        assert "op2" in dependents


# ============================================================================
# MIRBuilder Tests
# ============================================================================

class TestMIRBuilder:
    """Tests cho MIRBuilder fluent API."""

    def test_mirbuilder_version_chaining(self):
        """Test MIRBuilder.with_version() chaining."""
        builder = MIRBuilder().with_version("1.0.0")
        
        assert builder.mir.metadata["version"] == "1.0.0"

    def test_mirbuilder_source_chaining(self):
        """Test MIRBuilder.with_source() chaining."""
        builder = MIRBuilder().with_source("DSL ProjectionTree")
        
        assert builder.mir.metadata["source"] == "DSL ProjectionTree"

    def test_mirbuilder_add_operation_chaining(self):
        """Test MIRBuilder.add_operation() chaining."""
        builder = MIRBuilder().add_operation(
            op_id="op1",
            op_type="create_record",
            params={"entity": "Order"}
        )
        
        assert len(builder.mir.operations) == 1
        assert builder.mir.operations[0].op_id == "op1"

    def test_mirbuilder_add_data_flow_chaining(self):
        """Test MIRBuilder.add_data_flow() chaining."""
        builder = MIRBuilder().add_data_flow(
            source_op="op1", source_field="id",
            target_op="op2", target_field="id"
        )
        
        assert len(builder.mir.data_flows) == 1

    def test_mirbuilder_add_effect_flow_chaining(self):
        """Test MIRBuilder.add_effect_flow() chaining."""
        builder = MIRBuilder().add_effect_flow(
            source_op="op1", effect_type="event_publish", target="Event1"
        )
        
        assert len(builder.mir.effect_flows) == 1

    def test_mirbuilder_add_boundary_chaining(self):
        """Test MIRBuilder.add_boundary() chaining."""
        builder = MIRBuilder().add_boundary(
            boundary_id="txn_001",
            boundary_type="transaction",
            enclosing_ops=["op1"]
        )
        
        assert len(builder.mir.boundaries) == 1

    def test_mirbuilder_build_returns_mir(self):
        """Test MIRBuilder.build() returns MIR."""
        builder = MIRBuilder().with_version("1.0.0")
        builder.add_operation(op_id="op1", op_type="create_record", params={})
        
        mir = builder.build()
        
        assert isinstance(mir, MIR)
        assert mir.metadata["version"] == "1.0.0"
        assert len(mir.operations) == 1

    def test_mirbuilder_fluent_api_multiple_calls(self):
        """Test fluent API với multiple chained calls."""
        builder = MIRBuilder()
        
        mir = (builder
            .with_version("1.0.0")
            .with_source("test")
            .add_operation(op_id="op1", op_type="create_record", params={})
            .add_operation(op_id="op2", op_type="query_records", params={})
            .add_data_flow(source_op="op1", source_field="id", target_op="op2", target_field="id")
            .add_effect_flow(source_op="op1", effect_type="event_publish", target="Event1")
            .add_boundary(boundary_id="txn_001", boundary_type="transaction", enclosing_ops=["op1", "op2"])
            .build()
        )
        
        assert mir.metadata["version"] == "1.0.0"
        assert mir.metadata["source"] == "test"
        assert len(mir.operations) == 2
        assert len(mir.data_flows) == 1
        assert len(mir.effect_flows) == 1
        assert len(mir.boundaries) == 1

    def test_mirbuilder_with_optional_params(self):
        """Test MIRBuilder với optional params (None values)."""
        builder = MIRBuilder()
        
        # Test với obligation_refs=None
        builder.add_operation(
            op_id="op1", op_type="create_record", params={},
            obligation_refs=None, input_refs=None, output_refs=None
        )
        
        # Test với transformation=None
        builder.add_data_flow(
            source_op="op1", source_field="id",
            target_op="op2", target_field="id", transformation=None
        )
        
        # Test với payload_fields=None
        builder.add_effect_flow(
            source_op="op1", effect_type="event_publish",
            target="Event1", payload_fields=None
        )
        
        # Test với config=None
        builder.add_boundary(
            boundary_id="txn_001", boundary_type="transaction",
            enclosing_ops=["op1"], config=None
        )
        
        mir = builder.build()
        
        # Verify defaults were applied
        assert mir.operations[0].obligation_refs == []
        assert mir.data_flows[0].transformation is None
        assert mir.effect_flows[0].payload_fields == []
        assert mir.boundaries[0].config == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])