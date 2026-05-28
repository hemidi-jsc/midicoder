"""
CP03: FastAPI Authentication Emitter.

Module này cung cấp FastAPIAuthEmitter để generate FastAPI auth code
từ AuthIR (CP03):
- JWT authentication (tenant-scoped)
- Session management
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
from midicoder.errors import ErrorCode, MidicoderError, MidicoderErrorManager as EM


# ============================================================================
# FastAPI Auth Emitter Class
# ============================================================================


class FastAPIAuthEmitter:
    """
    Emitter cho FastAPI authentication code.

    Generate code từ AuthIR cho:
    - app/core/security/jwt_auth.py (CP03)
    - app/core/security/session.py (CP03)
    - app/core/security/permissions.py (CP03)

    Attributes:
        stack_dir: Đường dẫn đến templates directory
        template_env: Jinja2 Environment
    """

    def __init__(self, stack_dir: Path) -> None:
        """
        Khởi tạo FastAPIAuthEmitter.

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
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def emit(self, auth_ir: AuthIR, output_dir: Path) -> list[GeneratedFile]:
        """
        Emit FastAPI auth code từ AuthIR.

        Process:
        1. Emit jwt_auth.py
        2. Emit session.py
        3. Emit permissions.py
        4. Emit __init__.py

        Args:
            auth_ir: AuthIR instance
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []

        # Tạo output directory
        security_dir = output_dir / "core" / "security"
        security_dir.mkdir(parents=True, exist_ok=True)

        # Emit __init__.py
        files.append(self._emit_init(security_dir))

        # Emit jwt_auth.py nếu có JWT provider
        jwt_provider = auth_ir.get_jwt_provider()
        if jwt_provider:
            files.append(self._emit_jwt_auth(auth_ir, security_dir))

        # Emit session.py
        files.append(self._emit_session(auth_ir, security_dir))

        # Emit permissions.py
        files.append(self._emit_permissions(auth_ir, security_dir))

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

    def _emit_init(self, output_dir: Path) -> GeneratedFile:
        """
        Emit __init__.py cho security module.

        Args:
            output_dir: Output directory

        Returns:
            GeneratedFile instance
        """
        content = '''"""
Security Module - Authentication & Authorization cho FastAPI.

Module này cung cấp:
- JWT authentication (tenant-scoped)
- Session management
- Permission decorators

CP03: Authentication & Authorization Framework
"""

from .jwt_auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    get_current_active_user,
)
from .session import SessionManager, get_session_manager
from .permissions import require_permission, check_permission

__all__ = [
    # JWT Auth
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "get_current_user",
    "get_current_active_user",
    # Session
    "SessionManager",
    "get_session_manager",
    # Permissions
    "require_permission",
    "check_permission",
]
'''
        file_path = output_dir / "__init__.py"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path,
            content=content,
            template="auth/__init__.py",
            capability="CP03",
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
        jwt_provider = auth_ir.get_jwt_provider()
        config = jwt_provider.config if jwt_provider else JWTAuthConfig()

        # Try template first, fallback to inline
        try:
            content = self._render_template("auth/jwt_auth.py.jinja2", {
                "expire_minutes": config.expire_minutes,
                "refresh_expire_days": config.refresh_expire_days,
                "algorithm": config.algorithm,
                "tenant_scoped": config.tenant_scoped,
            })
        except MidicoderError:
            # Fallback: generate inline
            content = self._generate_jwt_auth_inline(config)

        file_path = output_dir / "jwt_auth.py"
        file_path.write_text(content, encoding="utf-8")

        return GeneratedFile(
            path=file_path,
            content=content,
            template="auth/jwt_auth.py.jinja2",
            capability="CP03",
        )

    def _generate_jwt_auth_inline(self, config: JWTAuthConfig) -> str:
        """
        Generate jwt_auth.py inline (khi không có template).

        Args:
            config: JWTAuthConfig instance

        Returns:
            Generated Python source code
        """
        return (
            '"""\n'
            "JWT Authentication Module - CP03.\n"
            "\n"
            "Module này cung cấp JWT authentication với tenant-scoped tokens.\n"
            "\n"
            f"Configuration:\n"
            f"- Access token expire: {config.expire_minutes} minutes\n"
            f"- Refresh token expire: {config.refresh_expire_days} days\n"
            f"- Algorithm: {config.algorithm}\n"
            f"- Tenant scoped: {config.tenant_scoped}\n"
            '"""\n'
            "\n"
            "from datetime import datetime, timedelta, timezone\n"
            "from typing import Any, Optional\n"
            "\n"
            "import jwt\n"
            "from fastapi import Depends, HTTPException, status\n"
            "from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials\n"
            "\n"
            "ACCESS_TOKEN_EXPIRE_MINUTES = " + str(config.expire_minutes) + "\n"
            "REFRESH_TOKEN_EXPIRE_DAYS = " + str(config.refresh_expire_days) + "\n"
            'ALGORITHM = "' + config.algorithm + '"\n'
            "TENANT_SCOPED = " + str(config.tenant_scoped).lower() + "\n"
            "\n"
            "security = HTTPBearer()\n"
            "\n"
            "\n"
            "def _get_secret_key() -> str:\n"
            '    """Lấy secret key từ environment variable."""\n'
            "    import os\n"
            '    secret = os.getenv("JWT_SECRET")\n'
            "    if not secret:\n"
            '        raise ValueError("JWT_SECRET environment variable is required")\n'
            "    return secret\n"
            "\n"
            "\n"
            "def create_access_token(\n"
            "    user_id: str,\n"
            "    email: str,\n"
            "    tenant_id: Optional[str] = None,\n"
            "    roles: Optional[list[str]] = None,\n"
            ") -> str:\n"
            "    now = datetime.now(timezone.utc)\n"
            "    payload = {\n"
            '        "sub": user_id,\n'
            '        "email": email,\n'
            '        "iat": now,\n'
            '        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),\n'
            '        "type": "access",\n'
            "    }\n"
            "    if TENANT_SCOPED and tenant_id:\n"
            '        payload["tenant_id"] = tenant_id\n'
            "    if roles:\n"
            '        payload["roles"] = roles\n'
            "    return jwt.encode(payload, _get_secret_key(), algorithm=ALGORITHM)\n"
            "\n"
            "\n"
            "def create_refresh_token(user_id: str) -> str:\n"
            "    now = datetime.now(timezone.utc)\n"
            "    payload = {\n"
            '        "sub": user_id,\n'
            '        "iat": now,\n'
            '        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),\n'
            '        "type": "refresh",\n'
            "    }\n"
            "    return jwt.encode(payload, _get_secret_key(), algorithm=ALGORITHM)\n"
            "\n"
            "\n"
            "def verify_token(token: str, expected_type: str = \"access\") -> dict[str, Any]:\n"
            "    try:\n"
            "        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])\n"
            "    except jwt.ExpiredSignatureError:\n"
            "        raise HTTPException(\n"
            "            status_code=status.HTTP_401_UNAUTHORIZED,\n"
            '            detail="Token đã hết hạn",\n'
            "        )\n"
            "    except jwt.InvalidTokenError as e:\n"
            "        raise HTTPException(\n"
            "            status_code=status.HTTP_401_UNAUTHORIZED,\n"
            '            detail=f"Token không hợp lệ: {{str(e)}}",\n'
            "        )\n"
            '    if payload.get("type") != expected_type:\n'
            "        raise HTTPException(\n"
            "            status_code=status.HTTP_401_UNAUTHORIZED,\n"
            "            detail=f\"Token type phải là '{expected_type}'\",\n"
            "        )\n"
            "    return payload\n"
            "\n"
            "\n"
            "def get_current_user(\n"
            "    credentials: HTTPAuthorizationCredentials = Depends(security),\n"
            ") -> dict[str, Any]:\n"
            "    payload = verify_token(credentials.credentials, \"access\")\n"
            "    return payload\n"
            "\n"
            "\n"
            "def get_current_active_user(\n"
            "    user: dict[str, Any] = Depends(get_current_user),\n"
            ") -> dict[str, Any]:\n"
            '    if user.get("disabled", False):\n'
            "        raise HTTPException(\n"
            "            status_code=status.HTTP_400_BAD_REQUEST,\n"
            '            detail="User đã bị vô hiệu hóa",\n'
            "        )\n"
            "    return user\n"
        )

    def _emit_session(self, auth_ir: AuthIR, output_dir: Path) -> GeneratedFile:
        """
        Emit session.py.

        Args:
            auth_ir: AuthIR instance
            output_dir: Output directory

        Returns:
            GeneratedFile instance
        """
        session = auth_ir.session

        content = f'''"""
Session Management Module - CP03.

Module này cung cấp session management với cookie-based sessions.

Configuration:
- Cookie name: {session.cookie_name}
- Max age: {session.max_age_minutes} minutes
- Secure: {session.secure}
- HttpOnly: {session.http_only}
- SameSite: {session.same_site}
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from starlette.requests import Request
from starlette.responses import Response


# ============================================================================
# Session Data Model
# ============================================================================


@dataclass
class SessionData:
    """
    Session data model.

    Attributes:
        session_id: Session identifier duy nhất
        user_id: User identifier
        tenant_id: Tenant identifier (optional)
        created_at: Thời điểm tạo session
        expires_at: Thời điểm hết hạn session
        ip_address: IP address của client (optional)
        user_agent: User agent của client (optional)
    """
    session_id: str
    user_id: str
    tenant_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    def is_expired(self) -> bool:
        """Kiểm tra xem session có hết hạn không."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


# ============================================================================
# Session Manager
# ============================================================================


class SessionManager:
    """
    Quản lý sessions.

    In-memory session store. Trong production, dùng Redis hoặc database.

    Configuration:
        cookie_name: Tên cookie session
        max_age_minutes: Thời gian sống tối đa (phút)
        secure: Chỉ gửi qua HTTPS
        http_only: Không cho JavaScript truy cập
        same_site: SameSite attribute
    """

    def __init__(
        self,
        cookie_name: str = "{session.cookie_name}",
        max_age_minutes: int = {session.max_age_minutes},
        secure: bool = {session.secure},
        http_only: bool = {session.http_only},
        same_site: str = "{session.same_site}",
    ) -> None:
        """
        Khởi tạo SessionManager.

        Args:
            cookie_name: Tên cookie session
            max_age_minutes: Thời gian sống tối đa (phút)
            secure: Chỉ gửi qua HTTPS
            http_only: Không cho JavaScript truy cập
            same_site: SameSite attribute
        """
        self.cookie_name = cookie_name
        self.max_age_minutes = max_age_minutes
        self.secure = secure
        self.http_only = http_only
        self.same_site = same_site
        self._store: dict[str, SessionData] = {{}}

    def create_session(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> SessionData:
        """
        Tạo session mới cho user.

        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            ip_address: IP address của client
            user_agent: User agent của client

        Returns:
            SessionData object
        """
        session_id = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self.max_age_minutes)

        session = SessionData(
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            created_at=now,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self._store[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Lấy session theo session_id.

        Args:
            session_id: Session identifier

        Returns:
            SessionData nếu tồn tại và chưa hết hạn, None nếu không
        """
        session = self._store.get(session_id)
        if session is None:
            return None
        if session.is_expired():
            self.destroy_session(session_id)
            return None
        return session

    def destroy_session(self, session_id: str) -> None:
        """
        Xóa session.

        Args:
            session_id: Session identifier
        """
        self._store.pop(session_id, None)

    def set_cookie(self, response: Response, session_id: str) -> None:
        """
        Set session cookie trong response.

        Args:
            response: HTTP Response object
            session_id: Session identifier
        """
        max_age = self.max_age_minutes * 60
        response.set_cookie(
            key=self.cookie_name,
            value=session_id,
            max_age=max_age,
            secure=self.secure,
            httponly=self.http_only,
            samesite=self.same_site,
            path="/",
        )

    def clear_cookie(self, response: Response) -> None:
        """
        Xóa session cookie trong response.

        Args:
            response: HTTP Response object
        """
        response.delete_cookie(
            key=self.cookie_name,
            path="/",
        )

    def get_session_from_request(self, request: Request) -> Optional[SessionData]:
        """
        Lấy session từ request cookie.

        Args:
            request: HTTP Request object

        Returns:
            SessionData nếu tìm thấy, None nếu không
        """
        session_id = request.cookies.get(self.cookie_name)
        if not session_id:
            return None
        return self.get_session(session_id)


# ============================================================================
# Singleton Instance
# ============================================================================

_default_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    Lấy default SessionManager instance.

    Returns:
        SessionManager instance
    """
    global _default_session_manager
    if _default_session_manager is None:
        _default_session_manager = SessionManager()
    return _default_session_manager
'''

        file_path = output_dir / "session.py"
        file_path.write_text(content, encoding="utf-8")

        return GeneratedFile(
            path=file_path,
            content=content,
            template="auth/session.py.jinja2",
            capability="CP03",
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
        # Collect all unique permissions
        all_permissions = auth_ir.get_all_permission_ids()
        permissions_list = sorted(all_permissions) if all_permissions else [
            "user:create", "user:read", "user:update", "user:delete",
            "order:create", "order:read", "order:update", "order:delete",
        ]

        # Generate permission constants
        perm_constants = "\n".join(
            f'    "{perm}",' for perm in permissions_list
        )

        content = f'''"""
Permission Module - CP03.

Module này cung cấp permission decorators và utility functions.
"""

from functools import wraps
from typing import Optional

from fastapi import Depends, HTTPException, status


# ============================================================================
# Permission Constants
# ============================================================================

KNOWN_PERMISSIONS = [
{perm_constants}
]


# ============================================================================
# Permission Matching
# ============================================================================


def _permission_matches(has_perm: str, need_perm: str) -> bool:
    """
    Kiểm tra permission có match không (hỗ trợ wildcard).

    Args:
        has_perm: Permission mà user có
        need_perm: Permission cần thiết

    Returns:
        True nếu match
    """
    if has_perm == need_perm:
        return True

    # Wildcard matching (ví dụ: "user:*" match "user:create")
    if has_perm.endswith(":*"):
        prefix = has_perm[:-1]  # "user:"
        if need_perm.startswith(prefix):
            return True

    return False


def check_permission(
    user_permissions: list[str], required_permission: str
) -> bool:
    """
    Kiểm tra user có permission cần thiết.

    Args:
        user_permissions: List permissions của user
        required_permission: Permission cần thiết

    Returns:
        True nếu user có permission
    """
    for perm in user_permissions:
        if _permission_matches(perm, required_permission):
            return True
    return False


# ============================================================================
# Permission Decorator
# ============================================================================


def require_permission(permission: str):
    """
    Decorator để require permission cho endpoint.

    Usage:
        @app.get("/users")
        @require_permission("user:read")
        def list_users(current_user = Depends(get_current_user)):
            ...

    Args:
        permission: Permission required
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Lấy current user từ kwargs
            current_user = kwargs.get("current_user")
            if current_user is None:
                # Thử tìm trong args
                for arg in args:
                    if isinstance(arg, dict) and "sub" in arg:
                        current_user = arg
                        break

            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Không tìm thấy user",
                )

            user_roles = current_user.get("roles", [])
            user_perms = current_user.get("permissions", [])

            # Kết hợp roles và permissions
            all_perms = list(set(user_perms + user_roles))

            if not check_permission(all_perms, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Yêu cầu permission: {{permission}}",
                )

            return func(*args, **kwargs)
        return wrapper
    return decorator
'''

        file_path = output_dir / "permissions.py"
        file_path.write_text(content, encoding="utf-8")

        return GeneratedFile(
            path=file_path,
            content=content,
            template="auth/permissions.py.jinja2",
            capability="CP03",
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