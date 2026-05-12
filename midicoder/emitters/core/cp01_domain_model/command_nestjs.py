"""
NestJS Command Emitter cho Code Generation.

Emitter class để generate NestJS command code từ Command definition:
- Generate command class
- Generate command handler
- Generate command validator
- Generate command guards
- Generate command effects
- Generate command errors
- Generate command module

Author: Midicoder Team
Version: 2.0.0
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from .models import Command


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


class NestJSCommandEmitter:
    """
    Emitter cho NestJS Command code generation.

    Generate code cho:
    - Command class (.ts)
    - Command handler (.handler.ts)
    - Command validator (.validator.ts)
    - Command guards (.guards.ts)
    - Command effects (.effects.ts)
    - Command errors (.errors.ts)
    - Command module (.module.ts)

    Usage:
        emitter = NestJSCommandEmitter(stack_dir=Path("midicoder/stacks/nestjs/templates"))
        files = emitter.emit(command, output_dir=Path("src/commands/create-order"))
    """

    def __init__(self, stack_dir: Path) -> None:
        """
        Khởi tạo NestJSCommandEmitter.

        Args:
            stack_dir: Đường dẫn đến templates directory
        """
        self._stack_dir = stack_dir
        self._env = Environment(
            loader=FileSystemLoader(str(stack_dir)),
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

        # Generate files (NestJS pattern with .ts extension, snake_case naming)
        command_snake = _to_snake_case(command.id)

        files[f"{command_snake}.ts"] = self._render(
            "command.ts.jinja2", context
        )
        files[f"{command_snake}.handler.ts"] = self._render(
            "command.handler.ts.jinja2", context
        )
        files[f"{command_snake}.validator.ts"] = self._render(
            "command.validator.ts.jinja2", context
        )
        files[f"{command_snake}.guards.ts"] = self._render(
            "command.guards.ts.jinja2", context
        )
        files[f"{command_snake}.effects.ts"] = self._render(
            "command.effects.ts.jinja2", context
        )
        files[f"{command_snake}.errors.ts"] = self._render(
            "command.errors.ts.jinja2", context
        )
        files[f"{command_snake}.module.ts"] = self._render(
            "command.module.ts.jinja2", context
        )
        files["index.ts"] = self._render("index.ts.jinja2", context)

        return files

    def _prepare_context(self, command: Command) -> dict[str, Any]:
        """
        Prepare template context từ Command.

        Args:
            command: Command definition

        Returns:
            Context dict
        """
        command_snake = _to_snake_case(command.id)

        return {
            "command": command,
            "command_id": command.id,
            "command_snake": command_snake,
            "command_id_snake": command_snake,
            "command_description": command.description,
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

