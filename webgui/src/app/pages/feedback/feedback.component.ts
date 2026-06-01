/**
 * Component Feedback
 * Cho phép người dùng gửi feedback
 */

import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';

@Component({
  selector: 'app-feedback',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="container mx-auto px-6 py-8">
      <!-- Header -->
      <div class="mb-6">
        <h1 class="text-2xl font-bold">Phản hồi</h1>
        <p class="text-text-secondary mt-1">Gửi phản hồi để cải thiện project</p>
      </div>

      <!-- Success Message -->
      @if (successMessage) {
        <div class="mb-4 p-3 bg-accent-success bg-opacity-10 border border-accent-success rounded text-accent-success">
          ✓ {{ successMessage }}
          @if (isPipelineTriggered) {
            <br/>
            <span class="text-sm">Pipeline đã được kích hoạt</span>
          }
        </div>
      }

      <!-- Feedback Form -->
      <div class="card max-w-2xl">
        <form (ngSubmit)="handleSubmit()" class="space-y-4">
          <!-- Feedback Type -->
          <div>
            <label class="block text-text-secondary mb-2">Loại</label>
            <select [(ngModel)]="feedbackType" name="type" class="input" required>
              <option value="" disabled>Chọn loại</option>
              <option value="bug">Lỗi</option>
              <option value="enhancement">Cải tiến</option>
              <option value="clarification">Làm rõ</option>
            </select>
          </div>

          <!-- Feedback Text -->
          <div>
            <label class="block text-text-secondary mb-2">Nội dung phản hồi</label>
            <textarea
              [(ngModel)]="feedbackText"
              name="feedback"
              class="input h-40 resize-none"
              placeholder="Mô tả chi tiết phản hồi của bạn..."
              required
            ></textarea>
          </div>

          <!-- Auto-apply Checkbox -->
          <div class="flex items-center space-x-2">
            <input
              type="checkbox"
              [(ngModel)]="autoApply"
              name="autoApply"
              id="autoApply"
              class="w-4 h-4"
            />
            <label for="autoApply" class="text-text-secondary">Tự động kích hoạt pipeline</label>
          </div>

          <!-- Submit Button -->
          <div class="flex justify-end">
            <button
              type="submit"
              class="btn btn-primary"
              [disabled]="isSubmitting"
            >
              {{ isSubmitting ? 'Đang tải...' : 'Gửi phản hồi' }}
            </button>
          </div>
        </form>
      </div>

      <!-- Pipeline Progress (if triggered) -->
      @if (pipelineProgress) {
        <div class="card mt-6">
          <h2 class="font-semibold mb-4">Pipeline Progress</h2>
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-text-secondary">Contract Generation</span>
              <span class="text-sm" [ngClass]="getProgressClass(pipelineProgress?.contract_gen)">
                {{ pipelineProgress?.contract_gen }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-text-secondary">Contract Validation</span>
              <span class="text-sm" [ngClass]="getProgressClass(pipelineProgress?.contract_check)">
                {{ pipelineProgress?.contract_check }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-text-secondary">IR Build</span>
              <span class="text-sm" [ngClass]="getProgressClass(pipelineProgress?.ir_build)">
                {{ pipelineProgress?.ir_build }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-text-secondary">Code Plan</span>
              <span class="text-sm" [ngClass]="getProgressClass(pipelineProgress?.code_plan)">
                {{ pipelineProgress?.code_plan }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-text-secondary">Code Generation</span>
              <span class="text-sm" [ngClass]="getProgressClass(pipelineProgress?.code_gen)">
                {{ pipelineProgress?.code_gen }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-text-secondary">Code Apply</span>
              <span class="text-sm" [ngClass]="getProgressClass(pipelineProgress?.code_apply)">
                {{ pipelineProgress?.code_apply }}
              </span>
            </div>
          </div>
        </div>
      }

      <!-- Back Button -->
      <div class="mt-6 flex justify-start">
        <a routerLink="/dashboard" class="btn btn-secondary">
          Quay lại Dashboard
        </a>
      </div>
    </div>
  `,
  styles: [],
})
export class FeedbackComponent {
  private api = inject(ApiService);

  feedbackType: 'bug' | 'enhancement' | 'clarification' = 'bug';
  feedbackText = '';
  autoApply = true;
  isSubmitting = false;
  successMessage = '';
  isPipelineTriggered = false;
  pipelineProgress: any = null;

  async handleSubmit(): Promise<void> {
    if (!this.feedbackText.trim()) {
      return;
    }

    this.isSubmitting = true;
    this.successMessage = '';

    const result = await this.api.submitFeedback({
      version: 'v1.0.0',
      type: this.feedbackType,
      feedback: this.feedbackText,
      auto_apply: this.autoApply,
    });

    if (result.success && result.data) {
      this.successMessage = 'Gửi phản hồi thành công';
      this.isPipelineTriggered = result.data.pipeline_triggered;
      this.pipelineProgress = result.data.pipeline_progress;

      // Reset form
      this.feedbackText = '';
    }

    this.isSubmitting = false;
  }

  getProgressClass(status: string): string {
    switch (status) {
      case 'complete':
        return 'text-accent-success';
      case 'in_progress':
        return 'text-accent-primary animate-pulse';
      case 'error':
        return 'text-accent-error';
      default:
        return 'text-text-tertiary';
    }
  }
}