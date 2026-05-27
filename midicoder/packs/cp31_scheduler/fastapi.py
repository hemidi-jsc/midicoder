"""
FastAPI Emitter cho CP31: Scheduler & Cron Engine.

Module này render Jinja2 templates để sinh scheduler engine code
cho FastAPI stack.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


@dataclass
class GeneratedFile:
    """File đã generate.

    Attributes:
        path: Đường dẫn relative của file.
        content: Nội dung file.
    """
    path: str
    content: str


class SchedulerFastAPIEmitter:
    """Emitter cho FastAPI stack.

    Render templates từ `stacks/fastapi/cp31_scheduler/`
    để sinh scheduler engine code.

    Ví dụ:
        >>> emitter = SchedulerFastAPIEmitter(stack_dir="/path/to/stacks/fastapi/core")
        >>> files = emitter.emit(schedules, output_dir="/path/to/output")
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Initialise emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/fastapi/`.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp31_scheduler"

        if not self.template_dir.exists():
            self.template_dir.mkdir(parents=True, exist_ok=True)

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Disable Escaping cho code generation
        self.env.autoescape = False

    def emit(
        self,
        schedules: list[dict[str, Any]],
        output_dir: str | Path,
        calendar_sets: list[dict[str, Any]] | None = None,
    ) -> list[GeneratedFile]:
        """Emit scheduler engine code cho FastAPI.

        Args:
            schedules: Danh sách schedule dicts.
            output_dir: Đường dẫn output directory.
            calendar_sets: Danh sách calendar set dicts (nếu có).

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = {
            "schedules": schedules,
            "schedule_count": len(schedules),
            "calendar_sets": calendar_sets or [],
            "has_calendar": bool(calendar_sets),
        }

        files = []

        # cron_parser.py
        if self._template_exists("cron_parser.py.jinja2"):
            content = self._render("cron_parser.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/scheduler/cron_parser.py",
                content=content,
            ))

        # calendar_engine.py
        if self._template_exists("calendar_engine.py.jinja2"):
            content = self._render("calendar_engine.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/scheduler/calendar_engine.py",
                content=content,
            ))

        # scheduler_service.py
        if self._template_exists("scheduler_service.py.jinja2"):
            content = self._render("scheduler_service.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/scheduler/scheduler_service.py",
                content=content,
            ))

        # scheduler_router.py
        if self._template_exists("scheduler_router.py.jinja2"):
            content = self._render("scheduler_router.py.jinja2", context)
            files.append(GeneratedFile(
                path="app/scheduler/scheduler_router.py",
                content=content,
            ))

        return files

    def _template_exists(self, name: str) -> bool:
        """Kiểm tra template có tồn tại không.

        Args:
            name: Tên template file.

        Returns:
            True nếu tồn tại.
        """
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render một template.

        Args:
            template_name: Tên template file.
            context: Template context.

        Returns:
            Rendered string.
        """
        template = self.env.get_template(template_name)
        return template.render(**context)
