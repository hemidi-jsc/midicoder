from __future__ import annotations

import json
from pathlib import Path

from midicoder.brief.analyzer import KEYWORD_CACHE_VERSION, get_keyword_map_cached
from midicoder.llm.client import LlmRequestError


def test_get_keyword_map_cached_migrates_legacy_cache_payload(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    legacy_payload = {
        "master_brief_hash": "abc123",
        "created_at": "2026-01-01T00:00:00+00:00",
        "keyword_map": {
            "domain_terms": ["billing"],
            "entities": ["Invoice"],
            "commands": ["CreateInvoice"],
            "events": [],
            "apis": [],
            "synonyms": {},
        },
        "contract_files": ["meta/info.yaml", "glossary.yaml"],
    }
    (cache_dir / "brief_keywords.json").write_text(
        json.dumps(legacy_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    master_brief = "billing brief"

    def _unused_llm(*args, **kwargs):  # pragma: no cover - cache hit path
        raise AssertionError("LLM should not be called for migrated cache hit")

    # Ensure hash matches cache hit path.
    import hashlib

    legacy_payload["master_brief_hash"] = hashlib.sha256(master_brief.encode("utf-8")).hexdigest()
    (cache_dir / "brief_keywords.json").write_text(
        json.dumps(legacy_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    keyword_map, cache_used = get_keyword_map_cached(
        cache_dir=cache_dir,
        master_brief_text=master_brief,
        llm_config={},
        call_llm_func=_unused_llm,
    )

    assert cache_used is True
    assert keyword_map.integrations == []
    assert keyword_map.access_control == []
    assert keyword_map.persistence == []
    assert keyword_map.scenarios == []

    migrated = json.loads((cache_dir / "brief_keywords.json").read_text(encoding="utf-8"))
    assert migrated["cache_version"] == KEYWORD_CACHE_VERSION


def test_get_keyword_map_cached_preserves_llm_request_error(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    def _raise_llm_error(*args, **kwargs):
        raise LlmRequestError("LLM network error: timeout")

    try:
        get_keyword_map_cached(
            cache_dir=cache_dir,
            master_brief_text="new brief",
            llm_config={},
            call_llm_func=_raise_llm_error,
            force_refresh=True,
        )
        assert False, "Expected LlmRequestError to propagate"
    except LlmRequestError as exc:
        assert "timeout" in str(exc).lower()
