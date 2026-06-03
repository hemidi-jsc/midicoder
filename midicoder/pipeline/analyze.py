"""
Pure pipeline functions for brief analysis and clarification.

Module này KHÔNG phụ thuộc click — dùng được từ cả CLI và WebGUI backend.
CLI (`brief.py`) wrap các functions này thêm click.echo, artifact saving, v.v.
WebGUI backend có thể import trực tiếp HOẶC call CLI command qua subprocess.

Các public function:
- analyze_brief_with_llm()      → BriefAnalysis
- generate_clarification_question() → (needs_more, question_text)
"""

import json
import re
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class BriefAnalysis:
    """Kết quả phân tích brief."""
    json_data: dict
    text_summary: str
    domain: str
    confidence: float
    tokens_used: int = 0
    latency_ms: int = 0


def analyze_brief_with_llm(
    brief_content: str,
    domain: Optional[str] = None,
    brief_id: str = "",
) -> BriefAnalysis:
    """
    Phân tích brief bằng LLM — pure function, không phụ thuộc click.

    Args:
        brief_content: Nội dung brief
        domain: Domain user-provided (optional)
        brief_id: Brief ID (cho compat signature)

    Returns:
        BriefAnalysis với json_data, text_summary, domain, confidence

    Raises:
        Exception: Khi LLM call fail hoặc JSON parse error
    """
    from midicoder.pipeline.llm import load_llm_config, call_llm
    from midicoder.pipeline.domain import (
        detect_domain,
        get_domain_prompt,
        normalize_domain,
    )
    from midicoder.pipeline.context_feed import get_brief_context

    # Load LLM config
    llm_config = load_llm_config()

    # Xác định domain
    if domain:
        final_domain = normalize_domain(domain)
    else:
        final_domain = detect_domain(brief_content, llm_config)

    # Load prompt template
    try:
        system_prompt = get_domain_prompt(final_domain)
    except Exception:
        system_prompt = get_domain_prompt("generic")

    # Query codebase context (optional)
    context_result = None
    try:
        context_result = get_brief_context(
            brief_content=brief_content,
            domain=final_domain,
            model_name=llm_config.model,
            system_prompt=system_prompt,
        )
    except Exception:
        pass

    # Build user message với context (nếu có)
    user_message_content = brief_content
    if context_result and context_result.formatted_context:
        user_message_content = (
            f"{context_result.formatted_context}\n\n## Brief Content:\n{brief_content}"
        )

    # Call LLM
    start_time = time.time()
    response = call_llm(
        config=llm_config,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message_content}],
    )
    latency_ms = int((time.time() - start_time) * 1000)
    tokens_used = response.usage.get("total_tokens", 0)

    # Parse JSON response
    llm_content = response.content.strip()

    # Strip <thinking> tags từ reasoning models
    llm_content = re.sub(r'<thinking>.*?</thinking>', '', llm_content, flags=re.DOTALL).strip()

    # Extract JSON từ markdown code block
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', llm_content, re.DOTALL)
    if json_match:
        llm_content = json_match.group(1).strip()

    # Fallback: tìm object đầu tiên { ... }
    if not llm_content.startswith('{'):
        brace_start = llm_content.find('{')
        if brace_start >= 0:
            brace_end = llm_content.rfind('}')
            if brace_end >= brace_start:
                llm_content = llm_content[brace_start:brace_end + 1]

    json_data = json.loads(llm_content)

    # Build text summary
    entities = json_data.get("entities", [])
    commands = json_data.get("commands", [])
    queries = json_data.get("queries", [])
    events = json_data.get("events", [])
    ui_components = json_data.get("ui_components", [])
    confidence = json_data.get("confidence", 0.5)
    summary = json_data.get("summary", "")

    entity_names = ', '.join(e.get('name', '') for e in entities[:5])
    text_summary = (
        f"Tóm tắt phân tích brief:\n"
        f"- Domain: {final_domain.title()}\n"
        f"- Số entities: {len(entities)} ({entity_names})\n"
        f"- Số commands: {len(commands)}\n"
        f"- Số queries: {len(queries)}\n"
        f"- Số events: {len(events)}\n"
        f"- Số UI components: {len(ui_components)}\n"
        f"- Độ tin cậy: {confidence:.0%}\n"
        f"- {summary}"
    )

    return BriefAnalysis(
        json_data=json_data,
        text_summary=text_summary,
        domain=final_domain,
        confidence=confidence,
        tokens_used=tokens_used,
        latency_ms=latency_ms,
    )


def generate_clarification_question(
    analysis_data: dict,
    qa_history: list,
    domain: str = "generic",
) -> tuple:
    """
    Generate clarification question bằng LLM — pure function.

    Args:
        analysis_data: Analysis JSON từ brief analyze
        qa_history: Lịch sử Q&A (list of {question, answer})
        domain: Domain name

    Returns:
        (needs_more, question_text)
        - needs_more=True: Còn cần hỏi thêm
        - needs_more=False: Đã đủ rõ, kết thúc
    """
    from midicoder.pipeline.llm import load_llm_config, call_llm
    from midicoder.pipeline.domain import get_domain_prompt
    from midicoder.pipeline.context_feed import get_clarify_context

    # Load LLM config
    llm_config = load_llm_config()

    # Load clarification prompt
    try:
        system_prompt = get_domain_prompt(domain, prompt_type="clarify")
    except Exception:
        system_prompt = get_domain_prompt("generic", prompt_type="clarify")

    # Query codebase context (optional)
    try:
        context_result = get_clarify_context(
            analysis_data=analysis_data,
            qa_history=qa_history,
            model_name=llm_config.model,
        )
    except Exception:
        context_result = None

    # Build user message
    user_content_parts = []

    if context_result and context_result.formatted_context:
        user_content_parts.append(context_result.formatted_context)

    user_content_parts.append(
        f"## Brief Analysis:\n{json.dumps(analysis_data, indent=2, ensure_ascii=False)}"
    )

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

    except json.JSONDecodeError:
        return (False, "")
    except Exception:
        raise
