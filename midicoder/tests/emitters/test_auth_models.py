"""
Tests cho CP03 Auth Models.

Unit tests cho:
- AuthProviderType enum
- JWTAuthConfig validation
- OAuth2AuthConfig validation
- AuthProvider validation
- SessionConfig validation
- Permission parsing
- AuthIR validation và utility methods

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
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
from midicoder.errors import ErrorCode, MidicoderError


# ============================================================================
# Test AuthProviderType
# ============================================================================


class TestAuthProviderType:
    """Tests cho AuthProviderType enum."""

    def test_jwt_value(self):
        """Test JWT provider type value."""
        assert AuthProviderType.JWT.value == "jwt"

    def test_oauth2_value(self):
        """Test OAuth2 provider type value."""
        assert AuthProviderType.OAUTH2.value == "oauth2"

    def test_from_string_jwt(self):
        """Test tạo từ string 'jwt'."""
        assert AuthProviderType("jwt") == AuthProviderType.JWT

    def test_from_string_oauth2(self):
        """Test tạo từ string 'oauth2'."""
        assert AuthProviderType("oauth2") == AuthProviderType.OAUTH2

    def test_from_string_invalid(self):
        """Test tạo từ string không hợp lệ."""
        with pytest.raises(ValueError):
            AuthProviderType("invalid")


# ============================================================================
# Test JWTAuthConfig
# ============================================================================


class TestJWTAuthConfig:
    """Tests cho JWTAuthConfig."""

    def test_default_values(self):
        """Test giá trị mặc định."""
        config = JWTAuthConfig()
        assert config.expire_minutes == 30
        assert config.refresh_expire_days == 7
        assert config.algorithm == "HS256"
        assert config.tenant_scoped is True

    def test_custom_values(self):
        """Test giá trị tùy chỉnh."""
        config = JWTAuthConfig(
            expire_minutes=60,
            refresh_expire_days=14,
            algorithm="RS256",
            tenant_scoped=False,
        )
        assert config.expire_minutes == 60
        assert config.refresh_expire_days == 14
        assert config.algorithm == "RS256"
        assert config.tenant_scoped is False

    def test_invalid_expire_minutes(self):
        """Test expire_minutes <= 0 raise error."""
        with pytest.raises(MidicoderError) as exc_info:
            JWTAuthConfig(expire_minutes=0)
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_invalid_expire_minutes_negative(self):
        """Test expire_minutes âm raise error."""
        with pytest.raises(MidicoderError) as exc_info:
            JWTAuthConfig(expire_minutes=-10)
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_invalid_refresh_expire_days(self):
        """Test refresh_expire_days <= 0 raise error."""
        with pytest.raises(MidicoderError) as exc_info:
            JWTAuthConfig(refresh_expire_days=0)
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_invalid_algorithm(self):
        """Test algorithm không hợp lệ raise error."""
        with pytest.raises(MidicoderError) as exc_info:
            JWTAuthConfig(algorithm="INVALID")
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_valid_algorithms(self):
        """Test các algorithm hợp lệ."""
        for alg in ("HS256", "RS256", "ES256", "HS384", "HS512"):
            config = JWTAuthConfig(algorithm=alg)
            assert config.algorithm == alg


# ============================================================================
# Test OAuth2AuthConfig
# ============================================================================


class TestOAuth2AuthConfig:
    """Tests cho OAuth2AuthConfig."""

    def test_valid_config(self):
        """Test config hợp lệ."""
        config = OAuth2AuthConfig(
            authorization_url="https://example.com/oauth/authorize",
            token_url="https://example.com/oauth/token",
            scopes=["read", "write"],
        )
        assert config.authorization_url == "https://example.com/oauth/authorize"
        assert config.token_url == "https://example.com/oauth/token"
        assert config.scopes == ["read", "write"]

    def test_missing_authorization_url(self):
        """Test thiếu authorization_url raise error."""
        with pytest.raises(MidicoderError) as exc_info:
            OAuth2AuthConfig(authorization_url="", token_url="https://example.com/token")
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_missing_token_url(self):
        """Test thiếu token_url raise error."""
        with pytest.raises(MidicoderError) as exc_info:
            OAuth2AuthConfig(authorization_url="https://example.com/auth", token_url="")
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID


# ============================================================================
# Test AuthProvider
# ============================================================================


class TestAuthProvider:
    """Tests cho AuthProvider."""

    def test_jwt_provider(self):
        """Test tạo JWT provider."""
        provider = AuthProvider(
            id="jwt_auth",
            provider_type=AuthProviderType.JWT,
            config=JWTAuthConfig(),
        )
        assert provider.id == "jwt_auth"
        assert provider.provider_type == AuthProviderType.JWT
        assert isinstance(provider.config, JWTAuthConfig)

    def test_oauth2_provider(self):
        """Test tạo OAuth2 provider."""
        provider = AuthProvider(
            id="google_oauth2",
            provider_type=AuthProviderType.OAUTH2,
            config=OAuth2AuthConfig(
                authorization_url="https://accounts.google.com/o/oauth2/auth",
                token_url="https://oauth2.googleapis.com/token",
            ),
        )
        assert provider.id == "google_oauth2"
        assert provider.provider_type == AuthProviderType.OAUTH2

    def test_empty_id_raises_error(self):
        """Test empty id raise error."""
        with pytest.raises(MidicoderError) as exc_info:
            AuthProvider(
                id="",
                provider_type=AuthProviderType.JWT,
                config=JWTAuthConfig(),
            )
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_jwt_provider_with_oauth2_config_raises_error(self):
        """Test JWT provider với OAuth2 config raise error."""
        with pytest.raises(MidicoderError) as exc_info:
            AuthProvider(
                id="invalid",
                provider_type=AuthProviderType.JWT,
                config=OAuth2AuthConfig(
                    authorization_url="https://example.com/auth",
                    token_url="https://example.com/token",
                ),
            )
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_oauth2_provider_with_jwt_config_raises_error(self):
        """Test OAuth2 provider với JWT config raise error."""
        with pytest.raises(MidicoderError) as exc_info:
            AuthProvider(
                id="invalid",
                provider_type=AuthProviderType.OAUTH2,
                config=JWTAuthConfig(),
            )
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID


# ============================================================================
# Test SessionConfig
# ============================================================================


class TestSessionConfig:
    """Tests cho SessionConfig."""

    def test_default_values(self):
        """Test giá trị mặc định."""
        config = SessionConfig()
        assert config.cookie_name == "session_id"
        assert config.max_age_minutes == 480
        assert config.secure is True
        assert config.http_only is True
        assert config.same_site == "lax"
        assert config.path == "/"

    def test_custom_values(self):
        """Test giá trị tùy chỉnh."""
        config = SessionConfig(
            cookie_name="auth_session",
            max_age_minutes=1440,
            same_site="strict",
        )
        assert config.cookie_name == "auth_session"
        assert config.max_age_minutes == 1440
        assert config.same_site == "strict"

    def test_invalid_max_age(self):
        """Test max_age_minutes <= 0 raise error."""
        with pytest.raises(MidicoderError) as exc_info:
            SessionConfig(max_age_minutes=0)
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_invalid_same_site(self):
        """Test same_site không hợp lệ raise error."""
        with pytest.raises(MidicoderError) as exc_info:
            SessionConfig(same_site="invalid")
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID


# ============================================================================
# Test Permission
# ============================================================================


class TestPermission:
    """Tests cho Permission."""

    def test_permission_with_resource_action(self):
        """Test permission format resource:action."""
        perm = Permission(id="user:create")
        assert perm.id == "user:create"
        assert perm.resource == "user"
        assert perm.action == "create"

    def test_permission_wildcard(self):
        """Test permission wildcard format."""
        perm = Permission(id="order:*")
        assert perm.resource == "order"
        assert perm.action == "*"

    def test_permission_with_explicit_resource_action(self):
        """Test permission với resource/action explicitly set."""
        perm = Permission(id="product:read", resource="product", action="read")
        assert perm.resource == "product"
        assert perm.action == "read"

    def test_permission_empty_id_raises_error(self):
        """Test empty id raise error."""
        with pytest.raises(MidicoderError) as exc_info:
            Permission(id="")
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_permission_invalid_format_raises_error(self):
        """Test format không có ':' raise error."""
        with pytest.raises(MidicoderError) as exc_info:
            Permission(id="invalid_format")
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_permission_with_description(self):
        """Test permission với description."""
        perm = Permission(id="user:delete", description="Xóa user")
        assert perm.description == "Xóa user"


# ============================================================================
# Test AuthIR
# ============================================================================


class TestAuthIR:
    """Tests cho AuthIR."""

    def test_default_values(self):
        """Test giá trị mặc định."""
        auth_ir = AuthIR()
        assert auth_ir.providers == []
        assert isinstance(auth_ir.session, SessionConfig)
        assert auth_ir.permissions == []

    def test_validate_no_providers_raises_error(self):
        """Test validate không có providers raise error."""
        auth_ir = AuthIR()
        with pytest.raises(MidicoderError) as exc_info:
            auth_ir.validate()
        assert exc_info.value.code == ErrorCode.CP03_AUTH_PROVIDER_NOT_FOUND

    def test_validate_with_jwt_provider(self):
        """Test validate với JWT provider pass."""
        auth_ir = AuthIR(
            providers=[
                AuthProvider(
                    id="jwt",
                    provider_type=AuthProviderType.JWT,
                    config=JWTAuthConfig(),
                )
            ]
        )
        auth_ir.validate()  # Không raise

    def test_get_jwt_provider(self):
        """Test lấy JWT provider."""
        auth_ir = AuthIR(
            providers=[
                AuthProvider(
                    id="jwt",
                    provider_type=AuthProviderType.JWT,
                    config=JWTAuthConfig(expire_minutes=60),
                ),
                AuthProvider(
                    id="google",
                    provider_type=AuthProviderType.OAUTH2,
                    config=OAuth2AuthConfig(
                        authorization_url="https://example.com/auth",
                        token_url="https://example.com/token",
                    ),
                ),
            ]
        )
        jwt_provider = auth_ir.get_jwt_provider()
        assert jwt_provider is not None
        assert jwt_provider.id == "jwt"
        assert jwt_provider.config.expire_minutes == 60

    def test_get_jwt_provider_none(self):
        """Test lấy JWT provider khi không có."""
        auth_ir = AuthIR(
            providers=[
                AuthProvider(
                    id="google",
                    provider_type=AuthProviderType.OAUTH2,
                    config=OAuth2AuthConfig(
                        authorization_url="https://example.com/auth",
                        token_url="https://example.com/token",
                    ),
                ),
            ]
        )
        assert auth_ir.get_jwt_provider() is None

    def test_get_oauth2_providers(self):
        """Test lấy OAuth2 providers."""
        auth_ir = AuthIR(
            providers=[
                AuthProvider(
                    id="jwt",
                    provider_type=AuthProviderType.JWT,
                    config=JWTAuthConfig(),
                ),
                AuthProvider(
                    id="google",
                    provider_type=AuthProviderType.OAUTH2,
                    config=OAuth2AuthConfig(
                        authorization_url="https://example.com/auth",
                        token_url="https://example.com/token",
                    ),
                ),
                AuthProvider(
                    id="github",
                    provider_type=AuthProviderType.OAUTH2,
                    config=OAuth2AuthConfig(
                        authorization_url="https://github.com/login/oauth/authorize",
                        token_url="https://github.com/login/oauth/access_token",
                    ),
                ),
            ]
        )
        oauth2 = auth_ir.get_oauth2_providers()
        assert len(oauth2) == 2
        assert {p.id for p in oauth2} == {"google", "github"}

    def test_get_all_permission_ids(self):
        """Test lấy tất cả permission IDs."""
        auth_ir = AuthIR(
            providers=[
                AuthProvider(
                    id="jwt",
                    provider_type=AuthProviderType.JWT,
                    config=JWTAuthConfig(),
                ),
            ],
            permissions=[
                Permission(id="user:create"),
                Permission(id="user:read"),
                Permission(id="order:*"),
            ],
        )
        perms = auth_ir.get_all_permission_ids()
        assert perms == {"user:create", "user:read", "order:*"}

    def test_full_auth_ir(self):
        """Test AuthIR hoàn chỉnh với providers, session, permissions."""
        auth_ir = AuthIR(
            providers=[
                AuthProvider(
                    id="jwt",
                    provider_type=AuthProviderType.JWT,
                    config=JWTAuthConfig(expire_minutes=30),
                ),
            ],
            session=SessionConfig(
                cookie_name="session",
                max_age_minutes=480,
                secure=True,
            ),
            permissions=[
                Permission(id="user:create", description="Tạo user mới"),
                Permission(id="user:read", description="Đọc thông tin user"),
                Permission(id="order:*", description="Tất cả actions trên order"),
            ],
        )
        auth_ir.validate()
        assert len(auth_ir.providers) == 1
        assert len(auth_ir.permissions) == 3
        assert auth_ir.session.cookie_name == "session"


# ============================================================================
# Test AuthValidationResult
# ============================================================================


class TestAuthValidationResult:
    """Tests cho AuthValidationResult."""

    def test_valid_result(self):
        """Test valid result."""
        result = AuthValidationResult(valid=True)
        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_invalid_result_with_errors(self):
        """Test invalid result với errors."""
        result = AuthValidationResult(
            valid=False,
            errors=["Lỗi 1", "Lỗi 2"],
            warnings=["Cảnh báo 1"],
        )
        assert result.valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])