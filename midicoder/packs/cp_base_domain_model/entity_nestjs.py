"""
NestJS Entity Emitter.

NestJS-specific implementation của EntityEmitter.
Generate TypeORM entity code với support cho:
- Field types mapping sang TypeScript
- Relationships
- Indexes
- Constraints

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .entity_emitter import EntityEmitter
from .models import Entity, EntityField as Field, EntityFieldType as FieldType, Relationship
from midicoder.packs.models import RenderContextSpec


class NestJSEntityEmitter(EntityEmitter):
    """
    NestJS Entity Emitter.
    
    Generate TypeORM entity code từ Entity objects.
    
    Usage:
        emitter = NestJSEntityEmitter(stack_dir=Path("midicoder/stacks/nestjs/templates"))
        code = emitter.emit(entity, all_entities)
    """

    def __init__(self, stack_dir: Path) -> None:
        """
        Khởi tạo NestJSEntityEmitter.
        
        Args:
            stack_dir: Đường dẫn đến templates directory
        """
        super().__init__(stack_dir)

    def emit(self, entity: Entity, all_entities: list[Entity]) -> str:
        """
        Generate TypeORM entity code từ Entity.
        
        Args:
            entity: Entity để emit
            all_entities: Danh sách tất cả entities
            
        Returns:
            Generated TypeScript code
        """
        context = self._build_template_context(entity, all_entities)
        
        try:
            return self.render_template("entity.ts.jinja2", context)
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
        
        # Build property definitions
        property_definitions = self._build_property_definitions(entity, all_entities)
        
        return {
            "entity": entity,
            "table_name": self.get_table_name(entity.id),
            "imports": imports,
            "property_definitions": property_definitions,
            "render_context": (entity.render_context or RenderContextSpec()).to_dict(),
        }

    def _collect_imports(self, entity: Entity) -> dict[str, list[str]]:
        """
        Collect tất cả required imports.
        
        Args:
            entity: Entity
            
        Returns:
            Dictionary của imports
        """
        imports = {
            "typeorm": [
                "import { Entity, Column, PrimaryGeneratedColumn, Index } from 'typeorm';",
            ],
            "common": [
                "import { IsString, IsOptional } from 'class-validator';",
            ],
        }
        
        # Add relationship imports
        has_relationships = any(
            r.rel_type.value != "self-referencing"
            for r in entity.relationships
        ) if entity.relationships else False
        
        if has_relationships:
            imports["typeorm"].append(
                "import { ManyToOne, OneToMany, OneToOne, ManyToMany, JoinTable } from 'typeorm';"
            )
        
        return imports

    def _get_typeScript_type(self, field_type: FieldType) -> str:
        """
        Get TypeScript type cho field type.
        
        Args:
            field_type: FieldType enum
            
        Returns:
            TypeScript type string
        """
        type_mapping = {
            FieldType.STRING: "string",
            FieldType.INTEGER: "number",
            FieldType.FLOAT: "number",
            FieldType.BOOLEAN: "boolean",
            FieldType.DATETIME: "Date",
            FieldType.TEXT: "string",
            FieldType.UUID: "string",
            FieldType.JSON: "any",
            FieldType.DECIMAL: "number",
            FieldType.ENUM: "string",
            FieldType.LARGE_BINARY: "Buffer",
            FieldType.ARRAY: "string[]",
        }
        
        return type_mapping.get(field_type, "any")

    def _build_property_definitions(
        self,
        entity: Entity,
        all_entities: list[Entity],
    ) -> list[str]:
        """
        Build property definition code.
        
        Args:
            entity: Entity
            all_entities: Tất cả entities
            
        Returns:
            List của property definition code strings
        """
        definitions = []
        
        # Build field definitions
        for field in entity.fields:
            field_code = self._build_field_definition(field)
            definitions.append(field_code)
        
        # Build relationship definitions
        for rel in entity.relationships:
            rel_code = self._build_relationship_definition(rel, entity, all_entities)
            definitions.append(rel_code)
        
        return definitions

    def _build_field_definition(self, field: Field) -> str:
        """
        Build một field definition code.
        
        Args:
            field: Field
            
        Returns:
            Field definition code string
        """
        ts_type = self._get_typeScript_type(field.field_type)
        
        lines = []
        
        # Decorator
        if field.primary_key:
            lines.append(f"  @PrimaryGeneratedColumn('uuid')")
        else:
            lines.append(f"  @Column()")
        
        # Validation decorators
        if not field.nullable:
            pass  # IsString, etc.
        
        if field.nullable:
            lines.append(f"  @IsOptional()")
        
        # Property
        lines.append(f"  {field.name}: {ts_type};")
        
        return "\n".join(lines)

    def _build_relationship_definition(
        self,
        rel: Relationship,
        entity: Entity,
        all_entities: list[Entity],
    ) -> str:
        """
        Build relationship definition code.
        
        Args:
            rel: Relationship
            entity: Parent entity
            all_entities: Tất cả entities
            
        Returns:
            Relationship definition code string
        """
        lines = []
        
        # Determine decorator based on relationship type
        decorator_mapping = {
            "one-to-one": "@OneToOne(() => {rel.target})",
            "one-to-many": "@OneToMany(() => {rel.target}, (target) => target.{rel.back_populates})",
            "many-to-one": "@ManyToOne(() => {rel.target})",
            "many-to-many": "@ManyToMany(() => {rel.target})",
        }
        
        rel_type = rel.rel_type.value
        decorator = decorator_mapping.get(rel_type, "@Column()")
        lines.append(f"  {decorator}")
        
        # Property
        field_name = rel.back_populates.lower() if rel.back_populates else f"{self.to_snake_case(rel.target)}"
        lines.append(f"  {field_name}: {rel.target};")
        
        return "\n".join(lines)

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
        
        code = f'''/**
 * {entity.id} Entity
 * 
 * Tự động generate từ Entity DSL.
 * Error: {error}
 */

import {{ Entity, Column, PrimaryGeneratedColumn }} from 'typeorm';

@Entity("{self.get_table_name(entity.id)}")
export class {entity.id} {{
  /** {entity.id} entity - TEMPLATE RENDERING FAILED */
  
  // Template rendering failed: {error}
  // Please fix the template or use fallback generation.
}}
'''
        return code