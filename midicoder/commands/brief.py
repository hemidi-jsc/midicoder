"""Brief management commands for master-brief.md."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from midicoder.brief.analyzer import (
    print_analysis_summary,
    refresh_contract_analysis,
)
from midicoder.brief.rewriter import rewrite_master_brief as rewrite_func
from midicoder.brief.rewriter import (
    save_rewritten_master_brief,
)
from midicoder.llm.client import call_llm, load_llm_config

from .base import (
    MidicoderPaths,
    create_run_dir,
    ensure_base_layout,
    ensure_version_layout,
    read_state,
    write_run_outputs,
)


def _setup_brief_command(root: Path) -> tuple[MidicoderPaths, dict[str, Any], str]:
    """
    Common setup for brief commands.

    Returns:
        Tuple of (paths, state, version)
    """
    paths = MidicoderPaths(root=root)
    ensure_base_layout(paths)
    state = read_state(paths)
    version = state.get("current_version")
    if not version:
        raise RuntimeError("No current version set. Run `version create` first.")
    ensure_version_layout(paths, str(version))
    return paths, state, str(version)


def analyze(root: Path) -> None:
    """Analyze the master brief to determine required contract files."""
    paths, state, version = _setup_brief_command(root)
    version_root = paths.versions / version
    master_brief = version_root / "master-brief.md"
    if not master_brief.exists():
        raise RuntimeError(
            "master-brief.md is missing. Cannot analyze without master brief."
        )

    master_brief_text = master_brief.read_text(encoding="utf-8")
    llm_config = load_llm_config(paths, tier="high")

    # Create run directory for logging
    run_dir = create_run_dir(paths, "brief_analyze")

    print(
        "[brief analyze] Analyzing master brief to determine required contract files..."
    )

    status = "failed"
    error_message = None
    required_files = []
    keyword_data = {}

    try:
        # Save original content for reference
        (run_dir / "master_brief.md").write_text(master_brief_text, encoding="utf-8")

        # Save LLM config
        import json

        (run_dir / "llm_config.json").write_text(
            json.dumps(
                {
                    "model": llm_config.model,
                    "base_url": llm_config.base_url,
                    "provider": llm_config.provider,
                    "cache_enabled": llm_config.cache_enabled,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        required_files, keyword_data = refresh_contract_analysis(
            paths,
            version,
            master_brief_text,
            llm_config,
            call_llm,
            run_dir=run_dir,
        )

        # Save analysis results
        (run_dir / "analysis_results.json").write_text(
            json.dumps(
                {
                    "contract_files": required_files,
                    "keyword_data": keyword_data,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        print_analysis_summary(required_files, keyword_data)

        status = "analyzed"
        print(f"[brief analyze] ✓ Analysis completed successfully")
        print(f"[brief analyze] ✓ Logs saved to: {run_dir.name}")

    except Exception as exc:
        from midicoder.llm.client import LlmRequestError

        # Save error details
        (run_dir / "error.txt").write_text(
            f"Error Type: {type(exc).__name__}\n"
            f"Error Message: {str(exc)}\n\n"
            f"Full Traceback:\n{_format_exception(exc)}",
            encoding="utf-8",
        )

        # Determine error message based on exception type
        if isinstance(exc, LlmRequestError):
            error_message = f"LLM request failed: {str(exc)}"

            # Save raw response if available
            if hasattr(exc, "raw_response") and exc.raw_response:
                (run_dir / "llm_error_response.txt").write_text(
                    exc.raw_response, encoding="utf-8"
                )

            # User-friendly error message
            if "504" in str(exc) or "Gateway Time-out" in str(exc):
                print(f"[brief analyze] ERROR: LLM server timeout (504)")
                print(
                    f"[brief analyze] → The master brief might be too long or the server is overloaded"
                )
                print(
                    f"[brief analyze] → Try again later or use a different LLM provider"
                )
            elif "timeout" in str(exc).lower():
                print(f"[brief analyze] ERROR: Request timeout")
                print(f"[brief analyze] → The LLM server took too long to respond")
                print(f"[brief analyze] → Try again later")
            else:
                print(f"[brief analyze] ERROR: {error_message}")
        else:
            error_message = f"Unexpected error: {str(exc)}"
            print(f"[brief analyze] ERROR: {error_message}")

        print(f"[brief analyze] ✓ Error details saved to: {run_dir.name}/error.txt")
        status = "failed"

    # Write run outputs
    summary = {
        "version": version,
        "status": status,
        "contract_files": required_files,
        "entities_count": len(keyword_data.get("entities", [])),
        "commands_count": len(keyword_data.get("commands", [])),
        "apis_count": len(keyword_data.get("apis", [])),
        "llm_config": {
            "model": llm_config.model,
            "base_url": llm_config.base_url,
            "provider": llm_config.provider,
        },
    }

    if error_message:
        summary["error"] = error_message

    write_run_outputs(
        run_dir,
        "brief_analyze",
        summary,
        state_before=state,
        state_after=state,
    )

    # Exit with error code if failed (don't raise to avoid showing traceback)
    if status == "failed":
        import sys

        sys.exit(1)


def rewrite(root: Path) -> None:
    """Review and rewrite master-brief.md using LLM."""
    paths, state, version = _setup_brief_command(root)
    version_root = paths.versions / version
    master_brief = version_root / "master-brief.md"
    if not master_brief.exists():
        raise RuntimeError(
            "master-brief.md is missing. Cannot rewrite without master brief."
        )

    master_brief_text = master_brief.read_text(encoding="utf-8")
    llm_config = load_llm_config(paths, tier="high")

    # Create run directory for logging
    run_dir = create_run_dir(paths, "brief_rewrite")

    print("[brief rewrite] Rewriting master brief using LLM...")

    status = "failed"
    error_message = None
    rewritten_content = None
    output_path = None

    try:
        # Save original content for reference
        (run_dir / "original_master_brief.md").write_text(
            master_brief_text, encoding="utf-8"
        )

        # Save LLM config
        import json

        (run_dir / "llm_config.json").write_text(
            json.dumps(
                {
                    "model": llm_config.model,
                    "base_url": llm_config.base_url,
                    "provider": llm_config.provider,
                    "cache_enabled": llm_config.cache_enabled,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        # Call LLM to analyze and generate improvements (pass run_dir to save prompts)
        (
            rewritten_content,
            llm_response,
            apply_errors,
            _context_summaries,
            _module_narratives,
        ) = rewrite_func(
            original_content=master_brief_text,
            llm_config=llm_config,
            run_dir=run_dir,
            repo_root=paths.root,
            context_dir=paths.context,
            cache_dir=paths.versions / version / "cache",
        )

        # Save rewritten content
        (run_dir / "rewritten_master_brief.md").write_text(
            rewritten_content, encoding="utf-8"
        )

        # Save to version directory
        output_path = save_rewritten_master_brief(
            version_root, rewritten_content, llm_response, apply_errors
        )

        status = "rewritten"

        print(f"[brief rewrite] ✓ Master brief improvements applied")
        print(f"[brief rewrite] ✓ Updated file: {output_path.name}")
        print(f"[brief rewrite] ✓ Analysis saved: master-brief.analysis.md")
        if apply_errors:
            print(f"[brief rewrite] ✓ Errors log: master-brief.errors.txt")
        print(f"[brief rewrite] ✓ Run logs: {run_dir.name}")
        print(
            f"[brief rewrite] → Review the changes and replace master-brief.md if satisfied"
        )

    except Exception as exc:
        from midicoder.llm.client import LlmRequestError

        # Save error details
        (run_dir / "error.txt").write_text(
            f"Error Type: {type(exc).__name__}\n"
            f"Error Message: {str(exc)}\n\n"
            f"Full Traceback:\n{_format_exception(exc)}",
            encoding="utf-8",
        )

        # Determine error message based on exception type
        if isinstance(exc, LlmRequestError):
            error_message = f"LLM request failed: {str(exc)}"

            # Save raw response if available
            if hasattr(exc, "raw_response") and exc.raw_response:
                (run_dir / "llm_error_response.txt").write_text(
                    exc.raw_response, encoding="utf-8"
                )

            # User-friendly error message
            if "504" in str(exc) or "Gateway Time-out" in str(exc):
                print(f"[brief rewrite] ERROR: LLM server timeout (504)")
                print(
                    f"[brief rewrite] → The master brief might be too long or the server is overloaded"
                )
                print(
                    f"[brief rewrite] → Try again later or use a different LLM provider"
                )
            elif "timeout" in str(exc).lower():
                print(f"[brief rewrite] ERROR: Request timeout")
                print(f"[brief rewrite] → The LLM server took too long to respond")
                print(f"[brief rewrite] → Try again later")
            else:
                print(f"[brief rewrite] ERROR: {error_message}")
        else:
            error_message = f"Unexpected error: {str(exc)}"
            print(f"[brief rewrite] ERROR: {error_message}")

        print(f"[brief rewrite] ✓ Error details saved to: {run_dir.name}/error.txt")
        status = "failed"

    # Write run outputs
    summary = {
        "version": version,
        "status": status,
        "original_file": "master-brief.md",
        "original_length": len(master_brief_text),
        "llm_config": {
            "model": llm_config.model,
            "base_url": llm_config.base_url,
            "provider": llm_config.provider,
        },
    }

    if status == "rewritten" and output_path and rewritten_content:
        summary.update(
            {
                "updated_file": str(output_path.name),
                "rewritten_length": len(rewritten_content),
                "changes_applied": len(rewritten_content) != len(master_brief_text),
                "has_errors": len(apply_errors) > 0 if apply_errors else False,
            }
        )

    if error_message:
        summary["error"] = error_message

    write_run_outputs(
        run_dir,
        "brief_rewrite",
        summary,
        state_before=state,
        state_after=state,
    )

    # Exit with error code if failed (don't raise to avoid showing traceback)
    if status == "failed":
        import sys

        sys.exit(1)


def _format_exception(exc: Exception) -> str:
    """Format exception with traceback."""
    import traceback

    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
