# coding: utf-8
"""
Tests cho CP37 parser: parse_feature_flags, parse_experiments, parse_configs, parse_to_ir.
"""

from __future__ import annotations

import pytest

from midicoder.emitters.core.cp37_feature_flags.parser import (
    FeatureFlagIR,
    parse_configs,
    parse_experiments,
    parse_feature_flags,
    parse_to_ir,
)


class TestParseFeatureFlags:
    """Tests cho parse_feature_flags."""

    def test_parse_single_flag(self):
        data = {
            "feature_flags": [
                {
                    "flag_key": "dark_mode",
                    "name": "Dark Mode",
                    "variant_type": "boolean",
                    "default_enabled": False,
                },
            ]
        }
        flags = parse_feature_flags(data)
        assert len(flags) == 1
        assert flags[0].flag_key == "dark_mode"
        assert flags[0].default_enabled is False

    def test_parse_flags_alternative_key(self):
        data = {
            "flags": [
                {"flag_key": "f1", "name": "Flag 1"},
            ]
        }
        flags = parse_feature_flags(data)
        assert len(flags) == 1
        assert flags[0].flag_key == "f1"

    def test_parse_flag_with_targeting_rules(self):
        data = {
            "feature_flags": [
                {
                    "flag_key": "admin_feature",
                    "variant_type": "targeted",
                    "targeting_rules": [
                        {
                            "rule_id": "admin_only",
                            "condition_type": "role",
                            "condition": {"role": "admin"},
                            "value": True,
                            "priority": 0,
                        },
                    ],
                },
            ]
        }
        flags = parse_feature_flags(data)
        assert len(flags) == 1
        assert len(flags[0].targeting_rules) == 1
        assert flags[0].targeting_rules[0].rule_id == "admin_only"

    def test_parse_empty_flags(self):
        data = {}
        flags = parse_feature_flags(data)
        assert len(flags) == 0


class TestParseExperiments:
    """Tests cho parse_experiments."""

    def test_parse_single_experiment(self):
        data = {
            "experiments": [
                {
                    "experiment_key": "checkout_test",
                    "name": "Checkout Test",
                    "variants": [
                        {"variant_key": "control", "weight": 50},
                        {"variant_key": "variant_a", "weight": 50},
                    ],
                }
            ]
        }
        experiments = parse_experiments(data)
        assert len(experiments) == 1
        assert experiments[0].experiment_key == "checkout_test"
        assert len(experiments[0].variants) == 2

    def test_parse_alternative_key(self):
        data = {
            "ab_experiments": [
                {
                    "experiment_key": "alt_test",
                    "variants": [
                        {"variant_key": "a", "weight": 50},
                        {"variant_key": "b", "weight": 50},
                    ],
                }
            ]
        }
        experiments = parse_experiments(data)
        assert len(experiments) == 1

    def test_parse_empty_experiments(self):
        data = {}
        experiments = parse_experiments(data)
        assert len(experiments) == 0


class TestParseConfigs:
    """Tests cho parse_configs."""

    def test_parse_single_config(self):
        data = {
            "dynamic_configs": [
                {"config_key": "app.rate_limit", "value": 1000, "value_type": "number"},
            ]
        }
        configs = parse_configs(data)
        assert len(configs) == 1
        assert configs[0].config_key == "app.rate_limit"
        assert configs[0].value == 1000

    def test_parse_alternative_key(self):
        data = {
            "configs": [
                {"config_key": "alt.key", "value": "val"},
            ]
        }
        configs = parse_configs(data)
        assert len(configs) == 1

    def test_parse_empty_configs(self):
        data = {}
        configs = parse_configs(data)
        assert len(configs) == 0

    def test_parse_config_with_tenant_scope(self):
        data = {
            "dynamic_configs": [
                {
                    "config_key": "tenant.branding",
                    "value": "#FF0000",
                    "scope": "tenant",
                    "tenant_id": "t1",
                },
            ]
        }
        configs = parse_configs(data)
        assert configs[0].scope.value == "tenant"
        assert configs[0].tenant_id == "t1"


class TestParseToIR:
    """Tests cho parse_to_ir."""

    def test_parse_to_ir_full(self):
        data = {
            "feature_flags": [
                {"flag_key": "f1", "default_enabled": True},
            ],
            "experiments": [
                {
                    "experiment_key": "e1",
                    "variants": [
                        {"variant_key": "a", "weight": 50},
                        {"variant_key": "b", "weight": 50},
                    ],
                }
            ],
            "dynamic_configs": [
                {"config_key": "c1", "value": "val"},
            ],
        }
        ir = parse_to_ir(data)
        assert len(ir.flags) == 1
        assert len(ir.experiments) == 1
        assert len(ir.configs) == 1

    def test_parse_to_ir_empty(self):
        data = {}
        ir = parse_to_ir(data)
        assert len(ir.flags) == 0
        assert len(ir.experiments) == 0
        assert len(ir.configs) == 0


class TestFeatureFlagIR:
    """Tests cho FeatureFlagIR."""

    def test_ir_to_dict(self):
        ir = parse_to_ir({
            "feature_flags": [{"flag_key": "f1"}],
            "dynamic_configs": [{"config_key": "c1", "value": "v1"}],
        })
        d = ir.to_dict()
        assert "flags" in d
        assert "configs" in d
        assert len(d["flags"]) == 1

    def test_ir_from_dict(self):
        data = {
            "flags": [{"flag_key": "restored"}],
            "experiments": [],
            "configs": [{"config_key": "r.key", "value": 42}],
        }
        ir = FeatureFlagIR.from_dict(data)
        assert len(ir.flags) == 1
        assert ir.flags[0].flag_key == "restored"
        assert len(ir.configs) == 1