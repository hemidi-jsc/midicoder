# coding: utf-8
"""
Mô-đun Angular emitter cho Versioning & History Generator (CP43).

Emit code Angular cho:
- VersionHistoryComponent: hiển thị danh sách versions của entity
- RestoreVersionDialog: dialog để restore entity về version cũ
- SoftDeleteIndicator: hiển thị trạng thái đã xóa/mã khôi phục

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any, Dict

from midicoder.packs.cp43_versioning.models import VersioningCollection


class AngularVersioningEmitter:
    """
    Emitter sinh code Angular cho versioning & history.

    Methods:
        generate(): Generate toàn bộ files
        generate_service(): Sinh VersionHistoryService
        generate_component(): Sinh VersionHistoryComponent
        generate_restore_dialog(): Sinh RestoreVersionDialog
        generate_indicator(): Sinh SoftDeleteIndicator
    """

    def __init__(self, collection: VersioningCollection | None = None) -> None:
        """
        Khởi tạo AngularVersioningEmitter.

        Args:
            collection: VersioningCollection (optional)
        """
        self.collection = collection or VersioningCollection()

    def generate(self) -> Dict[str, str]:
        """
        Generate toàn bộ files Angular.

        Returns:
            Dict {file_path: source_code}
        """
        result: Dict[str, str] = {}
        result.update(self.generate_service())
        result.update(self.generate_component())
        result.update(self.generate_restore_dialog())
        result.update(self.generate_indicator())
        return result

    def generate_service(self) -> Dict[str, str]:
        """Sinh VersionHistoryService — Angular service cho version history."""
        code = '''/**
 * Version History Service - CP43.
 *
 * Angular service để query version history, time-travel query,
 * và restore entity về version cũ.
 */

import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable } from "rxjs";

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

@Injectable({
  providedIn: "root",
})
export class VersionHistoryService {
  constructor(
    private http: HttpClient,
    private apiBase: string = "/api/v1",
  ) {}

  /**
   * Lấy danh sách versions của entity.
   *
   * @param entityType - Tên entity
   * @param entityId - ID entity
   * @param limit - Số lượng max
   */
  getVersionHistory(
    entityType: string,
    entityId: string,
    limit: number = 100,
  ): Observable<VersionHistoryEntry[]> {
    return this.http.get<VersionHistoryEntry[]>(
      `${this.apiBase}/version-history/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}`,
      { params: { limit: limit.toString() } },
    );
  }

  /**
   * Lấy snapshot của entity ở version cụ thể.
   *
   * @param entityType - Tên entity
   * @param entityId - ID entity
   * @param version - Số version
   */
  getAtVersion(
    entityType: string,
    entityId: string,
    version: number,
  ): Observable<Record<string, any>> {
    return this.http.get<Record<string, any>>(
      `${this.apiBase}/version-history/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}/version/${version}`,
    );
  }

  /**
   * Lấy snapshot gần nhất trước thời điểm T.
   *
   * @param entityType - Tên entity
   * @param entityId - ID entity
   * @param timestamp - Thời điểm (ISO string)
   */
  getAtTimestamp(
    entityType: string,
    entityId: string,
    timestamp: string,
  ): Observable<Record<string, any>> {
    return this.http.get<Record<string, any>>(
      `${this.apiBase}/version-history/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}/timestamp`,
      { params: { timestamp } },
    );
  }

  /**
   * So sánh 2 versions.
   *
   * @param entityType - Tên entity
   * @param entityId - ID entity
   * @param fromVersion - Version cũ
   * @param toVersion - Version mới
   */
  getChangesBetween(
    entityType: string,
    entityId: string,
    fromVersion: number,
    toVersion: number,
  ): Observable<ChangesBetween> {
    return this.http.get<ChangesBetween>(
      `${this.apiBase}/version-history/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}/compare`,
      { params: { from: fromVersion.toString(), to: toVersion.toString() } },
    );
  }

  /**
   * Restore entity về version cũ.
   *
   * @param entityType - Tên entity
   * @param entityId - ID entity
   * @param version - Version cần restore
   */
  restoreToVersion(
    entityType: string,
    entityId: string,
    version: number,
  ): Observable<any> {
    return this.http.post(
      `${this.apiBase}/version-history/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}/restore`,
      { version },
    );
  }
}
'''
        return {"src/app/core/versioning/version-history.service.ts": code}

    def generate_component(self) -> Dict[str, str]:
        """Sinh VersionHistoryComponent — hiển thị danh sách versions."""
        code = '''/**
 * Version History Component - CP43.
 *
 * Angular component hiển thị danh sách versions của entity,
 * cho phép xem chi tiết mỗi version và restore về version cũ.
 */

import { Component, OnInit, Input, Output, EventEmitter } from "@angular/core";
import { VersionHistoryService, VersionHistoryEntry } from "./version-history.service";

@Component({
  selector: "app-version-history",
  template: `
    <div class="version-history">
      <div class="version-history__header">
        <h3>Lịch sử Version</h3>
        <span class="version-history__count">{{ entries.length }} versions</span>
      </div>

      <div *ngIf="loading" class="version-history__loading">Đang tải...</div>
      <div *ngIf="error" class="version-history__error">{{ error }}</div>

      <div *ngIf="!loading && !error" class="version-history__list">
        <div
          *ngFor="let entry of entries; let i = index"
          class="version-history__entry"
          [class.version-history__entry--selected]="entry.version === selectedVersion"
          (click)="selectVersion(entry)"
        >
          <div class="version-history__entry-header">
            <span class="version-history__badge">{{ entry.version }}</span>
            <span class="version-history__operation">{{ entry.operation }}</span>
            <span class="version-history__date">{{ entry.created_at | date:'medium' }}</span>
            <span class="version-history__actor">{{ entry.created_by }}</span>
          </div>
          <div *ngIf="entry.changed_fields?.length" class="version-history__changed">
            Thay đổi: {{ entry.changed_fields.join(", ") }}
          </div>
        </div>
      </div>

      <div *ngIf="selectedEntry" class="version-history__detail">
        <h4>Chi tiết Version {{ selectedEntry.version }}</h4>
        <pre class="version-history__snapshot">{{ selectedEntry.snapshot | json }}</pre>
        <button class="version-history__restore-btn" (click)="restoreVersion(selectedEntry.version)">
          Restore về version {{ selectedEntry.version }}
        </button>
      </div>
    </div>
  `,
})
export class VersionHistoryComponent implements OnInit {
  @Input() entityType: string = "";
  @Input() entityId: string = "";
  @Output() restored = new EventEmitter<number>();

  entries: VersionHistoryEntry[] = [];
  selectedEntry: VersionHistoryEntry | null = null;
  selectedVersion: number | null = null;
  loading: boolean = false;
  error: string = "";

  constructor(private versionService: VersionHistoryService) {}

  ngOnInit(): void {
    this.loadHistory();
  }

  loadHistory(): void {
    this.loading = true;
    this.error = "";

    this.versionService.getVersionHistory(this.entityType, this.entityId).subscribe({
      next: (data) => {
        this.entries = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = `Lỗi tải version history: ${err.message}`;
        this.loading = false;
      },
    });
  }

  selectVersion(entry: VersionHistoryEntry): void {
    this.selectedEntry = entry;
    this.selectedVersion = entry.version;
  }

  restoreVersion(version: number): void {
    if (confirm(`Bạn có chắc muốn restore về version ${version}?`)) {
      this.versionService.restoreToVersion(this.entityType, this.entityId, version).subscribe({
        next: () => {
          this.restored.emit(version);
          this.loadHistory();
        },
        error: (err) => {
          alert(`Restore thất bại: ${err.message}`);
        },
      });
    }
  }
}
'''
        return {"src/app/shared/components/version-history/version-history.component.ts": code}

    def generate_restore_dialog(self) -> Dict[str, str]:
        """Sinh RestoreVersionDialog — dialog confirm restore."""
        code = '''/**
 * Restore Version Dialog - CP43.
 *
 * Dialog để confirm restore entity về version cũ.
 * Hiển thị thông tin version và các trường sẽ thay đổi.
 */

import { Component, Inject } from "@angular/core";
import { MatDialogRef, MAT_DIALOG_DATA } from "@angular/material/dialog";

export interface RestoreDialogData {
  entityType: string;
  entityId: string;
  currentVersion: number;
  targetVersion: number;
  changedFields: string[];
}

@Component({
  selector: "app-restore-version-dialog",
  template: `
    <h2 mat-dialog-title>Restore Version</h2>
    <mat-dialog-content>
      <p>Bạn đang restore <strong>{{ data.entityType }}</strong> về version <strong>{{ data.targetVersion }}</strong>.</p>
      <p>Current version: <strong>{{ data.currentVersion }}</strong></p>
      <div *ngIf="data.changedFields?.length">
        <p>Các trường sẽ thay đổi:</p>
        <ul>
          <li *ngFor="let field of data.changedFields">{{ field }}</li>
        </ul>
      </div>
      <p class="warning">Lưu ý: Hành động này không thể hoàn tác.</p>
    </mat-dialog-content>
    <mat-dialog-actions>
      <button mat-button (click)="onCancel()">Hủy</button>
      <button mat-raised-button color="warn" (click)="onConfirm()">Restore</button>
    </mat-dialog-actions>
  `,
})
export class RestoreVersionDialogComponent {
  constructor(
    public dialogRef: MatDialogRef<RestoreVersionDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: RestoreDialogData,
  ) {}

  onConfirm(): void {
    this.dialogRef.close(true);
  }

  onCancel(): void {
    this.dialogRef.close(false);
  }
}
'''
        return {"src/app/shared/components/version-history/restore-version-dialog.component.ts": code}

    def generate_indicator(self) -> Dict[str, str]:
        """Sinh SoftDeleteIndicator — hiển thị trạng thái đã xóa."""
        code = '''/**
 * Soft Delete Indicator - CP43.
 *
 * Hiển thị trạng thái soft delete của entity và button restore.
 */

import { Component, Input, Output, EventEmitter } from "@angular/core";

@Component({
  selector: "app-soft-delete-indicator",
  template: `
    <div *ngIf="isDeleted" class="soft-delete-indicator">
      <span class="soft-delete-indicator__badge">Đã xóa</span>
      <span class="soft-delete-indicator__info">
        Xóa bởi {{ deletedBy }} lúc {{ deletedAt | date:'medium' }}
      </span>
      <button class="soft-delete-indicator__restore-btn" (click)="onRestore()">
        Khôi phục
      </button>
    </div>
    <div *ngIf="!isDeleted" class="soft-delete-indicator--active">
      <span class="soft-delete-indicator__badge--active">Hoạt động</span>
    </div>
  `,
})
export class SoftDeleteIndicatorComponent {
  @Input() isDeleted: boolean = false;
  @Input() deletedAt: string | null = null;
  @Input() deletedBy: string = "";
  @Output() restore = new EventEmitter<void>();

  onRestore(): void {
    this.restore.emit();
  }
}
'''
        return {"src/app/shared/components/soft-delete-indicator/soft-delete-indicator.component.ts": code}
