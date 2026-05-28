# coding: utf-8
"""
Unit tests cho BaselineManager của CP25.

Author: Midicoder Team
Version: 1.0.0
"""

import os
import tempfile

import pytest

from midicoder.packs.cp_full_quality_security.baseline import BaselineManager
from midicoder.packs.cp_full_quality_security.models import PerfBaseline


class TestBaselineManager:
    """Test BaselineManager."""

    def setup_method(self) -> None:
        """Setup temp DB cho mỗi test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "artifacts.db")
        self.manager = BaselineManager(self.db_path)

        # Tạo DB schema
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                artifact_id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                content TEXT,
                metadata TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def test_save_and_load(self) -> None:
        """Lưu và load baseline."""
        baseline = PerfBaseline(
            id="baseline_test", scenario_id="perf_s1", timestamp="2026-05-20",
            response_time_p50=50, response_time_p95=200, response_time_p99=500,
            throughput_rps=100, error_rate=0.01,
        )
        self.manager.save(baseline)

        loaded = self.manager.load_latest("perf_s1")
        assert loaded is not None
        assert loaded.id == "baseline_test"
        assert loaded.response_time_p95 == 200

    def test_load_nonexistent(self) -> None:
        """Load baseline không tồn tại trả về None."""
        result = self.manager.load_latest("nonexistent")
        assert result is None

    def test_load_latest_returns_newest(self) -> None:
        """Load latest trả về baseline mới nhất."""
        b1 = PerfBaseline(
            id="b1", scenario_id="perf_s1", timestamp="2026-05-19",
            response_time_p50=50, response_time_p95=200, response_time_p99=500,
            throughput_rps=100, error_rate=0.01,
        )
        b2 = PerfBaseline(
            id="b2", scenario_id="perf_s1", timestamp="2026-05-20",
            response_time_p50=60, response_time_p95=240, response_time_p99=600,
            throughput_rps=80, error_rate=0.02,
        )
        self.manager.save(b1)
        self.manager.save(b2)

        loaded = self.manager.load_latest("perf_s1")
        assert loaded.id == "b2"

    def test_compare_with_baseline(self) -> None:
        """So sánh current với baseline cũ."""
        baseline = PerfBaseline(
            id="old", scenario_id="perf_s1", timestamp="2026-05-19",
            response_time_p50=50, response_time_p95=200, response_time_p99=500,
            throughput_rps=100, error_rate=0.01,
        )
        self.manager.save(baseline)

        current = PerfBaseline(
            id="new", scenario_id="perf_s1", timestamp="2026-05-20",
            response_time_p50=60, response_time_p95=240, response_time_p99=600,
            throughput_rps=80, error_rate=0.02,
        )

        report = self.manager.compare(current, "perf_s1")

        assert report.current == current
        assert report.baseline == baseline
        assert "response_time_p50_change_pct" in report.diff
        assert report.diff["response_time_p50_change_pct"] == 20.0  # (60-50)/50*100

    def test_compare_no_baseline(self) -> None:
        """So sánh khi không có baseline cũ."""
        current = PerfBaseline(
            id="first", scenario_id="perf_new", timestamp="2026-05-20",
            response_time_p50=50, response_time_p95=200, response_time_p99=500,
            throughput_rps=100, error_rate=0.01,
        )

        report = self.manager.compare(current, "perf_new")

        assert report.current == current
        assert report.baseline is None
        assert report.diff == {}

    def test_load_all(self) -> None:
        """Load tất cả baselines cho 1 scenario."""
        b1 = PerfBaseline(
            id="b1", scenario_id="perf_s1", timestamp="2026-05-19",
            response_time_p50=50, response_time_p95=200, response_time_p99=500,
            throughput_rps=100, error_rate=0.01,
        )
        b2 = PerfBaseline(
            id="b2", scenario_id="perf_s1", timestamp="2026-05-20",
            response_time_p50=60, response_time_p95=240, response_time_p99=600,
            throughput_rps=80, error_rate=0.02,
        )
        self.manager.save(b1)
        self.manager.save(b2)

        baselines = self.manager.load_all("perf_s1")
        assert len(baselines) == 2
        # Newest first
        assert baselines[0].id == "b2"
