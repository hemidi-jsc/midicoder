/**
 * LLM Config Page
 * Cấu hình LLM provider, model, API URL từ WebGUI
 */

import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../core/api.service';
import { I18nPipe } from '../../core/i18n.pipe';
import { I18nService } from '../../core/i18n.service';
import { DOCS_BASE } from '../../core/app.constants';

@Component({
  selector: 'app-llm-config',
  standalone: true,
  imports: [CommonModule, FormsModule, I18nPipe],
  template: `
    <div>
      <!-- Header -->
      <div class="mb-6">
        <div class="page-header-row">
          <h1 class="text-2xl font-bold">{{ 'llm.title' | i18n }}</h1>
          <a href="{{ docsUrl }}" target="_blank" rel="noopener" class="docs-link">{{ 'common.readGuide' | i18n }}</a>
        </div>
        <p class="text-text-secondary mt-1">{{ 'llm.subtitle' | i18n }}</p>
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
      <div class="card">
        <form (ngSubmit)="handleSave()" class="space-y-6">
          <!-- Provider -->
          <div>
            <label class="block text-base font-medium text-text-secondary mb-2">
              {{ 'llm.provider' | i18n }} <span class="text-accent-error">*</span>
            </label>
            <select
              [(ngModel)]="llm.provider"
              name="provider"
              class="w-full bg-bg-secondary border border-border-primary rounded-lg p-3 text-text-primary focus:outline-none focus:border-accent-primary"
            >
              <option [value]="'openai-compatible'">{{ 'llm.openaiCompatible' | i18n }}</option>
              @for (p of providers; track p) {
                @if (p !== 'openai-compatible') {
                  <option [value]="p" disabled>{{ p }} {{ 'llm.comingSoon' | i18n }}</option>
                }
              }
            </select>
            <p class="text-sm text-text-tertiary mt-2">
              @if (llm.provider === 'openai-compatible') { {{ 'llm.hintOpenaiCompatible' | i18n }} }
              @if (llm.provider === 'openai') { {{ 'llm.hintOpenai' | i18n }} }
              @if (llm.provider === 'anthropic') { {{ 'llm.hintAnthropic' | i18n }} }
              @if (llm.provider === 'aws-bedrock') { {{ 'llm.hintBedrock' | i18n }} }
              @if (llm.provider === 'azure') { {{ 'llm.hintAzure' | i18n }} }
              @if (llm.provider === 'vertex') { {{ 'llm.hintVertex' | i18n }} }
            </p>
          </div>

          <!-- Model -->
          <div>
            <label class="block text-base font-medium text-text-secondary mb-2">
              {{ 'llm.model' | i18n }} <span class="text-accent-error">*</span>
            </label>
            <input
              [(ngModel)]="llm.model"
              name="model"
              type="text"
              placeholder="qwen3.5-27B, gpt-4o, claude-3-sonnet..."
              class="w-full bg-bg-secondary border border-border-primary rounded-lg p-3 text-text-primary focus:outline-none focus:border-accent-primary"
            />
          </div>

          <!-- API URL -->
          <div>
            <label class="block text-base font-medium text-text-secondary mb-2">
              {{ 'llm.apiUrl' | i18n }} <span class="text-accent-error">*</span>
            </label>
            <input
              [(ngModel)]="llm.api_url"
              name="api_url"
              type="text"
              placeholder="http://localhost:11434/v1"
              class="w-full bg-bg-secondary border border-border-primary rounded-lg p-3 text-text-primary focus:outline-none focus:border-accent-primary"
            />
          </div>

          <!-- API Key (optional) -->
          <div>
            <label class="block text-base font-medium text-text-secondary mb-2">
              {{ 'llm.apiKeyOptional' | i18n }}
            </label>
            <input
              [(ngModel)]="llm.api_key"
              name="api_key"
              type="password"
              placeholder="sk-..."
              class="w-full bg-bg-secondary border border-border-primary rounded-lg p-3 text-text-primary focus:outline-none focus:border-accent-primary"
            />
          </div>

          <!-- Advanced Settings -->
          <details class="border-t border-border-primary pt-5">
            <summary class="text-base font-medium text-accent-primary cursor-pointer hover:text-accent-warning select-none">{{ 'llm.advanced' | i18n }}</summary>
            <div class="space-y-6 mt-6">
              <!-- Tip box -->
              <div class="tip-box">
                <span class="tip-icon"><i class="fa-solid fa-circle-info"></i></span>
                <div class="tip-content">
                  <p class="tip-title">{{ 'llm.advancedTipTitle' | i18n }}</p>
                  <ul class="tip-list">
                    <li><span class="tip-term">{{ 'llm.temperature' | i18n }}</span> — {{ 'llm.tipTemperature' | i18n }}</li>
                    <li><span class="tip-term">{{ 'llm.topP' | i18n }}</span> — {{ 'llm.tipTopP' | i18n }}</li>
                    <li><span class="tip-term">{{ 'llm.topK' | i18n }}</span> — {{ 'llm.tipTopK' | i18n }}</li>
                    <li><span class="tip-term">{{ 'llm.minP' | i18n }}</span> — {{ 'llm.tipMinP' | i18n }}</li>
                    <li><span class="tip-term">{{ 'llm.presencePenalty' | i18n }}</span> — {{ 'llm.tipPresencePenalty' | i18n }}</li>
                    <li><span class="tip-term">{{ 'llm.repetitionPenalty' | i18n }}</span> — {{ 'llm.tipRepetitionPenalty' | i18n }}</li>
                  </ul>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-6">
                <div>
                  <label class="block text-base font-medium text-text-secondary mb-2">{{ 'llm.maxTokens' | i18n }}</label>
                  <input
                    [(ngModel)]="llm.max_tokens"
                    name="max_tokens"
                    type="number"
                    class="w-full bg-bg-secondary border border-border-primary rounded-lg p-3 text-text-primary focus:outline-none focus:border-accent-primary"
                  />
                </div>
                <div>
                  <label class="block text-base font-medium text-text-secondary mb-2">{{ 'llm.temperature' | i18n }}</label>
                  <input
                    [(ngModel)]="llm.temperature"
                    name="temperature"
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    class="w-full bg-bg-secondary border border-border-primary rounded-lg p-3 text-text-primary focus:outline-none focus:border-accent-primary"
                  />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-6">
                <div>
                  <label class="block text-base font-medium text-text-secondary mb-2">{{ 'llm.timeout' | i18n }}</label>
                  <input
                    [(ngModel)]="llm.timeout"
                    name="timeout"
                    type="number"
                    class="w-full bg-bg-secondary border border-border-primary rounded-lg p-3 text-text-primary focus:outline-none focus:border-accent-primary"
                  />
                </div>
                <div>
                  <label class="block text-base font-medium text-text-secondary mb-2">{{ 'llm.retryAttempts' | i18n }}</label>
                  <input
                    [(ngModel)]="llm.retry_attempts"
                    name="retry_attempts"
                    type="number"
                    class="w-full bg-bg-secondary border border-border-primary rounded-lg p-3 text-text-primary focus:outline-none focus:border-accent-primary"
                  />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-6">
                <div>
                  <label class="block text-base font-medium text-text-secondary mb-2">{{ 'llm.topP' | i18n }}</label>
                  <input
                    [(ngModel)]="llm.top_p"
                    name="top_p"
                    type="number"
                    min="0"
                    max="1"
                    step="0.05"
                    class="w-full bg-bg-secondary border border-border-primary rounded-lg p-3 text-text-primary focus:outline-none focus:border-accent-primary"
                  />
                </div>
                <div>
                  <label class="block text-base font-medium text-text-secondary mb-2">{{ 'llm.topK' | i18n }}</label>
                  <input
                    [(ngModel)]="llm.top_k"
                    name="top_k"
                    type="number"
                    min="0"
                    step="1"
                    class="w-full bg-bg-secondary border border-border-primary rounded-lg p-3 text-text-primary focus:outline-none focus:border-accent-primary"
                  />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-6">
                <div>
                  <label class="block text-base font-medium text-text-secondary mb-2">{{ 'llm.minP' | i18n }}</label>
                  <input
                    [(ngModel)]="llm.min_p"
                    name="min_p"
                    type="number"
                    min="0"
                    max="1"
                    step="0.05"
                    class="w-full bg-bg-secondary border border-border-primary rounded-lg p-3 text-text-primary focus:outline-none focus:border-accent-primary"
                  />
                </div>
                <div>
                  <label class="block text-base font-medium text-text-secondary mb-2">{{ 'llm.presencePenalty' | i18n }}</label>
                  <input
                    [(ngModel)]="llm.presence_penalty"
                    name="presence_penalty"
                    type="number"
                    min="-2"
                    max="2"
                    step="0.1"
                    class="w-full bg-bg-secondary border border-border-primary rounded-lg p-3 text-text-primary focus:outline-none focus:border-accent-primary"
                  />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-6">
                <div>
                  <label class="block text-base font-medium text-text-secondary mb-2">{{ 'llm.repetitionPenalty' | i18n }}</label>
                  <input
                    [(ngModel)]="llm.repetition_penalty"
                    name="repetition_penalty"
                    type="number"
                    min="1"
                    max="2"
                    step="0.05"
                    class="w-full bg-bg-secondary border border-border-primary rounded-lg p-3 text-text-primary focus:outline-none focus:border-accent-primary"
                  />
                </div>
              </div>
            </div>
          </details>

          <!-- Action Buttons -->
          <div class="flex space-x-4 pt-3 border-t border-border-primary">
            <button
              type="submit"
              class="btn btn-primary px-8 py-3 text-base"
              [disabled]="isSaving"
            >
              {{ isSaving ? ('llm.saving' | i18n) : ('llm.save' | i18n) }}
            </button>
            <button
              type="button"
              (click)="handleTest()"
              class="btn btn-secondary px-8 py-3 text-base"
              [disabled]="isTesting"
            >
              {{ isTesting ? ('llm.testing' | i18n) : ('llm.test' | i18n) }}
            </button>
          </div>
        </form>
      </div>

      <!-- Test Result -->
      @if (testResult) {
        <div class="card mt-6">
          <h2 class="text-lg font-semibold mb-4">{{ 'llm.testResult' | i18n }}</h2>
          @if (testResult.connected) {
            <div class="p-4 rounded-lg border" style="background: rgba(63, 185, 80, 0.1); border-color: var(--accent-success)">
              <p style="color: var(--accent-success); font-weight: 600">{{ 'llm.connected' | i18n }}</p>
              <div class="mt-3 text-sm space-y-1" style="color: var(--text-primary)">
                <p><strong>{{ 'llm.providerLabel' | i18n }}</strong> {{ testResult.provider }}</p>
                <p><strong>{{ 'llm.modelLabel' | i18n }}</strong> {{ testResult.model }}</p>
                @if (testResult.response) {
                  <p><strong>{{ 'llm.responseLabel' | i18n }}</strong> {{ testResult.response }}</p>
                }
                @if (testResult.usage) {
                  <p><strong>{{ 'llm.tokensLabel' | i18n }}</strong> {{ testResult.usage.total_tokens }}</p>
                }
              </div>
            </div>
          } @else {
            <div class="p-4 rounded-lg border" style="background: rgba(242, 83, 83, 0.1); border-color: var(--accent-error)">
              <p style="color: var(--accent-error); font-weight: 600">{{ 'llm.failed' | i18n }}</p>
              @if (testResult.error) {
                <p class="text-sm mt-2" style="color: var(--text-primary)">{{ testResult.error }}</p>
              }
            </div>
          }
        </div>
      }
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

    /* Select with custom caret — same as project create form */
    select {
      appearance: none;
      cursor: pointer;
      padding-right: 36px;
      background-image: url("data:image/svg+xml,%3Csvg width='10' height='6' viewBox='0 0 10 6' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1L5 5L9 1' stroke='%23fc6767' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 12px center;
      background-size: 10px;
    }

    /* Details/Summary advanced section */
    details summary {
      list-style: none;
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 4px 0;
      user-select: none;
    }

    details summary::-webkit-details-marker {
      display: none;
    }

    details summary::before {
      content: '';
      display: inline-block;
      width: 0;
      height: 0;
      border-left: 5px solid var(--brand-color);
      border-top: 4px solid transparent;
      border-bottom: 4px solid transparent;
      transition: transform 0.2s;
      transform: rotate(0deg);
    }

    details[open] summary::before {
      transform: rotate(90deg);
    }

    /* Tip box — subtle, no flashy colors */
    .tip-box {
      display: flex;
      gap: 10px;
      padding: 12px 14px;
      border-left: 3px solid var(--border-primary);
      background: var(--bg-secondary);
    }

    .tip-icon {
      flex-shrink: 0;
      color: var(--text-tertiary);
      font-size: 14px;
      line-height: 1.5;
      margin-top: 2px;
    }

    .tip-title {
      font-size: 13px;
      font-weight: 600;
      color: var(--text-secondary);
      margin: 0 0 6px 0;
    }

    .tip-list {
      margin: 0;
      padding-left: 16px;
      font-size: 12px;
      line-height: 1.7;
      color: var(--text-tertiary);
    }

    .tip-term {
      font-weight: 600;
      color: var(--text-secondary);
    }
  `],
})
export class LlmConfigComponent implements OnInit {
  private api = inject(ApiService);
  private i18n = inject(I18nService);

  readonly docsUrl = `${DOCS_BASE}/llm`;

  // Form state
  llm = {
    provider: 'openai-compatible' as string,
    model: '' as string,
    api_url: '' as string,
    api_key: '' as string,
    max_tokens: 8192,
    temperature: 0.3,
    top_p: 0.9,
    top_k: 0,
    min_p: 0.0,
    presence_penalty: 0.0,
    repetition_penalty: 1.0,
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
      this.llm.top_p = llm.top_p ?? 0.9;
      this.llm.top_k = llm.top_k ?? 0;
      this.llm.min_p = llm.min_p ?? 0.0;
      this.llm.presence_penalty = llm.presence_penalty ?? 0.0;
      this.llm.repetition_penalty = llm.repetition_penalty ?? 1.0;
      this.llm.timeout = llm.timeout ?? 300;
      this.llm.retry_attempts = llm.retry_attempts ?? 3;
      this.providers = result.data.providers || [];
    }
  }

  async handleSave(): Promise<void> {
    if (!this.llm.provider || !this.llm.model || !this.llm.api_url) {
      this.errorMessage = this.i18n.t('llm.validateFields');
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
        top_p: this.llm.top_p,
        top_k: this.llm.top_k,
        min_p: this.llm.min_p,
        presence_penalty: this.llm.presence_penalty,
        repetition_penalty: this.llm.repetition_penalty,
        timeout: this.llm.timeout,
        retry_attempts: this.llm.retry_attempts,
      });

      if (result.success) {
        this.successMessage = this.i18n.t('llm.saveSuccess');
      } else {
        this.errorMessage = result.message || this.i18n.t('llm.saveError');
      }
    } finally {
      this.isSaving = false;
    }
  }

  async handleTest(): Promise<void> {
    if (!this.llm.provider || !this.llm.model || !this.llm.api_url) {
      this.errorMessage = this.i18n.t('llm.validateBeforeTest');
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
        this.testResult = { connected: false, error: result.message || this.i18n.t('llm.testFailed') };
      }
    } finally {
      this.isTesting = false;
    }
  }
}
