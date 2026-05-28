# coding: utf-8
"""
Tests for CP46 parser — MFA & Advanced Authentication.
"""

import pytest
from midicoder.packs.cp_full_mfa.parser import (
    MFAIR,
    MFARule,
    parse_mfa_rules,
    parse_mfa_config,
    parse_methods_config,
    parse_enabled_methods,
    parse_to_ir,
)
from midicoder.packs.cp_full_mfa.models import (
    MFAMethod,
    MFAPriority,
)


class TestMFARule:
    def test_create_default(self):
        rule = MFARule(rule_id="rule_001")
        assert rule.rule_id == "rule_001"
        assert rule.method == MFAMethod.TOTP
        assert rule.priority == MFAPriority.REQUIRED
        assert rule.enabled is True

    def test_create_custom(self):
        rule = MFARule(
            rule_id="rule_002",
            role_id="admin",
            method=MFAMethod.WEBAUTHN_FIDO2,
            priority=MFAPriority.REQUIRED,
        )
        assert rule.role_id == "admin"
        assert rule.method == MFAMethod.WEBAUTHN_FIDO2

    def test_to_dict(self):
        rule = MFARule(rule_id="rule_001", role_id="staff", method=MFAMethod.TOTP)
        d = rule.to_dict()
        assert d["rule_id"] == "rule_001"
        assert d["method"] == "totp"

    def test_from_dict(self):
        data = {
            "rule_id": "rule_001",
            "role_id": "admin",
            "method": "webauthn_fido2",
            "priority": "required",
            "enabled": True,
        }
        rule = MFARule.from_dict(data)
        assert rule.method == MFAMethod.WEBAUTHN_FIDO2
        assert rule.priority == MFAPriority.REQUIRED

    def test_roundtrip(self):
        rule = MFARule(
            rule_id="rule_001",
            role_id="staff",
            method=MFAMethod.SMS_OTP,
            priority=MFAPriority.BACKUP,
        )
        d = rule.to_dict()
        restored = MFARule.from_dict(d)
        assert restored.rule_id == rule.rule_id
        assert restored.method == rule.method
        assert restored.priority == rule.priority


class TestParseMFARules:
    def test_parse_empty(self):
        rules = parse_mfa_rules({})
        assert rules == []

    def test_parse_with_rules_key(self):
        data = {"rules": [{"rule_id": "r1", "method": "totp"}]}
        rules = parse_mfa_rules(data)
        assert len(rules) == 1
        assert rules[0].rule_id == "r1"

    def test_parse_with_mfa_rules_key(self):
        data = {"mfa_rules": [{"rule_id": "r1", "method": "sms_otp"}]}
        rules = parse_mfa_rules(data)
        assert len(rules) == 1
        assert rules[0].method == MFAMethod.SMS_OTP

    def test_parse_multiple_rules(self):
        data = {
            "rules": [
                {"rule_id": "r1", "method": "totp", "role_id": "staff"},
                {"rule_id": "r2", "method": "webauthn_fido2", "role_id": "admin"},
            ]
        }
        rules = parse_mfa_rules(data)
        assert len(rules) == 2


class TestParseMFAConfig:
    def test_parse_defaults(self):
        config = parse_mfa_config({})
        assert config["require_mfa"] is True
        assert config["max_attempts"] == 5
        assert config["challenge_timeout"] == 5

    def test_parse_custom(self):
        data = {
            "require_mfa": False,
            "max_attempts": 10,
            "challenge_timeout": 10,
            "session_duration": 720,
        }
        config = parse_mfa_config(data)
        assert config["require_mfa"] is False
        assert config["max_attempts"] == 10


class TestParseMethodsConfig:
    def test_parse_empty(self):
        methods = parse_methods_config({})
        assert methods["use_totp"] is True
        assert methods["use_webauthn"] is True

    def test_parse_dict_enabled(self):
        data = {"methods": {"totp": True, "webauthn": True, "biometric": False}}
        methods = parse_methods_config(data)
        assert methods["use_totp"] is True
        assert methods["use_biometric"] is False

    def test_parse_dict_all_disabled(self):
        data = {"methods": {"totp": False, "sms_otp": False, "webauthn_fido2": False, "biometric": False}}
        methods = parse_methods_config(data)
        assert all(v is False for v in methods.values())


class TestParseEnabledMethods:
    def test_default_from_methods_config(self):
        """Default: enabled_methods derived from methods config."""
        data = {"methods": {"totp": True, "sms_otp": False, "webauthn": True, "biometric": False}}
        enabled = parse_enabled_methods(data)
        assert MFAMethod.TOTP in enabled
        assert MFAMethod.SMS_OTP not in enabled
        assert MFAMethod.WEBAUTHN_FIDO2 in enabled
        assert MFAMethod.BIOMETRIC not in enabled

    def test_explicit_list(self):
        """Explicit enabled_methods list overrides methods config."""
        data = {"enabled_methods": ["totp", "sms_otp"]}
        enabled = parse_enabled_methods(data)
        assert enabled == [MFAMethod.TOTP, MFAMethod.SMS_OTP]

    def test_empty_data_returns_all(self):
        data = {}
        enabled = parse_enabled_methods(data)
        assert len(enabled) == 4  # All methods enabled by default


class TestParseToIR:
    def test_parse_empty(self):
        ir = parse_to_ir({})
        assert ir.rules == []
        assert ir.require_mfa is True

    def test_parse_full(self):
        data = {
            "rules": [
                {"rule_id": "r1", "method": "totp", "role_id": "all_users"},
                {"rule_id": "r2", "method": "webauthn_fido2", "role_id": "admin"},
            ],
            "require_mfa": True,
            "max_attempts": 5,
            "methods": {"totp": True, "webauthn": True},
        }
        ir = parse_to_ir(data)
        assert len(ir.rules) == 2
        assert ir.require_mfa is True
        assert ir.use_totp is True

    def test_parse_with_alias_keys(self):
        data = {
            "mfa_rules": [{"id": "r1", "method": "sms_otp"}],
        }
        ir = parse_to_ir(data)
        assert len(ir.rules) == 1
        assert ir.rules[0].rule_id == "r1"


class TestMFAIR:
    def test_create_default(self):
        ir = MFAIR()
        assert len(ir.enabled_methods) == 4
        assert ir.default_method == MFAMethod.TOTP

    def test_to_dict(self):
        ir = MFAIR(
            rules=[MFARule(rule_id="r1")],
            require_mfa=True,
        )
        d = ir.to_dict()
        assert len(d["rules"]) == 1
        assert d["require_mfa"] is True

    def test_from_dict(self):
        data = {
            "rules": [{"rule_id": "r1", "method": "totp"}],
            "default_method": "sms_otp",
            "require_mfa": False,
        }
        ir = MFAIR.from_dict(data)
        assert ir.default_method == MFAMethod.SMS_OTP
        assert ir.require_mfa is False
