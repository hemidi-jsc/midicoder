# coding: utf-8
"""
FastAPI Frontend Emitter (CP18).

Generate FastAPI ConfigService + SPA router để cung cấp frontend app config.

Templates:
  - frontend_config_service.py.jinja2
  - frontend_router.py.jinja2

Usage:
    from midicoder.emitters.core.cp18_frontend_framework.fastapi import FastAPIFrontendEmitter
    emitter = FastAPIFrontendEmitter()
    files = emitter.generate(app, output_dir)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound


# Resolve template directory relative to this package
_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent
_TEMPLATE_DIR = _PACKAGE_DIR / "stacks" / "fastapi" / "core" / "cp18_frontend_framework"


@dataclass
class GeneratedFile:
    """File đã generate."""
    path: Path
    content: str
    template: str


class FastAPIFrontendEmitter:
    """
    Emitter cho FastAPI ConfigService + SPA router.

    Sinh ra:
    - frontend_config_service.py — Pydantic models + ConfigService
    - frontend_router.py — API endpoints + SPA fallback route
    """

    name: str = "fastapi-frontend"
    language: str = "python"
    version: str = "1.0.0"
    description: str = "FastAPI frontend config service emitter"

    def __init__(self) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a jinja2 template with the given context."""
        try:
            template = self._env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            return f"# {template_name} - template not found\n"

    def generate(
        self,
        app: Any,
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """
        Sinh FastAPI config service + SPA router.

        Templates:
          - frontend_config_service.py.jinja2
          - frontend_router.py.jinja2

        Args:
            app: FrontendApp object
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        ctx = self._build_context(app)
        files: list[GeneratedFile] = []

        # Generate config service
        files.append(self._write_file(
            "frontend_config_service.py.jinja2",
            "frontend_config_service.py",
            ctx,
            output_dir,
        ))

        # Generate router
        files.append(self._write_file(
            "frontend_router.py.jinja2",
            "frontend_router.py",
            ctx,
            output_dir,
        ))

        return files

    @staticmethod
    def _build_context(app: Any) -> dict[str, Any]:
        """Build template context from FrontendApp."""
        app_name = getattr(app, "name", "frontend-app")
        framework = getattr(app, "framework", "react")
        framework_str = framework.value if hasattr(framework, "value") else framework
        ui_framework = getattr(app, "ui_framework", "material")
        layout = getattr(app, "layout", "sidebar")
        layout_str = layout.value if hasattr(layout, "value") else layout
        description = getattr(app, "description", "")

        return {
            "app_name": app_name,
            "framework": framework_str,
            "ui_framework": ui_framework,
            "layout": layout_str,
            "description": description,
        }

    def _write_file(
        self,
        template_name: str,
        filename: str,
        context: dict[str, Any],
        output_dir: Path,
    ) -> GeneratedFile:
        """Render template, write file, return GeneratedFile."""
        content = self._render(template_name, context)
        file_path = output_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=Path(filename),
            content=content,
            template=f"fastapi/{template_name}",
        )
