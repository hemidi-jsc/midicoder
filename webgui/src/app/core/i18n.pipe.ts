/**
 * I18n Pipe — dịch text trong template Angular.
 * 
 * Usage:
 *   {{ 'nav.dashboard' | i18n }}
 *   {{ 'update.newVersion' | i18n:{latest: 'v2.0', current: 'v1.0'} }}
 */

import { Pipe, PipeTransform } from '@angular/core';
import { I18nService } from './i18n.service';

@Pipe({
  name: 'i18n',
  standalone: true,
  pure: false, // Impure — re-evaluate khi language signal thay đổi
})
export class I18nPipe implements PipeTransform {
  constructor(private i18n: I18nService) {}

  transform(key: string, params?: Record<string, any>): string {
    return this.i18n.t(key, params);
  }
}
