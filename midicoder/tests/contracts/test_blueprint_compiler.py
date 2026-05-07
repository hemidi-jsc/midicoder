"""
Tests cho Blueprint Compiler - E07-017.

Tuân thủ TDD, kiểm tra:
- Blueprint validation rules (V001-V010)
- Dependency resolution (CP, DP, RX)
- Blueprint compilation workflow
- Contracts generation

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import yaml

from midicoder.contracts.blueprint_compiler import (
    BlueprintCompiler,
    BlueprintMetadata,
    IndustryInfo,
    CorePacksConfig,
    DomainPackRef,
    RegulatoryOverlayRef,
    InvariantsConfig,
    BusinessInvariant,
    ComplianceInvariant,
    FailureModeInvariant,
    BlueprintConfig,
    BlueprintReferences,
    CompiledBlueprint,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def compiler() -> BlueprintCompiler:
    """Blueprint Compiler instance."""
    return BlueprintCompiler()


@pytest.fixture
def sample_blueprint_data() -> dict[str, Any]:
    """Sample valid blueprint data."""
    now = datetime.utcnow().isoformat()
    return {
        "$schema": "industry-blueprint-v1",
        "metadata": {
            "version": "1.0.0",
            "created_at": now,
            "updated_at": now,
            "industry_id": "ecommerce-d2c",
            "name": "E-commerce D2C",
            "group": "Commerce/Logistics/Ops",
            "status": "draft"
        },
        "industry": {
            "id": "ecommerce-d2c",
            "name": "E-commerce D2C",
            "group": "Commerce/Logistics/Ops",
            "priority": 1,
            "complexity": "medium",
            "regulatory_risk": "low",
            "commercial_priority": "critical"
        },
        "core_packs": {
            "mandatory": ["CP01", "CP02", "CP03", "CP04", "CP07"],
            "included": ["CP05", "CP08", "CP14"],
            "excluded": [],
            "experimental": []
        },
        "domain_packs": [
            {"id": "DP01", "required": True, "config": {}},
            {"id": "DP12"}
        ],
        "regulatory_overlays": [
            {"id": "RX01", "strict_mode": True},
            {"id": "RX06"},
            {"id": "RX10"},
            {"id": "RX11", "strict_mode": True}
        ],
        "target_profiles": ["local", "aws"],
        "invariants": {
            "business": [
                {"id": "INV001", "name": "Order Status Valid", "description": "Order status phải hợp lệ", "enforcement": "compile-time"}
            ],
            "compliance": [
                {"id": "COMP001", "overlay": "RX01", "description": "PII encryption required", "controls": ["encryption_at_rest"]}
            ],
            "failure_modes": [
                {"id": "FAIL001", "scenario": "Payment gateway timeout", "handling": "retry_with_backoff"}
            ]
        },
        "config": {
            "default_tenant_mode": "schema",
            "default_auth_strategy": "jwt",
            "default_db_engine": "postgres"
        },
        "references": {
            "brief_path": "industry/briefs/ecommerce-d2c.md"
        }
    }


@pytest.fixture
def valid_blueprint(compiler: BlueprintCompiler, sample_blueprint_data: dict[str, Any]) -> CompiledBlueprint:
    """Valid compiled blueprint."""
    return compiler._parse_blueprint(sample_blueprint_data)


@pytest.fixture
def temp_blueprint_file(sample_blueprint_data: dict[str, Any], tmp_path: Path) -> Path:
    """Create temporary blueprint file."""
    blueprint_file = tmp_path / "test-blueprint.yml"
    with open(blueprint_file, 'w', encoding='utf-8') as f:
        yaml.dump(sample_blueprint_data, f)
    return blueprint_file


# ============================================================================
# Test Blueprint Parsing
# ============================================================================


class TestBlueprintParsing:
    """Tests cho blueprint parsing."""

    def test_parse_valid_blueprint(
        self, compiler: BlueprintCompiler, sample_blueprint_data: dict[str, Any]
    ) -> None:
        """Kiểm tra parse valid blueprint."""
        blueprint = compiler._parse_blueprint(sample_blueprint_data)
        
        assert blueprint is not None
        assert blueprint.schema_version == "industry-blueprint-v1"
        assert blueprint.industry.id == "ecommerce-d2c"
        assert len(blueprint.core_packs.mandatory) == 5
        assert len(blueprint.domain_packs) == 2
        assert len(blueprint.regulatory_overlays) == 4

    def test_parse_blueprint_preserves_metadata(
        self, valid_blueprint: CompiledBlueprint
    ) -> None:
        """Kiểm tra metadata được preserve."""
        assert valid_blueprint.metadata.version == "1.0.0"
        assert valid_blueprint.metadata.status == "draft"
        assert valid_blueprint.metadata.created_at is not None

    def test_parse_blueprint_preserves_config(
        self, valid_blueprint: CompiledBlueprint
    ) -> None:
        """Kiểm tra config được preserve."""
        from midicoder.emitters.core.tenant.models import TenantMode
        assert valid_blueprint.config.tenant_config.mode == TenantMode.SCHEMA
        assert valid_blueprint.config.default_auth_strategy == "jwt"
        assert valid_blueprint.config.default_db_engine == "postgres"

    def test_parse_blueprint_preserves_invariants(
        self, valid_blueprint: CompiledBlueprint
    ) -> None:
        """Kiểm tra invariants được preserve."""
        assert len(valid_blueprint.invariants.business) == 1
        assert len(valid_blueprint.invariants.compliance) == 1
        assert len(valid_blueprint.invariants.failure_modes) == 1
        assert valid_blueprint.invariants.business[0].id == "INV001"


# ============================================================================
# Test Validation Rules - P0 Core Packs (V001)
# ============================================================================


class TestValidationV001_P0CorePacks:
    """Tests cho V001: P0 Core Packs validation."""

    def test_v001_all_p0_packs_included(
        self, valid_blueprint: CompiledBlueprint
    ) -> None:
        """Kiểm tra V001 pass khi tất cả P0 packs được include."""
        errors = valid_blueprint.validate()
        v001_errors = [e for e in errors if e.startswith("V001")]
        assert len(v001_errors) == 0, f"V001 errors: {v001_errors}"

    def test_v001_missing_cp01(
        self, compiler: BlueprintCompiler, sample_blueprint_data: dict[str, Any]
    ) -> None:
        """Kiểm tra V001 error khi thiếu CP01."""
        sample_blueprint_data["core_packs"]["mandatory"] = ["CP02", "CP03", "CP04", "CP07"]
        blueprint = compiler._parse_blueprint(sample_blueprint_data)
        
        errors = blueprint.validate()
        v001_errors = [e for e in errors if e.startswith("V001")]
        assert len(v001_errors) == 1
        assert "CP01" in v001_errors[0]

    def test_v001_missing_cp07(
        self, compiler: BlueprintCompiler, sample_blueprint_data: dict[str, Any]
    ) -> None:
        """Kiểm tra V001 error khi thiếu CP07."""
        sample_blueprint_data["core_packs"]["mandatory"] = ["CP01", "CP02", "CP03", "CP04"]
        blueprint = compiler._parse_blueprint(sample_blueprint_data)
        
        errors = blueprint.validate()
        v001_errors = [e for e in errors if e.startswith("V001")]
        assert len(v001_errors) == 1
        assert "CP07" in v001_errors[0]

    def test_v001_multiple_p0_packs_missing(
        self, compiler: BlueprintCompiler, sample_blueprint_data: dict[str, Any]
    ) -> None:
        """Kiểm tra V001 multiple errors khi thiếu nhiều P0 packs."""
        sample_blueprint_data["core_packs"]["mandatory"] = ["CP01", "CP02"]
        blueprint = compiler._parse_blueprint(sample_blueprint_data)
        
        errors = blueprint.validate()
        v001_errors = [e for e in errors if e.startswith("V001")]
        assert len(v001_errors) == 3  # Thiếu CP03, CP04, CP07


# ============================================================================
# Test Validation Rules - Universal RX (V002)
# ============================================================================


class TestValidationV002_UniversalRX:
    """Tests cho V002: Universal Regulatory Overlays validation."""

    def test_v002_all_universal_rx_included(
        self, valid_blueprint: CompiledBlueprint
    ) -> None:
        """Kiểm tra V002 pass khi tất cả universal RX được include."""
        errors = valid_blueprint.validate()
        v002_errors = [e for e in errors if e.startswith("V002")]
        assert len(v002_errors) == 0, f"V002 errors: {v002_errors}"

    def test_v002_missing_rx01(
        self, compiler: BlueprintCompiler, sample_blueprint_data: dict[str, Any]
    ) -> None:
        """Kiểm tra V002 error khi thiếu RX01."""
        sample_blueprint_data["regulatory_overlays"] = [
            {"id": "RX06"}, {"id": "RX11"}
        ]
        blueprint = compiler._parse_blueprint(sample_blueprint_data)
        
        errors = blueprint.validate()
        v002_errors = [e for e in errors if e.startswith("V002")]
        assert len(v002_errors) == 1
        assert "RX01" in v002_errors[0]

    def test_v002_missing_rx11(
        self, compiler: BlueprintCompiler, sample_blueprint_data: dict[str, Any]
    ) -> None:
        """Kiểm tra V002 error khi thiếu RX11."""
        sample_blueprint_data["regulatory_overlays"] = [
            {"id": "RX01"}, {"id": "RX06"}
        ]
        blueprint = compiler._parse_blueprint(sample_blueprint_data)
        
        errors = blueprint.validate()
        v002_errors = [e for e in errors if e.startswith("V002")]
        assert len(v002_errors) == 1
        assert "RX11" in v002_errors[0]


# ============================================================================
# Test Validation Rules - Domain Pack IDs (V003)
# ============================================================================


class TestValidationV003_DomainPackIDs:
    """Tests cho V003: Domain Pack ID validation."""

    def test_v003_valid_dp_ids(
        self, valid_blueprint: CompiledBlueprint
    ) -> None:
        """Kiểm tra V003 pass khi DP IDs hợp lệ."""
        errors = valid_blueprint.validate()
        v003_errors = [e for e in errors if e.startswith("V003")]
        assert len(v003_errors) == 0

    def test_v003_invalid_dp_id(
        self, compiler: BlueprintCompiler, sample_blueprint_data: dict[str, Any]
    ) -> None:
        """Kiểm tra V003 error khi DP ID không hợp lệ."""
        sample_blueprint_data["domain_packs"] = [
            {"id": "DP99"},  # Invalid
        ]
        blueprint = compiler._parse_blueprint(sample_blueprint_data)
        
        errors = blueprint.validate()
        v003_errors = [e for e in errors if e.startswith("V003")]
        assert len(v003_errors) == 1
        assert "DP99" in v003_errors[0]


# ============================================================================
# Test Validation Rules - Regulatory Overlay IDs (V004)
# ============================================================================


class TestValidationV004_RegulatoryOverlayIDs:
    """Tests cho V004: Regulatory Overlay ID validation."""

    def test_v004_valid_rx_ids(
        self, valid_blueprint: CompiledBlueprint
    ) -> None:
        """Kiểm tra V004 pass khi RX IDs hợp lệ."""
        errors = valid_blueprint.validate()
        v004_errors = [e for e in errors if e.startswith("V004")]
        assert len(v004_errors) == 0

    def test_v004_invalid_rx_id(
        self, compiler: BlueprintCompiler, sample_blueprint_data: dict[str, Any]
    ) -> None:
        """Kiểm tra V004 error khi RX ID không hợp lệ."""
        sample_blueprint_data["regulatory_overlays"] = [
            {"id": "RX99"},  # Invalid
        ]
        blueprint = compiler._parse_blueprint(sample_blueprint_data)
        
        errors = blueprint.validate()
        v004_errors = [e for e in errors if e.startswith("V004")]
        assert len(v004_errors) == 1
        assert "RX99" in v004_errors[0]


# ============================================================================
# Test Validation Rules - Target Profiles (V005)
# ============================================================================


class TestValidationV005_TargetProfiles:
    """Tests cho V005: Target Profile validation."""

    def test_v005_valid_profiles(
        self, valid_blueprint: CompiledBlueprint
    ) -> None:
        """Kiểm tra V005 pass khi target profiles hợp lệ."""
        errors = valid_blueprint.validate()
        v005_errors = [e for e in errors if e.startswith("V005")]
        assert len(v005_errors) == 0

    def test_v005_invalid_profile(
        self, compiler: BlueprintCompiler, sample_blueprint_data: dict[str, Any]
    ) -> None:
        """Kiểm tra V005 error khi target profile không hợp lệ."""
        sample_blueprint_data["target_profiles"] = ["local", "invalid-cloud"]
        blueprint = compiler._parse_blueprint(sample_blueprint_data)
        
        errors = blueprint.validate()
        v005_errors = [e for e in errors if e.startswith("V005")]
        assert len(v005_errors) == 1
        assert "invalid-cloud" in v005_errors[0]


# ============================================================================
# Test Validation Rules - CP Dependencies (V006)
# ============================================================================


class TestValidationV006_CPDependencies:
    """Tests cho V006: CP dependency ordering."""

    def test_v006_dependencies_satisfied(
        self, valid_blueprint: CompiledBlueprint
    ) -> None:
        """Kiểm tra V006 pass khi dependencies được satisfy."""
        errors = valid_blueprint.validate()
        v006_errors = [e for e in errors if e.startswith("V006")]
        assert len(v006_errors) == 0


# ============================================================================
# Test Validation Rules - Brief Reference (V008)
# ============================================================================


class TestValidationV008_BriefReference:
    """Tests cho V008: Brief reference required."""

    def test_v008_brief_path_present(
        self, valid_blueprint: CompiledBlueprint
    ) -> None:
        """Kiểm tra V008 pass khi brief_path có mặt."""
        errors = valid_blueprint.validate()
        v008_errors = [e for e in errors if e.startswith("V008")]
        assert len(v008_errors) == 0

    def test_v008_brief_path_missing(
        self, compiler: BlueprintCompiler, sample_blueprint_data: dict[str, Any]
    ) -> None:
        """Kiểm tra V008 warning khi brief_path không có."""
        sample_blueprint_data["references"]["brief_path"] = None
        blueprint = compiler._parse_blueprint(sample_blueprint_data)
        
        errors = blueprint.validate()
        v008_errors = [e for e in errors if e.startswith("V008")]
        assert len(v008_errors) == 1


# ============================================================================
# Test Dependency Resolution
# ============================================================================


class TestDependencyResolution:
    """Tests cho dependency resolution."""

    def test_resolve_cp_dependencies(
        self, compiler: BlueprintCompiler
    ) -> None:
        """Kiểm tra CP dependency resolution."""
        resolved = compiler.resolve_cp_dependencies(["CP03"])
        assert "CP01" in resolved
        assert "CP02" in resolved
        assert "CP03" in resolved

    def test_resolve_dp_dependencies(
        self, compiler: BlueprintCompiler
    ) -> None:
        """Kiểm tra DP dependency resolution."""
        resolved = compiler.resolve_dp_dependencies("ecommerce-d2c")
        assert "DP01" in resolved
        assert "DP12" in resolved

    def test_resolve_rx_dependencies(
        self, compiler: BlueprintCompiler
    ) -> None:
        """Kiểm tra RX dependency resolution."""
        resolved = compiler.resolve_rx_dependencies("ecommerce-d2c")
        assert "RX01" in resolved
        assert "RX11" in resolved
        assert "RX06" in resolved
        assert "RX10" in resolved

    def test_find_missing_cp_dependencies(
        self, compiler: BlueprintCompiler
    ) -> None:
        """Kiểm tra find missing CP dependencies."""
        missing = compiler.find_missing_cp_dependencies({"CP03"})
        assert missing == {"CP01", "CP02"}

    def test_validate_cp_dependency_order(
        self, compiler: BlueprintCompiler
    ) -> None:
        """Kiểm tra CP dependency order validation."""
        errors = compiler.validate_cp_dependency_order(["CP01", "CP02", "CP03"])
        assert errors == []


# ============================================================================
# Test Universal RX Validation
# ============================================================================


class TestUniversalRXValidation:
    """Tests cho universal RX validation."""

    def test_validate_universal_rxs_pass(
        self, compiler: BlueprintCompiler
    ) -> None:
        """Kiểm tra universal RX validation pass."""
        errors = compiler.validate_universal_rxs({"RX01", "RX11", "RX06"})
        assert errors == []

    def test_validate_universal_rxs_fail(
        self, compiler: BlueprintCompiler
    ) -> None:
        """Kiểm tra universal RX validation fail."""
        errors = compiler.validate_universal_rxs({"RX06", "RX10"})
        assert len(errors) == 2
        assert any("RX01" in e for e in errors)
        assert any("RX11" in e for e in errors)

    def test_get_universal_rx_ids(
        self, compiler: BlueprintCompiler
    ) -> None:
        """Kiểm tra get universal RX IDs."""
        universal = compiler.get_universal_rx_ids()
        assert universal == {"RX01", "RX11"}


# ============================================================================
# Test Blueprint Info Methods
# ============================================================================


class TestBlueprintInfoMethods:
    """Tests cho blueprint info methods."""

    def test_get_dp_info(self, compiler: BlueprintCompiler) -> None:
        """Kiểm tra get DP info."""
        info = compiler.get_dp_info("DP01")
        assert info is not None
        assert info["name"] == "Commerce Core"
        assert info["category"] == "commerce"

    def test_get_rx_info(self, compiler: BlueprintCompiler) -> None:
        """Kiểm tra get RX info."""
        info = compiler.get_rx_info("RX01")
        assert info is not None
        assert info["name"] == "Privacy & PII Protection"
        assert "pii_encryption_required" in info["obligations"]

    def test_validate_dp_id(self, compiler: BlueprintCompiler) -> None:
        """Kiểm tra validate DP ID."""
        errors = compiler.validate_dp_id("DP01")
        assert errors == []
        
        errors = compiler.validate_dp_id("DP99")
        assert len(errors) == 1

    def test_validate_rx_id(self, compiler: BlueprintCompiler) -> None:
        """Kiểm tra validate RX ID."""
        errors = compiler.validate_rx_id("RX01")
        assert errors == []
        
        errors = compiler.validate_rx_id("RX99")
        assert len(errors) == 1


# ============================================================================
# Test Blueprint Compilation
# ============================================================================


class TestBlueprintCompilation:
    """Tests cho blueprint compilation."""

    def test_compile_blueprint_file(
        self, compiler: BlueprintCompiler, temp_blueprint_file: Path
    ) -> None:
        """Kiểm tra compile blueprint file."""
        blueprint = compiler.compile(temp_blueprint_file)
        
        assert blueprint is not None
        assert blueprint.industry.id == "ecommerce-d2c"
        assert blueprint.is_valid()

    def test_compile_nonexistent_file(
        self, compiler: BlueprintCompiler
    ) -> None:
        """Kiểm tra compile file không tồn tại."""
        with pytest.raises(FileNotFoundError):
            compiler.compile("nonexistent.yml")

    def test_compile_directory(
        self, compiler: BlueprintCompiler, temp_blueprint_file: Path
    ) -> None:
        """Kiểm tra compile directory."""
        blueprints = compiler.compile_directory(temp_blueprint_file.parent)
        assert len(blueprints) == 1


# ============================================================================
# Test Blueprint Helpers
# ============================================================================


class TestBlueprintHelpers:
    """Tests cho blueprint helper methods."""

    def test_get_all_core_packs(
        self, valid_blueprint: CompiledBlueprint
    ) -> None:
        """Kiểm tra get all core packs."""
        all_cp = valid_blueprint.core_packs.all_included
        assert len(all_cp) == 8  # 5 mandatory + 3 included
        assert "CP01" in all_cp
        assert "CP05" in all_cp

    def test_get_all_domain_packs(
        self, valid_blueprint: CompiledBlueprint
    ) -> None:
        """Kiểm tra get all domain packs."""
        all_dp = [dp.id for dp in valid_blueprint.domain_packs]
        assert "DP01" in all_dp
        assert "DP12" in all_dp

    def test_get_all_regulatory_overlays(
        self, valid_blueprint: CompiledBlueprint
    ) -> None:
        """Kiểm tra get all regulatory overlays."""
        all_rx = [ro.id for ro in valid_blueprint.regulatory_overlays]
        assert "RX01" in all_rx
        assert "RX11" in all_rx


# ============================================================================
# Test Blueprint Serialization
# ============================================================================


class TestBlueprintSerialization:
    """Tests cho blueprint serialization."""

    def test_blueprint_to_dict(
        self, valid_blueprint: CompiledBlueprint
    ) -> None:
        """Kiểm tra blueprint to_dict."""
        data = valid_blueprint.to_dict()
        
        assert data["type"] == "compiled_blueprint"
        assert "metadata" in data
        assert "industry" in data
        assert "core_packs" in data
        assert "validation" in data

    def test_blueprint_from_dict(
        self, sample_blueprint_data: dict[str, Any]
    ) -> None:
        """Kiểm tra blueprint from_dict."""
        blueprint = CompiledBlueprint.from_dict(sample_blueprint_data)
        
        assert blueprint.industry.id == "ecommerce-d2c"
        assert len(blueprint.core_packs.mandatory) == 5


# ============================================================================
# Test Complex Validation Scenarios
# ============================================================================


class TestComplexValidationScenarios:
    """Tests cho complex validation scenarios."""

    def test_complete_valid_blueprint(
        self, valid_blueprint: CompiledBlueprint
    ) -> None:
        """Kiểm tra complete valid blueprint."""
        errors = valid_blueprint.validate()
        # Chỉ có V008 warning cho brief_path
        critical_errors = [e for e in errors if e.startswith(("V001", "V002", "V009"))]
        assert len(critical_errors) == 0

    def test_blueprint_with_high_regulatory_risk(
        self, compiler: BlueprintCompiler, sample_blueprint_data: dict[str, Any]
    ) -> None:
        """Kiểm tra blueprint với high regulatory risk cần nhiều invariants."""
        sample_blueprint_data["industry"]["regulatory_risk"] = "high"
        # Only 2 invariants (should be >= 10)
        blueprint = compiler._parse_blueprint(sample_blueprint_data)
        
        errors = blueprint.validate()
        v009_errors = [e for e in errors if e.startswith("V009")]
        assert len(v009_errors) == 1
        assert "tối thiểu 10 invariants" in v009_errors[0]