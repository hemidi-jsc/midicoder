# coding: utf-8
"""
Mô-đun baseline management cho Performance Testing Generator (CP25).

Quản lý baseline:
- BaselineManager: Lưu/load/so sánh baseline vào/từ SQLite artifacts

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from midicoder.packs.cp25_performance_testing.models import (
    PerfBaseline,
    PerfReport,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class BaselineManager:
    """
    Quản lý baseline — lưu, load, so sánh baseline vào/từ SQLite artifacts.

    Attributes:
        db_path: Đường dẫn đến artifacts.db
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        """
        Init BaselineManager.

        Args:
            db_path: Đường dẫn đến SQLite DB. Mặc định: .midicoder/data/artifacts.db
        """
        if db_path is None:
            self.db_path = Path(".midicoder/data/artifacts.db")
        else:
            self.db_path = Path(db_path)

    def save(self, baseline: PerfBaseline) -> str:
        """
        Lưu baseline vào SQLite artifacts.

        Args:
            baseline: PerfBaseline instance

        Returns:
            Baseline ID

        Raises:
            MidicoderError: Nếu lưu thất bại
        """
        import sqlite3

        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(str(self.db_path))
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO artifacts
                    (artifact_id, type, name, content, metadata, created_at)
                    VALUES (?, 'perf_baseline', ?, ?, ?, ?)
                """, (
                    baseline.id,
                    baseline.scenario_id,
                    json.dumps(baseline.to_dict()),
                    json.dumps({
                        "scenario_id": baseline.scenario_id,
                        "timestamp": baseline.timestamp,
                    }),
                    baseline.timestamp,
                ))
                conn.commit()
            finally:
                conn.close()

            return baseline.id

        except Exception as e:
            EM.raise_error(
                ErrorCode.CP25_BASELINE_SAVE_FAILED,
                baseline_id=baseline.id,
                error=str(e)
            )

    def load_latest(self, scenario_id: str) -> Optional[PerfBaseline]:
        """
        Load baseline mới nhất cho 1 scenario.

        Args:
            scenario_id: ID của scenario

        Returns:
            PerfBaseline hoặc None nếu không có
        """
        import sqlite3

        if not self.db_path.exists():
            return None

        try:
            conn = sqlite3.connect(str(self.db_path))
            try:
                row = conn.execute("""
                    SELECT content FROM artifacts
                    WHERE type = 'perf_baseline' AND name = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (scenario_id,)).fetchone()

                if row:
                    data = json.loads(row[0])
                    return PerfBaseline(
                        id=data["id"],
                        scenario_id=data["scenario_id"],
                        timestamp=data["timestamp"],
                        response_time_p50=data["response_time_p50"],
                        response_time_p95=data["response_time_p95"],
                        response_time_p99=data["response_time_p99"],
                        throughput_rps=data["throughput_rps"],
                        error_rate=data["error_rate"],
                        cpu_percent=data.get("cpu_percent", 0.0),
                        memory_mb=data.get("memory_mb", 0.0),
                        passed=data.get("passed", True),
                        metadata=data.get("metadata", {}),
                    )
                return None
            finally:
                conn.close()

        except Exception:
            return None

    def load_all(self, scenario_id: str) -> list[PerfBaseline]:
        """
        Load tất cả baselines cho 1 scenario.

        Args:
            scenario_id: ID của scenario

        Returns:
            Danh sách PerfBaseline
        """
        import sqlite3

        if not self.db_path.exists():
            return []

        try:
            conn = sqlite3.connect(str(self.db_path))
            try:
                rows = conn.execute("""
                    SELECT content FROM artifacts
                    WHERE type = 'perf_baseline' AND name = ?
                    ORDER BY created_at DESC
                """, (scenario_id,)).fetchall()

                baselines: list[PerfBaseline] = []
                for row in rows:
                    data = json.loads(row[0])
                    baselines.append(PerfBaseline(
                        id=data["id"],
                        scenario_id=data["scenario_id"],
                        timestamp=data["timestamp"],
                        response_time_p50=data["response_time_p50"],
                        response_time_p95=data["response_time_p95"],
                        response_time_p99=data["response_time_p99"],
                        throughput_rps=data["throughput_rps"],
                        error_rate=data["error_rate"],
                        cpu_percent=data.get("cpu_percent", 0.0),
                        memory_mb=data.get("memory_mb", 0.0),
                        passed=data.get("passed", True),
                        metadata=data.get("metadata", {}),
                    ))
                return baselines
            finally:
                conn.close()

        except Exception:
            return []

    def compare(
        self,
        current: PerfBaseline,
        scenario_id: str,
    ) -> PerfReport:
        """
        So sánh current baseline với baseline cũ nhất.

        Args:
            current: Current baseline
            scenario_id: ID của scenario

        Returns:
            PerfReport chứa current, baseline (nếu có), và diff
        """
        report = PerfReport(
            run_id=current.id,
            scenario_id=scenario_id,
            current=current,
        )

        baseline = self.load_latest(scenario_id)
        if baseline:
            report.baseline_id = baseline.id
            report.baseline = baseline
            report.diff = self._compute_diff(current, baseline)

            # Kiểm tra thresholds
            if current.response_time_p95 <= (baseline.response_time_p95 * 1.2):
                report.thresholds_passed.append("response_time_p95")
            else:
                report.thresholds_failed.append("response_time_p95")

            if current.error_rate <= (baseline.error_rate * 2):
                report.thresholds_passed.append("error_rate")
            else:
                report.thresholds_failed.append("error_rate")

        return report

    @staticmethod
    def _compute_diff(current: PerfBaseline, baseline: PerfBaseline) -> dict[str, float]:
        """Tính percentage change giữa current và baseline."""
        diff: dict[str, float] = {}

        for key in ["response_time_p50", "response_time_p95", "response_time_p99"]:
            current_val = getattr(current, key)
            baseline_val = getattr(baseline, key)
            if baseline_val > 0:
                change = ((current_val - baseline_val) / baseline_val) * 100
                diff[f"{key}_change_pct"] = round(change, 2)

        if baseline.throughput_rps > 0:
            change = ((current.throughput_rps - baseline.throughput_rps) / baseline.throughput_rps) * 100
            diff["throughput_rps_change_pct"] = round(change, 2)

        diff["error_rate_change"] = round(current.error_rate - baseline.error_rate, 4)

        return diff
