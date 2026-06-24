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
    STATE_MACHINE_DEPENDENCY = "state_machine_entity"         # P2-15k: CP32
    FEATURE_FLAG_DEPENDENCY = "feature_flag_entity"           # P2-15l: CP37
    AUTH_UI_DEPENDENCY = "auth_ui_entity"                     # CP21
    CHANNEL_SPEC_DEPENDENCY = "channel_spec_entity"           # CP22
    WIDGET_CHANNEL_DEPENDENCY = "widget_channel_entity"       # CP22
    CUSTOM_CODE_DEPENDENCY = "custom_code_entity"             # CP28
    GEOFENCE_DEPENDENCY = "geofence_entity"                   # CP35
    TENANT_SUBSCRIPTION_DEPENDENCY = "tenant_sub_entity"      # CP36
    WEBHOOK_RETRY_DEPENDENCY = "webhook_retry_entity"         # CP40
    CONVERSATION_DEPENDENCY = "conversation_entity"           # CP41
    CHAT_CONVERSATION_DEPENDENCY = "chat_conversation_entity"  # CP41
    APPROVAL_REQUEST_DEPENDENCY = "approval_request_entity"   # CP42
    APPROVAL_STEP_DEPENDENCY = "approval_step_entity"         # CP42
    APPROVAL_ESCALATION_DEPENDENCY = "approval_esc_entity"    # CP42
    VERSION_ENTITY_DEPENDENCY = "version_entity_entity"       # CP43
    HISTORY_ENTITY_DEPENDENCY = "history_entity_entity"       # CP43
    BULK_ENTITY_DEPENDENCY = "bulk_entity_entity"             # CP44
    RETENTION_ENTITY_DEPENDENCY = "retention_entity_entity"   # CP47
    ERASURE_ENTITY_DEPENDENCY = "erasure_entity_entity"       # CP47
    RATE_LIMIT_ENDPOINT_DEPENDENCY = "ratelimit_ep_entity"    # CP48
    CONSENT_POLICY_DEPENDENCY = "consent_policy_entity"       # CP49
    CONSENT_RECORD_DEPENDENCY = "consent_record_entity"       # CP49


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
        elif node.kind == NodeKind.EVENT:
            self._extract_event_dependencies(node)
        elif node.kind == NodeKind.UI_COMPONENT:
            self._extract_ui_component_dependencies(node)
        # P2-15: Domain-specific dependency extraction
        elif node.kind == NodeKind.PLUGIN_SLOT:
            self._extract_plugin_slot_dependencies(node)
        elif node.kind == NodeKind.CALENDAR_SCHEDULE:
            self._extract_calendar_schedule_dependencies(node)
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
        elif node.kind == NodeKind.FACETED_SEARCH_INDEX:
            pass  # catalog dependencies removed; implement when needed
        # CP32/CP37: State Machine & Feature Flag dependency extraction
        elif node.kind == NodeKind.STATE_MACHINE:
            self._extract_state_machine_dependencies(node)
        elif node.kind == NodeKind.STATE_TRANSITION:
            self._extract_state_transition_dependencies(node)
        elif node.kind == NodeKind.FEATURE_FLAG:
            self._extract_feature_flag_dependencies(node)
        elif node.kind == NodeKind.AB_EXPERIMENT:
            self._extract_ab_experiment_dependencies(node)
        elif node.kind == NodeKind.DYNAMIC_CONFIG:
            self._extract_dynamic_config_dependencies(node)
        # CP21: Auth UI
        elif node.kind == NodeKind.AUTH_UI_CONFIG:
            self._extract_auth_ui_dependencies(node)
        # CP22: Real-time UI
        elif node.kind == NodeKind.CHANNEL_SPEC:
            self._extract_channel_spec_dependencies(node)
        elif node.kind == NodeKind.WIDGET_CONFIG:
            self._extract_widget_config_dependencies(node)
        # CP28: Custom Code
        elif node.kind in (NodeKind.CUSTOM_CODE_BLOCK, NodeKind.CUSTOM_HOOK, NodeKind.CUSTOM_PATCH_RULE):
            self._extract_custom_code_dependencies(node)
        # CP35: Geospatial
        elif node.kind == NodeKind.GEOSPATIAL_SPEC:
            self._extract_geospatial_dependencies(node)
        # CP40: Webhook
        elif node.kind == NodeKind.WEBHOOK_SUBSCRIPTION:
            self._extract_webhook_dependencies(node)
        # CP41: Chat
        elif node.kind == NodeKind.CONVERSATION:
            self._extract_conversation_dependencies(node)
        elif node.kind == NodeKind.CHAT_MESSAGE:
            self._extract_chat_message_dependencies(node)
        # CP42: Approval
        elif node.kind == NodeKind.APPROVAL_REQUEST:
            self._extract_approval_request_dependencies(node)
        elif node.kind == NodeKind.APPROVAL_STEP:
            self._extract_approval_step_dependencies(node)
        # CP43: Versioning
        elif node.kind == NodeKind.VERSION_CONFIG:
            self._extract_version_config_dependencies(node)
        elif node.kind == NodeKind.HISTORY_RECORD:
            self._extract_history_record_dependencies(node)
        # CP44: Bulk Ops
        elif node.kind == NodeKind.BULK_JOB:
            self._extract_bulk_job_dependencies(node)
        # CP47: Retention
        elif node.kind == NodeKind.RETENTION_POLICY:
            self._extract_retention_policy_dependencies(node)
        elif node.kind == NodeKind.ERASURE_REQUEST:
            self._extract_erasure_request_dependencies(node)
        # CP49: Consent
        elif node.kind == NodeKind.CONSENT_RECORD:
            self._extract_consent_record_dependencies(node)

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

    def _extract_state_machine_dependencies(self, node: ProjectionNode) -> None:
        """
        P2-15k: CP32 STATE_MACHINE — depends on ENTITY it manages.
        """
        entity_id = node.params.get("entity_id")
        if entity_id:
            self.graph.add_edge(
                source=node.id,
                target=entity_id,
                dep_type=DependencyType.STATE_MACHINE_DEPENDENCY,
                field="entity_id",
            )

    def _extract_state_transition_dependencies(self, node: ProjectionNode) -> None:
        """
        P2-15k: CP32 STATE_TRANSITION — depends on STATE_MACHINE and optional GUARD/EFFECT.
        """
        machine_id = node.params.get("machine_id")
        if machine_id:
            self.graph.add_edge(
                source=node.id,
                target=machine_id,
                dep_type=DependencyType.STATE_MACHINE_DEPENDENCY,
                field="machine_id",
            )
        guard = node.params.get("guard")
        if guard:
            self.graph.add_edge(
                source=node.id,
                target=guard,
                dep_type=DependencyType.COMMAND_GUARD,
                field="guard",
            )
        effect = node.params.get("effect")
        if effect:
            self.graph.add_edge(
                source=node.id,
                target=effect,
                dep_type=DependencyType.COMMAND_EFFECT,
                field="effect",
            )

    def _extract_feature_flag_dependencies(self, node: ProjectionNode) -> None:
        """
        P2-15l: CP37 FEATURE_FLAG — depends on ENTITY if targeted at specific entity scope.
        """
        for tenant in node.params.get("tenants", []):
            self.graph.add_edge(
                source=node.id,
                target=tenant,
                dep_type=DependencyType.FEATURE_FLAG_DEPENDENCY,
                field="tenants",
            )

    def _extract_ab_experiment_dependencies(self, node: ProjectionNode) -> None:
        """
        P2-15l: CP37 AB_EXPERIMENT — depends on ENTITY referenced by assignment_key.
        """
        assignment_key = node.params.get("assignment_key")
        if assignment_key:
            self.graph.add_edge(
                source=node.id,
                target=assignment_key,
                dep_type=DependencyType.FEATURE_FLAG_DEPENDENCY,
                field="assignment_key",
            )

    def _extract_dynamic_config_dependencies(self, node: ProjectionNode) -> None:
        """
        P2-15l: CP37 DYNAMIC_CONFIG — depends on TENANT if scoped.
        """
        scope = node.params.get("scope")
        if scope == "tenant":
            pass  # Tenant dependency is resolved at runtime, not in DSL graph

    # -----------------------------------------------------------------------
    # CP21: Auth UI dependency extraction
    # -----------------------------------------------------------------------
    def _extract_auth_ui_dependencies(self, node: ProjectionNode) -> None:
        """CP21: AUTH_UI_CONFIG — depends on ENTITY referenced by pages."""
        pass  # UI pages reference entities at render time

    # -----------------------------------------------------------------------
    # CP22: Real-time UI dependency extraction
    # -----------------------------------------------------------------------
    def _extract_channel_spec_dependencies(self, node: ProjectionNode) -> None:
        """CP22: CHANNEL_SPEC — depends on ENTITY."""
        entity_id = node.params.get("entity_id")
        if entity_id:
            self.graph.add_edge(
                source=node.id,
                target=entity_id,
                dep_type=DependencyType.CHANNEL_SPEC_DEPENDENCY,
                field="entity_id",
            )

    def _extract_widget_config_dependencies(self, node: ProjectionNode) -> None:
        """CP22: WIDGET_CONFIG — depends on CHANNEL_SPEC and ENTITY."""
        channel_id = node.params.get("channel_id")
        if channel_id:
            self.graph.add_edge(
                source=node.id,
                target=channel_id,
                dep_type=DependencyType.WIDGET_CHANNEL_DEPENDENCY,
                field="channel_id",
            )
        entity_id = node.params.get("entity_id")
        if entity_id:
            self.graph.add_edge(
                source=node.id,
                target=entity_id,
                dep_type=DependencyType.CHANNEL_SPEC_DEPENDENCY,
                field="entity_id",
            )

    # -----------------------------------------------------------------------
    # CP28: Custom Code dependency extraction
    # -----------------------------------------------------------------------
    def _extract_custom_code_dependencies(self, node: ProjectionNode) -> None:
        """CP28: Custom code — depends on target entity via target_path."""
        pass  # File-level dependency, not graph-level

    # -----------------------------------------------------------------------
    # CP35: Geospatial dependency extraction
    # -----------------------------------------------------------------------
    def _extract_geospatial_dependencies(self, node: ProjectionNode) -> None:
        """CP35: GEOSPATIAL_SPEC — depends on ENTITY and GEOFENCE nodes."""
        entity_id = node.params.get("entity_id")
        if entity_id:
            self.graph.add_edge(
                source=node.id,
                target=entity_id,
                dep_type=DependencyType.GEO_ENTITY_DEPENDENCY,
                field="entity_id",
            )
        for gf_id in node.params.get("geofences", []):
            self.graph.add_edge(
                source=node.id,
                target=gf_id,
                dep_type=DependencyType.GEOFENCE_DEPENDENCY,
                field="geofences",
            )

    # -----------------------------------------------------------------------
    # CP40: Webhook dependency extraction
    # -----------------------------------------------------------------------
    def _extract_webhook_dependencies(self, node: ProjectionNode) -> None:
        """CP40: WEBHOOK_SUBSCRIPTION — depends on RETRY_POLICY."""
        retry_id = node.params.get("retry_policy_id")
        if retry_id:
            self.graph.add_edge(
                source=node.id,
                target=retry_id,
                dep_type=DependencyType.WEBHOOK_RETRY_DEPENDENCY,
                field="retry_policy_id",
            )

    # -----------------------------------------------------------------------
    # CP41: Chat dependency extraction
    # -----------------------------------------------------------------------
    def _extract_conversation_dependencies(self, node: ProjectionNode) -> None:
        """CP41: CONVERSATION — depends on ENTITY (for support chat)."""
        entity_id = node.params.get("entity_id")
        if entity_id:
            self.graph.add_edge(
                source=node.id,
                target=entity_id,
                dep_type=DependencyType.CONVERSATION_DEPENDENCY,
                field="entity_id",
            )

    def _extract_chat_message_dependencies(self, node: ProjectionNode) -> None:
        """CP41: CHAT_MESSAGE — depends on CONVERSATION."""
        conv_id = node.params.get("conversation_id")
        if conv_id:
            self.graph.add_edge(
                source=node.id,
                target=conv_id,
                dep_type=DependencyType.CHAT_CONVERSATION_DEPENDENCY,
                field="conversation_id",
            )

    # -----------------------------------------------------------------------
    # CP42: Approval dependency extraction
    # -----------------------------------------------------------------------
    def _extract_approval_request_dependencies(self, node: ProjectionNode) -> None:
        """CP42: APPROVAL_REQUEST — depends on ENTITY, STEPS, ESCALATION_RULE."""
        entity_id = node.params.get("entity_id")
        if entity_id:
            self.graph.add_edge(
                source=node.id,
                target=entity_id,
                dep_type=DependencyType.APPROVAL_REQUEST_DEPENDENCY,
                field="entity_id",
            )
        for step_id in node.params.get("steps", []):
            self.graph.add_edge(
                source=node.id,
                target=step_id,
                dep_type=DependencyType.APPROVAL_STEP_DEPENDENCY,
                field="steps",
            )
        esc_id = node.params.get("escalation_rule_id")
        if esc_id:
            self.graph.add_edge(
                source=node.id,
                target=esc_id,
                dep_type=DependencyType.APPROVAL_ESCALATION_DEPENDENCY,
                field="escalation_rule_id",
            )

    def _extract_approval_step_dependencies(self, node: ProjectionNode) -> None:
        """CP42: APPROVAL_STEP — depends on APPROVAL_REQUEST."""
        req_id = node.params.get("request_id")
        if req_id:
            self.graph.add_edge(
                source=node.id,
                target=req_id,
                dep_type=DependencyType.APPROVAL_STEP_DEPENDENCY,
                field="request_id",
            )

    # -----------------------------------------------------------------------
    # CP43: Versioning dependency extraction
    # -----------------------------------------------------------------------
    def _extract_version_config_dependencies(self, node: ProjectionNode) -> None:
        """CP43: VERSION_CONFIG — depends on ENTITY."""
        entity_id = node.params.get("entity_id")
        if entity_id:
            self.graph.add_edge(
                source=node.id,
                target=entity_id,
                dep_type=DependencyType.VERSION_ENTITY_DEPENDENCY,
                field="entity_id",
            )

    def _extract_history_record_dependencies(self, node: ProjectionNode) -> None:
        """CP43: HISTORY_RECORD — depends on ENTITY."""
        entity_id = node.params.get("entity_id")
        if entity_id:
            self.graph.add_edge(
                source=node.id,
                target=entity_id,
                dep_type=DependencyType.HISTORY_ENTITY_DEPENDENCY,
                field="entity_id",
            )

    # -----------------------------------------------------------------------
    # CP44: Bulk Ops dependency extraction
    # -----------------------------------------------------------------------
    def _extract_bulk_job_dependencies(self, node: ProjectionNode) -> None:
        """CP44: BULK_JOB — depends on ENTITY."""
        entity_id = node.params.get("entity_id")
        if entity_id:
            self.graph.add_edge(
                source=node.id,
                target=entity_id,
                dep_type=DependencyType.BULK_ENTITY_DEPENDENCY,
                field="entity_id",
            )

    # -----------------------------------------------------------------------
    # CP47: Retention dependency extraction
    # -----------------------------------------------------------------------
    def _extract_retention_policy_dependencies(self, node: ProjectionNode) -> None:
        """CP47: RETENTION_POLICY — depends on ENTITY."""
        entity_id = node.params.get("entity_id")
        if entity_id:
            self.graph.add_edge(
                source=node.id,
                target=entity_id,
                dep_type=DependencyType.RETENTION_ENTITY_DEPENDENCY,
                field="entity_id",
            )

    def _extract_erasure_request_dependencies(self, node: ProjectionNode) -> None:
        """CP47: ERASURE_REQUEST — depends on entities to erase."""
        for entity_id in node.params.get("entities", []):
            self.graph.add_edge(
                source=node.id,
                target=entity_id,
                dep_type=DependencyType.ERASURE_ENTITY_DEPENDENCY,
                field="entities",
            )

    # -----------------------------------------------------------------------
    # CP49: Consent dependency extraction
    # -----------------------------------------------------------------------
    def _extract_consent_record_dependencies(self, node: ProjectionNode) -> None:
        """CP49: CONSENT_RECORD — depends on CONSENT_POLICY."""
        pass  # Policy reference is resolved at runtime

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

        # Emits (events published by command)
        for event_id in node.params.get("emits", []):
            self.graph.add_edge(
                source=node.id,
                target=event_id,
                dep_type=DependencyType.COMMAND_EFFECT,
                field="emits"
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

    def _extract_event_dependencies(self, node: ProjectionNode) -> None:
        """Extract dependencies from event."""
        # Source entity
        source_entity = node.params.get("source_entity")
        if source_entity:
            self.graph.add_edge(
                source=node.id,
                target=source_entity,
                dep_type=DependencyType.ENTITY_REFERENCE,
                field="source_entity"
            )

    def _extract_ui_component_dependencies(self, node: ProjectionNode) -> None:
        """Extract dependencies from UI component."""
        # Entity binding
        entity_id = node.params.get("entity_id")
        if entity_id:
            self.graph.add_edge(
                source=node.id,
                target=entity_id,
                dep_type=DependencyType.GENERIC,
                field="entity_id"
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
