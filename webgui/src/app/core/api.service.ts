/**
 * Real API Service - kết nối với FastAPI backend
 * Thay thế MockApiService bằng HTTP calls thực sự
 * Base URL: http://localhost:6868/api
 */

import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';

// Re-export types từ mock-api.service để dùng chung
import {
  ApiResponse,
  LoginRequest,
  LoginResponse,
  UserResponse,
  BriefAnalyzeRequest,
  BriefAnalyzeResponse,
  ClarificationStartRequest,
  ClarificationStartResponse,
  ClarificationAnswersRequest,
  ClarificationAnswersResponse,
  ClarificationStatusResponse,
  BriefSaveRequest,
  BriefSaveResponse,
  Brief,
  ContractGenRequest,
  ContractGenResponse,
  ContractCheckRequest,
  ContractCheckResponse,
  ContractIR,
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
} from './mock-api.service';

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
  stack?: string;
}

export interface ProjectInfo {
  id: number;
  project_id: string;
  name: string;
  path: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'http://localhost:6868/api';

  /**
   * Build HTTP headers với auth token và language
   */
  private buildHeaders(extraHeaders?: { [key: string]: string }): HttpHeaders {
    let headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'Accept-Language': 'vi',
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
              message: err.error?.message || err.message || 'Lỗi kết nối',
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
              message: err.error?.message || err.message || 'Lỗi kết nối',
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
   * GET /brief/lineage - Get brief change history (from brief_lineage table)
   */
  async getBriefLineage(version?: string): Promise<ApiResponse<{ lineage: any[]; count: number }>> {
    const params = version ? `?version=${version}` : '';
    return this.get(`/brief/lineage${params}`);
  }

  /**
   * POST /brief/freeze - Freeze brief (clarified → frozen)
   */
  async freezeBrief(version: string): Promise<ApiResponse<{ brief_id: string; status: string; type: string }>> {
    return this.post('/brief/freeze', { version });
  }

  // ============================================================================
  // CONTRACT ENDPOINTS
  // ============================================================================

  /**
   * POST /contract/gen - Generate contract
   */
  async generateContract(request?: ContractGenRequest): Promise<ApiResponse<ContractGenResponse>> {
    return this.post('/contract/gen', request || {});
  }

  /**
   * POST /contract/gen/resume - Resume contract generation
   */
  async resumeContractGen(): Promise<ApiResponse<any>> {
    return this.post('/contract/gen/resume');
  }

  /**
   * POST /contract/check - Check contract
   */
  async checkContract(request?: ContractCheckRequest): Promise<ApiResponse<ContractCheckResponse>> {
    return this.post('/contract/check', request || {});
  }

  /**
   * GET /contract/ir - Get contract IR
   */
  async getContractIR(): Promise<ApiResponse<ContractIR>> {
    return this.get('/contract/ir');
  }

  /**
   * POST /contract/feedback - Contract feedback
   */
  async contractFeedback(): Promise<ApiResponse<any>> {
    return this.post('/contract/feedback');
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
  // CLARIFICATION ENDPOINTS
  // ============================================================================

  /**
   * POST /clarification/start - Start clarification session
   */
  async startClarification(request: ClarificationStartRequest): Promise<ApiResponse<ClarificationStartResponse>> {
    return this.post('/clarification/start', request);
  }

  /**
   * POST /clarification/answers - Submit clarification answers
   */
  async submitClarificationAnswers(request: ClarificationAnswersRequest): Promise<ApiResponse<ClarificationAnswersResponse>> {
    return this.post('/clarification/answers', request);
  }

  /**
   * GET /clarification/status/{session_id} - Get clarification status
   */
  async getClarificationStatus(sessionId: string): Promise<ApiResponse<ClarificationStatusResponse>> {
    return this.get(`/clarification/status/${sessionId}`);
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
  // AUTH ENDPOINTS (mock for now - no backend auth)
  // ============================================================================

  /**
   * POST /auth/login - Login
   * Note: Backend doesn't have auth endpoints yet, using localStorage mock
   */
  async login(request: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    // For now, generate mock token locally (same as MockApiService)
    const mockToken = `token_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const mockUser = {
      id: `user_${Date.now()}`,
      email: request.email,
      tier: 'pro' as const,
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
      error: { code: 'NOT_AUTHENTICATED', message: 'Chưa đăng nhập' },
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
      message: 'Đăng xuất thành công',
      timestamp: new Date().toISOString(),
    };
  }
}
