"""Generate project context artifacts for Midicoder."""

from __future__ import annotations

import json
import logging
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .analyzers.registry import analyze_symbols
from .core.models import (
    ContextArtifacts,
    EntryPoint,
    Exemplar,
    FileMeta,
    IndexManifest,
    ProjectProfile,
    Seam,
    Symbol,
)
from .core.scanner import (
    FileCache,
    GitIgnoreMatcher,
    ProjectScanner,
    load_gitignore_files,
)
from .detectors.registry import detect_stack, read_config_stack
from .extractors.entrypoints import extract_entrypoints
from .extractors.exemplars import extract_exemplars
from .extractors.manifest import build_index_manifest
from .extractors.profile import extract_project_profile
from .extractors.seams import extract_seams
from .virtual_seams import write_virtual_seams

logger = logging.getLogger(__name__)
TOOL_VERSION = "0.1.0"


def build_context(
    root: Path,
    context_root: Path | None = None,
    refresh: bool = False,
    reindex_only_changed: bool = False,
    changed_paths: list[str] | None = None,
) -> None:
    start_time = time.time()

    if context_root is None:
        context_root = root

    logger.info(f"Starting context indexing for: {root}")
    logger.debug(f"Workspace directory: {root}")
    logger.debug(f"Context will be saved to: {context_root}")

    try:
        gitignore_files, ignored_patterns = load_gitignore_files(root)
        logger.debug(f"Loaded {len(ignored_patterns)} ignore patterns from .gitignore")

        file_cache = FileCache()
        ignore_matcher = GitIgnoreMatcher(root, gitignore_files)
        scanner = ProjectScanner(root, ignore_matcher, ignored_patterns, file_cache)

        existing = (
            load_existing_context(context_root / ".midicoder" / "context")
            if (refresh or reindex_only_changed)
            else {}
        )
        previous_files = {meta.path: meta for meta in existing.get("files", [])}
        changed_files: set[str] = set()
        deleted_files: set[str] = set()
        current_files: dict[str, FileMeta] = {}
        target_files: set[str] | None = None

        if reindex_only_changed:
            if not existing:
                raise RuntimeError(
                    "Reindex requires existing context. Run `midicoder index` first."
                )

            manual_path_inputs = normalize_changed_paths(changed_paths or [])
            if manual_path_inputs:
                # Explicit paths take precedence: do not use git delta.
                changed_files = expand_manual_changed_paths(
                    scanner=scanner,
                    manual_paths=manual_path_inputs,
                    previous_file_paths=set(previous_files.keys()),
                )
                deleted_files = set()
                logger.info(
                    "Reindex mode (manual paths): %d changed file(s), %d deleted file(s) [manual_inputs=%d]",
                    len(changed_files),
                    len(deleted_files),
                    len(manual_path_inputs),
                )
            else:
                previous_manifest = existing.get("manifest")
                previous_hash = None
                if isinstance(previous_manifest, dict):
                    previous_hash = previous_manifest.get("repo_hash")

                git_delta = get_git_file_deltas(root, previous_hash=previous_hash)
                if git_delta is None:
                    logger.warning(
                        "Git repository (.git) not found under %s. "
                        "Use `midicoder index reindex --path <path>` to specify files when working outside git.",
                        root,
                    )
                    logger.info(
                        "Skipping reindex because git change detection is unavailable."
                    )
                    return
                changed_files, deleted_files = git_delta
                logger.info(
                    "Reindex mode (git): %d changed file(s), %d deleted file(s)",
                    len(changed_files),
                    len(deleted_files),
                )

            if changed_files:
                scanner.scan_selected(changed_files, compute_hash=True)
            else:
                scanner.scan_selected(set(), compute_hash=True)

            if scanner.skipped_unindexed_files:
                logger.info(
                    "Files not indexed: %d — see manifest.json: %s",
                    len(scanner.skipped_unindexed_files),
                    context_root / ".midicoder" / "context" / "manifest.json",
                )

            # Preserve old indexed files, then update changed/deleted paths.
            current_files = dict(previous_files)

            # Normalize for case-insensitive matching on Windows
            changes_to_apply = {p.lower() for p in (changed_files | deleted_files)}

            # Remove existing entries that are being updated or were deleted
            to_remove = [p for p in current_files if p.lower() in changes_to_apply]
            for p in to_remove:
                current_files.pop(p, None)

            for meta in scanner.indexed_files:
                current_files[meta.path] = meta

            # Analyze only files that are present in selected scan.
            target_files = {meta.path for meta in scanner.indexed_files}
        else:
            logger.debug("Scanning project files...")
            # Always compute hash to have baseline for future refreshes
            scanner.scan(compute_hash=True)
            if scanner.skipped_unindexed_files:
                logger.info(
                    "Files not indexed: %d — see manifest.json: %s",
                    len(scanner.skipped_unindexed_files),
                    context_root / ".midicoder" / "context" / "manifest.json",
                )

            current_files = {meta.path: meta for meta in scanner.indexed_files}
            changed_files, deleted_files = diff_file_sets(
                previous_files,
                current_files,
                root=root,
                use_git=True,  # Enable git integration as per documentation
            )
            target_files = changed_files if refresh else None

        config_stack = read_config_stack(root)
        if config_stack:
            logger.debug(f"Found config stack: {config_stack}")

        logger.debug("Detecting tech stack...")
        detected_stack = detect_stack(scanner, config_stack)

        logger.debug("Extracting project profile...")
        if reindex_only_changed and "profile" in existing:
            profile = existing["profile"]
        else:
            profile = extract_project_profile(scanner, detected_stack, config_stack)

        logger.debug("Analyzing symbols...")
        symbols, symbol_errors = analyze_symbols(scanner, target_files=target_files)

        logger.debug("Extracting entrypoints...")
        entrypoints = extract_entrypoints(
            scanner, detected_stack, target_files=target_files
        )

        logger.debug("Extracting seams...")
        seams, seam_errors = extract_seams(scanner, target_files=target_files)

        logger.debug("Extracting exemplars...")
        exemplars = extract_exemplars(
            scanner, symbols, detected_stack, target_files=target_files
        )

        if (refresh or reindex_only_changed) and existing:
            symbols = merge_symbols(
                existing.get("symbols", []), symbols, changed_files, deleted_files
            )
            entrypoints = merge_entrypoints(
                existing.get("entrypoints", []),
                entrypoints,
                changed_files,
                deleted_files,
            )
            seams = merge_seams(
                existing.get("seams", []), seams, changed_files, deleted_files
            )
            exemplars = merge_exemplars(
                existing.get("exemplars", []), exemplars, changed_files, deleted_files
            )

        # Final deduplication pass before building manifest and logging
        # This ensures in-memory data, manifest, and logs all show unique items.
        symbols = _final_dedupe(
            symbols,
            lambda s: (
                s.file.lower().replace("\\", "/"),
                s.line,
                s.name.lower(),
                s.kind,
            ),
        )
        entrypoints = _final_dedupe(
            entrypoints, lambda e: (e.file.lower().replace("\\", "/"), e.line, e.kind)
        )
        seams = _final_dedupe(
            seams,
            lambda s: (
                s.file.lower().replace("\\", "/"),
                s.line,
                s.group_id.lower(),
                s.kind,
            ),
        )
        exemplars = _final_dedupe(
            exemplars,
            lambda e: (e.file.lower().replace("\\", "/"), e.line, e.kind, e.snippet),
        )

        logger.debug("Building index manifest...")
        if reindex_only_changed:
            manifest = build_incremental_manifest(
                scanner=scanner,
                profile=profile,
                symbols=symbols,
                entrypoints=entrypoints,
                seams=seams,
                exemplars=exemplars,
                files=list(current_files.values()),
                existing_manifest=existing.get("manifest"),
            )
        else:
            manifest = build_index_manifest(
                scanner, profile, symbols, entrypoints, seams, exemplars
            )

        # Collect errors for logging only (not persisted)
        errors = symbol_errors + seam_errors

        files_list = sorted(current_files.values(), key=lambda meta: meta.path)
        artifacts = ContextArtifacts(
            profile=profile,
            files=files_list,
            symbols=symbols,
            entrypoints=entrypoints,
            seams=seams,
            exemplars=exemplars,
            manifest=manifest,
            stats={},  # Stats now in manifest.output_stats
            errors=errors,
        )

        logger.debug("Writing context artifacts...")
        virtual_seams_count = write_context_artifacts(
            context_root, artifacts, repo_root=root
        )

        elapsed = time.time() - start_time
        logger.info(
            f"Context indexing complete in {elapsed:.2f}s: "
            f"{len(symbols)} symbols, {len(entrypoints)} entrypoints, "
            f"{len(seams)} seams, {virtual_seams_count} virtual seams, {len(exemplars)} exemplars"
        )

    except Exception as e:
        logger.error(f"Failed to build context: {e}", exc_info=True)
        raise


def write_context_artifacts(
    root: Path, artifacts: ContextArtifacts, repo_root: Path | None = None
) -> int:
    """Write all context artifacts to .midicoder/context/. Returns virtual seam count."""
    context_dir = root / ".midicoder" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)

    files_to_write = [
        ("manifest.json", artifacts.manifest.to_dict()),
        ("profile.json", artifacts.profile.to_dict()),
        ("symbols.json", [s.to_dict() for s in sort_symbols(artifacts.symbols)]),
        (
            "entrypoints.json",
            [e.to_dict() for e in sort_entrypoints(artifacts.entrypoints)],
        ),
        ("seams.json", [s.to_dict() for s in sort_seams(artifacts.seams)]),
        ("exemplars.json", [e.to_dict() for e in sort_exemplars(artifacts.exemplars)]),
    ]

    for filename, data in files_to_write:
        path = context_dir / filename
        try:
            write_json(path, data)
            logger.debug(f"Wrote {filename}")
        except Exception as e:
            logger.error(f"Failed to write {filename}: {e}")
            raise

    try:
        virtual_seams = write_virtual_seams(context_dir, repo_root=repo_root)
    except Exception as e:
        logger.error(f"Failed to write virtual_seams.json: {e}")
        raise

    return len(virtual_seams)


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )


def _final_dedupe(items: list[Any], key_func: Any) -> list[Any]:
    seen = set()
    result = []
    for item in items:
        key = key_func(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def load_existing_context(context_dir: Path) -> dict[str, object]:
    """Load existing context for incremental refresh."""
    existing: dict[str, object] = {"files": []}

    manifest_payload = read_json_data(context_dir / "manifest.json")
    if isinstance(manifest_payload, dict):
        existing["manifest"] = manifest_payload
        file_hashes = manifest_payload.get("file_hashes")
        if isinstance(file_hashes, dict):
            existing["files"] = [
                FileMeta(
                    path=str(path),
                    size=0,
                    mtime=0.0,
                    sha256=str(file_hash),
                    language="unknown",
                    kind="unknown",
                )
                for path, file_hash in file_hashes.items()
                if isinstance(path, str) and file_hash
            ]

    profile_payload = read_json_data(context_dir / "profile.json")
    if isinstance(profile_payload, dict):
        existing["profile"] = profile_from_dict(profile_payload)

    symbols_payload = read_json_data(context_dir / "symbols.json")
    if isinstance(symbols_payload, list):
        existing["symbols"] = [
            symbol_from_dict(item) for item in symbols_payload if isinstance(item, dict)
        ]

    entrypoints_payload = read_json_data(context_dir / "entrypoints.json")
    if isinstance(entrypoints_payload, list):
        existing["entrypoints"] = [
            entrypoint_from_dict(item)
            for item in entrypoints_payload
            if isinstance(item, dict)
        ]

    seams_payload = read_json_data(context_dir / "seams.json")
    if isinstance(seams_payload, list):
        existing["seams"] = [
            seam_from_dict(item) for item in seams_payload if isinstance(item, dict)
        ]

    exemplars_payload = read_json_data(context_dir / "exemplars.json")
    if isinstance(exemplars_payload, list):
        existing["exemplars"] = [
            exemplar_from_dict(item)
            for item in exemplars_payload
            if isinstance(item, dict)
        ]

    existing["errors"] = []
    return existing


def read_json_data(path: Path) -> object | None:
    """Load JSON data from file."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def normalize_changed_paths(paths: list[str]) -> set[str]:
    normalized: set[str] = set()
    for path in paths:
        for raw in str(path).split(","):
            value = raw.strip().replace("\\", "/")
            if not value:
                continue
            if value.startswith("./"):
                value = value[2:]
            normalized.add(value)
    return normalized


def expand_manual_changed_paths(
    scanner: ProjectScanner,
    manual_paths: set[str],
    previous_file_paths: set[str],
) -> set[str]:
    """
    Expand manual file/folder paths into concrete changed file paths.
    Includes previous indexed files under provided folders to handle deletions.
    """
    expanded_files = scanner.expand_selected_paths(manual_paths)
    expanded_with_previous = set(expanded_files)

    for raw_path in manual_paths:
        normalized = raw_path.replace("\\", "/").lstrip("./").rstrip("/")
        if not normalized:
            continue

        prefix = f"{normalized}/"
        for old_path in previous_file_paths:
            if old_path == normalized or old_path.startswith(prefix):
                expanded_with_previous.add(old_path)

    return expanded_with_previous


def get_git_file_deltas(
    root: Path, previous_hash: str | None = None
) -> tuple[set[str], set[str]] | None:
    """
    Parse `git status --porcelain` and optionally `git diff` from previous_hash
    into changed and deleted relative paths.
    Returns None when git is unavailable or root is not a git repository.
    """
    try:
        # Check if we are in a git repository
        subprocess.check_output(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=root,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        logger.debug(f"Not a git repository: {root}")
        return None

    try:
        prefix = (
            subprocess.check_output(
                ["git", "rev-parse", "--show-prefix"],
                cwd=root,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            .decode("utf-8", errors="ignore")
            .strip()
            .replace("\\", "/")
        )
        if prefix and not prefix.endswith("/"):
            prefix += "/"
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        prefix = ""

    changed_files: set[str] = set()
    deleted_files: set[str] = set()

    # 1. Get current working tree and index status
    try:
        status_output = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=root,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).decode("utf-8", errors="ignore")

        for line in status_output.splitlines():
            if len(line) < 4:
                continue
            status = line[:2]
            path_data = line[3:].strip()

            new_path = path_data
            old_path: str | None = None
            if " -> " in path_data:
                old_path, new_path = path_data.split(" -> ", 1)

            new_path = _normalize_git_status_path(new_path)
            old_path = _normalize_git_status_path(old_path) if old_path else None

            if prefix:
                if new_path.startswith(prefix):
                    new_path = new_path[len(prefix) :]
                if old_path and old_path.startswith(prefix):
                    old_path = old_path[len(prefix) :]

            x_status = status[0]
            y_status = status[1]
            if (x_status == "R" or y_status == "R") and old_path:
                deleted_files.add(old_path)
                changed_files.add(new_path)
            elif x_status == "D" or y_status == "D":
                if new_path:
                    deleted_files.add(new_path)
            elif new_path:
                changed_files.add(new_path)

    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logger.debug(f"Git status failed: {e}")

    # 2. Get changes between previous_hash and HEAD (e.g. after git pull)
    if previous_hash:
        clean_hash = previous_hash
        if clean_hash.startswith("sha1:"):
            clean_hash = clean_hash[5:]

        try:
            # Check if hash exists
            subprocess.check_output(
                ["git", "rev-parse", "--verify", clean_hash],
                cwd=root,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )

            diff_output = subprocess.check_output(
                ["git", "diff", "--name-status", clean_hash, "HEAD"],
                cwd=root,
                stderr=subprocess.DEVNULL,
                timeout=10,
            ).decode("utf-8", errors="ignore")

            for line in diff_output.splitlines():
                parts = line.split(None, 2)
                if not parts:
                    continue

                status = parts[0]
                new_path = parts[1].strip()
                old_path: str | None = parts[2].strip() if len(parts) > 2 else None

                new_path = _normalize_git_status_path(new_path)
                old_path = _normalize_git_status_path(old_path) if old_path else None

                if prefix:
                    if new_path.startswith(prefix):
                        new_path = new_path[len(prefix) :]
                    if old_path and old_path.startswith(prefix):
                        old_path = old_path[len(prefix) :]

                if status.startswith("R") and old_path:
                    deleted_files.add(old_path)
                    changed_files.add(new_path)
                elif status.startswith("D"):
                    deleted_files.add(new_path)
                else:
                    changed_files.add(new_path)

        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.debug(f"Git diff since {previous_hash} failed: {e}")

    logger.debug(
        "Git detected %d changed file(s), %d deleted file(s)",
        len(changed_files),
        len(deleted_files),
    )
    return changed_files, deleted_files


def _normalize_git_status_path(filepath: str | None) -> str:
    if not filepath:
        return ""
    value = filepath.strip()
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    return value.replace("\\", "/")


def get_git_changed_files(root: Path) -> set[str] | None:
    """Backward-compatible helper used by refresh diff logic."""
    deltas = get_git_file_deltas(root)
    if deltas is None:
        return None
    changed_files, _ = deltas
    return changed_files


def diff_file_sets(
    previous: dict[str, FileMeta],
    current: dict[str, FileMeta],
    root: Path | None = None,
    use_git: bool = True,
) -> tuple[set[str], set[str]]:
    """
    Detect changed and deleted files.

    Args:
        previous: Previously indexed files
        current: Currently scanned files
        root: Repository root (for git integration)
        use_git: Whether to use git status for change detection

    Returns:
        Tuple of (changed_files, deleted_files)
    """
    changed: set[str] = set()

    # Try git integration first if enabled
    git_changed = None
    if use_git and root:
        git_changed = get_git_changed_files(root)

    if git_changed is not None:
        # Use git status as primary source
        for path in git_changed:
            if path in current:
                changed.add(path)

        # Also check for new files not in git yet
        for path in current:
            if path not in previous:
                changed.add(path)

        logger.debug(f"Using git-based change detection: {len(changed)} files changed")
    else:
        # Fall back to hash comparison
        for path, meta in current.items():
            prior = previous.get(path)
            if not prior:
                changed.add(path)
                continue
            if file_meta_changed(prior, meta):
                changed.add(path)

        logger.debug(f"Using hash-based change detection: {len(changed)} files changed")

    deleted = set(previous) - set(current)
    logger.debug(f"Detected {len(deleted)} deleted files")

    return changed, deleted


def file_meta_changed(previous: FileMeta, current: FileMeta) -> bool:
    if previous.sha256 and current.sha256:
        return previous.sha256 != current.sha256
    return (previous.size, previous.mtime) != (current.size, current.mtime)


def merge_symbols(
    existing: list[Symbol],
    updated: list[Symbol],
    changed_files: set[str],
    deleted_files: set[str],
) -> list[Symbol]:
    # Use lowercase sets with forward slashes for robust matching
    changes_to_retained = {
        p.lower().replace("\\", "/") for p in (changed_files | deleted_files)
    }

    retained = [
        symbol
        for symbol in existing
        if symbol.file.lower().replace("\\", "/") not in changes_to_retained
    ]
    return retained + updated


def merge_entrypoints(
    existing: list[EntryPoint],
    updated: list[EntryPoint],
    changed_files: set[str],
    deleted_files: set[str],
) -> list[EntryPoint]:
    # Use lowercase sets with forward slashes for robust matching
    changes_to_retained = {
        p.lower().replace("\\", "/") for p in (changed_files | deleted_files)
    }

    retained = [
        entry
        for entry in existing
        if entry.file.lower().replace("\\", "/") not in changes_to_retained
    ]
    return retained + updated


def merge_seams(
    existing: list[Seam],
    updated: list[Seam],
    changed_files: set[str],
    deleted_files: set[str],
) -> list[Seam]:
    # Use lowercase sets with forward slashes for robust matching
    changes_to_retained = {
        p.lower().replace("\\", "/") for p in (changed_files | deleted_files)
    }

    retained = [
        seam
        for seam in existing
        if seam.file.lower().replace("\\", "/") not in changes_to_retained
    ]
    return retained + updated


def merge_exemplars(
    existing: list[Exemplar],
    updated: list[Exemplar],
    changed_files: set[str],
    deleted_files: set[str],
) -> list[Exemplar]:
    # Use lowercase sets with forward slashes for robust matching
    changes_to_retained = {
        p.lower().replace("\\", "/") for p in (changed_files | deleted_files)
    }

    retained = [
        exemplar
        for exemplar in existing
        if exemplar.file.lower().replace("\\", "/") not in changes_to_retained
    ]
    return retained + updated


def sort_symbols(symbols: list[Symbol]) -> list[Symbol]:
    return sorted(symbols, key=lambda s: (s.file, s.line, s.name, s.kind))


def sort_entrypoints(entrypoints: list[EntryPoint]) -> list[EntryPoint]:
    return sorted(entrypoints, key=lambda e: (e.file, e.line, e.kind))


def sort_seams(seams: list[Seam]) -> list[Seam]:
    return sorted(seams, key=lambda s: (s.file, s.line, s.group_id, s.kind))


def sort_exemplars(exemplars: list[Exemplar]) -> list[Exemplar]:
    return sorted(exemplars, key=lambda e: (e.file, e.line, e.kind, e.score))


def profile_from_dict(payload: dict[str, Any]) -> ProjectProfile:
    stack = payload.get("stack")
    conventions = payload.get("conventions")
    return ProjectProfile(
        root=".",
        language=str(payload.get("language", "unknown")),
        stack=list(stack) if isinstance(stack, list) else [],
        orm=str(payload.get("orm")) if payload.get("orm") is not None else None,
        di_style=(
            str(payload.get("di_style"))
            if payload.get("di_style") is not None
            else None
        ),
        error_handling=(
            str(payload.get("error_handling"))
            if payload.get("error_handling") is not None
            else None
        ),
        conventions=conventions if isinstance(conventions, dict) else {},
    )


def build_incremental_manifest(
    scanner: ProjectScanner,
    profile: ProjectProfile,
    symbols: list[Symbol],
    entrypoints: list[EntryPoint],
    seams: list[Seam],
    exemplars: list[Exemplar],
    files: list[FileMeta],
    existing_manifest: object | None,
) -> IndexManifest:
    file_hashes = {meta.path: meta.sha256 for meta in files if meta.sha256}
    previous_output_stats: dict[str, Any] = {}
    previous_project_summary: dict[str, Any] = {}
    if isinstance(existing_manifest, dict):
        if isinstance(existing_manifest.get("output_stats"), dict):
            previous_output_stats = dict(existing_manifest["output_stats"])
        if isinstance(existing_manifest.get("project_summary"), dict):
            previous_project_summary = dict(existing_manifest["project_summary"])

    output_stats: dict[str, object] = {
        "files_found": scanner.total_files_found,
        "files_indexed": scanner.total_files_indexed,
        "files_not_indexed": sorted(scanner.skipped_unindexed_files),
        "files_not_indexed_count": len(scanner.skipped_unindexed_files),
        "symbols_count": len(symbols),
        "entrypoints_count": len(entrypoints),
        "seams_count": len(seams),
        "exemplars_count": len(exemplars),
    }
    output_stats.update(
        {
            "last_reindex_scope": {
                "files_found": scanner.total_files_found,
                "files_indexed": scanner.total_files_indexed,
            }
        }
    )
    for key, value in previous_output_stats.items():
        if key not in output_stats:
            output_stats[key] = value

    project_summary: dict[str, object] = {
        "language": profile.language,
        "stack": profile.stack,
        "total_lines": previous_project_summary.get("total_lines", 0),
    }

    repo_hash = None
    try:
        output = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=scanner.root,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        git_hash = output.decode("utf-8", errors="ignore").strip()
        repo_hash = f"sha1:{git_hash}" if git_hash else None
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        if isinstance(existing_manifest, dict):
            old_repo_hash = existing_manifest.get("repo_hash")
            if isinstance(old_repo_hash, str):
                repo_hash = old_repo_hash

    return IndexManifest(
        indexed_at=datetime.now(timezone.utc).isoformat(),
        repo_hash=repo_hash,
        tool_version=TOOL_VERSION,
        file_count=len(files),
        ignored_patterns=scanner.ignored_patterns,
        file_hashes=file_hashes,
        output_stats=output_stats,
        project_summary=project_summary,
    )


def symbol_from_dict(payload: dict[str, Any]) -> Symbol:
    return Symbol(
        name=str(payload.get("name", "")),
        kind=str(payload.get("kind", "")),
        language=str(payload.get("language", "")),
        file=str(payload.get("file", "")),
        line=int(payload.get("line", 0)),
        scope=payload.get("scope"),
        signature=payload.get("signature"),
    )


def entrypoint_from_dict(payload: dict[str, Any]) -> EntryPoint:
    """Deserialize EntryPoint from dict."""
    details = payload.get("details")
    kind = payload.get("kind")
    if kind is None and isinstance(details, dict):
        kind = details.get("stack")

    return EntryPoint(
        kind=str(kind or payload.get("type", "")),
        file=str(payload.get("file", "")),
        line=int(payload.get("line", 0)),
        detail=str(payload.get("detail", payload.get("description", ""))),
    )


def seam_from_dict(payload: dict[str, Any]) -> Seam:
    """Deserialize Seam from dict."""
    raw_kind = payload.get("kind")
    if raw_kind in ("begin", "end"):
        kind = str(raw_kind)
    else:
        kind = "begin"

    paired = payload.get("paired")
    if paired is None:
        line_start = int(payload.get("line_start", 0))
        line_end = int(payload.get("line_end", 0))
        paired = bool(line_start and line_end and line_end >= line_start)

    return Seam(
        kind=kind,
        file=str(payload.get("file", "")),
        line=int(payload.get("line", payload.get("line_start", 0))),
        detail=str(payload.get("detail", payload.get("marker", ""))),
        group_id=str(payload.get("group_id", payload.get("marker", "default"))),
        paired=bool(paired),
    )


def exemplar_from_dict(payload: dict[str, Any]) -> Exemplar:
    return Exemplar(
        kind=str(payload.get("kind", "")),
        language=str(payload.get("language", "")),
        file=str(payload.get("file", "")),
        line=int(payload.get("line", 0)),
        snippet=str(payload.get("snippet", "")),
        score=float(payload.get("score", 0.5)),
        source_symbol=payload.get("source_symbol"),
    )
