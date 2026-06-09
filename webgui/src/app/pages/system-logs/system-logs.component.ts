/**
 * System Logs Page
 * Xem nhật ký hệ thống và báo cáo lỗi
 */

import { Component, inject, OnInit, ViewChild, ElementRef, AfterViewInit, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../core/api.service';

@Component({
  selector: 'app-system-logs',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="container mx-auto px-6 py-8">
      <!-- Header -->
      <div class="mb-6">
        <h1 class="text-2xl font-bold">Nhật ký hệ thống</h1>
        <p class="text-text-secondary mt-1">Xem log hệ thống và báo cáo lỗi</p>
      </div>

      <!-- Status Messages -->
      @if (successMessage) {
        <div class="mb-4 p-3 rounded border" style="background: rgba(63, 185, 80, 0.1); border-color: var(--accent-success); color: var(--accent-success)">
          {{ successMessage }}
        </div>
      }
      @if (errorMessage) {
        <div class="mb-4 p-3 rounded border" style="background: rgba(242, 83, 83, 0.1); border-color: var(--accent-error); color: var(--accent-error)">
          {{ errorMessage }}
        </div>
      }

      <!-- Log Viewer Card -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold">Log Viewer</h2>
          <div class="flex items-center space-x-3">
            <!-- File Selector -->
            <select
              [(ngModel)]="selectedFile"
              (change)="onFileChange()"
              class="bg-bg-secondary border border-border-primary rounded p-2 text-sm text-text-primary focus:outline-none focus:border-accent-primary"
            >
              @for (f of logFiles; track f.filename) {
                <option [value]="f.filename">{{ f.filename }}</option>
              }
            </select>
            <!-- Reload Button -->
            <button
              (click)="loadLogs()"
              class="btn btn-secondary text-sm"
              [disabled]="loadingLogs"
            >
              {{ loadingLogs ? 'Đang tải...' : 'Nạp lại' }}
            </button>
          </div>
        </div>

        <!-- Search / Filter -->
        <div class="mb-3">
          <input
            [(ngModel)]="searchFilter"
            type="text"
            placeholder="Lọc log (nhập từ khóa...)"
            class="w-full bg-bg-secondary border border-border-primary rounded p-2 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-accent-primary"
          />
        </div>

        <!-- Log Content -->
        <div class="relative">
          @if (loadingLogs) {
            <div class="flex items-center justify-center h-[400px] text-text-tertiary">
              Đang tải log...
            </div>
          } @else {
            <div
              #logContainer
              class="log-viewer overflow-auto rounded"
              style="background: #1e1e1e; border: 1px solid var(--border-subtle); max-height: 600px;"
            >
              @if (filteredLines.length === 0) {
                <div class="p-4 text-text-tertiary" style="font-family: 'Courier New', Courier, monospace">
                  {{ logLines.length === 0 ? 'Không có log hoặc không thể kết nối đến hệ thống' : 'Không tìm thấy log phù hợp với bộ lọc' }}
                </div>
              } @else {
                @for (line of filteredLines; track $index) {
                  <div class="log-line" [class]="getLogLineClass(line)">
                    {{ line }}
                  </div>
                }
              }
            </div>
          }
        </div>

        <!-- Footer info -->
        @if (logLines.length > 0) {
          <div class="mt-2 text-xs text-text-tertiary flex justify-between">
            <span>{{ logLines.length }} dòng ({{ filteredLines.length }} sau khi lọc)</span>
            <span>Tập tin: {{ selectedFile }}</span>
          </div>
        }
      </div>

      <!-- Report Bug Card -->
      <div class="card mt-6">
        <h2 class="text-lg font-semibold mb-3">Báo cáo lỗi</h2>
        <p class="text-sm text-text-secondary mb-4">
          Mô tả lỗi bạn gặp phải. Khi nhấn "Gửi báo cáo lỗi", nội dung log + mô tả sẽ được sao chép vào bảng tạm,
          sau đó mở trang tạo issue mới trên GitHub — bạn chỉ cần dán (Ctrl+V) vào ô mô tả.
        </p>

        <div class="mb-4">
          <label class="block text-sm font-medium text-text-secondary mb-1">
            Mô tả lỗi <span class="text-accent-error">*</span>
          </label>
          <textarea
            [(ngModel)]="bugDescription"
            placeholder="Mô tả chi tiết lỗi bạn gặp phải, các bước để tái hiện..."
            rows="5"
            class="w-full bg-bg-secondary border border-border-primary rounded p-3 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-accent-primary resize-vertical"
          ></textarea>
        </div>

        <div class="flex items-center space-x-3">
          <button
            (click)="submitBugReport()"
            class="btn btn-primary"
            [disabled]="!bugDescription.trim()"
          >
            Gửi báo cáo lỗi
          </button>
          <span class="text-xs text-text-tertiary">
            Sao chép log → mở GitHub Issue → dán (Ctrl+V)
          </span>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .log-viewer {
        font-family: 'Courier New', Courier, monospace;
        font-size: 13px;
        line-height: 1.5;
        color: #d4d4d4;
      }

      .log-line {
        padding: 1px 12px;
        white-space: pre-wrap;
        word-break: break-all;
      }

      .log-line:hover {
        background: rgba(255, 255, 255, 0.05);
      }

      .log-error {
        color: #f44336;
      }

      .log-warning {
        color: #ffc107;
      }
    `,
  ],
})
export class SystemLogsComponent implements OnInit, AfterViewInit {
  private api = inject(ApiService);
  private zone = inject(NgZone);

  @ViewChild('logContainer') logContainer!: ElementRef;

  // Log viewer state
  logFiles: { filename: string; path: string; size: number; modified: string }[] = [];
  selectedFile = '';
  logLines: string[] = [];
  searchFilter = '';
  loadingFiles = false;
  loadingLogs = false;

  // Bug report state
  bugDescription = '';
  successMessage = '';
  errorMessage = '';

  /** Filtered log lines based on search input */
  get filteredLines(): string[] {
    if (!this.searchFilter.trim()) {
      return this.logLines;
    }
    const lower = this.searchFilter.toLowerCase();
    return this.logLines.filter((line) => line.toLowerCase().includes(lower));
  }

  async ngOnInit(): Promise<void> {
    await this.loadLogFiles();
  }

  ngAfterViewInit(): void {
    // Auto-scroll after initial load
  }

  async loadLogFiles(): Promise<void> {
    this.loadingFiles = true;
    try {
      const result = await this.api.getLogFiles();
      this.zone.run(() => {
        if (result.success && result.data) {
          this.logFiles = result.data.files || [];
          if (this.logFiles.length > 0 && !this.selectedFile) {
            this.selectedFile = this.logFiles[0].filename;
            this.loadLogs();
          }
        } else {
          this.errorMessage = result.message || 'Không thể tải danh sách log';
        }
      });
    } catch (e) {
      console.error('Failed to load log files:', e);
    } finally {
      this.zone.run(() => { this.loadingFiles = false; });
    }
  }

  async loadLogs(): Promise<void> {
    if (!this.selectedFile) return;

    this.loadingLogs = true;
    this.errorMessage = '';
    this.successMessage = '';

    try {
      const result = await this.api.getLogs(this.selectedFile, 500);
      this.zone.run(() => {
        if (result.success && result.data) {
          this.logLines = result.data.lines || [];
          this.searchFilter = '';
          setTimeout(() => this.scrollToBottom(), 50);
        } else {
          this.errorMessage = result.message || 'Không thể tải log';
          this.logLines = [];
        }
      });
    } catch (e) {
      console.error('Failed to load logs:', e);
      this.zone.run(() => {
        this.errorMessage = 'Lỗi khi tải log: ' + (e as Error).message;
        this.logLines = [];
      });
    } finally {
      this.zone.run(() => { this.loadingLogs = false; });
    }
  }

  onFileChange(): void {
    this.loadLogs();
  }

  /**
   * Return CSS class for log line based on content keywords
   */
  getLogLineClass(line: string): string {
    const lower = line.toLowerCase();
    if (lower.includes('error') || lower.includes('exception') || lower.includes('fatal') || lower.includes('traceback')) {
      return 'log-line log-error';
    }
    if (lower.includes('warning') || lower.includes('warn')) {
      return 'log-line log-warning';
    }
    return 'log-line';
  }

  /**
   * Scroll log container to the bottom
   */
  private scrollToBottom(): void {
    if (this.logContainer) {
      const el = this.logContainer.nativeElement;
      el.scrollTop = el.scrollHeight;
    }
  }

  /**
   * Submit bug report: copy logs + description to clipboard, open GitHub issue
   * URL chỉ chứa tiêu đề — nội dung log được copy vào clipboard để tránh URL quá dài.
   */
  submitBugReport(): void {
    if (!this.bugDescription.trim()) {
      this.errorMessage = 'Vui lòng mô tả lỗi trước khi gửi báo cáo';
      return;
    }

    // Build the full body for the GitHub issue
    let logContent = this.filteredLines.length > 0 ? this.filteredLines.join('\n') : this.logLines.join('\n');

    // Limit log content to last 200 lines
    const lines = logContent.split('\n');
    if (lines.length > 200) {
      logContent = '...(truncated - showing last 200 lines)\n' + lines.slice(-200).join('\n');
    }

    const body = `## Mô tả lỗi

${this.bugDescription}

## Log hệ thống

\`\`\`
${logContent}
\`\`\`

## Thông tin

- Tập tin log: ${this.selectedFile}
- Số dòng log: ${this.logLines.length}
- Thời gian: ${new Date().toISOString()}`;

    // Copy full body to clipboard first
    navigator.clipboard.writeText(body).then(() => {
      // Open GitHub issue with a short body instructing user to paste
      const pasteBody = encodeURIComponent(
        `## Mô tả lỗi

_(Nội dung chi tiết + log đã được sao chép vào bảng tạm — hãy nhấn Ctrl+V để dán)_

## Log hệ thống

_(Đang chờ dán từ bảng tạm — nhấn Ctrl+V)_

---
- Tập tin log: ${this.selectedFile}
- Thời gian: ${new Date().toISOString()}`
      );
      const title = encodeURIComponent(`Báo cáo lỗi: ${this.bugDescription.trim().substring(0, 80)}`);
      const url = `https://github.com/hemidi-jsc/midicoder/issues/new?labels=bug&title=${title}&body=${pasteBody}`;
      window.open(url, '_blank');
      this.successMessage = '✅ Nội dung báo cáo đã được sao chép — hãy dán (Ctrl+V) vào ô mô tả issue trên GitHub';
    }).catch(() => {
      // Fallback: open without clipboard
      const title = encodeURIComponent(`Báo cáo lỗi: ${this.bugDescription.trim().substring(0, 80)}`);
      const url = `https://github.com/hemidi-jsc/midicoder/issues/new?labels=bug&title=${title}`;
      window.open(url, '_blank');
      this.errorMessage = 'Không thể sao chép nội dung — vui lòng mô tả lỗi thủ công trên GitHub';
    });
  }
}
