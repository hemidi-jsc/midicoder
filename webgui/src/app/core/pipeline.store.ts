/**
 * Store cho Pipeline state
 * Quản lý trạng thái của các phases trong pipeline
 */

import { Injectable, signal, computed } from '@angular/core';
import { MockApiService, PipelineStatus } from './mock-api.service';

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

  constructor(private mockApi: MockApiService) {}

  /**
   * Load pipeline status từ API
   */
  async loadStatus(): Promise<void> {
    this.isLoading.set(true);
    try {
      const result = await this.mockApi.getStatus();
      if (result.success && result.data) {
        this.updateFromApi(result.data);
      }
    } catch (error) {
      console.error('Failed to load pipeline status:', error);
    } finally {
      this.isLoading.set(false);
    }
  }

  /**
   * Update states từ API response
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
      status: 'pending', // Default, will be updated separately
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
}