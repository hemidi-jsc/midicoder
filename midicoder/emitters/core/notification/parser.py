"""
Notification Parser Module.

Module này parse YAML notification definitions thành các models:
- parse_notifications(): Parse notification templates từ YAML
- parse_channels(): Parse channel configuration từ YAML
- parse_providers(): Parse provider configuration từ YAML

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from midicoder.emitters.core.notification.models import (
    NotificationChannel,
    NotificationProvider,
    NotificationTemplate,
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

    Example:
        >>> data = {
        ...     "notifications": [
        ...         {"template_id": "welcome", "channel": "email", "subject": "Chào {{name}}"}
        ...     ]
        ... }
        >>> templates = parse_notifications(data)
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

    Example:
        >>> data = {
        ...     "channels": {
        ...         "email": {"rate_limit": 100, "enabled": True},
        ...         "sms": {"rate_limit": 10, "enabled": True}
        ...     }
        ... }
        >>> config = parse_channels(data)
    """
    result: dict[str, Any] = {}
    channels_data = data.get("channels", {})

    for channel_name, channel_config in channels_data.items():
        if isinstance(channel_config, dict):
            result[channel_name] = channel_config
        else:
            # Nếu không phải dict, treat như enabled flag
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

    Example:
        >>> data = {
        ...     "providers": [
        ...         {"provider_id": "sendgrid", "channel": "email", "priority": 1}
        ...     ]
        ... }
        >>> providers = parse_providers(data)
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
# Exports
# ============================================================================

__all__ = [
    "parse_notifications",
    "parse_channels",
    "parse_providers",
]