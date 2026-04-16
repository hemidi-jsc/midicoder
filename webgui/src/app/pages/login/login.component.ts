/**
 * Component trang đăng nhập
 */

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';

import { AuthService } from '../../core/auth.service';
import { MockApiService, ApiResponse } from '../../core/mock-api.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="min-h-screen flex items-center justify-center bg-bg-primary">
      <!-- Login Card -->
      <div class="card w-full max-w-md">
        <!-- Logo -->
        <div class="text-center mb-8">
          <h1 class="text-3xl font-bold text-accent-primary mb-2">Midicoder</h1>
          <p class="text-text-secondary">Chào mừng trở lại</p>
        </div>

        <!-- Error Message -->
        @if (errorMessage$ | async) {
          <div class="mb-4 p-3 bg-accent-error bg-opacity-10 border border-accent-error rounded text-accent-error text-sm">
            {{ errorMessage$ | async }}
          </div>
        }

        <!-- Login Form -->
        <form (ngSubmit)="handleLogin()" class="space-y-4">
          <!-- Email -->
          <div>
            <label class="block text-text-secondary mb-2">Email</label>
            <input
              type="email"
              [(ngModel)]="email"
              name="email"
              class="input"
              placeholder="test@example.com"
              required
            />
          </div>

          <!-- Password -->
          <div>
            <label class="block text-text-secondary mb-2">Mật khẩu</label>
            <input
              type="password"
              [(ngModel)]="password"
              name="password"
              class="input"
              placeholder="password"
              required
            />
          </div>

          <!-- Loading Spinner -->
          @if (isLoading$ | async) {
            <div class="flex justify-center py-4">
              <div class="spinner"></div>
            </div>
          }

          <!-- Submit Button -->
          <button
            type="submit"
            class="btn btn-primary w-full"
            [disabled]="isLoading$ | async"
          >
            {{ (isLoading$ | async) ? 'Đang tải...' : 'Đăng nhập' }}
          </button>
        </form>

        <!-- Signup Link -->
        <div class="mt-6 text-center">
          <p class="text-text-tertiary text-sm">
            Bạn chưa có tài khoản? Đăng ký tại midicoder.com
          </p>
          <a
            href="https://midicoder.com/register"
            target="_blank"
            class="text-accent-primary hover:underline text-sm mt-1 inline-block"
          >
            Đăng ký tài khoản →
          </a>
        </div>

        <!-- Demo Credentials -->
        <div class="mt-6 p-3 bg-bg-secondary rounded border border-border-primary">
          <p class="text-text-tertiary text-xs mb-2">Lưu ý: Demo credentials</p>
          <p class="text-text-secondary text-xs">Email: test@example.com</p>
          <p class="text-text-secondary text-xs">Password: password</p>
        </div>
      </div>
    </div>
  `,
  styles: [],
})
export class LoginComponent implements OnInit {
  email = '';
  password = '';
  isLoading$: Observable<boolean> = new Observable();
  errorMessage$: Observable<string | null> = new Observable();

  constructor(
    private authService: AuthService,
    private router: Router,
  ) {}

  ngOnInit(): void {
    this.isLoading$ = this.authService.isLoading$;
    this.errorMessage$ = this.authService.errorMessage$;
  }

  async handleLogin(): Promise<void> {
    const result = await this.authService.login(this.email, this.password);

    if (result.success) {
      this.router.navigate(['/dashboard']);
    }
    // Error đã được handle trong AuthService
  }
}