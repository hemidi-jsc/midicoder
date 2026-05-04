from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from .model_meta import ModelMeta
from .named_field_model import NamedField


class Projection(BaseModel):
    id: str
    description: Optional[str] = None
    source_events: list[str] = Field(default_factory=list)
    fields: list[NamedField] = Field(default_factory=list)
    storage: Optional[str] = None
    storage_kind: Optional[str] = None
    storage_ref: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    source: Optional[str] = None

    model_config = {"extra": "ignore"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="app.projection",
        usage_en=(
            "Read model built from one or more domain events, optimized for queries, reporting "
            "or external integrations."
        ),
        included_by=[
            "app.query",
            "api.http_route",
            "api.graphql",
        ],
        includes=[
            "domain.event",
            "shared.named_field",
        ],
        real_world_examples=[
            "UserSubscriptionProjection aggregating subscription and billing status",
            "InvoiceSummaryProjection for fast invoice listings",
            "UsageAggregationProjection for metered billing reports",
            "AuditLogProjection for security and compliance views",
            "FeatureFlagExposureProjection for experimentation analytics",
        ],
        visualizers=[
            "Analytics dashboards",
            "Reporting tools",
        ],
    )


class ProjectionsFile(BaseModel):
    projections: list[Projection]

    model_config = {"extra": "forbid"}
