"""
CP04: Angular RBAC Emitter.

Module này cung cấp AngularRBACEmitter để generate Angular RBAC code:
- RbacService: Service cho role/permission checks
- RoleGuard: Route guard (canActivate, canMatch)
- PermissionDirective: *appPermission directive

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
    """File da generate tu emitter."""
    path: Path
    content: str
    template: str = ""
    capability: str = "CP04"


class AngularRBACEmitter:
    """
    Emitter cho Angular RBAC code.

    Generate code tu RBACConfig cho:
    - rbac/rbac.service.ts
    - rbac/role.guard.ts
    - rbac/permission.directive.ts
    - rbac/rbac.module.ts
    """

    def __init__(self, config: Any) -> None:
        self._config = config

    def generate(self) -> dict[str, str]:
        """Generate toan bo Angular RBAC code."""
        result: dict[str, str] = {}
        result["src/app/core/rbac/rbac.service.ts"] = self._generate_service()
        result["src/app/core/rbac/role.guard.ts"] = self._generate_guard()
        result["src/app/core/rbac/permission.directive.ts"] = self._generate_directive()
        return result

    def emit(self, output_dir: Path) -> list[GeneratedFile]:
        """Emit files vao output directory."""
        files: list[GeneratedFile] = []
        for path_str, content in self.generate().items():
            file_path = output_dir / path_str
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            files.append(GeneratedFile(path=file_path, content=content))
        return files

    def _generate_service(self) -> str:
        return '''import { Injectable } from "@angular/core";
import { BehaviorSubject, Observable } from "rxjs";

/**
 * RBAC Service - CP04.
 *
 * Service cho Role-Based Access Control trong Angular.
 * Kiem tra role va permission cua user hien tai.
 */
@Injectable({
  providedIn: "root",
})
export class RbacService {
  private userRoles = new BehaviorSubject<string[]>([]);
  private userPermissions = new BehaviorSubject<string[]>([]);

  /** Observable cho danh sach roles */
  roles$ = this.userRoles.asObservable();
  /** Observable cho danh sach permissions */
  permissions$ = this.userPermissions.asObservable();

  /**
   * Cap nhat roles cua user.
   * Goi sau khi user login.
   */
  setRoles(roles: string[]): void {
    this.userRoles.next(roles);
  }

  /**
   * Cap nhat permissions cua user.
   * Goi sau khi user login.
   */
  setPermissions(permissions: string[]): void {
    this.userPermissions.next(permissions);
  }

  /**
   * Kiem tra user co role khong.
   *
   * @param role - Role can kiem tra
   * @returns True neu user co role
   */
  hasRole(role: string): boolean {
    return this.userRoles.value.includes(role);
  }

  /**
   * Kiem tra user co bat ky role nao trong danh sach khong (OR logic).
   *
   * @param roles - Danh sach roles
   * @returns True neu user co it nhat mot role
   */
  hasAnyRole(roles: string[]): boolean {
    const currentRoles = this.userRoles.value;
    return roles.some((role) => currentRoles.includes(role));
  }

  /**
   * Kiem tra user co tat ca roles khong (AND logic).
   *
   * @param roles - Danh sach roles
   * @returns True neu user co tat ca roles
   */
  hasAllRoles(roles: string[]): boolean {
    const currentRoles = this.userRoles.value;
    return roles.every((role) => currentRoles.includes(role));
  }

  /**
   * Kiem tra user co permission khong.
   *
   * @param permission - Permission can kiem tra (vd: "order:create")
   * @returns True neu user co permission
   */
  hasPermission(permission: string): boolean {
    return this.userPermissions.value.includes(permission);
  }

  /**
   * Kiem tra user co bat ky permission nao khong (OR logic).
   *
   * @param permissions - Danh sach permissions
   * @returns True neu user co it nhat mot permission
   */
  hasAnyPermission(permissions: string[]): boolean {
    const currentPerms = this.userPermissions.value;
    return permissions.some((perm) => currentPerms.includes(perm));
  }

  /**
   * Lay tat ca roles cua user.
   */
  getRoles(): string[] {
    return [...this.userRoles.value];
  }

  /**
   * Lay tat ca permissions cua user.
   */
  getPermissions(): string[] {
    return [...this.userPermissions.value];
  }

  /**
   * Xoa toan bo roles va permissions (logout).
   */
  clear(): void {
    this.userRoles.next([]);
    this.userPermissions.next([]);
  }
}
'''

    def _generate_guard(self) -> str:
        return '''import {
  CanActivate,
  CanMatch,
  Route,
  Router,
  UrlSegment,
} from "@angular/router";
import { Injectable } from "@angular/core";
import { RbacService } from "./rbac.service";

/**
 * Role Guard - CP04.
 *
 * Route guard cho role-based access control.
 * Su dung trong route config:
 *
 * ```ts
 * {
 *   path: "admin",
 *   canActivate: [RoleGuard],
 *   data: { requiredRoles: ["admin"] },
 *   component: AdminComponent
 * }
 * ```
 */
@Injectable({
  providedIn: "root",
})
export class RoleGuard implements CanActivate, CanMatch {
  constructor(
    private rbac: RbacService,
    private router: Router,
  ) {}

  canActivate(route: Route): boolean {
    const requiredRoles = route.data?.["requiredRoles"] as string[] | undefined;
    const requiredPermissions = route.data?.["requiredPermissions"] as string[] | undefined;

    if (!requiredRoles && !requiredPermissions) {
      return true; // Khong co yeu cau
    }

    // Kiem tra roles
    if (requiredRoles) {
      if (this.rbac.hasAnyRole(requiredRoles)) {
        return true;
      }
    }

    // Kiem tra permissions
    if (requiredPermissions) {
      if (this.rbac.hasAnyPermission(requiredPermissions)) {
        return true;
      }
    }

    // Khong du quyen -> chuyen den trang 403
    this.router.navigate(["/forbidden"]);
    return false;
  }

  canMatch(
    route: Route,
    segments: UrlSegment[],
  ): boolean {
    return this.canActivate(route);
  }
}
'''

    def _generate_directive(self) -> str:
        return '''import {
  Directive,
  Input,
  TemplateRef,
  ViewContainerRef,
  OnInit,
  OnChanges,
} from "@angular/core";
import { RbacService } from "./rbac.service";

/**
 * Permission Directive - CP04.
 *
 * Directive de hien thi/ẩn UI elements theo role hoac permission.
 *
 * Su dung:
 * ```html
 * <!-- Kiem tra role -->
 * <button *appPermission="{ roles: ['admin'] }">Admin Action</button>
 *
 * <!-- Kiem tra permission -->
 * <button *appPermission="{ permissions: ['order:delete'] }">Delete</button>
 *
 * <!-- Kiem tra ca role va permission -->
 * <div *appPermission="{ roles: ['admin'], permissions: ['user:manage'] }">
 *   Admin Panel
 * </div>
 * ```
 */
@Directive({
  selector: "[appPermission]",
  standalone: true,
})
export class PermissionDirective implements OnInit, OnChanges {
  @Input() appPermission: {
    roles?: string[];
    permissions?: string[];
  } = {};

  private hasPermission = false;

  constructor(
    private rbac: RbacService,
    private template: TemplateRef<unknown>,
    private viewContainer: ViewContainerRef,
  ) {}

  ngOnInit(): void {
    this._evaluate();
  }

  ngOnChanges(): void {
    this._evaluate();
  }

  private _evaluate(): void {
    this.hasPermission = false;

    // Khong co yeu cau -> cho phep
    if (!this.appPermission.roles && !this.appPermission.permissions) {
      this.hasPermission = true;
      return;
    }

    // Kiem tra roles (OR logic)
    if (this.appPermission.roles) {
      const hasRole = this.appPermission.roles.some((role) =>
        this.rbac.hasRole(role),
      );
      if (hasRole) {
        this.hasPermission = true;
      }
    }

    // Kiem tra permissions (OR logic)
    if (this.appPermission.permissions && !this.hasPermission) {
      const hasPermission = this.appPermission.permissions.some((perm) =>
        this.rbac.hasPermission(perm),
      );
      if (hasPermission) {
        this.hasPermission = true;
      }
    }

    // Render hoac ẩn element
    if (this.hasPermission) {
      this.viewContainer.createEmbeddedView(this.template);
    } else {
      this.viewContainer.clear();
    }
  }
}
'''