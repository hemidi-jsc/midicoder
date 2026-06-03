"""
Mô-đun Context Feed - Tích hợp codebase context vào brief commands.

Cung cấp các hàm để:
- Query codebase context từ indexer
- Format context cho LLM prompt injection
- Calculate adaptive context size theo LLM context window

Sử dụng:
    from midicoder.pipeline.context_feed import (
        get_brief_context,
        format_context_inject,
        calculate_adaptive_limit,
    )
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Optional

from midicoder.pipeline.llm import count_tokens

from midicoder.pipeline.indexer.query import (
    get_relevant_context,
    format_context_for_prompt,
    ContextItem,
    Brief,
)


# Default context window sizes cho các model phổ biến
MODEL_CONTEXT_WINDOWS: dict[str, int] = {
    # GPT models
    "gpt-4": 8192,
    "gpt-4-turbo": 128000,
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-3.5-turbo": 16385,
    # Claude models
    "claude-3-sonnet": 200000,
    "claude-3-opus": 200000,
    "claude-3-haiku": 200000,
    "claude-2": 100000,
    # Other models (default)
    "default": 8192,
}

# Tỷ lệ % context window dành cho codebase context
CONTEXT_WINDOW_RATIO = 0.30  # 30%

# Ngưỡng tối đa % context window được phép dùng (tránh overflow)
MAX_CONTEXT_WINDOW_THRESHOLD = 0.85  # 85%

# Timeout cho context query (giây)
CONTEXT_QUERY_TIMEOUT_SECONDS = 5


@dataclass
class ContextFeedResult:
    """
    Kết quả của context feed operation.

    Attributes:
        context_items: Danh sách ContextItem
        formatted_context: Formatted string cho prompt injection
        token_count: Số tokens của context
        query_time_ms: Thời gian query (ms)
        warning: Warning message (nếu có)
        brief_tokens: Số tokens của brief (nếu có tính)
        system_tokens: Số tokens của system prompt (nếu có tính)
        total_tokens: Tổng tokens (brief + system + context)
    """
    context_items: list[ContextItem]
    formatted_context: str
    token_count: int
    query_time_ms: int
    warning: Optional[str] = None
    brief_tokens: int = 0
    system_tokens: int = 0
    total_tokens: int = 0


def calculate_adaptive_limit(model_name: Optional[str] = None) -> int:
    """
    Calculate adaptive context limit dựa trên model context window.

    Sử dụng 30% của context window làm giới hạn cho codebase context.

    Args:
        model_name: Tên model (e.g., "gpt-4-turbo", "claude-3-sonnet")

    Returns:
        Số tokens tối đa cho context (int)
    """
    if not model_name:
        context_window = MODEL_CONTEXT_WINDOWS["default"]
    else:
        normalized = model_name.lower().strip()

        if normalized in MODEL_CONTEXT_WINDOWS:
            context_window = MODEL_CONTEXT_WINDOWS[normalized]
        else:
            context_window = MODEL_CONTEXT_WINDOWS["default"]
            for key, window in MODEL_CONTEXT_WINDOWS.items():
                if key != "default" and normalized.startswith(key):
                    context_window = window
                    break

    return int(context_window * CONTEXT_WINDOW_RATIO)


def get_brief_context(
    brief_content: str,
    domain: Optional[str] = None,
    model_name: Optional[str] = None,
    db_path: Optional[str] = None,
    system_prompt: str = "",
) -> ContextFeedResult:
    """
    Lấy codebase context cho brief analyze.

    Query context từ codebase dựa trên brief content và domain.
    Format context cho LLM prompt injection.

    Args:
        brief_content: Nội dung brief (Markdown)
        domain: Domain name (optional)
        model_name: Model name để calculate adaptive limit
        db_path: Đường dẫn context.db (optional)
        system_prompt: System prompt để tính total tokens

    Returns:
        ContextFeedResult với context items và formatted string
    """
    start_time = time.time()
    warning = None

    try:
        context_window = _get_model_context_window(model_name)
        max_allowed_tokens = int(context_window * MAX_CONTEXT_WINDOW_THRESHOLD)

        brief_tokens = count_tokens(brief_content)
        system_tokens = count_tokens(system_prompt)
        used_tokens = brief_tokens + system_tokens

        available_for_context = max_allowed_tokens - used_tokens

        if available_for_context <= 0:
            query_time_ms = int((time.time() - start_time) * 1000)
            return ContextFeedResult(
                context_items=[],
                formatted_context="",
                token_count=0,
                query_time_ms=query_time_ms,
                warning=f"⚠️ Không inject context: brief ({brief_tokens} tokens) + system ({system_tokens} tokens) đã chiếm {(used_tokens/context_window*100):.0f}% context window",
            )

        adaptive_limit = min(
            int(context_window * CONTEXT_WINDOW_RATIO),
            available_for_context
        )

        brief = Brief(content=brief_content, domain=domain)

        context_items = _query_context_with_timeout(
            brief=brief,
            db_path=db_path,
            timeout=CONTEXT_QUERY_TIMEOUT_SECONDS,
        )

        if not context_items:
            warning = "⚠️ Không tìm thấy codebase context liên quan cho brief này"

        formatted_context = format_context_for_prompt(context_items)

        token_count = count_tokens(formatted_context)

        if token_count > adaptive_limit and context_items:
            context_items = _truncate_context_by_tokens(
                context_items,
                max_tokens=adaptive_limit,
            )
            formatted_context = format_context_for_prompt(context_items)
            token_count = count_tokens(formatted_context)

        query_time_ms = int((time.time() - start_time) * 1000)

        return ContextFeedResult(
            context_items=context_items,
            formatted_context=formatted_context,
            token_count=token_count,
            query_time_ms=query_time_ms,
            warning=warning,
            brief_tokens=brief_tokens,
            system_tokens=system_tokens,
            total_tokens=used_tokens + token_count,
        )

    except Exception as e:
        query_time_ms = int((time.time() - start_time) * 1000)

        return ContextFeedResult(
            context_items=[],
            formatted_context="",
            token_count=0,
            query_time_ms=query_time_ms,
            warning=f"⚠️ Lỗi khi query codebase context: {str(e)}",
        )


def _query_context_with_timeout(
    brief: Brief,
    db_path: Optional[str],
    timeout: int,
) -> list[ContextItem]:
    """
    Query context với timeout.

    Args:
        brief: Brief object
        db_path: Đường dẫn context.db
        timeout: Timeout (giây)

    Returns:
        Danh sách ContextItem
    """
    if not db_path:
        db_path = _find_context_db()

    if not db_path or not os.path.exists(db_path):
        raise FileNotFoundError(f"Context database not found: {db_path}")

    return get_relevant_context(brief=brief, db_path=db_path, limit=20)


def _truncate_context_by_tokens(
    context_items: list[ContextItem],
    max_tokens: int,
) -> list[ContextItem]:
    """
    Truncate context items để fit vào max_tokens.

    Sort by relevance score và truncate từ items có score thấp nhất.

    Args:
        context_items: Danh sách ContextItem
        max_tokens: Max tokens

    Returns:
        Truncated list của ContextItem
    """
    if not context_items:
        return []

    sorted_items = sorted(context_items, key=lambda x: x.relevance_score, reverse=True)

    accumulated_tokens = 0
    result = []

    for item in sorted_items:
        item_context = item.format_for_prompt()
        item_tokens = count_tokens(item_context)

        if accumulated_tokens + item_tokens <= max_tokens:
            result.append(item)
            accumulated_tokens += item_tokens
        else:
            break

    return result


def format_context_inject(
    context_result: ContextFeedResult,
) -> str:
    """
    Format context result cho prompt injection.

    Args:
        context_result: ContextFeedResult từ get_brief_context

    Returns:
        Formatted string cho prompt injection
    """
    if not context_result.formatted_context:
        return ""

    return context_result.formatted_context


def _get_model_context_window(model_name: Optional[str] = None) -> int:
    """
    Lấy context window size của model.

    Args:
        model_name: Tên model

    Returns:
        Context window size (tokens)
    """
    if not model_name:
        return MODEL_CONTEXT_WINDOWS["default"]

    normalized = model_name.lower().strip()

    if normalized in MODEL_CONTEXT_WINDOWS:
        return MODEL_CONTEXT_WINDOWS[normalized]

    for key, window in MODEL_CONTEXT_WINDOWS.items():
        if key != "default" and normalized.startswith(key):
            return window

    return MODEL_CONTEXT_WINDOWS["default"]


def _find_context_db() -> Optional[str]:
    """
    Tìm context.db trong current project.

    Returns:
        Đường dẫn context.db hoặc None
    """
    cwd = os.getcwd()

    db_path = os.path.join(cwd, ".midicoder", "data", "context.db")
    if os.path.exists(db_path):
        return db_path

    env_db = os.environ.get("MIDICODER_CONTEXT_DB")
    if env_db and os.path.exists(env_db):
        return env_db

    return None


__all__ = [
    "ContextFeedResult",
    "calculate_adaptive_limit",
    "get_brief_context",
    "format_context_inject",
]
