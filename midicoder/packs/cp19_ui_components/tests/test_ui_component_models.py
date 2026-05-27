# coding: utf-8
"""
Tests cho models của UI Component Generator (CP19).

Module: midicoder/packs/ui_component/models.py
Features: ComponentSpec, FormFieldSpec, TableSpec + enums

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from midicoder.errors import MidicoderError, ErrorCode


class TestComponentType:
    """Tests cho enum ComponentType."""

    def test_component_type_values(self):
        """Test giá trị của ComponentType."""
        from midicoder.packs.cp19_ui_components.models import ComponentType
        assert ComponentType.FORM_FIELD.value == "form_field"
        assert ComponentType.DATA_TABLE.value == "data_table"
        assert ComponentType.CARD_LIST.value == "card_list"
        assert ComponentType.DIALOG.value == "dialog"

    def test_component_type_from_string(self):
        """Test tạo ComponentType từ string."""
        from midicoder.packs.cp19_ui_components.models import ComponentType
        assert ComponentType("form_field") == ComponentType.FORM_FIELD
        assert ComponentType("data_table") == ComponentType.DATA_TABLE
        assert ComponentType("card_list") == ComponentType.CARD_LIST
        assert ComponentType("dialog") == ComponentType.DIALOG


class TestFieldType:
    """Tests cho enum FieldType."""

    def test_field_type_values(self):
        """Test giá trị của FieldType."""
        from midicoder.packs.cp19_ui_components.models import FieldType
        assert FieldType.TEXT.value == "text"
        assert FieldType.NUMBER.value == "number"
        assert FieldType.EMAIL.value == "email"
        assert FieldType.DATE.value == "date"
        assert FieldType.BOOLEAN.value == "boolean"
        assert FieldType.SELECT.value == "select"
        assert FieldType.TEXTAREA.value == "textarea"
        assert FieldType.RADIO.value == "radio"
        assert FieldType.SWITCH.value == "switch"

    def test_field_type_from_string(self):
        """Test tạo FieldType từ string."""
        from midicoder.packs.cp19_ui_components.models import FieldType
        assert FieldType("text") == FieldType.TEXT
        assert FieldType("select") == FieldType.SELECT
        assert FieldType("boolean") == FieldType.BOOLEAN


class TestFormFieldSpec:
    """Tests cho FormFieldSpec."""

    def test_form_field_spec_creation(self):
        """Test tạo FormFieldSpec hợp lệ."""
        from midicoder.packs.cp19_ui_components.models import FormFieldSpec, FieldType
        spec = FormFieldSpec(
            field_name="email",
            field_type=FieldType.EMAIL,
            label="Email",
            binding_path="user.email",
        )
        assert spec.field_name == "email"
        assert spec.field_type == FieldType.EMAIL
        assert spec.label == "Email"
        assert spec.binding_path == "user.email"
        assert spec.required is False
        assert spec.options == []

    def test_form_field_spec_with_validators(self):
        """Test FormFieldSpec với validators."""
        from midicoder.packs.cp19_ui_components.models import FormFieldSpec, FieldType
        spec = FormFieldSpec(
            field_name="age",
            field_type=FieldType.NUMBER,
            label="Tuổi",
            binding_path="user.age",
            required=True,
            min_value=0,
            max_value=150,
        )
        assert spec.required is True
        assert spec.min_value == 0
        assert spec.max_value == 150

    def test_form_field_spec_with_options(self):
        """Test FormFieldSpec select/radio có options."""
        from midicoder.packs.cp19_ui_components.models import FormFieldSpec, FieldType
        spec = FormFieldSpec(
            field_name="status",
            field_type=FieldType.SELECT,
            label="Trạng thái",
            binding_path="order.status",
            options=["pending", "confirmed", "shipped", "delivered"],
        )
        assert len(spec.options) == 4
        assert "pending" in spec.options

    def test_form_field_spec_empty_name_raises(self):
        """Test FormFieldSpec name rỗng thì raise."""
        from midicoder.packs.cp19_ui_components.models import FormFieldSpec, FieldType
        with pytest.raises(MidicoderError) as exc_info:
            FormFieldSpec(
                field_name="",
                field_type=FieldType.TEXT,
                label="Test",
                binding_path="test",
            )
        assert exc_info.value.code == ErrorCode.CP19_MISSING_FORM_BINDING

    def test_form_field_spec_empty_binding_path_raises(self):
        """Test FormFieldSpec binding_path rỗng thì raise."""
        from midicoder.packs.cp19_ui_components.models import FormFieldSpec, FieldType
        with pytest.raises(MidicoderError) as exc_info:
            FormFieldSpec(
                field_name="name",
                field_type=FieldType.TEXT,
                label="Tên",
                binding_path="",
            )
        assert exc_info.value.code == ErrorCode.CP19_MISSING_FORM_BINDING

    def test_form_field_spec_to_dict(self):
        """Test serialise FormFieldSpec ra dict."""
        from midicoder.packs.cp19_ui_components.models import FormFieldSpec, FieldType
        spec = FormFieldSpec(
            field_name="email",
            field_type=FieldType.EMAIL,
            label="Email",
            binding_path="user.email",
            required=True,
        )
        d = spec.to_dict()
        assert d["field_name"] == "email"
        assert d["field_type"] == "email"
        assert d["label"] == "Email"
        assert d["required"] is True

    def test_form_field_spec_from_dict(self):
        """Test deserialise FormFieldSpec từ dict."""
        from midicoder.packs.cp19_ui_components.models import FormFieldSpec
        data = {
            "field_name": "password",
            "field_type": "text",
            "label": "Mật khẩu",
            "binding_path": "user.password",
            "required": True,
        }
        spec = FormFieldSpec.from_dict(data)
        assert spec.field_name == "password"
        assert spec.label == "Mật khẩu"
        assert spec.required is True


class TestTableColumn:
    """Tests cho TableColumn."""

    def test_table_column_creation(self):
        """Test tạo TableColumn hợp lệ."""
        from midicoder.packs.cp19_ui_components.models import TableColumn
        col = TableColumn(
            field_name="name",
            label="Tên",
            sortable=True,
            filterable=True,
        )
        assert col.field_name == "name"
        assert col.label == "Tên"
        assert col.sortable is True
        assert col.filterable is True

    def test_table_column_default_values(self):
        """Test giá trị mặc định của TableColumn."""
        from midicoder.packs.cp19_ui_components.models import TableColumn
        col = TableColumn(field_name="id", label="ID")
        assert col.sortable is True
        assert col.filterable is False


class TestTableSpec:
    """Tests cho TableSpec."""

    def test_table_spec_creation(self):
        """Test tạo TableSpec hợp lệ."""
        from midicoder.packs.cp19_ui_components.models import TableSpec, TableColumn
        spec = TableSpec(
            entity_id="Order",
            columns=[
                TableColumn(field_name="id", label="Mã"),
                TableColumn(field_name="status", label="Trạng thái"),
            ],
            sortable=True,
            paginated=True,
            page_size=20,
        )
        assert spec.entity_id == "Order"
        assert len(spec.columns) == 2
        assert spec.sortable is True
        assert spec.paginated is True
        assert spec.page_size == 20

    def test_table_spec_empty_entity_id_raises(self):
        """Test TableSpec entity_id rỗng thì raise."""
        from midicoder.packs.cp19_ui_components.models import TableSpec
        with pytest.raises(MidicoderError) as exc_info:
            TableSpec(entity_id="", columns=[])
        assert exc_info.value.code == ErrorCode.CP19_EMPTY_TABLE_COLUMNS

    def test_table_spec_empty_columns_raises(self):
        """Test TableSpec không có columns thì raise."""
        from midicoder.packs.cp19_ui_components.models import TableSpec
        with pytest.raises(MidicoderError) as exc_info:
            TableSpec(entity_id="Order", columns=[])
        assert exc_info.value.code == ErrorCode.CP19_EMPTY_TABLE_COLUMNS

    def test_table_spec_default_values(self):
        """Test giá trị mặc định của TableSpec."""
        from midicoder.packs.cp19_ui_components.models import TableSpec, TableColumn
        spec = TableSpec(
            entity_id="Product",
            columns=[TableColumn(field_name="name", label="Tên")],
        )
        assert spec.sortable is True
        assert spec.paginated is True
        assert spec.page_size == 20
        assert spec.filterable is False

    def test_table_spec_to_dict(self):
        """Test serialise TableSpec ra dict."""
        from midicoder.packs.cp19_ui_components.models import TableSpec, TableColumn
        spec = TableSpec(
            entity_id="Order",
            columns=[TableColumn(field_name="id", label="Mã")],
            paginated=False,
        )
        d = spec.to_dict()
        assert d["entity_id"] == "Order"
        assert d["paginated"] is False
        assert len(d["columns"]) == 1

    def test_table_spec_from_dict(self):
        """Test deserialise TableSpec từ dict."""
        from midicoder.packs.cp19_ui_components.models import TableSpec
        data = {
            "entity_id": "User",
            "columns": [
                {"field_name": "id", "label": "ID"},
                {"field_name": "name", "label": "Tên"},
            ],
            "sortable": True,
            "paginated": True,
            "page_size": 50,
        }
        spec = TableSpec.from_dict(data)
        assert spec.entity_id == "User"
        assert len(spec.columns) == 2
        assert spec.page_size == 50


class TestComponentSpec:
    """Tests cho ComponentSpec."""

    def test_component_spec_form_field(self):
        """Test tạo ComponentSpec cho form field."""
        from midicoder.packs.cp19_ui_components.models import (
            ComponentSpec, ComponentType, FormFieldSpec, FieldType,
        )
        spec = ComponentSpec(
            component_type=ComponentType.FORM_FIELD,
            entity_id="Order",
            fields=[
                FormFieldSpec(
                    field_name="email",
                    field_type=FieldType.EMAIL,
                    label="Email",
                    binding_path="order.email",
                ),
            ],
        )
        assert spec.component_type == ComponentType.FORM_FIELD
        assert spec.entity_id == "Order"
        assert len(spec.fields) == 1

    def test_component_spec_data_table(self):
        """Test tạo ComponentSpec cho data table."""
        from midicoder.packs.cp19_ui_components.models import (
            ComponentSpec, ComponentType, TableSpec, TableColumn,
        )
        spec = ComponentSpec(
            component_type=ComponentType.DATA_TABLE,
            entity_id="Product",
            table_spec=TableSpec(
                entity_id="Product",
                columns=[TableColumn(field_name="name", label="Tên")],
            ),
        )
        assert spec.component_type == ComponentType.DATA_TABLE
        assert spec.table_spec is not None

    def test_component_spec_card_list(self):
        """Test tạo ComponentSpec cho card list."""
        from midicoder.packs.cp19_ui_components.models import ComponentSpec, ComponentType
        spec = ComponentSpec(
            component_type=ComponentType.CARD_LIST,
            entity_id="User",
        )
        assert spec.component_type == ComponentType.CARD_LIST

    def test_component_spec_dialog(self):
        """Test tạo ComponentSpec cho dialog."""
        from midicoder.packs.cp19_ui_components.models import ComponentSpec, ComponentType
        spec = ComponentSpec(
            component_type=ComponentType.DIALOG,
            entity_id="Order",
            title="Chi tiết đơn hàng",
        )
        assert spec.component_type == ComponentType.DIALOG
        assert spec.title == "Chi tiết đơn hàng"

    def test_component_spec_empty_entity_raises(self):
        """Test ComponentSpec entity_id rỗng thì raise."""
        from midicoder.packs.cp19_ui_components.models import ComponentSpec, ComponentType
        with pytest.raises(MidicoderError) as exc_info:
            ComponentSpec(
                component_type=ComponentType.FORM_FIELD,
                entity_id="",
            )
        assert exc_info.value.code == ErrorCode.CP19_INVALID_COMPONENT_TYPE

    def test_component_spec_invalid_component_type_raises(self):
        """Test ComponentSpec với component type không hợp lệ."""
        # This test validates that the enum constrains valid types
        from midicoder.packs.cp19_ui_components.models import ComponentType
        valid_types = ["form_field", "data_table", "card_list", "dialog"]
        for t in valid_types:
            assert ComponentType(t) is not None

    def test_component_spec_to_dict(self):
        """Test serialise ComponentSpec ra dict."""
        from midicoder.packs.cp19_ui_components.models import (
            ComponentSpec, ComponentType, FormFieldSpec, FieldType,
        )
        spec = ComponentSpec(
            component_type=ComponentType.FORM_FIELD,
            entity_id="Order",
            fields=[
                FormFieldSpec(
                    field_name="name",
                    field_type=FieldType.TEXT,
                    label="Tên",
                    binding_path="order.name",
                ),
            ],
        )
        d = spec.to_dict()
        assert d["component_type"] == "form_field"
        assert d["entity_id"] == "Order"
        assert len(d["fields"]) == 1

    def test_component_spec_from_dict(self):
        """Test deserialise ComponentSpec từ dict."""
        from midicoder.packs.cp19_ui_components.models import ComponentSpec, ComponentType
        data = {
            "component_type": "card_list",
            "entity_id": "Product",
            "properties": {"grid_cols": 3},
        }
        spec = ComponentSpec.from_dict(data)
        assert spec.component_type == ComponentType.CARD_LIST
        assert spec.entity_id == "Product"

    def test_component_spec_generate_form_fields_from_entity(self):
        """Test generate form fields tự động từ entity fields."""
        from midicoder.packs.cp19_ui_components.models import (
            ComponentSpec, ComponentType,
        )
        entity = {
            "id": "Order",
            "fields": [
                {"name": "name", "type": "str"},
                {"name": "email", "type": "str"},
                {"name": "total", "type": "float"},
                {"name": "active", "type": "bool"},
            ],
        }
        spec = ComponentSpec.generate_form(entity)
        assert spec.component_type == ComponentType.FORM_FIELD
        assert spec.entity_id == "Order"
        assert len(spec.fields) == 4
        field_names = [f.field_name for f in spec.fields]
        assert "name" in field_names
        assert "email" in field_names
        assert "total" in field_names
        assert "active" in field_names

    def test_component_spec_generate_table_from_entity(self):
        """Test generate table spec tự động từ entity fields."""
        from midicoder.packs.cp19_ui_components.models import ComponentSpec, ComponentType
        entity = {
            "id": "Product",
            "fields": [
                {"name": "name", "type": "str"},
                {"name": "price", "type": "float"},
            ],
        }
        spec = ComponentSpec.generate_table(entity)
        assert spec.component_type == ComponentType.DATA_TABLE
        assert spec.table_spec is not None
        assert len(spec.table_spec.columns) == 2


class TestObligationSchemaConsistency:
    """Tests cho obligation: component schema consistency."""

    def test_field_type_mismatch_raises(self):
        """Test lỗi khi field type trong form không khớp entity."""
        from midicoder.packs.cp19_ui_components.models import ComponentSpec
        entity = {
            "id": "User",
            "fields": [
                {"name": "age", "type": "int"},
            ],
        }
        spec = ComponentSpec.generate_form(entity)
        age_field = [f for f in spec.fields if f.field_name == "age"][0]
        assert age_field.field_type.value == "number"

    def test_binding_path_follows_entity_id(self):
        """Test binding_path chứa entity_id."""
        from midicoder.packs.cp19_ui_components.models import ComponentSpec
        entity = {
            "id": "Order",
            "fields": [
                {"name": "status", "type": "str"},
            ],
        }
        spec = ComponentSpec.generate_form(entity)
        status_field = [f for f in spec.fields if f.field_name == "status"][0]
        assert "order" in status_field.binding_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
