"""
Mô-đun Index - Pure functions cho việc build và manage codebase index.

Cung cấp hàm:
- build_index(): Build index cho current project
- get_global_config_path(): Lấy đường dẫn global config
- get_current_project_path(): Lấy đường dẫn current project
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


def get_global_config_path() -> Path:
    """
    Lấy đường dẫn global config file.
    
    Returns:
        Path đến ~/.midicoder/midicoder.json
    """
    home_dir = Path.home()
    config_dir = home_dir / ".midicoder"
    return config_dir / "midicoder.json"


def get_current_project_path() -> Path:
    """
    Lấy đường dẫn current project từ global config.
    
    Returns:
        Path đến current project
        
    Raises:
        MidicoderError: Nếu không tìm thấy current project
    """
    config_path = get_global_config_path()
    
    if not config_path.exists():
        EM.raise_error(
            ErrorCode.INDEX_PROJECT_NOT_FOUND,
            config_path=str(config_path)
        )
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        EM.raise_error(
            ErrorCode.CONFIG_FORMAT_INVALID,
            file_path=str(config_path),
            cause=e
        )
    
    project_path = config.get("current_project")
    
    if not project_path:
        EM.raise_error(
            ErrorCode.INDEX_PROJECT_NOT_FOUND,
            message="Không tìm thấy current project trong config"
        )
    
    return Path(project_path)


def build_index(
    force: bool = False,
    watch: bool = False,
    verbose: bool = False,
) -> int:
    """
    Build codebase index cho context-aware brief analysis.

    Index source code vào SQLite (context.db) và Neo4j graph
    để cung cấp context cho brief analysis và clarification.

    Args:
        force: Rebuild entire index
        watch: Watch mode cho auto re-index
        verbose: Verbose output

    Returns:
        Exit code (0 = success, 1 = error)
    """
    from midicoder.errors import ExitCode

    # Get current project path
    try:
        project_path = get_current_project_path()
    except Exception as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        return ExitCode.GENERIC_ERROR.value

    # Check if project exists
    if not project_path.exists():
        print(
            f"Lỗi: Project directory không tồn tại: {project_path}",
            file=sys.stderr
        )
        return ExitCode.FILE_NOT_FOUND.value

    # Check if project is initialized
    midicoder_dir = project_path / ".midicoder"
    if not midicoder_dir.exists():
        print(
            f"Lỗi: Project chưa được khởi tạo. Chạy `midicoder init` trước.",
            file=sys.stderr
        )
        return ExitCode.GENERIC_ERROR.value

    # Import indexer (lazy import để tránh circular)
    try:
        from midicoder.pipeline.indexer import Indexer, IndexStats
    except ImportError as e:
        print(f"Lỗi khi import indexer module: {e}", file=sys.stderr)
        return ExitCode.GENERIC_ERROR.value

    # Create indexer
    db_path = midicoder_dir / "data" / "context.db"
    indexer = Indexer(
        project_path=str(project_path),
        db_path=str(db_path),
    )

    if verbose:
        print(f"Project: {project_path}")
        print(f"Database: {db_path}")

    if watch:
        # Watch mode
        if force:
            print("Rebuilding index before watch mode...")
            stats = indexer.build(force=True)
            _print_stats(stats, verbose)

        print("Starting watch mode...")
        print("Press Ctrl+C to stop.")

        try:
            indexer.watch(debounce_seconds=1.0)
        except KeyboardInterrupt:
            print("\nWatch mode stopped.")

        return ExitCode.SUCCESS.value

    # Build index
    try:
        stats = indexer.build(force=force)
    except Exception as e:
        print(f"Lỗi khi build index: {e}", file=sys.stderr)
        return ExitCode.GENERIC_ERROR.value

    # Print stats
    _print_stats(stats, verbose)

    # Print summary
    if force:
        print(f"\n✓ Rebuilt index: {stats.files_count} files, {stats.symbols_count} symbols")
    else:
        print(f"\n✓ Indexed: {stats.files_count} files, {stats.symbols_count} symbols")

    if stats.errors_count > 0:
        print(f"⚠ {stats.errors_count} files had errors (skipped)", file=sys.stderr)

    if stats.neo4j_synced:
        print("✓ Synced to Neo4j")
    else:
        print("⚠ Neo4j sync skipped (not available)", file=sys.stderr)

    return ExitCode.SUCCESS.value


def _print_stats(stats: "IndexStats", verbose: bool) -> None:
    """
    Print index stats.

    Args:
        stats: IndexStats object
        verbose: Verbose mode
    """
    if verbose:
        print("")
        print("Index Statistics:")
        print(f"  Files indexed: {stats.files_count}")
        print(f"  Symbols extracted: {stats.symbols_count}")
        print(f"  Relationships: {stats.relationships_count}")
        print(f"  Errors: {stats.errors_count}")
        print(f"  Duration: {stats.duration_seconds:.2f}s")
        print(f"  Neo4j synced: {'Yes' if stats.neo4j_synced else 'No'}")