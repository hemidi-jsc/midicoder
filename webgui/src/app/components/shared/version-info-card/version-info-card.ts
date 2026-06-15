/**
 * Version Info Card — hiển thị đầy đủ metadata của version đang active.
 * Dữ liệu lấy từ VersionService.
 */

import { Component, inject, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { formatDateLocal } from '../../../core/date.util';
import { I18nPipe } from '../../../core/i18n.pipe';
import { I18nService } from '../../../core/i18n.service';
import { DOCS_BASE } from '../../../core/app.constants';

const DOCS_URL = `${DOCS_BASE}/version-management`;

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
  imports: [CommonModule, I18nPipe],
  template: `
    <div class="info-card">
      <div class="card-header">
        <h3 class="card-title">{{ 'version.heading' | i18n }}</h3>
        <a [href]="docsUrl" target="_blank" rel="noopener noreferrer" class="help-icon" attr.title="{{ 'version.helpTitle' | i18n }}"><i class="fa-solid fa-circle-question"></i></a>
      </div>

      @if (!version) {
        <p class="empty-state">{{ 'version.noActive' | i18n }}</p>
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
                <span class="status-dot" attr.title="{{ 'version.selected' | i18n }}"></span>
              } @else {
                <span class="status-dot status-dot-inactive" attr.title="{{ 'version.notActive' | i18n }}"></span>
              }
            </span>
          </div>
          <div class="field-row">
            <span class="field-label">parent_version</span>
            <span class="field-value monospace">{{ version!.parent_version || 'null' }}</span>
          </div>
          <div class="field-row">
            <span class="field-label">branch</span>
            <span class="field-value">
              @if (version!.branch && version!.branch !== 'N/A') {
                <span class="repo-link">{{ version!.branch }}</span>
              } @else {
                <span class="field-value-null">null</span>
              }
            </span>
          </div>
          <div class="field-row">
            <span class="field-label">created_at</span>
            <span class="field-value monospace">{{ formatDate(version!.created_at) }}</span>
          </div>
          <div class="field-row">
            <span class="field-label">updated_at</span>
            <span class="field-value monospace">{{ formatDate(version!.updated_at) }}</span>
          </div>
        </div>

        <div class="card-actions">
          <button class="btn-create-version" (click)="createVersion.emit()" [disabled]="isArchived()">
            ＋ {{ 'version.createNew' | i18n }}
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

    .field-value-null {
      color: var(--text-tertiary);
      font-style: italic;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
    }

    .repo-link {
      color: var(--brand-color);
      text-decoration: none;
      font-size: 0.75rem;
      font-family: 'JetBrains Mono', monospace;
      transition: color 0.2s;
    }

    .repo-link:hover {
      color: #fb6363;
      text-decoration: underline;
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

  private i18n = inject(I18nService);
  docsUrl = DOCS_URL;

  /** Format ISO datetime → local timezone "YYYY-MM-DD HH:MM:SS" */
  formatDate(iso: string): string {
    return formatDateLocal(iso);
  }

  getStatusLabel(status: string): string {
    switch (status) {
      case 'draft': return this.i18n.t('version.statusDraft');
      case 'inbuild': return this.i18n.t('version.statusInbuild');
      case 'archived': return this.i18n.t('version.statusArchived');
      default: return status.toUpperCase();
    }
  }

  isArchived(): boolean {
    return this.version?.status === 'archived';
  }
}
