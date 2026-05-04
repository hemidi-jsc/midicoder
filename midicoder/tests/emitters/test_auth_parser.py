"""
Tests cho Auth/RBAC DSL Parser.

Unit tests cho:
- AuthParser class
- Auth models (TenantMode, AuthProvider, Role, Policy)
- Validation logic (KPI-028, KPI-029, KPI-030, KPI-031)

CP02: Multi-Tenant Architecture
CP03: Authentication & Authorization
CP04: RBAC & Policy Engine

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
import tempfile

from midicoder.emitters.authnz.models import (
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
from midicoder.emitters.authnz.parser import (
    AuthParser,
    parse_auth_dsl,
    validate_permission_format,
)
from midicoder.errors import ErrorCode, MidicoderError, MidicoderErrorManager as EM


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_auth_yaml():
    """Sample Auth DSL YAML content."""
    return """
tenant_mode: schema

authentication:
  providers:
    - id: jwt_auth
      type: jwt
      config:
        expire_minutes: 30
        refresh_expire_days: 7
        algorithm: HS256
        tenant_scoped: true

authorization:
  roles:
    - id: super_admin
      permissions:
        - "*"
      parents: []
      tenant_scoped: false
    
    - id: tenant_admin
      permissions:
        - "user:*"
        - "order:*"
      parents: []
      tenant_scoped: true
    
    - id: user
      permissions:
        - "order:create"
        - "order:read"
      parents: []
      tenant_scoped: true

  policies:
    - id: tenant_isolation
      description: "Tenant isolation policy"
      effect: deny
      conditions:
        - expression: "user.tenant_id != resource.tenant_id"
          description: "User not in resource tenant"
"""


@pytest.fixture
def temp_yaml_file(sample_auth_yaml):
    """Create temporary YAML file with sample content."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        f.write(sample_auth_yaml)
        temp_path = Path(f.name)
    
    yield temp_path
    temp_path.unlink()


# ============================================================================
# Test Auth Models
# ============================================================================


class TestTenantMode:
    """Tests cho TenantMode enum."""

    def test_tenant_mode_values(self):
        """Test TenantMode enum values."""
        assert TenantMode.DATABASE.value == "database"
        assert TenantMode.SCHEMA.value == "schema"
        assert TenantMode.ROW.value == "row"
        assert TenantMode.HYBRID.value == "hybrid"

    def test_tenant_mode_from_string(self):
        """Test TenantMode from string."""
        assert TenantMode("schema") == TenantMode.SCHEMA
        assert TenantMode("database") == TenantMode.DATABASE

    def test_tenant_mode_invalid_value(self):
        """Test TenantMode with invalid value."""
        with pytest.raises(ValueError):
            TenantMode("invalid_mode")


class TestAuthProvider:
    """Tests cho AuthProvider model."""

    def test_jwt_auth_provider(self):
        """Test JWT auth provider creation."""
        provider = AuthProvider(
            id="jwt_auth",
            provider_type=AuthProviderType.JWT,
            config=JWTAuthConfig(expire_minutes=60),
        )
        
        assert provider.id == "jwt_auth"
        assert provider.provider_type == AuthProviderType.JWT
        assert provider.config.expire_minutes == 60
        assert provider.config.tenant_scoped is True  # KPI-029

    def test_oauth2_auth_provider(self):
        """Test OAuth2 auth provider creation."""
        provider = AuthProvider(
            id="oauth2_auth",
            provider_type=AuthProviderType.OAUTH2,
            config=OAuth2AuthConfig(
                authorization_url="/oauth/authorize",
                token_url="/oauth/token",
                scopes=["read", "write"],
            ),
        )
        
        assert provider.id == "oauth2_auth"
        assert provider.provider_type == AuthProviderType.OAUTH2
        assert provider.config.scopes == ["read", "write"]


class TestRole:
    """Tests cho Role model."""

    def test_role_creation(self):
        """Test Role creation."""
        role = Role(
            id="admin",
            permissions=["user:*", "order:*"],
            parents=[],
            tenant_scoped=True,
        )
        
        assert role.id == "admin"
        assert role.permissions == ["user:*", "order:*"]
        assert role.tenant_scoped is True  # KPI-029

    def test_role_get_all_permissions_no_inheritance(self):
        """Test Role.get_all_permissions() without inheritance."""
        roles = {
            "admin": Role(
                id="admin",
                permissions=["user:create", "user:read"],
                parents=[],
            ),
        }
        
        permissions = roles["admin"].get_all_permissions(roles)
        assert permissions == {"user:create", "user:read"}

    def test_role_get_all_permissions_with_inheritance(self):
        """Test Role.get_all_permissions() with inheritance."""
        roles = {
            "base": Role(
                id="base",
                permissions=["user:read"],
                parents=[],
            ),
            "admin": Role(
                id="admin",
                permissions=["user:create"],
                parents=["base"],
            ),
        }
        
        permissions = roles["admin"].get_all_permissions(roles)
        assert permissions == {"user:read", "user:create"}

    def test_role_get_all_permissions_missing_parent(self):
        """Test Role.get_all_permissions() with missing parent (KPI-030)."""
        roles = {
            "admin": Role(
                id="admin",
                permissions=["user:create"],
                parents=["missing_role"],
            ),
        }
        
        with pytest.raises(MidicoderError) as exc_info:
            roles["admin"].get_all_permissions(roles)
        
        assert exc_info.value.code == ErrorCode.CP04_ROLE_NOT_FOUND

    def test_role_has_permission_exact_match(self):
        """Test Role.has_permission() with exact match."""
        roles = {
            "admin": Role(
                id="admin",
                permissions=["user:create"],
                parents=[],
            ),
        }
        
        assert roles["admin"].has_permission("user:create", roles) is True
        assert roles["admin"].has_permission("user:delete", roles) is False

    def test_role_has_permission_wildcard_match(self):
        """Test Role.has_permission() with wildcard match."""
        roles = {
            "admin": Role(
                id="admin",
                permissions=["user:*"],
                parents=[],
            ),
        }
        
        assert roles["admin"].has_permission("user:create", roles) is True
        assert roles["admin"].has_permission("user:delete", roles) is True
        assert roles["admin"].has_permission("order:create", roles) is False


class TestPolicy:
    """Tests cho Policy model."""

    def test_policy_creation(self):
        """Test Policy creation."""
        policy = Policy(
            id="tenant_isolation",
            effect=PolicyEffect.DENY,
            conditions=[
                PolicyCondition(
                    expression="user.tenant_id != resource.tenant_id",
                    description="User not in resource tenant",
                ),
            ],
            description="Tenant isolation policy",
        )
        
        assert policy.id == "tenant_isolation"
        assert policy.effect == PolicyEffect.DENY
        assert len(policy.conditions) == 1

    def test_policy_validate_valid(self):
        """Test Policy.validate() with valid policy."""
        policy = Policy(
            id="test_policy",
            effect=PolicyEffect.ALLOW,
            conditions=[
                PolicyCondition(expression="user.id == resource.owner_id"),
            ],
        )
        
        # Should not raise
        policy.validate()

    def test_policy_validate_unbalanced_parentheses(self):
        """Test Policy.validate() with unbalanced parentheses (KPI-031)."""
        policy = Policy(
            id="test_policy",
            effect=PolicyEffect.ALLOW,
            conditions=[
                PolicyCondition(expression="user.id == (resource.owner_id"),
            ],
        )
        
        with pytest.raises(MidicoderError) as exc_info:
            policy.validate()
        
        assert exc_info.value.code == ErrorCode.CP04_POLICY_SYNTAX_ERROR


# ============================================================================
# Test AuthIR
# ============================================================================


class TestAuthIR:
    """Tests cho AuthIR model."""

    def test_auth_ir_default_values(self):
        """Test AuthIR default values."""
        auth_ir = AuthIR()
        
        assert auth_ir.tenant_mode == TenantMode.SCHEMA
        assert auth_ir.providers == []
        assert auth_ir.roles == {}
        assert auth_ir.policies == {}

    def test_auth_ir_validate_no_providers(self):
        """Test AuthIR.validate() with no providers."""
        auth_ir = AuthIR()
        
        with pytest.raises(MidicoderError) as exc_info:
            auth_ir.validate()
        
        assert exc_info.value.code == ErrorCode.CP03_AUTH_PROVIDER_NOT_FOUND

    def test_auth_ir_validate_with_providers(self):
        """Test AuthIR.validate() with providers."""
        auth_ir = AuthIR(
            providers=[
                AuthProvider(
                    id="jwt_auth",
                    provider_type=AuthProviderType.JWT,
                    config=JWTAuthConfig(),
                ),
            ],
        )
        
        # Should not raise
        auth_ir.validate()

    def test_auth_ir_get_user_permissions(self):
        """Test AuthIR.get_user_permissions()."""
        auth_ir = AuthIR(
            tenant_mode=TenantMode.SCHEMA,
            providers=[
                AuthProvider(
                    id="jwt_auth",
                    provider_type=AuthProviderType.JWT,
                    config=JWTAuthConfig(),
                ),
            ],
            roles={
                "admin": Role(
                    id="admin",
                    permissions=["user:*"],
                    parents=[],
                ),
            },
        )
        
        permissions = auth_ir.get_user_permissions(["admin"])
        assert permissions == {"user:*"}


# ============================================================================
# Test AuthParser
# ============================================================================


class TestAuthParser:
    """Tests cho AuthParser class."""

    def test_parse_file_not_found(self):
        """Test parse() with file not found."""
        with pytest.raises(MidicoderError) as exc_info:
            AuthParser("/nonexistent/path/auth.yaml")
        
        assert exc_info.value.code == ErrorCode.DSL_FILE_NOT_FOUND

    def test_parse_valid_file(self, temp_yaml_file):
        """Test parse() with valid file."""
        parser = AuthParser(temp_yaml_file)
        auth_ir = parser.parse()
        
        assert auth_ir.tenant_mode == TenantMode.SCHEMA
        assert len(auth_ir.providers) == 1
        assert auth_ir.providers[0].id == "jwt_auth"
        assert len(auth_ir.roles) == 3
        assert "super_admin" in auth_ir.roles
        assert "tenant_admin" in auth_ir.roles
        assert "user" in auth_ir.roles
        assert len(auth_ir.policies) == 1

    def test_parse_invalid_tenant_mode(self):
        """Test parse() with invalid tenant_mode."""
        yaml_content = """
tenant_mode: invalid_mode
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(MidicoderError) as exc_info:
                AuthParser(temp_path).parse()
            
            assert exc_info.value.code == ErrorCode.CP02_TENANT_MODE_INVALID
        finally:
            temp_path.unlink()

    def test_parse_missing_parent_role(self):
        """Test parse() with missing parent role (KPI-030)."""
        yaml_content = """
tenant_mode: schema
authorization:
  roles:
    - id: child_role
      permissions: []
      parents: ["missing_parent"]
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(MidicoderError) as exc_info:
                AuthParser(temp_path).parse()
            
            assert exc_info.value.code == ErrorCode.CP04_ROLE_NOT_FOUND
        finally:
            temp_path.unlink()


# ============================================================================
# Test Utility Functions
# ============================================================================


class TestValidatePermissionFormat:
    """Tests cho validate_permission_format()."""

    def test_valid_permission_format(self):
        """Test valid permission formats."""
        assert validate_permission_format("user:create") is True
        assert validate_permission_format("order:read") is True
        assert validate_permission_format("product:delete") is True

    def test_valid_wildcard_format(self):
        """Test valid wildcard formats."""
        assert validate_permission_format("user:*") is True
        assert validate_permission_format("order:*") is True

    def test_invalid_permission_format(self):
        """Test invalid permission formats."""
        assert validate_permission_format("user:create:extra") is False
        assert validate_permission_format("user") is False
        assert validate_permission_format("invalid_format") is False


class TestParseAuthDSL:
    """Tests cho parse_auth_dsl() convenience function."""

    def test_parse_auth_dsl(self, temp_yaml_file):
        """Test parse_auth_dsl()."""
        auth_ir = parse_auth_dsl(temp_yaml_file)
        
        assert isinstance(auth_ir, AuthIR)
        assert len(auth_ir.providers) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])