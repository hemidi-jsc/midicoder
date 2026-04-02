"""Trace logging and debug artifact management for contract operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def save_generation_trace(
    run_dir: Path,
    pass_index: int,
    batch: list[str],
    trace: Any,
) -> dict[str, Any]:
    """
    Save comprehensive trace data for contract generation pass.

    Args:
        run_dir: Run directory for output
        pass_index: Current pass index (1-based)
        batch: List of target files in this batch
        trace: RetrievalTrace object from context_builder

    Returns:
        Trace data dict that was saved
    """
    trace_data = {
        "batch": batch,
        "semantic_groups": trace.semantic_groups,
        "keywords_count": len(trace.keywords_used),
        "keywords_used": trace.keywords_used,
        "top_k_results": trace.top_k_results,
        "estimated_tokens": trace.estimated_tokens,
        "items_dropped": trace.items_dropped,
    }

    # Save individual trace file for debugging
    trace_file = run_dir / f"trace_pass_{pass_index}.json"
    trace_file.write_text(
        json.dumps(trace_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return trace_data


def print_trace_summary(trace: Any, task_name: str = "contract gen") -> None:
    """
    Print human-readable trace summary to console.

    Args:
        trace: RetrievalTrace object from context_builder
        task_name: Name of the task for logging
    """
    print(
        f"[{task_name}] Context: {trace.estimated_tokens} tokens, "
        f"{len(trace.keywords_used)} keywords, "
        f"{sum(trace.top_k_results.values())} artifacts"
    )


def save_generation_prompt(
    run_dir: Path,
    pass_index: int,
    context_block: str,
    prompt: str,
) -> None:
    """
    Save full prompt for debugging (context + prompt combined).

    Args:
        run_dir: Run directory for output
        pass_index: Current pass index (1-based)
        context_block: Context block string
        prompt: Main prompt string
    """
    full_prompt = "\n\n".join([context_block, prompt])
    prompt_file = run_dir / f"prompt_pass_{pass_index}.txt"
    prompt_file.write_text(full_prompt, encoding="utf-8")


def save_generation_response(
    run_dir: Path,
    pass_index: int,
    raw_response: str,
    task_name: str = "contract gen",
) -> dict[str, Any]:
    """
    Save raw LLM response and check for truncation.

    Args:
        run_dir: Run directory for output
        pass_index: Current pass index (1-based)
        raw_response: Raw response string from LLM
        task_name: Name of the task for logging

    Returns:
        Response metadata dict with finish_reason, truncated flag, etc.
    """
    # Save raw response
    response_file = run_dir / f"response_pass_{pass_index}.txt"
    response_file.write_text(raw_response, encoding="utf-8")

    # Check if response was truncated
    metadata = {
        "truncated": False,
        "finish_reason": None,
    }

    try:
        response_data = json.loads(raw_response)
        finish_reason = response_data.get("choices", [{}])[0].get("finish_reason")
        metadata["finish_reason"] = finish_reason

        if finish_reason == "length":
            metadata["truncated"] = True
            print(
                f"[{task_name}] Warning: Pass {pass_index} response was truncated due to token limit"
            )
            print(
                f"[{task_name}] This may cause YAML parsing errors. Consider simplifying the target file."
            )
    except Exception:
        # If we can't parse response metadata, just continue
        pass

    return metadata


def save_processed_response(
    run_dir: Path,
    pass_index: int,
    processed_content: str,
) -> None:
    """
    Save processed/cleaned response content for debugging.

    Args:
        run_dir: Run directory for output
        pass_index: Current pass index (1-based)
        processed_content: Cleaned/processed response content
    """
    processed_file = run_dir / f"response_processed_pass_{pass_index}.txt"
    processed_file.write_text(processed_content, encoding="utf-8")


def validate_parsed_files(
    parsed_files: list[tuple[Path, Any]],
    expected_count: int,
    pass_index: int,
    task_name: str = "contract gen",
) -> None:
    """
    Validate parsed files count and print warnings if mismatch.

    Args:
        parsed_files: List of (path, content) tuples
        expected_count: Expected number of files (usually 1 for single-file-per-pass)
        pass_index: Current pass index (1-based)
        task_name: Name of the task for logging
    """
    if len(parsed_files) != expected_count:
        print(
            f"[{task_name}] Warning: Expected {expected_count} file(s), "
            f"got {len(parsed_files)} file(s) in pass {pass_index}"
        )
        print(f"[{task_name}] Files: {[str(p) for p, _ in parsed_files]}")


def save_error_artifacts(
    run_dir: Path,
    pass_index: int,
    pass_exc: Exception,
    target_file: str,
    response: Any = None,
    response_text: str = "",
    task_name: str = "contract gen",
) -> str:
    """
    Save error-related artifacts and build enhanced error message.

    Args:
        run_dir: Run directory for output
        pass_index: Current pass index (1-based)
        pass_exc: Exception that was raised
        target_file: Target file being processed
        response: LLM response object (optional)
        response_text: Processed response text (optional)
        task_name: Name of the task for logging

    Returns:
        Enhanced error message with additional context
    """
    from midicoder.llm.client import LlmRequestError

    error_details = []

    # Save error response if available
    if (
        isinstance(pass_exc, LlmRequestError)
        and hasattr(pass_exc, "raw_response")
        and pass_exc.raw_response
    ):
        response_file = run_dir / f"response_pass_{pass_index}.txt"
        response_file.write_text(pass_exc.raw_response, encoding="utf-8")
        error_details.append("LLM request failed")
    elif response and hasattr(response, "raw"):
        # If we have a response but processing failed, ensure raw response is saved
        response_file = run_dir / f"response_pass_{pass_index}.txt"
        response_file.write_text(response.raw, encoding="utf-8")

        # Check if response was truncated
        try:
            response_data = json.loads(response.raw)
            finish_reason = response_data.get("choices", [{}])[0].get("finish_reason")
            if finish_reason == "length":
                error_details.append("Response was truncated due to token limit")
                error_details.append(
                    f"Consider simplifying {target_file} or splitting into smaller contracts"
                )
        except:
            pass

    # Save processed content for debugging if available
    if response_text:
        processed_file = run_dir / f"response_processed_pass_{pass_index}.txt"
        processed_file.write_text(response_text, encoding="utf-8")
        error_details.append(
            f"Processed content saved to response_processed_pass_{pass_index}.txt"
        )

    # Build enhanced error message
    enhanced_error = f"Pass {pass_index} failed processing {target_file}: {pass_exc}"
    if error_details:
        enhanced_error += f"\nAdditional info: {'; '.join(error_details)}"

    print(f"[{task_name}] {enhanced_error}")

    return enhanced_error


def build_generation_summary(
    version: str,
    status: str,
    created_files: list[str],
    llm_config: Any,
    stack_target: str,
    task_name: str,
    required_files: list[str],
    all_traces: list[dict[str, Any]],
    error_message: str | None = None,
) -> dict[str, Any]:
    """
    Build comprehensive summary for contract generation run.

    Args:
        version: Version string
        status: Status string ("generated", "failed", etc.)
        created_files: List of created file paths
        llm_config: LLM config object
        stack_target: Technology stack
        task_name: Name of the task
        required_files: List of required files
        all_traces: List of trace data dicts
        error_message: Error message if failed

    Returns:
        Summary dict for write_run_outputs
    """
    from midicoder.llm.client import LlmConfig

    summary = {
        "version": version,
        "status": status,
        "created_files": created_files,
        "llm_model": llm_config.model
        if isinstance(llm_config, LlmConfig)
        else llm_config.get("model", "unknown"),
        "stack": stack_target,
        "task": task_name,
        "passes": len(all_traces),
        "total_files": len(required_files),
    }

    if error_message:
        summary["error"] = error_message

    if all_traces:
        summary["traces"] = all_traces

    return summary


def save_resume_context(
    run_dir: Path,
    latest_run_dir: Path,
    total_expected_files: int,
    completed_files: set[str],
    failed_files: set[str],
    never_attempted_files: set[str],
    remaining_files: list[str],
) -> None:
    """
    Save resume context for contract generation resume operation.

    Args:
        run_dir: Current run directory
        latest_run_dir: Path to the latest run being resumed
        total_expected_files: Total number of expected files
        completed_files: Set of completed file paths
        failed_files: Set of failed file paths
        never_attempted_files: Set of never attempted file paths
        remaining_files: List of remaining files to generate
    """
    resume_context = {
        "resumed_from": latest_run_dir.name,
        "total_expected_files": total_expected_files,
        "completed_files": sorted(list(completed_files)),
        "failed_files": sorted(list(failed_files)),
        "never_attempted_files": sorted(list(never_attempted_files)),
        "remaining_files": remaining_files,
        "resume_strategy": "intelligent_log_analysis",
        "completed_count": len(completed_files),
        "failed_count": len(failed_files),
        "never_attempted_count": len(never_attempted_files),
        "remaining_count": len(remaining_files),
    }

    resume_file = run_dir / "resume_context.json"
    resume_file.write_text(
        json.dumps(resume_context, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def print_resume_summary(
    completed_files: set[str],
    failed_files: set[str],
    never_attempted_files: set[str],
    remaining_files: list[str],
    task_name: str = "contract gen resume",
) -> None:
    """
    Print human-readable resume summary to console.

    Args:
        completed_files: Set of completed file paths
        failed_files: Set of failed file paths
        never_attempted_files: Set of never attempted file paths
        remaining_files: List of remaining files to generate
        task_name: Name of the task for logging
    """
    print(f"[{task_name}] Found {len(remaining_files)} files to generate:")

    if failed_files:
        print(f"[{task_name}] - {len(failed_files)} files failed in previous run:")
        for file in sorted(failed_files):
            print(f"[{task_name}]     {file}")

    if never_attempted_files:
        print(f"[{task_name}] - {len(never_attempted_files)} files never attempted:")
        for file in sorted(never_attempted_files):
            print(f"[{task_name}]     {file}")

    print(
        f"[{task_name}] Smart resume saved {len(completed_files)} LLM calls by reusing valid files"
    )
