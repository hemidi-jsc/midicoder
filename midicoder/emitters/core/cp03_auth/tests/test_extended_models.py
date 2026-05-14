"""
CP03: Extended Auth Models — RateLimit, MFA, TOTP, WebAuthn.

Tests for models added in hardening (Phase 2):
- RateLimitStrategyType enum
- RateLimitConfig dataclass
- MFAProviderType enum
- TOTPAlgorithm enum
- TOTPConfig dataclass
- WebAuthnConfig dataclass
- MFAPolicy dataclass
- AuthIR rate_limit + mfa fields
"""

import pytest
from midicoder.emitters.core.cp03_auth.models import (
    AuthIR,
    AuthProvider,
    AuthProviderType,
    JWTAuthConfig,
    MFAProviderType,
    MFAPolicy,
    RateLimitConfig,
    RateLimitStrategyType,
    TOTPAlgorithm,
    TOTPConfig,
    WebAuthnConfig,
)
from midicoder.errors import ErrorCode, MidicoderError


# ============================================================================
# RateLimitStrategyType
# ============================================================================


class TestRateLimitStrategyType:
    """Test RateLimitStrategyType enum."""

    def test_fixed_window_value(self):
        assert RateLimitStrategyType.FIXED_WINDOW == "fixed_window"

    def test_sliding_window_value(self):
        assert RateLimitStrategyType.SLIDING_WINDOW == "sliding_window"

    def test_token_bucket_value(self):
        assert RateLimitStrategyType.TOKEN_BUCKET == "token_bucket"

    def test_leaky_bucket_value(self):
        assert RateLimitStrategyType.LEAKY_BUCKET == "leaky_bucket"

    def test_all_members_exist(self):
        members = [m.value for m in RateLimitStrategyType]
        assert "fixed_window" in members
        assert "sliding_window" in members
        assert "token_bucket" in members
        assert "leaky_bucket" in members


# ============================================================================
# RateLimitConfig
# ============================================================================


class TestRateLimitConfig:
    """Test RateLimitConfig dataclass."""

    def test_default_values(self):
        cfg = RateLimitConfig()
        assert cfg.strategy == RateLimitStrategyType.SLIDING_WINDOW
        assert cfg.max_requests == 10
        assert cfg.window_seconds == 300
        assert cfg.per_user is True
        assert cfg.per_ip is True
        assert cfg.per_endpoint is False
        assert cfg.block_duration_seconds == 600
        assert cfg.storage_backend == "memory"

    def test_custom_values(self):
        cfg = RateLimitConfig(
            strategy=RateLimitStrategyType.TOKEN_BUCKET,
            max_requests=100,
            window_seconds=60,
            per_user=False,
            per_ip=True,
            per_endpoint=True,
            block_duration_seconds=1200,
            storage_backend="redis",
        )
        assert cfg.strategy == RateLimitStrategyType.TOKEN_BUCKET
        assert cfg.max_requests == 100
        assert cfg.window_seconds == 60
        assert cfg.per_endpoint is True

    def test_invalid_max_requests_zero(self):
        with pytest.raises(MidicoderError) as exc_info:
            RateLimitConfig(max_requests=0)
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_invalid_max_requests_negative(self):
        with pytest.raises(MidicoderError) as exc_info:
            RateLimitConfig(max_requests=-1)
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_invalid_window_seconds_zero(self):
        with pytest.raises(MidicoderError) as exc_info:
            RateLimitConfig(window_seconds=0)
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_invalid_window_seconds_negative(self):
        with pytest.raises(MidicoderError) as exc_info:
            RateLimitConfig(window_seconds=-60)
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_invalid_block_duration_negative(self):
        with pytest.raises(MidicoderError) as exc_info:
            RateLimitConfig(block_duration_seconds=-1)
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_block_duration_zero_ok(self):
        cfg = RateLimitConfig(block_duration_seconds=0)
        assert cfg.block_duration_seconds == 0


# ============================================================================
# MFAProviderType
# ============================================================================


class TestMFAProviderType:
    """Test MFAProviderType enum."""

    def test_totp_value(self):
        assert MFAProviderType.TOTP == "totp"

    def test_webauthn_value(self):
        assert MFAProviderType.WEBAUTHN == "webauthn"

    def test_sms_value(self):
        assert MFAProviderType.SMS == "sms"

    def test_email_otp_value(self):
        assert MFAProviderType.EMAIL_OTP == "email_otp"

    def test_all_members_exist(self):
        members = [m.value for m in MFAProviderType]
        assert "totp" in members
        assert "webauthn" in members
        assert "sms" in members
        assert "email_otp" in members


# ============================================================================
# TOTPAlgorithm
# ============================================================================


class TestTOTPAlgorithm:
    """Test TOTPAlgorithm enum."""

    def test_sha1(self):
        assert TOTPAlgorithm.SHA1 == "SHA1"

    def test_sha256(self):
        assert TOTPAlgorithm.SHA256 == "SHA256"

    def test_sha512(self):
        assert TOTPAlgorithm.SHA512 == "SHA512"


# ============================================================================
# TOTPConfig
# ============================================================================


class TestTOTPConfig:
    """Test TOTPConfig dataclass."""

    def test_default_values(self):
        cfg = TOTPConfig()
        assert cfg.algorithm == TOTPAlgorithm.SHA1
        assert cfg.digit_count == 6
        assert cfg.period == 30
        assert cfg.skew == 1

    def test_custom_values(self):
        cfg = TOTPConfig(
            algorithm=TOTPAlgorithm.SHA256,
            digit_count=8,
            period=60,
            skew=2,
        )
        assert cfg.algorithm == TOTPAlgorithm.SHA256
        assert cfg.digit_count == 8

    def test_invalid_digit_count_five(self):
        with pytest.raises(MidicoderError) as exc_info:
            TOTPConfig(digit_count=5)
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_invalid_digit_count_seven(self):
        with pytest.raises(MidicoderError) as exc_info:
            TOTPConfig(digit_count=7)
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_invalid_period_zero(self):
        with pytest.raises(MidicoderError) as exc_info:
            TOTPConfig(period=0)
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_invalid_period_negative(self):
        with pytest.raises(MidicoderError) as exc_info:
            TOTPConfig(period=-1)
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_invalid_skew_negative(self):
        with pytest.raises(MidicoderError) as exc_info:
            TOTPConfig(skew=-1)
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_skew_zero_ok(self):
        cfg = TOTPConfig(skew=0)
        assert cfg.skew == 0


# ============================================================================
# WebAuthnConfig
# ============================================================================


class TestWebAuthnConfig:
    """Test WebAuthnConfig dataclass."""

    def test_valid_config(self):
        cfg = WebAuthnConfig(
            rp_id="example.com",
            rp_name="Example Corp",
            origins=["https://example.com"],
        )
        assert cfg.rp_id == "example.com"
        assert cfg.rp_name == "Example Corp"
        assert cfg.require_resident_key is False
        assert cfg.user_verification == "preferred"
        assert cfg.timeout_seconds == 60

    def test_full_config(self):
        cfg = WebAuthnConfig(
            rp_id="app.example.com",
            rp_name="My App",
            origins=["https://app.example.com", "https://dev.example.com"],
            require_resident_key=True,
            user_verification="required",
            timeout_seconds=120,
            allow_credentials=["key1", "key2"],
        )
        assert cfg.require_resident_key is True
        assert len(cfg.allow_credentials) == 2

    def test_missing_rp_id(self):
        with pytest.raises(MidicoderError) as exc_info:
            WebAuthnConfig(rp_id="", rp_name="Test", origins=["https://x.com"])
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_missing_rp_name(self):
        with pytest.raises(MidicoderError) as exc_info:
            WebAuthnConfig(rp_id="x.com", rp_name="", origins=["https://x.com"])
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_missing_origins(self):
        with pytest.raises(MidicoderError) as exc_info:
            WebAuthnConfig(rp_id="x.com", rp_name="Test", origins=[])
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_invalid_user_verification(self):
        with pytest.raises(MidicoderError) as exc_info:
            WebAuthnConfig(
                rp_id="x.com",
                rp_name="Test",
                origins=["https://x.com"],
                user_verification="invalid",
            )
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_user_verification_required(self):
        cfg = WebAuthnConfig(
            rp_id="x.com", rp_name="T", origins=["https://x.com"], user_verification="required"
        )
        assert cfg.user_verification == "required"

    def test_user_verification_discouraged(self):
        cfg = WebAuthnConfig(
            rp_id="x.com", rp_name="T", origins=["https://x.com"], user_verification="discouraged"
        )
        assert cfg.user_verification == "discouraged"


# ============================================================================
# MFAPolicy
# ============================================================================


class TestMFAPolicy:
    """Test MFAPolicy dataclass."""

    def test_default_values(self):
        policy = MFAPolicy()
        assert policy.enabled is False
        assert policy.required is False
        assert policy.providers == []
        assert isinstance(policy.totp_config, TOTPConfig)
        assert policy.webauthn_config is None
        assert policy.enforce_on_role == []
        assert policy.grace_period_days == 0

    def test_full_mfa_policy(self):
        policy = MFAPolicy(
            enabled=True,
            required=True,
            providers=[MFAProviderType.TOTP, MFAProviderType.WEBAUTHN],
            totp_config=TOTPConfig(algorithm=TOTPAlgorithm.SHA256, digit_count=8),
            webauthn_config=WebAuthnConfig(
                rp_id="example.com", rp_name="Test", origins=["https://example.com"]
            ),
            enforce_on_role=["admin", "operator"],
        )
        assert policy.required is True
        assert len(policy.providers) == 2
        assert policy.totp_config.digit_count == 8
        assert policy.webauthn_config.rp_id == "example.com"
        assert "admin" in policy.enforce_on_role

    def test_required_without_providers(self):
        with pytest.raises(MidicoderError) as exc_info:
            MFAPolicy(required=True, providers=[])
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_required_with_grace_period(self):
        with pytest.raises(MidicoderError) as exc_info:
            MFAPolicy(required=True, providers=[MFAProviderType.TOTP], grace_period_days=7)
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_negative_grace_period(self):
        with pytest.raises(MidicoderError) as exc_info:
            MFAPolicy(grace_period_days=-1)
        assert exc_info.value.code == ErrorCode.CP03_AUTH_CONFIG_INVALID

    def test_optional_with_grace_period(self):
        policy = MFAPolicy(
            enabled=True,
            required=False,
            providers=[MFAProviderType.TOTP],
            grace_period_days=14,
        )
        assert policy.required is False
        assert policy.grace_period_days == 14

    def test_zero_grace_period_ok(self):
        policy = MFAPolicy(required=True, providers=[MFAProviderType.TOTP], grace_period_days=0)
        assert policy.grace_period_days == 0


# ============================================================================
# AuthIR — rate_limit and mfa fields
# ============================================================================


class TestAuthIRExtended:
    """Test AuthIR with new rate_limit and mfa fields."""

    def test_authir_default_rate_limit(self):
        ir = AuthIR(
            providers=[AuthProvider(
                id="jwt",
                provider_type=AuthProviderType.JWT,
                config=JWTAuthConfig(),
            )]
        )
        assert isinstance(ir.rate_limit, RateLimitConfig)
        assert ir.rate_limit.strategy == RateLimitStrategyType.SLIDING_WINDOW
        assert ir.rate_limit.max_requests == 10

    def test_authir_default_mfa(self):
        ir = AuthIR(
            providers=[AuthProvider(
                id="jwt",
                provider_type=AuthProviderType.JWT,
                config=JWTAuthConfig(),
            )]
        )
        assert isinstance(ir.mfa, MFAPolicy)
        assert ir.mfa.enabled is False
        assert ir.mfa.required is False

    def test_authir_custom_rate_limit(self):
        ir = AuthIR(
            providers=[AuthProvider(
                id="jwt",
                provider_type=AuthProviderType.JWT,
                config=JWTAuthConfig(),
            )],
            rate_limit=RateLimitConfig(
                strategy=RateLimitStrategyType.FIXED_WINDOW,
                max_requests=5,
                window_seconds=60,
            ),
        )
        assert ir.rate_limit.strategy == RateLimitStrategyType.FIXED_WINDOW
        assert ir.rate_limit.max_requests == 5

    def test_authir_with_mfa_enabled(self):
        ir = AuthIR(
            providers=[AuthProvider(
                id="jwt",
                provider_type=AuthProviderType.JWT,
                config=JWTAuthConfig(),
            )],
            mfa=MFAPolicy(
                enabled=True,
                required=True,
                providers=[MFAProviderType.TOTP],
            ),
        )
        assert ir.mfa.enabled is True
        assert ir.mfa.required is True
        assert MFAProviderType.TOTP in ir.mfa.providers

    def test_authir_full_composition(self):
        ir = AuthIR(
            providers=[AuthProvider(
                id="jwt",
                provider_type=AuthProviderType.JWT,
                config=JWTAuthConfig(expire_minutes=15),
            )],
            rate_limit=RateLimitConfig(max_requests=5, window_seconds=120),
            mfa=MFAPolicy(
                enabled=True,
                providers=[MFAProviderType.TOTP, MFAProviderType.WEBAUTHN],
                totp_config=TOTPConfig(digit_count=8),
                webauthn_config=WebAuthnConfig(
                    rp_id="example.com", rp_name="Test", origins=["https://example.com"]
                ),
            ),
        )
        assert len(ir.providers) == 1
        assert ir.rate_limit.max_requests == 5
        assert ir.mfa.totp_config.digit_count == 8
        assert ir.mfa.webauthn_config is not None
        assert ir.mfa.webauthn_config.rp_id == "example.com"
