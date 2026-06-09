/**
 * Shared API type definitions for Midicoder WebGUI
 */

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
  };
}

export interface UserResponse {
  id: string;
  email: string;
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
// END OF TYPES
// ============================================================================
