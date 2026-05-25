# coding: utf-8
"""
Test EMITTER_REGISTRY entries cho 9 pack mới (CP33, CP36, CP37, CP44, CP45, CP46, CP48, CP49, CP50)
và parser functions tương ứng.

Tác giả: Midicoder CE Team
Version: 1.0.0
"""

from __future__ import annotations

from midicoder.pipeline.pack_emitter_router import EMITTER_REGISTRY, PARSER_REGISTRY


# ===========================================================================
# Test EMITTER_REGISTRY — 36 entries (9 packs x 4 stacks)
# ===========================================================================

class TestEmitterRegistryEntries:
    """Kiểm tra tất cả 36 EMITTER_REGISTRY entries tồn tại và có cấu trúc đúng."""

    expected_packs = [
        ("cp33.financial.fastapi", "FinancialFastAPIEmitter", "cp33_financial"),
        ("cp33.financial.nestjs", "FinancialNestJSEmitter", "cp33_financial"),
        ("cp33.financial.angular", "FinancialAngularEmitter", "cp33_financial"),
        ("cp33.financial.react", "FinancialReactEmitter", "cp33_financial"),
        ("cp36.onboarding.fastapi", "TenantOnboardingFastAPIEmitter", "cp36_onboarding"),
        ("cp36.onboarding.nestjs", "TenantOnboardingNestJSEmitter", "cp36_onboarding"),
        ("cp36.onboarding.angular", "TenantOnboardingAngularEmitter", "cp36_onboarding"),
        ("cp36.onboarding.react", "TenantOnboardingReactEmitter", "cp36_onboarding"),
        ("cp37.feature_flags.fastapi", "FastAPIFeatureFlagEmitter", "cp37_feature_flags"),
        ("cp37.feature_flags.nestjs", "NestJSFeatureFlagEmitter", "cp37_feature_flags"),
        ("cp37.feature_flags.angular", "AngularFeatureFlagEmitter", "cp37_feature_flags"),
        ("cp37.feature_flags.react", "ReactFeatureFlagEmitter", "cp37_feature_flags"),
        ("cp44.bulk_ops.fastapi", "FastAPIBulkOpsEmitter", "cp44_bulk_ops"),
        ("cp44.bulk_ops.nestjs", "NestJSBulkOpsEmitter", "cp44_bulk_ops"),
        ("cp44.bulk_ops.angular", "AngularBulkOpsEmitter", "cp44_bulk_ops"),
        ("cp44.bulk_ops.react", "ReactBulkOpsEmitter", "cp44_bulk_ops"),
        ("cp45.payment.fastapi", "FastAPIPaymentEmitter", "cp45_payment"),
        ("cp45.payment.nestjs", "NestJSPaymentEmitter", "cp45_payment"),
        ("cp45.payment.angular", "AngularPaymentEmitter", "cp45_payment"),
        ("cp45.payment.react", "ReactPaymentEmitter", "cp45_payment"),
        ("cp46.mfa.fastapi", "FastAPIMFAEmitter", "cp46_mfa"),
        ("cp46.mfa.nestjs", "NestJSMFAEmitter", "cp46_mfa"),
        ("cp46.mfa.angular", "AngularMFAEmitter", "cp46_mfa"),
        ("cp46.mfa.react", "ReactMFAEmitter", "cp46_mfa"),
        ("cp48.rate_limit.fastapi", "FastAPIRateLimitEmitter", "cp48_rate_limit"),
        ("cp48.rate_limit.nestjs", "NestJSRateLimitEmitter", "cp48_rate_limit"),
        ("cp48.rate_limit.angular", "AngularRateLimitEmitter", "cp48_rate_limit"),
        ("cp48.rate_limit.react", "ReactRateLimitEmitter", "cp48_rate_limit"),
        ("cp49.consent.fastapi", "FastAPIConsentEmitter", "cp49_consent"),
        ("cp49.consent.nestjs", "NestJSConsentEmitter", "cp49_consent"),
        ("cp49.consent.angular", "AngularConsentEmitter", "cp49_consent"),
        ("cp49.consent.react", "ReactConsentEmitter", "cp49_consent"),
        ("cp50.catalog.fastapi", "FastAPICatalogEmitter", "cp50_catalog"),
        ("cp50.catalog.nestjs", "NestJSCatalogEmitter", "cp50_catalog"),
        ("cp50.catalog.angular", "AngularCatalogEmitter", "cp50_catalog"),
        ("cp50.catalog.react", "ReactCatalogEmitter", "cp50_catalog"),
    ]

    def test_all_36_entries_exist(self) -> None:
        """Kiểm tra tất cả 36 entries đều có trong registry."""
        for key, _cls, _parser in self.expected_packs:
            assert key in EMITTER_REGISTRY, f"Missing EMITTER_REGISTRY entry: {key}"

    def test_entry_structure(self) -> None:
        """Mỗi entry là tuple 3 phần: (module_path, class_name, parser_key)."""
        for key, expected_class, expected_parser in self.expected_packs:
            entry = EMITTER_REGISTRY[key]
            assert len(entry) == 3, f"Entry {key} should be 3-tuple"
            module_path, class_name, parser_key = entry
            assert isinstance(module_path, str)
            assert isinstance(class_name, str)
            assert parser_key is None or isinstance(parser_key, str)

    def test_class_names_correct(self) -> None:
        """Class name trong registry phải khớp với expected."""
        for key, expected_class, _parser in self.expected_packs:
            entry = EMITTER_REGISTRY[key]
            assert entry[1] == expected_class, (
                f"{key}: expected class '{expected_class}', got '{entry[1]}'"
            )

    def test_parser_keys_correct(self) -> None:
        """Parser key trong registry phải khớp với expected."""
        for key, _cls, expected_parser in self.expected_packs:
            entry = EMITTER_REGISTRY[key]
            assert entry[2] == expected_parser, (
                f"{key}: expected parser_key '{expected_parser}', got '{entry[2]}'"
            )

    def test_module_paths_start_with_prefix(self) -> None:
        """Module path phải bắt đầu bằng 'midicoder.emitters.core.'."""
        for key, _cls, _parser in self.expected_packs:
            module_path = EMITTER_REGISTRY[key][0]
            assert module_path.startswith("midicoder.emitters.core."), (
                f"{key}: module_path '{module_path}' doesn't start with expected prefix"
            )


# ===========================================================================
# Test PARSER_REGISTRY — 9 parser functions
# ===========================================================================

class TestParserRegistryEntries:
    """Kiểm tra 9 parser functions trong PARSER_REGISTRY."""

    expected_parsers = [
        "cp33_financial",
        "cp36_onboarding",
        "cp37_feature_flags",
        "cp44_bulk_ops",
        "cp45_payment",
        "cp46_mfa",
        "cp48_rate_limit",
        "cp49_consent",
        "cp50_catalog",
    ]

    def test_all_9_parsers_exist(self) -> None:
        """Kiểm tra tất cả 9 parser keys đều có trong PARSER_REGISTRY."""
        for key in self.expected_parsers:
            assert key in PARSER_REGISTRY, f"Missing PARSER_REGISTRY entry: {key}"

    def test_parser_values_are_callable(self) -> None:
        """Mỗi parser value phải là callable."""
        for key in self.expected_parsers:
            parser_fn = PARSER_REGISTRY[key]
            assert callable(parser_fn), f"Parser '{key}' should be callable"


# ===========================================================================
# Test Parser Functions — real data parsing
# ===========================================================================

class TestCP33FinancialParser:
    """Test _parse_financial_dict — pass-through raw dict."""

    def test_passthrough_raw_dict(self) -> None:
        from midicoder.pipeline.pack_emitter_router import _parse_financial_dict
        raw = {"currencies": [{"code": "USD"}]}
        result = _parse_financial_dict(raw)
        assert result == raw

    def test_passthrough_empty_dict(self) -> None:
        from midicoder.pipeline.pack_emitter_router import _parse_financial_dict
        result = _parse_financial_dict({})
        assert result == {}


class TestCP36OnboardingParser:
    """Test _parse_onboarding_dict — real OnboardingIR parsing."""

    def test_parse_minimal_dsl(self) -> None:
        from midicoder.pipeline.pack_emitter_router import _parse_onboarding_dict
        raw = {"plans": [], "trial": {}, "approval": {}, "token": {}}
        result = _parse_onboarding_dict(raw)
        assert result is not None

    def test_parse_with_plan(self) -> None:
        from midicoder.emitters.core.cp36_tenant_onboarding.models import OnboardingIR
        from midicoder.pipeline.pack_emitter_router import _parse_onboarding_dict
        raw = {
            "plans": [
                {
                    "plan": "professional",
                    "monthly_price": "29.99",
                    "yearly_price": "299.99",
                    "features": ["api_access"],
                    "max_users": 100,
                    "max_storage_gb": 100,
                }
            ],
            "trial": {"default_days": 14, "auto_start": True},
            "approval": {"require_admin_approval": False},
            "token": {"expiry_seconds": 86400},
        }
        result = _parse_onboarding_dict(raw)
        assert isinstance(result, OnboardingIR)
        assert len(result.plans) == 1


class TestCP37FeatureFlagParser:
    """Test _parse_feature_flag_dict — FeatureFlagIR.from_dict."""

    def test_parse_empty_dict(self) -> None:
        from midicoder.pipeline.pack_emitter_router import _parse_feature_flag_dict
        result = _parse_feature_flag_dict({})
        assert result is not None

    def test_parse_non_dict_returns_empty_list(self) -> None:
        from midicoder.pipeline.pack_emitter_router import _parse_feature_flag_dict
        result = _parse_feature_flag_dict("not_a_dict")  # type: ignore
        assert result == []


class TestCP44BulkOpsParser:
    """Test _parse_bulk_ops_dict — BulkIR.from_dict."""

    def test_parse_empty_dict(self) -> None:
        from midicoder.pipeline.pack_emitter_router import _parse_bulk_ops_dict
        result = _parse_bulk_ops_dict({})
        assert result is not None

    def test_parse_non_dict_returns_empty_list(self) -> None:
        from midicoder.pipeline.pack_emitter_router import _parse_bulk_ops_dict
        result = _parse_bulk_ops_dict(42)  # type: ignore
        assert result == []


class TestCP45PaymentParser:
    """Test _parse_payment_dict — PaymentIR.from_dict."""

    def test_parse_empty_dict(self) -> None:
        from midicoder.pipeline.pack_emitter_router import _parse_payment_dict
        result = _parse_payment_dict({})
        assert result is not None

    def test_parse_non_dict_returns_empty_list(self) -> None:
        from midicoder.pipeline.pack_emitter_router import _parse_payment_dict
        result = _parse_payment_dict(None)  # type: ignore
        assert result == []


class TestCP46MFAParser:
    """Test _parse_mfa_dict — MFAIR.from_dict."""

    def test_parse_empty_dict(self) -> None:
        from midicoder.pipeline.pack_emitter_router import _parse_mfa_dict
        result = _parse_mfa_dict({})
        assert result is not None

    def test_parse_non_dict_returns_empty_list(self) -> None:
        from midicoder.pipeline.pack_emitter_router import _parse_mfa_dict
        result = _parse_mfa_dict([])  # type: ignore
        assert result == []


class TestCP48RateLimitParser:
    """Test _parse_rate_limit_dict — RateLimitIR.from_dict."""

    def test_parse_empty_dict(self) -> None:
        from midicoder.pipeline.pack_emitter_router import _parse_rate_limit_dict
        result = _parse_rate_limit_dict({})
        assert result is not None

    def test_parse_non_dict_returns_empty_list(self) -> None:
        from midicoder.pipeline.pack_emitter_router import _parse_rate_limit_dict
        result = _parse_rate_limit_dict("invalid")  # type: ignore
        assert result == []


class TestCP49ConsentParser:
    """Test _parse_consent_dict — ConsentIR.from_dict."""

    def test_parse_empty_dict(self) -> None:
        from midicoder.pipeline.pack_emitter_router import _parse_consent_dict
        result = _parse_consent_dict({})
        assert result is not None

    def test_parse_non_dict_returns_empty_list(self) -> None:
        from midicoder.pipeline.pack_emitter_router import _parse_consent_dict
        result = _parse_consent_dict(0)  # type: ignore
        assert result == []


class TestCP50CatalogParser:
    """Test _parse_catalog_dict — CatalogIR.from_dict."""

    def test_parse_empty_dict(self) -> None:
        from midicoder.pipeline.pack_emitter_router import _parse_catalog_dict
        result = _parse_catalog_dict({})
        assert result is not None

    def test_parse_non_dict_returns_empty_list(self) -> None:
        from midicoder.pipeline.pack_emitter_router import _parse_catalog_dict
        result = _parse_catalog_dict(False)  # type: ignore
        assert result == []
