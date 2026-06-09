"""
Router cho system logs
Đọc log file từ launcher và trả về cho frontend
"""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, Query

from midicoder.api.i18n import i18n
from midicoder.api.models import ApiResponse

router = APIRouter(prefix="/system", tags=["System"])


def _find_log_dir() -> Path:
    """Tìm thư mục logs của midicoder."""
    return Path.home() / ".midicoder" / "logs"


def _find_log_files() -> list[dict]:
    """List tất cả file log, sắp xếp mới nhất trước."""
    log_dir = _find_log_dir()
    if not log_dir.exists():
        return []

    files = []
    for f in sorted(log_dir.glob("midicoder-*.log"), reverse=True):
        stat = f.stat()
        files.append({
            "filename": f.name,
            "path": str(f),
            "size": stat.st_size,
            "modified": str(stat.st_mtime),
        })
    return files


def _read_log_lines(filepath: str, tail: int = 2000) -> list[str]:
    """Đọc N dòng cuối của log file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return [line.rstrip("\n") for line in lines[-tail:]]
    except Exception:
        return []


@router.get("/log-files", response_model=ApiResponse)
async def list_log_files(request: Request):
    """List tất cả log files."""
    language = i18n.get_language_from_request(request)
    files = _find_log_files()

    return ApiResponse(
        success=True,
        data={"files": files, "count": len(files)},
        message=i18n.translate("common.success", language),
        language=language,
    )


@router.get("/logs", response_model=ApiResponse)
async def get_logs(
    request: Request,
    file: Optional[str] = Query(None, description="Tên file log (default: file mới nhất)"),
    lines: int = Query(2000, ge=100, le=10000, description="Số dòng từ cuối file"),
):
    """
    Lấy nội dung log file (N dòng cuối).
    Nếu không chỉ định file, lấy file mới nhất.
    """
    language = i18n.get_language_from_request(request)

    log_dir = _find_log_dir()
    if not log_dir.exists():
        return ApiResponse(
            success=True,
            data={"lines": [], "file": None, "total": 0},
            message="Log directory not found",
            language=language,
        )

    # Tìm file log
    if file:
        filepath = log_dir / file
        if not filepath.exists():
            return ApiResponse(
                success=False,
                data={"lines": [], "file": None, "total": 0},
                message=f"Log file not found: {file}",
                language=language,
            )
    else:
        # Lấy file mới nhất
        log_files = sorted(log_dir.glob("midicoder-*.log"), reverse=True)
        if not log_files:
            return ApiResponse(
                success=True,
                data={"lines": [], "file": None, "total": 0},
                message="No log files found",
                language=language,
            )
        filepath = log_files[0]
        file = filepath.name

    content_lines = _read_log_lines(str(filepath), tail=lines)

    return ApiResponse(
        success=True,
        data={
            "lines": content_lines,
            "file": file,
            "total": len(content_lines),
        },
        message=i18n.translate("common.success", language),
        language=language,
    )
