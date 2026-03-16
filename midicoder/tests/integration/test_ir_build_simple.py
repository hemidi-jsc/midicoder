"""Integration test for IR build with simple contracts."""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from midicoder.ir.builder import build_ir


@pytest.fixture
def temp_repo():
    """Create a temporary repository with simple contracts."""
    temp_dir = tempfile.mkdtemp()
    repo_path = Path(temp_dir)
    
    # Create .midicoder structure
    version = "0.1.0"
    contracts_dir = repo_path / ".midicoder" / "versions" / version / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy simple contracts
    fixture_path = Path(__file__).parent.parent / "fixtures" / "contracts" / "simple"
    
    if fixture_path.exists():
        shutil.copytree(fixture_path, contracts_dir, dirs_exist_ok=True)
    
    yield repo_path, version
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_ir_build_simple_success(temp_repo):
    """Test IR build with valid simple contracts."""
    repo_path, version = temp_repo
    
    # Build IR
    build_ir(version, repo_root=str(repo_path))
    
    # Check outputs exist
    ir_path = repo_path / ".midicoder" / "versions" / version / "irs" / "ir.json"
    manifest_path = repo_path / ".midicoder" / "versions" / version / "irs" / "manifest.json"
    
    assert ir_path.exists(), "IR JSON should be created"
    assert manifest_path.exists(), "Manifest should be created"
    
    # Load and validate IR
    with open(ir_path, "r", encoding="utf-8") as f:
        ir = json.load(f)
    
    assert ir["version"] == version
    assert "modules" in ir
    assert "domain" in ir["modules"]
    assert "application" in ir["modules"]
    assert "api" in ir["modules"]
    
    # Check domain module
    domain = ir["modules"]["domain"]
    assert len(domain["entities"]) == 2, "Should have 2 entities"
    assert len(domain["errors"]) == 3, "Should have 3 errors"
    
    # Check entity details
    entity_ids = [e["id"] for e in domain["entities"]]
    assert "user" in entity_ids
    assert "organization" in entity_ids
    
    user_entity = next(e for e in domain["entities"] if e["id"] == "user")
    assert user_entity["primary_key"] == "id"
    assert len(user_entity["fields"]) == 4
    assert len(user_entity["indexes"]) == 1
    
    # Check application module
    application = ir["modules"]["application"]
    assert len(application["commands"]) == 2, "Should have 2 commands"
    
    command_ids = [c["id"] for c in application["commands"]]
    assert "create_user" in command_ids
    assert "update_user_profile" in command_ids
    
    create_user_cmd = next(c for c in application["commands"] if c["id"] == "create_user")
    assert len(create_user_cmd["input"]) == 3
    assert len(create_user_cmd["fetches"]) == 1
    assert create_user_cmd["fetches"][0]["id"] == "organization"
    assert len(create_user_cmd["errors"]) == 2
    
    # Check API module
    api = ir["modules"]["api"]
    assert api["http"] is not None
    assert len(api["http"]["routes"]) == 2, "Should have 2 HTTP routes"
    
    # Check manifest
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    assert manifest["status"] == "success"
    assert manifest["version"] == version
    assert "stats" in manifest
    assert manifest["stats"]["entities"] == 2
    assert manifest["stats"]["commands"] == 2
    assert manifest["stats"]["http_routes"] == 2


def test_ir_build_with_missing_reference(temp_repo):
    """Test IR build fails with unresolved reference."""
    repo_path, version = temp_repo
    
    # Modify existing commands.yaml to add invalid reference
    commands_file = (
        repo_path / ".midicoder" / "versions" / version / "contracts" / "app" / "commands.yaml"
    )
    
    with open(commands_file, "a", encoding="utf-8") as f:
        f.write("""
  - id: delete_user
    description: Delete user
    input:
      - name: user_id
        type: uuid
        required: true
    returns: []
    fetches:
      - non_existent_entity
    guards: []
    effects: []
    errors: []
    emits: []
""")
    
    # Build should fail with cross-reference error
    with pytest.raises(RuntimeError, match="IR build failed"):
        build_ir(version, repo_root=str(repo_path))
    
    # Manifest should exist with errors
    manifest_path = repo_path / ".midicoder" / "versions" / version / "irs" / "manifest.json"
    assert manifest_path.exists()
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    assert manifest["status"] == "failed"
    assert len(manifest["errors"]) > 0
    # Should have unresolved entity reference error
    assert any("non_existent_entity" in str(e) for e in manifest["errors"])


def test_ir_build_with_duplicate_id(temp_repo):
    """Test IR build fails with duplicate ID."""
    repo_path, version = temp_repo
    
    # Add entity with duplicate ID
    entities_file = (
        repo_path / ".midicoder" / "versions" / version / "contracts" / "domain" / "entities.yaml"
    )
    
    with open(entities_file, "a", encoding="utf-8") as f:
        f.write("""
  - id: user
    description: Duplicate user entity
    fields:
      - name: id
        type: uuid
        required: true
    primary_key: id
""")
    
    # Build should fail with validation errors (duplicate ID detected in lint phase)
    with pytest.raises(RuntimeError, match="IR build failed"):
        build_ir(version, repo_root=str(repo_path))
    
    # Check manifest has error
    manifest_path = repo_path / ".midicoder" / "versions" / version / "irs" / "manifest.json"
    assert manifest_path.exists()
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    assert manifest["status"] == "failed"
    assert len(manifest["errors"]) > 0
    # Should have duplicate ID error
    assert any("Duplicate" in e.get("message", "") for e in manifest["errors"])
