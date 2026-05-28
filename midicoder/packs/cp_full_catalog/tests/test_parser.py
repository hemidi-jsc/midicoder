# coding: utf-8
"""
Kiểm tra mô-đun parser cho CP50 — Catalog & Taxonomy Engine.

Bao gồm các tests cho:
- CatalogIR: empty, with data, to_dict/from_dict roundtrip, flags
- parse_products: từ key 'products', từ alias 'catalog', empty, all fields, id alias, defaults
- parse_categories: từ key 'categories', từ alias 'taxonomy', empty, parent_id, all fields
- parse_variants: từ key 'variants', empty, all fields, id alias, variant_id alias
- parse_attribute_definitions: từ key 'attribute_definitions', từ alias 'attributes', empty
- parse_attribute_values: từ key 'attribute_values', empty, product/variant, value types
- parse_to_ir: full data, empty data, partial data, use_search, use_audit, alias keys

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import pytest

from midicoder.packs.cp_full_catalog.parser import (
    CatalogIR,
    parse_attribute_definitions,
    parse_attribute_values,
    parse_categories,
    parse_products,
    parse_to_ir,
    parse_variants,
)
from midicoder.packs.cp_full_catalog.models import (
    AttributeDefinition,
    AttributeType,
    AttributeValue,
    Category,
    Product,
    ProductStatus,
    ProductVariant,
    Visibility,
)


# ===========================================================================
# Test CatalogIR
# ===========================================================================


class TestCatalogIR:
    """Kiểm tra CatalogIR — khởi tạo, serialize, deserialize."""

    def test_catalog_ir_empty(self):
        """Kiểm tra CatalogIR rỗng có các danh sách rỗng và flags mặc định."""
        ir = CatalogIR()
        assert ir.products == []
        assert ir.categories == []
        assert ir.variants == []
        assert ir.attributes == []
        assert ir.attribute_values == []
        assert ir.use_search is True
        assert ir.use_audit is False

    def test_catalog_ir_to_dict_empty(self):
        """Kiểm tra chuyển CatalogIR rỗng sang dict với đầy đủ keys."""
        ir = CatalogIR()
        d = ir.to_dict()
        assert "products" in d
        assert "categories" in d
        assert "variants" in d
        assert "attributes" in d
        assert "attribute_values" in d
        assert "use_search" in d
        assert "use_audit" in d
        assert d["products"] == []
        assert d["categories"] == []
        assert d["variants"] == []
        assert d["attributes"] == []
        assert d["attribute_values"] == []
        assert d["use_search"] is True
        assert d["use_audit"] is False

    def test_catalog_ir_with_data(self):
        """Kiểm tra CatalogIR có dữ liệu đầy đủ các loại đối tượng."""
        product = Product(
            product_id="p_001",
            name="Sản phẩm thử",
            sku="SKU-001",
        )
        category = Category(
            category_id="c_001",
            name="Danh mục thử",
        )
        variant = ProductVariant(
            variant_id="v_001",
            product_id="p_001",
            sku="SKU-V001",
        )
        attribute = AttributeDefinition(
            attribute_id="a_001",
            name="Màu sắc",
        )
        attr_value = AttributeValue(
            attribute_value_id="av_001",
            attribute_id="a_001",
            product_id="p_001",
            value="Đỏ",
        )
        ir = CatalogIR(
            products=[product],
            categories=[category],
            variants=[variant],
            attributes=[attribute],
            attribute_values=[attr_value],
            use_search=False,
            use_audit=True,
        )
        assert len(ir.products) == 1
        assert len(ir.categories) == 1
        assert len(ir.variants) == 1
        assert len(ir.attributes) == 1
        assert len(ir.attribute_values) == 1
        assert ir.use_search is False
        assert ir.use_audit is True

    def test_catalog_ir_to_dict_with_data(self):
        """Kiểm tra chuyển CatalogIR có dữ liệu sang dict đúng."""
        product = Product(
            product_id="p_dict",
            name="Sản phẩm dict",
            sku="SKU-DICT",
        )
        category = Category(
            category_id="c_dict",
            name="Danh mục dict",
        )
        ir = CatalogIR(
            products=[product],
            categories=[category],
            use_search=True,
            use_audit=False,
        )
        d = ir.to_dict()
        assert len(d["products"]) == 1
        assert d["products"][0]["product_id"] == "p_dict"
        assert len(d["categories"]) == 1
        assert d["categories"][0]["category_id"] == "c_dict"
        assert d["use_search"] is True
        assert d["use_audit"] is False

    def test_catalog_ir_from_dict_roundtrip(self):
        """Kiểm tra CatalogIR to_dict rồi from_dict giữ nguyên dữ liệu."""
        product = Product(
            product_id="p_rt",
            name="Sản phẩm roundtrip",
            sku="SKU-RT",
            price=100000,
            currency="VND",
        )
        category = Category(
            category_id="c_rt",
            name="Danh mục roundtrip",
            sort_order=1,
        )
        variant = ProductVariant(
            variant_id="v_rt",
            product_id="p_rt",
            sku="SKU-V-RT",
        )
        attribute = AttributeDefinition(
            attribute_id="a_rt",
            name="Kích cỡ",
            attribute_type=AttributeType.STRING,
        )
        attr_value = AttributeValue(
            attribute_value_id="av_rt",
            attribute_id="a_rt",
            variant_id="v_rt",
            value="L",
        )
        ir = CatalogIR(
            products=[product],
            categories=[category],
            variants=[variant],
            attributes=[attribute],
            attribute_values=[attr_value],
            use_search=False,
            use_audit=True,
        )
        d = ir.to_dict()
        restored = CatalogIR.from_dict(d)
        assert len(restored.products) == 1
        assert restored.products[0].product_id == "p_rt"
        assert len(restored.categories) == 1
        assert restored.categories[0].category_id == "c_rt"
        assert len(restored.variants) == 1
        assert restored.variants[0].variant_id == "v_rt"
        assert len(restored.attributes) == 1
        assert restored.attributes[0].attribute_id == "a_rt"
        assert len(restored.attribute_values) == 1
        assert restored.attribute_values[0].attribute_value_id == "av_rt"
        assert restored.use_search is False
        assert restored.use_audit is True

    def test_catalog_ir_flags_default(self):
        """Kiểm tra use_search mặc định là True và use_audit mặc định là False."""
        ir = CatalogIR()
        assert ir.use_search is True
        assert ir.use_audit is False


# ===========================================================================
# Test parse_products
# ===========================================================================


class TestParseProducts:
    """Kiểm tra parse_products — nhiều key, alias, rỗng, defaults."""

    def test_parse_from_products_key(self):
        """Kiểm tra parse từ key chính 'products'."""
        data = {
            "products": [
                {
                    "product_id": "p_001",
                    "name": "Sản phẩm từ products",
                    "sku": "SKU-001",
                }
            ]
        }
        result = parse_products(data)
        assert len(result) == 1
        assert result[0].product_id == "p_001"
        assert result[0].name == "Sản phẩm từ products"

    def test_parse_from_catalog_alias_key(self):
        """Kiểm tra parse từ key alias 'catalog'."""
        data = {
            "catalog": [
                {
                    "product_id": "p_002",
                    "name": "Sản phẩm từ catalog",
                    "sku": "SKU-002",
                }
            ]
        }
        result = parse_products(data)
        assert len(result) == 1
        assert result[0].product_id == "p_002"
        assert result[0].name == "Sản phẩm từ catalog"

    def test_parse_empty(self):
        """Kiểm tra parse dữ liệu rỗng trả về danh sách rỗng."""
        data = {}
        result = parse_products(data)
        assert len(result) == 0

    def test_parse_with_all_fields(self):
        """Kiểm tra parse với tất cả các trường đầy đủ của sản phẩm."""
        data = {
            "products": [
                {
                    "product_id": "p_full",
                    "name": "Sản phẩm đầy đủ",
                    "sku": "SKU-FULL",
                    "description": "Mô tả sản phẩm đầy đủ",
                    "category_id": "c_full",
                    "brand_id": "b_full",
                    "price": 150000,
                    "cost_price": 100000,
                    "compare_at_price": 200000,
                    "currency": "USD",
                    "weight": 1.5,
                    "status": "active",
                    "visibility": "internal",
                    "tags": ["hot", "sale"],
                    "images": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
                    "seo_metadata": {"title": "SEO title", "description": "SEO desc"},
                }
            ]
        }
        result = parse_products(data)
        assert len(result) == 1
        p = result[0]
        assert p.product_id == "p_full"
        assert p.price == 150000.0
        assert p.cost_price == 100000.0
        assert p.compare_at_price == 200000.0
        assert p.currency == "USD"
        assert p.weight == 1.5
        assert p.status == ProductStatus.ACTIVE
        assert p.visibility == Visibility.INTERNAL
        assert p.tags == ["hot", "sale"]
        assert len(p.images) == 2
        assert p.seo_metadata["title"] == "SEO title"

    def test_parse_with_id_alias(self):
        """Kiểm tra alias key 'id' thay cho 'product_id'."""
        data = {
            "products": [
                {
                    "id": "p_alias_id",
                    "name": "Sản phẩm id alias",
                    "sku": "SKU-ALIAS",
                }
            ]
        }
        result = parse_products(data)
        assert result[0].product_id == "p_alias_id"

    def test_parse_with_defaults(self):
        """Kiểm tra các giá trị mặc định khi trường không được cung cấp."""
        data = {
            "products": [
                {
                    "product_id": "p_default",
                    "name": "Sản phẩm mặc định",
                    "sku": "SKU-DEFAULT",
                }
            ]
        }
        result = parse_products(data)
        assert result[0].status == ProductStatus.DRAFT
        assert result[0].visibility == Visibility.PUBLIC
        assert result[0].currency == "VND"
        assert result[0].price == 0.0
        assert result[0].cost_price == 0.0
        assert result[0].weight == 0.0
        assert result[0].tags == []
        assert result[0].images == []

    def test_parse_multiple_products(self):
        """Kiểm tra parse nhiều sản phẩm cùng lúc."""
        data = {
            "products": [
                {
                    "product_id": "p_001",
                    "name": "Sản phẩm thứ nhất",
                    "sku": "SKU-001",
                },
                {
                    "product_id": "p_002",
                    "name": "Sản phẩm thứ hai",
                    "sku": "SKU-002",
                    "status": "active",
                },
                {
                    "product_id": "p_003",
                    "name": "Sản phẩm thứ ba",
                    "sku": "SKU-003",
                    "status": "archived",
                },
            ]
        }
        result = parse_products(data)
        assert len(result) == 3
        assert result[0].product_id == "p_001"
        assert result[1].product_id == "p_002"
        assert result[2].product_id == "p_003"
        assert result[1].status == ProductStatus.ACTIVE
        assert result[2].status == ProductStatus.ARCHIVED

    def test_parse_product_with_vietnamese_name(self):
        """Kiểm tra slug tự động sinh từ tên tiếng Việt có dấu."""
        data = {
            "products": [
                {
                    "product_id": "p_vi",
                    "name": "Áo phông nam cao cấp",
                    "sku": "SKU-VI",
                }
            ]
        }
        result = parse_products(data)
        assert len(result) == 1
        # _slugify dùng NFKD normalize + encode ascii ignore -> "phông" => "phong"
        assert result[0].slug == "ao-phong-nam-cao-cap"


# ===========================================================================
# Test parse_categories
# ===========================================================================


class TestParseCategories:
    """Kiểm tra parse_categories — nhiều key, alias, rỗng."""

    def test_parse_from_categories_key(self):
        """Kiểm tra parse từ key chính 'categories'."""
        data = {
            "categories": [
                {
                    "category_id": "c_001",
                    "name": "Danh mục chính",
                }
            ]
        }
        result = parse_categories(data)
        assert len(result) == 1
        assert result[0].category_id == "c_001"
        assert result[0].name == "Danh mục chính"

    def test_parse_from_taxonomy_alias_key(self):
        """Kiểm tra parse từ key alias 'taxonomy'."""
        data = {
            "taxonomy": [
                {
                    "category_id": "c_002",
                    "name": "Danh mục từ taxonomy",
                }
            ]
        }
        result = parse_categories(data)
        assert len(result) == 1
        assert result[0].category_id == "c_002"
        assert result[0].name == "Danh mục từ taxonomy"

    def test_parse_empty(self):
        """Kiểm tra parse dữ liệu rỗng trả về danh sách rỗng."""
        data = {}
        result = parse_categories(data)
        assert len(result) == 0

    def test_parse_with_parent_id(self):
        """Kiểm tra parse danh mục có parent_id để tạo cấu trúc cây."""
        data = {
            "categories": [
                {
                    "category_id": "c_parent",
                    "name": "Danh mục cha",
                },
                {
                    "category_id": "c_child",
                    "name": "Danh mục con",
                    "parent_id": "c_parent",
                },
            ]
        }
        result = parse_categories(data)
        assert len(result) == 2
        assert result[0].parent_id is None
        assert result[1].parent_id == "c_parent"

    def test_parse_with_all_fields(self):
        """Kiểm tra parse với tất cả các trường đầy đủ của danh mục."""
        data = {
            "categories": [
                {
                    "category_id": "c_full",
                    "name": "Danh mục đầy đủ",
                    "slug": "custom-slug",
                    "description": "Mô tả danh mục",
                    "parent_id": "c_parent",
                    "sort_order": 5,
                    "icon": "📦",
                    "is_active": False,
                    "descendant_count": 10,
                    "metadata": {"custom_key": "custom_value"},
                }
            ]
        }
        result = parse_categories(data)
        assert len(result) == 1
        c = result[0]
        assert c.category_id == "c_full"
        assert c.slug == "custom-slug"
        assert c.description == "Mô tả danh mục"
        assert c.parent_id == "c_parent"
        assert c.sort_order == 5
        assert c.icon == "📦"
        assert c.is_active is False
        assert c.descendant_count == 10
        assert c.metadata["custom_key"] == "custom_value"

    def test_parse_with_id_alias(self):
        """Kiểm tra alias key 'id' và 'cat_id' thay cho 'category_id'."""
        data = {
            "categories": [
                {
                    "id": "c_id_alias",
                    "name": "Danh mục id alias",
                }
            ]
        }
        result = parse_categories(data)
        assert result[0].category_id == "c_id_alias"

    def test_parse_multiple_categories(self):
        """Kiểm tra parse nhiều danh mục cùng lúc."""
        data = {
            "categories": [
                {
                    "category_id": "c_001",
                    "name": "Danh mục một",
                    "sort_order": 1,
                },
                {
                    "category_id": "c_002",
                    "name": "Danh mục hai",
                    "sort_order": 2,
                },
                {
                    "category_id": "c_003",
                    "name": "Danh mục ba",
                    "sort_order": 3,
                    "is_active": False,
                },
            ]
        }
        result = parse_categories(data)
        assert len(result) == 3
        assert result[0].category_id == "c_001"
        assert result[1].category_id == "c_002"
        assert result[2].category_id == "c_003"
        assert result[2].is_active is False


# ===========================================================================
# Test parse_variants
# ===========================================================================


class TestParseVariants:
    """Kiểm tra parse_variants — nhiều key, alias, rỗng."""

    def test_parse_from_variants_key(self):
        """Kiểm tra parse từ key chính 'variants'."""
        data = {
            "variants": [
                {
                    "variant_id": "v_001",
                    "product_id": "p_001",
                    "sku": "SKU-V001",
                }
            ]
        }
        result = parse_variants(data)
        assert len(result) == 1
        assert result[0].variant_id == "v_001"
        assert result[0].product_id == "p_001"

    def test_parse_empty(self):
        """Kiểm tra parse dữ liệu rỗng trả về danh sách rỗng."""
        data = {}
        result = parse_variants(data)
        assert len(result) == 0

    def test_parse_with_all_fields(self):
        """Kiểm tra parse với tất cả các trường đầy đủ của biến thể."""
        data = {
            "variants": [
                {
                    "variant_id": "v_full",
                    "product_id": "p_full",
                    "sku": "SKU-VFULL",
                    "name": "Biến thể đầy đủ",
                    "attribute_values": {"color": "red", "size": "L"},
                    "price": 200000,
                    "cost_price": 150000,
                    "weight": 0.8,
                    "barcode": "1234567890123",
                    "images": ["https://example.com/variant.jpg"],
                    "is_active": True,
                    "sort_order": 1,
                    "metadata": {"supplier": "ACME"},
                }
            ]
        }
        result = parse_variants(data)
        assert len(result) == 1
        v = result[0]
        assert v.variant_id == "v_full"
        assert v.attribute_values == {"color": "red", "size": "L"}
        assert v.price == 200000.0
        assert v.cost_price == 150000.0
        assert v.weight == 0.8
        assert v.barcode == "1234567890123"
        assert len(v.images) == 1
        assert v.is_active is True
        assert v.sort_order == 1
        assert v.metadata["supplier"] == "ACME"

    def test_parse_with_id_alias(self):
        """Kiểm tra alias key 'id' thay cho 'variant_id' và 'product' thay cho 'product_id'."""
        data = {
            "variants": [
                {
                    "id": "v_alias_id",
                    "product": "p_alias_prod",
                    "sku": "SKU-ALIAS-V",
                }
            ]
        }
        result = parse_variants(data)
        assert result[0].variant_id == "v_alias_id"
        assert result[0].product_id == "p_alias_prod"

    def test_parse_multiple_variants(self):
        """Kiểm tra parse nhiều biến thể cùng lúc."""
        data = {
            "variants": [
                {
                    "variant_id": "v_001",
                    "product_id": "p_001",
                    "sku": "SKU-V001",
                },
                {
                    "variant_id": "v_002",
                    "product_id": "p_001",
                    "sku": "SKU-V002",
                },
                {
                    "variant_id": "v_003",
                    "product_id": "p_002",
                    "sku": "SKU-V003",
                    "is_active": False,
                },
            ]
        }
        result = parse_variants(data)
        assert len(result) == 3
        assert result[0].variant_id == "v_001"
        assert result[1].variant_id == "v_002"
        assert result[2].variant_id == "v_003"
        assert result[2].is_active is False

    def test_parse_with_variant_id_alias(self):
        """Kiểm tra alias 'id' cho variant_id và 'product' cho product_id."""
        data = {
            "variants": [
                {
                    "id": "v_alias_2",
                    "product": "p_alias_2",
                    "sku": "SKU-V-ALIAS-2",
                    "name": "Biến thể alias",
                }
            ]
        }
        result = parse_variants(data)
        assert result[0].variant_id == "v_alias_2"
        assert result[0].product_id == "p_alias_2"


# ===========================================================================
# Test parse_attribute_definitions
# ===========================================================================


class TestParseAttributeDefinitions:
    """Kiểm tra parse_attribute_definitions — nhiều key, alias, rỗng."""

    def test_parse_from_attribute_definitions_key(self):
        """Kiểm tra parse từ key chính 'attribute_definitions'."""
        data = {
            "attribute_definitions": [
                {
                    "attribute_id": "a_001",
                    "name": "Màu sắc",
                }
            ]
        }
        result = parse_attribute_definitions(data)
        assert len(result) == 1
        assert result[0].attribute_id == "a_001"
        assert result[0].name == "Màu sắc"

    def test_parse_from_attributes_alias_key(self):
        """Kiểm tra parse từ key alias 'attributes'."""
        data = {
            "attributes": [
                {
                    "attribute_id": "a_002",
                    "name": "Kích cỡ",
                }
            ]
        }
        result = parse_attribute_definitions(data)
        assert len(result) == 1
        assert result[0].attribute_id == "a_002"
        assert result[0].name == "Kích cỡ"

    def test_parse_empty(self):
        """Kiểm tra parse dữ liệu rỗng trả về danh sách rỗng."""
        data = {}
        result = parse_attribute_definitions(data)
        assert len(result) == 0

    def test_parse_with_all_fields(self):
        """Kiểm tra parse với tất cả các trường đầy đủ của định nghĩa thuộc tính."""
        data = {
            "attribute_definitions": [
                {
                    "attribute_id": "a_full",
                    "name": "Trọng lượng",
                    "key": "weight-attr",
                    "attribute_type": "number",
                    "is_required": True,
                    "validation_rules": {"min": 0, "max": 100},
                    "options": [],
                    "unit": "kg",
                    "is_searchable": True,
                    "is_filterable": True,
                    "is_visible": True,
                    "sort_order": 1,
                    "metadata": {"source": "admin"},
                }
            ]
        }
        result = parse_attribute_definitions(data)
        assert len(result) == 1
        a = result[0]
        assert a.attribute_id == "a_full"
        assert a.key == "weight-attr"
        assert a.attribute_type == AttributeType.NUMBER
        assert a.is_required is True
        assert a.validation_rules == {"min": 0, "max": 100}
        assert a.unit == "kg"
        assert a.is_searchable is True
        assert a.is_filterable is True
        assert a.is_visible is True
        assert a.sort_order == 1

    def test_parse_with_id_alias(self):
        """Kiểm tra alias key 'id' thay cho 'attribute_id' và 'type' thay cho 'attribute_type'."""
        data = {
            "attribute_definitions": [
                {
                    "id": "a_alias_id",
                    "name": "Chất liệu",
                    "type": "enum",
                }
            ]
        }
        result = parse_attribute_definitions(data)
        assert result[0].attribute_id == "a_alias_id"
        assert result[0].attribute_type == AttributeType.ENUM

    def test_parse_multiple_attributes(self):
        """Kiểm tra parse nhiều định nghĩa thuộc tính cùng lúc."""
        data = {
            "attribute_definitions": [
                {
                    "attribute_id": "a_001",
                    "name": "Màu sắc",
                    "attribute_type": "string",
                },
                {
                    "attribute_id": "a_002",
                    "name": "Trọng lượng",
                    "attribute_type": "number",
                    "is_required": True,
                },
                {
                    "attribute_id": "a_003",
                    "name": "Có sẵn",
                    "attribute_type": "boolean",
                },
            ]
        }
        result = parse_attribute_definitions(data)
        assert len(result) == 3
        assert result[0].attribute_id == "a_001"
        assert result[0].attribute_type == AttributeType.STRING
        assert result[1].attribute_id == "a_002"
        assert result[1].attribute_type == AttributeType.NUMBER
        assert result[2].attribute_id == "a_003"
        assert result[2].attribute_type == AttributeType.BOOLEAN


# ===========================================================================
# Test parse_attribute_values
# ===========================================================================


class TestParseAttributeValues:
    """Kiểm tra parse_attribute_values — nhiều key, alias, rỗng, value types."""

    def test_parse_from_attribute_values_key(self):
        """Kiểm tra parse từ key chính 'attribute_values'."""
        data = {
            "attribute_values": [
                {
                    "attribute_value_id": "av_001",
                    "attribute_id": "a_001",
                    "value": "Đỏ",
                }
            ]
        }
        result = parse_attribute_values(data)
        assert len(result) == 1
        assert result[0].attribute_value_id == "av_001"
        assert result[0].attribute_id == "a_001"
        assert result[0].value == "Đỏ"

    def test_parse_empty(self):
        """Kiểm tra parse dữ liệu rỗng trả về danh sách rỗng."""
        data = {}
        result = parse_attribute_values(data)
        assert len(result) == 0

    def test_parse_with_product_and_variant(self):
        """Kiểm tra parse giá trị thuộc tính gắn với product_id và variant_id."""
        data = {
            "attribute_values": [
                {
                    "attribute_value_id": "av_prod",
                    "attribute_id": "a_001",
                    "product_id": "p_001",
                    "value": "Giá trị cấp sản phẩm",
                },
                {
                    "attribute_value_id": "av_var",
                    "attribute_id": "a_002",
                    "variant_id": "v_001",
                    "value": "Giá trị cấp biến thể",
                },
            ]
        }
        result = parse_attribute_values(data)
        assert len(result) == 2
        assert result[0].product_id == "p_001"
        assert result[0].variant_id == ""
        assert result[1].product_id == ""
        assert result[1].variant_id == "v_001"

    def test_parse_various_value_types(self):
        """Kiểm tra parse các loại giá trị khác nhau: str, int, float, bool, list."""
        data = {
            "attribute_values": [
                {
                    "attribute_value_id": "av_str",
                    "attribute_id": "a_001",
                    "value": "chuỗi ký tự",
                },
                {
                    "attribute_value_id": "av_int",
                    "attribute_id": "a_002",
                    "value": 42,
                },
                {
                    "attribute_value_id": "av_float",
                    "attribute_id": "a_003",
                    "value": 3.14,
                },
                {
                    "attribute_value_id": "av_bool",
                    "attribute_id": "a_004",
                    "value": True,
                },
                {
                    "attribute_value_id": "av_list",
                    "attribute_id": "a_005",
                    "value": ["option1", "option2"],
                },
            ]
        }
        result = parse_attribute_values(data)
        assert len(result) == 5
        assert result[0].value == "chuỗi ký tự"
        assert result[1].value == 42
        assert result[2].value == 3.14
        assert result[3].value is True
        assert result[4].value == ["option1", "option2"]

    def test_parse_multiple_values(self):
        """Kiểm tra parse nhiều giá trị thuộc tính cùng lúc."""
        data = {
            "attribute_values": [
                {
                    "attribute_value_id": "av_001",
                    "attribute_id": "a_001",
                    "product_id": "p_001",
                    "value": "Giá trị 1",
                },
                {
                    "attribute_value_id": "av_002",
                    "attribute_id": "a_001",
                    "product_id": "p_002",
                    "value": "Giá trị 2",
                },
                {
                    "attribute_value_id": "av_003",
                    "attribute_id": "a_002",
                    "variant_id": "v_001",
                    "value": "Giá trị 3",
                },
            ]
        }
        result = parse_attribute_values(data)
        assert len(result) == 3
        assert result[0].attribute_value_id == "av_001"
        assert result[1].attribute_value_id == "av_002"
        assert result[2].attribute_value_id == "av_003"


# ===========================================================================
# Test parse_to_ir
# ===========================================================================


class TestParseToIR:
    """Kiểm tra parse_to_ir — DSL dict sang CatalogIR."""

    def test_parse_full_data(self):
        """Kiểm tra parse toàn bộ dữ liệu DSL sang CatalogIR với tất cả keys."""
        data = {
            "products": [
                {
                    "product_id": "p_ir",
                    "name": "Sản phẩm IR",
                    "sku": "SKU-IR",
                }
            ],
            "categories": [
                {
                    "category_id": "c_ir",
                    "name": "Danh mục IR",
                }
            ],
            "variants": [
                {
                    "variant_id": "v_ir",
                    "product_id": "p_ir",
                    "sku": "SKU-VIR",
                }
            ],
            "attribute_definitions": [
                {
                    "attribute_id": "a_ir",
                    "name": "Thuộc tính IR",
                }
            ],
            "attribute_values": [
                {
                    "attribute_value_id": "av_ir",
                    "attribute_id": "a_ir",
                    "product_id": "p_ir",
                    "value": "Giá trị IR",
                }
            ],
            "use_search": True,
            "use_audit": True,
        }
        ir = parse_to_ir(data)
        assert len(ir.products) == 1
        assert len(ir.categories) == 1
        assert len(ir.variants) == 1
        assert len(ir.attributes) == 1
        assert len(ir.attribute_values) == 1
        assert ir.products[0].product_id == "p_ir"
        assert ir.categories[0].category_id == "c_ir"
        assert ir.variants[0].variant_id == "v_ir"
        assert ir.attributes[0].attribute_id == "a_ir"
        assert ir.attribute_values[0].attribute_value_id == "av_ir"
        assert ir.use_search is True
        assert ir.use_audit is True

    def test_parse_empty_data(self):
        """Kiểm tra parse dữ liệu rỗng trả về CatalogIR với tất cả defaults."""
        data = {}
        ir = parse_to_ir(data)
        assert len(ir.products) == 0
        assert len(ir.categories) == 0
        assert len(ir.variants) == 0
        assert len(ir.attributes) == 0
        assert len(ir.attribute_values) == 0
        assert ir.use_search is True
        assert ir.use_audit is False

    def test_parse_partial_data(self):
        """Kiểm tra parse chỉ có products, các thành phần khác trả về rỗng."""
        data = {
            "products": [
                {
                    "product_id": "p_partial",
                    "name": "Sản phẩm riêng lẻ",
                    "sku": "SKU-PARTIAL",
                }
            ]
        }
        ir = parse_to_ir(data)
        assert len(ir.products) == 1
        assert len(ir.categories) == 0
        assert len(ir.variants) == 0
        assert len(ir.attributes) == 0
        assert len(ir.attribute_values) == 0
        assert ir.products[0].product_id == "p_partial"

    def test_parse_preserves_use_search(self):
        """Kiểm tra parse giữ nguyên giá trị use_search khi được khai báo."""
        data = {
            "use_search": False,
        }
        ir = parse_to_ir(data)
        assert ir.use_search is False

    def test_parse_preserves_use_audit(self):
        """Kiểm tra parse giữ nguyên giá trị use_audit khi được khai báo."""
        data = {
            "use_audit": True,
        }
        ir = parse_to_ir(data)
        assert ir.use_audit is True

    def test_parse_with_alias_keys(self):
        """Kiểm tra parse sử dụng tất cả key alias cho các thành phần."""
        data = {
            "catalog": [
                {
                    "product_id": "p_alias",
                    "name": "Sản phẩm alias",
                    "sku": "SKU-ALIAS",
                }
            ],
            "taxonomy": [
                {
                    "category_id": "c_alias",
                    "name": "Danh mục alias",
                }
            ],
            "attributes": [
                {
                    "attribute_id": "a_alias",
                    "name": "Thuộc tính alias",
                }
            ],
        }
        ir = parse_to_ir(data)
        assert len(ir.products) == 1
        assert ir.products[0].product_id == "p_alias"
        assert len(ir.categories) == 1
        assert ir.categories[0].category_id == "c_alias"
        assert len(ir.attributes) == 1
        assert ir.attributes[0].attribute_id == "a_alias"
        assert len(ir.variants) == 0
        assert len(ir.attribute_values) == 0
