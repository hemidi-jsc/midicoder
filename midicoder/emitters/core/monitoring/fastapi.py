from __future__ import annotations

from typing import Any, Dict


class FastAPIMonitoringEmitter:
    """Emitter cho các thành phần monitoring của FastAPI."""

    def __init__(self, collection: Any | None = None):
        self.collection = collection or {}

    def generate(self) -> Dict[str, str]:
        """Tạo tất cả các tệp monitoring cho FastAPI."""
        result: Dict[str, str] = {}
        result.update(self.generate_service())
        result.update(self.generate_router())
        return result

    def generate_service(self) -> Dict[str, str]:
        """Tạo MonitoringService — quản lý dashboard, cảnh báo, và SLI."""
        code = '''\
"""Dịch vụ monitoring cho FastAPI — dashboard, cảnh báo, và SLI."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AlertSeverity(str, Enum):
    """Các mức độ nghiêm trọng của cảnh báo."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"


class AlertStatus(str, Enum):
    """Trạng thái của cảnh báo."""
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    ACKNOWLEDGED = "ACKNOWLEDGED"


@dataclass
class AlertRule:
    """Quy tắc cảnh báo — định nghĩa điều kiện để kích hoạt cảnh báo."""
    name: str
    metric: str
    operator: str
    threshold: float
    severity: AlertSeverity
    message: str = ""
    evaluation_interval: int = 60  # giây

    def __post_init__(self) -> None:
        if not self.message:
            self.message = f"Cảnh báo: {self.metric} {self.operator} {self.threshold}"


@dataclass
class FiredAlert:
    """Cảnh báo đang được kích hoạt."""
    id: str
    rule_name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    current_value: float
    threshold: float
    fired_at: float
    acknowledged_at: Optional[float] = None
    resolved_at: Optional[float] = None

    def acknowledge(self) -> None:
        """Xác nhận cảnh báo."""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = time.time()

    def resolve(self) -> None:
        """Giải quyết cảnh báo."""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = time.time()


@dataclass
class Panel:
    """Một panel hiển thị metric trên dashboard."""
    name: str
    metric: str
    unit: str = ""
    type: str = "gauge"  # gauge, counter, histogram, timeseries
    thresholds: List[float] = field(default_factory=list)
    description: str = ""


@dataclass
class Dashboard:
    """Dashboard chứa nhiều panel để hiển thị metric."""
    name: str
    panels: List[Panel]
    description: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class SLIDefinition:
    """Định nghĩa chỉ số mức độ dịch vụ (SLI)."""
    name: str
    metric: str
    target: float  # mục tiêu (ví dụ: 99.9 cho tỷ lệ thành công)
    window: int = 3600  # cửa sổ đánh giá (giây)
    description: str = ""


@dataclass
class SLIStatus:
    """Trạng thái hiện tại của SLI."""
    name: str
    current_value: float
    target: float
    healthy: bool
    window_start: float
    window_end: float
    samples: int = 0


class DashboardManager:
    """Quản lý dashboard — tạo, lưu trữ, và truy vấn dashboard."""

    def __init__(self) -> None:
        self._dashboards: Dict[str, Dashboard] = {}

    def create(self, name: str, panels: List[Panel], description: str = "") -> Dashboard:
        """Tạo dashboard mới.

        Args:
            name: Tên duy nhất của dashboard.
            panels: Danh sách các panel hiển thị metric.
            description: Mô tả dashboard.

        Returns:
            Dashboard mới được tạo.
        """
        dashboard = Dashboard(name=name, panels=panels, description=description)
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

    def delete(self, name: str) -> bool:
        """Xóa dashboard theo tên.

        Args:
            name: Tên của dashboard cần xóa.

        Returns:
            True nếu xóa thành công, False nếu không tồn tại.
        """
        return self._dashboards.pop(name, None) is not None


class AlertEngine:
    """Động cơ cảnh báo — lưu trữ quy tắc và đánh giá điều kiện kích hoạt."""

    def __init__(self) -> None:
        self._rules: Dict[str, AlertRule] = {}
        self._fired_alerts: List[FiredAlert] = []

    def add_rule(self, rule: AlertRule) -> None:
        """Thêm quy tắc cảnh báo mới.

        Args:
            rule: Quy tắc cảnh báo cần thêm.
        """
        self._rules[rule.name] = rule

    def remove_rule(self, name: str) -> bool:
        """Xóa quy tắc cảnh báo theo tên.

        Args:
            name: Tên của quy tắc cần xóa.

        Returns:
            True nếu xóa thành công, False nếu không tồn tại.
        """
        return self._rules.pop(name, None) is not None

    def get_rules(self) -> List[AlertRule]:
        """Lấy tất cả quy tắc cảnh báo.

        Returns:
            Danh sách tất cả quy tắc.
        """
        return list(self._rules.values())

    def evaluate(self, metrics: Dict[str, float]) -> List[FiredAlert]:
        """Đánh giá tất cả quy tắc cảnh báo với metric hiện tại.

        Args:
            metrics: Bản đồ metric theo tên và giá trị hiện tại.

        Returns:
            Danh sách cảnh báo mới được kích hoạt.
        """
        new_alerts: List[FiredAlert] = []
        for rule in self._rules.values():
            value = metrics.get(rule.metric)
            if value is None:
                continue
            triggered = self._evaluate_condition(value, rule.operator, rule.threshold)
            if triggered:
                alert = FiredAlert(
                    id=str(uuid.uuid4()),
                    rule_name=rule.name,
                    severity=rule.severity,
                    status=AlertStatus.ACTIVE,
                    message=rule.message,
                    current_value=value,
                    threshold=rule.threshold,
                    fired_at=time.time(),
                )
                self._fired_alerts.append(alert)
                new_alerts.append(alert)
        return new_alerts

    def get_active_alerts(self) -> List[FiredAlert]:
        """Lấy tất cả cảnh báo đang kích hoạt.

        Returns:
            Danh sách cảnh báo có trạng thái ACTIVE hoặc ACKNOWLEDGED.
        """
        return [a for a in self._fired_alerts if a.status in (AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED)]

    def resolve_all(self) -> int:
        """Giải quyết tất cả cảnh báo đang kích hoạt.

        Returns:
            Số lượng cảnh báo đã được giải quyết.
        """
        count = 0
        for alert in self._fired_alerts:
            if alert.status in (AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED):
                alert.resolve()
                count += 1
        return count

    @staticmethod
    def _evaluate_condition(value: float, operator: str, threshold: float) -> bool:
        """Đánh giá điều kiện so sánh giữa giá trị và ngưỡng.

        Args:
            value: Giá trị metric hiện tại.
            operator: Toán tử so sánh (> < >= <= == !=).
            threshold: Ngưỡng so sánh.

        Returns:
            True nếu điều kiện được thỏa mãn.
        """
        ops = {
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
        }
        fn = ops.get(operator)
        if fn is None:
            return False
        return fn(value, threshold)


class SLIMonitor:
    """Giám sát SLI — theo dõi chỉ số mức độ dịch vụ."""

    def __init__(self) -> None:
        self._definitions: Dict[str, SLIDefinition] = {}
        self._samples: Dict[str, List[float]] = defaultdict(list)

    def add_definition(self, definition: SLIDefinition) -> None:
        """Thêm định nghĩa SLI mới.

        Args:
            definition: Định nghĩa SLI cần thêm.
        """
        self._definitions[definition.name] = definition

    def record_sample(self, name: str, value: float) -> None:
        """Ghi nhận mẫu metric cho SLI.

        Args:
            name: Tên của SLI.
            value: Giá trị mẫu metric.
        """
        self._samples[name].append(value)

    def check_all(self) -> List[SLIStatus]:
        """Kiểm tra tất cả SLI và trả về trạng thái hiện tại.

        Returns:
            Danh sách trạng thái SLI.
        """
        statuses: List[SLIStatus] = []
        now = time.time()
        for name, definition in self._definitions.items():
            samples = self._samples.get(name, [])
            window_start = now - definition.window
            # Lọc mẫu trong cửa sổ thời gian
            windowed = [s for s in samples if s >= window_start]
            if not windowed:
                current = 0.0
            else:
                current = sum(windowed) / len(windowed)
            statuses.append(SLIStatus(
                name=name,
                current_value=current,
                target=definition.target,
                healthy=current >= definition.target,
                window_start=window_start,
                window_end=now,
                samples=len(windowed),
            ))
        return statuses

    def get_definitions(self) -> List[SLIDefinition]:
        """Lấy tất cả định nghĩa SLI.

        Returns:
            Danh sách định nghĩa SLI.
        """
        return list(self._definitions.values())


class MonitoringService:
    """Dịch vụ chính cho monitoring — tích hợp dashboard, cảnh báo, và SLI.

    Cung cấp giao diện thống nhất để quản lý dashboard hiển thị,
    động cơ cảnh báo, và giám sát chỉ số mức độ dịch vụ trong ứng dụng FastAPI.
    """

    def __init__(self) -> None:
        """Khởi tạo MonitoringService với các thành phần con."""
        self.dashboard_manager = DashboardManager()
        self.alert_engine = AlertEngine()
        self.sli_monitor = SLIMonitor()

    def create_dashboard(self, name: str, panels: List[Panel], description: str = "") -> Dashboard:
        """Tạo dashboard mới với các panel hiển thị metric.

        Args:
            name: Tên duy nhất của dashboard.
            panels: Danh sách các panel hiển thị metric.
            description: Mô tả dashboard.

        Returns:
            Dashboard mới được tạo.
        """
        return self.dashboard_manager.create(name, panels, description)

    def get_dashboard(self, name: str) -> Optional[Dashboard]:
        """Lấy dashboard theo tên.

        Args:
            name: Tên của dashboard.

        Returns:
            Dashboard nếu tìm thấy, ngược lại None.
        """
        return self.dashboard_manager.get(name)

    def list_dashboards(self) -> List[Dashboard]:
        """Lấy tất cả dashboard đã tạo.

        Returns:
            Danh sách tất cả dashboard.
        """
        return self.dashboard_manager.list_all()

    def add_alert_rule(self, rule: AlertRule) -> None:
        """Thêm quy tắc cảnh báo mới.

        Args:
            rule: Quy tắc cảnh báo cần thêm.
        """
        self.alert_engine.add_rule(rule)

    def evaluate_alerts(self, metrics: Optional[Dict[str, float]] = None) -> List[FiredAlert]:
        """Đánh giá tất cả quy tắc cảnh báo với metric hiện tại.

        Args:
            metrics: Bản đồ metric theo tên và giá trị hiện tại (tùy chọn).

        Returns:
            Danh sách cảnh báo mới được kích hoạt.
        """
        return self.alert_engine.evaluate(metrics or {})

    def get_fired_alerts(self) -> List[FiredAlert]:
        """Lấy tất cả cảnh báo đang kích hoạt.

        Returns:
            Danh sách cảnh báo có trạng thái ACTIVE hoặc ACKNOWLEDGED.
        """
        return self.alert_engine.get_active_alerts()

    def check_slis(self) -> List[SLIStatus]:
        """Kiểm tra trạng thái của tất cả SLI.

        Returns:
            Danh sách trạng thái SLI hiện tại.
        """
        return self.sli_monitor.check_all()

    def get_sli_definitions(self) -> List[SLIDefinition]:
        """Lấy tất cả định nghĩa SLI.

        Returns:
            Danh sách định nghĩa SLI.
        """
        return self.sli_monitor.get_definitions()
'''
        return {"src/monitoring/monitoring_service.py": code}

    def generate_router(self) -> Dict[str, str]:
        """Tạo FastAPI router cho các endpoint monitoring."""
        code = '''\
"""Router monitoring cho FastAPI — endpoint REST cho dashboard, cảnh báo, SLI."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter

# Import MonitoringService từ mô-đun service
# Trong thực tế, service sẽ được inject qua dependency injection của FastAPI
_monitoring_service: Optional["MonitoringService"] = None


def set_monitoring_service(service: "MonitoringService") -> None:
    """Đặt instance MonitoringService toàn cục cho router.

    Args:
        service: Instance của MonitoringService.
    """
    global _monitoring_service
    _monitoring_service = service


# Tạo router cho các endpoint monitoring
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/dashboards")
def list_dashboards() -> List[Dict[str, Any]]:
    """Liệt kê tất cả dashboard.

    Returns:
        Danh sách dashboard dưới dạng dict.
    """
    service = _monitoring_service
    if not service:
        return []

    dashboards = service.list_dashboards()
    return [
        {
            "name": d.name,
            "description": d.description,
            "panels": [
                {
                    "name": p.name,
                    "metric": p.metric,
                    "unit": p.unit,
                    "type": p.type,
                    "description": p.description,
                }
                for p in d.panels
            ],
            "created_at": d.created_at,
            "updated_at": d.updated_at,
        }
        for d in dashboards
    ]


@router.get("/dashboards/{name}")
def get_dashboard(name: str) -> Optional[Dict[str, Any]]:
    """Lấy thông tin chi tiết của một dashboard.

    Args:
        name: Tên của dashboard.

    Returns:
        Thông tin dashboard dưới dạng dict, hoặc None nếu không tìm thấy.
    """
    service = _monitoring_service
    if not service:
        return None

    dashboard = service.get_dashboard(name)
    if not dashboard:
        return None

    return {
        "name": dashboard.name,
        "description": dashboard.description,
        "panels": [
            {
                "name": p.name,
                "metric": p.metric,
                "unit": p.unit,
                "type": p.type,
                "thresholds": p.thresholds,
                "description": p.description,
            }
            for p in dashboard.panels
        ],
        "created_at": dashboard.created_at,
        "updated_at": dashboard.updated_at,
    }


@router.post("/alerts")
def add_alert_rule(
    name: str,
    metric: str,
    operator: str,
    threshold: float,
    severity: str = "WARNING",
    message: str = "",
    evaluation_interval: int = 60,
) -> Dict[str, Any]:
    """Thêm quy tắc cảnh báo mới.

    Args:
        name: Tên duy nhất của quy tắc.
        metric: Tên metric cần giám sát.
        operator: Toán tử so sánh (> < >= <= == !=).
        threshold: Ngưỡng kích hoạt cảnh báo.
        severity: Mức độ nghiêm trọng.
        message: Thông điệp cảnh báo tùy chỉnh.
        evaluation_interval: Khoảng thời gian đánh giá (giây).

    Returns:
        Thông tin quy tắc đã thêm.
    """
    service = _monitoring_service
    if not service:
        return {"error": "Monitoring service không được cấu hình"}

    from monitoring.monitoring_service import AlertRule, AlertSeverity

    rule = AlertRule(
        name=name,
        metric=metric,
        operator=operator,
        threshold=threshold,
        severity=AlertSeverity(severity),
        message=message,
        evaluation_interval=evaluation_interval,
    )
    service.add_alert_rule(rule)

    return {
        "name": rule.name,
        "metric": rule.metric,
        "operator": rule.operator,
        "threshold": rule.threshold,
        "severity": rule.severity.value,
        "message": rule.message,
        "evaluation_interval": rule.evaluation_interval,
    }


@router.get("/alerts")
def get_fired_alerts() -> List[Dict[str, Any]]:
    """Lấy tất cả cảnh báo đang kích hoạt.

    Returns:
        Danh sách cảnh báo đang kích hoạt dưới dạng dict.
    """
    service = _monitoring_service
    if not service:
        return []

    alerts = service.get_fired_alerts()
    return [
        {
            "id": a.id,
            "rule_name": a.rule_name,
            "severity": a.severity.value,
            "status": a.status.value,
            "message": a.message,
            "current_value": a.current_value,
            "threshold": a.threshold,
            "fired_at": a.fired_at,
            "acknowledged_at": a.acknowledged_at,
            "resolved_at": a.resolved_at,
        }
        for a in alerts
    ]


@router.get("/slis")
def get_sli_status() -> List[Dict[str, Any]]:
    """Lấy trạng thái hiện tại của tất cả SLI.

    Returns:
        Danh sách trạng thái SLI dưới dạng dict.
    """
    service = _monitoring_service
    if not service:
        return []

    statuses = service.check_slis()
    return [
        {
            "name": s.name,
            "current_value": s.current_value,
            "target": s.target,
            "healthy": s.healthy,
            "window_start": s.window_start,
            "window_end": s.window_end,
            "samples": s.samples,
        }
        for s in statuses
    ]


@router.post("/alerts/evaluate")
def evaluate_alerts(metrics: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """Đánh giá tất cả quy tắc cảnh báo với metric hiện tại.

    Args:
        metrics: Bản đồ metric theo tên và giá trị hiện tại (tùy chọn).

    Returns:
        Kết quả đánh giá với danh sách cảnh báo mới được kích hoạt.
    """
    service = _monitoring_service
    if not service:
        return {"error": "Monitoring service không được cấu hình"}

    new_alerts = service.evaluate_alerts(metrics)
    return {
        "evaluated_at": __import__("time").time(),
        "new_alerts_count": len(new_alerts),
        "new_alerts": [
            {
                "id": a.id,
                "rule_name": a.rule_name,
                "severity": a.severity.value,
                "message": a.message,
                "current_value": a.current_value,
                "threshold": a.threshold,
            }
            for a in new_alerts
        ],
    }
'''
        return {"src/monitoring/monitoring_router.py": code}
