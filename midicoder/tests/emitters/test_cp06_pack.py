# coding: utf-8
"""
Tests cho CP06 pack manifest, error codes, và registry mapping.

Kiểm tra:
- pack.yml tồn tại và đồng bộ với taxonomy.yml
- Error codes MDC-CP06-001 ~ 020 tồn tại
- Registry resolve CP06 capabilities đúng

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
import pytest

from midicoder.errors import ErrorCode


# ===========================================================================
# Pack Manifest Tests
# ===========================================================================

PROJECT_ROOT = Path(__file__).parents[3]  # midicoder-ce root
PACK_YML_PATH = PROJECT_ROOT / "midicoder" / "emitters" / "core" / "gateway" / "pack.yml"
TAXONOMY_PATH = PROJECT_ROOT / "industry" / "taxonomy.yml"


class TestCP06PackManifest:
    """Tests cho pack.yml manifest của CP06."""

    @pytest.fixture
    def pack_data(self) -> dict[str, Any]:
        """Load pack.yml data."""
        assert PACK_YML_PATH.exists(), f"pack.yml không tồn tại tại {PACK_YML_PATH}"
        with open(PACK_YML_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @pytest.fixture
    def taxonomy_data(self) -> dict[str, Any]:
        """Load taxonomy.yml data."""
        assert TAXONOMY_PATH.exists(), f"taxonomy.yml không tồn tại tại {TAXONOMY_PATH}"
        with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_pack_yml_exists(self):
        """pack.yml tồn tại."""
        assert PACK_YML_PATH.exists()

    def test_pack_id_matches(self, pack_data: dict):
        """Pack ID trùng với CP06."""
        assert pack_data["pack"]["id"] == "CP06"

    def test_pack_name_matches(self, pack_data: dict):
        """Pack name đúng."""
        assert "API Gateway" in pack_data["pack"]["name"]

    def test_capabilities_provided(self, pack_data: dict):
        """Capabilities đúng theo spec."""
        caps = pack_data["pack"]["capabilities_provided"]
        assert "route_request" in caps
        assert "gateway_binding" in caps
        assert "service_mesh_config" in caps

    def test_status_is_stable(self, pack_data: dict):
        """Status là stable."""
        assert pack_data["pack"]["status"] == "stable"

    def test_phase_is_p1(self, pack_data: dict):
        """Phase là P1."""
        assert pack_data["pack"]["phase"] == "P1"

    def test_depends_on(self, pack_data: dict):
        """Dependencies đúng."""
        deps = pack_data["pack"]["depends_on"]
        assert "CP01" in deps
        assert "CP05" in deps

    def test_capabilities_sync_with_taxonomy(self, pack_data: dict, taxonomy_data: dict):
        """Capabilities trong pack.yml đồng bộ với taxonomy.yml."""
        # Tìm CP06 trong taxonomy
        cp06 = None
        for cp in taxonomy_data.get("core_packs", []):
            if cp["id"] == "CP06":
                cp06 = cp
                break

        assert cp06 is not None, "CP06 không tìm thấy trong taxonomy.yml"

        pack_caps = set(pack_data["pack"]["capabilities_provided"])
        taxonomy_caps = set(cp06.get("capabilities_provided", []))

        assert pack_caps == taxonomy_caps, (
            f"Mismatch: pack.yml={pack_caps}, taxonomy={taxonomy_caps}"
        )

    def test_templates_defined(self, pack_data: dict):
        """Templates được declare trong pack.yml."""
        templates = pack_data["pack"].get("templates", {})
        assert "route_request" in templates
        assert "gateway_binding" in templates

    def test_frontend_integration_defined(self, pack_data: dict):
        """Frontend integration được declare."""
        frontend = pack_data["pack"].get("frontend_integration", {})
        assert "angular" in frontend
        assert "react" in frontend


# ===========================================================================
# Error Code Tests
# ===========================================================================

class TestCP06ErrorCodes:
    """Tests cho CP06 error codes trong ErrorCode enum."""

    def test_route_validation_codes_exist(self):
        """Route validation error codes tồn tại."""
        assert ErrorCode.CP06_ROUTE_NOT_FOUND.value == "MDC-CP06-001"
        assert ErrorCode.CP06_INVALID_METHOD.value == "MDC-CP06-002"
        assert ErrorCode.CP06_DUPLICATE_PATH.value == "MDC-CP06-003"
        assert ErrorCode.CP06_INVALID_AUTH_CONFIG.value == "MDC-CP06-004"
        assert ErrorCode.CP06_HANDLER_NOT_FOUND.value == "MDC-CP06-005"

    def test_gateway_config_codes_exist(self):
        """Gateway config error codes tồn tại."""
        assert ErrorCode.CP06_GATEWAY_CONFIG_INVALID.value == "MDC-CP06-006"
        assert ErrorCode.CP06_SERVICE_URL_INVALID.value == "MDC-CP06-007"
        assert ErrorCode.CP06_ROUTE_BIND_FAILED.value == "MDC-CP06-008"
        assert ErrorCode.CP06_PLUGIN_CONFIG_INVALID.value == "MDC-CP06-009"
        assert ErrorCode.CP06_UPSTREAM_EMPTY.value == "MDC-CP06-010"

    def test_service_mesh_codes_exist(self):
        """Service mesh error codes tồn tại."""
        assert ErrorCode.CP06_MESH_CONFIG_INVALID.value == "MDC-CP06-011"
        assert ErrorCode.CP06_HEALTH_CHECK_FAILED.value == "MDC-CP06-012"
        assert ErrorCode.CP06_CONNECT_PROXY_ERROR.value == "MDC-CP06-013"
        assert ErrorCode.CP06_SERVICE_REG_FAILED.value == "MDC-CP06-014"
        assert ErrorCode.CP06_TLS_CONFIG_INVALID.value == "MDC-CP06-015"

    def test_kong_consul_codes_exist(self):
        """Kong/Consul integration error codes tồn tại."""
        assert ErrorCode.CP06_KONG_YAML_ERROR.value == "MDC-CP06-016"
        assert ErrorCode.CP06_CONSUL_HCL_ERROR.value == "MDC-CP06-017"
        assert ErrorCode.CP06_PLUGIN_NOT_FOUND.value == "MDC-CP06-018"
        assert ErrorCode.CP06_RATE_LIMIT_EXCEEDED.value == "MDC-CP06-019"
        assert ErrorCode.CP06_CIRCUIT_BREAKER_OPEN.value == "MDC-CP06-020"

    def test_all_20_codes_exist(self):
        """Tất cả 20 error codes tồn tại."""
        cp06_codes = [
            code for code in ErrorCode
            if code.value.startswith("MDC-CP06-")
        ]
        assert len(cp06_codes) == 20, f"Expected 20 CP06 error codes, found {len(cp06_codes)}"


# ===========================================================================
# Registry Mapping Tests
# ===========================================================================

class TestCP06RegistryMapping:
    """Tests cho registry mapping của CP06."""

    def test_registry_resolves_cp06_capabilities(self):
        """Registry resolve đúng pack cho CP06 capabilities."""
        from industry.registry import TaxonomyRegistry

        registry = TaxonomyRegistry.load(TAXONOMY_PATH)

        # Test route_request
        packs = registry.resolve_packs_for_operations(["route_request"])
        pack_ids = [p.id for p in packs]
        assert "CP06" in pack_ids

        # Test gateway_binding
        packs = registry.resolve_packs_for_operations(["gateway_binding"])
        pack_ids = [p.id for p in packs]
        assert "CP06" in pack_ids

        # Test service_mesh_config
        packs = registry.resolve_packs_for_operations(["service_mesh_config"])
        pack_ids = [p.id for p in packs]
        assert "CP06" in pack_ids

    def test_registry_get_cp06(self):
        """Registry get_pack trả về CP06 đúng."""
        from industry.registry import TaxonomyRegistry

        registry = TaxonomyRegistry.load(TAXONOMY_PATH)
        cp06 = registry.get_pack("CP06")

        assert cp06 is not None
        assert cp06.id == "CP06"
        assert cp06.pack_type == "core_pack"
        assert "API Gateway" in cp06.name

    def test_cp06_in_core_packs_query(self):
        """CP06 xuất hiện trong query core_packs."""
        from industry.registry import TaxonomyRegistry

        registry = TaxonomyRegistry.load(TAXONOMY_PATH)
        core_packs = registry.find_packs(pack_type="core_pack")
        ids = [p.id for p in core_packs]
        assert "CP06" in ids
