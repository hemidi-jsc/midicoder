# coding: utf-8
"""
Mô-đun parser cho CP62 — Mobile Backend (FCM/APNs Push, Deep Linking, Mobile Auth, OTA).

Parse DSL dict (từ contract YAML) sang MobileIR — Intermediate Representation
cho push notification configs, deep link routes, mobile auth providers,
OTA update configs, và device registrations.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from midicoder.emitters.core.cp62_mobile_backend.models import (
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


@dataclass
class MobileIR:
    """Intermediate Representation cho CP62.

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
        """Chuyển MobileIR sang dict."""
        return {
            "push_configs": [p.to_dict() for p in self.push_configs],
            "deep_links": [d.to_dict() for d in self.deep_links],
            "auth_providers": [a.to_dict() for a in self.auth_providers],
            "ota_configs": [o.to_dict() for o in self.ota_configs],
            "devices": [d.to_dict() for d in self.devices],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MobileIR":
        """Tạo MobileIR từ dict."""
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
    """Parse danh sách push notification configs từ DSL dict.

    Args:
        data: DSL dict với key 'push_configs' hoặc 'push_notifications'

    Returns:
        Danh sách PushNotificationConfig
    """
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
    """Parse danh sách deep link routes từ DSL dict.

    Args:
        data: DSL dict với key 'deep_links' hoặc 'deep_linking'

    Returns:
        Danh sách DeepLinkRoute
    """
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
    """Parse danh sách mobile auth providers từ DSL dict.

    Args:
        data: DSL dict với key 'auth_providers' hoặc 'mobile_auth'

    Returns:
        Danh sách MobileAuthProvider
    """
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
    """Parse danh sách OTA update configs từ DSL dict.

    Args:
        data: DSL dict với key 'ota_configs' hoặc 'ota_update'

    Returns:
        Danh sách OTAUpdateConfig
    """
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


def parse_to_ir(data: dict[str, Any]) -> MobileIR:
    """Parse DSL dict thành MobileIR.

    Args:
        data: DSL dict với push_configs, deep_links, auth_providers,
              ota_configs, devices

    Returns:
        MobileIR gom tập tất cả parsed data
    """
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


__all__ = [
    "MobileIR",
    "parse_push_configs",
    "parse_deep_links",
    "parse_auth_providers",
    "parse_ota_configs",
    "parse_to_ir",
]
