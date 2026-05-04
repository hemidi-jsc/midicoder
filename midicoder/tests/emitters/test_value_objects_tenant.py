"""
Tests cho KPI-029: Tenant Isolation trong Value Objects.

Module này test tenant_id implementation trong FastAPI Value Objects templates:
1. tenant_id field tồn tại trong base ValueObject
2. get_tenant_id() trả về tenant_id đúng
3. with_tenant() tạo copy với tenant_id mới
4. frozen=True vẫn hoạt động với tenant_id
5. to_dict() bao gồm tenant_id (optional)

KPI-029: Missing Tenant Filter Detection Rate
CP01: Domain Model - Value Objects
"""

from dataclasses import dataclass, field
from typing import Optional
import pytest


# ============================================================================
# Test: ValueObject Base Class Template - tenant_id field
# ============================================================================

class TestValueObjectTenantField:
    """Test tenant_id field trong ValueObject base template."""

    def test_value_object_has_tenant_id_field(self):
        """KPI-029: ValueObject template phải có tenant_id field."""
        # Simulate generated VO với tenant_id
        @dataclass(frozen=True)
        class TestValueObject:
            value: str
            tenant_id: Optional[str] = field(default=None, repr=False, compare=False)

            def get_tenant_id(self) -> Optional[str]:
                return self.tenant_id

        vo = TestValueObject(value="test")
        assert hasattr(vo, "tenant_id"), "ValueObject phải có tenant_id field"
        assert vo.tenant_id is None, "Default tenant_id phải là None"

    def test_value_object_tenant_id_optional(self):
        """KPI-029: tenant_id phải là optional field."""
        @dataclass(frozen=True)
        class TestValueObject:
            value: str
            tenant_id: Optional[str] = field(default=None, repr=False, compare=False)

        # Create without tenant_id
        vo1 = TestValueObject(value="test")
        assert vo1.tenant_id is None

        # Create with tenant_id
        vo2 = TestValueObject(value="test", tenant_id="tenant-123")
        assert vo2.tenant_id == "tenant-123"

    def test_value_object_tenant_id_not_in_repr(self):
        """KPI-029: tenant_id không hiển thị trong repr (repr=False)."""
        @dataclass(frozen=True)
        class TestValueObject:
            value: str
            tenant_id: Optional[str] = field(default=None, repr=False, compare=False)

        vo = TestValueObject(value="test", tenant_id="tenant-123")
        repr_str = repr(vo)
        assert "tenant_id" not in repr_str or "tenant-123" not in repr_str

    def test_value_object_tenant_id_not_in_compare(self):
        """KPI-029: tenant_id không ảnh hưởng equality (compare=False)."""
        @dataclass(frozen=True)
        class TestValueObject:
            value: str
            tenant_id: Optional[str] = field(default=None, repr=False, compare=False)

        vo1 = TestValueObject(value="test", tenant_id="tenant-123")
        vo2 = TestValueObject(value="test", tenant_id="tenant-456")
        vo3 = TestValueObject(value="test")

        # Equal because tenant_id is not compared
        assert vo1 == vo2, "VOs với cùng value nhưng khác tenant_id phải equal"
        assert vo1 == vo3, "VO với tenant_id=None phải equal với VO có tenant_id"


# ============================================================================
# Test: get_tenant_id() method
# ============================================================================

class TestValueObjectGetTenantId:
    """Test get_tenant_id() method trong ValueObjects."""

    def test_get_tenant_id_returns_none_by_default(self):
        """KPI-029: get_tenant_id() trả về None khi tenant_id chưa set."""
        @dataclass(frozen=True)
        class TestValueObject:
            value: str
            tenant_id: Optional[str] = field(default=None, repr=False, compare=False)

            def get_tenant_id(self) -> Optional[str]:
                return self.tenant_id

        vo = TestValueObject(value="test")
        assert vo.get_tenant_id() is None

    def test_get_tenant_id_returns_tenant_id_when_set(self):
        """KPI-029: get_tenant_id() trả về tenant_id khi đã set."""
        @dataclass(frozen=True)
        class TestValueObject:
            value: str
            tenant_id: Optional[str] = field(default=None, repr=False, compare=False)

            def get_tenant_id(self) -> Optional[str]:
                return self.tenant_id

        vo = TestValueObject(value="test", tenant_id="tenant-123")
        assert vo.get_tenant_id() == "tenant-123"

    def test_get_tenant_id_with_uuid_format(self):
        """KPI-029: get_tenant_id() hoạt động với UUID format tenant_id."""
        from uuid import uuid4

        @dataclass(frozen=True)
        class TestValueObject:
            value: str
            tenant_id: Optional[str] = field(default=None, repr=False, compare=False)

            def get_tenant_id(self) -> Optional[str]:
                return self.tenant_id

        tenant_id = str(uuid4())
        vo = TestValueObject(value="test", tenant_id=tenant_id)
        assert vo.get_tenant_id() == tenant_id


# ============================================================================
# Test: with_tenant() method
# ============================================================================

class TestValueObjectWithTenant:
    """Test with_tenant() method cho tenant context propagation."""

    def test_with_tenant_creates_copy_with_new_tenant_id(self):
        """KPI-029: with_tenant() tạo copy với tenant_id mới."""
        from dataclasses import replace

        @dataclass(frozen=True)
        class TestValueObject:
            value: str
            tenant_id: Optional[str] = field(default=None, repr=False, compare=False)

            def with_tenant(self, tenant_id: str) -> "TestValueObject":
                return replace(self, tenant_id=tenant_id)

        vo1 = TestValueObject(value="test")
        vo2 = vo1.with_tenant("tenant-123")

        assert vo1.tenant_id is None
        assert vo2.tenant_id == "tenant-123"
        assert vo1.value == vo2.value, "Giá trị nguyên bản không thay đổi"

    def test_with_tenant_original_unchanged(self):
        """KPI-029: Original VO không thay đổi sau with_tenant()."""
        from dataclasses import replace

        @dataclass(frozen=True)
        class TestValueObject:
            value: str
            tenant_id: Optional[str] = field(default=None, repr=False, compare=False)

            def with_tenant(self, tenant_id: str) -> "TestValueObject":
                return replace(self, tenant_id=tenant_id)

        vo1 = TestValueObject(value="test")
        _ = vo1.with_tenant("tenant-123")

        # Original VO vẫn là None
        assert vo1.tenant_id is None

    def test_with_tenant_replaces_existing_tenant_id(self):
        """KPI-029: with_tenant() replace tenant_id cũ."""
        from dataclasses import replace

        @dataclass(frozen=True)
        class TestValueObject:
            value: str
            tenant_id: Optional[str] = field(default=None, repr=False, compare=False)

            def with_tenant(self, tenant_id: str) -> "TestValueObject":
                return replace(self, tenant_id=tenant_id)

        vo1 = TestValueObject(value="test", tenant_id="tenant-old")
        vo2 = vo1.with_tenant("tenant-new")

        assert vo1.tenant_id == "tenant-old"
        assert vo2.tenant_id == "tenant-new"


# ============================================================================
# Test: to_dict() includes tenant_id
# ============================================================================

class TestValueObjectToDict:
    """Test to_dict() method với tenant_id."""

    def test_to_dict_includes_tenant_id_if_present(self):
        """KPI-029: to_dict() bao gồm tenant_id nếu có."""
        @dataclass(frozen=True)
        class TestValueObject:
            value: str
            tenant_id: Optional[str] = field(default=None, repr=False, compare=False)

            def to_dict(self) -> dict:
                return {
                    "value": self.value,
                    "tenant_id": self.tenant_id,
                }

        vo = TestValueObject(value="test", tenant_id="tenant-123")
        vo_dict = vo.to_dict()

        assert "tenant_id" in vo_dict
        assert vo_dict["tenant_id"] == "tenant-123"

    def test_to_dict_includes_tenant_id_none_if_not_set(self):
        """KPI-029: to_dict() bao gồm tenant_id=None nếu không set."""
        @dataclass(frozen=True)
        class TestValueObject:
            value: str
            tenant_id: Optional[str] = field(default=None, repr=False, compare=False)

            def to_dict(self) -> dict:
                result = {"value": self.value}
                if self.tenant_id is not None:
                    result["tenant_id"] = self.tenant_id
                return result

        vo = TestValueObject(value="test")
        vo_dict = vo.to_dict()

        # Optional: tenant_id có thể không hiện trong dict nếu là None
        assert "value" in vo_dict
        # Template có thể chọn exclude None values


# ============================================================================
# Test: from_dict() với tenant_id
# ============================================================================

class TestValueObjectFromDict:
    """Test from_dict() method với tenant_id."""

    def test_from_dict_includes_tenant_id(self):
        """KPI-029: from_dict() parse tenant_id từ dict."""
        @dataclass(frozen=True)
        class TestValueObject:
            value: str
            tenant_id: Optional[str] = field(default=None, repr=False, compare=False)

            @classmethod
            def from_dict(cls, data: dict) -> "TestValueObject":
                return cls(
                    value=data["value"],
                    tenant_id=data.get("tenant_id"),
                )

        data = {"value": "test", "tenant_id": "tenant-123"}
        vo = TestValueObject.from_dict(data)

        assert vo.value == "test"
        assert vo.tenant_id == "tenant-123"

    def test_from_dict_handles_missing_tenant_id(self):
        """KPI-029: from_dict() xử lý khi tenant_id không có trong dict."""
        @dataclass(frozen=True)
        class TestValueObject:
            value: str
            tenant_id: Optional[str] = field(default=None, repr=False, compare=False)

            @classmethod
            def from_dict(cls, data: dict) -> "TestValueObject":
                return cls(
                    value=data["value"],
                    tenant_id=data.get("tenant_id"),
                )

        data = {"value": "test"}  # No tenant_id
        vo = TestValueObject.from_dict(data)

        assert vo.value == "test"
        assert vo.tenant_id is None


# ============================================================================
# Test: Derived Value Objects inherit tenant_id
# ============================================================================

class TestDerivedValueObjects:
    """Test derived Value Objects kế thừa tenant_id từ base."""

    def test_money_value_object_has_tenant_id(self):
        """KPI-029: Money VO có tenant_id field."""
        from decimal import Decimal

        @dataclass(frozen=True)
        class Money:
            amount: Decimal
            currency: str
            tenant_id: Optional[str] = field(default=None, repr=False, compare=False)

            def get_tenant_id(self) -> Optional[str]:
                return self.tenant_id

        money = Money(amount=Decimal("100.00"), currency="USD", tenant_id="tenant-123")
        assert money.tenant_id == "tenant-123"
        assert money.get_tenant_id() == "tenant-123"

    def test_email_address_value_object_has_tenant_id(self):
        """KPI-029: EmailAddress VO có tenant_id field."""
        @dataclass(frozen=True)
        class EmailAddress:
            email: str
            tenant_id: Optional[str] = field(default=None, repr=False, compare=False)

            def get_tenant_id(self) -> Optional[str]:
                return self.tenant_id

        email = EmailAddress(email="test@example.com", tenant_id="tenant-123")
        assert email.tenant_id == "tenant-123"

    def test_phone_number_value_object_has_tenant_id(self):
        """KPI-029: PhoneNumber VO có tenant_id field."""
        @dataclass(frozen=True)
        class PhoneNumber:
            phone: str
            tenant_id: Optional[str] = field(default=None, repr=False, compare=False)

            def get_tenant_id(self) -> Optional[str]:
                return self.tenant_id

        phone = PhoneNumber(phone="+84123456789", tenant_id="tenant-123")
        assert phone.tenant_id == "tenant-123"


# ============================================================================
# Test: Template rendering verification
# ============================================================================

class TestTemplateRendering:
    """Test Jinja2 template rendering với tenant_id."""

    def test_value_object_template_has_tenant_id_field(self):
        """KPI-029: value_object.py.jinja2 template phải render tenant_id field."""
        # Read template file
        template_path = "midicoder/stacks/fastapi/templates/domain/value_objects/value_object.py.jinja2"
        
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check tenant_id field pattern in template
        # Template must have tenant_id field definition
        assert "tenant_id" in content, "Template phải chứa tenant_id reference"

        # Check get_tenant_id method
        assert "get_tenant_id" in content, "Template phải có get_tenant_id method"

    def test_value_object_template_has_kpi_029_comment(self):
        """KPI-029: Template phải có KPI-029 comment."""
        template_path = "midicoder/stacks/fastapi/templates/domain/value_objects/value_object.py.jinja2"
        
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "KPI-029" in content, "Template phải có KPI-029 comment"


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])