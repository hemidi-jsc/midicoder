"""Master brief analysis and contract file determination."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

KEYWORD_CACHE_VERSION = 2


@dataclass
class KeywordMap:
    """Structured keywords extracted from master brief."""

    domain_terms: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    apis: list[str] = field(default_factory=list)
    integrations: list[str] = field(default_factory=list)
    access_control: list[str] = field(default_factory=list)
    persistence: list[str] = field(default_factory=list)
    scenarios: list[str] = field(default_factory=list)
    synonyms: dict[str, list[str]] = field(default_factory=dict)
    contract_files: list[str] = field(default_factory=list)

    def all_keywords(self) -> set[str]:
        """Get all keywords as a flat set."""
        keywords = set()
        keywords.update(self.domain_terms)
        keywords.update(self.entities)
        keywords.update(self.commands)
        keywords.update(self.events)
        keywords.update(self.apis)
        keywords.update(self.integrations)
        keywords.update(self.access_control)
        keywords.update(self.persistence)
        keywords.update(self.scenarios)
        for synonym_list in self.synonyms.values():
            keywords.update(synonym_list)
        return keywords


def _hash_master_brief(master_brief: str) -> str:
    """Generate stable hash for master brief content."""
    return hashlib.sha256(master_brief.encode("utf-8")).hexdigest()


def _keyword_cache_path(cache_dir: Path) -> Path:
    """Return the keyword cache file path."""
    return cache_dir / "brief_keywords.json"


def _keyword_map_payload(keyword_map: KeywordMap) -> dict[str, Any]:
    """Serialize KeywordMap into cache payload."""
    return {
        "domain_terms": keyword_map.domain_terms,
        "entities": keyword_map.entities,
        "commands": keyword_map.commands,
        "events": keyword_map.events,
        "apis": keyword_map.apis,
        "integrations": keyword_map.integrations,
        "access_control": keyword_map.access_control,
        "persistence": keyword_map.persistence,
        "scenarios": keyword_map.scenarios,
        "synonyms": keyword_map.synonyms,
    }


def _keyword_map_from_payload(
    payload: dict[str, Any], contract_files: list[str]
) -> KeywordMap:
    """Deserialize KeywordMap from cache payload."""
    return KeywordMap(
        domain_terms=payload.get("domain_terms", []),
        entities=payload.get("entities", []),
        commands=payload.get("commands", []),
        events=payload.get("events", []),
        apis=payload.get("apis", []),
        integrations=payload.get("integrations", []),
        access_control=payload.get("access_control", []),
        persistence=payload.get("persistence", []),
        scenarios=payload.get("scenarios", []),
        synonyms=payload.get("synonyms", {}),
        contract_files=contract_files,
    )


def load_keyword_cache(cache_dir: Path) -> dict[str, Any] | None:
    """Load keyword cache data from version cache directory."""
    cache_file = _keyword_cache_path(cache_dir)
    if not cache_file.exists():
        return None
    try:
        payload = json.loads(cache_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(payload, dict):
        return None
    required_keys = {"master_brief_hash", "created_at", "keyword_map", "contract_files"}
    if not required_keys.issubset(payload.keys()):
        return None
    if "cache_version" not in payload:
        payload["cache_version"] = 1
    if not isinstance(payload.get("cache_version"), int):
        return None
    return payload


def save_keyword_cache(
    cache_dir: Path, master_brief_hash: str, keyword_map: KeywordMap
) -> None:
    """Save keyword cache data into version cache directory."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = _keyword_cache_path(cache_dir)
    cache_payload = {
        "cache_version": KEYWORD_CACHE_VERSION,
        "master_brief_hash": master_brief_hash,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "keyword_map": _keyword_map_payload(keyword_map),
        "contract_files": keyword_map.contract_files,
    }
    cache_file.write_text(
        json.dumps(cache_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _migrate_keyword_cache_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Migrate legacy keyword cache payloads to current version in-memory.
    """
    migrated = dict(payload)
    version = int(migrated.get("cache_version", 1))
    if version >= KEYWORD_CACHE_VERSION:
        return migrated

    keyword_map = migrated.get("keyword_map")
    if not isinstance(keyword_map, dict):
        keyword_map = {}
    for key in ("integrations", "access_control", "persistence", "scenarios"):
        if key not in keyword_map or not isinstance(keyword_map.get(key), list):
            keyword_map[key] = []
    if not isinstance(keyword_map.get("synonyms"), dict):
        keyword_map["synonyms"] = {}

    if not isinstance(migrated.get("contract_files"), list):
        migrated["contract_files"] = []

    migrated["keyword_map"] = keyword_map
    migrated["cache_version"] = KEYWORD_CACHE_VERSION
    return migrated


def get_keyword_map_cached(
    cache_dir: Path,
    master_brief_text: str,
    llm_config: Any,
    call_llm_func: Callable,
    *,
    force_refresh: bool = False,
    run_dir: Path | None = None,
) -> tuple[KeywordMap, bool]:
    """
    Load keyword map from cache; refresh with LLM if missing or stale.

    Returns:
        Tuple of (KeywordMap, cache_used)
    """
    master_brief_hash = _hash_master_brief(master_brief_text)
    if not force_refresh:
        cached_data = load_keyword_cache(cache_dir)
        if cached_data and cached_data.get("master_brief_hash") == master_brief_hash:
            cache_version = int(cached_data.get("cache_version", 1))
            if cache_version < KEYWORD_CACHE_VERSION:
                print(
                    f"[brief analysis] Migrating keyword cache v{cache_version} -> v{KEYWORD_CACHE_VERSION}..."
                )
                cached_data = _migrate_keyword_cache_payload(cached_data)
                migrated_keyword_map = _keyword_map_from_payload(
                    cached_data.get("keyword_map", {}),
                    cached_data.get("contract_files", []),
                )
                save_keyword_cache(cache_dir, master_brief_hash, migrated_keyword_map)
            keyword_map_payload = cached_data.get("keyword_map", {})
            contract_files = cached_data.get("contract_files", [])
            keyword_map = _keyword_map_from_payload(keyword_map_payload, contract_files)
            print(
                f"[brief analysis] Using cached keyword map from {cached_data.get('created_at')}"
            )
            return keyword_map, True
        if cached_data:
            print("[brief analysis] Master brief changed, refreshing keyword cache...")

    print("[brief analysis] Calling LLM to analyze master brief...")
    keyword_map = extract_keywords_and_contracts_with_llm(
        master_brief_text,
        llm_config,
        call_llm_func,
        run_dir=run_dir,
    )
    save_keyword_cache(cache_dir, master_brief_hash, keyword_map)
    print("[brief analysis] Keyword cache updated: brief_keywords.json")
    return keyword_map, False


def _strip_code_fences(text: str) -> str:
    """Strip a single leading/trailing markdown code fence pair."""
    content = text.strip()
    if not content:
        return content
    if content.startswith("```"):
        lines = content.splitlines()
        if len(lines) >= 2:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()
    return content


def _parse_json_resilient(text: str) -> dict[str, Any]:
    """Parse JSON object with light recovery for noisy LLM outputs."""
    content = _strip_code_fences(text)
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for idx, char in enumerate(content):
            if char != "{":
                continue
            try:
                parsed, end = decoder.raw_decode(content[idx:])
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict) and not content[idx + end :].strip():
                data = parsed
                break
        else:
            raise
    if not isinstance(data, dict):
        raise ValueError("LLM output is not a JSON object")
    return data


def extract_keywords_and_contracts_with_llm(
    master_brief: str,
    llm_config: Any,
    call_llm_func: Callable,
    run_dir: Path | None = None,
) -> KeywordMap:
    """
    Extract structured keywords AND required contract files from master brief using LLM.

    This analyzes the brief and determines:
    1. Keywords for filtering (domain terms, entities, commands, etc.)
    2. Which contract files are needed based on the brief content

    Args:
        master_brief: Content of master brief
        llm_config: LLM configuration
        call_llm_func: Function to call LLM
        run_dir: Optional run directory to save prompts and request info

    Returns:
        KeywordMap with keywords and contract_files list

    Raises:
        RuntimeError: If LLM extraction fails
    """
    system_prompt = """You are an expert software architecture analyst specializing in Midicoder contract generation planning.

Your mission is to analyze project briefs and extract two critical pieces of information:
1. **Structured keywords** for intelligent context filtering during contract generation
2. **Required contract files** based on the brief's actual scope and functionality

## Contract File Structure Reference

Available contract files in the Midicoder DSL system:

**Always Required:**
- `meta/info.yaml` - Project metadata (always include)
- `glossary.yaml` - Domain terminology (always include)

**Domain Layer:**
- `domain/entities.yaml` - Domain entities/models (include if any business objects mentioned)
- `domain/value_objects.yaml` - Value objects (include if specific value types mentioned)
- `domain/errors.yaml` - Domain errors (include if error handling/validation mentioned)
- `domain/events.yaml` - Domain events (include ONLY if events explicitly mentioned)

**Application Layer:**
- `app/commands.yaml` - Commands/actions (include if any operations/actions mentioned)
- `app/queries.yaml` - Read operations (include if read/query operations mentioned)
- `app/projections.yaml` - Read-model projections (include if read models/projections/materialized views are mentioned)

**Business Rules:**
- `rules/rules.yaml` - Business rules/policies (include if business logic rules mentioned)

**Process Layer:**
- `workflows/workflows.yaml` - Multi-step processes (include if workflows/processes mentioned)

**Security Layer:**
- `policy/rbac.yaml` - Role-based access (include if permissions/roles mentioned)
- `policy/policies.yaml` - Business/security policy rules (include if policy conditions/effects are mentioned)
- `policy/security.yaml` - Security baseline policies (include if security hardening is required)
- `policy/reliability.yaml` - Reliability policies (include if timeout/retry/circuit breaker rules are needed)

**Infrastructure Layer:**
- `persistence/model.yaml` - Persistence layer (include if database/storage patterns mentioned)
- `api/http.yaml` - HTTP APIs (include if REST APIs/HTTP endpoints mentioned)
- `api/graphql.yaml` - GraphQL APIs (include if GraphQL schema/query/mutation is mentioned)
- `integrations/integrations.yaml` - Third-party integrations (include if external services are mentioned)
- `ops/observability.yaml` - Logging/metrics/trace configuration (include if monitoring requirements are mentioned)

**Testing Layer:**
- `scenarios/scenarios.yaml` - Use cases/scenarios (include if testing scenarios mentioned)
- `testing/tests.yaml` - Contract-level test definitions (include if test automation scope is mentioned)

**Operations Layer:**
- `meta/profiles.yaml` - Environment profiles (include if local/dev/staging/prod differences are described)
- `meta/secrets.yaml` - Secret references (include if credentials/keys are needed)

## Analysis Guidelines

**Keyword Extraction Strategy:**
- Extract specific domain terms, not generic words
- Identify actual entity names (User, Order, Product) not generic terms
- Capture command verbs (Create, Update, Delete, Process, Send)
- Note integration services (Stripe, SendGrid, AWS)
- Include API route patterns (/users, /orders, /api/v1/*)

**Contract File Decision Logic:**
- **Conservative approach**: Only include files that are clearly needed
- **Evidence-based**: Require explicit mention or strong implication
- **Domain entities**: Include entities.yaml if any business objects are described
- **Commands**: Include commands.yaml if any actions/operations are described
- **APIs**: Include api/http.yaml if REST/HTTP endpoints are mentioned
- **Events**: Include events.yaml ONLY if event-driven patterns are explicitly described
- **Errors**: Include errors.yaml if validation, error handling, or failure cases mentioned
- **Integrations**: Include integrations/integrations.yaml if AWS/S3/SMTP/OAuth2/webhooks/external APIs are mentioned
- **Ownership permissions**: If brief implies "own_*" access (e.g., "view own payroll"), include BOTH `policy/rbac.yaml` and `policy/policies.yaml` so ownership conditions can be expressed explicitly

## Expected Output Format

Return ONLY a valid JSON object with these exact keys:

```json
{
  "domain_terms": ["user", "subscription", "billing", "payment", "plan"],
  "entities": ["User", "Subscription", "Plan", "Payment", "Invoice"],
  "commands": ["CreateUser", "SubscribeUser", "ProcessPayment", "CancelSubscription"],
  "events": ["UserCreated", "SubscriptionActivated", "PaymentProcessed"],
  "apis": ["/api/users", "/api/subscriptions", "/api/payments"],
  "integrations": ["Stripe", "SendGrid", "Slack"],
  "access_control": ["role", "permission", "rbac", "authorization"],
  "persistence": ["table", "datasource", "postgres", "redis"],
  "scenarios": ["happy_path_checkout", "refund_flow"],
  "synonyms": {
    "user": ["customer", "member", "subscriber"],
    "payment": ["transaction", "billing", "charge"],
    "plan": ["tier", "package", "subscription"]
  },
  "contract_files": [
    "meta/info.yaml",
    "glossary.yaml",
    "domain/entities.yaml",
    "domain/errors.yaml",
    "app/commands.yaml",
    "api/http.yaml"
  ]
}
```

## Decision Examples

**Example 1 - Simple CRUD API:**
Brief: "User management with basic CRUD operations"
→ Files: meta/info.yaml, glossary.yaml, domain/entities.yaml, app/commands.yaml, api/http.yaml

**Example 2 - Event-Driven System:**
Brief: "Order processing with events: OrderPlaced → PaymentProcessed → OrderShipped"
→ Files: meta/info.yaml, glossary.yaml, domain/entities.yaml, domain/events.yaml, app/commands.yaml, workflows/workflows.yaml

**Example 3 - Minimal API:**
Brief: "Simple calculator API with basic math operations"
→ Files: meta/info.yaml, glossary.yaml, api/http.yaml

## Critical Rules

✅ **Always include:** meta/info.yaml and glossary.yaml
✅ **Evidence-based inclusion:** Only include files with clear justification from the brief
✅ **Conservative approach:** When in doubt, exclude optional files
❌ **Never guess:** Don't include files based on assumptions
❌ **No explanations:** Return only the JSON object, no commentary

Analyze the brief thoroughly and make evidence-based decisions about which contract files are actually needed."""

    user_prompt = f"Analyze this project brief and extract keywords + required contract files:\n\n{master_brief}"

    # Save prompts to run_dir if provided
    if run_dir:
        # Save system prompt
        (run_dir / "prompt_system.txt").write_text(system_prompt, encoding="utf-8")

        # Save user prompt
        (run_dir / "prompt_user.txt").write_text(user_prompt, encoding="utf-8")

        # Save full request info
        request_info = {
            "model": llm_config.model if hasattr(llm_config, "model") else "unknown",
            "base_url": (
                llm_config.base_url if hasattr(llm_config, "base_url") else "unknown"
            ),
            "provider": (
                llm_config.provider if hasattr(llm_config, "provider") else None
            ),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        (run_dir / "llm_request.json").write_text(
            json.dumps(request_info, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    try:
        response = call_llm_func(
            llm_config,
            system=system_prompt,
            prompt=user_prompt,
        )

        data = _parse_json_resilient(response.content)

        # Validate contract_files
        contract_files = data.get("contract_files", [])
        if not contract_files:
            raise ValueError("LLM did not return contract_files list")

        # Ensure meta/info.yaml and glossary.yaml are always included
        if "meta/info.yaml" not in contract_files:
            contract_files.insert(0, "meta/info.yaml")
        if "glossary.yaml" not in contract_files:
            contract_files.insert(1, "glossary.yaml")

        return KeywordMap(
            domain_terms=data.get("domain_terms", []),
            entities=data.get("entities", []),
            commands=data.get("commands", []),
            events=data.get("events", []),
            apis=data.get("apis", []),
            integrations=data.get("integrations", []),
            access_control=data.get("access_control", []),
            persistence=data.get("persistence", []),
            scenarios=data.get("scenarios", []),
            synonyms=data.get("synonyms", {}),
            contract_files=contract_files,
        )
    except Exception as exc:
        # No fallback - raise error
        preview = ""
        if "response" in locals() and hasattr(response, "content"):
            preview = _strip_code_fences(str(response.content))[:300]
        raise RuntimeError(
            "Failed to extract keywords and contract files from master brief using LLM: "
            f"{exc}. Response preview: {preview!r}"
        ) from exc


def get_contract_files_from_master_brief(
    paths: Any,
    version: str,
    master_brief_text: str,
    llm_config: Any,
    call_llm_func: Any,
    force_refresh: bool = False,
    run_dir: Any = None,
) -> tuple[list[str], dict[str, Any]]:
    """
    Extract required contract files and keywords from master brief using LLM analysis.
    Uses caching to avoid duplicate LLM calls across commands.

    Args:
        paths: MidicoderPaths for file operations
        version: Current version string
        master_brief_text: Content of master brief
        llm_config: LLM configuration
        call_llm_func: Function to call LLM
        force_refresh: If True, ignore cache and call LLM again
        run_dir: Optional run directory to save prompts and request info

    Returns:
        Tuple of (contract_files, keyword_data)
    """
    cache_dir = paths.versions / str(version) / "cache"
    try:
        keyword_map, _ = get_keyword_map_cached(
            cache_dir=cache_dir,
            master_brief_text=master_brief_text,
            llm_config=llm_config,
            call_llm_func=call_llm_func,
            force_refresh=force_refresh,
            run_dir=run_dir,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to determine required contract files from master brief: {exc}"
        ) from exc

    keyword_data = {
        "domain_terms": keyword_map.domain_terms,
        "entities": keyword_map.entities,
        "commands": keyword_map.commands,
        "events": keyword_map.events,
        "apis": keyword_map.apis,
        "integrations": keyword_map.integrations,
        "access_control": keyword_map.access_control,
        "persistence": keyword_map.persistence,
        "scenarios": keyword_map.scenarios,
        "synonyms": keyword_map.synonyms,
    }

    return keyword_map.contract_files, keyword_data


def refresh_contract_analysis(
    paths: Any,
    version: str,
    master_brief_text: str,
    llm_config: Any,
    call_llm_func: Any,
    run_dir: Any = None,
) -> tuple[list[str], dict[str, Any]]:
    """
    Force refresh the cached contract analysis by re-analyzing the master brief.

    Args:
        paths: MidicoderPaths for file operations
        version: Current version string
        master_brief_text: Content of master brief
        llm_config: LLM configuration
        call_llm_func: Function to call LLM
        run_dir: Optional run directory to save prompts and request info

    Returns:
        Tuple of (contract_files, keyword_data)
    """
    print("[brief analysis] Force refreshing contract analysis cache...")

    return get_contract_files_from_master_brief(
        paths,
        version,
        master_brief_text,
        llm_config,
        call_llm_func,
        force_refresh=True,
        run_dir=run_dir,
    )


def save_keyword_extraction_result(run_dir: Path, keyword_data: dict[str, Any]) -> None:
    """
    Save keyword extraction result to run directory for reference.

    Args:
        run_dir: Run directory path
        keyword_data: Extracted keywords and metadata
    """
    (run_dir / "keyword_extraction.json").write_text(
        json.dumps(keyword_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def print_analysis_summary(
    contract_files: list[str], keyword_data: dict[str, Any]
) -> None:
    """
    Print summary of contract analysis results.

    Args:
        contract_files: List of determined contract files
        keyword_data: Extracted keywords
    """
    print(
        f"[brief analysis] Analysis complete - {len(contract_files)} contract files determined"
    )
    print(f"[brief analysis] Files: {', '.join(contract_files)}")

    # Show keyword summary
    entities = keyword_data.get("entities", [])
    commands = keyword_data.get("commands", [])
    apis = keyword_data.get("apis", [])

    if entities:
        print(
            f"[brief analysis] Entities: {', '.join(entities[:5])}{'...' if len(entities) > 5 else ''}"
        )
    if commands:
        print(
            f"[brief analysis] Commands: {', '.join(commands[:5])}{'...' if len(commands) > 5 else ''}"
        )
    if apis:
        print(
            f"[brief analysis] APIs: {', '.join(apis[:3])}{'...' if len(apis) > 3 else ''}"
        )


def get_cache_info(paths: Any, version: str) -> dict[str, Any] | None:
    """
    Get information about cached analysis if it exists.

    Args:
        paths: MidicoderPaths for file operations
        version: Current version string

    Returns:
        Cache info dict or None if no cache exists
    """
    cache_dir = paths.versions / str(version) / "cache"
    if not cache_dir.exists():
        return None

    cache_file = _keyword_cache_path(cache_dir)
    if not cache_file.exists():
        return None
    try:
        cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception:
        return None
    return {
        "file": cache_file.name,
        "cache_version": cache_data.get("cache_version", 1),
        "created_at": cache_data.get("created_at"),
        "contract_files_count": len(cache_data.get("contract_files", [])),
        "master_brief_hash": cache_data.get("master_brief_hash"),
    }


def clear_analysis_cache(paths: Any, version: str) -> int:
    """
    Clear all cached analysis files for a version.

    Args:
        paths: MidicoderPaths for file operations
        version: Current version string

    Returns:
        Number of cache files deleted
    """
    cache_dir = paths.versions / str(version) / "cache"
    if not cache_dir.exists():
        return 0

    cache_files = list(cache_dir.glob("contract_analysis_*.json"))
    cache_files.append(_keyword_cache_path(cache_dir))
    count = 0

    for cache_file in cache_files:
        try:
            if cache_file.exists():
                cache_file.unlink()
                count += 1
        except Exception as exc:
            print(
                f"[brief analysis] Warning: Failed to delete {cache_file.name}: {exc}"
            )

    return count
