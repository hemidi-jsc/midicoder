/**
 * General Settings Page
 * Quản lý cài đặt chung: Language, WebGUI, Version, Services (Neo4j, MCP)
 */

import { Component, OnInit, inject, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { APP_VERSION, DOCS_BASE } from '../../core/app.constants';
import { ApiService } from '../../core/api.service';
import { I18nService } from '../../core/i18n.service';
import { I18nPipe } from '../../core/i18n.pipe';

interface SettingsData {
  [key: string]: any;
}

@Component({
  selector: 'app-general-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, I18nPipe],
  template: `
    <div class="py-8">
      <!-- Header -->
      <div class="mb-6">
        <div class="page-header-row">
          <h1 class="text-2xl font-bold">{{ 'settings.title' | i18n }}</h1>
          <a href="{{ docsUrl }}" target="_blank" rel="noopener" class="docs-link">{{ 'common.readGuide' | i18n }}</a>
        </div>
        <p class="text-text-secondary mt-1">{{ 'settings.subtitle' | i18n }}</p>
        <div class="info-notice">
          <span class="notice-icon"><i class="fa-solid fa-circle-info"></i></span>
          <span>{{ 'settings.comingSoon' | i18n }}</span>
        </div>
      </div>

      <!-- Status Messages -->
      @if (successMessage) {
        <div class="mb-4 p-3 rounded border" style="background: rgba(63, 185, 80, 0.1); border-color: var(--accent-success); color: var(--accent-success)">
          {{ successMessage }}
        </div>
      }
      @if (errorMessage) {
        <div class="mb-4 p-3 rounded border" style="background: rgba(242, 83, 83, 0.1); border-color: var(--accent-error); color: var(--accent-error)">
          {{ errorMessage }}
        </div>
      }

      @if (loading) {
        <div class="flex items-center justify-center h-40 text-text-tertiary">{{ 'settings.loading' | i18n }}</div>
      } @else {

        <!-- General / Language -->
        <div class="card">
          <h2 class="text-lg font-semibold mb-4">{{ 'settings.language' | i18n }}</h2>
          <div class="setting-item">
            <label class="setting-label">{{ 'settings.interfaceLang' | i18n }}</label>
            <select [(ngModel)]="settings['cli.language']" class="setting-select" (change)="onLanguageChange()">
              <option value="vi">{{ 'settings.vietnamese' | i18n }}</option>
              <option value="en">{{ 'settings.english' | i18n }}</option>
            </select>
            <span class="setting-desc">{{ 'settings.interfaceLangDesc' | i18n }}</span>
          </div>
          <div class="card-actions">
            <button class="btn btn-primary text-sm" (click)="saveSection('cli.language')" [disabled]="saving">
              {{ saving ? ('settings.saving' | i18n) : ('settings.save' | i18n) }}
            </button>
          </div>
        </div>

        <!-- WebGUI -->
        <div class="card">
          <h2 class="text-lg font-semibold mb-4">{{ 'settings.webgui' | i18n }}</h2>
          <div class="setting-grid">
            <div class="setting-item">
              <label class="setting-label">{{ 'settings.backendHost' | i18n }}</label>
              <input [(ngModel)]="settings['webgui.host']" class="setting-input" (change)="markDirty()" />
            </div>
            <div class="setting-item">
              <label class="setting-label">{{ 'settings.backendPort' | i18n }}</label>
              <input type="number" [(ngModel)]="settings['webgui.port']" class="setting-input" (change)="markDirty()" />
            </div>
            <div class="setting-item">
              <label class="setting-label">{{ 'settings.frontendPort' | i18n }}</label>
              <input type="number" [(ngModel)]="settings['webgui.frontend_port']" class="setting-input" (change)="markDirty()" />
            </div>
          </div>
          <div class="setting-item">
            <label class="setting-label">{{ 'settings.autoStart' | i18n }}</label>
            <label class="toggle">
              <input type="checkbox" [(ngModel)]="settings['webgui.auto_start']" (change)="markDirty()" />
              <span class="toggle-slider"></span>
            </label>
            <span class="setting-desc">{{ 'settings.autoStartDesc' | i18n }}</span>
          </div>
          <div class="setting-item">
            <label class="setting-label">{{ 'settings.openBrowser' | i18n }}</label>
            <label class="toggle">
              <input type="checkbox" [(ngModel)]="settings['webgui.open_browser']" (change)="markDirty()" />
              <span class="toggle-slider"></span>
            </label>
            <span class="setting-desc">{{ 'settings.openBrowserDesc' | i18n }}</span>
          </div>
          <div class="card-actions">
            <button class="btn btn-primary text-sm" (click)="saveSection('webgui')" [disabled]="saving">
              {{ saving ? ('settings.saving' | i18n) : ('settings.save' | i18n) }}
            </button>
          </div>
        </div>

        <!-- Version -->
        <div class="card">
          <h2 class="text-lg font-semibold mb-4">{{ 'settings.version' | i18n }}</h2>
          <div class="setting-item">
            <label class="setting-label">{{ 'settings.maxVersions' | i18n }}</label>
            <input type="number" [(ngModel)]="settings['version.max_versions']" class="setting-input" min="3" max="20" (change)="markDirty()" />
            <span class="setting-desc">{{ 'settings.maxVersionsDesc' | i18n }}</span>
          </div>
          <div class="card-actions">
            <button class="btn btn-primary text-sm" (click)="saveSection('version.max_versions')" [disabled]="saving">
              {{ saving ? ('settings.saving' | i18n) : ('settings.save' | i18n) }}
            </button>
          </div>
        </div>

        <!-- Neo4j -->
        <div class="card">
          <h2 class="text-lg font-semibold mb-4">{{ 'settings.neo4j' | i18n }}</h2>
          <div class="setting-grid">
            <div class="setting-item">
              <label class="setting-label">{{ 'settings.host' | i18n }}</label>
              <input [(ngModel)]="settings['neo4j.host']" class="setting-input" (change)="markDirty()" />
            </div>
            <div class="setting-item">
              <label class="setting-label">{{ 'settings.port' | i18n }}</label>
              <input type="number" [(ngModel)]="settings['neo4j.port']" class="setting-input" (change)="markDirty()" />
            </div>
            <div class="setting-item">
              <label class="setting-label">{{ 'settings.username' | i18n }}</label>
              <input [(ngModel)]="settings['neo4j.username']" class="setting-input" (change)="markDirty()" />
            </div>
            <div class="setting-item">
              <label class="setting-label">{{ 'settings.password' | i18n }}</label>
              <input type="password" [(ngModel)]="settings['neo4j.password']" class="setting-input" (change)="markDirty()" />
            </div>
          </div>
          <div class="setting-item">
            <label class="setting-label">{{ 'settings.dockerAutoStart' | i18n }}</label>
            <label class="toggle">
              <input type="checkbox" [(ngModel)]="settings['neo4j.docker_auto_start']" (change)="markDirty()" />
              <span class="toggle-slider"></span>
            </label>
            <span class="setting-desc">{{ 'settings.dockerAutoStartDesc' | i18n }}</span>
          </div>
          <div class="card-actions">
            <button class="btn btn-primary text-sm" (click)="saveSection('neo4j')" [disabled]="saving">
              {{ saving ? ('settings.saving' | i18n) : ('settings.save' | i18n) }}
            </button>
          </div>
        </div>

        <!-- MCP -->
        <div class="card">
          <h2 class="text-lg font-semibold mb-4">{{ 'settings.mcp' | i18n }}</h2>
          <div class="setting-grid">
            <div class="setting-item">
              <label class="setting-label">{{ 'settings.host' | i18n }}</label>
              <input [(ngModel)]="settings['mcp.host']" class="setting-input" (change)="markDirty()" />
            </div>
            <div class="setting-item">
              <label class="setting-label">{{ 'settings.port' | i18n }}</label>
              <input type="number" [(ngModel)]="settings['mcp.port']" class="setting-input" (change)="markDirty()" />
            </div>
          </div>
          <div class="card-actions">
            <button class="btn btn-primary text-sm" (click)="saveSection('mcp')" [disabled]="saving">
              {{ saving ? ('settings.saving' | i18n) : ('settings.save' | i18n) }}
            </button>
          </div>
        </div>

        <!-- System Info -->
        <div class="card">
          <h2 class="text-lg font-semibold mb-4">{{ 'settings.systemInfo' | i18n }}</h2>
          <div class="info-grid">
            <div class="info-row">
              <span class="info-label">{{ 'settings.midicoderVersion' | i18n }}</span>
              <span class="info-value">{{ settings['version'] || appVersion }}</span>
            </div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    /* Page header docs link */
    .page-header-row {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .docs-link {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--accent-primary, #fc6767);
      text-decoration: none;
      letter-spacing: 0.04em;
      transition: color 0.2s;
    }

    .docs-link:hover {
      text-decoration: underline;
    }

    .card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      padding: 24px;
      margin-bottom: 24px;
    }

    /* Info notice */
    .info-notice {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      margin-top: 16px;
      padding: 12px 16px;
      background: rgba(66, 133, 244, 0.08);
      border: 1px solid rgba(66, 133, 244, 0.25);
      border-radius: 6px;
      font-size: 0.82rem;
      color: var(--text-secondary);
      line-height: 1.5;
    }

    .notice-icon {
      flex-shrink: 0;
      font-size: 1rem;
    }

    .setting-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 16px;
    }

    .setting-item {
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-bottom: 16px;
    }

    .setting-label {
      font-size: 0.82rem;
      font-weight: 500;
      color: var(--text-secondary);
    }

    .setting-input {
      padding: 8px 12px;
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      color: var(--text-primary);
      border-radius: 4px;
      font-size: 0.85rem;
      font-family: monospace;
      width: 100%;
      max-width: 300px;
    }

    .setting-input:focus {
      outline: none;
      border-color: var(--brand-color);
      box-shadow: var(--glow-sm);
    }

    .setting-select {
      padding: 8px 12px;
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      color: var(--text-primary);
      border-radius: 4px;
      font-size: 0.85rem;
      width: 200px;
    }

    .setting-select:focus {
      outline: none;
      border-color: var(--brand-color);
    }

    .setting-desc {
      font-size: 0.75rem;
      color: var(--text-tertiary);
      margin-top: 2px;
    }

    /* Toggle Switch */
    .toggle {
      position: relative;
      display: inline-flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
    }

    .toggle input {
      opacity: 0;
      width: 0;
      height: 0;
      position: absolute;
    }

    .toggle-slider {
      display: inline-block;
      width: 40px;
      height: 22px;
      background: var(--bg-tertiary);
      border-radius: 11px;
      position: relative;
      transition: background 0.2s;
    }

    .toggle-slider::after {
      content: '';
      position: absolute;
      top: 3px;
      left: 3px;
      width: 16px;
      height: 16px;
      background: var(--text-secondary);
      border-radius: 50%;
      transition: transform 0.2s;
    }

    .toggle input:checked + .toggle-slider {
      background: var(--brand-color);
    }

    .toggle input:checked + .toggle-slider::after {
      transform: translateX(18px);
      background: white;
    }

    .card-actions {
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid var(--border-subtle);
    }

    /* Info section */
    .info-grid {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .info-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid var(--border-subtle);
    }

    .info-row:last-child {
      border-bottom: none;
    }

    .info-label {
      font-size: 0.82rem;
      color: var(--text-secondary);
    }

    .info-value {
      font-size: 0.82rem;
      font-weight: 600;
      font-family: monospace;
      color: var(--text-primary);
    }

    .btn {
      padding: 8px 16px;
      font-size: 0.85rem;
      font-weight: 500;
      border: none;
      cursor: pointer;
      transition: all 0.2s;
      border-radius: 4px;
    }

    .btn-primary {
      background: var(--brand-gradient);
      color: white;
    }

    .btn-primary:hover:not(:disabled) {
      box-shadow: var(--glow-md);
    }

    .btn-primary:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  `]
})
export class GeneralSettingsComponent implements OnInit {
  private api = inject(ApiService);
  private i18n = inject(I18nService);
  private zone = inject(NgZone);

  readonly appVersion = APP_VERSION;
  readonly docsUrl = `${DOCS_BASE}/settings`;

  settings: SettingsData = {};
  loading = false;
  saving = false;
  successMessage = '';
  errorMessage = '';

  ngOnInit(): void {
    this.loadSettings();
  }

  loadSettings(): void {
    this.loading = true;
    this.api.listConfig().then(resp => {
      this.loading = false;
      if (resp.success && resp.data) {
        this.zone.run(() => {
          this.settings = resp.data as SettingsData;
          // Sync backend language with frontend I18nService
          if (this.settings['cli.language']) {
            this.i18n.setLanguage(this.settings['cli.language']);
          }
        });
      } else {
        this.zone.run(() => {
          this.errorMessage = this.i18n.t('settings.loadError');
        });
      }
    }).catch(() => {
      this.loading = false;
      this.zone.run(() => {
        this.errorMessage = this.i18n.t('settings.connectError');
      });
    });
  }

  /** User changed language — apply immediately, then prompt to save */
  onLanguageChange(): void {
    const lang = this.settings['cli.language'];
    if (lang) {
      this.i18n.setLanguage(lang);
    }
  }

  markDirty(): void {
    // No-op — just marks that changes were made (visual feedback handled by save button)
  }

  saveSection(section: string): void {
    this.saving = true;
    this.successMessage = '';
    this.errorMessage = '';

    let keysToSave: string[];

    if (section === 'cli.language') {
      keysToSave = ['cli.language'];
    } else if (section === 'webgui') {
      keysToSave = ['webgui.host', 'webgui.port', 'webgui.frontend_port', 'webgui.auto_start', 'webgui.open_browser'];
    } else if (section === 'version.max_versions') {
      keysToSave = ['version.max_versions'];
    } else if (section === 'neo4j') {
      keysToSave = ['neo4j.host', 'neo4j.port', 'neo4j.username', 'neo4j.password', 'neo4j.docker_auto_start'];
    } else if (section === 'mcp') {
      keysToSave = ['mcp.host', 'mcp.port'];
    } else {
      keysToSave = [];
    }

    // Save each key via POST /config/set
    let saved = 0;
    const promises = keysToSave.map(key => {
      const value = this.settings[key];
      return this.api.setConfig({ key, value: String(value) }).then(resp => {
        if (resp.success) saved++;
      }).catch(() => {});
    });

    Promise.all(promises).then(() => {
      this.saving = false;
      this.zone.run(() => {
        if (saved === keysToSave.length) {
          this.successMessage = this.i18n.t('settings.saved');
        } else {
          this.errorMessage = this.i18n.t('settings.savedCount', { saved: String(saved), total: String(keysToSave.length) });
        }
        // Clear message after 3s
        setTimeout(() => {
          this.zone.run(() => {
            this.successMessage = '';
            this.errorMessage = '';
          });
        }, 3000);
      });
    }).catch(() => {
      this.saving = false;
      this.zone.run(() => {
        this.errorMessage = this.i18n.t('settings.saveError');
      });
    });
  }
}
