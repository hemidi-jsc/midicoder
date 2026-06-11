/**
 * System Logs Page
 * Xem nhật ký hệ thống và báo cáo lỗi
 */

import { Component, inject, OnInit, ViewChild, ElementRef, AfterViewInit, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { I18nPipe } from '../../core/i18n.pipe';
import { I18nService } from '../../core/i18n.service';
import { DOCS_BASE } from '../../core/app.constants';
import { ApiService } from '../../core/api.service';

@Component({
  selector: 'app-system-logs',
  standalone: true,
  imports: [CommonModule, FormsModule, I18nPipe],
  template: `
    <div class="py-8">
      <!-- Header -->
      <div class="mb-6">
        <div class="page-header-row">
          <h1 class="text-2xl font-bold">{{ 'logs.title' | i18n }}</h1>
          <a href="{{ docsUrl }}" target="_blank" rel="noopener" class="docs-link">{{ 'common.readGuide' | i18n }}</a>
        </div>
        <p class="text-text-secondary mt-1">{{ 'logs.subtitle' | i18n }}</p>
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
          <h2 class="text-lg font-semibold">{{ 'logs.viewer' | i18n }}</h2>
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
              {{ loadingLogs ? ('common.loading' | i18n) : ('logs.refresh' | i18n) }}
            </button>
          </div>
        </div>

        <!-- Search / Filter -->
        <div class="mb-3">
          <input
            [(ngModel)]="searchFilter"
            type="text"
            [placeholder]="'logs.filter' | i18n"
            class="w-full bg-bg-secondary border border-border-primary rounded p-2 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-accent-primary"
          />
        </div>

        <!-- Log Content -->
        <div class="relative">
          @if (loadingLogs) {
            <div class="flex items-center justify-center h-[400px] text-text-tertiary">
              {{ 'logs.loadingLogs' | i18n }}
            </div>
          } @else {
            <div
              #logContainer
              class="log-viewer overflow-auto rounded"
              style="background: #1e1e1e; border: 1px solid var(--border-subtle); max-height: 600px;"
            >
              @if (filteredLines.length === 0) {
                <div class="p-4 text-text-tertiary" style="font-family: 'Courier New', Courier, monospace">
                  {{ logLines.length === 0 ? ('logs.noLogs' | i18n) : ('logs.noMatch' | i18n) }}
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
            <span>{{ 'logs.linesCount' | i18n:{count: logLines.length, filtered: filteredLines.length} }}</span>
            <span>{{ 'logs.file' | i18n }} {{ selectedFile }}</span>
          </div>
        }
      </div>

      <!-- Report Bug Card -->
      <div class="card mt-6">
        <h2 class="text-lg font-semibold mb-3">{{ 'logs.bugReport' | i18n }}</h2>
        <p class="text-sm text-text-secondary mb-4">
          {{ 'logs.bugDesc' | i18n }}
        </p>

        <div class="mb-4">
          <label class="block text-sm font-medium text-text-secondary mb-1">
            {{ 'logs.bugTitle' | i18n }}<span class="text-accent-error">*</span>
          </label>
          <textarea
            [(ngModel)]="bugDescription"
            [placeholder]="'logs.bugPlaceholder' | i18n"
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
            {{ 'logs.submitReport' | i18n }}
          </button>
          <span class="text-xs text-text-tertiary">
            {{ 'logs.reportTip' | i18n }}
          </span>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      /* Page header docs link */
      .page-header-row {
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .docs-link {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        color: var(--accent-primary, #fc6767);
        text-decoration: none;
        letter-spacing: 0.04em;
        transition: color 0.2s;
      }

      .docs-link:hover {
        text-decoration: underline;
      }

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
  private i18n = inject(I18nService);

  @ViewChild('logContainer') logContainer!: ElementRef;

  readonly docsUrl = `${DOCS_BASE}/logs`;

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
          this.errorMessage = result.message || this.i18n.t('logs.listError');
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
          this.errorMessage = result.message || this.i18n.t('logs.loadError');
          this.logLines = [];
        }
      });
    } catch (e) {
      console.error('Failed to load logs:', e);
      this.zone.run(() => {
        this.errorMessage = this.i18n.t('logs.loadErrorPrefix') + ' ' + (e as Error).message;
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
      this.errorMessage = this.i18n.t('logs.describeFirst');
      return;
    }

    // Build the full body for the GitHub issue
    let logContent = this.filteredLines.length > 0 ? this.filteredLines.join('\n') : this.logLines.join('\n');

    // Limit log content to last 200 lines
    const lines = logContent.split('\n');
    if (lines.length > 200) {
      logContent = this.i18n.t('logs.reportTruncated') + '\n' + lines.slice(-200).join('\n');
    }

    const body = `${this.i18n.t('logs.reportBodyDescription')}

${this.bugDescription}

${this.i18n.t('logs.reportBodyLog')}

\`\`\`
${logContent}
\`\`\`

${this.i18n.t('logs.reportBodyInfo')}

- ${this.i18n.t('logs.reportLogFile')} ${this.selectedFile}
- ${this.i18n.t('logs.reportLineCount')} ${this.logLines.length}
- ${this.i18n.t('logs.reportTimestamp')} ${new Date().toISOString()}`;

    // Copy full body to clipboard first
    navigator.clipboard.writeText(body).then(() => {
      // Open GitHub issue with a short body instructing user to paste
      const pasteBody = encodeURIComponent(
        `${this.i18n.t('logs.reportBodyDescription')}

_${this.i18n.t('logs.reportPasteHint')}_

${this.i18n.t('logs.reportBodyLog')}

_${this.i18n.t('logs.reportClipboardPending')}_

---
- ${this.i18n.t('logs.reportLogFile')} ${this.selectedFile}
- ${this.i18n.t('logs.reportTimestamp')} ${new Date().toISOString()}`
      );
      const title = encodeURIComponent(`${this.i18n.t('logs.reportTitlePrefix')} ${this.bugDescription.trim().substring(0, 80)}`);
      const url = `https://github.com/hemidi-jsc/midicoder/issues/new?labels=bug&title=${title}&body=${pasteBody}`;
      window.open(url, '_blank');
      this.successMessage = this.i18n.t('logs.copied');
    }).catch(() => {
      // Fallback: open without clipboard
      const title = encodeURIComponent(`${this.i18n.t('logs.reportTitlePrefix')} ${this.bugDescription.trim().substring(0, 80)}`);
      const url = `https://github.com/hemidi-jsc/midicoder/issues/new?labels=bug&title=${title}`;
      window.open(url, '_blank');
      this.errorMessage = this.i18n.t('logs.copyError');
    });
  }
}
