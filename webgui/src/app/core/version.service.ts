/**
 * Version Service
 * Quản lý thông tin và chuyển đổi giữa các version
 */

import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { MockApiService } from './mock-api.service';

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
  private versionsSubject = new BehaviorSubject<VersionInfo[]>([]);
  private activeVersionSubject = new BehaviorSubject<string>('');

  readonly versions$ = this.versionsSubject.asObservable();
  readonly activeVersion$ = this.activeVersionSubject.asObservable();

  constructor(private mockApi: MockApiService) {
    this.loadVersions();
  }

  /**
   * Load danh sách versions từ mock API
   */
  private loadVersions(): void {
    // Mock data cho versions
    const mockVersions: VersionInfo[] = [
      {
        version: 'v1.0.1',
        status: 'active',
        createdAt: '2026-04-10T10:00:00Z',
        parentVersion: 'v1.0.0',
        progress: {
          init: 'complete',
          brief: 'complete',
          contract: 'complete',
          ir: 'complete',
          code: 'in_progress',
          preview: 'pending',
        },
        lastModified: '2026-04-10T15:30:00Z',
      },
      {
        version: 'v1.0.0',
        status: 'active',
        createdAt: '2026-04-09T08:00:00Z',
        progress: {
          init: 'complete',
          brief: 'complete',
          contract: 'complete',
          ir: 'complete',
          code: 'complete',
          preview: 'pending',
        },
        lastModified: '2026-04-09T18:00:00Z',
      },
      {
        version: 'v0.9.9',
        status: 'archived',
        createdAt: '2026-04-08T08:00:00Z',
        progress: {
          init: 'complete',
          brief: 'complete',
          contract: 'complete',
          ir: 'complete',
          code: 'complete',
          preview: 'complete',
        },
        lastModified: '2026-04-09T08:00:00Z',
      },
    ];

    this.versionsSubject.next(mockVersions);

    // Set active version từ localStorage hoặc default
    const savedActive = localStorage.getItem('midicoder_active_version');
    if (savedActive) {
      this.activeVersionSubject.next(savedActive);
    } else {
      this.activeVersionSubject.next(mockVersions[0]?.version || '');
    }
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
  }

  /**
   * Tạo version mới
   */
  async createVersion(request: CreateVersionRequest): Promise<VersionInfo> {
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
   * Update version progress
   */
  updateVersionProgress(version: string, phase: keyof VersionInfo['progress'], status: VersionInfo['progress'][keyof VersionInfo['progress']]): void {
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
   * Xóa version
   */
  async deleteVersion(version: string): Promise<void> {
    const versions = this.versionsSubject.getValue();
    const filtered = versions.filter(v => v.version !== version);
    this.versionsSubject.next(filtered);

    // Nếu xóa version đang active, set active version mới
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