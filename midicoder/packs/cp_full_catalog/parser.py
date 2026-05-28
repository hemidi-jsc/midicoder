# coding: utf-8
"""
Mô-đun parser cho CP50 — Catalog & Taxonomy Engine.

Parse DSL dict (từ contract YAML) sang CatalogIR — Intermediate Representation
cho sản phẩm, danh mục phân loại, biến thể sản phẩm, định nghĩa thuộc tính,
và giá trị thuộc tính.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

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


@dataclass
class CatalogIR:
    """Intermediate Representation cho CP50.

    Gom tập tất cả dữ liệu catalog từ DSL, bao gồm
    danh sách sản phẩm, danh mục phân loại, biến thể sản phẩm,
    định nghĩa thuộc tính, và giá trị thuộc tính.

    Attributes:
        products: Danh sách sản phẩm trong catalog
        categories: Danh sách danh mục phân loại
        variants: Danh sách biến thể sản phẩm
        attributes: Danh sách định nghĩa thuộc tính
        attribute_values: Danh sách giá trị thuộc tính
        use_search: Có sử dụng tích hợp tìm kiếm không
        use_audit: Có sử dụng tích hợp audit (CP14) không
    """
    products: list[Product] = field(default_factory=list)
    categories: list[Category] = field(default_factory=list)
    variants: list[ProductVariant] = field(default_factory=list)
    attributes: list[AttributeDefinition] = field(default_factory=list)
    attribute_values: list[AttributeValue] = field(default_factory=list)
    use_search: bool = True
    use_audit: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Chuyển CatalogIR sang dict để xuất JSON."""
        return {
            "products": [p.to_dict() for p in self.products],
            "categories": [c.to_dict() for c in self.categories],
            "variants": [v.to_dict() for v in self.variants],
            "attributes": [a.to_dict() for a in self.attributes],
            "attribute_values": [av.to_dict() for av in self.attribute_values],
            "use_search": self.use_search,
            "use_audit": self.use_audit,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CatalogIR":
        """Tạo CatalogIR từ dict."""
        products = [Product.from_dict(p) for p in data.get("products", [])]
        categories = [Category.from_dict(c) for c in data.get("categories", [])]
        variants = [ProductVariant.from_dict(v) for v in data.get("variants", [])]
        attributes = [AttributeDefinition.from_dict(a) for a in data.get("attributes", [])]
        attribute_values = [AttributeValue.from_dict(av) for av in data.get("attribute_values", [])]
        return cls(
            products=products,
            categories=categories,
            variants=variants,
            attributes=attributes,
            attribute_values=attribute_values,
            use_search=data.get("use_search", True),
            use_audit=data.get("use_audit", False),
        )


def parse_products(data: dict[str, Any]) -> list[Product]:
    """Parse danh sách sản phẩm từ DSL dict.

    Hỗ trợ key chính 'products' và key alias 'catalog'.
    Xử lý field aliases: 'id' → 'product_id', 'cat_id' → 'category_id'.
    Chuyển đổi enum từ chuỗi: 'status' → ProductStatus, 'visibility' → Visibility.

    Args:
        data: DSL dict với key 'products' hoặc 'catalog'

    Returns:
        Danh sách Product đã parse
    """
    raw = data.get("products", data.get("catalog", []))

    if not raw or not isinstance(raw, list):
        return []

    products = []
    for item in raw:
        if not isinstance(item, dict):
            continue

        status_value = item.get("status", "draft")
        visibility_value = item.get("visibility", "public")

        products.append(Product(
            product_id=item.get("product_id", item.get("id", "")),
            name=item.get("name", ""),
            slug=item.get("slug", ""),
            sku=item.get("sku", ""),
            description=item.get("description", ""),
            category_id=item.get("category_id", item.get("cat_id", "")),
            brand_id=item.get("brand_id", item.get("brand", "")),
            price=float(item.get("price", 0.0)),
            cost_price=float(item.get("cost_price", 0.0)),
            compare_at_price=float(item.get("compare_at_price", 0.0)),
            currency=item.get("currency", "VND"),
            weight=float(item.get("weight", 0.0)),
            dimensions=item.get("dimensions", {}),
            status=ProductStatus(status_value) if isinstance(status_value, str) else status_value,
            visibility=Visibility(visibility_value) if isinstance(visibility_value, str) else visibility_value,
            tags=item.get("tags", []),
            seo_metadata=item.get("seo_metadata", {}),
            images=item.get("images", []),
            metadata=item.get("metadata", {}),
            is_deleted=item.get("is_deleted", False),
            tenant_id=item.get("tenant_id", item.get("tenant", "")),
        ))
    return products


def parse_categories(data: dict[str, Any]) -> list[Category]:
    """Parse danh sách danh mục phân loại từ DSL dict.

    Hỗ trợ key chính 'categories' và key alias 'taxonomy'.
    Xử lý field aliases: 'id' → 'category_id', 'cat_id' → 'category_id',
    'parent' → 'parent_id'.

    Args:
        data: DSL dict với key 'categories' hoặc 'taxonomy'

    Returns:
        Danh sách Category đã parse
    """
    raw = data.get("categories", data.get("taxonomy", []))

    if not raw or not isinstance(raw, list):
        return []

    categories = []
    for item in raw:
        if not isinstance(item, dict):
            continue

        parent = item.get("parent_id", item.get("parent", None))

        categories.append(Category(
            category_id=item.get("category_id", item.get("cat_id", item.get("id", ""))),
            name=item.get("name", ""),
            slug=item.get("slug", ""),
            description=item.get("description", ""),
            parent_id=parent if parent else None,
            sort_order=item.get("sort_order", 0),
            icon=item.get("icon", ""),
            is_active=item.get("is_active", True),
            descendant_count=item.get("descendant_count", 0),
            metadata=item.get("metadata", {}),
        ))
    return categories


def parse_variants(data: dict[str, Any]) -> list[ProductVariant]:
    """Parse danh sách biến thể sản phẩm từ DSL dict.

    Hỗ trợ key chính 'variants'.
    Xử lý field aliases: 'id' → 'variant_id', 'product' → 'product_id'.

    Args:
        data: DSL dict với key 'variants'

    Returns:
        Danh sách ProductVariant đã parse
    """
    raw = data.get("variants", [])

    if not raw or not isinstance(raw, list):
        return []

    variants = []
    for item in raw:
        if not isinstance(item, dict):
            continue

        variants.append(ProductVariant(
            variant_id=item.get("variant_id", item.get("id", "")),
            product_id=item.get("product_id", item.get("product", "")),
            sku=item.get("sku", ""),
            name=item.get("name", ""),
            attribute_values=item.get("attribute_values", {}),
            price=float(item.get("price", 0.0)),
            cost_price=float(item.get("cost_price", 0.0)),
            weight=float(item.get("weight", 0.0)),
            barcode=item.get("barcode", ""),
            images=item.get("images", []),
            is_active=item.get("is_active", True),
            sort_order=item.get("sort_order", 0),
            metadata=item.get("metadata", {}),
        ))
    return variants


def parse_attribute_definitions(data: dict[str, Any]) -> list[AttributeDefinition]:
    """Parse danh sách định nghĩa thuộc tính từ DSL dict.

    Hỗ trợ key chính 'attribute_definitions' và key alias 'attributes'.
    Xử lý field aliases: 'id' → 'attribute_id', 'type' → 'attribute_type'.
    Chuyển đổi enum từ chuỗi: 'attribute_type' → AttributeType.

    Args:
        data: DSL dict với key 'attribute_definitions' hoặc 'attributes'

    Returns:
        Danh sách AttributeDefinition đã parse
    """
    raw = data.get("attribute_definitions", data.get("attributes", []))

    if not raw or not isinstance(raw, list):
        return []

    attributes = []
    for item in raw:
        if not isinstance(item, dict):
            continue

        type_value = item.get("attribute_type", item.get("type", "string"))

        attributes.append(AttributeDefinition(
            attribute_id=item.get("attribute_id", item.get("id", "")),
            name=item.get("name", ""),
            key=item.get("key", ""),
            attribute_type=AttributeType(type_value) if isinstance(type_value, str) else type_value,
            is_required=item.get("is_required", False),
            validation_rules=item.get("validation_rules", {}),
            options=item.get("options", []),
            unit=item.get("unit", ""),
            is_searchable=item.get("is_searchable", False),
            is_filterable=item.get("is_filterable", False),
            is_visible=item.get("is_visible", True),
            sort_order=item.get("sort_order", 0),
            metadata=item.get("metadata", {}),
        ))
    return attributes


def parse_attribute_values(data: dict[str, Any]) -> list[AttributeValue]:
    """Parse danh sách giá trị thuộc tính từ DSL dict.

    Hỗ trợ key chính 'attribute_values'.
    Xử lý field aliases: 'id' → 'attribute_value_id', 'attr_id' → 'attribute_id'.

    Args:
        data: DSL dict với key 'attribute_values'

    Returns:
        Danh sách AttributeValue đã parse
    """
    raw = data.get("attribute_values", [])

    if not raw or not isinstance(raw, list):
        return []

    attribute_values = []
    for item in raw:
        if not isinstance(item, dict):
            continue

        attribute_values.append(AttributeValue(
            attribute_value_id=item.get("attribute_value_id", item.get("id", "")),
            attribute_id=item.get("attribute_id", item.get("attr_id", "")),
            product_id=item.get("product_id", item.get("product", "")),
            variant_id=item.get("variant_id", item.get("variant", "")),
            value=item.get("value", None),
        ))
    return attribute_values


def parse_to_ir(data: dict[str, Any]) -> CatalogIR:
    """Parse DSL dict thành CatalogIR.

    Gom tập tất cả các thành phần: products, categories, variants,
    attribute definitions, attribute values, và các flags tích hợp
    search/audit.

    Args:
        data: DSL dict với products, categories, variants,
            attribute_definitions, attribute_values

    Returns:
        CatalogIR gom tập tất cả parsed data
    """
    products = parse_products(data)
    categories = parse_categories(data)
    variants = parse_variants(data)
    attributes = parse_attribute_definitions(data)
    attribute_values = parse_attribute_values(data)

    return CatalogIR(
        products=products,
        categories=categories,
        variants=variants,
        attributes=attributes,
        attribute_values=attribute_values,
        use_search=data.get("use_search", True),
        use_audit=data.get("use_audit", False),
    )


__all__ = [
    "CatalogIR",
    "parse_products",
    "parse_categories",
    "parse_variants",
    "parse_attribute_definitions",
    "parse_attribute_values",
    "parse_to_ir",
]
