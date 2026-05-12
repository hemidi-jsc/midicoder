"""
CP03: React Authentication Emitter.

Module này cung cấp ReactEmitter để generate React auth code
từ AuthIR (CP03):
- AuthContext.tsx - React context cho authentication state
- useAuth.ts - Custom hook cho auth
- ProtectedRoute.tsx - Component bảo vệ routes
- api-client.ts - Axios client với JWT interceptor

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


# ============================================================================
# React Auth Emitter Class
# ============================================================================


class ReactEmitter:
    """
    Emitter cho React authentication code.

    Generate code từ AuthIR cho:
    - src/auth/AuthContext.tsx
    - src/auth/useAuth.ts
    - src/auth/ProtectedRoute.tsx
    - src/auth/api-client.ts
    - src/auth/auth.types.ts
    - src/auth/index.ts

    Attributes:
        stack_dir: Đường dẫn đến templates directory
        template_env: Jinja2 Environment
    """

    def __init__(self, stack_dir: Path) -> None:
        """
        Khởi tạo ReactEmitter.

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
        Emit React auth code từ AuthIR.

        Process:
        1. Emit auth.types.ts
        2. Emit AuthContext.tsx
        3. Emit useAuth.ts
        4. Emit ProtectedRoute.tsx
        5. Emit api-client.ts
        6. Emit index.ts

        Args:
            auth_ir: AuthIR instance
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []
        auth_dir = output_dir / "src" / "auth"
        auth_dir.mkdir(parents=True, exist_ok=True)

        files.append(self._emit_types(auth_dir))
        files.append(self._emit_auth_context(auth_ir, auth_dir))
        files.append(self._emit_use_auth(auth_dir))
        files.append(self._emit_protected_route(auth_dir))
        files.append(self._emit_api_client(auth_dir))
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

        Raises:
            MidicoderError: Nếu template render fail
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

    def _emit_types(self, output_dir: Path) -> GeneratedFile:
        """Emit auth.types.ts - TypeScript interfaces cho auth."""
        content = '''/**
 * Auth Types - CP03.
 *
 * TypeScript interfaces cho authentication.
 */

/** User interface - đại diện cho user đã đăng nhập */
export interface User {
  id: string;
  email: string;
  tenant_id?: string;
  roles?: string[];
  permissions?: string[];
  disabled?: boolean;
}

/** Response từ API login/refresh */
export interface AuthResponse {
  access_token: string;
  refresh_token?: string;
  user: User;
}

/** Context type cho AuthContext */
export interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isLoggedIn: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  getAccessToken: () => string | null;
}

/** Credentials cho login */
export interface LoginCredentials {
  email: string;
  password: string;
}
'''
        file_path = output_dir / "auth.types.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="auth/auth.types.ts.jinja2", capability="CP03",
        )

    def _emit_auth_context(self, auth_ir: AuthIR, output_dir: Path) -> GeneratedFile:
        """Emit AuthContext.tsx - React context cho auth state."""
        jwt_provider = auth_ir.get_jwt_provider()
        config = jwt_provider.config if jwt_provider else JWTAuthConfig()

        content = f'''import {{
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
}} from "react";
import {{ User, AuthContextType, AuthResponse }} from "./auth.types";
import api from "./api-client";

/**
 * Auth Context - CP03.
 *
 * Context này cung cấp authentication state và methods cho React app.
 *
 * Configuration:
 * - Token expire: {config.expire_minutes} minutes
 * - Algorithm: {config.algorithm}
 */

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export interface AuthProviderProps {{
  children: ReactNode;
}}

/** AuthProvider - wrap app để cung cấp auth context */
export function AuthProvider({{ children }}: AuthProviderProps) {{
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Kiểm tra token trong localStorage khi mount
  useEffect(() => {{
    const token = localStorage.getItem("access_token");
    const storedUser = localStorage.getItem("user");
    if (token && storedUser) {{
      setUser(JSON.parse(storedUser));
    }}
    setIsLoading(false);
  }}, []);

  /** Login user bằng email/password */
  const login = async (email: string, password: string): Promise<void> => {{
    const response = await api.post<AuthResponse>("/auth/login", {{ email, password }});
    localStorage.setItem("access_token", response.data.access_token);
    if (response.data.refresh_token) {{
      localStorage.setItem("refresh_token", response.data.refresh_token);
    }}
    localStorage.setItem("user", JSON.stringify(response.data.user));
    setUser(response.data.user);
  }};

  /** Logout user - xóa tokens và reset state */
  const logout = async (): Promise<void> => {{
    try {{
      await api.post("/auth/logout", {{}});
    }} finally {{
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user");
      setUser(null);
    }}
  }};

  /** Refresh access token bằng refresh token */
  const refreshToken = async (): Promise<void> => {{
    const refreshTok = localStorage.getItem("refresh_token");
    if (!refreshTok) throw new Error("No refresh token available");
    const response = await api.post<AuthResponse>("/auth/refresh", {{ refresh_token: refreshTok }});
    localStorage.setItem("access_token", response.data.access_token);
    if (response.data.refresh_token) {{
      localStorage.setItem("refresh_token", response.data.refresh_token);
    }}
    localStorage.setItem("user", JSON.stringify(response.data.user));
    setUser(response.data.user);
  }};

  /** Lấy access token từ localStorage */
  const getAccessToken = (): string | null => localStorage.getItem("access_token");

  const value: AuthContextType = {{
    user, isLoading, isLoggedIn: !!user,
    login, logout, refreshToken, getAccessToken,
  }};

  return <AuthContext.Provider value={{value}}>{{children}}</AuthContext.Provider>;
}}

/** Custom hook để sử dụng Auth Context */
export function useAuthContext(): AuthContextType {{
  const context = useContext(AuthContext);
  if (context === undefined)
    throw new Error("useAuthContext must be used within an AuthProvider");
  return context;
}}
'''
        file_path = output_dir / "AuthContext.tsx"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="auth/AuthContext.tsx.jinja2", capability="CP03",
        )

    def _emit_use_auth(self, output_dir: Path) -> GeneratedFile:
        """Emit useAuth.ts - Re-export hook."""
        content = '''/**
 * useAuth Hook - CP03.
 *
 * Re-export của useAuthContext cho convenience.
 */
export { useAuthContext as useAuth } from "./AuthContext";
'''
        file_path = output_dir / "useAuth.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="auth/useAuth.ts.jinja2", capability="CP03",
        )

    def _emit_protected_route(self, output_dir: Path) -> GeneratedFile:
        """Emit ProtectedRoute.tsx - Component bảo vệ routes yêu cầu auth."""
        content = '''import { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuthContext } from "./AuthContext";

/**
 * Protected Route Component - CP03.
 *
 * Component này bảo vệ route yêu cầu authentication.
 * Nếu user chưa login, redirect đến /login.
 *
 * Usage:
 *   <Route path="/dashboard" element={
 *     <ProtectedRoute><Dashboard /></ProtectedRoute>
 *   } />
 */
export interface ProtectedRouteProps {
  children: ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isLoggedIn, isLoading } = useAuthContext();
  const location = useLocation();

  if (isLoading) return <div>Loading...</div>;
  if (!isLoggedIn) return <Navigate to="/login" state={{ from: location }} replace />;
  return <>{children}</>;
}
'''
        file_path = output_dir / "ProtectedRoute.tsx"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="auth/ProtectedRoute.tsx.jinja2", capability="CP03",
        )

    def _emit_api_client(self, output_dir: Path) -> GeneratedFile:
        """Emit api-client.ts - Axios client với JWT interceptor."""
        content = '''import axios, { AxiosInstance } from "axios";

/**
 * API Client - CP03.
 *
 * Axios instance với JWT authentication interceptor.
 * Tự động attach token vào requests và retry khi 401.
 */
const api: AxiosInstance = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

// Request interceptor — attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor — handle 401 bằng cách refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshTok = localStorage.getItem("refresh_token");
        if (!refreshTok) throw new Error("No refresh token");
        const response = await axios.post("/api/auth/refresh", { refresh_token: refreshTok });
        localStorage.setItem("access_token", response.data.access_token);
        originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
        return api(originalRequest);
      } catch {
        localStorage.clear();
        window.location.href = "/login";
        return Promise.reject(error);
      }
    }
    return Promise.reject(error);
  },
);

export default api;
'''
        file_path = output_dir / "api-client.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="auth/api-client.ts.jinja2", capability="CP03",
        )

    def _emit_index(self, output_dir: Path) -> GeneratedFile:
        """Emit index.ts - barrel exports."""
        content = '''/**
 * Auth Module Exports - CP03.
 */
export * from "./AuthContext";
export * from "./useAuth";
export * from "./ProtectedRoute";
export * from "./auth.types";
export { default as api } from "./api-client";
'''
        file_path = output_dir / "index.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="auth/index.ts.jinja2", capability="CP03",
        )


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


def emit_react_auth(
    auth_ir: AuthIR,
    stack_dir: Path,
    output_dir: Path,
) -> list[GeneratedFile]:
    """
    Emit React auth code từ AuthIR.

    Args:
        auth_ir: AuthIR instance
        stack_dir: Templates directory
        output_dir: Output directory

    Returns:
        List of GeneratedFile instances
    """
    emitter = ReactEmitter(stack_dir)
    return emitter.emit(auth_ir, output_dir)


__all__ = ["ReactEmitter", "GeneratedFile", "emit_react_auth"]