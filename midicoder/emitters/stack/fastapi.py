"""
Backend FastAPI Emitter Module.

Module này cung cấp BackendFastAPIEmitter class để generate FastAPI backend code
từ MIR (Midicoder Intermediate Representation).

CP01: Domain Model - Entity models (SQLAlchemy)
CP08: Database & Data Access - Repositories

Theo SoT E07, emitter sử dụng Jinja2 templates để render code.
Templates nằm trong midicoder/stacks/fastapi/templates/.

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

from midicoder.emitters.core.domain_model import (
    FastAPIValueObjectEmitter,
    FastAPICommandEmitter,
    Command,
    FastAPIQueryEmitter,
    Query,
    QueryGuard,
    QueryEffect,
    QueryGuardType,
    QueryEffectType,
    EntityParser,
    FastAPIEntityEmitter,
)
from midicoder.emitters.core.auth import (
    AuthIR,
    AuthProvider,
    AuthProviderType,
    FastAPIAuthEmitter,
    JWTAuthConfig,
)
from midicoder.emitters.core.tenant.models import TenantMode
from midicoder.emitters.core.event import (
    FastAPIEventEmitter as CoreFastAPIEventEmitter,
    EventParser,
)
from midicoder.pipeline.mir import MIR
from midicoder.emitters.core.notification import (
    FastAPINotificationEmitter,
    parse_notifications,
)
from midicoder.emitters.core.cache import (
    CacheParser,
    FastAPICacheEmitter,
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

        # Emit API routes từ MIR metadata (CP06)
        files.extend(self._emit_routes(mir, output_dir))

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
    
    def _emit_auth(self, output_dir: Path) -> list[GeneratedFile]:
        """
        Emit auth code cho FastAPI backend (CP02-CP04).
        
        Files được emit:
        - app/core/security/jwt_auth.py
        - app/core/security/rbac_service.py
        - app/core/security/permissions.py
        - app/core/security/policy_engine.py
        - app/core/security/tenant_context.py
        
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
        auth_emitter = FastAPIAuthEmitter(stack_dir=self.stack_dir)
        
        try:
            auth_files = auth_emitter.emit(auth_data, output_dir)
            files.extend(auth_files)
        except Exception as e:
            import logging
            logging.warning(f"FastAPIAuthEmitter failed: {e}")
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
        Emit files cho một entity sử dụng FastAPIEntityEmitter mới.
        
        Files được emit:
        - app/models/{entity}.py (generated by FastAPIEntityEmitter)
        - app/repositories/{entity}_repo.py (repository template)
        
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
        
        app_dir = output_dir / "app"
        models_dir = app_dir / "models"
        
        try:
            # Sử dụng FastAPIEntityEmitter mới để generate entity model
            entity_emitter = FastAPIEntityEmitter(stack_dir=self.stack_dir)
            
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
            
            # Deep copy entity to avoid modifying original
            import copy
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
                entity_file_path = models_dir / f"{entity_lower}.py"
                entity_file_path.write_text(emitted_code, encoding="utf-8")
                
                files.append(GeneratedFile(
                    path=entity_file_path.relative_to(output_dir),
                    content=emitted_code,
                    template="entity_emitter",
                    capability="CP01",
                ))
        except Exception as e:
            # Fallback: Use base_model.py.jinja2 template nếu có lỗi
            import logging
            logging.warning(f"FastAPIEntityEmitter failed for {entity_id}, using fallback: {e}")
            
            # Sử dụng base_model.py.jinja2 template (đã tồn tại trong db/)
            files.append(self._write_file(
                output_dir=models_dir,
                filename=f"{entity_lower}.py",
                template="db/base_model.py.jinja2",
                context={"entity": entity},
                capability="CP01",
            ))
        
        # Emit repository (entity-specific - CP08) - Keep using template
        repos_dir = app_dir / "repositories"
        files.append(self._write_file(
            output_dir=repos_dir,
            filename=f"{entity_lower}_repo.py",
            template="db/repository.py.jinja2",
            context={"entity": entity},
            capability="CP08",
        ))
        
        return files
    
    def _emit_value_object(
        self,
        vo: dict[str, Any],
        output_dir: Path,
        all_value_objects: list[dict[str, Any]] = None
    ) -> list[GeneratedFile]:
        """
        Emit files cho một Value Object sử dụng FastAPIValueObjectEmitter mới.
        
        Files được emit:
        - app/domain/value_objects/{vo_id_lower}.py
        - app/domain/value_objects/__init__.py (nếu chưa tồn tại)
        
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
        
        # Sử dụng FastAPIValueObjectEmitter mới để generate code
        try:
            # Tạo emitter
            vo_emitter = FastAPIValueObjectEmitter(stack_dir=self.stack_dir)
            
            # Build vo_map cho inheritance resolution
            vo_map = {}
            if all_value_objects:
                for v in all_value_objects:
                    vo_map[v.get("id", "")] = v
            
            # Emit VO với inheritance support
            emitted_vo = vo_emitter.emit(vo, parent_vo_map=vo_map)
            
            # Write file
            file_path = vo_dir / f"{vo_lower}.py"
            file_path.write_text(emitted_vo.full_content, encoding="utf-8")
            
            files.append(GeneratedFile(
                path=file_path.relative_to(output_dir),
                content=emitted_vo.full_content,
                template="value_object_emitter",
                capability="CP01",
            ))
            
        except Exception as e:
            # Fallback: Use old template-based approach
            files.append(self._write_file(
                output_dir=vo_dir,
                filename=f"{vo_lower}.py",
                template="domain/value_objects/value_object.py.jinja2",
                context={"vo": vo},
                capability="CP01",
            ))
        
        return files
    
    def _emit_query(self, query: dict[str, Any], output_dir: Path) -> list[GeneratedFile]:
        """
        Emit files cho một Query (CP01-Part4).
        
        Sử dụng FastAPIQueryEmitter để generate code.
        
        Files được emit:
        - app/queries/{query_snake}/{query_snake}.py
        - app/queries/{query_snake}/{query_snake}_handler.py
        - app/queries/{query_snake}/{query_snake}_validator.py
        - app/queries/{query_snake}/{query_snake}_guards.py
        - app/queries/{query_snake}/{query_snake}_effects.py
        - app/queries/{query_snake}/{query_snake}_output.py
        - app/queries/{query_snake}/__init__.py
        
        Args:
            query: Query dict từ MIR metadata
            output_dir: Output directory
            
        Returns:
            List of GeneratedFile
        """
        files: list[GeneratedFile] = []
        
        query_id = query.get("id", "Query")
        query_snake = self._to_snake_case(query_id)
        
        app_dir = output_dir / "app"
        queries_dir = app_dir / "queries" / query_snake
        
        # Create queries directory
        queries_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Build Query object từ dict
            query_obj = self._build_query_from_dict(query)
            
            # Tạo emitter và emit files
            query_emitter = FastAPIQueryEmitter(stack_dir=self.stack_dir)
            
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
            logging.warning(f"FastAPIQueryEmitter failed, using fallback: {e}")
            
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
                filename=f"{query_snake}.py",
                template="queries/query.py.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=queries_dir,
                filename=f"{query_snake}_handler.py",
                template="queries/query_handler.py.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=queries_dir,
                filename=f"{query_snake}_validator.py",
                template="queries/query_validator.py.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=queries_dir,
                filename=f"{query_snake}_guards.py",
                template="queries/query_guards.py.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=queries_dir,
                filename=f"{query_snake}_output.py",
                template="queries/query_output.py.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=queries_dir,
                filename="__init__.py",
                template="queries/__init__.py.jinja2",
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
        
        Sử dụng FastAPICommandEmitter để generate code.
        
        Files được emit:
        - app/commands/{command_snake}/{command_snake}.py
        - app/commands/{command_snake}/{command_snake}_handler.py
        - app/commands/{command_snake}/{command_snake}_validator.py
        - app/commands/{command_snake}/{command_snake}_guards.py
        - app/commands/{command_snake}/{command_snake}_effects.py
        - app/commands/{command_snake}/{command_snake}_errors.py
        - app/commands/{command_snake}/__init__.py
        
        Args:
            command: Command dict từ MIR metadata
            output_dir: Output directory
            
        Returns:
            List of GeneratedFile
        """
        files: list[GeneratedFile] = []
        
        command_id = command.get("id", "Command")
        command_snake = self._to_snake_case(command_id)
        
        app_dir = output_dir / "app"
        commands_dir = app_dir / "commands" / command_snake
        
        # Create commands directory
        commands_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Sử dụng FastAPICommandEmitter để generate command files
            from midicoder.dsl.kernel import ProjectionNode
            
            # Build Command object từ dict
            projection_node = ProjectionNode.from_dict(command)
            command_obj = Command.from_projection_node(projection_node)
            
            # Tạo emitter và emit files
            command_emitter = FastAPICommandEmitter(stack_dir=self.stack_dir)
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
            logging.warning(f"FastAPICommandEmitter failed, using fallback: {e}")
            
            # Template context
            context = {
                "command": command,
                "command_id": command_id,
                "command_snake": command_snake,
            }
            
            # Emit command files (fallback)
            files.append(self._write_file(
                output_dir=commands_dir,
                filename=f"{command_snake}.py",
                template="commands/command.py.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename=f"{command_snake}_handler.py",
                template="commands/command_handler.py.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename=f"{command_snake}_validator.py",
                template="commands/command_validator.py.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename=f"{command_snake}_guards.py",
                template="commands/command_guards.py.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename=f"{command_snake}_effects.py",
                template="commands/command_effects.py.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename=f"{command_snake}_errors.py",
                template="commands/command_errors.py.jinja2",
                context=context,
                capability="CP01",
            ))
            
            files.append(self._write_file(
                output_dir=commands_dir,
                filename="__init__.py",
                template="commands/__init__.py.jinja2",
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
    
    def _emit_events(
        self,
        events_data: list[dict[str, Any]],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """
        Emit event code files (CP05: Event-Driven Architecture).

        Sử dụng FastAPIEventEmitter để generate event code.

        Files được emit:
        - app/core/event/event_bus.py
        - app/core/event/event_publisher.py
        - app/core/event/event_subscriber.py
        - app/core/event/__init__.py

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
            event_emitter = CoreFastAPIEventEmitter(stack_dir=self.stack_dir)
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
            logging.warning(f"FastAPIEventEmitter failed: {e}")

        return files

    def _emit_routes(
        self,
        mir: MIR,
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """
        Emit API route files (CP06: API Gateway & Service Mesh).

        Sử dụng RouteParser + FastAPIRouteEmitter để generate:
        - HTTP REST routes → app/routes/{tag}_routes.py
        - GraphQL resolvers → app/graphql/resolvers/
        - Webhook handlers → app/webhooks/

        Args:
            mir: MIR instance
            output_dir: Output directory

        Returns:
            List of GeneratedFile
        """
        files: list[GeneratedFile] = []

        try:
            from midicoder.emitters.core.gateway import (
                RouteParser,
                FastAPIRouteEmitter,
                FastAPIGraphQLResolverEmitter,
                FastAPIWebhookEmitter,
            )

            # Parse routes từ MIR metadata
            parser = RouteParser()
            collection = parser.parse_from_metadata(
                routes_data=mir.metadata.get("routes", []),
                graphql_data=mir.metadata.get("graphql", []),
                webhooks_data=mir.metadata.get("webhooks", []),
            )

            app_dir = output_dir / "app"

            # Emit HTTP REST routes
            if collection.routes:
                route_emitter = FastAPIRouteEmitter()
                emitted = route_emitter.emit(collection, app_dir)
                for file_path, content in emitted.items():
                    files.append(GeneratedFile(
                        path=Path(file_path),
                        content=content,
                        template="route_emitter",
                        capability="CP06",
                    ))

            # Emit GraphQL resolvers
            if collection.resolvers:
                gql_emitter = FastAPIGraphQLResolverEmitter()
                emitted = gql_emitter.emit(collection, app_dir)
                for file_path, content in emitted.items():
                    files.append(GeneratedFile(
                        path=Path(file_path),
                        content=content,
                        template="graphql_emitter",
                        capability="CP06",
                    ))

            # Emit Webhook handlers
            if collection.webhooks:
                webhook_emitter = FastAPIWebhookEmitter()
                emitted = webhook_emitter.emit(collection, app_dir)
                for file_path, content in emitted.items():
                    files.append(GeneratedFile(
                        path=Path(file_path),
                        content=content,
                        template="webhook_emitter",
                        capability="CP06",
                    ))

        except Exception as e:
            import logging
            logging.warning(f"CP06 Route Emitter failed: {e}")

        return files



    def _emit_cache(
        self,
        metadata: dict[str, Any],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """
        Emit cache code files (CP09: Caching & Performance Layer).

        Su dung FastAPICacheEmitter de generate cache code.

        Files duoc emit:
        - app/cache/__init__.py
        - app/cache/redis.py
        - app/cache/cache_strategy.py
        - app/cache/cache_decorators.py
        - app/cache/cache_invalidate.py

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
            cache_emitter = FastAPICacheEmitter()
            emitted = cache_emitter.generate(collection, stack="fastapi")

            app_dir = output_dir / "app"

            # Write files
            for file_path_str, content in emitted.items():
                file_path = app_dir / file_path_str
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
            logging.warning(f"FastAPICacheEmitter failed: {e}")

        return files
    def _emit_notifications(
        self,
        notifications_data: list[dict[str, Any]],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """
        Emit notification code files (CP12: Notification & Communication).

        Su dung FastAPINotificationEmitter de generate notification code.

        Files duoc emit:
        - app/services/notification_service.py
        - app/services/email_service.py
        - app/api/notifications.py

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
            notification_emitter = FastAPINotificationEmitter()
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
            logging.warning(f'FastAPINotificationEmitter failed: {e}')

        return files

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
