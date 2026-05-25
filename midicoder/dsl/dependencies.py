"""
DSL v1 Dependencies Module

Dependency graph builder and cycle detector for projection trees.
Ensures DAG (Directed Acyclic Graph) structure for valid code generation order.

Features:
- Dependency graph construction from projection trees
- Cycle detection using DFS
- Topological sort for build order
- LRU caching with TTL for resolution results
- Hash-based cache invalidation
"""

from __future__ import annotations

import hashlib
import time
from collections import defaultdict, deque, OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from .projection import NodeKind, ProjectionNode, ProjectionTree


class LRUCache:
    """
    Thread-safe LRU cache with TTL support.
    
    Features:
    - Maximum size limit with LRU eviction
    - Time-to-live (TTL) for cache entries
    - Hit/miss statistics
    """
    
    def __init__(self, max_size: int = 128, default_ttl: float = 300.0):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of entries (default 128)
            default_ttl: Default time-to-live in seconds (default 300 = 5 min)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        if key not in self._cache:
            self._misses += 1
            return None
        
        value, expiry = self._cache[key]
        
        # Check TTL
        if time.time() > expiry:
            del self._cache[key]
            self._misses += 1
            return None
        
        # Move to end (most recently used)
        self._cache.move_to_end(key)
        self._hits += 1
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            # Evict oldest if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
        
        expiry = time.time() + (ttl or self.default_ttl)
        self._cache[key] = (value, expiry)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
    
    def invalidate(self, key: str) -> None:
        """Invalidate a specific cache entry."""
        self._cache.pop(key, None)
    
    @property
    def size(self) -> int:
        """Current number of entries."""
        return len(self._cache)
    
    @property
    def hit_rate(self) -> float:
        """Cache hit rate (0.0 to 1.0)."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0
    
    @property
    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": self.size,
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{self.hit_rate:.2%}",
        }


class DependencyType(Enum):
    """Types of dependencies between nodes."""
    # Entity references
    ENTITY_REFERENCE = "entity_reference"
    FOREIGN_KEY = "foreign_key"
    
    # Command/Query references
    COMMAND_INPUT = "command_input"
    COMMAND_OUTPUT = "command_output"
    COMMAND_FETCH = "command_fetch"
    COMMAND_WRITES = "command_writes"
    QUERY_READS = "query_reads"
    
    # API bindings
    ROUTE_BINDS_COMMAND = "route_binds_command"
    ROUTE_BINDS_QUERY = "route_binds_query"
    
    # Workflow references
    WORKFLOW_TRANSITION = "workflow_transition"
    WORKFLOW_GUARD = "workflow_guard"
    WORKFLOW_EFFECT = "workflow_effect"
    
    # Access control
    ROLE_PERMISSION = "role_permission"
    ROLE_PARENT = "role_parent"
    POLICY_SUBJECT = "policy_subject"
    
    # Guard/Effect references
    COMMAND_GUARD = "command_guard"
    COMMAND_EFFECT = "command_effect"
    
    # Error references
    COMMAND_ERROR = "command_error"
    
    # Generic
    GENERIC = "generic"

    # P2-15: Domain-specific dependency types
    PLUGIN_SLOT_DEPENDENCY = "plugin_slot_dependency"      # P2-15a: CP27
    CALENDAR_WORKFLOW_DEPENDENCY = "calendar_workflow"      # P2-15b: CP31
    FINANCE_ENTITY_DEPENDENCY = "finance_entity"             # P2-15c: CP33
    REPORT_ENTITY_DEPENDENCY = "report_entity"               # P2-15d: CP34
    GEO_ENTITY_DEPENDENCY = "geo_entity"                     # P2-15e: CP35
    ETL_ENTITY_DEPENDENCY = "etl_entity"                     # P2-15f: CP38
    LOCALIZATION_ENTITY_DEPENDENCY = "localization_entity"   # P2-15g: CP39
    API_VERSION_ENTITY_DEPENDENCY = "api_version_entity"     # P2-15h: CP43
    PAYMENT_ENTITY_DEPENDENCY = "payment_entity"             # P2-15i: CP45
    CATALOG_ENTITY_DEPENDENCY = "catalog_entity"             # P2-15j: CP50


@dataclass
class Dependency:
    """
    A single dependency edge between two nodes.
    
    Attributes:
        source: Node ID that has the dependency
        target: Node ID that is depended upon
        dep_type: Type of dependency
        field: Field name where dependency is declared (optional)
    """
    source: str
    target: str
    dep_type: DependencyType
    field: Optional[str] = None
    
    def __hash__(self) -> int:
        return hash((self.source, self.target, self.dep_type))
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Dependency):
            return False
        return (
            self.source == other.source and
            self.target == other.target and
            self.dep_type == other.dep_type
        )


# ============================================================================
# Dependency Graph
# ============================================================================

@dataclass
class DependencyGraph:
    """
    Directed graph of dependencies between projection nodes.
    
    Attributes:
        edges: List of all dependency edges
        adjacency: Adjacency list (source -> [targets])
        reverse_adjacency: Reverse adjacency list (target -> [sources])
        nodes: Set of all node IDs in the graph
    """
    edges: list[Dependency] = field(default_factory=list)
    adjacency: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    reverse_adjacency: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    nodes: set[str] = field(default_factory=set)
    
    # Cache for computed results
    _graph_hash: Optional[str] = field(default=None, repr=False)
    
    def add_edge(self, source: str, target: str, dep_type: DependencyType, field: Optional[str] = None) -> None:
        """
        Add a dependency edge.
        
        Args:
            source: Node that depends on another
            target: Node being depended upon
            dep_type: Type of dependency
            field: Optional field name
        """
        # Invalidate cache on modification
        self._graph_hash = None
        
        # Avoid duplicates
        for edge in self.edges:
            if edge.source == source and edge.target == target and edge.dep_type == dep_type:
                return

        # Convert to string if not hashable (e.g. dict from LLM output)
        if not isinstance(target, str):
            target = str(target)
        if not isinstance(source, str):
            source = str(source)

        self.edges.append(Dependency(source=source, target=target, dep_type=dep_type, field=field))
        self.adjacency[source].append(target)
        self.reverse_adjacency[target].append(source)
        self.nodes.add(source)
        self.nodes.add(target)
    
    def get_dependencies(self, node_id: str) -> list[str]:
        """Get all nodes that a node depends on."""
        return self.adjacency.get(node_id, [])
    
    def get_dependents(self, node_id: str) -> list[str]:
        """Get all nodes that depend on a node."""
        return self.reverse_adjacency.get(node_id, [])
    
    def get_in_degree(self, node_id: str) -> int:
        """Get number of incoming edges (dependencies)."""
        return len(self.get_dependencies(node_id))
    
    def get_out_degree(self, node_id: str) -> int:
        """Get number of outgoing edges (dependents)."""
        return len(self.get_dependents(node_id))
    
    def node_count(self) -> int:
        """Get number of nodes."""
        return len(self.nodes)
    
    def edge_count(self) -> int:
        """Get number of edges."""
        return len(self.edges)
    
    def compute_hash(self) -> str:
        """
        Compute a hash of the graph structure for caching purposes.
        
        Returns:
            SHA-256 hash string of the graph structure
        """
        if self._graph_hash is not None:
            return self._graph_hash
        
        # Create a deterministic representation of the graph
        hasher = hashlib.sha256()
        
        # Sort nodes for deterministic ordering
        sorted_nodes = sorted(self.nodes)
        hasher.update("|".join(sorted_nodes).encode())
        
        # Sort edges for deterministic ordering
        sorted_edges = sorted(
            [(e.source, e.target, e.dep_type.value) for e in self.edges],
            key=lambda x: (x[0], x[1], x[2])
        )
        hasher.update("|".join(f"{s}:{t}:{d}" for s, t, d in sorted_edges).encode())
        
        self._graph_hash = hasher.hexdigest()
        return self._graph_hash
    
    def reset_hash_cache(self) -> None:
        """Reset the cached hash (call after structural modifications)."""
        self._graph_hash = None


# ============================================================================
# Cached Cycle Detection and Topological Sort
# ============================================================================

# Global caches for dependency resolution results
_cycle_cache = LRUCache(max_size=256, default_ttl=600.0)
_topo_cache = LRUCache(max_size=256, default_ttl=600.0)
_analysis_cache = LRUCache(max_size=128, default_ttl=600.0)


def get_cycle_cache() -> LRUCache:
    """Get the global cycle detection cache."""
    return _cycle_cache


def get_topo_cache() -> LRUCache:
    """Get the global topological sort cache."""
    return _topo_cache


def get_analysis_cache() -> LRUCache:
    """Get the global analysis cache."""
    return _analysis_cache


def clear_resolution_caches() -> None:
    """Clear all dependency resolution caches."""
    _cycle_cache.clear()
    _topo_cache.clear()
    _analysis_cache.clear()


def get_cache_stats() -> dict[str, dict[str, Any]]:
    """Get statistics for all dependency resolution caches."""
    return {
        "cycle_cache": _cycle_cache.stats,
        "topo_cache": _topo_cache.stats,
        "analysis_cache": _analysis_cache.stats,
    }


# ============================================================================
# Cycle Detection
# ============================================================================

@dataclass
class CycleInfo:
    """Information about a detected cycle."""
    cycle: list[str]
    message: str
    
    def __str__(self) -> str:
        cycle_str = " -> ".join(self.cycle)
        return f"Cycle detected: {cycle_str}"


@dataclass
class CycleDetectionResult:
    """Result of cycle detection."""
    has_cycle: bool
    cycles: list[CycleInfo]
    
    def is_valid(self) -> bool:
        return not self.has_cycle


def detect_cycles(graph: DependencyGraph) -> CycleDetectionResult:
    """
    Detect cycles in the dependency graph using DFS.
    
    Args:
        graph: Dependency graph to analyze
        
    Returns:
        CycleDetectionResult with cycle information
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {node: WHITE for node in graph.nodes}
    parent: dict[str, Optional[str]] = {node: None for node in graph.nodes}
    cycles: list[CycleInfo] = []
    
    def dfs(node: str, path: list[str]) -> None:
        color[node] = GRAY
        path.append(node)
        
        for neighbor in graph.adjacency.get(node, []):
            if color[neighbor] == GRAY:
                # Found a back edge - cycle detected
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(CycleInfo(
                    cycle=cycle,
                    message=f"Dependency cycle: {' -> '.join(cycle)}"
                ))
            elif color[neighbor] == WHITE:
                dfs(neighbor, path)
        
        path.pop()
        color[node] = BLACK
    
    for node in graph.nodes:
        if color[node] == WHITE:
            dfs(node, [])
    
    return CycleDetectionResult(
        has_cycle=len(cycles) > 0,
        cycles=cycles
    )


# ============================================================================
# Topological Sort (Build Order)
# ============================================================================

@dataclass
class TopologicalSortResult:
    """Result of topological sort."""
    success: bool
    order: list[str]
    error: Optional[str] = None
    
    def is_valid(self) -> bool:
        return self.success


def topological_sort(graph: DependencyGraph) -> TopologicalSortResult:
    """
    Perform topological sort using Kahn's algorithm.
    
    Returns build order where dependencies come before dependents.
    
    Args:
        graph: Dependency graph to sort
        
    Returns:
        TopologicalSortResult with node order or error
    """
    # Check for cycles first
    cycle_result = detect_cycles(graph)
    if cycle_result.has_cycle:
        return TopologicalSortResult(
            success=False,
            order=[],
            error=cycle_result.cycles[0].message
        )
    
    # Calculate in-degrees
    in_degree: dict[str, int] = {node: 0 for node in graph.nodes}
    for node in graph.nodes:
        for dep in graph.adjacency.get(node, []):
            in_degree[node] += 1
    
    # Start with nodes that have no dependencies
    queue = deque([node for node in graph.nodes if in_degree[node] == 0])
    order: list[str] = []
    
    while queue:
        node = queue.popleft()
        order.append(node)
        
        # Reduce in-degree for dependents
        for dependent in graph.reverse_adjacency.get(node, []):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)
    
    # Check if all nodes are included
    if len(order) != len(graph.nodes):
        return TopologicalSortResult(
            success=False,
            order=order,
            error="Could not sort all nodes (possible cycle)"
        )
    
    return TopologicalSortResult(success=True, order=order)


# ============================================================================
# Dependency Builder
# ============================================================================

@dataclass
class DependencyBuilder:
    """
    Builds dependency graph from a projection tree.
    
    Analyzes node params to extract implicit dependencies.
    """
    tree: ProjectionTree
    graph: DependencyGraph = field(default_factory=DependencyGraph)
    
    def build(self) -> DependencyGraph:
        """
        Build the complete dependency graph.
        
        Returns:
            Built dependency graph
        """
        # Register all nodes
        for node_id in self.tree.nodes:
            self.graph.nodes.add(node_id)
        
        # Extract dependencies by node kind
        for node in self.tree.nodes.values():
            self._extract_node_dependencies(node)
        
        return self.graph
    
    def _extract_node_dependencies(self, node: ProjectionNode) -> None:
        """Extract dependencies from a single node."""

        if node.kind == NodeKind.ENTITY:
            self._extract_entity_dependencies(node)
        elif node.kind == NodeKind.COMMAND:
            self._extract_command_dependencies(node)
        elif node.kind == NodeKind.QUERY:
            self._extract_query_dependencies(node)
        elif node.kind == NodeKind.HTTP_ROUTE:
            self._extract_http_route_dependencies(node)
        elif node.kind == NodeKind.WORKFLOW:
            self._extract_workflow_dependencies(node)
        elif node.kind == NodeKind.ROLE:
            self._extract_role_dependencies(node)
        # P2-15: Domain-specific dependency extraction
        elif node.kind == NodeKind.PLUGIN_SLOT:
            self._extract_plugin_slot_dependencies(node)
        elif node.kind == NodeKind.CALENDAR_SCHEDULE:
            self._extract_calendar_schedule_dependencies(node)
        elif node.kind in (NodeKind.GENERAL_LEDGER, NodeKind.FINANCIAL_INSTRUMENT, NodeKind.CURRENCY_EXCHANGE):
            self._extract_finance_dependencies(node)
        elif node.kind in (NodeKind.REPORT, NodeKind.DASHBOARD, NodeKind.EXPORT):
            self._extract_report_dependencies(node)
        elif node.kind == NodeKind.GEO_SEARCH_INDEX:
            self._extract_geo_search_dependencies(node)
        elif node.kind in (NodeKind.DATA_MIGRATION, NodeKind.BATCH_JOB):
            self._extract_etl_dependencies(node)
        elif node.kind == NodeKind.LOCALIZATION:
            self._extract_localization_dependencies(node)
        elif node.kind == NodeKind.API_VERSION:
            self._extract_api_version_dependencies(node)
        elif node.kind == NodeKind.PAYMENT_GATEWAY:
            self._extract_payment_gateway_dependencies(node)
        elif node.kind in (NodeKind.PRODUCT_CATALOG, NodeKind.FACETED_SEARCH_INDEX):
            self._extract_catalog_dependencies(node)

    # -----------------------------------------------------------------------
    # P2-15: Domain-specific dependency extraction methods
    # -----------------------------------------------------------------------

    def _extract_plugin_slot_dependencies(self, node: ProjectionNode) -> None:
        """
        P2-15a: CP27 PLUGIN_SLOT — depends on entities referenced in slot config.
        """
        # Plugin slots may reference entities via 'entity_id' or 'entities' param
        entity_id = node.params.get("entity_id")
        if entity_id:
            self.graph.add_edge(
                source=node.id,
                target=entity_id,
                dep_type=DependencyType.PLUGIN_SLOT_DEPENDENCY,
                field="entity_id",
            )
        for eid in node.params.get("entities", []):
            self.graph.add_edge(
                source=node.id,
                target=eid,
                dep_type=DependencyType.PLUGIN_SLOT_DEPENDENCY,
                field="entities",
            )

    def _extract_calendar_schedule_dependencies(self, node: ProjectionNode) -> None:
        """
        P2-15b: CP31 CALENDAR_SCHEDULE — depends on WORKFLOW (CP13).
        """
        workflow_id = node.params.get("workflow_id")
        if workflow_id:
            self.graph.add_edge(
                source=node.id,
                target=workflow_id,
                dep_type=DependencyType.CALENDAR_WORKFLOW_DEPENDENCY,
                field="workflow_id",
            )
        # Also check 'workflow' field
        wf = node.params.get("workflow")
        if wf:
            self.graph.add_edge(
                source=node.id,
                target=wf,
                dep_type=DependencyType.CALENDAR_WORKFLOW_DEPENDENCY,
                field="workflow",
            )

    def _extract_finance_dependencies(self, node: ProjectionNode) -> None:
        """
        P2-15c: CP33 GENERAL_LEDGER, FINANCIAL_INSTRUMENT, CURRENCY_EXCHANGE —
        depends on ENTITY, CP08.
        """
        entity_id = node.params.get("entity_id")
        if entity_id:
            self.graph.add_edge(
                source=node.id,
                target=entity_id,
                dep_type=DependencyType.FINANCE_ENTITY_DEPENDENCY,
                field="entity_id",
            )
        for eid in node.params.get("entities", []):
            self.graph.add_edge(
                source=node.id,
                target=eid,
                dep_type=DependencyType.FINANCE_ENTITY_DEPENDENCY,
                field="entities",
            )

    def _extract_report_dependencies(self, node: ProjectionNode) -> None:
        """
        P2-15d: CP34 REPORT, DASHBOARD, EXPORT — depends on ENTITY.
        """
        for ref in node.params.get("data_sources", []):
            self.graph.add_edge(
                source=node.id,
                target=ref,
                dep_type=DependencyType.REPORT_ENTITY_DEPENDENCY,
                field="data_sources",
            )
        source_id = node.params.get("source_id")
        if source_id:
            self.graph.add_edge(
                source=node.id,
                target=source_id,
                dep_type=DependencyType.REPORT_ENTITY_DEPENDENCY,
                field="source_id",
            )

    def _extract_geo_search_dependencies(self, node: ProjectionNode) -> None:
        """
        P2-15e: CP35 GEO_SEARCH_INDEX — depends on ENTITY with geofield.
        """
        entity_id = node.params.get("entity_id")
        if entity_id:
            self.graph.add_edge(
                source=node.id,
                target=entity_id,
                dep_type=DependencyType.GEO_ENTITY_DEPENDENCY,
                field="entity_id",
            )

    def _extract_etl_dependencies(self, node: ProjectionNode) -> None:
        """
        P2-15f: CP38 DATA_MIGRATION, BATCH_JOB — depends on ENTITY (source/target).
        """
        source_schema = node.params.get("source_schema")
        if source_schema:
            self.graph.add_edge(
                source=node.id,
                target=source_schema,
                dep_type=DependencyType.ETL_ENTITY_DEPENDENCY,
                field="source_schema",
            )
        target_schema = node.params.get("target_schema")
        if target_schema:
            self.graph.add_edge(
                source=node.id,
                target=target_schema,
                dep_type=DependencyType.ETL_ENTITY_DEPENDENCY,
                field="target_schema",
            )
        # Also check input_sources and output_destinations for BATCH_JOB
        for src in node.params.get("input_sources", []):
            self.graph.add_edge(
                source=node.id,
                target=src,
                dep_type=DependencyType.ETL_ENTITY_DEPENDENCY,
                field="input_sources",
            )
        for dst in node.params.get("output_destinations", []):
            self.graph.add_edge(
                source=node.id,
                target=dst,
                dep_type=DependencyType.ETL_ENTITY_DEPENDENCY,
                field="output_destinations",
            )

    def _extract_localization_dependencies(self, node: ProjectionNode) -> None:
        """
        P2-15g: CP39 LOCALIZATION — depends on ENTITY (translatable fields).
        """
        entity_id = node.params.get("entity_id")
        if entity_id:
            self.graph.add_edge(
                source=node.id,
                target=entity_id,
                dep_type=DependencyType.LOCALIZATION_ENTITY_DEPENDENCY,
                field="entity_id",
            )

    def _extract_api_version_dependencies(self, node: ProjectionNode) -> None:
        """
        P2-15h: CP43 API_VERSION — depends on ENTITY.
        """
        api_id = node.params.get("api_id")
        if api_id:
            self.graph.add_edge(
                source=node.id,
                target=api_id,
                dep_type=DependencyType.API_VERSION_ENTITY_DEPENDENCY,
                field="api_id",
            )
        # Also check entities field
        for eid in node.params.get("entities", []):
            self.graph.add_edge(
                source=node.id,
                target=eid,
                dep_type=DependencyType.API_VERSION_ENTITY_DEPENDENCY,
                field="entities",
            )

    def _extract_payment_gateway_dependencies(self, node: ProjectionNode) -> None:
        """
        P2-15i: CP45 PAYMENT_GATEWAY — depends on CP33 (Currency), CP40 (Webhook).
        """
        for currency in node.params.get("currencies", []):
            self.graph.add_edge(
                source=node.id,
                target=currency,
                dep_type=DependencyType.PAYMENT_ENTITY_DEPENDENCY,
                field="currencies",
            )
        webhook = node.params.get("webhook_id")
        if webhook:
            self.graph.add_edge(
                source=node.id,
                target=webhook,
                dep_type=DependencyType.PAYMENT_ENTITY_DEPENDENCY,
                field="webhook_id",
            )

    def _extract_catalog_dependencies(self, node: ProjectionNode) -> None:
        """
        P2-15j: CP50 PRODUCT_CATALOG, FACETED_SEARCH_INDEX — depends on CP08, CP10.
        """
        # Product catalog may reference entities for products
        for product_id in node.params.get("products", []):
            if isinstance(product_id, str):
                self.graph.add_edge(
                    source=node.id,
                    target=product_id,
                    dep_type=DependencyType.CATALOG_ENTITY_DEPENDENCY,
                    field="products",
                )
        # Search index dependency
        index_id = node.params.get("search_index_id")
        if index_id:
            self.graph.add_edge(
                source=node.id,
                target=index_id,
                dep_type=DependencyType.CATALOG_ENTITY_DEPENDENCY,
                field="search_index_id",
            )
        # Entity reference
        entity_id = node.params.get("entity_id")
        if entity_id:
            self.graph.add_edge(
                source=node.id,
                target=entity_id,
                dep_type=DependencyType.CATALOG_ENTITY_DEPENDENCY,
                field="entity_id",
            )
    
    def _extract_entity_dependencies(self, node: ProjectionNode) -> None:
        """Extract dependencies from entity (foreign keys)."""
        constraints = node.params.get("constraints", [])
        for c in constraints:
            if c.get("type") == "foreign_key":
                ref = c.get("ref")
                if ref:
                    self.graph.add_edge(
                        source=node.id,
                        target=ref,
                        dep_type=DependencyType.FOREIGN_KEY,
                        field="constraints"
                    )
    
    def _extract_command_dependencies(self, node: ProjectionNode) -> None:
        """Extract dependencies from command."""
        # Fetches (entities read)
        for fetch_id in node.params.get("fetches", []):
            self.graph.add_edge(
                source=node.id,
                target=fetch_id,
                dep_type=DependencyType.COMMAND_FETCH,
                field="fetches"
            )
        
        # Writes to (entities modified)
        for write_id in node.params.get("writes_to", []):
            self.graph.add_edge(
                source=node.id,
                target=write_id,
                dep_type=DependencyType.COMMAND_WRITES,
                field="writes_to"
            )
        
        # Errors
        for error_id in node.params.get("errors", []):
            self.graph.add_edge(
                source=node.id,
                target=error_id,
                dep_type=DependencyType.COMMAND_ERROR,
                field="errors"
            )
        
        # Guards
        for guard in node.params.get("guards", []):
            guard_id = guard.get("id") if isinstance(guard, dict) else guard
            if guard_id:
                self.graph.add_edge(
                    source=node.id,
                    target=guard_id,
                    dep_type=DependencyType.COMMAND_GUARD,
                    field="guards"
                )
        
        # Effects
        for effect in node.params.get("effects", []):
            effect_id = effect.get("id") if isinstance(effect, dict) else effect
            if effect_id:
                self.graph.add_edge(
                    source=node.id,
                    target=effect_id,
                    dep_type=DependencyType.COMMAND_EFFECT,
                    field="effects"
                )
    
    def _extract_query_dependencies(self, node: ProjectionNode) -> None:
        """Extract dependencies from query."""
        # Reads from (entities queried)
        for read_id in node.params.get("reads_from", []):
            self.graph.add_edge(
                source=node.id,
                target=read_id,
                dep_type=DependencyType.QUERY_READS,
                field="reads_from"
            )
    
    def _extract_http_route_dependencies(self, node: ProjectionNode) -> None:
        """Extract dependencies from HTTP route."""
        command_id = node.params.get("command_id")
        if command_id:
            self.graph.add_edge(
                source=node.id,
                target=command_id,
                dep_type=DependencyType.ROUTE_BINDS_COMMAND,
                field="command_id"
            )
        
        query_id = node.params.get("query_id")
        if query_id:
            self.graph.add_edge(
                source=node.id,
                target=query_id,
                dep_type=DependencyType.ROUTE_BINDS_QUERY,
                field="query_id"
            )
    
    def _extract_workflow_dependencies(self, node: ProjectionNode) -> None:
        """Extract dependencies from workflow."""
        # Guards
        for guard in node.params.get("guards", []):
            guard_id = guard.get("id") if isinstance(guard, dict) else guard
            if guard_id:
                self.graph.add_edge(
                    source=node.id,
                    target=guard_id,
                    dep_type=DependencyType.WORKFLOW_GUARD,
                    field="guards"
                )
        
        # Effects
        for effect in node.params.get("effects", []):
            effect_id = effect.get("id") if isinstance(effect, dict) else effect
            if effect_id:
                self.graph.add_edge(
                    source=node.id,
                    target=effect_id,
                    dep_type=DependencyType.WORKFLOW_EFFECT,
                    field="effects"
                )
    
    def _extract_role_dependencies(self, node: ProjectionNode) -> None:
        """Extract dependencies from role."""
        # Permissions
        for perm_id in node.params.get("permissions", []):
            self.graph.add_edge(
                source=node.id,
                target=perm_id,
                dep_type=DependencyType.ROLE_PERMISSION,
                field="permissions"
            )
        
        # Parent roles
        for parent_id in node.params.get("parent_roles", []):
            self.graph.add_edge(
                source=node.id,
                target=parent_id,
                dep_type=DependencyType.ROLE_PARENT,
                field="parent_roles"
            )


# ============================================================================
# Analysis Utilities
# ============================================================================

@dataclass
class DependencyAnalysis:
    """Results of dependency analysis."""
    graph: DependencyGraph
    has_cycles: bool
    cycles: list[CycleInfo]
    build_order: list[str]
    orphans: list[str]  # Nodes with no connections
    leaves: list[str]  # Nodes with no dependents (endpoints)
    roots: list[str]  # Nodes with no dependencies (entry points)
    
    @classmethod
    def analyze(cls, tree: ProjectionTree) -> "DependencyAnalysis":
        """
        Perform complete dependency analysis.
        
        Args:
            tree: Projection tree to analyze
            
        Returns:
            Complete dependency analysis
        """
        # Build graph
        builder = DependencyBuilder(tree=tree)
        graph = builder.build()
        
        # Detect cycles
        cycle_result = detect_cycles(graph)
        
        # Get build order
        topo_result = topological_sort(graph)
        build_order = topo_result.order if topo_result.success else []
        
        # Find orphans (no connections)
        connected_nodes = set()
        for edge in graph.edges:
            connected_nodes.add(edge.source)
            connected_nodes.add(edge.target)
        orphans = [n for n in graph.nodes if n not in connected_nodes]
        
        # Find leaves (no dependents)
        leaves = [n for n in graph.nodes if not graph.get_dependents(n)]
        
        # Find roots (no dependencies)
        roots = [n for n in graph.nodes if not graph.get_dependencies(n)]
        
        return cls(
            graph=graph,
            has_cycles=cycle_result.has_cycle,
            cycles=cycle_result.cycles,
            build_order=build_order,
            orphans=orphans,
            leaves=leaves,
            roots=roots,
        )
    
    def is_valid(self) -> bool:
        """Check if the dependency structure is valid (DAG)."""
        return not self.has_cycles
    
    def get_layered_order(self) -> list[list[str]]:
        """
        Get build order grouped by layers.
        
        Nodes in the same layer have no dependencies on each other
        and can be processed in parallel.
        
        Returns:
            List of layers, each containing node IDs
        """
        if not self.is_valid():
            return []
        
        layers: list[list[str]] = []
        in_degree: dict[str, int] = {n: 0 for n in self.graph.nodes}
        
        # Calculate in-degrees
        for node in self.graph.nodes:
            for dep in self.graph.adjacency.get(node, []):
                in_degree[node] += 1
        
        remaining = set(self.graph.nodes)
        
        while remaining:
            # Find all nodes with in-degree 0
            layer = [n for n in remaining if in_degree[n] == 0]
            if not layer:
                break  # Cycle detected (shouldn't happen if is_valid())
            
            layers.append(layer)
            
            # Remove layer nodes and update in-degrees
            for node in layer:
                remaining.remove(node)
                for dependent in self.graph.reverse_adjacency.get(node, []):
                    if dependent in remaining:
                        in_degree[dependent] -= 1
        
        return layers


# ============================================================================
# Cached Resolution Functions
# ============================================================================

def cached_detect_cycles(graph: DependencyGraph, use_cache: bool = True) -> tuple[CycleDetectionResult, bool]:
    """
    Detect cycles with caching support.
    
    Args:
        graph: Dependency graph to analyze
        use_cache: Whether to use cache (default True)
        
    Returns:
        Tuple of (CycleDetectionResult, is_cache_hit)
    """
    if not use_cache:
        return detect_cycles(graph), False
    
    graph_hash = graph.compute_hash()
    cache_key = f"cycle:{graph_hash}"
    
    # Try cache
    cached_result = _cycle_cache.get(cache_key)
    if cached_result is not None:
        # Convert tuple back to CycleDetectionResult
        has_cycle, cycles_data = cached_result
        cycles = [CycleInfo(cycle=c, message=m) for c, m in cycles_data]
        return CycleDetectionResult(has_cycle=has_cycle, cycles=cycles), True
    
    # Compute and cache
    result = detect_cycles(graph)
    cycles_data = [(c.cycle, c.message) for c in result.cycles]
    _cycle_cache.set(cache_key, (result.has_cycle, cycles_data))
    
    return result, False


def cached_topological_sort(graph: DependencyGraph, use_cache: bool = True) -> tuple[TopologicalSortResult, bool]:
    """
    Perform topological sort with caching support.
    
    Args:
        graph: Dependency graph to sort
        use_cache: Whether to use cache (default True)
        
    Returns:
        Tuple of (TopologicalSortResult, is_cache_hit)
    """
    if not use_cache:
        return topological_sort(graph), False
    
    graph_hash = graph.compute_hash()
    cache_key = f"topo:{graph_hash}"
    
    # Try cache
    cached_result = _topo_cache.get(cache_key)
    if cached_result is not None:
        success, order, error = cached_result
        return TopologicalSortResult(success=success, order=order, error=error), True
    
    # Compute and cache
    result = topological_sort(graph)
    _topo_cache.set(cache_key, (result.success, result.order, result.error))
    
    return result, False


@dataclass
class CachingDependencyBuilder:
    """
    Dependency builder with caching support for repeated analyses.
    
    Caches the built graph and analysis results based on tree hash.
    Ideal for scenarios where the same tree is analyzed multiple times.
    
    Attributes:
        tree: Projection tree to build dependencies from
        use_cache: Whether to enable caching (default True)
        cache_ttl: Time-to-live for cache entries in seconds (default 600)
    """
    tree: ProjectionTree
    use_cache: bool = True
    cache_ttl: float = 600.0
    
    def build_with_cache(self) -> tuple[DependencyGraph, bool]:
        """
        Build dependency graph with caching.
        
        Returns:
            Tuple of (DependencyGraph, is_cache_hit)
        """
        if not self.use_cache:
            builder = DependencyBuilder(tree=self.tree)
            return builder.build(), False
        
        # Compute tree hash for cache key
        tree_hash = self._compute_tree_hash()
        cache_key = f"graph:{tree_hash}"
        
        # Try cache (store as serializable format)
        cached_data = _analysis_cache.get(cache_key)
        if cached_data is not None:
            return self._deserialize_graph(cached_data), True
        
        # Build and cache
        builder = DependencyBuilder(tree=self.tree)
        graph = builder.build()
        serialized = self._serialize_graph(graph)
        _analysis_cache.set(cache_key, serialized, ttl=self.cache_ttl)
        
        return graph, False
    
    def _compute_tree_hash(self) -> str:
        """Compute hash of the projection tree structure."""
        hasher = hashlib.sha256()
        
        # Hash all nodes and their params
        for node_id in sorted(self.tree.nodes.keys()):
            node = self.tree.nodes[node_id]
            hasher.update(f"{node_id}:{node.kind.value}".encode())
            # Hash params (convert to sorted string for determinism)
            params_str = str(sorted(str((k, v)) for k, v in node.params.items()))
            hasher.update(params_str.encode())
        
        return hasher.hexdigest()
    
    def _serialize_graph(self, graph: DependencyGraph) -> dict[str, Any]:
        """Serialize graph to cacheable format."""
        return {
            "nodes": list(graph.nodes),
            "edges": [
                {"source": e.source, "target": e.target, "type": e.dep_type.value, "field": e.field}
                for e in graph.edges
            ],
        }
    
    def _deserialize_graph(self, data: dict[str, Any]) -> DependencyGraph:
        """Deserialize graph from cache format."""
        graph = DependencyGraph()
        graph.nodes = set(data["nodes"])
        
        for edge_data in data["edges"]:
            dep_type = DependencyType(edge_data["type"])
            graph.adjacency[edge_data["source"]].append(edge_data["target"])
            graph.reverse_adjacency[edge_data["target"]].append(edge_data["source"])
            graph.edges.append(Dependency(
                source=edge_data["source"],
                target=edge_data["target"],
                dep_type=dep_type,
                field=edge_data.get("field")
            ))
        
        return graph
    
    def analyze_with_cache(self) -> tuple[DependencyAnalysis, bool]:
        """
        Perform full dependency analysis with caching.
        
        Returns:
            Tuple of (DependencyAnalysis, is_cache_hit)
        """
        # Build graph (may use cache)
        graph, graph_hit = self.build_with_cache()
        
        # Detect cycles (may use cache)
        cycle_result, cycle_hit = cached_detect_cycles(graph, self.use_cache)
        
        # Get build order (may use cache)
        topo_result, topo_hit = cached_topological_sort(graph, self.use_cache)
        
        # Compute remaining analysis (not cached separately)
        build_order = topo_result.order if topo_result.success else []
        
        connected_nodes = set()
        for edge in graph.edges:
            connected_nodes.add(edge.source)
            connected_nodes.add(edge.target)
        orphans = [n for n in graph.nodes if n not in connected_nodes]
        
        leaves = [n for n in graph.nodes if not graph.get_dependents(n)]
        roots = [n for n in graph.nodes if not graph.get_dependencies(n)]
        
        analysis = DependencyAnalysis(
            graph=graph,
            has_cycles=cycle_result.has_cycle,
            cycles=cycle_result.cycles,
            build_order=build_order,
            orphans=orphans,
            leaves=leaves,
            roots=roots,
        )
        
        # Cache hit if all operations hit cache
        is_hit = graph_hit and cycle_hit and topo_hit
        return analysis, is_hit
