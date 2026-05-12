"""
FastAPI Entity Emitter.

FastAPI-specific implementation của EntityEmitter.
Generate SQLAlchemy model code với support cho:
- 12+ field types
- Relationships (one-to-one, one-to-many, many-to-many, self-ref, polymorphic)
- Constraints (check, unique)
- Indexes
- Lifecycle hooks

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

from .entity_emitter import EntityEmitter
from .entity_models import (
    Entity,
    Field,
    FieldType,
    Relationship,
    RelationshipType,
    Constraint,
    ConstraintType,
    LifecycleHook,
    LifecycleEvent,
)


class FastAPIEntityEmitter(EntityEmitter):
    """
    FastAPI Entity Emitter.
    
    Generate SQLAlchemy model code từ Entity objects.
    
    Usage:
        emitter = FastAPIEntityEmitter(stack_dir=Path("midicoder/stacks/fastapi/templates"))
        code = emitter.emit(entity, all_entities)
    """

    def __init__(self, stack_dir: Path) -> None:
        """
        Khởi tạo FastAPIEntityEmitter.
        
        Args:
            stack_dir: Đường dẫn đến templates directory
        """
        super().__init__(stack_dir)

    def emit(self, entity: Entity, all_entities: list[Entity]) -> str:
        """
        Generate SQLAlchemy model code từ Entity.
        
        Args:
            entity: Entity để emit
            all_entities: Danh sách tất cả entities (để resolve relationships)
            
        Returns:
            Generated Python code
        """
        context = self._build_template_context(entity, all_entities)
        
        try:
            return self.render_template("entity.py.jinja2", context)
        except Exception as e:
            return self._generate_code_fallback(context, e)

    def _build_template_context(
        self,
        entity: Entity,
        all_entities: list[Entity],
    ) -> dict[str, Any]:
        """
        Build template context cho Jinja2 rendering.
        
        Args:
            entity: Entity để build context
            all_entities: Danh sách tất cả entities
            
        Returns:
            Template context dictionary
        """
        # Build imports
        imports = self._collect_imports(entity)
        
        # Build enum classes
        enum_classes = self._build_enum_classes(entity)
        
        # Build field definitions
        field_definitions = self._build_field_definitions(entity)
        
        # Build relationship definitions
        relationship_definitions = self._build_relationship_definitions(
            entity, all_entities
        )
        
        # Build __table_args__
        table_args = self._build_table_args(entity)
        
        # Build lifecycle hooks
        lifecycle_hooks = self._build_lifecycle_hooks(entity)
        
        return {
            "entity": entity,
            "table_name": self.get_table_name(entity.id),
            "imports": imports,
            "enum_classes": enum_classes,
            "field_definitions": field_definitions,
            "relationship_definitions": relationship_definitions,
            "table_args": table_args,
            "lifecycle_hooks": lifecycle_hooks,
        }

    def _collect_imports(self, entity: Entity) -> dict[str, list[str]]:
        """
        Collect tất cả required imports.
        
        Args:
            entity: Entity
            
        Returns:
            Dictionary của imports theo module
        """
        imports = {
            "standard": [
                "from __future__ import annotations",
            ],
            "typing": [
                "from typing import Any",
            ],
            "sqlalchemy": [
                "from sqlalchemy import Column",
                "from sqlalchemy.orm import Mapped, relationship",
                "from api.app.database import Base",
            ],
        }
        
        # Collect field-specific imports
        for field in entity.fields:
            field_imports = self._get_field_imports(field)
            for key, value in field_imports.items():
                if key in imports:
                    imports[key].extend(value)
                else:
                    imports[key] = value
        
        # Add imports for constraints
        has_check = any(
            c.constraint_type == ConstraintType.CHECK
            for c in entity.constraints
        )
        if has_check:
            imports["sqlalchemy"].append("from sqlalchemy import CheckConstraint")
        
        # Add index imports
        if entity.indexes:
            imports["sqlalchemy"].append("from sqlalchemy import Index")
        
        # Add lifecycle imports
        if entity.lifecycle_hooks:
            imports["sqlalchemy"].append("from sqlalchemy import event")
        
        return imports

    def _get_field_imports(self, field: Field) -> dict[str, list[str]]:
        """
        Get imports cho một field type.
        
        Args:
            field: Field
            
        Returns:
            Dictionary của imports
        """
        imports: dict[str, list[str]] = {"standard": [], "typing": [], "sqlalchemy": []}
        
        type_mapping = {
            FieldType.UUID: {
                "standard": ["from uuid import UUID"],
                "sqlalchemy": ["from sqlalchemy.dialects.postgresql import UUID as PGUUID"],
            },
            FieldType.DATETIME: {
                "standard": ["from datetime import datetime"],
            },
            FieldType.DECIMAL: {
                "standard": ["from decimal import Decimal"],
                "sqlalchemy": ["from sqlalchemy import Numeric"],
            },
            FieldType.JSON: {
                "sqlalchemy": ["from sqlalchemy.dialects.postgresql import JSONB"],
            },
            FieldType.STRING: {
                "sqlalchemy": ["from sqlalchemy import String"],
            },
            FieldType.INTEGER: {
                "sqlalchemy": ["from sqlalchemy import Integer"],
            },
            FieldType.FLOAT: {
                "sqlalchemy": ["from sqlalchemy import Float"],
            },
            FieldType.BOOLEAN: {
                "sqlalchemy": ["from sqlalchemy import Boolean"],
            },
            FieldType.TEXT: {
                "sqlalchemy": ["from sqlalchemy import Text"],
            },
            FieldType.ENUM: {
                "standard": ["from enum import Enum"],
            },
            FieldType.LARGE_BINARY: {
                "sqlalchemy": ["from sqlalchemy import LargeBinary"],
            },
            FieldType.ARRAY: {
                "sqlalchemy": ["from sqlalchemy import ARRAY"],
            },
        }
        
        mapping = type_mapping.get(field.field_type, {})
        result: dict[str, list[str]] = {}
        for key, values in mapping.items():
            result[key] = values
        return result

    def _build_enum_classes(self, entity: Entity) -> list[str]:
        """
        Build enum class definitions cho enum fields.
        
        Args:
            entity: Entity
            
        Returns:
            List của enum class code strings
        """
        enum_classes = []
        
        for field in entity.fields:
            if field.field_type == FieldType.ENUM and field.enum_values:
                # Build enum class name
                enum_class_name = f"{entity.id}{self._to_pascal_case(field.name)}"
                
                # Build enum code
                enum_code = f'''

class {enum_class_name}(str, Enum):
    """{field.name.replace("_", " ").title()} enumeration."""
'''
                for value in field.enum_values:
                    enum_value = value.upper().replace("-", "_").replace(" ", "_")
                    enum_code += f'    {enum_value} = "{value}"\n'
                
                enum_classes.append(enum_code)
        
        return enum_classes

    def _to_pascal_case(self, name: str) -> str:
        """
        Convert string sang PascalCase.
        
        Args:
            name: Tên cần convert
            
        Returns:
            Pascal case string
        """
        parts = name.replace("_", " ").title().split()
        return "".join(parts)

    def _build_field_definitions(self, entity: Entity) -> list[str]:
        """
        Build field definition code.
        
        Args:
            entity: Entity
            
        Returns:
            List của field definition code strings
        """
        definitions = []
        
        for field in entity.fields:
            field_code = self._build_field_definition(field, entity)
            definitions.append(field_code)
        
        return definitions

    def _build_field_definition(self, field: Field, entity: Entity) -> str:
        """
        Build một field definition code.
        
        Args:
            field: Field
            entity: Parent entity
            
        Returns:
            Field definition code string
        """
        # Build type annotation
        type_annotation = self._get_type_annotation(field)
        
        # Build Column arguments
        column_args = self._build_column_args(field, entity)
        
        return f'''
    {field.name}: Mapped[{type_annotation}] = Column({column_args})'''

    def _get_type_annotation(self, field: Field) -> str:
        """
        Get Python type annotation cho field.
        
        Args:
            field: Field
            
        Returns:
            Type annotation string
        """
        type_mapping = {
            FieldType.STRING: "str",
            FieldType.INTEGER: "int",
            FieldType.FLOAT: "float",
            FieldType.BOOLEAN: "bool",
            FieldType.DATETIME: "datetime",
            FieldType.TEXT: "str",
            FieldType.UUID: "UUID",
            FieldType.JSON: "Any",
            FieldType.DECIMAL: "Decimal",
            FieldType.ENUM: f"{self._get_enum_class_name(field)}",
            FieldType.LARGE_BINARY: "bytes",
            FieldType.ARRAY: "list[str]",
        }
        
        base_type = type_mapping.get(field.field_type, "Any")
        
        # Add Optional if nullable
        if field.nullable:
            return f"{base_type} | None"
        return base_type

    def _get_enum_class_name(self, field: Field) -> str:
        """
        Get enum class name cho enum field.
        
        Args:
            field: Enum field
            
        Returns:
            Enum class name
        """
        # This will be replaced by actual entity id in template context
        return f"{{entity.id}}{self._to_pascal_case(field.name)}"

    def _build_column_args(self, field: Field, entity: Field) -> str:
        """
        Build Column() arguments.
        
        Args:
            field: Field
            entity: Parent entity
            
        Returns:
            Column arguments string
        """
        args = []
        
        # Type first
        type_arg = self._get_sqlalchemy_type(field)
        args.append(type_arg)
        
        # Primary key
        if field.primary_key:
            args.append("primary_key=True")
        
        # Nullable
        if not field.nullable:
            args.append("nullable=False")
        
        # Unique
        if field.unique:
            args.append("unique=True")
        
        # Index
        if field.index:
            args.append("index=True")
        
        # Default
        if field.default is not None:
            if isinstance(field.default, str):
                args.append(f"default={field.default!r}")
            else:
                args.append(f"default={field.default!r}")
        
        # Server default
        if field.server_default:
            args.append(f"server_default={field.server_default!r}")
        
        return ", ".join(args)

    def _get_sqlalchemy_type(self, field: Field) -> str:
        """
        Get SQLAlchemy type string.
        
        Args:
            field: Field
            
        Returns:
            SQLAlchemy type string
        """
        type_mapping = {
            FieldType.STRING: f"String({field.length or 255})",
            FieldType.INTEGER: "Integer()",
            FieldType.FLOAT: "Float()",
            FieldType.BOOLEAN: "Boolean()",
            FieldType.DATETIME: "DateTime()",
            FieldType.TEXT: "Text()",
            FieldType.UUID: "PGUUID(as_uuid=True)",
            FieldType.JSON: "JSONB()",
            FieldType.DECIMAL: f"Numeric({field.precision or 10}, {field.scale or 2})",
            FieldType.ENUM: f"String({field.length or 50})",
            FieldType.LARGE_BINARY: "LargeBinary()",
            FieldType.ARRAY: "ARRAY(String())",
        }
        
        return type_mapping.get(field.field_type, "String(255)")

    def _build_relationship_definitions(
        self,
        entity: Entity,
        all_entities: list[Entity],
    ) -> list[str]:
        """
        Build relationship definition code.
        
        Args:
            entity: Entity
            all_entities: Tất cả entities
            
        Returns:
            List của relationship definition code strings
        """
        definitions = []
        
        for rel in entity.relationships:
            rel_code = self._build_relationship_definition(rel, entity, all_entities)
            definitions.append(rel_code)
        
        return definitions

    def _build_relationship_definition(
        self,
        rel: Relationship,
        entity: Entity,
        all_entities: list[Entity],
    ) -> str:
        """
        Build một relationship definition code.
        
        Args:
            rel: Relationship
            entity: Parent entity
            all_entities: Tất cả entities
            
        Returns:
            Relationship definition code string
        """
        # Determine field name from back_populates or generate from target
        if rel.back_populates:
            field_name = rel.back_populates.lower()
            if not field_name.endswith("s"):
                field_name += "s"
        else:
            field_name = self.to_snake_case(rel.target) + "_rel"
        
        # Build type annotation
        if rel.rel_type == RelationshipType.ONE_TO_ONE:
            type_annotation = f"{rel.target} | None"
        else:
            type_annotation = f"list[{rel.target}]"
        
        # Build relationship arguments
        args = [f'"{rel.target}"']
        
        # uselist for one-to-one
        if rel.rel_type == RelationshipType.ONE_TO_ONE:
            args.append("uselist=False")
        
        # back_populates
        if rel.back_populates:
            args.append(f'back_populates="{rel.back_populates}"')
        
        # cascade
        if rel.cascade:
            args.append(f'cascade="{rel.cascade}"')
        
        # secondary for many-to-many
        if rel.secondary:
            args.append(f'secondary="{rel.secondary}"')
        
        # remote_side for self-referencing
        if rel.rel_type == RelationshipType.SELF_REFERENCING and rel.foreign_field:
            args.append(f'remote_side="{entity.id}.{rel.foreign_field}"')
        
        return f'''
    {field_name}: Mapped[{type_annotation}] = relationship({", ".join(args)})'''

    def _build_table_args(self, entity: Entity) -> str:
        """
        Build __table_args__ definition.
        
        Args:
            entity: Entity
            
        Returns:
            __table_args__ code string
        """
        args = []
        
        # Check constraints
        for constraint in entity.constraints:
            if constraint.constraint_type == ConstraintType.CHECK and constraint.condition:
                constraint_name = constraint.name or f"check_{'_'.join(constraint.condition.split())[:3]}"
                args.append(f'CheckConstraint({constraint.condition!r}, name="{constraint_name}")')
        
        # Indexes
        for index in entity.indexes:
            index_name = index.name or f"idx_{entity.id.lower()}_{'_'.join(index.fields)}"
            fields_str = ", ".join(f'"{f}"' for f in index.fields)
            if index.unique:
                args.append(f'Index("{index_name}", {fields_str}, unique=True)')
            else:
                args.append(f'Index("{index_name}", {fields_str})')
        
        if not args:
            return ""
        
        return f'''
    __table_args__ = (
{chr(10).join("        " + arg + "," for arg in args)}
    )'''

    def _build_lifecycle_hooks(self, entity: Entity) -> str:
        """
        Build lifecycle hook code.
        
        Args:
            entity: Entity
            
        Returns:
            Lifecycle hooks code string
        """
        if not entity.lifecycle_hooks:
            return ""
        
        hooks_code = "\n\n# Lifecycle Hooks\n"
        
        for hook in entity.lifecycle_hooks:
            hooks_code += f'''

@event.listens_for({entity.id}, "{hook.event.value}")
def {hook.hook_name}(mapper, connection, target):
    """{hook.hook_name.replace("_", " ").title()} hook."""
    pass  # TODO: Implement {hook.hook_name}
'''
        
        return hooks_code

    def _generate_code_fallback(
        self,
        context: dict[str, Any],
        error: Exception,
    ) -> str:
        """
        Fallback code generation nếu template failed.
        
        Args:
            context: Template context
            error: Error occurred
            
        Returns:
            Generated code string
        """
        entity = context["entity"]
        
        code = f'''"""
{entity.id} Entity Model

Tự động generate từ Entity DSL.
Error: {error}
"""

from __future__ import annotations
from api.app.database import Base
from sqlalchemy import Column
from sqlalchemy.orm import Mapped


class {entity.id}(Base):
    """{entity.id} entity model - TEMPLATE RENDERING FAILED."""
    
    __tablename__ = "{self.get_table_name(entity.id)}"
    
    # Template rendering failed: {error}
    # Please fix the template or use fallback generation.
'''
        return code