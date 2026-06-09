/**
 * General Settings Page
 * Quản lý cài đặt chung: Language, WebGUI, Version, Services (Neo4j, MCP)
 */

import { Component, OnInit, inject, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/api.service';

interface SettingsData {
  [key: string]: any;
}

@Component({
  selector: 'app-general-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="container mx-auto px-6 py-8">
      <!-- Header -->
      <div class="mb-6">
        <h1 class="text-2xl font-bold">Cài đặt chung</h1>
        <p class="text-text-secondary mt-1">Quản lý cài đặt hệ thống, giao diện và dịch vụ</p>
        <div class="info-notice">
          <span class="notice-icon">ℹ️</span>
          <span>Các chức năng dưới đây chưa hoàn thiện trong version này của Midicoder, hiện chỉ có thể điều chỉnh mà không có tác dụng thực tế</span>
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
        <div class="flex items-center justify-center h-40 text-text-tertiary">Đang tải...</div>
      } @else {

        <!-- General / Language -->
        <div class="card">
          <h2 class="text-lg font-semibold mb-4">🌐 Ngôn ngữ</h2>
          <div class="setting-item">
            <label class="setting-label">Ngôn ngữ giao diện</label>
            <select [(ngModel)]="settings['cli.language']" class="setting-select" (change)="markDirty()">
              <option value="vi">Tiếng Việt</option>
              <option value="en">English</option>
            </select>
            <span class="setting-desc">Ngôn ngữ mặc định cho giao diện</span>
          </div>
          <div class="card-actions">
            <button class="btn btn-primary text-sm" (click)="saveSection('cli.language')" [disabled]="saving">
              {{ saving ? 'Đang lưu...' : 'Lưu' }}
            </button>
          </div>
        </div>

        <!-- WebGUI -->
        <div class="card">
          <h2 class="text-lg font-semibold mb-4">🖥️ WebGUI Server</h2>
          <div class="setting-grid">
            <div class="setting-item">
              <label class="setting-label">Backend Host</label>
              <input [(ngModel)]="settings['webgui.host']" class="setting-input" (change)="markDirty()" />
            </div>
            <div class="setting-item">
              <label class="setting-label">Backend Port</label>
              <input type="number" [(ngModel)]="settings['webgui.port']" class="setting-input" (change)="markDirty()" />
            </div>
            <div class="setting-item">
              <label class="setting-label">Frontend Port</label>
              <input type="number" [(ngModel)]="settings['webgui.frontend_port']" class="setting-input" (change)="markDirty()" />
            </div>
          </div>
          <div class="setting-item">
            <label class="setting-label">Auto-start Server</label>
            <label class="toggle">
              <input type="checkbox" [(ngModel)]="settings['webgui.auto_start']" (change)="markDirty()" />
              <span class="toggle-slider"></span>
            </label>
            <span class="setting-desc">Tự động khởi động backend/frontend khi mở ứng dụng</span>
          </div>
          <div class="setting-item">
            <label class="setting-label">Open Browser</label>
            <label class="toggle">
              <input type="checkbox" [(ngModel)]="settings['webgui.open_browser']" (change)="markDirty()" />
              <span class="toggle-slider"></span>
            </label>
            <span class="setting-desc">Tự động mở trình duyệt sau khi khởi động</span>
          </div>
          <div class="card-actions">
            <button class="btn btn-primary text-sm" (click)="saveSection('webgui')" [disabled]="saving">
              {{ saving ? 'Đang lưu...' : 'Lưu' }}
            </button>
          </div>
        </div>

        <!-- Version -->
        <div class="card">
          <h2 class="text-lg font-semibold mb-4">🏷️ Phiên bản</h2>
          <div class="setting-item">
            <label class="setting-label">Số phiên bản tối đa</label>
            <input type="number" [(ngModel)]="settings['version.max_versions']" class="setting-input" min="3" max="20" (change)="markDirty()" />
            <span class="setting-desc">Khi vượt quá giới hạn, các phiên bản cũ nhất sẽ bị xóa tự động (tối thiểu 3, tối đa 20)</span>
          </div>
          <div class="card-actions">
            <button class="btn btn-primary text-sm" (click)="saveSection('version.max_versions')" [disabled]="saving">
              {{ saving ? 'Đang lưu...' : 'Lưu' }}
            </button>
          </div>
        </div>

        <!-- Neo4j -->
        <div class="card">
          <h2 class="text-lg font-semibold mb-4">🔗 Neo4j Database</h2>
          <div class="setting-grid">
            <div class="setting-item">
              <label class="setting-label">Host</label>
              <input [(ngModel)]="settings['neo4j.host']" class="setting-input" (change)="markDirty()" />
            </div>
            <div class="setting-item">
              <label class="setting-label">Port</label>
              <input type="number" [(ngModel)]="settings['neo4j.port']" class="setting-input" (change)="markDirty()" />
            </div>
            <div class="setting-item">
              <label class="setting-label">Username</label>
              <input [(ngModel)]="settings['neo4j.username']" class="setting-input" (change)="markDirty()" />
            </div>
            <div class="setting-item">
              <label class="setting-label">Password</label>
              <input type="password" [(ngModel)]="settings['neo4j.password']" class="setting-input" (change)="markDirty()" />
            </div>
          </div>
          <div class="setting-item">
            <label class="setting-label">Docker Auto-start</label>
            <label class="toggle">
              <input type="checkbox" [(ngModel)]="settings['neo4j.docker_auto_start']" (change)="markDirty()" />
              <span class="toggle-slider"></span>
            </label>
            <span class="setting-desc">Tự động khởi động Neo4j trong Docker container</span>
          </div>
          <div class="card-actions">
            <button class="btn btn-primary text-sm" (click)="saveSection('neo4j')" [disabled]="saving">
              {{ saving ? 'Đang lưu...' : 'Lưu' }}
            </button>
          </div>
        </div>

        <!-- MCP -->
        <div class="card">
          <h2 class="text-lg font-semibold mb-4">🔧 MCP Server</h2>
          <div class="setting-grid">
            <div class="setting-item">
              <label class="setting-label">Host</label>
              <input [(ngModel)]="settings['mcp.host']" class="setting-input" (change)="markDirty()" />
            </div>
            <div class="setting-item">
              <label class="setting-label">Port</label>
              <input type="number" [(ngModel)]="settings['mcp.port']" class="setting-input" (change)="markDirty()" />
            </div>
          </div>
          <div class="card-actions">
            <button class="btn btn-primary text-sm" (click)="saveSection('mcp')" [disabled]="saving">
              {{ saving ? 'Đang lưu...' : 'Lưu' }}
            </button>
          </div>
        </div>

        <!-- System Info -->
        <div class="card">
          <h2 class="text-lg font-semibold mb-4">ℹ️ Thông tin hệ thống</h2>
          <div class="info-grid">
            <div class="info-row">
              <span class="info-label">Phiên bản Midicoder</span>
              <span class="info-value">{{ settings['version'] || '1.0.0' }}</span>
            </div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
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
  private zone = inject(NgZone);

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
        });
      } else {
        this.zone.run(() => {
          this.errorMessage = 'Không thể tải cài đặt';
        });
      }
    }).catch(() => {
      this.loading = false;
      this.zone.run(() => {
        this.errorMessage = 'Lỗi kết nối đến server';
      });
    });
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
          this.successMessage = `Đã lưu cài đặt (${saved}/${keysToSave.length})`;
        } else {
          this.errorMessage = `Lưu thành công ${saved}/${keysToSave.length} mục`;
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
        this.errorMessage = 'Lỗi khi lưu cài đặt';
      });
    });
  }
}
