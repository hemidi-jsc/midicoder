/**
 * LLM Config Page
 * Cấu hình LLM provider, model, API URL từ WebGUI
 */

import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../core/api.service';

@Component({
  selector: 'app-llm-config',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="container mx-auto px-6 py-8">
      <!-- Header -->
      <div class="mb-6">
        <h1 class="text-2xl font-bold">Cấu hình LLM</h1>
        <p class="text-text-secondary mt-1">Thiết lập kết nối đến LLM provider</p>
      </div>

      <!-- Status Messages -->
      @if (successMessage) {
        <div class="mb-4 p-3 rounded border" style="background: rgba(63, 185, 80, 0.1); border-color: var(--accent-success); color: var(--accent-success)">
          {{ successMessage }}
        </div>
      }
      @if (errorMessage) {
        <div class="mb-4 p-3 rounded border" style="background: rgba(242, 83, 83, 0.1); border-color: var(--accent-error); color: var(--accent-error)">
          {{ errorMessage }}
        </div>
      }

      <!-- Config Form -->
      <div class="card max-w-2xl">
        <form (ngSubmit)="handleSave()" class="space-y-5">
          <!-- Provider -->
          <div>
            <label class="block text-sm font-medium text-text-secondary mb-1">
              Provider <span class="text-accent-error">*</span>
            </label>
            <select
              [(ngModel)]="llm.provider"
              name="provider"
              class="w-full bg-bg-secondary border border-border-primary rounded p-3 text-text-primary focus:outline-none focus:border-accent-primary"
            >
              @for (p of providers; track p) {
                <option [value]="p">{{ p }}</option>
              }
            </select>
            <p class="text-xs text-text-tertiary mt-1">
              @if (llm.provider === 'openai-compatible') { Custom URL với OpenAI API format (Ollama, LM Studio, v.v.) }
              @if (llm.provider === 'openai') { OpenAI API (gpt-4o, gpt-4, v.v.) }
              @if (llm.provider === 'anthropic') { Anthropic API (claude-3-sonnet, v.v.) }
            </p>
          </div>

          <!-- Model -->
          <div>
            <label class="block text-sm font-medium text-text-secondary mb-1">
              Model <span class="text-accent-error">*</span>
            </label>
            <input
              [(ngModel)]="llm.model"
              name="model"
              type="text"
              placeholder="qwen3.5-27B, gpt-4o, claude-3-sonnet..."
              class="w-full bg-bg-secondary border border-border-primary rounded p-3 text-text-primary focus:outline-none focus:border-accent-primary"
            />
          </div>

          <!-- API URL -->
          <div>
            <label class="block text-sm font-medium text-text-secondary mb-1">
              API URL <span class="text-accent-error">*</span>
            </label>
            <input
              [(ngModel)]="llm.api_url"
              name="api_url"
              type="text"
              placeholder="http://localhost:11434/v1"
              class="w-full bg-bg-secondary border border-border-primary rounded p-3 text-text-primary focus:outline-none focus:border-accent-primary"
            />
          </div>

          <!-- API Key (optional) -->
          <div>
            <label class="block text-sm font-medium text-text-secondary mb-1">
              API Key <span class="text-text-tertiary">(optional)</span>
            </label>
            <input
              [(ngModel)]="llm.api_key"
              name="api_key"
              type="password"
              placeholder="sk-..."
              class="w-full bg-bg-secondary border border-border-primary rounded p-3 text-text-primary focus:outline-none focus:border-accent-primary"
            />
          </div>

          <!-- Advanced Settings -->
          <details class="border-t border-border-primary pt-4">
            <summary class="text-sm text-accent-primary cursor-pointer">Cài đặt nâng cao</summary>
            <div class="grid grid-cols-2 gap-4 mt-3">
              <div>
                <label class="block text-sm font-medium text-text-secondary mb-1">Max Tokens</label>
                <input
                  [(ngModel)]="llm.max_tokens"
                  name="max_tokens"
                  type="number"
                  class="w-full bg-bg-secondary border border-border-primary rounded p-3 text-text-primary focus:outline-none focus:border-accent-primary"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-text-secondary mb-1">Temperature</label>
                <input
                  [(ngModel)]="llm.temperature"
                  name="temperature"
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                  class="w-full bg-bg-secondary border border-border-primary rounded p-3 text-text-primary focus:outline-none focus:border-accent-primary"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-text-secondary mb-1">Timeout (giây)</label>
                <input
                  [(ngModel)]="llm.timeout"
                  name="timeout"
                  type="number"
                  class="w-full bg-bg-secondary border border-border-primary rounded p-3 text-text-primary focus:outline-none focus:border-accent-primary"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-text-secondary mb-1">Retry Attempts</label>
                <input
                  [(ngModel)]="llm.retry_attempts"
                  name="retry_attempts"
                  type="number"
                  class="w-full bg-bg-secondary border border-border-primary rounded p-3 text-text-primary focus:outline-none focus:border-accent-primary"
                />
              </div>
            </div>
          </details>

          <!-- Action Buttons -->
          <div class="flex space-x-3 pt-2">
            <button
              type="submit"
              class="btn btn-primary"
              [disabled]="isSaving"
            >
              {{ isSaving ? 'Đang lưu...' : 'Lưu cấu hình' }}
            </button>
            <button
              type="button"
              (click)="handleTest()"
              class="btn btn-secondary"
              [disabled]="isTesting"
            >
              {{ isTesting ? 'Đang test...' : 'Test kết nối' }}
            </button>
          </div>
        </form>
      </div>

      <!-- Test Result -->
      @if (testResult) {
        <div class="card mt-6">
          <h2 class="text-lg font-semibold mb-3" style="color: var(--text-primary)">Kết quả test kết nối</h2>
          @if (testResult.connected) {
            <div class="p-3 rounded border" style="background: rgba(63, 185, 80, 0.1); border-color: var(--accent-success)">
              <p style="color: var(--accent-success); font-weight: 600">✓ Kết nối thành công!</p>
              <div class="mt-2 text-sm space-y-1" style="color: var(--text-primary)">
                <p><strong>Provider:</strong> {{ testResult.provider }}</p>
                <p><strong>Model:</strong> {{ testResult.model }}</p>
                @if (testResult.response) {
                  <p><strong>Response:</strong> {{ testResult.response }}</p>
                }
                @if (testResult.usage) {
                  <p><strong>Tokens:</strong> {{ testResult.usage.total_tokens }}</p>
                }
              </div>
            </div>
          } @else {
            <div class="p-3 rounded border" style="background: rgba(242, 83, 83, 0.1); border-color: var(--accent-error)">
              <p style="color: var(--accent-error); font-weight: 600">✗ Kết nối thất bại</p>
              @if (testResult.error) {
                <p class="text-sm mt-2" style="color: var(--text-primary)">{{ testResult.error }}</p>
              }
            </div>
          }
        </div>
      }

      <!-- Presets -->
      <div class="card mt-6">
        <h2 class="text-lg font-semibold mb-3">Cài đặt sẵn</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <button (click)="applyPreset('ollama')" class="p-3 bg-bg-secondary rounded border border-border-primary hover:border-accent-primary text-left">
            <p class="font-medium text-accent-primary">Ollama (local)</p>
            <p class="text-xs text-text-tertiary mt-1">qwen3.5-27B trên localhost:11434</p>
          </button>
          <button (click)="applyPreset('openai')" class="p-3 bg-bg-secondary rounded border border-border-primary hover:border-accent-primary text-left">
            <p class="font-medium text-accent-primary">OpenAI</p>
            <p class="text-xs text-text-tertiary mt-1">gpt-4o với API key</p>
          </button>
          <button (click)="applyPreset('anthropic')" class="p-3 bg-bg-secondary rounded border border-border-primary hover:border-accent-primary text-left">
            <p class="font-medium text-accent-primary">Anthropic</p>
            <p class="text-xs text-text-tertiary mt-1">claude-3-sonnet</p>
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [],
})
export class LlmConfigComponent implements OnInit {
  private api = inject(ApiService);

  // Form state
  llm = {
    provider: 'openai-compatible' as string,
    model: '' as string,
    api_url: '' as string,
    api_key: '' as string,
    max_tokens: 8192,
    temperature: 0.3,
    timeout: 300,
    retry_attempts: 3,
  };

  providers: string[] = [];
  isSaving = false;
  isTesting = false;
  successMessage = '';
  errorMessage = '';
  testResult: any = null;

  async ngOnInit(): Promise<void> {
    await this.loadConfig();
  }

  async loadConfig(): Promise<void> {
    const result = await this.api.getLlmConfig();
    if (result.success && result.data) {
      const llm = result.data.llm || {};
      this.llm.provider = llm.provider || 'openai-compatible';
      this.llm.model = llm.model || '';
      this.llm.api_url = llm.api_url || '';
      this.llm.api_key = llm.api_key || '';
      this.llm.max_tokens = llm.max_tokens ?? 8192;
      this.llm.temperature = llm.temperature ?? 0.3;
      this.llm.timeout = llm.timeout ?? 300;
      this.llm.retry_attempts = llm.retry_attempts ?? 3;
      this.providers = result.data.providers || [];
    }
  }

  async handleSave(): Promise<void> {
    if (!this.llm.provider || !this.llm.model || !this.llm.api_url) {
      this.errorMessage = 'Vui lòng điền đầy đủ provider, model, và API URL';
      return;
    }

    this.isSaving = true;
    this.successMessage = '';
    this.errorMessage = '';

    try {
      const result = await this.api.setLlmConfig({
        provider: this.llm.provider,
        model: this.llm.model,
        api_url: this.llm.api_url,
        api_key: this.llm.api_key || undefined,
        max_tokens: this.llm.max_tokens,
        temperature: this.llm.temperature,
        timeout: this.llm.timeout,
        retry_attempts: this.llm.retry_attempts,
      });

      if (result.success) {
        this.successMessage = 'Lưu cấu hình LLM thành công';
      } else {
        this.errorMessage = result.message || 'Lưu thất bại';
      }
    } finally {
      this.isSaving = false;
    }
  }

  async handleTest(): Promise<void> {
    if (!this.llm.provider || !this.llm.model || !this.llm.api_url) {
      this.errorMessage = 'Vui lòng điền đầy đủ provider, model, và API URL trước khi test';
      return;
    }

    this.isTesting = true;
    this.testResult = null;
    this.errorMessage = '';

    try {
      const result = await this.api.testLlmConfig();
      if (result.success && result.data) {
        this.testResult = result.data;
      } else {
        this.testResult = { connected: false, error: result.message || 'Test failed' };
      }
    } finally {
      this.isTesting = false;
    }
  }

  applyPreset(preset: string): void {
    switch (preset) {
      case 'ollama':
        this.llm.provider = 'openai-compatible';
        this.llm.model = 'qwen3.5-27B';
        this.llm.api_url = 'http://localhost:11434/v1';
        this.llm.api_key = '';
        break;
      case 'openai':
        this.llm.provider = 'openai';
        this.llm.model = 'gpt-4o';
        this.llm.api_url = 'https://api.openai.com/v1';
        break;
      case 'anthropic':
        this.llm.provider = 'anthropic';
        this.llm.model = 'claude-3-5-sonnet-20241022';
        this.llm.api_url = 'https://api.anthropic.com';
        break;
    }
  }
}
