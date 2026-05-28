# coding: utf-8
"""
CP09: Angular Cache Emitter.

Module này cung cấp AngularEmitter để generate Angular cache code
từ CacheCollection (CP09):
- CacheService - Service để get/set/invalidate cache
- CacheInterceptor - HTTP interceptor để cache API responses
- CacheModule - NgModule để export cache providers

KPI-029: Tenant-aware caching qua key prefix.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from midicoder.packs.cp_backend_cache.models import CacheCollection, CacheBackend
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ============================================================================
# Generated File
# ============================================================================


@dataclass
class GeneratedFile:
    """
    File đã generate từ emitter.

    Attributes:
        path: Đường dẫn file
        content: Nội dung file
        template: Tên template
        capability: Core Capability code (CP09)
    """
    path: Path
    content: str
    template: str
    capability: str


# ============================================================================
# Angular Cache Emitter
# ============================================================================


class AngularEmitter:
    """
    Emitter cho Angular cache code.

    Generate code từ CacheCollection cho:
    - src/app/core/cache/cache.service.ts
    - src/app/core/cache/cache.interceptor.ts
    - src/app/core/cache/cache.module.ts
    - src/app/core/cache/cache.models.ts
    - src/app/core/cache/index.ts
    """

    def __init__(self, stack_dir: Path) -> None:
        """
        Khởi tạo AngularEmitter.

        Args:
            stack_dir: Đường dẫn đến templates directory
        """
        self.stack_dir = stack_dir

    def emit(
        self,
        collection: CacheCollection,
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """
        Emit Angular cache code từ CacheCollection.

        Args:
            collection: CacheCollection instance
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances

        Raises:
            MidicoderError: Nếu collection rỗng
        """
        if not collection.profiles:
            EM.raise_error(
                ErrorCode.MDC-BE02_KEY_EMPTY,
                detail="CacheCollection không có profiles để emit",
            )

        files: list[GeneratedFile] = []
        cache_dir = output_dir / "src" / "app" / "core" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        files.append(self._emit_models(cache_dir))
        files.append(self._emit_cache_service(collection, cache_dir))
        files.append(self._emit_cache_interceptor(cache_dir))
        files.append(self._emit_cache_module(collection, cache_dir))
        files.append(self._emit_index(cache_dir))

        return files

    def _emit_models(self, output_dir: Path) -> GeneratedFile:
        """Emit cache.models.ts - TypeScript interfaces cho cache."""
        content = '''/**
 * Cache Models - CP09.
 *
 * TypeScript interfaces cho caching layer.
 * KPI-029: Tenant-aware caching.
 */

/** Strategy caching */
export type CacheStrategyType = "read_through" | "write_through" | "cache_aside";

/** Backend cache */
export type CacheBackend = "redis" | "memory";

/** Profile cache */
export interface CacheProfileConfig {
  id: string;
  backend: CacheBackend;
  ttl: number;
  max_size?: number;
  serializer: string;
  key_prefix: string;
  tenant_isolated: boolean;
}

/** Cache entry đã được lưu */
export interface CacheEntry<T = any> {
  key: string;
  value: T;
  ttl: number;
  tenant_id?: string;
  created_at: number;
}

/** Kết quả từ cache operation */
export interface CacheResult<T = any> {
  hit: boolean;
  value: T | null;
  key: string;
}
'''
        file_path = output_dir / "cache.models.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="cache/cache.models.ts.jinja2", capability="CP09",
        )

    def _emit_cache_service(
        self,
        collection: CacheCollection,
        output_dir: Path,
    ) -> GeneratedFile:
        """Emit cache.service.ts."""
        has_redis = any(p.backend == CacheBackend.REDIS for p in collection.profiles)
        has_memory = any(p.backend == CacheBackend.MEMORY for p in collection.profiles)
        default_ttl = collection.profiles[0].ttl if collection.profiles else 300

        # Generate profile config lines
        profile_lines = ""
        for profile in collection.profiles:
            profile_lines += (
                f"  {{ id: '{profile.id}', backend: '{profile.backend.value}', "
                f"ttl: {profile.ttl}, tenant_isolated: {profile.tenant_isolated} }},\n"
            )

        backend_desc = "Redis + Memory" if has_redis and has_memory else ("Redis" if has_redis else "Memory")

        # Use template string (not f-string) to avoid TypeScript ${{}} conflicts
        content = (
            '/**\n'
            ' * Cache Service - CP09.\n'
            ' *\n'
            ' * Service nay xu ly caching cho Angular application.\n'
            ' * KPI-029: Tenant-aware cache key prefixing.\n'
            ' *\n'
            f' * Backends: {backend_desc}\n'
            f' * Default TTL: {default_ttl} giay\n'
            ' */\n'
            '\n'
            'import { Injectable } from "@angular/core";\n'
            'import { HttpClient } from "@angular/common/http";\n'
            'import { Observable, of, BehaviorSubject } from "rxjs";\n'
            'import { CacheEntry, CacheResult, CacheProfileConfig } from "./cache.models";\n'
            '\n'
            '@Injectable({\n'
            '  providedIn: "root",\n'
            '})\n'
            'export class CacheService {\n'
            '  private memoryStore: Map<string, CacheEntry> = new Map();\n'
            '  private tenantId$ = new BehaviorSubject<string | undefined>(undefined);\n'
            f'  private defaultTtl = {default_ttl};\n'
            '\n'
            '  /** Cache profiles da cau hinh */\n'
            '  private profiles: CacheProfileConfig[] = [\n'
            + profile_lines
            + '  ];\n'
            '\n'
            '  constructor(private http: HttpClient) {}\n'
            '\n'
            '  /**\n'
            '   * Dat tenant ID cho tenant isolation (KPI-029).\n'
            '   */\n'
            '  setTenantId(tenantId: string | undefined): void {\n'
            '    this.tenantId$.next(tenantId);\n'
            '  }\n'
            '\n'
            '  /**\n'
            '   * Xay dung cache key voi tenant prefix (KPI-029).\n'
            '   */\n'
            '  private _buildKey(key: string, tenantId?: string): string {\n'
            '    const tid = tenantId || this.tenantId$.value;\n'
            '    return tid ? `${tid}::${key}` : key;\n'
            '  }\n'
            '\n'
            '  /**\n'
            '   * Lay gia tri tu cache.\n'
            '   */\n'
            '  get<T = any>(key: string, tenantId?: string): CacheResult<T> {\n'
            '    const fullKey = this._buildKey(key, tenantId);\n'
            '    const entry = this.memoryStore.get(fullKey);\n'
            '\n'
            '    if (!entry) {\n'
            '      return { hit: false, value: null, key };\n'
            '    }\n'
            '\n'
            '    // Kiem tra expiry\n'
            '    if (entry.ttl > 0 && Date.now() > entry.created_at + entry.ttl * 1000) {\n'
            '      this.memoryStore.delete(fullKey);\n'
            '      return { hit: false, value: null, key };\n'
            '    }\n'
            '\n'
            '    return { hit: true, value: entry.value as T, key };\n'
            '  }\n'
            '\n'
            '  /**\n'
            '   * Luu gia tri vao cache.\n'
            '   */\n'
            '  set<T = any>(\n'
            '    key: string,\n'
            '    value: T,\n'
            '    ttl?: number,\n'
            '    tenantId?: string,\n'
            '  ): void {\n'
            '    const fullKey = this._buildKey(key, tenantId);\n'
            '    this.memoryStore.set(fullKey, {\n'
            '      key: fullKey,\n'
            '      value,\n'
            '      ttl: ttl || this.defaultTtl,\n'
            '      tenant_id: tenantId,\n'
            '      created_at: Date.now(),\n'
            '    });\n'
            '  }\n'
            '\n'
            '  /**\n'
            '   * Xoa key khoi cache.\n'
            '   */\n'
            '  delete(key: string, tenantId?: string): boolean {\n'
            '    const fullKey = this._buildKey(key, tenantId);\n'
            '    return this.memoryStore.delete(fullKey);\n'
            '  }\n'
            '\n'
            '  /**\n'
            '   * Invalidate batch keys theo pattern.\n'
            '   */\n'
            '  invalidatePattern(pattern: string, tenantId?: string): number {\n'
            '    const prefix = this._buildKey("", tenantId);\n'
            '    let deleted = 0;\n'
            '    for (const key of this.memoryStore.keys()) {\n'
            '      if (key.startsWith(prefix) || this._matchPattern(key, pattern)) {\n'
            '        this.memoryStore.delete(key);\n'
            '        deleted++;\n'
            '      }\n'
            '    }\n'
            '    return deleted;\n'
            '  }\n'
            '\n'
            '  /**\n'
            '   * Xoa toan bo cache.\n'
            '   */\n'
            '  clear(): void {\n'
            '    this.memoryStore.clear();\n'
            '  }\n'
            '\n'
            '  /**\n'
            '   * Simple glob pattern matching.\n'
            '   */\n'
            '  private _matchPattern(key: string, pattern: string): boolean {\n'
            '    const regex = new RegExp("^" + pattern.replace(/\\*/g, ".*") + "$");\n'
            '    return regex.test(key);\n'
            '  }\n'
            '}\n'
        )

        file_path = output_dir / "cache.service.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="cache/cache.service.ts.jinja2", capability="CP09",
        )

    def _emit_cache_interceptor(self, output_dir: Path) -> GeneratedFile:
        """Emit cache.interceptor.ts."""
        content = '''/**
 * Cache Interceptor - CP09.
 *
 * HTTP interceptor để tự động cache GET requests.
 * KPI-029: Tenant-aware caching qua header x-tenant-id.
 */

import { Injectable } from "@angular/core";
import {
  HttpInterceptor,
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpResponse,
} from "@angular/common/http";
import { Observable, of } from "rxjs";
import { tap } from "rxjs/operators";
import { CacheService } from "./cache.service";

@Injectable({
  providedIn: "root",
})
export class CacheInterceptor implements HttpInterceptor {
  constructor(private cacheService: CacheService) {}

  intercept(
    req: HttpRequest<unknown>,
    next: HttpHandler,
  ): Observable<HttpEvent<unknown>> {
    // Chỉ cache GET requests
    if (req.method !== "GET") {
      return next.handle(req);
    }

    // KPI-029: Lấy tenant ID từ header
    const tenantId = req.headers.get("x-tenant-id") || undefined;
    const cacheKey = `http:${req.urlWithParams}`;

    // Kiểm tra cache
    const cached = this.cacheService.get(cacheKey, tenantId);
    if (cached.hit) {
      return of(new HttpResponse({{ body: cached.value }}));
    }

    // Cache miss — gọi API và lưu kết quả
    return next.handle(req).pipe(
      tap((event) => {
        if (event instanceof HttpResponse) {
          this.cacheService.set(cacheKey, event.body, 300, tenantId);
        }
      }),
    );
  }
}
'''
        file_path = output_dir / "cache.interceptor.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="cache/cache.interceptor.ts.jinja2", capability="CP09",
        )

    def _emit_cache_module(
        self,
        collection: CacheCollection,
        output_dir: Path,
    ) -> GeneratedFile:
        """Emit cache.module.ts."""
        content = '''/**
 * Cache Module - CP09.
 *
 * Module này cung cấp caching services và interceptors.
 * KPI-029: Tenant-aware caching.
 */

import { NgModule } from "@angular/core";
import { CommonModule } from "@angular/common";
import { HTTP_INTERCEPTORS } from "@angular/common/http";
import { CacheInterceptor } from "./cache.interceptor";

@NgModule({
  imports: [CommonModule],
  providers: [
    {
      provide: HTTP_INTERCEPTORS,
      useClass: CacheInterceptor,
      multi: true,
    },
  ],
})
export class CacheNgModule {}
'''
        file_path = output_dir / "cache.module.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="cache/cache.module.ts.jinja2", capability="CP09",
        )

    def _emit_index(self, output_dir: Path) -> GeneratedFile:
        """Emit index.ts."""
        content = '''/**
 * Cache Module Exports - CP09.
 */
export * from "./cache.module";
export * from "./cache.service";
export * from "./cache.interceptor";
export * from "./cache.models";
'''
        file_path = output_dir / "index.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="cache/index.ts.jinja2", capability="CP09",
        )


# ============================================================================
# Convenience Function
# ============================================================================


def emit_angular_cache(
    collection: CacheCollection,
    stack_dir: Path,
    output_dir: Path,
) -> list[GeneratedFile]:
    """
    Emit Angular cache code từ CacheCollection.

    Args:
        collection: CacheCollection instance
        stack_dir: Templates directory
        output_dir: Output directory

    Returns:
        List of GeneratedFile instances
    """
    emitter = AngularEmitter(stack_dir)
    return emitter.emit(collection, output_dir)
