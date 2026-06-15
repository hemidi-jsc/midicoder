/**
 * Analysis Result Modal — modal hiển thị kết quả phân tích brief + form làm rõ
 * 2 tabs: Kết quả (analysis results) và Làm rõ (clarification form)
 * Style: #16161e background, sharp corners, IBM Carbon style
 */

import { Component, Input, Output, EventEmitter, inject, ChangeDetectorRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { I18nPipe } from '../../../core/i18n.pipe';

export interface AmbiguityItem {
  id?: string;
  summary: string;
  question: string;
  recommend: string;
}

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
  selector: 'app-analysis-result-modal',
  standalone: true,
  imports: [CommonModule, FormsModule, I18nPipe],
  template: `
    <div class="analysis-modal-backdrop" (click)="closeModal()">
      <div class="analysis-modal-card" (click)="$event.stopPropagation()">

        <!-- Header -->
        <div class="modal-header">
          <div class="modal-title">
            <i class="fa-solid fa-chart-bar"></i>
            <span>{{ 'analysisResult.title' | i18n }}</span>
            @if (analysisResult?.status === 'needs_clarification') {
              <span class="status-badge status-clarify">{{ 'brief.needClarify' | i18n }}</span>
            } @else {
              <span class="status-badge status-ready">{{ 'brief.readyContract' | i18n }}</span>
            }
          </div>
          <button class="modal-close-btn" (click)="closeModal()" title="{{ 'common.close' | i18n }}">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>

        <!-- Tab bar -->
        <div class="modal-tabs">
          <button
            class="modal-tab"
            [class.active]="activeTab === 'result'"
            (click)="activeTab = 'result'"
          >
            <i class="fa-solid fa-list-check"></i> {{ 'analysisResult.tabResult' | i18n }}
          </button>
          <button
            class="modal-tab"
            [class.active]="activeTab === 'clarify'"
            (click)="onClarifyTabClick()"
          >
            <i class="fa-solid fa-pen-to-square"></i> {{ 'analysisResult.tabClarify' | i18n }}
            @if (analysisResult?.analysis?.ambiguities?.length) {
              <span class="tab-count">{{ analysisResult.analysis.ambiguities.length }}</span>
            }
          </button>
        </div>

        <!-- Tab content -->
        <div class="modal-content">

          <!-- ==================== RESULT TAB ==================== -->
          @if (activeTab === 'result') {
            <div class="result-panel">

              <!-- Summary box -->
              @if (analysisResult?.analysis?.summary) {
                <div class="summary-box">
                  <p class="summary-text">{{ analysisResult.analysis.summary }}</p>
                </div>
              }

              <!-- Intent grid: domain, type, scale, quality_score -->
              <div class="intent-grid">
                <div class="intent-item">
                  <span class="intent-label">{{ 'brief.domain' | i18n }}</span>
                  <p class="intent-value">{{ analysisResult?.analysis?.intent?.domain || '—' }}</p>
                </div>
                <div class="intent-item">
                  <span class="intent-label">{{ 'brief.type' | i18n }}</span>
                  <p class="intent-value">{{ analysisResult?.analysis?.intent?.type || '—' }}</p>
                </div>
                <div class="intent-item">
                  <span class="intent-label">{{ 'brief.scale' | i18n }}</span>
                  <p class="intent-value">{{ analysisResult?.analysis?.intent?.scale || '—' }}</p>
                </div>
                <div class="intent-item">
                  <span class="intent-label">{{ 'brief.qualityScore' | i18n }}</span>
                  <div class="confidence-row">
                    <div class="confidence-bar">
                      <div
                        class="confidence-fill"
                        [class.conf-high]="qualityScore >= 0.9"
                        [class.conf-mid]="qualityScore >= 0.7 && qualityScore < 0.9"
                        [class.conf-low]="qualityScore < 0.7"
                        [style.width.%]="qualityScore * 100"
                      ></div>
                    </div>
                    <span class="confidence-pct">
                      {{ (qualityScore * 100).toFixed(0) }}%
                    </span>
                  </div>
                </div>
              </div>

              <!-- Resource stats grid: 12 cards -->
              <div class="resource-stats">
                <div class="stat-card">
                  <p class="stat-num color-blue">{{ analysisResult?.metadata?.entities || 0 }}</p>
                  <p class="stat-label">{{ 'brief.entities' | i18n }}</p>
                </div>
                <div class="stat-card">
                  <p class="stat-num color-orange">{{ analysisResult?.metadata?.commands || 0 }}</p>
                  <p class="stat-label">{{ 'brief.commands' | i18n }}</p>
                </div>
                <div class="stat-card">
                  <p class="stat-num color-cyan">{{ analysisResult?.metadata?.queries || 0 }}</p>
                  <p class="stat-label">{{ 'brief.queries' | i18n }}</p>
                </div>
                <div class="stat-card">
                  <p class="stat-num color-purple">{{ analysisResult?.metadata?.events || 0 }}</p>
                  <p class="stat-label">{{ 'brief.events' | i18n }}</p>
                </div>
                <div class="stat-card">
                  <p class="stat-num color-teal">{{ analysisResult?.metadata?.ui_components || 0 }}</p>
                  <p class="stat-label">{{ 'brief.uiComponents' | i18n }}</p>
                </div>
                <div class="stat-card">
                  <p class="stat-num color-blue">{{ analysisResult?.metadata?.value_objects || 0 }}</p>
                  <p class="stat-label">{{ 'brief.valueObjects' | i18n }}</p>
                </div>
                <div class="stat-card">
                  <p class="stat-num color-orange">{{ analysisResult?.metadata?.guards || 0 }}</p>
                  <p class="stat-label">{{ 'brief.guards' | i18n }}</p>
                </div>
                <div class="stat-card">
                  <p class="stat-num color-cyan">{{ analysisResult?.metadata?.workflows || 0 }}</p>
                  <p class="stat-label">{{ 'brief.workflows' | i18n }}</p>
                </div>
                <div class="stat-card">
                  <p class="stat-num color-purple">{{ analysisResult?.metadata?.aggregates || 0 }}</p>
                  <p class="stat-label">{{ 'brief.aggregates' | i18n }}</p>
                </div>
                <div class="stat-card">
                  <p class="stat-num color-teal">{{ analysisResult?.metadata?.roles || 0 }}</p>
                  <p class="stat-label">{{ 'brief.roles' | i18n }}</p>
                </div>
                <div class="stat-card">
                  <p class="stat-num color-blue">{{ analysisResult?.metadata?.permissions || 0 }}</p>
                  <p class="stat-label">{{ 'brief.permissions' | i18n }}</p>
                </div>
                <div class="stat-card">
                  <p class="stat-num color-orange">{{ analysisResult?.metadata?.state_machines || 0 }}</p>
                  <p class="stat-label">{{ 'brief.stateMachines' | i18n }}</p>
                </div>
              </div>

              <!-- Collapsible tables -->
              <div class="collapsible-sections">

                <!-- Entities -->
                @if (analysisResult?.analysis?.entities?.length) {
                  <div class="collapsible-section">
                    <button class="section-toggle" (click)="toggleSection('entities')">
                      <span class="section-title">
                        <i class="fa-solid fa-cube"></i> {{ 'brief.entities' | i18n }}
                        <span class="section-count">({{ analysisResult.analysis.entities.length }})</span>
                      </span>
                      <i class="fa-solid fa-chevron-down" [class.open]="sectionOpen.entities"></i>
                    </button>
                    @if (sectionOpen.entities) {
                      <div class="section-table-wrap">
                        <table class="section-table">
                          <thead>
                            <tr>
                              <th>{{ 'brief.name' | i18n }}</th>
                              <th>{{ 'brief.entityType' | i18n }}</th>
                              <th>{{ 'brief.description' | i18n }}</th>
                            </tr>
                          </thead>
                          <tbody>
                            @for (e of analysisResult.analysis.entities; track e.name) {
                              <tr>
                                <td class="cell-name color-blue">{{ e.name }}</td>
                                <td class="cell-muted">{{ e.type || '—' }}</td>
                                <td>{{ e.description || '—' }}</td>
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
                  <div class="collapsible-section">
                    <button class="section-toggle" (click)="toggleSection('commands')">
                      <span class="section-title">
                        <i class="fa-solid fa-bolt"></i> {{ 'brief.commands' | i18n }}
                        <span class="section-count">({{ analysisResult.analysis.commands.length }})</span>
                      </span>
                      <i class="fa-solid fa-chevron-down" [class.open]="sectionOpen.commands"></i>
                    </button>
                    @if (sectionOpen.commands) {
                      <div class="section-table-wrap">
                        <table class="section-table">
                          <thead>
                            <tr>
                              <th>{{ 'brief.name' | i18n }}</th>
                              <th>{{ 'brief.target' | i18n }}</th>
                              <th>{{ 'brief.description' | i18n }}</th>
                            </tr>
                          </thead>
                          <tbody>
                            @for (c of analysisResult.analysis.commands; track c.name) {
                              <tr>
                                <td class="cell-name color-orange">{{ c.name }}</td>
                                <td class="cell-muted">{{ c.target || '—' }}</td>
                                <td>{{ c.description || '—' }}</td>
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
                  <div class="collapsible-section">
                    <button class="section-toggle" (click)="toggleSection('queries')">
                      <span class="section-title">
                        <i class="fa-solid fa-magnifying-glass"></i> {{ 'brief.queries' | i18n }}
                        <span class="section-count">({{ analysisResult.analysis.queries.length }})</span>
                      </span>
                      <i class="fa-solid fa-chevron-down" [class.open]="sectionOpen.queries"></i>
                    </button>
                    @if (sectionOpen.queries) {
                      <div class="section-table-wrap">
                        <table class="section-table">
                          <thead>
                            <tr>
                              <th>{{ 'brief.name' | i18n }}</th>
                              <th>{{ 'brief.entities' | i18n }}</th>
                              <th>{{ 'brief.filter' | i18n }}</th>
                            </tr>
                          </thead>
                          <tbody>
                            @for (q of analysisResult.analysis.queries; track q.name) {
                              <tr>
                                <td class="cell-name color-cyan">{{ q.name }}</td>
                                <td class="cell-muted">{{ q.entity || '—' }}</td>
                                <td>{{ q.filter || '—' }}</td>
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
                  <div class="collapsible-section">
                    <button class="section-toggle" (click)="toggleSection('events')">
                      <span class="section-title">
                        <i class="fa-solid fa-satellite-dish"></i> {{ 'brief.events' | i18n }}
                        <span class="section-count">({{ analysisResult.analysis.events.length }})</span>
                      </span>
                      <i class="fa-solid fa-chevron-down" [class.open]="sectionOpen.events"></i>
                    </button>
                    @if (sectionOpen.events) {
                      <div class="section-table-wrap">
                        <table class="section-table">
                          <thead>
                            <tr>
                              <th>{{ 'brief.name' | i18n }}</th>
                              <th>{{ 'brief.source' | i18n }}</th>
                              <th>{{ 'brief.description' | i18n }}</th>
                            </tr>
                          </thead>
                          <tbody>
                            @for (ev of analysisResult.analysis.events; track ev.name) {
                              <tr>
                                <td class="cell-name color-purple">{{ ev.name }}</td>
                                <td class="cell-muted">{{ ev.source || '—' }}</td>
                                <td>{{ ev.description || '—' }}</td>
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
                  <div class="collapsible-section">
                    <button class="section-toggle" (click)="toggleSection('ui_components')">
                      <span class="section-title">
                        <i class="fa-solid fa-puzzle-piece"></i> {{ 'brief.uiComponents' | i18n }}
                        <span class="section-count">({{ analysisResult.analysis.ui_components.length }})</span>
                      </span>
                      <i class="fa-solid fa-chevron-down" [class.open]="sectionOpen.ui_components"></i>
                    </button>
                    @if (sectionOpen.ui_components) {
                      <div class="section-table-wrap">
                        <table class="section-table">
                          <thead>
                            <tr>
                              <th>{{ 'brief.name' | i18n }}</th>
                              <th>{{ 'brief.componentType' | i18n }}</th>
                              <th>{{ 'brief.description' | i18n }}</th>
                            </tr>
                          </thead>
                          <tbody>
                            @for (uc of analysisResult.analysis.ui_components; track uc.name) {
                              <tr>
                                <td class="cell-name color-teal">{{ uc.name }}</td>
                                <td class="cell-muted">{{ uc.type || '—' }}</td>
                                <td>{{ uc.description || '—' }}</td>
                              </tr>
                            }
                          </tbody>
                        </table>
                      </div>
                    }
                  </div>
                }

                <!-- Value Objects -->
                @if (analysisResult?.analysis?.value_objects?.length) {
                  <div class="collapsible-section">
                    <button class="section-toggle" (click)="toggleSection('value_objects')">
                      <span class="section-title">
                        <i class="fa-solid fa-gem"></i> {{ 'brief.valueObjects' | i18n }}
                        <span class="section-count">({{ analysisResult.analysis.value_objects.length }})</span>
                      </span>
                      <i class="fa-solid fa-chevron-down" [class.open]="sectionOpen.value_objects"></i>
                    </button>
                    @if (sectionOpen.value_objects) {
                      <div class="section-table-wrap">
                        <table class="section-table">
                          <thead>
                            <tr>
                              <th>{{ 'brief.name' | i18n }}</th>
                              <th>{{ 'brief.description' | i18n }}</th>
                              <th>{{ 'brief.fields' | i18n }}</th>
                            </tr>
                          </thead>
                          <tbody>
                            @for (vo of analysisResult.analysis.value_objects; track vo.name) {
                              <tr>
                                <td class="cell-name color-blue">{{ vo.name }}</td>
                                <td>{{ vo.description || '—' }}</td>
                                <td class="cell-muted">{{ (vo.fields || []).join(', ') || '—' }}</td>
                              </tr>
                            }
                          </tbody>
                        </table>
                      </div>
                    }
                  </div>
                }

                <!-- Guards -->
                @if (analysisResult?.analysis?.guards?.length) {
                  <div class="collapsible-section">
                    <button class="section-toggle" (click)="toggleSection('guards')">
                      <span class="section-title">
                        <i class="fa-solid fa-shield-halved"></i> {{ 'brief.guards' | i18n }}
                        <span class="section-count">({{ analysisResult.analysis.guards.length }})</span>
                      </span>
                      <i class="fa-solid fa-chevron-down" [class.open]="sectionOpen.guards"></i>
                    </button>
                    @if (sectionOpen.guards) {
                      <div class="section-table-wrap">
                        <table class="section-table">
                          <thead>
                            <tr>
                              <th>{{ 'brief.name' | i18n }}</th>
                              <th>{{ 'brief.target' | i18n }}</th>
                              <th>{{ 'brief.description' | i18n }}</th>
                            </tr>
                          </thead>
                          <tbody>
                            @for (g of analysisResult.analysis.guards; track g.name) {
                              <tr>
                                <td class="cell-name color-orange">{{ g.name }}</td>
                                <td class="cell-muted">{{ g.target || '—' }}</td>
                                <td>{{ g.description || '—' }}</td>
                              </tr>
                            }
                          </tbody>
                        </table>
                      </div>
                    }
                  </div>
                }

                <!-- Workflows -->
                @if (analysisResult?.analysis?.workflows?.length) {
                  <div class="collapsible-section">
                    <button class="section-toggle" (click)="toggleSection('workflows')">
                      <span class="section-title">
                        <i class="fa-solid fa-diagram-project"></i> {{ 'brief.workflows' | i18n }}
                        <span class="section-count">({{ analysisResult.analysis.workflows.length }})</span>
                      </span>
                      <i class="fa-solid fa-chevron-down" [class.open]="sectionOpen.workflows"></i>
                    </button>
                    @if (sectionOpen.workflows) {
                      <div class="section-table-wrap">
                        <table class="section-table">
                          <thead>
                            <tr>
                              <th>{{ 'brief.name' | i18n }}</th>
                              <th>{{ 'brief.trigger' | i18n }}</th>
                              <th>{{ 'brief.description' | i18n }}</th>
                            </tr>
                          </thead>
                          <tbody>
                            @for (w of analysisResult.analysis.workflows; track w.name) {
                              <tr>
                                <td class="cell-name color-cyan">{{ w.name }}</td>
                                <td class="cell-muted">{{ w.trigger || '—' }}</td>
                                <td>{{ w.description || '—' }}</td>
                              </tr>
                            }
                          </tbody>
                        </table>
                      </div>
                    }
                  </div>
                }

                <!-- Aggregates -->
                @if (analysisResult?.analysis?.aggregates?.length) {
                  <div class="collapsible-section">
                    <button class="section-toggle" (click)="toggleSection('aggregates')">
                      <span class="section-title">
                        <i class="fa-solid fa-sitemap"></i> {{ 'brief.aggregates' | i18n }}
                        <span class="section-count">({{ analysisResult.analysis.aggregates.length }})</span>
                      </span>
                      <i class="fa-solid fa-chevron-down" [class.open]="sectionOpen.aggregates"></i>
                    </button>
                    @if (sectionOpen.aggregates) {
                      <div class="section-table-wrap">
                        <table class="section-table">
                          <thead>
                            <tr>
                              <th>{{ 'brief.name' | i18n }}</th>
                              <th>{{ 'brief.rootEntity' | i18n }}</th>
                              <th>{{ 'brief.memberEntities' | i18n }}</th>
                            </tr>
                          </thead>
                          <tbody>
                            @for (a of analysisResult.analysis.aggregates; track a.name) {
                              <tr>
                                <td class="cell-name color-purple">{{ a.name }}</td>
                                <td class="cell-muted">{{ a.root_entity || '—' }}</td>
                                <td>{{ (a.member_entities || []).join(', ') || '—' }}</td>
                              </tr>
                            }
                          </tbody>
                        </table>
                      </div>
                    }
                  </div>
                }

                <!-- Roles -->
                @if (analysisResult?.analysis?.roles?.length) {
                  <div class="collapsible-section">
                    <button class="section-toggle" (click)="toggleSection('roles')">
                      <span class="section-title">
                        <i class="fa-solid fa-users"></i> {{ 'brief.roles' | i18n }}
                        <span class="section-count">({{ analysisResult.analysis.roles.length }})</span>
                      </span>
                      <i class="fa-solid fa-chevron-down" [class.open]="sectionOpen.roles"></i>
                    </button>
                    @if (sectionOpen.roles) {
                      <div class="section-table-wrap">
                        <table class="section-table">
                          <thead>
                            <tr>
                              <th>{{ 'brief.name' | i18n }}</th>
                              <th>{{ 'brief.description' | i18n }}</th>
                              <th>{{ 'brief.permissions' | i18n }}</th>
                            </tr>
                          </thead>
                          <tbody>
                            @for (r of analysisResult.analysis.roles; track r.name) {
                              <tr>
                                <td class="cell-name color-teal">{{ r.name }}</td>
                                <td>{{ r.description || '—' }}</td>
                                <td class="cell-muted">{{ (r.permissions || []).join(', ') || '—' }}</td>
                              </tr>
                            }
                          </tbody>
                        </table>
                      </div>
                    }
                  </div>
                }

                <!-- Permissions -->
                @if (analysisResult?.analysis?.permissions?.length) {
                  <div class="collapsible-section">
                    <button class="section-toggle" (click)="toggleSection('permissions')">
                      <span class="section-title">
                        <i class="fa-solid fa-key"></i> {{ 'brief.permissions' | i18n }}
                        <span class="section-count">({{ analysisResult.analysis.permissions.length }})</span>
                      </span>
                      <i class="fa-solid fa-chevron-down" [class.open]="sectionOpen.permissions"></i>
                    </button>
                    @if (sectionOpen.permissions) {
                      <div class="section-table-wrap">
                        <table class="section-table">
                          <thead>
                            <tr>
                              <th>{{ 'brief.name' | i18n }}</th>
                              <th>{{ 'brief.resource' | i18n }}</th>
                              <th>{{ 'brief.action' | i18n }}</th>
                            </tr>
                          </thead>
                          <tbody>
                            @for (p of analysisResult.analysis.permissions; track p.name) {
                              <tr>
                                <td class="cell-name color-blue">{{ p.name }}</td>
                                <td class="cell-muted">{{ p.resource || '—' }}</td>
                                <td>{{ p.action || '—' }}</td>
                              </tr>
                            }
                          </tbody>
                        </table>
                      </div>
                    }
                  </div>
                }

                <!-- State Machines -->
                @if (analysisResult?.analysis?.state_machines?.length) {
                  <div class="collapsible-section">
                    <button class="section-toggle" (click)="toggleSection('state_machines')">
                      <span class="section-title">
                        <i class="fa-solid fa-rotate"></i> {{ 'brief.stateMachines' | i18n }}
                        <span class="section-count">({{ analysisResult.analysis.state_machines.length }})</span>
                      </span>
                      <i class="fa-solid fa-chevron-down" [class.open]="sectionOpen.state_machines"></i>
                    </button>
                    @if (sectionOpen.state_machines) {
                      <div class="section-table-wrap">
                        <table class="section-table">
                          <thead>
                            <tr>
                              <th>{{ 'brief.name' | i18n }}</th>
                              <th>{{ 'brief.smEntity' | i18n }}</th>
                              <th>{{ 'brief.states' | i18n }}</th>
                            </tr>
                          </thead>
                          <tbody>
                            @for (sm of analysisResult.analysis.state_machines; track sm.name) {
                              <tr>
                                <td class="cell-name color-orange">{{ sm.name }}</td>
                                <td class="cell-muted">{{ sm.entity || '—' }}</td>
                                <td>{{ (sm.states || []).join(', ') || '—' }}</td>
                              </tr>
                            }
                          </tbody>
                        </table>
                      </div>
                    }
                  </div>
                }
              </div>

              <!-- Ambiguities list -->
              @if (analysisResult?.analysis?.ambiguities?.length) {
                <div class="ambiguities-section">
                  <h3 class="ambiguities-title">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    {{ 'brief.needClarify' | i18n }} ({{ analysisResult.analysis.ambiguities.length }})
                  </h3>
                  @for (amb of analysisResult.analysis.ambiguities; track amb.id || amb.summary) {
                    <div class="ambiguity-item">
                      <p class="ambiguity-desc">
                        <strong>{{ amb.summary }}</strong>
                      </p>
                      <p class="ambiguity-question">{{ amb.question }}</p>
                      @if (amb.recommend) {
                        <p class="ambiguity-recommend"><i class="fa-solid fa-lightbulb"></i> {{ amb.recommend }}</p>
                      }
                    </div>
                  }
                </div>
              }

            </div>
          }

          <!-- ==================== CLARIFY TAB ==================== -->
          @if (activeTab === 'clarify') {
            <div class="clarify-panel">

              <!-- Clarification header -->
              @if (clarificationAmbiguities.length > 0) {
                <div class="clarify-header">
                  <h3 class="clarify-title">{{ 'brief.clarify' | i18n }}</h3>
                  <p class="clarify-subtitle">{{ 'brief.clarifyCount' | i18n:{count: clarificationAmbiguities.length} }}</p>
                </div>

                <!-- Ambiguity cards with textareas -->
                <div class="clarify-cards">
                  @for (amb of clarificationAmbiguities; track amb.id || amb.summary) {
                    <div
                      class="clarify-card"
                      [class.answered]="clarificationAnswers[amb.id || amb.summary]?.trim()"
                      [class.blocker]="isBlocker(amb)"
                    >
                      <div class="clarify-card-header">
                        <div class="clarify-card-title-row">
                          <span class="clarify-card-title">{{ amb.summary }}</span>
                          @if (isBlocker(amb)) {
                            <span class="badge badge-blocker">{{ 'brief.blocker' | i18n }}</span>
                          } @else {
                            <span class="badge badge-optional">{{ 'brief.optional' | i18n }}</span>
                          }
                        </div>
                        @if (clarificationAnswers[amb.id || amb.summary]?.trim()) {
                          <span class="answered-check"><i class="fa-solid fa-check"></i></span>
                        }
                      </div>
                      <p class="clarify-question">{{ amb.question }}</p>
                      @if (amb.recommend) {
                        <div class="clarify-recommend-row">
                          <p class="clarify-recommend-text"><i class="fa-solid fa-lightbulb"></i> {{ amb.recommend }}</p>
                          <button class="btn-use-recommend" (click)="useRecommendation(amb.id || amb.summary)">
                            {{ 'brief.useRecommend' | i18n }}
                          </button>
                        </div>
                      }
                      <textarea
                        [(ngModel)]="clarificationAnswers[amb.id || amb.summary]"
                        placeholder="{{ 'brief.answerPlaceholder' | i18n }}"
                        rows="2"
                        class="clarify-textarea"
                      ></textarea>
                    </div>
                  }
                </div>

                <!-- Progress bar -->
                <div class="clarify-progress-wrap">
                  <div class="clarify-progress-bar">
                    <div
                      class="clarify-progress-fill"
                      [style.width.%]="progressPct"
                    ></div>
                  </div>
                  <p class="clarify-progress-text">
                    {{ 'brief.answered' | i18n:{count: answeredCount} }}
                    @if (totalBlockers > 0) {
                      <span class="blocker-progress">
                        {{ 'brief.blockersProgress' | i18n: {answered: blockerAnsweredCount, total: totalBlockers} }}
                      </span>
                    }
                  </p>
                </div>

                <!-- Submit row -->
                <div class="clarify-submit-row">
                  <button class="btn btn-secondary" (click)="cancelClarification()">
                    {{ 'brief.cancel' | i18n }}
                  </button>
                  <button
                    class="btn btn-primary"
                    (click)="submitAnswers()"
                    [disabled]="!canSubmit() || isSubmitting"
                  >
                    @if (isSubmitting) {
                      <i class="fa-solid fa-spinner fa-spin"></i> {{ 'brief.sending' | i18n }}
                    } @else {
                      <i class="fa-solid fa-paper-plane"></i> {{ 'brief.sendAll' | i18n }} ({{ answeredCount }}/{{ clarificationAmbiguities.length }})
                    }
                  </button>
                </div>

              } @else {
                <!-- No ambiguities -->
                <div class="clarify-empty">
                  <i class="fa-solid fa-check-circle"></i>
                  <p>{{ 'brief.noAmbiguity' | i18n }}</p>
                </div>
              }

            </div>
          }

        </div>

        <!-- Footer (Result tab only) -->
        @if (activeTab === 'result') {
          <div class="modal-footer">
            <span class="footer-info">
              @if (analysisResult?.metadata?.brief_id) {
                <span class="footer-brief-id">{{ analysisResult.metadata.brief_id }}</span>
              }
            </span>
            <div class="footer-actions">
              @if (analysisResult?.status === 'needs_clarification') {
                <button class="btn btn-primary" (click)="onClarifyTabClick()">
                  <i class="fa-solid fa-pen-to-square"></i> {{ 'analysisResult.startClarify' | i18n }}
                </button>
              } @else {
                <button class="btn btn-primary" (click)="goToContract.emit()">
                  <i class="fa-solid fa-file-contract"></i> {{ 'analysisResult.createContract' | i18n }}
                </button>
              }
            </div>
          </div>
        }

      </div>
    </div>
  `,
  styles: [`
    /* ===== Backdrop ===== */
    .analysis-modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.85);
      backdrop-filter: blur(4px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10000;
      padding: 2rem;
    }

    /* ===== Modal Card ===== */
    .analysis-modal-card {
      background: #16161e;
      border: 1px solid rgba(252, 103, 103, 0.25);
      width: 100%;
      max-width: 900px;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      box-shadow: 0 0 40px rgba(252, 103, 103, 0.15);
    }

    /* ===== Header ===== */
    .modal-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 18px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      flex-shrink: 0;
    }

    .modal-title {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 1rem;
      font-weight: 600;
      color: #fff;
    }

    .modal-title i {
      color: #fc6767;
      font-size: 1.1rem;
    }

    .status-badge {
      font-size: 0.6875rem;
      padding: 2px 8px;
      font-weight: 600;
    }

    .status-clarify {
      background: rgba(210, 168, 58, 0.2);
      color: #d2a83a;
      border: 1px solid rgba(210, 168, 58, 0.3);
    }

    .status-ready {
      background: rgba(63, 185, 80, 0.2);
      color: #3fb950;
      border: 1px solid rgba(63, 185, 80, 0.3);
    }

    .modal-close-btn {
      background: none;
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: rgba(255, 255, 255, 0.5);
      font-size: 1rem;
      padding: 4px 10px;
      cursor: pointer;
      transition: all 0.2s;
    }

    .modal-close-btn:hover {
      color: #fff;
      border-color: #fc6767;
    }

    /* ===== Tabs ===== */
    .modal-tabs {
      display: flex;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      flex-shrink: 0;
    }

    .modal-tab {
      padding: 8px 16px;
      background: none;
      border: none;
      color: rgba(255, 255, 255, 0.4);
      font-size: 0.8125rem;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }

    .modal-tab:hover {
      color: rgba(255, 255, 255, 0.7);
    }

    .modal-tab.active {
      color: #fc6767;
      border-bottom: 2px solid #fc6767;
    }

    .tab-count {
      background: rgba(210, 168, 58, 0.2);
      color: #d2a83a;
      font-size: 0.6875rem;
      padding: 1px 6px;
      font-weight: 600;
    }

    /* ===== Content ===== */
    .modal-content {
      flex: 1;
      overflow-y: auto;
      min-height: 0;
    }

    .modal-content::-webkit-scrollbar {
      width: 5px;
    }

    .modal-content::-webkit-scrollbar-thumb {
      background: rgba(252, 103, 103, 0.2);
    }

    .result-panel {
      padding: 14px;
    }

    /* ===== Summary box ===== */
    .summary-box {
      margin-bottom: 12px;
      padding: 10px 14px;
      background: rgba(56, 132, 255, 0.08);
      border-left: 3px solid #3884ff;
    }

    .summary-text {
      font-size: 0.8125rem;
      color: rgba(255, 255, 255, 0.7);
      line-height: 1.5;
      margin: 0;
    }

    /* ===== Intent grid ===== */
    .intent-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
      margin-bottom: 12px;
    }

    .intent-item {
      padding: 8px 10px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.06);
    }

    .intent-label {
      display: block;
      font-size: 0.6875rem;
      color: rgba(255, 255, 255, 0.4);
      text-transform: uppercase;
      margin-bottom: 4px;
    }

    .intent-value {
      font-size: 0.8125rem;
      font-weight: 600;
      color: #fff;
      margin: 0;
    }

    .confidence-row {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .confidence-bar {
      flex: 1;
      height: 6px;
      background: rgba(255, 255, 255, 0.06);
      overflow: hidden;
    }

    .confidence-fill {
      height: 100%;
      transition: width 0.5s;
    }

    .conf-high { background-color: #3fb950; }
    .conf-mid { background-color: #d2a83a; }
    .conf-low  { background-color: #f85149; }

    .confidence-pct {
      font-size: 0.75rem;
      font-weight: 600;
    }

    .confidence-pct.conf-high { color: #3fb950; }
    .confidence-pct.conf-mid { color: #d2a83a; }
    .confidence-pct.conf-low  { color: #f85149; }

    /* ===== Resource stats ===== */
    .resource-stats {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      margin-bottom: 14px;
    }

    .stat-card {
      text-align: center;
      padding: 8px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.06);
    }

    .stat-num {
      display: block;
      font-size: 1.25rem;
      font-weight: 700;
      margin: 0 0 2px 0;
    }

    .stat-label {
      font-size: 0.625rem;
      color: rgba(255, 255, 255, 0.4);
      text-transform: uppercase;
      margin: 0;
    }

    .color-blue   { color: #58a6ff; }
    .color-orange { color: #f0883e; }
    .color-cyan   { color: #39c5cf; }
    .color-purple { color: #bc8cff; }
    .color-teal   { color: #56d364; }

    /* ===== Collapsible sections ===== */
    .collapsible-sections {
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-bottom: 14px;
    }

    .collapsible-section {
      border: 1px solid rgba(255, 255, 255, 0.06);
      overflow: hidden;
    }

    .section-toggle {
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 12px;
      background: rgba(255, 255, 255, 0.03);
      border: none;
      color: #fff;
      cursor: pointer;
      transition: background 0.2s;
    }

    .section-toggle:hover {
      background: rgba(255, 255, 255, 0.06);
    }

    .section-title {
      font-size: 0.8125rem;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .section-title i {
      color: #fc6767;
      font-size: 0.75rem;
    }

    .section-count {
      color: rgba(255, 255, 255, 0.3);
      font-weight: 400;
    }

    .section-toggle .fa-chevron-down {
      font-size: 0.75rem;
      color: rgba(255, 255, 255, 0.4);
      transition: transform 0.2s;
    }

    .section-toggle .fa-chevron-down.open {
      transform: rotate(180deg);
    }

    .section-table-wrap {
      overflow-x: auto;
    }

    .section-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.75rem;
    }

    .section-table thead {
      background: rgba(255, 255, 255, 0.03);
    }

    .section-table th {
      padding: 6px 12px;
      text-align: left;
      font-size: 0.6875rem;
      color: rgba(255, 255, 255, 0.4);
      text-transform: uppercase;
      font-weight: 500;
    }

    .section-table td {
      padding: 6px 12px;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      color: rgba(255, 255, 255, 0.7);
    }

    .cell-name {
      font-weight: 600;
    }

    .cell-muted {
      color: rgba(255, 255, 255, 0.35);
    }

    /* ===== Ambiguities section ===== */
    .ambiguities-section {
      margin-top: 4px;
    }

    .ambiguities-title {
      font-size: 0.8125rem;
      font-weight: 600;
      color: #d2a83a;
      margin: 0 0 8px 0;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .ambiguity-item {
      padding: 8px 12px;
      background: rgba(210, 168, 58, 0.08);
      border-left: 2px solid #d2a83a;
      margin-bottom: 6px;
    }

    .ambiguity-desc {
      font-size: 0.75rem;
      color: rgba(255, 255, 255, 0.85);
      margin: 0;
      font-weight: 500;
    }

    .ambiguity-question {
      font-size: 0.6875rem;
      color: rgba(255, 255, 255, 0.6);
      margin: 3px 0 0 0;
    }

    .ambiguity-recommend {
      font-size: 0.65rem;
      color: rgba(63, 185, 80, 0.9);
      margin: 3px 0 0 0;
    }

    /* ===== Clarify panel ===== */
    .clarify-panel {
      padding: 14px;
    }

    .clarify-header {
      margin-bottom: 12px;
    }

    .clarify-title {
      font-size: 0.9375rem;
      font-weight: 600;
      color: #fff;
      margin: 0 0 4px 0;
    }

    .clarify-subtitle {
      font-size: 0.75rem;
      color: rgba(255, 255, 255, 0.4);
      margin: 0;
    }

    .clarify-cards {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-bottom: 12px;
    }

    .clarify-card {
      padding: 10px 12px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.06);
      transition: border-color 0.2s;
    }

    .clarify-card.answered {
      border-color: rgba(63, 185, 80, 0.3);
    }

    .clarify-card.blocker {
      border-color: rgba(248, 81, 73, 0.3);
      background: rgba(248, 81, 73, 0.05);
    }

    .clarify-card.blocker.answered {
      border-color: rgba(63, 185, 80, 0.4);
      background: rgba(63, 185, 80, 0.05);
    }

    .clarify-card-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      margin-bottom: 6px;
    }

    .clarify-card-title-row {
      display: flex;
      align-items: center;
      gap: 6px;
      flex: 1;
    }

    .badge {
      font-size: 0.6rem;
      padding: 1px 5px;
      font-weight: 700;
      letter-spacing: 0.05em;
    }

    .badge-blocker {
      background: rgba(248, 81, 73, 0.2);
      color: #f85149;
      border: 1px solid rgba(248, 81, 73, 0.3);
    }

    .badge-optional {
      background: rgba(255, 255, 255, 0.06);
      color: rgba(255, 255, 255, 0.35);
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .clarify-card-title {
      font-size: 0.8125rem;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.85);
    }

    .answered-check {
      color: #3fb950;
      font-size: 0.875rem;
      font-weight: 700;
    }

    .clarify-question {
      font-size: 0.75rem;
      color: rgba(255, 255, 255, 0.7);
      margin: 0 0 4px 0;
      line-height: 1.4;
    }

    .clarify-recommend-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 6px;
      padding: 4px 8px;
      background: rgba(63, 185, 80, 0.06);
      border: 1px dashed rgba(63, 185, 80, 0.2);
    }

    .clarify-recommend-text {
      font-size: 0.6875rem;
      color: rgba(63, 185, 80, 0.9);
      margin: 0;
      font-style: italic;
      flex: 1;
    }

    .btn-use-recommend {
      font-size: 0.6875rem;
      padding: 2px 8px;
      background: rgba(63, 185, 80, 0.15);
      color: #3fb950;
      border: 1px solid rgba(63, 185, 80, 0.3);
      cursor: pointer;
      white-space: nowrap;
      flex-shrink: 0;
      transition: background 0.15s;
    }

    .btn-use-recommend:hover {
      background: rgba(63, 185, 80, 0.25);
    }

    .clarify-textarea {
      width: 100%;
      background: rgba(0, 0, 0, 0.2);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: #fff;
      font-size: 0.75rem;
      padding: 6px 10px;
      font-family: inherit;
      resize: vertical;
      transition: border-color 0.2s;
    }

    .clarify-textarea:focus {
      outline: none;
      border-color: #fc6767;
    }

    .clarify-textarea::placeholder {
      color: rgba(255, 255, 255, 0.25);
    }

    /* Progress */
    .clarify-progress-wrap {
      margin-bottom: 10px;
    }

    .clarify-progress-bar {
      height: 4px;
      background: rgba(255, 255, 255, 0.06);
      overflow: hidden;
      margin-bottom: 4px;
    }

    .clarify-progress-fill {
      height: 100%;
      background: #fc6767;
      transition: width 0.3s;
    }

    .clarify-progress-text {
      font-size: 0.6875rem;
      color: rgba(255, 255, 255, 0.4);
      margin: 0;
    }

    /* Submit row */
    .clarify-submit-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    /* ===== Clarify empty state ===== */
    .clarify-empty {
      text-align: center;
      padding: 2rem;
      color: rgba(255, 255, 255, 0.3);
    }

    .clarify-empty i {
      font-size: 2rem;
      color: #3fb950;
      margin-bottom: 8px;
      display: block;
    }

    .clarify-empty p {
      font-size: 0.85rem;
      margin: 0;
    }

    /* ===== Footer ===== */
    .modal-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 18px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      flex-shrink: 0;
    }

    .footer-info {
      font-size: 0.75rem;
      color: rgba(255, 255, 255, 0.3);
    }

    .footer-brief-id {
      font-family: monospace;
    }

    .footer-actions {
      display: flex;
      gap: 8px;
    }

    /* ===== Buttons ===== */
    .btn {
      padding: 6px 16px;
      font-size: 0.8rem;
      font-weight: 500;
      cursor: pointer;
      border: none;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .btn-primary {
      background: #fc6767;
      color: #fff;
    }

    .btn-primary:hover:not(:disabled) {
      background: #e55a5a;
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.08);
      color: rgba(255, 255, 255, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.15);
    }

    .btn-secondary:hover:not(:disabled) {
      background: rgba(255, 255, 255, 0.12);
    }
  `]
})
export class AnalysisResultModalComponent implements AfterViewInit {
  private cdr = inject(ChangeDetectorRef);

  // === Inputs / Outputs ===
  @Input() analysisResult: any = null;
  @Input() initialTab: 'result' | 'clarify' = 'result';
  @Output() close = new EventEmitter<void>();
  @Output() submitClarification = new EventEmitter<any[]>();
  @Output() goToContract = new EventEmitter<void>();

  // === Tabs ===
  activeTab: 'result' | 'clarify' = 'result';

  ngAfterViewInit(): void {
    // All @Inputs are guaranteed to be bound by now
    this.activeTab = this.initialTab;
    if (this.initialTab === 'clarify' && this.analysisResult) {
      this.startClarification();
      this.cdr.detectChanges();
    }
  }

  // === Collapsible sections ===
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

  // === Clarification state ===
  clarificationAmbiguities: AmbiguityItem[] = [];
  clarificationAnswers: Record<string, string> = {};

  get qualityScore(): number {
    // Fallback: use metadata.quality_score, then analysis.quality_score, then confidence
    return this.analysisResult?.metadata?.quality_score
      ?? this.analysisResult?.analysis?.quality_score
      ?? (this.analysisResult?.metadata?.confidence ?? 0.5);
  }

  get blockers(): string[] {
    return this.analysisResult?.metadata?.blockers
      ?? this.analysisResult?.analysis?.blockers
      ?? [];
  }

  isBlocker(amb: AmbiguityItem): boolean {
    const id = amb.id || amb.summary;
    return this.blockers.includes(id);
  }

  get answeredCount(): number {
    return this.clarificationAmbiguities.filter(amb => {
      const key = amb.id || amb.summary;
      return this.clarificationAnswers[key]?.trim();
    }).length;
  }

  get blockerAnsweredCount(): number {
    return this.clarificationAmbiguities.filter(amb => {
      if (!this.isBlocker(amb)) return false;
      const key = amb.id || amb.summary;
      return this.clarificationAnswers[key]?.trim();
    }).length;
  }

  get totalBlockers(): number {
    return this.clarificationAmbiguities.filter(amb => this.isBlocker(amb)).length;
  }

  get progressPct(): number {
    if (!this.clarificationAmbiguities.length) return 0;
    return Math.round((this.answeredCount / this.clarificationAmbiguities.length) * 100);
  }

  canSubmit(): boolean {
    // Submit enabled when all blockers answered (optional: all ambiguities)
    return this.blockerAnsweredCount >= this.totalBlockers && this.answeredCount > 0;
  }

  isSubmitting = false;

  // === Methods ===
  toggleSection(key: keyof SectionOpenState): void {
    this.sectionOpen[key] = !this.sectionOpen[key];
  }

  startClarification(): void {
    const ambiguities = this.analysisResult?.analysis?.ambiguities || [];
    this.clarificationAmbiguities = ambiguities.map((a: AmbiguityItem) => ({ ...a }));
    this.clarificationAnswers = {};
    this.activeTab = 'clarify';
    this.cdr.markForCheck();
  }

  cancelClarification(): void {
    this.activeTab = 'result';
    this.clarificationAmbiguities = [];
    this.clarificationAnswers = {};
    this.isSubmitting = false;
    this.cdr.markForCheck();
  }

  submitAnswers(): void {
    if (!this.canSubmit()) return;
    this.isSubmitting = true;

    // Only emit answers that have non-empty text
    const answers = this.clarificationAmbiguities
      .map(amb => {
        const key = amb.id || amb.summary;
        return {
          id: amb.id,
          summary: amb.summary,
          question: amb.question,
          recommend: amb.recommend,
          answer: this.clarificationAnswers[key] || ''
        };
      })
      .filter(a => a.answer.trim()); // Only send answered items

    this.submitClarification.emit(answers);
    // isSubmitting reset by parent after response
  }

  useRecommendation(key: string): void {
    const amb = this.clarificationAmbiguities.find(a => (a.id || a.summary) === key);
    if (amb && amb.recommend) {
      this.clarificationAnswers[key] = amb.recommend;
      this.cdr.markForCheck();
    }
  }

  onClarifyTabClick(): void {
    if (this.activeTab !== 'clarify') {
      this.startClarification();
    }
  }

  closeModal(): void {
    this.close.emit();
  }
}
