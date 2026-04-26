"""
Domain Detection & Prompt Loading Helper.

Module này cung cấp:
- Auto-detect domain từ brief content
- Load prompt templates từ domain packs hoặc default
- Map domain names về canonical names

E02: Brief Processing - Domain Detection
"""

import logging
from pathlib import Path
from typing import Optional

from midicoder.pipeline.llm import load_llm_config, call_llm

# Logger
logger = logging.getLogger(__name__)

# canonical domain names
KNOWN_DOMAINS = [
    "ecommerce",
    "finance",
    "healthcare",
    "saas",
    "marketplace",
    "logistics",
    "education",
    "social",
    "content",
    "crm",
    "erp",
    "hrms",
    "generic",  # default khi không detect được
]

# Default prompt paths
DEFAULT_ANALYZE_PROMPT_PATH = Path(__file__).parent / "prompts" / "default-brief-analyze.md"
DEFAULT_CLARIFY_PROMPT_PATH = Path(__file__).parent / "prompts" / "default-brief-clarify.md"

# Domain detection prompt (nhỏ, nhanh)
DOMAIN_DETECTION_PROMPT = """
Bạn là domain classifier. Đọc brief và xác định domain chính.

TRẢ LỜI CHỈ 1 TỪ: domain name từ danh sách sau:
{domains_list}

Nếu không rõ: trả về "generic"

Brief:
{brief_content}

Domain:"""


def detect_domain(brief_content: str, llm_config: Optional[dict] = None) -> str:
    """
    Auto-detect domain từ brief content bằng LLM.

    Args:
        brief_content: Nội dung brief (Markdown)
        llm_config: LLM config (optional, nếu None sẽ load từ file)

    Returns:
        Domain name (canonical)
    """
    # Load LLM config nếu không có
    if llm_config is None:
        try:
            llm_config = load_llm_config()
        except Exception as e:
            logger.warning(f"Không thể load LLM config: {e}, dùng 'generic'")
            return "generic"

    # Build prompt
    domains_list = ", ".join(KNOWN_DOMAINS[:-1])  # Loại "generic"
    prompt = DOMAIN_DETECTION_PROMPT.format(
        domains_list=domains_list, brief_content=brief_content[:2000]  # Giới hạn 2000 chars
    )

    try:
        # Call LLM
        response = call_llm(
            config=llm_config,
            system="You are a domain classifier. Reply with EXACTLY one domain name.",
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract domain from response
        detected = response.content.strip().lower()

        # Normalize và validate
        for domain in KNOWN_DOMAINS:
            if domain in detected or detected in domain:
                logger.info(f"Detected domain: {domain}")
                return domain

        # Nếu không match, return generic
        logger.warning(f"Domain không khớp '{detected}', dùng 'generic'")
        return "generic"

    except Exception as e:
        logger.error(f"Lỗi khi detect domain: {e}")
        return "generic"


def get_domain_prompt(
    domain: str,
    industry_path: Optional[Path] = None,
    prompt_type: str = "analyze",
) -> str:
    """
    Load prompt template cho domain.

    Supports two prompt types:
    - "analyze": brief-analyze.md (cho brief analyze)
    - "clarify": brief-clarify.md (cho brief clarify)

    Priority:
    1. industry/<domain>/prompts/brief-{type}.md (original domain name)
    2. industry/<domain>/brief-{type}.md (original domain name)
    3. industry/<normalized-domain>/prompts/brief-{type}.md (canonical name)
    4. industry/<normalized-domain>/brief-{type}.md (canonical name)
    5. Default prompt (midicoder/pipeline/prompts/default-brief-{type}.md)

    Ví dụ:
    - Input: "ecommerce-d2c", prompt_type="analyze" → Check "industry/ecommerce-d2c/prompts/brief-analyze.md"
    - Input: "ecommerce-d2c", prompt_type="clarify" → Check "industry/ecommerce-d2c/prompts/brief-clarify.md"
    - Input: "e-commerce" → normalize → "ecommerce" → Check "industry/ecommerce/prompts/brief-analyze.md"

    Args:
        domain: Domain name (original hoặc normalized)
        industry_path: Path đến industry folder (default: ./industry)
        prompt_type: Loại prompt ("analyze" hoặc "clarify")

    Returns:
        Prompt template content

    Raises:
        FileNotFoundError: Khi không tìm thấy prompt file
    """
    if industry_path is None:
        industry_path = Path("industry")

    # Xác định prompt filename dựa theo prompt_type
    prompt_filename = f"brief-{prompt_type}.md"

    # Try original domain name first (preserves exact path like "ecommerce-d2c")
    original_prompt_path = industry_path / domain / "prompts" / prompt_filename
    if original_prompt_path.exists():
        logger.info(f"Load domain prompt (original, {prompt_type}): {original_prompt_path}")
        return original_prompt_path.read_text(encoding="utf-8")

    # Try alternate path with original domain
    alt_original_path = industry_path / domain / prompt_filename
    if alt_original_path.exists():
        logger.info(f"Load alternate domain prompt (original, {prompt_type}): {alt_original_path}")
        return alt_original_path.read_text(encoding="utf-8")

    # Try normalized domain name (canonical)
    normalized_domain = normalize_domain(domain)
    if normalized_domain != domain:
        normalized_prompt_path = industry_path / normalized_domain / "prompts" / prompt_filename
        if normalized_prompt_path.exists():
            logger.info(f"Load domain prompt (normalized, {prompt_type}): {normalized_prompt_path}")
            return normalized_prompt_path.read_text(encoding="utf-8")

        # Try alternate path with normalized domain
        alt_normalized_path = industry_path / normalized_domain / prompt_filename
        if alt_normalized_path.exists():
            logger.info(f"Load alternate domain prompt (normalized, {prompt_type}): {alt_normalized_path}")
            return alt_normalized_path.read_text(encoding="utf-8")

    # Fallback to default
    default_path = DEFAULT_CLARIFY_PROMPT_PATH if prompt_type == "clarify" else DEFAULT_ANALYZE_PROMPT_PATH
    if not default_path.exists():
        logger.error(f"Default prompt không tồn tại: {default_path}")
        raise FileNotFoundError(f"Default prompt file not found: {default_path}")

    logger.info(f"Dùng default prompt ({prompt_type}) cho domain '{domain}'")
    return default_path.read_text(encoding="utf-8")


def normalize_domain(domain: str) -> str:
    """
    Normalize domain name về canonical form.

    Args:
        domain: Domain name (có thể có dash, underscore, ...)

    Returns:
        Canonical domain name
    """
    # Convert to lowercase, replace separators
    normalized = domain.lower().replace("-", "_").replace(" ", "_")

    # Map aliases (cả dạng có dash và có underscore)
    # Lưu ý: domain name trong file system phải match với canonical name
    # Ví dụ: industry/ecommerce-d2c/prompts/brief-analyze.md → canonical = "ecommerce"
    aliases = {
        "ecommerce": [
            "ecommerce", "e_commerce", "ecom", "shop", "store", "retail", "e-commerce",
            "ecommerce-d2c", "ecommerce_d2c", "d2c", "d_2_c"  # E-commerce D2C variants
        ],
        "finance": ["finance", "fintech", "banking", "payment"],
        "healthcare": ["healthcare", "medical", "hospital", "clinic"],
        "saas": ["saas", "software"],
        "marketplace": ["marketplace", "multi-vendor", "multi_vendor", "b2b2c"],
        "logistics": ["logistics", "shipping", "delivery", "supply-chain", "supply_chain"],
        "education": ["education", "edu", "learning", "lms", "elearning"],
        "social": ["social", "social-network", "social_network", "social-media", "social_media"],
        "content": ["content", "cms", "blog", "news", "media"],
        "crm": ["crm", "customer-relationship", "customer_relationship"],
        "erp": ["erp", "enterprise-resource", "enterprise_resource"],
        "hrms": ["hrms", "hrm", "human-resource", "human_resource"],
    }

    # Check aliases (với normalized string)
    for canonical, aliases_list in aliases.items():
        if normalized in aliases_list:
            logger.debug(f"Map alias '{normalized}' → '{canonical}'")
            return canonical

    # Check if already known
    if normalized in KNOWN_DOMAINS:
        return normalized

    # Return generic
    logger.warning(f"Domain '{domain}' không recognized, normalize về 'generic'")
    return "generic"


def get_industry_path() -> Path:
    """
    Lấy path đến industry folder.

    Returns:
        Path đến industry/briefs
    """
    return Path("industry/briefs")


def list_available_domains() -> list[str]:
    """
    List các domains có sẵn trong industry folder.

    Returns:
        List of domain names
    """
    industry_path = get_industry_path()
    if not industry_path.exists():
        return []

    domains = []
    for domain_dir in industry_path.iterdir():
        if domain_dir.is_dir():
            # Check if có brief.md
            brief_file = domain_dir / "brief.md"
            if brief_file.exists():
                domains.append(domain_dir.name)

    return sorted(domains)