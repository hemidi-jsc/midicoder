"""
Tests cho Entity models.

Kiểm tra:
- FieldType enum
- RelationshipType enum
- ConstraintType enum
- LifecycleEvent enum
- Field dataclass
- Relationship dataclass
- Constraint dataclass
- Index dataclass
- LifecycleHook dataclass
- Entity dataclass

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.emitters.core.cp01_domain_model.models import (
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


class TestFieldType:
    """Tests cho FieldType enum."""

    def test_field_types_exist(self):
        """Kiểm tra tất cả field types được định nghĩa."""
        assert FieldType.STRING.value == "string"
        assert FieldType.INTEGER.value == "integer"
        assert FieldType.FLOAT.value == "float"
        assert FieldType.BOOLEAN.value == "boolean"
        assert FieldType.DATETIME.value == "datetime"
        assert FieldType.TEXT.value == "text"
        assert FieldType.UUID.value == "uuid"
        assert FieldType.JSON.value == "json"
        assert FieldType.DECIMAL.value == "decimal"
        assert FieldType.ENUM.value == "enum"
        assert FieldType.LARGE_BINARY.value == "largebinary"
        assert FieldType.ARRAY.value == "array"

    def test_field_type_from_string(self):
        """Kiểm tra parse field type từ string."""
        assert FieldType("string") == FieldType.STRING
        assert FieldType("uuid") == FieldType.UUID
        assert FieldType("datetime") == FieldType.DATETIME

    def test_field_type_invalid_raises(self):
        """Kiểm tra invalid field type raise ValueError."""
        with pytest.raises(ValueError):
            FieldType("invalid_type")


class TestRelationshipType:
    """Tests cho RelationshipType enum."""

    def test_relationship_types_exist(self):
        """Kiểm tra tất cả relationship types được định nghĩa."""
        assert RelationshipType.ONE_TO_ONE.value == "one-to-one"
        assert RelationshipType.ONE_TO_MANY.value == "one-to-many"
        assert RelationshipType.MANY_TO_MANY.value == "many-to-many"
        assert RelationshipType.SELF_REFERENCING.value == "self-referencing"
        assert RelationshipType.POLYMORPHIC.value == "polymorphic"


class TestConstraintType:
    """Tests cho ConstraintType enum."""

    def test_constraint_types_exist(self):
        """Kiểm tra tất cả constraint types được định nghĩa."""
        assert ConstraintType.UNIQUE.value == "unique"
        assert ConstraintType.CHECK.value == "check"
        assert ConstraintType.FOREIGN_KEY.value == "foreign_key"


class TestLifecycleEvent:
    """Tests cho LifecycleEvent enum."""

    def test_lifecycle_events_exist(self):
        """Kiểm tra tất cả lifecycle events được định nghĩa."""
        assert LifecycleEvent.BEFORE_INSERT.value == "before_insert"
        assert LifecycleEvent.AFTER_INSERT.value == "after_insert"
        assert LifecycleEvent.BEFORE_UPDATE.value == "before_update"
        assert LifecycleEvent.AFTER_UPDATE.value == "after_update"
        assert LifecycleEvent.BEFORE_DELETE.value == "before_delete"
        assert LifecycleEvent.AFTER_DELETE.value == "after_delete"


class TestField:
    """Tests cho Field dataclass."""

    def test_field_minimal(self):
        """Kiểm tra Field với tối thiểu attributes."""
        field = Field(name="email", field_type=FieldType.STRING)
        assert field.name == "email"
        assert field.field_type == FieldType.STRING
        assert field.nullable is True
        assert field.unique is False
        assert field.primary_key is False

    def test_field_with_all_options(self):
        """Kiểm tra Field với tất cả options."""
        field = Field(
            name="id",
            field_type=FieldType.UUID,
            nullable=False,
            unique=True,
            primary_key=True,
            index=True,
            default="uuid_generate_v4()",
        )
        assert field.name == "id"
        assert field.primary_key is True
        assert field.nullable is False
        assert field.unique is True

    def test_field_decimal_with_precision_scale(self):
        """Kiểm tra Field decimal với precision và scale."""
        field = Field(
            name="balance",
            field_type=FieldType.DECIMAL,
            precision=12,
            scale=2,
        )
        assert field.precision == 12
        assert field.scale == 2

    def test_field_enum_with_values(self):
        """Kiểm tra Field enum với enum_values."""
        field = Field(
            name="status",
            field_type=FieldType.ENUM,
            enum_values=["active", "inactive"],
        )
        assert field.enum_values == ["active", "inactive"]


class TestRelationship:
    """Tests cho Relationship dataclass."""

    def test_relationship_one_to_many(self):
        """Kiểm tra Relationship one-to-many."""
        rel = Relationship(
            rel_type=RelationshipType.ONE_TO_MANY,
            target="Order",
            back_populates="user",
        )
        assert rel.rel_type == RelationshipType.ONE_TO_MANY
        assert rel.target == "Order"
        assert rel.back_populates == "user"

    def test_relationship_many_to_many_with_secondary(self):
        """Kiểm tra Relationship many-to-many với secondary table."""
        rel = Relationship(
            rel_type=RelationshipType.MANY_TO_MANY,
            target="Role",
            secondary="user_roles",
            back_populates="users",
        )
        assert rel.rel_type == RelationshipType.MANY_TO_MANY
        assert rel.secondary == "user_roles"

    def test_relationship_with_cascade(self):
        """Kiểm tra Relationship với cascade option."""
        rel = Relationship(
            rel_type=RelationshipType.ONE_TO_ONE,
            target="UserProfile",
            cascade="all, delete-orphan",
            back_populates="user",
        )
        assert rel.cascade == "all, delete-orphan"


class TestConstraint:
    """Tests cho Constraint dataclass."""

    def test_check_constraint(self):
        """Kiểm tra Check constraint."""
        constraint = Constraint(
            constraint_type=ConstraintType.CHECK,
            name="check_balance_non_negative",
            condition="balance >= 0",
        )
        assert constraint.constraint_type == ConstraintType.CHECK
        assert constraint.condition == "balance >= 0"

    def test_unique_constraint(self):
        """Kiểm tra Unique constraint."""
        constraint = Constraint(
            constraint_type=ConstraintType.UNIQUE,
            fields=["email"],
        )
        assert constraint.constraint_type == ConstraintType.UNIQUE
        assert constraint.fields == ["email"]


class TestIndex:
    """Tests cho Index dataclass."""

    def test_index_with_name(self):
        """Kiểm tra Index với name."""
        index = Index(
            name="idx_user_status_created",
            fields=["status", "created_at"],
            unique=False,
        )
        assert index.name == "idx_user_status_created"
        assert index.fields == ["status", "created_at"]

    def test_index_unique(self):
        """Kiểm tra Unique index."""
        index = Index(fields=["email"], unique=True)
        assert index.unique is True


class TestLifecycleHook:
    """Tests cho LifecycleHook dataclass."""

    def test_lifecycle_hook_simple(self):
        """Kiểm tra LifecycleHook đơn giản."""
        hook = LifecycleHook(
            event=LifecycleEvent.BEFORE_INSERT,
            hook_name="set_default_tenant",
        )
        assert hook.event == LifecycleEvent.BEFORE_INSERT
        assert hook.hook_name == "set_default_tenant"
        assert hook.params == {}

    def test_lifecycle_hook_with_params(self):
        """Kiểm tra LifecycleHook với params."""
        hook = LifecycleHook(
            event=LifecycleEvent.AFTER_INSERT,
            hook_name="log_audit_event",
            params={"event_type": "USER_CREATED"},
        )
        assert hook.params == {"event_type": "USER_CREATED"}


class TestEntity:
    """Tests cho Entity dataclass."""

    def test_entity_minimal(self):
        """Kiểm tra Entity với tối thiểu attributes."""
        entity = Entity(id="User")
        assert entity.id == "User"
        assert entity.fields == []
        assert entity.relationships == []

    def test_entity_with_fields(self):
        """Kiểm tra Entity với fields."""
        entity = Entity(
            id="User",
            description="User entity",
            fields=[
                Field(name="id", field_type=FieldType.UUID, primary_key=True),
                Field(name="email", field_type=FieldType.STRING, unique=True),
            ],
        )
        assert len(entity.fields) == 2
        assert entity.fields[0].name == "id"
        assert entity.fields[1].name == "email"

    def test_entity_with_relationships(self):
        """Kiểm tra Entity với relationships."""
        entity = Entity(
            id="User",
            relationships=[
                Relationship(
                    rel_type=RelationshipType.ONE_TO_MANY,
                    target="Order",
                    back_populates="user",
                ),
            ],
        )
        assert len(entity.relationships) == 1
        assert entity.relationships[0].target == "Order"

    def test_entity_with_constraints(self):
        """Kiểm tra Entity với constraints."""
        entity = Entity(
            id="User",
            fields=[Field(name="id", field_type=FieldType.UUID, primary_key=True)],
            constraints=[
                Constraint(
                    constraint_type=ConstraintType.CHECK,
                    condition="age >= 0",
                ),
            ],
        )
        assert len(entity.constraints) == 1

    def test_entity_with_indexes(self):
        """Kiểm tra Entity với indexes."""
        entity = Entity(
            id="User",
            fields=[Field(name="id", field_type=FieldType.UUID, primary_key=True)],
            indexes=[
                Index(fields=["email"], unique=True),
            ],
        )
        assert len(entity.indexes) == 1

    def test_entity_with_lifecycle_hooks(self):
        """Kiểm tra Entity với lifecycle hooks."""
        entity = Entity(
            id="User",
            fields=[Field(name="id", field_type=FieldType.UUID, primary_key=True)],
            lifecycle_hooks=[
                LifecycleHook(
                    event=LifecycleEvent.BEFORE_INSERT,
                    hook_name="set_default_tenant",
                ),
            ],
        )
        assert len(entity.lifecycle_hooks) == 1

    def test_entity_full(self):
        """Kiểm tra Entity đầy đủ với tất cả attributes."""
        entity = Entity(
            id="User",
            description="User entity for authentication",
            fields=[
                Field(name="id", field_type=FieldType.UUID, primary_key=True),
                Field(name="email", field_type=FieldType.STRING, unique=True),
            ],
            relationships=[
                Relationship(
                    rel_type=RelationshipType.ONE_TO_MANY,
                    target="Order",
                    back_populates="user",
                ),
            ],
            constraints=[
                Constraint(
                    constraint_type=ConstraintType.CHECK,
                    condition="age >= 0",
                ),
            ],
            indexes=[
                Index(fields=["email"], unique=True),
            ],
            lifecycle_hooks=[
                LifecycleHook(
                    event=LifecycleEvent.BEFORE_INSERT,
                    hook_name="set_default_tenant",
                ),
            ],
        )
        assert entity.id == "User"
        assert len(entity.fields) == 2
        assert len(entity.relationships) == 1
        assert len(entity.constraints) == 1
        assert len(entity.indexes) == 1
        assert len(entity.lifecycle_hooks) == 1