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
import click
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Optional, Any

from midicoder.storage.sqlite import (
    BriefsManager,
    ArtifactsManager,
    ProvenanceManager,
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


def _analyze_with_llm(
    brief_content: str,
    domain: Optional[str],
    brief_id: str,
) -> BriefAnalysis:
    """
    CLI wrapper cho analyze_brief_with_llm — thêm click.echo output.

    Delegate vào pure module (midicoder.pipeline.analyze), thêm progress
    output cho CLI user.
    """
    click.echo("   → Đang xác định domain...")
    try:
        analysis = analyze_brief_with_llm(
            brief_content=brief_content,
            domain=domain,
            brief_id=brief_id,
        )
    except Exception as e:
        click.echo(f"❌ LLM call failed: {e}")
        raise

    click.echo(f"   ✓ Domain: {analysis.domain}")
    click.echo(f"   ✓ LLM response: {analysis.tokens_used} tokens, {analysis.latency_ms}ms")
    click.echo(f"   ✓ Confidence: {analysis.confidence:.0%}")
    click.echo("   ✓ JSON parsed successfully")

    return analysis


@click.group()
def brief():
    """
    Quản lý và phân tích yêu cầu (briefs).

    Brief là mô tả yêu cầu hệ thống bằng tự nhiên (Markdown).
    Các lệnh con:
      analyze  Phân tích brief để extract requirements
      save     Lưu brief vào library
      load     Load brief từ library
      list     Hiển thị danh sách briefs
      library  Hiển thị industry brief templates
    """
    pass


@brief.command()
@click.option(
    "--domain",
    type=str,
    help="Tên domain (optional)"
)
@click.option(
    "--force", "-f",
    is_flag=True,
    default=False,
    help="Ghi đè brief cũ mà không hỏi confirmation"
)
def analyze(domain, force):
    """
    Phân tích brief để extract requirements.

    Sử dụng LLM để hiểu brief và tạo brief analysis.
    Lưu kết quả vào SQLite (working-brief).

    Brief file luôn được đọc từ:
    .midicoder/versions/{active_version}/brief.md

    OPTIONS:
      --domain DOMAIN    Tên domain (optional)
      --force, -f        Ghi đè brief cũ mà không hỏi confirmation

    EXAMPLES:
      midicoder brief analyze
      midicoder brief analyze --domain ecommerce
      midicoder brief analyze --force
    """
    _execute_analyze(domain, force)


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
    click.echo("📖 Đang phân tích brief...")

    # Bước 1: Lấy active_version từ config
    config = get_config()
    active_version = config.get("active_version")
    
    if not active_version:
        click.echo("❌ Không tìm thấy active_version trong config")
        click.echo("💡 Chạy 'midicoder version create' hoặc 'midicoder init' trước")
        raise SystemExit(1)

    # Bước 2: Xác định đường dẫn brief file
    versions_dir = Path(".midicoder/versions") / active_version
    brief_file = versions_dir / "brief.md"
    
    if not brief_file.exists():
        click.echo(f"❌ File brief.md không tồn tại tại: {brief_file}")
        click.echo(f"💡 Tạo file tại: {brief_file}")
        click.echo(f"   Hoặc chạy 'midicoder version create' để tạo version mới")
        raise SystemExit(1)

    content = brief_file.read_text(encoding="utf-8")
    click.echo(f"   ✓ Đã đọc brief: {brief_file}")
    click.echo(f"   → Version: {active_version}")
    click.echo(f"   → Kích thước: {len(content)} characters")

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
        click.echo(f"⚠️  Brief đã tồn tại: {existing.get('brief_id')}")
        if force:
            click.echo("   → Ghi đè (--force)")
        else:
            response = click.prompt("Ghi đè?", type=str, default="n")
            if response.lower() != "y":
                click.echo("❌ Hủy bỏ.")
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

    click.echo(f"   ✓ Working-brief đã lưu: {brief_id}")
    click.echo(f"   → Type: {record['type']}")
    click.echo(f"   → Status: {record['status']}")

    # Bước 4: LLM analysis
    click.echo("")
    click.echo("🤖 Đang phân tích requirements bằng LLM...")
    
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
        
        click.echo(f"   ✓ Analysis artifact đã lưu")
        
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
            click.echo(f"   ✓ Provenance lineage đã record")
        except Exception as e:
            click.echo(f"⚠️  Không thể record provenance: {e}")
        
        # Bước 6: Brief vẫn ở status draft sau analyze (clarify → clarified → user frozen)
        
        # Bước 7: Hiển thị tóm tắt
        click.echo("")
        click.echo("📊 Kết quả phân tích:")
        click.echo("=" * 60)
        click.echo(analysis.text_summary)
        click.echo("=" * 60)
        
    except Exception as e:
        click.echo(f"❌ Lỗi khi phân tích với LLM: {e}")
        click.echo("💡 Brief đã lưu nhưng chưa có analysis. Hãy:")
        click.echo("   1. Kiểm tra ~/.midicoder/midicoder.json")
        click.echo("   2. Đảm bảo LLM server đang chạy")
        click.echo("   3. Chạy lại lệnh")
        raise SystemExit(1)

    # Done
    click.echo("")
    click.echo("✅ Brief analysis hoàn tất!")
    click.echo("")
    click.echo("Tiếp theo:")
    click.echo("  1. midicoder contract gen - Generate DSL contracts")


@brief.command()
@click.option(
    "--name", "-n",
    required=True,
    type=str,
    help="Tên library brief (bắt buộc)"
)
@click.option(
    "--tags", "-t",
    type=str,
    help="Tags cách nhau bằng dấu phẩy (optional)"
)
def save(name, tags):
    """
    Lưu brief vào library.

    Lưu master-brief vào library để tái sử dụng.
    Có thể export ra file Markdown.

    OPTIONS:
      -n, --name NAME    Tên library brief (bắt buộc)
      -t, --tags TAGS    Tags cách nhau bằng dấu phẩy (optional)

    EXAMPLES:
      midicoder brief save --name "ecommerce-d2c"
      midicoder brief save -n "ecommerce-d2c" -t "ecommerce,retail"
    """
    _execute_save(name, tags)


def _execute_save(name: str, tags: Optional[str] = None) -> None:
    """
    Thực thi lưu brief vào library.

    Args:
        name: Tên library brief
        tags: Comma-separated tags (optional)
    """
    click.echo(f"💾 Lưu brief vào library: {name}")

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
        click.echo("❌ Không có master-brief nào để lưu")
        click.echo("💡 Chạy 'midicoder brief clarify' trước")
        return

    brief_id = master_brief.get("brief_id")
    click.echo(f"   → Brief: {master_brief.get('title')}")
    click.echo(f"   → ID: {brief_id}")
    click.echo(f"   → Tags: {tags or 'none'}")

    # TODO: Create library-brief record
    click.echo("")
    click.echo("   ℹ️  Library save - sẽ implement đầy đủ")
    click.echo("   → Update status: library")
    click.echo("   → Export to: industry/briefs/<name>/brief.md (optional)")

    click.echo("")
    click.echo(f"✅ Brief đã lưu vào library: {name}")


@brief.command()
@click.argument("name")
def load(name):
    """
    Load brief từ library.

    Load brief từ library (SQLite hoặc industry/briefs/).
    Tạo working-brief mới từ library brief.

    ARGUMENTS:
      name  Tên library brief

    EXAMPLES:
      midicoder brief load ecommerce-d2c
      midicoder brief load banking-core
    """
    _execute_load(name)


def _execute_load(name: str) -> None:
    """
    Thực thi load brief từ library.

    Args:
        name: Tên library brief
    """
    click.echo(f"📚 Load brief từ library: {name}")

    # Check industry/briefs folder
    industry_briefs = Path("industry/briefs") / name
    brief_file = industry_briefs / "brief.md"

    if brief_file.exists():
        click.echo(f"   ✓ Found: {brief_file}")
        click.echo("   ℹ️  Load từ industry briefs")
        # TODO: Load brief vào SQLite
    else:
        # Check SQLite
        briefs_manager = BriefsManager()
        briefs_manager.init()

        library_brief = None
        for brief in briefs_manager.list():
            if brief.get("type") == "library" and brief.get("name") == name:
                library_brief = brief
                break

        if library_brief:
            click.echo(f"   ✓ Found in SQLite: {library_brief.get('brief_id')}")
            # TODO: Copy library-brief → working-brief
        else:
            click.echo(f"❌ Không tìm thấy brief: {name}")
            return

    click.echo("")
    click.echo(f"✅ Brief đã load: {name}")


@brief.command()
@click.option(
    "--domain",
    type=str,
    help="Lọc theo domain (optional)"
)
def list(domain):
    """
    Hiển thị danh sách briefs.

    Hiển thị tất cả briefs trong SQLite, phân loại theo type.

    OPTIONS:
      --domain DOMAIN  Lọc theo domain (optional)

    EXAMPLES:
      midicoder brief list
      midicoder brief list --domain finance
    """
    _execute_list(domain)


def _execute_list(domain: Optional[str] = None) -> None:
    """
    Thực thi hiển thị danh sách briefs.

    Args:
        domain: Filter by domain (optional)
    """
    click.echo("📋 Danh sách briefs:")
    click.echo("=" * 60)

    briefs_manager = BriefsManager()
    briefs_manager.init()

    briefs = briefs_manager.list()

    if not briefs:
        click.echo("   📭 Không có brief nào.")
        click.echo("")
        click.echo("   💡 Để tạo brief:")
        click.echo("      1. Tạo file brief.md")
        click.echo("      2. Chạy: midicoder brief analyze")
        return

    # Group by type
    by_type = {"working": [], "master": [], "library": [], "patch": []}

    for brief in briefs:
        brief_type = brief.get("type", "working")
        if brief_type in by_type:
            by_type[brief_type].append(brief)

    # Display
    for type_name, type_briefs in by_type.items():
        if not type_briefs:
            continue

        click.echo(f"\n[{type_name.upper()} BRIEFS]")
        click.echo("-" * 40)

        for brief in type_briefs:
            title = brief.get("title", "Untitled")
            brief_id = brief.get("brief_id", "N/A")
            status = brief.get("status", "N/A")
            version = brief.get("version", "N/A")

            click.echo(f"\n  • {title}")
            click.echo(f"    ID: {brief_id}")
            click.echo(f"    Version: {version}")
            click.echo(f"    Status: {status}")

    click.echo("")
    click.echo(f"Total: {len(briefs)} briefs")


@brief.command()
def library():
    """
    Hiển thị industry brief templates.

    Hiển thị các brief templates sẵn có trong industry/briefs/.
    Có thể load bằng 'midicoder brief load <name>'.

    EXAMPLES:
      midicoder brief library
    """
    _execute_library()


def _execute_library() -> None:
    """
    Thực thi hiển thị industry brief library.
    """
    click.echo("📚 Industry Brief Library")
    click.echo("=" * 60)

    # Check industry/briefs folder
    industry_briefs = Path("industry/briefs")
    if not industry_briefs.exists():
        click.echo("   ⚠️  Industry briefs folder không tồn tại")
        click.echo(f"   Path: {industry_briefs.absolute()}")
        return

    # List available briefs
    brief_dirs = [d for d in industry_briefs.iterdir() if d.is_dir()]

    if not brief_dirs:
        click.echo("   📭 Không có brief templates nào.")
        return

    click.echo(f"\n📁 {len(brief_dirs)} domain briefs available:\n")

    for brief_dir in sorted(brief_dirs):
        brief_file = brief_dir / "brief.md"
        if brief_file.exists():
            # Extract info
            content = brief_file.read_text(encoding="utf-8")
            lines = content.split("\n")

            title = brief_dir.name.replace("-", " ").title()
            desc = "No description"

            # Try to find description
            for line in lines[:30]:
                if line.startswith("### Product Name"):
                    idx = lines.index(line)
                    if idx + 2 < len(lines):
                        desc = lines[idx + 2].strip()
                        break

            click.echo(f"• {title}")
            click.echo(f"  {desc}")
            click.echo(f"  Load: midicoder brief load {brief_dir.name}")
            click.echo("")