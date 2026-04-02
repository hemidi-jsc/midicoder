from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from .guard_effect_model import EffectRef, GuardRef
from .model_meta import ModelMeta


WORKFLOW_STATE_KIND_CATALOG = {
    "initial",
    "normal",
    "final",
}


class WorkflowState(BaseModel):
    id: str
    description: Optional[str] = None
    kind: Optional[str] = None

    model_config = {"extra": "forbid"}


class WorkflowTransition(BaseModel):
    from_state: str
    to_state: str
    on_command: Optional[str] = None
    on_event: Optional[str] = None
    guards: list[GuardRef] = Field(default_factory=list)
    effects: list[EffectRef] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class WorkflowErrorHandler(BaseModel):
    error: str
    action: str
    transition_to: Optional[str] = None

    model_config = {"extra": "forbid"}


class Workflow(BaseModel):
    id: str
    description: Optional[str] = None
    entity: str
    states: list[WorkflowState] = Field(default_factory=list)
    transitions: list[WorkflowTransition] = Field(default_factory=list)
    initial_state: str
    error_handlers: list[WorkflowErrorHandler] = Field(default_factory=list)
    required_roles: list[str] = Field(default_factory=list)
    required_permissions: list[str] = Field(default_factory=list)
    scenarios: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source: Optional[str] = None

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="workflow.definition",
        usage_en=(
            "State machine that describes the lifecycle of a domain entity and the commands "
            "or events that trigger transitions between states."
        ),
        included_by=[
            "scenario.definition",
            "policy.business",
        ],
        includes=[
            "domain.entity",
            "domain.event",
            "app.command",
            "shared.guard_ref",
            "shared.effect_ref",
        ],
        real_world_examples=[
            "Subscription lifecycle from trial to active and cancelled",
            "Invoice lifecycle from draft to paid and void",
            "User onboarding workflow with activation steps",
            "Approval workflow for high-value orders",
            "Support ticket workflow from open to resolved",
        ],
        visualizers=[
            "State machine diagrams",
            "BPMN-like workflow tools",
        ],
    )


class WorkflowsFile(BaseModel):
    workflows: list[Workflow]

    model_config = {"extra": "forbid"}
