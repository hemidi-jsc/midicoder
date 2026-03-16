from __future__ import annotations

from typing import Any, ClassVar, Optional

from pydantic import BaseModel, Field

from .model_meta import ModelMeta


RULE_SEVERITY_CATALOG = {
    "info",
    "warning",
    "error",
}


class RuleRow(BaseModel):
    when: dict[str, Any]
    then: dict[str, Any]

    model_config = {"extra": "forbid"}


class Rule(BaseModel):
    id: str
    description: Optional[str] = None
    applies_to: Optional[str] = None
    applies_to_scenario: Optional[str] = None
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    rows: list[RuleRow] = Field(default_factory=list)
    severity: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    source: Optional[str] = None

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="rules.rule",
        usage_en=(
            "Declarative business rule expressed as a set of when/then rows, used to refine "
            "behavior of commands, workflows or policies in a SaaS system."
        ),
        included_by=[
            "policy.business",
            "scenario.definition",
        ],
        includes=[],
        real_world_examples=[
            "Discount rule based on subscription plan and seat count",
            "Feature access rule based on user role and plan",
            "Billing retry rule controlling payment attempts",
            "Usage limit rule for API rate limiting",
            "Approval rule for high-value orders",
        ],
        visualizers=[
            "Decision table editors",
            "Rule engine dashboards",
        ],
    )


class RulesFile(BaseModel):
    rules: list[Rule]

    model_config = {"extra": "forbid"}
