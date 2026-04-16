/**
 * Dịch vụ Authentication
 * Quản lý trạng thái đăng nhập, token, và user info
 */

import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { MockApiService, ApiResponse, LoginRequest, LoginResponse, UserResponse } from './mock-api.service';

export interface User {
  id: string;
  email: string;
  tier: 'free' | 'pro' | 'enterprise';
}

@Injectable({
  providedIn: 'root',
})
export class AuthService {
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

  constructor(private mockApi: MockApiService) {
    // Kiểm tra token trong localStorage khi khởi động
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
   * Mock login - Bypass midicoder.com authentication for testing
   * Cho phép đăng nhập nhanh với email/password bất kỳ (không cần server)
   */
  async mockLogin(email: string, password: string): Promise<ApiResponse<LoginResponse>> {
    this.isLoadingSubject.next(true);
    this.errorMessageSubject.next(null);

    try {
      // Accept any non-empty email and password for testing
      if (!email || !password) {
        this.errorMessageSubject.next('Vui lòng nhập email và mật khẩu');
        return {
          success: false,
          error: { code: 'INVALID_CREDENTIALS', message: 'Vui lòng nhập email và mật khẩu' },
          timestamp: new Date().toISOString(),
        };
      }

      // Generate mock token and user
      const mockToken = `mock_token_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const mockUser: User = {
        id: `user_${Date.now()}`,
        email: email,
        tier: 'pro',
      };

      const mockResponse: LoginResponse = {
        token: mockToken,
        user: mockUser,
        expires_in: 86400, // 24 hours
      };

      // Lưu token và user info
      this.tokenSubject.next(mockToken);
      this.userSubject.next(mockUser);
      this.isAuthenticatedSubject.next(true);

      // Lưu vào localStorage
      localStorage.setItem('midicoder_token', mockToken);
      localStorage.setItem('midicoder_user', JSON.stringify(mockUser));

      return {
        success: true,
        data: mockResponse,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      this.errorMessageSubject.next('Lỗi đăng nhập');
      return {
        success: false,
        error: { code: 'UNKNOWN_ERROR', message: 'Lỗi đăng nhập' },
        timestamp: new Date().toISOString(),
      };
    } finally {
      this.isLoadingSubject.next(false);
    }
  }

  /**
   * Đăng nhập (có thể use mock hoặc real API)
   * setMockMode = true để bypass midicoder.com
   */
  async login(email: string, password: string, setMockMode: boolean = true): Promise<ApiResponse<LoginResponse>> {
    // Nếu bật mock mode, dùng mock login
    if (setMockMode) {
      return this.mockLogin(email, password);
    }

    this.isLoadingSubject.next(true);
    this.errorMessageSubject.next(null);

    try {
      // Generate device fingerprint
      const deviceFingerprint = this.generateDeviceFingerprint();

      const request: LoginRequest = {
        email,
        password,
        device_fingerprint: deviceFingerprint,
      };

      const result = await this.mockApi.login(request);

      if (result.success && result.data) {
        // Lưu token và user info
        this.tokenSubject.next(result.data.token);
        this.userSubject.next(result.data.user);
        this.isAuthenticatedSubject.next(true);

        // Lưu vào localStorage
        localStorage.setItem('midicoder_token', result.data.token);
        localStorage.setItem('midicoder_user', JSON.stringify(result.data.user));
      } else {
        this.errorMessageSubject.next(result.error?.message || 'Đăng nhập thất bại');
      }

      return result;
    } catch (error) {
      this.errorMessageSubject.next('Lỗi kết nối');
      return {
        success: false,
        error: { code: 'NETWORK_ERROR', message: 'Lỗi kết nối' },
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
    // Xóa session trước
    this.tokenSubject.next(null);
    this.userSubject.next(null);
    this.isAuthenticatedSubject.next(false);

    // Xóa localStorage
    localStorage.removeItem('midicoder_token');
    localStorage.removeItem('midicoder_user');

    // Gọi API logout (optional, just for logging)
    const result = await this.mockApi.logout();
    return result;
  }

  /**
   * Refresh token
   */
  async refreshToken(): Promise<ApiResponse<LoginResponse>> {
    const result = await this.mockApi.refresh();

    if (result.success && result.data) {
      this.tokenSubject.next(result.data.token);
      localStorage.setItem('midicoder_token', result.data.token);
    }

    return result;
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

  /**
   * Generate device fingerprint
   */
  private generateDeviceFingerprint(): string {
    const factors = [
      navigator.userAgent,
      screen.width + 'x' + screen.height,
      navigator.language,
      new Date().getTimezoneOffset(),
      navigator.hardwareConcurrency || 'unknown',
    ];
    // Simple hash function
    let hash = 0;
    const str = factors.join('|');
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(16);
  }
}