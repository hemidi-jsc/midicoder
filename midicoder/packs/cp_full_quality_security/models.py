# coding: utf-8
"""
Mô-đun models cho Code Quality & Security Scanner Generator (CP24).

Định nghĩa các dataclass biểu diễn:
- QualityProfile: Cấu hình quality profile cho từng stack
- SecurityScanRule: Quy tắc security scanning
- SeverityLevel: Enum mức độ nghiêm trọng
- QualityGateConfig: Cấu hình quality gate (block/warn)
- QualityReport: Kết quả quality gate check
- QualityCollection: Output của QualityProfileParser

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ===========================================================================
# Enums
# ===========================================================================


class SeverityLevel(str, Enum):
    """Enum mức độ nghiêm trọng của vi phạm."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    __test__ = False  # Prevent pytest collection


class StackType(str, Enum):
    """Enum các stack được hỗ trợ."""
    FASTAPI = "fastapi"
    NESTJS = "nestjs"
    ANGULAR = "angular"
    REACT = "react"

    __test__ = False  # Prevent pytest collection


class LinterType(str, Enum):
    """Enum các công cụ linting."""
    RUFF = "ruff"
    ESLINT = "eslint"
    PYLINT = "pylint"
    FLAKE8 = "flake8"

    __test__ = False  # Prevent pytest collection


class FormatterType(str, Enum):
    """Enum các công cụ formatting."""
    BLACK = "black"
    PRETTIER = "prettier"
    ISORT = "isort"

    __test__ = False  # Prevent pytest collection


class SecurityTool(str, Enum):
    """Enum các công cụ security scanning."""
    BANDIT = "bandit"
    SAFETY = "safety"
    NPM_AUDIT = "npm-audit"
    ESLINT_SECURITY = "eslint-security"
    LOCKFILE_LINT = "lockfile-lint"

    __test__ = False  # Prevent pytest collection


# ===========================================================================
# QualityProfile
# ===========================================================================


@dataclass
class QualityProfile:
    """
    Cấu hình quality profile cho 1 stack.

    Attributes:
        name: Tên profile ("strict", "standard", "minimal")
        stack: Stack target (fastapi, nestjs, angular, react)
        linter: Công cụ linting (ruff, eslint, pylint, flake8)
        formatter: Công cụ formatting (black, prettier, isort)
        min_score: Score tối thiểu 0-100
        rules: Rule overrides (dict)
        exclude: File patterns to exclude (list)
    """
    __test__ = False  # Prevent pytest collection

    name: str
    stack: StackType
    linter: LinterType
    formatter: FormatterType
    min_score: int = 80
    rules: dict[str, Any] = field(default_factory=dict)
    exclude: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển quality profile sang dict format."""
        return {
            "name": self.name,
            "stack": self.stack.value,
            "linter": self.linter.value,
            "formatter": self.formatter.value,
            "min_score": self.min_score,
            "rules": self.rules,
            "exclude": self.exclude,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QualityProfile":
        """Tạo QualityProfile từ dict."""
        return cls(
            name=data.get("name", "standard"),
            stack=StackType(data.get("stack", "fastapi")),
            linter=LinterType(data.get("linter", "ruff")),
            formatter=FormatterType(data.get("formatter", "black")),
            min_score=data.get("min_score", 80),
            rules=data.get("rules", {}),
            exclude=data.get("exclude", []),
        )


# ===========================================================================
# SecurityScanRule
# ===========================================================================


@dataclass
class SecurityScanRule:
    """
    Quy tắc security scanning.

    Attributes:
        rule_id: Định danh rule (vd: "bandit-B104", "eslint-security-malicious-domain")
        severity: Mức độ nghiêm trọng
        tool: Công cụ security scanning
        enabled: Có kích hoạt rule không (default True)
        description: Mô tả rule
    """
    __test__ = False  # Prevent pytest collection

    rule_id: str
    severity: SeverityLevel
    tool: SecurityTool
    enabled: bool = True
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Chuyển security rule sang dict format."""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "tool": self.tool.value,
            "enabled": self.enabled,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SecurityScanRule":
        """Tạo SecurityScanRule từ dict."""
        return cls(
            rule_id=data.get("rule_id", ""),
            severity=SeverityLevel(data.get("severity", "medium")),
            tool=SecurityTool(data.get("tool", "bandit")),
            enabled=data.get("enabled", True),
            description=data.get("description", ""),
        )


# ===========================================================================
# SecurityScanConfig
# ===========================================================================


@dataclass
class SecurityScanConfig:
    """
    Cấu hình security scanning cho 1 stack.

    Attributes:
        stack: Stack target
        tools: Danh sách security tools
        rules: Danh sách security rules
        fail_on_severity: Severity threshold để fail scan
        exclude: File patterns to exclude
    """
    __test__ = False  # Prevent pytest collection

    stack: StackType
    tools: list[SecurityTool] = field(default_factory=list)
    rules: list[SecurityScanRule] = field(default_factory=list)
    fail_on_severity: SeverityLevel = SeverityLevel.HIGH
    exclude: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển security config sang dict format."""
        return {
            "stack": self.stack.value,
            "tools": [t.value for t in self.tools],
            "rules": [r.to_dict() for r in self.rules],
            "fail_on_severity": self.fail_on_severity.value,
            "exclude": self.exclude,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SecurityScanConfig":
        """Tạo SecurityScanConfig từ dict."""
        tools_raw = data.get("tools", [])
        rules_raw = data.get("rules", [])
        return cls(
            stack=StackType(data.get("stack", "fastapi")),
            tools=[SecurityTool(t) for t in tools_raw] if tools_raw else [],
            rules=[SecurityScanRule.from_dict(r) for r in rules_raw] if rules_raw else [],
            fail_on_severity=SeverityLevel(data.get("fail_on_severity", "high")),
            exclude=data.get("exclude", []),
        )


# ===========================================================================
# QualityGateConfig
# ===========================================================================


@dataclass
class QualityGateConfig:
    """
    Cấu hình quality gate.

    Attributes:
        enabled: Có kích hoạt quality gate không (default True)
        block_on_fail: Block pipeline khi fail (luôn True cho CP24)
        profiles: Danh sách quality profiles
        security_configs: Danh sách security scan configs
        report_path: Đường dẫn output report
        min_coverage: Coverage threshold (từ CP23 reference)
    """
    __test__ = False  # Prevent pytest collection

    enabled: bool = True
    block_on_fail: bool = True
    profiles: list[QualityProfile] = field(default_factory=list)
    security_configs: list[SecurityScanConfig] = field(default_factory=list)
    report_path: str = "reports/quality_gate.json"
    min_coverage: int = 80

    def add_profile(self, profile: QualityProfile) -> None:
        """Thêm quality profile vào config."""
        self.profiles.append(profile)

    def add_security_config(self, config: SecurityScanConfig) -> None:
        """Thêm security scan config vào config."""
        self.security_configs.append(config)

    def get_profile_for_stack(self, stack: StackType) -> Optional[QualityProfile]:
        """Tìm quality profile cho stack."""
        for p in self.profiles:
            if p.stack == stack:
                return p
        return None

    def get_security_for_stack(self, stack: StackType) -> Optional[SecurityScanConfig]:
        """Tìm security config cho stack."""
        for s in self.security_configs:
            if s.stack == stack:
                return s
        return None

    def to_dict(self) -> dict[str, Any]:
        """Chuyển quality gate config sang dict format."""
        return {
            "enabled": self.enabled,
            "block_on_fail": self.block_on_fail,
            "profiles": [p.to_dict() for p in self.profiles],
            "security_configs": [s.to_dict() for s in self.security_configs],
            "report_path": self.report_path,
            "min_coverage": self.min_coverage,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QualityGateConfig":
        """Tạo QualityGateConfig từ dict."""
        profiles_raw = data.get("profiles", [])
        security_raw = data.get("security_configs", [])
        return cls(
            enabled=data.get("enabled", True),
            block_on_fail=data.get("block_on_fail", True),
            profiles=[QualityProfile.from_dict(p) for p in profiles_raw] if profiles_raw else [],
            security_configs=[SecurityScanConfig.from_dict(s) for s in security_raw] if security_raw else [],
            report_path=data.get("report_path", "reports/quality_gate.json"),
            min_coverage=data.get("min_coverage", 80),
        )


# ===========================================================================
# QualityViolation
# ===========================================================================


@dataclass
class QualityViolation:
    """
    Một vi phạm chất lượng code.

    Attributes:
        rule_id: Rule ID gây vi phạm
        file_path: Đường dẫn file vi phạm
        line: Line number (optional)
        column: Column number (optional)
        severity: Mức độ nghiêm trọng
        message: Thông điệp vi phạm
    """
    __test__ = False  # Prevent pytest collection

    rule_id: str
    file_path: str
    line: int = 0
    column: int = 0
    severity: SeverityLevel = SeverityLevel.MEDIUM
    message: str = ""


# ===========================================================================
# QualityReport
# ===========================================================================


@dataclass
class QualityReport:
    """
    Kết quả quality gate check.

    Attributes:
        passed: Có pass không
        total_violations: Tổng số vi phạm
        violations: Danh sách violations
        stack: Stack được kiểm tra
        profile_name: Tên profile được sử dụng
    """
    __test__ = False  # Prevent pytest collection

    passed: bool
    total_violations: int
    violations: list[QualityViolation] = field(default_factory=list)
    stack: str = ""
    profile_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Chuyển report sang dict format."""
        return {
            "passed": self.passed,
            "total_violations": self.total_violations,
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "file_path": v.file_path,
                    "line": v.line,
                    "column": v.column,
                    "severity": v.severity.value,
                    "message": v.message,
                }
                for v in self.violations
            ],
            "stack": self.stack,
            "profile_name": self.profile_name,
        }


# ===========================================================================
# QualityCollection — output chính của QualityProfileParser
# ===========================================================================


@dataclass
class QualityCollection:
    """
    Collection chứa tất cả quality profiles, security configs, và gate config.

    Dùng làm output của QualityProfileParser và input cho Stack Emitters.

    Attributes:
        profiles: Danh sách quality profiles
        security_configs: Danh sách security scan configs
        gate_config: Quality gate config
    """
    __test__ = False  # Prevent pytest collection

    profiles: list[QualityProfile] = field(default_factory=list)
    security_configs: list[SecurityScanConfig] = field(default_factory=list)
    gate_config: Optional[QualityGateConfig] = None

    def add_profile(self, profile: QualityProfile) -> None:
        """Thêm quality profile vào collection."""
        self.profiles.append(profile)

    def add_security_config(self, config: SecurityScanConfig) -> None:
        """Thêm security scan config vào collection."""
        self.security_configs.append(config)

    def get_profiles_for_stack(self, stack: StackType) -> list[QualityProfile]:
        """Lọc profiles theo stack."""
        return [p for p in self.profiles if p.stack == stack]

    def get_security_for_stack(self, stack: StackType) -> list[SecurityScanConfig]:
        """Lọc security configs theo stack."""
        return [s for s in self.security_configs if s.stack == stack]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển collection sang dict format."""
        return {
            "profiles": [p.to_dict() for p in self.profiles],
            "security_configs": [s.to_dict() for s in self.security_configs],
            "gate_config": self.gate_config.to_dict() if self.gate_config else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QualityCollection":
        """Tạo QualityCollection từ dict."""
        collection = cls()
        profiles_raw = data.get("profiles", [])
        security_raw = data.get("security_configs", [])
        gate_raw = data.get("gate_config")

        for p in profiles_raw:
            collection.add_profile(QualityProfile.from_dict(p))
        for s in security_raw:
            collection.add_security_config(SecurityScanConfig.from_dict(s))
        if gate_raw:
            collection.gate_config = QualityGateConfig.from_dict(gate_raw)

        return collection


# ===========================================================================
# Data Quality & Profiling — enums
# ===========================================================================


class DataQualityRule(str, Enum):
    """Enum các loại quality check cho dữ liệu."""
    COMPLETENESS = "completeness"  # % non-null values
    ACCURACY = "accuracy"  # values within expected range/format
    FRESHNESS = "freshness"  # max age of data
    CONSISTENCY = "consistency"  # cross-table/entity consistency
    UNIQUENESS = "uniqueness"  # no duplicate records
    VALIDITY = "validity"  # matches regex/pattern

    __test__ = False  # Prevent pytest collection


class AlertSeverity(str, Enum):
    """Enum mức độ cảnh báo cho data quality."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

    __test__ = False  # Prevent pytest collection


# ===========================================================================
# Data Quality & Profiling — dataclasses
# ===========================================================================


@dataclass
class QualityCheck:
    """
    Data quality check rule.

    Attributes:
        id: Định danh check (vd: "qc-users-email-completeness")
        name: Tên hiển thị
        target: Table/entity/column (vd: "users.email")
        rule: Loại quality rule
        threshold: Threshold tối thiểu (0.0-1.0, default 95%)
        sample_size: Số mẫu (0 = full table)
        description: Mô tả check
        enabled: Có kích hoạt không
        metadata: Metadata bổ sung
    """
    __test__ = False  # Prevent pytest collection

    id: str
    name: str
    target: str
    rule: DataQualityRule
    threshold: float = 0.95
    sample_size: int = 0
    description: str = ""
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id or not self.id.strip():
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_EMPTY_QUALITY_CHECK_ID,
                message="QualityCheck id không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển QualityCheck sang dict format."""
        return {
            "id": self.id,
            "name": self.name,
            "target": self.target,
            "rule": self.rule.value,
            "threshold": self.threshold,
            "sample_size": self.sample_size,
            "description": self.description,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QualityCheck":
        """Tạo QualityCheck từ dict."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            target=data.get("target", ""),
            rule=DataQualityRule(data.get("rule", "completeness")),
            threshold=data.get("threshold", 0.95),
            sample_size=data.get("sample_size", 0),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )


@dataclass
class QualityThreshold:
    """
    Threshold cho quality check.

    Attributes:
        id: Định danh threshold
        check_id: ID của QualityCheck liên kết
        metric_name: Tên metric (vd: "completeness_pct", "null_count", "age_hours")
        operator: So sánh (>=, <=, ==, >, <)
        value: Giá trị threshold
        severity: Mức độ cảnh báo khi vượt threshold
    """
    __test__ = False  # Prevent pytest collection

    id: str
    check_id: str
    metric_name: str
    operator: str = ">="
    value: float = 0.95
    severity: AlertSeverity = AlertSeverity.WARNING

    def __post_init__(self):
        if not self.id or not self.id.strip():
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_EMPTY_QUALITY_CHECK_ID,
                message="QualityThreshold id không được để trống",
            )
        valid_operators = (">=", "<=", "==", ">", "<")
        if self.operator not in valid_operators:
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_INVALID_QUALITY_THRESHOLD,
                operator=self.operator,
                valid=valid_operators,
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển QualityThreshold sang dict format."""
        return {
            "id": self.id,
            "check_id": self.check_id,
            "metric_name": self.metric_name,
            "operator": self.operator,
            "value": self.value,
            "severity": self.severity.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QualityThreshold":
        """Tạo QualityThreshold từ dict."""
        return cls(
            id=data.get("id", ""),
            check_id=data.get("check_id", ""),
            metric_name=data.get("metric_name", ""),
            operator=data.get("operator", ">="),
            value=data.get("value", 0.95),
            severity=AlertSeverity(data.get("severity", "warning")),
        )


@dataclass
class DataQualityProfile:
    """
    Profile grouping nhiều quality checks.

    Attributes:
        id: Định danh profile
        name: Tên hiển thị
        checks: Danh sách check IDs
        schedule_cron: Cron expression (default: daily)
        alert_on_failure: Có alert khi fail không
        slack_webhook: URL webhook Slack
        email_recipients: Danh sách email nhận alert
        generate_report: Có generate report không
        report_format: Format report (json, csv, html)
    """
    __test__ = False  # Prevent pytest collection

    id: str
    name: str
    checks: list[str] = field(default_factory=list)
    schedule_cron: str = "0 0 * * *"
    alert_on_failure: bool = True
    slack_webhook: str = ""
    email_recipients: list[str] = field(default_factory=list)
    generate_report: bool = True
    report_format: str = "json"

    def __post_init__(self):
        if not self.id or not self.id.strip():
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_EMPTY_QUALITY_CHECK_ID,
                message="DataQualityProfile id không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển DataQualityProfile sang dict format."""
        return {
            "id": self.id,
            "name": self.name,
            "checks": self.checks,
            "schedule_cron": self.schedule_cron,
            "alert_on_failure": self.alert_on_failure,
            "slack_webhook": self.slack_webhook,
            "email_recipients": self.email_recipients,
            "generate_report": self.generate_report,
            "report_format": self.report_format,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DataQualityProfile":
        """Tạo DataQualityProfile từ dict."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            checks=data.get("checks", []),
            schedule_cron=data.get("schedule_cron", "0 0 * * *"),
            alert_on_failure=data.get("alert_on_failure", True),
            slack_webhook=data.get("slack_webhook", ""),
            email_recipients=data.get("email_recipients", []),
            generate_report=data.get("generate_report", True),
            report_format=data.get("report_format", "json"),
        )


@dataclass
class QualityResult:
    """
    Kết quả quality check.

    Attributes:
        id: Định danh result
        check_id: ID của QualityCheck
        profile_id: ID của DataQualityProfile (optional)
        passed: Có pass không
        metric_name: Tên metric được kiểm tra
        actual_value: Giá trị thực tế
        threshold_value: Giá trị threshold
        details: Chi tiết kết quả
        checked_at: Timestamp kiểm tra (ISO)
    """
    __test__ = False  # Prevent pytest collection

    id: str
    check_id: str
    profile_id: str = ""
    passed: bool = True
    metric_name: str = ""
    actual_value: float = 0.0
    threshold_value: float = 0.0
    details: str = ""
    checked_at: str = ""

    def __post_init__(self):
        if not self.id or not self.id.strip():
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_EMPTY_QUALITY_CHECK_ID,
                message="QualityResult id không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển QualityResult sang dict format."""
        return {
            "id": self.id,
            "check_id": self.check_id,
            "profile_id": self.profile_id,
            "passed": self.passed,
            "metric_name": self.metric_name,
            "actual_value": self.actual_value,
            "threshold_value": self.threshold_value,
            "details": self.details,
            "checked_at": self.checked_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QualityResult":
        """Tạo QualityResult từ dict."""
        return cls(
            id=data.get("id", ""),
            check_id=data.get("check_id", ""),
            profile_id=data.get("profile_id", ""),
            passed=data.get("passed", True),
            metric_name=data.get("metric_name", ""),
            actual_value=data.get("actual_value", 0.0),
            threshold_value=data.get("threshold_value", 0.0),
            details=data.get("details", ""),
            checked_at=data.get("checked_at", ""),
        )


# ===========================================================================
# Performance Testing Models (from CP25)
# ===========================================================================


class PerfScenarioType(str, Enum):
    """Enum các loại performance scenario."""
    LOAD = "load"
    STRESS = "stress"
    SPIKE = "spike"
    ENDURANCE = "endurance"

    __test__ = False  # Ngăn pytest thu thập enum làm test


@dataclass
class PerfThreshold:
    """Threshold definition cho performance metrics."""
    __test__ = False

    max_response_time_p95: Optional[float] = None
    max_response_time_p99: Optional[float] = None
    min_throughput: Optional[float] = None
    max_error_rate: Optional[float] = None
    max_cpu_percent: Optional[float] = None
    max_memory_mb: Optional[float] = None

    def __post_init__(self) -> None:
        """Validate threshold values sau khi khởi tạo."""
        if self.max_response_time_p95 is not None and self.max_response_time_p95 <= 0:
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_THRESHOLD_INVALID,
                field="max_response_time_p95",
                value=self.max_response_time_p95
            )
        if self.max_response_time_p99 is not None and self.max_response_time_p99 <= 0:
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_THRESHOLD_INVALID,
                field="max_response_time_p99",
                value=self.max_response_time_p99
            )
        if self.min_throughput is not None and self.min_throughput < 0:
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_THRESHOLD_INVALID,
                field="min_throughput",
                value=self.min_throughput
            )
        if self.max_error_rate is not None and not (0 <= self.max_error_rate <= 1):
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_THRESHOLD_INVALID,
                field="max_error_rate",
                value=self.max_error_rate
            )
        if self.max_cpu_percent is not None and not (0 < self.max_cpu_percent <= 100):
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_THRESHOLD_INVALID,
                field="max_cpu_percent",
                value=self.max_cpu_percent
            )
        if self.max_memory_mb is not None and self.max_memory_mb <= 0:
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_THRESHOLD_INVALID,
                field="max_memory_mb",
                value=self.max_memory_mb
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển threshold sang dict format."""
        result: dict[str, Any] = {}
        if self.max_response_time_p95 is not None:
            result["max_response_time_p95"] = self.max_response_time_p95
        if self.max_response_time_p99 is not None:
            result["max_response_time_p99"] = self.max_response_time_p99
        if self.min_throughput is not None:
            result["min_throughput"] = self.min_throughput
        if self.max_error_rate is not None:
            result["max_error_rate"] = self.max_error_rate
        if self.max_cpu_percent is not None:
            result["max_cpu_percent"] = self.max_cpu_percent
        if self.max_memory_mb is not None:
            result["max_memory_mb"] = self.max_memory_mb
        return result


@dataclass
class PerfScenario:
    """Một performance scenario đơn lẻ."""
    __test__ = False

    id: str
    type: PerfScenarioType
    target: str
    description: str = ""
    concurrent_users: int = 100
    spawn_rate: int = 10
    duration: int = 300
    thresholds: Optional[PerfThreshold] = None
    enabled: bool = True
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate scenario sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(ErrorCode.MDC-F10_EMPTY_SCENARIO_ID, field="scenario.id")
        if not self.target or not self.target.strip():
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_MISSING_SCENARIO_TARGET,
                scenario_id=self.id
            )
        if self.concurrent_users < 1:
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_INVALID_CONCURRENCY,
                scenario_id=self.id,
                concurrent_users=self.concurrent_users
            )
        if self.spawn_rate < 1:
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_INVALID_CONCURRENCY,
                scenario_id=self.id,
                spawn_rate=self.spawn_rate
            )
        if self.duration < 1:
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_INVALID_DURATION,
                scenario_id=self.id,
                duration=self.duration
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển scenario sang dict format."""
        return {
            "id": self.id,
            "type": self.type.value,
            "target": self.target,
            "description": self.description,
            "concurrent_users": self.concurrent_users,
            "spawn_rate": self.spawn_rate,
            "duration": self.duration,
            "thresholds": self.thresholds.to_dict() if self.thresholds else None,
            "enabled": self.enabled,
            "tags": self.tags,
        }


@dataclass
class PerfBaseline:
    """Kết quả baseline từ 1 lần chạy performance test."""
    __test__ = False

    id: str
    scenario_id: str
    timestamp: str
    response_time_p50: float
    response_time_p95: float
    response_time_p99: float
    throughput_rps: float
    error_rate: float
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    passed: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate baseline metrics sau khi khởi tạo."""
        if self.response_time_p50 < 0 or self.response_time_p95 < 0 or self.response_time_p99 < 0:
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_INVALID_METRIC_VALUE,
                baseline_id=self.id,
                field="response_time"
            )
        if self.throughput_rps < 0:
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_INVALID_METRIC_VALUE,
                baseline_id=self.id,
                field="throughput_rps"
            )
        if not (0 <= self.error_rate <= 1):
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_INVALID_METRIC_VALUE,
                baseline_id=self.id,
                field="error_rate"
            )
        # p50 <= p95 <= p99
        if self.response_time_p50 > self.response_time_p95:
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_INVALID_METRIC_VALUE,
                baseline_id=self.id,
                field="response_time_p50 > p95"
            )
        if self.response_time_p95 > self.response_time_p99:
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_INVALID_METRIC_VALUE,
                baseline_id=self.id,
                field="response_time_p95 > p99"
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển baseline sang dict format."""
        return {
            "id": self.id,
            "scenario_id": self.scenario_id,
            "timestamp": self.timestamp,
            "response_time_p50": self.response_time_p50,
            "response_time_p95": self.response_time_p95,
            "response_time_p99": self.response_time_p99,
            "throughput_rps": self.throughput_rps,
            "error_rate": self.error_rate,
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "passed": self.passed,
            "metadata": self.metadata,
        }


@dataclass
class PerfReport:
    """Report output từ 1 lần chạy performance test, so sánh vs baseline."""
    __test__ = False

    run_id: str
    scenario_id: str
    baseline_id: Optional[str] = None
    current: Optional[PerfBaseline] = None
    baseline: Optional[PerfBaseline] = None
    diff: dict[str, float] = field(default_factory=dict)
    thresholds_passed: list[str] = field(default_factory=list)
    thresholds_failed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển report sang dict format."""
        result: dict[str, Any] = {
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "baseline_id": self.baseline_id,
            "current": self.current.to_dict() if self.current else None,
            "baseline": self.baseline.to_dict() if self.baseline else None,
            "diff": self.diff,
            "thresholds_passed": self.thresholds_passed,
            "thresholds_failed": self.thresholds_failed,
        }
        return result


@dataclass
class PerfSuite:
    """Collection của performance scenarios."""
    __test__ = False

    name: str
    stack: str
    scenarios: list[PerfScenario] = field(default_factory=list)
    default_thresholds: Optional[PerfThreshold] = None
    setup: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate suite sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(ErrorCode.MDC-F10_EMPTY_SUITE_NAME, field="suite.name")

    def add_scenario(self, scenario: PerfScenario) -> None:
        """Thêm scenario vào suite."""
        if self.get_scenario_by_id(scenario.id):
            from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
            EM.raise_error(
                ErrorCode.MDC-F10_DUPLICATE_SCENARIO_ID,
                id=scenario.id,
                suite_name=self.name
            )
        self.scenarios.append(scenario)

    def get_scenario_by_id(self, scenario_id: str) -> Optional[PerfScenario]:
        """Tìm scenario theo ID."""
        for scenario in self.scenarios:
            if scenario.id == scenario_id:
                return scenario
        return None

    def get_enabled_scenarios(self) -> list[PerfScenario]:
        """Lọc các scenarios đang active."""
        return [s for s in self.scenarios if s.enabled]

    def get_scenarios_by_type(self, scenario_type: PerfScenarioType) -> list[PerfScenario]:
        """Lọc scenarios theo type."""
        return [s for s in self.scenarios if s.type == scenario_type]

    def to_dict(self) -> dict[str, Any]:
        """Chuyển suite sang dict format."""
        return {
            "name": self.name,
            "stack": self.stack,
            "scenarios": [s.to_dict() for s in self.scenarios],
            "default_thresholds": self.default_thresholds.to_dict() if self.default_thresholds else None,
            "setup": self.setup,
        }


@dataclass
class PerfCollection:
    """Collection chứa tất cả perf suites và baselines."""
    __test__ = False

    suites: list[PerfSuite] = field(default_factory=list)
    baselines: list[PerfBaseline] = field(default_factory=list)

    def add_suite(self, suite: PerfSuite) -> None:
        """Thêm perf suite vào collection."""
        self.suites.append(suite)

    def add_baseline(self, baseline: PerfBaseline) -> None:
        """Thêm baseline vào collection."""
        self.baselines.append(baseline)

    def get_suites_by_stack(self, stack: str) -> list[PerfSuite]:
        """Lọc suites theo stack."""
        return [s for s in self.suites if s.stack == stack]

    def get_all_scenarios(self) -> list[PerfScenario]:
        """Lấy tất cả scenarios từ mọi suite."""
        scenarios: list[PerfScenario] = []
        for suite in self.suites:
            scenarios.extend(suite.scenarios)
        return scenarios

    def get_scenarios_by_type(self, scenario_type: PerfScenarioType) -> list[PerfScenario]:
        """Lọc scenarios theo type."""
        scenarios: list[PerfScenario] = []
        for suite in self.suites:
            scenarios.extend(suite.get_scenarios_by_type(scenario_type))
        return scenarios

    def get_baseline_by_scenario(self, scenario_id: str) -> Optional[PerfBaseline]:
        """Tìm baseline theo scenario ID."""
        for baseline in self.baselines:
            if baseline.scenario_id == scenario_id:
                return baseline
        return None

    def count_scenarios(self) -> dict[str, int]:
        """Đếm số scenarios theo type."""
        counts = {"load": 0, "stress": 0, "spike": 0, "endurance": 0}
        for suite in self.suites:
            for scenario in suite.scenarios:
                counts[scenario.type.value] += 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        """Chuyển collection sang dict format."""
        return {
            "suites": [s.to_dict() for s in self.suites],
            "baselines": [b.to_dict() for b in self.baselines],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PerfCollection":
        """Tạo PerfCollection từ dict."""
        collection = cls()

        # Parse suites
        for suite_data in data.get("suites", []):
            suite = PerfSuite(
                name=suite_data["name"],
                stack=suite_data["stack"],
                setup=suite_data.get("setup", {}),
            )
            if suite_data.get("default_thresholds"):
                suite.default_thresholds = PerfThreshold(**suite_data["default_thresholds"])

            for scenario_data in suite_data.get("scenarios", []):
                thresholds = None
                if scenario_data.get("thresholds"):
                    thresholds = PerfThreshold(**scenario_data["thresholds"])

                scenario = PerfScenario(
                    id=scenario_data["id"],
                    type=PerfScenarioType(scenario_data["type"]),
                    target=scenario_data["target"],
                    description=scenario_data.get("description", ""),
                    concurrent_users=scenario_data.get("concurrent_users", 100),
                    spawn_rate=scenario_data.get("spawn_rate", 10),
                    duration=scenario_data.get("duration", 300),
                    thresholds=thresholds,
                    enabled=scenario_data.get("enabled", True),
                    tags=scenario_data.get("tags", []),
                )
                suite.add_scenario(scenario)

            collection.add_suite(suite)

        # Parse baselines
        for baseline_data in data.get("baselines", []):
            baseline = PerfBaseline(
                id=baseline_data["id"],
                scenario_id=baseline_data["scenario_id"],
                timestamp=baseline_data["timestamp"],
                response_time_p50=baseline_data["response_time_p50"],
                response_time_p95=baseline_data["response_time_p95"],
                response_time_p99=baseline_data["response_time_p99"],
                throughput_rps=baseline_data["throughput_rps"],
                error_rate=baseline_data["error_rate"],
                cpu_percent=baseline_data.get("cpu_percent", 0.0),
                memory_mb=baseline_data.get("memory_mb", 0.0),
                passed=baseline_data.get("passed", True),
                metadata=baseline_data.get("metadata", {}),
            )
            collection.add_baseline(baseline)

        return collection
