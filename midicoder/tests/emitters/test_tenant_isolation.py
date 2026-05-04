"""
Tests cho Tenant Isolation Templates.

Kiểm tra tenant isolation đã được implement đúng trong:
- FastAPI entity templates (SQLAlchemy)
- NestJS entity templates (TypeORM)

KPI-029: Tenant Isolation
"""

import pytest
from pathlib import Path


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def fastapi_entity_template_path():
    """Path đến FastAPI entity template."""
    return Path("midicoder/stacks/fastapi/templates/domain/entities/entity.py.jinja2")


@pytest.fixture
def nestjs_entity_template_path():
    """Path đến NestJS entity template."""
    return Path("midicoder/stacks/nestjs/templates/domain/entities/entity.ts.jinja2")


@pytest.fixture
def fastapi_tenant_mixin_path():
    """Path đến FastAPI tenant mixin template."""
    return Path("midicoder/stacks/fastapi/templates/db/tenant_mixin.py.jinja2")


@pytest.fixture
def nestjs_tenant_decorators_path():
    """Path đến NestJS tenant decorators template."""
    return Path("midicoder/stacks/nestjs/templates/db/tenant.decorators.ts.jinja2")


# ============================================================================
# FastAPI Entity Template Tests
# ============================================================================

class TestFastAPIEntityTemplate:
    """Tests cho FastAPI entity template với tenant isolation."""

    def test_template_file_exists(self, fastapi_entity_template_path):
        """Template file phải tồn tại."""
        assert fastapi_entity_template_path.exists()

    def test_template_contains_tenant_row_mixin(self, fastapi_entity_template_path):
        """Template phải kế thừa TenantRowMixin."""
        content = fastapi_entity_template_path.read_text()
        assert "TenantRowMixin" in content

    def test_template_contains_tenant_id_docstring(self, fastapi_entity_template_path):
        """Template phải có docstring về tenant isolation."""
        content = fastapi_entity_template_path.read_text()
        assert "Tenant Isolation" in content
        assert "tenant_id" in content

    def test_template_inheritance_syntax(self, fastapi_entity_template_path):
        """Template phải có syntax kế thừa đúng (Base, TenantRowMixin)."""
        content = fastapi_entity_template_path.read_text()
        assert "(Base, TenantRowMixin)" in content

    def test_template_usage_example(self, fastapi_entity_template_path):
        """Template phải có usage example cho tenant."""
        content = fastapi_entity_template_path.read_text()
        assert "is_tenant_owner" in content or "tenant_id" in content


# ============================================================================
# FastAPI Tenant Mixin Tests
# ============================================================================

class TestFastAPITenantMixin:
    """Tests cho FastAPI tenant mixin template."""

    def test_tenant_mixin_file_exists(self, fastapi_tenant_mixin_path):
        """Tenant mixin file phải tồn tại."""
        assert fastapi_tenant_mixin_path.exists()

    def test_tenant_row_mixin_class_exists(self, fastapi_tenant_mixin_path):
        """TenantRowMixin class phải được define."""
        content = fastapi_tenant_mixin_path.read_text(encoding='utf-8')
        assert "class TenantRowMixin" in content

    def test_tenant_schema_mixin_class_exists(self, fastapi_tenant_mixin_path):
        """TenantSchemaMixin class phải được define."""
        content = fastapi_tenant_mixin_path.read_text(encoding='utf-8')
        assert "class TenantSchemaMixin" in content

    def test_tenant_database_mixin_class_exists(self, fastapi_tenant_mixin_path):
        """TenantDatabaseMixin class phải được define."""
        content = fastapi_tenant_mixin_path.read_text(encoding='utf-8')
        assert "class TenantDatabaseMixin" in content

    def test_tenant_row_mixin_has_tenant_id(self, fastapi_tenant_mixin_path):
        """TenantRowMixin phải có tenant_id column."""
        content = fastapi_tenant_mixin_path.read_text(encoding='utf-8')
        assert "tenant_id" in content
        assert "Mapped[str]" in content

    def test_tenant_row_mixin_has_index(self, fastapi_tenant_mixin_path):
        """TenantRowMixin phải có index trên tenant_id."""
        content = fastapi_tenant_mixin_path.read_text(encoding='utf-8')
        assert "idx_tenant_id" in content

    def test_tenant_row_mixin_has_is_tenant_owner(self, fastapi_tenant_mixin_path):
        """TenantRowMixin phải có is_tenant_owner method."""
        content = fastapi_tenant_mixin_path.read_text(encoding='utf-8')
        assert "def is_tenant_owner" in content

    def test_tenant_schema_mixin_has_get_tenant_schema(self, fastapi_tenant_mixin_path):
        """TenantSchemaMixin phải có get_tenant_schema method."""
        content = fastapi_tenant_mixin_path.read_text(encoding='utf-8')
        assert "def get_tenant_schema" in content

    def test_tenant_database_mixin_has_get_tenant_database_url(self, fastapi_tenant_mixin_path):
        """TenantDatabaseMixin phải có get_tenant_database_url method."""
        content = fastapi_tenant_mixin_path.read_text(encoding='utf-8')
        assert "def get_tenant_database_url" in content

    def test_vietnamese_docstrings(self, fastapi_tenant_mixin_path):
        """Template phải có Vietnamese docstrings."""
        content = fastapi_tenant_mixin_path.read_text(encoding='utf-8')
        # Check for Vietnamese characters
        assert "cho" in content or "lấy" in content or "kiểm tra" in content


# ============================================================================
# NestJS Entity Template Tests
# ============================================================================

class TestNestJSEntityTemplate:
    """Tests cho NestJS entity template với tenant isolation."""

    def test_template_file_exists(self, nestjs_entity_template_path):
        """Template file phải tồn tại."""
        assert nestjs_entity_template_path.exists()

    def test_template_contains_tenant_id_column(self, nestjs_entity_template_path):
        """Template phải có tenantId column."""
        content = nestjs_entity_template_path.read_text(encoding='utf-8')
        assert "tenantId" in content

    def test_template_contains_tenant_id_decorator(self, nestjs_entity_template_path):
        """Template phải có @Column decorator cho tenantId."""
        content = nestjs_entity_template_path.read_text(encoding='utf-8')
        assert "@Column" in content
        assert "tenantId" in content

    def test_template_contains_tenant_index(self, nestjs_entity_template_path):
        """Template phải có @Index decorator cho tenantId."""
        content = nestjs_entity_template_path.read_text(encoding='utf-8')
        assert "@Index" in content
        assert "idx_tenant_id" in content

    def test_template_contains_is_tenant_owner_method(self, nestjs_entity_template_path):
        """Template phải có isTenantOwner method."""
        content = nestjs_entity_template_path.read_text(encoding='utf-8')
        assert "isTenantOwner" in content

    def test_template_contains_before_insert_hook(self, nestjs_entity_template_path):
        """Template phải có @BeforeInsert hook cho tenant validation."""
        content = nestjs_entity_template_path.read_text(encoding='utf-8')
        assert "@BeforeInsert" in content
        assert "validateTenantOnInsert" in content

    def test_template_contains_before_update_hook(self, nestjs_entity_template_path):
        """Template phải có @BeforeUpdate hook cho tenant immutability."""
        content = nestjs_entity_template_path.read_text(encoding='utf-8')
        assert "@BeforeUpdate" in content
        assert "preventTenantChange" in content

    def test_template_contains_vietnamese_comments(self, nestjs_entity_template_path):
        """Template phải có Vietnamese comments/docstrings."""
        content = nestjs_entity_template_path.read_text(encoding='utf-8')
        # Check for Vietnamese characters in comments
        assert "cho" in content or "kiểm tra" in content or "bắt buộc" in content

    def test_tenant_id_is_uuid_type(self, nestjs_entity_template_path):
        """tenantId phải là UUID type."""
        content = nestjs_entity_template_path.read_text(encoding='utf-8')
        assert "type: 'uuid'" in content

    def test_tenant_id_is_not_nullable(self, nestjs_entity_template_path):
        """tenantId phải là non-nullable."""
        content = nestjs_entity_template_path.read_text(encoding='utf-8')
        assert "nullable: false" in content


# ============================================================================
# Integration Tests
# ============================================================================

class TestTenantIsolationIntegration:
    """Integration tests cho tenant isolation."""

    def test_both_templates_have_tenant_isolation(self, fastapi_entity_template_path, nestjs_entity_template_path):
        """Cả FastAPI và NestJS templates đều phải có tenant isolation."""
        fastapi_content = fastapi_entity_template_path.read_text(encoding='utf-8')
        nestjs_content = nestjs_entity_template_path.read_text(encoding='utf-8')
        
        # FastAPI: TenantRowMixin
        assert "TenantRowMixin" in fastapi_content
        
        # NestJS: tenantId column
        assert "tenantId" in nestjs_content

    def test_kpi_029_reference(self, fastapi_tenant_mixin_path, nestjs_entity_template_path):
        """Templates phải reference KPI-029."""
        fastapi_mixin_content = fastapi_tenant_mixin_path.read_text(encoding='utf-8')
        nestjs_content = nestjs_entity_template_path.read_text(encoding='utf-8')
        
        # Either explicit KPI-029 reference or tenant isolation mention
        has_kpi_ref = (
            "KPI-029" in fastapi_mixin_content or 
            "KPI-029" in nestjs_content or
            "tenant isolation" in fastapi_mixin_content.lower() or
            "Tenant Isolation" in nestjs_content
        )
        assert has_kpi_ref, "Must have KPI-029 reference or tenant isolation mention"


# ============================================================================
# NestJS Tenant Decorators Tests
# ============================================================================

class TestNestJSTenantDecorators:
    """Tests cho NestJS tenant decorators template."""

    def test_decorators_file_exists(self, nestjs_tenant_decorators_path):
        """Tenant decorators file phải tồn tại."""
        assert nestjs_tenant_decorators_path.exists()

    def test_tenant_row_decorator_exists(self, nestjs_tenant_decorators_path):
        """TenantRow decorator phải được define."""
        content = nestjs_tenant_decorators_path.read_text(encoding='utf-8')
        assert "export function TenantRow()" in content

    def test_tenant_schema_decorator_exists(self, nestjs_tenant_decorators_path):
        """TenantSchema decorator phải được define."""
        content = nestjs_tenant_decorators_path.read_text(encoding='utf-8')
        assert "export function TenantSchema" in content

    def test_tenant_database_decorator_exists(self, nestjs_tenant_decorators_path):
        """TenantDatabase decorator phải được define."""
        content = nestjs_tenant_decorators_path.read_text(encoding='utf-8')
        assert "export function TenantDatabase" in content

    def test_tenant_row_metadata_key(self, nestjs_tenant_decorators_path):
        """TENANT_ROW_KEY phải được define."""
        content = nestjs_tenant_decorators_path.read_text(encoding='utf-8')
        assert "TENANT_ROW_KEY" in content

    def test_tenant_schema_metadata_key(self, nestjs_tenant_decorators_path):
        """TENANT_SCHEMA_KEY phải được define."""
        content = nestjs_tenant_decorators_path.read_text(encoding='utf-8')
        assert "TENANT_SCHEMA_KEY" in content

    def test_tenant_database_metadata_key(self, nestjs_tenant_decorators_path):
        """TENANT_DATABASE_KEY phải được define."""
        content = nestjs_tenant_decorators_path.read_text(encoding='utf-8')
        assert "TENANT_DATABASE_KEY" in content

    def test_tenant_metadata_interface(self, nestjs_tenant_decorators_path):
        """TenantMetadata interface phải được define."""
        content = nestjs_tenant_decorators_path.read_text(encoding='utf-8')
        assert "interface TenantMetadata" in content

    def test_tenant_context_helpers(self, nestjs_tenant_decorators_path):
        """Tenant context helper functions phải được define."""
        content = nestjs_tenant_decorators_path.read_text(encoding='utf-8')
        assert "getTenantContext" in content
        assert "setTenantContext" in content
        assert "clearTenantContext" in content

    def test_vietnamese_docstrings_decorators(self, nestjs_tenant_decorators_path):
        """Decorators phải có Vietnamese docstrings."""
        content = nestjs_tenant_decorators_path.read_text(encoding='utf-8')
        assert "cho" in content or "tự động" in content or "bắt buộc" in content


class TestNestJSEntityTemplateWithDecorator:
    """Tests cho NestJS entity template với @TenantRow decorator."""

    def test_entity_uses_tenant_row_decorator(self, nestjs_entity_template_path):
        """Entity template phải dùng @TenantRow() decorator."""
        content = nestjs_entity_template_path.read_text(encoding='utf-8')
        assert "@TenantRow()" in content

    def test_entity_imports_tenant_row(self, nestjs_entity_template_path):
        """Entity template phải import TenantRow."""
        content = nestjs_entity_template_path.read_text(encoding='utf-8')
        assert "import { TenantRow }" in content or "from '@app/common/tenant'" in content

    def test_entity_has_tenant_isolation_docstring(self, nestjs_entity_template_path):
        """Entity template phải có docstring về Tenant Isolation."""
        content = nestjs_entity_template_path.read_text(encoding='utf-8')
        assert "Tenant Isolation" in content
        assert "@TenantRow" in content
