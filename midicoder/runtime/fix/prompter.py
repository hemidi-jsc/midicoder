"""Build LLM prompts for runtime fix generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from midicoder.llm.context_builder import _estimate_tokens

from .analyzer import ErrorAnalysis


@dataclass
class FixPrompt:
    """LLM prompt for fix generation."""

    context: str
    user_prompt: str


def _is_project_file(file_path: str, working_dir: Path) -> bool:
    """Check if file belongs to project workspace (exclude venv/library)."""
    normalized = file_path.replace("\\", "/").lower()
    skip_patterns = (
        "/venv/",
        "/.venv/",
        "/site-packages/",
        "/lib/python",
        "\\venv\\",
        "\\.venv\\",
        "\\site-packages\\",
    )
    if any(pattern in normalized for pattern in skip_patterns):
        return False

    # Relative paths are considered project-local.
    if not _is_absolute_path(file_path):
        return True

    try:
        abs_path = Path(file_path).resolve()
        abs_root = working_dir.resolve()
        abs_path.relative_to(abs_root)
        return True
    except Exception:
        return False


def _is_absolute_path(path_value: str) -> bool:
    return path_value.startswith("/") or (len(path_value) > 2 and path_value[1] == ":")


def _safe_read_file(working_dir: Path, file_path: str) -> str | None:
    try:
        target = (
            working_dir / file_path
            if not _is_absolute_path(file_path)
            else Path(file_path)
        )
        if not target.exists() or not target.is_file():
            return None
        if target.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
            return None
        return target.read_text(encoding="utf-8")
    except Exception:
        return None


def _extract_source_window(
    source_code: str, error_lines: list[int], *, max_lines: int
) -> str:
    """Extract focused source windows near error lines plus import header."""
    lines = source_code.splitlines()
    if not lines:
        return ""

    if len(lines) <= max_lines:
        return source_code

    selected: set[int] = set()

    # Keep import/header region.
    header_limit = min(40, len(lines))
    for idx in range(header_limit):
        selected.add(idx)

    # Keep windows near error lines.
    for line in error_lines:
        center = max(0, min(len(lines) - 1, line - 1))
        for idx in range(max(0, center - 10), min(len(lines), center + 11)):
            selected.add(idx)

    ordered = sorted(selected)
    chunks: list[str] = []
    prev = -2
    for idx in ordered:
        if idx != prev + 1:
            if prev >= 0:
                chunks.append("# ... lines skipped ...")
        chunks.append(lines[idx])
        prev = idx

    return "\n".join(chunks)


def _detect_stack(profile_summary: dict[str, Any]) -> str:
    stack = str(profile_summary.get("stack") or "").lower().strip()
    framework = str(profile_summary.get("framework") or "").lower().strip()
    candidates = [stack, framework]
    for value in candidates:
        if "nest" in value:
            return "nest"
        if "angular" in value:
            return "angular"
        if "fastapi" in value:
            return "fastapi"
    return "generic"


def _stack_adapter_rules(stack: str) -> list[str]:
    if stack == "fastapi":
        return [
            "STACK ADAPTER (FastAPI):",
            "- Respect existing FastAPI routing and dependency patterns.",
            "- Keep Pydantic schema definitions isolated from route handlers where possible.",
            "- Fix circular imports by moving shared types/constants to neutral modules.",
        ]
    if stack == "nest":
        return [
            "STACK ADAPTER (NestJS):",
            "- Respect module/provider/controller boundaries and DI registration.",
            "- Fix runtime DI/import errors by adjusting module exports/imports, not by bypassing DI.",
            "- Preserve DTO/service/controller responsibilities.",
        ]
    if stack == "angular":
        return [
            "STACK ADAPTER (Angular):",
            "- Respect NgModule/standalone boundaries and provider wiring.",
            "- Fix runtime import/injection issues through proper module/provider declarations.",
            "- Preserve component/service responsibilities and avoid moving business logic into views.",
        ]
    return [
        "STACK ADAPTER (Generic):",
        "- Infer conventions from provided source snippets and profile.",
        "- Keep fixes minimal, local, and aligned with current module structure.",
        "- Do not assume FastAPI/Nest/Angular unless the source context proves it.",
    ]


def build_fix_prompt(
    analysis: ErrorAnalysis,
    runtime_context: dict[str, Any],
    working_dir: Path,
) -> FixPrompt:
    """Build runtime-fix prompt from normalized runtime context schema."""
    profile_summary = runtime_context.get("profile_summary", {})
    relevant_files = list(runtime_context.get("relevant_files", []))
    symbols_by_file = runtime_context.get("symbols_by_file", {})
    traceback_focus = list(runtime_context.get("traceback_focus", []))
    seams = list(runtime_context.get("seams", []))
    entrypoints = list(runtime_context.get("entrypoints", []))
    contracts_focus = list(runtime_context.get("contracts_focus", []))
    ir_focus = list(runtime_context.get("ir_focus", []))

    stack = _detect_stack(profile_summary)

    context_parts: list[str] = []
    context_parts.append("## Runtime Fix Context")
    context_parts.append(f"Stack: {profile_summary.get('stack', 'unknown')}")
    context_parts.append(f"Framework: {profile_summary.get('framework', 'unknown')}")
    context_parts.append("")

    if traceback_focus:
        context_parts.append("## Traceback Focus")
        for item in traceback_focus[:20]:
            context_parts.append(
                f"- {item.get('file')}:{item.get('line', '?')} [{item.get('source', 'traceback')}]"
            )
        context_parts.append("")

    context_parts.append("## Relevant Source Files")
    max_total_tokens = 8000
    used_tokens = 0
    for file_path in relevant_files:
        if not _is_project_file(file_path, working_dir):
            continue

        source_code = _safe_read_file(working_dir, file_path)
        if not source_code:
            continue

        file_error_lines = [
            int(item.get("line"))
            for item in traceback_focus
            if item.get("file") == file_path and str(item.get("line") or "").isdigit()
        ]
        display_code = _extract_source_window(
            source_code, file_error_lines, max_lines=220
        )
        file_tokens = _estimate_tokens(display_code)
        if used_tokens + file_tokens > max_total_tokens:
            continue

        context_parts.append(f"### {file_path}")
        context_parts.append("```text")
        context_parts.append(display_code)
        context_parts.append("```")
        context_parts.append("")

        if file_path in symbols_by_file:
            context_parts.append("Symbols:")
            for sym in symbols_by_file[file_path][:20]:
                context_parts.append(f"- {sym}")
            context_parts.append("")

        used_tokens += file_tokens

    if entrypoints:
        context_parts.append("## Entrypoints")
        for ep in entrypoints[:10]:
            context_parts.append(f"- {ep}")
        context_parts.append("")

    if seams:
        context_parts.append("## Seams")
        for seam in seams[:12]:
            context_parts.append(f"- {seam}")
        context_parts.append("")

    if contracts_focus:
        context_parts.append("## Business Constraints from Contracts")
        for item in contracts_focus[:15]:
            context_parts.append(f"- {item}")
        context_parts.append("")

    if ir_focus:
        context_parts.append("## Business Constraints from IR")
        for item in ir_focus[:20]:
            context_parts.append(f"- {item}")
        context_parts.append("")

    context_parts.append("## Error Summary")
    for category in analysis.errors:
        context_parts.append(f"### {category.type} ({len(category.errors)} error(s))")
        for error in category.errors[:5]:
            message = str(error.get("message", "Unknown error")).strip()
            file_path = str(error.get("file") or "")
            line = error.get("line")
            marker = (
                "PROJECT"
                if file_path and _is_project_file(file_path, working_dir)
                else "EXTERNAL"
            )
            if file_path:
                context_parts.append(f"- {message}")
                context_parts.append(f"  at {file_path}:{line or '?'} [{marker}]")
            else:
                context_parts.append(f"- {message}")
        context_parts.append("")

    context_section = "\n".join(context_parts)

    user_prompt_parts: list[str] = [
        "Analyze runtime failures and generate patch-plan operations that fix root causes.",
        "",
        "UNIVERSAL RULES:",
        "- Fix only project files. Never patch venv/site-packages/system libraries.",
        "- Prioritize traceback-nearest root cause over symptom-level edits.",
        "- Keep fixes minimal and preserve existing business behavior.",
        "- Respect contract/IR constraints listed in context.",
        "",
    ]
    user_prompt_parts.extend(_stack_adapter_rules(stack))
    user_prompt_parts.extend(
        [
            "",
            "BUSINESS GUARD RULES:",
            "- Do not bypass validations/permissions/workflow rules just to make runtime pass.",
            "- Do not remove required domain constraints or API contract semantics.",
            "- If a risky behavior change is unavoidable, choose the smallest safe fix and annotate via ir_ref naming.",
            "",
            "OUTPUT FORMAT:",
            "Return ONLY valid JSON object with shape:",
            "{",
            '  "operations": [',
            "    {",
            '      "operation_type": "upsert_region",',
            '      "ir_ref": "runtime_fix:<category>:<id>",',
            '      "merge_mode": "patch",',
            '      "region_start": "# region runtime_fix:<category>:<id>",',
            '      "region_end": "# endregion runtime_fix:<category>:<id>",',
            '      "region_content": "...",',
            '      "imports": ["..."],',
            '      "file_path": "relative/path/to/file"',
            "    }",
            "  ]",
            "}",
            "",
            "STRICT REQUIREMENTS:",
            "- operation_type must be 'upsert_region'.",
            "- merge_mode must be one of: patch | create | append.",
            "- file_path is required and must be project-relative.",
            "- region_content must contain real fix code (not empty, not pass-only).",
            "",
            "Return JSON only.",
        ]
    )

    return FixPrompt(context=context_section, user_prompt="\n".join(user_prompt_parts))
