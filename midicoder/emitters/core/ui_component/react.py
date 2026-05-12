# coding: utf-8
"""
React UI Component Emitter (CP19).

Module này cung cấp ReactUIEmitter để emit reusable UI components:
- FormField: Generic form field
- DataTable: Sortable/paginated data table
- CardList: Card grid layout
- Dialog: Modal dialog wrapper

Templates:
  - FormField.tsx.jinja2
  - DataTable.tsx.jinja2
  - CardList.tsx.jinja2
  - Dialog.tsx.jinja2

Usage:
    from midicoder.emitters.core.ui_component.react import ReactUIEmitter
    emitter = ReactUIEmitter(ui_framework="tailwind")
    files = emitter.generate(components, output_dir)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.ui_component.models import ComponentSpec, ComponentType

# Resolve template directory relative to this package
_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent
_TEMPLATE_DIR = _PACKAGE_DIR / "stacks" / "react" / "core" / "ui_component"


@dataclass
class GeneratedFile:
    """File đã generate."""
    path: Path
    content: str
    template: str


class ReactUIEmitter:
    """Emitter cho React UI Components tái sử dụng.

    Sinh ra:
    - FormField.tsx — Generic form field
    - DataTable.tsx — Sortable/paginated data table
    - CardList.tsx — Card grid layout
    - Dialog.tsx — Modal dialog wrapper
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
        """Sinh React UI components từ danh sách ComponentSpec.

        Templates:
          - FormField.tsx.jinja2
          - DataTable.tsx.jinja2
          - CardList.tsx.jinja2
          - Dialog.tsx.jinja2

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
                "FormField.tsx.jinja2",
                "FormField.tsx",
                ctx, output_dir,
            ))

        if ComponentType.DATA_TABLE in types_needed:
            files.append(self._write_file(
                "DataTable.tsx.jinja2",
                "DataTable.tsx",
                ctx, output_dir,
            ))

        if ComponentType.CARD_LIST in types_needed:
            files.append(self._write_file(
                "CardList.tsx.jinja2",
                "CardList.tsx",
                ctx, output_dir,
            ))

        if ComponentType.DIALOG in types_needed:
            files.append(self._write_file(
                "Dialog.tsx.jinja2",
                "Dialog.tsx",
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
            template=f"react/ui_component/{template_name}",
        )


__all__ = ["ReactUIEmitter", "GeneratedFile"]
