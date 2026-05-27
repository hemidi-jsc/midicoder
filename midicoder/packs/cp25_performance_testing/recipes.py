# coding: utf-8
"""
Mô-đun recipes cho Performance Testing Generator (CP25).

Các recipe helper:
- auto_generate_perf_scenarios_from_mir: Tự động tạo scenarios từ MIR
- generate_load_scenarios: Sinh load scenarios cho API endpoints
- generate_web_vitals_tests: Sinh Web Vitals tests cho frontend
- save_baseline: Lưu baseline vào SQLite
- compare_baseline: So sánh baseline mới vs cũ

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from midicoder.packs.cp25_performance_testing.models import (
    PerfBaseline,
    PerfCollection,
    PerfScenario,
    PerfScenarioType,
    PerfSuite,
)


def auto_generate_perf_scenarios_from_mir(
    metadata: dict[str, Any],
    stack: str = "fastapi",
) -> PerfCollection:
    """
    Tự động tạo perf scenarios từ MIR metadata.

    Tạo load scenario cho mỗi command và query trong MIR.

    Args:
        metadata: MIR metadata dict (chứa entities, commands, queries)
        stack: Target stack name

    Returns:
        PerfCollection với scenarios auto-generated
    """
    collection = PerfCollection()
    suite = PerfSuite(name=f"{stack}_perf_tests", stack=stack)

    # Tạo load scenario cho mỗi command
    commands = metadata.get("commands", [])
    for cmd in commands:
        if isinstance(cmd, dict):
            cmd_id = cmd.get("id", "")
            if cmd_id:
                scenario = PerfScenario(
                    id=f"perf_{cmd_id.lower()}",
                    type=PerfScenarioType.LOAD,
                    target=cmd_id,
                    description=f"Load test cho command {cmd_id}",
                    concurrent_users=100,
                    spawn_rate=10,
                    duration=300,
                )
                suite.add_scenario(scenario)

    # Tạo load scenario cho mỗi query (ít users hơn)
    queries = metadata.get("queries", [])
    for qry in queries:
        if isinstance(qry, dict):
            qry_id = qry.get("id", "")
            if qry_id:
                scenario = PerfScenario(
                    id=f"perf_{qry_id.lower()}",
                    type=PerfScenarioType.LOAD,
                    target=qry_id,
                    description=f"Load test cho query {qry_id}",
                    concurrent_users=50,
                    spawn_rate=5,
                    duration=180,
                )
                suite.add_scenario(scenario)

    if suite.scenarios:
        collection.add_suite(suite)

    return collection


def generate_load_scenarios(
    targets: list[str],
    stack: str = "fastapi",
    concurrent_users: int = 100,
    spawn_rate: int = 10,
    duration: int = 300,
) -> PerfCollection:
    """
    Sinh load scenarios cho danh sách API endpoints.

    Args:
        targets: Danh sách target IDs (entity/command/query)
        stack: Target stack name
        concurrent_users: Số user đồng thời
        spawn_rate: Tốc độ spawn user (user/giây)
        duration: Thời gian chạy (giây)

    Returns:
        PerfCollection với load scenarios
    """
    collection = PerfCollection()
    suite = PerfSuite(name=f"{stack}_load_tests", stack=stack)

    for target in targets:
        scenario = PerfScenario(
            id=f"perf_{target.lower()}",
            type=PerfScenarioType.LOAD,
            target=target,
            description=f"Load test cho {target}",
            concurrent_users=concurrent_users,
            spawn_rate=spawn_rate,
            duration=duration,
        )
        suite.add_scenario(scenario)

    if suite.scenarios:
        collection.add_suite(suite)

    return collection


def generate_web_vitals_tests(
    pages: list[str],
    stack: str = "react",
) -> PerfCollection:
    """
    Sinh Web Vitals tests cho frontend pages.

    Tạo endurance scenario cho mỗi page URL.

    Args:
        pages: Danh sách page URLs
        stack: Target frontend stack (angular, react)

    Returns:
        PerfCollection với web vitals scenarios
    """
    collection = PerfCollection()
    suite = PerfSuite(name=f"{stack}_web_vitals", stack=stack)

    for page in pages:
        scenario = PerfScenario(
            id=f"perf_vitals_{page.replace('/', '_').strip('_').lower()}",
            type=PerfScenarioType.ENDURANCE,
            target=page,
            description=f"Web Vitals test cho trang {page}",
            concurrent_users=10,
            spawn_rate=1,
            duration=600,
        )
        suite.add_scenario(scenario)

    if suite.scenarios:
        collection.add_suite(suite)

    return collection


def save_baseline(
    scenario_id: str,
    metrics: dict[str, float],
) -> PerfBaseline:
    """
    Tạo PerfBaseline từ metrics dict.

    Lưu baseline vào SQLite artifacts (type="perf_baseline").

    Args:
        scenario_id: ID của scenario
        metrics: Dict chứa metrics (response_time_p50, p95, p99, throughput_rps, error_rate)

    Returns:
        PerfBaseline instance đã tạo
    """
    import time
    from datetime import datetime, timezone

    baseline_id = f"baseline_{scenario_id}_{int(time.time())}"
    timestamp = datetime.now(timezone.utc).isoformat()

    baseline = PerfBaseline(
        id=baseline_id,
        scenario_id=scenario_id,
        timestamp=timestamp,
        response_time_p50=metrics.get("response_time_p50", 0.0),
        response_time_p95=metrics.get("response_time_p95", 0.0),
        response_time_p99=metrics.get("response_time_p99", 0.0),
        throughput_rps=metrics.get("throughput_rps", 0.0),
        error_rate=metrics.get("error_rate", 0.0),
        cpu_percent=metrics.get("cpu_percent", 0.0),
        memory_mb=metrics.get("memory_mb", 0.0),
    )

    return baseline


def compare_baseline(
    current: PerfBaseline,
    baseline: PerfBaseline,
) -> dict[str, float]:
    """
    So sánh current baseline với baseline cũ.

    Trả về dict chứa percentage change cho mỗi metric.

    Args:
        current: Current baseline
        baseline: Baseline cũ để so sánh

    Returns:
        Dict chứa percentage change (âm = cải thiện cho response time)
    """
    diff: dict[str, float] = {}

    # Response time — giảm là tốt (âm = cải thiện)
    for key in ["response_time_p50", "response_time_p95", "response_time_p99"]:
        current_val = getattr(current, key)
        baseline_val = getattr(baseline, key)
        if baseline_val > 0:
            change = ((current_val - baseline_val) / baseline_val) * 100
            diff[f"{key}_change_pct"] = round(change, 2)

    # Throughput — tăng là tốt (dương = cải thiện)
    if baseline.throughput_rps > 0:
        change = ((current.throughput_rps - baseline.throughput_rps) / baseline.throughput_rps) * 100
        diff["throughput_rps_change_pct"] = round(change, 2)

    # Error rate — giảm là tốt (âm = cải thiện)
    diff["error_rate_change"] = round(current.error_rate - baseline.error_rate, 4)

    return diff
