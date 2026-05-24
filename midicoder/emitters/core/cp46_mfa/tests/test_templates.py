# coding: utf-8
"""
Tests for CP46 templates — MFA & Advanced Authentication.
"""

import pytest
from pathlib import Path
import yaml


PACK_DIR = Path(__file__).resolve().parent.parent


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
        assert data["pack"]["id"] == "CP46"

    def test_pack_internal_id(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["internal_id"] == "cp46_mfa"

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
        assert data["pack"]["category"] == "security"

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
        assert "totp_auth" in caps
        assert "sms_otp" in caps
        assert "webauthn_fido2" in caps
        assert "biometric_auth" in caps

    def test_pack_obligations(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        obligations = data["pack"]["obligations"]
        obligation_names = [o["name"] for o in obligations]
        assert "MfaEnrollmentFlow" in obligation_names
        assert "MfaChallengeVerification" in obligation_names

    def test_pack_depends_on(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "CP03" in data["pack"]["depends_on"]
        assert "CP12" in data["pack"]["depends_on"]

    def test_pack_error_codes_prefix(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["pack"]["error_codes"]["prefix"] == "MDC-CP46"

    def test_pack_definitions(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        defs = data["pack"]["definitions"]
        def_names = [d["name"] for d in defs]
        assert "MFACredential" in def_names
        assert "MFAChallengeSession" in def_names
        assert "MFAEnrollment" in def_names
        assert "MFASession" in def_names

    def test_pack_file_contributions_count(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        contributions = data["pack"]["file_contributions"]["infrastructure"]
        assert len(contributions) >= 20  # 24 templates across 4 stacks

    def test_pack_file_contributions_by_stack(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        contributions = data["pack"]["file_contributions"]["infrastructure"]
        stacks_found = set()
        for contrib in contributions:
            stacks_found.update(contrib["stacks"])
        assert "fastapi" in stacks_found
        assert "nestjs" in stacks_found
        assert "angular" in stacks_found
        assert "react" in stacks_found

    def test_pack_frontend_integration(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        fe = data["pack"]["frontend_integration"]
        assert "react" in fe
        assert "angular" in fe
        assert "MFASetup" in fe["react"]
        assert "MfaSetupComponent" in fe["angular"]

    def test_pack_recipes(self):
        with open(PACK_DIR / "pack.yml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        recipes = data["pack"]["recipes"]
        assert "basic_mfa_recipe" in recipes
        assert "full_mfa_recipe" in recipes


class TestFastAPITemplates:
    @pytest.fixture
    def template_dir(self):
        root = Path(__file__).resolve().parent.parent.parent.parent.parent
        return root / "stacks" / "fastapi" / "core" / "cp46_mfa"

    def test_all_templates_exist(self, template_dir):
        templates = [
            "mfa_models.py.jinja2",
            "mfa_schemas.py.jinja2",
            "mfa_service.py.jinja2",
            "mfa_router.py.jinja2",
            "mfa_totp.py.jinja2",
            "mfa_webauthn.py.jinja2",
        ]
        for name in templates:
            assert (template_dir / name).exists(), f"Template {name} không tồn tại"

    def test_template_not_empty(self, template_dir):
        for tpl in template_dir.glob("*.jinja2"):
            assert tpl.read_text(encoding="utf-8").strip(), f"Template {tpl.name} rỗng"


class TestNestJSTemplates:
    @pytest.fixture
    def template_dir(self):
        root = Path(__file__).resolve().parent.parent.parent.parent.parent
        return root / "stacks" / "nestjs" / "core" / "cp46_mfa"

    def test_all_templates_exist(self, template_dir):
        templates = [
            "mfa.controller.ts.jinja2",
            "mfa.service.ts.jinja2",
            "mfa.module.ts.jinja2",
            "mfa.dto.ts.jinja2",
            "mfa.entity.ts.jinja2",
            "mfa.guard.ts.jinja2",
        ]
        for name in templates:
            assert (template_dir / name).exists(), f"Template {name} không tồn tại"

    def test_template_not_empty(self, template_dir):
        for tpl in template_dir.glob("*.jinja2"):
            assert tpl.read_text(encoding="utf-8").strip(), f"Template {tpl.name} rỗng"


class TestAngularTemplates:
    @pytest.fixture
    def template_dir(self):
        root = Path(__file__).resolve().parent.parent.parent.parent.parent
        return root / "stacks" / "angular" / "core" / "cp46_mfa"

    def test_all_templates_exist(self, template_dir):
        templates = [
            "mfa-setup.component.ts.jinja2",
            "mfa-verify.component.ts.jinja2",
            "mfa-methods.component.ts.jinja2",
            "mfa.service.ts.jinja2",
            "mfa-types.ts.jinja2",
            "mfa-forms.ts.jinja2",
        ]
        for name in templates:
            assert (template_dir / name).exists(), f"Template {name} không tồn tại"

    def test_template_not_empty(self, template_dir):
        for tpl in template_dir.glob("*.jinja2"):
            assert tpl.read_text(encoding="utf-8").strip(), f"Template {tpl.name} rỗng"


class TestReactTemplates:
    @pytest.fixture
    def template_dir(self):
        root = Path(__file__).resolve().parent.parent.parent.parent.parent
        return root / "stacks" / "react" / "core" / "cp46_mfa"

    def test_all_templates_exist(self, template_dir):
        templates = [
            "MFASetup.tsx.jinja2",
            "MFAVerify.tsx.jinja2",
            "MFAMethods.tsx.jinja2",
            "useMFA.ts.jinja2",
            "mfa-types.ts.jinja2",
            "mfa-api.ts.jinja2",
        ]
        for name in templates:
            assert (template_dir / name).exists(), f"Template {name} không tồn tại"

    def test_template_not_empty(self, template_dir):
        for tpl in template_dir.glob("*.jinja2"):
            assert tpl.read_text(encoding="utf-8").strip(), f"Template {tpl.name} rỗng"


class TestChangelog:
    def test_changelog_exists(self):
        assert (PACK_DIR / "CHANGELOG.md").exists()

    def test_changelog_has_version(self):
        content = (PACK_DIR / "CHANGELOG.md").read_text()
        assert "1.0.0" in content


class TestRegistry:
    def test_cp46_in_registry(self):
        import midicoder.contracts.registry as reg
        assert "CP46" in reg.CP_ID_TO_INTERNAL
        assert reg.CP_ID_TO_INTERNAL["CP46"] == "cp46_mfa"


class TestInitModule:
    def test_init_exists(self):
        assert (PACK_DIR / "__init__.py").exists()

    def test_init_exports_models(self):
        from midicoder.emitters.core.cp46_mfa import (
            MFAMethod,
            MFAMethodStatus,
            MFAPriority,
            MFAChallenge,
            MFACredential,
            MFAChallengeSession,
            MFAEnrollment,
            MFASession,
            MFAEngine,
        )

    def test_init_exports_parser(self):
        from midicoder.emitters.core.cp46_mfa import (
            MFAIR,
            MFARule,
            parse_to_ir,
        )

    def test_init_exports_recipes(self):
        from midicoder.emitters.core.cp46_mfa import (
            RecipeOutput,
            basic_mfa_recipe,
            full_mfa_recipe,
        )
