# coding: utf-8
"""
CP42 — Approval Workflow Engine Pack.

Public API barrel export.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from midicoder.packs.cp_full_approval.models import (
    ApprovalEngine,
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStep,
    ApprovalStatus,
    ApprovalType,
    DelegationRecord,
    DelegationType,
    EscalationRule,
    EscalationStrategy,
    VotingMode,
)
from midicoder.packs.cp_full_approval.parser import (
    ApprovalIR,
    parse_approval_requests,
    parse_approval_steps,
    parse_escalation_rules,
    parse_to_ir,
)
from midicoder.packs.cp_full_approval.recipes import (
    RecipeOutput,
    basic_approval_recipe,
    full_workflow_recipe,
)
from midicoder.packs.cp_full_approval.fastapi import (
    FastAPIApprovalEmitter,
)
from midicoder.packs.cp_full_approval.nestjs import (
    NestJSApprovalEmitter,
)
from midicoder.packs.cp_full_approval.angular import (
    AngularApprovalEmitter,
)
from midicoder.packs.cp_full_approval.react import (
    ReactApprovalEmitter,
)

__all__ = [
    # Models - Enums
    "ApprovalStatus",
    "ApprovalType",
    "EscalationStrategy",
    "DelegationType",
    "VotingMode",
    # Models - Core
    "ApprovalRequest",
    "ApprovalStep",
    "ApprovalDecision",
    "EscalationRule",
    "DelegationRecord",
    # Models - Engine
    "ApprovalEngine",
    # Parser
    "ApprovalIR",
    "parse_approval_requests",
    "parse_approval_steps",
    "parse_escalation_rules",
    "parse_to_ir",
    # Recipes
    "RecipeOutput",
    "basic_approval_recipe",
    "full_workflow_recipe",
    # Emitters
    "FastAPIApprovalEmitter",
    "NestJSApprovalEmitter",
    "AngularApprovalEmitter",
    "ReactApprovalEmitter",
]
