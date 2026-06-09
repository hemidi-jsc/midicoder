/**
 * Version Service
 * Quản lý thông tin và chuyển đổi giữa các version
 * Sử dụng API thực từ backend FastAPI
 */

import { Injectable, inject } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { ApiService } from './api.service';

export interface VersionInfo {
  version: string;
  status: 'draft' | 'inbuild' | 'archived';
  createdAt: string;
  progress: {
    init: 'pending' | 'in_progress' | 'complete' | 'error';
    brief: 'pending' | 'in_progress' | 'complete' | 'error';
    contract: 'pending' | 'in_progress' | 'complete' | 'error';
    ir: 'pending' | 'in_progress' | 'complete' | 'error';
    code: 'pending' | 'in_progress' | 'complete' | 'error';
    preview: 'pending' | 'in_progress' | 'complete' | 'error';
  };
  lastModified?: string;
}

export interface CreateVersionRequest {
  name: string;
}

@Injectable({
  providedIn: 'root',
})
export class VersionService {
  private api = inject(ApiService);

  private versionsSubject = new BehaviorSubject<VersionInfo[]>([]);
  private activeVersionSubject = new BehaviorSubject<string>('');

  readonly versions$ = this.versionsSubject.asObservable();
  readonly activeVersion$ = this.activeVersionSubject.asObservable();

  /**
   * Load danh sách tất cả versions từ backend API
   * Gọi GET /version/list để lấy versions, GET /pipeline/status để lấy pipeline progress
   */
  async loadVersions(): Promise<void> {
    try {
      // Load versions list từ backend
      const listResult = await this.api.listVersions();
      const versions: VersionInfo[] = [];

      if (listResult.success && listResult.data?.versions) {
        const backendVersions = listResult.data.versions;
        const activeVersionName = listResult.data.active_version;

        // Build VersionInfo cho từng version
        for (const bv of backendVersions) {
          const vname = bv.version || bv.name || '';
          // Strip leading 'v' for display
          const displayVersion = vname.startsWith('v') ? vname : 'v' + vname;

          const versionInfo: VersionInfo = {
            version: displayVersion,
            status: bv.status || 'draft',
            createdAt: bv.created_at || '',
            progress: {
              init: 'pending',
              brief: 'pending',
              contract: 'pending',
              ir: 'pending',
              code: 'pending',
              preview: 'pending',
            },
            lastModified: bv.updated_at || bv.created_at || '',
          };

          // Chỉ fill pipeline progress cho active version
          if (displayVersion === activeVersionName) {
            const statusResult = await this.api.getPipelineStatus();
            if (statusResult.success && statusResult.data) {
              const progress = statusResult.data.pipeline_progress || {};
              versionInfo.progress = {
                init: (progress.init as any) || 'pending',
                brief: (progress.brief as any) || 'pending',
                contract: (progress.contract as any) || 'pending',
                ir: (progress.ir as any) || 'pending',
                code: (progress.code as any) || 'pending',
                preview: ((progress as any).preview || 'pending') as any,
              };
            }
          }

          versions.push(versionInfo);
        }

        this.versionsSubject.next(versions);
        this.activeVersionSubject.next(activeVersionName || '');
        if (activeVersionName) {
          localStorage.setItem('midicoder_active_version', activeVersionName);
        }
      } else {
        this.versionsSubject.next([]);
        this.activeVersionSubject.next('');
      }
    } catch (error) {
      console.warn('Failed to load versions from backend:', error);
      this.versionsSubject.next([]);
    }
  }

  constructor() {
    this.loadVersions();
  }

  /**
   * Get danh sách versions
   */
  getVersions(): VersionInfo[] {
    return this.versionsSubject.getValue();
  }

  /**
   * Get version theo version string
   */
  getVersion(version: string): VersionInfo | undefined {
    return this.versionsSubject.getValue().find(v => v.version === version);
  }

  /**
   * Get active version
   */
  getActiveVersion(): string {
    return this.activeVersionSubject.getValue();
  }

  /**
   * Get active version info
   */
  getActiveVersionInfo(): VersionInfo | undefined {
    return this.getVersion(this.getActiveVersion());
  }

  /**
   * Set active version — gọi backend API POST /version/use để switch SQLite + config file
   * Block nếu version đã bị archived
   */
  async setActiveVersion(version: string): Promise<boolean> {
    // Block switch to archived version
    const target = this.getVersion(version);
    if (target && target.status === 'archived') {
      console.warn(`Cannot switch to archived version '${version}'`);
      return false;
    }

    try {
      const result = await this.api.useVersion({ version });
      if (result.success) {
        this.activeVersionSubject.next(version);
        localStorage.setItem('midicoder_active_version', version);
        // Reload để lấy pipeline progress của version mới
        await this.loadVersions();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to switch version:', error);
      return false;
    }
  }

  /**
   * Tạo version mới — gọi API POST /version/create
   */
  async createVersion(request: CreateVersionRequest): Promise<VersionInfo> {
    const result = await this.api.createVersion({ version: request.name });

    if (!result.success) {
      throw new Error(result.message || 'Failed to create version');
    }

    const newVersion: VersionInfo = {
      version: request.name,
      status: 'draft',
      createdAt: new Date().toISOString(),
      progress: {
        init: 'pending',
        brief: 'pending',
        contract: 'pending',
        ir: 'pending',
        code: 'pending',
        preview: 'pending',
      },
      lastModified: new Date().toISOString(),
    };

    const currentVersions = this.versionsSubject.getValue();
    currentVersions.unshift(newVersion);
    this.versionsSubject.next(currentVersions);

    // Version mới đã active trong SQLite (backend set_active=True), chỉ update local state
    this.activeVersionSubject.next(newVersion.version);
    localStorage.setItem('midicoder_active_version', newVersion.version);
    // Reload để sync toàn bộ danh sách versions + pipeline progress
    await this.loadVersions();

    return newVersion;
  }

  /**
   * Refresh pipeline progress cho version hiện tại
   */
  async refreshPipelineProgress(): Promise<void> {
    await this.loadVersions();
  }

  /**
   * Update version progress
   */
  updateVersionProgress(
    version: string,
    phase: keyof VersionInfo['progress'],
    status: VersionInfo['progress'][keyof VersionInfo['progress']]
  ): void {
    const versions = this.versionsSubject.getValue();
    const index = versions.findIndex(v => v.version === version);

    if (index !== -1) {
      versions[index].progress[phase] = status;
      versions[index].lastModified = new Date().toISOString();
      this.versionsSubject.next(versions);
    }
  }

  /**
   * Update version status
   */
  updateVersionStatus(version: string, status: 'draft' | 'inbuild' | 'archived'): void {
    const versions = this.versionsSubject.getValue();
    const index = versions.findIndex(v => v.version === version);

    if (index !== -1) {
      versions[index].status = status;
      this.versionsSubject.next(versions);
    }
  }

  /**
   * Xóa version (local only — backend không có endpoint này)
   */
  async deleteVersion(version: string): Promise<void> {
    const versions = this.versionsSubject.getValue();
    const filtered = versions.filter(v => v.version !== version);
    this.versionsSubject.next(filtered);

    if (this.getActiveVersion() === version && filtered.length > 0) {
      this.setActiveVersion(filtered[0].version);
    }
  }

  /**
   * Tính toán overall progress percentage cho version
   */
  calculateProgress(versionInfo: VersionInfo): number {
    const phases = Object.values(versionInfo.progress);
    const completed = phases.filter(p => p === 'complete').length;
    return Math.round((completed / phases.length) * 100);
  }
}