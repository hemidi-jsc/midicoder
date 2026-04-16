/**
 * Component Brief Editor
 * Cho phép viết và phân tích brief
 */

import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, Router } from '@angular/router';

import { MockApiService } from '../../core/mock-api.service';

@Component({
  selector: 'app-brief-editor',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="container mx-auto px-6 py-8">
      <!-- Header -->
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold">Brief Editor</h1>
          <p class="text-text-secondary mt-1">Viết brief cho project của bạn</p>
        </div>
        <div class="flex space-x-3">
          <button (click)="handleAnalyze()" class="btn btn-primary" [disabled]="isAnalyzing">
            {{ isAnalyzing ? 'Đang tải...' : 'Phân tích' }}
          </button>
          <button (click)="handleSave()" class="btn btn-secondary" [disabled]="isSaving">
            {{ isSaving ? 'Đang tải...' : 'Lưu brief' }}
          </button>
        </div>
      </div>

      <!-- Success Message -->
      @if (successMessage) {
        <div class="mb-4 p-3 bg-accent-success bg-opacity-10 border border-accent-success rounded text-accent-success">
          {{ successMessage }}
        </div>
      }

      <!-- Error Message -->
      @if (errorMessage) {
        <div class="mb-4 p-3 bg-accent-error bg-opacity-10 border border-accent-error rounded text-accent-error">
          {{ errorMessage }}
        </div>
      }

      <!-- Editor -->
      <div class="card">
        <textarea
          [(ngModel)]="briefContent"
          class="w-full h-96 bg-bg-secondary border border-border-primary rounded p-4 text-text-primary font-mono text-sm resize-none focus:outline-none focus:border-accent-primary"
          placeholder="Viết brief của bạn ở đây..."
        ></textarea>
      </div>

      <!-- Analysis Result -->
      @if (analysisResult) {
        <div class="card mt-6">
          <h2 class="text-lg font-semibold mb-4">Kết quả phân tích</h2>
          
          <!-- Intent -->
          <div class="mb-4">
            <h3 class="font-medium text-accent-primary mb-2">Intent</h3>
            <div class="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span class="text-text-tertiary">Domain:</span>
                <span class="ml-2">{{ analysisResult?.analysis.intent.domain }}</span>
              </div>
              <div>
                <span class="text-text-tertiary">Type:</span>
                <span class="ml-2">{{ analysisResult?.analysis.intent.type }}</span>
              </div>
              <div>
                <span class="text-text-tertiary">Scale:</span>
                <span class="ml-2">{{ analysisResult?.analysis.intent.scale }}</span>
              </div>
            </div>
          </div>

          <!-- Ambiguities -->
          @if (analysisResult?.analysis.ambiguities?.length) {
            <div>
              <h3 class="font-medium text-accent-warning mb-2">Ambiguities ({{ analysisResult?.analysis.ambiguities?.length }})</h3>
              <div class="space-y-2">
                @for (ambiguity of analysisResult?.analysis.ambiguities; track ambiguity.id) {
                  <div class="p-3 bg-bg-secondary rounded border-l-2 border-accent-warning">
                    <p class="text-sm text-text-primary"><strong>{{ ambiguity.type }}:</strong> {{ ambiguity.description }}</p>
                    <p class="text-sm text-text-tertiary mt-1">{{ ambiguity.source_text }}</p>
                  </div>
                }
              </div>
            </div>
          }

          <!-- Next Action -->
          @if (analysisResult?.status === 'needs_clarification') {
            <div class="mt-4 flex justify-end">
              <a routerLink="/clarification" class="btn btn-primary">
                Làm rõ yêu cầu →
              </a>
            </div>
          }
        </div>
      }
    </div>
  `,
  styles: [],
})
export class BriefEditorComponent {
  briefContent = '';
  isAnalyzing = false;
  isSaving = false;
  successMessage = '';
  errorMessage = '';
  analysisResult: any = null;

  constructor(
    private mockApi: MockApiService,
    private router: Router,
  ) {}

  async handleAnalyze(): Promise<void> {
    if (!this.briefContent.trim()) {
      this.errorMessage = 'Vui lòng nhập brief';
      return;
    }

    this.isAnalyzing = true;
    this.successMessage = '';
    this.errorMessage = '';

    try {
      const result = await this.mockApi.analyzeBrief({
        brief_content: this.briefContent,
        version: 'v1.0.0',
      });

      if (result.success && result.data) {
        this.analysisResult = result.data;
        this.successMessage = 'Phân tích thành công';
      } else {
        this.errorMessage = result.error?.message || 'Phân tích thất bại';
      }
    } finally {
      this.isAnalyzing = false;
    }
  }

  async handleSave(): Promise<void> {
    if (!this.briefContent.trim()) {
      this.errorMessage = 'Vui lòng nhập brief';
      return;
    }

    this.isSaving = true;
    this.successMessage = '';
    this.errorMessage = '';

    try {
      const result = await this.mockApi.saveBrief({
        name: 'my-brief',
        tags: ['draft'],
        version: 'v1.0.0',
      });

      if (result.success) {
        this.successMessage = 'Lưu brief thành công';
      } else {
        this.errorMessage = result.error?.message || 'Lưu thất bại';
      }
    } finally {
      this.isSaving = false;
    }
  }
}