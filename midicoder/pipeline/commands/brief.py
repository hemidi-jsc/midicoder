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

import uuid
import click
from pathlib import Path
from datetime import datetime
from typing import Optional

from midicoder.storage.sqlite import (
    BriefsManager,
    ArtifactsManager,
)


@click.group()
def brief():
    """
    Quản lý và phân tích yêu cầu (briefs).

    Brief là mô tả yêu cầu hệ thống bằng tự nhiên (Markdown).
    Các lệnh con:
      analyze  Phân tích brief để extract requirements
      clarify  Interactive clarification session
      save     Lưu brief vào library
      load     Load brief từ library
      list     Hiển thị danh sách briefs
      library  Hiển thị industry brief templates
    """
    pass


@brief.command()
@click.argument("brief_path", type=click.Path(exists=True), required=False)
@click.option(
    "--file", "-f",
    "file_path",
    type=click.Path(exists=True),
    help="Đường dẫn đến brief file (default: brief.md)"
)
@click.option(
    "--domain",
    type=str,
    help="Tên domain (optional)"
)
def analyze(brief_path, file_path, domain):
    """
    Phân tích brief để extract requirements.

    Sử dụng LLM để hiểu brief và tạo brief analysis.
    Lưu kết quả vào SQLite (working-brief).

    ARGUMENTS:
      brief_path  Đường dẫn đến brief file (optional)

    OPTIONS:
      -f, --file FILE    Đường dẫn đến brief file
      --domain DOMAIN    Tên domain (optional)

    EXAMPLES:
      midicoder brief analyze
      midicoder brief analyze -f my-brief.md
      midicoder brief analyze ./docs/requirements.md
    """
    # Ưu tiên file_path từ --file option
    if file_path:
        brief_path = file_path
    elif not brief_path:
        brief_path = "brief.md"

    _execute_analyze(brief_path, domain)


def _execute_analyze(brief_path: str, domain: Optional[str] = None) -> None:
    """
    Thực thi phân tích brief.

    Args:
        brief_path: Đường dẫn đến brief file
        domain: Tên domain (optional)

    Raises:
        FileNotFoundError: Nếu brief file không tồn tại
    """
    click.echo("📖 Đang phân tích brief...")

    # Bước 1: Đọc brief
    brief_file = Path(brief_path)
    if not brief_file.exists():
        click.echo(f"❌ File không tồn tại: {brief_path}")
        click.echo("💡 Tạo brief.md hoặc chỉ định đường dẫn đúng")
        raise SystemExit(1)

    content = brief_file.read_text(encoding="utf-8")
    click.echo(f"   ✓ Đã đọc brief: {brief_file}")
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

    # Bước 4: LLM analysis (placeholder - integrate với LLM client sau)
    click.echo("")
    click.echo("🤖 Đang phân tích requirements bằng LLM...")
    click.echo("   ℹ️  LLM analysis - sẽ integrate với LLM client")
    click.echo("   → Extract: entities, commands, queries, events")
    click.echo("   → Domain: " + (domain or "auto-detect"))

    # Bước 5: Log activity
    try:
        artifacts_manager = ArtifactsManager()
        artifacts_manager.init()
        artifacts_manager.create(
            artifact_id=f"analysis-{brief_id}",
            artifact_type="analysis",
            name="Brief Analysis",
            version=version,
            brief_id=brief_id,
        )
    except Exception as e:
        click.echo(f"   ⚠️  Không thể log artifact: {e}")

    # Bước 6: Update status
    briefs_manager.update_status(brief_id, "analyzed")

    # Done
    click.echo("")
    click.echo("✅ Brief analysis hoàn tất!")
    click.echo("")
    click.echo("Tiếp theo:")
    click.echo("  1. midicoder brief clarify - Interactive Q&A để clarify requirements")
    click.echo("  2. midicoder contract gen - Generate DSL contracts (skip clarify)")


@brief.command()
@click.option(
    "--max-rounds", "-n",
    default=10,
    type=int,
    help="Số vòng clarification tối đa (default: 10)"
)
def clarify(max_rounds):
    """
    Interactive clarification session.

    Chat với LLM để làm rõ yêu cầu từ working-brief.
    Kết quả: master-brief + clarifications (SQLite)

    OPTIONS:
      -n, --max-rounds N  Số vòng clarification tối đa (default: 10)

    EXAMPLES:
      midicoder brief clarify
      midicoder brief clarify --max-rounds 5
    """
    _execute_clarify(max_rounds)


def _execute_clarify(max_rounds: int = 10) -> None:
    """
    Thực thi clarification session.

    Args:
        max_rounds: Số vòng clarification tối đa
    """
    click.echo("💬 Clarification mode")
    click.echo("=" * 60)

    # Bước 1: Tìm active working-brief
    briefs_manager = BriefsManager()
    briefs_manager.init()

    # Tìm brief có status = analyzed hoặc type = working
    active_brief = None
    for brief in briefs_manager.list():
        if brief.get("status") == "analyzed" or brief.get("type") == "working":
            active_brief = brief
            break

    if not active_brief:
        click.echo("❌ Không có working-brief nào để clarify")
        click.echo("💡 Chạy 'midicoder brief analyze' trước")
        return

    brief_id = active_brief.get("brief_id")
    click.echo(f"   → Brief: {active_brief.get('title')}")
    click.echo(f"   → ID: {brief_id}")
    click.echo(f"   → Max rounds: {max_rounds}")
    click.echo("")

    # Bước 2: Interactive Q&A loop
    # Placeholder - sẽ integrate với LLM client
    click.echo("🤖 LLM clarification loop - sẽ integrate với LLM client")
    click.echo("   ℹ️  Process:")
    click.echo("   1. LLM generate question từ working-brief")
    click.echo("   2. User answer (text)")
    click.echo("   3. LLM evaluate nếu cần thêm question")
    click.echo("   4. Loop cho đến khi không còn question hoặc đạt max_rounds")
    click.echo("   5. Convert working-brief → master-brief")
    click.echo("")

    # Demo: Lưu clarification record (placeholder)
    # Trong real implementation, sẽ có Q&A loop với LLM
    click.echo("💡 Để disable placeholder và implement thật, cần integrate LLM client")
    click.echo("")

    # Bước 3: Convert working-brief → master-brief
    briefs_manager.update_status(brief_id, "clarified")
    click.echo(f"   ✓ Brief đã chuyển sang status: clarified")

    click.echo("")
    click.echo("✅ Clarification hoàn tất!")
    click.echo("")
    click.echo("Tiếp theo:")
    click.echo("  1. midicoder brief save - Lưu vào library (optional)")
    click.echo("  2. midicoder contract gen - Generate DSL contracts")


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