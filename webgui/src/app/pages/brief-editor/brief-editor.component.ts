/**
 * Component Brief Editor
 * 1 version = 1 brief duy nhất, status = progress (draft → clarified → frozen → archived)
 * Auto-save + phân tích + clarification history + change log
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
      <!-- Toast Notification -->
      @if (toast.show) {
        <div class="fixed top-16 right-4 z-50 animate-slide-in pointer-events-none">
          <div class="pointer-events-auto flex items-center gap-3 px-5 py-3.5 rounded-lg shadow-2xl"
               [ngClass]="toast.type === 'success'
                 ? 'bg-green-600 border border-green-400'
                 : 'bg-red-600 border border-red-400'">
            <!-- Icon -->
            @if (toast.type === 'success') {
              <svg class="h-5 w-5 text-green-100 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
            } @else {
              <svg class="h-5 w-5 text-red-100 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
              </svg>
            }
            <span class="font-semibold text-sm text-white">
              {{ toast.message }}
            </span>
            <button (click)="toast.show = false" class="ml-1 opacity-60 hover:opacity-100 transition-opacity">
              <svg class="h-4 w-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
              </svg>
            </button>
          </div>
        </div>
      }

      <!-- Header -->
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold">Brief Editor</h1>
          <p class="text-text-secondary mt-1">Viết brief cho project của bạn</p>

          <!-- Status Badges + Version -->
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
              <svg class="mr-2 h-4 w-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
              </svg>
              Đã lưu
            } @else if (hasUnsavedChanges) {
              <span class="text-yellow-400">● Có thay đổi chưa lưu</span>
            }
          </span>

          <!-- Rewrite Button -->
          @if (briefInfo && briefInfo.status !== 'frozen') {
            <button (click)="handleRewrite()" class="btn btn-secondary" [disabled]="isRewriting || isAnalyzing || !briefContent.trim()">
              {{ isRewriting ? '⏳ Đang xử lý...' : '✏️ Viết lại' }}
            </button>
          }

          <!-- Freeze Button - chỉ hiện khi status === clarified -->
          @if (briefInfo && briefInfo.status === 'clarified') {
            <button (click)="handleFreeze()" class="btn btn-secondary" [disabled]="isFreezing">
              {{ isFreezing ? '⏳ Đang xử lý...' : '🔒 Đóng (Freeze)' }}
            </button>
          }

          <!-- Analyze Button - chỉ hiện khi status !== frozen -->
          @if (!briefInfo || briefInfo.status !== 'frozen') {
            <button (click)="handleAnalyze()" class="btn btn-primary" [disabled]="isAnalyzing || !briefContent.trim()">
              {{ isAnalyzing ? '⏳ Đang phân tích...' : '🔍 Phân tích' }}
            </button>
          } @else {
            <span class="text-xs text-text-tertiary italic">Brief đã được đóng</span>
          }

          <!-- History Toggle -->
          <button (click)="toggleHistory()" class="btn btn-secondary text-xs" [disabled]="isFrozen">
            📋 Lịch sử
          </button>
        </div>
      </div>

      <!-- Frozen Banner -->
      @if (briefInfo && briefInfo.status === 'frozen') {
        <div class="mb-4 p-3 bg-orange-900 bg-opacity-30 border border-orange-500 rounded">
          <span class="text-orange-300 font-semibold">🔒 Brief đã đóng (frozen)</span>
          <span class="text-orange-200 text-sm ml-2">— không thể chỉnh sửa. Tạo version mới để inherit.</span>
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
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold">📊 Kết quả phân tích</h2>
            <div class="flex items-center gap-2">
              <span class="text-xs px-2 py-1 rounded font-medium"
                    [class]="analysisResult.status === 'needs_clarification'
                      ? 'bg-yellow-900 bg-opacity-40 text-yellow-300 border border-yellow-700'
                      : 'bg-green-900 bg-opacity-40 text-green-300 border border-green-700'">
                {{ analysisResult.status === 'needs_clarification' ? '⚠️ Cần clarify' : '✅ Sẵn sàng contract' }}
              </span>
              @if (analysisResult?.metadata?.brief_id) {
                <span class="text-xs text-text-tertiary font-mono">{{ analysisResult.metadata.brief_id }}</span>
              }
            </div>
          </div>

          <!-- Summary -->
          @if (analysisResult?.analysis?.summary) {
            <div class="mb-4 p-3 bg-blue-900 bg-opacity-20 rounded border-l-4 border-blue-400">
              <p class="text-sm text-blue-200">{{ analysisResult.analysis.summary }}</p>
            </div>
          }

          <!-- Intent + Confidence -->
          <div class="mb-4 grid grid-cols-4 gap-4">
            <div>
              <span class="text-text-tertiary text-xs">Domain</span>
              <p class="text-sm font-medium">{{ analysisResult?.analysis?.intent?.domain }}</p>
            </div>
            <div>
              <span class="text-text-tertiary text-xs">Type</span>
              <p class="text-sm font-medium">{{ analysisResult?.analysis?.intent?.type }}</p>
            </div>
            <div>
              <span class="text-text-tertiary text-xs">Scale</span>
              <p class="text-sm font-medium">{{ analysisResult?.analysis?.intent?.scale }}</p>
            </div>
            <div>
              <span class="text-text-tertiary text-xs">Confidence</span>
              <div class="flex items-center gap-2">
                <div class="flex-1 h-2 bg-bg-secondary rounded-full overflow-hidden">
                  <div class="h-full rounded-full transition-all duration-500"
                       [class]="analysisResult?.metadata?.confidence >= 0.8
                         ? 'bg-green-400'
                         : analysisResult?.metadata?.confidence >= 0.5
                           ? 'bg-yellow-400'
                           : 'bg-red-400'"
                       [style.width.%]="analysisResult?.metadata?.confidence * 100"></div>
                </div>
                <span class="text-sm font-medium"
                      [class]="analysisResult?.metadata?.confidence >= 0.8
                        ? 'text-green-300'
                        : analysisResult?.metadata?.confidence >= 0.5
                          ? 'text-yellow-300'
                          : 'text-red-300'">
                  {{ (analysisResult?.metadata?.confidence * 100).toFixed(0) }}%
                </span>
              </div>
            </div>
          </div>

          <!-- Extracted Resources Grid -->
          <div class="mb-4">
            <h3 class="font-medium text-accent-primary mb-2">📦 Resources extracted</h3>
            <div class="grid grid-cols-5 gap-3">
              <div class="p-3 bg-bg-secondary rounded text-center border border-border-primary">
                <p class="text-2xl font-bold text-blue-400">{{ analysisResult?.metadata?.entities }}</p>
                <p class="text-xs text-text-tertiary mt-1">Entities</p>
              </div>
              <div class="p-3 bg-bg-secondary rounded text-center border border-border-primary">
                <p class="text-2xl font-bold text-orange-400">{{ analysisResult?.metadata?.commands }}</p>
                <p class="text-xs text-text-tertiary mt-1">Commands</p>
              </div>
              <div class="p-3 bg-bg-secondary rounded text-center border border-border-primary">
                <p class="text-2xl font-bold text-cyan-400">{{ analysisResult?.metadata?.queries }}</p>
                <p class="text-xs text-text-tertiary mt-1">Queries</p>
              </div>
              <div class="p-3 bg-bg-secondary rounded text-center border border-border-primary">
                <p class="text-2xl font-bold text-purple-400">{{ analysisResult?.metadata?.events }}</p>
                <p class="text-xs text-text-tertiary mt-1">Events</p>
              </div>
              <div class="p-3 bg-bg-secondary rounded text-center border border-border-primary">
                <p class="text-2xl font-bold text-teal-400">{{ analysisResult?.metadata?.ui_components }}</p>
                <p class="text-xs text-text-tertiary mt-1">UI Components</p>
              </div>
            </div>
          </div>

          <!-- Ambiguities -->
          @if (analysisResult?.analysis?.ambiguities?.length) {
            <div class="mb-4">
              <h3 class="font-medium text-yellow-400 mb-2">⚠️ Ambiguities ({{ analysisResult?.analysis?.ambiguities?.length }})</h3>
              <div class="space-y-2">
                @for (ambiguity of analysisResult?.analysis?.ambiguities; track ambiguity.id) {
                  <div class="p-3 bg-yellow-900 bg-opacity-10 rounded border-l-2 border-yellow-500">
                    <p class="text-sm text-text-primary"><strong>{{ ambiguity.type }}:</strong> {{ ambiguity.description }}</p>
                    <p class="text-sm text-text-tertiary mt-1">{{ ambiguity.source_text }}</p>
                  </div>
                }
              </div>
            </div>
          }

          <!-- Next Action -->
          <div class="mt-4 flex justify-end gap-3">
            @if (analysisResult?.status === 'needs_clarification') {
              <a routerLink="/clarification" class="btn btn-primary">
                Làm rõ yêu cầu →
              </a>
            } @else {
              <a routerLink="/contract-viewer" class="btn btn-primary">
                Generate Contract →
              </a>
            }
          </div>
        </div>
      }

      <!-- Clarification History -->
      @if (clarifications.length > 0) {
        <div class="card mt-6">
          <h2 class="text-lg font-semibold mb-4">💬 Lịch sử Clarification ({{ clarifications.length }})</h2>
          <div class="space-y-4">
            @for (cl of clarifications; track cl.id) {
              <div class="p-4 bg-bg-secondary rounded border-l-2" [class]="cl.is_memo ? 'border-yellow-500' : 'border-border-primary'">
                <div class="flex items-start justify-between mb-2">
                  <span class="text-xs font-mono text-text-tertiary">Round {{ cl.round }}</span>
                  @if (cl.is_memo) {
                    <span class="text-xs bg-yellow-900 bg-opacity-40 text-yellow-300 px-2 py-0.5 rounded">Memo</span>
                  }
                </div>
                <p class="text-sm text-text-primary mb-2">
                  <span class="text-blue-400 font-medium">Q:</span> {{ cl.question }}
                </p>
                <p class="text-sm text-text-secondary">
                  <span class="text-green-400 font-medium">A:</span> {{ cl.answer }}
                </p>
              </div>
            }
          </div>
        </div>
      }

      <!-- Change History (Lineage) -->
      @if (showHistory && lineage.length > 0) {
        <div class="card mt-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold">📋 Lịch sử thay đổi ({{ lineage.length }})</h2>
            <button (click)="showHistory = false" class="text-xs text-text-tertiary hover:text-text-primary">✕ Đóng</button>
          </div>
          <div class="space-y-2">
            @for (entry of lineage; track entry.id) {
              <div class="p-3 bg-bg-secondary rounded flex items-center gap-4">
                <span class="text-xs font-mono text-text-tertiary whitespace-nowrap">{{ entry.created_at || '' }}</span>
                <span class="text-xs px-2 py-0.5 rounded font-medium"
                      [class]="entry.change_type === 'created'
                        ? 'bg-green-900 bg-opacity-40 text-green-300 border border-green-700'
                        : entry.change_type === 'content_update'
                          ? 'bg-blue-900 bg-opacity-40 text-blue-300 border border-blue-700'
                          : entry.change_type === 'frozen'
                            ? 'bg-red-900 bg-opacity-40 text-red-300 border border-red-700'
                            : 'bg-gray-900 bg-opacity-40 text-gray-300 border border-gray-700'">
                  {{ entry.change_type }}
                </span>
                <span class="text-sm text-text-secondary flex-1">{{ entry.change_description }}</span>
              </div>
            }
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    .animate-slide-in {
      animation: slideIn 0.3s ease-out;
    }
  `],
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
  analysisResult: any = null;

  clarifications: any[] = [];
  lineage: any[] = [];
  showHistory = false;

  // Single brief info (1 version = 1 brief, status = progress)
  briefInfo: any = null;
  get isFrozen(): boolean {
    return this.briefInfo?.status === 'frozen';
  }

  // Dynamic version từ PipelineStore
  get activeVersion(): string {
    return this.pipelineStore.getActiveVersion() || '';
  }

  // Toast notification
  toast = { show: false, message: '', type: 'success' as 'success' | 'error' };

  private api = inject(ApiService);
  private pipelineStore = inject(PipelineStore);
  private cdr = inject(ChangeDetectorRef);
  private router = inject(Router);
  private saveTimer: any = null;
  private toastTimer: any = null;

  async ngOnInit(): Promise<void> {
    await this.pipelineStore.loadStatus();
    await this.loadBrief();
    await this.loadLineage();
    this.cdr.detectChanges();
  }

  ngOnDestroy(): void {
    if (this.saveTimer) clearTimeout(this.saveTimer);
    if (this.toastTimer) clearTimeout(this.toastTimer);
  }

  // ============================================================================
  // Toast
  // ============================================================================

  showToast(message: string, type: 'success' | 'error' = 'success'): void {
    this.toast = { show: true, message, type };
    this.cdr.detectChanges();
    if (this.toastTimer) clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => {
      this.toast.show = false;
      this.cdr.detectChanges();
    }, 4000);
  }

  // ============================================================================
  // Load brief + lineage
  // ============================================================================

  async loadBrief(): Promise<void> {
    const result = await this.api.getBrief(this.activeVersion);
    if (result.success && result.data) {
      this.briefInfo = result.data;
      this.briefContent = result.data.content || '';
      this._lastSavedContent = this.briefContent;
      this.clarifications = result.data.clarifications || [];
      // Restore analysis result from backend (persisted in artifacts table)
      this.analysisResult = result.data.analysis || null;
    }
  }

  async loadLineage(): Promise<void> {
    const result = await this.api.getBriefLineage(this.activeVersion);
    if (result.success && result.data?.lineage) {
      this.lineage = result.data.lineage;
    }
  }

  toggleHistory(): void {
    this.showHistory = !this.showHistory;
    this.cdr.detectChanges();
  }

  // ============================================================================
  // Auto-save
  // ============================================================================

  onContentChange(): void {
    this.saveStatus = 'idle';
    if (this.saveTimer) clearTimeout(this.saveTimer);
    this.saveTimer = setTimeout(() => {
      this.autoSave();
    }, 2000);
  }

  async autoSave(): Promise<void> {
    if (!this.briefContent.trim() || this.isFrozen) return;

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
      this.showToast('Vui lòng nhập brief', 'error');
      return;
    }
    if (this.hasUnsavedChanges) await this.autoSave();

    this.isAnalyzing = true;
    this.cdr.detectChanges();

    // Timeout safety net: 2 phút max
    const timeoutId = setTimeout(() => {
      if (this.isAnalyzing) {
        this.isAnalyzing = false;
        this.showToast('Phân tích quá lâu, vui lòng thử lại', 'error');
        this.cdr.detectChanges();
      }
    }, 120000);

    try {
      const result = await this.api.analyzeBrief({
        brief_content: this.briefContent,
        version: this.activeVersion,
      });
      clearTimeout(timeoutId);

      if (result.success && result.data) {
        this.analysisResult = result.data;
        await this.loadBrief();
        await this.loadLineage();
        this.showToast('Phân tích thành công! Đã extract ' + (result.data.metadata?.entities || 0) + ' entities', 'success');
      } else {
        this.showToast(result.error?.message || 'Phân tích thất bại', 'error');
      }
    } catch (e) {
      clearTimeout(timeoutId);
      this.showToast('Lỗi kết nối server', 'error');
    } finally {
      this.isAnalyzing = false;
      this.cdr.detectChanges();
    }
  }

  async handleRewrite(): Promise<void> {
    if (!this.briefContent.trim()) {
      this.showToast('Vui lòng nhập brief', 'error');
      return;
    }

    this.isRewriting = true;
    this.cdr.detectChanges();

    try {
      const result = await this.api.rewriteBrief(this.briefContent);

      if (result.success && result.data?.content) {
        this.briefContent = result.data.content;
        this._lastSavedContent = result.data.content;
        this.showToast('Viết lại brief thành công', 'success');
        await this.loadBrief();
      } else {
        this.showToast(result.error?.message || 'Viết lại thất bại', 'error');
      }
    } catch {
      this.showToast('Lỗi kết nối server', 'error');
    } finally {
      this.isRewriting = false;
      this.cdr.detectChanges();
    }
  }

  async handleFreeze(): Promise<void> {
    this.isFreezing = true;
    this.cdr.detectChanges();

    try {
      const result = await this.api.freezeBrief(this.activeVersion);

      if (result.success) {
        this.showToast('Brief đã được đóng (frozen)', 'success');
        await this.loadBrief();
      } else {
        this.showToast(result.error?.message || 'Không thể đóng brief', 'error');
      }
    } catch {
      this.showToast('Lỗi kết nối server', 'error');
    } finally {
      this.isFreezing = false;
      this.cdr.detectChanges();
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
