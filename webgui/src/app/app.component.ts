/**
 * Component chính của ứng dụng
 * Bao gồm layout: header, sidebar, main content
 */

import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, Router, NavigationEnd } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Subscription, filter } from 'rxjs';

import { AuthService } from './core/auth.service';
import { ScreenCheckService } from './core/screen-check.service';
import { VersionService } from './core/version.service';
import { SidebarComponent } from './components/sidebar/sidebar.component';

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
          <!-- Logo và Version Selector - bên trái -->
          <div class="flex items-center space-x-4">
            <img src="logo.png" alt="Midicoder" class="logo-header">
            <div class="version-selector">
              <select 
                [(ngModel)]="activeVersion" 
                (change)="switchVersion($event)"
                class="version-select"
              >
                @for (v of versions; track v.version) {
                  <option [value]="v.version">{{ v.version }}</option>
                }
              </select>
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

        <!-- Main Content -->
        <main class="main-content">
          <router-outlet />
        </main>
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

    .version-selector {
      position: relative;
    }

    .version-select {
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      color: var(--text-primary);
      padding: 6px 28px 6px 12px;
      font-size: 0.85rem;
      font-weight: 500;
      cursor: pointer;
      appearance: none;
      transition: all 0.2s;
    }

    .version-select:hover {
      border-color: var(--border-hover);
    }

    .version-select:focus {
      outline: none;
      border-color: var(--brand-color);
      box-shadow: var(--glow-sm);
    }

    .version-select option {
      background: var(--bg-secondary);
      color: var(--text-primary);
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
  
  // Version management
  versions: any[] = [];
  activeVersion = '';

  private authSub?: Subscription;
  private routerSub?: Subscription;
  private versionSub?: Subscription;
  private activeVersionSub?: Subscription;

  constructor(
    private authService: AuthService,
    private router: Router,
    private screenCheck: ScreenCheckService,
    private versionService: VersionService,
  ) {
    // Subscribe to auth state changes
    this.authSub = this.authService.isAuthenticated$.subscribe((auth) => {
      this.isAuthenticated = auth;
      this.currentUser = this.authService.getCurrentUser();
    });

    // Subscribe to versions
    this.versionSub = this.versionService.versions$.subscribe(versions => {
      this.versions = versions;
    });

    // Subscribe to active version
    this.activeVersionSub = this.versionService.activeVersion$.subscribe(version => {
      this.activeVersion = version;
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
    this.versionSub?.unsubscribe();
    this.activeVersionSub?.unsubscribe();
  }

  /**
   * Xử lý logout
   */
  async handleLogout(): Promise<void> {
    await this.authService.logout();
    // Auth state will be updated via subscription
  }

  /**
   * Switch version
   */
  switchVersion(event: Event): void {
    const select = event.target as HTMLSelectElement;
    const version = select.value;
    this.versionService.setActiveVersion(version);
  }
}
