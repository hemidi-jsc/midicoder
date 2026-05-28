# coding: utf-8
"""
Kiểm tra mô-đun parser cho CP49 — Consent & Preference Management.

Bao gồm các tests cho:
- ConsentIR: empty, with data, to_dict/from_dict roundtrip
- parse_consent_policies: từ key 'consent_policies', từ key 'policies', empty, alias
- parse_consent_records: từ key 'consent_records', từ key 'consents', empty, alias
- parse_cookie_config: từ key 'cookie_config', từ key 'cookies', list, dict
- parse_comm_config: từ key 'communication_preferences', từ key 'comm_config', list, dict
- parse_to_ir: full data, empty data, partial data, defaults

Lưu ý: gdpr_erasure delegate đến CP47 (Data Retention & Lifecycle Management).
"""

from __future__ import annotations

import pytest

from midicoder.packs.cp_full_consent.parser import (
    ConsentIR,
    parse_consent_policies,
    parse_consent_records,
    parse_cookie_config,
    parse_comm_config,
    parse_to_ir,
)
from midicoder.packs.cp_full_consent.models import (
    ConsentCategory,
    ConsentPolicy,
    ConsentPurpose,
    ConsentRecord,
    ConsentStatus,
)


# ===========================================================================
# Test ConsentIR
# ===========================================================================


class TestConsentIR:
    """Kiểm tra ConsentIR — khởi tạo, serialize, deserialize."""

    def test_consent_ir_empty(self):
        """Kiểm tra ConsentIR rỗng có các danh sách rỗng và flags mặc định."""
        ir = ConsentIR()
        assert len(ir.policies) == 0
        assert len(ir.consents) == 0
        assert len(ir.cookie_categories) == 0
        assert len(ir.comm_channels) == 0
        assert ir.use_audit is True
        assert ir.use_retention is True

    def test_consent_ir_to_dict_empty(self):
        """Kiểm tra chuyển ConsentIR rỗng sang dict."""
        ir = ConsentIR()
        d = ir.to_dict()
        assert d["policies"] == []
        assert d["consents"] == []
        assert d["cookie_categories"] == []
        assert d["comm_channels"] == []
        assert d["use_audit"] is True
        assert d["use_retention"] is True

    def test_consent_ir_with_data(self):
        """Kiểm tra ConsentIR có dữ liệu đầy đủ các loại đối tượng."""
        policy = ConsentPolicy(
            policy_id="pol_001",
            tenant_id="t_001",
            purpose=ConsentPurpose.ANALYTICS,
            category=ConsentCategory.ANALYTICS,
            is_mandatory=False,
            description="Chính sách phân tích",
            expiry_days=180,
        )
        record = ConsentRecord(
            record_id="rec_001",
            user_id="u_001",
            tenant_id="t_001",
            purpose=ConsentPurpose.MARKETING,
            category=ConsentCategory.ADVERTISING,
            status=ConsentStatus.ACTIVE,
        )
        ir = ConsentIR(
            policies=[policy],
            consents=[record],
            cookie_categories=["necessary", "functional"],
            comm_channels=["email", "sms"],
            use_audit=False,
            use_retention=False,
        )
        assert len(ir.policies) == 1
        assert len(ir.consents) == 1
        assert ir.cookie_categories == ["necessary", "functional"]
        assert ir.comm_channels == ["email", "sms"]
        assert ir.use_audit is False
        assert ir.use_retention is False

    def test_consent_ir_to_dict_with_data(self):
        """Kiểm tra chuyển ConsentIR có dữ liệu sang dict đúng."""
        policy = ConsentPolicy(
            policy_id="pol_dict",
            tenant_id="t_dict",
            purpose=ConsentPurpose.ESSENTIAL,
            category=ConsentCategory.NECESSARY,
        )
        record = ConsentRecord(
            record_id="rec_dict",
            user_id="u_dict",
            tenant_id="t_dict",
            purpose=ConsentPurpose.ESSENTIAL,
            category=ConsentCategory.NECESSARY,
        )
        ir = ConsentIR(
            policies=[policy],
            consents=[record],
            cookie_categories=["analytics"],
            comm_channels=["push"],
            use_audit=True,
            use_retention=False,
        )
        d = ir.to_dict()
        assert len(d["policies"]) == 1
        assert d["policies"][0]["policy_id"] == "pol_dict"
        assert len(d["consents"]) == 1
        assert d["consents"][0]["record_id"] == "rec_dict"
        assert d["cookie_categories"] == ["analytics"]
        assert d["comm_channels"] == ["push"]
        assert d["use_audit"] is True
        assert d["use_retention"] is False

    def test_consent_ir_from_dict_roundtrip(self):
        """Kiểm tra ConsentIR to_dict rồi from_dict giữ nguyên dữ liệu."""
        policy = ConsentPolicy(
            policy_id="pol_rt",
            tenant_id="t_rt",
            purpose=ConsentPurpose.FUNCTIONAL,
            category=ConsentCategory.FUNCTIONAL,
            is_mandatory=True,
            expiry_days=90,
        )
        record = ConsentRecord(
            record_id="rec_rt",
            user_id="u_rt",
            tenant_id="t_rt",
            purpose=ConsentPurpose.DATA_PROCESSING,
            category=ConsentCategory.ANALYTICS,
            status=ConsentStatus.REVOKED,
        )
        ir = ConsentIR(
            policies=[policy],
            consents=[record],
            cookie_categories=["necessary", "advertising"],
            comm_channels=["email", "webhook"],
            use_audit=False,
            use_retention=True,
        )
        d = ir.to_dict()
        restored = ConsentIR.from_dict(d)
        assert len(restored.policies) == 1
        assert restored.policies[0].policy_id == "pol_rt"
        assert len(restored.consents) == 1
        assert restored.consents[0].record_id == "rec_rt"
        assert restored.cookie_categories == ["necessary", "advertising"]
        assert restored.comm_channels == ["email", "webhook"]
        assert restored.use_audit is False
        assert restored.use_retention is True


# ===========================================================================
# Test parse_consent_policies
# ===========================================================================


class TestParseConsentPolicies:
    """Kiểm tra parse_consent_policies — nhiều key, alias, rỗng."""

    def test_parse_from_consent_policies_key(self):
        """Kiểm tra parse từ key chính 'consent_policies'."""
        data = {
            "consent_policies": [
                {
                    "policy_id": "pol_001",
                    "tenant_id": "t_001",
                    "purpose": "analytics",
                }
            ]
        }
        result = parse_consent_policies(data)
        assert len(result) == 1
        assert result[0].policy_id == "pol_001"
        assert result[0].tenant_id == "t_001"

    def test_parse_from_policies_alias_key(self):
        """Kiểm tra parse từ key alias 'policies'."""
        data = {
            "policies": [
                {
                    "policy_id": "pol_002",
                    "tenant_id": "t_002",
                    "purpose": "marketing",
                }
            ]
        }
        result = parse_consent_policies(data)
        assert len(result) == 1
        assert result[0].policy_id == "pol_002"
        assert result[0].tenant_id == "t_002"

    def test_parse_empty(self):
        """Kiểm tra parse dữ liệu rỗng trả về danh sách rỗng."""
        data = {}
        result = parse_consent_policies(data)
        assert len(result) == 0

    def test_parse_with_all_fields(self):
        """Kiểm tra parse với tất cả các trường đầy đủ."""
        data = {
            "consent_policies": [
                {
                    "policy_id": "pol_full",
                    "tenant_id": "t_full",
                    "purpose": "data_processing",
                    "category": "analytics",
                    "is_mandatory": False,
                    "description": "Chính sách xử lý dữ liệu đầy đủ",
                    "expiry_days": 180,
                    "renewal_reminder_days": 14,
                }
            ]
        }
        result = parse_consent_policies(data)
        assert len(result) == 1
        p = result[0]
        assert p.policy_id == "pol_full"
        assert p.tenant_id == "t_full"
        assert p.purpose == ConsentPurpose.DATA_PROCESSING
        assert p.category == ConsentCategory.ANALYTICS
        assert p.is_mandatory is False
        assert p.description == "Chính sách xử lý dữ liệu đầy đủ"
        assert p.expiry_days == 180
        assert p.renewal_reminder_days == 14

    def test_parse_with_id_alias(self):
        """Kiểm tra alias key 'id' thay cho 'policy_id'."""
        data = {
            "consent_policies": [
                {
                    "id": "pol_alias_id",
                    "tenant_id": "t_alias",
                }
            ]
        }
        result = parse_consent_policies(data)
        assert result[0].policy_id == "pol_alias_id"

    def test_parse_with_tenant_alias(self):
        """Kiểm tra alias key 'tenant' thay cho 'tenant_id'."""
        data = {
            "consent_policies": [
                {
                    "policy_id": "pol_tenant_alias",
                    "tenant": "tenant_alias_val",
                }
            ]
        }
        result = parse_consent_policies(data)
        assert result[0].tenant_id == "tenant_alias_val"

    def test_parse_with_defaults(self):
        """Kiểm tra các giá trị mặc định khi trường không được cung cấp."""
        data = {
            "consent_policies": [
                {
                    "policy_id": "pol_default",
                    "tenant_id": "t_default",
                }
            ]
        }
        result = parse_consent_policies(data)
        assert result[0].purpose == ConsentPurpose.ESSENTIAL
        assert result[0].category == ConsentCategory.NECESSARY
        assert result[0].is_mandatory is False
        assert result[0].expiry_days == 365
        assert result[0].renewal_reminder_days == 30

    def test_parse_multiple_policies(self):
        """Kiểm tra parse nhiều chính sách consent cùng lúc."""
        data = {
            "consent_policies": [
                {
                    "policy_id": "pol_001",
                    "tenant_id": "t_001",
                    "purpose": "essential",
                },
                {
                    "policy_id": "pol_002",
                    "tenant_id": "t_001",
                    "purpose": "marketing",
                },
                {
                    "policy_id": "pol_003",
                    "tenant_id": "t_002",
                    "purpose": "analytics",
                },
            ]
        }
        result = parse_consent_policies(data)
        assert len(result) == 3
        assert result[0].policy_id == "pol_001"
        assert result[1].policy_id == "pol_002"
        assert result[2].policy_id == "pol_003"


# ===========================================================================
# Test parse_consent_records
# ===========================================================================


class TestParseConsentRecords:
    """Kiểm tra parse_consent_records — nhiều key, alias, rỗng."""

    def test_parse_from_consent_records_key(self):
        """Kiểm tra parse từ key chính 'consent_records'."""
        data = {
            "consent_records": [
                {
                    "record_id": "rec_001",
                    "user_id": "u_001",
                    "tenant_id": "t_001",
                    "purpose": "analytics",
                }
            ]
        }
        result = parse_consent_records(data)
        assert len(result) == 1
        assert result[0].record_id == "rec_001"
        assert result[0].user_id == "u_001"

    def test_parse_from_consents_alias_key(self):
        """Kiểm tra parse từ key alias 'consents'."""
        data = {
            "consents": [
                {
                    "record_id": "rec_002",
                    "user_id": "u_002",
                    "tenant_id": "t_002",
                    "purpose": "marketing",
                }
            ]
        }
        result = parse_consent_records(data)
        assert len(result) == 1
        assert result[0].record_id == "rec_002"
        assert result[0].user_id == "u_002"

    def test_parse_empty(self):
        """Kiểm tra parse dữ liệu rỗng trả về danh sách rỗng."""
        data = {}
        result = parse_consent_records(data)
        assert len(result) == 0

    def test_parse_with_all_fields(self):
        """Kiểm tra parse với tất cả các trường đầy đủ."""
        data = {
            "consent_records": [
                {
                    "record_id": "rec_full",
                    "user_id": "u_full",
                    "tenant_id": "t_full",
                    "purpose": "third_party",
                    "category": "advertising",
                    "status": "revoked",
                    "ip_address": "192.168.1.1",
                    "user_agent": "Mozilla/5.0",
                    "metadata": {"source": "web_portal"},
                }
            ]
        }
        result = parse_consent_records(data)
        assert len(result) == 1
        r = result[0]
        assert r.record_id == "rec_full"
        assert r.user_id == "u_full"
        assert r.tenant_id == "t_full"
        assert r.purpose == ConsentPurpose.THIRD_PARTY
        assert r.category == ConsentCategory.ADVERTISING
        assert r.status == ConsentStatus.REVOKED
        assert r.ip_address == "192.168.1.1"
        assert r.user_agent == "Mozilla/5.0"
        assert r.metadata == {"source": "web_portal"}

    def test_parse_with_id_alias(self):
        """Kiểm tra alias key 'id' thay cho 'record_id'."""
        data = {
            "consent_records": [
                {
                    "id": "rec_alias_id",
                    "user_id": "u_alias",
                    "tenant_id": "t_alias",
                }
            ]
        }
        result = parse_consent_records(data)
        assert result[0].record_id == "rec_alias_id"

    def test_parse_with_user_alias(self):
        """Kiểm tra alias key 'user' thay cho 'user_id'."""
        data = {
            "consent_records": [
                {
                    "record_id": "rec_user_alias",
                    "user": "user_alias_val",
                    "tenant_id": "t_alias",
                }
            ]
        }
        result = parse_consent_records(data)
        assert result[0].user_id == "user_alias_val"

    def test_parse_with_tenant_alias(self):
        """Kiểm tra alias key 'tenant' thay cho 'tenant_id'."""
        data = {
            "consent_records": [
                {
                    "record_id": "rec_tenant_alias",
                    "user_id": "u_alias",
                    "tenant": "tenant_alias_val",
                }
            ]
        }
        result = parse_consent_records(data)
        assert result[0].tenant_id == "tenant_alias_val"

    def test_parse_with_defaults(self):
        """Kiểm tra các giá trị mặc định khi trường không được cung cấp."""
        data = {
            "consent_records": [
                {
                    "record_id": "rec_default",
                    "user_id": "u_default",
                    "tenant_id": "t_default",
                }
            ]
        }
        result = parse_consent_records(data)
        assert result[0].purpose == ConsentPurpose.ESSENTIAL
        assert result[0].category == ConsentCategory.NECESSARY
        assert result[0].status == ConsentStatus.ACTIVE
        assert result[0].ip_address == ""
        assert result[0].user_agent == ""
        assert result[0].metadata == {}

    def test_parse_multiple_records(self):
        """Kiểm tra parse nhiều bản ghi consent cùng lúc."""
        data = {
            "consent_records": [
                {
                    "record_id": "rec_001",
                    "user_id": "u_001",
                    "tenant_id": "t_001",
                    "purpose": "essential",
                },
                {
                    "record_id": "rec_002",
                    "user_id": "u_001",
                    "tenant_id": "t_001",
                    "purpose": "marketing",
                    "status": "revoked",
                },
            ]
        }
        result = parse_consent_records(data)
        assert len(result) == 2
        assert result[0].record_id == "rec_001"
        assert result[0].status == ConsentStatus.ACTIVE
        assert result[1].record_id == "rec_002"
        assert result[1].status == ConsentStatus.REVOKED


# ===========================================================================
# Test parse_cookie_config
# ===========================================================================


class TestParseCookieConfig:
    """Kiểm tra parse_cookie_config — list, dict, rỗng."""

    def test_parse_from_cookie_config_key(self):
        """Kiểm tra parse từ key chính 'cookie_config'."""
        data = {
            "cookie_config": {
                "necessary": {"enabled": True},
                "analytics": {"enabled": False},
            }
        }
        result = parse_cookie_config(data)
        assert len(result) == 2
        assert "necessary" in result
        assert "analytics" in result

    def test_parse_from_cookies_alias_key(self):
        """Kiểm tra parse từ key alias 'cookies'."""
        data = {
            "cookies": {
                "functional": {"enabled": True},
                "advertising": {"enabled": False},
            }
        }
        result = parse_cookie_config(data)
        assert len(result) == 2
        assert "functional" in result
        assert "advertising" in result

    def test_parse_empty(self):
        """Kiểm tra parse dữ liệu rỗng trả về danh sách rỗng."""
        data = {}
        result = parse_cookie_config(data)
        assert len(result) == 0

    def test_parse_list_input(self):
        """Kiểm tra parse đầu vào là danh sách trả về danh sách trực tiếp."""
        data = {
            "cookie_config": ["necessary", "functional", "analytics"]
        }
        result = parse_cookie_config(data)
        assert len(result) == 3
        assert result[0] == "necessary"
        assert result[1] == "functional"
        assert result[2] == "analytics"

    def test_parse_dict_with_valid_categories(self):
        """Kiểm tra parse dict chỉ lấy các danh mục cookie hợp lệ."""
        data = {
            "cookie_config": {
                "necessary": {"enabled": True},
                "functional": {"enabled": True},
                "unknown_category": {"enabled": True},
            }
        }
        result = parse_cookie_config(data)
        assert "necessary" in result
        assert "functional" in result
        assert "unknown_category" not in result

    def test_parse_all_cookie_categories(self):
        """Kiểm tra parse tất cả danh mục cookie hợp lệ."""
        data = {
            "cookie_config": {
                "necessary": True,
                "functional": True,
                "analytics": True,
                "advertising": True,
            }
        }
        result = parse_cookie_config(data)
        assert len(result) == 4
        assert "necessary" in result
        assert "functional" in result
        assert "analytics" in result
        assert "advertising" in result


# ===========================================================================
# Test parse_comm_config
# ===========================================================================


class TestParseCommConfig:
    """Kiểm tra parse_comm_config — list, dict, rỗng."""

    def test_parse_from_communication_preferences_key(self):
        """Kiểm tra parse từ key chính 'communication_preferences'."""
        data = {
            "communication_preferences": {
                "email": {"enabled": True},
                "sms": {"enabled": False},
            }
        }
        result = parse_comm_config(data)
        assert len(result) == 2
        assert "email" in result
        assert "sms" in result

    def test_parse_from_comm_config_alias_key(self):
        """Kiểm tra parse từ key alias 'comm_config'."""
        data = {
            "comm_config": {
                "push": {"enabled": True},
                "webhook": {"enabled": False},
            }
        }
        result = parse_comm_config(data)
        assert len(result) == 2
        assert "push" in result
        assert "webhook" in result

    def test_parse_empty(self):
        """Kiểm tra parse dữ liệu rỗng trả về danh sách rỗng."""
        data = {}
        result = parse_comm_config(data)
        assert len(result) == 0

    def test_parse_list_input(self):
        """Kiểm tra parse đầu vào là danh sách trả về danh sách trực tiếp."""
        data = {
            "communication_preferences": ["email", "push"]
        }
        result = parse_comm_config(data)
        assert len(result) == 2
        assert result[0] == "email"
        assert result[1] == "push"

    def test_parse_dict_with_valid_channels(self):
        """Kiểm tra parse dict chỉ lấy các kênh truyền thông hợp lệ."""
        data = {
            "communication_preferences": {
                "email": {"enabled": True},
                "unknown_channel": {"enabled": True},
            }
        }
        result = parse_comm_config(data)
        assert "email" in result
        assert "unknown_channel" not in result

    def test_parse_all_comm_channels(self):
        """Kiểm tra parse tất cả kênh truyền thông hợp lệ."""
        data = {
            "communication_preferences": {
                "email": True,
                "sms": True,
                "push": True,
                "webhook": True,
            }
        }
        result = parse_comm_config(data)
        assert len(result) == 4
        assert "email" in result
        assert "sms" in result
        assert "push" in result
        assert "webhook" in result


# ===========================================================================
# Test parse_to_ir
# ===========================================================================


class TestParseToIR:
    """Kiểm tra parse_to_ir — DSL dict sang ConsentIR."""

    def test_parse_full_data_to_ir(self):
        """Kiểm tra parse toàn bộ dữ liệu DSL sang ConsentIR."""
        data = {
            "consent_policies": [
                {
                    "policy_id": "pol_ir",
                    "tenant_id": "t_ir",
                    "purpose": "analytics",
                    "category": "analytics",
                }
            ],
            "consent_records": [
                {
                    "record_id": "rec_ir",
                    "user_id": "u_ir",
                    "tenant_id": "t_ir",
                    "purpose": "analytics",
                }
            ],
            "cookie_config": {
                "necessary": True,
                "analytics": True,
            },
            "communication_preferences": {
                "email": True,
                "sms": False,
            },
            "use_audit": True,
            "use_retention": False,
        }
        ir = parse_to_ir(data)
        assert len(ir.policies) == 1
        assert len(ir.consents) == 1
        assert len(ir.cookie_categories) == 2
        assert len(ir.comm_channels) == 2
        assert ir.policies[0].policy_id == "pol_ir"
        assert ir.consents[0].record_id == "rec_ir"
        assert ir.use_audit is True
        assert ir.use_retention is False

    def test_parse_empty_data(self):
        """Kiểm tra parse dữ liệu rỗng trả về ConsentIR rỗng."""
        data = {}
        ir = parse_to_ir(data)
        assert len(ir.policies) == 0
        assert len(ir.consents) == 0
        assert len(ir.cookie_categories) == 0
        assert len(ir.comm_channels) == 0
        assert ir.use_audit is True
        assert ir.use_retention is True

    def test_parse_only_policies(self):
        """Kiểm tra parse chỉ có chính sách, các thành phần khác rỗng."""
        data = {
            "consent_policies": [
                {
                    "policy_id": "pol_only",
                    "tenant_id": "t_only",
                }
            ]
        }
        ir = parse_to_ir(data)
        assert len(ir.policies) == 1
        assert len(ir.consents) == 0
        assert len(ir.cookie_categories) == 0
        assert len(ir.comm_channels) == 0

    def test_parse_only_records(self):
        """Kiểm tra parse chỉ có bản ghi consent, các thành phần khác rỗng."""
        data = {
            "consent_records": [
                {
                    "record_id": "rec_only",
                    "user_id": "u_only",
                    "tenant_id": "t_only",
                }
            ]
        }
        ir = parse_to_ir(data)
        assert len(ir.policies) == 0
        assert len(ir.consents) == 1
        assert ir.consents[0].record_id == "rec_only"

    def test_parse_with_cookie_and_comm_only(self):
        """Kiểm tra parse chỉ có cookie và truyền thông, các thành phần khác rỗng."""
        data = {
            "cookie_config": ["necessary", "functional"],
            "communication_preferences": ["email", "push"],
        }
        ir = parse_to_ir(data)
        assert len(ir.policies) == 0
        assert len(ir.consents) == 0
        assert ir.cookie_categories == ["necessary", "functional"]
        assert ir.comm_channels == ["email", "push"]

    def test_parse_with_alias_keys(self):
        """Kiểm tra parse sử dụng tất cả key alias."""
        data = {
            "policies": [
                {
                    "policy_id": "pol_alias",
                    "tenant_id": "t_alias",
                }
            ],
            "consents": [
                {
                    "record_id": "rec_alias",
                    "user_id": "u_alias",
                    "tenant_id": "t_alias",
                }
            ],
            "cookies": {
                "necessary": True,
            },
            "comm_config": {
                "email": True,
            },
        }
        ir = parse_to_ir(data)
        assert len(ir.policies) == 1
        assert len(ir.consents) == 1
        assert len(ir.cookie_categories) == 1
        assert len(ir.comm_channels) == 1

    def test_parse_defaults_audit_retention(self):
        """Kiểm tra use_audit và use_retention mặc định là True khi không khai báo."""
        data = {
            "consent_policies": [
                {
                    "policy_id": "pol_default",
                    "tenant_id": "t_default",
                }
            ]
        }
        ir = parse_to_ir(data)
        assert ir.use_audit is True
        assert ir.use_retention is True

    def test_parse_explicit_false_audit_retention(self):
        """Kiểm tra use_audit và use_retention đặt rõ là False."""
        data = {
            "use_audit": False,
            "use_retention": False,
        }
        ir = parse_to_ir(data)
        assert ir.use_audit is False
        assert ir.use_retention is False
