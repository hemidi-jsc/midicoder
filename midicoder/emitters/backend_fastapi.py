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
        3. Write files to output directory
        4. Return list of GeneratedFile
        
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
        
        # Emit model (use db model template pattern)
        files.append(self._write_file(
            output_dir=app_dir / "models",
            filename=f"{entity_lower}.py",
            template="model.py.jinja2",
            context={"entity": entity},
            capability="CP01",
        ))
        
        # Emit repository (entity-specific)
        files.append(self._write_file(
            output_dir=app_dir / "repositories",
            filename=f"{entity_lower}_repo.py",
            template="repository.py.jinja2",
            context={"entity": entity},
            capability="CP08",
        ))
        
        return files
    
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