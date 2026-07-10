/**
 * Contract Generation Progress Overlay — dedicated to contract category generation.
 * Single unified timeline with accordion items. Tokens stream in real-time.
 * Each item is collapsed by default, except thinking and streaming output which auto-expand.
 */

import { Component, Input, Output, EventEmitter, inject, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface ContractStreamMessage {
  type: string;
  data: any;
}

export interface TaskStage {
  id: string;
  label: string;
  icon: string;
  status: 'pending' | 'active' | 'done' | 'error';
  duration_ms?: number;
  startedAt?: number;
  summary?: string;
}

const MAX_PREVIEW_CHARS = 200;

@Component({
  selector: 'app-contract-gen-progress',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (visible) {
    <div class="cgp-backdrop">
      <div class="cgp-card" (click)="$event.stopPropagation()">

        <!-- Header -->
        <div class="cgp-header">
          <div class="cgp-title">
            <i class="fa-solid fa-file-contract"></i>
            <span>{{ title }}</span>
          </div>
          <button class="cgp-close-btn" (click)="close()">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>

        <!-- Info bar -->
        @if (llmConfig) {
          <div class="cgp-info-bar">
            <span class="cgp-info-item"><i class="fa-solid fa-server"></i> {{ llmConfig.model }}</span>
            @if (llmConfig.temperature != null) {
              <span class="cgp-info-item"><i class="fa-solid fa-temperature-half"></i> T={{ llmConfig.temperature }}</span>
            }
            @if (llmConfig.max_tokens) {
              <span class="cgp-info-item"><i class="fa-solid fa-cubes"></i> max={{ llmConfig.max_tokens }}</span>
            }
          </div>
        }

        <!-- Stage Progress -->
        <div class="cgp-stages">
          @for (stage of stages; track stage.id) {
            <div class="cgp-stage" [class]="getStageClass(stage)">
              <div class="cgp-stage-icon">
                @if (stage.status === 'done') { <i class="fa-solid fa-circle-check"></i> }
                @else if (stage.status === 'error') { <i class="fa-solid fa-circle-xmark"></i> }
                @else if (stage.status === 'active') { <i class="fa-solid fa-spinner fa-spin"></i> }
                @else { <i class="fa-solid {{ stage.icon }}"></i> }
              </div>
              <div class="cgp-stage-label">{{ stage.label }}</div>
              @if (stage.duration_ms != null) {
                <div class="cgp-stage-duration">{{ (stage.duration_ms / 1000).toFixed(1) }}s</div>
              }
            </div>
          }
        </div>

        <!-- Tabs -->
        <div class="cgp-tabs">
          <button class="cgp-tab" [class.active]="activeTab === 'stream'" (click)="activeTab = 'stream'">
            <i class="fa-solid fa-tty"></i> Stream
          </button>
          <button class="cgp-tab" [class.active]="activeTab === 'prompt'" (click)="activeTab = 'prompt'">
            <i class="fa-solid fa-scroll"></i> Prompt
          </button>
          <button class="cgp-tab" [class.active]="activeTab === 'payload'" (click)="activeTab = 'payload'">
            <i class="fa-solid fa-file-lines"></i> Payload
          </button>
        </div>

        <!-- Content -->
        <div class="cgp-content">

          <!-- Stream tab — unified timeline -->
          @if (activeTab === 'stream') {
            <div class="cgp-stream-panel" #streamPanel>

              <!-- Single unified timeline -->
              @for (item of timelineItems; track item) {
                <div class="cgp-timeline-item"
                     [class]="getItemClass(item)">
                  <button class="cgp-header" (click)="toggleItem(item)">
                    <span class="cgp-dot">
                      @if (item.type === 'thinking') { <i class="fa-solid fa-brain"></i> }
                      @else if (item.type === 'content') { <i class="fa-solid fa-file-code"></i> }
                      @else if (item.type === 'call' || item.type === 'tool') {
                        @if (item._valid === true) { <i class="fa-solid fa-circle-check"></i> }
                        @else if (item._valid === false) { <i class="fa-solid fa-circle-xmark"></i> }
                        @else { <i class="fa-solid fa-wrench"></i> }
                      }
                      @else if (item.type === 'error') { <i class="fa-solid fa-triangle-exclamation"></i> }
                      @else { <i class="fa-solid fa-circle"></i> }
                    </span>
                    <span class="cgp-label" [innerHTML]="getItemLabel(item)"></span>
                    <span class="cgp-preview">{{ getPreview(item) }}</span>
                    @if (item.isStreaming) {
                      <span class="cgp-cursor-dot"></span>
                    }
                    @if (item.duration != null) {
                      <span class="cgp-duration">{{ item.duration }}ms</span>
                    }
                    <span class="cgp-chevron"><i class="fa-solid fa-chevron-right" [class.expanded]="item._expanded"></i></span>
                  </button>
                  @if (item._expanded) {
                    <div class="cgp-body">
                      @if (item.type === 'thinking') {
                        <pre class="cgp-think-text">{{ item.text }}@if (item.isStreaming) {<span class="cgp-cursor">|</span>}</pre>
                      }
                      @if (item.type === 'content') {
                        <pre class="cgp-content-text">{{ item.text }}@if (item.isStreaming) {<span class="cgp-cursor">|</span>}</pre>
                      }
                      @if (item.type === 'tool' || item.type === 'call') {
                        @if (item.arguments) {
                          <div class="cgp-sublabel">Params:</div>
                          <pre class="cgp-json">{{ jsonStr(item.arguments) }}</pre>
                        }
                        @if (item.full_result) {
                          <div class="cgp-sublabel">Result:</div>
                          <pre class="cgp-json">{{ jsonStr(item.full_result) }}</pre>
                        }
                      }
                      @if (item.type === 'error') {
                        <pre class="cgp-error-text">{{ item.text }}</pre>
                      }
                    </div>
                  }
                </div>
              }

              <!-- Pending shimmer -->
              @if (shouldShowPendingShimmer) {
                <div class="cgp-pending"><span class="cgp-pending-text">Đang xử lý...</span></div>
              }

            </div>
          }

          <!-- Prompt tab -->
          @if (activeTab === 'prompt') {
            <div class="cgp-prompt-panel">
              @if (systemPrompt) {
                <pre class="cgp-prompt-text">{{ systemPrompt }}</pre>
              }
              @if (!systemPrompt) {
                <div class="cgp-empty">Chưa có prompt</div>
              }
            </div>
          }

          <!-- Payload tab -->
          @if (activeTab === 'payload') {
            <div class="cgp-payload-panel">
              <div class="cgp-payload-section">
                <button class="cgp-section-toggle" (click)="sections.rawResponse = !sections.rawResponse">
                  <i class="fa-solid fa-chevron-down" [class.cgp-rotated]="sections.rawResponse"></i>
                  Raw Response
                  @if (rawResponseContent) { <span class="cgp-section-size">{{ rawResponseContent.length }} chars</span> }
                </button>
                @if (sections.rawResponse && rawResponseContent) {
                  <pre class="cgp-payload-text">{{ rawResponseContent }}</pre>
                }
              </div>
              <div class="cgp-payload-section">
                <button class="cgp-section-toggle" (click)="sections.tokenStats = !sections.tokenStats">
                  <i class="fa-solid fa-chevron-down" [class.cgp-rotated]="sections.tokenStats"></i>
                  Token Stats
                </button>
                @if (sections.tokenStats && tokenStats) {
                  <div class="cgp-stats-grid">
                    <div class="cgp-stat"><span class="cgp-stat-label">Model</span><span class="cgp-stat-val">{{ tokenStats.model || llmConfig?.model || 'N/A' }}</span></div>
                    <div class="cgp-stat"><span class="cgp-stat-label">Prompt</span><span class="cgp-stat-val">{{ tokenStats.prompt_tokens || 0 }}</span></div>
                    <div class="cgp-stat"><span class="cgp-stat-label">Completion</span><span class="cgp-stat-val">{{ tokenStats.completion_tokens || 0 }}</span></div>
                    <div class="cgp-stat"><span class="cgp-stat-label">Total</span><span class="cgp-stat-val">{{ tokenStats.total_tokens || 0 }}</span></div>
                    <div class="cgp-stat"><span class="cgp-stat-label">Latency</span><span class="cgp-stat-val">{{ tokenStats.latency_ms || 0 }}ms</span></div>
                  </div>
                }
              </div>
            </div>
          }
        </div>

        <!-- Footer -->
        <div class="cgp-footer">
          <span class="cgp-footer-text">
            @if (status === 'streaming') {
              <svg class="cgp-spinner" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            }
            @if (streamCount > 0) { {{ streamCount }} chunks }
            @if (streamCount === 0 && status === 'streaming') { Connecting... }
          </span>
          <div class="cgp-footer-actions">
            <button class="btn btn-secondary" (click)="cancel()">
              {{ status === 'streaming' ? 'Cancel' : 'Close' }}
            </button>
          </div>
        </div>
      </div>
    </div>
    }
  `,
  styles: [`
    .cgp-backdrop {
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

    .cgp-card {
      background: #16161e;
      border: 1px solid rgba(252, 103, 103, 0.25);
      width: 100%;
      max-width: 860px;
      height: 80vh;
      display: flex;
      flex-direction: column;
      box-shadow: 0 0 40px rgba(252, 103, 103, 0.15);
    }

    /* Header */
    .cgp-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 18px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      flex-shrink: 0;
    }
    .cgp-title {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 1rem;
      font-weight: 600;
      color: #fff;
    }
    .cgp-title i { color: #fc6767; }
    .cgp-close-btn {
      background: none;
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: rgba(255, 255, 255, 0.5);
      font-size: 1rem;
      padding: 4px 10px;
      cursor: pointer;
      transition: all 0.2s;
    }
    .cgp-close-btn:hover { color: #fff; border-color: #fc6767; }

    /* Info bar */
    .cgp-info-bar {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 8px 18px;
      background: rgba(255, 255, 255, 0.03);
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      flex-shrink: 0;
      flex-wrap: wrap;
    }
    .cgp-info-item {
      font-size: 0.75rem;
      color: rgba(255, 255, 255, 0.6);
      display: flex;
      align-items: center;
      gap: 4px;
      font-family: monospace;
    }
    .cgp-info-item i { color: #fc6767; font-size: 0.7rem; }

    /* Stage Progress */
    .cgp-stages {
      display: flex;
      align-items: stretch;
      gap: 0;
      padding: 16px 24px;
      background: rgba(0, 0, 0, 0.3);
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      flex-shrink: 0;
    }
    .cgp-stage {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-start;
      position: relative;
      padding-top: 16px;
      padding-bottom: 16px;
    }
    /* Connector line between stages — from right edge of current icon to left edge of next icon */
    .cgp-stage:not(:last-child)::after {
      content: '';
      position: absolute;
      left: calc(50% + 17px);
      top: 33px;
      width: calc(100% - 34px);
      height: 3px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 2px;
    }
    .cgp-stage-icon {
      width: 34px;
      height: 34px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.9rem;
      background: rgba(255, 255, 255, 0.04);
      color: rgba(255, 255, 255, 0.25);
      z-index: 1;
      border: 2px solid rgba(255, 255, 255, 0.08);
      transition: all 0.3s;
    }
    .cgp-stage.active .cgp-stage-icon {
      background: rgba(58, 144, 217, 0.15);
      color: #58a6ff;
      border-color: rgba(58, 144, 217, 0.5);
      box-shadow: 0 0 12px rgba(58, 144, 217, 0.3);
    }
    .cgp-stage.done .cgp-stage-icon {
      background: rgba(63, 185, 80, 0.15);
      color: #3fb950;
      border-color: rgba(63, 185, 80, 0.5);
    }
    .cgp-stage.error .cgp-stage-icon {
      background: rgba(248, 81, 73, 0.15);
      color: #f85149;
      border-color: rgba(248, 81, 73, 0.5);
    }
    .cgp-stage-label {
      font-size: 0.7rem;
      color: rgba(255, 255, 255, 0.35);
      text-align: center;
      font-weight: 500;
    }
    .cgp-stage.active .cgp-stage-label { color: #58a6ff; font-weight: 600; }
    .cgp-stage.done .cgp-stage-label { color: #3fb950; }
    .cgp-stage.error .cgp-stage-label { color: #f85149; }
    .cgp-stage-duration {
      font-size: 0.6rem;
      color: rgba(255, 255, 255, 0.3);
      font-family: monospace;
    }

    /* Tabs */
    .cgp-tabs {
      display: flex;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      flex-shrink: 0;
    }
    .cgp-tab {
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
    .cgp-tab:hover { color: rgba(255, 255, 255, 0.7); }
    .cgp-tab.active { color: #fc6767; border-bottom: 2px solid #fc6767; }

    /* Content */
    .cgp-content {
      flex: 1;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      min-height: 0;
    }

    /* Stream panel */
    .cgp-stream-panel {
      flex: 1;
      height: 100%;
      overflow-y: auto;
      padding: 10px 14px;
      font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
      font-size: 0.78rem;
      line-height: 1.55;
      min-width: 0;
      box-sizing: border-box;
      background: #0d0d12;
      display: block;
    }
    .cgp-stream-panel::-webkit-scrollbar { width: 5px; }
    .cgp-stream-panel::-webkit-scrollbar-thumb { background: rgba(252, 103, 103, 0.2); }

    .cgp-init-line {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 2px 0;
      font-size: 0.7rem;
      color: rgba(255, 255, 255, 0.35);
    }
    .cgp-init-line i { color: #3fb950; font-size: 0.6rem; width: 12px; text-align: center; }

    .cgp-task-banner {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 10px;
      background: rgba(58, 144, 217, 0.08);
      border: 1px solid rgba(58, 144, 217, 0.2);
      font-size: 0.72rem;
      color: #58a6ff;
      animation: cgpFadeIn 0.3s ease-out;
    }
    .cgp-task-banner i { font-size: 0.7rem; }
    .cgp-task-num {
      margin-left: auto;
      font-family: monospace;
      font-size: 0.6rem;
      color: rgba(88, 166, 255, 0.6);
    }

    .cgp-task-done-banner {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 4px 10px;
      font-size: 0.65rem;
      color: #3fb950;
    }
    .cgp-task-done-banner i { font-size: 0.6rem; }

    .cgp-separator {
      border: none;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
      margin: 6px 0 8px 0;
    }

    /* Timeline items */
    .cgp-timeline-item {
      position: relative;
      margin: 2px 0;
      padding-left: 22px;
      animation: cgpFadeIn 0.3s ease-out;
      flex-shrink: 0;
    }
    @keyframes cgpFadeIn {
      from { opacity: 0; transform: translateX(-6px); }
      to { opacity: 1; transform: translateX(0); }
    }
    /* Vertical timeline line */
    .cgp-timeline-item::before {
      content: '';
      position: absolute;
      left: 4px;
      top: 4px;
      bottom: 4px;
      width: 3px;
      border-radius: 2px;
      background: rgba(255, 255, 255, 0.2);
    }
    .cgp-timeline-item.streaming::before { background: #fc6767; }
    .cgp-timeline-item.cgp-valid::before { background: #3fb950; }
    .cgp-timeline-item.cgp-invalid::before { background: #f85149; }
    .cgp-timeline-item.cgp-thinking::before { background: #d2a83a; }
    .cgp-timeline-item.cgp-content::before { background: #7ee787; }
    .cgp-timeline-item.cgp-error-item::before { background: #f85149; }

    .cgp-header {
      display: flex;
      align-items: center;
      gap: 10px;
      width: 100%;
      padding: 8px 10px;
      background: transparent;
      border: none;
      cursor: pointer;
      text-align: left;
      transition: background 0.15s;
      font-family: 'Cascadia Code', 'Fira Code', monospace;
      font-size: 0.78rem;
      border-radius: 3px;
    }
    .cgp-header:hover { background: rgba(255, 255, 255, 0.04); }

    .cgp-dot {
      flex-shrink: 0;
      width: 22px;
      height: 22px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.7rem;
      color: rgba(255, 255, 255, 0.5);
      background: rgba(255, 255, 255, 0.08);
      border: 2px solid rgba(255, 255, 255, 0.2);
    }
    .cgp-thinking .cgp-dot { color: #d2a83a; background: rgba(210,168,58,0.15); border-color: #d2a83a; }
    .cgp-content .cgp-dot { color: #7ee787; background: rgba(63,185,80,0.15); border-color: #7ee787; }
    .cgp-valid .cgp-dot { color: #3fb950; background: rgba(63,185,80,0.15); border-color: #3fb950; }
    .cgp-invalid .cgp-dot { color: #f85149; background: rgba(248,81,73,0.15); border-color: #f85149; }
    .cgp-error-item .cgp-dot { color: #f85149; background: rgba(248,81,73,0.15); border-color: #f85149; }

    .cgp-label {
      flex-shrink: 0;
      color: rgba(255, 255, 255, 0.75);
      font-size: 0.78rem;
      font-weight: 500;
    }
    .cgp-label strong { color: rgba(255, 255, 255, 0.9); font-weight: 600; }
    .cgp-error-label { color: #f85149; }

    .cgp-preview {
      flex: 1;
      font-size: 0.68rem;
      color: rgba(255, 255, 255, 0.3);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-style: italic;
      margin-left: 4px;
    }

    .cgp-time {
      font-size: 0.65rem;
      color: rgba(255, 255, 255, 0.3);
      font-family: monospace;
      flex-shrink: 0;
    }
    .cgp-duration {
      font-size: 0.65rem;
      color: rgba(255, 255, 255, 0.3);
      font-family: monospace;
      flex-shrink: 0;
    }

    .cgp-chevron {
      font-size: 0.6rem;
      color: rgba(255, 255, 255, 0.25);
      flex-shrink: 0;
    }
    .cgp-chevron i.expanded { transform: rotate(90deg); transition: transform 0.2s; }

    .cgp-body {
      padding: 0;
      background: transparent;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      width: 100%;
      box-sizing: border-box;
    }

    .cgp-json,
    .cgp-think-text,
    .cgp-content-text,
    .cgp-error-text {
      font-family: 'Cascadia Code', 'Fira Code', monospace;
      font-size: 0.75rem;
      font-weight: 400;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
      margin: 0;
      padding: 8px 10px 8px 14px;
      width: 100%;
      display: block;
      box-sizing: border-box;
    }

    .cgp-json {
      color: #c9d1d9;
      max-height: 400px;
      overflow-y: auto;
    }

    .cgp-think-text {
      color: #d2a83a;
      font-style: italic;
    }

    .cgp-content-text {
      color: #c9d1d9;
    }

    .cgp-error-text {
      color: #f85149;
    }

    .cgp-sublabel {
      font-size: 0.65rem;
      color: rgba(255, 255, 255, 0.35);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
    }

    /* Live cursor */
    .cgp-cursor {
      animation: cgpCursorBlink 0.6s step-end infinite;
      color: #fc6767;
      font-weight: bold;
      margin-left: 1px;
    }
    .cgp-live-cursor-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #fc6767;
      animation: cgpDotPulse 1s ease-in-out infinite;
      flex-shrink: 0;
    }
    @keyframes cgpCursorBlink { 0%,100%{opacity:1} 50%{opacity:0} }
    @keyframes cgpDotPulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.7)} }

    /* Pending shimmer */
    .cgp-pending {
      padding: 8px 0;
      animation: cgpShimmer 1.5s ease-in-out infinite;
      flex-shrink: 0;
    }
    .cgp-pending-text {
      font-size: 0.7rem;
      color: rgba(255, 255, 255, 0.3);
      font-style: italic;
    }
    @keyframes cgpShimmer { 0%,100%{opacity:0.3} 50%{opacity:1} }

    /* Prompt panel */
    .cgp-prompt-panel {
      height: 100%;
      overflow-y: auto;
      padding: 10px 14px;
    }
    .cgp-prompt-text {
      font-family: 'Cascadia Code', monospace;
      font-size: 0.72rem;
      color: rgba(255, 255, 255, 0.5);
      white-space: pre-wrap;
      word-break: break-word;
      line-height: 1.6;
    }

    /* Payload panel */
    .cgp-payload-panel {
      height: 100%;
      overflow-y: auto;
      padding: 10px 14px;
    }
    .cgp-payload-section {
      margin-bottom: 8px;
    }
    .cgp-section-toggle {
      display: flex;
      align-items: center;
      gap: 8px;
      width: 100%;
      padding: 6px 8px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.06);
      color: rgba(255, 255, 255, 0.6);
      font-size: 0.72rem;
      cursor: pointer;
      font-family: inherit;
      border-radius: 4px;
    }
    .cgp-section-toggle:hover { background: rgba(255, 255, 255, 0.06); }
    .cgp-toggle-icon i.expanded { transform: rotate(90deg); transition: transform 0.2s; }
    .cgp-section-size { margin-left: auto; font-size: 0.6rem; color: rgba(255,255,255,0.3); font-family: monospace; }
    .cgp-section-label { font-size: 0.65rem; color: rgba(255,255,255,0.4); margin-bottom: 4px; }
    .cgp-payload-body {
      padding: 6px 8px;
      background: rgba(0, 0, 0, 0.2);
    }
    .cgp-payload-text {
      font-family: 'Cascadia Code', monospace;
      font-size: 0.65rem;
      color: rgba(255, 255, 255, 0.5);
      white-space: pre-wrap;
      word-break: break-word;
      max-height: 400px;
      overflow-y: auto;
      margin: 0;
    }

    /* Stats grid */
    .cgp-stats-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .cgp-stat {
      display: flex;
      flex-direction: column;
      gap: 2px;
      padding: 8px;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 4px;
    }
    .cgp-stat-label { font-size: 0.62rem; color: rgba(255,255,255,0.4); }
    .cgp-stat-val { font-size: 0.8rem; color: rgba(255,255,255,0.8); font-family: monospace; font-weight: 600; }

    .cgp-empty {
      padding: 12px;
      text-align: center;
      color: rgba(255, 255, 255, 0.25);
      font-size: 0.72rem;
    }

    /* Footer */
    .cgp-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 18px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      flex-shrink: 0;
    }
    .cgp-footer-text {
      font-size: 0.72rem;
      color: rgba(255, 255, 255, 0.4);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .cgp-spinner {
      width: 16px;
      height: 16px;
      color: #fc6767;
    }
    .cgp-footer-actions { display: flex; gap: 8px; }

    .btn {
      padding: 6px 14px;
      font-size: 0.78rem;
      border: 1px solid rgba(255, 255, 255, 0.15);
      cursor: pointer;
      font-family: inherit;
      border-radius: 4px;
      transition: all 0.2s;
    }
    .btn-secondary {
      background: rgba(255, 255, 255, 0.06);
      color: rgba(255, 255, 255, 0.7);
    }
    .btn-secondary:hover { background: rgba(255, 255, 255, 0.12); }
  `],
})
export class ContractGenProgressComponent {
  private ngZone = inject(NgZone);
  private cdr = inject(ChangeDetectorRef);

  @Input() visible = false;
  @Input() title = 'Generating Contract';
  @Input() category = '';
  @Output() closeOverlay = new EventEmitter<void>();
  @Output() viewResult = new EventEmitter<void>();

  // Stage tracking
  stages: TaskStage[] = [
    { id: 'schema', label: 'Học Schema', icon: 'fa-book', status: 'pending' },
    { id: 'draft', label: 'Viết YAML', icon: 'fa-pen-to-square', status: 'pending' },
    { id: 'validate', label: 'Validate & Sửa', icon: 'fa-shield-halved', status: 'pending' },
    { id: 'final', label: 'Output Final', icon: 'fa-file-export', status: 'pending' },
  ];

  // State
  status: 'streaming' | 'complete' | 'error' = 'streaming';
  activeTab: 'stream' | 'prompt' | 'payload' = 'stream';
  streamCount = 0;
  lastError = '';
  systemPrompt = '';
  llmConfig: any = null;
  rawResponseContent = '';
  tokenStats: any = null;
  sections = { rawResponse: false, tokenStats: false };

  // Timeline items (merged thinking/content/tool)
  initEvents: ContractStreamMessage[] = [];
  timelineItems: any[] = [];
  private currentTaskId = '';

  // Idle detection
  private idleTimer: any = null;
  private lastMessageTime: number = Date.now();

  get shouldShowPendingShimmer(): boolean {
    if (this.status !== 'streaming') return false;
    if (this.timelineItems.length > 0) {
      const last = this.timelineItems[this.timelineItems.length - 1];
      if (last.isStreaming) return false;
    }
    return true;
  }

  getStageClass(stage: TaskStage): string {
    return `cgp-stage ${stage.status}`;
  }

  jsonStr(obj: any): string {
    try { return JSON.stringify(obj, null, 2); } catch { return String(obj); }
  }

  private _cleanText(text: string): string {
    // Only strip thinking tags — preserve all whitespace
    return text.replace(/<antThinking>|<\/antThinking>|<thinking>|<\/thinking>/gi, '');
  }

  private _stopStreamingOnLast(): void {
    if (this.timelineItems.length > 0) {
      const last = this.timelineItems[this.timelineItems.length - 1];
      if (last.isStreaming) last.isStreaming = false;
    }
  }

  private _truncateForDisplay(obj: any, maxDepth: number = 8, maxItems: number = 50): any {
    if (obj === null || obj === undefined || typeof obj !== 'object') return obj;
    if (Array.isArray(obj)) {
      return obj.slice(0, maxItems).map(i => typeof i === 'object' && i ? this._truncateForDisplay(i, maxDepth - 1, maxItems) : i);
    }
    if (maxDepth <= 0) return { ...obj };
    const result: any = {};
    for (const [k, v] of Object.entries(obj)) {
      result[k] = typeof v === 'object' && v ? this._truncateForDisplay(v, maxDepth - 1, maxItems) : v;
    }
    return result;
  }

  getItemClass(item: any): string {
    let cls = 'cgp-timeline-item';
    if (item.type === 'thinking') cls += ' cgp-thinking';
    if (item.type === 'content') cls += ' cgp-content';
    if (item._valid === true) cls += ' cgp-valid';
    if (item._valid === false) cls += ' cgp-invalid';
    if (item.type === 'error') cls += ' cgp-error-item';
    if (item.isStreaming) cls += ' streaming';
    return cls;
  }

  toggleItem(item: any): void {
    item._expanded = !item._expanded;
  }

  getItemLabel(item: any): string {
    if (item.type === 'thinking') return 'Suy nghĩ';
    if (item.type === 'content') return 'Output';
    if (item.type === 'call' || item.type === 'tool') {
      let label = `Tool: ${item.name || 'unknown'}`;
      if (item.arguments) {
        const args = item.arguments;
        // Show the most meaningful argument value
        if (args.section) label += ` <span style="opacity:0.5">(${args.section})</span>`;
        else if (args.yaml_content) label += ` <span style="opacity:0.5">(${(args.yaml_content as string).length} chars)</span>`;
        else if (args.query) label += ` <span style="opacity:0.5">(${args.query})</span>`;
      }
      return label;
    }
    if (item.type === 'error') return 'Lỗi';
    return item.type;
  }

  getPreview(item: any): string {
    if (!item.text) return '';
    const text = item.text.trim();
    if (text.length <= MAX_PREVIEW_CHARS) return '';
    return text.substring(0, MAX_PREVIEW_CHARS) + '...';
  }

  /** Get stage index by task id from backend */
  private _findStage(taskId: string): TaskStage | undefined {
    const map: Record<string, string> = {
      'learn_schema': 'schema',
      'schema': 'schema',
      'draft_yaml': 'draft',
      'draft': 'draft',
      'validate': 'validate',
      'validate_and_fix': 'validate',
      'final_review': 'final',
      'final': 'final',
    };
    return this.stages.find(s => s.id === map[taskId]);
  }

  onMessage(msg: ContractStreamMessage): void {
    this.ngZone.run(() => {
      this.streamCount++;
      this.lastMessageTime = Date.now();

      switch (msg.type) {
        case 'started':
          this.initEvents.push(msg);
          break;

        case 'system_prompt':
          this.systemPrompt = typeof msg.data === 'string' ? msg.data : JSON.stringify(msg.data);
          break;

        case 'llm_config':
          this.llmConfig = msg.data;
          break;

        case 'user_payload':
          break;

        case 'task_started': {
          // Backend sent task transition
          const stage = this._findStage(msg.data?.task || msg.data?.task_name || '');
          if (stage) {
            // Mark previous stage done
            this.stages.forEach(s => {
              if (s.status === 'active') {
                const dur = s.startedAt ? Date.now() - s.startedAt : 0;
                s.duration_ms = dur;
                s.status = 'done';
              }
            });
            stage.status = 'active';
            stage.startedAt = Date.now();
          }
          this.initEvents.push(msg);
          this._stopStreamingOnLast();
          break;
        }

        case 'task_completed': {
          const stage = this._findStage(msg.data?.task || msg.data?.task_name || '');
          if (stage && stage.status === 'active') {
            stage.duration_ms = stage.startedAt ? Date.now() - stage.startedAt : 0;
            stage.status = 'done';
            stage.summary = msg.data?.summary || 'Hoàn tất';
          }
          this.initEvents.push(msg);
          break;
        }

        case 'thinking': {
          const text = typeof msg.data === 'string' ? msg.data : (msg.data?.text || '');
          const cleaned = this._cleanText(text);
          if (!cleaned.trim()) break;
          const chunk = { type: 'thinking' as const, text: cleaned, isStreaming: true, _expanded: true };
          if (this.timelineItems.length > 0) {
            const last = this.timelineItems[this.timelineItems.length - 1];
            if (last.type === 'thinking') {
              last.text = this._cleanText(last.text + cleaned);
              last.isStreaming = true;
              last._expanded = true;
            } else {
              this._stopStreamingOnLast();
              this.timelineItems.push(chunk);
            }
          } else {
            this.timelineItems.push(chunk);
          }
          break;
        }

        case 'thinking_end':
          this._stopStreamingOnLast();
          break;

        case 'content': {
          const text = typeof msg.data === 'string' ? msg.data : (msg.data?.text || '');
          const cleaned = this._cleanText(text);
          if (!cleaned.trim()) break;
          const chunk = { type: 'content' as const, text: cleaned, isStreaming: true, _expanded: true };
          if (this.timelineItems.length > 0) {
            const last = this.timelineItems[this.timelineItems.length - 1];
            if (last.type === 'content') {
              last.text = this._cleanText(last.text + cleaned);
              last.isStreaming = true;
              last._expanded = true;
            } else {
              this._stopStreamingOnLast();
              this.timelineItems.push(chunk);
            }
          } else {
            this.timelineItems.push(chunk);
          }
          break;
        }

        case 'tool_call':
          this._stopStreamingOnLast();
          this.timelineItems.push({
            type: 'call',
            name: msg.data?.name,
            arguments: msg.data?.arguments,
            duration: 0,
            _ts: Date.now(),
          });
          break;

        case 'tool_result': {
          this._stopStreamingOnLast();
          // Don't truncate tool results — let CSS max-height handle display
          const fullResult = msg.data?.full_result || msg.data?.summary || {};
          const lastItem = this.timelineItems.length > 0 ? this.timelineItems[this.timelineItems.length - 1] : null;
          if (lastItem && lastItem.type === 'call' && lastItem.name === msg.data?.name) {
            lastItem.full_result = fullResult;
            lastItem.duration = Date.now() - (lastItem._ts || Date.now());
            delete lastItem._ts;
            lastItem.type = 'tool';
            const s = msg.data?.summary || {};
            if (s.error || (s.errors && s.errors > 0)) {
              lastItem._valid = false;
            } else if (s.valid === true) {
              lastItem._valid = true;
            }
          } else {
            this.timelineItems.push({
              type: 'tool',
              name: msg.data?.name,
              full_result: fullResult,
              duration: msg.data?.duration_ms || 0,
            });
          }
          break;
        }

        case 'heartbeat':
        case 'idle_warning':
          break;

        case 'complete':
          this.status = 'complete';
          this.tokenStats = msg.data;
          // Mark any remaining active stage as done
          this.stages.forEach(s => {
            if (s.status === 'active') {
              s.duration_ms = s.startedAt ? Date.now() - s.startedAt : 0;
              s.status = 'done';
            }
          });
          break;

        case 'final_content':
          this.rawResponseContent = typeof msg.data === 'string' ? msg.data : JSON.stringify(msg.data);
          break;

        case 'error':
          this.lastError = typeof msg.data === 'string' ? msg.data : JSON.stringify(msg.data);
          this.status = 'error';
          // Mark ALL stages as error (not just active) — the last active stage failed
          for (let i = this.stages.length - 1; i >= 0; i--) {
            if (this.stages[i].status === 'active' || this.stages[i].status === 'pending') {
              this.stages[i].status = 'error';
              break;
            }
          }
          break;
      }

      // Auto-scroll
      if (this.activeTab === 'stream') {
        setTimeout(() => {
          const panel = document.querySelector('.cgp-stream-panel');
          if (panel) panel.scrollTop = panel.scrollHeight;
        }, 16);
      }

      this.cdr.detectChanges();
    });
  }

  close(): void {
    if (this.status === 'streaming') {
      this.closeOverlay.emit();
    } else {
      this.closeOverlay.emit();
    }
  }

  cancel(): void {
    this.closeOverlay.emit();
  }

  reset(): void {
    this.systemPrompt = '';
    this.llmConfig = null;
    this.rawResponseContent = '';
    this.tokenStats = null;
    this.initEvents = [];
    this.timelineItems = [];
    this.lastError = '';
    this.status = 'streaming';
    this.activeTab = 'stream';
    this.streamCount = 0;
    this.sections = { rawResponse: false, tokenStats: false };
    this.lastMessageTime = Date.now();
    this.stages = [
      { id: 'schema', label: 'Học Schema', icon: 'fa-book', status: 'pending' },
      { id: 'draft', label: 'Viết YAML', icon: 'fa-pen-to-square', status: 'pending' },
      { id: 'validate', label: 'Validate & Sửa', icon: 'fa-shield-halved', status: 'pending' },
      { id: 'final', label: 'Output Final', icon: 'fa-file-export', status: 'pending' },
    ];
  }
}
