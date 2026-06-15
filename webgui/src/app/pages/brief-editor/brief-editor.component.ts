/**
 * Component Brief Editor
 * 1 version = 1 brief duy nhất, status = progress (draft → clarified → frozen → archived)
 * Auto-save + phân tích + clarification history + change log
 */

import { Component, ChangeDetectorRef, inject, OnInit, OnDestroy, ViewChild, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, Router } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { I18nPipe } from '../../core/i18n.pipe';
import { I18nService } from '../../core/i18n.service';
import { VersionService } from '../../core/version.service';
import { PipelineStore } from '../../core/pipeline.store';
import { formatDateLocal } from '../../core/date.util';
import { DOCS_BASE } from '../../core/app.constants';
import { ClarificationListComponent } from '../../components/shared/clarification-list/clarification-list.component';
import { HistoryListComponent } from '../../components/shared/history-list/history-list.component';
import { LlmProgressComponent } from '../../components/shared/llm-progress/llm-progress.component';
import { AnalysisResultModalComponent } from '../../components/shared/analysis-result-modal/analysis-result-modal.component';

interface SectionOpenState {
  entities: boolean;
  commands: boolean;
  queries: boolean;
  events: boolean;
  ui_components: boolean;
  value_objects: boolean;
  guards: boolean;
  workflows: boolean;
  aggregates: boolean;
  roles: boolean;
  permissions: boolean;
  state_machines: boolean;
}

@Component({
  selector: 'app-brief-editor',
  standalone: true,
  imports: [CommonModule, FormsModule, I18nPipe, HistoryListComponent, LlmProgressComponent, AnalysisResultModalComponent],
  template: `
    <div class="brief-page py-8">
      <!-- Toast Notification -->
      @if (toast.show) {
        <div class="fixed top-16 right-4 z-50 animate-slide-in pointer-events-none">
          <div class="pointer-events-auto flex items-center gap-3 px-5 py-3.5"
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

      <!-- Header: 3 columns — Title | Progress Bar | Buttons -->
      <div class="mb-6 flex items-center justify-between gap-6">

        <!-- Column 1: Page title -->
        <div class="flex-shrink-0">
          <div class="brief-header-row">
            <h1 class="text-2xl font-bold">{{ 'brief.title' | i18n }}</h1>
            <a href="{{ docsUrl }}" target="_blank" rel="noopener" class="docs-link">{{ 'common.readGuide' | i18n }}</a>
          </div>
          <p class="text-text-secondary mt-1">{{ 'brief.subtitle' | i18n }}</p>
        </div>

        <!-- Column 2: Brief Lifecycle Progress Bar -->
        <div class="flex-1 flex items-center justify-center brief-lifecycle-bar">
          <div class="lifecycle-steps">
            <!-- Step 1: Draft -->
            <div class="lifecycle-step" [class.active]="!isFrozen" [class.done]="isFrozen">
              <div class="step-dot">
                @if (isFrozen) {
                  <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                  </svg>
                } @else {
                  <div class="step-pulse"></div>
                }
              </div>
              <div class="step-label">
                <span class="step-title">{{ 'brief.lifecyle.draft' | i18n }}</span>
                <span class="step-desc">{{ 'brief.lifecyle.draftDesc' | i18n }}</span>
              </div>
            </div>

            <!-- Connector line -->
            <div class="step-connector" [class.done]="isFrozen"></div>

            <!-- Step 2: Freezed -->
            <div class="lifecycle-step" [class.active]="isFrozen" [class.done]="isFrozen">
              <div class="step-dot">
                @if (isFrozen) {
                  <svg width="14" height="14" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 2a5 5 0 00-5 5v2a2 2 0 00-2 2v5a2 2 0 002 2h10a2 2 0 002-2v-5a2 2 0 00-2-2H8V7a3 3 0 01.22-1.165l.444-1.444A2 2 0 019.934 2H10z"/>
                  </svg>
                } @else {
                  <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.4" viewBox="0 0 20 20">
                    <path d="M10 2a5 5 0 00-5 5v2a2 2 0 00-2 2v5a2 2 0 002 2h10a2 2 0 002-2v-5a2 2 0 00-2-2H8V7a3 3 0 01.22-1.165l.444-1.444A2 2 0 019.934 2H10z"/>
                  </svg>
                }
              </div>
              <div class="step-label">
                <span class="step-title">{{ 'brief.lifecyle.freezed' | i18n }}</span>
                <span class="step-desc">{{ 'brief.lifecyle.freezedDesc' | i18n }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Column 3: Buttons -->
        <div class="flex items-center space-x-3 flex-shrink-0">
          <!-- Auto-save status -->
          @if (saveStatus === 'saving') {
            <span class="inline-flex items-center text-xs font-medium text-blue-300">
              <svg class="animate-spin -ml-0.5 mr-1.5 h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ 'brief.saving' | i18n }}
            </span>
          } @else if (hasUnsavedChanges) {
            <span class="text-xs font-medium text-amber-300">{{ 'brief.unsaved' | i18n }}</span>
          } @else if (saveStatus === 'saved') {
            <span class="text-xs font-medium text-green-400">{{ 'brief.saved' | i18n }}</span>
          } @else {
            <span class="text-xs text-text-tertiary">{{ 'brief.autoSaveOn' | i18n }}</span>
          }

          <!-- Analyze Button - chỉ hiện khi status !== freezed -->
          @if (!briefInfo || briefInfo.status !== 'freezed') {
            <button (click)="handleAnalyze()" class="btn btn-primary" [disabled]="isAnalyzing || !briefContent.trim()">
              {{ isAnalyzing ? ('brief.analyzing' | i18n) : ('brief.analyze' | i18n) }}
            </button>
          } @else {
            <span class="text-xs text-text-tertiary italic">{{ 'brief.freezed' | i18n }}</span>
          }

          <!-- Freeze Button - hiện khi brief chưa có hoặc status là draft -->
          @if (!briefInfo || briefInfo.status === 'draft') {
            <button (click)="handleFreeze()" class="btn btn-secondary" [disabled]="isFreezing || !briefContent.trim()">
              {{ isFreezing ? ('brief.processing' | i18n) : ('brief.freeze' | i18n) }}
            </button>
          }
        </div>
      </div>

      <!-- Frozen Banner -->
      @if (briefInfo && briefInfo.status === 'freezed') {
        <div class="mb-4 p-3 bg-orange-900 bg-opacity-30 border border-orange-500">
          <span class="text-orange-300 font-semibold">{{ 'brief.freezedBanner' | i18n }}</span>
          <span class="text-orange-200 text-sm ml-2">{{ 'brief.freezedBannerDesc' | i18n }}</span>
        </div>
      }

      <!-- Two-column layout: Editor (2/3) + Sidebar (1/3) -->
      <div class="brief-grid">
        <!-- Left column: Editor + Analysis -->
        <div class="brief-main">
          <!-- Editor -->
          <div class="card">
            <textarea
              [(ngModel)]="briefContent"
              (ngModelChange)="onContentChange()"
              [readonly]="isFrozen"
              class="w-full bg-bg-secondary border border-border-primary p-4 text-text-primary font-mono text-sm resize-none focus:outline-none focus:border-accent-primary"
              [class.opacity-50]="isFrozen"
              placeholder="{{ 'brief.placeholder' | i18n }}"
            ></textarea>
          </div>

        </div>

        <!-- Right column: Sidebar with Analysis/History tabs -->
        <div class="brief-sidebar">
          <!-- Tab toggle -->
          <div class="sidebar-tabs">
            @if (analysisResult) {
              <button
                type="button"
                class="sidebar-tab"
                [class.active]="rightTab === 'analysis'"
                (click)="rightTab = 'analysis'"
              >
                {{ 'brief.analysis' | i18n }}
                @if (analysisResult.status === 'needs_clarification') {
                  <span class="tab-badge">!</span>
                }
              </button>
            }
            <button
              type="button"
              class="sidebar-tab"
              [class.active]="rightTab === 'history'"
              (click)="rightTab = 'history'"
            >
              {{ 'brief.history' | i18n }}
              @if (lineage.length > 0) {
                <span class="tab-badge">{{ lineage.length }}</span>
              }
            </button>
          </div>

          <!-- Analysis tab panel (sidebar summary) -->
          @if (rightTab === 'analysis' && analysisResult) {
            <div class="sidebar-panel analysis-sidebar">
              <!-- Summary -->
              @if (analysisResult.analysis?.summary) {
                <div class="analysis-summary">
                  <p class="analysis-summary-text">{{ analysisResult.analysis.summary }}</p>
                </div>
              }

              <!-- Intent row -->
              @if (analysisResult.analysis) {
                <div class="analysis-intent-row">
                  @let domain = analysisResult.analysis.domain || analysisResult.analysis.intent?.domain;
                  @let type = analysisResult.analysis.type || analysisResult.analysis.intent?.type;
                  @if (domain) {
                    <span class="intent-chip"><span class="chip-label">{{ 'brief.domain' | i18n }}</span> {{ domain }}</span>
                  }
                  @if (type) {
                    <span class="intent-chip"><span class="chip-label">{{ 'brief.type' | i18n }}</span> {{ type }}</span>
                  }
                  @let scale = analysisResult.analysis.scale || analysisResult.analysis.intent?.scale;
                  @if (scale) {
                    <span class="intent-chip"><span class="chip-label">{{ 'brief.scale' | i18n }}</span> {{ scale }}</span>
                  }
                </div>
              }

              <!-- Resource stats -->
              @if (analysisResult.analysis) {
                @let entities = analysisResult.analysis.entities || [];
                @let commands = analysisResult.analysis.commands || [];
                @let queries = analysisResult.analysis.queries || [];
                @let events = analysisResult.analysis.events || [];
                @let uiComponents = analysisResult.analysis.ui_components || [];
                @let valueObjects = analysisResult.analysis.value_objects || [];
                @let guards = analysisResult.analysis.guards || [];
                @let workflows = analysisResult.analysis.workflows || [];
                @let aggregates = analysisResult.analysis.aggregates || [];
                @let roles = analysisResult.analysis.roles || [];
                @let permissions = analysisResult.analysis.permissions || [];
                @let stateMachines = analysisResult.analysis.state_machines || [];
                <div class="analysis-stats-row">
                  <span class="stat-item"><span class="stat-val">{{ entities.length }}</span> <span class="stat-label">{{ 'brief.entities' | i18n }}</span></span>
                  <span class="stat-item"><span class="stat-val">{{ commands.length }}</span> <span class="stat-label">{{ 'brief.commands' | i18n }}</span></span>
                  <span class="stat-item"><span class="stat-val">{{ queries.length }}</span> <span class="stat-label">{{ 'brief.queries' | i18n }}</span></span>
                  <span class="stat-item"><span class="stat-val">{{ events.length }}</span> <span class="stat-label">{{ 'brief.events' | i18n }}</span></span>
                  <span class="stat-item"><span class="stat-val">{{ uiComponents.length }}</span> <span class="stat-label">{{ 'brief.uiComponents' | i18n }}</span></span>
                  <span class="stat-item"><span class="stat-val">{{ valueObjects.length }}</span> <span class="stat-label">{{ 'brief.valueObjects' | i18n }}</span></span>
                  <span class="stat-item"><span class="stat-val">{{ guards.length }}</span> <span class="stat-label">{{ 'brief.guards' | i18n }}</span></span>
                  <span class="stat-item"><span class="stat-val">{{ workflows.length }}</span> <span class="stat-label">{{ 'brief.workflows' | i18n }}</span></span>
                  <span class="stat-item"><span class="stat-val">{{ aggregates.length }}</span> <span class="stat-label">{{ 'brief.aggregates' | i18n }}</span></span>
                  <span class="stat-item"><span class="stat-val">{{ roles.length }}</span> <span class="stat-label">{{ 'brief.roles' | i18n }}</span></span>
                  <span class="stat-item"><span class="stat-val">{{ permissions.length }}</span> <span class="stat-label">{{ 'brief.permissions' | i18n }}</span></span>
                  <span class="stat-item"><span class="stat-val">{{ stateMachines.length }}</span> <span class="stat-label">{{ 'brief.stateMachines' | i18n }}</span></span>
                </div>
              }

              <!-- Ambiguities preview -->
              @if (analysisResult.analysis?.ambiguities?.length > 0) {
                <div class="sidebar-ambiguities">
                  <h4 class="ambiguity-heading">
                    {{ 'brief.needClarify' | i18n }} ({{ analysisResult.analysis.ambiguities.length }})
                  </h4>
                  @for (amb of analysisResult.analysis.ambiguities; track $index) {
                    <div class="amb-item">
                      <p class="amb-summary">{{ amb.summary }}</p>
                      @if (amb.recommend) {
                        <p class="amb-recommend">💡 {{ amb.recommend }}</p>
                      }
                    </div>
                  }
                </div>
              }

              <!-- Footer actions -->
              <div class="sidebar-footer">
                <button (click)="openAnalysisModal()" class="btn btn-secondary w-full">
                  <i class="fa-solid fa-expand"></i> {{ 'analysisResult.view' | i18n }}
                </button>
                @if (analysisResult.status === 'ready') {
                  <button (click)="navigateToContract()" class="btn btn-primary w-full mt-2">
                    <i class="fa-solid fa-file-contract"></i> {{ 'analysisResult.createContract' | i18n }}
                  </button>
                } @else if (analysisResult.status === 'needs_clarification') {
                  <button (click)="openAnalysisModal('clarify')" class="btn btn-accent w-full mt-2">
                    <i class="fa-solid fa-pen-to-square"></i> {{ 'analysisResult.startClarify' | i18n }}
                  </button>
                }
              </div>
            </div>
          }

          <!-- History tab panel -->
          @if (rightTab === 'history') {
            <div class="sidebar-panel">
              <app-history-list [items]="lineage" (viewDiff)="openDiffModal($event)"></app-history-list>
            </div>
          }
        </div>
      </div>

      <!-- Diff Modal -->
      @if (showDiffModal && diffData) {
        <div class="diff-modal-overlay" (click)="closeDiffModal()">
          <div class="diff-modal" (click)="$event.stopPropagation()">
            <div class="diff-modal-header">
              <div class="diff-modal-title">
                <span class="diff-modal-rev">#{{ diffData.revision_number }}</span>
                <span class="diff-modal-event">{{ getEventLabelForModal(diffData.event) }}</span>
                @if (diffData.diff_summary) {
                  <span class="diff-modal-summary">{{ diffData.diff_summary }}</span>
                }
              </div>
              <button class="diff-modal-close" (click)="closeDiffModal()">✕</button>
            </div>
            <div class="diff-modal-stats">
              @if (diffData.stats) {
                <span class="diff-stat diff-stat-added">+{{ diffData.stats.added }}</span>
                <span class="diff-stat diff-stat-removed">-{{ diffData.stats.removed }}</span>
              }
            </div>
            <div class="diff-modal-body">
              @if (diffData.loading) {
                <div class="diff-loading">{{ 'brief.loadingDiff' | i18n }}</div>
              } @else if (diffData.diff_lines && diffData.diff_lines.length > 0) {
                @for (line of diffData.diff_lines; track line.text) {
                  <div class="diff-line" [class.diff-added]="line.type === 'added'" [class.diff-removed]="line.type === 'removed'" [class.diff-header]="line.type === 'header'" [class.diff-context]="line.type === 'context'">
                    <span class="diff-sign">{{ line.sign }}</span>
                    <span class="diff-text">{{ line.text }}</span>
                  </div>
                }
              } @else {
                <div class="diff-empty">Không có thay đổi</div>
              }
            </div>
          </div>
        </div>
      }

      <!-- LLM Progress Overlay -->
      @if (showAnalyzeOverlay) {
        <app-llm-progress
          [visible]="showAnalyzeOverlay"
          [title]="'analyze.title' | i18n"
          (closeOverlay)="onCloseAnalyzeOverlay()"
          (cancelAnalyze)="onCancelAnalyze()"
          (viewResult)="openAnalysisModal()"
          #analyzeOverlay
        ></app-llm-progress>
      }

      <!-- Analysis Result Modal -->
      @if (showAnalysisModal) {
        <app-analysis-result-modal
          [analysisResult]="analysisResult"
          [initialTab]="modalInitialTab"
          (close)="closeAnalysisModal()"
          (submitClarification)="onSubmitClarification($event)"
          (goToContract)="navigateToContract()"
        ></app-analysis-result-modal>
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

    /* ---- Page header docs link ---- */
    .brief-header-row {
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

    /* ---- Brief Lifecycle Progress Bar ---- */
    .lifecycle-steps {
      display: flex;
      align-items: center;
      gap: 0;
    }

    .lifecycle-step {
      display: flex;
      align-items: center;
      gap: 8px;
      opacity: 0.4;
      transition: opacity 0.3s;
    }

    .lifecycle-step.active {
      opacity: 1;
    }

    .lifecycle-step.done {
      opacity: 0.7;
    }

    .step-dot {
      width: 26px;
      height: 26px;
      border-radius: 50%;
      border: 2px solid var(--border-primary, rgba(255,255,255,0.15));
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      color: var(--text-tertiary, rgba(255,255,255,0.3));
      transition: all 0.3s;
    }

    .lifecycle-step.active .step-dot {
      border-color: var(--brand-color, #fc6767);
      color: var(--brand-color, #fc6767);
      box-shadow: 0 0 12px rgba(252, 103, 103, 0.3);
    }

    .lifecycle-step.done .step-dot {
      border-color: var(--accent-success, #4ade80);
      color: var(--accent-success, #4ade80);
      background: rgba(74, 222, 128, 0.1);
    }

    .step-pulse {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--brand-color, #fc6767);
      animation: stepPulse 2s ease-in-out infinite;
    }

    @keyframes stepPulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.5; transform: scale(0.75); }
    }

    .step-label {
      display: flex;
      flex-direction: column;
      gap: 1px;
    }

    .step-title {
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--text-secondary, rgba(255,255,255,0.6));
      line-height: 1.2;
    }

    .lifecycle-step.active .step-title {
      color: var(--text-primary, #fff);
    }

    .lifecycle-step.done .step-title {
      color: var(--accent-success, #4ade80);
    }

    .step-desc {
      font-size: 0.65rem;
      color: var(--text-tertiary, rgba(255,255,255,0.3));
      line-height: 1.2;
    }

    .lifecycle-step.active .step-desc {
      color: var(--text-secondary, rgba(255,255,255,0.5));
    }

    .step-connector {
      width: 60px;
      min-width: 40px;
      max-width: 80px;
      height: 2px;
      margin: 0 12px;
      background: var(--border-primary, rgba(255,255,255,0.1));
      position: relative;
    }

    .step-connector.done {
      background: var(--accent-success, #4ade80);
      box-shadow: 0 0 6px rgba(74, 222, 128, 0.3);
    }

    /* ---- Clarification Batch UI ---- */
    .clarification-batch-section {
      margin-top: 24px;
      padding: 24px;
      background: #14141f;
      border: 1px solid rgba(168, 85, 247, 0.3);
      border-radius: 0;
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
      border-radius: 0;
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
      border-radius: 0;
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
      border-radius: 0;
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
      /* IBM Carbon: no box-shadow */
    }
    .ambiguity-textarea::placeholder {
      color: rgba(255, 255, 255, 0.25);
    }
    .clarification-progress-bar {
      width: 100%;
      height: 4px;
      background: rgba(255, 255, 255, 0.06);
      border-radius: 0;
      overflow: hidden;
      margin-bottom: 8px;
    }
    .clarification-progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #a855f7, #fc6767);
      border-radius: 0;
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
      border-radius: 0;
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

    /* =================================================================
     * 2-Column layout: Editor (2/3) + Sidebar (1/3)
     * Fixed height — inner scroll
     * ================================================================= */
    .brief-page {
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }
    .brief-grid {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 1.5rem;
      align-items: stretch;
      flex: 1;
      min-height: 0;
    }
    .brief-main {
      display: flex;
      flex-direction: column;
      min-width: 0;
      min-height: 0;
      overflow-y: auto;
    }
    .brief-main::-webkit-scrollbar {
      width: 6px;
    }
    .brief-main::-webkit-scrollbar-thumb {
      background: rgba(252,103,103,0.15);
    }
    .brief-main > .card {
      display: flex;
      flex-direction: column;
      min-height: 100%;
    }
    .brief-main > .card textarea {
      flex: 1;
      min-height: 260px;
      overflow-y: auto;
    }
    .brief-sidebar {
      display: flex;
      flex-direction: column;
      background: #14141f;
      border: 1px solid rgba(252,103,103,0.15);
      overflow: hidden;
      min-height: 0;
    }

    /* IBM Carbon: no border-radius anywhere in this component */
    .brief-grid *,
    .brief-grid *::before,
    .brief-grid *::after {
      border-radius: 0 !important;
    }

    /* Tab toggle */
    .sidebar-tabs {
      display: flex;
      border-bottom: 1px solid rgba(252,103,103,0.15);
      flex-shrink: 0;
    }
    .sidebar-tab {
      flex: 1;
      padding: 10px 0;
      background: transparent;
      border: none;
      color: rgba(255,255,255,0.45);
      font-size: 0.8125rem;
      font-weight: 600;
      cursor: pointer;
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: all 0.2s;
    }
    .sidebar-tab:hover {
      color: rgba(255,255,255,0.75);
      background: rgba(255,255,255,0.03);
    }
    .sidebar-tab.active {
      color: #fc6767;
      border-bottom: 2px solid #fc6767;
    }
    .tab-badge {
      font-size: 0.6875rem;
      padding: 1px 6px;
      border-radius: 0;
      background: rgba(252,103,103,0.2);
      color: #fc6767;
      line-height: 1.4;
    }

    /* Sidebar panel (scrollable content) */
    .sidebar-panel {
      flex: 1;
      overflow-y: auto;
      padding: 12px;
    }

    /* Analysis sidebar — clean, data-focused */
    .analysis-sidebar {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .analysis-summary-text {
      font-size: 0.8125rem;
      color: rgba(255, 255, 255, 0.7);
      line-height: 1.55;
      margin: 0;
    }

    /* Intent chips — horizontal row */
    .analysis-intent-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .intent-chip {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 10px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
      font-size: 0.75rem;
      color: rgba(255, 255, 255, 0.7);
    }
    .intent-chip .chip-label {
      font-size: 0.625rem;
      color: rgba(255, 255, 255, 0.4);
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }

    /* Stats row — compact, horizontal */
    .analysis-stats-row {
      display: flex;
      flex-wrap: wrap;
      gap: 4px 12px;
      padding: 8px 10px;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .analysis-stats-row .stat-item {
      display: inline-flex;
      align-items: baseline;
      gap: 4px;
      font-size: 0.78rem;
    }
    .analysis-stats-row .stat-val {
      font-weight: 700;
      color: rgba(255, 255, 255, 0.85);
      font-size: 0.9rem;
    }
    .analysis-stats-row .stat-label {
      font-size: 0.6875rem;
      color: rgba(255, 255, 255, 0.4);
    }

    /* Ambiguities — subtle */
    .ambiguity-heading {
      font-size: 0.75rem;
      font-weight: 600;
      color: rgba(250, 204, 21, 0.8);
      margin: 0 0 8px 0;
    }
    .amb-item {
      padding: 8px 10px;
      margin-bottom: 6px;
      background: rgba(255, 255, 255, 0.02);
      border-left: 2px solid rgba(255, 255, 255, 0.08);
    }
    .amb-summary {
      font-size: 0.75rem;
      color: rgba(255, 255, 255, 0.8);
      font-weight: 500;
      margin: 0;
      line-height: 1.4;
    }
    .amb-recommend {
      font-size: 0.6875rem;
      color: rgba(63, 185, 80, 0.8);
      margin: 3px 0 0 0;
      font-style: italic;
    }

    /* Sidebar footer buttons */
    .sidebar-footer {
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-top: auto;
      padding-top: 10px;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
    }
    .sidebar-footer .btn {
      width: 100%;
      padding: 8px;
      font-size: 0.8125rem;
    }
    .btn-accent {
      background: #e91e63;
      color: #fff;
      border: none;
      cursor: pointer;
    }
    .btn-accent:hover {
      background: #c2185b;
    }

    /* Responsive: stack on small screens */
    @media (max-width: 1024px) {
      .brief-grid {
        grid-template-columns: 1fr;
      }
      .brief-sidebar {
        position: static;
        max-height: none;
      }
    }

    /* Diff Modal */
    .diff-modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.7);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 9999;
      padding: 2rem;
    }
    .diff-modal {
      background: #16161e;
      border: 1px solid rgba(255, 255, 255, 0.1);
      width: 100%;
      max-width: 720px;
      max-height: 80vh;
      display: flex;
      flex-direction: column;
    }
    .diff-modal-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      flex-shrink: 0;
    }
    .diff-modal-title {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .diff-modal-rev {
      font-size: 0.8125rem;
      font-family: monospace;
      color: rgba(255, 255, 255, 0.5);
    }
    .diff-modal-event {
      font-size: 0.75rem;
      padding: 2px 8px;
      border-radius: 0;
      font-weight: 600;
      background: rgba(56, 132, 255, 0.2);
      color: #58a6ff;
      border: 1px solid rgba(56, 132, 255, 0.3);
    }
    .diff-modal-summary {
      font-size: 0.75rem;
      color: rgba(255, 255, 255, 0.6);
    }
    .diff-modal-close {
      background: none;
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: rgba(255, 255, 255, 0.5);
      font-size: 0.875rem;
      padding: 2px 8px;
      cursor: pointer;
      border-radius: 0;
    }
    .diff-modal-close:hover {
      color: white;
      background: rgba(255, 255, 255, 0.05);
    }
    .diff-modal-stats {
      display: flex;
      gap: 12px;
      padding: 8px 16px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      flex-shrink: 0;
    }
    .diff-stat {
      font-size: 0.75rem;
      font-family: monospace;
    }
    .diff-stat-added {
      color: #3fb950;
      background: rgba(63, 185, 80, 0.1);
      padding: 1px 6px;
    }
    .diff-stat-removed {
      color: #f85149;
      background: rgba(248, 81, 73, 0.1);
      padding: 1px 6px;
    }
    .diff-modal-body {
      flex: 1;
      overflow: auto;
      padding: 0;
    }
    .diff-loading {
      padding: 16px;
      font-size: 0.8125rem;
      color: rgba(255,255,255,0.4);
      text-align: center;
    }
    .diff-empty {
      padding: 16px;
      font-size: 0.8125rem;
      color: rgba(255,255,255,0.3);
      text-align: center;
    }
    .diff-line {
      font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
      font-size: 0.75rem;
      line-height: 1.6;
      display: flex;
      align-items: flex-start;
      white-space: pre-wrap;
      word-break: break-all;
    }
    .diff-line.diff-header {
      color: rgba(255,255,255,0.35);
      font-size: 0.6875rem;
      padding: 2px 12px;
      border-bottom: 1px solid rgba(255,255,255,0.04);
      background: rgba(255,255,255,0.02);
    }
    .diff-line.diff-context {
      color: rgba(255,255,255,0.4);
      padding: 0 12px;
    }
    .diff-line.diff-added {
      color: #7ee787;
      background: rgba(63,185,80,0.08);
      padding: 0 12px;
    }
    .diff-line.diff-removed {
      color: #f97583;
      background: rgba(248,81,73,0.08);
      padding: 0 12px;
    }
    .diff-sign {
      flex-shrink: 0;
      width: 1em;
      user-select: none;
    }
    .diff-text {
      flex: 1;
      min-width: 0;
    }
  `],
})
export class BriefEditorComponent implements OnInit, OnDestroy, AfterViewChecked {
  briefContent = '';
  private _lastSavedContent = '';
  private _normalizeWhitespace(content: string): string {
    return content.split('\n').map(line => line.trimEnd()).join('\n').replace(/\n{3,}/g, '\n\n').trim();
  }
  get hasUnsavedChanges(): boolean {
    return this._normalizeWhitespace(this.briefContent) !== this._normalizeWhitespace(this._lastSavedContent);
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
    value_objects: false,
    guards: false,
    workflows: false,
    aggregates: false,
    roles: false,
    permissions: false,
    state_machines: false,
  };

  formatDate(iso: string): string {
    return formatDateLocal(iso);
  }

  // Clarification inline session — batch mode
  clarificationActive = false;
  clarificationSessionId: string | null = null;
  clarificationAmbiguities: any[] = [];
  clarificationAnswers: Record<string, string> = {};
  isSubmittingAnswers = false;

  // Diff modal
  showDiffModal = false;
  diffData: {
    revision_number: number;
    event: string;
    diff_summary: string | null;
    diff_text: string;
    diff_lines: { type: 'header' | 'added' | 'removed' | 'context'; sign: string; text: string }[];
    stats: { added: number; removed: number } | null;
    loading: boolean;
  } | null = null;

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
    return this.briefInfo?.status === 'freezed';
  }

  // Right sidebar tab toggle
  rightTab: 'analysis' | 'history' = 'analysis';

  // Dynamic version từ PipelineStore
  get activeVersion(): string {
    return this.pipelineStore.getActiveVersion() || '';
  }

  // Toast notification
  toast = { show: false, message: '', type: 'success' as 'success' | 'error' };

  readonly docsUrl = `${DOCS_BASE}/brief`;

  private api = inject(ApiService);
  private pipelineStore = inject(PipelineStore);
  private cdr = inject(ChangeDetectorRef);
  private router = inject(Router);
  private i18n = inject(I18nService);
  private versionService = inject(VersionService);
  private saveTimer: any = null;
  private toastTimer: any = null;

  async ngOnInit(): Promise<void> {
    await this.pipelineStore.loadStatus();
    await this.loadBrief();
    await this.loadLineage();
    this.cdr.detectChanges();

    // Reload khi version switch
    window.addEventListener('version-switched', this.onVersionSwitched);
  }

  ngAfterViewChecked(): void {
    // Flush pending SSE messages when overlay ref becomes available
    if (this.pendingMessages.length > 0 && this.analyzeOverlayRef) {
      for (const msg of this.pendingMessages) {
        this.analyzeOverlayRef.onMessage(msg);
      }
      this.pendingMessages = [];
    }
  }

  ngOnDestroy(): void {
    if (this.saveTimer) clearTimeout(this.saveTimer);
    if (this.toastTimer) clearTimeout(this.toastTimer);
    if (this.analyzeTimeoutId) clearTimeout(this.analyzeTimeoutId);
    if (this.abortController) this.abortController.abort();
    window.removeEventListener('version-switched', this.onVersionSwitched);
  }

  /** Reload toàn bộ brief data khi version switch */
  private onVersionSwitched = async (event: any) => {
    const targetVersion = event?.detail?.version || this.activeVersion;
    try {
      await this.pipelineStore.loadStatus();
      await this.loadBriefForVersion(targetVersion);
      await this.loadLineageForVersion(targetVersion);
      this.cdr.detectChanges();
    } catch (e) {
      console.error('BriefEditor onVersionSwitched error:', e);
    } finally {
      this.versionService.stopLoading();
    }
  };

  async loadBriefForVersion(version: string): Promise<void> {
    const result = await this.api.getBrief(version);
    if (result.success && result.data) {
      this.briefInfo = result.data;
      this.briefContent = result.data.content || '';
      this._lastSavedContent = this.briefContent;
      this.clarifications = result.data.clarifications || [];
      this.analysisResult = result.data.analysis || null;
    } else {
      // Clear all content khi không có brief cho version này
      this.briefInfo = null;
      this.briefContent = '';
      this._lastSavedContent = '';
      this.clarifications = [];
      this.analysisResult = null;
    }
  }

  async loadLineageForVersion(version: string): Promise<void> {
    const result = await this.api.getBriefRevisions(version);
    if (result.success && result.data?.revisions) {
      this.lineage = result.data.revisions;
    } else {
      this.lineage = [];
    }
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
    } else {
      // Clear all content khi không có brief cho version này
      this.briefInfo = null;
      this.briefContent = '';
      this._lastSavedContent = '';
      this.clarifications = [];
      this.analysisResult = null;
    }
  }

  async loadLineage(): Promise<void> {
    const result = await this.api.getBriefRevisions(this.activeVersion);
    if (result.success && result.data?.revisions) {
      this.lineage = result.data.revisions;
    } else {
      this.lineage = [];
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
    }, 5000);
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
        this.loadLineage();
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

  @ViewChild('analyzeOverlay') analyzeOverlayRef?: LlmProgressComponent;

  // Analyze overlay state
  showAnalyzeOverlay = false;
  private abortController: AbortController | null = null;
  private analyzeTimeoutId: any = null;
  private pendingMessages: any[] = [];

  // Analysis result modal
  showAnalysisModal = false;
  modalInitialTab: 'result' | 'clarify' = 'result';

  openAnalysisModal(tab: 'result' | 'clarify' = 'result'): void {
    this.modalInitialTab = tab;
    // Force Angular to recreate the component so setter fires
    this.showAnalysisModal = false;
    this.cdr.detectChanges();
    setTimeout(() => {
      this.showAnalysisModal = true;
      this.cdr.detectChanges();
    }, 100);
  }

  closeAnalysisModal(): void {
    this.showAnalysisModal = false;
    this.cdr.detectChanges();
  }

  onSubmitClarification(items: any[]): void {
    // Handle clarification submission — forward to existing submitBatchAnswers logic
    this.closeAnalysisModal();
    this.startBatchClarification();
  }

  navigateToContract(): void {
    this.router.navigate(['/contract-viewer']);
  }

  handleAnalyze(): void {
    if (!this.briefContent.trim()) {
      this.showToast(this.i18n.t('brief.enterBrief'), 'error');
      return;
    }
    if (this.hasUnsavedChanges) {
      // Auto-save trước, sau đó mở overlay
      this.autoSave().then(() => {
        this.openAnalyzeOverlay();
      });
    } else {
      this.openAnalyzeOverlay();
    }
  }

  openAnalyzeOverlay(): void {
    this.showAnalyzeOverlay = true;
    this.isAnalyzing = true;
    this.pendingMessages = [];
    this.cdr.detectChanges();

    // Timeout safety net: 3 phút max
    this.analyzeTimeoutId = setTimeout(() => {
      if (this.abortController) this.abortController.abort();
      this.isAnalyzing = false;
      this.showToast(this.i18n.t('brief.analyzeTimeout'), 'error');
      this.cdr.detectChanges();
    }, 180000);

    // Connect SSE via fetch + ReadableStream
    this.abortController = new AbortController();
    const apiUrl = `http://localhost:6868/api/brief/analyze-stream?version=${encodeURIComponent(this.activeVersion)}`;

    fetch(apiUrl, { signal: this.abortController.signal })
      .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const reader = response.body?.getReader();
        if (!reader) throw new Error('No readable stream');
        this._readSSEStream(reader);
      })
      .catch(err => {
        if (err.name === 'AbortError') return;
        console.error('[BriefEditor] SSE connect error:', err);
        clearTimeout(this.analyzeTimeoutId);
        this.isAnalyzing = false;
        this.showToast(`Kết nối lỗi: ${err.message}`, 'error');
        this.cdr.detectChanges();
      });
  }

  /** Read SSE stream line by line */
  private async _readSSEStream(reader: ReadableStreamDefaultReader<Uint8Array>): Promise<void> {
    const decoder = new TextDecoder();
    let buffer = '';
    let lastEvent = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE lines
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) {
            // Empty line = end of SSE event — we already parsed data, skip
            continue;
          }
          if (trimmed.startsWith('data: ')) {
            const dataStr = trimmed.slice(6);
            try {
              const data = JSON.parse(dataStr);
              const msg = { type: lastEvent, data: data };
              // Forward message to overlay component (buffer if not ready)
              if (this.analyzeOverlayRef) {
                this.analyzeOverlayRef.onMessage(msg);
              } else {
                this.pendingMessages.push(msg);
              }

              // If final_result or error, cleanup
              if (lastEvent === 'final_result') {
                clearTimeout(this.analyzeTimeoutId);
                this.isAnalyzing = false;
                this.analysisResult = data;
                this.cdr.detectChanges();
              } else if (lastEvent === 'error') {
                clearTimeout(this.analyzeTimeoutId);
                this.isAnalyzing = false;
                this.cdr.detectChanges();
              }
            } catch {
              // data might be plain string for error events
              const msg = { type: lastEvent, data: dataStr };
              if (this.analyzeOverlayRef) {
                this.analyzeOverlayRef.onMessage(msg);
              } else {
                this.pendingMessages.push(msg);
              }
              if (lastEvent === 'error') {
                clearTimeout(this.analyzeTimeoutId);
                this.isAnalyzing = false;
                this.cdr.detectChanges();
              }
            }
          } else if (trimmed.startsWith('event: ')) {
            lastEvent = trimmed.slice(7);
          }
        }
      }
    } catch (err: any) {
      if (err?.name === 'AbortError') return;
      throw err;
    } finally {
      reader.releaseLock();
    }
  }

  onCloseAnalyzeOverlay(): void {
    this.showAnalyzeOverlay = false;
    this.cdr.detectChanges();
  }

  onCancelAnalyze(): void {
    if (this.abortController) this.abortController.abort();
    clearTimeout(this.analyzeTimeoutId);
    this.isAnalyzing = false;
    this.showAnalyzeOverlay = false;
    this.abortController = null;
    this.cdr.detectChanges();
  }

  async handleFreeze(): Promise<void> {
    this.isFreezing = true;
    this.cdr.detectChanges();

    try {
      const result = await this.api.freezeBrief(this.activeVersion);

      if (result.success) {
        this.showToast(this.i18n.t('brief.freezedMsg'), 'success');
        await this.loadBrief();
      } else {
        this.showToast(result.error?.message || this.i18n.t('brief.freezeError'), 'error');
      }
    } catch {
      this.showToast(this.i18n.t('brief.connectError'), 'error');
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
      freezed: 'bg-red-900 bg-opacity-40 text-red-300 border border-red-700',
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
      this.showToast(this.i18n.t('brief.noAmbiguity'), 'error');
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
      this.showToast(this.i18n.t('brief.answerAll'), 'error');
      return;
    }

    this.isSubmittingAnswers = true;
    this.cdr.detectChanges();

    try {
      // Build answers text and append to brief content
      const answersText = this.clarificationAmbiguities
        .map(amb => `${amb.summary || ''}: ${this.clarificationAnswers[amb.id || amb.summary] || ''}`)
        .join('\n');

      const updatedContent = this.briefContent + '\n\n--- Clarification Answers ---\n' + answersText;

      // 1. Save the clarified brief first
      const saveResult = await this.api.saveBrief({
        version: this.activeVersion,
        brief_content: updatedContent,
      });

      if (!saveResult.success) {
        this.showToast(this.i18n.t('brief.saveFailed'), 'error');
        return;
      }

      this.briefContent = updatedContent;
      this._lastSavedContent = updatedContent;
      this.cancelClarification();

      // 2. Re-analyze with clarified content via WebSocket overlay
      this.openAnalyzeOverlay();
      this.isSubmittingAnswers = false;
    } catch {
      this.showToast(this.i18n.t('brief.connectError'), 'error');
      this.isSubmittingAnswers = false;
      this.cdr.detectChanges();
    }
  }

  // ============================================================================
  // Diff Modal
  // ============================================================================

  getEventLabelForModal(event: string): string {
    const labels: Record<string, string> = {
      'created': 'Created',
      'content_updated': 'Updated',
      'analyzed': 'Analyzed',
      'freezed': 'Freezed',
    };
    return labels[event] || event;
  }

  async openDiffModal(entry: any): Promise<void> {
    this.showDiffModal = true;
    this.diffData = {
      revision_number: entry.revision_number,
      event: entry.event,
      diff_summary: entry.diff_summary,
      diff_text: '',
      diff_lines: [],
      stats: null,
      loading: true,
    };
    this.cdr.detectChanges();

    try {
      const result = await this.api.getRevisionDiff(entry.revision_number, this.activeVersion);
      if (result.success && result.data) {
        const lines = this.parseDiffText(result.data.diff_text);
        this.diffData = {
          revision_number: result.data.revision_number,
          event: result.data.event || entry.event,
          diff_summary: result.data.diff_summary || entry.diff_summary,
          diff_text: result.data.diff_text,
          diff_lines: lines,
          stats: result.data.stats,
          loading: false,
        };
      } else {
        this.diffData = { ...this.diffData!, loading: false, diff_text: '', diff_lines: [] };
      }
    } catch {
      this.diffData = { ...this.diffData!, loading: false, diff_text: '', diff_lines: [] };
    }
  }

  parseDiffText(text: string): { type: 'header' | 'added' | 'removed' | 'context'; sign: string; text: string }[] {
    if (!text) return [];
    const lines = text.split('\n');
    const result: { type: 'header' | 'added' | 'removed' | 'context'; sign: string; text: string }[] = [];
    for (const line of lines) {
      if (line.startsWith('---') || line.startsWith('+++')) {
        result.push({ type: 'header', sign: '', text: line });
      } else if (line.startsWith('@@')) {
        result.push({ type: 'header', sign: '', text: line });
      } else if (line.startsWith('+')) {
        result.push({ type: 'added', sign: '+', text: line.substring(1) });
      } else if (line.startsWith('-')) {
        result.push({ type: 'removed', sign: '-', text: line.substring(1) });
      } else if (line.startsWith(' ')) {
        result.push({ type: 'context', sign: ' ', text: line.substring(1) });
      } else {
        result.push({ type: 'context', sign: '', text: line });
      }
    }
    return result;
  }

  closeDiffModal(): void {
    this.showDiffModal = false;
    this.diffData = null;
  }
}
