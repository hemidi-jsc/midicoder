# coding: utf-8
"""
Test templates và pack manifest cho CP49 — Consent & Preference Management.

Test:
- pack.yml tồn tại và hợp lệ
- Templates tồn tại cho 4 stacks (FastAPI, NestJS, Angular, React)
- Registry entry cho CP49
- __init__.py barrel exports
"""

import pytest
from pathlib import Path
import yaml


# __file__ = .../midicoder/emitters/core/cp49_consent/tests/test_templates.py
# parent x6 = midicoder-ce/
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
EMITTERS_DIR = PROJECT_ROOT / "midicoder" / "emitters" / "core" / "cp49_consent"
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
        """Pack ID là CP49."""
        with open(EMITTERS_DIR / "pack.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["id"] == "CP49"

    def test_pack_internal_id(self):
        """Internal ID đúng."""
        with open(EMITTERS_DIR / "pack.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["internal_id"] == "cp49_consent"

    def test_pack_capabilities(self):
        """Capabilities đúng."""
        with open(EMITTERS_DIR / "pack.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        caps = data["pack"]["capabilities_provided"]
        assert "cookie_consent" in caps
        assert "data_consent" in caps
        assert "comm_preference" in caps
        assert "privacy_center" in caps
        assert "marketing_opt_out" in caps
        assert "gdpr_erasure" in caps

    def test_pack_obligations(self):
        """Obligations có TenantIsolation và AuditTrail."""
        with open(EMITTERS_DIR / "pack.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        obligations = data["pack"]["obligations"]
        names = [o["name"] for o in obligations]
        assert "TenantIsolation" in names
        assert "AuditTrail" in names

    def test_pack_depends_on(self):
        """Depends on CP01, CP02, CP03, CP14, CP47."""
        with open(EMITTERS_DIR / "pack.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        deps = data["pack"]["depends_on"]
        assert "CP01" in deps
        assert "CP02" in deps
        assert "CP03" in deps
        assert "CP14" in deps
        assert "CP47" in deps

    def test_pack_file_contributions_count(self):
        """Có 26 file contributions cho 4 stacks."""
        with open(EMITTERS_DIR / "pack.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        contributions = data["pack"]["file_contributions"]["infrastructure"]
        assert len(contributions) == 26  # 7+7+6+6

    def test_pack_recipes(self):
        """Recipes đúng."""
        with open(EMITTERS_DIR / "pack.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        recipes = data["pack"]["recipes"]
        assert "basic_consent_recipe" in recipes
        assert "full_consent_recipe" in recipes


class TestFastAPITemplates:
    """Test FastAPI templates tồn tại."""

    expected_templates = [
        "consent_models.py.jinja2",
        "consent_schemas.py.jinja2",
        "consent_service.py.jinja2",
        "consent_router.py.jinja2",
        "cookie_banner_service.py.jinja2",
        "erasure_service.py.jinja2",
        "consent_middleware.py.jinja2",
    ]

    def test_all_templates_exist(self):
        """Tất cả FastAPI templates tồn tại."""
        stack_dir = STACKS_DIR / "fastapi" / "core" / "cp49_consent"
        for template in self.expected_templates:
            assert (stack_dir / template).exists(), f"Thiếu template: {template}"

    def test_template_not_empty(self):
        """Templates không rỗng."""
        stack_dir = STACKS_DIR / "fastapi" / "core" / "cp49_consent"
        for template in self.expected_templates:
            size = (stack_dir / template).stat().st_size
            assert size > 0, f"Template rỗng: {template}"


class TestNestJSTemplates:
    """Test NestJS templates tồn tại."""

    expected_templates = [
        "consent.entity.ts.jinja2",
        "consent.dto.ts.jinja2",
        "consent.service.ts.jinja2",
        "consent.controller.ts.jinja2",
        "consent.module.ts.jinja2",
        "erasure.service.ts.jinja2",
        "consent.guard.ts.jinja2",
    ]

    def test_all_templates_exist(self):
        """Tất cả NestJS templates tồn tại."""
        stack_dir = STACKS_DIR / "nestjs" / "core" / "cp49_consent"
        for template in self.expected_templates:
            assert (stack_dir / template).exists(), f"Thiếu template: {template}"

    def test_template_not_empty(self):
        """Templates không rỗng."""
        stack_dir = STACKS_DIR / "nestjs" / "core" / "cp49_consent"
        for template in self.expected_templates:
            size = (stack_dir / template).stat().st_size
            assert size > 0, f"Template rỗng: {template}"


class TestAngularTemplates:
    """Test Angular templates tồn tại."""

    expected_templates = [
        "privacy-center.component.ts.jinja2",
        "cookie-banner.component.ts.jinja2",
        "consent-manager.component.ts.jinja2",
        "erasure-request.component.ts.jinja2",
        "consent.service.ts.jinja2",
        "consent.store.ts.jinja2",
    ]

    def test_all_templates_exist(self):
        """Tất cả Angular templates tồn tại."""
        stack_dir = STACKS_DIR / "angular" / "core" / "cp49_consent"
        for template in self.expected_templates:
            assert (stack_dir / template).exists(), f"Thiếu template: {template}"

    def test_template_not_empty(self):
        """Templates không rỗng."""
        stack_dir = STACKS_DIR / "angular" / "core" / "cp49_consent"
        for template in self.expected_templates:
            size = (stack_dir / template).stat().st_size
            assert size > 0, f"Template rỗng: {template}"


class TestReactTemplates:
    """Test React templates tồn tại."""

    expected_templates = [
        "PrivacyCenter.tsx.jinja2",
        "CookieBanner.tsx.jinja2",
        "ConsentManager.tsx.jinja2",
        "ErasureRequest.tsx.jinja2",
        "CommunicationPreferences.tsx.jinja2",
        "useConsent.ts.jinja2",
    ]

    def test_all_templates_exist(self):
        """Tất cả React templates tồn tại."""
        stack_dir = STACKS_DIR / "react" / "core" / "cp49_consent"
        for template in self.expected_templates:
            assert (stack_dir / template).exists(), f"Thiếu template: {template}"

    def test_template_not_empty(self):
        """Templates không rỗng."""
        stack_dir = STACKS_DIR / "react" / "core" / "cp49_consent"
        for template in self.expected_templates:
            size = (stack_dir / template).stat().st_size
            assert size > 0, f"Template rỗng: {template}"


class TestRegistry:
    """Test registry entry cho CP49."""

    def test_cp49_in_registry(self):
        """CP49 có trong registry."""
        from midicoder.contracts.registry import CP_ID_TO_INTERNAL
        assert "CP49" in CP_ID_TO_INTERNAL
        assert CP_ID_TO_INTERNAL["CP49"] == "cp49_consent"


class TestInitModule:
    """Test __init__.py barrel exports."""

    def test_init_exists(self):
        """__init__.py tồn tại."""
        assert (EMITTERS_DIR / "__init__.py").exists()

    def test_init_exports_models(self):
        """__init__.py export models."""
        from midicoder.emitters.core.cp49_consent import (
            ConsentRecord,
            ConsentPolicy,
            CookiePreference,
            ErasureRequest,
            CommunicationPreference,
            ConsentEngine,
        )
        assert ConsentRecord is not None
        assert ConsentPolicy is not None
        assert CookiePreference is not None
        assert ErasureRequest is not None
        assert CommunicationPreference is not None
        assert ConsentEngine is not None

    def test_init_exports_parser(self):
        """__init__.py export parser."""
        from midicoder.emitters.core.cp49_consent import (
            ConsentIR,
            parse_to_ir,
        )
        assert ConsentIR is not None
        assert parse_to_ir is not None

    def test_init_exports_recipes(self):
        """__init__.py export recipes."""
        from midicoder.emitters.core.cp49_consent import (
            basic_consent_recipe,
            full_consent_recipe,
        )
        assert basic_consent_recipe is not None
        assert full_consent_recipe is not None
