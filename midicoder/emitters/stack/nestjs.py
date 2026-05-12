"""
Backend NestJS Emitter Module.

Module này cung cấp BackendNestJSEmitter class để generate NestJS/TypeScript backend code
từ MIR (Midicoder Intermediate Representation).

CP01: Domain Model - Entity models (TypeORM)
CP08: Database & Data Access - Repositories

Theo SoT E07, emitter sử dụng Jinja2 templates để render code.
Templates nằm trong midicoder/stacks/nestjs/templates/.

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

from midicoder.emitters.core.domain_model import (
    NestJSValueObjectEmitter,
    NestJSCommandEmitter,
    Command,
    NestJSQueryEmitter,
    Query,
    QueryGuard,
    QueryEffect,
    QueryGuardType,
    QueryEffectType,
    EntityParser,
    NestJSEntityEmitter,
)
from midicoder.emitters.core.auth import (
    AuthIR,
    AuthProvider,
    AuthProviderType,
    JWTAuthConfig,
    NestJSEmitter as NestJSAuthEmitter,
)
from midicoder.emitters.core.tenant.models import TenantMode
from midicoder.emitters.core.event import (
    NestJSEventEmitter as CoreNestJSEventEmitter,
    EventParser,
)
from midicoder.pipeline.mir import MIR
from midicoder.emitters.core.notification import (
    NestJSNotificationEmitter,
    parse_notifications,
)
from midicoder.emitters.core.cache import (
    CacheParser,
    NestJSCacheEmitter,
    CacheCollection,
)


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
        
        # Emit auth code (CP02-CP04)
        files.extend(self._emit_auth(output_dir))

        # Emit events từ MIR metadata (CP05)
        events_data = mir.metadata.get("events", [])
        if events_data:
            files.extend(self._emit_events(events_data, output_dir))


        # Emit cache code từ MIR metadata (CP09)
        cache_profiles_data = mir.metadata.get("cache_profiles", [])
        if cache_profiles_data:
            files.extend(self._emit_cache(mir.metadata, output_dir))

        # Emit notification code tu MIR metadata (CP12)
        notifications_data = mir.metadata.get('notifications', [])
        if notifications_data:
            files.extend(self._emit_notifications(notifications_data, output_dir))
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
    
    def _emit_auth(self, output_dir: Path) -> list[GeneratedFile]:
        """
        Emit auth code cho NestJS backend (CP02-CP04).
        
        Files được emit:
        - src/auth/jwt-auth.guard.ts
        - src/auth/rbac.service.ts
        - src/auth/permissions.module.ts
        - src/auth/policy_engine.ts
        - src/auth/tenant_context.ts
        - src/auth/index.ts
        
        KPI-028: Missing permission detection
        KPI-029: Missing tenant filter detection
        KPI-030: Invalid role binding detection
        KPI-031: Invalid policy detection
        
        Args:
            output_dir: Output directory
            
        Returns:
            List of GeneratedFile
        """
        files: list[GeneratedFile] = []
        
        # Build default AuthIR nếu không có trong MIR metadata
        auth_data = self._build_default_auth_ir()
        
        # Tạo emitter và emit auth files
        auth_emitter = NestJSAuthEmitter(stack_dir=self.stack_dir)
        
        try:
            auth_files = auth_emitter.emit(auth_data, output_dir)
            files.extend(auth_files)
        except Exception as e:
            import logging
            logging.warning(f"NestJSAuthEmitter failed: {e}")
            # Continue without auth files - basic templates will work
        
        return files
    
    def _build_default_auth_ir(self) -> AuthIR:
        """
        Build default AuthIR với JWT auth và tenant-scoped roles.
        
        Returns:
            AuthIR instance với default config
        
        KPI-029: Default tenant_scoped=True cho tất cả roles
        """
        return AuthIR(
            tenant_mode=TenantMode.SCHEMA,
            providers=[
                AuthProvider(
                    id="default_jwt",
                    provider_type=AuthProviderType.JWT,
                    config=JWTAuthConfig(
                        expire_minutes=30,
                        refresh_expire_days=7,
                        algorithm="HS256",
                        tenant_scoped=True,  # KPI-029
                    ),
                ),
            ],
            roles={
                "super_admin": Role(
                    id="super_admin",
                    permissions=["*"],
                    parents=[],
                    tenant_scoped=False,
                    description="Super admin with all permissions",
                ),
                "tenant_admin": Role(
                    id="tenant_admin",
                    permissions=["user:*", "order:*", "product:*"],
                    parents=[],
                    tenant_scoped=True,  # KPI-029
                    description="Tenant admin with scoped permissions",
                ),
                "user": Role(
                    id="user",
                    permissions=["order:create", "order:read"],
                    parents=[],
                    tenant_scoped=True,  # KPI-029
                    description="Regular user with limited permissions",
                ),
            },
            policies={},
        )
    
    def _emit_entity(self, entity: dict[str, Any], output_dir: Path, all_entities: list[dict[str, Any]] = None) -> list[GeneratedFile]:
        """
        Emit files cho một entity sử dụng NestJSEntityEmitter mới.
        
        Files được emit:
        - src/modules/{entity}/{entity}.entity.ts (generated by NestJSEntityEmitter)
        - src/modules/{entity}/{entity}.repository.ts (repository template)
        - src/modules/{entity}/{entity}.controller.ts (controller template)
        - src/modules/{entity}/{entity}.service.ts (service template)
        
        Args:
            entity: Entity dict từ MIR metadata
            output_dir: Output directory
            all_entities: Danh sách tất cả entities (cho relationship resolution)
            
        Returns:
            List of GeneratedFile
        """
        files: list[GeneratedFile] = []
        
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()
        
        # Create entity directory
        entity_dir = output_dir / "modules" / entity_lower
        dto_dir = entity_dir / "dto"
        
        entity_dir.mkdir(parents=True, exist_ok=True)
        dto_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Sử dụng NestJSEntityEmitter mới để generate entity
            entity_emitter = NestJSEntityEmitter(stack_dir=self.stack_dir)
            
            # Convert Python type names to EntityParser expected format
            def convert_entity_type(field: dict) -> None:
                """Convert Python type to EntityParser type."""
                type_mapping = {
                    "str": "string",
                    "int": "integer",
                    "float": "float",
                    "bool": "boolean",
                    "datetime": "datetime",
                }
                if "type" in field and isinstance(field["type"], str):
                    field["type"] = type_mapping.get(field["type"], field["type"])
            
            # Parse entity DSL từ dict (convert dict to YAML format then parse)
            import yaml
            import copy
            
            # Deep copy entity to avoid modifying original
            entity_copy = copy.deepcopy(entity) if isinstance(entity, dict) else entity
            
            # Convert field types
            if isinstance(entity_copy, dict) and "fields" in entity_copy:
                for field in entity_copy["fields"]:
                    convert_entity_type(field)
            
            entities_yaml = {"entities": [entity_copy] if isinstance(entity_copy, dict) else entity_copy}
            yaml_content = yaml.safe_dump(entities_yaml)
            parsed_entities = EntityParser().parse(yaml_content)
            
            # Convert all_entities dict list to yaml and parse
            all_parsed_entities = []
            if all_entities:
                # Deep copy all_entities to avoid modifying original
                all_entities_copy = copy.deepcopy(all_entities)
                
                # Convert field types for all entities
                for ent in all_entities_copy:
                    if isinstance(ent, dict) and "fields" in ent:
                        for field in ent["fields"]:
                            convert_entity_type(field)
                
                all_entities_yaml = {"entities": all_entities_copy}
                all_yaml_content = yaml.safe_dump(all_entities_yaml)
                all_parsed_entities = EntityParser().parse(all_yaml_content)
            
            # Emit entity code
            if parsed_entities:
                entity_obj = parsed_entities[0]
                emitted_code = entity_emitter.emit(entity_obj, all_parsed_entities)
                
                # Write entity file
                entity_file_path = entity_dir / f"{entity_lower}.entity.ts"
                entity_file_path.write_text(emitted_code, encoding="utf-8")
                
                files.append(GeneratedFile(
                    path=entity_file_path.relative_to(output_dir),
                    content=emitted_code,
                    template="entity_emitter",
                    capability="CP01",
                ))
        except Exception as e:
            # Fallback: Use old template-based approach nếu có lỗi
            import logging
            logging.warning(f"NestJSEntityEmitter failed for {entity_id}, using fallback: {e}")
            
            files.append(self._write_file(
                output_dir=entity_dir,
                filename=f"{entity_lower}.entity.ts",
                template="db/entity.ts.jinja2",
                context={"entity": entity},
                capability="CP01",
            ))
        
        # Emit repository file (from db/repository.ts.jinja2) - Keep using template
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
                template="value-objects/value-object.ts.jinja2",
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
                template="queries/query.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=queries_dir,
                filename=f"{query_snake}.handler.ts",
                template="queries/query.handler.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=queries_dir,
                filename=f"{query_snake}.validator.ts",
                template="queries/query.validator.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=queries_dir,
                filename=f"{query_snake}.guards.ts",
                template="queries/query.guards.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=queries_dir,
                filename=f"{query_snake}.output.ts",
                template="queries/query.output.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=queries_dir,
                filename="index.ts",
                template="queries/index.ts.jinja2",
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
        from midicoder.emitters.core.domain_model import (
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
                template="commands/command.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename=f"{command_snake}.handler.ts",
                template="commands/command.handler.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename=f"{command_snake}.validator.ts",
                template="commands/command.validator.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename=f"{command_snake}.guards.ts",
                template="commands/command.guards.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename=f"{command_snake}.effects.ts",
                template="commands/command.effects.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename=f"{command_snake}.errors.ts",
                template="commands/command.errors.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename=f"{command_snake}.module.ts",
                template="commands/command.module.ts.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename="index.ts",
                template="commands/index.ts.jinja2",
                context=context,
                capability="CP01",
            ))
        
        return files
    
    def _emit_events(
        self,
        events_data: list[dict[str, Any]],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """
        Emit event code files (CP05: Event-Driven Architecture).

        Sử dụng NestJSEventEmitter để generate event code.

        Files được emit:
        - core/event/event-bus.service.ts
        - core/event/event-publisher.service.ts
        - core/event/event-subscriber.service.ts
        - core/event/event.module.ts
        - core/event/index.ts

        Args:
            events_data: List of event dicts từ MIR metadata
            output_dir: Output directory

        Returns:
            List of GeneratedFile
        """
        files: list[GeneratedFile] = []

        try:
            # Parse events từ dict
            parser = EventParser()
            events = parser.parse(events_data)

            # Tạo emitter và emit files
            event_emitter = CoreNestJSEventEmitter(stack_dir=self.stack_dir)
            emitted_files = event_emitter.emit(events, output_dir)

            # Chuyển đổi sang GeneratedFile
            for emitted in emitted_files:
                files.append(GeneratedFile(
                    path=emitted.path,
                    content=emitted.content,
                    template=emitted.template,
                    capability="CP05",
                ))
        except Exception as e:
            import logging
            logging.warning(f"NestJSEventEmitter failed: {e}")

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
    

    def _emit_cache(
        self,
        metadata: dict[str, Any],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """
        Emit cache code files (CP09: Caching & Performance Layer).

        Su dung NestJSCacheEmitter de generate cache code.

        Files duoc emit:
        - src/cache/cache.module.ts
        - src/cache/cache.service.ts
        - src/cache/cache.interceptor.ts

        KPI-029: Tenant-aware caching qua key prefix.

        Args:
            metadata: MIR metadata dict chua cache_profiles
            output_dir: Output directory

        Returns:
            List of GeneratedFile
        """
        files: list[GeneratedFile] = []

        try:
            # Parse cache config tu metadata
            parser = CacheParser()
            collection = parser.parse_from_metadata(metadata)

            if not collection.profiles:
                return files

            # Tao emitter va emit files
            cache_emitter = NestJSCacheEmitter()
            emitted = cache_emitter.generate(collection, stack="nestjs")

            src_dir = output_dir / "src"

            # Write files
            for file_path_str, content in emitted.items():
                file_path = src_dir / file_path_str
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding="utf-8")

                files.append(GeneratedFile(
                    path=file_path.relative_to(output_dir),
                    content=content,
                    template="cache_emitter",
                    capability="CP09",
                ))
        except Exception as e:
            import logging
            logging.warning(f"NestJSCacheEmitter failed: {e}")

        return files

    def _emit_notifications(
        self,
        notifications_data: list[dict[str, Any]],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """
        Emit notification code files (CP12: Notification & Communication).

        Su dung NestJSNotificationEmitter de generate notification code.

        Files duoc emit:
        - src/notifications/notification.module.ts
        - src/notifications/notification.service.ts
        - src/notifications/notification.controller.ts

        Args:
            notifications_data: List of notification dicts tu MIR metadata
            output_dir: Output directory

        Returns:
            List of GeneratedFile
        """
        files: list[GeneratedFile] = []

        try:
            # Parse notifications tu dict
            templates = parse_notifications(notifications_data)

            # Tao emitter va emit files
            notification_emitter = NestJSNotificationEmitter()
            emitted_files = notification_emitter.generate(templates=templates)

            # Chuyen doi sang GeneratedFile
            for file_path, file_content in emitted_files.items():
                files.append(GeneratedFile(
                    path=Path(file_path),
                    content=file_content,
                    template='notification_emitter',
                    capability='CP12',
                ))
        except Exception as e:
            import logging
            logging.warning(f'NestJSNotificationEmitter failed: {e}')

        return files

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