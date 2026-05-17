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
import click
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from midicoder.storage.sqlite import ArtifactsManager, ProvenanceManager
from midicoder.pipeline.config import get_config
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
# CLI Commands
# ============================================================================

@click.group()
def code():
    """
    Code planning, generation, và application.
    
    Các lệnh con:
      plan   Tạo implementation plan từ MIR
      gen    Generate code từ plan + templates
      apply  Apply code vào target directory
    
    Ví dụ:
      midicoder code plan           # Tạo plan
      midicoder code gen --target all   # Generate code
      midicoder code apply          # Apply vào project
    """
    pass


@code.command()
@click.option(
    "--target", "-t",
    type=click.Choice(["backend", "frontend", "all"]),
    default="all",
    help="Target để generate (backend|frontend|all)"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Hiển thị chi tiết plan"
)
def plan(target: str, verbose: bool):
    """
    Tạo implementation plan từ MIR.
    
    Phân tích MIR và tạo kế hoạch files cần generate.
    Lưu plan vào SQLite artifacts table.
    
    OPTIONS:
      --target, -t    Target để generate (backend|frontend|all, mặc định: all)
      --verbose, -v   Hiển thị chi tiết plan
    
    EXAMPLES:
      midicoder code plan
      midicoder code plan --target backend
      midicoder code plan --verbose
    """
    _execute_plan(target=target, verbose=verbose)


@code.command()
@click.option(
    "--target", "-t",
    type=click.Choice(["backend", "frontend", "all"]),
    default="all",
    help="Target để generate (backend|frontend|all)"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Generate nhưng không lưu files"
)
def gen(target: str, dry_run: bool):
    """
    Generate code từ plan.
    
    Sử dụng Jinja2 templates để generate code từ plan.
    Lưu vào .midicoder/versions/{active_version}/src/
    
    OPTIONS:
      --target, -t    Target để generate (backend|frontend|all, mặc định: all)
      --dry-run       Generate nhưng không lưu files
    
    EXAMPLES:
      midicoder code gen
      midicoder code gen --target backend
      midicoder code gen --dry-run
    """
    _execute_gen(target=target, dry_run=dry_run)


@code.command()
@click.option(
    "--target-dir", "-d",
    type=click.Path(),
    default=".",
    help="Target directory để apply code"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Hiển thị sẽ apply những gì"
)
@click.option(
    "--backup",
    is_flag=True,
    help="Tạo backup trước khi overwrite"
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Overwrite không hỏi confirmation"
)
def apply(target_dir: str, dry_run: bool, backup: bool, force: bool):
    """
    Apply generated code vào target directory.
    
    Copy/merge generated files vào target directory.
    Handle conflicts với prompt hoặc force.
    
    OPTIONS:
      --target-dir, -d    Target directory (mặc định: current)
      --dry-run           Hiển thị sẽ apply những gì
      --backup            Tạo backup trước khi overwrite
      --force, -f         Overwrite không hỏi confirmation
    
    EXAMPLES:
      midicoder code apply
      midicoder code apply --target-dir ./src
      midicoder code apply --backup --force
    """
    _execute_apply(target_dir=target_dir, dry_run=dry_run, backup=backup, force=force)


# ============================================================================
# Implementation Functions
# ============================================================================

def _execute_plan(target: str = "all", verbose: bool = False) -> None:
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
    """
    click.echo("📋 Đang tạo implementation plan...")
    
    # Bước 1: Load MIR từ SQLite
    mir_data = _load_mir_from_artifacts()
    if mir_data is None:
        click.echo("❌ MIR không tồn tại trong artifacts")
        click.echo("💡 Chạy 'midicoder ir build' trước")
        raise SystemExit(1)
    
    click.echo(f"   ✓ Đã load MIR: {len(mir_data.get('operations', []))} operations")
    
    # Bước 2: Lấy active_version
    config = get_config()
    active_version = config.get("active_version", "v1.0.0")
    
    # Bước 3: Tạo plan
    plan = _create_implementation_plan(mir_data, target)
    
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
    click.echo(f"   ✓ Plan đã lưu vào artifacts: plan-{active_version}")
    
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
        click.echo(f"   ✓ Provenance lineage đã record")
    except Exception as e:
        click.echo(f"⚠️  Không thể record provenance: {e}")
    
    # Bước 6: Hiển thị summary
    click.echo("")
    click.echo("📊 Plan Summary:")
    click.echo("=" * 60)
    click.echo(f"   Target: {target}")
    click.echo(f"   Backend modules: {len(plan.get_modules_by_type('backend'))}")
    click.echo(f"   Frontend modules: {len(plan.get_modules_by_type('frontend'))}")
    click.echo(f"   Infra modules: {len(plan.get_modules_by_type('infra'))}")
    click.echo(f"   Plan hash: {plan.compute_hash()[:16]}...")
    click.echo("=" * 60)
    
    if verbose:
        click.echo("")
        click.echo("📄 Chi tiết modules:")
        click.echo("-" * 40)
        for module in plan.modules:
            click.echo(f"   • {module.name} ({module.module_type}): {len(module.files)} files")
            for file_spec in module.files:
                click.echo(f"     - {file_spec.path} ({file_spec.file_type})")
    
    click.echo("")
    click.echo("✅ Plan tạo thành công!")
    click.echo("")
    click.echo("Tiếp theo:")
    click.echo("  1. midicoder code gen --target backend  # Generate code")
    click.echo("  2. midicoder code apply                 # Apply code")


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
        click.echo("⚠️  MIR content không phải JSON hợp lệ")
        return None


def _create_implementation_plan(mir: dict, target: str) -> ImplementationPlan:
    """
    Tạo implementation plan từ MIR.
    
    Args:
        mir: MIR dictionary
        target: Target để generate
    
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
        backend_files = _plan_backend_files(mir)

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
        frontend_files = _plan_frontend_files(mir)

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
    infra_files = _plan_infra_files()
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

    # DP packs: Domain Packs (emit after CPs — can override/extend core)
    if target in ["backend", "all"]:
        dp_files = _load_domain_pack_files(target)
        if dp_files:
            dp_specs = [FileSpec(
                path=f["path"],
                file_type=f["type"],
                template=f["template"],
                context=f.get("context", {}),
                dependencies=["core"],
                metadata=f.get("metadata", {})
            ) for f in dp_files]
            plan.add_module(ModuleSpec(
                name="domain",
                module_type="backend",
                files=dp_specs,
                dependencies=["core"]
            ))

    # RX packs: Regulatory Overlays (emit last — inject compliance)
    if target in ["backend", "all"]:
        rx_files = _load_regulatory_pack_files(target)
        if rx_files:
            rx_specs = [FileSpec(
                path=f["path"],
                file_type=f["type"],
                template=f["template"],
                context=f.get("context", {}),
                dependencies=["core"],
                metadata=f.get("metadata", {})
            ) for f in rx_files]
            plan.add_module(ModuleSpec(
                name="regulatory",
                module_type="backend",
                files=rx_specs,
                dependencies=["core", "domain"]
            ))

    return plan


def _load_domain_pack_files(target: str) -> List[dict]:
    """Load infrastructure files from Domain Packs (DP).

    Args:
        target: Target to generate (backend|frontend|all)

    Returns:
        List of file plan dicts from domain packs.
    """
    if target not in ("backend", "all"):
        return []

    backend_stack = _get_backend_stack()
    loader = FileContributionsLoader()
    domain_contributions = loader.load_all_domain(stack=backend_stack)

    files: List[dict] = []
    seen: set[str] = set()
    for fc in domain_contributions:
        for f in loader.expand_infrastructure(fc):
            if f["path"] not in seen:
                seen.add(f["path"])
                files.append(f)
    return files


def _load_regulatory_pack_files(target: str) -> List[dict]:
    """Load infrastructure files from Regulatory Overlays (RX).

    Args:
        target: Target to generate (backend|frontend|all)

    Returns:
        List of file plan dicts from regulatory packs.
    """
    if target not in ("backend", "all"):
        return []

    backend_stack = _get_backend_stack()
    loader = FileContributionsLoader()
    regulatory_contributions = loader.load_all_regulatory(stack=backend_stack)

    files: List[dict] = []
    seen: set[str] = set()
    for fc in regulatory_contributions:
        for f in loader.expand_infrastructure(fc):
            if f["path"] not in seen:
                seen.add(f["path"])
                files.append(f)
    return files


def _plan_backend_files(mir: dict) -> List[dict]:
    """
    Plan backend files from MIR.

    Stack-aware: resolves file contributions from ALL packs for the
    configured backend stack (default: ``fastapi``).  Entity model/schema
    FileSpecs carry ``metadata.pack_emitter`` so that ``_generate_file()``
    can dispatch to the structured CP01 emitter instead of raw Jinja2.

    Args:
        mir: MIR dictionary (as produced by MIR.to_dict())

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
    infra_files = loader.resolve_all_infrastructure(backend_stack, metadata)
    _merge_files(files, infra_files)

    # --- Pack-declared per-entity files for this backend stack ---
    per_entity_files = loader.resolve_all_per_entity(backend_stack, entities)
    _merge_files(files, per_entity_files)

    # --- Pack-declared per-command files for this backend stack ---
    per_command_files = loader.resolve_all_per_command(backend_stack, commands)
    _merge_files(files, per_command_files)

    # --- Pack-declared per-query files for this backend stack ---
    per_query_files = loader.resolve_all_per_query(backend_stack, queries)
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


def _plan_frontend_files(mir: dict) -> List[dict]:
    """
    Plan frontend files from MIR.

    Stack-aware: resolves file contributions from ALL packs for the
    configured frontend stack (default: ``angular``).

    Args:
        mir: MIR dictionary

    Returns:
        Danh sách frontend file plans
    """
    metadata = mir.get("metadata", {})
    entities = metadata.get("entities", [])

    frontend_stack = _get_frontend_stack()
    loader = FileContributionsLoader()

    files = []

    # --- Pack-declared infrastructure files for this frontend stack ---
    infra_files = loader.resolve_all_infrastructure(frontend_stack, metadata)
    for f in infra_files:
        f.setdefault("metadata", {})["stack"] = frontend_stack
    _merge_files(files, infra_files)

    # --- Pack-declared per-entity files for this frontend stack ---
    per_entity_files = loader.resolve_all_per_entity(frontend_stack, entities)
    for f in per_entity_files:
        f.setdefault("metadata", {})["stack"] = frontend_stack
    _merge_files(files, per_entity_files)

    # --- Inject ui_framework into all frontend file contexts ---
    ui_framework = _get_ui_framework(frontend_stack)
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


def _plan_infra_files() -> List[dict]:
    """
    Plan infrastructure files.

    Stack-aware: resolves file contributions from ALL packs for the
    ``infrastructure`` stack role (CP07 IaC).  Falls back to a minimal
    set of well-known infra files when the loader returns nothing.

    Returns:
        Danh sách infra file plans
    """
    loader = FileContributionsLoader()

    # CP07 (IaC) contributes docker-compose, Dockerfile for fastapi/nestjs
    # Since infra is stack-agnostic, try "fastapi" first (where CP07 lives)
    infra_files = loader.resolve_all_infrastructure("fastapi")

    # Filter to only infrastructure-type files
    infra_paths = {"docker-compose.yml", "Dockerfile", "Dockerfile.api", ".env.example"}
    infra_only = [f for f in infra_files if f["path"] in infra_paths]

    if infra_only:
        return infra_only

    # Fallback: minimal infra files if loader returns nothing
    return [
        {
            "path": "docker-compose.yml",
            "type": "docker_compose",
            "template": "cp07_iac/docker-compose.yml.jinja2",
            "context": {},
            "metadata": {},
        },
        {
            "path": "Dockerfile",
            "type": "dockerfile",
            "template": "cp07_iac/Dockerfile.api.jinja2",
            "context": {},
            "metadata": {},
        },
    ]


def _execute_gen(target: str = "all", dry_run: bool = False) -> None:
    """
    Thực thi code gen command.
    
    Process:
    1. Load plan từ SQLite artifacts table
    2. Generate code cho mỗi file trong plan
    3. Generate Docker Compose từ MIR
    4. Lưu vào .midicoder/versions/{active_version}/src/
    5. Hiển thị summary
    
    Args:
        target: Target để generate (backend|frontend|all)
        dry_run: Generate nhưng không lưu files
    """
    click.echo("🔨 Đang generate code...")
    
    # Bước 1: Load plan từ SQLite
    config = get_config()
    active_version = config.get("active_version", "v1.0.0")
    
    plan_data = _load_plan_from_artifacts(active_version)
    if plan_data is None:
        click.echo("❌ Plan không tồn tại trong artifacts")
        click.echo("💡 Chạy 'midicoder code plan' trước")
        raise SystemExit(1)
    
    click.echo(f"   ✓ Đã load plan: {active_version}")
    
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
        click.echo("⚠️  MIR không tồn tại - Docker Compose generation bị skip")
        mir = None
    else:
        try:
            # Late import để tránh circular import
            from midicoder.pipeline.mir import MIR as MIRClass
            mir = MIRClass.from_dict(mir_data)
            click.echo(f"   ✓ Đã load MIR: {len(mir.operations)} operations")
        except Exception as e:
            click.echo(f"⚠️  Không thể parse MIR: {e}")
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
    
    click.echo(f"   ✓ Generated {len(files_generated)} files")
    
    if dry_run:
        click.echo(f"   ℹ️  Dry run - files trong: {output_dir}")
    else:
        click.echo(f"   ✓ Files đã lưu vào: {output_dir}")
    
    # Bước 4: Log vào artifacts (metadata)
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
            },
        )
        click.echo(f"   ✓ Generated code metadata đã lưu vào artifacts")
    except Exception as e:
        click.echo(f"⚠️  Không thể log vào artifacts: {e}")
    
    click.echo("")
    click.echo("✅ Code generation hoàn tất!")
    click.echo("")
    click.echo("Tiếp theo:")
    click.echo("  1. midicoder code apply  # Apply code vào project")


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
                click.echo("⚠️  Plan content không phải JSON hợp lệ")
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
                    click.echo(f"⚠️  MIR không tồn tại — skip {file_path}")
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
        click.echo(f"⚠️  Không thể generate {file_path}: {e}")
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
            from midicoder.emitters.core.cp07_iac.docker import DockerComposeGenerator as DCG
            generator = DCG()
            infra_config = generator.generate(mir, full_path)
            content = full_path.read_text(encoding="utf-8")
            click.echo(f"   ✓ Docker Compose generated với services: {', '.join(infra_config.services)}")
            return GeneratedFile(
                path=str(file_path),
                content=content,
                type="docker_compose",
                template="pack_emitter:cp07.docker",
            )

        elif pack_emitter == "cp07.terraform":
            from midicoder.emitters.core.cp07_iac.terraform import TerraformGenerator
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

        click.echo(f"⚠️  Unknown IAC emitter: {pack_emitter}")
        return None

    except Exception as e:
        click.echo(f"⚠️  IAC generation failed for {file_path}: {e}")
        import traceback
        click.echo(traceback.format_exc())
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
    click.echo("📦 Đang apply code vào target...")
    
    # Bước 1: Lấy active_version và generated code path
    config = get_config()
    active_version = config.get("active_version", "v1.0.0")
    
    src_dir = Path(f".midicoder/versions/{active_version}/src")
    if not src_dir.exists():
        click.echo(f"❌ Generated code directory không tồn tại: {src_dir}")
        click.echo("💡 Chạy 'midicoder code gen' trước")
        raise SystemExit(1)
    
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)
    
    click.echo(f"   ✓ Source: {src_dir}")
    click.echo(f"   ✓ Target: {target_path.absolute()}")
    
    # Bước 2: Tìm tất cả files trong src
    files_to_apply = []
    for file_path in src_dir.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(src_dir)
            files_to_apply.append((file_path, relative_path))
    
    if not files_to_apply:
        click.echo("⚠️  Không có files nào để apply")
        click.echo("💡 Chạy 'midicoder code gen' trước")
        raise SystemExit(1)
    
    click.echo(f"   ✓ Found {len(files_to_apply)} files to apply")
    
    # Bước 3: Apply files
    applied_count = 0
    skipped_count = 0
    
    for src_file, relative_path in files_to_apply:
        dest_file = target_path / relative_path
        
        # Check conflicts
        if dest_file.exists():
            if dry_run:
                click.echo(f"   ⚠️  Would overwrite: {relative_path}")
                applied_count += 1
                continue
            
            if backup:
                # Tạo backup
                backup_file = dest_file.with_suffix(dest_file.suffix + ".backup")
                shutil.copy2(src_file, backup_file)
                click.echo(f"   ↻ Backup: {relative_path} → {backup_file.name}")
            
            if not force:
                response = click.prompt(
                    f"File đã tồn tại: {relative_path}. Ghi đè?",
                    type=click.Choice(["y", "n", "a"]),
                    default="n",
                )
                if response == "n":
                    skipped_count += 1
                    continue
                elif response == "a":
                    force = True  # Apply all remaining
            
            click.echo(f"   ↻ Overwrite: {relative_path}")
        
        # Copy file
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)
        click.echo(f"   ✓ Applied: {relative_path}")
        applied_count += 1
    
    click.echo("")
    click.echo("📊 Apply Summary:")
    click.echo("=" * 60)
    click.echo(f"   Applied: {applied_count} files")
    click.echo(f"   Skipped: {skipped_count} files")
    click.echo(f"   Dry run: {dry_run}")
    click.echo("=" * 60)
    
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
        click.echo(f"   ✓ Apply metadata đã lưu vào artifacts")
    except Exception as e:
        click.echo(f"⚠️  Không thể log vào artifacts: {e}")
    
    click.echo("")
    click.echo("✅ Code apply hoàn tất!")
    click.echo("")
    click.echo("Tiếp theo:")
    click.echo("  1. Kiểm tra code đã apply")
    click.echo("  2. midicoder preview start  # Start local preview")


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