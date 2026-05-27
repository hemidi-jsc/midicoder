# coding: utf-8
"""
Mô-đun recipes cho CP62 — Mobile Backend (FCM/APNs Push, Deep Linking, Mobile Auth, OTA).

Cung cấp các recipe functions để build MobileIR từ DSL dict,
tương tự pattern của CP45 payment recipes.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp62_mobile_backend.models import (
    DeepLinkRoute,
    DevicePlatform,
    DeviceRegistration,
    MobileAuthProvider,
    MobileAuthType,
    OTAPlatform,
    OTAUpdateConfig,
    PushNotificationConfig,
    PushPlatform,
)
from midicoder.packs.cp62_mobile_backend.parser import MobileIR


@dataclass
class RecipeOutput:
    """Kết quả từ recipe.

    Attributes:
        ir: MobileIR đã build từ recipe
        message: Thông điệp mô tả kết quả
    """
    ir: MobileIR
    message: str = ""


def fcm_push_notification_recipe(
    server_key_ref: str = "",
    topic: str = "default",
    bundle_id: str = "",
) -> RecipeOutput:
    """Recipe cho FCM push notification service.

    Tạo cấu hình push notification cho Firebase Cloud Messaging (FCM)
    với hỗ trợ topic-based và multicast messaging.

    Args:
        server_key_ref: Reference đến FCM server key trong secret store
        topic: Topic mặc định cho push notification
        bundle_id: Package name của ứng dụng Android

    Returns:
        RecipeOutput với MobileIR chứa FCM push config
    """
    push_config = PushNotificationConfig(
        id="fcm_push",
        platform=PushPlatform.FCM,
        server_key_ref=server_key_ref,
        bundle_id=bundle_id,
        topic=topic,
        sound=True,
        badge=True,
        data_payload=True,
    )
    ir = MobileIR(push_configs=[push_config])
    return RecipeOutput(
        ir=ir,
        message=f"FCM push notification config đã tạo với topic: {topic}",
    )


def apns_push_notification_recipe(
    key_id: str = "",
    team_id: str = "",
    bundle_id: str = "",
    topic: str = "",
) -> RecipeOutput:
    """Recipe cho APNs push notification service.

    Tạo cấu hình push notification cho Apple Push Notification Service (APNs)
    với PKCS12 certificate hoặc Apple Push Key (.p8).

    Args:
        key_id: APNs Key ID từ Apple Developer Portal
        team_id: Team ID của Apple Developer
        bundle_id: Bundle ID của ứng dụng iOS
        topic: Topic mặc định (thường bằng bundle_id)

    Returns:
        RecipeOutput với MobileIR chứa APNs push config
    """
    if not topic:
        topic = bundle_id
    push_config = PushNotificationConfig(
        id="apns_push",
        platform=PushPlatform.APNS,
        server_key_ref=key_id,
        bundle_id=bundle_id,
        topic=topic,
        sound=True,
        badge=True,
        data_payload=True,
    )
    ir = MobileIR(push_configs=[push_config])
    return RecipeOutput(
        ir=ir,
        message=f"APNs push notification config đã tạo với bundle: {bundle_id}",
    )


def deep_linking_recipe(
    routes: list[dict[str, Any]] | None = None,
    universal_links: bool = True,
) -> RecipeOutput:
    """Recipe cho deep linking setup.

    Tạo cấu hình deep linking với Universal Link (iOS) và App Link (Android).
    Hỗ trợ path pattern matching và auth requirement.

    Args:
        routes: Danh sách route definitions với path_pattern, target_screen,
                auth_required, params, fallback_url
        universal_links: Có bật Universal Link/App Link không

    Returns:
        RecipeOutput với MobileIR chứa deep link routes
    """
    if routes is None:
        routes = [
            {
                "id": "deep_link_home",
                "path_pattern": "/",
                "target_screen": "HomeScreen",
                "auth_required": False,
            },
            {
                "id": "deep_link_profile",
                "path_pattern": "/profile/{user_id}",
                "target_screen": "ProfileScreen",
                "auth_required": True,
                "params": {"user_id": "string"},
            },
        ]

    deep_links = []
    for route_data in routes:
        deep_links.append(DeepLinkRoute(
            id=route_data.get("id", ""),
            path_pattern=route_data.get("path_pattern", ""),
            target_screen=route_data.get("target_screen", ""),
            auth_required=route_data.get("auth_required", False),
            params=route_data.get("params", {}),
            fallback_url=route_data.get("fallback_url", ""),
            universal_link_enabled=universal_links,
        ))

    ir = MobileIR(deep_links=deep_links)
    return RecipeOutput(
        ir=ir,
        message=f"Deep linking config đã tạo với {len(deep_links)} routes",
    )


def mobile_auth_recipe(
    providers: list[dict[str, Any]] | None = None,
) -> RecipeOutput:
    """Recipe cho OAuth2 mobile authentication.

    Tạo cấu hình mobile auth với các OAuth2 providers phổ biến
    (Apple, Google, Facebook).

    Args:
        providers: Danh sách auth provider definitions với type,
                   client_id_ref, client_secret_ref, redirect_uri, scopes

    Returns:
        RecipeOutput với MobileIR chứa auth providers
    """
    if providers is None:
        providers = [
            {
                "id": "google_auth",
                "type": "google",
                "scopes": ["openid", "email", "profile"],
            },
            {
                "id": "apple_auth",
                "type": "apple",
                "scopes": ["name", "email"],
            },
        ]

    auth_providers = []
    for provider_data in providers:
        auth_providers.append(MobileAuthProvider(
            id=provider_data.get("id", ""),
            type=MobileAuthType(provider_data.get("type", "google")),
            client_id_ref=provider_data.get("client_id_ref", ""),
            client_secret_ref=provider_data.get("client_secret_ref", ""),
            redirect_uri=provider_data.get("redirect_uri", ""),
            scopes=provider_data.get("scopes", []),
        ))

    ir = MobileIR(auth_providers=auth_providers)
    return RecipeOutput(
        ir=ir,
        message=f"Mobile auth config đã tạo với {len(auth_providers)} providers",
    )


def ota_update_recipe(
    platform: str = "both",
    forced_update: bool = False,
    minimum_version: str = "",
    release_notes_url: str = "",
    download_url: str = "",
    rollout_percentage: int = 100,
) -> RecipeOutput:
    """Recipe cho OTA update configuration.

    Tạo cấu hình over-the-air update với forced update, version check,
    và gradual rollout.

    Args:
        platform: Nền tảng mục tiêu (ios|android|both)
        forced_update: Có bắt buộc update không
        minimum_version: Phiên bản tối thiểu yêu cầu
        release_notes_url: URL đến release notes
        download_url: URL download bản cập nhật
        rollout_percentage: Phần trăm rollout (1-100)

    Returns:
        RecipeOutput với MobileIR chứa OTA update config
    """
    ota_config = OTAUpdateConfig(
        id="ota_update",
        platform=OTAPlatform(platform),
        forced_update=forced_update,
        minimum_version=minimum_version,
        release_notes_url=release_notes_url,
        download_url=download_url,
        rollout_percentage=rollout_percentage,
    )
    ir = MobileIR(ota_configs=[ota_config])
    return RecipeOutput(
        ir=ir,
        message=f"OTA update config đã tạo cho {platform} (rollout: {rollout_percentage}%)",
    )


def full_mobile_backend_recipe(
    push_platform: str = "both",
    enable_deep_linking: bool = True,
    enable_mobile_auth: bool = True,
    enable_ota: bool = True,
) -> RecipeOutput:
    """Recipe full mobile backend.

    Tạo cấu hình đầy đủ cho mobile backend bao gồm push notification,
    deep linking, mobile auth, và OTA update.

    Args:
        push_platform: Nền tảng push notification (fcm|apns|both)
        enable_deep_linking: Có bật deep linking không
        enable_mobile_auth: Có bật mobile auth không
        enable_ota: Có bật OTA update không

    Returns:
        RecipeOutput với MobileIR chứa toàn bộ cấu hình mobile backend
    """
    push_configs = []
    deep_links = []
    auth_providers = []
    ota_configs = []

    # Push notification
    if push_platform == "fcm" or push_platform == "both":
        push_configs.append(PushNotificationConfig(
            id="fcm_push",
            platform=PushPlatform.FCM,
            sound=True,
            badge=True,
            data_payload=True,
        ))
    if push_platform == "apns" or push_platform == "both":
        push_configs.append(PushNotificationConfig(
            id="apns_push",
            platform=PushPlatform.APNS,
            sound=True,
            badge=True,
            data_payload=True,
        ))

    # Deep linking
    if enable_deep_linking:
        deep_links.append(DeepLinkRoute(
            id="deep_link_home",
            path_pattern="/",
            target_screen="HomeScreen",
            auth_required=False,
            universal_link_enabled=True,
        ))

    # Mobile auth
    if enable_mobile_auth:
        auth_providers.append(MobileAuthProvider(
            id="google_auth",
            type=MobileAuthType.GOOGLE,
            scopes=["openid", "email", "profile"],
        ))

    # OTA update
    if enable_ota:
        ota_configs.append(OTAUpdateConfig(
            id="ota_update",
            platform=OTAPlatform(push_platform) if push_platform in ("ios", "android", "both") else OTAPlatform.BOTH,
            forced_update=False,
            rollout_percentage=100,
        ))

    ir = MobileIR(
        push_configs=push_configs,
        deep_links=deep_links,
        auth_providers=auth_providers,
        ota_configs=ota_configs,
    )
    return RecipeOutput(
        ir=ir,
        message="Full mobile backend config đã tạo",
    )


__all__ = [
    "RecipeOutput",
    "fcm_push_notification_recipe",
    "apns_push_notification_recipe",
    "deep_linking_recipe",
    "mobile_auth_recipe",
    "ota_update_recipe",
    "full_mobile_backend_recipe",
]
