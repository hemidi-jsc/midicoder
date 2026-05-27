# coding: utf-8
"""
Unit tests cho recipes của CP24.

Kiểm tra:
- generate_default_profiles trả về profile đúng theo stack
- generate_strict_profiles trả về strict profile
- generate_security_config trả về security config đúng
- auto_generate_quality_collection generate đầy đủ cho 4 stacks

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.packs.cp24_quality_security.models import (
    AlertSeverity,
    DataQualityProfile,
    DataQualityRule,
    FormatterType,
    LinterType,
    QualityCheck,
    QualityCollection,
    QualityGateConfig,
    QualityThreshold,
    SecurityScanConfig,
    SecurityTool,
    SeverityLevel,
    StackType,
)
from midicoder.packs.cp24_quality_security.recipes import (
    RecipeOutput,
    auto_generate_quality_collection,
    data_quality_recipe,
    generate_default_profiles,
    generate_security_config,
    generate_strict_profiles,
)


class TestGenerateDefaultProfiles:
    """Test cho generate_default_profiles recipe."""

    def test_fastapi_default(self) -> None:
        """Kiểm tra FastAPI có ruff + black mặc định."""
        profile = generate_default_profiles(StackType.FASTAPI)
        assert profile.name == "standard"
        assert profile.stack == StackType.FASTAPI
        assert profile.linter == LinterType.RUFF
        assert profile.formatter == FormatterType.BLACK
        assert profile.min_score == 80

    def test_nestjs_default(self) -> None:
        """Kiểm tra NestJS có eslint + prettier mặc định."""
        profile = generate_default_profiles(StackType.NESTJS)
        assert profile.linter == LinterType.ESLINT
        assert profile.formatter == FormatterType.PRETTIER

    def test_angular_default(self) -> None:
        """Kiểm tra Angular có eslint + prettier mặc định."""
        profile = generate_default_profiles(StackType.ANGULAR)
        assert profile.linter == LinterType.ESLINT
        assert profile.formatter == FormatterType.PRETTIER

    def test_react_default(self) -> None:
        """Kiểm tra React có eslint + prettier mặc định."""
        profile = generate_default_profiles(StackType.REACT)
        assert profile.linter == LinterType.ESLINT
        assert profile.formatter == FormatterType.PRETTIER


class TestGenerateStrictProfiles:
    """Test cho generate_strict_profiles recipe."""

    def test_strict_min_score(self) -> None:
        """Kiểm tra strict profile có min_score cao."""
        profile = generate_strict_profiles(StackType.FASTAPI)
        assert profile.name == "strict"
        assert profile.min_score == 95


class TestGenerateSecurityConfig:
    """Test cho generate_security_config recipe."""

    def test_fastapi_security_tools(self) -> None:
        """Kiểm tra FastAPI có bandit + safety."""
        config = generate_security_config(StackType.FASTAPI)
        assert config.stack == StackType.FASTAPI
        assert SecurityTool.BANDIT in config.tools
        assert SecurityTool.SAFETY in config.tools
        assert config.fail_on_severity == SeverityLevel.HIGH

    def test_nestjs_security_tools(self) -> None:
        """Kiểm tra NestJS có npm-audit + eslint-security."""
        config = generate_security_config(StackType.NESTJS)
        assert SecurityTool.NPM_AUDIT in config.tools
        assert SecurityTool.ESLINT_SECURITY in config.tools

    def test_angular_security_tools(self) -> None:
        """Kiểm tra Angular có eslint-security + lockfile-lint."""
        config = generate_security_config(StackType.ANGULAR)
        assert SecurityTool.ESLINT_SECURITY in config.tools
        assert SecurityTool.LOCKFILE_LINT in config.tools

    def test_react_security_tools(self) -> None:
        """Kiểm tra React có eslint-security + lockfile-lint."""
        config = generate_security_config(StackType.REACT)
        assert SecurityTool.ESLINT_SECURITY in config.tools
        assert SecurityTool.LOCKFILE_LINT in config.tools


class TestAutoGenerateQualityCollection:
    """Test cho auto_generate_quality_collection recipe."""

    def test_generate_all_stacks(self) -> None:
        """Kiểm tra generate đầy đủ cho 4 stacks."""
        collection = auto_generate_quality_collection()
        assert len(collection.profiles) == 4
        assert len(collection.security_configs) == 4
        assert collection.gate_config is not None

    def test_generate_specific_stacks(self) -> None:
        """Kiểm tra generate chỉ cho stacks được chỉ định."""
        collection = auto_generate_quality_collection(stacks=[StackType.FASTAPI, StackType.REACT])
        assert len(collection.profiles) == 2
        assert len(collection.security_configs) == 2

    def test_generate_with_custom_profile_name(self) -> None:
        """Kiểm tra generate với tên profile tùy chỉnh."""
        collection = auto_generate_quality_collection(profile_name="strict", min_score=95)
        for profile in collection.profiles:
            assert profile.name == "strict"
            assert profile.min_score == 95

    def test_gate_config_defaults(self) -> None:
        """Kiểm tra gate config mặc định."""
        collection = auto_generate_quality_collection()
        assert collection.gate_config is not None
        assert collection.gate_config.enabled is True
        assert collection.gate_config.block_on_fail is True
        assert collection.gate_config.report_path == "reports/quality_gate.json"
        assert collection.gate_config.min_coverage == 80

    def test_empty_stacks_list(self) -> None:
        """Kiểm tra generate với danh sách stacks rỗng."""
        collection = auto_generate_quality_collection(stacks=[])
        assert len(collection.profiles) == 0
        assert len(collection.security_configs) == 0
        # Vẫn có gate config
        assert collection.gate_config is not None


class TestDataQualityRecipe:
    """Test cho data_quality_recipe."""

    def test_returns_recipe_output(self) -> None:
        """Kiểm tra recipe trả về RecipeOutput."""
        result = data_quality_recipe()
        assert isinstance(result, RecipeOutput)

    def test_recipe_name_and_description(self) -> None:
        """Kiểm tra tên và mô tả recipe."""
        result = data_quality_recipe()
        assert result.name == "data_quality_default"
        assert "completeness" in result.description
        assert "accuracy" in result.description
        assert "freshness" in result.description

    def test_contains_all_rule_types(self) -> None:
        """Kiểm tra recipe chứa tất cả 6 loại quality rule."""
        result = data_quality_recipe()
        rules = {c.rule for c in result.checks}
        assert DataQualityRule.COMPLETENESS in rules
        assert DataQualityRule.ACCURACY in rules
        assert DataQualityRule.FRESHNESS in rules
        assert DataQualityRule.UNIQUENESS in rules
        assert DataQualityRule.VALIDITY in rules
        assert DataQualityRule.CONSISTENCY in rules

    def test_check_count(self) -> None:
        """Kiểm tra số lượng quality checks."""
        result = data_quality_recipe()
        assert len(result.checks) == 6

    def test_threshold_count(self) -> None:
        """Kiểm tra số lượng thresholds."""
        result = data_quality_recipe()
        assert len(result.thresholds) == 6

    def test_threshold_linked_to_checks(self) -> None:
        """Kiểm tra mỗi threshold liên kết với một check."""
        result = data_quality_recipe()
        check_ids = {c.id for c in result.checks}
        for threshold in result.thresholds:
            assert threshold.check_id in check_ids

    def test_profile_contains_check_ids(self) -> None:
        """Kiểm tra profile chứa đúng check IDs."""
        result = data_quality_recipe()
        check_ids = {c.id for c in result.checks}
        assert set(result.profile.checks) == check_ids

    def test_profile_defaults(self) -> None:
        """Kiểm tra giá trị mặc định của profile."""
        result = data_quality_recipe()
        assert result.profile.schedule_cron == "0 0 * * *"
        assert result.profile.alert_on_failure is True
        assert result.profile.generate_report is True
        assert result.profile.report_format == "json"

    def test_severity_distribution(self) -> None:
        """Kiểm tra có cả CRITICAL và WARNING severity."""
        result = data_quality_recipe()
        severities = {t.severity for t in result.thresholds}
        assert AlertSeverity.CRITICAL in severities
        assert AlertSeverity.WARNING in severities

    def test_to_dict(self) -> None:
        """Kiểm tra serialization RecipeOutput."""
        result = data_quality_recipe()
        d = result.to_dict()
        assert d["name"] == "data_quality_default"
        assert len(d["checks"]) == 6
        assert len(d["thresholds"]) == 6
        assert "profile" in d

    def test_raw_data_contains_all_sections(self) -> None:
        """Kiểm tra raw_data chứa đầy đủ sections."""
        result = data_quality_recipe()
        assert "checks" in result.raw_data
        assert "thresholds" in result.raw_data
        assert "profile" in result.raw_data

    def test_completeness_check_details(self) -> None:
        """Kiểm tra chi tiết completeness check."""
        result = data_quality_recipe()
        completeness_checks = [c for c in result.checks if c.rule == DataQualityRule.COMPLETENESS]
        assert len(completeness_checks) == 1
        check = completeness_checks[0]
        assert "email" in check.target
        assert check.threshold == 0.98

    def test_freshness_check_details(self) -> None:
        """Kiểm tra chi tiết freshness check."""
        result = data_quality_recipe()
        freshness_checks = [c for c in result.checks if c.rule == DataQualityRule.FRESHNESS]
        assert len(freshness_checks) == 1
        check = freshness_checks[0]
        assert check.threshold == 24.0
        assert "unit" in check.metadata

    def test_uniqueness_threshold_is_critical(self) -> None:
        """Kiểm tra uniqueness threshold có severity CRITICAL."""
        result = data_quality_recipe()
        uniq_check = [c for c in result.checks if c.rule == DataQualityRule.UNIQUENESS][0]
        uniq_threshold = [t for t in result.thresholds if t.check_id == uniq_check.id][0]
        assert uniq_threshold.severity == AlertSeverity.CRITICAL
