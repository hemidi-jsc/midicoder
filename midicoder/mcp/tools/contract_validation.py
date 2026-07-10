"""
MCP-G: Contract Validation Tools.

Cung cấp 4 MCP tools cho LLM agent tự xác thực contract trong quá trình generate:
- validate_contract_yaml: Validate YAML + DSL constraints của 1 category
- cross_check_category: Cross-reference với các category đã generate
- verify_structural_fidelity: So sánh contract YAML với analysis data (detect drifts)
- get_generated_artifact: Lấy nội dung artifact đã tồn tại

Tất cả đều delegate đến midicoder.pipeline.commands.contract để tránh duplicate logic.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


# ============================================================================
# MCP Tool: validate_contract_yaml
# ============================================================================


def validate_contract_yaml(category: str, yaml_content: str) -> Dict[str, Any]:
    """
    Validate YAML + DSL constraints của một category contract.

    LLM dùng tool này để tự kiểm tra contract trước khi hoàn tất.
    Delegate đến midicoder.pipeline.commands.contract._validate_single_category().

    Args:
        category: Tên category (entities, commands, queries, events, workflows, value_objects, guards, roles, ui_components)
        yaml_content: Raw YAML string cần validate

    Returns:
        Dictionary với:
        - status: "valid", "warnings", "errors", "error"
        - is_valid: True nếu không có errors
        - yaml_valid: True nếu YAML parse thành công
        - total_errors: số lỗi
        - total_warnings: số cảnh báo
        - errors: list chi tiết lỗi (constraint_id, level, message, node_id)
        - warnings: list chi tiết warnings
    """
    from midicoder.pipeline.commands.contract import _validate_single_category
    return _validate_single_category(category, yaml_content)


# ============================================================================
# MCP Tool: cross_check_category
# ============================================================================


def cross_check_category(category: str, yaml_content: str) -> Dict[str, Any]:
    """
    Cross-reference một category với các category đã generate trong SQLite.

    Kiểm tra các references giữa categories:
    - Commands/Queries tham chiếu entities → entities phải tồn tại
    - Commands tham chiếu events → events phải tồn tại
    - Guards tham chiếu roles → roles phải tồn tại
    - Workflows tham chiếu commands → commands phải tồn tại

    Delegate đến midicoder.pipeline.commands.contract._cross_check_category().

    Args:
        category: Tên category đang check
        yaml_content: Raw YAML string của category này

    Returns:
        Dictionary với:
        - valid: True nếu không có errors
        - errors: list lỗi cross-reference
        - warnings: list warnings (không blocking)
        - checked_references: số references đã check
    """
    from midicoder.pipeline.commands.contract import _cross_check_category
    return _cross_check_category(category, yaml_content)


# ============================================================================
# MCP Tool: get_generated_artifact
# ============================================================================


def get_generated_artifact(category: str) -> Dict[str, Any]:
    """
    Lấy nội dung artifact đã generate từ SQLite cho một category.

    Dùng để LLM xem nội dung category đã generate trước đó
    khi cần cross-check hoặc tham khảo.

    Delegate đến midicoder.pipeline.commands.contract._get_artifact_for_category().

    Args:
        category: Tên category (entities, commands, queries, events, workflows, value_objects, guards, roles, ui_components)

    Returns:
        Dictionary với:
        - found: True nếu artifact tồn tại
        - content: Raw YAML string (nếu found)
        - artifact_id: ID của artifact trong DB
        - metadata: Metadata của artifact
        - name: Tên display của artifact
    """
    from midicoder.pipeline.commands.contract import _get_artifact_for_category
    return _get_artifact_for_category(category)


# ============================================================================
# MCP Tool: verify_structural_fidelity
# ============================================================================


def verify_structural_fidelity(category: str, yaml_content: str) -> Dict[str, Any]:
    """
    So sánh contract YAML với analysis data để phát hiện structural drifts.

    Detects:
    - missing_fields: fields có trong analysis nhưng thiếu trong contract
    - missing_node: analysis item không có contract node tương ứng
    - missing_items: permissions/inputs/effects thiếu trong contract
    - target_mismatch: target entity không khớp
    - value_mismatch: type/triggers khác nhau

    Delegate đến midicoder.pipeline.commands.contract._verify_structural_fidelity().

    Args:
        category: Tên category đang verify
        yaml_content: Raw YAML string của contract đang kiểm tra

    Returns:
        Dictionary với:
        - has_drifts: True nếu có drifts
        - drift_count: Số drifts tìm thấy
        - drifts: List chi tiết (drift_type, analysis_field, details, severity)
        - summary: Text summary ngắn gọn
    """
    from midicoder.pipeline.commands.contract import _verify_structural_fidelity
    return _verify_structural_fidelity(category, yaml_content)
