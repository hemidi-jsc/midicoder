/**
 * Project Info Card — hiển thị đầy đủ metadata của project đang active.
 * Dữ liệu lấy từ GET /projects/active.
 */

import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService, ProjectInfo } from '../../../core/api.service';
import { formatDateLocal } from '../../../core/date.util';

const APP_VERSION = '1.0.0';
const DOCS_URL = `https://docs.midicoder.com/ce/${APP_VERSION}/project-management`;

@Component({
  selector: 'app-project-info-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="info-card">
      <div class="card-header">
        <h3 class="card-title">📁 Project</h3>
        <a [href]="docsUrl" target="_blank" rel="noopener noreferrer" class="help-icon" title="Hướng dẫn quản lý project">❓</a>
      </div>

      @if (!project) {
        <p class="empty-state">Chưa có project active</p>
      } @else {
        <div class="field-list">
          <div class="field-row">
            <span class="field-label">name</span>
            <span class="field-value">{{ project!.name }}</span>
          </div>
          <div class="field-row">
            <span class="field-label">project_id</span>
            <span class="field-value monospace">{{ project!.project_id }}</span>
          </div>
          <div class="field-row">
            <span class="field-label">path</span>
            <span class="field-value monospace">{{ project!.path }}</span>
          </div>
          <div class="field-row">
            <span class="field-label">active</span>
            <span class="field-value"><span class="status-dot" title="Đang active"></span></span>
          </div>
          @if (project!.repo_url) {
            <div class="field-row">
              <span class="field-label">repo_url</span>
              <span class="field-value">
                <a [href]="project!.repo_url" target="_blank" rel="noopener noreferrer" class="repo-link">{{ getRepoHost(project!.repo_url) }}</a>
              </span>
            </div>
          }
          <div class="field-row">
            <span class="field-label">created_at</span>
            <span class="field-value monospace">{{ formatDate(project!.created_at) }}</span>
          </div>
          <div class="field-row">
            <span class="field-label">updated_at</span>
            <span class="field-value monospace">{{ formatDate(project!.updated_at) }}</span>
          </div>
        </div>

        <div class="card-actions">
          <button class="btn-open-ide" (click)="openInIde()" [attr.title]="'Mở trong VS Code'">
            📂 Mở dự án trong IDE
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
      min-width: 100px;
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

    .badge-active {
      background: rgba(63, 185, 80, 0.15);
      color: var(--accent-success);
      border: 1px solid rgba(63, 185, 80, 0.3);
    }

    .status-dot {
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent-success);
      box-shadow: 0 0 6px rgba(63, 185, 80, 0.6);
    }

    .card-actions {
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid var(--border-subtle);
    }

    .btn-open-ide {
      width: 100%;
      padding: 8px 16px;
      background: var(--bg-secondary);
      color: var(--text-primary);
      border: 1px solid var(--border-subtle);
      border-radius: 4px;
      font-size: 0.85rem;
      cursor: pointer;
      transition: all 0.2s;
    }

    .btn-open-ide:hover {
      border-color: var(--brand-color);
      color: var(--brand-color);
      box-shadow: var(--glow-sm);
    }
  `]
})
export class ProjectInfoCardComponent {
  @Input() project: ProjectInfo | null = null;

  docsUrl = DOCS_URL;

  formatDate(iso: string): string {
    return formatDateLocal(iso);
  }

  /** Extract host from repo URL for display */
  getRepoHost(url: string): string {
    if (!url) return '';
    try {
      const m = url.match(/^https?:\/\/([^/]+)/);
      if (m) return m[1];
      // Fallback: truncate long URL
      return url.length > 40 ? url.substring(0, 40) + '…' : url;
    } catch {
      return url;
    }
  }

  openInIde(): void {
    if (!this.project?.path) return;
    // Mở VS Code: code <path> (cross-platform)
    const path = this.project.path.replace(/\\/g, '/');
    // Dùng window.open với protocol vscode://
    // Fallback: mở command line
    const vscodeUrl = `vscode://file/${path}`;
    window.open(vscodeUrl, '_blank');
  }
}
