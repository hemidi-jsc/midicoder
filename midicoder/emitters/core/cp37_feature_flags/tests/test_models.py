# coding: utf-8
"""
Tests cho CP37 models: FeatureFlag, TargetingRule, FlagEvaluation, FeatureFlagEvaluator,
ABExperiment, ABVariant, ABExperimentEngine, DynamicConfig, ConfigChange, enums.
"""

from __future__ import annotations

import pytest

from midicoder.errors import ErrorCode, MidicoderError


# ============================================================================
# Test Error Codes
# ============================================================================


class TestCP37ErrorCodes:
    """Tests cho CP37 error codes."""

    def test_cp37_empty_flag_key_exists(self):
        assert hasattr(ErrorCode, "CP37_EMPTY_FLAG_KEY")
        assert ErrorCode.CP37_EMPTY_FLAG_KEY == "MDC-CP37-001"

    def test_cp37_invalid_variant_type_exists(self):
        assert hasattr(ErrorCode, "CP37_INVALID_VARIANT_TYPE")

    def test_cp37_invalid_percentage_exists(self):
        assert hasattr(ErrorCode, "CP37_INVALID_PERCENTAGE")

    def test_cp37_flag_not_found_exists(self):
        assert hasattr(ErrorCode, "CP37_FLAG_NOT_FOUND")

    def test_cp37_duplicate_flag_key_exists(self):
        assert hasattr(ErrorCode, "CP37_DUPLICATE_FLAG_KEY")

    def test_cp37_empty_config_key_exists(self):
        assert hasattr(ErrorCode, "CP37_EMPTY_CONFIG_KEY")

    def test_cp37_config_not_found_exists(self):
        assert hasattr(ErrorCode, "CP37_CONFIG_NOT_FOUND")

    def test_cp37_invalid_config_scope_exists(self):
        assert hasattr(ErrorCode, "CP37_INVALID_CONFIG_SCOPE")

    def test_cp37_empty_experiment_key_exists(self):
        assert hasattr(ErrorCode, "CP37_EMPTY_EXPERIMENT_KEY")

    def test_cp37_too_few_variants_exists(self):
        assert hasattr(ErrorCode, "CP37_TOO_FEW_VARIANTS")


# ============================================================================
# Test Enums
# ============================================================================


class TestCP37Enums:
    """Tests cho CP37 enums."""

    def test_flag_variant_type_boolean(self):
        from midicoder.emitters.core.cp37_feature_flags.models import FlagVariantType
        assert FlagVariantType.BOOLEAN.value == "boolean"

    def test_flag_variant_type_percentage(self):
        from midicoder.emitters.core.cp37_feature_flags.models import FlagVariantType
        assert FlagVariantType.PERCENTAGE.value == "percentage"

    def test_flag_variant_type_targeted(self):
        from midicoder.emitters.core.cp37_feature_flags.models import FlagVariantType
        assert FlagVariantType.TARGETED.value == "targeted"

    def test_condition_type_role(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ConditionType
        assert ConditionType.ROLE.value == "role"

    def test_condition_type_tenant(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ConditionType
        assert ConditionType.TENANT.value == "tenant"

    def test_condition_type_attribute(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ConditionType
        assert ConditionType.ATTRIBUTE.value == "attribute"

    def test_condition_type_segment(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ConditionType
        assert ConditionType.SEGMENT.value == "segment"

    def test_config_scope_global(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ConfigScope
        assert ConfigScope.GLOBAL.value == "global"

    def test_config_scope_tenant(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ConfigScope
        assert ConfigScope.TENANT.value == "tenant"

    def test_config_scope_environment(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ConfigScope
        assert ConfigScope.ENVIRONMENT.value == "environment"

    def test_config_value_type_string(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ConfigValueType
        assert ConfigValueType.STRING.value == "string"

    def test_config_value_type_number(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ConfigValueType
        assert ConfigValueType.NUMBER.value == "number"

    def test_config_value_type_boolean(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ConfigValueType
        assert ConfigValueType.BOOLEAN.value == "boolean"

    def test_config_value_type_json(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ConfigValueType
        assert ConfigValueType.JSON.value == "json"

    def test_config_value_type_array(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ConfigValueType
        assert ConfigValueType.ARRAY.value == "array"


# ============================================================================
# Test FeatureFlag Model
# ============================================================================


class TestFeatureFlag:
    """Tests cho FeatureFlag model."""

    def test_flag_creation_boolean(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            FeatureFlag,
            FlagVariantType,
        )

        flag = FeatureFlag(
            flag_key="dark_mode",
            name="Dark Mode",
            variant_type=FlagVariantType.BOOLEAN,
            default_enabled=False,
        )
        assert flag.flag_key == "dark_mode"
        assert flag.default_enabled is False
        assert flag.is_active is True

    def test_flag_creation_percentage(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            FeatureFlag,
            FlagVariantType,
        )

        flag = FeatureFlag(
            flag_key="new_checkout",
            variant_type=FlagVariantType.PERCENTAGE,
            percentage=50,
        )
        assert flag.percentage == 50

    def test_flag_empty_key_raises_error(self):
        from midicoder.emitters.core.cp37_feature_flags.models import FeatureFlag

        with pytest.raises(MidicoderError):
            FeatureFlag(flag_key="", name="Test")

    def test_flag_invalid_percentage_raises_error(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            FeatureFlag,
            FlagVariantType,
        )

        with pytest.raises(MidicoderError):
            FeatureFlag(
                flag_key="bad_flag",
                variant_type=FlagVariantType.PERCENTAGE,
                percentage=150,
            )

    def test_flag_to_dict(self):
        from midicoder.emitters.core.cp37_feature_flags.models import FeatureFlag

        flag = FeatureFlag(flag_key="test_flag", name="Test")
        d = flag.to_dict()
        assert d["flag_key"] == "test_flag"
        assert d["variant_type"] == "boolean"
        assert "created_at" in d

    def test_flag_from_dict(self):
        from midicoder.emitters.core.cp37_feature_flags.models import FeatureFlag

        data = {
            "flag_key": "restored_flag",
            "name": "Restored",
            "variant_type": "percentage",
            "percentage": 75,
            "default_enabled": True,
        }
        flag = FeatureFlag.from_dict(data)
        assert flag.flag_key == "restored_flag"
        assert flag.percentage == 75

    def test_flag_tenant_overrides(self):
        from midicoder.emitters.core.cp37_feature_flags.models import FeatureFlag

        flag = FeatureFlag(
            flag_key="tenant_flag",
            tenant_overrides={"tenant_a": True, "tenant_b": False},
        )
        assert flag.tenant_overrides["tenant_a"] is True

    def test_flag_timestamps_auto_set(self):
        from midicoder.emitters.core.cp37_feature_flags.models import FeatureFlag

        flag = FeatureFlag(flag_key="ts_test")
        assert flag.created_at is not None
        assert flag.updated_at is not None


# ============================================================================
# Test TargetingRule
# ============================================================================


class TestTargetingRule:
    """Tests cho TargetingRule."""

    def test_rule_role_match(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            TargetingRule,
            ConditionType,
        )

        rule = TargetingRule(
            rule_id="admin_rule",
            condition_type=ConditionType.ROLE,
            condition={"role": "admin"},
            value=True,
        )
        assert rule.matches({"role": "admin"}) is True
        assert rule.matches({"role": "user"}) is False

    def test_rule_tenant_match(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            TargetingRule,
            ConditionType,
        )

        rule = TargetingRule(
            rule_id="tenant_rule",
            condition_type=ConditionType.TENANT,
            condition={"tenant_id": "t1"},
            value=True,
        )
        assert rule.matches({"tenant_id": "t1"}) is True

    def test_rule_attribute_match(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            TargetingRule,
            ConditionType,
        )

        rule = TargetingRule(
            rule_id="attr_rule",
            condition_type=ConditionType.ATTRIBUTE,
            condition={"plan": "premium"},
            value=True,
        )
        assert rule.matches({"attributes": {"plan": "premium"}}) is True

    def test_rule_segment_match(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            TargetingRule,
            ConditionType,
        )

        rule = TargetingRule(
            rule_id="seg_rule",
            condition_type=ConditionType.SEGMENT,
            condition={"segment": "beta_users"},
            value=True,
        )
        assert rule.matches({"segments": ["beta_users", "early_adopter"]}) is True

    def test_rule_empty_id_raises_error(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            TargetingRule,
            ConditionType,
        )

        with pytest.raises(MidicoderError):
            TargetingRule(rule_id="", condition_type=ConditionType.ROLE, condition={}, value=True)

    def test_rule_to_dict(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            TargetingRule,
            ConditionType,
        )

        rule = TargetingRule(
            rule_id="dict_rule",
            condition_type=ConditionType.ROLE,
            condition={"role": "admin"},
            value=True,
            priority=1,
        )
        d = rule.to_dict()
        assert d["rule_id"] == "dict_rule"
        assert d["condition_type"] == "role"
        assert d["priority"] == 1

    def test_rule_from_dict(self):
        from midicoder.emitters.core.cp37_feature_flags.models import TargetingRule

        data = {
            "rule_id": "restored_rule",
            "condition_type": "tenant",
            "condition": {"tenant_id": "t1"},
            "value": False,
            "priority": 2,
        }
        rule = TargetingRule.from_dict(data)
        assert rule.rule_id == "restored_rule"
        assert rule.value is False


# ============================================================================
# Test FlagEvaluation
# ============================================================================


class TestFlagEvaluation:
    """Tests cho FlagEvaluation."""

    def test_evaluation_auto_timestamp(self):
        from midicoder.emitters.core.cp37_feature_flags.models import FlagEvaluation

        ev = FlagEvaluation(
            flag_key="test_flag",
            evaluated_value=True,
            reason="default_value",
        )
        assert ev.evaluated_at is not None

    def test_evaluation_to_dict(self):
        from midicoder.emitters.core.cp37_feature_flags.models import FlagEvaluation

        ev = FlagEvaluation(
            flag_key="test_flag",
            user_id="u1",
            tenant_id="t1",
            evaluated_value=True,
            reason="tenant_override",
        )
        d = ev.to_dict()
        assert d["flag_key"] == "test_flag"
        assert d["evaluated_value"] is True
        assert d["reason"] == "tenant_override"


# ============================================================================
# Test FeatureFlagEvaluator
# ============================================================================


class TestFeatureFlagEvaluator:
    """Tests cho FeatureFlagEvaluator."""

    def test_evaluate_default_value(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            FeatureFlag,
            FeatureFlagEvaluator,
        )

        flag = FeatureFlag(flag_key="simple_flag", default_enabled=True)
        evaluator = FeatureFlagEvaluator(flags=[flag])
        result = evaluator.evaluate("simple_flag", {})
        assert result.evaluated_value is True
        assert result.reason == "default_value"

    def test_evaluate_tenant_override(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            FeatureFlag,
            FeatureFlagEvaluator,
        )

        flag = FeatureFlag(
            flag_key="tenant_flag",
            default_enabled=False,
            tenant_overrides={"t1": True},
        )
        evaluator = FeatureFlagEvaluator(flags=[flag])
        result = evaluator.evaluate("tenant_flag", {"tenant_id": "t1"})
        assert result.evaluated_value is True
        assert "tenant_override" in result.reason

    def test_evaluate_targeting_rule(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            FeatureFlag,
            FeatureFlagEvaluator,
            FlagVariantType,
            TargetingRule,
            ConditionType,
        )

        rule = TargetingRule(
            rule_id="admin_rule",
            condition_type=ConditionType.ROLE,
            condition={"role": "admin"},
            value=True,
            priority=0,
        )
        flag = FeatureFlag(
            flag_key="targeted_flag",
            variant_type=FlagVariantType.TARGETED,
            default_enabled=False,
            targeting_rules=[rule],
        )
        evaluator = FeatureFlagEvaluator(flags=[flag])
        result = evaluator.evaluate("targeted_flag", {"role": "admin"})
        assert result.evaluated_value is True
        assert "targeting_rule" in result.reason

    def test_evaluate_percentage(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            FeatureFlag,
            FeatureFlagEvaluator,
            FlagVariantType,
        )

        flag = FeatureFlag(
            flag_key="pct_flag",
            variant_type=FlagVariantType.PERCENTAGE,
            percentage=100,
        )
        evaluator = FeatureFlagEvaluator(flags=[flag])
        result = evaluator.evaluate("pct_flag", {"user_id": "any_user"})
        assert result.evaluated_value is True

    def test_evaluate_flag_not_found(self):
        from midicoder.emitters.core.cp37_feature_flags.models import FeatureFlagEvaluator

        evaluator = FeatureFlagEvaluator()
        result = evaluator.evaluate("nonexistent", {})
        assert result.evaluated_value is False
        assert "flag_not_found" in result.reason

    def test_evaluate_inactive_flag(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            FeatureFlag,
            FeatureFlagEvaluator,
        )

        flag = FeatureFlag(flag_key="inactive_flag", is_active=False)
        evaluator = FeatureFlagEvaluator(flags=[flag])
        result = evaluator.evaluate("inactive_flag", {})
        assert result.evaluated_value is False

    def test_evaluate_all(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            FeatureFlag,
            FeatureFlagEvaluator,
        )

        flags = [
            FeatureFlag(flag_key="f1", default_enabled=True),
            FeatureFlag(flag_key="f2", default_enabled=False),
        ]
        evaluator = FeatureFlagEvaluator(flags=flags)
        result = evaluator.evaluate_all({})
        assert result["f1"] is True
        assert result["f2"] is False

    def test_add_flag(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            FeatureFlag,
            FeatureFlagEvaluator,
        )

        evaluator = FeatureFlagEvaluator()
        evaluator.add_flag(FeatureFlag(flag_key="added_flag"))
        result = evaluator.evaluate("added_flag", {})
        assert result.flag_key == "added_flag"

    def test_remove_flag(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            FeatureFlag,
            FeatureFlagEvaluator,
        )

        evaluator = FeatureFlagEvaluator(flags=[FeatureFlag(flag_key="to_remove")])
        evaluator.remove_flag("to_remove")
        result = evaluator.evaluate("to_remove", {})
        assert result.evaluated_value is False


# ============================================================================
# Test ABVariant
# ============================================================================


class TestABVariant:
    """Tests cho ABVariant."""

    def test_variant_creation(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ABVariant

        v = ABVariant(variant_key="control", weight=50.0)
        assert v.variant_key == "control"
        assert v.weight == 50.0

    def test_variant_empty_key_raises_error(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ABVariant

        with pytest.raises(MidicoderError):
            ABVariant(variant_key="", weight=50.0)

    def test_variant_negative_weight_raises_error(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ABVariant

        with pytest.raises(MidicoderError):
            ABVariant(variant_key="v1", weight=-10.0)

    def test_variant_to_dict(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ABVariant

        v = ABVariant(variant_key="v1", name="Test", weight=50.0, metadata={"color": "blue"})
        d = v.to_dict()
        assert d["variant_key"] == "v1"
        assert d["metadata"]["color"] == "blue"

    def test_variant_from_dict(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ABVariant

        data = {"variant_key": "restored", "weight": 100.0}
        v = ABVariant.from_dict(data)
        assert v.variant_key == "restored"


# ============================================================================
# Test ABExperiment
# ============================================================================


class TestABExperiment:
    """Tests cho ABExperiment."""

    def test_experiment_creation(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            ABExperiment,
            ABVariant,
        )

        exp = ABExperiment(
            experiment_key="checkout_test",
            variants=[
                ABVariant(variant_key="control", weight=50.0),
                ABVariant(variant_key="variant_a", weight=50.0),
            ],
        )
        assert exp.experiment_key == "checkout_test"
        assert len(exp.variants) == 2

    def test_experiment_empty_key_raises_error(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            ABExperiment,
            ABVariant,
        )

        with pytest.raises(MidicoderError):
            ABExperiment(
                experiment_key="",
                variants=[
                    ABVariant(variant_key="a", weight=50),
                    ABVariant(variant_key="b", weight=50),
                ],
            )

    def test_experiment_too_few_variants_raises_error(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            ABExperiment,
            ABVariant,
        )

        with pytest.raises(MidicoderError):
            ABExperiment(
                experiment_key="bad",
                variants=[ABVariant(variant_key="only_one", weight=100)],
            )

    def test_experiment_invalid_weight_raises_error(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            ABExperiment,
            ABVariant,
        )

        with pytest.raises(MidicoderError):
            ABExperiment(
                experiment_key="bad",
                variants=[
                    ABVariant(variant_key="a", weight=60),
                    ABVariant(variant_key="b", weight=60),
                ],
            )

    def test_experiment_is_running(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            ABExperiment,
            ABVariant,
        )

        exp = ABExperiment(
            experiment_key="running",
            variants=[
                ABVariant(variant_key="a", weight=50),
                ABVariant(variant_key="b", weight=50),
            ],
            is_active=True,
        )
        assert exp.is_running is True

    def test_experiment_to_dict_from_dict(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ABExperiment, ABVariant

        exp = ABExperiment(
            experiment_key="serial_test",
            variants=[
                ABVariant(variant_key="a", weight=50),
                ABVariant(variant_key="b", weight=50),
            ],
        )
        d = exp.to_dict()
        restored = ABExperiment.from_dict(d)
        assert restored.experiment_key == "serial_test"


# ============================================================================
# Test ABExperimentAssignment
# ============================================================================


class TestABExperimentAssignment:
    """Tests cho ABExperimentAssignment."""

    def test_assignment_auto_timestamp(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ABExperimentAssignment

        a = ABExperimentAssignment(
            experiment_key="e1",
            user_id="u1",
            assigned_variant="control",
        )
        assert a.assigned_at is not None

    def test_assignment_to_dict(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ABExperimentAssignment

        a = ABExperimentAssignment(
            experiment_key="e1",
            user_id="u1",
            tenant_id="t1",
            assigned_variant="variant_a",
        )
        d = a.to_dict()
        assert d["assigned_variant"] == "variant_a"


# ============================================================================
# Test ABExperimentEngine
# ============================================================================


class TestABExperimentEngine:
    """Tests cho ABExperimentEngine."""

    def test_deterministic_assignment(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            ABExperiment,
            ABVariant,
            ABExperimentEngine,
        )

        exp = ABExperiment(
            experiment_key="det_test",
            variants=[
                ABVariant(variant_key="control", weight=50),
                ABVariant(variant_key="variant_a", weight=50),
            ],
        )
        engine = ABExperimentEngine(experiments=[exp])

        # Cùng user luôn được assign cùng variant
        v1 = engine.assign("det_test", "user123")
        v2 = engine.assign("det_test", "user123")
        assert v1 is not None and v2 is not None
        assert v1.variant_key == v2.variant_key

    def test_assign_not_running_returns_none(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            ABExperiment,
            ABVariant,
            ABExperimentEngine,
        )

        exp = ABExperiment(
            experiment_key="stopped",
            variants=[
                ABVariant(variant_key="a", weight=50),
                ABVariant(variant_key="b", weight=50),
            ],
            is_active=False,
        )
        engine = ABExperimentEngine(experiments=[exp])
        result = engine.assign("stopped", "user1")
        assert result is None

    def test_assign_experiment_not_found_raises_error(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ABExperimentEngine

        engine = ABExperimentEngine()
        with pytest.raises(MidicoderError):
            engine.assign("nonexistent", "user1")

    def test_add_experiment_duplicate_raises_error(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            ABExperiment,
            ABVariant,
            ABExperimentEngine,
        )

        exp = ABExperiment(
            experiment_key="dup",
            variants=[
                ABVariant(variant_key="a", weight=50),
                ABVariant(variant_key="b", weight=50),
            ],
        )
        engine = ABExperimentEngine(experiments=[exp])
        with pytest.raises(MidicoderError):
            engine.add_experiment(exp)

    def test_get_experiment(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            ABExperiment,
            ABVariant,
            ABExperimentEngine,
        )

        exp = ABExperiment(
            experiment_key="find_me",
            variants=[
                ABVariant(variant_key="a", weight=50),
                ABVariant(variant_key="b", weight=50),
            ],
        )
        engine = ABExperimentEngine(experiments=[exp])
        found = engine.get_experiment("find_me")
        assert found is not None
        assert found.experiment_key == "find_me"

    def test_get_active_experiments(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            ABExperiment,
            ABVariant,
            ABExperimentEngine,
        )

        exp = ABExperiment(
            experiment_key="active",
            variants=[
                ABVariant(variant_key="a", weight=50),
                ABVariant(variant_key="b", weight=50),
            ],
            is_active=True,
        )
        engine = ABExperimentEngine(experiments=[exp])
        active = engine.get_active_experiments()
        assert len(active) == 1

    def test_create_assignment(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            ABExperiment,
            ABVariant,
            ABExperimentEngine,
        )

        exp = ABExperiment(
            experiment_key="assign_test",
            variants=[
                ABVariant(variant_key="a", weight=50),
                ABVariant(variant_key="b", weight=50),
            ],
            is_active=True,
            traffic_percentage=100.0,
        )
        engine = ABExperimentEngine(experiments=[exp])
        assignment = engine.create_assignment("assign_test", "user1", "t1")
        assert assignment is not None
        assert assignment.experiment_key == "assign_test"


# ============================================================================
# Test ConfigChange
# ============================================================================


class TestConfigChange:
    """Tests cho ConfigChange."""

    def test_config_change_auto_timestamp(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ConfigChange

        cc = ConfigChange(config_key="test.key", old_value=1, new_value=2)
        assert cc.changed_at is not None

    def test_config_change_to_dict(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ConfigChange

        cc = ConfigChange(
            config_key="test.key",
            old_value=1,
            new_value=2,
            changed_by="admin",
            reason="increase limit",
        )
        d = cc.to_dict()
        assert d["config_key"] == "test.key"
        assert d["old_value"] == 1
        assert d["new_value"] == 2

    def test_config_change_from_dict(self):
        from midicoder.emitters.core.cp37_feature_flags.models import ConfigChange

        data = {
            "config_key": "restored.key",
            "old_value": "old",
            "new_value": "new",
            "changed_by": "system",
            "reason": "test",
        }
        cc = ConfigChange.from_dict(data)
        assert cc.config_key == "restored.key"


# ============================================================================
# Test DynamicConfig
# ============================================================================


class TestDynamicConfig:
    """Tests cho DynamicConfig."""

    def test_config_creation(self):
        from midicoder.emitters.core.cp37_feature_flags.models import DynamicConfig

        config = DynamicConfig(
            config_key="app.rate_limit",
            value=1000,
        )
        assert config.config_key == "app.rate_limit"
        assert config.value == 1000

    def test_config_empty_key_raises_error(self):
        from midicoder.emitters.core.cp37_feature_flags.models import DynamicConfig

        with pytest.raises(MidicoderError):
            DynamicConfig(config_key="", value=100)

    def test_config_update_with_audit_trail(self):
        from midicoder.emitters.core.cp37_feature_flags.models import DynamicConfig

        config = DynamicConfig(config_key="test.key", value=100)
        config.update_value(200, "admin", "increase limit")
        assert config.value == 200
        assert len(config.audit_trail) == 1
        assert config.audit_trail[0].old_value == 100
        assert config.audit_trail[0].new_value == 200

    def test_config_to_dict_from_dict(self):
        from midicoder.emitters.core.cp37_feature_flags.models import DynamicConfig

        config = DynamicConfig(
            config_key="serial.key",
            value="test_value",
        )
        d = config.to_dict()
        restored = DynamicConfig.from_dict(d)
        assert restored.config_key == "serial.key"
        assert restored.value == "test_value"

    def test_config_tenant_scope(self):
        from midicoder.emitters.core.cp37_feature_flags.models import (
            DynamicConfig,
            ConfigScope,
        )

        config = DynamicConfig(
            config_key="tenant.branding",
            value="#FF0000",
            scope=ConfigScope.TENANT,
            tenant_id="t1",
        )
        assert config.scope == ConfigScope.TENANT
        assert config.tenant_id == "t1"


# ============================================================================
# Test FlagStore (ABC)
# ============================================================================


class TestFlagStore:
    """Tests cho FlagStore abstract base class."""

    def test_flag_store_is_abstract(self):
        from midicoder.emitters.core.cp37_feature_flags.models import FlagStore

        with pytest.raises(TypeError):
            FlagStore()
