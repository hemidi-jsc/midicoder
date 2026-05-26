# coding: utf-8
"""
Test UI framework variant rendering cho frontend packs.

Mô-đun này kiểm tra rằng cùng một template Jinja2 sản sinh ra nội dung
khác nhau khi `ui_framework` được thay đổi (material, tailwind, bootstrap,
antd, carbon). Điều này đảm bảo các nhánh {% if ui_framework == ... %}
trong template hoạt động đúng.

Tiếp cận:
- CP21 (React & Angular): Dùng specialized pack emitters (ReactAuthUIEmitter,
  AngularAuthUIEmitter) vì các template này dùng custom Jinja2 delimiters
  variable_start_string="{[{" để tránh conflict với JSX/Angular {{ }}.
- CP36 (React Onboarding): Dùng Emitter class với custom template_dir,
  vì các template này dùng {% raw %}...{% endraw %} blocks và tương thích
  với default Jinja2 delimiters.
- CP45 (React Payment): Dùng Emitter class với custom template_dir,
  tương tự CP36.

Tác giả: Midicoder CE Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from midicoder.emitters.core.cp21_auth_ui.angular import AngularAuthUIEmitter
from midicoder.emitters.core.cp21_auth_ui.models import (
    AuthPageType,
    AuthUIConfig,
)
from midicoder.emitters.core.cp21_auth_ui.react import ReactAuthUIEmitter
from midicoder.pipeline.emitter import Emitter


# ============================================================================
# UI Frameworks để test
# ============================================================================

UI_FRAMEWORKS = ["material", "tailwind", "bootstrap", "antd", "carbon"]


# ============================================================================
# CP21 Helpers — dùng specialized pack emitters
# ============================================================================


def _make_auth_config(
    ui_framework: str,
    pages: list[AuthPageType] | None = None,
) -> AuthUIConfig:
    """Tạo AuthUIConfig tối thiểu cho test."""
    if pages is None:
        pages = [AuthPageType.LOGIN]
    return AuthUIConfig(
        ui_framework=ui_framework,
        pages=pages,
        include_role_guard=False,
        include_permission_guard=False,
        include_session_timeout=False,
    )


def _render_react_page(
    ui_framework: str,
    page_type: AuthPageType,
) -> str:
    """Render một React auth page template với ui_framework đã chỉ định."""
    emitter = ReactAuthUIEmitter(ui_framework=ui_framework)
    config = _make_auth_config(ui_framework, pages=[page_type])
    page_cfg = config.get_page_config(page_type)
    ctx = emitter._build_context(config, page_type, page_cfg)

    template_name = {
        AuthPageType.LOGIN: "login.tsx.jinja2",
        AuthPageType.REGISTER: "register.tsx.jinja2",
        AuthPageType.FORGOT_PASSWORD: "forgot-password.tsx.jinja2",
        AuthPageType.RESET_PASSWORD: "reset-password.tsx.jinja2",
        AuthPageType.MFA_VERIFY: "mfa-verify.tsx.jinja2",
        AuthPageType.OAUTH_CALLBACK: "oauth-callback.tsx.jinja2",
    }[page_type]

    return emitter._render_template(template_name, ctx)


def _render_angular_page(
    ui_framework: str,
    page_type: AuthPageType,
) -> str:
    """Render một Angular auth page template với ui_framework đã chỉ định."""
    emitter = AngularAuthUIEmitter(ui_framework=ui_framework)
    config = _make_auth_config(ui_framework, pages=[page_type])
    page_cfg = config.get_page_config(page_type)
    ctx = emitter._build_context(config, page_type, page_cfg)

    template_name = {
        AuthPageType.LOGIN: "login.component.ts.jinja2",
        AuthPageType.REGISTER: "register.component.ts.jinja2",
        AuthPageType.FORGOT_PASSWORD: "forgot-password.component.ts.jinja2",
        AuthPageType.RESET_PASSWORD: "reset-password.component.ts.jinja2",
        AuthPageType.MFA_VERIFY: "mfa-verify.component.ts.jinja2",
        AuthPageType.OAUTH_CALLBACK: "oauth-callback.component.ts.jinja2",
    }[page_type]

    return emitter._render_template(template_name, ctx)


def _collect_react_outputs(page_type: AuthPageType) -> dict[str, str]:
    """Render một React page với tất cả 5 frameworks."""
    return {fw: _render_react_page(fw, page_type) for fw in UI_FRAMEWORKS}


def _collect_angular_outputs(page_type: AuthPageType) -> dict[str, str]:
    """Render một Angular page với tất cả 5 frameworks."""
    return {fw: _render_angular_page(fw, page_type) for fw in UI_FRAMEWORKS}


# ============================================================================
# CP36 / CP45 Helpers — dùng generic Emitter class
# ============================================================================

def _get_stacks_dir() -> Path:
    """Lấy đường dẫn đến stacks/ directory."""
    return Path(__file__).resolve().parent.parent.parent / "stacks"


def _make_context_with_framework(framework: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Tạo template context với ui_framework đã chỉ định."""
    context: dict[str, Any] = {"ui_framework": framework}
    if extra:
        context.update(extra)
    return context


# CP36 context — RegistrationForm cần plans với đầy đủ fields, TrialBanner cần plans + default_trial_days
CP36_CONTEXT = {
    "plans": [
        {
            "plan": "free",
            "label": "Free",
            "monthly_price": "0",
            "yearly_price": "0",
            "features": [],
            "max_users": 5,
            "max_storage_gb": 1,
        },
        {
            "plan": "pro",
            "label": "Professional",
            "monthly_price": "29.99",
            "yearly_price": "299.99",
            "features": ["api_access", "priority_support"],
            "max_users": 100,
            "max_storage_gb": 100,
        },
    ],
    "default_trial_days": 14,
    "require_admin_approval": False,
    "auto_start_trial": True,
    "verification_token_expiry_hours": 24,
}


# ============================================================================
# Test: CP21 React — UI Framework Variants
# ============================================================================

class TestCP21ReactUIFrameworkVariants:
    """Kiểm tra CP21 React templates sản sinh nội dung khác nhau theo ui_framework."""

    @pytest.mark.parametrize("ui_framework", UI_FRAMEWORKS)
    def test_login_template_no_error(self, ui_framework: str) -> None:
        """Login template render không lỗi với mọi ui_framework."""
        content = _render_react_page(ui_framework, AuthPageType.LOGIN)
        assert isinstance(content, str)
        assert len(content) > 0

    @pytest.mark.parametrize("ui_framework", UI_FRAMEWORKS)
    def test_register_template_no_error(self, ui_framework: str) -> None:
        """Register template render không lỗi với mọi ui_framework."""
        content = _render_react_page(ui_framework, AuthPageType.REGISTER)
        assert isinstance(content, str)
        assert len(content) > 0

    @pytest.mark.parametrize("ui_framework", UI_FRAMEWORKS)
    def test_forgot_password_template_no_error(self, ui_framework: str) -> None:
        """Forgot-password template render không lỗi với mọi ui_framework."""
        content = _render_react_page(ui_framework, AuthPageType.FORGOT_PASSWORD)
        assert isinstance(content, str)
        assert len(content) > 0

    def test_login_template_produces_different_output(self) -> None:
        """Login template phải cho output khác nhau giữa ít nhất 2 frameworks."""
        results = _collect_react_outputs(AuthPageType.LOGIN)
        unique_outputs = set(results.values())
        assert len(unique_outputs) >= 2, (
            f"Login template cho output giống nhau với tất cả {len(UI_FRAMEWORKS)} frameworks. "
            f"Đã thấy {len(unique_outputs)} output duy nhất."
        )

    def test_register_template_produces_different_output(self) -> None:
        """Register template phải cho output khác nhau giữa ít nhất 2 frameworks."""
        results = _collect_react_outputs(AuthPageType.REGISTER)
        unique_outputs = set(results.values())
        assert len(unique_outputs) >= 2, (
            "Register template cho output giống nhau với tất cả frameworks."
        )

    def test_forgot_password_template_produces_different_output(self) -> None:
        """Forgot-password template phải cho output khác nhau giữa ít nhất 2 frameworks."""
        results = _collect_react_outputs(AuthPageType.FORGOT_PASSWORD)
        unique_outputs = set(results.values())
        assert len(unique_outputs) >= 2, (
            "Forgot-password template cho output giống nhau với tất cả frameworks."
        )


# ============================================================================
# Test: CP21 Angular — UI Framework Variants
# ============================================================================

class TestCP21AngularUIFrameworkVariants:
    """Kiểm tra CP21 Angular templates sản sinh nội dung khác nhau theo ui_framework."""

    @pytest.mark.parametrize("ui_framework", UI_FRAMEWORKS)
    def test_login_component_no_error(self, ui_framework: str) -> None:
        """Angular login component render không lỗi với mọi ui_framework."""
        content = _render_angular_page(ui_framework, AuthPageType.LOGIN)
        assert isinstance(content, str)
        assert len(content) > 0

    @pytest.mark.parametrize("ui_framework", UI_FRAMEWORKS)
    def test_register_component_no_error(self, ui_framework: str) -> None:
        """Angular register component render không lỗi với mọi ui_framework."""
        content = _render_angular_page(ui_framework, AuthPageType.REGISTER)
        assert isinstance(content, str)
        assert len(content) > 0

    def test_login_component_produces_different_output(self) -> None:
        """Angular login component cho output khác nhau giữa các frameworks."""
        results = _collect_angular_outputs(AuthPageType.LOGIN)
        unique_outputs = set(results.values())
        assert len(unique_outputs) >= 2, (
            "Angular login component cho output giống nhau với tất cả frameworks."
        )

    def test_register_component_produces_different_output(self) -> None:
        """Angular register component cho output khác nhau giữa các frameworks."""
        results = _collect_angular_outputs(AuthPageType.REGISTER)
        unique_outputs = set(results.values())
        assert len(unique_outputs) >= 2, (
            "Angular register component cho output giống nhau với tất cả frameworks."
        )

    def test_forgot_password_component_produces_different_output(self) -> None:
        """Angular forgot-password component cho output khác nhau giữa các frameworks."""
        results = _collect_angular_outputs(AuthPageType.FORGOT_PASSWORD)
        unique_outputs = set(results.values())
        assert len(unique_outputs) >= 2, (
            "Angular forgot-password component cho output giống nhau với tất cả frameworks."
        )


# ============================================================================
# Test: CP36 React (Tenant Onboarding) — UI Framework Variants
# ============================================================================

class TestCP36ReactUIFrameworkVariants:
    """Kiểm tra CP36 React templates (tenant onboarding) theo ui_framework.

    Dùng Emitter class với custom template_dir.
    """

    @pytest.fixture
    def emitter(self) -> Emitter:
        """Tạo Emitter cho CP36 React templates."""
        template_dir = _get_stacks_dir() / "react" / "core" / "cp36_tenant_onboarding"
        return Emitter(stack="react", template_dir=template_dir)

    @pytest.mark.parametrize("ui_framework", UI_FRAMEWORKS)
    def test_registration_form_no_error(self, emitter: Emitter, ui_framework: str) -> None:
        """CP36 RegistrationForm render không lỗi với mọi ui_framework."""
        context = _make_context_with_framework(ui_framework, CP36_CONTEXT)
        content = emitter.render("RegistrationForm.tsx.jinja2", context)
        assert isinstance(content, str)
        assert len(content) > 0

    @pytest.mark.parametrize("ui_framework", UI_FRAMEWORKS)
    def test_trial_banner_no_error(self, emitter: Emitter, ui_framework: str) -> None:
        """CP36 TrialBanner render không lỗi với mọi ui_framework."""
        context = _make_context_with_framework(ui_framework, CP36_CONTEXT)
        content = emitter.render("TrialBanner.tsx.jinja2", context)
        assert isinstance(content, str)
        assert len(content) > 0

    def test_registration_form_produces_different_output(self, emitter: Emitter) -> None:
        """CP36 RegistrationForm cho output khác nhau giữa các frameworks."""
        results = {
            fw: emitter.render(
                "RegistrationForm.tsx.jinja2",
                _make_context_with_framework(fw, CP36_CONTEXT),
            )
            for fw in UI_FRAMEWORKS
        }
        unique_outputs = set(results.values())
        assert len(unique_outputs) >= 2, (
            "CP36 RegistrationForm cho output giống nhau với tất cả frameworks."
        )

    def test_trial_banner_produces_different_output(self, emitter: Emitter) -> None:
        """CP36 TrialBanner cho output khác nhau giữa các frameworks."""
        results = {
            fw: emitter.render(
                "TrialBanner.tsx.jinja2",
                _make_context_with_framework(fw, CP36_CONTEXT),
            )
            for fw in UI_FRAMEWORKS
        }
        unique_outputs = set(results.values())
        assert len(unique_outputs) >= 2, (
            "CP36 TrialBanner cho output giống nhau với tất cả frameworks."
        )


# ============================================================================
# Test: CP45 React (Payment) — UI Framework Variants
# ============================================================================

class TestCP45ReactUIFrameworkVariants:
    """Kiểm tra CP45 React templates (payment) theo ui_framework.

    Dùng Emitter class với custom template_dir.
    """

    @pytest.fixture
    def emitter(self) -> Emitter:
        """Tạo Emitter cho CP45 React templates."""
        template_dir = _get_stacks_dir() / "react" / "core" / "cp45_payment"
        return Emitter(stack="react", template_dir=template_dir)

    @pytest.mark.parametrize("ui_framework", UI_FRAMEWORKS)
    def test_payment_dashboard_no_error(self, emitter: Emitter, ui_framework: str) -> None:
        """CP45 PaymentDashboard render không lỗi với mọi ui_framework."""
        context = _make_context_with_framework(ui_framework)
        content = emitter.render("PaymentDashboard.tsx.jinja2", context)
        assert isinstance(content, str)
        assert len(content) > 0

    @pytest.mark.parametrize("ui_framework", UI_FRAMEWORKS)
    def test_payment_history_no_error(self, emitter: Emitter, ui_framework: str) -> None:
        """CP45 PaymentHistory render không lỗi với mọi ui_framework."""
        context = _make_context_with_framework(ui_framework)
        content = emitter.render("PaymentHistory.tsx.jinja2", context)
        assert isinstance(content, str)
        assert len(content) > 0

    def test_payment_dashboard_produces_different_output(self, emitter: Emitter) -> None:
        """CP45 PaymentDashboard cho output khác nhau giữa các frameworks."""
        results = {
            fw: emitter.render(
                "PaymentDashboard.tsx.jinja2",
                _make_context_with_framework(fw),
            )
            for fw in UI_FRAMEWORKS
        }
        unique_outputs = set(results.values())
        assert len(unique_outputs) >= 2, (
            "CP45 PaymentDashboard cho output giống nhau với tất cả frameworks."
        )

    def test_payment_history_produces_different_output(self, emitter: Emitter) -> None:
        """CP45 PaymentHistory cho output khác nhau giữa các frameworks."""
        results = {
            fw: emitter.render(
                "PaymentHistory.tsx.jinja2",
                _make_context_with_framework(fw),
            )
            for fw in UI_FRAMEWORKS
        }
        unique_outputs = set(results.values())
        assert len(unique_outputs) >= 2, (
            "CP45 PaymentHistory cho output giống nhau với tất cả frameworks."
        )


# ============================================================================
# Test: Cross-framework import verification (React)
# ============================================================================

class TestReactUIFrameworkImportVerification:
    """Kiểm tra rằng React output chứa đúng import cho từng ui_framework."""

    def test_login_material_imports_mui(self) -> None:
        """Login với ui_framework='material' phải import @mui/material."""
        content = _render_react_page("material", AuthPageType.LOGIN)
        assert "@mui/material" in content

    def test_login_tailwind_no_mui_import(self) -> None:
        """Login với ui_framework='tailwind' không import @mui/material."""
        content = _render_react_page("tailwind", AuthPageType.LOGIN)
        assert "@mui/material" not in content

    def test_login_antd_imports_ant_design(self) -> None:
        """Login với ui_framework='antd' phải import từ 'antd'."""
        content = _render_react_page("antd", AuthPageType.LOGIN)
        assert "from \"antd\"" in content or "from 'antd'" in content

    def test_login_bootstrap_imports_react_bootstrap(self) -> None:
        """Login với ui_framework='bootstrap' phải import react-bootstrap."""
        content = _render_react_page("bootstrap", AuthPageType.LOGIN)
        assert "react-bootstrap" in content

    def test_login_carbon_imports_carbon(self) -> None:
        """Login với ui_framework='carbon' phải import @carbon/react."""
        content = _render_react_page("carbon", AuthPageType.LOGIN)
        assert "@carbon/react" in content


# ============================================================================
# Test: Cross-framework import verification (Angular)
# ============================================================================

class TestAngularUIFrameworkImportVerification:
    """Kiểm tra rằng Angular output chứa đúng import cho từng ui_framework."""

    def test_login_material_imports_angular_material(self) -> None:
        """Angular login với material phải import @angular/material."""
        content = _render_angular_page("material", AuthPageType.LOGIN)
        assert "@angular/material" in content

    def test_login_tailwind_no_material_import(self) -> None:
        """Angular login với tailwind không import @angular/material."""
        content = _render_angular_page("tailwind", AuthPageType.LOGIN)
        assert "@angular/material" not in content

    def test_login_antd_imports_ng_zorro(self) -> None:
        """Angular login với antd phải import ng-zorro."""
        content = _render_angular_page("antd", AuthPageType.LOGIN)
        assert "ng-zorro" in content

    def test_login_bootstrap_imports_ng_bootstrap(self) -> None:
        """Angular login với bootstrap phải import ng-bootstrap."""
        content = _render_angular_page("bootstrap", AuthPageType.LOGIN)
        assert "ng-bootstrap" in content

    def test_login_carbon_imports_carbon_angular(self) -> None:
        """Angular login với carbon phải import @carbon/angular."""
        content = _render_angular_page("carbon", AuthPageType.LOGIN)
        assert "@carbon/angular" in content
