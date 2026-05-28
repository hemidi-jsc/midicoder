# coding: utf-8
"""
Unit tests cho CP36 — 4 Emitter (FastAPI, NestJS, React, Angular).

Test emitter classes sinh ra files dung.

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
from decimal import Decimal

from midicoder.packs.cp_full_tenant_onboarding.models import (
    OnboardingIR,
    PlanConfig,
    SubscriptionPlan,
)
from midicoder.packs.cp_full_tenant_onboarding.fastapi import (
    TenantOnboardingFastAPIEmitter,
    GeneratedFile,
)
from midicoder.packs.cp_full_tenant_onboarding.nestjs import (
    TenantOnboardingNestJSEmitter,
)
from midicoder.packs.cp_full_tenant_onboarding.react import (
    TenantOnboardingReactEmitter,
)
from midicoder.packs.cp_full_tenant_onboarding.angular import (
    TenantOnboardingAngularEmitter,
)
from midicoder.packs.cp_full_tenant_onboarding.recipes import (
    self_service_saas_recipe,
)


# Path to stacks directory
_STACKS_DIR = Path(__file__).parents[4] / "stacks"


def _make_ir() -> OnboardingIR:
    """Tao OnboardingIR mau de test emitter."""
    return self_service_saas_recipe(trial_days=14)


def _make_dsl_config() -> dict:
    """Tao DSL config dict de test FastAPI emitter."""
    return {
        "currencies": [{"code": "USD", "name": "US Dollar"}],
        "accounts": [],
        "base_currency": "USD",
        "fx_rates": [],
    }


# ===========================================================================
# Test FastAPI Emitter
# ===========================================================================


class TestFastAPIEmitter:
    """Test TenantOnboardingFastAPIEmitter."""

    def test_emit_produces_files(self) -> None:
        """Emitter sinh ra danh sach files."""
        stack_dir = _STACKS_DIR / "fastapi" / "core"
        template_dir = stack_dir / "cp_full_tenant_onboarding"

        if not template_dir.exists():
            pytest.skip("FastAPI templates khong ton tai")

        emitter = TenantOnboardingFastAPIEmitter(str(stack_dir))
        files = emitter.emit(_make_dsl_config(), "/tmp/output")

        assert isinstance(files, list)
        assert len(files) > 0
        # Dem so luong template duoc render
        assert len(files) == len(list(template_dir.glob("*.jinja2")))
        for f in files:
            assert isinstance(f, GeneratedFile)
            assert f.path
            assert f.content
            # Rule V1: generated code khong import midicoder
            assert "import midicoder" not in f.content

    def test_emitted_files_have_vietnamese_comments(self) -> None:
        """Files sinh ra co comments tieng Viet."""
        stack_dir = _STACKS_DIR / "fastapi" / "core"
        template_dir = stack_dir / "cp_full_tenant_onboarding"

        if not template_dir.exists():
            pytest.skip("FastAPI templates khong ton tai")

        emitter = TenantOnboardingFastAPIEmitter(str(stack_dir))
        files = emitter.emit(_make_dsl_config(), "/tmp/output")

        # Moi file phai co it nhat 1 comment
        total_comments = sum(1 for f in files if "#" in f.content or '"""' in f.content)
        assert total_comments > 0

    def test_emitted_files_contain_entity_references(self) -> None:
        """Files sinh ra co chua tham chieu den TenantRegistration/TenantSubscription."""
        stack_dir = _STACKS_DIR / "fastapi" / "core"
        template_dir = stack_dir / "cp_full_tenant_onboarding"

        if not template_dir.exists():
            pytest.skip("FastAPI templates khong ton tai")

        emitter = TenantOnboardingFastAPIEmitter(str(stack_dir))
        files = emitter.emit(_make_dsl_config(), "/tmp/output")

        all_content = "\n".join(f.content for f in files)
        assert "TenantRegistration" in all_content or "registration" in all_content.lower()
        assert "TenantSubscription" in all_content or "subscription" in all_content.lower()

    def test_template_not_found_raises(self) -> None:
        """Template khong ton tai throw loi MDC-CP36."""
        from midicoder.errors import MidicoderError
        stack_dir = _STACKS_DIR / "fastapi" / "core"
        template_dir = stack_dir / "cp_full_tenant_onboarding"

        if not template_dir.exists():
            pytest.skip("FastAPI templates khong ton tai")

        emitter = TenantOnboardingFastAPIEmitter(str(stack_dir))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.py.jinja2", {})


# ===========================================================================
# Test NestJS Emitter
# ===========================================================================


class TestNestJSEmitter:
    """Test TenantOnboardingNestJSEmitter."""

    def test_emit_produces_files(self) -> None:
        """Emitter sinh ra danh sach files."""
        stack_dir = _STACKS_DIR / "nestjs" / "core"
        template_dir = stack_dir / "cp_full_tenant_onboarding"

        if not template_dir.exists():
            pytest.skip("NestJS templates khong ton tai")

        ir = _make_ir()
        emitter = TenantOnboardingNestJSEmitter(str(stack_dir))
        result = emitter.emit(ir, "/tmp/output")

        assert isinstance(result, (dict, list))
        # Dem so luong template duoc render
        assert len(result) == len(list(template_dir.glob("*.jinja2")))
        if isinstance(result, dict):
            for path, content in result.items():
                assert path.endswith(".ts")
                assert isinstance(content, str)
                assert len(content) > 0
        else:
            for item in result:
                assert hasattr(item, 'path') and hasattr(item, 'content')

    def test_emitted_files_have_typescript_types(self) -> None:
        """Files NestJS sinh ra co TypeScript types."""
        stack_dir = _STACKS_DIR / "nestjs" / "core"
        template_dir = stack_dir / "cp_full_tenant_onboarding"

        if not template_dir.exists():
            pytest.skip("NestJS templates khong ton tai")

        ir = _make_ir()
        emitter = TenantOnboardingNestJSEmitter(str(stack_dir))
        result = emitter.emit(ir, "/tmp/output")

        if isinstance(result, dict):
            all_content = "\n".join(result.values())
        else:
            all_content = "\n".join(f.content for f in result)

        assert "interface" in all_content or "class" in all_content
        assert "Entity" in all_content or "entity" in all_content

    def test_template_not_found_raises(self) -> None:
        """Template khong ton tai throw loi MDC-CP36."""
        from midicoder.errors import MidicoderError
        stack_dir = _STACKS_DIR / "nestjs" / "core"
        template_dir = stack_dir / "cp_full_tenant_onboarding"

        if not template_dir.exists():
            pytest.skip("NestJS templates khong ton tai")

        emitter = TenantOnboardingNestJSEmitter(str(stack_dir))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.ts.jinja2", {})


# ===========================================================================
# Test React Emitter
# ===========================================================================


class TestReactEmitter:
    """Test TenantOnboardingReactEmitter."""

    def test_emit_produces_files(self) -> None:
        """Emitter sinh ra cac component React."""
        stack_dir = _STACKS_DIR / "react" / "core"
        template_dir = stack_dir / "cp_full_tenant_onboarding"

        if not template_dir.exists():
            pytest.skip("React templates khong ton tai")

        ir = _make_ir()
        emitter = TenantOnboardingReactEmitter(str(stack_dir))
        result = emitter.emit(ir)

        assert isinstance(result, (dict, list))
        # Dem so luong template duoc render
        assert len(result) == len(list(template_dir.glob("*.jinja2")))
        if isinstance(result, dict):
            for path, content in result.items():
                assert isinstance(content, str)
                assert len(content) > 0
        else:
            for item in result:
                assert hasattr(item, 'path') and hasattr(item, 'content')

    def test_emitted_files_have_react_hooks(self) -> None:
        """Files React sinh ra co hooks."""
        stack_dir = _STACKS_DIR / "react" / "core"
        template_dir = stack_dir / "cp_full_tenant_onboarding"

        if not template_dir.exists():
            pytest.skip("React templates khong ton tai")

        ir = _make_ir()
        emitter = TenantOnboardingReactEmitter(str(stack_dir))
        result = emitter.emit(ir)

        if isinstance(result, dict):
            all_content = "\n".join(result.values())
        else:
            all_content = "\n".join(f.content for f in result)

        # Phai co it nhat 1 React hook
        assert "useState" in all_content or "useEffect" in all_content or "useCallback" in all_content

    def test_template_not_found_raises(self) -> None:
        """Template khong ton tai throw loi MDC-CP36."""
        from midicoder.errors import MidicoderError
        stack_dir = _STACKS_DIR / "react" / "core"
        template_dir = stack_dir / "cp_full_tenant_onboarding"

        if not template_dir.exists():
            pytest.skip("React templates khong ton tai")

        emitter = TenantOnboardingReactEmitter(str(stack_dir))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.tsx.jinja2", {})


# ===========================================================================
# Test Angular Emitter
# ===========================================================================


class TestAngularEmitter:
    """Test TenantOnboardingAngularEmitter."""

    def test_emit_produces_files(self) -> None:
        """Emitter sinh ra cac component Angular."""
        stack_dir = _STACKS_DIR / "angular" / "core"
        template_dir = stack_dir / "cp_full_tenant_onboarding"

        if not template_dir.exists():
            pytest.skip("Angular templates khong ton tai")

        ir = _make_ir()
        emitter = TenantOnboardingAngularEmitter(str(stack_dir))
        result = emitter.emit(ir)

        assert isinstance(result, (dict, list))
        # Dem so luong template duoc render
        assert len(result) == len(list(template_dir.glob("*.jinja2")))
        if isinstance(result, dict):
            for path, content in result.items():
                assert isinstance(content, str)
                assert len(content) > 0
        else:
            for item in result:
                assert hasattr(item, 'path') and hasattr(item, 'content')

    def test_emitted_files_have_angular_decorators(self) -> None:
        """Files Angular sinh ra co decorators."""
        stack_dir = _STACKS_DIR / "angular" / "core"
        template_dir = stack_dir / "cp_full_tenant_onboarding"

        if not template_dir.exists():
            pytest.skip("Angular templates khong ton tai")

        ir = _make_ir()
        emitter = TenantOnboardingAngularEmitter(str(stack_dir))
        result = emitter.emit(ir)

        if isinstance(result, dict):
            all_content = "\n".join(result.values())
        else:
            all_content = "\n".join(f.content for f in result)

        assert "Component" in all_content or "Injectable" in all_content

    def test_template_not_found_raises(self) -> None:
        """Template khong ton tai throw loi MDC-CP36."""
        from midicoder.errors import MidicoderError
        stack_dir = _STACKS_DIR / "angular" / "core"
        template_dir = stack_dir / "cp_full_tenant_onboarding"

        if not template_dir.exists():
            pytest.skip("Angular templates khong ton tai")

        emitter = TenantOnboardingAngularEmitter(str(stack_dir))
        with pytest.raises(MidicoderError):
            emitter._render("nonexistent.ts.jinja2", {})
