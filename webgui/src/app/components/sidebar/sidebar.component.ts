/**
 * Sidebar Component
 * Hiển thị Projects, Versions
 */

import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router, NavigationEnd } from '@angular/router';
import { Subscription, filter } from 'rxjs';

import { VersionService, VersionInfo } from '../../core/version.service';
import { ApiService, ProjectInfo } from '../../core/api.service';
import { I18nPipe } from '../../core/i18n.pipe';
import { VersionCreateFormComponent } from '../shared/version-create-form/version-create-form';
import { ProjectCreateFormComponent } from '../shared/project-create-form/project-create-form';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink, I18nPipe, VersionCreateFormComponent, ProjectCreateFormComponent],
  template: `
    <aside class="sidebar">
      <!-- Dashboard Link -->
      <a routerLink="/dashboard" class="sidebar-dashboard-link">
        <span class="dashboard-icon">⌂</span>
        <span>{{ 'nav.dashboard' | i18n }}</span>
      </a>
      <hr class="sidebar-divider" />

      <!-- Projects Section -->
      <div class="sidebar-section">
        <div class="sidebar-header">
          <h3>{{ 'nav.projects' | i18n }}</h3>
          <button class="btn-icon" (click)="showCreateProjectModal = true" title="{{ 'nav.createProject' | i18n }}">
            +
          </button>
        </div>

        <div class="project-list">
          @for (project of projects; track project.project_id) {
            <div
              class="project-item"
              [class.active]="project.active"
              (click)="switchProject(project)"
            >
              <div class="project-info">
                <span class="project-name">{{ project.name }}</span>
                @if (project.active) {
                  <span class="project-active-badge">{{ 'nav.active' | i18n }}</span>
                }
              </div>
            </div>
          } @empty {
            <p class="empty-text">{{ 'project.empty' | i18n }}</p>
          }
        </div>
      </div>

      <!-- Versions Section -->
      <div class="sidebar-section">
        <div class="sidebar-header">
          <h3>{{ 'nav.versions' | i18n }}</h3>
          <button class="btn-icon" (click)="showCreateModal = true" title="{{ 'nav.createVersion' | i18n }}">
            +
          </button>
        </div>

        <div class="version-list">
          @for (version of versions; track version.version) {
            <div
              class="version-item"
              [class.selected]="version.version === activeVersion"
              [class.archived]="version.status === 'archived'"
              [class.disabled]="version.status === 'archived'"
              (click)="version.status !== 'archived' && switchVersion(version.version)"
              [title]="version.status === 'archived' ? ('version.archivedTitle' | i18n) : ''"
            >
              <div class="version-info">
                <span class="version-name">{{ version.version }}</span>
                <span class="version-status" [ngClass]="version.status">
                  {{ version.status }}
                </span>
              </div>
            </div>
          } @empty {
            <p class="empty-text">{{ 'version.empty' | i18n }}</p>
          }
        </div>
      </div>

      <!-- Settings Section -->
      <div class="sidebar-section">
        <div class="sidebar-header">
          <h3>{{ 'nav.settings' | i18n }}</h3>
        </div>
        <div class="settings-list">
          <a routerLink="/general-settings" class="settings-item">
            <span class="settings-icon">🛠️</span>
            <span class="settings-name">{{ 'nav.general' | i18n }}</span>
          </a>
          <a routerLink="/llm-config" class="settings-item">
            <span class="settings-icon">⚙️</span>
            <span class="settings-name">{{ 'nav.llmConfig' | i18n }}</span>
          </a>
          <a routerLink="/system-logs" class="settings-item">
            <span class="settings-icon">📋</span>
            <span class="settings-name">{{ 'nav.systemLogs' | i18n }}</span>
          </a>
        </div>
      </div>
    </aside>

    <!-- Create Version Modal -->
    @if (showCreateModal) {
      <app-version-create-form
        [existingVersionCount]="versions.length"
        (versionCreated)="onVersionCreated()"
        (cancel)="showCreateModal = false"
      />
    }

    <!-- Create Project Modal -->
    @if (showCreateProjectModal) {
      <app-project-create-form
        [useModal]="true"
        (projectCreated)="onProjectCreated()"
        (cancel)="showCreateProjectModal = false"
      />
    }
  `,
  styles: [`
    .sidebar {
      width: 320px;
      min-width: 320px;
      background: var(--bg-secondary);
      border-right: 1px solid var(--border-subtle);
      height: 100vh;
      position: fixed;
      top: 0;
      left: 0;
      overflow-y: auto;
      overflow-x: hidden;
      padding: 80px 0 16px 0;
      z-index: 30;
    }

    /* Dashboard link */
    .sidebar-dashboard-link {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 12px 20px;
      margin: 0 12px 8px 12px;
      color: var(--text-secondary);
      text-decoration: none;
      font-size: 0.8125rem;
      font-weight: 500;
      transition: color 0.2s, background 0.2s;
    }

    .sidebar-dashboard-link:hover {
      color: var(--brand-color);
    }

    .sidebar-dashboard-link.router-link-active {
      color: var(--brand-color);
    }

    .dashboard-icon {
      font-size: 1rem;
    }

    /* Divider below dashboard link */
    .sidebar-divider {
      height: 1px;
      margin: 4px 16px 12px 16px;
      border: none;
      background: var(--border-subtle);
    }

    /* Custom scrollbar for sidebar */
    .sidebar::-webkit-scrollbar {
      width: 6px;
    }

    .sidebar::-webkit-scrollbar-track {
      background: transparent;
    }

    .sidebar::-webkit-scrollbar-thumb {
      background: var(--border-subtle);
    }

    .sidebar::-webkit-scrollbar-thumb:hover {
      background: var(--brand-color);
    }

    .sidebar-section {
      margin-bottom: 32px;
      padding: 0 16px;
    }

    /* Project List */
    .project-list {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .project-item {
      display: flex;
      align-items: center;
      padding: 10px 12px;
      border-left: 3px solid transparent;
      cursor: pointer;
      transition: all 0.2s;
    }

    .project-item:hover {
      background: var(--bg-card);
    }

    .project-item.active {
      border-left-color: var(--accent-success);
      background: rgba(63, 185, 80, 0.08);
    }

    .project-info {
      display: flex;
      align-items: center;
      gap: 8px;
      flex: 1;
      min-width: 0;
    }

    .project-name {
      font-weight: 500;
      color: var(--text-primary);
      font-size: 0.9rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .project-active-badge {
      font-size: 0.6rem;
      padding: 1px 5px;
      background: rgba(63, 185, 80, 0.2);
      color: var(--accent-success);
      border-radius: 2px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      flex-shrink: 0;
    }

    .empty-text {
      color: var(--text-tertiary);
      font-size: 0.8rem;
      text-align: center;
      padding: 12px 0;
      margin: 0;
    }

    .error-text {
      color: var(--accent-error);
      font-size: 0.85rem;
      margin-top: 8px;
    }

    .sidebar-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }

    .sidebar-header h3 {
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin: 0;
    }

    .btn-icon {
      width: 24px;
      height: 24px;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      color: var(--text-secondary);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.25rem;
      font-weight: 300;
      transition: all 0.2s;
      line-height: 1;
    }

    .btn-icon:hover {
      border-color: var(--brand-color);
      color: var(--brand-color);
      box-shadow: var(--glow-sm);
    }

    .version-list {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .version-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 12px;
      border-left: 3px solid transparent;
      cursor: pointer;
      transition: all 0.2s;
    }

    .version-item:hover:not(.disabled) {
      background: var(--bg-card);
    }

    .version-item.selected {
      border-left-color: var(--brand-color);
      background: rgba(252, 103, 103, 0.1);
    }

    .version-item.archived {
      opacity: 0.4;
    }

    .version-item.disabled {
      cursor: not-allowed;
      pointer-events: all;
    }

    .version-item.disabled:hover {
      background: transparent;
    }

    .version-info {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .version-name {
      font-weight: 500;
      color: var(--text-primary);
      font-size: 0.9rem;
    }

    .version-status {
      font-size: 0.65rem;
      padding: 2px 6px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }

    .version-status.inbuild {
      background: rgba(63, 185, 80, 0.2);
      color: var(--accent-success);
    }

    .version-status.draft {
      background: rgba(210, 153, 34, 0.2);
      color: var(--accent-warning);
    }

    .version-status.archived {
      background: rgba(139, 148, 158, 0.2);
      color: var(--text-tertiary);
    }

    /* Modal */
    .modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.7);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 100;
      padding: 20px;
    }

    .modal {
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      width: 100%;
      max-width: 400px;
      box-shadow: var(--glow-md);
    }

    .modal-wide {
      max-width: 480px;
    }

    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 20px;
      border-bottom: 1px solid var(--border-subtle);
    }

    .modal-header h3 {
      margin: 0;
      font-size: 1.1rem;
    }

    .btn-close {
      background: none;
      border: none;
      color: var(--text-secondary);
      font-size: 1.5rem;
      cursor: pointer;
      padding: 0;
      line-height: 1;
    }

    .btn-close:hover {
      color: var(--text-primary);
    }

    .modal-body {
      padding: 20px;
    }

    .warning-banner {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      padding: 12px 14px;
      margin-bottom: 16px;
      background: rgba(210, 153, 34, 0.1);
      border: 1px solid rgba(210, 153, 34, 0.3);
      border-radius: 6px;
      font-size: 0.8rem;
      color: var(--accent-warning);
      line-height: 1.4;
    }

    .warning-icon {
      font-size: 1.1rem;
      flex-shrink: 0;
    }

    .form-group {
      margin-bottom: 16px;
    }

    .form-group label {
      display: block;
      margin-bottom: 6px;
      font-size: 0.85rem;
      color: var(--text-secondary);
    }

    .form-group .input {
      width: 100%;
      padding: 10px 12px;
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      color: var(--text-primary);
      font-size: 0.9rem;
    }

    .form-group .input:focus {
      outline: none;
      border-color: var(--brand-color);
      box-shadow: var(--glow-sm);
    }

    .modal-footer {
      display: flex;
      justify-content: flex-end;
      gap: 12px;
      padding: 16px 20px;
      border-top: 1px solid var(--border-subtle);
    }

    .btn {
      padding: 8px 16px;
      font-size: 0.9rem;
      font-weight: 500;
      border: none;
      cursor: pointer;
      transition: all 0.2s;
    }

    .btn-secondary {
      background: var(--bg-card);
      color: var(--text-secondary);
      border: 1px solid var(--border-subtle);
    }

    .btn-secondary:hover {
      background: var(--border-subtle);
    }

    .btn-primary {
      background: var(--brand-gradient);
      color: white;
    }

    .btn-primary:hover:not(:disabled) {
      box-shadow: var(--glow-md);
    }

    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    /* Modal select styling */
    .modal select.input {
      appearance: none;
      cursor: pointer;
    }

    .modal select.input option {
      background: var(--bg-secondary);
      color: var(--text-primary);
    }

    /* Settings */
    .settings-list {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .settings-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 12px;
      cursor: pointer;
      transition: all 0.2s;
      border: 1px solid transparent;
      text-decoration: none;
      color: inherit;
    }

    .settings-item:hover {
      background: var(--bg-card);
      border-color: var(--border-subtle);
    }

    .settings-icon {
      font-size: 0.9rem;
    }

    .settings-name {
      font-size: 0.85rem;
      font-weight: 500;
    }
  `]
})
export class SidebarComponent implements OnInit, OnDestroy {
  versions: VersionInfo[] = [];
  activeVersion: string = '';
  activeVersionInfo?: VersionInfo;
  showCreateModal = false;
  newVersionName = '';
  // Projects
  projects: ProjectInfo[] = [];
  showCreateProjectModal = false;

  private routerSub?: Subscription;

  constructor(
    private versionService: VersionService,
    private router: Router,
    private api: ApiService,
  ) {}

  ngOnInit(): void {
    // Subscribe to versions changes
    this.versionService.versions$.subscribe(versions => {
      this.versions = versions;
    });

    // Subscribe to active version changes
    this.versionService.activeVersion$.subscribe(version => {
      this.activeVersion = version;
      this.activeVersionInfo = this.versionService.getVersion(version);
    });

    // Load projects from backend
    this.loadProjects();

    // Subscribe to navigation events to refresh sidebar state
    this.routerSub = this.router.events.pipe(filter(event => event instanceof NavigationEnd)).subscribe(() => {
      // navigation event — nothing extra needed
    });
  }

  ngOnDestroy(): void {
    this.routerSub?.unsubscribe();
  }

  // ====================================================================
  // Project methods
  // ====================================================================

  async loadProjects(): Promise<void> {
    try {
      const result = await this.api.listProjects();
      if (result.success && result.data) {
        this.projects = result.data.projects || [];
      }
    } catch (e) {
      console.warn('Failed to load projects:', e);
    }
  }

  async switchProject(project: ProjectInfo): Promise<void> {
    if (project.active) return;
    try {
      const result = await this.api.activateProject(project.project_id);
      if (result.success) {
        // Update local state — không reload page (giữ nguyên thứ tự danh sách)
        await this.loadProjects();
        this.versionService.loadVersions();
        // Notify other components to refresh
        window.dispatchEvent(new CustomEvent('project-switched'));
      }
    } catch (e) {
      console.error('Failed to switch project:', e);
    }
  }

  // ====================================================================
  // Existing methods
  // ====================================================================

  async switchVersion(version: string): Promise<void> {
    await this.versionService.setActiveVersion(version);
    this.activeVersionInfo = this.versionService.getVersion(version);
  }

  onVersionCreated(): void {
    this.showCreateModal = false;
  }

  onProjectCreated(): void {
    this.showCreateProjectModal = false;
    window.location.reload();
  }
}