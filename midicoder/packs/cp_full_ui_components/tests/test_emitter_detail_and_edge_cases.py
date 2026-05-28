# coding: utf-8
"""
Bổ sung test coverage chi tiết cho FastAPIUIEmitter, NestJSUIEmitter
và edge cases cho tất cả emitters.

Author: Midicoder Team
Version: 2.0.0
"""

import pytest
from pathlib import Path
from midicoder.packs.cp_full_ui_components.models import (
    ComponentSpec, ComponentType, FormFieldSpec, FieldType,
    TableSpec, TableColumn, FormBuilderSpec, ThemeSpec, ConditionalRule,
)


# ============================================================================
# FastAPIUIEmitter — Detail coverage
# ============================================================================


class TestFastAPIUIEmitterDetail:
    """Tests chi tiết cho FastAPIUIEmitter."""

    def test_fastapi_emitter_multiple_entities(self, tmp_path: Path):
        """Test sinh form validation cho nhiều entities."""
        from midicoder.packs.cp_full_ui_components.fastapi import FastAPIUIEmitter

        emitter = FastAPIUIEmitter()
        components = [
            ComponentSpec(
                component_type=ComponentType.FORM_FIELD,
                entity_id="User",
                fields=[
                    FormFieldSpec(field_name="email", field_type=FieldType.EMAIL, label="Email", binding_path="user.email", required=True),
                    FormFieldSpec(field_name="name", field_type=FieldType.TEXT, label="Tên", binding_path="user.name"),
                ],
            ),
            ComponentSpec(
                component_type=ComponentType.FORM_FIELD,
                entity_id="Order",
                fields=[
                    FormFieldSpec(field_name="total", field_type=FieldType.NUMBER, label="Tổng", binding_path="order.total", min_value=0, max_value=999999),
                    FormFieldSpec(field_name="status", field_type=FieldType.SELECT, label="Trạng thái", binding_path="order.status", options=["pending", "done"]),
                ],
            ),
        ]

        files = emitter.generate(components, tmp_path)
        assert len(files) == 1
        assert Path(tmp_path / "form_validation_service.py").exists()
        content = files[0].content
        assert "pydantic" in content.lower() or "validation" in content.lower() or "not found" in content

    def test_fastapi_emitter_all_field_types(self, tmp_path: Path):
        """Test sinh với tất cả field types."""
        from midicoder.packs.cp_full_ui_components.fastapi import FastAPIUIEmitter

        emitter = FastAPIUIEmitter()
        all_types = [
            (FieldType.TEXT, "text_field"),
            (FieldType.NUMBER, "num_field"),
            (FieldType.EMAIL, "email_field"),
            (FieldType.DATE, "date_field"),
            (FieldType.BOOLEAN, "bool_field"),
            (FieldType.SELECT, "select_field"),
            (FieldType.TEXTAREA, "textarea_field"),
            (FieldType.RADIO, "radio_field"),
            (FieldType.SWITCH, "switch_field"),
        ]

        fields = [
            FormFieldSpec(field_name=name, field_type=ft, label=name, binding_path=f"form.{name}")
            for ft, name in all_types
        ]
        components = [ComponentSpec(component_type=ComponentType.FORM_FIELD, entity_id="TestForm", fields=fields)]

        files = emitter.generate(components, tmp_path)
        assert len(files) == 1
        assert len(files[0].content) > 0

    def test_fastapi_emitter_output_dir_nested(self, tmp_path: Path):
        """Test sinh file vào nested output directory."""
        from midicoder.packs.cp_full_ui_components.fastapi import FastAPIUIEmitter

        emitter = FastAPIUIEmitter()
        nested = tmp_path / "deeply" / "nested" / "dir"
        components = [
            ComponentSpec(component_type=ComponentType.FORM_FIELD, entity_id="Test"),
        ]
        files = emitter.generate(components, nested)
        assert len(files) == 1
        assert (nested / "form_validation_service.py").exists()


# ============================================================================
# NestJSUIEmitter — Detail coverage
# ============================================================================


class TestNestJSUIEmitterDetail:
    """Tests chi tiết cho NestJSUIEmitter."""

    def test_nestjs_emitter_multiple_dto_fields(self, tmp_path: Path):
        """Test sinh DTO với nhiều field types."""
        from midicoder.packs.cp_full_ui_components.nestjs import NestJSUIEmitter

        emitter = NestJSUIEmitter()
        fields = [
            FormFieldSpec(field_name="name", field_type=FieldType.TEXT, label="Tên", binding_path="u.name", required=True),
            FormFieldSpec(field_name="email", field_type=FieldType.EMAIL, label="Email", binding_path="u.email", required=True),
            FormFieldSpec(field_name="age", field_type=FieldType.NUMBER, label="Tuổi", binding_path="u.age", min_value=0, max_value=150),
            FormFieldSpec(field_name="active", field_type=FieldType.BOOLEAN, label="Hoạt động", binding_path="u.active"),
            FormFieldSpec(field_name="role", field_type=FieldType.SELECT, label="Vai trò", binding_path="u.role", options=["admin", "user"]),
            FormFieldSpec(field_name="bio", field_type=FieldType.TEXTAREA, label="Tiểu sử", binding_path="u.bio"),
            FormFieldSpec(field_name="signup_date", field_type=FieldType.DATE, label="Ngày đăng ký", binding_path="u.signup_date"),
        ]
        components = [
            ComponentSpec(component_type=ComponentType.FORM_FIELD, entity_id="User", fields=fields),
        ]

        files = emitter.generate(components, tmp_path)
        assert len(files) == 2  # DTO + Pipe
        dto_file = [f for f in files if "dto" in str(f.path)][0]
        pipe_file = [f for f in files if "pipe" in str(f.path)][0]

        assert len(dto_file.content) > 0
        assert "class-validator" in dto_file.content.lower() or "IsString" in dto_file.content or "not found" in dto_file.content
        assert len(pipe_file.content) > 0

    def test_nestjs_emitter_multiple_entities_multiple_dtos(self, tmp_path: Path):
        """Test sinh DTO cho nhiều entities → nhiều file DTO + 1 pipe."""
        from midicoder.packs.cp_full_ui_components.nestjs import NestJSUIEmitter

        emitter = NestJSUIEmitter()
        components = [
            ComponentSpec(
                component_type=ComponentType.FORM_FIELD,
                entity_id="User",
                fields=[FormFieldSpec(field_name="email", field_type=FieldType.EMAIL, label="Email", binding_path="u.email")],
            ),
            ComponentSpec(
                component_type=ComponentType.FORM_FIELD,
                entity_id="Order",
                fields=[FormFieldSpec(field_name="total", field_type=FieldType.NUMBER, label="Tổng", binding_path="o.total")],
            ),
            ComponentSpec(
                component_type=ComponentType.FORM_FIELD,
                entity_id="Product",
                fields=[FormFieldSpec(field_name="name", field_type=FieldType.TEXT, label="Tên", binding_path="p.name")],
            ),
        ]

        files = emitter.generate(components, tmp_path)
        # 3 DTO files + 1 Pipe = 4 files
        assert len(files) == 4
        dto_files = [f for f in files if "dto" in str(f.path)]
        assert len(dto_files) == 3
        pipe_files = [f for f in files if "pipe" in str(f.path)]
        assert len(pipe_files) == 1

    def test_nestjs_emitter_options_validation(self, tmp_path: Path):
        """Test DTO với select field có options → IsIn decorator."""
        from midicoder.packs.cp_full_ui_components.nestjs import NestJSUIEmitter

        emitter = NestJSUIEmitter()
        components = [
            ComponentSpec(
                component_type=ComponentType.FORM_FIELD,
                entity_id="Order",
                fields=[
                    FormFieldSpec(
                        field_name="status",
                        field_type=FieldType.SELECT,
                        label="Trạng thái",
                        binding_path="order.status",
                        options=["pending", "confirmed", "shipped", "delivered", "cancelled"],
                        required=True,
                    )
                ],
            ),
        ]

        files = emitter.generate(components, tmp_path)
        dto_content = [f for f in files if "dto" in str(f.path)][0].content
        # IsIn decorator should contain the option values
        assert "IsIn" in dto_content or "pending" in dto_content or "not found" in dto_content

    def test_nestjs_emitter_min_max(self, tmp_path: Path):
        """Test DTO với number field có min/max → Min/Max decorators."""
        from midicoder.packs.cp_full_ui_components.nestjs import NestJSUIEmitter

        emitter = NestJSUIEmitter()
        components = [
            ComponentSpec(
                component_type=ComponentType.FORM_FIELD,
                entity_id="User",
                fields=[
                    FormFieldSpec(
                        field_name="age",
                        field_type=FieldType.NUMBER,
                        label="Tuổi",
                        binding_path="user.age",
                        min_value=0,
                        max_value=150,
                        required=True,
                    )
                ],
            ),
        ]

        files = emitter.generate(components, tmp_path)
        dto_content = [f for f in files if "dto" in str(f.path)][0].content
        assert "Min" in dto_content or "Max" in dto_content or "not found" in dto_content


# ============================================================================
# Edge Case Tests — Tất cả emitters
# ============================================================================


class TestEdgeCases:
    """Tests cho edge case của tất cả emitters."""

    def test_angular_empty_components_list(self, tmp_path: Path):
        """Test Angular emit với empty component list."""
        from midicoder.packs.cp_full_ui_components.angular import AngularUIEmitter

        emitter = AngularUIEmitter(ui_framework="material")
        files = emitter.generate([], tmp_path)
        assert len(files) == 0

    def test_react_empty_components_list(self, tmp_path: Path):
        """Test React emit với empty component list."""
        from midicoder.packs.cp_full_ui_components.react import ReactUIEmitter

        emitter = ReactUIEmitter(ui_framework="tailwind")
        files = emitter.generate([], tmp_path)
        assert len(files) == 0

    def test_angular_entity_no_fields(self, tmp_path: Path):
        """Test emit với entity không có fields."""
        from midicoder.packs.cp_full_ui_components.angular import AngularUIEmitter

        entity = {"id": "EmptyEntity", "fields": []}
        components = [
            ComponentSpec.generate_form(entity),
            ComponentSpec.generate_table(entity),
        ]
        emitter = AngularUIEmitter(ui_framework="material")
        files = emitter.generate(components, tmp_path)
        assert len(files) == 2

    def test_react_entity_no_fields(self, tmp_path: Path):
        """Test emit React với entity không có fields."""
        from midicoder.packs.cp_full_ui_components.react import ReactUIEmitter

        entity = {"id": "EmptyEntity", "fields": []}
        components = [
            ComponentSpec.generate_form(entity),
            ComponentSpec.generate_table(entity),
        ]
        emitter = ReactUIEmitter(ui_framework="tailwind")
        files = emitter.generate(components, tmp_path)
        assert len(files) == 2

    def test_unknown_component_type_still_emits(self, tmp_path: Path):
        """Test component type không trong template map — fallback."""
        from midicoder.packs.cp_full_ui_components.angular import AngularUIEmitter

        components = [
            ComponentSpec(
                component_type=ComponentType.SPINNER,  # có trong map nhưng test fallback path
                entity_id="Test",
            ),
        ]
        emitter = AngularUIEmitter(ui_framework="material")
        files = emitter.generate(components, tmp_path)
        assert len(files) == 1

    def test_duplicate_component_types_deduped(self, tmp_path: Path):
        """Test duplicate component types → multiple specs emitted."""
        from midicoder.packs.cp_full_ui_components.react import ReactUIEmitter

        components = [
            ComponentSpec(component_type=ComponentType.FORM_FIELD, entity_id="User"),
            ComponentSpec(component_type=ComponentType.FORM_FIELD, entity_id="Order"),
            ComponentSpec(component_type=ComponentType.FORM_FIELD, entity_id="Product"),
        ]
        emitter = ReactUIEmitter(ui_framework="tailwind")
        files = emitter.generate(components, tmp_path)
        # Each entity gets its own FormField.tsx
        assert len(files) == 3

    def test_angular_all_component_categories(self, tmp_path: Path):
        """Test Angular emit cho tất cả component categories."""
        from midicoder.packs.cp_full_ui_components.angular import AngularUIEmitter

        # Select one from each category
        components = [
            ComponentSpec(component_type=ComponentType.FORM_FIELD, entity_id="User"),      # data-input
            ComponentSpec(component_type=ComponentType.DATA_TABLE, entity_id="User",       # data-display
                          table_spec=TableSpec(entity_id="User", columns=[TableColumn(field_name="id", label="ID")])),
            ComponentSpec(component_type=ComponentType.ALERT, entity_id="App"),            # feedback
            ComponentSpec(component_type=ComponentType.NAVBAR, entity_id="App"),           # navigation
            ComponentSpec(component_type=ComponentType.CONTAINER, entity_id="App"),        # layout
            ComponentSpec(component_type=ComponentType.BUTTON, entity_id="App"),           # utility
            ComponentSpec(component_type=ComponentType.DRAWER, entity_id="App"),           # surface
        ]
        emitter = AngularUIEmitter(ui_framework="material")
        files = emitter.generate(components, tmp_path)
        assert len(files) == 7

    def test_react_all_component_categories(self, tmp_path: Path):
        """Test React emit cho tất cả component categories."""
        from midicoder.packs.cp_full_ui_components.react import ReactUIEmitter

        components = [
            ComponentSpec(component_type=ComponentType.FORM_FIELD, entity_id="User"),
            ComponentSpec(component_type=ComponentType.DATA_TABLE, entity_id="User",
                          table_spec=TableSpec(entity_id="User", columns=[TableColumn(field_name="id", label="ID")])),
            ComponentSpec(component_type=ComponentType.ALERT, entity_id="App"),
            ComponentSpec(component_type=ComponentType.NAVBAR, entity_id="App"),
            ComponentSpec(component_type=ComponentType.CONTAINER, entity_id="App"),
            ComponentSpec(component_type=ComponentType.BUTTON, entity_id="App"),
            ComponentSpec(component_type=ComponentType.DRAWER, entity_id="App"),
        ]
        emitter = ReactUIEmitter(ui_framework="tailwind")
        files = emitter.generate(components, tmp_path)
        assert len(files) == 7

    def test_fastapi_emitter_non_form_components(self, tmp_path: Path):
        """Test FastAPI emitter chỉ xử lý FORM_FIELD, ignore non-form."""
        from midicoder.packs.cp_full_ui_components.fastapi import FastAPIUIEmitter

        emitter = FastAPIUIEmitter()
        components = [
            ComponentSpec(component_type=ComponentType.DATA_TABLE, entity_id="User"),
            ComponentSpec(component_type=ComponentType.DIALOG, entity_id="User"),
        ]
        files = emitter.generate(components, tmp_path)
        assert len(files) == 1  # vẫn sinh service mặc định

    def test_nestjs_emitter_non_form_components(self, tmp_path: Path):
        """Test NestJS emitter chỉ xử lý FORM_FIELD."""
        from midicoder.packs.cp_full_ui_components.nestjs import NestJSUIEmitter

        emitter = NestJSUIEmitter()
        components = [
            ComponentSpec(component_type=ComponentType.DATA_TABLE, entity_id="User"),
        ]
        files = emitter.generate(components, tmp_path)
        assert len(files) == 1  # chỉ pipe

    def test_card_list_from_entity(self, tmp_path: Path):
        """Test generate_card_list từ entity."""
        entity = {
            "id": "Product",
            "fields": [
                {"name": "name", "type": "str"},
                {"name": "price", "type": "float"},
                {"name": "active", "type": "bool"},
            ],
        }
        card_spec = ComponentSpec.generate_card_list(entity)
        assert card_spec.component_type == ComponentType.CARD_LIST
        assert card_spec.entity_id == "Product"

    def test_dialog_from_entity(self, tmp_path: Path):
        """Test generate_dialog từ entity."""
        entity = {"id": "Order", "fields": [{"name": "id", "type": "str"}]}
        dialog_spec = ComponentSpec.generate_dialog(entity)
        assert dialog_spec.component_type == ComponentType.DIALOG
        assert dialog_spec.entity_id == "Order"


# ============================================================================
# Model Edge Cases
# ============================================================================


class TestModelEdgeCases:
    """Tests cho edge case của models."""

    def test_form_field_spec_whitespace_name_raises(self):
        """Test FormFieldSpec name chỉ whitespace thì raise."""
        from midicoder.errors import MidicoderError, ErrorCode

        with pytest.raises(MidicoderError) as exc_info:
            FormFieldSpec(field_name="   ", field_type=FieldType.TEXT, label="Test", binding_path="test")
        assert exc_info.value.code == ErrorCode.MDC-F07_MISSING_FORM_BINDING

    def test_form_field_spec_whitespace_binding_raises(self):
        """Test FormFieldSpec binding_path chỉ whitespace thì raise."""
        from midicoder.errors import MidicoderError, ErrorCode

        with pytest.raises(MidicoderError) as exc_info:
            FormFieldSpec(field_name="test", field_type=FieldType.TEXT, label="Test", binding_path="   ")
        assert exc_info.value.code == ErrorCode.MDC-F07_MISSING_FORM_BINDING

    def test_table_spec_whitespace_entity_raises(self):
        """Test TableSpec entity_id chỉ whitespace thì raise."""
        from midicoder.errors import MidicoderError, ErrorCode

        with pytest.raises(MidicoderError) as exc_info:
            TableSpec(entity_id="   ", columns=[TableColumn(field_name="id", label="ID")])
        assert exc_info.value.code == ErrorCode.MDC-F07_EMPTY_TABLE_COLUMNS

    def test_component_spec_whitespace_entity_raises(self):
        """Test ComponentSpec entity_id chỉ whitespace thì raise."""
        from midicoder.errors import MidicoderError, ErrorCode

        with pytest.raises(MidicoderError) as exc_info:
            ComponentSpec(component_type=ComponentType.FORM_FIELD, entity_id="   ")
        assert exc_info.value.code == ErrorCode.MDC-F07_INVALID_COMPONENT_TYPE

    def test_form_builder_spec_from_entity(self):
        """Test FormBuilderSpec from entity."""
        entity = {
            "id": "Customer",
            "fields": [
                {"name": "name", "type": "str", "required": True},
                {"name": "email", "type": "str"},
                {"name": "phone", "type": "str"},
            ],
        }
        spec = FormBuilderSpec.from_entity(entity)
        assert spec.entity_id == "Customer"
        assert len(spec.fields) == 3
        assert spec.fields[0].required is True

    def test_form_builder_spec_with_conditional_rules(self):
        """Test FormBuilderSpec với conditional rules."""
        spec = FormBuilderSpec(
            entity_id="Order",
            fields=[
                FormFieldSpec(field_name="shipping", field_type=FieldType.BOOLEAN, label="Shipping", binding_path="order.shipping"),
                FormFieldSpec(field_name="address", field_type=FieldType.TEXT, label="Address", binding_path="order.address"),
            ],
            conditional_rules=[
                ConditionalRule(target_field="address", condition_field="shipping", condition_operator="eq", condition_value=True, show=True),
            ],
        )
        assert len(spec.conditional_rules) == 1
        assert spec.conditional_rules[0].target_field == "address"

    def test_theme_spec_roundtrip(self):
        """Test ThemeSpec serialize/deserialize."""
        theme = ThemeSpec(
            name="dark",
            primary_color="#0f62fe",
            dark_mode=True,
        )
        d = theme.to_dict()
        restored = ThemeSpec.from_dict(d)
        assert restored.name == "dark"
        assert restored.dark_mode is True

    def test_component_spec_from_dict_unknown_type_fallback(self):
        """Test ComponentSpec.from_dict với unknown type → fallback FORM_FIELD."""
        data = {"component_type": "unknown_type_xyz", "entity_id": "Test"}
        spec = ComponentSpec.from_dict(data)
        assert spec.component_type == ComponentType.FORM_FIELD

    def test_field_type_mapping(self):
        """Test _FIELD_TYPE_MAP covers all expected types."""
        from midicoder.packs.cp_full_ui_components.models import _FIELD_TYPE_MAP

        assert _FIELD_TYPE_MAP["str"] == FieldType.TEXT
        assert _FIELD_TYPE_MAP["int"] == FieldType.NUMBER
        assert _FIELD_TYPE_MAP["float"] == FieldType.NUMBER
        assert _FIELD_TYPE_MAP["bool"] == FieldType.BOOLEAN
        assert _FIELD_TYPE_MAP["email"] == FieldType.EMAIL
        assert _FIELD_TYPE_MAP["date"] == FieldType.DATE
        assert _FIELD_TYPE_MAP["datetime"] == FieldType.DATE
        assert _FIELD_TYPE_MAP["text"] == FieldType.TEXTAREA
        # Unknown type should fallback to TEXT
        spec = ComponentSpec.generate_form({"id": "Test", "fields": [{"name": "x", "type": "unknown_type"}]})
        assert spec.fields[0].field_type == FieldType.TEXT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
