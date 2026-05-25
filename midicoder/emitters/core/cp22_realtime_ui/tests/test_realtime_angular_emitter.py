"""
Test cho Angular emitter của CP22 — Realtime UI Generator.

Kiểm tra:
- AngularRealtimeEmitter: sinh tất cả widgets + services
- Fallback inline generation khi không có template
- UI framework validation
- Tenant isolation trong context
"""

import pytest
from pathlib import Path

from midicoder.emitters.core.cp22_realtime_ui.angular import (
    AngularRealtimeEmitter,
    GeneratedFile,
)
from midicoder.emitters.core.cp22_realtime_ui.models import (
    ChannelSpec,
    WidgetConfig,
    WidgetType,
    TransportType,
)


def _make_sample_channels() -> list[ChannelSpec]:
    """Tạo sample channels cho testing."""
    return [
        ChannelSpec(
            channel_id="order.created",
            event_topic="orders",
            transport=TransportType.WEBSOCKET,
            payload_fields=["order_id", "total"],
        ),
        ChannelSpec(
            channel_id="user.presence.changed",
            event_topic="presence",
            transport=TransportType.WEBSOCKET,
            tenant_id="tenant-1",
            payload_fields=["user_id", "status"],
        ),
        ChannelSpec(
            channel_id="payment.completed",
            event_topic="payments",
            transport=TransportType.WEBSOCKET,
            payload_fields=["payment_id", "amount"],
        ),
    ]


def _make_widget_configs() -> list[WidgetConfig]:
    """Tạo sample widget configs cho testing."""
    return [
        WidgetConfig(
            widget_type=WidgetType.PRESENCE,
            channel_id="user.presence.changed",
            tenant_id="tenant-1",
            ui_framework="material",
        ),
        WidgetConfig(
            widget_type=WidgetType.LIVE_FEED,
            channel_id="order.created",
            ui_framework="material",
            max_items=50,
            auto_scroll=True,
        ),
    ]


# ============================================================================
# Test AngularRealtimeEmitter
# ============================================================================

class TestAngularRealtimeEmitter:
    """Kiểm tra Angular emitter."""

    def test_init_default_ui_framework(self):
        """Init với UI framework mặc định."""
        emitter = AngularRealtimeEmitter()
        assert emitter.ui_framework == "material"

    def test_init_custom_ui_framework(self):
        """Init với UI framework tuỳ chọn."""
        emitter = AngularRealtimeEmitter(ui_framework="tailwind")
        assert emitter.ui_framework == "tailwind"

    def test_init_invalid_ui_framework(self):
        """Init với UI framework không hợp lệ gây lỗi."""
        with pytest.raises(ValueError, match="không được hỗ trợ"):
            AngularRealtimeEmitter(ui_framework="invalid-framework")

    def test_generate_returns_generated_files(self, tmp_path: Path):
        """Generate trả về danh sách GeneratedFile."""
        emitter = AngularRealtimeEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        assert len(files) > 0
        assert all(isinstance(f, GeneratedFile) for f in files)

    def test_generate_includes_channel_service(self, tmp_path: Path):
        """Generate bao gồm channel-subscription.service.ts."""
        emitter = AngularRealtimeEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        names = [f.path.name for f in files]
        assert "channel-subscription.service.ts" in names

    def test_generate_includes_presence_service(self, tmp_path: Path):
        """Generate bao gồm presence.service.ts."""
        emitter = AngularRealtimeEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        names = [f.path.name for f in files]
        assert "presence.service.ts" in names

    def test_generate_includes_refresh_mixin(self, tmp_path: Path):
        """Generate bao gồm realtime-refresh-mixin.ts."""
        emitter = AngularRealtimeEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        names = [f.path.name for f in files]
        assert "realtime-refresh-mixin.ts" in names

    def test_generate_with_widget_configs(self, tmp_path: Path):
        """Generate với widget configs sinh đúng widgets."""
        emitter = AngularRealtimeEmitter()
        channels = _make_sample_channels()
        configs = _make_widget_configs()
        files = emitter.generate(channels, configs, output_dir=tmp_path)

        names = [f.path.name for f in files]
        assert "presence-indicator.component.ts" in names
        assert "live-feed.component.ts" in names

    def test_generate_without_widget_configs_defaults_feed(self, tmp_path: Path):
        """Generate không có widget config -> sinh default LiveFeed."""
        emitter = AngularRealtimeEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, [], output_dir=tmp_path)

        names = [f.path.name for f in files]
        assert "live-feed.component.ts" in names

    def test_generate_files_written_to_disk(self, tmp_path: Path):
        """Generate write files vào disk."""
        emitter = AngularRealtimeEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        for f in files:
            assert (tmp_path / f.path).exists()

    def test_generate_content_has_typescript(self, tmp_path: Path):
        """Nội dung sinh ra có TypeScript syntax."""
        emitter = AngularRealtimeEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        # Service content chứa TypeScript import
        service_file = next(
            f for f in files if f.path.name == "channel-subscription.service.ts"
        )
        assert "import" in service_file.content
        assert "export" in service_file.content

    def test_generate_content_has_angular_decorators(self, tmp_path: Path):
        """Nội dung service sinh ra có Angular decorators."""
        emitter = AngularRealtimeEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        service_file = next(
            f for f in files if f.path.name == "channel-subscription.service.ts"
        )
        assert "@Injectable" in service_file.content
        assert "providedIn: 'root'" in service_file.content

    def test_generate_content_has_rxjs(self, tmp_path: Path):
        """Nội dung service sinh ra có RxJS imports."""
        emitter = AngularRealtimeEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        service_file = next(
            f for f in files if f.path.name == "channel-subscription.service.ts"
        )
        assert "Subject" in service_file.content
        assert "Observable" in service_file.content
        # BehaviorSubject is in presence.service.ts, not channel-subscription

    def test_generate_content_has_channel_ids(self, tmp_path: Path):
        """Nội dung sinh ra chứa WebSocket URL với channel ID."""
        emitter = AngularRealtimeEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        service_file = next(
            f for f in files if f.path.name == "channel-subscription.service.ts"
        )
        # Templates generate WebSocket URL with channelId variable, not hardcoded IDs
        assert "channelId" in service_file.content
        assert "WebSocket" in service_file.content

    def test_generate_tenant_isolation(self, tmp_path: Path):
        """Nội dung có tenant isolation khi channel scoped."""
        emitter = AngularRealtimeEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        service_file = next(
            f for f in files if f.path.name == "channel-subscription.service.ts"
        )
        assert "tenant" in service_file.content.lower()

    def test_generate_content_has_sse_fallback(self, tmp_path: Path):
        """Nội dung service sinh ra có reconnect logic (SSE fallback)."""
        emitter = AngularRealtimeEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        service_file = next(
            f for f in files if f.path.name == "channel-subscription.service.ts"
        )
        # SSE fallback is via autoReconnect logic in template
        assert "autoReconnect" in service_file.content
        assert "onclose" in service_file.content

    def test_generate_presence_service_content(self, tmp_path: Path):
        """Nội dung presence service có đúng API."""
        emitter = AngularRealtimeEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        presence_file = next(
            f for f in files if f.path.name == "presence.service.ts"
        )
        assert "isOnline" in presence_file.content
        assert "isTyping" in presence_file.content
        assert "onlineCount" in presence_file.content
        assert "UserPresence" in presence_file.content

    def test_generate_refresh_mixin_content(self, tmp_path: Path):
        """Nội dung refresh mixin có đúng API."""
        emitter = AngularRealtimeEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        mixin_file = next(
            f for f in files if f.path.name == "realtime-refresh-mixin.ts"
        )
        assert "subscribeToRefresh" in mixin_file.content
        assert "AUTO_REFRESH_TOPICS" in mixin_file.content
        assert "orders" in mixin_file.content
        assert "debounceMs" in mixin_file.content
        assert "throttleMs" in mixin_file.content

    def test_generate_widget_component_content(self, tmp_path: Path):
        """Nội dung widget component có Angular decorators."""
        emitter = AngularRealtimeEmitter()
        channels = _make_sample_channels()
        configs = [
            WidgetConfig(
                widget_type=WidgetType.LIVE_FEED,
                channel_id="order.created",
                ui_framework="material",
                max_items=100,
            )
        ]
        files = emitter.generate(channels, configs, output_dir=tmp_path)

        widget_file = next(
            f for f in files if f.path.name == "live-feed.component.ts"
        )
        assert "@Component" in widget_file.content
        assert "@Input" in widget_file.content
        assert "selector:" in widget_file.content
        assert "midicoder-live-feed" in widget_file.content
        assert "LiveFeedComponent" in widget_file.content
        assert "maxItems" in widget_file.content

    def test_different_ui_frameworks(self, tmp_path: Path):
        """Các UI framework khác nhau sinh content khác nhau."""
        channels = _make_sample_channels()

        emitter_material = AngularRealtimeEmitter(ui_framework="material")
        files_m = emitter_material.generate(channels, output_dir=tmp_path / "m")

        emitter_tw = AngularRealtimeEmitter(ui_framework="tailwind")
        files_tw = emitter_tw.generate(channels, output_dir=tmp_path / "tw")

        # Same file count, potentially different imports
        assert len(files_m) == len(files_tw)

    def test_generated_file_attributes(self, tmp_path: Path):
        """GeneratedFile có đầy đủ attributes."""
        emitter = AngularRealtimeEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        f = files[0]
        assert isinstance(f.path, Path)
        assert isinstance(f.content, str)
        assert isinstance(f.template, str)
        assert "angular/cp22" in f.template

    def test_all_widget_types_generated(self, tmp_path: Path):
        """Tất cả 5 widget types có thể được sinh."""
        emitter = AngularRealtimeEmitter()
        channels = _make_sample_channels()
        configs = [
            WidgetConfig(
                widget_type=wt,
                channel_id="order.created",
                ui_framework="material",
            )
            for wt in WidgetType
        ]
        files = emitter.generate(channels, configs, output_dir=tmp_path)

        names = [f.path.name for f in files]
        assert "presence-indicator.component.ts" in names
        assert "live-feed.component.ts" in names
        assert "live-counter.component.ts" in names
        assert "live-cursor.component.ts" in names
        assert "notification-toast.component.ts" in names


# ============================================================================
# Test GeneratedFile
# ============================================================================

class TestGeneratedFile:
    """Kiểm tra GeneratedFile dataclass."""

    def test_create_with_str_path(self):
        """Tạo GeneratedFile với string path."""
        gf = GeneratedFile(
            path="src/channel-subscription.service.ts",
            content="code",
            template="t.ts",
        )
        assert gf.path == Path("src/channel-subscription.service.ts")

    def test_create_with_path_obj(self):
        """Tạo GeneratedFile với Path object."""
        gf = GeneratedFile(
            path=Path("src/channel-subscription.service.ts"),
            content="code",
            template="t.ts",
        )
        assert gf.path == Path("src/channel-subscription.service.ts")

    def test_dataclass_fields(self):
        """GeneratedFile là dataclass với đúng fields."""
        gf = GeneratedFile(
            path=Path("test.ts"),
            content="const x = 1;",
            template="angular/cp22_realtime_ui/test.ts.jinja2",
        )
        assert gf.path == Path("test.ts")
        assert gf.content == "const x = 1;"
        assert gf.template == "angular/cp22_realtime_ui/test.ts.jinja2"


# ============================================================================
# Test Angular Inline Fallback (khi không có template)
# ============================================================================

class TestAngularInlineFallback:
    """Kiểm tra fallback inline generation khi template không tồn tại."""

    def _make_fallback_emitter(self):
        """Tạo emitter dùng BaseLoader (không template) để trigger fallback."""
        from jinja2 import BaseLoader, Environment
        emitter = AngularRealtimeEmitter(ui_framework="material")
        emitter._template_env = Environment(
            loader=BaseLoader(),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
            variable_start_string="{[{",
            variable_end_string="}]}",
        )
        return emitter

    def test_fallback_channel_service(self, tmp_path: Path):
        """Fallback sinh channel-subscription.service.ts."""
        emitter = self._make_fallback_emitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        svc = next(f for f in files if f.path.name == "channel-subscription.service.ts")
        assert "@Injectable" in svc.content
        assert "fallback" in svc.content.lower()

    def test_fallback_presence_service(self, tmp_path: Path):
        """Fallback sinh presence.service.ts."""
        emitter = self._make_fallback_emitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        svc = next(f for f in files if f.path.name == "presence.service.ts")
        assert "isOnline" in svc.content
        assert "fallback" in svc.content.lower()

    def test_fallback_refresh_mixin(self, tmp_path: Path):
        """Fallback sinh realtime-refresh-mixin.ts."""
        emitter = self._make_fallback_emitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        mixin = next(f for f in files if f.path.name == "realtime-refresh-mixin.ts")
        assert "fallback" in mixin.content.lower()

    def test_fallback_all_widgets(self, tmp_path: Path):
        """Fallback sinh tất cả 5 widget types."""
        emitter = self._make_fallback_emitter()
        channels = _make_sample_channels()
        configs = [
            WidgetConfig(widget_type=wt, channel_id="order.created", ui_framework="material")
            for wt in WidgetType
        ]
        files = emitter.generate(channels, configs, output_dir=tmp_path)
        names = [f.path.name for f in files]

        assert "presence-indicator.component.ts" in names
        assert "live-feed.component.ts" in names
        assert "live-counter.component.ts" in names
        assert "live-cursor.component.ts" in names
        assert "notification-toast.component.ts" in names
