import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, Router, NavigationEnd } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Subscription, filter } from 'rxjs';

import { AuthService } from './core/auth.service';
import { ScreenCheckService } from './core/screen-check.service';
import { SidebarComponent } from './components/sidebar/sidebar.component';

/** Application version — lấy từ package.json build-time, fallback nếu dev */
const APP_VERSION = '1.0.0';

/** Docs base URL theo version */
const DOCS_BASE = `https://docs.midicoder.com/${APP_VERSION}/ce`;

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, FormsModule, SidebarComponent],
  template: `
    <div class="min-h-screen bg-bg-primary text-text-primary">
      <!-- Screen Warning Overlay -->
      @if (!screenSupported) {
        <div class="fixed inset-0 z-50 bg-bg-primary bg-opacity-95 flex items-center justify-center">
          <div class="card max-w-md text-center">
            <h2 class="text-xl font-bold text-accent-warning mb-4">
              ⚠️ Cảnh báo màn hình
            </h2>
            <p class="text-text-secondary mb-4">
              {{ screenWarningMessage }}
            </p>
            <p class="text-text-tertiary text-sm">
              Ứng dụng có thể không hiển thị đúng trên màn hình nhỏ.
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
              title="Xem release trên GitHub"
            >
              v{{ appVersion }}
            </a>
            <div class="header-links">
              <a
                [attr.href]="docsChangelogUrl"
                target="_blank"
                rel="noopener noreferrer"
                class="header-link"
                title="Changelog"
              >
                Changelog
              </a>
              <span class="header-separator">·</span>
              <a
                [attr.href]="docsGettingStartedUrl"
                target="_blank"
                rel="noopener noreferrer"
                class="header-link"
                title="Tài liệu"
              >
                Docs
              </a>
            </div>
          </div>

          <!-- User Info - bên phải -->
          <div class="flex items-center space-x-4">
            <span class="text-text-secondary text-sm">{{ currentUser?.email }}</span>
            <button (click)="handleLogout()" class="logout-btn">
              Logout
            </button>
          </div>
        </header>

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

  private authSub?: Subscription;
  private routerSub?: Subscription;

  constructor(
    private authService: AuthService,
    private router: Router,
    private screenCheck: ScreenCheckService,
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
}
