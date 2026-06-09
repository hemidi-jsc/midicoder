import { Component, Input, OnInit, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/api.service';

@Component({
  selector: 'app-project-create-form',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './project-create-form.html',
  styleUrls: ['./project-create-form.css'],
})
export class ProjectCreateFormComponent {
  private api = inject(ApiService);

  // When true, render inside a modal overlay (for sidebar use)
  @Input() useModal = false;
  @Output() cancel = new EventEmitter<void>();

  // Form fields
  projectName = '';
  projectPath = '';
  projectPathPlaceholder = 'D:\\projects\\my-app';

  // Tech stack
  isLoadedTechStacks = false;
  techStackOptions = {
    infrastructure: [{ value: '', label: '' }],
    backend: [{ value: '', label: '' }],
    frontend: [{ value: '', label: '' }],
    ui_framework: [{ value: '', label: '' }],
  };
  stackSelection = {
    infrastructure: 'infrastructure',
    backend: 'fastapi',
    frontend: 'angular',
    ui_framework: 'carbon',
  };
  promptDomains: { value: string; label: string }[] = [{ value: 'default', label: 'Default' }];
  selectedPromptDomain = 'default';

  // State
  isCreating = false;
  createError = '';

  @Output() projectCreated = new EventEmitter<void>();

  get isFormValid(): boolean {
    return !!(
      this.projectName.trim() &&
      this.projectPath.trim() &&
      this.stackSelection.infrastructure &&
      this.stackSelection.backend &&
      this.stackSelection.frontend &&
      this.stackSelection.ui_framework &&
      this.selectedPromptDomain
    );
  }

  ngOnInit(): void {
    this.loadTechStacks();
  }

  async loadTechStacks(): Promise<void> {
    try {
      const result = await this.api.getTechStacks();
      if (result.success && result.data?.stacks) {
        const s = result.data.stacks;
        this.techStackOptions.infrastructure = s.infrastructure || this.techStackOptions.infrastructure;
        this.techStackOptions.backend = s.backend || this.techStackOptions.backend;
        this.techStackOptions.frontend = s.frontend || this.techStackOptions.frontend;
        this.techStackOptions.ui_framework = s.ui_framework || this.techStackOptions.ui_framework;
        this.promptDomains = result.data.prompt_domains || this.promptDomains;
        this.isLoadedTechStacks = true;
      }
    } catch (e) {
      console.warn('Failed to load tech stacks:', e);
    }
  }

  async onCreate(): Promise<void> {
    if (!this.projectName.trim() || !this.projectPath.trim()) return;
    this.isCreating = true;
    this.createError = '';
    try {
      const result = await this.api.createProject({
        name: this.projectName.trim(),
        path: this.projectPath.trim(),
        tech_stack: { ...this.stackSelection },
        prompt_domain: this.selectedPromptDomain,
      });
      if (result.success) {
        this.projectCreated.emit();
        window.location.reload();
      } else {
        this.createError = result.message || 'Tạo project thất bại';
      }
    } catch (error: any) {
      this.createError = error.message || 'Tạo project thất bại';
    } finally {
      this.isCreating = false;
    }
  }

  reset(): void {
    this.projectName = '';
    this.projectPath = '';
    this.createError = '';
  }

  onCancel(): void {
    this.cancel.emit();
  }
}
