# coding: utf-8
"""
Mô-đun models cho CP36 — Tenant Onboarding & Subscription.

Định nghĩa các dataclass biểu diễn:
- SubscriptionPlan: Enum các bậc gói subscription (free, starter, professional, enterprise)
- RegistrationStatus: Enum trạng thái đăng ký (pending, verified, rejected, cancelled)
- SubscriptionStatus: Enum trạng thái subscription (trial, active, past_due, cancelled, expired)
- BillingCycle: Enum chu kỳ thanh toán (monthly, yearly)
- TenantRegistration: Entity đăng ký tenant mới
- TenantSubscription: Entity quản lý subscription
- PlanConfig: Cấu hình giá cho từng plan
- OnboardingIR: Intermediate Representation cho CP36

KPI-005: CP Obligations Coverage (>= 2 obligations cho CP36).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Optional


from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class SubscriptionPlan(str, Enum):
    """
    Enum các bậc gói subscription.

    - FREE: Gói miễn phí, hạn chế tính năng
    - STARTER: Gói cơ bản, phù hợp startup
    - PROFESSIONAL: Gói chuyên nghiệp, đầy đủ tính năng
    - ENTERPRISE: Gói doanh nghiệp, custom pricing
    """
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class RegistrationStatus(str, Enum):
    """
    Trạng thái của tenant registration.

    - PENDING: Đang chờ xác minh
    - VERIFIED: Đã xác minh thành công
    - REJECTED: Bị từ chối
    - CANCELLED: Đã hủy
    """
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class SubscriptionStatus(str, Enum):
    """
    Trạng thái của subscription.

    - TRIAL: Đang trong thời gian dùng thử
    - ACTIVE: Đang hoạt động
    - PAST_DUE: Quá hạn thanh toán
    - CANCELLED: Đã hủy
    - EXPIRED: Đã hết hạn
    """
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class BillingCycle(str, Enum):
    """
    Chu kỳ thanh toán.

    - MONTHLY: Thanh toán hàng tháng
    - YEARLY: Thanh toán hàng năm (có giảm giá)
    """
    MONTHLY = "monthly"
    YEARLY = "yearly"


# ===========================================================================
# TenantRegistration
# ===========================================================================


@dataclass
class TenantRegistration:
    """
    Entity đăng ký tenant mới.

    Lưu trữ thông tin đăng ký của tenant trước khi được xác minh.
    Mỗi registration liên kết với một tenant_id sau khi tạo thành công.

    Attributes:
        email: Email đăng ký (unique, required)
        company_name: Tên công ty/tổ chức (required)
        plan: Gói subscription yêu cầu
        trial_days: Số ngày trial (mặc định 14, 0 = không trial)
        status: Trạng thái đăng ký
        verification_token: Token xác minh email (hmac-signed, expire 24h)
        tenant_id: Reference đến tenant đã tạo (CP02)
        created_at: Thời điểm tạo
        updated_at: Thời điểm cập nhật cuối
    """
    email: str
    company_name: str
    plan: SubscriptionPlan
    trial_days: int = 14
    status: RegistrationStatus = RegistrationStatus.PENDING
    verification_token: str = ""
    tenant_id: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate tenant registration sau khi khởi tạo."""
        # Kiểm tra email không để trống
        if not self.email or not self.email.strip():
            EM.raise_error(
                ErrorCode.CP36_EMPTY_EMAIL,
                message="Email không được để trống"
            )

        # Kiểm tra định dạng email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email.strip()):
            EM.raise_error(
                ErrorCode.CP36_INVALID_EMAIL,
                email=self.email,
                message=f"Email không hợp lệ: {self.email}"
            )

        # Kiểm tra company_name không để trống
        if not self.company_name or not self.company_name.strip():
            EM.raise_error(
                ErrorCode.CP36_EMPTY_COMPANY_NAME,
                message="Tên công ty không được để trống"
            )

        # Kiểm tra trial_days không âm
        if self.trial_days < 0:
            EM.raise_error(
                ErrorCode.CP36_INVALID_TRIAL_DAYS,
                trial_days=self.trial_days,
                message=f"Số ngày trial không được âm: {self.trial_days}"
            )

        # Set timestamps nếu chưa có
        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    def compute_expiry_date(self) -> datetime:
        """
        Tính ngày hết hạn trial.

        Returns:
            DateTime của ngày hết hạn trial
        """
        base = self.created_at or datetime.now(timezone.utc)
        return base + timedelta(days=self.trial_days)

    def is_trial_expired(self) -> bool:
        """
        Kiểm tra trial đã hết hạn chưa.

        Returns:
            True nếu trial đã hết hạn, False nếu còn thời gian
        """
        if self.trial_days == 0:
            return True
        expiry = self.compute_expiry_date()
        return datetime.now(timezone.utc) > expiry

    @property
    def is_verified(self) -> bool:
        """Trả về True nếu registration đã được xác minh."""
        return self.status == RegistrationStatus.VERIFIED

    def to_dict(self) -> dict[str, Any]:
        """Chuyển tenant registration sang dict format."""
        return {
            "email": self.email,
            "company_name": self.company_name,
            "plan": self.plan.value,
            "trial_days": self.trial_days,
            "status": self.status.value,
            "verification_token": self.verification_token,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TenantRegistration":
        """Tạo TenantRegistration từ dict."""
        return cls(
            email=data.get("email", ""),
            company_name=data.get("company_name", ""),
            plan=SubscriptionPlan(data.get("plan", "free")),
            trial_days=data.get("trial_days", 14),
            status=RegistrationStatus(data.get("status", "pending")),
            verification_token=data.get("verification_token", ""),
            tenant_id=data.get("tenant_id", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )


# ===========================================================================
# TenantSubscription
# ===========================================================================


@dataclass
class TenantSubscription:
    """
    Entity quản lý subscription của tenant.

    Theo dõi trạng thái subscription, pricing, billing cycle.
    Linked với CP02 tenant và CP33 financial (currency).

    Attributes:
        tenant_id: FK đến tenant (CP02)
        plan: Gói subscription hiện tại
        billing_cycle: Chu kỳ thanh toán
        status: Trạng thái subscription
        start_date: Ngày bắt đầu
        end_date: Ngày kết thúc
        payment_method_id: Reference đến payment method (CP45)
        price: Giá theo currency
        currency: Mã tiền tệ ISO 4217
        metadata: Custom metadata
    """
    tenant_id: str
    plan: SubscriptionPlan
    billing_cycle: BillingCycle
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    start_date: datetime | None = None
    end_date: datetime | None = None
    payment_method_id: str = ""
    price: Decimal = Decimal("0")
    currency: str = "USD"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate tenant subscription sau khi khởi tạo."""
        # Tenant ID không được trống
        if not self.tenant_id or not self.tenant_id.strip():
            EM.raise_error(
                ErrorCode.CP36_SUBSCRIPTION_NOT_FOUND,
                message="Tenant ID không được để trống cho subscription"
            )

        # Price không được âm
        if self.price < Decimal("0"):
            EM.raise_error(
                ErrorCode.CP36_INVALID_PLAN,
                price=str(self.price),
                message=f"Giá không được âm: {self.price}"
            )

        # Set timestamps nếu chưa có
        now = datetime.now(timezone.utc)
        if self.start_date is None:
            self.start_date = now

    @property
    def is_active(self) -> bool:
        """Trả về True nếu subscription đang hoạt động."""
        return self.status == SubscriptionStatus.ACTIVE

    @property
    def is_trial(self) -> bool:
        """Trả về True nếu subscription đang trong thời gian trial."""
        return self.status == SubscriptionStatus.TRIAL

    @property
    def requires_payment(self) -> bool:
        """Trả về True nếu subscription yêu cầu thanh toán."""
        return self.plan != SubscriptionPlan.FREE

    def can_upgrade(self, new_plan: SubscriptionPlan) -> bool:
        """
        Kiểm tra có thể upgrade sang plan mới không.

        Args:
            new_plan: Plan muốn upgrade

        Returns:
            True nếu có thể upgrade, False nếu không
        """
        if not self.is_active:
            return False
        if new_plan == self.plan:
            return False
        # Plan order: free < starter < professional < enterprise
        plan_order = {
            SubscriptionPlan.FREE: 0,
            SubscriptionPlan.STARTER: 1,
            SubscriptionPlan.PROFESSIONAL: 2,
            SubscriptionPlan.ENTERPRISE: 3,
        }
        return plan_order.get(new_plan, 0) > plan_order.get(self.plan, 0)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển tenant subscription sang dict format."""
        return {
            "tenant_id": self.tenant_id,
            "plan": self.plan.value,
            "billing_cycle": self.billing_cycle.value,
            "status": self.status.value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "payment_method_id": self.payment_method_id,
            "price": str(self.price),
            "currency": self.currency,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TenantSubscription":
        """Tạo TenantSubscription từ dict."""
        return cls(
            tenant_id=data.get("tenant_id", ""),
            plan=SubscriptionPlan(data.get("plan", "free")),
            billing_cycle=BillingCycle(data.get("billing_cycle", "monthly")),
            status=SubscriptionStatus(data.get("status", "active")),
            start_date=datetime.fromisoformat(data["start_date"]) if data.get("start_date") else None,
            end_date=datetime.fromisoformat(data["end_date"]) if data.get("end_date") else None,
            payment_method_id=data.get("payment_method_id", ""),
            price=Decimal(str(data.get("price", "0"))),
            currency=data.get("currency", "USD"),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# PlanConfig
# ===========================================================================


@dataclass
class PlanConfig:
    """
    Cấu hình giá cho từng subscription plan.

    Attributes:
        plan: Gói subscription
        monthly_price: Giá hàng tháng
        yearly_price: Giá hàng năm (thường có giảm giá)
        features: Danh sách tính năng trong gói
        max_users: Số users tối đa
        max_storage_gb: Storage tối đa (GB)
    """
    plan: SubscriptionPlan
    monthly_price: Decimal = Decimal("0")
    yearly_price: Decimal = Decimal("0")
    features: list[str] = field(default_factory=list)
    max_users: int = 10
    max_storage_gb: int = 10

    def to_dict(self) -> dict[str, Any]:
        """Chuyển plan config sang dict."""
        return {
            "plan": self.plan.value,
            "monthly_price": str(self.monthly_price),
            "yearly_price": str(self.yearly_price),
            "features": self.features,
            "max_users": self.max_users,
            "max_storage_gb": self.max_storage_gb,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlanConfig":
        """Tạo PlanConfig từ dict."""
        return cls(
            plan=SubscriptionPlan(data.get("plan", "free")),
            monthly_price=Decimal(str(data.get("monthly_price", "0"))),
            yearly_price=Decimal(str(data.get("yearly_price", "0"))),
            features=data.get("features", []),
            max_users=data.get("max_users", 10),
            max_storage_gb=data.get("max_storage_gb", 10),
        )


# ===========================================================================
# OnboardingIR
# ===========================================================================


@dataclass
class OnboardingIR:
    """
    Intermediate Representation cho CP36 — Tenant Onboarding.

    Gom tập tất cả cấu hình onboarding từ DSL, bao gồm:
    - Plan configs (pricing, features)
    - Trial settings
    - Approval policy
    - Auto-start trial setting

    Attributes:
        plans: Danh sách plan configs
        default_trial_days: Số ngày trial mặc định
        require_admin_approval: Có yêu cầu admin approve không
        auto_start_trial: Có tự động bắt đầu trial sau verification không
        verification_token_expiry_hours: Thời gian hết hạn verification token (giờ)
    """
    plans: list[PlanConfig] = field(default_factory=list)
    default_trial_days: int = 14
    require_admin_approval: bool = False
    auto_start_trial: bool = True
    verification_token_expiry_hours: int = 24

    def __post_init__(self) -> None:
        """Validate OnboardingIR sau khi khởi tạo."""
        if self.default_trial_days < 0:
            EM.raise_error(
                ErrorCode.CP36_INVALID_TRIAL_DAYS,
                trial_days=self.default_trial_days,
                message=f"Số ngày trial mặc định không được âm: {self.default_trial_days}"
            )
        if self.verification_token_expiry_hours < 1:
            self.verification_token_expiry_hours = 24

    def get_plan_price(self, plan: SubscriptionPlan, cycle: BillingCycle) -> Optional[Decimal]:
        """
        Lấy giá của plan theo billing cycle.

        Args:
            plan: Gói subscription
            cycle: Chu kỳ thanh toán

        Returns:
            Giá của plan hoặc None nếu không tìm thấy
        """
        for pc in self.plans:
            if pc.plan == plan:
                if cycle == BillingCycle.MONTHLY:
                    return pc.monthly_price
                else:
                    return pc.yearly_price
        return None

    def get_plan_config(self, plan: SubscriptionPlan) -> Optional[PlanConfig]:
        """
        Lấy config của plan.

        Args:
            plan: Gói subscription

        Returns:
            PlanConfig hoặc None nếu không tìm thấy
        """
        for pc in self.plans:
            if pc.plan == plan:
                return pc
        return None

    def validate(self) -> None:
        """
        Validate toàn bộ OnboardingIR.

        Raises:
            MidicoderError: Nếu có sai sót trong cấu hình
        """
        # Kiểm tra free plan luôn có giá = 0
        for pc in self.plans:
            if pc.plan == SubscriptionPlan.FREE:
                if pc.monthly_price > Decimal("0") or pc.yearly_price > Decimal("0"):
                    EM.raise_error(
                        ErrorCode.CP36_INVALID_PLAN,
                        message="Free plan không được có giá"
                    )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển OnboardingIR sang dict format."""
        return {
            "plans": [pc.to_dict() for pc in self.plans],
            "default_trial_days": self.default_trial_days,
            "require_admin_approval": self.require_admin_approval,
            "auto_start_trial": self.auto_start_trial,
            "verification_token_expiry_hours": self.verification_token_expiry_hours,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OnboardingIR":
        """Tạo OnboardingIR từ dict."""
        plans_data = data.get("plans", [])
        plans = [PlanConfig.from_dict(p) for p in plans_data]
        return cls(
            plans=plans,
            default_trial_days=data.get("default_trial_days", 14),
            require_admin_approval=data.get("require_admin_approval", False),
            auto_start_trial=data.get("auto_start_trial", True),
            verification_token_expiry_hours=data.get("verification_token_expiry_hours", 24),
        )
