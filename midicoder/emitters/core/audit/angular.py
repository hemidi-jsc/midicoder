# coding: utf-8
"""
CP14: Angular Audit Trail Emitter.

Module này cung cấp AngularAuditComplianceEmitter để generate Angular audit code
từ AuditComplianceCollection (CP14):
- audit_logger_service.ts - Angular service với log/query operations
- audit_log_list.component.ts - Component hiển thị audit logs với filter + pagination

KPI-029: Tenant-aware audit logging qua header x-tenant-id.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any, Dict

from midicoder.emitters.core.audit.models import AuditComplianceCollection


class AngularAuditComplianceEmitter:
    """
    Emitter sinh code Angular cho audit trail & compliance.

    Methods:
        generate(): Generate toàn bộ files
        generate_service(): Sinh AuditLoggerService
        generate_component(): Sinh AuditLogListComponent
    """

    def __init__(self, collection: AuditComplianceCollection | None = None) -> None:
        """
        Khởi tạo AngularAuditComplianceEmitter.

        Args:
            collection: AuditComplianceCollection (optional)
        """
        self.collection = collection or AuditComplianceCollection()

    def generate(self) -> Dict[str, str]:
        """
        Generate toàn bộ files Angular.

        Returns:
            Dict {file_path: source_code}
        """
        result: Dict[str, str] = {}
        result.update(self.generate_service())
        result.update(self.generate_component())
        return result

    def generate_service(self) -> Dict[str, str]:
        """Sinh AuditLoggerService — Angular service cho audit operations."""
        code = '''/**
 * Audit Logger Service - CP14.
 *
 * Angular service cho audit trail logging và query.
 * Cung cấp phương thức ghi audit log và query audit history.
 *
 * Sử dụng HttpClient để giao tiếp với backend audit API.
 * Auto-generate immutable hash (SHA-256) cho tamper-evidence (RX11).
 */

import { Injectable } from "@angular/core";
import { HttpClient, HttpHeaders } from "@angular/common/http";
import { Observable, BehaviorSubject } from "rxjs";

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

/** Payload để ghi audit log */
export interface AuditLogPayload {
  action: string;
  entity_type: string;
  entity_id: string;
  actor_id: string;
  actor_type?: "user" | "system" | "background_job";
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

@Injectable({
  providedIn: "root",
})
export class AuditLoggerService {
  /** BehaviorSubject để theo dõi tenant ID hiện tại */
  private tenantId$ = new BehaviorSubject<string | undefined>(undefined);

  /**
   * Khởi tạo AuditLoggerService.
   *
   * @param http HttpClient instance
   * @param apiBase URL cơ bản của API
   */
  constructor(
    private http: HttpClient,
    private apiBase: string = "/api/v1",
  ) {}

  /**
   * Đặt tenant ID cho tenant isolation.
   *
   * @param tenantId Tenant ID
   */
  setTenantId(tenantId: string | undefined): void {
    this.tenantId$.next(tenantId);
  }

  /**
   * Lấy tenant ID hiện tại.
   */
  getTenantId(): string | undefined {
    return this.tenantId$.value;
  }

  /**
   * Xây dựng HTTP headers với tenant ID.
   */
  private _buildHeaders(): HttpHeaders {
    const headers: Record<string, string> = {};
    const tenantId = this.tenantId$.value;
    if (tenantId) {
      headers["x-tenant-id"] = tenantId;
    }
    return new HttpHeaders(headers);
  }

  /**
   * Ghi audit log entry.
   *
   * Gửi payload đến backend để ghi audit log.
   * Backend sẽ auto-generate immutable hash cho tamper-evidence.
   *
   * @param payload Payload chứa thông tin audit log
   * @returns Observable của entry ID
   */
  log(payload: AuditLogPayload): Observable<string> {
    return this.http.post<string>(
      `${this.apiBase}/audit/log`,
      payload,
      {
        headers: this._buildHeaders(),
        responseType: "text" as "json",
      },
    );
  }

  /**
   * Query audit logs với filters.
   *
   * @param params Query params (entity_type, actor_id, tenant_id, action, limit, offset)
   * @returns Observable của audit query result
   */
  query(params: AuditQueryParams = {}): Observable<AuditQueryResult> {
    const queryParams: Record<string, string> = {};
    if (params.entity_type) queryParams.entity_type = params.entity_type;
    if (params.actor_id) queryParams.actor_id = params.actor_id;
    if (params.tenant_id) queryParams.tenant_id = params.tenant_id;
    if (params.action) queryParams.action = params.action;
    if (params.limit) queryParams.limit = params.limit.toString();
    if (params.offset) queryParams.offset = params.offset.toString();

    return this.http.get<AuditQueryResult>(
      `${this.apiBase}/audit/query`,
      {
        headers: this._buildHeaders(),
        params: queryParams,
      },
    );
  }

  /**
   * Lấy audit logs cho một entity cụ thể.
   *
   * @param entityType Entity type
   * @param entityId Entity ID
   * @param limit Số lượng max (mặc định 100)
   * @returns Observable của audit log entries
   */
  getEntityAuditTrail(
    entityType: string,
    entityId: string,
    limit: number = 100,
  ): Observable<AuditLogEntry[]> {
    return this.http.get<AuditLogEntry[]>(
      `${this.apiBase}/audit/entity/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}`,
      {
        headers: this._buildHeaders(),
        params: { limit: limit.toString() },
      },
    );
  }
}
'''
        return {"src/app/core/audit/audit_logger_service.ts": code}

    def generate_component(self) -> Dict[str, str]:
        """Sinh AuditLogListComponent — Component hiển thị audit logs."""
        code = '''/**
 * Audit Log List Component - CP14.
 *
 * Angular component hiển thị danh sách audit logs với filter và pagination.
 * Cho phép lọc theo entity_type, actor_id, action.
 * Hiển thị thông tin chi tiết của mỗi audit entry.
 */

import { Component, OnInit, Input } from "@angular/core";
import {
  AuditLoggerService,
  AuditLogEntry,
  AuditQueryParams,
} from "./audit_logger_service";

@Component({
  selector: "app-audit-log-list",
  template: `
    <div class="audit-log-list">
      <div class="audit-log-list__header">
        <h2>Audit Logs</h2>
        <span class="audit-log-list__count">Tổng: {{ total }} entries</span>
      </div>

      <!-- Filters -->
      <div class="audit-log-list__filters">
        <input type="text" placeholder="Filter theo entity type..."
               [value]="filterEntityType" (input)="onFilterEntityType($event)" />
        <input type="text" placeholder="Filter theo actor ID..."
               [value]="filterActorId" (input)="onFilterActorId($event)" />
        <select [value]="filterAction" (change)="onFilterAction($event)">
          <option value="">Tất cả actions</option>
          <option *ngFor="let action of actionOptions" [value]="action">{{ action }}</option>
        </select>
      </div>

      <!-- Loading / Error -->
      <div *ngIf="loading" class="audit-log-list__loading">Đang tải...</div>
      <div *ngIf="error" class="audit-log-list__error">{{ error }}</div>

      <!-- Entries -->
      <div *ngIf="!loading && !error" class="audit-log-list__entries">
        <div *ngFor="let entry of entries" class="audit-log-list__entry">
          <div class="audit-log-list__entry-header">
            <span class="audit-log-list__entry-action">{{ entry.action }}</span>
            <span>{{ entry.entity_type }}:{{ entry.entity_id }}</span>
            <span>{{ entry.timestamp | date:'medium' }}</span>
            <span>{{ entry.actor_type }}: {{ entry.actor_id }}</span>
          </div>
        </div>
        <div *ngIf="entries.length === 0" class="audit-log-list__empty">
          Không có audit logs.
        </div>
      </div>

      <!-- Pagination -->
      <div *ngIf="total > limit" class="audit-log-list__pagination">
        <button (click)="loadPreviousPage()" [disabled]="offset === 0">← Trước</button>
        <span>{{ offset + 1 }}-{{ offset + entries.length }} / {{ total }}</span>
        <button (click)="loadNextPage()" [disabled]="offset + entries.length >= total">Sau →</button>
      </div>
    </div>
  `,
})
export class AuditLogListComponent implements OnInit {
  @Input() defaultEntityType: string = "";
  @Input() limit: number = 50;

  entries: AuditLogEntry[] = [];
  total: number = 0;
  offset: number = 0;
  loading: boolean = false;
  error: string = "";
  filterEntityType: string = "";
  filterActorId: string = "";
  filterAction: string = "";

  actionOptions = ["CREATE", "UPDATE", "DELETE", "READ", "LOGIN", "LOGOUT",
                   "EXPORT", "APPROVE", "REJECT", "CUSTOM"];

  constructor(private auditLogger: AuditLoggerService) {}

  ngOnInit(): void {
    this.filterEntityType = this.defaultEntityType;
    this.loadEntries();
  }

  loadEntries(): void {
    this.loading = true;
    this.error = "";
    const params: AuditQueryParams = { limit: this.limit, offset: this.offset };
    if (this.filterEntityType) params.entity_type = this.filterEntityType;
    if (this.filterActorId) params.actor_id = this.filterActorId;
    if (this.filterAction) params.action = this.filterAction;

    this.auditLogger.query(params).subscribe({
      next: (result) => {
        this.entries = result.entries;
        this.total = result.total;
        this.loading = false;
      },
      error: (err) => {
        this.error = `Lỗi tải audit logs: ${err.message}`;
        this.loading = false;
      },
    });
  }

  onFilterEntityType(event: Event): void {
    this.filterEntityType = (event.target as HTMLInputElement).value;
    this.offset = 0;
    this.loadEntries();
  }

  onFilterActorId(event: Event): void {
    this.filterActorId = (event.target as HTMLInputElement).value;
    this.offset = 0;
    this.loadEntries();
  }

  onFilterAction(event: Event): void {
    this.filterAction = (event.target as HTMLSelectElement).value;
    this.offset = 0;
    this.loadEntries();
  }

  loadPreviousPage(): void {
    if (this.offset > 0) {
      this.offset -= this.limit;
      this.loadEntries();
    }
  }

  loadNextPage(): void {
    if (this.offset + this.entries.length < this.total) {
      this.offset += this.limit;
      this.loadEntries();
    }
  }
}
'''
        return {"src/app/core/audit/audit_log_list.component.ts": code}
