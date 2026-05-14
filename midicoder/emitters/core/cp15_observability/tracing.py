# coding: utf-8
"""
Mô-đun tracing runtime engine (CP15).

Cung cấp:
- Span: Một span trong trace — đại diện cho một operation
- TraceContext: Context cho distributed tracing với W3C propagation

W3C Trace Context format:
- traceparent: 00-{trace_id}-{span_id}-{flags}
- tracestate: vendor-specific

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Span:
    """Một span trong trace — đại diện cho một operation.

    Attributes:
        name: Tên span
        trace_id: Trace ID (unique cho toàn bộ trace)
        span_id: Span ID (unique cho span)
        parent_span_id: Parent span ID (nếu có)
        start_time: Thời gian bắt đầu
        end_time: Thời gian kết thúc (None nếu đang hoạt động)
        events: Danh sách events trong span
        attributes: Attributes của span
    """

    name: str
    trace_id: str
    span_id: str
    parent_span_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    events: list = field(default_factory=list)
    attributes: dict = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        """Tính duration (ms) từ start đến end.

        Returns:
            Thời gian duration tính bằng mili giây.
            Nếu span chưa kết thúc, trả về thời gian từ start đến hiện tại.
        """
        end = self.end_time if self.end_time is not None else datetime.now(timezone.utc)
        delta = end - self.start_time
        return delta.total_seconds() * 1000.0

    def end(self) -> None:
        """Kết thúc span, ghi end_time."""
        self.end_time = datetime.now(timezone.utc)

    def add_event(self, name: str, attributes: Optional[dict] = None) -> None:
        """Thêm event vào span.

        Args:
            name: Tên event
            attributes: Các attributes của event (tùy chọn)
        """
        if attributes is None:
            attributes = {}
        event = {
            "name": name,
            "attributes": attributes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.events.append(event)

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary chứa tất cả attributes của Span
        """
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": round(self.duration_ms, 3),
            "events": list(self.events),
            "attributes": dict(self.attributes),
        }


class TraceContext:
    """Context cho distributed tracing.

    Cung cấp:
    - start_span(name, parent=None) -> tạo span mới
    - active_span() -> lấy span đang hoạt động
    - end_span() -> kết thúc span đang hoạt động
    - inject_trace_header() -> inject trace headers cho propagation (W3C format)
    - extract_trace_header(headers) -> extract trace context từ headers
    - spans() -> lấy tất cả spans trong trace
    - export_json() -> export trace làm JSON

    W3C Trace Context format:
    - traceparent: 00-{trace_id}-{span_id}-{flags}
    - tracestate: vendor-specific
    """

    def __init__(self, service_name: str = "midicoder") -> None:
        """Khởi tạo TraceContext.

        Args:
            service_name: Tên service
        """
        self._service_name: str = service_name
        self._trace_id: str = self._generate_trace_id()
        self._spans: list[Span] = []
        self._active_spans: list[Span] = []

    @property
    def trace_id(self) -> str:
        """Lấy trace ID hiện tại của context.

        Returns:
            Trace ID (32 ký tự hex)
        """
        return self._trace_id

    def _generate_trace_id(self) -> str:
        """Generate random 32-char hex trace ID.

        Returns:
            Chuỗi hex 32 ký tự
        """
        return os.urandom(16).hex()

    def _generate_span_id(self) -> str:
        """Generate random 16-char hex span ID.

        Returns:
            Chuỗi hex 16 ký tự
        """
        return os.urandom(8).hex()

    def start_span(self, name: str, parent: Optional[Span] = None) -> Span:
        """Tạo span mới. Nếu không có parent, dùng active span.

        Span mới được push vào active stack và có thể làm parent
        cho các span con sau này.

        Args:
            name: Tên span
            parent: Parent span (tùy chọn, mặc định là active span)

        Returns:
            Span vừa tạo
        """
        if parent is None and self._active_spans:
            parent = self._active_spans[-1]

        parent_span_id = parent.span_id if parent is not None else ""

        span = Span(
            name=name,
            trace_id=self._trace_id,
            span_id=self._generate_span_id(),
            parent_span_id=parent_span_id,
            start_time=datetime.now(timezone.utc),
        )

        self._spans.append(span)
        self._active_spans.append(span)
        return span

    def active_span(self) -> Optional[Span]:
        """Lấy span đang hoạt động (cuối cùng trong stack).

        Returns:
            Span đang hoạt động hoặc None nếu không có
        """
        if self._active_spans:
            return self._active_spans[-1]
        return None

    def end_span(self) -> Optional[Span]:
        """Kết thúc span đang hoạt động.

        Pop span từ active stack và ghi end_time.

        Returns:
            Span vừa kết thúc hoặc None nếu không có active span
        """
        if not self._active_spans:
            return None
        span = self._active_spans.pop()
        span.end()
        return span

    def spans(self) -> list[Span]:
        """Lấy tất cả spans.

        Returns:
            Danh sách tất cả Span trong trace
        """
        return list(self._spans)

    def inject_trace_header(self, format: str = "w3c") -> dict:
        """Inject trace headers cho propagation.

        Hỗ trợ 2 định dạng:
        - w3c: W3C Trace Context (traceparent + tracestate)
        - b3: Zipkin B3 (X-B3-TraceId, X-B3-SpanId, X-B3-Sampled)

        Args:
            format: Định dạng propagation ("w3c" hoặc "b3")

        Returns:
            Dictionary chứa trace headers
        """
        active = self.active_span()

        if format == "b3":
            return self._inject_b3(active)

        # Default: W3C Trace Context
        if active is None:
            return {"traceparent": f"00-{self._trace_id}-{'0' * 16}-01"}

        return {
            "traceparent": f"00-{self._trace_id}-{active.span_id}-01",
            "tracestate": self._service_name,
        }

    def _inject_b3(self, active: Optional[Span]) -> dict:
        """Inject B3 headers cho Zipkin propagation.

        Returns:
            Dictionary với X-B3-TraceId, X-B3-SpanId, X-B3-Sampled
        """
        span_id = active.span_id if active is not None else "0" * 16
        headers = {
            "X-B3-TraceId": self._trace_id,
            "X-B3-SpanId": span_id,
            "X-B3-Sampled": "1",
        }
        if active is not None and active.parent_span_id:
            headers["X-B3-ParentSpanId"] = active.parent_span_id
        return headers

    def extract_trace_header(self, headers: dict, format: str = "w3c") -> tuple:
        """Extract trace_id, span_id từ propagation headers.

        Hỗ trợ 2 định dạng:
        - w3c: Parse traceparent header (W3C Trace Context)
        - b3: Parse X-B3-TraceId, X-B3-SpanId headers

        Args:
            headers: Dictionary chứa headers
            format: Định dạng propagation ("w3c" hoặc "b3")

        Returns:
            Tuple (trace_id, span_id) hoặc (None, None) nếu không parse được
        """
        if format == "b3":
            return self._extract_b3(headers)

        return self._extract_w3c(headers)

    def _extract_w3c(self, headers: dict) -> tuple:
        """Extract trace_id, span_id từ W3C traceparent header.

        Parse traceparent header theo định dạng:
        00-{trace_id-32hex}-{span_id-16hex}-{flags-2hex}

        Args:
            headers: Dictionary chứa headers

        Returns:
            Tuple (trace_id, span_id) hoặc (None, None) nếu không parse được
        """
        traceparent = headers.get("traceparent", "")
        if not traceparent:
            return (None, None)

        try:
            parts = traceparent.split("-")
            if len(parts) < 4:
                return (None, None)

            version = parts[0]
            trace_id = parts[1]
            span_id = parts[2]
            # flags = parts[3]  # Không sử dụng trong extract

            # Validate format: trace_id 32 hex, span_id 16 hex
            if len(trace_id) != 32 or len(span_id) != 16:
                return (None, None)

            # Kiểm tra các ký tự hex
            int(trace_id, 16)
            int(span_id, 16)

            return (trace_id, span_id)
        except (ValueError, IndexError):
            return (None, None)

    def _extract_b3(self, headers: dict) -> tuple:
        """Extract trace_id, span_id từ B3 headers.

        Args:
            headers: Dictionary chứa X-B3-TraceId, X-B3-SpanId

        Returns:
            Tuple (trace_id, span_id) hoặc (None, None) nếu không parse được
        """
        trace_id = headers.get("X-B3-TraceId")
        span_id = headers.get("X-B3-SpanId")

        if not trace_id or not span_id:
            return (None, None)

        # Normalize: B3 trace_id có thể 16 hoặc 32 hex
        if len(trace_id) == 16:
            trace_id = trace_id * 2

        return (trace_id, span_id)

    def export_json(self) -> str:
        """Export toàn bộ trace làm JSON.

        Returns:
            Chuỗi JSON chứa trace context và danh sách spans
        """
        trace_data = {
            "service_name": self._service_name,
            "trace_id": self._trace_id,
            "spans": [span.to_dict() for span in self._spans],
            "total_spans": len(self._spans),
            "active_spans": len(self._active_spans),
        }
        return json.dumps(trace_data, sort_keys=True, default=str)
