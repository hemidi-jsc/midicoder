/**
 * Component Code Generator
 * Xem và quản lý code đã tạo
 */

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { MockApiService } from '../../core/mock-api.service';

@Component({
  selector: 'app-code-generator',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="container mx-auto px-6 py-8">
      <!-- Header -->
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold">Trình tạo mã</h1>
          <p class="text-text-secondary mt-1">Quản lý code đã tạo</p>
        </div>
        <div class="flex space-x-3">
          <button (click)="handlePlan()" class="btn btn-secondary" [disabled]="isProcessing">
            Kế hoạch
          </button>
          <button (click)="handleGenerate()" class="btn btn-secondary" [disabled]="isProcessing">
            Tạo mã
          </button>
          <button (click)="handleApply()" class="btn btn-primary" [disabled]="isProcessing">
            Áp dụng
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
        <h3 class="font-semibold mb-3">Mục tiêu</h3>
        <div class="flex space-x-4">
          <label class="flex items-center space-x-2">
            <input type="radio" name="target" value="all" [(ngModel)]="selectedTarget" class="w-4 h-4" />
            <span>Both Backend & Frontend</span>
          </label>
          <label class="flex items-center space-x-2">
            <input type="radio" name="target" value="backend" [(ngModel)]="selectedTarget" class="w-4 h-4" />
            <span>Backend</span>
          </label>
          <label class="flex items-center space-x-2">
            <input type="radio" name="target" value="frontend" [(ngModel)]="selectedTarget" class="w-4 h-4" />
            <span>Frontend</span>
          </label>
        </div>
      </div>

      <!-- Generated Files -->
      @if (codeFiles.length) {
        <div class="card mb-6">
          <h2 class="font-semibold mb-4">Generated Files ({{ codeFiles.length }})</h2>
          
          <div class="space-y-2 max-h-96 overflow-auto">
            @for (file of codeFiles; track file.path) {
              <div class="flex items-center justify-between p-3 bg-bg-secondary rounded hover:bg-bg-tertiary transition-colors">
                <div class="flex items-center space-x-3">
                  <span class="text-text-tertiary">{{ file.type }}</span>
                  <span class="text-text-primary font-mono text-sm">{{ file.path }}</span>
                </div>
                <span class="text-text-tertiary text-sm">{{ file.lines }} dòng</span>
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
            <div class="text-sm text-text-tertiary">Tệp tin</div>
          </div>
          <div class="card text-center">
            <div class="text-2xl font-bold text-accent-primary">{{ codeSummary?.total_lines }}</div>
            <div class="text-sm text-text-tertiary">Dòng</div>
          </div>
          <div class="card text-center">
            <div class="text-2xl font-bold text-accent-primary">{{ codeSummary?.templates_used }}</div>
            <div class="text-sm text-text-tertiary">Templates</div>
          </div>
        </div>
      }

      <!-- Next Action -->
      <div class="mt-6 flex justify-end">
        <a routerLink="/preview" class="btn btn-primary">
          Xem trước →
        </a>
      </div>
    </div>
  `,
  styles: [],
})
export class CodeGeneratorComponent implements OnInit {
  selectedTarget: 'backend' | 'frontend' | 'all' = 'all';
  codeFiles: any[] = [];
  codeSummary: any = null;
  isProcessing = false;
  successMessage = '';

  constructor(private mockApi: MockApiService) {}

  async ngOnInit(): Promise<void> {
    await this.loadCodeFiles();
  }

  async loadCodeFiles(): Promise<void> {
    const result = await this.mockApi.getCodeFiles();
    if (result.success && result.data) {
      this.codeFiles = result.data;
    }
  }

  async handlePlan(): Promise<void> {
    this.isProcessing = true;
    this.successMessage = '';

    await this.mockApi.planCode({ version: 'v1.0.0', target: this.selectedTarget });
    
    this.successMessage = 'Tạo kế hoạch thành công';
    this.isProcessing = false;
  }

  async handleGenerate(): Promise<void> {
    this.isProcessing = true;
    this.successMessage = '';

    const result = await this.mockApi.generateCode({ version: 'v1.0.0', target: this.selectedTarget });
    
    if (result.success && result.data) {
      this.codeSummary = result.data.summary;
    }
    
    await this.loadCodeFiles();
    
    this.successMessage = 'Tạo mã thành công';
    this.isProcessing = false;
  }

  async handleApply(): Promise<void> {
    this.isProcessing = true;
    this.successMessage = '';

    await this.mockApi.applyCode({ version: 'v1.0.0', target_dir: './src', backup: true });
    
    this.successMessage = 'Áp dụng mã thành công';
    this.isProcessing = false;
  }
}