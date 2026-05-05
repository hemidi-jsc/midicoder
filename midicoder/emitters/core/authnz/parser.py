"""
Auth/RBAC DSL Parser Module.

Module này cung cấp parser để chuyển Auth DSL YAML thành AuthIR:
- Parse tenant_mode (CP02)
- Parse authentication providers (CP03)
- Parse roles và policies (CP04)

Sử dụng PyYAML để parse YAML, sau đó validate và convert thành AuthIR.

CP02: Multi-Tenant Architecture
CP03: Authentication & Authorization
CP04: RBAC & Policy Engine

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from midicoder.emitters.core.authnz.models import (
    AuthIR,
    AuthProvider,
    AuthProviderType,
    JWTAuthConfig,
    OAuth2AuthConfig,
    Policy,
    PolicyCondition,
    PolicyEffect,
    Role,
    TenantMode,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ============================================================================
# Auth Parser Class
# ============================================================================


class AuthParser:
    """
    Parser cho Auth/RBAC DSL YAML.

    Parse YAML file thành AuthIR object:
    1. Load YAML file
    2. Parse tenant_mode (CP02)
    3. Parse authentication providers (CP03)
    4. Parse roles và policies (CP04)
    5. Validate và return AuthIR

    KPI-028: Missing permission detection
    KPI-029: Missing tenant filter detection
    KPI-030: Invalid role binding detection
    KPI-031: Invalid policy detection
    """

    def __init__(self, file_path: str | Path) -> None:
        """
        Initialize AuthParser.

        Args:
            file_path: Đường dẫn đến YAML file

        Raises:
            MidicoderError: Nếu file không tồn tại
        """
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            EM.raise_error(
                ErrorCode.DSL_FILE_NOT_FOUND,
                file_path=str(self.file_path),
            )

    def parse(self) -> AuthIR:
        """
        Parse YAML file thành AuthIR.

        Returns:
            AuthIR object với parsed data

        Raises:
            MidicoderError: Nếu parse hoặc validate fail
        """
        # Load YAML
        data = self._load_yaml()

        # Parse từng section
        tenant_mode = self._parse_tenant_mode(data)
        providers = self._parse_providers(data)
        roles = self._parse_roles(data)
        policies = self._parse_policies(data)

        # Build AuthIR
        auth_ir = AuthIR(
            tenant_mode=tenant_mode,
            providers=providers,
            roles=roles,
            policies=policies,
        )

        # Validate (KPI-028, KPI-029, KPI-030, KPI-031)
        auth_ir.validate()

        return auth_ir

    def _load_yaml(self) -> dict[str, Any]:
        """
        Load và parse YAML file.

        Returns:
            Parsed YAML data

        Raises:
            MidicoderError: Nếu YAML parse fail
        """
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data is None:
                EM.raise_error(
                    ErrorCode.DSL_YAML_PARSE_ERROR,
                    file_path=str(self.file_path),
                    reason="Empty YAML file",
                )

            if not isinstance(data, dict):
                EM.raise_error(
                    ErrorCode.DSL_YAML_PARSE_ERROR,
                    file_path=str(self.file_path),
                    reason="YAML root must be a mapping",
                )

            return data

        except yaml.YAMLError as e:
            EM.raise_error(
                ErrorCode.DSL_YAML_PARSE_ERROR,
                file_path=str(self.file_path),
                reason=str(e),
                cause=e,
            )

    def _parse_tenant_mode(self, data: dict[str, Any]) -> TenantMode:
        """
        Parse tenant_mode field (CP02).

        Args:
            data: Parsed YAML data

        Returns:
            TenantMode enum

        Raises:
            MidicoderError: Nếu tenant_mode không valid
        """
        tenant_mode_str = data.get("tenant_mode", "schema")

        try:
            return TenantMode(tenant_mode_str.lower())
        except ValueError:
            EM.raise_error(
                ErrorCode.CP02_TENANT_MODE_INVALID,
                tenant_mode=tenant_mode_str,
                valid_values=[mode.value for mode in TenantMode],
            )

    def _parse_providers(self, data: dict[str, Any]) -> list[AuthProvider]:
        """
        Parse authentication providers (CP03).

        Args:
            data: Parsed YAML data

        Returns:
            List AuthProvider objects

        Raises:
            MidicoderError: Nếu provider config không valid
        """
        authentication = data.get("authentication", {})
        providers_data = authentication.get("providers", [])

        if not providers_data:
            # Default to JWT if no providers specified
            return [
                AuthProvider(
                    id="default_jwt",
                    provider_type=AuthProviderType.JWT,
                    config=JWTAuthConfig(),
                )
            ]

        providers: list[AuthProvider] = []

        for i, provider_data in enumerate(providers_data):
            provider = self._parse_provider(provider_data, i)
            providers.append(provider)

        return providers

    def _parse_provider(
        self, provider_data: dict[str, Any], index: int
    ) -> AuthProvider:
        """
        Parse single authentication provider.

        Args:
            provider_data: Provider YAML data
            index: Provider index (for error messages)

        Returns:
            AuthProvider object

        Raises:
            MidicoderError: Nếu provider config không valid
        """
        provider_id = provider_data.get("id", f"provider_{index}")
        provider_type_str = provider_data.get("type", "jwt")
        config_data = provider_data.get("config", {})

        try:
            provider_type = AuthProviderType(provider_type_str.lower())
        except ValueError:
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                provider_id=provider_id,
                type=provider_type_str,
                valid_types=[t.value for t in AuthProviderType],
            )

        # Parse config based on type
        if provider_type == AuthProviderType.JWT:
            config = self._parse_jwt_config(config_data, provider_id)
        elif provider_type == AuthProviderType.OAUTH2:
            config = self._parse_oauth2_config(config_data, provider_id)
        else:
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                provider_id=provider_id,
                type=provider_type_str,
                reason="Unsupported provider type",
            )

        return AuthProvider(
            id=provider_id,
            provider_type=provider_type,
            config=config,
        )

    def _parse_jwt_config(
        self, config_data: dict[str, Any], provider_id: str
    ) -> JWTAuthConfig:
        """
        Parse JWT auth config.

        Args:
            config_data: Config YAML data
            provider_id: Provider ID (for error messages)

        Returns:
            JWTAuthConfig object
        """
        return JWTAuthConfig(
            expire_minutes=config_data.get("expire_minutes", 30),
            refresh_expire_days=config_data.get("refresh_expire_days", 7),
            algorithm=config_data.get("algorithm", "HS256"),
            tenant_scoped=config_data.get("tenant_scoped", True),  # KPI-029
        )

    def _parse_oauth2_config(
        self, config_data: dict[str, Any], provider_id: str
    ) -> OAuth2AuthConfig:
        """
        Parse OAuth2 auth config.

        Args:
            config_data: Config YAML data
            provider_id: Provider ID (for error messages)

        Returns:
            OAuth2AuthConfig object

        Raises:
            MidicoderError: Nếu required fields missing
        """
        authorization_url = config_data.get("authorization_url")
        token_url = config_data.get("token_url")

        if not authorization_url:
            EM.raise_error(
                ErrorCode.DSL_MISSING_REQUIRED_FIELD,
                field="authorization_url",
                provider_id=provider_id,
            )

        if not token_url:
            EM.raise_error(
                ErrorCode.DSL_MISSING_REQUIRED_FIELD,
                field="token_url",
                provider_id=provider_id,
            )

        return OAuth2AuthConfig(
            authorization_url=authorization_url,
            token_url=token_url,
            scopes=config_data.get("scopes", []),
        )

    def _parse_roles(self, data: dict[str, Any]) -> dict[str, Role]:
        """
        Parse roles (CP04).

        Args:
            data: Parsed YAML data

        Returns:
            Mapping từ role id -> Role object
        """
        authorization = data.get("authorization", {})
        roles_data = authorization.get("roles", [])

        roles: dict[str, Role] = {}

        for role_data in roles_data:
            role = self._parse_role(role_data)
            roles[role.id] = role

        return roles

    def _parse_role(self, role_data: dict[str, Any]) -> Role:
        """
        Parse single role.

        Args:
            role_data: Role YAML data

        Returns:
            Role object
        """
        return Role(
            id=role_data["id"],
            permissions=role_data.get("permissions", []),
            parents=role_data.get("parents", []),
            tenant_scoped=role_data.get("tenant_scoped", True),  # KPI-029
            description=role_data.get("description", ""),
        )

    def _parse_policies(self, data: dict[str, Any]) -> dict[str, Policy]:
        """
        Parse policies (CP04).

        Args:
            data: Parsed YAML data

        Returns:
            Mapping từ policy id -> Policy object

        KPI-031: Policy validation tại compile-time
        """
        authorization = data.get("authorization", {})
        policies_data = authorization.get("policies", [])

        policies: dict[str, Policy] = {}

        for policy_data in policies_data:
            policy = self._parse_policy(policy_data)
            policies[policy.id] = policy

        return policies

    def _parse_policy(self, policy_data: dict[str, Any]) -> Policy:
        """
        Parse single policy.

        Args:
            policy_data: Policy YAML data

        Returns:
            Policy object

        KPI-031: Policy validation
        """
        effect_str = policy_data.get("effect", "allow")

        try:
            effect = PolicyEffect(effect_str.lower())
        except ValueError:
            EM.raise_error(
                ErrorCode.CP04_POLICY_NOT_FOUND,
                policy_id=policy_data.get("id", "unknown"),
                effect=effect_str,
                valid_effects=[e.value for e in PolicyEffect],
            )

        # Parse conditions
        conditions = []
        conditions_data = policy_data.get("conditions", [])

        for cond_data in conditions_data:
            condition = PolicyCondition(
                expression=cond_data["expression"],
                description=cond_data.get("description", ""),
            )
            conditions.append(condition)

        return Policy(
            id=policy_data["id"],
            effect=effect,
            conditions=conditions,
            description=policy_data.get("description", ""),
        )


# ============================================================================
# Utility Functions
# ============================================================================


def parse_auth_dsl(file_path: str | Path) -> AuthIR:
    """
    Parse Auth DSL YAML file.

    Convenience function để parse YAML file thành AuthIR.

    Args:
        file_path: Đường dẫn đến YAML file

    Returns:
        AuthIR object
    """
    parser = AuthParser(file_path)
    return parser.parse()


def validate_permission_format(permission: str) -> bool:
    """
    Validate permission format.

    Permission format: "resource:action" (ví dụ: "user:create", "order:*")

    KPI-028: Missing permission detection.

    Args:
        permission: Permission string

    Returns:
        True nếu format valid
    """
    # Check wildcard format (ví dụ: "user:*")
    if permission.endswith(":*"):
        resource = permission[:-2]
        return bool(resource and re.match(r"^[a-z]+$", resource))

    # Check specific format (ví dụ: "user:create")
    parts = permission.split(":")
    if len(parts) != 2:
        return False

    resource, action = parts
    return bool(resource and action and re.match(r"^[a-z]+$", resource) and re.match(r"^[a-z]+$", action))


__all__ = [
    "AuthParser",
    "parse_auth_dsl",
    "validate_permission_format",
]