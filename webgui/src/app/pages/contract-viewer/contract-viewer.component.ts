/**
 * Component Contract Viewer
 * Hiển thị DSL contracts dưới dạng tree view
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
  selector: 'app-contract-viewer',
  standalone: true,
  imports: [CommonModule, RouterLink, I18nPipe],
  template: `
    <div class="py-8">
      <!-- Header -->
      <div class="mb-6 flex items-center justify-between">
        <div>
          <div class="page-header-row">
            <h1 class="text-2xl font-bold">{{ 'contract.title' | i18n }}</h1>
            <a href="{{ docsUrl }}" target="_blank" rel="noopener" class="docs-link">{{ 'common.readGuide' | i18n }}</a>
          </div>
          <p class="text-text-secondary mt-1">{{ 'contract.subtitle' | i18n }}</p>
        </div>
        <div class="flex space-x-3">
          <button (click)="handleGenerate()" class="btn btn-primary" [disabled]="isGenerating">
            {{ isGenerating ? ('contract.loading' | i18n) : ('contract.generate' | i18n) }}
          </button>
          <button (click)="handleValidate()" class="btn btn-secondary" [disabled]="isValidating">
            {{ isValidating ? ('contract.loading' | i18n) : ('contract.validate' | i18n) }}
          </button>
        </div>
      </div>

      <!-- Success Message -->
      @if (successMessage) {
        <div class="mb-4 p-3 bg-accent-success bg-opacity-10 border border-accent-success rounded text-accent-success">
          {{ successMessage }}
        </div>
      }

      <!-- Summary Stats -->
      @if (contractSummary) {
        <div class="grid grid-cols-5 gap-4 mb-6">
          <div class="card text-center">
            <div class="text-2xl font-bold text-accent-primary">{{ contractSummary?.entities }}</div>
            <div class="text-sm text-text-tertiary">{{ 'contract.entities' | i18n }}</div>
          </div>
          <div class="card text-center">
            <div class="text-2xl font-bold text-accent-primary">{{ contractSummary?.commands }}</div>
            <div class="text-sm text-text-tertiary">{{ 'contract.commands' | i18n }}</div>
          </div>
          <div class="card text-center">
            <div class="text-2xl font-bold text-accent-primary">{{ contractSummary?.queries }}</div>
            <div class="text-sm text-text-tertiary">{{ 'contract.queries' | i18n }}</div>
          </div>
          <div class="card text-center">
            <div class="text-2xl font-bold text-accent-primary">{{ contractSummary?.events }}</div>
            <div class="text-sm text-text-tertiary">{{ 'contract.events' | i18n }}</div>
          </div>
          <div class="card text-center">
            <div class="text-2xl font-bold text-accent-primary">{{ contractSummary?.workflows }}</div>
            <div class="text-sm text-text-tertiary">{{ 'contract.workflows' | i18n }}</div>
          </div>
        </div>
      }

      <!-- Contract Tree -->
      @if (contractIR) {
        <div class="grid grid-cols-3 gap-6">
          <!-- Entities -->
          <div class="card">
            <h3 class="font-semibold mb-4 text-accent-primary">{{ 'contract.entities' | i18n }}</h3>
            @if (contractIR?.entities?.length) {
              <div class="space-y-2">
                @for (entity of contractIR?.entities; track entity.name) {
                  <div class="p-2 bg-bg-secondary rounded">
                    <div class="font-medium text-sm">{{ entity.name }}</div>
                    <div class="text-xs text-text-tertiary">{{ entity.table }}</div>
                  </div>
                }
              </div>
            }
          </div>

          <!-- Commands -->
          <div class="card">
            <h3 class="font-semibold mb-4 text-accent-primary">{{ 'contract.commands' | i18n }}</h3>
            @if (contractIR?.commands?.length) {
              <div class="space-y-2">
                @for (cmd of contractIR?.commands; track cmd.name) {
                  <div class="p-2 bg-bg-secondary rounded">
                    <div class="font-medium text-sm">{{ cmd.name }}</div>
                  </div>
                }
              </div>
            } @else {
              <p class="text-sm text-text-tertiary">{{ 'contract.noCommands' | i18n }}</p>
            }
          </div>

          <!-- Queries -->
          <div class="card">
            <h3 class="font-semibold mb-4 text-accent-primary">{{ 'contract.queries' | i18n }}</h3>
            @if (contractIR?.queries?.length) {
              <div class="space-y-2">
                @for (query of contractIR?.queries; track query.name) {
                  <div class="p-2 bg-bg-secondary rounded">
                    <div class="font-medium text-sm">{{ query.name }}</div>
                  </div>
                }
              </div>
            } @else {
              <p class="text-sm text-text-tertiary">{{ 'contract.noQueries' | i18n }}</p>
            }
          </div>

          <!-- Events -->
          <div class="card">
            <h3 class="font-semibold mb-4 text-accent-primary">{{ 'contract.events' | i18n }}</h3>
            @if (contractIR?.events?.length) {
              <div class="space-y-2">
                @for (event of contractIR?.events; track event.name) {
                  <div class="p-2 bg-bg-secondary rounded">
                    <div class="font-medium text-sm">{{ event.name }}</div>
                  </div>
                }
              </div>
            } @else {
              <p class="text-sm text-text-tertiary">{{ 'contract.noEvents' | i18n }}</p>
            }
          </div>

          <!-- Workflows -->
          <div class="card">
            <h3 class="font-semibold mb-4 text-accent-primary">{{ 'contract.workflows' | i18n }}</h3>
            @if (contractIR?.workflows?.length) {
              <div class="space-y-2">
                @for (workflow of contractIR?.workflows; track workflow.name) {
                  <div class="p-2 bg-bg-secondary rounded">
                    <div class="font-medium text-sm">{{ workflow.name }}</div>
                  </div>
                }
              </div>
            } @else {
              <p class="text-sm text-text-tertiary">{{ 'contract.noWorkflows' | i18n }}</p>
            }
          </div>

          <!-- Raw JSON -->
          <div class="card">
            <h3 class="font-semibold mb-4 text-accent-primary">{{ 'contract.rawJson' | i18n }}</h3>
            <pre class="text-xs text-text-secondary overflow-auto max-h-64">{{ contractIR | json }}</pre>
          </div>
        </div>
      }

      <!-- Next Action -->
      <div class="mt-6 flex justify-end">
        <a routerLink="/ir-explorer" class="btn btn-primary">
          {{ 'contract.toIR' | i18n }}
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
export class ContractViewerComponent implements OnInit, OnDestroy {
  private readonly api = inject(ApiService);
  private readonly i18n = inject(I18nService);
  private readonly versionService = inject(VersionService);

  readonly docsUrl = `${DOCS_BASE}/contract`;

  contractIR: any = null;
  contractSummary: any = null;
  isGenerating = false;
  isValidating = false;
  successMessage = '';

  async ngOnInit(): Promise<void> {
    await this.loadContractIR();

    // Reload khi version switch
    window.addEventListener('version-switched', this.onVersionSwitched);
  }

  ngOnDestroy(): void {
    window.removeEventListener('version-switched', this.onVersionSwitched);
  }

  /** Reload toàn bộ data khi version switch */
  private onVersionSwitched = async (event: any) => {
    try {
      await this.loadContractIR();
    } finally {
      this.versionService.stopLoading();
    }
  };

  async loadContractIR(): Promise<void> {
    const result = await this.api.getContractIR();
    if (result.success && result.data) {
      this.contractIR = result.data;
    }
  }

  async handleGenerate(): Promise<void> {
    this.isGenerating = true;
    this.successMessage = '';

    const result = await this.api.generateContract({ version: 'v1.0.0' });

    if (result.success && result.data) {
      this.contractSummary = result.data.summary;
      this.successMessage = this.i18n.t('contract.genSuccess');
      await this.loadContractIR();
    }

    this.isGenerating = false;
  }

  async handleValidate(): Promise<void> {
    this.isValidating = true;

    await this.api.checkContract({ version: 'v1.0.0', auto_fix: true });

    this.isValidating = false;
    this.successMessage = this.i18n.t('contract.validateSuccess');
  }
}