/**
 * Component Clarification
 * Q&A interface cho clarification flow
 */

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, Router } from '@angular/router';

import { MockApiService } from '../../core/mock-api.service';

@Component({
  selector: 'app-clarification',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="container mx-auto px-6 py-8">
      <!-- Header -->
      <div class="mb-6">
        <h1 class="text-2xl font-bold">Làm rõ yêu cầu</h1>
        <p class="text-text-secondary mt-1">Vòng {{ round }} of {{ totalRounds }}</p>
        <div class="mt-2 h-2 bg-bg-secondary rounded-full overflow-hidden">
          <div class="h-full bg-accent-primary transition-all" [style.width.%]="progress"></div>
        </div>
      </div>

      @if (!questions.length) {
        <!-- Complete State -->
        <div class="card text-center py-12">
          <div class="text-4xl mb-4">✓</div>
          <h2 class="text-xl font-semibold text-accent-success mb-2">Hoàn thành</h2>
          <p class="text-text-secondary mb-6">Tất cả câu hỏi đã được trả lời</p>
          <a routerLink="/contract-viewer" class="btn btn-primary">Tiếp tục →</a>
        </div>
      } @else {
        <!-- Questions -->
        <div class="space-y-6">
          @for (question of questions; track question.id; let i = $index) {
            <div class="card">
              <div class="flex items-start justify-between mb-4">
                <span class="text-sm text-text-tertiary">Câu hỏi {{ i + 1 }} của {{ questions.length }}</span>
                @if (question.required) {
                  <span class="text-xs bg-accent-warning bg-opacity-20 text-accent-warning px-2 py-1 rounded">Required</span>
                }
              </div>

              <h3 class="font-medium text-lg mb-2">{{ question.question }}</h3>
              <p class="text-sm text-text-tertiary mb-4">Source: "{{ question.source_text }}"</p>

              <!-- Single Select -->
              @if (question.type === 'single_select') {
                <div class="space-y-2">
                  @for (option of question.options; track option.value) {
                    <label class="flex items-center space-x-3 p-3 bg-bg-secondary rounded cursor-pointer hover:bg-bg-tertiary transition-colors">
                      <input
                        type="radio"
                        [name]="'q_' + question.id"
                        [value]="option.value"
                        [(ngModel)]="answers[question.id]"
                        class="w-4 h-4"
                      />
                      <span>{{ option.label }}</span>
                    </label>
                  }
                </div>
              }

              <!-- Multi Select -->
              @if (question.type === 'multi_select') {
                <div class="space-y-2">
                  @for (option of question.options; track option.value) {
                    <label class="flex items-center space-x-3 p-3 bg-bg-secondary rounded cursor-pointer hover:bg-bg-tertiary transition-colors">
                      <input
                        type="checkbox"
                        [value]="option.value"
                        (change)="toggleAnswer(question.id, option.value)"
                        class="w-4 h-4"
                      />
                      <span>{{ option.label }}</span>
                    </label>
                  }
                </div>
              }

              <!-- Notes -->
              <div class="mt-4">
                <textarea
                  [(ngModel)]="notes[question.id]"
                  class="input h-20 resize-none"
                  placeholder="Ghi chú (tùy chọn)..."
                ></textarea>
              </div>
            </div>
          }
        </div>

        <!-- Submit Button -->
        <div class="mt-6 flex justify-end">
          <button (click)="handleSubmit()" class="btn btn-primary" [disabled]="isSubmitting">
            {{ isSubmitting ? 'Đang tải...' : 'Gửi câu trả lời' }}
          </button>
        </div>
      }
    </div>
  `,
  styles: [],
})
export class ClarificationComponent implements OnInit {
  questions: any[] = [];
  answers: Record<string, string | string[]> = {};
  notes: Record<string, string> = {};
  round = 1;
  totalRounds = 3;
  progress = 33;
  isSubmitting = false;

  constructor(
    private mockApi: MockApiService,
    private router: Router,
  ) {}

  async ngOnInit(): Promise<void> {
    // Load questions from mock
    const result = await this.mockApi.startClarification({ version: 'v1.0.0' });
    if (result.success && result.data && result.data.questions) {
      this.questions = result.data.questions;
    }
  }

  toggleAnswer(questionId: string, value: string): void {
    if (!this.answers[questionId]) {
      this.answers[questionId] = [];
    }
    const arr = this.answers[questionId] as string[];
    const index = arr.indexOf(value);
    if (index > -1) {
      arr.splice(index, 1);
    } else {
      arr.push(value);
    }
  }

  async handleSubmit(): Promise<void> {
    this.isSubmitting = true;

    // Mock: submit và chuyển đến contract viewer
    setTimeout(() => {
      this.isSubmitting = false;
      this.router.navigate(['/contract-viewer']);
    }, 1000);
  }
}