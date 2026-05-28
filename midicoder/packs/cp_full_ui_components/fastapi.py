# coding: utf-8
"""
FastAPI UI Emitter (CP19).

Module này cung cấp FastAPIUIEmitter để sinh form validation schemas
từ FormFieldSpec (Pydantic models với field-level validation).

Templates:
  - form_validation_service.py.jinja2

Usage:
    from midicoder.packs.cp_full_ui_components.fastapi import FastAPIUIEmitter
    emitter = FastAPIUIEmitter()
    files = emitter.generate(components, output_dir)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_full_ui_components.models import ComponentSpec

# Resolve template directory relative to this package
_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent
_TEMPLATE_DIR = _PACKAGE_DIR / "stacks" / "fastapi" / "cp_full_ui_components"


@dataclass
class GeneratedFile:
    """File đã generate."""
    path: Path
    content: str
    template: str


class FastAPIUIEmitter:
    """Emitter cho FastAPI Form Validation Service.

    Sinh ra:
    - form_validation_service.py — Pydantic schemas với validators
    """

    name: str = "fastapi-ui"
    language: str = "python"
    version: str = "1.0.0"
    description: str = "FastAPI form validation service emitter"

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
            return f"# {template_name} - template not found\n"

    def generate(
        self,
        components: list[ComponentSpec],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Sinh FastAPI form validation service từ ComponentSpec.

        Templates:
          - form_validation_service.py.jinja2

        Args:
            components: Danh sách ComponentSpec (chỉ xử lý FORM_FIELD)
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []

        # Thu thập tất cả form fields từ components
        form_components = [c for c in components if c.component_type.value == "form_field"]

        if not form_components:
            # Vẫn sinh service mặc định
            form_components = []

        # Xây dựng context với entity schemas
        schemas: list[dict[str, Any]] = []
        for comp in form_components:
            fields_data = [f.to_dict() for f in comp.fields] if comp.fields else []
            schemas.append({
                "entity_id": comp.entity_id,
                "fields": fields_data,
            })

        ctx = {"schemas": schemas}

        files.append(self._write_file(
            "form_validation_service.py.jinja2",
            "form_validation_service.py",
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
            template=f"fastapi/ui_component/{template_name}",
        )


def rc_component(render_context, component_name):
    """Jinja2 bridge: lookup component override từ RenderContextSpec."""
    if hasattr(render_context, "get_component"):
        override = render_context.get_component(component_name)
        b = {}
        for attr in ["sortable", "paginated", "page_size", "selectable",
                      "filterable", "searchable", "editable", "virtual_scroll",
                      "close_on_backdrop", "show_cancel", "default_width",
                      "form_layout", "validation_mode", "conditional_enabled"]:
            v = getattr(override.behavior, attr, None)
            if v is not None:
                b[attr] = v
        return {"behavior": b, "tokens": {}}
    elif isinstance(render_context, dict):
        return render_context.get("components", {}).get(component_name.lower(), {})
    return {}


def rc_behavior(render_context, component_name, key, default=None):
    """Get behavior prop from render context."""
    comp = rc_component(render_context, component_name)
    return comp.get("behavior", {}).get(key, default)


def rc_token(render_context, component_name, key, default=""):
    """Get CSS token from render context."""
    comp = rc_component(render_context, component_name)
    return comp.get("tokens", {}).get(key, default)


__all__ = ["FastAPIUIEmitter", "GeneratedFile"]
