from __future__ import annotations

from typing import Any, Dict


class FastAPIObservabilityEmitter:
    """Emitter cho các thành phần observability của FastAPI."""

    def __init__(self, collection: Any | None = None):
        self.collection = collection or {}

    def generate(self) -> Dict[str, str]:
        """Tạo tất cả các tệp observability cho FastAPI."""
        result: Dict[str, str] = {}
        result.update(self.generate_service())
        result.update(self.generate_middleware())
        result.update(self.generate_metrics_endpoint())
        return result

    def generate_service(self) -> Dict[str, str]:
        """Tạo ObservabilityService — ghi metric, log cấu trúc, trace span."""
        code = '''\
"""Dịch vụ observability cho FastAPI — metric, log cấu trúc, trace."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class LogLevel(str, Enum):
    """Các mức độ log."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class Span:
    """Đại diện cho một trace span."""
    trace_id: str
    span_id: str
    name: str
    start_time: float
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

    def finish(self) -> None:
        """Kết thúc span và ghi thời gian kết thúc."""
        self.end_time = time.time()

    @property
    def duration_ms(self) -> float:
        """Tính toán thời gian thực hiện của span (ms)."""
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000


class MetricRegistry:
    """Registry đơn giản cho các metric (tương thích Prometheus)."""

    def __init__(self) -> None:
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, List[float]] = defaultdict(list)

    def inc(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Tăng giá trị counter."""
        key = self._key(name, labels)
        self._counters[key] += value

    def set(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Đặt giá trị gauge."""
        key = self._key(name, labels)
        self._gauges[key] = value

    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Ghi nhận một observation vào histogram."""
        key = self._key(name, labels)
        self._histograms[key].append(value)

    def export(self) -> str:
        """Xuất tất cả metric dưới định dạng Prometheus text."""
        lines: List[str] = []
        for key, value in self._counters.items():
            lines.append(f"# TYPE {self._base(key)} counter")
            lines.append(f"{self._formatted(key)} {value}")
        for key, value in self._gauges.items():
            lines.append(f"# TYPE {self._base(key)} gauge")
            lines.append(f"{self._formatted(key)} {value}")
        for key, values in self._histograms.items():
            lines.append(f"# TYPE {self._base(key)} histogram")
            lines.append(f"{self._formatted(key)}_count {len(values)}")
            if values:
                lines.append(f"{self._formatted(key)}_sum {sum(values)}")
                lines.append(f"{self._formatted(key)}_min {min(values)}")
                lines.append(f"{self._formatted(key)}_max {max(values)}")
        return "\\n".join(lines)

    @staticmethod
    def _key(name: str, labels: Optional[Dict[str, str]]) -> str:
        """Tạo key duy nhất cho metric với label."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    @staticmethod
    def _base(key: str) -> str:
        """Trích xuất tên base từ key."""
        return key.split("{")[0]

    @staticmethod
    def _formatted(key: str) -> str:
        """Định dạng key cho Prometheus."""
        return key


class StructuredLogger:
    """Logger ghi log có cấu trúc với trường metadata."""

    def __init__(self, service_name: str = "midicoder") -> None:
        self.service_name = service_name
        self._entries: List[Dict[str, Any]] = []

    def log(self, level: LogLevel, message: str, fields: Optional[Dict[str, Any]] = None) -> None:
        """Ghi một log entry có cấu trúc."""
        entry = {
            "timestamp": time.time(),
            "level": level.value,
            "service": self.service_name,
            "message": message,
            "fields": fields or {},
        }
        self._entries.append(entry)
        print(f"[{level.value}] {self.service_name}: {message} | {entry['fields']}")

    def get_entries(self, level: Optional[LogLevel] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Lấy các log entries, tùy chọn lọc theo level."""
        entries = self._entries
        if level:
            entries = [e for e in entries if e["level"] == level.value]
        return entries[-limit:]


class ObservabilityService:
    """Dịch vụ chính cho observability — tích hợp metric, log, và trace.

    Cung cấp giao diện thống nhất để ghi metric, log cấu trúc,
    và tạo trace span trong ứng dụng FastAPI.
    """

    def __init__(self, service_name: str = "midicoder") -> None:
        """Khởi tạo ObservabilityService với tên dịch vụ.

        Args:
            service_name: Tên của dịch vụ để gắn nhãn log và metric.
        """
        self.service_name = service_name
        self.metrics = MetricRegistry()
        self.logger = StructuredLogger(service_name)
        self._active_spans: Dict[str, Span] = {}
        self._completed_spans: List[Span] = []

    def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Ghi nhận một metric (dạng gauge).

        Args:
            name: Tên của metric.
            value: Giá trị số của metric.
            labels: Các label để phân loại metric.
        """
        self.metrics.set(name, value, labels)
        self.logger.log(
            LogLevel.DEBUG,
            f"Metric recorded: {name}={value}",
            {"name": name, "value": value, "labels": labels},
        )

    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Tăng counter metric.

        Args:
            name: Tên counter.
            value: Giá trị tăng (mặc định 1.0).
            labels: Các label để phân loại.
        """
        self.metrics.inc(name, value, labels)

    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Ghi nhận observation vào histogram.

        Args:
            name: Tên histogram.
            value: Giá trị observation.
            labels: Các label để phân loại.
        """
        self.metrics.observe(name, value, labels)

    def log(self, level: LogLevel, message: str, fields: Optional[Dict[str, Any]] = None) -> None:
        """Ghi một log entry có cấu trúc.

        Args:
            level: Mức độ log.
            message: Thông điệp log.
            fields: Các trường metadata bổ sung.
        """
        self.logger.log(level, message, fields)

    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> str:
        """Bắt đầu một trace span mới.

        Args:
            name: Tên của span.
            attributes: Các attribute gắn với span.

        Returns:
            span_id: ID duy nhất của span được tạo.
        """
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            name=name,
            start_time=time.time(),
            attributes=attributes or {},
        )
        self._active_spans[span_id] = span
        self.logger.log(
            LogLevel.DEBUG,
            f"Span started: {name}",
            {"trace_id": trace_id, "span_id": span_id},
        )
        return span_id

    def finish_span(self, span_id: str) -> Optional[Span]:
        """Kết thúc một trace span.

        Args:
            span_id: ID của span cần kết thúc.

        Returns:
            Span đã hoàn thành hoặc None nếu không tìm thấy.
        """
        span = self._active_spans.pop(span_id, None)
        if span:
            span.finish()
            self._completed_spans.append(span)
            self.logger.log(
                LogLevel.DEBUG,
                f"Span finished: {span.name} ({span.duration_ms:.2f}ms)",
                {"span_id": span_id, "duration_ms": span.duration_ms},
            )
        return span

    def export_metrics(self) -> str:
        """Xuất tất cả metric dưới định dạng Prometheus text.

        Returns:
            Chuỗi metric đã được định dạng.
        """
        return self.metrics.export()

    def get_recent_spans(self, limit: int = 50) -> List[Span]:
        """Lấy các span đã hoàn thành gần đây.

        Args:
            limit: Số lượng span tối đa.

        Returns:
            Danh sách các span gần đây.
        """
        return self._completed_spans[-limit:]

    def get_logs(self, level: Optional[LogLevel] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Lấy các log entries gần đây.

        Args:
            level: Lọc theo mức độ log (tùy chọn).
            limit: Số lượng entries tối đa.

        Returns:
            Danh sách các log entries.
        """
        return self.logger.get_entries(level, limit)
'''
        return {"src/observability/observability_service.py": code}

    def generate_middleware(self) -> Dict[str, str]:
        """Tạo Starlette middleware để tự động instrument HTTP request."""
        code = '''\
"""Middleware observability cho FastAPI — tự động ghi metric, log, và trace."""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


# Import ObservabilityService từ mô-đun service
# Trong thực tế, service sẽ được inject qua dependency injection của FastAPI
_observability_service: Optional["ObservabilityService"] = None


def set_observability_service(service: "ObservabilityService") -> None:
    """Đặt instance ObservabilityService toàn cục cho middleware.

    Args:
        service: Instance của ObservabilityService.
    """
    global _observability_service
    _observability_service = service


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware tự động instrument các yêu cầu HTTP.

    Ghi lại:
    - Thời gian xử lý request (histogram)
    - Số lượng request theo method và status (counter)
    - Log cấu trúc cho mỗi request/response
    - Trace span cho từng request
    """

    def __init__(
        self,
        app: Any,
        service: Optional["ObservabilityService"] = None,
        exclude_paths: Optional[list[str]] = None,
    ) -> None:
        """Khởi tạo ObservabilityMiddleware.

        Args:
            app: Ứng dụng ASGI.
            service: Instance ObservabilityService (tùy chọn).
            exclude_paths: Các đường dẫn cần loại trừ khỏi quan sát.
        """
        super().__init__(app)
        self._service = service or _observability_service
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Xử lý yêu cầu HTTP và tự động ghi observability data.

        Args:
            request: Yêu cầu HTTP đến.
            call_next: Hàm gọi middleware/endpoint tiếp theo.

        Returns:
            Response từ ứng dụng.
        """
        # Bỏ qua các đường dẫn bị loại trừ
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Khởi tạo service nếu chưa có
        service = self._service
        if not service:
            return await call_next(request)

        # Bắt đầu trace span cho request này
        span_id = service.start_span(
            name=f"{request.method} {request.url.path}",
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.client_ip": request.client.host if request.client else None,
            },
        )

        # Ghi log request đến
        service.log(
            "INFO",
            f"Request received: {request.method} {request.url.path}",
            fields={
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "content_type": request.headers.get("content-type"),
                "user_agent": request.headers.get("user-agent"),
            },
        )

        # Đo thời gian xử lý
        start_time = time.time()
        try:
            response = await call_next(request)
        except Exception as exc:
            # Log lỗi và hoàn thành span
            service.log(
                "ERROR",
                f"Request failed: {request.method} {request.url.path}",
                fields={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
            )
            if span_id:
                span = service.finish_span(span_id)
                if span:
                    span.attributes["http.error"] = str(exc)
            raise

        # Tính thời gian xử lý
        duration_ms = (time.time() - start_time) * 1000

        # Ghi histogram cho thời gian request
        service.observe_histogram(
            "http_request_duration_ms",
            duration_ms,
            labels={
                "method": request.method,
                "path": request.url.path,
                "status": str(response.status_code),
            },
        )

        # Tăng counter cho số lượng request
        service.increment_counter(
            "http_requests_total",
            labels={
                "method": request.method,
                "path": request.url.path,
                "status": str(response.status_code),
            },
        )

        # Log response
        log_level = "WARNING" if response.status_code >= 500 else "INFO"
        service.log(
            log_level,
            f"Request completed: {request.method} {request.url.path} -> {response.status_code}",
            fields={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "response_content_length": response.headers.get("content-length"),
            },
        )

        # Hoàn thành trace span
        if span_id:
            span = service.finish_span(span_id)
            if span:
                span.attributes["http.status_code"] = response.status_code
                span.attributes["http.duration_ms"] = round(duration_ms, 2)

        return response
'''
        return {"src/observability/observability_middleware.py": code}

    def generate_metrics_endpoint(self) -> Dict[str, str]:
        """Tạo FastAPI endpoint /metrics để export Prometheus metrics."""
        code = '''\\
"""Endpoint /metrics cho FastAPI — export Prometheus metrics."""

from __future__ import annotations

from fastapi import APIRouter

# Import ObservabilityService từ mô-đun service
# Trong thực tế, service sẽ được inject qua dependency injection của FastAPI
_observability_service: "ObservabilityService | None" = None


def set_metrics_service(service: "ObservabilityService") -> None:
    """Đặt instance ObservabilityService cho metrics endpoint.

    Args:
        service: Instance của ObservabilityService.
    """
    global _observability_service
    _observability_service = service


router = APIRouter()


@router.get("/metrics")
def metrics_endpoint() -> str:
    """Xuất tất cả metric dưới định dạng Prometheus text.

    Returns:
        Chuỗi metric đã được định dạng Prometheus.
    """
    service = _observability_service
    if not service:
        return "# No observability service configured\\n"
    return service.export_metrics()
'''
        return {"src/observability/metrics_endpoint.py": code}
