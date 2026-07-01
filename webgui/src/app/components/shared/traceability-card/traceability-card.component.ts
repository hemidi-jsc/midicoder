/**
 * Traceability Card — hiển thị ma trận traceability và drift detection
 * giữa Brief Analysis và Contract YAML.
 */

import { Component, OnInit, NgZone, ApplicationRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../../core/api.service';
import { ContractGraphComponent } from '../contract-graph/contract-graph.component';

export interface TraceabilityData {
  trace_matrix: Record<string, Array<{
    trace_id: string;
    analysis_name: string | null;
    contract_id: string | null;
    status: 'matched' | 'orphan_analysis' | 'orphan_contract' | 'mismatch';
    description_similarity?: number;
  }>>;
  drifts: Array<{
    type: string;
    category: string;
    name: string;
    trace_id: string;
    severity: 'error' | 'warning';
    message: string;
  }>;
  summary: {
    total_analysis: number;
    total_contract: number;
    matched: number;
    orphan_analysis: number;
    orphan_contract: number;
    mismatched: number;
  };
  unmapped_analysis: Array<{ category: string; count: number }>;
  brief_coverage: {
    coverage_ratio: number;
    covered_count: number;
    uncovered_count: number;
    uncovered_items: Array<{ name: string; category: string }>;
  };
  health_score: number;
  graph?: {
    nodes: Array<{
      uid: string; label: string; category: string; status: string;
      fields?: Array<{ name: string; type: string; is_pk?: boolean; is_fk?: boolean }>;
      foreign_keys?: Array<{ field: string; target_entity: string; cardinality: string }>;
    }>;
    edges: Array<{ from: string; to: string; type: string; cardinality?: string }>;
  };
}

@Component({
  selector: 'app-traceability-card',
  standalone: true,
  imports: [CommonModule, ContractGraphComponent],
  template: `
    <div class="trace-card">
      <!-- Header -->
      <div class="trace-header">
        <div class="trace-title">
          <i class="fa-solid fa-link"></i>
          <span>Traceability — Brief → Contract</span>
        </div>
        <div class="trace-health" [class]="getHealthClass(data.health_score)">
          <i class="fa-solid {{ getHealthIcon() }}"></i>
          <span>{{ data.health_score }}%</span>
        </div>
      </div>

      <!-- Stats Grid -->
      <div class="trace-stats">
        <div class="stat-box">
          <div class="stat-value">{{ data.summary.total_analysis }}</div>
          <div class="stat-label">Analysis Items</div>
        </div>
        <div class="stat-box">
          <div class="stat-value">{{ data.summary.total_contract }}</div>
          <div class="stat-label">Contract Nodes</div>
        </div>
        <div class="stat-box matched">
          <div class="stat-value">{{ data.summary.matched }}</div>
          <div class="stat-label">Matched</div>
        </div>
        <div class="stat-box orphan">
          <div class="stat-value">{{ data.summary.orphan_analysis }}</div>
          <div class="stat-label">Thiếu trong Contract</div>
        </div>
        <div class="stat-box extra">
          <div class="stat-value">{{ data.summary.orphan_contract }}</div>
          <div class="stat-label">Không có Analysis</div>
        </div>
        <div class="stat-box mismatch" *ngIf="data.summary.mismatched > 0">
          <div class="stat-value">{{ data.summary.mismatched }}</div>
          <div class="stat-label">Lệch Description</div>
        </div>
      </div>

      <!-- Brief Coverage -->
      <div class="trace-coverage">
        <div class="coverage-label">
          <i class="fa-solid fa-file-lines"></i>
          <span>Brief Text Coverage:</span>
        </div>
        <div class="coverage-bar">
          <div class="coverage-fill" [style.width.%]="data.brief_coverage.coverage_ratio * 100"
               [class]="getCoverageColorClass(data.brief_coverage.coverage_ratio)"></div>
        </div>
        <div class="coverage-percent">{{ (data.brief_coverage.coverage_ratio * 100).toFixed(0) }}%</div>
      </div>

      <!-- p5.js Diagram -->
      <app-contract-graph [traceMatrix]="data.trace_matrix" [graph]="data.graph"></app-contract-graph>

      <!-- Drift List -->
      <div class="trace-drifts" *ngIf="data.drifts.length > 0">
        <div class="drift-title">
          <i class="fa-solid fa-triangle-exclamation"></i>
          <span>Drifts phát hiện ({{ data.drifts.length }})</span>
          <button class="drift-toggle" (click)="showDrifts = !showDrifts">
            <i class="fa-solid" [class]="showDrifts ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
          </button>
        </div>

        @if (showDrifts) {
          <div class="drift-list">
            @for (drift of data.drifts; track drift.trace_id + drift.name) {
              <div class="drift-item" [class]="drift.severity">
                <i class="fa-solid {{ getDriftIcon(drift.type) }}"></i>
                <span class="drift-category">{{ getCategoryLabel(drift.category) }}</span>
                <span class="drift-name">{{ drift.name }}</span>
                <span class="drift-message">{{ drift.message }}</span>
              </div>
            }
          </div>
        }
      </div>

      <!-- Unmapped Categories -->
      <div class="trace-unmapped" *ngIf="data.unmapped_analysis.length > 0">
        <div class="unmapped-title">
          <i class="fa-solid fa-layer-group"></i>
          <span>Analysis categories không có contract counterpart:</span>
        </div>
        <div class="unmapped-list">
          @for (u of data.unmapped_analysis; track u.category) {
            <span class="unmapped-tag">{{ u.category }} ({{ u.count }} items)</span>
          }
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="trace-actions" *ngIf="data.drifts.length > 0">
        <button class="btn-fix" (click)="onFixDrifts()">
          <i class="fa-solid fa-wrench"></i>
          Sửa hợp đồng
        </button>
        <button class="btn-retry" (click)="onRefresh()">
          <i class="fa-solid fa-rotate-right"></i>
          Refresh
        </button>
      </div>
    </div>
  `,
  styles: [`
    .trace-card {
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 10px;
      padding: 16px;
      margin-top: 12px;
      margin-bottom: 24px;
    }

    .trace-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 14px;
    }
    .trace-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 15px;
      font-weight: 600;
      color: #e6edf3;
    }
    .trace-title i {
      color: #58a6ff;
    }

    .trace-health {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 14px;
      font-weight: 700;
    }
    .trace-health.health-excellent {
      background: rgba(46,204,113,0.15);
      color: #2ecc71;
      border: 1px solid rgba(46,204,113,0.3);
    }
    .trace-health.health-good {
      background: rgba(46,204,113,0.1);
      color: #58d68d;
      border: 1px solid rgba(46,204,113,0.2);
    }
    .trace-health.health-warning {
      background: rgba(241,196,15,0.15);
      color: #f1c40f;
      border: 1px solid rgba(241,196,15,0.3);
    }
    .trace-health.health-error {
      background: rgba(231,76,60,0.15);
      color: #e74c3c;
      border: 1px solid rgba(231,76,60,0.3);
    }

    /* Stats Grid */
    .trace-stats {
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 8px;
      margin-bottom: 14px;
    }
    .stat-box {
      background: #0d1117;
      border: 1px solid #21262d;
      border-radius: 8px;
      padding: 10px 8px;
      text-align: center;
    }
    .stat-value {
      font-size: 22px;
      font-weight: 700;
      color: #e6edf3;
    }
    .stat-label {
      font-size: 10px;
      color: #8b949e;
      margin-top: 2px;
    }
    .stat-box.matched .stat-value { color: #2ecc71; }
    .stat-box.orphan .stat-value { color: #e74c3c; }
    .stat-box.extra .stat-value { color: #f1c40f; }
    .stat-box.mismatch .stat-value { color: #e67e22; }

    /* Brief Coverage */
    .trace-coverage {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 12px;
      padding: 8px 12px;
      background: #0d1117;
      border-radius: 8px;
    }
    .coverage-label {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: #8b949e;
      white-space: nowrap;
    }
    .coverage-label i { color: #58a6ff; }
    .coverage-bar {
      flex: 1;
      height: 8px;
      background: #21262d;
      border-radius: 4px;
      overflow: hidden;
    }
    .coverage-fill {
      height: 100%;
      border-radius: 4px;
      transition: width 0.5s ease;
    }
    .coverage-fill.coverage-high { background: #2ecc71; }
    .coverage-fill.coverage-mid { background: #f1c40f; }
    .coverage-fill.coverage-low { background: #e74c3c; }
    .coverage-percent {
      font-size: 13px;
      font-weight: 600;
      color: #c9d1d9;
      min-width: 40px;
      text-align: right;
    }

    /* Drifts */
    .trace-drifts {
      margin-top: 12px;
      border-top: 1px solid #21262d;
      padding-top: 10px;
    }
    .drift-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      font-weight: 600;
      color: #e74c3c;
      margin-bottom: 8px;
    }
    .drift-toggle {
      margin-left: auto;
      background: none;
      border: none;
      color: #8b949e;
      cursor: pointer;
      font-size: 12px;
    }
    .drift-list {
      max-height: 200px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .drift-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 10px;
      border-radius: 6px;
      font-size: 12px;
    }
    .drift-item.error {
      background: rgba(231,76,60,0.1);
      border-left: 3px solid #e74c3c;
      color: #e74c3c;
    }
    .drift-item.warning {
      background: rgba(241,196,15,0.1);
      border-left: 3px solid #f1c40f;
      color: #f1c40f;
    }
    .drift-category {
      font-weight: 600;
      min-width: 80px;
    }
    .drift-name {
      font-weight: 500;
      color: #e6edf3;
      min-width: 120px;
    }
    .drift-message {
      color: #8b949e;
      flex: 1;
    }

    /* Unmapped */
    .trace-unmapped {
      margin-top: 10px;
      padding: 8px 12px;
      background: rgba(139,148,158,0.05);
      border-radius: 8px;
      font-size: 12px;
      color: #8b949e;
    }
    .unmapped-title {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 6px;
    }
    .unmapped-list {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }
    .unmapped-tag {
      padding: 3px 10px;
      background: #21262d;
      border-radius: 12px;
      font-size: 11px;
      color: #c9d1d9;
    }

    /* Actions */
    .trace-actions {
      display: flex;
      gap: 10px;
      margin-top: 14px;
      padding-top: 12px;
      border-top: 1px solid #21262d;
    }
    .btn-fix {
      padding: 8px 20px;
      background: linear-gradient(135deg, #e74c3c, #e67e22);
      border: none;
      border-radius: 6px;
      color: white;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: opacity 0.2s;
    }
    .btn-fix:hover { opacity: 0.85; }
    .btn-retry {
      padding: 8px 16px;
      background: #21262d;
      border: 1px solid #30363d;
      border-radius: 6px;
      color: #c9d1d9;
      font-size: 13px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .btn-retry:hover { background: #30363d; }

    @media (max-width: 768px) {
      .trace-stats {
        grid-template-columns: repeat(3, 1fr);
      }
    }
  `]
})
export class TraceabilityCardComponent implements OnInit {
  data: TraceabilityData = {
    trace_matrix: {},
    drifts: [],
    summary: { total_analysis: 0, total_contract: 0, matched: 0, orphan_analysis: 0, orphan_contract: 0, mismatched: 0 },
    unmapped_analysis: [],
    brief_coverage: { coverage_ratio: 0, covered_count: 0, uncovered_count: 0, uncovered_items: [] },
    health_score: 0,
  };

  contractArtifacts: Record<string, any> = {};
  showDrifts = true;
  loading = false;

  constructor(
    private api: ApiService,
    private ngZone: NgZone,
    private appRef: ApplicationRef,
  ) {}

  ngOnInit(): void {
    this.load();
  }

  async load(): Promise<void> {
    this.loading = true;
    try {
      const resp = await this.api.getTraceability();
      if (resp.success && resp.data) {
        this.ngZone.run(() => {
          this.data = JSON.parse(JSON.stringify(resp.data));
          this.appRef.tick();
        });
      }
    } catch (e) {
      console.error('[Traceability] Failed to load:', e);
    }
    this.loading = false;
  }

  getHealthClass(score: number): string {
    if (score >= 90) return 'trace-health health-excellent';
    if (score >= 70) return 'trace-health health-good';
    if (score >= 50) return 'trace-health health-warning';
    return 'trace-health health-error';
  }

  getHealthIcon(): string {
    if (this.data.health_score >= 90) return 'fa-circle-check';
    if (this.data.health_score >= 70) return 'fa-face-smile';
    if (this.data.health_score >= 50) return 'fa-face-meh';
    return 'fa-face-frown';
  }

  getCoverageColorClass(ratio: number): string {
    if (ratio >= 0.8) return 'coverage-high';
    if (ratio >= 0.5) return 'coverage-mid';
    return 'coverage-low';
  }

  getDriftIcon(type: string): string {
    switch (type) {
      case 'orphan_analysis': return 'fa-circle-xmark';
      case 'orphan_contract': return 'fa-circle-plus';
      case 'description_mismatch': return 'fa-circle-exclamation';
      default: return 'fa-triangle-exclamation';
    }
  }

  getCategoryLabel(cat: string): string {
    const labels: Record<string, string> = {
      entities: 'Thực thể',
      commands: 'Lệnh',
      queries: 'Truy vấn',
      events: 'Sự kiện',
      workflows: 'Quy trình',
      value_objects: 'Giá trị',
      guards: 'Bảo vệ',
      roles: 'Vai trò',
      ui_components: 'UI',
    };
    return labels[cat] || cat;
  }

  onFixDrifts(): void {
    // Emit event to parent to handle fix
    const errorDrifts = this.data.drifts.filter(d => d.severity === 'error');
    const categories = [...new Set(errorDrifts.map(d => d.category))];
    console.log('[Traceability] Fix drifts for categories:', categories);
    // The parent component will handle re-generation
    window.dispatchEvent(new CustomEvent('midicoder:fix-contract-drifts', {
      detail: { categories, drifts: this.data.drifts }
    }));
  }

  onRefresh(): void {
    this.load();
  }
}
