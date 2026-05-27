# coding: utf-8
"""
Kiểm tra mô-đun recipes cho CP50 — Catalog & Taxonomy Engine.

Bao gồm các tests cho:
- RecipeOutput: tạo, fields, loại IR
- basic_catalog_recipe: tên, mô tả, 2 categories, 2 products (ACTIVE/DRAFT),
  1 attribute definition (color ENUM), 1 variant, use_search True, use_audit False
- full_catalog_recipe: tên, mô tả, 5 categories phân cấp, 4 products (ACTIVE/INACTIVE/DRAFT/ARCHIVED),
  2 variants (sku khác nhau), 3 attribute definitions (color/size/weight),
  attribute values liên kết sản phẩm, use_search True, use_audit False
- to_dict roundtrip
"""

from __future__ import annotations

import pytest

from midicoder.packs.cp50_catalog.recipes import (
    RecipeOutput,
    basic_catalog_recipe,
    full_catalog_recipe,
)
from midicoder.packs.cp50_catalog.parser import CatalogIR
from midicoder.packs.cp50_catalog.models import ProductStatus, AttributeType


# ===========================================================================
# Test RecipeOutput
# ===========================================================================


class TestRecipeOutput:
    """Kiểm tra RecipeOutput — dataclass cơ bản."""

    def test_returns_recipe_output(self):
        """Kiểm tra recipe trả về đối tượng RecipeOutput."""
        output = basic_catalog_recipe()
        assert isinstance(output, RecipeOutput)

    def test_ir_is_catalog_ir(self):
        """Kiểm tra ir là đối tượng CatalogIR."""
        output = basic_catalog_recipe()
        assert type(output.ir).__name__ == "CatalogIR"

    def test_has_name_and_description(self):
        """Kiểm tra RecipeOutput có name và description không rỗng."""
        output = basic_catalog_recipe()
        assert output.name
        assert output.description


# ===========================================================================
# Test basic_catalog_recipe
# ===========================================================================


class TestBasicCatalogRecipe:
    """Kiểm tra basic_catalog_recipe — 2 categories, 2 products, 1 attribute, 1 variant."""

    def test_name_is_basic_catalog(self):
        """Kiểm tra tên recipe là basic_catalog."""
        output = basic_catalog_recipe()
        assert output.name == "basic_catalog"

    def test_has_description(self):
        """Kiểm tra recipe có mô tả không rỗng."""
        output = basic_catalog_recipe()
        assert output.description
        assert len(output.description) > 10

    def test_has_two_categories(self):
        """Kiểm tra có đúng 2 danh mục: cat_root và cat_sub."""
        output = basic_catalog_recipe()
        assert len(output.ir.categories) == 2

    def test_first_category_is_root(self):
        """Kiểm tra danh mục đầu tiên là root (parent_id=None)."""
        output = basic_catalog_recipe()
        cat_root = output.ir.categories[0]
        assert cat_root.category_id == "cat_root"
        assert cat_root.parent_id is None

    def test_second_category_has_parent(self):
        """Kiểm tra danh mục thứ hai có parent_id trỏ về cat_root."""
        output = basic_catalog_recipe()
        cat_sub = output.ir.categories[1]
        assert cat_sub.category_id == "cat_sub"
        assert cat_sub.parent_id == "cat_root"

    def test_has_two_products(self):
        """Kiểm tra có đúng 2 sản phẩm: prod_001 (ACTIVE), prod_002 (DRAFT)."""
        output = basic_catalog_recipe()
        assert len(output.ir.products) == 2

    def test_first_product_is_active(self):
        """Kiểm tra sản phẩm đầu tiên có trạng thái ACTIVE."""
        output = basic_catalog_recipe()
        assert output.ir.products[0].product_id == "prod_001"
        assert output.ir.products[0].status == ProductStatus.ACTIVE

    def test_second_product_is_draft(self):
        """Kiểm tra sản phẩm thứ hai có trạng thái DRAFT."""
        output = basic_catalog_recipe()
        assert output.ir.products[1].product_id == "prod_002"
        assert output.ir.products[1].status == ProductStatus.DRAFT

    def test_products_belong_to_sub_category(self):
        """Kiểm tra cả 2 sản phẩm thuộc danh mục con cat_sub."""
        output = basic_catalog_recipe()
        assert output.ir.products[0].category_id == "cat_sub"
        assert output.ir.products[1].category_id == "cat_sub"

    def test_has_one_attribute_definition(self):
        """Kiểm tra có đúng 1 định nghĩa thuộc tính — color, type=ENUM."""
        output = basic_catalog_recipe()
        assert len(output.ir.attributes) == 1
        assert output.ir.attributes[0].attribute_id == "attr_color"
        assert output.ir.attributes[0].attribute_type == AttributeType.ENUM

    def test_attribute_has_options(self):
        """Kiểm tra thuộc tính color có 3 lựa chọn: Đỏ, Xanh, Vàng."""
        output = basic_catalog_recipe()
        attr = output.ir.attributes[0]
        assert attr.options == ["Đỏ", "Xanh", "Vàng"]

    def test_has_one_variant(self):
        """Kiểm tra có đúng 1 biến thể sản phẩm."""
        output = basic_catalog_recipe()
        assert len(output.ir.variants) == 1

    def test_variant_belongs_to_first_product(self):
        """Kiểm tra biến thể thuộc về sản phẩm đầu tiên (prod_001)."""
        output = basic_catalog_recipe()
        assert output.ir.variants[0].variant_id == "var_001"
        assert output.ir.variants[0].product_id == "prod_001"

    def test_use_search_is_true(self):
        """Kiểm tra use_search là True."""
        output = basic_catalog_recipe()
        assert output.ir.use_search is True

    def test_use_audit_is_false(self):
        """Kiểm tra use_audit là False."""
        output = basic_catalog_recipe()
        assert output.ir.use_audit is False

    def test_product_ids_are_unique(self):
        """Kiểm tra các product_id là duy nhất."""
        output = basic_catalog_recipe()
        ids = [p.product_id for p in output.ir.products]
        assert len(ids) == len(set(ids))


# ===========================================================================
# Test full_catalog_recipe
# ===========================================================================


class TestFullCatalogRecipe:
    """Kiểm tra full_catalog_recipe — 5 categories, 4 products, 2 variants, 3 attributes."""

    def test_name_is_full_catalog(self):
        """Kiểm tra tên recipe là full_catalog."""
        output = full_catalog_recipe()
        assert output.name == "full_catalog"

    def test_has_description(self):
        """Kiểm tra recipe có mô tả không rỗng."""
        output = full_catalog_recipe()
        assert output.description
        assert len(output.description) > 10

    def test_has_five_categories(self):
        """Kiểm tra có đúng 5 danh mục phân cấp."""
        output = full_catalog_recipe()
        assert len(output.ir.categories) == 5

    def test_categories_have_nested_hierarchy(self):
        """Kiểm tra các danh mục có cấu trúc phân cấp: root → level1 → level2 → level3."""
        output = full_catalog_recipe()
        cats = {c.category_id: c for c in output.ir.categories}

        # cat_root không có cha
        assert cats["cat_root"].parent_id is None

        # cat_level1 → cat_root
        assert cats["cat_level1"].parent_id == "cat_root"

        # cat_level2 → cat_level1
        assert cats["cat_level2"].parent_id == "cat_level1"

        # cat_level3 → cat_level2
        assert cats["cat_level3"].parent_id == "cat_level2"

        # cat_level3_alt → cat_level2
        assert cats["cat_level3_alt"].parent_id == "cat_level2"

    def test_has_four_products(self):
        """Kiểm tra có đúng 4 sản phẩm."""
        output = full_catalog_recipe()
        assert len(output.ir.products) == 4

    def test_all_product_statuses_present(self):
        """Kiểm tra 4 trạng thái sản phẩm đều có mặt: ACTIVE, INACTIVE, DRAFT, ARCHIVED."""
        output = full_catalog_recipe()
        statuses = {p.status for p in output.ir.products}
        assert ProductStatus.ACTIVE in statuses
        assert ProductStatus.INACTIVE in statuses
        assert ProductStatus.DRAFT in statuses
        assert ProductStatus.ARCHIVED in statuses

    def test_first_product_is_active(self):
        """Kiểm tra sản phẩm đầu tiên có trạng thái ACTIVE."""
        output = full_catalog_recipe()
        assert output.ir.products[0].product_id == "prod_full_001"
        assert output.ir.products[0].status == ProductStatus.ACTIVE

    def test_second_product_is_inactive(self):
        """Kiểm tra sản phẩm thứ hai có trạng thái INACTIVE."""
        output = full_catalog_recipe()
        assert output.ir.products[1].product_id == "prod_full_002"
        assert output.ir.products[1].status == ProductStatus.INACTIVE

    def test_third_product_is_draft(self):
        """Kiểm tra sản phẩm thứ ba có trạng thái DRAFT."""
        output = full_catalog_recipe()
        assert output.ir.products[2].product_id == "prod_full_003"
        assert output.ir.products[2].status == ProductStatus.DRAFT

    def test_fourth_product_is_archived(self):
        """Kiểm tra sản phẩm thứ tư có trạng thái ARCHIVED."""
        output = full_catalog_recipe()
        assert output.ir.products[3].product_id == "prod_full_004"
        assert output.ir.products[3].status == ProductStatus.ARCHIVED

    def test_has_two_variants_for_first_product(self):
        """Kiểm tra có 2 biến thể cho sản phẩm đầu tiên (prod_full_001)."""
        output = full_catalog_recipe()
        assert len(output.ir.variants) == 2
        assert output.ir.variants[0].product_id == "prod_full_001"
        assert output.ir.variants[1].product_id == "prod_full_001"

    def test_variants_have_different_skus(self):
        """Kiểm tra các biến thể có SKU khác nhau."""
        output = full_catalog_recipe()
        skus = [v.sku for v in output.ir.variants]
        assert len(skus) == len(set(skus))
        assert "TSHIRT-OVS-001-M" in skus
        assert "TSHIRT-OVS-001-L" in skus

    def test_has_three_attribute_definitions(self):
        """Kiểm tra có đúng 3 định nghĩa thuộc tính."""
        output = full_catalog_recipe()
        assert len(output.ir.attributes) == 3

    def test_attributes_include_color_size_weight(self):
        """Kiểm tra 3 thuộc tính: color (ENUM), size (ENUM), weight (NUMBER)."""
        output = full_catalog_recipe()
        attrs = {a.attribute_id: a for a in output.ir.attributes}
        assert "attr_color" in attrs
        assert attrs["attr_color"].attribute_type == AttributeType.ENUM
        assert "attr_size" in attrs
        assert attrs["attr_size"].attribute_type == AttributeType.ENUM
        assert "attr_weight" in attrs
        assert attrs["attr_weight"].attribute_type == AttributeType.NUMBER

    def test_has_attribute_values(self):
        """Kiểm tra attribute_values không rỗng."""
        output = full_catalog_recipe()
        assert len(output.ir.attribute_values) > 0

    def test_attribute_values_linked_to_products(self):
        """Kiểm tra các giá trị thuộc tính được liên kết với sản phẩm."""
        output = full_catalog_recipe()
        product_ids = {p.product_id for p in output.ir.products}
        for av in output.ir.attribute_values:
            assert av.product_id in product_ids

    def test_use_search_is_true(self):
        """Kiểm tra use_search là True."""
        output = full_catalog_recipe()
        assert output.ir.use_search is True

    def test_use_audit_is_false(self):
        """Kiểm tra use_audit là False."""
        output = full_catalog_recipe()
        assert output.ir.use_audit is False

    def test_product_ids_are_unique(self):
        """Kiểm tra các product_id là duy nhất."""
        output = full_catalog_recipe()
        ids = [p.product_id for p in output.ir.products]
        assert len(ids) == len(set(ids))

    def test_variant_ids_are_unique(self):
        """Kiểm tra các variant_id là duy nhất."""
        output = full_catalog_recipe()
        ids = [v.variant_id for v in output.ir.variants]
        assert len(ids) == len(set(ids))

    def test_attribute_ids_are_unique(self):
        """Kiểm tra các attribute_id là duy nhất."""
        output = full_catalog_recipe()
        ids = [a.attribute_id for a in output.ir.attributes]
        assert len(ids) == len(set(ids))


# ===========================================================================
# Test Recipe to_dict roundtrip
# ===========================================================================


class TestRecipeToDict:
    """Kiểm tra to_dict và from_dict roundtrip cho các recipe."""

    def test_basic_recipe_ir_to_dict(self):
        """Kiểm tra basic recipe chuyển sang dict có đúng cấu trúc."""
        output = basic_catalog_recipe()
        d = output.ir.to_dict()
        assert "products" in d
        assert "categories" in d
        assert "variants" in d
        assert "attributes" in d
        assert "attribute_values" in d
        assert "use_search" in d
        assert "use_audit" in d
        assert len(d["products"]) == 2
        assert len(d["categories"]) == 2
        assert len(d["variants"]) == 1
        assert len(d["attributes"]) == 1

    def test_basic_recipe_ir_from_dict_roundtrip(self):
        """Kiểm tra basic recipe roundtrip to_dict -> from_dict giữ nguyên dữ liệu."""
        output = basic_catalog_recipe()
        d = output.ir.to_dict()
        restored = CatalogIR.from_dict(d)
        assert len(restored.products) == 2
        assert len(restored.categories) == 2
        assert len(restored.variants) == 1
        assert len(restored.attributes) == 1
        assert restored.products[0].product_id == "prod_001"
        assert restored.categories[0].category_id == "cat_root"
        assert restored.use_search is True
        assert restored.use_audit is False

    def test_full_recipe_ir_to_dict(self):
        """Kiểm tra full recipe chuyển sang dict có đầy đủ dữ liệu."""
        output = full_catalog_recipe()
        d = output.ir.to_dict()
        assert len(d["products"]) == 4
        assert len(d["categories"]) == 5
        assert len(d["variants"]) == 2
        assert len(d["attributes"]) == 3
        assert len(d["attribute_values"]) > 0
        assert d["use_search"] is True
        assert d["use_audit"] is False

    def test_full_recipe_ir_from_dict_roundtrip(self):
        """Kiểm tra full recipe roundtrip to_dict -> from_dict giữ nguyên dữ liệu."""
        output = full_catalog_recipe()
        d = output.ir.to_dict()
        restored = CatalogIR.from_dict(d)
        assert len(restored.products) == 4
        assert len(restored.categories) == 5
        assert len(restored.variants) == 2
        assert len(restored.attributes) == 3
        assert restored.products[0].product_id == "prod_full_001"
        assert restored.categories[0].category_id == "cat_root"

    def test_roundtrip_preserves_product_statuses(self):
        """Kiểm tra roundtrip giữ nguyên trạng thái sản phẩm."""
        output = full_catalog_recipe()
        d = output.ir.to_dict()
        restored = CatalogIR.from_dict(d)
        assert restored.products[0].status == ProductStatus.ACTIVE
        assert restored.products[1].status == ProductStatus.INACTIVE
        assert restored.products[2].status == ProductStatus.DRAFT
        assert restored.products[3].status == ProductStatus.ARCHIVED

    def test_roundtrip_preserves_category_hierarchy(self):
        """Kiểm tra roundtrip giữ nguyên phân cấp danh mục."""
        output = full_catalog_recipe()
        d = output.ir.to_dict()
        restored = CatalogIR.from_dict(d)
        cats = {c.category_id: c for c in restored.categories}
        assert cats["cat_root"].parent_id is None
        assert cats["cat_level1"].parent_id == "cat_root"
        assert cats["cat_level2"].parent_id == "cat_level1"
        assert cats["cat_level3"].parent_id == "cat_level2"
        assert cats["cat_level3_alt"].parent_id == "cat_level2"
