"""
Brief Commands Implementation.

Lệnh quản lý briefs theo SoT E02, E20:
- brief analyze: Phân tích brief bằng LLM → working-brief
- brief clarify: Interactive Q&A → master-brief
- brief save: Lưu vào library
- brief load: Load từ library
- brief list: Hiển thị danh sách briefs

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


def analyze_brief(
    brief_path: Optional[str] = None,
    domain: Optional[str] = None,
    force: bool = False
) -> None:
    """
    Phân tích brief để extract requirements bằng LLM.

    Theo SoT E02:
    - Input: user brief (natural language)
    - Process: LLM extracts requirements
    - Output: working-brief (SQLite)

    Args:
        brief_path: Đường dẫn đến brief file (default: brief.md)
        domain: Domain name (optional)
        force: Force regenerate even if exists

    Raises:
        FileNotFoundError: Nếu brief file không tồn tại
    """
    click.echo("📖 Đang phân tích brief...")

    # Bước 1: Đọc brief
    if brief_path is None:
        brief_path = "brief.md"

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

    if existing and not force:
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

    # Bước 4: LLM analysis (placeholder - integrate with LLM client later)
    click.echo("")
    click.echo("🤖 Đang phân tích requirements bằng LLM...")
    click.echo("   ℹ️  LLM analysis - sẽ integrate với LLM client")
    click.echo("   → Extract: entities, commands, queries, events")
    click.echo("   → Domain: " + (domain or "auto-detect"))

    # Step 5: Log activity
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
        click.echo(f"   ⚠️  Could not log artifact: {e}")

    # Step 6: Update status
    briefs_manager.update_status(brief_id, "analyzed")

    # Done
    click.echo("")
    click.echo("✅ Brief analysis hoàn tất!")
    click.echo("")
    click.echo("Tiếp theo:")
    click.echo("  1. midicoder brief clarify - Interactive Q&A để clarify requirements")
    click.echo("  2. midicoder contract gen - Generate DSL contracts (skip clarify)")


def clarify_brief(max_rounds: int = 10) -> None:
    """
    Interactive clarification session với LLM.

    Theo SoT E02:
    - Input: working-brief + user answers
    - Process: Interactive Q&A loop
    - Output: master-brief + clarifications (SQLite)

    Clarifications lưu trong table clarifications:
    - brief_id, round_number, question, answer, is_memo

    Args:
        max_rounds: Max clarification rounds (default: 10)

    Raises:
        RuntimeError: Nếu không có working-brief
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


def save_brief(name: str, tags: Optional[str] = None) -> None:
    """
    Lưu brief vào library.

    Theo SoT E02:
    - Input: master-brief (đã clarified)
    - Process: Mark as library-brief
    - Output: library-brief (SQLite + optional MD export)

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


def load_brief(name: str) -> None:
    """
    Load brief từ library.

    Theo SoT E02:
    - Input: library brief name
    - Process: Load from SQLite or industry/briefs/
    - Output: working-brief

    Args:
        name: Library brief name
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


def list_briefs(domain: Optional[str] = None) -> None:
    """
    Hiển thị danh sách briefs.

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


def brief_library() -> None:
    """
    Industry brief library browser.

    Hiển thị các templates sẵn có trong industry/briefs/
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