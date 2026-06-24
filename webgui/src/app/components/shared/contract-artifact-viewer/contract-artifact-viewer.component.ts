/**
 * Contract Artifact Viewer — modal hiển thị raw YAML content của 1 category contract.
 * Reusable cho tất cả 9 loại contract (entities, commands, queries, events, ...).
 */

import { Component, Input, Output, EventEmitter, inject, ChangeDetectorRef, OnChanges, SimpleChanges, ViewEncapsulation } from '@angular/core';
import { CommonModule, NgClass } from '@angular/common';
import { I18nPipe } from '../../../core/i18n.pipe';
import { ApiService } from '../../../core/api.service';

import hljs from 'highlight.js/lib/core';
import yaml from 'highlight.js/lib/languages/yaml';
hljs.registerLanguage('yaml', yaml);

@Component({
  selector: 'app-contract-artifact-viewer',
  standalone: true,
  imports: [CommonModule, NgClass, I18nPipe],
  encapsulation: ViewEncapsulation.None,
  template: `
    @if (visible) {
    <div class="viewer-backdrop" (click)="onBackdropClick()">
      <div class="viewer-card" (click)="$event.stopPropagation()">
        <div class="viewer-header">
          <div class="viewer-title">
            <i class="fa-solid fa-file-code"></i>
            <span>{{ title }}</span>
            @if (loading) {
              <span class="viewer-loading"><i class="fa-solid fa-spinner fa-spin"></i></span>
            }
          </div>
          <div class="viewer-actions">
            @if (content) {
              <button class="viewer-copy-btn" (click)="copyToClipboard()" title="Copy YAML">
                <i class="fa-solid" [ngClass]="copied ? 'fa-check' : 'fa-copy'"></i>
                {{ copied ? 'Copied!' : 'Copy' }}
              </button>
            }
            <button class="viewer-close" (click)="onBackdropClick()">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>
        </div>
        @if (content) {
          <pre class="viewer-content"><code [innerHTML]="highlightedContent"></code></pre>
        } @else if (error) {
          <div class="viewer-error">{{ error }}</div>
        } @else if (!loading) {
          <div class="viewer-empty">{{ 'contract.noContent' | i18n }}</div>
        }
      </div>
    </div>
    }
  `,
  styles: [`
    app-contract-artifact-viewer * { margin: 0; padding: 0; box-sizing: border-box; }
    app-contract-artifact-viewer .viewer-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.85);
      backdrop-filter: blur(4px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10000;
      padding: 2rem;
    }
    app-contract-artifact-viewer .viewer-card {
      background: #16161e;
      border: 1px solid rgba(255,255,255,0.1);
      width: 100%;
      max-width: 900px;
      height: 75vh;
      display: flex;
      flex-direction: column;
      box-shadow: 0 0 40px rgba(0,0,0,0.5);
    }
    app-contract-artifact-viewer .viewer-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 18px;
      border-bottom: 1px solid rgba(255,255,255,0.08);
      flex-shrink: 0;
    }
    app-contract-artifact-viewer .viewer-title {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 1rem;
      font-weight: 600;
      color: #fff;
    }
    app-contract-artifact-viewer .viewer-title i { color: #fc6767; }
    app-contract-artifact-viewer .viewer-loading { color: rgba(255,255,255,0.4); font-size: 0.85rem; }
    app-contract-artifact-viewer .viewer-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    app-contract-artifact-viewer .viewer-copy-btn {
      background: none;
      border: 1px solid rgba(255,255,255,0.15);
      color: rgba(255,255,255,0.5);
      font-size: 0.75rem;
      padding: 4px 10px;
      cursor: pointer;
      transition: all 0.2s;
      display: flex;
      align-items: center;
      gap: 5px;
    }
    app-contract-artifact-viewer .viewer-copy-btn:hover { color: #fff; border-color: #58a6ff; }
    app-contract-artifact-viewer .viewer-copy-btn .fa-check { color: #3fb950; }
    app-contract-artifact-viewer .viewer-close {
      background: none;
      border: 1px solid rgba(255,255,255,0.15);
      color: rgba(255,255,255,0.5);
      font-size: 1rem;
      padding: 4px 10px;
      cursor: pointer;
      transition: all 0.2s;
    }
    app-contract-artifact-viewer .viewer-close:hover { color: #fff; border-color: #fc6767; }
    app-contract-artifact-viewer .viewer-content {
      flex: 1;
      overflow-y: auto;
      padding: 14px 18px;
      margin: 0;
    }
    app-contract-artifact-viewer .viewer-content code {
      font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
      font-size: 0.78rem;
      line-height: 1.6;
      background: transparent;
      padding: 0;
    }
    /* highlight.js dark theme */
    app-contract-artifact-viewer .viewer-content .hljs { color: rgba(255,255,255,0.75); background: transparent; }
    app-contract-artifact-viewer .viewer-content .hljs-keyword { color: #ff7b72; }
    app-contract-artifact-viewer .viewer-content .hljs-string { color: #a5d6ff; }
    app-contract-artifact-viewer .viewer-content .hljs-number { color: #79c0ff; }
    app-contract-artifact-viewer .viewer-content .hljs-boolean { color: #79c0ff; }
    app-contract-artifact-viewer .viewer-content .hljs-literal { color: #79c0ff; }
    app-contract-artifact-viewer .viewer-content .hljs-null { color: #79c0ff; }
    app-contract-artifact-viewer .viewer-content .hljs-type { color: #d2a8ff; }
    app-contract-artifact-viewer .viewer-content .hljs-attr { color: #7ee787; }
    app-contract-artifact-viewer .viewer-content .hljs-punctuation { color: rgba(255,255,255,0.35); }
    app-contract-artifact-viewer .viewer-content .hljs-comment { color: rgba(255,255,255,0.3); font-style: italic; }
    app-contract-artifact-viewer .viewer-content .hljs-name { color: #d2a8ff; }
    app-contract-artifact-viewer .viewer-content .hljs-bullet { color: rgba(255,255,255,0.4); }
    app-contract-artifact-viewer .viewer-empty,
    app-contract-artifact-viewer .viewer-error {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.85rem;
    }
    app-contract-artifact-viewer .viewer-empty { color: rgba(255,255,255,0.3); }
    app-contract-artifact-viewer .viewer-error { color: #f85149; }
  `]
})
export class ContractArtifactViewerComponent implements OnChanges {
  private api = inject(ApiService);
  private cdr = inject(ChangeDetectorRef);

  @Input() visible = false;
  @Input() category = '';
  @Input() title = '';
  @Output() close = new EventEmitter<void>();

  content = '';
  highlightedContent = '';
  loading = false;
  error = '';
  copied = false;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible'] && this.visible && this.category) {
      this.load();
    } else if (changes['visible'] && !this.visible) {
      this.content = '';
      this.highlightedContent = '';
      this.error = '';
      this.loading = false;
      this.copied = false;
    }
  }

  private async load(): Promise<void> {
    this.loading = true;
    this.content = '';
    this.highlightedContent = '';
    this.error = '';
    this.cdr.detectChanges();
    try {
      const result = await this.api.getContractArtifactContent(this.category);
      if (result.success && result.data) {
        this.content = result.data.content || '';
        this.highlight();
      } else {
        this.error = result.message || 'Not found';
      }
    } catch (err: any) {
      this.error = err.message || 'Failed to load';
    } finally {
      this.loading = false;
    }
  }

  private highlight(): void {
    try {
      this.highlightedContent = hljs.highlight(this.content, { language: 'yaml' }).value;
    } catch {
      // Fallback: escape HTML and show plain
      this.highlightedContent = this.escapeHtml(this.content);
    }
  }

  private escapeHtml(text: string): string {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  async copyToClipboard(): Promise<void> {
    if (!this.content) return;
    try {
      await navigator.clipboard.writeText(this.content);
      this.copied = true;
      setTimeout(() => (this.copied = false), 2000);
    } catch {
      this.copied = false;
    }
  }

  onBackdropClick(): void {
    this.close.emit();
  }
}
