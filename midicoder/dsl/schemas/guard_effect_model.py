from __future__ import annotations

from typing import Any, ClassVar

from pydantic import BaseModel, model_validator

from .integration_model import IntegrationOperationRefStr, IntegrationRefStr
from .model_meta import ModelMeta


class GuardRef(BaseModel):
    id: str
    params: dict[str, Any] | None = None

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="shared.guard_ref",
        usage_en=(
            "Reference to a reusable guard condition (precondition) that can be attached to "
            "commands, workflows or policies before executing business logic."
        ),
        included_by=[
            "app.command",
            "workflow.definition",
            "policy.business",
            "scenario.definition",
        ],
        includes=[],
        real_world_examples=[
            "auth.role guard ensuring only admins can perform an action",
            "auth.permission guard checking fine-grained permissions",
            "ownership guard ensuring user owns the resource",
            "state.equals guard enforcing workflow state transitions",
            "quota.limit guard enforcing per-tenant usage limits",
        ],
        visualizers=[
            "Rule/decision table viewers",
            "Policy visualization tools",
        ],
    )


class EffectRef(BaseModel):
    id: str
    params: dict[str, Any] | None = None

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_effect_params(self) -> "EffectRef":
        # Keep params as dict for downstream compatibility, but enforce typed payload
        # for call.integration so operation/target refs are validated at schema time.
        if self.id == "call.integration":
            payload = IntegrationCallParams.model_validate(self.params or {})
            self.params = payload.model_dump(exclude_none=True)
        return self

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="shared.effect_ref",
        usage_en=(
            "Reference to a reusable side-effect that can be attached to commands or workflows "
            "to persist changes, emit events or call external systems."
        ),
        included_by=[
            "app.command",
            "workflow.definition",
            "scenario.definition",
        ],
        includes=[],
        real_world_examples=[
            "db.insert effect to create a new record",
            "db.update effect to modify existing data",
            "emit.event effect to publish domain events",
            "call.integration effect to call external APIs",
            "send.notification effect to notify users",
        ],
        visualizers=[
            "Sequence diagrams",
            "Event-driven architecture diagrams",
        ],
    )


GUARD_CATALOG = {
    "auth.role",
    "auth.permission",
    "ownership",
    "state.equals",
    "state.in",
    "exists",
    "not_exists",
    "quota.limit",
    "feature.enabled",
    "tenant.active",
    "subscription.active",
}


EFFECT_CATALOG = {
    "db.insert",
    "db.update",
    "db.delete",
    "db.upsert",
    "emit.event",
    "call.integration",
    "send.email",
    "send.notification",
    "schedule.job",
    "cache.invalidate",
}


class IntegrationCallParams(BaseModel):
    target: IntegrationRefStr | None = None
    integration: IntegrationRefStr | None = None
    service: str | None = None
    operation_id: IntegrationOperationRefStr | None = None
    payload: dict[str, Any] | None = None

    model_config = {"extra": "allow"}

    @model_validator(mode="after")
    def validate_target_presence(self) -> "IntegrationCallParams":
        if not any((self.target, self.integration, self.service)):
            raise ValueError(
                "call.integration requires one of 'target', 'integration', or 'service'"
            )
        return self
