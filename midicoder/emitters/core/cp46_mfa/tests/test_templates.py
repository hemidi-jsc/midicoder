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
        with open(PACK_DIR / "pack.yml") as f:
            data = yaml.safe_load(f)
        assert data is not None

    def test_pack_id(self):
        with open(PACK_DIR / "pack.yml") as f:
            data = yaml.safe_load(f)
        assert data["pack_id"] == "CP46"

    def test_pack_internal_id(self):
        with open(PACK_DIR / "pack.yml") as f:
            data = yaml.safe_load(f)
        assert data["internal_id"] == "cp46_mfa"

    def test_pack_capabilities(self):
        with open(PACK_DIR / "pack.yml") as f:
            data = yaml.safe_load(f)
        assert "totp_auth" in data["capabilities"]
        assert "sms_otp" in data["capabilities"]
        assert "webauthn_fido2" in data["capabilities"]
        assert "biometric_auth" in data["capabilities"]

    def test_pack_obligations(self):
        with open(PACK_DIR / "pack.yml") as f:
            data = yaml.safe_load(f)
        assert "mfa_enrollment_flow" in data["obligations"]
        assert "mfa_challenge_verification" in data["obligations"]

    def test_pack_depends_on(self):
        with open(PACK_DIR / "pack.yml") as f:
            data = yaml.safe_load(f)
        assert "CP03" in data["depends_on"]
        assert "CP12" in data["depends_on"]

    def test_pack_file_contributions_count(self):
        with open(PACK_DIR / "pack.yml") as f:
            data = yaml.safe_load(f)
        assert len(data["file_contributions"]) >= 5

    def test_pack_recipes(self):
        with open(PACK_DIR / "pack.yml") as f:
            data = yaml.safe_load(f)
        assert "basic_mfa" in str(data["recipes"])
        assert "full_mfa" in str(data["recipes"])


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
