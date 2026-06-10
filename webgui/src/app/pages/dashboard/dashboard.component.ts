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
import { RouterLink } from '@angular/router';
import { Subscription } from 'rxjs';

import { I18nPipe } from '../../core/i18n.pipe';
import { I18nService } from '../../core/i18n.service';
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
    CommonModule, FormsModule, RouterLink, I18nPipe,
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
        <h1 class="dashboard-title">{{ 'dashboard.title' | i18n }}</h1>
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

        <!-- Row 2: Pipeline Progress -->
        <div class="dashboard-card">
          <h2 class="card-title">{{ 'dashboard.pipelineProgress' | i18n }}</h2>

          <div class="progress-section">
            <div class="progress-header">
              <span class="progress-label">{{ 'dashboard.totalProgress' | i18n }}</span>
              <span class="progress-value">{{ overallProgress() }}%</span>
            </div>
            <div class="progress-track">
              <div class="progress-fill" [style.width.%]="overallProgress()"></div>
            </div>
          </div>

          <div class="phase-grid">
            <a class="phase-item" routerLink="/dashboard">
              <div class="phase-icon" [ngClass]="'phase-' + initPhase().status">
                @if (initPhase().status === 'complete') { ✓ }
                @else if (initPhase().status === 'in_progress') { ◎ }
                @else { 1 }
              </div>
              <p class="phase-name">{{ 'dashboard.phaseInit' | i18n }}</p>
              <p class="phase-status">{{ getPhaseStatusText(initPhase().status) }}</p>
            </a>
            <a class="phase-item" routerLink="/brief-editor">
              <div class="phase-icon" [ngClass]="'phase-' + briefPhase().status">
                @if (briefPhase().status === 'complete') { ✓ }
                @else if (briefPhase().status === 'in_progress') { ◎ }
                @else { 2 }
              </div>
              <p class="phase-name">{{ 'dashboard.phaseBrief' | i18n }}</p>
              <p class="phase-status">{{ getPhaseStatusText(briefPhase().status) }}</p>
            </a>
            <a class="phase-item" routerLink="/contract-viewer">
              <div class="phase-icon" [ngClass]="'phase-' + contractPhase().status">
                @if (contractPhase().status === 'complete') { ✓ }
                @else if (contractPhase().status === 'in_progress') { ◎ }
                @else { 3 }
              </div>
              <p class="phase-name">{{ 'dashboard.phaseContract' | i18n }}</p>
              <p class="phase-status">{{ getPhaseStatusText(contractPhase().status) }}</p>
            </a>
            <a class="phase-item" routerLink="/ir-explorer">
              <div class="phase-icon" [ngClass]="'phase-' + irPhase().status">
                @if (irPhase().status === 'complete') { ✓ }
                @else if (irPhase().status === 'in_progress') { ◎ }
                @else { 4 }
              </div>
              <p class="phase-name">{{ 'dashboard.phaseIR' | i18n }}</p>
              <p class="phase-status">{{ getPhaseStatusText(irPhase().status) }}</p>
            </a>
            <a class="phase-item" routerLink="/code-generator">
              <div class="phase-icon" [ngClass]="'phase-' + codePhase().status">
                @if (codePhase().status === 'complete') { ✓ }
                @else if (codePhase().status === 'in_progress') { ◎ }
                @else { 5 }
              </div>
              <p class="phase-name">{{ 'dashboard.phaseCode' | i18n }}</p>
              <p class="phase-status">{{ getPhaseStatusText(codePhase().status) }}</p>
            </a>
            <a class="phase-item" routerLink="/preview">
              <div class="phase-icon" [ngClass]="'phase-' + previewPhase().status">
                @if (previewPhase().status === 'complete') { ✓ }
                @else if (previewPhase().status === 'in_progress') { ◎ }
                @else { 6 }
              </div>
              <p class="phase-name">{{ 'dashboard.phasePreview' | i18n }}</p>
              <p class="phase-status">{{ getPhaseStatusText(previewPhase().status) }}</p>
            </a>
          </div>
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
    .dashboard-container {
      padding: 32px 32px 32px 0;
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

    /* Progress Section */
    .progress-section {
      margin-bottom: 28px;
    }

    .progress-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }

    .progress-label {
      font-size: 0.9rem;
      color: var(--text-secondary);
    }

    .progress-value {
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--brand-color);
    }

    .progress-track {
      height: 8px;
      background: var(--bg-secondary);
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      background: var(--brand-gradient);
      transition: width 0.5s ease;
    }

    /* Phase Grid */
    .phase-grid {
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 16px;
    }

    .phase-item {
      text-align: center;
      text-decoration: none;
      color: inherit;
      cursor: pointer;
      transition: opacity 0.2s;
    }

    .phase-item:hover {
      opacity: 0.8;
    }

    .phase-icon {
      width: 56px;
      height: 56px;
      margin: 0 auto 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 2px solid var(--border-subtle);
      font-size: 1.4rem;
      transition: all 0.2s;
    }

    .phase-item .phase-icon.phase-complete {
      border-color: var(--accent-success);
      color: var(--accent-success);
      background: rgba(63, 185, 80, 0.1);
    }

    .phase-item .phase-icon.phase-in_progress {
      border-color: var(--brand-color);
      color: var(--brand-color);
      background: rgba(252, 103, 103, 0.1);
      box-shadow: 0 0 15px rgba(252, 103, 103, 0.3);
    }

    .phase-item .phase-icon.phase-pending {
      border-color: var(--border-subtle);
      color: var(--text-tertiary);
    }

    .phase-item .phase-icon.phase-error {
      border-color: var(--accent-error);
      color: var(--accent-error);
      background: rgba(248, 81, 73, 0.1);
    }

    .phase-name {
      font-size: 0.85rem;
      font-weight: 500;
      color: var(--text-primary);
      margin: 0 0 4px 0;
    }

    .phase-status {
      font-size: 0.75rem;
      color: var(--text-secondary);
      margin: 0;
    }
  `]
})
export class DashboardComponent implements OnInit {
  private pipelineStore = inject(PipelineStore);
  private api = inject(ApiService);
  private versionService = inject(VersionService);
  private i18n = inject(I18nService);

  private subscriptions = new Subscription();

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
  }

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
}
