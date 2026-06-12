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
from pathlib import Path

from midicoder.pipeline.prompts import load_prompt as _load_prompt_from_package

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

def get_domain_prompt(
    domain: str,
    prompt_type: str = "analyze",
) -> str:
    """
    Load prompt template cho domain.

    - domain="default"  → prompts/brief-{type}.md
    - domain="ecommerce" → prompts/ecommerce/brief-{type}.md

    Fallback: nếu domain folder không có file → fallback root default.

    Returns:
        Prompt template content

    Raises:
        FileNotFoundError: Khi không tìm thấy prompt file
    """
    prompt_filename = f"brief-{prompt_type}"

    # domain="default" hoặc empty → root prompt
    if not domain or domain.lower() == "default":
        try:
            content = _load_prompt_from_package(prompt_filename)
            logger.info(f"Load default prompt: {prompt_filename}")
            return content
        except FileNotFoundError:
            pass

    # Try domain-specific prompt
    package_prompt = f"{domain}/{prompt_filename}"
    try:
        content = _load_prompt_from_package(package_prompt)
        logger.info(f"Load domain prompt: {package_prompt}")
        return content
    except FileNotFoundError:
        pass

    # Fallback to root default
    try:
        content = _load_prompt_from_package(prompt_filename)
        logger.info(f"Fallback to default prompt cho domain '{domain}': {prompt_filename}")
        return content
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
