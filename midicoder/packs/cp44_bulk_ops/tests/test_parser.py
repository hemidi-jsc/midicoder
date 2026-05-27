# coding: utf-8
"""
Test parser cho CP44 — Bulk Operations Engine.

Test đầy đủ:
- BulkIR: tạo, to_dict, from_dict, roundtrip
- parse_bulk_jobs: parse từ DSL dict
- parse_bulk_config: parse config từ DSL dict
- parse_dlq_config: parse DLQ config
- parse_to_ir: parse toàn bộ DSL dict thành BulkIR
"""

import pytest

from midicoder.packs.cp44_bulk_ops.parser import (
    BulkIR,
    parse_bulk_config,
    parse_bulk_jobs,
    parse_dlq_config,
    parse_to_ir,
)
from midicoder.packs.cp44_bulk_ops.models import (
    BulkAction,
    RetryStrategy,
)


# ============================================================================
# Test BulkIR
# ============================================================================


class TestBulkIR:
    """Test dataclass BulkIR."""

    def test_create_default(self):
        """Tạo BulkIR với giá trị mặc định."""
        ir = BulkIR()
        assert ir.jobs == []
        assert ir.default_chunk_size == 100
        assert ir.default_concurrency == 10
        assert ir.default_max_retries == 3
        assert ir.default_retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert ir.default_timeout == 300
        assert ir.dlq_enabled is True
        assert ir.use_events is True
        assert ir.use_audit is True

    def test_create_custom(self):
        """Tạo BulkIR với config tùy chỉnh."""
        ir = BulkIR(
            default_chunk_size=50,
            default_concurrency=5,
            default_max_retries=5,
            default_retry_strategy=RetryStrategy.FIXED_DELAY,
            default_timeout=600,
            dlq_enabled=False,
            use_events=False,
            use_audit=False,
        )
        assert ir.default_chunk_size == 50
        assert ir.default_concurrency == 5
        assert ir.default_retry_strategy == RetryStrategy.FIXED_DELAY
        assert ir.dlq_enabled is False

    def test_to_dict(self):
        """Chuyển BulkIR sang dict."""
        ir = BulkIR(
            default_chunk_size=75,
            default_retry_strategy=RetryStrategy.LINEAR_BACKOFF,
        )
        d = ir.to_dict()
        assert d["default_chunk_size"] == 75
        assert d["default_retry_strategy"] == "linear_backoff"
        assert d["jobs"] == []
        assert d["dlq_enabled"] is True

    def test_from_dict(self):
        """Tạo BulkIR từ dict."""
        d = {
            "default_chunk_size": 200,
            "default_concurrency": 20,
            "default_max_retries": 5,
            "default_retry_strategy": "fixed_delay",
            "default_timeout": 600,
            "dlq_enabled": False,
        }
        ir = BulkIR.from_dict(d)
        assert ir.default_chunk_size == 200
        assert ir.default_concurrency == 20
        assert ir.default_retry_strategy == RetryStrategy.FIXED_DELAY
        assert ir.dlq_enabled is False

    def test_roundtrip(self):
        """to_dict -> from_dict giữ nguyên dữ liệu."""
        original = BulkIR(
            default_chunk_size=50,
            default_concurrency=5,
            default_max_retries=5,
            default_retry_strategy=RetryStrategy.LINEAR_BACKOFF,
            default_timeout=120,
            dlq_enabled=False,
            use_events=False,
        )
        restored = BulkIR.from_dict(original.to_dict())
        assert restored.default_chunk_size == original.default_chunk_size
        assert restored.default_concurrency == original.default_concurrency
        assert restored.default_max_retries == original.default_max_retries
        assert restored.default_retry_strategy == original.default_retry_strategy
        assert restored.default_timeout == original.default_timeout
        assert restored.dlq_enabled == original.dlq_enabled
        assert restored.use_events == original.use_events


# ============================================================================
# Test parse_bulk_jobs
# ============================================================================


class TestParseBulkJobs:
    """Test parse_bulk_jobs function."""

    def test_parse_empty(self):
        """Parse dict rỗng trả về list rỗng."""
        result = parse_bulk_jobs({})
        assert result == []

    def test_parse_with_bulk_jobs_key(self):
        """Parse với key 'bulk_jobs'."""
        data = {
            "bulk_jobs": [
                {
                    "job_id": "j1",
                    "entity_type": "user",
                    "action": "batch_update",
                    "entity_ids": ["u1", "u2"],
                }
            ]
        }
        result = parse_bulk_jobs(data)
        assert len(result) == 1
        assert result[0].job_id == "j1"
        assert result[0].entity_type == "user"
        assert result[0].action == BulkAction.BATCH_UPDATE

    def test_parse_with_jobs_key(self):
        """Parse với key 'jobs' (alias)."""
        data = {
            "jobs": [
                {"id": "j2", "type": "product", "action": "batch_delete", "ids": ["p1"]}
            ]
        }
        result = parse_bulk_jobs(data)
        assert len(result) == 1
        assert result[0].job_id == "j2"
        assert result[0].entity_type == "product"
        assert result[0].action == BulkAction.BATCH_DELETE

    def test_parse_multiple_jobs(self):
        """Parse nhiều jobs."""
        data = {
            "bulk_jobs": [
                {"job_id": "j1", "entity_type": "u", "action": "batch_update"},
                {"job_id": "j2", "entity_type": "p", "action": "batch_create"},
                {"job_id": "j3", "entity_type": "o", "action": "batch_delete"},
            ]
        }
        result = parse_bulk_jobs(data)
        assert len(result) == 3

    def test_parse_with_config(self):
        """Parse job có config tùy chỉnh."""
        data = {
            "bulk_jobs": [
                {
                    "job_id": "j1",
                    "entity_type": "user",
                    "action": "batch_update",
                    "chunk_size": 50,
                    "max_concurrency": 5,
                    "max_retries": 5,
                    "retry_strategy": "fixed_delay",
                    "timeout_seconds": 600,
                    "tenant_id": "t1",
                }
            ]
        }
        result = parse_bulk_jobs(data)
        assert result[0].chunk_size == 50
        assert result[0].max_concurrency == 5
        assert result[0].max_retries == 5
        assert result[0].retry_strategy == RetryStrategy.FIXED_DELAY
        assert result[0].timeout_seconds == 600


# ============================================================================
# Test parse_bulk_config
# ============================================================================


class TestParseBulkConfig:
    """Test parse_bulk_config function."""

    def test_parse_defaults(self):
        """Parse dict rỗng trả về defaults."""
        result = parse_bulk_config({})
        assert result["default_chunk_size"] == 100
        assert result["default_concurrency"] == 10
        assert result["default_max_retries"] == 3
        assert result["default_retry_strategy"] == "exponential_backoff"
        assert result["default_timeout"] == 300

    def test_parse_custom(self):
        """Parse config tùy chỉnh."""
        data = {
            "default_chunk_size": 200,
            "default_concurrency": 20,
            "default_max_retries": 5,
            "default_retry_strategy": "linear_backoff",
            "default_timeout": 600,
        }
        result = parse_bulk_config(data)
        assert result["default_chunk_size"] == 200
        assert result["default_concurrency"] == 20

    def test_parse_short_keys(self):
        """Parse với short keys (alias)."""
        data = {
            "chunk_size": 50,
            "concurrency": 5,
            "max_retries": 2,
            "retry_strategy": "fixed_delay",
            "timeout": 120,
        }
        result = parse_bulk_config(data)
        assert result["default_chunk_size"] == 50
        assert result["default_concurrency"] == 5
        assert result["default_timeout"] == 120


# ============================================================================
# Test parse_dlq_config
# ============================================================================


class TestParseDLQConfig:
    """Test parse_dlq_config function."""

    def test_parse_empty(self):
        """Parse dict rỗng trả về dlq_enabled=True."""
        result = parse_dlq_config({})
        assert result["dlq_enabled"] is True

    def test_parse_dict_enabled(self):
        """Parse dict với enabled=True."""
        data = {"dlq": {"enabled": True}}
        result = parse_dlq_config(data)
        assert result["dlq_enabled"] is True

    def test_parse_dict_disabled(self):
        """Parse dict với enabled=False."""
        data = {"dead_letter_queue": {"enabled": False}}
        result = parse_dlq_config(data)
        assert result["dlq_enabled"] is False

    def test_parse_bool_true(self):
        """Parse boolean True."""
        data = {"dlq": True}
        result = parse_dlq_config(data)
        assert result["dlq_enabled"] is True

    def test_parse_bool_false(self):
        """Parse boolean False."""
        data = {"dlq": False}
        result = parse_dlq_config(data)
        assert result["dlq_enabled"] is False


# ============================================================================
# Test parse_to_ir
# ============================================================================


class TestParseToIR:
    """Test parse_to_ir function."""

    def test_parse_empty(self):
        """Parse dict rỗng trả về BulkIR với defaults."""
        ir = parse_to_ir({})
        assert ir.jobs == []
        assert ir.default_chunk_size == 100
        assert ir.dlq_enabled is True

    def test_parse_full(self):
        """Parse DSL dict đầy đủ."""
        data = {
            "bulk_jobs": [
                {
                    "job_id": "j1",
                    "entity_type": "user",
                    "action": "batch_update",
                    "entity_ids": ["u1", "u2"],
                }
            ],
            "default_chunk_size": 50,
            "default_concurrency": 5,
            "dlq": {"enabled": True},
            "use_events": True,
            "use_audit": False,
        }
        ir = parse_to_ir(data)
        assert len(ir.jobs) == 1
        assert ir.jobs[0].job_id == "j1"
        assert ir.default_chunk_size == 50
        assert ir.default_concurrency == 5
        assert ir.dlq_enabled is True
        assert ir.use_events is True
        assert ir.use_audit is False

    def test_parse_with_alias_keys(self):
        """Parse với alias keys."""
        data = {
            "jobs": [
                {"id": "j1", "type": "product", "action": "batch_create"}
            ],
            "chunk_size": 200,
            "dead_letter_queue": False,
        }
        ir = parse_to_ir(data)
        assert len(ir.jobs) == 1
        assert ir.default_chunk_size == 200
        assert ir.dlq_enabled is False
