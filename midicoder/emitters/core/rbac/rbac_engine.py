"""
CP04: RBAC & Policy Engine — RBAC Runtime Engine.

Engine runtime cho Role-Based Access Control:
- Kiểm tra user có role không (bao gồm hierarchical inheritance)
- Kiểm tra user có permission không

Import CP03 AuthUser từ auth models.
Tất cả comments bằng tiếng Việt.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any, Optional

from midicoder.emitters.core.rbac.models import Role, RBACConfig


class RBACEngine:
    """
    RBAC Engine — Runtime engine cho Role-Based Access Control.

    Engine cung cấp các phương thức:
    - check_role(): Kiểm tra user có role yêu cầu (bao gồm inheritance)
    - check_permission(): Kiểm tra user có permission cụ thể

    Role hierarchy: Nếu user có role 'admin' và 'admin' extends 'manager',
    thì user có cả 2 roles.
    """

    def __init__(self, config: RBACConfig) -> None:
        """
        Khởi tạo RBAC Engine.

        Args:
            config: RBACConfig chứa roles và policies
        """
        self._config = config
        self._role_cache: dict[str, Role] = {role.name: role for role in config.roles}

    def check_role(
        self, user_role_names: list[str], required_role: str
    ) -> bool:
        """
        Kiểm tra user có role yêu cầu (bao gồm hierarchical inheritance).

        Args:
            user_role_names: Danh sách role names của user
            required_role: Role name cần kiểm tra

        Returns:
            True nếu user có role (trực tiếp hoặc qua inheritance)
        """
        for role_name in user_role_names:
            if self._role_has(role_name, required_role):
                return True
        return False

    def check_permission(
        self,
        user_role_names: list[str],
        resource: str,
        action: str,
    ) -> bool:
        """
        Kiểm tra user có permission cho resource:action.

        Args:
            user_role_names: Danh sách role names của user
            resource: Resource name (ví dụ: "Order")
            action: Action name (ví dụ: "create")

        Returns:
            True nếu user có permission
        """
        permission_id = f"{resource.lower()}.{action}"

        # Gather tất cả permissions từ user roles (bao gồm inheritance)
        all_permissions = self._gather_permissions(user_role_names)
        return permission_id in all_permissions

    def get_effective_roles(self, user_role_names: list[str]) -> set[str]:
        """
        Lấy tất cả effective roles của user (bao gồm inherited).

        Args:
            user_role_names: Danh sách role names trực tiếp của user

        Returns:
            Set của tất cả role names (trực tiếp + inherited)
        """
        effective: set[str] = set()
        for role_name in user_role_names:
            effective.add(role_name)
            # Thêm tất cả parent roles (recursive)
            effective.update(self._get_parent_roles(role_name))
        return effective

    def _role_has(self, role_name: str, target_role: str) -> bool:
        """
        Kiểm tra role có target role (trực tiếp hoặc inheritance).

        Args:
            role_name: Role name gốc
            target_role: Role name mục tiêu

        Returns:
            True nếu role_name có target_role qua inheritance
        """
        if role_name == target_role:
            return True

        role = self._role_cache.get(role_name)
        if role is None:
            return False

        # Kiểm tra parent roles (recursive)
        for parent_name in role.parent_roles:
            if self._role_has(parent_name, target_role):
                return True

        return False

    def _get_parent_roles(self, role_name: str) -> set[str]:
        """
        Lấy tất cả parent roles của một role (recursive).

        Args:
            role_name: Role name

        Returns:
            Set của parent role names
        """
        result: set[str] = set()
        role = self._role_cache.get(role_name)
        if role is None:
            return result

        for parent_name in role.parent_roles:
            result.add(parent_name)
            result.update(self._get_parent_roles(parent_name))

        return result

    def _gather_permissions(
        self, user_role_names: list[str]
    ) -> set[str]:
        """
        Thu thập tất cả permissions từ user roles (bao gồm inheritance).

        Args:
            user_role_names: Danh sách role names của user

        Returns:
            Set của tất cả permission IDs
        """
        all_permissions: set[str] = set()

        for role_name in user_role_names:
            role = self._role_cache.get(role_name)
            if role is None:
                continue
            # Get all permissions bao gồm inherited
            parent_roles = {
                name: self._role_cache[name]
                for name in self._role_cache
            }
            all_permissions.update(
                role.get_all_permissions(parent_roles)
            )

        return all_permissions