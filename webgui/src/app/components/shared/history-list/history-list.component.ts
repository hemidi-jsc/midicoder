/**
 * History List — hiển thị timeline brief_revisions (lịch sử thay đổi của brief).
 * Data shape từ SQLite table `brief_revisions`:
 *   { id, brief_id, version, revision_number, event, snapshot_hash, diff_summary,
 *     content_snapshot, created_at }
 */

import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { I18nPipe } from '../../../core/i18n.pipe';
import { formatDateLocal } from '../../../core/date.util';

export interface BriefRevisionItem {
  id: number;
  brief_id: string;
  version: string;
  revision_number: number;
  event: string;
  snapshot_hash: string | null;
  diff_summary: string | null;
  content_snapshot: string | null;
  created_at: string;
}

@Component({
  selector: 'app-history-list',
  standalone: true,
  imports: [CommonModule, I18nPipe],
  template: `
    <div class="hl-list">
      @if (items.length === 0) {
        <div class="hl-empty">
          <p class="hl-empty-icon">📝</p>
          <p class="hl-empty-title">{{ 'brief.historyEmpty' | i18n }}</p>
          <p class="hl-empty-hint">{{ 'brief.historyHint' | i18n }}</p>
        </div>
      } @else {
        <div class="hl-scroll">
          @for (entry of items; track entry.id; let idx = $index) {
            <div class="hl-entry">
              <div class="hl-dot-col">
                <div class="hl-dot"
                     [class]="dotColorClass(entry.event)">
                </div>
                @if (idx < items.length - 1) {
                  <div class="hl-line"></div>
                }
              </div>
              <div class="hl-content">
                <div class="hl-meta">
                  <span class="hl-rev">#{{ entry.revision_number }}</span>
                  <span class="hl-badge"
                        [class]="badgeClass(entry.event)">
                    {{ getEventLabel(entry.event) }}
                  </span>
                  <span class="hl-date">{{ formatDateTime(entry.created_at) }}</span>
                </div>
                @if (entry.diff_summary) {
                  <p class="hl-desc">{{ entry.diff_summary }}</p>
                }
                @if (entry.snapshot_hash) {
                  <div class="hl-hash">
                    <span class="hash-new">{{ entry.snapshot_hash | slice:0:7 }}</span>
                  </div>
                }
              </div>
            </div>
          }
        </div>
        @if (items.length > 0) {
          <div class="hl-footer">
            <span class="hl-footer-text">{{ 'brief.lastUpdate' | i18n }} {{ formatDateTime(items[0]?.created_at || '') }}</span>
          </div>
        }
      }
    </div>
  `,
  styles: [`
    .hl-list {
      display: flex;
      flex-direction: column;
      flex: 1;
      min-height: 0;
    }

    .hl-empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      padding: 2rem 1rem;
    }
    .hl-empty-icon {
      font-size: 1.5rem;
      margin: 0 0 0.5rem 0;
    }
    .hl-empty-title {
      font-size: 0.8125rem;
      color: rgba(255,255,255,0.5);
      margin: 0 0 0.25rem 0;
    }
    .hl-empty-hint {
      font-size: 0.75rem;
      color: rgba(255,255,255,0.3);
      margin: 0;
    }

    .hl-scroll {
      flex: 1;
      overflow-y: auto;
      padding: 12px;
    }
    .hl-scroll::-webkit-scrollbar {
      width: 4px;
    }
    .hl-scroll::-webkit-scrollbar-thumb {
      background: rgba(252,103,103,0.15);
      border-radius: 0;
    }

    .hl-entry {
      display: flex;
      gap: 10px;
      padding-bottom: 12px;
    }
    .hl-dot-col {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding-top: 3px;
      flex-shrink: 0;
    }
    .hl-dot {
      width: 9px;
      height: 9px;
      border-radius: 0;
      flex-shrink: 0;
    }
    .dot-green  { background: #3fb950; }
    .dot-blue   { background: #3884ff; }
    .dot-purple { background: #a855f7; }
    .dot-red    { background: #f85149; }
    .dot-gray   { background: #888; }
    .hl-line {
      width: 1px;
      flex: 1;
      min-height: 16px;
      margin-top: 3px;
      background: rgba(252,103,103,0.12);
    }

    .hl-content {
      flex: 1;
      min-width: 0;
      padding-bottom: 4px;
    }
    .hl-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 3px;
      flex-wrap: wrap;
    }
    .hl-rev {
      font-size: 0.6875rem;
      font-family: monospace;
      color: rgba(255,255,255,0.3);
    }
    .hl-badge {
      font-size: 0.6875rem;
      padding: 2px 7px;
      border-radius: 0;
      font-weight: 600;
    }
    .badge-green  { background: rgba(63,185,80,0.2); color: #56d364; border: 1px solid rgba(63,185,80,0.3); }
    .badge-blue   { background: rgba(56,132,255,0.2); color: #58a6ff; border: 1px solid rgba(56,132,255,0.3); }
    .badge-purple { background: rgba(168,85,247,0.2); color: #c084fc; border: 1px solid rgba(168,85,247,0.3); }
    .badge-red    { background: rgba(248,81,73,0.2); color: #f87171; border: 1px solid rgba(248,81,73,0.3); }
    .badge-gray   { background: rgba(136,136,136,0.2); color: #999; border: 1px solid rgba(136,136,136,0.3); }
    .hl-date {
      font-size: 0.6875rem;
      font-family: monospace;
      color: rgba(255,255,255,0.35);
    }
    .hl-desc {
      font-size: 0.75rem;
      color: rgba(255,255,255,0.75);
      line-height: 1.4;
      margin: 0;
    }
    .hl-hash {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-top: 4px;
    }
    .hash-new {
      font-size: 0.6875rem;
      font-family: monospace;
      color: #3fb950;
      background: rgba(63,185,80,0.1);
      padding: 1px 5px;
      border-radius: 0;
    }

    .hl-footer {
      padding: 10px 12px;
      border-top: 1px solid rgba(252,103,103,0.1);
      flex-shrink: 0;
    }
    .hl-footer-text {
      font-size: 0.6875rem;
      color: rgba(255,255,255,0.3);
    }
  `]
})
export class HistoryListComponent {
  /** Danh sách revision items (từ SQLite brief_revisions table) */
  @Input() items: BriefRevisionItem[] = [];

  formatDateTime(iso: string): string {
    return formatDateLocal(iso);
  }

  getEventLabel(event: string): string {
    const labels: Record<string, string> = {
      'created': 'Created',
      'content_updated': 'Updated',
      'analyzed': 'Analyzed',
      'freezed': 'Freezed',
    };
    return labels[event] || event;
  }

  dotColorClass(event: string): string {
    const map: Record<string, string> = {
      'created': 'dot-green',
      'content_updated': 'dot-blue',
      'analyzed': 'dot-purple',
      'freezed': 'dot-red',
    };
    return map[event] || 'dot-gray';
  }

  badgeClass(event: string): string {
    const map: Record<string, string> = {
      'created': 'badge-green',
      'content_updated': 'badge-blue',
      'analyzed': 'badge-purple',
      'freezed': 'badge-red',
    };
    return `hl-badge ${map[event] || 'badge-gray'}`;
  }
}
