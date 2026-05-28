"""
Integration tests CP15 — Observability Stack Generator.

Ki?m tra:
- End-to-end: parser ? models ? engine ? emitter
- Metric Retention Obligation (append-only, immutable)
- Log Immutability Obligation (SHA-256 hash)
- Trace Propagation (W3C format)
- Pack/Taxonomy sync
- __init__.py exports

Luu ý: Ðã lo?i b? TestQueryEffectsIntegration và TestCommandEffectsIntegration
(based trên inspect.getsource() + MagicMock — fragile, d? break khi refactor).
"""

import os
import sys

import pytest

# File lives at: .../midicoder/packs/cp_core_observability/tests/
# 6 levels up = midicoder-ce (repo root)
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
MIDICODER_ROOT = os.path.join(REPO_ROOT, "midicoder")
if MIDICODER_ROOT not in sys.path:
    sys.path.insert(0, MIDICODER_ROOT)


class TestEndToEndPipeline:
    """Ki?m tra pipeline end-to-end: DSL ? Parser ? Models ? Engine ? Emitter."""

    def test_parse_to_metric_registry(self):
        """DSL parse ? MetricProfile ? record metric thành công."""
        from midicoder.packs.cp_core_observability.parser import ObservabilityParser
        from midicoder.packs.cp_core_observability.metrics import MetricRegistry

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
        """DSL parse ? StructuredLogConfig ? log thành công."""
        from midicoder.packs.cp_core_observability.parser import ObservabilityParser
        from midicoder.packs.cp_core_observability.logging import StructuredLogger

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
        """DSL parse ? TraceConfig ? trace thành công."""
        from midicoder.packs.cp_core_observability.parser import ObservabilityParser
        from midicoder.packs.cp_core_observability.tracing import TraceContext

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
        """Full DSL ? Parse ? Emit code thành công."""
        from midicoder.packs.cp_core_observability.parser import ObservabilityParser
        from midicoder.packs.cp_core_observability.fastapi import FastAPIObservabilityEmitter

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
        """T?t c? 4 emitters ph?i generate thành công."""
        from midicoder.packs.cp_core_observability.fastapi import FastAPIObservabilityEmitter
        from midicoder.packs.cp_core_observability.nestjs import NestJSObservabilityEmitter
        from midicoder.packs.cp_core_observability.angular import AngularObservabilityEmitter
        from midicoder.packs.cp_core_observability.react import ReactObservabilityEmitter

        for cls in [FastAPIObservabilityEmitter, NestJSObservabilityEmitter,
                     AngularObservabilityEmitter, ReactObservabilityEmitter]:
            emitter = cls()
            result = emitter.generate()
            assert len(result) > 0, f"{cls.__name__} ph?i generate ít nh?t 1 file"


class TestMetricRetentionObligation:
    """Ki?m tra Obligation 1: Metric Retention (append-only, immutable)."""

    def test_metric_entries_are_immutable(self):
        """MetricEntry không th? s?a d?i sau khi t?o."""
        from midicoder.packs.cp_core_observability.metrics import MetricRegistry
        registry = MetricRegistry()
        entry = registry.record("test_metric", 1.0)
        # MetricEntry là frozen dataclass, không th? s?a
        with pytest.raises(Exception):
            entry.value = 2.0

    def test_counter_append_only(self):
        """Counter ch? append, không s?a entry cu."""
        from midicoder.packs.cp_core_observability.metrics import MetricRegistry
        registry = MetricRegistry()
        registry.counter("req_count", {"method": "GET"})
        registry.counter("req_count", {"method": "GET"})
        entries = registry.get("req_count")
        assert len(entries) == 2, "Counter ph?i t?o 2 entry riêng"


class TestLogImmutabilityObligation:
    """Ki?m tra Obligation 2: Log Immutability (SHA-256 hash)."""

    def test_log_entry_hash_verified(self):
        """LogEntry hash verify ph?i tr? v? True."""
        from midicoder.packs.cp_core_observability.logging import StructuredLogger
        logger = StructuredLogger(service_name="test")
        entry = logger.info("test message")
        assert entry.verify_hash() is True

    def test_log_entry_hash_detected_tampering(self):
        """LogEntry phát hi?n tampering."""
        from midicoder.packs.cp_core_observability.logging import StructuredLogger, LogEntry
        from datetime import datetime
        logger = StructuredLogger(service_name="test")
        entry = logger.info("test message")
        original_hash = entry.immutable_hash
        # LogEntry là frozen, nên ta t?o m?i v?i hash sai
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
        from midicoder.packs.cp_core_observability.logging import StructuredLogger
        logger = StructuredLogger(service_name="test")
        entry = logger.info("test")
        with pytest.raises(Exception):
            entry.message = "tampered"


class TestTracePropagation:
    """Ki?m tra trace propagation (W3C format)."""

    def test_inject_extract_roundtrip(self):
        """Inject ? Extract ph?i tr? v? dúng trace_id, span_id."""
        from midicoder.packs.cp_core_observability.tracing import TraceContext
        ctx = TraceContext(service_name="test")
        span = ctx.start_span("op1")
        headers = ctx.inject_trace_header()
        assert "traceparent" in headers
        extracted_id, extracted_span = ctx.extract_trace_header(headers)
        assert extracted_id == ctx.trace_id
        assert extracted_span == span.span_id

    def test_traceparent_w3c_format(self):
        """Traceparent ph?i dúng format W3C: 00-{trace_id}-{span_id}-{flags}."""
        from midicoder.packs.cp_core_observability.tracing import TraceContext
        ctx = TraceContext(service_name="test")
        ctx.start_span("op1")
        headers = ctx.inject_trace_header()
        tp = headers["traceparent"]
        parts = tp.split("-")
        assert len(parts) == 4, "traceparent ph?i có 4 ph?n"
        assert parts[0] == "00", "version ph?i là 00"
        assert len(parts[1]) == 32, "trace_id ph?i 32 ký t? hex"
        assert len(parts[2]) == 16, "span_id ph?i 16 ký t? hex"


class TestPackTaxonomySync:
    """Ki?m tra pack.yml d?ng b? v?i taxonomy.yml."""

    def test_pack_yml_exists(self):
        """pack.yml phai ton tai."""
        pack_path = os.path.join(MIDICODER_ROOT, "emitters", "core", "cp_core_observability", "pack.yml")
        assert os.path.isfile(pack_path), "pack.yml missing"

    def test_pack_capabilities(self):
        """pack.yml capabilities_provided phai dung."""
        import yaml
        pack_path = os.path.join(MIDICODER_ROOT, "emitters", "core", "cp_core_observability", "pack.yml")
        with open(pack_path, "r") as f:
            pack = yaml.safe_load(f)
        caps = pack.get("pack", {}).get("capabilities_provided", [])
        assert "emit_metric" in caps
        assert "structured_logging" in caps
        assert "distributed_tracing" in caps

    def test_taxonomy_status_stable(self):
        """taxonomy.yml CP15 status ph?i là 'stable'."""
        import yaml
        taxonomy_path = os.path.join(REPO_ROOT, "industry", "taxonomy.yml")
        with open(taxonomy_path, "r") as f:
            taxonomy = yaml.safe_load(f)
        cp15 = None
        for pack in taxonomy.get("core_packs", []):
            if pack.get("id") == "CP15":
                cp15 = pack
                break
        assert cp15 is not None, "CP15 không tìm th?y trong taxonomy"
        assert cp15.get("status") == "stable", f"CP15 status ph?i là stable, got {cp15.get('status')}"


class TestInitExports:
    """Ki?m tra __init__.py export d?y d?."""

    def test_all_models_exported(self):
        """T?t c? models ph?i du?c export."""
        from midicoder.packs.cp_core_observability import (
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
        """T?t c? emitters ph?i du?c export."""
        from midicoder.packs.cp_core_observability import (
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
        """T?t c? engine ph?i du?c export."""
        from midicoder.packs.cp_core_observability import (
            MetricRegistry, StructuredLogger, TraceContext,
        )
        assert MetricRegistry is not None
        assert StructuredLogger is not None
        assert TraceContext is not None

    def test_all_list_complete(self):
        """__all__ ph?i ch?a t?t c? exports."""
        from midicoder.packs.cp_core_observability import __all__
        expected = {
            "MetricType", "LogLevel", "TracePropagationFormat",
            "MetricProfile", "StructuredLogConfig", "TraceConfig",
            "ObservabilityParser",
            "MetricRegistry", "StructuredLogger", "TraceContext",
            "FastAPIObservabilityEmitter", "NestJSObservabilityEmitter",
            "AngularObservabilityEmitter", "ReactObservabilityEmitter",
        }
        actual = set(__all__)
        assert expected.issubset(actual), f"Thi?u exports: {expected - actual}"
