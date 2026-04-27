"""
Backend NestJS Emitter Module.

Module này cung cấp `BackendNestJSEmitter` class để generate NestJS/TypeScript backend code
từ MIR (Midicoder Intermediate Representation).

CP01: Domain Model - Entity models (TypeORM)
CP08: Database & Data Access - Repositories

Theo SoT E07, emitter sử dụng Jinja2 templates để render code.
Templates nằm trong `midicoder/stacks/nestjs/templates/`.

Ví dụ sử dụng:
    from midicoder.pipeline.mir import MIR
    from midicoder.emitters.backend_nestjs import BackendNestJSEmitter
    
    # Load MIR từ SQLite
    mir = MIR.from_json(mir_json)
    
    # Tạo emitter
    emitter = BackendNestJSEmitter(
        stack_dir=Path("midicoder/stacks/nestjs/templates")
    )
    
    # Emit code
    files = emitter.emit(mir, output_dir=Path(".midicoder/versions/v1.0.0/src"))
    
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
        path: Đường dẫn file tương đối (ví dụ: src/modules/order/order.entity.ts)
        content: Nội dung file đã generate
        template: Tên template đã dùng
        capability: Core Capability code (CP01, CP08, etc.)
    """
    
    path: Path
    content: str
    template: str
    capability: str


# ============================================================================
# Backend NestJS Emitter
# ============================================================================


class BackendNestJSEmitter:
    """
    Emitter cho NestJS backend.
    
    Generate code từ MIR cho:
    - CP01: Domain Models (TypeORM entities)
    - CP08: Repositories
    - CP06: Controllers (future)
    
    Attributes:
        stack_dir: Đường dẫn đến templates directory
        template_env: Jinja2 Environment
    """
    
    def __init__(self, stack_dir: Path) -> None:
        """
        Khởi tạo BackendNestJSEmitter.
        
        Args:
            stack_dir: Đường dẫn đến templates directory (ví dụ: midicoder/stacks/nestjs/templates)
            
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
        1. Emit base files (main.ts, app.module.ts, config.ts, etc.)
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
        Emit base files cho NestJS backend.
        
        Files được emit:
        - src/main.ts
        - src/app.module.ts
        - src/config.ts
        - src/common/index.ts
        - src/modules/index.ts
        - src/database/index.ts
        
        Args:
            output_dir: Output directory
            
        Returns:
            List of GeneratedFile
        """
        files: list[GeneratedFile] = []
        
        # Create directories
        modules_dir = output_dir / "modules"
        entities_dir = modules_dir / "entities"
        database_dir = output_dir / "database"
        common_dir = output_dir / "common"
        
        for dir_path in [output_dir, modules_dir, entities_dir, database_dir, common_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Emit main.ts
        files.append(self._write_file(
            output_dir=output_dir,
            filename="main.ts",
            template="main.ts.jinja2",
            context={},
            capability="CP06",
        ))
        
        # Emit app.module.ts
        files.append(self._write_file(
            output_dir=output_dir,
            filename="app.module.ts",
            template="app.module.ts.jinja2",
            context={},
            capability="CP06",
        ))
        
        # Emit config.ts
        files.append(self._write_file(
            output_dir=output_dir,
            filename="config.ts",
            template="config.ts.jinja2",
            context={},
            capability="CP01",
        ))
        
        # Emit index files
        files.append(self._write_file(
            output_dir=common_dir,
            filename="index.ts",
            template="index.ts.jinja2",
            context={"module_name": "common"},
            capability="CP01",
        ))
        files.append(self._write_file(
            output_dir=modules_dir,
            filename="index.ts",
            template="index.ts.jinja2",
            context={"module_name": "modules"},
            capability="CP01",
        ))
        files.append(self._write_file(
            output_dir=database_dir,
            filename="index.ts",
            template="index.ts.jinja2",
            context={"module_name": "database"},
            capability="CP08",
        ))
        
        # Emit base entity (from db/base.entity.ts.jinja2)
        files.append(self._write_file(
            output_dir=database_dir,
            filename="base.entity.ts",
            template="db/base.entity.ts.jinja2",
            context={},
            capability="CP01",
        ))
        
        # Emit base repository (from db/base.repository.ts.jinja2)
        files.append(self._write_file(
            output_dir=database_dir,
            filename="base.repository.ts",
            template="db/base.repository.ts.jinja2",
            context={},
            capability="CP08",
        ))
        
        # Emit database module
        files.append(self._write_file(
            output_dir=modules_dir / "database",
            filename="database.module.ts",
            template="db/database.module.ts.jinja2",
            context={},
            capability="CP08",
        ))
        
        return files
    
    def _emit_entity(self, entity: dict[str, Any], output_dir: Path) -> list[GeneratedFile]:
        """
        Emit files cho một entity.
        
        Files được emit:
        - src/modules/entities/{entity}/{entity}.entity.ts
        - src/modules/entities/{entity}/{entity}.controller.ts
        - src/modules/entities/{entity}/{entity}.service.ts
        - src/modules/entities/{entity}/{entity}.dto.ts
        - src/modules/entities/{entity}/{entity}.module.ts
        
        Args:
            entity: Entity dict từ MIR metadata
            output_dir: Output directory
            
        Returns:
            List of GeneratedFile
        """
        files: list[GeneratedFile] = []
        
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()
        
        # Create entity directory
        entity_dir = output_dir / "modules" / "entities" / entity_lower
        dto_dir = entity_dir / "dto"
        
        entity_dir.mkdir(parents=True, exist_ok=True)
        dto_dir.mkdir(parents=True, exist_ok=True)
        
        # Emit entity file (from db/entity.ts.jinja2)
        files.append(self._write_file(
            output_dir=entity_dir,
            filename=f"{entity_lower}.entity.ts",
            template="db/entity.ts.jinja2",
            context={"entity": entity},
            capability="CP01",
        ))
        
        # Emit repository file (from db/repository.ts.jinja2)
        files.append(self._write_file(
            output_dir=entity_dir,
            filename=f"{entity_lower}.repository.ts",
            template="db/repository.ts.jinja2",
            context={"entity": entity},
            capability="CP08",
        ))
        
        # Emit controller
        files.append(self._write_file(
            output_dir=entity_dir,
            filename=f"{entity_lower}.controller.ts",
            template="controller.ts.jinja2",
            context={"entity": entity},
            capability="CP06",
        ))
        
        # Emit service
        files.append(self._write_file(
            output_dir=entity_dir,
            filename=f"{entity_lower}.service.ts",
            template="service.ts.jinja2",
            context={"entity": entity},
            capability="CP08",
        ))
        
        # Emit DTOs
        files.append(self._write_file(
            output_dir=dto_dir,
            filename=f"create.{entity_lower}.dto.ts",
            template="dto.ts.jinja2",
            context={"entity": entity},
            capability="CP01",
        ))
        files.append(self._write_file(
            output_dir=dto_dir,
            filename=f"update.{entity_lower}.dto.ts",
            template="dto.ts.jinja2",
            context={"entity": entity},
            capability="CP01",
        ))
        
        return files
    
    def _emit_value_object(self, vo: dict[str, Any], output_dir: Path) -> list[GeneratedFile]:
        """
        Emit files cho một Value Object.
        
        Files được emit:
        - src/domain/value-objects/{vo_id}.value-object.ts
        - src/domain/value-objects/index.ts (nếu chưa tồn tại)
        
        Args:
            vo: Value Object dict từ MIR metadata
            output_dir: Output directory
            
        Returns:
            List of GeneratedFile
        """
        files: list[GeneratedFile] = []
        
        vo_id = vo.get("id", "ValueObject")
        vo_lower = vo_id.lower()
        
        src_dir = output_dir / "src"
        domain_dir = src_dir / "domain"
        vo_dir = domain_dir / "value-objects"
        
        # Create value-objects directory
        vo_dir.mkdir(parents=True, exist_ok=True)
        
        # Emit index.ts for value-objects directory nếu chưa có
        index_file = vo_dir / "index.ts"
        if not index_file.exists():
            index_content = """// Value Objects exports\n"""
            index_file.write_text(index_content, encoding="utf-8")
            files.append(GeneratedFile(
                path=index_file.relative_to(output_dir),
                content=index_content,
                template="generated",
                capability="CP01",
            ))
        
        # Emit value object file (use domain/value-object.ts.jinja2 template - CP01)
        files.append(self._write_file(
            output_dir=vo_dir,
            filename=f"{vo_lower}.value-object.ts",
            template="domain/value-object.ts.jinja2",
            context={"vo": vo},
            capability="CP01",
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
            template_name: Tên template (ví dụ: main.ts.jinja2)
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
                f"Template không tìm thấy: {template_name}"
            ) from e
        except TemplateSyntaxError as e:
            raise TemplateSyntaxError(
                f"Lỗi syntax trong template {template_name}: {e.message}",
                e.filename,
                e.lineno,
            ) from e