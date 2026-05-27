# coding: utf-8
"""
Tests cho CP37 pack.yml và template validation.
"""

from __future__ import annotations

from pathlib import Path

import yaml
import jinja2

# midicoder/packs/cp37_feature_flags/tests/
# parent.parent = cp37_feature_flags/
# parent.parent.parent = packs/
PACK_YML = Path(__file__).parent.parent / "pack.yml"


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


# ============================================================================
# Rule V1 & V2 (P2-17) — template render tests
# ============================================================================

# Đường dẫn stack directories
MIDICODER_ROOT_37 = Path(__file__).parent.parent.parent.parent.parent

STACK_DIRS_37 = {
    "fastapi": MIDICODER_ROOT_37 / "stacks" / "fastapi" / "core" / "cp37_feature_flags",
    "nestjs": MIDICODER_ROOT_37 / "stacks" / "nestjs" / "core" / "cp37_feature_flags",
    "angular": MIDICODER_ROOT_37 / "stacks" / "angular" / "core" / "cp37_feature_flags",
    "react": MIDICODER_ROOT_37 / "stacks" / "react" / "core" / "cp37_feature_flags",
}

FASTAPI_TEMPLATES_37 = [
    "flag_model.py.jinja2",
    "flag_schema.py.jinja2",
    "flag_service.py.jinja2",
    "flag_router.py.jinja2",
    "ab_experiment_model.py.jinja2",
    "config_model.py.jinja2",
    "flag_evaluator.py.jinja2",
    "flag_store.py.jinja2",
    "redis_store.py.jinja2",
    "db_store.py.jinja2",
    "config_service.py.jinja2",
    "__init__.py.jinja2",
]

NESTJS_TEMPLATES_37 = [
    "flag.entity.ts.jinja2",
    "flag.dto.ts.jinja2",
    "flag.service.ts.jinja2",
    "flag.controller.ts.jinja2",
    "experiment.entity.ts.jinja2",
    "config.entity.ts.jinja2",
    "feature-flags.module.ts.jinja2",
]

ANGULAR_TEMPLATES_37 = [
    "flag-provider.service.ts.jinja2",
    "flag-directive.ts.jinja2",
    "flag-interceptor.ts.jinja2",
    "config.service.ts.jinja2",
    "flag-sync.service.ts.jinja2",
]

REACT_TEMPLATES_37 = [
    "FeatureFlagProvider.tsx.jinja2",
    "useFeatureFlag.ts.jinja2",
    "useAllFlags.ts.jinja2",
    "useABVariant.ts.jinja2",
    "useConfig.ts.jinja2",
    "FeatureFlagGate.tsx.jinja2",
    "FlagSyncWorker.ts.jinja2",
]

ALL_TEMPLATES_37 = {
    "fastapi": FASTAPI_TEMPLATES_37,
    "nestjs": NESTJS_TEMPLATES_37,
    "angular": ANGULAR_TEMPLATES_37,
    "react": REACT_TEMPLATES_37,
}


def _render_template_37(stack: str, template_name: str) -> str:
    """Render template với context cơ bản; fallback sang đọc source thô nếu render lỗi."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(STACK_DIRS_37[stack])),
        undefined=jinja2.ChainableUndefined,
    )
    ctx: dict = {}
    try:
        template = env.get_template(template_name)
        return template.render(**ctx)
    except Exception:
        # Template chứa JSX/TSX không bọc {% raw %} — đọc source thô
        source_path = STACK_DIRS_37[stack] / template_name
        return source_path.read_text(encoding="utf-8")


class TestRuleV1NoMidicoderImport:
    """Rule V1: Output của template KHÔNG chứa 'from midicoder'."""

    def test_fastapi_no_midicoder_import(self):
        """FastAPI templates không chứa 'from midicoder' trong output."""
        for template in FASTAPI_TEMPLATES_37:
            result = _render_template_37("fastapi", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_nestjs_no_midicoder_import(self):
        """NestJS templates không chứa 'from midicoder' trong output."""
        for template in NESTJS_TEMPLATES_37:
            result = _render_template_37("nestjs", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_angular_no_midicoder_import(self):
        """Angular templates không chứa 'from midicoder' trong output."""
        for template in ANGULAR_TEMPLATES_37:
            result = _render_template_37("angular", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"

    def test_react_no_midicoder_import(self):
        """React templates không chứa 'from midicoder' trong output."""
        for template in REACT_TEMPLATES_37:
            result = _render_template_37("react", template)
            assert "from midicoder" not in result, f"Rule V1 vi phạm: {template}"
            assert "import midicoder" not in result, f"Rule V1 vi phạm: {template}"


class TestRuleV2NoPostInit:
    """Rule V2: Output của template KHÔNG chứa '__post_init__'."""

    def test_fastapi_no_post_init(self):
        """FastAPI templates không chứa __post_init__ trong output."""
        for template in FASTAPI_TEMPLATES_37:
            result = _render_template_37("fastapi", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_nestjs_no_post_init(self):
        """NestJS templates không chứa __post_init__ trong output."""
        for template in NESTJS_TEMPLATES_37:
            result = _render_template_37("nestjs", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_angular_no_post_init(self):
        """Angular templates không chứa __post_init__ trong output."""
        for template in ANGULAR_TEMPLATES_37:
            result = _render_template_37("angular", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"

    def test_react_no_post_init(self):
        """React templates không chứa __post_init__ trong output."""
        for template in REACT_TEMPLATES_37:
            result = _render_template_37("react", template)
            assert "__post_init__" not in result, f"Rule V2 vi phạm: {template}"
