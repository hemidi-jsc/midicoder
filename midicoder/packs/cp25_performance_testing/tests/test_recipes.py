# coding: utf-8
"""
Unit tests cho recipes của CP25.

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.packs.cp25_performance_testing.recipes import (
    auto_generate_perf_scenarios_from_mir,
    compare_baseline,
    generate_load_scenarios,
    generate_web_vitals_tests,
    save_baseline,
)
from midicoder.packs.cp25_performance_testing.models import (
    PerfBaseline,
    PerfScenarioType,
)


class TestAutoGenerateScenarios:
    """Test auto_generate_perf_scenarios_from_mir."""

    def test_generate_from_commands(self) -> None:
        """Tạo scenarios từ commands trong MIR."""
        metadata = {
            "commands": [
                {"id": "CreateOrder"},
                {"id": "CreateCustomer"},
            ],
        }
        result = auto_generate_perf_scenarios_from_mir(metadata, stack="fastapi")

        assert len(result.suites) == 1
        assert len(result.suites[0].scenarios) == 2
        assert result.suites[0].scenarios[0].type == PerfScenarioType.LOAD

    def test_generate_from_queries(self) -> None:
        """Tạo scenarios từ queries trong MIR."""
        metadata = {
            "queries": [
                {"id": "SearchProducts"},
            ],
        }
        result = auto_generate_perf_scenarios_from_mir(metadata, stack="fastapi")

        assert len(result.suites) == 1
        assert len(result.suites[0].scenarios) == 1
        assert result.suites[0].scenarios[0].concurrent_users == 50  # queries có ít users hơn

    def test_generate_empty_metadata(self) -> None:
        """Metadata rỗng trả về collection rỗng."""
        result = auto_generate_perf_scenarios_from_mir({}, stack="fastapi")
        assert len(result.suites) == 0


class TestGenerateLoadScenarios:
    """Test generate_load_scenarios."""

    def test_generate(self) -> None:
        """Tạo load scenarios cho danh sách targets."""
        result = generate_load_scenarios(
            targets=["CreateOrder", "SearchProducts"],
            stack="fastapi",
            concurrent_users=200,
        )

        assert len(result.suites) == 1
        assert len(result.suites[0].scenarios) == 2
        assert result.suites[0].scenarios[0].concurrent_users == 200


class TestGenerateWebVitalsTests:
    """Test generate_web_vitals_tests."""

    def test_generate(self) -> None:
        """Tạo Web Vitals tests cho frontend pages."""
        result = generate_web_vitals_tests(
            pages=["/", "/products", "/orders"],
            stack="react",
        )

        assert len(result.suites) == 1
        assert len(result.suites[0].scenarios) == 3
        assert result.suites[0].scenarios[0].type == PerfScenarioType.ENDURANCE


class TestSaveBaseline:
    """Test save_baseline recipe."""

    def test_create_baseline(self) -> None:
        """Tạo PerfBaseline từ metrics dict."""
        metrics = {
            "response_time_p50": 50.0,
            "response_time_p95": 200.0,
            "response_time_p99": 500.0,
            "throughput_rps": 100.0,
            "error_rate": 0.001,
        }
        baseline = save_baseline("perf_order", metrics)

        assert baseline.scenario_id == "perf_order"
        assert baseline.response_time_p50 == 50.0
        assert baseline.throughput_rps == 100.0


class TestCompareBaseline:
    """Test compare_baseline recipe."""

    def test_compute_diff(self) -> None:
        """Tính diff giữa 2 baselines."""
        current = PerfBaseline(
            id="current", scenario_id="s1", timestamp="2026-05-20",
            response_time_p50=60, response_time_p95=240, response_time_p99=600,
            throughput_rps=80, error_rate=0.02,
        )
        baseline = PerfBaseline(
            id="baseline", scenario_id="s1", timestamp="2026-05-19",
            response_time_p50=50, response_time_p95=200, response_time_p99=500,
            throughput_rps=100, error_rate=0.01,
        )
        diff = compare_baseline(current, baseline)

        # p50 tăng 20% (60-50)/50*100
        assert diff["response_time_p50_change_pct"] == 20.0
        # throughput giảm 20% (80-100)/100*100
        assert diff["throughput_rps_change_pct"] == -20.0
        # error_rate tăng 0.01
        assert diff["error_rate_change"] == 0.01
