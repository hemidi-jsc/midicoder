"""
Evidence/Integration tests for `midicoder init` command.
Unified location: midicoder/tests/integration/
Organized according to the Universal Testing Plan v0.2.0.
Goal: Black-box testing with high-volume parametrization.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
import pytest


def normalize_output(text: str) -> str:
    """Collapse all whitespace sequences (newlines, double spaces from rich wrapping) to a single space."""
    return re.sub(r'\s+', ' ', text).lower()


def run_cli(*args: str, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Helper to run the midicoder CLI in black-box mode via subprocess."""
    cmd = [sys.executable, "-m", "midicoder"] + list(args)
    
    # Ensure current dir has .midicoder to stop upward traversal
    (cwd / ".midicoder").mkdir(parents=True, exist_ok=True)
    
    full_env = os.environ.copy()
    # Path to the source root
    project_root = Path(__file__).resolve().parents[3]
    # Subprocess coverage tracking
    helper_path = Path(__file__).resolve().parents[3] / "coverage_helper"
    full_env["PYTHONPATH"] = f"{project_root}{os.pathsep}{helper_path}"
    full_env["COVERAGE_PROCESS_START"] = str(Path(__file__).resolve().parents[3] / ".coveragerc")
    full_env["PYTHONIOENCODING"] = "utf-8"
    if env:
        full_env.update(env)
    
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=full_env,
        input="",  # Force Non-TTY
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

# --- Integration Matrix: Happy Paths ---

@pytest.mark.parametrize("stack", ["fastapi", "nest,angular"])
@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_init_happy_path_matrix(tmp_path: Path, stack: str, provider: str) -> None:
    """Matrix tests for common stacks/providers."""
    model = "gpt-4o" if provider == "openai" else "claude-3-sonnet"
    key = f"fake-{provider}-key"
    
    result = run_cli(
        "init", "--non-interactive",
        "--stack", stack,
        "--llm-high-provider", provider,
        f"--llm-high-{provider}-model", model,
        f"--llm-high-{provider}-key", key,
        "--llm-cheap-provider", provider,
        f"--llm-cheap-{provider}-model", model,
        f"--llm-cheap-{provider}-key", key,
        cwd=tmp_path
    )
    
    assert result.returncode == 0, f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    config_file = tmp_path / ".midicoder" / "config.json"
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
    assert config["stack"] == stack.split(",")


# --- Integration Matrix: Failure Modes ---

@pytest.mark.parametrize("provider, missing_args, expected_msg", [
    ("openai", ["--llm-high-provider"], "LLM high tier provider is required"),
    ("openai", ["--llm-high-openai-model"], "model is required"),
    ("anthropic", ["--llm-cheap-provider"], "LLM cheap tier provider is required"),
    ("bedrock", ["--llm-high-aws-region-name"], "requires 'aws_region_name'"),
    ("azure", ["--llm-high-azure-openai-endpoint"], "requires 'azure_openai_endpoint'"),
])
def test_init_missing_preconditions_matrix(tmp_path: Path, provider: str, missing_args: list[str], expected_msg: str) -> None:
    """Test validation errors for each provider matrix."""
    base_args = [
        "init", "--non-interactive",
        "--stack", "fastapi",
        "--llm-high-provider", provider,
        "--llm-cheap-provider", provider,
    ]
    
    # Provider-specific needs
    if provider == "openai":
        base_args += ["--llm-high-openai-model", "gpt-4", "--llm-cheap-openai-model", "gpt-4"]
    elif provider == "bedrock":
        base_args += ["--llm-high-bedrock-model", "cl", "--llm-cheap-bedrock-model", "cl", "--llm-high-aws-region-name", "us-1"]
    elif provider == "azure":
        base_args += ["--llm-high-azure-model", "g", "--llm-cheap-azure-model", "g", 
                      "--llm-high-azure-openai-endpoint", "h", "--llm-high-azure-openai-api-version", "v", "--llm-high-azure-openai-deployment", "d"]
    
    # Remove args targeted for "missing"
    final_args = []
    i = 0
    while i < len(base_args):
        if base_args[i] in missing_args:
            if i + 1 < len(base_args) and not base_args[i+1].startswith("--"): i += 2
            else: i += 1
        else:
            final_args.append(base_args[i]); i += 1

    result = run_cli(*final_args, cwd=tmp_path)
    assert result.returncode == 1, f"Expected 1, got {result.returncode}\nSTDOUT: {result.stdout}"
    assert expected_msg.lower() in (result.stdout + result.stderr).lower()


# --- Operation matrices ---

def test_init_overwrite_protection(tmp_path: Path) -> None:
    args = ["init", "--non-interactive", "--stack", "fastapi", "--llm-high-provider", "openai", "--llm-high-openai-model", "gpt-4", "--llm-cheap-provider", "openai", "--llm-cheap-openai-model", "gpt-4"]
    run_cli(*args, cwd=tmp_path)
    # Fail
    res = run_cli(*args, cwd=tmp_path)
    assert res.returncode == 1
    # Success with rewrite
    res = run_cli(*(args + ["--rewrite-config"]), cwd=tmp_path)
    assert res.returncode == 0

def test_init_interactive_fallback(tmp_path: Path) -> None:
    # No --non-interactive
    result = run_cli("init", cwd=tmp_path)
    assert result.returncode == 0, f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    with open(tmp_path / ".midicoder" / "config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    assert config["stack"] == ["fastapi"]

@pytest.mark.parametrize("env_val", ["y", "yes", "true", "1", "YES", "on"])
def test_init_boolean_parser_matrix(tmp_path: Path, env_val: str) -> None:
    (tmp_path / ".midicoder").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".midicoder" / "config.json").write_text("{}", encoding="utf-8")
    env = {
        "MIDICODER_REWRITE_CONFIG": env_val,
        "MIDICODER_STACK": "fastapi",
        "MIDICODER_LLM_HIGH_PROVIDER": "openai",
        "MIDICODER_LLM_HIGH_OPENAI_MODEL": "gpt-4",
        "MIDICODER_LLM_CHEAP_PROVIDER": "openai",
        "MIDICODER_LLM_CHEAP_OPENAI_MODEL": "gpt-4"
    }
    result = run_cli("init", "--non-interactive", cwd=tmp_path, env=env)
    assert result.returncode == 0, f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"

def test_init_security_warning_detection(tmp_path: Path) -> None:
    result = run_cli(
        "init", "--non-interactive", "--stack", "fastapi",
        "--llm-high-provider", "openai", "--llm-high-openai-model", "gpt-4",
        "--llm-high-openai-key", "my-secret-key",
        "--llm-cheap-provider", "openai", "--llm-cheap-openai-model", "gpt-4",
        cwd=tmp_path
    )
    assert "visible in process list" in (result.stdout + result.stderr).lower()

def test_init_config_list_flag(tmp_path: Path) -> None:
    result = run_cli("init", "--config-list", cwd=tmp_path)
    assert result.returncode == 0
    assert "keywords" in result.stdout.lower()

def test_init_invalid_boolean_matrix(tmp_path: Path) -> None:
    env = {"MIDICODER_REWRITE_CONFIG": "maybe"}
    result = run_cli("init", "--non-interactive", cwd=tmp_path, env=env)
    assert result.returncode == 1
    assert "invalid rewrite setting" in result.stdout.lower()

def test_init_invalid_working_dir(tmp_path: Path) -> None:
    # On Windows, something like "CON" or "PRN" or a path with illegal chars
    result = run_cli("init", "--non-interactive", "--working-dir", "*/invalid", cwd=tmp_path)
    assert result.returncode == 1
    assert "invalid working directory" in result.stdout.lower()

def test_init_interactive_overwrite_deny(tmp_path: Path) -> None:
    # First init
    run_cli("init", "--non-interactive", "--stack", "fastapi", "--llm-high-provider", "openai", "--llm-high-openai-model", "gpt-4", "--llm-cheap-provider", "openai", "--llm-cheap-openai-model", "gpt-4", cwd=tmp_path)
    # Interactive init (will see existing config)
    # With input="", prompt_confirm returns default=False
    result = run_cli("init", cwd=tmp_path)
    assert result.returncode == 1
    assert "rewrite denied" in result.stdout.lower()

def test_init_bedrock_full_secrets(tmp_path: Path) -> None:
    env = {
        "MIDICODER_LLM_HIGH_PROVIDER": "bedrock",
        "MIDICODER_LLM_HIGH_BEDROCK_MODEL": "cl",
        "MIDICODER_LLM_HIGH_AWS_REGION_NAME": "us-east-1",
        "MIDICODER_LLM_HIGH_AWS_ACCESS_KEY_ID": "AKEY",
        "MIDICODER_LLM_HIGH_AWS_SECRET_ACCESS_KEY": "SKEY",
        "MIDICODER_LLM_CHEAP_PROVIDER": "openai",
        "MIDICODER_LLM_CHEAP_OPENAI_MODEL": "gpt-4"
    }
    result = run_cli("init", "--non-interactive", "--stack", "fastapi", cwd=tmp_path, env=env)
    assert result.returncode == 0
    # Check secrets.json
    secrets_file = tmp_path / ".midicoder" / "secrets" / "secrets.json"
    with open(secrets_file, "r", encoding="utf-8") as f:
        secrets = json.load(f)
    assert secrets["llm"]["high"]["aws_access_key_id"] == "AKEY"

def test_init_bedrock_env_secret_not_found(tmp_path: Path) -> None:
    result = run_cli(
        "init", "--non-interactive", "--stack", "fastapi",
        "--llm-high-provider", "bedrock", "--llm-high-bedrock-model", "cl",
        "--llm-high-aws-region-name", "us-1",
        "--llm-high-aws-access-key-id-env", "NOT_EXIST_AWS",
        "--llm-cheap-provider", "openai", "--llm-cheap-openai-model", "gpt-4",
        cwd=tmp_path
    )
    out = normalize_output(result.stdout + result.stderr)
    assert "not found for secret 'aws_access_key_id'" in out

def test_init_env_key_not_found(tmp_path: Path) -> None:
    result = run_cli(
        "init", "--non-interactive", "--stack", "fastapi",
        "--llm-high-provider", "openai", "--llm-high-openai-model", "gpt-4o",
        "--llm-high-openai-key-env", "NOT_EXIST_KEY",
        "--llm-cheap-provider", "openai", "--llm-cheap-openai-model", "gpt-4o-mini",
        cwd=tmp_path
    )
    out = normalize_output(result.stdout + result.stderr)
    assert "not found for" in out and "not_exist_key" in out

def test_init_openai_key_env(tmp_path: Path) -> None:
    env = {"MY_OPENAI_KEY": "SK-PROMPT"}
    result = run_cli(
        "init", "--non-interactive", "--stack", "fastapi",
        "--llm-high-provider", "openai", "--llm-high-openai-model", "gpt-4o",
        "--llm-high-openai-key-env", "MY_OPENAI_KEY",
        "--llm-cheap-provider", "openai", "--llm-cheap-openai-model", "gpt-4o-mini",
        cwd=tmp_path, env=env
    )
    out = normalize_output(result.stdout + result.stderr)
    assert "using api key for high-openai tier from env var: my_openai_key" in out

def test_init_provider_default_env_key(tmp_path: Path) -> None:
    # The CLI resolves the env var as MIDICODER_LLM_HIGH-OPENAI_API_KEY (tier="high-openai")
    env = {"MIDICODER_LLM_HIGH-OPENAI_API_KEY": "SK-DEFAULT"}
    result = run_cli(
        "init", "--non-interactive", "--stack", "fastapi",
        "--llm-high-provider", "openai", "--llm-high-openai-model", "gpt-4o",
        "--llm-cheap-provider", "openai", "--llm-cheap-openai-model", "gpt-4o-mini",
        cwd=tmp_path, env=env
    )
    out = normalize_output(result.stdout + result.stderr)
    assert "using api key for high-openai tier from env var: midicoder_llm_high-openai_api_key" in out

def test_init_openai_compatible(tmp_path: Path) -> None:
    result = run_cli(
        "init", "--non-interactive", "--stack", "fastapi",
        "--llm-high-provider", "openai_compatible", "--llm-high-model", "my-m",
        "--llm-high-url", "http://l", "--llm-high-key", "k",
        "--llm-cheap-provider", "openai", "--llm-cheap-openai-model", "gpt-4",
        cwd=tmp_path
    )
    assert result.returncode == 0
    with open(tmp_path / ".midicoder" / "config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    assert config["llm"]["high"]["base_url"] == "http://l"

def test_init_bedrock_env_secrets(tmp_path: Path) -> None:
    # Provide both required bedrock secrets via env var references
    env = {"MY_AWS_KEY": "KEY_VAL", "MY_AWS_SECRET": "SECRET_VAL"}
    result = run_cli(
        "init", "--non-interactive", "--stack", "fastapi",
        "--llm-high-provider", "bedrock", "--llm-high-bedrock-model", "cl",
        "--llm-high-aws-region-name", "us-1",
        "--llm-high-aws-access-key-id-env", "MY_AWS_KEY",
        "--llm-high-aws-secret-access-key-env", "MY_AWS_SECRET",
        "--llm-cheap-provider", "openai", "--llm-cheap-openai-model", "gpt-4",
        cwd=tmp_path, env=env
    )
    assert result.returncode == 0
    out = normalize_output(result.stdout + result.stderr)
    assert "using secret 'aws_access_key_id' for high tier from env var: my_aws_key" in out

def test_init_bedrock_direct_secrets(tmp_path: Path) -> None:
    result = run_cli(
        "init", "--non-interactive", "--stack", "fastapi",
        "--llm-high-provider", "bedrock", "--llm-high-bedrock-model", "cl",
        "--llm-high-aws-region-name", "us-1",
        "--llm-high-aws-access-key-id", "SECRET",
        "--llm-cheap-provider", "openai", "--llm-cheap-openai-model", "gpt-4",
        cwd=tmp_path
    )
    assert "provided directly via flag" in result.stdout.lower()

def test_init_vertex_provider_full_matrix(tmp_path: Path) -> None:
    env = {
        "MIDICODER_LLM_HIGH_PROVIDER": "vertex_partner",
        "MIDICODER_LLM_HIGH_VERTEX_MODEL": "gemini-pro",
        "MIDICODER_LLM_HIGH_VERTEX_PROJECT": "p123",
        "MIDICODER_LLM_HIGH_VERTEX_LOCATION": "l123",
        "MIDICODER_LLM_CHEAP_PROVIDER": "openai",
        "MIDICODER_LLM_CHEAP_OPENAI_MODEL": "gpt-4"
    }
    result = run_cli("init", "--non-interactive", "--stack", "fastapi", cwd=tmp_path, env=env)
    assert result.returncode == 0, f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    with open(tmp_path / ".midicoder" / "config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    assert config["llm"]["high"]["vertex_project"] == "p123"

    assert config["llm"]["high"]["vertex_project"] == "p123"

# --- Additional Evidence Cases (Pure E2E) ---

@pytest.mark.parametrize("off_val", ["n", "no", "off", "0", "false"])
def test_init_boolean_false_variants(tmp_path: Path, off_val: str) -> None:
    # First init to create config
    args = ["init", "--non-interactive", "--stack", "fastapi", "--llm-high-provider", "openai", "--llm-high-openai-model", "gpt-4", "--llm-cheap-provider", "openai", "--llm-cheap-openai-model", "gpt-4"]
    run_cli(*args, cwd=tmp_path)
    
    # Try to re-init with rewrite=off variant via env
    env = {"MIDICODER_REWRITE_CONFIG": off_val}
    result = run_cli(*args, cwd=tmp_path, env=env)
    # Should fail because rewrite is False
    assert result.returncode == 1
    assert "already exists" in (result.stdout + result.stderr).lower()

def test_init_empty_stack_defaults_to_fastapi(tmp_path: Path) -> None:
    # If stack is empty string, it fallbacks to DEFAULT_STACK (fastapi)
    # We need to provide LLM args to let it succeed
    result = run_cli("init", "--non-interactive", "--stack", "", 
                     "--llm-high-provider", "openai", "--llm-high-openai-model", "m", "--llm-high-openai-key", "k",
                     "--llm-cheap-provider", "openai", "--llm-cheap-openai-model", "m", "--llm-cheap-openai-key", "k",
                     cwd=tmp_path)
    assert result.returncode == 0
    with open(tmp_path / ".midicoder" / "config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    assert config["stack"] == ["fastapi"]

def test_init_unsupported_stack_error(tmp_path: Path) -> None:
    result = run_cli("init", "--non-interactive", "--stack", "unknown-stack", cwd=tmp_path)
    assert result.returncode == 1
    assert "unsupported stack" in (result.stdout + result.stderr).lower()

def test_init_unsupported_provider_error(tmp_path: Path) -> None:
    # Argparse handles choices, so it returns exit code 2
    result = run_cli("init", "--non-interactive", "--stack", "fastapi", "--llm-high-provider", "fake-llm", cwd=tmp_path)
    assert result.returncode == 2
    assert "invalid choice: 'fake-llm'" in (result.stdout + result.stderr).lower()