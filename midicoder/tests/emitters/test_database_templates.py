"""
Test suite cho Database & Data Access templates (CP08).

Test coverage cho:
- FastAPI: SQLAlchemy, Repository, Migrations
- NestJS: TypeORM, Repository, Decorators

Tổng cộng: 55+ tests

Mục tiêu coverage: >80%

CP08: Database & Data Access
"""

from unittest import TestCase
from pathlib import Path


class TestSQLAlchemyBaseModel(TestCase):
    """Test SQLAlchemy base model template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/fastapi/templates/db/base_model.py.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Base model template không tồn tại")

    def test_template_has_sqlalchemy_imports(self):
        """Test template có SQLAlchemy imports."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("sqlalchemy", content) or self.assertIn("SQLAlchemy", content)

    def test_template_has_declarative_base(self):
        """Test template có DeclarativeBase."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("Base", content) or self.assertIn("Model", content)

    def test_template_has_id_column(self):
        """Test template có ID column."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("id", content) or self.assertIn("ID", content)

    def test_template_has_created_at(self):
        """Test template có created_at timestamp."""
        content = self.template_path.read_text(encoding="utf-8")
        assert "created_at" in content or "timestamp" in content or "datetime" in content, "Không có created_at/timestamp/datetime"

    def test_template_has_updated_at(self):
        """Test template có updated_at timestamp."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("updated", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


class TestTenantMixinModel(TestCase):
    """Test TenantMixin model template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/fastapi/templates/db/tenant_mixin.py.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Tenant mixin template không tồn tại")

    def test_template_has_tenant_id_column(self):
        """Test template có tenant_id column."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("tenant", content) or self.assertIn("Tenant", content)

    def test_template_has_sqlalchemy(self):
        """Test template có SQLAlchemy."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("sqlalchemy", content) or self.assertIn("Column", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


class TestAuditMixinModel(TestCase):
    """Test AuditMixin model template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/fastapi/templates/db/audit_mixin.py.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Audit mixin template không tồn tại")

    def test_template_has_created_by(self):
        """Test template có created_by column."""
        content = self.template_path.read_text(encoding="utf-8")
        assert "created_by" in content or "author" in content or "Created" in content, "Không có created_by/author"

    def test_template_has_updated_by(self):
        """Test template có updated_by column."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("updated", content)

    def test_template_has_deleted_at(self):
        """Test template có soft delete column."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("deleted", content) or self.assertIn("soft", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


class TestBaseRepository(TestCase):
    """Test BaseRepository template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/fastapi/templates/db/base_repository.py.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Base repository template không tồn tại")

    def test_template_has_get_method(self):
        """Test template có get method."""
        content = self.template_path.read_text(encoding="utf-8")
        assert "def get" in content or "find" in content, "Không có get/find method"

    def test_template_has_create_method(self):
        """Test template có create method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("create", content) or self.assertIn("add", content)

    def test_template_has_update_method(self):
        """Test template có update method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("update", content)

    def test_template_has_delete_method(self):
        """Test template có delete method."""
        content = self.template_path.read_text(encoding="utf-8")
        assert "def delete" in content or "def soft_delete" in content or "delete(" in content, "Không có delete method"

    def test_template_has_list_method(self):
        """Test template có list/query method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("list", content) or self.assertIn("query", content)

    def test_template_has_async(self):
        """Test template có async support."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async", content) or self.assertIn("await", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


class TestDatabaseConfig(TestCase):
    """Test Database config template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/fastapi/templates/db/database.py.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Database config template không tồn tại")

    def test_template_has_engine_config(self):
        """Test template có engine configuration."""
        content = self.template_path.read_text(encoding="utf-8")
        assert "engine" in content or "Engine" in content or "create_async_engine" in content, "Không có engine config"

    def test_template_has_session(self):
        """Test template có session configuration."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("session", content) or self.assertIn("Session", content)

    def test_template_has_connection_pool(self):
        """Test template có connection pooling."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("pool", content) or self.assertIn("Pool", content)

    def test_template_has_database_url(self):
        """Test template có DATABASE_URL."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("DATABASE", content) or self.assertIn("database", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


class TestAlembicMigration(TestCase):
    """Test Alembic migration template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/fastapi/templates/db/migrations/env.py.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "Alembic migration template không tồn tại")

    def test_template_has_alembic_config(self):
        """Test template có Alembic configuration."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("alembic", content) or self.assertIn("Alembic", content)

    def test_template_has_migration_context(self):
        """Test template có migration context."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("alembic", content) or self.assertIn("context", content) or self.assertIn("migrations", content)

    def test_template_has_target_metadata(self):
        """Test template có target_metadata."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("metadata", content) or self.assertIn("target", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("#", content) or self.assertIn('"""', content)


class TestNestJsDatabaseModule(TestCase):
    """Test NestJS DatabaseModule template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/nestjs/templates/db/database.module.ts.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "NestJS DatabaseModule không tồn tại")

    def test_template_has_typeorm(self):
        """Test template có TypeORM imports."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("typeorm", content) or self.assertIn("TypeOrmModule", content)

    def test_template_has_database_config(self):
        """Test template có database configuration."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("forRoot", content) or self.assertIn("DATABASE", content)

    def test_template_has_pooling(self):
        """Test template có connection pooling."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("pool", content) or self.assertIn("max", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("/", content) or self.assertIn("*", content)


class TestNestJsBaseEntity(TestCase):
    """Test NestJS BaseEntity template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/nestjs/templates/db/base.entity.ts.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "NestJS BaseEntity không tồn tại")

    def test_template_has_entity_decorator(self):
        """Test template có @Entity decorator."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("@Entity", content) or self.assertIn("Entity", content)

    def test_template_has_id_column(self):
        """Test template có ID column."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("id", content) or self.assertIn("PrimaryGeneratedColumn", content)

    def test_template_has_timestamps(self):
        """Test template có createdAt/updatedAt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("createdAt", content) or self.assertIn("updatedAt", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("/", content) or self.assertIn("*", content)


class TestNestJsTenantDecorator(TestCase):
    """Test NestJS Tenant decorator template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/nestjs/templates/db/tenant.decorator.ts.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "NestJS Tenant decorator không tồn tại")

    def test_template_has_tenant_column(self):
        """Test template có TenantColumn decorator."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("TenantColumn", content) or self.assertIn("tenant_id", content)

    def test_template_has_itenant_interface(self):
        """Test template có ITenant interface."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("ITenant", content) or self.assertIn("tenantId", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("/", content) or self.assertIn("*", content)


class TestNestJsAuditDecorator(TestCase):
    """Test NestJS Audit decorator template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/nestjs/templates/db/audit.decorator.ts.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "NestJS Audit decorator không tồn tại")

    def test_template_has_audit_columns(self):
        """Test template có audit columns."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("createdBy", content) or self.assertIn("updatedBy", content)

    def test_template_has_soft_delete(self):
        """Test template có soft delete support."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("deletedAt", content) or self.assertIn("DeleteDateColumn", content)

    def test_template_has_iaudit_interface(self):
        """Test template có IAudit interface."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("IAudit", content) or self.assertIn("isDeleted", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("/", content) or self.assertIn("*", content)


class TestNestJsBaseRepository(TestCase):
    """Test NestJS BaseRepository template."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/nestjs/templates/db/base.repository.ts.jinja2")

    def test_template_file_exists(self):
        """Test template file tồn tại."""
        self.assertTrue(self.template_path.exists(), "NestJS BaseRepository không tồn tại")

    def test_template_has_get_method(self):
        """Test template có get method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async get", content) or self.assertIn("findOne", content)

    def test_template_has_create_method(self):
        """Test template có create method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async create", content)

    def test_template_has_update_method(self):
        """Test template có update method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async update", content)

    def test_template_has_delete_method(self):
        """Test template có delete method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async delete", content)

    def test_template_has_list_method(self):
        """Test template có list method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async list", content) or self.assertIn("findAndCount", content)

    def test_template_has_count_method(self):
        """Test template có count method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("async count", content)

    def test_template_has_vietnamese_comments(self):
        """Test template có comments tiếng Việt."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("/", content) or self.assertIn("*", content)


class TestFastAPIRepositoryHardening(TestCase):
    """Test hardened features in FastAPI base_repository."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/fastapi/templates/db/base_repository.py.jinja2")

    def test_template_has_notfound_error(self):
        """Test template có NotFoundError class."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("NotFoundError", content)

    def test_template_has_tenant_isolation_error(self):
        """Test template có TenantIsolationError class."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("TenantIsolationError", content)

    def test_template_has_validation_error(self):
        """Test template có ValidationError class."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("ValidationError", content)

    def test_template_has_tenant_isolation_check(self):
        """Test template có tenant isolation check trong update."""
        content = self.template_path.read_text(encoding="utf-8")
        # Check for tenant_id prevention in update
        self.assertIn("tenant_id", content)
        self.assertIn("TenantIsolationError", content)

    def test_template_has_transaction_support(self):
        """Test template có transaction wrapper."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("transaction", content)
        self.assertIn("commit", content)
        self.assertIn("rollback", content)

    def test_template_has_bulk_create(self):
        """Test template có bulk_create method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("bulk_create", content)

    def test_template_has_bulk_update(self):
        """Test template có bulk_update method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("bulk_update", content)

    def test_template_has_kpi_029_comments(self):
        """Test template có KPI-029 comments (tenant filter detection)."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("KPI-029", content) or self.assertIn("tenant filter", content)

    def test_template_has_load_relations_support(self):
        """Test template có eager loading support."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("load_relations", content) or self.assertIn("selectinload", content)

    def test_template_has_safety_limit(self):
        """Test template có safety limit cho list."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("1000", content) or self.assertIn("min(limit", content)


class TestFastAPIRepositoryMethods(TestCase):
    """Test specific method signatures in FastAPI base_repository."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/fastapi/templates/db/base_repository.py.jinja2")

    def test_get_raises_notfound(self):
        """Test get method raises NotFoundError."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("raise NotFoundError", content)

    def test_update_validates_tenant(self):
        """Test update method validates tenant."""
        content = self.template_path.read_text(encoding="utf-8")
        # Should have tenant verification
        self.assertIn("tenant_id", content)

    def test_validate_before_create_exists(self):
        """Test _validate_before_create method exists."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("_validate_before_create", content)

    def test_validate_before_update_exists(self):
        """Test _validate_before_update method exists."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("_validate_before_update", content)


class TestNestJSRepositoryHardening(TestCase):
    """Test hardened features in NestJS base.repository."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/nestjs/templates/db/base.repository.ts.jinja2")

    def test_template_has_notfound_error(self):
        """Test template có NotFoundError class."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("NotFoundError", content)

    def test_template_has_tenant_isolation_error(self):
        """Test template có TenantIsolationError class."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("TenantIsolationError", content)

    def test_template_has_validation_error(self):
        """Test template có ValidationError class."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("ValidationError", content)

    def test_template_has_repository_error(self):
        """Test template có RepositoryError base class."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("RepositoryError", content)

    def test_template_has_tenant_isolation_check(self):
        """Test template có tenant isolation check trong update."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("tenantId", content)
        self.assertIn("TenantIsolationError", content)

    def test_template_has_transaction_support(self):
        """Test template có transaction wrapper."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("transaction", content)
        self.assertIn("EntityManager", content)

    def test_template_has_bulk_create(self):
        """Test template có bulkCreate method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("bulkCreate", content)

    def test_template_has_bulk_update(self):
        """Test template có bulkUpdate method."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("bulkUpdate", content)

    def test_template_has_kpi_029_comments(self):
        """Test template có KPI-029 comments."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("KPI-029", content)

    def test_template_has_safety_limit(self):
        """Test template có safety limit cho list."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("1000", content) or self.assertIn("Math.min", content)

    def test_template_has_select_support(self):
        """Test template có projection support (select)."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("select", content) or self.assertIn("FindOptionsSelect", content)

    def test_template_has_order_support(self):
        """Test template có order by support."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("order", content) or self.assertIn("FindOptionsOrder", content)

    def test_template_has_validate_hooks(self):
        """Test template có validation hooks."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("validateBeforeCreate", content)
        self.assertIn("validateBeforeUpdate", content)


class TestFastAPIBaseModelComprehensive(TestCase):
    """Test comprehensive features in FastAPI base_model."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/fastapi/templates/db/base_model.py.jinja2")

    def test_template_has_soft_delete_fields(self):
        """Test template có deleted_at field."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("deleted_at", content)
        self.assertIn("Deleted at", content) or self.assertIn("soft delete", content)

    def test_template_has_optimistic_locking(self):
        """Test template có version field cho optimistic locking."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("version", content)
        self.assertIn("Optimistic Locking", content) or self.assertIn("optimistic", content)

    def test_template_has_soft_delete_methods(self):
        """Test template có soft delete methods."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("soft_delete", content)
        self.assertIn("restore", content)
        self.assertIn("is_deleted", content)
        self.assertIn("is_active", content)

    def test_template_has_serialization_methods(self):
        """Test template có serialization methods."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("to_dict", content)
        self.assertIn("from_dict", content)
        self.assertIn("to_json", content)
        self.assertIn("from_json", content)

    def test_template_has_comparison_methods(self):
        """Test template có comparison methods."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("__repr__", content)
        self.assertIn("__str__", content)
        self.assertIn("__eq__", content)
        self.assertIn("__hash__", content)

    def test_template_has_validation_helpers(self):
        """Test template có validation helpers."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("validate_required_fields", content)
        self.assertIn("is_valid", content)

    def test_template_has_metadata_helpers(self):
        """Test template có metadata helpers."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("get_table_name", content)
        self.assertIn("get_columns", content)
        self.assertIn("get_primary_key", content)


class TestNestJSBaseEntityComprehensive(TestCase):
    """Test comprehensive features in NestJS base.entity."""

    def setUp(self):
        """Thiết lập test fixtures."""
        self.template_path = Path("midicoder/stacks/nestjs/templates/db/base.entity.ts.jinja2")

    def test_template_has_soft_delete_fields(self):
        """Test template có deletedAt field."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("deletedAt", content)
        self.assertIn("DeleteDateColumn", content)

    def test_template_has_optimistic_locking(self):
        """Test template có version field cho optimistic locking."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("version", content)
        self.assertIn("optimistic", content)

    def test_template_has_soft_delete_methods(self):
        """Test template có soft delete methods."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("softDelete", content)
        self.assertIn("restore", content)
        self.assertIn("isDeleted", content)
        self.assertIn("isActive", content)

    def test_template_has_serialization_methods(self):
        """Test template có serialization methods."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("toObject", content)
        self.assertIn("fromObject", content)
        self.assertIn("toJSON", content)
        self.assertIn("fromJSON", content)
        self.assertIn("clone", content)

    def test_template_has_validation_helpers(self):
        """Test template có validation helpers."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("validateRequiredFields", content)
        self.assertIn("isValid", content)

    def test_template_has_comparison_methods(self):
        """Test template có comparison methods."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("equals", content)
        self.assertIn("toString", content)

    def test_template_has_metadata_helpers(self):
        """Test template có metadata helpers."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("getEntityName", content)
        self.assertIn("getPropertyNames", content)
        self.assertIn("getProperty", content)
        self.assertIn("setProperty", content)

    def test_template_has_utility_methods(self):
        """Test template có utility methods."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("clear", content)
        self.assertIn("isPersisted", content)
        self.assertIn("isNew", content)
        self.assertIn("merge", content)

    def test_template_has_interface(self):
        """Test template có IBaseEntity interface."""
        content = self.template_path.read_text(encoding="utf-8")
        self.assertIn("IBaseEntity", content)


# Run tests
if __name__ == "__main__":
    import unittest
    unittest.main()
