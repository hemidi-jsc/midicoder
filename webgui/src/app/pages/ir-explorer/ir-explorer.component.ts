/**
 * Component IR Explorer
 * Hiển thị MIR và Symbol Table
 */

import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';

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

            @if (symbolTable.length > 0) {
              <div class="space-y-3">
                @for (entity of symbolTable; track entity.name || entity.id || entity) {
                  <div class="p-3 bg-bg-secondary rounded">
                    <div class="font-medium text-accent-primary mb-2">{{ entity.name || entity.id || entity }}</div>
                    @if (entity.fields) {
                      <div class="space-y-1 text-sm">
                        @for (field of entity.fields; track field.name || field) {
                          <div class="flex justify-between">
                            <span class="text-text-tertiary">{{ field.name || field.field || field }}</span>
                            <span class="text-text-secondary">{{ field.type || field.field_type || '' }}</span>
                          </div>
                        }
                      </div>
                    }
                    @if (entity.properties) {
                      <div class="space-y-1 text-sm">
                        @for (prop of entity.properties; track $index) {
                          <div class="flex justify-between">
                            <span class="text-text-tertiary">{{ prop.name || prop }}</span>
                            <span class="text-text-secondary">{{ prop.type || '' }}</span>
                          </div>
                        }
                      </div>
                    }
                  </div>
                }
              </div>
            } @else {
              <p class="text-text-tertiary text-sm">Chưa có symbol table. Hãy build IR trước.</p>
            }
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
  symbolTable: any[] = [];
  isBuilding = false;
  successMessage = '';

  private api = inject(ApiService);

  async ngOnInit(): Promise<void> {
    await this.loadMIR();
    await this.loadSymbolTable();
  }

  async loadMIR(): Promise<void> {
    const result = await this.api.getMIR();
    if (result.success && result.data) {
      this.mirData = result.data;
    }
  }

  async loadSymbolTable(): Promise<void> {
    const result = await this.api.getSymbolTable();
    if (result.success && result.data) {
      // Symbol table có thể là array hoặc object { symbols: [...] }
      this.symbolTable = Array.isArray(result.data) ? result.data : (result.data.symbols || result.data.entities || Object.keys(result.data).map(k => ({ name: k, ...result.data[k] })));
    }
  }

  async handleBuild(): Promise<void> {
    this.isBuilding = true;
    this.successMessage = '';

    await this.api.buildIR({ skip_diagrams: false });

    await this.loadMIR();
    await this.loadSymbolTable();

    this.successMessage = 'Build IR thành công';
    this.isBuilding = false;
  }
}