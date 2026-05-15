# coding: utf-8
"""
Tests cho CP53 — Domain Pack Runtime Bridge.

Kiểm tra:
- models.py: DomainPackDescriptor, BridgeBinding, RuntimeInvoker
- pack.yml tồn tại và đồng bộ với taxonomy.yml
- FastAPIDomainBridgeEmitter.generate() emit đúng files
- NestJSDomainBridgeEmitter.generate() emit đúng files
- Error codes CP53 tồn tại trong ErrorCode enum

Tác giả: Midicoder Team
Version: 1.0.0
"""

import pytest
import yaml
from pathlib import Path

from midicoder.errors import ErrorCode

# Root của project (midicoder-ce/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
# Root của midicoder/
ROOT = Path(__file__).resolve().parent.parent.parent


# ============================================================================
# Tests cho Error Codes
# ============================================================================


class TestErrorCodes:
    """Tests cho error codes CP53 trong ErrorCode enum."""

    def test_cp53_bridge_capability_invalid_exists(self) -> None:
        """Kiểm tra MDC-CP53-001 tồn tại trong ErrorCode."""
        assert hasattr(ErrorCode, "CP53_BRIDGE_CAPABILITY_INVALID")
        assert ErrorCode.CP53_BRIDGE_CAPABILITY_INVALID.value == "MDC-CP53-001"

    def test_cp53_dp_not_registered_exists(self) -> None:
        """Kiểm tra MDC-CP53-002 tồn tại trong ErrorCode."""
        assert hasattr(ErrorCode, "CP53_DP_NOT_REGISTERED")
        assert ErrorCode.CP53_DP_NOT_REGISTERED.value == "MDC-CP53-002"

    def test_cp53_duplicate_dp_id_exists(self) -> None:
        """Kiểm tra MDC-CP53-003 tồn tại trong ErrorCode."""
        assert hasattr(ErrorCode, "CP53_DUPLICATE_DP_ID")
        assert ErrorCode.CP53_DUPLICATE_DP_ID.value == "MDC-CP53-003"

    def test_cp53_invalid_binding_id_exists(self) -> None:
        """Kiểm tra MDC-CP53-004 tồn tại trong ErrorCode."""
        assert hasattr(ErrorCode, "CP53_INVALID_BINDING_ID")
        assert ErrorCode.CP53_INVALID_BINDING_ID.value == "MDC-CP53-004"

    def test_cp53_invoker_config_empty_exists(self) -> None:
        """Kiểm tra MDC-CP53-005 tồn tại trong ErrorCode."""
        assert hasattr(ErrorCode, "CP53_INVOKER_CONFIG_EMPTY")
        assert ErrorCode.CP53_INVOKER_CONFIG_EMPTY.value == "MDC-CP53-005"


# ============================================================================
# Tests cho DomainPackDescriptor
# ============================================================================


class TestDomainPackDescriptor:
    """Tests cho model DomainPackDescriptor."""

    def test_create_valid_descriptor(self) -> None:
        """Tạo DomainPackDescriptor hợp lệ."""
        from midicoder.emitters.core.domain_bridge.models import DomainPackDescriptor

        desc = DomainPackDescriptor(
            pack_id="DP01",
            internal_id="dp01-commerce",
            name="Commerce Core",
            capabilities=["product_catalog", "order_management"],
            depends_on=["CP01", "CP08"],
        )

        assert desc.pack_id == "DP01"
        assert desc.internal_id == "dp01-commerce"
        assert desc.name == "Commerce Core"
        assert len(desc.capabilities) == 2
        assert "product_catalog" in desc.capabilities

    def test_descriptor_empty_pack_id_raises(self) -> None:
        """DomainPackDescriptor với pack_id rỗng sẽ throw error."""
        from midicoder.emitters.core.domain_bridge.models import DomainPackDescriptor
        from midicoder.errors import MidicoderError

        with pytest.raises(MidicoderError) as exc_info:
            DomainPackDescriptor(
                pack_id="",
                internal_id="dp01-commerce",
                name="Commerce Core",
                capabilities=["product_catalog"],
            )

        assert exc_info.value.code == ErrorCode.CP53_DUPLICATE_DP_ID or \
               exc_info.value.code.value.startswith("MDC-CP53")

    def test_descriptor_empty_capabilities_raises(self) -> None:
        """DomainPackDescriptor với capabilities rỗng sẽ throw error."""
        from midicoder.emitters.core.domain_bridge.models import DomainPackDescriptor
        from midicoder.errors import MidicoderError

        with pytest.raises(MidicoderError):
            DomainPackDescriptor(
                pack_id="DP01",
                internal_id="dp01-commerce",
                name="Commerce Core",
                capabilities=[],
            )

    def test_descriptor_to_dict(self) -> None:
        """DomainPackDescriptor.to_dict() serialize đúng."""
        from midicoder.emitters.core.domain_bridge.models import DomainPackDescriptor

        desc = DomainPackDescriptor(
            pack_id="DP01",
            internal_id="dp01-commerce",
            name="Commerce Core",
            capabilities=["product_catalog", "order_management"],
            depends_on=["CP01"],
        )

        d = desc.to_dict()

        assert d["pack_id"] == "DP01"
        assert d["internal_id"] == "dp01-commerce"
        assert d["name"] == "Commerce Core"
        assert len(d["capabilities"]) == 2

    def test_descriptor_from_dict(self) -> None:
        """DomainPackDescriptor.from_dict() deserialize đúng."""
        from midicoder.emitters.core.domain_bridge.models import DomainPackDescriptor

        data = {
            "pack_id": "DP02",
            "internal_id": "dp02-marketplace",
            "name": "Marketplace Core",
            "capabilities": ["seller_management", "commission"],
            "depends_on": ["CP01", "CP08"],
            "metadata": {"tier": "premium"},
        }

        desc = DomainPackDescriptor.from_dict(data)

        assert desc.pack_id == "DP02"
        assert desc.internal_id == "dp02-marketplace"
        assert desc.name == "Marketplace Core"
        assert desc.metadata.get("tier") == "premium"


# ============================================================================
# Tests cho BridgeBinding
# ============================================================================


class TestBridgeBinding:
    """Tests cho model BridgeBinding."""

    def test_create_valid_binding(self) -> None:
        """Tạo BridgeBinding hợp lệ."""
        from midicoder.emitters.core.domain_bridge.models import BridgeBinding

        binding = BridgeBinding(
            binding_id="bind-001",
            cp_capability="create_record",
            dp_pack_id="DP01",
            dp_handler="commerce_create_handler",
        )

        assert binding.binding_id == "bind-001"
        assert binding.cp_capability == "create_record"
        assert binding.dp_pack_id == "DP01"
        assert binding.dp_handler == "commerce_create_handler"

    def test_binding_empty_cp_capability_raises(self) -> None:
        """BridgeBinding với cp_capability rỗng sẽ throw error (Obligation 1)."""
        from midicoder.emitters.core.domain_bridge.models import BridgeBinding
        from midicoder.errors import MidicoderError

        with pytest.raises(MidicoderError) as exc_info:
            BridgeBinding(
                binding_id="bind-001",
                cp_capability="",
                dp_pack_id="DP01",
                dp_handler="handler",
            )

        assert exc_info.value.code == ErrorCode.CP53_BRIDGE_CAPABILITY_INVALID

    def test_binding_empty_dp_pack_id_raises(self) -> None:
        """BridgeBinding với dp_pack_id rỗng sẽ throw error."""
        from midicoder.emitters.core.domain_bridge.models import BridgeBinding
        from midicoder.errors import MidicoderError

        with pytest.raises(MidicoderError):
            BridgeBinding(
                binding_id="bind-001",
                cp_capability="create_record",
                dp_pack_id="",
                dp_handler="handler",
            )

    def test_binding_empty_binding_id_raises(self) -> None:
        """BridgeBinding với binding_id rỗng sẽ throw error (MDC-CP53-004)."""
        from midicoder.emitters.core.domain_bridge.models import BridgeBinding
        from midicoder.errors import MidicoderError

        with pytest.raises(MidicoderError) as exc_info:
            BridgeBinding(
                binding_id="",
                cp_capability="create_record",
                dp_pack_id="DP01",
                dp_handler="handler",
            )

        assert exc_info.value.code == ErrorCode.CP53_INVALID_BINDING_ID

    def test_binding_to_dict(self) -> None:
        """BridgeBinding.to_dict() serialize đúng."""
        from midicoder.emitters.core.domain_bridge.models import BridgeBinding

        binding = BridgeBinding(
            binding_id="bind-001",
            cp_capability="create_record",
            dp_pack_id="DP01",
            dp_handler="commerce_create_handler",
        )

        d = binding.to_dict()

        assert d["binding_id"] == "bind-001"
        assert d["cp_capability"] == "create_record"
        assert d["dp_pack_id"] == "DP01"

    def test_binding_from_dict(self) -> None:
        """BridgeBinding.from_dict() deserialize đúng."""
        from midicoder.emitters.core.domain_bridge.models import BridgeBinding

        data = {
            "binding_id": "bind-002",
            "cp_capability": "query_records",
            "dp_pack_id": "DP02",
            "dp_handler": "marketplace_query_handler",
            "priority": 10,
        }

        binding = BridgeBinding.from_dict(data)

        assert binding.binding_id == "bind-002"
        assert binding.cp_capability == "query_records"
        assert binding.priority == 10


# ============================================================================
# Tests cho RuntimeInvoker
# ============================================================================


class TestRuntimeInvoker:
    """Tests cho model RuntimeInvoker."""

    def test_create_valid_invoker(self) -> None:
        """Tạo RuntimeInvoker hợp lệ."""
        from midicoder.emitters.core.domain_bridge.models import RuntimeInvoker

        invoker = RuntimeInvoker(
            capability="create_record",
            dp_pack_id="DP01",
            handler_method="handle_create",
        )

        assert invoker.capability == "create_record"
        assert invoker.dp_pack_id == "DP01"
        assert invoker.handler_method == "handle_create"

    def test_invoker_empty_capability_raises(self) -> None:
        """RuntimeInvoker với capability rỗng sẽ throw error."""
        from midicoder.emitters.core.domain_bridge.models import RuntimeInvoker
        from midicoder.errors import MidicoderError

        with pytest.raises(MidicoderError):
            RuntimeInvoker(
                capability="",
                dp_pack_id="DP01",
                handler_method="handle_create",
            )

    def test_invoker_empty_dp_target_raises(self) -> None:
        """RuntimeInvoker với dp_pack_id rỗng sẽ throw error (Obligation 2)."""
        from midicoder.emitters.core.domain_bridge.models import RuntimeInvoker
        from midicoder.errors import MidicoderError

        with pytest.raises(MidicoderError) as exc_info:
            RuntimeInvoker(
                capability="create_record",
                dp_pack_id="",
                handler_method="handle_create",
            )

        assert exc_info.value.code == ErrorCode.CP53_DP_NOT_REGISTERED

    def test_invoker_empty_handler_raises(self) -> None:
        """RuntimeInvoker với handler_method rỗng sẽ throw error."""
        from midicoder.emitters.core.domain_bridge.models import RuntimeInvoker
        from midicoder.errors import MidicoderError

        with pytest.raises(MidicoderError):
            RuntimeInvoker(
                capability="create_record",
                dp_pack_id="DP01",
                handler_method="",
            )

    def test_invoker_to_dict(self) -> None:
        """RuntimeInvoker.to_dict() serialize đúng."""
        from midicoder.emitters.core.domain_bridge.models import RuntimeInvoker

        invoker = RuntimeInvoker(
            capability="create_record",
            dp_pack_id="DP01",
            handler_method="handle_create",
        )

        d = invoker.to_dict()

        assert d["capability"] == "create_record"
        assert d["dp_pack_id"] == "DP01"
        assert d["handler_method"] == "handle_create"

    def test_invoker_from_dict(self) -> None:
        """RuntimeInvoker.from_dict() deserialize đúng."""
        from midicoder.emitters.core.domain_bridge.models import RuntimeInvoker

        data = {
            "capability": "query_records",
            "dp_pack_id": "DP01",
            "handler_method": "handle_query",
            "timeout_ms": 5000,
            "retry_count": 3,
        }

        invoker = RuntimeInvoker.from_dict(data)

        assert invoker.capability == "query_records"
        assert invoker.timeout_ms == 5000
        assert invoker.retry_count == 3


# ============================================================================
# Tests cho pack.yml
# ============================================================================


class TestPackYml:
    """Tests cho pack.yml của CP53."""

    def test_pack_yml_exists(self) -> None:
        """Kiểm tra pack.yml tồn tại."""
        pack_yml = ROOT / "emitters/core/domain_bridge/pack.yml"
        assert pack_yml.exists(), f"pack.yml không tồn tại tại {pack_yml}"

    def test_pack_yml_has_correct_id(self) -> None:
        """Kiểm tra pack.yml có id=CP53."""
        pack_yml = ROOT / "emitters/core/domain_bridge/pack.yml"
        with open(pack_yml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["id"] == "CP53"

    def test_pack_yml_capabilities_match_taxonomy(self) -> None:
        """Kiểm tra capabilities_provided trong pack.yml match taxonomy.yml."""
        pack_yml = ROOT / "emitters/core/domain_bridge/pack.yml"
        taxonomy_yml = PROJECT_ROOT / "industry/taxonomy.yml"

        with open(pack_yml, "r", encoding="utf-8") as f:
            pack_data = yaml.safe_load(f)

        with open(taxonomy_yml, "r", encoding="utf-8") as f:
            taxonomy_data = yaml.safe_load(f)

        # Tìm CP53 trong taxonomy
        cp53 = None
        for pack in taxonomy_data.get("core_packs", []):
            if pack.get("id") == "CP53":
                cp53 = pack
                break

        assert cp53 is not None, "CP53 không tồn tại trong taxonomy.yml"

        pack_caps = set(pack_data["pack"]["capabilities_provided"])
        taxonomy_caps = set(cp53.get("capabilities_provided", []))

        assert pack_caps == taxonomy_caps, (
            f"capabilities_provided không match: pack.yml={pack_caps}, "
            f"taxonomy.yml={taxonomy_caps}"
        )

    def test_pack_yml_capabilities_correct(self) -> None:
        """Kiểm tra capabilities_provided đúng: bridge_domain_pack, runtime_invoke."""
        pack_yml = ROOT / "emitters/core/domain_bridge/pack.yml"
        with open(pack_yml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        caps = data["pack"]["capabilities_provided"]
        assert "bridge_domain_pack" in caps
        assert "runtime_invoke" in caps

    def test_pack_yml_depends_on_cp01_and_cp51(self) -> None:
        """Kiểm tra pack.yml depends_on CP01 và CP51."""
        pack_yml = ROOT / "emitters/core/domain_bridge/pack.yml"
        with open(pack_yml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        deps = data["pack"]["depends_on"]
        assert "CP01" in deps
        assert "CP51" in deps


# ============================================================================
# Tests cho FastAPI Emitter
# ============================================================================


class TestFastAPIEmitter:
    """Tests cho FastAPIDomainBridgeEmitter."""

    def test_emitter_class_exists(self) -> None:
        """Kiểm tra FastAPIDomainBridgeEmitter class tồn tại."""
        from midicoder.emitters.core.domain_bridge.fastapi import FastAPIDomainBridgeEmitter
        emitter = FastAPIDomainBridgeEmitter()
        assert emitter is not None

    def test_generate_returns_dict(self) -> None:
        """Kiểm tra generate() trả về dict."""
        from midicoder.emitters.core.domain_bridge.fastapi import FastAPIDomainBridgeEmitter

        emitter = FastAPIDomainBridgeEmitter()
        result = emitter.generate()

        assert isinstance(result, dict)
        assert len(result) > 0

    def test_generate_has_required_files(self) -> None:
        """Kiểm tra generate() emit các file bắt buộc."""
        from midicoder.emitters.core.domain_bridge.fastapi import FastAPIDomainBridgeEmitter

        emitter = FastAPIDomainBridgeEmitter()
        result = emitter.generate()

        keys = list(result.keys())
        # Phải có registry, bindings, invoker
        has_registry = any("registry" in k for k in keys)
        has_bindings = any("binding" in k for k in keys)
        has_invoker = any("invoker" in k for k in keys)

        assert has_registry, f"Thiếu registry file. Có: {keys}"
        assert has_bindings, f"Thiếu bindings file. Có: {keys}"
        assert has_invoker, f"Thiếu invoker file. Có: {keys}"

    def test_generated_code_is_valid_python(self) -> None:
        """Kiểm tra code emit ra là Python hợp lệ."""
        from midicoder.emitters.core.domain_bridge.fastapi import FastAPIDomainBridgeEmitter

        emitter = FastAPIDomainBridgeEmitter()
        result = emitter.generate()

        for path, code in result.items():
            # Compile code để kiểm tra syntax
            try:
                compile(code, path, "exec")
            except SyntaxError as e:
                pytest.fail(f"SyntaxError trong {path}: {e}")


# ============================================================================
# Tests cho NestJS Emitter
# ============================================================================


class TestNestJSEmitter:
    """Tests cho NestJSDomainBridgeEmitter."""

    def test_emitter_class_exists(self) -> None:
        """Kiểm tra NestJSDomainBridgeEmitter class tồn tại."""
        from midicoder.emitters.core.domain_bridge.nestjs import NestJSDomainBridgeEmitter
        emitter = NestJSDomainBridgeEmitter()
        assert emitter is not None

    def test_generate_returns_dict(self) -> None:
        """Kiểm tra generate() trả về dict."""
        from midicoder.emitters.core.domain_bridge.nestjs import NestJSDomainBridgeEmitter

        emitter = NestJSDomainBridgeEmitter()
        result = emitter.generate()

        assert isinstance(result, dict)
        assert len(result) > 0

    def test_generate_has_required_files(self) -> None:
        """Kiểm tra generate() emit các file bắt buộc."""
        from midicoder.emitters.core.domain_bridge.nestjs import NestJSDomainBridgeEmitter

        emitter = NestJSDomainBridgeEmitter()
        result = emitter.generate()

        keys = list(result.keys())
        # Phải có registry, bindings, invoker
        has_registry = any("registry" in k for k in keys)
        has_bindings = any("binding" in k for k in keys)
        has_invoker = any("invoker" in k for k in keys)

        assert has_registry, f"Thiếu registry file. Có: {keys}"
        assert has_bindings, f"Thiếu bindings file. Có: {keys}"
        assert has_invoker, f"Thiếu invoker file. Có: {keys}"


# ============================================================================
# Tests cho __init__.py exports
# ============================================================================


class TestExports:
    """Tests cho exports của domain_bridge module."""

    def test_exports_domain_pack_descriptor(self) -> None:
        """Kiểm tra export DomainPackDescriptor."""
        from midicoder.emitters.core.domain_bridge import DomainPackDescriptor
        assert DomainPackDescriptor is not None

    def test_exports_bridge_binding(self) -> None:
        """Kiểm tra export BridgeBinding."""
        from midicoder.emitters.core.domain_bridge import BridgeBinding
        assert BridgeBinding is not None

    def test_exports_runtime_invoker(self) -> None:
        """Kiểm tra export RuntimeInvoker."""
        from midicoder.emitters.core.domain_bridge import RuntimeInvoker
        assert RuntimeInvoker is not None

    def test_exports_fastapi_emitter(self) -> None:
        """Kiểm tra export FastAPIDomainBridgeEmitter."""
        from midicoder.emitters.core.domain_bridge import FastAPIDomainBridgeEmitter
        assert FastAPIDomainBridgeEmitter is not None

    def test_exports_nestjs_emitter(self) -> None:
        """Kiểm tra export NestJSDomainBridgeEmitter."""
        from midicoder.emitters.core.domain_bridge import NestJSDomainBridgeEmitter
        assert NestJSDomainBridgeEmitter is not None


# ============================================================================
# Tests cho PackResolver integration
# ============================================================================


class TestPackResolverIntegration:
    """Tests cho integration của CP53 với CP_ID_TO_INTERNAL registry."""

    def test_registry_maps_cp53_to_domain_bridge(self) -> None:
        """Kiểm tra CP_ID_TO_INTERNAL mapping CP53 → cp53_domain_bridge."""
        from midicoder.contracts.registry import CP_ID_TO_INTERNAL

        assert CP_ID_TO_INTERNAL.get("CP53") == "cp53_domain_bridge"
