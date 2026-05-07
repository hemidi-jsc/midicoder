"""
Tests cho CP03 Auth Parser.

Unit tests cho:
- AuthParser class (parse YAML → AuthIR)
- parse_auth_dsl convenience function
- validate_permission_format utility

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
import tempfile
from pathlib import Path

from midicoder.emitters.core.auth.parser import (
    AuthParser,
    parse_auth_dsl,
    validate_permission_format,
)
from midicoder.emitters.core.auth.models import (
    AuthIR,
    AuthProviderType,
)
from midicoder.errors import ErrorCode, MidicoderError


# ============================================================================
# Test AuthParser
# ============================================================================


class TestAuthParser:
    """Tests cho AuthParser."""

    def test_parser_file_not_found(self):
        """Test parser với file không tồn tại raise error."""
        with pytest.raises(MidicoderError) as exc_info:
            AuthParser("/nonexistent/path/auth.yaml")
        assert exc_info.value.code == ErrorCode.DSL_FILE_NOT_FOUND

    def test_parse_minimal_yaml(self):
        """Test parse YAML tối thiểu (không có providers → default JWT)."""
        yaml_content = "authentication: {}\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write(yaml_content)
            path = Path(f.name)
        try:
            parser = AuthParser(path)
            auth_ir = parser.parse()
        finally:
            path.unlink()

        assert isinstance(auth_ir, AuthIR)
        assert len(auth_ir.providers) == 1
        assert auth_ir.providers[0].id == "default_jwt"
        assert auth_ir.providers[0].provider_type == AuthProviderType.JWT

    def test_parse_full_yaml(self):
        """Test parse YAML đầy đủ với JWT, OAuth2, session, permissions."""
        yaml_content = """
authentication:
  providers:
    - id: jwt_auth
      type: jwt
      config:
        expire_minutes: 60
        refresh_expire_days: 14
        algorithm: RS256
        tenant_scoped: true
    - id: google_oauth
      type: oauth2
      config:
        authorization_url: https://accounts.google.com/o/oauth2/auth
        token_url: https://oauth2.googleapis.com/token
        scopes:
          - email
          - profile
  session:
    cookie_name: my_session
    max_age_minutes: 1440
    secure: true
    http_only: true
    same_site: strict
authorization:
  permissions:
    - id: "user:create"
      description: "Tao user"
    - "order:read"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write(yaml_content)
            path = Path(f.name)
        try:
            parser = AuthParser(path)
            auth_ir = parser.parse()
        finally:
            path.unlink()

        assert isinstance(auth_ir, AuthIR)
        assert len(auth_ir.providers) == 2

        # Check JWT provider
        jwt = auth_ir.providers[0]
        assert jwt.id == "jwt_auth"
        assert jwt.provider_type == AuthProviderType.JWT
        assert jwt.config.expire_minutes == 60
        assert jwt.config.algorithm == "RS256"

        # Check OAuth2 provider
        oauth = auth_ir.providers[1]
        assert oauth.id == "google_oauth"
        assert oauth.provider_type == AuthProviderType.OAUTH2
        assert oauth.config.scopes == ["email", "profile"]

        # Check session
        assert auth_ir.session.cookie_name == "my_session"
        assert auth_ir.session.max_age_minutes == 1440
        assert auth_ir.session.same_site == "strict"

        # Check permissions
        assert len(auth_ir.permissions) == 2
        assert auth_ir.permissions[0].id == "user:create"
        assert auth_ir.permissions[1].id == "order:read"

    def test_parse_empty_yaml_raises_error(self):
        """Test parse file YAML rỗng raise error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write("")
            path = Path(f.name)
        try:
            with pytest.raises(MidicoderError) as exc_info:
                AuthParser(path).parse()
            assert exc_info.value.code == ErrorCode.DSL_YAML_PARSE_ERROR
        finally:
            path.unlink()

    def test_parse_invalid_provider_type(self):
        """Test parse provider type không hợp lệ raise error."""
        yaml_content = """
authentication:
  providers:
    - id: bad_provider
      type: invalid_type
      config: {}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write(yaml_content)
            path = Path(f.name)
        try:
            with pytest.raises(MidicoderError) as exc_info:
                AuthParser(path).parse()
            assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID
        finally:
            path.unlink()

    def test_parse_oauth2_missing_url(self):
        """Test parse OAuth2 thiếu authorization_url raise error."""
        yaml_content = """
authentication:
  providers:
    - id: oauth
      type: oauth2
      config:
        token_url: https://example.com/token
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write(yaml_content)
            path = Path(f.name)
        try:
            with pytest.raises(MidicoderError) as exc_info:
                AuthParser(path).parse()
            assert exc_info.value.code == ErrorCode.DSL_MISSING_REQUIRED_FIELD
        finally:
            path.unlink()

    def test_parse_with_string_permissions(self):
        """Test parse permissions ở format string đơn giản."""
        yaml_content = """
authentication:
  providers:
    - id: jwt
      type: jwt
authorization:
  permissions:
    - "user:create"
    - "order:*"
    - "product:read"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write(yaml_content)
            path = Path(f.name)
        try:
            parser = AuthParser(path)
            auth_ir = parser.parse()
        finally:
            path.unlink()

        assert len(auth_ir.permissions) == 3
        assert auth_ir.permissions[0].resource == "user"
        assert auth_ir.permissions[0].action == "create"
        assert auth_ir.permissions[1].action == "*"

    def test_parse_yaml_not_mapping(self):
        """Test parse YAML là list (không phải mapping) raise error."""
        yaml_content = "- item1\n- item2\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write(yaml_content)
            path = Path(f.name)
        try:
            with pytest.raises(MidicoderError) as exc_info:
                AuthParser(path).parse()
            assert exc_info.value.code == ErrorCode.DSL_YAML_PARSE_ERROR
        finally:
            path.unlink()


# ============================================================================
# Test parse_auth_dsl Convenience Function
# ============================================================================


class TestParseAuthDSL:
    """Tests cho parse_auth_dsl()."""

    def test_parse_auth_dsl_success(self):
        """Test parse_auth_dsl với YAML hợp lệ."""
        yaml_content = """
authentication:
  providers:
    - id: jwt
      type: jwt
      config:
        expire_minutes: 45
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write(yaml_content)
            path = Path(f.name)
        try:
            auth_ir = parse_auth_dsl(path)
        finally:
            path.unlink()

        assert isinstance(auth_ir, AuthIR)
        assert auth_ir.providers[0].config.expire_minutes == 45

    def test_parse_auth_dsl_file_not_found(self):
        """Test parse_auth_dsl với file không tồn tại."""
        with pytest.raises(MidicoderError) as exc_info:
            parse_auth_dsl("/nonexistent/file.yaml")
        assert exc_info.value.code == ErrorCode.DSL_FILE_NOT_FOUND


# ============================================================================
# Test validate_permission_format
# ============================================================================


class TestValidatePermissionFormat:
    """Tests cho validate_permission_format()."""

    def test_valid_resource_action(self):
        """Test format 'resource:action' hợp lệ."""
        assert validate_permission_format("user:create") is True
        assert validate_permission_format("order:read") is True
        assert validate_permission_format("product:delete") is True

    def test_valid_wildcard(self):
        """Test format wildcard hợp lệ."""
        assert validate_permission_format("user:*") is True
        assert validate_permission_format("order:*") is True

    def test_invalid_no_colon(self):
        """Test format không có ':' không hợp lệ."""
        assert validate_permission_format("invalid") is False

    def test_invalid_extra_colon(self):
        """Test format có nhiều ':' không hợp lệ."""
        assert validate_permission_format("user:create:extra") is False

    def test_empty_permission(self):
        """Test permission rỗng không hợp lệ."""
        assert validate_permission_format("") is False

    def test_uppercase_invalid(self):
        """Test uppercase characters không hợp lệ."""
        assert validate_permission_format("User:Create") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])