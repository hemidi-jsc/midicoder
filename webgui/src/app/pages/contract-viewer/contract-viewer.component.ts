/**
 * Component Contract Viewer
 * Hiển thị DSL contracts dưới dạng tree view
 */

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { MockApiService } from '../../core/mock-api.service';

@Component({
  selector: 'app-contract-viewer',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="container mx-auto px-6 py-8">
      <!-- Header -->
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold">Xem Hợp đồng</h1>
          <p class="text-text-secondary mt-1">Xem DSL contracts</p>
        </div>
        <div class="flex space-x-3">
          <button (click)="handleGenerate()" class="btn btn-primary" [disabled]="isGenerating">
            {{ isGenerating ? 'Đang tải...' : 'Tạo hợp đồng' }}
          </button>
          <button (click)="handleValidate()" class="btn btn-secondary" [disabled]="isValidating">
            {{ isValidating ? 'Đang tải...' : 'Xác thực' }}
          </button>
        </div>
      </div>

      <!-- Success Message -->
      @if (successMessage) {
        <div class="mb-4 p-3 bg-accent-success bg-opacity-10 border border-accent-success rounded text-accent-success">
          {{ successMessage }}
        </div>
      }

      <!-- Summary Stats -->
      @if (contractSummary) {
        <div class="grid grid-cols-5 gap-4 mb-6">
          <div class="card text-center">
            <div class="text-2xl font-bold text-accent-primary">{{ contractSummary?.entities }}</div>
            <div class="text-sm text-text-tertiary">Thực thể</div>
          </div>
          <div class="card text-center">
            <div class="text-2xl font-bold text-accent-primary">{{ contractSummary?.commands }}</div>
            <div class="text-sm text-text-tertiary">Lệnh</div>
          </div>
          <div class="card text-center">
            <div class="text-2xl font-bold text-accent-primary">{{ contractSummary?.queries }}</div>
            <div class="text-sm text-text-tertiary">Truy vấn</div>
          </div>
          <div class="card text-center">
            <div class="text-2xl font-bold text-accent-primary">{{ contractSummary?.events }}</div>
            <div class="text-sm text-text-tertiary">Sự kiện</div>
          </div>
          <div class="card text-center">
            <div class="text-2xl font-bold text-accent-primary">{{ contractSummary?.workflows }}</div>
            <div class="text-sm text-text-tertiary">Quy trình</div>
          </div>
        </div>
      }

      <!-- Contract Tree -->
      @if (contractIR) {
        <div class="grid grid-cols-3 gap-6">
          <!-- Entities -->
          <div class="card">
            <h3 class="font-semibold mb-4 text-accent-primary">Entities</h3>
            @if (contractIR?.entities?.length) {
              <div class="space-y-2">
                @for (entity of contractIR?.entities; track entity.name) {
                  <div class="p-2 bg-bg-secondary rounded">
                    <div class="font-medium text-sm">{{ entity.name }}</div>
                    <div class="text-xs text-text-tertiary">{{ entity.table }}</div>
                  </div>
                }
              </div>
            }
          </div>

          <!-- Commands -->
          <div class="card">
            <h3 class="font-semibold mb-4 text-accent-primary">Commands</h3>
            @if (contractIR?.commands?.length) {
              <div class="space-y-2">
                @for (cmd of contractIR?.commands; track cmd.name) {
                  <div class="p-2 bg-bg-secondary rounded">
                    <div class="font-medium text-sm">{{ cmd.name }}</div>
                  </div>
                }
              </div>
            } @else {
              <p class="text-sm text-text-tertiary">No commands defined</p>
            }
          </div>

          <!-- Queries -->
          <div class="card">
            <h3 class="font-semibold mb-4 text-accent-primary">Queries</h3>
            @if (contractIR?.queries?.length) {
              <div class="space-y-2">
                @for (query of contractIR?.queries; track query.name) {
                  <div class="p-2 bg-bg-secondary rounded">
                    <div class="font-medium text-sm">{{ query.name }}</div>
                  </div>
                }
              </div>
            } @else {
              <p class="text-sm text-text-tertiary">No queries defined</p>
            }
          </div>

          <!-- Events -->
          <div class="card">
            <h3 class="font-semibold mb-4 text-accent-primary">Events</h3>
            @if (contractIR?.events?.length) {
              <div class="space-y-2">
                @for (event of contractIR?.events; track event.name) {
                  <div class="p-2 bg-bg-secondary rounded">
                    <div class="font-medium text-sm">{{ event.name }}</div>
                  </div>
                }
              </div>
            } @else {
              <p class="text-sm text-text-tertiary">No events defined</p>
            }
          </div>

          <!-- Workflows -->
          <div class="card">
            <h3 class="font-semibold mb-4 text-accent-primary">Workflows</h3>
            @if (contractIR?.workflows?.length) {
              <div class="space-y-2">
                @for (workflow of contractIR?.workflows; track workflow.name) {
                  <div class="p-2 bg-bg-secondary rounded">
                    <div class="font-medium text-sm">{{ workflow.name }}</div>
                  </div>
                }
              </div>
            } @else {
              <p class="text-sm text-text-tertiary">No workflows defined</p>
            }
          </div>

          <!-- Raw JSON -->
          <div class="card">
            <h3 class="font-semibold mb-4 text-accent-primary">Raw JSON</h3>
            <pre class="text-xs text-text-secondary overflow-auto max-h-64">{{ contractIR | json }}</pre>
          </div>
        </div>
      }

      <!-- Next Action -->
      <div class="mt-6 flex justify-end">
        <a routerLink="/ir-explorer" class="btn btn-primary">
          IR →
        </a>
      </div>
    </div>
  `,
  styles: [],
})
export class ContractViewerComponent implements OnInit {
  contractIR: any = null;
  contractSummary: any = null;
  isGenerating = false;
  isValidating = false;
  successMessage = '';

  constructor(private mockApi: MockApiService) {}

  async ngOnInit(): Promise<void> {
    await this.loadContractIR();
  }

  async loadContractIR(): Promise<void> {
    const result = await this.mockApi.getContractIR();
    if (result.success && result.data) {
      this.contractIR = result.data;
    }
  }

  async handleGenerate(): Promise<void> {
    this.isGenerating = true;
    this.successMessage = '';

    const result = await this.mockApi.generateContract({ version: 'v1.0.0' });
    
    if (result.success && result.data) {
      this.contractSummary = result.data.summary;
      this.successMessage = 'Tạo hợp đồng thành công';
      await this.loadContractIR();
    }

    this.isGenerating = false;
  }

  async handleValidate(): Promise<void> {
    this.isValidating = true;
    
    await this.mockApi.checkContract({ version: 'v1.0.0', auto_fix: true });
    
    this.isValidating = false;
    this.successMessage = 'Contract validation passed';
  }
}