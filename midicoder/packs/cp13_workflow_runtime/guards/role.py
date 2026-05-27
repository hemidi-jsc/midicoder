"""
Mô-đun Role Guard.

Cung cấp:
- RoleGuard: Guard cho role membership checking

Author: Midicoder Team
Version: 1.0.0
"""

from typing import Any


class RoleGuard:
    """
    Guard evaluator cho role-based guards.

    Kiểm tra user có thuộc một trong các roles yêu cầu không.

    Usage:
        guard = RoleGuard(roles=["admin", "manager"])
        result = guard.evaluate(context={"user_roles": ["admin"]})
    """

    def __init__(self, roles: list[str] | None = None) -> None:
        self.roles = roles or []

    def evaluate(self, context: dict[str, Any]) -> bool:
        """
        Evaluate role guard.

        Args:
            context: Context dictionary

        Returns:
            True nếu user có ít nhất một role yêu cầu, False nếu không
        """
        # TODO: Integrate với CP04 RBAC system

        # Placeholder: return True (implement actual role check)
        return True