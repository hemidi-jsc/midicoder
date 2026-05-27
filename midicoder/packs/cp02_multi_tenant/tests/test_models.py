# coding: utf-8
"""
Unit tests cho CP02 models — Multi-Tenant Architecture Generator.

Coverage:
- TenantIsolationStrategy enum
- TenantMode enum + isolation_strategy mapping
- TenantConfig validation + roundtrip
- TenantContext validation + roundtrip
- TenantResolver logic (header, JWT, subdomain, cache)
- SchemaIsolationConfig roundtrip
- TenantProvisioningConfig roundtrip
- CrossTenantAccessRule roundtrip
- TenantFilter factory methods
"""

from __future__ import annotations

import pytest

from midicoder.packs.cp02_multi_tenant.models import (
    TenantMode,
    TenantConfig,
    TenantContext,
    TenantResolver,
    TenantIsolationStrategy,
    TenantFilter,
    SchemaIsolationMode,
    SchemaIsolationConfig,
    ProvisioningStrategy,
    TenantStatus,
    TenantProvisioningConfig,
    CrossTenantAccessRule,
)


# ===========================================================================
# TenantIsolationStrategy Tests
# ===========================================================================

class TestTenantIsolationStrategy:
    """Test TenantIsolationStrategy enum values."""

    def test_row_value(self):
        assert TenantIsolationStrategy.ROW.value == "row"

    def test_schema_value(self):
        assert TenantIsolationStrategy.SCHEMA.value == "schema"

    def test_database_value(self):
        assert TenantIsolationStrategy.DATABASE.value == "database"

    def test_hybrid_value(self):
        assert TenantIsolationStrategy.HYBRID.value == "hybrid"

    def test_from_string(self):
        assert TenantIsolationStrategy("row") == TenantIsolationStrategy.ROW
        assert TenantIsolationStrategy("database") == TenantIsolationStrategy.DATABASE


# ===========================================================================
# TenantMode Tests (legacy + mapping)
# ===========================================================================

class TestTenantMode:
    """Test TenantMode enum + isolation_strategy mapping."""

    def test_schema_mode(self):
        assert TenantMode.SCHEMA.value == "schema"

    def test_row_mode(self):
        assert TenantMode.ROW.value == "row"

    def test_subdomain_mode(self):
        assert TenantMode.SUBDOMAIN.value == "subdomain"

    def test_mode_from_string(self):
        assert TenantMode("schema") == TenantMode.SCHEMA
        assert TenantMode("row") == TenantMode.ROW
        assert TenantMode("subdomain") == TenantMode.SUBDOMAIN

    def test_mode_from_invalid_string_raises(self):
        with pytest.raises(ValueError):
            TenantMode("invalid_mode")

    def test_schema_maps_to_schema_strategy(self):
        assert TenantMode.SCHEMA.isolation_strategy == TenantIsolationStrategy.SCHEMA

    def test_row_maps_to_row_strategy(self):
        assert TenantMode.ROW.isolation_strategy == TenantIsolationStrategy.ROW

    def test_subdomain_maps_to_row_strategy(self):
        # SUBDOMAIN = discovery method → ROW isolation
        assert TenantMode.SUBDOMAIN.isolation_strategy == TenantIsolationStrategy.ROW


# ===========================================================================
# TenantConfig Tests
# ===========================================================================

class TestTenantConfig:
    """Test TenantConfig dataclass validation."""

    def test_valid_row_config(self):
        config = TenantConfig(mode=TenantMode.ROW, tenant_id_column="tenant_id")
        assert config.mode == TenantMode.ROW
        assert config.tenant_id_column == "tenant_id"

    def test_valid_schema_config(self):
        config = TenantConfig(mode=TenantMode.SCHEMA, schema_prefix="t_")
        assert config.mode == TenantMode.SCHEMA
        assert config.schema_prefix == "t_"

    def test_valid_subdomain_config(self):
        config = TenantConfig(mode=TenantMode.SUBDOMAIN, domain="app.example.com")
        assert config.mode == TenantMode.SUBDOMAIN
        assert config.domain == "app.example.com"

    def test_empty_tenant_id_column_raises(self):
        with pytest.raises(Exception) as exc_info:
            TenantConfig(mode=TenantMode.ROW, tenant_id_column="")
        assert "MDC-CP02-005" in str(exc_info.value)

    def test_subdomain_empty_domain_raises(self):
        with pytest.raises(Exception) as exc_info:
            TenantConfig(mode=TenantMode.SUBDOMAIN, domain="")
        assert "MDC-CP02-001" in str(exc_info.value)

    def test_negative_cache_ttl_clamped_to_zero(self):
        config = TenantConfig(mode=TenantMode.ROW, cache_ttl=-10)
        assert config.cache_ttl == 0

    def test_to_dict(self):
        config = TenantConfig(
            mode=TenantMode.ROW,
            tenant_id_column="org_id",
            default_tenant_id="system",
            cache_ttl=600,
        )
        d = config.to_dict()
        assert d["mode"] == "row"
        assert d["tenant_id_column"] == "org_id"
        assert d["default_tenant_id"] == "system"
        assert d["cache_ttl"] == 600

    def test_from_dict_roundtrip(self):
        original = TenantConfig(
            mode=TenantMode.SCHEMA,
            tenant_id_column="t_id",
            default_tenant_id="main",
            schema_prefix="t_",
            domain="",
            cache_ttl=120,
        )
        restored = TenantConfig.from_dict(original.to_dict())
        assert restored.mode == original.mode
        assert restored.tenant_id_column == original.tenant_id_column
        assert restored.default_tenant_id == original.default_tenant_id
        assert restored.schema_prefix == original.schema_prefix
        assert restored.cache_ttl == original.cache_ttl


# ===========================================================================
# TenantContext Tests
# ===========================================================================

class TestTenantContext:
    """Test TenantContext validation."""

    def test_valid_context(self):
        ctx = TenantContext(tenant_id="t-123", user_id="u-456", mode=TenantMode.ROW)
        assert ctx.tenant_id == "t-123"
        assert ctx.user_id == "u-456"

    def test_empty_tenant_id_raises(self):
        with pytest.raises(Exception) as exc_info:
            TenantContext(tenant_id="", mode=TenantMode.ROW)
        assert "MDC-CP02-002" in str(exc_info.value)

    def test_none_tenant_id_raises(self):
        with pytest.raises(Exception) as exc_info:
            TenantContext(tenant_id=None, mode=TenantMode.ROW)
        assert "MDC-CP02-002" in str(exc_info.value)

    def test_to_dict(self):
        ctx = TenantContext(
            tenant_id="t-1",
            user_id="u-2",
            mode=TenantMode.SCHEMA,
            headers={"X-Custom": "v"},
        )
        d = ctx.to_dict()
        assert d["tenant_id"] == "t-1"
        assert d["mode"] == "schema"
        assert d["headers"]["X-Custom"] == "v"


# ===========================================================================
# TenantResolver Tests
# ===========================================================================

class TestTenantResolver:
    """Test TenantResolver logic."""

    def test_resolve_from_header(self):
        r = TenantResolver()
        assert r.resolve(headers={"X-Tenant-ID": "h1"}) == "h1"

    def test_resolve_from_jwt(self):
        r = TenantResolver()
        assert r.resolve(jwt_claims={"tenant_id": "j1"}) == "j1"

    def test_resolve_header_over_jwt(self):
        r = TenantResolver()
        result = r.resolve(
            headers={"X-Tenant-ID": "h1"},
            jwt_claims={"tenant_id": "j1"},
        )
        assert result == "h1"

    def test_resolve_from_subdomain(self):
        r = TenantResolver(domain="app.example.com")
        assert r.resolve(host="sub.app.example.com") == "sub"

    def test_resolve_raises_no_source(self):
        r = TenantResolver()
        with pytest.raises(Exception) as exc_info:
            r.resolve(headers={}, jwt_claims={}, host="example.com")
        assert "MDC-CP02-002" in str(exc_info.value)

    def test_cache_hit(self):
        r = TenantResolver()
        r.resolve(headers={"X-Tenant-ID": "t1"}, host="app.example.com")
        result = r.resolve(headers={"X-Tenant-ID": "t1"}, host="app.example.com")
        assert result == "t1"

    def test_clear_cache(self):
        r = TenantResolver()
        r.resolve(headers={"X-Tenant-ID": "t1"})
        assert len(r._cache) == 1
        r.clear_cache()
        assert len(r._cache) == 0

    def test_subdomain_no_match(self):
        r = TenantResolver(domain="app.example.com")
        assert r._extract_subdomain("other.example.com") == ""

    def test_subdomain_empty_host(self):
        r = TenantResolver(domain="app.example.com")
        assert r._extract_subdomain("") == ""

    def test_subdomain_exact_domain(self):
        r = TenantResolver(domain="app.example.com")
        assert r._extract_subdomain("app.example.com") == ""

    def test_subdomain_with_port(self):
        r = TenantResolver(domain="app.example.com")
        assert r._extract_subdomain("sub.app.example.com:8080") == "sub"


# ===========================================================================
# SchemaIsolationConfig Tests
# ===========================================================================

class TestSchemaIsolationConfig:
    """Test SchemaIsolationConfig roundtrip."""

    def test_defaults(self):
        c = SchemaIsolationConfig()
        assert c.isolation_mode == SchemaIsolationMode.DEDICATED_SCHEMA
        assert c.schema_prefix == "t_"
        assert c.create_on_first_access is True

    def test_custom(self):
        c = SchemaIsolationConfig(
            isolation_mode=SchemaIsolationMode.DEDICATED_DATABASE,
            schema_prefix="db_",
            enable_row_level_security=True,
        )
        assert c.isolation_mode == SchemaIsolationMode.DEDICATED_DATABASE
        assert c.enable_row_level_security is True

    def test_empty_prefix_defaults(self):
        c = SchemaIsolationConfig(schema_prefix="")
        assert c.schema_prefix == "t_"

    def test_negative_max_tenants_defaults(self):
        c = SchemaIsolationConfig(max_tenants_per_db=-1)
        assert c.max_tenants_per_db == 1000

    def test_roundtrip(self):
        original = SchemaIsolationConfig(
            isolation_mode=SchemaIsolationMode.SHARED_SCHEMA,
            schema_prefix="s_",
            migration_strategy="flyway",
            max_tenants_per_db=500,
        )
        restored = SchemaIsolationConfig.from_dict(original.to_dict())
        assert restored.isolation_mode == original.isolation_mode
        assert restored.schema_prefix == original.schema_prefix
        assert restored.migration_strategy == original.migration_strategy
        assert restored.max_tenants_per_db == original.max_tenants_per_db


# ===========================================================================
# TenantProvisioningConfig Tests
# ===========================================================================

class TestTenantProvisioningConfig:
    """Test TenantProvisioningConfig."""

    def test_defaults(self):
        c = TenantProvisioningConfig()
        assert c.strategy == ProvisioningStrategy.AUTOMATIC
        assert c.default_plan == "starter"
        assert c.auto_activate is True

    def test_roundtrip(self):
        original = TenantProvisioningConfig(
            strategy=ProvisioningStrategy.MANUAL_REVIEW,
            default_plan="pro",
            notification_email="admin@example.com",
        )
        restored = TenantProvisioningConfig.from_dict(original.to_dict())
        assert restored.strategy == original.strategy
        assert restored.default_plan == original.default_plan
        assert restored.notification_email == original.notification_email

    def test_empty_features_defaults(self):
        c = TenantProvisioningConfig(default_features=[])
        assert c.default_features == ["basic_api", "dashboard"]


# ===========================================================================
# CrossTenantAccessRule Tests
# ===========================================================================

class TestCrossTenantAccessRule:
    """Test CrossTenantAccessRule."""

    def test_defaults(self):
        r = CrossTenantAccessRule(source_tenant="a", target_tenant="b")
        assert r.read_only is True
        assert r.requires_approval is True

    def test_roundtrip(self):
        original = CrossTenantAccessRule(
            source_tenant="src",
            target_tenant="tgt",
            allowed_entities=["orders", "users"],
            read_only=False,
            expires_at="2026-12-31",
        )
        restored = CrossTenantAccessRule.from_dict(original.to_dict())
        assert restored.source_tenant == original.source_tenant
        assert restored.target_tenant == original.target_tenant
        assert restored.allowed_entities == original.allowed_entities
        assert restored.read_only is False
        assert restored.expires_at == "2026-12-31"


# ===========================================================================
# ProvisioningStrategy + TenantStatus
# ===========================================================================

class TestEnums:
    """Test ProvisioningStrategy and TenantStatus enums."""

    def test_provisioning_strategies(self):
        assert ProvisioningStrategy.AUTOMATIC.value == "automatic"
        assert ProvisioningStrategy.MANUAL_REVIEW.value == "manual_review"
        assert ProvisioningStrategy.API_DRIVEN.value == "api_driven"
        assert ProvisioningStrategy.TERRAFORM.value == "terraform"

    def test_tenant_statuses(self):
        assert TenantStatus.PROVISIONING.value == "provisioning"
        assert TenantStatus.ACTIVE.value == "active"
        assert TenantStatus.SUSPENDED.value == "suspended"
        assert TenantStatus.DELETED.value == "deleted"

    def test_schema_isolation_modes(self):
        assert SchemaIsolationMode.DEDICATED_SCHEMA.value == "dedicated_schema"
        assert SchemaIsolationMode.DEDICATED_DATABASE.value == "dedicated_database"
        assert SchemaIsolationMode.SHARED_SCHEMA.value == "shared_schema"


# ===========================================================================
# TenantFilter Tests
# ===========================================================================

class TestTenantFilter:
    """Test TenantFilter factory methods."""

    def test_create_row_filter(self):
        f = TenantFilter.create_row_filter(tenant_id="t1", tenant_column="tid")
        assert f.tenant_id == "t1"
        assert f.tenant_column == "tid"
        assert f.filter_type == "row"

    def test_create_schema_filter(self):
        f = TenantFilter.create_schema_filter(tenant_id="t1", schema_name="s1")
        assert f.tenant_id == "t1"
        assert f.tenant_column == "s1"
        assert f.filter_type == "schema"

    def test_to_dict(self):
        f = TenantFilter(tenant_id="t1", tenant_column="tc", filter_type="row")
        d = f.to_dict()
        assert d["tenant_id"] == "t1"
        assert d["tenant_column"] == "tc"
        assert d["filter_type"] == "row"
