"""
DSL v1 Validator Module - Enhanced

Full validation pipeline với caching và actionable insights.

Features:
- Validation caching (T02-003)
- Actionable insights (T02-004)
- Constraint-level caching
- Tree-level caching
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Protocol

from .constraints import (
    ConstraintLevel,
    ConstraintResult,
    ConstraintRegistry,
    get_registry,
)
from .dependencies import (
    CycleInfo,
    DependencyAnalysis,
    DependencyGraph,
)
from .metadata import ValidationContext
from .projection import ProjectionNode, ProjectionTree


# ============================================================================
# Validation Caching (T02-003)
# ============================================================================

@dataclass
class ValidationCacheEntry:
    """Entry in validation cache."""
    timestamp: float
    tree_hash: str
    result: ValidationReport
    
    def is_stale(self, max_age_seconds: float = 60.0) -> bool:
        """Check if cache entry is stale."""
        return time.time() - self.timestamp > max_age_seconds


class ValidationCache:
    """
    Cache for validation results.
    
    Caches:
    - Tree-level validation results
    - Node-level constraint results
    """
    
    def __init__(self, max_size: int = 100):
        self._tree_cache: dict[str, ValidationCacheEntry] = {}
        self._node_cache: dict[str, dict[str, list[ConstraintResult]]] = {}
        self._max_size = max_size
    
    def _compute_tree_hash(self, tree: ProjectionTree) -> str:
        """Compute hash of tree for cache key."""
        # Simple hash based on node IDs and kinds
        items = []
        for node_id in sorted(tree.nodes.keys()):
            node = tree.get_node(node_id)
            if node:
                items.append(f"{node_id}:{node.kind.value}")
        content = "|".join(items)
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_tree_result(
        self,
        tree: ProjectionTree,
        max_age: float = 60.0
    ) -> Optional[ValidationReport]:
        """Get cached tree validation result."""
        tree_hash = self._compute_tree_hash(tree)
        entry = self._tree_cache.get(tree_hash)
        
        if entry and not entry.is_stale(max_age):
            return entry.result
        
        return None
    
    def set_tree_result(
        self,
        tree: ProjectionTree,
        result: ValidationReport
    ) -> None:
        """Cache tree validation result."""
        tree_hash = self._compute_tree_hash(tree)
        
        # Evict old entries if cache is full
        if len(self._tree_cache) >= self._max_size:
            # Remove oldest entry
            oldest_key = min(self._tree_cache.keys(), 
                           key=lambda k: self._tree_cache[k].timestamp)
            del self._tree_cache[oldest_key]
        
        self._tree_cache[tree_hash] = ValidationCacheEntry(
            timestamp=time.time(),
            tree_hash=tree_hash,
            result=result,
        )
    
    def get_node_result(
        self,
        node: ProjectionNode,
        constraint_id: str
    ) -> Optional[list[ConstraintResult]]:
        """Get cached node constraint result."""
        cache_key = f"{node.id}:{constraint_id}"
        return self._node_cache.get(cache_key)
    
    def set_node_result(
        self,
        node: ProjectionNode,
        constraint_id: str,
        results: list[ConstraintResult]
    ) -> None:
        """Cache node constraint result."""
        cache_key = f"{node.id}:{constraint_id}"
        self._node_cache[cache_key] = results
    
    def clear(self) -> None:
        """Clear all cached results."""
        self._tree_cache.clear()
        self._node_cache.clear()
    
    def clear_tree(self, tree: ProjectionTree) -> None:
        """Clear cache for specific tree."""
        tree_hash = self._compute_tree_hash(tree)
        self._tree_cache.pop(tree_hash, None)


# ============================================================================
# Validation Status
# ============================================================================

class ValidationStatus(Enum):
    """Overall validation status."""
    VALID = "valid"
    WARNINGS = "warnings"
    ERRORS = "errors"
    FATAL = "fatal"


# ============================================================================
# Validation Report
# ============================================================================

@dataclass
class ValidationReport:
    """
    Complete validation report for a projection tree.
    
    Attributes:
        status: Overall validation status
        constraint_results: All constraint validation results
        dependency_analysis: Dependency graph analysis
        total_errors: Count of error-level issues
        total_warnings: Count of warning-level issues
        total_info: Count of info-level issues
    """
    status: ValidationStatus
    constraint_results: list[ConstraintResult]
    dependency_analysis: Optional[DependencyAnalysis]
    total_errors: int = 0
    total_warnings: int = 0
    total_info: int = 0
    
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return self.status in (ValidationStatus.VALID, ValidationStatus.WARNINGS)
    
    def get_errors(self) -> list[ConstraintResult]:
        """Get only error-level results."""
        return [r for r in self.constraint_results if r.level == ConstraintLevel.ERROR]
    
    def get_warnings(self) -> list[ConstraintResult]:
        """Get only warning-level results."""
        return [r for r in self.constraint_results if r.level == ConstraintLevel.WARNING]
    
    def get_info(self) -> list[ConstraintResult]:
        """Get only info-level results."""
        return [r for r in self.constraint_results if r.level == ConstraintLevel.INFO]
    
    def get_errors_by_node(self) -> dict[str, list[ConstraintResult]]:
        """Group errors by node ID."""
        by_node: dict[str, list[ConstraintResult]] = {}
        for result in self.get_errors():
            node_id = result.node_id or "root"
            if node_id not in by_node:
                by_node[node_id] = []
            by_node[node_id].append(result)
        return by_node
    
    def get_warnings_by_node(self) -> dict[str, list[ConstraintResult]]:
        """Group warnings by node ID."""
        by_node: dict[str, list[ConstraintResult]] = {}
        for result in self.get_warnings():
            node_id = result.node_id or "root"
            if node_id not in by_node:
                by_node[node_id] = []
            by_node[node_id].append(result)
        return by_node
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "total_errors": self.total_errors,
            "total_warnings": self.total_warnings,
            "total_info": self.total_info,
            "is_valid": self.is_valid(),
            "errors": [r.to_dict() for r in self.get_errors()],
            "warnings": [r.to_dict() for r in self.get_warnings()],
            "info": [r.to_dict() for r in self.get_info()],
            "has_cycles": self.dependency_analysis.has_cycles if self.dependency_analysis else None,
            "build_order": self.dependency_analysis.build_order if self.dependency_analysis else None,
        }


# ============================================================================
# Validator
# ============================================================================

@dataclass
class Validator:
    """
    Main validator class for DSL v1 projection trees.
    
    Orchestrates constraint validation và dependency analysis.
    Supports validation caching and actionable insights.
    
    Attributes:
        registry: Constraint registry để use
        fail_on_warnings: Nếu True, warnings cause validation fail
        include_dependency_analysis: Nếu True, run dependency analysis
        cache: Validation cache (optional)
        use_cache: Enable caching
        max_cache_age: Maximum cache age in seconds
    """
    registry: ConstraintRegistry = field(default_factory=get_registry)
    fail_on_warnings: bool = False
    include_dependency_analysis: bool = True
    cache: Optional[ValidationCache] = None
    use_cache: bool = True
    max_cache_age: float = 60.0
    
    def validate(
        self,
        tree: ProjectionTree,
        context: Optional[ValidationContext] = None
    ) -> ValidationReport:
        """
        Validate complete projection tree với caching support.
        
        Args:
            tree: Projection tree để validate
            context: Optional validation context
            
        Returns:
            Complete validation report (từ cache hoặc fresh)
        """
        # Try cache first
        if self.use_cache and self.cache:
            cached = self.cache.get_tree_result(tree, self.max_cache_age)
            if cached:
                return cached
        
        all_results: list[ConstraintResult] = []
        
        # Run constraint validation on each node
        for node_id in tree.nodes:
            node = tree.get_node(node_id)
            if node:
                ctx = ValidationContext(node_id=node_id)
                results = self._validate_node_with_cache(node, tree, ctx)
                all_results.extend(results)
        
        # Run dependency analysis if requested
        dependency_analysis: Optional[DependencyAnalysis] = None
        if self.include_dependency_analysis:
            dependency_analysis = DependencyAnalysis.analyze(tree)
            
            # Add cycle errors if found
            if dependency_analysis.has_cycles:
                for cycle_info in dependency_analysis.cycles:
                    all_results.append(ConstraintResult(
                        constraint_id="DEP001",
                        level=ConstraintLevel.ERROR,
                        message=cycle_info.message,
                        node_id=None,
                    ))
        
        # Calculate totals
        total_errors = sum(1 for r in all_results if r.level == ConstraintLevel.ERROR)
        total_warnings = sum(1 for r in all_results if r.level == ConstraintLevel.WARNING)
        total_info = sum(1 for r in all_results if r.level == ConstraintLevel.INFO)
        
        # Determine overall status
        if total_errors > 0:
            status = ValidationStatus.ERRORS
        elif total_warnings > 0 and self.fail_on_warnings:
            status = ValidationStatus.ERRORS
        elif total_warnings > 0:
            status = ValidationStatus.WARNINGS
        else:
            status = ValidationStatus.VALID
        
        report = ValidationReport(
            status=status,
            constraint_results=all_results,
            dependency_analysis=dependency_analysis,
            total_errors=total_errors,
            total_warnings=total_warnings,
            total_info=total_info,
        )
        
        # Cache result
        if self.use_cache and self.cache:
            self.cache.set_tree_result(tree, report)
        
        return report
    
    def _validate_node_with_cache(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        """Validate single node với per-constraint caching."""
        all_results: list[ConstraintResult] = []
        
        for constraint in self.registry.get_all():
            # Try cache
            if self.use_cache and self.cache:
                cached = self.cache.get_node_result(node, constraint.id)
                if cached is not None:
                    all_results.extend(cached)
                    continue
            
            # Fresh validation
            results = constraint(node, tree, ctx)
            all_results.extend(results)
            
            # Cache result
            if self.use_cache and self.cache:
                self.cache.set_node_result(node, constraint.id, results)
        
        return all_results
    
    def validate_node(
        self,
        node: ProjectionNode,
        tree: ProjectionTree
    ) -> list[ConstraintResult]:
        """
        Validate a single node.
        
        Args:
            node: Node to validate
            tree: Full tree for cross-node validation
            
        Returns:
            List of constraint results
        """
        ctx = ValidationContext(node_id=node.id)
        return self.registry.validate_node(node, tree, ctx)
    
    def quick_check(
        self,
        tree: ProjectionTree
    ) -> bool:
        """
        Quick validation check (True if valid).
        
        Args:
            tree: Projection tree to check
            
        Returns:
            True if no errors
        """
        report = self.validate(tree)
        return report.is_valid()


# ============================================================================
# Convenience Functions
# ============================================================================

def validate_tree(tree: ProjectionTree) -> ValidationReport:
    """
    Validate a projection tree with default settings.
    
    Args:
        tree: Projection tree to validate
        
    Returns:
        Validation report
    """
    validator = Validator()
    return validator.validate(tree)


def quick_validate(tree: ProjectionTree) -> bool:
    """
    Quick validation check.
    
    Args:
        tree: Projection tree to validate
        
    Returns:
        True if valid
    """
    return validate_tree(tree).is_valid()


# ============================================================================
# Validation Utilities
# ============================================================================

@dataclass
class ValidationError:
    """Formatted validation error for display."""
    constraint_id: str
    node_id: Optional[str]
    message: str
    field: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None
    
    def format_short(self) -> str:
        """Format as short error message."""
        prefix = f"[{self.constraint_id}]" if self.constraint_id else ""
        node = f"{self.node_id}: " if self.node_id else ""
        return f"{prefix} {node}{self.message}"
    
    def format_full(self) -> str:
        """Format as full error message with details."""
        lines = [self.format_short()]
        if self.field:
            lines.append(f"  Field: {self.field}")
        if self.expected:
            lines.append(f"  Expected: {self.expected}")
        if self.actual:
            lines.append(f"  Actual: {self.actual}")
        return "\n".join(lines)


def format_report(report: ValidationReport, verbose: bool = False) -> str:
    """
    Format validation report thành human-readable string.
    
    Args:
        report: Validation report để format
        verbose: Include full details
        
    Returns:
        Formatted string
    """
    lines = []
    
    # Header
    status_symbol = "✓" if report.is_valid() else "✗"
    lines.append(f"{status_symbol} Validation Status: {report.status.value.upper()}")
    lines.append(f"  Errors: {report.total_errors}")
    lines.append(f"  Warnings: {report.total_warnings}")
    lines.append(f"  Info: {report.total_info}")
    lines.append("")
    
    # Errors
    if report.get_errors():
        lines.append("ERRORS:")
        for result in report.get_errors():
            err = ValidationError(
                constraint_id=result.constraint_id,
                node_id=result.node_id,
                message=result.message,
                field=result.field,
                expected=result.expected,
                actual=result.actual,
            )
            lines.append(f"  {err.format_full() if verbose else err.format_short()}")
        lines.append("")
    
    # Warnings
    if report.get_warnings():
        lines.append("WARNINGS:")
        for result in report.get_warnings():
            err = ValidationError(
                constraint_id=result.constraint_id,
                node_id=result.node_id,
                message=result.message,
                field=result.field,
                expected=result.expected,
                actual=result.actual,
            )
            lines.append(f"  {err.format_full() if verbose else err.format_short()}")
        lines.append("")
    
    # Dependency info
    if report.dependency_analysis:
        analysis = report.dependency_analysis
        lines.append("DEPENDENCY ANALYSIS:")
        lines.append(f"  Has Cycles: {analysis.has_cycles}")
        lines.append(f"  Build Order Valid: {analysis.is_valid()}")
        lines.append(f"  Total Nodes: {analysis.graph.node_count()}")
        lines.append(f"  Total Dependencies: {analysis.graph.edge_count()}")
        
        if analysis.has_cycles:
            lines.append("  Cycles:")
            for cycle in analysis.cycles:
                lines.append(f"    - {cycle}")
        
        lines.append("")
    
    # Actionable insights (T02-004)
    lines.append("ACTIONABLE INSIGHTS:")
    insights = get_actionable_insights(report)
    for insight in insights:
        lines.append(f"  • {insight}")
    lines.append("")
    
    return "\n".join(lines)


# ============================================================================
# Actionable Insights (T02-004)
# ============================================================================

def get_actionable_insights(report: ValidationReport) -> list[str]:
    """
    Generate actionable insights from validation report.
    
    Analyzes error patterns và suggests fixes.
    
    Args:
        report: Validation report to analyze
        
    Returns:
        List of actionable insights
    """
    insights = []
    
    # Group errors by type
    errors_by_constraint: dict[str, list[ConstraintResult]] = {}
    for result in report.get_errors():
        cid = result.constraint_id
        if cid not in errors_by_constraint:
            errors_by_constraint[cid] = []
        errors_by_constraint[cid].append(result)
    
    # Generate insights based on patterns
    if errors_by_constraint.get("C001"):  # Invalid field types
        insights.append("Review field types in entities - use types from FIELD_TYPE_CATALOG")
    
    if errors_by_constraint.get("C002"):  # Missing primary keys
        insights.append("Add primary_key field to all entities")
    
    if errors_by_constraint.get("C006") or errors_by_constraint.get("C007"):  # Invalid categories
        insights.append("Check command/query categories against COMMAND_CATEGORY_CATALOG and QUERY_CATEGORY_CATALOG")
    
    if errors_by_constraint.get("C010"):  # Invalid HTTP methods
        insights.append("Use valid HTTP methods: GET, POST, PUT, DELETE, PATCH")
    
    if errors_by_constraint.get("C011"):  # HTTP route binding
        insights.append("Bind HTTP routes to existing commands or queries")
    
    if errors_by_constraint.get("C019"):  # Duplicate error codes
        insights.append("Ensure all error codes are unique within the DSL")
    
    if errors_by_constraint.get("C049"):  # Referential integrity
        insights.append("Fix broken references - ensure all referenced nodes exist")
    
    if errors_by_constraint.get("C050") or report.dependency_analysis and report.dependency_analysis.has_cycles:
        insights.append("Break circular dependencies by redesigning node relationships")
    
    if report.total_errors > 10:
        insights.append("High error count - start by fixing foundational issues (entities, primary keys) first")
    
    if report.total_warnings > 5:
        insights.append("Review warnings to improve DSL quality")
    
    # Node-specific insights
    errors_by_node = report.get_errors_by_node()
    for node_id, node_errors in errors_by_node.items():
        if len(node_errors) > 3:
            insights.append(f"Node '{node_id}' has {len(node_errors)} errors - prioritize fixing this node")
    
    # If no insights generated
    if not insights:
        if report.is_valid():
            insights.append("DSL is valid - ready for code generation")
        else:
            insights.append("Review errors above and fix them in order of severity")
    
    return insights


# ============================================================================
# Validation Hooks
# ============================================================================

class ValidationHook(Protocol):
    """Protocol for validation hooks."""
    
    def on_validate_start(self, tree: ProjectionTree) -> None:
        """Called before validation starts."""
        ...
    
    def on_validate_end(self, report: ValidationReport) -> None:
        """Called after validation completes."""
        ...
    
    def on_error(self, result: ConstraintResult) -> None:
        """Called when an error is found."""
        ...
    
    def on_warning(self, result: ConstraintResult) -> None:
        """Called when a warning is found."""
        ...


@dataclass
class LoggingHook:
    """Validation hook that logs to a callback."""
    
    log: callable
    
    def on_validate_start(self, tree: ProjectionTree) -> None:
        self.log(f"Starting validation of tree with {tree.node_count()} nodes")
    
    def on_validate_end(self, report: ValidationReport) -> None:
        self.log(f"Validation complete: {report.status.value}")
    
    def on_error(self, result: ConstraintResult) -> None:
        self.log(f"ERROR [{result.constraint_id}]: {result.message}")
    
    def on_warning(self, result: ConstraintResult) -> None:
        self.log(f"WARN [{result.constraint_id}]: {result.message}")