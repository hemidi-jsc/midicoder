"""
DSL v1 Loader - Load YAML files into ProjectionTree.

Module này cung cấp functions để load DSL YAML files và convert thành
ProjectionNode objects sử dụng v1 kernel (projection.py).

Thay thế v0 Pydantic-based loaders với v1 dataclass-based loading.

Features:
- Input validation cho paths và YAML data
- Error handling với MidicoderErrorManager
- Duplicate ID detection
- Missing file handling
- Comprehensive error messages với context
- T03-003: YAML parsing cache with file-based hashing
- T03-003: Incremental parsing support
- T03-003: Cache invalidation on file modification

Sử dụng:
    from midicoder.dsl import load_projection_tree

    tree = load_projection_tree(Path("dsl/brief1/"))
"""

from __future__ import annotations

import hashlib
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Optional

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from midicoder.errors import ErrorCode, MidicoderError, MidicoderErrorManager as EM
from midicoder.dsl.projection import (
    NodeKind,
    ProjectionNode,
    ProjectionTree,
)

yaml = YAML(typ="rt")


# ============================================================================
# T03-003: YAML Parsing Cache
# ============================================================================

class YAMLCache:
    """
    Cache for parsed YAML files with file-based hashing and TTL.
    
    Features:
    - Content hash-based cache keys (SHA-256 of file content)
    - Modification time tracking for invalidation
    - TTL support for cache entries
    - Hit/miss statistics
    - Incremental loading support
    """
    
    def __init__(self, max_size: int = 256, default_ttl: float = 600.0):
        """
        Initialize YAML cache.
        
        Args:
            max_size: Maximum number of cached files
            default_ttl: Default time-to-live in seconds (default 600 = 10 min)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[Any, float, str]] = OrderedDict()
        self._file_hashes: dict[str, str] = {}  # path -> content hash
        self._file_mtimes: dict[str, float] = {}  # path -> mtime
        self._hits = 0
        self._misses = 0
    
    def _compute_file_hash(self, path: Path) -> str:
        """Compute SHA-256 hash of file content."""
        hasher = hashlib.sha256()
        try:
            with path.open("rb") as f:
                # Read in chunks for large files
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except OSError:
            return ""
    
    def _get_cache_key(self, path: Path) -> str:
        """Generate cache key from path."""
        return f"yaml:{path.absolute()}"
    
    def get(self, path: Path) -> Optional[Any]:
        """
        Get cached YAML data if valid.
        
        Args:
            path: Path to YAML file
            
        Returns:
            Cached YAML data if valid, None otherwise
        """
        cache_key = self._get_cache_key(path)
        
        if cache_key not in self._cache:
            self._misses += 1
            return None
        
        cached_data, expiry, cached_hash = self._cache[cache_key]
        
        # Check TTL
        if time.time() > expiry:
            del self._cache[cache_key]
            self._file_hashes.pop(str(path), None)
            self._file_mtimes.pop(str(path), None)
            self._misses += 1
            return None
        
        # Check if file was modified
        try:
            current_mtime = path.stat().st_mtime
            cached_mtime = self._file_mtimes.get(str(path))
            
            if cached_mtime is not None and current_mtime > cached_mtime:
                # File was modified, invalidate cache
                del self._cache[cache_key]
                self._file_hashes.pop(str(path), None)
                self._file_mtimes.pop(str(path), None)
                self._misses += 1
                return None
        except OSError:
            pass
        
        # Move to end (most recently used)
        self._cache.move_to_end(cache_key)
        self._hits += 1
        return cached_data
    
    def set(self, path: Path, data: Any, ttl: Optional[float] = None) -> None:
        """
        Cache parsed YAML data.
        
        Args:
            path: Path to YAML file
            data: Parsed YAML data
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        cache_key = self._get_cache_key(path)
        
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
        else:
            # Evict oldest if at capacity
            while len(self._cache) >= self.max_size:
                oldest_key = self._cache.popitem(last=False)
                self._file_hashes.pop(oldest_key, None)
                # Extract path from key for mtime cleanup
                if oldest_key and oldest_key.startswith("yaml:"):
                    self._file_mtimes.pop(oldest_key[5:], None)
        
        expiry = time.time() + (ttl or self.default_ttl)
        file_hash = self._compute_file_hash(path)
        
        self._cache[cache_key] = (data, expiry, file_hash)
        self._file_hashes[str(path)] = file_hash
        
        try:
            self._file_mtimes[str(path)] = path.stat().st_mtime
        except OSError:
            pass
    
    def invalidate(self, path: Path) -> bool:
        """
        Invalidate cache for a specific file.
        
        Args:
            path: Path to YAML file
            
        Returns:
            True if entry was invalidated, False if not found
        """
        cache_key = self._get_cache_key(path)
        if cache_key in self._cache:
            del self._cache[cache_key]
            self._file_hashes.pop(str(path), None)
            self._file_mtimes.pop(str(path), None)
            return True
        return False
    
    def invalidate_all(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._file_hashes.clear()
        self._file_mtimes.clear()
    
    def check_modified(self, paths: list[Path]) -> list[Path]:
        """
        Check which files have been modified since caching.
        
        Args:
            paths: List of file paths to check
            
        Returns:
            List of paths that have been modified
        """
        modified = []
        for path in paths:
            try:
                current_mtime = path.stat().st_mtime
                cached_mtime = self._file_mtimes.get(str(path))
                if cached_mtime is None or current_mtime > cached_mtime:
                    modified.append(path)
            except OSError:
                modified.append(path)
        return modified
    
    @property
    def size(self) -> int:
        """Current number of cached entries."""
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
            "tracked_files": len(self._file_hashes),
        }


# Global YAML cache instance
_yaml_cache = YAMLCache(max_size=256, default_ttl=600.0)

# Global flag to enable/disable caching
_yaml_caching_enabled = True


def get_yaml_cache() -> YAMLCache:
    """Get the global YAML cache instance."""
    return _yaml_cache


def clear_yaml_cache() -> None:
    """Clear the global YAML cache."""
    _yaml_cache.invalidate_all()


def get_yaml_cache_stats() -> dict[str, Any]:
    """Get YAML cache statistics."""
    return _yaml_cache.stats


def enable_yaml_caching() -> None:
    """Enable YAML caching."""
    global _yaml_caching_enabled
    _yaml_caching_enabled = True


def disable_yaml_caching() -> None:
    """Disable YAML caching."""
    global _yaml_caching_enabled
    _yaml_caching_enabled = False


def is_yaml_caching_enabled() -> bool:
    """Check if YAML caching is enabled."""
    return _yaml_caching_enabled


def _load_yaml_raw(path: Path) -> Any:
    """
    Load YAML file without caching.
    
    Internal function for raw YAML loading.
    """
    # Validate path
    if not isinstance(path, Path):
        path = Path(path)

    if not path.exists():
        EM.raise_error(
            ErrorCode.DSL_FILE_NOT_FOUND,
            file_path=str(path),
            suggestions=[
                "Kiểm tra đường dẫn file có chính xác không",
                "Đảm bảo file tồn tại trong filesystem",
            ],
        )

    if not path.is_file():
        EM.raise_error(
            ErrorCode.DSL_FILE_NOT_FOUND,
            file_path=str(path),
            message=f"{path} không phải là file.",
        )

    # Parse YAML with error handling
    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.load(handle)
    except YAMLError as e:
        raise EM.wrap_exception(
            e,
            ErrorCode.DSL_YAML_PARSE_ERROR,
            file_path=str(path),
            yaml_error=str(e),
        )
    except OSError as e:
        raise EM.wrap_exception(
            e,
            ErrorCode.DSL_LOAD_FAILED,
            file_path=str(path),
            os_error=str(e),
        )


def load_yaml(path: Path, use_cache: bool = True) -> tuple[Any, bool]:
    """
    Load YAML file với optional caching.

    Args:
        path: Path đến YAML file
        use_cache: Whether to use cache (default True)

    Returns:
        Tuple of (parsed YAML data, is_cache_hit)

    Raises:
        MidicoderError: Nếu file không tồn tại hoặc YAML parse fail
    """
    # Validate path
    if not isinstance(path, Path):
        path = Path(path)

    # Check cache if enabled
    if use_cache and _yaml_caching_enabled:
        cached = _yaml_cache.get(path)
        if cached is not None:
            return cached, True
    
    # Load from file
    data = _load_yaml_raw(path)
    
    # Cache the result if enabled
    if use_cache and _yaml_caching_enabled:
        _yaml_cache.set(path, data)
    
    return data, False


def load_yaml_unsafe(path: Path) -> Any:
    """
    Load YAML file without validation (unsafe).
    
    Use with caution - does not validate file existence.
    
    Args:
        path: Path to YAML file
        
    Returns:
        Raw YAML data (may be None if file doesn't exist)
    """
    if not isinstance(path, Path):
        path = Path(path)
    
    if not path.exists():
        return None
    
    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.load(handle)
    except (YAMLError, OSError):
        return None


def _validate_dsl_path(dsl_path: Path) -> None:
    """
    Validate DSL directory path.

    Args:
        dsl_path: Path to DSL directory

    Raises:
        MidicoderError: Nếu path không hợp lệ
    """
    if not isinstance(dsl_path, Path):
        dsl_path = Path(dsl_path)

    if not dsl_path.exists():
        EM.raise_error(
            ErrorCode.DSL_FILE_NOT_FOUND,
            file_path=str(dsl_path),
            is_directory=True,
            suggestions=[
                "Kiểm tra đường dẫn DSL directory có chính xác không",
                "Đảm bảo directory tồn tại với các file YAML cần thiết",
            ],
        )

    if not dsl_path.is_dir():
        EM.raise_error(
            ErrorCode.DSL_FILE_NOT_FOUND,
            file_path=str(dsl_path),
            message=f"{dsl_path} không phải là directory.",
        )


def load_projection_tree(dsl_path: Path) -> ProjectionTree:
    """
    Load complete DSL directory vào ProjectionTree với comprehensive validation.

    Load các file YAML theo thứ tự:
    1. Domain layer: entities, value-objects, enums, errors, events
    2. Application layer: commands, queries, workflows, rules
    3. API layer: http-api, graphql-api
    4. Access control: policies, access-policy
    5. Infrastructure: persistence-model, integrations
    6. Observability: observability

    Args:
        dsl_path: Path đến DSL directory chứa entities.yaml, commands.yaml, etc.

    Returns:
        ProjectionTree với tất cả nodes đã load

    Raises:
        MidicoderError: Nếu path không hợp lệ hoặc load fail

    Example:
        tree = load_projection_tree(Path("dsl/brief1/"))
        print(f"Loaded {tree.node_count()} nodes")
    """
    # Convert to Path if needed
    if not isinstance(dsl_path, Path):
        dsl_path = Path(dsl_path)

    # Validate DSL path first
    _validate_dsl_path(dsl_path)

    tree = ProjectionTree()
    seen_ids: set[str] = set()

    def add_nodes(nodes: list[ProjectionNode]) -> None:
        """Add nodes to tree with duplicate ID check."""
        for node in nodes:
            if node.id in seen_ids:
                EM.raise_error(
                    ErrorCode.DSL_DUPLICATE_NODE_ID,
                    node_id=node.id,
                    node_kind=node.kind.value,
                    file_path=str(nodes[0].params.get("source", "unknown")),
                    suggestions=[
                        "Mỗi node ID phải duy nhất trong toàn bộ DSL",
                        "Review các file YAML để tìm duplicate IDs",
                    ],
                )
            seen_ids.add(node.id)
            tree.add_node(node)

    # Load entities
    entities_file = dsl_path / "entities.yaml"
    if entities_file.exists():
        add_nodes(_load_entities(entities_file))

    # Load value objects
    value_objects_file = dsl_path / "value-objects.yaml"
    if value_objects_file.exists():
        add_nodes(_load_value_objects(value_objects_file))

    # Load enums
    enums_file = dsl_path / "enums.yaml"
    if enums_file.exists():
        add_nodes(_load_enums(enums_file))

    # Load errors
    errors_file = dsl_path / "errors.yaml"
    if errors_file.exists():
        add_nodes(_load_errors(errors_file))

    # Load events
    events_file = dsl_path / "events.yaml"
    if events_file.exists():
        add_nodes(_load_events(events_file))

    # Load commands
    commands_file = dsl_path / "commands.yaml"
    if commands_file.exists():
        add_nodes(_load_commands(commands_file))

    # Load queries
    queries_file = dsl_path / "queries.yaml"
    if queries_file.exists():
        add_nodes(_load_queries(queries_file))

    # Load workflows
    workflows_file = dsl_path / "workflows.yaml"
    if workflows_file.exists():
        add_nodes(_load_workflows(workflows_file))

    # Load rules
    rules_file = dsl_path / "rules.yaml"
    if rules_file.exists():
        add_nodes(_load_rules(rules_file))

    # Load HTTP API
    http_file = dsl_path / "http-api.yaml"
    if http_file.exists():
        add_nodes(_load_http(http_file))

    # Load GraphQL API
    graphql_file = dsl_path / "graphql-api.yaml"
    if graphql_file.exists():
        add_nodes(_load_graphql(graphql_file))

    # Load projections
    projections_file = dsl_path / "projections.yaml"
    if projections_file.exists():
        add_nodes(_load_projections(projections_file))

    # Load policies
    policies_file = dsl_path / "policies.yaml"
    if policies_file.exists():
        add_nodes(_load_policies(policies_file))

    # Load access policy
    access_policy_file = dsl_path / "access-policy.yaml"
    if access_policy_file.exists():
        add_nodes(_load_access_policy(access_policy_file))

    # Load persistence model
    persistence_file = dsl_path / "persistence-model.yaml"
    if persistence_file.exists():
        add_nodes(_load_persistence(persistence_file))

    # Load integrations
    integrations_file = dsl_path / "integrations.yaml"
    if integrations_file.exists():
        add_nodes(_load_integrations(integrations_file))

    # Load observability
    observability_file = dsl_path / "observability.yaml"
    if observability_file.exists():
        add_nodes(_load_observability(observability_file))

    # Load frontends (CP18)
    frontends_file = dsl_path / "frontends.yaml"
    if frontends_file.exists():
        add_nodes(_load_frontends(frontends_file))

    return tree


# ============================================================================
# Entity Loaders
# ============================================================================

def _load_entities(path: Path) -> list[ProjectionNode]:
    """Load entities.yaml into ProjectionNodes."""
    data, _ = load_yaml(path)
    nodes = []
    
    if "entities" in data:
        for entity in data["entities"]:
            node = ProjectionNode(
                id=entity.get("id", ""),
                kind=NodeKind.ENTITY,
                params={
                    "id": entity.get("id"),
                    "description": entity.get("description"),
                    "fields": entity.get("fields", []),
                    "primary_key": entity.get("primary_key"),
                    "indexes": entity.get("indexes", []),
                    "constraints": entity.get("constraints", []),
                    "tags": entity.get("tags", []),
                    "tenant_scope": entity.get("tenant_scope"),
                    "source": "entities.yaml",
                },
            )
            nodes.append(node)
    
    return nodes


def _load_value_objects(path: Path) -> list[ProjectionNode]:
    """Load value-objects.yaml into ProjectionNodes."""
    data, _ = load_yaml(path)
    nodes = []
    
    if "value_objects" in data:
        for vo in data["value_objects"]:
            node = ProjectionNode(
                id=vo.get("id", ""),
                kind=NodeKind.VALUE_OBJECT,
                params={
                    "id": vo.get("id"),
                    "description": vo.get("description"),
                    "fields": vo.get("fields", []),
                    "immutable": vo.get("immutable", True),
                    "comparable": vo.get("comparable", False),
                    "tags": vo.get("tags", []),
                    "source": "value-objects.yaml",
                },
            )
            nodes.append(node)
    
    return nodes


def _load_enums(path: Path) -> list[ProjectionNode]:
    """Load enums.yaml into ProjectionNodes."""
    data, _ = load_yaml(path)
    nodes = []
    
    if "enums" in data:
        for enum_def in data["enums"]:
            node = ProjectionNode(
                id=enum_def.get("id", ""),
                kind=NodeKind.ENUM,
                params={
                    "id": enum_def.get("id"),
                    "description": enum_def.get("description"),
                    "values": enum_def.get("values", []),
                    "underlying_type": enum_def.get("underlying_type", "string"),
                    "tags": enum_def.get("tags", []),
                    "source": "enums.yaml",
                },
            )
            nodes.append(node)
    
    return nodes


def _load_errors(path: Path) -> list[ProjectionNode]:
    """Load errors.yaml into ProjectionNodes."""
    data, _ = load_yaml(path)
    nodes = []
    
    if "errors" in data:
        for error in data["errors"]:
            node = ProjectionNode(
                id=error.get("id", ""),
                kind=NodeKind.ERROR,
                params={
                    "id": error.get("id"),
                    "code": error.get("code"),
                    "description": error.get("description"),
                    "severity": error.get("severity"),
                    "category": error.get("category"),
                    "http_status": error.get("http_status"),
                    "recoverable": error.get("recoverable", False),
                    "fields": error.get("fields", []),
                    "tags": error.get("tags", []),
                    "source": "errors.yaml",
                },
            )
            nodes.append(node)
    
    return nodes


def _load_events(path: Path) -> list[ProjectionNode]:
    """Load events.yaml into ProjectionNodes."""
    data, _ = load_yaml(path)
    nodes = []
    
    if "events" in data:
        for event in data["events"]:
            node = ProjectionNode(
                id=event.get("id", ""),
                kind=NodeKind.EVENT,
                params={
                    "id": event.get("id"),
                    "description": event.get("description"),
                    "type": event.get("type"),
                    "source_entity": event.get("source_entity"),
                    "fields": event.get("fields", []),
                    "version": event.get("version", "v1"),
                    "tags": event.get("tags", []),
                    "tenant_scope": event.get("tenant_scope"),
                    "source": "events.yaml",
                },
            )
            nodes.append(node)
    
    return nodes


# ============================================================================
# Application Layer Loaders
# ============================================================================

def _load_commands(path: Path) -> list[ProjectionNode]:
    """Load commands.yaml into ProjectionNodes."""
    data, _ = load_yaml(path)
    nodes = []
    
    if "commands" in data:
        for command in data["commands"]:
            node = ProjectionNode(
                id=command.get("id", ""),
                kind=NodeKind.COMMAND,
                params={
                    "id": command.get("id"),
                    "description": command.get("description"),
                    "input": command.get("input", []),
                    "fetches": command.get("fetches", []),
                    "guards": command.get("guards", []),
                    "effects": command.get("effects", []),
                    "errors": command.get("errors", []),
                    "returns": command.get("returns", []),
                    "category": command.get("category"),
                    "emits": command.get("emits", []),
                    "required_roles": command.get("required_roles", []),
                    "required_permissions": command.get("required_permissions", []),
                    "writes_to": command.get("writes_to", []),
                    "datasource": command.get("datasource"),
                    "transaction": command.get("transaction", False),
                    "tenant_scope": command.get("tenant_scope"),
                    "source": "commands.yaml",
                    "tags": command.get("tags", []),
                },
            )
            nodes.append(node)
    
    return nodes


def _load_queries(path: Path) -> list[ProjectionNode]:
    """Load queries.yaml into ProjectionNodes."""
    data, _ = load_yaml(path)
    nodes = []
    
    if "queries" in data:
        for query in data["queries"]:
            node = ProjectionNode(
                id=query.get("id", ""),
                kind=NodeKind.QUERY,
                params={
                    "id": query.get("id"),
                    "description": query.get("description"),
                    "input": query.get("input", []),
                    "fetches": query.get("fetches", []),
                    "guards": query.get("guards", []),
                    "returns": query.get("returns", []),
                    "category": query.get("category"),
                    "reads_from": query.get("reads_from", []),
                    "required_roles": query.get("required_roles", []),
                    "required_permissions": query.get("required_permissions", []),
                    "datasource": query.get("datasource"),
                    "tenant_scope": query.get("tenant_scope"),
                    "source": "queries.yaml",
                    "tags": query.get("tags", []),
                },
            )
            nodes.append(node)
    
    return nodes


def _load_workflows(path: Path) -> list[ProjectionNode]:
    """Load workflows.yaml into ProjectionNodes."""
    data, _ = load_yaml(path)
    nodes = []
    
    if "workflows" in data:
        for workflow in data["workflows"]:
            node = ProjectionNode(
                id=workflow.get("id", ""),
                kind=NodeKind.WORKFLOW,
                params={
                    "id": workflow.get("id"),
                    "description": workflow.get("description"),
                    "states": workflow.get("states", []),
                    "transitions": workflow.get("transitions", []),
                    "guards": workflow.get("guards", []),
                    "effects": workflow.get("effects", []),
                    "tenant_scope": workflow.get("tenant_scope"),
                    "tags": workflow.get("tags", []),
                    "gateway_types": workflow.get("gateway_types", []),
                    "sub_workflows": workflow.get("sub_workflows", []),
                    "compensation": workflow.get("compensation", []),
                    "human_tasks": workflow.get("human_tasks", []),
                    "timers": workflow.get("timers", []),
                },
            )
            nodes.append(node)
    
    return nodes


def _load_rules(path: Path) -> list[ProjectionNode]:
    """Load rules.yaml into ProjectionNodes."""
    data, _ = load_yaml(path)
    nodes = []
    
    if "rules" in data:
        for rule in data["rules"]:
            node = ProjectionNode(
                id=rule.get("id", ""),
                kind=NodeKind.RULE,
                params={
                    "id": rule.get("id"),
                    "description": rule.get("description"),
                    "type": rule.get("type"),
                    "condition": rule.get("condition", {}),
                    "action": rule.get("action", {}),
                    "priority": rule.get("priority", 0),
                    "enabled": rule.get("enabled", True),
                    "tags": rule.get("tags", []),
                },
            )
            nodes.append(node)
    
    return nodes


# ============================================================================
# API Layer Loaders
# ============================================================================

def _load_http(path: Path) -> list[ProjectionNode]:
    """Load http-api.yaml into ProjectionNodes."""
    data, _ = load_yaml(path)
    nodes = []
    
    if "routes" in data:
        for route in data["routes"]:
            node = ProjectionNode(
                id=route.get("id", ""),
                kind=NodeKind.HTTP_ROUTE,
                params={
                    "id": route.get("id"),
                    "method": route.get("method"),
                    "path": route.get("path"),
                    "command_id": route.get("command_id"),
                    "query_id": route.get("query_id"),
                    "auth_required": route.get("auth_required", True),
                    "required_roles": route.get("required_roles", []),
                    "required_permissions": route.get("required_permissions", []),
                    "request_schema": route.get("request_schema", {}),
                    "response_schema": route.get("response_schema", {}),
                    "tags": route.get("tags", []),
                },
            )
            nodes.append(node)
    
    return nodes


def _load_graphql(path: Path) -> list[ProjectionNode]:
    """Load graphql-api.yaml into ProjectionNodes."""
    data, _ = load_yaml(path)
    nodes = []
    
    if "types" in data:
        for gql_type in data["types"]:
            node = ProjectionNode(
                id=gql_type.get("id", ""),
                kind=NodeKind.GRAPHQL_RESOLVER,
                params={
                    "id": gql_type.get("id"),
                    "description": gql_type.get("description"),
                    "operation": gql_type.get("operation", "query"),
                    "type_name": gql_type.get("type_name"),
                    "field_name": gql_type.get("field_name"),
                    "command_id": gql_type.get("command_id"),
                    "query_id": gql_type.get("query_id"),
                    "args": gql_type.get("args", []),
                    "returns": gql_type.get("returns", {}),
                    "auth_required": gql_type.get("auth_required", True),
                    "tags": gql_type.get("tags", []),
                },
            )
            nodes.append(node)
    
    return nodes


# ============================================================================
# Other Layer Loaders
# ============================================================================

def _load_projections(path: Path) -> list[ProjectionNode]:
    """Load projections.yaml into ProjectionNodes."""
    data, _ = load_yaml(path)
    nodes = []
    
    if "projections" in data:
        for projection in data["projections"]:
            # Projections can be various types, default to generic
            node = ProjectionNode(
                id=projection.get("id", ""),
                kind=NodeKind.CQRS_PROJECTION,
                params={
                    "id": projection.get("id"),
                    "description": projection.get("description"),
                    "source_events": projection.get("source_events", []),
                    "target_entity": projection.get("target_entity"),
                    "transformation": projection.get("transformation", {}),
                    "materialization": projection.get("materialization", "read_model"),
                    "tags": projection.get("tags", []),
                },
            )
            nodes.append(node)
    
    return nodes


def _load_policies(path: Path) -> list[ProjectionNode]:
    """Load policies.yaml into ProjectionNodes."""
    data, _ = load_yaml(path)
    nodes = []
    
    if "policies" in data:
        for policy in data["policies"]:
            node = ProjectionNode(
                id=policy.get("id", ""),
                kind=NodeKind.POLICY,
                params={
                    "id": policy.get("id"),
                    "description": policy.get("description"),
                    "effect": policy.get("effect"),
                    "subject": policy.get("subject", {}),
                    "action": policy.get("action", []),
                    "resource": policy.get("resource", {}),
                    "conditions": policy.get("conditions", []),
                    "tags": policy.get("tags", []),
                },
            )
            nodes.append(node)
    
    return nodes


def _load_access_policy(path: Path) -> list[ProjectionNode]:
    """Load access-policy.yaml into ProjectionNodes."""
    data, _ = load_yaml(path)
    nodes = []
    
    # Load roles
    if "roles" in data:
        for role in data["roles"]:
            node = ProjectionNode(
                id=role.get("id", ""),
                kind=NodeKind.ROLE,
                params={
                    "id": role.get("id"),
                    "description": role.get("description"),
                    "permissions": role.get("permissions", []),
                    "parent_roles": role.get("parent_roles", []),
                    "tenant_scope": role.get("tenant_scope"),
                    "tags": role.get("tags", []),
                },
            )
            nodes.append(node)
    
    # Load permissions
    if "permissions" in data:
        for perm in data["permissions"]:
            node = ProjectionNode(
                id=perm.get("id", ""),
                kind=NodeKind.PERMISSION,
                params={
                    "id": perm.get("id"),
                    "description": perm.get("description"),
                    "resource": perm.get("resource"),
                    "action": perm.get("action"),
                    "conditions": perm.get("conditions", []),
                    "tags": perm.get("tags", []),
                },
            )
            nodes.append(node)
    
    return nodes


def _load_persistence(path: Path) -> list[ProjectionNode]:
    """Load persistence-model.yaml into ProjectionNodes."""
    data, _ = load_yaml(path)
    nodes = []
    
    # Load datasources
    if "datasources" in data:
        for ds in data["datasources"]:
            node = ProjectionNode(
                id=ds.get("id", ""),
                kind=NodeKind.DATASOURCE,
                params={
                    "id": ds.get("id"),
                    "type": ds.get("type"),
                    "name": ds.get("name"),
                    "connection_string": ds.get("connection_string"),
                    "schema": ds.get("schema"),
                    "config": ds.get("config", {}),
                },
            )
            nodes.append(node)
    
    # Load tables
    if "tables" in data:
        for table in data["tables"]:
            node = ProjectionNode(
                id=table.get("id", ""),
                kind=NodeKind.TABLE,
                params={
                    "id": table.get("id"),
                    "name": table.get("name"),
                    "entity_id": table.get("entity_id"),
                    "datasource": table.get("datasource"),
                    "schema": table.get("schema"),
                    "columns": table.get("columns", []),
                    "indexes": table.get("indexes", []),
                    "constraints": table.get("constraints", []),
                },
            )
            nodes.append(node)
    
    # Load indexes
    if "indexes" in data:
        for index in data["indexes"]:
            node = ProjectionNode(
                id=index.get("id", ""),
                kind=NodeKind.INDEX,
                params={
                    "id": index.get("id"),
                    "name": index.get("name"),
                    "table_id": index.get("table_id"),
                    "columns": index.get("columns", []),
                    "unique": index.get("unique", False),
                    "type": index.get("type", "btree"),
                    "config": index.get("config", {}),
                },
            )
            nodes.append(node)
    
    return nodes


def _load_integrations(path: Path) -> list[ProjectionNode]:
    """Load integrations.yaml into ProjectionNodes."""
    data, _ = load_yaml(path)
    nodes = []
    
    if "integrations" in data:
        for integration in data["integrations"]:
            node = ProjectionNode(
                id=integration.get("id", ""),
                kind=NodeKind.INTEGRATION,
                params={
                    "id": integration.get("id"),
                    "name": integration.get("name"),
                    "type": integration.get("type"),
                    "provider": integration.get("provider"),
                    "auth_type": integration.get("auth_type"),
                    "config": integration.get("config", {}),
                    "required": integration.get("required", False),
                },
            )
            nodes.append(node)
    
    # Load auth providers
    if "auth_providers" in data:
        for auth in data["auth_providers"]:
            node = ProjectionNode(
                id=auth.get("id", ""),
                kind=NodeKind.AUTH_PROVIDER,
                params={
                    "id": auth.get("id"),
                    "type": auth.get("type"),
                    "provider": auth.get("provider"),
                    "config": auth.get("config", {}),
                    "scopes": auth.get("scopes", []),
                    "token_endpoint": auth.get("token_endpoint"),
                    "auth_endpoint": auth.get("auth_endpoint"),
                    "jwks_uri": auth.get("jwks_uri"),
                },
            )
            nodes.append(node)
    
    return nodes


def _load_observability(path: Path) -> list[ProjectionNode]:
    """Load observability.yaml into ProjectionNodes."""
    data, _ = load_yaml(path)
    nodes = []
    
    if "observability" in data:
        obs = data["observability"]
        
        # Load metrics
        if "metrics" in obs:
            for metric in obs["metrics"]:
                node = ProjectionNode(
                    id=metric.get("id", ""),
                    kind=NodeKind.METRIC,
                    params={
                        "id": metric.get("id"),
                        "description": metric.get("description"),
                        "type": metric.get("type"),
                        "name": metric.get("name"),
                        "unit": metric.get("unit"),
                        "labels": metric.get("labels", []),
                        "aggregation": metric.get("aggregation"),
                        "config": metric.get("config", {}),
                    },
                )
                nodes.append(node)
        
        # Load logs
        if "logs" in obs:
            for log in obs["logs"]:
                node = ProjectionNode(
                    id=log.get("id", ""),
                    kind=NodeKind.LOG,
                    params={
                        "id": log.get("id"),
                        "description": log.get("description"),
                        "name": log.get("name"),
                        "level": log.get("level"),
                        "format": log.get("format"),
                        "fields": log.get("fields", []),
                        "output": log.get("output"),
                        "config": log.get("config", {}),
                    },
                )
                nodes.append(node)
        
        # Load alerts
        if "alerts" in obs:
            for alert in obs["alerts"]:
                node = ProjectionNode(
                    id=alert.get("id", ""),
                    kind=NodeKind.ALERT,
                    params={
                        "id": alert.get("id"),
                        "description": alert.get("description"),
                        "name": alert.get("name"),
                        "condition": alert.get("condition", {}),
                        "severity": alert.get("severity"),
                        "channels": alert.get("channels", []),
                        "cooldown": alert.get("cooldown"),
                        "config": alert.get("config", {}),
                    },
                )
                nodes.append(node)
        
        # Load traces
        if "traces" in obs:
            for trace in obs["traces"]:
                node = ProjectionNode(
                    id=trace.get("id", ""),
                    kind=NodeKind.TRACE,
                    params={
                        "id": trace.get("id"),
                        "description": trace.get("description"),
                        "name": trace.get("name"),
                        "sampling_rate": trace.get("sampling_rate", 1.0),
                        "exporter": trace.get("exporter"),
                        "config": trace.get("config", {}),
                    },
                )
                nodes.append(node)
    
    return nodes


# ============================================================================
# CP18: Frontend Framework Loaders
# ============================================================================

def _load_frontends(path: Path) -> list[ProjectionNode]:
    """Load frontends.yaml vào ProjectionNodes (CP18).

    Parse cấu hình frontend application: app shell, routes, state store.

    Args:
        path: Đường dẫn đến frontends.yaml

    Returns:
        Danh sách ProjectionNodes cho frontend config
    """
    data, _ = load_yaml(path)
    nodes = []

    # Load frontend apps
    if "apps" in data:
        for app in data["apps"]:
            node = ProjectionNode(
                id=app.get("id", ""),
                kind=NodeKind.FRONTEND_APP,
                params={
                    "id": app.get("id"),
                    "name": app.get("name", ""),
                    "framework": app.get("framework", "react"),
                    "ui_framework": app.get("ui_framework", "material"),
                    "layout": app.get("layout", "sidebar"),
                    "description": app.get("description", ""),
                    "routes": app.get("routes", []),
                    "state_store": app.get("state_store"),
                    "router_strategy": app.get("router_strategy", "lazy"),
                    "tags": app.get("tags", []),
                    "source": "frontends.yaml",
                },
            )
            nodes.append(node)

    # Load individual routes (nếu tách riêng)
    if "routes" in data:
        for route in data["routes"]:
            node = ProjectionNode(
                id=route.get("id", ""),
                kind=NodeKind.FRONTEND_ROUTE,
                params={
                    "id": route.get("id"),
                    "path": route.get("path", ""),
                    "component": route.get("component", ""),
                    "is_lazy": route.get("is_lazy", False),
                    "children": route.get("children", []),
                    "guards": route.get("guards", []),
                    "required_permissions": route.get("required_permissions", []),
                    "data": route.get("data", {}),
                    "tags": route.get("tags", []),
                    "source": "frontends.yaml",
                },
            )
            nodes.append(node)

    # Load state stores (nếu tách riêng)
    if "stores" in data:
        for store in data["stores"]:
            node = ProjectionNode(
                id=store.get("id", ""),
                kind=NodeKind.FRONTEND_STORE,
                params={
                    "id": store.get("id"),
                    "store_type": store.get("store_type", "zustand"),
                    "entities": store.get("entities", []),
                    "selectors": store.get("selectors", []),
                    "actions": store.get("actions", []),
                    "persistence": store.get("persistence", "none"),
                    "tags": store.get("tags", []),
                    "source": "frontends.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# Extension Methods
# ============================================================================

def extend(self: ProjectionTree, nodes: list[ProjectionNode]) -> None:
    """Add multiple nodes to a ProjectionTree."""
    for node in nodes:
        self.add_node(node)


# Monkey-patch extend method
ProjectionTree.extend = extend