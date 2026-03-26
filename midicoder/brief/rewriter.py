"""Master brief rewriter using LLM to improve master-brief.md structure and content."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from midicoder.brief import MASTER_BRIEF_TEMPLATE
from midicoder.llm.client import LlmConfig, call_llm

MAX_SNIPPET_TOKENS = 1000
MAX_TOTAL_SNIPPET_TOKENS = 4000
SNIPPET_CONTEXT_LINES = 5


@dataclass
class SnippetBlock:
    file: str
    begin_line: int | None
    end_line: int | None
    group_id: str | None
    kind: str | None
    detail: str | None
    source: str
    snippet: str
    symbol: str | None = None


def _estimate_tokens(text: str) -> int:
    return len(text) // 4


def _truncate_to_token_budget(text: str, max_tokens: int) -> str:
    if _estimate_tokens(text) <= max_tokens:
        return text
    max_chars = max_tokens * 4
    return text[:max_chars].rstrip() + "..."


def _load_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _load_virtual_seams(context_dir: Path) -> list[dict[str, Any]]:
    return _load_json_list(context_dir / "virtual_seams.json")


def _load_real_seams(context_dir: Path) -> list[dict[str, Any]]:
    return _load_json_list(context_dir / "seams.json")


def _build_symbol_name_index(symbols: list[dict[str, Any]]) -> dict[str, list[str]]:
    names_by_file: dict[str, list[str]] = {}
    for symbol in symbols:
        file_path = str(symbol.get("file", "")).strip()
        name = str(symbol.get("name", "")).strip()
        if not file_path or not name:
            continue
        names_by_file.setdefault(file_path, []).append(name.lower())
    return names_by_file


def _keyword_match(text: str, keywords: set[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _filter_seams(
    seams: list[dict[str, Any]],
    keywords: set[str],
    symbol_names_by_file: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    if not seams:
        return []
    if not keywords:
        return seams
    filtered: list[dict[str, Any]] = []
    for seam in seams:
        file_path = str(seam.get("file", "")).strip()
        group_id = str(seam.get("group_id", "")).lower()
        detail = str(seam.get("detail", "")).lower()
        symbol_names = (symbol_names_by_file or {}).get(file_path, [])
        symbol_match = any(_keyword_match(name, keywords) for name in symbol_names)
        if (
            _keyword_match(file_path.lower(), keywords)
            or _keyword_match(group_id, keywords)
            or _keyword_match(detail, keywords)
            or symbol_match
        ):
            filtered.append(seam)
    return filtered


def _extract_block_snippet(
    repo_root: Path,
    file_path: str,
    begin_line: int | None,
    end_line: int | None,
) -> str | None:
    absolute_path = repo_root / file_path
    if not absolute_path.exists():
        return None
    try:
        lines = absolute_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    if begin_line is None:
        return None
    begin_index = max(begin_line - 1, 0)
    if end_line is None or end_line < begin_line:
        start = max(begin_index - SNIPPET_CONTEXT_LINES, 0)
        end = min(begin_index + SNIPPET_CONTEXT_LINES + 1, len(lines))
    else:
        start = begin_index
        end = min(end_line, len(lines))
    snippet = "\n".join(lines[start:end]).strip()
    return snippet or None


def _coerce_line(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _extract_line_snippet(
    repo_root: Path,
    file_path: str,
    line: int | None,
) -> str | None:
    if not line:
        return None
    return _extract_block_snippet(repo_root, file_path, line, None)


def _collect_virtual_seam_snippets(
    repo_root: Path,
    seams: list[dict[str, Any]],
) -> list[SnippetBlock]:
    blocks: list[SnippetBlock] = []
    for seam in seams:
        file_path = str(seam.get("file", "")).strip()
        if not file_path:
            continue
        begin_line = _coerce_line(seam.get("begin_line"))
        end_line = _coerce_line(seam.get("end_line"))
        if begin_line is None:
            begin_line = _coerce_line(seam.get("line"))
        snippet = _extract_block_snippet(repo_root, file_path, begin_line, end_line)
        if not snippet:
            continue
        blocks.append(
            SnippetBlock(
                file=file_path,
                begin_line=begin_line,
                end_line=end_line,
                group_id=str(seam.get("group_id") or "") or None,
                kind=str(seam.get("kind") or "") or None,
                detail=str(seam.get("detail") or "") or None,
                source="virtual_seam",
                snippet=snippet,
            )
        )
    return blocks


def _collect_symbol_snippets(
    repo_root: Path,
    symbols: list[dict[str, Any]],
) -> list[SnippetBlock]:
    blocks: list[SnippetBlock] = []
    from midicoder.context.virtual_seams.bounds import resolve_block_bounds_for_symbol

    for symbol in symbols:
        file_path = str(symbol.get("file", "")).strip()
        if not file_path:
            continue
        line = _coerce_line(symbol.get("line"))
        begin_line, end_line = resolve_block_bounds_for_symbol(repo_root, symbol)
        if begin_line is None:
            begin_line = line
        snippet = _extract_block_snippet(repo_root, file_path, begin_line, end_line) or _extract_line_snippet(
            repo_root, file_path, line
        )
        if not snippet:
            continue
        blocks.append(
            SnippetBlock(
                file=file_path,
                begin_line=begin_line,
                end_line=end_line,
                group_id=None,
                kind=str(symbol.get("kind") or "") or None,
                detail=None,
                source="symbol",
                symbol=str(symbol.get("name") or "") or None,
                snippet=snippet,
            )
        )
    return blocks


def _collect_exemplar_snippets(
    repo_root: Path,
    exemplars: list[dict[str, Any]],
) -> list[SnippetBlock]:
    blocks: list[SnippetBlock] = []
    from midicoder.context.virtual_seams.bounds import resolve_block_bounds_for_exemplar

    for exemplar in exemplars:
        file_path = str(exemplar.get("file", "")).strip()
        if not file_path:
            continue
        snippet = str(exemplar.get("snippet") or "").strip()
        begin_line = None
        end_line = None
        if not snippet:
            line = _coerce_line(exemplar.get("line"))
            begin_line, end_line = resolve_block_bounds_for_exemplar(repo_root, exemplar)
            if begin_line is None:
                begin_line = line
            snippet = (
                _extract_block_snippet(repo_root, file_path, begin_line, end_line)
                or _extract_line_snippet(repo_root, file_path, line)
                or ""
            )
        if not snippet:
            continue
        blocks.append(
            SnippetBlock(
                file=file_path,
                begin_line=begin_line,
                end_line=end_line,
                group_id=None,
                kind=str(exemplar.get("kind") or "") or None,
                detail=None,
                source="exemplar",
                symbol=str(exemplar.get("source_symbol") or "") or None,
                snippet=snippet,
            )
        )
    return blocks


def _collect_real_seam_snippets(
    repo_root: Path,
    seams: list[dict[str, Any]],
) -> list[SnippetBlock]:
    by_file_group: dict[tuple[str, str], dict[str, int]] = {}
    for seam in seams:
        file_path = str(seam.get("file", "")).strip()
        group_id = str(seam.get("group_id", "")).strip()
        kind = str(seam.get("kind", "")).strip().lower()
        line = _coerce_line(seam.get("line"))
        if not file_path or not group_id or not line:
            continue
        key = (file_path, group_id)
        slot = by_file_group.setdefault(key, {})
        if kind == "begin" and "begin" not in slot:
            slot["begin"] = line
        elif kind == "end" and "end" not in slot:
            slot["end"] = line

    blocks: list[SnippetBlock] = []
    for (file_path, group_id), bounds in by_file_group.items():
        begin_line = bounds.get("begin")
        end_line = bounds.get("end")
        if begin_line is None:
            continue
        range_start = begin_line + 1 if end_line and end_line > begin_line else begin_line
        range_end = (end_line - 1) if end_line and end_line > begin_line else None
        snippet = _extract_block_snippet(repo_root, file_path, range_start, range_end)
        if not snippet:
            continue
        blocks.append(
            SnippetBlock(
                file=file_path,
                begin_line=range_start,
                end_line=range_end,
                group_id=group_id,
                kind="seam",
                detail=None,
                source="seam",
                snippet=snippet,
            )
        )
    return blocks


def _truncate_snippets(snippets: list[SnippetBlock]) -> list[SnippetBlock]:
    total_tokens = 0
    trimmed: list[SnippetBlock] = []
    for block in snippets:
        block.snippet = _truncate_to_token_budget(block.snippet, MAX_SNIPPET_TOKENS)
        block_tokens = _estimate_tokens(block.snippet)
        if total_tokens + block_tokens > MAX_TOTAL_SNIPPET_TOKENS:
            break
        total_tokens += block_tokens
        trimmed.append(block)
    return trimmed


def _strip_code_fences(text: str) -> str:
    content = text.strip()
    if not content:
        return content
    # Remove a leading markdown code fence like ``` or ```json.
    content = re.sub(r"^\s*```[a-zA-Z0-9_-]*\s*\n", "", content)
    # Remove a trailing markdown code fence if the model appends one.
    content = re.sub(r"\n\s*```\s*$", "", content)
    return content


def _parse_llm_json(text: str, pass_name: str) -> Any:
    content = _strip_code_fences(text)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for idx, char in enumerate(content):
            if char not in "[{":
                continue
            try:
                parsed, end = decoder.raw_decode(content[idx:])
            except json.JSONDecodeError:
                continue
            if not content[idx + end :].strip():
                return parsed
        raise RuntimeError(f"{pass_name} JSON parse failed: unable to recover valid JSON")


def _build_rewrite_system_prompt() -> str:
    """Build system prompt for master brief rewriting."""

    git_marker_block = "\n".join([
        "<<<<<<< ORIGINAL",
        "[exact text from original file]",
        "=======",
        "[corrected text]",
        ">>>>>>> UPDATED"
    ])

    return f"""You are an expert technical documentation analyst, specializing in Master Briefs for software projects following the Midicoder DSL standard.

## Your Task

Analyze the user's master-brief.md and provide **targeted corrections** only:

1. **Identify issues**:
   - Structural problems (missing sections, wrong section names)
   - Unclear or ambiguous descriptions
   - Missing important details for mapping to contract files
   - Inconsistent terminology or formatting

2. **Provide fixes** in SEARCH/REPLACE format:
   - DO NOT rewrite the entire file
   - DO NOT add new business logic or fabricated information
   - ONLY fix what is actually wrong or unclear
   - Keep changes minimal and focused

## Important Principles

- **PRESERVE THE ORIGINAL LANGUAGE** - Use the same language (Vietnamese, English, etc.) as the original
- Keep original names for projects, entities, commands, API endpoints
- Only suggest changes that improve clarity, structure, or completeness based on the provided code context summaries
- If something is already good, do NOT change it

## Output Format

Return your response in this EXACT format:

```
# Brief Rewrite Analysis

## Summary
- Overall quality: [Good/Needs Improvement/Poor]
- Main issues: [brief list]
- Sections needing attention: [list section numbers]

## Recommended Changes

[If no changes needed, write "No changes recommended - the brief is well-structured."]

[Otherwise, provide SEARCH/REPLACE blocks:]

{git_marker_block}

[Repeat for each change]
```

**Critical Rules**:
- Each ORIGINAL block must match EXACTLY the text in the user's file (including whitespace)
- Only include changes that fix real problems
- Do NOT output the entire file content
- Use the same language as the original content"""


def _build_rewrite_prompt(original_content: str, module_narratives: list[dict[str, Any]]) -> str:
    """Build the prompt for master brief rewriting."""
    return f"""# Master Brief Review Request

## Standard Midicoder Template (reference)

```markdown
{MASTER_BRIEF_TEMPLATE}
```

## User's Current Master Brief

```markdown
{original_content}
```

## Module Narratives (from code context)

```json
{json.dumps(module_narratives, indent=2, ensure_ascii=False)}
```

## Instructions

1. Compare the user's brief against the Midicoder template
2. Identify structural issues, unclear descriptions, or missing mappings
3. Provide SEARCH/REPLACE blocks to fix these issues
4. Keep changes minimal - only fix what needs fixing
5. Use the same language as the original content

**Remember**: Output the analysis summary + SEARCH/REPLACE blocks, NOT the entire rewritten file."""


def _build_context_summary_system_prompt() -> str:
    return """You are a code summarization assistant.

Summarize each code snippet block into a concise description and list subfunctions.
Return ONLY valid JSON (no markdown, no commentary) matching this schema:

[
  {
    "symbol": "string",
    "file": "string",
    "summary": "string",
    "subfunctions": ["string"]
  }
]
"""


def _build_context_summary_prompt(snippets: list[SnippetBlock]) -> str:
    payload = [
        {
            "symbol": block.symbol or block.group_id or block.detail or "",
            "file": block.file,
            "begin_line": block.begin_line,
            "end_line": block.end_line,
            "source": block.source,
            "snippet": block.snippet,
        }
        for block in snippets
    ]
    return (
        "Summarize the following code snippets into the required JSON schema:\n\n"
        f"{json.dumps(payload, indent=2, ensure_ascii=False)}"
    )


def _build_module_narratives_system_prompt() -> str:
    return """You are a code synthesis assistant.

Aggregate block summaries into module/function narratives.
Return ONLY valid JSON (no markdown, no commentary) matching this schema:

[
  {
    "module": "string",
    "functions": [
      {
        "name": "string",
        "full_description": "string"
      }
    ]
  }
]
"""


def _build_module_narratives_prompt(context_summaries: list[dict[str, Any]]) -> str:
    return (
        "Aggregate these context summaries into module narratives:\n\n"
        f"{json.dumps(context_summaries, indent=2, ensure_ascii=False)}"
    )


def _parse_search_replace_blocks(llm_response: str) -> list[tuple[str, str]]:
    """
    Parse SEARCH/REPLACE blocks from LLM response.
    
    Returns:
        List of (original_text, updated_text) tuples
    """
    blocks = []
    
    # Pattern to match SEARCH/REPLACE blocks
    pattern = r'<<<<<<< ORIGINAL\s*\n(.*?)\n=======\s*\n(.*?)\n>>>>>>> UPDATED'
    
    matches = re.finditer(pattern, llm_response, re.DOTALL)
    
    for match in matches:
        original = match.group(1)
        updated = match.group(2)
        blocks.append((original, updated))
    
    return blocks


def _apply_search_replace_blocks(
    original_content: str,
    blocks: list[tuple[str, str]],
) -> tuple[str, list[str]]:
    """
    Apply SEARCH/REPLACE blocks to original content.
    
    Returns:
        Tuple of (updated_content, list_of_errors)
    """
    content = original_content
    errors = []
    applied_count = 0
    
    for i, (search_text, replace_text) in enumerate(blocks, 1):
        # Try to find the search text
        if search_text in content:
            content = content.replace(search_text, replace_text, 1)
            applied_count += 1
        else:
            # Try with normalized whitespace
            normalized_search = ' '.join(search_text.split())
            normalized_content = ' '.join(content.split())
            
            if normalized_search in normalized_content:
                errors.append(
                    f"Block {i}: Found with whitespace differences. "
                    f"Original text might have been modified. Skipping."
                )
            else:
                errors.append(
                    f"Block {i}: Search text not found in original content. "
                    f"First 50 chars: {search_text[:50]}..."
                )
    
    if applied_count > 0:
        print(f"[brief rewrite] OK Applied {applied_count}/{len(blocks)} change blocks")
    
    if errors:
        print(f"[brief rewrite] WARN {len(errors)} blocks could not be applied (see errors.txt)")
    
    return content, errors


def rewrite_master_brief(
    *,
    original_content: str,
    llm_config: LlmConfig,
    run_dir: Path | None = None,
    repo_root: Path,
    context_dir: Path,
    cache_dir: Path,
) -> tuple[str, str, list[str], list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Rewrite master brief using multi-pass LLM with context snippets.

    Args:
        original_content: Original master-brief.md content
        llm_config: LLM configuration
        run_dir: Optional run directory to save prompts and request info
        repo_root: Repository root path for snippet extraction
        context_dir: Path to .midicoder/context directory
        cache_dir: Version cache directory for keyword map

    Returns:
        Tuple of (rewritten_content, llm_response, errors, context_summaries, module_narratives)
    """
    print("[brief rewrite] Building keyword map and context snippets...")

    from midicoder.brief.analyzer import get_keyword_map_cached
    from midicoder.llm.context_builder import filter_exemplars, filter_symbols

    keyword_map, cache_used = get_keyword_map_cached(
        cache_dir=cache_dir,
        master_brief_text=original_content,
        llm_config=llm_config,
        call_llm_func=call_llm,
        run_dir=run_dir,
    )

    if run_dir:
        (run_dir / "keyword_cache_used.json").write_text(
            json.dumps(
                {
                    "cache_used": cache_used,
                    "keyword_map": {
                        "domain_terms": keyword_map.domain_terms,
                        "entities": keyword_map.entities,
                        "commands": keyword_map.commands,
                        "events": keyword_map.events,
                        "apis": keyword_map.apis,
                        "integrations": keyword_map.integrations,
                        "synonyms": keyword_map.synonyms,
                    },
                    "contract_files": keyword_map.contract_files,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    keywords = {kw.lower() for kw in keyword_map.all_keywords() if kw}
    symbols = _load_json_list(context_dir / "symbols.json")
    symbol_names_by_file = _build_symbol_name_index(symbols)

    virtual_seams = _load_virtual_seams(context_dir)
    if not virtual_seams:
        print("[brief rewrite] WARN virtual_seams.json missing or empty; falling back to seams/symbols/exemplars.")
    filtered_virtual_seams = _filter_seams(virtual_seams, keywords, symbol_names_by_file)
    seam_snippets = _collect_virtual_seam_snippets(repo_root, filtered_virtual_seams)

    snippets: list[SnippetBlock] = seam_snippets

    if not snippets:
        real_seams = _load_real_seams(context_dir)
        filtered_real_seams = _filter_seams(real_seams, keywords, symbol_names_by_file)
        snippets = _collect_real_seam_snippets(repo_root, filtered_real_seams)

    if not snippets:
        exemplars = _load_json_list(context_dir / "exemplars.json")
        filtered_symbols = filter_symbols(symbols, keyword_map, top_k=20, min_score=2.0)
        filtered_exemplars = filter_exemplars(exemplars, keyword_map, semantic_groups=[], top_k=15, min_score=2.0)
        snippets = _collect_symbol_snippets(repo_root, filtered_symbols) + _collect_exemplar_snippets(
            repo_root, filtered_exemplars
        )

    snippets = _truncate_snippets(snippets)
    if not snippets:
        print("[brief rewrite] WARN No snippets available for context summarization.")

    print("[brief rewrite] Running multi-pass rewrite...")

    if not snippets:
        context_summaries: list[dict[str, Any]] = []
        module_narratives: list[dict[str, Any]] = []
        if run_dir:
            (run_dir / "pass1_prompt_user.txt").write_text("No snippets available.", encoding="utf-8")
            (run_dir / "pass1_llm_response.txt").write_text("[]", encoding="utf-8")
            (run_dir / "pass2_prompt_user.txt").write_text("No context summaries available.", encoding="utf-8")
            (run_dir / "pass2_llm_response.txt").write_text("[]", encoding="utf-8")
    else:
        # Pass 1: Summarize blocks
        pass1_system = _build_context_summary_system_prompt()
        pass1_prompt = _build_context_summary_prompt(snippets)
        if run_dir:
            (run_dir / "pass1_prompt_system.txt").write_text(pass1_system, encoding="utf-8")
            (run_dir / "pass1_prompt_user.txt").write_text(pass1_prompt, encoding="utf-8")
        pass1_response = call_llm(
            llm_config,
            system=pass1_system,
            prompt=pass1_prompt,
            temperature=0.2,
            max_tokens=8000,
        )
        pass1_text = _strip_code_fences(pass1_response.content)
        if run_dir:
            (run_dir / "pass1_llm_response.txt").write_text(pass1_text, encoding="utf-8")
        try:
            context_summaries = _parse_llm_json(pass1_response.content, "Pass 1")
        except RuntimeError as exc:
            raise RuntimeError(str(exc)) from exc

        # Pass 2: Aggregate modules
        pass2_system = _build_module_narratives_system_prompt()
        pass2_prompt = _build_module_narratives_prompt(context_summaries)
        if run_dir:
            (run_dir / "pass2_prompt_system.txt").write_text(pass2_system, encoding="utf-8")
            (run_dir / "pass2_prompt_user.txt").write_text(pass2_prompt, encoding="utf-8")
        pass2_response = call_llm(
            llm_config,
            system=pass2_system,
            prompt=pass2_prompt,
            temperature=0.2,
            max_tokens=8000,
        )
        pass2_text = _strip_code_fences(pass2_response.content)
        if run_dir:
            (run_dir / "pass2_llm_response.txt").write_text(pass2_text, encoding="utf-8")
        try:
            module_narratives = _parse_llm_json(pass2_response.content, "Pass 2")
        except RuntimeError as exc:
            raise RuntimeError(str(exc)) from exc

    if run_dir:
        (run_dir / "context_summaries.json").write_text(
            json.dumps(context_summaries, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (run_dir / "module_narratives.json").write_text(
            json.dumps(module_narratives, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # Pass 3: Rewrite brief with narratives
    system_prompt = _build_rewrite_system_prompt()
    prompt = _build_rewrite_prompt(original_content, module_narratives)

    if run_dir:
        request_info = {
            "model": llm_config.model,
            "base_url": llm_config.base_url,
            "provider": llm_config.provider,
            "temperature": 0.2,
            "max_tokens": 16000,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        }
        (run_dir / "prompt_system.txt").write_text(system_prompt, encoding="utf-8")
        (run_dir / "prompt_user.txt").write_text(prompt, encoding="utf-8")
        (run_dir / "llm_request.json").write_text(
            json.dumps(request_info, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    response = call_llm(
        llm_config,
        system=system_prompt,
        prompt=prompt,
        temperature=0.2,
        max_tokens=16000,
    )

    llm_response = response.content.strip()
    if run_dir:
        (run_dir / "llm_response.txt").write_text(llm_response, encoding="utf-8")

    blocks = _parse_search_replace_blocks(llm_response)

    if not blocks:
        print("[brief rewrite] INFO No changes recommended by LLM")
        return original_content, llm_response, [], context_summaries, module_narratives

    print(f"[brief rewrite] Found {len(blocks)} suggested changes")
    rewritten_content, errors = _apply_search_replace_blocks(original_content, blocks)

    return rewritten_content, llm_response, errors, context_summaries, module_narratives


def save_rewritten_master_brief(
    version_root: Path,
    rewritten_content: str,
    llm_response: str,
    errors: list[str],
) -> Path:
    """
    Save rewritten master brief to master-brief.updated.md.
    
    Args:
        version_root: Path to version directory
        rewritten_content: Rewritten content
        llm_response: Raw LLM response with analysis
        errors: List of errors during applying changes
        
    Returns:
        Path to the created file
    """
    output_path = version_root / "master-brief.updated.md"
    output_path.write_text(rewritten_content, encoding="utf-8")
    
    # Save LLM analysis separately
    analysis_path = version_root / "master-brief.analysis.md"
    analysis_path.write_text(llm_response, encoding="utf-8")
    
    # Save errors if any
    if errors:
        errors_path = version_root / "master-brief.errors.txt"
        errors_path.write_text("\n\n".join(errors), encoding="utf-8")
    
    return output_path
