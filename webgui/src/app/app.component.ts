import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, Router, NavigationEnd } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Subscription, filter } from 'rxjs';

import { APP_VERSION, DOCS_BASE } from './core/app.constants';
import { I18nPipe } from './core/i18n.pipe';
import { AuthService } from './core/auth.service';
import { ScreenCheckService } from './core/screen-check.service';
import { UpdateService } from './core/update.service';
import { SidebarComponent } from './components/sidebar/sidebar.component';
import type { UpdateStatus } from './core/api.types';

/** Application version — import từ shared constants */

/** Docs base URL theo version */

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, FormsModule, SidebarComponent, I18nPipe],
  template: `
    <div class="min-h-screen bg-bg-primary text-text-primary">
      <!-- Screen Warning Overlay -->
      @if (!screenSupported) {
        <div class="fixed inset-0 z-50 bg-bg-primary bg-opacity-95 flex items-center justify-center">
          <div class="card max-w-md text-center">
            <h2 class="text-xl font-bold text-accent-warning mb-4">
              ⚠️ {{ 'screen.title' | i18n }}
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
        <header class="fixed top-0 left-0 w-full bg-bg-secondary border-b border-border-primary z-50 flex items-center justify-between">
          <!-- Logo và App Version Badge - bên trái -->
          <div class="flex items-center space-x-3">
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

          <!-- User Info - bên phải -->
          <div class="flex items-center space-x-4">
            <span class="text-text-secondary text-sm">{{ currentUser?.email }}</span>
            <button (click)="handleLogout()" class="logout-btn">
              {{ 'auth.logout' | i18n }}
            </button>
          </div>
        </header>

        <!-- Update Banner — hiện khi có phiên bản mới -->
        @if (updateStatus && updateStatus.has_update && !isUpgrading) {
          <div class="update-banner" style="position:fixed;top:65px;left:0;right:0;z-index:40;background:linear-gradient(90deg,var(--brand-color),#ff4da6);color:#fff;display:flex;align-items:center;justify-content:center;padding:10px 48px;gap:16px;box-shadow:0 2px 12px rgba(233,0,137,0.25);">
            <span style="font-size:0.9rem;font-weight:500;">🎉 {{ 'update.banner' | i18n }} <strong>v{{ updateStatus.latest_version }}</strong> {{ 'update.currentVersion' | i18n:{current: updateStatus.current_version} }}</span>
            <a [attr.href]="updateStatus.download_url" target="_blank" rel="noopener noreferrer" style="color:#fff;text-decoration:underline;cursor:pointer;font-size:0.85rem;margin-left:4px;">{{ 'update.changelog' | i18n }}</a>
            <button (click)="handleUpgrade()" style="background:rgba(255,255,255,0.25);border:1px solid rgba(255,255,255,0.6);color:#fff;padding:5px 16px;border-radius:4px;cursor:pointer;font-size:0.85rem;font-weight:600;transition:background 0.2s;" title="{{ 'update.upgradeTitle' | i18n }}">
              ⬆ {{ 'update.upgrade' | i18n }}
            </button>
          </div>
        }

        <!-- Upgrading Overlay — hiện khi đang restart -->
        @if (isUpgrading) {
          <div style="position:fixed;inset:0;z-index:60;background:rgba(15,15,23,0.9);display:flex;align-items:center;justify-content:center;flex-direction:column;gap:16px;">
            <div style="font-size:2rem;animation:spin 1s linear infinite;">⏳</div>
            <p style="color:var(--text-primary);font-size:1.1rem;font-weight:500;">{{ 'update.upgrading' | i18n }}</p>
          </div>
        }

        <!-- Sidebar -->
        <app-sidebar *ngIf="isAuthenticated && !isLoginPage"></app-sidebar>
      }

      <!-- Main Content - router-outlet luôn render (bao gồm login) -->
      @if (isAuthenticated && !isLoginPage) {
        <main class="main-content">
          <router-outlet />
        </main>
      } @else {
        <router-outlet />
      }
    </div>
  `,
  styles: [`
    header {
      padding: 16px 48px;
    }

    .logo-header {
      height: 28px;
      width: auto;
    }

    /* App Version Badge */
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

    /* Header Links */
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

    .main-content {
      margin-left: 320px;
      min-height: calc(100vh - 65px);
      padding: 24px;
      padding-top: 65px;
    }
  `]
})
export class AppComponent implements OnInit, OnDestroy {
  /**
   * State
   */
  isAuthenticated = false;
  currentUser: any = null;
  projectName = '';
  screenSupported = true;
  screenWarningMessage = '';
  isLoginPage = false;

  /** App version to display in header */
  appVersion = APP_VERSION;
  docsChangelogUrl = `${DOCS_BASE}/changelog`;
  docsGettingStartedUrl = `${DOCS_BASE}/getting-started`;

  /** Update state */
  updateStatus: UpdateStatus | null = null;
  isUpgrading = false;

  private authSub?: Subscription;
  private routerSub?: Subscription;

  constructor(
    private authService: AuthService,
    private router: Router,
    private screenCheck: ScreenCheckService,
    private updateService: UpdateService,
  ) {
    // Subscribe to auth state changes
    this.authSub = this.authService.isAuthenticated$.subscribe((auth) => {
      this.isAuthenticated = auth;
      this.currentUser = this.authService.getCurrentUser();
    });

    // Subscribe to navigation events - check auth AFTER navigation completes
    this.routerSub = this.router.events.pipe(filter(event => event instanceof NavigationEnd)).subscribe(() => {
      this.isLoginPage = this.router.url === '/login';

      // Check auth after navigation completes to avoid redirect loops
      setTimeout(() => {
        const auth = this.authService.isAuthenticated();
        if (!auth && !this.isLoginPage) {
          this.router.navigate(['/login']);
        } else if (auth && this.isLoginPage) {
          this.router.navigate(['/dashboard']);
        }
      }, 0);
    });
  }

  ngOnInit(): void {
    this.screenSupported = this.screenCheck.isSupported();
    this.screenWarningMessage = this.screenCheck.getWarningMessage();

    // Subscribe to update status
    this.updateService.status$.subscribe((status) => {
      this.updateStatus = status;
      this.isUpgrading = status?.upgrading ?? false;
    });
    // Initial check + start polling
    this.updateService.startPolling(120000); // every 2 minutes
  }

  ngOnDestroy(): void {
    this.authSub?.unsubscribe();
    this.routerSub?.unsubscribe();
  }

  /**
   * Xử lý logout
   */
  async handleLogout(): Promise<void> {
    await this.authService.logout();
    this.router.navigate(['/login']);
  }

  /**
   * Xử lý upgrade phiên bản mới
   */
  handleUpgrade(): void {
    this.updateService.upgrade().subscribe({
      next: (success) => {
        if (success) {
          // Frontend sẽ mất kết nối khi backend shutdown
          // Hiện overlay "đang khởi động lại"
          this.isUpgrading = true;
          // Auto reload khi backend quay lại
          setTimeout(() => {
            window.location.reload();
          }, 5000);
        }
      },
      error: () => {
        console.error('Upgrade failed');
      },
    });
  }

  /**
   * Force kiểm tra phiên bản mới ngay
   */
  handleCheckUpdate(): void {
    this.updateService.forceCheck().subscribe();
  }
}
