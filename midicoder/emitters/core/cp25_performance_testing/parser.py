# coding: utf-8
"""
Mô-đun parser cho Performance Testing Generator (CP25).

Parse DSL perf nodes từ MIR metadata / Contract YAML thành PerfCollection.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

import yaml

from midicoder.emitters.core.cp25_performance_testing.models import (
    PerfBaseline,
    PerfCollection,
    PerfScenario,
    PerfScenarioType,
    PerfSuite,
    PerfThreshold,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


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
                    ErrorCode.CP25_DSL_PARSE_ERROR,
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
                ErrorCode.CP25_DSL_PARSE_ERROR,
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
                ErrorCode.CP25_INVALID_SCENARIO_TYPE,
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
