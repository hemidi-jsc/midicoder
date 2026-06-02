/**
 * Sidebar Component
 * Hiển thị Projects, Versions, Pipeline progress
 */

import { Component, OnInit, OnDestroy, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router, NavigationEnd } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { DOCUMENT } from '@angular/common';
import { Subscription, filter } from 'rxjs';

import { VersionService, VersionInfo } from '../../core/version.service';
import { ApiService, ProjectInfo } from '../../core/api.service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  template: `
    <aside class="sidebar">
      <!-- Projects Section -->
      <div class="sidebar-section">
        <div class="sidebar-header">
          <h3>Projects</h3>
          <button class="btn-icon" (click)="showCreateProjectModal = true" title="Create new project">
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
                  <span class="project-active-badge">ACTIVE</span>
                }
              </div>
            </div>
          } @empty {
            <p class="empty-text">Chưa có project nào</p>
          }
        </div>
      </div>

      <!-- Versions Section -->
      <div class="sidebar-section">
        <div class="sidebar-header">
          <h3>Versions</h3>
          <button class="btn-icon" (click)="showCreateModal = true" title="Create new version">
            +
          </button>
        </div>

        <div class="version-list">
          @for (version of versions; track version.version) {
            <div
              class="version-item"
              [class.active]="version.version === activeVersion"
              [class.archived]="version.status === 'archived'"
              (click)="switchVersion(version.version)"
            >
              <div class="version-info">
                <span class="version-name">{{ version.version }}</span>
                <span class="version-status" [ngClass]="version.status">
                  {{ version.status }}
                </span>
              </div>
              @if (version.version === activeVersion) {
                <span class="version-active-indicator">✓</span>
              }
            </div>
          } @empty {
            <p class="empty-text">Chưa có phiên bản nào</p>
          }
        </div>
      </div>

      <!-- Pipeline Progress Section -->
      <div class="sidebar-section">
        <div class="sidebar-header">
          <h3>Pipeline</h3>
        </div>

        <div class="pipeline-progress">
          @if (activeVersionInfo) {
            <div 
              class="pipeline-phase" 
              [class.complete]="activeVersionInfo.progress.init === 'complete'"
              [class.in-progress]="activeVersionInfo.progress.init === 'in_progress'"
              [class.current]="currentPhase === 'init'"
              [class.error]="activeVersionInfo.progress.init === 'error'"
              routerLink="/dashboard"
            >
              <span class="phase-icon">
                @if (activeVersionInfo.progress.init === 'complete') { ✓ }
                @else if (activeVersionInfo.progress.init === 'in_progress') { ◎ }
                @else { ○ }
              </span>
              <span class="phase-name">Init</span>
            </div>

            <div 
              class="pipeline-phase" 
              [class.complete]="activeVersionInfo.progress.brief === 'complete'"
              [class.in-progress]="activeVersionInfo.progress.brief === 'in_progress'"
              [class.current]="currentPhase === 'brief'"
              [class.error]="activeVersionInfo.progress.brief === 'error'"
              routerLink="/brief-editor"
            >
              <span class="phase-icon">
                @if (activeVersionInfo.progress.brief === 'complete') { ✓ }
                @else if (activeVersionInfo.progress.brief === 'in_progress') { ◎ }
                @else { ○ }
              </span>
              <span class="phase-name">Brief</span>
            </div>

            <div 
              class="pipeline-phase" 
              [class.complete]="activeVersionInfo.progress.contract === 'complete'"
              [class.in-progress]="activeVersionInfo.progress.contract === 'in_progress'"
              [class.current]="currentPhase === 'contract'"
              [class.error]="activeVersionInfo.progress.contract === 'error'"
              routerLink="/contract-viewer"
            >
              <span class="phase-icon">
                @if (activeVersionInfo.progress.contract === 'complete') { ✓ }
                @else if (activeVersionInfo.progress.contract === 'in_progress') { ◎ }
                @else { ○ }
              </span>
              <span class="phase-name">Contract</span>
            </div>

            <div 
              class="pipeline-phase" 
              [class.complete]="activeVersionInfo.progress.ir === 'complete'"
              [class.in-progress]="activeVersionInfo.progress.ir === 'in_progress'"
              [class.current]="currentPhase === 'ir'"
              [class.error]="activeVersionInfo.progress.ir === 'error'"
              routerLink="/ir-explorer"
            >
              <span class="phase-icon">
                @if (activeVersionInfo.progress.ir === 'complete') { ✓ }
                @else if (activeVersionInfo.progress.ir === 'in_progress') { ◎ }
                @else { ○ }
              </span>
              <span class="phase-name">IR</span>
            </div>

            <div 
              class="pipeline-phase" 
              [class.complete]="activeVersionInfo.progress.code === 'complete'"
              [class.in-progress]="activeVersionInfo.progress.code === 'in_progress'"
              [class.current]="currentPhase === 'code'"
              [class.error]="activeVersionInfo.progress.code === 'error'"
              routerLink="/code-generator"
            >
              <span class="phase-icon">
                @if (activeVersionInfo.progress.code === 'complete') { ✓ }
                @else if (activeVersionInfo.progress.code === 'in_progress') { ◎ }
                @else { ○ }
              </span>
              <span class="phase-name">Code</span>
            </div>

            <div 
              class="pipeline-phase" 
              [class.complete]="activeVersionInfo.progress.preview === 'complete'"
              [class.in-progress]="activeVersionInfo.progress.preview === 'in_progress'"
              [class.current]="currentPhase === 'preview'"
              [class.error]="activeVersionInfo.progress.preview === 'error'"
              routerLink="/preview"
            >
              <span class="phase-icon">
                @if (activeVersionInfo.progress.preview === 'complete') { ✓ }
                @else if (activeVersionInfo.progress.preview === 'in_progress') { ◎ }
                @else { ○ }
              </span>
              <span class="phase-name">Preview</span>
            </div>
          }
        </div>

        <!-- Progress Bar -->
        @if (activeVersionInfo) {
          <div class="progress-section">
            <div class="progress-labels">
              <span>Progress</span>
              <span>{{ overallProgress }}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" [style.width.%]="overallProgress"></div>
            </div>
          </div>
        }
      </div>

      <!-- Settings Section -->
      <div class="sidebar-section">
        <div class="sidebar-header">
          <h3>Settings</h3>
        </div>
        <div class="settings-list">
          <a routerLink="/llm-config" class="settings-item">
            <span class="settings-icon">⚙️</span>
            <span class="settings-name">LLM Config</span>
          </a>
        </div>
      </div>
    </aside>

    <!-- Create Version Modal -->
    @if (showCreateModal) {
      <div class="modal-overlay" (click)="showCreateModal = false">
        <div class="modal" (click)="$event.stopPropagation()">
          <div class="modal-header">
            <h3>Create New Version</h3>
            <button class="btn-close" (click)="showCreateModal = false">×</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label for="versionName">Version Name</label>
              <input
                id="versionName"
                type="text"
                [(ngModel)]="newVersionName"
                placeholder="v1.0.2"
                class="input"
              >
            </div>
            <div class="form-group">
              <label for="fromVersion">Base Version (Optional)</label>
              <select id="fromVersion" [(ngModel)]="fromVersion" class="input">
                <option value="">Create from scratch</option>
                @for (v of versions; track v.version) {
                  <option [value]="v.version">{{ v.version }}</option>
                }
              </select>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" (click)="showCreateModal = false">Cancel</button>
            <button class="btn btn-primary" (click)="createVersion()" [disabled]="!newVersionName">Create</button>
          </div>
        </div>
      </div>
    }

    <!-- Create Project Modal -->
    @if (showCreateProjectModal) {
      <div class="modal-overlay" (click)="showCreateProjectModal = false">
        <div class="modal" (click)="$event.stopPropagation()">
          <div class="modal-header">
            <h3>Tạo Project Mới</h3>
            <button class="btn-close" (click)="showCreateProjectModal = false">×</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label for="projectName">Tên Project *</label>
              <input id="projectName" type="text" [(ngModel)]="newProjectName" placeholder="my-app" class="input">
            </div>
            <div class="form-group">
              <label for="projectPath">Working Directory *</label>
              <input id="projectPath" type="text" [(ngModel)]="newProjectPath" placeholder="D:\projects\my-app" class="input">
            </div>
            <div class="form-group">
              <label for="projectStack">Tech Stack (optional)</label>
              <input id="projectStack" type="text" [(ngModel)]="newProjectStack" placeholder="fastapi,angular" class="input">
            </div>
            @if (createProjectError) {
              <p class="error-text">{{ createProjectError }}</p>
            }
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" (click)="closeProjectModal()">Hủy</button>
            <button class="btn btn-primary" (click)="createProject()" [disabled]="!newProjectName || !newProjectPath || isCreatingProject">
              {{ isCreatingProject ? 'Đang tạo...' : 'Tạo' }}
            </button>
          </div>
        </div>
      </div>
    }
  `,
  styles: [`
    .sidebar {
      width: 320px;
      min-width: 320px;
      background: var(--bg-secondary);
      border-right: 1px solid var(--border-subtle);
      height: calc(100vh - 65px);
      position: fixed;
      top: 65px;
      left: 0;
      overflow-y: auto;
      overflow-x: hidden;
      padding: 16px 0;
      z-index: 30;
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

    .version-item:hover {
      background: var(--bg-card);
    }

    .version-item.active {
      border-left-color: var(--brand-color);
      background: rgba(252, 103, 103, 0.1);
    }

    .version-item.archived {
      opacity: 0.6;
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

    .version-status.active {
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

    .version-active-indicator {
      color: var(--brand-color);
      font-weight: bold;
    }

    /* Pipeline Progress */
    .pipeline-progress {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .pipeline-phase {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 12px;
      cursor: pointer;
      transition: all 0.2s;
      border: 1px solid transparent;
    }

    .pipeline-phase:hover {
      background: var(--bg-card);
      border-color: var(--border-subtle);
    }

    .pipeline-phase.complete {
      color: var(--accent-success);
    }

    .pipeline-phase.in-progress {
      color: var(--brand-color);
    }

    .pipeline-phase.current {
      background: rgba(252, 103, 103, 0.1);
      border-color: var(--border-hover);
      box-shadow: var(--glow-sm);
    }

    .pipeline-phase.error {
      color: var(--accent-error);
    }

    .phase-icon {
      font-size: 0.9rem;
    }

    .phase-name {
      font-size: 0.85rem;
      font-weight: 500;
    }

    /* Progress Section */
    .progress-section {
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid var(--border-subtle);
    }

    .progress-labels {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      font-size: 0.8rem;
      color: var(--text-secondary);
    }

    .progress-bar {
      height: 6px;
      background: var(--bg-card);
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      background: var(--brand-gradient);
      transition: width 0.5s ease;
      box-shadow: var(--glow-sm);
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
  fromVersion = '';
  currentPhase: 'init' | 'brief' | 'contract' | 'ir' | 'code' | 'preview' = 'init';

  // Projects
  projects: ProjectInfo[] = [];
  showCreateProjectModal = false;
  newProjectName = '';
  newProjectPath = '';
  newProjectStack = '';
  isCreatingProject = false;
  createProjectError = '';

  private routerSub?: Subscription;

  constructor(
    private versionService: VersionService,
    private router: Router,
    private api: ApiService,
    @Inject(DOCUMENT) private document: Document,
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

    // Determine current phase based on URL
    this.updateCurrentPhase();

    // Subscribe to navigation events
    this.routerSub = this.router.events.pipe(filter(event => event instanceof NavigationEnd)).subscribe(() => {
      this.updateCurrentPhase();
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
        await this.loadProjects();
        // Reload page to pick up new project context
        window.location.reload();
      }
    } catch (e) {
      console.error('Failed to switch project:', e);
    }
  }

  async createProject(): Promise<void> {
    if (!this.newProjectName.trim() || !this.newProjectPath.trim()) return;

    this.isCreatingProject = true;
    this.createProjectError = '';

    try {
      const result = await this.api.createProject({
        name: this.newProjectName.trim(),
        path: this.newProjectPath.trim(),
        stack: this.newProjectStack.trim() || undefined,
      });

      if (result.success) {
        this.closeProjectModal();
        await this.loadProjects();
        window.location.reload();
      } else {
        this.createProjectError = result.message || 'Tạo project thất bại';
      }
    } catch (e: any) {
      this.createProjectError = e.message || 'Lỗi kết nối đến server';
    } finally {
      this.isCreatingProject = false;
    }
  }

  closeProjectModal(): void {
    this.showCreateProjectModal = false;
    this.newProjectName = '';
    this.newProjectPath = '';
    this.newProjectStack = '';
    this.createProjectError = '';
  }

  // ====================================================================
  // Existing methods
  // ====================================================================

  private updateCurrentPhase(): void {
    const url = this.router.url;
    if (url.includes('brief')) this.currentPhase = 'brief';
    else if (url.includes('contract')) this.currentPhase = 'contract';
    else if (url.includes('ir')) this.currentPhase = 'ir';
    else if (url.includes('code')) this.currentPhase = 'code';
    else if (url.includes('preview')) this.currentPhase = 'preview';
    else if (url.includes('feedback')) this.currentPhase = 'preview';
    else this.currentPhase = 'init';
  }

  get overallProgress(): number {
    if (!this.activeVersionInfo) return 0;
    return this.versionService.calculateProgress(this.activeVersionInfo);
  }

  switchVersion(version: string): void {
    this.versionService.setActiveVersion(version);
    this.activeVersionInfo = this.versionService.getVersion(version);
  }

  async createVersion(): Promise<void> {
    if (!this.newVersionName) return;

    await this.versionService.createVersion({
      name: this.newVersionName,
      fromVersion: this.fromVersion || undefined,
    });

    this.showCreateModal = false;
    this.newVersionName = '';
    this.fromVersion = '';
  }
}