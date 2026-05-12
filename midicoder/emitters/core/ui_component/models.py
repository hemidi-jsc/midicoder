# coding: utf-8
"""
UI Component Models (CP19).

Module này cung cấp các models cho UI Component Generator:
- ComponentSpec: spec cho một UI component (form_field, data_table, card_list, dialog)
- FormFieldSpec: spec cho một form field (field type, validators, binding)
- TableSpec: spec cho data table (columns, sortable, paginated)
- ComponentType: enum cho loại component
- FieldType: enum cho loại form field

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ============================================================================
# Enums
# ============================================================================


class ComponentType(str, Enum):
    """Loại UI component để generate."""
    FORM_FIELD = "form_field"
    DATA_TABLE = "data_table"
    CARD_LIST = "card_list"
    DIALOG = "dialog"


class FieldType(str, Enum):
    """Loại form field để generate."""
    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"
    DATE = "date"
    BOOLEAN = "boolean"
    SELECT = "select"
    TEXTAREA = "textarea"
    RADIO = "radio"
    SWITCH = "switch"


# ============================================================================
# Mapping: entity field type (CP01) → UI FieldType
# ============================================================================

_FIELD_TYPE_MAP: dict[str, FieldType] = {
    "str": FieldType.TEXT,
    "int": FieldType.NUMBER,
    "float": FieldType.NUMBER,
    "bool": FieldType.BOOLEAN,
    "email": FieldType.EMAIL,
    "date": FieldType.DATE,
    "datetime": FieldType.DATE,
    "text": FieldType.TEXTAREA,
}


# ============================================================================
# TableColumn — Cột trong DataTable
# ============================================================================


@dataclass
class TableColumn:
    """
    Column định nghĩa cho DataTable.

    Attributes:
        field_name: Tên field trong entity
        label: Nhãn hiển thị
        sortable: Có thể sort theo cột này không
        filterable: Có thể filter theo cột này không
    """
    field_name: str
    label: str
    sortable: bool = True
    filterable: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialise ra dict."""
        return {
            "field_name": self.field_name,
            "label": self.label,
            "sortable": self.sortable,
            "filterable": self.filterable,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TableColumn":
        """Deserialise từ dict."""
        return cls(
            field_name=data["field_name"],
            label=data.get("label", data["field_name"]),
            sortable=data.get("sortable", True),
            filterable=data.get("filterable", False),
        )


# ============================================================================
# FormFieldSpec — Spec cho một form field
# ============================================================================


@dataclass
class FormFieldSpec:
    """
    Spec cho một form field trong UI.

    Attributes:
        field_name: Tên field trong entity
        field_type: Loại field (text, number, email, ...)
        label: Nhãn hiển thị
        binding_path: Đường dẫn binding (ví dụ: user.email)
        required: Bắt buộc điền không
        min_value: Giá trị tối thiểu (cho number)
        max_value: Giá trị tối đa (cho number)
        options: Danh sách option (cho select/radio)
    """
    field_name: str
    field_type: FieldType
    label: str
    binding_path: str
    required: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    options: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate FormFieldSpec sau khi khởi tạo."""
        # Kiểm tra field_name và binding_path không rỗng
        if not self.field_name or not self.field_name.strip():
            EM.raise_error(
                ErrorCode.CP19_MISSING_FORM_BINDING,
                field=self.field_name,
            )
        if not self.binding_path or not self.binding_path.strip():
            EM.raise_error(
                ErrorCode.CP19_MISSING_FORM_BINDING,
                field=self.field_name,
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialise ra dict."""
        return {
            "field_name": self.field_name,
            "field_type": self.field_type.value,
            "label": self.label,
            "binding_path": self.binding_path,
            "required": self.required,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "options": self.options,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FormFieldSpec":
        """Deserialise từ dict."""
        field_type_str = data.get("field_type", "text")
        return cls(
            field_name=data["field_name"],
            field_type=FieldType(field_type_str),
            label=data.get("label", data["field_name"]),
            binding_path=data["binding_path"],
            required=data.get("required", False),
            min_value=data.get("min_value"),
            max_value=data.get("max_value"),
            options=data.get("options", []),
        )

    @classmethod
    def from_entity_field(
        cls,
        entity_id: str,
        field_def: dict[str, Any],
    ) -> "FormFieldSpec":
        """
        Tạo FormFieldSpec tự động từ entity field definition của CP01.

        Args:
            entity_id: Tên entity (ví dụ: "Order")
            field_def: Dict field từ CP01 (name, type, ...)

        Returns:
            FormFieldSpec instance
        """
        name = field_def["name"]
        ftype = field_def.get("type", "str")
        ui_type = _FIELD_TYPE_MAP.get(ftype, FieldType.TEXT)
        label = name.replace("_", " ").title()
        binding_path = f"{entity_id.lower()}.{name}"

        return cls(
            field_name=name,
            field_type=ui_type,
            label=label,
            binding_path=binding_path,
            required=field_def.get("required", False),
        )


# ============================================================================
# TableSpec — Spec cho DataTable
# ============================================================================


@dataclass
class TableSpec:
    """
    Spec cho Data Table trong UI.

    Attributes:
        entity_id: Tên entity hiển thị
        columns: Danh sách các cột
        sortable: Có thể sort không
        paginated: Có phân trang không
        page_size: Số dòng mỗi trang
        filterable: Có thể filter không
    """
    entity_id: str
    columns: list[TableColumn]
    sortable: bool = True
    paginated: bool = True
    page_size: int = 20
    filterable: bool = False

    def __post_init__(self) -> None:
        """Validate TableSpec sau khi khởi tạo."""
        if not self.entity_id or not self.entity_id.strip():
            EM.raise_error(
                ErrorCode.CP19_EMPTY_TABLE_COLUMNS,
                entity=self.entity_id,
            )
        if not self.columns:
            EM.raise_error(
                ErrorCode.CP19_EMPTY_TABLE_COLUMNS,
                entity=self.entity_id,
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialise ra dict."""
        return {
            "entity_id": self.entity_id,
            "columns": [c.to_dict() for c in self.columns],
            "sortable": self.sortable,
            "paginated": self.paginated,
            "page_size": self.page_size,
            "filterable": self.filterable,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TableSpec":
        """Deserialise từ dict."""
        columns_data = data.get("columns", [])
        return cls(
            entity_id=data["entity_id"],
            columns=[TableColumn.from_dict(c) for c in columns_data],
            sortable=data.get("sortable", True),
            paginated=data.get("paginated", True),
            page_size=data.get("page_size", 20),
            filterable=data.get("filterable", False),
        )

    @classmethod
    def from_entity(cls, entity: dict[str, Any]) -> "TableSpec":
        """
        Tạo TableSpec tự động từ entity definition của CP01.

        Args:
            entity: Dict entity từ CP01 (id, fields, ...)

        Returns:
            TableSpec instance
        """
        entity_id = entity["id"]
        columns = []
        for fdef in entity.get("fields", []):
            name = fdef["name"]
            label = name.replace("_", " ").title()
            columns.append(TableColumn(field_name=name, label=label))

        if not columns:
            # Thêm column mặc định nếu entity không có fields
            columns.append(TableColumn(field_name="id", label="ID"))

        return cls(entity_id=entity_id, columns=columns)


# ============================================================================
# ComponentSpec — Spec cho một UI component
# ============================================================================


@dataclass
class ComponentSpec:
    """
    Spec cho một UI component để generate.

    Attributes:
        component_type: Loại component (form_field, data_table, card_list, dialog)
        entity_id: Tên entity liên kết
        title: Tiêu đề (cho dialog/card_list)
        properties: Thuộc tính bổ sung (grid_cols, ...)
        fields: Danh sách FormFieldSpec (cho form_field)
        table_spec: TableSpec (cho data_table)
    """
    component_type: ComponentType
    entity_id: str
    title: Optional[str] = None
    properties: dict[str, Any] = field(default_factory=dict)
    fields: list[FormFieldSpec] = field(default_factory=list)
    table_spec: Optional[TableSpec] = None

    def __post_init__(self) -> None:
        """Validate ComponentSpec sau khi khởi tạo."""
        if not self.entity_id or not self.entity_id.strip():
            EM.raise_error(
                ErrorCode.CP19_INVALID_COMPONENT_TYPE,
                entity=self.entity_id,
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialise ra dict."""
        result: dict[str, Any] = {
            "component_type": self.component_type.value,
            "entity_id": self.entity_id,
            "title": self.title,
            "properties": self.properties,
        }
        if self.fields:
            result["fields"] = [f.to_dict() for f in self.fields]
        if self.table_spec:
            result["table_spec"] = self.table_spec.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComponentSpec":
        """Deserialise từ dict."""
        comp_type = ComponentType(data["component_type"])
        entity_id = data.get("entity_id", "")

        result: dict[str, Any] = {
            "component_type": comp_type,
            "entity_id": entity_id,
            "title": data.get("title"),
            "properties": data.get("properties", {}),
        }

        if "fields" in data:
            result["fields"] = [FormFieldSpec.from_dict(f) for f in data["fields"]]

        if "table_spec" in data:
            result["table_spec"] = TableSpec.from_dict(data["table_spec"])

        return cls(**result)

    @classmethod
    def generate_form(cls, entity: dict[str, Any]) -> "ComponentSpec":
        """
        Tạo ComponentSpec cho form field tự động từ entity.

        Args:
            entity: Dict entity từ CP01 (id, fields, ...)

        Returns:
            ComponentSpec với type FORM_FIELD
        """
        entity_id = entity["id"]
        fields = []
        for fdef in entity.get("fields", []):
            fields.append(FormFieldSpec.from_entity_field(entity_id, fdef))

        return cls(
            component_type=ComponentType.FORM_FIELD,
            entity_id=entity_id,
            fields=fields,
        )

    @classmethod
    def generate_table(cls, entity: dict[str, Any]) -> "ComponentSpec":
        """
        Tạo ComponentSpec cho data table tự động từ entity.

        Args:
            entity: Dict entity từ CP01 (id, fields, ...)

        Returns:
            ComponentSpec với type DATA_TABLE
        """
        entity_id = entity["id"]
        table_spec = TableSpec.from_entity(entity)

        return cls(
            component_type=ComponentType.DATA_TABLE,
            entity_id=entity_id,
            table_spec=table_spec,
        )

    @classmethod
    def generate_card_list(cls, entity: dict[str, Any]) -> "ComponentSpec":
        """
        Tạo ComponentSpec cho card list tự động từ entity.

        Args:
            entity: Dict entity từ CP01 (id, fields, ...)

        Returns:
            ComponentSpec với type CARD_LIST
        """
        entity_id = entity["id"]
        return cls(
            component_type=ComponentType.CARD_LIST,
            entity_id=entity_id,
            title=f"{entity_id}s",
            properties={"grid_cols": 3},
        )

    @classmethod
    def generate_dialog(cls, entity: dict[str, Any], title: str | None = None) -> "ComponentSpec":
        """
        Tạo ComponentSpec cho dialog tự động từ entity.

        Args:
            entity: Dict entity từ CP01 (id, fields, ...)
            title: Tiêu đề dialog (mặc định: entity_id Detail)

        Returns:
            ComponentSpec với type DIALOG
        """
        entity_id = entity["id"]
        dialog_title = title or f"{entity_id} Detail"

        return cls(
            component_type=ComponentType.DIALOG,
            entity_id=entity_id,
            title=dialog_title,
        )


__all__ = [
    # Enums
    "ComponentType",
    "FieldType",
    # Models
    "TableColumn",
    "FormFieldSpec",
    "TableSpec",
    "ComponentSpec",
]
