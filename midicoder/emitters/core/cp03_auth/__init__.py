"""
CP03: Authentication & Authorization Framework Module.

Module này cung cấp các components cho Authentication & Authorization:
- models.py: Auth data models (AuthProvider, JWTAuthConfig, OAuth2AuthConfig, AuthIR)
- parser.py: YAML parser cho Auth DSL
- fastapi.py: FastAPI emitter cho Auth code
- nestjs.py: NestJS emitter cho Auth code
- angular.py: Angular emitter cho Auth code
- react.py: React emitter cho Auth code

Capabilities: authenticate_user, authorize_permission

Author: Midicoder Team
Version: 1.0.0
"""

from midicoder.emitters.core.cp03_auth.models import (
    AuthIR,
    AuthProvider,
    AuthProviderType,
    AuthValidationResult,
    JWTAuthConfig,
    OAuth2AuthConfig,
    Permission,
    SessionConfig,
)
from midicoder.emitters.core.cp03_auth.parser import (
    AuthParser,
    parse_auth_dsl,
    validate_permission_format,
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
    # Parser
    "AuthParser",
    "parse_auth_dsl",
    "validate_permission_format",
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