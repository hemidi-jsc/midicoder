"""
React Frontend Auth Emitter (P2-002-C).

Module này cung cấp ReactAuthEmitter class để emit auth module
cho React frontend: AuthContext, AuthInterceptor, ProtectedRoute.

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


class ReactAuthEmitter:
    """
    Emitter cho React auth module.

    Generate code cho:
    - AuthContext: Context provider cho authentication/authorization
    - AuthInterceptor: RTK Query baseQuery với JWT token
    - ProtectedRoute: Route component bảo vệ routes

    Usage:
        emitter = ReactAuthEmitter()
        files = emitter.emit(auth_config, output_dir)
    """

    def emit(
        self,
        auth_config: dict[str, Any],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """
        Emit React auth module.

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

        # Emit AuthContext
        files.append(self._write_file(
            filename="AuthContext.tsx",
            content=self._generate_auth_context(auth_config),
            output_dir=auth_dir,
        ))

        # Emit AuthInterceptor
        files.append(self._write_file(
            filename="authInterceptor.ts",
            content=self._generate_auth_interceptor(),
            output_dir=auth_dir,
        ))

        # Emit ProtectedRoute
        files.append(self._write_file(
            filename="ProtectedRoute.tsx",
            content=self._generate_protected_route(),
            output_dir=auth_dir,
        ))

        return files

    def _generate_auth_context(self, auth_config: dict[str, Any]) -> str:
        """Generate AuthContext."""
        provider = auth_config.get("provider", "jwt")

        return (
            '/**\n'
            ' * Auth Context - Quản lý authentication và authorization.\n'
            ' *\n'
            f' * Provider: {provider}\n'
            ' * Features:\n'
            ' * - JWT token management\n'
            ' * - Login/Logout\n'
            ' * - Permission checking\n'
            ' */\n\n'
            "import React, { createContext, useContext, useState, ReactNode } from 'react';\n\n"
            'interface AuthUser {\n'
            '  id: string;\n'
            '  email: string;\n'
            '  roles: string[];\n'
            '  permissions: string[];\n'
            '}\n\n'
            'interface AuthContextType {\n'
            '  user: AuthUser | null;\n'
            '  token: string | null;\n'
            '  login: (token: string, user: AuthUser) => void;\n'
            '  logout: () => void;\n'
            '  hasPermission: (permission: string) => boolean;\n'
            '  hasRole: (role: string) => boolean;\n'
            '}\n\n'
            'const AuthContext = createContext<AuthContextType | null>(null);\n\n'
            'export function AuthProvider({ children }: { children: ReactNode }) {\n'
            '  const [user, setUser] = useState<AuthUser | null>(\n'
            '    () => {\n'
            '      const stored = localStorage.getItem(\'auth_user\');\n'
            '      return stored ? JSON.parse(stored) : null;\n'
            '    }\n'
            '  );\n'
            "  const [token, setToken] = useState<string | null>(() => localStorage.getItem('auth_token'));\n\n"
            '  const login = (newToken: string, newUser: AuthUser) => {\n'
            "    localStorage.setItem('auth_token', newToken);\n"
            "    localStorage.setItem('auth_user', JSON.stringify(newUser));\n"
            '    setToken(newToken);\n'
            '    setUser(newUser);\n'
            '  };\n\n'
            '  const logout = () => {\n'
            "    localStorage.removeItem('auth_token');\n"
            "    localStorage.removeItem('auth_user');\n"
            '    setToken(null);\n'
            '    setUser(null);\n'
            '  };\n\n'
            '  const hasPermission = (permission: string): boolean => {\n'
            '    return user?.permissions.includes(permission) ?? false;\n'
            '  };\n\n'
            '  const hasRole = (role: string): boolean => {\n'
            '    return user?.roles.includes(role) ?? false;\n'
            '  };\n\n'
            '  return (\n'
            '    <AuthContext.Provider value={{ user, token, login, logout, hasPermission, hasRole }}>\n'
            '      {children}\n'
            '    </AuthContext.Provider>\n'
            '  );\n'
            '}\n\n'
            'export function useAuth() {\n'
            '  const context = useContext(AuthContext);\n'
            '  if (!context) {\n'
            "    throw new Error('useAuth must be used within AuthProvider');\n"
            '  }\n'
            '  return context;\n'
            '}\n\n'
            'export default AuthContext;\n'
        )

    def _generate_auth_interceptor(self) -> str:
        """Generate AuthInterceptor."""
        return (
            '/**\n'
            ' * Auth Interceptor - Tự động attach JWT token vào HTTP requests.\n'
            ' *\n'
            ' * Sử dụng với RTK Query baseQuery.\n'
            ' * Mọi request sẽ được thêm Header Authorization: Bearer <token>.\n'
            ' */\n\n'
            "import { fetchBaseQuery } from '@reduxjs/toolkit/query/react';\n\n"
            'const baseQuery = fetchBaseQuery({\n'
            "  baseUrl: '/api',\n"
            '  prepareHeaders: (headers) => {\n'
            "    const token = localStorage.getItem('auth_token');\n"
            '    if (token) {\n'
            "      headers.set('Authorization', `Bearer ${token}`);\n"
            '    }\n'
            '    return headers;\n'
            '  },\n'
            '});\n\n'
            'export default baseQuery;\n'
        )

    def _generate_protected_route(self) -> str:
        """Generate ProtectedRoute."""
        return (
            '/**\n'
            ' * Protected Route - Route guard cho protected routes.\n'
            ' *\n'
            ' * Nếu user chưa đăng nhập, redirect về trang login.\n'
            ' */\n\n'
            "import { Navigate, useLocation } from 'react-router-dom';\n"
            "import { useAuth } from './AuthContext';\n\n"
            'export default function ProtectedRoute({ children }: { children: JSX.Element }) {\n'
            '  const { user } = useAuth();\n'
            '  const location = useLocation();\n\n'
            '  if (!user) {\n'
            "    return <Navigate to='/login' state={{ from: location }} replace />;\n"
            '  }\n\n'
            '  return children;\n'
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
            template=f"authnz/react/{filename}",
        )


__all__ = ["ReactAuthEmitter", "GeneratedFile"]