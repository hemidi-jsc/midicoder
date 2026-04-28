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

from midicoder.emitters.value_object import NestJSValueObjectEmitter
from midicoder.emitters.command import (
    NestJSCommandEmitter,
    Command,
)
from midicoder.emitters.query import (
    NestJSQueryEmitter,
    Query,
    AggregationQuery,
    QueryGuard,
    QueryEffect,
    QueryGuardType,
    QueryEffectType,
)
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
            files.extend(self._emit_value_object(vo, output_dir, all_value_objects=value_objects))
        
        # Emit queries từ MIR metadata (CP01-Part4)
        queries = mir.metadata.get("queries", [])
        for query in queries:
            files.extend(self._emit_query(query, output_dir))
        
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
    
    def _emit_value_object(
        self,
        vo: dict[str, Any],
        output_dir: Path,
        all_value_objects: list[dict[str, Any]] = None
    ) -> list[GeneratedFile]:
        """
        Emit files cho một Value Object sử dụng NestJSValueObjectEmitter mới.
        
        Files được emit:
        - src/domain/value-objects/{vo_id_lower}.value-object.ts
        - src/domain/value-objects/index.ts (nếu chưa tồn tại)
        
        Args:
            vo: Value Object dict từ MIR metadata
            output_dir: Output directory
            all_value_objects: Danh sách tất cả value objects (cho inheritance resolution)
            
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
        
        # Sử dụng NestJSValueObjectEmitter mới để generate code
        try:
            # Tạo emitter
            vo_emitter = NestJSValueObjectEmitter(stack_dir=self.stack_dir)
            
            # Build vo_map cho inheritance resolution
            vo_map = {}
            if all_value_objects:
                for v in all_value_objects:
                    vo_map[v.get("id", "")] = v
            
            # Emit VO với inheritance support
            emitted_vo = vo_emitter.emit(vo, parent_vo_map=vo_map)
            
            # Render template với context đầy đủ
            context = vo_emitter._build_template_context(emitted_vo)
            rendered_content = vo_emitter.render_value_object(emitted_vo)
            
            # Write file
            file_path = vo_dir / f"{vo_lower}.value-object.ts"
            file_path.write_text(rendered_content, encoding="utf-8")
            
            files.append(GeneratedFile(
                path=file_path.relative_to(output_dir),
                content=rendered_content,
                template="domain/value-objects/value-object.ts.jinja2",
                capability="CP01",
            ))
            
        except Exception:
            # Fallback: Use emitter's fallback method
            vo_emitter = NestJSValueObjectEmitter(stack_dir=self.stack_dir)
            emitted_vo = vo_emitter.emit(vo)
            
            file_path = vo_dir / f"{vo_lower}.value-object.ts"
            file_path.write_text(emitted_vo.full_content, encoding="utf-8")
            
            files.append(GeneratedFile(
                path=file_path.relative_to(output_dir),
                content=emitted_vo.full_content,
                template="value_object_emitter_fallback",
                capability="CP01",
            ))
        
        return files
    
    def _emit_query(self, query: dict[str, Any], output_dir: Path) -> list[GeneratedFile]:
        """
        Emit files cho một Query (CP01-Part4).
        
        Sử dụng NestJSQueryEmitter để generate code.
        
        Files được emit:
        - src/queries/{query_snake}/{query_snake}.ts
        - src/queries/{query_snake}/{query_snake}.handler.ts
        - src/queries/{query_snake}/{query_snake}.validator.ts
        - src/queries/{query_snake}/{query_snake}.guards.ts
        - src/queries/{query_snake}/{query_snake}.effects.ts
        - src/queries/{query_snake}/{query_snake}.output.ts
        - src/queries/{query_snake}/index.ts
        
        Args:
            query: Query dict từ MIR metadata
            output_dir: Output directory
            
        Returns:
            List of GeneratedFile
        """
        files: list[GeneratedFile] = []
        
        query_id = query.get("id", "Query")
        query_snake = self._to_snake_case(query_id)
        
        src_dir = output_dir / "src"
        queries_dir = src_dir / "queries" / query_snake
        
        # Create queries directory
        queries_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Build Query object từ dict
            query_obj = self._build_query_from_dict(query)
            
            # Tạo emitter và emit files
            query_emitter = NestJSQueryEmitter(stack_dir=self.stack_dir)
            
            # Kiểm tra aggregation query
            if query_obj.get("aggregation"):
                emitted_files = query_emitter.emit_aggregation(
                    query_obj["aggregation"], 
                    queries_dir
                )
            else:
                emitted_files = query_emitter.emit(query_obj["query"], queries_dir)
            
            # Chuyển đổi sang GeneratedFile
            for filename, content in emitted_files.items():
                file_path = queries_dir / filename
                file_path.write_text(content, encoding="utf-8")
                
                files.append(GeneratedFile(
                    path=file_path.relative_to(output_dir),
                    content=content,
                    template=f"query_emitter/{filename}",
                    capability="CP01",
                ))
                
        except Exception as e:
            # Fallback: Use old template-based approach nếu có lỗi
            import logging
            logging.warning(f"NestJSQueryEmitter failed, using fallback: {e}")
            
            # Template context (old style)
            context = {
                "query": query,
                "query_id": query_id,
                "query_snake": query_snake,
                "query_description": query.get("description", ""),
                "query_input": query.get("input", []),
                "query_output": query.get("returns", []),
                "entity_id": query.get("reads_from", ["Entity"])[0] if query.get("reads_from") else "Entity",
                "entity_lower": (query.get("reads_from", ["entity"])[0] if query.get("reads_from") else "entity").lower(),
            }
            
            # Emit query files (fallback)
            files.append(self._write_file(
                output_dir=queries_dir,
                filename=f"{query_snake}.query.ts",
                template="domain/queries/query.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=queries_dir,
                filename=f"{query_snake}.handler.ts",
                template="domain/queries/query.handler.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=queries_dir,
                filename=f"{query_snake}.validator.ts",
                template="domain/queries/query.validator.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=queries_dir,
                filename=f"{query_snake}.guards.ts",
                template="domain/queries/query.guards.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=queries_dir,
                filename=f"{query_snake}.output.ts",
                template="domain/queries/query.output.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=queries_dir,
                filename="index.ts",
                template="domain/queries/index.ts.jinja2",
                context=context,
                capability="CP01",
            ))
        
        return files
    
    def _build_query_from_dict(self, query: dict[str, Any]) -> dict[str, Any]:
        """
        Build Query object từ dict (từ MIR metadata).
        
        Args:
            query: Query dict từ MIR metadata
            
        Returns:
            Dictionary với Query hoặc AggregationQuery instance
        """
        from midicoder.emitters.query import (
            QueryField, FilterExpression, FilterOp,
            PaginationConfig, PaginationType, ProjectionConfig,
            SortExpression, SortDirection,
        )
        
        # Parse input fields
        input_fields = [
            QueryField(
                name=f.get("name", ""),
                field_type=f.get("type", "str"),
                required=f.get("required", False),
            )
            for f in query.get("input", [])
        ]
        
        # Parse filters
        filters = [
            FilterExpression(
                field=f.get("field", ""),
                operator=FilterOp(f.get("operator", "eq")),
                value=f.get("value"),
            )
            for f in query.get("filters", [])
        ]
        
        # Parse pagination
        pagination_data = query.get("pagination", {})
        pagination = PaginationConfig(
            type=PaginationType(pagination_data.get("type", "offset")),
            page_size=pagination_data.get("page_size", 20),
            page=pagination_data.get("page", 1),
        )
        
        # Parse projection
        projection_data = query.get("projection", {})
        projection = ProjectionConfig(
            include=projection_data.get("include", []),
            exclude=projection_data.get("exclude", []),
        )
        
        # Parse sort
        sort = [
            SortExpression(
                field=s.get("field", ""),
                direction=SortDirection(s.get("direction", "asc")),
            )
            for s in query.get("sort", [])
        ]
        
        # Parse guards
        guards = [
            QueryGuard(
                guard_type=QueryGuardType(g.get("type", "auth")),
                permission=g.get("permission"),
                mode=g.get("mode", "tenant_isolated"),
            )
            for g in query.get("guards", [])
        ]
        
        # Parse effects
        effects = [
            QueryEffect(
                effect_type=QueryEffectType(e.get("type", "write_audit_log")),
                audit_action=e.get("audit_action"),
                metric_name=e.get("metric_name"),
            )
            for e in query.get("effects", [])
        ]
        
        # Build Query object
        query_obj = Query(
            id=query.get("id", "Query"),
            description=query.get("description", ""),
            reads_from=query.get("reads_from", "Entity"),
            input=input_fields,
            filters=filters,
            pagination=pagination,
            projection=projection,
            sort=sort,
            guards=guards,
            effects=effects,
        )
        
        return {"query": query_obj}
    
    def _emit_command(self, command: dict[str, Any], output_dir: Path) -> list[GeneratedFile]:
        """
        Emit files cho một Command (Full DDD pattern).
        
        Sử dụng NestJSCommandEmitter để generate code.
        
        Files được emit:
        - src/commands/{command_snake}/{command_snake}.ts
        - src/commands/{command_snake}/{command_snake}.handler.ts
        - src/commands/{command_snake}/{command_snake}.validator.ts
        - src/commands/{command_snake}/{command_snake}.guards.ts
        - src/commands/{command_snake}/{command_snake}.effects.ts
        - src/commands/{command_snake}/{command_snake}.errors.ts
        - src/commands/{command_snake}/{command_snake}.module.ts
        - src/commands/{command_snake}/index.ts
        
        Args:
            command: Command dict từ MIR metadata
            output_dir: Output directory
            
        Returns:
            List of GeneratedFile
        """
        files: list[GeneratedFile] = []
        
        command_id = command.get("id", "Command")
        command_snake = self._to_snake_case(command_id)
        
        src_dir = output_dir / "src"
        commands_dir = src_dir / "commands" / command_snake
        
        # Create commands directory
        commands_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Sử dụng NestJSCommandEmitter để generate command files
            from midicoder.dsl.kernel import ProjectionNode
            
            # Build Command object từ dict
            projection_node = ProjectionNode.from_dict(command)
            command_obj = Command.from_projection_node(projection_node)
            
            # Tạo emitter và emit files
            command_emitter = NestJSCommandEmitter(stack_dir=self.stack_dir)
            emitted_files = command_emitter.emit(command_obj, commands_dir)
            
            # Chuyển đổi sang GeneratedFile
            for filename, content in emitted_files.items():
                file_path = commands_dir / filename
                file_path.write_text(content, encoding="utf-8")
                
                files.append(GeneratedFile(
                    path=file_path.relative_to(output_dir),
                    content=content,
                    template=f"command_emitter/{filename}",
                    capability="CP01",
                ))
                
        except Exception as e:
            # Fallback: Use old template-based approach nếu có lỗi
            import logging
            logging.warning(f"NestJSCommandEmitter failed, using fallback: {e}")
            
            # Template context
            context = {
                "command": command,
                "command_snake": command_snake,
            }
            
            # Emit command files (fallback)
            files.append(self._write_file(
                output_dir=commands_dir,
                filename=f"{command_snake}.ts",
                template="domain/commands/command.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename=f"{command_snake}.handler.ts",
                template="domain/commands/command.handler.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename=f"{command_snake}.validator.ts",
                template="domain/commands/command.validator.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename=f"{command_snake}.guards.ts",
                template="domain/commands/command.guards.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename=f"{command_snake}.effects.ts",
                template="domain/commands/command.effects.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename=f"{command_snake}.errors.ts",
                template="domain/commands/command.errors.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename=f"{command_snake}.module.ts",
                template="domain/commands/command.module.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename="index.ts",
                template="domain/commands/index.ts.jinja2",
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