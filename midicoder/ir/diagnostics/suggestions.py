"""Suggestion generation for error messages.

This module provides fuzzy matching and suggestion capabilities
to help users fix errors quickly.
"""

from __future__ import annotations

from difflib import get_close_matches

from ..symbols.symbol_table import SymbolTable


def suggest_similar_ids(
    target: str,
    candidates: list[str],
    n: int = 3,
    cutoff: float = 0.6,
) -> list[str]:
    """
    Find similar IDs using fuzzy matching.

    Args:
        target: The ID that wasn't found
        candidates: List of valid IDs to compare against
        n: Maximum number of suggestions to return
        cutoff: Similarity threshold (0.0 to 1.0)

    Returns:
        List of similar IDs, sorted by similarity

    Examples:
        >>> suggest_similar_ids("usr", ["user", "user_profile", "account"])
        ["user", "user_profile"]
    """
    if not candidates:
        return []

    return get_close_matches(target, candidates, n=n, cutoff=cutoff)


def suggest_for_unresolved_entity(
    entity_id: str,
    symbol_table: SymbolTable,
) -> str | None:
    """
    Generate suggestion for unresolved entity reference.

    Args:
        entity_id: The entity ID that wasn't found
        symbol_table: Symbol table to search for similar entities

    Returns:
        Suggestion message or None
    """
    from ..symbols.symbol_table import SYMBOL_TYPE_ENTITY

    entities = symbol_table.get_all_by_type(SYMBOL_TYPE_ENTITY)
    entity_ids = [e.id for e in entities]

    similar = suggest_similar_ids(entity_id, entity_ids)

    if similar:
        if len(similar) == 1:
            return f"Did you mean '{similar[0]}'?"
        else:
            quoted_suggestions = [f"'{s}'" for s in similar]
            return f"Did you mean one of: {', '.join(quoted_suggestions)}?"

    return None


def suggest_for_unresolved_type(
    ref_type: str,
    ref_id: str,
    symbol_table: SymbolTable,
) -> str | None:
    """
    Generate suggestion for unresolved type reference.

    Args:
        ref_type: Type name (Entity, Enum, ValueObject)
        ref_id: The ID that wasn't found
        symbol_table: Symbol table to search

    Returns:
        Suggestion message or None
    """
    from ..symbols.symbol_table import (
        SYMBOL_TYPE_ENTITY,
        SYMBOL_TYPE_ENUM,
        SYMBOL_TYPE_VALUE_OBJECT,
    )

    # Map type names to symbol types
    type_map = {
        "Entity": SYMBOL_TYPE_ENTITY,
        "ValueObject": SYMBOL_TYPE_VALUE_OBJECT,
        "Enum": SYMBOL_TYPE_ENUM,
    }

    if ref_type not in type_map:
        return None

    symbol_type = type_map[ref_type]
    symbols = symbol_table.get_all_by_type(symbol_type)
    ids = [s.id for s in symbols]

    similar = suggest_similar_ids(ref_id, ids)

    if similar:
        if len(similar) == 1:
            return f"Did you mean '{ref_type}:{similar[0]}'?"
        else:
            suggestions = ", ".join(f"'{ref_type}:{s}'" for s in similar)
            return f"Did you mean one of: {suggestions}?"

    return None


def suggest_for_unresolved_command(
    command_id: str,
    symbol_table: SymbolTable,
) -> str | None:
    """Generate suggestion for unresolved command reference."""
    from ..symbols.symbol_table import SYMBOL_TYPE_COMMAND

    commands = symbol_table.get_all_by_type(SYMBOL_TYPE_COMMAND)
    command_ids = [c.id for c in commands]

    similar = suggest_similar_ids(command_id, command_ids)

    if similar:
        if len(similar) == 1:
            return f"Did you mean '{similar[0]}'?"
        else:
            quoted_suggestions = [f"'{s}'" for s in similar]
            return f"Did you mean one of: {', '.join(quoted_suggestions)}?"

    return None


def suggest_for_unresolved_query(
    query_id: str,
    symbol_table: SymbolTable,
) -> str | None:
    """Generate suggestion for unresolved query reference."""
    from ..symbols.symbol_table import SYMBOL_TYPE_QUERY

    queries = symbol_table.get_all_by_type(SYMBOL_TYPE_QUERY)
    query_ids = [q.id for q in queries]

    similar = suggest_similar_ids(query_id, query_ids)

    if similar:
        if len(similar) == 1:
            return f"Did you mean '{similar[0]}'?"
        else:
            quoted_suggestions = [f"'{s}'" for s in similar]
            return f"Did you mean one of: {', '.join(quoted_suggestions)}?"

    return None


def suggest_for_unresolved_error(
    error_id: str,
    symbol_table: SymbolTable,
) -> str | None:
    """Generate suggestion for unresolved error reference."""
    from ..symbols.symbol_table import SYMBOL_TYPE_ERROR

    errors = symbol_table.get_all_by_type(SYMBOL_TYPE_ERROR)
    error_ids = [e.id for e in errors]

    similar = suggest_similar_ids(error_id, error_ids)

    if similar:
        if len(similar) == 1:
            return f"Did you mean '{similar[0]}'?"
        else:
            quoted_suggestions = [f"'{s}'" for s in similar]
            return f"Did you mean one of: {', '.join(quoted_suggestions)}?"

    return None


def suggest_for_unresolved_event(
    event_id: str,
    symbol_table: SymbolTable,
) -> str | None:
    """Generate suggestion for unresolved event reference."""
    from ..symbols.symbol_table import SYMBOL_TYPE_EVENT

    events = symbol_table.get_all_by_type(SYMBOL_TYPE_EVENT)
    event_ids = [e.id for e in events]

    similar = suggest_similar_ids(event_id, event_ids)

    if similar:
        if len(similar) == 1:
            return f"Did you mean '{similar[0]}'?"
        else:
            quoted_suggestions = [f"'{s}'" for s in similar]
            return f"Did you mean one of: {', '.join(quoted_suggestions)}?"

    return None


__all__ = [
    "suggest_similar_ids",
    "suggest_for_unresolved_entity",
    "suggest_for_unresolved_type",
    "suggest_for_unresolved_command",
    "suggest_for_unresolved_query",
    "suggest_for_unresolved_error",
    "suggest_for_unresolved_event",
]
