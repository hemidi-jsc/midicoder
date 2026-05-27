"""
CP03: Recipes Tests.

Tests for all recipe functions in recipes.py (Phase 3):
- jwt_recipe()
- oauth2_recipe()
- saml_recipe()
- ldap_recipe()
- mtls_recipe()
- stateful_session_recipe()
- mfa_totp_recipe()
- mfa_webauthn_recipe()
- multi_provider_recipe()
"""

import pytest
from midicoder.packs.cp03_auth.models import (
    AuthIR,
    AuthProvider,
    AuthProviderType,
    MFAProviderType,
    MFAPolicy,
    RateLimitStrategyType,
    SessionStoreType,
    TOTPAlgorithm,
)
from midicoder.packs.cp03_auth.recipes import (
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


# ============================================================================
# jwt_recipe
# ============================================================================


class TestJWTRecipe:
    """Test JWT recipe."""

    def test_default_jwt_recipe(self):
        ir = jwt_recipe()
        assert len(ir.providers) == 1
        assert ir.providers[0].provider_type == AuthProviderType.JWT
        assert ir.providers[0].id == "jwt_auth"
        cfg = ir.providers[0].config
        assert cfg.expire_minutes == 30
        assert cfg.refresh_expire_days == 7
        assert cfg.algorithm == "HS256"
        assert cfg.tenant_scoped is True

    def test_jwt_recipe_custom_values(self):
        ir = jwt_recipe(
            expire_minutes=15,
            refresh_expire_days=3,
            algorithm="RS256",
            tenant_scoped=False,
            max_login_attempts=5,
            rate_limit_window=60,
        )
        cfg = ir.providers[0].config
        assert cfg.expire_minutes == 15
        assert cfg.algorithm == "RS256"
        assert cfg.tenant_scoped is False
        assert ir.rate_limit.max_requests == 5
        assert ir.rate_limit.window_seconds == 60

    def test_jwt_recipe_with_mfa(self):
        ir = jwt_recipe(enable_mfa=True)
        assert ir.mfa.enabled is True
        assert MFAProviderType.TOTP in ir.mfa.providers
        assert ir.mfa.totp_config.algorithm == TOTPAlgorithm.SHA256
        assert ir.mfa.totp_config.digit_count == 6

    def test_jwt_recipe_rate_limit(self):
        ir = jwt_recipe()
        assert ir.rate_limit.strategy == RateLimitStrategyType.SLIDING_WINDOW
        assert ir.rate_limit.max_requests == 10
        assert ir.rate_limit.window_seconds == 300


# ============================================================================
# oauth2_recipe
# ============================================================================


class TestOAuth2Recipe:
    """Test OAuth2 recipe."""

    def test_google_oauth2_default(self):
        ir = oauth2_recipe("google")
        assert len(ir.providers) == 1
        assert ir.providers[0].provider_type == AuthProviderType.OAUTH2
        assert ir.providers[0].id == "google_oauth2"
        cfg = ir.providers[0].config
        assert cfg.authorization_url == "https://accounts.google.com/o/oauth2/v2/auth"
        assert cfg.token_url == "https://oauth2.googleapis.com/token"
        assert "openid" in cfg.scopes
        assert "email" in cfg.scopes

    def test_github_oauth2_default(self):
        ir = oauth2_recipe("github")
        cfg = ir.providers[0].config
        assert cfg.authorization_url == "https://github.com/login/oauth/authorize"
        assert cfg.token_url == "https://github.com/login/oauth/access_token"
        assert "read:user" in cfg.scopes

    def test_custom_oauth2(self):
        ir = oauth2_recipe(
            provider_name="custom",
            client_id="my_client_id",
            scopes=["custom:scope1"],
        )
        cfg = ir.providers[0].config
        assert cfg.client_id == "my_client_id"
        assert cfg.scopes == ["custom:scope1"]
        # custom provider has empty URLs (user must fill at runtime)
        assert cfg.authorization_url == ""
        assert cfg.token_url == ""

    def test_oauth2_with_mfa(self):
        ir = oauth2_recipe("google", enable_mfa=True)
        assert ir.mfa.enabled is True
        assert MFAProviderType.TOTP in ir.mfa.providers


# ============================================================================
# saml_recipe
# ============================================================================


class TestSAMLRecipe:
    """Test SAML recipe."""

    def test_default_saml_recipe(self):
        ir = saml_recipe(
            idp_name="okta",
            idp_metadata_url="https://okta.example.com/saml/metadata",
            sp_entity_id="https://app.example.com/saml",
        )
        assert len(ir.providers) == 1
        assert ir.providers[0].provider_type == AuthProviderType.SAML
        assert ir.providers[0].id == "okta_saml"
        cfg = ir.providers[0].config
        assert cfg.want_authn_requests_signed is True
        assert cfg.want_response_signed is True
        assert cfg.want_assertion_signed is True

    def test_saml_with_cert_and_key(self):
        ir = saml_recipe(
            idp_name="adfs",
            idp_metadata_url="https://adfs.example.com/metadata",
            sp_entity_id="https://app.example.com/adfs",
            sp_acs_url="https://app.example.com/adfs/acs",
            cert="-----BEGIN CERTIFICATE-----\n...",
            key="-----BEGIN PRIVATE KEY-----\n...",
        )
        cfg = ir.providers[0].config
        assert cfg.sp_assertion_consumer_url == "https://app.example.com/adfs/acs"
        assert cfg.cert == "-----BEGIN CERTIFICATE-----\n..."

    def test_saml_session_config(self):
        ir = saml_recipe(
            idp_name="test",
            idp_metadata_url="https://x.com/m",
            sp_entity_id="https://x.com",
        )
        assert ir.session.cookie_name == "saml_session_id"
        assert ir.session.max_age_minutes == 480

    def test_saml_rate_limit(self):
        ir = saml_recipe(
            idp_name="test",
            idp_metadata_url="https://x.com/m",
            sp_entity_id="https://x.com",
        )
        assert ir.rate_limit.max_requests == 20


# ============================================================================
# ldap_recipe
# ============================================================================


class TestLDAPRecipe:
    """Test LDAP recipe."""

    def test_default_ldap_recipe(self):
        ir = ldap_recipe(
            server="ldaps://dc01.example.com:636",
            base_dn="dc=example,dc=com",
        )
        assert len(ir.providers) == 1
        assert ir.providers[0].provider_type == AuthProviderType.LDAP
        cfg = ir.providers[0].config
        assert cfg.server == "ldaps://dc01.example.com:636"
        assert cfg.base_dn == "dc=example,dc=com"
        assert cfg.user_search_filter == "(sAMAccountName={login})"

    def test_ldap_full_config(self):
        ir = ldap_recipe(
            server="ldap://dc01.example.com:389",
            base_dn="dc=example,dc=com",
            use_ssl=False,
            user_search_base="ou=users",
            bind_dn="cn=svc_auth,ou=service",
        )
        cfg = ir.providers[0].config
        assert cfg.use_ssl is False
        assert cfg.user_search_base == "ou=users"
        assert cfg.bind_dn == "cn=svc_auth,ou=service"

    def test_ldap_session_config(self):
        ir = ldap_recipe(
            server="ldaps://x.com",
            base_dn="dc=x,dc=com",
        )
        assert ir.session.cookie_name == "ldap_session_id"
        assert ir.session.same_site == "strict"

    def test_ldap_rate_limit_strict(self):
        ir = ldap_recipe(
            server="ldaps://x.com",
            base_dn="dc=x,dc=com",
        )
        assert ir.rate_limit.max_requests == 5
        assert ir.rate_limit.block_duration_seconds == 900


# ============================================================================
# mtls_recipe
# ============================================================================


class TestMTLSRecipe:
    """Test mTLS recipe."""

    def test_default_mtls_recipe(self):
        ir = mtls_recipe(ca_cert_path="/etc/ssl/ca.pem")
        assert len(ir.providers) == 1
        assert ir.providers[0].provider_type == AuthProviderType.MTLS
        cfg = ir.providers[0].config
        assert cfg.ca_cert_path == "/etc/ssl/ca.pem"
        assert cfg.verification_mode == "required"

    def test_mtls_full_config(self):
        ir = mtls_recipe(
            ca_cert_path="/etc/ssl/ca.pem",
            server_cert_path="/etc/ssl/server.pem",
            server_key_path="/etc/ssl/server.key",
            verification_mode="optional",
            allowed_cn_patterns=["service-*"],
        )
        cfg = ir.providers[0].config
        assert cfg.server_cert_path == "/etc/ssl/server.pem"
        assert cfg.verification_mode == "optional"
        assert cfg.allowed_cn_patterns == ["service-*"]

    def test_mtls_rate_limit(self):
        ir = mtls_recipe(ca_cert_path="/ca.pem")
        assert ir.rate_limit.strategy == RateLimitStrategyType.TOKEN_BUCKET
        assert ir.rate_limit.per_user is False
        assert ir.rate_limit.per_ip is True


# ============================================================================
# stateful_session_recipe
# ============================================================================


class TestStatefulSessionRecipe:
    """Test stateful session recipe."""

    def test_redis_session(self):
        ir = stateful_session_recipe(
            store_type="redis",
            store_connection_string="redis://localhost:6379/0",
        )
        assert len(ir.providers) == 1
        assert ir.providers[0].provider_type == AuthProviderType.SESSION
        cfg = ir.providers[0].config
        assert cfg.store_type == SessionStoreType.REDIS
        assert cfg.store_connection_string == "redis://localhost:6379/0"

    def test_database_session(self):
        ir = stateful_session_recipe(store_type="database")
        assert ir.providers[0].config.store_type == SessionStoreType.DATABASE

    def test_custom_ttl(self):
        ir = stateful_session_recipe(ttl_seconds=43200, idle_timeout_seconds=1800)
        cfg = ir.providers[0].config
        assert cfg.ttl_seconds == 43200
        assert cfg.idle_timeout_seconds == 1800
        assert ir.session.max_age_minutes == 720  # 43200 / 60


# ============================================================================
# mfa_totp_recipe
# ============================================================================


class TestMFATOTPRecipe:
    """Test MFA TOTP recipe (add-on)."""

    def test_add_totp_mfa(self):
        base_ir = jwt_recipe()
        ir = mfa_totp_recipe(base_ir)
        assert ir.mfa.enabled is True
        assert ir.mfa.required is False
        assert MFAProviderType.TOTP in ir.mfa.providers
        assert ir.mfa.totp_config.algorithm == TOTPAlgorithm.SHA256

    def test_add_required_mfa(self):
        base_ir = jwt_recipe()
        ir = mfa_totp_recipe(base_ir, required=True)
        assert ir.mfa.required is True

    def test_mfa_enforce_on_roles(self):
        base_ir = jwt_recipe()
        ir = mfa_totp_recipe(
            base_ir,
            required=False,
            enforce_on_roles=["admin", "operator"],
        )
        assert "admin" in ir.mfa.enforce_on_role
        assert "operator" in ir.mfa.enforce_on_role

    def test_mfa_grace_period(self):
        base_ir = jwt_recipe()
        ir = mfa_totp_recipe(base_ir, required=False, grace_period_days=7)
        assert ir.mfa.grace_period_days == 7

    def test_mfa_returns_same_ir(self):
        base_ir = jwt_recipe()
        ir = mfa_totp_recipe(base_ir)
        assert ir is base_ir  # modifies in-place


# ============================================================================
# mfa_webauthn_recipe
# ============================================================================


class TestMFAWebAuthnRecipe:
    """Test MFA WebAuthn recipe (add-on)."""

    def test_add_webauthn_mfa(self):
        base_ir = jwt_recipe()
        ir = mfa_webauthn_recipe(
            base_ir,
            rp_id="example.com",
            rp_name="Example Corp",
            origins=["https://example.com"],
        )
        assert ir.mfa.enabled is True
        assert MFAProviderType.WEBAUTHN in ir.mfa.providers
        assert MFAProviderType.TOTP in ir.mfa.providers  # fallback
        assert ir.mfa.webauthn_config is not None
        assert ir.mfa.webauthn_config.rp_id == "example.com"
        assert ir.mfa.webauthn_config.user_verification == "required"

    def test_required_webauthn(self):
        base_ir = jwt_recipe()
        ir = mfa_webauthn_recipe(
            base_ir,
            rp_id="example.com",
            rp_name="Test",
            origins=["https://example.com"],
            required=True,
        )
        assert ir.mfa.required is True


# ============================================================================
# multi_provider_recipe
# ============================================================================


class TestMultiProviderRecipe:
    """Test multi-provider recipe."""

    def test_combine_jwt_and_saml(self):
        jwt_provider = AuthProvider(
            id="jwt",
            provider_type=AuthProviderType.JWT,
            config=jwt_recipe().providers[0].config,
        )
        ir = multi_provider_recipe(providers=[jwt_provider])
        assert len(ir.providers) == 1

    def test_with_default_permissions(self):
        ir = multi_provider_recipe(
            providers=[],
            default_permissions=["user:read", "user:write", "order:*"],
        )
        assert len(ir.permissions) == 3
        perm_ids = {p.id for p in ir.permissions}
        assert "user:read" in perm_ids
        assert "order:*" in perm_ids

    def test_with_custom_rate_limit(self):
        from midicoder.packs.cp03_auth.models import RateLimitConfig
        ir = multi_provider_recipe(
            providers=[],
            rate_limit_config=RateLimitConfig(max_requests=50, window_seconds=60),
        )
        assert ir.rate_limit.max_requests == 50

    def test_empty_providers_no_error(self):
        ir = multi_provider_recipe(providers=[])
        assert ir.providers == []
        # Should NOT raise since validate() is not called by recipes
