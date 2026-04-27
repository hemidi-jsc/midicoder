"""
Backend FastAPI Emitter Module.

Module này cung cấp `BackendFastAPIEmitter` class để generate FastAPI backend code
từ MIR (Midicoder Intermediate Representation).

CP01: Domain Model - Entity models (SQLAlchemy)
CP08: Database & Data Access - Repositories

Theo SoT E07, emitter sử dụng Jinja2 templates để render code.
Templates nằm trong `midicoder/stacks/fastapi/templates/`.

Ví dụ sử dụng:
    from midicoder.pipeline.mir import MIR
    from midicoder.emitters.backend_fastapi import BackendFastAPIEmitter
    
    # Load MIR từ SQLite
    mir = MIR.from_json(mir_json)
    
    # Tạo emitter
    emitter = BackendFastAPIEmitter(
        stack_dir=Path("midicoder/stacks/fastapi/templates")
    )
    
    # Emit code
    files = emitter.emit(mir, output_dir=Path(".midicoder/versions/v1.0.0/src/api"))
    
    # files: list[GeneratedFile] với path, content, template, capability

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, TemplateSyntaxError

from midicoder.pipeline.mir import MIR


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class GeneratedFile:
    """
    Generated File - File đã generate từ template.
    
    Attributes:
        path: Đường dẫn file tương đối (ví dụ: app/models/order.py)
        content: Nội dung file đã generate
        template: Tên template đã dùng
        capability: Core Capability code (CP01, CP08, etc.)
    """
    
    path: Path
    content: str
    template: str
    capability: str


# ============================================================================
# Backend FastAPI Emitter
# ============================================================================


class BackendFastAPIEmitter:
    """
    Emitter cho FastAPI backend.
    
    Generate code từ MIR cho:
    - CP01: Domain Models (SQLAlchemy)
    - CP08: Repositories
    - CP06: API Routes (future)
    
    Attributes:
        stack_dir: Đường dẫn đến templates directory
        template_env: Jinja2 Environment
    """
    
    def __init__(self, stack_dir: Path) -> None:
        """
        Khởi tạo BackendFastAPIEmitter.
        
        Args:
            stack_dir: Đường dẫn đến templates directory (ví dụ: midicoder/stacks/fastapi/templates)
            
        Raises:
            FileNotFoundError: Nếu stack_dir không tồn tại
        """
        self.stack_dir = stack_dir
        
        if not stack_dir.exists():
            raise FileNotFoundError(
                f"Template directory not found: {stack_dir}"
            )
        
        # Initialize Jinja2 environment
        self.template_env = Environment(
            loader=FileSystemLoader(str(stack_dir)),
            autoescape=True,
        )
    
    def emit(self, mir: MIR, output_dir: Path) -> list[GeneratedFile]:
        """
        Emit code từ MIR.
        
        Process:
        1. Emit base files (main.py, config.py, database.py, __init__.py files)
        2. Emit entity files cho mỗi entity trong MIR metadata
        3. Emit value object files cho mỗi value object trong MIR metadata
        4. Write files to output directory
        5. Return list of GeneratedFile
        
        Args:
            mir: MIR instance
            output_dir: Output directory
            
        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []
        
        # Emit base files
        files.extend(self._emit_base_files(output_dir))
        
        # Emit entities từ MIR metadata
        entities = mir.metadata.get("entities", [])
        for entity in entities:
            files.extend(self._emit_entity(entity, output_dir))
        
        # Emit value objects từ MIR metadata
        value_objects = mir.metadata.get("value_objects", [])
        for vo in value_objects:
            files.extend(self._emit_value_object(vo, output_dir))
        
        return files
    
    def _emit_base_files(self, output_dir: Path) -> list[GeneratedFile]:
        """
        Emit base files cho FastAPI backend.
        
        Files được emit:
        - app/main.py
        - app/config.py
        - app/database.py
        - app/__init__.py
        - app/models/__init__.py
        - app/models/base.py
        - app/schemas/__init__.py
        - app/repositories/__init__.py
        - app/repositories/base.py
        - app/routes/__init__.py
        
        Args:
            output_dir: Output directory
            
        Returns:
            List of GeneratedFile
        """
        files: list[GeneratedFile] = []
        
        # Create directories
        app_dir = output_dir / "app"
        models_dir = app_dir / "models"
        schemas_dir = app_dir / "schemas"
        repos_dir = app_dir / "repositories"
        routes_dir = app_dir / "routes"
        
        for dir_path in [app_dir, models_dir, schemas_dir, repos_dir, routes_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Emit main.py
        files.append(self._write_file(
            output_dir=app_dir,
            filename="main.py",
            template="main.py.jinja2",
            context={},
            capability="CP06",
        ))
        
        # Emit config.py
        files.append(self._write_file(
            output_dir=app_dir,
            filename="config.py",
            template="config.py.jinja2",
            context={},
            capability="CP01",
        ))
        
        # Emit database.py (from db/database.py.jinja2)
        files.append(self._write_file(
            output_dir=app_dir,
            filename="database.py",
            template="db/database.py.jinja2",
            context={},
            capability="CP08",
        ))
        
        # Emit __init__.py files
        files.append(self._write_file(
            output_dir=app_dir,
            filename="__init__.py",
            template="__init__.py.jinja2",
            context={"module_name": "app"},
            capability="CP01",
        ))
        files.append(self._write_file(
            output_dir=models_dir,
            filename="__init__.py",
            template="__init__.py.jinja2",
            context={"module_name": "models"},
            capability="CP01",
        ))
        files.append(self._write_file(
            output_dir=schemas_dir,
            filename="__init__.py",
            template="__init__.py.jinja2",
            context={"module_name": "schemas"},
            capability="CP01",
        ))
        files.append(self._write_file(
            output_dir=repos_dir,
            filename="__init__.py",
            template="__init__.py.jinja2",
            context={"module_name": "repositories"},
            capability="CP08",
        ))
        files.append(self._write_file(
            output_dir=routes_dir,
            filename="__init__.py",
            template="__init__.py.jinja2",
            context={"module_name": "routes"},
            capability="CP06",
        ))
        
        # Emit base model (copy from db/base_model.py.jinja2)
        files.append(self._write_file(
            output_dir=models_dir,
            filename="base.py",
            template="db/base_model.py.jinja2",
            context={},
            capability="CP01",
        ))
        
        # Emit base repository (copy from db/base_repository.py.jinja2)
        files.append(self._write_file(
            output_dir=repos_dir,
            filename="base.py",
            template="db/base_repository.py.jinja2",
            context={},
            capability="CP08",
        ))
        
        return files
    
    def _emit_entity(self, entity: dict[str, Any], output_dir: Path) -> list[GeneratedFile]:
        """
        Emit files cho một entity.
        
        Files được emit:
        - app/models/{entity}.py
        - app/schemas/{entity}.py
        - app/repositories/{entity}_repo.py
        - app/routes/{entity}.py
        
        Args:
            entity: Entity dict từ MIR metadata
            output_dir: Output directory
            
        Returns:
            List of GeneratedFile
        """
        files: list[GeneratedFile] = []
        
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()
        
        app_dir = output_dir / "app"
        
        # Emit model (use db/model.py.jinja2 template - CP01)
        files.append(self._write_file(
            output_dir=app_dir / "models",
            filename=f"{entity_lower}.py",
            template="db/model.py.jinja2",
            context={"entity": entity},
            capability="CP01",
        ))
        
        # Emit repository (entity-specific - CP08)
        files.append(self._write_file(
            output_dir=app_dir / "repositories",
            filename=f"{entity_lower}_repo.py",
            template="db/repository.py.jinja2",
            context={"entity": entity},
            capability="CP08",
        ))
        
        return files
    
    def _emit_value_object(self, vo: dict[str, Any], output_dir: Path) -> list[GeneratedFile]:
        """
        Emit files cho một Value Object.
        
        Files được emit:
        - app/domain/value_objects/{vo_id_lower}.py
        - app/domain/value_objects/__init__.py (nếu chưa tồn tại)
        
        Args:
            vo: Value Object dict từ MIR metadata
            output_dir: Output directory
            
        Returns:
            List of GeneratedFile
        """
        files: list[GeneratedFile] = []
        
        vo_id = vo.get("id", "ValueObject")
        vo_lower = vo_id.lower()
        
        app_dir = output_dir / "app"
        domain_dir = app_dir / "domain"
        vo_dir = domain_dir / "value_objects"
        
        # Create value_objects directory
        vo_dir.mkdir(parents=True, exist_ok=True)
        
        # Emit __init__.py for value_objects directory nếu chưa có
        init_file = vo_dir / "__init__.py"
        if not init_file.exists():
            files.append(self._write_file(
                output_dir=vo_dir,
                filename="__init__.py",
                template="__init__.py.jinja2",
                context={"module_name": "value_objects"},
                capability="CP01",
            ))
        
        # Emit value object file (use domain/value_object.py.jinja2 template - CP01)
        files.append(self._write_file(
            output_dir=vo_dir,
            filename=f"{vo_lower}.py",
            template="domain/value_object.py.jinja2",
            context={"vo": vo},
            capability="CP01",
        ))
        
        return files
    
    def _emit_command(self, command: dict[str, Any], output_dir: Path) -> list[GeneratedFile]:
        """
        Emit files cho một Command (Full DDD pattern).
        
        Files được emit:
        - app/commands/{command_id_lower}/{command_id}.py
        - app/commands/{command_id_lower}/{command_id}_handler.py
        - app/commands/{command_id_lower}/{command_id}_validator.py
        - app/commands/{command_id_lower}/{command_id}_guards.py
        - app/commands/{command_id_lower}/{command_id}_effects.py
        - app/commands/{command_id_lower}/{command_id}_errors.py
        - app/commands/{command_id_lower}/__init__.py
        - app/schemas/commands/{command_id}_input.py
        
        Args:
            command: Command dict từ MIR metadata
            output_dir: Output directory
            
        Returns:
            List of GeneratedFile
        """
        files: list[GeneratedFile] = []
        
        command_id = command.get("id", "Command")
        command_lower = command_id.lower()
        command_snake = self._to_snake_case(command_id)
        
        app_dir = output_dir / "app"
        commands_dir = app_dir / "commands" / command_snake
        schemas_dir = app_dir / "schemas" / "commands"
        
        # Create directories
        commands_dir.mkdir(parents=True, exist_ok=True)
        schemas_dir.mkdir(parents=True, exist_ok=True)
        
        # Template context
        context = {
            "command": command,
            "command_id_lower": command_lower,
            "command_snake": command_snake,
        }
        
        # Emit command files
        files.append(self._write_file(
            output_dir=commands_dir,
            filename=f"{command_snake}.py",
            template="domain/commands/command.py.jinja2",
            context=context,
            capability="CP01",
        ))
        
        files.append(self._write_file(
            output_dir=commands_dir,
            filename=f"{command_snake}_handler.py",
            template="domain/commands/command_handler.py.jinja2",
            context=context,
            capability="CP01",
        ))
        
        files.append(self._write_file(
            output_dir=commands_dir,
            filename=f"{command_snake}_validator.py",
            template="domain/commands/command_validator.py.jinja2",
            context=context,
            capability="CP01",
        ))
        
        files.append(self._write_file(
            output_dir=commands_dir,
            filename=f"{command_snake}_guards.py",
            template="domain/commands/command_guards.py.jinja2",
            context=context,
            capability="CP01",
        ))
        
        files.append(self._write_file(
            output_dir=commands_dir,
            filename=f"{command_snake}_effects.py",
            template="domain/commands/command_effects.py.jinja2",
            context=context,
            capability="CP01",
        ))
        
        files.append(self._write_file(
            output_dir=commands_dir,
            filename=f"{command_snake}_errors.py",
            template="domain/commands/command_errors.py.jinja2",
            context=context,
            capability="CP01",
        ))
        
        files.append(self._write_file(
            output_dir=commands_dir,
            filename="__init__.py",
            template="domain/commands/__init__.py.jinja2",
            context=context,
            capability="CP01",
        ))
        
        # Emit input schema
        files.append(self._write_file(
            output_dir=schemas_dir,
            filename=f"{command_snake}_input.py",
            template="domain/commands/command_input.py.jinja2",
            context=context,
            capability="CP01",
        ))
        
        return files
    
    def _to_snake_case(self, name: str) -> str:
        """
        Chuyển string sang snake_case.
        
        Args:
            name: Tên cần chuyển
            
        Returns:
            Snake case string
        """
        import re
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    
    def _write_file(
        self,
        output_dir: Path,
        filename: str,
        template: str,
        context: dict[str, Any],
        capability: str,
    ) -> GeneratedFile:
        """
        Render template và write file.
        
        Args:
            output_dir: Output directory
            filename: Tên file
            template: Template name
            context: Template context
            capability: Core Capability code
            
        Returns:
            GeneratedFile instance
            
        Raises:
            FileNotFoundError: Nếu template không tìm thấy
            TemplateSyntaxError: Nếu template có syntax error
        """
        # Render template
        content = self._render_template(template, context)
        
        # Write file
        file_path = output_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        
        return GeneratedFile(
            path=file_path.relative_to(output_dir.parent),
            content=content,
            template=template,
            capability=capability,
        )
    
    def _render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Render Jinja2 template với context.
        
        Args:
            template_name: Tên template (ví dụ: main.py.jinja2)
            context: Template context
            
        Returns:
            Rendered content
            
        Raises:
            FileNotFoundError: Nếu template không tìm thấy
            TemplateSyntaxError: Nếu template có syntax error
        """
        try:
            template = self.template_env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound as e:
            raise FileNotFoundError(
                f"Template not found: {template_name}"
            ) from e
        except TemplateSyntaxError as e:
            raise TemplateSyntaxError(
                f"Template syntax error in {template_name}: {e.message}",
                e.filename,
                e.lineno,
            ) from e