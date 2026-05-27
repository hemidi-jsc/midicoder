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


# __file__ = .../midicoder/packs/cp49_consent/tests/test_templates.py
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

    def test_pack_no_gdpr_erasure(self):
        """gdpr_erasure không còn trong capabilities (delegate đến CP47)."""
        with open(EMITTERS_DIR / "pack.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        caps = data["pack"]["capabilities_provided"]
        assert "gdpr_erasure" not in caps

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
        """Có 24 file contributions cho 4 stacks (6+6+6+6)."""
        with open(EMITTERS_DIR / "pack.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        contributions = data["pack"]["file_contributions"]["infrastructure"]
        assert len(contributions) == 24  # 6+6+6+6

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
        from midicoder.packs.cp49_consent import (
            ConsentRecord,
            ConsentPolicy,
            CookiePreference,
            CommunicationPreference,
            ConsentEngine,
        )
        assert ConsentRecord is not None
        assert ConsentPolicy is not None
        assert CookiePreference is not None
        assert CommunicationPreference is not None
        assert ConsentEngine is not None

    def test_init_exports_parser(self):
        """__init__.py export parser."""
        from midicoder.packs.cp49_consent import (
            ConsentIR,
            parse_to_ir,
        )
        assert ConsentIR is not None
        assert parse_to_ir is not None

    def test_init_exports_recipes(self):
        """__init__.py export recipes."""
        from midicoder.packs.cp49_consent import (
            basic_consent_recipe,
            full_consent_recipe,
        )
        assert basic_consent_recipe is not None
        assert full_consent_recipe is not None


# ===========================================================================
# Test Template Render (P2-17)
# ===========================================================================

class TestTemplateRender:
    """Test render templates với context thật và verify Rule V1."""

    def _render_all_fastapi(self):
        """Render tất cả FastAPI templates và trả về danh sách (name, content)."""
        from midicoder.packs.cp49_consent.fastapi import FastAPIConsentEmitter
        from midicoder.packs.cp49_consent.recipes import basic_consent_recipe
        emitter = FastAPIConsentEmitter(stack_dir=str(STACKS_DIR / "fastapi" / "core" / "cp49_consent"))
        ir = basic_consent_recipe().ir
        files = emitter.emit(ir, "/tmp")
        return [(f.path, f.content) for f in files]

    def _render_all_nestjs(self):
        """Render tất cả NestJS templates và trả về danh sách (name, content)."""
        from midicoder.packs.cp49_consent.nestjs import NestJSConsentEmitter
        from midicoder.packs.cp49_consent.recipes import basic_consent_recipe
        emitter = NestJSConsentEmitter(stack_dir=str(STACKS_DIR / "nestjs" / "core" / "cp49_consent"))
        ir = basic_consent_recipe().ir
        files = emitter.emit(ir, "/tmp")
        return [(f.path, f.content) for f in files]

    def _render_all_angular(self):
        """Render tất cả Angular templates và trả về danh sách (name, content)."""
        from midicoder.packs.cp49_consent.angular import AngularConsentEmitter
        from midicoder.packs.cp49_consent.recipes import basic_consent_recipe
        emitter = AngularConsentEmitter(stack_dir=str(STACKS_DIR / "angular" / "core" / "cp49_consent"))
        ir = basic_consent_recipe().ir
        files = emitter.emit(ir, "/tmp")
        return [(f.path, f.content) for f in files]

    def _render_all_react(self):
        """Render tất cả React templates và trả về danh sách (name, content)."""
        from midicoder.packs.cp49_consent.react import ReactConsentEmitter
        from midicoder.packs.cp49_consent.recipes import basic_consent_recipe
        emitter = ReactConsentEmitter(stack_dir=str(STACKS_DIR / "react" / "core" / "cp49_consent"))
        ir = basic_consent_recipe().ir
        files = emitter.emit(ir)
        return [(f["path"], f["content"]) for f in files]

    # --- FastAPI render tests ---

    def test_fastapi_templates_render_success(self):
        """Tất cả FastAPI templates render thành công không throw exception."""
        files = self._render_all_fastapi()
        assert len(files) > 0

    def test_fastapi_templates_no_midicoder_import(self):
        """Rule V1: FastAPI templates không chứa 'from midicoder' trong output."""
        for path, content in self._render_all_fastapi():
            assert "from midicoder" not in content, f"Rule V1 vi phạm trong {path}"
            assert "import midicoder" not in content, f"Rule V1 vi phạm trong {path}"

    def test_fastapi_templates_have_keywords(self):
        """FastAPI templates chứa keywords Python quan trọng."""
        files = self._render_all_fastapi()
        # Ít nhất 1 file phải chứa import statement
        all_content = "\n".join(c for _, c in files)
        assert "import" in all_content, "FastAPI output không chứa import statement"

    # --- NestJS render tests ---

    def test_nestjs_templates_render_success(self):
        """Tất cả NestJS templates render thành công không throw exception."""
        files = self._render_all_nestjs()
        assert len(files) > 0

    def test_nestjs_templates_no_midicoder_import(self):
        """Rule V1: NestJS templates không chứa 'from midicoder' trong output."""
        for path, content in self._render_all_nestjs():
            assert "from midicoder" not in content, f"Rule V1 vi phạm trong {path}"
            assert "import midicoder" not in content, f"Rule V1 vi phạm trong {path}"

    def test_nestjs_templates_have_keywords(self):
        """NestJS templates chứa keywords TypeScript quan trọng."""
        files = self._render_all_nestjs()
        all_content = "\n".join(c for _, c in files)
        assert "export" in all_content, "NestJS output không chứa export statement"

    # --- Angular render tests ---

    def test_angular_templates_render_success(self):
        """Tất cả Angular templates render thành công không throw exception."""
        files = self._render_all_angular()
        assert len(files) > 0

    def test_angular_templates_no_midicoder_import(self):
        """Rule V1: Angular templates không chứa 'from midicoder' trong output."""
        for path, content in self._render_all_angular():
            assert "from midicoder" not in content, f"Rule V1 vi phạm trong {path}"
            assert "import midicoder" not in content, f"Rule V1 vi phạm trong {path}"

    def test_angular_templates_have_keywords(self):
        """Angular templates chứa keywords TypeScript quan trọng."""
        files = self._render_all_angular()
        all_content = "\n".join(c for _, c in files)
        assert "import" in all_content, "Angular output không chứa import statement"

    # --- React render tests ---

    def test_react_templates_render_success(self):
        """Tất cả React templates render thành công không throw exception."""
        files = self._render_all_react()
        assert len(files) > 0

    def test_react_templates_no_midicoder_import(self):
        """Rule V1: React templates không chứa 'from midicoder' trong output."""
        for path, content in self._render_all_react():
            assert "from midicoder" not in content, f"Rule V1 vi phạm trong {path}"
            assert "import midicoder" not in content, f"Rule V1 vi phạm trong {path}"

    def test_react_templates_have_keywords(self):
        """React templates chứa keywords JSX quan trọng."""
        files = self._render_all_react()
        all_content = "\n".join(c for _, c in files)
        assert "import" in all_content, "React output không chứa import statement"

    # --- Rule V2: No __post_init__ in templates ---

    def test_no_post_init_in_any_template(self):
        """Rule V2: Không có __post_init__ trong output của bất kỳ template nào."""
        for renderer in [self._render_all_fastapi, self._render_all_nestjs,
                         self._render_all_angular, self._render_all_react]:
            for path, content in renderer():
                assert "__post_init__" not in content, f"Rule V2 vi phạm trong {path}"
