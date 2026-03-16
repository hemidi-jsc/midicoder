from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from .model_meta import ModelMeta


class EnumDef(BaseModel):
    id: str
    description: Optional[str] = None
    values: list[str]
    value_labels: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    source: Optional[str] = None

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="domain.enum",
        usage_en=(
            "Named enumeration of allowed values used by entities, value objects, commands and "
            "queries for constrained fields such as plan, status or role."
        ),
        included_by=[
            "domain.entity",
            "domain.value_object",
            "app.command",
            "app.query",
            "api.http_route",
        ],
        includes=[],
        real_world_examples=[
            "SubscriptionPlan enum for Free, Pro, Enterprise",
            "SubscriptionStatus enum for trial, active, past_due, cancelled",
            "UserRole enum for member, admin, owner",
            "InvoiceStatus enum for draft, issued, paid, void",
            "FeatureFlagState enum for enabled, disabled, rollout",
        ],
        visualizers=[
            "API documentation",
            "Admin configuration UIs",
        ],
    )


class EnumsFile(BaseModel):
    enums: list[EnumDef]

    model_config = {"extra": "forbid"}

