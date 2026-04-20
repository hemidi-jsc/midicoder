"""
Unit Tests cho Capability Graph Contracts.

Kiểm tra behavior của:
- Obligation class
- CapabilityInstance class
- MacroCapability class
- CoreCapability class
- CapabilityGraph class

Tests tuân thủ TDD, không mocks, bám sát SoT.

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.contracts.graph import (
    Obligation,
    CapabilityInstance,
    MacroCapability,
    CoreCapability,
    CapabilityGraph,
)


class TestObligation:
    """Tests cho Obligation class."""

    def test_obligation_created_with_required_fields(self):
        """Kiểm tra Obligation được tạo với các fields bắt buộc."""
        obligation = Obligation(
            id="test_001",
            type="permission_check_required",
            description="Yêu cầu permission check",
            source="capability:TestCapability",
        )

        assert obligation.id == "test_001"
        assert obligation.type == "permission_check_required"
        assert obligation.description == "Yêu cầu permission check"
        assert obligation.source == "capability:TestCapability"
        assert obligation.satisfied is False
        assert obligation.satisfaction_evidence is None

    def test_obligation_satisfied_can_be_set(self):
        """Kiểm tra satisfied flag có thể được set."""
        obligation = Obligation(
            id="test_002",
            type="tenant_filter_required",
            description="Yêu cầu tenant filter",
            source="capability:TestCapability",
        )

        obligation.satisfied = True
        obligation.satisfaction_evidence = "file.py:line 42"

        assert obligation.satisfied is True
        assert obligation.satisfaction_evidence == "file.py:line 42"

    def test_obligation_to_dict_contains_all_fields(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        obligation = Obligation(
            id="test_003",
            type="transaction_required",
            description="Yêu cầu transaction",
            source="capability:TestCapability",
            satisfied=True,
            satisfaction_evidence="file.py:line 10",
        )
        obligation_dict = obligation.to_dict()

        assert obligation_dict["id"] == "test_003"
        assert obligation_dict["type"] == "transaction_required"
        assert obligation_dict["description"] == "Yêu cầu transaction"
        assert obligation_dict["source"] == "capability:TestCapability"
        assert obligation_dict["satisfied"] is True
        assert obligation_dict["satisfaction_evidence"] == "file.py:line 10"

    def test_obligation_from_dict_creates_obligation(self):
        """Kiểm tra from_dict tạo Obligation đúng."""
        obligation_data = {
            "id": "test_004",
            "type": "audit_log_required",
            "description": "Yêu cầu audit log",
            "source": "capability:TestCapability",
            "satisfied": False,
            "satisfaction_evidence": None,
        }

        obligation = Obligation.from_dict(obligation_data)

        assert obligation.id == "test_004"
        assert obligation.type == "audit_log_required"
        assert obligation.description == "Yêu cầu audit log"
        assert obligation.satisfied is False

    def test_obligation_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        original = Obligation(
            id="test_005",
            type="permission_check_required",
            description="Yêu cầu permission check",
            source="capability:TestCapability",
            satisfied=True,
            satisfaction_evidence="file.py:line 20",
        )

        obligation_dict = original.to_dict()
        reconstructed = Obligation.from_dict(obligation_dict)

        assert reconstructed.id == original.id
        assert reconstructed.type == original.type
        assert reconstructed.description == original.description
        assert reconstructed.source == original.source
        assert reconstructed.satisfied == original.satisfied
        assert reconstructed.satisfaction_evidence == original.satisfaction_evidence


class TestCapabilityInstance:
    """Tests cho CapabilityInstance class."""

    def test_instance_created_with_required_fields(self):
        """Kiểm tra CapabilityInstance được tạo với các fields bắt buộc."""
        instance = CapabilityInstance(
            id="create_order",
            type="authorized_mutation",
        )

        assert instance.id == "create_order"
        assert instance.type == "authorized_mutation"
        assert instance.description is None
        assert instance.confidence == 1.0
        assert instance.params == {}
        assert instance.reads == []
        assert instance.writes == []
        assert instance.emits == []
        assert instance.obligations == []
        assert instance.tags == []

    def test_instance_created_with_all_fields(self):
        """Kiểm tra CapabilityInstance được tạo với tất cả fields."""
        instance = CapabilityInstance(
            id="create_order",
            type="authorized_mutation",
            description="Tạo đơn hàng mới",
            confidence=0.95,
            params={"permission": "order.create"},
            reads=["Customer"],
            writes=["Order", "OrderItem"],
            emits=["OrderCreated"],
            obligations=["permission_check_required", "tenant_filter_required"],
            tags=["commerce", "critical"],
        )

        assert instance.id == "create_order"
        assert instance.type == "authorized_mutation"
        assert instance.description == "Tạo đơn hàng mới"
        assert instance.confidence == 0.95
        assert instance.params == {"permission": "order.create"}
        assert instance.reads == ["Customer"]
        assert instance.writes == ["Order", "OrderItem"]
        assert instance.emits == ["OrderCreated"]
        assert len(instance.obligations) == 2
        assert len(instance.tags) == 2

    def test_add_obligation_no_duplicates(self):
        """Kiểm tra add_obligation không tạo duplicates."""
        instance = CapabilityInstance(
            id="test_instance",
            type="authorized_mutation",
            obligations=["permission_check_required"],
        )

        # Thêm obligation đã tồn tại
        instance.add_obligation("permission_check_required")

        # Kiểm tra chỉ có 1 instance
        assert instance.obligations.count("permission_check_required") == 1

    def test_add_obligation_adds_new_obligation(self):
        """Kiểm tra add_obligation thêm obligation mới."""
        instance = CapabilityInstance(
            id="test_instance",
            type="authorized_mutation",
            obligations=["permission_check_required"],
        )

        instance.add_obligation("tenant_filter_required")

        assert len(instance.obligations) == 2
        assert "tenant_filter_required" in instance.obligations

    def test_is_high_confidence_threshold(self):
        """Kiểm tra is_high_confidence threshold >= 0.8."""
        high_confidence = CapabilityInstance(
            id="test_high",
            type="authorized_mutation",
            confidence=0.8,
        )
        medium_confidence = CapabilityInstance(
            id="test_medium",
            type="authorized_mutation",
            confidence=0.79,
        )
        low_confidence = CapabilityInstance(
            id="test_low",
            type="authorized_mutation",
            confidence=0.5,
        )

        assert high_confidence.is_high_confidence() is True
        assert medium_confidence.is_high_confidence() is False
        assert low_confidence.is_high_confidence() is False

    def test_confidence_bounds(self):
        """Kiểm tra confidence nằm trong [0.0, 1.0]."""
        instance = CapabilityInstance(
            id="test_bounds",
            type="authorized_mutation",
            confidence=1.0,
        )

        assert 0.0 <= instance.confidence <= 1.0

    def test_instance_to_dict_contains_all_fields(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        instance = CapabilityInstance(
            id="test_instance",
            type="authorized_mutation",
            description="Test description",
            confidence=0.9,
            params={"test": "value"},
            reads=["Entity1"],
            writes=["Entity2"],
            emits=["Event1"],
            obligations=["obligation1"],
            tags=["tag1"],
        )
        instance_dict = instance.to_dict()

        assert instance_dict["id"] == "test_instance"
        assert instance_dict["type"] == "authorized_mutation"
        assert instance_dict["description"] == "Test description"
        assert instance_dict["confidence"] == 0.9
        assert instance_dict["params"] == {"test": "value"}
        assert instance_dict["reads"] == ["Entity1"]
        assert instance_dict["writes"] == ["Entity2"]
        assert instance_dict["emits"] == ["Event1"]
        assert instance_dict["obligations"] == ["obligation1"]
        assert instance_dict["tags"] == ["tag1"]

    def test_instance_from_dict_creates_instance(self):
        """Kiểm tra from_dict tạo CapabilityInstance đúng."""
        instance_data = {
            "id": "test_from_dict",
            "type": "authorized_query",
            "description": "Test from dict",
            "confidence": 0.85,
            "params": {"test": "value"},
            "reads": ["Entity1"],
            "writes": [],
            "emits": [],
            "obligations": ["tenant_filter_required"],
            "tags": ["test"],
        }

        instance = CapabilityInstance.from_dict(instance_data)

        assert instance.id == "test_from_dict"
        assert instance.type == "authorized_query"
        assert instance.description == "Test from dict"
        assert instance.confidence == 0.85
        assert "tenant_filter_required" in instance.obligations

    def test_instance_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        original = CapabilityInstance(
            id="test_roundtrip",
            type="authorized_mutation",
            description="Test roundtrip",
            confidence=0.92,
            params={"permission": "test.create"},
            reads=["Source"],
            writes=["Target"],
            emits=["Created"],
            obligations=["permission_check_required"],
            tags=["test"],
        )

        instance_dict = original.to_dict()
        reconstructed = CapabilityInstance.from_dict(instance_dict)

        assert reconstructed.id == original.id
        assert reconstructed.type == original.type
        assert reconstructed.description == original.description
        assert reconstructed.confidence == original.confidence
        assert reconstructed.params == original.params
        assert reconstructed.reads == original.reads
        assert reconstructed.writes == original.writes
        assert reconstructed.emits == original.emits
        assert reconstructed.obligations == original.obligations
        assert reconstructed.tags == original.tags


class TestMacroCapability:
    """Tests cho MacroCapability class."""

    def test_macro_created_with_required_fields(self):
        """Kiểm tra MacroCapability được tạo với các fields bắt buộc."""
        macro = MacroCapability(
            id="test_macro",
            name="Test Macro",
        )

        assert macro.id == "test_macro"
        assert macro.name == "Test Macro"
        assert macro.description is None
        assert macro.expands_to == []
        assert macro.params_schema == {}
        assert macro.default_obligations == []

    def test_macro_expands_to_non_empty(self):
        """Kiểm tra MacroCapability có expands_to không rỗng."""
        macro = MacroCapability(
            id="test_macro_expands",
            name="Test Macro Expands",
            expands_to=["authorize_permission", "create_record"],
        )

        assert len(macro.expands_to) > 0
        assert "authorize_permission" in macro.expands_to
        assert "create_record" in macro.expands_to

    def test_macro_to_dict_contains_all_fields(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        macro = MacroCapability(
            id="test_macro_dict",
            name="Test Macro Dict",
            description="Test description",
            expands_to=["core1", "core2"],
            params_schema={"field1": {"type": "string"}},
            default_obligations=["obligation1"],
        )
        macro_dict = macro.to_dict()

        assert macro_dict["id"] == "test_macro_dict"
        assert macro_dict["name"] == "Test Macro Dict"
        assert macro_dict["description"] == "Test description"
        assert macro_dict["expands_to"] == ["core1", "core2"]
        assert "field1" in macro_dict["params_schema"]
        assert macro_dict["default_obligations"] == ["obligation1"]

    def test_macro_from_dict_creates_macro(self):
        """Kiểm tra from_dict tạo MacroCapability đúng."""
        macro_data = {
            "id": "test_from_dict",
            "name": "Test From Dict",
            "description": "Test from dict description",
            "expands_to": ["authorize_permission"],
            "params_schema": {"test": {"type": "string"}},
            "default_obligations": ["test_obligation"],
        }

        macro = MacroCapability.from_dict(macro_data)

        assert macro.id == "test_from_dict"
        assert macro.name == "Test From Dict"
        assert macro.description == "Test from dict description"
        assert "authorize_permission" in macro.expands_to
        assert "test_obligation" in macro.default_obligations

    def test_macro_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        original = MacroCapability(
            id="test_roundtrip",
            name="Test Roundtrip",
            description="Test roundtrip description",
            expands_to=["core1", "core2", "core3"],
            params_schema={"field1": {"type": "string"}, "field2": {"type": "integer"}},
            default_obligations=["oblig1", "oblig2"],
        )

        macro_dict = original.to_dict()
        reconstructed = MacroCapability.from_dict(macro_dict)

        assert reconstructed.id == original.id
        assert reconstructed.name == original.name
        assert reconstructed.description == original.description
        assert reconstructed.expands_to == original.expands_to
        assert reconstructed.params_schema == original.params_schema
        assert reconstructed.default_obligations == original.default_obligations


class TestCoreCapability:
    """Tests cho CoreCapability class."""

    def test_core_created_with_required_fields(self):
        """Kiểm tra CoreCapability được tạo với các fields bắt buộc."""
        core = CoreCapability(
            id="test_core",
            name="Test Core",
        )

        assert core.id == "test_core"
        assert core.name == "Test Core"
        assert core.description is None
        assert core.params_schema == {}
        assert core.default_obligations == []
        assert core.read_access == []
        assert core.write_access == []
        assert core.effects == []

    def test_core_with_access_patterns(self):
        """Kiểm tra CoreCapability với access patterns."""
        core = CoreCapability(
            id="test_core_access",
            name="Test Core Access",
            description="Test access patterns",
            read_access=["database", "cache"],
            write_access=["database"],
            effects=["record_created"],
        )

        assert "database" in core.read_access
        assert "cache" in core.read_access
        assert "database" in core.write_access
        assert "record_created" in core.effects

    def test_core_to_dict_contains_all_fields(self):
        """Kiểm tra to_dict chứa tất cả fields."""
        core = CoreCapability(
            id="test_core_dict",
            name="Test Core Dict",
            description="Test description",
            params_schema={"field1": {"type": "string"}},
            default_obligations=["obligation1"],
            read_access=["read1"],
            write_access=["write1"],
            effects=["effect1"],
        )
        core_dict = core.to_dict()

        assert core_dict["id"] == "test_core_dict"
        assert core_dict["name"] == "Test Core Dict"
        assert core_dict["description"] == "Test description"
        assert "field1" in core_dict["params_schema"]
        assert core_dict["default_obligations"] == ["obligation1"]
        assert core_dict["read_access"] == ["read1"]
        assert core_dict["write_access"] == ["write1"]
        assert core_dict["effects"] == ["effect1"]

    def test_core_from_dict_creates_core(self):
        """Kiểm tra from_dict tạo CoreCapability đúng."""
        core_data = {
            "id": "test_from_dict",
            "name": "Test From Dict",
            "description": "Test from dict description",
            "params_schema": {"test": {"type": "string"}},
            "default_obligations": ["test_obligation"],
            "read_access": ["database"],
            "write_access": ["database"],
            "effects": ["record_updated"],
        }

        core = CoreCapability.from_dict(core_data)

        assert core.id == "test_from_dict"
        assert core.name == "Test From Dict"
        assert core.description == "Test from dict description"
        assert "database" in core.read_access
        assert "database" in core.write_access
        assert "record_updated" in core.effects

    def test_core_roundtrip_preserves_state(self):
        """Kiểm tra roundtrip serialization giữ nguyên state."""
        original = CoreCapability(
            id="test_roundtrip",
            name="Test Roundtrip",
            description="Test roundtrip description",
            params_schema={"field1": {"type": "string"}},
            default_obligations=["oblig1"],
            read_access=["read1", "read2"],
            write_access=["write1"],
            effects=["effect1", "effect2"],
        )

        core_dict = original.to_dict()
        reconstructed = CoreCapability.from_dict(core_dict)

        assert reconstructed.id == original.id
        assert reconstructed.name == original.name
        assert reconstructed.description == original.description
        assert reconstructed.params_schema == original.params_schema
        assert reconstructed.default_obligations == original.default_obligations
        assert reconstructed.read_access == original.read_access
        assert reconstructed.write_access == original.write_access
        assert reconstructed.effects == original.effects


class TestCapabilityGraph:
    """Tests cho CapabilityGraph class."""

    def test_graph_created_empty(self):
        """Kiểm tra CapabilityGraph có thể được tạo rỗng."""
        graph = CapabilityGraph()

        assert graph is not None

    def test_graph_add_instance_no_duplicates(self):
        """Kiểm tra add_instance không tạo duplicate IDs."""
        graph = CapabilityGraph()
        instance1 = CapabilityInstance(id="test_instance", type="authorized_mutation")
        instance2 = CapabilityInstance(id="test_instance", type="authorized_query")

        graph.add_instance(instance1)
        graph.add_instance(instance2)

        # Instance thứ 2 sẽ override instance thứ 1 trong cache
        result = graph.get_instance("test_instance")
        assert result is not None
        assert result.id == "test_instance"
        # Type sẽ là của instance thứ 2 (authorized_query)
        assert result.type == "authorized_query"

    def test_graph_get_instance(self):
        """Kiểm tra get_instance trả về instance đúng."""
        graph = CapabilityGraph()
        instance = CapabilityInstance(id="test_get", type="authorized_mutation")

        graph.add_instance(instance)

        result = graph.get_instance("test_get")
        assert result is not None
        assert result.id == "test_get"

    def test_graph_get_instance_not_found(self):
        """Kiểm tra get_instance trả về None khi không tìm thấy."""
        graph = CapabilityGraph()

        result = graph.get_instance("nonexistent")
        assert result is None

    def test_graph_get_instances_by_type(self):
        """Kiểm tra get_instances_by_type trả về instances đúng type."""
        graph = CapabilityGraph()
        instance1 = CapabilityInstance(id="inst1", type="authorized_mutation")
        instance2 = CapabilityInstance(id="inst2", type="authorized_mutation")
        instance3 = CapabilityInstance(id="inst3", type="authorized_query")

        graph.add_instance(instance1)
        graph.add_instance(instance2)
        graph.add_instance(instance3)

        results = graph.get_instances_by_type("authorized_mutation")
        assert len(results) == 2
        assert all(inst.type == "authorized_mutation" for inst in results)

    def test_graph_instance_count(self):
        """Kiểm tra số lượng instances đúng."""
        graph = CapabilityGraph()
        instance1 = CapabilityInstance(id="inst1", type="authorized_mutation")
        instance2 = CapabilityInstance(id="inst2", type="authorized_query")

        graph.add_instance(instance1)
        graph.add_instance(instance2)

        assert len(graph.instances) == 2

    def test_graph_to_dict_contains_instances(self):
        """Kiểm tra to_dict chứa danh sách instances."""
        graph = CapabilityGraph()
        instance = CapabilityInstance(id="test_graph", type="authorized_mutation")

        graph.add_instance(instance)

        graph_dict = graph.to_dict()
        assert "instances" in graph_dict
        assert len(graph_dict["instances"]) == 1

    def test_graph_from_dict_creates_graph(self):
        """Kiểm tra from_dict tạo CapabilityGraph đúng."""
        graph_data = {
            "type": "capability_graph",
            "version": "1.0.0",
            "metadata": {
                "description": "Test graph",
                "tags": ["test"],
            },
            "instances": [
                {
                    "id": "test_from_dict",
                    "type": "authorized_mutation",
                    "description": "Test instance",
                }
            ],
            "core_capabilities": [],
            "macro_capabilities": [],
            "obligations": [],
        }

        graph = CapabilityGraph.from_dict(graph_data)
        assert graph is not None
        assert len(graph.instances) == 1
        assert graph.instances[0].id == "test_from_dict"

    def test_graph_roundtrip_preserves_instances(self):
        """Kiểm tra roundtrip serialization giữ nguyên instances."""
        graph = CapabilityGraph()
        instance = CapabilityInstance(
            id="test_roundtrip",
            type="authorized_mutation",
            description="Test roundtrip instance",
        )

        graph.add_instance(instance)

        graph_dict = graph.to_dict()
        reconstructed = CapabilityGraph.from_dict(graph_dict)

        assert reconstructed.get_instance("test_roundtrip") is not None
        assert reconstructed.get_instance("test_roundtrip").description == "Test roundtrip instance"
