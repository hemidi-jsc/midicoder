# coding: utf-8
"""
Angular UI Component Emitter (CP19).

Module này cung cấp AngularUIEmitter để emit reusable UI components:
- FormFieldComponent: Generic form field
- DataTableComponent: Sortable/paginated data table
- CardListComponent: Card grid layout
- DialogComponent: Modal dialog wrapper

Templates:
  - form-field.component.ts.jinja2
  - data-table.component.ts.jinja2
  - card-list.component.ts.jinja2
  - dialog.component.ts.jinja2

Usage:
    from midicoder.emitters.core.cp19_ui_components.angular import AngularUIEmitter
    emitter = AngularUIEmitter(ui_framework="material")
    files = emitter.generate(components, output_dir)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.cp19_ui_components.models import ComponentSpec, ComponentType

# Resolve template directory relative to this package
_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent
_TEMPLATE_DIR = _PACKAGE_DIR / "stacks" / "angular" / "core" / "ui_component"


@dataclass
class GeneratedFile:
    """File đã generate."""
    path: Path
    content: str
    template: str


class AngularUIEmitter:
    """Emitter cho Angular UI Components tái sử dụng.

    Sinh ra:
    - form-field.component.ts — Generic form field
    - data-table.component.ts — Sortable/paginated data table
    - card-list.component.ts — Card grid layout
    - dialog.component.ts — Modal dialog wrapper
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
        )

    def _render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """Render jinja2 template với context."""
        try:
            template = self._template_env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            return f"// {template_name} - template not found\n"

    def generate(
        self,
        components: list[ComponentSpec],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Sinh Angular UI components từ danh sách ComponentSpec.

        Templates:
          - form-field.component.ts.jinja2
          - data-table.component.ts.jinja2
          - card-list.component.ts.jinja2
          - dialog.component.ts.jinja2

        Args:
            components: Danh sách ComponentSpec
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []
        ctx = {"ui_framework": self.ui_framework}

        # Xác định cần emit component nào
        types_needed = set()
        for comp in components:
            types_needed.add(comp.component_type)

        if ComponentType.FORM_FIELD in types_needed:
            files.append(self._write_file(
                "form-field.component.ts.jinja2",
                "form-field.component.ts",
                ctx, output_dir,
            ))

        if ComponentType.DATA_TABLE in types_needed:
            files.append(self._write_file(
                "data-table.component.ts.jinja2",
                "data-table.component.ts",
                ctx, output_dir,
            ))

        if ComponentType.CARD_LIST in types_needed:
            files.append(self._write_file(
                "card-list.component.ts.jinja2",
                "card-list.component.ts",
                ctx, output_dir,
            ))

        if ComponentType.DIALOG in types_needed:
            files.append(self._write_file(
                "dialog.component.ts.jinja2",
                "dialog.component.ts",
                ctx, output_dir,
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
            template=f"angular/ui_component/{template_name}",
        )


__all__ = ["AngularUIEmitter", "GeneratedFile"]
