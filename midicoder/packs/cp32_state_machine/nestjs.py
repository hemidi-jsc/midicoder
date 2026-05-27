"""
NestJS Emitter cho CP32: State Machine Engine.

Module này render Jinja2 templates để sinh state machine engine code
cho NestJS stack.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
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


class StateMachineNestJSEmitter:
    """Emitter cho NestJS stack — CP32 State Machine.

    Render templates từ `stacks/nestjs/cp32_state_machine/`
    để sinh state machine engine code.

    Ví dụ:
        >>> emitter = StateMachineNestJSEmitter(stack_dir="/path/to/stacks/nestjs/core")
        >>> files = emitter.emit(state_machines, output_dir="/path/to/output")
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/nestjs/`.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp32_state_machine"

        if not self.template_dir.exists():
            self.template_dir.mkdir(parents=True, exist_ok=True)

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def emit(
        self,
        state_machines: list[dict[str, Any]],
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit state machine engine code cho NestJS.

        Args:
            state_machines: Danh sách state machine definition dicts.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        if not state_machines:
            return []

        context = {
            "state_machines": state_machines,
            "machine_count": len(state_machines),
        }

        files = []

        # state-machine.service.ts
        if self._template_exists("state-machine.service.ts.jinja2"):
            content = self._render("state-machine.service.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/state-machine/state-machine.service.ts",
                content=content,
            ))

        # state-registry.service.ts
        if self._template_exists("state-registry.service.ts.jinja2"):
            content = self._render("state-registry.service.ts.jinja2", context)
            files.append(GeneratedFile(
                path="src/state-machine/state-registry.service.ts",
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
