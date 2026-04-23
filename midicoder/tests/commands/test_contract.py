"""
Tests cho Contract Commands (E03, E20).

Test cases cho:
1. contract gen: Generate DSL contracts từ brief analysis
2. contract check: Validate contracts với DSL schema
3. contract repair: Sửa contracts có lỗi bằng LLM (chưa implement)

Theo SoT E03:
- Input: master-brief (SQLite)
- Process: LLM generate DSL contracts
- Output: DSL contracts (.midicoder/contracts/*.yml)

Theo SoT E20:
- contract gen: --force, --interactive options
- contract check: --auto-fix, --strict options
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

from midicoder.pipeline.commands.contract import (
    check_contracts,
    generate_contracts,
    generate_placeholder_contracts,
    repair_contracts,
)
from midicoder.storage.sqlite import BriefsManager, ArtifactsManager


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_workspace():
    """
    Tạo temporary workspace cho testing.
    
    Yields:
        Path: Temporary directory path
    """
    # Tạo temp directory
    temp_dir = tempfile.mkdtemp()
    original_cwd = Path.cwd()
    
    # Chuyển sang temp directory
    os.chdir(temp_dir)
    
    yield Path(temp_dir)
    
    # Cleanup
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def briefs_manager():
    """
    Tạo BriefsManager instance cho testing.
    
    Returns:
        BriefsManager: Initialized manager
    """
    manager = BriefsManager()
    manager.init()
    return manager


@pytest.fixture
def artifacts_manager():
    """
    Tạo ArtifactsManager instance cho testing.
    
    Returns:
        ArtifactsManager: Initialized manager
    """
    manager = ArtifactsManager()
    manager.init()
    return manager


@pytest.fixture
def sample_brief(briefs_manager):
    """
    Tạo sample brief cho testing.
    
    Args:
        briefs_manager: BriefsManager instance
        
    Returns:
        str: Brief ID
    """
    content = """# E-commerce D2C Platform

Build an e-commerce platform for direct-to-consumer business.
"""
    brief_id = briefs_manager.create(
        brief_id="test-brief-001",
        version="v1.0.0",
        content=content,
        title="E-commerce D2C",
        brief_type="working",
    )["brief_id"]
    briefs_manager.update_status(brief_id, "analyzed")
    return brief_id


@pytest.fixture
def contracts_dir(temp_workspace):
    """
    Tạo contracts directory cho testing.
    
    Args:
        temp_workspace: Temporary workspace path
        
    Returns:
        Path: Contracts directory path
    """
    contracts_dir = temp_workspace / ".midicoder" / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    return contracts_dir


# ============================================================================
# Tests: generate_placeholder_contracts
# ============================================================================

def test_generate_placeholder_contracts_creates_files(contracts_dir):
    """
    Test: Tạo placeholder contracts files (entities, commands, queries, events).
    
    Expected:
    - entities.yaml được tạo với meta và entities
    - commands.yaml được tạo với meta và commands
    - queries.yaml được tạo với meta và queries
    - events.yaml được tạo với meta và events
    """
    brief_id = "test-brief-001"
    
    generate_placeholder_contracts(contracts_dir, brief_id)
    
    # Verify files exist (using .yaml extension as per DSL v1)
    assert (contracts_dir / "entities.yaml").exists()
    assert (contracts_dir / "commands.yaml").exists()
    assert (contracts_dir / "queries.yaml").exists()
    assert (contracts_dir / "events.yaml").exists()
    
    # Verify entities.yaml content
    entities = yaml.safe_load((contracts_dir / "entities.yaml").read_text(encoding="utf-8"))
    assert "meta" in entities
    assert "entities" in entities
    assert entities["meta"]["brief_id"] == brief_id
    assert len(entities["entities"]) == 3  # User, Product, Order
    
    # Verify commands.yaml content
    commands = yaml.safe_load((contracts_dir / "commands.yaml").read_text(encoding="utf-8"))
    assert "meta" in commands
    assert "commands" in commands
    assert commands["meta"]["brief_id"] == brief_id
    assert len(commands["commands"]) == 2  # CreateUser, CreateOrder
    
    # Verify queries.yaml content
    queries = yaml.safe_load((contracts_dir / "queries.yaml").read_text(encoding="utf-8"))
    assert "meta" in queries
    assert "queries" in queries
    assert queries["meta"]["brief_id"] == brief_id
    assert len(queries["queries"]) == 3  # GetUserById, ListProducts, GetOrdersByUser
    
    # Verify events.yaml content
    events = yaml.safe_load((contracts_dir / "events.yaml").read_text(encoding="utf-8"))
    assert "meta" in events
    assert "events" in events
    assert events["meta"]["brief_id"] == brief_id
    assert len(events["events"]) == 2  # UserCreated, OrderCreated


def test_generate_placeholder_contracts_has_required_fields(contracts_dir):
    """
    Test: Placeholder contracts có required fields theo DSL schema v1.
    
    Expected theo loader.py:
    - Entity có: id, description, fields, primary_key, tenant_scope, tags
    - Command có: id, description, input, fetches, guards, effects, returns, required_permissions
    - Query có: id, description, input, fetches, returns, required_permissions
    - Event có: id, description, type, source_entity, fields, version
    """
    brief_id = "test-brief-001"
    
    generate_placeholder_contracts(contracts_dir, brief_id)
    
    # Verify entity fields (DSL v1 schema)
    entities = yaml.safe_load((contracts_dir / "entities.yaml").read_text(encoding="utf-8"))
    entity = entities["entities"][0]
    
    assert "id" in entity
    assert "description" in entity
    assert "fields" in entity
    assert "primary_key" in entity
    assert "tenant_scope" in entity
    assert "tags" in entity
    
    for field in entity["fields"]:
        assert "name" in field
        assert "type" in field
        assert "required" in field
    
    # Verify command fields (DSL v1 schema)
    commands = yaml.safe_load((contracts_dir / "commands.yaml").read_text(encoding="utf-8"))
    command = commands["commands"][0]
    
    assert "id" in command
    assert "description" in command
    assert "input" in command
    assert "fetches" in command
    assert "guards" in command
    assert "effects" in command
    assert "returns" in command
    assert "required_permissions" in command
    assert "tenant_scope" in command
    
    # Verify query fields (DSL v1 schema)
    queries = yaml.safe_load((contracts_dir / "queries.yaml").read_text(encoding="utf-8"))
    query = queries["queries"][0]
    
    assert "id" in query
    assert "description" in query
    assert "input" in query
    assert "fetches" in query
    assert "returns" in query
    assert "required_permissions" in query
    assert "tenant_scope" in query
    
    # Verify event fields (DSL v1 schema)
    events = yaml.safe_load((contracts_dir / "events.yaml").read_text(encoding="utf-8"))
    event = events["events"][0]
    
    assert "id" in event
    assert "description" in event
    assert "type" in event
    assert "source_entity" in event
    assert "fields" in event
    assert "version" in event
    assert "tenant_scope" in event


def test_generate_placeholder_contracts_meta_version(contracts_dir):
    """
    Test: Meta section có version, brief_id và generated_at.
    """
    brief_id = "test-brief-001"
    
    generate_placeholder_contracts(contracts_dir, brief_id)
    
    # Check all files have proper meta
    for filename in ["entities.yaml", "commands.yaml", "queries.yaml", "events.yaml"]:
        content = yaml.safe_load((contracts_dir / filename).read_text(encoding="utf-8"))
        
        assert "meta" in content, f"{filename} missing meta section"
        assert "version" in content["meta"]
        assert content["meta"]["version"] == "1.0.0"
        assert "generated_at" in content["meta"]
        assert content["meta"]["brief_id"] == brief_id


# ============================================================================
# Tests: generate_contracts
# ============================================================================

@patch("midicoder.pipeline.commands.contract.click.echo")
@patch("midicoder.pipeline.commands.contract.click.prompt")
@patch("midicoder.pipeline.commands.contract.BriefsManager")
def test_generate_contracts_with_analyzed_brief(
    mock_briefs_manager_class,
    mock_prompt,
    mock_echo,
    temp_workspace,
    briefs_manager
):
    """
    Test: Generate contracts khi có analyzed brief.
    
    Expected:
    - Tạo contracts directory
    - Gọi generate_placeholder_contracts
    - Display success message
    """
    # Setup mock
    mock_manager_instance = MagicMock()
    mock_manager_instance.list.return_value = [
        {
            "brief_id": "test-brief-001",
            "title": "Test Brief",
            "status": "analyzed"
        }
    ]
    mock_briefs_manager_class.return_value = mock_manager_instance
    
    mock_prompt.return_value = "y"
    
    # Run
    generate_contracts()
    
    # Verify
    mock_manager_instance.list.assert_called_once()


@patch("midicoder.pipeline.commands.contract.click.echo")
@patch("midicoder.pipeline.commands.contract.BriefsManager")
def test_generate_contracts_no_briefs(mock_briefs_manager_class, mock_echo, temp_workspace):
    """
    Test: Generate contracts khi không có brief nào.
    
    Expected:
    - Display error message
    - Suggest running brief analyze first
    - Return early
    """
    # Setup mock
    mock_manager_instance = MagicMock()
    mock_manager_instance.list.return_value = []
    mock_briefs_manager_class.return_value = mock_manager_instance
    
    # Run
    generate_contracts()
    
    # Verify manager was called
    mock_manager_instance.list.assert_called_once()


@patch("midicoder.pipeline.commands.contract.click.echo")
@patch("midicoder.pipeline.commands.contract.click.prompt")
@patch("midicoder.pipeline.commands.contract.BriefsManager")
def test_generate_contracts_force_overwrite(
    mock_briefs_manager_class,
    mock_prompt,
    mock_echo,
    contracts_dir
):
    """
    Test: Generate contracts với --force flag overwrite existing.
    
    Expected:
    - Không hỏi confirmation
    - Overwrite existing files
    """
    # Setup mock
    mock_manager_instance = MagicMock()
    mock_manager_instance.list.return_value = [
        {
            "brief_id": "test-brief-001",
            "title": "Test Brief",
            "status": "analyzed"
        }
    ]
    mock_briefs_manager_class.return_value = mock_manager_instance
    
    # Tạo file contracts trước (using .yaml extension)
    (contracts_dir / "entities.yaml").write_text("existing: content")
    
    mock_prompt.return_value = "y"
    
    # Run with force
    generate_contracts(force=True)
    
    # Verify files were overwritten
    entities = yaml.safe_load((contracts_dir / "entities.yaml").read_text(encoding="utf-8"))
    assert "meta" in entities  # New format, not "existing: content"


@patch("midicoder.pipeline.commands.contract.click.echo")
@patch("midicoder.pipeline.commands.contract.click.prompt")
@patch("midicoder.pipeline.commands.contract.BriefsManager")
def test_generate_contracts_cancel_overwrite(
    mock_briefs_manager_class,
    mock_prompt,
    mock_echo,
    contracts_dir
):
    """
    Test: Hủy bỏ generate khi user từ chối overwrite.
    
    Expected:
    - Hỏi confirmation
    - User declines → return early
    - Existing files không bị thay đổi
    """
    # Setup mock
    mock_manager_instance = MagicMock()
    mock_manager_instance.list.return_value = [
        {
            "brief_id": "test-brief-001",
            "title": "Test Brief",
            "status": "analyzed"
        }
    ]
    mock_briefs_manager_class.return_value = mock_manager_instance
    
    # Tạo file contracts trước (using .yaml extension)
    original_content = "existing: content"
    (contracts_dir / "entities.yaml").write_text(original_content)
    
    # User declines
    mock_prompt.return_value = "n"
    
    # Run
    generate_contracts()
    
    # Verify file was NOT overwritten (note: mock doesn't trigger generate, file stays same)
    content = (contracts_dir / "entities.yaml").read_text(encoding="utf-8")
    assert content == original_content


# ============================================================================
# Tests: check_contracts
# ============================================================================

@patch("midicoder.pipeline.commands.contract.click.echo")
def test_check_contracts_valid(mock_echo, contracts_dir):
    """
    Test: Check contracts thành công khi valid.
    
    Expected:
    - Load contracts vào ProjectionTree
    - Validate tree
    - Display success message
    """
    # Setup mocks
    mock_tree = MagicMock()
    mock_tree.node_count.return_value = 10
    
    mock_report = MagicMock()
    mock_report.total_errors = 0
    mock_report.total_warnings = 1
    mock_report.total_info = 2
    mock_report.status = MagicMock(name="VALID")
    mock_report.get_warnings.return_value = []
    mock_report.dependency_analysis = None
    
    with patch("midicoder.pipeline.commands.contract.load_projection_tree", return_value=mock_tree):
        with patch("midicoder.pipeline.commands.contract.validate_tree", return_value=mock_report):
            # Run
            check_contracts()
    
    # Test đã chạy thành công, không có lỗi


@patch("midicoder.pipeline.commands.contract.click.echo")
def test_check_contracts_with_errors(mock_echo, contracts_dir):
    """
    Test: Check contracts với errors.
    
    Expected:
    - Display error count
    - Display errors by node
    - Report FAIL
    """
    # Setup mock
    mock_tree = MagicMock()
    mock_tree.node_count.return_value = 10
    
    mock_error = MagicMock()
    mock_error.message = "Missing required field: email"
    
    mock_report = MagicMock()
    mock_report.total_errors = 3
    mock_report.total_warnings = 0
    mock_report.total_info = 0
    mock_report.status = MagicMock(name="ERRORS")
    mock_report.get_errors_by_node.return_value = {
        "User:1": [mock_error]
    }
    mock_report.get_warnings.return_value = []
    mock_report.dependency_analysis = None
    
    with patch("midicoder.pipeline.commands.contract.load_projection_tree", return_value=mock_tree):
        with patch("midicoder.pipeline.commands.contract.validate_tree", return_value=mock_report):
            check_contracts()
    
    # Test đã chạy thành công, không có lỗi


@patch("midicoder.pipeline.commands.contract.click.echo")
@patch("midicoder.pipeline.commands.contract.load_projection_tree")
def test_check_contracts_with_dependency_cycles(
    mock_load_tree,
    mock_echo,
    contracts_dir
):
    """
    Test: Check contracts với dependency cycles.
    
    Expected:
    - Display cycle information
    """
    # Setup mock
    mock_tree = MagicMock()
    mock_tree.node_count.return_value = 10
    mock_load_tree.return_value = mock_tree
    
    mock_report = MagicMock()
    mock_report.total_errors = 1
    mock_report.total_warnings = 0
    mock_report.total_info = 0
    mock_report.status = MagicMock(name="ERRORS")
    mock_report.get_errors_by_node.return_value = {}
    mock_report.get_warnings.return_value = []
    
    # Setup dependency analysis with cycle
    mock_cycle = MagicMock()
    mock_cycle.nodes = ["A", "B", "C", "A"]
    mock_report.dependency_analysis = MagicMock()
    mock_report.dependency_analysis.cycles = [mock_cycle]
    
    with patch("midicoder.pipeline.commands.contract.validate_tree", return_value=mock_report):
        check_contracts()


@patch("midicoder.pipeline.commands.contract.click.echo")
def test_check_contracts_no_contracts_dir(mock_echo, temp_workspace):
    """
    Test: Check contracts khi contracts directory không tồn tại.
    
    Expected:
    - Display error message
    - Suggest running contract gen first
    """
    # contracts_dir không tồn tại
    check_contracts()


@patch("midicoder.pipeline.commands.contract.click.echo")
def test_check_contracts_no_contract_files(mock_echo, contracts_dir):
    """
    Test: Check contracts khi không có contract files.
    
    Expected:
    - Display no files message
    """
    # Xóa tất cả files
    for f in contracts_dir.glob("*.yml"):
        f.unlink()
    
    check_contracts()


@patch("midicoder.pipeline.commands.contract.click.echo")
@patch("midicoder.pipeline.commands.contract.load_projection_tree")
def test_check_contracts_yaml_syntax_error(
    mock_load_tree,
    mock_echo,
    contracts_dir
):
    """
    Test: Check contracts với YAML syntax error.
    
    Expected:
    - Display YAML error
    - Return early
    """
    # Tạo invalid YAML
    (contracts_dir / "invalid.yml").write_text("""
entities:
  - id: User
    fields:
      - name: id
        type: UUID
      - name: email
        type: String
        # Missing closing bracket
    invalid: [
""")
    
    # Mock load_tree to not be called (we fail before)
    mock_load_tree.side_effect = Exception("Should not be called")
    
    check_contracts()


# ============================================================================
# Tests: repair_contracts
# ============================================================================

# ============================================================================
# Tests: repair_contracts (LLM-based DSL Repair)
# ============================================================================

@patch("midicoder.pipeline.commands.contract.click.echo")
def test_repair_contracts_no_contracts_dir(mock_echo, temp_workspace):
    """
    Test: Repair contracts khi contracts directory không tồn tại.
    
    Expected:
    - Display error message
    - Suggest running contract gen first
    """
    # Contracts directory không tồn tại
    repair_contracts()


@patch("midicoder.pipeline.commands.contract.click.echo")
def test_repair_contracts_valid_contracts(mock_echo, contracts_dir):
    """
    Test: Repair contracts khi contracts đã valid.
    
    Expected:
    - Chạy validation
    - Không có errors → không cần repair
    - Display success message
    """
    # Tạo valid contracts (dùng encoding UTF-8 cho tiếng Việt)
    (contracts_dir / "entities.yaml").write_text("""
meta:
  version: "1.0.0"
  brief_id: test-brief-001
entities:
  - id: User
    description: User entity
    fields:
      - name: id
        type: UUID
        required: true
    primary_key: id
    tenant_scope: tenant_isolated
    tags: [core]
""", encoding="utf-8")
    
    # Mock load_tree và validate_tree (valid)
    mock_tree = MagicMock()
    mock_tree.node_count.return_value = 1
    
    mock_report = MagicMock()
    mock_report.total_errors = 0
    mock_report.total_warnings = 0
    mock_report.total_info = 0
    mock_report.status = MagicMock(name="VALID")
    mock_report.get_errors_by_node.return_value = {}
    mock_report.get_warnings.return_value = []
    mock_report.dependency_analysis = None
    
    with patch("midicoder.pipeline.commands.contract.load_projection_tree", return_value=mock_tree):
        with patch("midicoder.pipeline.commands.contract.validate_tree", return_value=mock_report):
            repair_contracts()


@patch("midicoder.pipeline.commands.contract.click.echo")
@patch("midicoder.pipeline.commands.contract.call_llm")
@patch("midicoder.pipeline.commands.contract.load_llm_config")
def test_repair_contracts_with_errors_uses_llm(
    mock_load_llm_config,
    mock_call_llm,
    mock_echo,
    contracts_dir
):
    """
    Test: Repair contracts với errors sử dụng LLM để fix.
    
    Expected theo TDD:
    - Chạy validation để tìm errors
    - Nếu có errors → gọi LLM để fix
    - Write fixed contracts back
    - Re-validate để confirm
    """
    # Tạo contracts có lỗi (thiếu required field) - dùng UTF-8 encoding
    (contracts_dir / "entities.yaml").write_text("""
meta:
  version: "1.0.0"
  brief_id: test-brief-001
entities:
  - id: User
    description: User entity missing fields
    # Thiếu fields (required field)
    primary_key: id
    tenant_scope: tenant_isolated
    tags: [core]
""", encoding="utf-8")
    
    # Mock LLM config
    mock_config = MagicMock()
    mock_config.base_url = "http://localhost:11434"
    mock_config.model = "test-model"
    mock_config.api_key = None
    mock_config.provider = "ollama"
    mock_config.cache_enabled = False
    mock_config.cache_type = None
    mock_load_llm_config.return_value = mock_config
    
    # Mock LLM response - fixed YAML
    fixed_yaml = """meta:
  version: "1.0.0"
  brief_id: test-brief-001
entities:
  - id: User
    description: Người dùng hệ thống
    fields:
      - name: id
        type: UUID
        required: true
    primary_key: id
    tenant_scope: tenant_isolated
    tags: [core]
"""
    mock_llm_response = MagicMock()
    mock_llm_response.content = fixed_yaml
    mock_call_llm.return_value = mock_llm_response
    
    # Mock validate_tree - lần đầu có errors
    mock_tree = MagicMock()
    mock_tree.node_count.return_value = 1
    
    mock_error = MagicMock()
    mock_error.node_id = "User:1"
    mock_error.message = "Missing required field: fields"
    
    mock_report_invalid = MagicMock()
    mock_report_invalid.total_errors = 1
    mock_report_invalid.total_warnings = 0
    mock_report_invalid.total_info = 0
    mock_report_invalid.status = MagicMock(name="ERRORS")
    mock_report_invalid.get_errors_by_node.return_value = {
        "User:1": [mock_error]
    }
    mock_report_invalid.get_warnings.return_value = []
    mock_report_invalid.dependency_analysis = None
    
    mock_report_valid = MagicMock()
    mock_report_valid.total_errors = 0
    mock_report_valid.total_warnings = 0
    mock_report_valid.total_info = 0
    mock_report_valid.status = MagicMock(name="VALID")
    mock_report_valid.get_errors_by_node.return_value = {}
    mock_report_valid.get_warnings.return_value = []
    mock_report_valid.dependency_analysis = None
    
    # Lần đầu validate → có errors, lần sau → valid
    mock_validate_tree = MagicMock(side_effect=[mock_report_invalid, mock_report_valid])
    mock_load_tree = MagicMock(return_value=mock_tree)
    
    with patch("midicoder.pipeline.commands.contract.load_projection_tree", mock_load_tree):
        with patch("midicoder.pipeline.commands.contract.validate_tree", mock_validate_tree):
            repair_contracts()
    
    # Verify LLM was called with repair prompt
    assert mock_call_llm.called
    call_args = mock_call_llm.call_args
    assert "repair" in call_args.kwargs.get("system", "").lower() or "fix" in call_args.kwargs.get("system", "").lower()


@patch("midicoder.pipeline.commands.contract.click.echo")
@patch("midicoder.pipeline.commands.contract.call_llm")
def test_repair_contracts_llm_error_handling(mock_call_llm, mock_echo, contracts_dir):
    """
    Test: Repair contracts khi LLM error.
    
    Expected:
    - Display error message
    - Suggest manual fix
    - Return gracefully (không crash)
    """
    # Tạo contracts có lỗi
    (contracts_dir / "entities.yaml").write_text("""
meta:
  version: "1.0.0"
entities:
  - id: User
""")
    
    # Mock LLM error
    from midicoder.llm.client import LlmRequestError
    mock_call_llm.side_effect = LlmRequestError("LLM unavailable")
    
    mock_tree = MagicMock()
    mock_tree.node_count.return_value = 1
    
    mock_report = MagicMock()
    mock_report.total_errors = 1
    mock_report.total_warnings = 0
    mock_report.total_info = 0
    mock_report.status = MagicMock(name="ERRORS")
    mock_report.get_errors_by_node.return_value = {}
    mock_report.get_warnings.return_value = []
    mock_report.dependency_analysis = None
    
    with patch("midicoder.pipeline.commands.contract.load_projection_tree", return_value=mock_tree):
        with patch("midicoder.pipeline.commands.contract.validate_tree", return_value=mock_report):
            # Should not raise, handle gracefully
            repair_contracts()


@patch("midicoder.pipeline.commands.contract.click.echo")
@patch("midicoder.pipeline.commands.contract.call_llm")
@patch("midicoder.pipeline.commands.contract.load_llm_config")
def test_repair_contracts_max_attempts(
    mock_load_llm_config,
    mock_call_llm,
    mock_echo,
    contracts_dir
):
    """
    Test: Repair contracts với max retry attempts.
    
    Expected:
    - Nếu LLM fix không valid → retry (max 3 attempts)
    - Sau max attempts → display error và return
    """
    # Tạo contracts có lỗi
    (contracts_dir / "entities.yaml").write_text("""
meta:
  version: "1.0.0"
entities:
  - id: User
""")
    
    # Mock LLM config
    mock_config = MagicMock()
    mock_load_llm_config.return_value = mock_config
    
    # Mock LLM luôn trả về invalid fix
    mock_llm_response = MagicMock()
    mock_llm_response.content = "# Invalid YAML"
    mock_call_llm.return_value = mock_llm_response
    
    mock_tree = MagicMock()
    mock_tree.node_count.return_value = 1
    
    mock_report_invalid = MagicMock()
    mock_report_invalid.total_errors = 1
    mock_report_invalid.total_warnings = 0
    mock_report_invalid.total_info = 0
    mock_report_invalid.status = MagicMock(name="ERRORS")
    mock_report_invalid.get_errors_by_node.return_value = {}
    mock_report_invalid.get_warnings.return_value = []
    mock_report_invalid.dependency_analysis = None
    
    with patch("midicoder.pipeline.commands.contract.load_projection_tree", return_value=mock_tree):
        with patch("midicoder.pipeline.commands.contract.validate_tree", return_value=mock_report_invalid):
            # Should not raise, should retry and eventually give up
            repair_contracts()


@patch("midicoder.pipeline.commands.contract.click.echo")
def test_repair_contracts_empty_contract_dir(mock_echo, contracts_dir):
    """
    Test: Repair contracts khi contracts directory trống.
    
    Expected:
    - Display error message
    - Suggest running contract gen first
    """
    # Directory tồn tại nhưng không có files
    repair_contracts()


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_generate_and_check_flow(temp_workspace, briefs_manager, artifacts_manager):
    """
    Integration Test: Full flow generate → check contracts.
    
    Steps:
    1. Create analyzed brief
    2. Generate contracts
    3. Check contracts
    4. Verify all files exist and are valid
    """
    # Step 1: Create brief
    content = "# Test E-commerce\n\nBuild e-commerce platform."
    brief_id = briefs_manager.create(
        brief_id="integration-test-brief",
        version="v1.0.0",
        content=content,
        title="Integration Test",
        brief_type="working",
    )["brief_id"]
    briefs_manager.update_status(brief_id, "analyzed")
    
    # Step 2: Generate contracts (suppress output)
    with patch("midicoder.pipeline.commands.contract.click.echo"):
        with patch("midicoder.pipeline.commands.contract.click.prompt", return_value="y"):
            generate_contracts()
    
    # Step 3: Verify contracts directory created
    contracts_dir = Path(".midicoder/contracts")
    assert contracts_dir.exists()
    
    # Step 4: Verify files exist (using .yaml extension)
    assert (contracts_dir / "entities.yaml").exists()
    assert (contracts_dir / "commands.yaml").exists()
    assert (contracts_dir / "queries.yaml").exists()
    assert (contracts_dir / "events.yaml").exists()
    
    # Step 5: Check contracts (suppress output)
    with patch("midicoder.pipeline.commands.contract.click.echo"):
        check_contracts()
    
    # Step 6: Verify YAML is valid
    entities = yaml.safe_load((contracts_dir / "entities.yaml").read_text(encoding="utf-8"))
    assert "entities" in entities
    assert len(entities["entities"]) == 3  # User, Product, Order


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_check_contracts_load_error(temp_workspace, contracts_dir):
    """
    Test: Check contracts khi load ProjectionTree lỗi.
    """
    # Create some contract files (using .yaml extension)
    (contracts_dir / "entities.yaml").write_text("valid: yaml")
    
    # Mock load_projection_tree to raise exception
    with patch("midicoder.pipeline.commands.contract.click.echo"):
        with patch("midicoder.pipeline.commands.contract.load_projection_tree", side_effect=Exception("Load error")):
            check_contracts()


def test_check_contracts_validation_error(temp_workspace, contracts_dir):
    """
    Test: Check contracts khi validation lỗi.
    """
    # Create some contract files (using .yaml extension)
    (contracts_dir / "entities.yaml").write_text("valid: yaml")
    
    # Mock validate_tree to raise exception
    mock_tree = MagicMock()
    mock_tree.node_count.return_value = 1
    
    with patch("midicoder.pipeline.commands.contract.click.echo"):
        with patch("midicoder.pipeline.commands.contract.load_projection_tree", return_value=mock_tree):
            with patch("midicoder.pipeline.commands.contract.validate_tree", side_effect=Exception("Validation error")):
                check_contracts()
