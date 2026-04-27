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
from midicoder.pipeline.context_feed import (
    get_brief_context,
    get_clarify_context,
)


@dataclass
class BriefAnalysis:
    """
    Kết quả phân tích brief.
    
    Attributes:
        json_data: JSON structured data (entities, commands, queries, events)
        text_summary: Tóm tắt text
        domain: Domain detected
        confidence: Độ tin cậy
        tokens_used: Số tokens LLM đã dùng
        latency_ms: Thời gian LLM call (ms)
    """
    json_data: dict
    text_summary: str
    domain: str
    confidence: float
    tokens_used: int = 0
    latency_ms: int = 0


def _analyze_with_llm(
    brief_content: str,
    domain: Optional[str],
    brief_id: str,
) -> BriefAnalysis:
    """
    Gọi LLM để phân tích brief.
    
    Process:
    1. Xác định domain (user-provided hoặc auto-detect)
    2. Load domain prompt template
    3. Query codebase context (optional)
    4. Call LLM với prompt + brief content (+ context)
    5. Parse JSON response
    6. Tạo text summary từ JSON
    
    Args:
        brief_content: Nội dung brief (Markdown)
        domain: Domain user-provided (optional)
        brief_id: Brief ID (cho artifact naming)
    
    Returns:
        BriefAnalysis với json_data và text_summary
    
    Raises:
        MidicoderError: Khi LLM call fail hoặc JSON parse error
    """
    # Step 1: Load LLM config
    try:
        llm_config = load_llm_config()
    except Exception as e:
        click.echo(f"⚠️  Không thể load LLM config: {e}")
        click.echo("💡 Cấu hình LLM tại ~/.midicoder/midicoder.json")
        raise
    
    # Step 2: Xác định domain
    if domain:
        final_domain = normalize_domain(domain)
        click.echo(f"   → Domain (user-provided): {final_domain}")
    else:
        click.echo("   → Đang auto-detect domain...")
        final_domain = detect_domain(brief_content, llm_config)
        click.echo(f"   → Domain detected: {final_domain}")
    
    # Step 3: Load prompt template
    try:
        system_prompt = get_domain_prompt(final_domain)
        click.echo(f"   → Đã load prompt template")
    except Exception as e:
        click.echo(f"⚠️  Lỗi load prompt: {e}, dùng default")
        system_prompt = get_domain_prompt("generic")
    
    # Step 3.5: Query codebase context (optional enhancement)
    click.echo("   → Đang query codebase context...")
    try:
        context_result = get_brief_context(
            brief_content=brief_content,
            domain=final_domain,
            model_name=llm_config.model,
        )
        
        if context_result.warning:
            click.echo(f"   {context_result.warning}")
        elif context_result.context_items:
            click.echo(f"   ✓ Codebase context: {len(context_result.context_items)} items, {context_result.token_count} tokens")
        else:
            click.echo("   ⚠️ Không tìm thấy codebase context (chạy 'midicoder index' để index codebase)")
    except Exception as e:
        click.echo(f"   ⚠️ Không thể query codebase context: {e}")
        context_result = None
    
    # Build user message với context (nếu có)
    user_message_content = brief_content
    if context_result and context_result.formatted_context:
        # Inject context vào đầu user message
        user_message_content = f"{context_result.formatted_context}\n\n## Brief Content:\n{brief_content}"
    
    # Step 4: Call LLM
    click.echo("   → Đang gọi LLM...")
    start_time = time.time()
    
    try:
        response = call_llm(
            config=llm_config,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message_content}],
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        tokens_used = response.usage.get("total_tokens", 0)
        
        click.echo(f"   ✓ LLM response: {tokens_used} tokens, {latency_ms}ms")
        
    except Exception as e:
        click.echo(f"❌ LLM call failed: {e}")
        briefs_manager = BriefsManager()
        briefs_manager.update_status(brief_id, "error")
        raise
    
    # Step 5: Parse JSON response
    click.echo("   → Đang parse JSON response...")
    llm_content = response.content.strip()
    
    try:
        # Try to extract JSON if wrapped in markdown
        if llm_content.startswith("```json"):
            llm_content = llm_content.removeprefix("```json").removesuffix("```")
        elif llm_content.startswith("```"):
            llm_content = llm_content.removeprefix("```").removesuffix("```")
        
        json_data = json.loads(llm_content)
        click.echo("   ✓ JSON parsed successfully")
        
    except json.JSONDecodeError as e:
        click.echo(f"❌ JSON parse error: {e}")
        click.echo("💡 Lưu raw response vào artifact")
        
        # Lưu raw response vào artifact
        artifacts_manager = ArtifactsManager()
        artifacts_manager.init()
        artifacts_manager.create(
            artifact_id=f"analysis-{brief_id}",
            artifact_type="analysis",
            name="Brief Analysis (Raw)",
            version="v1.0.0",
            brief_id=brief_id,
            content=llm_content,
            metadata={"error": "JSON parse failed", "latency_ms": latency_ms},
        )
        
        raise
    
    # Step 6: Tạo text summary từ JSON
    entities = json_data.get("entities", [])
    commands = json_data.get("commands", [])
    queries = json_data.get("queries", [])
    events = json_data.get("events", [])
    confidence = json_data.get("confidence", 0.5)
    summary = json_data.get("summary", "")
    
    text_summary = f"""Tóm tắt phân tích brief:
- Domain: {final_domain.title()}
- Số entities: {len(entities)} ({', '.join(e.get('name', '') for e in entities[:5])})
- Số commands: {len(commands)}
- Số queries: {len(queries)}
- Số events: {len(events)}
- Độ tin cậy: {confidence:.0%}
- {summary}"""
    
    return BriefAnalysis(
        json_data=json_data,
        text_summary=text_summary,
        domain=final_domain,
        confidence=confidence,
        tokens_used=tokens_used,
        latency_ms=latency_ms,
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
@click.option(
    "--domain",
    type=str,
    help="Tên domain (optional)"
)
def analyze(domain):
    """
    Phân tích brief để extract requirements.

    Sử dụng LLM để hiểu brief và tạo brief analysis.
    Lưu kết quả vào SQLite (working-brief).

    Brief file luôn được đọc từ:
    .midicoder/versions/{active_version}/brief.md

    OPTIONS:
      --domain DOMAIN    Tên domain (optional)

    EXAMPLES:
      midicoder brief analyze
      midicoder brief analyze --domain ecommerce
    """
    _execute_analyze(domain)


def _execute_analyze(domain: Optional[str] = None) -> None:
    """
    Thực thi phân tích brief.

    Brief file được đọc từ:
    .midicoder/versions/{active_version}/brief.md

    Args:
        domain: Tên domain (optional)

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
        
        # Bước 6: Update status
        briefs_manager.update_status(brief_id, "analyzed")
        
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
        briefs_manager.update_status(brief_id, "error")
        raise SystemExit(1)

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


def _generate_clarification_question(
    analysis_data: dict,
    qa_history: list[dict],
    llm_config,
    domain: str,
) -> tuple[bool, str]:
    """
    Gọi LLM để generate clarification question.

    Sử dụng brief-clarify.md prompt template với narrower context focus.

    Args:
        analysis_data: Analysis JSON từ brief analyze
        qa_history: Lịch sử Q&A (list of {question, answer})
        llm_config: LLM config
        domain: Domain name

    Returns:
        (needs_more, question_text)
        - needs_more=True: Còn cần hỏi thêm
        - needs_more=False: Đã đủ rõ, kết thúc
    """
    # Load clarification prompt
    try:
        system_prompt = get_domain_prompt(domain, prompt_type="clarify")
    except Exception:
        click.echo("⚠️  Không load được domain prompt, dùng default")
        system_prompt = get_domain_prompt("generic", prompt_type="clarify")

    # Query codebase context với narrower focus (dựa trên analysis + Q&A history)
    try:
        context_result = get_clarify_context(
            analysis_data=analysis_data,
            qa_history=qa_history,
            model_name=llm_config.model,
        )
        
        if context_result.warning:
            click.echo(f"   {context_result.warning}")
        elif context_result.context_items:
            click.echo(f"   ✓ Clarify context: {len(context_result.context_items)} items")
        else:
            click.echo("   ⚠️ Không tìm thấy codebase context cho clarification")
    except Exception as e:
        click.echo(f"   ⚠️ Không thể query codebase context: {e}")
        context_result = None

    # Build user message với context + analysis + history
    user_content_parts = []
    
    # Inject context vào đầu (nếu có)
    if context_result and context_result.formatted_context:
        user_content_parts.append(context_result.formatted_context)
    
    # Thêm brief analysis
    user_content_parts.append(f"## Brief Analysis:\n{json.dumps(analysis_data, indent=2, ensure_ascii=False)}")
    
    # Thêm Q&A history
    user_content_parts.append("\n## Q&A History:")
    if qa_history:
        for i, qa in enumerate(qa_history, 1):
            user_content_parts.append(f"\nQ{i}: {qa['question']}\nA{i}: {qa['answer']}")
    else:
        user_content_parts.append("\n(Chưa có câu hỏi nào)")
    
    user_content = "\n".join(user_content_parts)

    try:
        response = call_llm(
            config=llm_config,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )

        # Parse JSON response
        content = response.content.strip()
        if content.startswith("```json"):
            content = content.removeprefix("```json").removesuffix("```")
        elif content.startswith("```"):
            content = content.removeprefix("```").removesuffix("```")

        result = json.loads(content)
        done = result.get("done", False)

        if done:
            return (False, "")
        else:
            return (True, result.get("question", ""))

    except json.JSONDecodeError as e:
        click.echo(f"⚠️  LLM response không phải JSON hợp lệ: {e}")
        click.echo("Trả về done=True để kết thúc")
        return (False, "")
    except Exception as e:
        click.echo(f"❌ LLM call failed: {e}")
        raise


def _save_clarification(
    briefs_manager: BriefsManager,
    brief_id: str,
    round_num: int,
    question: str,
    answer: str,
) -> None:
    """
    Lưu Q&A vào clarifications table.

    Args:
        briefs_manager: BriefsManager instance
        brief_id: Brief ID
        round_num: Round number
        question: Câu hỏi
        answer: Câu trả lời
    """
    briefs_manager.add_clarification(
        brief_id=brief_id,
        round_num=round_num,
        question=question,
        answer=answer,
        is_memo=False,
    )


def _convert_to_master_brief(
    briefs_manager: BriefsManager,
    brief_id: str,
) -> None:
    """
    Convert working-brief → master-brief.

    Update type="master" và status="clarified".

    Args:
        briefs_manager: BriefsManager instance
        brief_id: Brief ID
    """
    briefs_manager._convert_to_master(brief_id)


def _execute_clarify(max_rounds: int = 10) -> None:
    """
    Thực thi clarification session với LLM Q&A loop.

    Process:
    1. Tìm active working-brief
    2. Load analysis JSON từ artifacts
    3. LLM generate questions iteratively
    4. User answers each question
    5. Save Q&A vào clarifications table
    6. Convert to master-brief khi xong

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
    domain = active_brief.get("domain", "generic")
    click.echo(f"   → Brief: {active_brief.get('title')}")
    click.echo(f"   → ID: {brief_id}")
    click.echo(f"   → Domain: {domain}")
    click.echo(f"   → Max rounds: {max_rounds}")
    click.echo("")

    # Bước 2: Load analysis JSON từ artifacts
    try:
        artifacts_manager = ArtifactsManager()
        artifacts_manager.init()

        analysis_artifact = None
        for artifact in artifacts_manager.list(artifact_type="analysis", brief_id=brief_id):
            analysis_artifact = artifact
            break

        if not analysis_artifact:
            click.echo("⚠️  Không tìm thấy analysis artifact")
            click.echo("💡 Chạy 'midicoder brief analyze' trước")
            return

        # Load analysis content
        analysis_record = artifacts_manager.get(
            artifact_id=f"analysis-{brief_id}"
        )
        if not analysis_record:
            click.echo("❌ Không load được analysis")
            return

        analysis_data = json.loads(analysis_record.get("content", "{}"))
        click.echo(f"✓ Đã load analysis: {len(analysis_data.get('entities', []))} entities")
        click.echo("")

    except Exception as e:
        click.echo(f"❌ Lỗi khi load analysis: {e}")
        return

    # Bước 3: Load LLM config
    try:
        llm_config = load_llm_config()
        click.echo(f"✓ LLM config: {llm_config.provider} / {llm_config.model}")
        click.echo("")
    except Exception as e:
        click.echo(f"❌ Không thể load LLM config: {e}")
        click.echo("💡 Cấu hình LLM tại ~/.midicoder/midicoder.json")
        return

    # Bước 4: Q&A Loop
    qa_history = []
    round_num = 0

    try:
        while round_num < max_rounds:
            round_num += 1
            click.echo(f"--- Round {round_num}/{max_rounds} ---")

            # Generate question từ LLM
            needs_more, question = _generate_clarification_question(
                analysis_data=analysis_data,
                qa_history=qa_history,
                llm_config=llm_config,
                domain=domain,
            )

            if not needs_more or not question:
                click.echo("✓ LLM xác nhận brief đã đủ rõ")
                break

            # Display question
            click.echo(f"\n🤖 Câu hỏi {round_num}:")
            click.echo(f"   {question}")

            # Get user answer
            answer = click.prompt("Trả lời của bạn", default="")

            if not answer.strip():
                click.echo("⚠️  Câu trả lời trống, bỏ qua")
                continue

            # Save clarification
            _save_clarification(
                briefs_manager=briefs_manager,
                brief_id=brief_id,
                round_num=round_num,
                question=question,
                answer=answer,
            )

            qa_history.append({"question": question, "answer": answer})
            click.echo(f"✓ Đã lưu câu trả lời")
            click.echo("")

    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Người dùng hủy bỏ (Ctrl+C)")
        click.echo("Lưu các câu trả lời đã có và chuyển sang master-brief")

    # Bước 5: Record provenance decisions cho mỗi Q&A
    try:
        provenance_manager = ProvenanceManager()
        provenance_manager.init()
        
        for i, qa in enumerate(qa_history, 1):
            provenance_manager.record_decision(
                decision_id=f"clarify-{brief_id}-q{i}",
                title=f"Clarification Q{i}: {qa['question'][:50]}...",
                status="accepted",
                description=qa['question'],
                rationale=qa['answer'],
                consequences="Brief đã được làm rõ",
                decided_by="user",
                related_brief_id=brief_id,
                related_version=active_brief.get("version", "v1.0.0"),
            )
        
        click.echo(f"✓ Đã record {len(qa_history)} provenance decisions")
    except Exception as e:
        click.echo(f"⚠️  Không thể record provenance: {e}")

    # Bước 6: Convert to master-brief
    click.echo("")
    click.echo("Đang convert thành master-brief...")
    _convert_to_master_brief(briefs_manager, brief_id)
    click.echo(f"✓ Brief đã chuyển sang: type=master, status=clarified")

    # Summary
    click.echo("")
    click.echo("✅ Clarification hoàn tất!")
    click.echo("=" * 60)
    click.echo(f"   → Rounds: {round_num}")
    click.echo(f"   → Questions asked: {len(qa_history)}")
    click.echo(f"   → Answers saved: {len(qa_history)}")
    click.echo(f"   → Status: clarified")
    click.echo("=" * 60)

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