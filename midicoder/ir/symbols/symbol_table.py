"""Symbol table for IR cross-reference resolution."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class Symbol:
    """Represents a symbol in the contract system."""

    type: str  # "Entity", "Command", "Workflow", etc.
    id: str  # Canonical ID (normalized)
    source_file: str  # Relative path to source file
    source_line: int | None  # Line number if available
    data: Any  # Full object data

    def __repr__(self) -> str:
        return f"Symbol({self.type}:{self.id} @ {self.source_file})"


class SymbolTable:
    """Global symbol table for contract resolution."""

    def __init__(self) -> None:
        # (type, id) → Symbol
        self._symbols: dict[tuple[str, str], Symbol] = {}

        # Track duplicates for error reporting
        self._duplicates: list[tuple[str, str, Symbol, Symbol]] = []

    def register(
        self,
        type: str,
        id: str,
        source_file: str,
        data: Any,
        source_line: int | None = None,
    ) -> bool:
        """
        Register a symbol in the table.

        Returns:
            True if registered successfully, False if duplicate found.
        """
        key = (type, id)

        if key in self._symbols:
            existing = self._symbols[key]
            new_symbol = Symbol(type, id, source_file, source_line, data)
            if self._is_equivalent_payload(existing.data, data):
                # Same semantic symbol declared in another file.
                # Treat as idempotent instead of hard duplicate.
                return True

            existing_score = self._source_affinity_score(type, existing.source_file)
            new_score = self._source_affinity_score(type, source_file)

            # Auto-resolve only when one definition is from an auxiliary file
            # (score == 0) and the other is from a canonical-looking file.
            if new_score > existing_score and existing_score == 0:
                self._symbols[key] = new_symbol
                return True

            if new_score < existing_score and new_score == 0:
                return True

            # Conflicting duplicate with equal priority.
            self._duplicates.append((type, id, existing, new_symbol))
            return False

        symbol = Symbol(type, id, source_file, source_line, data)
        self._symbols[key] = symbol
        return True

    def _source_affinity_score(self, symbol_type: str, source_file: str) -> int:
        """
        Heuristic score for how well a file path matches symbol semantics.

        Higher score means the path appears more canonical for that symbol type.
        """
        normalized = source_file.replace("\\", "/").lower()
        tokens = [t for t in re.split(r"[/_.\-]+", normalized) if t]
        if not tokens:
            return 0

        type_tokens = self._split_type_tokens(symbol_type)
        if not type_tokens:
            return 0

        score = 0
        for token in tokens:
            for hint in type_tokens:
                if token == hint:
                    score += 3
                elif hint in token:
                    score += 1

        return score

    def _split_type_tokens(self, symbol_type: str) -> list[str]:
        """
        Convert symbol type names to path-matching tokens.

        Example:
        - "ValueObject" -> ["value", "object", "value_object", "value_objects"]
        - "GraphQLType" -> ["graphql", "type", "graphql_type", "graphql_types"]
        """
        if not symbol_type:
            return []

        words = re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+", symbol_type)
        lowered = [w.lower() for w in words if w]
        if not lowered:
            return []

        joined = "_".join(lowered)
        variants = set(lowered)
        variants.add(joined)
        variants.add(f"{joined}s")

        # Basic singularization for common irregular plurals in paths.
        if joined.endswith("y"):
            variants.add(f"{joined[:-1]}ies")

        return sorted(variants)

    def _is_equivalent_payload(self, left: Any, right: Any) -> bool:
        """Check whether two symbol payloads are semantically equivalent."""
        return self._canonical_payload(left) == self._canonical_payload(right)

    def _canonical_payload(self, payload: Any) -> str:
        if hasattr(payload, "model_dump"):
            payload = payload.model_dump()
        try:
            return json.dumps(
                payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            )
        except TypeError:
            return repr(payload)

    def resolve(self, type: str, id: str) -> Symbol | None:
        """Resolve a reference to a symbol."""
        key = (type, id)
        return self._symbols.get(key)

    def get_all_by_type(self, type: str) -> list[Symbol]:
        """Get all symbols of a specific type."""
        return [
            symbol
            for (sym_type, _), symbol in self._symbols.items()
            if sym_type == type
        ]

    def has_duplicates(self) -> bool:
        """Check if there are any duplicate symbols."""
        return len(self._duplicates) > 0

    def get_duplicates(self) -> list[tuple[str, str, Symbol, Symbol]]:
        """Get list of duplicate symbols."""
        return self._duplicates

    def get_all_symbols(self) -> dict[tuple[str, str], Symbol]:
        """Get all symbols."""
        return self._symbols.copy()

    def get_stats(self) -> dict[str, int]:
        """Get statistics about symbols."""
        stats: dict[str, int] = {}
        for (type, _), _ in self._symbols.items():
            stats[type] = stats.get(type, 0) + 1
        return stats


# Symbol types
SYMBOL_TYPE_ENTITY = "Entity"
SYMBOL_TYPE_VALUE_OBJECT = "ValueObject"
SYMBOL_TYPE_ENUM = "Enum"
SYMBOL_TYPE_ERROR = "Error"
SYMBOL_TYPE_EVENT = "Event"
SYMBOL_TYPE_COMMAND = "Command"
SYMBOL_TYPE_QUERY = "Query"
SYMBOL_TYPE_PROJECTION = "Projection"
SYMBOL_TYPE_WORKFLOW = "Workflow"
SYMBOL_TYPE_RULE = "Rule"
SYMBOL_TYPE_SCENARIO = "Scenario"
SYMBOL_TYPE_ROLE = "Role"
SYMBOL_TYPE_PERMISSION = "Permission"
SYMBOL_TYPE_POLICY = "Policy"
SYMBOL_TYPE_HTTP_ROUTE = "HttpRoute"
SYMBOL_TYPE_GRAPHQL_TYPE = "GraphQLType"
SYMBOL_TYPE_GRAPHQL_QUERY = "GraphQLQuery"
SYMBOL_TYPE_GRAPHQL_MUTATION = "GraphQLMutation"
SYMBOL_TYPE_PERSISTENCE_DATASOURCE = "PersistenceDatasource"
SYMBOL_TYPE_PERSISTENCE_TABLE = "PersistenceTable"
SYMBOL_TYPE_INTEGRATION = "Integration"
SYMBOL_TYPE_INTEGRATION_OPERATION = "IntegrationOperation"
SYMBOL_TYPE_RELIABILITY_POLICY = "ReliabilityPolicy"
SYMBOL_TYPE_TEST_CASE = "TestCase"
SYMBOL_TYPE_SECRET = "Secret"


# Catalog of all symbol types
ALL_SYMBOL_TYPES = [
    SYMBOL_TYPE_ENTITY,
    SYMBOL_TYPE_VALUE_OBJECT,
    SYMBOL_TYPE_ENUM,
    SYMBOL_TYPE_ERROR,
    SYMBOL_TYPE_EVENT,
    SYMBOL_TYPE_COMMAND,
    SYMBOL_TYPE_QUERY,
    SYMBOL_TYPE_PROJECTION,
    SYMBOL_TYPE_WORKFLOW,
    SYMBOL_TYPE_RULE,
    SYMBOL_TYPE_SCENARIO,
    SYMBOL_TYPE_ROLE,
    SYMBOL_TYPE_PERMISSION,
    SYMBOL_TYPE_POLICY,
    SYMBOL_TYPE_HTTP_ROUTE,
    SYMBOL_TYPE_GRAPHQL_TYPE,
    SYMBOL_TYPE_GRAPHQL_QUERY,
    SYMBOL_TYPE_GRAPHQL_MUTATION,
    SYMBOL_TYPE_PERSISTENCE_DATASOURCE,
    SYMBOL_TYPE_PERSISTENCE_TABLE,
    SYMBOL_TYPE_INTEGRATION,
    SYMBOL_TYPE_INTEGRATION_OPERATION,
    SYMBOL_TYPE_RELIABILITY_POLICY,
    SYMBOL_TYPE_TEST_CASE,
    SYMBOL_TYPE_SECRET,
]
