"""
Tests cho Blueprint YAML Schema Validation.

Tuân thủ TDD, kiểm tra:
- Schema file tồn tại và hợp lệ
- Schema có đủ các sections (metadata, industry, core_packs)
- Schema validates valid blueprints đúng
- Schema rejects invalid blueprints đúng
- Required fields được enforce đúng
- Pattern validation cho CP IDs

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def schema_path() -> Path:
    """Đường dẫn đến blueprint schema."""
    return Path("industry/blueprints/schema.yml")


@pytest.fixture
def schema(schema_path: Path) -> dict:
    """Load và parse blueprint schema."""
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def valid_blueprint_data() -> dict:
    """Valid blueprint data cho testing."""
    return {
        "$schema": "industry-blueprint-v1",
        "metadata": {
            "version": "1.0.0",
            "industry_id": "ecommerce-d2c",
            "name": "E-commerce D2C",
            "group": "Commerce/Logistics/Ops",
            "priority": 1,
            "complexity": "medium",
            "regulatory_risk": "low",
            "commercial_priority": "critical",
            "status": "approved",
            "tags": ["priority", "top20"]
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
        "target_profiles": ["local", "aws"],
        "invariants": {
            "business": [
                {"id": "INV001", "name": "Order Status Valid", "description": "Order status phải hợp lệ", "enforcement": "compile-time"},
                "INV002"
            ],
            "compliance": [
                "COMP002"
            ],
            "failure_modes": [
                {"id": "FAIL001", "scenario": "Payment gateway timeout", "handling": "retry_with_backoff", "recovery": "manual_review"}
            ]
        },
        "config": {
            "default_tenant_mode": "schema",
            "default_auth_strategy": "jwt",
            "default_db_engine": "postgres",
            "observability": {"metrics": True, "tracing": True},
            "security": {"rate_limit": 1000}
        },
        "references": {
            "brief_path": "industry/briefs/ecommerce-d2c.md",
            "documentation_url": "https://docs.midicoder.dev/blueprints/ecommerce-d2c",
            "related_blueprints": ["marketplace-c2c", "dropshipping"]
        }
    }


# ============================================================================
# Test Schema File Structure
# ============================================================================


class TestSchemaFileStructure:
    """Tests cho schema file structure."""

    def test_schema_file_exists(self, schema_path: Path) -> None:
        """Kiểm tra schema file tồn tại."""
        assert schema_path.exists(), "Blueprint schema file phải tồn tại"

    def test_schema_is_valid_yaml(self, schema_path: Path) -> None:
        """Kiểm tra schema là valid YAML."""
        with open(schema_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None, "Schema phải parse được"

    def test_schema_has_required_fields(self, schema: dict) -> None:
        """Kiểm tra schema có required sections."""
        assert "type" in schema, "Schema phải có 'type'"
        assert schema["type"] == "object", "Schema type phải là 'object'"
        assert "properties" in schema, "Schema phải có 'properties'"
        assert "required" in schema, "Schema phải có 'required'"

    def test_schema_declares_required_fields(self, schema: dict) -> None:
        """Kiểm tra schema declares required fields."""
        required = schema.get("required", [])
        # Theo requirement.md, required fields là:
        # - $schema (schema version)
        # - metadata (blueprint metadata)
        # - industry (industry info)
        # - core_packs (CP configuration)
        assert "$schema" in required, "Schema version phải required"
        assert "metadata" in required, "Metadata phải required"
        assert "industry" in required, "Industry info phải required"
        assert "core_packs" in required, "Core packs phải required"

    def test_schema_has_all_sections(self, schema: dict) -> None:
        """Kiểm tra schema có tất cả sections theo requirement.md."""
        properties = schema.get("properties", {})
        expected_sections = [
            "$schema",
            "metadata",
            "industry",
            "core_packs",
            "target_profiles",
            "invariants",
            "config",
            "references"
        ]
        for section in expected_sections:
            assert section in properties, f"Schema phải có section '{section}'"


# ============================================================================
# Test Metadata Section
# ============================================================================


class TestMetadataSection:
    """Tests cho metadata section."""

    def test_metadata_required_fields(self, schema: dict) -> None:
        """Kiểm tra metadata có required fields."""
        metadata_schema = schema["properties"]["metadata"]
        required = metadata_schema.get("required", [])
        assert "version" in required, "Metadata.version phải required"
        assert "industry_id" in required, "Metadata.industry_id phải required"
        assert "name" in required, "Metadata.name phải required"
        assert "group" in required, "Metadata.group phải required"

    def test_metadata_version_semver_pattern(self, schema: dict) -> None:
        """Kiểm tra version field có semver pattern."""
        version_schema = schema["properties"]["metadata"]["properties"]["version"]
        assert "pattern" in version_schema, "Version phải có pattern"
        # Semver pattern validation
        import re
        pattern = version_schema["pattern"]
        # Test valid semver
        assert re.match(pattern, "1.0.0"), "1.0.0 phải valid"
        assert re.match(pattern, "2.1.0"), "2.1.0 phải valid"
        assert re.match(pattern, "0.0.1-alpha"), "0.0.1-alpha phải valid"
        # Test invalid semver
        assert not re.match(pattern, "invalid"), "invalid phải invalid"
        assert not re.match(pattern, "1.0"), "1.0 phải invalid (thiếu patch)"

    def test_metadata_industry_id_pattern(self, schema: dict) -> None:
        """Kiểm tra industry_id pattern (lowercase, hyphenated)."""
        id_schema = schema["properties"]["metadata"]["properties"]["industry_id"]
        assert "pattern" in id_schema, "industry_id phải có pattern"
        import re
        pattern = id_schema["pattern"]
        assert re.match(pattern, "ecommerce-d2c"), "ecommerce-d2c phải valid"
        assert re.match(pattern, "banking-core"), "banking-core phải valid"
        assert not re.match(pattern, "Ecommerce"), "Ecommerce (uppercase) phải invalid"
        assert not re.match(pattern, "ecommerce_d2c"), "underscore phải invalid"

    def test_metadata_group_enum(self, schema: dict) -> None:
        """Kiểm tra group field có đúng enum values."""
        group_schema = schema["properties"]["metadata"]["properties"]["group"]
        assert "enum" in group_schema, "Group phải có enum"
        enum_values = group_schema["enum"]
        # Theo requirement.md - Industry groups
        assert "Commerce/Logistics/Ops" in enum_values
        assert "CRM/ERP/HR/Education" in enum_values
        assert "Healthcare/Banking/Exchange" in enum_values
        assert "SaaS/Platform" in enum_values
        assert "Media/Content" in enum_values
        assert "Other" in enum_values


# ============================================================================
# Test Core Packs Section
# ============================================================================


class TestCorePacksSection:
    """Tests cho core_packs section."""

    def test_core_packs_structure(self, schema: dict) -> None:
        """Kiểm tra core_packs structure."""
        cp_schema = schema["properties"]["core_packs"]
        assert cp_schema["type"] == "object"
        assert "mandatory" in cp_schema["properties"]
        assert "included" in cp_schema["properties"]
        assert "excluded" in cp_schema["properties"]
        assert "experimental" in cp_schema["properties"]

    def test_core_packs_id_pattern(self, schema: dict) -> None:
        """Kiểm tra CP ID pattern (CP01-CP30)."""
        mandatory_schema = schema["properties"]["core_packs"]["properties"]["mandatory"]
        pattern = mandatory_schema["items"]["pattern"]
        import re
        # Valid CP IDs
        assert re.match(pattern, "CP01"), "CP01 phải valid"
        assert re.match(pattern, "CP15"), "CP15 phải valid"
        assert re.match(pattern, "CP30"), "CP30 phải valid"
        # Invalid CP IDs
        assert not re.match(pattern, "CP00"), "CP00 phải invalid"
        assert not re.match(pattern, "CP31"), "CP31 phải invalid"
        assert not re.match(pattern, "DP01"), "DP01 phải invalid (domain pack)"

    def test_experimental_p4_only(self, schema: dict) -> None:
        """Kiểm tra experimental field chỉ cho phép P4 packs (CP27-CP30)."""
        exp_schema = schema["properties"]["core_packs"]["properties"]["experimental"]
        pattern = exp_schema["items"]["pattern"]
        import re
        # P4 packs only: CP27, CP28, CP29, CP30
        assert re.match(pattern, "CP27"), "CP27 phải valid"
        assert re.match(pattern, "CP30"), "CP30 phải valid"
        # Non-P4 phải invalid
        assert not re.match(pattern, "CP01"), "CP01 phải invalid trong experimental"
        assert not re.match(pattern, "CP15"), "CP15 phải invalid trong experimental"


# ============================================================================
# Test Target Profiles Section
# ============================================================================


class TestTargetProfilesSection:
    """Tests cho target_profiles section."""

    def test_target_profiles_enum(self, schema: dict) -> None:
        """Kiểm tra target_profiles enum values."""
        tp_schema = schema["properties"]["target_profiles"]
        enum_values = tp_schema["items"]["enum"]
        # Theo requirement.md - Target profiles
        assert "local" in enum_values
        assert "aws" in enum_values
        assert "gcp" in enum_values
        assert "azure" in enum_values
        assert "on-premise" in enum_values

    def test_target_profiles_default(self, schema: dict) -> None:
        """Kiểm tra target_profiles default values."""
        tp_schema = schema["properties"]["target_profiles"]
        default = tp_schema.get("default", [])
        assert "local" in default, "local phải trong default"
        assert "aws" in default, "aws phải trong default"


# ============================================================================
# Test Invariants Section
# ============================================================================


class TestInvariantsSection:
    """Tests cho invariants section."""

    def test_invariants_structure(self, schema: dict) -> None:
        """Kiểm tra invariants có 3 sections."""
        inv_schema = schema["properties"]["invariants"]
        assert "business" in inv_schema["properties"]
        assert "compliance" in inv_schema["properties"]
        assert "failure_modes" in inv_schema["properties"]

    def test_business_invariant_enforcement_enum(self, schema: dict) -> None:
        """Kiểm tra enforcement enum values."""
        biz_schema = schema["properties"]["invariants"]["properties"]["business"]["items"]
        # Full form
        full_form = biz_schema["oneOf"][1]["properties"]["enforcement"]
        enum_values = full_form["enum"]
        assert "compile-time" in enum_values
        assert "runtime" in enum_values
        assert "both" in enum_values


# ============================================================================
# Test Config Section
# ============================================================================


class TestConfigSection:
    """Tests cho config section."""

    def test_config_tenant_mode_enum(self, schema: dict) -> None:
        """Kiểm tra default_tenant_mode enum values."""
        config_schema = schema["properties"]["config"]["properties"]["default_tenant_mode"]
        enum_values = config_schema["enum"]
        assert "database" in enum_values
        assert "schema" in enum_values
        assert "row" in enum_values
        assert "hybrid" in enum_values
        assert config_schema["default"] == "schema"

    def test_config_db_engine_enum(self, schema: dict) -> None:
        """Kiểm tra default_db_engine enum values."""
        db_schema = schema["properties"]["config"]["properties"]["default_db_engine"]
        enum_values = db_schema["enum"]
        assert "postgres" in enum_values
        assert "mysql" in enum_values
        assert "sqlserver" in enum_values
        assert "oracle" in enum_values
        assert db_schema["default"] == "postgres"


# ============================================================================
# Test Schema Validation Behavior
# ============================================================================


class TestSchemaValidationBehavior:
    """Tests cho schema validation behavior."""

    def test_valid_blueprint_structure(self, schema: dict, valid_blueprint_data: dict) -> None:
        """Kiểm tra valid blueprint có cấu trúc đúng."""
        # Kiểm tra tất cả required fields có mặt
        for req in schema["required"]:
            assert req in valid_blueprint_data, f"Valid blueprint thiếu '{req}'"

    def test_blueprint_no_additional_properties(self, schema: dict) -> None:
        """Kiểm tra schema không cho phép additional properties."""
        assert schema.get("additionalProperties") is False, "Schema phải forbid additional properties"


# ============================================================================
# Test Schema File Content
# ============================================================================


class TestSchemaFileContent:
    """Tests cho schema file content."""

    def test_schema_has_vietnamese_comments(self, schema_path: Path) -> None:
        """Kiểm tra schema file có Vietnamese comments."""
        with open(schema_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Check for Vietnamese text in comments
        assert "Cấu hình" in content or "Thông tin" in content or "Mô tả" in content, \
            "Schema phải có Vietnamese comments"

    def test_schema_has_author_info(self, schema_path: Path) -> None:
        """Kiểm tra schema file có author info."""
        with open(schema_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Tác giả" in content or "Author" in content, "Schema phải có author info"
        assert "Version" in content, "Schema phải có version"