# coding: utf-8
"""
Mô-đun recipes cho CP37 — Feature Flags & Dynamic Config.

Cung cấp các recipe patterns để generate feature flags, A/B experiments,
và dynamic configs theo common use cases.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp_full_service_discovery.models import (
    ABExperiment,
    ABVariant,
    ConfigScope,
    ConfigValueType,
    ConditionType,
    DynamicConfig,
    FeatureFlag,
    FlagVariantType,
    TargetingRule,
)
from midicoder.packs.cp_full_service_discovery.parser import FeatureFlagIR


@dataclass
class RecipeOutput:
    """Kết quả của recipe.

    Attributes:
        name: Tên recipe
        description: Mô tả recipe
        ir: FeatureFlagIR kết quả
    """
    name: str
    description: str
    ir: FeatureFlagIR


def simple_flags_recipe() -> RecipeOutput:
    """Recipe: On/off flags global, không targeting, eval từ cache.

    Tạo các feature flags cơ bản cho use case bật/tắt tính năng
    toàn cục. Phù hợp cho MVP và rapid prototyping.

    Returns:
        RecipeOutput với các default flags
    """
    flags = [
        FeatureFlag(
            flag_key="dark_mode",
            name="Dark Mode",
            description="Bật/tắt giao diện dark mode",
            variant_type=FlagVariantType.BOOLEAN,
            default_enabled=False,
            is_active=True,
        ),
        FeatureFlag(
            flag_key="new_checkout_flow",
            name="New Checkout Flow",
            description="Dùng flow checkout mới",
            variant_type=FlagVariantType.BOOLEAN,
            default_enabled=False,
            is_active=True,
        ),
        FeatureFlag(
            flag_key="advanced_search",
            name="Advanced Search",
            description="Bật tính năng tìm kiếm nâng cao",
            variant_type=FlagVariantType.BOOLEAN,
            default_enabled=True,
            is_active=True,
        ),
    ]

    configs = [
        DynamicConfig(
            config_key="feature_flags.cache_ttl",
            value=300,
            value_type=ConfigValueType.NUMBER,
            scope=ConfigScope.GLOBAL,
        ),
        DynamicConfig(
            config_key="feature_flags.eval_timeout_ms",
            value=50,
            value_type=ConfigValueType.NUMBER,
            scope=ConfigScope.GLOBAL,
        ),
    ]

    return RecipeOutput(
        name="simple_flags",
        description="On/off flags global, không targeting, eval từ cache",
        ir=FeatureFlagIR(flags=flags, configs=configs),
    )


def ab_testing_recipe() -> RecipeOutput:
    """Recipe: Experiment engine + deterministic assignment + traffic control.

    Tạo A/B experiment templates cho UI và feature testing.
    Hỗ trợ deterministic assignment và traffic percentage control.

    Returns:
        RecipeOutput với experiment templates
    """
    experiments = [
        ABExperiment(
            experiment_key="checkout_button_color",
            name="Checkout Button Color",
            description="Test màu sắc nút checkout để tối ưu conversion",
            variants=[
                ABVariant(variant_key="control", name="Xanh dương (mặc định)", weight=50.0),
                ABVariant(variant_key="variant_a", name="Xanh lá cây", weight=50.0),
            ],
            is_active=True,
            traffic_percentage=50.0,
            success_metric="conversion_rate",
        ),
        ABExperiment(
            experiment_key="pricing_display",
            name="Pricing Display Format",
            description="Test format hiển thị giá cả",
            variants=[
                ABVariant(variant_key="control", name="Hiển thị đầy đủ", weight=33.34),
                ABVariant(variant_key="variant_a", name="Chỉ hiển thị từ", weight=33.33),
                ABVariant(variant_key="variant_b", name="Hiển thị theo package", weight=33.33),
            ],
            is_active=True,
            traffic_percentage=100.0,
            success_metric="click_through_rate",
        ),
    ]

    flags = [
        FeatureFlag(
            flag_key="ab_experiment_engine",
            name="A/B Experiment Engine",
            description="Bật/tắt experiment engine",
            variant_type=FlagVariantType.BOOLEAN,
            default_enabled=True,
            is_active=True,
        ),
    ]

    configs = [
        DynamicConfig(
            config_key="ab_testing.assignment_cache_ttl",
            value=86400,
            value_type=ConfigValueType.NUMBER,
            scope=ConfigScope.GLOBAL,
        ),
        DynamicConfig(
            config_key="ab_testing.default_traffic_percentage",
            value=50.0,
            value_type=ConfigValueType.NUMBER,
            scope=ConfigScope.GLOBAL,
        ),
    ]

    return RecipeOutput(
        name="ab_testing",
        description="Experiment engine + deterministic assignment + traffic control",
        ir=FeatureFlagIR(flags=flags, experiments=experiments, configs=configs),
    )


def dynamic_config_recipe() -> RecipeOutput:
    """Recipe: Hierarchical config + tenant/environment scope + audit trail.

    Tạo cấu trúc dynamic config hierarchical cho tenant-aware applications.
    Hỗ trợ scope theo global, tenant, environment.

    Returns:
        RecipeOutput với hierarchical configs
    """
    configs = [
        # Global configs
        DynamicConfig(
            config_key="app.rate_limit.requests_per_minute",
            value=1000,
            value_type=ConfigValueType.NUMBER,
            scope=ConfigScope.GLOBAL,
        ),
        DynamicConfig(
            config_key="app.max_upload_size_mb",
            value=50,
            value_type=ConfigValueType.NUMBER,
            scope=ConfigScope.GLOBAL,
        ),
        DynamicConfig(
            config_key="app.maintenance_mode",
            value=False,
            value_type=ConfigValueType.BOOLEAN,
            scope=ConfigScope.GLOBAL,
        ),
        DynamicConfig(
            config_key="app.supported_locales",
            value=["vi", "en", "ja"],
            value_type=ConfigValueType.ARRAY,
            scope=ConfigScope.GLOBAL,
        ),
        # Tenant-scoped configs
        DynamicConfig(
            config_key="tenant.branding.primary_color",
            value="#0070F3",
            value_type=ConfigValueType.STRING,
            scope=ConfigScope.TENANT,
            tenant_id="tenant_placeholder",
        ),
        # Environment-scoped configs
        DynamicConfig(
            config_key="env.debug.enabled",
            value=True,
            value_type=ConfigValueType.BOOLEAN,
            scope=ConfigScope.ENVIRONMENT,
            environment="development",
        ),
        DynamicConfig(
            config_key="env.debug.enabled",
            value=False,
            value_type=ConfigValueType.BOOLEAN,
            scope=ConfigScope.ENVIRONMENT,
            environment="production",
        ),
    ]

    flags = [
        FeatureFlag(
            flag_key="dynamic_config_realtime_sync",
            name="Dynamic Config Realtime Sync",
            description="Bật/tắt sync realtime config thay đổi",
            variant_type=FlagVariantType.BOOLEAN,
            default_enabled=True,
            is_active=True,
        ),
    ]

    return RecipeOutput(
        name="dynamic_config",
        description="Hierarchical config + tenant/environment scope + audit trail",
        ir=FeatureFlagIR(flags=flags, configs=configs),
    )


__all__ = [
    "RecipeOutput",
    "simple_flags_recipe",
    "ab_testing_recipe",
    "dynamic_config_recipe",
]
