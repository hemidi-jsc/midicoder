"""
CP03: Angular Authentication Emitter.

Module này cung cấp AngularEmitter để generate Angular auth code
từ AuthIR (CP03):
- Auth service
- Auth guard
- JWT interceptor
- Auth module

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.cp03_auth.models import AuthIR, JWTAuthConfig
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class AngularEmitter:
    """
    Emitter cho Angular authentication code.

    Generate code từ AuthIR cho:
    - src/app/core/auth/auth.service.ts
    - src/app/core/auth/auth.guard.ts
    - src/app/core/auth/jwt.interceptor.ts
    - src/app/core/auth/auth.module.ts
    """

    def __init__(self, stack_dir: Path) -> None:
        """
        Khởi tạo AngularEmitter.

        Args:
            stack_dir: Đường dẫn đến templates directory
        """
        self.stack_dir = stack_dir
        if not stack_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {stack_dir}")
        self.template_env = Environment(
            loader=FileSystemLoader(str(stack_dir)),
            autoescape=True, trim_blocks=True, lstrip_blocks=True,
        )

    def emit(self, auth_ir: AuthIR, output_dir: Path) -> list[GeneratedFile]:
        """
        Emit Angular auth code từ AuthIR.

        Args:
            auth_ir: AuthIR instance
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []
        auth_dir = output_dir / "src" / "app" / "core" / "auth"
        auth_dir.mkdir(parents=True, exist_ok=True)

        files.append(self._emit_auth_service(auth_ir, auth_dir))
        files.append(self._emit_auth_guard(auth_dir))
        files.append(self._emit_jwt_interceptor(auth_dir))
        files.append(self._emit_auth_module(auth_ir, auth_dir))
        files.append(self._emit_models(auth_dir))
        files.append(self._emit_index(auth_dir))

        return files

    def _emit_auth_service(self, auth_ir: AuthIR, output_dir: Path) -> GeneratedFile:
        """Emit auth.service.ts."""
        jwt_provider = auth_ir.get_jwt_provider()
        config = jwt_provider.config if jwt_provider else JWTAuthConfig()

        content = f'''import {{ Injectable }} from "@angular/core";
import {{ HttpClient }} from "@angular/common/http";
import {{ Observable, BehaviorSubject }} from "rxjs";
import {{ tap, take }} from "rxjs/operators";
import {{ User, AuthResponse }} from "./auth.models";

/**
 * Auth Service - CP03.
 *
 * Service này xử lý authentication cho Angular application.
 *
 * Configuration:
 * - Token expire: {config.expire_minutes} minutes
 * - Algorithm: {config.algorithm}
 */
@Injectable({{
  providedIn: "root",
}})
export class AuthService {{
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  private apiUrl = "/api/auth";

  constructor(private http: HttpClient) {{}}

  /**
   * Login user.
   */
  login(credentials: {{ email: string; password: string }}): Observable<AuthResponse> {{
    return this.http.post<AuthResponse>(`${{this.apiUrl}}/login`, credentials).pipe(
      tap(response => {{
        localStorage.setItem("access_token", response.access_token);
        if (response.refresh_token) {{
          localStorage.setItem("refresh_token", response.refresh_token);
        }}
        this.currentUserSubject.next(response.user);
      }}),
    );
  }}

  /**
   * Logout user.
   */
  logout(): Observable<void> {{
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    this.currentUserSubject.next(null);
    return this.http.post<void>(`${{this.apiUrl}}/logout`, {{}});
  }}

  /**
   * Refresh access token.
   */
  refreshToken(): Observable<AuthResponse> {{
    const refreshTok = localStorage.getItem("refresh_token");
    if (!refreshTok) {{
      throw new Error("No refresh token available");
    }}
    return this.http.post<AuthResponse>(`${{this.apiUrl}}/refresh`, {{
      refresh_token: refreshTok,
    }}).pipe(
      tap(response => {{
        localStorage.setItem("access_token", response.access_token);
        this.currentUserSubject.next(response.user);
      }}),
    );
  }}

  /**
   * Lấy current user.
   */
  getCurrentUser(): User | null {{
    return this.currentUserSubject.value;
  }}

  /**
   * Observable cho current user.
   */
  currentUser$() {{
    return this.currentUserSubject.asObservable();
  }}

  /**
   * Kiểm tra user đã auth chưa.
   */
  isLoggedIn(): boolean {{
    return !!localStorage.getItem("access_token");
  }}

  /**
   * Lấy access token.
   */
  getAccessToken(): string | null {{
    return localStorage.getItem("access_token");
  }}
}}
'''
        file_path = output_dir / "auth.service.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(path=file_path, content=content, template="auth/auth.service.ts.jinja2", capability="CP03")

    def _emit_auth_guard(self, output_dir: Path) -> GeneratedFile:
        """Emit auth.guard.ts."""
        content = '''import { Injectable } from "@angular/core";
import {
  CanActivate,
  ActivatedRouteSnapshot,
  RouterStateSnapshot,
  Router,
} from "@angular/router";
import { AuthService } from "./auth.service";

/**
 * Auth Guard - CP03.
 *
 * Guard này kiểm tra authentication trước khi navigate.
 */
@Injectable({
  providedIn: "root",
})
export class AuthGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router,
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot,
  ): boolean {
    if (this.authService.isLoggedIn()) {
      return true;
    }

    // Redirect đến login page
    this.router.navigate(["/login"], {{ queryParams: {{ returnUrl: state.url }} }});
    return false;
  }
}
'''
        file_path = output_dir / "auth.guard.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(path=file_path, content=content, template="auth/auth.guard.ts.jinja2", capability="CP03")

    def _emit_jwt_interceptor(self, output_dir: Path) -> GeneratedFile:
        """Emit jwt.interceptor.ts."""
        content = '''import { Injectable } from "@angular/core";
import {
  HttpInterceptor,
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpErrorResponse,
} from "@angular/common/http";
import { Observable, throwError } from "rxjs";
import { catchError } from "rxjs/operators";
import { AuthService } from "./auth.service";

/**
 * JWT Interceptor - CP03.
 *
 * Interceptor này attach JWT token vào mọi HTTP request.
 */
@Injectable({
  providedIn: "root",
})
export class JwtInterceptor implements HttpInterceptor {
  constructor(private authService: AuthService) {}

  intercept(
    request: HttpRequest<unknown>,
    next: HttpHandler,
  ): Observable<HttpEvent<unknown>> {
    const token = this.authService.getAccessToken();

    if (token) {
      request = request.clone({
        setHeaders: { Authorization: `Bearer ${token}` },
      });
    }

    return next.handle(request).pipe(
      catchError((error: HttpErrorResponse) => {
        if (error.status === 401) {
          // Token hết hạn — thử refresh
          if (!this._isRefreshing) {
            this._isRefreshing = true;
            this._refreshSubject.next(undefined);

            return this.authService.refreshToken().pipe(
              catchError((err) => {
                this._isRefreshing = false;
                this.authService.logout().subscribe();
                this._refreshSubject.error(err);
                return throwError(() => err);
              }),
              (response) => {{
                this._isRefreshing = false;
                this._refreshSubject.next(response.access_token);
                return next.handle(request.clone({{
                  setHeaders: {{ Authorization: `Bearer ${{response.access_token}}` }},
                }}));
              }},
            );
          } else {{
            return this._refreshSubject.pipe(
              (token) => next.handle(request.clone({{
                setHeaders: {{ Authorization: `Bearer ${{token}}` }},
              }})),
              catchError(() => throwError(() => error)),
            );
          }}
        }
        return throwError(() => error);
      }},
    );
  }

  private _isRefreshing = false;
  private _refreshSubject = new BehaviorSubject<string | undefined>(undefined);
}
'''
        file_path = output_dir / "jwt.interceptor.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(path=file_path, content=content, template="auth/jwt.interceptor.ts.jinja2", capability="CP03")

    def _emit_auth_module(self, auth_ir: AuthIR, output_dir: Path) -> GeneratedFile:
        """Emit auth.module.ts."""
        content = '''import { NgModule } from "@angular/core";
import { CommonModule } from "@angular/common";
import { HttpClientModule, HTTP_INTERCEPTORS } from "@angular/common/http";
import { JwtInterceptor } from "./jwt.interceptor";

/**
 * Auth Module - CP03.
 *
 * Module này cung cấp authentication services và interceptors.
 */
@NgModule({
  imports: [CommonModule, HttpClientModule],
  providers: [
    {{
      provide: HTTP_INTERCEPTORS,
      useClass: JwtInterceptor,
      multi: true,
    }},
  ],
})
export class AuthModule {}
'''
        file_path = output_dir / "auth.module.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(path=file_path, content=content, template="auth/auth.module.ts.jinja2", capability="CP03")

    def _emit_models(self, output_dir: Path) -> GeneratedFile:
        """Emit auth.models.ts."""
        content = '''/**
 * Auth Models - CP03.
 */

export interface User {{
  id: string;
  email: string;
  tenant_id?: string;
  roles?: string[];
  permissions?: string[];
  disabled?: boolean;
}}

export interface AuthResponse {{
  access_token: string;
  refresh_token?: string;
  user: User;
}}

export interface LoginCredentials {{
  email: string;
  password: string;
}}
'''
        file_path = output_dir / "auth.models.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(path=file_path, content=content, template="auth/auth.models.ts.jinja2", capability="CP03")

    def _emit_index(self, output_dir: Path) -> GeneratedFile:
        """Emit index.ts."""
        content = '''/**
 * Auth Module Exports - CP03.
 */
export * from "./auth.module";
export * from "./auth.service";
export * from "./auth.guard";
export * from "./jwt.interceptor";
export * from "./auth.models";
'''
        file_path = output_dir / "index.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(path=file_path, content=content, template="auth/index.ts.jinja2", capability="CP03")


@dataclass
class GeneratedFile:
    """Generated File."""
    path: Path
    content: str
    template: str
    capability: str


def emit_angular_auth(
    auth_ir: AuthIR,
    stack_dir: Path,
    output_dir: Path,
) -> list[GeneratedFile]:
    """Emit Angular auth code."""
    emitter = AngularEmitter(stack_dir)
    return emitter.emit(auth_ir, output_dir)


__all__ = ["AngularEmitter", "GeneratedFile", "emit_angular_auth"]