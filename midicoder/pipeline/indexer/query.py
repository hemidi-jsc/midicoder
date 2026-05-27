"""
Mô-đun Query - Context query API cho brief analysis và clarification.

Cung cấp:
- get_relevant_context(): Lấy context từ codebase cho một brief
- Hybrid search: Structural (SQLite) + Semantic (Neo4j vectors)

Sử dụng:
    from midicoder.pipeline.indexer.query import get_relevant_context, ContextItem
    
    # Lấy context cho brief
    context_items = get_relevant_context(brief=brief_object)
    for item in context_items:
        print(f"{item.symbol_name}: {item.description}")
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class ContextItem:
    """
    Đại diện cho một context item từ codebase.
    
    Attributes:
        symbol_name: Tên symbol
        symbol_type: Loại symbol (function, class, interface, etc.)
        file_path: Đường dẫn file chứa symbol
        signature: Signature của symbol
        description: Mô tả symbol
        content_snippet: Đoạn code snippet xung quanh symbol
        relevance_score: Điểm relevance (0.0 - 1.0)
    """
    symbol_name: str
    symbol_type: str
    file_path: str
    signature: str
    description: str
    content_snippet: str
    relevance_score: float
    
    def to_dict(self) -> dict[str, Any]:
        """Chuyển ContextItem thành dictionary."""
        return {
            "symbol_name": self.symbol_name,
            "symbol_type": self.symbol_type,
            "file_path": self.file_path,
            "signature": self.signature,
            "description": self.description,
            "content_snippet": self.content_snippet,
            "relevance_score": self.relevance_score,
        }
    
    def format_for_prompt(self) -> str:
        """
        Format context item cho LLM prompt.
        
        Returns:
            Formatted string cho prompt injection
        """
        lines = [
            f"- **{self.symbol_name}** ({self.symbol_type})",
            f"  Location: {self.file_path}",
            f"  Signature: {self.signature}",
        ]
        if self.description:
            lines.append(f"  Description: {self.description}")
        if self.content_snippet:
            lines.append(f"  Code:\n```")
            lines.append(self.content_snippet.strip())
            lines.append("```")
        return "\n".join(lines)


class Brief:
    """
    Simple Brief class cho type hints.
    
    Trong thực tế sẽ import từ brief module.
    """
    def __init__(self, content: str, domain: Optional[str] = None):
        self.content = content
        self.domain = domain


def get_relevant_context(
    brief: Brief,
    db_path: Optional[str] = None,
    limit: int = 10,
) -> list[ContextItem]:
    """
    Lấy ngữ cảnh codebase liên quan đến brief.
    
    Thuật toán:
    1. Extract keywords từ brief content
    2. Query SQLite cho structural matches (symbol names, signatures)
    3. Query Neo4j cho semantic similarity (nếu có vectors)
    4. Merge results, rank by relevance
    5. Return top N context items
    
    Args:
        brief: Brief object với content và domain
        db_path: Đường dẫn context.db (default: tìm từ environment)
        limit: Số context items trả về
        
    Returns:
        Danh sách ContextItem objects, sorted by relevance score
    """
    # Extract keywords from brief
    keywords = _extract_keywords(brief.content)
    
    # Get structural matches from SQLite
    structural_results = _query_structural(db_path, keywords, limit * 2)
    
    # Get semantic matches from Neo4j (if available)
    semantic_results = _query_semantic(db_path, brief.content, limit * 2)
    
    # Merge and rank results
    all_results = _merge_and_rank(structural_results, semantic_results, keywords)
    
    return all_results[:limit]


def _extract_keywords(text: str) -> list[str]:
    """
    Extract keywords từ text.
    
    Simple implementation: Split by whitespace và punctuation,
    filter common words.
    
    Args:
        text: Text để extract keywords
        
    Returns:
        List của keywords
    """
    # Common words to filter
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
        "be", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "must", "shall", "can", "need",
        "dare", "ought", "used", "it", "its", "this", "that", "these", "those",
        "i", "you", "he", "she", "we", "they", "what", "which", "who", "whom",
        "all", "each", "every", "both", "few", "more", "most", "other", "some",
        "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too",
        "very", "just", "also", "now", "here", "there", "when", "where", "why",
        "how", "all", "any", "both", "each", "few", "more", "most", "other",
        "some", "such", "can", "could", "should", "would", "will", "shall",
        "may", "might", "must", "need", "dare", "ought", "used", "to", "of",
        "and", "or", "but", "in", "on", "at", "for", "with", "by", "from",
        "up", "about", "into", "through", "during", "before", "after", "above",
        "below", "between", "under", "again", "further", "then", "once",
        "build", "create", "make", "develop", "system", "application", "app",
        "platform", "software", "website", "web", "site", "user", "users",
        "data", "information", "service", "api", "backend", "frontend",
    }
    
    # Simple tokenization
    import re
    words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]+\b', text.lower())
    
    # Filter stop words and short words
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    return list(set(keywords))[:20]  # Return top 20 unique keywords


def _query_structural(
    db_path: Optional[str],
    keywords: list[str],
    limit: int,
) -> list[ContextItem]:
    """
    Query SQLite cho structural matches.
    
    Args:
        db_path: Đường dẫn context.db
        keywords: Danh sách keywords
        limit: Số results trả về
        
    Returns:
        Danh sách ContextItem từ structural search
    """
    if not db_path:
        db_path = _find_context_db()
    
    if not db_path or not os.path.exists(db_path):
        return []
    
    results = []
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for keyword in keywords:
            # Search in symbol names and descriptions
            cursor.execute("""
                SELECT s.name, s.type, s.signature, s.description, f.path, f.content
                FROM symbols s
                JOIN files f ON s.file_id = f.id
                WHERE s.name LIKE ? OR s.description LIKE ? OR s.signature LIKE ?
                LIMIT ?
            """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit // len(keywords) if keywords else limit))
            
            for row in cursor.fetchall():
                symbol_name, symbol_type, signature, description, file_path, content = row
                
                # Extract content snippet around symbol
                snippet = _extract_snippet_from_content(content, symbol_name) if content else ""
                
                # Calculate simple relevance score
                score = _calculate_keyword_relevance(
                    f"{symbol_name} {signature} {description or ''}",
                    keywords
                )
                
                results.append(ContextItem(
                    symbol_name=symbol_name,
                    symbol_type=symbol_type or "unknown",
                    file_path=file_path,
                    signature=signature or "",
                    description=description or "",
                    content_snippet=snippet,
                    relevance_score=score,
                ))
        
        conn.close()
        
    except Exception as e:
        print(f"Warning: Structural query failed: {e}")
    
    return results


def _query_semantic(
    db_path: Optional[str],
    query_text: str,
    limit: int,
) -> list[ContextItem]:
    """
    Query Neo4j cho semantic similarity.
    
    Đây là placeholder - production sẽ dùng vector embeddings.
    
    Args:
        db_path: Đường dẫn context.db
        query_text: Query text
        limit: Số results
        
    Returns:
        Danh sách ContextItem từ semantic search
    """
    # Placeholder: Return empty for now
    # Future implementation sẽ:
    # 1. Generate embedding for query_text
    # 2. Query Neo4j với vector similarity
    # 3. Return results with cosine similarity scores
    
    try:
        from neo4j import GraphDatabase
    except ImportError:
        return []
    
    results = []
    
    neo4j_uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
    neo4j_password = os.environ.get("NEO4J_PASSWORD", "midicoder")
    
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        with driver.session() as session:
            # Placeholder query - just return some symbols
            # Real implementation sẽ dùng vector similarity
            result = session.run("""
                MATCH (s:Symbol)
                RETURN s.name, s.type, s.signature, s.file_path
                LIMIT $limit
            """, limit=limit)
            
            for record in result:
                # Get content from SQLite
                if db_path and os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT f.content FROM files f
                        WHERE f.path = ?
                    """, (record["s.file_path"],))
                    row = cursor.fetchone()
                    content = row[0] if row else ""
                    conn.close()
                else:
                    content = ""
                
                snippet = _extract_snippet_from_content(content, record["s.name"]) if content else ""
                
                results.append(ContextItem(
                    symbol_name=record["s.name"],
                    symbol_type=record["s.type"] or "unknown",
                    file_path=record["s.file_path"],
                    signature=record["s.signature"] or "",
                    description="",
                    content_snippet=snippet,
                    relevance_score=0.5,  # Placeholder score
                ))
        
        driver.close()
        
    except Exception as e:
        print(f"Warning: Semantic query failed: {e}")
    
    return results


def _extract_snippet_from_content(content: str, symbol_name: str, context_lines: int = 5) -> str:
    """
    Extract code snippet xung quanh symbol từ content.
    
    Args:
        content: Full file content
        symbol_name: Tên symbol để tìm
        context_lines: Số dòng context xung quanh
        
    Returns:
        Code snippet string
    """
    lines = content.split("\n")
    
    for i, line in enumerate(lines):
        if symbol_name in line and (line.strip().startswith("def ") or line.strip().startswith("class ") or line.strip().startswith("function ")):
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)
            return "\n".join(lines[start:end])
    
    # Fallback: return first 20 lines
    return "\n".join(lines[:20])


def _calculate_keyword_relevance(text: str, keywords: list[str]) -> float:
    """
    Tính relevance score dựa trên keyword matches.
    
    Args:
        text: Text để check
        keywords: Danh sách keywords
        
    Returns:
        Relevance score (0.0 - 1.0)
    """
    if not keywords:
        return 0.0
    
    text_lower = text.lower()
    matches = sum(1 for kw in keywords if kw.lower() in text_lower)
    
    # Simple TF-like scoring
    score = matches / len(keywords) if keywords else 0.0
    
    return min(1.0, score)


def _merge_and_rank(
    structural: list[ContextItem],
    semantic: list[ContextItem],
    keywords: list[str],
) -> list[ContextItem]:
    """
    Merge và rank results từ structural và semantic search.
    
    Args:
        structural: Results từ structural search
        semantic: Results từ semantic search
        keywords: Keywords để tính relevance
        
    Returns:
        Merged và ranked list của ContextItem
    """
    # Deduplicate by symbol_name + file_path
    seen = set()
    merged = []
    
    for item in structural + semantic:
        key = (item.symbol_name, item.file_path)
        if key not in seen:
            seen.add(key)
            merged.append(item)
    
    # Sort by relevance score
    merged.sort(key=lambda x: x.relevance_score, reverse=True)
    
    return merged


def _find_context_db() -> Optional[str]:
    """
    Tìm context.db trong current project.
    
    Returns:
        Đường dẫn context.db hoặc None
    """
    # Try current directory
    cwd = os.getcwd()
    
    # Check .midicoder/data/context.db
    db_path = os.path.join(cwd, ".midicoder", "data", "context.db")
    if os.path.exists(db_path):
        return db_path
    
    # Check environment variable
    env_db = os.environ.get("MIDICODER_CONTEXT_DB")
    if env_db and os.path.exists(env_db):
        return env_db
    
    return None


def format_context_for_prompt(context_items: list[ContextItem]) -> str:
    """
    Format danh sách context items cho LLM prompt.
    
    Args:
        context_items: Danh sách ContextItem
        
    Returns:
        Formatted string cho prompt injection
    """
    if not context_items:
        return "No relevant codebase context found."
    
    lines = [
        "## Codebase Context",
        "",
        "The following symbols and code patterns exist in the codebase:",
        "",
    ]
    
    for item in context_items:
        lines.append(item.format_for_prompt())
        lines.append("")
    
    return "\n".join(lines)


__all__ = [
    "ContextItem",
    "Brief",
    "get_relevant_context",
    "format_context_for_prompt",
]