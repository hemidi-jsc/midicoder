"""
CP03: Authentication & Authorization Framework Module.

Module này cung cấp các components cho Authentication & Authorization:
- models.py: Auth data models (AuthProvider, JWTAuthConfig, OAuth2AuthConfig,
  SAMLAuthConfig, LDAPOAuthConfig, MTLSAuthConfig, StatefulSessionConfig,
  RateLimitConfig, TOTPConfig, WebAuthnConfig, MFAPolicy, AuthIR)
- parser.py: YAML parser cho Auth DSL
- recipes.py: Pattern recipes (jwt_recipe, oauth2_recipe, saml_recipe, ...)
- fastapi.py: FastAPI emitter cho Auth code
- nestjs.py: NestJS emitter cho Auth code
- angular.py: Angular emitter cho Auth code
- react.py: React emitter cho Auth code

Capabilities: authenticate_user, authorize_permission

Author: Midicoder Team
Version: 1.1.0
"""

from midicoder.emitters.core.cp03_auth.models import (
    AuthIR,
    AuthProvider,
    AuthProviderType,
    AuthValidationResult,
    JWTAuthConfig,
    LDAPOAuthConfig,
    LDAPReferralMode,
    MFAPolicy,
    MFAProviderType,
    MTLSAuthConfig,
    MTLSVerificationMode,
    NameIDFormat,
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
from midicoder.emitters.core.cp03_auth.parser import (
    AuthParser,
    parse_auth_dsl,
    validate_permission_format,
)
from midicoder.emitters.core.cp03_auth.recipes import (
    jwt_recipe,
    oauth2_recipe,
    saml_recipe,
    ldap_recipe,
    mtls_recipe,
    stateful_session_recipe,
    mfa_totp_recipe,
    mfa_webauthn_recipe,
    multi_provider_recipe,
)
from midicoder.emitters.core.cp03_auth.fastapi import (
    FastAPIAuthEmitter,
    emit_fastapi_auth,
)
from midicoder.emitters.core.cp03_auth.nestjs import (
    NestJSEmitter,
    emit_nestjs_auth,
)
from midicoder.emitters.core.cp03_auth.angular import (
    AngularEmitter,
    emit_angular_auth,
)
from midicoder.emitters.core.cp03_auth.react import (
    ReactEmitter,
    emit_react_auth,
)

__all__ = [
    # Enums
    "AuthProviderType",
    "NameIDFormat",
    "LDAPReferralMode",
    "MTLSVerificationMode",
    "SessionStoreType",
    "RateLimitStrategyType",
    "MFAProviderType",
    "TOTPAlgorithm",
    # Config classes
    "JWTAuthConfig",
    "OAuth2AuthConfig",
    "SAMLAuthConfig",
    "LDAPOAuthConfig",
    "MTLSAuthConfig",
    "StatefulSessionConfig",
    "SessionConfig",
    "RateLimitConfig",
    "TOTPConfig",
    "WebAuthnConfig",
    "MFAPolicy",
    # Main models
    "AuthProvider",
    "Permission",
    "AuthIR",
    # Validation
    "AuthValidationResult",
    # Parser
    "AuthParser",
    "parse_auth_dsl",
    "validate_permission_format",
    # Recipes
    "jwt_recipe",
    "oauth2_recipe",
    "saml_recipe",
    "ldap_recipe",
    "mtls_recipe",
    "stateful_session_recipe",
    "mfa_totp_recipe",
    "mfa_webauthn_recipe",
    "multi_provider_recipe",
    # FastAPI Emitter
    "FastAPIAuthEmitter",
    "emit_fastapi_auth",
    # NestJS Emitter
    "NestJSEmitter",
    "emit_nestjs_auth",
    # Angular Emitter
    "AngularEmitter",
    "emit_angular_auth",
    # React Emitter
    "ReactEmitter",
    "emit_react_auth",
]