/**
 * Analyze Overlay Card — overlay lên brief editor khi đang phân tích
 * Hiển thị real-time LLM streaming: thinking, prompt, config, content, kết quả
 */

import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface StreamMessage {
  type: string;
  data: any;
  accumulated?: string;
}

@Component({
  selector: 'app-analyze-overlay',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="analyze-overlay-backdrop" (click)="close()">
      <div class="analyze-overlay-card" (click)="$event.stopPropagation()">
        <!-- Header -->
        <div class="overlay-header">
          <div class="overlay-title">
            <i class="fa-solid fa-brain"></i>
            <span>Phân tích Brief</span>
            @if (status === 'streaming') {
              <span class="status-badge status-streaming">
                <svg class="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Đang xử lý
              </span>
            } @else if (status === 'complete') {
              <span class="status-badge status-complete">Hoàn tất</span>
            } @else if (status === 'error') {
              <span class="status-badge status-error">Lỗi</span>
            }
          </div>
          <button class="close-btn" (click)="close()" title="Đóng">
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
            <i class="fa-solid fa-tty"></i> Stream
          </button>
          <button class="overlay-tab" [class.active]="activeTab === 'prompt'" (click)="activeTab = 'prompt'">
            <i class="fa-solid fa-scroll"></i> Prompt
          </button>
          <button class="overlay-tab" [class.active]="activeTab === 'payload'" (click)="activeTab = 'payload'">
            <i class="fa-solid fa-file-lines"></i> Payload
          </button>
          @if (status === 'complete' && finalResult) {
            <button class="overlay-tab" [class.active]="activeTab === 'result'" (click)="activeTab = 'result'">
              <i class="fa-solid fa-chart-bar"></i> Kết quả
            </button>
          }
        </div>

        <!-- Tab content -->
        <div class="overlay-content">

          <!-- Stream tab -->
          @if (activeTab === 'stream') {
            <div class="stream-panel" #streamPanel>
              @for (msg of displayedMessages; track msg) {
                @if (msg.type === 'thinking') {
                  <div class="stream-line stream-thinking">
                    <span class="stream-label"><i class="fa-solid fa-lightbulb"></i> thinking</span>
                    <span class="stream-text">{{ msg.data }}</span>
                  </div>
                } @else if (msg.type === 'thinking_end') {
                  <div class="stream-line stream-thinking-end">
                    <span class="stream-label"><i class="fa-solid fa-lightbulb"></i> /thinking</span>
                  </div>
                } @else if (msg.type === 'content') {
                  <div class="stream-line stream-content">
                    <span class="stream-label"><i class="fa-solid fa-terminal"></i> token</span>
                    <span class="stream-text">{{ msg.data }}</span>
                  </div>
                } @else if (msg.type === 'started') {
                  <div class="stream-line stream-info">
                    <span class="stream-label"><i class="fa-solid fa-play"></i> started</span>
                    <span class="stream-text">brief_id={{ msg.data?.brief_id }}, length={{ msg.data?.brief_length }}</span>
                  </div>
                } @else if (msg.type === 'context_injected') {
                  <div class="stream-line stream-info">
                    <span class="stream-label"><i class="fa-solid fa-inbox"></i> context</span>
                    <span class="stream-text">{{ msg.data?.token_count }} tokens ({{ msg.data?.query_time_ms }}ms)</span>
                  </div>
                } @else if (msg.type === 'error') {
                  <div class="stream-line stream-error">
                    <span class="stream-label"><i class="fa-solid fa-triangle-exclamation"></i> error</span>
                    <span class="stream-text">{{ msg.data }}</span>
                  </div>
                } @else if (msg.type === 'complete') {
                  <div class="stream-line stream-complete">
                    <span class="stream-label"><i class="fa-solid fa-check-circle"></i> complete</span>
                  </div>
                }
              }
            </div>
          }

          <!-- Prompt tab -->
          @if (activeTab === 'prompt') {
            <div class="prompt-panel">
              @if (systemPrompt) {
                <pre class="prompt-text">{{ systemPrompt }}</pre>
              } @else {
                <div class="empty-state">Chưa nhận được prompt</div>
              }
            </div>
          }

          <!-- Payload tab -->
          @if (activeTab === 'payload') {
            <div class="payload-panel">
              @if (userPayloadInfo) {
                <div class="payload-info">
                  <div class="payload-row">
                    <span class="payload-label">Brief length:</span>
                    <span class="payload-value">{{ userPayloadInfo.brief_length }} chars</span>
                  </div>
                  @if (userPayloadInfo.user_message_length) {
                    <div class="payload-row">
                      <span class="payload-label">User message length:</span>
                      <span class="payload-value">{{ userPayloadInfo.user_message_length }} chars</span>
                    </div>
                  }
                </div>
              } @else {
                <div class="empty-state">Chưa nhận được payload info</div>
              }
            </div>
          }

          <!-- Result tab -->
          @if (activeTab === 'result' && finalResult) {
            <div class="result-panel">
              <div class="result-header">
                <span class="result-domain">{{ finalResult.metadata?.domain }}</span>
                <span class="result-confidence" [class]="finalResult.metadata?.confidence >= 0.8 ? 'conf-high' : 'conf-low'">
                  {{ (finalResult.metadata?.confidence * 100).toFixed(0) }}%
                </span>
              </div>
              @if (finalResult.analysis?.summary) {
                <p class="result-summary">{{ finalResult.analysis.summary }}</p>
              }
              <div class="result-stats">
                <div class="stat-item">
                  <span class="stat-num">{{ finalResult.metadata?.entities }}</span>
                  <span class="stat-label">Entities</span>
                </div>
                <div class="stat-item">
                  <span class="stat-num">{{ finalResult.metadata?.commands }}</span>
                  <span class="stat-label">Commands</span>
                </div>
                <div class="stat-item">
                  <span class="stat-num">{{ finalResult.metadata?.queries }}</span>
                  <span class="stat-label">Queries</span>
                </div>
                <div class="stat-item">
                  <span class="stat-num">{{ finalResult.metadata?.events }}</span>
                  <span class="stat-label">Events</span>
                </div>
                <div class="stat-item">
                  <span class="stat-num">{{ finalResult.metadata?.ui_components }}</span>
                  <span class="stat-label">UI</span>
                </div>
              </div>
            </div>
          }
        </div>

        <!-- Footer -->
        <div class="overlay-footer">
          <span class="footer-text">
            @if (streamCount > 0) {
              {{ streamCount }} chunks đã nhận
            }
          </span>
          @if (status === 'complete') {
            <button class="btn btn-primary" (click)="close()">Đóng</button>
          } @else {
            <button class="btn btn-secondary" (click)="cancel()">Hủy</button>
          }
        </div>
      </div>
    </div>
  `,
  styles: [`
    .analyze-overlay-backdrop {
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

    .analyze-overlay-card {
      background: #16161e;
      border: 1px solid rgba(252, 103, 103, 0.25);
      width: 100%;
      max-width: 860px;
      max-height: 85vh;
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

    .status-badge {
      font-size: 0.6875rem;
      padding: 2px 8px;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }

    .status-streaming {
      background: rgba(56, 132, 255, 0.2);
      color: #58a6ff;
      border: 1px solid rgba(56, 132, 255, 0.3);
    }

    .status-complete {
      background: rgba(63, 185, 80, 0.2);
      color: #3fb950;
      border: 1px solid rgba(63, 185, 80, 0.3);
    }

    .status-error {
      background: rgba(248, 81, 73, 0.2);
      color: #f85149;
      border: 1px solid rgba(248, 81, 73, 0.3);
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
      min-height: 0;
    }

    /* Stream panel */
    .stream-panel {
      height: 360px;
      overflow-y: auto;
      padding: 10px 14px;
      font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
      font-size: 0.75rem;
      line-height: 1.7;
    }

    .stream-panel::-webkit-scrollbar {
      width: 5px;
    }

    .stream-panel::-webkit-scrollbar-thumb {
      background: rgba(252, 103, 103, 0.2);
    }

    .stream-line {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      padding: 2px 0;
    }

    .stream-label {
      flex-shrink: 0;
      width: 70px;
      font-size: 0.65rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      padding-top: 2px;
    }

    .stream-text {
      flex: 1;
      white-space: pre-wrap;
      word-break: break-all;
    }

    .stream-thinking .stream-label { color: #d2a83a; }
    .stream-thinking .stream-text { color: #d2a83a; font-style: italic; }

    .stream-thinking-end .stream-label { color: #d2a83a; }

    .stream-content .stream-label { color: #58a6ff; }
    .stream-content .stream-text { color: rgba(255, 255, 255, 0.75); }

    .stream-info .stream-label { color: #3fb950; }
    .stream-info .stream-text { color: rgba(255, 255, 255, 0.5); }

    .stream-error .stream-label { color: #f85149; }
    .stream-error .stream-text { color: #f85149; }

    .stream-complete .stream-label { color: #3fb950; }

    /* Prompt panel */
    .prompt-panel {
      height: 360px;
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
      padding: 14px;
    }

    .payload-info {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .payload-row {
      display: flex;
      justify-content: space-between;
      padding: 6px 10px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .payload-label {
      font-size: 0.8rem;
      color: rgba(255, 255, 255, 0.5);
    }

    .payload-value {
      font-size: 0.8rem;
      color: #fff;
      font-family: monospace;
    }

    /* Result panel */
    .result-panel {
      padding: 14px;
      max-height: 360px;
      overflow-y: auto;
    }

    .result-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 10px;
    }

    .result-domain {
      font-size: 0.85rem;
      font-weight: 600;
      color: #fc6767;
      text-transform: uppercase;
    }

    .result-confidence {
      font-size: 0.85rem;
      font-weight: 600;
    }

    .conf-high { color: #3fb950; }
    .conf-low { color: #d2a83a; }

    .result-summary {
      font-size: 0.8rem;
      color: rgba(255, 255, 255, 0.6);
      line-height: 1.5;
      margin: 0 0 12px 0;
    }

    .result-stats {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 8px;
    }

    .stat-item {
      text-align: center;
      padding: 8px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.06);
    }

    .stat-num {
      display: block;
      font-size: 1.25rem;
      font-weight: 700;
      color: #58a6ff;
    }

    .stat-label {
      font-size: 0.65rem;
      color: rgba(255, 255, 255, 0.4);
      text-transform: uppercase;
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
      padding: 10px 18px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      flex-shrink: 0;
    }

    .footer-text {
      font-size: 0.75rem;
      color: rgba(255, 255, 255, 0.4);
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
export class AnalyzeOverlayComponent {
  @Input() visible = false;
  @Output() closeOverlay = new EventEmitter<void>();
  @Output() cancelAnalyze = new EventEmitter<void>();

  // Data từ WebSocket
  systemPrompt = '';
  llmConfig: any = null;
  domain = '';
  userPayloadInfo: any = null;
  finalResult: any = null;
  accumulatedContent = '';

  // Stream messages (giới hạn 200 dòng)
  streamMessages: StreamMessage[] = [];
  get displayedMessages(): StreamMessage[] {
    return this.streamMessages.slice(-200);
  }

  // State
  status: 'streaming' | 'complete' | 'error' = 'streaming';
  activeTab: 'stream' | 'prompt' | 'payload' | 'result' = 'stream';
  streamCount = 0;

  /** Xử lý message từ WebSocket */
  onMessage(msg: StreamMessage): void {
    this.streamCount++;

    switch (msg.type) {
      case 'started':
        this.streamMessages.push(msg);
        break;
      case 'system_prompt':
        this.systemPrompt = typeof msg.data === 'string' ? msg.data : JSON.stringify(msg.data);
        this.streamMessages.push(msg);
        break;
      case 'llm_config':
        this.llmConfig = msg.data;
        break;
      case 'domain':
        this.domain = typeof msg.data === 'string' ? msg.data : String(msg.data);
        break;
      case 'context_injected':
        this.streamMessages.push(msg);
        break;
      case 'user_payload':
        this.userPayloadInfo = msg.data;
        break;
      case 'thinking':
      case 'thinking_end':
        this.streamMessages.push(msg);
        break;
      case 'content':
        this.accumulatedContent = msg.accumulated || this.accumulatedContent + (msg.data || '');
        this.streamMessages.push(msg);
        break;
      case 'complete':
        this.streamMessages.push(msg);
        this.status = 'complete';
        break;
      case 'final_result':
        this.finalResult = msg.data;
        this.status = 'complete';
        this.activeTab = 'result';
        break;
      case 'error':
        this.streamMessages.push(msg);
        this.status = 'error';
        break;
    }

    // Auto-scroll stream panel
    if (this.activeTab === 'stream') {
      setTimeout(() => {
        const panel = document.querySelector('.stream-panel');
        if (panel) panel.scrollTop = panel.scrollHeight;
      }, 0);
    }
  }

  close(): void {
    this.closeOverlay.emit();
  }

  cancel(): void {
    this.cancelAnalyze.emit();
    this.closeOverlay.emit();
  }

  /** Reset state */
  reset(): void {
    this.systemPrompt = '';
    this.llmConfig = null;
    this.domain = '';
    this.userPayloadInfo = null;
    this.finalResult = null;
    this.accumulatedContent = '';
    this.streamMessages = [];
    this.status = 'streaming';
    this.activeTab = 'stream';
    this.streamCount = 0;
  }
}
