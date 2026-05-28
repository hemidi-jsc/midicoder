# coding: utf-8
"""
Mô-đun models cho CP59 — Tenant Billing & Invoicing.

Định nghĩa các dataclass biểu diễn:
- BillingPlan: Kế hoạch thanh toán (free, starter, professional, enterprise)
- BillingCycle: Chu kỳ thanh toán (tháng, quý, năm)
- InvoiceConfig: Cấu hình hóa đơn (draft, sent, paid, overdue, void)
- UsageMeter: Đo lường sử dụng (api_calls, storage_gb, users, bandwidth_gb)
- PaymentGatewayConfig: Cấu hình payment gateway (Stripe, PayPal, Adyen)

KPI-005: CP Obligations Coverage (>= 2 obligations cho CP59).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class PlanTier(str, Enum):
    """Loại tier của billing plan.

    - FREE: Kế hoạch miễn phí, giới hạn cơ bản
    - STARTER: Kế hoạch khởi đầu, phù hợp team nhỏ
    - PROFESSIONAL: Kế hoạch chuyên nghiệp, cho team/công ty vừa
    - ENTERPRISE: Kế hoạch doanh nghiệp, không giới hạn
    """
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class CycleType(str, Enum):
    """Loại chu kỳ thanh toán.

    - MONTHLY: Thanh toán hàng tháng
    - QUARTERLY: Thanh toán hàng quý (3 tháng)
    - ANNUAL: Thanh toán hàng năm (12 tháng)
    """
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class InvoiceStatus(str, Enum):
    """Trạng thái hóa đơn.

    State machine: draft → sent → paid | overdue → void

    - DRAFT: Hóa đơn nháp, chưa gửi
    - SENT: Đã gửi cho khách hàng
    - PAID: Đã thanh toán
    - OVERDUE: Quá hạn thanh toán
    - VOID: Đã hủy/hook
    """
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"


class MetricName(str, Enum):
    """Tên metric cho usage metering.

    - API_CALLS: Số lần gọi API
    - STORAGE_GB: Dung lượng lưu trữ (GB)
    - USERS: Số người dùng
    - BANDWIDTH_GB: Băng thông (GB)
    """
    API_CALLS = "api_calls"
    STORAGE_GB = "storage_gb"
    USERS = "users"
    BANDWIDTH_GB = "bandwidth_gb"


class GatewayProvider(str, Enum):
    """Nhà cung cấp payment gateway.

    - STRIPE: Stripe Payment Gateway
    - PAYPAL: PayPal Payment Gateway
    - ADYEN: Adyen Payment Gateway
    """
    STRIPE = "stripe"
    PAYPAL = "paypal"
    ADYEN = "adyen"


class CaptureMode(str, Enum):
    """Chế độ thu tiền.

    - AUTOMATIC: Tự động thu tiền khi đến hạn
    - MANUAL: Thu tiền thủ công theo yêu cầu
    """
    AUTOMATIC = "automatic"
    MANUAL = "manual"


# ===========================================================================
# BillingPlan
# ===========================================================================


@dataclass
class BillingPlan:
    """Kế hoạch thanh toán (billing plan).

    Định nghĩa một plan với tier, giá cả, tính năng, và giới hạn sử dụng.

    Attributes:
        id: ID duy nhất của plan
        name: Tên hiển thị của plan
        tier: Loại tier (free, starter, professional, enterprise)
        monthly_price: Giá hàng tháng (đơn vị: cents/smallest currency unit)
        annual_price: Giá hàng năm (đơn vị: cents/smallest currency unit)
        features: Danh sách tính năng của plan
        usage_limits: Giới hạn sử dụng theo metric
        created_at: Thời điểm tạo plan
        updated_at: Thời điểm cập nhật cuối
    """
    id: str
    name: str
    tier: PlanTier
    monthly_price: int = 0
    annual_price: int = 0
    features: list[str] = field(default_factory=list)
    usage_limits: dict[str, int] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate billing plan sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F34_BILLING_PLAN_NOT_FOUND,
                reason="plan_id bắt buộc và không được để trống",
            )

        if self.monthly_price < 0:
            raise EM.raise_error(
                ErrorCode.MDC-F34_INVALID_BILLING_AMOUNT,
                reason=f"monthly_price phải >= 0, nhận được: {self.monthly_price}",
            )

        if self.annual_price < 0:
            raise EM.raise_error(
                ErrorCode.MDC-F34_INVALID_BILLING_AMOUNT,
                reason=f"annual_price phải >= 0, nhận được: {self.annual_price}",
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    @property
    def annual_savings_percentage(self) -> float:
        """Trả về phần trăm tiết kiệm khi chọn năm so với tháng.

        Returns:
            Phần trăm tiết kiệm (0.0 - 100.0)
        """
        if self.monthly_price == 0:
            return 0.0
        monthly_total = self.monthly_price * 12
        if monthly_total == 0:
            return 0.0
        return round((1 - self.annual_price / monthly_total) * 100, 2)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển BillingPlan sang dict."""
        return {
            "id": self.id,
            "name": self.name,
            "tier": self.tier.value,
            "monthly_price": self.monthly_price,
            "annual_price": self.annual_price,
            "features": self.features,
            "usage_limits": self.usage_limits,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BillingPlan":
        """Tạo BillingPlan từ dict."""
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            tier=PlanTier(data.get("tier", "free")),
            monthly_price=data.get("monthly_price", 0),
            annual_price=data.get("annual_price", 0),
            features=data.get("features", []),
            usage_limits=data.get("usage_limits", {}),
        )


# ===========================================================================
# BillingCycle
# ===========================================================================


@dataclass
class BillingCycle:
    """Chu kỳ thanh toán (billing cycle).

    Xác định khoảng thời gian thanh toán với ngày bắt đầu, kết thúc,
    và chế độ gia hạn tự động.

    Attributes:
        id: ID duy nhất của billing cycle
        type: Loại chu kỳ (monthly, quarterly, annual)
        start_date: Ngày bắt đầu chu kỳ
        end_date: Ngày kết thúc chu kỳ
        auto_renew: Có gia hạn tự động không
        metadata: Dữ liệu bổ sung
    """
    id: str
    type: CycleType
    start_date: datetime
    end_date: datetime
    auto_renew: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate billing cycle sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F34_BILLING_CYCLE_NOT_FOUND,
                reason="cycle_id bắt buộc và không được để trống",
            )

        if self.end_date <= self.start_date:
            raise EM.raise_error(
                ErrorCode.MDC-F34_INVALID_BILLING_CYCLE,
                reason=f"end_date phải sau start_date, nhận được: start={self.start_date}, end={self.end_date}",
            )

    @property
    def is_active(self) -> bool:
        """Trả về True nếu chu kỳ đang hoạt động."""
        now = datetime.now(timezone.utc)
        return self.start_date <= now <= self.end_date

    @property
    def is_expired(self) -> bool:
        """Trả về True nếu chu kỳ đã hết hạn."""
        return datetime.now(timezone.utc) > self.end_date

    def to_dict(self) -> dict[str, Any]:
        """Chuyển BillingCycle sang dict."""
        return {
            "id": self.id,
            "type": self.type.value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "auto_renew": self.auto_renew,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BillingCycle":
        """Tạo BillingCycle từ dict."""
        start = data.get("start_date")
        end = data.get("end_date")
        return cls(
            id=data["id"],
            type=CycleType(data.get("type", "monthly")),
            start_date=datetime.fromisoformat(start) if isinstance(start, str) else (start or datetime.now(timezone.utc)),
            end_date=datetime.fromisoformat(end) if isinstance(end, str) else (end or datetime.now(timezone.utc)),
            auto_renew=data.get("auto_renew", True),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# InvoiceConfig
# ===========================================================================


@dataclass
class InvoiceConfig:
    """Cấu hình hóa đơn (invoice).

    Đại diện cho một hóa đơn với thông tin tenant, plan, số tiền,
    currency, trạng thái, và các dòng chi tiết.

    Attributes:
        id: ID duy nhất của hóa đơn
        tenant_id: ID tenant được xuất hóa đơn
        plan_id: ID billing plan liên kết
        amount: Tổng số tiền (đơn vị: cents/smallest currency unit)
        currency: Mã currency ISO 4217 (vd: "VND", "USD")
        status: Trạng thái hóa đơn
        due_date: Ngày đến hạn thanh toán
        line_items: Danh sách các dòng chi tiết
        metadata: Dữ liệu bổ sung
        created_at: Thời điểm tạo hóa đơn
        paid_at: Thời điểm thanh toán
    """
    id: str
    tenant_id: str
    plan_id: str
    amount: int
    currency: str = "USD"
    status: InvoiceStatus = InvoiceStatus.DRAFT
    due_date: datetime | None = None
    line_items: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    paid_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate invoice config sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F34_INVOICE_NOT_FOUND,
                reason="invoice_id bắt buộc và không được để trống",
            )

        if not self.tenant_id or not self.tenant_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F34_INVOICE_NOT_FOUND,
                reason="tenant_id bắt buộc và không được để trống",
            )

        if self.amount < 0:
            raise EM.raise_error(
                ErrorCode.MDC-F34_INVALID_BILLING_AMOUNT,
                reason=f"amount phải >= 0, nhận được: {self.amount}",
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now

    @property
    def amount_decimal(self) -> float:
        """Trả về số tiền dưới dạng decimal (chia cho 100)."""
        return self.amount / 100

    @property
    def is_overdue(self) -> bool:
        """Trả về True nếu hóa đơn quá hạn."""
        if self.due_date is None:
            return False
        return datetime.now(timezone.utc) > self.due_date and self.status != InvoiceStatus.PAID

    @property
    def can_void(self) -> bool:
        """Trả về True nếu hóa đơn có thể hủy."""
        return self.status in (InvoiceStatus.DRAFT, InvoiceStatus.SENT)

    @property
    def can_send(self) -> bool:
        """Trả về True nếu hóa đơn có thể gửi."""
        return self.status == InvoiceStatus.DRAFT

    def to_dict(self) -> dict[str, Any]:
        """Chuyển InvoiceConfig sang dict."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "plan_id": self.plan_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "line_items": self.line_items,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InvoiceConfig":
        """Tạo InvoiceConfig từ dict."""
        due = data.get("due_date")
        return cls(
            id=data["id"],
            tenant_id=data.get("tenant_id", ""),
            plan_id=data.get("plan_id", ""),
            amount=data.get("amount", 0),
            currency=data.get("currency", "USD"),
            status=InvoiceStatus(data.get("status", "draft")),
            due_date=datetime.fromisoformat(due) if isinstance(due, str) else due,
            line_items=data.get("line_items", []),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# UsageMeter
# ===========================================================================


@dataclass
class UsageMeter:
    """Thiết bị đo lường sử dụng (usage meter).

    Theo dõi lượng sử dụng của một metric cụ thể (API calls, storage,
    số người dùng, băng thông) với giá đơn vị và ngưỡng cảnh báo.

    Attributes:
        id: ID duy nhất của usage meter
        metric_name: Tên metric (api_calls, storage_gb, users, bandwidth_gb)
        unit_price: Giá đơn vị tính (đơn vị: cents per unit)
        billing_period: Kỳ tính phí (monthly, quarterly, annual)
        threshold_alerts: Danh sách ngưỡng cảnh báo (%)
        metadata: Dữ liệu bổ sung
    """
    id: str
    metric_name: MetricName
    unit_price: int = 0
    billing_period: str = "monthly"
    threshold_alerts: list[int] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate usage meter sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F34_USAGE_METER_NOT_FOUND,
                reason="meter_id bắt buộc và không được để trống",
            )

        if self.unit_price < 0:
            raise EM.raise_error(
                ErrorCode.MDC-F34_INVALID_BILLING_AMOUNT,
                reason=f"unit_price phải >= 0, nhận được: {self.unit_price}",
            )

    def calculate_cost(self, usage_amount: int) -> int:
        """Tính chi phí dựa trên lượng sử dụng.

        Args:
            usage_amount: Lượng sử dụng

        Returns:
            Tổng chi phí (đơn vị: cents)
        """
        return usage_amount * self.unit_price

    def get_alert_level(self, current_usage: int, limit: int) -> str | None:
        """Xác định mức cảnh báo dựa trên phần trăm sử dụng.

        Args:
            current_usage: Lượng sử dụng hiện tại
            limit: Giới hạn tối đa

        Returns:
            Mức cảnh báo hoặc None nếu chưa đạt ngưỡng
        """
        if limit == 0:
            return None
        percentage = (current_usage / limit) * 100
        alerts_sorted = sorted(self.threshold_alerts, reverse=True)
        for threshold in alerts_sorted:
            if percentage >= threshold:
                return f"{threshold}%"
        return None

    def to_dict(self) -> dict[str, Any]:
        """Chuyển UsageMeter sang dict."""
        return {
            "id": self.id,
            "metric_name": self.metric_name.value,
            "unit_price": self.unit_price,
            "billing_period": self.billing_period,
            "threshold_alerts": self.threshold_alerts,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UsageMeter":
        """Tạo UsageMeter từ dict."""
        return cls(
            id=data["id"],
            metric_name=MetricName(data.get("metric_name", "api_calls")),
            unit_price=data.get("unit_price", 0),
            billing_period=data.get("billing_period", "monthly"),
            threshold_alerts=data.get("threshold_alerts", []),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# PaymentGatewayConfig
# ===========================================================================


@dataclass
class PaymentGatewayConfig:
    """Cấu hình payment gateway.

    Chứa thông tin cấu hình để tích hợp với payment gateway provider,
    bao gồm API key reference, webhook secret, và chế độ thu tiền.

    Attributes:
        id: ID duy nhất của gateway config
        provider: Nhà cung cấp gateway (stripe, paypal, adyen)
        api_key_ref: Reference đến API key (lưu trữ an toàn)
        webhook_secret: Secret để verify webhook signature
        currencies: Danh sách currency được hỗ trợ
        capture_mode: Chế độ thu tiền (automatic, manual)
        is_enabled: Có bật gateway này không
        is_sandbox: Có đang dùng sandbox không
        metadata: Dữ liệu bổ sung
    """
    id: str
    provider: GatewayProvider
    api_key_ref: str = ""
    webhook_secret: str = ""
    currencies: list[str] = field(default_factory=list)
    capture_mode: CaptureMode = CaptureMode.AUTOMATIC
    is_enabled: bool = True
    is_sandbox: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate gateway config sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F34_PAYMENT_GATEWAY_NOT_FOUND,
                reason="gateway_id bắt buộc và không được để trống",
            )

        if not self.currencies:
            self.currencies = ["USD"]

    @property
    def masked_api_key_ref(self) -> str:
        """Trả về API key reference đã mask."""
        if len(self.api_key_ref) <= 4:
            return "****"
        return f"****{self.api_key_ref[-4:]}"

    def to_dict(self) -> dict[str, Any]:
        """Chuyển PaymentGatewayConfig sang dict."""
        return {
            "id": self.id,
            "provider": self.provider.value,
            "api_key_ref": self.masked_api_key_ref,
            "webhook_secret": "****",
            "currencies": self.currencies,
            "capture_mode": self.capture_mode.value,
            "is_enabled": self.is_enabled,
            "is_sandbox": self.is_sandbox,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PaymentGatewayConfig":
        """Tạo PaymentGatewayConfig từ dict."""
        return cls(
            id=data["id"],
            provider=GatewayProvider(data.get("provider", "stripe")),
            api_key_ref=data.get("api_key_ref", ""),
            webhook_secret=data.get("webhook_secret", ""),
            currencies=data.get("currencies", ["USD"]),
            capture_mode=CaptureMode(data.get("capture_mode", "automatic")),
            is_enabled=data.get("is_enabled", True),
            is_sandbox=data.get("is_sandbox", True),
            metadata=data.get("metadata", {}),
        )
