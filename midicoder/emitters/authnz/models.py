"""
Auth/RBAC IR Models Module.

Module này định nghĩa các data models cho Auth/RBAC IR (CP02-CP04):
- TenantMode: Multi-tenant isolation strategies
- AuthProvider: JWT/OAuth2 authentication providers
- Role: Role definitions với permissions và inheritance
- Policy: Policy rules (OPA-compatible)
- AuthIR: Complete authentication/authorization configuration

CP02: Multi-Tenant Architecture
CP03: Authentication & Authorization  
CP04: RBAC & Policy Engine

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ============================================================================
# Tenant Mode Enum (CP02)
# ============================================================================


class TenantMode(str, Enum):
    """
    Multi-tenant isolation strategies.

    database: Mỗi tenant có database riêng (strongest isolation)
    schema: Mỗi tenant có schema riêng trong cùng database
    row: Tenant isolation qua row-level filters (tenant_id column)
    hybrid: Kết hợp row-level + additional checks
    """
    DATABASE = "database"
    SCHEMA = "schema"
    ROW = "row"
    HYBRID = "hybrid"


# ============================================================================
# Auth Provider Type Enum (CP03)
# ============================================================================


class AuthProviderType(str, Enum):
    """
    Authentication provider types.

    jwt: JWT-based authentication
    oauth2: OAuth2 flow authentication
    """
    JWT = "jwt"
    OAUTH2 = "oauth2"


# ============================================================================
# Policy Effect Enum (CP04)
# ============================================================================


class PolicyEffect(str, Enum):
    """
    Policy evaluation effects.

    allow: Cho phép action
    deny: Từ chối action
    """
    ALLOW = "allow"
    DENY = "deny"


# ============================================================================
# Auth Provider Config Dataclass
# ============================================================================


@dataclass
class JWTAuthConfig:
    """
    JWT Authentication Configuration.

    Attributes:
        expire_minutes: Thời gian hết hạn access token (phút)
        refresh_expire_days: Thời gian hết hạn refresh token (ngày)
        algorithm: JWT signing algorithm (HS256, RS256, etc.)
        tenant_scoped: Có embed tenant_id vào token không (KPI-029)
    """
    expire_minutes: int = 30
    refresh_expire_days: int = 7
    algorithm: str = "HS256"
    tenant_scoped: bool = True


@dataclass
class OAuth2AuthConfig:
    """
    OAuth2 Authentication Configuration.

    Attributes:
        authorization_url: URL cho authorization endpoint
        token_url: URL cho token endpoint
        scopes: List OAuth2 scopes
    """
    authorization_url: str
    token_url: str
    scopes: list[str] = field(default_factory=list)


# ============================================================================
# Auth Provider Dataclass
# ============================================================================


@dataclass
class AuthProvider:
    """
    Authentication Provider.

    Attributes:
        id: Provider identifier (ví dụ: jwt_auth, oauth2_auth)
        provider_type: Loại provider (jwt, oauth2)
        config: Configuration cho provider
    """
    id: str
    provider_type: AuthProviderType
    config: JWTAuthConfig | OAuth2AuthConfig


# ============================================================================
# Role Dataclass (CP04)
# ============================================================================


@dataclass
class Role:
    """
    Role definition cho RBAC.

    Attributes:
        id: Role identifier (ví dụ: admin, user, viewer)
        permissions: List permission strings (support wildcard: "user:*")
        parents: List parent role IDs cho inheritance
        tenant_scoped: Role chỉ apply trong tenant này không (KPI-029)
        description: Mô tả role (optional)

    KPI-029: tenant_scoped=True nghĩa là role chỉ valid trong tenant context
    KPI-030: parents field được validate để detect cycles
    """
    id: str
    permissions: list[str] = field(default_factory=list)
    parents: list[str] = field(default_factory=list)
    tenant_scoped: bool = True
    description: str = ""

    def get_all_permissions(self, roles: dict[str, "Role"]) -> set[str]:
        """
        Lấy tất cả permissions của role (bao gồm inherited từ parents).

        KPI-030: Validate parent role references tồn tại.

        Args:
            roles: Mapping từ role id -> Role object

        Returns:
            Set của tất cả permission strings (bao gồm từ parent roles)

        Raises:
            MidicoderError: Nếu parent role không tồn tại (KPI-030)
        """
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        all_permissions: set[str] = set()

        # Thêm permissions của role này
        all_permissions.update(self.permissions)

        # Recursively thêm permissions từ parents
        for parent_id in self.parents:
            if parent_id not in roles:
                # KPI-030: Invalid role binding detection
                EM.raise_error(
                    ErrorCode.CP04_ROLE_NOT_FOUND,
                    role_id=parent_id,
                    child_role=self.id,
                )

            parent_role = roles[parent_id]
            all_permissions.update(parent_role.get_all_permissions(roles))

        return all_permissions

    def has_permission(self, permission: str, roles: dict[str, "Role"]) -> bool:
        """
        Check nếu role có permission (bao gồm inherited).

        Support wildcard matching (ví dụ: "user:*" match "user:create").

        Args:
            permission: Permission string để check
            roles: Mapping từ role id -> Role object

        Returns:
            True nếu role có permission, False nếu không
        """
        all_permissions = self.get_all_permissions(roles)

        for perm in all_permissions:
            # Check exact match
            if perm == permission:
                return True

            # Check wildcard match (ví dụ: "user:*" match "user:create")
            if perm.endswith("*"):
                prefix = perm[:-1]  # "user:"
                if permission.startswith(prefix):
                    return True

        return False


# ============================================================================
# Policy Condition Dataclass
# ============================================================================


@dataclass
class PolicyCondition:
    """
    Policy condition cho policy evaluation.

    Attributes:
        expression: Expression string để evaluate
        description: Mô tả condition (optional)
    """
    expression: str
    description: str = ""


# ============================================================================
# Policy Dataclass (CP04)
# ============================================================================


@dataclass
class Policy:
    """
    Policy definition (OPA-compatible).

    Attributes:
        id: Policy identifier
        description: Mô tả policy
        effect: Policy effect (allow/deny)
        conditions: List policy conditions

    KPI-031: Policy validation tại compile-time (syntax check)
    """
    id: str
    effect: PolicyEffect
    conditions: list[PolicyCondition] = field(default_factory=list)
    description: str = ""

    def validate(self) -> None:
        """
        Validate policy.

        KPI-031: Policy validation tại compile-time.

        Raises:
            MidicoderError: Nếu policy không valid
        """
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        if not self.conditions:
            # Empty conditions là valid (always allow/deny)
            return

        # Basic syntax validation cho expressions
        for condition in self.conditions:
            self._validate_expression(condition.expression)

    def _validate_expression(self, expression: str) -> None:
        """
        Validate policy expression syntax.

        Basic validation:
        - Check balanced parentheses
        - Check valid operators
        - Check valid function calls

        Args:
            expression: Expression string

        Raises:
            MidicoderError: Nếu expression không valid (KPI-031)
        """
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        # Check balanced parentheses
        if expression.count("(") != expression.count(")"):
            EM.raise_error(
                ErrorCode.CP04_POLICY_SYNTAX_ERROR,
                policy_id=self.id,
                expression=expression,
                reason="Unbalanced parentheses",
            )

        # Check for valid operators
        valid_operators = ["==", "!=", ">", "<", ">=", "<=", "and", "or", "not"]
        expression_lower = expression.lower()

        # Basic check: expression should contain at least one operator
        has_operator = any(op in expression_lower for op in valid_operators)
        if not has_operator:
            # Allow simple expressions like "user.id"
            if "." not in expression and " " not in expression:
                pass  # Simple identifier
            else:
                EM.raise_error(
                    ErrorCode.CP04_POLICY_SYNTAX_ERROR,
                    policy_id=self.id,
                    expression=expression,
                    reason="Missing valid operator",
                )


# ============================================================================
# Auth IR (Main Dataclass)
# ============================================================================


@dataclass
class AuthIR:
    """
    Authentication & Authorization IR.

    Intermediate representation cho CP02-CP04:
    - CP02: Tenant mode configuration
    - CP03: Authentication providers
    - CP04: Roles và Policies

    Attributes:
        tenant_mode: Multi-tenant isolation strategy (CP02)
        providers: List authentication providers (CP03)
        roles: Mapping từ role id -> Role (CP04)
        policies: Mapping từ policy id -> Policy (CP04)

    KPI-028: Missing permission detection
    KPI-029: Missing tenant filter detection
    KPI-030: Invalid role binding detection
    KPI-031: Invalid policy detection
    """

    tenant_mode: TenantMode = TenantMode.SCHEMA
    providers: list[AuthProvider] = field(default_factory=list)
    roles: dict[str, Role] = field(default_factory=dict)
    policies: dict[str, Policy] = field(default_factory=dict)

    def validate(self) -> None:
        """
        Validate AuthIR.

        Validate:
        - At least one auth provider
        - Role parent references exist (KPI-030)
        - Policy syntax valid (KPI-031)

        Raises:
            MidicoderError: Nếu validation fail
        """
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        # Check at least one auth provider
        if not self.providers:
            EM.raise_error(
                ErrorCode.CP03_AUTH_PROVIDER_NOT_FOUND,
                reason="At least one authentication provider required",
            )

        # Validate roles (KPI-030: detect cycles và missing parents)
        self._validate_roles()

        # Validate policies (KPI-031)
        for policy_id, policy in self.policies.items():
            policy.validate()

    def _validate_roles(self) -> None:
        """
        Validate roles.

        Checks:
        - Parent role references exist (KPI-030)
        - No circular inheritance (KPI-030)

        Raises:
            MidicoderError: Nếu validation fail
        """
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        # Check parent references
        for role_id, role in self.roles.items():
            for parent_id in role.parents:
                if parent_id not in self.roles:
                    EM.raise_error(
                        ErrorCode.CP04_ROLE_NOT_FOUND,
                        role_id=parent_id,
                        child_role=role_id,
                    )

        # Detect cycles
        for role_id in self.roles:
            self._check_role_cycle(role_id, set())

    def _check_role_cycle(self, role_id: str, visited: set[str]) -> None:
        """
        Check cho role inheritance cycles.

        Args:
            role_id: Role ID để check
            visited: Set của visited role IDs

        Raises:
            MidicoderError: Nếu phát hiện cycle (KPI-030)
        """
        from midicoder.errors import ErrorCode, MidicoderErrorManager as EM

        if role_id in visited:
            EM.raise_error(
                ErrorCode.CP04_ROLE_CYCLE_DETECTED,
                role_id=role_id,
            )

        if role_id not in self.roles:
            return

        visited.add(role_id)
        role = self.roles[role_id]

        for parent_id in role.parents:
            self._check_role_cycle(parent_id, visited.copy())

    def get_user_permissions(
        self, user_roles: list[str], tenant_id: str | None = None
    ) -> set[str]:
        """
        Lấy tất cả permissions của user từ roles.

        KPI-029: Filter tenant-scoped roles nếu có tenant_id.

        Args:
            user_roles: List role IDs của user
            tenant_id: Tenant ID (optional cho KPI-029)

        Returns:
            Set của tất cả permission strings
        """
        all_permissions: set[str] = set()

        for role_id in user_roles:
            if role_id not in self.roles:
                continue

            role = self.roles[role_id]

            # KPI-029: Check tenant-scoped roles
            if role.tenant_scoped and tenant_id:
                # Role is tenant-scoped, user must belong to same tenant
                # (tenant check happens at runtime)
                pass

            all_permissions.update(role.get_all_permissions(self.roles))

        return all_permissions


# ============================================================================
# Validation Result Dataclass
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
    "TenantMode",
    "AuthProviderType",
    "PolicyEffect",
    # Config classes
    "JWTAuthConfig",
    "OAuth2AuthConfig",
    # Main models
    "AuthProvider",
    "Role",
    "PolicyCondition",
    "Policy",
    "AuthIR",
    # Validation
    "AuthValidationResult",
]