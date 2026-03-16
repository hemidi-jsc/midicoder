from __future__ import annotations

from pathlib import Path
from typing import Any

from midicoder.commands.base import MidicoderPaths
from midicoder.llm.client import LlmRequestError, call_llm, load_llm_config

from .models import PlanItemRuntime
from .prompt import build_codegen_prompt, build_project_file_prompt


def _strip_markdown_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def _drop_forbidden_full_file_lines(text: str) -> str:
    filtered: list[str] = []
    for line in text.splitlines():
        raw = line.strip()
        if raw.startswith("```"):
            continue
        if raw == "python":
            continue
        if raw == "from __future__ import annotations":
            continue
        filtered.append(line)
    return "\n".join(filtered).strip()


def _ensure_region_block(text: str, ir_ref: str) -> str:
    start = f"# region {ir_ref}"
    end = f"# endregion {ir_ref}"
    lines = [ln.rstrip() for ln in text.splitlines()]
    if lines and lines[0].strip() == start and lines[-1].strip() == end:
        return "\n".join(lines) + "\n"
    body = "\n".join(lines).strip()
    if not body:
        body = "__all__: list[str] = []"
    return f"{start}\n{body}\n{end}\n"


def _normalize_llm_output(text: str, ir_ref: str) -> str:
    text = _strip_markdown_fence(text)
    text = _drop_forbidden_full_file_lines(text)
    return _ensure_region_block(text, ir_ref)


def _should_use_llm(config: dict[str, Any] | None) -> bool:
    cfg = config or {}
    use_llm = cfg.get("code_gen_use_llm", True)
    if isinstance(use_llm, str):
        use_llm = use_llm.strip().lower() not in {"0", "false", "off", "no"}
    return bool(use_llm)


def _normalize_plain_text_output(text: str) -> str:
    cleaned = _strip_markdown_fence(text)
    cleaned_lines = [line.rstrip() for line in cleaned.splitlines() if not line.strip().startswith("```")]
    normalized = "\n".join(cleaned_lines).strip()
    return normalized + ("\n" if normalized and not normalized.endswith("\n") else "")


def maybe_generate_with_llm(
    *,
    workspace_root: Path,
    plan_item: PlanItemRuntime,
    context: dict[str, Any],
    runtime_path: str,
    config: dict[str, Any] | None,
    attempt: int = 1,
    max_attempts: int = 1,
    validation_errors: list[str] | None = None,
) -> tuple[str | None, list[str]]:
    warnings: list[str] = []
    if not _should_use_llm(config):
        return None, warnings

    paths = MidicoderPaths(root=workspace_root)
    try:
        llm_cfg = load_llm_config(paths, tier="cheap")
    except Exception as exc:  # pragma: no cover - config dependent
        warnings.append(f"LLM disabled for {plan_item.ir_ref}: {exc}")
        return None, warnings

    prompt = build_codegen_prompt(
        plan_item,
        context,
        runtime_path,
        attempt=attempt,
        max_attempts=max_attempts,
        validation_errors=validation_errors,
    )
    retry_mode = bool(validation_errors)
    try:
        response = call_llm(
            llm_cfg,
            system=(
                "Generate only valid FastAPI Python code for deterministic plan-to-patch conversion. "
                "Respect allowed_internal_modules from prompt; do not invent unresolved app.* imports. "
                "When validation errors are provided, fix every listed error in this attempt."
            ),
            prompt=prompt,
            temperature=0.1,
            max_tokens=8192,
        )
    except LlmRequestError as exc:  # pragma: no cover - network dependent
        warnings.append(f"LLM request failed for {plan_item.ir_ref}: {exc}")
        return None, warnings
    except Exception as exc:  # pragma: no cover - defensive
        warnings.append(f"LLM unexpected error for {plan_item.ir_ref}: {exc}")
        return None, warnings

    content = response.content.strip()
    if not content:
        mode = "retry" if retry_mode else "initial"
        warnings.append(f"LLM returned empty content for {plan_item.ir_ref} ({mode} attempt)")
        return None, warnings
    return _normalize_llm_output(content, plan_item.ir_ref), warnings


def maybe_generate_project_file_with_llm(
    *,
    workspace_root: Path,
    project_kind: str,
    runtime_path: str,
    context_payload: dict[str, Any],
    config: dict[str, Any] | None,
    attempt: int = 1,
    max_attempts: int = 1,
    validation_errors: list[str] | None = None,
) -> tuple[str | None, list[str]]:
    warnings: list[str] = []
    if not _should_use_llm(config):
        return None, warnings

    paths = MidicoderPaths(root=workspace_root)
    try:
        llm_cfg = load_llm_config(paths, tier="cheap")
    except Exception as exc:  # pragma: no cover - config dependent
        warnings.append(f"Project-file LLM disabled for {runtime_path}: {exc}")
        return None, warnings

    prompt = build_project_file_prompt(
        project_kind=project_kind,
        runtime_path=runtime_path,
        context_payload=context_payload,
        attempt=attempt,
        max_attempts=max_attempts,
        validation_errors=validation_errors,
    )
    try:
        response = call_llm(
            llm_cfg,
            system=(
                "Generate only valid deterministic JSON for project_file patch operation. "
                "Do not invent dependencies or symbols not present in provided context."
            ),
            prompt=prompt,
            temperature=0.0,
            max_tokens=2048,
        )
    except LlmRequestError as exc:  # pragma: no cover - network dependent
        warnings.append(f"Project-file LLM request failed for {runtime_path}: {exc}")
        return None, warnings
    except Exception as exc:  # pragma: no cover - defensive
        warnings.append(f"Project-file LLM unexpected error for {runtime_path}: {exc}")
        return None, warnings

    content = response.content.strip()
    if not content:
        warnings.append(f"Project-file LLM returned empty content for {runtime_path}")
        return None, warnings
    return _normalize_plain_text_output(content), warnings
