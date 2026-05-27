"""
Mô-đun Notification Effect.

Cung cấp:
- NotificationEffect: Effect cho sending notifications

Author: Midicoder Team
Version: 1.0.0
"""

from typing import Any

from .base import EffectResult


class NotificationEffect:
    """
    Effect executor cho notifications.

    Send notifications (email, sms, push) khi transition fire.

    Usage:
        effect = NotificationEffect(channel="email")
        result = effect.execute(data={"recipient": "user@test.com"})
    """

    def __init__(
        self,
        channel: str | None = None,
        template: str | None = None,
        recipient_field: str | None = None,
    ) -> None:
        self.channel = channel
        self.template = template
        self.recipient_field = recipient_field

    def execute(self, data: dict[str, Any]) -> EffectResult:
        """
        Execute notification effect.

        Args:
            data: Data dictionary

        Returns:
            EffectResult với send result
        """
        # TODO: Integrate với CP12 Notification
        channel = self.channel
        template = self.template

        # Send notification (placeholder)
        return EffectResult.success(
            data={"notification": {"channel": channel, "template": template, **data}},
            message=f"Sent notification via {channel} with template {template}",
        )