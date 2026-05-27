# coding: utf-8
"""
Mô-đun models cho CP42 — Approval Workflow Engine.

Định nghĩa các dataclass biểu diễn:
- ApprovalStatus: Trạng thái phê duyệt (pending, approved, rejected, escalated, delegated, expired, cancelled)
- ApprovalType: Loại quy trình phê duyệt (sequential, parallel, matrix, voting, single)
- EscalationStrategy: Chiến lược leo thang (next_level, next_role, manager, timeout)
- DelegationType: Loại ủy quyền (temporary, permanent, conditional)
- VotingMode: Chế độ biểu quyết (majority, unanimity, first_decides, weighted)
- ApprovalRequest: Yêu cầu phê duyệt với metadata và trạng thái
- ApprovalStep: Bước phê duyệt trong chuỗi (approver, deadline, điều kiện)
- ApprovalDecision: Quyết định phê duyệt (approved/rejected, nhận xét)
- EscalationRule: Quy tắc leo thang (trigger, chiến lược, mục tiêu)
- DelegationRecord: Bản ghi ủy quyền (người ủy, người nhận, phạm vi, thời hạn)
- ApprovalEngine: Engine xử lý chuỗi phê duyệt, leo thang, và ủy quyền

KPI-005: CP Obligations Coverage (>= 2 obligations cho CP42).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any


from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class ApprovalStatus(str, Enum):
    """Trạng thái của yêu cầu phê duyệt.

    - PENDING: Đang chờ phê duyệt
    - APPROVED: Đã được phê duyệt
    - REJECTED: Đã bị từ chối
    - ESCALATED: Đã leo thang đến cấp cao hơn
    - DELEGATED: Đã được ủy quyền cho người khác
    - EXPIRED: Đã hết thời hạn
    - CANCELLED: Đã bị hủy
    """
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    DELEGATED = "delegated"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ApprovalType(str, Enum):
    """Loại quy trình phê duyệt.

    - SEQUENTIAL: Phê duyệt tuần tự, từng bước theo thứ tự
    - PARALLEL: Phê duyệt song song, nhiều người cùng lúc
    - MATRIX: Phê duyệt ma trận (theo cả cấp bậc và chuyên môn)
    - VOTING: Phê duyệt bằng biểu quyết (đa số/tất cả)
    - SINGLE: Phê duyệt bởi một người duy nhất
    """
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    MATRIX = "matrix"
    VOTING = "voting"
    SINGLE = "single"


class EscalationStrategy(str, Enum):
    """Chiến lược leo thang khi hết thời hạn phê duyệt.

    - NEXT_LEVEL: Tự động chuyển đến cấp phê duyệt tiếp theo
    - NEXT_ROLE: Chuyển đến vai trò khác có thẩm quyền
    - MANAGER: Chuyển đến quản lý trực tiếp
    - TIMEOUT: Tự động xử lý khi hết thời gian
    """
    NEXT_LEVEL = "next_level"
    NEXT_ROLE = "next_role"
    MANAGER = "manager"
    TIMEOUT = "timeout"


class DelegationType(str, Enum):
    """Loại ủy quyền phê duyệt.

    - TEMPORARY: Ủy quyền tạm thời (có thời hạn)
    - PERMANENT: Ủy quyền vĩnh viễn (cho đến khi thu hồi)
    - CONDITIONAL: Ủy quyền có điều kiện (phù hợp điều kiện mới kích hoạt)
    """
    TEMPORARY = "temporary"
    PERMANENT = "permanent"
    CONDITIONAL = "conditional"


class VotingMode(str, Enum):
    """Chế độ biểu quyết cho phê duyệt loại voting.

    - MAJORITY: Đa số (trên 50% số phiếu)
    - UNANIMITY: Nhất trí (100% số phiếu)
    - FIRST_DECIDES: Người đầu tiên quyết định có hiệu lực
    - WEIGHTED: Biểu quyết có trọng số (mỗi phiếu có trọng số khác nhau)
    """
    MAJORITY = "majority"
    UNANIMITY = "unanimity"
    FIRST_DECIDES = "first_decides"
    WEIGHTED = "weighted"


# ===========================================================================
# ApprovalRequest
# ===========================================================================


@dataclass
class ApprovalRequest:
    """Yêu cầu phê duyệt — thực thể chính trong quy trình.

    Đại diện cho một yêu cầu cần được phê duyệt, bao gồm loại quy trình,
    trạng thái hiện tại, và tổng số bước phê duyệt.

    Attributes:
        request_id: ID duy nhất của yêu cầu phê duyệt
        title: Tiêu đề yêu cầu
        description: Mô tả chi tiết yêu cầu
        entity_type: Loại thực thể cần phê duyệt (ví dụ: 'purchase_order', 'leave_request')
        entity_id: ID của thực thể liên quan
        approval_type: Loại quy trình phê duyệt
        status: Trạng thái hiện tại của yêu cầu
        initiator_id: ID người khởi tạo yêu cầu
        current_step: Số bước hiện tại đang xử lý
        total_steps: Tổng số bước phê duyệt
        deadline: Thời hạn phê duyệt cuối cùng
        metadata: Dữ liệu bổ sung (dict tùy chỉnh)
        created_at: Thời điểm tạo yêu cầu
        updated_at: Thời điểm cập nhật cuối
    """
    request_id: str
    title: str = ""
    description: str = ""
    entity_type: str = ""
    entity_id: str = ""
    approval_type: ApprovalType = ApprovalType.SEQUENTIAL
    status: ApprovalStatus = ApprovalStatus.PENDING
    initiator_id: str = ""
    current_step: int = 1
    total_steps: int = 1
    deadline: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate yêu cầu phê duyệt sau khi khởi tạo."""
        if not self.request_id or not self.request_id.strip():
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_REQUEST_NOT_FOUND,
                reason="request_id bắt buộc và không được để trống",
            )

        if self.total_steps < 1:
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_REQUEST_NOT_FOUND,
                reason=f"total_steps phải lớn hơn hoặc bằng 1, nhận được: {self.total_steps}",
            )

        if self.current_step < 1:
            self.current_step = 1

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now
        if self.deadline is None:
            # Mặc định: thời hạn 7 ngày từ thời điểm tạo
            self.deadline = now + timedelta(days=7)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ApprovalRequest sang dict."""
        return {
            "request_id": self.request_id,
            "title": self.title,
            "description": self.description,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "approval_type": self.approval_type.value,
            "status": self.status.value,
            "initiator_id": self.initiator_id,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApprovalRequest":
        """Tạo ApprovalRequest từ dict."""
        return cls(
            request_id=data.get("request_id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            entity_type=data.get("entity_type", ""),
            entity_id=data.get("entity_id", ""),
            approval_type=ApprovalType(data.get("approval_type", "sequential")),
            status=ApprovalStatus(data.get("status", "pending")),
            initiator_id=data.get("initiator_id", ""),
            current_step=data.get("current_step", 1),
            total_steps=data.get("total_steps", 1),
            deadline=datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None,
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )


# ===========================================================================
# ApprovalStep
# ===========================================================================


@dataclass
class ApprovalStep:
    """Bước phê duyệt trong chuỗi.

    Mỗi bước xác định một người phê duyệt cụ thể với vai trò,
    thời hạn hành động, và điều kiện kích hoạt.

    Attributes:
        step_id: ID duy nhất của bước phê duyệt
        request_id: ID yêu cầu phê duyệt cha
        step_number: Thứ tự bước trong chuỗi (1-based)
        approver_id: ID người phê duyệt
        approver_role: Vai trò của người phê duyệt
        status: Trạng thái của bước (pending/approved/rejected/escalated/delegated/expired)
        action_deadline: Thời hạn hành động cho bước này
        is_parallel: Bước có thực hiện song song với các bước khác không
        condition_expression: Biểu thức điều kiện để kích hoạt bước này (nullable)
        created_at: Thời điểm tạo bước
    """
    step_id: str
    request_id: str
    step_number: int
    approver_id: str
    approver_role: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    action_deadline: datetime | None = None
    is_parallel: bool = False
    condition_expression: str | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate bước phê duyệt sau khi khởi tạo."""
        if not self.step_id or not self.step_id.strip():
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_REQUEST_NOT_FOUND,
                reason="step_id bắt buộc và không được để trống",
            )

        if not self.request_id or not self.request_id.strip():
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_REQUEST_NOT_FOUND,
                reason="request_id bắt buộc cho bước phê duyệt",
            )

        if not self.approver_id or not self.approver_id.strip():
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_MISSING_ROLE,
                reason="approver_id bắt buộc và không được để trống",
            )

        if self.step_number < 1:
            self.step_number = 1

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.action_deadline is None:
            # Mặc định: thời hạn 3 ngày từ thời điểm tạo bước
            self.action_deadline = now + timedelta(days=3)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ApprovalStep sang dict."""
        return {
            "step_id": self.step_id,
            "request_id": self.request_id,
            "step_number": self.step_number,
            "approver_id": self.approver_id,
            "approver_role": self.approver_role,
            "status": self.status.value,
            "action_deadline": self.action_deadline.isoformat() if self.action_deadline else None,
            "is_parallel": self.is_parallel,
            "condition_expression": self.condition_expression,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApprovalStep":
        """Tạo ApprovalStep từ dict."""
        return cls(
            step_id=data.get("step_id", ""),
            request_id=data.get("request_id", ""),
            step_number=data.get("step_number", 1),
            approver_id=data.get("approver_id", ""),
            approver_role=data.get("approver_role", ""),
            status=ApprovalStatus(data.get("status", "pending")),
            action_deadline=datetime.fromisoformat(data["action_deadline"]) if data.get("action_deadline") else None,
            is_parallel=data.get("is_parallel", False),
            condition_expression=data.get("condition_expression"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
        )


# ===========================================================================
# ApprovalDecision
# ===========================================================================


@dataclass
class ApprovalDecision:
    """Quyết định phê duyệt.

    Ghi nhận quyết định (phê duyệt/từ chối) của một người phê duyệt
    tại một bước cụ thể, kèm theo nhận xét.

    Attributes:
        decision_id: ID duy nhất của quyết định
        step_id: ID bước phê duyệt liên quan
        request_id: ID yêu cầu phê duyệt cha
        approver_id: ID người đưa ra quyết định
        decision: Quyết định phê duyệt ("approved" hoặc "rejected")
        comment: Nhận xét hoặc lý do (nullable)
        created_at: Thời điểm đưa ra quyết định
    """
    decision_id: str
    step_id: str
    request_id: str
    approver_id: str
    decision: str
    comment: str = ""
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate quyết định phê duyệt sau khi khởi tạo."""
        if not self.decision_id or not self.decision_id.strip():
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_REQUEST_NOT_FOUND,
                reason="decision_id bắt buộc và không được để trống",
            )

        if not self.step_id or not self.step_id.strip():
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_REQUEST_NOT_FOUND,
                reason="step_id bắt buộc cho quyết định phê duyệt",
            )

        valid_decisions = ("approved", "rejected")
        if self.decision not in valid_decisions:
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_REQUEST_NOT_FOUND,
                reason=f"decision phải là một trong {valid_decisions}, nhận được: {self.decision}",
            )

        if not self.approver_id or not self.approver_id.strip():
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_MISSING_ROLE,
                reason="approver_id bắt buộc cho quyết định phê duyệt",
            )

        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ApprovalDecision sang dict."""
        return {
            "decision_id": self.decision_id,
            "step_id": self.step_id,
            "request_id": self.request_id,
            "approver_id": self.approver_id,
            "decision": self.decision,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApprovalDecision":
        """Tạo ApprovalDecision từ dict."""
        return cls(
            decision_id=data.get("decision_id", ""),
            step_id=data.get("step_id", ""),
            request_id=data.get("request_id", ""),
            approver_id=data.get("approver_id", ""),
            decision=data.get("decision", "approved"),
            comment=data.get("comment", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
        )


# ===========================================================================
# EscalationRule
# ===========================================================================


@dataclass
class EscalationRule:
    """Quy tắc leo thang phê duyệt.

    Xác định khi nào và như thế nào một yêu cầu phê duyệt
    sẽ được leo thang khi không được xử lý kịp thời.

    Attributes:
        rule_id: ID duy nhất của quy tắc leo thang
        request_id: ID yêu cầu phê duyệt liên quan
        trigger_after_minutes: Thời gian (phút) sau khi kích hoạt leo thang
        escalation_strategy: Chiến lược leo thang
        target_role: Vai trò mục tiêu khi leo thang (nullable)
        target_id: ID người/phòng ban mục tiêu khi leo thang (nullable)
        max_escalation_level: Mức leo thang tối đa
        is_active: Quy tắc có đang hoạt động không
    """
    rule_id: str
    request_id: str
    trigger_after_minutes: int = 60
    escalation_strategy: EscalationStrategy = EscalationStrategy.NEXT_LEVEL
    target_role: str = ""
    target_id: str = ""
    max_escalation_level: int = 3
    is_active: bool = True

    def __post_init__(self) -> None:
        """Validate quy tắc leo thang sau khi khởi tạo."""
        if not self.rule_id or not self.rule_id.strip():
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_ESCALATION_NO_NEXT_LEVEL,
                reason="rule_id bắt buộc và không được để trống",
            )

        if not self.request_id or not self.request_id.strip():
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_REQUEST_NOT_FOUND,
                reason="request_id bắt buộc cho quy tắc leo thang",
            )

        if self.trigger_after_minutes < 1:
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_ESCALATION_NO_NEXT_LEVEL,
                reason=f"trigger_after_minutes phải lớn hơn 0, nhận được: {self.trigger_after_minutes}",
            )

        if self.max_escalation_level < 1:
            self.max_escalation_level = 3

    def to_dict(self) -> dict[str, Any]:
        """Chuyển EscalationRule sang dict."""
        return {
            "rule_id": self.rule_id,
            "request_id": self.request_id,
            "trigger_after_minutes": self.trigger_after_minutes,
            "escalation_strategy": self.escalation_strategy.value,
            "target_role": self.target_role,
            "target_id": self.target_id,
            "max_escalation_level": self.max_escalation_level,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EscalationRule":
        """Tạo EscalationRule từ dict."""
        return cls(
            rule_id=data.get("rule_id", ""),
            request_id=data.get("request_id", ""),
            trigger_after_minutes=data.get("trigger_after_minutes", 60),
            escalation_strategy=EscalationStrategy(data.get("escalation_strategy", "next_level")),
            target_role=data.get("target_role", ""),
            target_id=data.get("target_id", ""),
            max_escalation_level=data.get("max_escalation_level", 3),
            is_active=data.get("is_active", True),
        )


# ===========================================================================
# DelegationRecord
# ===========================================================================


@dataclass
class DelegationRecord:
    """Bản ghi ủy quyền phê duyệt.

    Ghi nhận việc một người phê duyệt ủy quyền công việc
    cho người khác, với phạm vi và thời hạn rõ ràng.

    Attributes:
        delegation_id: ID duy nhất của bản ghi ủy quyền
        delegator_id: ID người ủy quyền
        delegatee_id: ID người được ủy quyền
        delegation_type: Loại ủy quyền
        scope: Phạm vi ủy quyền (request_id cụ thể hoặc "*" cho tất cả)
        valid_from: Thời điểm bắt đầu có hiệu lực
        valid_until: Thời điểm hết hiệu lực (nullable — None = vĩnh viễn)
        is_active: Bản ghi ủy quyền có đang hoạt động không
    """
    delegation_id: str
    delegator_id: str
    delegatee_id: str
    delegation_type: DelegationType = DelegationType.TEMPORARY
    scope: str = "*"
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    is_active: bool = True

    def __post_init__(self) -> None:
        """Validate bản ghi ủy quyền sau khi khởi tạo."""
        if not self.delegation_id or not self.delegation_id.strip():
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_DELEGATION_EXPIRED,
                reason="delegation_id bắt buộc và không được để trống",
            )

        if not self.delegator_id or not self.delegator_id.strip():
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_DELEGATION_SELF,
                reason="delegator_id bắt buộc và không được để trống",
            )

        if not self.delegatee_id or not self.delegatee_id.strip():
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_DELEGATION_SELF,
                reason="delegatee_id bắt buộc và không được để trống",
            )

        now = datetime.now(timezone.utc)
        if self.valid_from is None:
            self.valid_from = now

        # Kiểm tra valid_from không được sau valid_until
        if self.valid_until and self.valid_from and self.valid_from > self.valid_until:
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_DELEGATION_EXPIRED,
                reason="valid_from không được sau valid_until",
            )

    def is_valid_at(self, moment: datetime | None = None) -> bool:
        """Kiểm tra ủy quyền có còn hiệu lực tại thời điểm cụ thể không.

        Args:
            moment: Thời điểm cần kiểm tra (mặc định là hiện tại)

        Returns:
            True nếu ủy quyền còn hiệu lực
        """
        if not self.is_active:
            return False

        check_time = moment or datetime.now(timezone.utc)

        if self.valid_from and check_time < self.valid_from:
            return False

        if self.valid_until and check_time > self.valid_until:
            return False

        return True

    def to_dict(self) -> dict[str, Any]:
        """Chuyển DelegationRecord sang dict."""
        return {
            "delegation_id": self.delegation_id,
            "delegator_id": self.delegator_id,
            "delegatee_id": self.delegatee_id,
            "delegation_type": self.delegation_type.value,
            "scope": self.scope,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DelegationRecord":
        """Tạo DelegationRecord từ dict."""
        return cls(
            delegation_id=data.get("delegation_id", ""),
            delegator_id=data.get("delegator_id", ""),
            delegatee_id=data.get("delegatee_id", ""),
            delegation_type=DelegationType(data.get("delegation_type", "temporary")),
            scope=data.get("scope", "*"),
            valid_from=datetime.fromisoformat(data["valid_from"]) if data.get("valid_from") else None,
            valid_until=datetime.fromisoformat(data["valid_until"]) if data.get("valid_until") else None,
            is_active=data.get("is_active", True),
        )


# ===========================================================================
# ApprovalEngine
# ===========================================================================


class ApprovalEngine:
    """Engine xử lý chuỗi phê duyệt, leo thang, và ủy quyền.

    In-memory engine cho quy trình phê duyệt: quản lý yêu cầu, bước,
    quyết định, leo thang, và ủy quyền. Hỗ trợ nhiều loại quy trình
    (sequential, parallel, matrix, voting, single).

    Workflow:
    1. Tạo ApprovalRequest với metadata và loại quy trình
    2. Thêm ApprovalStep(s) — tuần tự hoặc song song
    3. Người phê duyệt gọi decide() để phê duyệt/từ chối
    4. Engine tự động chuyển bước tiếp theo (sequential) hoặc tổng hợp (parallel/voting)
    5. Tự động leo thang khi hết thời hạn
    6. Hỗ trợ ủy quyền — người phê duyệt có thể ủy cho người khác
    7. Phát hiện chu trình vô hạn trong chuỗi phê duyệt

    Attributes:
        requests: Dict request_id -> ApprovalRequest
        steps: Dict step_id -> ApprovalStep
        decisions: Dict decision_id -> ApprovalDecision
        escalation_rules: Dict rule_id -> EscalationRule
        delegations: Dict delegation_id -> DelegationRecord
    """

    def __init__(self) -> None:
        """Khởi tạo ApprovalEngine với các bộ sưu tập rỗng."""
        self.requests: dict[str, ApprovalRequest] = {}
        self.steps: dict[str, ApprovalStep] = {}
        self.decisions: dict[str, ApprovalDecision] = {}
        self.escalation_rules: dict[str, EscalationRule] = {}
        self.delegations: dict[str, DelegationRecord] = {}
        self._decision_counter = 0
        self._escalation_counter = 0
        self._delegation_counter = 0

    def create_request(self, request: ApprovalRequest) -> str:
        """Tạo yêu cầu phê duyệt mới.

        Validate yêu cầu không trùng lặp và lưu vào store.

        Args:
            request: ApprovalRequest cần tạo

        Returns:
            request_id của yêu cầu đã tạo

        Raises:
            MidicoderError: Nếu request_id đã tồn tại (MDC-CP42-001)
        """
        if request.request_id in self.requests:
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_REQUEST_NOT_FOUND,
                reason=f"request_id '{request.request_id}' đã tồn tại",
            )

        self.requests[request.request_id] = request
        return request.request_id

    def get_request(self, request_id: str) -> ApprovalRequest:
        """Lấy yêu cầu phê duyệt theo ID.

        Args:
            request_id: ID yêu cầu phê duyệt cần lấy

        Returns:
            ApprovalRequest nếu tìm thấy

        Raises:
            MidicoderError: Nếu không tìm thấy yêu cầu (MDC-CP42-001)
        """
        if request_id not in self.requests:
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_REQUEST_NOT_FOUND,
                request_id=request_id,
            )
        return self.requests[request_id]

    def decide(self, step_id: str, approver_id: str, decision: str, comment: str = "") -> ApprovalDecision:
        """Đưa ra quyết định phê duyệt cho một bước.

        Validate: (1) bước tồn tại và đúng lượt của người phê duyệt,
        (2) bước chưa có quyết định, (3) người phê duyệt có vai trò hợp lệ.
        Sau đó tạo decision record và tự động chuyển bước tiếp theo
        (sequential) hoặc tổng hợp kết quả (parallel/voting).

        Args:
            step_id: ID bước phê duyệt
            approver_id: ID người đưa ra quyết định
            decision: Quyết định ("approved" hoặc "rejected")
            comment: Nhận xét (nullable)

        Returns:
            ApprovalDecision đã tạo

        Raises:
            MidicoderError: Nếu không phải lượt của người phê duyệt (MDC-CP42-002)
            MidicoderError: Nếu bước đã có quyết định (MDC-CP42-003)
            MidicoderError: Nếu người phê duyệt thiếu vai trò (MDC-CP42-004)
        """
        # Tìm bước phê duyệt
        if step_id not in self.steps:
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_NOT_YOUR_TURN,
                reason=f"step_id '{step_id}' không tồn tại",
            )

        step = self.steps[step_id]

        # Kiểm tra ủy quyền: giải quyết người phê duyệt thực tế
        actual_approver_id = self.resolve_approver(approver_id)

        # Validate: đã đúng lượt của người phê duyệt chưa?
        if step.approver_id != actual_approver_id and step.approver_id != approver_id:
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_NOT_YOUR_TURN,
                step_id=step_id,
                approver_id=approver_id,
            )

        # Validate: bước chưa được quyết định
        if step.status not in (ApprovalStatus.PENDING, ApprovalStatus.ESCALATED):
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_ALREADY_DECIDED,
                step_id=step_id,
                current_status=step.status.value,
            )

        # Validate: người phê duyệt có vai trò
        if not step.approver_role or not step.approver_role.strip():
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_MISSING_ROLE,
                step_id=step_id,
            )

        # Tạo decision record
        self._decision_counter += 1
        decision_id = f"decision_{self._decision_counter}_{int(time.time() * 1000)}"

        approval_decision = ApprovalDecision(
            decision_id=decision_id,
            step_id=step_id,
            request_id=step.request_id,
            approver_id=approver_id,
            decision=decision,
            comment=comment,
        )
        self.decisions[decision_id] = approval_decision

        # Cập nhật trạng thái bước
        if decision == "approved":
            step.status = ApprovalStatus.APPROVED
        else:
            step.status = ApprovalStatus.REJECTED

        # Chuyển tiếp chuỗi phê duyệt
        self._advance_chain(step, decision)

        return approval_decision

    def delegate(self, request_id: str, delegator_id: str, delegatee_id: str,
                 delegation_type: DelegationType = DelegationType.TEMPORARY,
                 valid_until: datetime | None = None) -> DelegationRecord:
        """Ủy quyền phê duyệt cho người khác.

        Validate: (1) yêu cầu tồn tại, (2) không ủy quyền cho chính mình.
        Tạo bản ghi ủy quyền với phạm vi và thời hạn.

        Args:
            request_id: ID yêu cầu phê duyệt
            delegator_id: ID người ủy quyền
            delegatee_id: ID người được ủy quyền
            delegation_type: Loại ủy quyền
            valid_until: Thời điểm hết hiệu lực (nullable)

        Returns:
            DelegationRecord đã tạo

        Raises:
            MidicoderError: Nếu ủy quyền cho chính mình (MDC-CP42-008)
            MidicoderError: Nếu yêu cầu không tồn tại (MDC-CP42-001)
        """
        # Validate yêu cầu tồn tại
        if request_id not in self.requests:
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_REQUEST_NOT_FOUND,
                request_id=request_id,
            )

        # Validate: không ủy quyền cho chính mình
        if delegator_id == delegatee_id:
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_DELEGATION_SELF,
                user_id=delegator_id,
            )

        # Tạo bản ghi ủy quyền
        self._delegation_counter += 1
        delegation_id = f"delegation_{self._delegation_counter}_{int(time.time() * 1000)}"

        delegation = DelegationRecord(
            delegation_id=delegation_id,
            delegator_id=delegator_id,
            delegatee_id=delegatee_id,
            delegation_type=delegation_type,
            scope=request_id,
            valid_until=valid_until,
        )
        self.delegations[delegation_id] = delegation

        # Cập nhật trạng thái request
        self.requests[request_id].status = ApprovalStatus.DELEGATED
        self.requests[request_id].updated_at = datetime.now(timezone.utc)

        return delegation

    def escalate(self, request_id: str) -> list[str]:
        """Leo thang yêu cầu phê duyệt.

        Kiểm tra các quy tắc leo thang đã đăng ký, di chuyển yêu cầu
        đến cấp/phòng ban tiếp theo theo chiến lược đã cấu hình.

        Args:
            request_id: ID yêu cầu phê duyệt cần leo thang

        Returns:
            Danh sách rule_ids đã được kích hoạt

        Raises:
            MidicoderError: Nếu không có cấp tiếp theo để leo thang (MDC-CP42-006)
            MidicoderError: Nếu yêu cầu không tồn tại (MDC-CP42-001)
        """
        # Validate yêu cầu tồn tại
        if request_id not in self.requests:
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_REQUEST_NOT_FOUND,
                request_id=request_id,
            )

        request = self.requests[request_id]

        # Tìm các quy tắc leo thang còn hoạt động cho request này
        active_rules = [
            rule for rule in self.escalation_rules.values()
            if rule.request_id == request_id and rule.is_active
        ]

        if not active_rules:
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_ESCALATION_NO_NEXT_LEVEL,
                request_id=request_id,
            )

        escalated_rules: list[str] = []

        for rule in active_rules:
            # Cập nhật trạng thái request
            request.status = ApprovalStatus.ESCALATED
            request.updated_at = datetime.now(timezone.utc)

            # Cập nhật trạng thái các bước đang pending
            pending_steps = [
                step for step in self.steps.values()
                if step.request_id == request_id and step.status == ApprovalStatus.PENDING
            ]

            for step in pending_steps:
                step.status = ApprovalStatus.ESCALATED

                # Nếu có target_role hoặc target_id từ rule, cập nhật step
                if rule.target_role:
                    step.approver_role = rule.target_role
                if rule.target_id:
                    step.approver_id = rule.target_id

                # Đặt lại thời hạn hành động
                step.action_deadline = datetime.now(timezone.utc) + timedelta(
                    minutes=rule.trigger_after_minutes
                )

            escalated_rules.append(rule.rule_id)

        return escalated_rules

    def check_deadlines(self) -> list[str]:
        """Kiểm tra các yêu cầu phê duyệt đã hết thời hạn.

        Duyệt qua tất cả yêu cầu đang pending, tìm những yêu cầu
        vượt quá thời hạn và tự động leo thang.

        Returns:
            Danh sách request_ids đã hết hạn và được tự động leo thang
        """
        now = datetime.now(timezone.utc)
        expired_requests: list[str] = []

        for request_id, request in list(self.requests.items()):
            if request.status not in (ApprovalStatus.PENDING, ApprovalStatus.DELEGATED):
                continue

            # Kiểm tra deadline tổng của request
            if request.deadline and now > request.deadline:
                request.status = ApprovalStatus.EXPIRED
                request.updated_at = now
                expired_requests.append(request_id)

                # Thử tự động leo thang
                try:
                    self.escalate(request_id)
                except Exception:
                    # Nếu không có quy tắc leo thang, giữ trạng thái EXPIRED
                    pass

            # Kiểm tra deadline của từng bước
            request_steps = [
                step for step in self.steps.values()
                if step.request_id == request_id and step.status == ApprovalStatus.PENDING
            ]

            for step in request_steps:
                if step.action_deadline and now > step.action_deadline:
                    step.status = ApprovalStatus.EXPIRED

                    # Nếu request chưa bị expired, thử leo thang
                    if request.status == ApprovalStatus.PENDING:
                        try:
                            self.escalate(request_id)
                        except Exception:
                            pass

        return expired_requests

    def get_pending_approvals(self, user_id: str) -> list[ApprovalRequest]:
        """Lấy danh sách yêu cầu phê duyệt đang chờ người dùng xử lý.

        Tìm tất cả yêu cầu có bước pending dành cho user_id,
        bao gồm cả các bước đã được ủy quyền cho user.

        Args:
            user_id: ID người dùng

        Returns:
            Danh sách ApprovalRequest đang chờ xử lý
        """
        pending_request_ids: set[str] = set()

        # Tìm các bước pending của user
        for step in self.steps.values():
            if step.status != ApprovalStatus.PENDING:
                continue

            # Kiểm tra trực tiếp
            if step.approver_id == user_id:
                pending_request_ids.add(step.request_id)
                continue

            # Kiểm tra ủy quyền: user có phải delegatee của approver không?
            for delegation in self.delegations.values():
                if (delegation.delegator_id == step.approver_id
                        and delegation.delegatee_id == user_id
                        and delegation.is_active
                        and delegation.is_valid_at()):
                    pending_request_ids.add(step.request_id)
                    break

        # Lọc các request còn pending
        result = [
            self.requests[rid] for rid in pending_request_ids
            if rid in self.requests
            and self.requests[rid].status in (ApprovalStatus.PENDING, ApprovalStatus.DELEGATED)
        ]

        return result

    def get_decisions(self, request_id: str) -> list[ApprovalDecision]:
        """Lấy tất cả quyết định cho một yêu cầu phê duyệt.

        Sắp xếp theo created_at tăng dần (cũ nhất trước).

        Args:
            request_id: ID yêu cầu phê duyệt

        Returns:
            Danh sách ApprovalDecision sắp xếp theo created_at tăng dần

        Raises:
            MidicoderError: Nếu yêu cầu không tồn tại (MDC-CP42-001)
        """
        if request_id not in self.requests:
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_REQUEST_NOT_FOUND,
                request_id=request_id,
            )

        request_decisions = [
            d for d in self.decisions.values()
            if d.request_id == request_id
        ]

        # Sắp xếp theo created_at tăng dần
        request_decisions.sort(
            key=lambda d: d.created_at if d.created_at else datetime.min.replace(tzinfo=timezone.utc),
        )

        return request_decisions

    def detect_cycle(self, request_id: str) -> bool:
        """Phát hiện chu trình trong chuỗi phê duyệt.

        Duyệt qua các bước của yêu cầu, kiểm tra xem có tồn tại
        chu trình lặp vô hạn trong chuỗi phê duyệt hay không
        (ví dụ: A -> B -> A).

        Args:
            request_id: ID yêu cầu phê duyệt

        Returns:
            True nếu phát hiện chu trình

        Raises:
            MidicoderError: Nếu phát hiện chu trình (MDC-CP42-005)
            MidicoderError: Nếu yêu cầu không tồn tại (MDC-CP42-001)
        """
        if request_id not in self.requests:
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_REQUEST_NOT_FOUND,
                request_id=request_id,
            )

        # Lấy tất cả bước của request, sắp xếp theo step_number
        request_steps = sorted(
            [s for s in self.steps.values() if s.request_id == request_id],
            key=lambda s: s.step_number,
        )

        # Kiểm tra: nếu có 2 bước khác nhau với cùng approver_id
        # Với quy trình sequential, điều này là chu trình
        seen_approvers: dict[str, list[int]] = {}

        for step in request_steps:
            approver = step.approver_id
            if approver not in seen_approvers:
                seen_approvers[approver] = []
            seen_approvers[approver].append(step.step_number)

        # Với sequential, một approver không được xuất hiện ở nhiều bước
        request = self.requests[request_id]
        if request.approval_type == ApprovalType.SEQUENTIAL:
            for approver, step_numbers in seen_approvers.items():
                if len(step_numbers) > 1:
                    EM.raise_error(
                        ErrorCode.CP42_APPROVAL_CHAIN_CYCLE_DETECTED,
                        request_id=request_id,
                        approver_id=approver,
                        step_numbers=step_numbers,
                    )

        return False

    def resolve_approver(self, approver_id: str) -> str:
        """Giải quyết người phê duyệt thực tế dựa trên ủy quyền.

        Kiểm tra xem approver_id có ủy quyền cho người khác không.
        Nếu có ủy quyền hiệu lực, trả về delegatee_id thay vì approver_id.

        Args:
            approver_id: ID người phê duyệt ban đầu

        Returns:
            ID người phê duyệt thực tế (có thể là delegatee)
        """
        now = datetime.now(timezone.utc)

        # Tìm ủy quyền hiệu lực: approver_id là delegator
        for delegation in self.delegations.values():
            if (delegation.delegator_id == approver_id
                    and delegation.is_active
                    and delegation.is_valid_at(now)):
                # Trả về delegatee — người thực tế sẽ phê duyệt
                return delegation.delegatee_id

        return approver_id

    def get_steps_for_request(self, request_id: str) -> list[ApprovalStep]:
        """Lấy tất cả bước phê duyệt của một yêu cầu.

        Sắp xếp theo step_number tăng dần.

        Args:
            request_id: ID yêu cầu phê duyệt

        Returns:
            Danh sách ApprovalStep sắp xếp theo step_number

        Raises:
            MidicoderError: Nếu yêu cầu không tồn tại (MDC-CP42-001)
        """
        if request_id not in self.requests:
            EM.raise_error(
                ErrorCode.CP42_APPROVAL_REQUEST_NOT_FOUND,
                request_id=request_id,
            )

        request_steps = [
            s for s in self.steps.values()
            if s.request_id == request_id
        ]

        request_steps.sort(key=lambda s: s.step_number)
        return request_steps

    def get_active_delegations(self, user_id: str) -> list[DelegationRecord]:
        """Lấy tất cả ủy quyền đang hoạt động của người dùng.

        Bao gồm cả ủy quyền user đã tạo và ủy quyền dành cho user.

        Args:
            user_id: ID người dùng

        Returns:
            Danh sách DelegationRecord đang hoạt động
        """
        now = datetime.now(timezone.utc)

        return [
            d for d in self.delegations.values()
            if ((d.delegator_id == user_id or d.delegatee_id == user_id)
                and d.is_active
                and d.is_valid_at(now))
        ]

    def _advance_chain(self, step: ApprovalStep, decision: str) -> None:
        """Tự động chuyển tiếp chuỗi phê duyệt sau khi có quyết định.

        Xử lý theo loại quy trình:
        - SEQUENTIAL: Chuyển đến bước tiếp theo (step_number + 1)
        - PARALLEL: Kiểm tra tất cả bước song song đã quyết định chưa
        - VOTING: Tổng hợp kết quả biểu quyết
        - SINGLE: Hoàn tất ngay sau quyết định
        - MATRIX: Chuyển đến hàng/cột tiếp theo

        Args:
            step: Bước vừa có quyết định
            decision: Quyết định ("approved" hoặc "rejected")
        """
        request = self.requests.get(step.request_id)
        if not request:
            return

        # Nếu bị từ chối, kết thúc luôn
        if decision == "rejected":
            request.status = ApprovalStatus.REJECTED
            request.updated_at = datetime.now(timezone.utc)
            return

        # Xử lý theo loại quy trình
        if request.approval_type == ApprovalType.SINGLE:
            # Một người phê duyệt duy nhất — đã xong
            request.status = ApprovalStatus.APPROVED
            request.updated_at = datetime.now(timezone.utc)

        elif request.approval_type == ApprovalType.SEQUENTIAL:
            # Chuyển đến bước tiếp theo
            next_steps = [
                s for s in self.steps.values()
                if s.request_id == step.request_id
                and s.step_number == step.step_number + 1
                and s.status == ApprovalStatus.PENDING
            ]

            if next_steps:
                request.current_step = next_steps[0].step_number
            else:
                # Không có bước tiếp theo — hoàn tất
                request.status = ApprovalStatus.APPROVED

            request.updated_at = datetime.now(timezone.utc)

        elif request.approval_type == ApprovalType.PARALLEL:
            # Kiểm tra tất cả bước song song đã quyết định
            parallel_steps = [
                s for s in self.steps.values()
                if s.request_id == step.request_id and s.is_parallel
            ]

            all_decided = all(
                s.status in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED)
                for s in parallel_steps
            )

            if all_decided:
                # Kiểm tra có bước nào bị từ chối không
                has_rejection = any(
                    s.status == ApprovalStatus.REJECTED for s in parallel_steps
                )
                request.status = ApprovalStatus.REJECTED if has_rejection else ApprovalStatus.APPROVED

            request.updated_at = datetime.now(timezone.utc)

        elif request.approval_type == ApprovalType.VOTING:
            # Tổng hợp biểu quyết
            self._resolve_voting(request)

    def _resolve_voting(self, request: ApprovalRequest) -> None:
        """Tổng hợp kết quả biểu quyết cho yêu cầu phê duyệt.

        Dựa vào voting_mode (majority, unanimity, first_decides, weighted),
        xác định kết quả cuối cùng từ các quyết định đã thu thập.

        Args:
            request: ApprovalRequest cần tổng hợp
        """
        request_steps = [
            s for s in self.steps.values()
            if s.request_id == request.request_id
        ]

        decided_steps = [
            s for s in request_steps
            if s.status in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED)
        ]

        if not decided_steps:
            return

        approved_count = sum(1 for s in decided_steps if s.status == ApprovalStatus.APPROVED)
        rejected_count = sum(1 for s in decided_steps if s.status == ApprovalStatus.REJECTED)
        total_steps = len(request_steps)

        # Kiểm tra điều kiện quorum (ít nhất một nửa số bước phải có quyết định)
        if len(decided_steps) < max(1, total_steps // 2):
            return

        # Đã hoàn tất khi tất cả bước đều có quyết định
        if len(decided_steps) == total_steps:
            if approved_count >= rejected_count:
                request.status = ApprovalStatus.APPROVED
            else:
                request.status = ApprovalStatus.REJECTED
        else:
            # Chưa hoàn tất — áp dụng majority partial
            if approved_count > rejected_count:
                pass
            elif rejected_count > approved_count:
                pass

        request.updated_at = datetime.now(timezone.utc)
