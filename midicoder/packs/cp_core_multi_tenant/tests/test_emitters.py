# coding: utf-8
"""
Unit tests cho CP02 stack emitters — tất cả 4 stack (FastAPI, NestJS, Angular, React).
"""

from __future__ import annotations

import pytest

from midicoder.packs.cp_core_multi_tenant.models import TenantMode, TenantConfig
from midicoder.packs.cp_core_multi_tenant.fastapi import FastAPITenantEmitter
from midicoder.packs.cp_core_multi_tenant.nestjs import NestJSTenantEmitter
from midicoder.packs.cp_core_multi_tenant.angular import AngularTenantEmitter
from midicoder.packs.cp_core_multi_tenant.react import ReactTenantEmitter


# ===========================================================================
# FastAPITenantEmitter Tests
# ===========================================================================

class TestFastAPITenantEmitter:
    """Test FastAPI tenant emitter output."""

    def _config(self, mode=TenantMode.ROW) -> TenantConfig:
        if mode == TenantMode.SUBDOMAIN:
            return TenantConfig(mode=mode, domain="app.example.com")
        return TenantConfig(mode=mode, tenant_id_column="tenant_id")

    def test_emit_returns_three_files(self):
        emitter = FastAPITenantEmitter()
        files = emitter.emit(self._config())
        assert len(files) == 3

    def test_emit_has_context_file(self):
        emitter = FastAPITenantEmitter()
        files = emitter.emit(self._config())
        assert "app/core/security/tenant_context.py" in files

    def test_emit_has_middleware_file(self):
        emitter = FastAPITenantEmitter()
        files = emitter.emit(self._config())
        assert "app/core/security/tenant_middleware.py" in files

    def test_emit_has_router_file(self):
        emitter = FastAPITenantEmitter()
        files = emitter.emit(self._config())
        assert "app/core/security/tenant_router.py" in files

    def test_context_contains_contextvar(self):
        emitter = FastAPITenantEmitter()
        files = emitter.emit(self._config())
        ctx = files["app/core/security/tenant_context.py"]
        assert "ContextVar" in ctx
        assert "get_tenant_id" in ctx
        assert "set_tenant_id" in ctx

    def test_middleware_row_mode(self):
        emitter = FastAPITenantEmitter()
        files = emitter.emit(self._config(TenantMode.ROW))
        content = files["app/core/security/tenant_middleware.py"]
        assert "ROW mode" in content or "row" in content.lower()

    def test_middleware_schema_mode_has_search_path(self):
        emitter = FastAPITenantEmitter()
        files = emitter.emit(self._config(TenantMode.SCHEMA))
        content = files["app/core/security/tenant_middleware.py"]
        assert "search_path" in content

    def test_middleware_subdomain_mode(self):
        emitter = FastAPITenantEmitter()
        files = emitter.emit(self._config(TenantMode.SUBDOMAIN))
        content = files["app/core/security/tenant_middleware.py"]
        assert "SUBDOMAIN mode" in content or "subdomain" in content.lower()

    def test_router_has_create_endpoint(self):
        emitter = FastAPITenantEmitter()
        files = emitter.emit(self._config())
        content = files["app/core/security/tenant_router.py"]
        assert "create_tenant" in content
        assert "@router.post" in content

    def test_router_has_list_endpoint(self):
        emitter = FastAPITenantEmitter()
        files = emitter.emit(self._config())
        content = files["app/core/security/tenant_router.py"]
        assert "list_tenants" in content
        assert "@router.get" in content


# ===========================================================================
# NestJSTenantEmitter Tests
# ===========================================================================

class TestNestJSTenantEmitter:
    """Test NestJS tenant emitter output."""

    def test_emit_returns_three_files(self):
        emitter = NestJSTenantEmitter()
        config = TenantConfig(mode=TenantMode.ROW)
        files = emitter.emit(config)
        assert len(files) == 3

    def test_emit_has_module(self):
        emitter = NestJSTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        assert any("tenant.module" in k for k in files)

    def test_emit_has_middleware(self):
        emitter = NestJSTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        assert any("tenant.middleware" in k for k in files)

    def test_emit_has_interceptor(self):
        emitter = NestJSTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        assert any("tenant.interceptor" in k for k in files)

    def test_module_has_forConfig(self):
        emitter = NestJSTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        module_content = files["src/core/tenant/tenant.module.ts"]
        assert "forConfig" in module_content
        assert "@Global()" in module_content

    def test_middleware_has_tenant_extraction(self):
        emitter = NestJSTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        mw = files["src/core/tenant/tenant.middleware.ts"]
        assert "x-tenant-id" in mw
        assert "NestMiddleware" in mw

    def test_interceptor_filters_array(self):
        emitter = NestJSTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW, tenant_id_column="org_id"))
        interceptor = files["src/core/tenant/tenant.interceptor.ts"]
        assert "Array.isArray" in interceptor
        assert "org_id" in interceptor

    def test_interceptor_no_syntax_error(self):
        """Verify generated interceptor has no broken double-brace syntax."""
        emitter = NestJSTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        interceptor = files["src/core/tenant/tenant.interceptor.ts"]
        # Should NOT contain the broken {{'...'}} pattern
        assert "{{'tenant_id'}}" not in interceptor


# ===========================================================================
# AngularTenantEmitter Tests
# ===========================================================================

class TestAngularTenantEmitter:
    """Test Angular tenant emitter output."""

    def test_emit_returns_three_files(self):
        emitter = AngularTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        assert len(files) == 3

    def test_emit_has_service(self):
        emitter = AngularTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        assert any("tenant.service" in k for k in files)

    def test_emit_has_guard(self):
        emitter = AngularTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        assert any("tenant.guard" in k for k in files)

    def test_emit_has_interceptor(self):
        emitter = AngularTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        assert any("tenant.interceptor" in k for k in files)

    def test_service_has_behavior_subject(self):
        emitter = AngularTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        svc = files["src/app/core/tenant/tenant.service.ts"]
        assert "BehaviorSubject" in svc
        assert "getTenantId" in svc
        assert "setTenant" in svc

    def test_guard_redirects_to_select(self):
        emitter = AngularTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        guard = files["src/app/core/tenant/tenant.guard.ts"]
        assert "tenant-select" in guard
        assert "CanActivate" in guard

    def test_interceptor_injects_header(self):
        emitter = AngularTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        interceptor = files["src/app/core/tenant/tenant.interceptor.ts"]
        assert "X-Tenant-ID" in interceptor
        assert "HttpInterceptor" in interceptor


# ===========================================================================
# ReactTenantEmitter Tests
# ===========================================================================

class TestReactTenantEmitter:
    """Test React tenant emitter output."""

    def test_emit_returns_three_files(self):
        emitter = ReactTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        assert len(files) == 3

    def test_emit_has_context(self):
        emitter = ReactTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        assert any("TenantContext" in k for k in files)

    def test_emit_has_provider(self):
        emitter = ReactTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        assert any("TenantProvider" in k for k in files)

    def test_emit_has_hook(self):
        emitter = ReactTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        assert any("useTenant" in k for k in files)

    def test_context_has_create_context(self):
        emitter = ReactTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        ctx = files["src/app/core/tenant/TenantContext.ts"]
        assert "createContext" in ctx
        assert "TenantContextType" in ctx

    def test_provider_has_localstorage(self):
        emitter = ReactTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        provider = files["src/app/core/tenant/TenantProvider.tsx"]
        assert "localStorage" in provider
        assert "TenantContext.Provider" in provider

    def test_hook_throws_without_provider(self):
        emitter = ReactTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        hook = files["src/app/core/tenant/useTenant.ts"]
        assert "must be used within a TenantProvider" in hook

    def test_hook_has_use_tenant_id(self):
        emitter = ReactTenantEmitter()
        files = emitter.emit(TenantConfig(mode=TenantMode.ROW))
        hook = files["src/app/core/tenant/useTenant.ts"]
        assert "useTenantId" in hook
