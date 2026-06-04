"""
Pydantic models cho API — request/response bodies.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    success: bool = Field(..., description="Kết quả thành công hay thất bại")
    data: Optional[Any] = Field(default=None, description="Dữ liệu trả về")
    message: Optional[str] = Field(default=None, description="Thông điệp")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Thời gian phản hồi")
    language: str = Field(default="vi", description="Ngôn ngữ của response")


class ErrorResponse(BaseModel):
    success: bool = Field(default=False)
    error: Dict[str, Any] = Field(..., description="Chi tiết lỗi")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    language: str = Field(default="vi")


class CLICommandRequest(BaseModel):
    command: str = Field(..., description="Tên command")
    subcommand: Optional[str] = Field(default=None, description="Subcommand")
    args: Dict[str, Any] = Field(default={}, description="Các đối số cho command")


class CLICommandResponse(BaseModel):
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
    key: str = Field(..., description="Key của config")


class ConfigSetRequest(BaseModel):
    key: str = Field(..., description="Key của config")
    value: str = Field(..., description="Giá trị mới")


class ConfigGetResponse(BaseModel):
    key: str
    value: Any


class ConfigListResponse(BaseModel):
    config: Dict[str, Any]


# ==================== Version Models ====================

class VersionCreateRequest(BaseModel):
    version: str = Field(..., description="Tên phiên bản")


class VersionCreateResponse(BaseModel):
    version: str
    created: bool


# ==================== Index Models ====================

class IndexReindexRequest(BaseModel):
    paths: list[str] = Field(default=[], description="Đường dẫn file đã thay đổi")


class IndexResponse(BaseModel):
    indexed: bool
    files_count: Optional[int] = None


# ==================== Brief Models ====================

class BriefAnalyzeResponse(BaseModel):
    analyzed: bool
    status: str
    ambiguities: list[Dict[str, Any]]


class BriefRewriteResponse(BaseModel):
    rewritten: bool
    content: Optional[str]


# ==================== Contract Models ====================

class ContractGenResponse(BaseModel):
    generated: bool
    contract_path: Optional[str]
    manifest_path: Optional[str]


class ContractCheckResponse(BaseModel):
    valid: bool
    errors: list[Dict[str, Any]]
    warnings: list[Dict[str, Any]]


class ContractFeedbackRequest(BaseModel):
    feedback: str = Field(..., description="Phản hồi về contract")


class ContractFeedbackResponse(BaseModel):
    processed: bool


# ==================== IR Models ====================

class IRBuildRequest(BaseModel):
    skip_diagrams: bool = Field(default=False)


class IRBuildResponse(BaseModel):
    built: bool
    mir_path: Optional[str]
    symbol_table_path: Optional[str]


# ==================== Code Models ====================

class CodeBuildResponse(BaseModel):
    built: bool
    plan_path: Optional[str]


class CodeGenRequest(BaseModel):
    runtime: bool = Field(default=False)


class CodeGenResponse(BaseModel):
    generated: bool
    generated_path: Optional[str]
    report_path: Optional[str]


class CodeApplyRequest(BaseModel):
    force: bool = Field(default=False)
    dry_run: bool = Field(default=False)
    no_reindex: bool = Field(default=False)
    patches_subdir: Optional[str] = Field(default=None)


class CodeApplyResponse(BaseModel):
    applied: bool
    files_count: Optional[int]
    conflicts: list[Dict[str, Any]]
    status_path: Optional[str]


# ==================== Runtime Models ====================

class RuntimeTestRequest(BaseModel):
    timeout: int = Field(default=30)
    port: int = Field(default=8000)
    verbose: bool = Field(default=False)


class RuntimeTestResponse(BaseModel):
    passed: bool
    errors: list[Dict[str, Any]]
    logs: str


class RuntimeFixRequest(BaseModel):
    log_timestamp: Optional[str] = Field(default=None)
    dry_run: bool = Field(default=False)
    auto_apply: bool = Field(default=False)
    auto_fix_loop: bool = Field(default=False)
    test_timeout: int = Field(default=30)
    test_port: int = Field(default=8000)


class RuntimeFixResponse(BaseModel):
    fixed: bool
    patch_plans: list[str]
    applied: bool


# ==================== Health & Status Models ====================

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str
    timestamp: datetime


class LanguagesResponse(BaseModel):
    languages: list[str]
    default: str


# ==================== Pipeline Status Models ====================

class PipelineStatus(BaseModel):
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