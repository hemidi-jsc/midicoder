"""
CP03 + CP04: RBAC & Policy Engine Models.

Module này chứa các core models cho RBAC (Role-Based Access Control) và Policy Engine:
- Permission: Định nghĩa permission cho resource + action
- Role: Định nghĩa role với permissions và parent roles (inheritance)
- PolicyCondition: Điều kiện cho policy evaluation
- Policy: Policy với effect (allow/deny) và conditions
- PolicyEffect: Enum cho policy effect (ALLOW, DENY)
- PolicyEvaluationResult: Kết quả policy evaluation

Theo SoT (E12 CP03 + CP04):
- JWT authentication
- OAuth2 integration
- Permission-based authorization
- Role-based access control (RBAC)
- Role definitions
- Permission bindings
- Policy evaluation (OPA-compatible)
- Access control lists (ACL)

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

    Permission đại diện cho một quyền truy cập cụ thể vào một resource.
    Permission ID thường có format: resource.action (ví dụ: order.create)

    Attributes:
        id: Định danh duy nhất của permission
        resource: Resource mà permission áp dụng cho (ví dụ: Order, Customer)
        action: Action cho phép thực hiện (ví dụ: create, read, update, delete)
        description: Mô tả permission (optional)
    """

    id: str
    resource: str
    action: str
    description: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert Permission sang dict.

        Returns:
            Dict representation của Permission
        """
        return {
            "id": self.id,
            "resource": self.resource,
            "action": self.action,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Permission":
        """
        Tạo Permission từ dict.

        Args:
            data: Dict với keys: id, resource, action, description

        Returns:
            Permission instance
        """
        return cls(
            id=data["id"],
            resource=data["resource"],
            action=data["action"],
            description=data.get("description"),
        )

    @classmethod
    def format_id(cls, resource: str, action: str) -> str:
        """
        Format permission ID từ resource và action.

        Format: resource_lowercase.action (ví dụ: Order, create -> order.create)

        Args:
            resource: Resource name (ví dụ: Order)
            action: Action name (ví dụ: create)

        Returns:
            Permission ID string
        """
        return f"{resource.lower()}.{action}"

    def __str__(self) -> str:
        """Return string representation của Permission."""
        return f"Permission(id={self.id}, resource={self.resource}, action={self.action})"

    def __eq__(self, other: object) -> bool:
        """Kiểm tra equality giữa 2 Permissions."""
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
    Role - Định nghĩa role với permissions và parent roles.

    Role đại diện cho một vai trò trong hệ thống, có thể:
    - Có danh sách permissions (quyền truy cập)
    - Có parent roles (inheritance - thừa kế permissions từ parent)

    Attributes:
        name: Tên của role
        description: Mô tả role (optional)
        permissions: Danh sách permission IDs
        parent_roles: Danh sách parent role names (inheritance)
    """

    name: str
    description: Optional[str] = None
    permissions: list[str] = field(default_factory=list)
    parent_roles: list[str] = field(default_factory=list)

    def add_permission(self, permission_id: str) -> None:
        """
        Thêm permission vào role.

        Args:
            permission_id: Permission ID để thêm
        """
        if permission_id not in self.permissions:
            self.permissions.append(permission_id)

    def remove_permission(self, permission_id: str) -> None:
        """
        Xóa permission khỏi role.

        Args:
            permission_id: Permission ID để xóa
        """
        if permission_id in self.permissions:
            self.permissions.remove(permission_id)

    def has_permission(self, permission_id: str) -> bool:
        """
        Kiểm tra nếu role có permission.

        Args:
            permission_id: Permission ID để kiểm tra

        Returns:
            True nếu role có permission, False nếu không
        """
        return permission_id in self.permissions

    def add_parent_role(self, parent_role_name: str) -> None:
        """
        Thêm parent role (inheritance).

        Args:
            parent_role_name: Parent role name để thêm
        """
        if parent_role_name not in self.parent_roles:
            self.parent_roles.append(parent_role_name)

    def get_all_permissions(
        self, parent_roles: Optional[dict[str, "Role"]] = None
    ) -> set[str]:
        """
        Lấy tất cả permissions của role, bao gồm inheritance.

        Args:
            parent_roles: Mapping từ role name -> Role object (optional)

        Returns:
            Set của tất cả permission IDs
        """
        all_permissions = set(self.permissions)

        # Thêm permissions từ parent roles
        if parent_roles:
            for parent_name in self.parent_roles:
                if parent_name in parent_roles:
                    parent_role = parent_roles[parent_name]
                    # Recursively get permissions from parent
                    all_permissions.update(
                        parent_role.get_all_permissions(parent_roles)
                    )

        return all_permissions

    def to_dict(self) -> dict[str, Any]:
        """
        Convert Role sang dict.

        Returns:
            Dict representation của Role
        """
        return {
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions.copy(),
            "parent_roles": self.parent_roles.copy(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Role":
        """
        Tạo Role từ dict.

        Args:
            data: Dict với keys: name, description, permissions, parent_roles

        Returns:
            Role instance
        """
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
    """
    Policy Effect - Hiệu ứng của policy.

    Theo OPA (Open Policy Agent) compatibility:
    - ALLOW: Cho phép action
    - DENY: Từ chối action

    Attributes:
        value: String value của effect
    """

    ALLOW = "allow"
    DENY = "deny"


# ============================================================================
# PolicyCondition Class
# ============================================================================


@dataclass
class PolicyCondition:
    """
    Policy Condition - Điều kiện cho policy evaluation.

    Condition đại diện cho một điều kiện cần được evaluate để determine
    nếu policy match với context hiện tại.

    Operators hỗ trợ (OPA-compatible):
    - eq: equals
    - ne: not equals
    - gt: greater than
    - gte: greater than or equal
    - lt: less than
    - lte: less than or equal
    - in: in list
    - not_in: not in list
    - contains: string contains
    - starts_with: string starts with
    - ends_with: string ends with

    Attributes:
        field: Field name trong context để check
        operator: Operator để sử dụng
        value: Value để compare
    """

    field: str
    operator: str
    value: Any

    def to_dict(self) -> dict[str, Any]:
        """
        Convert PolicyCondition sang dict.

        Returns:
            Dict representation của PolicyCondition
        """
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PolicyCondition":
        """
        Tạo PolicyCondition từ dict.

        Args:
            data: Dict với keys: field, operator, value

        Returns:
            PolicyCondition instance
        """
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
    """
    Policy Evaluation Result - Kết quả policy evaluation.

    Kết quả trả về sau khi evaluate một policy với context.

    Attributes:
        policy_id: Policy ID được evaluate
        matched: True nếu policy match với context
        allowed: True nếu policy cho phép (effect = ALLOW và match)
        reason: Lý do cho kết quả (optional)
    """

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
    Policy - Policy cho authorization.

    Policy đại diện cho một quy tắc authorization với:
    - Effect: ALLOW hoặc DENY
    - Conditions: Danh sách điều kiện (AND logic)
    - Actions: Danh sách actions áp dụng
    - Resources: Danh sách resources áp dụng

    Theo OPA (Open Policy Agent) compatibility.

    Attributes:
        id: Định danh duy nhất của policy
        effect: Policy effect (ALLOW/DENY)
        conditions: Danh sách conditions (AND logic - tất cả phải match)
        actions: Danh sách actions áp dụng
        resources: Danh sách resources áp dụng
        description: Mô tả policy (optional)
    """

    id: str
    effect: PolicyEffect
    conditions: list[PolicyCondition] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
    description: Optional[str] = None

    def evaluate(self, context: dict[str, Any]) -> PolicyEvaluationResult:
        """
        Evaluate policy với context.

        Args:
            context: Context với field values để evaluate

        Returns:
            PolicyEvaluationResult với kết quả
        """
        # Check conditions
        matched = self._evaluate_conditions(context)

        if not matched:
            return PolicyEvaluationResult(
                policy_id=self.id,
                matched=False,
                allowed=False,
                reason="Conditions không match",
            )

        # Conditions matched - return effect
        return PolicyEvaluationResult(
            policy_id=self.id,
            matched=True,
            allowed=self.effect == PolicyEffect.ALLOW,
            reason=f"Policy match - effect: {self.effect.value}",
        )

    def _evaluate_conditions(self, context: dict[str, Any]) -> bool:
        """
        Evaluate tất cả conditions (AND logic).

        Tất cả conditions phải match để policy match.

        Args:
            context: Context với field values

        Returns:
            True nếu tất cả conditions match
        """
        # No conditions = always match
        if not self.conditions:
            return True

        for condition in self.conditions:
            if not self._evaluate_condition(condition, context):
                return False

        return True

    def _evaluate_condition(
        self, condition: PolicyCondition, context: dict[str, Any]
    ) -> bool:
        """
        Evaluate một condition với context.

        Args:
            condition: Condition để evaluate
            context: Context với field values

        Returns:
            True nếu condition match
        """
        # Get field value từ context
        field_value = context.get(condition.field)

        # Evaluate dựa trên operator
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
            # Unknown operator - default to False
            return False

    def to_dict(self) -> dict[str, Any]:
        """
        Convert Policy sang dict.

        Returns:
            Dict representation của Policy
        """
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
        """
        Tạo Policy từ dict.

        Args:
            data: Dict với keys: id, effect, conditions, actions, resources

        Returns:
            Policy instance
        """
        # Parse effect
        effect_value = data.get("effect", "allow")
        effect = PolicyEffect(effect_value)

        # Parse conditions
        conditions = []
        for cond_data in data.get("conditions", []):
            conditions.append(PolicyCondition.from_dict(cond_data))

        return cls(
            id=data["id"],
            effect=effect,
            conditions=conditions,
            actions=data.get("actions", []),
            resources=data.get("resources", []),
            description=data.get("description"),
        )