"""
CP04: RBAC & Policy Engine — Data Models.

Module này định nghĩa các data models cho RBAC & Policy Engine:
- Permission: Định nghĩa permission cho resource + action
- Role: Định nghĩa role với permissions và parent roles (inheritance)
- PolicyEffect: Enum cho policy effect (ALLOW, DENY)
- PolicyCondition: Điều kiện cho policy evaluation
- PolicyEvaluationResult: Kết quả policy evaluation
- Policy: Policy với effect (allow/deny) và conditions
- PolicyRule: Quy tắc policy với condition expression DSL
- PolicyContext: Context cho policy evaluation (user, resource, env)
- PolicyDecision: Kết quả policy evaluation
- RBACConfig: Complete RBAC configuration

Tất cả comments bằng tiếng Việt.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ============================================================================
# Permission Class
# ============================================================================


@dataclass
class Permission:
    """
    Permission - Định nghĩa permission cho resource + action.

    Permission ID thường có format: resource.action (ví dụ: order.create)
    """

    id: str
    resource: str
    action: str
    description: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert Permission sang dict."""
        return {
            "id": self.id,
            "resource": self.resource,
            "action": self.action,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Permission":
        """Tạo Permission từ dict."""
        return cls(
            id=data["id"],
            resource=data["resource"],
            action=data["action"],
            description=data.get("description"),
        )

    @classmethod
    def format_id(cls, resource: str, action: str) -> str:
        """Format permission ID: resource_lowercase.action."""
        return f"{resource.lower()}.{action}"

    def __str__(self) -> str:
        return f"Permission(id={self.id}, resource={self.resource}, action={self.action})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Permission):
            return False
        return (
            self.id == other.id
            and self.resource == other.resource
            and self.action == other.action
        )


# ============================================================================
# Role Class
# ============================================================================


@dataclass
class Role:
    """
    Role - Định nghĩa role với permissions và parent roles (inheritance).
    """

    name: str
    description: Optional[str] = None
    permissions: list[str] = field(default_factory=list)
    parent_roles: list[str] = field(default_factory=list)

    def add_permission(self, permission_id: str) -> None:
        """Thêm permission vào role."""
        if permission_id not in self.permissions:
            self.permissions.append(permission_id)

    def remove_permission(self, permission_id: str) -> None:
        """Xóa permission khỏi role."""
        if permission_id in self.permissions:
            self.permissions.remove(permission_id)

    def has_permission(self, permission_id: str) -> bool:
        """Kiểm tra nếu role có permission."""
        return permission_id in self.permissions

    def add_parent_role(self, parent_role_name: str) -> None:
        """Thêm parent role (inheritance)."""
        if parent_role_name not in self.parent_roles:
            self.parent_roles.append(parent_role_name)

    def get_all_permissions(
        self, parent_roles: Optional[dict[str, "Role"]] = None
    ) -> set[str]:
        """Lấy tất cả permissions của role, bao gồm inheritance."""
        all_permissions = set(self.permissions)

        if parent_roles:
            for parent_name in self.parent_roles:
                if parent_name in parent_roles:
                    parent_role = parent_roles[parent_name]
                    all_permissions.update(
                        parent_role.get_all_permissions(parent_roles)
                    )

        return all_permissions

    def to_dict(self) -> dict[str, Any]:
        """Convert Role sang dict."""
        return {
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions.copy(),
            "parent_roles": self.parent_roles.copy(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Role":
        """Tạo Role từ dict."""
        return cls(
            name=data["name"],
            description=data.get("description"),
            permissions=data.get("permissions", []),
            parent_roles=data.get("parent_roles", []),
        )


# ============================================================================
# PolicyEffect Enum
# ============================================================================


class PolicyEffect(str, Enum):
    """Policy Effect - Hiệu ứng của policy (OPA-compatible)."""

    ALLOW = "allow"
    DENY = "deny"


# ============================================================================
# PolicyCondition Class
# ============================================================================


@dataclass
class PolicyCondition:
    """
    Policy Condition - Điều kiện cho policy evaluation (OPA-compatible).
    """

    field: str
    operator: str
    value: Any

    def to_dict(self) -> dict[str, Any]:
        """Convert PolicyCondition sang dict."""
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PolicyCondition":
        """Tạo PolicyCondition từ dict."""
        return cls(
            field=data["field"],
            operator=data["operator"],
            value=data["value"],
        )


# ============================================================================
# PolicyEvaluationResult Class
# ============================================================================


@dataclass
class PolicyEvaluationResult:
    """Policy Evaluation Result - Kết quả policy evaluation."""

    policy_id: str
    matched: bool
    allowed: bool
    reason: Optional[str] = None


# ============================================================================
# Policy Class
# ============================================================================


@dataclass
class Policy:
    """
    Policy - Policy cho authorization (OPA-compatible).

    Policy đại diện cho một quy tắc authorization với:
    - Effect: ALLOW hoặc DENY
    - Conditions: Danh sách điều kiện (AND logic)
    - Actions: Danh sách actions áp dụng
    - Resources: Danh sách resources áp dụng
    """

    id: str
    effect: PolicyEffect
    conditions: list[PolicyCondition] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
    description: Optional[str] = None

    def evaluate(self, context: dict[str, Any]) -> "PolicyEvaluationResult":
        """Evaluate policy với context."""
        matched = self._evaluate_conditions(context)

        if not matched:
            return PolicyEvaluationResult(
                policy_id=self.id,
                matched=False,
                allowed=False,
                reason="Conditions không match",
            )

        return PolicyEvaluationResult(
            policy_id=self.id,
            matched=True,
            allowed=self.effect == PolicyEffect.ALLOW,
            reason=f"Policy match - effect: {self.effect.value}",
        )

    def _evaluate_conditions(self, context: dict[str, Any]) -> bool:
        """Evaluate tất cả conditions (AND logic)."""
        if not self.conditions:
            return True

        for condition in self.conditions:
            if not self._evaluate_condition(condition, context):
                return False

        return True

    def _evaluate_condition(
        self, condition: PolicyCondition, context: dict[str, Any]
    ) -> bool:
        """Evaluate một condition với context."""
        field_value = context.get(condition.field)
        operator = condition.operator
        compare_value = condition.value

        if operator == "eq":
            return field_value == compare_value
        elif operator == "ne":
            return field_value != compare_value
        elif operator == "gt":
            return field_value is not None and field_value > compare_value
        elif operator == "gte":
            return field_value is not None and field_value >= compare_value
        elif operator == "lt":
            return field_value is not None and field_value < compare_value
        elif operator == "lte":
            return field_value is not None and field_value <= compare_value
        elif operator == "in":
            return field_value in compare_value if isinstance(compare_value, list) else False
        elif operator == "not_in":
            return field_value not in compare_value if isinstance(compare_value, list) else True
        elif operator == "contains":
            return compare_value in field_value if field_value else False
        elif operator == "starts_with":
            return field_value.startswith(compare_value) if field_value else False
        elif operator == "ends_with":
            return field_value.endswith(compare_value) if field_value else False
        else:
            return False

    def to_dict(self) -> dict[str, Any]:
        """Convert Policy sang dict."""
        return {
            "id": self.id,
            "effect": self.effect.value,
            "conditions": [c.to_dict() for c in self.conditions],
            "actions": self.actions.copy(),
            "resources": self.resources.copy(),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Policy":
        """Tạo Policy từ dict."""
        effect_value = data.get("effect", "allow")
        effect = PolicyEffect(effect_value)

        conditions = [
            PolicyCondition.from_dict(cond_data)
            for cond_data in data.get("conditions", [])
        ]

        return cls(
            id=data["id"],
            effect=effect,
            conditions=conditions,
            actions=data.get("actions", []),
            resources=data.get("resources", []),
            description=data.get("description"),
        )


# ============================================================================
# PolicyRule
# ============================================================================


@dataclass
class PolicyRule:
    """
    Policy Rule — Quy tắc chính sách phân quyền (ABAC).

    Policy rule định nghĩa một quy tắc authorization với:
    - Effect: ALLOW hoặc DENY
    - Condition: Expression DSL để evaluate
    - Resource type: Resource mà policy apply lên (optional)
    - Actions: Danh sách actions mà policy áp dụng (optional)
    """

    id: str
    effect: str = "allow"
    condition: str = ""
    resource_type: Optional[str] = None
    actions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate policy rule sau khi khởi tạo."""
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        if not self.id:
            EM.raise_error(
                ErrorCode.MDC-F02_POLICY_NOT_FOUND,
                reason="Policy rule id không được để trống",
            )

        if not self.condition:
            EM.raise_error(
                ErrorCode.MDC-F02_POLICY_SYNTAX_ERROR,
                policy_id=self.id,
                reason="Policy condition không được để trống",
            )

        if self.effect not in ("allow", "deny"):
            EM.raise_error(
                ErrorCode.MDC-F02_POLICY_SYNTAX_ERROR,
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
    """

    action: str
    user_attributes: dict[str, Any] = field(default_factory=dict)
    resource_attributes: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate policy context sau khi khởi tạo."""
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        if not self.action:
            EM.raise_error(
                ErrorCode.MDC-F02_POLICY_EVALUATION_FAILED,
                reason="Action trong policy context không được để trống",
            )

    def get(self, key: str) -> Any:
        """Lấy giá trị từ context (ưu tiên user, sau resource, rồi environment)."""
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
    - Roles: Danh sách role definitions
    - Policies: Danh sách policy rules (ABAC)
    """

    roles: list[Role] = field(default_factory=list)
    policies: list[PolicyRule] = field(default_factory=list)

    def get_role(self, name: str) -> Optional[Role]:
        """Lấy role theo tên."""
        for role in self.roles:
            if role.name == name:
                return role
        return None

    def get_policy(self, policy_id: str) -> Optional[PolicyRule]:
        """Lấy policy rule theo id."""
        for policy in self.policies:
            if policy.id == policy_id:
                return policy
        return None

    def get_roles_with_permission(self, permission_id: str) -> list[Role]:
        """Lấy danh sách roles có permission cụ thể."""
        result = []
        for role in self.roles:
            if role.has_permission(permission_id):
                result.append(role)
        return result


__all__ = [
    "Permission",
    "Role",
    "PolicyEffect",
    "PolicyCondition",
    "PolicyEvaluationResult",
    "Policy",
    "PolicyRule",
    "PolicyContext",
    "PolicyDecision",
    "RBACConfig",
]
