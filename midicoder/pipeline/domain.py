"""
Domain Prompt Loading Helper.

Module này cung cấp:
- Load prompt templates từ domain folder hoặc default
- List các domains có sẵn

Prompt path: domain="default" → midicoder/pipeline/prompts/brief-{type}.md
             domain="ecommerce" → midicoder/pipeline/prompts/ecommerce/brief-{type}.md

Domains được scan từ folder midicoder/pipeline/prompts/ — sync với API GET /projects/techstacks.
"""

import logging
import re
from pathlib import Path

from midicoder.pipeline.prompts import load_prompt as _load_prompt_from_package

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Language resolution
# ---------------------------------------------------------------------------

_LANGUAGE_MAP = {
    "vi": {"language_display_name": "Tiếng Việt", "language_instruction": "Phản hồi bằng Tiếng Việt."},
    "en": {"language_display_name": "English", "language_instruction": "Respond in English."},
}


def _resolve_language_info(language: str) -> dict:
    """Resolve language code to display name and instruction."""
    return _LANGUAGE_MAP.get(language, _LANGUAGE_MAP["vi"])


def _inject_language(content: str, lang_info: dict) -> str:
    """
    Replace {{ language_display_name }} and {{ language_instruction }} in prompt template.

    Uses regex to avoid conflict with JSON curly braces in the prompt content.
    Only replaces double-braced placeholders that match our known keys.
    """
    for key, value in lang_info.items():
        pattern = r"\{\{\s*" + re.escape(key) + r"\s*\}\}"
        content = re.sub(pattern, value, content)
    return content


def _inject_clarification_history(content: str, history: str) -> str:
    """
    Replace {{ clarification_history_placeholder }} in prompt template.

    Args:
        content: Prompt template content
        history: Formatted clarification history text (or "No previous clarifications.")
    """
    placeholder = "{{ clarification_history_placeholder }}"
    if placeholder in content:
        content = content.replace(placeholder, history.strip() or "No previous clarifications.")
    return content


# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

def get_domain_prompt(
    domain: str,
    prompt_type: str = "analyze",
    language: str = "vi",
    clarification_history: str = "",
) -> str:
    """
    Load prompt template cho domain.

    - domain="default"  → prompts/brief-{type}.md
    - domain="ecommerce" → prompts/ecommerce/brief-{type}.md

    Fallback: nếu domain folder không có file → fallback root default.

    Args:
        domain: Tên domain (default, ecommerce, ...)
        prompt_type: Loại prompt (analyze)
        language: Mã ngôn ngữ user chọn (vi, en) — inject vào prompt template
        clarification_history: Lịch sử clarification từ các round trước (format text)

    Returns:
        Prompt template content với language variables và clarification history đã được thay thế

    Raises:
        FileNotFoundError: Khi không tìm thấy prompt file
    """
    prompt_filename = f"brief-{prompt_type}"
    lang_info = _resolve_language_info(language)

    history_text = clarification_history.strip() or "No previous clarifications."

    # domain="default" hoặc empty → root prompt
    if not domain or domain.lower() == "default":
        try:
            content = _load_prompt_from_package(prompt_filename)
            logger.info(f"Load default prompt: {prompt_filename}")
            content = _inject_language(content, lang_info)
            return _inject_clarification_history(content, history_text)
        except FileNotFoundError:
            pass

    # Try domain-specific prompt
    package_prompt = f"{domain}/{prompt_filename}"
    try:
        content = _load_prompt_from_package(package_prompt)
        logger.info(f"Load domain prompt: {package_prompt}")
        content = _inject_language(content, lang_info)
        return _inject_clarification_history(content, history_text)
    except FileNotFoundError:
        pass

    # Fallback to root default
    try:
        content = _load_prompt_from_package(prompt_filename)
        logger.info(f"Fallback to default prompt cho domain '{domain}': {prompt_filename}")
        content = _inject_language(content, lang_info)
        return _inject_clarification_history(content, history_text)
    except FileNotFoundError:
        pass

    logger.error(f"Không tìm thấy prompt ({prompt_type}) cho domain '{domain}'")
    raise FileNotFoundError(
        f"Không tìm thấy prompt template ({prompt_type}) cho domain '{domain}'.\n"
        f"Đã thử:\n"
        f"  1. midicoder/pipeline/prompts/{domain}/{prompt_filename}.md\n"
        f"  2. midicoder/pipeline/prompts/{prompt_filename}.md (default)"
    )


# ---------------------------------------------------------------------------
# Domain listing — scan package prompts dir (same source as get_prompt_domains)
# ---------------------------------------------------------------------------

def list_available_domains() -> list[str]:
    """List các domain folders có trong midicoder/pipeline/prompts/."""
    prompts_dir = Path(__file__).parent / "prompts"
    domains = []
    if prompts_dir.is_dir():
        for entry in sorted(prompts_dir.iterdir()):
            if entry.is_dir() and not entry.name.startswith("__"):
                domains.append(entry.name)
    return sorted(domains)
