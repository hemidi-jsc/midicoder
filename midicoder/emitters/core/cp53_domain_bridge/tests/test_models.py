# coding: utf-8
"""
Tests cho CP53 — Domain Pack Runtime Bridge models.

Phạm vi: import tất cả classes từ __init__.py, basic model creation,
to_dict / from_dict round-trip, validation errors.
"""

import pytest
from midicoder.emitters.core.cp53_domain_bridge.models import (
    DomainPackDescriptor,
    BridgeBinding,
    RuntimeInvoker,
)


# ---------------------------------------------------------------------------
# DomainPackDescriptor
# ---------------------------------------------------------------------------

class TestDomainPackDescriptor:
    def test_creation(self):
        dpd = DomainPackDescriptor(
            pack_id="DP01",
            internal_id="dp01-commerce",
            name="Commerce Pack",
            capabilities=["payment", "order"],
            depends_on=["CP01", "CP08"],
        )
        assert dpd.pack_id == "DP01"
        assert dpd.internal_id == "dp01-commerce"
        assert dpd.depends_on == ["CP01", "CP08"]

    def test_to_dict(self):
        dpd = DomainPackDescriptor(
            pack_id="DP02",
            internal_id="dp02-healthcare",
            name="Healthcare",
            capabilities=["patient_record"],
            metadata={"version": "1.0"},
        )
        d = dpd.to_dict()
        assert d["pack_id"] == "DP02"
        assert d["metadata"]["version"] == "1.0"

    def test_from_dict(self):
        data = {
            "pack_id": "DP03",
            "internal_id": "dp03",
            "name": "Test DP",
            "capabilities": ["cap1"],
            "depends_on": ["CP01"],
        }
        dpd = DomainPackDescriptor.from_dict(data)
        assert dpd.pack_id == "DP03"
        assert dpd.capabilities == ["cap1"]

    def test_roundtrip(self):
        original = DomainPackDescriptor(
            pack_id="DP01",
            internal_id="dp01",
            name="Commerce",
            capabilities=["payment"],
            depends_on=["CP01"],
            metadata={"k": "v"},
        )
        restored = DomainPackDescriptor.from_dict(original.to_dict())
        assert restored.pack_id == original.pack_id
        assert restored.metadata == original.metadata

    def test_empty_pack_id_raises(self):
        with pytest.raises(Exception):
            DomainPackDescriptor(
                pack_id="",
                internal_id="dp",
                name="N",
                capabilities=["c"],
            )

    def test_empty_capabilities_raises(self):
        with pytest.raises(Exception):
            DomainPackDescriptor(
                pack_id="DP01",
                internal_id="dp",
                name="N",
                capabilities=[],
            )


# ---------------------------------------------------------------------------
# BridgeBinding
# ---------------------------------------------------------------------------

class TestBridgeBinding:
    def test_creation(self):
        bb = BridgeBinding(
            binding_id="BB-001",
            cp_capability="create_record",
            dp_pack_id="DP01",
            dp_handler="handle_create",
            priority=10,
        )
        assert bb.binding_id == "BB-001"
        assert bb.priority == 10

    def test_creation_with_defaults(self):
        bb = BridgeBinding(
            binding_id="BB-002",
            cp_capability="query",
            dp_pack_id="DP02",
            dp_handler="handle_query",
        )
        assert bb.priority == 0
        assert bb.metadata == {}

    def test_to_dict(self):
        bb = BridgeBinding(
            binding_id="BB-003",
            cp_capability="update",
            dp_pack_id="DP01",
            dp_handler="handle_update",
            metadata={"v": 2},
        )
        d = bb.to_dict()
        assert d["cp_capability"] == "update"
        assert d["metadata"]["v"] == 2

    def test_from_dict(self):
        data = {
            "binding_id": "BB-004",
            "cp_capability": "delete",
            "dp_pack_id": "DP03",
            "dp_handler": "handle_delete",
            "priority": 5,
        }
        bb = BridgeBinding.from_dict(data)
        assert bb.dp_pack_id == "DP03"
        assert bb.priority == 5

    def test_roundtrip(self):
        original = BridgeBinding(
            binding_id="BB-001",
            cp_capability="create",
            dp_pack_id="DP01",
            dp_handler="create_handler",
            priority=1,
        )
        restored = BridgeBinding.from_dict(original.to_dict())
        assert restored.binding_id == original.binding_id
        assert restored.dp_handler == original.dp_handler

    def test_empty_cp_capability_raises(self):
        with pytest.raises(Exception):
            BridgeBinding(
                binding_id="BB",
                cp_capability="",
                dp_pack_id="DP01",
                dp_handler="h",
            )

    def test_empty_binding_id_raises(self):
        with pytest.raises(Exception):
            BridgeBinding(
                binding_id="",
                cp_capability="cap",
                dp_pack_id="DP01",
                dp_handler="h",
            )

    def test_empty_dp_pack_id_raises(self):
        with pytest.raises(Exception):
            BridgeBinding(
                binding_id="BB",
                cp_capability="cap",
                dp_pack_id="",
                dp_handler="h",
            )


# ---------------------------------------------------------------------------
# RuntimeInvoker
# ---------------------------------------------------------------------------

class TestRuntimeInvoker:
    def test_creation(self):
        ri = RuntimeInvoker(
            capability="create_record",
            dp_pack_id="DP01",
            handler_method="create",
        )
        assert ri.timeout_ms == 30000
        assert ri.retry_count == 0

    def test_creation_with_custom_timeout(self):
        ri = RuntimeInvoker(
            capability="query",
            dp_pack_id="DP02",
            handler_method="query",
            timeout_ms=5000,
            retry_count=3,
        )
        assert ri.timeout_ms == 5000
        assert ri.retry_count == 3

    def test_to_dict(self):
        ri = RuntimeInvoker(
            capability="update",
            dp_pack_id="DP01",
            handler_method="update",
            timeout_ms=10000,
            metadata={"key": "val"},
        )
        d = ri.to_dict()
        assert d["timeout_ms"] == 10000
        assert d["metadata"]["key"] == "val"

    def test_from_dict(self):
        data = {
            "capability": "delete",
            "dp_pack_id": "DP03",
            "handler_method": "delete",
            "timeout_ms": 60000,
            "retry_count": 5,
        }
        ri = RuntimeInvoker.from_dict(data)
        assert ri.handler_method == "delete"
        assert ri.retry_count == 5

    def test_roundtrip(self):
        original = RuntimeInvoker(
            capability="create",
            dp_pack_id="DP01",
            handler_method="handle_create",
            timeout_ms=15000,
            retry_count=2,
        )
        restored = RuntimeInvoker.from_dict(original.to_dict())
        assert restored.timeout_ms == 15000
        assert restored.retry_count == 2

    def test_empty_capability_raises(self):
        with pytest.raises(Exception):
            RuntimeInvoker(
                capability="",
                dp_pack_id="DP01",
                handler_method="h",
            )

    def test_empty_dp_pack_id_raises(self):
        with pytest.raises(Exception):
            RuntimeInvoker(
                capability="cap",
                dp_pack_id="",
                handler_method="h",
            )

    def test_empty_handler_method_raises(self):
        with pytest.raises(Exception):
            RuntimeInvoker(
                capability="cap",
                dp_pack_id="DP01",
                handler_method="",
            )
