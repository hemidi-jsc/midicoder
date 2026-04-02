"""Stack/target/path resolution for code plan."""

from __future__ import annotations

import os
from pathlib import PurePosixPath
from typing import Any

from .constants import TARGET_MAP_FASTAPI, TARGET_MAP_NEST
from .models import GraphCandidate, GraphEdge, GraphNode, IRPlanItem, SuggestedPath


def resolve_stack(
    profile: dict[str, Any] | None,
    config: dict[str, Any] | None,
    seams: list[dict[str, Any]],
    virtual_seams: list[dict[str, Any]],
) -> tuple[str, str | None]:
    profile_stack = _stack_from_profile(profile)
    if profile_stack:
        return profile_stack, None

    config_stack = _stack_from_config(config)
    if config_stack:
        return config_stack, None

    inferred = _infer_stack_from_files(seams + virtual_seams)
    if inferred:
        return inferred, None

    return "fastapi", "unable to resolve stack; fallback to fastapi"


def map_target(stack: str, kind: str) -> str:
    normalized = kind.lower()
    mapping = TARGET_MAP_NEST if stack == "nest" else TARGET_MAP_FASTAPI
    return mapping.get(normalized, f"{stack}_{normalized}")


def build_dependency_graph(
    seams: list[dict[str, Any]],
    virtual_seams: list[dict[str, Any]],
    ir: dict[str, Any] | None = None,
) -> tuple[list[GraphNode], list[GraphEdge]]:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    seen_files: set[str] = set()

    ordered = list(seams) + list(virtual_seams)
    for idx, seam in enumerate(ordered):
        file_path = _normalize_file(str(seam.get("file", "")))
        if not file_path:
            continue
        if not _is_runtime_candidate(file_path):
            continue
        if file_path in seen_files:
            continue
        seen_files.add(file_path)

        group_id = str(seam.get("group_id", ""))
        seam_kind, seam_module = _parse_group_id(group_id)
        if not seam_kind:
            seam_kind = _infer_kind_from_file(file_path)
        if not seam_module:
            seam_module = _infer_module_from_file(file_path)

        nodes.append(
            GraphNode(
                file=file_path,
                module=seam_module,
                kind=seam_kind,
                symbols=[],
                score_base=0.5 if str(seam.get("kind", "")) == "virtual" else 0.8,
                source_order=idx,
            )
        )

    # Add lightweight nodes from IR symbol index when available.
    if isinstance(ir, dict):
        indexes = ir.get("indexes")
        if isinstance(indexes, dict):
            symbols = indexes.get("symbols")
            if isinstance(symbols, dict):
                for symbol_type, symbol_entries in symbols.items():
                    if not isinstance(symbol_entries, dict):
                        continue
                    inferred_kind = _kind_from_symbol_type(str(symbol_type))
                    for entry in symbol_entries.values():
                        if not isinstance(entry, dict):
                            continue
                        source_file = _normalize_file(str(entry.get("source_file", "")))
                        if not source_file or not _is_runtime_candidate(source_file):
                            continue
                        if source_file in seen_files:
                            continue
                        seen_files.add(source_file)
                        nodes.append(
                            GraphNode(
                                file=source_file,
                                module=_infer_module_from_file(source_file),
                                kind=inferred_kind,
                                symbols=[str(entry.get("id", ""))],
                                score_base=0.3,
                                source_order=len(nodes),
                            )
                        )

    nodes_sorted = sorted(nodes, key=lambda node: (node.source_order, node.file))
    for idx in range(max(len(nodes_sorted) - 1, 0)):
        edges.append(
            GraphEdge(
                from_file=nodes_sorted[idx].file,
                to_file=nodes_sorted[idx + 1].file,
                type="uses",
                weight=1.0,
            )
        )
    return nodes_sorted, edges


def traverse_graph_for_target(
    nodes: list[GraphNode],
    item: IRPlanItem,
) -> list[GraphCandidate]:
    candidates: list[GraphCandidate] = []
    for node in nodes:
        if not _is_runtime_candidate(node.file):
            continue
        if node.kind != item.kind:
            continue
        score = score_candidate(node, item)
        candidates.append(
            GraphCandidate(
                file=node.file,
                module=node.module,
                kind=node.kind,
                source_order=node.source_order,
                score=score,
                distance=0,
            )
        )
    return sort_candidates(candidates)


def score_candidate(node: GraphNode, item: IRPlanItem) -> float:
    kind_match = 5.0 if node.kind == item.kind else 0.0
    module_match = 3.0 if node.module == item.module else 0.0
    path_match = 1.0 if item.module.lower() in node.file.lower() else 0.0
    route_affinity = 1.5 if _route_affinity_match(node.file, item) else 0.0
    reference_affinity = (
        0.5 if item.raw_id.lower() in "/".join(node.symbols).lower() else 0.0
    )
    seam_bonus = node.score_base
    distance_penalty = 0.0
    return (
        kind_match
        + module_match
        + path_match
        + route_affinity
        + reference_affinity
        + seam_bonus
        - distance_penalty
    )


def sort_candidates(candidates: list[GraphCandidate]) -> list[GraphCandidate]:
    return sorted(
        candidates,
        key=lambda item: (-item.score, item.source_order, item.file),
    )


def resolve_suggested_paths(
    *,
    item: IRPlanItem,
    candidates: list[GraphCandidate],
    seams: list[dict[str, Any]],
    virtual_seams: list[dict[str, Any]],
    profile: dict[str, Any] | None,
    stack: str,
) -> tuple[list[SuggestedPath], str]:
    # 0) route-aware resolution for command/query with route contract
    route_paths = _resolve_route_paths(item=item, stack=stack)
    if route_paths:
        return route_paths, "route"

    # 1) graph candidate first
    if candidates:
        top = candidates[0]
        anchor = f"graph:{item.kind}:{item.module}"
        return [
            SuggestedPath(
                file=top.file,
                anchor=anchor,
                reason="best graph candidate",
                score=top.score,
                resolver_source="graph",
                confidence=min(0.99, max(0.0, top.score / 10.0)),
            )
        ], "graph"

    # 2) real seam
    real = _find_matching_seam(seams, item.kind, item.module)
    if real:
        return [
            SuggestedPath(
                file=real["file"],
                anchor=real["anchor"],
                reason="matched real seam by group_id",
                score=0.8,
                resolver_source="real_seam",
                confidence=0.8,
            )
        ], "real_seam"

    # 3) virtual seam
    virtual = _find_matching_seam(virtual_seams, item.kind, item.module)
    if virtual:
        return [
            SuggestedPath(
                file=virtual["file"],
                anchor=virtual["anchor"],
                reason="matched virtual seam by group_id",
                score=0.65,
                resolver_source="virtual_seam",
                confidence=0.65,
            )
        ], "virtual_seam"

    # 4) fallback convention
    fallback_file = fallback_convention_path(item=item, profile=profile, stack=stack)
    return [
        SuggestedPath(
            file=fallback_file,
            anchor=f"fallback:{item.kind}:{item.module}",
            reason="fallback to convention path",
            score=0.25,
            resolver_source="fallback",
            confidence=0.25,
        )
    ], "fallback"


def fallback_convention_path(
    *, item: IRPlanItem, profile: dict[str, Any] | None, stack: str
) -> str:
    module_layout = {}
    if isinstance(profile, dict):
        maybe_layout = profile.get("module_layout")
        if isinstance(maybe_layout, dict):
            module_layout = maybe_layout

    kind_layout = (
        module_layout.get(item.kind)
        if isinstance(module_layout.get(item.kind), str)
        else None
    )
    if kind_layout:
        base_dir = kind_layout.strip("/").strip()
    elif stack == "nest":
        base_dir = f"src/{item.module}"
    else:
        base_dir = f"app/{item.module}"

    if item.kind == "controller":
        name = "controller"
    elif item.kind == "service":
        name = "service"
    elif item.kind == "repository":
        name = "repository"
    elif item.kind == "model":
        name = "model"
    elif item.kind == "route":
        name = "routes"
    elif item.kind == "workflow":
        name = "workflow"
    elif item.kind == "projection":
        name = "projection"
    else:
        name = item.kind

    if stack == "nest":
        return f"{base_dir}/{name}.ts"
    return f"{base_dir}/{name}.py"


def _find_matching_seam(
    items: list[dict[str, Any]], kind: str, module: str
) -> dict[str, str] | None:
    target_group = f"{kind}:{module}"
    for seam in items:
        group_id = str(seam.get("group_id", ""))
        detail = str(seam.get("detail", ""))
        file_path = _normalize_file(str(seam.get("file", "")))
        if not file_path:
            continue

        anchor = ""
        if group_id:
            anchor = (
                f"{'virtual' if seam.get('kind') == 'virtual' else 'seam'}:{group_id}"
            )
        elif detail:
            anchor = detail

        if group_id == target_group:
            if not _is_runtime_candidate(file_path):
                continue
            return {"file": file_path, "anchor": anchor or f"seam:{target_group}"}
    return None


def _resolve_route_paths(item: IRPlanItem, stack: str) -> list[SuggestedPath]:
    routes = (
        item.api_contract.get("routes", [])
        if isinstance(item.api_contract, dict)
        else []
    )
    if not isinstance(routes, list) or not routes:
        return []
    route = sorted(
        [route for route in routes if isinstance(route, dict)],
        key=lambda candidate: (
            candidate.get("source_order", 0) or 0,
            str(candidate.get("method", "")),
            str(candidate.get("path", "")),
        ),
    )[0]
    method = str(route.get("method", "")).upper()
    path = str(route.get("path", ""))
    route_file = _route_to_file(item, stack)
    return [
        SuggestedPath(
            file=route_file,
            anchor=f"route:{method}:{path}",
            reason="resolved from HTTP route contract",
            score=0.92,
            resolver_source="route",
            confidence=0.92,
        )
    ]


def _route_to_file(item: IRPlanItem, stack: str) -> str:
    base_dir = f"src/{item.module}" if stack == "nest" else f"app/{item.module}"
    if item.kind in {"controller", "route"}:
        name = "controller" if item.kind == "controller" else "routes"
    else:
        name = "controller"
    ext = "ts" if stack == "nest" else "py"
    return f"{base_dir}/{name}.{ext}"


def _stack_from_profile(profile: dict[str, Any] | None) -> str | None:
    if not isinstance(profile, dict):
        return None
    raw_stack = profile.get("stack")
    if isinstance(raw_stack, list) and raw_stack:
        head = str(raw_stack[0]).strip().lower()
        if head in {"fastapi", "nest"}:
            return head
    if isinstance(raw_stack, str):
        normalized = raw_stack.strip().lower()
        if normalized in {"fastapi", "nest"}:
            return normalized
    return None


def _stack_from_config(config: dict[str, Any] | None) -> str | None:
    if not isinstance(config, dict):
        return None
    raw_stack = config.get("stack")
    if isinstance(raw_stack, list) and raw_stack:
        head = str(raw_stack[0]).strip().lower()
        if head in {"fastapi", "nest"}:
            return head
    if isinstance(raw_stack, str):
        normalized = raw_stack.strip().lower()
        if normalized in {"fastapi", "nest"}:
            return normalized
    return None


def _infer_stack_from_files(records: list[dict[str, Any]]) -> str | None:
    ts_count = 0
    py_count = 0
    for record in records:
        file_path = _normalize_file(str(record.get("file", "")))
        lower = file_path.lower()
        if lower.endswith(".ts") or lower.endswith(".js"):
            ts_count += 1
        if lower.endswith(".py"):
            py_count += 1
    if ts_count > py_count and ts_count > 0:
        return "nest"
    if py_count > 0:
        return "fastapi"
    return None


def _parse_group_id(group_id: str) -> tuple[str, str]:
    if ":" not in group_id:
        return "", ""
    kind, module = group_id.split(":", 1)
    return kind.strip().lower(), module.strip()


def _infer_kind_from_file(file_path: str) -> str:
    lower = file_path.lower()
    filename = lower.split("/")[-1]
    if "controller" in filename:
        return "controller"
    if "service" in filename:
        return "service"
    if "repository" in filename:
        return "repository"
    if "model" in filename or "entity" in filename:
        return "model"
    if "route" in filename or "/routes/" in lower:
        return "route"
    if "workflow" in filename:
        return "workflow"
    if "projection" in filename:
        return "projection"
    return "service"


def _infer_module_from_file(file_path: str) -> str:
    normalized = file_path.strip("/").replace("\\", "/")
    if not normalized:
        return "core"
    parts = [part for part in normalized.split("/") if part]
    for anchor in ("src", "app", "modules", "domain"):
        if anchor in parts:
            idx = parts.index(anchor)
            if idx + 1 < len(parts):
                return parts[idx + 1]
    if len(parts) > 1:
        return parts[-2]
    stem, _ = os.path.splitext(parts[-1])
    return stem or "core"


def _normalize_file(path: str) -> str:
    if not path.strip():
        return ""
    return str(PurePosixPath(path.replace("\\", "/")))


def _is_runtime_candidate(file_path: str) -> bool:
    lowered = file_path.strip().lower().lstrip("./")
    blocked_prefixes = (
        "midicoder/",
        ".midicoder/",
        "technic/",
        "docs/",
        "tests/",
    )
    if lowered.startswith(blocked_prefixes):
        return False
    blocked_segments = (
        "/code/builder/",
        "/code/bak/",
        "/brief/",
    )
    if any(segment in f"/{lowered}" for segment in blocked_segments):
        return False
    allowed_roots = (
        "app/",
        "src/",
        "domain/",
        "modules/",
        "api/",
        "services/",
        "controllers/",
        "repositories/",
        "workflows/",
    )
    if not lowered.startswith(allowed_roots):
        return False
    if "." in lowered.split("/")[-1]:
        ext = lowered.rsplit(".", 1)[-1]
        if ext not in {"py", "ts", "tsx", "js", "jsx"}:
            return False
    return True


def _route_affinity_match(file_path: str, item: IRPlanItem) -> bool:
    routes = (
        item.api_contract.get("routes", [])
        if isinstance(item.api_contract, dict)
        else []
    )
    if not isinstance(routes, list) or not routes:
        return False
    return item.module.lower() in file_path.lower() and (
        "controller" in file_path.lower() or "route" in file_path.lower()
    )


def _kind_from_symbol_type(symbol_type: str) -> str:
    lowered = symbol_type.strip().lower()
    if lowered == "command":
        return "controller"
    if lowered == "query":
        return "service"
    if lowered == "entity":
        return "model"
    if lowered == "workflow":
        return "workflow"
    if lowered == "projection":
        return "projection"
    return "service"
