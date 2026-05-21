# coding: utf-8
"""
Mô-đun Angular emitter cho Report & Document Generator (CP34).

Emit code Angular cho:
- ReportListComponent: Danh sách reports có thể generate
- ReportViewerComponent: Xem report (PDF embed, Excel table)
- BatchStatusComponent: Progress indicator cho batch job

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path

from midicoder.emitters.core.cp34_reporting.models import (
    ReportCollection,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class AngularReportEmitter:
    """Emitter sinh code Angular cho report viewer components."""

    def emit(
        self, collection: ReportCollection, output_dir: Path | None = None
    ) -> list[dict[str, str]]:
        """
        Generate toàn bộ Angular components từ ReportCollection.

        Args:
            collection: ReportCollection chứa report specs
            output_dir: Output directory (optional)

        Returns:
            List của {path, content} cho mỗi file
        """
        if not collection.reports:
            EM.raise_error(ErrorCode.CP34_REPORT_SPEC_INVALID, reason="Collection trống")

        result: list[dict[str, str]] = []
        result.extend(self.generate_report_list(collection))
        result.extend(self.generate_report_viewer(collection))
        result.extend(self.generate_batch_status(collection))
        return result

    def generate_report_list(self, collection: ReportCollection) -> list[dict[str, str]]:
        """Sinh ReportListComponent."""
        report_names = [r.name for r in collection.reports]
        report_ids = [r.id for r in collection.reports]

        ts_code = f'''// Report List Component — Hiển thị danh sách reports có thể generate.
// CP34: Report & Document Generator (Angular)

import {{ Component, OnInit }} from "@angular/core";
import {{ CommonModule }} from "@angular/common";
import {{ HttpClient }} from "@angular/common/http";
import {{ FormBuilder, FormGroup }} from "@angular/forms";

export interface ReportMeta {{
  id: string;
  name: string;
  entity: string;
  format: string;
  layout: string;
  description: string;
}}

@Component({{
  selector: "app-report-list",
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="report-list">
      <h2>Danh sách Báo cáo</h2>
      <div class="report-grid">
        <div
          *ngFor="let report of reports"
          class="report-card"
          (click)="onSelect(report)"
        >
          <h3>{{{{"report.name"}}}}</h3>
          <p class="entity">{{{{"report.entity"}}}}</p>
          <span class="format-badge">{{{{"report.format"}}}}</span>
          <p class="description">{{{{"report.description"}}}}</p>
          <button (click)="generateReport(report.id, $event)">Generate</button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host {{ display: block; padding: 20px; }}
    .report-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 16px;
    }}
    .report-card {{
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 16px;
      cursor: pointer;
      transition: box-shadow 0.2s;
    }}
    .report-card:hover {{ box-shadow: 0 2px 8px rgba(0,0,0,0.15); }}
    .format-badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      background: #4CAF50;
      color: white;
      font-size: 12px;
    }}
    .entity {{ color: #666; margin: 4px 0; }}
    .description {{ color: #888; font-size: 14px; }}
    button {{
      margin-top: 8px;
      padding: 8px 16px;
      background: #4CAF50;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }}
  `]
}})
export class ReportListComponent implements OnInit {{
  reports: ReportMeta[] = [];
  selectedReport: ReportMeta | null = null;

  constructor(
    private http: HttpClient,
    private fb: FormBuilder
  ) {{}}

  ngOnInit(): void {{
    this.loadReports();
  }}

  loadReports(): void {{
    this.http.get<ReportMeta[]>("/api/reports").subscribe({{
      next: (data) => {{ this.reports = data; }},
      error: (err) => {{ console.error("Failed to load reports:", err); }},
    }});
  }}

  onSelect(report: ReportMeta): void {{
    this.selectedReport = report;
  }}

  generateReport(reportId: string, event?: Event): void {{
    event?.stopPropagation();
    this.http.post(`/api/reports/${{{{reportId}}}}/generate`, {{}}).subscribe({{
      next: (res: any) => {{
        window.open(res.file_url, "_blank");
      }},
      error: (err) => {{ console.error("Failed to generate report:", err); }},
    }});
  }}

  // Danh sách reports đã định nghĩa
  REPORT_NAMES = {str(report_names).replace("'", '"')};
  REPORT_IDS = {str(report_ids).replace("'", '"')};
}}
'''
        return [{"path": "src/app/reports/report-list.component.ts", "content": ts_code}]

    def generate_report_viewer(self, collection: ReportCollection) -> list[dict[str, str]]:
        """Sinh ReportViewerComponent."""
        code = '''// Report Viewer Component — Hiển thị report trong browser.
// CP34: Report & Document Generator (Angular)
// Hỗ trợ: PDF embed (iframe), Excel table.

import { Component, Input, OnInit } from "@angular/core";
import { CommonModule } from "@angular/common";
import { HttpClient } from "@angular/common/http";

export interface ViewerConfig {
  reportId: string;
  format: "pdf" | "xlsx" | "csv";
  autoGenerate?: boolean;
}

@Component({
  selector: "app-report-viewer",
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="report-viewer">
      <div class="viewer-header">
        <h2>{{ title }}</h2>
        <div class="actions">
          <button (click)="regenerate()">Tạo lại</button>
          <button (click)="download()">Tải xuống</button>
        </div>
      </div>

      <ng-container [ngSwitch]="config?.format">
        <!-- PDF Viewer -->
        <iframe
          *ngSwitchCase="'pdf'"
          [src]="pdfUrl"
          class="pdf-frame"
        ></iframe>

        <!-- Excel/CSV — Download only -->
        <div *ngSwitchDefault class="download-prompt">
          <p>Báo cáo sẽ được tải xuống dưới định dạng {{ config?.format }}.</p>
          <button (click)="download()">Tải xuống</button>
        </div>
      </ng-container>

      <div *ngIf="loading" class="loading">
        <p>Đang tạo báo cáo...</p>
      </div>

      <div *ngIf="error" class="error">
        <p>{{ error }}</p>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; padding: 20px; }
    .viewer-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
    .pdf-frame {
      width: 100%;
      height: 80vh;
      border: 1px solid #ddd;
      border-radius: 4px;
    }
    .loading { text-align: center; padding: 40px; color: #666; }
    .error { text-align: center; padding: 40px; color: red; }
    button {
      padding: 8px 16px;
      background: #4CAF50;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      margin-left: 8px;
    }
  `]
})
export class ReportViewerComponent implements OnInit {
  @Input() config: ViewerConfig | null = null;
  @Input() title: string = "Xem Báo cáo";

  loading = false;
  error: string = "";
  pdfUrl: string = "";
  downloadUrl: string = "";

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    if (this.config?.autoGenerate !== false) {
      this.generate();
    }
  }

  generate(): void {
    if (!this.config?.reportId) return;
    this.loading = true;
    this.error = "";

    this.http.post(`/api/reports/${this.config.reportId}/generate`, {}).subscribe({
      next: (res: any) => {
        this.loading = false;
        this.downloadUrl = res.file_url;
        if (this.config?.format === "pdf") {
          this.pdfUrl = res.file_url;
        }
      },
      error: (err) => {
        this.loading = false;
        this.error = `Tạo báo cáo thất bại: ${err.message}`;
      },
    });
  }

  regenerate(): void {
    this.generate();
  }

  download(): void {
    if (this.downloadUrl) {
      window.open(this.downloadUrl, "_blank");
    }
  }
}
'''
        return [{"path": "src/app/reports/report-viewer.component.ts", "content": code}]

    def generate_batch_status(self, collection: ReportCollection) -> list[dict[str, str]]:
        """Sinh BatchStatusComponent."""
        code = '''// Batch Status Component — Progress indicator cho batch job.
// CP34: Report & Document Generator (Angular)

import { Component, Input, OnInit, OnDestroy } from "@angular/core";
import { CommonModule } from "@angular/common";
import { HttpClient } from "@angular/common/http";
import { Subscription, interval } from "rxjs";
import { switchMap } from "rxjs/operators";

export interface BatchJobStatus {
  id: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  reportSpecIds: string[];
  resultUrls: string[];
  error: string;
}

@Component({
  selector: "app-batch-status",
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="batch-status">
      <h3>Trạng thái Batch Job</h3>
      <div class="status-badge" [ngClass]="job?.status">
        {{ getStatusLabel(job?.status) }}
      </div>

      <div *ngIf="job?.status === 'running'" class="progress">
        <div class="progress-bar" [style.width.%]="progressPercent"></div>
        <p>{{ completedCount }} / {{ totalCount }} báo cáo</p>
      </div>

      <div *ngIf="job?.status === 'completed'" class="results">
        <h4>Kết quả ({{ job.resultUrls.length }}):</h4>
        <ul>
          <li *ngFor="let url of job.resultUrls; let i = index">
            <a [href]="url" target="_blank">Báo cáo {{ i + 1 }}</a>
          </li>
        </ul>
      </div>

      <div *ngIf="job?.status === 'failed'" class="error">
        <p>{{ job.error }}</p>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; padding: 20px; }
    .status-badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 14px;
      font-weight: bold;
    }
    .status-badge.pending { background: #ff9800; color: white; }
    .status-badge.running { background: #2196f3; color: white; }
    .status-badge.completed { background: #4caf50; color: white; }
    .status-badge.failed { background: #f44336; color: white; }
    .status-badge.cancelled { background: #9e9e9e; color: white; }
    .progress { margin: 16px 0; }
    .progress-bar {
      height: 8px;
      background: #4caf50;
      border-radius: 4px;
      transition: width 0.3s;
    }
    .results ul { list-style: none; padding: 0; }
    .results li { padding: 4px 0; }
    .error { color: red; margin-top: 16px; }
  `]
})
export class BatchStatusComponent implements OnInit, OnDestroy {
  @Input() jobId: string = "";

  job: BatchJobStatus | null = null;
  private pollSubscription: Subscription | null = null;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.startPolling();
  }

  ngOnDestroy(): void {
    this.stopPolling();
  }

  startPolling(): void {
    this.pollSubscription = interval(3000).pipe(
      switchMap(() => this.http.get<BatchJobStatus>(`/api/reports/batch/${this.jobId}`))
    ).subscribe({
      next: (data) => {
        this.job = data;
        if (data.status === "completed" || data.status === "failed" || data.status === "cancelled") {
          this.stopPolling();
        }
      },
      error: (err) => {
        console.error("Failed to poll batch status:", err);
      },
    });
  }

  stopPolling(): void {
    if (this.pollSubscription) {
      this.pollSubscription.unsubscribe();
      this.pollSubscription = null;
    }
  }

  get progressPercent(): number {
    if (!this.job || this.job.status !== "running") return 0;
    if (this.totalCount === 0) return 0;
    return Math.round((this.completedCount / this.totalCount) * 100);
  }

  get completedCount(): number {
    return this.job?.resultUrls?.length || 0;
  }

  get totalCount(): number {
    return this.job?.reportSpecIds?.length || 0;
  }

  getStatusLabel(status?: string): string {
    const labels: Record<string, string> = {
      pending: "Đang chờ",
      running: "Đang chạy",
      completed: "Hoàn thành",
      failed: "Thất bại",
      cancelled: "Đã hủy",
    };
    return labels[status || ""] || "Không rõ";
  }
}
'''
        return [{"path": "src/app/reports/batch-status.component.ts", "content": code}]
