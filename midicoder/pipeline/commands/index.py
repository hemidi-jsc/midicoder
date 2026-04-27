"""
Mô-đun Index Command - CLI command cho việc build và manage codebase index.

Cung cấp commands:
- midicoder index: Build index cho current project
- midicoder index --force: Rebuild toàn bộ index
- midicoder index --watch: Watch mode cho auto re-index

Sử dụng:
    midicoder index
    midicoder index --force
    midicoder index --watch
"""

from __future__ import annotations

import os
import sys
import json
from pathlib import Path
from typing import Optional

import click

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM, ExitCode


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


@click.command("index")
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Rebuild entire index from scratch",
)
@click.option(
    "--watch",
    is_flag=True,
    default=False,
    help="Watch for file changes và auto re-index (debounce 1s)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Verbose output",
)
def index_command(force: bool, watch: bool, verbose: bool) -> int:
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
    # Get current project path
    try:
        project_path = get_current_project_path()
    except Exception as e:
        click.echo(f"Lỗi: {e}", err=True)
        return ExitCode.GENERIC_ERROR.value
    
    # Check if project exists
    if not project_path.exists():
        click.echo(
            f"Lỗi: Project directory không tồn tại: {project_path}",
            err=True
        )
        return ExitCode.FILE_NOT_FOUND.value
    
    # Check if project is initialized
    midicoder_dir = project_path / ".midicoder"
    if not midicoder_dir.exists():
        click.echo(
            f"Lỗi: Project chưa được khởi tạo. Chạy `midicoder init` trước.",
            err=True
        )
        return ExitCode.GENERIC_ERROR.value
    
    # Import indexer (lazy import để tránh circular)
    try:
        from midicoder.pipeline.indexer import Indexer, IndexStats
    except ImportError as e:
        click.echo(f"Lỗi khi import indexer module: {e}", err=True)
        return ExitCode.GENERIC_ERROR.value
    
    # Create indexer
    db_path = midicoder_dir / "data" / "context.db"
    indexer = Indexer(
        project_path=str(project_path),
        db_path=str(db_path),
    )
    
    if verbose:
        click.echo(f"Project: {project_path}")
        click.echo(f"Database: {db_path}")
    
    if watch:
        # Watch mode
        if force:
            click.echo("Rebuilding index before watch mode...")
            stats = indexer.build(force=True)
            _print_stats(stats, verbose)
        
        click.echo("Starting watch mode...")
        click.echo("Press Ctrl+C to stop.")
        
        try:
            indexer.watch(debounce_seconds=1.0)
        except KeyboardInterrupt:
            click.echo("\nWatch mode stopped.")
        
        return ExitCode.SUCCESS.value
    
    # Build index
    try:
        stats = indexer.build(force=force)
    except Exception as e:
        click.echo(f"Lỗi khi build index: {e}", err=True)
        return ExitCode.GENERIC_ERROR.value
    
    # Print stats
    _print_stats(stats, verbose)
    
    # Print summary
    if force:
        click.echo(f"\n✓ Rebuilt index: {stats.files_count} files, {stats.symbols_count} symbols")
    else:
        click.echo(f"\n✓ Indexed: {stats.files_count} files, {stats.symbols_count} symbols")
    
    if stats.errors_count > 0:
        click.echo(f"⚠ {stats.errors_count} files had errors (skipped)", err=True)
    
    if stats.neo4j_synced:
        click.echo("✓ Synced to Neo4j")
    else:
        click.echo("⚠ Neo4j sync skipped (not available)", err=True)
    
    return ExitCode.SUCCESS.value


def _print_stats(stats: IndexStats, verbose: bool) -> None:
    """
    Print index stats.
    
    Args:
        stats: IndexStats object
        verbose: Verbose mode
    """
    if verbose:
        click.echo("")
        click.echo("Index Statistics:")
        click.echo(f"  Files indexed: {stats.files_count}")
        click.echo(f"  Symbols extracted: {stats.symbols_count}")
        click.echo(f"  Relationships: {stats.relationships_count}")
        click.echo(f"  Errors: {stats.errors_count}")
        click.echo(f"  Duration: {stats.duration_seconds:.2f}s")
        click.echo(f"  Neo4j synced: {'Yes' if stats.neo4j_synced else 'No'}")


def register_index_command(cli: click.Group) -> None:
    """
    Register index command vào main CLI.
    
    Args:
        cli: Main CLI group
    """
    cli.add_command(index_command)


# Allow running as standalone for testing
if __name__ == "__main__":
    sys.exit(index_command())