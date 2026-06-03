"""
Domain Detection & Prompt Loading Helper.

Module này cung cấp:
- Auto-detect domain từ brief content
- Load prompt templates từ domain packs hoặc default
- Map domain names về canonical names

Prompt path priority (EU-0.3+):
1. midicoder/pipeline/prompts/{domain}/brief-{type}.md  (new — package-level)
2. industry/{original-domain}/prompts/brief-{type}.md    (legacy — backward compat)
3. industry/{normalized-domain}/brief-{type}.md           (legacy alternate)
4. midicoder/pipeline/prompts/default-brief-{type}.md     (fallback)

E02: Brief Processing - Domain Detection
"""

import logging
from pathlib import Path
from typing import Optional

from midicoder.pipeline.llm import load_llm_config, call_llm
from midicoder.pipeline.prompts import load_prompt as _load_prompt_from_package

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

# Default prompt paths (flat files in prompts/)
DEFAULT_PROMPT_PREFIX = "brief"  # brief-analyze

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

    Priority (EU-0.3+):
    1. midicoder/pipeline/prompts/{normalized-domain}/brief-{type}.md  (new — package-level)
    2. industry/{original-domain}/prompts/brief-{type}.md              (legacy — backward compat)
    3. industry/{original-domain}/brief-{type}.md                      (legacy alternate)
    4. industry/{normalized-domain}/brief-{type}.md                    (legacy canonical)
    5. midicoder/pipeline/prompts/brief-{type}.md                      (fallback)

    Ví dụ:
    - Input: "ecommerce-d2c", prompt_type="analyze"
      1. prompts/ecommerce/brief-analyze.md (normalized → ecommerce) ✅
      2. industry/ecommerce-d2c/prompts/brief-analyze.md (legacy fallback)

    Args:
        domain: Domain name (original hoặc normalized)
        industry_path: Path đến industry folder (default: ./industry) — legacy compat
        prompt_type: Loại prompt ("analyze")

    Returns:
        Prompt template content

    Raises:
        FileNotFoundError: Khi không tìm thấy prompt file
    """
    prompt_filename = f"brief-{prompt_type}"

    # --- Priority 1: New package-level path (normalized domain) ---
    normalized_domain = normalize_domain(domain)
    package_prompt = f"{normalized_domain}/{prompt_filename}"
    try:
        content = _load_prompt_from_package(package_prompt)
        logger.info(f"Load domain prompt (package, {prompt_type}): {package_prompt}")
        return content
    except FileNotFoundError:
        pass

    # --- Priority 2-4: Legacy industry paths (backward compat) ---
    if industry_path is None:
        industry_path = Path("industry")

    legacy_filename = f"{prompt_filename}.md"

    # Try original domain name first
    for legacy_path in [
        industry_path / domain / "prompts" / legacy_filename,
        industry_path / domain / legacy_filename,
    ]:
        if legacy_path.exists():
            logger.info(f"Load domain prompt (legacy original, {prompt_type}): {legacy_path}")
            return legacy_path.read_text(encoding="utf-8")

    # Try normalized domain name
    if normalized_domain != domain:
        for legacy_path in [
            industry_path / normalized_domain / "prompts" / legacy_filename,
            industry_path / normalized_domain / legacy_filename,
        ]:
            if legacy_path.exists():
                logger.info(f"Load domain prompt (legacy normalized, {prompt_type}): {legacy_path}")
                return legacy_path.read_text(encoding="utf-8")

    # --- Priority 5: Fallback to default ---
    try:
        default_prompt = f"{DEFAULT_PROMPT_PREFIX}-{prompt_type}"
        content = _load_prompt_from_package(default_prompt)
        logger.info(f"Dùng default prompt ({prompt_type}) cho domain '{domain}'")
        return content
    except FileNotFoundError:
        pass

    logger.error(f"Không tìm thấy prompt ({prompt_type}) cho domain '{domain}'")
    raise FileNotFoundError(
        f"Không tìm thấy prompt template ({prompt_type}) cho domain '{domain}'.\n"
        f"Đã thử:\n"
        f"  1. midicoder/pipeline/prompts/{normalized_domain}/{prompt_filename}.md\n"
        f"  2. industry/{domain}/prompts/{legacy_filename}\n"
        f"  3. industry/{domain}/{legacy_filename}\n"
        f"  4. midicoder/pipeline/prompts/{DEFAULT_PROMPT_PREFIX}-{prompt_type}.md"
    )


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