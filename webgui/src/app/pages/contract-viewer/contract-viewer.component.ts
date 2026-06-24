/**
 * Component Contract Viewer
 * 
 * UI: Card list của 9 categories — mỗi category có nút "Tạo hợp đồng" riêng.
 * Khi bấm nút → hiện `llm-progress` overlay (SSE stream 1 category).
 * Ràng buộc: phải gen theo thứ tự, category sau bị disabled nếu category trước chưa xong.
 */

import { Component, inject, OnInit, OnDestroy, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { I18nPipe } from '../../core/i18n.pipe';
import { I18nService } from '../../core/i18n.service';
import { ApiService } from '../../core/api.service';
import { VersionService } from '../../core/version.service';
import { LlmProgressComponent } from '../../components/shared/llm-progress/llm-progress.component';
import { ContractArtifactViewerComponent } from '../../components/shared/contract-artifact-viewer/contract-artifact-viewer.component';
import { DOCS_BASE } from '../../core/app.constants';

interface CategoryDef {
  key: string;
  labelKey: string;
  icon: string;
  colorClass: string;
  order: number;
  exists: boolean;
  generating: boolean;
  count: number;
}

@Component({
  selector: 'app-contract-viewer',
  standalone: true,
  imports: [CommonModule, RouterLink, I18nPipe, LlmProgressComponent, ContractArtifactViewerComponent],
  template: `
    <div>
      <!-- Header -->
      <div class="mb-6 flex items-center justify-between">
        <div>
          <div class="page-header-row">
            <h1 class="text-2xl font-bold">{{ 'contract.title' | i18n }}</h1>
            <a href="{{ docsUrl }}" target="_blank" rel="noopener" class="docs-link">{{ 'common.readGuide' | i18n }}</a>
          </div>
          <p class="text-text-secondary mt-1">{{ 'contract.subtitle' | i18n }}</p>
        </div>
        <div class="flex space-x-3">
          <!-- Freeze — show khi tất cả đã gen -->
          @if (allGenerated) {
            <button (click)="handleFreeze()" class="btn btn-secondary freeze-btn" [disabled]="isFreezing">
              @if (isFreezing) {
                <i class="fa-solid fa-spinner fa-spin"></i>
              } @else {
                <i class="fa-solid fa-lock"></i>
              }
              {{ isFreezing ? ('contract.loading' | i18n) : ('contract.freeze' | i18n) }}
            </button>
          }
        </div>
      </div>

      <!-- Progress bar -->
      <div class="progress-bar-card mb-6">
        <div class="progress-header">
          <span class="progress-label">{{ completedCount }}/{{ categories.length }} {{ 'contract.categoryDone' | i18n }}</span>
          <span class="progress-pct">{{ progressPct }}%</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" [style.width.%]="progressPct"></div>
        </div>
      </div>

      <!-- Success/Error banner -->
      @if (successMessage) {
        <div class="banner banner-success mb-4">
          <i class="fa-solid fa-circle-check"></i>
          <span>{{ successMessage }}</span>
          <button class="dismiss-btn" (click)="successMessage = ''"><i class="fa-solid fa-xmark"></i></button>
        </div>
      }
      @if (errorMessage) {
        <div class="banner banner-error mb-4">
          <i class="fa-solid fa-circle-xmark"></i>
          <span>{{ errorMessage }}</span>
          <button class="dismiss-btn" (click)="errorMessage = ''"><i class="fa-solid fa-xmark"></i></button>
        </div>
      }

      <!-- Category cards grid -->
      <div class="category-grid">
        @for (cat of categories; track cat.key) {
          <div class="cat-card" [class]="getCatCardClass(cat)">
            <div class="cat-header">
              <div class="cat-icon-wrap" [class]="cat.colorClass">
                <i class="fa-solid {{ cat.icon }}"></i>
              </div>
              <div class="cat-info">
                <span class="cat-label">{{ ('contract.' + cat.labelKey) | i18n }}</span>
                <span class="cat-order">#{{ cat.order }}</span>
              </div>
              @if (cat.exists) {
                <i class="fa-solid fa-circle-check cat-status-done"></i>
              } @else if (cat.generating) {
                <i class="fa-solid fa-spinner fa-spin cat-status-running"></i>
              }
            </div>

            @if (cat.exists) {
              <div class="cat-footer cat-footer-done">
                <div class="cat-count">{{ cat.count }} chars</div>
                <button class="btn btn-secondary btn-view" (click)="handleViewCategory(cat)">
                  <i class="fa-solid fa-eye"></i> {{ 'contract.viewArtifact' | i18n }}
                </button>
              </div>
            }

            @if (!cat.exists) {
              <div class="cat-footer">
                @if (isPrerequisiteReady(cat)) {
                  <button
                    class="btn btn-primary btn-gen"
                    (click)="handleGenerateCategory(cat)"
                    [disabled]="hasActiveGeneration"
                  >
                    <i class="fa-solid fa-wand-magic-sparkles"></i>
                    {{ 'contract.generate' | i18n }}
                  </button>
                } @else {
                  <div class="cat-blocked">
                    <i class="fa-solid fa-lock"></i>
                    <span>{{ 'contract.blocked' | i18n }}</span>
                  </div>
                }
              </div>
            }
          </div>
        }
      </div>

      <!-- Next action — show khi tất cả đã gen -->
      @if (allGenerated) {
        <div class="mt-6 flex justify-end">
          <a routerLink="/ir-explorer" class="btn btn-primary">
            {{ 'contract.toIR' | i18n }}
          </a>
        </div>
      }
    </div>

    <!-- llm-progress overlay -->
    <app-llm-progress
      [visible]="llmProgressVisible"
      [title]="llmProgressTitle"
      (closeOverlay)="closeLlmProgress()"
      (viewResult)="onLlmProgressDone()"
    >
    </app-llm-progress>

    <!-- Artifact viewer modal -->
    <app-contract-artifact-viewer
      [visible]="viewerVisible"
      [category]="viewerCategoryKey"
      [title]="viewerTitle"
      (close)="viewerVisible = false"
    />
  `,
  styles: [`
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
    .docs-link:hover { text-decoration: underline; }

    /* Progress bar */
    .progress-bar-card {
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.06);
      padding: 12px 16px;
    }
    .progress-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      font-size: 0.78rem;
      color: rgba(255,255,255,0.5);
    }
    .progress-pct {
      font-family: monospace;
      font-weight: 700;
      color: #fc6767;
    }
    .progress-track {
      height: 6px;
      background: rgba(255,255,255,0.06);
      overflow: hidden;
    }
    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #fc6767, #f0883e);
      transition: width 0.4s ease;
    }

    /* Category grid */
    .category-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
    }

    .cat-card {
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.06);
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      transition: all 0.2s;
    }
    .cat-card:hover {
      border-color: rgba(255,255,255,0.12);
      background: rgba(255,255,255,0.05);
    }
    .cat-card.done {
      border-color: rgba(63,185,80,0.25);
    }
    .cat-card.generating {
      border-color: rgba(58,144,217,0.4);
      background: rgba(58,144,217,0.05);
    }
    .cat-card.blocked {
      opacity: 0.45;
    }

    .cat-header {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .cat-icon-wrap {
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(255,255,255,0.05);
      font-size: 1rem;
      flex-shrink: 0;
    }
    .cat-icon-wrap.color-blue { color: #58a6ff; }
    .cat-icon-wrap.color-orange { color: #f0883e; }
    .cat-icon-wrap.color-cyan { color: #39c5cf; }
    .cat-icon-wrap.color-purple { color: #bc8cff; }
    .cat-icon-wrap.color-teal { color: #56b6c2; }

    .cat-info {
      display: flex;
      flex-direction: column;
      gap: 2px;
      flex: 1;
      min-width: 0;
    }
    .cat-label {
      font-size: 0.85rem;
      font-weight: 600;
      color: rgba(255,255,255,0.85);
    }
    .cat-order {
      font-size: 0.65rem;
      color: rgba(255,255,255,0.3);
      font-family: monospace;
    }

    .cat-status-done { color: #3fb950; font-size: 1rem; }
    .cat-status-running { color: #3a90d9; font-size: 1rem; }

    .cat-count {
      font-size: 0.72rem;
      color: rgba(255,255,255,0.35);
      font-family: monospace;
    }

    .cat-footer {
      margin-top: auto;
      padding-top: 6px;
    }
    .cat-footer-done {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .btn-view {
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      font-size: 0.78rem;
    }

    .btn-gen {
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }

    .cat-blocked {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      padding: 8px;
      font-size: 0.72rem;
      color: rgba(255,255,255,0.3);
    }
    .cat-blocked i { color: rgba(255,255,255,0.2); }

    /* Banners */
    .banner {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      font-size: 0.8rem;
      font-weight: 500;
      border: 1px solid;
    }
    .banner-success {
      background: rgba(63,185,80,0.08);
      border-color: rgba(63,185,80,0.3);
      color: #3fb950;
    }
    .banner-error {
      background: rgba(248,81,73,0.08);
      border-color: rgba(248,81,73,0.3);
      color: #f85149;
    }
    .banner-valid {
      background: rgba(63,185,80,0.08);
      border-color: rgba(63,185,80,0.3);
      color: #3fb950;
    }
    .banner-warnings {
      background: rgba(210,168,58,0.08);
      border-color: rgba(210,168,58,0.3);
      color: #d2a83a;
    }
    .banner-errors {
      background: rgba(248,81,73,0.08);
      border-color: rgba(248,81,73,0.3);
      color: #f85149;
    }
    .banner-fatal {
      background: rgba(248,81,73,0.15);
      border-color: rgba(248,81,73,0.5);
      color: #f85149;
    }
    .dismiss-btn {
      margin-left: auto;
      background: none;
      border: none;
      color: inherit;
      opacity: 0.5;
      cursor: pointer;
      font-size: 0.85rem;
      padding: 0 4px;
    }
    .dismiss-btn:hover { opacity: 1; }

    .inline-btn {
      margin-left: 12px;
      padding: 2px 10px;
      background: rgba(248,81,73,0.15);
      border: 1px solid rgba(248,81,73,0.4);
      color: #f85149;
      font-size: 0.72rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
    .inline-btn:hover { background: rgba(248,81,73,0.25); }

    .freeze-btn {
      border: 1px solid rgba(210,168,58,0.3) !important;
      color: #d2a83a !important;
    }
    .freeze-btn:hover {
      background: rgba(210,168,58,0.15) !important;
      border-color: rgba(210,168,58,0.5) !important;
    }
  `],
})
export class ContractViewerComponent implements OnInit, OnDestroy {
  private readonly api = inject(ApiService);
  private readonly i18n = inject(I18nService);
  private readonly versionService = inject(VersionService);

  readonly docsUrl = `${DOCS_BASE}/contract`;

  // Categories
  categories: CategoryDef[] = [
    { key: 'entities', labelKey: 'entities', icon: 'fa-cube', colorClass: 'color-blue', order: 1, exists: false, generating: false, count: 0 },
    { key: 'commands', labelKey: 'commands', icon: 'fa-bolt', colorClass: 'color-orange', order: 2, exists: false, generating: false, count: 0 },
    { key: 'queries', labelKey: 'queries', icon: 'fa-magnifying-glass', colorClass: 'color-cyan', order: 3, exists: false, generating: false, count: 0 },
    { key: 'events', labelKey: 'events', icon: 'fa-satellite-dish', colorClass: 'color-purple', order: 4, exists: false, generating: false, count: 0 },
    { key: 'workflows', labelKey: 'workflows', icon: 'fa-diagram-project', colorClass: 'color-teal', order: 5, exists: false, generating: false, count: 0 },
    { key: 'value_objects', labelKey: 'valueObjects', icon: 'fa-gem', colorClass: 'color-blue', order: 6, exists: false, generating: false, count: 0 },
    { key: 'guards', labelKey: 'guards', icon: 'fa-shield-halved', colorClass: 'color-orange', order: 7, exists: false, generating: false, count: 0 },
    { key: 'roles', labelKey: 'roles', icon: 'fa-users', colorClass: 'color-purple', order: 8, exists: false, generating: false, count: 0 },
    { key: 'ui_components', labelKey: 'uiComponents', icon: 'fa-puzzle-piece', colorClass: 'color-teal', order: 9, exists: false, generating: false, count: 0 },
  ];

  get completedCount(): number {
    return this.categories.filter(c => c.exists).length;
  }

  get progressPct(): number {
    return Math.round((this.completedCount / this.categories.length) * 100);
  }

  get allGenerated(): boolean {
    return this.completedCount === this.categories.length;
  }

  get hasActiveGeneration(): boolean {
    return this.categories.some(c => c.generating);
  }

  // Generation state
  isFreezing = false;
  successMessage = '';
  errorMessage = '';

  // llm-progress
  llmProgressVisible = false;
  llmProgressTitle = '';
  llmProgressCategory: string = '';
  @ViewChild(LlmProgressComponent) llmProgressRef!: LlmProgressComponent;

  // YAML viewer
  viewerVisible = false;
  viewerCategoryKey = '';
  viewerTitle = '';

  async ngOnInit(): Promise<void> {
    await this.loadContracts();
    window.addEventListener('version-switched', this.onVersionSwitched);
  }

  ngOnDestroy(): void {
    window.removeEventListener('version-switched', this.onVersionSwitched);
  }

  private onVersionSwitched = async () => {
    try {
      await this.loadContracts();
    } finally {
      this.versionService.stopLoading();
    }
  };

  /* ── helpers ── */
  isPrerequisiteReady(cat: CategoryDef): boolean {
    if (cat.order === 1) return true;
    // All categories before this one must exist
    return this.categories.slice(0, cat.order - 1).every(c => c.exists);
  }

  getCatCardClass(cat: CategoryDef): string {
    let cls = 'cat-card';
    if (cat.exists) cls += ' done';
    else if (cat.generating) cls += ' generating';
    else if (!this.isPrerequisiteReady(cat)) cls += ' blocked';
    return cls;
  }

  /* ── load ── */
  async loadContracts(): Promise<void> {
    this.successMessage = '';
    this.errorMessage = '';

    // Check each category via /contract/artifacts
    for (const cat of this.categories) {
      cat.generating = false;
      try {
        const result = await this.api.getContractArtifact(cat.key);
        if (result.success && result.data?.exists) {
          cat.exists = true;
          cat.count = result.data.content_length || 0;
        } else {
          cat.exists = false;
          cat.count = 0;
        }
      } catch {
        cat.exists = false;
        cat.count = 0;
      }
    }
  }

  /* ── generate single category ── */
  async handleGenerateCategory(cat: CategoryDef): Promise<void> {
    if (!this.isPrerequisiteReady(cat)) return;

    cat.generating = true;
    this.errorMessage = '';
    this.successMessage = '';

    // Set title for llm-progress
    this.llmProgressTitle = `${this.i18n.t('contract.generateStreaming')} — ${this.i18n.t('contract.' + cat.labelKey)}`;
    this.llmProgressCategory = cat.key;

    // Open llm-progress overlay
    this.llmProgressVisible = true;

    // Reset llm-progress component state
    if (this.llmProgressRef) {
      this.llmProgressRef.reset();
      this.llmProgressRef.status = 'streaming';
    }

    // Start SSE stream
    const stream = this.api.streamContractCategory(cat.key);

    try {
      for await (const { event, data } of stream) {
        if (this.llmProgressRef) {
          this.llmProgressRef.onMessage({ type: event, data });
          // Propagate error to banner
          if (event === 'error' && this.llmProgressRef.lastError) {
            this.errorMessage = this.llmProgressRef.lastError;
          }
        }
      }

      // If completed successfully
      if (!this.llmProgressRef?.lastError) {
        this.successMessage = `${this.i18n.t('contract.' + cat.labelKey)} — ${this.i18n.t('contract.genSuccess')}`;
      }
    } catch (err: any) {
      this.errorMessage = err.message || 'Stream failed';
      if (this.llmProgressRef) {
        this.llmProgressRef.status = 'error';
        this.llmProgressRef.lastError = this.errorMessage;
      }
    } finally {
      cat.generating = false;
      await this.loadContracts();
    }
  }

  closeLlmProgress(): void {
    this.llmProgressVisible = false;
  }

  onLlmProgressDone(): void {
    this.llmProgressVisible = false;
  }

  /* ── view artifact ── */
  async handleViewCategory(cat: CategoryDef): Promise<void> {
    this.viewerCategoryKey = cat.key;
    this.viewerTitle = `${this.i18n.t('contract.viewArtifact')} — ${this.i18n.t('contract.' + cat.labelKey)}`;
    this.viewerVisible = true;
  }

  /* ── freeze ── */
  async handleFreeze(): Promise<void> {
    if (!confirm(this.i18n.t('contract.freezeConfirm'))) return;

    this.isFreezing = true;
    this.successMessage = '';
    this.errorMessage = '';

    try {
      const result = await this.api.freezeContract();
      if (result.success) {
        const data = result.data as any;
        this.successMessage = this.i18n.t('contract.freezeSuccess', { count: data.frozen_count });
      } else {
        this.errorMessage = result.message || this.i18n.t('contract.freezeFailed');
      }
    } catch (err: any) {
      this.errorMessage = err.message || this.i18n.t('contract.freezeFailed');
    } finally {
      this.isFreezing = false;
    }
  }
}
