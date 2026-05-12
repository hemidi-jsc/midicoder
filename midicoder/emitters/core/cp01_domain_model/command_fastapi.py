"""
Command Emitter cho Code Generation.

Emitter class để generate command code từ Command definition:
- Generate command dataclass/class
- Generate handler
- Generate validator
- Generate guards
- Generate effects
- Generate errors

Author: Midicoder Team
Version: 2.0.0
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from .command_models import Command


def _to_snake_case(name: str) -> str:
    """
    Chuyển PascalCase sang snake_case.
    
    Args:
        name: Tên cần chuyển
        
    Returns:
        Snake case string
    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class FastAPICommandEmitter:
    """
    Emitter cho FastAPI Command code generation.

    Generate code cho:
    - Command class
    - Command handler
    - Command validator
    - Command guards
    - Command effects
    - Command errors

    Usage:
        emitter = FastAPICommandEmitter(stack_dir=Path("midicoder/stacks/fastapi/templates"))
        files = emitter.emit(command, output_dir=Path("app/commands/create_order"))
    """
    
    def __init__(self, stack_dir: Path) -> None:
        """
        Khởi tạo FastAPICommandEmitter.

        Args:
            stack_dir: Đường dẫn đến templates directory
        """
        self._stack_dir = stack_dir
        self._env = Environment(
            loader=FileSystemLoader(str(stack_dir / "commands")),
            autoescape=True,
        )

    def emit(
        self,
        command: Command,
        output_dir: Path,
    ) -> dict[str, str]:
        """
        Emit command code files.

        Args:
            command: Command definition
            output_dir: Output directory

        Returns:
            Dict của file path -> content
        """
        files: dict[str, str] = {}

        # Prepare context
        context = self._prepare_context(command)

        # Generate files (snake_case naming)
        command_snake = _to_snake_case(command.id)

        files[f"{command_snake}.py"] = self._render(
            "command.py.jinja2", context
        )
        files[f"{command_snake}_handler.py"] = self._render(
            "command_handler.py.jinja2", context
        )
        files[f"{command_snake}_validator.py"] = self._render(
            "command_validator.py.jinja2", context
        )
        files[f"{command_snake}_guards.py"] = self._render(
            "command_guards.py.jinja2", context
        )
        files[f"{command_snake}_effects.py"] = self._render(
            "command_effects.py.jinja2", context
        )
        files[f"{command_snake}_errors.py"] = self._render(
            "command_errors.py.jinja2", context
        )
        files["__init__.py"] = self._render("__init__.py.jinja2", context)

        return files

    def _prepare_context(self, command: Command) -> dict[str, Any]:
        """
        Prepare template context từ Command.

        Args:
            command: Command definition

        Returns:
            Context dict
        """
        return {
            "command": command,
            "command_id": command.id,
            "command_id_lower": command.id.lower(),
            "command_description": command.description,
            "command_id_snake": _to_snake_case(command.id),
            "input_fields": command.input,
            "guards": command.guards,
            "effects": command.effects,
            "errors": command.errors,
            "transaction_required": command.transaction_required,
            "has_auth_guard": command.has_auth_guard(),
            "has_tenant_guard": command.has_tenant_guard(),
            "has_transaction_effects": command.has_transaction_effects(),
            "required_permissions": command.get_required_permissions(),
            "create_effects": command.get_create_effects(),
            "update_effects": command.get_update_effects(),
            "delete_effects": command.get_delete_effects(),
            "event_effects": command.get_event_effects(),
            "EffectType": "EffectType",
            "GuardType": "GuardType",
        }

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Render Jinja2 template.

        Args:
            template_name: Template name
            context: Template context

        Returns:
            Rendered content
        """
        template = self._env.get_template(template_name)
        return template.render(**context)

    def write_files(
        self,
        files: dict[str, str],
        output_dir: Path,
    ) -> None:
        """
        Write generated files to disk.

        Args:
            files: Dict of file path -> content
            output_dir: Output directory
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        for filename, content in files.items():
            file_path = output_dir / filename
            file_path.write_text(content, encoding="utf-8")