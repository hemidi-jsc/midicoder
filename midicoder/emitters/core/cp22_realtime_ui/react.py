"""
React emitter cho CP22 — Real-time UI Generator.

RealtimeComponentEmitter sinh ra:
- 5 Realtime widgets (PresenceIndicator, LiveFeed, LiveCounter, LiveCursor, NotificationToast)
- Realtime mixin hook (useRealtimeRefresh)
- Channel subscription hook (useChannelSubscription)
- Presence hook (usePresence)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from jinja2 import BaseLoader, Environment, FileSystemLoader, TemplateNotFound

from .models import (
    ChannelSpec,
    WidgetConfig,
    WidgetType,
)


# Phân giải thư mục template
_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent
_TEMPLATE_DIR = _PACKAGE_DIR / "stacks" / "react" / "core" / "cp22_realtime_ui"


class GeneratedFile:
    """File đã được sinh ra bởi emitter."""

    def __init__(
        self,
        path: str | Path,
        content: str,
        template: str,
    ) -> None:
        self.path = Path(path)
        self.content = content
        self.template = template


# Mapping giữa widget type và template/output files
_WIDGET_TEMPLATE_MAP: dict[WidgetType, tuple[str, str]] = {
    WidgetType.PRESENCE: (
        "PresenceIndicator.tsx.jinja2",
        "PresenceIndicator.tsx",
    ),
    WidgetType.LIVE_FEED: (
        "LiveFeed.tsx.jinja2",
        "LiveFeed.tsx",
    ),
    WidgetType.LIVE_COUNTER: (
        "LiveCounter.tsx.jinja2",
        "LiveCounter.tsx",
    ),
    WidgetType.LIVE_CURSOR: (
        "LiveCursor.tsx.jinja2",
        "LiveCursor.tsx",
    ),
    WidgetType.NOTIFICATION_TOAST: (
        "NotificationToast.tsx.jinja2",
        "NotificationToast.tsx",
    ),
}


class RealtimeComponentEmitter:
    """
    Emitter cho React realtime components.

    Sinh ra các components và hooks TypeScript/TSX từ ChannelSpec và WidgetConfig.
    """

    SUPPORTED_UI_FRAMEWORKS = ["material", "tailwind", "bootstrap", "antd", "carbon"]

    def __init__(self, ui_framework: str = "material") -> None:
        """
        Khởi tạo emitter cho React.

        Args:
            ui_framework: UI framework để render (material, tailwind, bootstrap, antd, carbon).
        """
        if ui_framework not in self.SUPPORTED_UI_FRAMEWORKS:
            raise ValueError(
                f"UI framework '{ui_framework}' không được hỗ trợ. "
                f"Sử dụng: {self.SUPPORTED_UI_FRAMEWORKS}"
            )
        self.ui_framework = ui_framework
        loader = FileSystemLoader(str(_TEMPLATE_DIR)) if _TEMPLATE_DIR.exists() else BaseLoader()
        self._template_env = Environment(
            loader=loader,
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
            variable_start_string="{[{",
            variable_end_string="}]}",
        )

    def _render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """Render Jinja2 template với context."""
        try:
            template = self._template_env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            return self._generate_inline_fallback(template_name, context)

    def generate(
        self,
        channels: list[ChannelSpec],
        widget_configs: list[WidgetConfig] | None = None,
        output_dir: Path | None = None,
    ) -> list[GeneratedFile]:
        """
        Sinh tất cả realtime components và hooks.

        Args:
            channels: Danh sách ChannelSpec từ parser.
            widget_configs: Danh sách WidgetConfig (tuỳ chọn).
            output_dir: Thư mục output (tuỳ chọn).

        Returns:
            Danh sách GeneratedFile đã sinh.
        """
        generated: list[GeneratedFile] = []
        if widget_configs is None:
            widget_configs = []

        generated.append(self._emit_channel_subscription_hook(channels, output_dir))
        generated.append(self._emit_presence_hook(channels, output_dir))

        emitted_widgets: set[WidgetType] = set()
        for config in widget_configs:
            if config.widget_type not in emitted_widgets:
                wf = self._emit_widget(config, channels, output_dir)
                if wf:
                    generated.append(wf)
                    emitted_widgets.add(config.widget_type)

        # Default: sinh LiveFeed nếu không có widget nào
        if not emitted_widgets:
            default_cfg = WidgetConfig(
                widget_type=WidgetType.LIVE_FEED,
                channel_id=channels[0].channel_id if channels else "default",
                ui_framework=self.ui_framework,
                max_items=50,
            )
            wf = self._emit_widget(default_cfg, channels, output_dir)
            if wf:
                generated.append(wf)

        generated.append(self._emit_realtime_refresh_hook(channels, output_dir))
        return generated

    def _emit_channel_subscription_hook(
        self, channels: list[ChannelSpec], output_dir: Path | None,
    ) -> GeneratedFile:
        """Sinh useChannelSubscription hook."""
        ctx = {
            "ui_framework": self.ui_framework,
            "channels": [ch.to_dict() for ch in channels],
            "channel_count": len(channels),
            "has_tenant_channels": any(ch.is_tenant_scoped for ch in channels),
        }
        return self._write_file(
            "useChannelSubscription.ts.jinja2", "useChannelSubscription.ts", ctx, output_dir
        )

    def _emit_presence_hook(
        self, channels: list[ChannelSpec], output_dir: Path | None,
    ) -> GeneratedFile:
        """Sinh usePresence hook."""
        presence_channels = [
            ch for ch in channels
            if "presence" in ch.channel_id.lower() or "online" in ch.channel_id.lower()
        ]
        ctx = {
            "ui_framework": self.ui_framework,
            "channels": [ch.to_dict() for ch in channels],
            "presence_channels": [ch.to_dict() for ch in presence_channels],
            "has_tenant_presence": any(ch.is_tenant_scoped for ch in presence_channels),
        }
        return self._write_file(
            "usePresence.ts.jinja2", "usePresence.ts", ctx, output_dir
        )

    def _emit_widget(
        self, config: WidgetConfig, channels: list[ChannelSpec], output_dir: Path | None,
    ) -> GeneratedFile | None:
        """Sinh một widget component."""
        template_info = _WIDGET_TEMPLATE_MAP.get(config.widget_type)
        if not template_info:
            return None
        template_name, output_name = template_info
        matching_channels = [
            ch for ch in channels
            if config.channel_id in ch.channel_id or config.widget_type.value in ch.channel_id
        ]
        ctx = {
            "ui_framework": self.ui_framework,
            "widget_config": config.to_dict(),
            "widget_type": config.widget_type.value,
            "channels": [ch.to_dict() for ch in matching_channels],
            "all_channels": [ch.to_dict() for ch in channels],
            "has_tenant_scope": config.tenant_id is not None,
            "tenant_id": config.tenant_id,
            "max_items": config.max_items,
            "auto_scroll": config.auto_scroll,
            "initial_value": config.initial_value,
            "threshold_colors": config.threshold_colors,
        }
        return self._write_file(template_name, output_name, ctx, output_dir)

    def _emit_realtime_refresh_hook(
        self, channels: list[ChannelSpec], output_dir: Path | None,
    ) -> GeneratedFile:
        """Sinh useRealtimeRefresh hook — realtime mixin cho CP19."""
        ctx = {
            "ui_framework": self.ui_framework,
            "channels": [ch.to_dict() for ch in channels],
            "channel_topics": [ch.event_topic for ch in channels],
            "channel_count": len(channels),
        }
        return self._write_file(
            "useRealtimeRefresh.ts.jinja2", "useRealtimeRefresh.ts", ctx, output_dir
        )

    def _write_file(
        self,
        template_name: str,
        filename: str,
        context: dict[str, Any],
        output_dir: Path | None,
    ) -> GeneratedFile:
        """Render template và write file."""
        content = self._render_template(template_name, context)
        if output_dir is not None:
            file_path = output_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=Path(filename),
            content=content,
            template="react/cp22_realtime_ui/" + template_name,
        )

    # ------------------------------------------------------------------
    # Inline fallback generators (khi chưa có Jinja2 template)
    # ------------------------------------------------------------------

    def _generate_inline_fallback(
        self, template_name: str, context: dict[str, Any],
    ) -> str:
        """Sinh nội dung fallback inline khi template không tồn tại."""
        if template_name == "useChannelSubscription.ts.jinja2":
            return self._fallback_channel_hook(context)
        elif template_name == "usePresence.ts.jinja2":
            return self._fallback_presence_hook(context)
        elif template_name == "useRealtimeRefresh.ts.jinja2":
            return self._fallback_refresh_hook(context)
        component_name = re.sub(r"\.(tsx?)?\.(jinja2)?$", "", template_name)
        return self._fallback_widget_component(component_name, context)

    def _fallback_channel_hook(self, ctx: dict[str, Any]) -> str:
        """Sinh fallback cho useChannelSubscription hook."""
        channels = ctx.get("channels", [])
        has_tenant = ctx.get("has_tenant_channels", False)
        ui_fw = ctx.get("ui_framework", "material")

        parts: list[str] = []
        parts.append('/**')
        parts.append(' * useChannelSubscription hook — subscribe realtime channels')
        parts.append(' *')
        parts.append(f' * Sinh bởi CP22 RealtimeComponentEmitter (fallback mode)')
        parts.append(f' * UI Framework: {ui_fw}')
        parts.append(' */')
        parts.append('')
        parts.append('import { useState, useEffect, useCallback, useRef } from "react";')
        parts.append('')
        parts.append('// Kiểu channel ID tự động sinh từ CP05 events')
        parts.append('export type ChannelId =')
        for ch in channels:
            cid = ch.get("channel_id", "unknown")
            parts.append(f"  | '{cid}'")
        parts.append('  | string;')
        parts.append('')
        parts.append('interface MessagePayload {')
        parts.append('  channel: string;')
        parts.append('  data: unknown;')
        parts.append('  timestamp: string;')
        if has_tenant:
            parts.append('  tenant_id: string;')
        parts.append('}')
        parts.append('')
        parts.append('/**')
        parts.append(' * Hook để subscribe vào realtime channel (WebSocket với SSE fallback)')
        parts.append(' *')
        parts.append(' * @param channelId - ID của channel để subscribe')
        parts.append(' * @param options   - Cấu hình kết nối')
        parts.append(' * @returns         - Trạng thái subscription')
        parts.append(' */')
        parts.append('export function useChannelSubscription(')
        parts.append('  channelId: ChannelId,')
        parts.append('  options?: {')
        parts.append('    url?: string;')
        if has_tenant:
            parts.append('    tenantId?: string;')
        parts.append('    autoReconnect?: boolean;')
        parts.append('    maxRetries?: number;')
        parts.append('    onMessage?: (payload: MessagePayload) => void;')
        parts.append('  }')
        parts.append(') {')
        parts.append('  const {')
        parts.append('    url = "/ws",')
        if has_tenant:
            parts.append('    tenantId,')
        parts.append('    autoReconnect = true,')
        parts.append('    maxRetries = 5,')
        parts.append('    onMessage,')
        parts.append('  } = options || {};')
        parts.append('')
        parts.append('  const [isConnected, setIsConnected] = useState(false);')
        parts.append('  const [messages, setMessages] = useState<MessagePayload[]>([]);')
        parts.append('  const wsRef = useRef<WebSocket | null>(null);')
        parts.append('  const retryCountRef = useRef(0);')
        parts.append('')
        parts.append('  useEffect(() => {')
        parts.append('    const params = new URLSearchParams();')
        if has_tenant:
            parts.append('    if (tenantId) params.set("tenant_id", tenantId);')
        parts.append('    const query = params.toString();')
        parts.append('    const wsUrl = `${url}/${channelId}${query ? `?${query}` : ""}`;')
        parts.append('    const ws = new WebSocket(wsUrl);')
        parts.append('')
        parts.append('    ws.onopen = () => {')
        parts.append('      setIsConnected(true);')
        parts.append('      retryCountRef.current = 0;')
        parts.append('    };')
        parts.append('')
        parts.append('    ws.onmessage = (event) => {')
        parts.append('      const payload: MessagePayload = JSON.parse(event.data);')
        parts.append('      setMessages((prev) => [...prev, payload]);')
        parts.append('      onMessage?.(payload);')
        parts.append('    };')
        parts.append('')
        parts.append('    ws.onclose = () => {')
        parts.append('      setIsConnected(false);')
        parts.append('      if (autoReconnect && retryCountRef.current < maxRetries) {')
        parts.append('        retryCountRef.current++;')
        parts.append('        setTimeout(() => {')
        parts.append('          ws.onopen();')
        parts.append('        }, 1000 * retryCountRef.current);')
        parts.append('      }')
        parts.append('    };')
        parts.append('')
        parts.append('    wsRef.current = ws;')
        parts.append('    return () => ws.close();')
        dep_array = ['channelId', 'url']
        if has_tenant:
            dep_array.append("tenantId")
        parts.append("  }, [" + ", ".join(dep_array) + "]);")
        parts.append('')
        parts.append('  return {')
        parts.append('    channelId,')
        parts.append('    isConnected,')
        parts.append('    messages,')
        parts.append('    subscribe: (topic: string) => {')
        parts.append('      if (wsRef.current?.readyState === WebSocket.OPEN) {')
        parts.append('        wsRef.current.send(JSON.stringify({ type: "subscribe", topic }));')
        parts.append('      }')
        parts.append('    },')
        parts.append('  };')
        parts.append('}')
        parts.append('')

        return "\n".join(parts)

    def _fallback_presence_hook(self, ctx: dict[str, Any]) -> str:
        """Sinh fallback cho usePresence hook."""
        ui_fw = ctx.get("ui_framework", "material")
        presence_ch = ctx.get("presence_channels", [])
        has_tenant = ctx.get("has_tenant_presence", False)

        channel_ids = [ch.get("channel_id", "default") for ch in presence_ch]
        default_ch = channel_ids[0] if channel_ids else "user.presence.changed"

        lines: list[str] = []
        lines.append('/**')
        lines.append(' * usePresence hook — quản lý trạng thái presence realtime')
        lines.append(' *')
        lines.append(f' * Sinh bởi CP22 RealtimeComponentEmitter (fallback mode)')
        lines.append(f' * UI Framework: {ui_fw}')
        lines.append(' */')
        lines.append('')
        lines.append('import { useState, useEffect, useCallback, useMemo } from "react";')
        lines.append('')
        lines.append('export type PresenceStatus = "online" | "offline" | "typing" | "away";')
        lines.append('')
        lines.append('interface UserPresence {')
        lines.append('  user_id: string;')
        lines.append('  status: PresenceStatus;')
        lines.append('  last_seen?: string;')
        if has_tenant:
            lines.append('  tenant_id?: string;')
        lines.append('}')
        lines.append('')
        lines.append('interface PresenceState {')
        lines.append('  users: Map<string, UserPresence>;')
        lines.append('  onlineCount: number;')
        lines.append('  isOnline: (userId: string) => boolean;')
        lines.append('  isTyping: (userId: string) => boolean;')
        lines.append('  isConnected: boolean;')
        lines.append('}')
        lines.append('')
        lines.append('/**')
        lines.append(' * Hook để theo dõi presence của users realtime')
        lines.append(' *')
        lines.append(' * @param options - Cấu hình presence')
        lines.append(' * @returns       - Trạng thái presence và helper functions')
        lines.append(' */')
        lines.append('export function usePresence(options?: {')
        lines.append(f'  channel?: string; // default: "{default_ch}"')
        if has_tenant:
            lines.append('  tenantId?: string;')
        lines.append('  onUpdate?: (presence: UserPresence) => void;')
        lines.append('}) {')
        lines.append('  const {')
        lines.append(f'    channel = "{default_ch}",')
        if has_tenant:
            lines.append('    tenantId,')
        lines.append('    onUpdate,')
        lines.append('  } = options || {};')
        lines.append('')
        lines.append('  const [users, setUsers] = useState<Map<string, UserPresence>>(new Map());')
        lines.append('  const [isConnected, setIsConnected] = useState(false);')
        lines.append('')
        lines.append('  const onlineCount = useMemo(() => {')
        lines.append('    let count = 0;')
        lines.append('    users.forEach((u) => { if (u.status === "online") count++; });')
        lines.append('    return count;')
        lines.append('  }, [users]);')
        lines.append('')
        lines.append('  const isOnline = useCallback((userId: string) => {')
        lines.append('    return users.get(userId)?.status === "online";')
        lines.append('  }, [users]);')
        lines.append('')
        lines.append('  const isTyping = useCallback((userId: string) => {')
        lines.append('    return users.get(userId)?.status === "typing";')
        lines.append('  }, [users]);')
        lines.append('')
        lines.append('  useEffect(() => {')
        lines.append('    // Subscribe vào presence channel qua WebSocket')
        lines.append('    return () => { /* cleanup */ };')
        if has_tenant:
            lines.append('  }, [channel, tenantId]);')
        else:
            lines.append('  }, [channel]);')
        lines.append('')
        lines.append('  return { users, onlineCount, isOnline, isTyping, isConnected } as PresenceState;')
        lines.append('}')
        lines.append('')
        return "\n".join(lines)

    def _fallback_refresh_hook(self, ctx: dict[str, Any]) -> str:
        """Sinh fallback cho useRealtimeRefresh hook."""
        topics = ctx.get("channel_topics", [])
        ui_fw = ctx.get("ui_framework", "material")

        lines: list[str] = []
        lines.append('/**')
        lines.append(' * useRealtimeRefresh hook — realtime mixin cho CP19 components')
        lines.append(' *')
        lines.append(' * Sinh bởi CP22 RealtimeComponentEmitter (fallback mode)')
        lines.append(f' * UI Framework: {ui_fw}')
        lines.append(' *')
        lines.append(' * Cho phép DataTable, CardList tự động refresh khi có event realtime.')
        lines.append(' */')
        lines.append('')
        lines.append('import { useCallback, useRef, useState } from "react";')
        lines.append('')
        lines.append('// Danh sách event topics tự động sinh từ CP05')
        lines.append('const AUTO_REFRESH_TOPICS = [')
        for t in topics:
            lines.append(f'  "{t}",')
        lines.append('];')
        lines.append('')
        lines.append('interface RefreshConfig {')
        lines.append('  debounceMs?: number;')
        lines.append('  throttleMs?: number;')
        lines.append('  topics?: string[];')
        lines.append('}')
        lines.append('')
        lines.append('/**')
        lines.append(' * Hook mixin để enable realtime refresh cho component')
        lines.append(' *')
        lines.append(' * Sử dụng:')
        lines.append(' *   const { subscribeToRefresh } = useRealtimeRefresh();')
        lines.append(' *   useEffect(() => {')
        lines.append(' *     const unsub = subscribeToRefresh(fetchData);')
        lines.append(' *     return unsub;')
        lines.append(' *   }, []);')
        lines.append(' *')
        lines.append(' * @param config - Cấu hình refresh')
        lines.append(' * @returns      - subscribeToRefresh function')
        lines.append(' */')
        lines.append('export function useRealtimeRefresh(config?: RefreshConfig) {')
        lines.append('  const {')
        lines.append('    debounceMs = 300,')
        lines.append('    throttleMs = 1000,')
        lines.append('    topics = AUTO_REFRESH_TOPICS,')
        lines.append('  } = config || {};')
        lines.append('')
        lines.append('  const lastTriggerRef = useRef(0);')
        lines.append('  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);')
        lines.append('')
        lines.append('  const subscribeToRefresh = useCallback(')
        lines.append('    (refreshFn: () => Promise<void>) => {')
        lines.append('      const handler = (event: { channel: string; topic?: string }) => {')
        lines.append('        const topic = event.topic || event.channel;')
        lines.append('        if (!topics.includes(topic)) return;')
        lines.append('')
        lines.append('        const now = Date.now();')
        lines.append('        if (now - lastTriggerRef.current < throttleMs) return;')
        lines.append('        lastTriggerRef.current = now;')
        lines.append('')
        lines.append('        if (timeoutRef.current) clearTimeout(timeoutRef.current);')
        lines.append('        timeoutRef.current = setTimeout(() => {')
        lines.append('          refreshFn().catch(console.error);')
        lines.append('        }, debounceMs);')
        lines.append('      };')
        lines.append('')
        lines.append('      return () => {')
        lines.append('        if (timeoutRef.current) clearTimeout(timeoutRef.current);')
        lines.append('      };')
        lines.append('    },')
        lines.append('    [debounceMs, throttleMs, topics]')
        lines.append('  );')
        lines.append('')
        lines.append('  return { subscribeToRefresh };')
        lines.append('}')
        lines.append('')
        return "\n".join(lines)

    def _fallback_widget_component(
        self, component_name: str, ctx: dict[str, Any],
    ) -> str:
        """Sinh fallback widget component."""
        widget_type = ctx.get("widget_type", "live_feed")
        ui_fw = ctx.get("ui_framework", "material")

        descriptions = {
            "PresenceIndicator": "Hiển thị trạng thái presence (online/offline/typing)",
            "LiveFeed": "Hiển thị realtime event feed (activity stream)",
            "LiveCounter": "Hiển thị số realtime với animated transitions",
            "LiveCursor": "Hiển thị con trỏ multi-user collaborative editing",
            "NotificationToast": "Hiển thị realtime toast notifications",
        }
        desc = descriptions.get(component_name, "Realtime widget")

        lines: list[str] = []
        lines.append('/**')
        lines.append(f' * {component_name} component — {desc}')
        lines.append(' *')
        lines.append(f' * Sinh bởi CP22 RealtimeComponentEmitter (fallback mode)')
        lines.append(f' * UI Framework: {ui_fw}')
        lines.append(f' * Widget Type: {widget_type}')
        lines.append(' */')
        lines.append('')
        lines.append('import React, { useState, useEffect } from "react";')
        lines.append('')
        lines.append(f'interface {component_name}Props {{')
        lines.append('  channel?: string;')
        lines.append('  tenantId?: string;')
        if "LiveFeed" in component_name:
            lines.append('  maxItems?: number;')
            lines.append('  autoScroll?: boolean;')
        if "LiveCounter" in component_name:
            lines.append('  initialValue?: number;')
        lines.append('  className?: string;')
        lines.append('  onEvent?: (data: unknown) => void;')
        lines.append('}')
        lines.append('')
        lines.append(f'export const {component_name}: React.FC<{component_name}Props> = ({{')
        lines.append('  channel = "default",')
        lines.append('  tenantId,')
        if "LiveFeed" in component_name:
            max_items = ctx.get("max_items", 50)
            auto_scroll = ctx.get("auto_scroll", True)
            lines.append(f'  maxItems = {max_items},')
            lines.append(f'  autoScroll = {str(auto_scroll).lower()},')
        if "LiveCounter" in component_name:
            iv = ctx.get("initial_value", 0)
            lines.append(f'  initialValue = {iv},')
        lines.append('  className,')
        lines.append('  onEvent,')
        lines.append('}) => {')
        lines.append('  const [data, setData] = useState<unknown[]>([]);')
        lines.append('')
        lines.append('  useEffect(() => {')
        lines.append('    // Subscribe vào channel realtime')
        lines.append('    return () => { /* cleanup */ };')
        lines.append('  }, [channel, tenantId]);')
        lines.append('')
        lines.append('  return (')
        lines.append('    <div className={`midicoder-${widget_type} ${className || ""}`.trim()}>')
        lines.append(f'      <span>{component_name} (fallback)</span>')
        lines.append('    </div>')
        lines.append('  );')
        lines.append('};')
        lines.append('')
        lines.append(f'export default {component_name};')
        lines.append('')
        return "\n".join(lines)


__all__ = ["RealtimeComponentEmitter", "GeneratedFile"]
