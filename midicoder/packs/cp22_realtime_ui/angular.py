# coding: utf-8
"""
Angular emitter cho CP22 — Real-time UI Generator.

AngularRealtimeEmitter sinh ra:
- 5 Realtime widgets (PresenceIndicator, LiveFeed, LiveCounter, LiveCursor, NotificationToast)
- Channel subscription service (channel-subscription.service.ts)
- Presence service (presence.service.ts)
- Realtime refresh mixin (realtime-refresh-mixin.ts)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import BaseLoader, Environment, FileSystemLoader, TemplateNotFound

from .models import (
    ChannelSpec,
    SUPPORTED_UI_FRAMEWORKS,
    WidgetConfig,
    WidgetType,
)


# Phân giải thư mục template
_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent
_TEMPLATE_DIR = _PACKAGE_DIR / "stacks" / "angular" / "core" / "cp22_realtime_ui"


@dataclass
class GeneratedFile:
    """File đã được sinh ra bởi emitter."""
    path: Path
    content: str
    template: str

    def __post_init__(self) -> None:
        """Chuyển string path sang Path object."""
        self.path = Path(self.path)


# Mapping giữa widget type và template/output files
_WIDGET_TEMPLATE_MAP: dict[WidgetType, tuple[str, str]] = {
    WidgetType.PRESENCE: (
        "PresenceIndicator.component.ts.jinja2",
        "presence-indicator.component.ts",
    ),
    WidgetType.LIVE_FEED: (
        "LiveFeed.component.ts.jinja2",
        "live-feed.component.ts",
    ),
    WidgetType.LIVE_COUNTER: (
        "LiveCounter.component.ts.jinja2",
        "live-counter.component.ts",
    ),
    WidgetType.LIVE_CURSOR: (
        "LiveCursor.component.ts.jinja2",
        "live-cursor.component.ts",
    ),
    WidgetType.NOTIFICATION_TOAST: (
        "NotificationToast.component.ts.jinja2",
        "notification-toast.component.ts",
    ),
}


class AngularRealtimeEmitter:
    """
    Emitter cho Angular realtime components.

    Sinh ra các components và services TypeScript từ ChannelSpec và WidgetConfig.
    """

    SUPPORTED_UI_FRAMEWORKS = SUPPORTED_UI_FRAMEWORKS

    def __init__(self, ui_framework: str = "material") -> None:
        """
        Khởi tạo emitter cho Angular.

        Args:
            ui_framework: UI framework để render (material, tailwind, bootstrap, antd, carbon).
        """
        if ui_framework not in self.SUPPORTED_UI_FRAMEWORKS:
            raise ValueError(
                "UI framework '" + ui_framework + "' không được hỗ trợ. "
                + "Sử dụng: " + str(self.SUPPORTED_UI_FRAMEWORKS)
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
        if self._template_env.loader is None:
            return self._generate_inline_fallback(template_name, context)
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
        Sinh tất cả realtime components và services.

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

        generated.append(self._emit_channel_subscription_service(channels, output_dir))
        generated.append(self._emit_presence_service(channels, output_dir))

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

        generated.append(self._emit_realtime_refresh_mixin(channels, output_dir))
        return generated

    def _emit_channel_subscription_service(
        self, channels: list[ChannelSpec], output_dir: Path | None,
    ) -> GeneratedFile:
        """Sinh channel-subscription.service.ts."""
        ctx = {
            "ui_framework": self.ui_framework,
            "channels": [ch.to_dict() for ch in channels],
            "channel_count": len(channels),
            "has_tenant_channels": any(ch.is_tenant_scoped for ch in channels),
        }
        return self._write_file(
            "channel-subscription.service.ts.jinja2",
            "channel-subscription.service.ts",
            ctx,
            output_dir,
        )

    def _emit_presence_service(
        self, channels: list[ChannelSpec], output_dir: Path | None,
    ) -> GeneratedFile:
        """Sinh presence.service.ts."""
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
            "presence.service.ts.jinja2",
            "presence.service.ts",
            ctx,
            output_dir,
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

    def _emit_realtime_refresh_mixin(
        self, channels: list[ChannelSpec], output_dir: Path | None,
    ) -> GeneratedFile:
        """Sinh realtime-refresh-mixin.ts — realtime mixin service cho CP19."""
        ctx = {
            "ui_framework": self.ui_framework,
            "channels": [ch.to_dict() for ch in channels],
            "channel_topics": [ch.event_topic for ch in channels],
            "channel_count": len(channels),
        }
        return self._write_file(
            "realtime-refresh-mixin.ts.jinja2",
            "realtime-refresh-mixin.ts",
            ctx,
            output_dir,
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
            template="angular/cp22_realtime_ui/" + template_name,
        )

    # ------------------------------------------------------------------
    # Inline fallback generators (khi chưa có Jinja2 template)
    # ------------------------------------------------------------------

    def _generate_inline_fallback(
        self, template_name: str, context: dict[str, Any],
    ) -> str:
        """Sinh nội dung fallback inline khi template không tồn tại."""
        if template_name == "channel-subscription.service.ts.jinja2":
            return self._fallback_channel_service(context)
        elif template_name == "presence.service.ts.jinja2":
            return self._fallback_presence_service(context)
        elif template_name == "realtime-refresh-mixin.ts.jinja2":
            return self._fallback_refresh_mixin(context)
        component_name = re.sub(r"\.(component\.ts)?\.(jinja2)?$", "", template_name)
        return self._fallback_widget_component(component_name, context)

    def _fallback_channel_service(self, ctx: dict[str, Any]) -> str:
        """Sinh fallback cho channel-subscription.service.ts."""
        channels = ctx.get("channels", [])
        has_tenant = ctx.get("has_tenant_channels", False)
        ui_fw = ctx.get("ui_framework", "material")

        lines: list[str] = []
        lines.append("/**")
        lines.append(" * ChannelSubscriptionService — subscribe realtime channels")
        lines.append(" *")
        lines.append(" * Sinh bởi CP22 AngularRealtimeEmitter (fallback mode)")
        lines.append(" * UI Framework: " + ui_fw)
        lines.append(" */")
        lines.append("")
        lines.append('import { Injectable, OnDestroy, OnInit } from "@angular/core";')
        lines.append('import { HttpClient, HttpEvent, HttpEventType } from "@angular/common/http";')
        lines.append("import { Subject, Observable, BehaviorSubject, of, Subscription } from \"rxjs\";")
        lines.append("import { tap, catchError, shareReplay, takeUntil } from \"rxjs/operators\";")
        lines.append("")
        lines.append("// Kiểu channel ID tự động sinh từ CP05 events")
        lines.append("export type ChannelId =")
        for ch in channels:
            cid = ch.get("channel_id", "unknown")
            lines.append("  | '" + cid + "'")
        lines.append("  | string;")
        lines.append("")
        lines.append("export interface MessagePayload {")
        lines.append("  channel: string;")
        lines.append("  data: unknown;")
        lines.append("  timestamp: string;")
        if has_tenant:
            lines.append("  tenant_id: string;")
        lines.append("}")
        lines.append("")
        lines.append("export interface SubscriptionStatus {")
        lines.append("  channelId: string;")
        lines.append("  isConnected: boolean;")
        lines.append("  messages: MessagePayload[];")
        lines.append("}")
        lines.append("")
        lines.append('@Injectable({')
        lines.append("  providedIn: 'root',")
        lines.append("})")
        lines.append("export class ChannelSubscriptionService implements OnDestroy {")
        lines.append("")
        lines.append("  private readonly destroy$ = new Subject<void>();")
        lines.append("  private ws: WebSocket | null = null;")
        lines.append("  private retryCount = 0;")
        lines.append("")
        lines.append("  private messagesSubject = new BehaviorSubject<MessagePayload[]>([]);")
        lines.append("  private connectedSubject = new BehaviorSubject<boolean>(false);")
        lines.append("")
        lines.append("  messages$: Observable<MessagePayload[]> = this.messagesSubject.asObservable();")
        lines.append("  connected$: Observable<boolean> = this.connectedSubject.asObservable();")
        lines.append("")
        lines.append("  constructor(private http: HttpClient) {}")
        lines.append("")
        lines.append("  /**")
        lines.append("   * Subscribe vào realtime channel (WebSocket với SSE fallback)")
        lines.append("   */")
        lines.append("  subscribe(channelId: ChannelId, options?: {")
        lines.append("    url?: string;")
        if has_tenant:
            lines.append("    tenantId?: string;")
        lines.append("    autoReconnect?: boolean;")
        lines.append("    maxRetries?: number;")
        lines.append("  }): void {")
        lines.append("    const url = options?.url || '/ws';")
        lines.append("    const autoReconnect = options?.autoReconnect ?? true;")
        lines.append("    const maxRetries = options?.maxRetries ?? 5;")
        if has_tenant:
            lines.append("    const tenantId = options?.tenantId;")
        lines.append("")
        lines.append("    const params: string[] = [];")
        if has_tenant:
            lines.append("    if (tenantId) params.push('tenant_id=' + tenantId);")
        lines.append("    const query = params.length ? '?' + params.join('&') : '';")
        lines.append("    const wsUrl = 'ws://' + window.location.host + url + '/' + channelId + query;")
        lines.append("")
        lines.append("    this.ws = new WebSocket(wsUrl);")
        lines.append("")
        lines.append("    this.ws.onopen = () => {")
        lines.append("      this.connectedSubject.next(true);")
        lines.append("      this.retryCount = 0;")
        lines.append("    };")
        lines.append("")
        lines.append("    this.ws.onmessage = (event) => {")
        lines.append("      const payload: MessagePayload = JSON.parse(event.data);")
        lines.append("      const current = this.messagesSubject.value;")
        lines.append("      this.messagesSubject.next([...current, payload]);")
        lines.append("    };")
        lines.append("")
        lines.append("    this.ws.onclose = () => {")
        lines.append("      this.connectedSubject.next(false);")
        lines.append("      if (autoReconnect && this.retryCount < maxRetries) {")
        lines.append("        this.retryCount++;")
        lines.append("        setTimeout(() => this.subscribe(channelId, options), 1000 * this.retryCount);")
        lines.append("      }")
        lines.append("    };")
        lines.append("  }")
        lines.append("")
        lines.append("  /**")
        lines.append("   * SSE fallback khi WebSocket không được hỗ trợ")
        lines.append("   */")
        lines.append("  subscribeSSE(channelId: ChannelId, baseUrl?: string): Observable<HttpEvent<string>> {")
        lines.append("    const url = (baseUrl || '/api/sse') + '/' + channelId;")
        lines.append("    return this.http.get(url, { responseType: 'text', observe: 'events' }).pipe(")
        lines.append("      tap((event) => {")
        lines.append("        if (event.type === HttpEventType.Body) {")
        lines.append("          try {")
        lines.append("            const payload: MessagePayload = JSON.parse(event.body);")
        lines.append("            const current = this.messagesSubject.value;")
        lines.append("            this.messagesSubject.next([...current, payload]);")
        lines.append("          } catch (e) {")
        lines.append("            console.error('SSE parse error:', e);")
        lines.append("          }")
        lines.append("        }")
        lines.append("      }),")
        lines.append("      catchError((error) => {")
        lines.append("        console.error('SSE error:', error);")
        lines.append("        return of();")
        lines.append("      }),")
        lines.append("      shareReplay(1)")
        lines.append("    );")
        lines.append("  }")
        lines.append("")
        lines.append("  unsubscribe(channelId?: ChannelId): void {")
        lines.append("    if (this.ws && this.ws.readyState === WebSocket.OPEN) {")
        lines.append("      this.ws.close();")
        lines.append("    }")
        lines.append("  }")
        lines.append("")
        lines.append("  ngOnDestroy(): void {")
        lines.append("    this.unsubscribe();")
        lines.append("    this.destroy$.next();")
        lines.append("    this.destroy$.complete();")
        lines.append("  }")
        lines.append("}")
        lines.append("")

        return "\n".join(lines)

    def _fallback_presence_service(self, ctx: dict[str, Any]) -> str:
        """Sinh fallback cho presence.service.ts."""
        ui_fw = ctx.get("ui_framework", "material")
        presence_ch = ctx.get("presence_channels", [])
        has_tenant = ctx.get("has_tenant_presence", False)

        channel_ids = [ch.get("channel_id", "default") for ch in presence_ch]
        default_ch = channel_ids[0] if channel_ids else "user.presence.changed"

        lines: list[str] = []
        lines.append("/**")
        lines.append(" * PresenceService — quản lý trạng thái presence realtime")
        lines.append(" *")
        lines.append(" * Sinh bởi CP22 AngularRealtimeEmitter (fallback mode)")
        lines.append(" * UI Framework: " + ui_fw)
        lines.append(" */")
        lines.append("")
        lines.append('import { Injectable, OnDestroy } from "@angular/core";')
        lines.append("import { BehaviorSubject, Observable } from \"rxjs\";")
        lines.append("")
        lines.append("export type PresenceStatus = 'online' | 'offline' | 'typing' | 'away';")
        lines.append("")
        lines.append("export interface UserPresence {")
        lines.append("  user_id: string;")
        lines.append("  status: PresenceStatus;")
        lines.append("  last_seen?: string;")
        if has_tenant:
            lines.append("  tenant_id?: string;")
        lines.append("}")
        lines.append("")
        lines.append("export interface PresenceState {")
        lines.append("  users: Map<string, UserPresence>;")
        lines.append("  onlineCount: number;")
        lines.append("  isConnected: boolean;")
        lines.append("}")
        lines.append("")
        lines.append('@Injectable({')
        lines.append("  providedIn: 'root',")
        lines.append("})")
        lines.append("export class PresenceService implements OnDestroy {")
        lines.append("")
        lines.append('  private readonly defaultChannel = "' + default_ch + '";')
        lines.append("")
        lines.append("  private usersSubject = new BehaviorSubject<Map<string, UserPresence>>(new Map());")
        lines.append("  private connectedSubject = new BehaviorSubject<boolean>(false);")
        lines.append("")
        lines.append("  users$: Observable<Map<string, UserPresence>> = this.usersSubject.asObservable();")
        lines.append("  connected$: Observable<boolean> = this.connectedSubject.asObservable();")
        lines.append("")
        lines.append("  constructor() {}")
        lines.append("")
        lines.append("  /**")
        lines.append("   * Tính số user online từ current state")
        lines.append("   */")
        lines.append("  getOnlineCount(): number {")
        lines.append("    const users = this.usersSubject.value;")
        lines.append("    let count = 0;")
        lines.append("    users.forEach((u) => { if (u.status === 'online') count++; });")
        lines.append("    return count;")
        lines.append("  }")
        lines.append("")
        lines.append("  /**")
        lines.append("   * Kiểm tra user có online không")
        lines.append("   */")
        lines.append("  isOnline(userId: string): boolean {")
        lines.append("    return this.usersSubject.value.get(userId)?.status === 'online';")
        lines.append("  }")
        lines.append("")
        lines.append("  /**")
        lines.append("   * Kiểm tra user đang typing không")
        lines.append("   */")
        lines.append("  isTyping(userId: string): boolean {")
        lines.append("    return this.usersSubject.value.get(userId)?.status === 'typing';")
        lines.append("  }")
        lines.append("")
        lines.append("  /**")
        lines.append("   * Cập nhật presence của một user")
        lines.append("   */")
        lines.append("  updateUserPresence(user: UserPresence): void {")
        lines.append("    const current = new Map(this.usersSubject.value);")
        lines.append("    current.set(user.user_id, user);")
        lines.append("    this.usersSubject.next(current);")
        lines.append("  }")
        lines.append("")
        lines.append("  /**")
        lines.append("   * Subscribe vào presence channel")
        lines.append("   */")
        lines.append("  subscribeToPresence(channel?: string, tenantId?: string): void {")
        lines.append("    // Subscribe vào presence channel qua WebSocket")
        lines.append("    this.connectedSubject.next(true);")
        lines.append("  }")
        lines.append("")
        lines.append("  ngOnDestroy(): void {")
        lines.append("    this.usersSubject.complete();")
        lines.append("    this.connectedSubject.complete();")
        lines.append("  }")
        lines.append("}")
        lines.append("")
        return "\n".join(lines)

    def _fallback_refresh_mixin(self, ctx: dict[str, Any]) -> str:
        """Sinh fallback cho realtime-refresh-mixin.ts."""
        topics = ctx.get("channel_topics", [])
        ui_fw = ctx.get("ui_framework", "material")

        lines: list[str] = []
        lines.append("/**")
        lines.append(" * RealtimeRefreshMixin — realtime mixin service cho CP19 components")
        lines.append(" *")
        lines.append(" * Sinh bởi CP22 AngularRealtimeEmitter (fallback mode)")
        lines.append(" * UI Framework: " + ui_fw)
        lines.append(" *")
        lines.append(" * Cho phép DataTable, CardList tự động refresh khi có event realtime.")
        lines.append(" */")
        lines.append("")
        lines.append('import { Injectable, OnDestroy } from "@angular/core";')
        lines.append("import { Subject, Observable, Subscription } from \"rxjs\";")
        lines.append("")
        lines.append("// Danh sách event topics tự động sinh từ CP05")
        lines.append("export const AUTO_REFRESH_TOPICS = [")
        for t in topics:
            lines.append("  \"" + t + "\",")
        lines.append("];")
        lines.append("")
        lines.append("export interface RefreshConfig {")
        lines.append("  debounceMs?: number;")
        lines.append("  throttleMs?: number;")
        lines.append("  topics?: string[];")
        lines.append("}")
        lines.append("")
        lines.append("export interface RefreshEvent {")
        lines.append("  channel: string;")
        lines.append("  topic?: string;")
        lines.append("}")
        lines.append("")
        lines.append('@Injectable({')
        lines.append("  providedIn: 'root',")
        lines.append("})")
        lines.append("export class RealtimeRefreshMixin implements OnDestroy {")
        lines.append("")
        lines.append("  private refreshSubject = new Subject<RefreshEvent>();")
        lines.append("  private lastTrigger = 0;")
        lines.append("  private timeoutId: ReturnType<typeof setTimeout> | null = null;")
        lines.append("")
        lines.append("  refresh$: Observable<RefreshEvent> = this.refreshSubject.asObservable();")
        lines.append("")
        lines.append("  constructor() {}")
        lines.append("")
        lines.append("  /**")
        lines.append("   * Emit refresh event cho các component subscribed")
        lines.append("   */")
        lines.append("  emitRefresh(event: RefreshEvent): void {")
        lines.append("    this.refreshSubject.next(event);")
        lines.append("  }")
        lines.append("")
        lines.append("  /**")
        lines.append("   * Subscribe vào refresh events với debounce/throttle")
        lines.append("   *")
        lines.append("   * Sử dụng:")
        lines.append("   *   const sub = mixin.subscribeToRefresh(fetchData, config);")
        lines.append("   *   // trong ngOnDestroy: sub.unsubscribe();")
        lines.append("   */")
        lines.append("  subscribeToRefresh(")
        lines.append("    refreshFn: () => Promise<void>,")
        lines.append("    config?: RefreshConfig")
        lines.append("  ): Subscription {")
        lines.append("    const debounceMs = config?.debounceMs ?? 300;")
        lines.append("    const throttleMs = config?.throttleMs ?? 1000;")
        lines.append("    const topics = config?.topics ?? AUTO_REFRESH_TOPICS;")
        lines.append("")
        lines.append("    return this.refresh$.subscribe((event) => {")
        lines.append("      const topic = event.topic || event.channel;")
        lines.append("      if (!topics.includes(topic)) return;")
        lines.append("")
        lines.append("      const now = Date.now();")
        lines.append("      if (now - this.lastTrigger < throttleMs) return;")
        lines.append("      this.lastTrigger = now;")
        lines.append("")
        lines.append("      if (this.timeoutId) clearTimeout(this.timeoutId);")
        lines.append("      this.timeoutId = setTimeout(() => {")
        lines.append("        refreshFn().catch(console.error);")
        lines.append("      }, debounceMs);")
        lines.append("    });")
        lines.append("  }")
        lines.append("")
        lines.append("  ngOnDestroy(): void {")
        lines.append("    if (this.timeoutId) clearTimeout(this.timeoutId);")
        lines.append("    this.refreshSubject.complete();")
        lines.append("  }")
        lines.append("}")
        lines.append("")
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

        # PascalCase -> kebab-case cho selector
        kebab_name = re.sub(
            r"(?<!^)(?=[A-Z])", "-", component_name
        ).lower()

        # Tạo Angular decorator metadata
        lines: list[str] = []
        lines.append("/**")
        lines.append(" * " + component_name + " component — " + desc)
        lines.append(" *")
        lines.append(" * Sinh bởi CP22 AngularRealtimeEmitter (fallback mode)")
        lines.append(" * UI Framework: " + ui_fw)
        lines.append(" * Widget Type: " + widget_type)
        lines.append(" */")
        lines.append("")
        lines.append('import { Component, Input, Output, OnInit, OnDestroy, ChangeDetectionStrategy } from "@angular/core";')
        lines.append("import { Subject, Subscription } from \"rxjs\";")
        lines.append("")
        lines.append("export interface " + component_name + "Event {")
        lines.append("  channel: string;")
        lines.append("  data: unknown;")
        lines.append("  timestamp: string;")
        lines.append("}")
        lines.append("")
        lines.append("@Component({")
        lines.append("  selector: 'mc-" + kebab_name + "',")
        lines.append('  template: `')
        lines.append("    <div class=\"midicoder-" + widget_type + " {{ className }}\">")
        lines.append("      <ng-content></ng-content>")
        lines.append("    </div>")
        lines.append("  `,")
        lines.append("  changeDetection: ChangeDetectionStrategy.OnPush,")
        lines.append("})")
        lines.append("export class " + component_name + "Component implements OnInit, OnDestroy {")
        lines.append("")
        lines.append('  @Input() channel: string = "default";')
        lines.append("  @Input() tenantId?: string;")
        if "LiveFeed" in component_name:
            max_items = ctx.get("max_items", 50)
            auto_scroll = ctx.get("auto_scroll", True)
            lines.append("  @Input() maxItems: number = " + str(max_items) + ";")
            lines.append("  @Input() autoScroll: boolean = " + str(auto_scroll) + ";")
        if "LiveCounter" in component_name:
            iv = ctx.get("initial_value", 0)
            lines.append("  @Input() initialValue: number = " + str(iv) + ";")
        lines.append("  @Input() className?: string;")
        lines.append("  @Output() event = new Subject<" + component_name + "Event>();")
        lines.append("")
        lines.append("  protected destroy$ = new Subject<void>();")
        lines.append("  protected subscriptions: Subscription[] = [];")
        lines.append("")
        lines.append("  ngOnInit(): void {")
        lines.append("    // Subscribe vào channel realtime")
        lines.append("  }")
        lines.append("")
        lines.append("  ngOnDestroy(): void {")
        lines.append("    this.destroy$.next();")
        lines.append("    this.destroy$.complete();")
        lines.append("    this.subscriptions.forEach((s) => s.unsubscribe());")
        lines.append("    this.event.complete();")
        lines.append("  }")
        lines.append("}")
        lines.append("")
        return "\n".join(lines)


__all__ = ["AngularRealtimeEmitter", "GeneratedFile"]
