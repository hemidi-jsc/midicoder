/**
 * I18n Service — quản lý ngôn ngữ giao diện WebGUI.
 *
 * - Import locale JSON trực tiếp (ESM)
 * - Lưu language preference vào localStorage
 * - Cung cấp signal `lang` để các component tự update khi đổi ngôn ngữ
 * - Cung cấp phương thức `t(key, params?)` để dịch text
 */

import { Injectable, signal, effect } from '@angular/core';

// Direct ESM import — không cần HTTP, không cần restart dev server
import viLocale from '../../locales/vi.json';
import enLocale from '../../locales/en.json';

const STORAGE_KEY = 'midicoder_language';
const DEFAULT_LANG = 'vi';

export interface LocaleData {
  [key: string]: any;
}

@Injectable({
  providedIn: 'root',
})
export class I18nService {
  /** Current language code — readable signal */
  readonly lang = signal<string>(DEFAULT_LANG);

  /** All loaded locales — loaded at construction time */
  private readonly locales: Record<string, LocaleData> = {
    vi: viLocale,
    en: enLocale,
  };

  constructor() {
    // Restore from localStorage
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && saved in this.locales) {
      this.lang.set(saved);
    }

    // Auto-save when language changes
    effect(() => {
      localStorage.setItem(STORAGE_KEY, this.lang());
    });
  }

  /**
   * Switch language — applies immediately.
   */
  setLanguage(code: string): void {
    if (code === this.lang() || !(code in this.locales)) return;
    this.lang.set(code);
  }

  /**
   * Translate a dot-separated key, e.g. 'nav.dashboard'
   * Supports interpolation: `t('update.newVersion', { latest: 'v2.0', current: 'v1.0' })`
   */
  t(key: string, params?: Record<string, any>): string {
    const locale = this.locales[this.lang()];
    if (!locale) return key;

    let value: any = locale;

    // Navigate nested object
    const parts = key.split('.');
    for (const part of parts) {
      if (value && typeof value === 'object') {
        value = value[part];
      } else {
        return key;
      }
    }

    if (typeof value !== 'string') {
      return key;
    }

    // Interpolate params: {{key}} syntax
    if (params) {
      for (const [k, v] of Object.entries(params)) {
        value = value.replace(new RegExp(`{{${k}}}`, 'g'), String(v));
      }
    }

    return value;
  }

  /**
   * Get current language code.
   */
  getLanguage(): string {
    return this.lang();
  }
}
