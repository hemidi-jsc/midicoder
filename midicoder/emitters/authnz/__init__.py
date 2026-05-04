"""
AuthN/AuthZ (Authentication & Authorization) Module.

Module này cung cấp các components cho Authentication, Authorization và RBAC:
- auth_models.py: Auth IR data models (TenantMode, AuthProvider, Role, Policy, AuthIR)
- auth_parser.py: YAML parser cho Auth DSL
- auth_fastapi.py: FastAPI emitter cho Auth code
- auth_nestjs.py: NestJS emitter cho Auth code

CP02: Multi-Tenant Architecture
CP03: Authentication & Authorization
CP04: RBAC & Policy Engine

KPI-028: Missing permission detection
KPI-029: Missing tenant filter detection
KPI-030: Invalid role binding detection
KPI-031: Invalid policy detection

Author: Midicoder Team
Version: 1.0.0
"""

from midicoder.emitters.authnz.models import (
    AuthIR,
    AuthProvider,
    AuthProviderType,
    AuthValidationResult,
    JWTAuthConfig,
    OAuth2AuthConfig,
    Policy,
    PolicyCondition,
    PolicyEffect,
    Role,
    TenantMode,
)
from midicoder.emitters.authnz.parser import (
    AuthParser,
    parse_auth_dsl,
    validate_permission_format,
)
from midicoder.emitters.authnz.fastapi import (
    FastAPIAuthEmitter,
    emit_fastapi_auth,
)
from midicoder.emitters.authnz.nestjs import (
    NestJSEmitter,
    emit_nestjs_auth,
)

__all__ = [
    # Models
    "TenantMode",
    "AuthProviderType",
    "PolicyEffect",
    "JWTAuthConfig",
    "OAuth2AuthConfig",
    "AuthProvider",
    "Role",
    "PolicyCondition",
    "Policy",
    "AuthIR",
    "AuthValidationResult",
    # Parser
    "AuthParser",
    "parse_auth_dsl",
    "validate_permission_format",
    # FastAPI Emitters
    "FastAPIAuthEmitter",
    "emit_fastapi_auth",
    # NestJS Emitters
    "NestJSEmitter",
    "emit_nestjs_auth",
]
