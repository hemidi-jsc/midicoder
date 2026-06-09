"""
Code Generation Commands Implementation.

Lệnh quản lý code generation theo SoT E07, E20:
- code plan: Tạo implementation plan từ MIR
- code gen: Generate code từ plan + templates
- code apply: Apply code vào target directory

Pipeline:
MIR (SQLite) → code plan → Plan (SQLite) → code gen → Generated Files → code apply → Target

E07: Emitter & Scaffolder
"""

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from midicoder.storage.sqlite import ArtifactsManager, ProvenanceManager, get_connection
from midicoder.pipeline.config import get_config, load_user_config
from midicoder.pipeline.plan import ImplementationPlan, ModuleSpec, FileSpec
from midicoder.pipeline.file_contributions_loader import (
    FileContributionsLoader,
    BACKEND_STACKS,
    FRONTEND_STACKS,
    INFRA_STACK,
    CP_ID_TO_INTERNAL,
)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class CodePlan:
    """
    Implementation Plan - Kế hoạch code generation.
    
    Attributes:
        meta: Meta thông tin (version, created_at, target)
        backend_files: Danh sách backend files cần generate
        frontend_files: Danh sách frontend files cần generate
        infra_files: Danh sách infrastructure files cần generate
    """
    meta: dict
    backend_files: List[dict]
    frontend_files: List[dict]
    infra_files: List[dict]


@dataclass
class GeneratedFile:
    """
    Generated File - File đã generate.
    
    Attributes:
        path: Đường dẫn file
        content: Nội dung file
        type: Loại file (model, schema, route, etc.)
        template: Template đã dùng
    """
    path: str
    content: str
    type: str
    template: str


# ============================================================================
# Activity Logging Helper
# ============================================================================

def _log_activity(action: str, resource_type: str = "code", resource_id: str = "", details: dict = None, status: str = "success") -> None:
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


# ============================================================================
# Implementation Functions
# ============================================================================

def _execute_plan(
    target: str = "all",
    verbose: bool = False,
    status_filter: str | None = None,
) -> None:
    """
    Thực thi code plan command.

    Process:
    1. Load MIR từ SQLite artifacts table
    2. Phân tích MIR để tạo plan
    3. Lưu plan vào SQLite artifacts table
    4. Hiển thị summary

    Args:
        target: Target để generate (backend|frontend|all)
        verbose: Hiển thị chi tiết plan
        status_filter: Nếu set, chỉ include packs có status tương ứng
    """
    if status_filter:
        _log_activity("code.plan.started", details={"status_filter": status_filter})
    else:
        _log_activity("code.plan.started")

    # Bước 1: Load MIR từ SQLite
    mir_data = _load_mir_from_artifacts()
    if mir_data is None:
        _log_activity("code.plan.failed", status="error", details={"reason": "MIR không tồn tại trong artifacts"})
        raise SystemExit(1)

    _log_activity("code.plan.mir_loaded", details={"operations_count": len(mir_data.get("operations", []))})

    # Bước 2: Lấy active_version
    config = get_config()
    active_version = config.get("active_version", "v1.0.0")

    # EU-0.2: Load user config từ project root
    user_config = load_user_config(Path("."))

    # Bước 3: Tạo plan
    plan = _create_implementation_plan(mir_data, target, status_filter=status_filter, user_config=user_config)
    
    # Bước 4: Lưu plan vào artifacts
    artifacts_manager = ArtifactsManager()
    artifacts_manager.init()
    
    # Serialize plan to JSON using typed methods
    plan_json = plan.to_json()
    file_counts = plan.count_files()
    
    artifacts_manager.create(
        artifact_id=f"plan-{active_version}",
        artifact_type="plan",
        name="Implementation Plan",
        version=active_version,
        content=plan_json,
        metadata={
            "target": target,
            "backend_files_count": file_counts.get("backend", 0),
            "frontend_files_count": file_counts.get("frontend", 0),
            "infra_files_count": file_counts.get("infra", 0),
            "plan_hash": plan.compute_hash(),
        },
    )
    _log_activity("code.plan.saved", details={"artifact_id": f"plan-{active_version}"})

    # Bước 5: Record provenance
    try:
        provenance_manager = ProvenanceManager()
        provenance_manager.init()
        provenance_manager.record_lineage(
            entity_id=f"plan-{active_version}",
            entity_type="artifact",
            source_id=f"mir-{active_version}",
            source_type="artifact",
            relationship="generated_from",
            metadata={"target": target},
        )
        _log_activity("code.plan.provenance_recorded")
    except Exception as e:
        _log_activity("code.plan.provenance_warning", status="warning", details={"error": str(e)})

    # Bước 6: Log summary
    _log_activity("code.plan.summary", details={
        "target": target,
        "backend_modules": len(plan.get_modules_by_type("backend")),
        "frontend_modules": len(plan.get_modules_by_type("frontend")),
        "infra_modules": len(plan.get_modules_by_type("infra")),
        "plan_hash": plan.compute_hash()[:16],
    })

    if verbose:
        module_details = []
        for module in plan.modules:
            module_details.append({
                "name": module.name,
                "type": module.module_type,
                "file_count": len(module.files),
                "files": [{"path": f.path, "type": f.file_type} for f in module.files],
            })
        _log_activity("code.plan.verbose_modules", details={"modules": module_details})

    _log_activity("code.plan.completed")


def _load_mir_from_artifacts() -> Optional[dict]:
    """
    Load MIR từ SQLite artifacts table.
    
    Returns:
        MIR dictionary hoặc None nếu không tìm thấy
    """
    artifacts_manager = ArtifactsManager()
    artifacts_manager.init()
    
    # Tìm artifact có type="mir"
    artifacts = artifacts_manager.list(artifact_type="mir")
    if not artifacts:
        return None
    
    # Lấy artifact mới nhất
    mir_artifact = artifacts[-1]
    content = mir_artifact.get("content", "{}")
    
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        _log_activity("code.load.mir_json_error", status="warning", details={"reason": "MIR content không phải JSON hợp lệ"})
        return None


def _create_implementation_plan(
    mir: dict,
    target: str,
    status_filter: str | None = None,
    user_config: dict | None = None,  # EU-0.2
) -> ImplementationPlan:
    """
    Tạo implementation plan từ MIR.

    Args:
        mir: MIR dictionary
        target: Target để generate
        user_config: Optional user config từ midicoder.config.yml

    Returns:
        ImplementationPlan typed instance
    """
    plan = ImplementationPlan(
        meta={
            "version": "1.0.0",
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "target": target,
        }
    )

    # Tạo backend modules
    if target in ["backend", "all"]:
        backend_files = _plan_backend_files(mir, status_filter=status_filter, user_config=user_config)

        # BUG FIX: read entities from MIR.metadata (same fix as in _plan_backend_files)
        metadata_dict = mir.get("metadata", {})
        entities = metadata_dict.get("entities", [])

        # Nhóm files theo module
        core_files = [f for f in backend_files if f["type"] in ["main", "config", "database"]]

        # Core module
        if core_files:
            core_specs = [FileSpec(
                path=f["path"],
                file_type=f["type"],
                template=f["template"],
                context=f.get("context", {}),
                dependencies=[],
                metadata=f.get("metadata", {})
            ) for f in core_files]
            plan.add_module(ModuleSpec(
                name="core",
                module_type="backend",
                files=core_specs,
                dependencies=[]
            ))

        # Entity modules (models, schemas, routes per entity)
        # Collect paths already assigned to core or entity modules
        _assigned_paths: set[str] = {f["path"] for f in core_files}

        for entity in entities:
            entity_name = entity.get("id", "").lower()
            entity_files = [
                f for f in backend_files
                if entity_name in f["path"] or f["type"] in ["model", "schema", "route", "repository"]
            ]

            if entity_files:
                entity_specs = [FileSpec(
                    path=f["path"],
                    file_type=f["type"],
                    template=f["template"],
                    context=f.get("context", {}),
                    dependencies=[],
                    metadata=f.get("metadata", {})
                ) for f in entity_files]
                plan.add_module(ModuleSpec(
                    name=entity_name,
                    module_type="backend",
                    files=entity_specs,
                    dependencies=["core"]
                ))
                for ef in entity_files:
                    _assigned_paths.add(ef["path"])

        # Pack infrastructure modules — files not assigned to core or any entity
        # These are pack-declared infrastructure files (workflow, cache, search, notification, ...)
        remaining_files = [f for f in backend_files if f["path"] not in _assigned_paths]
        if remaining_files:
            # Group remaining files by top-level directory (e.g., "workflow", "multitenant", "cache")
            from collections import defaultdict
            group_by_prefix: dict[str, list[dict]] = defaultdict(list)
            for f in remaining_files:
                # Extract module prefix from path (e.g., "app/workflow/x.py" → "workflow")
                parts = f["path"].split(os.sep)
                if len(parts) >= 3 and parts[0] == "app":
                    group_key = parts[1]  # e.g., "workflow", "cache"
                else:
                    group_key = "shared"
                group_by_prefix[group_key].append(f)

            for group_name in sorted(group_by_prefix.keys()):
                group_files = group_by_prefix[group_name]
                group_specs = [FileSpec(
                    path=f["path"],
                    file_type=f["type"],
                    template=f["template"],
                    context=f.get("context", {}),
                    dependencies=[],
                    metadata=f.get("metadata", {})
                ) for f in group_files]
                plan.add_module(ModuleSpec(
                    name=group_name,
                    module_type="backend",
                    files=group_specs,
                    dependencies=["core"]
                ))

    # Tạo frontend modules
    if target in ["frontend", "all"]:
        frontend_files = _plan_frontend_files(mir, status_filter=status_filter, user_config=user_config)

        frontend_specs = [FileSpec(
            path=f["path"],
            file_type=f["type"],
            template=f["template"],
            context=f.get("context", {}),
            dependencies=[],
            metadata=f.get("metadata", {})
        ) for f in frontend_files]

        plan.add_module(ModuleSpec(
            name="frontend",
            module_type="frontend",
            files=frontend_specs,
            dependencies=[]
        ))

    # Infrastructure module
    infra_files = _plan_infra_files(status_filter=status_filter, user_config=user_config)
    infra_specs = [FileSpec(
        path=f["path"],
        file_type=f["type"],
        template=f["template"],
        context=f.get("context", {}),
        dependencies=[],
        metadata={}
    ) for f in infra_files]

    plan.add_module(ModuleSpec(
        name="infra",
        module_type="infra",
        files=infra_specs,
        dependencies=[]
    ))

    return plan


def _plan_backend_files(mir: dict, status_filter: str | None = None, user_config: dict | None = None) -> List[dict]:
    """
    Plan backend files from MIR.

    Stack-aware: resolves file contributions from ALL packs for the
    configured backend stack (default: ``fastapi``).  Entity model/schema
    FileSpecs carry ``metadata.pack_emitter`` so that ``_generate_file()``
    can dispatch to the structured CP01 emitter instead of raw Jinja2.

    Args:
        mir: MIR dictionary (as produced by MIR.to_dict())
        status_filter: If set, only include packs with matching status.
        user_config: Optional user config from midicoder.config.yml (EU-0.2).

    Returns:
        Danh sách backend file plans
    """
    metadata = mir.get("metadata", {})
    entities = metadata.get("entities", [])
    commands = metadata.get("commands", [])
    queries = metadata.get("queries", [])

    backend_stack = _get_backend_stack()
    loader = FileContributionsLoader()

    files = []

    # --- Core files (always include, no pack owns these) ---
    files.extend([
        {
            "path": "app/main.py",
            "type": "main",
            "template": "main.py.jinja2",
            "context": {},
        },
        {
            "path": "app/config.py",
            "type": "config",
            "template": "config.py.jinja2",
            "context": {},
        },
    ])

    # --- Pack-declared infrastructure files for this backend stack ---
    infra_files = loader.resolve_all_infrastructure(
        backend_stack, metadata, status_filter=status_filter, user_config=user_config
    )
    _merge_files(files, infra_files)

    # --- Pack-declared per-entity files for this backend stack ---
    per_entity_files = loader.resolve_all_per_entity(
        backend_stack, entities, status_filter=status_filter, user_config=user_config
    )
    _merge_files(files, per_entity_files)

    # --- Pack-declared per-command files for this backend stack ---
    per_command_files = loader.resolve_all_per_command(
        backend_stack, commands, status_filter=status_filter, user_config=user_config
    )
    _merge_files(files, per_command_files)

    # --- Pack-declared per-query files for this backend stack ---
    per_query_files = loader.resolve_all_per_query(
        backend_stack, queries, status_filter=status_filter, user_config=user_config
    )
    _merge_files(files, per_query_files)

    return files


def _get_backend_stack() -> str:
    """Get the configured backend stack from config."""
    config = get_config()
    stack = config.get("backend_stack", config.get("stack", "fastapi"))
    return stack if stack in BACKEND_STACKS else "fastapi"


def _merge_files(target: List[dict], source: List[dict]) -> None:
    """Merge *source* into *target*, deduplicating by ``path``."""
    seen = {f["path"] for f in target}
    for f in source:
        if f["path"] not in seen:
            seen.add(f["path"])
            target.append(f)


def _plan_frontend_files(mir: dict, status_filter: str | None = None, user_config: dict | None = None) -> List[dict]:
    """
    Plan frontend files from MIR.

    Stack-aware: resolves file contributions from ALL packs for the
    configured frontend stack (default: ``angular``).

    Args:
        mir: MIR dictionary
        status_filter: If set, only include packs with matching status.
        user_config: Optional user config from midicoder.config.yml (EU-0.2).

    Returns:
        Danh sách frontend file plans
    """
    metadata = mir.get("metadata", {})
    entities = metadata.get("entities", [])

    frontend_stack = _get_frontend_stack()
    ui_framework = _get_ui_framework(frontend_stack)  # EU-0.3: resolve early
    loader = FileContributionsLoader()

    files = []

    # --- Pack-declared infrastructure files for this frontend stack ---
    infra_files = loader.resolve_all_infrastructure(
        frontend_stack, metadata, status_filter=status_filter, user_config=user_config
    )
    for f in infra_files:
        f.setdefault("metadata", {})["stack"] = frontend_stack
    _merge_files(files, infra_files)

    # --- Pack-declared per-entity files for this frontend stack ---
    # EU-0.3: pass ui_framework for StyleResolver
    per_entity_files = loader.resolve_all_per_entity(
        frontend_stack, entities, status_filter=status_filter,
        user_config=user_config, ui_framework=ui_framework,
    )
    for f in per_entity_files:
        f.setdefault("metadata", {})["stack"] = frontend_stack
    _merge_files(files, per_entity_files)

    # --- Pack-declared per-ui-component files (entities × component_types) ---
    # EU-0.3: pass ui_framework for StyleResolver
    per_ui_component_files = loader.resolve_all_per_ui_component(
        frontend_stack, entities, status_filter=status_filter,
        user_config=user_config, ui_framework=ui_framework,
    )
    for f in per_ui_component_files:
        f.setdefault("metadata", {})["stack"] = frontend_stack
    _merge_files(files, per_ui_component_files)

    # --- Pack-declared per-widget files (CP22 realtime widgets) ---
    per_widget_files = loader.resolve_all_per_widget(
        frontend_stack, None, status_filter=status_filter, user_config=user_config
    )
    for f in per_widget_files:
        f.setdefault("metadata", {})["stack"] = frontend_stack
    _merge_files(files, per_widget_files)

    # --- Inject ui_framework into all frontend file contexts ---
    for f in files:
        f.setdefault("context", {})["ui_framework"] = ui_framework
        f.setdefault("metadata", {})["ui_framework"] = ui_framework

    return files


def _get_frontend_stack() -> str:
    """Get the configured frontend stack from config."""
    config = get_config()
    stack = config.get("frontend_stack", "angular")
    return stack if stack in FRONTEND_STACKS else "angular"


def _get_ui_framework(frontend_stack: str) -> str:
    """
    Get the configured UI framework from config.

    Defaults:
    - Angular → "material"
    - React → "antd"

    Args:
        frontend_stack: Frontend stack name

    Returns:
        UI framework name
    """
    config = get_config()
    ui_framework = config.get("ui_framework")
    if ui_framework:
        return ui_framework
    # Default per stack
    return "material" if frontend_stack == "angular" else "antd"


def _plan_infra_files(status_filter: str | None = None, user_config: dict | None = None) -> List[dict]:
    """
    Plan infrastructure files.

    Stack-aware: resolves file contributions from ALL packs for the
    ``infrastructure`` stack role (CP07 IaC).  Falls back to a minimal
    set of well-known infra files when the loader returns nothing.

    Args:
        status_filter: If set, only include packs with matching status.
        user_config: Optional user config from midicoder.config.yml (EU-0.2).

    Returns:
        Danh sách infra file plans
    """
    loader = FileContributionsLoader()

    # CP07 (IaC) contributes docker-compose, Dockerfile for fastapi/nestjs
    # Since infra is stack-agnostic, try "fastapi" first (where CP07 lives)
    infra_files = loader.resolve_all_infrastructure(
        "fastapi", status_filter=status_filter, user_config=user_config
    )

    # Filter to only infrastructure-type files
    infra_paths = {"docker-compose.yml", "Dockerfile", "Dockerfile.api", ".env.example"}
    infra_only = [f for f in infra_files if f["path"] in infra_paths]

    if infra_only:
        return infra_only

    # Fallback: minimal infra files if loader returns nothing
    # EU-0.2: inject infrastructure render overrides từ user config
    infra_rc = {}
    if user_config:
        infra_rc = user_config.get("render", {}).get("infrastructure", {})
    return [
        {
            "path": "docker-compose.yml",
            "type": "docker_compose",
            "template": "cp_infra_iac/docker-compose.yml.jinja2",
            "context": {"render_context": infra_rc},
            "metadata": {},
        },
        {
            "path": "Dockerfile",
            "type": "dockerfile",
            "template": "cp_infra_iac/Dockerfile.api.jinja2",
            "context": {"render_context": infra_rc},
            "metadata": {},
        },
    ]


def _execute_gen(target: str = "all", dry_run: bool = False, status_filter: str | None = None, verify: bool = False) -> None:
    """
    Thực thi code gen command.

    Process:
    1. Load plan từ SQLite artifacts table
    2. Generate code cho mỗi file trong plan
    3. Generate Docker Compose từ MIR
    4. Lưu vào .midicoder/versions/{active_version}/src/
    5. (Optional) Kiểm tra compile/syntax cho file đã generate
    6. Hiển thị summary + verification report

    Args:
        target: Target để generate (backend|frontend|all)
        dry_run: Generate nhưng không lưu files
        status_filter: Nếu set, chỉ include packs có status tương ứng
                       (Lưu ý: gen đọc từ plan đã build sẵn, filter thực sự
                        xảy ra ở `code plan`.)
        verify: Nếu True, chạy CodeVerifier cho từng file sau khi generate
    """
    if status_filter:
        _log_activity("code.gen.started", details={"status_filter": status_filter})
    else:
        _log_activity("code.gen.started")

    # Bước 1: Load plan từ SQLite
    config = get_config()
    active_version = config.get("active_version", "v1.0.0")

    plan_data = _load_plan_from_artifacts(active_version)
    if plan_data is None:
        _log_activity("code.gen.failed", status="error", details={"reason": "Plan không tồn tại trong artifacts"})
        raise SystemExit(1)

    _log_activity("code.gen.plan_loaded", details={"version": active_version})

    # Bước 2: Xác định output directory
    output_dir = Path(f".midicoder/versions/{active_version}/src")
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        # Dry run: dùng thư mục tạm
        output_dir = Path("generated-dry-run")
        output_dir.mkdir(parents=True, exist_ok=True)

    # Bước 3: Load MIR từ SQLite để generate Docker Compose
    mir_data = _load_mir_from_artifacts()
    if mir_data is None:
        _log_activity("code.gen.mir_missing", status="warning", details={"reason": "MIR không tồn tại - Docker Compose generation bị skip"})
        mir = None
    else:
        try:
            # Late import để tránh circular import
            from midicoder.pipeline.mir import MIR as MIRClass
            mir = MIRClass.from_dict(mir_data)
            _log_activity("code.gen.mir_loaded", details={"operations_count": len(mir.operations)})
        except Exception as e:
            _log_activity("code.gen.mir_parse_error", status="warning", details={"error": str(e)})
            mir = None

    # Bước 4: Generate files từ plan.modules (typed roundtrip)
    from midicoder.pipeline.plan import ImplementationPlan
    plan = ImplementationPlan.from_dict(plan_data)

    files_generated = []
    modules = plan.get_modules_by_type("backend") if target == "backend" else \
              plan.get_modules_by_type("frontend") if target == "frontend" else \
              plan.modules

    for module in modules:
        for file_spec in module.files:
            generated = _generate_file(file_spec.to_dict(), output_dir, dry_run, mir_data)
            if generated:
                files_generated.append(generated)

    _log_activity("code.gen.files_generated", details={
        "files_count": len(files_generated),
        "file_paths": [f.path for f in files_generated],
    })

    if dry_run:
        _log_activity("code.gen.dry_run", details={"output_dir": str(output_dir)})
    else:
        _log_activity("code.gen.saved", details={"output_dir": str(output_dir)})

    # Bước 5: Verify compile/syntax (nếu --verify được bật)
    verification_report = None
    if verify and files_generated:
        _log_activity("code.verify.started")
        from midicoder.pipeline.code_verifier import CodeVerifier

        verifier = CodeVerifier()
        file_paths = [output_dir / f.path for f in files_generated]
        verification_report = verifier.verify_batch(file_paths, check_imports=True)

        _log_activity("code.verify.completed", details={
            "passed": verification_report.passed,
            "failed": verification_report.failed,
        })

        if verification_report.failed > 0:
            failed_details = []
            for r in verification_report.results:
                if not r.success:
                    failed_details.append({"file": str(r.file_path), "errors": [str(e) for e in r.errors]})
            _log_activity("code.verify.failed_files", status="error", details={"failed_files": failed_details})

    # Bước 6: Log vào artifacts (metadata)
    try:
        artifacts_manager = ArtifactsManager()
        artifacts_manager.init()
        artifacts_manager.create(
            artifact_id=f"generated-{active_version}",
            artifact_type="generated_code",
            name="Generated Code",
            version=active_version,
            content="",
            metadata={
                "target": target,
                "files_count": len(files_generated),
                "files": [f.path for f in files_generated],
                "dry_run": dry_run,
                "verified": verify,
                "verification_passed": verification_report.passed if verification_report else None,
                "verification_failed": verification_report.failed if verification_report else None,
            },
        )
        _log_activity("code.gen.artifacts_logged")
    except Exception as e:
        _log_activity("code.gen.artifacts_error", status="warning", details={"error": str(e)})

    if verify and verification_report and verification_report.failed > 0:
        _log_activity("code.gen.completed_with_errors", status="error", details={"failed_count": verification_report.failed})
        # Raise exit code để CI/CD detect failure
        raise SystemExit(1)

    _log_activity("code.gen.completed")


def _load_plan_from_artifacts(active_version: str) -> Optional[dict]:
    """
    Load plan từ SQLite artifacts table.
    
    Args:
        active_version: Active version
    
    Returns:
        Plan dictionary hoặc None nếu không tìm thấy
    """
    artifacts_manager = ArtifactsManager()
    artifacts_manager.init()
    
    # Tìm artifact có type="plan" và version=active_version
    artifacts = artifacts_manager.list(artifact_type="plan")
    for artifact in artifacts:
        if artifact.get("version") == active_version:
            content = artifact.get("content", "{}")
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                _log_activity("code.load.plan_json_error", status="warning", details={"reason": "Plan content không phải JSON hợp lệ"})
                return None

    return None


def _generate_file(file_plan: dict, output_dir: Path, dry_run: bool, mir_data: dict | None = None) -> Optional[GeneratedFile]:
    """
    Generate một file từ plan.

    Supports three rendering paths:
    1. **Pack emitter dispatch** — if ``file_plan["metadata"]["pack_emitter"]``
       is set, delegates to the structured pack emitter (e.g. CP01 EntityEmitter).
    2. **IAC dispatch** — if ``pack_emitter`` starts with ``cp07.``, passes
       the typed MIR object to the generator (Docker Compose, Terraform).
    3. **Raw Jinja2** — falls back to ``Emitter.render()`` with the stack
       determined by ``file_plan["metadata"]["stack"]`` (or config default).

    Args:
        file_plan: File plan dictionary (from ImplementationPlan JSON)
        output_dir: Output directory
        dry_run: Dry run mode
        mir_data: Optional MIR dictionary for IAC generators

    Returns:
        GeneratedFile hoặc None nếu lỗi
    """
    file_path = Path(file_plan.get("path", ""))
    template = file_plan.get("template", "")
    file_type = file_plan.get("type", "unknown")
    metadata = file_plan.get("metadata", {})

    try:
        # Tạo parent directories
        full_path = output_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # --- Pack emitter dispatch ---
        pack_emitter = metadata.get("pack_emitter")
        if pack_emitter:
            # --- IAC dispatch (Docker Compose / Terraform) ---
            if pack_emitter.startswith("cp07."):
                from midicoder.pipeline.mir import MIR as MIRClass
                mir = MIRClass.from_dict(mir_data) if mir_data else None
                if mir is None:
                    _log_activity("code.gen.file.skipped", status="warning", details={"file": str(file_path), "reason": "MIR không tồn tại"})
                    return None
                return _generate_iac_file(pack_emitter, mir, output_dir, file_path)

            # --- Structured pack emitter dispatch ---
            from midicoder.pipeline.pack_emitter_router import PackEmitterRouter
            stack = metadata.get("stack", _get_stack_from_config())
            result_files = PackEmitterRouter.dispatch(
                pack_emitter, file_plan, stack
            )
            # The router may return multiple files; write each.
            generated = []
            for rf in result_files:
                out_path = output_dir / rf["path"]
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(rf["content"], encoding="utf-8")
                generated.append(GeneratedFile(
                    path=rf["path"],
                    content=rf["content"],
                    type=file_type,
                    template=f"pack_emitter:{pack_emitter}",
                ))
            # Return the first one (caller expects a single GeneratedFile)
            return generated[0] if generated else None

        # --- Raw Jinja2 fallback ---
        # BUG FIX: per-file stack override (for frontend templates)
        stack = metadata.get("stack", _get_stack_from_config())
        content = _render_template(template, file_plan.get("context", {}), stack=stack)

        if not dry_run:
            full_path.write_text(content, encoding="utf-8")
        else:
            # Dry run: vẫn lưu để review
            full_path.write_text(content, encoding="utf-8")

        return GeneratedFile(
            path=str(file_path),
            content=content,
            type=file_type,
            template=template,
        )
    except Exception as e:
        _log_activity("code.gen.file.error", status="error", details={"file": str(file_path), "error": str(e)})
        return None


def _generate_iac_file(
    pack_emitter: str,
    mir,
    output_dir: Path,
    file_path: Path,
) -> Optional[GeneratedFile]:
    """
    Generate IAC files (Docker Compose, Terraform) from typed MIR.

    Args:
        pack_emitter: Emitter key (e.g. "cp07.docker", "cp07.terraform")
        mir: Typed MIR object
        output_dir: Output directory
        file_path: Relative file path

    Returns:
        GeneratedFile or None
    """
    try:
        full_path = output_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        if pack_emitter == "cp07.docker":
            from midicoder.packs.cp_infra_iac.docker import DockerComposeGenerator as DCG
            generator = DCG()
            infra_config = generator.generate(mir, full_path)
            content = full_path.read_text(encoding="utf-8")
            _log_activity("code.gen.iac.docker", details={"file": str(file_path), "services": infra_config.services})
            return GeneratedFile(
                path=str(file_path),
                content=content,
                type="docker_compose",
                template="pack_emitter:cp07.docker",
            )

        elif pack_emitter == "cp07.terraform":
            from midicoder.packs.cp_infra_iac.terraform import TerraformGenerator
            generator = TerraformGenerator()
            generator.generate(mir, full_path.parent)
            # Terraform may generate multiple files; return the main one
            if full_path.exists():
                content = full_path.read_text(encoding="utf-8")
                return GeneratedFile(
                    path=str(file_path),
                    content=content,
                    type="terraform",
                    template="pack_emitter:cp07.terraform",
                )

        _log_activity("code.gen.iac.unknown_emitter", status="warning", details={"emitter": pack_emitter})
        return None

    except Exception as e:
        _log_activity("code.gen.iac.error", status="error", details={"file": str(file_path), "error": str(e)})
        return None


def _get_stack_from_config() -> str:
    """
    Lấy stack target từ config file.
    
    Returns:
        Stack name (mặc định: fastapi)
    """
    config = get_config()
    return config.get("stack", "fastapi")


def _render_template(template_name: str, context: dict, stack: str | None = None) -> str:
    """
    Render Jinja2 template với context bằng Emitter class.

    Sử dụng Emitter để load và render template từ stack directory.
    Stack target được đọc từ config file (mặc định: fastapi) hoặc từ
    tham số ``stack`` (per-file override cho frontend templates).

    Args:
        template_name: Tên template (ví dụ: main.py.jinja2)
        context: Template context (MIR metadata)
        stack: Stack override (ví dụ: "angular" cho frontend templates).
               Nếu None, đọc từ config.

    Returns:
        Rendered content string
    """
    if stack is None:
        stack = _get_stack_from_config()

    # Tạo Emitter và render template
    from midicoder.pipeline.emitter import Emitter
    emitter = Emitter(stack=stack)
    return emitter.render(template_name, context)


def _execute_apply(target_dir: str, dry_run: bool, backup: bool, force: bool) -> None:
    """
    Thực thi code apply command.
    
    Process:
    1. Load generated code từ .midicoder/versions/{version}/src/
    2. Copy/merge vào target directory
    3. Handle conflicts (prompt hoặc force)
    4. Log vào activity_log
    
    Args:
        target_dir: Target directory
        dry_run: Hiển thị sẽ apply những gì
        backup: Tạo backup trước khi overwrite
        force: Overwrite không hỏi confirmation
    """
    _log_activity("code.apply.started")

    # Bước 1: Lấy active_version và generated code path
    config = get_config()
    active_version = config.get("active_version", "v1.0.0")

    src_dir = Path(f".midicoder/versions/{active_version}/src")
    if not src_dir.exists():
        _log_activity("code.apply.failed", status="error", details={"reason": f"Generated code directory không tồn tại: {src_dir}"})
        raise SystemExit(1)

    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)

    _log_activity("code.apply.paths_resolved", details={"source": str(src_dir), "target": str(target_path.absolute())})

    # Bước 2: Tìm tất cả files trong src
    files_to_apply = []
    for file_path in src_dir.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(src_dir)
            files_to_apply.append((file_path, relative_path))

    if not files_to_apply:
        _log_activity("code.apply.failed", status="error", details={"reason": "Không có files nào để apply"})
        raise SystemExit(1)

    _log_activity("code.apply.files_discovered", details={"files_count": len(files_to_apply)})

    # Bước 3: Apply files
    applied_count = 0
    skipped_count = 0

    for src_file, relative_path in files_to_apply:
        dest_file = target_path / relative_path

        # Check conflicts
        if dest_file.exists():
            if dry_run:
                _log_activity("code.apply.file.would_overwrite", details={"file": str(relative_path)})
                applied_count += 1
                continue

            if backup:
                # Tạo backup
                backup_file = dest_file.with_suffix(dest_file.suffix + ".backup")
                shutil.copy2(src_file, backup_file)
                _log_activity("code.apply.file.backed_up", details={"file": str(relative_path), "backup": backup_file.name})

            if not force:
                _log_activity("code.apply.file.skipped", status="warning", details={"file": str(relative_path), "reason": "File đã tồn tại, dùng --force để ghi đè"})
                skipped_count += 1
                continue

            _log_activity("code.apply.file.overwritten", details={"file": str(relative_path)})

        # Copy file
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)
        _log_activity("code.apply.file.applied", details={"file": str(relative_path)})
        applied_count += 1

    _log_activity("code.apply.summary", details={
        "applied_count": applied_count,
        "skipped_count": skipped_count,
        "dry_run": dry_run,
    })

    # Bước 4: Log vào artifacts
    try:
        artifacts_manager = ArtifactsManager()
        artifacts_manager.init()
        artifacts_manager.create(
            artifact_id=f"applied-{active_version}",
            artifact_type="applied_code",
            name="Applied Code",
            version=active_version,
            content="",
            metadata={
                "target_dir": str(target_path.absolute()),
                "files_applied": applied_count,
                "files_skipped": skipped_count,
                "dry_run": dry_run,
            },
        )
        _log_activity("code.apply.artifacts_logged")
    except Exception as e:
        _log_activity("code.apply.artifacts_error", status="warning", details={"error": str(e)})

    _log_activity("code.apply.completed")


# ============================================================================
# Legacy Functions (deprecated, kept for backward compatibility)
# ============================================================================

def create_plan(target: str = "all", verbose: bool = False) -> None:
    """
    Legacy function - gọi _execute_plan.
    
    Deprecated: Dùng CLI command thay thế.
    """
    _execute_plan(target=target, verbose=verbose)


def generate_code(target: str = "all", dry_run: bool = False) -> None:
    """
    Legacy function - gọi _execute_gen.
    
    Deprecated: Dùng CLI command thay thế.
    """
    _execute_gen(target=target, dry_run=dry_run)


def apply_code(target_dir: str = ".", dry_run: bool = False, force: bool = False) -> None:
    """
    Legacy function - gọi _execute_apply.
    
    Deprecated: Dùng CLI command thay thế.
    """
    _execute_apply(target_dir=target_dir, dry_run=dry_run, backup=False, force=force)