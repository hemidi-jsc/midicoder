import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, Router, NavigationEnd, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Subscription, filter } from 'rxjs';

import { APP_VERSION, DOCS_BASE } from './core/app.constants';
import { I18nPipe } from './core/i18n.pipe';
import { AuthService } from './core/auth.service';
import { ScreenCheckService } from './core/screen-check.service';
import { UpdateService } from './core/update.service';
import { PipelineStore, PhaseStatus } from './core/pipeline.store';
import { VersionService } from './core/version.service';
import { SidebarComponent } from './components/sidebar/sidebar.component';
import type { UpdateStatus } from './core/api.types';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, FormsModule, RouterLink, SidebarComponent, I18nPipe],
  template: `
    <div class="min-h-screen bg-bg-primary text-text-primary">
      <!-- Screen Warning Overlay -->
      @if (!screenSupported) {
        <div class="fixed inset-0 z-50 bg-bg-primary bg-opacity-95 flex items-center justify-center">
          <div class="card max-w-md text-center">
            <h2 class="text-xl font-bold text-accent-warning mb-4">
              <i class="fa-solid fa-triangle-exclamation"></i> {{ 'screen.title' | i18n }}
            </h2>
            <p class="text-text-secondary mb-4">
              {{ screenWarningMessage }}
            </p>
            <p class="text-text-tertiary text-sm">
              {{ 'screen.description' | i18n }}
            </p>
          </div>
        </div>
      }

      <!-- Header - chỉ hiển thị khi đã đăng nhập và không ở trang login -->
      @if (isAuthenticated && !isLoginPage) {
        <header class="fixed top-0 left-0 w-full bg-bg-secondary border-b border-border-primary z-50">
          <!-- Row 1: Logo left | Pipeline center | User right -->
          <div class="header-row">
            <!-- Cột 1: Logo + Version Badge + Links -->
            <div class="header-left">
              <img src="logo.png" alt="Midicoder" class="logo-header">
              <a
                href="https://github.com/hemidi-jsc/midicoder/releases"
                target="_blank"
                rel="noopener noreferrer"
                class="app-version-badge"
                title="{{ 'header.viewRelease' | i18n }}"
              >
                v{{ appVersion }}
              </a>
              <div class="header-links">
                <a
                  [attr.href]="docsChangelogUrl"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="header-link"
                  title="{{ 'update.changelog' | i18n }}"
                >
                  {{ 'update.changelog' | i18n }}
                </a>
                <span class="header-separator">·</span>
                <a
                  [attr.href]="docsGettingStartedUrl"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="header-link"
                  title="{{ 'header.documentation' | i18n }}"
                >
                  {{ 'header.documentation' | i18n }}
                </a>
              </div>
            </div>

            <!-- Cột 2: Gaming Pipeline Progress Bar (giữa) -->
            @if (pipelineInitialized()) {
              <div class="header-center">
                <div class="pipeline-wrapper">
                  <!-- Version label — left of pipeline -->
                  <span class="pipeline-version-badge">
                    {{ 'header.versionLabel' | i18n }} <strong>{{ activeVersion() }}</strong>
                  </span>

                  <nav class="pipeline-nav">
                    <!-- Track runs behind all steps -->
                    <div class="pipeline-track">
                      <div class="pipeline-fill" [style.width.%]="overallProgress()"></div>
                    </div>

                    <!-- Steps row — each step = icon + label -->
                    <div class="pipeline-steps">
                    @for (step of pipelineSteps(); track step.key) {
                      <a
                        class="pipeline-step"
                        [routerLink]="step.route"
                        [ngClass]="'step-' + step.state().status"
                      >
                        <div class="step-circle">
                          @if (step.state().status === 'complete') {
                            <span class="step-check">✓</span>
                          } @else if (step.state().status === 'in_progress') {
                            <span class="step-spinner">◌</span>
                          } @else {
                            <span class="step-number">{{ step.number }}</span>
                          }
                        </div>
                        <span class="step-label">{{ step.labelKey | i18n }}</span>
                      </a>
                    }
                  </div>
                </nav>
              </div>
            </div>
            }

            <!-- Cột 3: User Info + Logout -->
            <div class="header-right">
              <span class="user-email">{{ currentUser?.email }}</span>
              <button (click)="handleLogout()" class="logout-btn">
                {{ 'auth.logout' | i18n }}
              </button>
            </div>
          </div>
        </header>

        <!-- Update Banner — hiện khi có phiên bản mới -->
        @if (updateStatus && updateStatus.has_update && !isUpgrading) {
          <div class="update-banner" style="position:fixed;top:95px;left:0;right:0;z-index:40;background:linear-gradient(90deg,var(--brand-color),#ff4da6);color:#fff;display:flex;align-items:center;justify-content:center;padding:10px 48px;gap:16px;box-shadow:0 2px 12px rgba(233,0,137,0.25);">
            <span style="font-size:0.9rem;font-weight:500;"><i class="fa-solid fa-party-horn"></i> {{ 'update.banner' | i18n }} <strong>v{{ updateStatus.latest_version }}</strong> {{ 'update.currentVersion' | i18n:{current: updateStatus.current_version} }}</span>
            <a [attr.href]="updateStatus.download_url" target="_blank" rel="noopener noreferrer" style="color:#fff;text-decoration:underline;cursor:pointer;font-size:0.85rem;margin-left:4px;">{{ 'update.changelog' | i18n }}</a>
            <button (click)="handleUpgrade()" style="background:rgba(255,255,255,0.25);border:1px solid rgba(255,255,255,0.6);color:#fff;padding:5px 16px;border-radius:4px;cursor:pointer;font-size:0.85rem;font-weight:600;transition:background 0.2s;" title="{{ 'update.upgradeTitle' | i18n }}">
              ⬆ {{ 'update.upgrade' | i18n }}
            </button>
          </div>
        }

        <!-- Upgrading Overlay — hiện khi đang restart -->
        @if (isUpgrading) {
          <div style="position:fixed;inset:0;z-index:60;background:rgba(15,15,23,0.9);display:flex;align-items:center;justify-content:center;flex-direction:column;gap:16px;">
            <div style="font-size:2rem;animation:spin 1s linear infinite;"><i class="fa-solid fa-spinner"></i></div>
            <p style="color:var(--text-primary);font-size:1.1rem;font-weight:500;">{{ 'update.upgrading' | i18n }}</p>
          </div>
        }

        <!-- Sidebar -->
        <app-sidebar *ngIf="isAuthenticated && !isLoginPage"></app-sidebar>
      }

      <!-- Main Content -->
      @if (isAuthenticated && !isLoginPage) {
        <main class="main-content">
          <!-- Version switching loading overlay -->
          @if (isSwitchingVersion) {
            <div class="version-switch-overlay">
              <div class="version-switch-spinner">
                <i class="fa-solid fa-spinner"></i>
                <span>{{ 'common.loading' | i18n }}</span>
              </div>
            </div>
          }
          <router-outlet />
        </main>
      } @else {
        <router-outlet />
      }
    </div>
  `,
  styles: [`
    header {
      padding: 0 24px 0 344px;
    }

    .header-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 80px;
    }

    /* ===== Column 1: Left ===== */
    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-shrink: 0;
    }

    .logo-header {
      height: 28px;
      width: auto;
    }

    .app-version-badge {
      display: inline-flex;
      align-items: center;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      color: var(--text-secondary);
      padding: 3px 10px;
      font-size: 0.75rem;
      font-weight: 600;
      font-family: monospace;
      letter-spacing: 0.02em;
      text-decoration: none;
      transition: all 0.2s;
      cursor: pointer;
    }

    .app-version-badge:hover {
      border-color: var(--brand-color);
      color: var(--brand-color);
      box-shadow: var(--glow-sm);
    }

    .header-links {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .header-link {
      color: var(--text-tertiary);
      font-size: 0.8rem;
      text-decoration: none;
      transition: color 0.2s;
      white-space: nowrap;
    }

    .header-link:hover {
      color: var(--brand-color);
    }

    .header-separator {
      color: var(--text-tertiary);
      font-size: 0.75rem;
      user-select: none;
    }

    /* ===== Column 2: Gaming Pipeline ===== */
    .header-center {
      flex: 1;
      display: flex;
      align-items: flex-start;
      justify-content: center;
      padding: 0 20px;
      min-width: 0;
    }

    /* Wrapper holds version label + pipeline nav */
    .pipeline-wrapper {
      display: flex;
      align-items: center;
      gap: 16px;
      width: 100%;
      max-width: 720px;
    }

    /* Version label — plain text, vertically centered */
    .pipeline-version-badge {
      flex-shrink: 0;
      font-size: 13px;
      font-weight: 700;
      color: rgba(255, 255, 255, 0.55);
      white-space: nowrap;
      letter-spacing: 0.02em;
    }

    .pipeline-version-badge strong {
      color: rgba(255, 255, 255, 0.9);
    }

    .pipeline-nav {
      flex: 1;
      position: relative;
      padding-top: 0;
      min-width: 0;
    }

    /* Track — behind everything, centered on the 32px circles */
    .pipeline-track {
      position: absolute;
      top: 16px;
      transform: translateY(-50%);
      left: 16px;
      right: 16px;
      height: 3px;
      background: rgba(255,255,255,0.08);
      border-radius: 2px;
      overflow: hidden;
      z-index: 0;
    }

    .pipeline-fill {
      height: 100%;
      width: 0;
      background: linear-gradient(90deg, #3dbf54, #fc6767, #ff4da6);
      border-radius: 2px;
      transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: 0 0 12px rgba(252, 103, 103, 0.5);
    }

    /* Steps flex row */
    .pipeline-steps {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      position: relative;
      z-index: 1;
    }

    /* Each step — icon over label, column centered */
    .pipeline-step {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-decoration: none;
      cursor: pointer;
      transition: transform 0.2s;
    }

    .pipeline-step:hover {
      transform: translateY(-2px);
    }

    /* Circle — solid bg to cover track behind */
    .step-circle {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: 700;
      border: 2px solid rgba(255,255,255,0.12);
      background: var(--bg-secondary);
      color: rgba(255,255,255,0.25);
      transition: all 0.3s;
      margin-bottom: 4px;
      position: relative;
      z-index: 3;
    }

    /* Completed — solid bg to hide track */
    .pipeline-step.step-complete .step-circle {
      border-color: #3dbf54;
      color: #3dbf54;
      background: var(--bg-secondary);
      box-shadow: 0 0 12px rgba(61, 191, 84, 0.35), inset 0 0 8px rgba(61, 191, 84, 0.1);
    }

    .step-check {
      font-size: 16px;
      line-height: 1;
    }

    /* In-progress — solid bg */
    .pipeline-step.step-in_progress .step-circle {
      border-color: #fc6767;
      color: #fc6767;
      background: var(--bg-secondary);
      box-shadow: 0 0 16px rgba(252, 103, 103, 0.45), inset 0 0 6px rgba(252, 103, 103, 0.1);
      animation: activePulse 2s infinite;
    }

    .step-spinner {
      font-size: 16px;
      animation: spin 1s linear infinite;
    }

    /* Pending — solid dark bg */
    .pipeline-step.step-pending .step-circle {
      border-color: rgba(255,255,255,0.22);
      color: rgba(255,255,255,0.45);
      background: var(--bg-secondary);
    }

    .step-number {
      font-size: 12px;
    }

    /* Error — solid bg */
    .pipeline-step.step-error .step-circle {
      border-color: #f85149;
      color: #f85149;
      background: var(--bg-secondary);
      box-shadow: 0 0 12px rgba(248, 81, 73, 0.3);
    }

    /* Label */
    .step-label {
      font-size: 11px;
      font-weight: 600;
      color: rgba(255,255,255,0.6);
      transition: color 0.2s;
      white-space: nowrap;
    }

    .pipeline-step.step-complete .step-label {
      color: #3dbf54;
    }

    .pipeline-step.step-in_progress .step-label {
      color: #fc6767;
    }

    .pipeline-step:hover .step-label {
      color: rgba(255,255,255,0.95);
    }

    /* ===== Column 3: Right ===== */
    .header-right {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-shrink: 0;
    }

    .user-email {
      color: var(--text-secondary);
      font-size: 0.85rem;
    }

    .logout-btn {
      background: transparent;
      border: 1px solid var(--border-subtle);
      color: var(--text-secondary);
      padding: 6px 14px;
      font-size: 0.85rem;
      cursor: pointer;
      transition: all 0.2s;
    }

    .logout-btn:hover {
      border-color: var(--accent-error);
      color: var(--accent-error);
    }

    /* Main content — matches header padding */
    .main-content {
      margin-left: 320px;
      min-height: 100vh;
      padding: 24px;
      padding-top: 104px;
      position: relative;
    }

    /* Version switch loading overlay */
    .version-switch-overlay {
      position: fixed;
      top: 96px;
      left: 344px;
      right: 0;
      bottom: 0;
      background: rgba(15, 15, 23, 0.6);
      backdrop-filter: blur(3px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 25;
    }

    .version-switch-spinner {
      display: flex;
      align-items: center;
      gap: 12px;
      color: var(--text-primary);
      font-size: 1rem;
      font-weight: 500;
    }

    .version-switch-spinner i {
      animation: spin 1s linear infinite;
      font-size: 1.4rem;
      color: var(--brand-color);
    }

    /* ===== Gaming Animations ===== */
    @keyframes activePulse {
      0%, 100% {
        box-shadow: 0 0 12px rgba(252, 103, 103, 0.4);
        transform: scale(1);
      }
      50% {
        box-shadow: 0 0 20px rgba(252, 103, 103, 0.6);
        transform: scale(1.08);
      }
    }

    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
  `]
})
export class AppComponent implements OnInit, OnDestroy {
  private pipelineStore = inject(PipelineStore);
  private versionService = inject(VersionService);

  isAuthenticated = false;
  currentUser: any = null;
  screenSupported = true;
  screenWarningMessage = '';
  isLoginPage = false;
  isSwitchingVersion = false;

  appVersion = APP_VERSION;
  docsChangelogUrl = `${DOCS_BASE}/changelog`;
  docsGettingStartedUrl = `${DOCS_BASE}/getting-started`;

  updateStatus: UpdateStatus | null = null;
  isUpgrading = false;

  private authSub?: Subscription;
  private routerSub?: Subscription;
  private versionLoadingSub?: Subscription;

  constructor(
    private authService: AuthService,
    private router: Router,
    private screenCheck: ScreenCheckService,
    private updateService: UpdateService,
  ) {
    this.authSub = this.authService.isAuthenticated$.subscribe((auth) => {
      this.isAuthenticated = auth;
      this.currentUser = this.authService.getCurrentUser();
    });

    this.routerSub = this.router.events.pipe(filter(event => event instanceof NavigationEnd)).subscribe(() => {
      this.isLoginPage = this.router.url === '/login';
      setTimeout(() => {
        const auth = this.authService.isAuthenticated();
        if (!auth && !this.isLoginPage) {
          this.router.navigate(['/login']);
        } else if (auth && this.isLoginPage) {
          this.router.navigate(['/dashboard']);
        }
      }, 0);
    });

    // Subscribe to version loading state
    this.versionLoadingSub = this.versionService.loading$.subscribe(loading => {
      this.isSwitchingVersion = loading;
    });
  }

  /** Pipeline steps definition — drives the header progress bar */
  pipelineSteps() {
    return [
      { number: 1, key: 'brief',    route: '/brief-editor',     state: () => this.pipelineStore.getBriefPhase(),    labelKey: 'header.stepBrief' },
      { number: 2, key: 'contract', route: '/contract-viewer',  state: () => this.pipelineStore.getContractPhase(), labelKey: 'header.stepContract' },
      { number: 3, key: 'ir',       route: '/ir-explorer',      state: () => this.pipelineStore.getIRPhase(),       labelKey: 'header.stepIR' },
      { number: 4, key: 'code',     route: '/code-generator',   state: () => this.pipelineStore.getCodePhase(),     labelKey: 'header.stepCode' },
      { number: 5, key: 'preview',  route: '/preview',          state: () => this.pipelineStore.getPreviewPhase(),  labelKey: 'header.stepPreview' },
    ];
  }

  overallProgress() { return this.pipelineStore.overallProgress(); }
  activeVersion() { return this.pipelineStore.getActiveVersion(); }
  pipelineInitialized(): boolean {
    return this.pipelineStore.isWorkspaceInitialized();
  }

  ngOnInit(): void {
    this.screenSupported = this.screenCheck.isSupported();
    this.screenWarningMessage = this.screenCheck.getWarningMessage();
    this.pipelineStore.loadStatus();
    this.updateService.status$.subscribe((status) => {
      this.updateStatus = status;
      this.isUpgrading = status?.upgrading ?? false;
    });
    this.updateService.startPolling(120000);
  }

  ngOnDestroy(): void {
    this.authSub?.unsubscribe();
    this.routerSub?.unsubscribe();
    this.versionLoadingSub?.unsubscribe();
  }

  async handleLogout(): Promise<void> {
    await this.authService.logout();
    this.router.navigate(['/login']);
  }

  handleUpgrade(): void {
    this.updateService.upgrade().subscribe({
      next: (success) => {
        if (success) {
          this.isUpgrading = true;
          setTimeout(() => { window.location.reload(); }, 5000);
        }
      },
      error: () => { console.error('Upgrade failed'); },
    });
  }

  handleCheckUpdate(): void {
    this.updateService.forceCheck().subscribe();
  }
}
