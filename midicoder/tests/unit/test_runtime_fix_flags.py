from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from midicoder.commands import runtime as runtime_commands
from midicoder.runtime.fix.models import PatchPlanItem, RuntimeFixResult
from midicoder.runtime.test.models import RuntimeTestResult


def _ok_fix_result(patches_dir: str = "/repo/.midicoder/versions/0.1.0/patches/runtime-fix/20260314T000000Z") -> RuntimeFixResult:
    return RuntimeFixResult(
        success=True,
        patch_plans=[
            PatchPlanItem(
                runtime_path="app/main.py",
                operation="upsert_region",
                ir_ref="Command.demo",
                patches=[],
            )
        ],
        patches_dir=patches_dir,
        errors=[],
    )


def test_runtime_fix_auto_apply_calls_code_apply(monkeypatch) -> None:
    root = Path("/repo")
    called: dict[str, object] = {}

    monkeypatch.setattr(
        "midicoder.runtime.fix.generator.generate_runtime_fixes",
        lambda workspace_root, log_timestamp, dry_run: _ok_fix_result(),
    )

    def _fake_apply(workspace_root, *, force, dry_run, reindex, patches_subdir):
        called["root"] = workspace_root
        called["patches_subdir"] = patches_subdir
        called["force"] = force
        called["dry_run"] = dry_run
        called["reindex"] = reindex

    monkeypatch.setattr("midicoder.commands.code.apply", _fake_apply)

    args = Namespace(
        log_timestamp=None,
        dry_run=False,
        auto_apply=True,
        auto_fix_loop=False,
        test_timeout=30,
        test_port=8000,
    )
    runtime_commands.fix(root, args)

    assert called["root"] == root
    assert called["patches_subdir"] == "patches/runtime-fix/20260314T000000Z"
    assert called["force"] is False
    assert called["dry_run"] is False
    assert called["reindex"] is True


def test_runtime_fix_auto_fix_loop_runs_until_runtime_test_passes(monkeypatch) -> None:
    root = Path("/repo")
    calls = {"test": 0, "fix": 0, "apply": 0}

    def _fake_test(workspace_root, timeout, port, verbose):
        calls["test"] += 1
        if calls["test"] == 1:
            return RuntimeTestResult(
                timestamp="20260314T010000Z",
                success=False,
                port=port,
                errors=[],
                log_dir="/repo/.midicoder/logs/20260314T010000Z",
                debug_output=[],
            )
        return RuntimeTestResult(
            timestamp="20260314T010500Z",
            success=True,
            port=port,
            errors=[],
            log_dir="/repo/.midicoder/logs/20260314T010500Z",
            debug_output=[],
        )

    def _fake_fix(workspace_root, log_timestamp, dry_run):
        calls["fix"] += 1
        assert log_timestamp == "20260314T010000Z"
        assert dry_run is False
        return _ok_fix_result()

    def _fake_apply(workspace_root, *, force, dry_run, reindex, patches_subdir):
        calls["apply"] += 1
        assert patches_subdir == "patches/runtime-fix/20260314T000000Z"

    monkeypatch.setattr("midicoder.runtime.test.runner.run_runtime_test", _fake_test)
    monkeypatch.setattr("midicoder.runtime.fix.generator.generate_runtime_fixes", _fake_fix)
    monkeypatch.setattr("midicoder.commands.code.apply", _fake_apply)

    args = Namespace(
        log_timestamp=None,
        dry_run=False,
        auto_apply=False,
        auto_fix_loop=True,
        test_timeout=15,
        test_port=9000,
    )
    runtime_commands.fix(root, args)

    assert calls["test"] == 2
    assert calls["fix"] == 1
    assert calls["apply"] == 1


def test_runtime_fix_dry_run_disables_auto_apply(monkeypatch) -> None:
    root = Path("/repo")
    called = {"apply": 0}

    monkeypatch.setattr(
        "midicoder.runtime.fix.generator.generate_runtime_fixes",
        lambda workspace_root, log_timestamp, dry_run: _ok_fix_result(),
    )
    monkeypatch.setattr(
        "midicoder.commands.code.apply",
        lambda *args, **kwargs: called.__setitem__("apply", called["apply"] + 1),
    )

    args = Namespace(
        log_timestamp=None,
        dry_run=True,
        auto_apply=True,
        auto_fix_loop=False,
        test_timeout=30,
        test_port=8000,
    )
    runtime_commands.fix(root, args)

    assert called["apply"] == 0
