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
import { I18nPipe } from '../../core/i18n.pipe';
import { I18nService } from '../../core/i18n.service';
import { VersionService } from '../../core/version.service';
import { PipelineStore } from '../../core/pipeline.store';
import { formatDateLocal } from '../../core/date.util';
import { DOCS_BASE } from '../../core/app.constants';
import { ClarificationListComponent } from '../../components/shared/clarification-list/clarification-list.component';
import { HistoryListComponent } from '../../components/shared/history-list/history-list.component';
import { AnalyzeOverlayComponent } from '../../components/shared/analyze-overlay/analyze-overlay.component';

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
  imports: [CommonModule, FormsModule, RouterLink, I18nPipe, ClarificationListComponent, HistoryListComponent, AnalyzeOverlayComponent],
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

          <!-- Analysis Result -->
          @if (analysisResult) {
        <div class="card mt-6 analysis-card">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold">{{ 'brief.analysis' | i18n }}</h2>
            <div class="flex items-center gap-2">
              <span class="text-xs px-2 py-1 font-medium"
                    [class]="analysisResult.status === 'needs_clarification'
                      ? 'bg-yellow-900 bg-opacity-40 text-yellow-300 border border-yellow-700'
                      : 'bg-green-900 bg-opacity-40 text-green-300 border border-green-700'">
                {{ analysisResult.status === 'needs_clarification' ? ('brief.needClarify' | i18n) : ('brief.readyContract' | i18n) }}
              </span>
              @if (analysisResult?.metadata?.brief_id) {
                <span class="text-xs text-text-tertiary font-mono">{{ analysisResult.metadata.brief_id }}</span>
              }
            </div>
          </div>

          <!-- Summary -->
          @if (analysisResult?.analysis?.summary) {
            <div class="mb-4 p-3 bg-blue-900 bg-opacity-20 border-l-4 border-blue-400">
              <p class="text-sm text-blue-200">{{ analysisResult.analysis.summary }}</p>
            </div>
          }

          <!-- Intent + Confidence -->
          <div class="mb-4 grid grid-cols-4 gap-4">
            <div>
              <span class="text-text-secondary text-xs">{{ 'brief.domain' | i18n }}</span>
              <p class="text-sm font-medium text-text-primary">{{ analysisResult?.analysis?.intent?.domain }}</p>
            </div>
            <div>
              <span class="text-text-secondary text-xs">{{ 'brief.type' | i18n }}</span>
              <p class="text-sm font-medium text-text-primary">{{ analysisResult?.analysis?.intent?.type }}</p>
            </div>
            <div>
              <span class="text-text-secondary text-xs">{{ 'brief.scale' | i18n }}</span>
              <p class="text-sm font-medium text-text-primary">{{ analysisResult?.analysis?.intent?.scale }}</p>
            </div>
            <div>
              <span class="text-text-tertiary text-xs">{{ 'brief.confidence' | i18n }}</span>
              <div class="flex items-center gap-2">
                <div class="flex-1 h-2 bg-bg-secondary overflow-hidden">
                  <div class="h-full transition-all duration-500"
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
            <h3 class="font-medium text-accent-primary mb-2"><i class="fa-solid fa-box-open"></i> {{ 'brief.resourcesExtracted' | i18n }}</h3>            <div class="grid grid-cols-5 gap-3">
              <div class="p-3 bg-bg-secondary text-center border border-border-primary">
                <p class="text-2xl font-bold text-blue-400">{{ analysisResult?.metadata?.entities }}</p>
                <p class="text-xs text-text-secondary mt-1">{{ 'brief.entities' | i18n }}</p>
              </div>
              <div class="p-3 bg-bg-secondary text-center border border-border-primary">
                <p class="text-2xl font-bold text-orange-400">{{ analysisResult?.metadata?.commands }}</p>
                <p class="text-xs text-text-secondary mt-1">{{ 'brief.commands' | i18n }}</p>
              </div>
              <div class="p-3 bg-bg-secondary text-center border border-border-primary">
                <p class="text-2xl font-bold text-cyan-400">{{ analysisResult?.metadata?.queries }}</p>
                <p class="text-xs text-text-secondary mt-1">{{ 'brief.queries' | i18n }}</p>
              </div>
              <div class="p-3 bg-bg-secondary text-center border border-border-primary">
                <p class="text-2xl font-bold text-purple-400">{{ analysisResult?.metadata?.events }}</p>
                <p class="text-xs text-text-secondary mt-1">{{ 'brief.events' | i18n }}</p>
              </div>
              <div class="p-3 bg-bg-secondary text-center border border-border-primary">
                <p class="text-2xl font-bold text-teal-400">{{ analysisResult?.metadata?.ui_components }}</p>
                <p class="text-xs text-text-secondary mt-1">{{ 'brief.uiComponents' | i18n }}</p>
              </div>
            </div>
          </div>

          <!-- Collapsible: Raw Details -->
          <div class="mb-4 space-y-3">
            <!-- Entities -->
            @if (analysisResult?.analysis?.entities?.length) {
              <div class="border border-border-primary overflow-hidden">
                <button (click)="toggleSection('entities')" class="w-full flex items-center justify-between p-3 bg-bg-secondary hover:bg-bg-tertiary transition-colors">
                  <span class="font-medium text-sm text-text-primary"><i class="fa-solid fa-cube"></i> {{ 'brief.entities' | i18n }} ({{ analysisResult.analysis.entities.length }})</span>
                  <svg class="h-4 w-4 text-text-secondary transition-transform" [class.rotate-180]="sectionOpen.entities" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                </button>
                @if (sectionOpen.entities) {
                  <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                      <thead class="bg-bg-secondary text-text-tertiary text-xs uppercase">
                        <tr><th class="px-4 py-2 text-left">{{ 'brief.name' | i18n }}</th><th class="px-4 py-2 text-left">{{ 'brief.entityType' | i18n }}</th><th class="px-4 py-2 text-left">{{ 'brief.description' | i18n }}</th></tr>
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
              <div class="border border-border-primary overflow-hidden">
                <button (click)="toggleSection('commands')" class="w-full flex items-center justify-between p-3 bg-bg-secondary hover:bg-bg-tertiary transition-colors">
                  <span class="font-medium text-sm text-text-primary"><i class="fa-solid fa-bolt"></i> {{ 'brief.commands' | i18n }} ({{ analysisResult.analysis.commands.length }})</span>
                  <svg class="h-4 w-4 text-text-secondary transition-transform" [class.rotate-180]="sectionOpen.commands" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                </button>
                @if (sectionOpen.commands) {
                  <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                      <thead class="bg-bg-secondary text-text-tertiary text-xs uppercase">
                        <tr><th class="px-4 py-2 text-left">{{ 'brief.name' | i18n }}</th><th class="px-4 py-2 text-left">{{ 'brief.target' | i18n }}</th><th class="px-4 py-2 text-left">{{ 'brief.description' | i18n }}</th></tr>
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
              <div class="border border-border-primary overflow-hidden">
                <button (click)="toggleSection('queries')" class="w-full flex items-center justify-between p-3 bg-bg-secondary hover:bg-bg-tertiary transition-colors">
                  <span class="font-medium text-sm text-text-primary"><i class="fa-solid fa-magnifying-glass"></i> {{ 'brief.queries' | i18n }} ({{ analysisResult.analysis.queries.length }})</span>
                  <svg class="h-4 w-4 text-text-secondary transition-transform" [class.rotate-180]="sectionOpen.queries" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                </button>
                @if (sectionOpen.queries) {
                  <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                      <thead class="bg-bg-secondary text-text-tertiary text-xs uppercase">
                        <tr><th class="px-4 py-2 text-left">{{ 'brief.name' | i18n }}</th><th class="px-4 py-2 text-left">{{ 'brief.entities' | i18n }}</th><th class="px-4 py-2 text-left">{{ 'brief.filter' | i18n }}</th></tr>
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
              <div class="border border-border-primary overflow-hidden">
                <button (click)="toggleSection('events')" class="w-full flex items-center justify-between p-3 bg-bg-secondary hover:bg-bg-tertiary transition-colors">
                  <span class="font-medium text-sm text-text-primary"><i class="fa-solid fa-satellite-dish"></i> {{ 'brief.events' | i18n }} ({{ analysisResult.analysis.events.length }})</span>
                  <svg class="h-4 w-4 text-text-secondary transition-transform" [class.rotate-180]="sectionOpen.events" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                </button>
                @if (sectionOpen.events) {
                  <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                      <thead class="bg-bg-secondary text-text-tertiary text-xs uppercase">
                        <tr><th class="px-4 py-2 text-left">{{ 'brief.name' | i18n }}</th><th class="px-4 py-2 text-left">{{ 'brief.source' | i18n }}</th><th class="px-4 py-2 text-left">{{ 'brief.description' | i18n }}</th></tr>
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
              <div class="border border-border-primary overflow-hidden">
                <button (click)="toggleSection('ui_components')" class="w-full flex items-center justify-between p-3 bg-bg-secondary hover:bg-bg-tertiary transition-colors">
                  <span class="font-medium text-sm text-text-primary"><i class="fa-solid fa-puzzle-piece"></i> {{ 'brief.uiComponents' | i18n }} ({{ analysisResult.analysis.ui_components.length }})</span>
                  <svg class="h-4 w-4 text-text-secondary transition-transform" [class.rotate-180]="sectionOpen.ui_components" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                </button>
                @if (sectionOpen.ui_components) {
                  <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                      <thead class="bg-bg-secondary text-text-tertiary text-xs uppercase">
                        <tr><th class="px-4 py-2 text-left">{{ 'brief.name' | i18n }}</th><th class="px-4 py-2 text-left">{{ 'brief.componentType' | i18n }}</th><th class="px-4 py-2 text-left">{{ 'brief.description' | i18n }}</th></tr>
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
              <h3 class="font-medium text-yellow-400 mb-2"><i class="fa-solid fa-triangle-exclamation"></i> {{ 'brief.needClarify' | i18n }} ({{ analysisResult?.analysis?.ambiguities?.length }})</h3>
              <div class="space-y-2">
                @for (ambiguity of analysisResult?.analysis?.ambiguities; track ambiguity.id) {
                  <div class="p-3 bg-yellow-900 bg-opacity-20 border-l-2 border-yellow-500">
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
                  {{ isStartingClarification ? ('brief.clarifying' | i18n) : ('brief.clarifyTitle' | i18n) }}
                </button>
              }
            } @else {
              <a routerLink="/contract-viewer" class="btn btn-primary">
                {{ 'contract.generate' | i18n }} →
              </a>
            }
          </div>

          <!-- Clarification Batch Section -->
          @if (clarificationActive) {
            <div class="clarification-batch-section">
              <div class="clarification-batch-header">
                <h3 class="clarification-batch-title">{{ 'brief.clarify' | i18n }}</h3>
                <p class="clarification-batch-subtitle">{{ 'brief.clarifyCount' | i18n:{count: clarificationAmbiguities.length} }}</p>
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
                      placeholder="{{ 'brief.answerPlaceholder' | i18n }}"
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
              <p class="clarification-progress-text">{{ 'brief.answered' | i18n:{count: answeredCount} }}</p>

              <!-- Submit button -->
              <div class="clarification-submit-row">
                <button (click)="cancelClarification()" class="clarification-cancel-btn">{{ 'brief.cancel' | i18n }}</button>
                <button (click)="submitBatchAnswers()" class="btn btn-primary clarification-submit-btn"
                        [disabled]="answeredCount < clarificationAmbiguities.length || isSubmittingAnswers">
                  @if (isSubmittingAnswers) {
                    {{ 'brief.sending' | i18n }}
                  } @else {
                    <i class="fa-solid fa-paper-plane"></i> {{ 'brief.sendAll' | i18n }} ({{ answeredCount }}/{{ clarificationAmbiguities.length }})
                  }
                </button>
              </div>
            </div>
          }
        </div>
      }
        </div>

        <!-- Right column: Sidebar with Clarify/History tabs -->
        <div class="brief-sidebar">
          <!-- Tab toggle -->
          <div class="sidebar-tabs">
            <button
              type="button"
              class="sidebar-tab"
              [class.active]="rightTab === 'clarify'"
              (click)="rightTab = 'clarify'"
            >
              {{ 'brief.clarify' | i18n }}
              @if (clarifications.length > 0) {
                <span class="tab-badge">{{ clarifications.length }}</span>
              }
            </button>
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

          <!-- Clarify tab panel -->
          @if (rightTab === 'clarify') {
            <div class="sidebar-panel">
              <app-clarification-list [items]="clarifications"></app-clarification-list>
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

      <!-- Analyze Overlay -->
      @if (showAnalyzeOverlay) {
        <app-analyze-overlay
          [visible]="showAnalyzeOverlay"
          (closeOverlay)="onCloseAnalyzeOverlay()"
          (cancelAnalyze)="onCancelAnalyze()"
          #analyzeOverlay
        ></app-analyze-overlay>
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
  rightTab: 'clarify' | 'history' = 'clarify';

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

  // Analyze overlay state
  showAnalyzeOverlay = false;
  private abortController: AbortController | null = null;
  private analyzeTimeoutId: any = null;

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
              // Forward message to overlay component
              const overlayEl = document.querySelector('app-analyze-overlay');
              if (overlayEl && (overlayEl as any).onMessage) {
                (overlayEl as any).onMessage(msg);
              }

              // If final_result or error, cleanup
              if (lastEvent === 'final_result') {
                clearTimeout(this.analyzeTimeoutId);
                this.isAnalyzing = false;
                this.analysisResult = data;
                this.showToast(`Phân tích thành công — ${data.metadata?.entities || 0} entities`, 'success');
                this.cdr.detectChanges();
              } else if (lastEvent === 'error') {
                clearTimeout(this.analyzeTimeoutId);
                this.isAnalyzing = false;
                this.showToast(`Lỗi: ${data}`, 'error');
                this.cdr.detectChanges();
              }
            } catch {
              // data might be plain string for error events
              const msg = { type: lastEvent, data: dataStr };
              const overlayEl = document.querySelector('app-analyze-overlay');
              if (overlayEl && (overlayEl as any).onMessage) {
                (overlayEl as any).onMessage(msg);
              }
              if (lastEvent === 'error') {
                clearTimeout(this.analyzeTimeoutId);
                this.isAnalyzing = false;
                this.showToast(`Lỗi: ${dataStr}`, 'error');
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
        .map(amb => `[${amb.type}]: ${this.clarificationAnswers[amb.id] || ''}`)
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
