# coding: utf-8
"""
Mô-đun recipes cho CP49 — Consent & Preference Management.

Cung cấp các recipe patterns để generate hệ thống quản lý consent với
chính sách đa mục đích, bản ghi consent, sở thích cookie, sở thích truyền thông.

Lưu ý: gdpr_erasure delegate đến CP47 (Data Retention & Lifecycle Management).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from midicoder.emitters.core.cp49_consent.models import (
    ConsentCategory,
    ConsentPolicy,
    ConsentPurpose,
    ConsentRecord,
    ConsentStatus,
    CookiePreference,
    CommunicationPreference,
)
from midicoder.emitters.core.cp49_consent.parser import ConsentIR


@dataclass
class RecipeOutput:
    """Kết quả của recipe.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: ConsentIR kết quả
    """
    name: str
    description: str
    ir: ConsentIR


def basic_consent_recipe() -> RecipeOutput:
    """Recipe: Quản lý consent cơ bản — 2 chính sách, 1 bản ghi, cookie config cơ bản.

    Tạo 2 chính sách consent (analytics, marketing), 1 bản ghi consent ACTIVE,
    và cấu hình cookie cơ bản với 4 danh mục. use_audit=True, use_retention=True.

    Phù hợp cho môi trường dev/prototyping khi cần consent tối thiểu.

    Returns:
        RecipeOutput với cấu hình consent cơ bản
    """
    policies = [
        ConsentPolicy(
            policy_id="pol_analytics_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
            is_mandatory=False,
            description="Chính sách consent cho phân tích hành vi người dùng",
            expiry_days=365,
            renewal_reminder_days=30,
        ),
        ConsentPolicy(
            policy_id="pol_marketing_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.MARKETING,
            category=ConsentCategory.ADVERTISING,
            is_mandatory=False,
            description="Chính sách consent cho tiếp thị và quảng cáo",
            expiry_days=180,
            renewal_reminder_days=14,
        ),
    ]

    consents = [
        ConsentRecord(
            record_id="consent_001",
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
            status=ConsentStatus.ACTIVE,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            metadata={"source": "cookie_banner", "banner_version": "v2"},
        ),
    ]

    return RecipeOutput(
        name="basic_consent",
        description="2 chính sách (analytics, marketing), 1 bản ghi consent ACTIVE, cookie config cơ bản",
        ir=ConsentIR(
            policies=policies,
            consents=consents,
            cookie_categories=["necessary", "functional", "analytics", "advertising"],
            comm_channels=[],
            use_audit=True,
            use_retention=True,
        ),
    )


def full_consent_recipe() -> RecipeOutput:
    """Recipe: Quản lý consent đầy đủ — 5 chính sách, 3 bản ghi, full cookie + comm config.

    Tạo 5 chính sách consent đa mục đích (essential, analytics, marketing,
    third_party, data_processing), 3 bản ghi consent (ACTIVE, REVOKED, EXPIRED),
    cấu hình cookie đầy đủ với tất cả danh mục, sở thích truyền thông đa kênh,
    tích hợp audit và retention.

    Lưu ý: gdpr_erasure delegate đến CP47 (Data Retention & Lifecycle Management).

    Phù hợp cho môi trường production với đầy đủ tính năng compliance GDPR/CCPA.

    Returns:
        RecipeOutput với cấu hình consent đầy đủ
    """
    now = datetime.now(timezone.utc)

    policies = [
        ConsentPolicy(
            policy_id="pol_essential_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ESSENTIAL,
            category=ConsentCategory.NECESSARY,
            is_mandatory=True,
            description="Chính sách consent bắt buộc cho hoạt động thiết yếu của dịch vụ",
            expiry_days=730,
            renewal_reminder_days=60,
        ),
        ConsentPolicy(
            policy_id="pol_analytics_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
            is_mandatory=False,
            description="Chính sách consent cho phân tích hành vi người dùng",
            expiry_days=365,
            renewal_reminder_days=30,
        ),
        ConsentPolicy(
            policy_id="pol_marketing_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.MARKETING,
            category=ConsentCategory.ADVERTISING,
            is_mandatory=False,
            description="Chính sách consent cho tiếp thị và quảng cáo nhắm mục tiêu",
            expiry_days=180,
            renewal_reminder_days=14,
        ),
        ConsentPolicy(
            policy_id="pol_thirdparty_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.THIRD_PARTY,
            category=ConsentCategory.FUNCTIONAL,
            is_mandatory=False,
            description="Chính sách consent cho chia sẻ dữ liệu với bên thứ ba",
            expiry_days=365,
            renewal_reminder_days=30,
        ),
        ConsentPolicy(
            policy_id="pol_dataproc_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.DATA_PROCESSING,
            category=ConsentCategory.FUNCTIONAL,
            is_mandatory=False,
            description="Chính sách consent cho xử lý dữ liệu cá nhân tổng quát",
            expiry_days=365,
            renewal_reminder_days=45,
        ),
    ]

    consents = [
        ConsentRecord(
            record_id="consent_full_001",
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
            status=ConsentStatus.ACTIVE,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            metadata={"source": "privacy_center", "granted_via": "explicit_opt_in"},
        ),
        ConsentRecord(
            record_id="consent_full_002",
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.MARKETING,
            category=ConsentCategory.ADVERTISING,
            status=ConsentStatus.REVOKED,
            revoked_at=now - timedelta(days=5),
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            metadata={"source": "privacy_center", "revoke_reason": "User requested opt-out"},
        ),
        ConsentRecord(
            record_id="consent_full_003",
            user_id="user_002",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.DATA_PROCESSING,
            category=ConsentCategory.FUNCTIONAL,
            status=ConsentStatus.EXPIRED,
            granted_at=now - timedelta(days=400),
            ip_address="10.0.0.55",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            metadata={"source": "cookie_banner", "expired_due_to": "expiry_days_exceeded"},
        ),
    ]

    return RecipeOutput(
        name="full_consent",
        description=(
            "5 chính sách (essential, analytics, marketing, third_party, data_processing), "
            "3 bản ghi consent (active/revoked/expired), full cookie + comm config, "
            "tích hợp audit + retention"
        ),
        ir=ConsentIR(
            policies=policies,
            consents=consents,
            cookie_categories=["necessary", "functional", "analytics", "advertising"],
            comm_channels=["email", "sms", "push", "webhook"],
            use_audit=True,
            use_retention=True,
        ),
    )


__all__ = [
    "RecipeOutput",
    "basic_consent_recipe",
    "full_consent_recipe",
]
