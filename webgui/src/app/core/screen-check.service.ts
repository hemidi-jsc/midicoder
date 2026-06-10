/**
 * Dịch vụ kiểm tra độ phân giải màn hình
 * Yêu cầu tối thiểu 1366px width
 */

import { Injectable, inject } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { I18nService } from './i18n.service';

@Injectable({
  providedIn: 'root',
})
export class ScreenCheckService {
  private i18n = inject(I18nService);
  private readonly MIN_WIDTH = 1366;

  private isSupportedSubject = new BehaviorSubject<boolean>(true);

  readonly isSupported$ = this.isSupportedSubject.asObservable();

  constructor() {
    this.checkScreen();
    // Listen resize events
    window.addEventListener('resize', () => this.checkScreen());
  }

  /**
   * Kiểm tra màn hình có đạt yêu cầu không
   */
  checkScreen(): void {
    const supported = window.innerWidth >= this.MIN_WIDTH;
    this.isSupportedSubject.next(supported);
  }

  /**
   * Get current screen width
   */
  getScreenWidth(): number {
    return window.innerWidth;
  }

  /**
   * Check màn hình có hỗ trợ không
   */
  isSupported(): boolean {
    return this.isSupportedSubject.getValue();
  }

  /**
   * Lấy thông báo cảnh báo
   */
  getWarningMessage(): string {
    const currentWidth = window.innerWidth;
    return this.i18n.t('screen.warning', { current: currentWidth, min: this.MIN_WIDTH });
  }

  /**
   * Subscribe vào resize events
   */
  onResize(callback: () => void): () => void {
    const handler = () => callback();
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }
}