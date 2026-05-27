# coding: utf-8
"""
Kiểm tra mô-đun parser cho CP42 — Approval Workflow Engine.

Bao gồm các tests cho:
- ApprovalIR: empty, with data, to_dict/from_dict roundtrip
- parse_approval_requests: từ key 'approval_requests', từ key 'approvals', empty, alias
- parse_approval_steps: từ key 'approval_steps', từ key 'steps', empty, alias
- parse_escalation_rules: từ key 'escalation_rules', từ key 'escalations', empty, alias
- parse_delegations: từ key 'delegations', từ key 'delegates', alias
- parse_to_ir: full data, empty data, only requests, only steps, events default
"""

from __future__ import annotations

import pytest


# ===========================================================================
# Test ApprovalIR
# ===========================================================================


class TestApprovalIR:
    """Kiểm tra ApprovalIR — khởi tạo, serialize, deserialize."""

    def test_approval_ir_empty(self):
        """Kiểm tra ApprovalIR rỗng có các danh sách rỗng và use_events=True."""
        from midicoder.packs.cp42_approval.parser import ApprovalIR
        ir = ApprovalIR()
        assert len(ir.requests) == 0
        assert len(ir.steps) == 0
        assert len(ir.escalation_rules) == 0
        assert len(ir.delegations) == 0
        assert ir.notification_config == {}
        assert ir.use_events is True

    def test_approval_ir_to_dict_empty(self):
        """Kiểm tra chuyển ApprovalIR rỗng sang dict."""
        from midicoder.packs.cp42_approval.parser import ApprovalIR
        ir = ApprovalIR()
        d = ir.to_dict()
        assert d["requests"] == []
        assert d["steps"] == []
        assert d["escalation_rules"] == []
        assert d["delegations"] == []
        assert d["notification_config"] == {}
        assert d["use_events"] is True

    def test_approval_ir_with_data(self):
        """Kiểm tra ApprovalIR có dữ liệu đầy đủ các loại đối tượng."""
        from midicoder.packs.cp42_approval.parser import ApprovalIR
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
        req = ApprovalRequest(
            request_id="req_001",
            title="Phê duyệt đơn mua",
            approval_type=ApprovalType.SEQUENTIAL,
            status=ApprovalStatus.PENDING,
        )
        step = ApprovalStep(
            step_id="step_001",
            request_id="req_001",
            step_number=1,
            approver_id="user_001",
            approver_role="manager",
        )
        rule = EscalationRule(
            rule_id="rule_001",
            request_id="req_001",
            escalation_strategy=EscalationStrategy.NEXT_LEVEL,
        )
        delegation = DelegationRecord(
            delegation_id="del_001",
            delegator_id="user_001",
            delegatee_id="user_002",
            delegation_type=DelegationType.TEMPORARY,
        )
        ir = ApprovalIR(
            requests=[req],
            steps=[step],
            escalation_rules=[rule],
            delegations=[delegation],
            notification_config={"email": True},
            use_events=False,
        )
        assert len(ir.requests) == 1
        assert len(ir.steps) == 1
        assert len(ir.escalation_rules) == 1
        assert len(ir.delegations) == 1
        assert ir.notification_config == {"email": True}
        assert ir.use_events is False

    def test_approval_ir_to_dict_with_data(self):
        """Kiểm tra chuyển ApprovalIR có dữ liệu sang dict đúng."""
        from midicoder.packs.cp42_approval.parser import ApprovalIR
        from midicoder.packs.cp42_approval.models import (
            ApprovalRequest,
            ApprovalStep,
            ApprovalType,
        )
        req = ApprovalRequest(
            request_id="req_dict",
            title="Test dict",
            approval_type=ApprovalType.PARALLEL,
        )
        step = ApprovalStep(
            step_id="step_dict",
            request_id="req_dict",
            step_number=1,
            approver_id="user_dict",
            approver_role="admin",
        )
        ir = ApprovalIR(requests=[req], steps=[step], use_events=False)
        d = ir.to_dict()
        assert len(d["requests"]) == 1
        assert d["requests"][0]["request_id"] == "req_dict"
        assert len(d["steps"]) == 1
        assert d["steps"][0]["step_id"] == "step_dict"
        assert d["use_events"] is False

    def test_approval_ir_from_dict_roundtrip(self):
        """Kiểm tra ApprovalIR to_dict rồi from_dict giữ nguyên dữ liệu."""
        from midicoder.packs.cp42_approval.parser import ApprovalIR
        from midicoder.packs.cp42_approval.models import (
            ApprovalRequest,
            ApprovalStep,
            ApprovalType,
            DelegationRecord,
            DelegationType,
            EscalationRule,
            EscalationStrategy,
        )
        req = ApprovalRequest(
            request_id="req_rt",
            title="Roundtrip test",
            approval_type=ApprovalType.MATRIX,
        )
        step = ApprovalStep(
            step_id="step_rt",
            request_id="req_rt",
            step_number=2,
            approver_id="user_rt",
            approver_role="director",
        )
        rule = EscalationRule(
            rule_id="rule_rt",
            request_id="req_rt",
            escalation_strategy=EscalationStrategy.MANAGER,
        )
        delegation = DelegationRecord(
            delegation_id="del_rt",
            delegator_id="user_rt",
            delegatee_id="user_rt2",
            delegation_type=DelegationType.PERMANENT,
        )
        ir = ApprovalIR(
            requests=[req],
            steps=[step],
            escalation_rules=[rule],
            delegations=[delegation],
            notification_config={"sms": True},
            use_events=True,
        )
        d = ir.to_dict()
        restored = ApprovalIR.from_dict(d)
        assert len(restored.requests) == 1
        assert restored.requests[0].request_id == "req_rt"
        assert len(restored.steps) == 1
        assert restored.steps[0].step_id == "step_rt"
        assert len(restored.escalation_rules) == 1
        assert restored.escalation_rules[0].rule_id == "rule_rt"
        assert len(restored.delegations) == 1
        assert restored.delegations[0].delegation_id == "del_rt"
        assert restored.notification_config == {"sms": True}
        assert restored.use_events is True


# ===========================================================================
# Test parse_approval_requests
# ===========================================================================


class TestParseApprovalRequests:
    """Kiểm tra parse_approval_requests — nhiều key, alias, rỗng."""

    def test_parse_from_approval_requests_key(self):
        """Kiểm tra parse từ key chính 'approval_requests'."""
        from midicoder.packs.cp42_approval.parser import parse_approval_requests
        data = {
            "approval_requests": [
                {
                    "request_id": "req_001",
                    "title": "Phê duyệt đơn mua",
                    "approval_type": "sequential",
                }
            ]
        }
        result = parse_approval_requests(data)
        assert len(result) == 1
        assert result[0].request_id == "req_001"
        assert result[0].title == "Phê duyệt đơn mua"

    def test_parse_from_approvals_alias_key(self):
        """Kiểm tra parse từ key alias 'approvals'."""
        from midicoder.packs.cp42_approval.parser import parse_approval_requests
        data = {
            "approvals": [
                {
                    "request_id": "req_002",
                    "title": "Phê duyệt nghỉ phép",
                    "approval_type": "parallel",
                }
            ]
        }
        result = parse_approval_requests(data)
        assert len(result) == 1
        assert result[0].request_id == "req_002"
        assert result[0].title == "Phê duyệt nghỉ phép"

    def test_parse_empty(self):
        """Kiểm tra parse dữ liệu rỗng trả về danh sách rỗng."""
        from midicoder.packs.cp42_approval.parser import parse_approval_requests
        data = {}
        result = parse_approval_requests(data)
        assert len(result) == 0

    def test_parse_with_all_fields(self):
        """Kiểm tra parse với tất cả các trường đầy đủ."""
        from midicoder.packs.cp42_approval.parser import parse_approval_requests
        data = {
            "approval_requests": [
                {
                    "request_id": "req_full",
                    "title": "Yêu cầu đầy đủ",
                    "description": "Mô tả chi tiết yêu cầu phê duyệt",
                    "entity_type": "purchase_order",
                    "entity_id": "po_123",
                    "approval_type": "matrix",
                    "status": "approved",
                    "initiator_id": "user_init",
                    "current_step": 3,
                    "total_steps": 5,
                    "metadata": {"department": "finance"},
                }
            ]
        }
        result = parse_approval_requests(data)
        assert len(result) == 1
        r = result[0]
        assert r.request_id == "req_full"
        assert r.title == "Yêu cầu đầy đủ"
        assert r.description == "Mô tả chi tiết yêu cầu phê duyệt"
        assert r.entity_type == "purchase_order"
        assert r.entity_id == "po_123"
        assert r.initiator_id == "user_init"
        assert r.current_step == 3
        assert r.total_steps == 5
        assert r.metadata == {"department": "finance"}

    def test_parse_with_id_alias(self):
        """Kiểm tra alias key 'id' thay cho 'request_id'."""
        from midicoder.packs.cp42_approval.parser import parse_approval_requests
        data = {
            "approval_requests": [
                {
                    "id": "req_alias_id",
                    "title": "Test alias id",
                }
            ]
        }
        result = parse_approval_requests(data)
        assert result[0].request_id == "req_alias_id"

    def test_parse_with_initiator_alias(self):
        """Kiểm tra alias key 'initiator' thay cho 'initiator_id'."""
        from midicoder.packs.cp42_approval.parser import parse_approval_requests
        data = {
            "approval_requests": [
                {
                    "request_id": "req_init_alias",
                    "initiator": "user_initiator",
                }
            ]
        }
        result = parse_approval_requests(data)
        assert result[0].initiator_id == "user_initiator"

    def test_parse_with_type_alias(self):
        """Kiểm tra alias key 'type' thay cho 'entity_type'."""
        from midicoder.packs.cp42_approval.parser import parse_approval_requests
        data = {
            "approval_requests": [
                {
                    "request_id": "req_type_alias",
                    "type": "leave_request",
                }
            ]
        }
        result = parse_approval_requests(data)
        assert result[0].entity_type == "leave_request"

    def test_parse_multiple_requests(self):
        """Kiểm tra parse nhiều yêu cầu phê duyệt cùng lúc."""
        from midicoder.packs.cp42_approval.parser import parse_approval_requests
        data = {
            "approval_requests": [
                {
                    "request_id": "req_001",
                    "title": "Đơn mua số 1",
                },
                {
                    "request_id": "req_002",
                    "title": "Đơn mua số 2",
                },
                {
                    "request_id": "req_003",
                    "title": "Đơn mua số 3",
                },
            ]
        }
        result = parse_approval_requests(data)
        assert len(result) == 3
        assert result[0].request_id == "req_001"
        assert result[1].request_id == "req_002"
        assert result[2].request_id == "req_003"


# ===========================================================================
# Test parse_approval_steps
# ===========================================================================


class TestParseApprovalSteps:
    """Kiểm tra parse_approval_steps — nhiều key, alias, rỗng."""

    def test_parse_from_approval_steps_key(self):
        """Kiểm tra parse từ key chính 'approval_steps'."""
        from midicoder.packs.cp42_approval.parser import parse_approval_steps
        data = {
            "approval_steps": [
                {
                    "step_id": "step_001",
                    "request_id": "req_001",
                    "step_number": 1,
                    "approver_id": "user_001",
                    "approver_role": "manager",
                }
            ]
        }
        result = parse_approval_steps(data)
        assert len(result) == 1
        assert result[0].step_id == "step_001"
        assert result[0].request_id == "req_001"

    def test_parse_from_steps_alias_key(self):
        """Kiểm tra parse từ key alias 'steps'."""
        from midicoder.packs.cp42_approval.parser import parse_approval_steps
        data = {
            "steps": [
                {
                    "step_id": "step_002",
                    "request_id": "req_002",
                    "step_number": 2,
                    "approver_id": "user_002",
                    "approver_role": "director",
                }
            ]
        }
        result = parse_approval_steps(data)
        assert len(result) == 1
        assert result[0].step_id == "step_002"

    def test_parse_empty(self):
        """Kiểm tra parse dữ liệu rỗng trả về danh sách rỗng."""
        from midicoder.packs.cp42_approval.parser import parse_approval_steps
        data = {}
        result = parse_approval_steps(data)
        assert len(result) == 0

    def test_parse_with_all_fields(self):
        """Kiểm tra parse với tất cả các trường đầy đủ."""
        from midicoder.packs.cp42_approval.parser import parse_approval_steps
        data = {
            "approval_steps": [
                {
                    "step_id": "step_full",
                    "request_id": "req_full",
                    "step_number": 3,
                    "approver_id": "user_approver",
                    "approver_role": "cto",
                    "status": "approved",
                    "is_parallel": True,
                }
            ]
        }
        result = parse_approval_steps(data)
        assert len(result) == 1
        s = result[0]
        assert s.step_id == "step_full"
        assert s.step_number == 3
        assert s.approver_id == "user_approver"
        assert s.approver_role == "cto"
        assert s.is_parallel is True

    def test_parse_with_id_alias(self):
        """Kiểm tra alias key 'id' thay cho 'step_id'."""
        from midicoder.packs.cp42_approval.parser import parse_approval_steps
        data = {
            "approval_steps": [
                {
                    "id": "step_alias_id",
                    "request_id": "req_001",
                    "approver_id": "user_001",
                }
            ]
        }
        result = parse_approval_steps(data)
        assert result[0].step_id == "step_alias_id"

    def test_parse_with_approver_alias(self):
        """Kiểm tra alias key 'approver' thay cho 'approver_id'."""
        from midicoder.packs.cp42_approval.parser import parse_approval_steps
        data = {
            "approval_steps": [
                {
                    "step_id": "step_approver_alias",
                    "request_id": "req_001",
                    "approver": "user_alias_approver",
                }
            ]
        }
        result = parse_approval_steps(data)
        assert result[0].approver_id == "user_alias_approver"

    def test_parse_with_role_alias(self):
        """Kiểm tra alias key 'role' thay cho 'approver_role'."""
        from midicoder.packs.cp42_approval.parser import parse_approval_steps
        data = {
            "approval_steps": [
                {
                    "step_id": "step_role_alias",
                    "request_id": "req_001",
                    "approver_id": "user_001",
                    "role": "vp_kythuat",
                }
            ]
        }
        result = parse_approval_steps(data)
        assert result[0].approver_role == "vp_kythuat"

    def test_parse_multiple_steps(self):
        """Kiểm tra parse nhiều bước phê duyệt cùng lúc."""
        from midicoder.packs.cp42_approval.parser import parse_approval_steps
        data = {
            "approval_steps": [
                {
                    "step_id": "step_001",
                    "request_id": "req_001",
                    "step_number": 1,
                    "approver_id": "user_001",
                },
                {
                    "step_id": "step_002",
                    "request_id": "req_001",
                    "step_number": 2,
                    "approver_id": "user_002",
                },
            ]
        }
        result = parse_approval_steps(data)
        assert len(result) == 2
        assert result[0].step_id == "step_001"
        assert result[0].step_number == 1
        assert result[1].step_id == "step_002"
        assert result[1].step_number == 2


# ===========================================================================
# Test parse_escalation_rules
# ===========================================================================


class TestParseEscalationRules:
    """Kiểm tra parse_escalation_rules — nhiều key, alias, rỗng."""

    def test_parse_from_escalation_rules_key(self):
        """Kiểm tra parse từ key chính 'escalation_rules'."""
        from midicoder.packs.cp42_approval.parser import parse_escalation_rules
        data = {
            "escalation_rules": [
                {
                    "rule_id": "rule_001",
                    "request_id": "req_001",
                    "trigger_after_minutes": 30,
                    "escalation_strategy": "next_level",
                    "target_role": "director",
                    "target_id": "user_dir",
                    "max_escalation_level": 5,
                    "is_active": True,
                }
            ]
        }
        result = parse_escalation_rules(data)
        assert len(result) == 1
        assert result[0].rule_id == "rule_001"
        assert result[0].request_id == "req_001"
        assert result[0].trigger_after_minutes == 30

    def test_parse_from_escalations_alias_key(self):
        """Kiểm tra parse từ key alias 'escalations'."""
        from midicoder.packs.cp42_approval.parser import parse_escalation_rules
        data = {
            "escalations": [
                {
                    "rule_id": "rule_002",
                    "request_id": "req_002",
                    "trigger_after_minutes": 120,
                }
            ]
        }
        result = parse_escalation_rules(data)
        assert len(result) == 1
        assert result[0].rule_id == "rule_002"
        assert result[0].trigger_after_minutes == 120

    def test_parse_empty(self):
        """Kiểm tra parse dữ liệu rỗng trả về danh sách rỗng."""
        from midicoder.packs.cp42_approval.parser import parse_escalation_rules
        data = {}
        result = parse_escalation_rules(data)
        assert len(result) == 0

    def test_parse_with_all_fields(self):
        """Kiểm tra parse với tất cả các trường đầy đủ."""
        from midicoder.packs.cp42_approval.parser import parse_escalation_rules
        data = {
            "escalation_rules": [
                {
                    "rule_id": "rule_full",
                    "request_id": "req_full",
                    "trigger_after_minutes": 45,
                    "escalation_strategy": "manager",
                    "target_role": "gm",
                    "target_id": "user_gm",
                    "max_escalation_level": 4,
                    "is_active": False,
                }
            ]
        }
        result = parse_escalation_rules(data)
        assert len(result) == 1
        r = result[0]
        assert r.rule_id == "rule_full"
        assert r.trigger_after_minutes == 45
        assert r.target_role == "gm"
        assert r.target_id == "user_gm"
        assert r.max_escalation_level == 4
        assert r.is_active is False

    def test_parse_with_strategy_alias(self):
        """Kiểm tra alias key 'strategy' thay cho 'escalation_strategy'."""
        from midicoder.packs.cp42_approval.parser import parse_escalation_rules
        from midicoder.packs.cp42_approval.models import EscalationStrategy
        data = {
            "escalation_rules": [
                {
                    "rule_id": "rule_strat_alias",
                    "request_id": "req_001",
                    "strategy": "timeout",
                }
            ]
        }
        result = parse_escalation_rules(data)
        assert result[0].escalation_strategy == EscalationStrategy.TIMEOUT

    def test_parse_multiple_rules(self):
        """Kiểm tra parse nhiều quy tắc leo thang cùng lúc."""
        from midicoder.packs.cp42_approval.parser import parse_escalation_rules
        data = {
            "escalation_rules": [
                {
                    "rule_id": "rule_001",
                    "request_id": "req_001",
                    "trigger_after_minutes": 30,
                },
                {
                    "rule_id": "rule_002",
                    "request_id": "req_001",
                    "trigger_after_minutes": 60,
                },
            ]
        }
        result = parse_escalation_rules(data)
        assert len(result) == 2
        assert result[0].rule_id == "rule_001"
        assert result[1].rule_id == "rule_002"


# ===========================================================================
# Test parse_delegations
# ===========================================================================


class TestParseDelegations:
    """Kiểm tra parse_delegations — nhiều key, alias, rỗng."""

    def test_parse_from_delegations_key(self):
        """Kiểm tra parse từ key chính 'delegations'."""
        from midicoder.packs.cp42_approval.parser import parse_delegations
        data = {
            "delegations": [
                {
                    "delegation_id": "del_001",
                    "delegator_id": "user_001",
                    "delegatee_id": "user_002",
                    "delegation_type": "temporary",
                    "scope": "req_001",
                    "is_active": True,
                }
            ]
        }
        result = parse_delegations(data)
        assert len(result) == 1
        assert result[0].delegation_id == "del_001"
        assert result[0].delegator_id == "user_001"
        assert result[0].delegatee_id == "user_002"
        assert result[0].scope == "req_001"

    def test_parse_from_delegates_alias_key(self):
        """Kiểm tra parse từ key alias 'delegates'."""
        from midicoder.packs.cp42_approval.parser import parse_delegations
        data = {
            "delegates": [
                {
                    "delegation_id": "del_002",
                    "delegator_id": "user_003",
                    "delegatee_id": "user_004",
                }
            ]
        }
        result = parse_delegations(data)
        assert len(result) == 1
        assert result[0].delegation_id == "del_002"
        assert result[0].delegator_id == "user_003"

    def test_parse_with_type_alias(self):
        """Kiểm tra alias key 'type' thay cho 'delegation_type'."""
        from midicoder.packs.cp42_approval.parser import parse_delegations
        from midicoder.packs.cp42_approval.models import DelegationType
        data = {
            "delegations": [
                {
                    "delegation_id": "del_type_alias",
                    "delegator_id": "user_001",
                    "delegatee_id": "user_002",
                    "type": "permanent",
                }
            ]
        }
        result = parse_delegations(data)
        assert result[0].delegation_type == DelegationType.PERMANENT

    def test_parse_with_delegator_delegatee_aliases(self):
        """Kiểm tra alias 'delegator' và 'delegatee' thay cho trường đầy đủ."""
        from midicoder.packs.cp42_approval.parser import parse_delegations
        data = {
            "delegations": [
                {
                    "delegation_id": "del_alias",
                    "delegator": "user_from",
                    "delegatee": "user_to",
                }
            ]
        }
        result = parse_delegations(data)
        assert result[0].delegator_id == "user_from"
        assert result[0].delegatee_id == "user_to"


# ===========================================================================
# Test parse_to_ir
# ===========================================================================


class TestParseToIR:
    """Kiểm tra parse_to_ir — DSL dict sang ApprovalIR."""

    def test_parse_full_data_to_ir(self):
        """Kiểm tra parse toàn bộ dữ liệu DSL sang ApprovalIR."""
        from midicoder.packs.cp42_approval.parser import parse_to_ir
        data = {
            "approval_requests": [
                {
                    "request_id": "req_ir",
                    "title": "IR test request",
                    "entity_type": "purchase_order",
                    "entity_id": "po_ir",
                    "initiator_id": "user_ir",
                }
            ],
            "approval_steps": [
                {
                    "step_id": "step_ir",
                    "request_id": "req_ir",
                    "step_number": 1,
                    "approver_id": "user_ir_approver",
                    "approver_role": "manager",
                }
            ],
            "escalation_rules": [
                {
                    "rule_id": "rule_ir",
                    "request_id": "req_ir",
                    "trigger_after_minutes": 30,
                }
            ],
            "delegations": [
                {
                    "delegation_id": "del_ir",
                    "delegator_id": "user_ir",
                    "delegatee_id": "user_ir2",
                }
            ],
            "notification_config": {"email": True, "sms": False},
            "use_events": True,
        }
        ir = parse_to_ir(data)
        assert len(ir.requests) == 1
        assert len(ir.steps) == 1
        assert len(ir.escalation_rules) == 1
        assert len(ir.delegations) == 1
        assert ir.requests[0].request_id == "req_ir"
        assert ir.steps[0].step_id == "step_ir"
        assert ir.escalation_rules[0].rule_id == "rule_ir"
        assert ir.delegations[0].delegation_id == "del_ir"
        assert ir.notification_config == {"email": True, "sms": False}
        assert ir.use_events is True

    def test_parse_empty_data(self):
        """Kiểm tra parse dữ liệu rỗng trả về ApprovalIR rỗng."""
        from midicoder.packs.cp42_approval.parser import parse_to_ir
        data = {}
        ir = parse_to_ir(data)
        assert len(ir.requests) == 0
        assert len(ir.steps) == 0
        assert len(ir.escalation_rules) == 0
        assert len(ir.delegations) == 0
        assert ir.notification_config == {}
        assert ir.use_events is True

    def test_parse_only_requests(self):
        """Kiểm tra parse chỉ có yêu cầu phê duyệt, các thành phần khác rỗng."""
        from midicoder.packs.cp42_approval.parser import parse_to_ir
        data = {
            "approval_requests": [
                {
                    "request_id": "req_only",
                    "title": "Chỉ có request",
                }
            ]
        }
        ir = parse_to_ir(data)
        assert len(ir.requests) == 1
        assert len(ir.steps) == 0
        assert len(ir.escalation_rules) == 0
        assert len(ir.delegations) == 0

    def test_parse_only_steps(self):
        """Kiểm tra parse chỉ có bước phê duyệt, các thành phần khác rỗng."""
        from midicoder.packs.cp42_approval.parser import parse_to_ir
        data = {
            "approval_steps": [
                {
                    "step_id": "step_only",
                    "request_id": "req_only",
                    "approver_id": "user_only",
                }
            ]
        }
        ir = parse_to_ir(data)
        assert len(ir.requests) == 0
        assert len(ir.steps) == 1
        assert ir.steps[0].step_id == "step_only"

    def test_parse_with_events_default_true(self):
        """Kiểm tra use_events mặc định là True khi không khai báo."""
        from midicoder.packs.cp42_approval.parser import parse_to_ir
        data = {
            "approval_requests": [
                {
                    "request_id": "req_events",
                }
            ]
        }
        ir = parse_to_ir(data)
        assert ir.use_events is True
