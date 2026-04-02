from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from .model_meta import ModelMeta
from .named_field_model import NamedField

VALUE_OBJECT_CATEGORY_CATALOG = {
    "money",
    "address",
    "period",
    "geo",
    "contact",
}


class ValueObject(BaseModel):
    id: str
    description: Optional[str] = None
    fields: list[NamedField]
    category: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    source: Optional[str] = None

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="domain.value_object",
        usage_en=(
            "Small immutable data structure that is always interpreted by its values, such as "
            "money, address, period or contact information in a SaaS domain."
        ),
        included_by=[
            "domain.entity",
            "app.command",
            "app.query",
            "app.projection",
        ],
        includes=["shared.named_field"],
        real_world_examples=[
            "Money value object for currency and amount",
            "PostalAddress for shipping and billing details",
            "BillingPeriod for subscription cycles",
            "GeoLocation for tracking locations",
            "ContactInfo for user and organization contacts",
        ],
        visualizers=[
            "ERD diagrams",
            "API documentation",
        ],
    )


class ValueObjectsFile(BaseModel):
    value_objects: list[ValueObject]

    model_config = {"extra": "forbid"}
