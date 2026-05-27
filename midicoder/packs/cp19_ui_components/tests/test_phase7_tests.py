# coding: utf-8
"""
Phase 7: Tests cho DESIGN_TOKENS + 5 UI Frameworks + Accessibility + i18n
"""

import pytest
from pathlib import Path

from midicoder.packs.cp19_ui_components.models import (
    ComponentType,
    FieldType,
    FormFieldSpec,
    TableSpec,
    TableColumn,
    ComponentSpec,
)


class TestDesignTokens:
    """Tests cho component DESIGN_TOKENS."""

    def test_design_tokens_enum_exists(self):
        """Test enum DESIGN_TOKENS tồn tại."""
        assert ComponentType.DESIGN_TOKENS == "design_tokens"

    def test_design_tokens_in_utility_category(self):
        """Test DESIGN_TOKENS thuộc category utility."""
        from midicoder.packs.cp19_ui_components.models import _COMPONENT_CATEGORIES
        assert _COMPONENT_CATEGORIES.get(ComponentType.DESIGN_TOKENS) == "utility"

    def test_angular_emit_design_tokens(self, tmp_path: Path):
        """Test Angular emit design-tokens.scss."""
        from midicoder.packs.cp19_ui_components.angular import AngularUIEmitter
        emitter = AngularUIEmitter(ui_framework="material")
        components = [
            ComponentSpec(component_type=ComponentType.DESIGN_TOKENS, entity_id="App"),
        ]
        files = emitter.generate(components, tmp_path)
        assert len(files) == 1
        assert "design-tokens.scss" in str(files[0].path)
        assert Path(tmp_path / "utility" / "design-tokens.scss").exists()
        # Verify material-specific tokens in output
        assert "#3f51b5" in files[0].content  # MD primary color

    def test_react_emit_design_tokens(self, tmp_path: Path):
        """Test React emit DesignTokens.ts."""
        from midicoder.packs.cp19_ui_components.react import ReactUIEmitter
        emitter = ReactUIEmitter(ui_framework="tailwind")
        components = [
            ComponentSpec(component_type=ComponentType.DESIGN_TOKENS, entity_id="App"),
        ]
        files = emitter.generate(components, tmp_path)
        assert len(files) == 1
        assert "DesignTokens.ts" in str(files[0].path)
        assert Path(tmp_path / "utility" / "DesignTokens.ts").exists()
        # Verify Tailwind-specific tokens in output
        assert "#6366f1" in files[0].content  # Tailwind indigo-500


class TestFiveUIFrameworks:
    """Tests cho tất cả 5 UI frameworks — verify output contains framework-specific markers."""

    FRAMEWORKS = ["material", "tailwind", "bootstrap", "antd", "carbon"]

    @pytest.mark.parametrize("fw", FRAMEWORKS)
    def test_angular_all_frameworks_form_field(self, fw: str, tmp_path: Path):
        """Test Angular emit FormField cho mỗi framework."""
        from midicoder.packs.cp19_ui_components.angular import AngularUIEmitter
        emitter = AngularUIEmitter(ui_framework=fw)
        components = [
            ComponentSpec(
                component_type=ComponentType.FORM_FIELD,
                entity_id="User",
                fields=[FormFieldSpec(
                    field_name="email",
                    field_type=FieldType.EMAIL,
                    label="Email",
                    binding_path="user.email",
                )],
            ),
        ]
        files = emitter.generate(components, tmp_path)
        assert len(files) == 1
        content = files[0].content
        assert len(content) > 50  # Không rỗng

        # Each framework has distinct markers
        if fw == "material":
            assert "mat-" in content.lower() or "angular/material" in content.lower() or "'#3f51b5'" in content
        elif fw == "tailwind":
            assert "text-sm" in content.lower() or "text-gray" in content.lower() or "w-full" in content.lower()
        elif fw == "bootstrap":
            assert "form-group" in content.lower() or "form-control" in content.lower() or "bs-" in content.lower()
        elif fw == "antd":
            assert "antd-" in content.lower() or "nz-" in content.lower() or "ant-" in content.lower()
        elif fw == "carbon":
            assert "cds-" in content.lower() or "carbon" in content.lower() or "cds--" in content.lower()

    @pytest.mark.parametrize("fw", FRAMEWORKS)
    def test_react_all_frameworks_form_field(self, fw: str, tmp_path: Path):
        """Test React emit FormField cho mỗi framework."""
        from midicoder.packs.cp19_ui_components.react import ReactUIEmitter
        emitter = ReactUIEmitter(ui_framework=fw)
        components = [
            ComponentSpec(
                component_type=ComponentType.FORM_FIELD,
                entity_id="User",
                fields=[FormFieldSpec(
                    field_name="name",
                    field_type=FieldType.TEXT,
                    label="Tên",
                    binding_path="user.name",
                )],
            ),
        ]
        files = emitter.generate(components, tmp_path)
        assert len(files) == 1
        content = files[0].content
        assert len(content) > 50

    @pytest.mark.parametrize("fw", FRAMEWORKS)
    def test_angular_all_frameworks_button(self, fw: str, tmp_path: Path):
        """Test Angular emit Button cho mỗi framework."""
        from midicoder.packs.cp19_ui_components.angular import AngularUIEmitter
        emitter = AngularUIEmitter(ui_framework=fw)
        components = [
            ComponentSpec(component_type=ComponentType.BUTTON, entity_id="User"),
        ]
        files = emitter.generate(components, tmp_path)
        assert len(files) == 1
        assert len(files[0].content) > 30

    @pytest.mark.parametrize("fw", FRAMEWORKS)
    def test_react_all_frameworks_button(self, fw: str, tmp_path: Path):
        """Test React emit Button cho mỗi framework."""
        from midicoder.packs.cp19_ui_components.react import ReactUIEmitter
        emitter = ReactUIEmitter(ui_framework=fw)
        components = [
            ComponentSpec(component_type=ComponentType.BUTTON, entity_id="User"),
        ]
        files = emitter.generate(components, tmp_path)
        assert len(files) == 1
        assert len(files[0].content) > 30

    @pytest.mark.parametrize("fw", FRAMEWORKS)
    def test_angular_design_tokens_has_framework(self, fw: str, tmp_path: Path):
        """Test design tokens output chứa marker riêng của framework."""
        from midicoder.packs.cp19_ui_components.angular import AngularUIEmitter
        emitter = AngularUIEmitter(ui_framework=fw)
        components = [
            ComponentSpec(component_type=ComponentType.DESIGN_TOKENS, entity_id="App"),
        ]
        files = emitter.generate(components, tmp_path)
        assert len(files) == 1
        content = files[0].content
        # Mỗi framework có palette màu khác nhau
        if fw == "material":
            assert "#3f51b5" in content  # MD indigo
        elif fw == "tailwind":
            assert "#6366f1" in content  # Tailwind indigo
        elif fw == "bootstrap":
            assert "#0d6efd" in content  # BS blue
        elif fw == "antd":
            assert "#1677ff" in content  # AntD blue
        elif fw == "carbon":
            assert "#0f62fe" in content  # Carbon blue


class TestAccessibilityFields:
    """Tests cho Phase 4 — Accessibility fields trong models."""

    def test_form_field_spec_aria_label(self):
        """Test FormFieldSpec có aria_label."""
        spec = FormFieldSpec(
            field_name="email",
            field_type=FieldType.EMAIL,
            label="Email",
            binding_path="user.email",
            aria_label="Nhập địa chỉ email của bạn",
            aria_described_by="email-hint",
        )
        assert spec.aria_label == "Nhập địa chỉ email của bạn"
        assert spec.aria_described_by == "email-hint"

    def test_form_field_spec_aria_to_dict(self):
        """Test aria fields serialize vào dict."""
        spec = FormFieldSpec(
            field_name="email",
            field_type=FieldType.EMAIL,
            label="Email",
            binding_path="user.email",
            aria_label="Email input",
            i18n_key="user.email.label",
        )
        d = spec.to_dict()
        assert d["aria_label"] == "Email input"
        assert d["i18n_key"] == "user.email.label"

    def test_form_field_spec_aria_from_dict(self):
        """Test aria fields deserialize từ dict."""
        data = {
            "field_name": "email",
            "field_type": "email",
            "label": "Email",
            "binding_path": "user.email",
            "aria_label": "Email address",
            "aria_described_by": "email-hint",
            "i18n_key": "user.email.label",
        }
        spec = FormFieldSpec.from_dict(data)
        assert spec.aria_label == "Email address"
        assert spec.aria_described_by == "email-hint"
        assert spec.i18n_key == "user.email.label"

    def test_component_spec_accessible_default(self):
        """Test ComponentSpec.default accessible=True."""
        spec = ComponentSpec(component_type=ComponentType.FORM_FIELD, entity_id="User")
        assert spec.accessible is True

    def test_component_spec_aria_and_i18n(self):
        """Test ComponentSpec có aria_label + i18n_key."""
        spec = ComponentSpec(
            component_type=ComponentType.FORM_FIELD,
            entity_id="User",
            aria_label="User registration form",
            i18n_key="forms.user.title",
            locale="vi",
        )
        assert spec.aria_label == "User registration form"
        assert spec.i18n_key == "forms.user.title"
        assert spec.locale == "vi"


class TestCardListPathFix:
    """Tests cho fix Angular CARD_LIST path."""

    def test_angular_card_list_in_data_display(self, tmp_path: Path):
        """Test CARD_LIST output ở data-display/ (không root)."""
        from midicoder.packs.cp19_ui_components.angular import AngularUIEmitter
        entity = {
            "id": "Product",
            "fields": [
                {"name": "name", "type": "str"},
                {"name": "price", "type": "float"},
            ],
        }
        card = ComponentSpec.generate_card_list(entity)
        emitter = AngularUIEmitter(ui_framework="material")
        files = emitter.generate([card], tmp_path)
        assert len(files) == 1
        # File nên nằm trong data-display/
        assert Path(tmp_path / "data-display" / "card-list.component.ts").exists()

    def test_react_card_list_in_data_display(self, tmp_path: Path):
        """Test React CARD_LIST cũng ở data-display/."""
        from midicoder.packs.cp19_ui_components.react import ReactUIEmitter
        entity = {
            "id": "Product",
            "fields": [{"name": "name", "type": "str"}],
        }
        card = ComponentSpec.generate_card_list(entity)
        emitter = ReactUIEmitter(ui_framework="tailwind")
        files = emitter.generate([card], tmp_path)
        assert Path(tmp_path / "data-display" / "CardList.tsx").exists()


class TestComponentSpecRoundtrip:
    """Tests cho serialization roundtrip với fields mới."""

    def test_roundtrip_with_aria_i18n(self):
        """Test ComponentSpec roundtrip với aria + i18n fields."""
        spec = ComponentSpec(
            component_type=ComponentType.FORM_FIELD,
            entity_id="User",
            title="User Form",
            aria_label="User registration form",
            i18n_key="forms.user.title",
            locale="vi",
            fields=[
                FormFieldSpec(
                    field_name="email",
                    field_type=FieldType.EMAIL,
                    label="Email",
                    binding_path="user.email",
                    aria_label="Enter email",
                    i18n_key="user.email.label",
                )
            ],
        )
        d = spec.to_dict()
        restored = ComponentSpec.from_dict(d)
        assert restored.aria_label == spec.aria_label
        assert restored.i18n_key == spec.i18n_key
        assert restored.locale == spec.locale
        assert restored.accessible == spec.accessible
        assert len(restored.fields) == 1
        assert restored.fields[0].aria_label == "Enter email"
        assert restored.fields[0].i18n_key == "user.email.label"
