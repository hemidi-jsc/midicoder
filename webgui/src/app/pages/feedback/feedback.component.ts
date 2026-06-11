/**
 * Component Feedback
 * Cho phép người dùng gửi feedback
 */

import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { I18nPipe } from '../../core/i18n.pipe';
import { I18nService } from '../../core/i18n.service';
import { DOCS_BASE } from '../../core/app.constants';

@Component({
  selector: 'app-feedback',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, I18nPipe],
  template: `
    <div class="py-8">
      <!-- Header -->
      <div class="mb-6">
        <div class="page-header-row">
          <h1 class="text-2xl font-bold">{{ 'feedback.title' | i18n }}</h1>
          <a href="{{ docsUrl }}" target="_blank" rel="noopener" class="docs-link">{{ 'common.readGuide' | i18n }}</a>
        </div>
        <p class="text-text-secondary mt-1">{{ 'feedback.subtitle' | i18n }}</p>
      </div>

      <!-- Success Message -->
      @if (successMessage) {
        <div class="mb-4 p-3 bg-accent-success bg-opacity-10 border border-accent-success rounded text-accent-success">
          ✓ {{ successMessage }}
          @if (isPipelineTriggered) {
            <br/>
            <span class="text-sm">{{ 'feedback.pipelineTriggered' | i18n }}</span>
          }
        </div>
      }

      <!-- Feedback Form -->
      <div class="card max-w-2xl">
        <form (ngSubmit)="handleSubmit()" class="space-y-4">
          <!-- Feedback Type -->
          <div>
            <label class="block text-text-secondary mb-2">{{ 'feedback.type' | i18n }}</label>
            <select [(ngModel)]="feedbackType" name="type" class="input" required>
              <option value="" disabled>{{ 'feedback.selectType' | i18n }}</option>
              <option value="bug">{{ 'feedback.bug' | i18n }}</option>
              <option value="enhancement">{{ 'feedback.enhancement' | i18n }}</option>
              <option value="clarification">{{ 'feedback.clarification' | i18n }}</option>
            </select>
          </div>

          <!-- Feedback Text -->
          <div>
            <label class="block text-text-secondary mb-2">{{ 'feedback.content' | i18n }}</label>
            <textarea
              [(ngModel)]="feedbackText"
              name="feedback"
              class="input h-40 resize-none"
              [placeholder]="'feedback.contentPlaceholder' | i18n"
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
            <label for="autoApply" class="text-text-secondary">{{ 'feedback.autoPipeline' | i18n }}</label>
          </div>

          <!-- Submit Button -->
          <div class="flex justify-end">
            <button
              type="submit"
              class="btn btn-primary"
              [disabled]="isSubmitting"
            >
              {{ isSubmitting ? ('common.loading' | i18n) : ('feedback.submit' | i18n) }}
            </button>
          </div>
        </form>
      </div>

      <!-- Pipeline Progress (if triggered) -->
      @if (pipelineProgress) {
        <div class="card mt-6">
          <h2 class="font-semibold mb-4">{{ 'feedback.pipelineProgress' | i18n }}</h2>
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-text-secondary">{{ 'feedback.pipelineContractGen' | i18n }}</span>
              <span class="text-sm" [ngClass]="getProgressClass(pipelineProgress?.contract_gen)">
                {{ pipelineProgress?.contract_gen }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-text-secondary">{{ 'feedback.pipelineContractCheck' | i18n }}</span>
              <span class="text-sm" [ngClass]="getProgressClass(pipelineProgress?.contract_check)">
                {{ pipelineProgress?.contract_check }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-text-secondary">{{ 'feedback.pipelineIrBuild' | i18n }}</span>
              <span class="text-sm" [ngClass]="getProgressClass(pipelineProgress?.ir_build)">
                {{ pipelineProgress?.ir_build }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-text-secondary">{{ 'feedback.pipelineCodePlan' | i18n }}</span>
              <span class="text-sm" [ngClass]="getProgressClass(pipelineProgress?.code_plan)">
                {{ pipelineProgress?.code_plan }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-text-secondary">{{ 'feedback.pipelineCodeGen' | i18n }}</span>
              <span class="text-sm" [ngClass]="getProgressClass(pipelineProgress?.code_gen)">
                {{ pipelineProgress?.code_gen }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-text-secondary">{{ 'feedback.pipelineCodeApply' | i18n }}</span>
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
          {{ 'feedback.backDashboard' | i18n }}
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
export class FeedbackComponent {
  private api = inject(ApiService);
  private i18n = inject(I18nService);

  readonly docsUrl = `${DOCS_BASE}/feedback`;

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
      this.successMessage = this.i18n.t('feedback.submitSuccess');
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