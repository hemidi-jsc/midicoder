/**
 * Real API Service - kết nối với FastAPI backend
 * Base URL: http://localhost:6868/api
 */

import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { I18nService } from './i18n.service';

// Re-export types — shared API type definitions
import {
  ApiResponse,
  LoginRequest,
  LoginResponse,
  UserResponse,
  BriefAnalyzeRequest,
  BriefAnalyzeResponse,
  BriefSaveRequest,
  BriefSaveResponse,
  Brief,
  ContractGenRequest,
  ContractGenResponse,
  IRBuildRequest,
  IRBuildResponse,
  MIR,
  CodePlanRequest,
  CodePlanResponse,
  CodeGenRequest,
  CodeGenResponse,
  CodeApplyRequest,
  CodeApplyResponse,
  CodeFile,
  PreviewStartRequest,
  PreviewStartResponse,
  PreviewStatusResponse,
  FeedbackRequest,
  FeedbackResponse,
  PipelineStatus,
  NewsItem,
  NewsResponse,
} from './api.types';

// ============================================================================
// Request/Response models cho backend FastAPI
// Backend trả về: { success, data, message, timestamp, language }
// ============================================================================

interface FastAPIResponse {
  success: boolean;
  data?: any;
  message?: string;
  timestamp?: string;
  language?: string;
}

export interface InitRequest {
  non_interactive?: boolean;
  working_dir?: string;
  stack?: string;
  llm_high_provider?: string;
  llm_high_model?: string;
  llm_high_url?: string;
  llm_high_key_env?: string;
  llm_cheap_provider?: string;
  llm_cheap_model?: string;
  llm_cheap_url?: string;
  llm_cheap_key_env?: string;
}

export interface ConfigSetRequest {
  key: string;
  value: string;
}

export interface VersionCreateRequest {
  version: string;
}

export interface IRBuildRequestFastAPI {
  skip_diagrams?: boolean;
}

export interface CodeGenRequestFastAPI {
  runtime?: boolean;
}

export interface CodeApplyRequestFastAPI {
  force?: boolean;
  dry_run?: boolean;
  no_reindex?: boolean;
  patches_subdir?: string;
}

export interface RuntimeTestRequest {
  timeout?: number;
  port?: number;
  verbose?: boolean;
}

export interface RuntimeFixRequest {
  log_timestamp?: string;
  dry_run?: boolean;
  auto_apply?: boolean;
  auto_fix_loop?: boolean;
  test_timeout?: number;
  test_port?: number;
}

export interface IndexReindexRequest {
  paths?: string[];
}

export interface ProjectCreateRequest {
  name: string;
  path: string;
  tech_stack: {
    infrastructure: string;
    backend: string;
    frontend: string;
    ui_framework: string;
  };
  prompt_domain: string;
}

export interface ProjectInfo {
  id: number;
  project_id: string;
  name: string;
  path: string;
  active: boolean;
  created_at: string;
  updated_at: string;
  repo_url?: string | null;
  tech_stack?: {
    infrastructure?: string;
    backend?: string;
    frontend?: string;
    ui_framework?: string;
  };
  prompt_domain?: string;
}

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly i18n = inject(I18nService);
  private readonly baseUrl = 'http://localhost:6868/api';

  /**
   * Build HTTP headers với auth token và language
   */
  private buildHeaders(extraHeaders?: { [key: string]: string }): HttpHeaders {
    const lang = this.i18n.getLanguage();
    let headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'X-Language': lang,
      'Accept-Language': lang,
    });

    const token = localStorage.getItem('midicoder_token');
    if (token) {
      headers = headers.set('Authorization', `Bearer ${token}`);
    }

    if (extraHeaders) {
      for (const [key, value] of Object.entries(extraHeaders)) {
        headers = headers.set(key, value);
      }
    }

    return headers;
  }

  /**
   * Helper: gửi POST request và parse response
   */
  private post<T>(endpoint: string, body?: any): Promise<ApiResponse<T>> {
    return new Promise((resolve) => {
      this.http.post<FastAPIResponse>(`${this.baseUrl}${endpoint}`, body || {}, {
        headers: this.buildHeaders(),
      }).subscribe({
        next: (res) => {
          resolve({
            success: res.success,
            data: res.data as T,
            message: res.message,
            timestamp: res.timestamp || new Date().toISOString(),
          });
        },
        error: (err) => {
          console.error(`API Error [POST ${endpoint}]:`, err);
          resolve({
            success: false,
            error: {
              code: 'NETWORK_ERROR',
              message: err.error?.message || err.message || 'Connection error',
            },
            timestamp: new Date().toISOString(),
          });
        },
      });
    });
  }

  /**
   * Helper: gửi GET request và parse response
   */
  private get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return new Promise((resolve) => {
      this.http.get<FastAPIResponse>(`${this.baseUrl}${endpoint}`, {
        headers: this.buildHeaders(),
      }).subscribe({
        next: (res) => {
          resolve({
            success: res.success,
            data: res.data as T,
            message: res.message,
            timestamp: res.timestamp || new Date().toISOString(),
          });
        },
        error: (err) => {
          console.error(`API Error [GET ${endpoint}]:`, err);
          resolve({
            success: false,
            error: {
              code: 'NETWORK_ERROR',
              message: err.error?.message || err.message || 'Connection error',
            },
            timestamp: new Date().toISOString(),
          });
        },
      });
    });
  }

  // ============================================================================
  // HEALTH ENDPOINTS
  // ============================================================================

  /**
   * GET /health/ - Health check
   */
  async healthCheck(): Promise<ApiResponse<{ status: string; version: string; timestamp: string }>> {
    return this.get('/health/');
  }

  /**
   * GET /health/ready - Ready check
   */
  async readyCheck(): Promise<ApiResponse<{ status: string; version: string; timestamp: string }>> {
    return this.get('/health/ready');
  }

  /**
   * GET /health/info - API info
   */
  async getApiInfo(): Promise<ApiResponse<any>> {
    return this.get('/health/info');
  }

  /**
   * GET /health/languages - Supported languages
   */
  async getLanguages(): Promise<ApiResponse<{ languages: string[]; default: string }>> {
    return this.get('/health/languages');
  }

  /**
   * GET /health/status - System status
   */
  async getSystemStatus(): Promise<ApiResponse<any>> {
    return this.get('/health/status');
  }

  // ============================================================================
  // LLM CONFIG ENDPOINTS
  // ============================================================================

  /**
   * GET /config/llm - Get LLM config
   */
  async getLlmConfig(): Promise<ApiResponse<{ llm: any; providers: string[] }>> {
    return this.get('/config/llm');
  }

  /**
   * POST /config/llm - Set LLM config
   */
  async setLlmConfig(config: {
    provider: string;
    model: string;
    api_url: string;
    api_key?: string;
    max_tokens?: number;
    temperature?: number;
    top_p?: number;
    top_k?: number;
    min_p?: number;
    presence_penalty?: number;
    repetition_penalty?: number;
    timeout?: number;
    retry_attempts?: number;
  }): Promise<ApiResponse<{ saved: boolean }>> {
    return this.post('/config/llm', config);
  }

  /**
   * POST /config/llm/test - Test LLM connection
   */
  async testLlmConfig(): Promise<ApiResponse<any>> {
    return this.post('/config/llm/test', {});
  }

  // ============================================================================
  // INIT ENDPOINT
  // ============================================================================

  /**
   * POST /init - Initialize project
   */
  async initProject(request?: InitRequest): Promise<ApiResponse<any>> {
    return this.post('/init', request || { non_interactive: true });
  }

  // ============================================================================
  // CONFIG ENDPOINTS
  // ============================================================================

  /**
   * GET /config/list - List all config
   */
  async listConfig(): Promise<ApiResponse<any>> {
    return this.get('/config/list');
  }

  /**
   * GET /config/get/{key} - Get config value
   */
  async getConfig(key: string): Promise<ApiResponse<any>> {
    return this.get(`/config/get/${key}`);
  }

  /**
   * POST /config/set - Set config value
   */
  async setConfig(request: ConfigSetRequest): Promise<ApiResponse<any>> {
    return this.post('/config/set', request);
  }

  /**
   * POST /config/validate - Validate config
   */
  async validateConfig(): Promise<ApiResponse<any>> {
    return this.post('/config/validate');
  }

  /**
   * POST /config/reset - Reset config
   */
  async resetConfig(): Promise<ApiResponse<any>> {
    return this.post('/config/reset');
  }

  // ============================================================================
  // INDEX ENDPOINTS
  // ============================================================================

  /**
   * POST /index/ - Build index
   */
  async buildIndex(): Promise<ApiResponse<any>> {
    return this.post('/index/');
  }

  /**
   * POST /index/reindex - Reindex files
   */
  async reindex(request?: IndexReindexRequest): Promise<ApiResponse<any>> {
    return this.post('/index/reindex', request || {});
  }

  // ============================================================================
  // VERSION ENDPOINTS
  // ============================================================================

  /**
   * POST /version/create - Create version
   */
  async createVersion(request: VersionCreateRequest): Promise<ApiResponse<any>> {
    return this.post('/version/create', request);
  }

  /**
   * GET /version/list - List all versions
   */
  async listVersions(): Promise<ApiResponse<{ versions: any[]; active_version?: string }>> {
    return this.get('/version/list');
  }

  /**
   * POST /version/check-create - Check impact before creating version
   */
  async checkCreateVersion(versionName: string): Promise<ApiResponse<{
    will_archive: { version: string; status: string; note: string }[];
    will_delete: { version: string; status: string; created_at: string }[];
    max_versions: number;
    current_count: number;
    parent_version: string | null;
  }>> {
    return this.post('/version/check-create', { version: versionName });
  }

  /**
   * POST /version/use - Switch version
   */
  async useVersion(request: VersionCreateRequest): Promise<ApiResponse<any>> {
    return this.post('/version/use', request);
  }

  // ============================================================================
  // BRIEF ENDPOINTS
  // ============================================================================

  /**
   * POST /brief/analyze - Analyze brief
   */
  async analyzeBrief(request: BriefAnalyzeRequest): Promise<ApiResponse<BriefAnalyzeResponse>> {
    return this.post('/brief/analyze', request);
  }

  /**
   * POST /brief/save - Save brief (upsert: 1 version = 1 brief)
   */
  async saveBrief(request: { version?: string; brief_content?: string }): Promise<ApiResponse<{ saved: boolean; brief_id?: string; updated?: boolean }>> {
    return this.post('/brief/save', request);
  }

  /**
   * GET /brief/get - Get single brief for version (replaces /master, /working, /raw)
   */
  async getBrief(version?: string): Promise<ApiResponse<{
    brief_id: string;
    version: string;
    type: string;
    status: string;
    title: string;
    content: string;
    clarifications: any[];
    analysis?: BriefAnalyzeResponse | null;
    created_at: string;
    updated_at: string;
  }>> {
    const params = version ? `?version=${version}` : '';
    return this.get(`/brief/get${params}`);
  }

  /**
   * GET /brief/clarifications - Get clarification Q&A history
   */
  async getClarifications(version?: string): Promise<ApiResponse<{ clarifications: any[]; count: number }>> {
    const params = version ? `?version=${version}` : '';
    return this.get(`/brief/clarifications${params}`);
  }

  /**
   * GET /brief/revisions - Get brief revision history (from brief_revisions table)
   */
  async getBriefRevisions(version?: string): Promise<ApiResponse<{ revisions: any[]; count: number }>> {
    const params = version ? `?version=${version}` : '';
    return this.get(`/brief/revisions${params}`);
  }

  /**
   * GET /brief/revisions/{revision_number}/diff - Get unified diff for a revision
   */
  async getRevisionDiff(revisionNumber: number, version?: string): Promise<ApiResponse<{ revision_number: number; event: string; diff_summary: string | null; diff_text: string; stats: { added: number; removed: number }; has_diff: boolean }>> {
    const params = version ? `?version=${version}` : '';
    return this.get(`/brief/revisions/${revisionNumber}/diff${params}`);
  }

  /**
   * POST /brief/freeze - Freeze brief (clarified → frozen)
   */
  async freezeBrief(version: string): Promise<ApiResponse<{ brief_id: string; status: string; type: string }>> {
    return this.post('/brief/freeze', { version });
  }

  /**
   * POST /brief/clarify - Submit clarification answers, merge into brief, optionally re-analyze
   */
  async clarifyBrief(request: {
    version: string;
    answers: Array<{ id: string; summary: string; question: string; recommend: string; answer: string }>;
    re_analyze: boolean;
  }): Promise<ApiResponse<{
    brief_id: string;
    revision_number: number;
    clarification_count: number;
    round: number;
    should_re_analyze: boolean;
    quality_score?: number;
    remaining_ambiguities?: Array<{ summary: string; question: string; recommend: string }>;
    remaining_blockers?: number;
  }>> {
    return this.post('/brief/clarify', request);
  }

  // ============================================================================
  // CONTRACT ENDPOINTS
  // ============================================================================

  /**
   * POST /contract/freeze - Freeze contracts
   */
  async freezeContract(): Promise<ApiResponse<{
    frozen_count: number;
    validation_status: string;
    errors: number;
    warnings: number;
  }>> {
    return this.post('/contract/freeze', {});
  }

  /**
   * SSE Stream: GET /contract/gen-category-stream — gen 1 category riêng
   * Compatible with llm-progress component events
   */
  async* streamContractCategory(category: string): AsyncGenerator<{event: string; data: any}, void, unknown> {
    const url = `http://localhost:6868/api/contract/gen-category-stream?category=${encodeURIComponent(category)}`;
    yield* this._parseSseStream(url);
  }

  /**
   * Internal helper: parse SSE stream from a URL
   */
  private async* _parseSseStream(url: string): AsyncGenerator<{event: string; data: any}, void, unknown> {
    const response = await fetch(url, {
      headers: {
        'X-Language': this.i18n.getLanguage(),
        'Accept-Language': this.i18n.getLanguage(),
      },
    });

    if (!response.ok || !response.body) {
      throw new Error(`Stream failed: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n\n');
        // Keep the last incomplete chunk in buffer
        buffer = lines.pop() || '';

        for (const chunk of lines) {
          const parts = chunk.split('\n');
          let currentEvent = '';
          let currentData = '';

          for (const line of parts) {
            if (line.startsWith('event: ')) {
              currentEvent = line.slice(7).trim();
            } else if (line.startsWith('data: ')) {
              currentData = line.slice(6).trim();
            }
          }

          if (currentData) {
            try {
              yield { event: currentEvent, data: JSON.parse(currentData) };
            } catch {
              yield { event: currentEvent, data: currentData };
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * GET /contract/artifacts?category={key} - Check existence + metadata for a contract category
   */
  async getContractArtifact(category: string): Promise<ApiResponse<{
    exists: boolean;
    artifact_id?: string;
    status?: string;
    content_length?: number;
    updated_at?: string;
  }>> {
    return this.get<any>(`/contract/artifacts?category=${encodeURIComponent(category)}`);
  }

  /**
   * GET /contract/artifacts/{category} - Get raw YAML content for a contract category
   */
  async getContractArtifactContent(category: string): Promise<ApiResponse<{
    exists: boolean;
    content: string;
    artifact_id?: string;
    status?: string;
    updated_at?: string;
  }>> {
    return this.get<any>(`/contract/artifacts/${encodeURIComponent(category)}`);
  }

  /**
   * GET /contract/manifest - Get contract manifest
   */
  async getContractManifest(): Promise<ApiResponse<{
    total: number;
    categories: Record<string, { name: string; status: string; updated_at: string }>;
  }>> {
    return this.get('/contract/manifest');
  }

  /**
   * GET /contract/traceability - Get traceability matrix and drift detection
   */
  async getTraceability(): Promise<ApiResponse<{
    trace_matrix: Record<string, Array<{
      trace_id: string;
      analysis_name: string | null;
      contract_id: string | null;
      status: 'matched' | 'orphan_analysis' | 'orphan_contract' | 'mismatch';
      analysis_item?: any;
      contract_node?: any;
      description_similarity?: number;
    }>>;
    drifts: Array<{
      type: string;
      category: string;
      name: string;
      trace_id: string;
      severity: 'error' | 'warning';
      message: string;
    }>;
    summary: {
      total_analysis: number;
      total_contract: number;
      matched: number;
      orphan_analysis: number;
      orphan_contract: number;
      mismatched: number;
    };
    unmapped_analysis: Array<{ category: string; count: number }>;
    brief_coverage: {
      coverage_ratio: number;
      covered_count: number;
      uncovered_count: number;
      uncovered_items: Array<{ name: string; category: string }>;
    };
    health_score: number;
  }>> {
    return this.get('/contract/traceability');
  }

  // ============================================================================
  // IR ENDPOINTS
  // ============================================================================

  /**
   * POST /ir/build - Build IR
   */
  async buildIR(request?: IRBuildRequestFastAPI): Promise<ApiResponse<IRBuildResponse>> {
    return this.post('/ir/build', request || {});
  }

  /**
   * GET /ir/mir - Get MIR data
   */
  async getMIR(): Promise<ApiResponse<MIR>> {
    return this.get('/ir/mir');
  }

  /**
   * GET /ir/symbol-table - Get symbol table data
   */
  async getSymbolTable(): Promise<ApiResponse<any>> {
    return this.get('/ir/symbol-table');
  }

  // ============================================================================
  // CODE ENDPOINTS
  // ============================================================================

  /**
   * POST /code/build - Build code plan
   */
  async buildCodePlan(): Promise<ApiResponse<CodePlanResponse>> {
    return this.post('/code/build');
  }

  /**
   * POST /code/plan - Plan code (alias)
   */
  async planCode(request?: CodePlanRequest): Promise<ApiResponse<CodePlanResponse>> {
    return this.post('/code/plan', request || {});
  }

  /**
   * POST /code/gen - Generate code
   */
  async generateCode(request?: CodeGenRequestFastAPI): Promise<ApiResponse<CodeGenResponse>> {
    return this.post('/code/gen', request || {});
  }

  /**
   * POST /code/apply - Apply code
   */
  async applyCode(request?: CodeApplyRequestFastAPI): Promise<ApiResponse<CodeApplyResponse>> {
    return this.post('/code/apply', request || {});
  }

  /**
   * GET /code/files - Get generated code files
   */
  async getCodeFiles(): Promise<ApiResponse<{ files: CodeFile[]; count: number }>> {
    return this.get('/code/files');
  }

  // ============================================================================
  // RUNTIME ENDPOINTS
  // ============================================================================

  /**
   * POST /runtime/test - Test runtime
   */
  async testRuntime(request?: RuntimeTestRequest): Promise<ApiResponse<any>> {
    return this.post('/runtime/test', request || {});
  }

  /**
   * POST /runtime/fix - Fix runtime errors
   */
  async fixRuntime(request?: RuntimeFixRequest): Promise<ApiResponse<any>> {
    return this.post('/runtime/fix', request || {});
  }

  // ============================================================================
  // PIPELINE STATUS
  // ============================================================================

  /**
   * GET /pipeline/status - Get pipeline progress
   * Maps to backend /health/status for now
   */
  async getPipelineStatus(): Promise<ApiResponse<PipelineStatus>> {
    return this.get('/pipeline/status');
  }

  /**
   * GET /artifacts/stats - Get artifact statistics for active version
   */
  async getArtifactStats(): Promise<ApiResponse<any>> {
    return this.get('/artifacts/stats');
  }

  // ============================================================================
  // PREVIEW ENDPOINTS (Docker Compose)
  // ============================================================================

  /**
   * POST /preview/start - Start Docker Compose preview
   */
  async startPreview(request: PreviewStartRequest): Promise<ApiResponse<PreviewStartResponse>> {
    return this.post('/preview/start', request);
  }

  /**
   * POST /preview/stop - Stop Docker Compose preview
   */
  async stopPreview(): Promise<ApiResponse<any>> {
    return this.post('/preview/stop');
  }

  /**
   * GET /preview/status - Get preview status
   */
  async getPreviewStatus(): Promise<ApiResponse<PreviewStatusResponse>> {
    return this.get('/preview/status');
  }

  // ============================================================================
  // FEEDBACK ENDPOINT
  // ============================================================================

  /**
   * POST /feedback - Submit feedback
   */
  async submitFeedback(request: FeedbackRequest): Promise<ApiResponse<FeedbackResponse>> {
    return this.post('/feedback', request);
  }

  // ============================================================================
  // NEWS ENDPOINT
  // ============================================================================

  /**
   * GET /news - Get news items
   * Note: This is an external API, not available on local backend
   */
  async getNews(): Promise<ApiResponse<NewsResponse>> {
    return this.get('/news');
  }

  // ============================================================================
  // System Logs
  // ============================================================================

  async getLogFiles(): Promise<ApiResponse<{ files: { filename: string; path: string; size: number; modified: string }[]; count: number }>> {
    return this.get<any>('/system/log-files');
  }

  async getLogs(filename?: string, lines?: number): Promise<ApiResponse<{ lines: string[]; file: string | null; total: number }>> {
    const params = [];
    if (filename) params.push(`file=${filename}`);
    if (lines) params.push(`lines=${lines}`);
    return this.get<any>(`/system/logs?${params.join('&')}`);
  }

  // ============================================================================
  // Activity Log — lịch sử hoạt động
  // ============================================================================

  async getActivityRecent(): Promise<ApiResponse<{
    activities: { id: number; timestamp: string; user: string; action: string; resource_type: string; resource_id: string; details: string | null; status: string }[];
    count: number;
  }>> {
    return this.get<any>('/activity/recent');
  }

  async getActivityAll(page: number = 1, perPage: number = 50): Promise<ApiResponse<{
    activities: { id: number; timestamp: string; user: string; action: string; resource_type: string; resource_id: string; details: string | null; status: string }[];
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
  }>> {
    return this.get<any>(`/activity/all?page=${page}&per_page=${perPage}`);
  }

  // ============================================================================
  // AUTH ENDPOINTS (mock for now - no backend auth)
  // ============================================================================

  /**
   * POST /auth/login - Login
   * Note: Backend doesn't have auth endpoints yet, using localStorage mock
   */
  async login(request: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    // Local mock login (backend không có auth endpoint)
    const mockToken = `token_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const mockUser = {
      id: `user_${Date.now()}`,
      email: request.email,
    };

    localStorage.setItem('midicoder_token', mockToken);
    localStorage.setItem('midicoder_user', JSON.stringify(mockUser));

    return {
      success: true,
      data: {
        token: mockToken,
        user: mockUser,
        expires_in: 86400,
      },
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * GET /auth/me - Get current user
   */
  async me(): Promise<ApiResponse<UserResponse>> {
    const userStr = localStorage.getItem('midicoder_user');
    if (userStr) {
      const user = JSON.parse(userStr);
      return {
        success: true,
        data: {
          ...user,
          devices: [],
        },
        timestamp: new Date().toISOString(),
      };
    }
    return {
      success: false,
      error: { code: 'NOT_AUTHENTICATED', message: this.i18n.t('auth.notAuthenticated') },
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * POST /auth/logout - Logout
   */
  // ============================================================================
  // Projects — multi-project management
  // ============================================================================

  async listProjects(): Promise<ApiResponse<{ projects: ProjectInfo[]; active?: ProjectInfo }>> {
    return this.get<any>('/projects');
  }

  async getActiveProject(): Promise<ApiResponse<{ project?: ProjectInfo }>> {
    return this.get<any>('/projects/active');
  }

  async getTechStacks(): Promise<ApiResponse<{
    stacks: { infrastructure: any[]; backend: any[]; frontend: any[]; ui_framework: any[] };
    prompt_domains: { value: string; label: string }[];
  }>> {
    return this.get<any>('/projects/techstacks');
  }

  async createProject(request: ProjectCreateRequest): Promise<ApiResponse<any>> {
    return this.post<any>('/projects', request);
  }

  async activateProject(projectId: string): Promise<ApiResponse<{ project: ProjectInfo }>> {
    return this.post<any>(`/projects/${projectId}/activate`);
  }

  async deleteProject(projectId: string): Promise<ApiResponse<any>> {
    return this.http.delete<any>(`${this.baseUrl}/projects/${projectId}`).toPromise();
  }

  async logout(): Promise<ApiResponse> {
    localStorage.removeItem('midicoder_token');
    localStorage.removeItem('midicoder_user');
    return {
      success: true,
      message: this.i18n.t('auth.logoutSuccess'),
      timestamp: new Date().toISOString(),
    };
  }
}
