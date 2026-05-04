from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field, model_validator

from .model_meta import ModelMeta
from .named_field_model import NamedField

HTTP_METHOD_CATALOG = {
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "HEAD",
    "OPTIONS",
}


class HttpRoute(BaseModel):
    method: str
    path: str
    command: Optional[str] = None
    description: Optional[str] = None
    query: Optional[str] = None
    auth: Optional[str] = None
    request_schema: Optional[list[NamedField]] = None
    response_schema: Optional[list[NamedField]] = None
    deprecated: bool = False
    tags: list[str] = Field(default_factory=list)
    source: Optional[str] = None

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_target(self) -> "HttpRoute":
        has_command = bool((self.command or "").strip())
        has_query = bool((self.query or "").strip())
        if has_command == has_query:
            raise ValueError("Exactly one of 'command' or 'query' must be provided")
        return self

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="api.http_route",
        usage_en=(
            "HTTP route mapping an external REST endpoint to an underlying command or query, "
            "including authentication and request/response schema hints."
        ),
        included_by=["api.http_file"],
        includes=[
            "app.command",
            "app.query",
            "shared.named_field",
            "policy.access",
        ],
        real_world_examples=[
            "POST /api/v1/users mapped to CreateUser command",
            "POST /api/v1/auth/login mapped to Login command",
            "GET /api/v1/subscriptions mapped to ListSubscriptions query",
            "POST /api/v1/payments/webhook mapped to RecordPayment command",
            "GET /api/v1/feature-flags mapped to ListFeatureFlags query",
        ],
        visualizers=[
            "OpenAPI/Swagger UI",
            "API gateway consoles",
        ],
    )


class HttpApiFile(BaseModel):
    routes: list[HttpRoute]

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="api.http_file",
        usage_en=(
            "Collection of HTTP routes defining the REST surface area of a SaaS application, "
            "mapping endpoints to commands and queries."
        ),
        included_by=[],
        includes=["api.http_route"],
        real_world_examples=[
            "User and organization management REST API",
            "Billing and subscription HTTP API",
            "Admin REST API for configuration and feature flags",
            "Webhook endpoints for external providers",
            "Reporting and analytics endpoints",
        ],
        visualizers=[
            "OpenAPI/Swagger UI",
            "API gateway consoles",
        ],
    )
