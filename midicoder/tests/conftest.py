from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TEXTURES_DIR = REPO_ROOT / "tests" / "textures" / "briefs"


@pytest.fixture()
def tmp_workdir(tmp_path: Path) -> Path:
    return tmp_path


def run_cli(args: Iterable[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    pythonpath = full_env.get("PYTHONPATH", "")
    full_env["PYTHONPATH"] = os.pathsep.join([str(REPO_ROOT), pythonpath]) if pythonpath else str(REPO_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "midicoder", *args],
        cwd=cwd,
        env=full_env,
        capture_output=True,
        text=True,
        check=False,
    )


def copy_brief(fixture_name: str, target_path: Path) -> None:
    source = TEXTURES_DIR / fixture_name
    if not source.exists():
        raise FileNotFoundError(f"Fixture not found: {source}")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target_path)


def write_llm_config(root: Path) -> dict[str, str] | None:
    """
    Prepare LLM config for tests by copying the repository-level
    `.midicoder/config.json` (and optional secrets) into the test workspace.
    """
    repo_midicoder = REPO_ROOT.parent / ".midicoder"
    repo_config_path = repo_midicoder / "config.json"
    if not repo_config_path.exists():
        return None

    payload = json.loads(repo_config_path.read_text(encoding="utf-8"))
    llm_section = payload.get("llm", {})
    high_section = llm_section.get("high") if isinstance(llm_section, dict) else None
    if not isinstance(high_section, dict):
        return None

    base_url = high_section.get("base_url") or high_section.get("baseUrl")
    model = high_section.get("model") or high_section.get("model_name")
    if not base_url or not model:
        return None

    config_path = root / ".midicoder" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    repo_secrets_path = repo_midicoder / "secrets" / "secrets.json"
    if repo_secrets_path.exists():
        secrets_target = root / ".midicoder" / "secrets" / "secrets.json"
        secrets_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo_secrets_path, secrets_target)

    return {"base_url": str(base_url), "model": str(model)}


def write_minimal_contracts(root: Path, version: str) -> Path:
    contracts_root = root / ".midicoder" / "versions" / version / "contracts"
    (contracts_root / "domain").mkdir(parents=True, exist_ok=True)
    (contracts_root / "app").mkdir(parents=True, exist_ok=True)
    (contracts_root / "api").mkdir(parents=True, exist_ok=True)
    (contracts_root / "rules").mkdir(parents=True, exist_ok=True)

    (contracts_root / "domain" / "entities.yaml").write_text(
        """
entities:
  - id: Order
    fields:
      - name: id
        type: uuid
""".lstrip(),
        encoding="utf-8",
    )
    (contracts_root / "domain" / "errors.yaml").write_text(
        """
errors:
  - id: OrderNotFound
    category: business
""".lstrip(),
        encoding="utf-8",
    )
    (contracts_root / "app" / "commands.yaml").write_text(
        """
commands:
  - id: CreateOrder
    input:
      - name: order_id
        type: uuid
    fetches: []
    guards: []
    effects: []
    errors: []
    returns: []
""".lstrip(),
        encoding="utf-8",
    )
    (contracts_root / "api" / "http.yaml").write_text(
        """
routes:
  - method: POST
    path: /orders
    command: CreateOrder
""".lstrip(),
        encoding="utf-8",
    )
    (contracts_root / "rules" / "rules.yaml").write_text(
        """
rules:
  - id: RuleCreateOrder
    applies_to: CreateOrder
    rows: []
""".lstrip(),
        encoding="utf-8",
    )
    return contracts_root


def assert_cli_success(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, (
        f"CLI failed with code {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
