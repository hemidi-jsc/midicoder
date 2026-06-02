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
  status: 'draft' | 'active' | 'archived';
  createdAt: string;
  parentVersion?: string;
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
  fromVersion?: string;
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
   * Load danh sách versions từ backend API
   * Gọi GET /pipeline/versions + GET /pipeline/status
   */
  async loadVersions(): Promise<void> {
    try {
      // Load versions list
      const versionsResult = await this.api.getPipelineStatus();
      if (versionsResult.success && versionsResult.data) {
        const data = versionsResult.data;
        const activeVersion = data.active_version || '';

        // Build version info from pipeline progress
        const progress = data.pipeline_progress || {};

        const versionInfo: VersionInfo = {
          version: activeVersion || '',
          status: activeVersion ? 'active' : 'draft',
          createdAt: new Date().toISOString(),
          progress: {
            init: (progress.init as any) || 'pending',
            brief: (progress.brief as any) || 'pending',
            contract: (progress.contract as any) || 'pending',
            ir: (progress.ir as any) || 'pending',
            code: (progress.code as any) || 'pending',
            preview: ((progress as any).preview || 'pending') as any,
          },
          lastModified: new Date().toISOString(),
        };

        // Chỉ push version nếu có active_version thực sự
        if (activeVersion) {
          this.versionsSubject.next([versionInfo]);
        } else {
          this.versionsSubject.next([]);
        }
        this.activeVersionSubject.next(activeVersion || '');
        localStorage.setItem('midicoder_active_version', activeVersion || '');
      }
    } catch (error) {
      console.warn('Failed to load versions from backend:', error);
      // Không fallback localStorage khi project mới — chỉ fallback nếu có stored version
      const storedVersion = localStorage.getItem('midicoder_active_version') || '';
      // Xóa stale localStorage để tránh version cũ bám theo project mới
      localStorage.removeItem('midicoder_active_version');
      if (storedVersion) {
        this.activeVersionSubject.next(storedVersion);
      }
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
   * Set active version
   */
  setActiveVersion(version: string): void {
    this.activeVersionSubject.next(version);
    localStorage.setItem('midicoder_active_version', version);
    // Reload to get updated pipeline progress
    this.loadVersions();
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
      parentVersion: request.fromVersion,
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

    this.setActiveVersion(newVersion.version);

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
  updateVersionStatus(version: string, status: 'draft' | 'active' | 'archived'): void {
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