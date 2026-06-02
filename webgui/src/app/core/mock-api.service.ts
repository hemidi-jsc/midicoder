/**
 * Dịch vụ Mock API Singleton
 * Dùng để giả lập API responses cho testing trước khi có backend thực
 * Cấu trúc payload/response giống hệt backend FastAPI để dễ reuse
 */

import { Injectable } from '@angular/core';

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

// Response wrapper chung cho tất cả API
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
}

// ============================================================================
// AUTH TYPES
// ============================================================================

export interface LoginRequest {
  email: string;
  password: string;
  device_fingerprint: string;
}

export interface LoginResponse {
  token: string;
  expires_in: number;
  user: {
    id: string;
    email: string;
    tier: 'free' | 'pro' | 'enterprise';
  };
}

export interface UserResponse {
  id: string;
  email: string;
  tier: string;
  devices: Array<{
    id: string;
    fingerprint: string;
    last_used: string;
  }>;
}

// ============================================================================
// BRIEF TYPES
// ============================================================================

export interface BriefAnalyzeRequest {
  brief_content: string;
  version?: string;
}

export interface BriefAnalyzeResponse {
  status: 'needs_clarification' | 'ready_for_contract';
  analysis: {
    intent: {
      domain: string;
      type: string;
      scale: string;
    };
    ambiguities: Array<{
      id: string;
      type: string;
      source_text: string;
      description: string;
    }>;
    summary?: string;
  };
  metadata?: {
    domain: string;
    confidence: number;
    entities: number;
    commands: number;
    queries: number;
    events: number;
    ui_components: number;
    brief_id?: string;
  };
}

export interface ClarificationStartRequest {
  version: string;
  non_interactive?: boolean;
}

export interface Question {
  id: string;
  source_text: string;
  ambiguity_type: string;
  question: string;
  options?: Array<{ value: string; label: string }>;
  required: boolean;
  type: 'single_select' | 'multi_select' | 'text';
}

export interface ClarificationStartResponse {
  clarification_id: string;
  status: 'questions_ready' | 'ready';
  round: number;
  questions?: Question[];
  message?: string;
}

export interface ClarificationAnswersRequest {
  session_id: string;
  answers: Array<{
    question_id: string;
    values: string[];
    notes?: string;
  }>;
}

export interface ClarificationAnswersResponse {
  status: 'more_questions' | 'ready';
  round: number;
  questions?: Question[];
}

export interface ClarificationStatusResponse {
  clarification_id: string;
  status: string;
  current_round: number;
  total_rounds: number;
  master_brief_path?: string;
  clarification_log?: {
    total_questions: number;
    total_tokens_used: number;
  };
}

export interface BriefSaveRequest {
  name: string;
  tags?: string[];
  version?: string;
}

export interface BriefSaveResponse {
  saved_path: string;
}

export interface Brief {
  name: string;
  domain: string;
  tags: string[];
  created_at: string;
  usage_count: number;
}

// ============================================================================
// CONTRACT TYPES
// ============================================================================

export interface ContractGenRequest {
  version: string;
  capabilities?: string[];
}

export interface ContractGenResponse {
  status: string;
  artifacts: {
    ir_path: string;
    manifest_path: string;
    schemas_path: string;
  };
  summary: {
    entities: number;
    commands: number;
    queries: number;
    events: number;
    workflows: number;
  };
  llm_usage: {
    tokens_used: number;
    requests: number;
  };
}

export interface ContractCheckRequest {
  version: string;
  auto_fix?: boolean;
}

export interface ContractCheckResponse {
  status: string;
  errors: {
    before: number;
    after: number;
    auto_fixed: number;
  };
  warnings: number;
  report_path: string;
}

export interface ContractIR {
  schema: string;
  domain: string;
  version: string;
  entities: any[];
  commands: any[];
  queries: any[];
  events: any[];
  workflows: any[];
}

// ============================================================================
// IR TYPES
// ============================================================================

export interface IRBuildRequest {
  version: string;
}

export interface IRBuildResponse {
  artifacts: {
    mir_path: string;
    symbol_table_path: string;
  };
  metadata: {
    total_entities: number;
    total_commands: number;
    total_queries: number;
    total_events: number;
  };
}

export interface MIR {
  schema: string;
  version: string;
  generated_at: string;
  source: {
    contract: string;
    manifest: string;
  };
  modules: any[];
  metadata: any;
}

// ============================================================================
// CODE TYPES
// ============================================================================

export interface CodePlanRequest {
  version: string;
  target?: 'backend' | 'frontend' | 'all';
}

export interface CodePlanResponse {
  artifacts: {
    lowering_path: string;
    patches_path: string;
  };
  summary: {
    total_files: number;
    backend_files: number;
    frontend_files: number;
  };
}

export interface CodeGenRequest {
  version: string;
  target?: 'backend' | 'frontend' | 'all';
  dry_run?: boolean;
}

export interface CodeGenResponse {
  artifacts: {
    generated_path: string;
    report_path: string;
  };
  summary: {
    total_files: number;
    total_lines: number;
    templates_used: number;
  };
}

export interface CodeApplyRequest {
  version: string;
  target_dir: string;
  backup?: boolean;
  dry_run?: boolean;
}

export interface CodeApplyResponse {
  target_dir: string;
  summary: {
    total_files: number;
    applied: number;
    skipped: number;
    conflicts: number;
    backups_created: number;
  };
  status_path: string;
}

export interface CodeFile {
  path: string;
  type: string;
  lines: number;
  status: string;
}

// ============================================================================
// PREVIEW TYPES
// ============================================================================

export interface PreviewStartRequest {
  version: string;
  port?: number;
  target?: 'backend' | 'frontend' | 'all';
}

export interface PreviewStartResponse {
  status: string;
  urls: {
    frontend: string;
    backend: string;
  };
  docker_compose_path: string;
}

export interface PreviewStatusResponse {
  status: 'stopped' | 'starting' | 'running' | 'error';
  services: {
    backend: { status: string; port: number };
    frontend: { status: string; port: number };
    db: { status: string; port: number };
  };
  logs: {
    backend: string;
    frontend: string;
  };
}

// ============================================================================
// FEEDBACK TYPES
// ============================================================================

export interface FeedbackRequest {
  version: string;
  type: 'bug' | 'enhancement' | 'clarification';
  feedback: string;
  auto_apply?: boolean;
}

export interface FeedbackResponse {
  patch_brief_path: string;
  analysis: {
    identified_changes: string[];
    impact: {
      breaking_changes: boolean;
      new_entities: number;
      modified_queries: number;
    };
  };
  pipeline_triggered: boolean;
  pipeline_status: string;
  pipeline_progress: {
    contract_gen: string;
    contract_check: string;
    ir_build: string;
    code_plan: string;
    code_gen: string;
    code_apply: string;
  };
}

// ============================================================================
// SYSTEM TYPES
// ============================================================================

export interface PipelineStatus {
  project: {
    name: string;
    initialized: boolean;
  };
  active_version: string;
  pipeline_progress: {
    init: { status: string; completed_at?: string };
    brief: { status: string; completed_at?: string };
    contract: { status: string; completed_at?: string };
    ir: { status: string; completed_at?: string };
    code: { status: string; current_step?: string };
  };
  artifacts: {
    briefs: { master_brief: string; working_brief: string };
    contracts: { ir: string; manifest: string };
    ir: { mir: string; symbol_table: string };
    code: { plan: string; generated: string; applied: string };
  };
}

// ============================================================================
// NEWS TYPES
// ============================================================================

export interface NewsItem {
  id: string;
  type: 'announcement' | 'blog' | 'ads' | 'release';
  title: string;
  content: string;
  link?: string;
  priority?: 'low' | 'medium' | 'high';
  created_at: string;
  expires_at?: string;
  version?: string;
}

export interface NewsResponse {
  news: NewsItem[];
}

// ============================================================================
// MOCK API SERVICE
// ============================================================================

@Injectable({
  providedIn: 'root',
})
export class MockApiService {
  /**
   * Base URL của API (để dùng chung với real API khi có backend)
   */
  private readonly baseUrl = 'http://localhost:6868/api/v1';

  /**
   * Token giả lập cho authentication
   */
  private mockToken = 'mock-jwt-token-12345';

  /**
   * Tạo timestamp hiện tại
   */
  private getTimestamp(): string {
    return new Date().toISOString();
  }

  /**
   * Tạo response thành công
   */
  private success<T>(data: T, message?: string): ApiResponse<T> {
    return {
      success: true,
      data,
      message,
      timestamp: this.getTimestamp(),
    };
  }

  /**
   * Tạo response lỗi
   */
  private error(code: string, message: string, details?: any): ApiResponse {
    return {
      success: false,
      error: { code, message, details },
      timestamp: this.getTimestamp(),
    };
  }

  // ============================================================================
  // AUTH ENDPOINTS
  // ============================================================================

  /**
   * POST /auth/login
   */
  async login(request: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    // Delay giả lập network request
    await this.delay(500);

    // Validate email/password giả lập
    if (request.email === 'test@example.com' && request.password === 'password') {
      return this.success({
        token: this.mockToken,
        expires_in: 604800, // 7 days
        user: {
          id: 'user_123',
          email: request.email,
          tier: 'free',
        },
      });
    }

    return this.error('INVALID_CREDENTIALS', 'Email hoặc mật khẩu không đúng');
  }

  /**
   * POST /auth/refresh
   */
  async refresh(): Promise<ApiResponse<LoginResponse>> {
    await this.delay(300);

    return this.success({
      token: this.mockToken + '_refreshed',
      expires_in: 604800,
      user: {
        id: 'user_123',
        email: 'test@example.com',
        tier: 'free',
      },
    });
  }

  /**
   * GET /auth/me
   */
  async me(): Promise<ApiResponse<UserResponse>> {
    await this.delay(200);

    return this.success({
      id: 'user_123',
      email: 'test@example.com',
      tier: 'free',
      devices: [
        {
          id: 'device_1',
          fingerprint: 'abc123...',
          last_used: this.getTimestamp(),
        },
      ],
    });
  }

  /**
   * POST /auth/logout
   */
  async logout(): Promise<ApiResponse> {
    await this.delay(200);
    return this.success({}, 'Đăng xuất thành công');
  }

  // ============================================================================
  // BRIEF ENDPOINTS
  // ============================================================================

  /**
   * POST /brief/analyze
   */
  async analyzeBrief(request: BriefAnalyzeRequest): Promise<ApiResponse<BriefAnalyzeResponse>> {
    await this.delay(1000);

    return this.success({
      status: 'needs_clarification',
      analysis: {
        intent: {
          domain: 'e-commerce',
          type: 'multi-tenant-platform',
          scale: 'enterprise',
        },
        ambiguities: [
          {
            id: 'amb-001',
            type: 'scope',
            source_text: 'sync inventory across channels',
            description: 'Which sales channels?',
          },
          {
            id: 'amb-002',
            type: 'data_policy',
            source_text: 'multi-tenant platform',
            description: 'What level of tenant isolation?',
          },
        ],
      },
    });
  }

  /**
   * POST /brief/clarify/start
   */
  async startClarification(request: ClarificationStartRequest): Promise<ApiResponse<ClarificationStartResponse>> {
    await this.delay(800);

    return this.success({
      clarification_id: 'clarify-abc123',
      status: 'questions_ready',
      round: 1,
      questions: [
        {
          id: 'q-001',
          source_text: 'sync inventory across channels',
          ambiguity_type: 'scope',
          question: 'Which sales channels do you need to sync?',
          options: [
            { value: 'amazon', label: 'Amazon' },
            { value: 'walmart', label: 'Walmart' },
            { value: 'shopify', label: 'Shopify' },
            { value: 'ebay', label: 'eBay' },
            { value: 'custom', label: 'Custom (specify)' },
          ],
          required: true,
          type: 'multi_select',
        },
        {
          id: 'q-002',
          source_text: 'multi-tenant platform',
          ambiguity_type: 'data_policy',
          question: 'What level of tenant isolation do you need?',
          options: [
            { value: 'schema_per_tenant', label: 'Schema-per-tenant (full isolation)' },
            { value: 'row_level_security', label: 'Row-level security (shared schema)' },
            { value: 'tenant_id_filter', label: 'Shared schema with tenant_id filter' },
          ],
          required: true,
          type: 'single_select',
        },
      ],
    });
  }

  /**
   * POST /brief/clarify/answers
   */
  async submitAnswers(request: ClarificationAnswersRequest): Promise<ApiResponse<ClarificationAnswersResponse>> {
    await this.delay(1000);

    // Mock: trả về status ready sau khi submit
    return this.success({
      status: 'ready',
      round: 2,
    });
  }

  /**
   * GET /brief/clarify/status
   */
  async getClarificationStatus(): Promise<ApiResponse<ClarificationStatusResponse>> {
    await this.delay(300);

    return this.success({
      clarification_id: 'clarify-abc123',
      status: 'ready',
      current_round: 2,
      total_rounds: 2,
      master_brief_path: '.midicoder/versions/v1.0.0/briefs/master-brief.md',
      clarification_log: {
        total_questions: 2,
        total_tokens_used: 1234,
      },
    });
  }

  /**
   * POST /brief/save
   */
  async saveBrief(request: BriefSaveRequest): Promise<ApiResponse<BriefSaveResponse>> {
    await this.delay(500);

    return this.success({
      saved_path: `.midicoder/versions/v1.0.0/briefs/library/${request.name}.md`,
    });
  }

  /**
   * GET /brief/library
   */
  async getBriefLibrary(): Promise<ApiResponse<Brief[]>> {
    await this.delay(300);

    return this.success([
      {
        name: 'multi-tenant-ecommerce',
        domain: 'e-commerce',
        tags: ['ecommerce', 'multi-tenant'],
        created_at: this.getTimestamp(),
        usage_count: 3,
      },
    ]);
  }

  // ============================================================================
  // CONTRACT ENDPOINTS
  // ============================================================================

  /**
   * POST /contract/gen
   */
  async generateContract(request: ContractGenRequest): Promise<ApiResponse<ContractGenResponse>> {
    await this.delay(2000);

    return this.success({
      status: 'completed',
      artifacts: {
        ir_path: '.midicoder/versions/v1.0.0/contracts/ir.json',
        manifest_path: '.midicoder/versions/v1.0.0/contracts/manifest.json',
        schemas_path: '.midicoder/versions/v1.0.0/contracts/schemas/',
      },
      summary: {
        entities: 12,
        commands: 8,
        queries: 6,
        events: 15,
        workflows: 4,
      },
      llm_usage: {
        tokens_used: 15678,
        requests: 8,
      },
    });
  }

  /**
   * POST /contract/check
   */
  async checkContract(request: ContractCheckRequest): Promise<ApiResponse<ContractCheckResponse>> {
    await this.delay(1000);

    return this.success({
      status: 'passed_with_fixes',
      errors: {
        before: 3,
        after: 0,
        auto_fixed: 3,
      },
      warnings: 2,
      report_path: '.midicoder/versions/v1.0.0/contracts/validation-report.json',
    });
  }

  /**
   * GET /contract/ir
   */
  async getContractIR(): Promise<ApiResponse<ContractIR>> {
    await this.delay(500);

    return this.success({
      schema: 'midicoder-contract-v1',
      domain: 'multi-channel-ecommerce',
      version: '1.0.0',
      entities: [
        { name: 'Product', table: 'products' },
        { name: 'Order', table: 'orders' },
        { name: 'Tenant', table: 'tenants' },
      ],
      commands: [],
      queries: [],
      events: [],
      workflows: [],
    });
  }

  // ============================================================================
  // IR ENDPOINTS
  // ============================================================================

  /**
   * POST /ir/build
   */
  async buildIR(request: IRBuildRequest): Promise<ApiResponse<IRBuildResponse>> {
    await this.delay(1500);

    return this.success({
      artifacts: {
        mir_path: '.midicoder/versions/v1.0.0/ir/mir.json',
        symbol_table_path: '.midicoder/versions/v1.0.0/ir/symbol-table.json',
      },
      metadata: {
        total_entities: 12,
        total_commands: 8,
        total_queries: 6,
        total_events: 15,
      },
    });
  }

  /**
   * GET /ir/mir
   */
  async getMIR(): Promise<ApiResponse<MIR>> {
    await this.delay(500);

    return this.success({
      schema: 'midicoder-mir-v1',
      version: '1.0.0',
      generated_at: this.getTimestamp(),
      source: {
        contract: 'contracts/ir.json',
        manifest: 'contracts/manifest.json',
      },
      modules: [
        {
          name: 'product-module',
          entities: [
            {
              id: 'entity-product',
              name: 'Product',
              table: 'products',
              fields: [
                { id: 'field-id', name: 'id', type: 'uuid' },
                { id: 'field-sku', name: 'sku', type: 'string' },
              ],
            },
          ],
        },
      ],
      metadata: {},
    });
  }

  // ============================================================================
  // CODE ENDPOINTS
  // ============================================================================

  /**
   * POST /code/plan
   */
  async planCode(request: CodePlanRequest): Promise<ApiResponse<CodePlanResponse>> {
    await this.delay(1000);

    return this.success({
      artifacts: {
        lowering_path: '.midicoder/versions/v1.0.0/plan/lowering.json',
        patches_path: '.midicoder/versions/v1.0.0/plan/patches/',
      },
      summary: {
        total_files: 87,
        backend_files: 54,
        frontend_files: 33,
      },
    });
  }

  /**
   * POST /code/gen
   */
  async generateCode(request: CodeGenRequest): Promise<ApiResponse<CodeGenResponse>> {
    await this.delay(3000);

    return this.success({
      artifacts: {
        generated_path: '.midicoder/versions/v1.0.0/code/generated/',
        report_path: '.midicoder/versions/v1.0.0/code/report.json',
      },
      summary: {
        total_files: 87,
        total_lines: 12456,
        templates_used: 24,
      },
    });
  }

  /**
   * POST /code/apply
   */
  async applyCode(request: CodeApplyRequest): Promise<ApiResponse<CodeApplyResponse>> {
    await this.delay(2000);

    return this.success({
      target_dir: request.target_dir,
      summary: {
        total_files: 87,
        applied: 87,
        skipped: 0,
        conflicts: 0,
        backups_created: request.backup ? 87 : 0,
      },
      status_path: '.midicoder/versions/v1.0.0/code/applied/status.json',
    });
  }

  /**
   * GET /code/files
   */
  async getCodeFiles(): Promise<ApiResponse<CodeFile[]>> {
    await this.delay(300);

    return this.success([
      { path: 'src/product/product.controller.ts', type: 'controller', lines: 234, status: 'generated' },
      { path: 'src/product/product.service.ts', type: 'service', lines: 456, status: 'generated' },
      { path: 'src/product/product.model.ts', type: 'model', lines: 123, status: 'generated' },
    ]);
  }

  // ============================================================================
  // PREVIEW ENDPOINTS
  // ============================================================================

  /**
   * POST /preview/start
   */
  async startPreview(request: PreviewStartRequest): Promise<ApiResponse<PreviewStartResponse>> {
    await this.delay(1000);

    return this.success({
      status: 'starting',
      urls: {
        frontend: 'http://localhost:3000',
        backend: 'http://localhost:3001',
      },
      docker_compose_path: '.midicoder/runtime/docker-compose.yml',
    });
  }

  /**
   * POST /preview/stop
   */
  async stopPreview(): Promise<ApiResponse> {
    await this.delay(500);

    return this.success({}, 'Preview stopped');
  }

  /**
   * GET /preview/status
   */
  async getPreviewStatus(): Promise<ApiResponse<PreviewStatusResponse>> {
    await this.delay(300);

    return this.success({
      status: 'running',
      services: {
        backend: { status: 'running', port: 3001 },
        frontend: { status: 'running', port: 3000 },
        db: { status: 'running', port: 5432 },
      },
      logs: {
        backend: 'Server started on port 3001...',
        frontend: 'Build successful. Serving on port 3000...',
      },
    });
  }

  // ============================================================================
  // FEEDBACK ENDPOINT
  // ============================================================================

  /**
   * POST /feedback
   */
  async submitFeedback(request: FeedbackRequest): Promise<ApiResponse<FeedbackResponse>> {
    await this.delay(2000);

    return this.success({
      patch_brief_path: '.midicoder/versions/v1.0.0/briefs/patch-briefs/patch-20260409.md',
      analysis: {
        identified_changes: ['Add Category entity', 'Add filter parameters'],
        impact: {
          breaking_changes: false,
          new_entities: 1,
          modified_queries: 1,
        },
      },
      pipeline_triggered: request.auto_apply ?? true,
      pipeline_status: 'running',
      pipeline_progress: {
        contract_gen: 'in_progress',
        contract_check: 'pending',
        ir_build: 'pending',
        code_plan: 'pending',
        code_gen: 'pending',
        code_apply: 'pending',
      },
    });
  }

  // ============================================================================
  // SYSTEM ENDPOINTS
  // ============================================================================

  /**
   * GET /status
   */
  async getStatus(): Promise<ApiResponse<PipelineStatus>> {
    await this.delay(300);

    return this.success({
      project: {
        name: 'my-saas-platform',
        initialized: true,
      },
      active_version: 'v1.0.0',
      pipeline_progress: {
        init: { status: 'complete', completed_at: this.getTimestamp() },
        brief: { status: 'complete', completed_at: this.getTimestamp() },
        contract: { status: 'complete', completed_at: this.getTimestamp() },
        ir: { status: 'complete', completed_at: this.getTimestamp() },
        code: { status: 'in_progress', current_step: 'code_gen' },
      },
      artifacts: {
        briefs: { master_brief: 'exists', working_brief: 'exists' },
        contracts: { ir: 'exists', manifest: 'exists' },
        ir: { mir: 'exists', symbol_table: 'exists' },
        code: { plan: 'exists', generated: 'exists', applied: 'pending' },
      },
    });
  }

  // ============================================================================
  // NEWS ENDPOINT (external API mock)
  // ============================================================================

  /**
   * GET https://midicoder.com/api/news
   */
  async getNews(): Promise<ApiResponse<NewsResponse>> {
    await this.delay(500);

    return this.success({
      news: [
        {
          id: 'news-001',
          type: 'announcement',
          title: 'Midicoder v1.0 Released!',
          content: "We're excited to announce the release of Midicoder v1.0!",
          link: 'https://midicoder.com/blog/v1-release',
          priority: 'high',
          created_at: this.getTimestamp(),
          expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: 'news-002',
          type: 'release',
          title: 'v1.0.1 Patch Notes',
          content: 'Bug fixes and improvements...',
          version: '1.0.1',
          created_at: this.getTimestamp(),
        },
        {
          id: 'news-003',
          type: 'blog',
          title: 'Best Practices for Writing Briefs',
          content: 'Learn how to write effective briefs for Midicoder...',
          link: 'https://midicoder.com/blog/brief-best-practices',
          created_at: this.getTimestamp(),
        },
      ],
    });
  }

  // ============================================================================
  // UTILITY
  // ============================================================================

  /**
   * Delay helper để giả lập network latency
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}