"""
FastAPI Event Emitter Module.

Module này cung cấp FastAPIEventEmitter class để generate FastAPI event code
từ EventDefinition objects.

Templates nằm trong midicoder/stacks/fastapi/templates/event/.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from .models import EventDefinition


# ============================================================================
# Generated File
# ============================================================================


@dataclass
class GeneratedFile:
    """
    Generated File - File đã generate từ template.

    Attributes:
        path: Đường dẫn file tương đối
        content: Nội dung file đã generate
        template: Tên template đã dùng
    """

    path: Path
    content: str
    template: str


# ============================================================================
# FastAPI Event Emitter
# ============================================================================


class FastAPIEventEmitter:
    """
    Emitter cho FastAPI Event code generation.

    Generate code cho:
    - app/core/event/event_bus.py
    - app/core/event/event_publisher.py
    - app/core/event/event_subscriber.py
    - app/core/event/__init__.py

    Usage:
        emitter = FastAPIEventEmitter(stack_dir=Path("midicoder/stacks/fastapi/templates"))
        files = emitter.emit(events, output_dir=Path("/tmp/output"))
    """

    def __init__(self, stack_dir: Path) -> None:
        """
        Khởi tạo FastAPIEventEmitter.

        Args:
            stack_dir: Đường dẫn đến templates directory

        Raises:
            FileNotFoundError: Nếu stack_dir không tồn tại
        """
        self.stack_dir = stack_dir

        if not stack_dir.exists():
            raise FileNotFoundError(
                f"Template directory not found: {stack_dir}"
            )

        self._env = Environment(
            loader=FileSystemLoader(str(stack_dir / "cp05_event_driven")),
            autoescape=True,
        )

    def emit(
        self,
        events: list[EventDefinition],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """
        Emit event code files.

        Args:
            events: List of EventDefinition
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []

        # Create event directory structure
        event_dir = output_dir / "app" / "core" / "event"
        event_dir.mkdir(parents=True, exist_ok=True)

        # Prepare context
        context = self._prepare_context(events)

        # Generate event_bus.py
        files.append(self._render_file(
            template_name="event_bus.py.jinja2",
            filename="event_bus.py",
            output_dir=event_dir,
            context=context,
        ))

        # Generate event_publisher.py
        files.append(self._render_file(
            template_name="event_publisher.py.jinja2",
            filename="event_publisher.py",
            output_dir=event_dir,
            context=context,
        ))

        # Generate event_subscriber.py
        files.append(self._render_file(
            template_name="event_subscriber.py.jinja2",
            filename="event_subscriber.py",
            output_dir=event_dir,
            context=context,
        ))

        # Generate event_outbox.py
        files.append(self._render_file(
            template_name="event_outbox.py.jinja2",
            filename="event_outbox.py",
            output_dir=event_dir,
            context=context,
        ))

        # Generate __init__.py
        files.append(self._render_file(
            template_name="__init__.py.jinja2",
            filename="__init__.py",
            output_dir=event_dir,
            context=context,
        ))

        return files

    def _prepare_context(
        self,
        events: list[EventDefinition],
    ) -> dict[str, Any]:
        """
        Prepare template context từ EventDefinitions.

        Args:
            events: List of EventDefinition

        Returns:
            Context dict
        """
        return {
            "events": events,
            "event_count": len(events),
            "has_tenant_events": any(e.tenant_id for e in events),
            "topics": list({e.topic for e in events}),
        }

    def _render_file(
        self,
        template_name: str,
        filename: str,
        output_dir: Path,
        context: dict[str, Any],
    ) -> GeneratedFile:
        """
        Render template và write file.

        Args:
            template_name: Template name
            filename: Output filename
            output_dir: Output directory
            context: Template context

        Returns:
            GeneratedFile instance
        """
        try:
            template = self._env.get_template(template_name)
            content = template.render(**context)
        except TemplateNotFound:
            # If template not found, create minimal content
            content = f"# {filename} - auto-generated\n"

        # Write file
        file_path = output_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        return GeneratedFile(
            path=file_path.relative_to(output_dir.parent),
            content=content,
            template=template_name,
        )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "FastAPIEventEmitter",
    "GeneratedFile",
]