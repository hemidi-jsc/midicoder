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

from midicoder.emitters.core.cp24_quality_security.models import (
    FormatterType,
    LinterType,
    QualityCollection,
    QualityGateConfig,
    SecurityScanConfig,
    SecurityTool,
    SeverityLevel,
    StackType,
)
from midicoder.emitters.core.cp24_quality_security.recipes import (
    auto_generate_quality_collection,
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
