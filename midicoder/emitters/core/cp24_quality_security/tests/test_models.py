# coding: utf-8
"""
Unit tests cho models của CP24 — Code Quality & Security Scanner Generator.

Kiểm tra:
- Tạo instance và serialization (to_dict / from_dict)
- Validation và error codes
- Helper methods trên các dataclass

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.emitters.core.cp24_quality_security.models import (
    FormatterType,
    LinterType,
    QualityCollection,
    QualityGateConfig,
    QualityProfile,
    QualityReport,
    QualityViolation,
    SecurityScanConfig,
    SecurityScanRule,
    SecurityTool,
    SeverityLevel,
    StackType,
)


class TestQualityProfile:
    """Test cho QualityProfile dataclass."""

    def test_create_default_profile(self) -> None:
        """Kiểm tra tạo profile với giá trị mặc định."""
        profile = QualityProfile(
            name="standard",
            stack=StackType.FASTAPI,
            linter=LinterType.RUFF,
            formatter=FormatterType.BLACK,
        )
        assert profile.name == "standard"
        assert profile.stack == StackType.FASTAPI
        assert profile.linter == LinterType.RUFF
        assert profile.formatter == FormatterType.BLACK
        assert profile.min_score == 80
        assert profile.rules == {}
        assert profile.exclude == []

    def test_create_profile_with_all_fields(self) -> None:
        """Kiểm tra tạo profile với đầy đủ fields."""
        profile = QualityProfile(
            name="strict",
            stack=StackType.NESTJS,
            linter=LinterType.ESLINT,
            formatter=FormatterType.PRETTIER,
            min_score=95,
            rules={"no-explicit-any": "warn"},
            exclude=["dist/", "node_modules/"],
        )
        assert profile.name == "strict"
        assert profile.min_score == 95
        assert profile.rules == {"no-explicit-any": "warn"}
        assert profile.exclude == ["dist/", "node_modules/"]

    def test_to_dict(self) -> None:
        """Kiểm tra serialization sang dict."""
        profile = QualityProfile(
            name="standard",
            stack=StackType.REACT,
            linter=LinterType.ESLINT,
            formatter=FormatterType.PRETTIER,
            min_score=85,
        )
        d = profile.to_dict()
        assert d["name"] == "standard"
        assert d["stack"] == "react"
        assert d["linter"] == "eslint"
        assert d["formatter"] == "prettier"
        assert d["min_score"] == 85

    def test_from_dict(self) -> None:
        """Kiểm tra deserialization từ dict."""
        data = {
            "name": "minimal",
            "stack": "angular",
            "linter": "eslint",
            "formatter": "prettier",
            "min_score": 70,
            "rules": {},
            "exclude": ["tests/"],
        }
        profile = QualityProfile.from_dict(data)
        assert profile.name == "minimal"
        assert profile.stack == StackType.ANGULAR
        assert profile.linter == LinterType.ESLINT
        assert profile.formatter == FormatterType.PRETTIER
        assert profile.min_score == 70
        assert profile.exclude == ["tests/"]

    def test_roundtrip(self) -> None:
        """Kiểm tra to_dict → from_dict giữ nguyên dữ liệu."""
        original = QualityProfile(
            name="strict",
            stack=StackType.FASTAPI,
            linter=LinterType.RUFF,
            formatter=FormatterType.BLACK,
            min_score=90,
            rules={"E501": "ignore"},
            exclude=["build/"],
        )
        restored = QualityProfile.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.stack == original.stack
        assert restored.linter == original.linter
        assert restored.formatter == original.formatter
        assert restored.min_score == original.min_score
        assert restored.rules == original.rules
        assert restored.exclude == original.exclude


class TestSecurityScanRule:
    """Test cho SecurityScanRule dataclass."""

    def test_create_rule(self) -> None:
        """Kiểm tra tạo rule."""
        rule = SecurityScanRule(
            rule_id="bandit-B104",
            severity=SeverityLevel.HIGH,
            tool=SecurityTool.BANDIT,
            enabled=True,
            description="Hardcoded password binding",
        )
        assert rule.rule_id == "bandit-B104"
        assert rule.severity == SeverityLevel.HIGH
        assert rule.tool == SecurityTool.BANDIT
        assert rule.enabled is True

    def test_to_dict(self) -> None:
        """Kiểm tra serialization."""
        rule = SecurityScanRule(
            rule_id="eslint-security-eval",
            severity=SeverityLevel.CRITICAL,
            tool=SecurityTool.ESLINT_SECURITY,
        )
        d = rule.to_dict()
        assert d["rule_id"] == "eslint-security-eval"
        assert d["severity"] == "critical"
        assert d["tool"] == "eslint-security"
        assert d["enabled"] is True

    def test_from_dict(self) -> None:
        """Kiểm tra deserialization."""
        data = {
            "rule_id": "npm-audit-prototype-pollution",
            "severity": "medium",
            "tool": "npm-audit",
            "enabled": False,
            "description": "Prototype pollution vulnerability",
        }
        rule = SecurityScanRule.from_dict(data)
        assert rule.rule_id == "npm-audit-prototype-pollution"
        assert rule.severity == SeverityLevel.MEDIUM
        assert rule.tool == SecurityTool.NPM_AUDIT
        assert rule.enabled is False


class TestSecurityScanConfig:
    """Test cho SecurityScanConfig dataclass."""

    def test_create_config(self) -> None:
        """Kiểm tra tạo security config."""
        config = SecurityScanConfig(
            stack=StackType.FASTAPI,
            tools=[SecurityTool.BANDIT, SecurityTool.SAFETY],
            fail_on_severity=SeverityLevel.HIGH,
        )
        assert config.stack == StackType.FASTAPI
        assert len(config.tools) == 2
        assert config.fail_on_severity == SeverityLevel.HIGH
        assert config.rules == []
        assert config.exclude == []

    def test_to_dict(self) -> None:
        """Kiểm tra serialization."""
        rule = SecurityScanRule(
            rule_id="test-rule",
            severity=SeverityLevel.HIGH,
            tool=SecurityTool.BANDIT,
        )
        config = SecurityScanConfig(
            stack=StackType.REACT,
            tools=[SecurityTool.ESLINT_SECURITY, SecurityTool.LOCKFILE_LINT],
            rules=[rule],
        )
        d = config.to_dict()
        assert d["stack"] == "react"
        assert len(d["tools"]) == 2
        assert len(d["rules"]) == 1
        assert d["rules"][0]["rule_id"] == "test-rule"

    def test_from_dict(self) -> None:
        """Kiểm tra deserialization."""
        data = {
            "stack": "nestjs",
            "tools": ["npm-audit", "eslint-security"],
            "rules": [
                {
                    "rule_id": "rule-1",
                    "severity": "critical",
                    "tool": "eslint-security",
                    "enabled": True,
                    "description": "Test rule",
                }
            ],
            "fail_on_severity": "critical",
            "exclude": ["dist/"],
        }
        config = SecurityScanConfig.from_dict(data)
        assert config.stack == StackType.NESTJS
        assert len(config.tools) == 2
        assert len(config.rules) == 1
        assert config.rules[0].rule_id == "rule-1"
        assert config.fail_on_severity == SeverityLevel.CRITICAL


class TestQualityGateConfig:
    """Test cho QualityGateConfig dataclass."""

    def test_create_default(self) -> None:
        """Kiểm tra tạo gate config với giá trị mặc định."""
        config = QualityGateConfig()
        assert config.enabled is True
        assert config.block_on_fail is True
        assert config.report_path == "reports/quality_gate.json"
        assert config.min_coverage == 80

    def test_add_profile(self) -> None:
        """Kiểm tra thêm profile."""
        config = QualityGateConfig()
        profile = QualityProfile(
            name="test",
            stack=StackType.FASTAPI,
            linter=LinterType.RUFF,
            formatter=FormatterType.BLACK,
        )
        config.add_profile(profile)
        assert len(config.profiles) == 1

    def test_get_profile_for_stack(self) -> None:
        """Kiểm tra tìm profile theo stack."""
        config = QualityGateConfig()
        fp = QualityProfile(
            name="fastapi-profile",
            stack=StackType.FASTAPI,
            linter=LinterType.RUFF,
            formatter=FormatterType.BLACK,
        )
        rp = QualityProfile(
            name="react-profile",
            stack=StackType.REACT,
            linter=LinterType.ESLINT,
            formatter=FormatterType.PRETTIER,
        )
        config.add_profile(fp)
        config.add_profile(rp)
        assert config.get_profile_for_stack(StackType.FASTAPI) == fp
        assert config.get_profile_for_stack(StackType.REACT) == rp
        assert config.get_profile_for_stack(StackType.ANGULAR) is None

    def test_to_dict_and_from_dict(self) -> None:
        """Kiểm tra serialization roundtrip."""
        config = QualityGateConfig(
            enabled=True,
            block_on_fail=True,
            report_path="custom/report.json",
            min_coverage=90,
        )
        profile = QualityProfile(
            name="standard",
            stack=StackType.FASTAPI,
            linter=LinterType.RUFF,
            formatter=FormatterType.BLACK,
        )
        config.add_profile(profile)

        restored = QualityGateConfig.from_dict(config.to_dict())
        assert restored.enabled == config.enabled
        assert restored.block_on_fail == config.block_on_fail
        assert restored.report_path == config.report_path
        assert restored.min_coverage == config.min_coverage
        assert len(restored.profiles) == 1


class TestQualityViolation:
    """Test cho QualityViolation dataclass."""

    def test_create_violation(self) -> None:
        """Kiểm tra tạo violation."""
        v = QualityViolation(
            rule_id="E501",
            file_path="src/main.py",
            line=42,
            column=120,
            severity=SeverityLevel.MEDIUM,
            message="Line too long",
        )
        assert v.rule_id == "E501"
        assert v.file_path == "src/main.py"
        assert v.line == 42
        assert v.severity == SeverityLevel.MEDIUM


class TestQualityReport:
    """Test cho QualityReport dataclass."""

    def test_create_passed_report(self) -> None:
        """Kiểm tra tạo report pass."""
        report = QualityReport(
            passed=True,
            total_violations=0,
            stack="fastapi",
            profile_name="standard",
        )
        assert report.passed is True
        assert report.total_violations == 0

    def test_to_dict_with_violations(self) -> None:
        """Kiểm tra serialization có violations."""
        v = QualityViolation(
            rule_id="B104",
            file_path="app/server.py",
            line=10,
            severity=SeverityLevel.HIGH,
            message="Hardcoded password",
        )
        report = QualityReport(
            passed=False,
            total_violations=1,
            violations=[v],
            stack="fastapi",
        )
        d = report.to_dict()
        assert d["passed"] is False
        assert d["total_violations"] == 1
        assert len(d["violations"]) == 1
        assert d["violations"][0]["rule_id"] == "B104"


class TestQualityCollection:
    """Test cho QualityCollection dataclass."""

    def test_create_empty(self) -> None:
        """Kiểm tra tạo collection rỗng."""
        c = QualityCollection()
        assert c.profiles == []
        assert c.security_configs == []
        assert c.gate_config is None

    def test_add_and_filter(self) -> None:
        """Kiểm tra thêm và filter theo stack."""
        c = QualityCollection()
        p1 = QualityProfile(
            name="s1", stack=StackType.FASTAPI,
            linter=LinterType.RUFF, formatter=FormatterType.BLACK,
        )
        p2 = QualityProfile(
            name="s2", stack=StackType.FASTAPI,
            linter=LinterType.PYLINT, formatter=FormatterType.BLACK,
        )
        p3 = QualityProfile(
            name="s3", stack=StackType.REACT,
            linter=LinterType.ESLINT, formatter=FormatterType.PRETTIER,
        )
        c.add_profile(p1)
        c.add_profile(p2)
        c.add_profile(p3)

        fastapi_profiles = c.get_profiles_for_stack(StackType.FASTAPI)
        assert len(fastapi_profiles) == 2
        react_profiles = c.get_profiles_for_stack(StackType.REACT)
        assert len(react_profiles) == 1
        angular_profiles = c.get_profiles_for_stack(StackType.ANGULAR)
        assert len(angular_profiles) == 0

    def test_to_dict_and_from_dict(self) -> None:
        """Kiểm tra serialization roundtrip."""
        c = QualityCollection()
        profile = QualityProfile(
            name="test",
            stack=StackType.FASTAPI,
            linter=LinterType.RUFF,
            formatter=FormatterType.BLACK,
        )
        c.add_profile(profile)
        c.gate_config = QualityGateConfig(min_coverage=85)

        restored = QualityCollection.from_dict(c.to_dict())
        assert len(restored.profiles) == 1
        assert restored.profiles[0].name == "test"
        assert restored.gate_config is not None
        assert restored.gate_config.min_coverage == 85


class TestEnums:
    """Test cho các enum."""

    def test_stack_type_values(self) -> None:
        """Kiểm tra giá trị enum StackType."""
        assert StackType.FASTAPI.value == "fastapi"
        assert StackType.NESTJS.value == "nestjs"
        assert StackType.ANGULAR.value == "angular"
        assert StackType.REACT.value == "react"

    def test_severity_level_values(self) -> None:
        """Kiểm tra giá trị enum SeverityLevel."""
        assert SeverityLevel.CRITICAL.value == "critical"
        assert SeverityLevel.HIGH.value == "high"
        assert SeverityLevel.MEDIUM.value == "medium"
        assert SeverityLevel.LOW.value == "low"
        assert SeverityLevel.INFO.value == "info"

    def test_linter_type_values(self) -> None:
        """Kiểm tra giá trị enum LinterType."""
        assert LinterType.RUFF.value == "ruff"
        assert LinterType.ESLINT.value == "eslint"
        assert LinterType.PYLINT.value == "pylint"
        assert LinterType.FLAKE8.value == "flake8"

    def test_security_tool_values(self) -> None:
        """Kiểm tra giá trị enum SecurityTool."""
        assert SecurityTool.BANDIT.value == "bandit"
        assert SecurityTool.SAFETY.value == "safety"
        assert SecurityTool.NPM_AUDIT.value == "npm-audit"
        assert SecurityTool.ESLINT_SECURITY.value == "eslint-security"
        assert SecurityTool.LOCKFILE_LINT.value == "lockfile-lint"
