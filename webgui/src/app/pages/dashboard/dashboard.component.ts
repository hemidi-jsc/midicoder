/**
 * Component Dashboard
 * Hiển thị tổng quan pipeline và các thao tác nhanh
 */

import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { PipelineStore, PhaseStatus } from '../../core/pipeline.store';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="dashboard-container">
      <!-- Header -->
      <div class="dashboard-header">
        <h1 class="dashboard-title">Bảng điều khiển</h1>
        <p class="dashboard-subtitle">Tiến độ pipeline: <span class="text-white">{{ overallProgress() }}</span>%</p>
      </div>

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
          <!-- Init Phase -->
          <div class="phase-item">
            <div class="phase-icon" [ngClass]="'phase-' + initPhase().status">
              @if (initPhase().status === 'complete') { ✓ }
              @else if (initPhase().status === 'in_progress') { ◎ }
              @else { 1 }
            </div>
            <p class="phase-name">Init</p>
            <p class="phase-status">{{ getPhaseStatusText(initPhase().status) }}</p>
          </div>

          <!-- Brief Phase -->
          <div class="phase-item">
            <div class="phase-icon" [ngClass]="'phase-' + briefPhase().status">
              @if (briefPhase().status === 'complete') { ✓ }
              @else if (briefPhase().status === 'in_progress') { ◎ }
              @else { 2 }
            </div>
            <p class="phase-name">Brief</p>
            <p class="phase-status">{{ getPhaseStatusText(briefPhase().status) }}</p>
          </div>

          <!-- Contract Phase -->
          <div class="phase-item">
            <div class="phase-icon" [ngClass]="'phase-' + contractPhase().status">
              @if (contractPhase().status === 'complete') { ✓ }
              @else if (contractPhase().status === 'in_progress') { ◎ }
              @else { 3 }
            </div>
            <p class="phase-name">Contract</p>
            <p class="phase-status">{{ getPhaseStatusText(contractPhase().status) }}</p>
          </div>

          <!-- IR Phase -->
          <div class="phase-item">
            <div class="phase-icon" [ngClass]="'phase-' + irPhase().status">
              @if (irPhase().status === 'complete') { ✓ }
              @else if (irPhase().status === 'in_progress') { ◎ }
              @else { 4 }
            </div>
            <p class="phase-name">IR</p>
            <p class="phase-status">{{ getPhaseStatusText(irPhase().status) }}</p>
          </div>

          <!-- Code Phase -->
          <div class="phase-item">
            <div class="phase-icon" [ngClass]="'phase-' + codePhase().status">
              @if (codePhase().status === 'complete') { ✓ }
              @else if (codePhase().status === 'in_progress') { ◎ }
              @else { 5 }
            </div>
            <p class="phase-name">Code</p>
            <p class="phase-status">{{ getPhaseStatusText(codePhase().status) }}</p>
          </div>

          <!-- Preview Phase -->
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

      <!-- Recent Activity -->
      <div class="dashboard-card">
        <h2 class="card-title">Hoạt động gần đây</h2>
        <div class="activity-list">
          <div class="activity-item">
            <span class="activity-icon success">✓</span>
            <span class="activity-text">IR Build completed</span>
            <span class="activity-time">2 phút trước</span>
          </div>
          <div class="activity-item">
            <span class="activity-icon success">✓</span>
            <span class="activity-text">Contract validation passed</span>
            <span class="activity-time">5 phút trước</span>
          </div>
          <div class="activity-item">
            <span class="activity-icon success">✓</span>
            <span class="activity-text">Master brief saved</span>
            <span class="activity-time">15 phút trước</span>
          </div>
        </div>
      </div>
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

    /* Activity List */
    .activity-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .activity-item {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .activity-icon {
      font-size: 0.9rem;
      color: var(--accent-success);
    }

    .activity-text {
      font-size: 0.9rem;
      color: var(--text-primary);
      flex: 1;
    }

    .activity-time {
      font-size: 0.8rem;
      color: var(--text-tertiary);
    }
  `]
})
export class DashboardComponent implements OnInit, OnDestroy {
  private subscriptions: Subscription[] = [];

  constructor(private pipelineStore: PipelineStore) {}

  // Direct method calls to pipeline store
  initPhase() { return this.pipelineStore.getInitPhase(); }
  briefPhase() { return this.pipelineStore.getBriefPhase(); }
  contractPhase() { return this.pipelineStore.getContractPhase(); }
  irPhase() { return this.pipelineStore.getIRPhase(); }
  codePhase() { return this.pipelineStore.getCodePhase(); }
  previewPhase() { return this.pipelineStore.getPreviewPhase(); }
  overallProgress() { return this.pipelineStore.overallProgress(); }

  ngOnInit(): void {
    // Load pipeline status
    this.pipelineStore.loadStatus();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  /**
   * Get CSS class cho phase status
   */
  getPhaseClass(status: PhaseStatus): string {
    switch (status) {
      case 'complete':
        return 'border-accent-success bg-accent-success bg-opacity-10 text-accent-success';
      case 'in_progress':
        return 'border-accent-primary bg-accent-primary bg-opacity-10 text-accent-primary animate-pulse';
      case 'error':
        return 'border-accent-error bg-accent-error bg-opacity-10 text-accent-error';
      default:
        return 'border-border-primary text-text-tertiary';
    }
  }

  /**
   * Get status text
   */
  getPhaseStatusText(status: PhaseStatus): string {
    switch (status) {
      case 'complete':
        return 'Hoàn thành';
      case 'in_progress':
        return 'Đang xử lý';
      case 'error':
        return 'Lỗi';
      default:
        return 'Chờ xử lý';
    }
  }
}