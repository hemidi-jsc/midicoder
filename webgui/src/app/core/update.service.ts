/**
 * Update Service — kiểm tra & nâng cấp phiên bản midicoder
 */

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, map } from 'rxjs';
import type { UpdateStatus } from './api.types';

@Injectable({
  providedIn: 'root',
})
export class UpdateService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'http://localhost:6868/api';

  /** Shared state — frontend subscribe để hiện banner */
  private statusSubject = new BehaviorSubject<UpdateStatus | null>(null);
  readonly status$ = this.statusSubject.asObservable();

  /**
   * Lấy trạng thái update từ cache backend (không gọi network)
   */
  checkStatus(): void {
    this.http.get<{ success: boolean; data?: UpdateStatus }>(`${this.baseUrl}/update/status`).subscribe({
      next: (res) => {
        if (res.success && res.data) {
          this.statusSubject.next(res.data);
        }
      },
      error: () => {
        // Backend chưa sẵn sàng — ignore
      },
    });
  }

  /**
   * Force check GitHub API ngay lập tức
   */
  forceCheck(): Observable<UpdateStatus | null> {
    return this.http.post<{ success: boolean; data?: UpdateStatus }>(`${this.baseUrl}/update/check-now`, {}).pipe(
      map((res) => {
        if (res.success && res.data) {
          this.statusSubject.next(res.data);
          return res.data;
        }
        return null;
      })
    );
  }

  /**
   * Bắt đầu upgrade — backend sẽ shutdown & restart
   */
  upgrade(): Observable<boolean> {
    return this.http.post<{ success: boolean }>(`${this.baseUrl}/update/upgrade`, {}).pipe(
      map((res) => {
        if (res.success) {
          // Frontend sẽ mất kết nối sau này — set state để UI hiển thị "đang khởi động lại"
          this.statusSubject.next({
            has_update: false,
            current_version: '',
            latest_version: '',
            upgrading: true,
            release_notes: '',
            download_url: '',
            checked_at: '',
            assets: {},
            error: '',
          });
          return true;
        }
        return false;
      })
    );
  }

  /**
   * Subscribe để poll periodically mỗi 60s
   */
  startPolling(intervalMs: number = 60000): void {
    this.checkStatus();
    setInterval(() => this.checkStatus(), intervalMs);
  }
}
