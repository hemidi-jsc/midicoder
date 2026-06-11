"""
Brief Commands Implementation.

Lệnh quản lý briefs:
- brief analyze: Phân tích brief bằng LLM, lưu kết quả vào artifact
- brief freeze: Đóng brief (status → freezed), version (draft → inbuild)
"""

import json
import uuid
from pathlib import Path
from typing import Optional

from midicoder.storage.sqlite import (
    BriefsManager,
    ArtifactsManager,
    get_connection,
)
from midicoder.storage.activity import log
from midicoder.pipeline.config import get_config
from midicoder.pipeline.analyze import (
    BriefAnalysis,
    analyze_brief_with_llm,
)


def _analyze_with_llm(
    brief_content: str,
    domain: Optional[str],
    brief_id: str,
) -> BriefAnalysis:
    """
    CLI wrapper cho analyze_brief_with_llm — thêm activity log output.

    Delegate vào pure module (midicoder.pipeline.analyze), thêm progress
    output cho CLI user.
    """
    log("brief.analyzing", resource_type="brief", resource_id=brief_id, details={"step": "detecting_domain"})
    try:
        analysis = analyze_brief_with_llm(
            brief_content=brief_content,
            domain=domain,
            brief_id=brief_id,
        )
    except Exception as e:
        log("llm.failed", resource_type="brief", resource_id=brief_id, details={"error": str(e)}, status="error")
        raise

    log("brief.analyzed", resource_type="brief", resource_id=brief_id, details={
        "domain": analysis.domain,
        "tokens_used": analysis.tokens_used,
        "latency_ms": analysis.latency_ms,
        "confidence": analysis.confidence,
    })
    log("brief.json_parsed", resource_type="brief", resource_id=brief_id)

    return analysis


def _execute_analyze(domain: Optional[str] = None, force: bool = False) -> None:
    """
    Thực thi phân tích brief.

    Brief file được đọc từ:
    .midicoder/versions/{active_version}/brief.md

    Args:
        domain: Tên domain (optional)
        force: Ghi đè brief cũ mà không hỏi confirmation

    Raises:
        SystemExit: Nếu brief file không tồn tại hoặc không có active version
    """
    log("brief.analyze_started", resource_type="brief", details={"domain": domain})

    # Bước 1: Lấy active_version từ config
    config = get_config()
    active_version = config.get("active_version")

    if not active_version:
        log("config.missing_active_version", resource_type="brief", status="error", details={"error": "Không tìm thấy active_version"})
        raise SystemExit(1)

    # Bước 2: Xác định đường dẫn brief file
    versions_dir = Path(".midicoder/versions") / active_version
    brief_file = versions_dir / "brief.md"

    if not brief_file.exists():
        log("brief.file_not_found", resource_type="brief", status="error", details={"path": str(brief_file)})
        raise SystemExit(1)

    content = brief_file.read_text(encoding="utf-8")
    log("brief.file_read", resource_type="brief", details={"path": str(brief_file), "version": active_version, "size": len(content)})

    # Bước 2: Kiểm tra đã có brief chưa
    briefs_manager = BriefsManager()
    briefs_manager.init()

    # Tìm brief cùng source file
    existing = None
    for brief in briefs_manager.list():
        if brief.get("source_file") == str(brief_file.absolute()):
            existing = brief
            break

    if existing:
        if force:
            log("brief.overriding_existing", resource_type="brief", resource_id=existing.get("brief_id"), details={"reason": "--force"})
        else:
            log("brief.skipped_existing", resource_type="brief", resource_id=existing.get("brief_id"), details={"reason": "already exists, use --force"})
            return

    # Bước 3: Tạo brief
    brief_id = f"brief-{uuid.uuid4().hex[:8]}"
    version = "v1.0.0"

    # Extract title from first line
    title = content.split("\n")[0].replace("#", "").strip() or brief_file.stem

    record = briefs_manager.create(
        brief_id=brief_id,
        version=version,
        content=content,
        title=title,
    )

    briefs_manager.add_revision(brief_id, version, "created", "Brief created", content)

    log("brief.created", resource_type="brief", resource_id=brief_id, details={"status": record["status"]})

    # Bước 4: LLM analysis
    log("llm.analysis_started", resource_type="brief", resource_id=brief_id)

    try:
        # Gọi LLM để phân tích
        analysis = _analyze_with_llm(
            brief_content=content,
            domain=domain,
            brief_id=brief_id,
        )

        briefs_manager.add_revision(brief_id, version, "analyzed", "LLM analysis completed", content)

        # Bước 5: Lưu kết quả vào artifact
        artifacts_manager = ArtifactsManager()
        artifacts_manager.init()
        artifacts_manager.create(
            artifact_id=f"analysis-{brief_id}",
            artifact_type="analysis",
            name="Brief Analysis",
            version=version,
            brief_id=brief_id,
            content=json.dumps(analysis.json_data, indent=2, ensure_ascii=False),
            metadata={
                "domain": analysis.domain,
                "confidence": analysis.confidence,
                "tokens_used": analysis.tokens_used,
                "latency_ms": analysis.latency_ms,
                "summary": analysis.text_summary,
            },
        )

        log("artifact.saved", resource_type="artifact", resource_id=f"analysis-{brief_id}", details={"artifact_type": "analysis"})

        # Bước 6: Hiển thị tóm tắt
        log("brief.analysis_summary", resource_type="brief", resource_id=brief_id, details={"summary": analysis.text_summary})

    except Exception as e:
        log("llm.analysis_failed", resource_type="brief", resource_id=brief_id, details={"error": str(e)}, status="error")
        raise SystemExit(1)

    # Done
    log("brief.analyze_completed", resource_type="brief", resource_id=brief_id)


def freeze_brief(version: str, project_cwd: str) -> dict:
    """
    Đóng brief: brief status → freezed, version status draft → inbuild.

    Ghi đồng bộ vào:
    - briefs.db: brief status → freezed
    - projects.db: version status → inbuild
    - .midicoder/versions/{v}/metadata.yml: status → inbuild

    Args:
        version: Version name (vd: "v1.0.0")
        project_cwd: Absolute path đến project root

    Returns:
        dict: {brief_id, status} nếu thành công

    Raises:
        MidicoderError: Nếu không tìm thấy brief hoặc brief đã freezed
    """
    briefs_db = Path(project_cwd) / ".midicoder" / "data" / "briefs.db"

    briefs_manager = BriefsManager(db_path=briefs_db)
    briefs_manager.init()

    # Find brief for this version
    target = None
    for b in briefs_manager.list(version=version):
        target = b
        break

    if not target:
        EM.raise_error(
            ErrorCode.CONFIG_READ_FAILED,
            message="Không tìm thấy brief",
            path=str(briefs_db),
        )

    if target.get("status") == "freezed":
        EM.raise_error(
            ErrorCode.CONFIG_READ_FAILED,
            message="Brief đã được đóng băng rồi",
            path=str(briefs_db),
        )

    brief_id = target.get("brief_id")

    # 1. Update brief status in briefs.db
    briefs_manager.update_status(brief_id, "freezed")
    log("brief.freezed", resource_type="brief", resource_id=brief_id, details={"brief_id": brief_id})

    # 2. Record revision lineage
    try:
        briefs_manager.add_revision(brief_id, version, "freezed", "Brief freezed, version → inbuild", "")
    except Exception:
        pass

    # 3. Update version status in projects.db (SQLite)
    try:
        from midicoder.storage.projects import ProjectsManager
        pm = ProjectsManager()
        pm.init()
        active_project = pm.get_active()
        if active_project:
            pm.version_update_status(active_project["project_id"], version, "inbuild")
            log("version.status_changed", resource_type="version", resource_id=version, details={"from": "draft", "to": "inbuild", "source": "sqlite"})
    except Exception:
        pass

    # 4. Update metadata.yml (filesystem) — SQLite là nguồn sự thật, sync ra file
    try:
        import yaml as _yaml
        meta_file = Path(project_cwd) / ".midicoder" / "versions" / version / "metadata.yml"
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = _yaml.safe_load(f) or {}
            meta["status"] = "inbuild"
            with open(meta_file, "w", encoding="utf-8") as f:
                _yaml.dump(meta, f, default_flow_style=False, allow_unicode=True)
            log("version.status_synced", resource_type="version", resource_id=version, details={"source": "metadata.yml"})
    except Exception:
        pass

    log("brief.freeze_completed", resource_type="brief", resource_id=brief_id, details={"version": version})

    return {"brief_id": brief_id, "status": "freezed"}
