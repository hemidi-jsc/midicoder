# coding: utf-8
"""
Mô-đun parser cho CP42 — Approval Workflow Engine.

Parse DSL dict (từ contract YAML) sang ApprovalIR — Intermediate Representation
cho các yêu cầu phê duyệt, bước phê duyệt, quy tắc leo thang, ủy quyền,
và cấu hình thông báo.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.emitters.core.cp42_approval.models import (
    ApprovalRequest,
    ApprovalStep,
    ApprovalStatus,
    ApprovalType,
    DelegationRecord,
    DelegationType,
    EscalationRule,
    EscalationStrategy,
)


@dataclass
class ApprovalIR:
    """Intermediate Representation cho CP42.

    Gom tập tất cả cấu hình quy trình phê duyệt từ DSL, bao gồm
    các yêu cầu phê duyệt, bước phê duyệt, quy tắc leo thang,
    ủy quyền, và cấu hình thông báo.

    Attributes:
        requests: Danh sách yêu cầu phê duyệt
        steps: Danh sách bước phê duyệt
        escalation_rules: Danh sách quy tắc leo thang
        delegations: Danh sách ghi nhận ủy quyền
        notification_config: Cấu hình thông báo
        use_events: Có sử dụng event-driven không
    """
    requests: list[ApprovalRequest] = field(default_factory=list)
    steps: list[ApprovalStep] = field(default_factory=list)
    escalation_rules: list[EscalationRule] = field(default_factory=list)
    delegations: list[DelegationRecord] = field(default_factory=list)
    notification_config: dict = field(default_factory=dict)
    use_events: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ApprovalIR sang dict."""
        return {
            "requests": [r.to_dict() for r in self.requests],
            "steps": [s.to_dict() for s in self.steps],
            "escalation_rules": [e.to_dict() for e in self.escalation_rules],
            "delegations": [d.to_dict() for d in self.delegations],
            "notification_config": self.notification_config,
            "use_events": self.use_events,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApprovalIR":
        """Tạo ApprovalIR từ dict."""
        requests = [ApprovalRequest.from_dict(r) for r in data.get("requests", [])]
        steps = [ApprovalStep.from_dict(s) for s in data.get("steps", [])]
        escalation_rules = [EscalationRule.from_dict(e) for e in data.get("escalation_rules", [])]
        delegations = [DelegationRecord.from_dict(d) for d in data.get("delegations", [])]
        return cls(
            requests=requests,
            steps=steps,
            escalation_rules=escalation_rules,
            delegations=delegations,
            notification_config=data.get("notification_config", {}),
            use_events=data.get("use_events", True),
        )


def parse_approval_requests(data: dict[str, Any]) -> list[ApprovalRequest]:
    """Parse danh sách yêu cầu phê duyệt từ DSL dict.

    Args:
        data: DSL dict với key 'approval_requests' hoặc 'approvals'

    Returns:
        Danh sách ApprovalRequest
    """
    raw = data.get("approval_requests", data.get("approvals", []))
    requests = []
    for req in raw:
        requests.append(ApprovalRequest(
            request_id=req.get("request_id", req.get("id", "")),
            title=req.get("title", ""),
            description=req.get("description", ""),
            entity_type=req.get("entity_type", req.get("type", "")),
            entity_id=req.get("entity_id", req.get("entity", "")),
            approval_type=ApprovalType(req.get("approval_type", "sequential")),
            status=ApprovalStatus(req.get("status", "pending")),
            initiator_id=req.get("initiator_id", req.get("initiator", "")),
            current_step=req.get("current_step", 1),
            total_steps=req.get("total_steps", 1),
            metadata=req.get("metadata", {}),
        ))
    return requests


def parse_approval_steps(data: dict[str, Any]) -> list[ApprovalStep]:
    """Parse danh sách bước phê duyệt từ DSL dict.

    Args:
        data: DSL dict với key 'approval_steps' hoặc 'steps'

    Returns:
        Danh sách ApprovalStep
    """
    raw = data.get("approval_steps", data.get("steps", []))
    steps = []
    for step in raw:
        steps.append(ApprovalStep(
            step_id=step.get("step_id", step.get("id", "")),
            request_id=step.get("request_id", step.get("approval_request_id", "")),
            step_number=step.get("step_number", step.get("order", 1)),
            approver_id=step.get("approver_id", step.get("approver", "")),
            approver_role=step.get("approver_role", step.get("role", "")),
            status=ApprovalStatus(step.get("status", "pending")),
            is_parallel=step.get("is_parallel", False),
        ))
    return steps


def parse_escalation_rules(data: dict[str, Any]) -> list[EscalationRule]:
    """Parse danh sách quy tắc leo thang từ DSL dict.

    Args:
        data: DSL dict với key 'escalation_rules' hoặc 'escalations'

    Returns:
        Danh sách EscalationRule
    """
    raw = data.get("escalation_rules", data.get("escalations", []))
    rules = []
    for rule in raw:
        rules.append(EscalationRule(
            rule_id=rule.get("rule_id", rule.get("id", "")),
            request_id=rule.get("request_id", rule.get("approval_request_id", "")),
            trigger_after_minutes=rule.get("trigger_after_minutes", rule.get("timeout_minutes", 60)),
            escalation_strategy=EscalationStrategy(rule.get("escalation_strategy", rule.get("strategy", "next_level"))),
            target_role=rule.get("target_role", rule.get("role", "")),
            target_id=rule.get("target_id", rule.get("target", "")),
            max_escalation_level=rule.get("max_escalation_level", 3),
            is_active=rule.get("is_active", True),
        ))
    return rules


def parse_delegations(data: dict[str, Any]) -> list[DelegationRecord]:
    """Parse danh sách ghi nhận ủy quyền từ DSL dict.

    Args:
        data: DSL dict với key 'delegations' hoặc 'delegates'

    Returns:
        Danh sách DelegationRecord
    """
    raw = data.get("delegations", data.get("delegates", []))
    delegations = []
    for del_rec in raw:
        delegations.append(DelegationRecord(
            delegation_id=del_rec.get("delegation_id", del_rec.get("id", "")),
            delegator_id=del_rec.get("delegator_id", del_rec.get("delegator", "")),
            delegatee_id=del_rec.get("delegatee_id", del_rec.get("delegatee", "")),
            delegation_type=DelegationType(del_rec.get("delegation_type", del_rec.get("type", "temporary"))),
            scope=del_rec.get("scope", ""),
            is_active=del_rec.get("is_active", True),
        ))
    return delegations


def parse_to_ir(data: dict[str, Any]) -> ApprovalIR:
    """Parse DSL dict thành ApprovalIR.

    Args:
        data: DSL dict với requests, steps, escalation_rules,
            delegations, notification_config, use_events

    Returns:
        ApprovalIR gom tập tất cả parsed data
    """
    requests = parse_approval_requests(data)
    steps = parse_approval_steps(data)
    escalation_rules = parse_escalation_rules(data)
    delegations = parse_delegations(data)
    return ApprovalIR(
        requests=requests,
        steps=steps,
        escalation_rules=escalation_rules,
        delegations=delegations,
        notification_config=data.get("notification_config", {}),
        use_events=data.get("use_events", True),
    )


__all__ = [
    "ApprovalIR",
    "parse_approval_requests",
    "parse_approval_steps",
    "parse_escalation_rules",
    "parse_delegations",
    "parse_to_ir",
]
