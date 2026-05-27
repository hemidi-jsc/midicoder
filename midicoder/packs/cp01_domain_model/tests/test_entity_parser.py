"""
Tests cho EntityParser — YAML DSL parser cho CP01 Entity domain model.

Parse YAML DSL thành Entity objects với validation cho fields, relationships,
constraints, indexes, và lifecycle hooks.

CP01: Domain Model - Entity Parser
"""

import pytest
import yaml

from midicoder.packs.cp01_domain_model.entity_parser import EntityParser
from midicoder.packs.cp01_domain_model.models import (
    EntityField,
    EntityFieldType,
    Relationship,
    RelationshipType,
    Constraint,
    ConstraintType,
    Index,
    LifecycleHook,
    LifecycleEvent,
)
from midicoder.errors import ErrorCode, MidicoderError


# ===========================================================================
# TestEntityParserBasic — basic happy path
# ===========================================================================

class TestEntityParserBasic:
    """Tests cho basic happy path của EntityParser."""

    def test_parse_full_entity(self):
        """Parse valid YAML với all features: fields, relationships, constraints, indexes, lifecycle hooks."""
        yaml_content = """
entities:
  - id: User
    description: User entity
    fields:
      - name: id
        type: uuid
        primary_key: true
        nullable: false
      - name: email
        type: string
        nullable: false
        unique: true
        length: 255
      - name: status
        type: string
        default: active
    relationships:
      - type: one-to-many
        target: Order
        back_populates: user
        cascade: "all, delete-orphan"
    constraints:
      - type: unique
        name: uq_user_email
        fields:
          - email
      - type: check
        name: check_status
        condition: "status IN ('active', 'inactive', 'suspended')"
    indexes:
      - fields:
          - status
          - created_at
      - name: idx_user_email
        fields:
          - email
        unique: true
    lifecycle:
      before_insert:
        - set_defaults
      after_insert:
        - hook: audit_log
          params:
            table: users
"""
        parser = EntityParser()
        entities = parser.parse(yaml_content)

        assert len(entities) == 1
        entity = entities[0]

        # Verify entity identity
        assert entity.id == "User"
        assert entity.description == "User entity"

        # Verify fields
        assert len(entity.fields) == 3
        id_field = next(f for f in entity.fields if f.name == "id")
        assert id_field.field_type == EntityFieldType.UUID
        assert id_field.primary_key is True
        assert id_field.nullable is False

        email_field = next(f for f in entity.fields if f.name == "email")
        assert email_field.field_type == EntityFieldType.STRING
        assert email_field.nullable is False
        assert email_field.unique is True
        assert email_field.length == 255

        status_field = next(f for f in entity.fields if f.name == "status")
        assert status_field.default == "active"

        # Verify relationships
        assert len(entity.relationships) == 1
        rel = entity.relationships[0]
        assert rel.rel_type == RelationshipType.ONE_TO_MANY
        assert rel.target == "Order"
        assert rel.back_populates == "user"
        assert rel.cascade == "all, delete-orphan"

        # Verify constraints
        assert len(entity.constraints) == 2
        unique_c = entity.constraints[0]
        assert unique_c.constraint_type == ConstraintType.UNIQUE
        assert unique_c.name == "uq_user_email"
        assert unique_c.fields == ["email"]

        check_c = entity.constraints[1]
        assert check_c.constraint_type == ConstraintType.CHECK
        assert check_c.condition == "status IN ('active', 'inactive', 'suspended')"

        # Verify indexes
        assert len(entity.indexes) == 2
        assert entity.indexes[0].name == "idx_status_created_at"  # auto-generated
        assert entity.indexes[0].fields == ["status", "created_at"]
        assert entity.indexes[1].name == "idx_user_email"
        assert entity.indexes[1].unique is True

        # Verify lifecycle hooks
        assert len(entity.lifecycle_hooks) == 2
        assert entity.lifecycle_hooks[0].event == LifecycleEvent.BEFORE_INSERT
        assert entity.lifecycle_hooks[0].hook_name == "set_defaults"
        assert entity.lifecycle_hooks[0].params == {}

        assert entity.lifecycle_hooks[1].event == LifecycleEvent.AFTER_INSERT
        assert entity.lifecycle_hooks[1].hook_name == "audit_log"
        assert entity.lifecycle_hooks[1].params == {"table": "users"}

    def test_parse_multiple_entities(self):
        """Parse multiple entities in single YAML."""
        yaml_content = """
entities:
  - id: User
    fields:
      - name: id
        type: uuid
        primary_key: true
  - id: Order
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: total
        type: decimal
        precision: 10
        scale: 2
"""
        parser = EntityParser()
        entities = parser.parse(yaml_content)

        assert len(entities) == 2
        assert entities[0].id == "User"
        assert entities[1].id == "Order"

        # Verify Order has decimal field with precision/scale
        total_field = next(f for f in entities[1].fields if f.name == "total")
        assert total_field.field_type == EntityFieldType.DECIMAL
        assert total_field.precision == 10
        assert total_field.scale == 2

    def test_field_defaults(self):
        """Verify field defaults: nullable=True, unique=False, primary_key=False."""
        yaml_content = """
entities:
  - id: Item
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: title
        type: string
"""
        parser = EntityParser()
        entities = parser.parse(yaml_content)
        item = entities[0]

        title_field = next(f for f in item.fields if f.name == "title")
        assert title_field.nullable is True
        assert title_field.unique is False
        assert title_field.primary_key is False

    def test_index_auto_name_generation(self):
        """Verify index auto-name generation when name not provided."""
        yaml_content = """
entities:
  - id: Product
    fields:
      - name: id
        type: uuid
        primary_key: true
    indexes:
      - fields:
          - category
          - price
"""
        parser = EntityParser()
        entities = parser.parse(yaml_content)
        product = entities[0]

        assert len(product.indexes) == 1
        assert product.indexes[0].name == "idx_category_price"


# ===========================================================================
# TestEntityParserFieldTypes — all 12 field types
# ===========================================================================

class TestEntityParserFieldTypes:
    """Tests cho tất cả 12 field types được hỗ trợ."""

    def test_string_type(self):
        yaml_content = """
entities:
  - id: E
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: name
        type: string
"""
        entities = EntityParser().parse(yaml_content)
        field = next(f for f in entities[0].fields if f.name == "name")
        assert field.field_type == EntityFieldType.STRING

    def test_integer_type(self):
        yaml_content = """
entities:
  - id: E
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: count
        type: integer
"""
        entities = EntityParser().parse(yaml_content)
        field = next(f for f in entities[0].fields if f.name == "count")
        assert field.field_type == EntityFieldType.INTEGER

    def test_float_type(self):
        yaml_content = """
entities:
  - id: E
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: ratio
        type: float
"""
        entities = EntityParser().parse(yaml_content)
        field = next(f for f in entities[0].fields if f.name == "ratio")
        assert field.field_type == EntityFieldType.FLOAT

    def test_boolean_type(self):
        yaml_content = """
entities:
  - id: E
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: active
        type: boolean
"""
        entities = EntityParser().parse(yaml_content)
        field = next(f for f in entities[0].fields if f.name == "active")
        assert field.field_type == EntityFieldType.BOOLEAN

    def test_datetime_type(self):
        yaml_content = """
entities:
  - id: E
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: created_at
        type: datetime
"""
        entities = EntityParser().parse(yaml_content)
        field = next(f for f in entities[0].fields if f.name == "created_at")
        assert field.field_type == EntityFieldType.DATETIME

    def test_text_type(self):
        yaml_content = """
entities:
  - id: E
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: body
        type: text
"""
        entities = EntityParser().parse(yaml_content)
        field = next(f for f in entities[0].fields if f.name == "body")
        assert field.field_type == EntityFieldType.TEXT

    def test_uuid_type(self):
        yaml_content = """
entities:
  - id: E
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: ref_id
        type: uuid
"""
        entities = EntityParser().parse(yaml_content)
        field = next(f for f in entities[0].fields if f.name == "ref_id")
        assert field.field_type == EntityFieldType.UUID

    def test_json_type(self):
        yaml_content = """
entities:
  - id: E
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: metadata
        type: json
"""
        entities = EntityParser().parse(yaml_content)
        field = next(f for f in entities[0].fields if f.name == "metadata")
        assert field.field_type == EntityFieldType.JSON

    def test_decimal_type(self):
        yaml_content = """
entities:
  - id: E
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: amount
        type: decimal
        precision: 15
        scale: 4
"""
        entities = EntityParser().parse(yaml_content)
        field = next(f for f in entities[0].fields if f.name == "amount")
        assert field.field_type == EntityFieldType.DECIMAL
        assert field.precision == 15
        assert field.scale == 4

    def test_enum_type(self):
        yaml_content = """
entities:
  - id: E
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: role
        type: enum
        enum_values:
          - admin
          - editor
          - viewer
"""
        entities = EntityParser().parse(yaml_content)
        field = next(f for f in entities[0].fields if f.name == "role")
        assert field.field_type == EntityFieldType.ENUM
        assert field.enum_values == ["admin", "editor", "viewer"]

    def test_largebinary_type(self):
        yaml_content = """
entities:
  - id: E
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: data
        type: largebinary
"""
        entities = EntityParser().parse(yaml_content)
        field = next(f for f in entities[0].fields if f.name == "data")
        assert field.field_type == EntityFieldType.LARGE_BINARY

    def test_array_type(self):
        yaml_content = """
entities:
  - id: E
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: tags
        type: array
"""
        entities = EntityParser().parse(yaml_content)
        field = next(f for f in entities[0].fields if f.name == "tags")
        assert field.field_type == EntityFieldType.ARRAY

    def test_invalid_field_type_raises_error(self):
        yaml_content = """
entities:
  - id: E
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: bad
        type: blob
"""
        with pytest.raises(MidicoderError) as exc_info:
            EntityParser().parse(yaml_content)
        assert exc_info.value.code == ErrorCode.CP01_INVALID_FIELD_TYPE


# ===========================================================================
# TestEntityParserRelationships — all relationship types
# ===========================================================================

class TestEntityParserRelationships:
    """Tests cho tất cả relationship types và validation."""

    def test_one_to_one(self):
        yaml_content = """
entities:
  - id: User
    fields:
      - name: id
        type: uuid
        primary_key: true
    relationships:
      - type: one-to-one
        target: Profile
        back_populates: user
"""
        entities = EntityParser().parse(yaml_content)
        rel = entities[0].relationships[0]
        assert rel.rel_type == RelationshipType.ONE_TO_ONE
        assert rel.target == "Profile"

    def test_one_to_many(self):
        yaml_content = """
entities:
  - id: User
    fields:
      - name: id
        type: uuid
        primary_key: true
    relationships:
      - type: one-to-many
        target: Order
        back_populates: user
"""
        entities = EntityParser().parse(yaml_content)
        rel = entities[0].relationships[0]
        assert rel.rel_type == RelationshipType.ONE_TO_MANY

    def test_many_to_many(self):
        yaml_content = """
entities:
  - id: User
    fields:
      - name: id
        type: uuid
        primary_key: true
    relationships:
      - type: many-to-many
        target: Role
        secondary: user_roles
        back_populates: users
"""
        entities = EntityParser().parse(yaml_content)
        rel = entities[0].relationships[0]
        assert rel.rel_type == RelationshipType.MANY_TO_MANY
        assert rel.secondary == "user_roles"

    def test_self_referencing_detection(self):
        """Self-referencing: target == entity_id overrides declared type."""
        yaml_content = """
entities:
  - id: Employee
    fields:
      - name: id
        type: uuid
        primary_key: true
    relationships:
      - type: one-to-one
        target: Employee
        local_field: manager_id
"""
        entities = EntityParser().parse(yaml_content)
        rel = entities[0].relationships[0]
        assert rel.rel_type == RelationshipType.SELF_REFERENCING

    def test_polymorphic_detection(self):
        """Polymorphic flag overrides declared type."""
        yaml_content = """
entities:
  - id: Comment
    fields:
      - name: id
        type: uuid
        primary_key: true
    relationships:
      - type: one-to-many
        target: Post
        polymorphic: true
"""
        entities = EntityParser().parse(yaml_content)
        rel = entities[0].relationships[0]
        assert rel.rel_type == RelationshipType.POLYMORPHIC
        assert rel.polymorphic is True

    def test_many_to_many_without_secondary_raises_error(self):
        yaml_content = """
entities:
  - id: User
    fields:
      - name: id
        type: uuid
        primary_key: true
    relationships:
      - type: many-to-many
        target: Role
"""
        with pytest.raises(MidicoderError) as exc_info:
            EntityParser().parse(yaml_content)
        assert exc_info.value.code == ErrorCode.CP01_ENTITY_INVALID_RELATIONSHIP

    def test_relationship_without_target_raises_error(self):
        yaml_content = """
entities:
  - id: User
    fields:
      - name: id
        type: uuid
        primary_key: true
    relationships:
      - type: one-to-many
        back_populates: user
"""
        with pytest.raises(MidicoderError) as exc_info:
            EntityParser().parse(yaml_content)
        assert exc_info.value.code == ErrorCode.CP01_ENTITY_INVALID_RELATIONSHIP

    def test_invalid_relationship_type_raises_error(self):
        yaml_content = """
entities:
  - id: User
    fields:
      - name: id
        type: uuid
        primary_key: true
    relationships:
      - type: bidirectional
        target: Profile
"""
        with pytest.raises(MidicoderError) as exc_info:
            EntityParser().parse(yaml_content)
        assert exc_info.value.code == ErrorCode.CP01_ENTITY_INVALID_RELATIONSHIP


# ===========================================================================
# TestEntityParserConstraints — constraint types
# ===========================================================================

class TestEntityParserConstraints:
    """Tests cho constraint parsing và validation."""

    def test_unique_constraint(self):
        yaml_content = """
entities:
  - id: User
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: email
        type: string
    constraints:
      - type: unique
        name: uq_email
        fields:
          - email
"""
        entities = EntityParser().parse(yaml_content)
        c = entities[0].constraints[0]
        assert c.constraint_type == ConstraintType.UNIQUE
        assert c.name == "uq_email"
        assert c.fields == ["email"]

    def test_check_constraint(self):
        yaml_content = """
entities:
  - id: Account
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: balance
        type: decimal
    constraints:
      - type: check
        name: check_balance
        condition: "balance >= 0"
"""
        entities = EntityParser().parse(yaml_content)
        c = entities[0].constraints[0]
        assert c.constraint_type == ConstraintType.CHECK
        assert c.condition == "balance >= 0"

    def test_foreign_key_constraint(self):
        yaml_content = """
entities:
  - id: Order
    fields:
      - name: id
        type: uuid
        primary_key: true
      - name: user_id
        type: uuid
    constraints:
      - type: foreign_key
        name: fk_user
        fields:
          - user_id
"""
        entities = EntityParser().parse(yaml_content)
        c = entities[0].constraints[0]
        assert c.constraint_type == ConstraintType.FOREIGN_KEY

    def test_check_constraint_without_condition_raises_error(self):
        yaml_content = """
entities:
  - id: Account
    fields:
      - name: id
        type: uuid
        primary_key: true
    constraints:
      - type: check
        name: check_something
"""
        with pytest.raises(MidicoderError) as exc_info:
            EntityParser().parse(yaml_content)
        assert exc_info.value.code == ErrorCode.CP01_ENTITY_INVALID_CONSTRAINT

    def test_unique_constraint_without_fields_raises_error(self):
        yaml_content = """
entities:
  - id: User
    fields:
      - name: id
        type: uuid
        primary_key: true
    constraints:
      - type: unique
        name: uq_empty
"""
        with pytest.raises(MidicoderError) as exc_info:
            EntityParser().parse(yaml_content)
        assert exc_info.value.code == ErrorCode.CP01_ENTITY_INVALID_CONSTRAINT

    def test_invalid_constraint_type_raises_error(self):
        yaml_content = """
entities:
  - id: User
    fields:
      - name: id
        type: uuid
        primary_key: true
    constraints:
      - type: not_null
        fields:
          - email
"""
        with pytest.raises(MidicoderError) as exc_info:
            EntityParser().parse(yaml_content)
        assert exc_info.value.code == ErrorCode.CP01_ENTITY_INVALID_CONSTRAINT


# ===========================================================================
# TestEntityParserLifecycle — lifecycle hooks
# ===========================================================================

class TestEntityParserLifecycle:
    """Tests cho lifecycle hook parsing."""

    def test_all_six_events(self):
        """Parse before_insert, after_insert, before_update, after_update, before_delete, after_delete."""
        yaml_content = """
entities:
  - id: Audit
    fields:
      - name: id
        type: uuid
        primary_key: true
    lifecycle:
      before_insert:
        - set_created_at
      after_insert:
        - log_insert
      before_update:
        - set_updated_at
      after_update:
        - log_update
      before_delete:
        - soft_delete_check
      after_delete:
        - log_delete
"""
        entities = EntityParser().parse(yaml_content)
        hooks = entities[0].lifecycle_hooks
        assert len(hooks) == 6

        events = [h.event for h in hooks]
        assert LifecycleEvent.BEFORE_INSERT in events
        assert LifecycleEvent.AFTER_INSERT in events
        assert LifecycleEvent.BEFORE_UPDATE in events
        assert LifecycleEvent.AFTER_UPDATE in events
        assert LifecycleEvent.BEFORE_DELETE in events
        assert LifecycleEvent.AFTER_DELETE in events

    def test_simple_string_form(self):
        """Simple string form: just hook name, no params."""
        yaml_content = """
entities:
  - id: E
    fields:
      - name: id
        type: uuid
        primary_key: true
    lifecycle:
      before_insert:
        - set_defaults
        - normalize_email
"""
        entities = EntityParser().parse(yaml_content)
        hooks = entities[0].lifecycle_hooks
        assert len(hooks) == 2
        assert hooks[0].hook_name == "set_defaults"
        assert hooks[0].params == {}
        assert hooks[1].hook_name == "normalize_email"

    def test_dict_form_with_params(self):
        """Dict form with hook name and params."""
        yaml_content = """
entities:
  - id: E
    fields:
      - name: id
        type: uuid
        primary_key: true
    lifecycle:
      before_insert:
        - hook: set_field
          params:
            field: tenant_id
            value: current_tenant
"""
        entities = EntityParser().parse(yaml_content)
        hooks = entities[0].lifecycle_hooks
        assert len(hooks) == 1
        assert hooks[0].hook_name == "set_field"
        assert hooks[0].params == {"field": "tenant_id", "value": "current_tenant"}

    def test_invalid_event_name_raises_error(self):
        yaml_content = """
entities:
  - id: E
    fields:
      - name: id
        type: uuid
        primary_key: true
    lifecycle:
      on_create:
        - some_hook
"""
        with pytest.raises(MidicoderError) as exc_info:
            EntityParser().parse(yaml_content)
        assert exc_info.value.code == ErrorCode.CP01_ENTITY_INVALID_LIFECYCLE


# ===========================================================================
# TestEntityParserValidation — validation rules
# ===========================================================================

class TestEntityParserValidation:
    """Tests cho validation rules."""

    def test_entity_without_id_raises_error(self):
        yaml_content = """
entities:
  - description: No id here
    fields:
      - name: id
        type: uuid
        primary_key: true
"""
        with pytest.raises(MidicoderError) as exc_info:
            EntityParser().parse(yaml_content)
        assert exc_info.value.code == ErrorCode.CP01_ENTITY_NOT_FOUND

    def test_missing_entities_key_raises_error(self):
        yaml_content = """
models:
  - id: User
    fields:
      - name: id
        type: uuid
        primary_key: true
"""
        with pytest.raises(MidicoderError) as exc_info:
            EntityParser().parse(yaml_content)
        assert exc_info.value.code == ErrorCode.CP01_ENTITY_NOT_FOUND

    def test_field_without_name_raises_error(self):
        yaml_content = """
entities:
  - id: User
    fields:
      - name: id
        type: uuid
        primary_key: true
      - type: string
"""
        with pytest.raises(MidicoderError) as exc_info:
            EntityParser().parse(yaml_content)
        assert exc_info.value.code == ErrorCode.CP01_ENTITY_INVALID_FIELD

    def test_entity_without_fields_raises_error(self):
        yaml_content = """
entities:
  - id: EmptyEntity
"""
        with pytest.raises(MidicoderError) as exc_info:
            EntityParser().parse(yaml_content)
        assert exc_info.value.code == ErrorCode.CP01_ENTITY_INVALID_FIELD

    def test_entity_without_primary_key_raises_error(self):
        yaml_content = """
entities:
  - id: NoPK
    fields:
      - name: name
        type: string
"""
        with pytest.raises(MidicoderError) as exc_info:
            EntityParser().parse(yaml_content)
        assert exc_info.value.code == ErrorCode.CP01_ENTITY_INVALID_FIELD

    def test_invalid_yaml_syntax_raises_error(self):
        yaml_content = """
entities:
  - id: User
    fields:
      - name: id
        type: uuid
        primary_key: true
        this is bad yaml: [
"""
        with pytest.raises(MidicoderError) as exc_info:
            EntityParser().parse(yaml_content)
        assert exc_info.value.code == ErrorCode.DSL_YAML_PARSE_ERROR

    def test_empty_yaml_raises_error(self):
        yaml_content = ""
        with pytest.raises(MidicoderError) as exc_info:
            EntityParser().parse(yaml_content)
        assert exc_info.value.code == ErrorCode.CP01_ENTITY_NOT_FOUND

    def test_null_yaml_raises_error(self):
        yaml_content = "---\n"
        with pytest.raises(MidicoderError) as exc_info:
            EntityParser().parse(yaml_content)
        assert exc_info.value.code == ErrorCode.CP01_ENTITY_NOT_FOUND
