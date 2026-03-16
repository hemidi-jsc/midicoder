from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from .model_meta import ModelMeta
from .named_field_model import NamedField


class Index(BaseModel):
    name: str
    fields: list[str]
    unique: bool = False

    model_config = {"extra": "forbid"}


class Constraint(BaseModel):
    type: str
    fields: list[str] = Field(default_factory=list)
    ref: Optional[str] = None

    model_config = {"extra": "forbid"}


CONSTRAINT_TYPE_CATALOG = {
    "unique",
    "check",
    "foreign_key",
}

TENANT_SCOPE_CATALOG = {
    "global",
    "tenant",
    "user",
}


class Entity(BaseModel):
    id: str
    description: Optional[str] = None
    fields: list[NamedField]
    primary_key: Optional[str] = "id"
    indexes: list[Index] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source: Optional[str] = None
    tenant_scope: Optional[str] = None

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="domain.entity",
        usage_en=(
            "Structured domain data model representing a core business concept such as user, "
            "organization, subscription or invoice in a SaaS platform."
        ),
        included_by=[
            "app.command",
            "app.query",
            "app.projection",
            "workflow.definition",
            "policy.business",
            "policy.access",
            "scenario.definition",
        ],
        includes=["shared.named_field"],
        real_world_examples=[
            "User profile for multi-tenant user management",
            "Organization or workspace entity for B2B SaaS",
            "Subscription entity for billing and lifecycle",
            "Invoice entity for payments and accounting",
            "FeatureFlag entity for feature rollout control",
        ],
        visualizers=[
            "dbdiagram.io",
            "Mermaid ERD",
            "Relational database schema viewers",
        ],
    )


class EntitiesFile(BaseModel):
    entities: list[Entity]

    model_config = {"extra": "forbid"}
