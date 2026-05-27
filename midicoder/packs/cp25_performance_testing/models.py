# coding: utf-8
"""
Mô-đun models cho Performance Testing Generator (CP25).

Định nghĩa các dataclass biểu diễn:
- PerfScenarioType: Enum các loại performance scenario (load, stress, spike, endurance)
- PerfScenario: Một performance scenario đơn lẻ
- PerfThreshold: Threshold definition cho metrics
- PerfBaseline: Kết quả baseline từ 1 lần chạy
- PerfReport: Report output từ performance test run
- PerfSuite: Collection của performance scenarios
- PerfCollection: Output chính của PerfParser

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class PerfScenarioType(str, Enum):
    """Enum các loại performance scenario."""
    LOAD = "load"
    STRESS = "stress"
    SPIKE = "spike"
    ENDURANCE = "endurance"

    __test__ = False  # Ngăn pytest thu thập enum làm test


# ===========================================================================
# PerfThreshold
# ===========================================================================


@dataclass
class PerfThreshold:
    """
    Threshold definition cho performance metrics.

    Attributes:
        max_response_time_p95: Thời gian phản hồi tối đa ở p95 (ms)
        max_response_time_p99: Thời gian phản hồi tối đa ở p99 (ms)
        min_throughput: Lưu lượng tối thiểu (requests/giây)
        max_error_rate: Tỷ lệ lỗi tối đa (0.0 - 1.0)
        max_cpu_percent: CPU usage tối đa (%)
        max_memory_mb: Memory usage tối đa (MB)
    """
    __test__ = False  # Ngăn pytest thu thập enum làm test

    max_response_time_p95: Optional[float] = None
    max_response_time_p99: Optional[float] = None
    min_throughput: Optional[float] = None
    max_error_rate: Optional[float] = None
    max_cpu_percent: Optional[float] = None
    max_memory_mb: Optional[float] = None

    def __post_init__(self) -> None:
        """Validate threshold values sau khi khởi tạo."""
        if self.max_response_time_p95 is not None and self.max_response_time_p95 <= 0:
            EM.raise_error(
                ErrorCode.CP25_THRESHOLD_INVALID,
                field="max_response_time_p95",
                value=self.max_response_time_p95
            )
        if self.max_response_time_p99 is not None and self.max_response_time_p99 <= 0:
            EM.raise_error(
                ErrorCode.CP25_THRESHOLD_INVALID,
                field="max_response_time_p99",
                value=self.max_response_time_p99
            )
        if self.min_throughput is not None and self.min_throughput < 0:
            EM.raise_error(
                ErrorCode.CP25_THRESHOLD_INVALID,
                field="min_throughput",
                value=self.min_throughput
            )
        if self.max_error_rate is not None and not (0 <= self.max_error_rate <= 1):
            EM.raise_error(
                ErrorCode.CP25_THRESHOLD_INVALID,
                field="max_error_rate",
                value=self.max_error_rate
            )
        if self.max_cpu_percent is not None and not (0 < self.max_cpu_percent <= 100):
            EM.raise_error(
                ErrorCode.CP25_THRESHOLD_INVALID,
                field="max_cpu_percent",
                value=self.max_cpu_percent
            )
        if self.max_memory_mb is not None and self.max_memory_mb <= 0:
            EM.raise_error(
                ErrorCode.CP25_THRESHOLD_INVALID,
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


# ===========================================================================
# PerfScenario
# ===========================================================================


@dataclass
class PerfScenario:
    """
    Một performance scenario đơn lẻ.

    Attributes:
        id: Định danh duy nhất của scenario
        type: Loại scenario (load, stress, spike, endurance)
        target: Target entity/command/query ID
        description: Mô tả scenario (optional)
        concurrent_users: Số user đồng thời
        spawn_rate: Tốc độ spawn user (user/giây)
        duration: Thời gian chạy (giây)
        thresholds: Threshold definitions (optional)
        enabled: Có kích hoạt scenario không (default True)
        tags: Danh sách tags để filter
    """
    __test__ = False  # Ngăn pytest thu thập enum làm test

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
            EM.raise_error(ErrorCode.CP25_EMPTY_SCENARIO_ID, field="scenario.id")
        if not self.target or not self.target.strip():
            EM.raise_error(
                ErrorCode.CP25_MISSING_SCENARIO_TARGET,
                scenario_id=self.id
            )
        if self.concurrent_users < 1:
            EM.raise_error(
                ErrorCode.CP25_INVALID_CONCURRENCY,
                scenario_id=self.id,
                concurrent_users=self.concurrent_users
            )
        if self.spawn_rate < 1:
            EM.raise_error(
                ErrorCode.CP25_INVALID_CONCURRENCY,
                scenario_id=self.id,
                spawn_rate=self.spawn_rate
            )
        if self.duration < 1:
            EM.raise_error(
                ErrorCode.CP25_INVALID_DURATION,
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


# ===========================================================================
# PerfBaseline
# ===========================================================================


@dataclass
class PerfBaseline:
    """
    Kết quả baseline từ 1 lần chạy performance test.

    Attributes:
        id: Định danh duy nhất của baseline
        scenario_id: ID của scenario đã chạy
        timestamp: Thời gian chạy (ISO format string)
        response_time_p50: Thời gian phản hồi ở p50 (ms)
        response_time_p95: Thời gian phản hồi ở p95 (ms)
        response_time_p99: Thời gian phản hồi ở p99 (ms)
        throughput_rps: Lưu lượng (requests/giây)
        error_rate: Tỷ lệ lỗi (0.0 - 1.0)
        cpu_percent: CPU usage (%)
        memory_mb: Memory usage (MB)
        passed: Có vượt qua thresholds không
        metadata: Metadata bổ sung
    """
    __test__ = False  # Ngăn pytest thu thập enum làm test

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
            EM.raise_error(
                ErrorCode.CP25_INVALID_METRIC_VALUE,
                baseline_id=self.id,
                field="response_time"
            )
        if self.throughput_rps < 0:
            EM.raise_error(
                ErrorCode.CP25_INVALID_METRIC_VALUE,
                baseline_id=self.id,
                field="throughput_rps"
            )
        if not (0 <= self.error_rate <= 1):
            EM.raise_error(
                ErrorCode.CP25_INVALID_METRIC_VALUE,
                baseline_id=self.id,
                field="error_rate"
            )
        # p50 <= p95 <= p99
        if self.response_time_p50 > self.response_time_p95:
            EM.raise_error(
                ErrorCode.CP25_INVALID_METRIC_VALUE,
                baseline_id=self.id,
                field="response_time_p50 > p95"
            )
        if self.response_time_p95 > self.response_time_p99:
            EM.raise_error(
                ErrorCode.CP25_INVALID_METRIC_VALUE,
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


# ===========================================================================
# PerfReport
# ===========================================================================


@dataclass
class PerfReport:
    """
    Report output từ 1 lần chạy performance test, so sánh vs baseline.

    Attributes:
        run_id: ID của lần chạy
        scenario_id: ID của scenario
        baseline_id: ID của baseline so sánh (optional)
        current: Kết quả hiện tại
        baseline: Kết quả baseline cũ (optional)
        diff: Sự khác biệt giữa current và baseline (optional)
        thresholds_passed: Các thresholds đã vượt qua
        thresholds_failed: Các thresholds đã thất bại
    """
    __test__ = False  # Ngăn pytest thu thập enum làm test

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


# ===========================================================================
# PerfSuite
# ===========================================================================


@dataclass
class PerfSuite:
    """
    Collection của performance scenarios.

    Attributes:
        name: Tên test suite
        stack: Target stack (fastapi, nestjs, angular, react)
        scenarios: Danh sách scenarios
        default_thresholds: Default thresholds cho toàn suite (optional)
        setup: Global setup data (optional)
    """
    __test__ = False  # Ngăn pytest thu thập enum làm test

    name: str
    stack: str
    scenarios: list[PerfScenario] = field(default_factory=list)
    default_thresholds: Optional[PerfThreshold] = None
    setup: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate suite sau khi khởi tạo."""
        if not self.name or not self.name.strip():
            EM.raise_error(ErrorCode.CP25_EMPTY_SUITE_NAME, field="suite.name")

    def add_scenario(self, scenario: PerfScenario) -> None:
        """Thêm scenario vào suite."""
        if self.get_scenario_by_id(scenario.id):
            EM.raise_error(
                ErrorCode.CP25_DUPLICATE_SCENARIO_ID,
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


# ===========================================================================
# PerfCollection — output chính của PerfParser
# ===========================================================================


@dataclass
class PerfCollection:
    """
    Collection chứa tất cả perf suites và baselines.

    Dùng làm output của PerfParser và input cho Stack Emitters.

    Attributes:
        suites: Danh sách perf suites
        baselines: Danh sách baselines
    """
    __test__ = False  # Ngăn pytest thu thập enum làm test

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
