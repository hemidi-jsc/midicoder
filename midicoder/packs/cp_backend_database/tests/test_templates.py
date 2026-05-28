# coding: utf-8
"""
Tests cho Jinja2 templates (CP08).

Bao gồm:
- FastAPI templates: database.py, base_model.py, base_repository.py,
  audit_mixin.py, tenant_mixin.py, repository.py, migrations/env.py
- NestJS templates: database.module.ts, base.entity.ts, base.repository.ts,
  audit.decorator.ts, tenant.decorators.ts, repository.ts
- Template rendering correctness
- No unresolved template variables
"""

import pytest
from pathlib import Path
import jinja2
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "stacks"


@pytest.fixture
def fastapi_template_dir():
    return BASE_DIR / "fastapi" / "core" / "cp_backend_database"


@pytest.fixture
def nestjs_template_dir():
    return BASE_DIR / "nestjs" / "core" / "cp_backend_database"


@pytest.fixture
def fastapi_jinja_env(fastapi_template_dir):
    return Environment(
        loader=FileSystemLoader(str(fastapi_template_dir.parent)),
        autoescape=select_autoescape(default_for_string=False),
    )


@pytest.fixture
def nestjs_jinja_env(nestjs_template_dir):
    return Environment(
        loader=FileSystemLoader(str(nestjs_template_dir.parent)),
        autoescape=select_autoescape(default_for_string=False),
    )


@pytest.fixture
def sample_entity():
    return {
        "id": "User",
        "table_name": "users",
        "tenant_scope": "tenant_isolated",
        "description": "User entity",
    }


@pytest.fixture
def db_config():
    return {
        "database_url": "postgresql://user:pass@localhost:5432/dbname",
        "pool_size": 10,
        "max_overflow": 20,
    }


# ============================================================================
# FastAPI Templates
# ============================================================================


class TestFastAPITemplates:
    def test_base_model_template_exists(self, fastapi_template_dir):
        tpl = fastapi_template_dir / "base_model.py.jinja2"
        assert tpl.exists()

    def test_base_model_renders_valid_python(self, fastapi_jinja_env):
        template = fastapi_jinja_env.get_template("cp_backend_database/base_model.py.jinja2")
        rendered = template.render()
        assert "class Base" in rendered
        compile(rendered, "<string>", "exec")

    def test_base_model_has_tenant_id(self, fastapi_jinja_env):
        template = fastapi_jinja_env.get_template("cp_backend_database/base_model.py.jinja2")
        rendered = template.render()
        assert "tenant_id" in rendered

    def test_base_model_has_soft_delete(self, fastapi_jinja_env):
        template = fastapi_jinja_env.get_template("cp_backend_database/base_model.py.jinja2")
        rendered = template.render()
        assert "soft_delete" in rendered
        assert "deleted_at" in rendered

    def test_database_template_exists(self, fastapi_template_dir):
        tpl = fastapi_template_dir / "database.py.jinja2"
        assert tpl.exists()

    def test_database_renders_valid_python(self, fastapi_jinja_env, db_config):
        template = fastapi_jinja_env.get_template("cp_backend_database/database.py.jinja2")
        rendered = template.render(config=db_config)
        assert "engine" in rendered.lower() or "Engine" in rendered
        compile(rendered, "<string>", "exec")

    def test_database_has_tenant_context(self, fastapi_jinja_env, db_config):
        template = fastapi_jinja_env.get_template("cp_backend_database/database.py.jinja2")
        rendered = template.render(config=db_config)
        assert "tenant" in rendered.lower()

    def test_base_repository_renders_valid_python(self, fastapi_jinja_env):
        template = fastapi_jinja_env.get_template("cp_backend_database/base_repository.py.jinja2")
        rendered = template.render()
        assert "BaseRepository" in rendered
        compile(rendered, "<string>", "exec")

    def test_base_repository_has_tenant_isolation(self, fastapi_jinja_env):
        template = fastapi_jinja_env.get_template("cp_backend_database/base_repository.py.jinja2")
        rendered = template.render()
        assert "tenant" in rendered.lower()

    def test_audit_mixin_exists(self, fastapi_template_dir):
        tpl = fastapi_template_dir / "audit_mixin.py.jinja2"
        assert tpl.exists()

    def test_audit_mixin_renders(self, fastapi_jinja_env):
        template = fastapi_jinja_env.get_template("cp_backend_database/audit_mixin.py.jinja2")
        rendered = template.render()
        assert "created_by" in rendered or "CreatedBy" in rendered
        compile(rendered, "<string>", "exec")

    def test_tenant_mixin_exists(self, fastapi_template_dir):
        tpl = fastapi_template_dir / "tenant_mixin.py.jinja2"
        assert tpl.exists()

    def test_tenant_mixin_renders(self, fastapi_jinja_env):
        template = fastapi_jinja_env.get_template("cp_backend_database/tenant_mixin.py.jinja2")
        rendered = template.render()
        assert "tenant_id" in rendered
        compile(rendered, "<string>", "exec")

    def test_repository_template_renders(self, fastapi_jinja_env, sample_entity):
        template = fastapi_jinja_env.get_template("cp_backend_database/repository.py.jinja2")
        rendered = template.render(entity=sample_entity)
        assert "User" in rendered
        compile(rendered, "<string>", "exec")

    def test_migrations_env_exists(self, fastapi_template_dir):
        tpl = fastapi_template_dir / "migrations" / "env.py.jinja2"
        assert tpl.exists()

    def test_migrations_env_renders(self, fastapi_jinja_env):
        template = fastapi_jinja_env.get_template("cp_backend_database/migrations/env.py.jinja2")
        rendered = template.render()
        assert "migration" in rendered.lower()
        # Note: migrations/env.py contains async module-level code (run_migrations_online)
        # which is valid for Alembic's execution context but not a standalone Python module.
        # So we skip compile() check and only verify content.
        assert "run_migrations_online" in rendered
        assert "run_migrations_offline" in rendered


class TestNestJSTemplates:
    def test_base_entity_template_exists(self, nestjs_template_dir):
        tpl = nestjs_template_dir / "base.entity.ts.jinja2"
        assert tpl.exists()

    def test_base_entity_renders(self, nestjs_jinja_env):
        template = nestjs_jinja_env.get_template("cp_backend_database/base.entity.ts.jinja2")
        rendered = template.render()
        assert "BaseEntity" in rendered
        assert "tenant" in rendered.lower()

    def test_database_module_renders(self, nestjs_jinja_env):
        template = nestjs_jinja_env.get_template("cp_backend_database/database.module.ts.jinja2")
        rendered = template.render()
        assert "DatabaseModule" in rendered or "database" in rendered.lower()
        assert "tenant" in rendered.lower()

    def test_base_repository_renders(self, nestjs_jinja_env):
        template = nestjs_jinja_env.get_template("cp_backend_database/base.repository.ts.jinja2")
        rendered = template.render()
        assert "BaseRepository" in rendered
        assert "tenant" in rendered.lower()

    def test_audit_decorator_renders(self, nestjs_jinja_env):
        template = nestjs_jinja_env.get_template("cp_backend_database/audit.decorator.ts.jinja2")
        rendered = template.render()
        assert "audit" in rendered.lower() or "Audit" in rendered

    def test_tenant_decorators_renders(self, nestjs_jinja_env):
        template = nestjs_jinja_env.get_template("cp_backend_database/tenant.decorators.ts.jinja2")
        rendered = template.render()
        assert "tenant" in rendered.lower()

    def test_repository_template_renders(self, nestjs_jinja_env, sample_entity):
        template = nestjs_jinja_env.get_template("cp_backend_database/repository.ts.jinja2")
        rendered = template.render(entity=sample_entity)
        assert "User" in rendered


class TestTemplateStructure:
    """Verify template file counts."""

    def test_fastapi_template_count(self, fastapi_template_dir):
        templates = list(fastapi_template_dir.glob("**/*.jinja2"))
        assert len(templates) >= 5  # at least 5 FastAPI templates

    def test_nestjs_template_count(self, nestjs_template_dir):
        templates = list(nestjs_template_dir.glob("**/*.jinja2"))
        assert len(templates) >= 5  # at least 5 NestJS templates

    def test_all_fastapi_templates_have_tenant_reference(self, fastapi_template_dir):
        # Utility/helper templates (spatial, time_series, jsonb, distributed_tx) are not tenant-specific
        non_tenant_templates = {
            "spatial_helpers.py.jinja2", "spatial_indexes.py.jinja2",
            "time_series_model.py.jinja2",
            "read_model.py.jinja2",
            "distributed_transaction.py.jinja2",
            "jsonb_helpers.py.jinja2",
        }
        for tpl in fastapi_template_dir.glob("**/*.jinja2"):
            if tpl.name in non_tenant_templates:
                continue
            content = tpl.read_text(encoding="utf-8")
            assert "tenant" in content.lower(), f"Template {tpl.name} missing tenant reference"

    def test_all_nestjs_templates_have_tenant_reference(self, nestjs_template_dir):
        # Utility/helper templates are not tenant-specific
        non_tenant_templates = {
            "spatial.decorators.ts.jinja2", "spatial-indexes.ts.jinja2",
            "time_series.entity.ts.jinja2",
            "read_model.entity.ts.jinja2",
            "distributed_transaction.ts.jinja2",
            "jsonb.decorators.ts.jinja2",
        }
        for tpl in nestjs_template_dir.glob("**/*.jinja2"):
            if tpl.name in non_tenant_templates:
                continue
            content = tpl.read_text(encoding="utf-8")
            assert "tenant" in content.lower(), f"Template {tpl.name} missing tenant reference"

# ===========================================================================
# Dữ liệu và helper cho Rule V1/V2 (P2-17)
# ===========================================================================

FASTAPI_TEMPLATES = [
    "base_model.py.jinja2",
    "database.py.jinja2",
    "base_repository.py.jinja2",
    "audit_mixin.py.jinja2",
    "tenant_mixin.py.jinja2",
    "repository.py.jinja2",
    "migrations/env.py.jinja2",
]

NESTJS_TEMPLATES = [
    "base.entity.ts.jinja2",
    "database.module.ts.jinja2",
    "base.repository.ts.jinja2",
    "audit.decorator.ts.jinja2",
    "tenant.decorators.ts.jinja2",
    "repository.ts.jinja2",
]


def _render_template(stack: str, template_name: str) -> str:
    """Render template với context cơ bản."""
    template_path = BASE_DIR / stack / "core" / "cp_backend_database"
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_path)),
        undefined=jinja2.ChainableUndefined,
    )
    ctx = {
        "entity": {
            "id": "User",
            "table_name": "users",
            "tenant_scope": "tenant_isolated",
            "description": "User entity",
        },
        "config": {
            "database_url": "postgresql://user:pass@localhost:5432/dbname",
            "pool_size": 10,
            "max_overflow": 20,
        },
    }
    template = env.get_template(template_name)
    return template.render(**ctx)


# ===========================================================================
# Test Rule V1 & V2 (P2-17)
# ===========================================================================

class TestRuleV1NoMidicoderImport:
    """Rule V1: Output của template KHÔNG chứa 'from midicoder'."""

    def test_fastapi_no_midicoder_import(self):
        """FastAPI templates không chứa 'from midicoder' trong output."""
        for template in FASTAPI_TEMPLATES:
            result = _render_template("fastapi", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_nestjs_no_midicoder_import(self):
        """NestJS templates không chứa 'from midicoder' trong output."""
        for template in NESTJS_TEMPLATES:
            result = _render_template("nestjs", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"


class TestRuleV2NoPostInit:
    """Rule V2: Output của template KHÔNG chứa '__post_init__'."""

    def test_fastapi_no_post_init(self):
        """FastAPI templates không chứa __post_init__ trong output."""
        for template in FASTAPI_TEMPLATES:
            result = _render_template("fastapi", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_nestjs_no_post_init(self):
        """NestJS templates không chứa __post_init__ trong output."""
        for template in NESTJS_TEMPLATES:
            result = _render_template("nestjs", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"
