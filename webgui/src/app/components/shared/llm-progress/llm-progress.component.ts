/**
 * LLM Progress Overlay — reusable modal showing real-time LLM streaming progress.
 * Used for brief analysis, contract generation, and any LLM pipeline step.
 *
 * Shows: thinking, content tokens, prompt, payload tabs.
 * Emits: close, cancelAnalyze, viewResult (when done)
 */

import { Component, Input, Output, EventEmitter, ChangeDetectorRef, NgZone, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { I18nPipe } from '../../../core/i18n.pipe';

export interface StreamMessage {
  type: string;
  data: any;
  accumulated?: string;
}

@Component({
  selector: 'app-llm-progress',
  standalone: true,
  imports: [CommonModule, I18nPipe],
  template: `
    <div class="llm-progress-backdrop">
      <div class="llm-progress-card" (click)="$event.stopPropagation()">
        <!-- Header -->
        <div class="overlay-header">
          <div class="overlay-title">
            <i class="fa-solid fa-brain"></i>
            <span>{{ title }}</span>
          </div>
          <button class="close-btn" (click)="close()" title="{{ 'analyze.close' | i18n }}">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>

        <!-- Info bar: LLM config -->
        @if (llmConfig) {
          <div class="info-bar">
            <span class="info-item"><i class="fa-solid fa-server"></i> {{ llmConfig.model }}</span>
            @if (llmConfig.temperature != null) {
              <span class="info-item"><i class="fa-solid fa-temperature-half"></i> T={{ llmConfig.temperature }}</span>
            }
            @if (llmConfig.max_tokens) {
              <span class="info-item"><i class="fa-solid fa-cubes"></i> max={{ llmConfig.max_tokens }}</span>
            }
            @if (domain) {
              <span class="info-item domain-badge"><i class="fa-solid fa-tags"></i> {{ domain }}</span>
            }
          </div>
        }

        <!-- Tabs -->
        <div class="overlay-tabs">
          <button class="overlay-tab" [class.active]="activeTab === 'stream'" (click)="activeTab = 'stream'">
            <i class="fa-solid fa-tty"></i> {{ 'analyze.tabs.stream' | i18n }}
          </button>
          <button class="overlay-tab" [class.active]="activeTab === 'prompt'" (click)="activeTab = 'prompt'">
            <i class="fa-solid fa-scroll"></i> {{ 'analyze.tabs.prompt' | i18n }}
          </button>
          <button class="overlay-tab" [class.active]="activeTab === 'payload'" (click)="activeTab = 'payload'">
            <i class="fa-solid fa-file-lines"></i> {{ 'analyze.tabs.payload' | i18n }}
          </button>
        </div>

        <!-- Tab content -->
        <div class="overlay-content">

          <!-- Stream tab — real-time LLM stream -->
          @if (activeTab === 'stream') {
            <div class="stream-panel" #streamPanel>
              <!-- Init phase events (compact) -->
              @for (evt of initEvents; track evt) {
                @if (evt.type === 'started') {
                  <div class="stream-line stream-line-info">
                    <span class="line-label">{{ 'analyze.stream.started' | i18n }}</span>
                    <span class="line-val">
                      @if (evt.data?.brief_id) {
                        #{{ evt.data.brief_id }}, {{ evt.data.brief_length }} {{ 'analyze.payload.chars' | i18n }}
                      } @else {
                        {{ 'analyze.stream.started' | i18n }}
                      }
                    </span>
                  </div>
                } @else if (evt.type === 'llm_config') {
                  <div class="stream-line stream-line-info">
                    <span class="line-label">{{ 'analyze.stream.llmConfig' | i18n }}</span>
                    <span class="line-val">{{ evt.data?.model }}, T={{ evt.data?.temperature }}</span>
                  </div>
                } @else if (evt.type === 'context_injected') {
                  <div class="stream-line stream-line-info">
                    <span class="line-label">{{ 'analyze.stream.contextInjected' | i18n }}</span>
                    <span class="line-val">{{ evt.data?.token_count }} tokens ({{ evt.data?.query_time_ms }}ms)</span>
                  </div>
                } @else if (evt.type === 'user_payload') {
                  <div class="stream-line stream-line-info">
                    <span class="line-label">{{ 'analyze.stream.payloadSent' | i18n }}</span>
                    <span class="line-val">{{ evt.data?.user_message_length }} {{ 'analyze.payload.chars' | i18n }}</span>
                  </div>
                }
              }

              <!-- LLM thinking — shown as it arrives, stripped of tags -->
              @if (accumulatedThinking) {
                <div class="stream-thinking">
                  @if (!thinkingDone) {
                    <span class="thinking-label">{{ 'analyze.stream.thinking' | i18n }}</span>
                  }
                  <div class="thinking-text">{{ accumulatedThinkingClean }}</div>
                </div>
              }

              <!-- LLM content — inline, no card wrapper -->
              @if (accumulatedContent) {
                <div class="stream-content">
                  <span class="content-label">{{ 'analyze.stream.output' | i18n }}</span>
                  <div class="content-text">{{ accumulatedContent }}</div>
                </div>
              }

              <!-- Pending shimmer — hidden when LLM starts outputting -->
              @if (status === 'streaming' && !accumulatedContent && !accumulatedThinking) {
                <div class="stream-pending">
                  <span class="pending-text">{{ 'analyze.stream.thinkingPending' | i18n }}</span>
                </div>
              }

              <!-- Error -->
              @if (status === 'error' && lastError) {
                <div class="stream-line stream-line-err">
                  <span class="line-label">{{ 'analyze.stream.error' | i18n }}</span>
                  <span class="line-val">{{ lastError }}</span>
                </div>
              }
            </div>
          }

          <!-- Prompt tab -->
          @if (activeTab === 'prompt') {
            <div class="prompt-panel">
              @if (systemPrompt) {
                <pre class="prompt-text">{{ systemPrompt }}</pre>
              } @else {
                <div class="empty-state">{{ 'analyze.promptEmpty' | i18n }}</div>
              }
            </div>
          }

          <!-- Payload tab — request/response/usage accordions -->
          @if (activeTab === 'payload') {
            <div class="payload-panel">
              <!-- Raw Request -->
              <div class="payload-section">
                <button class="section-toggle" (click)="sections.rawRequest = !sections.rawRequest">
                  <span class="toggle-icon">{{ sections.rawRequest ? '▾' : '▸' }}</span>
                  <i class="fa-solid fa-paper-plane" style="color:#58a6ff;font-size:0.7rem"></i>
                  {{ 'analyze.payload.rawRequest' | i18n }}
                  <span class="section-size">
                    @if (rawRequestJson) { JSON }
                  </span>
                </button>
                @if (sections.rawRequest) {
                  <div class="payload-body">
                    @if (rawRequestJson) {
                      <pre class="payload-text">{{ rawRequestJson }}</pre>
                    } @else {
                      <div class="empty-state">{{ 'analyze.payload.noResponseYet' | i18n }}</div>
                    }
                  </div>
                }
              </div>

              <!-- Raw Response -->
              <div class="payload-section">
                <button class="section-toggle" (click)="sections.rawResponse = !sections.rawResponse">
                  <span class="toggle-icon">{{ sections.rawResponse ? '▾' : '▸' }}</span>
                  <i class="fa-solid fa-reply" style="color:#3fb950;font-size:0.7rem"></i>
                  {{ 'analyze.payload.rawResponse' | i18n }}
                  <span class="section-size">
                    @if (rawResponseContent) { {{ rawResponseContent.length }} {{ 'analyze.payload.chars' | i18n }} }
                  </span>
                </button>
                @if (sections.rawResponse) {
                  <div class="payload-body">
                    @if (rawResponseContent) {
                      <pre class="payload-text">{{ rawResponseContent }}</pre>
                    } @else {
                      <div class="empty-state">{{ 'analyze.payload.noResponseYet' | i18n }}</div>
                    }
                  </div>
                }
              </div>

              <!-- Token Stats -->
              <div class="payload-section">
                <button class="section-toggle" (click)="sections.tokenStats = !sections.tokenStats">
                  <span class="toggle-icon">{{ sections.tokenStats ? '▾' : '▸' }}</span>
                  <i class="fa-solid fa-chart-pie" style="color:#d2a83a;font-size:0.7rem"></i>
                  {{ 'analyze.payload.tokenStats' | i18n }}
                </button>
                @if (sections.tokenStats) {
                  <div class="payload-body">
                    @if (tokenStats) {
                      <div class="token-stats-grid">
                        <div class="token-stat">
                          <span class="token-label">{{ 'analyze.payload.model' | i18n }}</span>
                          <span class="token-val">{{ tokenStats.model || llmConfig?.model || 'N/A' }}</span>
                        </div>
                        <div class="token-stat">
                          <span class="token-label">{{ 'analyze.payload.promptTokens' | i18n }}</span>
                          <span class="token-val">{{ tokenStats.prompt_tokens || 0 }}</span>
                        </div>
                        <div class="token-stat">
                          <span class="token-label">{{ 'analyze.payload.completionTokens' | i18n }}</span>
                          <span class="token-val">{{ tokenStats.completion_tokens || 0 }}</span>
                        </div>
                        <div class="token-stat">
                          <span class="token-label">{{ 'analyze.payload.totalTokens' | i18n }}</span>
                          <span class="token-val">{{ tokenStats.tokens_used || 0 }}</span>
                        </div>
                        <div class="token-stat">
                          <span class="token-label">{{ 'analyze.payload.latency' | i18n }}</span>
                          <span class="token-val">{{ tokenStats.latency_ms || 0 }}ms</span>
                        </div>
                        <div class="token-stat">
                          <span class="token-label">{{ 'analyze.payload.estimatedCost' | i18n }}</span>
                          <span class="token-val cost-val">{{ formattedCost }}</span>
                        </div>
                      </div>
                    } @else {
                      <div class="empty-state">{{ 'analyze.payload.noStatsYet' | i18n }}</div>
                    }
                  </div>
                }
              </div>
            </div>
          }
        </div>

        <!-- Footer -->
        <div class="overlay-footer">
          <span class="footer-text">
            @if (status === 'streaming') {
              <svg class="footer-spinner" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            }
            @if (streamCount > 0) {
              {{ 'analyze.chunksReceived' | i18n:{count: streamCount} }}
            } @else if (status === 'streaming') {
              {{ 'analyze.connecting' | i18n }}
            }
          </span>
          <div class="footer-actions">
            @if (status !== 'streaming') {
              <button class="btn btn-primary" (click)="viewResult.emit()" [disabled]="status !== 'complete'">
                {{ 'llmProgress.viewResult' | i18n }}
              </button>
            }
            <button class="btn btn-secondary" (click)="cancel()">
              {{ status === 'streaming' ? ('analyze.cancel' | i18n) : ('analyze.close' | i18n) }}
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .llm-progress-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.85);
      backdrop-filter: blur(4px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10000;
      padding: 2rem;
    }

    .llm-progress-card {
      background: #16161e;
      border: 1px solid rgba(252, 103, 103, 0.25);
      width: 100%;
      max-width: 860px;
      height: 75vh;
      display: flex;
      flex-direction: column;
      box-shadow: 0 0 40px rgba(252, 103, 103, 0.15);
    }

    /* Header */
    .overlay-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 18px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      flex-shrink: 0;
    }

    .overlay-title {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 1rem;
      font-weight: 600;
      color: #fff;
    }

    .overlay-title i {
      color: #fc6767;
      font-size: 1.1rem;
    }

    .close-btn {
      background: none;
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: rgba(255, 255, 255, 0.5);
      font-size: 1rem;
      padding: 4px 10px;
      cursor: pointer;
      transition: all 0.2s;
    }

    .close-btn:hover {
      color: #fff;
      border-color: #fc6767;
    }

    /* Info bar */
    .info-bar {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 8px 18px;
      background: rgba(255, 255, 255, 0.03);
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      flex-shrink: 0;
      flex-wrap: wrap;
    }

    .info-item {
      font-size: 0.75rem;
      color: rgba(255, 255, 255, 0.6);
      display: flex;
      align-items: center;
      gap: 4px;
      font-family: monospace;
    }

    .info-item i {
      color: #fc6767;
      font-size: 0.7rem;
    }

    .domain-badge {
      background: rgba(252, 103, 103, 0.15);
      padding: 1px 8px;
      border: 1px solid rgba(252, 103, 103, 0.25);
      color: #fc6767 !important;
    }

    /* Tabs */
    .overlay-tabs {
      display: flex;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      flex-shrink: 0;
    }

    .overlay-tab {
      padding: 8px 16px;
      background: none;
      border: none;
      color: rgba(255, 255, 255, 0.4);
      font-size: 0.8125rem;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }

    .overlay-tab:hover {
      color: rgba(255, 255, 255, 0.7);
    }

    .overlay-tab.active {
      color: #fc6767;
      border-bottom: 2px solid #fc6767;
    }

    /* Content */
    .overlay-content {
      flex: 1;
      overflow: hidden;
      display: flex;
      min-height: 0;
    }

    /* Stream panel */
    .stream-panel {
      height: 100%;
      overflow-y: auto;
      padding: 10px 14px;
      font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
      font-size: 0.78rem;
      line-height: 1.55;
    }

    .stream-panel::-webkit-scrollbar {
      width: 5px;
    }

    .stream-panel::-webkit-scrollbar-thumb {
      background: rgba(252, 103, 103, 0.2);
    }

    /* Info lines (init events, complete, error) */
    .stream-line {
      display: flex;
      align-items: baseline;
      gap: 6px;
      padding: 2px 0;
      font-size: 0.72rem;
    }

    .line-label {
      flex-shrink: 0;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }

    .line-val {
      flex: 1;
      color: rgba(255, 255, 255, 0.5);
    }

    .stream-line-info { color: rgba(255, 255, 255, 0.35); }
    .stream-line-info .line-label { color: #3fb950; }

    .stream-line-err { color: #f85149; }
    .stream-line-err .line-label { font-weight: 700; }

    /* LLM thinking — compact, no card */
    .stream-thinking {
      margin: 6px 0;
      font-size: 0.75rem;
    }

    .thinking-label {
      font-size: 0.65rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #d2a83a;
      margin-bottom: 3px;
      display: block;
    }

    .thinking-text {
      color: rgba(210, 168, 58, 0.7);
      font-style: italic;
      line-height: 1.5;
      white-space: pre-wrap;
      word-break: break-word;
      padding-left: 10px;
      border-left: 2px solid rgba(210, 168, 58, 0.25);
    }

    /* LLM content — inline, no card */
    .stream-content {
      margin: 6px 0;
      font-size: 0.75rem;
    }

    .content-label {
      font-size: 0.65rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #58a6ff;
      margin-bottom: 3px;
      display: block;
    }

    .content-text {
      color: rgba(255, 255, 255, 0.75);
      line-height: 1.55;
      white-space: pre-wrap;
      word-break: break-word;
      padding-left: 10px;
      border-left: 2px solid rgba(88, 166, 255, 0.25);
      font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    }

    /* Pending shimmer — text glow only */
    .stream-pending {
      padding: 4px 0;
    }

    .pending-text {
      font-size: 0.72rem;
      font-style: italic;
      color: rgba(255, 255, 255, 0.3);
      position: relative;
      display: inline-block;
      background: linear-gradient(90deg,
        rgba(255,255,255,0.3) 0%,
        rgba(255,255,255,0.8) 40%,
        rgba(255,255,255,0.3) 60%,
        rgba(255,255,255,0.3) 100%
      );
      background-size: 200% 100%;
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
      animation: textGlow 2s ease-in-out infinite;
    }

    @keyframes textGlow {
      0% { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }

    /* blink (keep for other uses) */
    @keyframes blink {
      0%, 50% { opacity: 1; }
      51%, 100% { opacity: 0; }
    }

    /* Prompt panel */
    .prompt-panel {
      height: 100%;
      overflow-y: auto;
      padding: 14px;
    }

    .prompt-text {
      font-family: 'Cascadia Code', 'Fira Code', monospace;
      font-size: 0.75rem;
      line-height: 1.6;
      color: rgba(255, 255, 255, 0.7);
      white-space: pre-wrap;
      word-break: break-word;
      margin: 0;
    }

    /* Payload panel */
    .payload-panel {
      height: 100%;
      overflow-y: auto;
      padding: 10px 14px;
    }

    /* Payload collapsible sections */
    .payload-section {
      margin-bottom: 6px;
      border: 1px solid rgba(255, 255, 255, 0.06);
      background: rgba(255, 255, 255, 0.02);
    }

    .section-toggle {
      width: 100%;
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 7px 10px;
      background: none;
      border: none;
      color: rgba(255, 255, 255, 0.65);
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      text-align: left;
      transition: background 0.15s;
    }

    .section-toggle:hover {
      background: rgba(255, 255, 255, 0.04);
    }

    .toggle-icon {
      color: #fc6767;
      font-size: 0.7rem;
      flex-shrink: 0;
    }

    .section-size {
      margin-left: auto;
      font-size: 0.62rem;
      color: rgba(255, 255, 255, 0.3);
      font-weight: 400;
      font-family: monospace;
    }

    .payload-text {
      font-family: 'Cascadia Code', 'Fira Code', monospace;
      font-size: 0.72rem;
      line-height: 1.5;
      color: rgba(255, 255, 255, 0.6);
      white-space: pre-wrap;
      word-break: break-word;
      margin: 0;
      padding: 8px 10px;
      background: rgba(0, 0, 0, 0.2);
      border-top: 1px solid rgba(255, 255, 255, 0.04);
      max-height: 300px;
      overflow-y: auto;
      width: 100%;
      box-sizing: border-box;
    }

    /* Payload body container */
    .payload-body {
      width: 100%;
      box-sizing: border-box;
    }

    .payload-block {
      margin-bottom: 10px;
    }

    .payload-block:last-child {
      margin-bottom: 0;
    }

    .block-label {
      font-size: 0.65rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: rgba(255, 255, 255, 0.4);
      padding: 4px 10px;
      background: rgba(255, 255, 255, 0.03);
      border-top: 1px solid rgba(255, 255, 255, 0.04);
    }

    /* Token stats grid */
    .token-stats-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      padding: 12px 10px;
    }

    .token-stat {
      display: flex;
      flex-direction: column;
      gap: 2px;
      padding: 8px 10px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.06);
    }

    .token-label {
      font-size: 0.625rem;
      color: rgba(255, 255, 255, 0.4);
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }

    .token-val {
      font-size: 0.9rem;
      font-weight: 700;
      color: rgba(255, 255, 255, 0.85);
      font-family: 'Cascadia Code', 'Fira Code', monospace;
    }

    .token-val.cost-val {
      color: #3fb950;
    }

    /* Empty state */
    .empty-state {
      padding: 2rem;
      text-align: center;
      color: rgba(255, 255, 255, 0.3);
      font-size: 0.85rem;
    }

    /* Footer */
    .overlay-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 10px 18px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      flex-shrink: 0;
    }

    .footer-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .footer-text {
      font-size: 0.75rem;
      color: rgba(255, 255, 255, 0.4);
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .footer-spinner {
      display: inline-block;
      width: 14px;
      height: 14px;
      animation: spin 1s linear infinite;
      color: rgba(255, 255, 255, 0.4);
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .btn {
      padding: 6px 16px;
      font-size: 0.8rem;
      font-weight: 500;
      cursor: pointer;
      border: none;
      transition: all 0.2s;
    }

    .btn-primary {
      background: #fc6767;
      color: #fff;
    }

    .btn-primary:hover {
      background: #e55a5a;
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.08);
      color: rgba(255, 255, 255, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.15);
    }

    .btn-secondary:hover {
      background: rgba(255, 255, 255, 0.12);
    }
  `]
})
export class LlmProgressComponent {
  @Input() visible = false;
  @Input() title = 'LLM Processing';
  @Output() closeOverlay = new EventEmitter<void>();
  @Output() cancelAnalyze = new EventEmitter<void>();
  @Output() viewResult = new EventEmitter<void>();

  private ngZone = inject(NgZone);
  private cdr = inject(ChangeDetectorRef);

  // Data
  systemPrompt = '';
  llmConfig: any = null;
  domain = '';
  userPayloadInfo: any = null;
  rawRequestJson = '';
  rawResponseContent = '';
  tokenStats: any = null;

  // Stream tab — user-friendly format
  initEvents: StreamMessage[] = [];
  accumulatedThinking = '';
  thinkingDone = false;
  accumulatedContent = '';
  lastError = '';

  /** Strip <thinking>...</thinking> tags from raw LLM output */
  get accumulatedThinkingClean(): string {
    return this.accumulatedThinking
      .replace(/<thinking>/gi, '')
      .replace(/<\/thinking>/gi, '')
      .trim();
  }

  // State
  status: 'streaming' | 'complete' | 'error' = 'streaming';
  activeTab: 'stream' | 'prompt' | 'payload' = 'stream';
  streamCount = 0;
  sections = { systemPrompt: false, userMessage: false, rawRequest: false, rawResponse: false, tokenStats: false };

  get formattedCost(): string {
    const val = this.tokenStats?.estimated_cost_usd || 0;
    return `$${val.toFixed(4)}`;
  }

  /** Unwrap SSE data: backend wraps as {"data":"...","accumulated":"..."} when accumulated present */
  private _extract(msg: StreamMessage): { text: string; accumulated?: string } {
    if (typeof msg.data === 'string') return { text: msg.data };
    if (msg.data && typeof msg.data === 'object') {
      return {
        text: msg.data.data ?? '',
        accumulated: msg.data.accumulated,
      };
    }
    return { text: String(msg.data ?? '') };
  }

  /** Xử lý message từ SSE stream */
  onMessage(msg: StreamMessage): void {
    this.ngZone.run(() => {
      this.streamCount++;

      switch (msg.type) {
        case 'started':
          this.initEvents.push(msg);
          break;

        case 'system_prompt':
          this.systemPrompt = typeof msg.data === 'string' ? msg.data : JSON.stringify(msg.data);
          this.initEvents.push(msg);
          break;

        case 'llm_config':
          this.llmConfig = msg.data;
          this.initEvents.push(msg);
          break;

        case 'domain':
          this.domain = typeof msg.data === 'string' ? msg.data : String(msg.data);
          break;

        case 'context_injected':
          this.initEvents.push(msg);
          break;

        case 'user_payload':
          this.userPayloadInfo = msg.data;
          this.initEvents.push(msg);
          // Store raw request as formatted JSON
          if (msg.data?.raw_request) {
            this.rawRequestJson = JSON.stringify(msg.data.raw_request, null, 2);
          }
          break;

        case 'thinking': {
          const { text, accumulated } = this._extract(msg);
          if (accumulated != null) {
            this.accumulatedThinking = accumulated;
          } else {
            this.accumulatedThinking += text;
          }
          break;
        }

        case 'thinking_end':
          this.thinkingDone = true;
          break;

        case 'content': {
          const { text, accumulated } = this._extract(msg);
          if (accumulated != null) {
            this.accumulatedContent = accumulated;
          } else {
            this.accumulatedContent += text;
          }
          break;
        }

        case 'complete':
          this.status = 'complete';
          // Capture token stats and model from complete event
          this.tokenStats = msg.data;
          break;

        case 'final_content':
          // Store raw LLM response content
          this.rawResponseContent = typeof msg.data === 'string' ? msg.data : JSON.stringify(msg.data);
          break;

        case 'final_result':
          this.status = 'complete';
          break;

        case 'error':
          this.lastError = typeof msg.data === 'string' ? msg.data : JSON.stringify(msg.data);
          this.status = 'error';
          break;
      }

      // Auto-scroll stream panel
      if (this.activeTab === 'stream') {
        setTimeout(() => {
          const panel = document.querySelector('.stream-panel');
          if (panel) panel.scrollTop = panel.scrollHeight;
        }, 16);
      }

      this.cdr.detectChanges();
    });
  }

  close(): void {
    if (this.status === 'streaming') {
      this.cancelAnalyze.emit();
    }
    this.closeOverlay.emit();
  }

  cancel(): void {
    this.cancelAnalyze.emit();
    this.closeOverlay.emit();
  }

  /** Reset state — called before each new session */
  reset(): void {
    this.systemPrompt = '';
    this.llmConfig = null;
    this.domain = '';
    this.userPayloadInfo = null;
    this.rawResponseContent = '';
    this.tokenStats = null;
    this.initEvents = [];
    this.accumulatedThinking = '';
    this.thinkingDone = false;
    this.accumulatedContent = '';
    this.lastError = '';
    this.status = 'streaming';
    this.activeTab = 'stream';
    this.streamCount = 0;
    this.sections = { systemPrompt: false, userMessage: false, rawRequest: false, rawResponse: false, tokenStats: false };
  }
}
