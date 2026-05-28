# coding: utf-8
"""
Mô-đun recipes cho CP57 — GraphQL Schema Federation.

Cung cấp các recipe để build GraphQLIR cho các use case phổ biến:
- basic_federation_recipe: Single service với @key directive
- multi_service_recipe: 2 services (User + Product) với gateway
- full_federation_recipe: 3+ services, gateway, persisted queries

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp_backend_graphql_federation.parser import (
    GraphQLIR,
    parse_to_ir,
)


@dataclass
class RecipeOutput:
    """Kết quả từ recipe builder.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: GraphQLIR đã build
        raw_data: Raw DSL dict
    """
    name: str
    description: str
    ir: GraphQLIR
    raw_data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RecipeOutput sang dict."""
        return {
            "name": self.name,
            "description": self.description,
            "ir": self.ir.to_dict(),
            "raw_data": self.raw_data,
        }


def basic_federation_recipe() -> RecipeOutput:
    """Recipe: Cấu hình federation cơ bản — single service.

    - 1 service (User Service)
    - 1 federated type (User) với @key directive
    - Không có gateway (single service mode)

    Returns:
        RecipeOutput chứa GraphQLIR
    """
    data = {
        "services": [
            {
                "id": "user-service",
                "name": "User Service",
                "url": "http://localhost:4001",
                "schema_path": "./graphql/schema.graphql",
                "port": 4001,
                "entity_ownerships": ["User"],
            }
        ],
        "types": [
            {
                "id": "User",
                "name": "User",
                "key_fields": ["id"],
                "owning_service": "user-service",
                "fields": [
                    {
                        "id": "User.id",
                        "name": "id",
                        "type_str": "ID!",
                    },
                    {
                        "id": "User.email",
                        "name": "email",
                        "type_str": "String!",
                    },
                    {
                        "id": "User.name",
                        "name": "name",
                        "type_str": "String!",
                    },
                ],
            }
        ],
        "resolvers": [
            {
                "id": "User.resolveReference",
                "entity_type": "User",
                "resolve_reference_query": "query { user(id: $id) { id email name } }",
                "resolve_reference_service": "user-service",
            }
        ],
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="basic_federation_recipe",
        description="GraphQL Federation cơ bản — single service với @key directive",
        ir=ir,
        raw_data=data,
    )


def multi_service_recipe() -> RecipeOutput:
    """Recipe: Federation với 2 services và gateway aggregation.

    - 2 services: User Service + Product Service
    - Federated types: User (owned by user-service), Product (owned by product-service)
    - Gateway config với CORS và rate limiting cơ bản
    - User type được extend bởi product-service (orders field)

    Returns:
        RecipeOutput chứa GraphQLIR
    """
    data = {
        "services": [
            {
                "id": "user-service",
                "name": "User Service",
                "url": "http://localhost:4001",
                "schema_path": "./graphql/user-schema.graphql",
                "port": 4001,
                "entity_ownerships": ["User"],
            },
            {
                "id": "product-service",
                "name": "Product Service",
                "url": "http://localhost:4002",
                "schema_path": "./graphql/product-schema.graphql",
                "port": 4002,
                "entity_ownerships": ["Product"],
            },
        ],
        "types": [
            {
                "id": "User",
                "name": "User",
                "key_fields": ["id"],
                "owning_service": "user-service",
                "extensions": ["product-service"],
                "fields": [
                    {
                        "id": "User.id",
                        "name": "id",
                        "type_str": "ID!",
                    },
                    {
                        "id": "User.email",
                        "name": "email",
                        "type_str": "String!",
                    },
                    {
                        "id": "User.name",
                        "name": "name",
                        "type_str": "String!",
                    },
                ],
            },
            {
                "id": "Product",
                "name": "Product",
                "key_fields": ["id"],
                "owning_service": "product-service",
                "fields": [
                    {
                        "id": "Product.id",
                        "name": "id",
                        "type_str": "ID!",
                    },
                    {
                        "id": "Product.title",
                        "name": "title",
                        "type_str": "String!",
                    },
                    {
                        "id": "Product.price",
                        "name": "price",
                        "type_str": "Float!",
                    },
                ],
            },
        ],
        "resolvers": [
            {
                "id": "User.resolveReference",
                "entity_type": "User",
                "resolve_reference_query": "query { user(id: $id) { id email name } }",
                "resolve_reference_service": "user-service",
            },
            {
                "id": "Product.resolveReference",
                "entity_type": "Product",
                "resolve_reference_query": "query { product(id: $id) { id title price } }",
                "resolve_reference_service": "product-service",
            },
        ],
        "gateway_config": {
            "id": "apollo-gateway",
            "persisted_queries_enabled": False,
            "introspection_enabled": True,
            "cors_origins": ["http://localhost:3000"],
            "rate_limit_rps": 100,
        },
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="multi_service_recipe",
        description="GraphQL Federation — 2 services (User + Product) với gateway aggregation",
        ir=ir,
        raw_data=data,
    )


def full_federation_recipe() -> RecipeOutput:
    """Recipe: Federation đầy đủ — 3+ services, gateway, persisted queries.

    - 3 services: User Service, Product Service, Order Service
    - Federated types: User, Product, Order (cross-service references)
    - Gateway config đầy đủ: persisted queries, CORS, rate limiting
    - Introspection disabled (production mode)
    - Order type reference cả User và Product

    Returns:
        RecipeOutput chứa GraphQLIR
    """
    data = {
        "services": [
            {
                "id": "user-service",
                "name": "User Service",
                "url": "http://localhost:4001",
                "schema_path": "./graphql/user-schema.graphql",
                "health_check": "/health",
                "port": 4001,
                "entity_ownerships": ["User"],
            },
            {
                "id": "product-service",
                "name": "Product Service",
                "url": "http://localhost:4002",
                "schema_path": "./graphql/product-schema.graphql",
                "health_check": "/health",
                "port": 4002,
                "entity_ownerships": ["Product"],
            },
            {
                "id": "order-service",
                "name": "Order Service",
                "url": "http://localhost:4003",
                "schema_path": "./graphql/order-schema.graphql",
                "health_check": "/health",
                "port": 4003,
                "entity_ownerships": ["Order"],
            },
        ],
        "types": [
            {
                "id": "User",
                "name": "User",
                "key_fields": ["id"],
                "owning_service": "user-service",
                "extensions": ["order-service"],
                "fields": [
                    {"id": "User.id", "name": "id", "type_str": "ID!"},
                    {"id": "User.email", "name": "email", "type_str": "String!"},
                    {"id": "User.name", "name": "name", "type_str": "String!"},
                ],
            },
            {
                "id": "Product",
                "name": "Product",
                "key_fields": ["id"],
                "owning_service": "product-service",
                "extensions": ["order-service"],
                "fields": [
                    {"id": "Product.id", "name": "id", "type_str": "ID!"},
                    {"id": "Product.title", "name": "title", "type_str": "String!"},
                    {"id": "Product.price", "name": "price", "type_str": "Float!"},
                ],
            },
            {
                "id": "Order",
                "name": "Order",
                "key_fields": ["id"],
                "owning_service": "order-service",
                "fields": [
                    {"id": "Order.id", "name": "id", "type_str": "ID!"},
                    {"id": "Order.user", "name": "user", "type_str": "User!", "resolve_reference": True},
                    {"id": "Order.product", "name": "product", "type_str": "Product!", "resolve_reference": True},
                    {"id": "Order.quantity", "name": "quantity", "type_str": "Int!"},
                    {"id": "Order.status", "name": "status", "type_str": "String!"},
                ],
            },
        ],
        "resolvers": [
            {
                "id": "User.resolveReference",
                "entity_type": "User",
                "resolve_reference_query": "query { user(id: $id) { id email name } }",
                "resolve_reference_service": "user-service",
            },
            {
                "id": "Product.resolveReference",
                "entity_type": "Product",
                "resolve_reference_query": "query { product(id: $id) { id title price } }",
                "resolve_reference_service": "product-service",
            },
            {
                "id": "Order.resolveReference",
                "entity_type": "Order",
                "resolve_reference_query": "query { order(id: $id) { id quantity status } }",
                "resolve_reference_service": "order-service",
            },
        ],
        "gateway_config": {
            "id": "apollo-gateway",
            "persisted_queries_enabled": True,
            "introspection_enabled": False,
            "cors_origins": ["http://localhost:3000", "https://app.example.com"],
            "rate_limit_rps": 500,
        },
    }

    ir = parse_to_ir(data)

    return RecipeOutput(
        name="full_federation_recipe",
        description="GraphQL Federation đầy đủ — 3 services, gateway, persisted queries, cross-service references",
        ir=ir,
        raw_data=data,
    )


__all__ = [
    "RecipeOutput",
    "basic_federation_recipe",
    "multi_service_recipe",
    "full_federation_recipe",
]
