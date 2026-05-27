# coding: utf-8
"""
Unit tests cho CP02 recipes — pattern macro verification.

Coverage:
- row_level_tenant_recipe
- schema_level_tenant_recipe
- database_level_tenant_recipe
- auto_provisioning_recipe
- manual_review_provisioning_recipe
- subdomain_tenant_recipe
- cross_tenant_access_recipe
"""

from __future__ import annotations

import pytest

from midicoder.packs.cp02_multi_tenant.models import (
    TenantMode,
    TenantIsolationStrategy,
    SchemaIsolationMode,
    ProvisioningStrategy,
)
from midicoder.packs.cp02_multi_tenant.recipes import (
    row_level_tenant_recipe,
    schema_level_tenant_recipe,
    database_level_tenant_recipe,
    auto_provisioning_recipe,
    manual_review_provisioning_recipe,
    subdomain_tenant_recipe,
    cross_tenant_access_recipe,
)


# ===========================================================================
# Row-Level Recipe Tests
# ===========================================================================

class TestRowLevelTenantRecipe:
    """Test row_level_tenant_recipe."""

    def test_default_values(self):
        config = row_level_tenant_recipe()
        assert config.mode == TenantMode.ROW
        assert config.tenant_id_column == "tenant_id"
        assert config.cache_ttl == 300

    def test_custom_column(self):
        config = row_level_tenant_recipe(tenant_id_column="org_id")
        assert config.tenant_id_column == "org_id"

    def test_maps_to_row_strategy(self):
        config = row_level_tenant_recipe()
        assert config.mode.isolation_strategy == TenantIsolationStrategy.ROW


# ===========================================================================
# Schema-Level Recipe Tests
# ===========================================================================

class TestSchemaLevelTenantRecipe:
    """Test schema_level_tenant_recipe."""

    def test_returns_tuple(self):
        config, isolation = schema_level_tenant_recipe()
        assert config is not None
        assert isolation is not None

    def test_config_is_schema_mode(self):
        config, _ = schema_level_tenant_recipe()
        assert config.mode == TenantMode.SCHEMA

    def test_isolation_is_dedicated_schema(self):
        _, isolation = schema_level_tenant_recipe()
        assert isolation.isolation_mode == SchemaIsolationMode.DEDICATED_SCHEMA

    def test_custom_prefix(self):
        config, isolation = schema_level_tenant_recipe(schema_prefix="cust_")
        assert config.schema_prefix == "cust_"
        assert isolation.schema_prefix == "cust_"

    def test_rls_enabled(self):
        _, isolation = schema_level_tenant_recipe(enable_rls=True)
        assert isolation.enable_row_level_security is True

    def test_rls_disabled_by_default(self):
        _, isolation = schema_level_tenant_recipe()
        assert isolation.enable_row_level_security is False


# ===========================================================================
# Database-Level Recipe Tests
# ===========================================================================

class TestDatabaseLevelTenantRecipe:
    """Test database_level_tenant_recipe."""

    def test_returns_tuple(self):
        config, isolation = database_level_tenant_recipe()
        assert config is not None
        assert isolation is not None

    def test_isolation_is_dedicated_database(self):
        _, isolation = database_level_tenant_recipe()
        assert isolation.isolation_mode == SchemaIsolationMode.DEDICATED_DATABASE

    def test_custom_max_tenants(self):
        _, isolation = database_level_tenant_recipe(max_tenants_per_db=50)
        assert isolation.max_tenants_per_db == 50

    def test_default_max_tenants(self):
        _, isolation = database_level_tenant_recipe()
        assert isolation.max_tenants_per_db == 100


# ===========================================================================
# Auto-Provisioning Recipe Tests
# ===========================================================================

class TestAutoProvisioningRecipe:
    """Test auto_provisioning_recipe."""

    def test_default_strategy(self):
        config = auto_provisioning_recipe()
        assert config.strategy == ProvisioningStrategy.AUTOMATIC

    def test_default_plan(self):
        config = auto_provisioning_recipe()
        assert config.default_plan == "starter"

    def test_custom_plan(self):
        config = auto_provisioning_recipe(default_plan="enterprise")
        assert config.default_plan == "enterprise"

    def test_resource_limits(self):
        config = auto_provisioning_recipe(storage_gb=100, max_users=500)
        assert config.resource_limits["storage_gb"] == 100
        assert config.resource_limits["max_users"] == 500

    def test_auto_activate_true(self):
        config = auto_provisioning_recipe()
        assert config.auto_activate is True


# ===========================================================================
# Manual Review Recipe Tests
# ===========================================================================

class TestManualReviewProvisioningRecipe:
    """Test manual_review_provisioning_recipe."""

    def test_manual_review_strategy(self):
        config = manual_review_provisioning_recipe()
        assert config.strategy == ProvisioningStrategy.MANUAL_REVIEW

    def test_auto_activate_false(self):
        config = manual_review_provisioning_recipe()
        assert config.auto_activate is False

    def test_notification_email(self):
        config = manual_review_provisioning_recipe(
            notification_email="admin@test.com"
        )
        assert config.notification_email == "admin@test.com"


# ===========================================================================
# Subdomain Recipe Tests
# ===========================================================================

class TestSubdomainTenantRecipe:
    """Test subdomain_tenant_recipe."""

    def test_subdomain_mode(self):
        config = subdomain_tenant_recipe(domain="app.example.com")
        assert config.mode == TenantMode.SUBDOMAIN

    def test_domain_set(self):
        config = subdomain_tenant_recipe(domain="app.example.com")
        assert config.domain == "app.example.com"

    def test_higher_cache_ttl(self):
        config = subdomain_tenant_recipe(domain="app.example.com")
        assert config.cache_ttl == 600


# ===========================================================================
# Cross-Tenant Access Recipe Tests
# ===========================================================================

class TestCrossTenantAccessRecipe:
    """Test cross_tenant_access_recipe."""

    def test_basic_rule(self):
        rule = cross_tenant_access_recipe("src", "tgt")
        assert rule.source_tenant == "src"
        assert rule.target_tenant == "tgt"

    def test_custom_entities(self):
        rule = cross_tenant_access_recipe(
            "a", "b", entities=["orders", "users", "products"]
        )
        assert rule.allowed_entities == ["orders", "users", "products"]

    def test_expiry(self):
        rule = cross_tenant_access_recipe(
            "a", "b", expires_at="2026-12-31T23:59:59Z"
        )
        assert rule.expires_at == "2026-12-31T23:59:59Z"

    def test_read_only_by_default(self):
        rule = cross_tenant_access_recipe("a", "b")
        assert rule.read_only is True

    def test_requires_approval_by_default(self):
        rule = cross_tenant_access_recipe("a", "b")
        assert rule.requires_approval is True
