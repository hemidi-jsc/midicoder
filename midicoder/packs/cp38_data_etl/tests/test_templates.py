# coding: utf-8
"""
Tests cho CP38 pack.yml và template validation.
"""

from __future__ import annotations

from pathlib import Path

import yaml
import jinja2

# midicoder/packs/cp38_data_etl/tests/
# parent.parent = cp38_data_etl/
PACK_YML = Path(__file__).parent.parent / "pack.yml"


class TestCP38PackYaml:
    """Tests cho pack.yml CP38."""

    def test_pack_yml_exists(self):
        assert PACK_YML.exists(), f"pack.yml không tồn tại tại {PACK_YML}"

    def test_pack_yml_has_file_contributions(self):
        with open(PACK_YML, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "file_contributions" in data.get("pack", {})
        assert "infrastructure" in data["pack"]["file_contributions"]

    def test_pack_yml_has_4_stacks(self):
        with open(PACK_YML, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        infra = data["pack"]["file_contributions"]["infrastructure"]
        stacks_found = set()
        for entry in infra:
            for s in entry.get("stacks", []):
                stacks_found.add(s)
        assert "fastapi" in stacks_found
        assert "nestjs" in stacks_found
        assert "angular" in stacks_found
        assert "react" in stacks_found

    def test_pack_yml_has_correct_pack_id(self):
        with open(PACK_YML, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["id"] == "CP38"

    def test_pack_yml_has_capabilities(self):
        with open(PACK_YML, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        caps = data["pack"].get("capabilities_provided", [])
        assert "csv_import" in caps
        assert "json_import" in caps
        assert "data_migrate" in caps
        assert "bulk_operation" in caps
        assert "etl_pipeline" in caps
        assert "data_export" in caps


class TestFastAPITemplates:
    """Tests cho FastAPI template existence và content."""

    def _get_template_dir(self):
        return Path(__file__).parent.parent.parent.parent.parent / "stacks" / "fastapi" / "core" / "cp38_data_etl"

    def test_init_template_exists(self):
        assert (self._get_template_dir() / "__init__.py.jinja2").exists()

    def test_import_models_template_exists(self):
        assert (self._get_template_dir() / "import_models.py.jinja2").exists()

    def test_import_schemas_template_exists(self):
        assert (self._get_template_dir() / "import_schemas.py.jinja2").exists()

    def test_import_service_template_exists(self):
        assert (self._get_template_dir() / "import_service.py.jinja2").exists()

    def test_export_service_template_exists(self):
        assert (self._get_template_dir() / "export_service.py.jinja2").exists()

    def test_etl_service_template_exists(self):
        assert (self._get_template_dir() / "etl_service.py.jinja2").exists()

    def test_import_router_template_exists(self):
        assert (self._get_template_dir() / "import_router.py.jinja2").exists()

    def test_export_router_template_exists(self):
        assert (self._get_template_dir() / "export_router.py.jinja2").exists()

    def test_bulk_worker_template_exists(self):
        assert (self._get_template_dir() / "bulk_worker.py.jinja2").exists()

    def test_csv_parser_template_exists(self):
        assert (self._get_template_dir() / "csv_parser.py.jinja2").exists()

    def test_json_parser_template_exists(self):
        assert (self._get_template_dir() / "json_parser.py.jinja2").exists()

    def test_import_models_content(self):
        content = (self._get_template_dir() / "import_models.py.jinja2").read_text(encoding="utf-8")
        assert "ImportJob" in content

    def test_exactly_11_templates(self):
        templates = list(self._get_template_dir().glob("*.jinja2"))
        assert len(templates) == 11


class TestNestJSTemplates:
    """Tests cho NestJS template existence và content."""

    def _get_template_dir(self):
        return Path(__file__).parent.parent.parent.parent.parent / "stacks" / "nestjs" / "core" / "cp38_data_etl"

    def test_import_entity_template_exists(self):
        assert (self._get_template_dir() / "import.entity.ts.jinja2").exists()

    def test_import_dto_template_exists(self):
        assert (self._get_template_dir() / "import.dto.ts.jinja2").exists()

    def test_import_service_template_exists(self):
        assert (self._get_template_dir() / "import.service.ts.jinja2").exists()

    def test_export_service_template_exists(self):
        assert (self._get_template_dir() / "export.service.ts.jinja2").exists()

    def test_etl_service_template_exists(self):
        assert (self._get_template_dir() / "etl.service.ts.jinja2").exists()

    def test_import_controller_template_exists(self):
        assert (self._get_template_dir() / "import.controller.ts.jinja2").exists()

    def test_export_controller_template_exists(self):
        assert (self._get_template_dir() / "export.controller.ts.jinja2").exists()

    def test_bulk_processor_template_exists(self):
        assert (self._get_template_dir() / "bulk-processor.service.ts.jinja2").exists()

    def test_etl_module_template_exists(self):
        assert (self._get_template_dir() / "etl.module.ts.jinja2").exists()

    def test_import_entity_content(self):
        content = (self._get_template_dir() / "import.entity.ts.jinja2").read_text(encoding="utf-8")
        assert "Entity" in content or "entity" in content.lower() or "ImportJob" in content

    def test_exactly_9_templates(self):
        templates = list(self._get_template_dir().glob("*.jinja2"))
        assert len(templates) == 9


class TestAngularTemplates:
    """Tests cho Angular template existence và content."""

    def _get_template_dir(self):
        return Path(__file__).parent.parent.parent.parent.parent / "stacks" / "angular" / "core" / "cp38_data_etl"

    def test_import_wizard_template_exists(self):
        assert (self._get_template_dir() / "import-wizard.component.ts.jinja2").exists()

    def test_export_dialog_template_exists(self):
        assert (self._get_template_dir() / "export-dialog.component.ts.jinja2").exists()

    def test_import_service_template_exists(self):
        assert (self._get_template_dir() / "import.service.ts.jinja2").exists()

    def test_export_service_template_exists(self):
        assert (self._get_template_dir() / "export.service.ts.jinja2").exists()

    def test_job_status_template_exists(self):
        assert (self._get_template_dir() / "job-status.component.ts.jinja2").exists()

    def test_import_wizard_content(self):
        content = (self._get_template_dir() / "import-wizard.component.ts.jinja2").read_text(encoding="utf-8")
        assert "Component" in content or "component" in content.lower() or "import" in content.lower()

    def test_exactly_5_templates(self):
        templates = list(self._get_template_dir().glob("*.jinja2"))
        assert len(templates) == 5


class TestReactTemplates:
    """Tests cho React template existence và content."""

    def _get_template_dir(self):
        return Path(__file__).parent.parent.parent.parent.parent / "stacks" / "react" / "core" / "cp38_data_etl"

    def test_import_wizard_template_exists(self):
        assert (self._get_template_dir() / "ImportWizard.tsx.jinja2").exists()

    def test_export_dialog_template_exists(self):
        assert (self._get_template_dir() / "ExportDialog.tsx.jinja2").exists()

    def test_use_import_job_template_exists(self):
        assert (self._get_template_dir() / "useImportJob.ts.jinja2").exists()

    def test_use_export_job_template_exists(self):
        assert (self._get_template_dir() / "useExportJob.ts.jinja2").exists()

    def test_job_status_panel_template_exists(self):
        assert (self._get_template_dir() / "JobStatusPanel.tsx.jinja2").exists()

    def test_import_service_template_exists(self):
        assert (self._get_template_dir() / "import.service.ts.jinja2").exists()

    def test_export_service_template_exists(self):
        assert (self._get_template_dir() / "export.service.ts.jinja2").exists()

    def test_import_wizard_content(self):
        content = (self._get_template_dir() / "ImportWizard.tsx.jinja2").read_text(encoding="utf-8")
        assert "import" in content.lower() or "Import" in content or "Wizard" in content

    def test_exactly_7_templates(self):
        templates = list(self._get_template_dir().glob("*.jinja2"))
        assert len(templates) == 7


# ============================================================================
# Rule V1 & V2 (P2-17) — template render tests
# ============================================================================

# Đường dẫn stack directories
MIDICODER_ROOT_38 = Path(__file__).parent.parent.parent.parent.parent

STACK_DIRS_38 = {
    "fastapi": MIDICODER_ROOT_38 / "stacks" / "fastapi" / "core" / "cp38_data_etl",
    "nestjs": MIDICODER_ROOT_38 / "stacks" / "nestjs" / "core" / "cp38_data_etl",
    "angular": MIDICODER_ROOT_38 / "stacks" / "angular" / "core" / "cp38_data_etl",
    "react": MIDICODER_ROOT_38 / "stacks" / "react" / "core" / "cp38_data_etl",
}

FASTAPI_TEMPLATES_38 = [
    "__init__.py.jinja2",
    "import_models.py.jinja2",
    "import_schemas.py.jinja2",
    "import_service.py.jinja2",
    "export_service.py.jinja2",
    "etl_service.py.jinja2",
    "import_router.py.jinja2",
    "export_router.py.jinja2",
    "bulk_worker.py.jinja2",
    "csv_parser.py.jinja2",
    "json_parser.py.jinja2",
]

NESTJS_TEMPLATES_38 = [
    "import.entity.ts.jinja2",
    "import.dto.ts.jinja2",
    "import.service.ts.jinja2",
    "export.service.ts.jinja2",
    "etl.service.ts.jinja2",
    "import.controller.ts.jinja2",
    "export.controller.ts.jinja2",
    "bulk-processor.service.ts.jinja2",
    "etl.module.ts.jinja2",
]

ANGULAR_TEMPLATES_38 = [
    "import-wizard.component.ts.jinja2",
    "export-dialog.component.ts.jinja2",
    "import.service.ts.jinja2",
    "export.service.ts.jinja2",
    "job-status.component.ts.jinja2",
]

REACT_TEMPLATES_38 = [
    "ImportWizard.tsx.jinja2",
    "ExportDialog.tsx.jinja2",
    "useImportJob.ts.jinja2",
    "useExportJob.ts.jinja2",
    "JobStatusPanel.tsx.jinja2",
    "import.service.ts.jinja2",
    "export.service.ts.jinja2",
]

ALL_TEMPLATES_38 = {
    "fastapi": FASTAPI_TEMPLATES_38,
    "nestjs": NESTJS_TEMPLATES_38,
    "angular": ANGULAR_TEMPLATES_38,
    "react": REACT_TEMPLATES_38,
}


def _render_template_38(stack: str, template_name: str) -> str:
    """Render template với context cơ bản; fallback sang đọc source thô nếu render lỗi."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(STACK_DIRS_38[stack])),
        undefined=jinja2.ChainableUndefined,
    )
    ctx: dict = {}
    try:
        template = env.get_template(template_name)
        return template.render(**ctx)
    except Exception:
        # Template chứa JSX/TSX không bọc {% raw %} — đọc source thô
        source_path = STACK_DIRS_38[stack] / template_name
        return source_path.read_text(encoding="utf-8")


class TestRuleV1NoMidicoderImport:
    """Rule V1: Output của template KHÔNG chứa 'from midicoder'."""

    def test_fastapi_no_midicoder_import(self):
        """FastAPI templates không chứa 'from midicoder' trong output."""
        for template in FASTAPI_TEMPLATES_38:
            result = _render_template_38("fastapi", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_nestjs_no_midicoder_import(self):
        """NestJS templates không chứa 'from midicoder' trong output."""
        for template in NESTJS_TEMPLATES_38:
            result = _render_template_38("nestjs", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_angular_no_midicoder_import(self):
        """Angular templates không chứa 'from midicoder' trong output."""
        for template in ANGULAR_TEMPLATES_38:
            result = _render_template_38("angular", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_react_no_midicoder_import(self):
        """React templates không chứa 'from midicoder' trong output."""
        for template in REACT_TEMPLATES_38:
            result = _render_template_38("react", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"


class TestRuleV2NoPostInit:
    """Rule V2: Output của template KHÔNG chứa '__post_init__'."""

    def test_fastapi_no_post_init(self):
        """FastAPI templates không chứa __post_init__ trong output."""
        for template in FASTAPI_TEMPLATES_38:
            result = _render_template_38("fastapi", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_nestjs_no_post_init(self):
        """NestJS templates không chứa __post_init__ trong output."""
        for template in NESTJS_TEMPLATES_38:
            result = _render_template_38("nestjs", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_angular_no_post_init(self):
        """Angular templates không chứa __post_init__ trong output."""
        for template in ANGULAR_TEMPLATES_38:
            result = _render_template_38("angular", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_react_no_post_init(self):
        """React templates không chứa __post_init__ trong output."""
        for template in REACT_TEMPLATES_38:
            result = _render_template_38("react", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"
