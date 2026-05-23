# coding: utf-8
"""
Mô-đun React emitter cho Versioning & History Generator (CP43).

Emit code React cho:
- VersionHistory: component hiển thị danh sách versions của entity
- RestoreVersionModal: modal để restore entity về version cũ
- SoftDeleteIndicator: hiển thị trạng thái đã xóa/mã khôi phục

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any, Dict

from midicoder.emitters.core.cp43_versioning.models import VersioningCollection


class ReactVersioningEmitter:
    """
    Emitter sinh code React cho versioning & history.

    Methods:
        generate(): Generate toàn bộ files
        generate_types(): Sinh TypeScript interfaces
        generate_hook(): Sinh useVersionHistory hook
        generate_component(): Sinh VersionHistory component
        generate_restore_modal(): Sinh RestoreVersionModal
        generate_indicator(): Sinh SoftDeleteIndicator
    """

    def __init__(self, collection: VersioningCollection | None = None) -> None:
        """
        Khởi tạo ReactVersioningEmitter.

        Args:
            collection: VersioningCollection (optional)
        """
        self.collection = collection or VersioningCollection()

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
        result.update(self.generate_restore_modal())
        result.update(self.generate_indicator())
        return result

    def generate_types(self) -> Dict[str, str]:
        """Sinh TypeScript interfaces cho versioning."""
        code = '''/**
 * Versioning Types - CP43.
 *
 * TypeScript interfaces cho versioning & history layer.
 */

/** Một entry trong version history */
export interface VersionHistoryEntry {
  version: number;
  operation: string;
  snapshot: Record<string, any>;
  changed_fields: string[];
  created_at: string;
  created_by: string;
}

/** Kết quả so sánh 2 versions */
export interface ChangesBetween {
  old: Record<string, any>;
  new: Record<string, any>;
  changes: Array<{ field: string; old_value: any; new_value: any }>;
}

/** Props cho VersionHistory component */
export interface VersionHistoryProps {
  entityType: string;
  entityId: string;
  apiBase?: string;
  onRestore?: (version: number) => void;
}

/** Props cho RestoreVersionModal */
export interface RestoreVersionModalProps {
  open: boolean;
  entityType: string;
  entityId: string;
  currentVersion: number;
  targetVersion: number;
  changedFields?: string[];
  onClose: () => void;
  onConfirm: () => void;
}

/** Props cho SoftDeleteIndicator */
export interface SoftDeleteIndicatorProps {
  isDeleted: boolean;
  deletedAt?: string | null;
  deletedBy?: string;
  onRestore?: () => void;
}

/** Return type của useVersionHistory hook */
export interface UseVersionHistoryReturn {
  entries: VersionHistoryEntry[];
  loading: boolean;
  error: string | null;
  loadHistory: (limit?: number) => Promise<void>;
  getAtVersion: (version: number) => Promise<Record<string, any> | null>;
  restoreToVersion: (version: number) => Promise<void>;
}
'''
        return {"src/versioning/types.ts": code}

    def generate_hook(self) -> Dict[str, str]:
        """Sinh useVersionHistory hook."""
        code = '''/**
 * useVersionHistory Hook - CP43.
 *
 * Custom hook để query version history, time-travel query,
 * và restore entity về version cũ.
 */

import { useCallback, useState, useMemo } from "react";
import {
  VersionHistoryEntry,
  UseVersionHistoryReturn,
} from "./types";

/**
 * Hook để truy cập version history operations.
 *
 * @param entityType - Tên entity
 * @param entityId - ID entity
 * @param apiBase - API base URL (mặc định "/api/v1")
 */
export function useVersionHistory(
  entityType: string,
  entityId: string,
  apiBase: string = "/api/v1",
): UseVersionHistoryReturn {
  const [entries, setEntries] = useState<VersionHistoryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /** Lấy danh sách versions của entity */
  const loadHistory = useCallback(
    async (limit: number = 100) => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(
          `${apiBase}/version-history/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}?limit=${limit}`,
        );
        if (!response.ok) throw new Error(`Lỗi tải version history: ${response.status}`);
        const data = await response.json();
        setEntries(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Lỗi tải version history");
        setEntries([]);
      } finally {
        setLoading(false);
      }
    },
    [apiBase, entityType, entityId],
  );

  /** Lấy snapshot của entity ở version cụ thể */
  const getAtVersion = useCallback(
    async (version: number): Promise<Record<string, any> | null> => {
      const response = await fetch(
        `${apiBase}/version-history/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}/version/${version}`,
      );
      if (!response.ok) return null;
      return response.json();
    },
    [apiBase, entityType, entityId],
  );

  /** Restore entity về version cũ */
  const restoreToVersion = useCallback(
    async (version: number) => {
      const response = await fetch(
        `${apiBase}/version-history/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}/restore`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ version }),
        },
      );
      if (!response.ok) throw new Error(`Restore thất bại: ${response.status}`);
      await loadHistory();
    },
    [apiBase, entityType, entityId, loadHistory],
  );

  return useMemo(
    () => ({ entries, loading, error, loadHistory, getAtVersion, restoreToVersion }),
    [entries, loading, error, loadHistory, getAtVersion, restoreToVersion],
  );
}
'''
        return {"src/versioning/useVersionHistory.ts": code}

    def generate_component(self) -> Dict[str, str]:
        """Sinh VersionHistory component."""
        code = '''/**
 * Version History Component - CP43.
 *
 * React component hiển thị danh sách versions của entity,
 * cho phép xem chi tiết mỗi version và restore về version cũ.
 */

import { useEffect, useState } from "react";
import { useVersionHistory } from "./useVersionHistory";
import { VersionHistoryEntry, VersionHistoryProps } from "./types";

export function VersionHistory({
  entityType,
  entityId,
  apiBase,
  onRestore,
}: VersionHistoryProps) {
  const { entries, loading, error, loadHistory, restoreToVersion } =
    useVersionHistory(entityType, entityId, apiBase);
  const [selectedEntry, setSelectedEntry] = useState<VersionHistoryEntry | null>(null);
  const [confirmRestore, setConfirmRestore] = useState<number | null>(null);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  return (
    <div className="version-history">
      <div className="version-history__header">
        <h3>Lịch sử Version</h3>
        <span className="version-history__count">{entries.length} versions</span>
      </div>

      {loading && <div className="version-history__loading">Đang tải...</div>}
      {error && <div className="version-history__error">{error}</div>}

      {!loading && !error && (
        <div className="version-history__list">
          {entries.map((entry) => (
            <div
              key={entry.version}
              className={
                "version-history__entry" +
                (selectedEntry?.version === entry.version ? " version-history__entry--selected" : "")
              }
              onClick={() => setSelectedEntry(entry)}
            >
              <div className="version-history__entry-header">
                <span className="version-history__badge">v{entry.version}</span>
                <span className="version-history__operation">{entry.operation}</span>
                <span className="version-history__date">
                  {new Date(entry.created_at).toLocaleString("vi-VN")}
                </span>
                <span className="version-history__actor">{entry.created_by}</span>
              </div>
              {entry.changed_fields?.length > 0 && (
                <div className="version-history__changed">
                  Thay đổi: {entry.changed_fields.join(", ")}
                </div>
              )}
            </div>
          ))}
          {entries.length === 0 && (
            <div className="version-history__empty">Không có version history.</div>
          )}
        </div>
      )}

      {selectedEntry && (
        <div className="version-history__detail">
          <h4>Chi tiết Version {selectedEntry.version}</h4>
          <pre className="version-history__snapshot">
            {JSON.stringify(selectedEntry.snapshot, null, 2)}
          </pre>
          <button
            className="version-history__restore-btn"
            onClick={() => setConfirmRestore(selectedEntry.version)}
          >
            Restore về version {selectedEntry.version}
          </button>
        </div>
      )}

      {confirmRestore !== null && (
        <div className="version-history__confirm-overlay">
          <div className="version-history__confirm-dialog">
            <p>Bạn có chắc muốn restore về version {confirmRestore}?</p>
            <p className="version-history__confirm-warning">
              Hành động này không thể hoàn tác.
            </p>
            <div className="version-history__confirm-actions">
              <button onClick={() => setConfirmRestore(null)}>Hủy</button>
              <button
                className="version-history__confirm-btn"
                onClick={async () => {
                  await restoreToVersion(confirmRestore);
                  setConfirmRestore(null);
                  onRestore?.(confirmRestore);
                }}
              >
                Restore
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default VersionHistory;
'''
        return {"src/versioning/VersionHistory.tsx": code}

    def generate_restore_modal(self) -> Dict[str, str]:
        """Sinh RestoreVersionModal."""
        code = '''/**
 * Restore Version Modal - CP43.
 *
 * Modal để confirm restore entity về version cũ.
 * Hiển thị thông tin version và các trường sẽ thay đổi.
 */

import { RestoreVersionModalProps } from "./types";

export function RestoreVersionModal({
  open,
  entityType,
  entityId,
  currentVersion,
  targetVersion,
  changedFields,
  onClose,
  onConfirm,
}: RestoreVersionModalProps) {
  if (!open) return null;

  return (
    <div className="restore-modal__overlay" onClick={onClose}>
      <div className="restore-modal__dialog" onClick={(e) => e.stopPropagation()}>
        <h2 className="restore-modal__title">Restore Version</h2>
        <div className="restore-modal__content">
          <p>
            Bạn đang restore <strong>{entityType}</strong> về version{" "}
            <strong>{targetVersion}</strong>.
          </p>
          <p>
            Current version: <strong>{currentVersion}</strong>
          </p>
          {changedFields && changedFields.length > 0 && (
            <div className="restore-modal__fields">
              <p>Các trường sẽ thay đổi:</p>
              <ul>
                {changedFields.map((field) => (
                  <li key={field}>{field}</li>
                ))}
              </ul>
            </div>
          )}
          <p className="restore-modal__warning">
            Lưu ý: Hành động này không thể hoàn tác.
          </p>
        </div>
        <div className="restore-modal__actions">
          <button className="restore-modal__btn-cancel" onClick={onClose}>
            Hủy
          </button>
          <button className="restore-modal__btn-confirm" onClick={onConfirm}>
            Restore
          </button>
        </div>
      </div>
    </div>
  );
}

export default RestoreVersionModal;
'''
        return {"src/versioning/RestoreVersionModal.tsx": code}

    def generate_indicator(self) -> Dict[str, str]:
        """Sinh SoftDeleteIndicator."""
        code = '''/**
 * Soft Delete Indicator - CP43.
 *
 * Hiển thị trạng thái soft delete của entity và button restore.
 */

import { SoftDeleteIndicatorProps } from "./types";

export function SoftDeleteIndicator({
  isDeleted,
  deletedAt,
  deletedBy,
  onRestore,
}: SoftDeleteIndicatorProps) {
  if (isDeleted) {
    return (
      <div className="soft-delete-indicator">
        <span className="soft-delete-indicator__badge">Đã xóa</span>
        <span className="soft-delete-indicator__info">
          Xóa bởi {deletedBy || "system"}{" "}
          {deletedAt && `lúc ${new Date(deletedAt).toLocaleString("vi-VN")}`}
        </span>
        {onRestore && (
          <button
            className="soft-delete-indicator__restore-btn"
            onClick={onRestore}
          >
            Khôi phục
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="soft-delete-indicator--active">
      <span className="soft-delete-indicator__badge--active">Hoạt động</span>
    </div>
  );
}

export default SoftDeleteIndicator;
'''
        return {"src/versioning/SoftDeleteIndicator.tsx": code}
