# coding: utf-8
"""
Recipes cho Blueprint Composition Engine (CP51).

Recipe = 1-level pattern macro — concrete value assignment đến patterns
trong models.py. Không nest, không domain-specific.

Mỗi recipe trả về một dictionary chứa các pattern instances đã được
configure với concrete values phù hợp với use case cụ thể.

Recipes:
- FullStackBlueprintRecipe: Full-stack app (frontend + backend + database)
- BackendOnlyRecipe: Backend-only API service
- FrontendOnlyRecipe: Frontend-only SPA/PWA
- MicroserviceBlueprintRecipe: Microservice architecture
- MonolithRecipe: Monolithic application

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any

from midicoder.packs.cp51_blueprint.models import (
    BlueprintSchema,
    CapabilityGraph,
    CapabilityNode,
    ConflictResolution,
    MergeMode,
    MergeStrategy,
    Resolution,
    ResolutionStatus,
    VersionConstraint,
)


# ===========================================================================
# P0 mandatory packs (luôn có trong mọi blueprint)
# ===========================================================================

P0_PACKS = [
    ("CP01", "core", ["domain_model"], []),
    ("CP02", "core", ["multi_tenant"], ["CP01"]),
    ("CP03", "core", ["authentication"], ["CP01", "CP02"]),
    ("CP04", "core", ["authorization", "rbac"], ["CP02", "CP03"]),
    ("CP07", "core", ["error_handling"], []),
]


def _make_nodes(packs: list[tuple[str, str, list[str], list[str]]]) -> list[CapabilityNode]:
    """Tạo danh sách CapabilityNode từ pack specs."""
    return [
        CapabilityNode(
            pack_id=pack_id,
            pack_type=pack_type,
            capabilities=caps,
            depends_on=deps,
        )
        for pack_id, pack_type, caps, deps in packs
    ]


def _make_graph(nodes: list[CapabilityNode]) -> CapabilityGraph:
    """Tạo CapabilityGraph từ nodes — edges được infer từ depends_on."""
    edges: list[tuple[str, str]] = []
    for node in nodes:
        for dep in node.depends_on:
            edges.append((node.pack_id, dep))
    return CapabilityGraph(nodes=nodes, edges=edges)


def _default_schema() -> BlueprintSchema:
    """Default blueprint schema."""
    return BlueprintSchema(
        schema_version="1.0.0",
        min_compatible_version="1.0.0",
        max_compatible_version="2.0.0",
    )


def _default_resolution(graph: CapabilityGraph) -> Resolution:
    """Tạo resolution từ graph (giả sử tất cả resolve thành công)."""
    return Resolution(
        status=ResolutionStatus.RESOLVED,
        resolved_packs=[n.pack_id for n in graph.nodes],
        topological_order=graph.get_topological_order(),
    )


# ===========================================================================
# FullStackBlueprintRecipe
# ===========================================================================


def FullStackBlueprintRecipe() -> dict[str, Any]:
    """
    Full-stack web application blueprint.

    Bao gồm: frontend (React/Angular) + backend (FastAPI/NestJS) + database
    + tất cả P0 mandatory packs + P1 packs cho full capability.

    Returns:
        Dictionary chứa: graph, schema, resolution, merge_strategy, constraints
    """
    # P0 mandatory + P1 packs cho full-stack
    packs = P0_PACKS + [
        ("CP05", "core", ["eventing", "events"], ["CP01"]),
        ("CP06", "core", ["api_gateway", "gateway", "routing"], ["CP01", "CP05"]),
        ("CP08", "core", ["database", "data_access"], ["CP01"]),
        ("CP09", "core", ["caching"], ["CP08"]),
        ("CP10", "core", ["search"], ["CP08"]),
        ("CP11", "core", ["file_storage"], ["CP07"]),
        ("CP12", "core", ["notification"], ["CP05"]),
        ("CP13", "core", ["workflow"], ["CP05"]),
        ("CP14", "core", ["audit"], ["CP01"]),
        ("CP15", "core", ["observability"], ["CP07"]),
        ("CP18", "core", ["frontend"], ["CP01"]),
        ("CP19", "core", ["ui"], ["CP18"]),
        ("CP20", "core", ["api_client"], ["CP06", "CP18"]),
    ]

    nodes = _make_nodes(packs)
    graph = _make_graph(nodes)
    schema = _default_schema()
    resolution = _default_resolution(graph)

    merge_strategy = MergeStrategy(
        mode=MergeMode.TOPOLOGICAL,
        priority_map={
            "CP01": 100,
            "CP02": 90,
            "CP03": 85,
            "CP04": 80,
            "CP07": 95,
        },
    )

    # Version constraints cho P0 packs
    constraints = [
        VersionConstraint(pack_id=cp, min_version="1.0.0", max_version="2.0.0")
        for cp, _, _, _ in P0_PACKS
    ]

    return {
        "name": "full_stack_blueprint",
        "graph": graph,
        "schema": schema,
        "resolution": resolution,
        "merge_strategy": merge_strategy,
        "constraints": constraints,
        "capabilities": graph.get_all_capabilities(),
    }


# ===========================================================================
# BackendOnlyRecipe
# ===========================================================================


def BackendOnlyRecipe() -> dict[str, Any]:
    """
    Backend-only API service blueprint.

    Bao gồm: backend (FastAPI/NestJS) + database + P0 mandatory + core
    backend packs. Không có frontend/UI packs.

    Returns:
        Dictionary chứa: graph, schema, resolution, merge_strategy, constraints
    """
    # P0 mandatory + backend-only P1 packs
    packs = P0_PACKS + [
        ("CP05", "core", ["eventing", "events"], ["CP01"]),
        ("CP06", "core", ["api_gateway", "gateway", "routing"], ["CP01", "CP05"]),
        ("CP08", "core", ["database", "data_access"], ["CP01"]),
        ("CP09", "core", ["caching"], ["CP08"]),
        ("CP10", "core", ["search"], ["CP08"]),
        ("CP11", "core", ["file_storage"], ["CP07"]),
        ("CP12", "core", ["notification"], ["CP05"]),
        ("CP13", "core", ["workflow"], ["CP05"]),
        ("CP14", "core", ["audit"], ["CP01"]),
        ("CP15", "core", ["observability"], ["CP07"]),
    ]

    nodes = _make_nodes(packs)
    graph = _make_graph(nodes)
    schema = _default_schema()
    resolution = _default_resolution(graph)

    merge_strategy = MergeStrategy(
        mode=MergeMode.TOPOLOGICAL,
        priority_map={
            "CP01": 100,
            "CP07": 95,
            "CP08": 90,
        },
    )

    constraints = [
        VersionConstraint(pack_id=cp, min_version="1.0.0", max_version="2.0.0")
        for cp, _, _, _ in P0_PACKS
    ]

    return {
        "name": "backend_only_blueprint",
        "graph": graph,
        "schema": schema,
        "resolution": resolution,
        "merge_strategy": merge_strategy,
        "constraints": constraints,
        "capabilities": graph.get_all_capabilities(),
    }


# ===========================================================================
# FrontendOnlyRecipe
# ===========================================================================


def FrontendOnlyRecipe() -> dict[str, Any]:
    """
    Frontend-only SPA/PWA blueprint.

    Bao gồm: frontend (React/Angular) + UI + API client để communicate
    với external backend. Có P0 mandatory cho domain model + auth.

    Returns:
        Dictionary chứa: graph, schema, resolution, merge_strategy, constraints
    """
    # P0 mandatory + frontend-only packs
    packs = P0_PACKS + [
        ("CP18", "core", ["frontend"], ["CP01"]),
        ("CP19", "core", ["ui"], ["CP18"]),
        ("CP20", "core", ["api_client"], ["CP06", "CP18"]),
    ]

    nodes = _make_nodes(packs)
    graph = _make_graph(nodes)
    schema = _default_schema()
    resolution = _default_resolution(graph)

    merge_strategy = MergeStrategy(
        mode=MergeMode.TOPOLOGICAL,
        priority_map={
            "CP01": 100,
            "CP18": 90,
            "CP19": 85,
        },
    )

    constraints = [
        VersionConstraint(pack_id=cp, min_version="1.0.0", max_version="2.0.0")
        for cp, _, _, _ in P0_PACKS
    ]

    return {
        "name": "frontend_only_blueprint",
        "graph": graph,
        "schema": schema,
        "resolution": resolution,
        "merge_strategy": merge_strategy,
        "constraints": constraints,
        "capabilities": graph.get_all_capabilities(),
    }


# ===========================================================================
# MicroserviceBlueprintRecipe
# ===========================================================================


def MicroserviceBlueprintRecipe() -> dict[str, Any]:
    """
    Microservice architecture blueprint.

    Bao gồm: backend service + event-driven communication + API gateway
    + observability + independent database per service.

    Returns:
        Dictionary chứa: graph, schema, resolution, merge_strategy, constraints
    """
    # P0 mandatory + microservice-essential packs
    packs = P0_PACKS + [
        ("CP05", "core", ["eventing", "events"], ["CP01"]),
        ("CP06", "core", ["api_gateway", "gateway", "routing"], ["CP01", "CP05"]),
        ("CP08", "core", ["database", "data_access"], ["CP01"]),
        ("CP11", "core", ["file_storage"], ["CP07"]),
        ("CP12", "core", ["notification"], ["CP05"]),
        ("CP13", "core", ["workflow"], ["CP05"]),
        ("CP14", "core", ["audit"], ["CP01"]),
        ("CP15", "core", ["observability"], ["CP07"]),
        ("CP16", "core", ["monitoring"], ["CP15"]),
        ("CP20", "core", ["api_client"], ["CP06", "CP18"]),
    ]

    nodes = _make_nodes(packs)
    graph = _make_graph(nodes)
    schema = _default_schema()
    resolution = _default_resolution(graph)

    merge_strategy = MergeStrategy(
        mode=MergeMode.PRIORITY_BASED,
        priority_map={
            "CP01": 100,
            "CP05": 95,   # Eventing is critical for microservices
            "CP06": 90,   # API Gateway is critical
            "CP07": 95,
            "CP15": 85,   # Observability is important
        },
    )

    constraints = [
        VersionConstraint(pack_id=cp, min_version="1.0.0", max_version="2.0.0")
        for cp, _, _, _ in P0_PACKS
    ]

    return {
        "name": "microservice_blueprint",
        "graph": graph,
        "schema": schema,
        "resolution": resolution,
        "merge_strategy": merge_strategy,
        "constraints": constraints,
        "capabilities": graph.get_all_capabilities(),
    }


# ===========================================================================
# MonolithRecipe
# ===========================================================================


def MonolithRecipe() -> dict[str, Any]:
    """
    Monolithic application blueprint.

    Bao gồm: tất cả packs trong một single deployment unit. Simple,
    straightforward — phù hợp cho small/medium apps.

    Returns:
        Dictionary chứa: graph, schema, resolution, merge_strategy, constraints
    """
    # P0 mandatory + all P1 packs
    packs = P0_PACKS + [
        ("CP05", "core", ["eventing", "events"], ["CP01"]),
        ("CP06", "core", ["api_gateway", "gateway", "routing"], ["CP01", "CP05"]),
        ("CP08", "core", ["database", "data_access"], ["CP01"]),
        ("CP09", "core", ["caching"], ["CP08"]),
        ("CP10", "core", ["search"], ["CP08"]),
        ("CP11", "core", ["file_storage"], ["CP07"]),
        ("CP12", "core", ["notification"], ["CP05"]),
        ("CP13", "core", ["workflow"], ["CP05"]),
        ("CP14", "core", ["audit"], ["CP01"]),
        ("CP15", "core", ["observability"], ["CP07"]),
        ("CP16", "core", ["monitoring"], ["CP15"]),
        ("CP17", "core", ["analytics", "bi"], ["CP08", "CP15"]),
        ("CP18", "core", ["frontend"], ["CP01"]),
        ("CP19", "core", ["ui"], ["CP18"]),
        ("CP20", "core", ["api_client"], ["CP06", "CP18"]),
    ]

    nodes = _make_nodes(packs)
    graph = _make_graph(nodes)
    schema = _default_schema()
    resolution = _default_resolution(graph)

    merge_strategy = MergeStrategy(
        mode=MergeMode.MERGE_ALL,
        priority_map={
            "CP01": 100,
            "CP07": 95,
        },
    )

    constraints = [
        VersionConstraint(pack_id=cp, min_version="1.0.0", max_version="2.0.0")
        for cp, _, _, _ in P0_PACKS
    ]

    return {
        "name": "monolith_blueprint",
        "graph": graph,
        "schema": schema,
        "resolution": resolution,
        "merge_strategy": merge_strategy,
        "constraints": constraints,
        "capabilities": graph.get_all_capabilities(),
    }


__all__ = [
    "FullStackBlueprintRecipe",
    "BackendOnlyRecipe",
    "FrontendOnlyRecipe",
    "MicroserviceBlueprintRecipe",
    "MonolithRecipe",
]
