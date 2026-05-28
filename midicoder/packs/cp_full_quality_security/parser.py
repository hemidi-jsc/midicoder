# coding: utf-8
"""
Mô-đun parser cho Code Quality & Security Scanner Generator (CP24).

Parse DSL quality/security nodes từ MIR metadata / Contract YAML thành
QualityCollection.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

import yaml

from midicoder.packs.cp_full_quality_security.models import (
    FormatterType,
    LinterType,
    PerfBaseline,
    PerfCollection,
    PerfScenario,
    PerfScenarioType,
    PerfSuite,
    PerfThreshold,
    QualityCollection,
    QualityGateConfig,
    QualityProfile,
    SecurityScanConfig,
    SecurityScanRule,
    SecurityTool,
    SeverityLevel,
    StackType,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# Mapping mặc định: stack → (linter, formatter)
DEFAULT_LINTER: dict[StackType, LinterType] = {
    StackType.FASTAPI: LinterType.RUFF,
    StackType.NESTJS: LinterType.ESLINT,
    StackType.ANGULAR: LinterType.ESLINT,
    StackType.REACT: LinterType.ESLINT,
}

DEFAULT_FORMATTER: dict[StackType, FormatterType] = {
    StackType.FASTAPI: FormatterType.BLACK,
    StackType.NESTJS: FormatterType.PRETTIER,
    StackType.ANGULAR: FormatterType.PRETTIER,
    StackType.REACT: FormatterType.PRETTIER,
}

# Security tools mặc định per stack
DEFAULT_SECURITY_TOOLS: dict[StackType, list[SecurityTool]] = {
    StackType.FASTAPI: [SecurityTool.BANDIT, SecurityTool.SAFETY],
    StackType.NESTJS: [SecurityTool.NPM_AUDIT, SecurityTool.ESLINT_SECURITY],
    StackType.ANGULAR: [SecurityTool.ESLINT_SECURITY, SecurityTool.LOCKFILE_LINT],
    StackType.REACT: [SecurityTool.ESLINT_SECURITY, SecurityTool.LOCKFILE_LINT],
}


class QualityProfileParser:
    """
    Parser cho DSL quality/security nodes.

    Parse YAML DSL hoặc dict metadata thành QualityCollection.

    Ví dụ DSL:
        quality:
          profiles:
            - name: strict
              stack: fastapi
              linter: ruff
              min_score: 90
          security:
            - stack: fastapi
              tools: [bandit, safety]
              fail_on_severity: high
          gate:
            enabled: true
            block_on_fail: true
    """

    def parse(self, raw: str | dict[str, Any]) -> QualityCollection:
        """
        Parse YAML string hoặc dict thành QualityCollection.

        Args:
            raw: YAML string hoặc dict chứa quality definitions

        Returns:
            QualityCollection chứa profiles, security configs, gate config

        Raises:
            MidicoderError: Nếu parse thất bại
        """
        if isinstance(raw, str):
            if not raw or not raw.strip():
                return QualityCollection()
            try:
                data = yaml.safe_load(raw)
            except yaml.YAMLError as e:
                EM.raise_error(
                    ErrorCode.MDC-F10_DSL_PARSE_ERROR,
                    message=f"Lỗi parse YAML quality nodes: {e}",
                    error=str(e),
                )
            if data is None:
                return QualityCollection()
        elif isinstance(raw, dict):
            data = raw
        else:
            return QualityCollection()

        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.MDC-F10_DSL_PARSE_ERROR,
                message="DSL quality nodes phải là YAML mapping",
            )

        return self._parse_from_dict(data)

    def parse_from_metadata(self, metadata: dict[str, Any]) -> QualityCollection:
        """
        Parse từ MIR metadata dict.

        MIR metadata có thể chứa key 'quality' hoặc 'quality_config'.

        Args:
            metadata: MIR metadata dict

        Returns:
            QualityCollection
        """
        quality_data = metadata.get("quality", metadata.get("quality_config"))
        if not quality_data or not isinstance(quality_data, dict):
            return self._generate_defaults()

        return self._parse_from_dict(quality_data)

    def _parse_from_dict(self, data: dict[str, Any]) -> QualityCollection:
        """Parse từ dict đã load."""
        collection = QualityCollection()

        # Parse quality profiles
        profiles_data = data.get("profiles", data.get("quality_profiles", []))
        if isinstance(profiles_data, list):
            for profile_data in profiles_data:
                if isinstance(profile_data, dict):
                    profile = self._parse_profile(profile_data)
                    collection.add_profile(profile)

        # Parse security configs
        security_data = data.get("security", data.get("security_configs", []))
        if isinstance(security_data, list):
            for sec_data in security_data:
                if isinstance(sec_data, dict):
                    sec_config = self._parse_security_config(sec_data)
                    collection.add_security_config(sec_config)

        # Parse gate config
        gate_data = data.get("gate", data.get("quality_gate"))
        if gate_data and isinstance(gate_data, dict):
            collection.gate_config = self._parse_gate_config(gate_data)

        # Nếu không có profiles nào — generate defaults
        if not collection.profiles:
            defaults = self._generate_defaults()
            collection.profiles = defaults.profiles
            collection.security_configs = defaults.security_configs

        # Nếu không có gate config — tạo mặc định
        if not collection.gate_config:
            collection.gate_config = QualityGateConfig(
                enabled=True,
                block_on_fail=True,
            )

        return collection

    def _parse_stack(self, value: str) -> StackType:
        """Parse string thành StackType enum."""
        try:
            return StackType(value)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-F10_INVALID_STACK,
                stack=value,
                valid=[s.value for s in StackType],
            )

    def _parse_linter(self, value: str) -> LinterType:
        """Parse string thành LinterType enum."""
        try:
            return LinterType(value)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-F10_PROFILE_INVALID,
                field="linter",
                value=value,
                valid=[l.value for l in LinterType],
            )

    def _parse_formatter(self, value: str) -> FormatterType:
        """Parse string thành FormatterType enum."""
        try:
            return FormatterType(value)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-F10_PROFILE_INVALID,
                field="formatter",
                value=value,
                valid=[f.value for f in FormatterType],
            )

    def _parse_severity(self, value: str) -> SeverityLevel:
        """Parse string thành SeverityLevel enum."""
        try:
            return SeverityLevel(value)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-F10_SCAN_CONFIG_INVALID,
                field="severity",
                value=value,
                valid=[s.value for s in SeverityLevel],
            )

    def _parse_security_tool(self, value: str) -> SecurityTool:
        """Parse string thành SecurityTool enum."""
        try:
            return SecurityTool(value)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-F10_SCAN_CONFIG_INVALID,
                field="tool",
                value=value,
                valid=[t.value for t in SecurityTool],
            )

    def _parse_profile(self, data: dict[str, Any]) -> QualityProfile:
        """Parse quality profile definition."""
        name = data.get("name", data.get("profile", "standard"))
        if not name or not name.strip():
            EM.raise_error(ErrorCode.MDC-F10_EMPTY_PROFILE_NAME)

        stack_str = data.get("stack", "fastapi")
        stack = self._parse_stack(stack_str)

        # Linter: lấy từ data hoặc mặc định theo stack
        linter_str = data.get("linter", DEFAULT_LINTER[stack].value)
        linter = self._parse_linter(linter_str)

        # Formatter: lấy từ data hoặc mặc định theo stack
        formatter_str = data.get("formatter", DEFAULT_FORMATTER[stack].value)
        formatter = self._parse_formatter(formatter_str)

        return QualityProfile(
            name=name,
            stack=stack,
            linter=linter,
            formatter=formatter,
            min_score=data.get("min_score", 80),
            rules=data.get("rules", {}),
            exclude=data.get("exclude", []),
        )

    def _parse_security_config(self, data: dict[str, Any]) -> SecurityScanConfig:
        """Parse security scan config definition."""
        stack_str = data.get("stack", "fastapi")
        stack = self._parse_stack(stack_str)

        # Tools: lấy từ data hoặc mặc định theo stack
        tools_raw = data.get("tools", [])
        if tools_raw:
            tools = [self._parse_security_tool(t) for t in tools_raw]
        else:
            tools = list(DEFAULT_SECURITY_TOOLS[stack])

        # Rules
        rules_raw = data.get("rules", [])
        rules = [self._parse_security_rule(r) for r in rules_raw if isinstance(r, dict)]

        # Fail severity
        fail_on = self._parse_severity(data.get("fail_on_severity", "high"))

        return SecurityScanConfig(
            stack=stack,
            tools=tools,
            rules=rules,
            fail_on_severity=fail_on,
            exclude=data.get("exclude", []),
        )

    def _parse_security_rule(self, data: dict[str, Any]) -> SecurityScanRule:
        """Parse security scan rule definition."""
        rule_id = data.get("rule_id", data.get("id", ""))
        severity = self._parse_severity(data.get("severity", "medium"))
        tool = self._parse_security_tool(data.get("tool", "bandit"))

        return SecurityScanRule(
            rule_id=rule_id,
            severity=severity,
            tool=tool,
            enabled=data.get("enabled", True),
            description=data.get("description", ""),
        )

    def _parse_gate_config(self, data: dict[str, Any]) -> QualityGateConfig:
        """Parse quality gate config definition."""
        return QualityGateConfig(
            enabled=data.get("enabled", True),
            block_on_fail=True,  # CP24: luôn block, không có warn mode
            report_path=data.get("report_path", "reports/quality_gate.json"),
            min_coverage=data.get("min_coverage", 80),
        )

    def _generate_defaults(self) -> QualityCollection:
        """Generate cấu hình mặc định cho tất cả 4 stacks."""
        collection = QualityCollection()

        for stack in StackType:
            collection.add_profile(QualityProfile(
                name="standard",
                stack=stack,
                linter=DEFAULT_LINTER[stack],
                formatter=DEFAULT_FORMATTER[stack],
                min_score=80,
            ))
            collection.add_security_config(SecurityScanConfig(
                stack=stack,
                tools=list(DEFAULT_SECURITY_TOOLS[stack]),
                fail_on_severity=SeverityLevel.HIGH,
            ))

        return collection



# PerfParser - merged from CP25 Performance Testing
class PerfParser:
    """
    Parser cho DSL perf nodes.

    Parse YAML DSL hoặc dict metadata thành PerfCollection.

    Ví dụ DSL:
        perf_scenarios:
          - id: perf_order_create
            type: load
            target: CreateOrder
            concurrent_users: 100
            spawn_rate: 10
            duration: 300
    """

    def parse(self, raw: str | dict[str, Any]) -> PerfCollection:
        """
        Parse YAML string hoặc dict thành PerfCollection.

        Args:
            raw: YAML string hoặc dict chứa perf definitions

        Returns:
            PerfCollection chứa suites và scenarios

        Raises:
            MidicoderError: Nếu parse thất bại
        """
        if isinstance(raw, str):
            if not raw or not raw.strip():
                return PerfCollection()
            try:
                data = yaml.safe_load(raw)
            except yaml.YAMLError as e:
                EM.raise_error(
                    ErrorCode.MDC-F10_DSL_PARSE_ERROR,
                    message=f"Lỗi parse YAML perf nodes: {e}",
                    error=str(e)
                )
            if data is None:
                return PerfCollection()
        elif isinstance(raw, dict):
            data = raw
        else:
            return PerfCollection()

        if not isinstance(data, dict):
            EM.raise_error(
                ErrorCode.MDC-F10_DSL_PARSE_ERROR,
                message="DSL perf nodes phải là YAML mapping"
            )

        return self._parse_from_dict(data)

    def parse_from_metadata(self, metadata: dict[str, Any], stack: str = "fastapi") -> PerfCollection:
        """
        Parse từ MIR metadata dict.

        Args:
            metadata: MIR metadata dict
            stack: Target stack name

        Returns:
            PerfCollection
        """
        collection = PerfCollection()

        # Parse explicit perf scenarios từ metadata
        perf_data = metadata.get("perf_scenarios", metadata.get("perf", []))
        if perf_data and isinstance(perf_data, list):
            suite = PerfSuite(name=f"{stack}_perf_tests", stack=stack)

            for scenario_data in perf_data:
                if isinstance(scenario_data, dict):
                    scenario = self._parse_scenario(scenario_data)
                    suite.add_scenario(scenario)

            if suite.scenarios:
                collection.add_suite(suite)

        # Parse baselines
        baselines_data = metadata.get("perf_baselines", [])
        if baselines_data and isinstance(baselines_data, list):
            for baseline_data in baselines_data:
                if isinstance(baseline_data, dict):
                    baseline = self._parse_baseline(baseline_data)
                    collection.add_baseline(baseline)

        # Auto-generate from entities/commands if no explicit perf scenarios
        if not collection.suites:
            collection = self._auto_generate_from_mir(metadata, stack)

        return collection

    def _auto_generate_from_mir(self, metadata: dict[str, Any], stack: str) -> PerfCollection:
        """Tự động generate perf scenarios từ MIR entities/commands."""
        collection = PerfCollection()
        suite = PerfSuite(name=f"{stack}_perf_tests", stack=stack)

        # Generate load scenario cho mỗi command
        commands = metadata.get("commands", [])
        for cmd in commands:
            if isinstance(cmd, dict):
                cmd_id = cmd.get("id", "")
                if cmd_id:
                    scenario = PerfScenario(
                        id=f"perf_{cmd_id.lower()}",
                        type=PerfScenarioType.LOAD,
                        target=cmd_id,
                        description=f"Load test cho {cmd_id}",
                        concurrent_users=100,
                        spawn_rate=10,
                        duration=300,
                    )
                    suite.add_scenario(scenario)

        # Generate load scenario cho mỗi query
        queries = metadata.get("queries", [])
        for qry in queries:
            if isinstance(qry, dict):
                qry_id = qry.get("id", "")
                if qry_id:
                    scenario = PerfScenario(
                        id=f"perf_{qry_id.lower()}",
                        type=PerfScenarioType.LOAD,
                        target=qry_id,
                        description=f"Load test cho {qry_id}",
                        concurrent_users=50,
                        spawn_rate=5,
                        duration=180,
                    )
                    suite.add_scenario(scenario)

        if suite.scenarios:
            collection.add_suite(suite)

        return collection

    def _parse_from_dict(self, data: dict[str, Any]) -> PerfCollection:
        """Parse từ dict đã load."""
        collection = PerfCollection()

        # Parse perf suites
        suites_data = data.get("perf_suites", data.get("suites", []))
        if isinstance(suites_data, list):
            for suite_data in suites_data:
                if isinstance(suite_data, dict):
                    suite = self._parse_suite(suite_data)
                    collection.add_suite(suite)

        # Parse flat perf scenarios
        scenarios_data = data.get("perf_scenarios", data.get("scenarios", []))
        if isinstance(scenarios_data, list) and scenarios_data:
            # Wrap into default suite
            stack = data.get("stack", "fastapi")
            suite = PerfSuite(name="perf_tests", stack=stack)
            for scenario_data in scenarios_data:
                if isinstance(scenario_data, dict):
                    scenario = self._parse_scenario(scenario_data)
                    suite.add_scenario(scenario)
            if suite.scenarios:
                collection.add_suite(suite)

        # Parse baselines
        baselines_data = data.get("perf_baselines", data.get("baselines", []))
        if isinstance(baselines_data, list):
            for baseline_data in baselines_data:
                if isinstance(baseline_data, dict):
                    baseline = self._parse_baseline(baseline_data)
                    collection.add_baseline(baseline)

        return collection

    def _parse_suite(self, data: dict[str, Any]) -> PerfSuite:
        """Parse suite definition."""
        name = data.get("name", "perf_tests")
        stack = data.get("stack", "fastapi")

        suite = PerfSuite(
            name=name,
            stack=stack,
            setup=data.get("setup", {}),
        )

        # Parse default thresholds
        if data.get("default_thresholds"):
            suite.default_thresholds = self._parse_threshold(data["default_thresholds"])

        # Parse scenarios
        for scenario_data in data.get("scenarios", []):
            if isinstance(scenario_data, dict):
                scenario = self._parse_scenario(scenario_data)
                suite.add_scenario(scenario)

        return suite

    def _parse_scenario(self, data: dict[str, Any]) -> PerfScenario:
        """Parse scenario definition."""
        type_str = data.get("type", "load")
        try:
            scenario_type = PerfScenarioType(type_str)
        except ValueError:
            EM.raise_error(
                ErrorCode.MDC-F10_INVALID_SCENARIO_TYPE,
                scenario_type=type_str,
                valid=[t.value for t in PerfScenarioType]
            )

        # Parse thresholds
        thresholds = None
        if data.get("thresholds"):
            thresholds = self._parse_threshold(data["thresholds"])

        return PerfScenario(
            id=data.get("id", ""),
            type=scenario_type,
            target=data.get("target", ""),
            description=data.get("description", ""),
            concurrent_users=data.get("concurrent_users", 100),
            spawn_rate=data.get("spawn_rate", 10),
            duration=data.get("duration", 300),
            thresholds=thresholds,
            enabled=data.get("enabled", True),
            tags=data.get("tags", []),
        )

    def _parse_threshold(self, data: dict[str, Any]) -> PerfThreshold:
        """Parse threshold definition."""
        return PerfThreshold(
            max_response_time_p95=data.get("max_response_time_p95"),
            max_response_time_p99=data.get("max_response_time_p99"),
            min_throughput=data.get("min_throughput"),
            max_error_rate=data.get("max_error_rate"),
            max_cpu_percent=data.get("max_cpu_percent"),
            max_memory_mb=data.get("max_memory_mb"),
        )

    def _parse_baseline(self, data: dict[str, Any]) -> PerfBaseline:
        """Parse baseline definition."""
        return PerfBaseline(
            id=data.get("id", ""),
            scenario_id=data.get("scenario_id", ""),
            timestamp=data.get("timestamp", ""),
            response_time_p50=data.get("response_time_p50", 0.0),
            response_time_p95=data.get("response_time_p95", 0.0),
            response_time_p99=data.get("response_time_p99", 0.0),
            throughput_rps=data.get("throughput_rps", 0.0),
            error_rate=data.get("error_rate", 0.0),
            cpu_percent=data.get("cpu_percent", 0.0),
            memory_mb=data.get("memory_mb", 0.0),
            passed=data.get("passed", True),
            metadata=data.get("metadata", {}),
        )
