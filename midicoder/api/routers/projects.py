"""
Projects router — multi-project management via pipeline_bridge.

Tất cả logic nằm trong midicoder/pipeline/commands/project.py.
Router chỉ gọi qua pipeline_bridge và wrap response.
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from midicoder.api.i18n import i18n
from midicoder.api.models import ApiResponse
from midicoder.api.pipeline_bridge import pipeline_bridge

router = APIRouter(prefix="/projects", tags=["Projects"])


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., description="Tên project")
    path: str = Field(..., description="Đường dẫn tuyệt đối đến folder project")
    tech_stack: dict = Field(..., description="Tech stack selection: { infrastructure, backend, frontend, ui_framework }")
    prompt_domain: str = Field(..., description="Prompt engineering domain (default, ecommerce, ...)")


class ProjectUpdateRequest(BaseModel):
    name: str = Field(default=None, description="Tên mới")


# ============================================================================
# GET /projects/techstacks — return available stacks + prompt domains
# ============================================================================

@router.get("/techstacks", response_model=ApiResponse)
async def get_techstacks(request: Request):
    """Lấy danh sách tech stack và prompt domain hỗ trợ."""
    language = i18n.get_language_from_request(request)
    try:
        result = await pipeline_bridge.execute_command("project", "techstacks")
        if result["success"]:
            data = result.get("_data", {})
            return ApiResponse(
                success=True,
                data={
                    "stacks": data.get("stacks", {}),
                    "prompt_domains": data.get("prompt_domains", []),
                },
                language=language,
            )
        return ApiResponse(
            success=False, data=None, message=result.get("stderr", ""), language=language
        )
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


# ============================================================================
# GET /projects — list tất cả projects
# ============================================================================

@router.get("/", response_model=ApiResponse)
async def list_projects(request: Request):
    """Lấy danh sách tất cả projects và project đang active."""
    language = i18n.get_language_from_request(request)
    try:
        result = await pipeline_bridge.execute_command("project", "list")
        if result["success"]:
            data = result.get("_data", {})
            return ApiResponse(
                success=True,
                data={
                    "projects": data.get("projects", []),
                    "active": data.get("active"),
                },
                language=language,
            )
        return ApiResponse(
            success=False, data=None, message=result.get("stderr", ""), language=language
        )
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


# ============================================================================
# POST /projects — tạo project mới + init workspace
# ============================================================================

@router.post("/", response_model=ApiResponse)
async def create_project(request_data: ProjectCreateRequest, request: Request):
    """Tạo project mới — delegate vào pipeline.commands.project."""
    language = i18n.get_language_from_request(request)
    try:
        result = await pipeline_bridge.execute_command(
            "project", "create",
            name=request_data.name,
            path=request_data.path,
            tech_stack=request_data.tech_stack,
            prompt_domain=request_data.prompt_domain,
        )
        if result["success"]:
            data = result.get("_data", {})
            project = data.get("project", {})
            created = data.get("created", True)

            msg = f"Project '{request_data.name}' đã được tạo thành công"
            if not created:
                if data.get("already_exists"):
                    msg = "Project đã tồn tại, đã đánh dấu active"
                elif data.get("imported"):
                    msg = f"Đã import project '{request_data.name}' từ disk"

            return ApiResponse(
                success=True,
                data={"project": project, "created": created, "already_exists": data.get("already_exists", False)},
                message=msg,
                language=language,
            )
        return ApiResponse(
            success=False, data=None, message=result.get("stderr", "Tạo project thất bại"), language=language
        )
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


# ============================================================================
# POST /projects/:id/activate — chuyển project active
# ============================================================================

@router.post("/{project_id}/activate", response_model=ApiResponse)
async def activate_project(project_id: str, request: Request):
    """Đánh dấu project là active."""
    language = i18n.get_language_from_request(request)
    try:
        result = await pipeline_bridge.execute_command(
            "project", "activate", project_id=project_id
        )
        if result["success"]:
            data = result.get("_data", {})
            project = data.get("project", {})
            return ApiResponse(
                success=True,
                data={"project": project},
                message=f"Đã chuyển sang project '{project.get('name', project_id)}'",
                language=language,
            )
        return ApiResponse(
            success=False, data=None, message=result.get("stderr", ""), language=language
        )
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


# ============================================================================
# DELETE /projects/:id — xóa project khỏi registry
# ============================================================================

@router.delete("/{project_id}", response_model=ApiResponse)
async def delete_project(project_id: str, request: Request):
    """Xóa project khỏi registry (không xóa thư mục trên disk)."""
    language = i18n.get_language_from_request(request)
    try:
        result = await pipeline_bridge.execute_command(
            "project", "delete", project_id=project_id
        )
        if result["success"]:
            data = result.get("_data", {})
            name = data.get("name", project_id)
            return ApiResponse(
                success=True,
                data=None,
                message=f"Đã xóa project '{name}' khỏi registry",
                language=language,
            )
        return ApiResponse(
            success=False, data=None, message=result.get("stderr", ""), language=language
        )
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


# ============================================================================
# GET /projects/active — lấy project đang active
# ============================================================================

@router.get("/active", response_model=ApiResponse)
async def get_active_project(request: Request):
    """Lấy project đang active."""
    language = i18n.get_language_from_request(request)
    try:
        result = await pipeline_bridge.execute_command("project", "active")
        if result["success"]:
            data = result.get("_data", None)
            return ApiResponse(
                success=True,
                data={"project": data},
                language=language,
            )
        return ApiResponse(
            success=False, data=None, message=result.get("stderr", ""), language=language
        )
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)
