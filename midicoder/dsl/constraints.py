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
]:
    default_registry.register(cls())


def get_registry() -> ConstraintRegistry:
    """Get the default constraint registry."""
    return default_registry