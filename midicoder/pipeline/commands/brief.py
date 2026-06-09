"""
Brief Commands Implementation.

Lệnh quản lý briefs theo SoT E02, E20:
- brief analyze: Phân tích brief bằng LLM → working-brief
- brief clarify: Interactive Q&A → master-brief
- brief save: Lưu vào library
- brief load: Load từ library
- brief list: Hiển thị danh sách briefs
- brief library: Hiển thị industry templates

Brief types (E01):
- working-brief: Brief đang phân tích (draft)
- master-brief: Brief đã clarify (frozen)
- patch-brief: Incremental changes từ feedback (draft)
- library-brief: Reusable templates (frozen)

Brief lifecycle:
user-brief.md → brief analyze → working-brief → brief clarify → master-brief → brief save → library-brief
"""

import json
import uuid
import time
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Optional, Any

from midicoder.storage.sqlite import (
    BriefsManager,
    ArtifactsManager,
    ProvenanceManager,
    get_connection,
)
from midicoder.pipeline.llm import load_llm_config, call_llm
from midicoder.pipeline.domain import (
    detect_domain,
    get_domain_prompt,
    normalize_domain,
)
from midicoder.pipeline.config import get_config
from midicoder.pipeline.context_feed import get_brief_context
from midicoder.pipeline.analyze import (
    BriefAnalysis,
    analyze_brief_with_llm,
)


def _log_activity(action: str, resource_type: str = "brief", resource_id: str = "", details: dict = None, status: str = "success") -> None:
    """Ghi activity log vào artifacts.db activity_log table."""
    data_dir = Path(".midicoder/data")
    artifacts_db = data_dir / "artifacts.db"
    if not artifacts_db.exists():
        return
    try:
        with get_connection(artifacts_db) as conn:
            conn.execute(
                """INSERT INTO activity_log (action, resource_type, resource_id, details, status)
                   VALUES (?, ?, ?, ?, ?)""",
                (action, resource_type, resource_id,
                 json.dumps(details) if details else None, status),
            )
    except Exception:
        pass


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
    _log_activity("brief.analyzing", resource_id=brief_id, details={"step": "detecting_domain"})
    try:
        analysis = analyze_brief_with_llm(
            brief_content=brief_content,
            domain=domain,
            brief_id=brief_id,
        )
    except Exception as e:
        _log_activity("llm.failed", resource_id=brief_id, details={"error": str(e)}, status="error")
        raise

    _log_activity("brief.analyzed", resource_id=brief_id, details={
        "domain": analysis.domain,
        "tokens_used": analysis.tokens_used,
        "latency_ms": analysis.latency_ms,
        "confidence": analysis.confidence,
    })
    _log_activity("brief.json_parsed", resource_id=brief_id)

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
    _log_activity("brief.analyze_started", details={"domain": domain})

    # Bước 1: Lấy active_version từ config
    config = get_config()
    active_version = config.get("active_version")

    if not active_version:
        _log_activity("config.missing_active_version", status="error", details={"error": "Không tìm thấy active_version"})
        raise SystemExit(1)

    # Bước 2: Xác định đường dẫn brief file
    versions_dir = Path(".midicoder/versions") / active_version
    brief_file = versions_dir / "brief.md"

    if not brief_file.exists():
        _log_activity("brief.file_not_found", status="error", details={"path": str(brief_file)})
        raise SystemExit(1)

    content = brief_file.read_text(encoding="utf-8")
    _log_activity("brief.file_read", details={"path": str(brief_file), "version": active_version, "size": len(content)})

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
            _log_activity("brief.overriding_existing", resource_id=existing.get("brief_id"), details={"reason": "--force"})
        else:
            _log_activity("brief.skipped_existing", resource_id=existing.get("brief_id"), details={"reason": "already exists, use --force"})
            return

    # Bước 3: Tạo working-brief
    brief_id = f"brief-{uuid.uuid4().hex[:8]}"
    version = "v1.0.0"

    # Extract title from first line
    title = content.split("\n")[0].replace("#", "").strip() or brief_file.stem

    record = briefs_manager.create(
        brief_id=brief_id,
        version=version,
        content=content,
        title=title,
        brief_type="working",  # working-brief theo SoT
    )

    # Lưu source_file vào brief record
    briefs_manager._update_source_file(brief_id, str(brief_file.absolute()))

    _log_activity("brief.created", resource_id=brief_id, details={"type": record["type"], "status": record["status"]})

    # Bước 4: LLM analysis
    _log_activity("llm.analysis_started", resource_id=brief_id)

    try:
        # Gọi LLM để phân tích
        analysis = _analyze_with_llm(
            brief_content=content,
            domain=domain,
            brief_id=brief_id,
        )

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

        _log_activity("artifact.saved", resource_id=f"analysis-{brief_id}", resource_type="artifact", details={"artifact_type": "analysis"})

        # Bước 5: Record provenance lineage
        try:
            provenance_manager = ProvenanceManager()
            provenance_manager.init()
            provenance_manager.record_lineage(
                entity_id=f"analysis-{brief_id}",
                entity_type="artifact",
                source_id=brief_id,
                source_type="brief",
                relationship="generated_from",
                metadata={
                    "domain": analysis.domain,
                    "confidence": analysis.confidence,
                    "tokens_used": analysis.tokens_used,
                    "latency_ms": analysis.latency_ms,
                },
            )
            _log_activity("provenance.recorded", resource_id=f"analysis-{brief_id}", resource_type="provenance")
        except Exception as e:
            _log_activity("provenance.failed", resource_id=f"analysis-{brief_id}", details={"error": str(e)}, status="warning")

        # Bước 6: Brief vẫn ở status draft sau analyze (clarify → clarified → user frozen)

        # Bước 7: Hiển thị tóm tắt
        _log_activity("brief.analysis_summary", resource_id=brief_id, details={"summary": analysis.text_summary})

    except Exception as e:
        _log_activity("llm.analysis_failed", resource_id=brief_id, details={"error": str(e)}, status="error")
        raise SystemExit(1)

    # Done
    _log_activity("brief.analyze_completed", resource_id=brief_id)


def _execute_save(name: str, tags: Optional[str] = None) -> None:
    """
    Thực thi lưu brief vào library.

    Args:
        name: Tên library brief
        tags: Comma-separated tags (optional)
    """
    _log_activity("brief.save_started", details={"name": name, "tags": tags})

    # Tìm master-brief
    briefs_manager = BriefsManager()
    briefs_manager.init()

    # Tìm brief có status = clarified
    master_brief = None
    for brief in briefs_manager.list():
        if brief.get("status") == "clarified":
            master_brief = brief
            break

    if not master_brief:
        _log_activity("brief.save_no_master", status="error", details={"error": "Không có master-brief đã clarified"})
        return

    brief_id = master_brief.get("brief_id")
    _log_activity("brief.save_info", resource_id=brief_id, details={"title": master_brief.get("title"), "tags": tags or "none"})

    # Save master-brief → library-brief trong SQLite
    briefs_manager.save_as_library(brief_id, name, tags)
    _log_activity("brief.type_updated", resource_id=brief_id, details={"from": "master", "to": "library"})
    _log_activity("brief.status_changed", resource_id=brief_id, details={"from": "clarified", "to": "frozen"})

    # Export đến industry/briefs/ (optional)
    industry_briefs = Path("industry/briefs") / name
    industry_briefs.mkdir(parents=True, exist_ok=True)
    brief_file = industry_briefs / "brief.md"
    content = master_brief.get("content")
    if content:
        brief_file.write_text(content, encoding="utf-8")
        _log_activity("brief.exported", resource_id=brief_id, details={"export_path": str(brief_file)})

    _log_activity("brief.saved", resource_id=brief_id, details={"library_name": name})


def _execute_load(name: str) -> None:
    """
    Thực thi load brief từ library.

    Args:
        name: Tên library brief
    """
    _log_activity("brief.load_started", details={"name": name})

    # Check industry/briefs folder
    industry_briefs = Path("industry/briefs") / name
    brief_file = industry_briefs / "brief.md"

    if brief_file.exists():
        _log_activity("brief.found_industry", details={"path": str(brief_file)})
        # Load content file → tạo working-brief mới trong SQLite
        content = brief_file.read_text(encoding="utf-8")
        new_brief_id = f"brief-{uuid.uuid4().hex[:8]}"
        briefs_manager = BriefsManager()
        briefs_manager.init()
        briefs_manager.create(
            brief_id=new_brief_id,
            version="v1.0.0",
            content=content,
            title=name,
            brief_type="working",
        )
        _log_activity("brief.created_from_industry", resource_id=new_brief_id, details={"source": "industry_briefs", "library_name": name})
    else:
        # Check SQLite library
        briefs_manager = BriefsManager()
        briefs_manager.init()

        library_brief = briefs_manager.get_library_brief(name)

        if library_brief:
            _log_activity("brief.found_in_sqlite", resource_id=library_brief.get("brief_id"))
            # Copy library-brief → working-brief mới
            new_brief_id = f"brief-{uuid.uuid4().hex[:8]}"
            new_brief = briefs_manager.duplicate_brief(
                library_brief["brief_id"], new_brief_id, "working"
            )
            if new_brief:
                _log_activity("brief.created_from_library", resource_id=new_brief["brief_id"], details={"type": new_brief["type"], "status": new_brief["status"], "source_id": library_brief["brief_id"]})
        else:
            _log_activity("brief.not_found", status="error", details={"name": name})
            return

    _log_activity("brief.loaded", details={"name": name})


def _execute_list(domain: Optional[str] = None) -> None:
    """
    Thực thi hiển thị danh sách briefs.

    Args:
        domain: Filter by domain (optional)
    """
    _log_activity("brief.list_started", details={"domain": domain})

    briefs_manager = BriefsManager()
    briefs_manager.init()

    briefs = briefs_manager.list()

    if not briefs:
        _log_activity("brief.list_empty", details={"total": 0})
        return

    # Group by type
    by_type = {"working": [], "master": [], "library": [], "patch": []}

    for brief in briefs:
        brief_type = brief.get("type", "working")
        if brief_type in by_type:
            by_type[brief_type].append(brief)

    # Build summary for activity log
    counts = {t: len(bs) for t, bs in by_type.items() if bs}
    _log_activity("brief.listed", details={"total": len(briefs), "counts": counts})


def _execute_library() -> None:
    """
    Thực thi hiển thị industry brief library.
    """
    _log_activity("library.list_started")

    # Check industry/briefs folder
    industry_briefs = Path("industry/briefs")
    if not industry_briefs.exists():
        _log_activity("library.folder_not_found", status="warning", details={"path": str(industry_briefs.absolute())})
        return

    # List available briefs
    brief_dirs = [d for d in industry_briefs.iterdir() if d.is_dir()]

    if not brief_dirs:
        _log_activity("library.empty", details={"total": 0})
        return

    # Build summary of available templates
    templates = []
    for brief_dir in sorted(brief_dirs):
        brief_file = brief_dir / "brief.md"
        if brief_file.exists():
            content = brief_file.read_text(encoding="utf-8")
            line_list = content.split("\n")
            title = brief_dir.name.replace("-", " ").title()
            desc = "No description"
            for line in line_list[:30]:
                if line.startswith("### Product Name"):
                    idx = line_list.index(line)
                    if idx + 2 < len(line_list):
                        desc = line_list[idx + 2].strip()
                        break
            templates.append({"name": brief_dir.name, "title": title, "desc": desc})

    _log_activity("library.listed", details={"total": len(brief_dirs), "templates_with_brief": len(templates)})


def freeze_brief(version: str, project_cwd: str) -> dict:
    """
    Đóng brief: brief status → frozen, version status draft → inbuild.

    Ghi đồng bộ vào:
    - briefs.db: brief status → frozen
    - projects.db: version status → inbuild
    - .midicoder/versions/{v}/metadata.yml: status → inbuild

    Args:
        version: Version name (vd: "v1.0.0")
        project_cwd: Absolute path đến project root

    Returns:
        dict: {brief_id, status} nếu thành công

    Raises:
        MidicoderError: Nếu không tìm thấy brief hoặc brief đã frozen
    """
    briefs_db = Path(project_cwd) / ".midicoder" / "data" / "briefs.db"

    briefs_manager = BriefsManager(db_path=briefs_db)
    briefs_manager.init()

    # Find working brief for this version
    target = None
    for b in briefs_manager.list(version=version):
        if b.get("type") == "working":
            target = b
            break

    if not target:
        EM.raise_error(
            ErrorCode.CONFIG_READ_FAILED,
            message="Không tìm thấy brief",
            path=str(briefs_db),
        )

    if target.get("status") == "frozen":
        EM.raise_error(
            ErrorCode.CONFIG_READ_FAILED,
            message="Brief đã được đóng rồi",
            path=str(briefs_db),
        )

    brief_id = target.get("brief_id")
    brief_hash = target.get("hash", "")

    # 1. Update brief status in briefs.db
    briefs_manager.update_status(brief_id, "frozen")
    _log_activity("brief.frozen", resource_id=brief_id, details={"brief_id": brief_id})

    # Log lineage
    try:
        with briefs_manager._get_connection() as conn:
            cursor = conn.execute("PRAGMA table_info(brief_lineage)")
            columns = [row["name"] for row in cursor.fetchall()]
            if "old_content_hash" in columns:
                conn.execute(
                    "INSERT INTO brief_lineage (brief_id, parent_brief_id, version, change_type, change_description, old_content_hash, new_content_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (brief_id, brief_id, version, "frozen", "Brief frozen", brief_hash, brief_hash),
                )
            else:
                conn.execute(
                    "INSERT INTO brief_lineage (brief_id, parent_brief_id, version, change_type, change_description) VALUES (?, ?, ?, ?, ?)",
                    (brief_id, brief_id, version, "frozen", "Brief frozen"),
                )
    except Exception:
        pass

    # 2. Update version status in projects.db (SQLite)
    try:
        from midicoder.storage.projects import ProjectsManager
        pm = ProjectsManager()
        pm.init()
        active_project = pm.get_active()
        if active_project:
            pm.version_update_status(active_project["project_id"], version, "inbuild")
            _log_activity("version.status_changed", resource_id=version, resource_type="version", details={"from": "draft", "to": "inbuild", "source": "sqlite"})
    except Exception:
        pass

    # 3. Update metadata.yml (filesystem) — SQLite là nguồn sự thật, sync ra file
    try:
        import yaml as _yaml
        meta_file = Path(project_cwd) / ".midicoder" / "versions" / version / "metadata.yml"
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = _yaml.safe_load(f) or {}
            meta["status"] = "inbuild"
            with open(meta_file, "w", encoding="utf-8") as f:
                _yaml.dump(meta, f, default_flow_style=False, allow_unicode=True)
            _log_activity("version.status_synced", resource_id=version, resource_type="version", details={"source": "metadata.yml"})
    except Exception:
        pass

    _log_activity("brief.freeze_completed", resource_id=brief_id, details={"version": version})

    return {"brief_id": brief_id, "status": "frozen"}
