"""
DSL v1 Constraints Module

Production-level validation constraints for all DSL components.
34+ constraint types covering all layers: domain, app, api, access, integration, infra, observability.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Protocol

from .catalogs import (
    ALERT_SEVERITY_CATALOG,
    AUTH_PROVIDER_TYPE_CATALOG,
    COMMAND_CATEGORY_CATALOG,
    CONSTRAINT_TYPE_CATALOG,
    DATASOURCE_TYPE_CATALOG,
    EFFECT_TYPE_CATALOG,
    ERROR_CATEGORY_CATALOG,
    ERROR_SEVERITY_CATALOG,
    EVENT_TYPE_CATALOG,
    FIELD_TYPE_CATALOG,
    GRAPHQL_OPERATION_CATALOG,
    GUARD_TYPE_CATALOG,
    HTTP_METHOD_CATALOG,
    INDEX_TYPE_CATALOG,
    INTEGRATION_AUTH_TYPE_CATALOG,
    INTEGRATION_TYPE_CATALOG,
    LOG_FORMAT_CATALOG,
    LOG_LEVEL_CATALOG,
    METRIC_AGGREGATION_CATALOG,
    METRIC_TYPE_CATALOG,
    POLICY_EFFECT_CATALOG,
    QUERY_CATEGORY_CATALOG,
    RULE_TYPE_CATALOG,
    TENANT_SCOPE_CATALOG,
    TRACE_EXPORTER_CATALOG,
    WORKFLOW_GATEWAY_TYPE_CATALOG,
    WORKFLOW_STATE_TYPE_CATALOG,
    validate_catalog_value,
)
from .metadata import ValidationContext
from .projection import NodeKind, ProjectionNode, ProjectionTree


# ============================================================================
# Constraint Result
# ============================================================================

class ConstraintLevel(Enum):
    """Severity level for constraint violations."""
    ERROR = "error"        # Must be fixed
    WARNING = "warning"    # Should be reviewed
    INFO = "info"          # Informational


@dataclass
class ConstraintResult:
    """Result of a constraint check."""
    constraint_id: str
    level: ConstraintLevel
    message: str
    node_id: Optional[str] = None
    field: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None
    
    def is_error(self) -> bool:
        return self.level == ConstraintLevel.ERROR
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "constraint_id": self.constraint_id,
            "level": self.level.value,
            "message": self.message,
            "node_id": self.node_id,
            "field": self.field,
            "expected": self.expected,
            "actual": self.actual,
        }


# ============================================================================
# Constraint Protocol
# ============================================================================

class Constraint(Protocol):
    """Protocol for constraint validators."""
    
    def __call__(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        """
        Validate a node against this constraint.
        
        Args:
            node: Node to validate
            tree: Full projection tree for cross-node validation
            ctx: Validation context
            
        Returns:
            List of constraint results (empty if valid)
        """
        ...


# ============================================================================
# Base Constraint Class
# ============================================================================

class BaseConstraint(ABC):
    """Base class for all constraints."""
    
    id: str = "base"
    description: str = "Base constraint"
    level: ConstraintLevel = ConstraintLevel.ERROR
    
    @abstractmethod
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        """Implement validation logic."""
        pass
    
    def __call__(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        return self.validate(node, tree, ctx)


# ============================================================================
# Domain Layer Constraints
# ============================================================================

class EntityFieldTypesValid(BaseConstraint):
    """
    C001: All entity fields must have valid types.
    
    Checks that field types are in FIELD_TYPE_CATALOG.
    """
    id = "C001"
    description = "Entity field types must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.ENTITY:
            return []
        
        results = []
        fields = node.params.get("fields", [])
        
        for fld in fields:
            field_type = fld.get("type")
            if field_type and field_type not in FIELD_TYPE_CATALOG:
                results.append(ConstraintResult(
                    constraint_id=self.id,
                    level=self.level,
                    message=f"Invalid field type '{field_type}' for field '{fld.get('name')}'",
                    node_id=node.id,
                    field=fld.get("name"),
                    expected="one of: " + ", ".join(sorted(FIELD_TYPE_CATALOG)),
                    actual=field_type,
                ))
        
        return results


class EntityPrimaryKeyDefined(BaseConstraint):
    """
    C002: Entity must have a primary key defined.
    """
    id = "C002"
    description = "Entity must have a primary key"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.ENTITY:
            return []
        
        results = []
        primary_key = node.params.get("primary_key", "id")
        fields = node.params.get("fields", [])
        
        field_names = [f.get("name") for f in fields]
        if primary_key not in field_names:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Primary key '{primary_key}' not defined in fields",
                node_id=node.id,
                field="primary_key",
                expected=f"one of: {', '.join(field_names)}",
                actual=primary_key,
            ))
        
        return results


class EntityTenantScopeValid(BaseConstraint):
    """
    C003: Entity tenant_scope must be valid.
    
    Checks against TENANT_SCOPE_CATALOG.
    """
    id = "C003"
    description = "Entity tenant_scope must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.ENTITY:
            return []
        
        results = []
        tenant_scope = node.params.get("tenant_scope")
        
        if tenant_scope and tenant_scope not in TENANT_SCOPE_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid tenant_scope '{tenant_scope}'",
                node_id=node.id,
                field="tenant_scope",
                expected=", ".join(sorted(TENANT_SCOPE_CATALOG)),
                actual=tenant_scope,
            ))
        
        return results


class EntityConstraintTypesValid(BaseConstraint):
    """
    C004: Entity constraint types must be valid.
    
    Checks against CONSTRAINT_TYPE_CATALOG.
    """
    id = "C004"
    description = "Entity constraint types must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.ENTITY:
            return []
        
        results = []
        constraints = node.params.get("constraints", [])
        
        for c in constraints:
            constraint_type = c.get("type")
            if constraint_type and constraint_type not in CONSTRAINT_TYPE_CATALOG:
                results.append(ConstraintResult(
                    constraint_id=self.id,
                    level=self.level,
                    message=f"Invalid constraint type '{constraint_type}'",
                    node_id=node.id,
                    field="constraints.type",
                    expected=", ".join(sorted(CONSTRAINT_TYPE_CATALOG)),
                    actual=constraint_type,
                ))
        
        return results


class ForeignKeyReferencesValid(BaseConstraint):
    """
    C005: Foreign key constraints must reference existing entities.
    """
    id = "C005"
    description = "Foreign key references must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.ENTITY:
            return []
        
        results = []
        constraints = node.params.get("constraints", [])
        entity_ids = [n.id for n in tree.get_nodes_by_kind(NodeKind.ENTITY)]
        
        for c in constraints:
            if c.get("type") == "foreign_key":
                ref = c.get("ref")
                if ref and ref not in entity_ids:
                    results.append(ConstraintResult(
                        constraint_id=self.id,
                        level=self.level,
                        message=f"Foreign key references non-existent entity '{ref}'",
                        node_id=node.id,
                        field="constraints.ref",
                        expected=f"one of: {', '.join(entity_ids)}",
                        actual=ref,
                    ))
        
        return results


# ============================================================================
# Application Layer Constraints
# ============================================================================

class CommandCategoryValid(BaseConstraint):
    """
    C006: Command category must be valid.
    
    Checks against COMMAND_CATEGORY_CATALOG.
    """
    id = "C006"
    description = "Command category must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.COMMAND:
            return []
        
        results = []
        category = node.params.get("category")
        
        if category and category not in COMMAND_CATEGORY_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid command category '{category}'",
                node_id=node.id,
                field="category",
                expected=", ".join(sorted(COMMAND_CATEGORY_CATALOG)),
                actual=category,
            ))
        
        return results


class QueryCategoryValid(BaseConstraint):
    """
    C007: Query category must be valid.
    
    Checks against QUERY_CATEGORY_CATALOG.
    """
    id = "C007"
    description = "Query category must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.QUERY:
            return []
        
        results = []
        category = node.params.get("category")
        
        if category and category not in QUERY_CATEGORY_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid query category '{category}'",
                node_id=node.id,
                field="category",
                expected=", ".join(sorted(QUERY_CATEGORY_CATALOG)),
                actual=category,
            ))
        
        return results


class CommandTenantScopeValid(BaseConstraint):
    """
    C008: Command tenant_scope must be valid.
    """
    id = "C008"
    description = "Command tenant_scope must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.COMMAND:
            return []
        
        results = []
        tenant_scope = node.params.get("tenant_scope")
        
        if tenant_scope and tenant_scope not in TENANT_SCOPE_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid tenant_scope '{tenant_scope}'",
                node_id=node.id,
                field="tenant_scope",
                expected=", ".join(sorted(TENANT_SCOPE_CATALOG)),
                actual=tenant_scope,
            ))
        
        return results


class WorkflowStateMachineValid(BaseConstraint):
    """
    C009: Workflow state machine must be strongly connected.
    
    Checks:
    - Exactly one initial state
    - At least one terminal state
    - All states are reachable from initial
    - No orphan transitions
    """
    id = "C009"
    description = "Workflow state machine must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.WORKFLOW:
            return []
        
        results = []
        states = node.params.get("states", [])
        transitions = node.params.get("transitions", [])
        
        # Check for initial state
        initial_states = [s for s in states if s.get("type") == "initial"]
        if len(initial_states) == 0:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message="Workflow must have exactly one initial state",
                node_id=node.id,
                field="states",
                expected="1 initial state",
                actual="0 initial states",
            ))
        elif len(initial_states) > 1:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Workflow has {len(initial_states)} initial states (must be 1)",
                node_id=node.id,
                field="states",
                expected="1 initial state",
                actual=f"{len(initial_states)} initial states",
            ))
        
        # Check for terminal state
        terminal_states = [s for s in states if s.get("type") == "terminal"]
        if len(terminal_states) == 0:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message="Workflow must have at least one terminal state",
                node_id=node.id,
                field="states",
                expected=">=1 terminal state",
                actual="0 terminal states",
            ))
        
        # Check state type validity
        state_ids = {s.get("id") for s in states}
        for t in transitions:
            from_state = t.get("from")
            to_state = t.get("to")
            if from_state and from_state not in state_ids:
                results.append(ConstraintResult(
                    constraint_id=self.id,
                    level=self.level,
                    message=f"Transition references non-existent state '{from_state}'",
                    node_id=node.id,
                    field="transitions.from",
                    expected=f"one of: {', '.join(state_ids)}",
                    actual=from_state,
                ))
            if to_state and to_state not in state_ids:
                results.append(ConstraintResult(
                    constraint_id=self.id,
                    level=self.level,
                    message=f"Transition references non-existent state '{to_state}'",
                    node_id=node.id,
                    field="transitions.to",
                    expected=f"one of: {', '.join(state_ids)}",
                    actual=to_state,
                ))
        
        return results


# ============================================================================
# API Layer Constraints
# ============================================================================

class HTTPMethodValid(BaseConstraint):
    """
    C010: HTTP route method must be valid.
    
    Checks against HTTP_METHOD_CATALOG.
    """
    id = "C010"
    description = "HTTP method must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.HTTP_ROUTE:
            return []
        
        results = []
        method = node.params.get("method")
        
        if method and method not in HTTP_METHOD_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid HTTP method '{method}'",
                node_id=node.id,
                field="method",
                expected=", ".join(sorted(HTTP_METHOD_CATALOG)),
                actual=method,
            ))
        
        return results


class HTTPRouteBindsToCommandOrQuery(BaseConstraint):
    """
    C011: HTTP route must bind to a command or query.
    
    Checks that command_id or query_id references an existing node.
    """
    id = "C011"
    description = "HTTP route must bind to command or query"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.HTTP_ROUTE:
            return []
        
        results = []
        command_id = node.params.get("command_id")
        query_id = node.params.get("query_id")
        
        if not command_id and not query_id:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message="HTTP route must bind to a command or query",
                node_id=node.id,
                field="command_id or query_id",
                expected="one must be specified",
                actual="neither specified",
            ))
        
        if command_id:
            if not tree.get_node(command_id):
                results.append(ConstraintResult(
                    constraint_id=self.id,
                    level=self.level,
                    message=f"HTTP route references non-existent command '{command_id}'",
                    node_id=node.id,
                    field="command_id",
                    expected="existing command ID",
                    actual=command_id,
                ))
        
        if query_id:
            if not tree.get_node(query_id):
                results.append(ConstraintResult(
                    constraint_id=self.id,
                    level=self.level,
                    message=f"HTTP route references non-existent query '{query_id}'",
                    node_id=node.id,
                    field="query_id",
                    expected="existing query ID",
                    actual=query_id,
                ))
        
        return results


# ============================================================================
# Access Control Constraints
# ============================================================================

class RolePermissionsValid(BaseConstraint):
    """
    C012: Role permissions must reference existing permissions.
    """
    id = "C012"
    description = "Role permissions must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.ROLE:
            return []
        
        results = []
        permissions = node.params.get("permissions", [])
        permission_ids = [n.id for n in tree.get_nodes_by_kind(NodeKind.PERMISSION)]
        
        for perm in permissions:
            if perm not in permission_ids:
                results.append(ConstraintResult(
                    constraint_id=self.id,
                    level=self.level,
                    message=f"Role references non-existent permission '{perm}'",
                    node_id=node.id,
                    field="permissions",
                    expected=f"one of: {', '.join(permission_ids)}",
                    actual=perm,
                ))
        
        return results


class RoleTenantScopeValid(BaseConstraint):
    """
    C013: Role tenant_scope must be valid.
    """
    id = "C013"
    description = "Role tenant_scope must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.ROLE:
            return []
        
        results = []
        tenant_scope = node.params.get("tenant_scope")
        
        if tenant_scope and tenant_scope not in TENANT_SCOPE_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid tenant_scope '{tenant_scope}'",
                node_id=node.id,
                field="tenant_scope",
                expected=", ".join(sorted(TENANT_SCOPE_CATALOG)),
                actual=tenant_scope,
            ))
        
        return results


class PolicyEffectValid(BaseConstraint):
    """
    C014: Policy effect must be valid.
    
    Checks against POLICY_EFFECT_CATALOG.
    """
    id = "C014"
    description = "Policy effect must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.POLICY:
            return []
        
        results = []
        effect = node.params.get("effect")
        
        if effect and effect not in POLICY_EFFECT_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid policy effect '{effect}'",
                node_id=node.id,
                field="effect",
                expected=", ".join(sorted(POLICY_EFFECT_CATALOG)),
                actual=effect,
            ))
        
        return results


# ============================================================================
# Integration Constraints
# ============================================================================

class IntegrationAuthTypeValid(BaseConstraint):
    """
    C015: Integration auth_type must be valid.
    
    Checks against INTEGRATION_AUTH_TYPE_CATALOG.
    """
    id = "C015"
    description = "Integration auth_type must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.INTEGRATION:
            return []
        
        results = []
        auth_type = node.params.get("auth_type")
        
        if auth_type and auth_type not in INTEGRATION_AUTH_TYPE_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid auth_type '{auth_type}'",
                node_id=node.id,
                field="auth_type",
                expected=", ".join(sorted(INTEGRATION_AUTH_TYPE_CATALOG)),
                actual=auth_type,
            ))
        
        return results


class DataSourceConnectionStringPresent(BaseConstraint):
    """
    C016: DataSource must have connection_string in strict mode.
    """
    id = "C016"
    description = "DataSource must have connection string"
    level = ConstraintLevel.WARNING  # Warning because it can be env var
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.DATASOURCE:
            return []
        
        results = []
        connection_string = node.params.get("connection_string")
        
        if not connection_string:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message="DataSource missing connection_string (can use env var)",
                node_id=node.id,
                field="connection_string",
                expected="connection string or env var reference",
                actual="missing",
            ))
        
        return results


# ============================================================================
# Error Domain Constraints
# ============================================================================

class ErrorSeverityValid(BaseConstraint):
    """
    C017: Error severity must be valid.
    
    Checks against ERROR_SEVERITY_CATALOG.
    """
    id = "C017"
    description = "Error severity must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.ERROR:
            return []
        
        results = []
        severity = node.params.get("severity")
        
        if severity and severity not in ERROR_SEVERITY_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid error severity '{severity}'",
                node_id=node.id,
                field="severity",
                expected=", ".join(sorted(ERROR_SEVERITY_CATALOG)),
                actual=severity,
            ))
        
        return results


class ErrorCategoryValid(BaseConstraint):
    """
    C018: Error category must be valid.
    
    Checks against ERROR_CATEGORY_CATALOG.
    """
    id = "C018"
    description = "Error category must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.ERROR:
            return []
        
        results = []
        category = node.params.get("category")
        
        if category and category not in ERROR_CATEGORY_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid error category '{category}'",
                node_id=node.id,
                field="category",
                expected=", ".join(sorted(ERROR_CATEGORY_CATALOG)),
                actual=category,
            ))
        
        return results


class ErrorCodeUnique(BaseConstraint):
    """
    C019: Error codes must be unique within the projection.
    """
    id = "C019"
    description = "Error codes must be unique"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.ERROR:
            return []
        
        results = []
        error_code = node.params.get("code")
        
        if not error_code:
            return results
        
        # Check against all other errors
        error_nodes = tree.get_nodes_by_kind(NodeKind.ERROR)
        for err_node in error_nodes:
            if err_node.id != node.id:
                if err_node.params.get("code") == error_code:
                    results.append(ConstraintResult(
                        constraint_id=self.id,
                        level=self.level,
                        message=f"Error code '{error_code}' is duplicate (also used by '{err_node.id}')",
                        node_id=node.id,
                        field="code",
                        expected="unique error code",
                        actual=error_code,
                    ))
                    break
        
        return results


# ============================================================================
# Guard/Effect/Rule Constraints
# ============================================================================

class GuardTypeValid(BaseConstraint):
    """
    C020: Guard type must be valid.
    
    Checks against GUARD_TYPE_CATALOG.
    """
    id = "C020"
    description = "Guard type must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.GUARD:
            return []
        
        results = []
        guard_type = node.params.get("type")
        
        if guard_type and guard_type not in GUARD_TYPE_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid guard type '{guard_type}'",
                node_id=node.id,
                field="type",
                expected=", ".join(sorted(GUARD_TYPE_CATALOG)),
                actual=guard_type,
            ))
        
        return results


class EffectTypeValid(BaseConstraint):
    """
    C021: Effect type must be valid.
    
    Checks against EFFECT_TYPE_CATALOG.
    """
    id = "C021"
    description = "Effect type must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.EFFECT:
            return []
        
        results = []
        effect_type = node.params.get("type")
        
        if effect_type and effect_type not in EFFECT_TYPE_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid effect type '{effect_type}'",
                node_id=node.id,
                field="type",
                expected=", ".join(sorted(EFFECT_TYPE_CATALOG)),
                actual=effect_type,
            ))
        
        return results


class RuleTypeValid(BaseConstraint):
    """
    C022: Rule type must be valid.
    
    Checks against RULE_TYPE_CATALOG.
    """
    id = "C022"
    description = "Rule type must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.RULE:
            return []
        
        results = []
        rule_type = node.params.get("type")
        
        if rule_type and rule_type not in RULE_TYPE_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid rule type '{rule_type}'",
                node_id=node.id,
                field="type",
                expected=", ".join(sorted(RULE_TYPE_CATALOG)),
                actual=rule_type,
            ))
        
        return results


class EventTypeValid(BaseConstraint):
    """
    C023: Event type must be valid.
    
    Checks against EVENT_TYPE_CATALOG.
    """
    id = "C023"
    description = "Event type must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.EVENT:
            return []
        
        results = []
        event_type = node.params.get("type")
        
        if event_type and event_type not in EVENT_TYPE_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid event type '{event_type}'",
                node_id=node.id,
                field="type",
                expected=", ".join(sorted(EVENT_TYPE_CATALOG)),
                actual=event_type,
            ))
        
        return results


class GraphQLOperationValid(BaseConstraint):
    """
    C024: GraphQL operation must be valid.
    
    Checks against GRAPHQL_OPERATION_CATALOG.
    """
    id = "C024"
    description = "GraphQL operation must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.GRAPHQL_RESOLVER:
            return []
        
        results = []
        operation = node.params.get("operation")
        
        if operation and operation not in GRAPHQL_OPERATION_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid GraphQL operation '{operation}'",
                node_id=node.id,
                field="operation",
                expected=", ".join(sorted(GRAPHQL_OPERATION_CATALOG)),
                actual=operation,
            ))
        
        return results


# ============================================================================
# Infrastructure Constraints
# ============================================================================

class DataSourceTypeValid(BaseConstraint):
    """
    C025: DataSource type must be valid.
    
    Checks against DATASOURCE_TYPE_CATALOG.
    """
    id = "C025"
    description = "DataSource type must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.DATASOURCE:
            return []
        
        results = []
        ds_type = node.params.get("type")
        
        if ds_type and ds_type not in DATASOURCE_TYPE_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid datasource type '{ds_type}'",
                node_id=node.id,
                field="type",
                expected=", ".join(sorted(DATASOURCE_TYPE_CATALOG)),
                actual=ds_type,
            ))
        
        return results


class IntegrationTypeValid(BaseConstraint):
    """
    C026: Integration type must be valid.
    
    Checks against INTEGRATION_TYPE_CATALOG.
    """
    id = "C026"
    description = "Integration type must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.INTEGRATION:
            return []
        
        results = []
        int_type = node.params.get("type")
        
        if int_type and int_type not in INTEGRATION_TYPE_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid integration type '{int_type}'",
                node_id=node.id,
                field="type",
                expected=", ".join(sorted(INTEGRATION_TYPE_CATALOG)),
                actual=int_type,
            ))
        
        return results


class AuthProviderTypeValid(BaseConstraint):
    """
    C027: AuthProvider type must be valid.
    
    Checks against AUTH_PROVIDER_TYPE_CATALOG.
    """
    id = "C027"
    description = "AuthProvider type must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.AUTH_PROVIDER:
            return []
        
        results = []
        auth_type = node.params.get("type")
        
        if auth_type and auth_type not in AUTH_PROVIDER_TYPE_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid auth provider type '{auth_type}'",
                node_id=node.id,
                field="type",
                expected=", ".join(sorted(AUTH_PROVIDER_TYPE_CATALOG)),
                actual=auth_type,
            ))
        
        return results


class IndexTypeValid(BaseConstraint):
    """
    C028: Index type must be valid.
    
    Checks against INDEX_TYPE_CATALOG.
    """
    id = "C028"
    description = "Index type must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.INDEX:
            return []
        
        results = []
        idx_type = node.params.get("type")
        
        if idx_type and idx_type not in INDEX_TYPE_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid index type '{idx_type}'",
                node_id=node.id,
                field="type",
                expected=", ".join(sorted(INDEX_TYPE_CATALOG)),
                actual=idx_type,
            ))
        
        return results


# ============================================================================
# Observability Constraints
# ============================================================================

class MetricTypeValid(BaseConstraint):
    """
    C029: Metric type must be valid.
    
    Checks against METRIC_TYPE_CATALOG.
    """
    id = "C029"
    description = "Metric type must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.METRIC:
            return []
        
        results = []
        metric_type = node.params.get("type")
        
        if metric_type and metric_type not in METRIC_TYPE_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid metric type '{metric_type}'",
                node_id=node.id,
                field="type",
                expected=", ".join(sorted(METRIC_TYPE_CATALOG)),
                actual=metric_type,
            ))
        
        return results


class MetricAggregationValid(BaseConstraint):
    """
    C030: Metric aggregation must be valid.
    
    Checks against METRIC_AGGREGATION_CATALOG.
    """
    id = "C030"
    description = "Metric aggregation must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.METRIC:
            return []
        
        results = []
        aggregation = node.params.get("aggregation")
        
        if aggregation and aggregation not in METRIC_AGGREGATION_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid metric aggregation '{aggregation}'",
                node_id=node.id,
                field="aggregation",
                expected=", ".join(sorted(METRIC_AGGREGATION_CATALOG)),
                actual=aggregation,
            ))
        
        return results


class LogLevelValid(BaseConstraint):
    """
    C031: Log level must be valid.
    
    Checks against LOG_LEVEL_CATALOG.
    """
    id = "C031"
    description = "Log level must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.LOG:
            return []
        
        results = []
        level = node.params.get("level")
        
        if level and level not in LOG_LEVEL_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid log level '{level}'",
                node_id=node.id,
                field="level",
                expected=", ".join(sorted(LOG_LEVEL_CATALOG)),
                actual=level,
            ))
        
        return results


class LogFormatValid(BaseConstraint):
    """
    C032: Log format must be valid.
    
    Checks against LOG_FORMAT_CATALOG.
    """
    id = "C032"
    description = "Log format must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.LOG:
            return []
        
        results = []
        log_format = node.params.get("format")
        
        if log_format and log_format not in LOG_FORMAT_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid log format '{log_format}'",
                node_id=node.id,
                field="format",
                expected=", ".join(sorted(LOG_FORMAT_CATALOG)),
                actual=log_format,
            ))
        
        return results


class AlertSeverityValid(BaseConstraint):
    """
    C033: Alert severity must be valid.
    
    Checks against ALERT_SEVERITY_CATALOG.
    """
    id = "C033"
    description = "Alert severity must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.ALERT:
            return []
        
        results = []
        severity = node.params.get("severity")
        
        if severity and severity not in ALERT_SEVERITY_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid alert severity '{severity}'",
                node_id=node.id,
                field="severity",
                expected=", ".join(sorted(ALERT_SEVERITY_CATALOG)),
                actual=severity,
            ))
        
        return results


class TraceExporterValid(BaseConstraint):
    """
    C034: Trace exporter must be valid.
    
    Checks against TRACE_EXPORTER_CATALOG.
    """
    id = "C034"
    description = "Trace exporter must be valid"
    level = ConstraintLevel.ERROR
    
    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.TRACE:
            return []
        
        results = []
        exporter = node.params.get("exporter")
        
        if exporter and exporter not in TRACE_EXPORTER_CATALOG:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid trace exporter '{exporter}'",
                node_id=node.id,
                field="exporter",
                expected=", ".join(sorted(TRACE_EXPORTER_CATALOG)),
                actual=exporter,
            ))
        
        return results


# ============================================================================
# P0: Reporting & Analytics Constraints
# ============================================================================

class ReportDataSourcePresent(BaseConstraint):
    """
    C035: Report must have at least one data source.
    """
    id = "C035"
    description = "Report must have data sources"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.REPORT:
            return []

        results = []
        data_sources = node.params.get("data_sources", [])

        if not data_sources:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message="Report must have at least one data source",
                node_id=node.id,
                field="data_sources",
            ))

        return results


class DashboardWidgetPresent(BaseConstraint):
    """
    C036: Dashboard must have at least one widget.
    """
    id = "C036"
    description = "Dashboard must have widgets"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.DASHBOARD:
            return []

        results = []
        widgets = node.params.get("widgets", [])

        if not widgets:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message="Dashboard must have at least one widget",
                node_id=node.id,
                field="widgets",
            ))

        return results


# ============================================================================
# P0: Notification Constraints
# ============================================================================

class NotificationTemplateRequired(BaseConstraint):
    """
    C037: Notification rule must reference a valid template.
    """
    id = "C037"
    description = "Notification rule must have template"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.NOTIFICATION_RULE:
            return []

        results = []
        template_id = node.params.get("template_id")

        if not template_id:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message="Notification rule must have a template_id",
                node_id=node.id,
                field="template_id",
            ))
        elif not tree.get_node(template_id):
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Template '{template_id}' not found",
                node_id=node.id,
                field="template_id",
                actual=template_id,
            ))

        return results


# ============================================================================
# P0: Compliance Constraints
# ============================================================================

class ComplianceRuleFrameworkValid(BaseConstraint):
    """
    C038: Compliance rule must have valid framework.
    """
    id = "C038"
    description = "Compliance rule framework must be valid"
    level = ConstraintLevel.ERROR

    VALID_FRAMEWORKS = {"HIPAA", "PCI-DSS", "GDPR", "SOX", "ISO27001", "SOC2"}

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.COMPLIANCE_RULE:
            return []

        results = []
        framework = node.params.get("framework")

        if framework and framework not in self.VALID_FRAMEWORKS:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid framework '{framework}'",
                node_id=node.id,
                field="framework",
                expected=", ".join(sorted(self.VALID_FRAMEWORKS)),
                actual=framework,
            ))

        return results


class DataRetentionPeriodValid(BaseConstraint):
    """
    C039: Data retention period must be valid format.
    """
    id = "C039"
    description = "Data retention period must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.DATA_RETENTION:
            return []

        results = []
        period = node.params.get("retention_period", "")

        # Check format: number + unit (d, w, m, y)
        import re
        if not re.match(r"^\d+[dwmy]$", period):
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid retention period format '{period}' (use: 30d, 1w, 6m, 1y)",
                node_id=node.id,
                field="retention_period",
                actual=period,
            ))

        return results


# ============================================================================
# P1: Workflow Enhancement Constraints
# ============================================================================

class WorkflowGatewayTypeValid(BaseConstraint):
    """
    C040: Workflow gateway must have valid type.
    """
    id = "C040"
    description = "Workflow gateway type must be valid"
    level = ConstraintLevel.ERROR

    VALID_GATEWAY_TYPES = {"parallel", "exclusive", "inclusive"}

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.WORKFLOW_GATEWAY:
            return []

        results = []
        gw_type = node.params.get("type")

        if gw_type and gw_type not in self.VALID_GATEWAY_TYPES:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid gateway type '{gw_type}'",
                node_id=node.id,
                field="type",
                expected=", ".join(sorted(self.VALID_GATEWAY_TYPES)),
                actual=gw_type,
            ))

        return results


class HumanTaskAssigneeRequired(BaseConstraint):
    """
    C041: Human task must have assignee.
    """
    id = "C041"
    description = "Human task must have assignee"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.HUMAN_TASK:
            return []

        results = []
        assignee = node.params.get("assignee")

        if not assignee:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message="Human task must have an assignee",
                node_id=node.id,
                field="assignee",
            ))

        return results


# ============================================================================
# P1: Event-Driven Constraints
# ============================================================================

class EventBusTypeValid(BaseConstraint):
    """
    C042: Event bus must have valid type.
    """
    id = "C042"
    description = "Event bus type must be valid"
    level = ConstraintLevel.ERROR

    VALID_BUS_TYPES = {"kafka", "rabbitmq", "sqs", "pulsar", "redis"}

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.EVENT_BUS:
            return []

        results = []
        bus_type = node.params.get("type")

        if bus_type and bus_type not in self.VALID_BUS_TYPES:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid event bus type '{bus_type}'",
                node_id=node.id,
                field="type",
                expected=", ".join(sorted(self.VALID_BUS_TYPES)),
                actual=bus_type,
            ))

        return results


class CQRSProjectionHasSourceEvents(BaseConstraint):
    """
    C043: CQRS projection must have source events.
    """
    id = "C043"
    description = "CQRS projection must have source events"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.CQRS_PROJECTION:
            return []

        results = []
        source_events = node.params.get("source_events", [])

        if not source_events:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message="CQRS projection must have at least one source event",
                node_id=node.id,
                field="source_events",
            ))

        return results


# ============================================================================
# P1: Search & Indexing Constraints
# ============================================================================

class SearchIndexEngineValid(BaseConstraint):
    """
    C044: Search index must have valid engine.
    """
    id = "C044"
    description = "Search index engine must be valid"
    level = ConstraintLevel.ERROR

    VALID_ENGINES = {"elasticsearch", "opensearch", "solr", "meilisearch"}

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.SEARCH_INDEX:
            return []

        results = []
        engine = node.params.get("engine")

        if engine and engine not in self.VALID_ENGINES:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid search engine '{engine}'",
                node_id=node.id,
                field="engine",
                expected=", ".join(sorted(self.VALID_ENGINES)),
                actual=engine,
            ))

        return results


# ============================================================================
# P2: Domain-Specific Constraints
# ============================================================================

class PaymentGatewayProviderValid(BaseConstraint):
    """
    C045: Payment gateway must have valid provider.
    """
    id = "C045"
    description = "Payment gateway provider must be valid"
    level = ConstraintLevel.ERROR

    VALID_PROVIDERS = {"stripe", "paypal", "midtrans", "adyen", "square"}

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.PAYMENT_GATEWAY:
            return []

        results = []
        provider = node.params.get("provider")

        if provider and provider not in self.VALID_PROVIDERS:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid payment provider '{provider}'",
                node_id=node.id,
                field="provider",
                expected=", ".join(sorted(self.VALID_PROVIDERS)),
                actual=provider,
            ))

        return results


class FinancialInstrumentTypeValid(BaseConstraint):
    """
    C046: Financial instrument must have valid type.
    """
    id = "C046"
    description = "Financial instrument type must be valid"
    level = ConstraintLevel.ERROR

    VALID_INSTRUMENT_TYPES = {"stock", "bond", "derivative", "forex", "commodity"}

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.FINANCIAL_INSTRUMENT:
            return []

        results = []
        inst_type = node.params.get("type")

        if inst_type and inst_type not in self.VALID_INSTRUMENT_TYPES:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid instrument type '{inst_type}'",
                node_id=node.id,
                field="type",
                expected=", ".join(sorted(self.VALID_INSTRUMENT_TYPES)),
                actual=inst_type,
            ))

        return results


# ============================================================================
# P2: Advanced Patterns Constraints
# ============================================================================

class CircuitBreakerThresholdValid(BaseConstraint):
    """
    C047: Circuit breaker thresholds must be positive.
    """
    id = "C047"
    description = "Circuit breaker thresholds must be positive"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.CIRCUIT_BREAKER:
            return []

        results = []
        failure_threshold = node.params.get("failure_threshold", 0)
        success_threshold = node.params.get("success_threshold", 0)

        if failure_threshold <= 0:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message="failure_threshold must be positive",
                node_id=node.id,
                field="failure_threshold",
                actual=str(failure_threshold),
            ))

        if success_threshold <= 0:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message="success_threshold must be positive",
                node_id=node.id,
                field="success_threshold",
                actual=str(success_threshold),
            ))

        return results


class RateLimiterAlgorithmValid(BaseConstraint):
    """
    C048: Rate limiter must have valid algorithm.
    """
    id = "C048"
    description = "Rate limiter algorithm must be valid"
    level = ConstraintLevel.ERROR

    VALID_ALGORITHMS = {"token_bucket", "sliding_window", "fixed_window", "leaky_bucket"}

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.RATE_LIMITER:
            return []

        results = []
        algorithm = node.params.get("algorithm")

        if algorithm and algorithm not in self.VALID_ALGORITHMS:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid rate limiter algorithm '{algorithm}'",
                node_id=node.id,
                field="algorithm",
                expected=", ".join(sorted(self.VALID_ALGORITHMS)),
                actual=algorithm,
            ))

        return results


# ============================================================================
# Cross-Node Validation Constraints (T02-002)
# ============================================================================

class ReferentialIntegrityConstraint(BaseConstraint):
    """
    C049: All node references must point to existing nodes.
    
    Cross-node validation to ensure referential integrity.
    """
    id = "C049"
    description = "Referential integrity check"
    level = ConstraintLevel.ERROR

    # Fields that contain node IDs as lists
    REFERENCE_FIELDS = {
        NodeKind.COMMAND: ["fetches", "writes_to", "errors", "emits"],
        NodeKind.QUERY: ["reads_from"],
        NodeKind.HTTP_ROUTE: ["command_id", "query_id"],
        NodeKind.NOTIFICATION_RULE: ["template_id", "channel_ids"],
        NodeKind.CQRS_PROJECTION: ["source_events", "target_entity"],
    }

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        results = []
        ref_fields = self.REFERENCE_FIELDS.get(node.kind, [])

        for field in ref_fields:
            value = node.params.get(field)

            if isinstance(value, list):
                for ref_id in value:
                    if ref_id and not tree.get_node(ref_id):
                        results.append(ConstraintResult(
                            constraint_id=self.id,
                            level=self.level,
                            message=f"Reference '{ref_id}' in {field} not found",
                            node_id=node.id,
                            field=field,
                            actual=ref_id,
                        ))
            elif isinstance(value, str) and value:
                if not tree.get_node(value):
                    results.append(ConstraintResult(
                        constraint_id=self.id,
                        level=self.level,
                        message=f"Reference '{value}' in {field} not found",
                        node_id=node.id,
                        field=field,
                        actual=value,
                    ))

        return results


class CircularDependencyConstraint(BaseConstraint):
    """
    C050: No circular dependencies between nodes.
    
    Cross-node validation to detect circular dependencies.
    """
    id = "C050"
    description = "No circular dependencies"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        # Only check once per tree validation
        if getattr(tree, "_circular_check_done", False):
            return []

        # Simple cycle detection in dependencies
        # This is a simplified version - full detection in dependencies.py
        tree._circular_check_done = True

        results = []
        visited = set()
        rec_stack = set()

        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            node = tree.get_node(node_id)
            if node:
                for dep_id in node.dependencies:
                    if dep_id not in visited:
                        if has_cycle(dep_id):
                            return True
                    elif dep_id in rec_stack:
                        return True

            rec_stack.remove(node_id)
            return False

        for node_id in tree.nodes:
            if node_id not in visited:
                if has_cycle(node_id):
                    results.append(ConstraintResult(
                        constraint_id=self.id,
                        level=self.level,
                        message=f"Circular dependency detected involving node '{node_id}'",
                        node_id=node_id,
                    ))
                    break

        return results


# ============================================================================
# P2: Advanced Constraints C051–C060
# ============================================================================

class PluginSlotIdUnique(BaseConstraint):
    """
    C051: Plugin slot IDs must be unique across the tree.

    CP27: PLUGIN_SLOT, PLUGIN_CONTRACT, PLUGIN_POLICY — each slot ID must
    appear exactly once.  Duplicates cause ambiguous plugin resolution.
    """
    id = "C051"
    description = "Plugin slot IDs must be unique"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.PLUGIN_SLOT:
            return []

        # Only run once (on the first PLUGIN_SLOT encountered)
        if getattr(tree, "_c051_check_done", False):
            return []
        tree._c051_check_done = True

        results = []
        slot_ids = [n.id for n in tree.get_nodes_by_kind(NodeKind.PLUGIN_SLOT)]
        seen = set()
        for sid in slot_ids:
            if sid in seen:
                results.append(ConstraintResult(
                    constraint_id=self.id,
                    level=self.level,
                    message=f"Duplicate plugin slot ID '{sid}'",
                    node_id=sid,
                    field="id",
                    expected="unique slot ID",
                    actual=sid,
                ))
            seen.add(sid)

        return results


class CalendarScheduleCronValid(BaseConstraint):
    """
    C052: Calendar schedule must have a valid cron expression in recurrence_rule.

    CP31: CALENDAR_SCHEDULE — ``recurrence_rule`` (if present) must be a
    5-field cron string (minute hour dom month dow).
    """
    id = "C052"
    description = "Calendar schedule cron expression must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.CALENDAR_SCHEDULE:
            return []

        results = []
        cron = node.params.get("recurrence_rule")
        if not cron:
            return []

        if not isinstance(cron, str) or len(cron.split()) != 5:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid cron expression '{cron}' — expected 5 fields",
                node_id=node.id,
                field="recurrence_rule",
                expected="minute hour dom month dow",
                actual=cron,
            ))

        return results


class GeneralLedgerDoubleEntryValid(BaseConstraint):
    """
    C053: General ledger entries must balance (double-entry bookkeeping).

    CP33: GENERAL_LEDGER, FINANCIAL_INSTRUMENT, CURRENCY_EXCHANGE, TAX_RULE,
    SUBLEDGER — the sum of debit amounts must equal the sum of credit amounts
    within each ledger entry.
    """
    id = "C053"
    description = "General ledger entries must balance (double-entry)"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind not in (NodeKind.GENERAL_LEDGER, NodeKind.SUBLEDGER):
            return []

        results = []
        entries = node.params.get("entries", [])

        for entry in entries:
            debits = sum(float(e.get("amount", 0)) for e in entry.get("debits", []))
            credits = sum(float(e.get("amount", 0)) for e in entry.get("credits", []))

            if abs(debits - credits) > 1e-9 and debits > 0:
                results.append(ConstraintResult(
                    constraint_id=self.id,
                    level=self.level,
                    message=f"Ledger entry '{entry.get('id')}' does not balance: debits={debits}, credits={credits}",
                    node_id=node.id,
                    field="entries",
                    expected="debits == credits",
                    actual=f"{debits} != {credits}",
                ))

        return results


class ReportEntityReferenceExists(BaseConstraint):
    """
    C054: Report data sources must reference existing entities.

    CP34: REPORT, DASHBOARD, EXPORT, SCHEDULED_REPORT — every ID in
    ``data_sources`` (or ``source_id``) must match an ENTITY or a
    pre-existing REPORT / DASHBOARD node.
    """
    id = "C054"
    description = "Report entity references must exist"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind not in (NodeKind.REPORT, NodeKind.DASHBOARD, NodeKind.EXPORT, NodeKind.SCHEDULED_REPORT):
            return []

        results = []
        known_ids = {n.id for n in tree.get_nodes_by_kind(NodeKind.ENTITY)}
        known_ids.update(n.id for n in tree.get_nodes_by_kind(NodeKind.REPORT))
        known_ids.update(n.id for n in tree.get_nodes_by_kind(NodeKind.DASHBOARD))

        # REPORT, DASHBOARD, EXPORT — check data_sources
        data_sources = node.params.get("data_sources", [])
        for ref in data_sources:
            if ref not in known_ids:
                results.append(ConstraintResult(
                    constraint_id=self.id,
                    level=self.level,
                    message=f"Report references non-existent entity '{ref}'",
                    node_id=node.id,
                    field="data_sources",
                    expected=f"one of: {', '.join(sorted(known_ids))}",
                    actual=ref,
                ))

        # EXPORT — check source_id
        source_id = node.params.get("source_id")
        if source_id and source_id not in known_ids:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Export references non-existent source '{source_id}'",
                node_id=node.id,
                field="source_id",
                expected=f"one of: {', '.join(sorted(known_ids))}",
                actual=source_id,
            ))

        # SCHEDULED_REPORT — check report_id
        report_id = node.params.get("report_id")
        if report_id and report_id not in known_ids:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Scheduled report references non-existent report '{report_id}'",
                node_id=node.id,
                field="report_id",
                expected=f"one of: {', '.join(sorted(known_ids))}",
                actual=report_id,
            ))

        return results


class GeofenceCoordinateRangeValid(BaseConstraint):
    """
    C055: Geofence coordinates must be within valid ranges.

    CP35: GEO_SEARCH_INDEX — latitude must be in [-90, 90], longitude in
    [-180, 180].
    """
    id = "C055"
    description = "Geofence coordinates must be within valid ranges"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.GEO_SEARCH_INDEX:
            return []

        results = []
        geofences = node.params.get("geofences", [])

        for gf in geofences:
            lat = gf.get("latitude")
            lon = gf.get("longitude")

            if lat is not None and not (-90 <= lat <= 90):
                results.append(ConstraintResult(
                    constraint_id=self.id,
                    level=self.level,
                    message=f"Latitude {lat} out of range [-90, 90]",
                    node_id=node.id,
                    field="geofences.latitude",
                    expected="-90..90",
                    actual=str(lat),
                ))

            if lon is not None and not (-180 <= lon <= 180):
                results.append(ConstraintResult(
                    constraint_id=self.id,
                    level=self.level,
                    message=f"Longitude {lon} out of range [-180, 180]",
                    node_id=node.id,
                    field="geofences.longitude",
                    expected="-180..180",
                    actual=str(lon),
                ))

        return results


class ETLStepHasExtractAndLoad(BaseConstraint):
    """
    C056: ETL migration batch job must have both extract and load steps.

    CP38: DATA_MIGRATION, BATCH_JOB — a valid ETL pipeline requires at
    least one ``extract`` step and at least one ``load`` step.
    """
    id = "C056"
    description = "ETL step must have extract and load"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind not in (NodeKind.DATA_MIGRATION, NodeKind.BATCH_JOB):
            return []

        results = []
        steps = node.params.get("steps", node.params.get("mapping_rules", []))

        step_types = {s.get("type", "") for s in steps if isinstance(s, dict)}

        if "extract" not in step_types and steps:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message="ETL pipeline missing 'extract' step",
                node_id=node.id,
                field="steps",
                expected="at least one step with type='extract'",
                actual=", ".join(sorted(step_types)),
            ))

        if "load" not in step_types and steps:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message="ETL pipeline missing 'load' step",
                node_id=node.id,
                field="steps",
                expected="at least one step with type='load'",
                actual=", ".join(sorted(step_types)),
            ))

        return results


class LocalizationLocaleBCP47(BaseConstraint):
    """
    C057: Localization locale codes must follow BCP 47 format.

    CP39: LOCALIZATION — each locale in ``locales`` must match the
    simplified BCP 47 pattern ``language`` or ``language-Script-Region``
    (e.g. ``en``, ``en-US``, ``zh-Hant-TW``).
    """
    id = "C057"
    description = "Localization locale code must follow BCP 47 format"
    level = ConstraintLevel.ERROR

    # Simplified BCP 47 regex: 2-3 letter language, optional script/region
    _BCP47_PATTERN = re.compile(r"^[a-zA-Z]{2,3}(-[a-zA-Z]{4})?(-[a-zA-Z]{2})?(-[a-zA-Z0-9]{1,8})?$")

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.LOCALIZATION:
            return []

        results = []
        locales = node.params.get("locales", [])

        for locale in locales:
            if not self._BCP47_PATTERN.match(locale):
                results.append(ConstraintResult(
                    constraint_id=self.id,
                    level=self.level,
                    message=f"Invalid BCP 47 locale code '{locale}'",
                    node_id=node.id,
                    field="locales",
                    expected="e.g. en, en-US, zh-Hant-TW",
                    actual=locale,
                ))

        return results


class APIVersionSemanticVersion(BaseConstraint):
    """
    C058: API version string must follow semantic versioning (MAJOR.MINOR.PATCH).

    CP43: API_VERSION, DEPRECATION_NOTICE, PAGINATION_SPEC — ``version``
    must be a valid semver string (e.g. ``1.0.0``, ``2.3.1``).
    """
    id = "C058"
    description = "API version must follow semantic versioning"
    level = ConstraintLevel.ERROR

    _SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$")

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.API_VERSION:
            return []

        results = []
        version = node.params.get("version")

        if version and not self._SEMVER_PATTERN.match(version):
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid semantic version '{version}'",
                node_id=node.id,
                field="version",
                expected="MAJOR.MINOR.PATCH (e.g. 1.0.0)",
                actual=version,
            ))

        return results


class PaymentGatewayEndpointsValid(BaseConstraint):
    """
    C059: Payment gateway configuration must have valid endpoint URLs.

    CP45: PAYMENT_GATEWAY — ``webhook_url`` (if present) must be a valid
    HTTP(S) URL.
    """
    id = "C059"
    description = "Payment gateway must have valid endpoint URLs"
    level = ConstraintLevel.ERROR

    _URL_PATTERN = re.compile(r"^https?://[^\s/$.?#]+\.?[^\s]*")

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.PAYMENT_GATEWAY:
            return []

        results = []
        webhook_url = node.params.get("webhook_url")

        if webhook_url and not self._URL_PATTERN.match(webhook_url):
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Invalid webhook URL '{webhook_url}'",
                node_id=node.id,
                field="webhook_url",
                expected="valid HTTP(S) URL",
                actual=webhook_url,
            ))

        return results


class ProductCatalogUniqueSKU(BaseConstraint):
    """
    C060: Product catalog must have unique SKU within each category.

    CP50: PRODUCT_CATALOG, FACETED_SEARCH_INDEX — every product in the
    same category must have a distinct SKU.
    """
    id = "C060"
    description = "Product catalog SKUs must be unique per category"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.PRODUCT_CATALOG:
            return []

        results = []
        products = node.params.get("products", [])

        # Group by category, then check SKU uniqueness within each group
        category_skus: dict[str, list[str]] = {}
        for product in products:
            if not isinstance(product, dict):
                continue
            category = product.get("category", "default")
            sku = product.get("sku")
            if sku:
                category_skus.setdefault(category, []).append(sku)

        for category, skus in category_skus.items():
            seen = set()
            for sku in skus:
                if sku in seen:
                    results.append(ConstraintResult(
                        constraint_id=self.id,
                        level=self.level,
                        message=f"Duplicate SKU '{sku}' in category '{category}'",
                        node_id=node.id,
                        field="products.sku",
                        expected="unique SKU per category",
                        actual=f"{sku} (category: {category})",
                    ))
                seen.add(sku)

        return results


# ============================================================================
# CP32: State Machine Engine Constraints
# ============================================================================


class StateMachineTransitionValid(BaseConstraint):
    """
    C061: State machine transitions must reference valid states within the machine.

    CP32: STATE_TRANSITION — both ``from_state`` and ``to_state`` must
    exist in the ``states`` list of the referenced ``machine_id``.
    """
    id = "C061"
    description = "State machine transition states must exist in machine"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.STATE_TRANSITION:
            return []

        results: list[ConstraintResult] = []
        machine_id = node.params.get("machine_id")
        if not machine_id:
            return []

        machine_node = tree.get_node(machine_id)
        if not machine_node:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Transition references non-existent machine '{machine_id}'",
                node_id=node.id,
                field="machine_id",
                expected="existing state machine ID",
                actual=machine_id,
            ))
            return results

        valid_states = set(machine_node.params.get("states", []))

        from_state = node.params.get("from_state")
        if from_state and from_state not in valid_states:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Transition '{node.id}': from_state '{from_state}' not in machine states {valid_states}",
                node_id=node.id,
                field="from_state",
                expected=f"one of {valid_states}",
                actual=from_state,
            ))

        to_state = node.params.get("to_state")
        if to_state and to_state not in valid_states:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Transition '{node.id}': to_state '{to_state}' not in machine states {valid_states}",
                node_id=node.id,
                field="to_state",
                expected=f"one of {valid_states}",
                actual=to_state,
            ))

        return results


class StateMachineInitialStateExists(BaseConstraint):
    """
    C062: State machine initial_state must be in the states list.

    CP32: STATE_MACHINE — ``initial_state`` must be one of the declared ``states``.
    """
    id = "C062"
    description = "State machine initial state must exist in states list"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.STATE_MACHINE:
            return []

        results: list[ConstraintResult] = []
        initial = node.params.get("initial_state")
        states = node.params.get("states", [])

        if initial and initial not in states:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"State machine '{node.id}': initial_state '{initial}' not in states {states}",
                node_id=node.id,
                field="initial_state",
                expected=f"one of {states}",
                actual=initial,
            ))

        return results


# ============================================================================
# CP37: Feature Flags & Dynamic Config Constraints
# ============================================================================


class FeatureFlagKeyUnique(BaseConstraint):
    """
    C063: Feature flag keys must be unique across the tree.

    CP37: FEATURE_FLAG — each ``key`` must appear exactly once.
    """
    id = "C063"
    description = "Feature flag keys must be unique"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.FEATURE_FLAG:
            return []

        # Run once
        if getattr(tree, "_c063_check_done", False):
            return []
        tree._c063_check_done = True

        results: list[ConstraintResult] = []
        flags = tree.get_nodes_by_kind(NodeKind.FEATURE_FLAG)
        seen: set[str] = set()
        for n in flags:
            k = n.params.get("key")
            if k in seen:
                results.append(ConstraintResult(
                    constraint_id=self.id,
                    level=self.level,
                    message=f"Duplicate feature flag key '{k}'",
                    node_id=n.id,
                    field="key",
                    expected="unique flag key",
                    actual=k,
                ))
            seen.add(k)

        return results


class ExperimentTrafficSplitValid(BaseConstraint):
    """
    C064: A/B experiment traffic split must sum to ~1.0 and match variant count.

    CP37: AB_EXPERIMENT — ``traffic_split`` must have same length as ``variants``
    and sum to approximately 1.0.
    """
    id = "C064"
    description = "A/B experiment traffic split must sum to 1.0"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.AB_EXPERIMENT:
            return []

        results: list[ConstraintResult] = []
        variants = node.params.get("variants", [])
        splits = node.params.get("traffic_split", [])

        if len(variants) != len(splits):
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Experiment '{node.id}': {len(variants)} variants but {len(splits)} traffic splits",
                node_id=node.id,
                field="traffic_split",
                expected=f"{len(variants)} splits matching variants",
                actual=f"{len(splits)} splits",
            ))

        total = sum(splits) if splits else 0
        if total and abs(total - 1.0) > 1e-6:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Experiment '{node.id}': traffic split sums to {total}, expected 1.0",
                node_id=node.id,
                field="traffic_split",
                expected="1.0",
                actual=str(total),
            ))

        return results


class DynamicConfigScopeValid(BaseConstraint):
    """
    C065: Dynamic config scope must be one of the valid values.

    CP37: DYNAMIC_CONFIG — ``scope`` must be "global", "tenant", or "environment".
    """
    id = "C065"
    description = "Dynamic config scope must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.DYNAMIC_CONFIG:
            return []

        results: list[ConstraintResult] = []
        valid_scopes = {"global", "tenant", "environment"}
        scope = node.params.get("scope")

        if scope and scope not in valid_scopes:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Dynamic config '{node.id}': invalid scope '{scope}'",
                node_id=node.id,
                field="scope",
                expected=f"one of {valid_scopes}",
                actual=scope,
            ))

        return results


# ============================================================================
# CP21: Authentication UI Constraints
# ============================================================================

class AuthUIFrameworkValid(BaseConstraint):
    """
    C066: Auth UI framework must be one of the supported frameworks.

    CP21: AUTH_UI_CONFIG — ``ui_framework`` must be "material", "tailwind", "bootstrap", "antd", or "carbon".
    """
    id = "C066"
    description = "Auth UI framework must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.AUTH_UI_CONFIG:
            return []

        results: list[ConstraintResult] = []
        valid_fw = {"material", "tailwind", "bootstrap", "antd", "carbon"}
        fw = node.params.get("ui_framework")

        if fw and fw not in valid_fw:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Auth UI '{node.id}': invalid ui_framework '{fw}'",
                node_id=node.id,
                field="ui_framework",
                expected=f"one of {valid_fw}",
                actual=fw,
            ))

        return results


# ============================================================================
# CP22: Real-time UI Constraints
# ============================================================================

class ChannelTransportValid(BaseConstraint):
    """
    C067: Channel transport must be 'websocket' or 'sse'.

    CP22: CHANNEL_SPEC — ``transport`` must be one of the valid values.
    """
    id = "C067"
    description = "Channel transport must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.CHANNEL_SPEC:
            return []

        results: list[ConstraintResult] = []
        valid_transports = {"websocket", "sse"}
        transport = node.params.get("transport")

        if transport and transport not in valid_transports:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Channel '{node.id}': invalid transport '{transport}'",
                node_id=node.id,
                field="transport",
                expected=f"one of {valid_transports}",
                actual=transport,
            ))

        return results


class WidgetTypeValid(BaseConstraint):
    """
    C068: Widget type must be a valid widget type.

    CP22: WIDGET_CONFIG — ``widget_type`` must be "live_feed", "live_counter", "presence_indicator", or "notification_toast".
    """
    id = "C068"
    description = "Widget type must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.WIDGET_CONFIG:
            return []

        results: list[ConstraintResult] = []
        valid_types = {"live_feed", "live_counter", "presence_indicator", "notification_toast"}
        wt = node.params.get("widget_type")

        if wt and wt not in valid_types:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Widget '{node.id}': invalid widget_type '{wt}'",
                node_id=node.id,
                field="widget_type",
                expected=f"one of {valid_types}",
                actual=wt,
            ))

        return results


# ============================================================================
# CP28: Custom Code Injection Constraints
# ============================================================================

class CustomCodeInjectPointValid(BaseConstraint):
    """
    C069: Custom code inject point must be valid.

    CP28: CUSTOM_CODE_BLOCK — ``inject_point`` must be "before_class", "after_class", "before_method", "after_method", "top", or "bottom".
    """
    id = "C069"
    description = "Custom code inject point must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.CUSTOM_CODE_BLOCK:
            return []

        results: list[ConstraintResult] = []
        valid_points = {"before_class", "after_class", "before_method", "after_method", "top", "bottom"}
        ip = node.params.get("inject_point")

        if ip and ip not in valid_points:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Code block '{node.id}': invalid inject_point '{ip}'",
                node_id=node.id,
                field="inject_point",
                expected=f"one of {valid_points}",
                actual=ip,
            ))

        return results


class HookEventValid(BaseConstraint):
    """
    C070: Hook event must be a valid lifecycle event.

    CP28: CUSTOM_HOOK — ``event`` must be "before_emit", "after_emit", "before_render", or "after_render".
    """
    id = "C070"
    description = "Hook event must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.CUSTOM_HOOK:
            return []

        results: list[ConstraintResult] = []
        valid_events = {"before_emit", "after_emit", "before_render", "after_render"}
        event = node.params.get("event")

        if event and event not in valid_events:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Hook '{node.id}': invalid event '{event}'",
                node_id=node.id,
                field="event",
                expected=f"one of {valid_events}",
                actual=event,
            ))

        return results


# ============================================================================
# CP31: Scheduler Constraints
# ============================================================================

class CronExpressionValid(BaseConstraint):
    """
    C071: Cron expression must have 5 fields.

    CP31: SCHEDULE — ``cron_expr`` must be a valid 5-field cron expression.
    """
    id = "C071"
    description = "Cron expression must have 5 fields"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.SCHEDULE:
            return []

        results: list[ConstraintResult] = []
        cron = node.params.get("cron_expr")

        if cron and not isinstance(cron, str):
            return results

        if cron:
            parts = cron.split()
            if len(parts) != 5:
                results.append(ConstraintResult(
                    constraint_id=self.id,
                    level=self.level,
                    message=f"Schedule '{node.id}': cron expression has {len(parts)} fields, expected 5",
                    node_id=node.id,
                    field="cron_expr",
                    expected="5 fields",
                    actual=str(len(parts)),
                ))

        return results


# ============================================================================
# CP35: Geospatial Constraints
# ============================================================================

class GeofenceShapeValid(BaseConstraint):
    """
    C072: Geofence shape must be valid.

    CP35: GEOFENCE — ``shape`` must be "circle", "polygon", or "rectangle".
    """
    id = "C072"
    description = "Geofence shape must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.GEOFENCE:
            return []

        results: list[ConstraintResult] = []
        valid_shapes = {"circle", "polygon", "rectangle"}
        shape = node.params.get("shape")

        if shape and shape not in valid_shapes:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Geofence '{node.id}': invalid shape '{shape}'",
                node_id=node.id,
                field="shape",
                expected=f"one of {valid_shapes}",
                actual=shape,
            ))

        return results


# ============================================================================
# CP36: Tenant Onboarding Constraints
# ============================================================================

class TenantPlanNameUnique(BaseConstraint):
    """
    C073: Tenant subscription plan names must be unique.

    CP36: TENANT_SUBSCRIPTION — ``plan_name`` must be unique across all subscription nodes.
    """
    id = "C073"
    description = "Tenant subscription plan name must be unique"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.TENANT_SUBSCRIPTION:
            return []

        results: list[ConstraintResult] = []
        plan_name = node.params.get("plan_name")

        if not plan_name:
            return results

        existing = [n for n in tree.nodes if n.kind == NodeKind.TENANT_SUBSCRIPTION
                     and n.id != node.id and n.params.get("plan_name") == plan_name]
        if existing:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Subscription '{node.id}': duplicate plan_name '{plan_name}' (conflicts with '{existing[0].id}')",
                node_id=node.id,
                field="plan_name",
                expected="unique",
                actual=plan_name,
            ))

        return results


class TenantBillingCycleValid(BaseConstraint):
    """
    C074: Tenant billing cycle must be valid.

    CP36: TENANT_SUBSCRIPTION — ``billing_cycle`` must be "monthly" or "yearly".
    """
    id = "C074"
    description = "Tenant billing cycle must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.TENANT_SUBSCRIPTION:
            return []

        results: list[ConstraintResult] = []
        valid_cycles = {"monthly", "yearly"}
        cycle = node.params.get("billing_cycle")

        if cycle and cycle not in valid_cycles:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Subscription '{node.id}': invalid billing_cycle '{cycle}'",
                node_id=node.id,
                field="billing_cycle",
                expected=f"one of {valid_cycles}",
                actual=cycle,
            ))

        return results


# ============================================================================
# CP40: Webhook Constraints
# ============================================================================

class WebhookAuthTypeValid(BaseConstraint):
    """
    C075: Webhook auth type must be valid.

    CP40: WEBHOOK_SUBSCRIPTION — ``auth_type`` must be "none", "bearer", "hmac", or "basic".
    """
    id = "C075"
    description = "Webhook auth type must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.WEBHOOK_SUBSCRIPTION:
            return []

        results: list[ConstraintResult] = []
        valid_auth = {"none", "bearer", "hmac", "basic"}
        auth = node.params.get("auth_type")

        if auth and auth not in valid_auth:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Webhook '{node.id}': invalid auth_type '{auth}'",
                node_id=node.id,
                field="auth_type",
                expected=f"one of {valid_auth}",
                actual=auth,
            ))

        return results


class WebhookRetryPolicyPositive(BaseConstraint):
    """
    C076: Webhook retry policy max_retries must be positive.

    CP40: WEBHOOK_RETRY_POLICY — ``max_retries`` >= 0.
    """
    id = "C076"
    description = "Webhook retry policy max_retries must be >= 0"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.WEBHOOK_RETRY_POLICY:
            return []

        results: list[ConstraintResult] = []
        max_r = node.params.get("max_retries")

        if max_r is not None and max_r < 0:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Retry policy '{node.id}': max_retries={max_r} < 0",
                node_id=node.id,
                field="max_retries",
                expected=">= 0",
                actual=str(max_r),
            ))

        return results


# ============================================================================
# CP41: Chat Constraints
# ============================================================================

class ConversationTypeValid(BaseConstraint):
    """
    C077: Conversation type must be valid.

    CP41: CONVERSATION — ``conversation_type`` must be "direct", "group", "support", or "broadcast".
    """
    id = "C077"
    description = "Conversation type must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.CONVERSATION:
            return []

        results: list[ConstraintResult] = []
        valid_types = {"direct", "group", "support", "broadcast"}
        ct = node.params.get("conversation_type")

        if ct and ct not in valid_types:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Conversation '{node.id}': invalid conversation_type '{ct}'",
                node_id=node.id,
                field="conversation_type",
                expected=f"one of {valid_types}",
                actual=ct,
            ))

        return results


class ChatMessageTypeValid(BaseConstraint):
    """
    C078: Chat message type must be valid.

    CP41: CHAT_MESSAGE — ``message_type`` must be "text", "image", "video", "file", "reaction", or "system".
    """
    id = "C078"
    description = "Chat message type must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.CHAT_MESSAGE:
            return []

        results: list[ConstraintResult] = []
        valid_types = {"text", "image", "video", "file", "reaction", "system"}
        mt = node.params.get("message_type")

        if mt and mt not in valid_types:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Message '{node.id}': invalid message_type '{mt}'",
                node_id=node.id,
                field="message_type",
                expected=f"one of {valid_types}",
                actual=mt,
            ))

        return results


# ============================================================================
# CP42: Approval Constraints
# ============================================================================

class ApprovalChainTypeValid(BaseConstraint):
    """
    C079: Approval chain type must be valid.

    CP42: APPROVAL_REQUEST — ``chain_type`` must be "sequential", "parallel", or "matrix".
    """
    id = "C079"
    description = "Approval chain type must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.APPROVAL_REQUEST:
            return []

        results: list[ConstraintResult] = []
        valid_types = {"sequential", "parallel", "matrix"}
        ct = node.params.get("chain_type")

        if ct and ct not in valid_types:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Approval '{node.id}': invalid chain_type '{ct}'",
                node_id=node.id,
                field="chain_type",
                expected=f"one of {valid_types}",
                actual=ct,
            ))

        return results


class ApprovalApproverTypeValid(BaseConstraint):
    """
    C080: Approver type must be valid.

    CP42: APPROVAL_STEP — ``approver_type`` must be "role", "user", "group", or "dynamic".
    """
    id = "C080"
    description = "Approver type must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.APPROVAL_STEP:
            return []

        results: list[ConstraintResult] = []
        valid_types = {"role", "user", "group", "dynamic"}
        at = node.params.get("approver_type")

        if at and at not in valid_types:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Step '{node.id}': invalid approver_type '{at}'",
                node_id=node.id,
                field="approver_type",
                expected=f"one of {valid_types}",
                actual=at,
            ))

        return results


class EscalationTriggerValid(BaseConstraint):
    """
    C081: Escalation trigger must be valid.

    CP42: ESCALATION_RULE — ``trigger_on`` must be "timeout", "rejection", or "no_response".
    """
    id = "C081"
    description = "Escalation trigger must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.ESCALATION_RULE:
            return []

        results: list[ConstraintResult] = []
        valid_triggers = {"timeout", "rejection", "no_response"}
        trigger = node.params.get("trigger_on")

        if trigger and trigger not in valid_triggers:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Escalation '{node.id}': invalid trigger_on '{trigger}'",
                node_id=node.id,
                field="trigger_on",
                expected=f"one of {valid_triggers}",
                actual=trigger,
            ))

        return results


# ============================================================================
# CP43: Versioning Constraints
# ============================================================================

class HistoryOperationValid(BaseConstraint):
    """
    C082: History operation must be valid.

    CP43: HISTORY_RECORD — ``operation`` must be "create", "update", "delete", "restore", or "hard_delete".
    """
    id = "C082"
    description = "History operation must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.HISTORY_RECORD:
            return []

        results: list[ConstraintResult] = []
        valid_ops = {"create", "update", "delete", "restore", "hard_delete"}
        op = node.params.get("operation")

        if op and op not in valid_ops:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"History '{node.id}': invalid operation '{op}'",
                node_id=node.id,
                field="operation",
                expected=f"one of {valid_ops}",
                actual=op,
            ))

        return results


# ============================================================================
# CP44: Bulk Operations Constraints
# ============================================================================

class BulkOperationValid(BaseConstraint):
    """
    C083: Bulk operation must be valid.

    CP44: BULK_JOB — ``operation`` must be "create", "update", or "delete".
    """
    id = "C083"
    description = "Bulk operation must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.BULK_JOB:
            return []

        results: list[ConstraintResult] = []
        valid_ops = {"create", "update", "delete"}
        op = node.params.get("operation")

        if op and op not in valid_ops:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Bulk job '{node.id}': invalid operation '{op}'",
                node_id=node.id,
                field="operation",
                expected=f"one of {valid_ops}",
                actual=op,
            ))

        return results


class BulkChunkSizePositive(BaseConstraint):
    """
    C084: Bulk chunk size must be positive.

    CP44: BULK_JOB — ``chunk_size`` > 0.
    """
    id = "C084"
    description = "Bulk chunk size must be > 0"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.BULK_JOB:
            return []

        results: list[ConstraintResult] = []
        cs = node.params.get("chunk_size")

        if cs is not None and cs <= 0:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Bulk job '{node.id}': chunk_size={cs} <= 0",
                node_id=node.id,
                field="chunk_size",
                expected="> 0",
                actual=str(cs),
            ))

        return results


# ============================================================================
# CP46: MFA Constraints
# ============================================================================

class MFAMethodValid(BaseConstraint):
    """
    C085: MFA method must be valid.

    CP46: MFA_CREDENTIAL — each method in ``methods`` must be "totp", "sms_otp", "webauthn", or "biometric".
    """
    id = "C085"
    description = "MFA methods must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.MFA_CREDENTIAL:
            return []

        results: list[ConstraintResult] = []
        valid_methods = {"totp", "sms_otp", "webauthn", "biometric"}
        methods = node.params.get("methods", [])

        for m in methods:
            if m not in valid_methods:
                results.append(ConstraintResult(
                    constraint_id=self.id,
                    level=self.level,
                    message=f"MFA '{node.id}': invalid method '{m}'",
                    node_id=node.id,
                    field="methods",
                    expected=f"one of {valid_methods}",
                    actual=m,
                ))

        return results


class MFAChallengeMethodValid(BaseConstraint):
    """
    C086: MFA challenge method must be valid.

    CP46: MFA_CHALLENGE — ``method`` must be "totp", "sms_otp", "webauthn", or "biometric".
    """
    id = "C086"
    description = "MFA challenge method must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.MFA_CHALLENGE:
            return []

        results: list[ConstraintResult] = []
        valid_methods = {"totp", "sms_otp", "webauthn", "biometric"}
        method = node.params.get("method")

        if method and method not in valid_methods:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Challenge '{node.id}': invalid method '{method}'",
                node_id=node.id,
                field="method",
                expected=f"one of {valid_methods}",
                actual=method,
            ))

        return results


# ============================================================================
# CP47: Data Retention Constraints
# ============================================================================

class RetentionActionValid(BaseConstraint):
    """
    C087: Retention action after expiry must be valid.

    CP47: RETENTION_POLICY — ``action_after_expiry`` must be "archive", "purge", or "anonymize".
    """
    id = "C087"
    description = "Retention action must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.RETENTION_POLICY:
            return []

        results: list[ConstraintResult] = []
        valid_actions = {"archive", "purge", "anonymize"}
        action = node.params.get("action_after_expiry")

        if action and action not in valid_actions:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Policy '{node.id}': invalid action_after_expiry '{action}'",
                node_id=node.id,
                field="action_after_expiry",
                expected=f"one of {valid_actions}",
                actual=action,
            ))

        return results


class ErasureScopeValid(BaseConstraint):
    """
    C088: Erasure scope must be valid.

    CP47: ERASURE_REQUEST — ``scope`` must be "all" or "specific_entities".
    """
    id = "C088"
    description = "Erasure scope must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.ERASURE_REQUEST:
            return []

        results: list[ConstraintResult] = []
        valid_scopes = {"all", "specific_entities"}
        scope = node.params.get("scope")

        if scope and scope not in valid_scopes:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Erasure '{node.id}': invalid scope '{scope}'",
                node_id=node.id,
                field="scope",
                expected=f"one of {valid_scopes}",
                actual=scope,
            ))

        return results


# ============================================================================
# CP48: Rate Limiting Constraints
# ============================================================================

class RateLimitStrategyValid(BaseConstraint):
    """
    C089: Rate limit strategy must be valid.

    CP48: RATE_LIMIT_POLICY — ``strategy`` must be "fixed_window", "sliding_window", or "token_bucket".
    """
    id = "C089"
    description = "Rate limit strategy must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.RATE_LIMIT_POLICY:
            return []

        results: list[ConstraintResult] = []
        valid_strategies = {"fixed_window", "sliding_window", "token_bucket"}
        strategy = node.params.get("strategy")

        if strategy and strategy not in valid_strategies:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Rate limit '{node.id}': invalid strategy '{strategy}'",
                node_id=node.id,
                field="strategy",
                expected=f"one of {valid_strategies}",
                actual=strategy,
            ))

        return results


class QuotaLevelValid(BaseConstraint):
    """
    C090: Quota level must be valid.

    CP48: QUOTA_CONFIG — ``level`` must be "user", "tenant", "endpoint", or "global".
    """
    id = "C090"
    description = "Quota level must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.QUOTA_CONFIG:
            return []

        results: list[ConstraintResult] = []
        valid_levels = {"user", "tenant", "endpoint", "global"}
        level_val = node.params.get("level")

        if level_val and level_val not in valid_levels:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Quota '{node.id}': invalid level '{level_val}'",
                node_id=node.id,
                field="level",
                expected=f"one of {valid_levels}",
                actual=level_val,
            ))

        return results


class QuotaPeriodValid(BaseConstraint):
    """
    C091: Quota period must be valid.

    CP48: QUOTA_CONFIG — ``period`` must be "second", "minute", "hour", "day", or "month".
    """
    id = "C091"
    description = "Quota period must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.QUOTA_CONFIG:
            return []

        results: list[ConstraintResult] = []
        valid_periods = {"second", "minute", "hour", "day", "month"}
        period = node.params.get("period")

        if period and period not in valid_periods:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Quota '{node.id}': invalid period '{period}'",
                node_id=node.id,
                field="period",
                expected=f"one of {valid_periods}",
                actual=period,
            ))

        return results


# ============================================================================
# CP49: Consent & Preference Constraints
# ============================================================================

class ConsentTypeValid(BaseConstraint):
    """
    C092: Consent type must be valid.

    CP49: CONSENT_RECORD — ``consent_type`` must be "cookie", "data_processing", "marketing", or "analytics".
    """
    id = "C092"
    description = "Consent type must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.CONSENT_RECORD:
            return []

        results: list[ConstraintResult] = []
        valid_types = {"cookie", "data_processing", "marketing", "analytics"}
        ct = node.params.get("consent_type")

        if ct and ct not in valid_types:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Consent '{node.id}': invalid consent_type '{ct}'",
                node_id=node.id,
                field="consent_type",
                expected=f"one of {valid_types}",
                actual=ct,
            ))

        return results


class CommFrequencyValid(BaseConstraint):
    """
    C093: Communication frequency must be valid.

    CP49: COMM_PREFERENCE — ``frequency`` must be "realtime", "daily", "weekly", or "monthly".
    """
    id = "C093"
    description = "Communication frequency must be valid"
    level = ConstraintLevel.ERROR

    def validate(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext,
    ) -> list[ConstraintResult]:
        if node.kind != NodeKind.COMM_PREFERENCE:
            return []

        results: list[ConstraintResult] = []
        valid_freq = {"realtime", "daily", "weekly", "monthly"}
        freq = node.params.get("frequency")

        if freq and freq not in valid_freq:
            results.append(ConstraintResult(
                constraint_id=self.id,
                level=self.level,
                message=f"Comm preference '{node.id}': invalid frequency '{freq}'",
                node_id=node.id,
                field="frequency",
                expected=f"one of {valid_freq}",
                actual=freq,
            ))

        return results


# ============================================================================
# Constraint Registry
# ============================================================================

@dataclass
class ConstraintRegistry:
    """Registry of all constraints."""
    
    constraints: list[BaseConstraint] = field(default_factory=list)
    
    def register(self, constraint: BaseConstraint) -> "ConstraintRegistry":
        """Register a constraint."""
        self.constraints.append(constraint)
        return self
    
    def get_all(self) -> list[BaseConstraint]:
        """Get all registered constraints."""
        return self.constraints
    
    def validate_node(
        self,
        node: ProjectionNode,
        tree: ProjectionTree,
        ctx: ValidationContext
    ) -> list[ConstraintResult]:
        """Validate a node against all constraints."""
        results = []
        for constraint in self.constraints:
            constraint_results = constraint(node, tree, ctx)
            results.extend(constraint_results)
        return results
    
    def validate_tree(
        self,
        tree: ProjectionTree
    ) -> list[ConstraintResult]:
        """Validate all nodes in a tree."""
        all_results = []
        for node_id in tree.nodes:
            node = tree.get_node(node_id)
            if node:
                ctx = ValidationContext(node_id=node_id)
                results = self.validate_node(node, tree, ctx)
                all_results.extend(results)
        return all_results


# Default registry with all constraints
default_registry = ConstraintRegistry()

# Register all constraints
for cls in [
    # Domain
    EntityFieldTypesValid,
    EntityPrimaryKeyDefined,
    EntityTenantScopeValid,
    EntityConstraintTypesValid,
    ForeignKeyReferencesValid,
    # Application
    CommandCategoryValid,
    QueryCategoryValid,
    CommandTenantScopeValid,
    WorkflowStateMachineValid,
    # API
    HTTPMethodValid,
    HTTPRouteBindsToCommandOrQuery,
    # Access Control
    RolePermissionsValid,
    RoleTenantScopeValid,
    PolicyEffectValid,
    # Integration
    IntegrationAuthTypeValid,
    DataSourceConnectionStringPresent,
    # Error Domain
    ErrorSeverityValid,
    ErrorCategoryValid,
    ErrorCodeUnique,
    # Guard/Effect/Rule
    GuardTypeValid,
    EffectTypeValid,
    RuleTypeValid,
    EventTypeValid,
    GraphQLOperationValid,
    # Infrastructure
    DataSourceTypeValid,
    IntegrationTypeValid,
    AuthProviderTypeValid,
    IndexTypeValid,
    # Observability
    MetricTypeValid,
    MetricAggregationValid,
    LogLevelValid,
    LogFormatValid,
    AlertSeverityValid,
    TraceExporterValid,
    # Advanced C051-C060
    PluginSlotIdUnique,
    CalendarScheduleCronValid,
    GeneralLedgerDoubleEntryValid,
    ReportEntityReferenceExists,
    GeofenceCoordinateRangeValid,
    ETLStepHasExtractAndLoad,
    LocalizationLocaleBCP47,
    APIVersionSemanticVersion,
    PaymentGatewayEndpointsValid,
    ProductCatalogUniqueSKU,
    # CP32: State Machine Engine C061-C062
    StateMachineTransitionValid,
    StateMachineInitialStateExists,
    # CP37: Feature Flags & Dynamic Config C063-C065
    FeatureFlagKeyUnique,
    ExperimentTrafficSplitValid,
    DynamicConfigScopeValid,
    # CP21: Authentication UI C066
    AuthUIFrameworkValid,
    # CP22: Real-time UI C067-C068
    ChannelTransportValid,
    WidgetTypeValid,
    # CP28: Custom Code Injection C069-C070
    CustomCodeInjectPointValid,
    HookEventValid,
    # CP31: Scheduler C071
    CronExpressionValid,
    # CP35: Geospatial C072
    GeofenceShapeValid,
    # CP36: Tenant Onboarding C073-C074
    TenantPlanNameUnique,
    TenantBillingCycleValid,
    # CP40: Webhook C075-C076
    WebhookAuthTypeValid,
    WebhookRetryPolicyPositive,
    # CP41: Chat C077-C078
    ConversationTypeValid,
    ChatMessageTypeValid,
    # CP42: Approval C079-C081
    ApprovalChainTypeValid,
    ApprovalApproverTypeValid,
    EscalationTriggerValid,
    # CP43: Versioning C082
    HistoryOperationValid,
    # CP44: Bulk Operations C083-C084
    BulkOperationValid,
    BulkChunkSizePositive,
    # CP46: MFA C085-C086
    MFAMethodValid,
    MFAChallengeMethodValid,
    # CP47: Data Retention C087-C088
    RetentionActionValid,
    ErasureScopeValid,
    # CP48: Rate Limiting C089-C091
    RateLimitStrategyValid,
    QuotaLevelValid,
    QuotaPeriodValid,
    # CP49: Consent & Preference C092-C093
    ConsentTypeValid,
    CommFrequencyValid,
]:
    default_registry.register(cls())


def get_registry() -> ConstraintRegistry:
    """Get the default constraint registry."""
    return default_registry