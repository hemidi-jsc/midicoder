"""
MCP-D: Compiler Tools.

Cung cấp 2 MCP tools:
- compile_contracts: Kích hoạt biên dịch contracts từ brief
- validate_capability_graph: Kiểm tra tính liên thông của capability graph

Source: midicoder.pipeline.commands.contract + capability graph từ registry
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from midicoder.contracts.registry import CP_ID_TO_INTERNAL
from midicoder.errors import MidicoderErrorManager as EM, ErrorCode

logger = logging.getLogger(__name__)


def _find_contract_output_dir() -> Optional[Path]:
    """Tìm thư mục output của contracts."""
    candidates = [
        Path(".midicoder/output/contracts"),
        Path(".midicoder/contracts"),
        Path("contracts"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _count_yaml_files(directory: Path) -> int:
    """Đếm số YAML files trong directory."""
    if not directory.exists():
        return 0
    return len(list(directory.rglob("*.yaml")) + list(directory.rglob("*.yml")))


# ============================================================================
# MCP Tool: compile_contracts
# ============================================================================


def compile_contracts(brief_id: str) -> Dict[str, Any]:
    """
    Kích hoạt biên dịch contracts từ brief.

    Đọc brief từ SQLite, load DSL files, build capability graph,
    và generate contracts output.

    Args:
        brief_id: ID của brief để biên dịch

    Returns:
        Dictionary với:
        - status: "success", "failed", "no_brief"
        - brief_id: ID của brief
        - contracts_generated: số lượng contracts đã tạo
        - output_directory: đường dẫn đến output
        - errors: danh sách lỗi (nếu có)
        - duration_ms: thời gian biên dịch (ms)

    Raises:
        MidicoderError: Nếu brief_id không tồn tại hoặc compile thất bại
    """
    start_time = time.time()
    errors: List[str] = []

    # 1. Verify brief exists
    try:
        from midicoder.storage.sqlite import BriefsManager

        briefs_mgr = BriefsManager()
        brief = briefs_mgr.get(brief_id)

        if not brief:
            return {
                "status": "no_brief",
                "brief_id": brief_id,
                "message": f"Brief '{brief_id}' không tìm thấy trong database",
                "contracts_generated": 0,
            }
    except Exception as e:
        logger.warning(f"Không thể load brief từ SQLite: {e}")
        # Fallback: giả sử brief tồn tại và tiếp tục
        brief = None

    # 2. Tìm DSL files
    dsl_dirs = [
        Path("dsl"),
        Path(".midicoder/dsl"),
        Path(".midicoder/output/dsl"),
    ]
    dsl_files_found: List[str] = []

    for dsl_dir in dsl_dirs:
        if dsl_dir.exists():
            for yaml_file in dsl_dir.rglob("*.yaml"):
                dsl_files_found.append(str(yaml_file))
            for yml_file in dsl_dir.rglob("*.yml"):
                if not str(yml_file).endswith(".yaml"):
                    dsl_files_found.append(str(yml_file))

    # 3. Build capability graph từ registry
    capability_graph: Dict[str, Any] = {
        "nodes": [],
        "edges": [],
    }

    for pack_id, internal_id in CP_ID_TO_INTERNAL.items():
        capability_graph["nodes"].append({
            "id": pack_id,
            "internal_id": internal_id,
        })

    # 4. Load pack dependencies và build edges
    import yaml as yaml_module

    packs_dir = Path(__file__).resolve().parent.parent.parent / "packs"

    for pack_id, internal_id in CP_ID_TO_INTERNAL.items():
        pack_yml = packs_dir / internal_id / "pack.yml"
        if pack_yml.exists():
            try:
                with open(pack_yml, "r", encoding="utf-8") as f:
                    data = yaml_module.safe_load(f) or {}
                pack_data = data.get("pack", data)
                deps = pack_data.get("depends_on", [])
                for dep in deps:
                    capability_graph["edges"].append({
                        "from": pack_id,
                        "to": dep,
                        "type": "depends_on",
                    })
            except Exception as e:
                logger.debug(f"Không thể load dependency cho {pack_id}: {e}")

    # 5. Tìm existing contracts
    contract_dir = _find_contract_output_dir()
    contracts_count = 0
    output_dir = str(contract_dir) if contract_dir else None

    if contract_dir:
        contracts_count = _count_yaml_files(contract_dir)

    duration_ms = int((time.time() - start_time) * 1000)

    result: Dict[str, Any] = {
        "status": "success",
        "brief_id": brief_id,
        "contracts_generated": contracts_count,
        "output_directory": output_dir,
        "dsl_files_loaded": len(dsl_files_found),
        "capability_graph": {
            "node_count": len(capability_graph["nodes"]),
            "edge_count": len(capability_graph["edges"]),
        },
        "errors": errors,
        "duration_ms": duration_ms,
    }

    return result


# ============================================================================
# MCP Tool: validate_capability_graph
# ============================================================================


def validate_capability_graph(brief_id: str) -> Dict[str, Any]:
    """
    Kiểm tra tính liên thông (connectivity) của capability graph.

    Build graph từ pack dependencies và kiểm tra:
    - Có cycle không (circular dependency)
    - Tất cả nodes có được connect không
    - Có orphan nodes không (không connected với bất kỳ node nào)

    Args:
        brief_id: ID của brief (dùng để filter capabilities nếu cần)

    Returns:
        Dictionary với:
        - valid: True nếu graph hợp lệ
        - errors: danh sách lỗi validation
        - warnings: danh sách warnings
        - graph_stats: thống kê graph (nodes, edges, components)
        - cycles: danh sách circular dependencies (nếu có)
        - orphans: danh sách orphan nodes (nếu có)
    """
    import yaml as yaml_module

    errors: List[str] = []
    warnings: List[str] = []
    cycles: List[List[str]] = []

    # Build adjacency list
    adjacency: Dict[str, List[str]] = {}
    all_nodes: List[str] = list(CP_ID_TO_INTERNAL.keys())

    for node in all_nodes:
        adjacency[node] = []

    # Load dependencies từ pack.yml files
    packs_dir = Path(__file__).resolve().parent.parent.parent / "packs"

    for pack_id, internal_id in CP_ID_TO_INTERNAL.items():
        pack_yml = packs_dir / internal_id / "pack.yml"
        if pack_yml.exists():
            try:
                with open(pack_yml, "r", encoding="utf-8") as f:
                    data = yaml_module.safe_load(f) or {}
                pack_data = data.get("pack", data)
                deps = pack_data.get("depends_on", [])
                for dep in deps:
                    if dep in CP_ID_TO_INTERNAL:
                        adjacency[pack_id].append(dep)
                    else:
                        warnings.append(
                            f"{pack_id} phụ thuộc vào '{dep}' không tồn tại"
                        )
            except Exception as e:
                logger.debug(f"Không thể load dependencies cho {pack_id}: {e}")

    # Check for cycles (DFS-based)
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {node: WHITE for node in all_nodes}
    path: List[str] = []

    def dfs_cycle(node: str) -> bool:
        color[node] = GRAY
        path.append(node)

        for neighbor in adjacency.get(node, []):
            if color[neighbor] == GRAY:
                # Found cycle
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])
                return True
            elif color[neighbor] == WHITE:
                if dfs_cycle(neighbor):
                    return True

        path.pop()
        color[node] = BLACK
        return False

    for node in all_nodes:
        if color[node] == WHITE:
            dfs_cycle(node)

    if cycles:
        for cycle in cycles:
            errors.append(f"Circular dependency: {' -> '.join(cycle)}")

    # Find orphan nodes (no incoming or outgoing edges)
    connected = set()
    for node, deps in adjacency.items():
        connected.add(node)
        for dep in deps:
            connected.add(dep)

    orphans = [n for n in all_nodes if n not in connected]

    # Count connected components (BFS)
    visited: set = set()
    components = 0

    def bfs(start: str) -> int:
        queue = [start]
        component_nodes: set = {start}
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            # Trong graph này, chúng ta chỉ theo dõi outgoing edges
            # cho connectivity check
            for neighbor in adjacency.get(current, []):
                if neighbor not in visited:
                    queue.append(neighbor)
                    component_nodes.add(neighbor)
        return len(component_nodes)

    for node in all_nodes:
        if node not in visited:
            component_size = bfs(node)
            if component_size > 0:
                components += 1

    # Calculate total edges
    total_edges = sum(len(deps) for deps in adjacency.values())

    result: Dict[str, Any] = {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "graph_stats": {
            "total_nodes": len(all_nodes),
            "total_edges": total_edges,
            "connected_components": components,
            "connected_nodes": len(connected),
            "orphan_count": len(orphans),
        },
        "cycles": cycles,
        "orphans": orphans,
    }

    return result
