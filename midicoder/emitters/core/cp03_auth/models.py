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
# SAML 2.0 Auth Config
# ============================================================================


class NameIDFormat(str, Enum):
    """
    Định dạng NameID trong SAML assertion.

    - email: Email address (vd: user@example.com)
    - persistent: Persistent identifier (stable, unlinkable across IdPs)
    - transient: Transient identifier (changes per SP)
    - windows: Windows UUID
    - unspecified: Không xác định
    """
    EMAIL = "email"
    PERSISTENT = "persistent"
    TRANSIENT = "transient"
    WINDOWS = "windows"
    UNSPECIFIED = "unspecified"


@dataclass
class SAMLAuthConfig:
    """
    Cấu hình SAML 2.0 Authentication (enterprise SSO).

    SAML 2.0 cho phép user authenticate qua IdP (Identity Provider) enterprise
    như ADFS, Okta, OneLogin, PingIdentity.

    Attributes:
        idp_metadata_url: URL đến SAML metadata XML của IdP (bắt buộc)
        idp_metadata_xml: Nội dung metadata XML trực tiếp (alternative cho URL)
        sp_entity_id: Entity ID của Service Provider (vd: https://app.example.com/saml)
        sp_assertion_consumer_url: URL ACS endpoint nhận SAML response
        name_id_format: Định dạng NameID (persistent, email, transient, ...)
        want_authn_requests_signed: Có ký AuthnRequest không
        want_response_signed: Có yêu cầu response được ký không
        want_assertion_signed: Có yêu cầu assertion được ký không
        cert: SP certificate string (PEM) cho signing
        key: SP private key string (PEM) cho signing
    """
    idp_metadata_url: str = ""
    idp_metadata_xml: str = ""
    sp_entity_id: str = ""
    sp_assertion_consumer_url: str = ""
    name_id_format: NameIDFormat = NameIDFormat.PERSISTENT
    want_authn_requests_signed: bool = False
    want_response_signed: bool = True
    want_assertion_signed: bool = True
    cert: str = ""
    key: str = ""

    def __post_init__(self) -> None:
        """Validate cấu hình SAML 2.0 sau khi khởi tạo."""
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        if not self.idp_metadata_url and not self.idp_metadata_xml:
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                reason="Phải cung cấp idp_metadata_url HOẶC idp_metadata_xml cho SAML provider",
            )
        if not self.sp_entity_id:
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                reason="sp_entity_id bắt buộc cho SAML provider",
            )


# ============================================================================
# LDAP Auth Config
# ============================================================================


class LDAPReferralMode(str, Enum):
    """
    Chế độ xử lý LDAP referrals.

    - follow: Tự động follow referrals
    - ignore: Bỏ qua referrals
    - throw: Throw exception khi gặp referral
    """
    FOLLOW = "follow"
    IGNORE = "ignore"
    THROW = "throw"


@dataclass
class LDAPOAuthConfig:
    """
    Cấu hình LDAP Authentication (Active Directory / OpenLDAP).

    Connect đến LDAP directory để authenticate user enterprise.

    Attributes:
        server: Server URL (vd: ldap://dc01.example.com:389 hoặc ldaps://...:636)
        use_ssl: Kết nối qua SSL/TLS
        base_dn: Base DN cho search (vd: dc=example,dc=com)
        user_search_base: DN để search users (vd: ou=users,dc=example,dc=com)
        group_search_base: DN để search groups (vd: ou=groups,dc=example,dc=com)
        user_search_filter: LDAP filter tìm user (vd: (sAMAccountName={login}))
        group_search_filter: LDAP filter tìm group (vd: (member={dn}))
        bind_dn: DN dùng để bind & search (service account)
        bind_password: Password của bind_dn (set ở runtime)
        referral_mode: Chế độ xử lý referrals
        attributes: Attributes cần fetch (vd: [cn, mail, memberOf])
    """
    server: str
    use_ssl: bool = False
    base_dn: str = ""
    user_search_base: str = ""
    group_search_base: str = ""
    user_search_filter: str = "(sAMAccountName={login})"
    group_search_filter: str = "(member={dn})"
    bind_dn: str = ""
    bind_password: str = ""
    referral_mode: LDAPReferralMode = LDAPReferralMode.IGNORE
    attributes: list[str] = field(default_factory=lambda: ["cn", "mail", "memberOf"])

    def __post_init__(self) -> None:
        """Validate cấu hình LDAP sau khi khởi tạo."""
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        if not self.server:
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                reason="server URL bắt buộc cho LDAP provider",
            )
        if not self.base_dn:
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                reason="base_dn bắt buộc cho LDAP provider",
            )


# ============================================================================
# mTLS Auth Config
# ============================================================================


class MTLSVerificationMode(str, Enum):
    """
    Chế độ verification cho mTLS.

    - required: Bắt buộc client certificate (deny nếu không có)
    - optional: Chấp nhận với hoặc không có client certificate
    - request: Yêu cầu nhưng không enforce (kiểm tra ở application layer)
    """
    REQUIRED = "required"
    OPTIONAL = "optional"
    REQUEST = "request"


@dataclass
class MTLSAuthConfig:
    """
    Cấu hình Mutual TLS Authentication (mTLS).

    mTLS dùng cho machine-to-machine authentication — cả server và client
    đều phải verify lẫn nhau qua X.509 certificates.

    Attributes:
        ca_cert_path: Path đến CA certificate dùng để verify client certs
        server_cert_path: Path đến server certificate
        server_key_path: Path đến server private key
        verification_mode: Chế độ verification (required, optional, request)
        allowed_cn_patterns: Allowed Common Name patterns cho client certs
        allowed_ou_patterns: Allowed Organizational Unit patterns
        allowed_o_patterns: Allowed Organization patterns
    """
    ca_cert_path: str
    server_cert_path: str = ""
    server_key_path: str = ""
    verification_mode: MTLSVerificationMode = MTLSVerificationMode.REQUIRED
    allowed_cn_patterns: list[str] = field(default_factory=list)
    allowed_ou_patterns: list[str] = field(default_factory=list)
    allowed_o_patterns: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate cấu hình mTLS sau khi khởi tạo."""
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        if not self.ca_cert_path:
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                reason="ca_cert_path bắt buộc cho mTLS provider",
            )


# ============================================================================
# Stateful Session Config (extended)
# ============================================================================


class SessionStoreType(str, Enum):
    """
    Loại session store cho stateful session.

    - database: Lưu sessions vào database (durable, cross-process)
    - redis: Lưu sessions vào Redis (fast, distributed)
    - memcached: Lưu sessions vào Memcached (fast, in-memory)
    - file: Lưu sessions vào file system (single-process)
    """
    DATABASE = "database"
    REDIS = "redis"
    MEMCACHED = "memcached"
    FILE = "file"


@dataclass
class StatefulSessionConfig:
    """
    Cấu hình stateful session authentication.

    Sessions được lưu server-side — cookie chỉ chứa session ID.

    Attributes:
        store_type: Loại session store (database, redis, memcached, file)
        store_connection_string: Connection string cho store (Redis URL, DB URL, ...)
        cookie_name: Tên session cookie
        cookie_secure: Chỉ set cookie trên HTTPS
        cookie_http_only: Không access cookie từ JavaScript
        cookie_samesite: SameSite attribute (strict, lax, none)
        ttl_seconds: TTL của session (seconds)
        idle_timeout_seconds: Idle timeout (session invalidate sau bao lâu không hoạt động)
    """
    store_type: SessionStoreType = SessionStoreType.DATABASE
    store_connection_string: str = ""
    cookie_name: str = "session_id"
    cookie_secure: bool = True
    cookie_http_only: bool = True
    cookie_samesite: str = "lax"
    ttl_seconds: int = 86400
    idle_timeout_seconds: int = 3600

    def __post_init__(self) -> None:
        """Validate cấu hình stateful session sau khi khởi tạo."""
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        if self.ttl_seconds <= 0:
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                reason="ttl_seconds phải lớn hơn 0 cho stateful session",
            )
        if self.cookie_samesite not in ("strict", "lax", "none"):
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                reason="cookie_samesite phải là strict, lax, hoặc none",
            )


# ============================================================================
# Auth Provider
# ============================================================================


@dataclass
class AuthProvider:
    """
    Authentication Provider.

    Attributes:
        id: Provider identifier (ví dụ: jwt_auth, okta_saml, ad_ldap, service_mtls)
        provider_type: Loại provider (jwt, oauth2, saml, ldap, mtls, session)
        config: Configuration cho provider (union của các config types)
    """
    id: str
    provider_type: AuthProviderType
    config: JWTAuthConfig | OAuth2AuthConfig | SAMLAuthConfig | LDAPOAuthConfig | MTLSAuthConfig | StatefulSessionConfig

    def __post_init__(self) -> None:
        """Validate auth provider sau khi khởi tạo."""
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        if not self.id:
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                reason="Auth provider id không được để trống",
            )

        # Validate config type matches provider type
        expected = {
            AuthProviderType.JWT: JWTAuthConfig,
            AuthProviderType.OAUTH2: OAuth2AuthConfig,
            AuthProviderType.SAML: SAMLAuthConfig,
            AuthProviderType.LDAP: LDAPOAuthConfig,
            AuthProviderType.MTLS: MTLSAuthConfig,
            AuthProviderType.SESSION: StatefulSessionConfig,
        }
        exp_cls = expected.get(self.provider_type)
        if exp_cls and not isinstance(self.config, exp_cls):
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                provider_id=self.id,
                reason=f"{self.provider_type.value} provider cần {exp_cls.__name__}",
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
    "NameIDFormat",
    "LDAPReferralMode",
    "MTLSVerificationMode",
    "SessionStoreType",
    # Config classes
    "JWTAuthConfig",
    "OAuth2AuthConfig",
    "SAMLAuthConfig",
    "LDAPOAuthConfig",
    "MTLSAuthConfig",
    "StatefulSessionConfig",
    "SessionConfig",
    # Main models
    "AuthProvider",
    "Permission",
    "AuthIR",
    # Validation
    "AuthValidationResult",
]