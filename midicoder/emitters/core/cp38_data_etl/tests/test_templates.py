# coding: utf-8
"""
Tests cho CP38 pack.yml và template validation.
"""

from __future__ import annotations

from pathlib import Path

import yaml

# midicoder/emitters/core/cp38_data_etl/tests/
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
