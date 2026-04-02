from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from .model_meta import ModelMeta
from .named_field_model import NamedField


GRAPHQL_TYPE_KIND_CATALOG = {
    "object",
    "interface",
    "enum",
    "scalar",
}


class GraphQLType(BaseModel):
    name: str
    kind: Optional[str] = None
    fields: list[NamedField] = Field(default_factory=list)
    description: Optional[str] = None

    model_config = {"extra": "forbid"}


class GraphQLField(BaseModel):
    name: str
    resolver: str
    args: list[NamedField] = Field(default_factory=list)
    returns: list[NamedField] = Field(default_factory=list)
    description: Optional[str] = None

    model_config = {"extra": "forbid"}


class GraphQLApi(BaseModel):
    types: list[GraphQLType] = Field(default_factory=list)
    queries: list[GraphQLField] = Field(default_factory=list)
    mutations: list[GraphQLField] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="api.graphql",
        usage_en=(
            "GraphQL API surface mapping queries and mutations to underlying commands and "
            "queries, with types aligned to the domain schema."
        ),
        included_by=[],
        includes=[
            "app.command",
            "app.query",
            "shared.named_field",
        ],
        real_world_examples=[
            "GraphQL API for user and organization management",
            "GraphQL API for subscription and billing data",
            "GraphQL API for analytics dashboards",
            "GraphQL API for configuration and feature flags",
            "GraphQL API for developer-focused integrations",
        ],
        visualizers=[
            "GraphQL playgrounds",
            "Schema visualization tools",
        ],
    )


class GraphQLApiFile(BaseModel):
    api: GraphQLApi

    model_config = {"extra": "forbid"}
