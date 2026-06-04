"""
Các mô hình Pydantic cho API
Định nghĩa request/response bodies
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    """
    Response chung cho tất cả các endpoint
    """
    success: bool = Field(..., description="Kết quả thành công hay thất bại")
    data: Optional[Any] = Field(default=None, description="Dữ liệu trả về")
    message: Optional[str] = Field(default=None, description="Thông điệp")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Thời gian phản hồi")
    language: str = Field(default="vi", description="Ngôn ngữ của response")


class ErrorResponse(BaseModel):
    """
    Response lỗi
    """
    success: bool = Field(default=False)
    error: Dict[str, Any] = Field(..., description="Chi tiết lỗi")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    language: str = Field(default="vi")


class CLICommandRequest(BaseModel):
    """
    Request để thực thi một lệnh CLI
    """
    command: str = Field(..., description="Tên command (init, brief, contract, ir, code, runtime)")
    subcommand: Optional[str] = Field(default=None, description="Subcommand")
    args: Dict[str, Any] = Field(default={}, description="Các đối số cho command")


class CLICommandResponse(BaseModel):
    """
    Response từ việc thực thi CLI command
    """
    command: str
    subcommand: Optional[str]
    success: bool
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    duration_ms: int
    message: str


# ==================== Config Models ====================

class ConfigGetRequest(BaseModel):
    """Request lấy giá trị config"""
    key: str = Field(..., description="Key của config")


class ConfigSetRequest(BaseModel):
    """Request đặt giá trị config"""
    key: str = Field(..., description="Key của config")
    value: str = Field(..., description="Giá trị mới")


class ConfigGetResponse(BaseModel):
    """Response lấy giá trị config"""
    key: str
    value: Any


class ConfigListResponse(BaseModel):
    """Response danh sách config"""
    config: Dict[str, Any]


# ==================== Init Models ====================

class InitRequest(BaseModel):
    """Request khởi tạo dự án"""
    non_interactive: bool = Field(default=True, description="Chế độ không tương tác")
    working_dir: Optional[str] = Field(default=None, description="Thư mục làm việc")
    stack: Optional[str] = Field(default=None, description="Tech stack (e.g., fastapi,nest,angular)")
    llm_high_provider: Optional[str] = Field(default=None, description="LLM provider tier cao")
    llm_high_model: Optional[str] = Field(default=None, description="LLM model tier cao")
    llm_high_url: Optional[str] = Field(default=None, description="LLM URL tier cao")
    llm_high_key_env: Optional[str] = Field(default=None, description="Env var chứa API key tier cao")
    llm_cheap_provider: Optional[str] = Field(default=None, description="LLM provider tier rẻ")
    llm_cheap_model: Optional[str] = Field(default=None, description="LLM model tier rẻ")
    llm_cheap_url: Optional[str] = Field(default=None, description="LLM URL tier rẻ")
    llm_cheap_key_env: Optional[str] = Field(default=None, description="Env var chứa API key tier rẻ")


class InitResponse(BaseModel):
    """Response khởi tạo dự án"""
    initialized: bool
    working_dir: Optional[str]


# ==================== Version Models ====================

class VersionCreateRequest(BaseModel):
    """Request tạo phiên bản mới"""
    version: str = Field(..., description="Tên phiên bản (e.g., v1.0.0)")


class VersionCreateResponse(BaseModel):
    """Response tạo phiên bản"""
    version: str
    created: bool


# ==================== Index Models ====================

class IndexReindexRequest(BaseModel):
    """Request reindex các file đã thay đổi"""
    paths: list[str] = Field(default=[], description="Danh sách đường dẫn file đã thay đổi")


class IndexResponse(BaseModel):
    """Response index"""
    indexed: bool
    files_count: Optional[int] = None


# ==================== Brief Models ====================

class BriefAnalyzeResponse(BaseModel):
    """Response phân tích brief"""
    analyzed: bool
    status: str  # needs_clarification, ready_for_contract
    ambiguities: list[Dict[str, Any]]


class BriefRewriteResponse(BaseModel):
    """Response viết lại brief"""
    rewritten: bool
    content: Optional[str]


# ==================== Contract Models ====================

class ContractGenResponse(BaseModel):
    """Response tạo contract"""
    generated: bool
    contract_path: Optional[str]
    manifest_path: Optional[str]


class ContractCheckResponse(BaseModel):
    """Response kiểm tra contract"""
    valid: bool
    errors: list[Dict[str, Any]]
    warnings: list[Dict[str, Any]]


class ContractFeedbackRequest(BaseModel):
    """Request feedback cho contract"""
    feedback: str = Field(..., description="Phản hồi về contract")


class ContractFeedbackResponse(BaseModel):
    """Response feedback"""
    processed: bool


# ==================== IR Models ====================

class IRBuildRequest(BaseModel):
    """Request build IR"""
    skip_diagrams: bool = Field(default=False, description="Bỏ qua tạo diagrams")


class IRBuildResponse(BaseModel):
    """Response build IR"""
    built: bool
    mir_path: Optional[str]
    symbol_table_path: Optional[str]


# ==================== Code Models ====================

class CodeBuildResponse(BaseModel):
    """Response build code plan"""
    built: bool
    plan_path: Optional[str]


class CodeGenRequest(BaseModel):
    """Request generate code"""
    runtime: bool = Field(default=False, description="Cũng generate runtime files")


class CodeGenResponse(BaseModel):
    """Response generate code"""
    generated: bool
    generated_path: Optional[str]
    report_path: Optional[str]


class CodeApplyRequest(BaseModel):
    """Request apply code"""
    force: bool = Field(default=False, description="Force apply khi có conflict")
    dry_run: bool = Field(default=False, description="Xem trước mà không viết file")
    no_reindex: bool = Field(default=False, description="Tắt reindex (chỉ debug)")
    patches_subdir: Optional[str] = Field(default=None, description="Thư mục patches tùy chỉnh")


class CodeApplyResponse(BaseModel):
    """Response apply code"""
    applied: bool
    files_count: Optional[int]
    conflicts: list[Dict[str, Any]]
    status_path: Optional[str]


# ==================== Runtime Models ====================

class RuntimeTestRequest(BaseModel):
    """Request test runtime"""
    timeout: int = Field(default=30, description="Timeout tính bằng giây")
    port: int = Field(default=8000, description="Port cho FastAPI")
    verbose: bool = Field(default=False, description="Hiển thị output chi tiết")


class RuntimeTestResponse(BaseModel):
    """Response test runtime"""
    passed: bool
    errors: list[Dict[str, Any]]
    logs: str


class RuntimeFixRequest(BaseModel):
    """Request fix runtime errors"""
    log_timestamp: Optional[str] = Field(default=None, description="Timestamp cụ thể để fix")
    dry_run: bool = Field(default=False, description="Xem trước fixes")
    auto_apply: bool = Field(default=False, description="Tự động apply fixes")
    auto_fix_loop: bool = Field(default=False, description="Chạy loop fix cho đến khi pass")
    test_timeout: int = Field(default=30, description="Timeout cho mỗi lần test")
    test_port: int = Field(default=8000, description="Port cho test")


class RuntimeFixResponse(BaseModel):
    """Response fix runtime"""
    fixed: bool
    patch_plans: list[str]
    applied: bool


# ==================== Health & Status Models ====================

class HealthResponse(BaseModel):
    """Response health check"""
    status: str = "healthy"
    version: str
    timestamp: datetime


class LanguagesResponse(BaseModel):
    """Response danh sách ngôn ngữ"""
    languages: list[str]
    default: str


# ==================== Pipeline Status Models ====================

class PipelineStatus(BaseModel):
    """Trạng thái pipeline hiện tại"""
    version: Optional[str]
    brief_analyzed: bool = False
    brief_clarified: bool = False
    contract_generated: bool = False
    contract_validated: bool = False
    ir_built: bool = False
    code_planned: bool = False
    code_generated: bool = False
    code_applied: bool = False
    last_updated: Optional[datetime]