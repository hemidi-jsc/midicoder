"""Contract generation and validation commands - Bootstrap only."""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Constants
MAX_LLM_TOKENS = 64000
MAX_DISPLAYED_ISSUES = 5

from midicoder.brief.analyzer import (
    get_contract_files_from_master_brief,
)
from midicoder.contract.contract_utils import (
    analyze_run_logs,
    read_json,
    read_schema_tree,
    validate_contract_file,
    write_contract_files,
)
from midicoder.contract.contract_validator import check_contract
from midicoder.contract.feedback_processor import (
    create_feedback_file,
    determine_file_repair_order,
    group_feedback_by_file,
    report_repair_status,
    validate_feedback,
)
from midicoder.contract.file_processor import process_file_feedback_items
from midicoder.contract.prompt_builder import (
    build_contract_context_block,
    build_contract_prompt,
    build_contract_system_prompt,
)
from midicoder.contract.trace_logger import (
    build_generation_summary,
    print_resume_summary,
    print_trace_summary,
    save_error_artifacts,
    save_generation_prompt,
    save_generation_response,
    save_generation_trace,
    save_processed_response,
    save_resume_context,
    validate_parsed_files,
)
from midicoder.contract.yaml_processor import (
    parse_contract_documents,
    strip_yaml_code_fences,
)
from midicoder.llm.client import LlmConfig, call_llm, load_llm_config
from midicoder.llm.context_builder import build_context_for_contract_gen

from .base import (
    MidicoderPaths,
    create_run_dir,
    ensure_base_layout,
    ensure_version_layout,
    read_state,
    write_run_outputs,
)


def _setup_contract_command(root: Path) -> tuple[MidicoderPaths, dict[str, Any], str]:
    """
    Common setup for contract commands.

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


def _prepare_contract_generation(
    paths: MidicoderPaths, version: str, root: Path
) -> dict[str, Any]:
    """Prepare common context for contract generation operations."""
    version_root = paths.versions / str(version)
    master_brief = version_root / "master-brief.md"

    if not master_brief.exists():
        raise RuntimeError("master-brief.md is missing.")

    master_brief_text = master_brief.read_text(encoding="utf-8")
    config = read_json(paths.config)
    llm_config = load_llm_config(paths, tier="high")
    stack = config.get("stack")
    stack_target = stack.get("target") if isinstance(stack, dict) else stack
    schema_tree = read_schema_tree(root)

    system_prompt = build_contract_system_prompt(
        version=str(version),
        stack=stack_target,
        master_brief=master_brief_text,
    )

    return {
        "master_brief_text": master_brief_text,
        "llm_config": llm_config,
        "stack_target": stack_target,
        "schema_tree": schema_tree,
        "system_prompt": system_prompt,
    }


def gen(root: Path) -> None:
    """Generate contract files based on master brief analysis."""
    paths, state, version = _setup_contract_command(root)

    context = _prepare_contract_generation(paths, version, root)
    master_brief_text = context["master_brief_text"]
    llm_config = context["llm_config"]
    stack_target = context["stack_target"]
    schema_tree = context["schema_tree"]
    system_prompt = context["system_prompt"]
    # Analyze master brief to determine required contract files
    print(
        "[contract gen] Analyzing master brief to determine required contract files..."
    )

    try:
        required_files, keyword_data = get_contract_files_from_master_brief(
            paths,
            version,
            master_brief_text,
            llm_config,
            call_llm,
        )

        print(
            f"[contract gen] LLM determined {len(required_files)} required contract files"
        )
        print(f"[contract gen] Files: {', '.join(required_files)}")
    except Exception as exc:
        from midicoder.llm.client import LlmRequestError

        error_message = f"Failed to analyze master brief: {exc}"
        print(f"[contract gen] ERROR: {error_message}")
        run_dir = create_run_dir(paths, "contract_gen")
        summary: dict[str, Any] = {
            "version": version,
            "status": "failed",
            "error": error_message,
            "task": "contract_gen",
        }
        write_run_outputs(
            run_dir, "contract_gen", summary, state_before=state, state_after=state
        )

        # Exit cleanly for LLM errors to avoid showing traceback
        if isinstance(exc, LlmRequestError):
            import sys

            sys.exit(1)
        else:
            raise RuntimeError(error_message) from exc

    # Generate the files
    _generate_contract_files(
        paths=paths,
        version=version,
        required_files=required_files,
        master_brief_text=master_brief_text,
        system_prompt=system_prompt,
        schema_tree=schema_tree,
        llm_config=llm_config,
        stack_target=stack_target,
        state=state,
        task_name="contract_gen",
    )


def _generate_contract_files(
    *,
    paths: MidicoderPaths,
    version: str,
    required_files: list[str],
    master_brief_text: str,
    system_prompt: str,
    schema_tree: dict[str, Any],
    llm_config: LlmConfig | dict[str, Any],
    stack_target: str,
    state: dict[str, Any],
    task_name: str = "contract_gen",
) -> None:
    """Generate contract files using LLM."""
    run_dir = create_run_dir(paths, task_name)

    # One file per pass for precise schema slicing
    batches = [[file] for file in required_files]
    total_passes = len(batches)
    print(
        f"[{task_name}] Starting contract generation: {len(required_files)} file(s) in {total_passes} pass(es)..."
    )

    created_files: list[str] = []
    created_paths: set[Path] = set()
    status = "failed"
    error_message = None
    all_traces: list[dict[str, Any]] = []

    try:
        contracts_root = paths.versions / version / "contracts"

        for index, batch in enumerate(batches, start=1):
            target_file = batch[0]
            print(
                f"[{task_name}] Pass {index}/{total_passes}: generating {target_file}"
            )

            response = None
            response_text = ""

            try:
                # Build context per batch
                context, trace = build_context_for_contract_gen(
                    root=paths.root,
                    context_dir=paths.context,
                    master_brief=master_brief_text,
                    target_files=batch,
                    schema_tree=schema_tree,
                    cache_dir=paths.versions / version / "cache",
                    llm_config=llm_config,
                    call_llm_func=call_llm,
                    contracts_root=contracts_root,
                )

                # Save comprehensive trace data
                trace_data = save_generation_trace(run_dir, index, batch, trace)
                all_traces.append(trace_data)
                print_trace_summary(trace, task_name)

                context_block = build_contract_context_block(context=context)
                prompt = build_contract_prompt(target_files=batch)
                save_generation_prompt(run_dir, index, context_block, prompt)

                # Call LLM
                response = call_llm(
                    llm_config,
                    system=system_prompt,
                    context=context_block,
                    prompt=prompt,
                    max_tokens=MAX_LLM_TOKENS,
                )

                save_generation_response(run_dir, index, response.raw, task_name)

                # Process response
                response_text = strip_yaml_code_fences(response.content)
                save_processed_response(run_dir, index, response_text)

                parsed_files = parse_contract_documents(response_text, contracts_root)
                validate_parsed_files(parsed_files, 1, index, task_name)

                pass_created = 0
                for path, content in parsed_files:
                    if path in created_paths:
                        continue
                    from midicoder.commands.base import write_yaml

                    if isinstance(content, str):
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(content, encoding="utf-8")
                    else:
                        write_yaml(path, content)
                    created_paths.add(path)
                    created_files.append(path.as_posix())
                    pass_created += 1

                print(
                    f"[{task_name}] Pass {index}/{total_passes} completed: wrote {pass_created} new file(s)"
                )

            except Exception as pass_exc:
                # Save error artifacts and build enhanced error message
                enhanced_error = save_error_artifacts(
                    run_dir,
                    index,
                    pass_exc,
                    target_file,
                    response,
                    response_text,
                    task_name,
                )

                # Re-raise with enhanced message
                if isinstance(pass_exc, RuntimeError):
                    raise RuntimeError(enhanced_error) from pass_exc
                else:
                    raise pass_exc

        status = "generated"
    except Exception as exc:
        error_message = str(exc)

    summary = build_generation_summary(
        version,
        status,
        created_files,
        llm_config,
        stack_target,
        task_name,
        required_files,
        all_traces,
        error_message,
    )

    write_run_outputs(
        run_dir, task_name, summary, state_before=state, state_after=state
    )

    if status == "generated":
        print(
            f"[{task_name}] Generated {len(created_files)} file(s) for version {version}"
        )
    else:
        from midicoder.llm.client import LlmRequestError

        print(f"[{task_name}] FAILED – {error_message or 'unknown error'}")

        # Exit cleanly for LLM errors to avoid showing traceback
        if "exc" in locals() and isinstance(exc, LlmRequestError):
            import sys

            sys.exit(1)


def check(root: Path) -> None:
    """Check contract files for issues."""
    paths, state, version = _setup_contract_command(root)
    contracts_root = paths.versions / version / "contracts"

    # Get contract files from master brief analysis
    version_root = paths.versions / str(version)
    master_brief = version_root / "master-brief.md"

    if master_brief.exists():
        try:
            master_brief_text = master_brief.read_text(encoding="utf-8")
            llm_config = load_llm_config(paths, tier="high")
            contract_files, _ = get_contract_files_from_master_brief(
                paths,
                version,
                master_brief_text,
                llm_config,
                call_llm,
            )
            expected_files = [contracts_root / file for file in contract_files]
        except Exception:
            print(
                "[contract check] Warning: Could not analyze master brief, checking all existing contract files"
            )
            expected_files = (
                list(contracts_root.glob("**/*.yaml"))
                if contracts_root.exists()
                else []
            )
    else:
        expected_files = (
            list(contracts_root.glob("**/*.yaml")) if contracts_root.exists() else []
        )

    expected_files = [f for f in expected_files if f.exists()]
    checked_files = [path.as_posix() for path in expected_files]

    issues = check_contract(contracts_root)
    issue_payload = [
        {"location": issue.location, "message": issue.message} for issue in issues
    ]
    status = "ok" if not issues else "failed"

    run_dir = create_run_dir(paths, "contract_check")
    write_run_outputs(
        run_dir,
        "contract_check",
        {
            "version": version,
            "status": status,
            "issues": issue_payload,
            "checked_files": checked_files,
            "contracts_root": contracts_root.as_posix(),
        },
        state_before=state,
        state_after=state,
    )

    if not issues:
        print(f"[contract check] OK – no issues found in {len(checked_files)} file(s)")
        return

    print(
        f"[contract check] FAILED – {len(issues)} issue(s) found in {len(checked_files)} file(s)"
    )
    for issue in issues[:MAX_DISPLAYED_ISSUES]:
        print(f"- {issue.location}: {issue.message}")
    if len(issues) > MAX_DISPLAYED_ISSUES:
        print(f"... and {len(issues) - MAX_DISPLAYED_ISSUES} more issues")
    raise SystemExit(1)


def feedback(root: Path) -> None:
    """Create or update feedback file from contract validation issues."""
    paths, state, version = _setup_contract_command(root)
    contracts_root = paths.versions / version / "contracts"
    issues = check_contract(contracts_root)

    feedback_path, new_items_count = create_feedback_file(
        paths, version, contracts_root, issues
    )

    items_count = new_items_count
    if new_items_count:
        print(
            f"[contract feedback] {feedback_path} ({items_count} items, {new_items_count} new from contract check)"
        )
    else:
        print(f"[contract feedback] {feedback_path} ({items_count} items)")

    run_dir = create_run_dir(paths, "contract_feedback")
    write_run_outputs(
        run_dir,
        "contract_feedback",
        {
            "version": version,
            "status": "ok",
            "feedback_file": str(feedback_path),
            "items_count": items_count,
        },
        state_before=state,
        state_after=state,
    )


def repair_prepare(root: Path) -> None:
    """Prepare contract repair by validating feedback file."""
    paths, state, version = _setup_contract_command(root)
    feedback_path = paths.versions / version / "contract-feedbacks.yml"
    if not feedback_path.exists():
        raise RuntimeError(
            "contract-feedbacks.yml is missing. Run `contract feedback` first."
        )

    feedback, errors = validate_feedback(
        paths, version=version, feedback_path=feedback_path
    )

    run_dir = create_run_dir(paths, "contract_repair_prepare")
    write_run_outputs(
        run_dir,
        "contract_repair_prepare",
        {
            "version": version,
            "status": "validated" if not errors else "failed",
            "feedback_items": len(feedback.items) if feedback else 0,
            "errors": errors,
        },
        state_before=state,
        state_after=state,
    )

    report_repair_status(label="prepare", feedback=feedback, errors=errors)


def repair_run(root: Path) -> None:
    """Run contract repair using LLM to generate patches for feedback items."""
    paths, state, version = _setup_contract_command(root)
    feedback_path = paths.versions / version / "contract-feedbacks.yml"
    if not feedback_path.exists():
        raise RuntimeError(
            "contract-feedbacks.yml is missing. Run `contract feedback` first."
        )

    feedback, errors = validate_feedback(
        paths, version=str(version), feedback_path=feedback_path
    )
    if errors:
        report_repair_status(label="run", feedback=feedback, errors=errors)

    if feedback is None:
        raise RuntimeError("contract-feedbacks.yml is invalid.")

    run_dir = create_run_dir(paths, "contract_repair_run")
    contracts_root = paths.versions / version / "contracts"
    master_brief_path = paths.versions / version / "master-brief.md"
    llm_config = load_llm_config(paths, tier="high")
    schema_tree = read_schema_tree(paths.root)
    master_brief_text = master_brief_path.read_text(encoding="utf-8")

    pending_items = [
        item for item in feedback.items if item.status in {"pending", "in_progress"}
    ]
    if not pending_items:
        print("[contract repair run] No pending feedback items.")
        return

    print(
        f"[contract repair run] Processing {len(pending_items)} pending feedback items..."
    )

    # Load available contract files
    available_contract_files = []
    try:
        required_files, keyword_data = get_contract_files_from_master_brief(
            paths,
            version,
            master_brief_text,
            llm_config,
            call_llm,
        )
        available_contract_files = required_files
    except Exception as exc:
        print(f"[contract repair run] Warning: Could not load contract files: {exc}")

    # Group feedback items by file
    grouped_files = group_feedback_by_file(pending_items)
    ordered_files = determine_file_repair_order(grouped_files)

    print(
        f"[contract repair run] Grouped into {len(grouped_files)} files for file-level repair"
    )

    # Process files in dependency order
    all_repair_results = []
    failed_files = []

    for i, file_path in enumerate(ordered_files, 1):
        file_items = grouped_files[file_path]
        print(
            f"[contract repair run] Processing file {i}/{len(ordered_files)}: {file_path} ({len(file_items)} items)"
        )

        try:
            repair_result = process_file_feedback_items(
                paths=paths,
                version=version,
                file_path=file_path,
                feedback_items=file_items,
                master_brief=master_brief_text,
                schema_tree=schema_tree,
                llm_config=llm_config,
                run_dir=run_dir,
                file_index=i,
                available_contract_files=available_contract_files,
            )
            all_repair_results.append(repair_result)

        except Exception as exc:
            error_info = {
                "file_path": file_path,
                "error": str(exc),
                "success": False,
                "items_count": len(file_items),
            }
            all_repair_results.append(error_info)
            failed_files.append(file_path)
            print(f"[contract repair run] ERROR: Failed to process {file_path}: {exc}")

    # Report summary
    successful_files = len([r for r in all_repair_results if r.get("success", False)])
    print(
        f"[contract repair run] Completed: {successful_files}/{len(ordered_files)} files successful"
    )

    if failed_files:
        print(
            f"[contract repair run] Failed files ({len(failed_files)}): {', '.join(failed_files)}"
        )

    # Serialize repair results to make them JSON-compatible
    # Convert FeedbackItem objects to dicts
    serialized_results = []
    for result in all_repair_results:
        serialized_result = dict(result)  # Copy the dict

        # Convert feedback_items (list of FeedbackItem objects) to list of dicts
        if "feedback_items" in serialized_result:
            feedback_items = serialized_result["feedback_items"]
            serialized_result["feedback_items"] = [
                {
                    "id": item.id,
                    "file": item.file,
                    "location": item.location,
                    "status": item.status,
                    "issue": item.issue,
                }
                for item in feedback_items
            ]

        serialized_results.append(serialized_result)

    # Write summary with detailed results
    summary = {
        "version": version,
        "status": "completed" if not failed_files else "partial",
        "total_files": len(ordered_files),
        "successful_files": successful_files,
        "failed_files": len(failed_files),
        "failed_file_paths": failed_files,
        "repair_results": serialized_results,
    }

    write_run_outputs(
        run_dir,
        "contract_repair_run",
        summary,
        state_before=state,
        state_after=state,
    )


def gen_resume(root: Path) -> None:
    """Resume contract generation from the last incomplete run."""
    paths, state, version = _setup_contract_command(root)

    context = _prepare_contract_generation(paths, version, root)
    master_brief_text = context["master_brief_text"]
    llm_config = context["llm_config"]
    stack_target = context["stack_target"]
    schema_tree = context["schema_tree"]
    system_prompt = context["system_prompt"]

    # Find the latest contract_gen run
    contract_gen_runs_dir = paths.runs / "contract_gen"
    if not contract_gen_runs_dir.exists():
        print(
            "[contract gen resume] No previous contract_gen runs found. Use `contract gen` instead."
        )
        return

    run_dirs = sorted(
        [d for d in contract_gen_runs_dir.iterdir() if d.is_dir()],
        key=lambda x: x.name,
        reverse=True,
    )

    if not run_dirs:
        print(
            "[contract gen resume] No previous contract_gen runs found. Use `contract gen` instead."
        )
        return

    latest_run_dir = run_dirs[0]
    print(f"[contract gen resume] Found latest run: {latest_run_dir.name}")

    # Get expected contract files
    try:
        required_files, keyword_data = get_contract_files_from_master_brief(
            paths,
            version,
            master_brief_text,
            llm_config,
            call_llm,
        )
        print(
            f"[contract gen resume] Expected contract files: {len(required_files)} files"
        )
    except Exception as exc:
        print(f"[contract gen resume] Failed to get required files: {exc}")
        return

    # Analyze the latest run
    attempted_files, successful_files = analyze_run_logs(latest_run_dir, required_files)

    # Determine remaining files
    contracts_root = paths.versions / version / "contracts"
    completed_files = set()
    failed_files = set()

    for required_file in required_files:
        if required_file not in attempted_files:
            failed_files.add(required_file)
            continue

        contract_path = contracts_root / required_file

        if required_file in successful_files and contract_path.exists():
            is_valid = validate_contract_file(contract_path, required_file)
            if is_valid:
                completed_files.add(required_file)
            else:
                failed_files.add(required_file)
        else:
            failed_files.add(required_file)

    remaining_files = list(failed_files)

    if not remaining_files:
        print(
            "[contract gen resume] All contract files are already generated and valid."
        )
        return

    print_resume_summary(
        completed_files, failed_files, set(), remaining_files, "contract gen resume"
    )

    # Generate the remaining files (all runs go to contract_gen folder)
    _generate_contract_files(
        paths=paths,
        version=version,
        required_files=remaining_files,
        master_brief_text=master_brief_text,
        system_prompt=system_prompt,
        schema_tree=schema_tree,
        llm_config=llm_config,
        stack_target=stack_target,
        state=state,
        task_name="contract_gen",  # Same folder as gen
    )
