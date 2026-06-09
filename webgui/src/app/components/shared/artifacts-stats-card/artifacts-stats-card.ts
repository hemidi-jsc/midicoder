/**
 * Artifacts Stats Card — full width, 4 columns cho Briefs, Contracts, IR, Code.
 * Hiển thị thống kê chi tiết của các artifacts trong version active.
 */

import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface PipelineStatus {
  brief: string;
  contract: string;
  ir: string;
  code: string;
}

export interface BriefStats {
  count: number;
  status: string;
  title: string;
  word_count: number;
  clarification_count: number;
  change_count: number;
  updated_at: string;
  types: Record<string, number>;
}

export interface ContractStats {
  count: number;
  categories: Record<string, { status: string; updated_at: string }>;
  total_entities: number;
  total_commands: number;
  total_queries: number;
  total_events: number;
}

export interface IRStats {
  operations: number;
  data_flows: number;
  effect_flows: number;
  boundaries: number;
  entities: number;
}

export interface CodeStats {
  total_files: number;
  total_lines: number;
  total_size: number;
  file_types: Record<string, number>;
}

export interface ArtifactStatsData {
  pipeline: PipelineStatus;
  briefs: BriefStats;
  contracts: ContractStats;
  ir: IRStats;
  code: CodeStats;
}

@Component({
  selector: 'app-artifacts-stats-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="dashboard-card">
      <h2 class="card-title">📊 Artifacts</h2>
      <div class="artifact-grid">

        <!-- Column 1: Briefs -->
        <div class="artifact-col" [class.done]="isDone('brief')">
          <div class="artifact-header">
            <span class="artifact-icon" [class.done]="isDone('brief')">📝</span>
            <span class="artifact-name">Briefs</span>
          </div>
          @if (!isDone('brief')) {
            <p class="artifact-empty">Chưa xử lý</p>
          } @else {
            <div class="artifact-details">
              <div class="detail-row">
                <span class="detail-label">Số lượng</span>
                <span class="detail-value">{{ data.briefs.count }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Trạng thái</span>
                <span class="detail-value"><span [class]="'status-badge status-' + data.briefs.status">{{ data.briefs.status | uppercase }}</span></span>
              </div>
              @if (data.briefs.title) {
                <div class="detail-row">
                  <span class="detail-label">Tiêu đề</span>
                  <span class="detail-value truncate" [title]="data.briefs.title">{{ data.briefs.title }}</span>
                </div>
              }
              <div class="detail-row">
                <span class="detail-label">Số từ</span>
                <span class="detail-value">{{ data.briefs.word_count | number }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Làm rõ</span>
                <span class="detail-value">{{ data.briefs.clarification_count }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Thay đổi</span>
                <span class="detail-value">{{ data.briefs.change_count }}</span>
              </div>
            </div>
          }
        </div>

        <!-- Column 2: Contracts -->
        <div class="artifact-col" [class.done]="isDone('contract')">
          <div class="artifact-header">
            <span class="artifact-icon" [class.done]="isDone('contract')">📋</span>
            <span class="artifact-name">Contracts</span>
          </div>
          @if (!isDone('contract')) {
            <p class="artifact-empty">Chưa xử lý</p>
          } @else {
            <div class="artifact-details">
              <div class="detail-row">
                <span class="detail-label">Tổng số</span>
                <span class="detail-value">{{ data.contracts.count }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Entities</span>
                <span class="detail-value">{{ data.contracts.total_entities }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Commands</span>
                <span class="detail-value">{{ data.contracts.total_commands }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Queries</span>
                <span class="detail-value">{{ data.contracts.total_queries }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Events</span>
                <span class="detail-value">{{ data.contracts.total_events }}</span>
              </div>
              @for (cat of categories(); track cat.key) {
                <div class="detail-row detail-row-sub">
                  <span class="detail-label">{{ cat.key }}</span>
                  <span class="detail-value">
                    <span class="dot" [class]="cat.val.status === 'valid' || cat.val.status === 'completed' ? 'dot-green' : 'dot-gray'"></span>
                    {{ cat.val.status | titlecase }}
                  </span>
                </div>
              }
            </div>
          }
        </div>

        <!-- Column 3: IR -->
        <div class="artifact-col" [class.done]="isDone('ir')">
          <div class="artifact-header">
            <span class="artifact-icon" [class.done]="isDone('ir')">🔗</span>
            <span class="artifact-name">IR</span>
          </div>
          @if (!isDone('ir')) {
            <p class="artifact-empty">Chưa xử lý</p>
          } @else {
            <div class="artifact-details">
              <div class="detail-row">
                <span class="detail-label">Operations</span>
                <span class="detail-value">{{ data.ir.operations }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Data Flows</span>
                <span class="detail-value">{{ data.ir.data_flows }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Effect Flows</span>
                <span class="detail-value">{{ data.ir.effect_flows }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Boundaries</span>
                <span class="detail-value">{{ data.ir.boundaries }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Entities (IR)</span>
                <span class="detail-value">{{ data.ir.entities }}</span>
              </div>
            </div>
          }
        </div>

        <!-- Column 4: Code -->
        <div class="artifact-col" [class.done]="isDone('code')">
          <div class="artifact-header">
            <span class="artifact-icon" [class.done]="isDone('code')">💻</span>
            <span class="artifact-name">Code</span>
          </div>
          @if (!isDone('code')) {
            <p class="artifact-empty">Chưa xử lý</p>
          } @else {
            <div class="artifact-details">
              <div class="detail-row">
                <span class="detail-label">File sinh ra</span>
                <span class="detail-value">{{ data.code.total_files }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Dòng code</span>
                <span class="detail-value">{{ data.code.total_lines | number }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Dung lượng</span>
                <span class="detail-value">{{ formatSize(data.code.total_size) }}</span>
              </div>
              @for (ft of fileTypes(); track ft.key) {
                <div class="detail-row detail-row-sub">
                  <span class="detail-label"><span class="dot dot-gray"></span> .{{ ft.key || '?' }}</span>
                  <span class="detail-value">{{ ft.val }}</span>
                </div>
              }
            </div>
          }
        </div>

      </div>
    </div>
  `,
  styles: [`
    .dashboard-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      padding: 24px;
    }

    .card-title {
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 20px 0;
    }

    .artifact-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
    }

    .artifact-col {
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      padding: 16px;
      display: flex;
      flex-direction: column;
      opacity: 0.5;
      transition: opacity 0.3s;
    }

    .artifact-col.done {
      opacity: 1;
      border-color: rgba(63, 185, 80, 0.3);
    }

    .artifact-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border-subtle);
    }

    .artifact-icon {
      font-size: 1.2rem;
      filter: grayscale(1);
      opacity: 0.4;
      transition: all 0.3s;
    }

    .artifact-icon.done {
      filter: grayscale(0);
      opacity: 1;
    }

    .artifact-name {
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--text-primary);
    }

    .artifact-empty {
      font-size: 0.75rem;
      color: var(--text-tertiary);
      text-align: center;
      padding: 24px 0;
      margin: 0;
      font-style: italic;
    }

    .artifact-details {
      display: flex;
      flex-direction: column;
      gap: 6px;
      flex: 1;
    }

    .detail-row {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      font-size: 0.75rem;
    }

    .detail-row-sub {
      margin-left: 4px;
      border-left: 2px solid var(--border-subtle);
      padding-left: 8px;
    }

    .detail-label {
      color: var(--text-tertiary);
    }

    .detail-value {
      color: var(--text-primary);
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.7rem;
      text-align: right;
    }

    .truncate {
      max-width: 120px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      display: inline-block;
    }

    .status-badge {
      display: inline-block;
      padding: 1px 6px;
      border-radius: 3px;
      font-size: 0.65rem;
      font-weight: 600;
    }

    .status-draft {
      background: rgba(255, 203, 96, 0.15);
      color: #ffcb60;
    }

    .status-analyzed {
      background: rgba(100, 181, 246, 0.15);
      color: #64b5f6;
    }

    .status-clarified {
      background: rgba(129, 140, 248, 0.15);
      color: #818cf0;
    }

    .status-frozen {
      background: rgba(63, 185, 80, 0.15);
      color: var(--accent-success);
    }

    .dot {
      display: inline-block;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      margin-right: 4px;
      vertical-align: middle;
    }

    .dot-green {
      background: var(--accent-success);
    }

    .dot-gray {
      background: var(--text-tertiary);
    }
  `]
})
export class ArtifactsStatsCardComponent {
  @Input() data: ArtifactStatsData = {
    pipeline: { brief: 'none', contract: 'none', ir: 'none', code: 'none' },
    briefs: { count: 0, status: '', title: '', word_count: 0, clarification_count: 0, change_count: 0, updated_at: '', types: {} },
    contracts: { count: 0, categories: {}, total_entities: 0, total_commands: 0, total_queries: 0, total_events: 0 },
    ir: { operations: 0, data_flows: 0, effect_flows: 0, boundaries: 0, entities: 0 },
    code: { total_files: 0, total_lines: 0, total_size: 0, file_types: {} },
  };

  isDone(stage: 'brief' | 'contract' | 'ir' | 'code'): boolean {
    const val = this.data.pipeline[stage];
    return val !== 'none' && val !== 'pending' && val !== '';
  }

  /** Convert categories object to key-value array for template iteration */
  categories(): Array<{ key: string; val: { status: string; updated_at: string } }> {
    return Object.entries(this.data.contracts.categories || []).map(([key, val]) => ({
      key,
      val: val as any,
    }));
  }

  /** Convert file_types object to key-value array */
  fileTypes(): Array<{ key: string; val: number }> {
    return Object.entries(this.data.code.file_types || [])
      .map(([key, val]) => ({ key, val: val as number }))
      .sort((a, b) => b.val - a.val);
  }

  formatSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }
}
