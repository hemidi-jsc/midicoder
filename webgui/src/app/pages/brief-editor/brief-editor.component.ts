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

interface SectionOpenState {
  entities: boolean;
  commands: boolean;
  queries: boolean;
  events: boolean;
  ui_components: boolean;
}

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
        <div class="card mt-6 analysis-card">
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
              <span class="text-text-secondary text-xs">Domain</span>
              <p class="text-sm font-medium text-text-primary">{{ analysisResult?.analysis?.intent?.domain }}</p>
            </div>
            <div>
              <span class="text-text-secondary text-xs">Type</span>
              <p class="text-sm font-medium text-text-primary">{{ analysisResult?.analysis?.intent?.type }}</p>
            </div>
            <div>
              <span class="text-text-secondary text-xs">Scale</span>
              <p class="text-sm font-medium text-text-primary">{{ analysisResult?.analysis?.intent?.scale }}</p>
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
                <p class="text-xs text-text-secondary mt-1">Entities</p>
              </div>
              <div class="p-3 bg-bg-secondary rounded text-center border border-border-primary">
                <p class="text-2xl font-bold text-orange-400">{{ analysisResult?.metadata?.commands }}</p>
                <p class="text-xs text-text-secondary mt-1">Commands</p>
              </div>
              <div class="p-3 bg-bg-secondary rounded text-center border border-border-primary">
                <p class="text-2xl font-bold text-cyan-400">{{ analysisResult?.metadata?.queries }}</p>
                <p class="text-xs text-text-secondary mt-1">Queries</p>
              </div>
              <div class="p-3 bg-bg-secondary rounded text-center border border-border-primary">
                <p class="text-2xl font-bold text-purple-400">{{ analysisResult?.metadata?.events }}</p>
                <p class="text-xs text-text-secondary mt-1">Events</p>
              </div>
              <div class="p-3 bg-bg-secondary rounded text-center border border-border-primary">
                <p class="text-2xl font-bold text-teal-400">{{ analysisResult?.metadata?.ui_components }}</p>
                <p class="text-xs text-text-secondary mt-1">UI Components</p>
              </div>
            </div>
          </div>

          <!-- Collapsible: Raw Details -->
          <div class="mb-4 space-y-3">
            <!-- Entities -->
            @if (analysisResult?.analysis?.entities?.length) {
              <div class="border border-border-primary rounded overflow-hidden">
                <button (click)="toggleSection('entities')" class="w-full flex items-center justify-between p-3 bg-bg-secondary hover:bg-bg-tertiary transition-colors">
                  <span class="font-medium text-sm text-text-primary">📋 Entities ({{ analysisResult.analysis.entities.length }})</span>
                  <svg class="h-4 w-4 text-text-secondary transition-transform" [class.rotate-180]="sectionOpen.entities" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                </button>
                @if (sectionOpen.entities) {
                  <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                      <thead class="bg-bg-secondary text-text-tertiary text-xs uppercase">
                        <tr><th class="px-4 py-2 text-left">Name</th><th class="px-4 py-2 text-left">Type</th><th class="px-4 py-2 text-left">Description</th></tr>
                      </thead>
                      <tbody>
                        @for (e of analysisResult.analysis.entities; track e.name) {
                          <tr class="border-t border-border-primary">
                            <td class="px-4 py-2 font-medium text-blue-400">{{ e.name }}</td>
                            <td class="px-4 py-2 text-text-tertiary">{{ e.type || '—' }}</td>
                            <td class="px-4 py-2 text-text-secondary">{{ e.description || '—' }}</td>
                          </tr>
                        }
                      </tbody>
                    </table>
                  </div>
                }
              </div>
            }

            <!-- Commands -->
            @if (analysisResult?.analysis?.commands?.length) {
              <div class="border border-border-primary rounded overflow-hidden">
                <button (click)="toggleSection('commands')" class="w-full flex items-center justify-between p-3 bg-bg-secondary hover:bg-bg-tertiary transition-colors">
                  <span class="font-medium text-sm text-text-primary">⚡ Commands ({{ analysisResult.analysis.commands.length }})</span>
                  <svg class="h-4 w-4 text-text-secondary transition-transform" [class.rotate-180]="sectionOpen.commands" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                </button>
                @if (sectionOpen.commands) {
                  <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                      <thead class="bg-bg-secondary text-text-tertiary text-xs uppercase">
                        <tr><th class="px-4 py-2 text-left">Name</th><th class="px-4 py-2 text-left">Target</th><th class="px-4 py-2 text-left">Description</th></tr>
                      </thead>
                      <tbody>
                        @for (c of analysisResult.analysis.commands; track c.name) {
                          <tr class="border-t border-border-primary">
                            <td class="px-4 py-2 font-medium text-orange-400">{{ c.name }}</td>
                            <td class="px-4 py-2 text-text-tertiary">{{ c.target || '—' }}</td>
                            <td class="px-4 py-2 text-text-secondary">{{ c.description || '—' }}</td>
                          </tr>
                        }
                      </tbody>
                    </table>
                  </div>
                }
              </div>
            }

            <!-- Queries -->
            @if (analysisResult?.analysis?.queries?.length) {
              <div class="border border-border-primary rounded overflow-hidden">
                <button (click)="toggleSection('queries')" class="w-full flex items-center justify-between p-3 bg-bg-secondary hover:bg-bg-tertiary transition-colors">
                  <span class="font-medium text-sm text-text-primary">🔍 Queries ({{ analysisResult.analysis.queries.length }})</span>
                  <svg class="h-4 w-4 text-text-secondary transition-transform" [class.rotate-180]="sectionOpen.queries" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                </button>
                @if (sectionOpen.queries) {
                  <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                      <thead class="bg-bg-secondary text-text-tertiary text-xs uppercase">
                        <tr><th class="px-4 py-2 text-left">Name</th><th class="px-4 py-2 text-left">Entity</th><th class="px-4 py-2 text-left">Filter</th></tr>
                      </thead>
                      <tbody>
                        @for (q of analysisResult.analysis.queries; track q.name) {
                          <tr class="border-t border-border-primary">
                            <td class="px-4 py-2 font-medium text-cyan-400">{{ q.name }}</td>
                            <td class="px-4 py-2 text-text-tertiary">{{ q.entity || '—' }}</td>
                            <td class="px-4 py-2 text-text-secondary">{{ q.filter || '—' }}</td>
                          </tr>
                        }
                      </tbody>
                    </table>
                  </div>
                }
              </div>
            }

            <!-- Events -->
            @if (analysisResult?.analysis?.events?.length) {
              <div class="border border-border-primary rounded overflow-hidden">
                <button (click)="toggleSection('events')" class="w-full flex items-center justify-between p-3 bg-bg-secondary hover:bg-bg-tertiary transition-colors">
                  <span class="font-medium text-sm text-text-primary">🔔 Events ({{ analysisResult.analysis.events.length }})</span>
                  <svg class="h-4 w-4 text-text-secondary transition-transform" [class.rotate-180]="sectionOpen.events" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                </button>
                @if (sectionOpen.events) {
                  <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                      <thead class="bg-bg-secondary text-text-tertiary text-xs uppercase">
                        <tr><th class="px-4 py-2 text-left">Name</th><th class="px-4 py-2 text-left">Source</th><th class="px-4 py-2 text-left">Description</th></tr>
                      </thead>
                      <tbody>
                        @for (ev of analysisResult.analysis.events; track ev.name) {
                          <tr class="border-t border-border-primary">
                            <td class="px-4 py-2 font-medium text-purple-400">{{ ev.name }}</td>
                            <td class="px-4 py-2 text-text-tertiary">{{ ev.source || '—' }}</td>
                            <td class="px-4 py-2 text-text-secondary">{{ ev.description || '—' }}</td>
                          </tr>
                        }
                      </tbody>
                    </table>
                  </div>
                }
              </div>
            }

            <!-- UI Components -->
            @if (analysisResult?.analysis?.ui_components?.length) {
              <div class="border border-border-primary rounded overflow-hidden">
                <button (click)="toggleSection('ui_components')" class="w-full flex items-center justify-between p-3 bg-bg-secondary hover:bg-bg-tertiary transition-colors">
                  <span class="font-medium text-sm text-text-primary">🎨 UI Components ({{ analysisResult.analysis.ui_components.length }})</span>
                  <svg class="h-4 w-4 text-text-secondary transition-transform" [class.rotate-180]="sectionOpen.ui_components" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                </button>
                @if (sectionOpen.ui_components) {
                  <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                      <thead class="bg-bg-secondary text-text-tertiary text-xs uppercase">
                        <tr><th class="px-4 py-2 text-left">Name</th><th class="px-4 py-2 text-left">Type</th><th class="px-4 py-2 text-left">Description</th></tr>
                      </thead>
                      <tbody>
                        @for (uc of analysisResult.analysis.ui_components; track uc.name) {
                          <tr class="border-t border-border-primary">
                            <td class="px-4 py-2 font-medium text-teal-400">{{ uc.name }}</td>
                            <td class="px-4 py-2 text-text-tertiary">{{ uc.type || '—' }}</td>
                            <td class="px-4 py-2 text-text-secondary">{{ uc.description || '—' }}</td>
                          </tr>
                        }
                      </tbody>
                    </table>
                  </div>
                }
              </div>
            }
          </div>

          <!-- Ambiguities -->
          @if (analysisResult?.analysis?.ambiguities?.length) {
            <div class="mb-4">
              <h3 class="font-medium text-yellow-400 mb-2">⚠️ Ambiguities ({{ analysisResult?.analysis?.ambiguities?.length }})</h3>
              <div class="space-y-2">
                @for (ambiguity of analysisResult?.analysis?.ambiguities; track ambiguity.id) {
                  <div class="p-3 bg-yellow-900 bg-opacity-20 rounded border-l-2 border-yellow-500">
                    <p class="text-sm text-text-primary"><strong>{{ ambiguity.type }}:</strong> {{ ambiguity.description }}</p>
                    <p class="text-sm text-text-secondary mt-1">{{ ambiguity.source_text }}</p>
                  </div>
                }
              </div>
            </div>
          }

          <!-- Next Action -->
          <div class="mt-4 flex justify-end gap-3">
            @if (analysisResult?.status === 'needs_clarification') {
              @if (!clarificationActive) {
                <button (click)="startBatchClarification()" class="btn btn-primary" [disabled]="isStartingClarification">
                  {{ isStartingClarification ? '⏳ Đang bắt đầu...' : '💬 Làm rõ yêu cầu →' }}
                </button>
              }
            } @else {
              <a routerLink="/contract-viewer" class="btn btn-primary">
                Generate Contract →
              </a>
            }
          </div>

          <!-- Clarification Batch Section -->
          @if (clarificationActive) {
            <div class="clarification-batch-section">
              <div class="clarification-batch-header">
                <h3 class="clarification-batch-title">💬 Làm rõ các điểm chưa rõ</h3>
                <p class="clarification-batch-subtitle">{{ clarificationAmbiguities.length }} điểm cần làm rõ — hãy điền câu trả lời cho từng mục</p>
              </div>

              <div class="clarification-batch-questions">
                @for (amb of clarificationAmbiguities; track amb.id || amb.type) {
                  <div class="clarification-ambiguity-card"
                       [class.answered]="clarificationAnswers[amb.id || amb.type]?.trim()">
                    <div class="ambiguity-badge-wrapper">
                      <span class="ambiguity-type-badge"
                            [class]="amb.type === 'undefined_behavior' ? 'amb-undefined' : amb.type === 'missing_detail' ? 'amb-missing' : 'amb-tech'">
                        {{ amb.type }}
                      </span>
                      @if (clarificationAnswers[amb.id || amb.type]?.trim()) {
                        <span class="ambiguity-checked">✓</span>
                      }
                    </div>
                    <p class="ambiguity-description">{{ amb.description }}</p>
                    @if (amb.source_text) {
                      <p class="ambiguity-source">"— {{ amb.source_text }}"</p>
                    }
                    <textarea
                      [(ngModel)]="clarificationAnswers[amb.id || amb.type]"
                      placeholder="Điền câu trả lời của bạn..."
                      rows="2"
                      class="ambiguity-textarea"
                    ></textarea>
                  </div>
                }
              </div>

              <!-- Progress bar -->
              <div class="clarification-progress-bar">
                <div class="clarification-progress-fill" [style.width.%]="clarificationProgressPct"></div>
              </div>
              <p class="clarification-progress-text">{{ answeredCount }}/{{ clarificationAmbiguities.length }} câu đã trả lời</p>

              <!-- Submit button -->
              <div class="clarification-submit-row">
                <button (click)="cancelClarification()" class="clarification-cancel-btn">Hủy</button>
                <button (click)="submitBatchAnswers()" class="btn btn-primary clarification-submit-btn"
                        [disabled]="answeredCount < clarificationAmbiguities.length || isSubmittingAnswers">
                  @if (isSubmittingAnswers) {
                    ⏳ Đang gửi...
                  } @else {
                    ✅ Gửi tất cả ({{ answeredCount }}/{{ clarificationAmbiguities.length }})
                  }
                </button>
              </div>
            </div>
          }
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
    </div>

    <!-- History Modal Overlay -->
    @if (showHistory) {
      <div class="history-overlay" (click)="showHistory = false">
        <div class="history-backdrop"></div>
        <div class="history-modal" (click)="$event.stopPropagation()">
          <!-- Header -->
          <div class="history-header">
            <div>
              <h2 class="text-xl font-semibold text-white">📋 Lịch sử thay đổi</h2>
              @if (lineage.length > 0) {
                <p class="text-sm text-text-secondary mt-1">{{ lineage.length }} thay đổi đã được ghi nhận</p>
              }
            </div>
            <button (click)="showHistory = false" class="text-text-secondary hover:text-white text-2xl leading-none px-2 py-1 rounded hover:bg-bg-secondary transition-colors close-btn" type="button">✕</button>
          </div>
          <!-- Body -->
          <div class="history-body">
            @if (lineage.length === 0) {
              <div class="text-center py-16">
                <p class="text-4xl mb-3">📝</p>
                <p class="text-text-secondary text-base">Chưa có lịch sử thay đổi nào</p>
                <p class="text-text-tertiary text-sm mt-1">Lịch sử sẽ tự động ghi nhận khi bạn chỉnh sửa brief</p>
              </div>
            }
            @for (entry of lineage; track entry.id; let idx = $index) {
              <div class="history-entry">
                <!-- Timeline dot -->
                <div class="history-dot-col">
                  <div class="history-dot"
                       [class]="entry.change_type === 'created'
                         ? 'dot-green'
                         : entry.change_type === 'content_update'
                           ? 'dot-blue'
                           : entry.change_type === 'status_change'
                             ? 'dot-purple'
                             : entry.change_type === 'frozen'
                               ? 'dot-red'
                               : 'dot-gray'">
                  </div>
                  @if (idx < lineage.length - 1) {
                    <div class="history-line"></div>
                  }
                </div>
                <!-- Content -->
                <div class="history-entry-content">
                  <div class="history-entry-meta">
                    <span class="history-badge"
                          [class]="entry.change_type === 'created'
                            ? 'badge-green'
                            : entry.change_type === 'content_update'
                              ? 'badge-blue'
                              : entry.change_type === 'status_change'
                                ? 'badge-purple'
                                : entry.change_type === 'frozen'
                                  ? 'badge-red'
                                  : 'badge-gray'">
                      {{ entry.change_type }}
                    </span>
                    <span class="text-xs font-mono text-text-secondary">{{ entry.created_at || '' }}</span>
                  </div>
                  <p class="history-description">{{ entry.change_description }}</p>
                  @if (entry.old_content_hash && entry.new_content_hash) {
                    @if (entry.change_type === 'content_update' && entry.old_content_hash !== entry.new_content_hash) {
                      <div class="history-hash-row">
                        <span class="text-xs font-mono text-orange-300 bg-orange-900/30 px-2 py-1 rounded">
                          {{ entry.old_content_hash | slice:0:8 }}
                        </span>
                        <svg class="w-3 h-3 text-text-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/></svg>
                        <span class="text-xs font-mono text-green-300 bg-green-900/30 px-2 py-1 rounded">
                          {{ entry.new_content_hash | slice:0:8 }}
                        </span>
                      </div>
                    } @else {
                      <span class="text-xs font-mono text-text-tertiary mt-1 inline-block">#{{ entry.new_content_hash | slice:0:8 }}</span>
                    }
                  }
                </div>
              </div>
            }
          </div>
          <!-- Footer -->
          @if (lineage.length > 0) {
            <div class="history-footer">
              <span class="text-xs text-text-tertiary">Cập nhật cuối: {{ lineage[0]?.created_at || 'unknown' }}</span>
              <button (click)="showHistory = false" class="btn btn-secondary text-xs">Đóng</button>
            </div>
          }
        </div>
      </div>
    }
  `,
  styles: [`
    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    .animate-slide-in {
      animation: slideIn 0.3s ease-out;
    }

    /* ---- Clarification Batch UI ---- */
    .clarification-batch-section {
      margin-top: 24px;
      padding: 24px;
      background: #14141f;
      border: 1px solid rgba(168, 85, 247, 0.3);
      border-radius: 12px;
    }
    .clarification-batch-header {
      margin-bottom: 20px;
    }
    .clarification-batch-title {
      font-size: 1.125rem;
      font-weight: 600;
      color: #fff;
      margin: 0 0 6px 0;
    }
    .clarification-batch-subtitle {
      font-size: 0.875rem;
      color: rgba(255, 255, 255, 0.5);
      margin: 0;
    }
    .clarification-batch-questions {
      display: flex;
      flex-direction: column;
      gap: 16px;
      margin-bottom: 20px;
    }
    .clarification-ambiguity-card {
      padding: 16px;
      background: #1a1a2e;
      border: 1px solid rgba(252, 103, 103, 0.12);
      border-radius: 8px;
      transition: all 0.2s;
    }
    .clarification-ambiguity-card.answered {
      border-color: rgba(63, 185, 80, 0.4);
      background: rgba(63, 185, 80, 0.05);
    }
    .ambiguity-badge-wrapper {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 10px;
    }
    .ambiguity-type-badge {
      font-size: 0.75rem;
      padding: 2px 10px;
      border-radius: 6px;
      font-weight: 600;
    }
    .amb-undefined {
      background: rgba(255, 166, 0, 0.2);
      color: #ffb74d;
      border: 1px solid rgba(255, 166, 0, 0.3);
    }
    .amb-missing {
      background: rgba(255, 82, 82, 0.2);
      color: #ff8a80;
      border: 1px solid rgba(255, 82, 82, 0.3);
    }
    .amb-tech {
      background: rgba(41, 121, 255, 0.2);
      color: #82b1ff;
      border: 1px solid rgba(41, 121, 255, 0.3);
    }
    .ambiguity-checked {
      color: #3fb950;
      font-size: 16px;
      font-weight: bold;
    }
    .ambiguity-description {
      font-size: 0.875rem;
      color: rgba(255, 255, 255, 0.85);
      line-height: 1.5;
      margin: 0 0 6px 0;
    }
    .ambiguity-source {
      font-size: 0.8rem;
      color: rgba(255, 255, 255, 0.4);
      font-style: italic;
      margin: 0 0 12px 0;
    }
    .ambiguity-textarea {
      width: 100%;
      padding: 10px 12px;
      background: rgba(10, 10, 15, 0.6);
      border: 1px solid rgba(252, 103, 103, 0.12);
      border-radius: 6px;
      color: #fff;
      font-size: 0.875rem;
      font-family: inherit;
      resize: vertical;
      line-height: 1.5;
      transition: border-color 0.2s;
    }
    .ambiguity-textarea:focus {
      outline: none;
      border-color: var(--brand-color);
      box-shadow: 0 0 0 2px rgba(252, 103, 103, 0.1);
    }
    .ambiguity-textarea::placeholder {
      color: rgba(255, 255, 255, 0.25);
    }
    .clarification-progress-bar {
      width: 100%;
      height: 4px;
      background: rgba(255, 255, 255, 0.06);
      border-radius: 2px;
      overflow: hidden;
      margin-bottom: 8px;
    }
    .clarification-progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #a855f7, #fc6767);
      border-radius: 2px;
      transition: width 0.3s ease;
    }
    .clarification-progress-text {
      font-size: 0.8rem;
      color: rgba(255, 255, 255, 0.4);
      text-align: center;
      margin: 0 0 16px 0;
    }
    .clarification-submit-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .clarification-cancel-btn {
      padding: 8px 16px;
      background: transparent;
      border: 1px solid rgba(252, 103, 103, 0.12);
      color: rgba(255, 255, 255, 0.5);
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.875rem;
      transition: all 0.2s;
    }
    .clarification-cancel-btn:hover {
      color: #fff;
      border-color: rgba(252, 103, 103, 0.3);
    }
    .clarification-submit-btn {
      min-width: 200px;
    }

    /* ---- History Modal ---- */
    .history-overlay {
      position: fixed;
      inset: 0;
      z-index: 9999;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .history-backdrop {
      position: absolute;
      inset: 0;
      background: rgba(0,0,0,0.7);
    }
    .history-modal {
      position: relative;
      z-index: 10000;
      width: 90%;
      max-width: 720px;
      max-height: 80vh;
      background: #14141f;
      border: 1px solid rgba(252,103,103,0.2);
      border-radius: 12px;
      box-shadow: 0 0 40px rgba(0,0,0,0.6);
      display: flex;
      flex-direction: column;
    }
    .history-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 20px 24px;
      border-bottom: 1px solid rgba(252,103,103,0.12);
    }
    .history-header h2 {
      font-size: 1.25rem;
      font-weight: 600;
      color: #fff;
      margin: 0;
    }
    .history-header p {
      font-size: 0.875rem;
      color: rgba(255,255,255,0.6);
      margin-top: 4px;
    }
    .close-btn {
      min-width: 32px;
      text-align: center;
    }
    .history-body {
      flex: 1;
      overflow-y: auto;
      padding: 20px 24px;
    }
    .history-entry {
      display: flex;
      gap: 16px;
      padding: 16px;
      background: #1a1a2e;
      border-radius: 8px;
      border: 1px solid rgba(252,103,103,0.12);
      margin-bottom: 12px;
      transition: border-color 0.2s;
    }
    .history-entry:hover {
      border-color: rgba(252,103,103,0.4);
    }
    .history-dot-col {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding-top: 2px;
    }
    .history-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      flex-shrink: 0;
    }
    .dot-green { background: #3fb950; box-shadow: 0 0 8px rgba(63,185,80,0.5); }
    .dot-blue  { background: #3884ff; box-shadow: 0 0 8px rgba(56,132,255,0.5); }
    .dot-purple{ background: #a855f7; box-shadow: 0 0 8px rgba(168,85,247,0.5); }
    .dot-red   { background: #f85149; box-shadow: 0 0 8px rgba(248,81,73,0.5); }
    .dot-gray  { background: #888; }
    .history-line {
      width: 1px;
      flex: 1;
      min-height: 20px;
      margin-top: 4px;
      background: rgba(252,103,103,0.12);
    }
    .history-entry-content {
      flex: 1;
      min-width: 0;
    }
    .history-entry-meta {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 6px;
      flex-wrap: wrap;
    }
    .history-description {
      font-size: 0.875rem;
      color: #fff;
      line-height: 1.6;
      margin: 0;
    }
    .history-hash-row {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 8px;
    }
    .history-badge {
      font-size: 0.75rem;
      padding: 3px 10px;
      border-radius: 6px;
      font-weight: 600;
    }
    .badge-green  { background: rgba(63,185,80,0.2); color: #56d364; border: 1px solid rgba(63,185,80,0.3); }
    .badge-blue   { background: rgba(56,132,255,0.2); color: #58a6ff; border: 1px solid rgba(56,132,255,0.3); }
    .badge-purple { background: rgba(168,85,247,0.2); color: #c084fc; border: 1px solid rgba(168,85,247,0.3); }
    .badge-red    { background: rgba(248,81,73,0.2); color: #f87171; border: 1px solid rgba(248,81,73,0.3); }
    .badge-gray   { background: rgba(136,136,136,0.2); color: #999; border: 1px solid rgba(136,136,136,0.3); }
    .history-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 24px;
      border-top: 1px solid rgba(252,103,103,0.12);
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
  isFreezing = false;
  saveStatus: 'idle' | 'saving' | 'saved' = 'idle';
  analysisResult: any = null;

  clarifications: any[] = [];
  lineage: any[] = [];
  showHistory = false;

  // Collapsible sections state
  sectionOpen: SectionOpenState = {
    entities: false,
    commands: false,
    queries: false,
    events: false,
    ui_components: false,
  };

  // Clarification inline session — batch mode
  clarificationActive = false;
  clarificationSessionId: string | null = null;
  clarificationAmbiguities: any[] = [];
  clarificationAnswers: Record<string, string> = {};
  isSubmittingAnswers = false;

  get answeredCount(): number {
    return Object.values(this.clarificationAnswers).filter(v => v?.trim()).length;
  }
  get clarificationProgressPct(): number {
    if (this.clarificationAmbiguities.length === 0) return 0;
    return (this.answeredCount / this.clarificationAmbiguities.length) * 100;
  }

  cancelClarification(): void {
    this.clarificationActive = false;
    this.clarificationAmbiguities = [];
    this.clarificationAnswers = {};
    this.clarificationSessionId = null;
    this.cdr.detectChanges();
  }
  isStartingClarification = false;
  isSubmittingAnswer = false;

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

  toggleSection(key: keyof SectionOpenState): void {
    this.sectionOpen[key] = !this.sectionOpen[key];
    this.cdr.detectChanges();
  }

  onClarificationKeydown(event: Event): void {
    const kbEvent = event as KeyboardEvent;
    // Ctrl+Enter no longer triggers single answer submit (batch mode)
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
  // Actions: Analyze, Freeze
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

  // ============================================================================
  // Clarification batch session
  // ============================================================================

  async startBatchClarification(): Promise<void> {
    // Auto-save brief trước
    if (this.hasUnsavedChanges) await this.autoSave();

    // Lấy ambiguities từ analysisResult hiện tại
    const ambiguities = this.analysisResult?.analysis?.ambiguities || [];
    if (ambiguities.length === 0) {
      this.showToast('Không có ambiguity cần làm rõ', 'error');
      return;
    }

    // Set up batch UI với ambiguities từ analysis
    this.clarificationSessionId = null;
    this.clarificationAmbiguities = ambiguities.map((a: any, i: number) => ({
      id: a.id || `amb-${i}`,
      type: a.type || 'general',
      description: a.description || '',
      source_text: a.source_text || '',
    }));
    this.clarificationAnswers = {};
    this.clarificationActive = true;
    this.isStartingClarification = false;
    this.cdr.detectChanges();
  }

  async submitBatchAnswers(): Promise<void> {
    if (this.answeredCount < this.clarificationAmbiguities.length) {
      this.showToast('Vui lòng trả lời tất cả các câu hỏi', 'error');
      return;
    }

    this.isSubmittingAnswers = true;
    this.cdr.detectChanges();

    try {
      // Build answers text and append to brief content
      const answersText = this.clarificationAmbiguities
        .map(amb => `[${amb.type}]: ${this.clarificationAnswers[amb.id] || ''}`)
        .join('\n');

      const updatedContent = this.briefContent + '\n\n--- Câu trả lời làm rõ ---\n' + answersText;

      // Re-analyze brief with clarified content
      const result = await this.api.analyzeBrief({
        brief_content: updatedContent,
        version: this.activeVersion,
      });

      if (result.success && result.data) {
        this.analysisResult = result.data;
        this.briefContent = updatedContent;
        this._lastSavedContent = updatedContent;
        this.showToast('Làm rõ yêu cầu thành công! Analysis đã được cập nhật', 'success');
        this.cancelClarification();
        await this.loadBrief();
        await this.loadLineage();
      } else {
        this.showToast(result.error?.message || 'Lỗi khi xử lý clarification', 'error');
      }
    } catch {
      this.showToast('Lỗi kết nối server', 'error');
    } finally {
      this.isSubmittingAnswers = false;
      this.cdr.detectChanges();
    }
  }
}
