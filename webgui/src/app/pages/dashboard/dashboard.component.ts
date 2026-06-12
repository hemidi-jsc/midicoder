/**
 * Component Dashboard
 * Layout:
 *   Row 1: ProjectInfoCard (50%) | VersionInfoCard (50%)
 *   Row 2: Pipeline progress (khi có versions)
 *   State: chưa có project → form tạo project
 *   State: có project, chưa có version → card tạo version
 */

import { Component, OnInit, inject, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';

import { I18nPipe } from '../../core/i18n.pipe';
import { I18nService } from '../../core/i18n.service';
import { DOCS_BASE } from '../../core/app.constants';
import { PipelineStore, PhaseStatus } from '../../core/pipeline.store';
import { ApiService, ProjectInfo } from '../../core/api.service';
import { VersionService, VersionInfo } from '../../core/version.service';
import { ProjectInfoCardComponent } from '../../components/shared/project-info-card/project-info-card';
import { VersionInfoCardComponent, VersionMetadata } from '../../components/shared/version-info-card/version-info-card';
import { ProjectCreateFormComponent } from '../../components/shared/project-create-form/project-create-form';
import { VersionCreateFormComponent } from '../../components/shared/version-create-form/version-create-form';
import { ArtifactsStatsCardComponent, ArtifactStatsData } from '../../components/shared/artifacts-stats-card/artifacts-stats-card';
import { ActivityHistoryCardComponent } from '../../components/shared/activity-history-card/activity-history-card';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule, FormsModule, I18nPipe,
    ProjectInfoCardComponent,
    VersionInfoCardComponent,
    ProjectCreateFormComponent,
    VersionCreateFormComponent,
    ArtifactsStatsCardComponent,
    ActivityHistoryCardComponent,
  ],
  template: `
    <div class="dashboard-container">
      <!-- Header -->
      <div class="dashboard-header">
        <div class="page-header-row">
          <h1 class="dashboard-title">{{ 'dashboard.title' | i18n }}</h1>
          <a href="{{ docsUrl }}" target="_blank" rel="noopener" class="docs-link">{{ 'common.readGuide' | i18n }}</a>
        </div>
        <p class="dashboard-subtitle">
          {{ 'dashboard.project' | i18n }}<span class="text-white">{{ projectName() || ('dashboard.notInitialized' | i18n) }}</span>
          @if (activeVersion()) {
            &nbsp;— {{ activeVersion() }}
          }
          @if (pipelineInitialized()) {
            &nbsp;|&nbsp; {{ 'dashboard.progress' | i18n }}<span class="text-white">{{ overallProgress() }}</span>%
          }
        </p>
      </div>

      <!-- State 1: Chưa có project -->
      @if (!workspaceInitialized()) {
        <div class="card init-card">
          <div class="init-content">
            <h2 class="init-title">{{ 'dashboard.createImport' | i18n }}</h2>
            <p class="init-desc">{{ 'dashboard.createImportDesc' | i18n }}</p>
            <app-project-create-form />
          </div>
        </div>
      }

      <!-- State 2: Có project, chưa có version -->
      @if (workspaceInitialized() && !pipelineInitialized()) {
        <div class="card init-card">
          <div class="init-content">
            <h2 class="init-title">{{ 'dashboard.createFirstVersion' | i18n }}</h2>
            <p class="init-desc">{{ 'dashboard.createFirstVersionDesc' | i18n }}</p>
            <button class="btn-primary-large" (click)="showCreateVersionModal = true">
              {{ 'dashboard.createVersion' | i18n }}
            </button>
          </div>
        </div>
      }

      <!-- State 3: Có project + có versions → 2 cards + pipeline -->
      @if (workspaceInitialized() && pipelineInitialized()) {

        <!-- Row 1: Project + Version cards (50/50) -->
        <div class="info-cards-row">
          <app-project-info-card [project]="activeProject()" />
          <app-version-info-card
            [version]="activeVersionMetadata()"
            (createVersion)="showCreateVersionModal = true"
          />
        </div>

        <!-- Row 2: Tech Stack -->
        <div class="dashboard-card">
          <h2 class="card-title"><i class="fa-solid fa-layer-group"></i> {{ 'dashboard.techStack' | i18n }}</h2>
          @if (activeProject()?.tech_stack) {
            <div class="tech-stack-grid">
              <!-- Infrastructure -->
              <div class="tech-item">
                <div class="tech-icon-wrap">
                  <i class="{{ getTechIcon('infrastructure', activeProject()!.tech_stack?.infrastructure || '') }}"></i>
                </div>
                <div class="tech-label">{{ 'project.infrastructure' | i18n }}</div>
                <div class="tech-value">{{ getTechLabel('infrastructure', activeProject()!.tech_stack?.infrastructure || '') }}</div>
              </div>
              <!-- Backend -->
              <div class="tech-item">
                <div class="tech-icon-wrap">
                  <i class="{{ getTechIcon('backend', activeProject()!.tech_stack?.backend || '') }}"></i>
                </div>
                <div class="tech-label">{{ 'project.backend' | i18n }}</div>
                <div class="tech-value">{{ getTechLabel('backend', activeProject()!.tech_stack?.backend || '') }}</div>
              </div>
              <!-- Frontend -->
              <div class="tech-item">
                <div class="tech-icon-wrap">
                  <i class="{{ getTechIcon('frontend', activeProject()!.tech_stack?.frontend || '') }}"></i>
                </div>
                <div class="tech-label">{{ 'project.frontend' | i18n }}</div>
                <div class="tech-value">{{ getTechLabel('frontend', activeProject()!.tech_stack?.frontend || '') }}</div>
              </div>
              <!-- UI System -->
              <div class="tech-item">
                <div class="tech-icon-wrap">
                  <i class="{{ getTechIcon('ui_framework', activeProject()!.tech_stack?.ui_framework || '') }}"></i>
                </div>
                <div class="tech-label">{{ 'project.uiSystem' | i18n }}</div>
                <div class="tech-value">{{ getTechLabel('ui_framework', activeProject()!.tech_stack?.ui_framework || '') }}</div>
              </div>
              <!-- Domain -->
              <div class="tech-item">
                <div class="tech-icon-wrap">
                  <i class="fa-solid fa-cubes"></i>
                </div>
                <div class="tech-label">{{ 'project.domain' | i18n }}</div>
                <div class="tech-value">{{ activeProject()?.prompt_domain || 'Default' }}</div>
              </div>
            </div>
          } @else {
            <p class="empty-state">{{ 'dashboard.noTechStack' | i18n }}</p>
          }
        </div>

        <!-- Row 3: Artifacts Stats -->
        <app-artifacts-stats-card [data]="artifactStats()" />

        <!-- Row 4: Activity History (full width) -->
        <app-activity-history />
      }

      <!-- Create Version Modal -->
      @if (showCreateVersionModal) {
        <app-version-create-form
          [existingVersionCount]="versions().length"
          (versionCreated)="closeCreateModal()"
          (cancel)="closeCreateModal()"
        />
      }
    </div>
  `,
  styles: [`
    /* Page header docs link */
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

    .docs-link:hover {
      text-decoration: underline;
    }

    .dashboard-container {
      padding: 32px 0;
    }

    .dashboard-header {
      margin-bottom: 32px;
    }

    .dashboard-title {
      font-size: 1.75rem;
      font-weight: 700;
      color: var(--text-primary);
      margin: 0 0 8px 0;
    }

    .dashboard-subtitle {
      font-size: 0.95rem;
      color: var(--text-secondary);
      margin: 0;
    }

    /* Info Cards Row (50/50) */
    .info-cards-row {
      display: flex;
      gap: 16px;
      margin-bottom: 24px;
    }

    /* Init Card */
    .init-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      padding: 48px;
      margin-bottom: 24px;
      text-align: center;
    }

    .init-content {
      max-width: 500px;
      margin: 0 auto;
    }

    .init-title {
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--text-primary);
      margin: 0 0 12px 0;
    }

    .init-desc {
      font-size: 0.95rem;
      color: var(--text-secondary);
      margin: 0 0 32px 0;
    }

    .btn-primary-large {
      width: 100%;
      padding: 12px 24px;
      background: var(--brand-gradient);
      color: white;
      border: none;
      border-radius: 4px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      margin-top: 8px;
    }

    .btn-primary-large:hover:not(:disabled) {
      box-shadow: var(--glow-md);
    }

    .btn-primary-large:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    /* Dashboard Card */
    .dashboard-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      padding: 24px;
      margin-bottom: 24px;
    }

    .card-title {
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 20px 0;
    }

    /* Tech Stack Grid */
    .tech-stack-grid {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 12px;
    }

    .tech-item {
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      padding: 16px 12px;
      text-align: center;
      transition: all 0.2s;
    }

    .tech-item:hover {
      border-color: var(--brand-color);
      box-shadow: 0 0 10px rgba(252, 103, 103, 0.15);
    }

    .tech-icon-wrap {
      font-size: 2rem;
      margin-bottom: 8px;
      color: var(--brand-color);
    }

    .tech-label {
      font-size: 0.7rem;
      font-weight: 600;
      text-transform: uppercase;
      color: var(--text-secondary);
      margin-bottom: 4px;
      letter-spacing: 0.04em;
    }

    .tech-value {
      font-size: 0.85rem;
      font-weight: 500;
      color: var(--text-primary);
    }

    .empty-state {
      text-align: center;
      color: var(--text-tertiary);
      font-size: 0.9rem;
      margin: 24px 0;
    }
  `]
})
export class DashboardComponent implements OnInit {
  private pipelineStore = inject(PipelineStore);
  private api = inject(ApiService);
  private versionService = inject(VersionService);
  private i18n = inject(I18nService);

  private subscriptions = new Subscription();

  readonly docsUrl = `${DOCS_BASE}/dashboard`;

  // Data
  versions = signal<VersionInfo[]>([]);
  activeVersion = signal<string>('');
  activeProject = signal<ProjectInfo | null>(null);
  artifactStats = signal<ArtifactStatsData>({
    pipeline: { brief: 'none', contract: 'none', ir: 'none', code: 'none' },
    briefs: { count: 0, status: '', title: '', word_count: 0, clarification_count: 0, change_count: 0, updated_at: '', types: {} },
    contracts: { count: 0, categories: {}, total_entities: 0, total_commands: 0, total_queries: 0, total_events: 0 },
    ir: { operations: 0, data_flows: 0, effect_flows: 0, boundaries: 0, entities: 0 },
    code: { total_files: 0, total_lines: 0, total_size: 0, file_types: {} },
  });

  // UI
  showCreateVersionModal = false;

  // Pipeline phases
  initPhase() { return this.pipelineStore.getInitPhase(); }
  briefPhase() { return this.pipelineStore.getBriefPhase(); }
  contractPhase() { return this.pipelineStore.getContractPhase(); }
  irPhase() { return this.pipelineStore.getIRPhase(); }
  codePhase() { return this.pipelineStore.getCodePhase(); }
  previewPhase() { return this.pipelineStore.getPreviewPhase(); }
  projectName() { return this.pipelineStore.getProjectName(); }
  overallProgress() { return this.pipelineStore.overallProgress(); }
  workspaceInitialized = this.pipelineStore.workspaceInitializedSignal;

  /** Version metadata cho card — xây từ version service data */
  activeVersionMetadata = computed<VersionMetadata | null>(() => {
    const vname = this.activeVersion();
    const versions = this.versions();
    const v = versions.find(vi => vi.version === vname);
    if (!v) return null;

    return {
      version: v.version,
      status: v.status,
      active: true,
      parent_version: v.parentVersion || null,
      created_at: v.createdAt,
      updated_at: v.lastModified || v.createdAt,
      branch: v.branch,
      pipeline: v.pipeline,
    };
  });

  constructor() {
    this.subscriptions.add(
      this.versionService.versions$.subscribe(v => this.versions.set(v))
    );
    this.subscriptions.add(
      this.versionService.activeVersion$.subscribe(v => this.activeVersion.set(v))
    );

    // Khi active version thay đổi, refresh project + artifact stats
    effect(() => {
      this.activeVersion();
      this.loadActiveProject();
      this.loadArtifactStats();
    });

    // Listen to version-switched event from window
    this.subscriptions.add(
      new Subscription(() => {
        window.removeEventListener('version-switched', this.onVersionSwitched);
      })
    );
    window.addEventListener('version-switched', this.onVersionSwitched);
  }

  /** Reload toàn bộ data khi version được switch */
  private onVersionSwitched = async (event: any) => {
    try {
      this.pipelineStore.loadStatus();
      this.loadActiveProject();
      this.loadArtifactStats();
    } finally {
      this.versionService.stopLoading();
    }
  };

  ngOnInit(): void {
    this.pipelineStore.loadStatus();
    this.versionService.loadVersions();
    this.loadActiveProject();
    this.loadArtifactStats();
  }

  /** Lấy project active từ API */
  loadActiveProject(): void {
    this.api.getActiveProject().then(resp => {
      if (resp.success && resp.data?.project) {
        this.activeProject.set(resp.data.project);
      } else {
        this.activeProject.set(null);
      }
    }).catch(() => {
      this.activeProject.set(null);
    });
  }

  /** Lấy artifact stats từ API */
  loadArtifactStats(): void {
    this.api.getArtifactStats().then(resp => {
      if (resp.success && resp.data) {
        this.artifactStats.set(resp.data);
      }
    }).catch(() => {
      // silent — card sẽ hiện trạng thái mặc định "Chưa xử lý"
    });
  }

  pipelineInitialized(): boolean {
    return this.versions().length > 0;
  }

  switchVersion(version: string): void {
    this.versionService.setActiveVersion(version);
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  closeCreateModal(): void {
    this.showCreateVersionModal = false;
  }

  getPhaseStatusText(status: PhaseStatus): string {
    switch (status) {
      case 'complete': return this.i18n.t('dashboard.complete');
      case 'in_progress': return this.i18n.t('dashboard.inProgress');
      case 'error': return this.i18n.t('dashboard.error');
      default: return this.i18n.t('dashboard.pending');
    }
  }

  /** FontAwesome icon class cho tech stack */
  getTechIcon(category: string, value: string): string {
    const v = (value || '').toLowerCase();
    switch (category) {
      case 'infrastructure':
        if (v.includes('docker')) return 'fa-brands fa-docker';
        if (v.includes('k8s') || v.includes('kubernetes')) return 'fa-solid fa-dharmachakra';
        return 'fa-solid fa-server';
      case 'backend':
        if (v.includes('fastapi') || v.includes('python')) return 'fa-brands fa-python';
        if (v.includes('nestjs') || v.includes('node')) return 'fa-brands fa-node-js';
        if (v.includes('express')) return 'fa-brands fa-node-js';
        return 'fa-solid fa-server';
      case 'frontend':
        if (v.includes('angular')) return 'fa-brands fa-angular';
        if (v.includes('react')) return 'fa-brands fa-react';
        if (v.includes('vue')) return 'fa-brands fa-vuejs';
        return 'fa-solid fa-desktop';
      case 'ui_framework':
        if (v.includes('carbon')) return 'fa-solid fa-palette';
        if (v.includes('tailwind')) return 'fa-brands fa-css3';
        if (v.includes('material')) return 'fa-brands fa-material-ui';
        return 'fa-solid fa-paint-brush';
      default:
        return 'fa-solid fa-cube';
    }
  }

  /** Human-readable label cho tech stack */
  getTechLabel(category: string, value: string): string {
    const v = (value || '').toLowerCase();
    switch (category) {
      case 'infrastructure':
        if (v.includes('docker')) return 'Docker';
        if (v.includes('k8s') || v.includes('kubernetes')) return 'Kubernetes';
        if (v === 'infrastructure') return 'Docker/K8s';
        return value || '—';
      case 'backend':
        if (v.includes('fastapi')) return 'FastAPI';
        if (v.includes('nestjs')) return 'NestJS';
        if (v.includes('express')) return 'Express';
        return value || '—';
      case 'frontend':
        if (v.includes('angular')) return 'Angular';
        if (v.includes('react')) return 'React';
        if (v.includes('vue')) return 'Vue';
        return value || '—';
      case 'ui_framework':
        if (v.includes('carbon')) return 'Carbon';
        if (v.includes('tailwind')) return 'Tailwind';
        if (v.includes('material')) return 'Material';
        return value || '—';
      default:
        return value || '—';
    }
  }
}
