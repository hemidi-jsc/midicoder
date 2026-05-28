# coding: utf-8
"""
Mô-đun recipes cho CP50 — Catalog & Taxonomy Engine.

Cung cấp các recipe patterns để generate hệ thống catalog sản phẩm với
danh mục phân cấp, sản phẩm đa trạng thái, biến thể sản phẩm,
thuộc tính định nghĩa/giá trị, và cấu hình tìm kiếm.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass

from midicoder.packs.cp_full_catalog.models import (
    AttributeDefinition,
    AttributeType,
    AttributeValue,
    Category,
    Product,
    ProductStatus,
    ProductVariant,
)
from midicoder.packs.cp_full_catalog.parser import CatalogIR


@dataclass
class RecipeOutput:
    """Kết quả của recipe.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: CatalogIR kết quả
    """
    name: str
    description: str
    ir: CatalogIR


def basic_catalog_recipe() -> RecipeOutput:
    """Recipe: Catalog cơ bản — 2 danh mục, 2 sản phẩm, 1 thuộc tính, 1 biến thể.

    Tạo 2 danh mục phân cấp (root → sub), 2 sản phẩm (ACTIVE, DRAFT),
    1 định nghĩa thuộc tính color dạng ENUM với 3 lựa chọn, và
    1 biến thể cho sản phẩm ACTIVE. Không có kênh truyền thông,
    không có cấu hình xóa dữ liệu, use_search=True, use_audit=False.

    Phù hợp cho môi trường dev/prototyping khi cần catalog tối thiểu.

    Returns:
        RecipeOutput với cấu hình catalog cơ bản
    """
    categories = [
        Category(
            category_id="cat_root",
            name="Tất cả sản phẩm",
            description="Danh mục gốc chứa toàn bộ sản phẩm",
            parent_id=None,
            sort_order=0,
            icon="folder",
        ),
        Category(
            category_id="cat_sub",
            name="Áo thun",
            description="Danh mục áo thun các loại",
            parent_id="cat_root",
            sort_order=1,
            icon="tshirt",
        ),
    ]

    products = [
        Product(
            product_id="prod_001",
            name="Áo thun Basic",
            sku="TSHIRT-BASIC-001",
            description="Áo thun cotton 100% chất lượng cao",
            category_id="cat_sub",
            brand_id="brand_001",
            price=250000.0,
            cost_price=150000.0,
            compare_at_price=300000.0,
            currency="VND",
            weight=0.2,
            status=ProductStatus.ACTIVE,
            tags=["cotton", "basic", "unisex"],
            images=["https://example.com/images/tshirt-basic.jpg"],
            tenant_id="tenant_001",
        ),
        Product(
            product_id="prod_002",
            name="Áo thun Premium",
            sku="TSHIRT-PREM-002",
            description="Áo thun premium với chất liệu co giãn",
            category_id="cat_sub",
            brand_id="brand_001",
            price=450000.0,
            cost_price=280000.0,
            status=ProductStatus.DRAFT,
            tags=["premium", "stretch"],
            tenant_id="tenant_001",
        ),
    ]

    attribute_definitions = [
        AttributeDefinition(
            attribute_id="attr_color",
            name="Màu sắc",
            attribute_type=AttributeType.ENUM,
            is_required=False,
            options=["Đỏ", "Xanh", "Vàng"],
            is_searchable=True,
            is_filterable=True,
            is_visible=True,
            sort_order=1,
        ),
    ]

    variants = [
        ProductVariant(
            variant_id="var_001",
            product_id="prod_001",
            sku="TSHIRT-BASIC-001-RED",
            name="Áo thun Basic - Đỏ",
            attribute_values={"color": "Đỏ"},
            price=250000.0,
            cost_price=150000.0,
            weight=0.2,
            sort_order=1,
        ),
    ]

    return RecipeOutput(
        name="basic_catalog",
        description="2 danh mục (root → sub), 2 sản phẩm (active, draft), 1 thuộc tính color ENUM, 1 biến thể",
        ir=CatalogIR(
            categories=categories,
            products=products,
            variants=variants,
            attributes=attribute_definitions,
            attribute_values=[],
            use_search=True,
            use_audit=False,
        ),
    )


def full_catalog_recipe() -> RecipeOutput:
    """Recipe: Catalog đầy đủ — 5 danh mục phân cấp, 4 sản phẩm đa trạng thái, 2 biến thể, 3 thuộc tính.

    Tạo 5 danh mục phân cấp sâu (root → level1 → level2 → level3),
    4 sản phẩm với các trạng thái khác nhau (ACTIVE, INACTIVE, DRAFT, ARCHIVED),
    2 biến thể cho sản phẩm chính (kích thước M và L),
    3 định nghĩa thuộc tính (color ENUM, size ENUM, weight NUMBER),
    và giá trị thuộc tính gán cho từng sản phẩm. use_search=True, use_audit=False.

    Phù hợp cho môi trường production với đầy đủ tính năng catalog và phân loại.

    Returns:
        RecipeOutput với cấu hình catalog đầy đủ
    """
    categories = [
        Category(
            category_id="cat_root",
            name="Tất cả sản phẩm",
            description="Danh mục gốc của hệ thống catalog",
            parent_id=None,
            sort_order=0,
            icon="folder",
            descendant_count=4,
        ),
        Category(
            category_id="cat_level1",
            name="Thời trang",
            description="Danh mục thời trang nam nữ",
            parent_id="cat_root",
            sort_order=1,
            icon="shopping-bag",
            descendant_count=3,
        ),
        Category(
            category_id="cat_level2",
            name="Áo",
            description="Danh mục các loại áo",
            parent_id="cat_level1",
            sort_order=1,
            icon="tshirt",
            descendant_count=2,
        ),
        Category(
            category_id="cat_level3",
            name="Áo thun",
            description="Danh mục áo thun các loại và chất liệu",
            parent_id="cat_level2",
            sort_order=1,
            icon="tshirt-v",
            descendant_count=1,
        ),
        Category(
            category_id="cat_level3_alt",
            name="Áo sơ mi",
            description="Danh mục áo sơ mi công sở và casual",
            parent_id="cat_level2",
            sort_order=2,
            icon="shirt",
            descendant_count=0,
        ),
    ]

    products = [
        Product(
            product_id="prod_full_001",
            name="Áo thun Oversize",
            sku="TSHIRT-OVS-001",
            description="Áo thun oversize form rộng, cotton co giãn 4 chiều",
            category_id="cat_level3",
            brand_id="brand_001",
            price=350000.0,
            cost_price=200000.0,
            compare_at_price=420000.0,
            currency="VND",
            weight=0.3,
            dimensions={"length": 75.0, "width": 60.0, "height": 2.0},
            status=ProductStatus.ACTIVE,
            tags=["oversize", "cotton", "unisex", "bestseller"],
            seo_metadata={
                "title": "Áo thun Oversize - Chất liệu cotton cao cấp",
                "description": "Áo thun oversize form rộng, phù hợp nam nữ",
                "keywords": "áo thun, oversize, cotton, unisex",
            },
            images=[
                "https://example.com/images/tshirt-oversize-front.jpg",
                "https://example.com/images/tshirt-oversize-back.jpg",
            ],
            tenant_id="tenant_001",
        ),
        Product(
            product_id="prod_full_002",
            name="Áo thun Slim Fit",
            sku="TSHIRT-SF-002",
            description="Áo thun slim fit form bó gọn, chất liệu thun lạnh",
            category_id="cat_level3",
            brand_id="brand_002",
            price=280000.0,
            cost_price=170000.0,
            status=ProductStatus.INACTIVE,
            tags=["slim-fit", "thun-lanh"],
            tenant_id="tenant_001",
        ),
        Product(
            product_id="prod_full_003",
            name="Áo thun Vintage Wash",
            sku="TSHIRT-VW-003",
            description="Áo thun hiệu ứng Wash vintage, thiết kế retro",
            category_id="cat_level3",
            brand_id="brand_001",
            price=390000.0,
            cost_price=240000.0,
            status=ProductStatus.DRAFT,
            tags=["vintage", "wash", "retro"],
            tenant_id="tenant_001",
        ),
        Product(
            product_id="prod_full_004",
            name="Áo thun Classic 2023",
            sku="TSHIRT-CLS-004",
            description="Áo thun classic đã ngưng kinh doanh, thay thế bằng dòng 2024",
            category_id="cat_level3",
            brand_id="brand_001",
            price=250000.0,
            cost_price=150000.0,
            status=ProductStatus.ARCHIVED,
            tags=["classic", "2023", "discontinued"],
            tenant_id="tenant_001",
        ),
    ]

    variants = [
        ProductVariant(
            variant_id="var_full_001",
            product_id="prod_full_001",
            sku="TSHIRT-OVS-001-M",
            name="Áo thun Oversize - Size M",
            attribute_values={"size": "M"},
            price=350000.0,
            cost_price=200000.0,
            weight=0.3,
            barcode="8901234567890",
            images=["https://example.com/images/tshirt-oversize-m.jpg"],
            sort_order=1,
        ),
        ProductVariant(
            variant_id="var_full_002",
            product_id="prod_full_001",
            sku="TSHIRT-OVS-001-L",
            name="Áo thun Oversize - Size L",
            attribute_values={"size": "L"},
            price=360000.0,
            cost_price=210000.0,
            weight=0.35,
            barcode="8901234567891",
            images=["https://example.com/images/tshirt-oversize-l.jpg"],
            sort_order=2,
        ),
    ]

    attribute_definitions = [
        AttributeDefinition(
            attribute_id="attr_color",
            name="Màu sắc",
            attribute_type=AttributeType.ENUM,
            is_required=False,
            options=["Đỏ", "Xanh", "Vàng", "Đen", "Trắng"],
            is_searchable=True,
            is_filterable=True,
            is_visible=True,
            sort_order=1,
        ),
        AttributeDefinition(
            attribute_id="attr_size",
            name="Kích thước",
            attribute_type=AttributeType.ENUM,
            is_required=True,
            options=["XS", "S", "M", "L", "XL", "XXL"],
            is_searchable=True,
            is_filterable=True,
            is_visible=True,
            sort_order=2,
        ),
        AttributeDefinition(
            attribute_id="attr_weight",
            name="Trọng lượng",
            attribute_type=AttributeType.NUMBER,
            is_required=False,
            unit="kg",
            validation_rules={"min": 0.0, "max": 100.0},
            is_searchable=False,
            is_filterable=True,
            is_visible=True,
            sort_order=3,
        ),
    ]

    attribute_values = [
        # Giá trị thuộc tính cho prod_full_001 (Áo thun Oversize)
        AttributeValue(
            attribute_value_id="av_001",
            attribute_id="attr_color",
            product_id="prod_full_001",
            value="Đen",
        ),
        AttributeValue(
            attribute_value_id="av_002",
            attribute_id="attr_weight",
            product_id="prod_full_001",
            value=0.3,
        ),
        # Giá trị thuộc tính cho prod_full_002 (Áo thun Slim Fit)
        AttributeValue(
            attribute_value_id="av_003",
            attribute_id="attr_color",
            product_id="prod_full_002",
            value="Xanh",
        ),
        AttributeValue(
            attribute_value_id="av_004",
            attribute_id="attr_weight",
            product_id="prod_full_002",
            value=0.25,
        ),
        # Giá trị thuộc tính cho prod_full_003 (Áo thun Vintage Wash)
        AttributeValue(
            attribute_value_id="av_005",
            attribute_id="attr_color",
            product_id="prod_full_003",
            value="Vàng",
        ),
        AttributeValue(
            attribute_value_id="av_006",
            attribute_id="attr_size",
            product_id="prod_full_003",
            value="M",
        ),
    ]

    return RecipeOutput(
        name="full_catalog",
        description=(
            "5 danh mục phân cấp (root → level1 → level2 → level3), "
            "4 sản phẩm (active/inactive/draft/archived), "
            "2 biến thể (size M, L), 3 thuộc tính (color/size/weight), "
            "giá trị thuộc tính cho từng sản phẩm"
        ),
        ir=CatalogIR(
            categories=categories,
            products=products,
            variants=variants,
            attributes=attribute_definitions,
            attribute_values=attribute_values,
            use_search=True,
            use_audit=False,
        ),
    )


__all__ = [
    "RecipeOutput",
    "basic_catalog_recipe",
    "full_catalog_recipe",
]
