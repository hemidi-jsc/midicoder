# coding: utf-8
"""
Kiểm tra mô-đun recipes cho CP40 — Webhook & Outbound Integration Hub.

Bao gồm các tests cho:
- RecipeOutput: tạo, fields
- basic_webhook_recipe: name, description, ir.subscriptions, no auth
- event_driven_webhook_recipe: name, description, ir.subscriptions, HMAC auth, Redis URL
- subscription fields: subscription_id, event_type, url hợp lệ, status=ACTIVE
- to_dict roundtrip
"""

from __future__ import annotations

import pytest

from midicoder.packs.cp40_webhook.recipes import (
    RecipeOutput,
    basic_webhook_recipe,
    event_driven_webhook_recipe,
)


# ===========================================================================
# Test RecipeOutput
# ===========================================================================


class TestRecipeOutput:
    """Kiểm tra RecipeOutput — dataclass cơ bản."""

    def test_recipe_output_creation(self):
        from midicoder.packs.cp40_webhook.parser import WebhookIR
        output = RecipeOutput(
            name="test_recipe",
            description="Mô tả test",
            ir=WebhookIR(),
        )
        assert output.name == "test_recipe"
        assert output.description == "Mô tả test"
        assert isinstance(output.ir, WebhookIR)

    def test_recipe_output_ir_is_webhook_ir(self):
        from midicoder.packs.cp40_webhook.parser import WebhookIR
        output = RecipeOutput(
            name="ir_test",
            description="Kiểm tra loại IR",
            ir=WebhookIR(),
        )
        assert type(output.ir).__name__ == "WebhookIR"

    def test_recipe_output_fields_not_empty(self):
        from midicoder.packs.cp40_webhook.parser import WebhookIR
        output = RecipeOutput(
            name="filled_recipe",
            description="Không để trống",
            ir=WebhookIR(redis_url="redis://localhost:6379/0"),
        )
        assert output.name
        assert output.description
        assert output.ir.redis_url == "redis://localhost:6379/0"


# ===========================================================================
# Test basic_webhook_recipe
# ===========================================================================


class TestBasicWebhookRecipe:
    """Kiểm tra basic_webhook_recipe — tên, mô tả, subscriptions, không auth."""

    def test_basic_recipe_name(self):
        output = basic_webhook_recipe()
        assert output.name == "basic_webhook"

    def test_basic_recipe_description(self):
        output = basic_webhook_recipe()
        assert output.description == "Single endpoint, no auth, basic retry"

    def test_basic_recipe_has_two_subscriptions(self):
        output = basic_webhook_recipe()
        assert len(output.ir.subscriptions) == 2

    def test_basic_recipe_no_dispatches(self):
        output = basic_webhook_recipe()
        assert len(output.ir.dispatches) == 0

    def test_basic_recipe_no_redis_url(self):
        output = basic_webhook_recipe()
        assert output.ir.redis_url == ""

    def test_basic_recipe_first_subscription_id(self):
        output = basic_webhook_recipe()
        assert output.ir.subscriptions[0].subscription_id == "wh_basic_001"

    def test_basic_recipe_second_subscription_id(self):
        output = basic_webhook_recipe()
        assert output.ir.subscriptions[1].subscription_id == "wh_basic_002"

    def test_basic_recipe_first_event_type(self):
        output = basic_webhook_recipe()
        assert output.ir.subscriptions[0].event_type == "order.created"

    def test_basic_recipe_second_event_type(self):
        output = basic_webhook_recipe()
        assert output.ir.subscriptions[1].event_type == "customer.created"

    def test_basic_recipe_urls_are_valid_https(self):
        output = basic_webhook_recipe()
        for sub in output.ir.subscriptions:
            assert sub.url.startswith("https://")

    def test_basic_recipe_no_auth(self):
        from midicoder.packs.cp40_webhook.models import WebhookAuthType
        output = basic_webhook_recipe()
        for sub in output.ir.subscriptions:
            assert sub.auth_config.auth_type == WebhookAuthType.NONE

    def test_basic_recipe_default_http_method_post(self):
        output = basic_webhook_recipe()
        for sub in output.ir.subscriptions:
            assert sub.http_method == "POST"

    def test_basic_recipe_active_status(self):
        from midicoder.packs.cp40_webhook.models import WebhookStatus
        output = basic_webhook_recipe()
        for sub in output.ir.subscriptions:
            assert sub.status == WebhookStatus.ACTIVE

    def test_basic_recipe_retry_policy(self):
        output = basic_webhook_recipe()
        for sub in output.ir.subscriptions:
            assert sub.retry_policy["max_retries"] == 3
            assert sub.retry_policy["base_delay"] == 1.0
            assert sub.retry_policy["max_delay"] == 30.0

    def test_basic_recipe_rate_limit(self):
        output = basic_webhook_recipe()
        for sub in output.ir.subscriptions:
            assert sub.rate_limit_rpm == 30

    def test_basic_recipe_has_tags(self):
        output = basic_webhook_recipe()
        assert "basic" in output.ir.subscriptions[0].tags
        assert "order" in output.ir.subscriptions[0].tags
        assert "customer" in output.ir.subscriptions[1].tags

    def test_basic_recipe_payload_template(self):
        output = basic_webhook_recipe()
        template = output.ir.subscriptions[0].payload_template
        assert "event_type" in template
        assert "data" in template

    def test_basic_recipe_tenant_id_is_none(self):
        output = basic_webhook_recipe()
        for sub in output.ir.subscriptions:
            assert sub.tenant_id is None


# ===========================================================================
# Test event_driven_webhook_recipe
# ===========================================================================


class TestEventDrivenWebhookRecipe:
    """Kiểm tra event_driven_webhook_recipe — tên, mô tả, 3 subscriptions, HMAC auth, Redis."""

    def test_event_driven_recipe_name(self):
        output = event_driven_webhook_recipe()
        assert output.name == "event_driven_webhook"

    def test_event_driven_recipe_description(self):
        output = event_driven_webhook_recipe()
        assert output.description == "Multi-subscriber, HMAC auth, Redis queue, exponential backoff"

    def test_event_driven_recipe_has_three_subscriptions(self):
        output = event_driven_webhook_recipe()
        assert len(output.ir.subscriptions) == 3

    def test_event_driven_recipe_redis_url(self):
        output = event_driven_webhook_recipe()
        assert output.ir.redis_url == "redis://localhost:6379/0"

    def test_event_driven_recipe_subscription_ids(self):
        output = event_driven_webhook_recipe()
        ids = [s.subscription_id for s in output.ir.subscriptions]
        assert "wh_event_001" in ids
        assert "wh_event_002" in ids
        assert "wh_event_003" in ids

    def test_event_driven_recipe_event_types(self):
        output = event_driven_webhook_recipe()
        types = [s.event_type for s in output.ir.subscriptions]
        assert "order.created" in types
        assert "order.status_changed" in types
        assert "payment.completed" in types

    def test_event_driven_recipe_first_two_hmac_auth(self):
        from midicoder.packs.cp40_webhook.models import WebhookAuthType
        output = event_driven_webhook_recipe()
        assert output.ir.subscriptions[0].auth_config.auth_type == WebhookAuthType.HMAC
        assert output.ir.subscriptions[1].auth_config.auth_type == WebhookAuthType.HMAC

    def test_event_driven_recipe_third_bearer_auth(self):
        from midicoder.packs.cp40_webhook.models import WebhookAuthType
        output = event_driven_webhook_recipe()
        assert output.ir.subscriptions[2].auth_config.auth_type == WebhookAuthType.BEARER

    def test_event_driven_recipe_hmac_header_name(self):
        output = event_driven_webhook_recipe()
        assert output.ir.subscriptions[0].auth_config.header_name == "X-Webhook-Signature"
        assert output.ir.subscriptions[1].auth_config.header_name == "X-Webhook-Signature"

    def test_event_driven_recipe_hmac_algorithm(self):
        output = event_driven_webhook_recipe()
        assert output.ir.subscriptions[0].auth_config.algorithm == "sha256"

    def test_event_driven_recipe_hmac_secret_not_empty(self):
        output = event_driven_webhook_recipe()
        assert output.ir.subscriptions[0].auth_config.secret
        assert output.ir.subscriptions[1].auth_config.secret

    def test_event_driven_recipe_all_active_status(self):
        from midicoder.packs.cp40_webhook.models import WebhookStatus
        output = event_driven_webhook_recipe()
        for sub in output.ir.subscriptions:
            assert sub.status == WebhookStatus.ACTIVE

    def test_event_driven_recipe_all_valid_urls(self):
        output = event_driven_webhook_recipe()
        for sub in output.ir.subscriptions:
            assert sub.url.startswith("https://")

    def test_event_driven_recipe_all_post_method(self):
        output = event_driven_webhook_recipe()
        for sub in output.ir.subscriptions:
            assert sub.http_method == "POST"

    def test_event_driven_recipe_higher_retry_policy(self):
        output = event_driven_webhook_recipe()
        # wh_event_001 và wh_event_002 có max_retries=5
        assert output.ir.subscriptions[0].retry_policy["max_retries"] == 5
        assert output.ir.subscriptions[0].retry_policy["base_delay"] == 2.0
        assert output.ir.subscriptions[0].retry_policy["max_delay"] == 120.0

    def test_event_driven_recipe_tenant_id_on_first_two(self):
        output = event_driven_webhook_recipe()
        assert output.ir.subscriptions[0].tenant_id == "tenant_main"
        assert output.ir.subscriptions[1].tenant_id == "tenant_main"
        # wh_event_003 không có tenant_id
        assert output.ir.subscriptions[2].tenant_id is None

    def test_event_driven_recipe_tags_contain_event_driven(self):
        output = event_driven_webhook_recipe()
        for sub in output.ir.subscriptions:
            assert "event-driven" in sub.tags

    def test_event_driven_recipe_bearer_secret(self):
        output = event_driven_webhook_recipe()
        assert output.ir.subscriptions[2].auth_config.secret == "bearer_token_placeholder"

    def test_event_driven_recipe_bearer_header_name(self):
        output = event_driven_webhook_recipe()
        assert output.ir.subscriptions[2].auth_config.header_name == "Authorization"

    def test_event_driven_recipe_payment_rate_limit(self):
        output = event_driven_webhook_recipe()
        # wh_event_003 (payment) có rate_limit cao hơn
        assert output.ir.subscriptions[2].rate_limit_rpm == 120


# ===========================================================================
# Test to_dict roundtrip cho recipes
# ===========================================================================


class TestRecipeToDict:
    """Kiểm tra to_dict roundtrip cho các recipe."""

    def test_basic_recipe_to_dict_contains_subscriptions(self):
        output = basic_webhook_recipe()
        d = output.ir.to_dict()
        assert "subscriptions" in d
        assert len(d["subscriptions"]) == 2
        assert d["subscriptions"][0]["subscription_id"] == "wh_basic_001"

    def test_basic_recipe_to_dict_from_dict_roundtrip(self):
        from midicoder.packs.cp40_webhook.parser import WebhookIR
        output = basic_webhook_recipe()
        d = output.ir.to_dict()
        restored = WebhookIR.from_dict(d)
        assert len(restored.subscriptions) == 2
        assert restored.subscriptions[0].subscription_id == "wh_basic_001"
        assert restored.subscriptions[1].subscription_id == "wh_basic_002"

    def test_event_driven_recipe_to_dict_contains_redis_url(self):
        output = event_driven_webhook_recipe()
        d = output.ir.to_dict()
        assert d["redis_url"] == "redis://localhost:6379/0"

    def test_event_driven_recipe_to_dict_from_dict_roundtrip(self):
        from midicoder.packs.cp40_webhook.parser import WebhookIR
        output = event_driven_webhook_recipe()
        d = output.ir.to_dict()
        restored = WebhookIR.from_dict(d)
        assert len(restored.subscriptions) == 3
        assert restored.redis_url == "redis://localhost:6379/0"

    def test_event_driven_recipe_roundtrip_preserves_auth(self):
        from midicoder.packs.cp40_webhook.models import WebhookAuthType
        from midicoder.packs.cp40_webhook.parser import WebhookIR
        output = event_driven_webhook_recipe()
        d = output.ir.to_dict()
        restored = WebhookIR.from_dict(d)
        assert restored.subscriptions[0].auth_config.auth_type == WebhookAuthType.HMAC
        assert restored.subscriptions[2].auth_config.auth_type == WebhookAuthType.BEARER
