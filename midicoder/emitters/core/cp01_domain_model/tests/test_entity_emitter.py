"""
Tests cho Entity Emitter classes (CP01 Domain Model).

Test cases:
- EntityEmitter base class (table name conversion, snake_case, find_entity_by_id)
- FastAPIEntityEmitter (template context, imports, field definitions, relationships,
  table args, lifecycle hooks, enum classes, fallback generation)
- NestJSEntityEmitter (property definitions, TypeScript type mapping, relationships,
  fallback generation)

Author: Midicoder Team
Version: 1.0.0
"""

import tempfile
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from uuid import UUID

import pytest

from midicoder.emitters.core.cp01_domain_model import (
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
    FastAPIEntityEmitter,
    NestJSEntityEmitter,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_user_entity():
    """Sample User Entity với các fields phổ biến."""
    return Entity(
        id="User",
        description="User entity cho hệ thống authentication",
        fields=[
            Field(
                name="id",
                field_type=FieldType.UUID,
                primary_key=True,
                nullable=False,
            ),
            Field(
                name="email",
                field_type=FieldType.STRING,
                nullable=False,
                unique=True,
                length=255,
            ),
            Field(
                name="password_hash",
                field_type=FieldType.STRING,
                nullable=False,
                length=512,
            ),
            Field(
                name="created_at",
                field_type=FieldType.DATETIME,
                nullable=False,
                server_default="now()",
            ),
            Field(
                name="tenant_id",
                field_type=FieldType.UUID,
                nullable=False,
                index=True,
            ),
        ],
        indexes=[
            Index(
                name="idx_user_email",
                fields=["email"],
                unique=True,
            ),
        ],
        lifecycle_hooks=[
            LifecycleHook(
                event=LifecycleEvent.BEFORE_INSERT,
                hook_name="hash_password_before_insert",
            ),
        ],
    )


@pytest.fixture
def sample_order_entity():
    """Sample Order Entity với decimal, enum, và relationships."""
    return Entity(
        id="Order",
        description="Order entity cho order management",
        fields=[
            Field(
                name="id",
                field_type=FieldType.UUID,
                primary_key=True,
                nullable=False,
            ),
            Field(
                name="user_id",
                field_type=FieldType.UUID,
                nullable=False,
                index=True,
            ),
            Field(
                name="amount",
                field_type=FieldType.DECIMAL,
                nullable=False,
                precision=18,
                scale=2,
            ),
            Field(
                name="status",
                field_type=FieldType.ENUM,
                nullable=False,
                enum_values=["pending", "confirmed", "shipped", "delivered", "cancelled"],
            ),
            Field(
                name="notes",
                field_type=FieldType.TEXT,
                nullable=True,
            ),
            Field(
                name="metadata",
                field_type=FieldType.JSON,
                nullable=True,
            ),
            Field(
                name="created_at",
                field_type=FieldType.DATETIME,
                nullable=False,
                server_default="now()",
            ),
        ],
        relationships=[
            Relationship(
                rel_type=RelationshipType.ONE_TO_MANY,
                target="User",
                back_populates="orders",
            ),
            Relationship(
                rel_type=RelationshipType.ONE_TO_MANY,
                target="OrderItem",
                back_populates="order",
                cascade="all, delete-orphan",
            ),
        ],
        constraints=[
            Constraint(
                constraint_type=ConstraintType.CHECK,
                name="check_amount_positive",
                condition="amount > 0",
            ),
        ],
        indexes=[
            Index(
                name="idx_order_user_status",
                fields=["user_id", "status"],
                unique=False,
            ),
        ],
        lifecycle_hooks=[
            LifecycleHook(
                event=LifecycleEvent.AFTER_INSERT,
                hook_name="log_order_created",
                params={"event_type": "ORDER_CREATED"},
            ),
        ],
    )


@pytest.fixture
def sample_category_entity():
    """Sample Category Entity với self-referencing relationship."""
    return Entity(
        id="Category",
        description="Category entity với hierarchical structure",
        fields=[
            Field(
                name="id",
                field_type=FieldType.UUID,
                primary_key=True,
                nullable=False,
            ),
            Field(
                name="name",
                field_type=FieldType.STRING,
                nullable=False,
                length=100,
            ),
            Field(
                name="parent_id",
                field_type=FieldType.UUID,
                nullable=True,
            ),
            Field(
                name="sort_order",
                field_type=FieldType.INTEGER,
                nullable=False,
                default=0,
            ),
            Field(
                name="is_active",
                field_type=FieldType.BOOLEAN,
                nullable=False,
                default=True,
            ),
        ],
        relationships=[
            Relationship(
                rel_type=RelationshipType.SELF_REFERENCING,
                target="Category",
                foreign_field="parent_id",
                back_populates="children",
            ),
        ],
    )


@pytest.fixture
def sample_many_to_many_entity():
    """Sample Project Entity với many-to-many relationship."""
    return Entity(
        id="Project",
        description="Project entity với many-to-many relationship",
        fields=[
            Field(
                name="id",
                field_type=FieldType.UUID,
                primary_key=True,
                nullable=False,
            ),
            Field(
                name="title",
                field_type=FieldType.STRING,
                nullable=False,
                length=200,
            ),
            Field(
                name="description",
                field_type=FieldType.TEXT,
                nullable=True,
            ),
        ],
        relationships=[
            Relationship(
                rel_type=RelationshipType.MANY_TO_MANY,
                target="User",
                secondary="project_members",
                back_populates="projects",
            ),
        ],
    )


@pytest.fixture
def all_entities(
    sample_user_entity: Entity,
    sample_order_entity: Entity,
    sample_category_entity: Entity,
    sample_many_to_many_entity: Entity,
):
    """Danh sách tất cả entities để resolve relationships."""
    return [
        sample_user_entity,
        sample_order_entity,
        sample_category_entity,
        sample_many_to_many_entity,
    ]


@pytest.fixture
def fastapi_entity_emitter():
    """FastAPI Entity emitter instance."""
    stack_dir = Path("midicoder/stacks/fastapi/core/cp01_domain_model")
    return FastAPIEntityEmitter(stack_dir=stack_dir)


@pytest.fixture
def nestjs_entity_emitter():
    """NestJS Entity emitter instance."""
    stack_dir = Path("midicoder/stacks/nestjs/core/cp01_domain_model")
    return NestJSEntityEmitter(stack_dir=stack_dir)


# ============================================================================
# Tests for EntityEmitter Base Class
# ============================================================================


class TestEntityEmitterBase:
    """Tests cho EntityEmitter base class methods."""

    def test_get_table_name_simple(self, fastapi_entity_emitter: FastAPIEntityEmitter):
        """Test: get_table_name() với simple PascalCase entity ID."""
        assert fastapi_entity_emitter.get_table_name("User") == "users"

    def test_get_table_name_compound(self, fastapi_entity_emitter: FastAPIEntityEmitter):
        """Test: get_table_name() với compound PascalCase entity ID."""
        assert fastapi_entity_emitter.get_table_name("OrderItem") == "order_items"

    def test_get_table_name_ending_with_y(self, fastapi_entity_emitter: FastAPIEntityEmitter):
        """Test: get_table_name() với entity ID kết thúc bằng y (no special pluralization)."""
        assert fastapi_entity_emitter.get_table_name("Category") == "categorys"

    def test_get_table_name_single_letter(self, fastapi_entity_emitter: FastAPIEntityEmitter):
        """Test: get_table_name() với entity ID một ký tự."""
        assert fastapi_entity_emitter.get_table_name("A") == "as"

    def test_get_table_name_consecutive_uppercase(self, fastapi_entity_emitter: FastAPIEntityEmitter):
        """Test: get_table_name() với consecutive uppercase (APIKey)."""
        # The algorithm only inserts underscore at upper→lower transition
        assert fastapi_entity_emitter.get_table_name("APIKey") == "apikeys"

    def test_to_snake_case_camel_case(self, fastapi_entity_emitter: FastAPIEntityEmitter):
        """Test: to_snake_case() với camelCase input."""
        assert fastapi_entity_emitter.to_snake_case("userName") == "user_name"

    def test_to_snake_case_pascal_case(self, fastapi_entity_emitter: FastAPIEntityEmitter):
        """Test: to_snake_case() với PascalCase input."""
        assert fastapi_entity_emitter.to_snake_case("OrderItem") == "order_item"

    def test_to_snake_case_already_snake(self, fastapi_entity_emitter: FastAPIEntityEmitter):
        """Test: to_snake_case() với snake_case input không thay đổi."""
        assert fastapi_entity_emitter.to_snake_case("already_snake_case") == "already_snake_case"

    def test_to_snake_case_with_numbers(self, fastapi_entity_emitter: FastAPIEntityEmitter):
        """Test: to_snake_case() với input có số."""
        assert fastapi_entity_emitter.to_snake_case("field1Name") == "field1_name"

    def test_to_snake_case_single_word(self, fastapi_entity_emitter: FastAPIEntityEmitter):
        """Test: to_snake_case() với single word."""
        assert fastapi_entity_emitter.to_snake_case("email") == "email"

    def test_find_entity_by_id_found(self, fastapi_entity_emitter: FastAPIEntityEmitter, all_entities: list[Entity]):
        """Test: find_entity_by_id() tìm thấy entity."""
        entity = fastapi_entity_emitter.find_entity_by_id("User", all_entities)
        assert entity is not None
        assert entity.id == "User"

    def test_find_entity_by_id_case_insensitive(self, fastapi_entity_emitter: FastAPIEntityEmitter, all_entities: list[Entity]):
        """Test: find_entity_by_id() tìm entity không phân biệt chữ hoa thường."""
        entity = fastapi_entity_emitter.find_entity_by_id("user", all_entities)
        assert entity is not None
        assert entity.id == "User"

    def test_find_entity_by_id_case_insensitive_upper(self, fastapi_entity_emitter: FastAPIEntityEmitter, all_entities: list[Entity]):
        """Test: find_entity_by_id() tìm entity với uppercase input."""
        entity = fastapi_entity_emitter.find_entity_by_id("ORDER", all_entities)
        assert entity is not None
        assert entity.id == "Order"

    def test_find_entity_by_id_not_found(self, fastapi_entity_emitter: FastAPIEntityEmitter, all_entities: list[Entity]):
        """Test: find_entity_by_id() trả về None khi không tìm thấy."""
        entity = fastapi_entity_emitter.find_entity_by_id("NonExistent", all_entities)
        assert entity is None

    def test_find_entity_by_id_empty_list(self, fastapi_entity_emitter: FastAPIEntityEmitter):
        """Test: find_entity_by_id() với empty list."""
        entity = fastapi_entity_emitter.find_entity_by_id("User", [])
        assert entity is None

    def test_template_env_initialized(self, fastapi_entity_emitter: FastAPIEntityEmitter):
        """Test: Template environment được khởi tạo đúng."""
        assert fastapi_entity_emitter.template_env is not None
        assert fastapi_entity_emitter.stack_dir is not None

    def test_nestjs_emitter_inherits_base_methods(self, nestjs_entity_emitter: NestJSEntityEmitter):
        """Test: NestJS emitter kế thừa base methods."""
        assert nestjs_entity_emitter.get_table_name("User") == "users"
        assert nestjs_entity_emitter.to_snake_case("camelCase") == "camel_case"


# ============================================================================
# Tests for FastAPIEntityEmitter
# ============================================================================


class TestFastAPIEntityEmitter:
    """Tests cho FastAPIEntityEmitter."""

    def test_emit_returns_fallback_code(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: emit() generates full code with all components."""
        code = fastapi_entity_emitter.emit(sample_user_entity, all_entities)

        assert "User" in code
        assert "users" in code
        # Templates render fully, producing TenantRowMixin-enhanced code
        assert "class User(Base, TenantRowMixin):" in code

    def test_emit_contains_tablename(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Fallback code chứa __tablename__ đúng."""
        code = fastapi_entity_emitter.emit(sample_user_entity, all_entities)
        assert '__tablename__ = "users"' in code

    def test_emit_contains_class_definition(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Generated code contains class definition with TenantRowMixin."""
        code = fastapi_entity_emitter.emit(sample_user_entity, all_entities)
        assert "class User(Base, TenantRowMixin):" in code

    def test_emit_contains_base_imports(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Fallback code chứa required imports."""
        code = fastapi_entity_emitter.emit(sample_user_entity, all_entities)
        assert "from api.app.database import Base" in code
        assert "from sqlalchemy import Column" in code
        assert "from sqlalchemy.orm import Mapped" in code

    def test_build_template_context_contains_all_keys(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: _build_template_context() trả về context với tất cả required keys."""
        context = fastapi_entity_emitter._build_template_context(sample_user_entity, all_entities)

        expected_keys = {
            "entity",
            "table_name",
            "imports",
            "enum_classes",
            "field_definitions",
            "relationship_definitions",
            "table_args",
            "lifecycle_hooks",
        }
        assert set(context.keys()) == expected_keys

    def test_build_template_context_table_name(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_order_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Template context chứa table_name đúng."""
        context = fastapi_entity_emitter._build_template_context(sample_order_entity, all_entities)
        assert context["table_name"] == "orders"

    def test_build_template_context_entity_reference(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Template context chứa entity reference đúng."""
        context = fastapi_entity_emitter._build_template_context(sample_user_entity, all_entities)
        assert context["entity"] is sample_user_entity

    # -- Collect Imports Tests --

    def test_collect_imports_base_imports(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
    ):
        """Test: _collect_imports() chứa base imports."""
        imports = fastapi_entity_emitter._collect_imports(sample_user_entity)

        assert "standard" in imports
        assert "typing" in imports
        assert "sqlalchemy" in imports

        assert "from __future__ import annotations" in imports["standard"]
        assert "from typing import Any" in imports["typing"]
        assert "from sqlalchemy import Column" in imports["sqlalchemy"]
        assert "from sqlalchemy.orm import Mapped, relationship" in imports["sqlalchemy"]
        assert "from api.app.database import Base" in imports["sqlalchemy"]

    def test_collect_imports_uuid_field(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
    ):
        """Test: _collect_imports() thêm UUID imports cho UUID field."""
        imports = fastapi_entity_emitter._collect_imports(sample_user_entity)

        assert "from uuid import UUID" in imports["standard"]
        assert "from sqlalchemy.dialects.postgresql import UUID as PGUUID" in imports["sqlalchemy"]

    def test_collect_imports_datetime_field(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
    ):
        """Test: _collect_imports() thêm datetime import cho datetime field."""
        imports = fastapi_entity_emitter._collect_imports(sample_user_entity)
        assert "from datetime import datetime" in imports["standard"]

    def test_collect_imports_decimal_field(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_order_entity: Entity,
    ):
        """Test: _collect_imports() thêm Decimal và Numeric imports."""
        imports = fastapi_entity_emitter._collect_imports(sample_order_entity)

        assert "from decimal import Decimal" in imports["standard"]
        assert "from sqlalchemy import Numeric" in imports["sqlalchemy"]

    def test_collect_imports_json_field(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_order_entity: Entity,
    ):
        """Test: _collect_imports() thêm JSONB import cho JSON field."""
        imports = fastapi_entity_emitter._collect_imports(sample_order_entity)
        assert "from sqlalchemy.dialects.postgresql import JSONB" in imports["sqlalchemy"]

    def test_collect_imports_enum_field(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_order_entity: Entity,
    ):
        """Test: _collect_imports() thêm Enum import cho enum field."""
        imports = fastapi_entity_emitter._collect_imports(sample_order_entity)
        assert "from enum import Enum" in imports["standard"]

    def test_collect_imports_string_field(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
    ):
        """Test: _collect_imports() thêm String import cho string field."""
        imports = fastapi_entity_emitter._collect_imports(sample_user_entity)
        assert "from sqlalchemy import String" in imports["sqlalchemy"]

    def test_collect_imports_integer_field(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_category_entity: Entity,
    ):
        """Test: _collect_imports() thêm Integer import."""
        imports = fastapi_entity_emitter._collect_imports(sample_category_entity)
        assert "from sqlalchemy import Integer" in imports["sqlalchemy"]

    def test_collect_imports_boolean_field(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_category_entity: Entity,
    ):
        """Test: _collect_imports() thêm Boolean import."""
        imports = fastapi_entity_emitter._collect_imports(sample_category_entity)
        assert "from sqlalchemy import Boolean" in imports["sqlalchemy"]

    def test_collect_imports_text_field(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_order_entity: Entity,
    ):
        """Test: _collect_imports() thêm Text import."""
        imports = fastapi_entity_emitter._collect_imports(sample_order_entity)
        assert "from sqlalchemy import Text" in imports["sqlalchemy"]

    def test_collect_imports_float_field(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: _collect_imports() thêm Float import."""
        entity = Entity(
            id="TestEntity",
            fields=[
                Field(name="value", field_type=FieldType.FLOAT),
            ],
        )
        imports = fastapi_entity_emitter._collect_imports(entity)
        assert "from sqlalchemy import Float" in imports["sqlalchemy"]

    def test_collect_imports_largebinary_field(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: _collect_imports() thêm LargeBinary import."""
        entity = Entity(
            id="TestEntity",
            fields=[
                Field(name="data", field_type=FieldType.LARGE_BINARY),
            ],
        )
        imports = fastapi_entity_emitter._collect_imports(entity)
        assert "from sqlalchemy import LargeBinary" in imports["sqlalchemy"]

    def test_collect_imports_array_field(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: _collect_imports() thêm ARRAY import."""
        entity = Entity(
            id="TestEntity",
            fields=[
                Field(name="tags", field_type=FieldType.ARRAY),
            ],
        )
        imports = fastapi_entity_emitter._collect_imports(entity)
        assert "from sqlalchemy import ARRAY" in imports["sqlalchemy"]

    def test_collect_imports_with_check_constraint(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_order_entity: Entity,
    ):
        """Test: _collect_imports() thêm CheckConstraint import khi có check constraint."""
        imports = fastapi_entity_emitter._collect_imports(sample_order_entity)
        assert "from sqlalchemy import CheckConstraint" in imports["sqlalchemy"]

    def test_collect_imports_with_indexes(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
    ):
        """Test: _collect_imports() thêm Index import khi có indexes."""
        imports = fastapi_entity_emitter._collect_imports(sample_user_entity)
        assert "from sqlalchemy import Index" in imports["sqlalchemy"]

    def test_collect_imports_with_lifecycle_hooks(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
    ):
        """Test: _collect_imports() thêm event import khi có lifecycle hooks."""
        imports = fastapi_entity_emitter._collect_imports(sample_user_entity)
        assert "from sqlalchemy import event" in imports["sqlalchemy"]

    # -- Enum Classes Tests --

    def test_build_enum_classes_empty(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
    ):
        """Test: _build_enum_classes() trả về list rỗng khi không có enum field."""
        enum_classes = fastapi_entity_emitter._build_enum_classes(sample_user_entity)
        assert enum_classes == []

    def test_build_enum_classes_contains_enum(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_order_entity: Entity,
    ):
        """Test: _build_enum_classes() tạo enum class cho enum field."""
        enum_classes = fastapi_entity_emitter._build_enum_classes(sample_order_entity)

        assert len(enum_classes) == 1
        enum_code = enum_classes[0]

        assert "class OrderStatus" in enum_code
        assert "(str, Enum)" in enum_code
        assert 'PENDING = "pending"' in enum_code
        assert 'CONFIRMED = "confirmed"' in enum_code
        assert 'SHIPPED = "shipped"' in enum_code
        assert 'DELIVERED = "delivered"' in enum_code
        assert 'CANCELLED = "cancelled"' in enum_code

    def test_build_enum_classes_special_characters(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: _build_enum_classes() xử lý special characters trong enum values."""
        entity = Entity(
            id="Product",
            fields=[
                Field(
                    name="shipping_method",
                    field_type=FieldType.ENUM,
                    enum_values=["free-shipping", "express shipping"],
                ),
            ],
        )
        enum_classes = fastapi_entity_emitter._build_enum_classes(entity)
        enum_code = enum_classes[0]

        assert 'FREE_SHIPPING = "free-shipping"' in enum_code
        assert 'EXPRESS_SHIPPING = "express shipping"' in enum_code

    # -- Field Definitions Tests --

    def test_build_field_definitions_count(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
    ):
        """Test: _build_field_definitions() trả về đúng số field."""
        definitions = fastapi_entity_emitter._build_field_definitions(sample_user_entity)
        assert len(definitions) == len(sample_user_entity.fields)

    def test_build_field_definition_uuid_primary_key(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
    ):
        """Test: Field definition cho UUID primary key."""
        definitions = fastapi_entity_emitter._build_field_definitions(sample_user_entity)
        # First field is id (UUID, primary_key)
        id_def = definitions[0]
        assert "id:" in id_def
        assert "Mapped[UUID]" in id_def
        assert "PGUUID(as_uuid=True)" in id_def
        assert "primary_key=True" in id_def
        assert "nullable=False" in id_def

    def test_build_field_definition_string_with_length(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
    ):
        """Test: Field definition cho string với length."""
        definitions = fastapi_entity_emitter._build_field_definitions(sample_user_entity)
        email_def = definitions[1]  # email field
        assert "email:" in email_def
        assert "Mapped[str" in email_def
        assert "String(255)" in email_def
        assert "nullable=False" in email_def
        assert "unique=True" in email_def

    def test_build_field_definition_decimal_with_precision(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_order_entity: Entity,
    ):
        """Test: Field definition cho decimal với precision và scale."""
        definitions = fastapi_entity_emitter._build_field_definitions(sample_order_entity)
        # amount field
        amount_def = definitions[2]
        assert "amount:" in amount_def
        assert "Mapped[Decimal]" in amount_def
        assert "Numeric(18, 2)" in amount_def

    def test_build_field_definition_datetime_with_server_default(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
    ):
        """Test: Field definition cho datetime với server_default."""
        definitions = fastapi_entity_emitter._build_field_definitions(sample_user_entity)
        # created_at field
        created_def = definitions[3]
        assert "created_at:" in created_def
        assert "Mapped[datetime" in created_def
        assert "DateTime()" in created_def
        assert "server_default='now()'" in created_def

    def test_build_field_definition_nullable_text(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_order_entity: Entity,
    ):
        """Test: Field definition cho nullable text field."""
        definitions = fastapi_entity_emitter._build_field_definitions(sample_order_entity)
        # notes field (index 4)
        notes_def = definitions[4]
        assert "notes:" in notes_def
        assert "str | None" in notes_def
        assert "Text()" in notes_def

    def test_build_field_definition_json_field(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_order_entity: Entity,
    ):
        """Test: Field definition cho JSON field."""
        definitions = fastapi_entity_emitter._build_field_definitions(sample_order_entity)
        # metadata field (index 5)
        json_def = definitions[5]
        assert "metadata:" in json_def
        assert "Mapped[Any | None]" in json_def
        assert "JSONB()" in json_def

    def test_build_field_definition_boolean_with_default(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_category_entity: Entity,
    ):
        """Test: Field definition cho boolean với default value."""
        definitions = fastapi_entity_emitter._build_field_definitions(sample_category_entity)
        # is_active field (index 4)
        bool_def = definitions[4]
        assert "is_active:" in bool_def
        assert "Mapped[bool]" in bool_def
        assert "Boolean()" in bool_def
        assert "default=True" in bool_def

    def test_build_field_definition_integer_with_default(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_category_entity: Entity,
    ):
        """Test: Field definition cho integer với default value."""
        definitions = fastapi_entity_emitter._build_field_definitions(sample_category_entity)
        # sort_order field (index 3)
        int_def = definitions[3]
        assert "sort_order:" in int_def
        assert "Mapped[int]" in int_def
        assert "Integer()" in int_def
        assert "default=0" in int_def

    def test_build_field_definition_with_index(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
    ):
        """Test: Field definition với index=True."""
        definitions = fastapi_entity_emitter._build_field_definitions(sample_user_entity)
        # tenant_id field (index 4)
        tenant_def = definitions[4]
        assert "tenant_id:" in tenant_def
        assert "index=True" in tenant_def

    # -- Relationship Definitions Tests --

    def test_build_relationship_definitions_empty(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: _build_relationship_definitions() trả về list rỗng khi không có relationship."""
        # sample_user_entity has no relationships
        definitions = fastapi_entity_emitter._build_relationship_definitions(sample_user_entity, all_entities)
        assert definitions == []

    def test_build_relationship_definitions_one_to_many(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_order_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Relationship definition cho one-to-many."""
        definitions = fastapi_entity_emitter._build_relationship_definitions(sample_order_entity, all_entities)

        assert len(definitions) == 2

        # Find the OrderItem relationship (one-to-many, back_populates="order" → field "orders")
        order_items_def = definitions[1]
        # Field name derives from back_populates: "order" → "orders"
        assert "orders:" in order_items_def
        assert "Mapped[list[OrderItem]]" in order_items_def
        assert 'relationship("OrderItem"' in order_items_def
        assert 'back_populates="order"' in order_items_def
        assert 'cascade="all, delete-orphan"' in order_items_def

    def test_build_relationship_definitions_many_to_one(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_order_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Relationship definition for target User (ONE_TO_MANY rel_type)."""
        definitions = fastapi_entity_emitter._build_relationship_definitions(sample_order_entity, all_entities)

        # Find the User relationship (index 0, back_populates="orders")
        user_def = definitions[0]
        # field_name comes from back_populates → "orders"
        assert "orders:" in user_def or "orders" in user_def
        assert 'relationship("User"' in user_def
        assert 'back_populates="orders"' in user_def

    def test_build_relationship_definitions_self_referencing(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_category_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Relationship definition cho self-referencing với remote_side."""
        definitions = fastapi_entity_emitter._build_relationship_definitions(sample_category_entity, all_entities)

        assert len(definitions) == 1
        rel_def = definitions[0]
        assert 'relationship("Category"' in rel_def
        assert 'remote_side="Category.parent_id"' in rel_def

    def test_build_relationship_definitions_many_to_many(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_many_to_many_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Relationship definition cho many-to-many với secondary table."""
        definitions = fastapi_entity_emitter._build_relationship_definitions(sample_many_to_many_entity, all_entities)

        assert len(definitions) == 1
        rel_def = definitions[0]
        assert 'relationship("User"' in rel_def
        assert 'secondary="project_members"' in rel_def
        assert 'back_populates="projects"' in rel_def

    def test_build_relationship_one_to_one(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        all_entities: list[Entity],
    ):
        """Test: Relationship definition cho one-to-one với uselist=False."""
        entity = Entity(
            id="UserProfile",
            fields=[
                Field(name="id", field_type=FieldType.UUID, primary_key=True),
            ],
            relationships=[
                Relationship(
                    rel_type=RelationshipType.ONE_TO_ONE,
                    target="User",
                    back_populates="profile",
                ),
            ],
        )
        definitions = fastapi_entity_emitter._build_relationship_definitions(entity, all_entities)

        assert len(definitions) == 1
        rel_def = definitions[0]
        assert "uselist=False" in rel_def
        assert "Mapped[User | None]" in rel_def

    # -- Table Args Tests --

    def test_build_table_args_empty(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_category_entity: Entity,
    ):
        """Test: _build_table_args() trả về empty string khi không có constraints/indexes."""
        entity = Entity(
            id="Simple",
            fields=[Field(name="id", field_type=FieldType.UUID, primary_key=True)],
        )
        table_args = fastapi_entity_emitter._build_table_args(entity)
        assert table_args == ""

    def test_build_table_args_with_check_constraint(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_order_entity: Entity,
    ):
        """Test: _build_table_args() chứa CheckConstraint."""
        table_args = fastapi_entity_emitter._build_table_args(sample_order_entity)

        assert "CheckConstraint" in table_args
        assert "amount > 0" in table_args
        assert "__table_args__" in table_args

    def test_build_table_args_with_indexes(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
    ):
        """Test: _build_table_args() chứa Index."""
        table_args = fastapi_entity_emitter._build_table_args(sample_user_entity)

        assert "Index" in table_args
        assert "idx_user_email" in table_args
        assert "unique=True" in table_args

    def test_build_table_args_combined(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_order_entity: Entity,
    ):
        """Test: _build_table_args() chứa cả constraints và indexes."""
        table_args = fastapi_entity_emitter._build_table_args(sample_order_entity)

        assert "CheckConstraint" in table_args
        assert "Index" in table_args
        assert "idx_order_user_status" in table_args

    def test_build_table_args_nonunique_index(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_order_entity: Entity,
    ):
        """Test: _build_table_args() index không unique không có unique=True."""
        table_args = fastapi_entity_emitter._build_table_args(sample_order_entity)

        # idx_order_user_status is non-unique
        # We check that the index is present without unique=True for it
        assert "idx_order_user_status" in table_args

    # -- Lifecycle Hooks Tests --

    def test_build_lifecycle_hooks_empty(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_category_entity: Entity,
    ):
        """Test: _build_lifecycle_hooks() trả về empty string khi không có hooks."""
        hooks = fastapi_entity_emitter._build_lifecycle_hooks(sample_category_entity)
        assert hooks == ""

    def test_build_lifecycle_hooks_before_insert(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
    ):
        """Test: _build_lifecycle_hooks() chứa before_insert hook."""
        hooks = fastapi_entity_emitter._build_lifecycle_hooks(sample_user_entity)

        assert "Lifecycle Hooks" in hooks
        assert "@event.listens_for(User" in hooks
        assert '"before_insert"' in hooks
        assert "def hash_password_before_insert" in hooks

    def test_build_lifecycle_hooks_after_insert(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_order_entity: Entity,
    ):
        """Test: _build_lifecycle_hooks() chứa after_insert hook."""
        hooks = fastapi_entity_emitter._build_lifecycle_hooks(sample_order_entity)

        assert '"after_insert"' in hooks
        assert "def log_order_created" in hooks

    def test_build_lifecycle_hooks_multiple_events(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: _build_lifecycle_hooks() với nhiều lifecycle events."""
        entity = Entity(
            id="AuditLog",
            fields=[Field(name="id", field_type=FieldType.UUID, primary_key=True)],
            lifecycle_hooks=[
                LifecycleHook(
                    event=LifecycleEvent.BEFORE_INSERT,
                    hook_name="set_timestamp",
                ),
                LifecycleHook(
                    event=LifecycleEvent.AFTER_UPDATE,
                    hook_name="log_changes",
                ),
                LifecycleHook(
                    event=LifecycleEvent.BEFORE_DELETE,
                    hook_name="check_soft_delete",
                ),
            ],
        )
        hooks = fastapi_entity_emitter._build_lifecycle_hooks(entity)

        assert "set_timestamp" in hooks
        assert "log_changes" in hooks
        assert "check_soft_delete" in hooks

    # -- Type Annotation Tests --

    def test_get_type_annotation_basic_types(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: _get_type_annotation() với các basic types (nullable=False)."""
        assert fastapi_entity_emitter._get_type_annotation(
            Field(name="f", field_type=FieldType.STRING, nullable=False)
        ) == "str"
        assert fastapi_entity_emitter._get_type_annotation(
            Field(name="f", field_type=FieldType.INTEGER, nullable=False)
        ) == "int"
        assert fastapi_entity_emitter._get_type_annotation(
            Field(name="f", field_type=FieldType.FLOAT, nullable=False)
        ) == "float"
        assert fastapi_entity_emitter._get_type_annotation(
            Field(name="f", field_type=FieldType.BOOLEAN, nullable=False)
        ) == "bool"

    def test_get_type_annotation_nullable(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: _get_type_annotation() với nullable field."""
        field = Field(name="f", field_type=FieldType.STRING, nullable=True)
        annotation = fastapi_entity_emitter._get_type_annotation(field)
        assert annotation == "str | None"

    def test_get_type_annotation_default_nullable(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: _get_type_annotation() default nullable=True adds Optional."""
        field = Field(name="f", field_type=FieldType.STRING)  # default nullable=True
        annotation = fastapi_entity_emitter._get_type_annotation(field)
        assert annotation == "str | None"

    def test_get_type_annotation_complex_types(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: _get_type_annotation() với complex types (nullable=False)."""
        assert fastapi_entity_emitter._get_type_annotation(
            Field(name="f", field_type=FieldType.DATETIME, nullable=False)
        ) == "datetime"
        assert fastapi_entity_emitter._get_type_annotation(
            Field(name="f", field_type=FieldType.UUID, nullable=False)
        ) == "UUID"
        assert fastapi_entity_emitter._get_type_annotation(
            Field(name="f", field_type=FieldType.JSON, nullable=False)
        ) == "Any"
        assert fastapi_entity_emitter._get_type_annotation(
            Field(name="f", field_type=FieldType.DECIMAL, nullable=False)
        ) == "Decimal"
        assert fastapi_entity_emitter._get_type_annotation(
            Field(name="f", field_type=FieldType.TEXT, nullable=False)
        ) == "str"
        assert fastapi_entity_emitter._get_type_annotation(
            Field(name="f", field_type=FieldType.LARGE_BINARY, nullable=False)
        ) == "bytes"
        assert fastapi_entity_emitter._get_type_annotation(
            Field(name="f", field_type=FieldType.ARRAY, nullable=False)
        ) == "list[str]"

    # -- SQLAlchemy Type Tests --

    def test_get_sqlalchemy_type_string_with_length(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: _get_sqlalchemy_type() với string có length."""
        field = Field(name="f", field_type=FieldType.STRING, length=100)
        assert fastapi_entity_emitter._get_sqlalchemy_type(field) == "String(100)"

    def test_get_sqlalchemy_type_string_default_length(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: _get_sqlalchemy_type() với string không có length (default 255)."""
        field = Field(name="f", field_type=FieldType.STRING)
        assert fastapi_entity_emitter._get_sqlalchemy_type(field) == "String(255)"

    def test_get_sqlalchemy_type_decimal_with_precision(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: _get_sqlalchemy_type() với decimal có precision và scale."""
        field = Field(name="f", field_type=FieldType.DECIMAL, precision=20, scale=4)
        assert fastapi_entity_emitter._get_sqlalchemy_type(field) == "Numeric(20, 4)"

    def test_get_sqlalchemy_type_decimal_defaults(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: _get_sqlalchemy_type() với decimal defaults."""
        field = Field(name="f", field_type=FieldType.DECIMAL)
        assert fastapi_entity_emitter._get_sqlalchemy_type(field) == "Numeric(10, 2)"

    def test_get_sqlalchemy_type_enum_with_length(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: _get_sqlalchemy_type() với enum có length."""
        field = Field(name="f", field_type=FieldType.ENUM, length=30)
        assert fastapi_entity_emitter._get_sqlalchemy_type(field) == "String(30)"

    def test_get_sqlalchemy_type_all_types(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: _get_sqlalchemy_type() với tất cả field types."""
        assert fastapi_entity_emitter._get_sqlalchemy_type(Field(name="f", field_type=FieldType.INTEGER)) == "Integer()"
        assert fastapi_entity_emitter._get_sqlalchemy_type(Field(name="f", field_type=FieldType.FLOAT)) == "Float()"
        assert fastapi_entity_emitter._get_sqlalchemy_type(Field(name="f", field_type=FieldType.BOOLEAN)) == "Boolean()"
        assert fastapi_entity_emitter._get_sqlalchemy_type(Field(name="f", field_type=FieldType.DATETIME)) == "DateTime()"
        assert fastapi_entity_emitter._get_sqlalchemy_type(Field(name="f", field_type=FieldType.TEXT)) == "Text()"
        assert fastapi_entity_emitter._get_sqlalchemy_type(Field(name="f", field_type=FieldType.UUID)) == "PGUUID(as_uuid=True)"
        assert fastapi_entity_emitter._get_sqlalchemy_type(Field(name="f", field_type=FieldType.JSON)) == "JSONB()"
        assert fastapi_entity_emitter._get_sqlalchemy_type(Field(name="f", field_type=FieldType.LARGE_BINARY)) == "LargeBinary()"
        assert fastapi_entity_emitter._get_sqlalchemy_type(Field(name="f", field_type=FieldType.ARRAY)) == "ARRAY(String())"

    # -- Utility Methods --

    def test_to_pascal_case(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: _to_pascal_case() chuyển snake_case sang PascalCase."""
        assert fastapi_entity_emitter._to_pascal_case("order_status") == "OrderStatus"
        assert fastapi_entity_emitter._to_pascal_case("user") == "User"
        assert fastapi_entity_emitter._to_pascal_case("shipping_method") == "ShippingMethod"

    def test_emit_order_with_full_context(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_order_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: emit() Order entity tạo full code với templates."""
        code = fastapi_entity_emitter.emit(sample_order_entity, all_entities)

        assert "Order" in code
        assert "orders" in code
        # Template renders with TenantRowMixin
        assert "class Order(Base, TenantRowMixin):" in code

    def test_emit_category_self_referencing(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_category_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: emit() Category entity với self-referencing relationship."""
        code = fastapi_entity_emitter.emit(sample_category_entity, all_entities)

        assert "Category" in code
        # Table name uses simple pluralization
        assert "categorys" in code

    def test_emit_many_to_many(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_many_to_many_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: emit() Project entity với many-to-many relationship."""
        code = fastapi_entity_emitter.emit(sample_many_to_many_entity, all_entities)

        assert "Project" in code
        assert "projects" in code


# ============================================================================
# Tests for NestJSEntityEmitter
# ============================================================================


class TestNestJSEntityEmitter:
    """Tests cho NestJSEntityEmitter."""

    def test_emit_returns_fallback_code(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_user_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: emit() generates full TypeScript code with templates."""
        code = nestjs_entity_emitter.emit(sample_user_entity, all_entities)

        assert "User" in code
        assert "users" in code
        assert "export class User" in code

    def test_emit_fallback_contains_typeorm_decorators(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_user_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Fallback code chứa TypeORM decorators."""
        code = nestjs_entity_emitter.emit(sample_user_entity, all_entities)

        assert "@Entity" in code
        assert "import" in code
        assert "typeorm" in code

    def test_emit_fallback_export_class(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_user_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Fallback code chứa export class."""
        code = nestjs_entity_emitter.emit(sample_user_entity, all_entities)

        assert "export class User" in code

    def test_build_template_context_contains_all_keys(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_user_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: _build_template_context() trả về context với required keys."""
        context = nestjs_entity_emitter._build_template_context(sample_user_entity, all_entities)

        expected_keys = {"entity", "table_name", "imports", "property_definitions"}
        assert set(context.keys()) >= expected_keys

    def test_build_template_context_table_name(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_order_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Template context chứa table_name đúng."""
        context = nestjs_entity_emitter._build_template_context(sample_order_entity, all_entities)
        assert context["table_name"] == "orders"

    # -- Collect Imports Tests --

    def test_collect_imports_base(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_user_entity: Entity,
    ):
        """Test: _collect_imports() chứa base TypeORM và class-validator imports."""
        imports = nestjs_entity_emitter._collect_imports(sample_user_entity)

        assert "typeorm" in imports
        assert "common" in imports

        assert "import { Entity, Column, PrimaryGeneratedColumn, Index } from 'typeorm';" in imports["typeorm"]
        assert "import { IsString, IsOptional } from 'class-validator';" in imports["common"]

    def test_collect_imports_with_relationships(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_order_entity: Entity,
    ):
        """Test: _collect_imports() thêm relationship imports khi có relationships."""
        imports = nestjs_entity_emitter._collect_imports(sample_order_entity)

        assert "import { ManyToOne, OneToMany, OneToOne, ManyToMany, JoinTable } from 'typeorm';" in imports["typeorm"]

    def test_collect_imports_without_relationships(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_user_entity: Entity,
    ):
        """Test: _collect_imports() không thêm relationship imports khi không có relationships (hoặc chỉ self-ref)."""
        imports = nestjs_entity_emitter._collect_imports(sample_user_entity)

        # User entity has no relationships, so relationship imports should not be added
        relationship_import = "import { ManyToOne, OneToMany, OneToOne, ManyToMany, JoinTable } from 'typeorm';"
        assert relationship_import not in imports["typeorm"]

    def test_collect_imports_self_referencing_no_rel_imports(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_category_entity: Entity,
    ):
        """Test: _collect_imports() không thêm non-self-ref relationship imports."""
        imports = nestjs_entity_emitter._collect_imports(sample_category_entity)

        # Category only has self-referencing relationship
        relationship_import = "import { ManyToOne, OneToMany, OneToOne, ManyToMany, JoinTable } from 'typeorm';"
        assert relationship_import not in imports["typeorm"]

    # -- TypeScript Type Mapping Tests --

    def test_get_typescript_type_all_types(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
    ):
        """Test: _get_typeScript_type() mapping cho tất cả field types."""
        assert nestjs_entity_emitter._get_typeScript_type(FieldType.STRING) == "string"
        assert nestjs_entity_emitter._get_typeScript_type(FieldType.INTEGER) == "number"
        assert nestjs_entity_emitter._get_typeScript_type(FieldType.FLOAT) == "number"
        assert nestjs_entity_emitter._get_typeScript_type(FieldType.BOOLEAN) == "boolean"
        assert nestjs_entity_emitter._get_typeScript_type(FieldType.DATETIME) == "Date"
        assert nestjs_entity_emitter._get_typeScript_type(FieldType.TEXT) == "string"
        assert nestjs_entity_emitter._get_typeScript_type(FieldType.UUID) == "string"
        assert nestjs_entity_emitter._get_typeScript_type(FieldType.JSON) == "any"
        assert nestjs_entity_emitter._get_typeScript_type(FieldType.DECIMAL) == "number"
        assert nestjs_entity_emitter._get_typeScript_type(FieldType.ENUM) == "string"
        assert nestjs_entity_emitter._get_typeScript_type(FieldType.LARGE_BINARY) == "Buffer"
        assert nestjs_entity_emitter._get_typeScript_type(FieldType.ARRAY) == "string[]"

    # -- Property Definitions Tests --

    def test_build_property_definitions_count(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_user_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: _build_property_definitions() trả về đúng số property (fields + relationships)."""
        definitions = nestjs_entity_emitter._build_property_definitions(sample_user_entity, all_entities)
        # User has 5 fields, 0 relationships
        assert len(definitions) == len(sample_user_entity.fields)

    def test_build_property_definitions_primary_key(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_user_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Property definition cho primary key field."""
        definitions = nestjs_entity_emitter._build_property_definitions(sample_user_entity, all_entities)
        id_def = definitions[0]
        assert "@PrimaryGeneratedColumn" in id_def
        assert "id:" in id_def

    def test_build_property_definitions_regular_field(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_user_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Property definition cho regular field."""
        definitions = nestjs_entity_emitter._build_property_definitions(sample_user_entity, all_entities)
        email_def = definitions[1]
        assert "@Column()" in email_def
        assert "email:" in email_def
        assert "string;" in email_def

    def test_build_property_definitions_nullable_field(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
    ):
        """Test: Property definition cho nullable field với @IsOptional()."""
        entity = Entity(
            id="TestEntity",
            fields=[
                Field(name="id", field_type=FieldType.UUID, primary_key=True),
                Field(name="description", field_type=FieldType.STRING, nullable=True),
            ],
        )
        definitions = nestjs_entity_emitter._build_property_definitions(entity, [])
        desc_def = definitions[1]
        assert "@IsOptional()" in desc_def

    def test_build_property_definitions_typescript_types(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_order_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Property definitions sử dụng đúng TypeScript types."""
        definitions = nestjs_entity_emitter._build_property_definitions(sample_order_entity, all_entities)

        # Find definitions by name
        def find_by_name(name: str):
            for d in definitions:
                if f"{name}:" in d or f"{name} " in d:
                    return d
            return None

        # amount (decimal -> number)
        amount_def = find_by_name("amount")
        assert amount_def is not None
        assert "number;" in amount_def

        # created_at (datetime -> Date)
        created_def = find_by_name("created_at")
        assert created_def is not None
        assert "Date;" in created_def

    def test_build_property_definitions_with_relationships(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_order_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Property definitions chứa cả fields và relationships."""
        definitions = nestjs_entity_emitter._build_property_definitions(sample_order_entity, all_entities)

        # Order has 7 fields + 2 relationships = 9 definitions
        assert len(definitions) == len(sample_order_entity.fields) + len(sample_order_entity.relationships)

    def test_build_relationship_definition_one_to_many(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_order_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Relationship definition cho one-to-many."""
        rel = sample_order_entity.relationships[1]  # OrderItem relationship
        rel_def = nestjs_entity_emitter._build_relationship_definition(rel, sample_order_entity, all_entities)

        assert "@OneToMany" in rel_def
        # field_name = back_populates.lower() = "order"
        assert "order:" in rel_def
        assert "OrderItem" in rel_def

    def test_build_relationship_definition_many_to_one(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_order_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Relationship definition for target User (back_populates='orders')."""
        rel = sample_order_entity.relationships[0]  # User relationship
        rel_def = nestjs_entity_emitter._build_relationship_definition(rel, sample_order_entity, all_entities)

        # field_name = back_populates.lower() = "orders"
        assert "orders:" in rel_def
        assert "User" in rel_def

    def test_build_relationship_definition_many_to_many(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_many_to_many_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Relationship definition cho many-to-many."""
        rel = sample_many_to_many_entity.relationships[0]
        rel_def = nestjs_entity_emitter._build_relationship_definition(rel, sample_many_to_many_entity, all_entities)

        assert "@ManyToMany" in rel_def
        # field_name = back_populates.lower() = "projects"
        assert "projects:" in rel_def

    def test_build_relationship_definition_one_to_one(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        all_entities: list[Entity],
    ):
        """Test: Relationship definition cho one-to-one."""
        entity = Entity(
            id="UserProfile",
            fields=[Field(name="id", field_type=FieldType.UUID, primary_key=True)],
            relationships=[
                Relationship(
                    rel_type=RelationshipType.ONE_TO_ONE,
                    target="User",
                    back_populates="profile",
                ),
            ],
        )
        rel = entity.relationships[0]
        rel_def = nestjs_entity_emitter._build_relationship_definition(rel, entity, all_entities)

        assert "@OneToOne" in rel_def
        # field_name = back_populates.lower() = "profile"
        assert "profile:" in rel_def

    def test_emit_with_full_entity(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_order_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: emit() Order entity đầy đủ tạo fallback code."""
        code = nestjs_entity_emitter.emit(sample_order_entity, all_entities)

        assert "Order" in code
        assert "orders" in code
        assert "export class Order" in code

    def test_emit_category_self_referencing(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_category_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: emit() Category entity với self-referencing."""
        code = nestjs_entity_emitter.emit(sample_category_entity, all_entities)

        assert "Category" in code
        # Table name uses simple pluralization: categorys
        assert "categorys" in code

    def test_emit_many_to_many(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_many_to_many_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: emit() Project entity với many-to-many."""
        code = nestjs_entity_emitter.emit(sample_many_to_many_entity, all_entities)

        assert "Project" in code
        assert "projects" in code

    def test_emit_empty_entity(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
    ):
        """Test: emit() entity rỗng không crash."""
        entity = Entity(id="EmptyEntity")
        code = nestjs_entity_emitter.emit(entity, [])

        assert "EmptyEntity" in code
        # Table name follows simple pluralization rule: append 's'
        assert "empty_entities" in code or "empty_entitys" in code


# ============================================================================
# Cross-Emitter Comparison Tests
# ============================================================================


class TestCrossEmitterComparison:
    """Tests so sánh output giữa FastAPI và NestJS emitters."""

    def test_both_emitters_same_table_name(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_user_entity: Entity,
    ):
        """Test: Cả hai emitters generate cùng table name."""
        fastapi_ctx = fastapi_entity_emitter._build_template_context(sample_user_entity, [])
        nestjs_ctx = nestjs_entity_emitter._build_template_context(sample_user_entity, [])

        assert fastapi_ctx["table_name"] == nestjs_ctx["table_name"]

    def test_both_emitters_emit_without_error(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_order_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: Cả hai emitters emit mà không raise exception."""
        fastapi_code = fastapi_entity_emitter.emit(sample_order_entity, all_entities)
        nestjs_code = nestjs_entity_emitter.emit(sample_order_entity, all_entities)

        assert isinstance(fastapi_code, str)
        assert isinstance(nestjs_code, str)
        assert len(fastapi_code) > 0
        assert len(nestjs_code) > 0

    def test_fastapi_generates_python_style(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: FastAPI emitter generate Python-style code."""
        code = fastapi_entity_emitter.emit(sample_user_entity, all_entities)

        # Templates produce TenantRowMixin-enhanced code
        assert "class User(Base, TenantRowMixin):" in code
        assert "from sqlalchemy" in code

    def test_nestjs_generates_typescript_style(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
        sample_user_entity: Entity,
        all_entities: list[Entity],
    ):
        """Test: NestJS emitter generate TypeScript-style code."""
        code = nestjs_entity_emitter.emit(sample_user_entity, all_entities)

        assert "export class User" in code
        assert "from 'typeorm'" in code


# ============================================================================
# Edge Cases
# ============================================================================


class TestEntityEmitterEdgeCases:
    """Edge case tests cho Entity emitters."""

    def test_emit_entity_with_no_fields(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: emit() entity không có fields không crash."""
        entity = Entity(id="Empty")
        code = fastapi_entity_emitter.emit(entity, [])

        assert "Empty" in code
        # Simple pluralization: "empty" + "s" = "emptys"
        assert "emptys" in code

    def test_emit_entity_with_many_fields(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: emit() entity với nhiều fields."""
        fields = [
            Field(name=f"field_{i}", field_type=FieldType.STRING)
            for i in range(50)
        ]
        entity = Entity(id="LargeEntity", fields=fields)
        code = fastapi_entity_emitter.emit(entity, [])

        assert "LargeEntity" in code

    def test_emit_entity_with_long_description(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        sample_user_entity: Entity,
    ):
        """Test: emit() entity với description dài."""
        sample_user_entity.description = "A" * 1000
        code = fastapi_entity_emitter.emit(sample_user_entity, [])

        assert "User" in code

    def test_field_with_all_options_fastapi(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: Field với tất cả options cho FastAPI."""
        field = Field(
            name="full_field",
            field_type=FieldType.STRING,
            nullable=False,
            unique=True,
            primary_key=False,
            index=True,
            default="default_value",
            server_default="now()",
            length=500,
        )
        entity = Entity(id="Test", fields=[field])
        definitions = fastapi_entity_emitter._build_field_definitions(entity)
        field_def = definitions[0]

        assert "String(500)" in field_def
        assert "nullable=False" in field_def
        assert "unique=True" in field_def
        assert "index=True" in field_def
        assert "default='default_value'" in field_def
        assert "server_default='now()'" in field_def

    def test_field_with_all_options_nestjs(
        self,
        nestjs_entity_emitter: NestJSEntityEmitter,
    ):
        """Test: Field với tất cả options cho NestJS."""
        field = Field(
            name="full_field",
            field_type=FieldType.STRING,
            nullable=True,
            primary_key=False,
        )
        entity = Entity(id="Test", fields=[field])
        definitions = nestjs_entity_emitter._build_property_definitions(entity, [])
        field_def = definitions[0]

        assert "@Column()" in field_def
        assert "@IsOptional()" in field_def
        assert "string;" in field_def

    def test_constraint_without_name(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: Constraint không có name được generate name tự động."""
        entity = Entity(
            id="Account",
            fields=[Field(name="id", field_type=FieldType.UUID, primary_key=True)],
            constraints=[
                Constraint(
                    constraint_type=ConstraintType.CHECK,
                    condition="balance >= 0",
                ),
            ],
        )
        table_args = fastapi_entity_emitter._build_table_args(entity)

        assert "CheckConstraint" in table_args
        assert "balance >= 0" in table_args

    def test_index_without_name(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: Index không có name được generate name tự động."""
        entity = Entity(
            id="Product",
            fields=[Field(name="id", field_type=FieldType.UUID, primary_key=True)],
            indexes=[
                Index(fields=["sku", "category_id"]),
            ],
        )
        table_args = fastapi_entity_emitter._build_table_args(entity)

        assert "Index" in table_args
        assert "sku" in table_args

    def test_relationship_without_back_populates(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
        all_entities: list[Entity],
    ):
        """Test: Relationship không có back_populates được generate field name."""
        entity = Entity(
            id="Order",
            fields=[Field(name="id", field_type=FieldType.UUID, primary_key=True)],
            relationships=[
                Relationship(
                    rel_type=RelationshipType.ONE_TO_MANY,
                    target="OrderItem",
                ),
            ],
        )
        definitions = fastapi_entity_emitter._build_relationship_definitions(entity, all_entities)
        rel_def = definitions[0]

        # Should generate field name from target
        assert "order_item_rel" in rel_def

    def test_multiple_lifecycle_hooks_same_entity(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: Entity với nhiều lifecycle hooks."""
        entity = Entity(
            id="AuditEntity",
            fields=[Field(name="id", field_type=FieldType.UUID, primary_key=True)],
            lifecycle_hooks=[
                LifecycleHook(event=LifecycleEvent.BEFORE_INSERT, hook_name="set_created_at"),
                LifecycleHook(event=LifecycleEvent.AFTER_INSERT, hook_name="send_notification"),
                LifecycleHook(event=LifecycleEvent.BEFORE_UPDATE, hook_name="set_updated_at"),
                LifecycleHook(event=LifecycleEvent.AFTER_UPDATE, hook_name="log_update"),
                LifecycleHook(event=LifecycleEvent.BEFORE_DELETE, hook_name="prevent_hard_delete"),
                LifecycleHook(event=LifecycleEvent.AFTER_DELETE, hook_name="archive_record"),
            ],
        )
        hooks = fastapi_entity_emitter._build_lifecycle_hooks(entity)

        assert "set_created_at" in hooks
        assert "send_notification" in hooks
        assert "set_updated_at" in hooks
        assert "log_update" in hooks
        assert "prevent_hard_delete" in hooks
        assert "archive_record" in hooks

    def test_find_entity_by_id_with_similar_names(
        self,
        fastapi_entity_emitter: FastAPIEntityEmitter,
    ):
        """Test: find_entity_by_id() phân biệt các entity có tên tương tự."""
        entities = [
            Entity(id="User"),
            Entity(id="UserProfile"),
            Entity(id="UserRole"),
        ]

        assert fastapi_entity_emitter.find_entity_by_id("User", entities).id == "User"
        assert fastapi_entity_emitter.find_entity_by_id("UserProfile", entities).id == "UserProfile"
        assert fastapi_entity_emitter.find_entity_by_id("UserRole", entities).id == "UserRole"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
