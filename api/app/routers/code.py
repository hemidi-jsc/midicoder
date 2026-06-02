"""
Router cho các commands về code
"""

from fastapi import APIRouter, Query, Request

from app.cli_wrapper import cli_wrapper
from app.i18n import i18n
from app.models import ApiResponse, CodeGenRequest, CodeApplyRequest

router = APIRouter(prefix="/code", tags=["Code"])


@router.post("/build", response_model=ApiResponse)
async def build_code_plan(request: Request):
    """
    Build code plan từ IR
    
    Args:
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả build code plan
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để build code plan
    result = await cli_wrapper.code_build()
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data={
                "built": True,
                "plan_path": ".midicoder/versions/<version>/plan/lowering.json",
            },
            message=i18n.translate("code.build_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.post("/plan", response_model=ApiResponse)
async def plan_code(request: Request):
    """
    Plan code (alias của build)
    
    Args:
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả plan code
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để plan code
    result = await cli_wrapper.code_plan()
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data={
                "planned": True,
                "plan_path": ".midicoder/versions/<version>/plan/lowering.json",
            },
            message=i18n.translate("code.build_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.post("/gen", response_model=ApiResponse)
async def generate_code(request_data: CodeGenRequest = None, request: Request = None):
    """
    Generate code từ plan
    
    Args:
        request_data: Tham số generate code
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả generate code
    """
    if request_data is None:
        request_data = CodeGenRequest()
    
    language = i18n.get_language_from_request(request) if request else "vi"
    
    # Gọi CLI wrapper để generate code
    result = await cli_wrapper.code_gen(runtime=request_data.runtime)
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data={
                "generated": True,
                "generated_path": ".midicoder/versions/<version>/code/generated",
                "report_path": ".midicoder/versions/<version>/code/report.json",
            },
            message=i18n.translate("code.gen_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.post("/apply", response_model=ApiResponse)
async def apply_code(request_data: CodeApplyRequest = None, request: Request = None):
    """
    Apply code vào working directory
    
    Args:
        request_data: Tham số apply code
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả apply code
    """
    if request_data is None:
        request_data = CodeApplyRequest()
    
    language = i18n.get_language_from_request(request) if request else "vi"

    # Gọi CLI wrapper để apply code
    result = await cli_wrapper.code_apply(
        force=request_data.force,
        dry_run=request_data.dry_run,
        no_reindex=request_data.no_reindex,
        patches_subdir=request_data.patches_subdir,
    )

    if result["success"]:
        return ApiResponse(
            success=True,
            data={
                "applied": True,
                "status_path": ".midicoder/versions/<version>/code/applied/status.json",
            },
            message=i18n.translate("code.apply_success", language),
            language=language,
        )

    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


# ============================================================================
# GET endpoints — plan từ SQLite ArtifactsManager, code files từ disk
# ============================================================================

@router.get("/files", response_model=ApiResponse)
async def list_code_files(version: str = Query(None), request: Request = None):
    """List generated code files từ disk (generated source code)."""
    language = i18n.get_language_from_request(request)
    try:
        from pathlib import Path
        from app.config import get_project_cwd, get_active_version
        files = []
        project_cwd = Path(get_project_cwd())
        v = version or get_active_version() or "v1.0.0"
        code_dir = project_cwd / ".midicoder" / "versions" / v / "code" / "generated"
        if code_dir.exists():
            for child in sorted(code_dir.rglob("*")):
                if child.is_file():
                    rel_path = str(child.relative_to(code_dir))
                    files.append({
                        "path": rel_path,
                        "type": child.suffix.lstrip(".") or "text",
                        "size": child.stat().st_size,
                        "status": "generated",
                    })
        return ApiResponse(success=True, data={"files": files, "count": len(files)}, language=language)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


@router.get("/file/{file_path:path}", response_model=ApiResponse)
async def get_code_file(file_path: str, version: str = Query(None), request: Request = None):
    """Lấy nội dung file code đã generate từ disk."""
    language = i18n.get_language_from_request(request)
    try:
        from pathlib import Path
        from app.config import get_project_cwd, get_active_version
        project_cwd = Path(get_project_cwd())
        v = version or get_active_version() or "v1.0.0"
        file_full = project_cwd / ".midicoder" / "versions" / v / "code" / "generated" / file_path
        if not file_full.exists():
            return ApiResponse(success=False, data=None, message=f"File not found: {file_path}", language=language)
        content = file_full.read_text(encoding="utf-8")
        return ApiResponse(success=True, data={"path": file_path, "content": content}, language=language)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)


@router.get("/plan", response_model=ApiResponse)
async def get_code_plan(version: str = Query(None), request: Request = None):
    """Lấy lowering plan JSON từ SQLite ArtifactsManager."""
    language = i18n.get_language_from_request(request)
    try:
        import json
        from midicoder.storage.sqlite import ArtifactsManager
        from app.config import get_active_version
        mgr = ArtifactsManager()
        mgr.init()
        artifacts = mgr.list_by_type("plan")
        if not artifacts:
            return ApiResponse(success=False, data=None, message="Code plan not found", language=language)
        target_version = version or get_active_version() or "v1.0.0"
        for art in artifacts:
            aid = art.get("artifact_id", "")
            art_version = art.get("version", "")
            if aid == f"plan-{target_version}" or art_version == target_version:
                content = art.get("content", "")
                try:
                    data = json.loads(content)
                except (json.JSONDecodeError, TypeError):
                    data = {"raw": content}
                return ApiResponse(success=True, data=data, language=language)
        # Fallback: lấy plan mới nhất
        content = artifacts[0].get("content", "")
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            data = {"raw": content}
        return ApiResponse(success=True, data=data, language=language)
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e), language=language)