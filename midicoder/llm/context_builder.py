"""
Build filtered context payloads for LLM prompts.

This module implements a stack-aware, budgeted, and deterministic method
to retrieve project context for feeding into LLM prompts (e.g., contract gen).

Key features:
- Stack normalization layer for framework-agnostic retrieval
- Two-stage retrieval: cached keyword map (LLM refresh only if stale) + deterministic filtering
- Hard token budgeting with priority allocation
- Per-target/per-batch context building
- Schema slicing for relevant sections only
- Full traceability and debugging support
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable


# Import KeywordMap - avoid circular import by importing only when needed
def _get_keyword_map_class():
    """Lazy import KeywordMap to avoid circular dependency."""
    from midicoder.brief.analyzer import KeywordMap

    return KeywordMap


# For type hints
if TYPE_CHECKING:
    from midicoder.brief.analyzer import KeywordMap


@dataclass
class ContextOptions:
    """Configuration options for context building parts."""

    include_schema_cheatsheet: bool = True
    include_profile_summary: bool = True
    include_symbols: bool = True
    include_entrypoints: bool = True
    include_seams: bool = True
    include_exemplars: bool = True
    include_memos: bool = True  # Include project memos from feedback/repair cycles
    include_code_snippets: bool = False  # Default to False as it can be expensive
    code_snippet_context_lines: int = 5  # Lines before/after symbol for context
    max_snippet_length: int = 500  # Max characters per snippet
    max_memos: int = 20  # Maximum number of memos to include


# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

# Semantic groups for stack normalization
SEMANTIC_GROUPS = {
    "http_handlers": ["route", "controller", "endpoint", "handler", "api"],
    "di_patterns": ["inject", "dependency", "provider", "service"],
    "orm_models": ["model", "entity", "repository", "schema"],
    "cli_entrypoints": ["cli", "command", "console"],
    "ui_components": ["component", "view", "page", "widget"],
    "integration_boundaries": ["integration", "adapter", "client", "gateway"],
}

# Stack-specific signal mappings
STACK_SIGNALS = {
    "fastapi": {
        "http_handlers": [
            "@app.get",
            "@app.post",
            "@app.put",
            "@app.delete",
            "APIRouter",
        ],
        "di_patterns": ["Depends", "dependency"],
        "orm_models": ["SQLModel", "Base", "Table"],
    },
    "nestjs": {
        "http_handlers": ["@Controller", "@Get", "@Post", "@Put", "@Delete"],
        "di_patterns": ["@Injectable", "@Inject"],
        "orm_models": ["@Entity", "Repository"],
    },
    "laravel": {
        "http_handlers": ["Route::", "Controller"],
        "orm_models": ["Model", "Eloquent"],
    },
    "angular": {
        "ui_components": ["@Component", "@Directive", "@Pipe"],
        "di_patterns": ["@Injectable", "inject"],
    },
    "spring": {
        "http_handlers": ["@RestController", "@GetMapping", "@PostMapping"],
        "di_patterns": ["@Autowired", "@Component", "@Service"],
        "orm_models": ["@Entity", "@Repository"],
    },
}

# Default token budget allocation (in tokens)
DEFAULT_BUDGET = {
    "schema_cheatsheet": 2000,  # Required
    "profile_summary": 200,  # Small
    "symbols": 1500,
    "entrypoints": 1000,
    "seams": 800,
    "exemplars": 1000,
    "memos": 800,  # Project learnings and insights
    "code_snippets": 1500,  # Last, can be trimmed
}

MAX_TOTAL_BUDGET = 8000  # Maximum total tokens for context

STOPWORDS = {
    "and",
    "the",
    "for",
    "with",
    "from",
    "this",
    "that",
    "into",
    "your",
    "you",
    "are",
    "was",
    "were",
    "will",
    "can",
    "could",
    "should",
    "have",
    "has",
    "had",
    "must",
    "when",
    "where",
    "what",
    "which",
    "who",
    "whom",
    "why",
    "how",
    "not",
    "no",
    "yes",
    "true",
    "false",
    "none",
    "null",
    "và",
    "là",
    "của",
    "trong",
    "cho",
    "từ",
    "với",
    "như",
    "này",
    "đó",
    "khi",
    "để",
}

MODEL_SYNONYMS = {
    "entity": {"entity", "entities", "thuc", "thuc_the", "thực", "thực_thể", "domain"},
    "error": {"error", "errors", "lỗi", "loi", "exception"},
    "event": {"event", "events", "sự_kiện", "su_kien"},
    "command": {"command", "commands", "cmd", "lệnh", "lenh"},
    "rule": {"rule", "rules", "policy", "luat", "luật"},
    "http": {"http", "api", "route", "routes", "endpoint"},
    "workflow": {"workflow", "workflows", "luong", "luồng"},
    "scenario": {"scenario", "scenarios", "usecase", "use_case"},
}


# ============================================================================
# DATA CLASSES
# ============================================================================

# KeywordMap is now defined in midicoder.brief.analyzer
# Import it when needed: from midicoder.brief.analyzer import KeywordMap


@dataclass
class RetrievalTrace:
    """Traceability information for debugging."""

    semantic_groups: list[str] = field(default_factory=list)
    keywords_used: list[str] = field(default_factory=list)
    top_k_results: dict[str, int] = field(default_factory=dict)
    estimated_tokens: int = 0
    items_dropped: list[str] = field(default_factory=list)
    budget_allocation: dict[str, int] = field(default_factory=dict)
    keyword_cache_used: bool | None = None


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def _read_json(path: Path) -> dict[str, Any] | list[Any]:
    """Read and parse JSON file."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _estimate_tokens(text: str) -> int:
    """Rough token estimation (1 token ≈ 4 characters)."""
    return len(text) // 4


def _estimate_json_tokens(data: Any) -> int:
    """Estimate tokens for JSON data."""
    return _estimate_tokens(json.dumps(data, ensure_ascii=False))


def _stringify_entry(entry: Any) -> str:
    """Convert entry to string for filtering."""
    try:
        return json.dumps(entry, ensure_ascii=False)
    except TypeError:
        return str(entry)


def _read_config(root: Path) -> dict[str, Any]:
    """Read config.json from .midicoder directory."""
    config_path = root / ".midicoder" / "config.json"
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _extract_code_snippet(
    file_path: Path,
    line: int,
    context_lines: int = 5,
    max_length: int = 500,
) -> str | None:
    """
    Extract code snippet from file around specified line.

    Args:
        file_path: Path to source file
        line: Line number (1-based)
        context_lines: Number of lines before/after to include
        max_length: Maximum characters in snippet

    Returns:
        Code snippet string or None if file can't be read
    """
    if not file_path.exists():
        return None

    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()

        # Convert to 0-based indexing
        target_line = line - 1
        if target_line < 0 or target_line >= len(lines):
            return None

        # Calculate range
        start_line = max(0, target_line - context_lines)
        end_line = min(len(lines), target_line + context_lines + 1)

        # Extract lines
        snippet_lines = []
        for i in range(start_line, end_line):
            line_number = i + 1
            line_content = lines[i]

            # Mark the target line
            if i == target_line:
                snippet_lines.append(f"{line_number:3d}:>> {line_content}")
            else:
                snippet_lines.append(f"{line_number:3d}:   {line_content}")

        snippet = "\n".join(snippet_lines)

        # Truncate if too long
        if len(snippet) > max_length:
            snippet = snippet[: max_length - 3] + "..."

        return snippet

    except (OSError, UnicodeDecodeError):
        return None


def extract_code_snippets(
    root: Path,
    symbols: list[Any],
    keyword_map: KeywordMap,
    options: ContextOptions,
) -> list[dict[str, Any]]:
    """
    Extract code snippets from source files based on filtered symbols.

    This function:
    1. Gets working directory from config.json
    2. For each symbol that matches keywords
    3. Reads the corresponding source file
    4. Extracts code snippet around the symbol location

    Args:
        root: Project root path
        symbols: List of filtered symbols
        keyword_map: Keywords for additional filtering
        options: Context options with snippet configuration

    Returns:
        List of code snippet dictionaries
    """
    if not options.include_code_snippets:
        return []

    # Read config to get working directory
    config = _read_config(root)
    working_dir = config.get("working_dir")

    if not working_dir:
        # No working directory configured, can't extract snippets
        return []

    work_path = Path(working_dir)
    if not work_path.exists() or not work_path.is_dir():
        return []

    snippets = []
    keywords = keyword_map.all_keywords()

    for symbol in symbols:
        # Additional keyword filtering for relevance
        symbol_name = str(symbol.get("name", ""))
        symbol_file = str(symbol.get("file", ""))
        symbol_line = symbol.get("line", 0)

        # Check if symbol matches any keywords
        symbol_text = f"{symbol_name} {symbol_file}".lower()
        if not any(keyword.lower() in symbol_text for keyword in keywords):
            continue

        # Construct absolute file path
        if symbol_file.startswith("/"):
            # Absolute path
            file_path = Path(symbol_file)
        else:
            # Relative to working directory
            file_path = work_path / symbol_file

        # Extract snippet
        snippet_content = _extract_code_snippet(
            file_path=file_path,
            line=symbol_line,
            context_lines=options.code_snippet_context_lines,
            max_length=options.max_snippet_length,
        )

        if snippet_content:
            snippets.append(
                {
                    "symbol_name": symbol_name,
                    "symbol_kind": symbol.get("kind", ""),
                    "file": symbol_file,
                    "line": symbol_line,
                    "snippet": snippet_content,
                    "language": symbol.get("language", ""),
                }
            )

        # Limit number of snippets to avoid budget explosion
        if len(snippets) >= 10:
            break

    return snippets


def load_and_filter_memos(
    context_dir: Path,
    keyword_map: KeywordMap,
    options: ContextOptions,
) -> list[dict[str, Any]]:
    """
    Load project memos and filter them by keyword relevance using weighted scoring.

    Memos are created during contract repair cycles and contain valuable insights
    about fixes, patterns, and lessons learned. They provide context about
    previous issues and solutions that can inform current generation.

    This function ensures:
    - Weighted scoring based on entity/command/domain term matches
    - No duplicate content (deduplication by summary/content similarity)
    - Full content preservation (no aggressive truncation)
    - Relevance-based filtering with minimum score threshold
    - Proper sorting by relevance and recency

    Args:
        context_dir: Path to .midicoder/context directory
        keyword_map: Keywords for filtering relevance
        options: Context options with memo configuration

    Returns:
        List of unique, relevant memo dictionaries (deduplicated by content)
    """
    if not options.include_memos:
        return []

    memos_dir = context_dir / "memos"
    if not memos_dir.exists() or not memos_dir.is_dir():
        return []

    # Get all memo files
    memo_files = list(memos_dir.glob("*.md"))
    if not memo_files:
        return []

    filtered_memos = []
    seen_content_hashes = set()  # Track content hashes to prevent duplicates

    for memo_file in memo_files:
        try:
            content = memo_file.read_text(encoding="utf-8")

            # Extract memo ID from filename (e.g., FB-001.md -> FB-001)
            memo_id = memo_file.stem

            # Parse memo metadata
            lines = content.strip().split("\n")
            title = (
                lines[0].strip("# ") if lines and lines[0].startswith("#") else memo_id
            )

            # Extract creation timestamp from file stats
            stat = memo_file.stat()
            created_at = stat.st_mtime

            memo_data = {
                "id": memo_id,
                "title": title,
                "content": content,
                "created_at": created_at,
                "file_path": str(memo_file),
            }

            # Calculate weighted relevance score
            relevance_score = calculate_weighted_score(memo_data, keyword_map)

            # Apply minimum score threshold (lower for memos since they're valuable context)
            if relevance_score >= 1.0:
                memo_data["relevance_score"] = relevance_score

                # Create summary for context (preserves full content)
                memo_summary = _create_memo_summary(memo_data)

                # Create content hash for deduplication (normalize whitespace and case)
                normalized_content = memo_summary["summary"].lower().strip()
                normalized_content = " ".join(
                    normalized_content.split()
                )  # Normalize whitespace
                content_hash = hash(normalized_content)

                # Skip if we've seen this exact content before
                if content_hash in seen_content_hashes:
                    continue

                filtered_memos.append(memo_summary)
                seen_content_hashes.add(content_hash)

        except (OSError, UnicodeDecodeError):
            # Skip unreadable files
            continue

    # Sort by relevance score then by creation time (newest first)
    filtered_memos.sort(key=lambda x: (-x["relevance_score"], -x["created_at"]))

    # Limit to max_memos (deduplicated list)
    return filtered_memos[: options.max_memos]


def filter_memos(
    memos: list[Any],
    keyword_map: KeywordMap,
    top_k: int = 20,
    min_score: float = 1.0,
) -> list[Any]:
    """
    Filter memos by keyword relevance with deduplication and weighted scoring.

    This is used when memos are provided as a list rather than loaded from disk.
    Uses weighted scoring to prioritize memos matching key entities/commands.
    Ensures no duplicate content (summary) in the result.

    Args:
        memos: List of memo objects
        keyword_map: Structured keywords from master brief
        top_k: Maximum memos to return (default: 20)
        min_score: Minimum relevance score (default: 1.0)

    Returns:
        Filtered and deduplicated list of memos, sorted by relevance.
    """
    scored_memos = []
    seen_content_hashes = set()  # Track content hashes to prevent duplicates

    for memo in memos:
        # Convert memo to searchable text
        memo_text = ""
        summary_text = ""

        if isinstance(memo, dict):
            # Get summary for deduplication
            summary_text = str(memo.get("summary", memo.get("content", "")))
            # Combine all text fields for searching
            memo_text = " ".join(
                str(value) for value in memo.values() if isinstance(value, str)
            )
        else:
            memo_text = str(memo)
            summary_text = memo_text

        # Calculate weighted score
        score = calculate_weighted_score(memo, keyword_map)

        if score >= min_score:
            # Create content hash for deduplication (normalize whitespace and case)
            normalized_content = summary_text.lower().strip()
            normalized_content = " ".join(
                normalized_content.split()
            )  # Normalize whitespace
            content_hash = hash(normalized_content)

            # Skip if duplicate content
            if content_hash in seen_content_hashes:
                continue

            scored_memos.append((memo, score))
            seen_content_hashes.add(content_hash)

    # Sort by score descending
    scored_memos.sort(key=lambda x: x[1], reverse=True)

    # Apply top-k limit
    return [memo for memo, _ in scored_memos[:top_k]]


def _parse_memo_metadata(content: str) -> dict[str, Any]:
    """
    Parse memo metadata from content.

    Looks for metadata patterns like:
    # Title
    **Issue:** FB-001
    **Fixed:** Schema validation error
    **Impact:** Improved entity structure
    """
    lines = content.strip().split("\n")
    metadata = {}

    # Extract title (first # line)
    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()
        if line.startswith("# "):
            metadata["title"] = line[2:].strip()
            break

    # Extract metadata fields
    for line in lines[:10]:  # Check first 10 lines for metadata
        line = line.strip()
        if line.startswith("**") and ":**" in line:
            try:
                key_part, value_part = line.split(":**", 1)
                key = key_part.replace("**", "").strip().lower()
                value = value_part.strip()
                metadata[key] = value
            except ValueError:
                continue

    return metadata


def _create_memo_summary(memo_data: dict[str, Any]) -> dict[str, Any]:
    """
    Create a memo summary for context inclusion.

    This preserves complete memo content for better LLM understanding.
    The memo content is typically concise project learnings, so we include
    the full content rather than truncating.
    """
    content = memo_data.get("content", "")

    # Parse metadata for structured info
    metadata = _parse_memo_metadata(content)

    # For memos, the content is already concise learnings/insights
    # Don't truncate - keep full content to avoid losing critical information
    # Most memo files are 1-3 sentences describing patterns/lessons learned
    summary_text = content.strip()

    # Only truncate if extremely long (>1000 chars, which is unusual for memos)
    if len(summary_text) > 1000:
        summary_text = summary_text[:1000] + "..."

    return {
        "id": memo_data.get("id"),
        "title": metadata.get("title", memo_data.get("title", memo_data.get("id"))),
        "summary": summary_text,
        "content": content,  # Keep full content for reference
        "metadata": metadata,
        "created_at": memo_data.get("created_at"),
        "relevance_score": memo_data.get("relevance_score", 1.0),
    }


# ============================================================================
# STACK DETECTION AND NORMALIZATION
# ============================================================================


def detect_stack(profile: dict[str, Any]) -> str | None:
    """Detect primary stack from profile."""
    stack = profile.get("stack")
    if isinstance(stack, dict):
        return stack.get("target")
    return stack


def normalize_stack_signals(
    stack: str | None,
    artifacts: dict[str, list[Any]],
) -> dict[str, list[Any]]:
    """
    Map stack-specific signals to semantic groups.

    Returns artifacts grouped by semantic categories.
    """
    if not stack or stack.lower() not in STACK_SIGNALS:
        return artifacts

    stack_mapping = STACK_SIGNALS[stack.lower()]
    normalized: dict[str, list[Any]] = {group: [] for group in SEMANTIC_GROUPS}

    # Map each artifact to semantic groups based on stack signals
    for artifact_type, items in artifacts.items():
        for item in items:
            item_text = json.dumps(item, ensure_ascii=False).lower()

            for semantic_group, signals in stack_mapping.items():
                if any(signal.lower() in item_text for signal in signals):
                    if semantic_group in normalized:
                        normalized[semantic_group].append(item)
                        break

    return normalized


# ============================================================================
# DETERMINISTIC FILTERING (STAGE B)
# ============================================================================


def calculate_weighted_score(
    item: Any,
    keyword_map: "KeywordMap",
) -> float:
    """
    Calculate weighted relevance score for an item.

    Weighting strategy:
    - Entity exact match: 5.0
    - Entity substring match: 3.0
    - Command match: 2.5
    - Event match: 2.0
    - API/Integration match: 2.0
    - Domain term match: 1.0

    Returns weighted score (higher = more relevant).

    Args:
        item: Item to score (dict, object, etc.)
        keyword_map: KeywordMap from midicoder.brief.analyzer
    """
    score = 0.0
    item_text = _stringify_entry(item).lower()
    item_name = ""

    # Try to get name field for exact matching
    if isinstance(item, dict):
        item_name = str(item.get("name", "")).lower()

    # Entity keywords: highest weight (domain objects)
    for entity in keyword_map.entities:
        entity_lower = entity.lower()
        if entity_lower == item_name:
            # Exact name match - very strong signal
            score += 5.0
        elif entity_lower in item_text:
            # Substring match
            score += 3.0

    # Command keywords: high weight (actions/operations)
    for cmd in keyword_map.commands:
        if cmd.lower() in item_text:
            score += 2.5

    # Event keywords: medium-high weight
    for event in keyword_map.events:
        if event.lower() in item_text:
            score += 2.0

    # API keywords: medium-high weight
    for api in keyword_map.apis:
        if api.lower() in item_text:
            score += 2.0

    # Integration keywords: medium-high weight
    for integration in keyword_map.integrations:
        if integration.lower() in item_text:
            score += 2.0

    # Domain terms: base weight
    for term in keyword_map.domain_terms:
        if term.lower() in item_text:
            score += 1.0

    # Check synonyms
    for canonical, synonyms in keyword_map.synonyms.items():
        for synonym in synonyms:
            if synonym.lower() in item_text:
                score += 0.8  # Slightly lower than domain terms

    return score


def filter_by_keywords(
    items: list[Any],
    keywords: set[str],
    top_k: int | None = None,
    min_score: float = 0.0,
) -> list[tuple[Any, float]]:
    """
    Filter and score items by keyword matching with simple counting.

    This is the basic version used when KeywordMap is not available.
    For weighted scoring, use filter_by_weighted_score().

    Args:
        items: Items to filter
        keywords: Set of keywords to match
        top_k: Maximum number of items to return (None = no limit)
        min_score: Minimum score threshold (items below this are filtered out)

    Returns:
        List of (item, score) tuples sorted by score descending.
    """
    if not keywords:
        return []

    scored_items: list[tuple[Any, float]] = []

    for item in items:
        item_text = _stringify_entry(item).lower()

        # Count keyword matches
        matches = sum(1 for keyword in keywords if keyword.lower() in item_text)

        if matches > 0:
            score = float(matches)
            if score >= min_score:
                scored_items.append((item, score))

    # Sort by score descending
    scored_items.sort(key=lambda x: x[1], reverse=True)

    # Apply top-k limit if specified
    if top_k is not None and top_k > 0:
        scored_items = scored_items[:top_k]

    return scored_items


def filter_by_weighted_score(
    items: list[Any],
    keyword_map: KeywordMap,
    top_k: int = 20,
    min_score: float = 3.0,
) -> list[tuple[Any, float]]:
    """
    Filter and score items using weighted keyword matching.

    This provides more intelligent scoring than simple keyword counting:
    - Entity matches get higher weight (5.0 for exact, 3.0 for substring)
    - Exact name matches score highest
    - Commands, events, APIs get medium-high weight (2.0-2.5)
    - Domain terms get base weight (1.0)

    Default thresholds are conservative to ensure high-quality context:
    - top_k=20: Limit to most relevant items
    - min_score=3.0: Require at least one strong match (e.g., entity substring)

    Args:
        items: Items to filter
        keyword_map: Structured keyword map with different keyword types
        top_k: Maximum number of items to return (default: 20)
        min_score: Minimum relevance score threshold (default: 3.0)

    Returns:
        List of (item, score) tuples sorted by score descending.
    """
    scored_items: list[tuple[Any, float]] = []

    for item in items:
        score = calculate_weighted_score(item, keyword_map)

        if score >= min_score:
            scored_items.append((item, score))

    # Sort by score descending
    scored_items.sort(key=lambda x: x[1], reverse=True)

    # Apply top-k limit
    return scored_items[:top_k]


def filter_symbols(
    symbols: list[Any],
    keyword_map: KeywordMap,
    top_k: int = 20,
    min_score: float = 3.0,
) -> list[Any]:
    """
    Filter symbols by kind and naming patterns with weighted scoring.

    Uses intelligent scoring to prioritize:
    - Entity classes/types that match domain entities (score: 5.0 exact, 3.0 substring)
    - Commands, events, and API-related symbols (score: 2.0-2.5)
    - Symbols with high keyword relevance

    Conservative defaults ensure high-quality context:
    - Only top 20 most relevant symbols
    - Minimum score 3.0 (requires strong entity/command match)

    Args:
        symbols: List of symbol entries from index
        keyword_map: Structured keywords from master brief
        top_k: Maximum symbols to return (default: 20)
        min_score: Minimum relevance score (default: 3.0)

    Returns:
        Filtered list of symbols, sorted by relevance.
    """
    # Use weighted scoring for better relevance
    scored = filter_by_weighted_score(
        symbols, keyword_map, top_k=top_k, min_score=min_score
    )

    # Return just the items (scores already used for ranking)
    return [item for item, _ in scored]


def filter_entrypoints(
    entrypoints: list[Any],
    keyword_map: KeywordMap,
    semantic_groups: list[str],
    top_k: int = 10,
    min_score: float = 2.0,
) -> list[Any]:
    """
    Filter entrypoints by kind and semantic groups with weighted scoring.

    Args:
        entrypoints: List of entrypoint entries
        keyword_map: Structured keywords from master brief
        semantic_groups: Detected semantic groups
        top_k: Maximum entrypoints to return (default: 10)
        min_score: Minimum relevance score (default: 2.0)

    Returns:
        Filtered list of entrypoints.
    """
    # Only include if brief involves runtime behavior or APIs
    if not keyword_map.apis and "http_handlers" not in semantic_groups:
        return []

    scored = filter_by_weighted_score(
        entrypoints, keyword_map, top_k=top_k, min_score=min_score
    )
    return [item for item, _ in scored]


def filter_seams(
    seams: list[Any],
    keyword_map: KeywordMap,
    top_k: int = 15,
    min_score: float = 2.0,
) -> list[Any]:
    """
    Filter seams, preferring integration boundaries.

    Args:
        seams: List of seam entries (integration boundaries)
        keyword_map: Structured keywords from master brief
        top_k: Maximum seams to return (default: 15)
        min_score: Minimum relevance score (default: 2.0)

    Returns:
        Filtered list of seams.
    """
    scored = filter_by_weighted_score(
        seams, keyword_map, top_k=top_k, min_score=min_score
    )
    return [item for item, _ in scored]


def filter_exemplars(
    exemplars: list[Any],
    keyword_map: KeywordMap,
    semantic_groups: list[str],
    top_k: int = 15,
    min_score: float = 2.0,
) -> list[Any]:
    """
    Filter exemplars by pattern matching semantic groups.

    Args:
        exemplars: List of code pattern exemplars
        keyword_map: Structured keywords from master brief
        semantic_groups: Detected semantic groups
        top_k: Maximum exemplars to return (default: 15)
        min_score: Minimum relevance score (default: 2.0)

    Returns:
        Filtered list of exemplars.
    """
    scored = filter_by_weighted_score(
        exemplars, keyword_map, top_k=top_k, min_score=min_score
    )
    return [item for item, _ in scored]


# ============================================================================
# CONTEXT VALIDATION
# ============================================================================


def validate_context_relevance(
    filtered_symbols: list[Any],
    keyword_map: KeywordMap,
    min_relevance: float = 0.3,
) -> tuple[bool, float, dict[str, Any]]:
    """
    Validate whether filtered context is actually relevant to the master brief.

    This helps detect cases where the indexed codebase doesn't match the brief:
    - Brief describes an eStore but context contains auth/chat symbols
    - Brief describes a CRM but context contains payment gateway code

    The validation checks:
    1. Entity overlap: % of symbols matching brief entities
    2. Command overlap: % of symbols matching brief commands
    3. Overall keyword density

    Args:
        filtered_symbols: Symbols after filtering
        keyword_map: Keywords extracted from master brief
        min_relevance: Minimum relevance threshold (0.0-1.0)

    Returns:
        Tuple of (is_relevant, relevance_score, diagnostic_info)
    """
    if not filtered_symbols:
        return True, 1.0, {"reason": "no_symbols", "message": "No symbols to validate"}

    diagnostic = {
        "total_symbols": len(filtered_symbols),
        "entity_matches": 0,
        "command_matches": 0,
        "keyword_matches": 0,
        "matched_entities": [],
        "matched_commands": [],
        "unmatched_symbols": [],
    }

    # Check entity matches
    for symbol in filtered_symbols:
        symbol_name = str(symbol.get("name", "")).lower()
        symbol_file = str(symbol.get("file", "")).lower()

        matched = False

        # Check if symbol name contains any entity from brief
        for entity in keyword_map.entities:
            entity_lower = entity.lower()
            if entity_lower in symbol_name:
                diagnostic["entity_matches"] += 1
                diagnostic["matched_entities"].append(
                    {
                        "symbol": symbol_name,
                        "entity": entity,
                    }
                )
                matched = True
                break

        # Check if symbol name contains any command from brief
        if not matched:
            for cmd in keyword_map.commands:
                cmd_lower = cmd.lower()
                if cmd_lower in symbol_name:
                    diagnostic["command_matches"] += 1
                    diagnostic["matched_commands"].append(
                        {
                            "symbol": symbol_name,
                            "command": cmd,
                        }
                    )
                    matched = True
                    break

        # Check general keyword matches
        all_keywords = keyword_map.all_keywords()
        if not matched:
            for keyword in all_keywords:
                if keyword.lower() in symbol_name or keyword.lower() in symbol_file:
                    diagnostic["keyword_matches"] += 1
                    matched = True
                    break

        # Track unmatched symbols for diagnostics
        if not matched:
            diagnostic["unmatched_symbols"].append(symbol_name)

    # Calculate relevance scores
    entity_relevance = (
        diagnostic["entity_matches"] / len(filtered_symbols)
        if filtered_symbols
        else 0.0
    )
    command_relevance = (
        diagnostic["command_matches"] / len(filtered_symbols)
        if filtered_symbols
        else 0.0
    )
    keyword_relevance = (
        diagnostic["keyword_matches"] / len(filtered_symbols)
        if filtered_symbols
        else 0.0
    )

    # Overall relevance: weighted average (entities most important)
    relevance_score = (
        entity_relevance * 0.5 + command_relevance * 0.3 + keyword_relevance * 0.2
    )

    diagnostic["entity_relevance"] = entity_relevance
    diagnostic["command_relevance"] = command_relevance
    diagnostic["keyword_relevance"] = keyword_relevance
    diagnostic["overall_relevance"] = relevance_score

    # Determine if relevant
    is_relevant = relevance_score >= min_relevance

    if not is_relevant:
        diagnostic["reason"] = "low_relevance"
        diagnostic["message"] = (
            f"Context relevance too low ({relevance_score:.1%}). "
            f"Brief entities: {keyword_map.entities[:5]}, "
            f"but found symbols: {[s.get('name') for s in filtered_symbols[:5]]}"
        )

    return is_relevant, relevance_score, diagnostic


# ============================================================================
# BUDGETING
# ============================================================================


def apply_budget(
    context_parts: dict[str, Any],
    budget: dict[str, int],
    max_total: int,
) -> tuple[dict[str, Any], RetrievalTrace]:
    """
    Apply hard token budget to context parts.

    Returns filtered context and trace information.
    """
    trace = RetrievalTrace()
    trace.budget_allocation = budget.copy()

    result: dict[str, Any] = {}
    total_tokens = 0

    # Priority order
    priority_order = [
        "schema_cheatsheet",
        "profile_summary",
        "symbols",
        "entrypoints",
        "seams",
        "exemplars",
        "memos",
        "code_snippets",
    ]

    for key in priority_order:
        if key not in context_parts:
            continue

        part = context_parts[key]
        part_tokens = _estimate_json_tokens(part)
        allocated = budget.get(key, 0)

        if total_tokens + part_tokens <= max_total:
            # Fits within budget
            result[key] = part
            total_tokens += part_tokens
            trace.top_k_results[key] = len(part) if isinstance(part, list) else 1
        elif total_tokens + allocated <= max_total:
            # Trim to fit budget
            if isinstance(part, list):
                # Trim list items
                trimmed = []
                trimmed_tokens = 0
                for item in part:
                    item_tokens = _estimate_json_tokens(item)
                    if trimmed_tokens + item_tokens <= allocated:
                        trimmed.append(item)
                        trimmed_tokens += item_tokens
                    else:
                        trace.items_dropped.append(f"{key}[{len(trimmed)}+]")
                        break
                result[key] = trimmed
                total_tokens += trimmed_tokens
                trace.top_k_results[key] = len(trimmed)
            else:
                # Can't trim non-list, skip
                trace.items_dropped.append(key)
        else:
            # No room left
            trace.items_dropped.append(key)

    trace.estimated_tokens = total_tokens

    return result, trace


# ============================================================================
# SCHEMA SLICING
# ============================================================================


def slice_schema_for_targets(
    schema_tree: dict[str, Any],
    target_files: list[str],
) -> dict[str, Any]:
    """
    Slice schema tree to include only sections needed by target files.

    For example, if targets include only entities.yaml and commands.yaml,
    return only those schema sections.
    """
    # Map target files to schema module names
    file_to_schema_modules = {
        "meta/info.yaml": ["midicoder.dsl.schemas.info_model"],
        "meta/profiles.yaml": ["midicoder.dsl.schemas.profiles_model"],
        "meta/secrets.yaml": ["midicoder.dsl.schemas.secrets_contract_model"],
        "glossary.yaml": ["midicoder.dsl.schemas.glossary_model"],
        "domain/entities.yaml": [
            "midicoder.dsl.schemas.entity_model",
            "midicoder.dsl.schemas.named_field_model",
        ],
        "domain/value_objects.yaml": [
            "midicoder.dsl.schemas.value_object_model",
            "midicoder.dsl.schemas.named_field_model",
        ],
        "domain/enums.yaml": ["midicoder.dsl.schemas.enum_model"],
        "domain/errors.yaml": ["midicoder.dsl.schemas.error_model"],
        "domain/events.yaml": [
            "midicoder.dsl.schemas.event_model",
            "midicoder.dsl.schemas.named_field_model",
        ],
        "app/commands.yaml": [
            "midicoder.dsl.schemas.command_model",
            "midicoder.dsl.schemas.named_field_model",
            "midicoder.dsl.schemas.guard_effect_model",
        ],
        "app/queries.yaml": [
            "midicoder.dsl.schemas.query_model",
            "midicoder.dsl.schemas.named_field_model",
        ],
        "app/projections.yaml": [
            "midicoder.dsl.schemas.projection_model",
            "midicoder.dsl.schemas.named_field_model",
        ],
        "persistence/model.yaml": ["midicoder.dsl.schemas.persistence_model"],
        "api/http.yaml": [
            "midicoder.dsl.schemas.http_api_model",
            "midicoder.dsl.schemas.named_field_model",
        ],
        "api/graphql.yaml": [
            "midicoder.dsl.schemas.graphql_api_model",
            "midicoder.dsl.schemas.named_field_model",
        ],
        "rules/rules.yaml": ["midicoder.dsl.schemas.rule_model"],
        "workflows/workflows.yaml": [
            "midicoder.dsl.schemas.workflow_model",
            "midicoder.dsl.schemas.guard_effect_model",
        ],
        "policy/policies.yaml": ["midicoder.dsl.schemas.policy_model"],
        "policy/rbac.yaml": ["midicoder.dsl.schemas.access_policy_model"],
        "policy/permissions_map.yaml": ["midicoder.dsl.schemas.access_policy_model"],
        "policy/security.yaml": ["midicoder.dsl.schemas.security_baseline_model"],
        "policy/reliability.yaml": ["midicoder.dsl.schemas.reliability_model"],
        "integrations/integrations.yaml": [
            "midicoder.dsl.schemas.integration_model",
            "midicoder.dsl.schemas.named_field_model",
        ],
        "ops/observability.yaml": ["midicoder.dsl.schemas.observability_model"],
        "scenarios/scenarios.yaml": ["midicoder.dsl.schemas.scenario_model"],
        "testing/tests.yaml": ["midicoder.dsl.schemas.testing_model"],
    }

    # Collect all needed module names
    needed_modules = set()
    for target in target_files:
        modules = file_to_schema_modules.get(target, [])
        needed_modules.update(modules)

    # If no specific mapping found, return full tree
    if not needed_modules:
        return schema_tree

    # Extract only needed modules from the schema tree
    if "modules" in schema_tree:
        sliced_modules = {}
        for module_name in needed_modules:
            if module_name in schema_tree["modules"]:
                sliced_modules[module_name] = schema_tree["modules"][module_name]

        if sliced_modules:
            # Create sliced schema tree with same structure
            sliced = {
                "version": schema_tree.get("version", "v0"),
                "modules": sliced_modules,
            }
            return sliced

    # Fallback to full tree if slicing fails
    return schema_tree


# ============================================================================
# CONTEXT OPTIONS HELPERS
# ============================================================================


def create_context_options(
    *,
    include_memos: bool = True,
    include_code_snippets: bool = False,
    max_memos: int = 20,
    **kwargs,
) -> ContextOptions:
    """
    Create ContextOptions with common customizations.

    Args:
        include_memos: Whether to include project memos in context
        include_code_snippets: Whether to extract code snippets
        max_memos: Maximum number of memos to include
        **kwargs: Other ContextOptions parameters

    Returns:
        Configured ContextOptions instance
    """
    return ContextOptions(
        include_memos=include_memos,
        include_code_snippets=include_code_snippets,
        max_memos=max_memos,
        **kwargs,
    )


def create_minimal_context_options() -> ContextOptions:
    """
    Create minimal context options for lightweight operations.
    Disables expensive context parts like code snippets and limits memos.
    """
    return ContextOptions(
        include_schema_cheatsheet=True,
        include_profile_summary=True,
        include_symbols=True,
        include_entrypoints=False,
        include_seams=False,
        include_exemplars=False,
        include_memos=True,  # Keep memos as they're valuable and lightweight
        include_code_snippets=False,
        max_memos=10,
    )


def create_repair_context_options() -> ContextOptions:
    """
    Create context options optimized for contract repair.
    Emphasizes memos (previous fixes) and essential context.
    """
    return ContextOptions(
        include_schema_cheatsheet=True,
        include_profile_summary=True,
        include_symbols=True,
        include_entrypoints=True,
        include_seams=True,
        include_exemplars=True,
        include_memos=True,  # Critical for repair - learn from previous fixes
        include_code_snippets=False,
    )


# ============================================================================
# DEBUG AND UTILITY FUNCTIONS
# ============================================================================


def debug_memos_loading(
    context_dir: Path, keyword_map: KeywordMap | None = None
) -> dict[str, Any]:
    """
    Debug function to inspect memo loading process.

    Args:
        context_dir: Path to .midicoder/context directory
        keyword_map: Optional keywords for filtering (if None, loads all)

    Returns:
        Debug information about memo loading
    """
    memos_dir = context_dir / "memos"
    debug_info = {
        "memos_dir_exists": memos_dir.exists(),
        "memos_dir_path": str(memos_dir),
        "total_memo_files": 0,
        "memo_files": [],
        "filtered_memos": [],
        "errors": [],
    }

    if not memos_dir.exists():
        debug_info["errors"].append("Memos directory does not exist")
        return debug_info

    # Get all memo files
    memo_files = list(memos_dir.glob("*.md"))
    debug_info["total_memo_files"] = len(memo_files)
    debug_info["memo_files"] = [str(f) for f in memo_files]

    if keyword_map is None:
        # Create dummy keyword map to load all memos
        KeywordMapClass = _get_keyword_map_class()
        keyword_map = KeywordMapClass(domain_terms=["dummy"])

    # Load memos with filtering
    options = ContextOptions(include_memos=True, max_memos=50)
    try:
        filtered_memos = load_and_filter_memos(context_dir, keyword_map, options)
        debug_info["filtered_memos"] = filtered_memos
        debug_info["filtered_count"] = len(filtered_memos)
    except Exception as e:
        debug_info["errors"].append(f"Error loading memos: {e}")

    return debug_info


# ============================================================================
# MAIN CONTEXT BUILDING FUNCTIONS
# ============================================================================


def _build_context_core(
    context_dir: Path,
    master_brief: str,
    target_files: list[str],
    llm_config: Any,
    call_llm_func: Any,
    cache_dir: Path,
    budget: dict[str, int],
    max_total: int,
    schema_tree: dict[str, Any] | None = None,
    options: ContextOptions | None = None,
    root: Path | None = None,
    contracts_root: Path | None = None,
) -> tuple[dict[str, Any], RetrievalTrace]:
    """
    Core context building logic shared between different context building operations.

    This private function implements the common retrieval pipeline:
    1. Load context artifacts from disk
    2. Extract keywords using LLM
    3. Apply deterministic filtering
    4. Build and budget context parts based on options
    5. Extract code snippets if enabled

    Each context part can be enabled/disabled via ContextOptions for maximum reusability.

    Args:
        context_dir: Path to .midicoder/context directory
        master_brief: Content of master-brief.md
        target_files: List of target contract files
        llm_config: LLM configuration (required)
        call_llm_func: Function to call LLM (required)
        cache_dir: Version cache directory for keyword map
        budget: Budget allocation dict
        max_total: Maximum total token budget
        schema_tree: Full schema tree (optional, required if schema_cheatsheet enabled)
        options: Context options for enabling/disabling parts (defaults to all enabled)
        root: Project root path (optional, required if code_snippets enabled)

    Returns:
        Tuple of (context dict, retrieval trace)

    Raises:
        ValueError: If schema_tree is None but schema_cheatsheet is enabled
        ValueError: If root is None but code_snippets is enabled
    """
    # Use default options if not provided
    if options is None:
        options = ContextOptions()

    # Validate requirements
    if options.include_schema_cheatsheet and schema_tree is None:
        raise ValueError(
            "schema_tree is required when include_schema_cheatsheet is enabled"
        )

    if options.include_code_snippets and root is None:
        raise ValueError("root is required when include_code_snippets is enabled")

    trace = RetrievalTrace()

    # Load context artifacts
    profile_path = context_dir / "profile.json"
    symbols_path = context_dir / "symbols.json"
    entrypoints_path = context_dir / "entrypoints.json"
    seams_path = context_dir / "seams.json"
    exemplars_path = context_dir / "exemplars.json"

    profile = _read_json(profile_path) if profile_path.exists() else {}
    symbols = _read_json(symbols_path) if symbols_path.exists() else []
    entrypoints = _read_json(entrypoints_path) if entrypoints_path.exists() else []
    seams = _read_json(seams_path) if seams_path.exists() else []
    exemplars = _read_json(exemplars_path) if exemplars_path.exists() else []

    # Ensure lists
    if not isinstance(symbols, list):
        symbols = []
    if not isinstance(entrypoints, list):
        entrypoints = []
    if not isinstance(seams, list):
        seams = []
    if not isinstance(exemplars, list):
        exemplars = []

    # Stage A: Load keyword map from cache, refresh with LLM if needed
    from midicoder.brief.analyzer import get_keyword_map_cached

    keyword_map, cache_used = get_keyword_map_cached(
        cache_dir=cache_dir,
        master_brief_text=master_brief,
        llm_config=llm_config,
        call_llm_func=call_llm_func,
    )
    trace.keyword_cache_used = cache_used
    trace.keywords_used = sorted(keyword_map.all_keywords())

    # Detect stack and determine semantic groups
    stack = detect_stack(profile)

    # Determine semantic groups based on target files
    semantic_groups = []
    if any("api/http" in f for f in target_files):
        semantic_groups.append("http_handlers")
    if any("domain/entities" in f for f in target_files):
        semantic_groups.append("orm_models")
    if any("app/commands" in f for f in target_files):
        semantic_groups.append("di_patterns")

    trace.semantic_groups = semantic_groups

    # Stage B: Deterministic retrieval with weighted scoring (only for enabled parts)
    # Use stricter thresholds for better context quality
    filtered_symbols = (
        filter_symbols(
            symbols,
            keyword_map,
            top_k=20,
            min_score=3.0,  # Raised: only high-relevance symbols
        )
        if options.include_symbols
        else []
    )

    filtered_entrypoints = (
        filter_entrypoints(
            entrypoints,
            keyword_map,
            semantic_groups,
            top_k=10,
            min_score=2.0,  # Stricter
        )
        if options.include_entrypoints
        else []
    )

    filtered_seams = (
        filter_seams(seams, keyword_map, top_k=15, min_score=2.0)  # Stricter
        if options.include_seams
        else []
    )

    filtered_exemplars = (
        filter_exemplars(
            exemplars, keyword_map, semantic_groups, top_k=15, min_score=2.0  # Stricter
        )
        if options.include_exemplars
        else []
    )

    filtered_memos = (
        load_and_filter_memos(context_dir, keyword_map, options)
        if options.include_memos
        else []
    )

    # Stage C: Validate context relevance
    if options.include_symbols and filtered_symbols:
        is_relevant, relevance_score, diagnostic = validate_context_relevance(
            filtered_symbols, keyword_map, min_relevance=0.5
        )

        # Add validation info to trace
        trace.semantic_groups.append(f"context_relevance={relevance_score:.2f}")

        # Show simple one-line warning if relevance < 50%
        if relevance_score < 0.5:
            print(
                f"⚠️  Context relevance low ({relevance_score:.0%}). Indexed codebase may not match master brief."
            )

        # Always add diagnostic to trace (for debugging)
        if relevance_score < 0.5:
            trace.items_dropped.append(
                f"low_relevance_{relevance_score:.0%}: "
                f"entity={diagnostic['entity_relevance']:.0%} "
                f"cmd={diagnostic['command_relevance']:.0%} "
                f"kw={diagnostic['keyword_relevance']:.0%}"
            )

    # Assemble context parts based on options
    context_parts: dict[str, Any] = {}

    # Add schema cheatsheet if enabled
    if options.include_schema_cheatsheet and schema_tree is not None:
        sliced_schema = slice_schema_for_targets(schema_tree, target_files)
        context_parts["schema_cheatsheet"] = sliced_schema

    # Add profile summary if enabled
    if options.include_profile_summary:
        profile_summary = {
            "stack": stack,
            "languages": profile.get("languages"),
            "frameworks": profile.get("frameworks"),
        }
        context_parts["profile_summary"] = profile_summary

    # Add other parts if enabled
    if options.include_symbols:
        context_parts["symbols"] = filtered_symbols

    if options.include_entrypoints:
        context_parts["entrypoints"] = filtered_entrypoints

    if options.include_seams:
        context_parts["seams"] = filtered_seams

    if options.include_exemplars:
        context_parts["exemplars"] = filtered_exemplars

    if options.include_memos:
        context_parts["memos"] = filtered_memos

    if options.include_code_snippets and root is not None:
        # Extract code snippets from filtered symbols
        code_snippets = extract_code_snippets(
            root=root,
            symbols=filtered_symbols,
            keyword_map=keyword_map,
            options=options,
        )
        context_parts["code_snippets"] = code_snippets

    if contracts_root is not None:
        try:
            from midicoder.contract.reference_loader import collect_reference_catalog

            context_parts["available_reference_ids"] = collect_reference_catalog(
                contracts_root
            )
        except Exception:
            context_parts["available_reference_ids"] = {}

    # Apply budget
    final_context, budget_trace = apply_budget(context_parts, budget, max_total)

    # Merge traces
    trace.top_k_results = budget_trace.top_k_results
    trace.estimated_tokens = budget_trace.estimated_tokens
    trace.items_dropped = budget_trace.items_dropped
    trace.budget_allocation = budget_trace.budget_allocation

    return final_context, trace


def build_context_for_contract_gen(
    root: Path,
    context_dir: Path,
    *,
    master_brief: str,
    target_files: list[str],
    schema_tree: dict[str, Any],
    cache_dir: Path,
    llm_config: Any | None = None,
    call_llm_func: Any | None = None,
    budget: dict[str, int] | None = None,
    max_total: int = MAX_TOTAL_BUDGET,
    contracts_root: Path | None = None,
) -> tuple[dict[str, Any], RetrievalTrace]:
    """
    Build context for contract generation using advanced retrieval system.

    This implements the stack-aware, budgeted, deterministic retrieval method
    as specified in technic/DSL/5-project-context-retrieval.md.

    Uses all context parts including:
    - Schema cheatsheet (sliced for target files)
    - Profile summary (technology stack info)
    - Filtered symbols, entrypoints, seams, exemplars
    - Project memos (learnings from previous repair cycles)
    - Code snippets (optional, disabled by default)

    Args:
        root: Project root path
        context_dir: Path to .midicoder/context directory
        master_brief: Content of master-brief.md
        target_files: List of target contract files for this batch
        schema_tree: Full schema tree from tree_v0.yml
        cache_dir: Version cache directory for keyword map
        llm_config: LLM configuration (required for keyword extraction)
        call_llm_func: Function to call LLM (required)
        budget: Custom budget allocation (optional)
        max_total: Maximum total token budget

    Returns:
        Tuple of (context dict, retrieval trace)

    Context dict includes:
        - schema_cheatsheet: Sliced schema for target files
        - profile_summary: Technology stack and language info
        - symbols: Filtered code symbols matching keywords
        - entrypoints: Application entrypoints (if relevant)
        - seams: Integration boundaries (if relevant)
        - exemplars: Code patterns and examples
        - memos: Project learnings and repair insights
    """
    # LLM configuration is required for contract generation
    if not llm_config or not call_llm_func:
        raise RuntimeError(
            "LLM configuration is required for contract generation. "
            "The advanced retrieval system needs LLM to analyze master brief and determine required contract files."
        )

    # Use default budget if not provided
    if budget is None:
        budget = DEFAULT_BUDGET

    # Keep generation conservative: schema + code context, but no repair memos.
    gen_options = ContextOptions(include_memos=False, include_code_snippets=False)

    return _build_context_core(
        context_dir=context_dir,
        master_brief=master_brief,
        target_files=target_files,
        llm_config=llm_config,
        call_llm_func=call_llm_func,
        cache_dir=cache_dir,
        budget=budget,
        max_total=max_total,
        schema_tree=schema_tree,
        options=gen_options,
        root=root,
        contracts_root=contracts_root,
    )


def build_context_for_contract_repair(
    root: Path,
    context_dir: Path,
    *,
    master_brief: str,
    feedback_items: Iterable[Any],
    schema_tree: dict[str, Any],
    cache_dir: Path,
    llm_config: Any | None = None,
    call_llm_func: Any | None = None,
    budget: dict[str, int] | None = None,
    max_total: int = MAX_TOTAL_BUDGET,  # Use full budget for repair (same as generation)
    contracts_root: Path | None = None,
) -> tuple[dict[str, Any], RetrievalTrace]:
    """
    Build context for contract repair using advanced retrieval system optimized for repair operations.

    This function emphasizes memos and learnings from previous repair cycles to inform current repairs.
    Uses repair-specific context options that prioritize:
    - Previous repair memos (higher allocation)
    - Schema compliance patterns
    - Essential project artifacts

    Key differences from contract generation:
    - Higher memo allocation (600 tokens vs 800 for generation)
    - Uses repair-optimized context options
    - Smaller overall budget focused on repair-relevant context
    - Emphasizes previous learnings to avoid repeat issues

    Args:
        root: Project root path
        context_dir: Path to .midicoder/context directory
        master_brief: Content of master-brief.md
        feedback_items: Iterable of feedback items requiring repair
        schema_tree: Full schema tree from tree_v0.yml (required)
        cache_dir: Version cache directory for keyword map
        llm_config: LLM configuration (required for keyword extraction)
        call_llm_func: Function to call LLM (required)
        budget: Custom budget allocation (optional, defaults to repair-optimized budget)
        max_total: Maximum total token budget (default: half of generation budget)

    Returns:
        Tuple of (context dict, retrieval trace)

        Context dict includes:
        - schema_cheatsheet: Sliced schema for files being repaired
        - profile_summary: Technology stack info
        - symbols: Code symbols relevant to feedback issues
        - memos: Previous repair insights and learnings (emphasized)
        - Other artifacts filtered by feedback relevance

    Raises:
        RuntimeError: If LLM configuration is not provided
    """
    # LLM configuration is required for contract repair
    if not llm_config or not call_llm_func:
        raise RuntimeError(
            "LLM configuration is required for contract repair. "
            "The advanced retrieval system needs LLM to analyze master brief and determine context."
        )

    # Determine target files from feedback items
    target_files = []
    for item in feedback_items:
        file_value = str(getattr(item, "file", "") or "")
        if file_value and file_value not in target_files:
            # Extract just the file part from "contracts/domain/entities.yaml" -> "domain/entities.yaml"
            if file_value.startswith("contracts/"):
                file_value = file_value[len("contracts/") :]
            target_files.append(file_value)

    # Use repair-specific budget if not provided (includes schema_cheatsheet)
    if budget is None:
        budget = {
            "schema_cheatsheet": 2000,  # Sliced schema for repair context (increased)
            "profile_summary": 200,
            "symbols": 800,  # Increased for better context
            "entrypoints": 400,
            "seams": 300,
            "exemplars": 500,  # Increased
            "memos": 800,  # Increased - Previous repair insights (important for repair)
            "code_snippets": 300,
        }

    # Contract repair uses repair-optimized context options (emphasizes memos)
    repair_options = create_repair_context_options()

    return _build_context_core(
        context_dir=context_dir,
        master_brief=master_brief,
        target_files=target_files,
        llm_config=llm_config,
        call_llm_func=call_llm_func,
        cache_dir=cache_dir,
        budget=budget,
        max_total=max_total,
        schema_tree=schema_tree,
        options=repair_options,  # Use repair-optimized options
        root=root,
        contracts_root=contracts_root,
    )
