/**
 * Component IR Explorer
 * Hiển thị MIR và Symbol Table
 */

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { MockApiService } from '../../core/mock-api.service';

@Component({
  selector: 'app-ir-explorer',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="container mx-auto px-6 py-8">
      <!-- Header -->
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold">Khám phá IR</h1>
          <p class="text-text-secondary mt-1">Khám phá MIR và Symbol Table</p>
        </div>
        <button (click)="handleBuild()" class="btn btn-primary" [disabled]="isBuilding">
          {{ isBuilding ? 'Đang tải...' : 'Build IR' }}
        </button>
      </div>

      <!-- Success Message -->
      @if (successMessage) {
        <div class="mb-4 p-3 bg-accent-success bg-opacity-10 border border-accent-success rounded text-accent-success">
          {{ successMessage }}
        </div>
      }

      <!-- MIR Data -->
      @if (mirData) {
        <div class="grid grid-cols-2 gap-6">
          <!-- MIR -->
          <div class="card">
            <h2 class="font-semibold mb-4 text-accent-primary">MIR</h2>
            
            <!-- Metadata -->
            <div class="mb-4 space-y-2 text-sm">
              <div><span class="text-text-tertiary">Schema:</span> <span class="text-text-primary">{{ mirData?.schema }}</span></div>
              <div><span class="text-text-tertiary">Version:</span> <span class="text-text-primary">{{ mirData?.version }}</span></div>
              <div><span class="text-text-tertiary">Generated:</span> <span class="text-text-primary">{{ mirData?.generated_at }}</span></div>
            </div>

            <!-- Modules -->
            <h3 class="font-medium text-sm text-text-secondary mb-2">Modules</h3>
            @if (mirData?.modules) {
              <div class="space-y-2">
                @for (module of mirData?.modules; track module.name) {
                  <div class="p-3 bg-bg-secondary rounded">
                    <div class="font-medium text-accent-primary">{{ module.name }}</div>
                    @if (module.entities) {
                      <div class="mt-2">
                        <span class="text-xs text-text-tertiary">Entities:</span>
                        <div class="flex flex-wrap gap-1 mt-1">
                          @for (entity of module.entities; track entity.id) {
                            <span class="text-xs bg-bg-tertiary px-2 py-1 rounded">{{ entity.name }}</span>
                          }
                        </div>
                      </div>
                    }
                  </div>
                }
              </div>
            }

            <!-- Raw MIR -->
            <details class="mt-4">
              <summary class="text-sm text-accent-primary cursor-pointer">Xem raw JSON</summary>
              <pre class="mt-2 text-xs text-text-secondary overflow-auto max-h-64 p-2 bg-bg-tertiary rounded">{{ mirData | json }}</pre>
            </details>
          </div>

          <!-- Symbol Table -->
          <div class="card">
            <h2 class="font-semibold mb-4 text-accent-primary">Bảng ký hiệu</h2>
            
            <div class="space-y-3">
              <!-- Product Entity -->
              <div class="p-3 bg-bg-secondary rounded">
                <div class="font-medium text-accent-primary mb-2">Product</div>
                <div class="space-y-1 text-sm">
                  <div class="flex justify-between">
                    <span class="text-text-tertiary">id</span>
                    <span class="text-text-secondary">uuid</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-text-tertiary">sku</span>
                    <span class="text-text-secondary">string</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-text-tertiary">name</span>
                    <span class="text-text-secondary">string</span>
                  </div>
                </div>
              </div>

              <!-- Order Entity -->
              <div class="p-3 bg-bg-secondary rounded">
                <div class="font-medium text-accent-primary mb-2">Order</div>
                <div class="space-y-1 text-sm">
                  <div class="flex justify-between">
                    <span class="text-text-tertiary">id</span>
                    <span class="text-text-secondary">uuid</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-text-tertiary">order_number</span>
                    <span class="text-text-secondary">string</span>
                  </div>
                </div>
              </div>

              <!-- Tenant Entity -->
              <div class="p-3 bg-bg-secondary rounded">
                <div class="font-medium text-accent-primary mb-2">Tenant</div>
                <div class="space-y-1 text-sm">
                  <div class="flex justify-between">
                    <span class="text-text-tertiary">id</span>
                    <span class="text-text-secondary">uuid</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-text-tertiary">name</span>
                    <span class="text-text-secondary">string</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      }

      <!-- Next Action -->
      <div class="mt-6 flex justify-end">
        <a routerLink="/code-generator" class="btn btn-primary">
          Mã nguồn →
        </a>
      </div>
    </div>
  `,
  styles: [],
})
export class IRExplorerComponent implements OnInit {
  mirData: any = null;
  isBuilding = false;
  successMessage = '';

  constructor(private mockApi: MockApiService) {}

  async ngOnInit(): Promise<void> {
    await this.loadMIR();
  }

  async loadMIR(): Promise<void> {
    const result = await this.mockApi.getMIR();
    if (result.success && result.data) {
      this.mirData = result.data;
    }
  }

  async handleBuild(): Promise<void> {
    this.isBuilding = true;
    this.successMessage = '';

    await this.mockApi.buildIR({ version: 'v1.0.0' });
    
    await this.loadMIR();
    
    this.successMessage = 'Build IR thành công';
    this.isBuilding = false;
  }
}