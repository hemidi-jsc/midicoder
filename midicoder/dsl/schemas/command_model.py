from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from .guard_effect_model import EffectRef, GuardRef
from .model_meta import ModelMeta
from .named_field_model import NamedField

COMMAND_CATEGORY_CATALOG = {
    "crud.create",
    "crud.update",
    "crud.delete",
    "crud.read",
    "auth.login",
    "auth.logout",
    "billing.charge",
    "billing.refund",
    "subscription.activate",
    "subscription.cancel",
    "subscription.change_plan",
    "workflow.transition",
    "notification.send",
}

TENANT_SCOPE_CATALOG = {
    "global",
    "tenant",
    "user",
}


class Command(BaseModel):
    id: str
    description: Optional[str] = None
    input: list[NamedField]
    fetches: list[str] = Field(default_factory=list)
    guards: list[GuardRef] = Field(default_factory=list)
    effects: list[EffectRef] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    returns: list[NamedField] = Field(default_factory=list)
    category: Optional[str] = None
    emits: list[str] = Field(default_factory=list)
    required_roles: list[str] = Field(default_factory=list)
    required_permissions: list[str] = Field(default_factory=list)
    writes_to: list[str] = Field(default_factory=list)
    datasource: Optional[str] = None
    transaction: Optional[bool] = None
    tenant_scope: Optional[str] = None
    source: Optional[str] = None
    tags: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="app.command",
        usage_en=(
            "Application-level operation that changes state or triggers side effects, typically "
            "mapped from API endpoints or UI actions in a SaaS application."
        ),
        included_by=[
            "api.http_route",
            "api.graphql",
            "workflow.definition",
            "policy.business",
            "scenario.definition",
        ],
        includes=[
            "shared.named_field",
            "shared.guard_ref",
            "shared.effect_ref",
            "domain.entity",
            "domain.error",
            "domain.event",
        ],
        real_world_examples=[
            "CreateUser to register a new account",
            "AssignSubscription to attach a plan to a user",
            "CancelSubscription to stop billing and access",
            "RecordPayment to persist billing provider callbacks",
            "InviteMember to add a user to an organization",
        ],
        visualizers=[
            "API documentation (OpenAPI/Swagger)",
            "Sequence diagrams of application flows",
        ],
    )


class CommandsFile(BaseModel):
    commands: list[Command]

    model_config = {"extra": "forbid"}
