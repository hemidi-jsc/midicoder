# coding: utf-8
"""
UI Component Models (CP19).

Module này cung cấp các models cho UI Component Generator:
- ComponentSpec: spec cho một UI component
- FormFieldSpec: spec cho một form field
- TableSpec: spec cho data table
- FormBuilderSpec: spec cho dynamic form builder
- ThemeSpec: spec cho theme / design tokens
- ComponentType: enum cho loại component (~50 types)
- FieldType: enum cho loại form field

Author: Midicoder Team
Version: 2.0.0
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

    # ── Data Input ──────────────────────────────────────────────
    FORM_FIELD = "form_field"
    FORM_BUILDER = "form_builder"
    INPUT = "input"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SWITCH = "switch"
    SLIDER = "slider"
    DATE_PICKER = "date_picker"
    DATETIME_PICKER = "datetime_picker"
    COLOR_PICKER = "color_picker"
    FILE_UPLOAD = "file_upload"
    AUTOCOMPLETE = "autocomplete"
    RICH_TEXT_EDITOR = "rich_text_editor"

    # ── Data Display ───────────────────────────────────────────
    DATA_TABLE = "data_table"
    CARD = "card"
    CARD_LIST = "card_list"
    LIST = "list"
    TIMELINE = "timeline"
    AVATAR = "avatar"
    BADGE = "badge"
    CHIP = "chip"
    TOOLTIP = "tooltip"
    POPOVER = "popover"
    DESCRIPTION_LIST = "description_list"

    # ── Feedback ───────────────────────────────────────────────
    ALERT = "alert"
    SNACKBAR = "snackbar"
    TOAST = "toast"
    DIALOG = "dialog"
    MODAL = "modal"
    PROGRESS_BAR = "progress_bar"
    LINEAR_PROGRESS = "linear_progress"
    CIRCULAR_PROGRESS = "circular_progress"
    SKELETON = "skeleton"
    SPINNER = "spinner"

    # ── Navigation ─────────────────────────────────────────────
    NAVBAR = "navbar"
    SIDEBAR = "sidebar"
    BREADCRUMBS = "breadcrumbs"
    PAGINATION = "pagination"
    TABS = "tabs"
    STEPPER = "stepper"
    MENU = "menu"
    TREE_VIEW = "tree_view"

    # ── Layout ─────────────────────────────────────────────────
    CONTAINER = "container"
    GRID = "grid"
    ROW = "row"
    COLUMN = "column"
    BOX = "box"
    DIVIDER = "divider"
    SPACER = "spacer"
    FLEX = "flex"

    # ── Surface ────────────────────────────────────────────────
    DRAWER = "drawer"
    ACCORDION = "accordion"
    EXPANSION_PANEL = "expansion_panel"

    # ── Utility ────────────────────────────────────────────────
    THEME_PROVIDER = "theme_provider"
    DESIGN_TOKENS = "design_tokens"
    ICON = "icon"
    IMAGE = "image"
    BUTTON = "button"
    ICON_BUTTON = "icon_button"
    BADGE_BUTTON = "badge_button"


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

# Mapping: component category for template organization
_COMPONENT_CATEGORIES: dict[ComponentType, str] = {
    # Data Input
    ComponentType.FORM_FIELD: "data-input",
    ComponentType.FORM_BUILDER: "data-input",
    ComponentType.INPUT: "data-input",
    ComponentType.TEXTAREA: "data-input",
    ComponentType.SELECT: "data-input",
    ComponentType.CHECKBOX: "data-input",
    ComponentType.RADIO: "data-input",
    ComponentType.SWITCH: "data-input",
    ComponentType.SLIDER: "data-input",
    ComponentType.DATE_PICKER: "data-input",
    ComponentType.DATETIME_PICKER: "data-input",
    ComponentType.COLOR_PICKER: "data-input",
    ComponentType.FILE_UPLOAD: "data-input",
    ComponentType.AUTOCOMPLETE: "data-input",
    ComponentType.RICH_TEXT_EDITOR: "data-input",
    # Data Display
    ComponentType.DATA_TABLE: "data-display",
    ComponentType.CARD: "data-display",
    ComponentType.CARD_LIST: "data-display",
    ComponentType.LIST: "data-display",
    ComponentType.TIMELINE: "data-display",
    ComponentType.AVATAR: "data-display",
    ComponentType.BADGE: "data-display",
    ComponentType.CHIP: "data-display",
    ComponentType.TOOLTIP: "data-display",
    ComponentType.POPOVER: "data-display",
    ComponentType.DESCRIPTION_LIST: "data-display",
    # Feedback
    ComponentType.ALERT: "feedback",
    ComponentType.SNACKBAR: "feedback",
    ComponentType.TOAST: "feedback",
    ComponentType.DIALOG: "feedback",
    ComponentType.MODAL: "feedback",
    ComponentType.PROGRESS_BAR: "feedback",
    ComponentType.LINEAR_PROGRESS: "feedback",
    ComponentType.CIRCULAR_PROGRESS: "feedback",
    ComponentType.SKELETON: "feedback",
    ComponentType.SPINNER: "feedback",
    # Navigation
    ComponentType.NAVBAR: "navigation",
    ComponentType.SIDEBAR: "navigation",
    ComponentType.BREADCRUMBS: "navigation",
    ComponentType.PAGINATION: "navigation",
    ComponentType.TABS: "navigation",
    ComponentType.STEPPER: "navigation",
    ComponentType.MENU: "navigation",
    ComponentType.TREE_VIEW: "navigation",
    # Layout
    ComponentType.CONTAINER: "layout",
    ComponentType.GRID: "layout",
    ComponentType.ROW: "layout",
    ComponentType.COLUMN: "layout",
    ComponentType.BOX: "layout",
    ComponentType.DIVIDER: "layout",
    ComponentType.SPACER: "layout",
    ComponentType.FLEX: "layout",
    # Surface
    ComponentType.DRAWER: "surface",
    ComponentType.ACCORDION: "surface",
    ComponentType.EXPANSION_PANEL: "surface",
    # Utility
    ComponentType.THEME_PROVIDER: "utility",
    ComponentType.DESIGN_TOKENS: "utility",
    ComponentType.ICON: "utility",
    ComponentType.IMAGE: "utility",
    ComponentType.BUTTON: "utility",
    ComponentType.ICON_BUTTON: "utility",
    ComponentType.BADGE_BUTTON: "utility",
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
        aria_label: ARIA label cho accessibility (Phase 4)
        aria_described_by: Element ID mô tả field (Phase 4)
        i18n_key: i18n translation key (Phase 5)
    """
    field_name: str
    field_type: FieldType
    label: str
    binding_path: str
    required: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    options: list[str] = field(default_factory=list)
    # Phase 4: Accessibility
    aria_label: Optional[str] = None
    aria_described_by: Optional[str] = None
    # Phase 5: i18n
    i18n_key: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate FormFieldSpec sau khi khởi tạo."""
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
        result: dict[str, Any] = {
            "field_name": self.field_name,
            "field_type": self.field_type.value,
            "label": self.label,
            "binding_path": self.binding_path,
            "required": self.required,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "options": self.options,
        }
        if self.aria_label:
            result["aria_label"] = self.aria_label
        if self.aria_described_by:
            result["aria_described_by"] = self.aria_described_by
        if self.i18n_key:
            result["i18n_key"] = self.i18n_key
        return result

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
            aria_label=data.get("aria_label"),
            aria_described_by=data.get("aria_described_by"),
            i18n_key=data.get("i18n_key"),
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
            columns.append(TableColumn(field_name="id", label="ID"))

        return cls(entity_id=entity_id, columns=columns)


# ============================================================================
# ConditionalRule — Rule cho conditional fields trong Form Builder
# ============================================================================


@dataclass
class ConditionalRule:
    """
    Rule để hiển thị/ẩn field dựa trên value của field khác.

    Attributes:
        target_field: Field sẽ bị ẩn/hiện
        condition_field: Field điều kiện
        condition_operator: Toán tử so sánh (eq, neq, contains, gt, lt)
        condition_value: Giá trị so sánh
        show: True = hiện, False = ẩn
    """
    target_field: str
    condition_field: str
    condition_operator: str = "eq"
    condition_value: Any = None
    show: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_field": self.target_field,
            "condition_field": self.condition_field,
            "condition_operator": self.condition_operator,
            "condition_value": self.condition_value,
            "show": self.show,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConditionalRule":
        return cls(
            target_field=data["target_field"],
            condition_field=data["condition_field"],
            condition_operator=data.get("condition_operator", "eq"),
            condition_value=data.get("condition_value"),
            show=data.get("show", True),
        )


# ============================================================================
# FormBuilderSpec — Spec cho Dynamic Form Builder
# ============================================================================


@dataclass
class FormBuilderSpec:
    """
    Spec cho Dynamic Form Builder — sinh form động từ schema.

    Attributes:
        entity_id: Tên entity
        layout: Form layout (single_column, two_column, wizard)
        fields: Danh sách FormFieldSpec
        conditional_rules: Danh sách conditional rules
        validation_schema: JSON Schema validation dict
    """
    entity_id: str
    layout: str = "single_column"
    fields: list[FormFieldSpec] = field(default_factory=list)
    conditional_rules: list[ConditionalRule] = field(default_factory=list)
    validation_schema: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "layout": self.layout,
            "fields": [f.to_dict() for f in self.fields],
            "conditional_rules": [r.to_dict() for r in self.conditional_rules],
            "validation_schema": self.validation_schema,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FormBuilderSpec":
        return cls(
            entity_id=data["entity_id"],
            layout=data.get("layout", "single_column"),
            fields=[FormFieldSpec.from_dict(f) for f in data.get("fields", [])],
            conditional_rules=[ConditionalRule.from_dict(r) for r in data.get("conditional_rules", [])],
            validation_schema=data.get("validation_schema", {}),
        )

    @classmethod
    def from_entity(cls, entity: dict[str, Any], layout: str = "single_column") -> "FormBuilderSpec":
        """Tạo FormBuilderSpec từ entity definition của CP01."""
        entity_id = entity["id"]
        fields = []
        for fdef in entity.get("fields", []):
            fields.append(FormFieldSpec.from_entity_field(entity_id, fdef))
        return cls(entity_id=entity_id, layout=layout, fields=fields)


# ============================================================================
# ThemeSpec — Spec cho Theme / Design Tokens
# ============================================================================


@dataclass
class ThemeSpec:
    """
    Spec cho Theme / Design Tokens.

    Attributes:
        name: Tên theme (default, dark, custom)
        primary_color: Màu primary
        secondary_color: Màu secondary
        font_family: Font family
        border_radius: Border radius
        dark_mode: Có support dark mode không
    """
    name: str = "default"
    primary_color: str = "#1976d2"
    secondary_color: str = "#9c27b0"
    font_family: str = '"Roboto", "Helvetica", "Arial", sans-serif'
    border_radius: str = "4px"
    dark_mode: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "font_family": self.font_family,
            "border_radius": self.border_radius,
            "dark_mode": self.dark_mode,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ThemeSpec":
        return cls(
            name=data.get("name", "default"),
            primary_color=data.get("primary_color", "#1976d2"),
            secondary_color=data.get("secondary_color", "#9c27b0"),
            font_family=data.get("font_family", '"Roboto", "Helvetica", "Arial", sans-serif'),
            border_radius=data.get("border_radius", "4px"),
            dark_mode=data.get("dark_mode", False),
        )


# ============================================================================
# ComponentSpec — Spec cho một UI component
# ============================================================================


@dataclass
class ComponentSpec:
    """
    Spec cho một UI component để generate.

    Attributes:
        component_type: Loại component
        entity_id: Tên entity liên kết
        title: Tiêu đề (cho dialog/card_list)
        properties: Thuộc tính bổ sung (grid_cols, variant, size, ...)
        fields: Danh sách FormFieldSpec (cho form_field)
        table_spec: TableSpec (cho data_table)
        form_builder_spec: FormBuilderSpec (cho form_builder)
        theme_spec: ThemeSpec (cho theme_provider)
        variants: Danh sách variant names ("outlined", "contained", "text")
        size: Component size ("small", "medium", "large")
        accessible: Có inject ARIA attributes không (Phase 4)
        aria_label: ARIA label override (Phase 4)
        i18n_key: i18n translation key (Phase 5)
        locale: Default locale (Phase 5)
    """
    component_type: ComponentType
    entity_id: str
    title: Optional[str] = None
    properties: dict[str, Any] = field(default_factory=dict)
    fields: list[FormFieldSpec] = field(default_factory=list)
    table_spec: Optional[TableSpec] = None
    form_builder_spec: Optional[FormBuilderSpec] = None
    theme_spec: Optional[ThemeSpec] = None
    variants: list[str] = field(default_factory=list)
    size: str = "medium"
    # Phase 4: Accessibility
    accessible: bool = True
    aria_label: Optional[str] = None
    # Phase 5: i18n
    i18n_key: Optional[str] = None
    locale: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate ComponentSpec sau khi khởi tạo."""
        if not self.entity_id or not self.entity_id.strip():
            EM.raise_error(
                ErrorCode.CP19_INVALID_COMPONENT_TYPE,
                entity=self.entity_id,
            )

    @property
    def category(self) -> str:
        """Lấy category của component (data-input, data-display, ...)."""
        return _COMPONENT_CATEGORIES.get(self.component_type, "utility")

    def to_dict(self) -> dict[str, Any]:
        """Serialise ra dict."""
        result: dict[str, Any] = {
            "component_type": self.component_type.value,
            "entity_id": self.entity_id,
            "title": self.title,
            "properties": self.properties,
            "variants": self.variants,
            "size": self.size,
            "accessible": self.accessible,
        }
        if self.aria_label:
            result["aria_label"] = self.aria_label
        if self.i18n_key:
            result["i18n_key"] = self.i18n_key
        if self.locale:
            result["locale"] = self.locale
        if self.fields:
            result["fields"] = [f.to_dict() for f in self.fields]
        if self.table_spec:
            result["table_spec"] = self.table_spec.to_dict()
        if self.form_builder_spec:
            result["form_builder_spec"] = self.form_builder_spec.to_dict()
        if self.theme_spec:
            result["theme_spec"] = self.theme_spec.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComponentSpec":
        """Deserialise từ dict."""
        comp_type_str = data.get("component_type", "form_field")
        try:
            comp_type = ComponentType(comp_type_str)
        except ValueError:
            comp_type = ComponentType.FORM_FIELD

        result: dict[str, Any] = {
            "component_type": comp_type,
            "entity_id": data.get("entity_id", ""),
            "title": data.get("title"),
            "properties": data.get("properties", {}),
            "variants": data.get("variants", []),
            "size": data.get("size", "medium"),
            "accessible": data.get("accessible", True),
            "aria_label": data.get("aria_label"),
            "i18n_key": data.get("i18n_key"),
            "locale": data.get("locale"),
        }

        if "fields" in data:
            result["fields"] = [FormFieldSpec.from_dict(f) for f in data["fields"]]

        if "table_spec" in data:
            result["table_spec"] = TableSpec.from_dict(data["table_spec"])

        if "form_builder_spec" in data:
            result["form_builder_spec"] = FormBuilderSpec.from_dict(data["form_builder_spec"])

        if "theme_spec" in data:
            result["theme_spec"] = ThemeSpec.from_dict(data["theme_spec"])

        return cls(**result)

    # ── Factory methods ──────────────────────────────────────────

    @classmethod
    def generate_form(cls, entity: dict[str, Any]) -> "ComponentSpec":
        """Tạo ComponentSpec cho form field tự động từ entity."""
        entity_id = entity["id"]
        fields = []
        for fdef in entity.get("fields", []):
            fields.append(FormFieldSpec.from_entity_field(entity_id, fdef))
        return cls(component_type=ComponentType.FORM_FIELD, entity_id=entity_id, fields=fields)

    @classmethod
    def generate_table(cls, entity: dict[str, Any]) -> "ComponentSpec":
        """Tạo ComponentSpec cho data table tự động từ entity."""
        entity_id = entity["id"]
        table_spec = TableSpec.from_entity(entity)
        return cls(component_type=ComponentType.DATA_TABLE, entity_id=entity_id, table_spec=table_spec)

    @classmethod
    def generate_card_list(cls, entity: dict[str, Any]) -> "ComponentSpec":
        """Tạo ComponentSpec cho card list tự động từ entity."""
        entity_id = entity["id"]
        return cls(
            component_type=ComponentType.CARD_LIST,
            entity_id=entity_id,
            title=f"{entity_id}s",
            properties={"grid_cols": 3},
        )

    @classmethod
    def generate_dialog(cls, entity: dict[str, Any], title: str | None = None) -> "ComponentSpec":
        """Tạo ComponentSpec cho dialog tự động từ entity."""
        entity_id = entity["id"]
        dialog_title = title or f"{entity_id} Detail"
        return cls(component_type=ComponentType.DIALOG, entity_id=entity_id, title=dialog_title)

    @classmethod
    def generate_all_for_entity(cls, entity: dict[str, Any]) -> list["ComponentSpec"]:
        """Tạo TẤT CẢ component specs cho một entity."""
        return [
            cls.generate_form(entity),
            cls.generate_table(entity),
            cls.generate_card_list(entity),
            cls.generate_dialog(entity),
        ]

    @classmethod
    def generate_generic(cls, component_type: str, entity_id: str, **kwargs: Any) -> "ComponentSpec":
        """Tạo ComponentSpec generic cho bất kỳ component type nào."""
        try:
            ct = ComponentType(component_type)
        except ValueError:
            ct = ComponentType.FORM_FIELD
        return cls(
            component_type=ct,
            entity_id=entity_id,
            title=kwargs.get("title", entity_id.title()),
            properties=kwargs.get("properties", {}),
            variants=kwargs.get("variants", []),
            size=kwargs.get("size", "medium"),
        )


__all__ = [
    # Enums
    "ComponentType",
    "FieldType",
    # Mapping
    "_COMPONENT_CATEGORIES",
    # Models
    "TableColumn",
    "FormFieldSpec",
    "TableSpec",
    "ConditionalRule",
    "FormBuilderSpec",
    "ThemeSpec",
    "ComponentSpec",
]
