from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from .model_meta import ModelMeta


ERROR_CATEGORY_CATALOG = {
    "validation",
    "business",
    "security",
    "system",
    "integration",
}


class ErrorDef(BaseModel):
    id: str
    description: Optional[str] = None
    category: Optional[str] = "business"
    http_status: Optional[int] = None
    code: Optional[str] = None
    source: Optional[str] = None
    tags: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="domain.error",
        usage_en=(
            "Structured error definition used by commands, workflows and API responses to "
            "describe business, validation, security or system failures."
        ),
        included_by=[
            "app.command",
            "workflow.definition",
            "api.http_route",
            "scenario.definition",
        ],
        includes=[],
        real_world_examples=[
            "UserAlreadyExists when registering with an existing email",
            "SubscriptionExpired when accessing a protected feature",
            "PaymentFailed for billing integrations",
            "UnauthorizedAccess for security violations",
            "InvalidInput for failed validations on commands",
        ],
        visualizers=[
            "API error catalogs",
            "Monitoring and alerting dashboards",
        ],
    )


class ErrorsFile(BaseModel):
    errors: list[ErrorDef]

    model_config = {"extra": "forbid"}
