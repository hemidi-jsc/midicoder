/**
 * Version Info Card — hiển thị đầy đủ metadata của version đang active.
 * Dữ liệu lấy từ VersionService.
 */

import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { formatDateLocal } from '../../../core/date.util';

const APP_VERSION = '1.0.0';
const DOCS_URL = `https://docs.midicoder.com/ce/${APP_VERSION}/version-management`;

export interface VersionMetadata {
  version: string;
  status: 'draft' | 'inbuild' | 'archived';
  active: boolean;
  parent_version: string | null;
  created_at: string;
  updated_at: string;
  branch?: string;
  pipeline?: { brief: string; contract: string; ir: string; code: string };
}

@Component({
  selector: 'app-version-info-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="info-card">
      <div class="card-header">
        <h3 class="card-title">🔖 Version</h3>
        <a [href]="docsUrl" target="_blank" rel="noopener noreferrer" class="help-icon" title="Hướng dẫn quản lý version">❓</a>
      </div>

      @if (!version) {
        <p class="empty-state">Chưa có version active</p>
      } @else {
        <div class="field-list">
          <div class="field-row">
            <span class="field-label">version</span>
            <span class="field-value monospace">{{ version!.version }}</span>
          </div>
          <div class="field-row">
            <span class="field-label">status</span>
            <span class="field-value">
              <span [class]="'badge badge-' + version!.status">{{ getStatusLabel(version!.status) }}</span>
            </span>
          </div>
          <div class="field-row">
            <span class="field-label">active</span>
            <span class="field-value">
              @if (version!.active) {
                <span class="status-dot" title="Đang selected"></span>
              } @else {
                <span class="status-dot status-dot-inactive" title="Không active"></span>
              }
            </span>
          </div>
          <div class="field-row">
            <span class="field-label">parent_version</span>
            <span class="field-value monospace">{{ version!.parent_version || 'null' }}</span>
          </div>
          <div class="field-row">
            <span class="field-label">created_at</span>
            <span class="field-value monospace">{{ formatDate(version!.created_at) }}</span>
          </div>
          <div class="field-row">
            <span class="field-label">updated_at</span>
            <span class="field-value monospace">{{ formatDate(version!.updated_at) }}</span>
          </div>

          @if (version!.branch) {
            <div class="field-row">
              <span class="field-label">branch</span>
              <span class="field-value"><span class="branch-tag">🔀 {{ version!.branch }}</span></span>
            </div>
          }
        </div>

        <div class="card-actions">
          <button class="btn-create-version" (click)="createVersion.emit()" [disabled]="isArchived()">
            ＋ Tạo phiên bản mới
          </button>
        </div>
      }
    </div>
  `,
  styles: [`
    :host {
      flex: 1;
      min-width: 0;
    }

    .info-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      padding: 20px;
      height: 100%;
      display: flex;
      flex-direction: column;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }

    .card-title {
      font-size: 1rem;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }

    .help-icon {
      color: var(--text-tertiary);
      font-size: 1rem;
      text-decoration: none;
      transition: color 0.2s;
      cursor: pointer;
    }

    .help-icon:hover {
      color: var(--brand-color);
    }

    .empty-state {
      color: var(--text-tertiary);
      font-size: 0.85rem;
      text-align: center;
      padding: 24px 0;
    }

    .field-list {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .field-row {
      display: flex;
      align-items: baseline;
      gap: 8px;
      font-size: 0.8rem;
    }

    .field-label {
      color: var(--text-tertiary);
      font-weight: 500;
      min-width: 110px;
      font-family: 'JetBrains Mono', monospace;
    }

    .field-value {
      color: var(--text-primary);
      word-break: break-all;
    }

    .field-value.monospace {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
    }

    .badge {
      display: inline-block;
      padding: 2px 8px;
      font-size: 0.7rem;
      font-weight: 600;
      border-radius: 3px;
    }

    .badge-draft {
      background: rgba(255, 203, 96, 0.15);
      color: #ffcb60;
      border: 1px solid rgba(255, 203, 96, 0.3);
    }

    .badge-inbuild {
      background: rgba(63, 185, 80, 0.15);
      color: var(--accent-success);
      border: 1px solid rgba(63, 185, 80, 0.3);
    }

    .badge-archived {
      background: rgba(255, 82, 82, 0.15);
      color: var(--accent-error);
      border: 1px solid rgba(255, 82, 82, 0.3);
    }

    .badge-active {
      background: rgba(63, 185, 80, 0.15);
      color: var(--accent-success);
      border: 1px solid rgba(63, 185, 80, 0.3);
    }

    .badge-inactive {
      background: rgba(136, 148, 150, 0.15);
      color: var(--text-tertiary);
      border: 1px solid rgba(136, 148, 150, 0.3);
    }

    .status-dot {
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent-success);
      box-shadow: 0 0 6px rgba(63, 185, 80, 0.6);
    }

    .status-dot-inactive {
      background: var(--text-tertiary);
      box-shadow: none;
    }

    .branch-tag {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      background: rgba(100, 181, 246, 0.12);
      border: 1px solid rgba(100, 181, 246, 0.25);
      border-radius: 4px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
      color: #64b5f6;
    }

    .card-actions {
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid var(--border-subtle);
    }

    .btn-create-version {
      width: 100%;
      padding: 8px 16px;
      background: var(--brand-gradient);
      color: white;
      border: none;
      border-radius: 4px;
      font-size: 0.85rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
    }

    .btn-create-version:hover:not(:disabled) {
      box-shadow: var(--glow-md);
    }

    .btn-create-version:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  `]
})
export class VersionInfoCardComponent {
  @Input() version: VersionMetadata | null = null;
  @Output() createVersion = new EventEmitter<void>();

  docsUrl = DOCS_URL;

  /** Format ISO datetime → local timezone "YYYY-MM-DD HH:MM:SS" */
  formatDate(iso: string): string {
    return formatDateLocal(iso);
  }

  getStatusLabel(status: string): string {
    switch (status) {
      case 'draft': return 'DRAFT';
      case 'inbuild': return 'INBUILD';
      case 'archived': return 'ARCHIVED';
      default: return status.toUpperCase();
    }
  }

  isArchived(): boolean {
    return this.version?.status === 'archived';
  }
}
