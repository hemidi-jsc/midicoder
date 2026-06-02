/**
 * Component Brief Editor
 * 1 version = 1 brief duy nhất, status = progress (draft → clarified → frozen → archived)
 * Auto-save + phân tích + clarification history
 */

import { Component, ChangeDetectorRef, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, Router } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { PipelineStore } from '../../core/pipeline.store';

@Component({
  selector: 'app-brief-editor',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="container mx-auto px-6 py-8">
      <!-- Header -->
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold">Brief Editor</h1>
          <p class="text-text-secondary mt-1">Viết brief cho project của bạn</p>

          <!-- Status Badge + Version -->
          @if (briefInfo) {
            <div class="flex items-center space-x-2 mt-3">
              <span class="text-xs px-2 py-1 rounded font-medium"
                    [class]="getStatusBadgeClass(briefInfo.status)"
                    [title]="'Trạng thái: ' + briefInfo.status">
                {{ briefInfo.status | titlecase }}
              </span>
              @if (activeVersion) {
                <span class="text-xs px-2 py-1 rounded font-medium bg-bg-secondary text-text-tertiary border border-border-primary">
                  {{ activeVersion }}
                </span>
              }
            </div>
          }
        </div>

        <div class="flex items-center space-x-3">
          <!-- Auto-save status -->
          <span class="text-sm text-text-tertiary flex items-center">
            @if (saveStatus === 'saving') {
              <svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Đang lưu...
            } @else if (saveStatus === 'saved') {
              <svg class="mr-2 h-4 w-4 text-accent-success" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
              </svg>
              Đã lưu
            } @else if (hasUnsavedChanges) {
              <span class="text-accent-warning">● Có thay đổi chưa lưu</span>
            }
          </span>

          <!-- Rewrite Button -->
          @if (briefInfo && briefInfo.status !== 'frozen') {
            <button (click)="handleRewrite()" class="btn btn-secondary" [disabled]="isRewriting || !briefContent.trim()">
              {{ isRewriting ? 'Đang xử lý...' : 'Viết lại' }}
            </button>
          }

          <!-- Freeze Button - chỉ hiện khi status === clarified -->
          @if (briefInfo && briefInfo.status === 'clarified') {
            <button (click)="handleFreeze()" class="btn btn-secondary" [disabled]="isFreezing">
              {{ isFreezing ? 'Đang xử lý...' : 'Đóng (Freeze)' }}
            </button>
          }

          <!-- Analyze Button - chỉ hiện khi status !== frozen -->
          @if (!briefInfo || briefInfo.status !== 'frozen') {
            <button (click)="handleAnalyze()" class="btn btn-primary" [disabled]="isAnalyzing || !briefContent.trim()">
              {{ isAnalyzing ? 'Đang tải...' : 'Phân tích' }}
            </button>
          } @else {
            <span class="text-xs text-text-tertiary italic">Brief đã được đóng</span>
          }
        </div>
      </div>

      <!-- Frozen Banner -->
      @if (briefInfo && briefInfo.status === 'frozen') {
        <div class="mb-4 p-3 bg-accent-warning bg-opacity-10 border border-accent-warning rounded text-accent-warning">
          <strong>Brief đã đóng (frozen)</strong> — không thể chỉnh sửa. Tạo version mới để inherit.
        </div>
      }

      <!-- Success Message -->
      @if (successMessage) {
        <div class="mb-4 px-4 py-3 bg-green-600 bg-opacity-30 border border-green-400 rounded">
          <span class="text-green-200 font-bold text-sm">✓ {{ successMessage }}</span>
        </div>
      }

      <!-- Error Message -->
      @if (errorMessage) {
        <div class="mb-4 p-3 bg-accent-error bg-opacity-15 border border-accent-error rounded text-accent-error font-medium">
          {{ errorMessage }}
        </div>
      }

      <!-- Editor -->
      <div class="card">
        <textarea
          [(ngModel)]="briefContent"
          (ngModelChange)="onContentChange()"
          [readonly]="isFrozen"
          class="w-full h-96 bg-bg-secondary border border-border-primary rounded p-4 text-text-primary font-mono text-sm resize-none focus:outline-none focus:border-accent-primary"
          [class.opacity-50]="isFrozen"
          placeholder="Viết brief của bạn ở đây..."
        ></textarea>
      </div>

      <!-- Analysis Result -->
      @if (analysisResult) {
        <div class="card mt-6">
          <h2 class="text-lg font-semibold mb-4">Kết quả phân tích</h2>

          <!-- Intent -->
          <div class="mb-4">
            <h3 class="font-medium text-accent-primary mb-2">Intent</h3>
            <div class="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span class="text-text-tertiary">Domain:</span>
                <span class="ml-2">{{ analysisResult?.analysis?.intent?.domain }}</span>
              </div>
              <div>
                <span class="text-text-tertiary">Type:</span>
                <span class="ml-2">{{ analysisResult?.analysis?.intent?.type }}</span>
              </div>
              <div>
                <span class="text-text-tertiary">Scale:</span>
                <span class="ml-2">{{ analysisResult?.analysis?.intent?.scale }}</span>
              </div>
            </div>
          </div>

          <!-- Ambiguities -->
          @if (analysisResult?.analysis?.ambiguities?.length) {
            <div class="mb-4">
              <h3 class="font-medium text-accent-warning mb-2">Ambiguities ({{ analysisResult?.analysis?.ambiguities?.length }})</h3>
              <div class="space-y-2">
                @for (ambiguity of analysisResult?.analysis?.ambiguities; track ambiguity.id) {
                  <div class="p-3 bg-bg-secondary rounded border-l-2 border-accent-warning">
                    <p class="text-sm text-text-primary"><strong>{{ ambiguity.type }}:</strong> {{ ambiguity.description }}</p>
                    <p class="text-sm text-text-tertiary mt-1">{{ ambiguity.source_text }}</p>
                  </div>
                }
              </div>
            </div>
          }

          <!-- Next Action -->
          @if (analysisResult?.status === 'needs_clarification') {
            <div class="mt-4 flex justify-end">
              <a routerLink="/clarification" class="btn btn-primary">
                Làm rõ yêu cầu →
              </a>
            </div>
          }
        </div>
      }

      <!-- Clarification History -->
      @if (clarifications.length > 0) {
        <div class="card mt-6">
          <h2 class="text-lg font-semibold mb-4">Lịch sử Clarification ({{ clarifications.length }})</h2>
          <div class="space-y-4">
            @for (cl of clarifications; track cl.id) {
              <div class="p-4 bg-bg-secondary rounded border-l-2" [class]="cl.is_memo ? 'border-accent-warning' : 'border-border-primary'">
                <div class="flex items-start justify-between mb-2">
                  <span class="text-xs font-mono text-text-tertiary">Round {{ cl.round }}</span>
                  @if (cl.is_memo) {
                    <span class="text-xs bg-accent-warning bg-opacity-20 text-accent-warning px-2 py-0.5 rounded">Memo</span>
                  }
                </div>
                <p class="text-sm text-text-primary mb-2">
                  <span class="text-accent-primary font-medium">Q:</span> {{ cl.question }}
                </p>
                <p class="text-sm text-text-secondary">
                  <span class="text-accent-success font-medium">A:</span> {{ cl.answer }}
                </p>
              </div>
            }
          </div>
        </div>
      }
    </div>
  `,
  styles: [],
})
export class BriefEditorComponent implements OnInit, OnDestroy {
  briefContent = '';
  private _lastSavedContent = '';
  get hasUnsavedChanges(): boolean {
    return this.briefContent.trim() !== this._lastSavedContent.trim();
  }

  isAnalyzing = false;
  isRewriting = false;
  isFreezing = false;
  saveStatus: 'idle' | 'saving' | 'saved' = 'idle';
  successMessage = '';
  errorMessage = '';
  analysisResult: any = null;

  clarifications: any[] = [];

  // Single brief info (1 version = 1 brief, status = progress)
  briefInfo: any = null;
  get isFrozen(): boolean {
    return this.briefInfo?.status === 'frozen';
  }

  // Dynamic version từ PipelineStore
  get activeVersion(): string {
    return this.pipelineStore.getActiveVersion() || '';
  }

  private api = inject(ApiService);
  private pipelineStore = inject(PipelineStore);
  private cdr = inject(ChangeDetectorRef);
  private router = inject(Router);
  private saveTimer: any = null;

  async ngOnInit(): Promise<void> {
    await this.pipelineStore.loadStatus();
    await this.loadBrief();
    this.cdr.detectChanges();
  }

  ngOnDestroy(): void {
    if (this.saveTimer) {
      clearTimeout(this.saveTimer);
    }
  }

  // ============================================================================
  // Load single brief (1 version = 1 brief)
  // ============================================================================

  async loadBrief(): Promise<void> {
    const result = await this.api.getBrief(this.activeVersion);
    if (result.success && result.data) {
      this.briefInfo = result.data;
      this.briefContent = result.data.content || '';
      this._lastSavedContent = this.briefContent;
      this.clarifications = result.data.clarifications || [];
    }
  }

  // ============================================================================
  // Auto-save
  // ============================================================================

  onContentChange(): void {
    this.saveStatus = 'idle';
    if (this.saveTimer) {
      clearTimeout(this.saveTimer);
    }
    this.saveTimer = setTimeout(() => {
      this.autoSave();
    }, 2000);
  }

  async autoSave(): Promise<void> {
    if (!this.briefContent.trim() || this.isFrozen) {
      return;
    }

    this.saveStatus = 'saving';
    try {
      const result = await this.api.saveBrief({
        version: this.activeVersion,
        brief_content: this.briefContent,
      });

      if (result.success) {
        this._lastSavedContent = this.briefContent;
        this.saveStatus = 'saved';
        setTimeout(() => {
          if (this.saveStatus === 'saved' && !this.hasUnsavedChanges) {
            this.saveStatus = 'idle';
          }
        }, 3000);
      } else {
        this.errorMessage = result.error?.message || 'Lưu thất bại';
        this.saveStatus = 'idle';
      }
    } catch {
      this.saveStatus = 'idle';
    }
  }

  // ============================================================================
  // Actions: Analyze, Rewrite, Freeze
  // ============================================================================

  async handleAnalyze(): Promise<void> {
    if (!this.briefContent.trim()) {
      this.errorMessage = 'Vui lòng nhập brief';
      return;
    }
    if (this.hasUnsavedChanges) {
      await this.autoSave();
    }

    this.isAnalyzing = true;
    this.successMessage = '';
    this.errorMessage = '';

    try {
      const result = await this.api.analyzeBrief({
        brief_content: this.briefContent,
        version: this.activeVersion,
      });

      if (result.success && result.data) {
        this.analysisResult = result.data;
        this.successMessage = 'Phân tích thành công';
        await this.loadBrief();
      } else {
        this.errorMessage = result.error?.message || 'Phân tích thất bại';
      }
    } finally {
      this.isAnalyzing = false;
    }
  }

  async handleRewrite(): Promise<void> {
    if (!this.briefContent.trim()) {
      this.errorMessage = 'Vui lòng nhập brief';
      return;
    }

    this.isRewriting = true;
    this.successMessage = '';
    this.errorMessage = '';

    try {
      const result = await this.api.rewriteBrief(this.briefContent);

      if (result.success && result.data?.content) {
        this.briefContent = result.data.content;
        this._lastSavedContent = result.data.content;
        this.successMessage = 'Viết lại brief thành công';
        await this.loadBrief();
      } else {
        this.errorMessage = result.error?.message || 'Viết lại thất bại';
      }
    } finally {
      this.isRewriting = false;
    }
  }

  async handleFreeze(): Promise<void> {
    this.isFreezing = true;
    this.successMessage = '';
    this.errorMessage = '';

    try {
      const result = await this.api.freezeBrief(this.activeVersion);

      if (result.success) {
        this.successMessage = 'Brief đã được đóng (frozen), sẵn sàng cho contract gen';
        await this.loadBrief();
      } else {
        this.errorMessage = result.error?.message || 'Không thể đóng brief';
      }
    } finally {
      this.isFreezing = false;
    }
  }

  // ============================================================================
  // Badge styling
  // ============================================================================

  getStatusBadgeClass(status: string): string {
    const map: Record<string, string> = {
      draft: 'bg-yellow-900 bg-opacity-40 text-yellow-300 border border-yellow-700',
      clarified: 'bg-green-900 bg-opacity-40 text-green-300 border border-green-700',
      frozen: 'bg-red-900 bg-opacity-40 text-red-300 border border-red-700',
      archived: 'bg-gray-900 bg-opacity-40 text-gray-400 border border-gray-700',
    };
    return map[status] || 'bg-bg-secondary text-text-tertiary border border-border-primary';
  }
}
