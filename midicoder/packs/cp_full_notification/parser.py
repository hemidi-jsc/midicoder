"""
Mô-đun Notification Parser.

Module này parse YAML notification definitions thành các models:
- parse_notifications(): Parse notification templates từ YAML
- parse_channels(): Parse channel configuration từ YAML
- parse_providers(): Parse provider configuration từ YAML
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.packs.cp_full_notification.models import (
    NotificationChannel,
    NotificationProvider,
    NotificationTemplate,
    # Mobile Backend (CP62)
    PushNotificationConfig,
    PushPlatform,
    DeepLinkRoute,
    MobileAuthProvider,
    MobileAuthType,
    OTAUpdateConfig,
    OTAPlatform,
    DeviceRegistration,
    DevicePlatform,
)


# ============================================================================
# Parse Notifications
# ============================================================================


def parse_notifications(data: dict[str, Any]) -> list[NotificationTemplate]:
    """
    Parse notification templates từ YAML data.

    Chuyển đổi danh sách notifications trong YAML data thành
    list của NotificationTemplate objects.

    Args:
        data: Dictionary chứa key "notifications" với list template definitions

    Returns:
        List của NotificationTemplate objects
    """
    templates: list[NotificationTemplate] = []
    notifications_list = data.get("notifications", [])

    for item in notifications_list:
        channel_value = item.get("channel", "email")
        channel = NotificationChannel(channel_value)

        template = NotificationTemplate(
            template_id=item.get("template_id", ""),
            channel=channel,
            subject=item.get("subject", ""),
            body_html=item.get("body_html", ""),
            body_text=item.get("body_text", ""),
            variables=item.get("variables", []),
            locale=item.get("locale", "en"),
        )
        templates.append(template)

    return templates


# ============================================================================
# Parse Channels
# ============================================================================


def parse_channels(data: dict[str, Any]) -> dict[str, Any]:
    """
    Parse channel configuration từ YAML data.

    Chuyển đổi channel definitions trong YAML thành dictionary
    với channel name là key và configuration là value.

    Args:
        data: Dictionary chứa key "channels" với channel configuration

    Returns:
        Dictionary mapping channel name -> configuration dict
    """
    result: dict[str, Any] = {}
    channels_data = data.get("channels", {})

    for channel_name, channel_config in channels_data.items():
        if isinstance(channel_config, dict):
            result[channel_name] = channel_config
        else:
            result[channel_name] = {"enabled": bool(channel_config)}

    return result


# ============================================================================
# Parse Providers
# ============================================================================


def parse_providers(data: dict[str, Any]) -> list[NotificationProvider]:
    """
    Parse provider configuration từ YAML data.

    Chuyển đổi danh sách providers trong YAML thành
    list của NotificationProvider objects, sorted theo priority.

    Args:
        data: Dictionary chứa key "providers" với list provider definitions

    Returns:
        List của NotificationProvider objects (sorted by priority ascending)
    """
    providers: list[NotificationProvider] = []
    providers_list = data.get("providers", [])

    for item in providers_list:
        channel_value = item.get("channel", "email")
        channel = NotificationChannel(channel_value)

        provider = NotificationProvider(
            provider_id=item.get("provider_id", ""),
            channel=channel,
            config=item.get("config", {}),
            enabled=item.get("enabled", True),
            priority=item.get("priority", 99),
        )
        providers.append(provider)

    # Sắp xếp theo priority (nhỏ hơn = ưu tiên hơn)
    providers.sort(key=lambda p: p.priority)

    return providers


# ============================================================================
# Mobile Backend IR + Parsers (from CP62)
# ============================================================================


@dataclass
class MobileIR:
    """Intermediate Representation cho Mobile Backend (CP62).

    Gom tập tất cả cấu hình mobile backend từ DSL, bao gồm
    push notification configs, deep link routes, mobile auth providers,
    OTA update configs, và device registrations.

    Attributes:
        push_configs: Danh sách push notification configurations
        deep_links: Danh sách deep link routes
        auth_providers: Danh sách mobile auth providers
        ota_configs: Danh sách OTA update configurations
        devices: Danh sách device registrations
    """
    push_configs: list[PushNotificationConfig] = field(default_factory=list)
    deep_links: list[DeepLinkRoute] = field(default_factory=list)
    auth_providers: list[MobileAuthProvider] = field(default_factory=list)
    ota_configs: list[OTAUpdateConfig] = field(default_factory=list)
    devices: list[DeviceRegistration] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "push_configs": [p.to_dict() for p in self.push_configs],
            "deep_links": [d.to_dict() for d in self.deep_links],
            "auth_providers": [a.to_dict() for a in self.auth_providers],
            "ota_configs": [o.to_dict() for o in self.ota_configs],
            "devices": [d.to_dict() for d in self.devices],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MobileIR":
        push_configs = [PushNotificationConfig.from_dict(p) for p in data.get("push_configs", [])]
        deep_links = [DeepLinkRoute.from_dict(d) for d in data.get("deep_links", [])]
        auth_providers = [MobileAuthProvider.from_dict(a) for a in data.get("auth_providers", [])]
        ota_configs = [OTAUpdateConfig.from_dict(o) for o in data.get("ota_configs", [])]
        devices = [DeviceRegistration.from_dict(d) for d in data.get("devices", [])]
        return cls(
            push_configs=push_configs,
            deep_links=deep_links,
            auth_providers=auth_providers,
            ota_configs=ota_configs,
            devices=devices,
        )


def parse_push_configs(data: dict[str, Any]) -> list[PushNotificationConfig]:
    """Parse danh sách push notification configs từ DSL dict."""
    raw = data.get("push_configs", data.get("push_notifications", []))
    configs = []
    for p_data in raw:
        configs.append(PushNotificationConfig(
            id=p_data.get("id", ""),
            platform=PushPlatform(p_data.get("platform", "both")),
            server_key_ref=p_data.get("server_key_ref", ""),
            bundle_id=p_data.get("bundle_id", ""),
            topic=p_data.get("topic", ""),
            sound=p_data.get("sound", True),
            badge=p_data.get("badge", True),
            data_payload=p_data.get("data_payload", True),
        ))
    return configs


def parse_deep_links(data: dict[str, Any]) -> list[DeepLinkRoute]:
    """Parse danh sách deep link routes từ DSL dict."""
    raw = data.get("deep_links", data.get("deep_linking", []))
    routes = []
    for d_data in raw:
        routes.append(DeepLinkRoute(
            id=d_data.get("id", ""),
            path_pattern=d_data.get("path_pattern", ""),
            target_screen=d_data.get("target_screen", ""),
            auth_required=d_data.get("auth_required", False),
            params=d_data.get("params", {}),
            fallback_url=d_data.get("fallback_url", ""),
            universal_link_enabled=d_data.get("universal_link_enabled", False),
        ))
    return routes


def parse_auth_providers(data: dict[str, Any]) -> list[MobileAuthProvider]:
    """Parse danh sách mobile auth providers từ DSL dict."""
    raw = data.get("auth_providers", data.get("mobile_auth", []))
    providers = []
    for a_data in raw:
        providers.append(MobileAuthProvider(
            id=a_data.get("id", ""),
            type=MobileAuthType(a_data.get("type", "google")),
            client_id_ref=a_data.get("client_id_ref", ""),
            client_secret_ref=a_data.get("client_secret_ref", ""),
            redirect_uri=a_data.get("redirect_uri", ""),
            scopes=a_data.get("scopes", []),
        ))
    return providers


def parse_ota_configs(data: dict[str, Any]) -> list[OTAUpdateConfig]:
    """Parse danh sách OTA update configs từ DSL dict."""
    raw = data.get("ota_configs", data.get("ota_update", []))
    configs = []
    for o_data in raw:
        configs.append(OTAUpdateConfig(
            id=o_data.get("id", ""),
            platform=OTAPlatform(o_data.get("platform", "both")),
            forced_update=o_data.get("forced_update", False),
            minimum_version=o_data.get("minimum_version", ""),
            release_notes_url=o_data.get("release_notes_url", ""),
            download_url=o_data.get("download_url", ""),
            rollout_percentage=o_data.get("rollout_percentage", 100),
        ))
    return configs


def parse_mobile_to_ir(data: dict[str, Any]) -> MobileIR:
    """Parse DSL dict thành MobileIR."""
    push_configs = parse_push_configs(data)
    deep_links = parse_deep_links(data)
    auth_providers = parse_auth_providers(data)
    ota_configs = parse_ota_configs(data)
    return MobileIR(
        push_configs=push_configs,
        deep_links=deep_links,
        auth_providers=auth_providers,
        ota_configs=ota_configs,
    )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "parse_notifications",
    "parse_channels",
    "parse_providers",
    # Mobile Backend (CP62)
    "MobileIR",
    "parse_push_configs",
    "parse_deep_links",
    "parse_auth_providers",
    "parse_ota_configs",
    "parse_mobile_to_ir",
]
