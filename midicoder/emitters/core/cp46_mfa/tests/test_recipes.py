# coding: utf-8
"""
Tests for CP46 recipes — MFA & Advanced Authentication.
"""

import pytest
from midicoder.emitters.core.cp46_mfa.recipes import (
    RecipeOutput,
    basic_mfa_recipe,
    full_mfa_recipe,
)
from midicoder.emitters.core.cp46_mfa.models import MFAMethod, MFAPriority


class TestRecipeOutput:
    def test_create(self):
        from midicoder.emitters.core.cp46_mfa.parser import MFAIR
        output = RecipeOutput(
            name="test",
            description="test recipe",
            ir=MFAIR(),
        )
        assert output.name == "test"
        assert output.description == "test recipe"


class TestBasicMFARecipe:
    def test_returns_recipe_output(self):
        output = basic_mfa_recipe()
        assert isinstance(output, RecipeOutput)

    def test_name(self):
        output = basic_mfa_recipe()
        assert output.name == "basic_mfa"

    def test_description(self):
        output = basic_mfa_recipe()
        assert "TOTP" in output.description

    def test_has_one_rule(self):
        output = basic_mfa_recipe()
        assert len(output.ir.rules) == 1

    def test_rule_method(self):
        output = basic_mfa_recipe()
        assert output.ir.rules[0].method == MFAMethod.TOTP

    def test_require_mfa(self):
        output = basic_mfa_recipe()
        assert output.ir.require_mfa is True

    def test_totp_enabled(self):
        output = basic_mfa_recipe()
        assert output.ir.use_totp is True
        assert output.ir.use_webauthn is False
        assert output.ir.use_biometric is False
        assert output.ir.use_sms_otp is False


class TestFullMFARecipe:
    def test_returns_recipe_output(self):
        output = full_mfa_recipe()
        assert isinstance(output, RecipeOutput)

    def test_name(self):
        output = full_mfa_recipe()
        assert output.name == "full_mfa"

    def test_has_four_rules(self):
        output = full_mfa_recipe()
        assert len(output.ir.rules) == 4

    def test_rule_methods(self):
        output = full_mfa_recipe()
        methods = {r.method for r in output.ir.rules}
        assert MFAMethod.WEBAUTHN_FIDO2 in methods
        assert MFAMethod.TOTP in methods
        assert MFAMethod.SMS_OTP in methods
        assert MFAMethod.BIOMETRIC in methods

    def test_all_methods_enabled(self):
        output = full_mfa_recipe()
        assert output.ir.use_totp is True
        assert output.ir.use_webauthn is True
        assert output.ir.use_biometric is True
        assert output.ir.use_sms_otp is True

    def test_allow_backup(self):
        output = full_mfa_recipe()
        assert output.ir.allow_backup is True

    def test_different_priorities(self):
        output = full_mfa_recipe()
        priorities = {r.priority for r in output.ir.rules}
        assert MFAPriority.REQUIRED in priorities
        assert MFAPriority.BACKUP in priorities
        assert MFAPriority.OPTIONAL in priorities

    def test_multi_role(self):
        output = full_mfa_recipe()
        roles = {r.role_id for r in output.ir.rules}
        assert "admin" in roles
        assert "staff" in roles
        assert "all_users" in roles
        assert "mobile_users" in roles

    def test_all_rules_have_metadata(self):
        output = full_mfa_recipe()
        for rule in output.ir.rules:
            assert "recipe" in rule.metadata
