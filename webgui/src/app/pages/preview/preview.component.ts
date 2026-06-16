/**
 * Component Preview
 * Quản lý preview của project
 */

import { Component, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { I18nPipe } from '../../core/i18n.pipe';
import { I18nService } from '../../core/i18n.service';
import { VersionService } from '../../core/version.service';
import { DOCS_BASE } from '../../core/app.constants';

@Component({
  selector: 'app-preview',
  standalone: true,
  imports: [CommonModule, RouterLink, I18nPipe],
  template: `
    <div>
      <!-- Header -->
      <div class="mb-6 flex items-center justify-between">
        <div>
          <div class="page-header-row">
            <h1 class="text-2xl font-bold">{{ 'preview.title' | i18n }}</h1>
            <a href="{{ docsUrl }}" target="_blank" rel="noopener" class="docs-link">{{ 'common.readGuide' | i18n }}</a>
          </div>
          <p class="text-text-secondary mt-1">{{ 'preview.subtitle' | i18n }}</p>
        </div>
        <div class="flex space-x-3">
          @if (previewStatus?.status !== 'running') {
            <button (click)="handleStart()" class="btn btn-primary" [disabled]="isProcessing">
              {{ 'preview.start' | i18n }}
            </button>
          } @else {
            <button (click)="handleStop()" class="btn btn-danger" [disabled]="isProcessing">
              {{ 'preview.stop' | i18n }}
            </button>
          }
        </div>
      </div>

      <!-- Success Message -->
      @if (successMessage) {
        <div class="mb-4 p-3 bg-accent-success bg-opacity-10 border border-accent-success rounded text-accent-success">
          {{ successMessage }}
        </div>
      }

      <!-- Preview Status -->
      @if (previewStatus) {
        <div class="card mb-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="font-semibold">{{ 'preview.status' | i18n }}</h2>
            <span class="px-3 py-1 rounded text-sm"
              [ngClass]="{
                'bg-accent-success bg-opacity-20 text-accent-success': previewStatus?.status === 'running',
                'bg-accent-error bg-opacity-20 text-accent-error': previewStatus?.status === 'error',
                'bg-bg-tertiary text-text-secondary': previewStatus?.status === 'stopped'
              }">
              {{ previewStatus?.status }}
            </span>
          </div>

          <!-- Services -->
          <div class="grid grid-cols-3 gap-4">
            @if (previewStatus?.services?.backend) {
              <div class="p-3 bg-bg-secondary rounded">
                <div class="font-medium text-sm mb-2">{{ 'preview.backend' | i18n }}</div>
                <div class="flex items-center justify-between">
                  <span class="text-xs text-text-tertiary">Port {{ previewStatus?.services?.backend.port }}</span>
                  <span class="text-xs" [ngClass]="previewStatus?.services?.backend.status === 'running' ? 'text-accent-success' : 'text-text-tertiary'">
                    {{ previewStatus?.services?.backend.status }}
                  </span>
                </div>
              </div>
            }
            @if (previewStatus?.services?.frontend) {
              <div class="p-3 bg-bg-secondary rounded">
                <div class="font-medium text-sm mb-2">{{ 'preview.frontend' | i18n }}</div>
                <div class="flex items-center justify-between">
                  <span class="text-xs text-text-tertiary">Port {{ previewStatus?.services?.frontend.port }}</span>
                  <span class="text-xs" [ngClass]="previewStatus?.services?.frontend.status === 'running' ? 'text-accent-success' : 'text-text-tertiary'">
                    {{ previewStatus?.services?.frontend.status }}
                  </span>
                </div>
              </div>
            }
            @if (previewStatus?.services?.db) {
              <div class="p-3 bg-bg-secondary rounded">
                <div class="font-medium text-sm mb-2">{{ 'preview.database' | i18n }}</div>
                <div class="flex items-center justify-between">
                  <span class="text-xs text-text-tertiary">Port {{ previewStatus?.services?.db.port }}</span>
                  <span class="text-xs" [ngClass]="previewStatus?.services?.db.status === 'running' ? 'text-accent-success' : 'text-text-tertiary'">
                    {{ previewStatus?.services?.db.status }}
                  </span>
                </div>
              </div>
            }
          </div>
        </div>
      }

      <!-- URLs -->
      @if (previewUrls) {
        <div class="card mb-6">
          <h2 class="font-semibold mb-4">{{ 'preview.urls' | i18n }}</h2>
          <div class="space-y-2">
            <div class="flex items-center justify-between p-3 bg-bg-secondary rounded">
              <span class="text-text-secondary">{{ 'preview.frontendUrl' | i18n }}</span>
              <a [href]="previewUrls?.frontend" target="_blank" class="text-accent-primary hover:underline">
                {{ previewUrls?.frontend }} →
              </a>
            </div>
            <div class="flex items-center justify-between p-3 bg-bg-secondary rounded">
              <span class="text-text-secondary">{{ 'preview.backendUrl' | i18n }}</span>
              <a [href]="previewUrls?.backend" target="_blank" class="text-accent-primary hover:underline">
                {{ previewUrls?.backend }} →
              </a>
            </div>
          </div>
        </div>
      }

      <!-- Logs -->
      @if (previewStatus?.logs) {
        <div class="card">
          <h2 class="font-semibold mb-4">{{ 'preview.logs' | i18n }}</h2>
          <div class="space-y-4">
            <div>
              <div class="text-sm text-text-tertiary mb-1">{{ 'preview.backendLogs' | i18n }}</div>
              <pre class="bg-bg-tertiary p-3 rounded text-xs font-mono overflow-auto max-h-32">{{ previewStatus?.logs?.backend }}</pre>
            </div>
            <div>
              <div class="text-sm text-text-tertiary mb-1">{{ 'preview.frontendLogs' | i18n }}</div>
              <pre class="bg-bg-tertiary p-3 rounded text-xs font-mono overflow-auto max-h-32">{{ previewStatus?.logs?.frontend }}</pre>
            </div>
          </div>
        </div>
      }

      <!-- Next Action -->
      <div class="mt-6 flex justify-end">
        <a routerLink="/feedback" class="btn btn-primary">
          {{ 'preview.feedback' | i18n }}
        </a>
      </div>
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
  `],
})
export class PreviewComponent implements OnInit, OnDestroy {
  private api = inject(ApiService);
  private i18n = inject(I18nService);
  private versionService = inject(VersionService);

  readonly docsUrl = `${DOCS_BASE}/preview`;

  previewStatus: any = null;
  previewUrls: any = null;
  isProcessing = false;
  successMessage = '';

  async ngOnInit(): Promise<void> {
    await this.loadStatus();

    // Reload khi version switch
    window.addEventListener('version-switched', this.onVersionSwitched);
  }

  ngOnDestroy(): void {
    window.removeEventListener('version-switched', this.onVersionSwitched);
  }

  /** Reload toàn bộ data khi version switch */
  private onVersionSwitched = async (event: any) => {
    try {
      await this.loadStatus();
    } finally {
      this.versionService.stopLoading();
    }
  };

  async loadStatus(): Promise<void> {
    const result = await this.api.getPreviewStatus();
    if (result.success && result.data) {
      this.previewStatus = result.data;
      if (result.data.status === 'running') {
        this.previewUrls = {
          frontend: 'http://localhost:3000',
          backend: 'http://localhost:3001',
        };
      }
    }
  }

  async handleStart(): Promise<void> {
    this.isProcessing = true;
    this.successMessage = '';

    const result = await this.api.startPreview({ version: 'v1.0.0' });

    if (result.success && result.data) {
      this.previewUrls = result.data.urls;
    }

    await this.loadStatus();

    this.isProcessing = false;
  }

  async handleStop(): Promise<void> {
    this.isProcessing = true;

    await this.api.stopPreview();

    this.previewUrls = null;
    await this.loadStatus();

    this.successMessage = this.i18n.t('preview.stopped');
    this.isProcessing = false;
  }
}