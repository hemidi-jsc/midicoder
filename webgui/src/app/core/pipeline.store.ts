/**
 * Store cho Pipeline state
 * Quản lý trạng thái của các phases trong pipeline
 * Dùng ApiService để kết nối với backend FastAPI thực
 */

import { Injectable, signal, computed, inject } from '@angular/core';
import { ApiService } from './api.service';
import { PipelineStatus } from './mock-api.service';

export type PhaseStatus = 'pending' | 'in_progress' | 'complete' | 'error';

export interface PhaseState {
  status: PhaseStatus;
  completedAt?: string;
  errorMessage?: string;
  currentStep?: string;
}

@Injectable({
  providedIn: 'root',
})
export class PipelineStore {
  private api = inject(ApiService);

  /**
   * States cho từng phase của pipeline
   */
  private initPhaseState = signal<PhaseState>({ status: 'pending' });
  private briefPhaseState = signal<PhaseState>({ status: 'pending' });
  private contractPhaseState = signal<PhaseState>({ status: 'pending' });
  private irPhaseState = signal<PhaseState>({ status: 'pending' });
  private codePhaseState = signal<PhaseState>({ status: 'pending' });
  private previewPhaseState = signal<PhaseState>({ status: 'pending' });

  /**
   * Project info
   */
  private projectName = signal<string>('');
  private activeVersion = signal<string>('');

  /**
   * Loading state
   */
  private isLoading = signal<boolean>(false);

  /**
   * Computed: overall progress percentage
   */
  readonly overallProgress = computed(() => {
    const phases = [
      this.initPhaseState(),
      this.briefPhaseState(),
      this.contractPhaseState(),
      this.irPhaseState(),
      this.codePhaseState(),
      this.previewPhaseState(),
    ];
    const completed = phases.filter((p) => p.status === 'complete').length;
    return Math.round((completed / phases.length) * 100);
  });

  /**
   * Computed: current phase name
   */
  readonly currentPhase = computed(() => {
    const phases: Array<{ name: string; state: PhaseState }> = [
      { name: 'init', state: this.initPhaseState() },
      { name: 'brief', state: this.briefPhaseState() },
      { name: 'contract', state: this.contractPhaseState() },
      { name: 'ir', state: this.irPhaseState() },
      { name: 'code', state: this.codePhaseState() },
      { name: 'preview', state: this.previewPhaseState() },
    ];
    for (const phase of phases) {
      if (phase.state.status !== 'complete' && phase.state.status !== 'error') {
        return phase.name;
      }
    }
    return null;
  });

  /**
   * Computed: is pipeline complete
   */
  readonly isComplete = computed(() => {
    return (
      this.initPhaseState().status === 'complete' &&
      this.briefPhaseState().status === 'complete' &&
      this.contractPhaseState().status === 'complete' &&
      this.irPhaseState().status === 'complete' &&
      this.codePhaseState().status === 'complete'
    );
  });

  /**
   * Load pipeline status từ backend FastAPI
   * Fallback sang mock data nếu backend chưa sẵn sàng
   */
  async loadStatus(): Promise<void> {
    this.isLoading.set(true);
    try {
      // Use /pipeline/status which returns pipeline_progress from disk artifacts
      const result = await this.api.getPipelineStatus();
      if (result.success && result.data) {
        this.updateFromBackend(result.data);
      } else {
        this.setFallbackStatus();
      }
    } catch (error) {
      console.warn('Backend not available, using fallback status:', error);
      this.setFallbackStatus();
    } finally {
      this.isLoading.set(false);
    }
  }

  /**
   * Update states từ backend response
   */
  private updateFromBackend(data: any): void {
    this.projectName.set(data.project_name || data.cwd || '');
    this.activeVersion.set(data.active_version || 'v1.0.0');

    const progress = data.pipeline_progress || {};

    this.initPhaseState.set({
      status: (progress.init as PhaseStatus) || 'pending',
    });
    this.briefPhaseState.set({
      status: (progress.brief as PhaseStatus) || 'pending',
    });
    this.contractPhaseState.set({
      status: (progress.contract as PhaseStatus) || 'pending',
    });
    this.irPhaseState.set({
      status: (progress.ir as PhaseStatus) || 'pending',
    });
    this.codePhaseState.set({
      status: (progress.code as PhaseStatus) || 'pending',
      currentStep: progress.code_step,
    });
  }

  /**
   * Fallback status khi backend không available
   */
  private setFallbackStatus(): void {
    this.initPhaseState.set({ status: 'complete', completedAt: new Date().toISOString() });
    this.briefPhaseState.set({ status: 'pending' });
    this.contractPhaseState.set({ status: 'pending' });
    this.irPhaseState.set({ status: 'pending' });
    this.codePhaseState.set({ status: 'pending' });
    this.previewPhaseState.set({ status: 'pending' });
  }

  /**
   * Update states từ API response (deprecated - giữ để backward compat)
   */
  private updateFromApi(status: PipelineStatus): void {
    this.projectName.set(status.project.name);
    this.activeVersion.set(status.active_version);

    this.initPhaseState.set({
      status: status.pipeline_progress.init.status as PhaseStatus,
      completedAt: status.pipeline_progress.init.completed_at,
    });

    this.briefPhaseState.set({
      status: status.pipeline_progress.brief.status as PhaseStatus,
      completedAt: status.pipeline_progress.brief.completed_at,
    });

    this.contractPhaseState.set({
      status: status.pipeline_progress.contract.status as PhaseStatus,
      completedAt: status.pipeline_progress.contract.completed_at,
    });

    this.irPhaseState.set({
      status: status.pipeline_progress.ir.status as PhaseStatus,
      completedAt: status.pipeline_progress.ir.completed_at,
    });

    this.codePhaseState.set({
      status: status.pipeline_progress.code.status as PhaseStatus,
      currentStep: status.pipeline_progress.code.current_step,
    });

    this.previewPhaseState.set({
      status: 'pending',
    });
  }

  /**
   * Getters
   */
  getInitPhase(): PhaseState {
    return this.initPhaseState();
  }

  getBriefPhase(): PhaseState {
    return this.briefPhaseState();
  }

  getContractPhase(): PhaseState {
    return this.contractPhaseState();
  }

  getIRPhase(): PhaseState {
    return this.irPhaseState();
  }

  getCodePhase(): PhaseState {
    return this.codePhaseState();
  }

  getPreviewPhase(): PhaseState {
    return this.previewPhaseState();
  }

  getProjectName(): string {
    return this.projectName();
  }

  getActiveVersion(): string {
    return this.activeVersion();
  }

  isLoadingData(): boolean {
    return this.isLoading();
  }

  /**
   * Setters
   */
  setInitPhaseStatus(status: PhaseStatus): void {
    this.initPhaseState.set({ status });
  }

  setBriefPhaseStatus(status: PhaseStatus): void {
    this.briefPhaseState.set({ status });
  }

  setContractPhaseStatus(status: PhaseStatus): void {
    this.contractPhaseState.set({ status });
  }

  setIRPhaseStatus(status: PhaseStatus): void {
    this.irPhaseState.set({ status });
  }

  setCodePhaseStatus(status: PhaseStatus, currentStep?: string): void {
    this.codePhaseState.update((current) => ({
      ...current,
      status,
      currentStep,
    }));
  }

  setPreviewPhaseStatus(status: PhaseStatus): void {
    this.previewPhaseState.set({ status });
  }

  /**
   * Pipeline actions - gọi API thực
   */
  async runBriefAnalyze(): Promise<boolean> {
    this.briefPhaseState.set({ status: 'in_progress' });
    try {
      const result = await this.api.analyzeBrief({ brief_content: '' });
      if (result.success) {
        this.briefPhaseState.set({ status: 'complete', completedAt: new Date().toISOString() });
        return true;
      } else {
        this.briefPhaseState.set({ status: 'error', errorMessage: result.message || 'Brief analyze failed' });
        return false;
      }
    } catch (error) {
      this.briefPhaseState.set({ status: 'error', errorMessage: String(error) });
      return false;
    }
  }

  async runContractGen(): Promise<boolean> {
    this.contractPhaseState.set({ status: 'in_progress' });
    try {
      const result = await this.api.generateContract();
      if (result.success) {
        this.contractPhaseState.set({ status: 'complete', completedAt: new Date().toISOString() });
        return true;
      } else {
        this.contractPhaseState.set({ status: 'error', errorMessage: result.message || 'Contract gen failed' });
        return false;
      }
    } catch (error) {
      this.contractPhaseState.set({ status: 'error', errorMessage: String(error) });
      return false;
    }
  }

  async runContractCheck(): Promise<boolean> {
    try {
      const result = await this.api.checkContract();
      return result.success;
    } catch (error) {
      console.error('Contract check failed:', error);
      return false;
    }
  }

  async runIRBuild(): Promise<boolean> {
    this.irPhaseState.set({ status: 'in_progress' });
    try {
      const result = await this.api.buildIR();
      if (result.success) {
        this.irPhaseState.set({ status: 'complete', completedAt: new Date().toISOString() });
        return true;
      } else {
        this.irPhaseState.set({ status: 'error', errorMessage: result.message || 'IR build failed' });
        return false;
      }
    } catch (error) {
      this.irPhaseState.set({ status: 'error', errorMessage: String(error) });
      return false;
    }
  }

  async runCodeBuild(): Promise<boolean> {
    this.codePhaseState.set({ status: 'in_progress', currentStep: 'building' });
    try {
      const result = await this.api.buildCodePlan();
      if (result.success) {
        this.codePhaseState.set({ status: 'complete', completedAt: new Date().toISOString() });
        return true;
      } else {
        this.codePhaseState.set({ status: 'error', errorMessage: result.message || 'Code build failed' });
        return false;
      }
    } catch (error) {
      this.codePhaseState.set({ status: 'error', errorMessage: String(error) });
      return false;
    }
  }

  async runCodeGen(): Promise<boolean> {
    this.codePhaseState.set({ status: 'in_progress', currentStep: 'generating' });
    try {
      const result = await this.api.generateCode();
      if (result.success) {
        return true;
      } else {
        this.codePhaseState.set({ status: 'error', errorMessage: result.message || 'Code gen failed' });
        return false;
      }
    } catch (error) {
      this.codePhaseState.set({ status: 'error', errorMessage: String(error) });
      return false;
    }
  }

  async runCodeApply(): Promise<boolean> {
    this.codePhaseState.set({ status: 'in_progress', currentStep: 'applying' });
    try {
      const result = await this.api.applyCode();
      if (result.success) {
        this.codePhaseState.set({ status: 'complete', completedAt: new Date().toISOString() });
        return true;
      } else {
        this.codePhaseState.set({ status: 'error', errorMessage: result.message || 'Code apply failed' });
        return false;
      }
    } catch (error) {
      this.codePhaseState.set({ status: 'error', errorMessage: String(error) });
      return false;
    }
  }

  async runRuntimeTest(): Promise<boolean> {
    this.previewPhaseState.set({ status: 'in_progress' });
    try {
      const result = await this.api.testRuntime();
      if (result.success) {
        this.previewPhaseState.set({ status: 'complete', completedAt: new Date().toISOString() });
        return true;
      } else {
        this.previewPhaseState.set({ status: 'error', errorMessage: result.message || 'Runtime test failed' });
        return false;
      }
    } catch (error) {
      this.previewPhaseState.set({ status: 'error', errorMessage: String(error) });
      return false;
    }
  }
}
