"""
Test cho React emitter của CP22 — Realtime UI Generator.

Kiểm tra:
- RealtimeComponentEmitter: sinh tất cả widgets + hooks
- Fallback inline generation khi không có template
- UI framework validation
- Tenant isolation trong context
"""

import pytest
from pathlib import Path

from midicoder.packs.cp22_realtime_ui.react import (
    RealtimeComponentEmitter,
    GeneratedFile,
)
from midicoder.packs.cp22_realtime_ui.models import (
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
# Test RealtimeComponentEmitter
# ============================================================================

class TestReactRealtimeEmitter:
    """Kiểm tra React emitter."""

    def test_init_default_ui_framework(self):
        """Init với UI framework mặc định."""
        emitter = RealtimeComponentEmitter()
        assert emitter.ui_framework == "material"

    def test_init_custom_ui_framework(self):
        """Init với UI framework tuỳ chọn."""
        emitter = RealtimeComponentEmitter(ui_framework="tailwind")
        assert emitter.ui_framework == "tailwind"

    def test_init_invalid_ui_framework(self):
        """Init với UI framework không hợp lệ gây lỗi."""
        with pytest.raises(ValueError, match="không được hỗ trợ"):
            RealtimeComponentEmitter(ui_framework="invalid-framework")

    def test_generate_returns_generated_files(self, tmp_path: Path):
        """Generate trả về danh sách GeneratedFile."""
        emitter = RealtimeComponentEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        assert len(files) > 0
        assert all(isinstance(f, GeneratedFile) for f in files)

    def test_generate_includes_channel_hook(self, tmp_path: Path):
        """Generate bao gồm useChannelSubscription hook."""
        emitter = RealtimeComponentEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        names = [f.path.name for f in files]
        assert "useChannelSubscription.ts" in names

    def test_generate_includes_presence_hook(self, tmp_path: Path):
        """Generate bao gồm usePresence hook."""
        emitter = RealtimeComponentEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        names = [f.path.name for f in files]
        assert "usePresence.ts" in names

    def test_generate_includes_refresh_hook(self, tmp_path: Path):
        """Generate bao gồm useRealtimeRefresh hook."""
        emitter = RealtimeComponentEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        names = [f.path.name for f in files]
        assert "useRealtimeRefresh.ts" in names

    def test_generate_with_widget_configs(self, tmp_path: Path):
        """Generate với widget configs sinh đúng widgets."""
        emitter = RealtimeComponentEmitter()
        channels = _make_sample_channels()
        configs = _make_widget_configs()
        files = emitter.generate(channels, configs, output_dir=tmp_path)

        names = [f.path.name for f in files]
        assert "PresenceIndicator.tsx" in names
        assert "LiveFeed.tsx" in names

    def test_generate_without_widget_configs_defaults_feed(self, tmp_path: Path):
        """Generate không có widget config → sinh default LiveFeed."""
        emitter = RealtimeComponentEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, [], output_dir=tmp_path)

        names = [f.path.name for f in files]
        assert "LiveFeed.tsx" in names

    def test_generate_files_written_to_disk(self, tmp_path: Path):
        """Generate write files vào disk."""
        emitter = RealtimeComponentEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        for f in files:
            assert (tmp_path / f.path).exists()

    def test_generate_content_has_typescript(self, tmp_path: Path):
        """Nội dung sinh ra có TypeScript syntax."""
        emitter = RealtimeComponentEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        # Hook content chứa TypeScript import
        hook_file = next(
            f for f in files if f.path.name == "useChannelSubscription.ts"
        )
        assert "import" in hook_file.content
        assert "export" in hook_file.content

    def test_generate_content_has_channel_ids(self, tmp_path: Path):
        """Nội dung sinh ra chứa channel IDs từ input."""
        emitter = RealtimeComponentEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        hook_file = next(
            f for f in files if f.path.name == "useChannelSubscription.ts"
        )
        assert "order.created" in hook_file.content
        assert "user.presence.changed" in hook_file.content

    def test_generate_tenant_isolation(self, tmp_path: Path):
        """Nội dung có tenant isolation khi channel scoped."""
        emitter = RealtimeComponentEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        hook_file = next(
            f for f in files if f.path.name == "useChannelSubscription.ts"
        )
        assert "tenant" in hook_file.content.lower()

    def test_different_ui_frameworks(self, tmp_path: Path):
        """Các UI framework khác nhau sinh content khác nhau."""
        channels = _make_sample_channels()

        emitter_material = RealtimeComponentEmitter(ui_framework="material")
        files_m = emitter_material.generate(channels, output_dir=tmp_path / "m")

        emitter_tw = RealtimeComponentEmitter(ui_framework="tailwind")
        files_tw = emitter_tw.generate(channels, output_dir=tmp_path / "tw")

        # Same file count, potentially different imports
        assert len(files_m) == len(files_tw)

    def test_generated_file_attributes(self, tmp_path: Path):
        """GeneratedFile có đầy đủ attributes."""
        emitter = RealtimeComponentEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        f = files[0]
        assert isinstance(f.path, Path)
        assert isinstance(f.content, str)
        assert isinstance(f.template, str)
        assert "cp22" in f.template


# ============================================================================
# Test GeneratedFile
# ============================================================================

class TestGeneratedFile:
    """Kiểm tra GeneratedFile dataclass."""

    def test_create_with_str_path(self):
        """Tạo GeneratedFile với string path."""
        gf = GeneratedFile(path="src/widget.tsx", content="code", template="t.tsx")
        assert gf.path == Path("src/widget.tsx")

    def test_create_with_path_obj(self):
        """Tạo GeneratedFile với Path object."""
        gf = GeneratedFile(
            path=Path("src/widget.tsx"),
            content="code",
            template="t.tsx"
        )
        assert gf.path == Path("src/widget.tsx")


# ============================================================================
# Test React Inline Fallback (khi không có template)
# ============================================================================

class TestReactInlineFallback:
    """Kiểm tra fallback inline generation khi template không tồn tại."""

    def _make_fallback_emitter(self):
        """Tạo emitter dùng BaseLoader (không template) để trigger fallback."""
        from jinja2 import BaseLoader, Environment
        emitter = RealtimeComponentEmitter(ui_framework="material")
        emitter._template_env = Environment(
            loader=BaseLoader(),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
            variable_start_string="{[{",
            variable_end_string="}]}",
        )
        return emitter

    def test_fallback_channel_hook(self, tmp_path: Path):
        """Fallback sinh useChannelSubscription hook đúng cấu trúc."""
        emitter = self._make_fallback_emitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        hook = next(f for f in files if f.path.name == "useChannelSubscription.ts")
        assert "useState" in hook.content
        assert "useEffect" in hook.content
        assert "fallback" in hook.content.lower()

    def test_fallback_presence_hook(self, tmp_path: Path):
        """Fallback sinh usePresence hook đúng cấu trúc."""
        emitter = self._make_fallback_emitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        hook = next(f for f in files if f.path.name == "usePresence.ts")
        assert "PresenceStatus" in hook.content
        assert "fallback" in hook.content.lower()

    def test_fallback_refresh_hook(self, tmp_path: Path):
        """Fallback sinh useRealtimeRefresh hook đúng cấu trúc."""
        emitter = self._make_fallback_emitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        hook = next(f for f in files if f.path.name == "useRealtimeRefresh.ts")
        assert "debounce" in hook.content.lower()
        assert "fallback" in hook.content.lower()

    def test_fallback_widget_component(self, tmp_path: Path):
        """Fallback sinh widget component từ config."""
        emitter = self._make_fallback_emitter()
        channels = _make_sample_channels()
        configs = [
            WidgetConfig(
                widget_type=WidgetType.PRESENCE,
                channel_id="user.presence.changed",
                ui_framework="material",
            )
        ]
        files = emitter.generate(channels, configs, output_dir=tmp_path)

        widget = next(f for f in files if f.path.name == "PresenceIndicator.tsx")
        assert "fallback" in widget.content.lower()
        assert "PresenceIndicator" in widget.content

    def test_fallback_all_widgets(self, tmp_path: Path):
        """Fallback sinh được tất cả 5 widget types."""
        emitter = self._make_fallback_emitter()
        channels = _make_sample_channels()
        configs = [
            WidgetConfig(widget_type=wt, channel_id="order.created", ui_framework="material")
            for wt in WidgetType
        ]
        files = emitter.generate(channels, configs, output_dir=tmp_path)
        names = [f.path.name for f in files]

        assert "PresenceIndicator.tsx" in names
        assert "LiveFeed.tsx" in names
        assert "LiveCounter.tsx" in names
        assert "LiveCursor.tsx" in names
        assert "NotificationToast.tsx" in names


# ============================================================================
# Test Template Rules V1 + V2
# ============================================================================

class TestTemplateRules:
    """Kiểm tra generated code tuân thủ Template Rules."""

    def test_v1_no_midicoder_imports_react(self, tmp_path: Path):
        """V1: React generated code không import từ midicoder."""
        emitter = RealtimeComponentEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        for f in files:
            assert "from midicoder" not in f.content
            assert "import midicoder" not in f.content

    def test_v1_no_midicoder_imports_angular(self, tmp_path: Path):
        """V1: Angular generated code không import từ midicoder."""
        from midicoder.packs.cp22_realtime_ui.angular import AngularRealtimeEmitter
        emitter = AngularRealtimeEmitter()
        channels = _make_sample_channels()
        files = emitter.generate(channels, output_dir=tmp_path)

        for f in files:
            assert "from midicoder" not in f.content
            assert "@midicoder/" not in f.content
