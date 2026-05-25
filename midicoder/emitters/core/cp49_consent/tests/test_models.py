# coding: utf-8
"""
Kiểm tra mô-đun models cho CP49 — Consent & Preference Management.

Bao gồm các tests cho:
- Error codes: MDC-CP49-001 đến MDC-CP49-010
- Enums: ConsentStatus, ConsentPurpose, ConsentCategory, CookieCategory,
  CommChannel, ErasureStatus, ErasureScope
- ConsentRecord: tạo, validate, to_dict/from_dict
- ConsentPolicy: tạo, validate, to_dict/from_dict
- CookiePreference: tạo, validate, to_dict/from_dict
- ErasureRequest: tạo, validate, to_dict/from_dict
- CommunicationPreference: tạo, validate, to_dict/from_dict
- ConsentEngine: grant_consent, revoke_consent, check_consent,
  get_user_consents, set_cookie_preference, get_cookie_preference,
  set_comm_preference, get_comm_preference, create_erasure_request,
  process_erasure_request, check_expired_consents, get_tenant_consent_stats
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from midicoder.errors import ErrorCode, MidicoderError


# ===========================================================================
# Test Error Codes CP49
# ===========================================================================


class TestCP49ErrorCodes:
    """Kiểm tra các mã lỗi CP49 đã được định nghĩa đúng."""

    def test_cp49_consent_record_not_found_code(self):
        assert ErrorCode.CP49_CONSENT_RECORD_NOT_FOUND == "MDC-CP49-001"

    def test_cp49_consent_purpose_invalid_code(self):
        assert ErrorCode.CP49_CONSENT_PURPOSE_INVALID == "MDC-CP49-002"

    def test_cp49_consent_category_invalid_code(self):
        assert ErrorCode.CP49_CONSENT_CATEGORY_INVALID == "MDC-CP49-003"

    def test_cp49_mandatory_consent_cannot_revoke_code(self):
        assert ErrorCode.CP49_MANDATORY_CONSENT_CANNOT_REVOKE == "MDC-CP49-004"

    def test_cp49_erasure_request_not_found_code(self):
        assert ErrorCode.CP49_ERASURE_REQUEST_NOT_FOUND == "MDC-CP49-005"

    def test_cp49_erasure_scope_invalid_code(self):
        assert ErrorCode.CP49_ERASURE_SCOPE_INVALID == "MDC-CP49-006"

    def test_cp49_comm_channel_invalid_code(self):
        assert ErrorCode.CP49_COMM_CHANNEL_INVALID == "MDC-CP49-007"

    def test_cp49_tenant_policy_not_found_code(self):
        assert ErrorCode.CP49_TENANT_POLICY_NOT_FOUND == "MDC-CP49-008"

    def test_cp49_cookie_category_invalid_code(self):
        assert ErrorCode.CP49_COOKIE_CATEGORY_INVALID == "MDC-CP49-009"

    def test_cp49_consent_expired_need_renew_code(self):
        assert ErrorCode.CP49_CONSENT_EXPIRED_NEED_RENEW == "MDC-CP49-010"


# ===========================================================================
# Test ConsentStatus Enum
# ===========================================================================


class TestConsentStatus:
    """Kiểm tra các giá trị của enum ConsentStatus."""

    def test_status_active_value(self):
        from midicoder.emitters.core.cp49_consent.models import ConsentStatus
        assert ConsentStatus.ACTIVE.value == "active"

    def test_status_revoked_value(self):
        from midicoder.emitters.core.cp49_consent.models import ConsentStatus
        assert ConsentStatus.REVOKED.value == "revoked"

    def test_status_expired_value(self):
        from midicoder.emitters.core.cp49_consent.models import ConsentStatus
        assert ConsentStatus.EXPIRED.value == "expired"

    def test_status_pending_renewal_value(self):
        from midicoder.emitters.core.cp49_consent.models import ConsentStatus
        assert ConsentStatus.PENDING_RENEWAL.value == "pending_renewal"

    def test_status_members_count(self):
        from midicoder.emitters.core.cp49_consent.models import ConsentStatus
        assert len(ConsentStatus) == 4


# ===========================================================================
# Test ConsentPurpose Enum
# ===========================================================================


class TestConsentPurpose:
    """Kiểm tra các giá trị của enum ConsentPurpose."""

    def test_purpose_analytics_value(self):
        from midicoder.emitters.core.cp49_consent.models import ConsentPurpose
        assert ConsentPurpose.ANALYTICS.value == "analytics"

    def test_purpose_marketing_value(self):
        from midicoder.emitters.core.cp49_consent.models import ConsentPurpose
        assert ConsentPurpose.MARKETING.value == "marketing"

    def test_purpose_third_party_value(self):
        from midicoder.emitters.core.cp49_consent.models import ConsentPurpose
        assert ConsentPurpose.THIRD_PARTY.value == "third_party"

    def test_purpose_functional_value(self):
        from midicoder.emitters.core.cp49_consent.models import ConsentPurpose
        assert ConsentPurpose.FUNCTIONAL.value == "functional"

    def test_purpose_essential_value(self):
        from midicoder.emitters.core.cp49_consent.models import ConsentPurpose
        assert ConsentPurpose.ESSENTIAL.value == "essential"

    def test_purpose_data_processing_value(self):
        from midicoder.emitters.core.cp49_consent.models import ConsentPurpose
        assert ConsentPurpose.DATA_PROCESSING.value == "data_processing"

    def test_purpose_members_count(self):
        from midicoder.emitters.core.cp49_consent.models import ConsentPurpose
        assert len(ConsentPurpose) == 6


# ===========================================================================
# Test ConsentCategory Enum
# ===========================================================================


class TestConsentCategory:
    """Kiểm tra các giá trị của enum ConsentCategory."""

    def test_category_necessary_value(self):
        from midicoder.emitters.core.cp49_consent.models import ConsentCategory
        assert ConsentCategory.NECESSARY.value == "necessary"

    def test_category_functional_value(self):
        from midicoder.emitters.core.cp49_consent.models import ConsentCategory
        assert ConsentCategory.FUNCTIONAL.value == "functional"

    def test_category_analytics_value(self):
        from midicoder.emitters.core.cp49_consent.models import ConsentCategory
        assert ConsentCategory.ANALYTICS.value == "analytics"

    def test_category_advertising_value(self):
        from midicoder.emitters.core.cp49_consent.models import ConsentCategory
        assert ConsentCategory.ADVERTISING.value == "advertising"

    def test_category_members_count(self):
        from midicoder.emitters.core.cp49_consent.models import ConsentCategory
        assert len(ConsentCategory) == 4


# ===========================================================================
# Test CookieCategory Enum
# ===========================================================================


class TestCookieCategory:
    """Kiểm tra các giá trị của enum CookieCategory."""

    def test_cookie_necessary_value(self):
        from midicoder.emitters.core.cp49_consent.models import CookieCategory
        assert CookieCategory.NECESSARY.value == "necessary"

    def test_cookie_functional_value(self):
        from midicoder.emitters.core.cp49_consent.models import CookieCategory
        assert CookieCategory.FUNCTIONAL.value == "functional"

    def test_cookie_analytics_value(self):
        from midicoder.emitters.core.cp49_consent.models import CookieCategory
        assert CookieCategory.ANALYTICS.value == "analytics"

    def test_cookie_advertising_value(self):
        from midicoder.emitters.core.cp49_consent.models import CookieCategory
        assert CookieCategory.ADVERTISING.value == "advertising"

    def test_cookie_members_count(self):
        from midicoder.emitters.core.cp49_consent.models import CookieCategory
        assert len(CookieCategory) == 4


# ===========================================================================
# Test CommChannel Enum
# ===========================================================================


class TestCommChannel:
    """Kiểm tra các giá trị của enum CommChannel."""

    def test_channel_email_value(self):
        from midicoder.emitters.core.cp49_consent.models import CommChannel
        assert CommChannel.EMAIL.value == "email"

    def test_channel_sms_value(self):
        from midicoder.emitters.core.cp49_consent.models import CommChannel
        assert CommChannel.SMS.value == "sms"

    def test_channel_push_value(self):
        from midicoder.emitters.core.cp49_consent.models import CommChannel
        assert CommChannel.PUSH.value == "push"

    def test_channel_webhook_value(self):
        from midicoder.emitters.core.cp49_consent.models import CommChannel
        assert CommChannel.WEBHOOK.value == "webhook"

    def test_channel_members_count(self):
        from midicoder.emitters.core.cp49_consent.models import CommChannel
        assert len(CommChannel) == 4


# ===========================================================================
# Test ErasureStatus Enum
# ===========================================================================


class TestErasureStatus:
    """Kiểm tra các giá trị của enum ErasureStatus."""

    def test_erasure_pending_value(self):
        from midicoder.emitters.core.cp49_consent.models import ErasureStatus
        assert ErasureStatus.PENDING.value == "pending"

    def test_erasure_reviewing_value(self):
        from midicoder.emitters.core.cp49_consent.models import ErasureStatus
        assert ErasureStatus.REVIEWING.value == "reviewing"

    def test_erasure_approved_value(self):
        from midicoder.emitters.core.cp49_consent.models import ErasureStatus
        assert ErasureStatus.APPROVED.value == "approved"

    def test_erasure_processing_value(self):
        from midicoder.emitters.core.cp49_consent.models import ErasureStatus
        assert ErasureStatus.PROCESSING.value == "processing"

    def test_erasure_completed_value(self):
        from midicoder.emitters.core.cp49_consent.models import ErasureStatus
        assert ErasureStatus.COMPLETED.value == "completed"

    def test_erasure_rejected_value(self):
        from midicoder.emitters.core.cp49_consent.models import ErasureStatus
        assert ErasureStatus.REJECTED.value == "rejected"

    def test_erasure_members_count(self):
        from midicoder.emitters.core.cp49_consent.models import ErasureStatus
        assert len(ErasureStatus) == 6


# ===========================================================================
# Test ErasureScope Enum
# ===========================================================================


class TestErasureScope:
    """Kiểm tra các giá trị của enum ErasureScope."""

    def test_scope_all_personal_data_value(self):
        from midicoder.emitters.core.cp49_consent.models import ErasureScope
        assert ErasureScope.ALL_PERSONAL_DATA.value == "all_personal_data"

    def test_scope_consent_data_value(self):
        from midicoder.emitters.core.cp49_consent.models import ErasureScope
        assert ErasureScope.CONSENT_DATA.value == "consent_data"

    def test_scope_communication_data_value(self):
        from midicoder.emitters.core.cp49_consent.models import ErasureScope
        assert ErasureScope.COMMUNICATION_DATA.value == "communication_data"

    def test_scope_specific_entities_value(self):
        from midicoder.emitters.core.cp49_consent.models import ErasureScope
        assert ErasureScope.SPECIFIC_ENTITIES.value == "specific_entities"

    def test_scope_members_count(self):
        from midicoder.emitters.core.cp49_consent.models import ErasureScope
        assert len(ErasureScope) == 4


# ===========================================================================
# Test ConsentRecord
# ===========================================================================


class TestConsentRecord:
    """Kiểm tra ConsentRecord — tạo, validate, serialize."""

    def test_create_valid_record(self):
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentRecord,
            ConsentPurpose,
            ConsentCategory,
            ConsentStatus,
        )
        rec = ConsentRecord(
            record_id="rec_001",
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
            status=ConsentStatus.ACTIVE,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        assert rec.record_id == "rec_001"
        assert rec.user_id == "user_001"
        assert rec.tenant_id == "tenant_001"
        assert rec.purpose == ConsentPurpose.ANALYTICS
        assert rec.category == ConsentCategory.ANALYTICS
        assert rec.status == ConsentStatus.ACTIVE
        assert rec.ip_address == "192.168.1.1"
        assert rec.user_agent == "Mozilla/5.0"

    def test_create_record_empty_record_id_raises(self):
        """Kiểm tra tạo bản ghi với record_id rỗng sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentRecord,
            ConsentPurpose,
            ConsentCategory,
        )
        with pytest.raises(MidicoderError):
            ConsentRecord(
                record_id="",
                user_id="user_001",
                tenant_id="tenant_001",
                purpose=ConsentPurpose.ANALYTICS,
                category=ConsentCategory.ANALYTICS,
            )

    def test_create_record_whitespace_record_id_raises(self):
        """Kiểm tra tạo bản ghi với record_id chỉ khoảng trắng sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentRecord,
            ConsentPurpose,
            ConsentCategory,
        )
        with pytest.raises(MidicoderError):
            ConsentRecord(
                record_id="   ",
                user_id="user_001",
                tenant_id="tenant_001",
                purpose=ConsentPurpose.ANALYTICS,
                category=ConsentCategory.ANALYTICS,
            )

    def test_create_record_empty_user_id_raises(self):
        """Kiểm tra tạo bản ghi với user_id rỗng sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentRecord,
            ConsentPurpose,
            ConsentCategory,
        )
        with pytest.raises(MidicoderError):
            ConsentRecord(
                record_id="rec_001",
                user_id="",
                tenant_id="tenant_001",
                purpose=ConsentPurpose.ANALYTICS,
                category=ConsentCategory.ANALYTICS,
            )

    def test_create_record_empty_tenant_id_raises(self):
        """Kiểm tra tạo bản ghi với tenant_id rỗng sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentRecord,
            ConsentPurpose,
            ConsentCategory,
        )
        with pytest.raises(MidicoderError):
            ConsentRecord(
                record_id="rec_001",
                user_id="user_001",
                tenant_id="",
                purpose=ConsentPurpose.ANALYTICS,
                category=ConsentCategory.ANALYTICS,
            )

    def test_auto_granted_at(self):
        """Kiểm tra tự động tạo granted_at khi không cung cấp."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentRecord,
            ConsentPurpose,
            ConsentCategory,
        )
        rec = ConsentRecord(
            record_id="rec_ts",
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
        )
        assert rec.granted_at is not None

    def test_revoked_status_sets_revoked_at(self):
        """Kiểm tra trạng thái REVOKED tự động đặt revoked_at."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentRecord,
            ConsentPurpose,
            ConsentCategory,
            ConsentStatus,
        )
        rec = ConsentRecord(
            record_id="rec_rev",
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
            status=ConsentStatus.REVOKED,
        )
        assert rec.revoked_at is not None

    def test_default_status_is_active(self):
        """Kiểm tra trạng thái mặc định là ACTIVE."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentRecord,
            ConsentPurpose,
            ConsentCategory,
            ConsentStatus,
        )
        rec = ConsentRecord(
            record_id="rec_def",
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
        )
        assert rec.status == ConsentStatus.ACTIVE

    def test_default_metadata(self):
        """Kiểm tra metadata mặc định là dict rỗng."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentRecord,
            ConsentPurpose,
            ConsentCategory,
        )
        rec = ConsentRecord(
            record_id="rec_meta",
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
        )
        assert rec.metadata == {}

    def test_to_dict(self):
        """Kiểm tra chuyển ConsentRecord sang dict."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentRecord,
            ConsentPurpose,
            ConsentCategory,
        )
        rec = ConsentRecord(
            record_id="rec_dict",
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.MARKETING,
            category=ConsentCategory.ADVERTISING,
            ip_address="10.0.0.1",
            user_agent="Chrome/120",
            metadata={"consent_version": "2.0"},
        )
        d = rec.to_dict()
        assert d["record_id"] == "rec_dict"
        assert d["user_id"] == "user_001"
        assert d["tenant_id"] == "tenant_001"
        assert d["purpose"] == "marketing"
        assert d["category"] == "advertising"
        assert d["status"] == "active"
        assert d["ip_address"] == "10.0.0.1"
        assert d["user_agent"] == "Chrome/120"
        assert d["metadata"] == {"consent_version": "2.0"}
        assert d["revoked_at"] is None
        assert "granted_at" in d

    def test_from_dict_roundtrip(self):
        """Kiểm tra serialize/deserialize ConsentRecord qua to_dict/from_dict."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentRecord,
            ConsentPurpose,
            ConsentCategory,
            ConsentStatus,
        )
        rec = ConsentRecord(
            record_id="rec_rt",
            user_id="user_rt",
            tenant_id="tenant_rt",
            purpose=ConsentPurpose.THIRD_PARTY,
            category=ConsentCategory.FUNCTIONAL,
            status=ConsentStatus.ACTIVE,
            ip_address="172.16.0.1",
            user_agent="Safari/17",
            metadata={"source": "web_form"},
        )
        d = rec.to_dict()
        restored = ConsentRecord.from_dict(d)
        assert restored.record_id == "rec_rt"
        assert restored.user_id == "user_rt"
        assert restored.tenant_id == "tenant_rt"
        assert restored.purpose == ConsentPurpose.THIRD_PARTY
        assert restored.category == ConsentCategory.FUNCTIONAL
        assert restored.status == ConsentStatus.ACTIVE
        assert restored.metadata == {"source": "web_form"}

    def test_from_dict_without_optional(self):
        """Kiểm tra từ dict chỉ có các trường tối thiểu vẫn tạo được đối tượng."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentRecord,
            ConsentPurpose,
            ConsentCategory,
            ConsentStatus,
        )
        data = {
            "record_id": "rec_min",
            "user_id": "user_min",
            "tenant_id": "tenant_min",
        }
        rec = ConsentRecord.from_dict(data)
        assert rec.record_id == "rec_min"
        assert rec.purpose == ConsentPurpose.ESSENTIAL
        assert rec.category == ConsentCategory.NECESSARY
        assert rec.status == ConsentStatus.ACTIVE

    def test_with_custom_metadata(self):
        """Kiểm tra metadata được bảo toàn qua to_dict/from_dict."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentRecord,
            ConsentPurpose,
            ConsentCategory,
        )
        metadata = {"key1": "value1", "key2": [1, 2, 3]}
        rec = ConsentRecord(
            record_id="rec_cm",
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
            metadata=metadata,
        )
        d = rec.to_dict()
        restored = ConsentRecord.from_dict(d)
        assert restored.metadata == metadata


# ===========================================================================
# Test ConsentPolicy
# ===========================================================================


class TestConsentPolicy:
    """Kiểm tra ConsentPolicy — tạo, validate, serialize."""

    def test_create_valid_policy(self):
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentPolicy,
            ConsentPurpose,
            ConsentCategory,
        )
        policy = ConsentPolicy(
            policy_id="pol_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
            is_mandatory=False,
            description="Chính sách phân tích",
            expiry_days=180,
            renewal_reminder_days=14,
        )
        assert policy.policy_id == "pol_001"
        assert policy.tenant_id == "tenant_001"
        assert policy.purpose == ConsentPurpose.ANALYTICS
        assert policy.category == ConsentCategory.ANALYTICS
        assert policy.is_mandatory is False
        assert policy.expiry_days == 180
        assert policy.renewal_reminder_days == 14

    def test_create_policy_empty_policy_id_raises(self):
        """Kiểm tra tạo chính sách với policy_id rỗng sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentPolicy,
            ConsentPurpose,
            ConsentCategory,
        )
        with pytest.raises(MidicoderError):
            ConsentPolicy(
                policy_id="",
                tenant_id="tenant_001",
                purpose=ConsentPurpose.ANALYTICS,
                category=ConsentCategory.ANALYTICS,
            )

    def test_create_policy_empty_tenant_id_raises(self):
        """Kiểm tra tạo chính sách với tenant_id rỗng sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentPolicy,
            ConsentPurpose,
            ConsentCategory,
        )
        with pytest.raises(MidicoderError):
            ConsentPolicy(
                policy_id="pol_001",
                tenant_id="",
                purpose=ConsentPurpose.ANALYTICS,
                category=ConsentCategory.ANALYTICS,
            )

    def test_default_expiry_days(self):
        """Kiểm tra expiry_days mặc định là 365."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentPolicy,
            ConsentPurpose,
            ConsentCategory,
        )
        policy = ConsentPolicy(
            policy_id="pol_def",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
        )
        assert policy.expiry_days == 365

    def test_default_renewal_reminder_days(self):
        """Kiểm tra renewal_reminder_days mặc định là 30."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentPolicy,
            ConsentPurpose,
            ConsentCategory,
        )
        policy = ConsentPolicy(
            policy_id="pol_rem",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
        )
        assert policy.renewal_reminder_days == 30

    def test_expiry_days_less_than_one_resets(self):
        """Kiểm tra expiry_days nhỏ hơn 1 sẽ được đặt lại thành 365."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentPolicy,
            ConsentPurpose,
            ConsentCategory,
        )
        policy = ConsentPolicy(
            policy_id="pol_exp",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
            expiry_days=0,
        )
        assert policy.expiry_days == 365

    def test_renewal_reminder_negative_resets(self):
        """Kiểm tra renewal_reminder_days âm sẽ được đặt về 0."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentPolicy,
            ConsentPurpose,
            ConsentCategory,
        )
        policy = ConsentPolicy(
            policy_id="pol_remn",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
            renewal_reminder_days=-5,
        )
        assert policy.renewal_reminder_days == 0

    def test_mandatory_forces_necessary_category(self):
        """Kiểm tra chính sách bắt buộc phải thuộc danh mục NECESSARY."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentPolicy,
            ConsentPurpose,
            ConsentCategory,
        )
        policy = ConsentPolicy(
            policy_id="pol_man",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ESSENTIAL,
            category=ConsentCategory.ANALYTICS,
            is_mandatory=True,
        )
        assert policy.category == ConsentCategory.NECESSARY

    def test_to_dict(self):
        """Kiểm tra chuyển ConsentPolicy sang dict."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentPolicy,
            ConsentPurpose,
            ConsentCategory,
        )
        policy = ConsentPolicy(
            policy_id="pol_dict",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.MARKETING,
            category=ConsentCategory.ADVERTISING,
            is_mandatory=True,
            description="Chính sách tiếp thị",
            expiry_days=90,
            renewal_reminder_days=7,
        )
        d = policy.to_dict()
        assert d["policy_id"] == "pol_dict"
        assert d["tenant_id"] == "tenant_001"
        assert d["purpose"] == "marketing"
        assert d["is_mandatory"] is True
        assert d["description"] == "Chính sách tiếp thị"
        assert d["expiry_days"] == 90
        assert d["renewal_reminder_days"] == 7

    def test_from_dict_roundtrip(self):
        """Kiểm tra serialize/deserialize ConsentPolicy qua to_dict/from_dict."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentPolicy,
            ConsentPurpose,
            ConsentCategory,
        )
        policy = ConsentPolicy(
            policy_id="pol_rt",
            tenant_id="tenant_rt",
            purpose=ConsentPurpose.DATA_PROCESSING,
            category=ConsentCategory.NECESSARY,
            is_mandatory=False,
            description="Xử lý dữ liệu",
            expiry_days=730,
            renewal_reminder_days=60,
        )
        d = policy.to_dict()
        restored = ConsentPolicy.from_dict(d)
        assert restored.policy_id == "pol_rt"
        assert restored.tenant_id == "tenant_rt"
        assert restored.purpose == ConsentPurpose.DATA_PROCESSING
        assert restored.category == ConsentCategory.NECESSARY
        assert restored.is_mandatory is False
        assert restored.expiry_days == 730
        assert restored.renewal_reminder_days == 60

    def test_from_dict_without_optional(self):
        """Kiểm tra từ dict chỉ có các trường bắt buộc vẫn tạo được chính sách."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentPolicy,
            ConsentPurpose,
            ConsentCategory,
        )
        data = {
            "policy_id": "pol_min",
            "tenant_id": "tenant_min",
        }
        policy = ConsentPolicy.from_dict(data)
        assert policy.policy_id == "pol_min"
        assert policy.purpose == ConsentPurpose.ESSENTIAL
        assert policy.category == ConsentCategory.NECESSARY
        assert policy.is_mandatory is False
        assert policy.expiry_days == 365

    def test_default_is_mandatory_false(self):
        """Kiểm tra is_mandatory mặc định là False."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentPolicy,
            ConsentPurpose,
            ConsentCategory,
        )
        policy = ConsentPolicy(
            policy_id="pol_def",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
        )
        assert policy.is_mandatory is False


# ===========================================================================
# Test CookiePreference
# ===========================================================================


class TestCookiePreference:
    """Kiểm tra CookiePreference — tạo, validate, serialize."""

    def test_create_valid_preference(self):
        from midicoder.emitters.core.cp49_consent.models import CookiePreference
        pref = CookiePreference(
            preference_id="cookie_001",
            user_id="user_001",
            tenant_id="tenant_001",
            categories={
                "necessary": True,
                "functional": True,
                "analytics": False,
                "advertising": False,
            },
        )
        assert pref.user_id == "user_001"
        assert pref.tenant_id == "tenant_001"
        assert pref.categories["necessary"] is True
        assert pref.categories["functional"] is True
        assert pref.categories["analytics"] is False
        assert pref.categories["advertising"] is False

    def test_create_preference_empty_user_id_raises(self):
        """Kiểm tra tạo sở thích cookie với user_id rỗng sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import CookiePreference
        with pytest.raises(MidicoderError):
            CookiePreference(
                user_id="",
                tenant_id="tenant_001",
            )

    def test_create_preference_empty_tenant_id_raises(self):
        """Kiểm tra tạo sở thích cookie với tenant_id rỗng sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import CookiePreference
        with pytest.raises(MidicoderError):
            CookiePreference(
                user_id="user_001",
                tenant_id="",
            )

    def test_necessary_always_true(self):
        """Kiểm tra danh mục necessary luôn được đặt là True."""
        from midicoder.emitters.core.cp49_consent.models import CookiePreference
        pref = CookiePreference(
            user_id="user_001",
            tenant_id="tenant_001",
            categories={"necessary": False, "analytics": True},
        )
        assert pref.categories["necessary"] is True

    def test_invalid_category_raises(self):
        """Kiểm tra danh mục cookie không hợp lệ sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import CookiePreference
        with pytest.raises(MidicoderError):
            CookiePreference(
                user_id="user_001",
                tenant_id="tenant_001",
                categories={"invalid_cat": True},
            )

    def test_auto_updated_at(self):
        """Kiểm tra tự động tạo updated_at khi không cung cấp."""
        from midicoder.emitters.core.cp49_consent.models import CookiePreference
        pref = CookiePreference(
            user_id="user_001",
            tenant_id="tenant_001",
        )
        assert pref.updated_at is not None

    def test_auto_preference_id(self):
        """Kiểm tra tự động tạo preference_id từ user_id và tenant_id."""
        from midicoder.emitters.core.cp49_consent.models import CookiePreference
        pref = CookiePreference(
            user_id="user_auto",
            tenant_id="tenant_auto",
        )
        assert pref.preference_id == "cookie_pref_user_auto_tenant_auto"

    def test_to_dict(self):
        """Kiểm tra chuyển CookiePreference sang dict."""
        from midicoder.emitters.core.cp49_consent.models import CookiePreference
        pref = CookiePreference(
            preference_id="cookie_d",
            user_id="user_001",
            tenant_id="tenant_001",
            categories={"necessary": True, "analytics": True},
        )
        d = pref.to_dict()
        assert d["preference_id"] == "cookie_d"
        assert d["user_id"] == "user_001"
        assert d["tenant_id"] == "tenant_001"
        assert d["categories"]["necessary"] is True
        assert d["categories"]["analytics"] is True
        assert "updated_at" in d

    def test_from_dict_roundtrip(self):
        """Kiểm tra serialize/deserialize CookiePreference qua to_dict/from_dict."""
        from midicoder.emitters.core.cp49_consent.models import CookiePreference
        pref = CookiePreference(
            preference_id="cookie_rt",
            user_id="user_rt",
            tenant_id="tenant_rt",
            categories={"necessary": True, "functional": False, "advertising": True},
        )
        d = pref.to_dict()
        restored = CookiePreference.from_dict(d)
        assert restored.preference_id == "cookie_rt"
        assert restored.user_id == "user_rt"
        assert restored.tenant_id == "tenant_rt"
        assert restored.categories["necessary"] is True
        assert restored.categories["functional"] is False
        assert restored.categories["advertising"] is True

    def test_from_dict_without_optional(self):
        """Kiểm tra từ dict chỉ có các trường tối thiểu vẫn tạo được đối tượng."""
        from midicoder.emitters.core.cp49_consent.models import CookiePreference
        data = {
            "preference_id": "cookie_min",
            "user_id": "user_min",
            "tenant_id": "tenant_min",
        }
        pref = CookiePreference.from_dict(data)
        assert pref.preference_id == "cookie_min"
        assert pref.categories == {}


# ===========================================================================
# Test ErasureRequest
# ===========================================================================


class TestErasureRequest:
    """Kiểm tra ErasureRequest — tạo, validate, serialize."""

    def test_create_valid_request(self):
        from midicoder.emitters.core.cp49_consent.models import (
            ErasureRequest,
            ErasureScope,
            ErasureStatus,
        )
        req = ErasureRequest(
            request_id="erase_001",
            user_id="user_001",
            tenant_id="tenant_001",
            scope=ErasureScope.ALL_PERSONAL_DATA,
            reason="Xóa tất cả dữ liệu cá nhân",
        )
        assert req.request_id == "erase_001"
        assert req.user_id == "user_001"
        assert req.tenant_id == "tenant_001"
        assert req.scope == ErasureScope.ALL_PERSONAL_DATA
        assert req.status == ErasureStatus.PENDING
        assert req.reason == "Xóa tất cả dữ liệu cá nhân"

    def test_create_request_empty_request_id_raises(self):
        """Kiểm tra tạo yêu cầu xóa với request_id rỗng sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import (
            ErasureRequest,
            ErasureScope,
        )
        with pytest.raises(MidicoderError):
            ErasureRequest(
                request_id="",
                user_id="user_001",
                tenant_id="tenant_001",
                scope=ErasureScope.ALL_PERSONAL_DATA,
            )

    def test_create_request_empty_user_id_raises(self):
        """Kiểm tra tạo yêu cầu xóa với user_id rỗng sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import (
            ErasureRequest,
            ErasureScope,
        )
        with pytest.raises(MidicoderError):
            ErasureRequest(
                request_id="erase_001",
                user_id="",
                tenant_id="tenant_001",
                scope=ErasureScope.ALL_PERSONAL_DATA,
            )

    def test_create_request_empty_tenant_id_raises(self):
        """Kiểm tra tạo yêu cầu xóa với tenant_id rỗng sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import (
            ErasureRequest,
            ErasureScope,
        )
        with pytest.raises(MidicoderError):
            ErasureRequest(
                request_id="erase_001",
                user_id="user_001",
                tenant_id="",
                scope=ErasureScope.ALL_PERSONAL_DATA,
            )

    def test_default_status_is_pending(self):
        """Kiểm tra trạng thái mặc định là PENDING."""
        from midicoder.emitters.core.cp49_consent.models import (
            ErasureRequest,
            ErasureScope,
            ErasureStatus,
        )
        req = ErasureRequest(
            request_id="erase_def",
            user_id="user_001",
            tenant_id="tenant_001",
            scope=ErasureScope.CONSENT_DATA,
        )
        assert req.status == ErasureStatus.PENDING

    def test_auto_requested_at(self):
        """Kiểm tra tự động tạo requested_at khi không cung cấp."""
        from midicoder.emitters.core.cp49_consent.models import (
            ErasureRequest,
            ErasureScope,
        )
        req = ErasureRequest(
            request_id="erase_ts",
            user_id="user_001",
            tenant_id="tenant_001",
            scope=ErasureScope.COMMUNICATION_DATA,
        )
        assert req.requested_at is not None

    def test_completed_status_sets_completed_at(self):
        """Kiểm tra trạng thái COMPLETED tự động đặt completed_at."""
        from midicoder.emitters.core.cp49_consent.models import (
            ErasureRequest,
            ErasureScope,
            ErasureStatus,
        )
        req = ErasureRequest(
            request_id="erase_comp",
            user_id="user_001",
            tenant_id="tenant_001",
            scope=ErasureScope.ALL_PERSONAL_DATA,
            status=ErasureStatus.COMPLETED,
        )
        assert req.completed_at is not None

    def test_default_metadata(self):
        """Kiểm tra metadata mặc định là dict rỗng."""
        from midicoder.emitters.core.cp49_consent.models import (
            ErasureRequest,
            ErasureScope,
        )
        req = ErasureRequest(
            request_id="erase_meta",
            user_id="user_001",
            tenant_id="tenant_001",
            scope=ErasureScope.SPECIFIC_ENTITIES,
        )
        assert req.metadata == {}

    def test_different_scopes(self):
        """Kiểm tra các phạm vi xóa dữ liệu khác nhau."""
        from midicoder.emitters.core.cp49_consent.models import (
            ErasureRequest,
            ErasureScope,
        )
        req1 = ErasureRequest(
            request_id="erase_s1",
            user_id="user_001",
            tenant_id="tenant_001",
            scope=ErasureScope.CONSENT_DATA,
        )
        req2 = ErasureRequest(
            request_id="erase_s2",
            user_id="user_001",
            tenant_id="tenant_001",
            scope=ErasureScope.SPECIFIC_ENTITIES,
        )
        assert req1.scope == ErasureScope.CONSENT_DATA
        assert req2.scope == ErasureScope.SPECIFIC_ENTITIES

    def test_to_dict(self):
        """Kiểm tra chuyển ErasureRequest sang dict."""
        from midicoder.emitters.core.cp49_consent.models import (
            ErasureRequest,
            ErasureScope,
        )
        req = ErasureRequest(
            request_id="erase_dict",
            user_id="user_001",
            tenant_id="tenant_001",
            scope=ErasureScope.ALL_PERSONAL_DATA,
            reason="GDPR quyền bị quên",
            metadata={"entities": ["orders", "profiles"]},
        )
        d = req.to_dict()
        assert d["request_id"] == "erase_dict"
        assert d["user_id"] == "user_001"
        assert d["scope"] == "all_personal_data"
        assert d["status"] == "pending"
        assert d["reason"] == "GDPR quyền bị quên"
        assert d["metadata"] == {"entities": ["orders", "profiles"]}
        assert d["completed_at"] is None
        assert "requested_at" in d

    def test_from_dict_roundtrip(self):
        """Kiểm tra serialize/deserialize ErasureRequest qua to_dict/from_dict."""
        from midicoder.emitters.core.cp49_consent.models import (
            ErasureRequest,
            ErasureScope,
            ErasureStatus,
        )
        req = ErasureRequest(
            request_id="erase_rt",
            user_id="user_rt",
            tenant_id="tenant_rt",
            scope=ErasureScope.CONSENT_DATA,
            status=ErasureStatus.PENDING,
            reason="Xóa dữ liệu consent",
        )
        d = req.to_dict()
        restored = ErasureRequest.from_dict(d)
        assert restored.request_id == "erase_rt"
        assert restored.user_id == "user_rt"
        assert restored.scope == ErasureScope.CONSENT_DATA
        assert restored.status == ErasureStatus.PENDING
        assert restored.reason == "Xóa dữ liệu consent"

    def test_from_dict_without_optional(self):
        """Kiểm tra từ dict chỉ có các trường tối thiểu vẫn tạo được đối tượng."""
        from midicoder.emitters.core.cp49_consent.models import (
            ErasureRequest,
            ErasureScope,
            ErasureStatus,
        )
        data = {
            "request_id": "erase_min",
            "user_id": "user_min",
            "tenant_id": "tenant_min",
        }
        req = ErasureRequest.from_dict(data)
        assert req.request_id == "erase_min"
        assert req.scope == ErasureScope.ALL_PERSONAL_DATA
        assert req.status == ErasureStatus.PENDING

    def test_with_custom_metadata(self):
        """Kiểm tra metadata được bảo toàn qua to_dict/from_dict."""
        from midicoder.emitters.core.cp49_consent.models import (
            ErasureRequest,
            ErasureScope,
        )
        metadata = {"entity_ids": ["e1", "e2"], "admin_note": "đã kiểm tra"}
        req = ErasureRequest(
            request_id="erase_cm",
            user_id="user_001",
            tenant_id="tenant_001",
            scope=ErasureScope.SPECIFIC_ENTITIES,
            metadata=metadata,
        )
        d = req.to_dict()
        restored = ErasureRequest.from_dict(d)
        assert restored.metadata == metadata


# ===========================================================================
# Test CommunicationPreference
# ===========================================================================


class TestCommunicationPreference:
    """Kiểm tra CommunicationPreference — tạo, validate, serialize."""

    def test_create_valid_preference(self):
        from midicoder.emitters.core.cp49_consent.models import (
            CommunicationPreference,
        )
        pref = CommunicationPreference(
            preference_id="comm_001",
            user_id="user_001",
            tenant_id="tenant_001",
            channels={"email": True, "sms": False, "push": True},
            purposes={"marketing": True, "notifications": False},
        )
        assert pref.user_id == "user_001"
        assert pref.tenant_id == "tenant_001"
        assert pref.channels["email"] is True
        assert pref.channels["sms"] is False
        assert pref.channels["push"] is True
        assert pref.purposes["marketing"] is True
        assert pref.purposes["notifications"] is False

    def test_create_preference_empty_user_id_raises(self):
        """Kiểm tra tạo sở thích truyền thông với user_id rỗng sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import (
            CommunicationPreference,
        )
        with pytest.raises(MidicoderError):
            CommunicationPreference(
                user_id="",
                tenant_id="tenant_001",
            )

    def test_create_preference_empty_tenant_id_raises(self):
        """Kiểm tra tạo sở thích truyền thông với tenant_id rỗng sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import (
            CommunicationPreference,
        )
        with pytest.raises(MidicoderError):
            CommunicationPreference(
                user_id="user_001",
                tenant_id="",
            )

    def test_invalid_channel_raises(self):
        """Kiểm tra kênh truyền thông không hợp lệ sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import (
            CommunicationPreference,
        )
        with pytest.raises(MidicoderError):
            CommunicationPreference(
                user_id="user_001",
                tenant_id="tenant_001",
                channels={"invalid_channel": True},
            )

    def test_auto_updated_at(self):
        """Kiểm tra tự động tạo updated_at khi không cung cấp."""
        from midicoder.emitters.core.cp49_consent.models import (
            CommunicationPreference,
        )
        pref = CommunicationPreference(
            user_id="user_001",
            tenant_id="tenant_001",
        )
        assert pref.updated_at is not None

    def test_auto_preference_id(self):
        """Kiểm tra tự động tạo preference_id từ user_id và tenant_id."""
        from midicoder.emitters.core.cp49_consent.models import (
            CommunicationPreference,
        )
        pref = CommunicationPreference(
            user_id="user_auto",
            tenant_id="tenant_auto",
        )
        assert pref.preference_id == "comm_pref_user_auto_tenant_auto"

    def test_default_channels_and_purposes(self):
        """Kiểm tra channels và purposes mặc định là dict rỗng."""
        from midicoder.emitters.core.cp49_consent.models import (
            CommunicationPreference,
        )
        pref = CommunicationPreference(
            user_id="user_001",
            tenant_id="tenant_001",
        )
        assert pref.channels == {}
        assert pref.purposes == {}

    def test_all_channels(self):
        """Kiểm tra tất cả các kênh truyền thông hợp lệ."""
        from midicoder.emitters.core.cp49_consent.models import (
            CommunicationPreference,
        )
        pref = CommunicationPreference(
            user_id="user_001",
            tenant_id="tenant_001",
            channels={"email": True, "sms": True, "push": True, "webhook": True},
        )
        assert pref.channels["email"] is True
        assert pref.channels["sms"] is True
        assert pref.channels["push"] is True
        assert pref.channels["webhook"] is True

    def test_to_dict(self):
        """Kiểm tra chuyển CommunicationPreference sang dict."""
        from midicoder.emitters.core.cp49_consent.models import (
            CommunicationPreference,
        )
        pref = CommunicationPreference(
            preference_id="comm_d",
            user_id="user_001",
            tenant_id="tenant_001",
            channels={"email": True, "push": False},
            purposes={"marketing": False},
        )
        d = pref.to_dict()
        assert d["preference_id"] == "comm_d"
        assert d["user_id"] == "user_001"
        assert d["tenant_id"] == "tenant_001"
        assert d["channels"]["email"] is True
        assert d["channels"]["push"] is False
        assert d["purposes"]["marketing"] is False
        assert "updated_at" in d

    def test_from_dict_roundtrip(self):
        """Kiểm tra serialize/deserialize CommunicationPreference qua to_dict/from_dict."""
        from midicoder.emitters.core.cp49_consent.models import (
            CommunicationPreference,
        )
        pref = CommunicationPreference(
            preference_id="comm_rt",
            user_id="user_rt",
            tenant_id="tenant_rt",
            channels={"email": True, "sms": True},
            purposes={"marketing": True},
        )
        d = pref.to_dict()
        restored = CommunicationPreference.from_dict(d)
        assert restored.preference_id == "comm_rt"
        assert restored.user_id == "user_rt"
        assert restored.tenant_id == "tenant_rt"
        assert restored.channels["email"] is True
        assert restored.channels["sms"] is True
        assert restored.purposes["marketing"] is True

    def test_from_dict_without_optional(self):
        """Kiểm tra từ dict chỉ có các trường tối thiểu vẫn tạo được đối tượng."""
        from midicoder.emitters.core.cp49_consent.models import (
            CommunicationPreference,
        )
        data = {
            "preference_id": "comm_min",
            "user_id": "user_min",
            "tenant_id": "tenant_min",
        }
        pref = CommunicationPreference.from_dict(data)
        assert pref.preference_id == "comm_min"
        assert pref.channels == {}
        assert pref.purposes == {}


# ===========================================================================
# Test ConsentEngine
# ===========================================================================


class TestConsentEngine:
    """Kiểm tra ConsentEngine — toàn bộ workflow consent."""

    def test_engine_empty_collections_on_init(self):
        """Kiểm tra các bộ sưu tập rỗng khi khởi tạo engine."""
        from midicoder.emitters.core.cp49_consent.models import ConsentEngine
        engine = ConsentEngine()
        assert engine.records == {}
        assert engine.policies == {}
        assert engine.cookie_preferences == {}
        assert engine.comm_preferences == {}
        assert engine.erasure_requests == {}

    def test_grant_consent(self):
        """Kiểm tra cấp consent mới cho người dùng."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ConsentPurpose,
            ConsentCategory,
            ConsentStatus,
        )
        engine = ConsentEngine()
        record = engine.grant_consent(
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        assert record.user_id == "user_001"
        assert record.tenant_id == "tenant_001"
        assert record.purpose == ConsentPurpose.ANALYTICS
        assert record.status == ConsentStatus.ACTIVE
        assert record.ip_address == "192.168.1.1"
        assert record.record_id in engine.records

    def test_grant_consent_multiple(self):
        """Kiểm tra cấp nhiều consent với các mục đích khác nhau."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ConsentPurpose,
            ConsentCategory,
        )
        engine = ConsentEngine()
        rec1 = engine.grant_consent(
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
        )
        rec2 = engine.grant_consent(
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.MARKETING,
            category=ConsentCategory.ADVERTISING,
        )
        assert rec1.record_id != rec2.record_id
        assert len(engine.records) == 2

    def test_revoke_consent(self):
        """Kiểm tra rút lại consent đã cấp."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ConsentPurpose,
            ConsentCategory,
            ConsentStatus,
        )
        engine = ConsentEngine()
        record = engine.grant_consent(
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
        )
        revoked = engine.revoke_consent(record.record_id, reason="Người dùng yêu cầu")
        assert revoked.status == ConsentStatus.REVOKED
        assert revoked.revoked_at is not None
        assert revoked.metadata["revoke_reason"] == "Người dùng yêu cầu"

    def test_revoke_nonexistent_record_raises(self):
        """Kiểm tra rút consent không tồn tại sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import ConsentEngine
        engine = ConsentEngine()
        with pytest.raises(MidicoderError):
            engine.revoke_consent("nonexistent_record")

    def test_revoke_mandatory_consent_raises(self):
        """Kiểm tra rút consent bắt buộc sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ConsentPolicy,
            ConsentPurpose,
            ConsentCategory,
        )
        engine = ConsentEngine()
        policy = ConsentPolicy(
            policy_id="pol_man",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ESSENTIAL,
            category=ConsentCategory.NECESSARY,
            is_mandatory=True,
        )
        engine.policies["pol_man"] = policy
        record = engine.grant_consent(
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ESSENTIAL,
            category=ConsentCategory.NECESSARY,
        )
        with pytest.raises(MidicoderError):
            engine.revoke_consent(record.record_id)

    def test_check_consent_granted(self):
        """Kiểm tra người dùng có consent ACTIVE hợp lệ."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ConsentPurpose,
            ConsentCategory,
        )
        engine = ConsentEngine()
        engine.grant_consent(
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
        )
        result = engine.check_consent(
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
        )
        assert result is True

    def test_check_consent_revoked(self):
        """Kiểm tra người dùng có consent đã bị rút."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ConsentPurpose,
            ConsentCategory,
        )
        engine = ConsentEngine()
        record = engine.grant_consent(
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.MARKETING,
            category=ConsentCategory.ADVERTISING,
        )
        engine.revoke_consent(record.record_id)
        result = engine.check_consent(
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.MARKETING,
        )
        assert result is False

    def test_check_consent_not_granted(self):
        """Kiểm tra người dùng chưa cấp consent."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ConsentPurpose,
        )
        engine = ConsentEngine()
        result = engine.check_consent(
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
        )
        assert result is False

    def test_get_user_consents(self):
        """Kiểm tra lấy tất cả bản ghi consent của người dùng."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ConsentPurpose,
            ConsentCategory,
        )
        engine = ConsentEngine()
        engine.grant_consent(
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
        )
        engine.grant_consent(
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.MARKETING,
            category=ConsentCategory.ADVERTISING,
        )
        engine.grant_consent(
            user_id="user_002",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
        )
        consents = engine.get_user_consents("user_001", "tenant_001")
        assert len(consents) == 2

    def test_get_user_consents_empty(self):
        """Kiểm tra lấy consent khi người dùng không có bản ghi."""
        from midicoder.emitters.core.cp49_consent.models import ConsentEngine
        engine = ConsentEngine()
        consents = engine.get_user_consents("nobody", "tenant_001")
        assert consents == []

    def test_set_cookie_preference(self):
        """Kiểm tra đặt sở thích cookie mới."""
        from midicoder.emitters.core.cp49_consent.models import ConsentEngine
        engine = ConsentEngine()
        pref = engine.set_cookie_preference(
            user_id="user_001",
            tenant_id="tenant_001",
            categories={"necessary": True, "analytics": False},
        )
        assert pref.categories["necessary"] is True
        assert pref.categories["analytics"] is False
        key = "user_001:tenant_001"
        assert key in engine.cookie_preferences

    def test_set_cookie_preference_invalid_category_raises(self):
        """Kiểm tra đặt sở thích cookie với danh mục không hợp lệ sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import ConsentEngine
        engine = ConsentEngine()
        with pytest.raises(MidicoderError):
            engine.set_cookie_preference(
                user_id="user_001",
                tenant_id="tenant_001",
                categories={"invalid": True},
            )

    def test_get_cookie_preference(self):
        """Kiểm tra lấy sở thích cookie đã đặt."""
        from midicoder.emitters.core.cp49_consent.models import ConsentEngine
        engine = ConsentEngine()
        engine.set_cookie_preference(
            user_id="user_001",
            tenant_id="tenant_001",
            categories={"functional": True},
        )
        pref = engine.get_cookie_preference("user_001", "tenant_001")
        assert pref is not None
        assert pref.categories["functional"] is True

    def test_get_cookie_preference_none(self):
        """Kiểm tra lấy sở thích cookie khi chưa có."""
        from midicoder.emitters.core.cp49_consent.models import ConsentEngine
        engine = ConsentEngine()
        pref = engine.get_cookie_preference("user_001", "tenant_001")
        assert pref is None

    def test_set_communication_preference(self):
        """Kiểm tra đặt sở thích truyền thông mới."""
        from midicoder.emitters.core.cp49_consent.models import ConsentEngine
        engine = ConsentEngine()
        pref = engine.set_comm_preference(
            user_id="user_001",
            tenant_id="tenant_001",
            channels={"email": True, "sms": False},
            purposes={"marketing": True},
        )
        assert pref.channels["email"] is True
        assert pref.channels["sms"] is False
        assert pref.purposes["marketing"] is True
        key = "user_001:tenant_001"
        assert key in engine.comm_preferences

    def test_set_communication_preference_invalid_channel_raises(self):
        """Kiểm tra đặt sở thích truyền thông với kênh không hợp lệ sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import ConsentEngine
        engine = ConsentEngine()
        with pytest.raises(MidicoderError):
            engine.set_comm_preference(
                user_id="user_001",
                tenant_id="tenant_001",
                channels={"invalid_channel": True},
            )

    def test_get_communication_preference(self):
        """Kiểm tra lấy sở thích truyền thông đã đặt."""
        from midicoder.emitters.core.cp49_consent.models import ConsentEngine
        engine = ConsentEngine()
        engine.set_comm_preference(
            user_id="user_001",
            tenant_id="tenant_001",
            channels={"push": True},
        )
        pref = engine.get_comm_preference("user_001", "tenant_001")
        assert pref is not None
        assert pref.channels["push"] is True

    def test_get_communication_preference_none(self):
        """Kiểm tra lấy sở thích truyền thông khi chưa có."""
        from midicoder.emitters.core.cp49_consent.models import ConsentEngine
        engine = ConsentEngine()
        pref = engine.get_comm_preference("user_001", "tenant_001")
        assert pref is None

    def test_create_erasure_request(self):
        """Kiểm tra tạo yêu cầu xóa dữ liệu mới."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ErasureScope,
            ErasureStatus,
        )
        engine = ConsentEngine()
        request = engine.create_erasure_request(
            user_id="user_001",
            tenant_id="tenant_001",
            scope=ErasureScope.ALL_PERSONAL_DATA,
            reason="Yêu cầu xóa toàn bộ",
        )
        assert request.user_id == "user_001"
        assert request.scope == ErasureScope.ALL_PERSONAL_DATA
        assert request.status == ErasureStatus.PENDING
        assert request.reason == "Yêu cầu xóa toàn bộ"
        assert request.request_id in engine.erasure_requests

    def test_process_erasure_approve(self):
        """Kiểm tra phê duyệt yêu cầu xóa dữ liệu."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ErasureScope,
            ErasureStatus,
        )
        engine = ConsentEngine()
        request = engine.create_erasure_request(
            user_id="user_001",
            tenant_id="tenant_001",
            scope=ErasureScope.CONSENT_DATA,
        )
        result = engine.process_erasure_request(request.request_id, "approve")
        assert result.status == ErasureStatus.APPROVED

    def test_process_erasure_reject(self):
        """Kiểm tra từ chối yêu cầu xóa dữ liệu."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ErasureScope,
            ErasureStatus,
        )
        engine = ConsentEngine()
        request = engine.create_erasure_request(
            user_id="user_001",
            tenant_id="tenant_001",
            scope=ErasureScope.COMMUNICATION_DATA,
        )
        result = engine.process_erasure_request(request.request_id, "reject")
        assert result.status == ErasureStatus.REJECTED

    def test_process_erasure_review(self):
        """Kiểm tra chuyển yêu cầu xóa sang trạng thái đang xem xét."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ErasureScope,
            ErasureStatus,
        )
        engine = ConsentEngine()
        request = engine.create_erasure_request(
            user_id="user_001",
            tenant_id="tenant_001",
            scope=ErasureScope.ALL_PERSONAL_DATA,
        )
        result = engine.process_erasure_request(request.request_id, "review")
        assert result.status == ErasureStatus.REVIEWING

    def test_process_erasure_full_lifecycle(self):
        """Kiểm tra toàn bộ vòng đời yêu cầu xóa: PENDING -> APPROVED -> PROCESSING -> COMPLETED."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ErasureScope,
            ErasureStatus,
        )
        engine = ConsentEngine()
        request = engine.create_erasure_request(
            user_id="user_001",
            tenant_id="tenant_001",
            scope=ErasureScope.ALL_PERSONAL_DATA,
        )
        assert request.status == ErasureStatus.PENDING
        engine.process_erasure_request(request.request_id, "approve")
        assert engine.erasure_requests[request.request_id].status == ErasureStatus.APPROVED
        engine.process_erasure_request(request.request_id, "approve")
        assert engine.erasure_requests[request.request_id].status == ErasureStatus.PROCESSING
        engine.process_erasure_request(request.request_id, "complete")
        assert engine.erasure_requests[request.request_id].status == ErasureStatus.COMPLETED
        assert engine.erasure_requests[request.request_id].completed_at is not None

    def test_process_erasure_nonexistent_raises(self):
        """Kiểm tra xử lý yêu cầu xóa không tồn tại sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import ConsentEngine
        engine = ConsentEngine()
        with pytest.raises(MidicoderError):
            engine.process_erasure_request("nonexistent", "approve")

    def test_get_tenant_consent_stats(self):
        """Kiểm tra lấy thống kê consent của tenant."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ConsentPurpose,
            ConsentCategory,
        )
        engine = ConsentEngine()
        rec1 = engine.grant_consent(
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
        )
        engine.grant_consent(
            user_id="user_002",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.MARKETING,
            category=ConsentCategory.ADVERTISING,
        )
        engine.revoke_consent(rec1.record_id)
        stats = engine.get_tenant_consent_stats("tenant_001")
        assert stats["total"] == 2
        assert stats["active"] == 1
        assert stats["revoked"] == 1

    def test_get_tenant_consent_stats_empty(self):
        """Kiểm tra thống kê tenant khi không có bản ghi."""
        from midicoder.emitters.core.cp49_consent.models import ConsentEngine
        engine = ConsentEngine()
        stats = engine.get_tenant_consent_stats("empty_tenant")
        assert stats["total"] == 0
        assert stats["active"] == 0
        assert stats["revoked"] == 0
        assert stats["expired"] == 0
        assert stats["pending_renewal"] == 0

    def test_check_expired_consents_no_expiry(self):
        """Kiểm tra kiểm tra hết hạn khi chưa có consent hết hạn."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ConsentPurpose,
            ConsentCategory,
        )
        engine = ConsentEngine()
        engine.grant_consent(
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
        )
        expired = engine.check_expired_consents()
        assert expired == []

    def test_add_policy(self):
        """Kiểm tra thêm chính sách consent mới."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ConsentPolicy,
            ConsentPurpose,
            ConsentCategory,
        )
        engine = ConsentEngine()
        policy = ConsentPolicy(
            policy_id="pol_eng",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
            expiry_days=90,
        )
        policy_id = engine.add_policy(policy)
        assert policy_id == "pol_eng"
        assert "pol_eng" in engine.policies

    def test_add_duplicate_policy_raises(self):
        """Kiểm tra thêm chính sách trùng policy_id sẽ ném lỗi."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ConsentPolicy,
            ConsentPurpose,
            ConsentCategory,
        )
        engine = ConsentEngine()
        policy = ConsentPolicy(
            policy_id="pol_dup",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
        )
        engine.add_policy(policy)
        with pytest.raises(MidicoderError):
            engine.add_policy(policy)

    def test_get_policy(self):
        """Kiểm tra lấy chính sách theo ID."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ConsentPolicy,
            ConsentPurpose,
            ConsentCategory,
        )
        engine = ConsentEngine()
        policy = ConsentPolicy(
            policy_id="pol_get",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.MARKETING,
            category=ConsentCategory.ADVERTISING,
        )
        engine.add_policy(policy)
        fetched = engine.get_policy("pol_get")
        assert fetched is not None
        assert fetched.policy_id == "pol_get"

    def test_get_policy_not_found(self):
        """Kiểm tra lấy chính sách không tồn tại trả về None."""
        from midicoder.emitters.core.cp49_consent.models import ConsentEngine
        engine = ConsentEngine()
        fetched = engine.get_policy("nonexistent")
        assert fetched is None

    def test_get_policies_for_tenant(self):
        """Kiểm tra lấy tất cả chính sách của tenant."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ConsentPolicy,
            ConsentPurpose,
            ConsentCategory,
        )
        engine = ConsentEngine()
        engine.add_policy(ConsentPolicy(
            policy_id="pol_t1",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
        ))
        engine.add_policy(ConsentPolicy(
            policy_id="pol_t2",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.MARKETING,
            category=ConsentCategory.ADVERTISING,
        ))
        engine.add_policy(ConsentPolicy(
            policy_id="pol_t3",
            tenant_id="tenant_002",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
        ))
        policies = engine.get_policies_for_tenant("tenant_001")
        assert len(policies) == 2

    def test_full_consent_workflow(self):
        """Kiểm tra workflow đầy đủ: cấp consent, kiểm tra, rút consent, kiểm tra lại."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ConsentPurpose,
            ConsentCategory,
        )
        engine = ConsentEngine()
        # Cấp consent
        record = engine.grant_consent(
            user_id="user_001",
            tenant_id="tenant_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
        )
        # Kiểm tra có consent
        assert engine.check_consent("user_001", "tenant_001", ConsentPurpose.ANALYTICS) is True
        # Rút consent
        engine.revoke_consent(record.record_id, reason="Thay đổi ý")
        # Kiểm tra không còn consent
        assert engine.check_consent("user_001", "tenant_001", ConsentPurpose.ANALYTICS) is False

    def test_cookie_necessary_cannot_be_false(self):
        """Kiểm tra cookie necessary luôn được gán True qua engine."""
        from midicoder.emitters.core.cp49_consent.models import ConsentEngine
        engine = ConsentEngine()
        pref = engine.set_cookie_preference(
            user_id="user_001",
            tenant_id="tenant_001",
            categories={"necessary": False, "analytics": True},
        )
        assert pref.categories["necessary"] is True

    def test_update_cookie_preference_overwrites(self):
        """Kiểm tra cập nhật sở thích cookie ghi đè giá trị cũ."""
        from midicoder.emitters.core.cp49_consent.models import ConsentEngine
        engine = ConsentEngine()
        engine.set_cookie_preference(
            user_id="user_001",
            tenant_id="tenant_001",
            categories={"analytics": True},
        )
        engine.set_cookie_preference(
            user_id="user_001",
            tenant_id="tenant_001",
            categories={"analytics": False, "advertising": True},
        )
        pref = engine.get_cookie_preference("user_001", "tenant_001")
        assert pref.categories["analytics"] is False
        assert pref.categories["advertising"] is True

    def test_erasure_different_scopes(self):
        """Kiểm tra tạo nhiều yêu cầu xóa với các phạm vi khác nhau."""
        from midicoder.emitters.core.cp49_consent.models import (
            ConsentEngine,
            ErasureScope,
        )
        engine = ConsentEngine()
        req1 = engine.create_erasure_request(
            user_id="user_001",
            tenant_id="tenant_001",
            scope=ErasureScope.CONSENT_DATA,
        )
        req2 = engine.create_erasure_request(
            user_id="user_001",
            tenant_id="tenant_001",
            scope=ErasureScope.SPECIFIC_ENTITIES,
        )
        assert req1.scope == ErasureScope.CONSENT_DATA
        assert req2.scope == ErasureScope.SPECIFIC_ENTITIES
        assert req1.request_id != req2.request_id
