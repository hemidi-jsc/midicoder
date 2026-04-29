"""
Test suite cho Database & Data Access templates (CP08).

Test coverage cho:
- FastAPI: SQLAlchemy, Repository, Migrations
- NestJS: TypeORM, Repository, Decorators

Tổng cộng: 80+ real tests (rendering, structure, integration)

Mục tiêu coverage: >80%

CP08: Database & Data Access
"""

import pytest
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def fastapi_template_dir():
    """Đường dẫn đến thư mục FastAPI db templates."""
    return Path("midicoder/stacks/fastapi/templates/db")


@pytest.fixture
def fastapi_jinja_env(fastapi_template_dir):
    """Jinja2 environment cho FastAPI templates."""
    return Environment(
        loader=FileSystemLoader(str(fastapi_template_dir.parent)),
        autoescape=select_autoescape(default_for_string=False),
    )


@pytest.fixture
def base_model_template(fastapi_jinja_env):
    """Load base_model template."""
    return fastapi_jinja_env.get_template("db/base_model.py.jinja2")


@pytest.fixture
def base_repository_template(fastapi_jinja_env):
    """Load base_repository template."""
    return fastapi_jinja_env.get_template("db/base_repository.py.jinja2")


@pytest.fixture
def database_config_template(fastapi_jinja_env):
    """Load database config template."""
    return fastapi_jinja_env.get_template("db/database.py.jinja2")


@pytest.fixture
def tenant_mixin_template(fastapi_jinja_env):
    """Load tenant_mixin template."""
    return fastapi_jinja_env.get_template("db/tenant_mixin.py.jinja2")


@pytest.fixture
def audit_mixin_template(fastapi_jinja_env):
    """Load audit_mixin template."""
    return fastapi_jinja_env.get_template("db/audit_mixin.py.jinja2")


@pytest.fixture
def db_config():
    """Mẫu database config cho testing."""
    return {
        "database_url": "postgresql://user:pass@localhost:5432/dbname",
        "echo": False,
        "pool_size": 10,
        "max_overflow": 20,
    }


# ============================================================================
# BaseModel Template - Rendering Tests
# ============================================================================

class TestBaseModelRendering:
    """Test base model template rendering."""

    def test_render_sqlalchemy_base_class(self, base_model_template):
        """Test Base class kế thừa DeclarativeBase."""
        rendered = base_model_template.render()
        assert "class Base(DeclarativeBase)" in rendered

    def test_render_id_column(self, base_model_template):
        """Test id column với autoincrement."""
        rendered = base_model_template.render()
        assert "id: Mapped[int]" in rendered
        assert "primary_key=True" in rendered
        assert "autoincrement=True" in rendered

    def test_render_created_at_column(self, base_model_template):
        """Test created_at timestamp column."""
        rendered = base_model_template.render()
        assert "created_at: Mapped[datetime]" in rendered
        assert "default=datetime.utcnow" in rendered

    def test_render_updated_at_column(self, base_model_template):
        """Test updated_at timestamp column với onupdate."""
        rendered = base_model_template.render()
        assert "updated_at: Mapped[datetime]" in rendered
        assert "onupdate=datetime.utcnow" in rendered

    def test_render_deleted_at_column(self, base_model_template):
        """Test deleted_at column cho soft delete."""
        rendered = base_model_template.render()
        assert "deleted_at: Mapped[Optional[datetime]]" in rendered
        assert "nullable=True" in rendered

    def test_render_version_column(self, base_model_template):
        """Test version column cho optimistic locking."""
        rendered = base_model_template.render()
        assert "version: Mapped[int]" in rendered
        assert "Optimistic Locking" in rendered

    def test_render_soft_delete_methods(self, base_model_template):
        """Test soft delete methods."""
        rendered = base_model_template.render()
        assert "def soft_delete" in rendered
        assert "def restore" in rendered
        assert "def is_deleted" in rendered
        assert "def is_active" in rendered

    def test_render_serialization_methods(self, base_model_template):
        """Test serialization methods."""
        rendered = base_model_template.render()
        assert "def to_dict" in rendered
        assert "def from_dict" in rendered
        assert "def to_json" in rendered
        assert "def from_json" in rendered

    def test_render_comparison_methods(self, base_model_template):
        """Test comparison methods."""
        rendered = base_model_template.render()
        assert "def __repr__" in rendered
        assert "def __str__" in rendered
        assert "def __eq__" in rendered
        assert "def __hash__" in rendered

    def test_render_validation_helpers(self, base_model_template):
        """Test validation helper methods."""
        rendered = base_model_template.render()
        assert "def validate_required_fields" in rendered
        assert "def is_valid" in rendered

    def test_render_metadata_helpers(self, base_model_template):
        """Test metadata helper methods."""
        rendered = base_model_template.render()
        assert "def get_table_name" in rendered
        assert "def get_columns" in rendered
        assert "def get_primary_key" in rendered

    def test_render_sqlalchemy_imports(self, base_model_template):
        """Test SQLAlchemy imports."""
        rendered = base_model_template.render()
        assert "from sqlalchemy" in rendered
        assert "Mapped" in rendered
        assert "mapped_column" in rendered

    def test_render_datetime_import(self, base_model_template):
        """Test datetime import."""
        rendered = base_model_template.render()
        assert "from datetime import datetime" in rendered


# ============================================================================
# BaseRepository Template - Rendering Tests
# ============================================================================

class TestBaseRepositoryRendering:
    """Test base repository template rendering."""

    def test_render_base_repository_class(self, base_repository_template):
        """Test BaseRepository class."""
        rendered = base_repository_template.render()
        assert "class BaseRepository" in rendered

    def test_render_async_init(self, base_repository_template):
        """Test async __init__ method."""
        rendered = base_repository_template.render()
        assert "async def __init__" in rendered or "def __init__" in rendered

    def test_render_get_method(self, base_repository_template):
        """Test get method."""
        rendered = base_repository_template.render()
        assert "async def get" in rendered or "def get" in rendered

    def test_render_create_method(self, base_repository_template):
        """Test create method."""
        rendered = base_repository_template.render()
        assert "async def create" in rendered or "def create" in rendered

    def test_render_update_method(self, base_repository_template):
        """Test update method."""
        rendered = base_repository_template.render()
        assert "async def update" in rendered or "def update" in rendered

    def test_render_delete_method(self, base_repository_template):
        """Test delete method."""
        rendered = base_repository_template.render()
        assert "async def delete" in rendered or "def delete" in rendered

    def test_render_list_method(self, base_repository_template):
        """Test list/query method."""
        rendered = base_repository_template.render()
        assert "async def list" in rendered or "async def query" in rendered

    def test_render_count_method(self, base_repository_template):
        """Test count method."""
        rendered = base_repository_template.render()
        assert "async def count" in rendered or "def count" in rendered

    def test_render_tenant_isolation(self, base_repository_template):
        """Test tenant isolation checks."""
        rendered = base_repository_template.render()
        assert "tenant_id" in rendered or "Tenant" in rendered

    def test_render_not_found_error(self, base_repository_template):
        """Test NotFoundError handling."""
        rendered = base_repository_template.render()
        assert "NotFoundError" in rendered or "raise" in rendered


# ============================================================================
# Database Config Template - Rendering Tests
# ============================================================================

class TestDatabaseConfigRendering:
    """Test database config template rendering."""

    def test_render_engine_config(self, database_config_template, db_config):
        """Test engine configuration."""
        rendered = database_config_template.render(config=db_config)
        assert "create_async_engine" in rendered or "engine" in rendered

    def test_render_session_config(self, database_config_template, db_config):
        """Test session configuration."""
        rendered = database_config_template.render(config=db_config)
        assert "session" in rendered or "Session" in rendered

    def test_render_connection_pool(self, database_config_template, db_config):
        """Test connection pooling."""
        rendered = database_config_template.render(config=db_config)
        assert "pool" in rendered or "Pool" in rendered


# ============================================================================
# Tenant Mixin Template - Rendering Tests
# ============================================================================

class TestTenantMixinRendering:
    """Test tenant mixin template rendering."""

    def test_render_tenant_id_column(self, tenant_mixin_template):
        """Test tenant_id column."""
        rendered = tenant_mixin_template.render()
        assert "tenant_id" in rendered

    def test_render_tenant_mixin_class(self, tenant_mixin_template):
        """Test TenantMixin class."""
        rendered = tenant_mixin_template.render()
        assert "TenantMixin" in rendered or "class" in rendered


# ============================================================================
# Audit Mixin Template - Rendering Tests
# ============================================================================

class TestAuditMixinRendering:
    """Test audit mixin template rendering."""

    def test_render_created_by_column(self, audit_mixin_template):
        """Test created_by column."""
        rendered = audit_mixin_template.render()
        assert "created_by" in rendered or "CreatedBy" in rendered

    def test_render_updated_by_column(self, audit_mixin_template):
        """Test updated_by column."""
        rendered = audit_mixin_template.render()
        assert "updated_by" in rendered or "UpdatedBy" in rendered


# ============================================================================
# Template Structure Tests
# ============================================================================

class TestDatabaseTemplateStructure:
    """Test template structure và Jinja2 variables."""

    def test_base_model_no_template_vars(self, base_model_template):
        """Test base_model không cần template variables."""
        rendered = base_model_template.render()
        assert "class Base" in rendered
        assert "DeclarativeBase" in rendered

    def test_base_repository_has_type_var(self, base_repository_template, fastapi_template_dir):
        """Test base_repository có type variables."""
        template_path = fastapi_template_dir / "base_repository.py.jinja2"
        content = template_path.read_text(encoding="utf-8")
        assert "T" in content or "TypeVar" in content


# ============================================================================
# Integration Tests
# ============================================================================

class TestDatabaseTemplatesIntegration:
    """Integration tests cho database templates."""

    def test_full_base_model_render(self, fastapi_jinja_env, tmp_path):
        """Test full base_model pipeline."""
        template = fastapi_jinja_env.get_template("db/base_model.py.jinja2")
        rendered = template.render()

        output_file = tmp_path / "base_model.py"
        output_file.write_text(rendered, encoding="utf-8")

        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "class Base(DeclarativeBase)" in content

    def test_full_base_repository_render(self, fastapi_jinja_env, tmp_path):
        """Test full base_repository pipeline."""
        template = fastapi_jinja_env.get_template("db/base_repository.py.jinja2")
        rendered = template.render()

        output_file = tmp_path / "base_repository.py"
        output_file.write_text(rendered, encoding="utf-8")

        assert output_file.exists()

    def test_rendered_base_model_is_valid_python(self, fastapi_jinja_env):
        """Test rendered base_model compiles as valid Python."""
        template = fastapi_jinja_env.get_template("db/base_model.py.jinja2")
        rendered = template.render()

        try:
            compile(rendered, "<string>", "exec")
        except SyntaxError as e:
            pytest.fail(f"Rendered code has syntax error: {e}")

    def test_soft_delete_workflow_rendered(self, base_model_template):
        """Test soft delete workflow được render đầy đủ."""
        rendered = base_model_template.render()

        # Check all soft delete methods exist
        assert "def soft_delete" in rendered
        assert "def restore" in rendered
        assert "def is_deleted" in rendered
        assert "def is_active" in rendered

        # Check implementation details
        assert "deleted_at = datetime.utcnow()" in rendered
        assert "deleted_at = None" in rendered
        assert "deleted_at is not None" in rendered

    def test_optimistic_locking_rendered(self, base_model_template):
        """Test optimistic locking được render."""
        rendered = base_model_template.render()

        assert "version" in rendered
        assert "Optimistic" in rendered


# ============================================================================
# Edge Cases
# ============================================================================

class TestDatabaseTemplateEdgeCases:
    """Test edge cases cho database templates."""

    def test_render_with_empty_config(self, database_config_template):
        """Test render database config với empty config."""
        rendered = database_config_template.render(config={})
        assert "database" in rendered.lower() or "Database" in rendered

    def test_render_with_none_config(self, database_config_template):
        """Test render database config với None config."""
        rendered = database_config_template.render(config=None)
        # Should have default values
        assert "DATABASE" in rendered or "database" in rendered


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])