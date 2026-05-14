"""
CP03: Authentication & Authorization Framework — Recipes.

Recipes là cách gán giá trị cụ thể vào pattern vocabulary — không phải domain
logic, không phải nested recipe. Mỗi recipe ship sẵn trong pack để user không
cần tự mix.

Usage:
    auth_ir = JWTRecipe()                    # default JWT auth
    auth_ir = OAuth2Recipe("google")          # Google OAuth2
    auth_ir = SAMLRecipe("okta", idp_url)     # Okta SAML SSO
    auth_ir = LDAPRecipe("ldaps://ad.example.com", base_dn)
    auth_ir = mTLSRecipe("/path/to/ca.pem")   # mTLS for B2B API
    auth_ir = StatefulSessionRecipe("redis")  # Redis-backed sessions
    auth_ir = MultiProviderRecipe([...])       # multiple providers

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from midicoder.emitters.core.cp03_auth.models import (
    AuthIR,
    AuthProvider,
    AuthProviderType,
    JWTAuthConfig,
    LDAPOAuthConfig,
    MFAPolicy,
    MFAProviderType,
    MTLSAuthConfig,
    MTLSVerificationMode,
    OAuth2AuthConfig,
    Permission,
    RateLimitConfig,
    RateLimitStrategyType,
    SAMLAuthConfig,
    SessionConfig,
    SessionStoreType,
    StatefulSessionConfig,
    TOTPAlgorithm,
    TOTPConfig,
    WebAuthnConfig,
)


# ============================================================================
# JWT Recipe — default JWT authentication
# ============================================================================


def jwt_recipe(
    expire_minutes: int = 30,
    refresh_expire_days: int = 7,
    algorithm: str = "HS256",
    tenant_scoped: bool = True,
    max_login_attempts: int = 10,
    rate_limit_window: int = 300,
    enable_mfa: bool = False,
) -> AuthIR:
    """
    JWT Authentication Recipe.

    Recipe này gán concrete values vào AuthProvider pattern cho JWT auth.
    Default phù hợp cho hầu hết B2C web/mobile app.

    Args:
        expire_minutes: Thời gian hết hạn access token (phút)
        refresh_expire_days: Thời gian hết hạn refresh token (ngày)
        algorithm: JWT signing algorithm
        tenant_scoped: Có embed tenant_id vào token không
        max_login_attempts: Số lần thử login tối đa trong rate limit window
        rate_limit_window: Rate limit window (giây)
        enable_mfa: Có bật MFA (TOTP) không

    Returns:
        AuthIR với JWT provider + rate limiting + optional MFA
    """
    mfa = None
    if enable_mfa:
        mfa = MFAPolicy(
            enabled=True,
            required=False,
            providers=[MFAProviderType.TOTP],
            totp_config=TOTPConfig(
                algorithm=TOTPAlgorithm.SHA256,
                digit_count=6,
                period=30,
            ),
        )

    return AuthIR(
        providers=[
            AuthProvider(
                id="jwt_auth",
                provider_type=AuthProviderType.JWT,
                config=JWTAuthConfig(
                    expire_minutes=expire_minutes,
                    refresh_expire_days=refresh_expire_days,
                    algorithm=algorithm,
                    tenant_scoped=tenant_scoped,
                ),
            )
        ],
        session=SessionConfig(),
        rate_limit=RateLimitConfig(
            strategy=RateLimitStrategyType.SLIDING_WINDOW,
            max_requests=max_login_attempts,
            window_seconds=rate_limit_window,
        ),
        mfa=mfa or MFAPolicy(),
    )


# ============================================================================
# OAuth2 Recipe — common OAuth2 providers
# ============================================================================


def oauth2_recipe(
    provider_name: str = "google",
    client_id: str = "",
    scopes: list[str] | None = None,
    enable_mfa: bool = False,
    authorization_url: str | None = None,
    token_url: str | None = None,
) -> AuthIR:
    """
    OAuth2 Authentication Recipe.

    Pre-configured cho common OAuth2 providers: Google, GitHub, GitHub Enterprise.

    Args:
        provider_name: Tên provider ("google", "github", "custom")
        client_id: OAuth2 client ID
        scopes: OAuth2 scopes (auto-filled cho google/github)
        enable_mfa: Có bật MFA không
        authorization_url: Override authorization URL (cho custom provider)
        token_url: Override token URL (cho custom provider)

    Returns:
        AuthIR với OAuth2 provider
    """
    # Provider-specific defaults
    provider_configs = {
        "google": {
            "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "default_scopes": ["openid", "email", "profile"],
        },
        "github": {
            "authorization_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "default_scopes": ["read:user", "user:email"],
        },
    }

    config = provider_configs.get(provider_name, {})
    auth_url = authorization_url or config.get("authorization_url", "")
    token_url = token_url or config.get("token_url", "")
    default_scopes = config.get("default_scopes", [])

    if scopes is None:
        scopes = default_scopes

    mfa = MFAPolicy(
        enabled=True,
        providers=[MFAProviderType.TOTP],
        totp_config=TOTPConfig(),
    ) if enable_mfa else MFAPolicy()

    return AuthIR(
        providers=[
            AuthProvider(
                id=f"{provider_name}_oauth2",
                provider_type=AuthProviderType.OAUTH2,
                config=OAuth2AuthConfig(
                    authorization_url=auth_url,
                    token_url=token_url,
                    scopes=scopes,
                    client_id=client_id,
                ),
            )
        ],
        session=SessionConfig(),
        rate_limit=RateLimitConfig(
            strategy=RateLimitStrategyType.SLIDING_WINDOW,
            max_requests=10,
            window_seconds=300,
        ),
        mfa=mfa,
    )


# ============================================================================
# SAML Recipe — enterprise SSO (Okta, ADFS, OneLogin)
# ============================================================================


def saml_recipe(
    idp_name: str = "okta",
    idp_metadata_url: str = "",
    idp_metadata_xml: str = "",
    sp_entity_id: str = "https://app.example.com/saml",
    sp_acs_url: str = "https://app.example.com/saml/acs",
    cert: str = "",
    key: str = "",
) -> AuthIR:
    """
    SAML 2.0 Enterprise SSO Recipe.

    Pre-configured cho common SAML IdPs: Okta, ADFS, OneLogin, PingIdentity.

    Args:
        idp_name: Tên IdP ("okta", "adfs", "onelogin", "custom")
        idp_metadata_url: URL đến SAML metadata XML của IdP
        idp_metadata_xml: Nội dung metadata XML trực tiếp
        sp_entity_id: Entity ID của Service Provider
        sp_acs_url: Assertion Consumer Service URL
        cert: SP certificate (PEM)
        key: SP private key (PEM)

    Returns:
        AuthIR với SAML provider (enterprise-grade, signed assertions)
    """
    return AuthIR(
        providers=[
            AuthProvider(
                id=f"{idp_name}_saml",
                provider_type=AuthProviderType.SAML,
                config=SAMLAuthConfig(
                    idp_metadata_url=idp_metadata_url,
                    idp_metadata_xml=idp_metadata_xml,
                    sp_entity_id=sp_entity_id,
                    sp_assertion_consumer_url=sp_acs_url,
                    name_id_format="persistent",
                    want_authn_requests_signed=True,
                    want_response_signed=True,
                    want_assertion_signed=True,
                    cert=cert,
                    key=key,
                ),
            )
        ],
        session=SessionConfig(
            cookie_name="saml_session_id",
            max_age_minutes=480,
            secure=True,
            http_only=True,
            same_site="lax",
        ),
        rate_limit=RateLimitConfig(
            strategy=RateLimitStrategyType.SLIDING_WINDOW,
            max_requests=20,
            window_seconds=300,
        ),
    )


# ============================================================================
# LDAP Recipe — Active Directory / OpenLDAP
# ============================================================================


def ldap_recipe(
    server: str,
    base_dn: str,
    use_ssl: bool = True,
    user_search_base: str = "",
    group_search_base: str = "",
    bind_dn: str = "",
    user_search_filter: str = "(sAMAccountName={login})",
) -> AuthIR:
    """
    LDAP/Active Directory Authentication Recipe.

    Connect đến LDAP directory enterprise để authenticate user.

    Args:
        server: Server URL (ldap://...:389 hoặc ldaps://...:636)
        base_dn: Base DN cho search (dc=example,dc=com)
        use_ssl: Kết nối qua SSL/TLS
        user_search_base: DN để search users
        group_search_base: DN để search groups
        bind_dn: Service account DN cho bind & search
        user_search_filter: LDAP filter tìm user

    Returns:
        AuthIR với LDAP provider
    """
    return AuthIR(
        providers=[
            AuthProvider(
                id="ldap_auth",
                provider_type=AuthProviderType.LDAP,
                config=LDAPOAuthConfig(
                    server=server,
                    use_ssl=use_ssl,
                    base_dn=base_dn,
                    user_search_base=user_search_base,
                    group_search_base=group_search_base,
                    user_search_filter=user_search_filter,
                    group_search_filter="(member={dn})",
                    bind_dn=bind_dn,
                ),
            )
        ],
        session=SessionConfig(
            cookie_name="ldap_session_id",
            max_age_minutes=480,
            secure=True,
            http_only=True,
            same_site="strict",
        ),
        rate_limit=RateLimitConfig(
            strategy=RateLimitStrategyType.SLIDING_WINDOW,
            max_requests=5,
            window_seconds=300,
            block_duration_seconds=900,
        ),
    )


# ============================================================================
# mTLS Recipe — machine-to-machine authentication
# ============================================================================


def mtls_recipe(
    ca_cert_path: str,
    server_cert_path: str = "",
    server_key_path: str = "",
    verification_mode: str = "required",
    allowed_cn_patterns: list[str] | None = None,
) -> AuthIR:
    """
    Mutual TLS Authentication Recipe.

    mTLS cho machine-to-machine authentication — B2B API, IoT device auth.

    Args:
        ca_cert_path: Path đến CA certificate verify client certs
        server_cert_path: Path đến server certificate
        server_key_path: Path đến server private key
        verification_mode: required, optional, request
        allowed_cn_patterns: Allowed Common Name patterns

    Returns:
        AuthIR với mTLS provider
    """
    return AuthIR(
        providers=[
            AuthProvider(
                id="mtls_auth",
                provider_type=AuthProviderType.MTLS,
                config=MTLSAuthConfig(
                    ca_cert_path=ca_cert_path,
                    server_cert_path=server_cert_path,
                    server_key_path=server_key_path,
                    verification_mode=verification_mode,
                    allowed_cn_patterns=allowed_cn_patterns or [],
                ),
            )
        ],
        session=SessionConfig(
            cookie_name="mtls_session",
            max_age_minutes=1440,
            secure=True,
            http_only=True,
            same_site="strict",
        ),
        rate_limit=RateLimitConfig(
            strategy=RateLimitStrategyType.TOKEN_BUCKET,
            max_requests=100,
            window_seconds=60,
            per_user=False,
            per_ip=True,
        ),
    )


# ============================================================================
# Stateful Session Recipe — server-side sessions
# ============================================================================


def stateful_session_recipe(
    store_type: str = "redis",
    store_connection_string: str = "",
    cookie_name: str = "session_id",
    ttl_seconds: int = 86400,
    idle_timeout_seconds: int = 3600,
) -> AuthIR:
    """
    Stateful Session Authentication Recipe.

    Sessions được lưu server-side — cookie chỉ chứa session ID.
    Dùng khi cần revoke session từ xa, không dùng JWT.

    Args:
        store_type: database, redis, memcached, file
        store_connection_string: Connection string cho store
        cookie_name: Tên session cookie
        ttl_seconds: TTL của session
        idle_timeout_seconds: Idle timeout

    Returns:
        AuthIR với stateful session provider
    """
    store_type_enum = SessionStoreType(store_type)

    return AuthIR(
        providers=[
            AuthProvider(
                id="session_auth",
                provider_type=AuthProviderType.SESSION,
                config=StatefulSessionConfig(
                    store_type=store_type_enum,
                    store_connection_string=store_connection_string,
                    cookie_name=cookie_name,
                    cookie_secure=True,
                    cookie_http_only=True,
                    cookie_samesite="lax",
                    ttl_seconds=ttl_seconds,
                    idle_timeout_seconds=idle_timeout_seconds,
                ),
            )
        ],
        session=SessionConfig(
            cookie_name=cookie_name,
            max_age_minutes=ttl_seconds // 60,
            secure=True,
            http_only=True,
            same_site="lax",
        ),
    )


# ============================================================================
# MFA with TOTP Recipe — add MFA to existing AuthIR
# ============================================================================


def mfa_totp_recipe(
    existing_ir: AuthIR,
    required: bool = False,
    enforce_on_roles: list[str] | None = None,
    grace_period_days: int = 0,
) -> AuthIR:
    """
    Add TOTP-based MFA to an existing AuthIR.

    Args:
        existing_ir: AuthIR từ recipe khác (JWT, OAuth2, ...)
        required: Có bắt buộc MFA không
        enforce_on_roles: List roles bắt buộc MFA (empty = tất cả)
        grace_period_days: Grace period để user enroll MFA

    Returns:
        AuthIR với MFA policy
    """
    existing_ir.mfa = MFAPolicy(
        enabled=True,
        required=required,
        providers=[MFAProviderType.TOTP],
        totp_config=TOTPConfig(
            algorithm=TOTPAlgorithm.SHA256,
            digit_count=6,
            period=30,
            skew=1,
        ),
        enforce_on_role=enforce_on_roles or [],
        grace_period_days=grace_period_days,
    )
    return existing_ir


# ============================================================================
# MFA with WebAuthn Recipe — passkeys / hardware keys
# ============================================================================


def mfa_webauthn_recipe(
    existing_ir: AuthIR,
    rp_id: str,
    rp_name: str,
    origins: list[str],
    required: bool = False,
) -> AuthIR:
    """
    Add WebAuthn (passkeys / FIDO2) MFA to an existing AuthIR.

    Args:
        existing_ir: AuthIR từ recipe khác
        rp_id: Relying Party ID (domain)
        rp_name: Relying Party display name
        origins: Allowed origins
        required: Có bắt buộc MFA không

    Returns:
        AuthIR với WebAuthn MFA policy
    """
    existing_ir.mfa = MFAPolicy(
        enabled=True,
        required=required,
        providers=[MFAProviderType.WEBAUTHN, MFAProviderType.TOTP],
        totp_config=TOTPConfig(),
        webauthn_config=WebAuthnConfig(
            rp_id=rp_id,
            rp_name=rp_name,
            origins=origins,
            user_verification="required",
        ),
    )
    return existing_ir


# ============================================================================
# Multi-Provider Recipe — combine multiple auth providers
# ============================================================================


def multi_provider_recipe(
    providers: list[AuthProvider],
    default_permissions: list[str] | None = None,
    rate_limit_config: RateLimitConfig | None = None,
    session_config: SessionConfig | None = None,
    mfa_policy: MFAPolicy | None = None,
) -> AuthIR:
    """
    Multi-Provider Authentication Recipe.

    Kết hợp nhiều authentication providers (vd: JWT + SAML + LDAP)
    cho enterprise app cần multiple auth paths.

    Args:
        providers: List các AuthProvider
        default_permissions: List permission IDs mặc định
        rate_limit_config: Rate limiting config
        session_config: Session config
        mfa_policy: MFA policy

    Returns:
        AuthIR với multiple providers
    """
    permissions = []
    if default_permissions:
        permissions = [Permission(id=p) for p in default_permissions]

    return AuthIR(
        providers=providers,
        session=session_config or SessionConfig(),
        permissions=permissions,
        rate_limit=rate_limit_config or RateLimitConfig(),
        mfa=mfa_policy or MFAPolicy(),
    )


__all__ = [
    "jwt_recipe",
    "oauth2_recipe",
    "saml_recipe",
    "ldap_recipe",
    "mtls_recipe",
    "stateful_session_recipe",
    "mfa_totp_recipe",
    "mfa_webauthn_recipe",
    "multi_provider_recipe",
]
