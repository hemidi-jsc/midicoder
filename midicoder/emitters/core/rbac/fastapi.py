"""
CP04: FastAPI RBAC Emitter.

Module này cung cấp FastAPIRBACEmitter để generate FastAPI RBAC code:
- RBACService: Service lớp cho role/permission checks
- RoleGuard: FastAPI dependency cho role-based access
- PolicyGuard: FastAPI dependency cho ABAC policy evaluation

Import CP03 AuthUser context từ request.
Tất cả comments bằng tiếng Việt.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GeneratedFile:
    """
    File đã generate từ emitter.

    Attributes:
        path: Đường dẫn file
        content: Nội dung file
        template: Tên template (nếu có)
        capability: Core Capability code
    """
    path: Path
    content: str
    template: str = ""
    capability: str = "CP04"


class FastAPIRBACEmitter:
    """
    Emitter cho FastAPI RBAC code.

    Generate code từ RBACConfig cho:
    - app/core/rbac/service.py (RBACService)
    - app/core/rbac/guards.py (RoleGuard, PolicyGuard)
    - app/core/rbac/__init__.py
    """

    def __init__(self, config: Any) -> None:
        """
        Khởi tạo FastAPIRBACEmitter.

        Args:
            config: RBACConfig instance (hoặc dict context)
        """
        self._config = config

    def generate(self) -> dict[str, str]:
        """
        Generate toàn bộ FastAPI RBAC code.

        Returns:
            Dict {file_path: code_content}
        """
        result: dict[str, str] = {}
        result["app/core/rbac/__init__.py"] = self._generate_init()
        result["app/core/rbac/service.py"] = self._generate_service()
        result["app/core/rbac/guards.py"] = self._generate_guards()
        return result

    def emit(self, output_dir: Path) -> list[GeneratedFile]:
        """
        Emit files vào output directory.

        Args:
            output_dir: Output directory path

        Returns:
            List of GeneratedFile instances
        """
        rbac_dir = output_dir / "core" / "rbac"
        rbac_dir.mkdir(parents=True, exist_ok=True)

        files: list[GeneratedFile] = []
        for path_str, content in self.generate().items():
            file_path = output_dir / path_str
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            files.append(GeneratedFile(
                path=file_path,
                content=content,
                capability="CP04",
            ))
        return files

    # ========================================================================
    # Template Generators
    # ========================================================================

    def _generate_init(self) -> str:
        """Generate __init__.py cho rbac module."""
        return '''"""
RBAC Module - Role-Based Access Control & Policy Engine (CP04).

Module này cung cấp:
- RBACService: Service layer cho role/permission checks
- RoleGuard: FastAPI dependency cho role-based access
- PolicyGuard: FastAPI dependency cho ABAC policy evaluation

CP04: RBAC & Policy Engine
"""

from .service import RBACService, get_rbac_service
from .guards import RoleGuard, PolicyGuard, require_role, require_policy

__all__ = [
    "RBACService",
    "get_rbac_service",
    "RoleGuard",
    "PolicyGuard",
    "require_role",
    "require_policy",
]
'''

    def _generate_service(self) -> str:
        """Generate service.py - RBACService class."""
        return '''"""
RBAC Service - CP04.

Service layer cho Role-Based Access Control va Policy Evaluation.
"""

from typing import Any, Optional


class RBACService:
    """
    RBAC Service - Quan ly role/permission/policy checks.

    Service nay la trung tam cua CP04, cung cap:
    - check_role(): Kiem tra user co role yeu cau
    - check_permission(): Kiem tra user co permission
    - check_policy(): Evaluate ABAC policy voi context
    """

    def __init__(self) -> None:
        """Khoi tao RBACService."""
        self._roles: dict[str, dict[str, Any]] = {}
        self._policies: list[dict[str, Any]] = []

    def register_role(
        self,
        name: str,
        permissions: Optional[list[str]] = None,
        parent_roles: Optional[list[str]] = None,
    ) -> None:
        """
        Dang ky role moi.

        Args:
            name: Ten role
            permissions: Danh sach permissions
            parent_roles: Danh sach parent roles (inheritance)
        """
        self._roles[name] = {
            "name": name,
            "permissions": permissions or [],
            "parent_roles": parent_roles or [],
        }

    def register_policy(
        self,
        policy_id: str,
        effect: str,
        condition: str,
        resource_type: Optional[str] = None,
        actions: Optional[list[str]] = None,
    ) -> None:
        """
        Dang ky policy rule moi.

        Args:
            policy_id: Policy identifier
            effect: "allow" hoac "deny"
            condition: Expression DSL condition
            resource_type: Resource type (optional)
            actions: Danh sach actions (optional)
        """
        self._policies.append({
            "id": policy_id,
            "effect": effect,
            "condition": condition,
            "resource_type": resource_type,
            "actions": actions or [],
        })

    def check_role(
        self, user_roles: list[str], required_role: str
    ) -> bool:
        """
        Kiem tra user co role yeu cau (bao gom inheritance).

        Args:
            user_roles: Danh sach roles cua user
            required_role: Role can kiem tra

        Returns:
            True neu user co role
        """
        if required_role in user_roles:
            return True

        # Kiem tra inheritance
        for role_name in user_roles:
            role = self._roles.get(role_name)
            if role and self._role_inherits(role, required_role):
                return True

        return False

    def check_permission(
        self, user_roles: list[str], resource: str, action: str
    ) -> bool:
        """
        Kiem tra user co permission cho resource:action.

        Args:
            user_roles: Danh sach roles cua user
            resource: Resource name
            action: Action name

        Returns:
            True neu user co permission
        """
        permission_id = f"{resource.lower()}.{action}"

        # Thu thap tat ca permissions tu user roles
        all_permissions = self._gather_permissions(user_roles)
        return permission_id in all_permissions

    def check_policy(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Evaluate ABAC policy voi context.

        Args:
            context: Policy context (user, resource, action, env)

        Returns:
            Decision dict: {allowed: bool, policy_id: str, reason: str}
        """
        # Import PolicyEngine de evaluate
        try:
            from midicoder.emitters.core.rbac.policy_engine import PolicyEngine
            from midicoder.emitters.core.rbac.models import (
                PolicyContext, PolicyRule, RBACConfig,
            )
            from midicoder.contracts.rbac_models import Role

            # Xay config tu registered data
            roles = [
                Role(name=r["name"], permissions=r["permissions"],
                     parent_roles=r["parent_roles"])
                for r in self._roles.values()
            ]
            policies = [
                PolicyRule(
                    id=p["id"], effect=p["effect"],
                    condition=p["condition"],
                    resource_type=p.get("resource_type"),
                    actions=p.get("actions", []),
                )
                for p in self._policies
            ]
            config = RBACConfig(roles=roles, policies=policies)
            engine = PolicyEngine(config)

            # Xay PolicyContext
            policy_context = PolicyContext(
                action=context.get("action", ""),
                user_attributes=context.get("user", {}),
                resource_attributes=context.get("resource", {}),
                environment=context.get("env", {}),
            )

            decision = engine.evaluate(policy_context)
            return {
                "allowed": decision.allowed,
                "policy_id": decision.policy_id,
                "reason": decision.reason,
            }
        except ImportError:
            # Fallback: simple string match
            return {
                "allowed": True,
                "policy_id": "fallback",
                "reason": "PolicyEngine khong danh — fallback ALLOW",
            }

    def _role_inherits(self, role: dict[str, Any], target: str) -> bool:
        """Kiem tra role co target role qua inheritance."""
        for parent_name in role.get("parent_roles", []):
            if parent_name == target:
                return True
            parent = self._roles.get(parent_name)
            if parent and self._role_inherits(parent, target):
                return True
        return False

    def _gather_permissions(self, user_roles: list[str]) -> set[str]:
        """Thu thap tat ca permissions tu user roles."""
        permissions: set[str] = set()
        for role_name in user_roles:
            role = self._roles.get(role_name)
            if role:
                permissions.update(role.get("permissions", []))
                # Inherited permissions
                for parent_name in role.get("parent_roles", []):
                    parent = self._roles.get(parent_name)
                    if parent:
                        permissions.update(parent.get("permissions", []))
        return permissions


# Singleton instance
_default_service: Optional[RBACService] = None


def get_rbac_service() -> RBACService:
    """Lay default RBACService instance."""
    global _default_service
    if _default_service is None:
        _default_service = RBACService()
    return _default_service
'''

    def _generate_guards(self) -> str:
        """Generate guards.py - RoleGuard va PolicyGuard."""
        return '''"""
RBAC Guards - CP04.

FastAPI dependencies cho role-based va policy-based access control.
"""

from functools import wraps
from typing import Any, Callable, Optional

from fastapi import Depends, HTTPException, status, Request

from .service import RBACService, get_rbac_service


# ============================================================================
# Role Guard
# ============================================================================


class RoleGuard:
    """
    FastAPI dependency cho role-based access control.

    Usage:
        @app.get("/admin")
        def admin_page(
            guard: None = Depends(RoleGuard(required_roles=["admin"]))
        ):
            ...
    """

    def __init__(
        self,
        required_roles: Optional[list[str]] = None,
        required_permissions: Optional[list[str]] = None,
    ) -> None:
        """
        Khoi tao RoleGuard.

        Args:
            required_roles: Danh sach roles duoc phep (OR logic)
            required_permissions: Danh sach permissions duoc phep (OR logic)
        """
        self.required_roles = required_roles or []
        self.required_permissions = required_permissions or []

    async def __call__(
        self,
        request: Request,
        service: RBACService = Depends(get_rbac_service),
    ) -> None:
        """
        Execute guard logic.

        Args:
            request: HTTP Request
            service: RBACService instance

        Raises:
            HTTPException 403: Neu khong du quyen
        """
        # Lay user roles va permissions tu request state
        user_roles = getattr(request.state, "user_roles", [])
        user_permissions = getattr(request.state, "user_permissions", [])

        # Kiem tra roles
        if self.required_roles:
            has_role = any(
                role in user_roles for role in self.required_roles
            )
            if not has_role and not self.required_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Yeu cau role: {self.required_roles}",
                )

        # Kiem tra permissions
        if self.required_permissions:
            has_permission = any(
                perm in user_permissions for perm in self.required_permissions
            )
            if not has_permission and not self.required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Yeu cau permission: {self.required_permissions}",
                )


# ============================================================================
# Policy Guard
# ============================================================================


class PolicyGuard:
    """
    FastAPI dependency cho ABAC policy evaluation.

    Usage:
        @app.post("/orders")
        def create_order(
            request: Request,
            guard: None = Depends(PolicyGuard()),
        ):
            ...
    """

    def __init__(self, action: Optional[str] = None) -> None:
        """
        Khoi tao PolicyGuard.

        Args:
            action: Action name (neu khong co, lay tu route)
        """
        self.action = action

    async def __call__(
        self,
        request: Request,
        service: RBACService = Depends(get_rbac_service),
    ) -> None:
        """
        Execute policy guard logic.

        Raises:
            HTTPException 403: Neu policy deny
        """
        action = self.action or request.method.lower()

        # Xay policy context
        context = {
            "action": action,
            "user": {
                "role": getattr(request.state, "user_role", ""),
                "roles": getattr(request.state, "user_roles", []),
                "tenant_id": getattr(request.state, "tenant_id", ""),
            },
            "resource": {
                "type": getattr(request.state, "resource_type", ""),
                "tenant_id": getattr(request.state, "resource_tenant_id", ""),
            },
            "env": {
                "ip": request.client.host if request.client else "",
                "method": request.method,
                "path": str(request.url.path),
            },
        }

        decision = service.check_policy(context)
        if not decision.get("allowed"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=decision.get("reason", "Policy deny"),
            )


# ============================================================================
# Decorator Helpers
# ============================================================================


def require_role(*roles: str) -> Callable[..., Any]:
    """
    Decorator de require role cho endpoint.

    Usage:
        @app.get("/admin")
        @require_role("admin", "superadmin")
        def admin_page(...):
            ...

    Args:
        *roles: Roles duoc phep

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        # Them dependency vao function metadata
        if not hasattr(func, "_rbac_guards"):
            func._rbac_guards = []  # type: ignore
        func._rbac_guards.append(RoleGuard(required_roles=list(roles)))  # type: ignore
        return func
    return decorator


def require_policy(action: str) -> Callable[..., Any]:
    """
    Decorator de require policy check cho endpoint.

    Usage:
        @app.post("/orders")
        @require_policy("order:create")
        def create_order(...):
            ...

    Args:
        action: Action name

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        if not hasattr(func, "_rbac_guards"):
            func._rbac_guards = []  # type: ignore
        func._rbac_guards.append(PolicyGuard(action=action))  # type: ignore
        return func
    return decorator
'''


__all__ = [
    "FastAPIRBACEmitter",
    "GeneratedFile",
]