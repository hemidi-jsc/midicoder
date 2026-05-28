# coding: utf-8
"""
Kiểm tra mô-đun models cho CP50 — Catalog & Taxonomy Engine.

Bao gồm các tests cho:
- Error codes: MDC-CP50-001 đến MDC-CP50-010
- Enums: ProductStatus, AttributeType, SortOrder, Visibility, CategoryLevel
- Product: tạo, validate, auto slug, auto timestamp, to_dict/from_dict
- Category: tạo, validate, auto slug, default, to_dict/from_dict
- ProductVariant: tạo, validate, default, to_dict/from_dict
- AttributeDefinition: tạo, validate, auto key, default type, to_dict/from_dict
- AttributeValue: tạo, validate, various value types, to_dict/from_dict
- CatalogEngine: CRUD product, soft delete, restore, filter,
  duplicate SKU, category tree, ancestors, cycle detection
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from midicoder.errors import ErrorCode, MidicoderError


# ===========================================================================
# Test Error Codes CP50
# ===========================================================================


class TestCP50ErrorCodes:
    """Kiểm tra các mã lỗi CP50 đã được định nghĩa đúng."""

    def test_cp50_product_not_found(self):
        assert ErrorCode.MDC-F32_PRODUCT_NOT_FOUND == "MDC-CP50-001"

    def test_cp50_category_not_found(self):
        assert ErrorCode.MDC-F32_CATEGORY_NOT_FOUND == "MDC-CP50-002"

    def test_cp50_variant_not_found(self):
        assert ErrorCode.MDC-F32_VARIANT_NOT_FOUND == "MDC-CP50-003"

    def test_cp50_attribute_not_found(self):
        assert ErrorCode.MDC-F32_ATTRIBUTE_NOT_FOUND == "MDC-CP50-004"

    def test_cp50_duplicate_sku(self):
        assert ErrorCode.MDC-F32_DUPLICATE_SKU == "MDC-CP50-005"

    def test_cp50_invalid_product_status(self):
        assert ErrorCode.MDC-F32_INVALID_PRODUCT_STATUS == "MDC-CP50-006"

    def test_cp50_category_cycle_detected(self):
        assert ErrorCode.MDC-F32_CATEGORY_CYCLE_DETECTED == "MDC-CP50-007"

    def test_cp50_attribute_type_invalid(self):
        assert ErrorCode.MDC-F32_ATTRIBUTE_TYPE_INVALID == "MDC-CP50-008"

    def test_cp50_category_depth_exceeded(self):
        assert ErrorCode.MDC-F32_CATEGORY_DEPTH_EXCEEDED == "MDC-CP50-009"

    def test_cp50_search_index_not_ready(self):
        assert ErrorCode.MDC-F32_SEARCH_INDEX_NOT_READY == "MDC-CP50-010"


# ===========================================================================
# Test ProductStatus Enum
# ===========================================================================


class TestProductStatus:
    """Kiểm tra các giá trị của enum ProductStatus."""

    def test_status_draft_value(self):
        from midicoder.packs.cp_full_catalog.models import ProductStatus
        assert ProductStatus.DRAFT.value == "draft"

    def test_status_active_value(self):
        from midicoder.packs.cp_full_catalog.models import ProductStatus
        assert ProductStatus.ACTIVE.value == "active"

    def test_status_inactive_value(self):
        from midicoder.packs.cp_full_catalog.models import ProductStatus
        assert ProductStatus.INACTIVE.value == "inactive"

    def test_status_archived_value(self):
        from midicoder.packs.cp_full_catalog.models import ProductStatus
        assert ProductStatus.ARCHIVED.value == "archived"

    def test_status_members_count(self):
        from midicoder.packs.cp_full_catalog.models import ProductStatus
        assert len(ProductStatus) == 4


# ===========================================================================
# Test AttributeType Enum
# ===========================================================================


class TestAttributeType:
    """Kiểm tra các giá trị của enum AttributeType."""

    def test_type_string_value(self):
        from midicoder.packs.cp_full_catalog.models import AttributeType
        assert AttributeType.STRING.value == "string"

    def test_type_number_value(self):
        from midicoder.packs.cp_full_catalog.models import AttributeType
        assert AttributeType.NUMBER.value == "number"

    def test_type_boolean_value(self):
        from midicoder.packs.cp_full_catalog.models import AttributeType
        assert AttributeType.BOOLEAN.value == "boolean"

    def test_type_date_value(self):
        from midicoder.packs.cp_full_catalog.models import AttributeType
        assert AttributeType.DATE.value == "date"

    def test_type_enum_value(self):
        from midicoder.packs.cp_full_catalog.models import AttributeType
        assert AttributeType.ENUM.value == "enum"

    def test_type_color_value(self):
        from midicoder.packs.cp_full_catalog.models import AttributeType
        assert AttributeType.COLOR.value == "color"

    def test_type_members_count(self):
        from midicoder.packs.cp_full_catalog.models import AttributeType
        assert len(AttributeType) == 6


# ===========================================================================
# Test SortOrder Enum
# ===========================================================================


class TestSortOrder:
    """Kiểm tra các giá trị của enum SortOrder."""

    def test_order_asc_value(self):
        from midicoder.packs.cp_full_catalog.models import SortOrder
        assert SortOrder.ASC.value == "asc"

    def test_order_desc_value(self):
        from midicoder.packs.cp_full_catalog.models import SortOrder
        assert SortOrder.DESC.value == "desc"

    def test_order_members_count(self):
        from midicoder.packs.cp_full_catalog.models import SortOrder
        assert len(SortOrder) == 2


# ===========================================================================
# Test Visibility Enum
# ===========================================================================


class TestVisibility:
    """Kiểm tra các giá trị của enum Visibility."""

    def test_visibility_public_value(self):
        from midicoder.packs.cp_full_catalog.models import Visibility
        assert Visibility.PUBLIC.value == "public"

    def test_visibility_internal_value(self):
        from midicoder.packs.cp_full_catalog.models import Visibility
        assert Visibility.INTERNAL.value == "internal"

    def test_visibility_restricted_value(self):
        from midicoder.packs.cp_full_catalog.models import Visibility
        assert Visibility.RESTRICTED.value == "restricted"

    def test_visibility_members_count(self):
        from midicoder.packs.cp_full_catalog.models import Visibility
        assert len(Visibility) == 3


# ===========================================================================
# Test CategoryLevel Enum
# ===========================================================================


class TestCategoryLevel:
    """Kiểm tra các giá trị của enum CategoryLevel."""

    def test_level_root_value(self):
        from midicoder.packs.cp_full_catalog.models import CategoryLevel
        assert CategoryLevel.ROOT.value == "root"

    def test_level_1_value(self):
        from midicoder.packs.cp_full_catalog.models import CategoryLevel
        assert CategoryLevel.LEVEL_1.value == "level_1"

    def test_level_2_value(self):
        from midicoder.packs.cp_full_catalog.models import CategoryLevel
        assert CategoryLevel.LEVEL_2.value == "level_2"

    def test_level_3_value(self):
        from midicoder.packs.cp_full_catalog.models import CategoryLevel
        assert CategoryLevel.LEVEL_3.value == "level_3"

    def test_level_members_count(self):
        from midicoder.packs.cp_full_catalog.models import CategoryLevel
        assert len(CategoryLevel) == 4


# ===========================================================================
# Test Product
# ===========================================================================


class TestProduct:
    """Kiểm tra Product — tạo, validate, auto slug, auto timestamp, serialize."""

    def test_create_valid_product(self):
        """Kiểm tra tạo product hợp lệ với đầy đủ thông tin."""
        from midicoder.packs.cp_full_catalog.models import (
            Product,
            ProductStatus,
        )
        product = Product(
            product_id="prod_001",
            name="Áo thun cotton",
            sku="ATC-001",
            description="Áo thun chất lượng cao",
            category_id="cat_001",
            brand_id="brand_001",
            price=299000.0,
            status=ProductStatus.ACTIVE,
        )
        assert product.product_id == "prod_001"
        assert product.name == "Áo thun cotton"
        assert product.sku == "ATC-001"
        assert product.price == 299000.0
        assert product.status == ProductStatus.ACTIVE

    def test_create_product_empty_product_id_raises(self):
        """Kiểm tra tạo product với product_id rỗng sẽ ném lỗi."""
        from midicoder.packs.cp_full_catalog.models import Product
        with pytest.raises(MidicoderError):
            Product(
                product_id="",
                name="Sản phẩm rỗng ID",
            )

    def test_create_product_whitespace_product_id_raises(self):
        """Kiểm tra tạo product với product_id chỉ khoảng trắng sẽ ném lỗi."""
        from midicoder.packs.cp_full_catalog.models import Product
        with pytest.raises(MidicoderError):
            Product(
                product_id="   ",
                name="Sản phẩm khoảng trắng ID",
            )

    def test_create_product_empty_name_raises(self):
        """Kiểm tra tạo product với name rỗng sẽ ném lỗi."""
        from midicoder.packs.cp_full_catalog.models import Product
        with pytest.raises(MidicoderError):
            Product(
                product_id="prod_empty_name",
                name="",
            )

    def test_auto_slug_generation(self):
        """Kiểm tra tự động tạo slug từ name khi không cung cấp slug."""
        from midicoder.packs.cp_full_catalog.models import Product
        product = Product(
            product_id="prod_slug",
            name="Áo Thun Cotton Cao Cấp",
        )
        assert product.slug == "ao-thun-cotton-cao-cap"

    def test_custom_slug_preserved(self):
        """Kiểm tra slug tùy chỉnh không bị ghi đè."""
        from midicoder.packs.cp_full_catalog.models import Product
        product = Product(
            product_id="prod_custom_slug",
            name="Áo thun",
            slug="custom-url-slug",
        )
        assert product.slug == "custom-url-slug"

    def test_auto_timestamps(self):
        """Kiểm tra tự động đặt created_at khi không cung cấp."""
        from midicoder.packs.cp_full_catalog.models import Product
        product = Product(
            product_id="prod_ts",
            name="Sản phẩm timestamp",
        )
        assert product.created_at is not None
        assert product.updated_at is not None
        assert product.created_at.tzinfo is not None

    def test_default_status_is_draft(self):
        """Kiểm tra trạng thái mặc định là DRAFT."""
        from midicoder.packs.cp_full_catalog.models import (
            Product,
            ProductStatus,
        )
        product = Product(
            product_id="prod_default_status",
            name="Sản phẩm mặc định",
        )
        assert product.status == ProductStatus.DRAFT

    def test_default_currency_is_vnd(self):
        """Kiểm tra tiền tệ mặc định là VND."""
        from midicoder.packs.cp_full_catalog.models import Product
        product = Product(
            product_id="prod_currency",
            name="Sản phẩm tiền tệ",
        )
        assert product.currency == "VND"

    def test_to_dict(self):
        """Kiểm tra chuyển Product sang dict — serialize enums thành .value."""
        from midicoder.packs.cp_full_catalog.models import (
            Product,
            ProductStatus,
            Visibility,
        )
        product = Product(
            product_id="prod_dict",
            name="Sản phẩm dict",
            sku="DICT-001",
            status=ProductStatus.ACTIVE,
            visibility=Visibility.INTERNAL,
            tags=["new", "featured"],
        )
        d = product.to_dict()
        assert d["product_id"] == "prod_dict"
        assert d["name"] == "Sản phẩm dict"
        assert d["sku"] == "DICT-001"
        assert d["status"] == "active"
        assert d["visibility"] == "internal"
        assert d["tags"] == ["new", "featured"]
        assert d["is_deleted"] is False
        assert d["created_at"] is not None

    def test_from_dict_roundtrip(self):
        """Kiểm tra serialize/deserialize Product qua to_dict/from_dict giữ nguyên."""
        from midicoder.packs.cp_full_catalog.models import (
            Product,
            ProductStatus,
            Visibility,
        )
        product = Product(
            product_id="prod_rt",
            name="Sản phẩm roundtrip",
            sku="RT-001",
            category_id="cat_rt",
            brand_id="brand_rt",
            price=150000.0,
            cost_price=100000.0,
            status=ProductStatus.INACTIVE,
            visibility=Visibility.RESTRICTED,
            tags=["sale"],
            metadata={"source": "import"},
        )
        d = product.to_dict()
        restored = Product.from_dict(d)
        assert restored.product_id == "prod_rt"
        assert restored.name == "Sản phẩm roundtrip"
        assert restored.sku == "RT-001"
        assert restored.price == 150000.0
        assert restored.status == ProductStatus.INACTIVE
        assert restored.visibility == Visibility.RESTRICTED
        assert restored.tags == ["sale"]
        assert restored.metadata == {"source": "import"}


# ===========================================================================
# Test Category
# ===========================================================================


class TestCategory:
    """Kiểm tra Category — tạo, validate, auto slug, default, serialize."""

    def test_create_valid_category(self):
        """Kiểm tra tạo category hợp lệ."""
        from midicoder.packs.cp_full_catalog.models import Category
        cat = Category(
            category_id="cat_001",
            name="Điện tử",
            description="Danh mục thiết bị điện tử",
        )
        assert cat.category_id == "cat_001"
        assert cat.name == "Điện tử"
        assert cat.description == "Danh mục thiết bị điện tử"

    def test_create_category_empty_category_id_raises(self):
        """Kiểm tra tạo category với category_id rỗng sẽ ném lỗi."""
        from midicoder.packs.cp_full_catalog.models import Category
        with pytest.raises(MidicoderError):
            Category(
                category_id="",
                name="Danh mục rỗng ID",
            )

    def test_create_category_empty_name_raises(self):
        """Kiểm tra tạo category với name rỗng sẽ ném lỗi."""
        from midicoder.packs.cp_full_catalog.models import Category
        with pytest.raises(MidicoderError):
            Category(
                category_id="cat_empty_name",
                name="",
            )

    def test_auto_slug_generation(self):
        """Kiểm tra tự động tạo slug từ name cho category."""
        from midicoder.packs.cp_full_catalog.models import Category
        cat = Category(
            category_id="cat_slug",
            name="Thiết Bị Nhà Bếp",
        )
        assert cat.slug == "thiet-bi-nha-bep"

    def test_default_parent_id_none(self):
        """Kiểm tra parent_id mặc định là None (cấp gốc)."""
        from midicoder.packs.cp_full_catalog.models import Category
        cat = Category(
            category_id="cat_root",
            name="Danh mục gốc",
        )
        assert cat.parent_id is None

    def test_default_is_active_true(self):
        """Kiểm tra is_active mặc định là True."""
        from midicoder.packs.cp_full_catalog.models import Category
        cat = Category(
            category_id="cat_active",
            name="Danh mục hoạt động",
        )
        assert cat.is_active is True

    def test_default_descendant_count_zero(self):
        """Kiểm tra descendant_count mặc định là 0."""
        from midicoder.packs.cp_full_catalog.models import Category
        cat = Category(
            category_id="cat_desc",
            name="Danh mục đếm con",
        )
        assert cat.descendant_count == 0

    def test_to_dict_from_dict_roundtrip(self):
        """Kiểm tra serialize/deserialize Category qua to_dict/from_dict."""
        from midicoder.packs.cp_full_catalog.models import Category
        cat = Category(
            category_id="cat_rt",
            name="Danh mục roundtrip",
            description="Mô tả roundtrip",
            parent_id="cat_parent",
            sort_order=5,
            icon="icon-electronics",
            is_active=False,
            metadata={"level": 2},
        )
        d = cat.to_dict()
        restored = Category.from_dict(d)
        assert restored.category_id == "cat_rt"
        assert restored.name == "Danh mục roundtrip"
        assert restored.parent_id == "cat_parent"
        assert restored.sort_order == 5
        assert restored.is_active is False
        assert restored.metadata == {"level": 2}


# ===========================================================================
# Test ProductVariant
# ===========================================================================


class TestProductVariant:
    """Kiểm tra ProductVariant — tạo, validate, default, serialize."""

    def test_create_valid_variant(self):
        """Kiểm tra tạo variant hợp lệ."""
        from midicoder.packs.cp_full_catalog.models import ProductVariant
        variant = ProductVariant(
            variant_id="var_001",
            product_id="prod_001",
            sku="VAR-001-RED",
            name="Áo thun màu đỏ",
            attribute_values={"color": "đỏ", "size": "L"},
            price=320000.0,
        )
        assert variant.variant_id == "var_001"
        assert variant.product_id == "prod_001"
        assert variant.sku == "VAR-001-RED"
        assert variant.attribute_values == {"color": "đỏ", "size": "L"}

    def test_create_variant_empty_variant_id_raises(self):
        """Kiểm tra tạo variant với variant_id rỗng sẽ ném lỗi."""
        from midicoder.packs.cp_full_catalog.models import ProductVariant
        with pytest.raises(MidicoderError):
            ProductVariant(
                variant_id="",
                product_id="prod_001",
                sku="VAR-EMPTY-ID",
            )

    def test_create_variant_empty_product_id_raises(self):
        """Kiểm tra tạo variant với product_id rỗng sẽ ném lỗi."""
        from midicoder.packs.cp_full_catalog.models import ProductVariant
        with pytest.raises(MidicoderError):
            ProductVariant(
                variant_id="var_pid",
                product_id="",
                sku="VAR-EMPTY-PID",
            )

    def test_create_variant_empty_sku_raises(self):
        """Kiểm tra tạo variant với sku rỗng sẽ ném lỗi."""
        from midicoder.packs.cp_full_catalog.models import ProductVariant
        with pytest.raises(MidicoderError):
            ProductVariant(
                variant_id="var_sku",
                product_id="prod_001",
                sku="",
            )

    def test_default_is_active_true(self):
        """Kiểm tra is_active mặc định là True cho variant."""
        from midicoder.packs.cp_full_catalog.models import ProductVariant
        variant = ProductVariant(
            variant_id="var_default",
            product_id="prod_001",
            sku="VAR-DEFAULT",
        )
        assert variant.is_active is True

    def test_to_dict_from_dict_roundtrip(self):
        """Kiểm tra serialize/deserialize ProductVariant qua to_dict/from_dict."""
        from midicoder.packs.cp_full_catalog.models import ProductVariant
        variant = ProductVariant(
            variant_id="var_rt",
            product_id="prod_rt",
            sku="VAR-RT",
            name="Biến thể roundtrip",
            attribute_values={"color": "xanh", "size": "M"},
            price=250000.0,
            cost_price=180000.0,
            weight=0.3,
            barcode="123456789012",
            images=["https://example.com/img.jpg"],
            sort_order=2,
            metadata={"warehouse": "A1"},
        )
        d = variant.to_dict()
        restored = ProductVariant.from_dict(d)
        assert restored.variant_id == "var_rt"
        assert restored.product_id == "prod_rt"
        assert restored.sku == "VAR-RT"
        assert restored.attribute_values == {"color": "xanh", "size": "M"}
        assert restored.price == 250000.0
        assert restored.barcode == "123456789012"
        assert restored.sort_order == 2
        assert restored.metadata == {"warehouse": "A1"}


# ===========================================================================
# Test AttributeDefinition
# ===========================================================================


class TestAttributeDefinition:
    """Kiểm tra AttributeDefinition — tạo, validate, auto key, default type, serialize."""

    def test_create_valid_attribute(self):
        """Kiểm tra tạo attribute definition hợp lệ."""
        from midicoder.packs.cp_full_catalog.models import (
            AttributeDefinition,
            AttributeType,
        )
        attr = AttributeDefinition(
            attribute_id="attr_001",
            name="Màu sắc",
            attribute_type=AttributeType.STRING,
            is_required=True,
            is_searchable=True,
        )
        assert attr.attribute_id == "attr_001"
        assert attr.name == "Màu sắc"
        assert attr.attribute_type == AttributeType.STRING
        assert attr.is_required is True

    def test_create_attribute_empty_attribute_id_raises(self):
        """Kiểm tra tạo attribute với attribute_id rỗng sẽ ném lỗi."""
        from midicoder.packs.cp_full_catalog.models import AttributeDefinition
        with pytest.raises(MidicoderError):
            AttributeDefinition(
                attribute_id="",
                name="Thuộc tính rỗng ID",
            )

    def test_create_attribute_empty_name_raises(self):
        """Kiểm tra tạo attribute với name rỗng sẽ ném lỗi."""
        from midicoder.packs.cp_full_catalog.models import AttributeDefinition
        with pytest.raises(MidicoderError):
            AttributeDefinition(
                attribute_id="attr_empty",
                name="",
            )

    def test_default_type_is_string(self):
        """Kiểm tra loại thuộc tính mặc định là STRING."""
        from midicoder.packs.cp_full_catalog.models import (
            AttributeDefinition,
            AttributeType,
        )
        attr = AttributeDefinition(
            attribute_id="attr_default_type",
            name="Thuộc tính mặc định",
        )
        assert attr.attribute_type == AttributeType.STRING

    def test_auto_key_from_name(self):
        """Kiểm tra tự động tạo key từ name khi không cung cấp key."""
        from midicoder.packs.cp_full_catalog.models import AttributeDefinition
        attr = AttributeDefinition(
            attribute_id="attr_key",
            name="Chiều Dài Sản Phẩm",
        )
        assert attr.key == "chieu-dai-san-pham"

    def test_default_is_visible_true(self):
        """Kiểm tra is_visible mặc định là True."""
        from midicoder.packs.cp_full_catalog.models import AttributeDefinition
        attr = AttributeDefinition(
            attribute_id="attr_visible",
            name="Thuộc tính hiển thị",
        )
        assert attr.is_visible is True

    def test_to_dict_from_dict_roundtrip(self):
        """Kiểm tra serialize/deserialize AttributeDefinition qua to_dict/from_dict."""
        from midicoder.packs.cp_full_catalog.models import (
            AttributeDefinition,
            AttributeType,
        )
        attr = AttributeDefinition(
            attribute_id="attr_rt",
            name="Kích cỡ",
            attribute_type=AttributeType.ENUM,
            is_required=True,
            validation_rules={"min": 1, "max": 100},
            options=["S", "M", "L", "XL", "XXL"],
            unit="",
            is_searchable=True,
            is_filterable=True,
            sort_order=1,
            metadata={"group": "size"},
        )
        d = attr.to_dict()
        restored = AttributeDefinition.from_dict(d)
        assert restored.attribute_id == "attr_rt"
        assert restored.name == "Kích cỡ"
        assert restored.attribute_type == AttributeType.ENUM
        assert restored.is_required is True
        assert restored.options == ["S", "M", "L", "XL", "XXL"]
        assert restored.is_searchable is True
        assert restored.is_filterable is True
        assert restored.metadata == {"group": "size"}


# ===========================================================================
# Test AttributeValue
# ===========================================================================


class TestAttributeValue:
    """Kiểm tra AttributeValue — tạo, validate, various value types, serialize."""

    def test_create_valid_attribute_value(self):
        """Kiểm tra tạo attribute value hợp lệ."""
        from midicoder.packs.cp_full_catalog.models import AttributeValue
        av = AttributeValue(
            attribute_value_id="av_001",
            attribute_id="attr_001",
            product_id="prod_001",
            value="đỏ",
        )
        assert av.attribute_value_id == "av_001"
        assert av.attribute_id == "attr_001"
        assert av.product_id == "prod_001"
        assert av.value == "đỏ"

    def test_create_av_empty_id_raises(self):
        """Kiểm tra tạo attribute value với attribute_value_id rỗng sẽ ném lỗi."""
        from midicoder.packs.cp_full_catalog.models import AttributeValue
        with pytest.raises(MidicoderError):
            AttributeValue(
                attribute_value_id="",
                attribute_id="attr_001",
            )

    def test_create_av_empty_attribute_id_raises(self):
        """Kiểm tra tạo attribute value với attribute_id rỗng sẽ ném lỗi."""
        from midicoder.packs.cp_full_catalog.models import AttributeValue
        with pytest.raises(MidicoderError):
            AttributeValue(
                attribute_value_id="av_empty_attr",
                attribute_id="",
            )

    def test_various_value_types(self):
        """Kiểm tra attribute value hỗ trợ nhiều loại giá trị: str, int, float, bool, list."""
        from midicoder.packs.cp_full_catalog.models import AttributeValue

        # Giá trị chuỗi
        av_str = AttributeValue(
            attribute_value_id="av_str",
            attribute_id="attr_001",
            value="chuỗi giá trị",
        )
        assert av_str.value == "chuỗi giá trị"

        # Giá trị số nguyên
        av_int = AttributeValue(
            attribute_value_id="av_int",
            attribute_id="attr_002",
            value=42,
        )
        assert av_int.value == 42

        # Giá trị số thực
        av_float = AttributeValue(
            attribute_value_id="av_float",
            attribute_id="attr_003",
            value=3.14,
        )
        assert av_float.value == 3.14

        # Giá trị boolean
        av_bool = AttributeValue(
            attribute_value_id="av_bool",
            attribute_id="attr_004",
            value=True,
        )
        assert av_bool.value is True

        # Giá trị danh sách
        av_list = AttributeValue(
            attribute_value_id="av_list",
            attribute_id="attr_005",
            value=["giá trị 1", "giá trị 2"],
        )
        assert av_list.value == ["giá trị 1", "giá trị 2"]

    def test_to_dict_from_dict_roundtrip(self):
        """Kiểm tra serialize/deserialize AttributeValue qua to_dict/from_dict."""
        from midicoder.packs.cp_full_catalog.models import AttributeValue
        av = AttributeValue(
            attribute_value_id="av_rt",
            attribute_id="attr_rt",
            product_id="prod_rt",
            variant_id="var_rt",
            value={"nested": "value"},
        )
        d = av.to_dict()
        restored = AttributeValue.from_dict(d)
        assert restored.attribute_value_id == "av_rt"
        assert restored.attribute_id == "attr_rt"
        assert restored.product_id == "prod_rt"
        assert restored.variant_id == "var_rt"
        assert restored.value == {"nested": "value"}


# ===========================================================================
# Test CatalogEngine
# ===========================================================================


class TestCatalogEngine:
    """Kiểm tra CatalogEngine — CRUD product, category, variant, attribute, tìm kiếm."""

    def _create_engine(self) -> "CatalogEngine":
        """Tạo engine mới cho mỗi test."""
        from midicoder.packs.cp_full_catalog.models import CatalogEngine
        return CatalogEngine()

    # ---------------------------------------------------------------------
    # Product CRUD
    # ---------------------------------------------------------------------

    def test_create_and_get_product(self):
        """Kiểm tra tạo và lấy product qua CatalogEngine."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Product,
        )
        engine = self._create_engine()
        product = Product(
            product_id="engine_prod_001",
            name="Sản phẩm engine",
            sku="ENG-001",
        )
        created = engine.create_product(product)
        assert created.product_id == "engine_prod_001"

        fetched = engine.get_product("engine_prod_001")
        assert fetched.product_id == "engine_prod_001"
        assert fetched.name == "Sản phẩm engine"

    def test_update_product(self):
        """Kiểm tra cập nhật thông tin product qua CatalogEngine."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Product,
            ProductStatus,
        )
        engine = self._create_engine()
        engine.create_product(Product(
            product_id="update_prod",
            name="Tên cũ",
            sku="UPD-001",
            price=100000.0,
        ))
        updated = engine.update_product(
            "update_prod",
            name="Tên mới",
            price=200000.0,
            status=ProductStatus.ACTIVE,
        )
        assert updated.name == "Tên mới"
        assert updated.price == 200000.0
        assert updated.status == ProductStatus.ACTIVE

    def test_delete_product_soft(self):
        """Kiểm tra xóa mềm product: is_deleted=True, deleted_at được đặt."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Product,
        )
        engine = self._create_engine()
        engine.create_product(Product(
            product_id="delete_prod",
            name="Sản phẩm xóa",
            sku="DEL-001",
        ))
        deleted = engine.delete_product("delete_prod")
        assert deleted.is_deleted is True
        assert deleted.deleted_at is not None

        # Product vẫn tồn tại trong engine nhưng đã bị xóa mềm
        fetched = engine.get_product("delete_prod")
        assert fetched.is_deleted is True

    def test_restore_product(self):
        """Kiểm tra khôi phục product đã xóa mềm: is_deleted=False."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Product,
            ProductStatus,
        )
        engine = self._create_engine()
        engine.create_product(Product(
            product_id="restore_prod",
            name="Sản phẩm khôi phục",
            sku="RST-001",
            status=ProductStatus.ACTIVE,
        ))
        engine.delete_product("restore_prod")
        restored = engine.restore_product("restore_prod")
        assert restored.is_deleted is False
        assert restored.deleted_at is None
        # Khôi phục về trạng thái DRAFT để người dùng xem lại
        assert restored.status == ProductStatus.DRAFT

    def test_list_products_filter_by_status(self):
        """Kiểm tra lọc danh sách product theo trạng thái."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Product,
            ProductStatus,
        )
        engine = self._create_engine()
        engine.create_product(Product(
            product_id="list_001",
            name="Sản phẩm active",
            status=ProductStatus.ACTIVE,
        ))
        engine.create_product(Product(
            product_id="list_002",
            name="Sản phẩm draft",
            status=ProductStatus.DRAFT,
        ))
        engine.create_product(Product(
            product_id="list_003",
            name="Sản phẩm inactive",
            status=ProductStatus.INACTIVE,
        ))

        active_list = engine.list_products(status=ProductStatus.ACTIVE)
        assert len(active_list) == 1
        assert active_list[0].product_id == "list_001"

        draft_list = engine.list_products(status=ProductStatus.DRAFT)
        assert len(draft_list) == 1
        assert draft_list[0].product_id == "list_002"

    def test_list_products_filter_by_category(self):
        """Kiểm tra lọc danh sách product theo category_id."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Product,
        )
        engine = self._create_engine()
        engine.create_product(Product(
            product_id="cat_prod_001",
            name="SP danh mục A",
            category_id="cat_a",
        ))
        engine.create_product(Product(
            product_id="cat_prod_002",
            name="SP danh mục B",
            category_id="cat_b",
        ))
        engine.create_product(Product(
            product_id="cat_prod_003",
            name="SP danh mục A khác",
            category_id="cat_a",
        ))

        cat_a_list = engine.list_products(category_id="cat_a")
        assert len(cat_a_list) == 2
        ids = {p.product_id for p in cat_a_list}
        assert ids == {"cat_prod_001", "cat_prod_003"}

    def test_list_products_excludes_deleted(self):
        """Kiểm tra list_products loại trừ sản phẩm đã xóa mềm."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Product,
        )
        engine = self._create_engine()
        engine.create_product(Product(
            product_id="live_prod",
            name="Sản phẩm sống",
        ))
        engine.create_product(Product(
            product_id="dead_prod",
            name="Sản phẩm chết",
        ))
        engine.delete_product("dead_prod")

        all_products = engine.list_products()
        assert len(all_products) == 1
        assert all_products[0].product_id == "live_prod"

    def test_create_product_duplicate_sku_raises(self):
        """Kiểm tra tạo product có SKU trùng lặp sẽ ném lỗi."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Product,
        )
        engine = self._create_engine()
        engine.create_product(Product(
            product_id="dup_sku_001",
            name="Sản phẩm SKU 1",
            sku="DUP-SKU-001",
        ))
        with pytest.raises(MidicoderError):
            engine.create_product(Product(
                product_id="dup_sku_002",
                name="Sản phẩm SKU 2",
                sku="DUP-SKU-001",
            ))

    def test_get_product_not_found_raises(self):
        """Kiểm tra lấy product không tồn tại sẽ ném lỗi."""
        engine = self._create_engine()
        with pytest.raises(MidicoderError):
            engine.get_product("non_existent_product")

    def test_update_product_not_found_raises(self):
        """Kiểm tra cập nhật product không tồn tại sẽ ném lỗi."""
        engine = self._create_engine()
        with pytest.raises(MidicoderError):
            engine.update_product("non_existent", name="Tên mới")

    # ---------------------------------------------------------------------
    # Category
    # ---------------------------------------------------------------------

    def test_create_and_get_category(self):
        """Kiểm tra tạo category qua CatalogEngine."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Category,
        )
        engine = self._create_engine()
        cat = Category(
            category_id="engine_cat_001",
            name="Danh mục engine",
        )
        created = engine.create_category(cat)
        assert created.category_id == "engine_cat_001"
        assert created.name == "Danh mục engine"

    def test_get_category_tree(self):
        """Kiểm tra xây dựng cây danh mục theo thứ tự BFS."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Category,
        )
        engine = self._create_engine()
        # Tạo cây: root -> child1, child2
        engine.create_category(Category(
            category_id="tree_root",
            name="Gốc",
            sort_order=0,
        ))
        engine.create_category(Category(
            category_id="tree_c1",
            name="Con 1",
            parent_id="tree_root",
            sort_order=1,
        ))
        engine.create_category(Category(
            category_id="tree_c2",
            name="Con 2",
            parent_id="tree_root",
            sort_order=2,
        ))
        engine.create_category(Category(
            category_id="tree_c1_1",
            name="Cháu 1",
            parent_id="tree_c1",
            sort_order=0,
        ))

        tree = engine.get_category_tree()
        ids = [c.category_id for c in tree]
        # BFS: root, child1, child2, cháu1
        assert ids[0] == "tree_root"
        assert "tree_c1" in ids[1:3]
        assert "tree_c2" in ids[1:3]
        assert ids[-1] == "tree_c1_1"

    def test_get_category_ancestors(self):
        """Kiểm tra lấy danh sách tổ tiên của category (từ gốc đến cha trực tiếp)."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Category,
        )
        engine = self._create_engine()
        engine.create_category(Category(
            category_id="anc_root",
            name="Tổ tiên gốc",
        ))
        engine.create_category(Category(
            category_id="anc_mid",
            name="Tổ tiên giữa",
            parent_id="anc_root",
        ))
        engine.create_category(Category(
            category_id="anc_leaf",
            name="Lá",
            parent_id="anc_mid",
        ))

        ancestors = engine.get_category_ancestors("anc_leaf")
        assert len(ancestors) == 2
        # Từ gốc đến cha trực tiếp
        assert ancestors[0].category_id == "anc_root"
        assert ancestors[1].category_id == "anc_mid"

    def test_get_category_ancestors_root_returns_empty(self):
        """Kiểm tra lấy tổ tiên của category gốc trả về danh sách rỗng."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Category,
        )
        engine = self._create_engine()
        engine.create_category(Category(
            category_id="no_anc",
            name="Không tổ tiên",
        ))
        ancestors = engine.get_category_ancestors("no_anc")
        assert len(ancestors) == 0

    def test_create_category_cycle_detected(self):
        """Kiểm tra tạo category gây chu kỳ sẽ ném MidicoderError.

        Thiết lập: root -> child, sau đó cố gắng tạo category có ID=root
        với parent=child (tức là child -> root, tạo chu kỳ root -> child -> root).
        """
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Category,
        )
        engine = self._create_engine()
        # Tạo cây: cycle_root -> cycle_child
        engine.create_category(Category(
            category_id="cycle_root",
            name="Chu kỳ gốc",
        ))
        engine.create_category(Category(
            category_id="cycle_child",
            name="Chu kỳ con",
            parent_id="cycle_root",
        ))
        # Cố gắng tạo category mới có ID="cycle_root" và parent="cycle_child"
        # -> ancestors của "cycle_child" bao gồm "cycle_root" -> phát hiện chu kỳ
        with pytest.raises(MidicoderError):
            engine.create_category(Category(
                category_id="cycle_root",
                name="Chu kỳ gốc mới",
                parent_id="cycle_child",
            ))

    def test_create_category_updates_parent_descendant_count(self):
        """Kiểm tra tạo category con làm tăng descendant_count của parent."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Category,
        )
        engine = self._create_engine()
        engine.create_category(Category(
            category_id="parent_count",
            name="Parent đếm",
        ))
        parent = engine.categories["parent_count"]
        assert parent.descendant_count == 0

        engine.create_category(Category(
            category_id="child_count",
            name="Child đếm",
            parent_id="parent_count",
        ))
        parent = engine.categories["parent_count"]
        assert parent.descendant_count == 1

    # ---------------------------------------------------------------------
    # Variant
    # ---------------------------------------------------------------------

    def test_create_variant_through_engine(self):
        """Kiểm tra tạo variant qua CatalogEngine."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Product,
            ProductVariant,
        )
        engine = self._create_engine()
        engine.create_product(Product(
            product_id="var_engine_prod",
            name="Sản phẩm variant",
        ))
        variant = engine.create_variant(ProductVariant(
            variant_id="var_engine_001",
            product_id="var_engine_prod",
            sku="VAR-ENG-001",
            name="Biến thể engine",
        ))
        assert variant.variant_id == "var_engine_001"

    def test_create_variant_product_not_found_raises(self):
        """Kiểm tra tạo variant với product_id không tồn tại sẽ ném lỗi."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            ProductVariant,
        )
        engine = self._create_engine()
        with pytest.raises(MidicoderError):
            engine.create_variant(ProductVariant(
                variant_id="var_no_prod",
                product_id="non_existent",
                sku="VAR-NO-PROD",
            ))

    def test_list_variants_for_product(self):
        """Kiểm tra liệt kê variants của product, sắp theo sort_order."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Product,
            ProductVariant,
        )
        engine = self._create_engine()
        engine.create_product(Product(
            product_id="list_var_prod",
            name="SP liệt kê variant",
        ))
        engine.create_variant(ProductVariant(
            variant_id="lv_002",
            product_id="list_var_prod",
            sku="LV-002",
            sort_order=2,
        ))
        engine.create_variant(ProductVariant(
            variant_id="lv_001",
            product_id="list_var_prod",
            sku="LV-001",
            sort_order=1,
        ))

        variants = engine.list_variants_for_product("list_var_prod")
        assert len(variants) == 2
        assert variants[0].variant_id == "lv_001"
        assert variants[1].variant_id == "lv_002"

    # ---------------------------------------------------------------------
    # Attribute
    # ---------------------------------------------------------------------

    def test_create_attribute_definition(self):
        """Kiểm tra tạo attribute definition qua CatalogEngine."""
        from midicoder.packs.cp_full_catalog.models import (
            AttributeDefinition,
            AttributeType,
            CatalogEngine,
        )
        engine = self._create_engine()
        attr = AttributeDefinition(
            attribute_id="attr_engine",
            name="Trọng lượng",
            attribute_type=AttributeType.NUMBER,
            unit="kg",
        )
        created = engine.create_attribute_definition(attr)
        assert created.attribute_id == "attr_engine"
        assert created.attribute_type == AttributeType.NUMBER

    def test_set_and_get_product_attribute(self):
        """Kiểm tra đặt và lấy giá trị thuộc tính cho product."""
        from midicoder.packs.cp_full_catalog.models import (
            AttributeDefinition,
            CatalogEngine,
            Product,
        )
        engine = self._create_engine()
        engine.create_product(Product(
            product_id="attr_prod",
            name="SP thuộc tính",
        ))
        engine.create_attribute_definition(AttributeDefinition(
            attribute_id="attr_weight",
            name="Trọng lượng",
            unit="kg",
        ))
        av = engine.set_attribute_value(
            product_id="attr_prod",
            attribute_id="attr_weight",
            value=0.5,
        )
        assert av.value == 0.5

        attrs = engine.get_product_attributes("attr_prod")
        assert attrs["trong-luong"] == 0.5

    def test_update_existing_attribute_value(self):
        """Kiểm tra cập nhật giá trị thuộc tính cũ thay vì tạo mới."""
        from midicoder.packs.cp_full_catalog.models import (
            AttributeDefinition,
            CatalogEngine,
            Product,
        )
        engine = self._create_engine()
        engine.create_product(Product(
            product_id="update_attr_prod",
            name="SP cập nhật thuộc tính",
        ))
        engine.create_attribute_definition(AttributeDefinition(
            attribute_id="attr_color",
            name="Màu sắc",
        ))
        av1 = engine.set_attribute_value(
            product_id="update_attr_prod",
            attribute_id="attr_color",
            value="đỏ",
        )
        av2 = engine.set_attribute_value(
            product_id="update_attr_prod",
            attribute_id="attr_color",
            value="xanh",
        )
        # Cùng một đối tượng, giá trị đã được cập nhật
        assert av1.attribute_value_id == av2.attribute_value_id
        assert av2.value == "xanh"

    # ---------------------------------------------------------------------
    # Faceted Search
    # ---------------------------------------------------------------------

    def test_search_products_by_query(self):
        """Kiểm tra tìm kiếm product theo chuỗi query."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Product,
        )
        engine = self._create_engine()
        engine.create_product(Product(
            product_id="search_001",
            name="Áo thun nam",
            description="Áo thun cotton cho nam",
        ))
        engine.create_product(Product(
            product_id="search_002",
            name="Váy nữ",
            description="Váy hoa cho nữ",
        ))

        result = engine.search_products(query="nam")
        assert result["total"] == 1
        assert result["results"][0].product_id == "search_001"

    def test_search_products_with_filters(self):
        """Kiểm tra tìm kiếm product với bộ lọc status và category."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Product,
            ProductStatus,
        )
        engine = self._create_engine()
        engine.create_product(Product(
            product_id="filter_001",
            name="SP lọc 1",
            category_id="cat_elec",
            status=ProductStatus.ACTIVE,
            price=500000.0,
        ))
        engine.create_product(Product(
            product_id="filter_002",
            name="SP lọc 2",
            category_id="cat_elec",
            status=ProductStatus.DRAFT,
            price=300000.0,
        ))
        engine.create_product(Product(
            product_id="filter_003",
            name="SP lọc 3",
            category_id="cat_fashion",
            status=ProductStatus.ACTIVE,
            price=200000.0,
        ))

        # Lọc theo status và category
        result = engine.search_products(
            query="",
            filters={
                "status": "active",
                "category_id": "cat_elec",
            },
        )
        assert result["total"] == 1
        assert result["results"][0].product_id == "filter_001"

    def test_search_products_price_range(self):
        """Kiểm tra tìm kiếm product theo khoảng giá."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Product,
        )
        engine = self._create_engine()
        engine.create_product(Product(
            product_id="price_001",
            name="SP giá thấp",
            price=100000.0,
        ))
        engine.create_product(Product(
            product_id="price_002",
            name="SP giá giữa",
            price=250000.0,
        ))
        engine.create_product(Product(
            product_id="price_003",
            name="SP giá cao",
            price=500000.0,
        ))

        result = engine.search_products(
            query="",
            filters={
                "min_price": 150000.0,
                "max_price": 400000.0,
            },
        )
        assert result["total"] == 1
        assert result["results"][0].product_id == "price_002"

    def test_search_products_aggregations(self):
        """Kiểm tra aggregations trong kết quả tìm kiếm."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Product,
            ProductStatus,
        )
        engine = self._create_engine()
        engine.create_product(Product(
            product_id="agg_001",
            name="SP tổng hợp 1",
            category_id="cat_a",
            brand_id="brand_x",
            status=ProductStatus.ACTIVE,
        ))
        engine.create_product(Product(
            product_id="agg_002",
            name="SP tổng hợp 2",
            category_id="cat_a",
            brand_id="brand_y",
            status=ProductStatus.DRAFT,
        ))
        engine.create_product(Product(
            product_id="agg_003",
            name="SP tổng hợp 3",
            category_id="cat_b",
            brand_id="brand_x",
            status=ProductStatus.ACTIVE,
        ))

        result = engine.search_products(query="")
        agg = result["aggregations"]
        assert agg["category_count"]["cat_a"] == 2
        assert agg["category_count"]["cat_b"] == 1
        assert agg["brand_count"]["brand_x"] == 2
        assert agg["brand_count"]["brand_y"] == 1
        assert agg["status_count"]["active"] == 2
        assert agg["status_count"]["draft"] == 1

    def test_search_products_by_tags(self):
        """Kiểm tra tìm kiếm product theo danh sách tags."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Product,
        )
        engine = self._create_engine()
        engine.create_product(Product(
            product_id="tag_001",
            name="SP tag 1",
            tags=["sale", "new"],
        ))
        engine.create_product(Product(
            product_id="tag_002",
            name="SP tag 2",
            tags=["featured"],
        ))

        result = engine.search_products(
            query="",
            filters={"tags": ["sale"]},
        )
        assert result["total"] == 1
        assert result["results"][0].product_id == "tag_001"

    def test_search_excludes_deleted_products(self):
        """Kiểm tra tìm kiếm loại trừ sản phẩm đã xóa mềm."""
        from midicoder.packs.cp_full_catalog.models import (
            CatalogEngine,
            Product,
        )
        engine = self._create_engine()
        engine.create_product(Product(
            product_id="search_live",
            name="SP tìm kiếm sống",
        ))
        engine.create_product(Product(
            product_id="search_dead",
            name="SP tìm kiếm chết",
        ))
        engine.delete_product("search_dead")

        result = engine.search_products(query="SP tìm kiếm")
        assert result["total"] == 1
        assert result["results"][0].product_id == "search_live"
