from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from .model_meta import ModelMeta
from .named_field_model import NamedField

EVENT_KIND_CATALOG = {
    "domain",
    "integration",
    "audit",
}


class EventDef(BaseModel):
    id: str
    description: Optional[str] = None
    kind: Optional[str] = "domain"
    payload: list[NamedField] = Field(default_factory=list)
    source: Optional[str] = None
    tags: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="domain.event",
        usage_en=(
            "Domain event describing something that happened in the system, used for workflows, "
            "projections, audit trails and external integrations."
        ),
        included_by=[
            "app.command",
            "app.projection",
            "workflow.definition",
            "scenario.definition",
        ],
        includes=["shared.named_field"],
        real_world_examples=[
            "UserRegistered event after a successful sign up",
            "SubscriptionActivated when payment succeeds",
            "InvoicePaid when invoice is fully paid",
            "PasswordResetRequested for security flows",
            "FeatureFlagToggled for experimentation tracking",
        ],
        visualizers=[
            "Event storming boards",
            "Sequence diagrams",
            "Log and audit dashboards",
        ],
    )


class EventsFile(BaseModel):
    events: list[EventDef]

    model_config = {"extra": "forbid"}
