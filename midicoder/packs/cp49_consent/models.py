# coding: utf-8
"""
Mô-đun models cho CP49 — Consent & Preference Management.

Định nghĩa các dataclass biểu diễn:
- ConsentStatus: Trạng thái consent (active, revoked, expired, pending_renewal)
- ConsentPurpose: Mục đích consent (analytics, marketing, third_party, functional, essential, data_processing)
- ConsentCategory: Danh mục consent (necessary, functional, analytics, advertising)
- CookieCategory: Danh mục cookie (necessary, functional, analytics, advertising)
- CommChannel: Kênh truyền thông (email, sms, push, webhook)
- ConsentRecord: Bản ghi consent của người dùng
- ConsentPolicy: Chính sách consent của tenant
- CookiePreference: Sở thích cookie của người dùng
- CommunicationPreference: Sở thích truyền thông của người dùng
- ConsentEngine: Engine xử lý toàn bộ vòng đời consent, cookie, và truyền thông

Lưu ý: gdpr_erasure delegate đến CP47 (Data Retention & Lifecycle Management).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class ConsentStatus(str, Enum):
    """Trạng thái của bản ghi consent.

    - ACTIVE: Đang hoạt động, người dùng đã đồng ý
    - REVOKED: Đã bị thu hồi bởi người dùng
    - EXPIRED: Đã hết hạn theo chính sách
    - PENDING_RENEWAL: Đang chờ gia hạn (đã gửi nhắc nhở)
    """
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    PENDING_RENEWAL = "pending_renewal"


class ConsentPurpose(str, Enum):
    """Mục đích thu thập và xử lý dữ liệu.

    - ANALYTICS: Phân tích hành vi người dùng
    - MARKETING: Tiếp thị và quảng cáo
    - THIRD_PARTY: Chia sẻ với bên thứ ba
    - FUNCTIONAL: Chức năng nâng cao của dịch vụ
    - ESSENTIAL: Thiết yếu cho việc hoạt động dịch vụ
    - DATA_PROCESSING: Xử lý dữ liệu cá nhân tổng quát
    """
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    THIRD_PARTY = "third_party"
    FUNCTIONAL = "functional"
    ESSENTIAL = "essential"
    DATA_PROCESSING = "data_processing"


class ConsentCategory(str, Enum):
    """Danh mục phân loại consent.

    - NECESSARY: Bắt buộc, không thể từ chối
    - FUNCTIONAL: Cải thiện chức năng dịch vụ
    - ANALYTICS: Thu thập dữ liệu phân tích
    - ADVERTISING: Dùng cho mục đích quảng cáo
    """
    NECESSARY = "necessary"
    FUNCTIONAL = "functional"
    ANALYTICS = "analytics"
    ADVERTISING = "advertising"


class CookieCategory(str, Enum):
    """Danh mục cookie theo tiêu chuẩn GDPR.

    - NECESSARY: Cookie cần thiết cho hoạt động website
    - FUNCTIONAL: Cookie lưu cài đặt, tùy chỉnh của người dùng
    - ANALYTICS: Cookie theo dõi phân tích lưu lượng
    - ADVERTISING: Cookie dùng cho quảng cáo nhắm mục tiêu
    """
    NECESSARY = "necessary"
    FUNCTIONAL = "functional"
    ANALYTICS = "analytics"
    ADVERTISING = "advertising"


class CommChannel(str, Enum):
    """Kênh truyền thông để gửi thông báo.

    - EMAIL: Thư điện tử
    - SMS: Tin nhắn văn bản
    - PUSH: Thông báo đẩy ứng dụng
    - WEBHOOK: Callback HTTP đến endpoint của khách hàng
    """
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"


# ===========================================================================
# ConsentRecord
# ===========================================================================


@dataclass
class ConsentRecord:
    """Bản ghi consent của người dùng.

    Lưu chi tiết mỗi lần người dùng cấp hoặc rút sự đồng ý,
    bao gồm mục đích, danh mục, địa chỉ IP, và user agent tại thời điểm consent.

    Attributes:
        record_id: ID duy nhất của bản ghi consent
        user_id: ID người dùng đã cấp consent
        tenant_id: ID tenant scope của consent
        purpose: Mục đích thu thập/xử lý dữ liệu
        category: Danh mục phân loại consent
        status: Trạng thái hiện tại (active/revoked/expired/pending_renewal)
        granted_at: Thời điểm cấp consent
        revoked_at: Thời điểm rút consent (nullable)
        ip_address: Địa chỉ IP tại thời điểm cấp consent
        user_agent: User agent của trình duyệt tại thời điểm cấp consent
        metadata: Dữ liệu bổ sung (dict tùy chỉnh)
    """
    record_id: str
    user_id: str
    tenant_id: str
    purpose: ConsentPurpose
    category: ConsentCategory
    status: ConsentStatus = ConsentStatus.ACTIVE
    granted_at: datetime | None = None
    revoked_at: datetime | None = None
    ip_address: str = ""
    user_agent: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate bản ghi consent sau khi khởi tạo."""
        if not self.record_id or not self.record_id.strip():
            EM.raise_error(
                ErrorCode.CP49_CONSENT_RECORD_NOT_FOUND,
                reason="record_id bắt buộc và không được để trống",
            )

        if not self.user_id or not self.user_id.strip():
            EM.raise_error(
                ErrorCode.CP49_CONSENT_RECORD_NOT_FOUND,
                reason="user_id bắt buộc và không được để trống",
            )

        if not self.tenant_id or not self.tenant_id.strip():
            EM.raise_error(
                ErrorCode.CP49_TENANT_POLICY_NOT_FOUND,
                reason="tenant_id bắt buộc cho bản ghi consent",
            )

        if self.purpose not in ConsentPurpose:
            EM.raise_error(
                ErrorCode.CP49_CONSENT_PURPOSE_INVALID,
                purpose=str(self.purpose),
            )

        if self.category not in ConsentCategory:
            EM.raise_error(
                ErrorCode.CP49_CONSENT_CATEGORY_INVALID,
                category=str(self.category),
            )

        now = datetime.now(timezone.utc)
        if self.granted_at is None:
            self.granted_at = now

        # Nếu trạng thái là REVOKED nhưng chưa có revoked_at, đặt giá trị mặc định
        if self.status == ConsentStatus.REVOKED and self.revoked_at is None:
            self.revoked_at = now

        # Nếu trạng thái là EXPIRED, đảm bảo granted_at có giá trị
        if self.status == ConsentStatus.EXPIRED and self.granted_at is None:
            self.granted_at = now - timedelta(days=365)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ConsentRecord sang dict."""
        return {
            "record_id": self.record_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "purpose": self.purpose.value,
            "category": self.category.value,
            "status": self.status.value,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConsentRecord":
        """Tạo ConsentRecord từ dict."""
        return cls(
            record_id=data.get("record_id", ""),
            user_id=data.get("user_id", ""),
            tenant_id=data.get("tenant_id", ""),
            purpose=ConsentPurpose(data.get("purpose", "essential")),
            category=ConsentCategory(data.get("category", "necessary")),
            status=ConsentStatus(data.get("status", "active")),
            granted_at=datetime.fromisoformat(data["granted_at"]) if data.get("granted_at") else None,
            revoked_at=datetime.fromisoformat(data["revoked_at"]) if data.get("revoked_at") else None,
            ip_address=data.get("ip_address", ""),
            user_agent=data.get("user_agent", ""),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# ConsentPolicy
# ===========================================================================


@dataclass
class ConsentPolicy:
    """Chính sách consent của tenant.

    Định nghĩa các quy tắc consent mà một tenant áp dụng,
    bao gồm việc consent có bắt buộc không, thời hạn hết hạn,
    và số ngày nhắc nhở gia hạn trước khi hết hạn.

    Attributes:
        policy_id: ID duy nhất của chính sách
        tenant_id: ID tenant sở hữu chính sách
        purpose: Mục đích thu thập/xử lý dữ liệu
        category: Danh mục phân loại consent
        is_mandatory: Consent có bắt buộc không (không thể rút lại)
        description: Mô tả chi tiết chính sách
        expiry_days: Số ngày consent có hiệu lực từ thời điểm cấp
        renewal_reminder_days: Số ngày nhắc nhở trước khi hết hạn
    """
    policy_id: str
    tenant_id: str
    purpose: ConsentPurpose
    category: ConsentCategory
    is_mandatory: bool = False
    description: str = ""
    expiry_days: int = 365
    renewal_reminder_days: int = 30

    def __post_init__(self) -> None:
        """Validate chính sách consent sau khi khởi tạo."""
        if not self.policy_id or not self.policy_id.strip():
            EM.raise_error(
                ErrorCode.CP49_TENANT_POLICY_NOT_FOUND,
                reason="policy_id bắt buộc và không được để trống",
            )

        if not self.tenant_id or not self.tenant_id.strip():
            EM.raise_error(
                ErrorCode.CP49_TENANT_POLICY_NOT_FOUND,
                reason="tenant_id bắt buộc cho chính sách consent",
            )

        if self.purpose not in ConsentPurpose:
            EM.raise_error(
                ErrorCode.CP49_CONSENT_PURPOSE_INVALID,
                purpose=str(self.purpose),
            )

        if self.category not in ConsentCategory:
            EM.raise_error(
                ErrorCode.CP49_CONSENT_CATEGORY_INVALID,
                category=str(self.category),
            )

        if self.expiry_days < 1:
            self.expiry_days = 365

        if self.renewal_reminder_days < 0:
            self.renewal_reminder_days = 0

        # Consent bắt buộc phải thuộc danh mục NECESSARY
        if self.is_mandatory and self.category != ConsentCategory.NECESSARY:
            self.category = ConsentCategory.NECESSARY

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ConsentPolicy sang dict."""
        return {
            "policy_id": self.policy_id,
            "tenant_id": self.tenant_id,
            "purpose": self.purpose.value,
            "category": self.category.value,
            "is_mandatory": self.is_mandatory,
            "description": self.description,
            "expiry_days": self.expiry_days,
            "renewal_reminder_days": self.renewal_reminder_days,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConsentPolicy":
        """Tạo ConsentPolicy từ dict."""
        return cls(
            policy_id=data.get("policy_id", ""),
            tenant_id=data.get("tenant_id", ""),
            purpose=ConsentPurpose(data.get("purpose", "essential")),
            category=ConsentCategory(data.get("category", "necessary")),
            is_mandatory=data.get("is_mandatory", False),
            description=data.get("description", ""),
            expiry_days=data.get("expiry_days", 365),
            renewal_reminder_days=data.get("renewal_reminder_days", 30),
        )


# ===========================================================================
# CookiePreference
# ===========================================================================


@dataclass
class CookiePreference:
    """Sở thích cookie của người dùng.

    Lưu trữ sự đồng ý của người dùng đối với từng danh mục cookie,
    tuân thủ theo tiêu chuẩn GDPR cho cookie consent.

    Attributes:
        preference_id: ID duy nhất của bản ghi sở thích
        user_id: ID người dùng
        tenant_id: ID tenant scope
        categories: Từ điển ánh xạ danh mục cookie sang trạng thái đồng ý (bool)
        updated_at: Thời điểm cập nhật sở thích cuối cùng
    """
    preference_id: str = ""
    user_id: str = ""
    tenant_id: str = ""
    categories: dict[str, bool] = field(default_factory=dict)
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate sở thích cookie sau khi khởi tạo."""
        now = datetime.now(timezone.utc)

        if not self.user_id or not self.user_id.strip():
            EM.raise_error(
                ErrorCode.CP49_COOKIE_CATEGORY_INVALID,
                reason="user_id bắt buộc cho sở thích cookie",
            )

        if not self.tenant_id or not self.tenant_id.strip():
            EM.raise_error(
                ErrorCode.CP49_TENANT_POLICY_NOT_FOUND,
                reason="tenant_id bắt buộc cho sở thích cookie",
            )

        # Cookie NECESSARY luôn được đặt là True (không thể từ chối)
        if "necessary" in self.categories:
            self.categories["necessary"] = True

        # Kiểm tra các danh mục cookie có hợp lệ không
        valid_categories = {c.value for c in CookieCategory}
        for cat in self.categories:
            if cat not in valid_categories:
                EM.raise_error(
                    ErrorCode.CP49_COOKIE_CATEGORY_INVALID,
                    category=cat,
                )

        if self.updated_at is None:
            self.updated_at = now

        # Tự động tạo preference_id nếu chưa có
        if not self.preference_id:
            self.preference_id = f"cookie_pref_{self.user_id}_{self.tenant_id}"

    def to_dict(self) -> dict[str, Any]:
        """Chuyển CookiePreference sang dict."""
        return {
            "preference_id": self.preference_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "categories": self.categories,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CookiePreference":
        """Tạo CookiePreference từ dict."""
        return cls(
            preference_id=data.get("preference_id", ""),
            user_id=data.get("user_id", ""),
            tenant_id=data.get("tenant_id", ""),
            categories=data.get("categories", {}),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )


# ===========================================================================
# CommunicationPreference
# ===========================================================================


@dataclass
class CommunicationPreference:
    """Sở thích truyền thông của người dùng.

    Quản lý việc người dùng có đồng ý nhận thông tin qua từng kênh
    (email, SMS, push, webhook) và cho từng mục đích (marketing, thông báo, v.v.).

    Attributes:
        preference_id: ID duy nhất của bản ghi sở thích
        user_id: ID người dùng
        tenant_id: ID tenant scope
        channels: Từ điển ánh xạ kênh truyền thông sang trạng thái opt-in (bool)
        purposes: Từ điển ánh xạ mục đích truyền thông sang trạng thái opt-in (bool)
        updated_at: Thời điểm cập nhật sở thích cuối cùng
    """
    preference_id: str = ""
    user_id: str = ""
    tenant_id: str = ""
    channels: dict[str, bool] = field(default_factory=dict)
    purposes: dict[str, bool] = field(default_factory=dict)
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate sở thích truyền thông sau khi khởi tạo."""
        now = datetime.now(timezone.utc)

        if not self.user_id or not self.user_id.strip():
            EM.raise_error(
                ErrorCode.CP49_COMM_CHANNEL_INVALID,
                reason="user_id bắt buộc cho sở thích truyền thông",
            )

        if not self.tenant_id or not self.tenant_id.strip():
            EM.raise_error(
                ErrorCode.CP49_TENANT_POLICY_NOT_FOUND,
                reason="tenant_id bắt buộc cho sở thích truyền thông",
            )

        # Kiểm tra các kênh truyền thông có hợp lệ không
        valid_channels = {c.value for c in CommChannel}
        for ch in self.channels:
            if ch not in valid_channels:
                EM.raise_error(
                    ErrorCode.CP49_COMM_CHANNEL_INVALID,
                    channel=ch,
                )

        if self.updated_at is None:
            self.updated_at = now

        # Tự động tạo preference_id nếu chưa có
        if not self.preference_id:
            self.preference_id = f"comm_pref_{self.user_id}_{self.tenant_id}"

    def to_dict(self) -> dict[str, Any]:
        """Chuyển CommunicationPreference sang dict."""
        return {
            "preference_id": self.preference_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "channels": self.channels,
            "purposes": self.purposes,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CommunicationPreference":
        """Tạo CommunicationPreference từ dict."""
        return cls(
            preference_id=data.get("preference_id", ""),
            user_id=data.get("user_id", ""),
            tenant_id=data.get("tenant_id", ""),
            channels=data.get("channels", {}),
            purposes=data.get("purposes", {}),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )


# ===========================================================================
# ConsentEngine
# ===========================================================================


class ConsentEngine:
    """Engine xử lý toàn bộ vòng đời consent, cookie, và truyền thông.

    In-memory engine cho quản lý consent: cấp và rút consent, kiểm tra
    trạng thái consent, quản lý sở thích cookie và truyền thông, và kiểm
    tra consent hết hạn.

    Lưu ý: gdpr_erasure delegate đến CP47 (Data Retention & Lifecycle Management).

    Workflow:
    1. Tenant định nghĩa ConsentPolicy (mục đích, danh mục, thời hạn)
    2. User cấp consent → tạo ConsentRecord (status=ACTIVE)
    3. User rút consent → soft revoke (status=REVOKED, revoked_at=now)
    4. Engine tự động kiểm tra consent hết hạn theo expiry_days của policy
    5. User quản lý cookie preference, communication preference

    Attributes:
        records: Dict record_id → ConsentRecord
        policies: Dict policy_id → ConsentPolicy
        cookie_preferences: Dict key → CookiePreference
        comm_preferences: Dict key → CommunicationPreference
    """

    def __init__(self) -> None:
        """Khởi tạo ConsentEngine với các bộ sưu tập rỗng."""
        self.records: dict[str, ConsentRecord] = {}
        self.policies: dict[str, ConsentPolicy] = {}
        self.cookie_preferences: dict[str, CookiePreference] = {}
        self.comm_preferences: dict[str, CommunicationPreference] = {}
        self._record_counter = 0

    def grant_consent(
        self,
        user_id: str,
        tenant_id: str,
        purpose: ConsentPurpose,
        category: ConsentCategory,
        ip_address: str = "",
        user_agent: str = "",
    ) -> ConsentRecord:
        """Cấp consent mới cho người dùng.

        Tạo ConsentRecord mới với trạng thái ACTIVE. Validate rằng
        user_id và tenant_id không để trống, purpose và category hợp lệ.

        Args:
            user_id: ID người dùng cần cấp consent
            tenant_id: ID tenant scope của consent
            purpose: Mục đích thu thập/xử lý dữ liệu
            category: Danh mục phân loại consent
            ip_address: Địa chỉ IP tại thời điểm cấp consent
            user_agent: User agent của trình duyệt

        Returns:
            ConsentRecord đã tạo

        Raises:
            MidicoderError: Nếu purpose không hợp lệ (MDC-CP49-002)
            MidicoderError: Nếu category không hợp lệ (MDC-CP49-003)
        """
        if purpose not in ConsentPurpose:
            EM.raise_error(
                ErrorCode.CP49_CONSENT_PURPOSE_INVALID,
                purpose=str(purpose),
            )

        if category not in ConsentCategory:
            EM.raise_error(
                ErrorCode.CP49_CONSENT_CATEGORY_INVALID,
                category=str(category),
            )

        self._record_counter += 1
        record_id = f"consent_{self._record_counter}_{int(time.time() * 1000)}"

        record = ConsentRecord(
            record_id=record_id,
            user_id=user_id,
            tenant_id=tenant_id,
            purpose=purpose,
            category=category,
            status=ConsentStatus.ACTIVE,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.records[record_id] = record
        return record

    def revoke_consent(self, record_id: str, reason: str = "") -> ConsentRecord:
        """Rút lại consent đã cấp trước đó (soft revoke).

        Đặt trạng thái consent sang REVOKED và ghi lại thời điểm rút.
        Nếu consent thuộc policy bắt buộc (mandatory), sẽ từ chối rút.

        Args:
            record_id: ID của bản ghi consent cần rút
            reason: Lý do rút consent (nullable)

        Returns:
            ConsentRecord đã được cập nhật trạng thái REVOKED

        Raises:
            MidicoderError: Nếu record không tồn tại (MDC-CP49-001)
            MidicoderError: Nếu consent bắt buộc không thể rút (MDC-CP49-004)
        """
        if record_id not in self.records:
            EM.raise_error(
                ErrorCode.CP49_CONSENT_RECORD_NOT_FOUND,
                record_id=record_id,
            )

        record = self.records[record_id]

        # Kiểm tra xem có policy bắt buộc cho purpose+category này không
        for policy in self.policies.values():
            if (policy.tenant_id == record.tenant_id
                    and policy.purpose == record.purpose
                    and policy.category == record.category
                    and policy.is_mandatory):
                EM.raise_error(
                    ErrorCode.CP49_MANDATORY_CONSENT_CANNOT_REVOKE,
                    record_id=record_id,
                    policy_id=policy.policy_id,
                )

        record.status = ConsentStatus.REVOKED
        record.revoked_at = datetime.now(timezone.utc)

        if reason:
            record.metadata["revoke_reason"] = reason

        return record

    def check_consent(self, user_id: str, tenant_id: str, purpose: ConsentPurpose) -> bool:
        """Kiểm tra xem người dùng có consent hợp lệ cho mục đích cụ thể không.

        Tìm tất cả consent records của user+tenant với purpose đã cho,
        trả về True nếu có ít nhất một record đang ACTIVE và chưa hết hạn.

        Args:
            user_id: ID người dùng cần kiểm tra
            tenant_id: ID tenant scope
            purpose: Mục đích cần kiểm tra consent

        Returns:
            True nếu có consent ACTIVE hợp lệ, False nếu không có hoặc đã hết hạn
        """
        user_records = [
            r for r in self.records.values()
            if r.user_id == user_id
            and r.tenant_id == tenant_id
            and r.purpose == purpose
        ]

        for record in user_records:
            if record.status == ConsentStatus.ACTIVE:
                # Kiểm tra xem có bị expired không
                if not self._is_expired(record):
                    return True
            elif record.status == ConsentStatus.EXPIRED:
                continue

        return False

    def get_user_consents(self, user_id: str, tenant_id: str) -> list[ConsentRecord]:
        """Lấy tất cả bản ghi consent của người dùng trong tenant.

        Args:
            user_id: ID người dùng
            tenant_id: ID tenant scope

        Returns:
            Danh sách ConsentRecord của người dùng trong tenant
        """
        return [
            r for r in self.records.values()
            if r.user_id == user_id and r.tenant_id == tenant_id
        ]

    def set_cookie_preference(
        self,
        user_id: str,
        tenant_id: str,
        categories: dict[str, bool],
    ) -> CookiePreference:
        """Đặt hoặc cập nhật sở thích cookie của người dùng.

        Lưu hoặc ghi đè sở thích cookie cho user+tenant.
        Cookie NECESSARY luôn được gán True bất kể đầu vào.

        Args:
            user_id: ID người dùng
            tenant_id: ID tenant scope
            categories: Từ điển danh mục cookie → trạng thái đồng ý

        Returns:
            CookiePreference đã tạo hoặc cập nhật

        Raises:
            MidicoderError: Nếu cookie category không hợp lệ (MDC-CP49-009)
        """
        # Validate categories
        valid_categories = {c.value for c in CookieCategory}
        for cat in categories:
            if cat not in valid_categories:
                EM.raise_error(
                    ErrorCode.CP49_COOKIE_CATEGORY_INVALID,
                    category=cat,
                )

        pref = CookiePreference(
            user_id=user_id,
            tenant_id=tenant_id,
            categories=dict(categories),
        )

        key = f"{user_id}:{tenant_id}"
        self.cookie_preferences[key] = pref
        return pref

    def get_cookie_preference(
        self,
        user_id: str,
        tenant_id: str,
    ) -> CookiePreference | None:
        """Lấy sở thích cookie của người dùng.

        Args:
            user_id: ID người dùng
            tenant_id: ID tenant scope

        Returns:
            CookiePreference nếu tìm thấy, None nếu chưa có
        """
        key = f"{user_id}:{tenant_id}"
        return self.cookie_preferences.get(key)

    def set_comm_preference(
        self,
        user_id: str,
        tenant_id: str,
        channels: dict[str, bool],
        purposes: dict[str, bool] | None = None,
    ) -> CommunicationPreference:
        """Đặt hoặc cập nhật sở thích truyền thông của người dùng.

        Lưu hoặc ghi đè sở thích truyền thông cho user+tenant,
        bao gồm kênh nhận thông tin và mục đích được đồng ý.

        Args:
            user_id: ID người dùng
            tenant_id: ID tenant scope
            channels: Từ điển kênh truyền thông → trạng thái opt-in
            purposes: Từ điển mục đích truyền thông → trạng thái opt-in (nullable)

        Returns:
            CommunicationPreference đã tạo hoặc cập nhật

        Raises:
            MidicoderError: Nếu communication channel không hợp lệ (MDC-CP49-007)
        """
        # Validate channels
        valid_channels = {c.value for c in CommChannel}
        for ch in channels:
            if ch not in valid_channels:
                EM.raise_error(
                    ErrorCode.CP49_COMM_CHANNEL_INVALID,
                    channel=ch,
                )

        pref = CommunicationPreference(
            user_id=user_id,
            tenant_id=tenant_id,
            channels=dict(channels),
            purposes=dict(purposes) if purposes else {},
        )

        key = f"{user_id}:{tenant_id}"
        self.comm_preferences[key] = pref
        return pref

    def get_comm_preference(
        self,
        user_id: str,
        tenant_id: str,
    ) -> CommunicationPreference | None:
        """Lấy sở thích truyền thông của người dùng.

        Args:
            user_id: ID người dùng
            tenant_id: ID tenant scope

        Returns:
            CommunicationPreference nếu tìm thấy, None nếu chưa có
        """
        key = f"{user_id}:{tenant_id}"
        return self.comm_preferences.get(key)

    def check_expired_consents(self) -> list[ConsentRecord]:
        """Kiểm tra và trả về danh sách consent đã hết hạn.

        Duyệt qua tất cả consent records đang ACTIVE, so sánh với
        expiry_days của policy tương ứng. Đánh dấu những record
        vượt quá thời hạn sang trạng thái PENDING_RENEWAL hoặc EXPIRED.

        Returns:
            Danh sách ConsentRecord đã hết hạn hoặc đang chờ gia hạn
        """
        now = datetime.now(timezone.utc)
        expired_records: list[ConsentRecord] = []

        for record in self.records.values():
            if record.status != ConsentStatus.ACTIVE:
                continue

            if not record.granted_at:
                continue

            # Tìm policy phù hợp để lấy expiry_days
            expiry_days = 365  # Mặc định 1 năm
            for policy in self.policies.values():
                if (policy.tenant_id == record.tenant_id
                        and policy.purpose == record.purpose
                        and policy.category == record.category):
                    expiry_days = policy.expiry_days
                    # Kiểm tra renewal reminder
                    reminder_threshold = now - timedelta(days=expiry_days - policy.renewal_reminder_days)
                    if record.granted_at <= reminder_threshold <= now:
                        record.status = ConsentStatus.PENDING_RENEWAL
                        expired_records.append(record)
                    break

            # Kiểm tra hết hạn
            expiry_time = record.granted_at + timedelta(days=expiry_days)
            if now > expiry_time:
                record.status = ConsentStatus.EXPIRED
                expired_records.append(record)

        return expired_records

    def get_tenant_consent_stats(self, tenant_id: str) -> dict[str, int]:
        """Lấy thống kê consent của tenant.

        Đếm số lượng consent theo trạng thái (tổng, active, revoked, expired)
        cho tất cả người dùng trong tenant.

        Args:
            tenant_id: ID tenant cần thống kê

        Returns:
            Dict với các khóa: total, active, revoked, expired, pending_renewal
        """
        tenant_records = [
            r for r in self.records.values()
            if r.tenant_id == tenant_id
        ]

        stats: dict[str, int] = {
            "total": len(tenant_records),
            "active": 0,
            "revoked": 0,
            "expired": 0,
            "pending_renewal": 0,
        }

        for record in tenant_records:
            if record.status == ConsentStatus.ACTIVE:
                stats["active"] += 1
            elif record.status == ConsentStatus.REVOKED:
                stats["revoked"] += 1
            elif record.status == ConsentStatus.EXPIRED:
                stats["expired"] += 1
            elif record.status == ConsentStatus.PENDING_RENEWAL:
                stats["pending_renewal"] += 1

        return stats

    def add_policy(self, policy: ConsentPolicy) -> str:
        """Thêm chính sách consent mới cho tenant.

        Args:
            policy: ConsentPolicy cần thêm

        Returns:
            policy_id của chính sách đã thêm

        Raises:
            MidicoderError: Nếu policy_id đã tồn tại
        """
        if policy.policy_id in self.policies:
            EM.raise_error(
                ErrorCode.CP49_TENANT_POLICY_NOT_FOUND,
                reason=f"policy_id '{policy.policy_id}' đã tồn tại",
            )

        self.policies[policy.policy_id] = policy
        return policy.policy_id

    def get_policy(self, policy_id: str) -> ConsentPolicy | None:
        """Lấy chính sách consent theo ID.

        Args:
            policy_id: ID chính sách cần lấy

        Returns:
            ConsentPolicy nếu tìm thấy, None nếu không có
        """
        return self.policies.get(policy_id)

    def get_policies_for_tenant(self, tenant_id: str) -> list[ConsentPolicy]:
        """Lấy tất cả chính sách consent của tenant.

        Args:
            tenant_id: ID tenant cần lấy policies

        Returns:
            Danh sách ConsentPolicy của tenant
        """
        return [
            p for p in self.policies.values()
            if p.tenant_id == tenant_id
        ]

    def _is_expired(self, record: ConsentRecord) -> bool:
        """Kiểm tra xem bản ghi consent có đã hết hạn không.

        Args:
            record: ConsentRecord cần kiểm tra

        Returns:
            True nếu consent đã vượt quá thời hạn của policy
        """
        if not record.granted_at:
            return False

        # Tìm policy phù hợp
        expiry_days = 365
        for policy in self.policies.values():
            if (policy.tenant_id == record.tenant_id
                    and policy.purpose == record.purpose
                    and policy.category == record.category):
                expiry_days = policy.expiry_days
                break

        expiry_time = record.granted_at + timedelta(days=expiry_days)
        return datetime.now(timezone.utc) > expiry_time
