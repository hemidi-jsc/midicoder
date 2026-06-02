/**
 * Component Dashboard
 * Hiển thị tổng quan pipeline và các thao tác nhanh
 */

import { Component, OnInit, OnDestroy, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { PipelineStore, PhaseStatus } from '../../core/pipeline.store';
import { ApiService } from '../../core/api.service';
import { VersionService, VersionInfo } from '../../core/version.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  template: `
    <div class="dashboard-container">
      <!-- Header -->
      <div class="dashboard-header">
        <h1 class="dashboard-title">Bảng điều khiển</h1>
        <p class="dashboard-subtitle">
          Project: <span class="text-white">{{ projectName() || 'chưa khởi tạo' }}</span>
          @if (activeVersion()) {
            &nbsp;— {{ activeVersion() }}
          }
          @if (pipelineInitialized()) {
            &nbsp;|&nbsp; Tiến độ: <span class="text-white">{{ overallProgress() }}</span>%
          }
        </p>
      </div>

      <!-- No Versions State (workspace exists, versions empty) -->
      @if (workspaceInitialized() && !pipelineInitialized()) {
        <div class="card init-card">
          <div class="init-content">
            <h2 class="init-title">📋 Tạo phiên bản đầu tiên</h2>
            <p class="init-desc">Project đã được khởi tạo. Tạo phiên bản đầu tiên để bắt đầu pipeline.</p>
            <button class="btn-primary-large" (click)="showCreateVersionModal = true">
              Tạo phiên bản
            </button>
          </div>
        </div>
      }

      <!-- Pipeline Progress (versions exist) -->
      @if (pipelineInitialized()) {
        <!-- Pipeline Progress Card -->
        <div class="dashboard-card">
          <h2 class="card-title">Tiến độ Pipeline</h2>

          <!-- Progress Bar -->
          <div class="progress-section">
            <div class="progress-header">
              <span class="progress-label">Tổng tiến độ</span>
              <span class="progress-value">{{ overallProgress() }}%</span>
            </div>
            <div class="progress-track">
              <div
                class="progress-fill"
                [style.width.%]="overallProgress()"
              ></div>
            </div>
          </div>

          <!-- Phase Status Grid -->
          <div class="phase-grid">
            <div class="phase-item">
              <div class="phase-icon" [ngClass]="'phase-' + initPhase().status">
                @if (initPhase().status === 'complete') { ✓ }
                @else if (initPhase().status === 'in_progress') { ◎ }
                @else { 1 }
              </div>
              <p class="phase-name">Init</p>
              <p class="phase-status">{{ getPhaseStatusText(initPhase().status) }}</p>
            </div>
            <div class="phase-item">
              <div class="phase-icon" [ngClass]="'phase-' + briefPhase().status">
                @if (briefPhase().status === 'complete') { ✓ }
                @else if (briefPhase().status === 'in_progress') { ◎ }
                @else { 2 }
              </div>
              <p class="phase-name">Brief</p>
              <p class="phase-status">{{ getPhaseStatusText(briefPhase().status) }}</p>
            </div>
            <div class="phase-item">
              <div class="phase-icon" [ngClass]="'phase-' + contractPhase().status">
                @if (contractPhase().status === 'complete') { ✓ }
                @else if (contractPhase().status === 'in_progress') { ◎ }
                @else { 3 }
              </div>
              <p class="phase-name">Contract</p>
              <p class="phase-status">{{ getPhaseStatusText(contractPhase().status) }}</p>
            </div>
            <div class="phase-item">
              <div class="phase-icon" [ngClass]="'phase-' + irPhase().status">
                @if (irPhase().status === 'complete') { ✓ }
                @else if (irPhase().status === 'in_progress') { ◎ }
                @else { 4 }
              </div>
              <p class="phase-name">IR</p>
              <p class="phase-status">{{ getPhaseStatusText(irPhase().status) }}</p>
            </div>
            <div class="phase-item">
              <div class="phase-icon" [ngClass]="'phase-' + codePhase().status">
                @if (codePhase().status === 'complete') { ✓ }
                @else if (codePhase().status === 'in_progress') { ◎ }
                @else { 5 }
              </div>
              <p class="phase-name">Code</p>
              <p class="phase-status">{{ getPhaseStatusText(codePhase().status) }}</p>
            </div>
            <div class="phase-item">
              <div class="phase-icon" [ngClass]="'phase-' + previewPhase().status">
                @if (previewPhase().status === 'complete') { ✓ }
                @else if (previewPhase().status === 'in_progress') { ◎ }
                @else { 6 }
              </div>
              <p class="phase-name">Preview</p>
              <p class="phase-status">{{ getPhaseStatusText(previewPhase().status) }}</p>
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="actions-grid">
          <a routerLink="/brief-editor" class="action-card">
            <h3 class="action-title">Tạo brief mới</h3>
            <p class="action-desc">Tạo và chỉnh sửa brief cho project</p>
            <span class="action-arrow">→</span>
          </a>
          <a routerLink="/contract-viewer" class="action-card">
            <h3 class="action-title">Tạo hợp đồng</h3>
            <p class="action-desc">Tạo hợp đồng DSL từ brief</p>
            <span class="action-arrow">→</span>
          </a>
          <a routerLink="/code-generator" class="action-card">
            <h3 class="action-title">Xem mã đã tạo</h3>
            <p class="action-desc">Xem và quản lý code đã tạo</p>
            <span class="action-arrow">→</span>
          </a>
          <a routerLink="/preview" class="action-card">
            <h3 class="action-title">Bắt đầu xem trước</h3>
            <p class="action-desc">Khởi động preview project</p>
            <span class="action-arrow">→</span>
          </a>
        </div>

        <!-- Versions Card -->
        <div class="dashboard-card">
          <div class="card-header-row">
            <h2 class="card-title">Phiên bản</h2>
            <button class="btn-small" (click)="showCreateVersionModal = true">+ Tạo phiên bản mới</button>
          </div>
          <div class="version-list">
            @for (v of versions(); track v.version) {
              <div class="version-row" [class.active]="v.version === activeVersion()" (click)="switchVersion(v.version)">
                <span class="version-name">{{ v.version }}</span>
                <span class="version-status" [class]="getStatusClass(v.status)">{{ v.status }}</span>
                <span class="version-progress">{{ versionService.calculateProgress(v) }}%</span>
              </div>
            } @empty {
              <p class="empty-text">Chưa có phiên bản nào</p>
            }
          </div>
        </div>
      }

      <!-- Create Version Modal -->
      @if (showCreateVersionModal) {
        <div class="modal-overlay" (click)="closeCreateModal()">
          <div class="modal" (click)="$event.stopPropagation()">
            <div class="modal-header">
              <h3>Tạo phiên bản mới</h3>
              <button class="btn-close" (click)="closeCreateModal()">×</button>
            </div>
            <div class="modal-body">
              <div class="form-group">
                <label class="form-label" for="versionName">Tên phiên bản</label>
                <input
                  id="versionName"
                  type="text"
                  class="form-input"
                  [(ngModel)]="newVersionName"
                  placeholder="v1.0.1"
                />
              </div>
              <div class="form-group">
                <label class="form-label" for="fromVersion">Từ phiên bản (tùy chọn)</label>
                <select id="fromVersion" [(ngModel)]="fromVersion" class="form-input">
                  <option value="">Tạo mới hoàn toàn</option>
                  @for (v of versions(); track v.version) {
                    <option [value]="v.version">{{ v.version }}</option>
                  }
                </select>
              </div>
              @if (createVersionError) {
                <p class="error-text">{{ createVersionError }}</p>
              }
            </div>
            <div class="modal-footer">
              <button class="btn-secondary" (click)="closeCreateModal()">Hủy</button>
              <button class="btn-primary" (click)="createVersion()" [disabled]="!newVersionName || isCreatingVersion">
                {{ isCreatingVersion ? 'Đang tạo...' : 'Tạo' }}
              </button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .dashboard-container {
      padding: 32px 32px 32px 0;
    }

    .dashboard-header {
      margin-bottom: 32px;
    }

    .dashboard-title {
      font-size: 1.75rem;
      font-weight: 700;
      color: var(--text-primary);
      margin: 0 0 8px 0;
    }

    .dashboard-subtitle {
      font-size: 0.95rem;
      color: var(--text-secondary);
      margin: 0;
    }

    /* Init Card */
    .init-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      padding: 48px;
      margin-bottom: 24px;
      text-align: center;
    }

    .init-content {
      max-width: 500px;
      margin: 0 auto;
    }

    .init-title {
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--text-primary);
      margin: 0 0 12px 0;
    }

    .init-desc {
      font-size: 0.95rem;
      color: var(--text-secondary);
      margin: 0 0 32px 0;
    }

    .init-loading {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;
      color: var(--text-secondary);
    }

    .spinner {
      width: 32px;
      height: 32px;
      border: 3px solid var(--border-subtle);
      border-top-color: var(--brand-color);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .init-form {
      text-align: left;
      margin-top: 24px;
    }

    .form-group {
      margin-bottom: 16px;
    }

    .form-label {
      display: block;
      font-size: 0.85rem;
      font-weight: 500;
      color: var(--text-secondary);
      margin-bottom: 6px;
    }

    .form-input {
      width: 100%;
      padding: 10px 12px;
      font-size: 0.9rem;
      border-radius: 4px;
      outline: none;
      transition: border-color 0.2s;
      color: var(--text-primary);
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      box-sizing: border-box;
    }

    .form-input:focus {
      border-color: var(--brand-color) !important;
      box-shadow: var(--glow-sm);
    }

    .form-input:focus {
      border-color: var(--brand-color) !important;
      box-shadow: var(--glow-sm);
    }

    .btn-primary-large {
      width: 100%;
      padding: 12px 24px;
      background: var(--brand-gradient);
      color: white;
      border: none;
      border-radius: 4px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      margin-top: 8px;
    }

    .btn-primary-large:hover:not(:disabled) {
      box-shadow: var(--glow-md);
    }

    .btn-primary-large:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    /* Dashboard Card */
    .dashboard-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      padding: 24px;
      margin-bottom: 24px;
    }

    .card-title {
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 20px 0;
    }

    .card-header-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }

    .card-header-row .card-title {
      margin: 0;
    }

    /* Progress Section */
    .progress-section {
      margin-bottom: 28px;
    }

    .progress-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }

    .progress-label {
      font-size: 0.9rem;
      color: var(--text-secondary);
    }

    .progress-value {
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--brand-color);
    }

    .progress-track {
      height: 8px;
      background: var(--bg-secondary);
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      background: var(--brand-gradient);
      transition: width 0.5s ease;
    }

    /* Phase Grid */
    .phase-grid {
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 16px;
    }

    .phase-item {
      text-align: center;
    }

    .phase-icon {
      width: 56px;
      height: 56px;
      margin: 0 auto 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 2px solid var(--border-subtle);
      font-size: 1.4rem;
      transition: all 0.2s;
    }

    .phase-item .phase-icon.phase-complete {
      border-color: var(--accent-success);
      color: var(--accent-success);
      background: rgba(63, 185, 80, 0.1);
    }

    .phase-item .phase-icon.phase-in_progress {
      border-color: var(--brand-color);
      color: var(--brand-color);
      background: rgba(252, 103, 103, 0.1);
      box-shadow: 0 0 15px rgba(252, 103, 103, 0.3);
    }

    .phase-item .phase-icon.phase-pending {
      border-color: var(--border-subtle);
      color: var(--text-tertiary);
    }

    .phase-item .phase-icon.phase-error {
      border-color: var(--accent-error);
      color: var(--accent-error);
      background: rgba(248, 81, 73, 0.1);
    }

    .phase-name {
      font-size: 0.85rem;
      font-weight: 500;
      color: var(--text-primary);
      margin: 0 0 4px 0;
    }

    .phase-status {
      font-size: 0.75rem;
      color: var(--text-secondary);
      margin: 0;
    }

    /* Actions Grid */
    .actions-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
      margin-bottom: 24px;
    }

    .action-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      padding: 20px 24px;
      text-decoration: none;
      display: flex;
      flex-direction: column;
      gap: 8px;
      transition: all 0.2s;
      position: relative;
    }

    .action-card:hover {
      border-color: var(--border-hover);
      background: rgba(255, 255, 255, 0.05);
    }

    .action-title {
      font-size: 1rem;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }

    .action-desc {
      font-size: 0.85rem;
      color: var(--text-secondary);
      margin: 0;
    }

    .action-arrow {
      position: absolute;
      top: 20px;
      right: 24px;
      font-size: 1.2rem;
      color: var(--brand-color);
      opacity: 0.7;
    }

    /* Versions */
    .btn-small {
      background: transparent;
      border: 1px solid var(--border-subtle);
      color: var(--text-secondary);
      padding: 6px 12px;
      font-size: 0.8rem;
      cursor: pointer;
      transition: all 0.2s;
      border-radius: 4px;
    }

    .btn-small:hover {
      border-color: var(--brand-color);
      color: var(--brand-color);
    }

    .version-list {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .version-row {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 8px 12px;
      cursor: pointer;
      transition: all 0.2s;
      border-left: 3px solid transparent;
    }

    .version-row:hover {
      background: var(--bg-card);
    }

    .version-row.active {
      border-left-color: var(--brand-color);
      background: rgba(252, 103, 103, 0.1);
    }

    .version-name {
      font-weight: 500;
      color: var(--text-primary);
      font-size: 0.9rem;
    }

    .version-status {
      font-size: 0.7rem;
      padding: 2px 6px;
      text-transform: uppercase;
    }

    .version-status.status-active {
      background: rgba(63, 185, 80, 0.2);
      color: var(--accent-success);
    }

    .version-status.status-draft {
      background: rgba(210, 153, 34, 0.2);
      color: var(--accent-warning);
    }

    .version-status.status-archived {
      background: rgba(139, 148, 158, 0.2);
      color: var(--text-tertiary);
    }

    .version-progress {
      margin-left: auto;
      font-size: 0.8rem;
      color: var(--text-secondary);
    }

    .empty-text {
      color: var(--text-tertiary);
      font-size: 0.85rem;
      text-align: center;
      padding: 16px;
    }

    .error-text {
      color: var(--accent-error);
      font-size: 0.85rem;
      margin-top: 8px;
    }

    /* Modal */
    .modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.7);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 100;
    }

    .modal {
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      width: 100%;
      max-width: 420px;
    }

    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 20px;
      border-bottom: 1px solid var(--border-subtle);
    }

    .modal-header h3 {
      margin: 0;
      font-size: 1.1rem;
      color: var(--text-primary);
    }

    .btn-close {
      background: none;
      border: none;
      color: var(--text-secondary);
      font-size: 1.5rem;
      cursor: pointer;
    }

    .modal-body {
      padding: 20px;
    }

    .modal-footer {
      display: flex;
      justify-content: flex-end;
      gap: 12px;
      padding: 16px 20px;
      border-top: 1px solid var(--border-subtle);
    }

    .btn-secondary {
      padding: 8px 16px;
      background: var(--bg-card);
      color: var(--text-secondary);
      border: 1px solid var(--border-subtle);
      cursor: pointer;
      font-size: 0.9rem;
      border-radius: 4px;
    }

    .btn-secondary:hover {
      background: var(--border-subtle);
    }

    .btn-primary {
      padding: 8px 16px;
      background: var(--brand-gradient);
      color: white;
      border: none;
      cursor: pointer;
      font-size: 0.9rem;
      font-weight: 500;
      border-radius: 4px;
    }

    .btn-primary:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .btn-primary:hover:not(:disabled) {
      box-shadow: var(--glow-md);
    }

    .form-group select.form-input {
      appearance: none;
    }

    .form-group select.form-input option {
      background: var(--bg-secondary);
      color: var(--text-primary);
    }
  `]
})
export class DashboardComponent implements OnInit, OnDestroy {
  private pipelineStore = inject(PipelineStore);
  private api = inject(ApiService);
  public versionService = inject(VersionService);

  private subscriptions: Subscription[] = [];

  // Reactive version list
  versions = signal<VersionInfo[]>([]);

  // Version creation
  showCreateVersionModal = false;
  newVersionName = '';
  fromVersion = '';
  isCreatingVersion = false;
  createVersionError = '';

  // Direct accessors
  initPhase() { return this.pipelineStore.getInitPhase(); }
  briefPhase() { return this.pipelineStore.getBriefPhase(); }
  contractPhase() { return this.pipelineStore.getContractPhase(); }
  irPhase() { return this.pipelineStore.getIRPhase(); }
  codePhase() { return this.pipelineStore.getCodePhase(); }
  previewPhase() { return this.pipelineStore.getPreviewPhase(); }
  projectName() { return this.pipelineStore.getProjectName(); }
  activeVersion() { return this.pipelineStore.getActiveVersion(); }
  overallProgress() { return this.pipelineStore.overallProgress(); }
  workspaceInitialized() { return this.pipelineStore.isWorkspaceInitialized(); }

  constructor() {
    // Subscribe to versions
    this.subscriptions.push(
      this.versionService.versions$.subscribe(v => this.versions.set(v))
    );
  }

  /**
   * Check if pipeline has been initialized
   */
  pipelineInitialized(): boolean {
    const versions = this.versions();
    return versions.length > 0;
  }

  ngOnInit(): void {
    this.pipelineStore.loadStatus();
    this.versionService.loadVersions();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  /**
   * Get CSS class for version status
   */
  getStatusClass(status: string): string {
    return `version-status status-${status}`;
  }

  /**
   * Create new version
   */
  async createVersion(): Promise<void> {
    if (!this.newVersionName.trim()) return;

    this.isCreatingVersion = true;
    this.createVersionError = '';

    try {
      await this.versionService.createVersion({
        name: this.newVersionName.trim(),
        fromVersion: this.fromVersion || undefined,
      });

      this.showCreateVersionModal = false;
      this.newVersionName = '';
      this.fromVersion = '';
      await this.pipelineStore.loadStatus();
    } catch (error: any) {
      this.createVersionError = error.message || 'Tạo phiên bản thất bại';
    } finally {
      this.isCreatingVersion = false;
    }
  }

  /**
   * Switch version
   */
  switchVersion(version: string): void {
    this.versionService.setActiveVersion(version);
  }

  /**
   * Close create version modal
   */
  closeCreateModal(): void {
    this.showCreateVersionModal = false;
    this.newVersionName = '';
    this.fromVersion = '';
    this.createVersionError = '';
  }

  /**
   * Get status text
   */
  getPhaseStatusText(status: PhaseStatus): string {
    switch (status) {
      case 'complete': return 'Hoàn thành';
      case 'in_progress': return 'Đang xử lý';
      case 'error': return 'Lỗi';
      default: return 'Chờ xử lý';
    }
  }
}
