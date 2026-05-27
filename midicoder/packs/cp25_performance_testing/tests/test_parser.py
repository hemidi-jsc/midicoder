# coding: utf-8
"""
Unit tests cho PerfParser của Performance Testing Generator (CP25).

Author: Midicoder Team
Version: 1.0.0
"""

import pytest

from midicoder.packs.cp25_performance_testing.parser import PerfParser
from midicoder.packs.cp25_performance_testing.models import PerfScenarioType
from midicoder.errors import MidicoderError


class TestPerfParser:
    """Test PerfParser class."""

    def setup_method(self) -> None:
        """Setup parser instance."""
        self.parser = PerfParser()

    def test_parse_empty_string(self) -> None:
        """Parse string rỗng trả về collection rỗng."""
        result = self.parser.parse("")
        assert len(result.suites) == 0

    def test_parse_none_string(self) -> None:
        """Parse string chứa 'null' trả về collection rỗng."""
        result = self.parser.parse("null")
        assert len(result.suites) == 0

    def test_parse_invalid_yaml(self) -> None:
        """Parse YAML không hợp lệ throw error."""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse("::: invalid yaml :::")
        assert "CP25_DSL_PARSE_ERROR" in str(exc_info.value.code)

    def test_parse_flat_scenarios(self) -> None:
        """Parse danh sách scenarios dạng flat."""
        yaml_str = """
stack: fastapi
perf_scenarios:
  - id: perf_order_create
    type: load
    target: CreateOrder
    concurrent_users: 200
    spawn_rate: 20
    duration: 600
    thresholds:
      max_response_time_p95: 500
      max_error_rate: 0.01
  - id: perf_product_search
    type: stress
    target: SearchProducts
    concurrent_users: 500
    spawn_rate: 50
    duration: 300
"""
        result = self.parser.parse(yaml_str)
        assert len(result.suites) == 1
        assert result.suites[0].stack == "fastapi"
        assert len(result.suites[0].scenarios) == 2
        assert result.suites[0].scenarios[0].id == "perf_order_create"
        assert result.suites[0].scenarios[0].type == PerfScenarioType.LOAD
        assert result.suites[0].scenarios[0].concurrent_users == 200
        assert result.suites[0].scenarios[0].thresholds.max_response_time_p95 == 500

    def test_parse_suite_definition(self) -> None:
        """Parse suite definition với nhiều scenarios."""
        yaml_str = """
perf_suites:
  - name: backend_perf
    stack: fastapi
    default_thresholds:
      max_response_time_p95: 1000
    scenarios:
      - id: perf_create
        type: load
        target: CreateOrder
        concurrent_users: 100
"""
        result = self.parser.parse(yaml_str)
        assert len(result.suites) == 1
        assert result.suites[0].name == "backend_perf"
        assert result.suites[0].default_thresholds.max_response_time_p95 == 1000

    def test_parse_baselines(self) -> None:
        """Parse baseline definitions."""
        yaml_str = """
perf_baselines:
  - id: baseline_v1
    scenario_id: perf_order_create
    timestamp: "2026-05-20T00:00:00"
    response_time_p50: 50.0
    response_time_p95: 200.0
    response_time_p99: 500.0
    throughput_rps: 100.0
    error_rate: 0.001
"""
        result = self.parser.parse(yaml_str)
        assert len(result.baselines) == 1
        assert result.baselines[0].id == "baseline_v1"
        assert result.baselines[0].response_time_p95 == 200.0

    def test_parse_dict_input(self) -> None:
        """Parse dict input trực tiếp."""
        data = {
            "stack": "nestjs",
            "perf_scenarios": [
                {"id": "s1", "type": "load", "target": "T1"},
            ],
        }
        result = self.parser.parse(data)
        assert len(result.suites) == 1
        assert result.suites[0].stack == "nestjs"

    def test_parse_invalid_scenario_type(self) -> None:
        """Parse scenario type không hợp lệ throw error."""
        yaml_str = """
perf_scenarios:
  - id: s1
    type: invalid_type
    target: T1
"""
        with pytest.raises(MidicoderError) as exc_info:
            self.parser.parse(yaml_str)
        assert exc_info.value.code.value == "MDC-CP25-003"

    def test_parse_from_metadata_with_commands(self) -> None:
        """Parse từ MIR metadata chứa commands."""
        metadata = {
            "commands": [
                {"id": "CreateOrder"},
                {"id": "CreateCustomer"},
            ],
            "queries": [
                {"id": "SearchProducts"},
            ],
        }
        result = self.parser.parse_from_metadata(metadata, stack="fastapi")
        assert len(result.suites) == 1
        # 2 commands + 1 query = 3 scenarios
        assert len(result.suites[0].scenarios) == 3

    def test_parse_from_metadata_with_explicit_perf(self) -> None:
        """Parse từ MIR metadata có explicit perf_scenarios."""
        metadata = {
            "perf_scenarios": [
                {"id": "perf_explicit", "type": "load", "target": "ExplicitTarget", "concurrent_users": 150},
            ],
            "commands": [{"id": "CreateOrder"}],  # ignored khi có explicit
        }
        result = self.parser.parse_from_metadata(metadata, stack="fastapi")
        assert len(result.suites) == 1
        assert len(result.suites[0].scenarios) == 1
        assert result.suites[0].scenarios[0].id == "perf_explicit"

    def test_parse_from_metadata_empty(self) -> None:
        """Parse metadata rỗng trả về collection rỗng."""
        result = self.parser.parse_from_metadata({}, stack="fastapi")
        assert len(result.suites) == 0
