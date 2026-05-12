# coding: utf-8
"""
CP14: React Audit Trail Emitter.

Module này cung cấp ReactAuditComplianceEmitter để generate React audit code
từ AuditComplianceCollection (CP14):
- types.ts - TypeScript interfaces cho audit layer
- useAudit.ts - Custom hook để log/query audit
- AuditLogList.tsx - Component hiển thị audit logs với filter

KPI-029: Tenant-aware audit logging qua header x-tenant-id.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any, Dict

from midicoder.emitters.core.cp14_audit_compliance.models import AuditComplianceCollection


class ReactAuditComplianceEmitter:
    """
    Emitter sinh code React cho audit trail & compliance.

    Methods:
        generate(): Generate toàn bộ files
        generate_types(): Sinh TypeScript interfaces
        generate_hook(): Sinh useAudit hook
        generate_component(): Sinh AuditLogList component
    """

    def __init__(self, collection: AuditComplianceCollection | None = None) -> None:
        """
        Khởi tạo ReactAuditComplianceEmitter.

        Args:
            collection: AuditComplianceCollection (optional)
        """
        self.collection = collection or AuditComplianceCollection()

    def generate(self) -> Dict[str, str]:
        """
        Generate toàn bộ files React.

        Returns:
            Dict {file_path: source_code}
        """
        result: Dict[str, str] = {}
        result.update(self.generate_types())
        result.update(self.generate_hook())
        result.update(self.generate_component())
        return result

    def generate_types(self) -> Dict[str, str]:
        """Sinh TypeScript interfaces cho audit."""
        code = '''/**
 * Audit Types - CP14.
 *
 * TypeScript interfaces cho audit trail layer.
 * Dùng cho React frontend audit logging và query.
 */

/** Hành động audit */
export enum AuditAction {
  CREATE = "CREATE",
  UPDATE = "UPDATE",
  DELETE = "DELETE",
  READ = "READ",
  LOGIN = "LOGIN",
  LOGOUT = "LOGOUT",
  EXPORT = "EXPORT",
  APPROVE = "APPROVE",
  REJECT = "REJECT",
  CUSTOM = "CUSTOM",
}

/** Loại actor thực hiện hành động */
export type ActorType = "user" | "system" | "background_job";

/** Payload để ghi audit log */
export interface AuditLogPayload {
  action: string;
  entity_type: string;
  entity_id: string;
  actor_id: string;
  actor_type?: ActorType;
  tenant_id?: string;
  old_values?: Record<string, any>;
  new_values?: Record<string, any>;
  metadata?: Record<string, any>;
}

/** Audit log entry trả về từ API */
export interface AuditLogEntry {
  id: string;
  timestamp: string;
  action: string;
  entity_type: string;
  entity_id: string;
  actor_id: string;
  actor_type: string;
  tenant_id: string;
  old_values?: Record<string, any>;
  new_values?: Record<string, any>;
  metadata?: Record<string, any>;
  immutable_hash: string;
}

/** Query params để lọc audit logs */
export interface AuditQueryParams {
  entity_type?: string;
  actor_id?: string;
  tenant_id?: string;
  action?: string;
  limit?: number;
  offset?: number;
}

/** Kết quả query audit logs */
export interface AuditQueryResult {
  entries: AuditLogEntry[];
  total: number;
  limit: number;
  offset: number;
}

/** Return type của useAudit hook */
export interface UseAuditReturn {
  log: (payload: AuditLogPayload) => Promise<string>;
  query: (params?: AuditQueryParams) => Promise<AuditQueryResult>;
  getEntityAuditTrail: (
    entityType: string,
    entityId: string,
    limit?: number,
  ) => Promise<AuditLogEntry[]>;
  tenantId: string | undefined;
  setTenantId: (id: string | undefined) => void;
}
'''
        return {"src/audit/types.ts": code}

    def generate_hook(self) -> Dict[str, str]:
        """Sinh useAudit hook — Custom hook cho audit operations."""
        code = '''/**
 * useAudit Hook - CP14.
 *
 * Custom hook để ghi audit log và query audit history.
 * Sử dụng fetch API cho HTTP operations.
 * Auto-includes tenant ID trong headers (nếu có).
 */

import { useCallback, useState, useMemo } from "react";
import {
  AuditLogPayload,
  AuditQueryParams,
  AuditQueryResult,
  AuditLogEntry,
  UseAuditReturn,
} from "./types";

/**
 * Hook để truy cập audit operations.
 *
 * @param apiBase - API base URL (mặc định "/api/v1")
 * @param initialTenantId - Tenant ID ban đầu (optional)
 *
 * @example
 *   const { log, query } = useAudit("/api/v1");
 *   await log({ action: "CREATE", entity_type: "Order", entity_id: "123", actor_id: "user_1" });
 */
export function useAudit(
  apiBase: string = "/api/v1",
  initialTenantId?: string,
): UseAuditReturn {
  const [tenantId, setTenantIdState] = useState<string | undefined>(initialTenantId);

  /** Xây dựng headers với tenant ID */
  const buildHeaders = useCallback((): Record<string, string> => {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (tenantId) headers["x-tenant-id"] = tenantId;
    return headers;
  }, [tenantId]);

  /** Ghi audit log entry */
  const log = useCallback(
    async (payload: AuditLogPayload): Promise<string> => {
      const response = await fetch(`${apiBase}/audit/log`, {
        method: "POST",
        headers: buildHeaders(),
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(`Ghi audit log thất bại: ${response.status}`);
      }
      return response.text();
    },
    [apiBase, buildHeaders],
  );

  /** Query audit logs với filters */
  const query = useCallback(
    async (params: AuditQueryParams = {}): Promise<AuditQueryResult> => {
      const qs = new URLSearchParams();
      if (params.entity_type) qs.set("entity_type", params.entity_type);
      if (params.actor_id) qs.set("actor_id", params.actor_id);
      if (params.tenant_id) qs.set("tenant_id", params.tenant_id);
      if (params.action) qs.set("action", params.action);
      if (params.limit) qs.set("limit", params.limit.toString());
      if (params.offset) qs.set("offset", params.offset.toString());

      const url = qs.toString() ? `${apiBase}/audit/query?${qs}` : `${apiBase}/audit/query`;
      const response = await fetch(url, { method: "GET", headers: buildHeaders() });
      if (!response.ok) throw new Error(`Query audit logs thất bại: ${response.status}`);
      return response.json();
    },
    [apiBase, buildHeaders],
  );

  /** Lấy audit trail cho một entity cụ thể */
  const getEntityAuditTrail = useCallback(
    async (entityType: string, entityId: string, limit: number = 100): Promise<AuditLogEntry[]> => {
      const response = await fetch(
        `${apiBase}/audit/entity/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}?limit=${limit}`,
        { method: "GET", headers: buildHeaders() },
      );
      if (!response.ok) throw new Error(`Lấy audit trail thất bại: ${response.status}`);
      return response.json();
    },
    [apiBase, buildHeaders],
  );

  /** Đặt tenant ID */
  const setTenantId = useCallback((id: string | undefined) => {
    setTenantIdState(id);
  }, []);

  return useMemo(
    () => ({ log, query, getEntityAuditTrail, tenantId, setTenantId }),
    [log, query, getEntityAuditTrail, tenantId, setTenantId],
  );
}
'''
        return {"src/audit/useAudit.ts": code}

    def generate_component(self) -> Dict[str, str]:
        """Sinh AuditLogList component — Component hiển thị audit logs."""
        code = '''/**
 * Audit Log List Component - CP14.
 *
 * React component hiển thị danh sách audit logs với filter và pagination.
 * Cho phép lọc theo entity_type, actor_id, action.
 */

import { useState, useEffect, useCallback } from "react";
import { useAudit } from "./useAudit";
import { AuditLogEntry, AuditQueryParams } from "./types";

export interface AuditLogListProps {
  defaultEntityType?: string;
  pageSize?: number;
  apiBase?: string;
}

export function AuditLogList({
  defaultEntityType = "",
  pageSize = 50,
  apiBase,
}: AuditLogListProps) {
  const audit = useAudit(apiBase);
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterEntityType, setFilterEntityType] = useState(defaultEntityType);
  const [filterActorId, setFilterActorId] = useState("");
  const [filterAction, setFilterAction] = useState("");

  const loadEntries = useCallback(async () => {
    setLoading(true);
    setError(null);
    const params: AuditQueryParams = { limit: pageSize, offset };
    if (filterEntityType) params.entity_type = filterEntityType;
    if (filterActorId) params.actor_id = filterActorId;
    if (filterAction) params.action = filterAction;

    try {
      const result = await audit.query(params);
      setEntries(result.entries);
      setTotal(result.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lỗi tải audit logs");
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, [audit, pageSize, offset, filterEntityType, filterActorId, filterAction]);

  useEffect(() => { loadEntries(); }, [loadEntries]);

  return (
    <div className="audit-log-list">
      <div className="audit-log-list__header">
        <h2>Audit Logs</h2>
        <span>Total: {total}</span>
      </div>
      <div className="audit-log-list__filters">
        <input placeholder="Entity type..." value={filterEntityType}
               onChange={(e) => { setFilterEntityType(e.target.value); setOffset(0); }} />
        <input placeholder="Actor ID..." value={filterActorId}
               onChange={(e) => { setFilterActorId(e.target.value); setOffset(0); }} />
        <select value={filterAction}
                onChange={(e) => { setFilterAction(e.target.value); setOffset(0); }}>
          <option value="">All actions</option>
          {["CREATE","UPDATE","DELETE","READ","LOGIN","LOGOUT","EXPORT","APPROVE","REJECT","CUSTOM"].map((a) => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
      </div>
      {loading && <div>Loading...</div>}
      {error && <div className="audit-log-list__error">{error}</div>}
      {!loading && !error && (
        <div className="audit-log-list__entries">
          {entries.map((entry) => (
            <div key={entry.id} className="audit-log-list__entry">
              <span className="audit-log-list__action">{entry.action}</span>
              <span>{entry.entity_type}:{entry.entity_id}</span>
              <span>{new Date(entry.timestamp).toLocaleString()}</span>
              <span>{entry.actor_type}: {entry.actor_id}</span>
            </div>
          ))}
          {entries.length === 0 && <div>No audit logs.</div>}
        </div>
      )}
      {!loading && total > pageSize && (
        <div className="audit-log-list__pagination">
          <button onClick={() => setOffset((o) => Math.max(0, o - pageSize))}
                  disabled={offset === 0}>← Prev</button>
          <span>{offset + 1}-{Math.min(offset + pageSize, total)} / {total}</span>
          <button onClick={() => setOffset((o) => o + pageSize)}
                  disabled={offset + entries.length >= total}>Next →</button>
        </div>
      )}
    </div>
  );
}

export default AuditLogList;
'''
        return {"src/audit/AuditLogList.tsx": code}
