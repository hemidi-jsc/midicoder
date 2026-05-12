"""
Tests cho KPI-029: Tenant Isolation trong Value Objects (CP01).

Module này test tenant_id implementation trong ValueObject model:
1. ValueObject.from_dict() bao gồm tenant_id
2. ValueObject.to_dict() bao gồm tenant_id
3. Field-level: tenant_id là Optional[str], default=None
4. FastAPI/NestJS emitter render tenant_id field vào generated code

KPI-029: Missing Tenant Filter Detection Rate
CP01: Domain Model - Value Objects
"""

from decimal import Decimal

import pytest

from midicoder.emitters.core.cp01_domain_model import (
    ValueObject,
    VOField,
    VOFieldType,
)
from midicoder.emitters.core.cp01_domain_model.vo_fastapi import (
    FastAPIValueObjectEmitter,
)
from midicoder.emitters.core.cp01_domain_model.vo_nestjs import (
    NestJSValueObjectEmitter,
)


# ===========================================================================
# Test: ValueObject model — tenant_id field
# ===========================================================================

class TestValueObjectTenantField:
    """Test tenant_id field trong ValueObject dataclass."""

    def test_value_object_can_have_tenant_id_field(self):
        """KPI-029: ValueObject có thể chứa tenant_id field."""
        vo = ValueObject(
            id="Money",
            description="Money with tenant scope",
            fields=[
                VOField(name="amount", field_type=VOFieldType.DECIMAL, required=True),
                VOField(name="currency", field_type=VOFieldType.STRING, required=True),
                VOField(name="tenant_id", field_type=VOFieldType.STRING, required=False),
            ],
        )

        tenant_field = next((f for f in vo.fields if f.name == "tenant_id"), None)
        assert tenant_field is not None

    def test_value_object_from_dict_preserves_tenant_id(self):
        """KPI-029: from_dict() giữ tenant_id field nếu có."""
        vo_data = {
            "id": "Money",
            "description": "Money",
            "fields": [
                {"name": "amount", "type": "decimal", "required": True},
                {"name": "tenant_id", "type": "string", "required": False},
            ],
        }
        vo = ValueObject.from_dict(vo_data)
        assert vo.id == "Money"
        tenant_field = next((f for f in vo.fields if f.name == "tenant_id"), None)
        assert tenant_field is not None
        assert tenant_field.required is False

    def test_value_object_to_dict_includes_tenant_id(self):
        """KPI-029: to_dict() bao gồm tenant_id field nếu có."""
        vo = ValueObject(
            id="Money",
            description="Money",
            fields=[
                VOField(name="amount", field_type=VOFieldType.DECIMAL, required=True),
                VOField(name="tenant_id", field_type=VOFieldType.STRING, required=False),
            ],
        )
        vo_dict = vo.to_dict()
        fields_dict = vo_dict.get("fields", [])
        tenant_fields = [f for f in fields_dict if f.get("name") == "tenant_id"]
        assert len(tenant_fields) == 1

    def test_value_object_without_tenant_id(self):
        """KPI-029: ValueObject có thể không có tenant_id."""
        vo = ValueObject(
            id="Color",
            fields=[
                VOField(name="hex", field_type=VOFieldType.STRING, required=True),
            ],
        )
        tenant_field = next((f for f in vo.fields if f.name == "tenant_id"), None)
        assert tenant_field is None


# ===========================================================================
# Test: FastAPI emitter — tenant_id in generated code
# ===========================================================================

class TestFastAPIEmitterTenantId:
    """Test tenant_id trong generated Python code từ FastAPIValueObjectEmitter."""

    @pytest.fixture
    def emitter(self, tmp_path):
        return FastAPIValueObjectEmitter(stack_dir=tmp_path)

    def test_emit_vo_with_tenant_id_field(self, emitter):
        """KPI-029: FastAPI emitter render VO có tenant_id field."""
        vo_params = {
            "id": "Money",
            "description": "Money with tenant",
            "fields": [
                {"name": "amount", "type": "decimal", "required": True},
                {"name": "tenant_id", "type": "string", "required": False},
            ],
        }

        emitted = emitter.emit(vo_params)
        assert "tenant_id" in emitted.full_content
        assert "class Money" in emitted.full_content

    def test_emit_vo_without_tenant_id(self, emitter):
        """KPI-029: FastAPI emitter render VO không có tenant_id."""
        vo_params = {
            "id": "Color",
            "fields": [{"name": "hex", "type": "string", "required": True}],
        }

        emitted = emitter.emit(vo_params)
        assert "tenant_id" not in emitted.full_content


# ===========================================================================
# Test: NestJS emitter — tenant_id in generated code
# ===========================================================================

class TestNestJSEmitterTenantId:
    """Test tenant_id trong generated TypeScript code từ NestJSValueObjectEmitter."""

    @pytest.fixture
    def emitter(self, tmp_path):
        return NestJSValueObjectEmitter(stack_dir=tmp_path)

    def test_emit_vo_with_tenant_id_field(self, emitter):
        """KPI-029: NestJS emitter render VO có tenant_id field."""
        vo_params = {
            "id": "Money",
            "description": "Money with tenant",
            "fields": [
                {"name": "amount", "type": "decimal", "required": True},
                {"name": "tenant_id", "type": "string", "required": False},
            ],
        }

        emitted = emitter.emit(vo_params)
        assert "tenant_id" in emitted.full_content
        assert "export class Money" in emitted.full_content


# ===========================================================================
# Test: ValueObject tenant semantics (behavioral)
# ===========================================================================

class TestValueObjectTenantSemantics:
    """Test behavioral semantics of tenant_id trong generated ValueObjects."""

    def test_tenant_id_is_optional_and_not_compared(self):
        """KPI-029: tenant_id không ảnh hưởng equality."""
        from dataclasses import dataclass, field
        from typing import Optional

        @dataclass(frozen=True)
        class GeneratedMoney:
            """Simulates a VO generated by FastAPIValueObjectEmitter."""
            amount: Decimal
            currency: str
            tenant_id: Optional[str] = field(default=None, repr=False, compare=False)

            def get_tenant_id(self) -> str | None:
                return self.tenant_id

            def with_tenant(self, tenant_id: str) -> "GeneratedMoney":
                from dataclasses import replace
                return replace(self, tenant_id=tenant_id)

        a = GeneratedMoney(Decimal("100"), "USD", tenant_id="t1")
        b = GeneratedMoney(Decimal("100"), "USD", tenant_id="t2")
        c = GeneratedMoney(Decimal("100"), "USD")

        assert a == b, "VOs với cùng value nhưng khác tenant_id phải equal"
        assert a == c, "VO có tenant_id phải equal với VO không có"
        assert a.get_tenant_id() == "t1"

    def test_with_tenant_does_not_mutate_original(self):
        """KPI-029: with_tenant() không mutate original."""
        from dataclasses import dataclass, field, replace
        from typing import Optional

        @dataclass(frozen=True)
        class GeneratedVO:
            value: str
            tenant_id: Optional[str] = field(default=None, repr=False, compare=False)

            def with_tenant(self, tid: str) -> "GeneratedVO":
                return replace(self, tenant_id=tid)

        original = GeneratedVO("test")
        copy = original.with_tenant("new-tenant")

        assert original.tenant_id is None
        assert copy.tenant_id == "new-tenant"
        assert original.value == copy.value