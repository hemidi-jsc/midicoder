# coding: utf-8
"""
Angular UI Component Emitter (CP19).

Module này cung cấp AngularUIEmitter để emit reusable UI components
cho TẤT CẢ 50+ component types × 5 UI frameworks.

Templates: stacks/angular/cp19_ui_components/**/*.component.ts.jinja2

Usage:
    from midicoder.packs.cp19_ui_components.angular import AngularUIEmitter
    emitter = AngularUIEmitter(ui_framework="material")
    files = emitter.generate(components, output_dir)

Author: Midicoder Team
Version: 2.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp19_ui_components.models import ComponentSpec, ComponentType

# Resolve template directory relative to this package
_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent
_TEMPLATE_DIR = _PACKAGE_DIR / "stacks" / "angular" / "core" / "cp19_ui_components"


# Mapping: ComponentType → (subdirectory, template_file, output_file)
# subdirectory = None means root-level template
_COMPONENT_TEMPLATE_MAP: dict[ComponentType, tuple[str | None, str, str]] = {
    # ── Layout ──────────────────────────────────────────────────
    ComponentType.CONTAINER:  ("layout",  "container.component.ts.jinja2",  "container.component.ts"),
    ComponentType.GRID:       ("layout",  "grid.component.ts.jinja2",       "grid.component.ts"),
    ComponentType.ROW:        ("layout",  "row.component.ts.jinja2",        "row.component.ts"),
    ComponentType.COLUMN:     ("layout",  "column.component.ts.jinja2",     "column.component.ts"),
    ComponentType.BOX:        ("layout",  "box.component.ts.jinja2",        "box.component.ts"),
    ComponentType.DIVIDER:    ("layout",  "divider.component.ts.jinja2",    "divider.component.ts"),
    ComponentType.SPACER:     ("layout",  "spacer.component.ts.jinja2",     "spacer.component.ts"),
    ComponentType.FLEX:       ("layout",  "flex.component.ts.jinja2",       "flex.component.ts"),

    # ── Navigation ──────────────────────────────────────────────
    ComponentType.NAVBAR:       ("navigation", "navbar.component.ts.jinja2",       "navbar.component.ts"),
    ComponentType.SIDEBAR:      ("navigation", "sidebar.component.ts.jinja2",      "sidebar.component.ts"),
    ComponentType.BREADCRUMBS:  ("navigation", "breadcrumbs.component.ts.jinja2",  "breadcrumbs.component.ts"),
    ComponentType.PAGINATION:   ("navigation", "pagination.component.ts.jinja2",   "pagination.component.ts"),
    ComponentType.TABS:         ("navigation", "tabs.component.ts.jinja2",         "tabs.component.ts"),
    ComponentType.STEPPER:      ("navigation", "stepper.component.ts.jinja2",      "stepper.component.ts"),
    ComponentType.MENU:         ("navigation", "menu.component.ts.jinja2",         "menu.component.ts"),
    ComponentType.TREE_VIEW:    ("navigation", "tree-view.component.ts.jinja2",    "tree-view.component.ts"),

    # ── Data Display ────────────────────────────────────────────
    ComponentType.DATA_TABLE:       ("data-display", "data-table.component.ts.jinja2",       "data-table.component.ts"),
    ComponentType.CARD:             ("data-display", "card.component.ts.jinja2",             "card.component.ts"),
    ComponentType.CARD_LIST:        ("data-display", "card.component.ts.jinja2",             "card-list.component.ts"),
    ComponentType.LIST:             ("data-display", "list.component.ts.jinja2",             "list.component.ts"),
    ComponentType.TIMELINE:         ("data-display", "timeline.component.ts.jinja2",         "timeline.component.ts"),
    ComponentType.AVATAR:           ("data-display", "avatar.component.ts.jinja2",           "avatar.component.ts"),
    ComponentType.BADGE:            ("data-display", "badge.component.ts.jinja2",            "badge.component.ts"),
    ComponentType.CHIP:             ("data-display", "chip.component.ts.jinja2",             "chip.component.ts"),
    ComponentType.TOOLTIP:          ("data-display", "tooltip.component.ts.jinja2",          "tooltip.component.ts"),
    ComponentType.POPOVER:          ("data-display", "popover.component.ts.jinja2",          "popover.component.ts"),
    ComponentType.DESCRIPTION_LIST: ("data-display", "description-list.component.ts.jinja2", "description-list.component.ts"),

    # ── Data Input ──────────────────────────────────────────────
    ComponentType.FORM_FIELD:       ("data-input", "form-field.component.ts.jinja2",       "form-field.component.ts"),
    ComponentType.FORM_BUILDER:     ("data-input", "form-builder.component.ts.jinja2",     "form-builder.component.ts"),
    ComponentType.INPUT:            ("data-input", "input.component.ts.jinja2",            "input.component.ts"),
    ComponentType.TEXTAREA:         ("data-input", "textarea.component.ts.jinja2",         "textarea.component.ts"),
    ComponentType.SELECT:           ("data-input", "select.component.ts.jinja2",           "select.component.ts"),
    ComponentType.CHECKBOX:         ("data-input", "checkbox.component.ts.jinja2",         "checkbox.component.ts"),
    ComponentType.RADIO:            ("data-input", "radio.component.ts.jinja2",            "radio.component.ts"),
    ComponentType.SWITCH:           ("data-input", "switch.component.ts.jinja2",           "switch.component.ts"),
    ComponentType.SLIDER:           ("data-input", "slider.component.ts.jinja2",           "slider.component.ts"),
    ComponentType.DATE_PICKER:      ("data-input", "date-picker.component.ts.jinja2",      "date-picker.component.ts"),
    ComponentType.DATETIME_PICKER:  ("data-input", "datetime-picker.component.ts.jinja2",  "datetime-picker.component.ts"),
    ComponentType.COLOR_PICKER:     ("data-input", "color-picker.component.ts.jinja2",     "color-picker.component.ts"),
    ComponentType.FILE_UPLOAD:      ("data-input", "file-upload.component.ts.jinja2",      "file-upload.component.ts"),
    ComponentType.AUTOCOMPLETE:     ("data-input", "autocomplete.component.ts.jinja2",     "autocomplete.component.ts"),
    ComponentType.RICH_TEXT_EDITOR: ("data-input", "rich-text-editor.component.ts.jinja2", "rich-text-editor.component.ts"),

    # ── Feedback ────────────────────────────────────────────────
    ComponentType.ALERT:            ("feedback", "alert.component.ts.jinja2",            "alert.component.ts"),
    ComponentType.SNACKBAR:         ("feedback", "snackbar.component.ts.jinja2",         "snackbar.component.ts"),
    ComponentType.TOAST:            ("feedback", "toast.component.ts.jinja2",            "toast.component.ts"),
    ComponentType.DIALOG:           ("feedback", "dialog.component.ts.jinja2",           "dialog.component.ts"),
    ComponentType.MODAL:            ("feedback", "modal.component.ts.jinja2",            "modal.component.ts"),
    ComponentType.PROGRESS_BAR:     ("feedback", "progress-bar.component.ts.jinja2",     "progress-bar.component.ts"),
    ComponentType.LINEAR_PROGRESS:  ("feedback", "linear-progress.component.ts.jinja2",  "linear-progress.component.ts"),
    ComponentType.CIRCULAR_PROGRESS: ("feedback", "circular-progress.component.ts.jinja2", "circular-progress.component.ts"),
    ComponentType.SKELETON:         ("feedback", "skeleton.component.ts.jinja2",         "skeleton.component.ts"),
    ComponentType.SPINNER:          ("feedback", "spinner.component.ts.jinja2",          "spinner.component.ts"),
    ComponentType.ERROR_BOUNDARY:   ("feedback", "error-boundary.component.ts.jinja2",   "error-boundary.component.ts"),

    # ── Surface ─────────────────────────────────────────────────
    ComponentType.DRAWER:           ("surface", "drawer.component.ts.jinja2",           "drawer.component.ts"),
    ComponentType.ACCORDION:        ("surface", "accordion.component.ts.jinja2",        "accordion.component.ts"),
    ComponentType.EXPANSION_PANEL:  ("surface", "expansion-panel.component.ts.jinja2",  "expansion-panel.component.ts"),

    # ── Utility ─────────────────────────────────────────────────
    ComponentType.THEME_PROVIDER:   ("utility", "theme-provider.component.ts.jinja2",   "theme-provider.component.ts"),
    ComponentType.DESIGN_TOKENS:    ("utility", "design-tokens.scss.jinja2",            "design-tokens.scss"),
    ComponentType.ICON:             ("utility", "icon.component.ts.jinja2",             "icon.component.ts"),
    ComponentType.IMAGE:            ("utility", "image.component.ts.jinja2",            "image.component.ts"),
    ComponentType.BUTTON:           ("utility", "button.component.ts.jinja2",           "button.component.ts"),
    ComponentType.ICON_BUTTON:      ("utility", "icon-button.component.ts.jinja2",      "icon-button.component.ts"),
    ComponentType.BADGE_BUTTON:     ("utility", "badge-button.component.ts.jinja2",     "badge-button.component.ts"),

    # ── Service Layer (Phase 4) ─────────────────────────────────
    ComponentType.HTTP_CLIENT:      ("service", "http-client.service.ts.jinja2",        "http-client.service.ts"),
    ComponentType.API_INTERCEPTORS: ("service", "api-interceptors.service.ts.jinja2",   "api-interceptors.service.ts"),

    # ── Module Structure (Phase 5) ──────────────────────────────
    ComponentType.SHARED_MODULE:    ("module", "shared.module.ts.jinja2",               "shared.module.ts"),
    ComponentType.APP_ROUTING:      ("module", "app-routing.module.ts.jinja2",          "app-routing.module.ts"),
    ComponentType.AUTH_GUARD:       ("module", "auth.guard.ts.jinja2",                  "auth.guard.ts"),
}


@dataclass
class GeneratedFile:
    """File đã generate."""
    path: Path
    content: str
    template: str


class AngularUIEmitter:
    """Emitter cho Angular UI Components tái sử dụng.

    Sinh ra 50+ component types × 5 UI frameworks.
    """

    SUPPORTED_UI_FRAMEWORKS = ["material", "tailwind", "bootstrap", "antd", "carbon"]

    def __init__(self, ui_framework: str = "material") -> None:
        """Khởi tạo AngularUIEmitter.

        Args:
            ui_framework: UI framework (material, tailwind, bootstrap, antd, carbon)
        """
        if ui_framework not in self.SUPPORTED_UI_FRAMEWORKS:
            raise ValueError("UI framework '" + ui_framework + "' không được hỗ trợ. "
                           "Chọn từ: " + str(self.SUPPORTED_UI_FRAMEWORKS))
        self.ui_framework = ui_framework

        self._template_env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
            # Custom delimiters to avoid conflict with Angular {{ }} expressions
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
        # Fallback: try to derive from component_type value
        safe_name = component_type.value.replace("_", "-") + ".component.ts.jinja2"
        category = None
        for ct, (s, _, _) in _COMPONENT_TEMPLATE_MAP.items():
            if ct.value.replace("_", "-") == safe_name.replace(".component.ts.jinja2", ""):
                category = s
                break
        return category, safe_name

    def _get_output_path(self, component_type: ComponentType) -> str:
        """Lấy output filename cho ComponentType."""
        mapping = _COMPONENT_TEMPLATE_MAP.get(component_type)
        if mapping:
            _, _, output_file = mapping
            return output_file
        return component_type.value.replace("_", "-") + ".component.ts"

    def generate(
        self,
        components: list[ComponentSpec],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Sinh Angular UI components từ danh sách ComponentSpec.

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

            # Collect all specs of this type for context
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
            template=f"angular/cp19_ui_components/{template_name}",
        )


__all__ = ["AngularUIEmitter", "GeneratedFile"]
