/**
 * Clarification List — hiển thị danh sách Q&A clarifications của một brief.
 * Data shape từ SQLite table `clarifications`:
 *   { id, brief_id, round, question, answer, is_memo, created_at }
 */

import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { I18nPipe } from '../../../core/i18n.pipe';

export interface ClarificationItem {
  id: number;
  brief_id: string;
  round: number;
  question: string;
  answer: string;
  is_memo: boolean;
  created_at: string;
}

@Component({
  selector: 'app-clarification-list',
  standalone: true,
  imports: [CommonModule, I18nPipe],
  template: `
    <div class="cl-list">
      @if (items.length === 0) {
        <div class="cl-empty">
          <p class="cl-empty-icon"><i class="fa-regular fa-comments"></i></p>          <p class="cl-empty-title">{{ 'brief.clarifyHistory' | i18n }}</p>
          <p class="cl-empty-hint">{{ 'brief.clarifyEmpty' | i18n }}</p>
        </div>
      } @else {
        <div class="cl-scroll">
          @for (cl of items; track cl.id) {
            <div class="cl-card" [class.cl-memo]="cl.is_memo">
              <div class="cl-header">
                <span class="cl-round">{{ 'brief.round' | i18n }} {{ cl.round }}</span>
                @if (cl.is_memo) {
                  <span class="cl-memo-badge">{{ 'brief.memo' | i18n }}</span>
                }
              </div>
              <p class="cl-q">
                <span class="cl-q-prefix">{{ 'brief.questionPrefix' | i18n }}</span> {{ cl.question }}
              </p>
              <p class="cl-a">
                <span class="cl-a-prefix">{{ 'brief.answerPrefix' | i18n }}</span> {{ cl.answer }}
              </p>
            </div>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .cl-list {
      display: flex;
      flex-direction: column;
      flex: 1;
      min-height: 0;
    }

    .cl-empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      padding: 2rem 1rem;
    }
    .cl-empty-icon {
      font-size: 1.5rem;
      margin: 0 0 0.5rem 0;
    }
    .cl-empty-title {
      font-size: 0.8125rem;
      color: rgba(255,255,255,0.5);
      margin: 0 0 0.25rem 0;
    }
    .cl-empty-hint {
      font-size: 0.75rem;
      color: rgba(255,255,255,0.3);
      margin: 0;
    }

    .cl-scroll {
      flex: 1;
      overflow-y: auto;
      padding: 12px;
    }
    .cl-scroll::-webkit-scrollbar {
      width: 4px;
    }
    .cl-scroll::-webkit-scrollbar-thumb {
      background: rgba(252,103,103,0.15);
      border-radius: 0;
    }

    .cl-card {
      padding: 12px;
      background: #1a1a2e;
      border: 0;
      border-left: 3px solid rgba(252,103,103,0.15);
      margin-bottom: 8px;
      transition: border-color 0.2s;
    }
    .cl-card:hover {
      border-left-color: rgba(252,103,103,0.4);
    }
    .cl-card.cl-memo {
      border-left-color: #f59e0b;
      background: rgba(245,158,11,0.04);
    }
    .cl-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 6px;
    }
    .cl-round {
      font-size: 0.6875rem;
      font-family: monospace;
      color: rgba(255,255,255,0.35);
    }
    .cl-memo-badge {
      font-size: 0.6875rem;
      padding: 1px 8px;
      border-radius: 0;
      background: rgba(245,158,11,0.2);
      color: #fbbf24;
    }
    .cl-q {
      font-size: 0.8125rem;
      color: rgba(255,255,255,0.85);
      line-height: 1.5;
      margin: 0 0 4px 0;
    }
    .cl-q-prefix {
      color: #60a5fa;
      font-weight: 600;
    }
    .cl-a {
      font-size: 0.8125rem;
      color: rgba(255,255,255,0.55);
      line-height: 1.5;
      margin: 0;
    }
    .cl-a-prefix {
      color: #3fb950;
      font-weight: 600;
    }
  `]
})
export class ClarificationListComponent {
  /** Danh sách clarification items (từ SQLite clarifications table) */
  @Input() items: ClarificationItem[] = [];
}
