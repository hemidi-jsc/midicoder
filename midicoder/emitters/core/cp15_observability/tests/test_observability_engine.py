# coding: utf-8
"""
Test comprehensive cho CP15 Observability Stack Generator runtime engine.

Kiểm tra toàn bộ 3 runtime modules:
- MetricRegistry: Metrics registry (counter, gauge, histogram, retention, export)
- StructuredLogger: Structured JSON logging với tamper-evidence hash
- TraceContext: Distributed tracing với W3C propagation

Author: Midicoder Team
Version: 1.0.0
"""

import json
import time
import unittest
from datetime import datetime, timezone, timedelta

from midicoder.emitters.core.cp15_observability.metrics import (
    MetricEntry,
    MetricRegistry,
)
from midicoder.emitters.core.cp15_observability.logging import (
    LogEntry,
    StructuredLogger,
)
from midicoder.emitters.core.cp15_observability.tracing import (
    Span,
    TraceContext,
)
from midicoder.emitters.core.cp15_observability.models import (
    MetricType,
    LogLevel,
    TracePropagationFormat,
)


# ===========================================================================
# MetricRegistry tests
# ===========================================================================


class TestMetricRegistry(unittest.TestCase):
    """Kiểm tra MetricRegistry — counter, gauge, histogram, export, retention."""

    def test_init_default_retention(self):
        """Tạo MetricRegistry với retention mặc định 30 ngày."""
        registry = MetricRegistry()
        self.assertEqual(registry._retention_days, 30)
        self.assertEqual(len(registry._entries), 0)

    def test_init_custom_retention(self):
        """Tạo MetricRegistry với retention tùy chỉnh."""
        registry = MetricRegistry(retention_days=7)
        self.assertEqual(registry._retention_days, 7)

    def test_init_invalid_retention(self):
        """Tạo MetricRegistry với retention < 1 sẽ raise MidicoderError."""
        from midicoder.errors import MidicoderError
        with self.assertRaises(MidicoderError):
            MetricRegistry(retention_days=0)
        with self.assertRaises(MidicoderError):
            MetricRegistry(retention_days=-1)

    def test_counter_increment(self):
        """Counter tăng 1 đơn vị mỗi lần gọi."""
        registry = MetricRegistry()
        val = registry.counter("http_requests_total")
        self.assertEqual(val, 1.0)

    def test_counter_accumulate(self):
        """Counter cộng dồn các lần gọi với cùng name+labels."""
        registry = MetricRegistry()
        registry.counter("requests", {"method": "GET"})
        registry.counter("requests", {"method": "GET"})
        registry.counter("requests", {"method": "GET"})
        val = registry.counter("requests", {"method": "GET"})
        self.assertEqual(val, 4.0)

    def test_counter_different_labels(self):
        """Counter với labels khác nhau thì đếm riêng."""
        registry = MetricRegistry()
        registry.counter("requests", {"method": "GET"})
        registry.counter("requests", {"method": "GET"})
        get_val = registry.counter("requests", {"method": "GET"})
        post_val = registry.counter("requests", {"method": "POST"})
        self.assertEqual(get_val, 3.0)
        self.assertEqual(post_val, 1.0)

    def test_counter_no_labels(self):
        """Counter hoạt động không có labels."""
        registry = MetricRegistry()
        registry.counter("simple_counter")
        registry.counter("simple_counter")
        val = registry.counter("simple_counter")
        self.assertEqual(val, 3.0)

    def test_gauge_set_value(self):
        """Gauge set giá trị và trả về đúng value."""
        registry = MetricRegistry()
        val = registry.gauge("cpu_usage", 42.5)
        self.assertEqual(val, 42.5)

    def test_gauge_overwrite(self):
        """Gauge ghi đè giá trị cũ bằng entry mới."""
        registry = MetricRegistry()
        registry.gauge("cpu_usage", 10.0)
        registry.gauge("cpu_usage", 25.0)
        registry.gauge("cpu_usage", 50.0)
        # Entry cũ vẫn còn — append-only
        entries = registry.get("cpu_usage")
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[-1].value, 50.0)

    def test_histogram_observe(self):
        """Histogram ghi observation và trả về None."""
        registry = MetricRegistry()
        result = registry.histogram("request_duration", 0.125)
        self.assertIsNone(result)
        entries = registry.get("request_duration")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].value, 0.125)

    def test_histogram_multiple_observations(self):
        """Histogram lưu nhiều observations."""
        registry = MetricRegistry()
        registry.histogram("latency", 10.0)
        registry.histogram("latency", 20.0)
        registry.histogram("latency", 30.0)
        entries = registry.get("latency")
        self.assertEqual(len(entries), 3)

    def test_record_returns_entry(self):
        """Record trả về MetricEntry và append vào list."""
        registry = MetricRegistry()
        entry = registry.record("custom_metric", 100.0, {"env": "prod"})
        self.assertIsInstance(entry, MetricEntry)
        self.assertEqual(entry.name, "custom_metric")
        self.assertEqual(entry.value, 100.0)
        self.assertEqual(entry.labels["env"], "prod")

    def test_record_without_labels(self):
        """Record không truyền labels → default dict rỗng."""
        registry = MetricRegistry()
        entry = registry.record("no_label_metric", 42.0)
        self.assertEqual(entry.labels, {})

    def test_counter_without_labels(self):
        """Counter không truyền labels → default dict rỗng."""
        registry = MetricRegistry()
        val = registry.counter("simple")
        self.assertEqual(val, 1.0)

    def test_histogram_without_labels(self):
        """Histogram không truyền labels → default dict rỗng."""
        registry = MetricRegistry()
        registry.histogram("no_label_hist", 5.0)
        entries = registry.get("no_label_hist")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].labels, {})

    def test_gauge_without_labels(self):
        """Gauge không truyền labels → default dict rỗng."""
        registry = MetricRegistry()
        val = registry.gauge("no_label_gauge", 7.5)
        self.assertEqual(val, 7.5)

    def test_get_by_name(self):
        """Get trả về entries khớp theo name."""
        registry = MetricRegistry()
        registry.counter("a", {"x": "1"})
        registry.counter("b", {"x": "2"})
        a_entries = registry.get("a")
        self.assertEqual(len(a_entries), 1)
        self.assertEqual(a_entries[0].name, "a")

    def test_get_with_label_filter(self):
        """Get với label filter chỉ trả về entries khớp labels."""
        registry = MetricRegistry()
        registry.counter("req", {"method": "GET"})
        registry.counter("req", {"method": "POST"})
        get_entries = registry.get("req", {"method": "GET"})
        self.assertEqual(len(get_entries), 1)
        self.assertEqual(get_entries[0].labels["method"], "GET")

    def test_export_prometheus_counter(self):
        """Export Prometheus — counter được tổng hợp đúng."""
        registry = MetricRegistry()
        registry.counter("http_requests", {"method": "GET"})
        registry.counter("http_requests", {"method": "GET"})
        registry.counter("http_requests", {"method": "POST"})
        output = registry.export_prometheus()
        # Counter GET total = 2, POST total = 1
        self.assertIn('http_requests{method="GET"} 2.0', output)
        self.assertIn('http_requests{method="POST"} 1.0', output)

    def test_export_prometheus_gauge(self):
        """Export Prometheus — gauge lấy giá trị mới nhất."""
        registry = MetricRegistry()
        registry.gauge("temperature", 20.0)
        registry.gauge("temperature", 25.0)
        output = registry.export_prometheus()
        self.assertIn("temperature 25.0", output)

    def test_export_prometheus_empty(self):
        """Export Prometheus khi không có entries trả về rỗng."""
        registry = MetricRegistry()
        output = registry.export_prometheus()
        self.assertEqual(output, "")

    def test_export_prometheus_histogram(self):
        """Export Prometheus — histogram xuất mỗi observation riêng."""
        registry = MetricRegistry()
        registry.histogram("latency", 10.0)
        registry.histogram("latency", 20.0)
        output = registry.export_prometheus()
        self.assertIn("latency 10.0", output)
        self.assertIn("latency 20.0", output)

    def test_export_prometheus_all_types_mixed(self):
        """Export Prometheus — mixed counter + gauge + histogram cùng lúc."""
        registry = MetricRegistry()
        registry.counter("requests", {"method": "GET"})
        registry.gauge("cpu", 55.0)
        registry.gauge("mem", 70.0)   # gauge followed by histogram → covers gauge→loop
        registry.histogram("latency", 15.0)
        registry.histogram("latency2", 25.0)  # histogram followed by counter → covers histogram→loop
        registry.counter("errors")
        output = registry.export_prometheus()
        self.assertIn("requests", output)
        self.assertIn("cpu", output)
        self.assertIn("latency", output)
        self.assertIn("errors", output)

    def test_retention_check_removes_old(self):
        """Retention check xóa entries cũ hơn retention_days."""
        registry = MetricRegistry(retention_days=1)
        # Thêm entry hiện tại
        registry.counter("active")
        # Thêm entry cũ (giả lập)
        old_time = datetime.now(timezone.utc) - timedelta(days=3)
        old_entry = MetricEntry(
            name="old_metric",
            value=1.0,
            metric_type=MetricType.COUNTER.value,
            labels={},
            timestamp=old_time,
        )
        registry._entries.append(old_entry)
        # Tổng cộng 2 entries, 1 cái cũ
        deleted = registry.retention_check()
        self.assertEqual(deleted, 1)
        self.assertEqual(len(registry._entries), 1)

    def test_retention_check_custom_days(self):
        """Retention check với custom days override."""
        registry = MetricRegistry(retention_days=30)
        # Entry 15 ngày tuổi
        mid_time = datetime.now(timezone.utc) - timedelta(days=15)
        registry._entries.append(MetricEntry(
            name="mid_age",
            value=1.0,
            metric_type=MetricType.COUNTER.value,
            labels={},
            timestamp=mid_time,
        ))
        # Xóa entries cũ hơn 10 ngày
        deleted = registry.retention_check(older_than_days=10)
        self.assertEqual(deleted, 1)

    def test_append_only_immutability(self):
        """Metric entries là append-only — không thể sửa entry cũ."""
        registry = MetricRegistry()
        registry.counter("req")
        entry = registry._entries[0]
        original_value = entry.value
        # Vì MetricEntry là frozen dataclass, không thể sửa
        with self.assertRaises(Exception):
            entry.value = 999.0


# ===========================================================================
# StructuredLogger tests
# ===========================================================================


class TestStructuredLogger(unittest.TestCase):
    """Kiểm tra StructuredLogger — log entry, hash, export, shorthand."""

    def test_init_defaults(self):
        """Tạo StructuredLogger với giá trị mặc định."""
        logger = StructuredLogger()
        self.assertEqual(logger._service_name, "midicoder")
        self.assertTrue(logger._include_trace_id)
        self.assertTrue(logger._include_span_id)

    def test_init_custom_service(self):
        """Tạo StructuredLogger với service_name tùy chỉnh."""
        logger = StructuredLogger(service_name="my-service")
        self.assertEqual(logger._service_name, "my-service")

    def test_log_debug(self):
        """Ghi log DEBUG và trả về LogEntry."""
        logger = StructuredLogger()
        entry = logger.log("DEBUG", "debug message")
        self.assertIsInstance(entry, LogEntry)
        self.assertEqual(entry.level, "DEBUG")
        self.assertEqual(entry.message, "debug message")

    def test_log_info(self):
        """Ghi log INFO."""
        logger = StructuredLogger()
        entry = logger.log("INFO", "info message")
        self.assertEqual(entry.level, "INFO")

    def test_log_warning(self):
        """Ghi log WARNING."""
        logger = StructuredLogger()
        entry = logger.log("WARNING", "warn message")
        self.assertEqual(entry.level, "WARNING")

    def test_log_error(self):
        """Ghi log ERROR."""
        logger = StructuredLogger()
        entry = logger.log("ERROR", "error message")
        self.assertEqual(entry.level, "ERROR")

    def test_log_critical(self):
        """Ghi log CRITICAL."""
        logger = StructuredLogger()
        entry = logger.log("CRITICAL", "critical message")
        self.assertEqual(entry.level, "CRITICAL")

    def test_shorthand_methods(self):
        """Kiểm tra các shorthand method: debug, info, warning, error, critical."""
        logger = StructuredLogger()
        d = logger.debug("debug msg")
        i = logger.info("info msg")
        w = logger.warning("warn msg")
        e = logger.error("error msg")
        c = logger.critical("critical msg")
        self.assertEqual(d.level, "DEBUG")
        self.assertEqual(i.level, "INFO")
        self.assertEqual(w.level, "WARNING")
        self.assertEqual(e.level, "ERROR")
        self.assertEqual(c.level, "CRITICAL")

    def test_hash_verification_valid(self):
        """LogEntry hash verification — pass cho entry hợp lệ."""
        logger = StructuredLogger()
        entry = logger.info("test hash")
        self.assertTrue(entry.verify_hash())

    def test_hash_verification_tampered(self):
        """LogEntry hash verification — fail khi entry bị thay đổi.

        Vì LogEntry là frozen dataclass, kiểm tra bằng cách tạo entry
        với hash sai so với dữ liệu.
        """
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc),
            level="INFO",
            message="tampered",
            service_name="test",
            trace_id="",
            span_id="",
            fields={},
            immutable_hash="invalid_hash_value",
        )
        self.assertFalse(entry.verify_hash())

    def test_logger_excludes_trace_and_span_id(self):
        """Logger với include_trace_id=False, include_span_id=False."""
        logger = StructuredLogger(
            service_name="test",
            include_trace_id=False,
            include_span_id=False,
        )
        entry = logger.info("test", {"trace_id": "should-be-empty", "span_id": "also-empty"})
        self.assertEqual(entry.trace_id, "")
        self.assertEqual(entry.span_id, "")

    def test_logger_includes_trace_and_span_from_fields(self):
        """Logger lấy trace_id và span_id từ fields."""
        logger = StructuredLogger(service_name="test")
        entry = logger.info("test", {"trace_id": "t-123", "span_id": "s-456"})
        self.assertEqual(entry.trace_id, "t-123")
        self.assertEqual(entry.span_id, "s-456")

    def test_to_dict(self):
        """LogEntry.to_dict trả về dictionary đầy đủ."""
        logger = StructuredLogger()
        entry = logger.info("dict test", {"key": "value"})
        d = entry.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["level"], "INFO")
        self.assertEqual(d["message"], "dict test")
        self.assertEqual(d["fields"]["key"], "value")
        self.assertIn("immutable_hash", d)

    def test_to_json(self):
        """LogEntry.to_json trả về chuỗi JSON."""
        logger = StructuredLogger()
        entry = logger.info("json test")
        json_str = entry.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["level"], "INFO")
        self.assertEqual(parsed["message"], "json test")

    def test_export_json_lines(self):
        """Export JSON lines — mỗi entry là một dòng JSON."""
        logger = StructuredLogger()
        logger.info("line 1")
        logger.error("line 2")
        output = logger.export_json()
        lines = output.strip().split("\n")
        self.assertEqual(len(lines), 2)
        # Mỗi dòng phải parse JSON được
        json.loads(lines[0])
        json.loads(lines[1])

    def test_export_json_empty(self):
        """Export JSON khi không có entries trả về rỗng."""
        logger = StructuredLogger()
        output = logger.export_json()
        self.assertEqual(output, "")

    def test_auto_timestamp(self):
        """Log entry có timestamp tự động tạo."""
        logger = StructuredLogger()
        before = datetime.now(timezone.utc)
        entry = logger.info("timestamp test")
        after = datetime.now(timezone.utc)
        self.assertGreaterEqual(entry.timestamp, before - timedelta(seconds=1))
        self.assertLessEqual(entry.timestamp, after + timedelta(seconds=1))

    def test_fields_inclusion(self):
        """Log entry bao gồm các fields bổ sung."""
        logger = StructuredLogger()
        entry = logger.info("with fields", {"user_id": 42, "action": "login"})
        self.assertEqual(entry.fields["user_id"], 42)
        self.assertEqual(entry.fields["action"], "login")

    def test_entries_returns_all(self):
        """Entries trả về tất cả log entries đã ghi."""
        logger = StructuredLogger()
        logger.debug("d")
        logger.info("i")
        logger.error("e")
        all_entries = logger.entries()
        self.assertEqual(len(all_entries), 3)

    def test_service_name_in_entry(self):
        """Service name được ghi vào log entry."""
        logger = StructuredLogger(service_name="payment-service")
        entry = logger.info("test")
        self.assertEqual(entry.service_name, "payment-service")


# ===========================================================================
# TraceContext tests
# ===========================================================================


class TestTraceContext(unittest.TestCase):
    """Kiểm tra TraceContext — span, hierarchy, W3C propagation, export."""

    def test_init(self):
        """Tạo TraceContext với service_name mặc định."""
        ctx = TraceContext()
        self.assertEqual(ctx._service_name, "midicoder")
        self.assertEqual(len(ctx._spans), 0)
        self.assertEqual(len(ctx._active_spans), 0)

    def test_init_custom_service(self):
        """Tạo TraceContext với service_name tùy chỉnh."""
        ctx = TraceContext(service_name="order-service")
        self.assertEqual(ctx._service_name, "order-service")

    def test_generate_trace_id(self):
        """Trace ID là 32 ký tự hex."""
        ctx = TraceContext()
        self.assertEqual(len(ctx._trace_id), 32)
        int(ctx._trace_id, 16)  # Không raise → hợp lệ hex

    def test_generate_span_id(self):
        """Span ID là 16 ký tự hex."""
        ctx = TraceContext()
        sid = ctx._generate_span_id()
        self.assertEqual(len(sid), 16)
        int(sid, 16)

    def test_start_span(self):
        """Start span tạo span mới và push vào active stack."""
        ctx = TraceContext()
        span = ctx.start_span("test-span")
        self.assertIsInstance(span, Span)
        self.assertEqual(span.name, "test-span")
        self.assertEqual(len(ctx._spans), 1)
        self.assertEqual(len(ctx._active_spans), 1)

    def test_active_span(self):
        """Active span trả về span cuối cùng trong stack."""
        ctx = TraceContext()
        span = ctx.start_span("root")
        self.assertIs(ctx.active_span(), span)

    def test_active_span_none(self):
        """Active span trả về None khi không có span."""
        ctx = TraceContext()
        self.assertIsNone(ctx.active_span())

    def test_end_span(self):
        """End span pop từ stack và ghi end_time."""
        ctx = TraceContext()
        span = ctx.start_span("to-end")
        ended = ctx.end_span()
        self.assertIs(ended, span)
        self.assertIsNotNone(span.end_time)
        self.assertEqual(len(ctx._active_spans), 0)

    def test_end_span_none(self):
        """End span trả về None khi không có active span."""
        ctx = TraceContext()
        result = ctx.end_span()
        self.assertIsNone(result)

    def test_parent_child_hierarchy(self):
        """Tạo parent-child span hierarchy."""
        ctx = TraceContext()
        parent = ctx.start_span("parent")
        child = ctx.start_span("child")  # Tự động dùng parent là active span
        self.assertEqual(child.parent_span_id, parent.span_id)
        self.assertEqual(child.trace_id, parent.trace_id)

    def test_explicit_parent(self):
        """Tạo span với explicit parent."""
        ctx = TraceContext()
        p1 = ctx.start_span("p1")
        p1_end = ctx.end_span()
        p2 = ctx.start_span("p2")
        # Tạo child với parent = p1 (đã end)
        child = ctx.start_span("child-of-p1", parent=p1)
        self.assertEqual(child.parent_span_id, p1.span_id)

    def test_span_duration_ms(self):
        """Tính duration_ms của span đã kết thúc."""
        ctx = TraceContext()
        span = ctx.start_span("duration-test")
        time.sleep(0.05)  # Đợi 50ms
        ctx.end_span()
        self.assertGreater(span.duration_ms, 40.0)

    def test_span_duration_while_active(self):
        """Duration tính từ start đến hiện tại khi span đang hoạt động."""
        ctx = TraceContext()
        span = ctx.start_span("active-duration")
        time.sleep(0.03)
        # Chưa end — duration vẫn tính từ start đến now
        self.assertGreater(span.duration_ms, 0)

    def test_add_event(self):
        """Thêm event vào span."""
        ctx = TraceContext()
        span = ctx.start_span("event-test")
        span.add_event("user.click", {"element": "button"})
        self.assertEqual(len(span.events), 1)
        self.assertEqual(span.events[0]["name"], "user.click")
        self.assertEqual(span.events[0]["attributes"]["element"], "button")

    def test_add_event_no_attributes(self):
        """Thêm event không có attributes."""
        ctx = TraceContext()
        span = ctx.start_span("event-no-attr")
        span.add_event("simple.event")
        self.assertEqual(len(span.events), 1)
        self.assertEqual(span.events[0]["attributes"], {})

    def test_span_to_dict(self):
        """Span.to_dict trả về dictionary đầy đủ."""
        ctx = TraceContext()
        span = ctx.start_span("dict-test")
        span.attributes["key"] = "val"
        ctx.end_span()
        d = span.to_dict()
        self.assertEqual(d["name"], "dict-test")
        self.assertIn("trace_id", d)
        self.assertIn("span_id", d)
        self.assertIn("duration_ms", d)
        self.assertEqual(d["attributes"]["key"], "val")

    def test_inject_trace_header(self):
        """Inject trace header trả về W3C format."""
        ctx = TraceContext()
        span = ctx.start_span("inject-test")
        headers = ctx.inject_trace_header()
        self.assertIn("traceparent", headers)
        tp = headers["traceparent"]
        parts = tp.split("-")
        self.assertEqual(parts[0], "00")  # Version
        self.assertEqual(len(parts[1]), 32)  # trace_id
        self.assertEqual(parts[3], "01")  # flags

    def test_inject_trace_header_no_span(self):
        """Inject trace header khi không có active span."""
        ctx = TraceContext()
        headers = ctx.inject_trace_header()
        self.assertIn("traceparent", headers)
        tp = headers["traceparent"]
        parts = tp.split("-")
        self.assertEqual(parts[0], "00")

    def test_extract_trace_header_valid(self):
        """Extract trace header từ W3C traceparent hợp lệ."""
        ctx = TraceContext()
        trace_id = "0af7651916cd43dd8448eb211c80319c"
        span_id = "b7ad6b7169203331"
        # span_id phải đủ 16 ký tự hex
        span_id = span_id.ljust(16, "0")[:16]
        headers = {"traceparent": f"00-{trace_id}-{span_id}-01"}
        tid, sid = ctx.extract_trace_header(headers)
        self.assertEqual(tid, trace_id)
        self.assertEqual(sid, span_id)

    def test_extract_trace_header_invalid(self):
        """Extract trace header từ traceparent không hợp lệ."""
        ctx = TraceContext()
        # Thiếu phần flags
        headers = {"traceparent": "00-abc-def"}
        tid, sid = ctx.extract_trace_header(headers)
        self.assertIsNone(tid)
        self.assertIsNone(sid)

    def test_extract_trace_header_missing(self):
        """Extract trace header khi không có traceparent."""
        ctx = TraceContext()
        tid, sid = ctx.extract_trace_header({})
        self.assertIsNone(tid)
        self.assertIsNone(sid)

    def test_inject_then_extract_roundtrip(self):
        """Inject headers rồi extract — roundtrip thành công."""
        ctx = TraceContext()
        span = ctx.start_span("roundtrip")
        headers = ctx.inject_trace_header()

        # Tạo context mới để extract
        ctx2 = TraceContext()
        tid, sid = ctx2.extract_trace_header(headers)
        self.assertEqual(tid, ctx.trace_id)
        self.assertEqual(sid, span.span_id)

    def test_multiple_spans_in_trace(self):
        """Nhiều spans trong cùng một trace."""
        ctx = TraceContext()
        s1 = ctx.start_span("s1")
        s2 = ctx.start_span("s2")
        s3 = ctx.start_span("s3")
        # Tất cả cùng trace_id
        self.assertEqual(s1.trace_id, s2.trace_id)
        self.assertEqual(s2.trace_id, s3.trace_id)
        # Hierarchy: s3 -> s2 -> s1
        self.assertEqual(s2.parent_span_id, s1.span_id)
        self.assertEqual(s3.parent_span_id, s2.span_id)

    def test_spans_returns_all(self):
        """Spans trả về tất cả spans đã tạo."""
        ctx = TraceContext()
        ctx.start_span("a")
        ctx.start_span("b")
        ctx.start_span("c")
        all_spans = ctx.spans()
        self.assertEqual(len(all_spans), 3)

    def test_export_json(self):
        """Export trace làm JSON."""
        ctx = TraceContext()
        ctx.start_span("root")
        ctx.start_span("child")
        ctx.end_span()
        ctx.end_span()
        output = ctx.export_json()
        data = json.loads(output)
        self.assertEqual(data["total_spans"], 2)
        self.assertEqual(len(data["spans"]), 2)
        self.assertEqual(data["active_spans"], 0)

    def test_span_end_sets_time(self):
        """Span.end() thiết lập end_time chính xác."""
        span = Span(
            name="test",
            trace_id="0" * 32,
            span_id="0" * 16,
            parent_span_id="",
            start_time=datetime.now(timezone.utc),
        )
        self.assertIsNone(span.end_time)
        span.end()
        self.assertIsNotNone(span.end_time)

    def test_span_attributes(self):
        """Span có thể set attributes tùy ý."""
        ctx = TraceContext()
        span = ctx.start_span("attr-test")
        span.attributes["http.method"] = "GET"
        span.attributes["http.url"] = "/api/v1/users"
        self.assertEqual(span.attributes["http.method"], "GET")

    def test_extract_invalid_traceparent_short_parts(self):
        """Extract với traceparent không đủ 4 phần trả về (None, None)."""
        ctx = TraceContext(service_name="test")
        result = ctx.extract_trace_header({"traceparent": "00-abc-def-01"})
        self.assertEqual(result, (None, None))

    def test_extract_invalid_traceparent_bad_hex(self):
        """Extract với traceparent chứa ký tự không phải hex trả về (None, None)."""
        ctx = TraceContext(service_name="test")
        result = ctx.extract_trace_header({"traceparent": "00-" + "z" * 32 + "-" + "z" * 16 + "-01"})
        self.assertEqual(result, (None, None))

    def test_extract_empty_traceparent_header(self):
        """Extract với traceparent rỗng trả về (None, None)."""
        ctx = TraceContext(service_name="test")
        result = ctx.extract_trace_header({"traceparent": ""})
        self.assertEqual(result, (None, None))

    def test_extract_missing_traceparent_header(self):
        """Extract không có traceparent header trả về (None, None)."""
        ctx = TraceContext(service_name="test")
        result = ctx.extract_trace_header({})
        self.assertEqual(result, (None, None))

    def test_extract_wrong_trace_id_length(self):
        """Extract với trace_id độ dài sai trả về (None, None)."""
        ctx = TraceContext(service_name="test")
        result = ctx.extract_trace_header({"traceparent": "00-" + "a" * 10 + "-" + "b" * 16 + "-01"})
        self.assertEqual(result, (None, None))

    def test_extract_wrong_span_id_length(self):
        """Extract với span_id độ dài sai trả về (None, None)."""
        ctx = TraceContext(service_name="test")
        result = ctx.extract_trace_header({"traceparent": "00-" + "a" * 32 + "-" + "b" * 5 + "-01"})
        self.assertEqual(result, (None, None))


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    unittest.main()
