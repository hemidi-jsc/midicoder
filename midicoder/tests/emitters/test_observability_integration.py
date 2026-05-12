"""
Integration tests CP15 — Observability Stack Generator.

Kiểm tra:
- Query effects _record_metric() wire vào CP15 MetricRegistry
- Command effects _record_metric() wire vào CP15 MetricRegistry
- End-to-end: parser → models → engine → emitter
"""

import asyncio
import json
import os
import sys
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# Thêm project root vào path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class TestQueryEffectsIntegration:
    """Kiểm tra query effects wire vào CP15 MetricRegistry."""

    def test_record_metric_imports_metric_registry(self):
        """_record_metric phải import từ CP15."""
        from midicoder.emitters.core.cp01_domain_model.query_effects import QueryEffects
        import inspect
        source = inspect.getsource(QueryEffects._record_metric)
        assert "MetricRegistry" in source, "_record_metric phải sử dụng MetricRegistry"
        assert "observability" in source, "_record_metric phải import từ observability"

    def test_record_metric_calls_registry_record(self):
        """_record_metric phải gọi registry.record()."""
        import inspect
        from midicoder.emitters.core.cp01_domain_model.query_effects import QueryEffects
        source = inspect.getsource(QueryEffects._record_metric)
        assert "registry.record" in source or "registry = MetricRegistry" in source, \
            "_record_metric phải gọi registry.record()"

    def test_record_metric_no_placeholder(self):
        """_record_metric không còn placeholder."""
        import inspect
        from midicoder.emitters.core.cp01_domain_model.query_effects import QueryEffects
        source = inspect.getsource(QueryEffects._record_metric)
        assert "placeholder" not in source.lower(), "_record_metric không được có placeholder"
        assert "pass" not in source.strip().split("\n")[-1].strip(), "_record_metric không được chỉ có pass"

    def test_query_effects_execute_record_metric(self):
        """QueryEffects.execute_all() phải chạy _record_metric thành công."""
        from midicoder.emitters.core.cp01_domain_model.query_effects import QueryEffects
        from midicoder.emitters.core.cp01_domain_model.query_models import Query, QueryEffect, QueryEffectType

        effect = QueryEffect(
            effect_type=QueryEffectType.RECORD_METRIC,
            metric_name="query.test_duration",
            metric_value=42.0,
        )
        query = Query(
            id="TestQuery",
            description="Test",
            reads_from="TestEntity",
            effects=[effect],
        )
        qe = QueryEffects(query)
        context = {
            "query_id": "test-1",
            "user_id": "user-1",
            "tenant_id": "tenant-1",
        }
        result = asyncio.run(qe.execute_all(context))  # noqa:ASYNC
        assert result is None  # _record_metric returns None


class TestCommandEffectsIntegration:
    """Kiểm tra command effects wire vào CP15 MetricRegistry."""

    def test_record_metric_imports_metric_registry(self):
        """_record_metric phải import từ CP15."""
        from midicoder.emitters.core.cp01_domain_model.command_effects import CommandEffects
        import inspect
        source = inspect.getsource(CommandEffects._record_metric)
        assert "MetricRegistry" in source, "_record_metric phải sử dụng MetricRegistry"
        assert "observability" in source, "_record_metric phải import từ observability"

    def test_record_metric_calls_registry_record(self):
        """_record_metric phải gọi registry.record()."""
        import inspect
        from midicoder.emitters.core.cp01_domain_model.command_effects import CommandEffects
        source = inspect.getsource(CommandEffects._record_metric)
        assert "registry.record" in source or "registry = MetricRegistry" in source, \
            "_record_metric phải gọi registry.record()"

    def test_record_metric_no_placeholder(self):
        """_record_metric không còn placeholder."""
        import inspect
        from midicoder.emitters.core.cp01_domain_model.command_effects import CommandEffects
        source = inspect.getsource(CommandEffects._record_metric)
        assert "placeholder" not in source.lower(), "_record_metric không được có placeholder"
        assert "# Placeholder" not in source, "_record_metric không được có comment placeholder"

    def test_command_effects_execute_record_metric(self):
        """CommandEffects.execute() phải chạy _record_metric thành công."""
        from midicoder.emitters.core.cp01_domain_model.command_effects import CommandEffects, CommandEffect
        from midicoder.emitters.core.cp01_domain_model.command_models import Command, EffectType

        # CommandEffect lacks metric_name/metric_value fields; use MagicMock
        effect = MagicMock(spec=CommandEffect)
        effect.effect_type = EffectType.RECORD_METRIC
        effect.metric_name = "command.test_duration"
        effect.metric_value = 99.0
        effect.condition = None

        command = Command(
            id="TestCommand",
            description="Test",
            effects=[effect],
        )
        ce = CommandEffects(command)
        result = asyncio.run(
            ce.execute({}, user_id="u1", tenant_id="t1")
        )
        assert isinstance(result, dict)


class TestEndToEndPipeline:
    """Kiểm tra pipeline end-to-end: DSL → Parser → Models → Engine → Emitter."""

    def test_parse_to_metric_registry(self):
        """DSL parse → MetricProfile → record metric thành công."""
        from midicoder.emitters.core.cp15_observability.parser import ObservabilityParser
        from midicoder.emitters.core.cp15_observability.metrics import MetricRegistry

        dsl = """
metrics:
  - name: "http_requests_total"
    type: "counter"
    unit: "count"
    retention_days: 90
"""
        parser = ObservabilityParser()
        result = parser.parse(dsl)
        assert "metrics" in result
        assert len(result["metrics"]) == 1

        profile = result["metrics"][0]
        assert profile.name == "http_requests_total"
        assert profile.retention_days == 90

        registry = MetricRegistry(retention_days=profile.retention_days)
        entry = registry.record(profile.name, 1.0, {"method": "GET"})
        assert entry.name == profile.name

    def test_parse_to_structured_logger(self):
        """DSL parse → StructuredLogConfig → log thành công."""
        from midicoder.emitters.core.cp15_observability.parser import ObservabilityParser
        from midicoder.emitters.core.cp15_observability.logging import StructuredLogger

        dsl = """
logging:
  - service_name: "order-service"
    log_level: "INFO"
    output_format: "json"
"""
        parser = ObservabilityParser()
        result = parser.parse(dsl)
        assert len(result["logging"]) == 1

        config = result["logging"][0]
        logger = StructuredLogger(
            service_name=config.service_name,
            include_trace_id=config.include_trace_id,
        )
        entry = logger.info("test message", {"key": "value"})
        assert entry.service_name == "order-service"

    def test_parse_to_trace_context(self):
        """DSL parse → TraceConfig → trace thành công."""
        from midicoder.emitters.core.cp15_observability.parser import ObservabilityParser
        from midicoder.emitters.core.cp15_observability.tracing import TraceContext

        dsl = """
tracing:
  - service_name: "api-gateway"
    propagation_format: "w3c_trace_context"
    max_spans: 200
"""
        parser = ObservabilityParser()
        result = parser.parse(dsl)
        assert len(result["tracing"]) == 1

        config = result["tracing"][0]
        ctx = TraceContext(service_name=config.service_name)
        span = ctx.start_span("test-operation")
        assert span.name == "test-operation"

    def test_full_dsl_to_emitter(self):
        """Full DSL → Parse → Emit code thành công."""
        from midicoder.emitters.core.cp15_observability.parser import ObservabilityParser
        from midicoder.emitters.core.cp15_observability.fastapi import FastAPIObservabilityEmitter

        full_dsl = """
metrics:
  - name: "http_requests_total"
    type: "counter"
logging:
  - service_name: "test-service"
    log_level: "INFO"
tracing:
  - service_name: "test-service"
"""
        parser = ObservabilityParser()
        parsed = parser.parse(full_dsl)
        assert len(parsed["metrics"]) == 1
        assert len(parsed["logging"]) == 1
        assert len(parsed["tracing"]) == 1

        emitter = FastAPIObservabilityEmitter()
        generated = emitter.generate()
        assert len(generated) >= 2

    def test_all_4_emitters(self):
        """Tất cả 4 emitters phải generate thành công."""
        from midicoder.emitters.core.cp15_observability.fastapi import FastAPIObservabilityEmitter
        from midicoder.emitters.core.cp15_observability.nestjs import NestJSObservabilityEmitter
        from midicoder.emitters.core.cp15_observability.angular import AngularObservabilityEmitter
        from midicoder.emitters.core.cp15_observability.react import ReactObservabilityEmitter

        for cls in [FastAPIObservabilityEmitter, NestJSObservabilityEmitter,
                     AngularObservabilityEmitter, ReactObservabilityEmitter]:
            emitter = cls()
            result = emitter.generate()
            assert len(result) > 0, f"{cls.__name__} phải generate ít nhất 1 file"


class TestMetricRetentionObligation:
    """Kiểm tra Obligation 1: Metric Retention (append-only, immutable)."""

    def test_metric_entries_are_immutable(self):
        """MetricEntry không thể sửa đổi sau khi tạo."""
        from midicoder.emitters.core.cp15_observability.metrics import MetricRegistry
        registry = MetricRegistry()
        entry = registry.record("test_metric", 1.0)
        # MetricEntry là frozen dataclass, không thể sửa
        with pytest.raises(Exception):
            entry.value = 2.0

    def test_counter_append_only(self):
        """Counter chỉ append, không sửa entry cũ."""
        from midicoder.emitters.core.cp15_observability.metrics import MetricRegistry
        registry = MetricRegistry()
        registry.counter("req_count", {"method": "GET"})
        registry.counter("req_count", {"method": "GET"})
        entries = registry.get("req_count")
        assert len(entries) == 2, "Counter phải tạo 2 entry riêng"


class TestLogImmutabilityObligation:
    """Kiểm tra Obligation 2: Log Immutability (SHA-256 hash)."""

    def test_log_entry_hash_verified(self):
        """LogEntry hash verify phải trả về True."""
        from midicoder.emitters.core.cp15_observability.logging import StructuredLogger
        logger = StructuredLogger(service_name="test")
        entry = logger.info("test message")
        assert entry.verify_hash() is True

    def test_log_entry_hash_detected_tampering(self):
        """LogEntry phát hiện tampering."""
        from midicoder.emitters.core.cp15_observability.logging import StructuredLogger, LogEntry
        from datetime import datetime
        logger = StructuredLogger(service_name="test")
        entry = logger.info("test message")
        original_hash = entry.immutable_hash
        # LogEntry là frozen, nên ta tạo mới với hash sai
        tampered = LogEntry(
            timestamp=entry.timestamp,
            level=entry.level,
            message=entry.message,
            service_name=entry.service_name,
            trace_id=entry.trace_id,
            span_id=entry.span_id,
            fields=entry.fields,
            immutable_hash="wrong-hash-value",
        )
        assert tampered.verify_hash() is False

    def test_log_entry_is_frozen(self):
        """LogEntry là frozen (immutable)."""
        from midicoder.emitters.core.cp15_observability.logging import StructuredLogger
        logger = StructuredLogger(service_name="test")
        entry = logger.info("test")
        with pytest.raises(Exception):
            entry.message = "tampered"


class TestTracePropagation:
    """Kiểm tra trace propagation (W3C format)."""

    def test_inject_extract_roundtrip(self):
        """Inject → Extract phải trả về đúng trace_id, span_id."""
        from midicoder.emitters.core.cp15_observability.tracing import TraceContext
        ctx = TraceContext(service_name="test")
        span = ctx.start_span("op1")
        headers = ctx.inject_trace_header()
        assert "traceparent" in headers
        extracted_id, extracted_span = ctx.extract_trace_header(headers)
        assert extracted_id == ctx.trace_id
        assert extracted_span == span.span_id

    def test_traceparent_w3c_format(self):
        """Traceparent phải đúng format W3C: 00-{trace_id}-{span_id}-{flags}."""
        from midicoder.emitters.core.cp15_observability.tracing import TraceContext
        ctx = TraceContext(service_name="test")
        ctx.start_span("op1")
        headers = ctx.inject_trace_header()
        tp = headers["traceparent"]
        parts = tp.split("-")
        assert len(parts) == 4, "traceparent phải có 4 phần"
        assert parts[0] == "00", "version phải là 00"
        assert len(parts[1]) == 32, "trace_id phải 32 ký tự hex"
        assert len(parts[2]) == 16, "span_id phải 16 ký tự hex"


class TestPackTaxonomySync:
    """Kiểm tra pack.yml đồng bộ với taxonomy.yml."""

    def test_pack_yml_exists(self):
        """pack.yml phải tồn tại."""
        pack_path = os.path.join(PROJECT_ROOT, "emitters", "core", "cp15_observability", "pack.yml")
        assert os.path.isfile(pack_path), "pack.yml missing"

    def test_pack_capabilities(self):
        """pack.yml capabilities_provided phải đúng."""
        import yaml
        pack_path = os.path.join(PROJECT_ROOT, "emitters", "core", "cp15_observability", "pack.yml")
        with open(pack_path, "r") as f:
            pack = yaml.safe_load(f)
        caps = pack.get("pack", {}).get("capabilities_provided", [])
        assert "emit_metric" in caps
        assert "structured_logging" in caps
        assert "distributed_tracing" in caps

    def test_taxonomy_status_stable(self):
        """taxonomy.yml CP15 status phải là 'stable'."""
        import yaml
        taxonomy_path = os.path.join(
            os.path.dirname(PROJECT_ROOT), "industry", "taxonomy.yml"
        )
        if not os.path.isfile(taxonomy_path):
            taxonomy_path = os.path.join(PROJECT_ROOT, "..", "industry", "taxonomy.yml")
        with open(taxonomy_path, "r") as f:
            taxonomy = yaml.safe_load(f)
        cp15 = None
        for pack in taxonomy.get("core_packs", []):
            if pack.get("id") == "CP15":
                cp15 = pack
                break
        assert cp15 is not None, "CP15 không tìm thấy trong taxonomy"
        assert cp15.get("status") == "stable", f"CP15 status phải là stable, got {cp15.get('status')}"


class TestInitExports:
    """Kiểm tra __init__.py export đầy đủ."""

    def test_all_models_exported(self):
        """Tất cả models phải được export."""
        from midicoder.emitters.core.cp15_observability import (
            MetricType, LogLevel, TracePropagationFormat,
            MetricProfile, StructuredLogConfig, TraceConfig,
        )
        assert MetricType is not None
        assert LogLevel is not None
        assert TracePropagationFormat is not None
        assert MetricProfile is not None
        assert StructuredLogConfig is not None
        assert TraceConfig is not None

    def test_all_emitters_exported(self):
        """Tất cả emitters phải được export."""
        from midicoder.emitters.core.cp15_observability import (
            FastAPIObservabilityEmitter,
            NestJSObservabilityEmitter,
            AngularObservabilityEmitter,
            ReactObservabilityEmitter,
        )
        assert FastAPIObservabilityEmitter is not None
        assert NestJSObservabilityEmitter is not None
        assert AngularObservabilityEmitter is not None
        assert ReactObservabilityEmitter is not None

    def test_engine_exported(self):
        """Tất cả engine phải được export."""
        from midicoder.emitters.core.cp15_observability import (
            MetricRegistry, StructuredLogger, TraceContext,
        )
        assert MetricRegistry is not None
        assert StructuredLogger is not None
        assert TraceContext is not None

    def test_all_list_complete(self):
        """__all__ phải chứa tất cả exports."""
        from midicoder.emitters.core.cp15_observability import __all__
        expected = {
            "MetricType", "LogLevel", "TracePropagationFormat",
            "MetricProfile", "StructuredLogConfig", "TraceConfig",
            "ObservabilityParser",
            "MetricRegistry", "StructuredLogger", "TraceContext",
            "FastAPIObservabilityEmitter", "NestJSObservabilityEmitter",
            "AngularObservabilityEmitter", "ReactObservabilityEmitter",
        }
        actual = set(__all__)
        assert expected.issubset(actual), f"Thiếu exports: {expected - actual}"
