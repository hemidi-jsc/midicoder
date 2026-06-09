/**
 * Component Dashboard
 * Hiển thị tổng quan pipeline và các thao tác nhanh
 */

import { Component, OnInit, OnDestroy, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { PipelineStore, PhaseStatus } from '../../core/pipeline.store';
import { ApiService } from '../../core/api.service';
import { VersionService, VersionInfo } from '../../core/version.service';
import { Subscription } from 'rxjs';
import { ProjectCreateFormComponent } from '../../components/shared/project-create-form/project-create-form';
import { VersionCreateFormComponent } from '../../components/shared/version-create-form/version-create-form';

export interface ProjectInfo {
  id: number;
  project_id: string;
  name: string;
  path: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule, ProjectCreateFormComponent, VersionCreateFormComponent],
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

      <!-- No Project State — first time user -->
      @if (!workspaceInitialized()) {
        <div class="card init-card">
          <div class="init-content">
            <h2 class="init-title">🚀 Tạo hoặc Import Project</h2>
            <p class="init-desc">Tạo project mới hoặc import project Midicoder hiện có để bắt đầu.</p>
            <app-project-create-form />
          </div>
        </div>
      }

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
      }

      <!-- Create Version Modal -->
      @if (showCreateVersionModal) {
        <app-version-create-form
          [existingVersionCount]="versions().length"
          (versionCreated)="closeCreateModal()"
          (cancel)="closeCreateModal()"
        />
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

    /* Project create form */
    .project-create-form {
      display: flex;
      flex-direction: column;
      gap: 18px;
      margin-top: 24px;
      max-width: 480px;
      text-align: left;
    }

    .project-create-form .form-row {
      text-align: left;
    }

    .form-row label.form-label {
      display: block;
      font-size: 0.8rem;
      color: var(--text-secondary);
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .form-row input.form-input,
    .form-row select.form-input {
      width: 100%;
      padding: 10px 12px;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      color: var(--text-primary);
      font-size: 0.875rem;
      font-family: 'JetBrains Mono', 'Fira Code', monospace;
      text-align: left;
    }

    .form-row input.form-input:focus,
    .form-row select.form-input:focus {
      outline: none;
      border-color: var(--brand-color);
      box-shadow: var(--glow-sm);
    }

    .form-row select.form-input {
      appearance: none;
      padding-right: 32px;
      background-image: url("data:image/svg+xml,%3Csvg width='10' height='6' viewBox='0 0 10 6' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1L5 5L9 1' stroke='%23fc6767' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 12px center;
    }

    .form-row select.form-input option {
      background: var(--bg-secondary);
      color: var(--text-primary);
    }

    /* Stack radio groups */

    .form-actions {
      margin-top: 8px;
    }

    .btn-primary-large {
      width: 100%;
      padding: 12px 20px;
      font-size: 1rem;
      font-weight: 600;
      color: white;
      background: var(--brand-gradient);
      border: none;
      cursor: pointer;
      transition: box-shadow 0.2s;
    }

    .btn-primary-large:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .btn-primary-large:hover:not(:disabled) {
      box-shadow: var(--glow-md);
    }

    .loading-text {
      text-align: center;
      color: var(--text-muted);
      font-size: 0.875rem;
      margin-top: 32px;
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
  activeVersion = signal<string>('');

  // Version creation
  showCreateVersionModal = false;

  // Direct accessors
  initPhase() { return this.pipelineStore.getInitPhase(); }
  briefPhase() { return this.pipelineStore.getBriefPhase(); }
  contractPhase() { return this.pipelineStore.getContractPhase(); }
  irPhase() { return this.pipelineStore.getIRPhase(); }
  codePhase() { return this.pipelineStore.getCodePhase(); }
  previewPhase() { return this.pipelineStore.getPreviewPhase(); }
  projectName() { return this.pipelineStore.getProjectName(); }
  overallProgress() { return this.pipelineStore.overallProgress(); }

  // Expose the PipelineStore's workspace signal directly for template reactivity
  workspaceInitialized = this.pipelineStore.workspaceInitializedSignal;

  constructor() {
    // Subscribe to versions
    this.subscriptions.push(
      this.versionService.versions$.subscribe(v => this.versions.set(v))
    );
    this.subscriptions.push(
      this.versionService.activeVersion$.subscribe(v => this.activeVersion.set(v))
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

  /**
   * Switch version — calls versionService, no page reload
   */
  switchVersion(version: string): void {
    this.versionService.setActiveVersion(version);
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
   * Close create version modal
   */
  closeCreateModal(): void {
    this.showCreateVersionModal = false;
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
