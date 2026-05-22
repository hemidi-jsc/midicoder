# coding: utf-8
"""
Tests cho CP37 pack.yml và template validation.
"""

from __future__ import annotations

from pathlib import Path

import yaml

# midicoder/emitters/core/cp37_feature_flags/tests/
# parent.parent = cp37_feature_flags/
# parent.parent.parent = core/
# parent.parent.parent.parent = emitters/
PACK_YML = Path(__file__).parent.parent.parent / "cp37_feature_flags" / "pack.yml"


class TestCP37PackYaml:
    """Tests cho pack.yml CP37."""

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
        assert data["pack"]["id"] == "CP37"

    def test_pack_yml_has_capabilities(self):
        with open(PACK_YML, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        caps = data["pack"].get("capabilities_provided", [])
        assert "evaluate_feature_flag" in caps
        assert "assign_experiment" in caps
        assert "read_dynamic_config" in caps


class TestFastAPITemplates:
    """Tests cho FastAPI template existence và content."""

    def _get_template_dir(self):
        return Path(__file__).parent.parent.parent.parent.parent / "stacks" / "fastapi" / "core" / "cp37_feature_flags"

    def test_flag_model_template_exists(self):
        assert (self._get_template_dir() / "flag_model.py.jinja2").exists()

    def test_flag_schema_template_exists(self):
        assert (self._get_template_dir() / "flag_schema.py.jinja2").exists()

    def test_flag_service_template_exists(self):
        assert (self._get_template_dir() / "flag_service.py.jinja2").exists()

    def test_flag_router_template_exists(self):
        assert (self._get_template_dir() / "flag_router.py.jinja2").exists()

    def test_ab_experiment_model_template_exists(self):
        assert (self._get_template_dir() / "ab_experiment_model.py.jinja2").exists()

    def test_config_model_template_exists(self):
        assert (self._get_template_dir() / "config_model.py.jinja2").exists()

    def test_flag_evaluator_template_exists(self):
        assert (self._get_template_dir() / "flag_evaluator.py.jinja2").exists()

    def test_flag_store_template_exists(self):
        assert (self._get_template_dir() / "flag_store.py.jinja2").exists()

    def test_redis_store_template_exists(self):
        assert (self._get_template_dir() / "redis_store.py.jinja2").exists()

    def test_db_store_template_exists(self):
        assert (self._get_template_dir() / "db_store.py.jinja2").exists()

    def test_init_template_exists(self):
        assert (self._get_template_dir() / "__init__.py.jinja2").exists()

    def test_flag_model_content(self):
        content = (self._get_template_dir() / "flag_model.py.jinja2").read_text()
        assert "FeatureFlag" in content

    def test_config_service_template_exists(self):
        assert (self._get_template_dir() / "config_service.py.jinja2").exists()


class TestNestJSTemplates:
    """Tests cho NestJS template existence và content."""

    def _get_template_dir(self):
        return Path(__file__).parent.parent.parent.parent.parent / "stacks" / "nestjs" / "core" / "cp37_feature_flags"

    def test_flag_entity_template_exists(self):
        assert (self._get_template_dir() / "flag.entity.ts.jinja2").exists()

    def test_flag_dto_template_exists(self):
        assert (self._get_template_dir() / "flag.dto.ts.jinja2").exists()

    def test_flag_service_template_exists(self):
        assert (self._get_template_dir() / "flag.service.ts.jinja2").exists()

    def test_flag_controller_template_exists(self):
        assert (self._get_template_dir() / "flag.controller.ts.jinja2").exists()

    def test_experiment_entity_template_exists(self):
        assert (self._get_template_dir() / "experiment.entity.ts.jinja2").exists()

    def test_config_entity_template_exists(self):
        assert (self._get_template_dir() / "config.entity.ts.jinja2").exists()

    def test_feature_flags_module_template_exists(self):
        assert (self._get_template_dir() / "feature-flags.module.ts.jinja2").exists()

    def test_flag_entity_content(self):
        content = (self._get_template_dir() / "flag.entity.ts.jinja2").read_text()
        assert "Entity" in content or "entity" in content or "flag" in content.lower()


class TestAngularTemplates:
    """Tests cho Angular template existence và content."""

    def _get_template_dir(self):
        return Path(__file__).parent.parent.parent.parent.parent / "stacks" / "angular" / "core" / "cp37_feature_flags"

    def test_flag_provider_service_template_exists(self):
        assert (self._get_template_dir() / "flag-provider.service.ts.jinja2").exists()

    def test_flag_directive_template_exists(self):
        assert (self._get_template_dir() / "flag-directive.ts.jinja2").exists()

    def test_flag_interceptor_template_exists(self):
        assert (self._get_template_dir() / "flag-interceptor.ts.jinja2").exists()

    def test_config_service_template_exists(self):
        assert (self._get_template_dir() / "config.service.ts.jinja2").exists()

    def test_flag_sync_service_template_exists(self):
        assert (self._get_template_dir() / "flag-sync.service.ts.jinja2").exists()

    def test_flag_provider_content(self):
        content = (self._get_template_dir() / "flag-provider.service.ts.jinja2").read_text()
        assert "Service" in content or "Injectable" in content or "flag" in content.lower()

    def test_exactly_5_templates(self):
        templates = list(self._get_template_dir().glob("*.jinja2"))
        assert len(templates) == 5


class TestReactTemplates:
    """Tests cho React template existence và content."""

    def _get_template_dir(self):
        return Path(__file__).parent.parent.parent.parent.parent / "stacks" / "react" / "core" / "cp37_feature_flags"

    def test_feature_flag_provider_template_exists(self):
        assert (self._get_template_dir() / "FeatureFlagProvider.tsx.jinja2").exists()

    def test_use_feature_flag_template_exists(self):
        assert (self._get_template_dir() / "useFeatureFlag.ts.jinja2").exists()

    def test_use_all_flags_template_exists(self):
        assert (self._get_template_dir() / "useAllFlags.ts.jinja2").exists()

    def test_use_ab_variant_template_exists(self):
        assert (self._get_template_dir() / "useABVariant.ts.jinja2").exists()

    def test_use_config_template_exists(self):
        assert (self._get_template_dir() / "useConfig.ts.jinja2").exists()

    def test_feature_flag_gate_template_exists(self):
        assert (self._get_template_dir() / "FeatureFlagGate.tsx.jinja2").exists()

    def test_flag_sync_worker_template_exists(self):
        assert (self._get_template_dir() / "FlagSyncWorker.ts.jinja2").exists()

    def test_feature_flag_provider_content(self):
        content = (self._get_template_dir() / "FeatureFlagProvider.tsx.jinja2").read_text()
        assert "Provider" in content or "Context" in content or "flag" in content.lower()

    def test_exactly_7_templates(self):
        templates = list(self._get_template_dir().glob("*.jinja2"))
        assert len(templates) == 7
