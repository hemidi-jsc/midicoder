# coding: utf-8
"""
Unit tests cho models của Performance Testing Generator (CP25).

Kiểm tra:
- PerfThreshold validation
- PerfScenario validation
- PerfBaseline validation
- PerfSuite operations
- PerfCollection operations
- to_dict / from_dict serialization

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.packs.cp25_performance_testing.models import (
    PerfBaseline,
    PerfCollection,
    PerfScenario,
    PerfScenarioType,
    PerfSuite,
    PerfThreshold,
)
from midicoder.errors import ErrorCode, MidicoderError


class TestPerfThreshold:
    """Test PerfThreshold dataclass."""

    def test_create_threshold_with_all_fields(self) -> None:
        """Tạo threshold với đầy đủ fields."""
        t = PerfThreshold(
            max_response_time_p95=500.0,
            max_response_time_p99=1000.0,
            min_throughput=50.0,
            max_error_rate=0.01,
            max_cpu_percent=80.0,
            max_memory_mb=512.0,
        )
        assert t.max_response_time_p95 == 500.0
        assert t.max_response_time_p99 == 1000.0
        assert t.min_throughput == 50.0
        assert t.max_error_rate == 0.01
        assert t.max_cpu_percent == 80.0
        assert t.max_memory_mb == 512.0

    def test_create_threshold_all_optional(self) -> None:
        """Tạo threshold với tất cả fields optional."""
        t = PerfThreshold()
        assert t.max_response_time_p95 is None
        assert t.min_throughput is None

    def test_invalid_negative_response_time(self) -> None:
        """Threshold với response time âm sẽ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PerfThreshold(max_response_time_p95=-100)
        assert exc_info.value.code == ErrorCode.CP25_THRESHOLD_INVALID

    def test_invalid_zero_response_time(self) -> None:
        """Threshold với response time bằng 0 sẽ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PerfThreshold(max_response_time_p95=0)
        assert exc_info.value.code == ErrorCode.CP25_THRESHOLD_INVALID

    def test_invalid_negative_throughput(self) -> None:
        """Threshold với throughput âm sẽ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PerfThreshold(min_throughput=-10)
        assert exc_info.value.code == ErrorCode.CP25_THRESHOLD_INVALID

    def test_invalid_error_rate_over_1(self) -> None:
        """Threshold với error_rate > 1 sẽ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PerfThreshold(max_error_rate=1.5)
        assert exc_info.value.code == ErrorCode.CP25_THRESHOLD_INVALID

    def test_invalid_error_rate_negative(self) -> None:
        """Threshold với error_rate âm sẽ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PerfThreshold(max_error_rate=-0.1)
        assert exc_info.value.code == ErrorCode.CP25_THRESHOLD_INVALID

    def test_invalid_cpu_percent_over_100(self) -> None:
        """Threshold với cpu_percent > 100 sẽ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PerfThreshold(max_cpu_percent=150)
        assert exc_info.value.code == ErrorCode.CP25_THRESHOLD_INVALID

    def test_invalid_memory_mb_zero(self) -> None:
        """Threshold với memory_mb = 0 sẽ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PerfThreshold(max_memory_mb=0)
        assert exc_info.value.code == ErrorCode.CP25_THRESHOLD_INVALID

    def test_to_dict_with_values(self) -> None:
        """to_dict trả về dict với các values đã set."""
        t = PerfThreshold(
            max_response_time_p95=500.0,
            max_error_rate=0.01,
        )
        d = t.to_dict()
        assert d["max_response_time_p95"] == 500.0
        assert d["max_error_rate"] == 0.01
        assert "max_response_time_p99" not in d

    def test_to_dict_empty(self) -> None:
        """to_dict trả về dict rỗng khi không có value nào."""
        t = PerfThreshold()
        d = t.to_dict()
        assert d == {}


class TestPerfScenario:
    """Test PerfScenario dataclass."""

    def test_create_scenario_with_all_fields(self) -> None:
        """Tạo scenario với đầy đủ fields."""
        s = PerfScenario(
            id="perf_order_create",
            type=PerfScenarioType.LOAD,
            target="CreateOrder",
            description="Test load tạo đơn hàng",
            concurrent_users=200,
            spawn_rate=20,
            duration=600,
            thresholds=PerfThreshold(max_response_time_p95=500),
            tags=["orders", "critical"],
        )
        assert s.id == "perf_order_create"
        assert s.type == PerfScenarioType.LOAD
        assert s.concurrent_users == 200
        assert s.spawn_rate == 20
        assert s.duration == 600

    def test_create_scenario_defaults(self) -> None:
        """Tạo scenario với default values."""
        s = PerfScenario(
            id="perf_search",
            type=PerfScenarioType.LOAD,
            target="SearchProducts",
        )
        assert s.concurrent_users == 100
        assert s.spawn_rate == 10
        assert s.duration == 300
        assert s.thresholds is None
        assert s.enabled is True
        assert s.tags == []

    def test_empty_id_raises_error(self) -> None:
        """Scenario với ID rỗng sẽ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PerfScenario(id="", type=PerfScenarioType.LOAD, target="X")
        assert exc_info.value.code == ErrorCode.CP25_EMPTY_SCENARIO_ID

    def test_empty_target_raises_error(self) -> None:
        """Scenario với target rỗng sẽ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PerfScenario(id="x", type=PerfScenarioType.LOAD, target="")
        assert exc_info.value.code == ErrorCode.CP25_MISSING_SCENARIO_TARGET

    def test_zero_concurrent_users_raises_error(self) -> None:
        """Scenario với concurrent_users = 0 sẽ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PerfScenario(id="x", type=PerfScenarioType.LOAD, target="T", concurrent_users=0)
        assert exc_info.value.code == ErrorCode.CP25_INVALID_CONCURRENCY

    def test_zero_spawn_rate_raises_error(self) -> None:
        """Scenario với spawn_rate = 0 sẽ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PerfScenario(id="x", type=PerfScenarioType.LOAD, target="T", spawn_rate=0)
        assert exc_info.value.code == ErrorCode.CP25_INVALID_CONCURRENCY

    def test_zero_duration_raises_error(self) -> None:
        """Scenario với duration = 0 sẽ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PerfScenario(id="x", type=PerfScenarioType.LOAD, target="T", duration=0)
        assert exc_info.value.code == ErrorCode.CP25_INVALID_DURATION

    def test_all_scenario_types(self) -> None:
        """Tạo scenario với mọi loại type."""
        for t in PerfScenarioType:
            s = PerfScenario(id=f"s_{t.value}", type=t, target="T")
            assert s.type == t

    def test_to_dict(self) -> None:
        """to_dict trả về dict đầy đủ."""
        s = PerfScenario(
            id="perf_load",
            type=PerfScenarioType.LOAD,
            target="CreateOrder",
            thresholds=PerfThreshold(max_response_time_p95=500),
        )
        d = s.to_dict()
        assert d["id"] == "perf_load"
        assert d["type"] == "load"
        assert d["target"] == "CreateOrder"
        assert d["thresholds"]["max_response_time_p95"] == 500
        assert d["enabled"] is True


class TestPerfBaseline:
    """Test PerfBaseline dataclass."""

    def test_create_baseline(self) -> None:
        """Tạo baseline hợp lệ."""
        b = PerfBaseline(
            id="baseline_v1",
            scenario_id="perf_order_create",
            timestamp="2026-05-20T00:00:00",
            response_time_p50=50.0,
            response_time_p95=200.0,
            response_time_p99=500.0,
            throughput_rps=100.0,
            error_rate=0.001,
            cpu_percent=45.0,
            memory_mb=256.0,
        )
        assert b.response_time_p50 == 50.0
        assert b.response_time_p95 == 200.0
        assert b.throughput_rps == 100.0

    def test_negative_response_time_raises_error(self) -> None:
        """Baseline với response_time âm sẽ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PerfBaseline(
                id="b1", scenario_id="s1", timestamp="2026-05-20",
                response_time_p50=-10, response_time_p95=200, response_time_p99=500,
                throughput_rps=100, error_rate=0.01,
            )
        assert exc_info.value.code == ErrorCode.CP25_INVALID_METRIC_VALUE

    def test_p50_greater_than_p95_raises_error(self) -> None:
        """p50 > p95 sẽ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PerfBaseline(
                id="b1", scenario_id="s1", timestamp="2026-05-20",
                response_time_p50=300, response_time_p95=200, response_time_p99=500,
                throughput_rps=100, error_rate=0.01,
            )
        assert exc_info.value.code == ErrorCode.CP25_INVALID_METRIC_VALUE

    def test_p95_greater_than_p99_raises_error(self) -> None:
        """p95 > p99 sẽ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PerfBaseline(
                id="b1", scenario_id="s1", timestamp="2026-05-20",
                response_time_p50=50, response_time_p95=600, response_time_p99=500,
                throughput_rps=100, error_rate=0.01,
            )
        assert exc_info.value.code == ErrorCode.CP25_INVALID_METRIC_VALUE

    def test_error_rate_over_1_raises_error(self) -> None:
        """error_rate > 1 sẽ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PerfBaseline(
                id="b1", scenario_id="s1", timestamp="2026-05-20",
                response_time_p50=50, response_time_p95=200, response_time_p99=500,
                throughput_rps=100, error_rate=1.5,
            )
        assert exc_info.value.code == ErrorCode.CP25_INVALID_METRIC_VALUE

    def test_to_dict(self) -> None:
        """to_dict trả về dict đầy đủ."""
        b = PerfBaseline(
            id="b1", scenario_id="s1", timestamp="2026-05-20",
            response_time_p50=50, response_time_p95=200, response_time_p99=500,
            throughput_rps=100, error_rate=0.01,
        )
        d = b.to_dict()
        assert d["id"] == "b1"
        assert d["response_time_p95"] == 200
        assert d["passed"] is True


class TestPerfSuite:
    """Test PerfSuite dataclass."""

    def test_create_suite(self) -> None:
        """Tạo suite hợp lệ."""
        s = PerfSuite(name="load_tests", stack="fastapi")
        assert s.name == "load_tests"
        assert s.stack == "fastapi"
        assert s.scenarios == []

    def test_empty_name_raises_error(self) -> None:
        """Suite với name rỗng sẽ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            PerfSuite(name="", stack="fastapi")
        assert exc_info.value.code == ErrorCode.CP25_EMPTY_SUITE_NAME

    def test_add_scenario(self) -> None:
        """Thêm scenario vào suite."""
        s = PerfSuite(name="tests", stack="fastapi")
        sc = PerfScenario(id="s1", type=PerfScenarioType.LOAD, target="T")
        s.add_scenario(sc)
        assert len(s.scenarios) == 1
        assert s.scenarios[0].id == "s1"

    def test_duplicate_scenario_raises_error(self) -> None:
        """Thêm scenario trùng ID sẽ throw error."""
        s = PerfSuite(name="tests", stack="fastapi")
        s.add_scenario(PerfScenario(id="s1", type=PerfScenarioType.LOAD, target="T"))
        with pytest.raises(MidicoderError) as exc_info:
            s.add_scenario(PerfScenario(id="s1", type=PerfScenarioType.LOAD, target="T2"))
        assert exc_info.value.code == ErrorCode.CP25_DUPLICATE_SCENARIO_ID

    def test_get_scenario_by_id(self) -> None:
        """Tìm scenario theo ID."""
        s = PerfSuite(name="tests", stack="fastapi")
        s.add_scenario(PerfScenario(id="s1", type=PerfScenarioType.LOAD, target="T"))
        assert s.get_scenario_by_id("s1").id == "s1"
        assert s.get_scenario_by_id("nonexistent") is None

    def test_get_enabled_scenarios(self) -> None:
        """Lọc scenarios đang active."""
        s = PerfSuite(name="tests", stack="fastapi")
        s.add_scenario(PerfScenario(id="s1", type=PerfScenarioType.LOAD, target="T", enabled=True))
        s.add_scenario(PerfScenario(id="s2", type=PerfScenarioType.STRESS, target="T", enabled=False))
        assert len(s.get_enabled_scenarios()) == 1

    def test_get_scenarios_by_type(self) -> None:
        """Lọc scenarios theo type."""
        s = PerfSuite(name="tests", stack="fastapi")
        s.add_scenario(PerfScenario(id="s1", type=PerfScenarioType.LOAD, target="T"))
        s.add_scenario(PerfScenario(id="s2", type=PerfScenarioType.STRESS, target="T"))
        assert len(s.get_scenarios_by_type(PerfScenarioType.LOAD)) == 1
        assert len(s.get_scenarios_by_type(PerfScenarioType.STRESS)) == 1

    def test_to_dict(self) -> None:
        """to_dict trả về dict đầy đủ."""
        s = PerfSuite(
            name="tests", stack="fastapi",
            default_thresholds=PerfThreshold(max_response_time_p95=500),
        )
        s.add_scenario(PerfScenario(id="s1", type=PerfScenarioType.LOAD, target="T"))
        d = s.to_dict()
        assert d["name"] == "tests"
        assert d["stack"] == "fastapi"
        assert len(d["scenarios"]) == 1
        assert d["default_thresholds"]["max_response_time_p95"] == 500


class TestPerfCollection:
    """Test PerfCollection dataclass."""

    def test_create_empty_collection(self) -> None:
        """Tạo collection rỗng."""
        c = PerfCollection()
        assert c.suites == []
        assert c.baselines == []

    def test_add_suite_and_baseline(self) -> None:
        """Thêm suite và baseline vào collection."""
        c = PerfCollection()
        suite = PerfSuite(name="tests", stack="fastapi")
        c.add_suite(suite)
        b = PerfBaseline(
            id="b1", scenario_id="s1", timestamp="2026-05-20",
            response_time_p50=50, response_time_p95=200, response_time_p99=500,
            throughput_rps=100, error_rate=0.01,
        )
        c.add_baseline(b)
        assert len(c.suites) == 1
        assert len(c.baselines) == 1

    def test_get_suites_by_stack(self) -> None:
        """Lọc suites theo stack."""
        c = PerfCollection()
        c.add_suite(PerfSuite(name="fast", stack="fastapi"))
        c.add_suite(PerfSuite(name="nest", stack="nestjs"))
        assert len(c.get_suites_by_stack("fastapi")) == 1
        assert len(c.get_suites_by_stack("nestjs")) == 1

    def test_get_all_scenarios(self) -> None:
        """Lấy tất cả scenarios."""
        c = PerfCollection()
        s1 = PerfSuite(name="s1", stack="fastapi")
        s1.add_scenario(PerfScenario(id="sc1", type=PerfScenarioType.LOAD, target="T"))
        s2 = PerfSuite(name="s2", stack="fastapi")
        s2.add_scenario(PerfScenario(id="sc2", type=PerfScenarioType.STRESS, target="T"))
        c.add_suite(s1)
        c.add_suite(s2)
        assert len(c.get_all_scenarios()) == 2

    def test_get_baseline_by_scenario(self) -> None:
        """Tìm baseline theo scenario ID."""
        c = PerfCollection()
        b = PerfBaseline(
            id="b1", scenario_id="perf_s1", timestamp="2026-05-20",
            response_time_p50=50, response_time_p95=200, response_time_p99=500,
            throughput_rps=100, error_rate=0.01,
        )
        c.add_baseline(b)
        assert c.get_baseline_by_scenario("perf_s1").id == "b1"
        assert c.get_baseline_by_scenario("nonexistent") is None

    def test_count_scenarios(self) -> None:
        """Đếm scenarios theo type."""
        c = PerfCollection()
        s = PerfSuite(name="tests", stack="fastapi")
        s.add_scenario(PerfScenario(id="s1", type=PerfScenarioType.LOAD, target="T"))
        s.add_scenario(PerfScenario(id="s2", type=PerfScenarioType.LOAD, target="T"))
        s.add_scenario(PerfScenario(id="s3", type=PerfScenarioType.STRESS, target="T"))
        c.add_suite(s)
        counts = c.count_scenarios()
        assert counts["load"] == 2
        assert counts["stress"] == 1

    def test_to_dict_and_from_dict(self) -> None:
        """to_dict và from_dict là inverse của nhau."""
        c = PerfCollection()
        s = PerfSuite(
            name="tests", stack="fastapi",
            default_thresholds=PerfThreshold(max_response_time_p95=500),
        )
        s.add_scenario(PerfScenario(
            id="s1", type=PerfScenarioType.LOAD, target="CreateOrder",
            concurrent_users=200, spawn_rate=20, duration=600,
            thresholds=PerfThreshold(max_response_time_p95=300),
        ))
        c.add_suite(s)

        d = c.to_dict()
        c2 = PerfCollection.from_dict(d)

        assert len(c2.suites) == 1
        assert c2.suites[0].name == "tests"
        assert c2.suites[0].stack == "fastapi"
        assert len(c2.suites[0].scenarios) == 1
        assert c2.suites[0].scenarios[0].id == "s1"
        assert c2.suites[0].scenarios[0].concurrent_users == 200
