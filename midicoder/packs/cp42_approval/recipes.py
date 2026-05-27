# coding: utf-8
"""
Mô-đun recipes cho CP42 — Approval Workflow Engine.

Cung cấp các recipe patterns để generate quy trình phê duyệt với
chuỗi duyệt đa cấp, ma trận phê duyệt, ủy quyền, và nâng cấp.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from midicoder.packs.cp42_approval.models import (
    ApprovalRequest,
    ApprovalStep,
    ApprovalStatus,
    ApprovalType,
    DelegationRecord,
    DelegationType,
    EscalationRule,
    EscalationStrategy,
)
from midicoder.packs.cp42_approval.parser import ApprovalIR


@dataclass
class RecipeOutput:
    """Kết quả của recipe.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: ApprovalIR kết quả
    """
    name: str
    description: str
    ir: ApprovalIR


def basic_approval_recipe() -> RecipeOutput:
    """Recipe: Quy trình phê duyệt cơ bản — 1 yêu cầu tuần tự (2 bước: manager → director).

    Tạo yêu cầu phê duyệt tuần tự với 2 bước: quản lý phê duyệt trước,
    sau đó giám đốc phê duyệt. Không có quy tắc nâng cấp, không ủy quyền,
    use_events=True, không cấu hình thông báo — phù hợp cho dev/prototyping.

    Returns:
        RecipeOutput với cấu hình phê duyệt cơ bản
    """
    requests = [
        ApprovalRequest(
            request_id="appr_seq_001",
            title="Phê duyệt deploy payment-gateway v2.3.0",
            description="Yêu cầu phê duyệt deploy version 2.3.0 của payment-gateway lên production",
            entity_type="deploy",
            entity_id="deploy_v2.3.0",
            approval_type=ApprovalType.SEQUENTIAL,
            initiator_id="user_001",
            total_steps=2,
            metadata={"chain_type": "sequential"},
        ),
    ]

    steps = [
        ApprovalStep(
            step_id="step_seq_001",
            request_id="appr_seq_001",
            step_number=1,
            approver_id="manager_001",
            approver_role="manager",
            status=ApprovalStatus.PENDING,
        ),
        ApprovalStep(
            step_id="step_seq_002",
            request_id="appr_seq_001",
            step_number=2,
            approver_id="director_001",
            approver_role="director",
            status=ApprovalStatus.PENDING,
        ),
    ]

    return RecipeOutput(
        name="basic_approval",
        description="1 yêu cầu tuần tự (2 bước: manager → director), không nâng cấp, không ủy quyền",
        ir=ApprovalIR(
            requests=requests,
            steps=steps,
            escalation_rules=[],
            delegations=[],
            notification_config={},
            use_events=True,
        ),
    )


def full_workflow_recipe() -> RecipeOutput:
    """Recipe: Quy trình phê duyệt đầy đủ — 2 yêu cầu, 5 bước, nâng cấp, ủy quyền, thông báo.

    Tạo 2 yêu cầu phê duyệt: (1) tuần tự đa cấp với 3 bước (team_lead → manager → director),
    (2) song song bầu chọn với 2 bước (reviewer_001, reviewer_002).
    Bao gồm 2 quy tắc nâng cấp dựa trên timeout (next_level strategy),
    1 bản ghi ủy quyền tạm thời, cấu hình thông báo với event topics,
    use_events=True.

    Returns:
        RecipeOutput với cấu hình phê duyệt đầy đủ
    """
    now = datetime.now(timezone.utc)

    requests = [
        ApprovalRequest(
            request_id="appr_full_seq_001",
            title="Phê duyệt merge PR #42",
            description="Phê duyệt merge PR 42 (feature/payment-refactor) vào nhánh main của core-api",
            entity_type="merge",
            entity_id="pr_42",
            approval_type=ApprovalType.SEQUENTIAL,
            initiator_id="user_001",
            total_steps=3,
            metadata={"chain_type": "sequential", "priority": "high"},
        ),
        ApprovalRequest(
            request_id="appr_full_par_001",
            title="Phê duyệt release billing-service v3.0.0",
            description="Phê duyệt release version 3.0.0 của billing-service",
            entity_type="release",
            entity_id="release_v3.0.0",
            approval_type=ApprovalType.PARALLEL,
            initiator_id="user_002",
            total_steps=2,
            metadata={"chain_type": "parallel", "voting_mode": "majority"},
        ),
    ]

    steps = [
        # Yêu cầu tuần tự — 3 bước
        ApprovalStep(
            step_id="step_full_001",
            request_id="appr_full_seq_001",
            step_number=1,
            approver_id="team_lead_001",
            approver_role="team_lead",
            status=ApprovalStatus.PENDING,
        ),
        ApprovalStep(
            step_id="step_full_002",
            request_id="appr_full_seq_001",
            step_number=2,
            approver_id="manager_001",
            approver_role="manager",
            status=ApprovalStatus.PENDING,
        ),
        ApprovalStep(
            step_id="step_full_003",
            request_id="appr_full_seq_001",
            step_number=3,
            approver_id="director_001",
            approver_role="director",
            status=ApprovalStatus.PENDING,
        ),
        # Yêu cầu song song — 2 bước
        ApprovalStep(
            step_id="step_full_004",
            request_id="appr_full_par_001",
            step_number=1,
            approver_id="reviewer_001",
            approver_role="reviewer",
            status=ApprovalStatus.PENDING,
            is_parallel=True,
        ),
        ApprovalStep(
            step_id="step_full_005",
            request_id="appr_full_par_001",
            step_number=1,
            approver_id="reviewer_002",
            approver_role="reviewer",
            status=ApprovalStatus.PENDING,
            is_parallel=True,
        ),
    ]

    escalation_rules = [
        EscalationRule(
            rule_id="esc_full_001",
            request_id="appr_full_seq_001",
            trigger_after_minutes=120,
            escalation_strategy=EscalationStrategy.NEXT_LEVEL,
            target_role="director",
            target_id="director_001",
        ),
        EscalationRule(
            rule_id="esc_full_002",
            request_id="appr_full_par_001",
            trigger_after_minutes=240,
            escalation_strategy=EscalationStrategy.NEXT_LEVEL,
            target_role="cto",
            target_id="cto_001",
        ),
    ]

    delegations = [
        DelegationRecord(
            delegation_id="del_full_001",
            delegator_id="manager_001",
            delegatee_id="senior_dev_001",
            delegation_type=DelegationType.TEMPORARY,
            scope="merge",
            valid_until=now + timedelta(days=7),
        ),
    ]

    notification_config = {
        "event_topics": [
            "approval.requested",
            "approval.decided",
            "approval.escalated",
            "approval.delegated",
        ],
        "channels": ["email", "in_app"],
        "notify_on": ["step_assigned", "step_completed", "escalation_triggered"],
    }

    return RecipeOutput(
        name="full_workflow",
        description="2 yêu cầu (3 bước tuần tự + 2 bước song song), 2 quy tắc nâng cấp, 1 ủy quyền tạm thời, thông báo",
        ir=ApprovalIR(
            requests=requests,
            steps=steps,
            escalation_rules=escalation_rules,
            delegations=delegations,
            notification_config=notification_config,
            use_events=True,
        ),
    )


__all__ = [
    "RecipeOutput",
    "basic_approval_recipe",
    "full_workflow_recipe",
]
