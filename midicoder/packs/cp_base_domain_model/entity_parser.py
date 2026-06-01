"""
Mô-đun parser cho Entity DSL.

Cung cấp:
- EntityParser: Parse YAML DSL → Entity objects
- Validation cho fields, relationships, constraints, lifecycle hooks

Sử dụng:
    from midicoder.packs.cp_base_domain_model import EntityParser

    parser = EntityParser()
    entities = parser.parse(yaml_string)
    # entities: list[Entity]

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from typing import Any

import yaml

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

from .models import (
    Entity,
    EntityField as Field,
    EntityFieldType as FieldType,
    Relationship,
    RelationshipType,
    Constraint,
    ConstraintType,
    Index,
    LifecycleHook,
    LifecycleEvent,
)


class EntityParser:
    """
    Parser cho Entity DSL YAML.
    
    Parse YAML DSL thành list của Entity objects với validation.
    
    Usage:
        parser = EntityParser()
        entities = parser.parse(yaml_string)
    """

    def __init__(self) -> None:
        """Khởi tạo EntityParser."""
        pass

    def parse(self, yaml_content: str) -> list[Entity]:
        """
        Parse YAML content thành list Entity objects.
        
        Args:
            yaml_content: YAML string chứa entity definitions
            
        Returns:
            List của Entity objects
            
        Raises:
            MidicoderError: Nếu YAML không hợp lệ hoặc validation failed
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            EM.raise_error(
                ErrorCode.DSL_YAML_PARSE_ERROR,
                error=str(e),
            )
        
        if not data or "entities" not in data:
            EM.raise_error(
                ErrorCode.B01_ENTITY_NOT_FOUND,
                reason="Missing 'entities' key in YAML",
            )
        
        entities = []
        for entity_def in data.get("entities", []):
            entity = self._parse_entity(entity_def)
            entities.append(entity)
        
        return entities

    def _parse_entity(self, entity_def: dict[str, Any]) -> Entity:
        """
        Parse entity definition dict thành Entity object.
        
        Args:
            entity_def: Entity definition dict
            
        Returns:
            Entity object
        """
        if not entity_def.get("id"):
            EM.raise_error(
                ErrorCode.B01_ENTITY_NOT_FOUND,
                reason="Entity 'id' is required",
            )
        
        entity_id = entity_def["id"]
        entity = Entity(
            id=entity_id,
            description=entity_def.get("description"),
        )
        
        # Parse fields
        if "fields" in entity_def:
            entity.fields = [self._parse_field(f) for f in entity_def["fields"]]
        
        # Parse relationships
        if "relationships" in entity_def:
            entity.relationships = [
                self._parse_relationship(r, entity_id)
                for r in entity_def["relationships"]
            ]
        
        # Parse constraints
        if "constraints" in entity_def:
            entity.constraints = [
                self._parse_constraint(c)
                for c in entity_def["constraints"]
            ]
        
        # Parse indexes
        if "indexes" in entity_def:
            entity.indexes = [self._parse_index(idx) for idx in entity_def["indexes"]]
        
        # Parse lifecycle hooks
        if "lifecycle" in entity_def:
            entity.lifecycle_hooks = self._parse_lifecycle_hooks(
                entity_def["lifecycle"],
                entity_id,
            )
        
        # Validate entity
        self._validate_entity(entity)
        
        return entity

    def _parse_field(self, field_def: dict[str, Any]) -> Field:
        """
        Parse field definition dict thành Field object.
        
        Args:
            field_def: Field definition dict
            
        Returns:
            Field object
        """
        if not field_def.get("name"):
            EM.raise_error(
                ErrorCode.B01_ENTITY_INVALID_FIELD,
                reason="Field 'name' is required",
            )
        
        field_type_str = field_def.get("type", "string")
        field_type = self._parse_field_type(field_type_str)
        
        return Field(
            name=field_def["name"],
            field_type=field_type,
            nullable=field_def.get("nullable", True),
            unique=bool(field_def.get("unique", False)),
            primary_key=bool(field_def.get("primary_key", False)),
            index=bool(field_def.get("index", False)),
            default=field_def.get("default"),
            server_default=field_def.get("server_default"),
            length=field_def.get("length"),
            precision=field_def.get("precision"),
            scale=field_def.get("scale"),
            enum_values=field_def.get("enum_values"),
            description=field_def.get("description"),
        )

    def _parse_field_type(self, type_str: str) -> FieldType:
        """
        Parse string thành FieldType enum.
        
        Args:
            type_str: String type name
            
        Returns:
            FieldType enum value
            
        Raises:
            MidicoderError: Nếu type không hợp lệ
        """
        type_mapping = {
            "string": FieldType.STRING,
            "integer": FieldType.INTEGER,
            "float": FieldType.FLOAT,
            "boolean": FieldType.BOOLEAN,
            "datetime": FieldType.DATETIME,
            "text": FieldType.TEXT,
            "uuid": FieldType.UUID,
            "json": FieldType.JSON,
            "decimal": FieldType.DECIMAL,
            "enum": FieldType.ENUM,
            "largebinary": FieldType.LARGE_BINARY,
            "large_binary": FieldType.LARGE_BINARY,
            "array": FieldType.ARRAY,
        }
        
        type_lower = type_str.lower()
        if type_lower not in type_mapping:
            EM.raise_error(
                ErrorCode.B01_INVALID_FIELD_TYPE,
                field_type=type_str,
                supported_types=list(type_mapping.keys()),
            )
        
        return type_mapping[type_lower]

    def _parse_relationship(
        self,
        rel_def: dict[str, Any],
        entity_id: str,
    ) -> Relationship:
        """
        Parse relationship definition dict thành Relationship object.
        
        Args:
            rel_def: Relationship definition dict
            entity_id: Current entity ID (for self-ref detection)
            
        Returns:
            Relationship object
        """
        rel_type_str = rel_def.get("type", "one-to-many")
        rel_type = self._parse_relationship_type(rel_type_str)

        # Detect self-referencing before target validation
        is_self_ref = rel_type == RelationshipType.SELF_REFERENCING
        is_polymorphic = bool(rel_def.get("polymorphic", False))
        if is_polymorphic:
            rel_type = RelationshipType.POLYMORPHIC

        target = rel_def.get("target", "")
        # For self-referencing relationships, default target to entity's own ID
        if not target and is_self_ref:
            target = entity_id
        # For polymorphic relationships, target is optional (may reference multiple types)
        if not target and is_polymorphic:
            target = entity_id
        if not target:
            EM.raise_error(
                ErrorCode.B01_ENTITY_INVALID_RELATIONSHIP,
                reason="Relationship 'target' is required",
            )

        # Re-detect self-referencing from target value
        is_self_ref = is_self_ref or target.lower() == entity_id.lower()
        if is_self_ref:
            rel_type = RelationshipType.SELF_REFERENCING
        
        return Relationship(
            rel_type=rel_type,
            target=target,
            local_field=rel_def.get("local_field"),
            foreign_field=rel_def.get("foreign_field"),
            back_populates=rel_def.get("back_populates"),
            cascade=rel_def.get("cascade"),
            secondary=rel_def.get("secondary"),
            polymorphic=is_polymorphic,
            description=rel_def.get("description"),
        )

    def _parse_relationship_type(self, type_str: str) -> RelationshipType:
        """
        Parse string thành RelationshipType enum.
        
        Args:
            type_str: String type name
            
        Returns:
            RelationshipType enum value
        """
        type_mapping = {
            "one-to-one": RelationshipType.ONE_TO_ONE,
            "one_to_one": RelationshipType.ONE_TO_ONE,
            "one-to-many": RelationshipType.ONE_TO_MANY,
            "one_to_many": RelationshipType.ONE_TO_MANY,
            "many-to-many": RelationshipType.MANY_TO_MANY,
            "many_to_many": RelationshipType.MANY_TO_MANY,
            "self-referencing": RelationshipType.SELF_REFERENCING,
            "self_referencing": RelationshipType.SELF_REFERENCING,
            "polymorphic": RelationshipType.POLYMORPHIC,
        }
        
        type_lower = type_str.lower()
        if type_lower not in type_mapping:
            EM.raise_error(
                ErrorCode.B01_ENTITY_INVALID_RELATIONSHIP,
                rel_type=type_str,
                supported_types=list(type_mapping.keys()),
            )
        
        return type_mapping[type_lower]

    def _parse_constraint(self, constraint_def: dict[str, Any]) -> Constraint:
        """
        Parse constraint definition dict thành Constraint object.
        
        Args:
            constraint_def: Constraint definition dict
            
        Returns:
            Constraint object
        """
        constraint_type_str = constraint_def.get("type", "unique")
        constraint_type = self._parse_constraint_type(constraint_type_str)
        
        return Constraint(
            constraint_type=constraint_type,
            name=constraint_def.get("name"),
            fields=constraint_def.get("fields"),
            condition=constraint_def.get("condition"),
            description=constraint_def.get("description"),
        )

    def _parse_constraint_type(self, type_str: str) -> ConstraintType:
        """
        Parse string thành ConstraintType enum.
        
        Args:
            type_str: String type name
            
        Returns:
            ConstraintType enum value
        """
        type_mapping = {
            "unique": ConstraintType.UNIQUE,
            "check": ConstraintType.CHECK,
            "foreign_key": ConstraintType.FOREIGN_KEY,
            "foreign-key": ConstraintType.FOREIGN_KEY,
        }
        
        type_lower = type_str.lower()
        if type_lower not in type_mapping:
            EM.raise_error(
                ErrorCode.B01_ENTITY_INVALID_CONSTRAINT,
                constraint_type=type_str,
                supported_types=list(type_mapping.keys()),
            )
        
        return type_mapping[type_lower]

    def _parse_index(self, index_def: dict[str, Any]) -> Index:
        """
        Parse index definition dict thành Index object.
        
        Args:
            index_def: Index definition dict
            
        Returns:
            Index object
        """
        # Generate name if not provided
        name = index_def.get("name")
        fields = index_def.get("fields", [])
        
        if not name and fields:
            name = f"idx_{'_'.join(fields)}"
        
        return Index(
            name=name,
            fields=fields,
            unique=bool(index_def.get("unique", False)),
        )

    def _parse_lifecycle_hooks(
        self,
        lifecycle_def: dict[str, Any],
        entity_id: str,
    ) -> list[LifecycleHook]:
        """
        Parse lifecycle definition thành list LifecycleHook objects.
        
        Args:
            lifecycle_def: Lifecycle definition dict
            entity_id: Entity ID (for hook naming)
            
        Returns:
            List của LifecycleHook objects
        """
        hooks = []
        event_mapping = {
            "before_insert": LifecycleEvent.BEFORE_INSERT,
            "after_insert": LifecycleEvent.AFTER_INSERT,
            "before_update": LifecycleEvent.BEFORE_UPDATE,
            "after_update": LifecycleEvent.AFTER_UPDATE,
            "before_delete": LifecycleEvent.BEFORE_DELETE,
            "after_delete": LifecycleEvent.AFTER_DELETE,
        }
        
        for event_str, hooks_list in lifecycle_def.items():
            event = event_mapping.get(event_str.lower())
            if not event:
                EM.raise_error(
                    ErrorCode.B01_ENTITY_INVALID_LIFECYCLE,
                    event_name=event_str,
                    valid_events=list(event_mapping.keys()),
                )
            
            for hook_def in hooks_list:
                if isinstance(hook_def, str):
                    # Simple form: just hook name
                    hook_name = hook_def
                    params = {}
                elif isinstance(hook_def, dict):
                    hook_name = hook_def.get("hook", hook_def.get("name", ""))
                    params = hook_def.get("params", {})
                else:
                    continue
                
                if not hook_name:
                    continue
                
                hooks.append(LifecycleHook(
                    event=event,
                    hook_name=hook_name,
                    params=params,
                ))
        
        return hooks

    def _validate_entity(self, entity: Entity) -> None:
        """
        Validate Entity object.
        
        Args:
            entity: Entity to validate
            
        Raises:
            MidicoderError: Nếu validation failed
        """
        # Check for at least one field
        if not entity.fields:
            EM.raise_error(
                ErrorCode.B01_ENTITY_INVALID_FIELD,
                entity_id=entity.id,
                reason="Entity must have at least one field",
            )
        
        # Check for primary key
        has_pk = any(f.primary_key for f in entity.fields)
        if not has_pk:
            EM.raise_error(
                ErrorCode.B01_ENTITY_INVALID_FIELD,
                entity_id=entity.id,
                reason="Entity must have a primary key field",
            )
        
        # Check unique constraint for check constraints
        for constraint in entity.constraints:
            if constraint.constraint_type == ConstraintType.CHECK:
                if not constraint.condition:
                    EM.raise_error(
                        ErrorCode.B01_ENTITY_INVALID_CONSTRAINT,
                        entity_id=entity.id,
                        reason="Check constraint must have 'condition'",
                    )
            
            if constraint.constraint_type == ConstraintType.UNIQUE:
                if not constraint.fields:
                    EM.raise_error(
                        ErrorCode.B01_ENTITY_INVALID_CONSTRAINT,
                        entity_id=entity.id,
                        reason="Unique constraint must have 'fields'",
                    )
        
        # Check many-to-many requires secondary table
        for rel in entity.relationships:
            if rel.rel_type == RelationshipType.MANY_TO_MANY:
                if not rel.secondary:
                    EM.raise_error(
                        ErrorCode.B01_ENTITY_INVALID_RELATIONSHIP,
                        entity_id=entity.id,
                        target=rel.target,
                        reason="Many-to-many relationship requires 'secondary' table",
                    )