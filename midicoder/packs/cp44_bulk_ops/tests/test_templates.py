# coding: utf-8
"""
Test templates và pack manifest cho CP44 — Bulk Operations Engine.

Test:
- pack.yml tồn tại và hợp lệ
- Templates tồn tại cho 4 stacks
- CHANGELOG.md tồn tại
- Registry entry cho CP44
"""

import pytest
from pathlib import Path
import yaml
import jinja2


# Đường dẫn project root
# __file__ = .../midicoder/packs/cp44_bulk_ops/tests/test_templates.py
# parent x6 = midicoder-ce/
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
EMITTERS_DIR = PROJECT_ROOT / "midicoder" / "emitters" / "core" / "cp44_bulk_ops"
STACKS_DIR = PROJECT_ROOT / "midicoder" / "stacks"


class TestPackManifest:
    """Test pack.yml manifest."""

    def test_pack_yml_exists(self):
        """pack.yml tồn tại."""
        assert (EMITTERS_DIR / "pack.yml").exists()

    def test_pack_yml_valid_yaml(self):
        """pack.yml là YAML hợp lệ."""
        with open(EMITTERS_DIR / "pack.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert "pack" in data

    def test_pack_id(self):
        """Pack ID là CP44."""
        with open(EMITTERS_DIR / "pack.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["id"] == "CP44"

    def test_pack_internal_id(self):
        """Internal ID đúng."""
        with open(EMITTERS_DIR / "pack.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["internal_id"] == "cp44_bulk_ops"

    def test_pack_capabilities(self):
        """Capabilities đúng."""
        with open(EMITTERS_DIR / "pack.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        caps = data["pack"]["capabilities_provided"]
        assert "batch_process" in caps
        assert "bulk_update" in caps
        assert "parallel_process" in caps
        assert "chunk_process" in caps

    def test_pack_obligations(self):
        """Obligations có TenantIsolation và AuditTrail."""
        with open(EMITTERS_DIR / "pack.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        obligations = data["pack"]["obligations"]
        names = [o["name"] for o in obligations]
        assert "TenantIsolation" in names
        assert "AuditTrail" in names

    def test_pack_depends_on(self):
        """Depends on CP01, CP13, CP14."""
        with open(EMITTERS_DIR / "pack.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        deps = data["pack"]["depends_on"]
        assert "CP01" in deps
        assert "CP13" in deps
        assert "CP14" in deps

    def test_pack_file_contributions_count(self):
        """Có file contributions cho 4 stacks."""
        with open(EMITTERS_DIR / "pack.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        contributions = data["pack"]["file_contributions"]["infrastructure"]
        assert len(contributions) >= 20  # 7+7+6+5 = 25

    def test_pack_recipes(self):
        """Recipes đúng."""
        with open(EMITTERS_DIR / "pack.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        recipes = data["pack"]["recipes"]
        assert "basic_bulk_recipe" in recipes
        assert "full_bulk_recipe" in recipes


class TestFastAPITemplates:
    """Test FastAPI templates tồn tại."""

    expected_templates = [
        "bulk_models.py.jinja2",
        "bulk_schemas.py.jinja2",
        "bulk_service.py.jinja2",
        "bulk_router.py.jinja2",
        "bulk_worker.py.jinja2",
        "bulk_dlq_worker.py.jinja2",
        "bulk_sse.py.jinja2",
    ]

    def test_all_templates_exist(self):
        """Tất cả FastAPI templates tồn tại."""
        stack_dir = STACKS_DIR / "fastapi" / "core" / "cp44_bulk_ops"
        for template in self.expected_templates:
            assert (stack_dir / template).exists(), f"Thiếu template: {template}"

    def test_template_not_empty(self):
        """Templates không rỗng."""
        stack_dir = STACKS_DIR / "fastapi" / "core" / "cp44_bulk_ops"
        for template in self.expected_templates:
            size = (stack_dir / template).stat().st_size
            assert size > 0, f"Template rỗng: {template}"


class TestNestJSTemplates:
    """Test NestJS templates tồn tại."""

    expected_templates = [
        "bulk.entity.ts.jinja2",
        "bulk.dto.ts.jinja2",
        "bulk.service.ts.jinja2",
        "bulk.controller.ts.jinja2",
        "bulk.module.ts.jinja2",
        "bulk.scheduler.ts.jinja2",
        "bulk.gateway.ts.jinja2",
    ]

    def test_all_templates_exist(self):
        """Tất cả NestJS templates tồn tại."""
        stack_dir = STACKS_DIR / "nestjs" / "core" / "cp44_bulk_ops"
        for template in self.expected_templates:
            assert (stack_dir / template).exists(), f"Thiếu template: {template}"

    def test_template_not_empty(self):
        stack_dir = STACKS_DIR / "nestjs" / "core" / "cp44_bulk_ops"
        for template in self.expected_templates:
            size = (stack_dir / template).stat().st_size
            assert size > 0, f"Template rỗng: {template}"


class TestAngularTemplates:
    """Test Angular templates tồn tại."""

    expected_templates = [
        "bulk-dashboard.component.ts.jinja2",
        "bulk-jobs.component.ts.jinja2",
        "bulk-job-details.component.ts.jinja2",
        "bulk.service.ts.jinja2",
        "bulk.store.ts.jinja2",
        "bulk-types.ts.jinja2",
    ]

    def test_all_templates_exist(self):
        """Tất cả Angular templates tồn tại."""
        stack_dir = STACKS_DIR / "angular" / "core" / "cp44_bulk_ops"
        for template in self.expected_templates:
            assert (stack_dir / template).exists(), f"Thiếu template: {template}"

    def test_template_not_empty(self):
        stack_dir = STACKS_DIR / "angular" / "core" / "cp44_bulk_ops"
        for template in self.expected_templates:
            size = (stack_dir / template).stat().st_size
            assert size > 0, f"Template rỗng: {template}"


class TestReactTemplates:
    """Test React templates tồn tại."""

    expected_templates = [
        "BulkDashboard.tsx.jinja2",
        "BulkJobs.tsx.jinja2",
        "BulkJobDetails.tsx.jinja2",
        "BulkProgress.tsx.jinja2",
        "useBulkOps.ts.jinja2",
    ]

    def test_all_templates_exist(self):
        """Tất cả React templates tồn tại."""
        stack_dir = STACKS_DIR / "react" / "core" / "cp44_bulk_ops"
        for template in self.expected_templates:
            assert (stack_dir / template).exists(), f"Thiếu template: {template}"

    def test_template_not_empty(self):
        stack_dir = STACKS_DIR / "react" / "core" / "cp44_bulk_ops"
        for template in self.expected_templates:
            size = (stack_dir / template).stat().st_size
            assert size > 0, f"Template rỗng: {template}"


class TestChangelog:
    """Test CHANGELOG.md."""

    def test_changelog_exists(self):
        """CHANGELOG.md tồn tại."""
        assert (EMITTERS_DIR / "CHANGELOG.md").exists()

    def test_changelog_has_version(self):
        """CHANGELOG có version 1.0.0."""
        content = (EMITTERS_DIR / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "1.0.0" in content


class TestRegistry:
    """Test registry entry cho CP44."""

    def test_cp44_in_registry(self):
        """CP44 có trong registry."""
        from midicoder.contracts.registry import CP_ID_TO_INTERNAL
        assert "CP44" in CP_ID_TO_INTERNAL
        assert CP_ID_TO_INTERNAL["CP44"] == "cp44_bulk_ops"


class TestInitModule:
    """Test __init__.py barrel exports."""

    def test_init_exists(self):
        """__init__.py tồn tại."""
        assert (EMITTERS_DIR / "__init__.py").exists()

    def test_init_exports_models(self):
        """__init__.py export models."""
        from midicoder.packs.cp44_bulk_ops import (
            BulkAction,
            BulkJob,
            BulkEngine,
            JobStatus,
        )
        assert BulkAction is not None
        assert BulkJob is not None
        assert BulkEngine is not None
        assert JobStatus is not None

    def test_init_exports_parser(self):
        """__init__.py export parser."""
        from midicoder.packs.cp44_bulk_ops import (
            BulkIR,
            parse_to_ir,
        )
        assert BulkIR is not None
        assert parse_to_ir is not None

    def test_init_exports_recipes(self):
        """__init__.py export recipes."""
        from midicoder.packs.cp44_bulk_ops import (
            basic_bulk_recipe,
            full_bulk_recipe,
        )
        assert basic_bulk_recipe is not None
        assert full_bulk_recipe is not None


# ============================================================================
# Helper — render template với context cơ bản
# ============================================================================

CP44_STACK_NAMES = ["fastapi", "nestjs", "angular", "react"]

ALL_TEMPLATES = {
    "fastapi": [
        "bulk_models.py.jinja2",
        "bulk_schemas.py.jinja2",
        "bulk_service.py.jinja2",
        "bulk_router.py.jinja2",
        "bulk_worker.py.jinja2",
        "bulk_dlq_worker.py.jinja2",
        "bulk_sse.py.jinja2",
    ],
    "nestjs": [
        "bulk.entity.ts.jinja2",
        "bulk.dto.ts.jinja2",
        "bulk.service.ts.jinja2",
        "bulk.controller.ts.jinja2",
        "bulk.module.ts.jinja2",
        "bulk.scheduler.ts.jinja2",
        "bulk.gateway.ts.jinja2",
    ],
    "angular": [
        "bulk-dashboard.component.ts.jinja2",
        "bulk-jobs.component.ts.jinja2",
        "bulk-job-details.component.ts.jinja2",
        "bulk.service.ts.jinja2",
        "bulk.store.ts.jinja2",
        "bulk-types.ts.jinja2",
    ],
    "react": [
        "BulkDashboard.tsx.jinja2",
        "BulkJobs.tsx.jinja2",
        "BulkJobDetails.tsx.jinja2",
        "BulkProgress.tsx.jinja2",
        "useBulkOps.ts.jinja2",
    ],
}


def _render_template(stack: str, template_name: str) -> str:
    """Render template với context cơ bản để kiểm tra Rule V1/V2.

    Nếu render thất bại (thiếu biến context hoặc lỗi cú pháp), trả về nội dung
    thô của template để vẫn có thể kiểm tra Rule V1/V2.
    """
    template_dir = STACKS_DIR / stack / "core" / "cp44_bulk_ops"
    template_path = template_dir / template_name
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_dir)),
        undefined=jinja2.ChainableUndefined,
    )
    ctx = {
        "project_name": "test_project",
        "module_name": "test_module",
        "entity_name": "Bulk",
        "model_name": "BulkJob",
        "service_name": "BulkService",
        "use_events": True,
        "use_audit": True,
        "job_count": 100,
        "default_chunk_size": 100,
        "default_concurrency": 5,
        "default_max_retries": 3,
        "default_retry_strategy": "exponential_backoff",
        "default_timeout": 3600,
        "dlq_enabled": True,
    }
    try:
        template = env.get_template(template_name)
        return template.render(**ctx)
    except Exception:
        # Render thất bại: trả về nội dung thô để kiểm tra Rule V1/V2
        return template_path.read_text(encoding="utf-8")


# ============================================================================
# TestRuleV1NoMidicoderImport — kiểm tra rendered output không có `from midicoder`
# ============================================================================


class TestRuleV1NoMidicoderImport:
    """Rule V1: rendered output của template không được chứa 'from midicoder'."""

    @pytest.mark.parametrize("stack", CP44_STACK_NAMES)
    def test_rendered_no_midicoder_import(self, stack: str):
        """Mỗi template render ra không chứa 'from midicoder'."""
        for template_name in ALL_TEMPLATES[stack]:
            output = _render_template(stack, template_name)
            assert "from midicoder" not in output, (
                f"Rule V1 vi phạm: {stack}/{template_name} chứa 'from midicoder' trong rendered output"
            )


# ============================================================================
# TestRuleV2NoPostInit — kiểm tra rendered output không có `__post_init__`
# ============================================================================


class TestRuleV2NoPostInit:
    """Rule V2: rendered output của template không được chứa '__post_init__'."""

    @pytest.mark.parametrize("stack", CP44_STACK_NAMES)
    def test_rendered_no_post_init(self, stack: str):
        """Mỗi template render ra không chứa '__post_init__'."""
        for template_name in ALL_TEMPLATES[stack]:
            output = _render_template(stack, template_name)
            assert "__post_init__" not in output, (
                f"Rule V2 vi phạm: {stack}/{template_name} chứa '__post_init__' trong rendered output"
            )
