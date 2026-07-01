/**
 * Brief Analyze LLM Progress Overlay — dedicated to brief analysis streaming.
 * NOT shared with contract generation (use contract-gen-progress instead).
 *
 * Shows: thinking, content tokens, prompt, payload tabs.
 * Emits: close, cancelAnalyze, viewResult (when done)
 */

import { Component, Input, Output, EventEmitter, ChangeDetectorRef, NgZone, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { I18nPipe } from '../../../core/i18n.pipe';

export interface BriefAnalyzeStreamMessage {
  type: string;
  data: any;
  accumulated?: string;
}

@Component({
  selector: 'app-brief-analyze-llm-progress',
  standalone: true,
  imports: [CommonModule, I18nPipe],
  template: `
    @if (visible) {
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

          <!-- Stream tab — vertical timeline -->
          @if (activeTab === 'stream') {
            <div class="stream-panel" #streamPanel>
              <!-- Init phase (compact info lines) -->
              @for (evt of initEvents; track evt) {
                @if (evt.type === 'started') {
                  <div class="timeline-info">
                    <i class="fa-solid fa-play"></i>
                    <span>Bắt đầu: #{{ evt.data?.brief_id || 'unknown' }}</span>
                  </div>
                } @else if (evt.type === 'llm_config') {
                  <div class="timeline-info">
                    <i class="fa-solid fa-server"></i>
                    <span>{{ evt.data?.model }}, T={{ evt.data?.temperature }}</span>
                  </div>
                } @else if (evt.type === 'user_payload') {
                  <div class="timeline-info">
                    <i class="fa-solid fa-paper-plane"></i>
                    <span>{{ evt.data?.user_message_length }} ký tự</span>
                  </div>
                }
              }

              <!-- Timeline — LLM conversation flow -->
              @if (toolEvents.length > 0) {
                <div class="timeline-separator"></div>

                @for (te of toolEvents; track te) {
                  <!-- Thinking — LLM internal reasoning (auto-expanded when streaming) -->
                  @if (te.type === 'thinking' && te.text) {
                    <div class="timeline-item timeline-thinking" [class.streaming]="te.isStreaming">
                      <button class="timeline-header" (click)="te._expanded = !te._expanded">
                        <span class="timeline-dot"><i class="fa-solid fa-brain"></i></span>
                        <span class="timeline-label">Suy nghĩ</span>
                        @if (te.isStreaming) {
                          <span class="live-cursor-dot"></span>
                        }
                        <span class="timeline-toggle"><i class="fa-solid fa-chevron-right" [class.expanded]="te._expanded"></i></span>
                      </button>
                      @if (te._expanded) {
                        <div class="timeline-body">
                          <div class="timeline-thinking-text">
                            {{ te.text }}
                            @if (te.isStreaming) {<span class="live-cursor">|</span>}
                          </div>
                        </div>
                      }
                    </div>
                  }

                  <!-- Merged tool call + result (type === 'tool' after merge, or 'call' pending) -->
                  @if (te.type === 'tool' || te.type === 'call') {
                    <div class="timeline-item" [class.timeline-success]="te._valid === true" [class.timeline-error]="te._valid === false" [class.timeline-pending]="te.type === 'call'">
                      <button class="timeline-header" (click)="te._expanded = !te._expanded">
                        <span class="timeline-dot">
                          @if (te.type === 'tool' && te._valid === true) {
                            <i class="fa-solid fa-circle-check"></i>
                          } @else if (te.type === 'tool' && te._valid === false) {
                            <i class="fa-solid fa-circle-xmark"></i>
                          } @else if (te.type === 'tool') {
                            <i class="fa-solid fa-wrench"></i>
                          } @else {
                            <i class="fa-solid fa-wrench"></i>
                          }
                        </span>
                        <span class="timeline-label">Gọi tool: <strong>{{ te.name }}</strong>{{ getToolArgPreview(te) }}</span>
                        @if (te.duration != null) {
                          <span class="timeline-time">{{ te.duration }}ms</span>
                        }
                        <span class="timeline-toggle"><i class="fa-solid fa-chevron-right" [class.expanded]="te._expanded"></i></span>
                      </button>
                      @if (te._expanded) {
                        <div class="timeline-body">
                          @if (te.arguments) {
                            <div class="timeline-section-label">Tham số:</div>
                            <pre class="timeline-json">{{ jsonStr(te.arguments) }}</pre>
                          }
                          @if (te.full_result) {
                            <div class="timeline-section-label">Kết quả:</div>
                            <pre class="timeline-json">{{ jsonStr(te.full_result) }}</pre>
                          }
                          @if (!te.full_result && !te.arguments) {
                            <span class="timeline-empty">không có dữ liệu</span>
                          }
                        </div>
                      }
                    </div>
                  }

                  <!-- Orphan result (no matching call) -->
                  @if (te.type === 'result') {
                    <div class="timeline-item" [class.timeline-success]="te._valid === true" [class.timeline-error]="te._valid === false">
                      <button class="timeline-header" (click)="te._expanded = !te._expanded">
                        <span class="timeline-dot">
                          @if (te._valid === true) {
                            <i class="fa-solid fa-circle-check"></i>
                          } @else if (te._valid === false) {
                            <i class="fa-solid fa-circle-xmark"></i>
                          } @else {
                            <i class="fa-solid fa-wrench"></i>
                          }
                        </span>
                        <span class="timeline-label">Gọi tool: <strong>{{ te.name }}</strong>{{ getToolArgPreview(te) }}</span>
                        <span class="timeline-time">{{ te.duration || 0 }}ms</span>
                        <span class="timeline-toggle"><i class="fa-solid fa-chevron-right" [class.expanded]="te._expanded"></i></span>
                      </button>
                      @if (te._expanded) {
                        <div class="timeline-body">
                          @if (te.full_result) {
                            <pre class="timeline-json">{{ jsonStr(te.full_result) }}</pre>
                          } @else if (te.summary) {
                            <pre class="timeline-json">{{ jsonStr(te.summary) }}</pre>
                          }
                        </div>
                      }
                    </div>
                  }

                  <!-- Content — LLM text output (final YAML) (auto-expanded when streaming) -->
                  @if (te.type === 'content' && te.text) {
                    <div class="timeline-item timeline-content" [class.streaming]="te.isStreaming">
                      <button class="timeline-header" (click)="te._expanded = !te._expanded">
                        <span class="timeline-dot"><i class="fa-solid fa-file-code"></i></span>
                        <span class="timeline-label">Output</span>
                        @if (te.isStreaming) {
                          <span class="live-cursor-dot"></span>
                        }
                        <span class="timeline-toggle"><i class="fa-solid fa-chevron-right" [class.expanded]="te._expanded"></i></span>
                      </button>
                      @if (te._expanded) {
                        <div class="timeline-body">
                          <pre class="timeline-content-text">
                            {{ te.text }}
                            @if (te.isStreaming) {<span class="live-cursor">|</span>}
                          </pre>
                        </div>
                      }
                    </div>
                  }
                }
              }

              <!-- Pending shimmer -->
              @if (shouldShowPendingShimmer) {
                <div class="timeline-pending">
                  <span class="pending-text">Đang suy nghĩ...</span>
                </div>
              }

              <!-- Error -->
              @if (status === 'error' && lastError) {
                <div class="timeline-item timeline-error">
                  <div class="timeline-header">
                    <span class="timeline-dot"><i class="fa-solid fa-triangle-exclamation"></i></span>
                    <span class="timeline-label timeline-error-label">Lỗi: {{ lastError }}</span>
                  </div>
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
                  <span class="toggle-icon"><i class="fa-solid fa-chevron-down" [class.expanded]="sections.rawRequest"></i></span>
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
                  <span class="toggle-icon"><i class="fa-solid fa-chevron-down" [class.expanded]="sections.rawResponse"></i></span>
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
                  <span class="toggle-icon"><i class="fa-solid fa-chevron-down" [class.expanded]="sections.tokenStats"></i></span>
                  <i class="fa-solid fa-chart-pie" style="color:#d2a83a;font-size:0.7rem"></i>
                  {{ 'analyze.payload.tokenStats' | i18n }}
                </button>
                @if (sections.tokenStats) {
                  <div class="payload-body">
                    @if (_normalizedStats) {
                      <div class="token-stats-grid">
                        <div class="token-stat">
                          <span class="token-label">{{ 'analyze.payload.model' | i18n }}</span>
                          <span class="token-val">{{ _normalizedStats.model || llmConfig?.model || 'N/A' }}</span>
                        </div>
                        <div class="token-stat">
                          <span class="token-label">{{ 'analyze.payload.promptTokens' | i18n }}</span>
                          <span class="token-val">{{ _normalizedStats.prompt_tokens }}</span>
                        </div>
                        <div class="token-stat">
                          <span class="token-label">{{ 'analyze.payload.completionTokens' | i18n }}</span>
                          <span class="token-val">{{ _normalizedStats.completion_tokens }}</span>
                        </div>
                        <div class="token-stat">
                          <span class="token-label">{{ 'analyze.payload.totalTokens' | i18n }}</span>
                          <span class="token-val">{{ _normalizedStats.tokens_used }}</span>
                        </div>
                        <div class="token-stat">
                          <span class="token-label">{{ 'analyze.payload.latency' | i18n }}</span>
                          <span class="token-val">{{ _normalizedStats.latency_ms }}ms</span>
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
    }
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
      overflow-x: hidden;
      padding: 10px 14px;
      font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
      font-size: 0.78rem;
      line-height: 1.55;
      width: 100%;
      box-sizing: border-box;
    }

    .stream-panel::-webkit-scrollbar {
      width: 5px;
    }

    .stream-panel::-webkit-scrollbar-thumb {
      background: rgba(252, 103, 103, 0.2);
    }

    /* Timeline info lines (init phase) */
    .timeline-info {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 2px 0;
      font-size: 0.7rem;
      color: rgba(255, 255, 255, 0.35);
    }

    .timeline-info i {
      color: #3fb950;
      font-size: 0.6rem;
      width: 12px;
      text-align: center;
    }

    .timeline-separator {
      border: none;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
      margin: 6px 0 8px 0;
    }

    /* Timeline items — vertical flow with left border line */
    .timeline-item {
      position: relative;
      margin: 2px 0;
      padding-left: 24px;
      animation: timelineFadeIn 0.3s ease-out;
    }

    /* Vertical line connecting items */
    .timeline-item::before {
      content: '';
      position: absolute;
      left: 10px;
      top: 0;
      bottom: -6px;
      width: 1px;
      background: rgba(255, 255, 255, 0.08);
    }

    .timeline-item:last-child::before {
      bottom: 0;
    }

    @keyframes timelineFadeIn {
      from { opacity: 0; transform: translateX(-6px); }
      to { opacity: 1; transform: translateX(0); }
    }

    /* Timeline header — clickable accordion */
    .timeline-header {
      display: flex;
      align-items: center;
      gap: 8px;
      width: 100%;
      padding: 5px 8px;
      background: none;
      border: none;
      cursor: pointer;
      text-align: left;
      transition: background 0.15s;
      font-family: 'Cascadia Code', 'Fira Code', monospace;
      font-size: 0.72rem;
      border-radius: 3px;
    }

    .timeline-header:hover {
      background: rgba(255, 255, 255, 0.04);
    }

    /* Timeline dot — positioned inline (not absolute) */
    .timeline-dot {
      flex-shrink: 0;
      width: 14px;
      text-align: center;
      font-size: 0.7rem;
      color: rgba(255, 255, 255, 0.4);
    }

    /* Icon colors by type */
    .timeline-thinking .timeline-dot { color: #d2a83a; }
    .timeline-call .timeline-dot { color: #58a6ff; }
    .timeline-content .timeline-dot { color: #3fb950; }
    .timeline-success .timeline-dot { color: #3fb950; }
    .timeline-error .timeline-dot { color: #f85149; }

    /* Timeline label */
    .timeline-label {
      flex: 1;
      color: rgba(255, 255, 255, 0.7);
      font-size: 0.72rem;
    }

    .timeline-label strong {
      color: rgba(255, 255, 255, 0.9);
      font-weight: 600;
    }

    .timeline-error-label {
      color: #f85149;
    }

    .timeline-time {
      font-size: 0.62rem;
      color: rgba(255, 255, 255, 0.25);
      font-family: monospace;
    }

    /* Toggle chevron */
    .timeline-toggle {
      font-size: 0.6rem;
      color: rgba(255, 255, 255, 0.25);
      flex-shrink: 0;
    }

    .timeline-toggle i.expanded {
      transform: rotate(90deg);
      transition: transform 0.2s;
    }

    /* Timeline body — expanded content */
    .timeline-body {
      padding: 4px 8px 8px 8px;
      background: rgba(0, 0, 0, 0.2);
      border-top: 1px solid rgba(255, 255, 255, 0.04);
    }

    /* JSON display */
    .timeline-json {
      font-family: 'Cascadia Code', 'Fira Code', monospace;
      font-size: 0.65rem;
      line-height: 1.4;
      color: rgba(255, 255, 255, 0.5);
      white-space: pre-wrap;
      word-break: break-word;
      margin: 0;
      max-height: 400px;
      overflow-y: auto;
    }

    /* Thinking text */
    .timeline-thinking-text {
      color: rgba(210, 168, 58, 0.75);
      font-style: italic;
      font-size: 0.72rem;
      line-height: 1.5;
      white-space: pre-line;
      word-break: break-word;
    }

    /* Live cursor — blinks at end of streaming text */
    .live-cursor {
      animation: cursorBlink 0.6s step-end infinite;
      color: #fc6767;
      font-weight: bold;
      margin-left: 1px;
    }

    @keyframes cursorBlink {
      0%, 100% { opacity: 1; }
      50% { opacity: 0; }
    }

    /* Live cursor dot — small pulsing dot in header */
    .live-cursor-dot {
      width: 6px;
      height: 6px;
      background: #fc6767;
      border-radius: 50%;
      flex-shrink: 0;
      animation: pulseDot 1s ease-in-out infinite;
    }

    @keyframes pulseDot {
      0%, 100% { opacity: 0.4; transform: scale(0.8); }
      50% { opacity: 1; transform: scale(1.1); }
    }

    /* Streaming item — subtle highlight */
    .timeline-item.streaming {
      background: rgba(252, 103, 103, 0.03);
    }

    /* Content text (final output) */
    .timeline-content-text {
      color: rgba(255, 255, 255, 0.8);
      font-size: 0.75rem;
      line-height: 1.55;
      white-space: pre-line;
      word-break: break-word;
      max-height: 500px;
      overflow-y: auto;
    }

    /* Empty state */
    .timeline-empty {
      font-size: 0.65rem;
      color: rgba(255, 255, 255, 0.25);
      font-style: italic;
    }

    /* Pending shimmer */
    .timeline-pending {
      padding: 6px 0 6px 24px;
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
      width: 100%;
      box-sizing: border-box;
    }

    /* Payload collapsible sections */
    .payload-section {
      margin-bottom: 6px;
      border: 1px solid rgba(255, 255, 255, 0.06);
      background: rgba(255, 255, 255, 0.02);
      width: 100%;
      box-sizing: border-box;
      overflow: hidden;
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
      box-sizing: border-box;
    }

    .section-toggle:hover {
      background: rgba(255, 255, 255, 0.04);
    }

    .toggle-icon {
      color: #fc6767;
      font-size: 0.7rem;
      flex-shrink: 0;
    }
    .toggle-icon i.expanded {
      transform: rotate(180deg);
      transition: transform 0.2s;
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
      padding: 12px 0;
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
export class BriefAnalyzeLlmProgressComponent {
  @Input() visible = false;
  @Input() title = 'LLM Processing'; // Set by parent with i18n, English fallback
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
  rawResponseContent = '';
  tokenStats: any = null;

  /** Build raw request JSON from accumulated stream data */
  get rawRequestJson(): string {
    if (!this.llmConfig && !this.systemPrompt) return '';
    try {
      const req: any = {
        model: this.llmConfig?.model || '',
        messages: [],
      };
      if (this.systemPrompt) {
        req.messages.push({ role: 'system', content: this.systemPrompt });
      }
      if (this.userPayloadInfo) {
        req.messages.push({ role: 'user', content: '(user message, ' + (this.userPayloadInfo.user_message_length || 0) + ' chars)' });
      }
      if (this.llmConfig) {
        req.temperature = this.llmConfig.temperature;
        req.max_tokens = this.llmConfig.max_tokens;
        if (this.llmConfig.top_p != null) req.top_p = this.llmConfig.top_p;
        if (this.llmConfig.top_k != null) req.top_k = this.llmConfig.top_k;
        if (this.llmConfig.min_p != null) req.min_p = this.llmConfig.min_p;
      }
      req.stream = true;
      req.tools = '(7 function definitions)';
      return JSON.stringify(req, null, 2);
    } catch {
      return '';
    }
  }

  /** Normalize token stats — backend may send keys with or without wrapper */
  get _normalizedStats(): any {
    if (!this.tokenStats) return null;
    return {
      model: this.tokenStats.model || this.llmConfig?.model || '',
      prompt_tokens: this.tokenStats.prompt_tokens ?? this.tokenStats.input_tokens ?? 0,
      completion_tokens: this.tokenStats.completion_tokens ?? this.tokenStats.output_tokens ?? 0,
      tokens_used: this.tokenStats.tokens_used ?? this.tokenStats.total_tokens ?? 0,
      latency_ms: this.tokenStats.latency_ms ?? 0,
      estimated_cost_usd: this.tokenStats.estimated_cost_usd ?? 0,
    };
  }

  // Stream tab — user-friendly format
  initEvents: BriefAnalyzeStreamMessage[] = [];
  accumulatedThinking = '';
  thinkingDone = false;
  accumulatedContent = '';
  lastError = '';

  /** Strip `<thinking>` tags and collapse excessive whitespace */
  get accumulatedThinkingClean(): string {
    return this.accumulatedThinking
      .replace(/<antThinking>|<\/antThinking>|<thinking>|<\/thinking>/gi, '')
      .replace(/\n\s*\n\s*\n/g, '\n\n')  // collapse 3+ blank lines to single blank
      .replace(/^[ \t]+$/gm, '')           // strip lines that are only whitespace
      .trim();
  }

  // State
  status: 'streaming' | 'complete' | 'error' = 'streaming';
  activeTab: 'stream' | 'prompt' | 'payload' = 'stream';
  streamCount = 0;
  sections = { systemPrompt: false, userMessage: false, rawRequest: false, rawResponse: false, tokenStats: false };

  get formattedCost(): string {
    const val = this._normalizedStats?.estimated_cost_usd || 0;
    if (val === 0) return '$0.0000';
    return `$${val.toFixed(4)}`;
  }

  jsonStr(obj: any): string {
    try { return JSON.stringify(obj, null, 2); } catch { return String(obj); }
  }

  /** Get a short argument preview for tool call header */
  getToolArgPreview(item: any): string {
    if (!item.arguments) return '';
    const args = item.arguments;
    if (args.section) return ` <span style="opacity:0.5">(${args.section})</span>`;
    if (args.yaml_content) return ` <span style="opacity:0.5">(${(args.yaml_content as string).length} chars)</span>`;
    if (args.query) return ` <span style="opacity:0.5">(${args.query})</span>`;
    return '';
  }

  /** Strip thinking tags and collapse excessive whitespace */
  private _cleanThinkingText(text: string): string {
    return text
      .replace(/<antThinking>|<\/antThinking>|<thinking>|<\/thinking>|<anthinking>|<\/anthinking>/gi, '')
      .replace(/\n\s*\n\s*\n/g, '\n\n')  // collapse 3+ blank lines to double
      .replace(/^[ \t]+$/gm, '')           // strip lines that are only whitespace
      .trim();
  }

  /** Strip thinking tags from content text */
  private _cleanContentText(text: string): string {
    return text
      .replace(/<antThinking>|<\/antThinking>|<thinking>|<\/thinking>|<anthinking>|<\/anthinking>/gi, '')
      .trim();
  }

  /** Show "Đang suy nghĩ..." whenever streaming is active AND no item is currently receiving chunks */
  get shouldShowPendingShimmer(): boolean {
    if (this.status !== 'streaming') return false;
    // Don't show shimmer if an item is already streaming (has live cursor)
    if (this.toolEvents.length > 0) {
      const last = this.toolEvents[this.toolEvents.length - 1];
      if (last.isStreaming) return false;
    }
    return true;
  }

  /** Merge consecutive thinking/content chunks into the last item of the same type */
  private _tryMerge(last: any, newChunk: any): boolean {
    if (last.type !== newChunk.type) return false;
    if (last.type === 'thinking') {
      const cleaned = this._cleanThinkingText(newChunk.text);
      if (!cleaned) return true;  // Merge (swallow) empty chunk
      last.text = this._cleanThinkingText(last.text + cleaned);
      last.isStreaming = true;
      return true;
    }
    if (last.type === 'content') {
      const cleaned = this._cleanContentText(newChunk.text);
      if (!cleaned) return true;  // Merge (swallow) empty chunk
      last.text = this._cleanContentText(last.text + cleaned);
      last.isStreaming = true;
      return true;
    }
    return false;
  }

  /** Mark the previously active item as no longer streaming */
  private _stopStreamingOnLast(): void {
    if (this.toolEvents.length > 0) {
      const last = this.toolEvents[this.toolEvents.length - 1];
      if (last.isStreaming) {
        last.isStreaming = false;
      }
    }
  }

  /** Truncate deeply nested objects for display — keeps structure but limits array/object depth */
  private _truncateForDisplay(obj: any, maxDepth: number = 3, maxItems: number = 5): any {
    if (obj === null || obj === undefined) return obj;
    if (typeof obj !== 'object') return obj;

    if (Array.isArray(obj)) {
      if (obj.length > maxItems) {
        return obj.slice(0, maxItems).map(item =>
          typeof item === 'object' && item ? this._truncateForDisplay(item, maxDepth - 1, maxItems) : item
        ).concat(`... (${obj.length - maxItems} more items)`);
      }
      return obj.map(item =>
        typeof item === 'object' && item ? this._truncateForDisplay(item, maxDepth - 1, maxItems) : item
      );
    }

    if (maxDepth <= 0) {
      const keys = Object.keys(obj);
      if (keys.length > maxItems) {
        const shown: any = {};
        keys.slice(0, maxItems).forEach(k => shown[k] = obj[k]);
        return { ...shown, [`... (${keys.length - maxItems} more keys)`]: '...' };
      }
      return { ...obj };
    }

    const result: any = {};
    for (const [key, value] of Object.entries(obj)) {
      result[key] = typeof value === 'object' && value
        ? this._truncateForDisplay(value, maxDepth - 1, maxItems)
        : value;
    }
    return result;
  }

  /** Unwrap SSE data: handles both analyze brief format and contract gen format */
  private _extract(msg: BriefAnalyzeStreamMessage): { text: string; accumulated?: string } {
    if (typeof msg.data === 'string') return { text: msg.data };
    if (msg.data && typeof msg.data === 'object') {
      // Contract gen format: { text: "...", accumulated: "..." }
      // Analyze brief format: { data: "...", accumulated: "..." }
      return {
        text: (msg.data.text ?? msg.data.data ?? '') as string,
        accumulated: msg.data.accumulated,
      };
    }
    return { text: String(msg.data ?? '') };
  }

  // Tool-use state
  toolEvents: any[] = [];
  currentRepairRound = 0;
  maxRepairRounds = 10;
  private idleTimer: any = null;
  private lastMessageTime: number = Date.now();

  /** Xử lý message từ SSE stream */
  onMessage(msg: BriefAnalyzeStreamMessage): void {
    this.ngZone.run(() => {
      this.streamCount++;
      this.lastMessageTime = Date.now();

      // Check for idle timeout — warn if no data for > 2 minutes
      const idleMs = Date.now() - this.lastMessageTime;
      // (idle check is done by backend sending idle_warning event)

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
          break;

        case 'thinking': {
          const { text, accumulated } = this._extract(msg);
          const cleaned = this._cleanThinkingText(text);
          // Skip empty thinking chunks
          if (!cleaned) break;
          const chunk = { type: 'thinking' as const, text: cleaned, isStreaming: true, _expanded: true };
          // Merge with last thinking chunk
          if (this.toolEvents.length > 0) {
            const last = this.toolEvents[this.toolEvents.length - 1];
            if (!this._tryMerge(last, chunk)) {
              // Type switch — stop streaming on previous item
              this._stopStreamingOnLast();
              this.toolEvents.push(chunk);
            } else {
              last._expanded = true;
            }
          } else {
            this.toolEvents.push(chunk);
          }
          break;
        }

        case 'thinking_end':
          this.thinkingDone = true;
          this._stopStreamingOnLast();
          break;

        case 'content': {
          const { text, accumulated } = this._extract(msg);
          const cleaned = this._cleanContentText(text);
          // Skip empty content chunks
          if (!cleaned) break;
          const chunk = { type: 'content' as const, text: cleaned, isStreaming: true, _expanded: true };
          if (this.toolEvents.length > 0) {
            const last = this.toolEvents[this.toolEvents.length - 1];
            if (!this._tryMerge(last, chunk)) {
              // Type switch — stop streaming on previous item
              this._stopStreamingOnLast();
              this.toolEvents.push(chunk);
            } else {
              last._expanded = true;
            }
          } else {
            this.toolEvents.push(chunk);
          }
          break;
        }

        case 'tool_call':
          // LLM is calling a tool — stop streaming on previous item
          this._stopStreamingOnLast();
          // LLM is calling a tool — record timestamp for elapsed measurement
          this.toolEvents.push({
            type: 'call',
            name: msg.data?.name,
            arguments: msg.data?.arguments,
            duration: 0,
            _ts: Date.now(),  // client-side timestamp
          });
          break;

        case 'idle_warning':
          // Backend detected idle — log but continue waiting
          console.warn(`[LLM-PROGRESS] Idle warning: ${((msg.data?.idle_ms || 0) / 1000).toFixed(0)}s since last chunk`);
          break;

        case 'tool_result':
          // Tool returned result — stop streaming on previous item
          this._stopStreamingOnLast();
          // Tool returned result — MERGE into the last 'call' event
          const fullResult = msg.data?.full_result || msg.data?.summary || {};
          const truncated = this._truncateForDisplay(fullResult);
          const lastItem = this.toolEvents.length > 0 ? this.toolEvents[this.toolEvents.length - 1] : null;
          if (lastItem && lastItem.type === 'call' && lastItem.name === msg.data?.name) {
            // Merge into existing call item — compute client-side elapsed time
            lastItem.full_result = truncated;
            lastItem.summary = msg.data?.summary;
            lastItem.duration = Date.now() - (lastItem._ts || Date.now());
            delete lastItem._ts;
            lastItem.type = 'tool';  // Mark as complete call+result
            // Determine validity for icon display
            const s = msg.data?.summary || {};
            if (s.error || s.errors?.length > 0) {
              lastItem._valid = false;  // Has errors
            } else if (s.valid === true && s.yaml) {
              lastItem._valid = true;  // Validation passed
            }
            // For tools without valid field (get_dsl_section, etc.), _valid stays undefined → wrench icon
          } else {
            // Orphan result — push as standalone
            this.toolEvents.push({
              type: 'result',
              name: msg.data?.name,
              summary: msg.data?.summary,
              full_result: truncated,
              duration: msg.data?.duration_ms || 0,
            });
          }
          break;

        case 'repair_round':
          // Legacy — backend no longer sends this
          break;

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
    this.toolEvents = [];
    this.currentRepairRound = 0;
    this.maxRepairRounds = 10;
    this.lastMessageTime = Date.now();
    this._startIdleTimer();
  }

  /** Start periodic idle check — warn if no data for > 2 minutes */
  private _startIdleTimer(): void {
    this._stopIdleTimer();
    this.idleTimer = setInterval(() => {
      if (this.status === 'complete' || this.status === 'error') {
        this._stopIdleTimer();
        return;
      }
      const idleMs = Date.now() - this.lastMessageTime;
      if (idleMs > 180000) {
        // > 3 minutes idle — show error in stream
        console.error(`[LLM-PROGRESS] Stream stalled for ${(idleMs / 1000).toFixed(0)}s — connection likely dropped`);
        this.status = 'error';
        this.lastError = 'Stream stalled — LLM connection may have been dropped. Please try again.';
        this._stopIdleTimer();
      }
    }, 10000);  // Check every 10 seconds
  }

  private _stopIdleTimer(): void {
    if (this.idleTimer) {
      clearInterval(this.idleTimer);
      this.idleTimer = null;
    }
  }
}
