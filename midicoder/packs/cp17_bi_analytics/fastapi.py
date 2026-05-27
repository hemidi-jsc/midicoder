from __future__ import annotations

from typing import Any, Dict


class FastAPIAnalyticsEmitter:
    """Emitter cho các thành phần Business Intelligence & Analytics của FastAPI."""

    def __init__(self, collection: Any | None = None):
        self.collection = collection or {}

    def generate(self) -> Dict[str, str]:
        """Tạo tất cả các tệp analytics cho FastAPI."""
        result: Dict[str, str] = {}
        result.update(self.generate_service())
        result.update(self.generate_router())
        return result

    def generate_service(self) -> Dict[str, str]:
        """Tạo AnalyticsService — quản lý truy vấn, dashboard, và báo cáo."""
        code = '''\
"""Dịch vụ Business Intelligence & Analytics cho FastAPI — truy vấn, dashboard, và báo cáo."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ReportFormat(str, Enum):
    """Định dạng của báo cáo."""
    PDF = "PDF"
    CSV = "CSV"
    EXCEL = "EXCEL"
    JSON = "JSON"


class ReportStatus(str, Enum):
    """Trạng thái của báo cáo."""
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ScheduleFrequency(str, Enum):
    """Tần suất lập lịch báo cáo."""
    ONCE = "ONCE"
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class ChartType(str, Enum):
    """Loại biểu đồ hiển thị trên dashboard."""
    LINE = "LINE"
    BAR = "BAR"
    PIE = "PIE"
    GAUGE = "GAUGE"
    TABLE = "TABLE"


@dataclass
class AnalyticsModel:
    """Mô hình phân tích — định nghĩa nguồn dữ liệu và chỉ số có sẵn."""
    name: str
    description: str
    available_filters: List[str] = field(default_factory=list)
    available_metrics: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if not self.description:
            self.description = f"Mô hình phân tích: {self.name}"


@dataclass
class AnalyticsQuery:
    """Truy vấn phân tích — định nghĩa bộ lọc và chỉ số cần trả về."""
    model_name: str
    filters: Dict[str, Any] = field(default_factory=dict)
    metrics: List[str] = field(default_factory=list)
    group_by: List[str] = field(default_factory=list)
    order_by: Optional[str] = None
    limit: int = 1000
    offset: int = 0


@dataclass
class AnalyticsResult:
    """Kết quả từ truy vấn phân tích."""
    query_id: str
    model_name: str
    rows: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    execution_time_ms: float = 0.0
    queried_at: float = field(default_factory=time.time)


@dataclass
class Widget:
    """Một widget hiển thị trên dashboard — biểu đồ, bảng, hoặc chỉ số."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    chart_type: ChartType = ChartType.LINE
    metric: str = ""
    model_name: str = ""
    filters: Dict[str, Any] = field(default_factory=dict)
    position_x: int = 0
    position_y: int = 0
    width: int = 1
    height: int = 1
    title: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        if not self.title:
            self.title = self.name or self.metric or "Widget"


@dataclass
class Dashboard:
    """Dashboard chứa nhiều widget để hiển thị dữ liệu phân tích."""
    name: str
    widgets: List[Widget] = field(default_factory=list)
    description: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def add_widget(self, widget: Widget) -> None:
        """Thêm widget vào dashboard.

        Args:
            widget: Widget cần thêm.
        """
        self.widgets.append(widget)
        self.updated_at = time.time()

    def remove_widget(self, widget_id: str) -> bool:
        """Xóa widget khỏi dashboard theo ID.

        Args:
            widget_id: ID của widget cần xóa.

        Returns:
            True nếu xóa thành công, False nếu không tìm thấy.
        """
        before = len(self.widgets)
        self.widgets = [w for w in self.widgets if w.id != widget_id]
        if len(self.widgets) < before:
            self.updated_at = time.time()
            return True
        return False


@dataclass
class ReportDefinition:
    """Định nghĩa báo cáo — cấu hình nội dung và tần suất xuất bản."""
    name: str
    model_name: str
    filters: Dict[str, Any] = field(default_factory=dict)
    metrics: List[str] = field(default_factory=list)
    format: ReportFormat = ReportFormat.PDF
    frequency: ScheduleFrequency = ScheduleFrequency.ONCE
    next_run: Optional[float] = None
    recipients: List[str] = field(default_factory=list)
    description: str = ""
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if not self.description:
            self.description = f"Báo cáo: {self.name}"


@dataclass
class ReportSnapshot:
    """Một bản chụp báo cáo đã được tạo — lưu kết quả thực tế."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    report_name: str = ""
    status: ReportStatus = ReportStatus.PENDING
    format: ReportFormat = ReportFormat.PDF
    generated_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    file_size_bytes: int = 0
    rows_count: int = 0
    error_message: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

    def mark_generating(self) -> None:
        """Đánh dấu báo cáo đang được tạo."""
        self.status = ReportStatus.GENERATING

    def mark_completed(self, rows: int = 0, size: int = 0) -> None:
        """Đánh dấu báo cáo đã tạo xong.

        Args:
            rows: Số hàng dữ liệu trong báo cáo.
            size: Kích thước tệp báo cáo (byte).
        """
        self.status = ReportStatus.COMPLETED
        self.completed_at = time.time()
        self.rows_count = rows
        self.file_size_bytes = size

    def mark_failed(self, error: str) -> None:
        """Đánh dấu báo cáo thất bại.

        Args:
            error: Thông điệp lỗi.
        """
        self.status = ReportStatus.FAILED
        self.error_message = error


class AnalyticsEngine:
    """Động cơ phân tích — lưu trữ mô hình và xử lý truy vấn."""

    def __init__(self) -> None:
        self._models: Dict[str, AnalyticsModel] = {}
        self._query_history: List[AnalyticsResult] = []

    def register_model(self, model: AnalyticsModel) -> None:
        """Đăng ký mô hình phân tích mới.

        Args:
            model: Mô hình cần đăng ký.
        """
        self._models[model.name] = model

    def list_models(self) -> List[AnalyticsModel]:
        """Lấy danh sách tất cả mô hình phân tích.

        Returns:
            Danh sách mô hình phân tích.
        """
        return list(self._models.values())

    def get_model(self, name: str) -> Optional[AnalyticsModel]:
        """Lấy mô hình phân tích theo tên.

        Args:
            name: Tên của mô hình.

        Returns:
            Mô hình nếu tìm thấy, ngược lại None.
        """
        return self._models.get(name)

    def query(self, query: AnalyticsQuery) -> AnalyticsResult:
        """Thực thi truy vấn phân tích.

        Args:
            query: Đối tượng truy vấn với mô hình, bộ lọc, và chỉ số.

        Returns:
            Kết quả truy vấn phân tích.
        """
        start = time.time()
        model = self._models.get(query.model_name)

        query_id = str(uuid.uuid4())
        rows: List[Dict[str, Any]] = []

        if model:
            # Giả lập dữ liệu từ mô hình
            # Trong thực tế, sẽ kết nối với kho dữ liệu hoặc data warehouse
            for i in range(min(query.limit, 100)):
                row: Dict[str, Any] = {"row_index": i}
                for metric in (query.metrics or model.available_metrics):
                    row[metric] = self._generate_sample_value(metric, i)
                rows.append(row)

        execution_time = (time.time() - start) * 1000

        result = AnalyticsResult(
            query_id=query_id,
            model_name=query.model_name,
            rows=rows,
            total_count=len(rows),
            execution_time_ms=execution_time,
        )
        self._query_history.append(result)
        return result

    @staticmethod
    def _generate_sample_value(metric: str, index: int) -> float:
        """Tạo giá trị mẫu cho chỉ số (dùng trong demo).

        Args:
            metric: Tên chỉ số.
            index: Chỉ số hàng.

        Returns:
            Giá trị mẫu.
        """
        import hashlib
        h = hashlib.md5(f"{metric}:{index}".encode()).hexdigest()
        return float(int(h[:8], 16)) / 0xFFFFFFFF * 100


class DashboardBuilder:
    """Xây dựng và quản lý dashboard — tạo, lưu trữ, và truy vấn."""

    def __init__(self) -> None:
        self._dashboards: Dict[str, Dashboard] = {}

    def create(self, name: str, description: str = "") -> Dashboard:
        """Tạo dashboard mới.

        Args:
            name: Tên duy nhất của dashboard.
            description: Mô tả dashboard.

        Returns:
            Dashboard mới được tạo.
        """
        dashboard = Dashboard(name=name, description=description)
        self._dashboards[name] = dashboard
        return dashboard

    def get(self, name: str) -> Optional[Dashboard]:
        """Lấy dashboard theo tên.

        Args:
            name: Tên của dashboard.

        Returns:
            Dashboard nếu tìm thấy, ngược lại None.
        """
        return self._dashboards.get(name)

    def list_all(self) -> List[Dashboard]:
        """Lấy tất cả dashboard đã tạo.

        Returns:
            Danh sách tất cả dashboard.
        """
        return list(self._dashboards.values())

    def update(self, name: str, dashboard: Dashboard) -> bool:
        """Cập nhật dashboard hiện có.

        Args:
            name: Tên của dashboard cần cập nhật.
            dashboard: Dashboard mới để thay thế.

        Returns:
            True nếu cập nhật thành công, False nếu không tìm thấy.
        """
        if name in self._dashboards:
            self._dashboards[name] = dashboard
            return True
        return False

    def delete(self, name: str) -> bool:
        """Xóa dashboard theo tên.

        Args:
            name: Tên của dashboard cần xóa.

        Returns:
            True nếu xóa thành công, False nếu không tồn tại.
        """
        return self._dashboards.pop(name, None) is not None


class ReportScheduler:
    """Lập lịch và quản lý báo cáo — lên lịch, tạo, và lưu lịch sử."""

    def __init__(self) -> None:
        self._definitions: Dict[str, ReportDefinition] = {}
        self._snapshots: Dict[str, List[ReportSnapshot]] = defaultdict(list)

    def schedule(self, report_def: ReportDefinition) -> ReportDefinition:
        """Lên lịch báo cáo mới.

        Args:
            report_def: Định nghĩa báo cáo cần lên lịch.

        Returns:
            Định nghĩa báo cáo đã được lưu.
        """
        self._definitions[report_def.name] = report_def
        return report_def

    def get_definitions(self) -> List[ReportDefinition]:
        """Lấy tất cả định nghĩa báo cáo đã lên lịch.

        Returns:
            Danh sách định nghĩa báo cáo.
        """
        return list(self._definitions.values())

    def generate(self, report_name: str) -> ReportSnapshot:
        """Tạo báo cáo theo định nghĩa đã lên lịch.

        Args:
            report_name: Tên của báo cáo cần tạo.

        Returns:
            Bản chụp báo cáo đã tạo.
        """
        definition = self._definitions.get(report_name)
        if not definition:
            snapshot = ReportSnapshot(
                report_name=report_name,
                status=ReportStatus.FAILED,
                error_message=f"Không tìm thấy định nghĩa báo cáo: {report_name}",
            )
            self._snapshots[report_name].append(snapshot)
            return snapshot

        snapshot = ReportSnapshot(
            report_name=report_name,
            format=definition.format,
        )
        snapshot.mark_generating()

        # Giả lập quá trình tạo báo cáo
        rows_count = 0
        try:
            rows_count = 50  # Giả lập 50 hàng dữ liệu
            snapshot.mark_completed(rows=rows_count, size=rows_count * 256)
        except Exception as e:
            snapshot.mark_failed(str(e))

        self._snapshots[report_name].append(snapshot)
        return snapshot

    def get_history(self, report_name: str) -> List[ReportSnapshot]:
        """Lấy lịch sử báo cáo theo tên.

        Args:
            report_name: Tên của báo cáo.

        Returns:
            Danh sách bản chụp báo cáo theo thời gian.
        """
        return list(self._snapshots.get(report_name, []))

    def get_failed_reports(self) -> List[ReportSnapshot]:
        """Lấy tất cả báo cáo thất bại.

        Returns:
            Danh sách bản chụp báo cáo có trạng thái FAILED.
        """
        failed: List[ReportSnapshot] = []
        for snapshots in self._snapshots.values():
            failed.extend(s for s in snapshots if s.status == ReportStatus.FAILED)
        return failed


class AnalyticsService:
    """Dịch vụ Business Intelligence & Analytics — tích hợp truy vấn, dashboard, và báo cáo.

    Cung cấp giao diện thống nhất để:
    - Truy vấn dữ liệu phân tích từ nhiều mô hình
    - Xây dựng và quản lý dashboard BI
    - Lập lịch và tạo báo cáo tự động
    """

    def __init__(self) -> None:
        """Khởi tạo AnalyticsService với các thành phần con."""
        self.engine = AnalyticsEngine()
        self.dashboard_builder = DashboardBuilder()
        self.report_scheduler = ReportScheduler()

    def query_analytics(self, model_name: str, filters: Optional[Dict[str, Any]] = None) -> AnalyticsResult:
        """Truy vấn dữ liệu phân tích từ mô hình chỉ định.

        Args:
            model_name: Tên của mô hình phân tích.
            filters: Bộ lọc áp dụng cho truy vấn (tùy chọn).

        Returns:
            Kết quả truy vấn phân tích.
        """
        query = AnalyticsQuery(
            model_name=model_name,
            filters=filters or {},
        )
        return self.engine.query(query)

    def create_dashboard(self, definition: Dict[str, Any]) -> Dashboard:
        """Tạo dashboard BI mới từ định nghĩa.

        Args:
            definition: Định nghĩa dashboard với tên, mô tả, và cấu hình widget.

        Returns:
            Dashboard mới được tạo.
        """
        name = definition.get("name", f"dashboard_{uuid.uuid4().hex[:8]}")
        description = definition.get("description", "")
        dashboard = self.dashboard_builder.create(name, description)

        # Thêm widget từ định nghĩa
        widgets_def = definition.get("widgets", [])
        for widget_def in widgets_def:
            widget = Widget(
                name=widget_def.get("name", ""),
                chart_type=ChartType(widget_def.get("chart_type", "LINE")),
                metric=widget_def.get("metric", ""),
                model_name=widget_def.get("model_name", ""),
                title=widget_def.get("title", ""),
            )
            dashboard.add_widget(widget)

        return dashboard

    def schedule_report(self, report_def: Dict[str, Any]) -> ReportDefinition:
        """Lên lịch báo cáo tự động.

        Args:
            report_def: Định nghĩa báo cáo với tên, mô hình, và tần suất.

        Returns:
            Định nghĩa báo cáo đã lên lịch.
        """
        definition = ReportDefinition(
            name=report_def.get("name", f"report_{uuid.uuid4().hex[:8]}"),
            model_name=report_def.get("model_name", ""),
            filters=report_def.get("filters", {}),
            metrics=report_def.get("metrics", []),
            format=ReportFormat(report_def.get("format", "PDF")),
            frequency=ScheduleFrequency(report_def.get("frequency", "ONCE")),
            recipients=report_def.get("recipients", []),
            description=report_def.get("description", ""),
        )
        return self.report_scheduler.schedule(definition)

    def generate_report(self, report_name: str) -> ReportSnapshot:
        """Tạo báo cáo thủ công theo tên.

        Args:
            report_name: Tên của báo cáo cần tạo.

        Returns:
            Bản chụp báo cáo đã tạo.
        """
        return self.report_scheduler.generate(report_name)

    def get_dashboards(self) -> List[Dashboard]:
        """Lấy tất cả dashboard đã tạo.

        Returns:
            Danh sách dashboard.
        """
        return self.dashboard_builder.list_all()

    def get_report_history(self, report_name: str) -> List[ReportSnapshot]:
        """Lấy lịch sử báo cáo theo tên.

        Args:
            report_name: Tên của báo cáo.

        Returns:
            Danh sách bản chụp báo cáo theo thứ tự thời gian.
        """
        return self.report_scheduler.get_history(report_name)

    def list_models(self) -> List[AnalyticsModel]:
        """Lấy danh sách tất cả mô hình phân tích.

        Returns:
            Danh sách mô hình phân tích có sẵn.
        """
        return self.engine.list_models()
'''
        return {"src/analytics/analytics_service.py": code}

    def generate_router(self) -> Dict[str, str]:
        """Tạo FastAPI router cho các endpoint analytics, dashboard, và báo cáo."""
        code = '''\
"""Router analytics cho FastAPI — endpoint REST cho truy vấn, dashboard, và báo cáo.

Cung cấp API REST để:
- Liệt kê và truy vấn mô hình phân tích
- Quản lý dashboard BI (tạo, liệt kê)
- Xuất bản và xem lịch sử báo cáo
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

# Import AnalyticsService từ mô-đun service
# Trong thực tế, service sẽ được inject qua dependency injection của FastAPI
_analytics_service: Optional["AnalyticsService"] = None


def set_analytics_service(service: "AnalyticsService") -> None:
    """Đặt instance AnalyticsService toàn cục cho router.

    Args:
        service: Instance của AnalyticsService.
    """
    global _analytics_service
    _analytics_service = service


# Tạo router cho các endpoint analytics
router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/models")
def list_models() -> List[Dict[str, Any]]:
    """Liệt kê tất cả mô hình phân tích có sẵn.

    Returns:
        Danh sách mô hình phân tích dưới dạng dict.
    """
    service = _analytics_service
    if not service:
        return []

    models = service.list_models()
    return [
        {
            "name": m.name,
            "description": m.description,
            "available_filters": m.available_filters,
            "available_metrics": m.available_metrics,
            "created_at": m.created_at,
        }
        for m in models
    ]


@router.post("/query")
def query_analytics(model_name: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Truy vấn dữ liệu phân tích từ mô hình chỉ định.

    Args:
        model_name: Tên của mô hình phân tích.
        filters: Bộ lọc áp dụng cho truy vấn (tùy chọn).

    Returns:
        Kết quả truy vấn phân tích dưới dạng dict.
    """
    service = _analytics_service
    if not service:
        raise HTTPException(status_code=503, detail="Analytics service không được cấu hình")

    result = service.query_analytics(model_name, filters)
    return {
        "query_id": result.query_id,
        "model_name": result.model_name,
        "rows": result.rows,
        "total_count": result.total_count,
        "execution_time_ms": result.execution_time_ms,
        "queried_at": result.queried_at,
    }


@router.get("/dashboards")
def list_dashboards() -> List[Dict[str, Any]]:
    """Liệt kê tất cả dashboard BI đã tạo.

    Returns:
        Danh sách dashboard dưới dạng dict.
    """
    service = _analytics_service
    if not service:
        return []

    dashboards = service.get_dashboards()
    return [
        {
            "name": d.name,
            "description": d.description,
            "widgets": [
                {
                    "id": w.id,
                    "name": w.name,
                    "title": w.title,
                    "chart_type": w.chart_type.value,
                    "metric": w.metric,
                    "model_name": w.model_name,
                    "filters": w.filters,
                    "position_x": w.position_x,
                    "position_y": w.position_y,
                    "width": w.width,
                    "height": w.height,
                }
                for w in d.widgets
            ],
            "created_at": d.created_at,
            "updated_at": d.updated_at,
        }
        for d in dashboards
    ]


@router.post("/dashboards")
def create_dashboard(definition: Dict[str, Any]) -> Dict[str, Any]:
    """Tạo dashboard BI mới từ định nghĩa.

    Args:
        definition: Định nghĩa dashboard với tên, mô tả, và cấu hình widget.

    Returns:
        Dashboard mới được tạo dưới dạng dict.
    """
    service = _analytics_service
    if not service:
        raise HTTPException(status_code=503, detail="Analytics service không được cấu hình")

    dashboard = service.create_dashboard(definition)
    return {
        "name": dashboard.name,
        "description": dashboard.description,
        "widgets": [
            {
                "id": w.id,
                "name": w.name,
                "title": w.title,
                "chart_type": w.chart_type.value,
                "metric": w.metric,
                "model_name": w.model_name,
                "filters": w.filters,
                "position_x": w.position_x,
                "position_y": w.position_y,
                "width": w.width,
                "height": w.height,
            }
            for w in dashboard.widgets
        ],
        "created_at": dashboard.created_at,
        "updated_at": dashboard.updated_at,
    }


@router.get("/reports")
def list_reports() -> List[Dict[str, Any]]:
    """Liệt kê tất cả báo cáo đã lên lịch.

    Returns:
        Danh sách định nghĩa báo cáo dưới dạng dict.
    """
    service = _analytics_service
    if not service:
        return []

    definitions = service.report_scheduler.get_definitions()
    return [
        {
            "name": d.name,
            "model_name": d.model_name,
            "description": d.description,
            "format": d.format.value,
            "frequency": d.frequency.value,
            "recipients": d.recipients,
            "next_run": d.next_run,
            "created_at": d.created_at,
        }
        for d in definitions
    ]


@router.post("/reports/generate")
def generate_report(name: str) -> Dict[str, Any]:
    """Tạo báo cáo thủ công theo tên.

    Args:
        name: Tên của báo cáo cần tạo.

    Returns:
        Bản chụp báo cáo đã tạo dưới dạng dict.
    """
    service = _analytics_service
    if not service:
        raise HTTPException(status_code=503, detail="Analytics service không được cấu hình")

    snapshot = service.generate_report(name)
    return {
        "id": snapshot.id,
        "report_name": snapshot.report_name,
        "status": snapshot.status.value,
        "format": snapshot.format.value,
        "generated_at": snapshot.generated_at,
        "completed_at": snapshot.completed_at,
        "file_size_bytes": snapshot.file_size_bytes,
        "rows_count": snapshot.rows_count,
        "error_message": snapshot.error_message,
    }


@router.get("/reports/{name}/history")
def report_history(name: str) -> List[Dict[str, Any]]:
    """Lấy lịch sử báo cáo theo tên.

    Args:
        name: Tên của báo cáo.

    Returns:
        Danh sách bản chụp báo cáo theo thứ tự thời gian.
    """
    service = _analytics_service
    if not service:
        return []

    snapshots = service.get_report_history(name)
    return [
        {
            "id": s.id,
            "report_name": s.report_name,
            "status": s.status.value,
            "format": s.format.value,
            "generated_at": s.generated_at,
            "completed_at": s.completed_at,
            "file_size_bytes": s.file_size_bytes,
            "rows_count": s.rows_count,
            "error_message": s.error_message,
        }
        for s in snapshots
    ]
'''
        return {"src/analytics/analytics_router.py": code}
