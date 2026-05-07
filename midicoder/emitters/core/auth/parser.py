"""
CP03: Authentication & Authorization Framework — DSL Parser.

Module này cung cấp parser để chuyển Auth DSL YAML thành AuthIR:
- Parse authentication providers (CP03)
- Parse session configuration
- Parse permissions

Sử dụng PyYAML để parse YAML, sau đó validate và convert thành AuthIR.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from midicoder.emitters.core.auth.models import (
    AuthIR,
    AuthProvider,
    AuthProviderType,
    JWTAuthConfig,
    OAuth2AuthConfig,
    Permission,
    SessionConfig,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ============================================================================
# Auth Parser Class
# ============================================================================


class AuthParser:
    """
    Parser cho Authentication DSL YAML.

    Parse YAML file thành AuthIR object:
    1. Load YAML file
    2. Parse authentication providers (CP03)
    3. Parse session configuration
    4. Parse permissions
    5. Validate và return AuthIR
    """

    def __init__(self, file_path: str | Path) -> None:
        """
        Khởi tạo AuthParser.

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
        providers = self._parse_providers(data)
        session = self._parse_session(data)
        permissions = self._parse_permissions(data)

        # Build AuthIR
        auth_ir = AuthIR(
            providers=providers,
            session=session,
            permissions=permissions,
        )

        # Validate
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
                    reason="File YAML rỗng",
                )

            if not isinstance(data, dict):
                EM.raise_error(
                    ErrorCode.DSL_YAML_PARSE_ERROR,
                    file_path=str(self.file_path),
                    reason="YAML root phải là mapping",
                )

            return data

        except yaml.YAMLError as e:
            EM.raise_error(
                ErrorCode.DSL_YAML_PARSE_ERROR,
                file_path=str(self.file_path),
                reason=str(e),
                cause=e,
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
            # Mặc định JWT nếu không có providers
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
            index: Provider index (cho error messages)

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

        # Parse config theo type
        if provider_type == AuthProviderType.JWT:
            config = self._parse_jwt_config(config_data, provider_id)
        elif provider_type == AuthProviderType.OAUTH2:
            config = self._parse_oauth2_config(config_data, provider_id)
        else:
            EM.raise_error(
                ErrorCode.CP03_AUTH_CONFIG_INVALID,
                provider_id=provider_id,
                type=provider_type_str,
                reason="Loại provider không được hỗ trợ",
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
            provider_id: Provider ID (cho error messages)

        Returns:
            JWTAuthConfig object
        """
        return JWTAuthConfig(
            expire_minutes=config_data.get("expire_minutes", 30),
            refresh_expire_days=config_data.get("refresh_expire_days", 7),
            algorithm=config_data.get("algorithm", "HS256"),
            tenant_scoped=config_data.get("tenant_scoped", True),
        )

    def _parse_oauth2_config(
        self, config_data: dict[str, Any], provider_id: str
    ) -> OAuth2AuthConfig:
        """
        Parse OAuth2 auth config.

        Args:
            config_data: Config YAML data
            provider_id: Provider ID (cho error messages)

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

    def _parse_session(self, data: dict[str, Any]) -> SessionConfig:
        """
        Parse session configuration.

        Args:
            data: Parsed YAML data

        Returns:
            SessionConfig object
        """
        authentication = data.get("authentication", {})
        session_data = authentication.get("session", {})

        return SessionConfig(
            cookie_name=session_data.get("cookie_name", "session_id"),
            max_age_minutes=session_data.get("max_age_minutes", 480),
            secure=session_data.get("secure", True),
            http_only=session_data.get("http_only", True),
            same_site=session_data.get("same_site", "lax"),
            path=session_data.get("path", "/"),
        )

    def _parse_permissions(self, data: dict[str, Any]) -> list[Permission]:
        """
        Parse permissions list.

        Args:
            data: Parsed YAML data

        Returns:
            List Permission objects
        """
        authorization = data.get("authorization", {})
        permissions_data = authorization.get("permissions", [])

        permissions: list[Permission] = []

        for perm_data in permissions_data:
            if isinstance(perm_data, str):
                # Format đơn giản: "user:create"
                perm = Permission(id=perm_data)
            elif isinstance(perm_data, dict):
                perm = Permission(
                    id=perm_data["id"],
                    description=perm_data.get("description", ""),
                )
            else:
                continue

            permissions.append(perm)

        return permissions


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

    Args:
        permission: Permission string

    Returns:
        True nếu format valid
    """
    import re

    # Check wildcard format (ví dụ: "user:*")
    if permission.endswith(":*"):
        resource = permission[:-2]
        return bool(resource and re.match(r"^[a-z]+$", resource))

    # Check specific format (ví dụ: "user:create")
    parts = permission.split(":")
    if len(parts) != 2:
        return False

    resource, action = parts
    return bool(
        resource and action
        and re.match(r"^[a-z]+$", resource)
        and re.match(r"^[a-z]+$", action)
    )


__all__ = [
    "AuthParser",
    "parse_auth_dsl",
    "validate_permission_format",
]