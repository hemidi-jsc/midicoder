# coding: utf-8
"""
Kiểm tra mô-đun recipes cho CP49 — Consent & Preference Management.

Bao gồm các tests cho:
- RecipeOutput: tạo, fields, loại IR
- basic_consent_recipe: tên, mô tả, 2 policies, 1 consent, cookie_categories,
  comm_channels rỗng, use_audit/retention True
- full_consent_recipe: tên, mô tả, 5 policies, 3 consents (active/revoked/expired),
  cookie_categories, comm_channels 4 kênh
- to_dict roundtrip

Lưu ý: gdpr_erasure delegate đến CP47 (Data Retention & Lifecycle Management).
"""

from __future__ import annotations

import pytest

from midicoder.emitters.core.cp49_consent.recipes import (
    RecipeOutput,
    basic_consent_recipe,
    full_consent_recipe,
)
from midicoder.emitters.core.cp49_consent.parser import ConsentIR
from midicoder.emitters.core.cp49_consent.models import ConsentPurpose, ConsentCategory, ConsentStatus


# ===========================================================================
# Test RecipeOutput
# ===========================================================================


class TestRecipeOutput:
    """Kiểm tra RecipeOutput — dataclass cơ bản."""

    def test_returns_recipe_output(self):
        """Kiểm tra recipe trả về đối tượng RecipeOutput."""
        output = basic_consent_recipe()
        assert isinstance(output, RecipeOutput)

    def test_ir_is_consent_ir(self):
        """Kiểm tra ir là đối tượng ConsentIR."""
        output = basic_consent_recipe()
        assert type(output.ir).__name__ == "ConsentIR"

    def test_has_name_and_description(self):
        """Kiểm tra RecipeOutput có name và description không rỗng."""
        output = basic_consent_recipe()
        assert output.name
        assert output.description


# ===========================================================================
# Test basic_consent_recipe
# ===========================================================================


class TestBasicConsentRecipe:
    """Kiểm tra basic_consent_recipe — 2 policies, 1 consent, cookie config cơ bản."""

    def test_name_is_basic_consent(self):
        """Kiểm tra tên recipe là basic_consent."""
        output = basic_consent_recipe()
        assert output.name == "basic_consent"

    def test_has_description(self):
        """Kiểm tra recipe có mô tả không rỗng."""
        output = basic_consent_recipe()
        assert output.description
        assert len(output.description) > 10

    def test_has_two_policies(self):
        """Kiểm tra có đúng 2 chính sách consent."""
        output = basic_consent_recipe()
        assert len(output.ir.policies) == 2

    def test_first_policy_id_is_analytics(self):
        """Kiểm tra policy đầu tiên là pol_analytics_001."""
        output = basic_consent_recipe()
        assert output.ir.policies[0].policy_id == "pol_analytics_001"
        assert output.ir.policies[0].purpose == ConsentPurpose.ANALYTICS
        assert output.ir.policies[0].category == ConsentCategory.ANALYTICS

    def test_second_policy_id_is_marketing(self):
        """Kiểm tra policy thứ hai là pol_marketing_001."""
        output = basic_consent_recipe()
        assert output.ir.policies[1].policy_id == "pol_marketing_001"
        assert output.ir.policies[1].purpose == ConsentPurpose.MARKETING
        assert output.ir.policies[1].category == ConsentCategory.ADVERTISING

    def test_policies_not_mandatory(self):
        """Kiểm tra cả 2 policy đều không bắt buộc."""
        output = basic_consent_recipe()
        assert output.ir.policies[0].is_mandatory is False
        assert output.ir.policies[1].is_mandatory is False

    def test_has_one_consent(self):
        """Kiểm tra có đúng 1 bản ghi consent."""
        output = basic_consent_recipe()
        assert len(output.ir.consents) == 1

    def test_consent_id_is_consent_001(self):
        """Kiểm tra record_id là consent_001."""
        output = basic_consent_recipe()
        assert output.ir.consents[0].record_id == "consent_001"

    def test_consent_user_id_is_user_001(self):
        """Kiểm tra user_id là user_001."""
        output = basic_consent_recipe()
        assert output.ir.consents[0].user_id == "user_001"

    def test_consent_tenant_id_is_tenant_001(self):
        """Kiểm tra tenant_id là tenant_001."""
        output = basic_consent_recipe()
        assert output.ir.consents[0].tenant_id == "tenant_001"

    def test_consent_purpose_is_analytics(self):
        """Kiểm tra purpose là ANALYTICS."""
        output = basic_consent_recipe()
        assert output.ir.consents[0].purpose == ConsentPurpose.ANALYTICS

    def test_consent_status_is_active(self):
        """Kiểm tra status là ACTIVE."""
        output = basic_consent_recipe()
        assert output.ir.consents[0].status == ConsentStatus.ACTIVE

    def test_cookie_categories_has_four_items(self):
        """Kiểm tra cookie_categories có 4 danh mục."""
        output = basic_consent_recipe()
        assert len(output.ir.cookie_categories) == 4
        assert "necessary" in output.ir.cookie_categories
        assert "functional" in output.ir.cookie_categories
        assert "analytics" in output.ir.cookie_categories
        assert "advertising" in output.ir.cookie_categories

    def test_comm_channels_is_empty(self):
        """Kiểm tra comm_channels là danh sách rỗng."""
        output = basic_consent_recipe()
        assert output.ir.comm_channels == []

    def test_use_audit_is_true(self):
        """Kiểm tra use_audit là True."""
        output = basic_consent_recipe()
        assert output.ir.use_audit is True

    def test_use_retention_is_true(self):
        """Kiểm tra use_retention là True."""
        output = basic_consent_recipe()
        assert output.ir.use_retention is True

    def test_policy_ids_are_unique(self):
        """Kiểm tra các policy_id là duy nhất."""
        output = basic_consent_recipe()
        ids = [p.policy_id for p in output.ir.policies]
        assert len(ids) == len(set(ids))

    def test_consent_has_ip_and_user_agent(self):
        """Kiểm tra consent có ip_address và user_agent."""
        output = basic_consent_recipe()
        assert output.ir.consents[0].ip_address == "192.168.1.100"
        assert output.ir.consents[0].user_agent


# ===========================================================================
# Test full_consent_recipe
# ===========================================================================


class TestFullConsentRecipe:
    """Kiểm tra full_consent_recipe — 5 policies, 3 consents, full config."""

    def test_name_is_full_consent(self):
        """Kiểm tra tên recipe là full_consent."""
        output = full_consent_recipe()
        assert output.name == "full_consent"

    def test_has_description(self):
        """Kiểm tra recipe có mô tả không rỗng."""
        output = full_consent_recipe()
        assert output.description
        assert len(output.description) > 10

    def test_has_five_policies(self):
        """Kiểm tra có đúng 5 chính sách consent."""
        output = full_consent_recipe()
        assert len(output.ir.policies) == 5

    def test_first_policy_is_essential_mandatory(self):
        """Kiểm tra policy đầu tiên là ESSENTIAL/NECESSARY và bắt buộc."""
        output = full_consent_recipe()
        pol = output.ir.policies[0]
        assert pol.policy_id == "pol_essential_001"
        assert pol.purpose == ConsentPurpose.ESSENTIAL
        assert pol.category == ConsentCategory.NECESSARY
        assert pol.is_mandatory is True

    def test_second_policy_is_analytics(self):
        """Kiểm tra policy thứ hai là ANALYTICS/ANALYTICS."""
        output = full_consent_recipe()
        pol = output.ir.policies[1]
        assert pol.policy_id == "pol_analytics_001"
        assert pol.purpose == ConsentPurpose.ANALYTICS
        assert pol.category == ConsentCategory.ANALYTICS
        assert pol.is_mandatory is False

    def test_third_policy_is_marketing(self):
        """Kiểm tra policy thứ ba là MARKETING/ADVERTISING."""
        output = full_consent_recipe()
        pol = output.ir.policies[2]
        assert pol.policy_id == "pol_marketing_001"
        assert pol.purpose == ConsentPurpose.MARKETING
        assert pol.category == ConsentCategory.ADVERTISING

    def test_fourth_policy_is_thirdparty(self):
        """Kiểm tra policy thứ tư là THIRD_PARTY/FUNCTIONAL."""
        output = full_consent_recipe()
        pol = output.ir.policies[3]
        assert pol.policy_id == "pol_thirdparty_001"
        assert pol.purpose == ConsentPurpose.THIRD_PARTY
        assert pol.category == ConsentCategory.FUNCTIONAL

    def test_fifth_policy_is_dataproc(self):
        """Kiểm tra policy thứ năm là DATA_PROCESSING/FUNCTIONAL."""
        output = full_consent_recipe()
        pol = output.ir.policies[4]
        assert pol.policy_id == "pol_dataproc_001"
        assert pol.purpose == ConsentPurpose.DATA_PROCESSING
        assert pol.category == ConsentCategory.FUNCTIONAL

    def test_has_three_consents(self):
        """Kiểm tra có đúng 3 bản ghi consent."""
        output = full_consent_recipe()
        assert len(output.ir.consents) == 3

    def test_first_consent_is_active(self):
        """Kiểm tra consent đầu tiên có status ACTIVE."""
        output = full_consent_recipe()
        rec = output.ir.consents[0]
        assert rec.record_id == "consent_full_001"
        assert rec.status == ConsentStatus.ACTIVE

    def test_second_consent_is_revoked(self):
        """Kiểm tra consent thứ hai có status REVOKED."""
        output = full_consent_recipe()
        rec = output.ir.consents[1]
        assert rec.record_id == "consent_full_002"
        assert rec.status == ConsentStatus.REVOKED

    def test_third_consent_is_expired(self):
        """Kiểm tra consent thứ ba có status EXPIRED."""
        output = full_consent_recipe()
        rec = output.ir.consents[2]
        assert rec.record_id == "consent_full_003"
        assert rec.status == ConsentStatus.EXPIRED

    def test_all_statuses_present(self):
        """Kiểm tra 3 trạng thái consent đều có mặt: ACTIVE, REVOKED, EXPIRED."""
        output = full_consent_recipe()
        statuses = {c.status for c in output.ir.consents}
        assert ConsentStatus.ACTIVE in statuses
        assert ConsentStatus.REVOKED in statuses
        assert ConsentStatus.EXPIRED in statuses

    def test_first_consent_purpose_is_analytics(self):
        """Kiểm tra consent đầu tiên có purpose ANALYTICS."""
        output = full_consent_recipe()
        assert output.ir.consents[0].purpose == ConsentPurpose.ANALYTICS

    def test_second_consent_purpose_is_marketing(self):
        """Kiểm tra consent thứ hai có purpose MARKETING."""
        output = full_consent_recipe()
        assert output.ir.consents[1].purpose == ConsentPurpose.MARKETING

    def test_third_consent_purpose_is_dataproc(self):
        """Kiểm tra consent thứ ba có purpose DATA_PROCESSING."""
        output = full_consent_recipe()
        assert output.ir.consents[2].purpose == ConsentPurpose.DATA_PROCESSING

    def test_cookie_categories_has_four_items(self):
        """Kiểm tra cookie_categories có 4 danh mục."""
        output = full_consent_recipe()
        assert len(output.ir.cookie_categories) == 4
        assert "necessary" in output.ir.cookie_categories
        assert "functional" in output.ir.cookie_categories
        assert "analytics" in output.ir.cookie_categories
        assert "advertising" in output.ir.cookie_categories

    def test_comm_channels_has_four_channels(self):
        """Kiểm tra comm_channels có 4 kênh truyền thông."""
        output = full_consent_recipe()
        assert len(output.ir.comm_channels) == 4
        assert "email" in output.ir.comm_channels
        assert "sms" in output.ir.comm_channels
        assert "push" in output.ir.comm_channels
        assert "webhook" in output.ir.comm_channels

    def test_use_audit_is_true(self):
        """Kiểm tra use_audit là True."""
        output = full_consent_recipe()
        assert output.ir.use_audit is True

    def test_use_retention_is_true(self):
        """Kiểm tra use_retention là True."""
        output = full_consent_recipe()
        assert output.ir.use_retention is True

    def test_policy_ids_are_unique(self):
        """Kiểm tra các policy_id là duy nhất."""
        output = full_consent_recipe()
        ids = [p.policy_id for p in output.ir.policies]
        assert len(ids) == len(set(ids))

    def test_consent_record_ids_are_unique(self):
        """Kiểm tra các record_id là duy nhất."""
        output = full_consent_recipe()
        ids = [c.record_id for c in output.ir.consents]
        assert len(ids) == len(set(ids))

    def test_only_essential_policy_is_mandatory(self):
        """Kiểm tra chỉ có policy ESSENTIAL là bắt buộc."""
        output = full_consent_recipe()
        mandatory = [p for p in output.ir.policies if p.is_mandatory]
        assert len(mandatory) == 1
        assert mandatory[0].policy_id == "pol_essential_001"

    def test_revoked_consent_has_revoked_at(self):
        """Kiểm tra consent bị thu hồi có revoked_at."""
        output = full_consent_recipe()
        rec = output.ir.consents[1]
        assert rec.status == ConsentStatus.REVOKED
        assert rec.revoked_at is not None

    def test_consents_have_different_users(self):
        """Kiểm tra consent thứ ba thuộc user_002, khác 2 consent đầu."""
        output = full_consent_recipe()
        assert output.ir.consents[0].user_id == "user_001"
        assert output.ir.consents[1].user_id == "user_001"
        assert output.ir.consents[2].user_id == "user_002"


# ===========================================================================
# Test Recipe to_dict roundtrip
# ===========================================================================


class TestRecipeToDict:
    """Kiểm tra to_dict và from_dict roundtrip cho các recipe."""

    def test_basic_recipe_ir_to_dict(self):
        """Kiểm tra basic recipe chuyển sang dict có đúng cấu trúc."""
        output = basic_consent_recipe()
        d = output.ir.to_dict()
        assert "policies" in d
        assert "consents" in d
        assert "cookie_categories" in d
        assert "comm_channels" in d
        assert "use_audit" in d
        assert "use_retention" in d
        assert len(d["policies"]) == 2
        assert len(d["consents"]) == 1
        assert d["comm_channels"] == []

    def test_basic_recipe_ir_from_dict_roundtrip(self):
        """Kiểm tra basic recipe roundtrip to_dict -> from_dict giữ nguyên dữ liệu."""
        output = basic_consent_recipe()
        d = output.ir.to_dict()
        restored = ConsentIR.from_dict(d)
        assert len(restored.policies) == 2
        assert len(restored.consents) == 1
        assert restored.policies[0].policy_id == "pol_analytics_001"
        assert restored.consents[0].record_id == "consent_001"
        assert restored.use_audit is True
        assert restored.use_retention is True

    def test_full_recipe_ir_to_dict(self):
        """Kiểm tra full recipe chuyển sang dict có đầy đủ dữ liệu."""
        output = full_consent_recipe()
        d = output.ir.to_dict()
        assert len(d["policies"]) == 5
        assert len(d["consents"]) == 3
        assert len(d["cookie_categories"]) == 4
        assert len(d["comm_channels"]) == 4
        assert d["use_audit"] is True
        assert d["use_retention"] is True

    def test_full_recipe_ir_from_dict_roundtrip(self):
        """Kiểm tra full recipe roundtrip to_dict -> from_dict giữ nguyên dữ liệu."""
        output = full_consent_recipe()
        d = output.ir.to_dict()
        restored = ConsentIR.from_dict(d)
        assert len(restored.policies) == 5
        assert len(restored.consents) == 3
        assert restored.policies[0].policy_id == "pol_essential_001"
        assert restored.policies[0].is_mandatory is True
        assert restored.consents[0].record_id == "consent_full_001"
        assert restored.consents[1].record_id == "consent_full_002"
        assert restored.consents[2].record_id == "consent_full_003"

    def test_roundtrip_preserves_policy_details(self):
        """Kiểm tra roundtrip giữ nguyên chi tiết policy."""
        output = full_consent_recipe()
        d = output.ir.to_dict()
        restored = ConsentIR.from_dict(d)
        # Policy đầu: essential/necessary/mandatory
        assert restored.policies[0].purpose == ConsentPurpose.ESSENTIAL
        assert restored.policies[0].category == ConsentCategory.NECESSARY
        assert restored.policies[0].is_mandatory is True
        # Policy thứ ba: marketing/advertising
        assert restored.policies[2].purpose == ConsentPurpose.MARKETING
        assert restored.policies[2].category == ConsentCategory.ADVERTISING

    def test_roundtrip_preserves_consent_statuses(self):
        """Kiểm tra roundtrip giữ nguyên trạng thái consent."""
        output = full_consent_recipe()
        d = output.ir.to_dict()
        restored = ConsentIR.from_dict(d)
        assert restored.consents[0].status == ConsentStatus.ACTIVE
        assert restored.consents[1].status == ConsentStatus.REVOKED
        assert restored.consents[2].status == ConsentStatus.EXPIRED

    def test_roundtrip_preserves_cookie_and_comm(self):
        """Kiểm tra roundtrip giữ nguyên cookie_categories và comm_channels."""
        output = full_consent_recipe()
        d = output.ir.to_dict()
        restored = ConsentIR.from_dict(d)
        assert restored.cookie_categories == ["necessary", "functional", "analytics", "advertising"]
        assert restored.comm_channels == ["email", "sms", "push", "webhook"]

