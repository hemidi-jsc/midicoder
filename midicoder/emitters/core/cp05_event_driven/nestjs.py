"""
NestJS Event Emitter Module.

Module này cung cấp NestJSEventEmitter class để generate NestJS event code
từ EventDefinition objects.

Templates nằm trong midicoder/stacks/nestjs/templates/event/.

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
# NestJS Event Emitter
# ============================================================================


class NestJSEventEmitter:
    """
    Emitter cho NestJS Event code generation.

    Generate code cho:
    - core/event/event-bus.service.ts
    - core/event/event-publisher.service.ts
    - core/event/event-subscriber.service.ts
    - core/event/event.module.ts
    - core/event/index.ts

    Usage:
        emitter = NestJSEventEmitter(stack_dir=Path("midicoder/stacks/nestjs/templates"))
        files = emitter.emit(events, output_dir=Path("/tmp/output"))
    """

    def __init__(self, stack_dir: Path) -> None:
        """
        Khởi tạo NestJSEventEmitter.

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
            loader=FileSystemLoader(str(stack_dir / "event")),
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
        event_dir = output_dir / "core" / "event"
        event_dir.mkdir(parents=True, exist_ok=True)

        # Prepare context
        context = self._prepare_context(events)

        # Generate event-bus.service.ts
        files.append(self._render_file(
            template_name="event-bus.service.ts.jinja2",
            filename="event-bus.service.ts",
            output_dir=event_dir,
            context=context,
        ))

        # Generate event-publisher.service.ts
        files.append(self._render_file(
            template_name="event-publisher.service.ts.jinja2",
            filename="event-publisher.service.ts",
            output_dir=event_dir,
            context=context,
        ))

        # Generate event-subscriber.service.ts
        files.append(self._render_file(
            template_name="event-subscriber.service.ts.jinja2",
            filename="event-subscriber.service.ts",
            output_dir=event_dir,
            context=context,
        ))

        # Generate event-outbox.service.ts
        files.append(self._render_file(
            template_name="event-outbox.service.ts.jinja2",
            filename="event-outbox.service.ts",
            output_dir=event_dir,
            context=context,
        ))

        # Generate event.module.ts
        files.append(self._render_file(
            template_name="event.module.ts.jinja2",
            filename="event.module.ts",
            output_dir=event_dir,
            context=context,
        ))

        # Generate index.ts
        files.append(self._render_file(
            template_name="index.ts.jinja2",
            filename="index.ts",
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
            content = f"/** {filename} - auto-generated */\nexport {{}};\n"

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
    "NestJSEventEmitter",
    "GeneratedFile",
]