import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { VersionService } from '../../../core/version.service';
import { ApiService } from '../../../core/api.service';
import { formatDateLocal } from '../../../core/date.util';

export interface ImpactInfo {
  will_archive: { version: string; status: string }[];
  will_delete: { version: string; status: string; created_at: string }[];
  max_versions: number;
  current_count: number;
  parent_version: string | null;
}

@Component({
  selector: 'app-version-create-form',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './version-create-form.html',
  styleUrls: ['./version-create-form.css'],
})
export class VersionCreateFormComponent {
  private versionService = inject(VersionService);
  private api = inject(ApiService);

  versionName = '';
  isCreating = false;
  createError = '';

  // Confirmation dialog state
  showConfirm = false;
  impact: ImpactInfo | null = null;
  isChecking = false;

  /** Number of existing versions — used to show/hide archive warning */
  @Input() existingVersionCount: number = 0;
  @Output() versionCreated = new EventEmitter<void>();
  @Output() cancel = new EventEmitter<void>();

  /** Parent version name (read-only) — fetched after click "Tạo" */
  getParentVersion(): string | null {
    return this.impact?.parent_version || null;
  }

  /** Step 1: Kiểm tra impact từ backend, hiện dialog confirm */
  async onCheckCreate(): Promise<void> {
    if (!this.versionName.trim()) return;

    this.isChecking = true;
    this.createError = '';

    try {
      const result = await this.api.checkCreateVersion(this.versionName.trim());
      if (result.success && result.data) {
        this.impact = result.data;
        this.showConfirm = true;
      } else {
        this.createError = result.message || 'Không thể kiểm tra trạng thái version';
      }
    } catch (error: any) {
      this.createError = error.message || 'Lỗi kết nối đến server';
    } finally {
      this.isChecking = false;
    }
  }

  /** Step 2: User xác nhận → tạo version thật sự */
  async onConfirmCreate(): Promise<void> {
    if (!this.versionName.trim()) return;

    this.isCreating = true;
    this.createError = '';

    try {
      await this.versionService.createVersion({ name: this.versionName.trim() });
      this.versionName = '';
      this.showConfirm = false;
      this.impact = null;
      this.versionCreated.emit();
    } catch (error: any) {
      this.createError = error.message || 'Tạo phiên bản thất bại';
    } finally {
      this.isCreating = false;
    }
  }

  onCancel(): void {
    this.cancel.emit();
  }

  onConfirmCancel(): void {
    this.showConfirm = false;
    this.impact = null;
  }

  /** Check nếu có impact cần confirm */
  get hasImpact(): boolean {
    if (!this.impact) return false;
    return this.impact.will_archive.length > 0 || this.impact.will_delete.length > 0;
  }

  /** Format datetime to local, return only date part "YYYY-MM-DD" */
  formatDateShort(iso: string): string {
    if (!iso) return '';
    return formatDateLocal(iso).split(' ')[0];
  }
}
