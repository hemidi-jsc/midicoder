"""
Angular Frontend Auth Emitter (P2-002-C).

Module này cung cấp AngularAuthEmitter class để emit auth module
cho Angular frontend: AuthService, HttpInterceptor, AuthGuard, PermissionDirective.

Sử dụng inline templates (không cần Jinja2) vì nội dung đơn giản.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class GeneratedFile:
    """
    File đã generate.

    Attributes:
        path: Đường dẫn file tương đối
        content: Nội dung file
        template: Tên template
    """
    path: Path
    content: str
    template: str


class AngularAuthEmitter:
    """
    Emitter cho Angular auth module.

    Generate code cho:
    - AuthService: Quản lý JWT token, login/logout, permission checking
    - HttpInterceptor: Tự động attach JWT token vào HTTP requests
    - AuthGuard: Route guard kiểm tra authentication
    - PermissionDirective: Directive kiểm tra permission

    Usage:
        emitter = AngularAuthEmitter()
        files = emitter.emit(auth_config, output_dir)
    """

    def emit(
        self,
        auth_config: dict[str, Any],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """
        Emit Angular auth module.

        Args:
            auth_config: Auth config với keys: provider, roles, permissions
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []

        # Tạo auth directory
        auth_dir = output_dir / "auth"
        auth_dir.mkdir(parents=True, exist_ok=True)

        # Emit AuthService
        files.append(self._write_file(
            filename="auth.service.ts",
            content=self._generate_auth_service(auth_config),
            output_dir=auth_dir,
        ))

        # Emit HttpInterceptor
        files.append(self._write_file(
            filename="auth.interceptor.ts",
            content=self._generate_auth_interceptor(),
            output_dir=auth_dir,
        ))

        # Emit AuthGuard
        files.append(self._write_file(
            filename="auth.guard.ts",
            content=self._generate_auth_guard(),
            output_dir=auth_dir,
        ))

        # Emit PermissionDirective
        files.append(self._write_file(
            filename="permission.directive.ts",
            content=self._generate_permission_directive(auth_config),
            output_dir=auth_dir,
        ))

        return files

    def _generate_auth_service(self, auth_config: dict[str, Any]) -> str:
        """Generate AuthService."""
        provider = auth_config.get("provider", "jwt")
        roles = auth_config.get("roles", [])
        permissions = auth_config.get("permissions", [])

        roles_list = ", ".join(f"'{r}'" for r in roles) if roles else "'user'"
        permissions_list = ", ".join(f"'{p}'" for p in permissions) if permissions else "'read'"

        return (
            '/**\n'
            ' * Auth Service - Quản lý authentication và authorization.\n'
            ' *\n'
            f' * Provider: {provider}\n'
            ' * Features:\n'
            ' * - JWT token management\n'
            ' * - Login/Logout\n'
            ' * - Permission checking\n'
            ' */\n\n'
            'import { Injectable } from \'@angular/core\';\n'
            'import { BehaviorSubject } from \'rxjs\';\n\n'
            'export interface AuthUser {\n'
            '  id: string;\n'
            '  email: string;\n'
            '  roles: string[];\n'
            '  permissions: string[];\n'
            '}\n\n'
            '@Injectable({\n'
            '  providedIn: \'root\',\n'
            '})\n'
            'export class AuthService {\n'
            '  private readonly TOKEN_KEY = \'auth_token\';\n'
            '  private readonly USER_KEY = \'auth_user\';\n'
            '  private currentUserSubject = new BehaviorSubject<AuthUser | null>(null);\n'
            '  currentUser$ = this.currentUserSubject.asObservable();\n\n'
            '  constructor() {\n'
            '    // Load user từ localStorage khi khởi động\n'
            '    const userStr = localStorage.getItem(this.USER_KEY);\n'
            '    if (userStr) {\n'
            '      try {\n'
            '        this.currentUserSubject.next(JSON.parse(userStr));\n'
            '      } catch {\n'
            '        this.currentUserSubject.next(null);\n'
            '      }\n'
            '    }\n'
            '  }\n\n'
            '  login(token: string, user: AuthUser): void {\n'
            '    localStorage.setItem(this.TOKEN_KEY, token);\n'
            '    localStorage.setItem(this.USER_KEY, JSON.stringify(user));\n'
            '    this.currentUserSubject.next(user);\n'
            '  }\n\n'
            '  logout(): void {\n'
            '    localStorage.removeItem(this.TOKEN_KEY);\n'
            '    localStorage.removeItem(this.USER_KEY);\n'
            '    this.currentUserSubject.next(null);\n'
            '  }\n\n'
            '  getToken(): string | null {\n'
            '    return localStorage.getItem(this.TOKEN_KEY);\n'
            '  }\n\n'
            '  isAuthenticated(): boolean {\n'
            '    return this.getToken() !== null;\n'
            '  }\n\n'
            '  hasPermission(permission: string): boolean {\n'
            '    const user = this.currentUserSubject.value;\n'
            '    return user?.permissions.includes(permission) ?? false;\n'
            '  }\n\n'
            '  hasRole(role: string): boolean {\n'
            '    const user = this.currentUserSubject.value;\n'
            '    return user?.roles.includes(role) ?? false;\n'
            '  }\n'
            '}\n'
        )

    def _generate_auth_interceptor(self) -> str:
        """Generate HttpInterceptor."""
        return (
            '/**\n'
            ' * Auth Interceptor - Tự động attach JWT token vào HTTP requests.\n'
            ' *\n'
            ' * Mọi HTTP request sẽ được thêm Header Authorization: Bearer <token>.\n'
            ' */\n\n'
            'import { Injectable } from \'@angular/core\';\n'
            'import {\n'
            '  HttpInterceptor,\n'
            '  HttpRequest,\n'
            '  HttpHandler,\n'
            '  HttpEvent,\n'
            '} from \'@angular/common/http\';\n'
            'import { Observable } from \'rxjs\';\n'
            'import { AuthService } from \'./auth.service\';\n\n'
            '@Injectable()\n'
            'export class AuthInterceptor implements HttpInterceptor {\n'
            '  constructor(private authService: AuthService) {}\n\n'
            '  intercept(\n'
            '    request: HttpRequest<unknown>,\n'
            '    next: HttpHandler\n'
            '  ): Observable<HttpEvent<unknown>> {\n'
            '    const token = this.authService.getToken();\n\n'
            '    if (token) {\n'
            '      const cloned = request.clone({\n'
            '        setHeaders: {\n'
            '          Authorization: `Bearer ${token}`,\n'
            '        },\n'
            '      });\n'
            '      return next.handle(cloned);\n'
            '    }\n\n'
            '    return next.handle(request);\n'
            '  }\n'
            '}\n'
        )

    def _generate_auth_guard(self) -> str:
        """Generate AuthGuard."""
        return (
            '/**\n'
            ' * Auth Guard - Route guard kiểm tra authentication.\n'
            ' *\n'
            ' * Nếu user chưa đăng nhập, redirect về trang login.\n'
            ' */\n\n'
            'import { Injectable } from \'@angular/core\';\n'
            'import { CanActivate, Router } from \'@angular/router\';\n'
            'import { AuthService } from \'./auth.service\';\n\n'
            '@Injectable({\n'
            '  providedIn: \'root\',\n'
            '})\n'
            'export class AuthGuard implements CanActivate {\n'
            '  constructor(\n'
            '    private authService: AuthService,\n'
            '    private router: Router,\n'
            '  ) {}\n\n'
            '  canActivate(): boolean {\n'
            '    if (this.authService.isAuthenticated()) {\n'
            '      return true;\n'
            '    }\n\n'
            "    this.router.navigate(['/login']);\n"
            '    return false;\n'
            '  }\n'
            '}\n'
        )

    def _generate_permission_directive(self, auth_config: dict[str, Any]) -> str:
        """Generate PermissionDirective."""
        return (
            '/**\n'
            ' * Permission Directive - Directive kiểm tra permission.\n'
            ' *\n'
            ' * Usage: *appPermission="order:create"\n'
            ' * Nếu user không có permission, element sẽ bị ẩn.\n'
            ' */\n\n'
            'import {\n'
            '  Directive,\n'
            '  TemplateRef,\n'
            '  ViewContainerRef,\n'
            '} from \'@angular/core\';\n'
            'import { AuthService } from \'./auth.service\';\n\n'
            '@Directive({\n'
            '  selector: \'[appPermission]\',\n'
            '})\n'
            'export class PermissionDirective {\n'
            '  constructor(\n'
            '    private authService: AuthService,\n'
            '    private templateRef: TemplateRef<unknown>,\n'
            '    private viewContainer: ViewContainerRef,\n'
            '  ) {}\n\n'
            '  private permissionValue = \'\';\n\n'
            '  ngAfterViewInit(): void {\n'
            '    this._updateView();\n'
            '  }\n\n'
            '  @Input() set appPermission(permission: string) {\n'
            '    this.permissionValue = permission;\n'
            '    this._updateView();\n'
            '  }\n\n'
            '  private _updateView(): void {\n'
            '    if (this.authService.hasPermission(this.permissionValue)) {\n'
            '      this.viewContainer.createEmbeddedView(this.templateRef);\n'
            '    } else {\n'
            '      this.viewContainer.clear();\n'
            '    }\n'
            '  }\n'
            '}\n'
        )

    def _write_file(
        self,
        filename: str,
        content: str,
        output_dir: Path,
    ) -> GeneratedFile:
        """Write file và trả về GeneratedFile."""
        file_path = output_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        return GeneratedFile(
            path=file_path.relative_to(output_dir.parent),
            content=content,
            template=f"authnz/angular/{filename}",
        )


__all__ = ["AngularAuthEmitter", "GeneratedFile"]