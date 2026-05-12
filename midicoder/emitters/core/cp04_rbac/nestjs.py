"""
CP04: NestJS RBAC Emitter.

Module này cung cấp NestJSRBACEmitter để generate NestJS RBAC code:
- RolesGuard: NestJS canActivate cho role-based access
- PolicyGuard: NestJS canActivate cho ABAC policy evaluation
- RBACService: Service layer
- Decorators: @Roles(), @Policies()

Tất cả comments bằng tiếng Việt.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class GeneratedFile:
    """File đã generate từ emitter."""
    path: Path
    content: str
    template: str = ""
    capability: str = "CP04"


class NestJSRBACEmitter:
    """
    Emitter cho NestJS RBAC code.

    Generate code tu RBACConfig cho:
    - rbac/rbac.service.ts
    - rbac/roles.guard.ts
    - rbac/policy.guard.ts
    - rbac/decorators.ts
    - rbac/rbac.module.ts
    """

    def __init__(self, config: Any) -> None:
        self._config = config

    def generate(self) -> dict[str, str]:
        """Generate toàn bộ NestJS RBAC code."""
        result: dict[str, str] = {}
        result["src/core/rbac/rbac.module.ts"] = self._generate_module()
        result["src/core/rbac/rbac.service.ts"] = self._generate_service()
        result["src/core/rbac/roles.guard.ts"] = self._generate_roles_guard()
        result["src/core/rbac/policy.guard.ts"] = self._generate_policy_guard()
        result["src/core/rbac/decorators.ts"] = self._generate_decorators()
        return result

    def emit(self, output_dir: Path) -> list[GeneratedFile]:
        """Emit files vào output directory."""
        files: list[GeneratedFile] = []
        for path_str, content in self.generate().items():
            file_path = output_dir / path_str
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            files.append(GeneratedFile(path=file_path, content=content))
        return files

    def _generate_module(self) -> str:
        return '''import { Module, Global } from "@nestjs/common";
import { RBACService } from "./rbac.service";
import { RolesGuard } from "./roles.guard";
import { PolicyGuard } from "./policy.guard";

/**
 * RBAC Module - CP04.
 *
  * Module này cung cấp Role-Based Access Control và Policy Engine cho NestJS.
  * Export các guard và service để sử dụng trong toàn bộ app.
 */
@Global()
@Module({
  providers: [RBACService, RolesGuard, PolicyGuard],
  exports: [RBACService, RolesGuard, PolicyGuard],
})
export class RBACModule {}
'''

    def _generate_service(self) -> str:
        return '''import { Injectable } from "@nestjs/common";

/**
 * RBAC Service - CP04.
 *
 * Service layer cho Role-Based Access Control va Policy Evaluation.
 */
@Injectable()
export class RBACService {
  private roles: Map<string, { permissions: string[]; parentRoles: string[] }> = new Map();
  private policies: Array<{
    id: string;
    effect: "allow" | "deny";
    condition: string;
    resourceType?: string;
    actions?: string[];
  }> = [];

  /** Dang ky role moi */
  registerRole(
    name: string,
    permissions: string[] = [],
    parentRoles: string[] = [],
  ): void {
    this.roles.set(name, { permissions, parentRoles });
  }

  /** Dang ky policy rule moi */
  registerPolicy(
    id: string,
    effect: "allow" | "deny",
    condition: string,
    resourceType?: string,
    actions?: string[],
  ): void {
    this.policies.push({ id, effect, condition, resourceType, actions });
  }

  /** Kiểm tra user có role yêu cầu (bao gồm inheritance) */
  checkRole(userRoles: string[], requiredRole: string): boolean {
    if (userRoles.includes(requiredRole)) return true;

    for (const roleName of userRoles) {
      if (this._roleInherits(roleName, requiredRole)) return true;
    }
    return false;
  }

  /** Kiem tra user co permission cho resource:action */
  checkPermission(
    userRoles: string[],
    resource: string,
    action: string,
  ): boolean {
    const permissionId = `${resource.toLowerCase()}.${action}`;
    const allPermissions = this._gatherPermissions(userRoles);
    return allPermissions.has(permissionId);
  }

  /** Evaluate ABAC policy voi context */
  checkPolicy(context: {
    action: string;
    user: Record<string, unknown>;
    resource: Record<string, unknown>;
    env: Record<string, unknown>;
  }): { allowed: boolean; policyId: string; reason: string } {
    // Simple evaluation - trong production se goi PolicyEngine
    for (const policy of this.policies) {
      if (policy.actions && !policy.actions.includes(context.action)) continue;
      if (policy.resourceType && policy.resourceType !== context.resource["type"]) continue;

      // Evaluate condition (simple string match)
      if (this._evaluateCondition(policy.condition, context)) {
        return {
          allowed: policy.effect === "allow",
          policyId: policy.id,
          reason: `Policy '${policy.id}' matched — effect: ${policy.effect}`,
        };
      }
    }

    return {
      allowed: false,
      policyId: "",
      reason: "Khong co policy nao match — default DENY",
    };
  }

  private _roleInherits(roleName: string, target: string): boolean {
    const role = this.roles.get(roleName);
    if (!role) return false;

    for (const parentName of role.parentRoles) {
      if (parentName === target) return true;
      if (this._roleInherits(parentName, target)) return true;
    }
    return false;
  }

  private _gatherPermissions(userRoles: string[]): Set<string> {
    const permissions = new Set<string>();
    for (const roleName of userRoles) {
      const role = this.roles.get(roleName);
      if (role) {
        role.permissions.forEach((p) => permissions.add(p));
        for (const parentName of role.parentRoles) {
          const parent = this.roles.get(parentName);
          if (parent) {
            parent.permissions.forEach((p) => permissions.add(p));
          }
        }
      }
    }
    return permissions;
  }

  private _evaluateCondition(
    condition: string,
    context: Record<string, unknown>,
  ): boolean {
    // Simple evaluation — trong production sẽ sử dụng PolicyEngine AST parser
    try {
      // Co the mo phong: "user.role == 'admin'" -> context.user.role === "admin"
      // Day la fallback — chi support simple equality
      const parts = condition.split("==").map((s) => s.trim());
      if (parts.length === 2) {
        const leftVal = this._resolvePath(parts[0], context);
        const rightRaw = parts[1].replace(/['"]/g, "");
        return leftVal === rightRaw;
      }
    } catch {
      // Ignore errors
    }
    return false;
  }

  private _resolvePath(path: string, ctx: Record<string, unknown>): unknown {
    const parts = path.split(".");
    let current: unknown = ctx;
    for (const part of parts) {
      if (current && typeof current === "object" && part in (current as object)) {
        current = (current as Record<string, unknown>)[part];
      } else {
        return undefined;
      }
    }
    return current;
  }
}
'''

    def _generate_roles_guard(self) -> str:
        return '''import {
  CanActivate,
  ExecutionContext,
  ForbiddenException,
  Injectable,
} from "@nestjs/common";
import { Reflector } from "@nestjs/core";
import { RBACService } from "./rbac.service";
import { ROLES_KEY, PERMISSIONS_KEY } from "./decorators";

/**
 * Roles Guard - CP04.
 *
  * NestJS canActivate cho role-based access control.
  * Sử dụng @Roles() decorator để chỉ định roles được phép.
 */
@Injectable()
export class RolesGuard implements CanActivate {
  constructor(
    private reflector: Reflector,
    private rbacService: RBACService,
  ) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredRoles = this.reflector.getAllAndOverride<string[]>(
      ROLES_KEY,
      [context.getHandler(), context.getClass()],
    );

    const requiredPermissions = this.reflector.getAllAndOverride<string[]>(
      PERMISSIONS_KEY,
      [context.getHandler(), context.getClass()],
    );

    if (!requiredRoles && !requiredPermissions) {
      return true; // Không có yêu cầu -> cho phép
    }

    const request = context.switchToHttp().getRequest();
    const user = request.user;

    if (!user) {
      throw new ForbiddenException("Khong tim thay user");
    }

    const userRoles = user.roles || [];
    const userPermissions = user.permissions || [];

    // Kiem tra roles
    if (requiredRoles) {
      const hasRole = requiredRoles.some((role) =>
        this.rbacService.checkRole(userRoles, role),
      );
      if (!hasRole && !requiredPermissions) {
        throw new ForbiddenException(`Yeu cau role: ${requiredRoles.join(", ")}`);
      }
    }

    // Kiem tra permissions
    if (requiredPermissions) {
      const hasPermission = requiredPermissions.some((perm) =>
        userPermissions.includes(perm),
      );
      if (!hasPermission && !requiredRoles) {
        throw new ForbiddenException(
          `Yeu cau permission: ${requiredPermissions.join(", ")}`,
        );
      }
    }

    return true;
  }
}
'''

    def _generate_policy_guard(self) -> str:
        return '''import {
  CanActivate,
  ExecutionContext,
  ForbiddenException,
  Injectable,
} from "@nestjs/common";
import { Reflector } from "@nestjs/core";
import { RBACService } from "./rbac.service";
import { POLICY_ACTION_KEY } from "./decorators";

/**
 * Policy Guard - CP04.
 *
  * NestJS canActivate cho ABAC policy evaluation.
  * Sử dụng @Policies() decorator để chỉ định action.
 */
@Injectable()
export class PolicyGuard implements CanActivate {
  constructor(
    private reflector: Reflector,
    private rbacService: RBACService,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const action = this.reflector.getAllAndOverride<string>(
      POLICY_ACTION_KEY,
      [context.getHandler(), context.getClass()],
    );

    if (!action) {
      return true; // Không có policy check -> cho phép
    }

    const request = context.switchToHttp().getRequest();
    const user = request.user || {};

    // Xay policy context
    const policyContext = {
      action,
      user: {
        role: user.role || "",
        roles: user.roles || [],
        tenant_id: user.tenant_id || "",
      },
      resource: {
        type: request.body?.type || "",
        tenant_id: request.body?.tenant_id || "",
      },
      env: {
        ip: request.ip || "",
        method: request.method,
        path: request.url || "",
      },
    };

    const decision = this.rbacService.checkPolicy(policyContext);

    if (!decision.allowed) {
      throw new ForbiddenException(decision.reason || "Policy deny");
    }

    return true;
  }
}
'''

    def _generate_decorators(self) -> str:
        return '''import { SetMetadata, applyDecorators } from "@nestjs/common";

/**
 * RBAC Decorators - CP04.
 *
 * Cac decorator de chi dinh role/permission/policy requirements.
 */

// Key constants
export const ROLES_KEY = "rbac_roles";
export const PERMISSIONS_KEY = "rbac_permissions";
export const POLICY_ACTION_KEY = "rbac_policy_action";

/**
 * @Roles() - Chỉ định roles được phép truy cập.
 *
 * Usage:
 *   @Roles("admin", "manager")
 *   @Get("admin")
 *   adminPage() { ... }
 */
export function Roles(...roles: string[]) {
  return SetMetadata(ROLES_KEY, roles);
}

/**
 * @Permissions() - Chỉ định permissions được phép.
 *
 * Usage:
 *   @Permissions("order:create", "order:update")
 *   @Post("orders")
 *   createOrder() { ... }
 */
export function Permissions(...permissions: string[]) {
  return SetMetadata(PERMISSIONS_KEY, permissions);
}

/**
 * @Policies() - Chỉ định action cho policy evaluation.
 *
 * Usage:
 *   @Policies("order:create")
 *   @Post("orders")
 *   createOrder() { ... }
 */
export function Policies(action: string) {
  return SetMetadata(POLICY_ACTION_KEY, action);
}

/**
 * @RequireAuth() - Kết hợp @Roles() với RolesGuard.
 *
 * Usage:
 *   @RequireAuth("admin")
 *   @Get("admin")
 *   adminPage() { ... }
 */
export function RequireAuth(...roles: string[]) {
  return applyDecorators(Roles(...roles));
}
'''