/**
 * Component Clarification
 * Q&A interface cho clarification flow — gọi real backend API
 */

import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, Router } from '@angular/router';

import { ApiService } from '../../core/api.service';

@Component({
  selector: 'app-clarification',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="container mx-auto px-6 py-8">
      <!-- Header -->
      <div class="mb-6">
        <h1 class="text-2xl font-bold">Làm rõ yêu cầu</h1>
        <p class="text-text-secondary mt-1">Vòng {{ round }}</p>
        @if (maxRounds > 0) {
          <div class="mt-2 h-2 bg-bg-secondary rounded-full overflow-hidden">
            <div class="h-full bg-accent-primary transition-all" [style.width.%]="(round / maxRounds * 100)"></div>
          </div>
        }
      </div>

      <!-- Error -->
      @if (errorMessage) {
        <div class="mb-4 p-3 bg-accent-error bg-opacity-15 border border-accent-error rounded text-accent-error font-medium">
          {{ errorMessage }}
        </div>
      }

      @if (isLoading) {
        <!-- Loading State -->
        <div class="card text-center py-12">
          <svg class="animate-spin h-10 w-10 mx-auto text-accent-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p class="text-text-secondary mt-4">Đang tải câu hỏi...</p>
        </div>
      } @else if (isComplete) {
        <!-- Complete State -->
        <div class="card text-center py-12">
          <div class="text-4xl mb-4">✓</div>
          <h2 class="text-xl font-semibold text-accent-success mb-2">Hoàn thành</h2>
          <p class="text-text-secondary mb-6">Tất cả câu hỏi đã được trả lời sau {{ round }} rounds</p>
          <div class="flex justify-center space-x-3">
            <a routerLink="/brief-editor" class="btn btn-secondary">Quay lại Brief</a>
            <a routerLink="/contract-viewer" class="btn btn-primary">Tiếp tục →</a>
          </div>
        </div>
      } @else if (!questions.length) {
        <!-- No Questions -->
        <div class="card text-center py-12">
          <div class="text-4xl mb-4">📋</div>
          <h2 class="text-xl font-semibold mb-2">Không có câu hỏi</h2>
          <p class="text-text-secondary mb-6">Brief đã đủ rõ, không cần clarify thêm</p>
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
              @if (question.source_text) {
                <p class="text-sm text-text-tertiary mb-4">Source: "{{ question.source_text }}"</p>
              }

              <!-- Single Select -->
              @if (question.type === 'single_select') {
                <div class="space-y-2">
                  @for (option of question.options; track option.value) {
                    <label class="flex items-center space-x-3 p-3 bg-bg-secondary rounded cursor-pointer hover:bg-bg-tertiary transition-colors">
                      <input
                        type="radio"
                        [name]="'q_' + question.id"
                        [value]="option.value"
                        (change)="setAnswer(question.id, option.value)"
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

              <!-- Text Input -->
              @if (question.type === 'text') {
                <textarea
                  [(ngModel)]="textAnswers[question.id]"
                  class="input h-24 resize-none"
                  placeholder="Nhập câu trả lời của bạn..."
                ></textarea>
              }

              <!-- Notes -->
              <div class="mt-4">
                <textarea
                  [(ngModel)]="notes[question.id]"
                  class="input h-20 resize-none"
                  placeholder="Ghi chú bổ sung (tùy chọn)..."
                ></textarea>
              </div>
            </div>
          }
        </div>

        <!-- Submit Button -->
        <div class="mt-6 flex justify-end">
          <button (click)="handleSubmit()" class="btn btn-primary" [disabled]="isSubmitting">
            {{ isSubmitting ? 'Đang gửi...' : 'Gửi câu trả lời' }}
          </button>
        </div>
      }
    </div>
  `,
  styles: [],
})
export class ClarificationComponent implements OnInit {
  private api = inject(ApiService);
  private router = inject(Router);

  sessionId: string | null = null;
  questions: any[] = [];
  textAnswers: Record<string, string> = {};
  answers: Record<string, string | string[]> = {};
  notes: Record<string, string> = {};
  round = 1;
  maxRounds = 10;
  isLoading = true;
  isSubmitting = false;
  isComplete = false;
  errorMessage = '';

  async ngOnInit(): Promise<void> {
    await this.startSession();
  }

  async startSession(): Promise<void> {
    this.isLoading = true;
    this.errorMessage = '';

    try {
      const result = await this.api.startClarification({ version: 'v1.0.0' });

      if (!result.success) {
        this.errorMessage = result.error?.message || 'Không thể bắt đầu clarification session';
        this.isLoading = false;
        return;
      }

      const data = result.data;

      if (!data) {
        this.errorMessage = 'Phản hồi từ server không hợp lệ';
        this.isLoading = false;
        return;
      }

      if (data.status === 'ready') {
        // Brief đã đủ rõ, không cần clarify
        this.isComplete = true;
        this.questions = [];
      } else if (data.status === 'questions_ready') {
        this.sessionId = data.clarification_id;
        this.questions = data.questions || [];
        this.round = data.round || 1;
      }
    } catch (e) {
      this.errorMessage = 'Lỗi kết nối server';
    } finally {
      this.isLoading = false;
    }
  }

  setAnswer(questionId: string, value: string): void {
    this.answers[questionId] = value;
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
    if (!this.sessionId) {
      this.errorMessage = 'Session không hợp lệ';
      return;
    }

    this.isSubmitting = true;
    this.errorMessage = '';

    try {
      // Build answers array for backend
      const answersArray = this.questions.map(q => ({
        question_id: q.id,
        values: Array.isArray(this.answers[q.id])
          ? this.answers[q.id] as string[]
          : (this.answers[q.id] ? [this.answers[q.id] as string] : []),
        notes: this.notes[q.id] || '',
        // Add text answer if this is a text type question
        ...(q.type === 'text' && this.textAnswers[q.id]
          ? { values: [this.textAnswers[q.id]], notes: this.notes[q.id] || '' }
          : {}),
      }));

      const result = await this.api.submitClarificationAnswers({
        session_id: this.sessionId,
        answers: answersArray,
      });

      if (!result.success) {
        this.errorMessage = result.error?.message || 'Gửi thất bại';
        return;
      }

      const data = result.data;

      if (!data) {
        this.errorMessage = 'Phản hồi từ server không hợp lệ';
        this.isSubmitting = false;
        return;
      }

      if (data.status === 'ready') {
        // Hoàn thành clarification
        this.isComplete = true;
        this.questions = [];
      } else if (data.status === 'more_questions') {
        // Còn câu hỏi tiếp theo
        this.questions = data.questions || [];
        this.round = data.round || this.round + 1;
        this.answers = {};
        this.textAnswers = {};
        this.notes = {};
      }
    } catch (e) {
      this.errorMessage = 'Lỗi kết nối server';
    } finally {
      this.isSubmitting = false;
    }
  }
}
