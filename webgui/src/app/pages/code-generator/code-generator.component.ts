/**
 * Component Code Generator
 * Xem và quản lý code đã tạo
 */

import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { I18nPipe } from '../../core/i18n.pipe';
import { I18nService } from '../../core/i18n.service';
import { CodeFile } from '../../core/api.types';

@Component({
  selector: 'app-code-generator',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, I18nPipe],
  template: `
    <div class="container mx-auto px-6 py-8">
      <!-- Header -->
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold">{{ 'code.title' | i18n }}</h1>
          <p class="text-text-secondary mt-1">{{ 'code.subtitle' | i18n }}</p>
        </div>
        <div class="flex space-x-3">
          <button (click)="handlePlan()" class="btn btn-secondary" [disabled]="isProcessing">
            {{ 'code.plan' | i18n }}
          </button>
          <button (click)="handleGenerate()" class="btn btn-secondary" [disabled]="isProcessing">
            {{ 'code.generate' | i18n }}
          </button>
          <button (click)="handleApply()" class="btn btn-primary" [disabled]="isProcessing">
            {{ 'code.apply' | i18n }}
          </button>
        </div>
      </div>

      <!-- Success Message -->
      @if (successMessage) {
        <div class="mb-4 p-3 bg-accent-success bg-opacity-10 border border-accent-success rounded text-accent-success">
          {{ successMessage }}
        </div>
      }

      <!-- Target Selection -->
      <div class="card mb-6">
        <h3 class="font-semibold mb-3">{{ 'code.target' | i18n }}</h3>
        <div class="flex space-x-4">
          <label class="flex items-center space-x-2">
            <input type="radio" name="target" value="all" [(ngModel)]="selectedTarget" class="w-4 h-4" />
            <span>{{ 'code.both' | i18n }}</span>
          </label>
          <label class="flex items-center space-x-2">
            <input type="radio" name="target" value="backend" [(ngModel)]="selectedTarget" class="w-4 h-4" />
            <span>{{ 'code.backend' | i18n }}</span>
          </label>
          <label class="flex items-center space-x-2">
            <input type="radio" name="target" value="frontend" [(ngModel)]="selectedTarget" class="w-4 h-4" />
            <span>{{ 'code.frontend' | i18n }}</span>
          </label>
        </div>
      </div>

      <!-- Generated Files -->
      @if (codeFiles.length) {
        <div class="card mb-6">
          <h2 class="font-semibold mb-4">{{ 'code.generatedFiles' | i18n }} ({{ codeFiles.length }})</h2>

          <div class="space-y-2 max-h-96 overflow-auto">
            @for (file of codeFiles; track file.path) {
              <div class="flex items-center justify-between p-3 bg-bg-secondary rounded hover:bg-bg-tertiary transition-colors">
                <div class="flex items-center space-x-3">
                  <span class="text-text-tertiary">{{ file.type }}</span>
                  <span class="text-text-primary font-mono text-sm">{{ file.path }}</span>
                </div>
                <span class="text-text-tertiary text-sm">{{ file.lines }} {{ 'code.linesSuffix' | i18n }}</span>
              </div>
            }
          </div>
        </div>
      }

      <!-- Summary Stats -->
      @if (codeSummary) {
        <div class="grid grid-cols-3 gap-4 mb-6">
          <div class="card text-center">
            <div class="text-2xl font-bold text-accent-primary">{{ codeSummary?.total_files }}</div>
            <div class="text-sm text-text-tertiary">{{ 'code.filesLabel' | i18n }}</div>
          </div>
          <div class="card text-center">
            <div class="text-2xl font-bold text-accent-primary">{{ codeSummary?.total_lines }}</div>
            <div class="text-sm text-text-tertiary">{{ 'code.linesLabel' | i18n }}</div>
          </div>
          <div class="card text-center">
            <div class="text-2xl font-bold text-accent-primary">{{ codeSummary?.templates_used }}</div>
            <div class="text-sm text-text-tertiary">{{ 'code.templatesLabel' | i18n }}</div>
          </div>
        </div>
      }

      <!-- Next Action -->
      <div class="mt-6 flex justify-end">
        <a routerLink="/preview" class="btn btn-primary">
          {{ 'code.preview' | i18n }}
        </a>
      </div>
    </div>
  `,
  styles: [],
})
export class CodeGeneratorComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly i18n = inject(I18nService);

  selectedTarget: 'backend' | 'frontend' | 'all' = 'all';
  codeFiles: CodeFile[] = [];
  codeSummary: any = null;
  isProcessing = false;
  successMessage = '';

  async ngOnInit(): Promise<void> {
    await this.loadCodeFiles();
  }

  async loadCodeFiles(): Promise<void> {
    const result = await this.api.getCodeFiles();
    if (result.success && result.data) {
      // Backend trả về { files: [...], count: N }
      this.codeFiles = result.data.files || result.data;
    }
  }

  async handlePlan(): Promise<void> {
    this.isProcessing = true;
    this.successMessage = '';

    await this.api.buildCodePlan();

    this.successMessage = this.i18n.t('code.planSuccess');
    this.isProcessing = false;
  }

  async handleGenerate(): Promise<void> {
    this.isProcessing = true;
    this.successMessage = '';

    const result = await this.api.generateCode({ runtime: false });

    if (result.success && result.data) {
      this.codeSummary = result.data.summary;
    }

    await this.loadCodeFiles();

    this.successMessage = this.i18n.t('code.genSuccess');
    this.isProcessing = false;
  }

  async handleApply(): Promise<void> {
    this.isProcessing = true;
    this.successMessage = '';

    await this.api.applyCode({ force: false, dry_run: false });

    this.successMessage = this.i18n.t('code.applySuccess');
    this.isProcessing = false;
  }
}