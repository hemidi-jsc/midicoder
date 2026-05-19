# coding: utf-8
"""
NestJS UI Emitter (CP19).

Module này cung cấp NestJSUIEmitter để sinh form validation DTOs
từ FormFieldSpec (class-validator decorators + ValidationPipe).

Templates:
  - form-validation.dto.ts.jinja2
  - form-validation.pipe.ts.jinja2

Usage:
    from midicoder.emitters.core.cp19_ui_components.nestjs import NestJSUIEmitter
    emitter = NestJSUIEmitter()
    files = emitter.generate(components, output_dir)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.cp19_ui_components.models import ComponentSpec

# Resolve template directory relative to this package
_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent
_TEMPLATE_DIR = _PACKAGE_DIR / "stacks" / "nestjs" / "core" / "cp19_ui_components"


@dataclass
class GeneratedFile:
    """File đã generate."""
    path: Path
    content: str
    template: str


class NestJSUIEmitter:
    """Emitter cho NestJS Form Validation DTO + Pipe.

    Sinh ra:
    - form-validation.dto.ts — DTO class với class-validator decorators
    - form-validation.pipe.ts — Custom ValidationPipe
    """

    name: str = "nestjs-ui"
    language: str = "typescript"
    version: str = "1.0.0"
    description: str = "NestJS form validation dto/pipe emitter"

    def __init__(self) -> None:
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
        """Sinh NestJS form validation DTO + Pipe từ ComponentSpec.

        Templates:
          - form-validation.dto.ts.jinja2
          - form-validation.pipe.ts.jinja2

        Args:
            components: Danh sách ComponentSpec (chỉ xử lý FORM_FIELD)
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []

        # Thu thập tất cả form fields từ components
        form_components = [c for c in components if c.component_type.value == "form_field"]

        # Sinh DTO cho mỗi entity có form fields
        for comp in form_components:
            fields_data = [f.to_dict() for f in comp.fields] if comp.fields else []
            ctx = {"entity_id": comp.entity_id, "fields": fields_data}
            entity_lower = comp.entity_id.lower()

            files.append(self._write_file(
                "form-validation.dto.ts.jinja2",
                f"{entity_lower}-form-validation.dto.ts",
                ctx, output_dir,
            ))

        # Luôn sinh ValidationPipe
        files.append(self._write_file(
            "form-validation.pipe.ts.jinja2",
            "form-validation.pipe.ts",
            {}, output_dir,
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
            template=f"nestjs/ui_component/{template_name}",
        )


__all__ = ["NestJSUIEmitter", "GeneratedFile"]
