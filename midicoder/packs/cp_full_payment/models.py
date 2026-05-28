# coding: utf-8
"""
Mô-đun models cho CP45 — Payment Gateway Abstraction.

Định nghĩa các dataclass biểu diễn:
- PaymentGatewayType: Loại payment gateway provider (Stripe, VNPay, MoMo)
- PaymentMethodType: Loại phương thức thanh toán (credit_card, bank_transfer, ewallet, qr_code)
- PaymentMethodStatus: Trạng thái payment method (active, expired, suspended)
- PaymentStatus: Trạng thái giao dịch (pending → processing → completed | failed | refunded | cancelled)
- RefundStatus: Trạng thái hoàn tiền (pending → processing → completed | failed)
- PaymentGatewayConfig: Cấu hình payment gateway provider
- PaymentMethod: Phương thức thanh toán của user
- PaymentTransaction: Giao dịch thanh toán
- PaymentRefund: Yêu cầu hoàn tiền
- PaymentEngine: Engine xử lý payment operations (in-memory simulation)

KPI-005: CP Obligations Coverage (>= 2 obligations cho CP45).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class PaymentGatewayType(str, Enum):
    """Loại payment gateway provider.

    - STRIPE: Stripe Payment Gateway
    - VNPAY: VNPay Payment Gateway (Vietnam)
    - MOMO: MoMo E-Wallet Gateway (Vietnam)
    """
    STRIPE = "stripe"
    VNPay = "vnpay"
    MOMO = "momo"


class PaymentMethodType(str, Enum):
    """Loại phương thức thanh toán.

    - CREDIT_CARD: Thẻ tín dụng/ghi nợ
    - BANK_TRANSFER: Chuyển khoản ngân hàng
    - EWALLET: Ví điện tử
    - QR_CODE: Thanh toán qua mã QR
    """
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    EWALLET = "ewallet"
    QR_CODE = "qr_code"


class PaymentMethodStatus(str, Enum):
    """Trạng thái payment method.

    - ACTIVE: Đang hoạt động
    - EXPIRED: Hết hạn
    - SUSPENDED: Bị tạm ngưng
    """
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class PaymentStatus(str, Enum):
    """Trạng thái giao dịch thanh toán.

    State machine: pending → processing → completed | failed | refunded | cancelled

    - PENDING: Đang chờ xử lý
    - PROCESSING: Đang xử lý
    - COMPLETED: Thành công
    - FAILED: Thất bại
    - REFUNDED: Đã hoàn tiền
    - CANCELLED: Đã hủy
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class RefundStatus(str, Enum):
    """Trạng thái yêu cầu hoàn tiền.

    State machine: pending → processing → completed | failed

    - PENDING: Đang chờ xử lý
    - PROCESSING: Đang xử lý
    - COMPLETED: Đã hoàn tiền thành công
    - FAILED: Thất bại
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ===========================================================================
# PaymentGatewayConfig
# ===========================================================================


@dataclass
class PaymentGatewayConfig:
    """Cấu hình payment gateway provider.

    Chứa thông tin cấu hình cho một payment gateway cụ thể, bao gồm
    loại provider, API keys (masked), endpoint URLs, và timeout settings.

    Attributes:
        config_id: ID duy nhất của cấu hình
        gateway_type: Loại gateway provider
        api_key: API key (masked, chỉ hiện 4 ký tự cuối)
        api_secret: API secret (masked)
        webhook_secret: Secret để verify webhook signature
        endpoint_url: URL endpoint của gateway
        webhook_url: URL nhận webhook callback
        timeout_seconds: Thời gian chờ giao dịch (mặc định: 30)
        is_sandbox: Có đang dùng sandbox không
        is_enabled: Có bật gateway này không
        metadata: Dữ liệu bổ sung
    """
    config_id: str
    gateway_type: PaymentGatewayType
    api_key: str = ""
    api_secret: str = ""
    webhook_secret: str = ""
    endpoint_url: str = ""
    webhook_url: str = ""
    timeout_seconds: int = 30
    is_sandbox: bool = True
    is_enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate config sau khi khởi tạo."""
        if not self.config_id or not self.config_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F26_PAYMENT_GATEWAY_NOT_FOUND,
                reason="config_id bắt buộc và không được để trống",
            )

        if self.timeout_seconds < 1:
            raise EM.raise_error(
                ErrorCode.MDC-F26_INVALID_PAYMENT_AMOUNT,
                reason=f"timeout_seconds phải lớn hơn 0, nhận được: {self.timeout_seconds}",
            )

    @property
    def masked_api_key(self) -> str:
        """Trả về API key đã mask (chỉ hiện 4 ký tự cuối)."""
        if len(self.api_key) <= 4:
            return "****"
        return f"****{self.api_key[-4:]}"

    def to_dict(self) -> dict[str, Any]:
        """Chuyển PaymentGatewayConfig sang dict."""
        return {
            "config_id": self.config_id,
            "gateway_type": self.gateway_type.value,
            "api_key": self.masked_api_key,
            "api_secret": "****",
            "webhook_secret": "****",
            "endpoint_url": self.endpoint_url,
            "webhook_url": self.webhook_url,
            "timeout_seconds": self.timeout_seconds,
            "is_sandbox": self.is_sandbox,
            "is_enabled": self.is_enabled,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PaymentGatewayConfig":
        """Tạo PaymentGatewayConfig từ dict."""
        return cls(
            config_id=data["config_id"],
            gateway_type=PaymentGatewayType(data.get("gateway_type", "stripe")),
            api_key=data.get("api_key", ""),
            api_secret=data.get("api_secret", ""),
            webhook_secret=data.get("webhook_secret", ""),
            endpoint_url=data.get("endpoint_url", ""),
            webhook_url=data.get("webhook_url", ""),
            timeout_seconds=data.get("timeout_seconds", 30),
            is_sandbox=data.get("is_sandbox", True),
            is_enabled=data.get("is_enabled", True),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# PaymentMethod
# ===========================================================================


@dataclass
class PaymentMethod:
    """Phương thức thanh toán của user.

    Đại diện cho một phương thức thanh toán được lưu trữ, bao gồm
    loại thẻ/tài khoản, thông tin masked (PCI-DSS compliant),
    và trạng thái.

    Attributes:
        method_id: ID duy nhất của payment method
        user_id: ID user sở hữu
        method_type: Loại phương thức thanh toán
        gateway_type: Gateway provider liên kết
        display_name: Tên hiển thị (vd: "Visa •••• 4242")
        last4: 4 ký tự cuối của số thẻ/tài khoản
        token: Token từ gateway (an toàn hơn lưu raw data)
        status: Trạng thái hiện tại
        is_default: Có là phương thức mặc định không
        expiry_month: Tháng hết hạn (nếu có)
        expiry_year: Năm hết hạn (nếu có)
        tenant_id: ID tenant
        metadata: Dữ liệu bổ sung
        created_at: Thời điểm tạo
        updated_at: Thời điểm cập nhật cuối
    """
    method_id: str
    user_id: str
    method_type: PaymentMethodType
    gateway_type: PaymentGatewayType = PaymentGatewayType.STRIPE
    display_name: str = ""
    last4: str = ""
    token: str = ""
    status: PaymentMethodStatus = PaymentMethodStatus.ACTIVE
    is_default: bool = False
    expiry_month: int | None = None
    expiry_year: int | None = None
    tenant_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate payment method sau khi khởi tạo."""
        if not self.method_id or not self.method_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F26_PAYMENT_METHOD_NOT_FOUND,
                reason="method_id bắt buộc và không được để trống",
            )

        if not self.user_id or not self.user_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F26_PAYMENT_METHOD_NOT_FOUND,
                reason="user_id bắt buộc và không được để trống",
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    @property
    def is_usable(self) -> bool:
        """Trả về True nếu payment method có thể sử dụng."""
        return self.status == PaymentMethodStatus.ACTIVE

    def to_dict(self) -> dict[str, Any]:
        """Chuyển PaymentMethod sang dict."""
        return {
            "method_id": self.method_id,
            "user_id": self.user_id,
            "method_type": self.method_type.value,
            "gateway_type": self.gateway_type.value,
            "display_name": self.display_name,
            "last4": self.last4,
            "token": self.token,
            "status": self.status.value,
            "is_default": self.is_default,
            "expiry_month": self.expiry_month,
            "expiry_year": self.expiry_year,
            "tenant_id": self.tenant_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PaymentMethod":
        """Tạo PaymentMethod từ dict."""
        return cls(
            method_id=data["method_id"],
            user_id=data["user_id"],
            method_type=PaymentMethodType(data.get("method_type", "credit_card")),
            gateway_type=PaymentGatewayType(data.get("gateway_type", "stripe")),
            display_name=data.get("display_name", ""),
            last4=data.get("last4", ""),
            token=data.get("token", ""),
            status=PaymentMethodStatus(data.get("status", "active")),
            is_default=data.get("is_default", False),
            expiry_month=data.get("expiry_month"),
            expiry_year=data.get("expiry_year"),
            tenant_id=data.get("tenant_id", ""),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# PaymentTransaction
# ===========================================================================


@dataclass
class PaymentTransaction:
    """Giao dịch thanh toán.

    Đại diện cho một giao dịch thanh toán, bao gồm thông tin về
    người dùng, số tiền, currency, gateway, idempotency key,
    và trạng thái.

    State machine: pending → processing → completed | failed | refunded | cancelled

    Attributes:
        transaction_id: ID duy nhất của giao dịch
        user_id: ID user thực hiện giao dịch
        payment_method_id: ID payment method được sử dụng
        amount: Số tiền (đơn vị: smallest currency unit, vd: cents)
        currency: Mã currency ISO 4217 (vd: "VND", "USD")
        gateway_type: Gateway provider xử lý
        gateway_provider_ref: Reference ID từ gateway provider
        status: Trạng thái hiện tại
        idempotency_key: Key để deduplicate request
        description: Mô tả giao dịch
        metadata: Dữ liệu bổ sung
        created_at: Thời điểm tạo giao dịch
        updated_at: Thời điểm cập nhật cuối
        completed_at: Thời điểm hoàn thành
    """
    transaction_id: str
    user_id: str
    payment_method_id: str
    amount: int
    currency: str = "VND"
    gateway_type: PaymentGatewayType = PaymentGatewayType.STRIPE
    gateway_provider_ref: str = ""
    status: PaymentStatus = PaymentStatus.PENDING
    idempotency_key: str = ""
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate transaction sau khi khởi tạo."""
        if not self.transaction_id or not self.transaction_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F26_PAYMENT_PROCESSING_FAILED,
                reason="transaction_id bắt buộc và không được để trống",
            )

        if self.amount < 0:
            raise EM.raise_error(
                ErrorCode.MDC-F26_INVALID_PAYMENT_AMOUNT,
                reason=f"amount phải lớn hơn hoặc bằng 0, nhận được: {self.amount}",
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    @property
    def amount_decimal(self) -> float:
        """Trả về số tiền dưới dạng decimal (chia cho 100)."""
        return self.amount / 100

    @property
    def can_refund(self) -> bool:
        """Trả về True nếu giao dịch có thể hoàn tiền."""
        return self.status in (PaymentStatus.COMPLETED, PaymentStatus.PROCESSING)

    @property
    def can_cancel(self) -> bool:
        """Trả về True nếu giao dịch có thể hủy."""
        return self.status in (PaymentStatus.PENDING, PaymentStatus.PROCESSING)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển PaymentTransaction sang dict."""
        return {
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "payment_method_id": self.payment_method_id,
            "amount": self.amount,
            "currency": self.currency,
            "gateway_type": self.gateway_type.value,
            "gateway_provider_ref": self.gateway_provider_ref,
            "status": self.status.value,
            "idempotency_key": self.idempotency_key,
            "description": self.description,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PaymentTransaction":
        """Tạo PaymentTransaction từ dict."""
        return cls(
            transaction_id=data["transaction_id"],
            user_id=data["user_id"],
            payment_method_id=data.get("payment_method_id", ""),
            amount=data.get("amount", 0),
            currency=data.get("currency", "VND"),
            gateway_type=PaymentGatewayType(data.get("gateway_type", "stripe")),
            gateway_provider_ref=data.get("gateway_provider_ref", ""),
            status=PaymentStatus(data.get("status", "pending")),
            idempotency_key=data.get("idempotency_key", ""),
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# PaymentRefund
# ===========================================================================


@dataclass
class PaymentRefund:
    """Yêu cầu hoàn tiền.

    Đại diện cho một yêu cầu hoàn tiền cho giao dịch đã thành công,
    bao gồm số tiền hoàn, lý do, và trạng thái.

    State machine: pending → processing → completed | failed

    Attributes:
        refund_id: ID duy nhất của yêu cầu hoàn tiền
        transaction_id: ID giao dịch gốc
        user_id: ID user yêu cầu hoàn tiền
        amount: Số tiền hoàn (<= amount của transaction gốc)
        currency: Mã currency
        reason: Lý do hoàn tiền
        status: Trạng thái hiện tại
        gateway_refund_ref: Reference ID từ gateway
        metadata: Dữ liệu bổ sung
        created_at: Thời điểm tạo yêu cầu
        completed_at: Thời điểm hoàn thành
    """
    refund_id: str
    transaction_id: str
    user_id: str
    amount: int
    currency: str = "VND"
    reason: str = ""
    status: RefundStatus = RefundStatus.PENDING
    gateway_refund_ref: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate refund sau khi khởi tạo."""
        if not self.refund_id or not self.refund_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F26_REFUND_NOT_ALLOWED,
                reason="refund_id bắt buộc và không được để trống",
            )

        if not self.transaction_id or not self.transaction_id.strip():
            raise EM.raise_error(
                ErrorCode.MDC-F26_REFUND_NOT_ALLOWED,
                reason="transaction_id bắt buộc và không được để trống",
            )

        if self.amount < 0:
            raise EM.raise_error(
                ErrorCode.MDC-F26_INVALID_PAYMENT_AMOUNT,
                reason=f"refund amount phải lớn hơn hoặc bằng 0, nhận được: {self.amount}",
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now

    @property
    def amount_decimal(self) -> float:
        """Trả về số tiền hoàn dưới dạng decimal."""
        return self.amount / 100

    def to_dict(self) -> dict[str, Any]:
        """Chuyển PaymentRefund sang dict."""
        return {
            "refund_id": self.refund_id,
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "currency": self.currency,
            "reason": self.reason,
            "status": self.status.value,
            "gateway_refund_ref": self.gateway_refund_ref,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PaymentRefund":
        """Tạo PaymentRefund từ dict."""
        return cls(
            refund_id=data["refund_id"],
            transaction_id=data["transaction_id"],
            user_id=data["user_id"],
            amount=data.get("amount", 0),
            currency=data.get("currency", "VND"),
            reason=data.get("reason", ""),
            status=RefundStatus(data.get("status", "pending")),
            gateway_refund_ref=data.get("gateway_refund_ref", ""),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# PaymentEngine
# ===========================================================================


class PaymentEngine:
    """Engine xử lý payment operations (in-memory simulation).

    Quản lý toàn bộ vòng đời của payment: lưu payment methods,
    tạo giao dịch, xử lý thanh toán, hoàn tiền, và quản lý idempotency.

    Đây là in-memory simulation để testing và demonstration.
    Trong thực tế, engine sẽ tích hợp với database và payment gateway APIs.

    Attributes:
        gateways: Từ điển cấu hình gateways (config_id -> PaymentGatewayConfig)
        methods: Từ điển payment methods (method_id -> PaymentMethod)
        transactions: Từ điển transactions (transaction_id -> PaymentTransaction)
        refunds: Từ điển refunds (refund_id -> PaymentRefund)
        idempotency_keys: Từ điển idempotency keys (key -> transaction_id)
    """

    def __init__(self) -> None:
        """Khởi tạo PaymentEngine."""
        self.gateways: dict[str, PaymentGatewayConfig] = {}
        self.methods: dict[str, PaymentMethod] = {}
        self.transactions: dict[str, PaymentTransaction] = {}
        self.refunds: dict[str, PaymentRefund] = {}
        self.idempotency_keys: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Gateway Management
    # ------------------------------------------------------------------

    def register_gateway(self, config: PaymentGatewayConfig) -> PaymentGatewayConfig:
        """Đăng ký payment gateway.

        Args:
            config: Cấu hình gateway

        Returns:
            PaymentGatewayConfig đã đăng ký
        """
        self.gateways[config.config_id] = config
        return config

    def get_gateway(self, config_id: str) -> PaymentGatewayConfig:
        """Lấy cấu hình gateway theo ID.

        Args:
            config_id: ID của gateway config

        Returns:
            PaymentGatewayConfig

        Raises:
            MidicoderError: Nếu gateway không tồn tại
        """
        if config_id not in self.gateways:
            raise EM.raise_error(
                ErrorCode.MDC-F26_PAYMENT_GATEWAY_NOT_FOUND,
                reason=f"Gateway '{config_id}' không tồn tại",
            )
        return self.gateways[config_id]

    def get_enabled_gateways(self) -> list[PaymentGatewayConfig]:
        """Lấy danh sách gateways đang hoạt động.

        Returns:
            Danh sách PaymentGatewayConfig đang bật
        """
        return [g for g in self.gateways.values() if g.is_enabled]

    # ------------------------------------------------------------------
    # Payment Method Management
    # ------------------------------------------------------------------

    def add_payment_method(self, method: PaymentMethod) -> PaymentMethod:
        """Thêm payment method mới.

        Args:
            method: Payment method cần thêm

        Returns:
            PaymentMethod đã thêm
        """
        self.methods[method.method_id] = method
        return method

    def get_payment_method(self, method_id: str) -> PaymentMethod:
        """Lấy payment method theo ID.

        Args:
            method_id: ID của payment method

        Returns:
            PaymentMethod

        Raises:
            MidicoderError: Nếu payment method không tồn tại
        """
        if method_id not in self.methods:
            raise EM.raise_error(
                ErrorCode.MDC-F26_PAYMENT_METHOD_NOT_FOUND,
                reason=f"Payment method '{method_id}' không tồn tại",
            )
        return self.methods[method_id]

    def get_user_payment_methods(self, user_id: str) -> list[PaymentMethod]:
        """Lấy danh sách payment methods của user.

        Args:
            user_id: ID user

        Returns:
            Danh sách PaymentMethod
        """
        return [m for m in self.methods.values() if m.user_id == user_id]

    def get_default_payment_method(self, user_id: str) -> PaymentMethod | None:
        """Lấy payment method mặc định của user.

        Args:
            user_id: ID user

        Returns:
            PaymentMethod mặc định hoặc None
        """
        for method in self.get_user_payment_methods(user_id):
            if method.is_default and method.is_usable:
                return method
        return None

    def set_default_payment_method(self, user_id: str, method_id: str) -> PaymentMethod:
        """Đặt payment method mặc định cho user.

        Args:
            user_id: ID user
            method_id: ID payment method mới

        Returns:
            PaymentMethod đã đặt làm mặc định

        Raises:
            MidicoderError: Nếu payment method không tồn tại hoặc không usable
        """
        method = self.get_payment_method(method_id)
        if method.user_id != user_id:
            raise EM.raise_error(
                ErrorCode.MDC-F26_PAYMENT_METHOD_NOT_FOUND,
                reason=f"Payment method '{method_id}' không thuộc user '{user_id}'",
            )
        if not method.is_usable:
            raise EM.raise_error(
                ErrorCode.MDC-F26_PAYMENT_METHOD_EXPIRED,
                reason=f"Payment method '{method_id}' không thể sử dụng (status: {method.status.value})",
            )
        # Bỏ default của các methods khác
        for m in self.methods.values():
            if m.user_id == user_id:
                m.is_default = False
        method.is_default = True
        return method

    def suspend_payment_method(self, method_id: str) -> PaymentMethod:
        """Tạm ngưng payment method.

        Args:
            method_id: ID payment method

        Returns:
            PaymentMethod đã ngưng

        Raises:
            MidicoderError: Nếu payment method không tồn tại
        """
        method = self.get_payment_method(method_id)
        method.status = PaymentMethodStatus.SUSPENDED
        method.updated_at = datetime.now(timezone.utc)
        return method

    # ------------------------------------------------------------------
    # Payment Processing
    # ------------------------------------------------------------------

    def process_payment(
        self,
        user_id: str,
        amount: int,
        currency: str = "VND",
        payment_method_id: str = "",
        gateway_type: PaymentGatewayType = PaymentGatewayType.STRIPE,
        idempotency_key: str = "",
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> PaymentTransaction:
        """Xử lý thanh toán mới.

        Args:
            user_id: ID user
            amount: Số tiền (smallest currency unit)
            currency: Mã currency
            payment_method_id: ID payment method (nếu trống, lấy default)
            gateway_type: Gateway provider
            idempotency_key: Key idempotency
            description: Mô tả
            metadata: Dữ liệu bổ sung

        Returns:
            PaymentTransaction đã tạo

        Raises:
            MidicoderError: Nếu amount invalid, idempotency conflict,
                          payment method không tồn tại, gateway không tồn tại
        """
        # Kiểm tra amount
        if amount <= 0:
            raise EM.raise_error(
                ErrorCode.MDC-F26_INVALID_PAYMENT_AMOUNT,
                reason=f"amount phải lớn hơn 0, nhận được: {amount}",
            )

        # Kiểm tra idempotency
        if idempotency_key and idempotency_key in self.idempotency_keys:
            existing_tx_id = self.idempotency_keys[idempotency_key]
            raise EM.raise_error(
                ErrorCode.MDC-F26_PAYMENT_IDEMPOTENCY_CONFLICT,
                reason=f"Idempotency key '{idempotency_key}' đã được sử dụng cho transaction '{existing_tx_id}'",
            )

        # Lấy payment method
        if not payment_method_id:
            default = self.get_default_payment_method(user_id)
            if default is None:
                raise EM.raise_error(
                    ErrorCode.MDC-F26_PAYMENT_METHOD_NOT_FOUND,
                    reason=f"User '{user_id}' không có payment method mặc định",
                )
            payment_method_id = default.method_id

        method = self.get_payment_method(payment_method_id)
        if not method.is_usable:
            raise EM.raise_error(
                ErrorCode.MDC-F26_PAYMENT_METHOD_EXPIRED,
                reason=f"Payment method '{payment_method_id}' không thể sử dụng (status: {method.status.value})",
            )

        # Tạo transaction
        tx_id = f"tx_{uuid.uuid4().hex[:12]}"
        transaction = PaymentTransaction(
            transaction_id=tx_id,
            user_id=user_id,
            payment_method_id=payment_method_id,
            amount=amount,
            currency=currency,
            gateway_type=gateway_type,
            status=PaymentStatus.PENDING,
            idempotency_key=idempotency_key,
            description=description,
            metadata=metadata or {},
        )

        self.transactions[tx_id] = transaction

        # Lưu idempotency key
        if idempotency_key:
            self.idempotency_keys[idempotency_key] = tx_id

        # Simulation: chuyển sang processing → completed
        transaction.status = PaymentStatus.PROCESSING
        transaction.updated_at = datetime.now(timezone.utc)
        transaction.status = PaymentStatus.COMPLETED
        transaction.gateway_provider_ref = f"gw_{uuid.uuid4().hex[:8]}"
        transaction.completed_at = datetime.now(timezone.utc)

        return transaction

    def get_transaction(self, transaction_id: str) -> PaymentTransaction:
        """Lấy giao dịch theo ID.

        Args:
            transaction_id: ID giao dịch

        Returns:
            PaymentTransaction

        Raises:
            MidicoderError: Nếu giao dịch không tồn tại
        """
        if transaction_id not in self.transactions:
            raise EM.raise_error(
                ErrorCode.MDC-F26_PAYMENT_PROCESSING_FAILED,
                reason=f"Transaction '{transaction_id}' không tồn tại",
            )
        return self.transactions[transaction_id]

    def get_user_transactions(self, user_id: str) -> list[PaymentTransaction]:
        """Lấy danh sách giao dịch của user.

        Args:
            user_id: ID user

        Returns:
            Danh sách PaymentTransaction
        """
        return [
            tx for tx in self.transactions.values()
            if tx.user_id == user_id
        ]

    def cancel_payment(self, transaction_id: str) -> PaymentTransaction:
        """Hủy giao dịch đang xử lý.

        Args:
            transaction_id: ID giao dịch

        Returns:
            PaymentTransaction đã hủy

        Raises:
            MidicoderError: Nếu giao dịch không tồn tại hoặc không thể hủy
        """
        tx = self.get_transaction(transaction_id)
        if not tx.can_cancel:
            raise EM.raise_error(
                ErrorCode.MDC-F26_PAYMENT_PROCESSING_FAILED,
                reason=f"Transaction '{transaction_id}' không thể hủy (status: {tx.status.value})",
            )
        tx.status = PaymentStatus.CANCELLED
        tx.updated_at = datetime.now(timezone.utc)
        tx.completed_at = tx.updated_at
        return tx

    # ------------------------------------------------------------------
    # Refund Processing
    # ------------------------------------------------------------------

    def create_refund(
        self,
        transaction_id: str,
        amount: int | None = None,
        reason: str = "",
        user_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> PaymentRefund:
        """Tạo yêu cầu hoàn tiền.

        Args:
            transaction_id: ID giao dịch cần hoàn
            amount: Số tiền hoàn (nếu None, hoàn toàn bộ)
            reason: Lý do hoàn tiền
            user_id: ID user yêu cầu (nếu trống, lấy từ transaction)
            metadata: Dữ liệu bổ sung

        Returns:
            PaymentRefund đã tạo

        Raises:
            MidicoderError: Nếu transaction không tồn tại, không thể hoàn,
                          hoặc số tiền hoàn vượt quá số tiền giao dịch
        """
        tx = self.get_transaction(transaction_id)

        if not tx.can_refund:
            raise EM.raise_error(
                ErrorCode.MDC-F26_REFUND_NOT_ALLOWED,
                reason=f"Transaction '{transaction_id}' không thể hoàn tiền (status: {tx.status.value})",
            )

        if not user_id:
            user_id = tx.user_id

        refund_amount = amount if amount is not None else tx.amount

        if refund_amount > tx.amount:
            raise EM.raise_error(
                ErrorCode.MDC-F26_REFUND_AMOUNT_EXCEEDS_ORIGINAL,
                reason=f"Refund amount ({refund_amount}) vượt quá transaction amount ({tx.amount})",
            )

        refund_id = f"rf_{uuid.uuid4().hex[:12]}"
        refund = PaymentRefund(
            refund_id=refund_id,
            transaction_id=transaction_id,
            user_id=user_id,
            amount=refund_amount,
            currency=tx.currency,
            reason=reason,
            status=RefundStatus.PENDING,
            metadata=metadata or {},
        )

        self.refunds[refund_id] = refund

        # Simulation: pending → processing → completed
        refund.status = RefundStatus.PROCESSING
        refund.status = RefundStatus.COMPLETED
        refund.gateway_refund_ref = f"gw_rf_{uuid.uuid4().hex[:8]}"
        refund.completed_at = datetime.now(timezone.utc)

        # Update transaction status nếu full refund
        if refund_amount == tx.amount:
            tx.status = PaymentStatus.REFUNDED
            tx.updated_at = datetime.now(timezone.utc)

        return refund

    def get_refund(self, refund_id: str) -> PaymentRefund:
        """Lấy yêu cầu hoàn tiền theo ID.

        Args:
            refund_id: ID refund

        Returns:
            PaymentRefund

        Raises:
            MidicoderError: Nếu refund không tồn tại
        """
        if refund_id not in self.refunds:
            raise EM.raise_error(
                ErrorCode.MDC-F26_REFUND_NOT_ALLOWED,
                reason=f"Refund '{refund_id}' không tồn tại",
            )
        return self.refunds[refund_id]

    def get_transaction_refunds(self, transaction_id: str) -> list[PaymentRefund]:
        """Lấy danh sách refunds của một giao dịch.

        Args:
            transaction_id: ID giao dịch

        Returns:
            Danh sách PaymentRefund
        """
        return [
            r for r in self.refunds.values()
            if r.transaction_id == transaction_id
        ]

    # ------------------------------------------------------------------
    # Webhook
    # ------------------------------------------------------------------

    def verify_webhook_signature(
        self,
        gateway_type: PaymentGatewayType,
        payload: str,
        signature: str,
        timestamp: str,
    ) -> bool:
        """Xác thực webhook signature.

        Simulation: luôn trả về True nếu signature không rỗng.

        Args:
            gateway_type: Gateway provider
            payload: Raw payload
            signature: Signature gửi kèm
            timestamp: Timestamp

        Returns:
            True nếu hợp lệ

        Raises:
            MidicoderError: Nếu signature invalid
        """
        if not signature:
            raise EM.raise_error(
                ErrorCode.MDC-F26_WEBHOOK_SIGNATURE_INVALID,
                reason="Webhook signature bắt buộc",
            )
        return True

    def handle_webhook(
        self,
        gateway_type: PaymentGatewayType,
        event_type: str,
        payload: dict[str, Any],
    ) -> PaymentTransaction | PaymentRefund | None:
        """Xử lý webhook callback.

        Simulation: update transaction/refund status theo event type.

        Args:
            gateway_type: Gateway provider
            event_type: Loại event (payment.succeeded, payment.failed, refund.completed)
            payload: Payload data

        Returns:
            PaymentTransaction hoặc PaymentRefund đã cập nhật, hoặc None
        """
        tx_id = payload.get("transaction_id")
        refund_id = payload.get("refund_id")

        if event_type == "payment.succeeded" and tx_id:
            tx = self.get_transaction(tx_id)
            tx.status = PaymentStatus.COMPLETED
            tx.updated_at = datetime.now(timezone.utc)
            tx.completed_at = tx.updated_at
            return tx

        elif event_type == "payment.failed" and tx_id:
            tx = self.get_transaction(tx_id)
            tx.status = PaymentStatus.FAILED
            tx.updated_at = datetime.now(timezone.utc)
            tx.completed_at = tx.updated_at
            return tx

        elif event_type == "refund.completed" and refund_id:
            refund = self.get_refund(refund_id)
            refund.status = RefundStatus.COMPLETED
            refund.completed_at = datetime.now(timezone.utc)
            return refund

        return None

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_user_total_spent(self, user_id: str) -> int:
        """Tính tổng số tiền user đã thanh toán thành công.

        Args:
            user_id: ID user

        Returns:
            Tổng số tiền (smallest currency unit)
        """
        total = 0
        for tx in self.transactions.values():
            if tx.user_id == user_id and tx.status == PaymentStatus.COMPLETED:
                total += tx.amount
        return total

    def get_user_total_refunded(self, user_id: str) -> int:
        """Tính tổng số tiền user đã được hoàn tiền.

        Args:
            user_id: ID user

        Returns:
            Tổng số tiền hoàn (smallest currency unit)
        """
        total = 0
        for refund in self.refunds.values():
            if refund.user_id == user_id and refund.status == RefundStatus.COMPLETED:
                total += refund.amount
        return total


__all__ = [
    # Enums
    "PaymentGatewayType",
    "PaymentMethodType",
    "PaymentMethodStatus",
    "PaymentStatus",
    "RefundStatus",
    # Dataclasses
    "PaymentGatewayConfig",
    "PaymentMethod",
    "PaymentTransaction",
    "PaymentRefund",
    # Engine
    "PaymentEngine",
]
