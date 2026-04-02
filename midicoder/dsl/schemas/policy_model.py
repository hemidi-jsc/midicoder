from __future__ import annotations

from typing import Any, ClassVar, Optional

from pydantic import BaseModel, Field

from .model_meta import ModelMeta


POLICY_OPERATOR_CATALOG = {
    "eq",
    "neq",
    "gt",
    "lt",
    "gte",
    "lte",
    "in",
    "contains",
}

POLICY_EFFECT_TYPE_CATALOG = {
    "allow",
    "deny",
    "limit",
}


class PolicyCondition(BaseModel):
    field: str
    op: str
    value: Any

    model_config = {"extra": "forbid"}


class PolicyEffect(BaseModel):
    type: str
    params: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class Policy(BaseModel):
    id: str
    description: Optional[str] = None
    scope: str
    conditions: list[PolicyCondition] = Field(default_factory=list)
    effects: list[PolicyEffect] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source: Optional[str] = None

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="policy.business",
        usage_en=(
            "Business policy describing conditions and effects that constrain commands, "
            "workflows or entities, such as limits, approvals or eligibility rules."
        ),
        included_by=[
            "scenario.definition",
        ],
        includes=[
            "rules.rule",
        ],
        real_world_examples=[
            "Trial feature access policy based on subscription plan",
            "Usage cap policy for API calls per tenant",
            "Approval policy for invoices above a threshold",
            "Data retention policy based on region and plan",
            "Discount eligibility policy for promotional campaigns",
        ],
        visualizers=[
            "Policy editors",
            "Decision table tools",
        ],
    )


class PoliciesFile(BaseModel):
    policies: list[Policy]

    model_config = {"extra": "forbid"}
