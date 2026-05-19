# coding: utf-8
"""
React UI Component Emitter (CP19).

Module này cung cấp ReactUIEmitter để emit reusable UI components
cho TẤT CẢ 50+ component types × 5 UI frameworks.

Templates: stacks/react/core/cp19_ui_components/**/*.tsx.jinja2

Usage:
    from midicoder.emitters.core.cp19_ui_components.react import ReactUIEmitter
    emitter = ReactUIEmitter(ui_framework="tailwind")
    files = emitter.generate(components, output_dir)

Author: Midicoder Team
Version: 2.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.cp19_ui_components.models import ComponentSpec, ComponentType

# Resolve template directory relative to this package
_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent
_TEMPLATE_DIR = _PACKAGE_DIR / "stacks" / "react" / "core" / "cp19_ui_components"


# Mapping: ComponentType → (subdirectory, template_file, output_file)
# subdirectory = None means root-level template
_COMPONENT_TEMPLATE_MAP: dict[ComponentType, tuple[str | None, str, str]] = {
    # ── Layout ──────────────────────────────────────────────────
    ComponentType.CONTAINER:  ("layout",  "Container.tsx.jinja2",  "Container.tsx"),
    ComponentType.GRID:       ("layout",  "Grid.tsx.jinja2",       "Grid.tsx"),
    ComponentType.ROW:        ("layout",  "Row.tsx.jinja2",        "Row.tsx"),
    ComponentType.COLUMN:     ("layout",  "Column.tsx.jinja2",     "Column.tsx"),
    ComponentType.BOX:        ("layout",  "Box.tsx.jinja2",        "Box.tsx"),
    ComponentType.DIVIDER:    ("layout",  "Divider.tsx.jinja2",    "Divider.tsx"),
    ComponentType.SPACER:     ("layout",  "Spacer.tsx.jinja2",     "Spacer.tsx"),
    ComponentType.FLEX:       ("layout",  "Flex.tsx.jinja2",       "Flex.tsx"),

    # ── Navigation ──────────────────────────────────────────────
    ComponentType.NAVBAR:       ("navigation", "Navbar.tsx.jinja2",       "Navbar.tsx"),
    ComponentType.SIDEBAR:      ("navigation", "Sidebar.tsx.jinja2",      "Sidebar.tsx"),
    ComponentType.BREADCRUMBS:  ("navigation", "Breadcrumbs.tsx.jinja2",  "Breadcrumbs.tsx"),
    ComponentType.PAGINATION:   ("navigation", "Pagination.tsx.jinja2",   "Pagination.tsx"),
    ComponentType.TABS:         ("navigation", "Tabs.tsx.jinja2",         "Tabs.tsx"),
    ComponentType.STEPPER:      ("navigation", "Stepper.tsx.jinja2",      "Stepper.tsx"),
    ComponentType.MENU:         ("navigation", "Menu.tsx.jinja2",         "Menu.tsx"),
    ComponentType.TREE_VIEW:    ("navigation", "TreeView.tsx.jinja2",     "TreeView.tsx"),

    # ── Data Display ────────────────────────────────────────────
    ComponentType.DATA_TABLE:       ("data-display", "DataTable.tsx.jinja2",       "DataTable.tsx"),
    ComponentType.CARD:             ("data-display", "Card.tsx.jinja2",            "Card.tsx"),
    ComponentType.CARD_LIST:        ("data-display", "Card.tsx.jinja2",             "CardList.tsx"),
    ComponentType.LIST:             ("data-display", "List.tsx.jinja2",            "List.tsx"),
    ComponentType.TIMELINE:         ("data-display", "Timeline.tsx.jinja2",        "Timeline.tsx"),
    ComponentType.AVATAR:           ("data-display", "Avatar.tsx.jinja2",          "Avatar.tsx"),
    ComponentType.BADGE:            ("data-display", "Badge.tsx.jinja2",           "Badge.tsx"),
    ComponentType.CHIP:             ("data-display", "Chip.tsx.jinja2",            "Chip.tsx"),
    ComponentType.TOOLTIP:          ("data-display", "Tooltip.tsx.jinja2",         "Tooltip.tsx"),
    ComponentType.POPOVER:          ("data-display", "Popover.tsx.jinja2",         "Popover.tsx"),
    ComponentType.DESCRIPTION_LIST: ("data-display", "DescriptionList.tsx.jinja2", "DescriptionList.tsx"),

    # ── Data Input ──────────────────────────────────────────────
    ComponentType.FORM_FIELD:       ("data-input", "FormField.tsx.jinja2",       "FormField.tsx"),
    ComponentType.FORM_BUILDER:     ("data-input", "FormBuilder.tsx.jinja2",     "FormBuilder.tsx"),
    ComponentType.INPUT:            ("data-input", "Input.tsx.jinja2",           "Input.tsx"),
    ComponentType.TEXTAREA:         ("data-input", "Textarea.tsx.jinja2",        "Textarea.tsx"),
    ComponentType.SELECT:           ("data-input", "Select.tsx.jinja2",          "Select.tsx"),
    ComponentType.CHECKBOX:         ("data-input", "Checkbox.tsx.jinja2",        "Checkbox.tsx"),
    ComponentType.RADIO:            ("data-input", "Radio.tsx.jinja2",           "Radio.tsx"),
    ComponentType.SWITCH:           ("data-input", "Switch.tsx.jinja2",          "Switch.tsx"),
    ComponentType.SLIDER:           ("data-input", "Slider.tsx.jinja2",          "Slider.tsx"),
    ComponentType.DATE_PICKER:      ("data-input", "DatePicker.tsx.jinja2",      "DatePicker.tsx"),
    ComponentType.DATETIME_PICKER:  ("data-input", "DateTimePicker.tsx.jinja2",  "DateTimePicker.tsx"),
    ComponentType.COLOR_PICKER:     ("data-input", "ColorPicker.tsx.jinja2",     "ColorPicker.tsx"),
    ComponentType.FILE_UPLOAD:      ("data-input", "FileUpload.tsx.jinja2",      "FileUpload.tsx"),
    ComponentType.AUTOCOMPLETE:     ("data-input", "Autocomplete.tsx.jinja2",    "Autocomplete.tsx"),
    ComponentType.RICH_TEXT_EDITOR: ("data-input", "RichTextEditor.tsx.jinja2",  "RichTextEditor.tsx"),

    # ── Feedback ────────────────────────────────────────────────
    ComponentType.ALERT:            ("feedback", "Alert.tsx.jinja2",            "Alert.tsx"),
    ComponentType.SNACKBAR:         ("feedback", "Snackbar.tsx.jinja2",         "Snackbar.tsx"),
    ComponentType.TOAST:            ("feedback", "Toast.tsx.jinja2",            "Toast.tsx"),
    ComponentType.DIALOG:           ("feedback", "Dialog.tsx.jinja2",           "Dialog.tsx"),
    ComponentType.MODAL:            ("feedback", "Modal.tsx.jinja2",            "Modal.tsx"),
    ComponentType.PROGRESS_BAR:     ("feedback", "ProgressBar.tsx.jinja2",      "ProgressBar.tsx"),
    ComponentType.LINEAR_PROGRESS:  ("feedback", "LinearProgress.tsx.jinja2",   "LinearProgress.tsx"),
    ComponentType.CIRCULAR_PROGRESS: ("feedback", "CircularProgress.tsx.jinja2", "CircularProgress.tsx"),
    ComponentType.SKELETON:         ("feedback", "Skeleton.tsx.jinja2",         "Skeleton.tsx"),
    ComponentType.SPINNER:          ("feedback", "Spinner.tsx.jinja2",          "Spinner.tsx"),

    # ── Surface ─────────────────────────────────────────────────
    ComponentType.DRAWER:           ("surface", "Drawer.tsx.jinja2",           "Drawer.tsx"),
    ComponentType.ACCORDION:        ("surface", "Accordion.tsx.jinja2",        "Accordion.tsx"),
    ComponentType.EXPANSION_PANEL:  ("surface", "ExpansionPanel.tsx.jinja2",   "ExpansionPanel.tsx"),

    # ── Utility ─────────────────────────────────────────────────
    ComponentType.THEME_PROVIDER:   ("utility", "ThemeProvider.tsx.jinja2",    "ThemeProvider.tsx"),
    ComponentType.DESIGN_TOKENS:    ("utility", "DesignTokens.ts.jinja2",      "DesignTokens.ts"),
    ComponentType.ICON:             ("utility", "Icon.tsx.jinja2",             "Icon.tsx"),
    ComponentType.IMAGE:            ("utility", "Image.tsx.jinja2",            "Image.tsx"),
    ComponentType.BUTTON:           ("utility", "Button.tsx.jinja2",           "Button.tsx"),
    ComponentType.ICON_BUTTON:      ("utility", "IconButton.tsx.jinja2",       "IconButton.tsx"),
    ComponentType.BADGE_BUTTON:     ("utility", "BadgeButton.tsx.jinja2",      "BadgeButton.tsx"),

    # ── Service Layer (Phase 4) ─────────────────────────────────
    ComponentType.API_HOOKS:        ("service", "use-api.ts.jinja2",           "use-api.ts"),

    # ── Module Structure (Phase 5) ──────────────────────────────
    ComponentType.APP_ROUTING:      ("module", "app-routes.tsx.jinja2",        "app-routes.tsx"),
}


@dataclass
class GeneratedFile:
    """File đã generate."""
    path: Path
    content: str
    template: str


class ReactUIEmitter:
    """Emitter cho React UI Components tái sử dụng.

    Sinh ra 50+ component types × 5 UI frameworks.
    """

    SUPPORTED_UI_FRAMEWORKS = ["material", "tailwind", "bootstrap", "antd", "carbon"]

    def __init__(self, ui_framework: str = "tailwind") -> None:
        """Khởi tạo ReactUIEmitter.

        Args:
            ui_framework: UI framework (material, tailwind, bootstrap, antd, carbon)
        """
        if ui_framework not in self.SUPPORTED_UI_FRAMEWORKS:
            raise ValueError("UI framework '" + ui_framework + "' không được hỗ trợ.")
        self.ui_framework = ui_framework

        self._template_env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
            # Custom delimiters to avoid conflict with React/JSX {{ }} expressions
            variable_start_string="{[{",
            variable_end_string="}]}",
        )

    def _render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """Render jinja2 template với context."""
        try:
            template = self._template_env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            return f"// {template_name} - template not found\n"

    def _get_template_path(self, component_type: ComponentType) -> tuple[str | None, str]:
        """Lấy (subdirectory, template_file) cho ComponentType."""
        mapping = _COMPONENT_TEMPLATE_MAP.get(component_type)
        if mapping:
            subdir, template_file, _ = mapping
            return subdir, template_file
        safe_name = component_type.value.replace("_", "-") + ".tsx.jinja2"
        return None, safe_name

    def _get_output_path(self, component_type: ComponentType) -> str:
        """Lấy output filename cho ComponentType."""
        mapping = _COMPONENT_TEMPLATE_MAP.get(component_type)
        if mapping:
            _, _, output_file = mapping
            return output_file
        return component_type.value.replace("_", "-") + ".tsx"

    def generate(
        self,
        components: list[ComponentSpec],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Sinh React UI components từ danh sách ComponentSpec.

        Args:
            components: Danh sách ComponentSpec
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []

        # Group components by type, deduplicate
        seen_types: set[ComponentType] = set()
        components_by_type: dict[ComponentType, list[ComponentSpec]] = {}
        for comp in components:
            seen_types.add(comp.component_type)
            components_by_type.setdefault(comp.component_type, []).append(comp)

        # Emit each component type
        for comp_type in seen_types:
            subdir, template_name = self._get_template_path(comp_type)
            output_name = self._get_output_path(comp_type)

            # Build full template path
            if subdir:
                full_template = f"{subdir}/{template_name}"
                output_subdir = output_dir / subdir
            else:
                full_template = template_name
                output_subdir = output_dir

            type_components = components_by_type.get(comp_type, [])

            for comp in type_components:
                ctx = {
                    "ui_framework": self.ui_framework,
                    "component": comp.to_dict(),
                    "entity_id": comp.entity_id,
                    "component_type": comp.component_type.value,
                    "title": comp.title,
                    "properties": comp.properties,
                    "fields": [f.to_dict() for f in comp.fields] if comp.fields else [],
                    "table_spec": comp.table_spec.to_dict() if comp.table_spec else None,
                    "form_builder_spec": comp.form_builder_spec.to_dict() if comp.form_builder_spec else None,
                    "theme_spec": comp.theme_spec.to_dict() if comp.theme_spec else None,
                    "variants": comp.variants,
                    "size": comp.size,
                    "category": comp.category,
                }
                files.append(self._write_file(
                    full_template,
                    output_name,
                    ctx,
                    output_subdir,
                ))

        return files

    def _write_file(
        self,
        template_name: str,
        filename: str,
        context: dict[str, Any],
        output_dir: Path,
    ) -> GeneratedFile:
        """Render template, write file, trả về GeneratedFile."""
        content = self._render_template(template_name, context)
        file_path = output_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=Path(filename),
            content=content,
            template=f"react/cp19_ui_components/{template_name}",
        )


__all__ = ["ReactUIEmitter", "GeneratedFile"]
