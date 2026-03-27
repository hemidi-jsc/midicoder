from __future__ import annotations

import json
import subprocess
from pathlib import Path

from midicoder.tests.conftest import assert_cli_success, run_cli, write_llm_config


def test_index_integration_full_workflow(tmp_workdir: Path) -> None:
    """Integration test: index command creates all required context artifacts."""
    # Setup: Initialize project
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    # Execute: Run index command
    index_result = run_cli(["index"], tmp_workdir)
    assert_cli_success(index_result)

    # Verify: All context files are created
    context_dir = tmp_workdir / ".midicoder" / "context"
    assert context_dir.exists()
    
    expected_files = [
        "manifest.json",
        "profile.json",
        "symbols.json",
        "entrypoints.json",
        "seams.json",
        "exemplars.json",
    ]
    
    for filename in expected_files:
        file_path = context_dir / filename
        assert file_path.exists(), f"Expected file {filename} not found"
        
        # Verify file contains valid JSON
        content = json.loads(file_path.read_text(encoding="utf-8"))
        assert content is not None


def test_index_integration_with_source_files(tmp_workdir: Path) -> None:
    """Integration test: index command processes actual source files."""
    # Setup: Initialize and create source files
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)
    
    src_dir = tmp_workdir / "src"
    src_dir.mkdir()
    (src_dir / "example.py").write_text(
        "def example_function():\n"
        "    return 'Hello, World!'\n"
    )
    
    # Execute: Run index command
    index_result = run_cli(["index"], tmp_workdir)
    assert_cli_success(index_result)
    
    # Verify: Files are indexed
    context_dir = tmp_workdir / ".midicoder" / "context"
    manifest = json.loads((context_dir / "manifest.json").read_text(encoding="utf-8"))
    assert isinstance(manifest, dict)


def test_index_integration_with_working_dir_config(tmp_workdir: Path) -> None:
    """Integration test: index respects working_dirconfiguration."""
    # Setup: Create subdirectory structure
    src_dir = tmp_workdir / "src"
    src_dir.mkdir()
    (src_dir / "module.py").write_text("class MyClass:\n    pass\n")
    
    # Initialize project
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)
    
    # Configure working_dir
    config_path = tmp_workdir / ".midicoder" / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["working_dir"] = "src"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    
    # Execute: Run index command
    index_result = run_cli(["index"], tmp_workdir)
    assert_cli_success(index_result)
    
    # Verify: Context is created and respects working_dir
    context_dir = tmp_workdir / ".midicoder" / "context"
    manifest = json.loads((context_dir / "manifest.json").read_text(encoding="utf-8"))
    assert isinstance(manifest, dict)


def test_index_integration_reindex_updates_context(tmp_workdir: Path) -> None:
    """Integration test: running index multiple times updates context."""
    # Setup: Initialize and first index
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)
    
    first_index = run_cli(["index"], tmp_workdir)
    assert_cli_success(first_index)
    
    # Add new source file
    src_dir = tmp_workdir / "src"
    src_dir.mkdir(exist_ok=True)
    (src_dir / "new_module.py").write_text("def new_function():\n    pass\n")
    
    # Execute: Re-index
    second_index = run_cli(["index"], tmp_workdir)
    assert_cli_success(second_index)
    
    # Verify: Context files exist and are updated
    context_dir = tmp_workdir / ".midicoder" / "context"
    assert (context_dir / "manifest.json").exists()
    manifest = json.loads((context_dir / "manifest.json").read_text(encoding="utf-8"))
    assert isinstance(manifest, dict)


def test_index_reindex_only_updates_changed_files(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    src_dir = tmp_workdir / "src"
    src_dir.mkdir()
    module_path = src_dir / "module.py"
    untouched_path = src_dir / "untouched.py"
    module_path.write_text("def v1():\n    return 1\n", encoding="utf-8")
    untouched_path.write_text("def keep():\n    return 1\n", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=tmp_workdir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_workdir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_workdir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "."], cwd=tmp_workdir, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "baseline"],
        cwd=tmp_workdir,
        check=True,
        capture_output=True,
        text=True,
    )

    full_index = run_cli(["index"], tmp_workdir)
    assert_cli_success(full_index)
    before_manifest = json.loads((tmp_workdir / ".midicoder" / "context" / "manifest.json").read_text(encoding="utf-8"))
    before_hashes = dict(before_manifest.get("file_hashes", {}))

    module_path.write_text("def v2():\n    return 2\n", encoding="utf-8")

    reindex_result = run_cli(["index", "reindex"], tmp_workdir)
    assert_cli_success(reindex_result)

    after_manifest = json.loads((tmp_workdir / ".midicoder" / "context" / "manifest.json").read_text(encoding="utf-8"))
    after_hashes = dict(after_manifest.get("file_hashes", {}))

    assert "src/module.py" in before_hashes
    assert "src/module.py" in after_hashes
    assert before_hashes["src/module.py"] != after_hashes["src/module.py"]
    assert before_hashes["src/untouched.py"] == after_hashes["src/untouched.py"]


def test_reindex_supports_manual_paths_without_git(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    src_dir = tmp_workdir / "src"
    src_dir.mkdir()
    module_path = src_dir / "module.py"
    module_path.write_text("def v1():\n    return 1\n", encoding="utf-8")

    full_index = run_cli(["index"], tmp_workdir)
    assert_cli_success(full_index)
    before_manifest = json.loads((tmp_workdir / ".midicoder" / "context" / "manifest.json").read_text(encoding="utf-8"))
    before_hashes = dict(before_manifest.get("file_hashes", {}))

    module_path.write_text("def v2():\n    return 2\n", encoding="utf-8")

    reindex_result = run_cli(["index", "reindex", "--path", "src/module.py"], tmp_workdir)
    assert_cli_success(reindex_result)

    after_manifest = json.loads((tmp_workdir / ".midicoder" / "context" / "manifest.json").read_text(encoding="utf-8"))
    after_hashes = dict(after_manifest.get("file_hashes", {}))
    assert before_hashes["src/module.py"] != after_hashes["src/module.py"]


def test_reindex_supports_manual_folder_paths(tmp_workdir: Path) -> None:
    init_result = run_cli(["init"], tmp_workdir)
    assert_cli_success(init_result)

    module_dir = tmp_workdir / "src" / "core"
    module_dir.mkdir(parents=True)
    first = module_dir / "first.py"
    second = module_dir / "second.py"
    first.write_text("def one():\n    return 1\n", encoding="utf-8")
    second.write_text("def two():\n    return 2\n", encoding="utf-8")

    full_index = run_cli(["index"], tmp_workdir)
    assert_cli_success(full_index)
    before_manifest = json.loads((tmp_workdir / ".midicoder" / "context" / "manifest.json").read_text(encoding="utf-8"))
    before_hashes = dict(before_manifest.get("file_hashes", {}))

    first.write_text("def one():\n    return 10\n", encoding="utf-8")
    second.write_text("def two():\n    return 20\n", encoding="utf-8")

    reindex_result = run_cli(["index", "reindex", "--path", "src/core"], tmp_workdir)
    assert_cli_success(reindex_result)

    after_manifest = json.loads((tmp_workdir / ".midicoder" / "context" / "manifest.json").read_text(encoding="utf-8"))
    after_hashes = dict(after_manifest.get("file_hashes", {}))

    assert before_hashes["src/core/first.py"] != after_hashes["src/core/first.py"]
    assert before_hashes["src/core/second.py"] != after_hashes["src/core/second.py"]


def test_reindex_without_git_logs_user_message(tmp_workdir: Path) -> None:
    write_llm_config(tmp_workdir)
    config_path = tmp_workdir / ".midicoder" / "config.json"
    config_payload = json.loads(config_path.read_text(encoding="utf-8"))
    config_payload["working_dir"] = str(tmp_workdir)
    config_path.write_text(json.dumps(config_payload, indent=2), encoding="utf-8")

    src_dir = tmp_workdir / "src"
    src_dir.mkdir()
    module_path = src_dir / "module.py"
    module_path.write_text("def original():\n    return 1\n", encoding="utf-8")

    full_index = run_cli(["index"], tmp_workdir)
    assert_cli_success(full_index)

    module_path.write_text("def updated():\n    return 2\n", encoding="utf-8")

    reindex_result = run_cli(["index", "reindex"], tmp_workdir)
    assert_cli_success(reindex_result)
    assert "Git repository (.git) not found" in reindex_result.stderr
