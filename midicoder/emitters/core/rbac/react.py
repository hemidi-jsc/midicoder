"""
CP04: React RBAC Emitter.

Module này cung cấp ReactRBACEmitter để generate React RBAC code:
- useAuth(): Custom hook cho role/permission checks
- ProtectedRoute: Component bảo vệ route theo role
- WithPermission: HOC (Higher-Order Component) cho permission check

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


class ReactRBACEmitter:
    """
    Emitter cho React RBAC code.

    Generate code tu RBACConfig cho:
    - rbac/useAuth.ts (custom hook)
    - rbac/ProtectedRoute.tsx (route component)
    - rbac/WithPermission.tsx (HOC)
    """

    def __init__(self, config: Any) -> None:
        self._config = config

    def generate(self) -> dict[str, str]:
        """Generate toan bo React RBAC code."""
        result: dict[str, str] = {}
        result["src/core/rbac/useAuth.ts"] = self._generate_hook()
        result["src/core/rbac/ProtectedRoute.tsx"] = self._generate_protected_route()
        result["src/core/rbac/WithPermission.tsx"] = self._generate_with_permission()
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

    def _generate_hook(self) -> str:
        return '''import { createContext, useContext, useState, useEffect, ReactNode } from "react";

/**
 * RBAC Context & Hook - CP04.
 *
 * Cung cap useAuth() hook de kiem tra role va permission trong React.
 *
 * Su dung:
 * ```tsx
 * const { roles, permissions, hasRole, hasPermission } = useAuth();
 *
 * if (hasRole("admin")) {
 *   return <AdminPanel />;
 * }
 * ```
 */

interface AuthContextType {
  roles: string[];
  permissions: string[];
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  hasAllRoles: (roles: string[]) => boolean;
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType>({
  roles: [],
  permissions: [],
  hasRole: () => false,
  hasAnyRole: () => false,
  hasAllRoles: () => false,
  hasPermission: () => false,
  hasAnyPermission: () => false,
  isLoading: true,
});

/**
 * AuthProvider - Bao quanh app de cung cap RBAC context.
 *
 * Su dung:
 * ```tsx
 * <AuthProvider>
 *   <App />
 * </AuthProvider>
 * ```
 */
interface AuthProviderProps {
  children: ReactNode;
  initialRoles?: string[];
  initialPermissions?: string[];
}

export function AuthProvider({
  children,
  initialRoles = [],
  initialPermissions = [],
}: AuthProviderProps) {
  const [roles, setRoles] = useState<string[]>(initialRoles);
  const [permissions, setPermissions] = useState<string[]>(initialPermissions);
  const [isLoading, setIsLoading] = useState(false);

  /** Kiem tra user co role khong */
  const hasRole = (role: string): boolean => roles.includes(role);

  /** Kiem tra user co bat ky role nao khong (OR logic) */
  const hasAnyRole = (requiredRoles: string[]): boolean =>
    requiredRoles.some((role) => roles.includes(role));

  /** Kiem tra user co tat ca roles khong (AND logic) */
  const hasAllRoles = (requiredRoles: string[]): boolean =>
    requiredRoles.every((role) => roles.includes(role));

  /** Kiem tra user co permission khong */
  const hasPermission = (permission: string): boolean =>
    permissions.includes(permission);

  /** Kiem tra user co bat ky permission nao khong (OR logic) */
  const hasAnyPermission = (requiredPermissions: string[]): boolean =>
    requiredPermissions.some((perm) => permissions.includes(perm));

  return (
    <AuthContext.Provider
      value={{
        roles,
        permissions,
        hasRole,
        hasAnyRole,
        hasAllRoles,
        hasPermission,
        hasAnyPermission,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

/**
 * useAuth - Custom hook cho RBAC.
 *
 * Su dung:
 * ```tsx
 * function MyComponent() {
 *   const { hasRole, hasPermission } = useAuth();
 *
 *   if (hasRole("admin")) {
 *     return <AdminPanel />;
 *   }
 *   return <UserPanel />;
 * }
 * ```
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  return context;
}
'''

    def _generate_protected_route(self) -> str:
        return '''import { ReactNode, Navigate } from "react-router-dom";
import { useAuth } from "./useAuth";

/**
 * ProtectedRoute - Component bao ve route theo role.
 *
 * Su dung:
 * ```tsx
 * <Route
 *   path="/admin"
 *   element={
 *     <ProtectedRoute requiredRoles={["admin"]}>
 *       <AdminPage />
 *     </ProtectedRoute>
 *   }
 * />
 * ```
 */

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRoles?: string[];
  requiredPermissions?: string[];
  fallbackPath?: string;
}

export function ProtectedRoute({
  children,
  requiredRoles,
  requiredPermissions,
  fallbackPath = "/forbidden",
}: ProtectedRouteProps) {
  const { hasAnyRole, hasAnyPermission, isLoading } = useAuth();

  // Dang loading -> cho doi
  if (isLoading) {
    return <div>Loading...</div>;
  }

  // Khong co yeu cau -> cho phep
  if (!requiredRoles && !requiredPermissions) {
    return <>{children}</>;
  }

  // Kiem tra roles (OR logic)
  if (requiredRoles && hasAnyRole(requiredRoles)) {
    return <>{children}</>;
  }

  // Kiem tra permissions (OR logic)
  if (requiredPermissions && hasAnyPermission(requiredPermissions)) {
    return <>{children}</>;
  }

  // Khong du quyen -> chuyen huong
  return <Navigate to={fallbackPath} replace />;
}
'''

    def _generate_with_permission(self) -> str:
        return '''import { ComponentType, FC } from "react";
import { useAuth } from "./useAuth";

/**
 * WithPermission - Higher-Order Component cho permission check.
 *
 * Su dung:
 * ```tsx
 * const AdminOnlyComponent = WithPermission({
 *   requiredRoles: ["admin"],
 *   forbiddenComponent: <ForbiddenPage />,
 * })(AdminPanel);
 * ```
 */

interface WithPermissionOptions {
  requiredRoles?: string[];
  requiredPermissions?: string[];
  forbiddenComponent?: FC;
}

/**
 * WithPermission HOC.
 *
 * @param options - Options cho permission check
 * @returns HOC function
 */
export function WithPermission(options: WithPermissionOptions) {
  return <T extends Record<string, unknown>>(
    WrappedComponent: ComponentType<T>,
  ): FC<T> => {
    const WithPermissionComponent = (props: T) => {
      const { hasAnyRole, hasAnyPermission } = useAuth();

      // Khong co yeu cau -> render component
      if (!options.requiredRoles && !options.requiredPermissions) {
        return <WrappedComponent {...props} />;
      }

      // Kiem tra roles
      if (options.requiredRoles && hasAnyRole(options.requiredRoles)) {
        return <WrappedComponent {...props} />;
      }

      // Kiem tra permissions
      if (
        options.requiredPermissions &&
        hasAnyPermission(options.requiredPermissions)
      ) {
        return <WrappedComponent {...props} />;
      }

      // Khong du quyen
      if (options.forbiddenComponent) {
        return options.forbiddenComponent();
      }

      // Mac dinh: khong render gi ca
      return null;
    };

    WithPermissionComponent.displayName = `WithPermission(${WrappedComponent.displayName || WrappedComponent.name || "Component"})`;

    return WithPermissionComponent;
  };
}
'''