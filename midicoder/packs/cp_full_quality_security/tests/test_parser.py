# coding: utf-8
"""
Unit tests cho parser của CP24 — Code Quality & Security Scanner Generator.

Kiểm tra:
- Parse YAML string thành QualityCollection
- Parse dict metadata thành QualityCollection
- Parse từ MIR metadata
- Error handling khi parse dữ liệu không hợp lệ
- Default generation khi không có data

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.packs.cp_full_quality_security.models import (
    FormatterType,
    LinterType,
    QualityCollection,
    QualityGateConfig,
    QualityProfile,
    SecurityScanConfig,
    SecurityTool,
    SeverityLevel,
    StackType,
)
from midicoder.packs.cp_full_quality_security.parser import QualityProfileParser
from midicoder.errors import ErrorCode, MidicoderError


class TestQualityProfileParser:
    """Test cho QualityProfileParser."""

    def setup_method(self) -> None:
        """Setup parser trước mỗi test."""
        self.parser = QualityProfileParser()

    def test_parse_empty_string(self) -> None:
        """Kiểm tra parse string rỗng trả về collection rỗng."""
        result = self.parser.parse("")
        assert isinstance(result, QualityCollection)

    def test_parse_none_string(self) -> None:
        """Kiểm tra parse None-like string."""
        result = self.parser.parse("   ")
        assert isinstance(result, QualityCollection)

    def test_parse_valid_yaml(self) -> None:
        """Kiểm tra parse YAML hợp lệ."""
        yaml_str = """
profiles:
  - name: strict
    stack: fastapi
    linter: ruff
    formatter: black
    min_score: 95
  - name: standard
    stack: react
    linter: eslint
    formatter: prettier
security:
  - stack: fastapi
    tools: [bandit, safety]
    fail_on_severity: high
gate:
  enabled: true
  report_path: reports/quality.json
"""
        result = self.parser.parse(yaml_str)
        assert len(result.profiles) == 2
        assert result.profiles[0].name == "strict"
        assert result.profiles[0].stack == StackType.FASTAPI
        assert result.profiles[0].linter == LinterType.RUFF
        assert result.profiles[0].min_score == 95
        assert len(result.security_configs) == 1
        assert result.gate_config is not None
        assert result.gate_config.report_path == "reports/quality.json"

    def test_parse_dict(self) -> None:
        """Kiểm tra parse dict trực tiếp."""
        data = {
            "profiles": [
                {
                    "name": "minimal",
                    "stack": "nestjs",
                    "linter": "eslint",
                    "formatter": "prettier",
                    "min_score": 70,
                }
            ],
            "gate": {"enabled": True},
        }
        result = self.parser.parse(data)
        assert len(result.profiles) == 1
        assert result.profiles[0].stack == StackType.NESTJS
        assert result.profiles[0].min_score == 70

    def test_parse_invalid_yaml_raises_error(self) -> None:
        """Kiểm tra parse YAML không hợp lệ throw error."""
        invalid_yaml = ":::invalid yaml{{{"
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(invalid_yaml)
        assert exc_info.value.code == ErrorCode.MDC-F10_DSL_PARSE_ERROR

    def test_parse_invalid_stack_raises_error(self) -> None:
        """Kiểm tra stack không hợp lệ throw error."""
        data = {
            "profiles": [
                {"name": "test", "stack": "invalid_stack", "linter": "ruff", "formatter": "black"}
            ]
        }
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(data)
        assert exc_info.value.code == ErrorCode.MDC-F10_INVALID_STACK

    def test_parse_invalid_linter_raises_error(self) -> None:
        """Kiểm tra linter không hợp lệ throw error."""
        data = {
            "profiles": [
                {"name": "test", "stack": "fastapi", "linter": "invalid_linter", "formatter": "black"}
            ]
        }
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(data)
        assert exc_info.value.code == ErrorCode.MDC-F10_PROFILE_INVALID

    def test_parse_empty_profile_name_raises_error(self) -> None:
        """Kiểm tra profile name rỗng throw error."""
        data = {
            "profiles": [
                {"name": "", "stack": "fastapi", "linter": "ruff", "formatter": "black"}
            ]
        }
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(data)
        assert exc_info.value.code == ErrorCode.MDC-F10_EMPTY_PROFILE_NAME

    def test_parse_security_config_with_custom_rules(self) -> None:
        """Kiểm tra parse security config có custom rules."""
        data = {
            "profiles": [
                {"name": "standard", "stack": "react", "linter": "eslint", "formatter": "prettier"}
            ],
            "security": [
                {
                    "stack": "react",
                    "tools": ["eslint-security", "lockfile-lint"],
                    "fail_on_severity": "critical",
                    "rules": [
                        {
                            "rule_id": "detect-eval",
                            "severity": "critical",
                            "tool": "eslint-security",
                            "description": "Detect eval usage",
                        }
                    ],
                }
            ],
            "gate": {"enabled": True},
        }
        result = self.parser.parse(data)
        # Có 1 profile explicit + security config cho react
        assert len(result.profiles) >= 1
        assert any(s.stack == StackType.REACT for s in result.security_configs)
        # Tìm security config cho React
        react_sec = [s for s in result.security_configs if s.stack == StackType.REACT]
        assert len(react_sec) >= 1
        sec = react_sec[0]
        assert len(sec.tools) == 2
        assert sec.fail_on_severity == SeverityLevel.CRITICAL

    def test_parse_from_metadata(self) -> None:
        """Kiểm tra parse từ MIR metadata."""
        metadata = {
            "quality": {
                "profiles": [
                    {"name": "standard", "stack": "fastapi", "linter": "ruff", "formatter": "black"}
                ],
                "security": [
                    {"stack": "fastapi", "tools": ["bandit"], "fail_on_severity": "high"}
                ],
            }
        }
        result = self.parser.parse_from_metadata(metadata)
        assert len(result.profiles) == 1
        assert len(result.security_configs) == 1

    def test_parse_from_metadata_with_quality_config_key(self) -> None:
        """Kiểm tra parse từ MIR metadata dùng key quality_config."""
        metadata = {
            "quality_config": {
                "profiles": [
                    {"name": "strict", "stack": "angular", "linter": "eslint", "formatter": "prettier"}
                ]
            }
        }
        result = self.parser.parse_from_metadata(metadata)
        assert len(result.profiles) == 1
        assert result.profiles[0].stack == StackType.ANGULAR

    def test_parse_from_metadata_empty_returns_defaults(self) -> None:
        """Kiểm tra metadata rỗng trả về defaults."""
        metadata = {"entities": []}
        result = self.parser.parse_from_metadata(metadata)
        # Khi không có quality data, generate defaults cho 4 stacks
        assert len(result.profiles) == 4
        assert len(result.security_configs) == 4

    def test_parse_generates_defaults_when_no_profiles(self) -> None:
        """Kiểm tra tự generate defaults khi không có profiles."""
        data = {"security": []}
        result = self.parser.parse(data)
        # Không có profiles → generate defaults
        assert len(result.profiles) == 4
        # Có gate config mặc định
        assert result.gate_config is not None
        assert result.gate_config.block_on_fail is True

    def test_parse_with_exclude_patterns(self) -> None:
        """Kiểm tra parse profile có exclude patterns."""
        data = {
            "profiles": [
                {
                    "name": "standard",
                    "stack": "fastapi",
                    "linter": "ruff",
                    "formatter": "black",
                    "exclude": ["tests/", "venv/", "migrations/"],
                }
            ]
        }
        result = self.parser.parse(data)
        assert result.profiles[0].exclude == ["tests/", "venv/", "migrations/"]

    def test_parse_with_rule_overrides(self) -> None:
        """Kiểm tra parse profile có rule overrides."""
        data = {
            "profiles": [
                {
                    "name": "standard",
                    "stack": "react",
                    "linter": "eslint",
                    "formatter": "prettier",
                    "rules": {"no-explicit-any": "warn", "no-console": "error"},
                }
            ]
        }
        result = self.parser.parse(data)
        assert result.profiles[0].rules == {"no-explicit-any": "warn", "no-console": "error"}

    def test_parse_invalid_severity_raises_error(self) -> None:
        """Kiểm tra severity không hợp lệ throw error."""
        data = {
            "security": [
                {"stack": "fastapi", "tools": ["bandit"], "fail_on_severity": "invalid"}
            ]
        }
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(data)
        assert exc_info.value.code == ErrorCode.MDC-F10_SCAN_CONFIG_INVALID

    def test_parse_default_linter_per_stack(self) -> None:
        """Kiểm tra tự áp dụng linter mặc định theo stack."""
        data = {
            "profiles": [
                {"name": "auto", "stack": "fastapi"},
                {"name": "auto", "stack": "nestjs"},
            ]
        }
        result = self.parser.parse(data)
        # FastAPI → ruff mặc định
        assert result.profiles[0].linter == LinterType.RUFF
        # NestJS → eslint mặc định
        assert result.profiles[1].linter == LinterType.ESLINT

    def test_parse_alternate_keys(self) -> None:
        """Kiểm tra parse với alternate key names."""
        data = {
            "quality_profiles": [
                {"name": "alt", "stack": "fastapi", "linter": "ruff", "formatter": "black"}
            ],
            "security_configs": [
                {"stack": "fastapi", "tools": ["bandit"], "fail_on_severity": "medium"}
            ],
            "quality_gate": {"enabled": False},
        }
        result = self.parser.parse(data)
        assert len(result.profiles) == 1
        assert len(result.security_configs) == 1
        assert result.gate_config is not None
        assert result.gate_config.enabled is False
