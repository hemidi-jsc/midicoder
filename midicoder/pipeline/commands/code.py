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
import shutil
import click
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from midicoder.storage.sqlite import ArtifactsManager, ProvenanceManager
from midicoder.pipeline.config import get_config
from midicoder.pipeline.plan import ImplementationPlan, ModuleSpec, FileSpec


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
        
        # Nhóm files theo module
        core_files = [f for f in backend_files if f["type"] in ["main", "config", "database"]]
        model_files = [f for f in backend_files if f["type"] == "model"]
        schema_files = [f for f in backend_files if f["type"] == "schema"]
        route_files = [f for f in backend_files if f["type"] == "route"]
        
        # Core module
        if core_files:
            core_specs = [FileSpec(
                path=f["path"],
                file_type=f["type"],
                template=f["template"],
                context=f.get("context", {}),
                dependencies=[],
                metadata={}
            ) for f in core_files]
            plan.add_module(ModuleSpec(
                name="core",
                module_type="backend",
                files=core_specs,
                dependencies=[]
            ))
        
        # Entity modules (models, schemas, routes per entity)
        for entity in mir.get("entities", []):
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
                    metadata={}
                ) for f in entity_files]
                plan.add_module(ModuleSpec(
                    name=entity_name,
                    module_type="backend",
                    files=entity_specs,
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
            metadata={}
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
    
    return plan


def _plan_backend_files(mir: dict) -> List[dict]:
    """
    Plan backend files từ MIR.
    
    Args:
        mir: MIR dictionary
    
    Returns:
        Danh sách backend file plans
    """
    files = []
    
    # Core files (luôn include)
    # Template paths là relative so với stacks/{stack}/core/
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
        {
            "path": "app/database.py",
            "type": "database",
            "template": "db/database.py.jinja2",
            "context": {},
        },
    ])
    
    # Models và schemas cho mỗi entity
    for entity in mir.get("entities", []):
        entity_name = entity.get("id", "").lower()
        
        files.extend([
            {
                "path": f"app/models/{entity_name}.py",
                "type": "model",
                "template": "entities/entity.py.jinja2",
                "context": {"entity": entity},
            },
            {
                "path": f"app/schemas/{entity_name}.py",
                "type": "schema",
                "template": "entities/entity.py.jinja2",
                "context": {"entity": entity},
            },
            {
                "path": f"app/repositories/{entity_name}_repo.py",
                "type": "repository",
                "template": "db/repository.py.jinja2",
                "context": {"entity": entity},
            },
        ])
    
    # Routes cho mỗi entity (CRUD)
    for entity in mir.get("entities", []):
        entity_name = entity.get("id", "").lower()
        
        files.append({
            "path": f"app/routes/{entity_name}.py",
            "type": "route",
            "template": "routes/http_route.py.jinja2",
            "context": {"entity": entity, "operation": "crud"},
        })
    
    # Command handlers
    for command in mir.get("commands", []):
        command_name = command.get("id", "").lower()
        files.append({
            "path": f"app/commands/{command_name}_handler.py",
            "type": "command_handler",
            "template": "commands/command_handler.py.jinja2",
            "context": {"command": command},
        })
    
    # Query handlers
    for query in mir.get("queries", []):
        query_name = query.get("id", "").lower()
        files.append({
            "path": f"app/queries/{query_name}_handler.py",
            "type": "query_handler",
            "template": "queries/query_handler.py.jinja2",
            "context": {"query": query},
        })
    
    return files


def _plan_frontend_files(mir: dict) -> List[dict]:
    """
    Plan frontend files từ MIR.
    
    Args:
        mir: MIR dictionary
    
    Returns:
        Danh sách frontend file plans
    """
    files = []
    
    # Core files
    files.extend([
        {
            "path": "src/app/app.module.ts",
            "type": "module",
            "template": "angular/module.ts.jinja2",
            "context": {},
        },
        {
            "path": "src/app/app.component.ts",
            "type": "app_component",
            "template": "angular/app.component.ts.jinja2",
            "context": {},
        },
    ])
    
    # Components và services cho mỗi entity
    for entity in mir.get("entities", []):
        entity_name = entity.get("id", "").lower()
        
        files.extend([
            {
                "path": f"src/app/features/{entity_name}/components/{entity_name}.component.ts",
                "type": "component",
                "template": "angular/component.ts.jinja2",
                "context": {"entity": entity},
            },
            {
                "path": f"src/app/features/{entity_name}/components/{entity_name}.component.html",
                "type": "component_template",
                "template": "angular/component.html.jinja2",
                "context": {"entity": entity},
            },
            {
                "path": f"src/app/features/{entity_name}/services/{entity_name}.service.ts",
                "type": "service",
                "template": "angular/service.ts.jinja2",
                "context": {"entity": entity},
            },
        ])
    
    return files


def _plan_infra_files() -> List[dict]:
    """
    Plan infrastructure files.
    
    Returns:
        Danh sách infra file plans
    """
    return [
        {
            "path": "docker-compose.yml",
            "type": "docker_compose",
            "template": "infra/docker-compose.yml.jinja2",
            "context": {},
        },
        {
            "path": "Dockerfile",
            "type": "dockerfile",
            "template": "infra/Dockerfile.jinja2",
            "context": {},
        },
        {
            "path": ".env.example",
            "type": "env_example",
            "template": "infra/.env.example.jinja2",
            "context": {},
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
    
    # Bước 4: Generate Docker Compose từ MIR
    docker_compose_path = output_dir / "docker-compose.yml"
    if mir is not None:
        try:
            click.echo("   🐳 Đang generate Docker Compose từ MIR...")
            # Late import để tránh circular import
            from midicoder.emitters.core.iac.docker import DockerComposeGenerator as DCG
            docker_generator = DCG()
            infra_config = docker_generator.generate(mir, docker_compose_path)
            click.echo(f"   ✓ Docker Compose generated với services: {', '.join(infra_config.services)}")
        except Exception as e:
            click.echo(f"⚠️  Docker Compose generation failed: {e}")
            # Fallback: generate placeholder
            docker_generator = None
    else:
        docker_generator = None
    
    # Bước 5: Generate files
    files_generated = []
    
    for file_plan in plan_data.get("backend_files", []):
        if target in ["backend", "all"]:
            generated = _generate_file(file_plan, output_dir, dry_run)
            if generated:
                files_generated.append(generated)
    
    for file_plan in plan_data.get("frontend_files", []):
        if target in ["frontend", "all"]:
            generated = _generate_file(file_plan, output_dir, dry_run)
            if generated:
                files_generated.append(generated)
    
    # Skip docker-compose.yml trong infra_files vì đã generate từ MIR
    for file_plan in plan_data.get("infra_files", []):
        if file_plan.get("path") != "docker-compose.yml":
            generated = _generate_file(file_plan, output_dir, dry_run)
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


def _generate_file(file_plan: dict, output_dir: Path, dry_run: bool) -> Optional[GeneratedFile]:
    """
    Generate một file từ plan.
    
    Args:
        file_plan: File plan dictionary
        output_dir: Output directory
        dry_run: Dry run mode
    
    Returns:
        GeneratedFile hoặc None nếu lỗi
    """
    file_path = Path(file_plan.get("path", ""))
    template = file_plan.get("template", "")
    file_type = file_plan.get("type", "unknown")
    
    try:
        # Tạo parent directories
        full_path = output_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate content từ template
        # TODO: Integrate với Jinja2 template engine
        content = _render_template(template, file_plan.get("context", {}))
        
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


def _get_stack_from_config() -> str:
    """
    Lấy stack target từ config file.
    
    Returns:
        Stack name (mặc định: fastapi)
    """
    config = get_config()
    return config.get("stack", "fastapi")


def _render_template(template_name: str, context: dict) -> str:
    """
    Render Jinja2 template với context bằng Emitter class.
    
    Sử dụng Emitter để load và render template từ stack directory.
    Stack target được đọc từ config file (mặc định: fastapi).
    
    Args:
        template_name: Tên template (ví dụ: main.py.jinja2)
        context: Template context (MIR metadata)
    
    Returns:
        Rendered content string
    """
    # Lấy stack từ config
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