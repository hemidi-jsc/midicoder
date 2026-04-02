"""Shared helpers for Midicoder commands."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


_yaml_writer = YAML()
_yaml_writer.default_flow_style = False
_yaml_writer.indent(mapping=2, sequence=4, offset=2)


@dataclass(frozen=True)
class MidicoderPaths:
    root: Path

    @property
    def dot_midicoder(self) -> Path:
        return self.root / ".midicoder"

    @property
    def config(self) -> Path:
        return self.dot_midicoder / "config.json"

    @property
    def state(self) -> Path:
        return self.dot_midicoder / "state.json"

    @property
    def runs(self) -> Path:
        return self.dot_midicoder / "runs"

    @property
    def context(self) -> Path:
        return self.dot_midicoder / "context"

    @property
    def versions(self) -> Path:
        return self.dot_midicoder / "versions"

    @property
    def logs(self) -> Path:
        return self.dot_midicoder / "logs"

    @property
    def secrets(self) -> Path:
        return self.dot_midicoder / "secrets"


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def ensure_base_layout(paths: MidicoderPaths) -> None:
    ensure_dir(paths.dot_midicoder)
    ensure_dir(paths.logs)
    ensure_dir(paths.runs)
    ensure_dir(paths.secrets)
    ensure_dir(paths.context)
    ensure_dir(paths.versions)

    _create_gitignore(paths)
    _ensure_secrets_file(paths)


def _create_gitignore(paths: MidicoderPaths) -> None:
    """Create .gitignore file in .midicoder directory."""
    gitignore_path = paths.dot_midicoder / ".gitignore"

    if gitignore_path.exists():
        return

    gitignore_content = """# Ignore secrets file
secrets/secrets.json

# Ignore backup files
secrets/*.bak

# Ignore log files
logs/
"""

    gitignore_path.write_text(gitignore_content, encoding="utf-8")


def _ensure_secrets_file(paths: MidicoderPaths) -> None:
    """Ensure secrets file is initialized."""
    from midicoder.config import SecretsManager

    secrets_manager = SecretsManager(paths.secrets)

    if not secrets_manager.secrets_file.exists():
        secrets_manager.initialize_empty()


def read_state(paths: MidicoderPaths) -> dict[str, Any]:
    if not paths.state.exists():
        return {"current_version": None, "contracts_locked": False}
    return json.loads(paths.state.read_text(encoding="utf-8"))


def read_config(paths: MidicoderPaths) -> dict[str, Any]:
    """Read config.json, return default config if not exists."""
    if not paths.config.exists():
        return {"stack": "fastapi", "working_dir": ".", "commands": [], "llm": {}}
    return json.loads(paths.config.read_text(encoding="utf-8"))


def write_state(paths: MidicoderPaths, state: dict[str, Any]) -> None:
    paths.state.write_text(
        json.dumps(state, indent=2, sort_keys=True), encoding="utf-8"
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_yaml(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        _yaml_writer.dump(payload, handle)


def create_run_dir(paths: MidicoderPaths, stage: str) -> Path:
    run_dir = paths.runs / stage / utc_timestamp()
    ensure_dir(run_dir)
    return run_dir


def write_run_outputs(
    run_dir: Path,
    stage: str,
    summary: dict[str, Any],
    *,
    state_before: dict[str, Any] | None = None,
    state_after: dict[str, Any] | None = None,
) -> None:
    summary_payload = {"stage": stage, "run_id": run_dir.name, **summary}
    write_json(run_dir / "summary.json", summary_payload)
    write_json(
        run_dir / "state_transitions.json",
        {
            "stage": stage,
            "run_id": run_dir.name,
            "from": state_before,
            "to": state_after,
        },
    )
    report_metadata = {
        "stage": stage,
        "run_id": run_dir.name,
        "status": summary_payload.get("status"),
    }
    for key in ("version", "task"):
        if key in summary_payload:
            report_metadata[key] = summary_payload[key]
    write_json(run_dir / "report_metadata.json", report_metadata)


def version_root(paths: MidicoderPaths, version: str) -> Path:
    return paths.versions / version


def ensure_version_layout(paths: MidicoderPaths, version: str) -> None:
    root = version_root(paths, version)
    ensure_dir(root)
    ensure_dir(root / "locks")
    ensure_dir(root / "contracts")
    ensure_dir(root / "irs")
    ensure_dir(root / "plans")
    ensure_dir(root / "patches")
    ensure_dir(root / "snapshots")
