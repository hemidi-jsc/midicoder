# coding: utf-8
"""
Tests cho CP47 emitters — Data Retention & Lifecycle Management.
"""

from __future__ import annotations

import pytest
from pathlib import Path
import yaml

from midicoder.packs.cp_full_data_lifecycle.parser import parse_to_ir, RetentionIR

PACK_DIR = Path(__file__).resolve().parent.parent
PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent


class TestFastAPIEmitter:
    @pytest.fixture
    def emitter(self):
        from midicoder.packs.cp_full_data_lifecycle.fastapi import FastAPIRetentionEmitter
        stacks_dir = PACKAGE_DIR / "stacks"
        return FastAPIRetentionEmitter(stacks_dir / "fastapi" / "core")

    @pytest.fixture
    def ir(self):
        return parse_to_ir({
            "policies": [
                {"policy_id": "default", "entity_type": "Order", "retention_days": 365, "action": "archive"},
            ],
            "enable_archival": True,
            "enable_purge": True,
            "enable_erasure": True,
        })

    def test_emit_returns_files(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        assert len(files) > 0

    def test_emit_template_count(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        assert len(files) == 6

    def test_emit_has_models(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        paths = [f.path for f in files]
        assert any("retention_models" in p for p in paths)

    def test_emit_has_service(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        paths = [f.path for f in files]
        assert any("retention_service" in p for p in paths)

    def test_invalid_dir_raises_error(self):
        from midicoder.packs.cp_full_data_lifecycle.fastapi import FastAPIRetentionEmitter
        from midicoder.errors import MidicoderError
        with pytest.raises(MidicoderError):
            FastAPIRetentionEmitter("/nonexistent/path")


class TestNestJSEmitter:
    @pytest.fixture
    def emitter(self):
        from midicoder.packs.cp_full_data_lifecycle.nestjs import NestJSRetentionEmitter
        stacks_dir = PACKAGE_DIR / "stacks"
        return NestJSRetentionEmitter(stacks_dir / "nestjs" / "core")

    @pytest.fixture
    def ir(self):
        return parse_to_ir({
            "policies": [
                {"policy_id": "default", "entity_type": "Order", "retention_days": 365, "action": "archive"},
            ],
        })

    def test_emit_returns_files(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        assert len(files) > 0

    def test_emit_template_count(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        assert len(files) == 6

    def test_invalid_dir_raises_error(self):
        from midicoder.packs.cp_full_data_lifecycle.nestjs import NestJSRetentionEmitter
        from midicoder.errors import MidicoderError
        with pytest.raises(MidicoderError):
            NestJSRetentionEmitter("/nonexistent/path")


class TestAngularEmitter:
    @pytest.fixture
    def emitter(self):
        from midicoder.packs.cp_full_data_lifecycle.angular import AngularRetentionEmitter
        stacks_dir = PACKAGE_DIR / "stacks"
        return AngularRetentionEmitter(stacks_dir / "angular" / "core")

    @pytest.fixture
    def ir(self):
        return parse_to_ir({})

    def test_emit_returns_files(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        assert len(files) > 0

    def test_emit_template_count(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        assert len(files) == 6

    def test_invalid_dir_raises_error(self):
        from midicoder.packs.cp_full_data_lifecycle.angular import AngularRetentionEmitter
        from midicoder.errors import MidicoderError
        with pytest.raises(MidicoderError):
            AngularRetentionEmitter("/nonexistent/path")


class TestReactEmitter:
    @pytest.fixture
    def emitter(self):
        from midicoder.packs.cp_full_data_lifecycle.react import ReactRetentionEmitter
        stacks_dir = PACKAGE_DIR / "stacks"
        return ReactRetentionEmitter(stacks_dir / "react" / "core")

    @pytest.fixture
    def ir(self):
        return parse_to_ir({})

    def test_emit_returns_files(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        assert len(files) > 0

    def test_emit_with_context(self, emitter, ir, tmp_path):
        files = emitter.emit(ir, tmp_path)
        for f in files:
            assert len(f.content) > 0

    def test_invalid_dir_raises_error(self):
        from midicoder.packs.cp_full_data_lifecycle.react import ReactRetentionEmitter
        from midicoder.errors import MidicoderError
        with pytest.raises(MidicoderError):
            ReactRetentionEmitter("/nonexistent/path")


class TestEmitterIntegration:
    """Test IR data flows through emitter correctly."""

    def test_ir_data_flows_through_emitter(self, tmp_path):
        from midicoder.packs.cp_full_data_lifecycle.fastapi import FastAPIRetentionEmitter
        stacks_dir = PACKAGE_DIR / "stacks"
        emitter = FastAPIRetentionEmitter(stacks_dir / "fastapi" / "core")
        ir = parse_to_ir({
            "policies": [
                {"policy_id": "order_archive", "entity_type": "Order", "retention_days": 365, "action": "archive"},
            ],
            "enable_archival": True,
            "enable_purge": True,
            "enable_erasure": True,
        })
        files = emitter.emit(ir, tmp_path)
        assert len(files) > 0
        for f in files:
            assert f.content  # có nội dung


class TestPackManifest:
    def test_pack_yml_exists(self):
        assert (PACK_DIR / "pack.yml").exists()

    def test_pack_yml_valid_yaml(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert "pack" in data

    def test_pack_id(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["id"] == "CP47"

    def test_pack_internal_id(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["internal_id"] == "cp_full_data_lifecycle"

    def test_pack_version(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["version"] == "1.0.0"

    def test_pack_status(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["status"] == "stable"

    def test_pack_category(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["category"] == "compliance"

    def test_pack_definitions_count(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["definitions_count"] == 4

    def test_pack_obligations_count(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["obligations_count"] == 2

    def test_pack_capabilities_provided(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        caps = data["pack"]["capabilities_provided"]
        assert "retention_policy" in caps
        assert "data_archival" in caps
        assert "data_purge" in caps
        assert "gdpr_erasure" in caps

    def test_pack_depends_on(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "CP01" in data["pack"]["depends_on"]
        assert "CP08" in data["pack"]["depends_on"]
        assert "CP13" in data["pack"]["depends_on"]
        assert "CP14" in data["pack"]["depends_on"]

    def test_pack_error_codes_prefix(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["error_codes"]["prefix"] == "MDC-CP47"

    def test_pack_definitions(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        defs = data["pack"]["definitions"]
        def_names = [d["name"] for d in defs]
        assert "RetentionPolicy" in def_names
        assert "ArchivedRecord" in def_names
        assert "ErasureRequest" in def_names
        assert "RetentionEngine" in def_names

    def test_pack_file_contributions_count(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        contributions = data["pack"]["file_contributions"]["infrastructure"]
        assert len(contributions) == 24

    def test_pack_file_contributions_by_stack(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        contributions = data["pack"]["file_contributions"]["infrastructure"]
        fastapi_count = sum(1 for c in contributions if "fastapi" in c["stacks"])
        nestjs_count = sum(1 for c in contributions if "nestjs" in c["stacks"])
        angular_count = sum(1 for c in contributions if "angular" in c["stacks"])
        react_count = sum(1 for c in contributions if "react" in c["stacks"])
        assert fastapi_count == 6
        assert nestjs_count == 6
        assert angular_count == 6
        assert react_count == 6

    def test_pack_frontend_integration(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        fe = data["pack"]["frontend_integration"]
        assert "react" in fe
        assert "angular" in fe
        assert "RetentionDashboard" in fe["react"]
        assert "RetentionDashboardComponent" in fe["angular"]

    def test_pack_recipes(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        recipes = data["pack"]["recipes"]
        assert "basic_retention_recipe" in recipes
        assert "full_lifecycle_recipe" in recipes


class TestStackTemplates:
    """Kiểm tra templates tồn tại và có nội dung."""

    def _check_templates(self, stack_dir_name, expected_count):
        stacks_dir = PACKAGE_DIR / "stacks"
        template_dir = stacks_dir / stack_dir_name / "core" / "cp_full_data_lifecycle"
        templates = list(template_dir.glob("*.jinja2"))
        assert len(templates) == expected_count, f"Expected {expected_count} templates in {stack_dir_name}, found {len(templates)}"
        for t in templates:
            content = t.read_text(encoding="utf-8")
            assert len(content) > 50, f"Template {t.name} quá ngắn"

    def test_fastapi_templates(self):
        self._check_templates("fastapi", 6)

    def test_nestjs_templates(self):
        self._check_templates("nestjs", 6)

    def test_angular_templates(self):
        self._check_templates("angular", 6)

    def test_react_templates(self):
        self._check_templates("react", 6)


class TestChangelog:
    def test_changelog_exists(self):
        assert (PACK_DIR / "CHANGELOG.md").exists()

    def test_changelog_has_version(self):
        content = (PACK_DIR / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "1.0.0" in content


class TestRegistry:
    def test_cp47_in_registry(self):
        from midicoder.contracts.registry import CP_ID_TO_INTERNAL
        assert "CP47" in CP_ID_TO_INTERNAL
        assert CP_ID_TO_INTERNAL["CP47"] == "cp_full_data_lifecycle"


class TestInitModule:
    def test_init_exists(self):
        assert (PACK_DIR / "__init__.py").exists()

    def test_init_exports_models(self):
        from midicoder.packs.cp_full_data_lifecycle import (
            RetentionEngine,
            RetentionPolicy,
            ArchivedRecord,
            ErasureRequest,
        )
        assert RetentionEngine is not None

    def test_init_exports_parser(self):
        from midicoder.packs.cp_full_data_lifecycle import (
            RetentionIR,
            parse_to_ir,
            parse_policies,
        )
        assert RetentionIR is not None

    def test_init_exports_recipes(self):
        from midicoder.packs.cp_full_data_lifecycle import (
            basic_retention_recipe,
            full_lifecycle_recipe,
        )
        assert callable(basic_retention_recipe)
        assert callable(full_lifecycle_recipe)
