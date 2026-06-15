/**
 * History List — hiển thị timeline brief_revisions (lịch sử thay đổi của brief).
 * Data shape từ SQLite table `brief_revisions`:
 *   { id, brief_id, version, revision_number, event, snapshot_hash, diff_summary,
 *     content_snapshot, created_at }
 */

import { Component, EventEmitter, Input, Output } from '@angular/core';
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
          <p class="hl-empty-icon"><i class="fa-solid fa-scroll"></i></p>          <p class="hl-empty-title">{{ 'brief.historyEmpty' | i18n }}</p>
          <p class="hl-empty-hint">{{ 'brief.historyHint' | i18n }}</p>
        </div>
      } @else {
        <div class="hl-scroll">
          @for (entry of items; track entry.id; let idx = $index) {
            <div class="hl-entry">
              <div class="hl-dot-col">
                <div class="hl-dot" [class]="dotColorClass(entry.event)"></div>
                @if (idx < items.length - 1) {
                  <div class="hl-line"></div>
                }
              </div>
              <div class="hl-content">
                <div class="hl-meta">
                  <span class="hl-rev">#{{ entry.revision_number }}</span>
                  <span class="hl-date">{{ formatDateTime(entry.created_at) }}</span>
                </div>
                @if (entry.diff_summary) {
                  <p class="hl-desc">{{ entry.diff_summary }}</p>
                }
                @if (entry.revision_number > 1) {
                  <div class="hl-footer-row">
                    @if (entry.diff_summary && hasChanges(entry)) {
                      <button class="hl-diff-link" (click)="onViewDiff(entry)">{{ 'brief.viewDiff' | i18n }}</button>
                    }
                    @if ((entry.diff_summary && hasChanges(entry)) && entry.revision_number > 1 && entry.snapshot_hash) {
                      <span class="hl-sep">·</span>
                    }
                    @if (entry.revision_number > 1 && entry.snapshot_hash) {
                      <span class="hl-hash">{{ entry.snapshot_hash | slice:0:7 }}</span>
                    }
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
      padding-top: 2px;
      flex-shrink: 0;
    }
    .hl-dot {
      width: 7px;
      height: 7px;
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
      min-height: 12px;
      margin-top: 2px;
      background: rgba(255,255,255,0.06);
    }

    .hl-content {
      flex: 1;
      min-width: 0;
    }
    .hl-meta {
      display: flex;
      align-items: baseline;
      gap: 8px;
      margin-bottom: 2px;
    }
    .hl-rev {
      font-size: 0.75rem;
      font-family: monospace;
      font-weight: 600;
      color: rgba(255,255,255,0.6);
    }
    .hl-date {
      font-size: 0.6875rem;
      font-family: monospace;
      color: rgba(255,255,255,0.3);
    }
    .hl-desc {
      font-size: 0.75rem;
      color: rgba(255,255,255,0.65);
      line-height: 1.4;
      margin: 0 0 4px 0;
    }

    .hl-footer-row {
      display: flex;
      align-items: center;
      gap: 5px;
      margin-top: 3px;
    }
    .hl-diff-link {
      font-size: 0.6875rem;
      font-family: monospace;
      color: #58a6ff;
      background: none;
      border: none;
      padding: 0;
      cursor: pointer;
      text-decoration: none;
      transition: color 0.15s;
    }
    .hl-diff-link:hover {
      color: #79c0ff;
      text-decoration: underline;
    }
    .hl-sep {
      font-size: 0.6875rem;
      color: rgba(255,255,255,0.2);
    }
    .hl-hash {
      font-size: 0.6875rem;
      font-family: monospace;
      color: rgba(63,185,80,0.7);
    }

    .hl-footer {
      padding: 10px 12px;
      border-top: 1px solid rgba(255,255,255,0.06);
      flex-shrink: 0;
    }
    .hl-footer-text {
      font-size: 0.6875rem;
      color: rgba(255,255,255,0.25);
    }
  `]
})
export class HistoryListComponent {
  /** Danh sách revision items (từ SQLite brief_revisions table) */
  @Input() items: BriefRevisionItem[] = [];
  /** Emitted when user clicks "Xem diff" on a revision */
  @Output() viewDiff = new EventEmitter<BriefRevisionItem>();

  formatDateTime(iso: string): string {
    return formatDateLocal(iso);
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

  onViewDiff(entry: BriefRevisionItem): void {
    this.viewDiff.emit(entry);
  }

  /** Check if a revision should show diff link — metadata-only events don't have content diff */
  hasChanges(entry: BriefRevisionItem): boolean {
    // These events don't change brief content — skip diff
    const noDiffEvents = ['freezed', 'analyzed', 'created'];
    return !noDiffEvents.includes(entry.event);
  }
}
