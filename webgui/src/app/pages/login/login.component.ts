/**
 * Login / Welcome screen — full-screen split layout.
 *
 * Left  (75%): brand, tagline, mascot + benefits
 * Right (25%): "Bắt đầu" button + trial link + footer
 */

import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

import { AuthService } from '../../core/auth.service';
import { I18nPipe } from '../../core/i18n.pipe';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, I18nPipe],
  template: `
    <div class="login-fullscreen">
      <!-- ======== LEFT COLUMN (brand) ======== -->
      <div class="login-left">
        <div class="login-left-inner">

          <!-- Logo + title -->
          <div class="brand-header">
            <img src="logo.png" alt="Midicoder" class="brand-logo" />
            <h1 class="brand-title">Midi Coder</h1>
            <p class="brand-tagline">Contract coding platform</p>
          </div>

          <!-- Mascot + benefits -->
          <div class="brand-body">
            <img src="mascot_1.png" alt="Mascot" class="brand-mascot" />
            <ul class="brand-benefits">
              <li>
                <span class="benefit-icon">&#10003;</span>
                <span>{{ 'auth.benefit1' | i18n }}</span>
              </li>
              <li>
                <span class="benefit-icon">&#10003;</span>
                <span>{{ 'auth.benefit2' | i18n }}</span>
              </li>
              <li>
                <span class="benefit-icon">&#10003;</span>
                <span>{{ 'auth.benefit3' | i18n }}</span>
              </li>
              <li>
                <span class="benefit-icon">&#10003;</span>
                <span>{{ 'auth.benefit4' | i18n }}</span>
              </li>
            </ul>
          </div>

        </div>
      </div>

      <!-- ======== RIGHT COLUMN (action) ======== -->
      <div class="login-right">
        <div class="login-right-inner">

          <!-- Primary CTA -->
          <button class="btn-start" (click)="handleStart()">
            {{ 'auth.start' | i18n }}
          </button>

          <!-- Trial link -->
          <a class="btn-trial" href="https://midicoder.com" target="_blank" rel="noopener noreferrer">
            {{ 'auth.trial' | i18n }}
          </a>

          <!-- Spacer pushes footer to bottom -->
          <div class="login-spacer"></div>

          <!-- Footer -->
          <footer class="login-footer">
            <div class="footer-links">
              <a href="https://midicoder.com" target="_blank" rel="noopener noreferrer">midicoder.com</a>
              <a href="https://hemidi.com/legal" target="_blank" rel="noopener noreferrer">Legal</a>
            </div>
            <p class="footer-copyright">&copy; 2026 &mdash; Hemidi JSC</p>
          </footer>

        </div>
      </div>
    </div>
  `,
  styles: [`
    /* ---- Full-screen split ---- */
    .login-fullscreen {
      display: flex;
      width: 100vw;
      height: 100vh;
      overflow: hidden;
      background: var(--bg-primary);
    }

    /* ---- Left column (75%) ---- */
    .login-left {
      flex: 3 3 75%;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 64px 80px;
      position: relative;
      overflow: hidden;
    }

    /* Subtle radial glow behind brand area */
    .login-left::before {
      content: '';
      position: absolute;
      inset: 0;
      background: radial-gradient(ellipse at 30% 50%,
          rgba(252, 103, 103, 0.06) 0%,
          transparent 70%);
      pointer-events: none;
    }

    .login-left-inner {
      position: relative;
      z-index: 1;
      max-width: 720px;
    }

    /* Brand header */
    .brand-header {
      margin-bottom: 56px;
    }

    .brand-logo {
      height: 56px;
      width: auto;
      margin-bottom: 20px;
      filter: drop-shadow(0 0 18px rgba(252, 103, 103, 0.25));
    }

    .brand-title {
      font-size: 3rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      margin: 0 0 8px 0;
      background: var(--brand-gradient);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .brand-tagline {
      font-size: 1.125rem;
      color: var(--text-secondary);
      margin: 0;
      font-weight: 400;
    }

    /* Body: mascot + benefits side-by-side */
    .brand-body {
      display: flex;
      align-items: center;
      gap: 48px;
    }

    .brand-mascot {
      flex-shrink: 0;
      width: 200px;
      height: auto;
      filter: drop-shadow(0 0 24px rgba(252, 103, 103, 0.12));
    }

    /* Benefits list */
    .brand-benefits {
      list-style: none;
      padding: 0;
      margin: 0;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .brand-benefits li {
      display: flex;
      align-items: flex-start;
      gap: 14px;
      color: var(--text-secondary);
      font-size: 0.95rem;
      line-height: 1.6;
    }

    .benefit-icon {
      flex-shrink: 0;
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      background: rgba(252, 103, 103, 0.12);
      color: var(--brand-color);
      font-size: 0.75rem;
      font-weight: 700;
      margin-top: 2px;
    }

    /* ---- Right column (25%) ---- */
    .login-right {
      flex: 1 1 25%;
      display: flex;
      flex-direction: column;
      justify-content: center;
      padding: 48px 48px 0;
      border-left: 1px solid var(--border-subtle);
      background: var(--bg-secondary);
    }

    .login-right-inner {
      display: flex;
      flex-direction: column;
      min-height: 0;
    }

    /* Start button */
    .btn-start {
      width: 100%;
      padding: 16px 24px;
      font-size: 1.0625rem;
      font-weight: 600;
      color: #fff;
      background: var(--brand-gradient);
      border: none;
      cursor: pointer;
      transition: box-shadow 0.2s, transform 0.15s;
      letter-spacing: 0.01em;
    }

    .btn-start:hover {
      box-shadow: var(--glow-md);
      transform: translateY(-1px);
    }

    .btn-start:active {
      transform: translateY(0);
    }

    /* Trial button */
    .btn-trial {
      display: block;
      width: 100%;
      padding: 14px 24px;
      margin-top: 14px;
      font-size: 0.9375rem;
      font-weight: 500;
      color: var(--text-secondary);
      background: transparent;
      border: 1px solid var(--border-subtle);
      text-align: center;
      text-decoration: none;
      transition: border-color 0.2s, color 0.2s;
    }

    .btn-trial:hover {
      border-color: var(--brand-color);
      color: var(--brand-color);
    }

    /* Spacer pushes footer to bottom */
    .login-spacer {
      flex: 1 1 auto;
    }

    /* Footer */
    .login-footer {
      padding: 32px 0;
    }

    .footer-links {
      display: flex;
      gap: 20px;
      margin-bottom: 12px;
    }

    .footer-links a {
      color: var(--text-muted);
      font-size: 0.8125rem;
      text-decoration: none;
      transition: color 0.2s;
    }

    .footer-links a:hover {
      color: var(--brand-color);
    }

    .footer-copyright {
      color: var(--text-muted);
      font-size: 0.75rem;
      margin: 0;
    }
  `],
})
export class LoginComponent {
  constructor(
    private authService: AuthService,
    private router: Router,
  ) {}

  /**
   * "Bắt đầu" — auto-login with mock credentials and navigate to dashboard.
   */
  async handleStart(): Promise<void> {
    const result = await this.authService.login('bighero@midicoder.com', 'demo2026');
    if (result.success) {
      this.router.navigate(['/dashboard']);
    }
  }
}
