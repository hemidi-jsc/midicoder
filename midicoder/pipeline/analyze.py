"""
Pure pipeline functions for brief analysis.

Module này KHÔNG phụ thuộc click — dùng được từ cả CLI và WebGUI backend.
CLI (`brief.py`) wrap các functions này thêm click.echo, artifact saving, v.v.
WebGUI backend có thể import trực tiếp HOẶC call CLI command qua subprocess.

Các public function:
- analyze_brief_with_llm_sync()    → BriefAnalysis (domain explicit, KHÔNG gọi LLM để detect)
- analyze_brief_with_llm_stream()  → async generator (streaming LLM chunks)
"""

import json
import re
import time
from dataclasses import dataclass
from typing import Optional, AsyncIterator


@dataclass
class BriefAnalysis:
    """Kết quả phân tích brief."""
    json_data: dict
    text_summary: str
    domain: str
    confidence: float
    tokens_used: int = 0
    latency_ms: int = 0


@dataclass
class StreamChunk:
    """Chunk từ streaming LLM response."""
    type: str  # "thinking" | "content" | "metadata" | "complete" | "error"
    data: str | dict = ""
    accumulated: str = ""


def _parse_llm_response(llm_content: str) -> tuple[str, dict]:
    """Parse LLM response: strip thinking tags, extract JSON.
    
    Returns:
        (cleaned_text, json_data)
    """
    # Strip <thinking> tags từ reasoning models
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', llm_content, flags=re.DOTALL).strip()

    # Extract JSON từ markdown code block
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group(1).strip()

    # Fallback: tìm object đầu tiên { ... }
    if not cleaned.startswith('{'):
        brace_start = cleaned.find('{')
        if brace_start >= 0:
            brace_end = cleaned.rfind('}')
            if brace_end >= brace_start:
                cleaned = cleaned[brace_start:brace_end + 1]

    json_data = json.loads(cleaned)
    return cleaned, json_data


def _build_text_summary(json_data: dict, domain: str) -> str:
    """Build text summary từ json_data."""
    entities = json_data.get("entities", [])
    commands = json_data.get("commands", [])
    queries = json_data.get("queries", [])
    events = json_data.get("events", [])
    ui_components = json_data.get("ui_components", [])
    confidence = json_data.get("confidence", 0.5)
    summary = json_data.get("summary", "")

    entity_names = ', '.join(e.get('name', '') for e in entities[:5])
    return (
        f"Tóm tắt phân tích brief:\n"
        f"- Domain: {domain.title()}\n"
        f"- Số entities: {len(entities)} ({entity_names})\n"
        f"- Số commands: {len(commands)}\n"
        f"- Số queries: {len(queries)}\n"
        f"- Số events: {len(events)}\n"
        f"- Số UI components: {len(ui_components)}\n"
        f"- Độ tin cậy: {confidence:.0%}\n"
        f"- {summary}"
    )


def analyze_brief_with_llm_sync(
    brief_content: str,
    domain: str = "default",
    brief_id: str = "",
    language: str = "vi",
    clarification_history: str = "",
) -> BriefAnalysis:
    """
    Phân tích brief bằng LLM — domain explicit (KHÔNG gọi LLM để detect domain).

    Domain lấy từ projects.db field `domain` của active project.
    LLM config lấy từ settings.db (global-level).

    Args:
        brief_content: Nội dung brief
        domain: Domain explicit từ projects.db (default='default')
        brief_id: Brief ID
        language: Mã ngôn ngữ (vi, en) — inject vào prompt template
        clarification_history: Lịch sử clarification từ các round trước

    Returns:
        BriefAnalysis với json_data, text_summary, domain, confidence
    """
    from midicoder.pipeline.llm import load_llm_config, call_llm
    from midicoder.pipeline.domain import get_domain_prompt
    from midicoder.pipeline.context_feed import get_brief_context

    # Load LLM config từ settings.db
    llm_config = load_llm_config()

    # Domain từ project — dùng nguyên value (default, ecommerce, ...)
    final_domain = domain

    # Load prompt template theo domain
    try:
        system_prompt = get_domain_prompt(final_domain, language=language, clarification_history=clarification_history)
    except Exception:
        system_prompt = get_domain_prompt("default", language=language, clarification_history=clarification_history)

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

    # Build user message
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

    # Parse response
    _, json_data = _parse_llm_response(response.content)
    text_summary = _build_text_summary(json_data, final_domain)

    return BriefAnalysis(
        json_data=json_data,
        text_summary=text_summary,
        domain=final_domain,
        confidence=json_data.get("confidence", 0.5),
        tokens_used=tokens_used,
        latency_ms=latency_ms,
    )


async def analyze_brief_with_llm_stream(
    brief_content: str,
    domain: str = "default",
    brief_id: str = "",
    language: str = "vi",
    clarification_history: str = "",
) -> AsyncIterator[StreamChunk]:
    """
    Phân tích brief bằng LLM với streaming — phát từng chunk qua WebSocket.

    Message types:
    - {"type": "system_prompt", "data": "..."} — prompt template đã dùng
    - {"type": "llm_config", "data": {"model": "...", "temperature": ...}} — LLM config dùng
    - {"type": "thinking", "data": "..."} — reasoning/thinking của model
    - {"type": "content", "data": "..."} — chunk nội dung (accumulated)
    - {"type": "complete", "data": {json_data}} — kết quả cuối cùng
    - {"type": "error", "data": "error message"} — lỗi

    Args:
        brief_content: Nội dung brief
        domain: Domain từ projects.db
        brief_id: Brief ID
        language: Mã ngôn ngữ (vi, en) — inject vào prompt template
        clarification_history: Lịch sử clarification từ các round trước

    Yields:
        StreamChunk cho từng message type
    """
    from midicoder.pipeline.llm import load_llm_config, call_llm_stream
    from midicoder.pipeline.domain import get_domain_prompt
    from midicoder.pipeline.context_feed import get_brief_context

    try:
        # Load LLM config
        llm_config = load_llm_config()
        # Domain từ project — dùng nguyên value
        final_domain = domain

        # Load prompt
        try:
            system_prompt = get_domain_prompt(final_domain, language=language, clarification_history=clarification_history)
        except Exception:
            system_prompt = get_domain_prompt("default", language=language, clarification_history=clarification_history)

        # Send metadata
        yield StreamChunk(
            type="system_prompt",
            data=system_prompt,
        )
        yield StreamChunk(
            type="llm_config",
            data={
                "provider": llm_config.provider,
                "model": llm_config.model,
                "temperature": llm_config.temperature,
                "max_tokens": llm_config.max_tokens,
            },
        )
        yield StreamChunk(
            type="domain",
            data=final_domain,
        )

        # Query codebase context
        user_message_content = brief_content
        context_result = None
        try:
            context_result = get_brief_context(
                brief_content=brief_content,
                domain=final_domain,
                model_name=llm_config.model,
                system_prompt=system_prompt,
            )
            if context_result and context_result.formatted_context:
                user_message_content = (
                    f"{context_result.formatted_context}\n\n## Brief Content:\n{brief_content}"
                )
                yield StreamChunk(
                    type="context_injected",
                    data={"token_count": context_result.token_count, "query_time_ms": context_result.query_time_ms},
                )
        except Exception:
            pass

        # Send raw request payload — the exact JSON sent to LLM
        raw_request = {
            "model": llm_config.model,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message_content}],
            "temperature": llm_config.temperature,
            "max_tokens": llm_config.max_tokens,
        }
        yield StreamChunk(
            type="user_payload",
            data={
                "brief_length": len(brief_content),
                "user_message_length": len(user_message_content),
                "raw_request": raw_request,
            },
        )

        # Start streaming
        start_time = time.time()
        accumulated = ""
        thinking_buffer = ""
        in_thinking = False

        async for chunk in call_llm_stream(
            config=llm_config,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message_content}],
        ):
            content = chunk.content or ""
            if content:
                accumulated += content

                # Detect <thinking> tags
                if "<thinking>" in content and "</thinking>" not in content:
                    in_thinking = True
                    thinking_buffer += content
                    yield StreamChunk(type="thinking", data=content, accumulated=accumulated)
                    continue
                if in_thinking:
                    thinking_buffer += content
                    if "</thinking>" in content:
                        in_thinking = False
                        yield StreamChunk(type="thinking_end", data=thinking_buffer)
                        thinking_buffer = ""
                    else:
                        yield StreamChunk(type="thinking", data=content, accumulated=accumulated)
                    continue

                # Regular content chunk
                yield StreamChunk(type="content", data=content, accumulated=accumulated)

        latency_ms = int((time.time() - start_time) * 1000)

        # Get usage from last chunk — many providers (Ollama, OpenRouter) don't return it
        tokens_used = 0
        prompt_tokens = 0
        completion_tokens = 0
        usage = chunk.usage if hasattr(chunk, "usage") and chunk.usage else None
        if usage:
            if hasattr(usage, "prompt_tokens"):
                prompt_tokens = getattr(usage, "prompt_tokens", 0)
                completion_tokens = getattr(usage, "completion_tokens", 0)
            elif isinstance(usage, dict):
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
            tokens_used = prompt_tokens + completion_tokens

        # Fallback: estimate tokens via tiktoken when provider doesn't return usage
        if tokens_used == 0:
            try:
                from midicoder.pipeline.llm import count_tokens
                pt = count_tokens(system_prompt + user_message_content, llm_config.model)
                ct = count_tokens(accumulated, llm_config.model)
                prompt_tokens = pt
                completion_tokens = ct
                tokens_used = pt + ct
            except Exception:
                pass  # keep zeros if tiktoken also fails

        # Estimate cost (approximate, based on common pricing)
        cost = (prompt_tokens * 0.001 + completion_tokens * 0.002) / 1000  # USD per 1K tokens

        # Parse final JSON
        _, json_data = _parse_llm_response(accumulated)

        # Extract confidence & quality_score from root OR nested metadata dict
        confidence = json_data.get("confidence")
        quality_score = json_data.get("quality_score")
        if confidence is None or quality_score is None:
            meta = json_data.get("metadata")
            if isinstance(meta, dict):
                if confidence is None:
                    confidence = meta.get("confidence")
                if quality_score is None:
                    quality_score = meta.get("quality_score")
        if confidence is None:
            confidence = 0.5
        if quality_score is None:
            quality_score = confidence

        yield StreamChunk(
            type="complete",
            data={
                "json_data": json_data,
                "domain": final_domain,
                "confidence": confidence,
                "quality_score": quality_score,
                "latency_ms": latency_ms,
                "tokens_used": tokens_used,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "estimated_cost_usd": round(cost, 4),
                "model": llm_config.model,
            },
        )

        # Send final accumulated response content
        yield StreamChunk(
            type="final_content",
            data=accumulated,
        )

    except Exception as e:
        yield StreamChunk(type="error", data=str(e))
