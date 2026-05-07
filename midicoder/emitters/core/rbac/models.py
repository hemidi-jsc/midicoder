"""
CP04: RBAC & Policy Engine — Data Models.

Module này định nghĩa các data models cho RBAC & Policy Engine:
- PolicyRule: Quy tắc policy với condition expression DSL
- PolicyContext: Context cho policy evaluation (user, resource, env)
- PolicyDecision: Kết quả policy evaluation
- RBACConfig: Complete RBAC configuration

Import CP03 models để integrate với AuthUser.
Tất cả comments bằng tiếng Việt.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from midicoder.contracts.rbac_models import Role


# ============================================================================
# PolicyRule
# ============================================================================


@dataclass
class PolicyRule:
    """
    Policy Rule — Quy tắc chính sách phân quyền.

    Policy rule định nghĩa một quy tắc authorization với:
    - Effect: ALLOW hoặc DENY
    - Condition: Expression DSL để evaluate (ví dụ: "user.role == 'admin'")
    - Resource type: Resource mà policy apply lên (optional)
    - Actions: Danh sách actions mà policy áp dụng (optional)

    Attributes:
        id: Định danh duy nhất của policy rule
        effect: Hiệu ứng policy — "allow" hoặc "deny"
        condition: Expression DSL condition string
        resource_type: Resource type mà policy áp dụng (optional)
        actions: Danh sách actions mà policy áp dụng
    """

    id: str
    effect: str = "allow"
    condition: str = ""
    resource_type: Optional[str] = None
    actions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate policy rule sau khi khởi tạo."""
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        # Kiểm tra id không để trống
        if not self.id:
            EM.raise_error(
                ErrorCode.CP04_POLICY_NOT_FOUND,
                reason="Policy rule id không được để trống",
            )

        # Kiểm tra condition không để trống
        if not self.condition:
            EM.raise_error(
                ErrorCode.CP04_POLICY_SYNTAX_ERROR,
                policy_id=self.id,
                reason="Policy condition không được để trống",
            )

        # Kiểm tra effect hợp lệ
        if self.effect not in ("allow", "deny"):
            EM.raise_error(
                ErrorCode.CP04_POLICY_SYNTAX_ERROR,
                policy_id=self.id,
                reason=f"Effect '{self.effect}' không hợp lệ, phải là 'allow' hoặc 'deny'",
            )


# ============================================================================
# PolicyContext
# ============================================================================


@dataclass
class PolicyContext:
    """
    Policy Context — Context cho policy evaluation.

    Context chứa đầy đủ thông tin cần thiết để evaluate một policy:
    - User attributes: Thông tin người dùng (role, tenant_id, ...)
    - Resource attributes: Thông tin resource (tenant_id, owner, ...)
    - Action: Action đang được yêu cầu
    - Environment: Thông tin môi trường (ip, hour, ...)

    Attributes:
        action: Action đang được yêu cầu (bắt buộc)
        user_attributes: Thuộc tính của người dùng
        resource_attributes: Thuộc tính của resource
        environment: Thông tin môi trường
    """

    action: str
    user_attributes: dict[str, Any] = field(default_factory=dict)
    resource_attributes: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate policy context sau khi khởi tạo."""
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        # Kiểm tra action không để trống
        if not self.action:
            EM.raise_error(
                ErrorCode.CP04_POLICY_EVALUATION_FAILED,
                reason="Action trong policy context không được để trống",
            )

    def get(self, key: str) -> Any:
        """
        Lấy giá trị từ context (ưu tiên user, sau resource, rồi environment).

        Args:
            key: Key để tìm (ví dụ: "role", "tenant_id")

        Returns:
            Giá trị tìm thấy, None nếu không có
        """
        if key in self.user_attributes:
            return self.user_attributes[key]
        if key in self.resource_attributes:
            return self.resource_attributes[key]
        if key in self.environment:
            return self.environment[key]
        return None


# ============================================================================
# PolicyDecision
# ============================================================================


@dataclass
class PolicyDecision:
    """
    Policy Decision — Kết quả policy evaluation.

    Decision trả về sau khi evaluate policy với context:
    - allowed: True nếu cho phép, False nếu từ chối
    - policy_id: Policy rule ID đưa ra quyết định
    - reason: Lý do cho quyết định

    Attributes:
        allowed: True nếu action được cho phép
        policy_id: Policy rule ID đưa ra quyết định
        reason: Lý do cho quyết định (optional)
    """

    allowed: bool
    policy_id: str = ""
    reason: str = ""


# ============================================================================
# RBACConfig
# ============================================================================


@dataclass
class RBACConfig:
    """
    RBAC Configuration — Cấu hình RBAC hoàn chỉnh.

    Config chứa toàn bộ roles và policy rules của hệ thống:
    - Roles: Danh sách role definitions (từ contracts.rbac_models)
    - Policies: Danh sách policy rules (ABAC)

    Attributes:
        roles: Danh sách role definitions
        policies: Danh sách policy rules
    """

    roles: list[Role] = field(default_factory=list)
    policies: list[PolicyRule] = field(default_factory=list)

    def get_role(self, name: str) -> Optional[Role]:
        """
        Lấy role theo tên.

        Args:
            name: Tên role cần tìm

        Returns:
            Role nếu tìm thấy, None nếu không
        """
        for role in self.roles:
            if role.name == name:
                return role
        return None

    def get_policy(self, policy_id: str) -> Optional[PolicyRule]:
        """
        Lấy policy rule theo id.

        Args:
            policy_id: Policy rule id cần tìm

        Returns:
            PolicyRule nếu tìm thấy, None nếu không
        """
        for policy in self.policies:
            if policy.id == policy_id:
                return policy
        return None

    def get_roles_with_permission(self, permission_id: str) -> list[Role]:
        """
        Lấy danh sách roles có permission cụ thể.

        Args:
            permission_id: Permission ID cần tìm

        Returns:
            Danh sách roles có permission này
        """
        result = []
        for role in self.roles:
            if role.has_permission(permission_id):
                result.append(role)
        return result


__all__ = [
    "PolicyRule",
    "PolicyContext",
    "PolicyDecision",
    "RBACConfig",
]