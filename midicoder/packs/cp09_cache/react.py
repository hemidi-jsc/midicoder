# coding: utf-8
"""
CP09: React Cache Emitter.

Module này cung cấp ReactEmitter để generate React cache code
từ CacheCollection (CP09):
- useCache.ts - Custom hook để sử dụng cache
- CacheProvider.tsx - React context để quản lý cache state
- cache-utils.ts - Utilities cho cache operations
- cache.types.ts - TypeScript interfaces

KPI-029: Tenant-aware caching qua key prefix.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from midicoder.packs.cp09_cache.models import CacheCollection, CacheBackend
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
# React Cache Emitter
# ============================================================================


class ReactEmitter:
    """
    Emitter cho React cache code.

    Generate code từ CacheCollection cho:
    - src/cache/cache.types.ts
    - src/cache/CacheProvider.tsx
    - src/cache/useCache.ts
    - src/cache/cache-utils.ts
    - src/cache/index.ts
    """

    def __init__(self, stack_dir: Path) -> None:
        """
        Khởi tạo ReactEmitter.

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
        Emit React cache code từ CacheCollection.

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
                ErrorCode.CP09_KEY_EMPTY,
                detail="CacheCollection không có profiles để emit",
            )

        files: list[GeneratedFile] = []
        cache_dir = output_dir / "src" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        files.append(self._emit_types(collection, cache_dir))
        files.append(self._emit_cache_provider(collection, cache_dir))
        files.append(self._emit_use_cache(cache_dir))
        files.append(self._emit_cache_utils(cache_dir))
        files.append(self._emit_index(cache_dir))

        return files

    def _emit_types(
        self,
        collection: CacheCollection,
        output_dir: Path,
    ) -> GeneratedFile:
        """Emit cache.types.ts - TypeScript interfaces cho cache."""
        default_ttl = collection.profiles[0].ttl if collection.profiles else 300

        content = f'''/**
 * Cache Types - CP09.
 *
 * TypeScript interfaces cho caching layer.
 * KPI-029: Tenant-aware caching.
 */

/** Strategy caching */
export type CacheStrategyType = "read_through" | "write_through" | "cache_aside";

/** Backend cache */
export type CacheBackend = "redis" | "memory";

/** Cache entry đã lưu */
export interface CacheEntry<T = any> {{
  key: string;
  value: T;
  ttl: number;
  tenant_id?: string;
  created_at: number;
}}

/** Kết quả từ cache operation */
export interface CacheResult<T = any> {{
  hit: boolean;
  value: T | null;
  key: string;
}}

/** Config cho CacheProvider context */
export interface CacheContextConfig {{
  defaultTtl: number;
  tenantId?: string;
}}

/** Context type cho CacheProvider */
export interface CacheContextType {{
  get: <T = any>(key: string) => CacheResult<T>;
  set: <T = any>(key: string, value: T, ttl?: number) => void;
  delete: (key: string) => boolean;
  invalidate: (pattern: string) => number;
  clear: () => void;
  tenantId: string | undefined;
  setTenantId: (id: string | undefined) => void;
  defaultTtl: number;
}}
'''
        file_path = output_dir / "cache.types.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="cache/cache.types.ts.jinja2", capability="CP09",
        )

    def _emit_cache_provider(
        self,
        collection: CacheCollection,
        output_dir: Path,
    ) -> GeneratedFile:
        """Emit CacheProvider.tsx - React context để quản lý cache."""
        has_redis = any(p.backend == CacheBackend.REDIS for p in collection.profiles)
        backends = "Redis + Memory" if has_redis and len(collection.profiles) > 1 else ("Redis" if has_redis else "Memory")
        default_ttl = collection.profiles[0].ttl if collection.profiles else 300

        content = f'''/**
 * Cache Provider - CP09.
 *
 * React context để cung cấp caching capabilities cho toàn bộ app.
 * KPI-029: Tenant-aware caching.
 *
 * Backends: {backends}
 * Default TTL: {default_ttl} giây
 */

import {{
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
}} from "react";
import {{ CacheContextType, CacheResult, CacheEntry }} from "./cache.types";
import {{ buildKey, matchPattern }} from "./cache-utils";

const CacheContext = createContext<CacheContextType | undefined>(undefined);

export interface CacheProviderProps {{
  children: ReactNode;
  defaultTtl?: number;
  initialTenantId?: string;
}}

/** CacheProvider - wrap app để cung cấp cache context */
export function CacheProvider({{
  children,
  defaultTtl = {default_ttl},
  initialTenantId,
}}: CacheProviderProps) {{
  const [store, setStore] = useState<Map<string, CacheEntry>>(new Map());
  const [tenantId, setTenantIdState] = useState<string | undefined>(initialTenantId);

  /** Lấy giá trị từ cache (KPI-029: tenant-aware) */
  const get = useCallback(<T = any>(key: string): CacheResult<T> => {{
    const fullKey = buildKey(key, tenantId);
    const entry = store.get(fullKey);

    if (!entry) {{
      return {{ hit: false, value: null, key }};
    }}

    // Kiểm tra expiry
    if (entry.ttl > 0 && Date.now() > entry.created_at + entry.ttl * 1000) {{
      setStore(prev => {{
        const next = new Map(prev);
        next.delete(fullKey);
        return next;
      }});
      return {{ hit: false, value: null, key }};
    }}

    return {{ hit: true, value: entry.value as T, key }};
  }}, [store, tenantId]);

  /** Lưu giá trị vào cache (KPI-029: tenant-aware) */
  const set = useCallback(<T = any>(
    key: string,
    value: T,
    ttl?: number,
  ): void => {{
    const fullKey = buildKey(key, tenantId);
    setStore(prev => {{
      const next = new Map(prev);
      next.set(fullKey, {{
        key: fullKey,
        value,
        ttl: ttl || defaultTtl,
        tenant_id: tenantId,
        created_at: Date.now(),
      }});
      return next;
    }});
  }}, [defaultTtl, tenantId]);

  /** Xóa key khỏi cache (KPI-029: tenant-aware) */
  const deleteItem = useCallback((key: string): boolean => {{
    const fullKey = buildKey(key, tenantId);
    let deleted = false;
    setStore(prev => {{
      if (prev.has(fullKey)) {{
        deleted = true;
        const next = new Map(prev);
        next.delete(fullKey);
        return next;
      }}
      return prev;
    }});
    return deleted;
  }}, [tenantId]);

  /** Invalidate batch keys theo pattern (KPI-029: tenant-aware) */
  const invalidate = useCallback((pattern: string): number => {{
    let deleted = 0;
    setStore(prev => {{
      const next = new Map(prev);
      for (const key of next.keys()) {{
        if (matchPattern(key, pattern)) {{
          next.delete(key);
          deleted++;
        }}
      }}
      return next;
    }});
    return deleted;
  }}, []);

  /** Xóa toàn bộ cache */
  const clear = useCallback(() => {{
    setStore(new Map());
  }}, []);

  /** Đặt tenant ID (KPI-029) */
  const setTenantId = useCallback((id: string | undefined) => {{
    setTenantIdState(id);
  }}, []);

  const value: CacheContextType = {{
    get,
    set,
    delete: deleteItem,
    invalidate,
    clear,
    tenantId,
    setTenantId,
    defaultTtl,
  }};

  return (
    <CacheContext.Provider value={{value}}>
      {{children}}
    </CacheContext.Provider>
  );
}}
'''
        file_path = output_dir / "CacheProvider.tsx"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="cache/CacheProvider.tsx.jinja2", capability="CP09",
        )

    def _emit_use_cache(self, output_dir: Path) -> GeneratedFile:
        """Emit useCache.ts - Custom hook."""
        content = '''/**
 * useCache Hook - CP09.
 *
 * Custom hook để sử dụng cache từ CacheProvider context.
 * KPI-029: Tenant-aware caching.
 */

import { useContext } from "react";
import { CacheContext } from "./CacheProvider";
import { CacheContextType } from "./cache.types";

/**
 * Hook để truy cập cache operations.
 *
 * @throws Error nếu dùng bên ngoài CacheProvider
 *
 * @example
 *   const { get, set, delete, invalidate } = useCache();
 *   const data = get<User>("user:123");
 */
export function useCache(): CacheContextType {
  const context = useContext(CacheContext);

  if (context === undefined) {
    throw new Error("useCache phải dùng bên trong CacheProvider");
  }

  return context;
}
'''
        file_path = output_dir / "useCache.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="cache/useCache.ts.jinja2", capability="CP09",
        )

    def _emit_cache_utils(self, output_dir: Path) -> GeneratedFile:
        """Emit cache-utils.ts - Utilities."""
        content = '''/**
 * Cache Utilities - CP09.
 *
 * Helper functions cho cache operations.
 * KPI-029: Tenant-aware key building.
 */

/**
 * Xây dựng cache key với tenant prefix (KPI-029).
 *
 * @param key Cache key gốc
 * @param tenantId Tenant ID (optional)
 * @returns Cache key đã prefix
 */
export function buildKey(key: string, tenantId?: string): string {
  return tenantId ? `${tenantId}::${key}` : key;
}

/**
 * Simple glob pattern matching.
 *
 * @param key Key để kiểm tra
 * @param pattern Glob pattern (ví dụ: "user:*")
 * @returns True nếu key match pattern
 */
export function matchPattern(key: string, pattern: string): boolean {
  const regex = new RegExp("^" + pattern.replace(/\\*/g, ".*") + "$");
  return regex.test(key);
}

/**
 * Kiểm tra cache entry đã expire chưa.
 *
 * @param entry Cache entry
 * @returns True nếu đã expire
 */
export function isExpired(entry: {{ ttl: number; created_at: number }}): boolean {
  if (entry.ttl <= 0) return false;
  return Date.now() > entry.created_at + entry.ttl * 1000;
}
'''
        file_path = output_dir / "cache-utils.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="cache/cache-utils.ts.jinja2", capability="CP09",
        )

    def _emit_index(self, output_dir: Path) -> GeneratedFile:
        """Emit index.ts."""
        content = '''/**
 * Cache Module Exports - CP09.
 */
export * from "./cache.types";
export * from "./CacheProvider";
export * from "./useCache";
export * from "./cache-utils";
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


def emit_react_cache(
    collection: CacheCollection,
    stack_dir: Path,
    output_dir: Path,
) -> list[GeneratedFile]:
    """
    Emit React cache code từ CacheCollection.

    Args:
        collection: CacheCollection instance
        stack_dir: Templates directory
        output_dir: Output directory

    Returns:
        List of GeneratedFile instances
    """
    emitter = ReactEmitter(stack_dir)
    return emitter.emit(collection, output_dir)
