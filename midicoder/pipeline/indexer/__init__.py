"""
Mô-đun Indexer cho Midicoder.

Cung cấp khả năng:
- Index codebase thành SQLite (context.db) và Neo4j graph
- Query context cho brief analysis và clarification
- Watch mode cho auto re-index

Cấu trúc:
- indexer.py: Core indexing logic
- parser.py: AST parsing cho multiple languages
- neo4j_client.py: Neo4j sync operations
- query.py: Context query API
"""

from .indexer import Indexer, IndexStats
from .query import ContextItem, get_relevant_context
from .parser import Symbol, SymbolType, parse_file

__all__ = [
    "Indexer",
    "IndexStats",
    "ContextItem",
    "get_relevant_context",
    "Symbol",
    "SymbolType",
    "parse_file",
]