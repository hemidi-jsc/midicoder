/**
 * Dịch vụ Authentication
 * Quản lý trạng thái đăng nhập, token, và user info
 * Dùng ApiService để kết nối với backend (auth hiện tại local/mock)
 */

import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { ApiService } from './api.service';
import { I18nService } from './i18n.service';
import { ApiResponse, LoginRequest, LoginResponse, UserResponse } from './api.types';

export interface User {
  id: string;
  email: string;
}

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private i18n = inject(I18nService);

  /**
   * Trạng thái đăng nhập
   */
  private isAuthenticatedSubject = new BehaviorSubject<boolean>(false);
  private userSubject = new BehaviorSubject<User | null>(null);
  private tokenSubject = new BehaviorSubject<string | null>(null);
  private isLoadingSubject = new BehaviorSubject<boolean>(false);
  private errorMessageSubject = new BehaviorSubject<string | null>(null);

  readonly isAuthenticated$ = this.isAuthenticatedSubject.asObservable();
  readonly user$ = this.userSubject.asObservable();
  readonly token$ = this.tokenSubject.asObservable();
  readonly isLoading$ = this.isLoadingSubject.asObservable();
  readonly errorMessage$ = this.errorMessageSubject.asObservable();

  constructor(private api: ApiService) {
    this.checkExistingSession();
  }

  /**
   * Check token đã tồn tại
   */
  private checkExistingSession(): void {
    const token = localStorage.getItem('midicoder_token');
    const user = localStorage.getItem('midicoder_user');

    if (token && user) {
      this.tokenSubject.next(token);
      this.userSubject.next(JSON.parse(user));
      this.isAuthenticatedSubject.next(true);
    }
  }

  /**
   * Đăng nhập - hiện tại dùng local mock (backend chưa có auth endpoint)
   * Cho phép đăng nhập với email/password bất kỳ
   */
  async login(email: string, password: string, _setMockMode: boolean = true): Promise<ApiResponse<LoginResponse>> {
    this.isLoadingSubject.next(true);
    this.errorMessageSubject.next(null);

    try {
      if (!email || !password) {
        this.errorMessageSubject.next(this.i18n.t('auth.enterCredentials'));
        return {
          success: false,
          error: { code: 'INVALID_CREDENTIALS', message: this.i18n.t('auth.enterCredentials') },
          timestamp: new Date().toISOString(),
        };
      }

      // Generate token và user
      const mockToken = `token_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const mockUser: User = {
        id: `user_${Date.now()}`,
        email: email,
      };

      const mockResponse: LoginResponse = {
        token: mockToken,
        user: mockUser,
        expires_in: 86400,
      };

      // Lưu token và user info
      this.tokenSubject.next(mockToken);
      this.userSubject.next(mockUser);
      this.isAuthenticatedSubject.next(true);

      localStorage.setItem('midicoder_token', mockToken);
      localStorage.setItem('midicoder_user', JSON.stringify(mockUser));

      return {
        success: true,
        data: mockResponse,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      this.errorMessageSubject.next(this.i18n.t('auth.loginError'));
      return {
        success: false,
        error: { code: 'UNKNOWN_ERROR', message: this.i18n.t('auth.loginError') },
        timestamp: new Date().toISOString(),
      };
    } finally {
      this.isLoadingSubject.next(false);
    }
  }

  /**
   * Đăng xuất
   */
  async logout(): Promise<ApiResponse> {
    this.tokenSubject.next(null);
    this.userSubject.next(null);
    this.isAuthenticatedSubject.next(false);

    localStorage.removeItem('midicoder_token');
    localStorage.removeItem('midicoder_user');

    return {
      success: true,
      message: this.i18n.t('auth.logoutSuccess'),
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Refresh token (placeholder - backend chưa có auth endpoint)
   */
  async refreshToken(): Promise<ApiResponse<LoginResponse>> {
    const token = this.getToken();
    if (token) {
      return {
        success: true,
        data: {
          token: token,
          user: this.getCurrentUser()!,
          expires_in: 86400,
        },
        timestamp: new Date().toISOString(),
      };
    }
    return {
      success: false,
      error: { code: 'NO_TOKEN', message: this.i18n.t('auth.noToken') },
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Get current user
   */
  getCurrentUser(): User | null {
    return this.userSubject.getValue();
  }

  /**
   * Get token
   */
  getToken(): string | null {
    return this.tokenSubject.getValue();
  }

  /**
   * Check đã đăng nhập chưa
   */
  isAuthenticated(): boolean {
    return this.isAuthenticatedSubject.getValue();
  }
}
