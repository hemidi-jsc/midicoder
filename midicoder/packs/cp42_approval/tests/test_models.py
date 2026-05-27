# coding: utf-8
"""
Kiểm tra mô-đun models cho CP42 — Approval Workflow Engine.

Bao gồm các tests cho:
- Error codes: MDC-CP42-001 đến MDC-CP42-010
- Enums: ApprovalStatus, ApprovalType, EscalationStrategy, DelegationType, VotingMode
- ApprovalRequest: tạo, validate, to_dict/from_dict
- ApprovalStep: tạo, validate, to_dict/from_dict
- ApprovalDecision: tạo, validate, to_dict/from_dict
- EscalationRule: tạo, validate, to_dict/from_dict
- DelegationRecord: tạo, validate, to_dict/from_dict, is_valid_at
- ApprovalEngine: create_request, decide, delegate, escalate, check_deadlines,
  detect_cycle, resolve_approver, get_pending_approvals, get_decisions
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from midicoder.errors import ErrorCode, MidicoderError


# ===========================================================================
# Test Error Codes CP42
# ===========================================================================


class TestCP42ErrorCodes:
    """Kiểm tra các mã lỗi CP42 đã được định nghĩa đúng."""

    def test_cp42_approval_request_not_found_code(self):
        assert ErrorCode.CP42_APPROVAL_REQUEST_NOT_FOUND == "MDC-CP42-001"

    def test_cp42_approval_not_your_turn_code(self):
        assert ErrorCode.CP42_APPROVAL_NOT_YOUR_TURN == "MDC-CP42-002"

    def test_cp42_approval_already_decided_code(self):
        assert ErrorCode.CP42_APPROVAL_ALREADY_DECIDED == "MDC-CP42-003"

    def test_cp42_approval_missing_role_code(self):
        assert ErrorCode.CP42_APPROVAL_MISSING_ROLE == "MDC-CP42-004"

    def test_cp42_approval_chain_cycle_detected_code(self):
        assert ErrorCode.CP42_APPROVAL_CHAIN_CYCLE_DETECTED == "MDC-CP42-005"

    def test_cp42_approval_escalation_no_next_level_code(self):
        assert ErrorCode.CP42_APPROVAL_ESCALATION_NO_NEXT_LEVEL == "MDC-CP42-006"

    def test_cp42_approval_delegation_expired_code(self):
        assert ErrorCode.CP42_APPROVAL_DELEGATION_EXPIRED == "MDC-CP42-007"

    def test_cp42_approval_delegation_self_code(self):
        assert ErrorCode.CP42_APPROVAL_DELEGATION_SELF == "MDC-CP42-008"

    def test_cp42_approval_voting_not_quorum_code(self):
        assert ErrorCode.CP42_APPROVAL_VOTING_NOT_QUORUM == "MDC-CP42-009"

    def test_cp42_approval_event_handler_failed_code(self):
        assert ErrorCode.CP42_APPROVAL_EVENT_HANDLER_FAILED == "MDC-CP42-010"


# ===========================================================================
# Test ApprovalStatus Enum
# ===========================================================================


class TestApprovalStatus:
    """Kiểm tra các giá trị của enum ApprovalStatus."""

    def test_status_pending_value(self):
        from midicoder.packs.cp42_approval.models import ApprovalStatus
        assert ApprovalStatus.PENDING.value == "pending"

    def test_status_approved_value(self):
        from midicoder.packs.cp42_approval.models import ApprovalStatus
        assert ApprovalStatus.APPROVED.value == "approved"

    def test_status_rejected_value(self):
        from midicoder.packs.cp42_approval.models import ApprovalStatus
        assert ApprovalStatus.REJECTED.value == "rejected"

    def test_status_escalated_value(self):
        from midicoder.packs.cp42_approval.models import ApprovalStatus
        assert ApprovalStatus.ESCALATED.value == "escalated"

    def test_status_delegated_value(self):
        from midicoder.packs.cp42_approval.models import ApprovalStatus
        assert ApprovalStatus.DELEGATED.value == "delegated"

    def test_status_expired_value(self):
        from midicoder.packs.cp42_approval.models import ApprovalStatus
        assert ApprovalStatus.EXPIRED.value == "expired"

    def test_status_cancelled_value(self):
        from midicoder.packs.cp42_approval.models import ApprovalStatus
        assert ApprovalStatus.CANCELLED.value == "cancelled"

    def test_status_members_count(self):
        from midicoder.packs.cp42_approval.models import ApprovalStatus
        assert len(ApprovalStatus) == 7


# ===========================================================================
# Test ApprovalType Enum
# ===========================================================================


class TestApprovalType:
    """Kiểm tra các giá trị của enum ApprovalType."""

    def test_type_sequential_value(self):
        from midicoder.packs.cp42_approval.models import ApprovalType
        assert ApprovalType.SEQUENTIAL.value == "sequential"

    def test_type_parallel_value(self):
        from midicoder.packs.cp42_approval.models import ApprovalType
        assert ApprovalType.PARALLEL.value == "parallel"

    def test_type_matrix_value(self):
        from midicoder.packs.cp42_approval.models import ApprovalType
        assert ApprovalType.MATRIX.value == "matrix"

    def test_type_voting_value(self):
        from midicoder.packs.cp42_approval.models import ApprovalType
        assert ApprovalType.VOTING.value == "voting"

    def test_type_single_value(self):
        from midicoder.packs.cp42_approval.models import ApprovalType
        assert ApprovalType.SINGLE.value == "single"

    def test_type_members_count(self):
        from midicoder.packs.cp42_approval.models import ApprovalType
        assert len(ApprovalType) == 5


# ===========================================================================
# Test EscalationStrategy Enum
# ===========================================================================


class TestEscalationStrategy:
    """Kiểm tra các giá trị của enum EscalationStrategy."""

    def test_strategy_next_level_value(self):
        from midicoder.packs.cp42_approval.models import EscalationStrategy
        assert EscalationStrategy.NEXT_LEVEL.value == "next_level"

    def test_strategy_next_role_value(self):
        from midicoder.packs.cp42_approval.models import EscalationStrategy
        assert EscalationStrategy.NEXT_ROLE.value == "next_role"

    def test_strategy_manager_value(self):
        from midicoder.packs.cp42_approval.models import EscalationStrategy
        assert EscalationStrategy.MANAGER.value == "manager"

    def test_strategy_timeout_value(self):
        from midicoder.packs.cp42_approval.models import EscalationStrategy
        assert EscalationStrategy.TIMEOUT.value == "timeout"

    def test_strategy_members_count(self):
        from midicoder.packs.cp42_approval.models import EscalationStrategy
        assert len(EscalationStrategy) == 4


# ===========================================================================
# Test DelegationType Enum
# ===========================================================================


class TestDelegationType:
    """Kiểm tra các giá trị của enum DelegationType."""

    def test_delegation_type_temporary_value(self):
        from midicoder.packs.cp42_approval.models import DelegationType
        assert DelegationType.TEMPORARY.value == "temporary"

    def test_delegation_type_permanent_value(self):
        from midicoder.packs.cp42_approval.models import DelegationType
        assert DelegationType.PERMANENT.value == "permanent"

    def test_delegation_type_conditional_value(self):
        from midicoder.packs.cp42_approval.models import DelegationType
        assert DelegationType.CONDITIONAL.value == "conditional"

    def test_delegation_type_members_count(self):
        from midicoder.packs.cp42_approval.models import DelegationType
        assert len(DelegationType) == 3


# ===========================================================================
# Test VotingMode Enum
# ===========================================================================


class TestVotingMode:
    """Kiểm tra các giá trị của enum VotingMode."""

    def test_voting_mode_majority_value(self):
        from midicoder.packs.cp42_approval.models import VotingMode
        assert VotingMode.MAJORITY.value == "majority"

    def test_voting_mode_unanimity_value(self):
        from midicoder.packs.cp42_approval.models import VotingMode
        assert VotingMode.UNANIMITY.value == "unanimity"

    def test_voting_mode_first_decides_value(self):
        from midicoder.packs.cp42_approval.models import VotingMode
        assert VotingMode.FIRST_DECIDES.value == "first_decides"

    def test_voting_mode_weighted_value(self):
        from midicoder.packs.cp42_approval.models import VotingMode
        assert VotingMode.WEIGHTED.value == "weighted"

    def test_voting_mode_members_count(self):
        from midicoder.packs.cp42_approval.models import VotingMode
        assert len(VotingMode) == 4


# ===========================================================================
# Test ApprovalRequest
# ===========================================================================


class TestApprovalRequest:
    """Kiểm tra ApprovalRequest — tạo, validate, serialize."""

    def test_create_valid_request(self):
        from midicoder.packs.cp42_approval.models import (
            ApprovalRequest,
            ApprovalStatus,
            ApprovalType,
        )
        req = ApprovalRequest(
            request_id="req_001",
            title="Đề xuất mua sắm",
            description="Mua thiết bị mới",
            entity_type="purchase_order",
            entity_id="po_42",
            approval_type=ApprovalType.SEQUENTIAL,
            status=ApprovalStatus.PENDING,
            initiator_id="user_001",
            total_steps=3,
        )
        assert req.request_id == "req_001"
        assert req.title == "Đề xuất mua sắm"
        assert req.status == ApprovalStatus.PENDING
        assert req.approval_type == ApprovalType.SEQUENTIAL
        assert req.total_steps == 3

    def test_create_request_empty_id_raises(self):
        """Kiểm tra tạo yêu cầu với ID rỗng sẽ ném lỗi."""
        from midicoder.packs.cp42_approval.models import ApprovalRequest
        with pytest.raises(MidicoderError):
            ApprovalRequest(request_id="")

    def test_create_request_whitespace_id_raises(self):
        """Kiểm tra tạo yêu cầu với ID chỉ chứa khoảng trắng sẽ ném lỗi."""
        from midicoder.packs.cp42_approval.models import ApprovalRequest
        with pytest.raises(MidicoderError):
            ApprovalRequest(request_id="   ")

    def test_auto_timestamps(self):
        """Kiểm tra tự động tạo timestamps khi không cung cấp."""
        from midicoder.packs.cp42_approval.models import ApprovalRequest
        req = ApprovalRequest(request_id="req_ts")
        assert req.created_at is not None
        assert req.updated_at is not None
        assert req.deadline is not None

    def test_entity_fields(self):
        """Kiểm tra các trường entity_type và entity_id."""
        from midicoder.packs.cp42_approval.models import ApprovalRequest
        req = ApprovalRequest(
            request_id="req_ent",
            entity_type="leave_request",
            entity_id="leave_001",
        )
        assert req.entity_type == "leave_request"
        assert req.entity_id == "leave_001"

    def test_approval_type(self):
        """Kiểm tra loại phê duyệt mặc định là SEQUENTIAL."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalRequest,
            ApprovalType,
        )
        req = ApprovalRequest(request_id="req_type")
        assert req.approval_type == ApprovalType.SEQUENTIAL

    def test_status(self):
        """Kiểm tra trạng thái mặc định là PENDING."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalRequest,
            ApprovalStatus,
        )
        req = ApprovalRequest(request_id="req_stat")
        assert req.status == ApprovalStatus.PENDING

    def test_to_dict(self):
        """Kiểm tra chuyển ApprovalRequest sang dict."""
        from midicoder.packs.cp42_approval.models import ApprovalRequest
        req = ApprovalRequest(
            request_id="req_dict",
            title="Test title",
            description="Test desc",
            entity_type="leave",
            entity_id="leave_01",
            initiator_id="user_001",
            total_steps=2,
        )
        d = req.to_dict()
        assert d["request_id"] == "req_dict"
        assert d["title"] == "Test title"
        assert d["description"] == "Test desc"
        assert d["entity_type"] == "leave"
        assert d["entity_id"] == "leave_01"
        assert d["approval_type"] == "sequential"
        assert d["status"] == "pending"
        assert d["initiator_id"] == "user_001"
        assert d["total_steps"] == 2
        assert d["current_step"] == 1
        assert d["metadata"] == {}
        assert "created_at" in d
        assert "updated_at" in d
        assert "deadline" in d

    def test_from_dict_roundtrip(self):
        """Kiểm tra serialize/deserialize ApprovalRequest qua to_dict/from_dict."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalRequest,
            ApprovalStatus,
            ApprovalType,
        )
        req = ApprovalRequest(
            request_id="req_rt",
            title="Roundtrip",
            entity_type="purchase_order",
            entity_id="po_99",
            approval_type=ApprovalType.PARALLEL,
            status=ApprovalStatus.PENDING,
            initiator_id="user_002",
            total_steps=5,
            metadata={"priority": "high"},
        )
        d = req.to_dict()
        restored = ApprovalRequest.from_dict(d)
        assert restored.request_id == "req_rt"
        assert restored.title == "Roundtrip"
        assert restored.approval_type == ApprovalType.PARALLEL
        assert restored.total_steps == 5
        assert restored.metadata == {"priority": "high"}

    def test_from_dict_without_optional(self):
        """Kiểm tra từ dict chỉ có request_id vẫn tạo được đối tượng hợp lệ."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalRequest,
            ApprovalStatus,
            ApprovalType,
        )
        data = {"request_id": "req_min"}
        req = ApprovalRequest.from_dict(data)
        assert req.request_id == "req_min"
        assert req.approval_type == ApprovalType.SEQUENTIAL
        assert req.status == ApprovalStatus.PENDING
        assert req.current_step == 1
        assert req.total_steps == 1

    def test_default_values(self):
        """Kiểm tra các giá trị mặc định của ApprovalRequest."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalRequest,
            ApprovalStatus,
            ApprovalType,
        )
        req = ApprovalRequest(request_id="req_def")
        assert req.title == ""
        assert req.description == ""
        assert req.entity_type == ""
        assert req.entity_id == ""
        assert req.approval_type == ApprovalType.SEQUENTIAL
        assert req.status == ApprovalStatus.PENDING
        assert req.initiator_id == ""
        assert req.current_step == 1
        assert req.total_steps == 1
        assert req.metadata == {}

    def test_with_metadata(self):
        """Kiểm tra metadata được bảo toàn qua to_dict/from_dict."""
        from midicoder.packs.cp42_approval.models import ApprovalRequest
        metadata = {"key1": "value1", "key2": [1, 2, 3]}
        req = ApprovalRequest(
            request_id="req_meta",
            metadata=metadata,
        )
        d = req.to_dict()
        restored = ApprovalRequest.from_dict(d)
        assert restored.metadata == metadata

    def test_total_steps_validation(self):
        """Kiểm tra total_steps nhỏ hơn 1 sẽ ném lỗi."""
        from midicoder.packs.cp42_approval.models import ApprovalRequest
        with pytest.raises(MidicoderError):
            ApprovalRequest(request_id="req_bad", total_steps=0)


# ===========================================================================
# Test ApprovalStep
# ===========================================================================


class TestApprovalStep:
    """Kiểm tra ApprovalStep — tạo, validate, serialize."""

    def test_create_valid_step(self):
        from midicoder.packs.cp42_approval.models import (
            ApprovalStep,
            ApprovalStatus,
        )
        step = ApprovalStep(
            step_id="step_001",
            request_id="req_001",
            step_number=1,
            approver_id="manager_001",
            approver_role="manager",
        )
        assert step.step_id == "step_001"
        assert step.request_id == "req_001"
        assert step.step_number == 1
        assert step.approver_id == "manager_001"
        assert step.approver_role == "manager"
        assert step.status == ApprovalStatus.PENDING
        assert step.is_parallel is False

    def test_empty_id_raises(self):
        """Kiểm tra tạo bước với step_id rỗng sẽ ném lỗi."""
        from midicoder.packs.cp42_approval.models import ApprovalStep
        with pytest.raises(MidicoderError):
            ApprovalStep(
                step_id="",
                request_id="req_001",
                step_number=1,
                approver_id="m_001",
                approver_role="manager",
            )

    def test_auto_timestamp(self):
        """Kiểm tra tự động tạo timestamp và action_deadline."""
        from midicoder.packs.cp42_approval.models import ApprovalStep
        step = ApprovalStep(
            step_id="step_ts",
            request_id="req_ts",
            step_number=1,
            approver_id="m_001",
            approver_role="manager",
        )
        assert step.created_at is not None
        assert step.action_deadline is not None

    def test_approver_fields(self):
        """Kiểm tra các trường của người phê duyệt."""
        from midicoder.packs.cp42_approval.models import ApprovalStep
        step = ApprovalStep(
            step_id="step_appr",
            request_id="req_appr",
            step_number=2,
            approver_id="director_01",
            approver_role="department_head",
        )
        assert step.approver_id == "director_01"
        assert step.approver_role == "department_head"

    def test_to_dict(self):
        """Kiểm tra chuyển ApprovalStep sang dict."""
        from midicoder.packs.cp42_approval.models import ApprovalStep
        step = ApprovalStep(
            step_id="step_d",
            request_id="req_d",
            step_number=3,
            approver_id="u3",
            approver_role="r3",
            is_parallel=True,
            condition_expression="amount > 1000000",
        )
        d = step.to_dict()
        assert d["step_id"] == "step_d"
        assert d["request_id"] == "req_d"
        assert d["step_number"] == 3
        assert d["status"] == "pending"
        assert d["is_parallel"] is True
        assert d["condition_expression"] == "amount > 1000000"
        assert "created_at" in d

    def test_from_dict(self):
        """Kiểm tra tạo ApprovalStep từ dict."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalStep,
            ApprovalStatus,
        )
        step = ApprovalStep(
            step_id="step_fc",
            request_id="req_fc",
            step_number=1,
            approver_id="approver_x",
            approver_role="lead",
            status=ApprovalStatus.APPROVED,
            is_parallel=False,
        )
        d = step.to_dict()
        restored = ApprovalStep.from_dict(d)
        assert restored.step_id == "step_fc"
        assert restored.request_id == "req_fc"
        assert restored.step_number == 1
        assert restored.approver_id == "approver_x"
        assert restored.approver_role == "lead"
        assert restored.status == ApprovalStatus.APPROVED
        assert restored.is_parallel is False

    def test_is_parallel(self):
        """Kiểm tra cờ is_parallel của bước phê duyệt."""
        from midicoder.packs.cp42_approval.models import ApprovalStep
        step = ApprovalStep(
            step_id="step_par",
            request_id="req_par",
            step_number=1,
            approver_id="u1",
            approver_role="r1",
            is_parallel=True,
        )
        assert step.is_parallel is True

    def test_step_number(self):
        """Kiểm tra step_number nhỏ hơn 1 được điều chỉnh về 1."""
        from midicoder.packs.cp42_approval.models import ApprovalStep
        step = ApprovalStep(
            step_id="step_num",
            request_id="req_num",
            step_number=0,
            approver_id="u1",
            approver_role="r1",
        )
        assert step.step_number == 1

    def test_from_dict_without_optional(self):
        """Kiểm tra tạo ApprovalStep từ dict tối thiểu."""
        from midicoder.packs.cp42_approval.models import ApprovalStep
        data = {
            "step_id": "step_min",
            "request_id": "req_min",
            "step_number": 1,
            "approver_id": "u_min",
            "approver_role": "r_min",
        }
        step = ApprovalStep.from_dict(data)
        assert step.step_id == "step_min"
        assert step.is_parallel is False
        assert step.condition_expression is None

    def test_action_deadline_default(self):
        """Kiểm tra action_deadline mặc định là 3 ngày từ thời điểm tạo."""
        from midicoder.packs.cp42_approval.models import ApprovalStep
        step = ApprovalStep(
            step_id="step_dl",
            request_id="req_dl",
            step_number=1,
            approver_id="u1",
            approver_role="r1",
        )
        assert step.action_deadline is not None
        assert step.action_deadline > step.created_at


# ===========================================================================
# Test ApprovalDecision
# ===========================================================================


class TestApprovalDecision:
    """Kiểm tra ApprovalDecision — tạo, validate, serialize."""

    def test_create_valid_decision(self):
        from midicoder.packs.cp42_approval.models import ApprovalDecision
        dec = ApprovalDecision(
            decision_id="dec_001",
            step_id="step_001",
            request_id="req_001",
            approver_id="manager_001",
            decision="approved",
            comment="Đồng ý phê duyệt",
        )
        assert dec.decision_id == "dec_001"
        assert dec.decision == "approved"
        assert dec.comment == "Đồng ý phê duyệt"

    def test_empty_id_raises(self):
        """Kiểm tra tạo quyết định với decision_id rỗng sẽ ném lỗi."""
        from midicoder.packs.cp42_approval.models import ApprovalDecision
        with pytest.raises(MidicoderError):
            ApprovalDecision(
                decision_id="",
                step_id="step_001",
                request_id="req_001",
                approver_id="u1",
                decision="approved",
            )

    def test_decision_validation(self):
        """Kiểm tra decision không hợp lệ sẽ ném lỗi."""
        from midicoder.packs.cp42_approval.models import ApprovalDecision
        with pytest.raises(MidicoderError):
            ApprovalDecision(
                decision_id="dec_bad",
                step_id="step_001",
                request_id="req_001",
                approver_id="u1",
                decision="maybe",
            )

    def test_to_dict(self):
        """Kiểm tra chuyển ApprovalDecision sang dict."""
        from midicoder.packs.cp42_approval.models import ApprovalDecision
        dec = ApprovalDecision(
            decision_id="dec_d",
            step_id="step_d",
            request_id="req_d",
            approver_id="u_d",
            decision="rejected",
            comment="Không đủ hồ sơ",
        )
        d = dec.to_dict()
        assert d["decision_id"] == "dec_d"
        assert d["step_id"] == "step_d"
        assert d["decision"] == "rejected"
        assert d["comment"] == "Không đủ hồ sơ"
        assert "created_at" in d

    def test_from_dict(self):
        """Kiểm tra tạo ApprovalDecision từ dict."""
        from midicoder.packs.cp42_approval.models import ApprovalDecision
        dec = ApprovalDecision(
            decision_id="dec_rt",
            step_id="step_rt",
            request_id="req_rt",
            approver_id="u_rt",
            decision="approved",
            comment="OK",
        )
        d = dec.to_dict()
        restored = ApprovalDecision.from_dict(d)
        assert restored.decision_id == "dec_rt"
        assert restored.decision == "approved"
        assert restored.comment == "OK"
        assert restored.approver_id == "u_rt"

    def test_from_dict_without_optional(self):
        """Kiểm tra từ dict chỉ có các trường bắt buộc."""
        from midicoder.packs.cp42_approval.models import ApprovalDecision
        data = {
            "decision_id": "dec_min",
            "step_id": "step_min",
            "request_id": "req_min",
            "approver_id": "u_min",
        }
        dec = ApprovalDecision.from_dict(data)
        assert dec.decision_id == "dec_min"
        assert dec.decision == "approved"
        assert dec.comment == ""

    def test_comment_default(self):
        """Kiểm tra comment mặc định là chuỗi rỗng."""
        from midicoder.packs.cp42_approval.models import ApprovalDecision
        dec = ApprovalDecision(
            decision_id="dec_comm",
            step_id="step_001",
            request_id="req_001",
            approver_id="u1",
            decision="approved",
        )
        assert dec.comment == ""

    def test_approved_decision(self):
        """Kiểm tra quyết định phê duyệt với comment."""
        from midicoder.packs.cp42_approval.models import ApprovalDecision
        dec = ApprovalDecision(
            decision_id="dec_ok",
            step_id="step_001",
            request_id="req_001",
            approver_id="mgr_001",
            decision="approved",
            comment="Đã xem xét kỹ lưỡng — phê duyệt",
        )
        assert dec.decision == "approved"
        assert "xem xét" in dec.comment


# ===========================================================================
# Test EscalationRule
# ===========================================================================


class TestEscalationRule:
    """Kiểm tra EscalationRule — tạo, validate, serialize."""

    def test_create_valid_rule(self):
        from midicoder.packs.cp42_approval.models import (
            EscalationRule,
            EscalationStrategy,
        )
        rule = EscalationRule(
            rule_id="rule_001",
            request_id="req_001",
            trigger_after_minutes=30,
            escalation_strategy=EscalationStrategy.NEXT_LEVEL,
            target_role="senior_manager",
            target_id="mgr_01",
        )
        assert rule.rule_id == "rule_001"
        assert rule.request_id == "req_001"
        assert rule.trigger_after_minutes == 30
        assert rule.escalation_strategy == EscalationStrategy.NEXT_LEVEL
        assert rule.is_active is True

    def test_empty_id_raises(self):
        """Kiểm tra tạo quy tắc với rule_id rỗng sẽ ném lỗi."""
        from midicoder.packs.cp42_approval.models import EscalationRule
        with pytest.raises(MidicoderError):
            EscalationRule(rule_id="", request_id="req_001")

    def test_strategy(self):
        """Kiểm tra chiến lược leo thang khác nhau."""
        from midicoder.packs.cp42_approval.models import (
            EscalationRule,
            EscalationStrategy,
        )
        rule = EscalationRule(
            rule_id="rule_strat",
            request_id="req_strat",
            escalation_strategy=EscalationStrategy.MANAGER,
        )
        assert rule.escalation_strategy == EscalationStrategy.MANAGER

    def test_to_dict(self):
        """Kiểm tra chuyển EscalationRule sang dict."""
        from midicoder.packs.cp42_approval.models import (
            EscalationRule,
            EscalationStrategy,
        )
        rule = EscalationRule(
            rule_id="rule_d",
            request_id="req_d",
            trigger_after_minutes=120,
            escalation_strategy=EscalationStrategy.NEXT_ROLE,
            target_role="vp",
            target_id="vp_01",
            max_escalation_level=5,
            is_active=False,
        )
        d = rule.to_dict()
        assert d["rule_id"] == "rule_d"
        assert d["escalation_strategy"] == "next_role"
        assert d["target_role"] == "vp"
        assert d["target_id"] == "vp_01"
        assert d["max_escalation_level"] == 5
        assert d["is_active"] is False

    def test_from_dict(self):
        """Kiểm tra tạo EscalationRule từ dict."""
        from midicoder.packs.cp42_approval.models import (
            EscalationRule,
            EscalationStrategy,
        )
        rule = EscalationRule(
            rule_id="rule_fc",
            request_id="req_fc",
            trigger_after_minutes=45,
            escalation_strategy=EscalationStrategy.TIMEOUT,
            max_escalation_level=2,
        )
        d = rule.to_dict()
        restored = EscalationRule.from_dict(d)
        assert restored.rule_id == "rule_fc"
        assert restored.escalation_strategy == EscalationStrategy.TIMEOUT
        assert restored.trigger_after_minutes == 45
        assert restored.max_escalation_level == 2

    def test_defaults(self):
        """Kiểm tra các giá trị mặc định của EscalationRule."""
        from midicoder.packs.cp42_approval.models import (
            EscalationRule,
            EscalationStrategy,
        )
        rule = EscalationRule(rule_id="rule_def", request_id="req_def")
        assert rule.trigger_after_minutes == 60
        assert rule.escalation_strategy == EscalationStrategy.NEXT_LEVEL
        assert rule.max_escalation_level == 3
        assert rule.is_active is True
        assert rule.target_role == ""
        assert rule.target_id == ""

    def test_target_role(self):
        """Kiểm tra target_role được lưu đúng."""
        from midicoder.packs.cp42_approval.models import EscalationRule
        rule = EscalationRule(
            rule_id="rule_tr",
            request_id="req_tr",
            target_role="ceo",
        )
        assert rule.target_role == "ceo"

    def test_max_level(self):
        """Kiểm tra max_escalation_level được lưu đúng."""
        from midicoder.packs.cp42_approval.models import EscalationRule
        rule = EscalationRule(
            rule_id="rule_ml",
            request_id="req_ml",
            max_escalation_level=10,
        )
        assert rule.max_escalation_level == 10


# ===========================================================================
# Test DelegationRecord
# ===========================================================================


class TestDelegationRecord:
    """Kiểm tra DelegationRecord — tạo, validate, is_valid_at, serialize."""

    def test_create_valid_delegation(self):
        from midicoder.packs.cp42_approval.models import (
            DelegationRecord,
            DelegationType,
        )
        now = datetime.now(timezone.utc)
        del_rec = DelegationRecord(
            delegation_id="del_001",
            delegator_id="manager_01",
            delegatee_id="assistant_01",
            delegation_type=DelegationType.TEMPORARY,
            scope="req_001",
            valid_from=now,
            valid_until=now + timedelta(days=7),
        )
        assert del_rec.delegation_id == "del_001"
        assert del_rec.delegator_id == "manager_01"
        assert del_rec.delegatee_id == "assistant_01"
        assert del_rec.delegation_type == DelegationType.TEMPORARY
        assert del_rec.is_active is True

    def test_empty_id_raises(self):
        """Kiểm tra tạo ủy quyền với delegation_id rỗng sẽ ném lỗi."""
        from midicoder.packs.cp42_approval.models import DelegationRecord
        with pytest.raises(MidicoderError):
            DelegationRecord(
                delegation_id="",
                delegator_id="u1",
                delegatee_id="u2",
            )

    def test_delegation_type(self):
        """Kiểm tra các loại ủy quyền khác nhau."""
        from midicoder.packs.cp42_approval.models import (
            DelegationRecord,
            DelegationType,
        )
        del_perm = DelegationRecord(
            delegation_id="del_perm",
            delegator_id="u1",
            delegatee_id="u2",
            delegation_type=DelegationType.PERMANENT,
        )
        del_cond = DelegationRecord(
            delegation_id="del_cond",
            delegator_id="u1",
            delegatee_id="u2",
            delegation_type=DelegationType.CONDITIONAL,
        )
        assert del_perm.delegation_type == DelegationType.PERMANENT
        assert del_cond.delegation_type == DelegationType.CONDITIONAL

    def test_to_dict(self):
        """Kiểm tra chuyển DelegationRecord sang dict."""
        from midicoder.packs.cp42_approval.models import (
            DelegationRecord,
            DelegationType,
        )
        now = datetime.now(timezone.utc)
        del_rec = DelegationRecord(
            delegation_id="del_d",
            delegator_id="u1",
            delegatee_id="u2",
            delegation_type=DelegationType.TEMPORARY,
            scope="req_scope",
            valid_until=now + timedelta(days=3),
        )
        d = del_rec.to_dict()
        assert d["delegation_id"] == "del_d"
        assert d["delegation_type"] == "temporary"
        assert d["scope"] == "req_scope"
        assert d["is_active"] is True
        assert "valid_from" in d
        assert "valid_until" in d

    def test_from_dict(self):
        """Kiểm tra tạo DelegationRecord từ dict."""
        from midicoder.packs.cp42_approval.models import (
            DelegationRecord,
            DelegationType,
        )
        now = datetime.now(timezone.utc)
        del_rec = DelegationRecord(
            delegation_id="del_fc",
            delegator_id="u1",
            delegatee_id="u2",
            delegation_type=DelegationType.PERMANENT,
            scope="*",
            is_active=True,
        )
        d = del_rec.to_dict()
        restored = DelegationRecord.from_dict(d)
        assert restored.delegation_id == "del_fc"
        assert restored.delegation_type == DelegationType.PERMANENT
        assert restored.scope == "*"
        assert restored.is_active is True

    def test_valid_until(self):
        """Kiểm tra valid_until được lưu đúng."""
        from midicoder.packs.cp42_approval.models import DelegationRecord
        now = datetime.now(timezone.utc)
        del_rec = DelegationRecord(
            delegation_id="del_until",
            delegator_id="u1",
            delegatee_id="u2",
            valid_until=now + timedelta(days=1),
        )
        assert del_rec.valid_until is not None

    def test_is_valid_at(self):
        """Kiểm tra ủy quyền còn hiệu lực tại thời điểm hiện tại."""
        from midicoder.packs.cp42_approval.models import DelegationRecord
        now = datetime.now(timezone.utc)
        del_rec = DelegationRecord(
            delegation_id="del_valid",
            delegator_id="u1",
            delegatee_id="u2",
            valid_from=now - timedelta(hours=1),
            valid_until=now + timedelta(hours=1),
        )
        assert del_rec.is_valid_at(now) is True

    def test_is_valid_at_expired(self):
        """Kiểm tra ủy quyền hết hạn tại thời điểm hiện tại."""
        from midicoder.packs.cp42_approval.models import DelegationRecord
        now = datetime.now(timezone.utc)
        del_rec = DelegationRecord(
            delegation_id="del_expired",
            delegator_id="u1",
            delegatee_id="u2",
            valid_from=now - timedelta(hours=10),
            valid_until=now - timedelta(hours=5),
        )
        assert del_rec.is_valid_at(now) is False


# ===========================================================================
# Test ApprovalEngine
# ===========================================================================


class TestApprovalEngine:
    """Kiểm tra ApprovalEngine — toàn bộ workflow phê duyệt."""

    def _make_request(
        self,
        request_id: str = "req_eng_001",
        title: str = "Test",
        initiator_id: str = "initiator_01",
        total_steps: int = 3,
        **kwargs,
    ) -> "ApprovalRequest":
        from midicoder.packs.cp42_approval.models import ApprovalRequest
        defaults = dict(
            request_id=request_id,
            title=title,
            initiator_id=initiator_id,
            total_steps=total_steps,
        )
        defaults.update(kwargs)
        return ApprovalRequest(**defaults)

    def _make_step(
        self,
        step_id: str,
        request_id: str,
        step_number: int,
        approver_id: str,
        approver_role: str = "manager",
        **kwargs,
    ) -> "ApprovalStep":
        from midicoder.packs.cp42_approval.models import ApprovalStep
        return ApprovalStep(
            step_id=step_id,
            request_id=request_id,
            step_number=step_number,
            approver_id=approver_id,
            approver_role=approver_role,
            **kwargs,
        )

    def test_create_request(self):
        """Kiểm tra tạo yêu cầu phê duyệt mới."""
        from midicoder.packs.cp42_approval.models import ApprovalEngine
        engine = ApprovalEngine()
        req = self._make_request()
        result_id = engine.create_request(req)
        assert result_id == "req_eng_001"
        assert "req_eng_001" in engine.requests

    def test_get_request(self):
        """Kiểm tra lấy yêu cầu theo ID."""
        from midicoder.packs.cp42_approval.models import ApprovalEngine
        engine = ApprovalEngine()
        req = self._make_request()
        engine.create_request(req)
        fetched = engine.get_request("req_eng_001")
        assert fetched.request_id == "req_eng_001"
        assert fetched.initiator_id == "initiator_01"

    def test_get_nonexistent_request_raises(self):
        """Kiểm tra lấy yêu cầu không tồn tại sẽ ném lỗi."""
        from midicoder.packs.cp42_approval.models import ApprovalEngine
        engine = ApprovalEngine()
        with pytest.raises(MidicoderError):
            engine.get_request("nonexistent")

    def test_create_duplicate_request_raises(self):
        """Kiểm tra tạo yêu cầu trùng ID sẽ ném lỗi."""
        from midicoder.packs.cp42_approval.models import ApprovalEngine
        engine = ApprovalEngine()
        req = self._make_request()
        engine.create_request(req)
        with pytest.raises(MidicoderError):
            engine.create_request(req)

    def test_decide_approves_step(self):
        """Kiểm tra phê duyệt bước trong quy trình SINGLE."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalEngine,
            ApprovalDecision,
            ApprovalType,
        )
        engine = ApprovalEngine()
        req = self._make_request()
        req.approval_type = ApprovalType.SINGLE
        engine.create_request(req)
        step = self._make_step("step_001", "req_eng_001", 1, "approver_01")
        engine.steps["step_001"] = step
        decision = engine.decide("step_001", "approver_01", "approved", "Đồng ý")
        assert isinstance(decision, ApprovalDecision)
        assert decision.decision == "approved"
        assert decision.comment == "Đồng ý"
        assert decision.step_id == "step_001"

    def test_decide_rejects_step(self):
        """Kiểm tra từ chối bước trong quy trình SINGLE."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalEngine,
            ApprovalStatus,
            ApprovalType,
        )
        engine = ApprovalEngine()
        req = self._make_request()
        req.approval_type = ApprovalType.SINGLE
        engine.create_request(req)
        step = self._make_step("step_002", "req_eng_001", 1, "approver_02")
        engine.steps["step_002"] = step
        engine.decide("step_002", "approver_02", "rejected", "Không đồng ý")
        assert engine.requests["req_eng_001"].status == ApprovalStatus.REJECTED

    def test_decide_wrong_approver_raises(self):
        """Kiểm tra người phê duyệt sai sẽ ném lỗi."""
        from midicoder.packs.cp42_approval.models import ApprovalEngine
        engine = ApprovalEngine()
        req = self._make_request()
        engine.create_request(req)
        step = self._make_step("step_003", "req_eng_001", 1, "approver_03")
        engine.steps["step_003"] = step
        with pytest.raises(MidicoderError):
            engine.decide("step_003", "wrong_user", "approved")

    def test_decide_nonexistent_step_raises(self):
        """Kiểm tra quyết định bước không tồn tại sẽ ném lỗi."""
        from midicoder.packs.cp42_approval.models import ApprovalEngine
        engine = ApprovalEngine()
        with pytest.raises(MidicoderError):
            engine.decide("fake_step", "approver_01", "approved")

    def test_decide_already_decided_raises(self):
        """Kiểm tra quyết định bước đã có quyết định sẽ ném lỗi."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalEngine,
            ApprovalType,
        )
        engine = ApprovalEngine()
        req = self._make_request()
        req.approval_type = ApprovalType.SINGLE
        engine.create_request(req)
        step = self._make_step("step_004", "req_eng_001", 1, "approver_04")
        engine.steps["step_004"] = step
        engine.decide("step_004", "approver_04", "approved")
        with pytest.raises(MidicoderError):
            engine.decide("step_004", "approver_04", "rejected")

    def test_sequential_advance(self):
        """Kiểm tra chuyển bước tiếp theo trong quy trình SEQUENTIAL."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalEngine,
            ApprovalStatus,
            ApprovalType,
        )
        engine = ApprovalEngine()
        req = self._make_request(total_steps=3)
        req.approval_type = ApprovalType.SEQUENTIAL
        engine.create_request(req)
        step1 = self._make_step("seq_1", "req_eng_001", 1, "app_1")
        step2 = self._make_step("seq_2", "req_eng_001", 2, "app_2")
        step3 = self._make_step("seq_3", "req_eng_001", 3, "app_3")
        engine.steps.update({
            "seq_1": step1,
            "seq_2": step2,
            "seq_3": step3,
        })
        engine.decide("seq_1", "app_1", "approved")
        assert engine.requests["req_eng_001"].current_step == 2
        engine.decide("seq_2", "app_2", "approved")
        assert engine.requests["req_eng_001"].current_step == 3
        engine.decide("seq_3", "app_3", "approved")
        assert engine.requests["req_eng_001"].status == ApprovalStatus.APPROVED

    def test_sequential_reject_stops_chain(self):
        """Kiểm tra từ chối trong SEQUENTIAL sẽ dừng toàn bộ chuỗi."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalEngine,
            ApprovalStatus,
            ApprovalType,
        )
        engine = ApprovalEngine()
        req = self._make_request(total_steps=3)
        req.approval_type = ApprovalType.SEQUENTIAL
        engine.create_request(req)
        step1 = self._make_step("seq_r1", "req_eng_001", 1, "app_r1")
        step2 = self._make_step("seq_r2", "req_eng_001", 2, "app_r2")
        engine.steps.update({"seq_r1": step1, "seq_r2": step2})
        engine.decide("seq_r1", "app_r1", "rejected")
        assert engine.requests["req_eng_001"].status == ApprovalStatus.REJECTED

    def test_single_approve(self):
        """Kiểm tra quy trình SINGLE hoàn tất ngay sau quyết định."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalEngine,
            ApprovalStatus,
            ApprovalType,
        )
        engine = ApprovalEngine()
        req = self._make_request(total_steps=1)
        req.approval_type = ApprovalType.SINGLE
        engine.create_request(req)
        step = self._make_step("single_1", "req_eng_001", 1, "boss")
        engine.steps["single_1"] = step
        engine.decide("single_1", "boss", "approved")
        assert engine.requests["req_eng_001"].status == ApprovalStatus.APPROVED

    def test_delegate(self):
        """Kiểm tra ủy quyền phê duyệt."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalEngine,
            ApprovalStatus,
            DelegationType,
        )
        engine = ApprovalEngine()
        req = self._make_request()
        engine.create_request(req)
        delegation = engine.delegate(
            "req_eng_001", "manager_01", "assistant_01",
            delegation_type=DelegationType.TEMPORARY,
        )
        assert delegation.delegator_id == "manager_01"
        assert delegation.delegatee_id == "assistant_01"
        assert engine.requests["req_eng_001"].status == ApprovalStatus.DELEGATED

    def test_delegate_self_raises(self):
        """Kiểm tra ủy quyền cho chính mình sẽ ném lỗi."""
        from midicoder.packs.cp42_approval.models import ApprovalEngine
        engine = ApprovalEngine()
        req = self._make_request()
        engine.create_request(req)
        with pytest.raises(MidicoderError):
            engine.delegate("req_eng_001", "user_01", "user_01")

    def test_delegate_nonexistent_request_raises(self):
        """Kiểm tra ủy quyền yêu cầu không tồn tại sẽ ném lỗi."""
        from midicoder.packs.cp42_approval.models import ApprovalEngine
        engine = ApprovalEngine()
        with pytest.raises(MidicoderError):
            engine.delegate("fake_req", "u1", "u2")

    def test_escalate(self):
        """Kiểm tra leo thang yêu cầu phê duyệt."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalEngine,
            ApprovalStatus,
            EscalationRule,
            EscalationStrategy,
        )
        engine = ApprovalEngine()
        req = self._make_request()
        engine.create_request(req)
        step = self._make_step("esc_1", "req_eng_001", 1, "approver_esc")
        engine.steps["esc_1"] = step
        rule = EscalationRule(
            rule_id="rule_esc",
            request_id="req_eng_001",
            escalation_strategy=EscalationStrategy.NEXT_LEVEL,
            target_role="senior_director",
            target_id="director_01",
        )
        engine.escalation_rules["rule_esc"] = rule
        escalated = engine.escalate("req_eng_001")
        assert "rule_esc" in escalated
        assert engine.requests["req_eng_001"].status == ApprovalStatus.ESCALATED
        assert engine.steps["esc_1"].approver_role == "senior_director"
        assert engine.steps["esc_1"].approver_id == "director_01"

    def test_escalate_no_rules_raises(self):
        """Kiểm tra leo thang không có quy tắc sẽ ném lỗi."""
        from midicoder.packs.cp42_approval.models import ApprovalEngine
        engine = ApprovalEngine()
        req = self._make_request()
        engine.create_request(req)
        with pytest.raises(MidicoderError):
            engine.escalate("req_eng_001")

    def test_escalate_nonexistent_request_raises(self):
        """Kiểm tra leo thang yêu cầu không tồn tại sẽ ném lỗi."""
        from midicoder.packs.cp42_approval.models import ApprovalEngine
        engine = ApprovalEngine()
        with pytest.raises(MidicoderError):
            engine.escalate("fake_req")

    def test_check_deadlines(self):
        """Kiểm tra kiểm tra thời hạn khi chưa có yêu cầu hết hạn."""
        from midicoder.packs.cp42_approval.models import ApprovalEngine
        engine = ApprovalEngine()
        req = self._make_request()
        engine.create_request(req)
        expired = engine.check_deadlines()
        assert expired == []

    def test_check_deadlines_expires_request(self):
        """Kiểm tra đánh dấu yêu cầu hết hạn."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalEngine,
            ApprovalStatus,
        )
        engine = ApprovalEngine()
        req = self._make_request()
        req.deadline = datetime.now(timezone.utc) - timedelta(days=1)
        engine.create_request(req)
        expired = engine.check_deadlines()
        assert "req_eng_001" in expired
        assert engine.requests["req_eng_001"].status == ApprovalStatus.EXPIRED

    def test_detect_cycle_sequential_same_approver_raises(self):
        """Kiểm tra phát hiện chu trình với cùng approver trong SEQUENTIAL."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalEngine,
            ApprovalType,
        )
        engine = ApprovalEngine()
        req = self._make_request()
        req.approval_type = ApprovalType.SEQUENTIAL
        engine.create_request(req)
        step1 = self._make_step("cycle_1", "req_eng_001", 1, "duplicate_app")
        step2 = self._make_step("cycle_2", "req_eng_001", 2, "duplicate_app")
        engine.steps.update({"cycle_1": step1, "cycle_2": step2})
        with pytest.raises(MidicoderError):
            engine.detect_cycle("req_eng_001")

    def test_detect_cycle_no_cycle(self):
        """Kiểm tra không phát hiện chu trình khi approvers khác nhau."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalEngine,
            ApprovalType,
        )
        engine = ApprovalEngine()
        req = self._make_request()
        req.approval_type = ApprovalType.SEQUENTIAL
        engine.create_request(req)
        step1 = self._make_step("nocycle_1", "req_eng_001", 1, "app_a")
        step2 = self._make_step("nocycle_2", "req_eng_001", 2, "app_b")
        engine.steps.update({"nocycle_1": step1, "nocycle_2": step2})
        result = engine.detect_cycle("req_eng_001")
        assert result is False

    def test_detect_cycle_nonexistent_request_raises(self):
        """Kiểm tra phát hiện chu trình với yêu cầu không tồn tại."""
        from midicoder.packs.cp42_approval.models import ApprovalEngine
        engine = ApprovalEngine()
        with pytest.raises(MidicoderError):
            engine.detect_cycle("fake_req")

    def test_resolve_approver_no_delegation(self):
        """Kiểm tra giải quyết người phê duyệt khi không có ủy quyền."""
        from midicoder.packs.cp42_approval.models import ApprovalEngine
        engine = ApprovalEngine()
        resolved = engine.resolve_approver("original_approver")
        assert resolved == "original_approver"

    def test_resolve_approver_with_delegation(self):
        """Kiểm tra giải quyết người phê duyệt với ủy quyền hiệu lực."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalEngine,
            DelegationRecord,
            DelegationType,
        )
        engine = ApprovalEngine()
        now = datetime.now(timezone.utc)
        del_rec = DelegationRecord(
            delegation_id="del_res",
            delegator_id="manager_x",
            delegatee_id="delegate_y",
            delegation_type=DelegationType.TEMPORARY,
            valid_from=now - timedelta(hours=1),
            valid_until=now + timedelta(hours=1),
        )
        engine.delegations["del_res"] = del_rec
        resolved = engine.resolve_approver("manager_x")
        assert resolved == "delegate_y"

    def test_resolve_approver_expired_delegation(self):
        """Kiểm tra giải quyết người phê duyệt với ủy quyền hết hạn."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalEngine,
            DelegationRecord,
            DelegationType,
        )
        engine = ApprovalEngine()
        now = datetime.now(timezone.utc)
        del_rec = DelegationRecord(
            delegation_id="del_exp",
            delegator_id="manager_old",
            delegatee_id="delegate_old",
            delegation_type=DelegationType.TEMPORARY,
            valid_from=now - timedelta(days=2),
            valid_until=now - timedelta(days=1),
        )
        engine.delegations["del_exp"] = del_rec
        resolved = engine.resolve_approver("manager_old")
        assert resolved == "manager_old"

    def test_get_pending_approvals(self):
        """Kiểm tra lấy danh sách yêu cầu đang chờ xử lý."""
        from midicoder.packs.cp42_approval.models import ApprovalEngine
        engine = ApprovalEngine()
        req = self._make_request()
        engine.create_request(req)
        step = self._make_step("pending_1", "req_eng_001", 1, "pending_user")
        engine.steps["pending_1"] = step
        pending = engine.get_pending_approvals("pending_user")
        assert len(pending) == 1
        assert pending[0].request_id == "req_eng_001"

    def test_get_pending_approvals_empty(self):
        """Kiểm tra lấy danh sách yêu cầu khi không có gì đang chờ."""
        from midicoder.packs.cp42_approval.models import ApprovalEngine
        engine = ApprovalEngine()
        pending = engine.get_pending_approvals("nobody")
        assert pending == []

    def test_get_pending_approvals_with_delegation(self):
        """Kiểm tra lấy yêu cầu chờ qua ủy quyền."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalEngine,
            DelegationRecord,
            DelegationType,
        )
        engine = ApprovalEngine()
        req = self._make_request()
        engine.create_request(req)
        step = self._make_step("del_pend_1", "req_eng_001", 1, "original_approver")
        engine.steps["del_pend_1"] = step
        now = datetime.now(timezone.utc)
        del_rec = DelegationRecord(
            delegation_id="del_pend",
            delegator_id="original_approver",
            delegatee_id="delegate_approver",
            delegation_type=DelegationType.TEMPORARY,
            valid_from=now - timedelta(hours=1),
            valid_until=now + timedelta(hours=1),
        )
        engine.delegations["del_pend"] = del_rec
        pending = engine.get_pending_approvals("delegate_approver")
        assert len(pending) == 1
        assert pending[0].request_id == "req_eng_001"

    def test_get_decisions(self):
        """Kiểm tra lấy danh sách quyết định cho yêu cầu."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalEngine,
            ApprovalType,
        )
        engine = ApprovalEngine()
        req = self._make_request(total_steps=2)
        req.approval_type = ApprovalType.SEQUENTIAL
        engine.create_request(req)
        step1 = self._make_step("dec_s1", "req_eng_001", 1, "d_app_1")
        step2 = self._make_step("dec_s2", "req_eng_001", 2, "d_app_2")
        engine.steps.update({"dec_s1": step1, "dec_s2": step2})
        engine.decide("dec_s1", "d_app_1", "approved", "Buoc 1 OK")
        engine.decide("dec_s2", "d_app_2", "approved", "Buoc 2 OK")
        decisions = engine.get_decisions("req_eng_001")
        assert len(decisions) == 2
        assert decisions[0].comment == "Buoc 1 OK"

    def test_get_decisions_nonexistent_request_raises(self):
        """Kiểm tra lấy quyết định của yêu cầu không tồn tại."""
        from midicoder.packs.cp42_approval.models import ApprovalEngine
        engine = ApprovalEngine()
        with pytest.raises(MidicoderError):
            engine.get_decisions("fake_req")

    def test_get_steps_for_request(self):
        """Kiểm tra lấy danh sách bước sắp xếp theo step_number."""
        from midicoder.packs.cp42_approval.models import ApprovalEngine
        engine = ApprovalEngine()
        req = self._make_request(total_steps=3)
        engine.create_request(req)
        engine.steps["gs_1"] = self._make_step("gs_1", "req_eng_001", 3, "app_c")
        engine.steps["gs_2"] = self._make_step("gs_2", "req_eng_001", 1, "app_a")
        engine.steps["gs_3"] = self._make_step("gs_3", "req_eng_001", 2, "app_b")
        steps = engine.get_steps_for_request("req_eng_001")
        assert len(steps) == 3
        assert steps[0].step_number == 1
        assert steps[1].step_number == 2
        assert steps[2].step_number == 3

    def test_get_steps_for_request_nonexistent_raises(self):
        """Kiểm tra lấy bước của yêu cầu không tồn tại."""
        from midicoder.packs.cp42_approval.models import ApprovalEngine
        engine = ApprovalEngine()
        with pytest.raises(MidicoderError):
            engine.get_steps_for_request("fake_req")

    def test_get_active_delegations(self):
        """Kiểm tra lấy danh sách ủy quyền đang hoạt động."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalEngine,
            DelegationRecord,
            DelegationType,
        )
        engine = ApprovalEngine()
        now = datetime.now(timezone.utc)
        active_del = DelegationRecord(
            delegation_id="active_d",
            delegator_id="user_active",
            delegatee_id="user_target",
            delegation_type=DelegationType.TEMPORARY,
            valid_from=now - timedelta(hours=1),
            valid_until=now + timedelta(hours=1),
        )
        engine.delegations["active_d"] = active_del
        delegations = engine.get_active_delegations("user_active")
        assert len(delegations) == 1
        assert delegations[0].delegation_id == "active_d"

    def test_get_active_delegations_expired_excluded(self):
        """Kiểm tra ủy quyền hết hạn bị loại khỏi danh sách."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalEngine,
            DelegationRecord,
            DelegationType,
        )
        engine = ApprovalEngine()
        now = datetime.now(timezone.utc)
        expired_del = DelegationRecord(
            delegation_id="expired_d",
            delegator_id="user_old",
            delegatee_id="user_target_old",
            delegation_type=DelegationType.TEMPORARY,
            valid_from=now - timedelta(days=3),
            valid_until=now - timedelta(days=1),
        )
        engine.delegations["expired_d"] = expired_del
        delegations = engine.get_active_delegations("user_old")
        assert len(delegations) == 0

    def test_parallel_approval_all_approved(self):
        """Kiểm tra phê duyệt song song -- tất cả đều phê duyệt."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalEngine,
            ApprovalStatus,
            ApprovalType,
        )
        engine = ApprovalEngine()
        req = self._make_request(total_steps=2)
        req.approval_type = ApprovalType.PARALLEL
        engine.create_request(req)
        s1 = self._make_step("par_1", "req_eng_001", 1, "p_app_1", is_parallel=True)
        s2 = self._make_step("par_2", "req_eng_001", 2, "p_app_2", is_parallel=True)
        engine.steps.update({"par_1": s1, "par_2": s2})
        engine.decide("par_1", "p_app_1", "approved")
        engine.decide("par_2", "p_app_2", "approved")
        assert engine.requests["req_eng_001"].status == ApprovalStatus.APPROVED

    def test_parallel_approval_one_rejected(self):
        """Kiểm tra phê duyệt song song -- một người từ chối."""
        from midicoder.packs.cp42_approval.models import (
            ApprovalEngine,
            ApprovalStatus,
            ApprovalType,
        )
        engine = ApprovalEngine()
        req = self._make_request(total_steps=2)
        req.approval_type = ApprovalType.PARALLEL
        engine.create_request(req)
        s1 = self._make_step("par_r1", "req_eng_001", 1, "p_app_r1", is_parallel=True)
        s2 = self._make_step("par_r2", "req_eng_001", 2, "p_app_r2", is_parallel=True)
        engine.steps.update({"par_r1": s1, "par_r2": s2})
        engine.decide("par_r1", "p_app_r1", "approved")
        engine.decide("par_r2", "p_app_r2", "rejected")
        assert engine.requests["req_eng_001"].status == ApprovalStatus.REJECTED

    def test_engine_empty_collections_on_init(self):
        """Kiểm tra các bộ sưu tập rỗng khi khởi tạo engine."""
        from midicoder.packs.cp42_approval.models import ApprovalEngine
        engine = ApprovalEngine()
        assert engine.requests == {}
        assert engine.steps == {}
        assert engine.decisions == {}
        assert engine.escalation_rules == {}
        assert engine.delegations == {}

    def test_delegation_valid_from_after_valid_until_raises(self):
        """Kiểm tra valid_from sau valid_until sẽ ném lỗi."""
        from midicoder.packs.cp42_approval.models import DelegationRecord
        now = datetime.now(timezone.utc)
        with pytest.raises(MidicoderError):
            DelegationRecord(
                delegation_id="del_bad_order",
                delegator_id="u1",
                delegatee_id="u2",
                valid_from=now + timedelta(days=5),
                valid_until=now + timedelta(days=1),
            )

    def test_step_condition_expression(self):
        """Kiểm tra biểu thức điều kiện của bước phê duyệt."""
        from midicoder.packs.cp42_approval.models import ApprovalStep
        step = ApprovalStep(
            step_id="step_cond",
            request_id="req_cond",
            step_number=1,
            approver_id="cond_app",
            approver_role="cond_role",
            condition_expression="department == 'IT' and amount > 50000000",
        )
        assert step.condition_expression == "department == 'IT' and amount > 50000000"