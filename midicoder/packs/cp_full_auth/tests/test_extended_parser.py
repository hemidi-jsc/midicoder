"""
CP03: Extended Parser Tests — SAML, LDAP, mTLS, Session parsing.

Tests for parser methods added in hardening (Phase 1):
- SAML 2.0 config parsing
- LDAP config parsing
- mTLS config parsing
- Stateful session config parsing
- Multi-provider YAML parsing
- Error paths for each provider type
"""

import os
import tempfile

import pytest
import yaml

from midicoder.packs.cp_full_auth.parser import (
    AuthParser,
    parse_auth_dsl,
    validate_permission_format,
)
from midicoder.packs.cp_full_auth.models import (
    AuthProviderType,
    LDAPReferralMode,
    MTLSVerificationMode,
    NameIDFormat,
    SessionStoreType,
)
from midicoder.errors import ErrorCode, MidicoderError


def _write_temp_yaml(data: dict) -> str:
    """Helper: write dict to temp YAML file, return path."""
    fd, path = tempfile.mkstemp(suffix=".yml")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        yaml.dump(data, f)
    return path


# ============================================================================
# SAML Parsing
# ============================================================================


class TestParseSAML:
    """Test SAML 2.0 provider parsing."""

    def test_saml_basic_parse(self):
        yml = {
            "authentication": {
                "providers": [
                    {
                        "id": "okta_saml",
                        "type": "saml",
                        "config": {
                            "idp_metadata_url": "https://okta.example.com/saml/metadata",
                            "sp_entity_id": "https://app.example.com/saml",
                        },
                    }
                ]
            }
        }
        path = _write_temp_yaml(yml)
        try:
            parser = AuthParser(path)
            ir = parser.parse()
        finally:
            os.unlink(path)

        assert len(ir.providers) == 1
        assert ir.providers[0].id == "okta_saml"
        assert ir.providers[0].provider_type == AuthProviderType.SAML
        cfg = ir.providers[0].config
        assert cfg.idp_metadata_url == "https://okta.example.com/saml/metadata"
        assert cfg.sp_entity_id == "https://app.example.com/saml"
        assert cfg.name_id_format == NameIDFormat.PERSISTENT
        assert cfg.want_response_signed is True
        assert cfg.want_assertion_signed is True

    def test_saml_with_metadata_xml(self):
        yml = {
            "authentication": {
                "providers": [
                    {
                        "id": "adfs_saml",
                        "type": "saml",
                        "config": {
                            "idp_metadata_xml": "<md:EntityDescriptor>...</md:EntityDescriptor>",
                            "sp_entity_id": "https://app.example.com/adfs",
                        },
                    }
                ]
            }
        }
        path = _write_temp_yaml(yml)
        try:
            parser = AuthParser(path)
            ir = parser.parse()
        finally:
            os.unlink(path)

        cfg = ir.providers[0].config
        assert cfg.idp_metadata_xml == "<md:EntityDescriptor>...</md:EntityDescriptor>"
        assert cfg.idp_metadata_url == ""

    def test_saml_full_config(self):
        yml = {
            "authentication": {
                "providers": [
                    {
                        "id": "full_saml",
                        "type": "saml",
                        "config": {
                            "idp_metadata_url": "https://idp.example.com/metadata",
                            "sp_entity_id": "https://sp.example.com",
                            "sp_assertion_consumer_url": "https://sp.example.com/acs",
                            "name_id_format": "email",
                            "want_authn_requests_signed": True,
                            "want_response_signed": False,
                            "want_assertion_signed": False,
                            "cert": "-----BEGIN CERTIFICATE-----\n...",
                            "key": "-----BEGIN PRIVATE KEY-----\n...",
                        },
                    }
                ]
            }
        }
        path = _write_temp_yaml(yml)
        try:
            parser = AuthParser(path)
            ir = parser.parse()
        finally:
            os.unlink(path)

        cfg = ir.providers[0].config
        assert cfg.name_id_format == NameIDFormat.EMAIL
        assert cfg.want_authn_requests_signed is True
        assert cfg.want_response_signed is False
        assert cfg.cert == "-----BEGIN CERTIFICATE-----\n..."

    def test_saml_invalid_name_id_format(self):
        yml = {
            "authentication": {
                "providers": [
                    {
                        "id": "bad_saml",
                        "type": "saml",
                        "config": {
                            "idp_metadata_url": "https://x.com/m",
                            "sp_entity_id": "https://x.com",
                            "name_id_format": "invalid_format",
                        },
                    }
                ]
            }
        }
        path = _write_temp_yaml(yml)
        try:
            parser = AuthParser(path)
            with pytest.raises(MidicoderError) as exc_info:
                parser.parse()
            assert exc_info.value.code == ErrorCode.DSL_MISSING_REQUIRED_FIELD
        finally:
            os.unlink(path)


# ============================================================================
# LDAP Parsing
# ============================================================================


class TestParseLDAP:
    """Test LDAP provider parsing."""

    def test_ldap_basic_parse(self):
        yml = {
            "authentication": {
                "providers": [
                    {
                        "id": "ad_ldap",
                        "type": "ldap",
                        "config": {
                            "server": "ldaps://dc01.example.com:636",
                            "base_dn": "dc=example,dc=com",
                        },
                    }
                ]
            }
        }
        path = _write_temp_yaml(yml)
        try:
            parser = AuthParser(path)
            ir = parser.parse()
        finally:
            os.unlink(path)

        assert len(ir.providers) == 1
        assert ir.providers[0].provider_type == AuthProviderType.LDAP
        cfg = ir.providers[0].config
        assert cfg.server == "ldaps://dc01.example.com:636"
        assert cfg.base_dn == "dc=example,dc=com"
        assert cfg.use_ssl is False  # default (even though server is ldaps://)
        assert cfg.user_search_filter == "(sAMAccountName={login})"
        assert cfg.referral_mode == LDAPReferralMode.IGNORE

    def test_ldap_full_config(self):
        yml = {
            "authentication": {
                "providers": [
                    {
                        "id": "full_ldap",
                        "type": "ldap",
                        "config": {
                            "server": "ldaps://ad.example.com:636",
                            "base_dn": "dc=example,dc=com",
                            "use_ssl": True,
                            "user_search_base": "ou=users,dc=example,dc=com",
                            "group_search_base": "ou=groups,dc=example,dc=com",
                            "user_search_filter": "(sAMAccountName={login})",
                            "bind_dn": "cn=svc_auth,ou=service,dc=example,dc=com",
                            "bind_password": "secret123",
                            "referral_mode": "follow",
                            "attributes": ["cn", "mail", "displayName", "memberOf"],
                        },
                    }
                ]
            }
        }
        path = _write_temp_yaml(yml)
        try:
            parser = AuthParser(path)
            ir = parser.parse()
        finally:
            os.unlink(path)

        cfg = ir.providers[0].config
        assert cfg.use_ssl is True
        assert cfg.referral_mode == LDAPReferralMode.FOLLOW
        assert "displayName" in cfg.attributes
        assert cfg.bind_dn == "cn=svc_auth,ou=service,dc=example,dc=com"

    def test_ldap_invalid_referral_mode(self):
        yml = {
            "authentication": {
                "providers": [
                    {
                        "id": "bad_ldap",
                        "type": "ldap",
                        "config": {
                            "server": "ldap://x.com",
                            "base_dn": "dc=x,dc=com",
                            "referral_mode": "invalid_mode",
                        },
                    }
                ]
            }
        }
        path = _write_temp_yaml(yml)
        try:
            parser = AuthParser(path)
            with pytest.raises(MidicoderError) as exc_info:
                parser.parse()
            assert exc_info.value.code == ErrorCode.DSL_MISSING_REQUIRED_FIELD
        finally:
            os.unlink(path)


# ============================================================================
# mTLS Parsing
# ============================================================================


class TestParseMTLS:
    """Test mTLS provider parsing."""

    def test_mtls_basic_parse(self):
        yml = {
            "authentication": {
                "providers": [
                    {
                        "id": "service_mtls",
                        "type": "mtls",
                        "config": {
                            "ca_cert_path": "/etc/ssl/ca.pem",
                        },
                    }
                ]
            }
        }
        path = _write_temp_yaml(yml)
        try:
            parser = AuthParser(path)
            ir = parser.parse()
        finally:
            os.unlink(path)

        assert ir.providers[0].provider_type == AuthProviderType.MTLS
        cfg = ir.providers[0].config
        assert cfg.ca_cert_path == "/etc/ssl/ca.pem"
        assert cfg.verification_mode == MTLSVerificationMode.REQUIRED
        assert cfg.allowed_cn_patterns == []

    def test_mtls_full_config(self):
        yml = {
            "authentication": {
                "providers": [
                    {
                        "id": "full_mtls",
                        "type": "mtls",
                        "config": {
                            "ca_cert_path": "/etc/ssl/ca.pem",
                            "server_cert_path": "/etc/ssl/server.pem",
                            "server_key_path": "/etc/ssl/server.key",
                            "verification_mode": "optional",
                            "allowed_cn_patterns": ["service-*", "api-*"],
                            "allowed_ou_patterns": ["Engineering"],
                            "allowed_o_patterns": ["Example Corp"],
                        },
                    }
                ]
            }
        }
        path = _write_temp_yaml(yml)
        try:
            parser = AuthParser(path)
            ir = parser.parse()
        finally:
            os.unlink(path)

        cfg = ir.providers[0].config
        assert cfg.verification_mode == MTLSVerificationMode.OPTIONAL
        assert cfg.allowed_cn_patterns == ["service-*", "api-*"]
        assert cfg.server_cert_path == "/etc/ssl/server.pem"

    def test_mtls_invalid_verification_mode(self):
        yml = {
            "authentication": {
                "providers": [
                    {
                        "id": "bad_mtls",
                        "type": "mtls",
                        "config": {
                            "ca_cert_path": "/etc/ssl/ca.pem",
                            "verification_mode": "invalid_mode",
                        },
                    }
                ]
            }
        }
        path = _write_temp_yaml(yml)
        try:
            parser = AuthParser(path)
            with pytest.raises(MidicoderError) as exc_info:
                parser.parse()
            assert exc_info.value.code == ErrorCode.DSL_MISSING_REQUIRED_FIELD
        finally:
            os.unlink(path)


# ============================================================================
# Stateful Session Parsing
# ============================================================================


class TestParseSession:
    """Test stateful session provider parsing."""

    def test_session_redis_parse(self):
        yml = {
            "authentication": {
                "providers": [
                    {
                        "id": "redis_session",
                        "type": "session",
                        "config": {
                            "store_type": "redis",
                            "store_connection_string": "redis://localhost:6379/0",
                        },
                    }
                ]
            }
        }
        path = _write_temp_yaml(yml)
        try:
            parser = AuthParser(path)
            ir = parser.parse()
        finally:
            os.unlink(path)

        assert ir.providers[0].provider_type == AuthProviderType.SESSION
        cfg = ir.providers[0].config
        assert cfg.store_type == SessionStoreType.REDIS
        assert cfg.store_connection_string == "redis://localhost:6379/0"
        assert cfg.ttl_seconds == 86400

    def test_session_full_config(self):
        yml = {
            "authentication": {
                "providers": [
                    {
                        "id": "db_session",
                        "type": "session",
                        "config": {
                            "store_type": "database",
                            "store_connection_string": "postgresql://user:pass@localhost/db",
                            "cookie_name": "sid",
                            "cookie_secure": True,
                            "cookie_http_only": True,
                            "cookie_samesite": "strict",
                            "ttl_seconds": 43200,
                            "idle_timeout_seconds": 1800,
                        },
                    }
                ]
            }
        }
        path = _write_temp_yaml(yml)
        try:
            parser = AuthParser(path)
            ir = parser.parse()
        finally:
            os.unlink(path)

        cfg = ir.providers[0].config
        assert cfg.store_type == SessionStoreType.DATABASE
        assert cfg.cookie_name == "sid"
        assert cfg.ttl_seconds == 43200
        assert cfg.idle_timeout_seconds == 1800

    def test_session_memcached(self):
        yml = {
            "authentication": {
                "providers": [
                    {
                        "id": "mc_session",
                        "type": "session",
                        "config": {
                            "store_type": "memcached",
                            "store_connection_string": "memcached://localhost:11211",
                        },
                    }
                ]
            }
        }
        path = _write_temp_yaml(yml)
        try:
            parser = AuthParser(path)
            ir = parser.parse()
        finally:
            os.unlink(path)

        assert ir.providers[0].config.store_type == SessionStoreType.MEMCACHED

    def test_session_file_store(self):
        yml = {
            "authentication": {
                "providers": [
                    {
                        "id": "file_session",
                        "type": "session",
                        "config": {"store_type": "file"},
                    }
                ]
            }
        }
        path = _write_temp_yaml(yml)
        try:
            parser = AuthParser(path)
            ir = parser.parse()
        finally:
            os.unlink(path)

        assert ir.providers[0].config.store_type == SessionStoreType.FILE

    def test_session_invalid_store_type(self):
        yml = {
            "authentication": {
                "providers": [
                    {
                        "id": "bad_session",
                        "type": "session",
                        "config": {"store_type": "invalid_store"},
                    }
                ]
            }
        }
        path = _write_temp_yaml(yml)
        try:
            parser = AuthParser(path)
            with pytest.raises(MidicoderError) as exc_info:
                parser.parse()
            assert exc_info.value.code == ErrorCode.DSL_MISSING_REQUIRED_FIELD
        finally:
            os.unlink(path)


# ============================================================================
# Multi-Provider Parsing
# ============================================================================


class TestMultiProviderParse:
    """Test parsing multiple auth providers together."""

    def test_multi_provider_jwt_and_saml(self):
        yml = {
            "authentication": {
                "providers": [
                    {
                        "id": "internal_jwt",
                        "type": "jwt",
                        "config": {"expire_minutes": 15, "algorithm": "RS256"},
                    },
                    {
                        "id": "enterprise_saml",
                        "type": "saml",
                        "config": {
                            "idp_metadata_url": "https://idp.corp.com/metadata",
                            "sp_entity_id": "https://app.corp.com/saml",
                        },
                    },
                ]
            },
            "authorization": {
                "permissions": ["user:*", "order:read", "order:create"],
            },
        }
        path = _write_temp_yaml(yml)
        try:
            parser = AuthParser(path)
            ir = parser.parse()
        finally:
            os.unlink(path)

        assert len(ir.providers) == 2
        assert ir.providers[0].provider_type == AuthProviderType.JWT
        assert ir.providers[1].provider_type == AuthProviderType.SAML
        assert ir.providers[0].config.expire_minutes == 15
        assert ir.providers[0].config.algorithm == "RS256"
        assert len(ir.permissions) == 3

    def test_all_provider_types(self):
        yml = {
            "authentication": {
                "providers": [
                    {"id": "jwt", "type": "jwt", "config": {}},
                    {"id": "google", "type": "oauth2", "config": {"authorization_url": "https://x.com/auth", "token_url": "https://x.com/token"}},
                    {"id": "okta", "type": "saml", "config": {"idp_metadata_url": "https://x.com/m", "sp_entity_id": "https://s.com"}},
                    {"id": "ad", "type": "ldap", "config": {"server": "ldaps://x.com", "base_dn": "dc=x,dc=com"}},
                    {"id": "service", "type": "mtls", "config": {"ca_cert_path": "/ca.pem"}},
                    {"id": "session", "type": "session", "config": {}},
                ]
            }
        }
        path = _write_temp_yaml(yml)
        try:
            parser = AuthParser(path)
            ir = parser.parse()
        finally:
            os.unlink(path)

        assert len(ir.providers) == 6
        types = [p.provider_type for p in ir.providers]
        assert AuthProviderType.JWT in types
        assert AuthProviderType.OAUTH2 in types
        assert AuthProviderType.SAML in types
        assert AuthProviderType.LDAP in types
        assert AuthProviderType.MTLS in types
        assert AuthProviderType.SESSION in types
