# coding: utf-8
"""
CP50 — Catalog & Taxonomy Engine Pack.

Public API barrel export.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from midicoder.packs.cp50_catalog.models import (
    AttributeDefinition,
    AttributeType,
    AttributeValue,
    Category,
    CategoryLevel,
    CatalogEngine,
    Product,
    ProductStatus,
    ProductVariant,
    SortOrder,
    Visibility,
)
from midicoder.packs.cp50_catalog.parser import (
    CatalogIR,
    parse_attribute_definitions,
    parse_attribute_values,
    parse_categories,
    parse_products,
    parse_to_ir,
    parse_variants,
)
from midicoder.packs.cp50_catalog.recipes import (
    RecipeOutput,
    basic_catalog_recipe,
    full_catalog_recipe,
)
from midicoder.packs.cp50_catalog.fastapi import (
    FastAPICatalogEmitter,
)
from midicoder.packs.cp50_catalog.nestjs import (
    NestJSCatalogEmitter,
)
from midicoder.packs.cp50_catalog.angular import (
    AngularCatalogEmitter,
)
from midicoder.packs.cp50_catalog.react import (
    ReactCatalogEmitter,
)

__all__ = [
    # Models - Enums
    "ProductStatus",
    "AttributeType",
    "SortOrder",
    "Visibility",
    "CategoryLevel",
    # Models - Core
    "Product",
    "Category",
    "ProductVariant",
    "AttributeDefinition",
    "AttributeValue",
    # Models - Engine
    "CatalogEngine",
    # Parser
    "CatalogIR",
    "parse_products",
    "parse_categories",
    "parse_variants",
    "parse_attribute_definitions",
    "parse_attribute_values",
    "parse_to_ir",
    # Recipes
    "RecipeOutput",
    "basic_catalog_recipe",
    "full_catalog_recipe",
    # Emitters
    "FastAPICatalogEmitter",
    "NestJSCatalogEmitter",
    "AngularCatalogEmitter",
    "ReactCatalogEmitter",
]
