"""
CP03: Authentication & Authorization Framework — Data Models.

Module này định nghĩa các data models cho Authentication & Authorization:
- AuthProviderType: Loại provider (JWT, OAuth2)
- JWTAuthConfig: Cấu hình JWT authentication
- OAuth2AuthConfig: Cấu hình OAuth2 authentication
- AuthProvider: Provider authentication
- SessionConfig: Cấu hình session management
- AuthIR: Complete authentication configuration

Chỉ chứa các models liên quan đến CP03 (authenticate_user, authorize_permission).
Không chứa tenant (CP02) hay RBAC/Policy (CP04).

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ============================================================================
# Auth Provider Type Enum
# ============================================================================


class AuthProviderType(str, Enum):
    """
    Loại authentication provider.

    jwt: JWT-based authentication (stateless token)
    oauth2: OAuth2 flow authentication (authorization code, client credentials)
    saml: SAML 2.0 authentication (enterprise SSO)
    ldap: LDAP/Active Directory authentication
    mtls: Mutual TLS authentication (mTLS, machine-to-machine)
    session: Stateful session-based authentication (server-side sessions)
    """
    JWT = "jwt"
    OAUTH2 = "oauth2"
    SAML = "saml"
    LDAP = "ldap"
    MTLS = "mtls"
    SESSION = "session"


# ============================================================================
# JWT Auth Config
# ============================================================================


@dataclass
class JWTAuthConfig:
    """
    Cấu hình JWT Authentication.

    Attributes:
        expire_minutes: Thời gian hết hạn access token (phút), mặc định 30
        refresh_expire_days: Thời gian hết hạn refresh token (ngày), mặc định 7
        algorithm: JWT signing algorithm (HS256, RS256, ES256), mặc định HS256
        tenant_scoped: Có embed tenant_id vào token không, mặc định True
    """
    expire_minutes: int = 30
    refresh_expire_days: int = 7
    algorithm: str = "HS256"
    tenant_scoped: bool = True

    def __post_init__(self) -> None:
        """Validate cấu hình JWT sau khi khởi tạo."""
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        if self.expire_minutes <= 0:
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                reason="expire_minutes phải lớn hơn 0",
                value=self.expire_minutes,
            )
        if self.refresh_expire_days <= 0:
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                reason="refresh_expire_days phải lớn hơn 0",
                value=self.refresh_expire_days,
            )
        if self.algorithm not in ("HS256", "RS256", "ES256", "HS384", "HS512"):
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                reason=f"algorithm '{self.algorithm}' không được hỗ trợ",
                valid_algorithms="HS256, RS256, ES256, HS384, HS512",
            )


# ============================================================================
# OAuth2 Auth Config
# ============================================================================


@dataclass
class OAuth2AuthConfig:
    """
    Cấu hình OAuth2 Authentication.

    Attributes:
        authorization_url: URL cho authorization endpoint (bắt buộc)
        token_url: URL cho token endpoint (bắt buộc)
        scopes: List OAuth2 scopes mặc định
        client_id: OAuth2 client ID (optional, set ở runtime)
    """
    authorization_url: str
    token_url: str
    scopes: list[str] = field(default_factory=list)
    client_id: str = ""

    def __post_init__(self) -> None:
        """Validate cấu hình OAuth2 sau khi khởi tạo."""
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        if not self.authorization_url:
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                reason="authorization_url bắt buộc cho OAuth2 provider",
            )
        if not self.token_url:
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                reason="token_url bắt buộc cho OAuth2 provider",
            )


# ============================================================================
# Auth Provider
# ============================================================================


@dataclass
class AuthProvider:
    """
    Authentication Provider.

    Attributes:
        id: Provider identifier (ví dụ: jwt_auth, google_oauth2)
        provider_type: Loại provider (jwt, oauth2)
        config: Configuration cho provider (JWTAuthConfig hoặc OAuth2AuthConfig)
    """
    id: str
    provider_type: AuthProviderType
    config: JWTAuthConfig | OAuth2AuthConfig

    def __post_init__(self) -> None:
        """Validate auth provider sau khi khởi tạo."""
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        if not self.id:
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                reason="Auth provider id không được để trống",
            )

        # Validate config type matches provider type
        if self.provider_type == AuthProviderType.JWT:
            if not isinstance(self.config, JWTAuthConfig):
                EM.raise_error(
                    ErrorCode.CP03_AUTH_CONFIG_INVALID,
                    provider_id=self.id,
                    reason="JWT provider cần JWTAuthConfig",
                )
        elif self.provider_type == AuthProviderType.OAUTH2:
            if not isinstance(self.config, OAuth2AuthConfig):
                EM.raise_error(
                    ErrorCode.CP03_AUTH_CONFIG_INVALID,
                    provider_id=self.id,
                    reason="OAuth2 provider cần OAuth2AuthConfig",
                )


# ============================================================================
# Session Config
# ============================================================================


@dataclass
class SessionConfig:
    """
    Cấu hình Session Management.

    Attributes:
        cookie_name: Tên cookie session, mặc định "session_id"
        max_age_minutes: Thời gian sống tối đa của session (phút), mặc định 480 (8 giờ)
        secure: Chỉ gửi cookie qua HTTPS, mặc định True
        http_only: Không cho JavaScript truy cập cookie, mặc định True
        same_site: SameSite cookie attribute (lax, strict, none), mặc định "lax"
        path: Cookie path, mặc định "/"
    """
    cookie_name: str = "session_id"
    max_age_minutes: int = 480
    secure: bool = True
    http_only: bool = True
    same_site: str = "lax"
    path: str = "/"

    def __post_init__(self) -> None:
        """Validate session config sau khi khởi tạo."""
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        if self.max_age_minutes <= 0:
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                reason="max_age_minutes phải lớn hơn 0",
                value=self.max_age_minutes,
            )
        if self.same_site not in ("lax", "strict", "none"):
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                reason=f"same_site '{self.same_site}' không hợp lệ",
                valid_values="lax, strict, none",
            )


# ============================================================================
# Permission
# ============================================================================


@dataclass
class Permission:
    """
    Permission definition.

    Attributes:
        id: Permission identifier (ví dụ: "user:create", "order:*")
        description: Mô tả permission (optional)
        resource: Resource mà permission apply lên (ví dụ: "user", "order")
        action: Action được phép (ví dụ: "create", "read", "update", "delete", "*")
    """
    id: str
    description: str = ""
    resource: str = ""
    action: str = ""

    def __post_init__(self) -> None:
        """Validate permission sau khi khởi tạo."""
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        if not self.id:
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                reason="Permission id không được để trống",
            )

        # Tự động parse resource:action từ id nếu chưa set
        if not self.resource or not self.action:
            parts = self.id.split(":")
            if len(parts) == 2:
                self.resource = parts[0]
                self.action = parts[1]
            else:
                EM.raise_error(
                    ErrorCode.CP03_AUTH_CONFIG_INVALID,
                    permission_id=self.id,
                    reason="Permission id phải có format 'resource:action'",
                )


# ============================================================================
# AuthIR (Main Dataclass cho CP03)
# ============================================================================


@dataclass
class AuthIR:
    """
    Authentication & Authorization Intermediate Representation.

    Intermediate representation cho CP03:
    - Authentication providers (JWT, OAuth2)
    - Session management configuration
    - Permissions list

    Attributes:
        providers: List authentication providers
        session: Session configuration
        permissions: List permission definitions
    """
    providers: list[AuthProvider] = field(default_factory=list)
    session: SessionConfig = field(default_factory=SessionConfig)
    permissions: list[Permission] = field(default_factory=list)

    def validate(self) -> None:
        """
        Validate AuthIR.

        Validate:
        - Ít nhất một auth provider
        - Mỗi provider config hợp lệ

        Raises:
            MidicoderError: Nếu validation fail
        """
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        # Kiểm tra ít nhất một auth provider
        if not self.providers:
            EM.raise_error(
                ErrorCode.CP03_AUTH_PROVIDER_NOT_FOUND,
                reason="Ít nhất một authentication provider là bắt buộc",
            )

        # Validate mỗi provider
        for provider in self.providers:
            if not provider.id:
                EM.raise_error(
                    ErrorCode.CP03_AUTH_CONFIG_INVALID,
                    reason="Auth provider id không được để trống",
                )

    def get_jwt_provider(self) -> AuthProvider | None:
        """
        Lấy JWT provider từ danh sách providers.

        Returns:
            AuthProvider nếu có JWT provider, None nếu không có
        """
        for provider in self.providers:
            if provider.provider_type == AuthProviderType.JWT:
                return provider
        return None

    def get_oauth2_providers(self) -> list[AuthProvider]:
        """
        Lấy tất cả OAuth2 providers.

        Returns:
            List của OAuth2 AuthProvider
        """
        return [
            p for p in self.providers
            if p.provider_type == AuthProviderType.OAUTH2
        ]

    def get_all_permission_ids(self) -> set[str]:
        """
        Lấy tất cả permission IDs.

        Returns:
            Set của tất cả permission id strings
        """
        return {p.id for p in self.permissions}


# ============================================================================
# AuthValidationResult
# ============================================================================


@dataclass
class AuthValidationResult:
    """
    Validation result cho Auth DSL.

    Attributes:
        valid: Có valid không
        errors: List error messages
        warnings: List warning messages
    """
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


__all__ = [
    # Enums
    "AuthProviderType",
    # Config classes
    "JWTAuthConfig",
    "OAuth2AuthConfig",
    "SessionConfig",
    # Main models
    "AuthProvider",
    "Permission",
    "AuthIR",
    # Validation
    "AuthValidationResult",
]