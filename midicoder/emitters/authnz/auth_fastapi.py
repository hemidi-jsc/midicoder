"""
FastAPI Auth Emitter Module.

Module này cung cấp FastAPIAuthEmitter để generate FastAPI auth code
từ AuthIR (CP02-CP04):
- JWT authentication (tenant-scoped)
- RBAC service với permission checks
- Policy engine (OPA-compatible)
- Tenant context propagation

CP02: Multi-Tenant Architecture
CP03: Authentication & Authorization
CP04: RBAC & Policy Engine

KPI-028: Missing permission detection
KPI-029: Missing tenant filter detection
KPI-030: Invalid role binding detection
KPI-031: Invalid policy detection

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.authnz.auth_models import (
    AuthIR,
    JWTAuthConfig,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ============================================================================
# FastAPI Auth Emitter Class
# ============================================================================


class FastAPIAuthEmitter:
    """
    Emitter cho FastAPI authentication & authorization code.

    Generate code từ AuthIR cho:
    - app/core/security/jwt_auth.py (CP03)
    - app/core/security/rbac_service.py (CP04)
    - app/core/security/permissions.py (CP04)
    - app/core/security/policy_engine.py (CP04)
    - app/core/security/tenant_context.py (CP02)

    Attributes:
        stack_dir: Đường dẫn đến templates directory
        template_env: Jinja2 Environment
    """

    def __init__(self, stack_dir: Path) -> None:
        """
        Initialize FastAPIAuthEmitter.

        Args:
            stack_dir: Đường dẫn đến templates directory

        Raises:
            FileNotFoundError: Nếu stack_dir không tồn tại
        """
        self.stack_dir = stack_dir

        if not stack_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {stack_dir}")

        # Initialize Jinja2 environment
        self.template_env = Environment(
            loader=FileSystemLoader(str(stack_dir)),
            autoescape=True,
        )

    def emit(self, auth_ir: AuthIR, output_dir: Path) -> list[GeneratedFile]:
        """
        Emit FastAPI auth code từ AuthIR.

        Process:
        1. Emit jwt_auth.py (CP03)
        2. Emit rbac_service.py (CP04)
        3. Emit permissions.py (CP04)
        4. Emit policy_engine.py (CP04)
        5. Emit tenant_context.py (CP02)

        Args:
            auth_ir: AuthIR instance
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []

        # Create output directory
        security_dir = output_dir / "core" / "security"
        security_dir.mkdir(parents=True, exist_ok=True)

        # Emit __init__.py
        files.append(self._emit_init(security_dir))

        # Emit jwt_auth.py
        files.append(self._emit_jwt_auth(auth_ir, security_dir))

        # Emit rbac_service.py
        files.append(self._emit_rbac_service(auth_ir, security_dir))

        # Emit permissions.py
        files.append(self._emit_permissions(auth_ir, security_dir))

        # Emit policy_engine.py
        files.append(self._emit_policy_engine(auth_ir, security_dir))

        # Emit tenant_context.py
        files.append(self._emit_tenant_context(auth_ir, security_dir))

        return files

    def _render_template(
        self, template_name: str, context: dict[str, Any]
    ) -> str:
        """
        Render template với context.

        Args:
            template_name: Tên template file
            context: Template context

        Returns:
            Rendered template string

        Raises:
            MidicoderError: Nếu template render fail
        """
        try:
            template = self.template_env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            EM.raise_error(
                ErrorCode.TEMPLATE_NOT_FOUND,
                template_name=template_name,
            )
        except Exception as e:
            EM.raise_error(
                ErrorCode.TEMPLATE_RENDER_FAILED,
                template_name=template_name,
                cause=e,
            )

    def _emit_init(self, output_dir: Path) -> GeneratedFile:
        """
        Emit __init__.py.

        Args:
            output_dir: Output directory

        Returns:
            GeneratedFile instance
        """
        content = '''"""
Security Module - Authentication & Authorization cho FastAPI.

Module này cung cấp:
- JWT authentication (tenant-scoped)
- RBAC service với permission checks
- Policy engine (OPA-compatible)
- Tenant context propagation

CP02: Multi-Tenant Architecture
CP03: Authentication & Authorization
CP04: RBAC & Policy Engine
"""

from .jwt_auth import (
    create_access_token,
    verify_token,
    get_current_user,
    get_current_active_user,
)
from .rbac_service import (
    RBACService,
    get_rbac_service,
    PolicyService,
    get_policy_service,
)
from .permissions import Permissions, check_permission
from .policy_engine import evaluate_policy
from .tenant_context import get_tenant_id, set_tenant_id

__all__ = [
    # JWT Auth
    "create_access_token",
    "verify_token",
    "get_current_user",
    "get_current_active_user",
    # RBAC
    "RBACService",
    "get_rbac_service",
    "PolicyService",
    "get_policy_service",
    # Permissions
    "Permissions",
    "check_permission",
    # Policy Engine
    "evaluate_policy",
    # Tenant Context
    "get_tenant_id",
    "set_tenant_id",
]
'''
        return GeneratedFile(
            path=output_dir / "__init__.py",
            content=content,
            template="__init__.py.jinja2",
            capability="CP02-CP04",
        )

    def _emit_jwt_auth(self, auth_ir: AuthIR, output_dir: Path) -> GeneratedFile:
        """
        Emit jwt_auth.py.

        Args:
            auth_ir: AuthIR instance
            output_dir: Output directory

        Returns:
            GeneratedFile instance
        """
        # Get JWT provider config
        jwt_provider = None
        for provider in auth_ir.providers:
            if provider.provider_type.value == "jwt":
                jwt_provider = provider
                break

        config = jwt_provider.config if jwt_provider else JWTAuthConfig()

        context = {
            "expire_minutes": config.expire_minutes,
            "refresh_expire_days": config.refresh_expire_days,
            "algorithm": config.algorithm,
            "tenant_scoped": config.tenant_scoped,
        }

        content = self._render_template("auth/jwt_auth.py.jinja2", context)

        return GeneratedFile(
            path=output_dir / "jwt_auth.py",
            content=content,
            template="auth/jwt_auth.py.jinja2",
            capability="CP03",
        )

    def _emit_rbac_service(self, auth_ir: AuthIR, output_dir: Path) -> GeneratedFile:
        """
        Emit rbac_service.py.

        Args:
            auth_ir: AuthIR instance
            output_dir: Output directory

        Returns:
            GeneratedFile instance
        """
        context = {
            "roles": auth_ir.roles,
            "policies": auth_ir.policies,
        }

        content = self._render_template("auth/rbac_service.py.jinja2", context)

        return GeneratedFile(
            path=output_dir / "rbac_service.py",
            content=content,
            template="auth/rbac_service.py.jinja2",
            capability="CP04",
        )

    def _emit_permissions(self, auth_ir: AuthIR, output_dir: Path) -> GeneratedFile:
        """
        Emit permissions.py.

        Args:
            auth_ir: AuthIR instance
            output_dir: Output directory

        Returns:
            GeneratedFile instance
        """
        # Collect all unique permissions from roles
        all_permissions: set[str] = set()
        for role in auth_ir.roles.values():
            all_permissions.update(role.permissions)

        context = {
            "permissions": sorted(all_permissions),
            "tenant_scoped_roles": [
                role_id for role_id, role in auth_ir.roles.items()
                if role.tenant_scoped
            ],
        }

        content = self._render_template("auth/permissions.py.jinja2", context)

        return GeneratedFile(
            path=output_dir / "permissions.py",
            content=content,
            template="auth/permissions.py.jinja2",
            capability="CP04",
        )

    def _emit_policy_engine(self, auth_ir: AuthIR, output_dir: Path) -> GeneratedFile:
        """
        Emit policy_engine.py.

        Args:
            auth_ir: AuthIR instance
            output_dir: Output directory

        Returns:
            GeneratedFile instance
        """
        context = {
            "policies": auth_ir.policies,
        }

        content = self._render_template("auth/policy_engine.py.jinja2", context)

        return GeneratedFile(
            path=output_dir / "policy_engine.py",
            content=content,
            template="auth/policy_engine.py.jinja2",
            capability="CP04",
        )

    def _emit_tenant_context(self, auth_ir: AuthIR, output_dir: Path) -> GeneratedFile:
        """
        Emit tenant_context.py.

        Args:
            auth_ir: AuthIR instance
            output_dir: Output directory

        Returns:
            GeneratedFile instance
        """
        context = {
            "tenant_mode": auth_ir.tenant_mode.value,
        }

        content = self._render_template("tenant/tenant_context.py.jinja2", context)

        return GeneratedFile(
            path=output_dir / "tenant_context.py",
            content=content,
            template="tenant/tenant_context.py.jinja2",
            capability="CP02",
        )


# ============================================================================
# Generated File Dataclass
# ============================================================================


@dataclass
class GeneratedFile:
    """
    Generated File - File đã generate từ template.

    Attributes:
        path: Đường dẫn file
        content: Nội dung file đã generate
        template: Tên template đã dùng
        capability: Core Capability code (CP02, CP03, CP04)
    """
    path: Path
    content: str
    template: str
    capability: str


# ============================================================================
# Utility Functions
# ============================================================================


def emit_fastapi_auth(
    auth_ir: AuthIR,
    stack_dir: Path,
    output_dir: Path,
) -> list[GeneratedFile]:
    """
    Emit FastAPI auth code từ AuthIR.

    Convenience function.

    Args:
        auth_ir: AuthIR instance
        stack_dir: Templates directory
        output_dir: Output directory

    Returns:
        List of GeneratedFile instances
    """
    emitter = FastAPIAuthEmitter(stack_dir)
    return emitter.emit(auth_ir, output_dir)


__all__ = [
    "FastAPIAuthEmitter",
    "GeneratedFile",
    "emit_fastapi_auth",
]