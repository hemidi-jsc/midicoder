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

    # Load UI components (CP19)
    ui_components_file = dsl_path / "ui-components.yaml"
    if ui_components_file.exists():
        add_nodes(_load_ui_components(ui_components_file))

    # P2-16: Load domain-specific DSL files
    plugins_file = dsl_path / "plugins.yaml"
    if plugins_file.exists():
        add_nodes(_load_plugins(plugins_file))

    schedules_file = dsl_path / "schedules.yaml"
    if schedules_file.exists():
        add_nodes(_load_schedules(schedules_file))

    financial_file = dsl_path / "financial.yaml"
    if financial_file.exists():
        add_nodes(_load_financial(financial_file))

    reports_file = dsl_path / "reports.yaml"
    if reports_file.exists():
        add_nodes(_load_reports(reports_file))

    etl_file = dsl_path / "etl.yaml"
    if etl_file.exists():
        add_nodes(_load_etl(etl_file))

    localization_file = dsl_path / "localization.yaml"
    if localization_file.exists():
        add_nodes(_load_localization(localization_file))

    versioning_file = dsl_path / "versioning.yaml"
    if versioning_file.exists():
        add_nodes(_load_versioning(versioning_file))

    payment_file = dsl_path / "payment.yaml"
    if payment_file.exists():
        add_nodes(_load_payment(payment_file))

    catalog_file = dsl_path / "catalog.yaml"
    if catalog_file.exists():
        add_nodes(_load_catalog(catalog_file))

    # CP32: Load state machines
    state_machines_file = dsl_path / "state_machines.yaml"
    if state_machines_file.exists():
        add_nodes(_load_state_machines(state_machines_file))

    # CP37: Load feature flags
    feature_flags_file = dsl_path / "feature_flags.yaml"
    if feature_flags_file.exists():
        add_nodes(_load_feature_flags(feature_flags_file))

    # CP21: Load auth UI config
    auth_ui_file = dsl_path / "auth_ui.yaml"
    if auth_ui_file.exists():
        add_nodes(_load_auth_ui(auth_ui_file))

    # CP22: Load realtime UI config
    realtime_ui_file = dsl_path / "realtime_ui.yaml"
    if realtime_ui_file.exists():
        add_nodes(_load_realtime_ui(realtime_ui_file))

    # CP28: Load multi-region & geo-replication
    multi_region_file = dsl_path / "multi_region.yaml"
    if multi_region_file.exists():
        add_nodes(_load_multi_region(multi_region_file))

    # CP31: Load scheduler
    scheduler_file = dsl_path / "scheduler.yaml"
    if scheduler_file.exists():
        add_nodes(_load_scheduler(scheduler_file))

    # CP35: Load geospatial
    geospatial_file = dsl_path / "geospatial.yaml"
    if geospatial_file.exists():
        add_nodes(_load_geospatial(geospatial_file))

    # CP36: Load tenant onboarding
    tenant_onboarding_file = dsl_path / "tenant_onboarding.yaml"
    if tenant_onboarding_file.exists():
        add_nodes(_load_tenant_onboarding(tenant_onboarding_file))

    # CP40: Load webhook
    webhook_file = dsl_path / "webhook.yaml"
    if webhook_file.exists():
        add_nodes(_load_webhook(webhook_file))

    # CP41: Load chat
    chat_file = dsl_path / "chat.yaml"
    if chat_file.exists():
        add_nodes(_load_chat(chat_file))

    # CP42: Load approval
    approval_file = dsl_path / "approval.yaml"
    if approval_file.exists():
        add_nodes(_load_approval(approval_file))

    # CP43: Load versioning — already handled by existing _load_versioning at line ~593
    # (extended with VERSION_CONFIG + HISTORY_RECORD nodes, keeps legacy api_versions)

    # CP44: Load bulk operations
    bulk_ops_file = dsl_path / "bulk_ops.yaml"
    if bulk_ops_file.exists():
        add_nodes(_load_bulk_ops(bulk_ops_file))

    # CP46: Load MFA
    mfa_file = dsl_path / "mfa.yaml"
    if mfa_file.exists():
        add_nodes(_load_mfa(mfa_file))

    # CP47: Load retention
    retention_file = dsl_path / "retention.yaml"
    if retention_file.exists():
        add_nodes(_load_retention(retention_file))

    # CP48: Load rate limiting
    rate_limiting_file = dsl_path / "rate_limiting.yaml"
    if rate_limiting_file.exists():
        add_nodes(_load_rate_limiting(rate_limiting_file))

    # CP49: Load consent
    consent_file = dsl_path / "consent.yaml"
    if consent_file.exists():
        add_nodes(_load_consent(consent_file))

    # === Phase 0 S2: DSL Loaders cho 13 CP còn thiếu ===

    # CP02: Load tenancy configuration
    tenancy_file = dsl_path / "tenancy.yaml"
    if tenancy_file.exists():
        add_nodes(_load_tenancy(tenancy_file))

    # CP03: Load auth providers
    auth_file = dsl_path / "auth.yaml"
    if auth_file.exists():
        add_nodes(_load_auth(auth_file))

    # CP07: Load infrastructure as code
    infrastructure_file = dsl_path / "infrastructure.yaml"
    if infrastructure_file.exists():
        add_nodes(_load_infrastructure(infrastructure_file))

    # CP09: Load caching
    caching_file = dsl_path / "caching.yaml"
    if caching_file.exists():
        add_nodes(_load_caching(caching_file))

    # CP10: Load search
    search_file = dsl_path / "search.yaml"
    if search_file.exists():
        add_nodes(_load_search(search_file))

    # CP11: Load file & media storage
    storage_file = dsl_path / "storage.yaml"
    if storage_file.exists():
        add_nodes(_load_storage(storage_file))

    # CP16: Load monitoring
    monitoring_file = dsl_path / "monitoring.yaml"
    if monitoring_file.exists():
        add_nodes(_load_monitoring(monitoring_file))

    # CP20: Load API client
    api_client_file = dsl_path / "api_client.yaml"
    if api_client_file.exists():
        add_nodes(_load_api_client(api_client_file))

    # CP23: Load testing
    testing_file = dsl_path / "testing.yaml"
    if testing_file.exists():
        add_nodes(_load_testing(testing_file))

    # CP24: Load quality gates
    quality_file = dsl_path / "quality.yaml"
    if quality_file.exists():
        add_nodes(_load_quality(quality_file))

    # CP25: Load performance testing
    performance_file = dsl_path / "performance.yaml"
    if performance_file.exists():
        add_nodes(_load_performance(performance_file))

    # CP26: Load documentation
    documentation_file = dsl_path / "documentation.yaml"
    if documentation_file.exists():
        add_nodes(_load_documentation(documentation_file))

    # CP30: Load AI-assisted development
    ai_assisted_file = dsl_path / "ai_assisted.yaml"
    if ai_assisted_file.exists():
        add_nodes(_load_ai_assisted(ai_assisted_file))

    # CP55: Load CI/CD Pipeline
    cicd_file = dsl_path / "cicd.yaml"
    if cicd_file.exists():
        add_nodes(_load_cicd(cicd_file))

    # CP56: Load environment & secrets
    env_secrets_file = dsl_path / "env_secrets.yaml"
    if env_secrets_file.exists():
        add_nodes(_load_env_secrets(env_secrets_file))

    # CP57: Load GraphQL Federation
    federation_file = dsl_path / "graphql_federation.yaml"
    if federation_file.exists():
        add_nodes(_load_graphql_federation(federation_file))

    # CP58: Load data encryption at rest
    encryption_file = dsl_path / "encryption.yaml"
    if encryption_file.exists():
        add_nodes(_load_encryption(encryption_file))

    # CP59: Load tenant billing & invoicing
    tenant_billing_file = dsl_path / "tenant_billing.yaml"
    if tenant_billing_file.exists():
        add_nodes(_load_tenant_billing(tenant_billing_file))

    # CP60: Load service discovery & config center
    service_discovery_file = dsl_path / "service_discovery.yaml"
    if service_discovery_file.exists():
        add_nodes(_load_service_discovery(service_discovery_file))

    # CP54: Load Kubernetes & Cloud Native
    kubernetes_file = dsl_path / "kubernetes.yaml"
    if kubernetes_file.exists():
        add_nodes(_load_kubernetes(kubernetes_file))

    # CP62: Load mobile backend
    mobile_backend_file = dsl_path / "mobile_backend.yaml"
    if mobile_backend_file.exists():
        add_nodes(_load_mobile_backend(mobile_backend_file))

    # CP63: Load recommendation engine
    recommendation_file = dsl_path / "recommendation.yaml"
    if recommendation_file.exists():
        add_nodes(_load_recommendation(recommendation_file))

    # CP64: Load contract testing
    contract_testing_file = dsl_path / "contract_testing.yaml"
    if contract_testing_file.exists():
        add_nodes(_load_contract_testing(contract_testing_file))

    # CP65: Load backup & recovery
    backup_recovery_file = dsl_path / "backup_recovery.yaml"
    if backup_recovery_file.exists():
        add_nodes(_load_backup_recovery(backup_recovery_file))

    return tree

# ============================================================================
# CP19: UI Component Loaders
# ============================================================================

def _load_ui_components(path: Path) -> list[ProjectionNode]:
    """Load ui-components.yaml into ProjectionNodes (CP19).

    Supports four categories:
    - ui_components: individual UI component declarations
    - ui_layouts: page layout declarations
    - ui_themes: theme/design token declarations
    - ui_form_builders: dynamic form builder declarations

    Args:
        path: Path to ui-components.yaml

    Returns:
        List of ProjectionNodes
    """
    data, _ = load_yaml(path)
    nodes = []

    # UI Components
    if "ui_components" in data:
        for comp in data["ui_components"]:
            node = ProjectionNode(
                id=comp.get("id", ""),
                kind=NodeKind.UI_COMPONENT,
                params={
                    "id": comp.get("id"),
                    "description": comp.get("description"),
                    "component_type": comp.get("component_type", "form_field"),
                    "entity_id": comp.get("entity_id"),
                    "properties": comp.get("properties", {}),
                    "tags": comp.get("tags", []),
                    "source": "ui-components.yaml",
                },
            )
            nodes.append(node)

    # UI Layouts
    if "ui_layouts" in data:
        for layout in data["ui_layouts"]:
            node = ProjectionNode(
                id=layout.get("id", ""),
                kind=NodeKind.UI_LAYOUT,
                params={
                    "id": layout.get("id"),
                    "description": layout.get("description"),
                    "layout_type": layout.get("layout_type", "page"),
                    "regions": layout.get("regions", []),
                    "properties": layout.get("properties", {}),
                    "tags": layout.get("tags", []),
                    "source": "ui-components.yaml",
                },
            )
            nodes.append(node)

    # UI Themes
    if "ui_themes" in data:
        for theme in data["ui_themes"]:
            node = ProjectionNode(
                id=theme.get("id", ""),
                kind=NodeKind.UI_THEME,
                params={
                    "id": theme.get("id"),
                    "description": theme.get("description"),
                    "name": theme.get("name", "default"),
                    "tokens": theme.get("tokens", {}),
                    "dark_mode": theme.get("dark_mode", False),
                    "tags": theme.get("tags", []),
                    "source": "ui-components.yaml",
                },
            )
            nodes.append(node)

    # UI Form Builders
    if "ui_form_builders" in data:
        for fb in data["ui_form_builders"]:
            node = ProjectionNode(
                id=fb.get("id", ""),
                kind=NodeKind.UI_FORM_BUILDER,
                params={
                    "id": fb.get("id"),
                    "description": fb.get("description"),
                    "entity_id": fb.get("entity_id"),
                    "fields": fb.get("fields", []),
                    "conditional_rules": fb.get("conditional_rules", []),
                    "properties": fb.get("properties", {}),
                    "tags": fb.get("tags", []),
                    "source": "ui-components.yaml",
                },
            )
            nodes.append(node)

    return nodes


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
# P2-16: Domain-Specific DSL Loaders
# ============================================================================

def _load_plugins(path: Path) -> list[ProjectionNode]:
    """Load plugins.yaml vào ProjectionNodes (CP27 — Plugin System).

    Parse plugin slots, contracts, và policies từ YAML.

    Args:
        path: Đường dẫn đến plugins.yaml

    Returns:
        Danh sách ProjectionNodes cho plugin nodes
    """
    data, _ = load_yaml(path)
    nodes = []

    # Plugin slots
    if "slots" in data:
        for slot in data["slots"]:
            node = ProjectionNode(
                id=slot.get("id", ""),
                kind=NodeKind.PLUGIN_SLOT,
                params={
                    "id": slot.get("id"),
                    "name": slot.get("name", ""),
                    "entity_id": slot.get("entity_id"),
                    "events": slot.get("events", []),
                    "priority_range": slot.get("priority_range", (0, 100)),
                    "is_tenant_aware": slot.get("is_tenant_aware", True),
                    "entities": slot.get("entities", []),
                    "tags": slot.get("tags", []),
                    "source": "plugins.yaml",
                },
            )
            nodes.append(node)

    # Plugin contracts
    if "contracts" in data:
        for contract in data["contracts"]:
            node = ProjectionNode(
                id=contract.get("id", ""),
                kind=NodeKind.PLUGIN_CONTRACT,
                params={
                    "id": contract.get("id"),
                    "slots": contract.get("slots", []),
                    "config_schema": contract.get("config_schema", {}),
                    "dependencies": contract.get("dependencies", []),
                    "tags": contract.get("tags", []),
                    "source": "plugins.yaml",
                },
            )
            nodes.append(node)

    # Plugin policies
    if "policies" in data:
        for policy in data["policies"]:
            node = ProjectionNode(
                id=policy.get("id", ""),
                kind=NodeKind.PLUGIN_POLICY,
                params={
                    "id": policy.get("id"),
                    "policy_type": policy.get("policy_type", "security"),
                    "rule": policy.get("rule", ""),
                    "enforced": policy.get("enforced", True),
                    "config": policy.get("config", {}),
                    "tags": policy.get("tags", []),
                    "source": "plugins.yaml",
                },
            )
            nodes.append(node)

    return nodes


def _load_schedules(path: Path) -> list[ProjectionNode]:
    """Load schedules.yaml vào ProjectionNodes (CP31 — Calendar & Scheduling).

    Parse calendar schedules từ YAML.

    Args:
        path: Đường dẫn đến schedules.yaml

    Returns:
        Danh sách ProjectionNodes cho calendar schedule nodes
    """
    data, _ = load_yaml(path)
    nodes = []

    if "schedules" in data:
        for schedule in data["schedules"]:
            node = ProjectionNode(
                id=schedule.get("id", ""),
                kind=NodeKind.CALENDAR_SCHEDULE,
                params={
                    "id": schedule.get("id"),
                    "description": schedule.get("description"),
                    "name": schedule.get("name", ""),
                    "calendar_type": schedule.get("calendar_type", "academic"),
                    "workflow_id": schedule.get("workflow_id"),
                    "workflow": schedule.get("workflow"),
                    "periods": schedule.get("periods", []),
                    "holidays": schedule.get("holidays", []),
                    "recurrence_rule": schedule.get("recurrence_rule"),
                    "timezone": schedule.get("timezone"),
                    "tags": schedule.get("tags", []),
                    "source": "schedules.yaml",
                },
            )
            nodes.append(node)

    return nodes


def _load_financial(path: Path) -> list[ProjectionNode]:
    """Load financial.yaml vào ProjectionNodes (CP33 — Financial Engine).

    Parse general ledger, financial instruments, currency exchange, tax rules,
    và subledgers từ YAML.

    Args:
        path: Đường dẫn đến financial.yaml

    Returns:
        Danh sách ProjectionNodes cho finance nodes
    """
    data, _ = load_yaml(path)
    nodes = []

    # General ledgers
    if "ledgers" in data:
        for ledger in data["ledgers"]:
            node = ProjectionNode(
                id=ledger.get("id", ""),
                kind=NodeKind.GENERAL_LEDGER,
                params={
                    "id": ledger.get("id"),
                    "description": ledger.get("description"),
                    "chart_of_accounts": ledger.get("chart_of_accounts", []),
                    "fiscal_year_start": ledger.get("fiscal_year_start"),
                    "currency": ledger.get("currency"),
                    "accounting_standard": ledger.get("accounting_standard"),
                    "entity_id": ledger.get("entity_id"),
                    "entities": ledger.get("entities", []),
                    "entries": ledger.get("entries", []),
                    "tags": ledger.get("tags", []),
                    "source": "financial.yaml",
                },
            )
            nodes.append(node)

    # Financial instruments
    if "instruments" in data:
        for instrument in data["instruments"]:
            node = ProjectionNode(
                id=instrument.get("id", ""),
                kind=NodeKind.FINANCIAL_INSTRUMENT,
                params={
                    "id": instrument.get("id"),
                    "symbol": instrument.get("symbol"),
                    "type": instrument.get("type"),
                    "entity_id": instrument.get("entity_id"),
                    "entities": instrument.get("entities", []),
                    "tags": instrument.get("tags", []),
                    "source": "financial.yaml",
                },
            )
            nodes.append(node)

    # Currency exchange
    if "currency_exchanges" in data:
        for exchange in data["currency_exchanges"]:
            node = ProjectionNode(
                id=exchange.get("id", ""),
                kind=NodeKind.CURRENCY_EXCHANGE,
                params={
                    "id": exchange.get("id"),
                    "base_currency": exchange.get("base_currency"),
                    "quote_currency": exchange.get("quote_currency"),
                    "exchange_rate": exchange.get("exchange_rate"),
                    "entity_id": exchange.get("entity_id"),
                    "tags": exchange.get("tags", []),
                    "source": "financial.yaml",
                },
            )
            nodes.append(node)

    # Tax rules
    if "tax_rules" in data:
        for rule in data["tax_rules"]:
            node = ProjectionNode(
                id=rule.get("id", ""),
                kind=NodeKind.TAX_RULE,
                params={
                    "id": rule.get("id"),
                    "tax_type": rule.get("tax_type"),
                    "rate": rule.get("rate"),
                    "jurisdiction": rule.get("jurisdiction"),
                    "applicable_items": rule.get("applicable_items", []),
                    "tags": rule.get("tags", []),
                    "source": "financial.yaml",
                },
            )
            nodes.append(node)

    # Subledgers
    if "subledgers" in data:
        for subledger in data["subledgers"]:
            node = ProjectionNode(
                id=subledger.get("id", ""),
                kind=NodeKind.SUBLEDGER,
                params={
                    "id": subledger.get("id"),
                    "ledger_type": subledger.get("ledger_type"),
                    "parent_ledger_id": subledger.get("parent_ledger_id"),
                    "entries": subledger.get("entries", []),
                    "tags": subledger.get("tags", []),
                    "source": "financial.yaml",
                },
            )
            nodes.append(node)

    return nodes


def _load_reports(path: Path) -> list[ProjectionNode]:
    """Load reports.yaml vào ProjectionNodes (CP34 — Reporting & Analytics).

    Parse reports, dashboards, exports, và scheduled reports từ YAML.

    Args:
        path: Đường dẫn đến reports.yaml

    Returns:
        Danh sách ProjectionNodes cho reporting nodes
    """
    data, _ = load_yaml(path)
    nodes = []

    # Reports
    if "reports" in data:
        for report in data["reports"]:
            node = ProjectionNode(
                id=report.get("id", ""),
                kind=NodeKind.REPORT,
                params={
                    "id": report.get("id"),
                    "description": report.get("description"),
                    "name": report.get("name", ""),
                    "data_sources": report.get("data_sources", []),
                    "fields": report.get("fields", []),
                    "filters": report.get("filters", []),
                    "groupings": report.get("groupings", []),
                    "aggregations": report.get("aggregations", []),
                    "tags": report.get("tags", []),
                    "source": "reports.yaml",
                },
            )
            nodes.append(node)

    # Dashboards
    if "dashboards" in data:
        for dashboard in data["dashboards"]:
            node = ProjectionNode(
                id=dashboard.get("id", ""),
                kind=NodeKind.DASHBOARD,
                params={
                    "id": dashboard.get("id"),
                    "description": dashboard.get("description"),
                    "name": dashboard.get("name", ""),
                    "widgets": dashboard.get("widgets", []),
                    "data_sources": dashboard.get("data_sources", []),
                    "refresh_interval": dashboard.get("refresh_interval"),
                    "tags": dashboard.get("tags", []),
                    "source": "reports.yaml",
                },
            )
            nodes.append(node)

    # Exports
    if "exports" in data:
        for export in data["exports"]:
            node = ProjectionNode(
                id=export.get("id", ""),
                kind=NodeKind.EXPORT,
                params={
                    "id": export.get("id"),
                    "description": export.get("description"),
                    "name": export.get("name", ""),
                    "source_id": export.get("source_id"),
                    "format": export.get("format"),
                    "tags": export.get("tags", []),
                    "source": "reports.yaml",
                },
            )
            nodes.append(node)

    # Scheduled reports
    if "scheduled_reports" in data:
        for scheduled in data["scheduled_reports"]:
            node = ProjectionNode(
                id=scheduled.get("id", ""),
                kind=NodeKind.SCHEDULED_REPORT,
                params={
                    "id": scheduled.get("id"),
                    "report_id": scheduled.get("report_id"),
                    "frequency": scheduled.get("frequency"),
                    "time": scheduled.get("time"),
                    "recipients": scheduled.get("recipients", []),
                    "tags": scheduled.get("tags", []),
                    "source": "reports.yaml",
                },
            )
            nodes.append(node)

    return nodes


def _load_etl(path: Path) -> list[ProjectionNode]:
    """Load etl.yaml vào ProjectionNodes (CP38 — Data Migration & Batch).

    Parse data migrations và batch jobs từ YAML.

    Args:
        path: Đường dẫn đến etl.yaml

    Returns:
        Danh sách ProjectionNodes cho ETL nodes
    """
    data, _ = load_yaml(path)
    nodes = []

    # Data migrations
    if "migrations" in data:
        for migration in data["migrations"]:
            node = ProjectionNode(
                id=migration.get("id", ""),
                kind=NodeKind.DATA_MIGRATION,
                params={
                    "id": migration.get("id"),
                    "description": migration.get("description"),
                    "source_schema": migration.get("source_schema"),
                    "target_schema": migration.get("target_schema"),
                    "mapping_rules": migration.get("mapping_rules", []),
                    "steps": migration.get("steps", []),
                    "input_sources": migration.get("input_sources", []),
                    "output_destinations": migration.get("output_destinations", []),
                    "tags": migration.get("tags", []),
                    "source": "etl.yaml",
                },
            )
            nodes.append(node)

    # Batch jobs
    if "batch_jobs" in data:
        for job in data["batch_jobs"]:
            node = ProjectionNode(
                id=job.get("id", ""),
                kind=NodeKind.BATCH_JOB,
                params={
                    "id": job.get("id"),
                    "description": job.get("description"),
                    "job_type": job.get("job_type"),
                    "schedule": job.get("schedule"),
                    "steps": job.get("steps", []),
                    "input_sources": job.get("input_sources", []),
                    "output_destinations": job.get("output_destinations", []),
                    "tags": job.get("tags", []),
                    "source": "etl.yaml",
                },
            )
            nodes.append(node)

    return nodes


def _load_localization(path: Path) -> list[ProjectionNode]:
    """Load localization.yaml vào ProjectionNodes (CP39 — Multi-language).

    Parse localization specs từ YAML.

    Args:
        path: Đường dẫn đến localization.yaml

    Returns:
        Danh sách ProjectionNodes cho localization nodes
    """
    data, _ = load_yaml(path)
    nodes = []

    if "localizations" in data:
        for loc in data["localizations"]:
            node = ProjectionNode(
                id=loc.get("id", ""),
                kind=NodeKind.LOCALIZATION,
                params={
                    "id": loc.get("id"),
                    "description": loc.get("description"),
                    "entity_id": loc.get("entity_id"),
                    "locales": loc.get("locales", []),
                    "default_locale": loc.get("default_locale"),
                    "field_mappings": loc.get("field_mappings", []),
                    "fallback_strategy": loc.get("fallback_strategy"),
                    "tags": loc.get("tags", []),
                    "source": "localization.yaml",
                },
            )
            nodes.append(node)

    return nodes


def _load_versioning(path: Path) -> list[ProjectionNode]:
    """Load versioning.yaml vào ProjectionNodes (CP43 — API Versioning).

    Parse API versions, deprecation notices, và pagination specs từ YAML.

    Args:
        path: Đường dẫn đến versioning.yaml

    Returns:
        Danh sách ProjectionNodes cho versioning nodes
    """
    data, _ = load_yaml(path)
    nodes = []

    # API versions
    if "api_versions" in data:
        for version in data["api_versions"]:
            node = ProjectionNode(
                id=version.get("id", ""),
                kind=NodeKind.API_VERSION,
                params={
                    "id": version.get("id"),
                    "description": version.get("description"),
                    "name": version.get("name", ""),
                    "version": version.get("version"),
                    "api_id": version.get("api_id"),
                    "status": version.get("status"),
                    "release_date": version.get("release_date"),
                    "deprecation_date": version.get("deprecation_date"),
                    "entities": version.get("entities", []),
                    "tags": version.get("tags", []),
                    "source": "versioning.yaml",
                },
            )
            nodes.append(node)

    # Deprecation notices
    if "deprecation_notices" in data:
        for notice in data["deprecation_notices"]:
            node = ProjectionNode(
                id=notice.get("id", ""),
                kind=NodeKind.DEPRECATION_NOTICE,
                params={
                    "id": notice.get("id"),
                    "description": notice.get("description"),
                    "name": notice.get("name", ""),
                    "api_version_id": notice.get("api_version_id"),
                    "reason": notice.get("reason"),
                    "migration_guide": notice.get("migration_guide"),
                    "tags": notice.get("tags", []),
                    "source": "versioning.yaml",
                },
            )
            nodes.append(node)

    # Pagination specs
    if "pagination_specs" in data:
        for spec in data["pagination_specs"]:
            node = ProjectionNode(
                id=spec.get("id", ""),
                kind=NodeKind.PAGINATION_SPEC,
                params={
                    "id": spec.get("id"),
                    "description": spec.get("description"),
                    "name": spec.get("name", ""),
                    "page_size": spec.get("page_size"),
                    "max_page_size": spec.get("max_page_size"),
                    "cursor_enabled": spec.get("cursor_enabled", False),
                    "sort_fields": spec.get("sort_fields", []),
                    "tags": spec.get("tags", []),
                    "source": "versioning.yaml",
                },
            )
            nodes.append(node)

    return nodes


def _load_payment(path: Path) -> list[ProjectionNode]:
    """Load payment.yaml vào ProjectionNodes (CP45 — Payment Processing).

    Parse payment gateways từ YAML.

    Args:
        path: Đường dẫn đến payment.yaml

    Returns:
        Danh sách ProjectionNodes cho payment nodes
    """
    data, _ = load_yaml(path)
    nodes = []

    if "payment_gateways" in data:
        for gateway in data["payment_gateways"]:
            node = ProjectionNode(
                id=gateway.get("id", ""),
                kind=NodeKind.PAYMENT_GATEWAY,
                params={
                    "id": gateway.get("id"),
                    "description": gateway.get("description"),
                    "provider": gateway.get("provider"),
                    "supported_methods": gateway.get("supported_methods", []),
                    "currencies": gateway.get("currencies", []),
                    "webhook_url": gateway.get("webhook_url"),
                    "webhook_id": gateway.get("webhook_id"),
                    "sandbox_mode": gateway.get("sandbox_mode", False),
                    "tags": gateway.get("tags", []),
                    "source": "payment.yaml",
                },
            )
            nodes.append(node)

    return nodes


def _load_catalog(path: Path) -> list[ProjectionNode]:
    """Load catalog.yaml vào ProjectionNodes (CP50 — Product Catalog & Taxonomy).

    Parse product catalogs và faceted search indexes từ YAML.

    Args:
        path: Đường dẫn đến catalog.yaml

    Returns:
        Danh sách ProjectionNodes cho catalog nodes
    """
    data, _ = load_yaml(path)
    nodes = []

    # Product catalogs
    if "catalogs" in data:
        for catalog in data["catalogs"]:
            node = ProjectionNode(
                id=catalog.get("id", ""),
                kind=NodeKind.PRODUCT_CATALOG,
                params={
                    "id": catalog.get("id"),
                    "description": catalog.get("description"),
                    "categories": catalog.get("categories", []),
                    "products": catalog.get("products", []),
                    "inventory_tracking": catalog.get("inventory_tracking", False),
                    "entity_id": catalog.get("entity_id"),
                    "search_index_id": catalog.get("search_index_id"),
                    "tags": catalog.get("tags", []),
                    "source": "catalog.yaml",
                },
            )
            nodes.append(node)

    # Faceted search indexes
    if "faceted_search" in data:
        for search in data["faceted_search"]:
            node = ProjectionNode(
                id=search.get("id", ""),
                kind=NodeKind.FACETED_SEARCH_INDEX,
                params={
                    "id": search.get("id"),
                    "description": search.get("description"),
                    "entity_id": search.get("entity_id"),
                    "columns": search.get("columns", []),
                    "facets": search.get("facets", []),
                    "tags": search.get("tags", []),
                    "source": "catalog.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP32: State Machine Loader
# ============================================================================

def _load_state_machines(path: Path) -> list[ProjectionNode]:
    """Load state_machines.yaml vào ProjectionNodes (CP32 — State Machine Engine).

    Parse state machines và transitions từ YAML.

    Args:
        path: Đường dẫn đến state_machines.yaml

    Returns:
        Danh sách ProjectionNodes cho state machine nodes
    """
    data, _ = load_yaml(path)
    nodes = []

    # State machines
    if "state_machines" in data:
        for sm in data["state_machines"]:
            node = ProjectionNode(
                id=sm.get("id", ""),
                kind=NodeKind.STATE_MACHINE,
                params={
                    "id": sm.get("id"),
                    "description": sm.get("description"),
                    "name": sm.get("name"),
                    "entity_id": sm.get("entity_id"),
                    "initial_state": sm.get("initial_state"),
                    "states": sm.get("states", []),
                    "transitions": sm.get("transitions", []),
                    "is_global": sm.get("is_global", False),
                    "tags": sm.get("tags", []),
                    "source": "state_machines.yaml",
                },
            )
            nodes.append(node)

    # State transitions
    if "transitions" in data:
        for trans in data["transitions"]:
            node = ProjectionNode(
                id=trans.get("id", ""),
                kind=NodeKind.STATE_TRANSITION,
                params={
                    "id": trans.get("id"),
                    "description": trans.get("description"),
                    "machine_id": trans.get("machine_id"),
                    "from_state": trans.get("from_state"),
                    "to_state": trans.get("to_state"),
                    "guard": trans.get("guard"),
                    "effect": trans.get("effect"),
                    "tags": trans.get("tags", []),
                    "source": "state_machines.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP37: Feature Flags & Dynamic Config Loader
# ============================================================================

def _load_feature_flags(path: Path) -> list[ProjectionNode]:
    """Load feature_flags.yaml vào ProjectionNodes (CP37 — Feature Flags & Dynamic Config).

    Parse feature flags, A/B experiments, và dynamic configs từ YAML.

    Args:
        path: Đường dẫn đến feature_flags.yaml

    Returns:
        Danh sách ProjectionNodes cho feature flag nodes
    """
    data, _ = load_yaml(path)
    nodes = []

    # Feature flags
    if "feature_flags" in data:
        for flag in data["feature_flags"]:
            node = ProjectionNode(
                id=flag.get("id", ""),
                kind=NodeKind.FEATURE_FLAG,
                params={
                    "id": flag.get("id"),
                    "description": flag.get("description"),
                    "key": flag.get("key"),
                    "flag_type": flag.get("flag_type", "boolean"),
                    "default_value": flag.get("default_value", False),
                    "tenants": flag.get("tenants", []),
                    "environments": flag.get("environments", []),
                    "percentage": flag.get("percentage"),
                    "targeted_users": flag.get("targeted_users", []),
                    "tags": flag.get("tags", []),
                    "source": "feature_flags.yaml",
                },
            )
            nodes.append(node)

    # A/B experiments
    if "experiments" in data:
        for exp in data["experiments"]:
            node = ProjectionNode(
                id=exp.get("id", ""),
                kind=NodeKind.AB_EXPERIMENT,
                params={
                    "id": exp.get("id"),
                    "description": exp.get("description"),
                    "name": exp.get("name"),
                    "variants": exp.get("variants", []),
                    "traffic_split": exp.get("traffic_split", []),
                    "assignment_key": exp.get("assignment_key"),
                    "is_active": exp.get("is_active", True),
                    "tags": exp.get("tags", []),
                    "source": "feature_flags.yaml",
                },
            )
            nodes.append(node)

    # Dynamic configs
    if "dynamic_configs" in data:
        for config in data["dynamic_configs"]:
            node = ProjectionNode(
                id=config.get("id", ""),
                kind=NodeKind.DYNAMIC_CONFIG,
                params={
                    "id": config.get("id"),
                    "description": config.get("description"),
                    "key": config.get("key"),
                    "value_type": config.get("value_type", "string"),
                    "default_value": config.get("default_value"),
                    "scope": config.get("scope", "global"),
                    "tags": config.get("tags", []),
                    "source": "feature_flags.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP21: Authentication UI Loader
# ============================================================================

def _load_auth_ui(path: Path) -> list[ProjectionNode]:
    """Load auth_ui.yaml vào ProjectionNodes (CP21 — Authentication UI).

    Args:
        path: Đường dẫn đến auth_ui.yaml

    Returns:
        Danh sách ProjectionNodes cho auth UI config
    """
    data, _ = load_yaml(path)
    nodes = []

    if "auth_ui" in data:
        config = data["auth_ui"]
        node = ProjectionNode(
            id=config.get("id", "auth_ui"),
            kind=NodeKind.AUTH_UI_CONFIG,
            params={
                "id": config.get("id", "auth_ui"),
                "description": config.get("description"),
                "pages": config.get("pages", ["login", "register", "forgot_password"]),
                "ui_framework": config.get("ui_framework", "material"),
                "session_timeout_minutes": config.get("session_timeout_minutes", 30),
                "oauth_providers": config.get("oauth_providers", []),
                "enable_mfa": config.get("enable_mfa", False),
                "enable_captcha": config.get("enable_captcha", False),
                "enable_self_register": config.get("enable_self_register", True),
                "tags": config.get("tags", []),
                "source": "auth_ui.yaml",
            },
        )
        nodes.append(node)

    return nodes


# ============================================================================
# CP22: Real-time UI Loader
# ============================================================================

def _load_realtime_ui(path: Path) -> list[ProjectionNode]:
    """Load realtime_ui.yaml vào ProjectionNodes (CP22 — Real-time UI).

    Args:
        path: Đường dẫn đến realtime_ui.yaml

    Returns:
        Danh sách ProjectionNodes cho channel spec và widget config
    """
    data, _ = load_yaml(path)
    nodes = []

    if "channels" in data:
        for ch in data["channels"]:
            node = ProjectionNode(
                id=ch.get("id", ""),
                kind=NodeKind.CHANNEL_SPEC,
                params={
                    "id": ch.get("id"),
                    "description": ch.get("description"),
                    "topic": ch.get("topic", ""),
                    "transport": ch.get("transport", "websocket"),
                    "entity_id": ch.get("entity_id"),
                    "auth_required": ch.get("auth_required", True),
                    "tags": ch.get("tags", []),
                    "source": "realtime_ui.yaml",
                },
            )
            nodes.append(node)

    if "widgets" in data:
        for w in data["widgets"]:
            node = ProjectionNode(
                id=w.get("id", ""),
                kind=NodeKind.WIDGET_CONFIG,
                params={
                    "id": w.get("id"),
                    "description": w.get("description"),
                    "widget_type": w.get("widget_type", "live_feed"),
                    "channel_id": w.get("channel_id"),
                    "entity_id": w.get("entity_id"),
                    "refresh_interval_ms": w.get("refresh_interval_ms", 5000),
                    "tags": w.get("tags", []),
                    "source": "realtime_ui.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP28: Custom Code Injection Loader
# ============================================================================

def _load_custom_code(path: Path) -> list[ProjectionNode]:
    """Load custom_code.yaml vào ProjectionNodes (CP28 — Custom Code Injection).

    Args:
        path: Đường dẫn đến custom_code.yaml

    Returns:
        Danh sách ProjectionNodes cho custom code blocks, hooks, patch rules
    """
    data, _ = load_yaml(path)
    nodes = []

    if "code_blocks" in data:
        for block in data["code_blocks"]:
            node = ProjectionNode(
                id=block.get("id", ""),
                kind=NodeKind.CUSTOM_CODE_BLOCK,
                params={
                    "id": block.get("id"),
                    "description": block.get("description"),
                    "target_path": block.get("target_path", ""),
                    "inject_point": block.get("inject_point", "bottom"),
                    "language": block.get("language", "python"),
                    "code": block.get("code", ""),
                    "condition": block.get("condition"),
                    "tags": block.get("tags", []),
                    "source": "custom_code.yaml",
                },
            )
            nodes.append(node)

    if "hooks" in data:
        for h in data["hooks"]:
            node = ProjectionNode(
                id=h.get("id", ""),
                kind=NodeKind.CUSTOM_HOOK,
                params={
                    "id": h.get("id"),
                    "description": h.get("description"),
                    "event": h.get("event", "after_emit"),
                    "handler": h.get("handler", ""),
                    "priority": h.get("priority", 100),
                    "tags": h.get("tags", []),
                    "source": "custom_code.yaml",
                },
            )
            nodes.append(node)

    if "patch_rules" in data:
        for p in data["patch_rules"]:
            node = ProjectionNode(
                id=p.get("id", ""),
                kind=NodeKind.CUSTOM_PATCH_RULE,
                params={
                    "id": p.get("id"),
                    "description": p.get("description"),
                    "target_path": p.get("target_path", ""),
                    "pattern": p.get("pattern", ""),
                    "replacement": p.get("replacement", ""),
                    "flags": p.get("flags", ""),
                    "tags": p.get("tags", []),
                    "source": "custom_code.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP31: Scheduler Loader
# ============================================================================

def _load_scheduler(path: Path) -> list[ProjectionNode]:
    """Load scheduler.yaml vào ProjectionNodes (CP31 — Scheduler & Cron Engine).

    Args:
        path: Đường dẫn đến scheduler.yaml

    Returns:
        Danh sách ProjectionNodes cho schedule nodes
    """
    data, _ = load_yaml(path)
    nodes = []

    if "schedules" in data:
        for s in data["schedules"]:
            node = ProjectionNode(
                id=s.get("id", ""),
                kind=NodeKind.SCHEDULE,
                params={
                    "id": s.get("id"),
                    "description": s.get("description"),
                    "cron_expr": s.get("cron_expr", "*/5 * * * *"),
                    "handler": s.get("handler", ""),
                    "timezone": s.get("timezone", "UTC"),
                    "enabled": s.get("enabled", True),
                    "tags": s.get("tags", []),
                    "source": "scheduler.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP35: Geospatial Loader (extends existing partial)
# ============================================================================

def _load_geospatial(path: Path) -> list[ProjectionNode]:
    """Load geospatial.yaml vào ProjectionNodes (CP35 — Geospatial Services).

    Args:
        path: Đường dẫn đến geospatial.yaml

    Returns:
        Danh sách ProjectionNodes cho geospatial spec và geofence
    """
    data, _ = load_yaml(path)
    nodes = []

    if "specs" in data:
        for spec in data["specs"]:
            node = ProjectionNode(
                id=spec.get("id", ""),
                kind=NodeKind.GEOSPATIAL_SPEC,
                params={
                    "id": spec.get("id"),
                    "description": spec.get("description"),
                    "entity_id": spec.get("entity_id", ""),
                    "location_field": spec.get("location_field", "location"),
                    "geofences": spec.get("geofences", []),
                    "enable_routing": spec.get("enable_routing", False),
                    "enable_distance": spec.get("enable_distance", False),
                    "tags": spec.get("tags", []),
                    "source": "geospatial.yaml",
                },
            )
            nodes.append(node)

    if "geofences" in data:
        for gf in data["geofences"]:
            node = ProjectionNode(
                id=gf.get("id", ""),
                kind=NodeKind.GEOFENCE,
                params={
                    "id": gf.get("id"),
                    "description": gf.get("description"),
                    "name": gf.get("name", ""),
                    "shape": gf.get("shape", "circle"),
                    "center": gf.get("center"),
                    "radius_meters": gf.get("radius_meters"),
                    "vertices": gf.get("vertices"),
                    "corners": gf.get("corners"),
                    "alert_on_enter": gf.get("alert_on_enter", False),
                    "alert_on_exit": gf.get("alert_on_exit", False),
                    "notification_channel": gf.get("notification_channel"),
                    "tags": gf.get("tags", []),
                    "source": "geospatial.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP36: Tenant Onboarding Loader
# ============================================================================

def _load_tenant_onboarding(path: Path) -> list[ProjectionNode]:
    """Load tenant_onboarding.yaml vào ProjectionNodes (CP36 — Tenant Onboarding).

    Args:
        path: Đường dẫn đến tenant_onboarding.yaml

    Returns:
        Danh sách ProjectionNodes cho tenant registration và subscription
    """
    data, _ = load_yaml(path)
    nodes = []

    if "registration" in data:
        reg = data["registration"]
        node = ProjectionNode(
            id=reg.get("id", "tenant_registration"),
            kind=NodeKind.TENANT_REGISTRATION,
            params={
                "id": reg.get("id", "tenant_registration"),
                "description": reg.get("description"),
                "enable_self_service": reg.get("enable_self_service", True),
                "require_verification": reg.get("require_verification", True),
                "default_plan": reg.get("default_plan", "free"),
                "trial_days": reg.get("trial_days", 14),
                "auto_provision": reg.get("auto_provision", True),
                "tags": reg.get("tags", []),
                "source": "tenant_onboarding.yaml",
            },
        )
        nodes.append(node)

    if "subscriptions" in data:
        for sub in data["subscriptions"]:
            node = ProjectionNode(
                id=sub.get("id", ""),
                kind=NodeKind.TENANT_SUBSCRIPTION,
                params={
                    "id": sub.get("id"),
                    "description": sub.get("description"),
                    "plan_name": sub.get("plan_name", ""),
                    "billing_cycle": sub.get("billing_cycle", "monthly"),
                    "features": sub.get("features", []),
                    "max_users": sub.get("max_users", 1),
                    "max_storage_gb": sub.get("max_storage_gb", 1),
                    "price": sub.get("price", 0.0),
                    "currency": sub.get("currency", "USD"),
                    "tags": sub.get("tags", []),
                    "source": "tenant_onboarding.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP40: Webhook Loader
# ============================================================================

def _load_webhook(path: Path) -> list[ProjectionNode]:
    """Load webhook.yaml vào ProjectionNodes (CP40 — Webhook & Outbound Integration).

    Args:
        path: Đường dẫn đến webhook.yaml

    Returns:
        Danh sách ProjectionNodes cho webhook subscription và retry policy
    """
    data, _ = load_yaml(path)
    nodes = []

    if "subscriptions" in data:
        for sub in data["subscriptions"]:
            node = ProjectionNode(
                id=sub.get("id", ""),
                kind=NodeKind.WEBHOOK_SUBSCRIPTION,
                params={
                    "id": sub.get("id"),
                    "description": sub.get("description"),
                    "event_types": sub.get("event_types", []),
                    "url": sub.get("url", ""),
                    "auth_type": sub.get("auth_type", "none"),
                    "secret": sub.get("secret", ""),
                    "headers": sub.get("headers", {}),
                    "retry_policy_id": sub.get("retry_policy_id"),
                    "is_active": sub.get("is_active", True),
                    "tags": sub.get("tags", []),
                    "source": "webhook.yaml",
                },
            )
            nodes.append(node)

    if "retry_policies" in data:
        for rp in data["retry_policies"]:
            node = ProjectionNode(
                id=rp.get("id", ""),
                kind=NodeKind.WEBHOOK_RETRY_POLICY,
                params={
                    "id": rp.get("id"),
                    "description": rp.get("description"),
                    "max_retries": rp.get("max_retries", 3),
                    "base_delay_ms": rp.get("base_delay_ms", 1000),
                    "max_delay_ms": rp.get("max_delay_ms", 60000),
                    "backoff_multiplier": rp.get("backoff_multiplier", 2.0),
                    "http_retry_codes": rp.get("http_retry_codes", [500, 502, 503]),
                    "tags": rp.get("tags", []),
                    "source": "webhook.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP41: Chat Loader
# ============================================================================

def _load_chat(path: Path) -> list[ProjectionNode]:
    """Load chat.yaml vào ProjectionNodes (CP41 — Chat & Messaging).

    Args:
        path: Đường dẫn đến chat.yaml

    Returns:
        Danh sách ProjectionNodes cho conversation và chat message
    """
    data, _ = load_yaml(path)
    nodes = []

    if "conversations" in data:
        for conv in data["conversations"]:
            node = ProjectionNode(
                id=conv.get("id", ""),
                kind=NodeKind.CONVERSATION,
                params={
                    "id": conv.get("id"),
                    "description": conv.get("description"),
                    "conversation_type": conv.get("conversation_type", "direct"),
                    "entity_id": conv.get("entity_id"),
                    "participants": conv.get("participants", []),
                    "max_participants": conv.get("max_participants", 100),
                    "enable_typing_indicator": conv.get("enable_typing_indicator", True),
                    "enable_read_receipt": conv.get("enable_read_receipt", True),
                    "tags": conv.get("tags", []),
                    "source": "chat.yaml",
                },
            )
            nodes.append(node)

    if "messages" in data:
        for msg in data["messages"]:
            node = ProjectionNode(
                id=msg.get("id", ""),
                kind=NodeKind.CHAT_MESSAGE,
                params={
                    "id": msg.get("id"),
                    "description": msg.get("description"),
                    "conversation_id": msg.get("conversation_id", ""),
                    "message_type": msg.get("message_type", "text"),
                    "sender_id": msg.get("sender_id"),
                    "content": msg.get("content", ""),
                    "max_file_size_mb": msg.get("max_file_size_mb", 10),
                    "enable_reactions": msg.get("enable_reactions", True),
                    "tags": msg.get("tags", []),
                    "source": "chat.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP42: Approval Workflow Loader
# ============================================================================

def _load_approval(path: Path) -> list[ProjectionNode]:
    """Load approval.yaml vào ProjectionNodes (CP42 — Approval Workflow Engine).

    Args:
        path: Đường dẫn đến approval.yaml

    Returns:
        Danh sách ProjectionNodes cho approval request, step, escalation
    """
    data, _ = load_yaml(path)
    nodes = []

    if "requests" in data:
        for req in data["requests"]:
            node = ProjectionNode(
                id=req.get("id", ""),
                kind=NodeKind.APPROVAL_REQUEST,
                params={
                    "id": req.get("id"),
                    "description": req.get("description"),
                    "entity_id": req.get("entity_id", ""),
                    "chain_type": req.get("chain_type", "sequential"),
                    "steps": req.get("steps", []),
                    "escalation_rule_id": req.get("escalation_rule_id"),
                    "tags": req.get("tags", []),
                    "source": "approval.yaml",
                },
            )
            nodes.append(node)

    if "steps" in data:
        for step in data["steps"]:
            node = ProjectionNode(
                id=step.get("id", ""),
                kind=NodeKind.APPROVAL_STEP,
                params={
                    "id": step.get("id"),
                    "description": step.get("description"),
                    "request_id": step.get("request_id", ""),
                    "step_number": step.get("step_number", 1),
                    "approver_type": step.get("approver_type", "role"),
                    "approver_id": step.get("approver_id"),
                    "deadline_hours": step.get("deadline_hours", 24),
                    "can_delegate": step.get("can_delegate", True),
                    "tags": step.get("tags", []),
                    "source": "approval.yaml",
                },
            )
            nodes.append(node)

    if "escalation_rules" in data:
        for esc in data["escalation_rules"]:
            node = ProjectionNode(
                id=esc.get("id", ""),
                kind=NodeKind.ESCALATION_RULE,
                params={
                    "id": esc.get("id"),
                    "description": esc.get("description"),
                    "trigger_on": esc.get("trigger_on", "timeout"),
                    "timeout_hours": esc.get("timeout_hours", 24),
                    "escalate_to": esc.get("escalate_to", "manager"),
                    "notify_original": esc.get("notify_original", True),
                    "max_escalations": esc.get("max_escalations", 3),
                    "tags": esc.get("tags", []),
                    "source": "approval.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP43: Versioning Loader (extends existing partial)
# ============================================================================

def _load_versioning(path: Path) -> list[ProjectionNode]:
    """Load versioning.yaml vào ProjectionNodes (CP43 — Versioning & History).

    Args:
        path: Đường dẫn đến versioning.yaml

    Returns:
        Danh sách ProjectionNodes cho version config và history record
    """
    data, _ = load_yaml(path)
    nodes = []

    # CP43: Versioning configs
    if "versioning_configs" in data:
        for vc in data["versioning_configs"]:
            node = ProjectionNode(
                id=vc.get("id", ""),
                kind=NodeKind.VERSION_CONFIG,
                params={
                    "id": vc.get("id"),
                    "description": vc.get("description"),
                    "entity_id": vc.get("entity_id", ""),
                    "enable_versioning": vc.get("enable_versioning", True),
                    "enable_soft_delete": vc.get("enable_soft_delete", False),
                    "enable_history": vc.get("enable_history", True),
                    "max_versions": vc.get("max_versions", 50),
                    "auto_cleanup": vc.get("auto_cleanup", False),
                    "tags": vc.get("tags", []),
                    "source": "versioning.yaml",
                },
            )
            nodes.append(node)

    # CP43: History records
    if "history_records" in data:
        for hr in data["history_records"]:
            node = ProjectionNode(
                id=hr.get("id", ""),
                kind=NodeKind.HISTORY_RECORD,
                params={
                    "id": hr.get("id"),
                    "description": hr.get("description"),
                    "entity_id": hr.get("entity_id", ""),
                    "operation": hr.get("operation", "create"),
                    "stored_fields": hr.get("stored_fields", []),
                    "retention_days": hr.get("retention_days", 365),
                    "tags": hr.get("tags", []),
                    "source": "versioning.yaml",
                },
            )
            nodes.append(node)

    # Legacy: API versions
    if "api_versions" in data:
        for av in data["api_versions"]:
            node = ProjectionNode(
                id=av.get("id", ""),
                kind=NodeKind.API_VERSION,
                params={
                    "id": av.get("id"),
                    "version": av.get("version", "1.0.0"),
                    "api_id": av.get("api_id"),
                    "status": av.get("status", "active"),
                    "tags": av.get("tags", []),
                    "source": "versioning.yaml",
                },
            )
            nodes.append(node)

    # Legacy: Deprecation notices
    if "deprecation_notices" in data:
        for dep in data["deprecation_notices"]:
            node = ProjectionNode(
                id=dep.get("id", ""),
                kind=NodeKind.DEPRECATION_NOTICE,
                params={
                    "id": dep.get("id"),
                    "api_version_id": dep.get("api_version_id"),
                    "reason": dep.get("reason", ""),
                    "tags": dep.get("tags", []),
                    "source": "versioning.yaml",
                },
            )
            nodes.append(node)

    # Legacy: Pagination specs
    if "pagination_specs" in data:
        for ps in data["pagination_specs"]:
            node = ProjectionNode(
                id=ps.get("id", ""),
                kind=NodeKind.PAGINATION_SPEC,
                params={
                    "id": ps.get("id"),
                    "page_size": ps.get("page_size", 20),
                    "tags": ps.get("tags", []),
                    "source": "versioning.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP44: Bulk Operations Loader
# ============================================================================

def _load_bulk_ops(path: Path) -> list[ProjectionNode]:
    """Load bulk_ops.yaml vào ProjectionNodes (CP44 — Bulk Operations Engine).

    Args:
        path: Đường dẫn đến bulk_ops.yaml

    Returns:
        Danh sách ProjectionNodes cho bulk job
    """
    data, _ = load_yaml(path)
    nodes = []

    if "jobs" in data:
        for job in data["jobs"]:
            node = ProjectionNode(
                id=job.get("id", ""),
                kind=NodeKind.BULK_JOB,
                params={
                    "id": job.get("id"),
                    "description": job.get("description"),
                    "entity_id": job.get("entity_id", ""),
                    "operation": job.get("operation", "update"),
                    "chunk_size": job.get("chunk_size", 100),
                    "max_concurrency": job.get("max_concurrency", 5),
                    "retry_on_failure": job.get("retry_on_failure", True),
                    "max_retries": job.get("max_retries", 3),
                    "dlq_enabled": job.get("dlq_enabled", True),
                    "tags": job.get("tags", []),
                    "source": "bulk_ops.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP46: MFA Loader
# ============================================================================

def _load_mfa(path: Path) -> list[ProjectionNode]:
    """Load mfa.yaml vào ProjectionNodes (CP46 — MFA & Advanced Authentication).

    Args:
        path: Đường dẫn đến mfa.yaml

    Returns:
        Danh sách ProjectionNodes cho MFA credential và challenge
    """
    data, _ = load_yaml(path)
    nodes = []

    if "credentials" in data:
        for cred in data["credentials"]:
            node = ProjectionNode(
                id=cred.get("id", ""),
                kind=NodeKind.MFA_CREDENTIAL,
                params={
                    "id": cred.get("id"),
                    "description": cred.get("description"),
                    "methods": cred.get("methods", ["totp"]),
                    "enforce_on": cred.get("enforce_on", "login"),
                    "grace_period_days": cred.get("grace_period_days", 7),
                    "backup_codes_count": cred.get("backup_codes_count", 10),
                    "tags": cred.get("tags", []),
                    "source": "mfa.yaml",
                },
            )
            nodes.append(node)

    if "challenges" in data:
        for ch in data["challenges"]:
            node = ProjectionNode(
                id=ch.get("id", ""),
                kind=NodeKind.MFA_CHALLENGE,
                params={
                    "id": ch.get("id"),
                    "description": ch.get("description"),
                    "method": ch.get("method", "totp"),
                    "timeout_seconds": ch.get("timeout_seconds", 300),
                    "max_attempts": ch.get("max_attempts", 3),
                    "lockout_minutes": ch.get("lockout_minutes", 15),
                    "tags": ch.get("tags", []),
                    "source": "mfa.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP47: Data Retention Loader
# ============================================================================

def _load_retention(path: Path) -> list[ProjectionNode]:
    """Load retention.yaml vào ProjectionNodes (CP47 — Data Retention & Lifecycle).

    Args:
        path: Đường dẫn đến retention.yaml

    Returns:
        Danh sách ProjectionNodes cho retention policy và erasure request
    """
    data, _ = load_yaml(path)
    nodes = []

    if "policies" in data:
        for p in data["policies"]:
            node = ProjectionNode(
                id=p.get("id", ""),
                kind=NodeKind.RETENTION_POLICY,
                params={
                    "id": p.get("id"),
                    "description": p.get("description"),
                    "entity_id": p.get("entity_id", ""),
                    "retention_period_days": p.get("retention_period_days", 365),
                    "trigger_type": p.get("trigger_type", "time"),
                    "action_after_expiry": p.get("action_after_expiry", "archive"),
                    "exempt_entities": p.get("exempt_entities", []),
                    "tags": p.get("tags", []),
                    "source": "retention.yaml",
                },
            )
            nodes.append(node)

    if "erasure_requests" in data:
        for er in data["erasure_requests"]:
            node = ProjectionNode(
                id=er.get("id", ""),
                kind=NodeKind.ERASURE_REQUEST,
                params={
                    "id": er.get("id"),
                    "description": er.get("description"),
                    "user_id": er.get("user_id", ""),
                    "scope": er.get("scope", "all"),
                    "entities": er.get("entities", []),
                    "reason": er.get("reason", ""),
                    "verification_required": er.get("verification_required", True),
                    "deadline_days": er.get("deadline_days", 30),
                    "tags": er.get("tags", []),
                    "source": "retention.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP48: Rate Limiting Loader
# ============================================================================

def _load_rate_limiting(path: Path) -> list[ProjectionNode]:
    """Load rate_limiting.yaml vào ProjectionNodes (CP48 — Rate Limiting & Quota).

    Args:
        path: Đường dẫn đến rate_limiting.yaml

    Returns:
        Danh sách ProjectionNodes cho rate limit policy và quota config
    """
    data, _ = load_yaml(path)
    nodes = []

    if "policies" in data:
        for p in data["policies"]:
            node = ProjectionNode(
                id=p.get("id", ""),
                kind=NodeKind.RATE_LIMIT_POLICY,
                params={
                    "id": p.get("id"),
                    "description": p.get("description"),
                    "strategy": p.get("strategy", "sliding_window"),
                    "requests_per_window": p.get("requests_per_window", 100),
                    "window_seconds": p.get("window_seconds", 60),
                    "burst_size": p.get("burst_size", 20),
                    "apply_to": p.get("apply_to", "endpoint"),
                    "endpoints": p.get("endpoints", []),
                    "tags": p.get("tags", []),
                    "source": "rate_limiting.yaml",
                },
            )
            nodes.append(node)

    if "quotas" in data:
        for q in data["quotas"]:
            node = ProjectionNode(
                id=q.get("id", ""),
                kind=NodeKind.QUOTA_CONFIG,
                params={
                    "id": q.get("id"),
                    "description": q.get("description"),
                    "level": q.get("level", "user"),
                    "quota_type": q.get("quota_type", "requests"),
                    "limit": q.get("limit", 1000),
                    "period": q.get("period", "hour"),
                    "overage_action": q.get("overage_action", "reject"),
                    "tags": q.get("tags", []),
                    "source": "rate_limiting.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP49: Consent & Preference Loader
# ============================================================================

def _load_consent(path: Path) -> list[ProjectionNode]:
    """Load consent.yaml vào ProjectionNodes (CP49 — Consent & Preference Management).

    Args:
        path: Đường dẫn đến consent.yaml

    Returns:
        Danh sách ProjectionNodes cho consent record, policy, cookie/comm preference
    """
    data, _ = load_yaml(path)
    nodes = []

    if "records" in data:
        for rec in data["records"]:
            node = ProjectionNode(
                id=rec.get("id", ""),
                kind=NodeKind.CONSENT_RECORD,
                params={
                    "id": rec.get("id"),
                    "description": rec.get("description"),
                    "user_id": rec.get("user_id", ""),
                    "consent_type": rec.get("consent_type", "data_processing"),
                    "granted": rec.get("granted", False),
                    "withdrawn_at": rec.get("withdrawn_at"),
                    "policy_version": rec.get("policy_version"),
                    "tags": rec.get("tags", []),
                    "source": "consent.yaml",
                },
            )
            nodes.append(node)

    if "policies" in data:
        for pol in data["policies"]:
            node = ProjectionNode(
                id=pol.get("id", ""),
                kind=NodeKind.CONSENT_POLICY,
                params={
                    "id": pol.get("id"),
                    "description": pol.get("description"),
                    "tenant_id": pol.get("tenant_id", ""),
                    "consent_types": pol.get("consent_types", []),
                    "require_explicit_consent": pol.get("require_explicit_consent", True),
                    "cookie_categories": pol.get("cookie_categories", []),
                    "data_retention_days": pol.get("data_retention_days", 365),
                    "tags": pol.get("tags", []),
                    "source": "consent.yaml",
                },
            )
            nodes.append(node)

    if "cookie_preferences" in data:
        for cp in data["cookie_preferences"]:
            node = ProjectionNode(
                id=cp.get("id", ""),
                kind=NodeKind.COOKIE_PREFERENCE,
                params={
                    "id": cp.get("id"),
                    "description": cp.get("description"),
                    "user_id": cp.get("user_id", ""),
                    "necessary": cp.get("necessary", True),
                    "analytics": cp.get("analytics", False),
                    "marketing": cp.get("marketing", False),
                    "preferences": cp.get("preferences", True),
                    "tags": cp.get("tags", []),
                    "source": "consent.yaml",
                },
            )
            nodes.append(node)

    if "communication_preferences" in data:
        for cm in data["communication_preferences"]:
            node = ProjectionNode(
                id=cm.get("id", ""),
                kind=NodeKind.COMM_PREFERENCE,
                params={
                    "id": cm.get("id"),
                    "description": cm.get("description"),
                    "user_id": cm.get("user_id", ""),
                    "email_enabled": cm.get("email_enabled", True),
                    "sms_enabled": cm.get("sms_enabled", False),
                    "push_enabled": cm.get("push_enabled", True),
                    "in_app_enabled": cm.get("in_app_enabled", True),
                    "frequency": cm.get("frequency", "realtime"),
                    "tags": cm.get("tags", []),
                    "source": "consent.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# Phase 0 S2: DSL Loaders cho 13 CP còn thiếu
# ============================================================================

# --- CP02: Multi-Tenancy Configuration ---

def _load_tenancy(path: Path) -> list[ProjectionNode]:
    """Load tenancy.yaml vào ProjectionNodes (CP02 — Multi-Tenancy).

    Args:
        path: Đường dẫn đến tenancy.yaml

    Returns:
        Danh sách ProjectionNodes cho tenancy config và isolation policy
    """
    data, _ = load_yaml(path)
    nodes = []

    if "tenancy_config" in data:
        cfg = data["tenancy_config"]
        node = ProjectionNode(
            id=cfg.get("id", "default_tenancy"),
            kind=NodeKind.TENANCY_CONFIG,
            params={
                "id": cfg.get("id", "default_tenancy"),
                "description": cfg.get("description"),
                "isolation_strategy": cfg.get("isolation_strategy", "row_level"),
                "tenant_id_field": cfg.get("tenant_id_field", "tenant_id"),
                "auto_provision": cfg.get("auto_provision", False),
                "max_tenants": cfg.get("max_tenants", 1000),
                "tags": cfg.get("tags", []),
                "source": "tenancy.yaml",
            },
        )
        nodes.append(node)

    if "isolation_policies" in data:
        for pol in data["isolation_policies"]:
            node = ProjectionNode(
                id=pol.get("id", ""),
                kind=NodeKind.TENANT_ISOLATION_POLICY,
                params={
                    "id": pol.get("id"),
                    "description": pol.get("description"),
                    "policy_type": pol.get("policy_type", "strict"),
                    "data_leakage_prevention": pol.get("data_leakage_prevention", True),
                    "cross_tenant_query_allowed": pol.get("cross_tenant_query_allowed", False),
                    "tags": pol.get("tags", []),
                    "source": "tenancy.yaml",
                },
            )
            nodes.append(node)

    return nodes


# --- CP03: Auth Providers ---

def _load_auth(path: Path) -> list[ProjectionNode]:
    """Load auth.yaml vào ProjectionNodes (CP03 — Authentication).

    Args:
        path: Đường dẫn đến auth.yaml

    Returns:
        Danh sách ProjectionNodes cho auth providers
    """
    data, _ = load_yaml(path)
    nodes = []

    if "providers" in data:
        for prov in data["providers"]:
            node = ProjectionNode(
                id=prov.get("id", ""),
                kind=NodeKind.AUTH_PROVIDER,
                params={
                    "id": prov.get("id"),
                    "description": prov.get("description"),
                    "type": prov.get("type", "oauth2"),
                    "provider": prov.get("provider", ""),
                    "client_id": prov.get("client_id", ""),
                    "scopes": prov.get("scopes", []),
                    "auth_endpoint": prov.get("auth_endpoint", ""),
                    "tags": prov.get("tags", []),
                    "source": "auth.yaml",
                },
            )
            nodes.append(node)

    return nodes


# --- CP07: Infrastructure as Code ---

def _load_infrastructure(path: Path) -> list[ProjectionNode]:
    """Load infrastructure.yaml vào ProjectionNodes (CP07 — IAC).

    Args:
        path: Đường dẫn đến infrastructure.yaml

    Returns:
        Danh sách ProjectionNodes cho IAC resource và network
    """
    data, _ = load_yaml(path)
    nodes = []

    if "resources" in data:
        for res in data["resources"]:
            node = ProjectionNode(
                id=res.get("id", ""),
                kind=NodeKind.IAC_RESOURCE,
                params={
                    "id": res.get("id"),
                    "description": res.get("description"),
                    "resource_type": res.get("resource_type", "compute"),
                    "provider": res.get("provider", "aws"),
                    "region": res.get("region", "us-east-1"),
                    "configuration": res.get("configuration", {}),
                    "tags": res.get("tags", []),
                    "source": "infrastructure.yaml",
                },
            )
            nodes.append(node)

    if "networks" in data:
        for net in data["networks"]:
            node = ProjectionNode(
                id=net.get("id", ""),
                kind=NodeKind.IAC_NETWORK,
                params={
                    "id": net.get("id"),
                    "description": net.get("description"),
                    "vpc_cidr": net.get("vpc_cidr", "10.0.0.0/16"),
                    "subnets": net.get("subnets", []),
                    "security_groups": net.get("security_groups", []),
                    "tags": net.get("tags", []),
                    "source": "infrastructure.yaml",
                },
            )
            nodes.append(node)

    return nodes


# --- CP09: Cache ---

def _load_caching(path: Path) -> list[ProjectionNode]:
    """Load caching.yaml vào ProjectionNodes (CP09 — Cache).

    Args:
        path: Đường dẫn đến caching.yaml

    Returns:
        Danh sách ProjectionNodes cho cache config
    """
    data, _ = load_yaml(path)
    nodes = []

    if "caches" in data:
        for cache in data["caches"]:
            node = ProjectionNode(
                id=cache.get("id", ""),
                kind=NodeKind.CACHE,
                params={
                    "id": cache.get("id"),
                    "description": cache.get("description"),
                    "backend": cache.get("backend", "redis"),
                    "ttl_seconds": cache.get("ttl_seconds", 300),
                    "max_size": cache.get("max_size", 10000),
                    "eviction_policy": cache.get("eviction_policy", "lru"),
                    "tags": cache.get("tags", []),
                    "source": "caching.yaml",
                },
            )
            nodes.append(node)

    if "strategies" in data:
        for strat in data["strategies"]:
            node = ProjectionNode(
                id=strat.get("id", ""),
                kind=NodeKind.CACHE_STRATEGY,
                params={
                    "id": strat.get("id"),
                    "description": strat.get("description"),
                    "strategy": strat.get("strategy", "read_through"),
                    "invalidation": strat.get("invalidation", "ttl"),
                    "tags": strat.get("tags", []),
                    "source": "caching.yaml",
                },
            )
            nodes.append(node)

    return nodes


# --- CP10: Search ---

def _load_search(path: Path) -> list[ProjectionNode]:
    """Load search.yaml vào ProjectionNodes (CP10 — Search).

    Args:
        path: Đường dẫn đến search.yaml

    Returns:
        Danh sách ProjectionNodes cho search index và query
    """
    data, _ = load_yaml(path)
    nodes = []

    if "indexes" in data:
        for idx in data["indexes"]:
            node = ProjectionNode(
                id=idx.get("id", ""),
                kind=NodeKind.SEARCH_INDEX,
                params={
                    "id": idx.get("id"),
                    "description": idx.get("description"),
                    "engine": idx.get("engine", "elasticsearch"),
                    "entity_id": idx.get("entity_id", ""),
                    "fields": idx.get("fields", []),
                    "tags": idx.get("tags", []),
                    "source": "search.yaml",
                },
            )
            nodes.append(node)

    if "queries" in data:
        for q in data["queries"]:
            node = ProjectionNode(
                id=q.get("id", ""),
                kind=NodeKind.SEARCH_QUERY,
                params={
                    "id": q.get("id"),
                    "description": q.get("description"),
                    "index_id": q.get("index_id", ""),
                    "query_type": q.get("query_type", "fulltext"),
                    "filters": q.get("filters", []),
                    "tags": q.get("tags", []),
                    "source": "search.yaml",
                },
            )
            nodes.append(node)

    return nodes


# --- CP11: File & Media Storage ---

def _load_storage(path: Path) -> list[ProjectionNode]:
    """Load storage.yaml vào ProjectionNodes (CP11 — File & Media Storage).

    Args:
        path: Đường dẫn đến storage.yaml

    Returns:
        Danh sách ProjectionNodes cho file storage và media processing
    """
    data, _ = load_yaml(path)
    nodes = []

    if "buckets" in data:
        for bucket in data["buckets"]:
            node = ProjectionNode(
                id=bucket.get("id", ""),
                kind=NodeKind.FILE_STORAGE,
                params={
                    "id": bucket.get("id"),
                    "description": bucket.get("description"),
                    "provider": bucket.get("provider", "s3"),
                    "bucket": bucket.get("bucket", ""),
                    "region": bucket.get("region", ""),
                    "max_file_size_mb": bucket.get("max_file_size_mb", 100),
                    "allowed_mime_types": bucket.get("allowed_mime_types", []),
                    "cdn_enabled": bucket.get("cdn_enabled", False),
                    "tags": bucket.get("tags", []),
                    "source": "storage.yaml",
                },
            )
            nodes.append(node)

    if "processing_pipelines" in data:
        for pipe in data["processing_pipelines"]:
            node = ProjectionNode(
                id=pipe.get("id", ""),
                kind=NodeKind.MEDIA_PROCESSING,
                params={
                    "id": pipe.get("id"),
                    "description": pipe.get("description"),
                    "media_type": pipe.get("media_type", "image"),
                    "operations": pipe.get("operations", []),
                    "output_format": pipe.get("output_format", ""),
                    "quality": pipe.get("quality", "high"),
                    "tags": pipe.get("tags", []),
                    "source": "storage.yaml",
                },
            )
            nodes.append(node)

    return nodes


# --- CP16: Monitoring (metrics/alerts từ observability.yaml đã load rồi,
#    nhưng CP16 cần dashboard riêng) ---

def _load_monitoring(path: Path) -> list[ProjectionNode]:
    """Load monitoring.yaml vào ProjectionNodes (CP16 — Monitoring).

    Args:
        path: Đường dẫn đến monitoring.yaml

    Returns:
        Danh sách ProjectionNodes cho metric, alert, dashboard
    """
    data, _ = load_yaml(path)
    nodes = []

    if "metrics" in data:
        for metric in data["metrics"]:
            node = ProjectionNode(
                id=metric.get("id", ""),
                kind=NodeKind.METRIC,
                params={
                    "id": metric.get("id"),
                    "description": metric.get("description"),
                    "type": metric.get("type", "counter"),
                    "name": metric.get("name", ""),
                    "unit": metric.get("unit", ""),
                    "labels": metric.get("labels", []),
                    "config": metric.get("config", {}),
                    "tags": metric.get("tags", []),
                    "source": "monitoring.yaml",
                },
            )
            nodes.append(node)

    if "alerts" in data:
        for alert in data["alerts"]:
            node = ProjectionNode(
                id=alert.get("id", ""),
                kind=NodeKind.ALERT,
                params={
                    "id": alert.get("id"),
                    "description": alert.get("description"),
                    "name": alert.get("name", ""),
                    "condition": alert.get("condition", {}),
                    "severity": alert.get("severity", "warning"),
                    "channels": alert.get("channels", []),
                    "cooldown": alert.get("cooldown", ""),
                    "config": alert.get("config", {}),
                    "tags": alert.get("tags", []),
                    "source": "monitoring.yaml",
                },
            )
            nodes.append(node)

    if "dashboards" in data:
        for dash in data["dashboards"]:
            node = ProjectionNode(
                id=dash.get("id", ""),
                kind=NodeKind.DASHBOARD,
                params={
                    "id": dash.get("id"),
                    "description": dash.get("description"),
                    "title": dash.get("title", ""),
                    "widgets": dash.get("widgets", []),
                    "refresh_interval": dash.get("refresh_interval", 30),
                    "tags": dash.get("tags", []),
                    "source": "monitoring.yaml",
                },
            )
            nodes.append(node)

    return nodes


# --- CP20: API Client Generator ---

def _load_api_client(path: Path) -> list[ProjectionNode]:
    """Load api_client.yaml vào ProjectionNodes (CP20 — API Client Generator).

    Args:
        path: Đường dẫn đến api_client.yaml

    Returns:
        Danh sách ProjectionNodes cho API client và endpoints
    """
    data, _ = load_yaml(path)
    nodes = []

    if "clients" in data:
        for client in data["clients"]:
            node = ProjectionNode(
                id=client.get("id", ""),
                kind=NodeKind.API_CLIENT,
                params={
                    "id": client.get("id"),
                    "description": client.get("description"),
                    "base_url": client.get("base_url", ""),
                    "protocol": client.get("protocol", "rest"),
                    "auth_type": client.get("auth_type", "bearer"),
                    "timeout_ms": client.get("timeout_ms", 5000),
                    "retry_count": client.get("retry_count", 3),
                    "tags": client.get("tags", []),
                    "source": "api_client.yaml",
                },
            )
            nodes.append(node)

    if "endpoints" in data:
        for ep in data["endpoints"]:
            node = ProjectionNode(
                id=ep.get("id", ""),
                kind=NodeKind.API_CLIENT_ENDPOINT,
                params={
                    "id": ep.get("id"),
                    "description": ep.get("description"),
                    "client_id": ep.get("client_id", ""),
                    "method": ep.get("method", "GET"),
                    "path": ep.get("path", ""),
                    "request_schema": ep.get("request_schema", {}),
                    "response_schema": ep.get("response_schema", {}),
                    "tags": ep.get("tags", []),
                    "source": "api_client.yaml",
                },
            )
            nodes.append(node)

    return nodes


# --- CP23: Testing ---

def _load_testing(path: Path) -> list[ProjectionNode]:
    """Load testing.yaml vào ProjectionNodes (CP23 — Testing).

    Args:
        path: Đường dẫn đến testing.yaml

    Returns:
        Danh sách ProjectionNodes cho test suites
    """
    data, _ = load_yaml(path)
    nodes = []

    if "suites" in data:
        for suite in data["suites"]:
            node = ProjectionNode(
                id=suite.get("id", ""),
                kind=NodeKind.TEST_SUITE,
                params={
                    "id": suite.get("id"),
                    "description": suite.get("description"),
                    "test_type": suite.get("test_type", "unit"),
                    "framework": suite.get("framework", "pytest"),
                    "files": suite.get("files", []),
                    "coverage_threshold": suite.get("coverage_threshold", 80),
                    "parallel": suite.get("parallel", False),
                    "tags": suite.get("tags", []),
                    "source": "testing.yaml",
                },
            )
            nodes.append(node)

    return nodes


# --- CP24: Quality/Security ---

def _load_quality(path: Path) -> list[ProjectionNode]:
    """Load quality.yaml vào ProjectionNodes (CP24 — Quality/Security).

    Args:
        path: Đường dẫn đến quality.yaml

    Returns:
        Danh sách ProjectionNodes cho quality gates
    """
    data, _ = load_yaml(path)
    nodes = []

    if "gates" in data:
        for gate in data["gates"]:
            node = ProjectionNode(
                id=gate.get("id", ""),
                kind=NodeKind.QUALITY_GATE,
                params={
                    "id": gate.get("id"),
                    "description": gate.get("description"),
                    "gate_type": gate.get("gate_type", "code_quality"),
                    "checks": gate.get("checks", []),
                    "fail_threshold": gate.get("fail_threshold", 0),
                    "tags": gate.get("tags", []),
                    "source": "quality.yaml",
                },
            )
            nodes.append(node)

    return nodes


# --- CP25: Performance Testing ---

def _load_performance(path: Path) -> list[ProjectionNode]:
    """Load performance.yaml vào ProjectionNodes (CP25 — Performance Testing).

    Args:
        path: Đường dẫn đến performance.yaml

    Returns:
        Danh sách ProjectionNodes cho performance test và load profile
    """
    data, _ = load_yaml(path)
    nodes = []

    if "scenarios" in data:
        for scenario in data["scenarios"]:
            node = ProjectionNode(
                id=scenario.get("id", ""),
                kind=NodeKind.PERFORMANCE_TEST,
                params={
                    "id": scenario.get("id"),
                    "description": scenario.get("description"),
                    "test_type": scenario.get("test_type", "load"),
                    "target_rps": scenario.get("target_rps", 1000),
                    "duration_seconds": scenario.get("duration_seconds", 300),
                    "endpoints": scenario.get("endpoints", []),
                    "success_criteria": scenario.get("success_criteria", {}),
                    "tags": scenario.get("tags", []),
                    "source": "performance.yaml",
                },
            )
            nodes.append(node)

    if "load_profiles" in data:
        for profile in data["load_profiles"]:
            node = ProjectionNode(
                id=profile.get("id", ""),
                kind=NodeKind.LOAD_PROFILE,
                params={
                    "id": profile.get("id"),
                    "description": profile.get("description"),
                    "ramp_up_seconds": profile.get("ramp_up_seconds", 60),
                    "steady_state_seconds": profile.get("steady_state_seconds", 300),
                    "virtual_users": profile.get("virtual_users", 100),
                    "think_time_ms": profile.get("think_time_ms", 1000),
                    "tags": profile.get("tags", []),
                    "source": "performance.yaml",
                },
            )
            nodes.append(node)

    return nodes


# --- CP26: Documentation Generator ---

def _load_documentation(path: Path) -> list[ProjectionNode]:
    """Load documentation.yaml vào ProjectionNodes (CP26 — Documentation Generator).

    Args:
        path: Đường dẫn đến documentation.yaml

    Returns:
        Danh sách ProjectionNodes cho documentation spec và API doc sections
    """
    data, _ = load_yaml(path)
    nodes = []

    if "specs" in data:
        for spec in data["specs"]:
            node = ProjectionNode(
                id=spec.get("id", ""),
                kind=NodeKind.DOCUMENTATION_SPEC,
                params={
                    "id": spec.get("id"),
                    "description": spec.get("description"),
                    "doc_type": spec.get("doc_type", "api_docs"),
                    "format": spec.get("format", "openapi"),
                    "entities": spec.get("entities", []),
                    "output_path": spec.get("output_path", ""),
                    "tags": spec.get("tags", []),
                    "source": "documentation.yaml",
                },
            )
            nodes.append(node)

    if "sections" in data:
        for section in data["sections"]:
            node = ProjectionNode(
                id=section.get("id", ""),
                kind=NodeKind.API_DOC_SECTION,
                params={
                    "id": section.get("id"),
                    "description": section.get("description"),
                    "section_name": section.get("section_name", ""),
                    "endpoints": section.get("endpoints", []),
                    "examples": section.get("examples", []),
                    "tags": section.get("tags", []),
                    "source": "documentation.yaml",
                },
            )
            nodes.append(node)

    return nodes


# --- CP30: AI-Assisted Development ---

def _load_ai_assisted(path: Path) -> list[ProjectionNode]:
    """Load ai_assisted.yaml vào ProjectionNodes (CP30 — AI-Assisted Development).

    Args:
        path: Đường dẫn đến ai_assisted.yaml

    Returns:
        Danh sách ProjectionNodes cho AI service, prompt template, tool call
    """
    data, _ = load_yaml(path)
    nodes = []

    if "services" in data:
        for svc in data["services"]:
            node = ProjectionNode(
                id=svc.get("id", ""),
                kind=NodeKind.AI_SERVICE,
                params={
                    "id": svc.get("id"),
                    "description": svc.get("description"),
                    "service_type": svc.get("service_type", "llm"),
                    "provider": svc.get("provider", "openai"),
                    "model": svc.get("model", ""),
                    "api_key_ref": svc.get("api_key_ref", ""),
                    "max_tokens": svc.get("max_tokens", 2048),
                    "temperature": svc.get("temperature", 0.7),
                    "tags": svc.get("tags", []),
                    "source": "ai_assisted.yaml",
                },
            )
            nodes.append(node)

    if "prompt_templates" in data:
        for tmpl in data["prompt_templates"]:
            node = ProjectionNode(
                id=tmpl.get("id", ""),
                kind=NodeKind.AI_PROMPT_TEMPLATE,
                params={
                    "id": tmpl.get("id"),
                    "description": tmpl.get("description"),
                    "template": tmpl.get("template", ""),
                    "variables": tmpl.get("variables", []),
                    "system_prompt": tmpl.get("system_prompt", ""),
                    "max_tokens": tmpl.get("max_tokens", 2048),
                    "tags": tmpl.get("tags", []),
                    "source": "ai_assisted.yaml",
                },
            )
            nodes.append(node)

    if "tool_calls" in data:
        for tool in data["tool_calls"]:
            node = ProjectionNode(
                id=tool.get("id", ""),
                kind=NodeKind.AI_TOOL_CALL,
                params={
                    "id": tool.get("id"),
                    "description": tool.get("description"),
                    "tool_name": tool.get("tool_name", ""),
                    "tool_description": tool.get("tool_description", ""),
                    "parameters_schema": tool.get("parameters_schema", {}),
                    "required": tool.get("required", False),
                    "tags": tool.get("tags", []),
                    "source": "ai_assisted.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP54: Kubernetes & Cloud Native Loader
# ============================================================================

def _load_kubernetes(path: Path) -> list[ProjectionNode]:
    """Load kubernetes.yaml vào ProjectionNodes (CP54 — Kubernetes & Cloud Native).

    Args:
        path: Đường dẫn đến kubernetes.yaml

    Returns:
        Danh sách ProjectionNodes cho deployments, services, ingresses, HPAs, helm
    """
    data, _ = load_yaml(path)
    nodes: list[ProjectionNode] = []

    # Deployments
    if "deployments" in data:
        for dep in data["deployments"]:
            nodes.append(ProjectionNode(
                id=dep.get("id", ""),
                kind=NodeKind.K8S_DEPLOYMENT,
                params={
                    "id": dep.get("id"),
                    "name": dep.get("name", dep.get("id", "")),
                    "replicas": dep.get("replicas", 1),
                    "image": dep.get("image", ""),
                    "ports": dep.get("ports", []),
                    "resources": dep.get("resources", {}),
                    "strategy": dep.get("strategy", "RollingUpdate"),
                    "labels": dep.get("labels", {}),
                    "env": dep.get("env", []),
                    "volume_mounts": dep.get("volume_mounts", []),
                    "tags": dep.get("tags", []),
                    "source": "kubernetes.yaml",
                },
            ))

    # Services
    if "services" in data:
        for svc in data["services"]:
            nodes.append(ProjectionNode(
                id=svc.get("id", ""),
                kind=NodeKind.K8S_SERVICE,
                params={
                    "id": svc.get("id"),
                    "name": svc.get("name", svc.get("id", "")),
                    "type": svc.get("type", "ClusterIP"),
                    "ports": svc.get("ports", []),
                    "selector": svc.get("selector", {}),
                    "tags": svc.get("tags", []),
                    "source": "kubernetes.yaml",
                },
            ))

    # Ingresses
    if "ingresses" in data:
        for ing in data["ingresses"]:
            nodes.append(ProjectionNode(
                id=ing.get("id", ""),
                kind=NodeKind.K8S_INGRESS,
                params={
                    "id": ing.get("id"),
                    "name": ing.get("name", ing.get("id", "")),
                    "host": ing.get("host", ""),
                    "paths": ing.get("paths", []),
                    "tls": ing.get("tls", {}),
                    "annotations": ing.get("annotations", {}),
                    "tags": ing.get("tags", []),
                    "source": "kubernetes.yaml",
                },
            ))

    # HPAs
    if "hpas" in data:
        for hpa in data["hpas"]:
            nodes.append(ProjectionNode(
                id=hpa.get("id", ""),
                kind=NodeKind.K8S_HPA,
                params={
                    "id": hpa.get("id"),
                    "deployment_id": hpa.get("deployment_id", ""),
                    "min_replicas": hpa.get("min_replicas", 1),
                    "max_replicas": hpa.get("max_replicas", 10),
                    "target_cpu": hpa.get("target_cpu", 70),
                    "target_memory": hpa.get("target_memory", 80),
                    "tags": hpa.get("tags", []),
                    "source": "kubernetes.yaml",
                },
            ))

    # Helm charts
    if "helm_charts" in data:
        for chart in data["helm_charts"]:
            nodes.append(ProjectionNode(
                id=chart.get("id", ""),
                kind=NodeKind.HELM_CHART,
                params={
                    "id": chart.get("id"),
                    "name": chart.get("name", chart.get("id", "")),
                    "version": chart.get("version", "1.0.0"),
                    "app_version": chart.get("app_version", "1.0.0"),
                    "values": chart.get("values", {}),
                    "tags": chart.get("tags", []),
                    "source": "kubernetes.yaml",
                },
            ))

    return nodes


# ============================================================================
# CP55: CI/CD Pipeline Loader
# ============================================================================

def _load_cicd(path: Path) -> list[ProjectionNode]:
    """Load cicd.yaml vào ProjectionNodes (CP55 — CI/CD Pipeline Generator).

    Args:
        path: Đường dẫn đến cicd.yaml

    Returns:
        Danh sách ProjectionNodes cho pipeline, stage, và job
    """
    data, _ = load_yaml(path)
    nodes = []

    # Load pipeline configurations
    if "pipelines" in data:
        for pipeline in data["pipelines"]:
            node = ProjectionNode(
                id=pipeline.get("id", ""),
                kind=NodeKind.CI_PIPELINE,
                params={
                    "id": pipeline.get("id"),
                    "name": pipeline.get("name", pipeline.get("id", "")),
                    "description": pipeline.get("description", ""),
                    "platform": pipeline.get("platform", "github_actions"),
                    "triggers": pipeline.get("triggers", ["push"]),
                    "branches": pipeline.get("branches", ["main"]),
                    "env_vars": pipeline.get("env_vars", {}),
                    "tags": pipeline.get("tags", []),
                    "source": "cicd.yaml",
                },
            )
            nodes.append(node)

    # Load pipeline stages
    if "stages" in data:
        for stage in data["stages"]:
            node = ProjectionNode(
                id=stage.get("id", ""),
                kind=NodeKind.CI_STAGE,
                params={
                    "id": stage.get("id"),
                    "name": stage.get("name", stage.get("id", "")),
                    "description": stage.get("description", ""),
                    "steps": stage.get("steps", []),
                    "needs": stage.get("needs", []),
                    "allow_failure": stage.get("allow_failure", False),
                    "tags": stage.get("tags", []),
                    "source": "cicd.yaml",
                },
            )
            nodes.append(node)

    # Load pipeline jobs/steps
    if "jobs" in data:
        for job in data["jobs"]:
            node = ProjectionNode(
                id=job.get("id", ""),
                kind=NodeKind.CI_JOB,
                params={
                    "id": job.get("id"),
                    "name": job.get("name", job.get("id", "")),
                    "description": job.get("description", ""),
                    "image": job.get("image", ""),
                    "commands": job.get("commands", []),
                    "env": job.get("env", {}),
                    "timeout_minutes": job.get("timeout_minutes", 30),
                    "artifacts": job.get("artifacts", []),
                    "tags": job.get("tags", []),
                    "source": "cicd.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP56: Environment & Secret Management Loader
# ============================================================================

def _load_env_secrets(path: Path) -> list[ProjectionNode]:
    """Load env_secrets.yaml vào ProjectionNodes (CP56 — Environment & Secret Management).

    Args:
        path: Đường dẫn đến env_secrets.yaml

    Returns:
        Danh sách ProjectionNodes cho env config, secret config, và vault config
    """
    data, _ = load_yaml(path)
    nodes = []

    if "env_configs" in data:
        for e in data["env_configs"]:
            node = ProjectionNode(
                id=e.get("id", ""),
                kind=NodeKind.ENV_CONFIG,
                params={
                    "id": e.get("id"),
                    "name": e.get("name", e.get("id", "")),
                    "env_name": e.get("env_name", "dev"),
                    "variables": e.get("variables", {}),
                    "required_vars": e.get("required_vars", []),
                    "export_to_dotenv": e.get("export_to_dotenv", True),
                    "tags": e.get("tags", []),
                    "source": "env_secrets.yaml",
                },
            )
            nodes.append(node)

    if "secret_configs" in data:
        for s in data["secret_configs"]:
            node = ProjectionNode(
                id=s.get("id", ""),
                kind=NodeKind.SECRET_CONFIG,
                params={
                    "id": s.get("id"),
                    "name": s.get("name", s.get("id", "")),
                    "secret_type": s.get("secret_type", "local"),
                    "key_path": s.get("key_path", ""),
                    "engine_version": s.get("engine_version", 2),
                    "path": s.get("path", ""),
                    "access_policy": s.get("access_policy", "read-only"),
                    "tags": s.get("tags", []),
                    "source": "env_secrets.yaml",
                },
            )
            nodes.append(node)

    if "vault_configs" in data:
        for v in data["vault_configs"]:
            node = ProjectionNode(
                id=v.get("id", ""),
                kind=NodeKind.VAULT_CONFIG,
                params={
                    "id": v.get("id"),
                    "address": v.get("address", ""),
                    "engine_version": v.get("engine_version", 2),
                    "paths": v.get("paths", []),
                    "auto_auth": v.get("auto_auth", {}),
                    "tags": v.get("tags", []),
                    "source": "env_secrets.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP58: Data Encryption at Rest Loader
# ============================================================================

def _load_encryption(path: Path) -> list[ProjectionNode]:
    """Load encryption.yaml vào ProjectionNodes (CP58 — Data Encryption at Rest).

    Parse encryption configs, encrypted fields, encryption keys,
    và encryption policies từ YAML.

    Args:
        path: Đường dẫn đến encryption.yaml

    Returns:
        Danh sách ProjectionNodes cho encryption nodes
    """
    data, _ = load_yaml(path)
    nodes = []

    # Encryption configs
    if "configs" in data or "encryption_configs" in data:
        configs = data.get("configs", data.get("encryption_configs", []))
        for c in configs:
            node = ProjectionNode(
                id=c.get("id", ""),
                kind=NodeKind.ENCRYPTION_CONFIG,
                params={
                    "id": c.get("id"),
                    "name": c.get("name", c.get("id", "")),
                    "algorithm": c.get("algorithm", "AES256_GCM"),
                    "key_size": c.get("key_size", 256),
                    "mode": c.get("mode", "GCM"),
                    "key_management": c.get("key_management", "local"),
                    "tags": c.get("tags", []),
                    "source": "encryption.yaml",
                },
            )
            nodes.append(node)

    # Encrypted fields
    if "fields" in data or "encrypted_fields" in data:
        fields = data.get("fields", data.get("encrypted_fields", []))
        for f in fields:
            node = ProjectionNode(
                id=f.get("id", ""),
                kind=NodeKind.ENCRYPTED_FIELD,
                params={
                    "id": f.get("id"),
                    "entity_id": f.get("entity_id", ""),
                    "field_name": f.get("field_name", ""),
                    "algorithm": f.get("algorithm", "AES256_GCM"),
                    "key_id": f.get("key_id", ""),
                    "auto_encrypt": f.get("auto_encrypt", True),
                    "auto_decrypt": f.get("auto_decrypt", True),
                    "tags": f.get("tags", []),
                    "source": "encryption.yaml",
                },
            )
            nodes.append(node)

    # Encryption policies
    if "policies" in data or "encryption_policies" in data:
        policies = data.get("policies", data.get("encryption_policies", []))
        for p in policies:
            node = ProjectionNode(
                id=p.get("id", ""),
                kind=NodeKind.ENCRYPTION_POLICY,
                params={
                    "id": p.get("id"),
                    "name": p.get("name", p.get("id", "")),
                    "at_rest": p.get("at_rest", True),
                    "in_transit": p.get("in_transit", True),
                    "algorithm": p.get("algorithm", "AES256_GCM"),
                    "key_rotation_days": p.get("key_rotation_days", 90),
                    "compliance_standards": p.get("compliance_standards", []),
                    "tags": p.get("tags", []),
                    "source": "encryption.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP57: GraphQL Schema Federation Loader
# ============================================================================

def _load_graphql_federation(path: Path) -> list[ProjectionNode]:
    """Load graphql_federation.yaml vào ProjectionNodes (CP57 — GraphQL Schema Federation).

    Parse federation services, federated types, resolvers, và gateway config từ YAML.

    Args:
        path: Đường dẫn đến graphql_federation.yaml

    Returns:
        Danh sách ProjectionNodes cho GraphQL Federation nodes
    """
    data, _ = load_yaml(path)
    nodes = []

    # Federation services
    if "services" in data:
        for service in data["services"]:
            node = ProjectionNode(
                id=service.get("id", ""),
                kind=NodeKind.FEDERATION_SERVICE,
                params={
                    "id": service.get("id"),
                    "name": service.get("name", service.get("id", "")),
                    "url": service.get("url", ""),
                    "schema_path": service.get("schema_path", ""),
                    "health_check": service.get("health_check", "/health"),
                    "port": service.get("port", 4001),
                    "entity_ownerships": service.get("entity_ownerships", []),
                    "tags": service.get("tags", []),
                    "source": "graphql_federation.yaml",
                },
            )
            nodes.append(node)

    # Federated types
    if "types" in data:
        for ft in data["types"]:
            node = ProjectionNode(
                id=ft.get("id", ""),
                kind=NodeKind.FEDERATED_TYPE,
                params={
                    "id": ft.get("id"),
                    "name": ft.get("name", ft.get("id", "")),
                    "fields": ft.get("fields", []),
                    "key_fields": ft.get("key_fields", []),
                    "owning_service": ft.get("owning_service", ""),
                    "extensions": ft.get("extensions", []),
                    "tags": ft.get("tags", []),
                    "source": "graphql_federation.yaml",
                },
            )
            nodes.append(node)

    # Federated resolvers
    if "resolvers" in data:
        for resolver in data["resolvers"]:
            node = ProjectionNode(
                id=resolver.get("id", ""),
                kind=NodeKind.FEDERATED_RESOLVER,
                params={
                    "id": resolver.get("id"),
                    "entity_type": resolver.get("entity_type", ""),
                    "resolve_reference_query": resolver.get("resolve_reference_query", ""),
                    "resolve_reference_service": resolver.get("resolve_reference_service", ""),
                    "tags": resolver.get("tags", []),
                    "source": "graphql_federation.yaml",
                },
            )
            nodes.append(node)

    # Gateway config
    if "gateway_config" in data:
        gw = data["gateway_config"]
        node = ProjectionNode(
            id=gw.get("id", "default_gateway"),
            kind=NodeKind.GATEWAY_CONFIG,
            params={
                "id": gw.get("id", "default_gateway"),
                "services": gw.get("services", []),
                "persisted_queries_enabled": gw.get("persisted_queries_enabled", False),
                "introspection_enabled": gw.get("introspection_enabled", True),
                "cors_origins": gw.get("cors_origins", []),
                "rate_limit_rps": gw.get("rate_limit_rps", 100),
                "tags": gw.get("tags", []),
                "source": "graphql_federation.yaml",
            },
        )
        nodes.append(node)

    return nodes


# ============================================================================
# CP60: Service Discovery & Config Center Loader
# ============================================================================

def _load_service_discovery(path: Path) -> list[ProjectionNode]:
    """Load service_discovery.yaml vào ProjectionNodes (CP60 — Service Discovery & Config Center).

    Args:
        path: Đường dẫn đến service_discovery.yaml

    Returns:
        Danh sách ProjectionNodes cho service instance, registry, config entry, và load balancing
    """
    data, _ = load_yaml(path)
    nodes = []

    # Service instances
    if "instances" in data:
        for inst in data["instances"]:
            node = ProjectionNode(
                id=inst.get("instance_id", inst.get("id", "")),
                kind=NodeKind.SERVICE_INSTANCE,
                params={
                    "id": inst.get("instance_id", inst.get("id", "")),
                    "service_name": inst.get("service_name", inst.get("name", "")),
                    "host": inst.get("host", ""),
                    "port": inst.get("port", 8080),
                    "protocol": inst.get("protocol", "http"),
                    "metadata": inst.get("metadata", {}),
                    "health_check_path": inst.get("health_check_path", "/health"),
                    "tags": inst.get("tags", []),
                    "source": "service_discovery.yaml",
                },
            )
            nodes.append(node)

    # Service registries
    if "registries" in data:
        for reg in data["registries"]:
            node = ProjectionNode(
                id=reg.get("registry_id", reg.get("id", "")),
                kind=NodeKind.SERVICE_REGISTRY,
                params={
                    "id": reg.get("registry_id", reg.get("id", "")),
                    "name": reg.get("name", ""),
                    "provider": reg.get("provider", "consul"),
                    "quorum_size": reg.get("quorum_size", 3),
                    "session_ttl": reg.get("session_ttl", 30),
                    "peer_nodes": reg.get("peer_nodes", []),
                    "metadata": reg.get("metadata", {}),
                    "source": "service_discovery.yaml",
                },
            )
            nodes.append(node)

    # Config entries
    if "configs" in data:
        for cfg in data["configs"]:
            node = ProjectionNode(
                id=cfg.get("entry_id", cfg.get("id", "")),
                kind=NodeKind.CONFIG_ENTRY,
                params={
                    "id": cfg.get("entry_id", cfg.get("id", "")),
                    "key": cfg.get("key", ""),
                    "value": cfg.get("value", ""),
                    "environment": cfg.get("environment", "dev"),
                    "encrypted": cfg.get("encrypted", False),
                    "version": cfg.get("version", 1),
                    "watchers": cfg.get("watchers", []),
                    "metadata": cfg.get("metadata", {}),
                    "source": "service_discovery.yaml",
                },
            )
            nodes.append(node)

    # Load balancing configs
    if "load_balancers" in data:
        for lb in data["load_balancers"]:
            node = ProjectionNode(
                id=lb.get("config_id", lb.get("id", "")),
                kind=NodeKind.LOAD_BALANCING_CONFIG,
                params={
                    "id": lb.get("config_id", lb.get("id", "")),
                    "service_name": lb.get("service_name", ""),
                    "strategy": lb.get("strategy", "round_robin"),
                    "health_check_interval": lb.get("health_check_interval", 15),
                    "max_retries": lb.get("max_retries", 3),
                    "metadata": lb.get("metadata", {}),
                    "source": "service_discovery.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP62: Mobile Backend Loader
# ============================================================================

def _load_mobile_backend(path: Path) -> list[ProjectionNode]:
    """Load mobile_backend.yaml vào ProjectionNodes (CP62 — Mobile Backend).

    Parse push notification configs, deep link routes, mobile auth providers,
    và OTA update configs từ YAML.

    Args:
        path: Đường dẫn đến mobile_backend.yaml

    Returns:
        Danh sách ProjectionNodes cho mobile backend nodes
    """
    data, _ = load_yaml(path)
    nodes = []

    # Push notification configs
    if "push_configs" in data:
        for push in data["push_configs"]:
            node = ProjectionNode(
                id=push.get("id", ""),
                kind=NodeKind.PUSH_NOTIFICATION_CONFIG,
                params={
                    "id": push.get("id"),
                    "description": push.get("description"),
                    "platform": push.get("platform", "both"),
                    "server_key_ref": push.get("server_key_ref", ""),
                    "bundle_id": push.get("bundle_id", ""),
                    "topic": push.get("topic", ""),
                    "sound": push.get("sound", True),
                    "badge": push.get("badge", True),
                    "data_payload": push.get("data_payload", True),
                    "tags": push.get("tags", []),
                    "source": "mobile_backend.yaml",
                },
            )
            nodes.append(node)

    # Deep link routes
    if "deep_links" in data:
        for link in data["deep_links"]:
            node = ProjectionNode(
                id=link.get("id", ""),
                kind=NodeKind.DEEP_LINK_ROUTE,
                params={
                    "id": link.get("id"),
                    "description": link.get("description"),
                    "path_pattern": link.get("path_pattern", ""),
                    "target_screen": link.get("target_screen", ""),
                    "auth_required": link.get("auth_required", False),
                    "params": link.get("params", {}),
                    "fallback_url": link.get("fallback_url", ""),
                    "universal_link_enabled": link.get("universal_link_enabled", False),
                    "tags": link.get("tags", []),
                    "source": "mobile_backend.yaml",
                },
            )
            nodes.append(node)

    # Mobile auth providers
    if "auth_providers" in data:
        for auth in data["auth_providers"]:
            node = ProjectionNode(
                id=auth.get("id", ""),
                kind=NodeKind.MOBILE_AUTH_PROVIDER,
                params={
                    "id": auth.get("id"),
                    "description": auth.get("description"),
                    "type": auth.get("type", "google"),
                    "client_id_ref": auth.get("client_id_ref", ""),
                    "client_secret_ref": auth.get("client_secret_ref", ""),
                    "redirect_uri": auth.get("redirect_uri", ""),
                    "scopes": auth.get("scopes", []),
                    "tags": auth.get("tags", []),
                    "source": "mobile_backend.yaml",
                },
            )
            nodes.append(node)

    # OTA update configs
    if "ota_configs" in data:
        for ota in data["ota_configs"]:
            node = ProjectionNode(
                id=ota.get("id", ""),
                kind=NodeKind.OTA_UPDATE_CONFIG,
                params={
                    "id": ota.get("id"),
                    "description": ota.get("description"),
                    "platform": ota.get("platform", "both"),
                    "forced_update": ota.get("forced_update", False),
                    "minimum_version": ota.get("minimum_version", ""),
                    "release_notes_url": ota.get("release_notes_url", ""),
                    "download_url": ota.get("download_url", ""),
                    "rollout_percentage": ota.get("rollout_percentage", 100),
                    "tags": ota.get("tags", []),
                    "source": "mobile_backend.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP59: Tenant Billing & Invoicing Loader
# ============================================================================

def _load_tenant_billing(path: Path) -> list[ProjectionNode]:
    """Load tenant_billing.yaml vào ProjectionNodes (CP59 — Tenant Billing & Invoicing).

    Parse billing plans, billing cycles, usage meters, và invoice configs từ YAML.

    Args:
        path: Đường dẫn đến tenant_billing.yaml

    Returns:
        Danh sách ProjectionNodes cho tenant billing nodes
    """
    data, _ = load_yaml(path)
    nodes = []

    # Billing plans
    if "billing_plans" in data:
        for plan in data["billing_plans"]:
            node = ProjectionNode(
                id=plan.get("id", ""),
                kind=NodeKind.BILLING_PLAN,
                params={
                    "id": plan.get("id"),
                    "description": plan.get("description"),
                    "name": plan.get("name"),
                    "tier": plan.get("tier", "free"),
                    "monthly_price": plan.get("monthly_price", 0),
                    "annual_price": plan.get("annual_price", 0),
                    "features": plan.get("features", []),
                    "usage_limits": plan.get("usage_limits", {}),
                    "tags": plan.get("tags", []),
                    "source": "tenant_billing.yaml",
                },
            )
            nodes.append(node)

    # Billing cycles
    if "billing_cycles" in data:
        for cycle in data["billing_cycles"]:
            node = ProjectionNode(
                id=cycle.get("id", ""),
                kind=NodeKind.BILLING_CYCLE,
                params={
                    "id": cycle.get("id"),
                    "description": cycle.get("description"),
                    "type": cycle.get("type", "monthly"),
                    "start_date": cycle.get("start_date"),
                    "end_date": cycle.get("end_date"),
                    "auto_renew": cycle.get("auto_renew", True),
                    "metadata": cycle.get("metadata", {}),
                    "tags": cycle.get("tags", []),
                    "source": "tenant_billing.yaml",
                },
            )
            nodes.append(node)

    # Usage meters
    if "usage_meters" in data:
        for meter in data["usage_meters"]:
            node = ProjectionNode(
                id=meter.get("id", ""),
                kind=NodeKind.USAGE_METER,
                params={
                    "id": meter.get("id"),
                    "description": meter.get("description"),
                    "metric_name": meter.get("metric_name", "api_calls"),
                    "unit_price": meter.get("unit_price", 0),
                    "billing_period": meter.get("billing_period", "monthly"),
                    "threshold_alerts": meter.get("threshold_alerts", []),
                    "metadata": meter.get("metadata", {}),
                    "tags": meter.get("tags", []),
                    "source": "tenant_billing.yaml",
                },
            )
            nodes.append(node)

    # Invoice configs
    if "invoice_configs" in data:
        for invoice in data["invoice_configs"]:
            node = ProjectionNode(
                id=invoice.get("id", ""),
                kind=NodeKind.INVOICE_CONFIG,
                params={
                    "id": invoice.get("id"),
                    "description": invoice.get("description"),
                    "tenant_id": invoice.get("tenant_id", ""),
                    "plan_id": invoice.get("plan_id", ""),
                    "amount": invoice.get("amount", 0),
                    "currency": invoice.get("currency", "USD"),
                    "status": invoice.get("status", "draft"),
                    "due_date": invoice.get("due_date"),
                    "line_items": invoice.get("line_items", []),
                    "metadata": invoice.get("metadata", {}),
                    "tags": invoice.get("tags", []),
                    "source": "tenant_billing.yaml",
                },
            )
            nodes.append(node)

    return nodes


# ============================================================================
# CP63: Recommendation Engine Loader
# ============================================================================

def _load_recommendation(path: Path) -> list[ProjectionNode]:
    """Load recommendation.yaml vào ProjectionNodes (CP63 — Search & Recommendation Engine).

    Parse recommendation configs, item embeddings, và user preferences từ YAML.

    Args:
        path: Đường dẫn đến recommendation.yaml

    Returns:
        Danh sách ProjectionNodes cho recommendation nodes
    """
    data, _ = load_yaml(path)
    nodes = []

    # Recommendation configs
    if "configs" in data or "recommendation_configs" in data:
        configs = data.get("configs", data.get("recommendation_configs", []))
        for config in configs:
            nodes.append(ProjectionNode(
                id=config.get("id", ""),
                kind=NodeKind.RECOMMENDATION_CONFIG,
                params={
                    "id": config.get("id"),
                    "name": config.get("name", config.get("id", "")),
                    "description": config.get("description"),
                    "algorithm": config.get("algorithm", "hybrid"),
                    "item_entity": config.get("item_entity", "Product"),
                    "user_entity": config.get("user_entity", "User"),
                    "rating_field": config.get("rating_field", "rating"),
                    "top_k": config.get("top_k", 10),
                    "min_interactions": config.get("min_interactions", 5),
                    "ttl_seconds": config.get("ttl_seconds", 3600),
                    "cache_enabled": config.get("cache_enabled", True),
                    "metadata": config.get("metadata", {}),
                    "tags": config.get("tags", []),
                    "source": "recommendation.yaml",
                },
            ))

    # Item embeddings
    if "embeddings" in data or "item_embeddings" in data:
        embeddings = data.get("embeddings", data.get("item_embeddings", []))
        for embedding in embeddings:
            nodes.append(ProjectionNode(
                id=embedding.get("id", ""),
                kind=NodeKind.ITEM_EMBEDDING,
                params={
                    "id": embedding.get("id"),
                    "description": embedding.get("description"),
                    "item_type": embedding.get("item_type", ""),
                    "embedding_fields": embedding.get("embedding_fields", []),
                    "similarity_metric": embedding.get("similarity_metric", "cosine"),
                    "dimension": embedding.get("dimension", 128),
                    "auto_train": embedding.get("auto_train", True),
                    "metadata": embedding.get("metadata", {}),
                    "tags": embedding.get("tags", []),
                    "source": "recommendation.yaml",
                },
            ))

    # User preferences
    if "preferences" in data or "user_preferences" in data:
        preferences = data.get("preferences", data.get("user_preferences", []))
        for preference in preferences:
            nodes.append(ProjectionNode(
                id=preference.get("id", ""),
                kind=NodeKind.USER_PREFERENCE,
                params={
                    "id": preference.get("id"),
                    "description": preference.get("description"),
                    "user_entity": preference.get("user_entity", "User"),
                    "entity_type": preference.get("entity_type", "user"),
                    "weight": preference.get("weight", 1.0),
                    "history_window_days": preference.get("history_window_days", 30),
                    "exclude_viewed": preference.get("exclude_viewed", True),
                    "boost_categories": preference.get("boost_categories", []),
                    "metadata": preference.get("metadata", {}),
                    "tags": preference.get("tags", []),
                    "source": "recommendation.yaml",
                },
            ))

    return nodes


# ============================================================================
# CP28: Multi-Region & Geo-Replication Loader
# ============================================================================

def _load_multi_region(path: Path) -> list[ProjectionNode]:
    """Load multi_region.yaml vào ProjectionNodes (CP28 — Multi-Region & Geo-Replication).

    Args:
        path: Đường dẫn đến multi_region.yaml

    Returns:
        Danh sách ProjectionNodes cho regions, replication, geo-routing, failover,
        data residency rules, và health checks
    """
    data, _ = load_yaml(path)
    nodes: list[ProjectionNode] = []

    # Region configurations
    if "regions" in data:
        for region in data["regions"]:
            nodes.append(ProjectionNode(
                id=region.get("id", ""),
                kind=NodeKind.REGION_CONFIG,
                params={
                    "id": region.get("id"),
                    "name": region.get("name", region.get("id", "")),
                    "description": region.get("description", ""),
                    "cloud_provider": region.get("cloud_provider", "aws"),
                    "availability_zones": region.get("availability_zones", []),
                    "primary": region.get("primary", False),
                    "endpoint_url": region.get("endpoint_url", ""),
                    "replicas": region.get("replicas", 2),
                    "tags": region.get("tags", []),
                    "source": "multi_region.yaml",
                },
            ))

    # Replication policies
    if "replication_policies" in data:
        for policy in data["replication_policies"]:
            nodes.append(ProjectionNode(
                id=policy.get("id", ""),
                kind=NodeKind.REPLICATION_POLICY,
                params={
                    "id": policy.get("id"),
                    "name": policy.get("name", policy.get("id", "")),
                    "description": policy.get("description", ""),
                    "mode": policy.get("mode", "async"),
                    "source_region": policy.get("source_region", ""),
                    "target_regions": policy.get("target_regions", []),
                    "lag_threshold_ms": policy.get("lag_threshold_ms", 5000),
                    "conflict_resolution": policy.get("conflict_resolution", "source_wins"),
                    "tables": policy.get("tables", []),
                    "tags": policy.get("tags", []),
                    "source": "multi_region.yaml",
                },
            ))

    # Geo-routing rules
    if "geo_routing_rules" in data:
        for rule in data["geo_routing_rules"]:
            nodes.append(ProjectionNode(
                id=rule.get("id", ""),
                kind=NodeKind.GEO_ROUTING_RULE,
                params={
                    "id": rule.get("id"),
                    "name": rule.get("name", rule.get("id", "")),
                    "description": rule.get("description", ""),
                    "strategy": rule.get("strategy", "latency"),
                    "regions": rule.get("regions", []),
                    "fallback_region": rule.get("fallback_region", ""),
                    "health_check_path": rule.get("health_check_path", "/health"),
                    "tags": rule.get("tags", []),
                    "source": "multi_region.yaml",
                },
            ))

    # Failover policies
    if "failover_policies" in data:
        for policy in data["failover_policies"]:
            nodes.append(ProjectionNode(
                id=policy.get("id", ""),
                kind=NodeKind.FAILOVER_POLICY,
                params={
                    "id": policy.get("id"),
                    "name": policy.get("name", policy.get("id", "")),
                    "description": policy.get("description", ""),
                    "trigger": policy.get("trigger", "health_check"),
                    "regions": policy.get("regions", []),
                    "rto_minutes": policy.get("rto_minutes", 15),
                    "rpo_minutes": policy.get("rpo_minutes", 5),
                    "dns_ttl_seconds": policy.get("dns_ttl_seconds", 60),
                    "auto_failover_enabled": policy.get("auto_failover_enabled", True),
                    "tags": policy.get("tags", []),
                    "source": "multi_region.yaml",
                },
            ))

    # Data residency rules
    if "data_residency_rules" in data:
        for rule in data["data_residency_rules"]:
            nodes.append(ProjectionNode(
                id=rule.get("id", ""),
                kind=NodeKind.DATA_RESIDENCY_RULE,
                params={
                    "id": rule.get("id"),
                    "name": rule.get("name", rule.get("id", "")),
                    "description": rule.get("description", ""),
                    "region": rule.get("region", ""),
                    "allowed_countries": rule.get("allowed_countries", []),
                    "tenant_ids": rule.get("tenant_ids", []),
                    "data_categories": rule.get("data_categories", []),
                    "enforcement": rule.get("enforcement", "strict"),
                    "tags": rule.get("tags", []),
                    "source": "multi_region.yaml",
                },
            ))

    # Health checks
    if "health_checks" in data:
        for check in data["health_checks"]:
            nodes.append(ProjectionNode(
                id=check.get("id", ""),
                kind=NodeKind.REGION_HEALTH_CHECK,
                params={
                    "id": check.get("id"),
                    "description": check.get("description", ""),
                    "region": check.get("region", ""),
                    "endpoint_url": check.get("endpoint_url", ""),
                    "interval_seconds": check.get("interval_seconds", 30),
                    "timeout_seconds": check.get("timeout_seconds", 5),
                    "unhealthy_threshold": check.get("unhealthy_threshold", 3),
                    "healthy_threshold": check.get("healthy_threshold", 2),
                    "check_type": check.get("check_type", "http"),
                    "tags": check.get("tags", []),
                    "source": "multi_region.yaml",
                },
            ))

    return nodes


# ============================================================================
# CP64: API Contract Testing Loader
# ============================================================================

def _load_contract_testing(path: Path) -> list[ProjectionNode]:
    """Load contract_testing.yaml vào ProjectionNodes (CP64 — API Contract Testing).

    Args:
        path: Đường dẫn đến contract_testing.yaml

    Returns:
        Danh sách ProjectionNodes cho consumer specs, interactions, provider verifiers
    """
    data, _ = load_yaml(path)
    nodes: list[ProjectionNode] = []

    # Consumer specs
    if "consumer_specs" in data:
        for spec in data["consumer_specs"]:
            nodes.append(ProjectionNode(
                id=spec.get("id", ""),
                kind=NodeKind.CONSUMER_SPEC,
                params={
                    "id": spec.get("id"),
                    "consumer_name": spec.get("consumer_name", ""),
                    "provider_name": spec.get("provider_name", ""),
                    "pact_spec_version": spec.get("pact_spec_version", "2.0.0"),
                    "interactions": spec.get("interactions", []),
                    "tags": spec.get("tags", []),
                    "source": "contract_testing.yaml",
                },
            ))

    # Provider verifiers
    if "provider_verifiers" in data:
        for verifier in data["provider_verifiers"]:
            nodes.append(ProjectionNode(
                id=verifier.get("id", ""),
                kind=NodeKind.PROVIDER_VERIFIER,
                params={
                    "id": verifier.get("id"),
                    "provider_name": verifier.get("provider_name", ""),
                    "pact_broker_url": verifier.get("pact_broker_url", ""),
                    "publish_verification_results": verifier.get("publish_verification_results", True),
                    "tags": verifier.get("tags", []),
                    "source": "contract_testing.yaml",
                },
            ))

    # Pact broker config
    if "pact_broker_config" in data:
        broker = data["pact_broker_config"]
        nodes.append(ProjectionNode(
            id=broker.get("id", ""),
            kind=NodeKind.PACT_BROKER_CONFIG,
            params={
                "id": broker.get("id"),
                "url": broker.get("url", ""),
                "project": broker.get("project", ""),
                "tags": broker.get("tags", []),
                "auto_publish": broker.get("auto_publish", False),
                "source": "contract_testing.yaml",
            },
        ))

    return nodes


# ============================================================================
# CP65: Data Backup & Recovery Loader
# ============================================================================

def _load_backup_recovery(path: Path) -> list[ProjectionNode]:
    """Load backup_recovery.yaml vào ProjectionNodes (CP65 — Data Backup & Recovery).

    Args:
        path: Đường dẫn đến backup_recovery.yaml

    Returns:
        Danh sách ProjectionNodes cho backup policies, recovery plans, monitors
    """
    data, _ = load_yaml(path)
    nodes: list[ProjectionNode] = []

    # Backup policies
    if "backup_policies" in data:
        for policy in data["backup_policies"]:
            nodes.append(ProjectionNode(
                id=policy.get("id", ""),
                kind=NodeKind.BACKUP_POLICY,
                params={
                    "id": policy.get("id"),
                    "name": policy.get("name", ""),
                    "backup_type": policy.get("backup_type", "full"),
                    "target": policy.get("target", ""),
                    "storage_backend": policy.get("storage_backend", "local"),
                    "schedule_type": policy.get("schedule_type", "cron"),
                    "schedule_cron": policy.get("schedule_cron", ""),
                    "retention_days": policy.get("retention_days", 30),
                    "compression_enabled": policy.get("compression_enabled", True),
                    "encryption_enabled": policy.get("encryption_enabled", True),
                    "tags": policy.get("tags", []),
                    "source": "backup_recovery.yaml",
                },
            ))

    # Recovery plans
    if "recovery_plans" in data:
        for plan in data["recovery_plans"]:
            nodes.append(ProjectionNode(
                id=plan.get("id", ""),
                kind=NodeKind.RECOVERY_PLAN,
                params={
                    "id": plan.get("id"),
                    "name": plan.get("name", ""),
                    "rto_minutes": plan.get("rto_minutes", 15),
                    "rpo_minutes": plan.get("rpo_minutes", 5),
                    "priority": plan.get("priority", 1),
                    "steps": plan.get("steps", []),
                    "auto_trigger": plan.get("auto_trigger", False),
                    "notification_channels": plan.get("notification_channels", []),
                    "tags": plan.get("tags", []),
                    "source": "backup_recovery.yaml",
                },
            ))

    # Backup monitors
    if "monitors" in data:
        for monitor in data["monitors"]:
            nodes.append(ProjectionNode(
                id=monitor.get("id", ""),
                kind=NodeKind.BACKUP_MONITOR,
                params={
                    "id": monitor.get("id"),
                    "policy_ids": monitor.get("policy_ids", []),
                    "alert_on_failure": monitor.get("alert_on_failure", True),
                    "alert_on_lag_minutes": monitor.get("alert_on_lag_minutes", 60),
                    "slack_webhook": monitor.get("slack_webhook", ""),
                    "email_recipients": monitor.get("email_recipients", []),
                    "tags": monitor.get("tags", []),
                    "source": "backup_recovery.yaml",
                },
            ))

    return nodes


# ============================================================================

def extend(self: ProjectionTree, nodes: list[ProjectionNode]) -> None:
    """Add multiple nodes to a ProjectionTree."""
    for node in nodes:
        self.add_node(node)


# Monkey-patch extend method
ProjectionTree.extend = extend