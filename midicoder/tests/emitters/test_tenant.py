# coding: utf-8
"""
Unit tests cho CP02 Multi-Tenant Architecture Generator.

Test coverage:
- TenantMode enum validation
- TenantConfig validation (__post_init__)
- TenantContext validation (__post_init__)
- TenantResolver logic
- FastAPITenantEmitter output
- NestJSTenantEmitter output
- AngularTenantEmitter output
- ReactTenantEmitter output

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import pytest
from pathlib import Path

# Import models CP02
from midicoder.emitters.core.tenant.models import (
    TenantMode,
    TenantConfig,
    TenantContext,
    TenantResolver,
)
from midicoder.emitters.core.tenant.fastapi import FastAPITenantEmitter
from midicoder.emitters.core.tenant.nestjs import NestJSTenantEmitter
from midicoder.emitters.core.tenant.angular import AngularTenantEmitter
from midicoder.emitters.core.tenant.react import ReactTenantEmitter

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# TenantMode Tests
# ===========================================================================

class TestTenantMode:
    """Test TenantMode enum values."""

    def test_schema_mode_exists(self):
        """Kiem tra TenantMode.SCHEMA ton tai."""
        assert TenantMode.SCHEMA.value == "schema"

    def test_row_mode_exists(self):
        """Kiem tra TenantMode.ROW ton tai."""
        assert TenantMode.ROW.value == "row"

    def test_subdomain_mode_exists(self):
        """Kiem tra TenantMode.SUBDOMAIN ton tai."""
        assert TenantMode.SUBDOMAIN.value == "subdomain"

    def test_mode_from_valid_string(self):
        """Kiem tra khoi tao TenantMode tu string hop le."""
        assert TenantMode("schema") == TenantMode.SCHEMA
        assert TenantMode("row") == TenantMode.ROW
        assert TenantMode("subdomain") == TenantMode.SUBDOMAIN

    def test_mode_from_invalid_string_raises(self):
        """Kiem tra khoi tao TenantMode tu string khong hop le throw error."""
        with pytest.raises(ValueError):
            TenantMode("invalid_mode")


# ===========================================================================
# TenantConfig Tests
# ===========================================================================

class TestTenantConfig:
    """Test TenantConfig dataclass validation."""

    def test_valid_config_row_mode(self):
        """Kiem tra TenantConfig hop le voi row mode."""
        config = TenantConfig(
            mode=TenantMode.ROW,
            tenant_id_column="tenant_id",
            default_tenant_id="default",
        )
        assert config.mode == TenantMode.ROW
        assert config.tenant_id_column == "tenant_id"

    def test_valid_config_schema_mode(self):
        """Kiem tra TenantConfig hop le voi schema mode."""
        config = TenantConfig(
            mode=TenantMode.SCHEMA,
            schema_prefix="tenant_",
        )
        assert config.mode == TenantMode.SCHEMA
        assert config.schema_prefix == "tenant_"

    def test_valid_config_subdomain_mode(self):
        """Kiem tra TenantConfig hop le voi subdomain mode."""
        config = TenantConfig(
            mode=TenantMode.SUBDOMAIN,
            domain="app.example.com",
        )
        assert config.mode == TenantMode.SUBDOMAIN
        assert config.domain == "app.example.com"

    def test_empty_tenant_id_column_raises(self):
        """Kiem tra tenant_id_column rong throw MDC-CP02-005."""
        with pytest.raises(Exception) as exc_info:
            TenantConfig(
                mode=TenantMode.ROW,
                tenant_id_column="",
            )
        assert "MDC-CP02-005" in str(exc_info.value)

    def test_to_dict_roundtrip(self):
        """Kiem tra to_dict + from_dict roundtrip."""
        original = TenantConfig(
            mode=TenantMode.ROW,
            tenant_id_column="org_id",
            default_tenant_id="system",
            cache_ttl=300,
        )
        data = original.to_dict()
        restored = TenantConfig.from_dict(data)
        assert restored.mode == original.mode
        assert restored.tenant_id_column == original.tenant_id_column
        assert restored.default_tenant_id == original.default_tenant_id
        assert restored.cache_ttl == original.cache_ttl

    def test_negative_cache_ttl_defaults_to_zero(self):
        """Kiem tra cache_ttl am duoc dat ve 0."""
        config = TenantConfig(
            mode=TenantMode.ROW,
            tenant_id_column="tenant_id",
            cache_ttl=-10,
        )
        assert config.cache_ttl == 0

    def test_subdomain_mode_with_empty_domain_raises(self):
        """Kiem tra SUBDOMAIN mode voi domain rong throw MDC-CP02-001."""
        with pytest.raises(Exception) as exc_info:
            TenantConfig(
                mode=TenantMode.SUBDOMAIN,
                domain="",
            )
        assert "MDC-CP02-001" in str(exc_info.value)


# ===========================================================================
# TenantContext Tests
# ===========================================================================

class TestTenantContext:
    """Test TenantContext dataclass validation."""

    def test_valid_context(self):
        """Kiem tra TenantContext hop le."""
        ctx = TenantContext(
            tenant_id="t-123",
            user_id="u-456",
            mode=TenantMode.ROW,
        )
        assert ctx.tenant_id == "t-123"
        assert ctx.user_id == "u-456"

    def test_empty_tenant_id_raises(self):
        """Kiem tra tenant_id rong throw MDC-CP02-002."""
        with pytest.raises(Exception) as exc_info:
            TenantContext(
                tenant_id="",
                mode=TenantMode.ROW,
            )
        assert "MDC-CP02-002" in str(exc_info.value)

    def test_missing_tenant_id_raises(self):
        """Kiem tra tenant_id None throw MDC-CP02-002."""
        with pytest.raises(Exception) as exc_info:
            TenantContext(
                tenant_id=None,
                mode=TenantMode.ROW,
            )
        assert "MDC-CP02-002" in str(exc_info.value)

    def test_to_dict(self):
        """Kiem tra to_dict tra ve dict dung."""
        ctx = TenantContext(
            tenant_id="t-123",
            user_id="u-456",
            mode=TenantMode.SCHEMA,
            headers={"X-Custom": "value"},
        )
        data = ctx.to_dict()
        assert data["tenant_id"] == "t-123"
        assert data["mode"] == "schema"
        assert data["headers"]["X-Custom"] == "value"


# ===========================================================================
# TenantResolver Tests
# ===========================================================================

class TestTenantResolver:
    """Test TenantResolver logic."""

    def test_resolve_from_header(self):
        """Kiem tra resolve tenant ID tu header."""
        resolver = TenantResolver()
        result = resolver.resolve(
            headers={"X-Tenant-ID": "t-from-header"},
            jwt_claims={},
            host="app.example.com",
        )
        assert result == "t-from-header"

    def test_resolve_from_jwt_claims(self):
        """Kiem tra resolve tenant ID tu JWT claims khi khong co header."""
        resolver = TenantResolver()
        result = resolver.resolve(
            headers={},
            jwt_claims={"tenant_id": "t-from-jwt"},
            host="app.example.com",
        )
        assert result == "t-from-jwt"

    def test_resolve_from_subdomain(self):
        """Kiem tra resolve tenant ID tu subdomain khi khong co header/JWT."""
        resolver = TenantResolver(domain="app.example.com")
        result = resolver.resolve(
            headers={},
            jwt_claims={},
            host="mysubdomain.app.example.com",
        )
        assert result == "mysubdomain"

    def test_resolve_raises_when_no_source(self):
        """Kiem tra throw error khi khong co ngon tenant ID nao."""
        resolver = TenantResolver()
        with pytest.raises(Exception) as exc_info:
            resolver.resolve(
                headers={},
                jwt_claims={},
                host="example.com",
            )
        assert "MDC-CP02-002" in str(exc_info.value)

    def test_cache_resolved_tenant(self):
        """Kiem tra cache hoat dong - lan 2 khong goi resolve lai."""
        resolver = TenantResolver()
        result_1 = resolver.resolve(
            headers={"X-Tenant-ID": "t-cache"},
            jwt_claims={},
            host="app.example.com",
        )
        assert result_1 == "t-cache"
        # Cache miss da xay ra, cache da duoc ghi

        # Lan 2: cache hit — branch 223->227 duoc cover
        result_2 = resolver.resolve(
            headers={"X-Tenant-ID": "t-cache"},
            jwt_claims={},
            host="app.example.com",
        )
        assert result_2 == "t-cache"
        # Ket qua cache phai giong — key trong cache la "t-cache:app.example.com"
        assert any("t-cache" in k or "t-cache" == v for k, v in resolver._cache.items())

    def test_clear_cache(self):
        """Kiem tra clear_cache xoa toan bo cache."""
        resolver = TenantResolver()
        resolver.resolve(
            headers={"X-Tenant-ID": "t-1"},
            jwt_claims={},
            host="app.example.com",
        )
        assert len(resolver._cache) == 1
        resolver.clear_cache()
        assert len(resolver._cache) == 0

    def test_extract_subdomain_no_match(self):
        """Kiem tra extract subdomain khi host khong khop domain."""
        resolver = TenantResolver(domain="app.example.com")
        result = resolver._extract_subdomain("other.example.com")
        assert result == ""

    def test_extract_subdomain_empty_host(self):
        """Kiem tra extract subdomain khi host rong."""
        resolver = TenantResolver(domain="app.example.com")
        result = resolver._extract_subdomain("")
        assert result == ""

    def test_extract_subdomain_exact_domain_match(self):
        """Kiem tra extract subdomain khi host = domain (khong co subdomain)."""
        resolver = TenantResolver(domain="app.example.com")
        result = resolver._extract_subdomain("app.example.com")
        assert result == ""


# ===========================================================================
# FastAPITenantEmitter Tests
# ===========================================================================

class TestFastAPITenantEmitter:
    """Test FastAPI tenant emitter output."""

    def test_emit_middleware_file(self):
        """Kiem tra emitter sinh middleware file."""
        emitter = FastAPITenantEmitter()
        config = TenantConfig(mode=TenantMode.ROW, tenant_id_column="tenant_id")
        files = emitter.emit(config)
        assert "app/core/security/tenant_middleware.py" in files
        assert "X-Tenant-ID" in files["app/core/security/tenant_middleware.py"]

    def test_emit_context_file(self):
        """Kiem tra emitter sinh context file."""
        emitter = FastAPITenantEmitter()
        config = TenantConfig(mode=TenantMode.ROW, tenant_id_column="tenant_id")
        files = emitter.emit(config)
        assert "app/core/security/tenant_context.py" in files

    def test_emit_with_schema_mode(self):
        """Kiem tra emitter voi schema mode sinh code khac."""
        emitter = FastAPITenantEmitter()
        config = TenantConfig(mode=TenantMode.SCHEMA, schema_prefix="tenant_")
        files = emitter.emit(config)
        content = files["app/core/security/tenant_middleware.py"]
        assert "schema" in content.lower() or "search_path" in content.lower()

    def test_emit_with_subdomain_mode(self):
        """Kiem tra emitter voi subdomain mode sinh code subdomain."""
        emitter = FastAPITenantEmitter()
        config = TenantConfig(mode=TenantMode.SUBDOMAIN, domain="app.example.com")
        files = emitter.emit(config)
        content = files["app/core/security/tenant_middleware.py"]
        assert "subdomain" in content.lower()


# ===========================================================================
# NestJSTenantEmitter Tests
# ===========================================================================

class TestNestJSTenantEmitter:
    """Test NestJS tenant emitter output."""

    def test_emit_module_file(self):
        """Kiem tra emitter sinh module file."""
        emitter = NestJSTenantEmitter()
        config = TenantConfig(mode=TenantMode.ROW, tenant_id_column="tenant_id")
        files = emitter.emit(config)
        assert any("tenant.module" in k for k in files.keys())

    def test_emit_middleware_file(self):
        """Kiem tra emitter sinh middleware file."""
        emitter = NestJSTenantEmitter()
        config = TenantConfig(mode=TenantMode.ROW, tenant_id_column="tenant_id")
        files = emitter.emit(config)
        assert any("tenant.middleware" in k for k in files.keys())


# ===========================================================================
# AngularTenantEmitter Tests
# ===========================================================================

class TestAngularTenantEmitter:
    """Test Angular tenant emitter output."""

    def test_emit_service_file(self):
        """Kiem tra emitter sinh service file."""
        emitter = AngularTenantEmitter()
        config = TenantConfig(mode=TenantMode.ROW, tenant_id_column="tenant_id")
        files = emitter.emit(config)
        assert any("tenant.service" in k for k in files.keys())

    def test_emit_guard_file(self):
        """Kiem tra emitter sinh guard file."""
        emitter = AngularTenantEmitter()
        config = TenantConfig(mode=TenantMode.ROW, tenant_id_column="tenant_id")
        files = emitter.emit(config)
        assert any("tenant.guard" in k for k in files.keys())


# ===========================================================================
# ReactTenantEmitter Tests
# ===========================================================================

class TestReactTenantEmitter:
    """Test React tenant emitter output."""

    def test_emit_context_file(self):
        """Kiem tra emitter sinh context file."""
        emitter = ReactTenantEmitter()
        config = TenantConfig(mode=TenantMode.ROW, tenant_id_column="tenant_id")
        files = emitter.emit(config)
        assert any("TenantContext" in k for k in files.keys())

    def test_emit_hook_file(self):
        """Kiem tra emitter sinh hook file."""
        emitter = ReactTenantEmitter()
        config = TenantConfig(mode=TenantMode.ROW, tenant_id_column="tenant_id")
        files = emitter.emit(config)
        assert any("useTenant" in k for k in files.keys())

    def test_emit_provider_file(self):
        """Kiem tra emitter sinh provider file."""
        emitter = ReactTenantEmitter()
        config = TenantConfig(mode=TenantMode.ROW, tenant_id_column="tenant_id")
        files = emitter.emit(config)
        assert any("TenantProvider" in k for k in files.keys())