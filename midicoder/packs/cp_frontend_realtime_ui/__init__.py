"""
CP22 — Real-time UI Generator

Cung cấp:
- RealtimeParser: parse CP05 events → channel subscriptions
- RealtimeComponentEmitter: sinh React components/hooks
- AngularRealtimeEmitter: sinh Angular components/services
- Models: ChannelSpec, PresenceState, LiveFeedEntry, WidgetConfig
"""

from midicoder.packs.cp_frontend_realtime_ui.models import (
    ChannelSpec,
    LiveFeedEntry,
    PresenceState,
    PresenceStatus,
    SUPPORTED_UI_FRAMEWORKS,
    TransportType,
    WidgetConfig,
    WidgetType,
)
from midicoder.packs.cp_frontend_realtime_ui.parser import RealtimeParser
from midicoder.packs.cp_frontend_realtime_ui.react import (
    GeneratedFile as ReactGeneratedFile,
)
from midicoder.packs.cp_frontend_realtime_ui.react import RealtimeComponentEmitter

try:
    from midicoder.packs.cp_frontend_realtime_ui.angular import (
        AngularRealtimeEmitter,
        GeneratedFile as AngularGeneratedFile,
    )
except ImportError:
    AngularRealtimeEmitter = None  # type: ignore
    AngularGeneratedFile = None  # type: ignore

__all__ = [
    # Models
    "SUPPORTED_UI_FRAMEWORKS",
    "TransportType",
    "WidgetType",
    "PresenceStatus",
    "ChannelSpec",
    "PresenceState",
    "LiveFeedEntry",
    "WidgetConfig",
    # Parser
    "RealtimeParser",
    # React
    "RealtimeComponentEmitter",
    "ReactGeneratedFile",
    # Angular
    "AngularRealtimeEmitter",
    "AngularGeneratedFile",
]
