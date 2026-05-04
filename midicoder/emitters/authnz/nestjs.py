"""
NestJS Auth Emitter Module.

Module này cung cấp NestJSEmitter để generate NestJS auth code
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

from midicoder.emitters.authnz.models import (
    AuthIR,
    JWTAuthConfig,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ============================================================================
# NestJS Auth Emitter Class
# ============================================================================


class NestJSEmitter:
    """
    Emitter cho NestJS authentication & authorization code.

    Generate code từ AuthIR cho:
    - src/auth/jwt-auth.guard.ts (CP03)
    - src/auth/rbac.service.ts (CP04)
    - src/auth/permissions.module.ts (CP04)
    - src/auth/policy_engine.ts (CP04)
    - src/auth/tenant_context.ts (CP02)

    Attributes:
        stack_dir: Đường dẫn đến templates directory
        template_env: Jinja2 Environment
    """

    def __init__(self, stack_dir: Path) -> None:
        """
        Khởi tạo NestJSEmitter.

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
        Emit NestJS auth code từ AuthIR.

        Process:
        1. Emit jwt-auth.guard.ts (CP03)
        2. Emit rbac.service.ts (CP04)
        3. Emit permissions.module.ts (CP04)
        4. Emit policy_engine.ts (CP04)
        5. Emit tenant_context.ts (CP02)
        6. Emit index.ts (exports)

        Args:
            auth_ir: AuthIR instance
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []

        # Create output directory
        auth_dir = output_dir / "src" / "auth"
        auth_dir.mkdir(parents=True, exist_ok=True)

        # Emit index.ts
        files.append(self._emit_index(auth_dir))

        # Emit jwt-auth.guard.ts
        files.append(self._emit_jwt_auth(auth_ir, auth_dir))

        # Emit rbac.service.ts
        files.append(self._emit_rbac_service(auth_ir, auth_dir))

        # Emit permissions.module.ts
        files.append(self._emit_permissions(auth_ir, auth_dir))

        # Emit policy_engine.ts
        files.append(self._emit_policy_engine(auth_ir, auth_dir))

        # Emit tenant_context.ts
        files.append(self._emit_tenant_context(auth_ir, auth_dir))

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

    def _emit_index(self, output_dir: Path) -> GeneratedFile:
        """
        Emit index.ts (exports file).

        Args:
            output_dir: Output directory

        Returns:
            GeneratedFile instance
        """
        file_path = output_dir / "index.ts"
        
        try:
            content = self._render_template(
                "auth/index.ts.jinja2",
                context={},
            )
        except Exception:
            # Fallback: generate basic index.ts
            content = '''/**
 * Auth Module Exports - NestJS Authentication & Authorization.
 * 
 * Module này xuất các components:
 * - JWT authentication guard
 * - RBAC service
 * - Permissions module
 * - Policy engine
 * - Tenant context
 * 
 * CP02: Multi-Tenant Architecture
 * CP03: Authentication & Authorization
 * CP04: RBAC & Policy Engine
 */

export * from "./jwt-auth.guard";
export * from "./rbac.service";
export * from "./permissions.module";
export * from "./policy_engine";
export * from "./tenant_context";
'''

        # Write file to disk
        file_path.write_text(content, encoding="utf-8")

        return GeneratedFile(
            path=file_path,
            content=content,
            template="auth/index.ts.jinja2",
            capability="CP02-CP04",
        )

    def _emit_jwt_auth(self, auth_ir: AuthIR, output_dir: Path) -> GeneratedFile:
        """
        Emit jwt-auth.guard.ts.

        Args:
            auth_ir: AuthIR instance
            output_dir: Output directory

        Returns:
            GeneratedFile instance
        """
        file_path = output_dir / "jwt-auth.guard.ts"
        
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

        try:
            content = self._render_template(
                "auth/jwt-auth.guard.ts.jinja2",
                context,
            )
        except Exception:
            # Fallback: generate basic jwt-auth.guard.ts
            content = '''import { Injectable, CanActivate, ExecutionContext } from "@nestjs/common";
import { Reflector } from "@nestjs/core";
import { JwtService } from "@nestjs/jwt";
import { Request } from "express";

/**
 * JWT Authentication Guard.
 * 
 * Guard này verify JWT token từ request và attach user vào request object.
 * 
 * KPI-029: Tenant-scoped authentication với tenant_id embed vào token.
 */
@Injectable()
export class JwtAuthGuard implements CanActivate {
  constructor(
    private jwtService: JwtService,
    private reflector: Reflector,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest();
    const token = this.extractTokenFromHeader(request);

    if (!token) {
      return false;
    }

    try {
      const payload = await this.jwtService.verifyAsync(token, {
        secret: process.env.JWT_SECRET,
      });

      // KPI-029: Tenant-scoped user context
      request["user"] = {
        sub: payload.sub,
        email: payload.email,
        tenantId: payload.tenantId,
        roles: payload.roles || [],
      };
    } catch {
      return false;
    }

    return true;
  }

  private extractTokenFromHeader(request: Request): string | undefined {
    const [type, token] = request.headers.authorization?.split(" ") ?? [];
    return type === "Bearer" ? token : undefined;
  }
}
'''

        # Write file to disk
        file_path.write_text(content, encoding="utf-8")

        return GeneratedFile(
            path=file_path,
            content=content,
            template="auth/jwt-auth.guard.ts.jinja2",
            capability="CP03",
        )

    def _emit_rbac_service(self, auth_ir: AuthIR, output_dir: Path) -> GeneratedFile:
        """
        Emit rbac.service.ts.

        Args:
            auth_ir: AuthIR instance
            output_dir: Output directory

        Returns:
            GeneratedFile instance
        """
        file_path = output_dir / "rbac.service.ts"
        
        # Build roles data for template
        roles_data = []
        for role_id, role in auth_ir.roles.items():
            roles_data.append({
                "id": role_id,
                "permissions": role.permissions,
                "parents": role.parents,
                "tenant_scoped": role.tenant_scoped,
                "description": role.description,
            })

        context = {
            "roles": roles_data,
            "policies": list(auth_ir.policies.values()),
        }

        try:
            content = self._render_template(
                "auth/rbac.decorator.ts.jinja2",
                context,
            )
        except Exception:
            # Fallback: generate basic rbac.service.ts
            content = '''import { Injectable, SetMetadata, createParamDecorator } from "@nestjs/common";

/**
 * RBAC Decorator - Permissions.
 * 
 * Decorator để set permission requirement cho endpoint.
 * 
 * KPI-028: Missing permission detection.
 */
export const PERMISSION_KEY = "permission";

export const Permissions = (...permissions: string[]) =>
  SetMetadata(PERMISSION_KEY, permissions);

/**
 * Permissions Decorator - Extract permissions from request user.
 * 
 * KPI-029: Tenant-scoped permissions.
 */
export const CurrentUser = createParamDecorator(
  (data: unknown, ctx: any) => {
    const request = ctx.switchToHttp().getRequest();
    return request.user;
  },
);

/**
 * RBAC Service - Permission checking service.
 * 
 * Service này quản lý role definitions và permission checking.
 * 
 * KPI-028: Missing permission detection
 * KPI-029: Missing tenant filter detection
 * KPI-030: Invalid role binding detection
 */
@Injectable()
export class RbacService {
  private roles: Map<string, RoleDefinition> = new Map();

  /**
   * Đăng ký role definition.
   * 
   * @param role - Role definition
   */
  registerRole(role: RoleDefinition): void {
    this.roles.set(role.id, role);
  }

  /**
   * Check user có permission hay không.
   * 
   * @param userRoles - List role IDs của user
   * @param requiredPermission - Permission cần check
   * @returns True nếu user có permission
   */
  hasPermission(userRoles: string[], requiredPermission: string): boolean {
    for (const roleId of userRoles) {
      const role = this.roles.get(roleId);
      if (!role) continue;

      // Check direct permissions
      if (this._checkPermission(role.permissions, requiredPermission)) {
        return true;
      }

      // Check inherited permissions from parents
      for (const parentId of role.parents || []) {
        const parentRole = this.roles.get(parentId);
        if (parentRole && this._checkPermission(parentRole.permissions, requiredPermission)) {
          return true;
        }
      }
    }

    return false;
  }

  /**
   * Check permission với wildcard support.
   * 
   * @param permissions - List permissions
   * @param requiredPermission - Permission cần check
   * @returns True nếu match
   */
  private _checkPermission(permissions: string[], requiredPermission: string): boolean {
    for (const perm of permissions) {
      if (perm === requiredPermission) {
        return true;
      }
      // Wildcard matching (ví dụ: "user:*" match "user:create")
      if (perm.endsWith(":*")) {
        const prefix = perm.slice(0, -1);
        if (requiredPermission.startsWith(prefix)) {
          return true;
        }
      }
    }
    return false;
  }
}

/**
 * Role Definition Interface.
 */
export interface RoleDefinition {
  id: string;
  permissions: string[];
  parents?: string[];
  tenantScoped?: boolean;
  description?: string;
}
'''

        # Write file to disk
        file_path.write_text(content, encoding="utf-8")

        return GeneratedFile(
            path=file_path,
            content=content,
            template="auth/rbac.decorator.ts.jinja2",
            capability="CP04",
        )

    def _emit_permissions(self, auth_ir: AuthIR, output_dir: Path) -> GeneratedFile:
        """
        Emit permissions.module.ts.

        Args:
            auth_ir: AuthIR instance
            output_dir: Output directory

        Returns:
            GeneratedFile instance
        """
        file_path = output_dir / "permissions.module.ts"
        
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

        try:
            content = self._render_template(
                "auth/permissions.module.ts.jinja2",
                context,
            )
        except Exception:
            # Fallback: generate basic permissions.module.ts
            content = '''import { Module, Global } from "@nestjs/common";
import { RbacService } from "./rbac.service";
import { JwtAuthGuard } from "./jwt-auth.guard";

/**
 * Permissions Module.
 * 
 * Module này cung cấp RBAC và JWT auth services cho toàn app.
 * 
 * KPI-028: Missing permission detection
 * KPI-029: Missing tenant filter detection
 */
@Global()
@Module({
  providers: [RbacService, JwtAuthGuard],
  exports: [RbacService, JwtAuthGuard],
})
export class PermissionsModule {}
'''

        # Write file to disk
        file_path.write_text(content, encoding="utf-8")

        return GeneratedFile(
            path=file_path,
            content=content,
            template="auth/permissions.module.ts.jinja2",
            capability="CP04",
        )

    def _emit_policy_engine(self, auth_ir: AuthIR, output_dir: Path) -> GeneratedFile:
        """
        Emit policy_engine.ts.

        Args:
            auth_ir: AuthIR instance
            output_dir: Output directory

        Returns:
            GeneratedFile instance
        """
        file_path = output_dir / "policy_engine.ts"
        
        context = {
            "policies": list(auth_ir.policies.values()),
        }

        content = self._render_template(
            "auth/policy_engine.ts.jinja2",
            context,
        )

        # Write file to disk
        file_path.write_text(content, encoding="utf-8")

        return GeneratedFile(
            path=file_path,
            content=content,
            template="auth/policy_engine.ts.jinja2",
            capability="CP04",
        )

    def _emit_tenant_context(self, auth_ir: AuthIR, output_dir: Path) -> GeneratedFile:
        """
        Emit tenant_context.ts.

        Args:
            auth_ir: AuthIR instance
            output_dir: Output directory

        Returns:
            GeneratedFile instance
        """
        file_path = output_dir / "tenant_context.ts"
        
        context = {
            "tenant_mode": auth_ir.tenant_mode.value,
        }

        content = self._render_template(
            "auth/tenant_context.ts.jinja2",
            context,
        )

        # Write file to disk
        file_path.write_text(content, encoding="utf-8")

        return GeneratedFile(
            path=file_path,
            content=content,
            template="auth/tenant_context.ts.jinja2",
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


def emit_nestjs_auth(
    auth_ir: AuthIR,
    stack_dir: Path,
    output_dir: Path,
) -> list[GeneratedFile]:
    """
    Emit NestJS auth code từ AuthIR.

    Convenience function.

    Args:
        auth_ir: AuthIR instance
        stack_dir: Templates directory
        output_dir: Output directory

    Returns:
        List of GeneratedFile instances
    """
    emitter = NestJSEmitter(stack_dir)
    return emitter.emit(auth_ir, output_dir)


__all__ = [
    "NestJSEmitter",
    "GeneratedFile",
    "emit_nestjs_auth",
]