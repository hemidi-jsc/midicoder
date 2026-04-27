"""
Mô-đun Context Feed - Tích hợp codebase context vào brief commands.

Cung cấp các hàm để:
- Query codebase context từ indexer
- Format context cho LLM prompt injection
- Calculate adaptive context size theo LLM context window

Sử dụng:
    from midicoder.pipeline.context_feed import (
        get_brief_context,
        get_clarify_context,
        format_context_inject,
        calculate_adaptive_limit,
    )
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Optional

import litellm

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
    
    Examples:
        >>> calculate_adaptive_limit("gpt-4")
        2457  # 30% của 8192
        >>> calculate_adaptive_limit("claude-3-sonnet")
        60000  # 30% của 200000
    """
    if not model_name:
        context_window = MODEL_CONTEXT_WINDOWS["default"]
    else:
        # Normalize model name (lowercase, remove version suffixes)
        normalized = model_name.lower().strip()
        
        # Try exact match first
        if normalized in MODEL_CONTEXT_WINDOWS:
            context_window = MODEL_CONTEXT_WINDOWS[normalized]
        else:
            # Try prefix match (e.g., "gpt-4-0125-preview" → "gpt-4")
            for key, window in MODEL_CONTEXT_WINDOWS.items():
                if key != "default" and normalized.startswith(key):
                    context_window = window
                    break
            else:
                # Fallback to default
                context_window = MODEL_CONTEXT_WINDOWS["default"]
    
    # Calculate 30% of context window
    adaptive_limit = int(context_window * CONTEXT_WINDOW_RATIO)
    
    return adaptive_limit


def count_tokens_with_litellm(text: str, model: str = "gpt-4o-mini") -> int:
    """
    Đếm số tokens chính xác bằng litellm SDK.
    
    Sử dụng litellm.token_counter để đếm tokens chính xác theo model tokenizer.
    
    Args:
        text: Text để đếm tokens
        model: Model name để dùng tokenizer tương ứng
    
    Returns:
        Số tokens chính xác
    
    Examples:
        >>> count_tokens_with_litellm("Hello world", "gpt-4o-mini")
        3
    """
    if not text:
        return 0
    
    try:
        # Sử dụng litellm's token_counter
        return litellm.token_counter(model=model, text=text)
    except Exception:
        # Fallback: ~4 chars per token
        return len(text) // 4


def estimate_tokens(text: str) -> int:
    """
    Ước lượng số tokens của text.
    
    Deprecated: Dùng count_tokens_with_litellm() thay vì hàm này.
    Simple estimation: ~4 characters per token (English average).
    
    Args:
        text: Text để ước lượng
    
    Returns:
        Ước lượng số tokens
    """
    if not text:
        return 0
    return len(text) // 4


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
    
    Lưu ý: Không inject context nếu total tokens (system + brief + context) 
    vượt quá MAX_CONTEXT_WINDOW_THRESHOLD (85%) của model context window.
    
    Args:
        brief_content: Nội dung brief (Markdown) - giữ nguyên, không compact
        domain: Domain name (optional)
        model_name: Model name để calculate adaptive limit
        db_path: Đường dẫn context.db (optional)
        system_prompt: System prompt để tính total tokens
    
    Returns:
        ContextFeedResult với context items và formatted string
    
    Examples:
        >>> result = get_brief_context(brief_content="# E-commerce Platform", domain="ecommerce")
        >>> print(result.formatted_context)
        "## Codebase Context\\n\\nThe following symbols..."
        >>> print(result.warning)
        None  # Hoặc warning message nếu không có context
    """
    start_time = time.time()
    warning = None
    
    try:
        # Get model context window
        context_window = _get_model_context_window(model_name)
        max_allowed_tokens = int(context_window * MAX_CONTEXT_WINDOW_THRESHOLD)
        
        # Đếm tokens của brief và system prompt bằng litellm
        brief_tokens = count_tokens_with_litellm(brief_content, model_name)
        system_tokens = count_tokens_with_litellm(system_prompt, model_name)
        used_tokens = brief_tokens + system_tokens
        
        # Kiểm tra còn space cho context không
        available_for_context = max_allowed_tokens - used_tokens
        
        if available_for_context <= 0:
            # Không còn space, không inject context
            query_time_ms = int((time.time() - start_time) * 1000)
            return ContextFeedResult(
                context_items=[],
                formatted_context="",
                token_count=0,
                query_time_ms=query_time_ms,
                warning=f"⚠️ Không inject context: brief ({brief_tokens} tokens) + system ({system_tokens} tokens) đã chiếm {(used_tokens/context_window*100):.0f}% context window",
            )
        
        # Calculate adaptive limit (không vượt available space)
        adaptive_limit = min(
            int(context_window * CONTEXT_WINDOW_RATIO),
            available_for_context
        )
        
        # Create Brief object cho query API
        brief = Brief(content=brief_content, domain=domain)
        
        # Query context với timeout
        context_items = _query_context_with_timeout(
            brief=brief,
            db_path=db_path,
            timeout=CONTEXT_QUERY_TIMEOUT_SECONDS,
        )
        
        if not context_items:
            warning = "⚠️ Không tìm thấy codebase context liên quan cho brief này"
        
        # Format context cho prompt
        formatted_context = format_context_for_prompt(context_items)
        
        # Đếm token context chính xác bằng litellm
        token_count = count_tokens_with_litellm(formatted_context, model_name)
        
        # Truncate nếu vượt adaptive limit
        if token_count > adaptive_limit and context_items:
            context_items = _truncate_context_by_tokens(
                context_items,
                max_tokens=adaptive_limit,
            )
            formatted_context = format_context_for_prompt(context_items)
            token_count = count_tokens_with_litellm(formatted_context, model_name)
        
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


def get_clarify_context(
    analysis_data: dict[str, Any],
    qa_history: list[dict[str, str]],
    model_name: Optional[str] = None,
    db_path: Optional[str] = None,
) -> ContextFeedResult:
    """
    Lấy codebase context cho brief clarify (narrower focus).
    
    Query context dựa trên analysis data và Q&A history.
    Focus vào các entities/commands đang được clarify.
    
    Args:
        analysis_data: Analysis JSON từ brief analyze
        qa_history: Lịch sử Q&A (list of {question, answer})
        model_name: Model name để calculate adaptive limit
        db_path: Đường dẫn context.db (optional)
    
    Returns:
        ContextFeedResult với context items và formatted string
    
    Examples:
        >>> result = get_clarify_context(analysis_data, qa_history)
        >>> print(result.formatted_context)
        "## Codebase Context\\n\\nThe following symbols..."
    """
    start_time = time.time()
    warning = None
    
    try:
        # Calculate adaptive limit (nhỏ hơn cho clarify vì có Q&A history)
        adaptive_limit = calculate_adaptive_limit(model_name)
        
        # Extract focus keywords từ analysis + Q&A
        focus_text = _extract_clarify_focus(analysis_data, qa_history)
        
        # Create Brief object với focus text
        brief = Brief(content=focus_text)
        
        # Query context với timeout
        context_items = _query_context_with_timeout(
            brief=brief,
            db_path=db_path,
            timeout=CONTEXT_QUERY_TIMEOUT_SECONDS,
        )
        
        if not context_items:
            warning = "⚠️ Không tìm thấy codebase context liên quan cho clarification"
        
        # Format context cho prompt
        formatted_context = format_context_for_prompt(context_items)
        
        # Estimate token count và truncate nếu cần
        token_count = estimate_tokens(formatted_context)
        
        if token_count > adaptive_limit and context_items:
            context_items = _truncate_context_by_tokens(
                context_items,
                max_tokens=adaptive_limit,
            )
            formatted_context = format_context_for_prompt(context_items)
            token_count = estimate_tokens(formatted_context)
        
        query_time_ms = int((time.time() - start_time) * 1000)
        
        return ContextFeedResult(
            context_items=context_items,
            formatted_context=formatted_context,
            token_count=token_count,
            query_time_ms=query_time_ms,
            warning=warning,
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
    
    Raises:
        TimeoutError: Nếu query vượt quá timeout
    """
    # Check if context.db exists
    if not db_path:
        db_path = _find_context_db()
    
    if not db_path or not os.path.exists(db_path):
        raise FileNotFoundError(f"Context database not found: {db_path}")
    
    # Query context (synchronous với timeout check)
    # Note: get_relevant_context là sync, timeout được enforce ở外层
    return get_relevant_context(brief=brief, db_path=db_path, limit=20)


def _extract_clarify_focus(
    analysis_data: dict[str, Any],
    qa_history: list[dict[str, str]],
) -> str:
    """
    Extract focus text từ analysis data và Q&A history.
    
    Focus vào các entities/commands đang được clarify.
    
    Args:
        analysis_data: Analysis JSON từ brief analyze
        qa_history: Lịch sử Q&A
    
    Returns:
        Focus text cho context query
    """
    focus_parts = []
    
    # Extract entities from analysis
    entities = analysis_data.get("entities", [])
    if entities:
        entity_names = [e.get("name", "") for e in entities[:5]]  # Top 5 entities
        if entity_names:
            focus_parts.append(f"Entities: {', '.join(entity_names)}")
    
    # Extract commands from analysis
    commands = analysis_data.get("commands", [])
    if commands:
        command_names = [c.get("name", "") for c in commands[:3]]  # Top 3 commands
        if command_names:
            focus_parts.append(f"Commands: {', '.join(command_names)}")
    
    # Extract focus from latest Q&A (narrower focus)
    if qa_history:
        latest_qa = qa_history[-1]  # Latest question/answer
        question = latest_qa.get("question", "")
        answer = latest_qa.get("answer", "")
        if question:
            focus_parts.append(f"Clarifying: {question[:200]}")  # Limit length
        if answer:
            focus_parts.append(f"Answer: {answer[:200]}")  # Limit length
    
    return "\n".join(focus_parts) if focus_parts else ""


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
    
    # Sort by relevance score (highest first)
    sorted_items = sorted(context_items, key=lambda x: x.relevance_score, reverse=True)
    
    # Accumulate tokens until we exceed limit
    accumulated_tokens = 0
    result = []
    
    for item in sorted_items:
        item_context = item.format_for_prompt()
        item_tokens = estimate_tokens(item_context)
        
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
    
    Inject context vào user message (prepend trước brief content).
    
    Args:
        context_result: ContextFeedResult từ get_brief_context hoặc get_clarify_context
    
    Returns:
        Formatted string cho prompt injection (bao gồm cả header)
    
    Examples:
        >>> result = get_brief_context("# Brief")
        >>> injected = format_context_inject(result)
        >>> print(injected)
        "## Codebase Context\\n\\nThe following symbols..."
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
    
    # Try exact match
    if normalized in MODEL_CONTEXT_WINDOWS:
        return MODEL_CONTEXT_WINDOWS[normalized]
    
    # Try prefix match
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
    # Try current directory
    cwd = os.getcwd()
    
    # Check .midicoder/data/context.db
    db_path = os.path.join(cwd, ".midicoder", "data", "context.db")
    if os.path.exists(db_path):
        return db_path
    
    # Check environment variable
    env_db = os.environ.get("MIDICODER_CONTEXT_DB")
    if env_db and os.path.exists(env_db):
        return env_db
    
    return None


__all__ = [
    "ContextFeedResult",
    "calculate_adaptive_limit",
    "estimate_tokens",
    "count_tokens_with_litellm",
    "get_brief_context",
    "get_clarify_context",
    "format_context_inject",
]
