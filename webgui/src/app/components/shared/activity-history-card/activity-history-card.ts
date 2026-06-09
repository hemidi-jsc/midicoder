/**
 * Activity History Card — full width, hiển thị lịch sử hoạt động.
 * 2 chế độ: Gần đây (3 ngày) và Tất cả (phân trang 50 item/trang).
 */

import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { ApiService } from '../../../core/api.service';
import { formatDateLocal } from '../../../core/date.util';

export interface ActivityLog {
  id: number;
  timestamp: string;
  user: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details: string | null;
  status: string;
}

@Component({
  selector: 'app-activity-history',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="dashboard-card activity-card">
      <div class="activity-card-header">
        <h2 class="card-title">Lịch sử hoạt động</h2>
        <div class="activity-tabs">
          <button
            class="activity-tab"
            [class.active]="mode === 'recent'"
            (click)="switchMode('recent')"
          >
            Gần đây
            @if (recentCount > 0) {
              <span class="tab-count">{{ recentCount }}</span>
            }
          </button>
          <button
            class="activity-tab"
            [class.active]="mode === 'all'"
            (click)="switchMode('all')"
          >
            Tất cả
            @if (totalAll > 0) {
              <span class="tab-count">{{ totalAll }}</span>
            }
          </button>
        </div>
      </div>

      <!-- Loading -->
      @if (loading) {
        <div class="activity-loading">
          <div class="skeleton-item"><span class="sk"></span></div>
          <div class="skeleton-item"><span class="sk"></span></div>
          <div class="skeleton-item"><span class="sk"></span></div>
          <div class="skeleton-item"><span class="sk"></span></div>
        </div>
      }

      <!-- Recent Activities -->
      @if (!loading && mode === 'recent') {
        @if (recentActivities.length === 0) {
          <div class="activity-empty">
            <div class="empty-circle">
              <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6l4 2m6-2a10 10 0 11-20 0 10 10 0 0120 0z"/>
              </svg>
            </div>
            <span>Chưa có hoạt động nào trong 3 ngày gần đây</span>
          </div>
        } @else {
          <div class="activity-timeline">
            @for (item of recentActivities; track item.id; let ii = $index) {
              <div class="timeline-row" [class.error-row]="item.status === 'error'" [class.warning-row]="item.status === 'warning'">
                <div class="timeline-dot" [class]="dotClass(item.status)"></div>
                <div class="timeline-content">
                  <div class="timeline-main">
                    <span class="resource-badge" [class]="resourceBadgeClass(item.resource_type)">{{ item.resource_type }}</span>
                    <span class="action-text">{{ actionLabel(item.action) }}</span>
                    @if (item.resource_id) {
                      <code class="resource-ref">{{ item.resource_id }}</code>
                    }
                  </div>
                  <div class="timeline-sub">
                    <span class="status-label" [class]="statusLabelClass(item.status)">{{ statusLabel(item.status) }}</span>
                  </div>
                </div>
                <span class="timeline-ago">{{ formatTime(item.timestamp) }}</span>
              </div>
            }
          </div>
        }
      }

      <!-- All Activities with Pagination -->
      @if (!loading && mode === 'all') {
        @if (allActivities.length === 0) {
          <div class="activity-empty">
            <div class="empty-circle">
              <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6l4 2m6-2a10 10 0 11-20 0 10 10 0 0120 0z"/>
              </svg>
            </div>
            <span>Chưa có hoạt động nào</span>
          </div>
        } @else {
          <div class="activity-timeline">
            @for (item of allActivities; track item.id; let ii = $index) {
              <div class="timeline-row" [class.error-row]="item.status === 'error'" [class.warning-row]="item.status === 'warning'">
                <div class="timeline-dot" [class]="dotClass(item.status)"></div>
                <div class="timeline-content">
                  <div class="timeline-main">
                    <span class="resource-badge" [class]="resourceBadgeClass(item.resource_type)">{{ item.resource_type }}</span>
                    <span class="action-text">{{ actionLabel(item.action) }}</span>
                    @if (item.resource_id) {
                      <code class="resource-ref">{{ item.resource_id }}</code>
                    }
                  </div>
                  <div class="timeline-sub">
                    <span class="status-label" [class]="statusLabelClass(item.status)">{{ statusLabel(item.status) }}</span>
                  </div>
                </div>
                <span class="timeline-ago">{{ formatTime(item.timestamp) }}</span>
              </div>
            }
          </div>

          <!-- Pagination -->
          @if (totalPages > 1) {
            <div class="activity-pagination">
              <button class="pg-btn pg-prev" [disabled]="currentPage === 1" (click)="goToPage(currentPage - 1)">
                <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7"/>
                </svg>
              </button>
              @for (p of pageNumbers; track p) {
                @if (p === -1 || p === -2) {
                  <span class="pg-ellipsis">…</span>
                } @else {
                  <button
                    class="pg-btn"
                    [class.active]="p === currentPage"
                    (click)="goToPage(p)"
                  >{{ p }}</button>
                }
              }
              <button class="pg-btn pg-next" [disabled]="currentPage === totalPages" (click)="goToPage(currentPage + 1)">
                <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/>
                </svg>
              </button>
              <span class="pg-info">{{ currentPage }}/{{ totalPages }}</span>
            </div>
          }
        }
      }
    </div>
  `,
  styles: [`
    /* ---- Card shell (reuse .dashboard-card, override inside) ---- */
    .activity-card {
      padding: 24px;
    }

    /* ---- Header ---- */
    .activity-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }

    .card-title {
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 20px 0;
    }

    /* ---- Tabs ---- */
    .activity-tabs {
      display: flex;
      gap: 2px;
      background: var(--bg-secondary);
      border-radius: 6px;
      padding: 2px;
    }

    .activity-tab {
      border: none;
      background: transparent;
      color: var(--text-tertiary);
      font-size: 0.8rem;
      font-weight: 500;
      padding: 5px 14px;
      border-radius: 5px;
      cursor: pointer;
      transition: all 0.15s;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .activity-tab:hover {
      color: var(--text-secondary);
    }

    .activity-tab.active {
      background: var(--bg-card);
      color: var(--text-primary);
      box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }

    .tab-count {
      font-size: 0.65rem;
      font-weight: 700;
      padding: 1px 6px;
      border-radius: 8px;
      background: var(--bg-tertiary);
      color: var(--text-tertiary);
      line-height: 1.3;
    }

    .activity-tab.active .tab-count {
      background: rgba(252, 103, 103, 0.15);
      color: var(--brand-color);
    }

    /* ---- Skeleton loading ---- */
    .activity-loading {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .skeleton-item {
      height: 40px;
      border-radius: 6px;
      background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg-tertiary) 50%, var(--bg-secondary) 75%);
      background-size: 200% 100%;
      animation: shimmer 1.5s infinite;
    }

    @keyframes shimmer {
      0% { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }

    /* ---- Empty state ---- */
    .activity-empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      padding: 40px 20px;
      color: var(--text-tertiary);
      font-size: 0.82rem;
    }

    .empty-circle {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: var(--bg-secondary);
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--text-tertiary);
      margin-bottom: 4px;
    }

    /* ---- Timeline list ---- */
    .activity-timeline {
      max-height: 460px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
    }

    .activity-timeline::-webkit-scrollbar {
      width: 4px;
    }

    .activity-timeline::-webkit-scrollbar-thumb {
      background: var(--border-subtle);
      border-radius: 2px;
    }

    .activity-timeline::-webkit-scrollbar-track {
      background: transparent;
    }

    /* ---- Single timeline row ---- */
    .timeline-row {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 9px 0;
      border-bottom: 1px solid var(--border-subtle);
      transition: background 0.12s;
    }

    .timeline-row:last-child {
      border-bottom: none;
    }

    .timeline-row:hover {
      background: rgba(255,255,255,0.02);
    }

    .error-row {
      background: rgba(248, 81, 73, 0.04);
    }

    .warning-row {
      background: rgba(245, 158, 11, 0.04);
    }

    /* ---- Dot ---- */
    .timeline-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      margin-top: 6px;
      flex-shrink: 0;
    }

    .timeline-dot.dot-success { background: var(--accent-success); }
    .timeline-dot.dot-error { background: var(--accent-error); box-shadow: 0 0 6px rgba(248, 81, 73, 0.4); }
    .timeline-dot.dot-warning { background: #f59e0b; }
    .timeline-dot.dot-info { background: var(--brand-color); }

    /* ---- Content ---- */
    .timeline-content {
      flex: 1;
      min-width: 0;
    }

    .timeline-main {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .timeline-sub {
      margin-top: 3px;
    }

    /* ---- Resource badge ---- */
    .resource-badge {
      font-size: 0.65rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 2px 8px;
      border-radius: 3px;
      flex-shrink: 0;
    }

    .resource-badge.badge-version { background: rgba(168, 85, 247, 0.15); color: #a855f7; }
    .resource-badge.badge-project { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
    .resource-badge.badge-brief { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
    .resource-badge.badge-contract { background: rgba(249, 115, 22, 0.15); color: #f97316; }
    .resource-badge.badge-ir { background: rgba(6, 182, 212, 0.15); color: #06b6d4; }
    .resource-badge.badge-code { background: rgba(236, 72, 153, 0.15); color: #ec4899; }
    .resource-badge.badge-preview { background: rgba(20, 184, 166, 0.15); color: #14b8a6; }
    .resource-badge.badge-system { background: rgba(156, 163, 175, 0.15); color: #9ca3af; }
    .resource-badge.badge-default { background: var(--bg-tertiary); color: var(--text-tertiary); }

    /* ---- Action text ---- */
    .action-text {
      font-size: 0.82rem;
      font-weight: 500;
      color: var(--text-primary);
    }

    .resource-ref {
      font-size: 0.72rem;
      font-family: 'JetBrains Mono', 'Fira Code', monospace;
      color: var(--brand-color);
      background: rgba(252, 103, 103, 0.08);
      padding: 1px 6px;
      border-radius: 3px;
    }

    /* ---- Status label ---- */
    .status-label {
      font-size: 0.68rem;
      font-weight: 500;
    }

    .status-label.status-success { color: var(--accent-success); }
    .status-label.status-error { color: var(--accent-error); }
    .status-label.status-warning { color: #f59e0b; }
    .status-label.status-info { color: var(--brand-color); }

    /* ---- Time ---- */
    .timeline-ago {
      font-size: 0.7rem;
      color: var(--text-tertiary);
      white-space: nowrap;
      flex-shrink: 0;
      margin-top: 3px;
      font-variant-numeric: tabular-nums;
    }

    /* ---- Pagination ---- */
    .activity-pagination {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 3px;
      padding: 14px 0 4px;
      border-top: 1px solid var(--border-subtle);
      margin-top: 8px;
    }

    .pg-btn {
      border: 1px solid var(--border-subtle);
      background: transparent;
      color: var(--text-secondary);
      font-size: 0.75rem;
      padding: 3px 10px;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.12s;
      display: flex;
      align-items: center;
      justify-content: center;
      min-width: 30px;
    }

    .pg-btn:hover:not(:disabled):not(.active) {
      border-color: var(--brand-color);
      color: var(--brand-color);
    }

    .pg-btn.active {
      background: var(--brand-color);
      border-color: var(--brand-color);
      color: white;
      font-weight: 600;
    }

    .pg-btn:disabled {
      opacity: 0.3;
      cursor: not-allowed;
    }

    .pg-ellipsis {
      color: var(--text-tertiary);
      font-size: 0.8rem;
      padding: 0 4px;
    }

    .pg-info {
      font-size: 0.68rem;
      color: var(--text-tertiary);
      margin-left: 8px;
      font-variant-numeric: tabular-nums;
    }
  `]
})
export class ActivityHistoryCardComponent implements OnInit, OnDestroy {
  private subscriptions = new Subscription();

  // State
  mode: 'recent' | 'all' = 'recent';
  loading = false;

  // Recent
  recentActivities: ActivityLog[] = [];
  recentCount = 0;

  // All (paginated)
  allActivities: ActivityLog[] = [];
  currentPage = 1;
  totalAll = 0;
  totalPages = 0;
  pageNumbers: number[] = [];

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadRecent();
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  switchMode(mode: 'recent' | 'all'): void {
    if (this.mode === mode) return;
    this.mode = mode;
    this.currentPage = 1;
    if (mode === 'all') {
      this.loadAll();
    }
  }

  loadRecent(): void {
    this.loading = true;
    this.api.getActivityRecent().then(resp => {
      this.loading = false;
      if (resp.success && resp.data) {
        this.recentActivities = resp.data.activities || [];
        this.recentCount = resp.data.count || this.recentActivities.length;
      }
    }).catch(() => {
      this.loading = false;
    });
  }

  loadAll(): void {
    this.loading = true;
    this.api.getActivityAll(this.currentPage, 50).then(resp => {
      this.loading = false;
      if (resp.success && resp.data) {
        this.allActivities = resp.data.activities || [];
        this.totalAll = resp.data.total || 0;
        this.totalPages = resp.data.total_pages || 1;
        this.buildPageNumbers();
      }
    }).catch(() => {
      this.loading = false;
    });
  }

  goToPage(page: number): void {
    if (page < 1 || page > this.totalPages || page === this.currentPage) return;
    this.currentPage = page;
    this.loadAll();
  }

  private buildPageNumbers(): void {
    const pages: number[] = [];
    const total = this.totalPages;
    const current = this.currentPage;

    if (total <= 7) {
      for (let i = 1; i <= total; i++) pages.push(i);
    } else {
      pages.push(1);
      const start = Math.max(2, current - 2);
      const end = Math.min(total - 1, current + 2);
      if (start > 2) pages.push(-1);
      for (let i = start; i <= end; i++) pages.push(i);
      if (end < total - 1) pages.push(-2);
      pages.push(total);
    }
    this.pageNumbers = pages;
  }

  // ---- Formatting helpers ----

  actionLabel(action: string): string {
    const parts = action.split('.');
    if (parts.length < 2) return action;
    const type = parts[0].charAt(0).toUpperCase() + parts[0].slice(1);
    const verb = parts.slice(1).join(' ').replace(/_/g, ' ');
    return `${type} ${verb}`;
  }

  statusLabel(status: string): string {
    switch (status) {
      case 'success': return 'Thành công';
      case 'error': return 'Lỗi';
      case 'warning': return 'Cảnh báo';
      case 'info': return 'Thông tin';
      default: return status;
    }
  }

  formatTime(ts: string): string {
    try {
      const d = new Date(ts.replace(' ', 'T'));
      const now = new Date();
      const diffMs = now.getTime() - d.getTime();
      const diffMin = Math.floor(diffMs / 60000);
      const diffHr = Math.floor(diffMin / 60);
      const diffDay = Math.floor(diffHr / 24);

      if (diffMin < 1) return 'vừa xong';
      if (diffMin < 60) return `${diffMin}p trước`;
      if (diffHr < 24) return `${diffHr}h trước`;
      if (diffDay < 7) return `${diffDay}n trước`;
      return formatDateLocal(d.toISOString()).split(' ')[0];
    } catch {
      return ts;
    }
  }

  dotClass(status: string): string {
    return `dot-${status}`;
  }

  statusLabelClass(status: string): string {
    return `status-${status}`;
  }

  resourceBadgeClass(resourceType: string): string {
    const map: Record<string, string> = {
      'version': 'badge-version',
      'project': 'badge-project',
      'brief': 'badge-brief',
      'contract': 'badge-contract',
      'ir': 'badge-ir',
      'code': 'badge-code',
      'preview': 'badge-preview',
      'system': 'badge-system',
    };
    return `resource-badge ${map[resourceType] || 'badge-default'}`;
  }
}
