from __future__ import annotations

from typing import Any, ClassVar, Optional

from pydantic import BaseModel, Field

from .model_meta import ModelMeta
from .named_field_model import NamedField


QUERY_CATEGORY_CATALOG = {
    "list",
    "detail",
    "report",
    "search",
    "metrics",
}


class Query(BaseModel):
    id: str
    description: Optional[str] = None
    input: list[NamedField] = Field(default_factory=list)
    returns: list[NamedField] = Field(default_factory=list)
    reads: list[str] = Field(default_factory=list)
    filters: Optional[dict[str, Any]] = None
    pagination: Optional[dict[str, Any]] = None
    category: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    source: Optional[str] = None
    required_roles: list[str] = Field(default_factory=list)
    required_permissions: list[str] = Field(default_factory=list)
    reads_from: list[str] = Field(default_factory=list)
    datasource: Optional[str] = None

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="app.query",
        usage_en=(
            "Read-only application operation used to retrieve data for views, reports, dashboards "
            "or APIs without changing domain state."
        ),
        included_by=[
            "api.http_route",
            "api.graphql",
            "scenario.definition",
        ],
        includes=[
            "shared.named_field",
            "domain.entity",
        ],
        real_world_examples=[
            "ListUsers query for admin user management",
            "GetSubscription query for billing pages",
            "ListInvoices query for accounting exports",
            "SearchOrganizations query with filters and pagination",
            "UsageReport query for metered billing dashboards",
        ],
        visualizers=[
            "Reporting and BI tools",
            "API documentation",
        ],
    )


class QueriesFile(BaseModel):
    queries: list[Query]

    model_config = {"extra": "forbid"}

