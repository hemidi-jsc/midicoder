from __future__ import annotations

from typing import Any, ClassVar, Optional

from pydantic import BaseModel, Field, model_validator

from .model_meta import ModelMeta


SCENARIO_STEP_TYPE_CATALOG = {
    "command",
    "query",
    "event",
}


class ScenarioStep(BaseModel):
    type: str
    ref: str
    input: dict[str, Any] = Field(default_factory=dict)
    expect: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class Scenario(BaseModel):
    id: str
    description: Optional[str] = None
    actors: list[str] = Field(default_factory=list)
    actor_roles: list[str] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    steps: list[ScenarioStep] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source: Optional[str] = None

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def normalize_actor_roles(self) -> "Scenario":
        # Backward compatibility: legacy scenarios used `actors` to store role IDs.
        if not self.actor_roles and self.actors:
            self.actor_roles = list(self.actors)
        return self

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="scenario.definition",
        usage_en=(
            "End-to-end scenario describing actors, preconditions, steps and expectations used "
            "to validate contracts and flows across commands, queries and events."
        ),
        included_by=[],
        includes=[
            "app.command",
            "app.query",
            "domain.event",
            "policy.business",
            "policy.access",
            "workflow.definition",
        ],
        real_world_examples=[
            "New user signs up, verifies email and activates subscription",
            "Tenant admin invites a member and assigns roles",
            "Subscription payment fails and subscription moves to past_due",
            "Admin toggles a feature flag and users see new behavior",
            "Support agent resolves a ticket and triggers follow-up survey",
        ],
        visualizers=[
            "User journey maps",
            "Sequence diagrams",
        ],
    )


class ScenariosFile(BaseModel):
    scenarios: list[Scenario]

    model_config = {"extra": "forbid"}

