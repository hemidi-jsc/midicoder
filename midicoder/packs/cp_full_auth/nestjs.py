"""
CP03: NestJS Authentication Emitter.

Module này cung cấp NestJSEmitter để generate NestJS auth code
từ AuthIR (CP03):
- JWT authentication guard
- Auth service
- Permission decorator

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_full_auth.models import (
    AuthIR,
    JWTAuthConfig,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ============================================================================
# NestJS Auth Emitter Class
# ============================================================================


class NestJSEmitter:
    """
    Emitter cho NestJS authentication code.

    Generate code từ AuthIR cho:
    - src/auth/jwt-auth.guard.ts
    - src/auth/auth.service.ts
    - src/auth/permissions.decorator.ts
    - src/auth/auth.module.ts

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

        self.template_env = Environment(
            loader=FileSystemLoader(str(stack_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def emit(self, auth_ir: AuthIR, output_dir: Path) -> list[GeneratedFile]:
        """
        Emit NestJS auth code từ AuthIR.

        Args:
            auth_ir: AuthIR instance
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []

        auth_dir = output_dir / "src" / "auth"
        auth_dir.mkdir(parents=True, exist_ok=True)

        # Emit auth.module.ts
        files.append(self._emit_auth_module(auth_ir, auth_dir))

        # Emit jwt-auth.guard.ts
        jwt_provider = auth_ir.get_jwt_provider()
        if jwt_provider:
            files.append(self._emit_jwt_guard(auth_ir, auth_dir))

        # Emit auth.service.ts
        files.append(self._emit_auth_service(auth_ir, auth_dir))

        # Emit permissions.decorator.ts
        files.append(self._emit_permissions(auth_ir, auth_dir))

        # Emit index.ts
        files.append(self._emit_index(auth_dir))

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
        """
        try:
            template = self.template_env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            EM.raise_error(
                ErrorCode.CODE_TEMPLATE_NOT_FOUND,
                template_name=template_name,
            )
        except Exception as e:
            EM.raise_error(
                ErrorCode.TEMPLATE_RENDER_FAILED,
                template_name=template_name,
                cause=e,
            )

    def _emit_auth_module(self, auth_ir: AuthIR, output_dir: Path) -> GeneratedFile:
        """Emit auth.module.ts."""
        content = '''import { Global, Module } from "@nestjs/common";
import { JwtModule } from "@nestjs/jwt";
import { PassportModule } from "@nestjs/passport";
import { AuthService } from "./auth.service";
import { JwtAuthGuard } from "./jwt-auth.guard";

/**
 * Auth Module - CP03.
 *
 * Module này cung cấp authentication services và guards.
 */
@Global()
@Module({
  imports: [
    PassportModule.register({ defaultStrategy: "jwt" }),
    JwtModule.register({
      secret: process.env.JWT_SECRET,
      signOptions: {
        expiresIn: process.env.ACCESS_TOKEN_EXPIRE || "30m",
        algorithm: process.env.JWT_ALGORITHM || "HS256",
      },
    }),
  ],
  providers: [AuthService, JwtAuthGuard],
  exports: [AuthService, JwtAuthGuard, JwtModule],
})
export class AuthModule {}
'''
        file_path = output_dir / "auth.module.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(path=file_path, content=content, template="auth/auth.module.ts.jinja2", capability="CP03")

    def _emit_jwt_guard(self, auth_ir: AuthIR, output_dir: Path) -> GeneratedFile:
        """Emit jwt-auth.guard.ts."""
        jwt_provider = auth_ir.get_jwt_provider()
        config = jwt_provider.config if jwt_provider else JWTAuthConfig()

        content = f'''import {{
  CanActivate,
  ExecutionContext,
  Injectable,
  UnauthorizedException,
}} from "@nestjs/common";
import {{ Reflector }} from "@nestjs/core";
import {{ JwtService }} from "@nestjs/jwt";
import {{ Request }} from "express";

/**
 * JWT Authentication Guard - CP03.
 *
 * Guard này verify JWT token từ request và attach user vào request object.
 *
 * Configuration:
 * - Algorithm: {config.algorithm}
 * - Tenant scoped: {config.tenant_scoped}
 */
@Injectable()
export class JwtAuthGuard implements CanActivate {{
  constructor(
    private jwtService: JwtService,
    private reflector: Reflector,
  ) {{}}

  async canActivate(context: ExecutionContext): Promise<boolean> {{
    const request = context.switchToHttp().getRequest();
    const token = this.extractTokenFromHeader(request);

    if (!token) {{
      throw new UnauthorizedException("Thiếu authentication token");
    }}

    try {{
      const payload = await this.jwtService.verifyAsync(token, {{
        secret: process.env.JWT_SECRET,
        algorithms: ["{config.algorithm}"],
      }});

      // Attach user payload to request
      request["user"] = payload;
    }} catch {{
      throw new UnauthorizedException("Token không hợp lệ hoặc đã hết hạn");
    }}

    return true;
  }}

  private extractTokenFromHeader(request: Request): string | undefined {{
    const [type, token] = request.headers.authorization?.split(" ") ?? [];
    return type === "Bearer" ? token : undefined;
  }}
}}
'''
        file_path = output_dir / "jwt-auth.guard.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(path=file_path, content=content, template="auth/jwt-auth.guard.ts.jinja2", capability="CP03")

    def _emit_auth_service(self, auth_ir: AuthIR, output_dir: Path) -> GeneratedFile:
        """Emit auth.service.ts."""
        content = '''import { Injectable } from "@nestjs/common";
import { JwtService } from "@nestjs/jwt";

export interface TokenPayload {{
  sub: string;
  email: string;
  tenant_id?: string;
  roles?: string[];
}}

export interface TokenResponse {{
  access_token: string;
  refresh_token?: string;
}}

/**
 * Auth Service - CP03.
 *
 * Service này xử lý token creation và verification.
 */
@Injectable()
export class AuthService {{
  constructor(private jwtService: JwtService) {{}}

  /**
   * Tạo access token.
   */
  createAccessToken(payload: TokenPayload): string {{
    return this.jwtService.sign(payload);
  }}

  /**
   * Tạo refresh token.
   */
  createRefreshToken(userId: string): string {{
    return this.jwtService.sign(
      {{ sub: userId, type: "refresh" }},
      {{ expiresIn: process.env.REFRESH_TOKEN_EXPIRE || "7d" }},
    );
  }}

  /**
   * Verify và decode token.
   */
  verifyToken(token: string): TokenPayload {{
    try {{
      return this.jwtService.verify(token);
    }} catch {{
      throw new Error("Token không hợp lệ");
    }}
  }}

  /**
   * Tạo cả access và refresh token.
   */
  createTokenPair(payload: TokenPayload): TokenResponse {{
    return {{
      access_token: this.createAccessToken(payload),
      refresh_token: this.createRefreshToken(payload.sub),
    }};
  }}
}}
'''
        file_path = output_dir / "auth.service.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(path=file_path, content=content, template="auth/auth.service.ts.jinja2", capability="CP03")

    def _emit_permissions(self, auth_ir: AuthIR, output_dir: Path) -> GeneratedFile:
        """Emit permissions.decorator.ts."""
        content = '''import { SetMetadata, createParamDecorator } from "@nestjs/common";
import { Reflector } from "@nestjs/core";

/**
 * Permission Keys - CP03.
 */
export const PERMISSIONS_KEY = "permissions";

/**
 * Permissions Decorator.
 *
 * Usage:
 *   @Permissions("user:read")
 *   @Permissions("user:create", "user:update")
 */
export const Permissions = (...permissions: string[]) =>
  SetMetadata(PERMISSIONS_KEY, permissions);

/**
 * CurrentUser Decorator.
 *
 * Usage:
 *   getUser(@CurrentUser() user: any)
 */
export const CurrentUser = createParamDecorator(
  (data: unknown, ctx: any) => {{
    const request = ctx.switchToHttp().getRequest();
    return request.user;
  }},
);

/**
 * Permission matching utility.
 */
export function permissionMatches(has: string, need: string): boolean {{
  if (has === need) return true;
  if (has === "*") return true;
  if (has.endsWith(":*")) {{
    const prefix = has.slice(0, -1);
    return need.startsWith(prefix);
  }}
  return false;
}}

/**
 * Check if user has required permissions.
 */
export function hasPermission(
  userPermissions: string[],
  requiredPermission: string,
): boolean {{
  return userPermissions.some((p) => permissionMatches(p, requiredPermission));
}}
'''
        file_path = output_dir / "permissions.decorator.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(path=file_path, content=content, template="auth/permissions.decorator.ts.jinja2", capability="CP03")

    def _emit_index(self, output_dir: Path) -> GeneratedFile:
        """Emit index.ts."""
        content = '''/**
 * Auth Module Exports - CP03.
 */
export * from "./auth.module";
export * from "./auth.service";
export * from "./jwt-auth.guard";
export * from "./permissions.decorator";
'''
        file_path = output_dir / "index.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(path=file_path, content=content, template="auth/index.ts.jinja2", capability="CP03")


# ============================================================================
# Generated File Dataclass
# ============================================================================


@dataclass
class GeneratedFile:
    """
    Generated File - File đã generate từ emitter.

    Attributes:
        path: Đường dẫn file
        content: Nội dung file đã generate
        template: Tên template đã dùng
        capability: Core Capability code (CP03)
    """
    path: Path
    content: str
    template: str
    capability: str


def emit_nestjs_auth(
    auth_ir: AuthIR,
    stack_dir: Path,
    output_dir: Path,
) -> list[GeneratedFile]:
    """
    Emit NestJS auth code từ AuthIR.

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