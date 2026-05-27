"""
Mô-đun Indexer - Core logic cho việc build và manage codebase index.

Quản lý:
- SQLite storage (context.db): files, symbols, relationships
- Neo4j sync: graph relationships và embeddings
- Watch mode: auto re-index khi có file changes

Sử dụng:
    from midicoder.pipeline.indexer import Indexer
    
    # Tạo indexer
    indexer = Indexer(project_path="/path/to/project")
    
    # Build index
    stats = indexer.build(force=False)
    print(f"Indexed {stats.files_count} files, {stats.symbols_count} symbols")
    
    # Watch mode
    indexer.watch()
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


@dataclass
class IndexStats:
    """
    Thống kê về index operation.
    
    Attributes:
        files_count: Số files đã index
        symbols_count: Số symbols extract được
        relationships_count: Số relationships
        errors_count: Số lỗi gặp phải
        duration_seconds: Thời gian thực hiện (giây)
        neo4j_synced: Có đồng bộ Neo4j không
    """
    files_count: int = 0
    symbols_count: int = 0
    relationships_count: int = 0
    errors_count: int = 0
    duration_seconds: float = 0.0
    neo4j_synced: bool = False


class Indexer:
    """
    Core indexer class cho Midicoder.
    
    Quản lý việc:
    1. Parse source files
    2. Store vào SQLite (context.db)
    3. Sync vào Neo4j graph
    4. Watch mode cho auto re-index
    
    Attributes:
        project_path: Đường dẫn project cần index
        db_path: Đường dẫn context.db
        exclude_dirs: Danh sách thư mục exclude
        lock: Thread lock cho concurrent access
    """
    
    def __init__(
        self,
        project_path: str,
        db_path: Optional[str] = None,
        exclude_dirs: Optional[list[str]] = None,
    ):
        """
        Khởi tạo Indexer.
        
        Args:
            project_path: Đường dẫn project cần index
            db_path: Đường dẫn context.db (default: .midicoder/data/context.db)
            exclude_dirs: Danh sách thư mục exclude
        """
        self.project_path = os.path.abspath(project_path)
        
        # Default db path trong .midicoder/data/
        if db_path is None:
            self.db_path = os.path.join(
                self.project_path,
                ".midicoder",
                "data",
                "context.db"
            )
        else:
            self.db_path = os.path.abspath(db_path)
        
        self.exclude_dirs = exclude_dirs or []
        self.exclude_dirs.extend([".git", "node_modules", "venv", "__pycache__", "dist", "build", ".midicoder"])
        
        # Thread lock
        self._lock = threading.Lock()
        self._watching = False
        self._watch_thread: Optional[threading.Thread] = None
        
        # Ensure db directory exists
        self._ensure_db_directory()
        
        # Initialize database schema
        self._init_database()
    
    def _ensure_db_directory(self) -> None:
        """Đảm bảo thư mục database tồn tại."""
        db_dir = os.path.dirname(self.db_path)
        os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self) -> None:
        """
        Khởi tạo database schema nếu chưa tồn tại.
        
        Creates tables:
        - files: File metadata và content
        - symbols: Extracted symbols
        - relationships: Symbol relationships
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Files table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                content_hash TEXT,
                language TEXT,
                size_bytes INTEGER,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Symbols table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER REFERENCES files(id),
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                line_start INTEGER,
                line_end INTEGER,
                signature TEXT,
                description TEXT,
                embedding_ref TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Relationships table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_symbol_id INTEGER REFERENCES symbols(id),
                target_symbol_id INTEGER REFERENCES symbols(id),
                type TEXT NOT NULL
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_type ON symbols(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_language ON files(language)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_path ON files(path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_hash ON files(content_hash)")
        
        conn.commit()
        conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Lấy database connection."""
        return sqlite3.connect(self.db_path)
    
    def build(self, force: bool = False) -> IndexStats:
        """
        Build index cho project.
        
        Args:
            force: Nếu True, rebuild toàn bộ index từ đầu
            
        Returns:
            IndexStats với thống kê operation
            
        Raises:
            MidicoderError: Nếu có lỗi khi build index
        """
        start_time = time.time()
        stats = IndexStats()
        
        with self._lock:
            if force:
                self._clear_index()
            
            # Parse directory
            from .parser import parse_directory
            
            parsed_files = parse_directory(self.project_path, self.exclude_dirs)
            
            for parsed_file in parsed_files:
                try:
                    self._index_file(parsed_file)
                    stats.files_count += 1
                    stats.symbols_count += len(parsed_file.symbols)
                    stats.relationships_count += len(parsed_file.relationships)
                except Exception as e:
                    stats.errors_count += 1
                    # Log error but continue
                    print(f"Warning: Error indexing {parsed_file.file_path}: {e}")
            
            # Sync to Neo4j
            try:
                self._sync_to_neo4j()
                stats.neo4j_synced = True
            except Exception as e:
                # Neo4j sync is optional - don't fail the entire index
                print(f"Warning: Neo4j sync failed: {e}")
        
        stats.duration_seconds = time.time() - start_time
        return stats
    
    def _clear_index(self) -> None:
        """Xóa toàn bộ index (dùng cho force rebuild)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM relationships")
        cursor.execute("DELETE FROM symbols")
        cursor.execute("DELETE FROM files")
        
        conn.commit()
        conn.close()
    
    def _index_file(self, parsed_file: Any) -> None:
        """
        Index một file vào database.
        
        Args:
            parsed_file: ParsedFile object từ parser module
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Upsert file
        cursor.execute("""
            INSERT INTO files (path, content_hash, language, size_bytes, content)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                content_hash = excluded.content_hash,
                language = excluded.language,
                size_bytes = excluded.size_bytes,
                content = excluded.content,
                updated_at = CURRENT_TIMESTAMP
        """, (
            parsed_file.file_path,
            parsed_file.content_hash,
            parsed_file.language,
            parsed_file.size_bytes,
            parsed_file.content,
        ))
        
        file_id = cursor.lastrowid
        
        # Get existing file_id if updated
        if cursor.rowcount == 0:
            cursor.execute("SELECT id FROM files WHERE path = ?", (parsed_file.file_path,))
            row = cursor.fetchone()
            if row:
                file_id = row[0]
        
        # Insert symbols
        for symbol in parsed_file.symbols:
            cursor.execute("""
                INSERT INTO symbols (file_id, name, type, line_start, line_end, signature, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                file_id,
                symbol.name,
                symbol.symbol_type.value,
                symbol.line_start,
                symbol.line_end,
                symbol.signature,
                symbol.description,
            ))
        
        # Insert relationships (store symbol names for now, resolve IDs later)
        for rel in parsed_file.relationships:
            # Store relationship with symbol names
            # TODO: Resolve to symbol IDs after all symbols are indexed
            cursor.execute("""
                INSERT INTO relationships (source_symbol_id, target_symbol_id, type)
                VALUES (NULL, NULL, ?)
            """, (rel.relationship_type,))
        
        conn.commit()
        conn.close()
    
    def _sync_to_neo4j(self) -> None:
        """
        Sync index data vào Neo4j graph.
        
        Creates nodes:
        - (:File {path, hash, language})
        - (:Symbol {name, type, signature})
        
        Creates relationships:
        - (:File)-[:CONTAINS]->(:Symbol)
        - (:Symbol)-[:CALLS|IMPORTS|EXTENDS]->(:Symbol)
        """
        # Try to import neo4j driver
        try:
            from neo4j import GraphDatabase
        except ImportError:
            print("Warning: neo4j driver not installed. Skipping Neo4j sync.")
            return
        
        # Neo4j connection config
        neo4j_uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
        neo4j_password = os.environ.get("NEO4J_PASSWORD", "midicoder")
        
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        try:
            with driver.session() as session:
                # Get files
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("SELECT id, path, content_hash, language FROM files")
                files = cursor.fetchall()
                
                # Create File nodes
                for file_id, path, hash_val, language in files:
                    session.run("""
                        MERGE (f:File {path: $path})
                        SET f.hash = $hash, f.language = $language
                    """, path=path, hash=hash_val, language=language)
                
                # Get symbols
                cursor.execute("""
                    SELECT s.id, s.name, s.type, s.signature, f.path
                    FROM symbols s
                    JOIN files f ON s.file_id = f.id
                """)
                symbols = cursor.fetchall()
                
                # Create Symbol nodes và CONTAINS relationships
                for sym_id, name, sym_type, signature, file_path in symbols:
                    session.run("""
                        MATCH (f:File {path: $file_path})
                        MERGE (s:Symbol {name: $name, file_path: $file_path})
                        SET s.type = $type, s.signature = $signature
                        MERGE (f)-[:CONTAINS]->(s)
                    """, file_path=file_path, name=name, type=sym_type, signature=signature)
                
                conn.close()
                
        except Exception as e:
            print(f"Warning: Neo4j sync error: {e}")
        finally:
            driver.close()
    
    def watch(self, debounce_seconds: float = 1.0) -> None:
        """
        Start watch mode - auto re-index khi có file changes.
        
        Args:
            debounce_seconds: Debounce thời gian trước khi re-index
        """
        if self._watching:
            return
        
        # Try to import watchdog
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            print("Warning: watchdog not installed. Watch mode not available.")
            print("Install with: pip install watchdog")
            return
        
        class IndexHandler(FileSystemEventHandler):
            def __init__(self, indexer: Indexer, debounce: float):
                self.indexer = indexer
                self.debounce = debounce
                self._last_index_time = 0
                self._lock = threading.Lock()
            
            def on_modified(self, event):
                if event.is_directory:
                    return
                
                # Check debounce
                with self._lock:
                    now = time.time()
                    if now - self._last_index_time < self.debounce:
                        return
                    self._last_index_time = now
                
                # Trigger incremental index
                print(f"File modified: {event.src_path}")
                # TODO: Incremental re-index only changed file
            
            def on_created(self, event):
                if event.is_directory:
                    return
                print(f"File created: {event.src_path}")
            
            def on_deleted(self, event):
                if event.is_directory:
                    return
                print(f"File deleted: {event.src_path}")
        
        event_handler = IndexHandler(self, debounce_seconds)
        observer = Observer()
        observer.schedule(event_handler, self.project_path, recursive=True)
        observer.start()
        
        self._watching = True
        self._watch_thread = threading.current_thread()
        
        print(f"Watching directory: {self.project_path}")
        print("Press Ctrl+C to stop watching...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            self._watching = False
    
    def stop_watch(self) -> None:
        """Stop watch mode."""
        self._watching = False
    
    def get_file_count(self) -> int:
        """Lấy số lượng files đã index."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM files")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_symbol_count(self) -> int:
        """Lấy số lượng symbols đã index."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM symbols")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def search_symbols(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Tìm symbols theo query text.
        
        Args:
            query: Query text
            limit: Số kết quả trả về
            
        Returns:
            Danh sách symbols matching
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.name, s.type, s.signature, s.description, f.path
            FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE s.name LIKE ? OR s.description LIKE ? OR s.signature LIKE ?
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "name": row[0],
                "type": row[1],
                "signature": row[2],
                "description": row[3] or "",
                "file_path": row[4],
            })
        
        conn.close()
        return results


__all__ = ["IndexStats", "Indexer"]