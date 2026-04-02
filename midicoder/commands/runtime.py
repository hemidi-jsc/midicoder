"""Runtime test and fix commands."""

from __future__ import annotations

import argparse
from pathlib import Path

from midicoder.commands import code as code_commands

AUTO_FIX_LOOP_MAX_ITERATIONS = 10


def test(root: Path, args: argparse.Namespace) -> None:
    """Run runtime test on FastAPI application."""
    from midicoder.io.messages import (
        print_error,
        print_info,
        print_normal,
        print_success,
    )
    from midicoder.runtime.test.runner import run_runtime_test

    print_info("Starting runtime test...", title="Runtime Test")
    print_normal(f"Timeout: {args.timeout}s")
    print_normal(f"Port: {args.port}")
    print_normal("")

    result = run_runtime_test(
        workspace_root=root,
        timeout=args.timeout,
        port=args.port,
        verbose=args.verbose,
    )

    print_normal("")

    if result.success:
        print_success(
            f"Runtime test passed! App started successfully on port {result.port}",
            title="✓ Success",
        )
        print_normal(f"\nLogs saved to: [cyan]{result.log_dir}[/cyan]")
    else:
        print_error(
            f"Runtime test failed with {len(result.errors)} error(s)",
            title="✗ Failed",
        )
        print_normal(f"\nLogs saved to: [cyan]{result.log_dir}[/cyan]")
        print_normal("\n[bold]Error Summary:[/bold]")

        # Group errors by type
        error_types = {}
        for error in result.errors:
            if error.type not in error_types:
                error_types[error.type] = []
            error_types[error.type].append(error)

        for error_type, errors in error_types.items():
            print_normal(f"  • [red]{error_type}[/red]: {len(errors)} error(s)")
            for i, error in enumerate(errors[:3], 1):  # Show first 3 of each type
                print_normal(f"    {i}. {error.message[:100]}")
            if len(errors) > 3:
                print_normal(f"    ... and {len(errors) - 3} more")

        print_normal("\n[bold]Next steps:[/bold]")
        print_normal(
            "  1. Review error details: [cyan]cat "
            + result.log_dir
            + "/error.log[/cyan]"
        )
        print_normal("  2. Auto-fix errors: [cyan]midicoder runtime fix[/cyan]")
        print_normal("  3. Or manually fix the code")


def fix(root: Path, args: argparse.Namespace) -> None:
    """Generate fixes for runtime errors."""
    from midicoder.io.messages import (
        print_error,
        print_info,
        print_normal,
        print_success,
        print_warning,
    )
    from midicoder.runtime.fix.generator import generate_runtime_fixes
    from midicoder.runtime.test.runner import run_runtime_test

    auto_fix_loop = bool(getattr(args, "auto_fix_loop", False))
    auto_apply = bool(getattr(args, "auto_apply", False)) or auto_fix_loop

    if args.dry_run and (auto_apply or auto_fix_loop):
        print_warning(
            "Ignoring --auto-apply/--auto-fix-loop because --dry-run is enabled."
        )
        auto_apply = False
        auto_fix_loop = False

    print_info("Analyzing runtime errors...", title="Runtime Fix")
    if auto_apply:
        print_normal("Auto apply: enabled")
    if auto_fix_loop:
        print_normal(
            f"Auto-fix loop: enabled (max {AUTO_FIX_LOOP_MAX_ITERATIONS} iteration(s))"
        )

    if args.log_timestamp:
        print_normal(f"Using log timestamp: {args.log_timestamp}")
    else:
        print_normal("Using latest error log")

    if args.dry_run:
        print_normal("[yellow]DRY RUN MODE - No files will be saved[/yellow]")

    print_normal("")

    if auto_fix_loop:
        for iteration in range(1, AUTO_FIX_LOOP_MAX_ITERATIONS + 1):
            print_info(
                f"[Loop {iteration}/{AUTO_FIX_LOOP_MAX_ITERATIONS}] Running runtime test...",
            )
            test_result = run_runtime_test(
                workspace_root=root,
                timeout=int(getattr(args, "test_timeout", 30)),
                port=int(getattr(args, "test_port", 8000)),
                verbose=False,
            )

            if test_result.success:
                print_success(
                    f"Runtime test passed on iteration {iteration}. No more runtime errors detected.",
                    title="✓ Loop Completed",
                )
                print_normal(f"\nLogs saved to: [cyan]{test_result.log_dir}[/cyan]")
                return

            print_warning(
                f"[Loop {iteration}] Detected {len(test_result.errors)} runtime error(s). Generating fixes..."
            )
            result = generate_runtime_fixes(
                workspace_root=root,
                log_timestamp=test_result.timestamp,
                dry_run=False,
            )
            _print_fix_result(result=result, dry_run=False)
            if not result.success:
                return

            apply_ok = _auto_apply_runtime_fix_patches(root, result.patches_dir)
            if not apply_ok:
                return

            print_normal("")

        print_error(
            "Auto-fix loop reached max iterations without a clean runtime test.",
            title="✗ Loop Stopped",
        )
        print_normal(
            "Please inspect latest logs/patches and continue manually with "
            "[cyan]midicoder runtime test[/cyan] + [cyan]midicoder runtime fix[/cyan]."
        )
        return

    result = generate_runtime_fixes(
        workspace_root=root,
        log_timestamp=args.log_timestamp,
        dry_run=args.dry_run,
    )
    _print_fix_result(result=result, dry_run=args.dry_run)
    if not result.success or not auto_apply:
        return
    _auto_apply_runtime_fix_patches(root, result.patches_dir)


def _print_fix_result(result, dry_run: bool) -> None:
    from midicoder.io.messages import print_error, print_normal, print_success

    print_normal("")

    if result.success:
        print_success(
            f"Generated {len(result.patch_plans)} patch plan(s)",
            title="✓ Success",
        )

        if not dry_run:
            print_normal(f"\nPatches saved to: [cyan]{result.patches_dir}[/cyan]")

        print_normal("\n[bold]Generated patches:[/bold]")
        for i, plan in enumerate(result.patch_plans, 1):
            print_normal(f"  {i}. [cyan]{plan.runtime_path}[/cyan] ({plan.operation})")
            print_normal(f"     IR ref: [dim]{plan.ir_ref}[/dim]")
            print_normal(f"     Operations: {len(plan.patches)}")

        print_normal("\n[bold]Next steps:[/bold]")
        if dry_run:
            print_normal("  • Run without --dry-run to save patches")
        else:
            print_normal(
                "  1. Review patches: [cyan]ls " + result.patches_dir + "[/cyan]"
            )
            print_normal("  2. Apply patches: [cyan]midicoder code apply[/cyan]")
            print_normal("  3. Test again: [cyan]midicoder runtime test[/cyan]")
            print_normal("  4. Repeat until all errors are fixed")
        return

    print_error("Failed to generate fixes", title="✗ Failed")

    print_normal("\n[bold]Errors:[/bold]")
    for error in result.errors:
        print_error(f"  • {error}")

    print_normal("\n[bold]Troubleshooting:[/bold]")
    print_normal("  • Check that error logs exist: [cyan]ls .midicoder/logs[/cyan]")
    print_normal("  • Run test first: [cyan]midicoder runtime test[/cyan]")
    print_normal("  • Check LLM config: [cyan]midicoder config list[/cyan]")


def _auto_apply_runtime_fix_patches(root: Path, patches_dir: str) -> bool:
    from midicoder.io.messages import print_error, print_info

    subdir = _resolve_patches_subdir(root, patches_dir)
    if not subdir:
        print_error(
            f"Cannot auto-apply patches because path is invalid: {patches_dir}",
            title="✗ Auto Apply Failed",
        )
        return False

    print_info("Auto-applying runtime fix patches...", title="Code Apply")
    try:
        code_commands.apply(
            root,
            force=False,
            dry_run=False,
            reindex=True,
            patches_subdir=subdir,
        )
    except Exception as exc:
        print_error(f"Auto-apply failed: {exc}", title="✗ Auto Apply Failed")
        return False
    return True


def _resolve_patches_subdir(root: Path, patches_dir: str) -> str | None:
    if not patches_dir:
        return None

    absolute = Path(patches_dir)
    if not absolute.is_absolute():
        absolute = (root / patches_dir).resolve()

    parts = list(absolute.parts)
    if "patches" not in parts:
        return None
    start = parts.index("patches")
    return "/".join(parts[start:])
