"""File system scanner with caching and filtering."""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .models import FileMeta

logger = logging.getLogger(__name__)

HARD_IGNORED_DIRS = {
    ".git",
    ".midicoder",
}

DEFAULT_IGNORED_PATTERNS = [
    ".git/**",
    ".midicoder/**",
    "node_modules/**",
    "dist/**",
    "build/**",
    ".venv/**",
    "venv/**",
    "__pycache__/**",
    "*.pyc",
    "*.pyo",
    "*.so",
    "*.dylib",
    "*.dll",
]

SENSITIVE_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_dsa",
    "id_ed25519",
    "id_ecdsa",
}

SENSITIVE_FILE_EXTS = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".crt",
    ".cer",
    ".der",
}

HASH_CHUNK_SIZE = 8192
MAX_BINARY_CHECK_SIZE = 2048

PYTHON_EXTS = {".py", ".pyi"}
JS_TS_EXTS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".mts", ".cts"}
CODE_EXTS = PYTHON_EXTS | JS_TS_EXTS

CONFIG_FILES = {
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "setup.cfg",
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "angular.json",
    "nest-cli.json",
    "tsconfig.json",
}

LANGUAGE_BY_EXT = {
    ".py": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
}


@dataclass(frozen=True)
class GitIgnoreRule:
    pattern: str
    negated: bool
    anchored: bool
    source: str


@dataclass(frozen=True)
class GitIgnoreFile:
    base_path: Path
    rules: list[GitIgnoreRule]
    raw_patterns: list[str]


class GitIgnoreMatcher:
    def __init__(self, root: Path, gitignore_files: list[GitIgnoreFile]) -> None:
        self.root = root
        self.gitignore_files = gitignore_files
        self._cache: dict[str, bool] = {}  # Cache results to avoid redundant checks

    def is_ignored(self, path: Path, is_dir: bool) -> bool:
        """Check if path is ignored by gitignore rules.

        Results are cached to avoid redundant pattern matching.
        """
        # Create cache key
        cache_key = f"{path}:{is_dir}"

        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Compute result
        result = self._check_ignored_impl(path, is_dir)

        # Cache it
        self._cache[cache_key] = result
        return result

    def _check_ignored_impl(self, path: Path, is_dir: bool) -> bool:
        """Implementation of gitignore checking (original logic)."""
        relative = normalize_path(path.relative_to(self.root))
        ignored = False

        for gitignore in self.gitignore_files:
            base_rel = normalize_path(gitignore.base_path.relative_to(self.root))
            if base_rel:
                prefix = f"{base_rel}/"
                if not relative.startswith(prefix) and relative != base_rel:
                    continue
                rel_to_base = (
                    relative[len(prefix) :] if relative.startswith(prefix) else ""
                )
            else:
                rel_to_base = relative

            for rule in gitignore.rules:
                if matches_gitignore_rule(rel_to_base, rule, is_dir):
                    ignored = not rule.negated

        return ignored


class FileCache:
    def __init__(self) -> None:
        self._content_cache: dict[str, str] = {}
        self._content_bytes_cache: dict[str, bytes] = {}  # Cache raw bytes for hashing
        self._stat_cache: dict[str, tuple[int, float]] = {}

    def get_content(self, path: Path) -> str | None:
        key = str(path)
        if key in self._content_cache:
            return self._content_cache[key]

        content = safe_read_text(path)
        if content is not None:
            self._content_cache[key] = content
        return content

    def get_content_bytes(self, path: Path) -> bytes | None:
        """Get raw bytes content (useful for hashing)."""
        key = str(path)
        if key in self._content_bytes_cache:
            return self._content_bytes_cache[key]

        try:
            with path.open("rb") as handle:
                content_bytes = handle.read()

            self._content_bytes_cache[key] = content_bytes
            return content_bytes
        except OSError:
            return None

    def get_stat(self, path: Path) -> tuple[int, float] | None:
        key = str(path)
        if key in self._stat_cache:
            return self._stat_cache[key]

        try:
            stat = path.stat()
            result = (stat.st_size, stat.st_mtime)
            self._stat_cache[key] = result
            return result
        except OSError:
            return None

    def clear(self) -> None:
        self._content_cache.clear()
        self._content_bytes_cache.clear()
        self._stat_cache.clear()


class ProjectScanner:
    def __init__(
        self,
        root: Path,
        ignore_matcher: GitIgnoreMatcher,
        ignored_patterns: list[str],
        file_cache: FileCache | None = None,
    ) -> None:
        self.root = root.resolve()
        self.ignore_matcher = ignore_matcher
        self.ignored_patterns = ignored_patterns
        self.cache = file_cache or FileCache()

        self.python_files: list[Path] = []
        self.js_ts_files: list[Path] = []
        self.config_files: list[Path] = []
        self.all_code_files: list[Path] = []

        self.indexed_files: list[FileMeta] = []
        self.total_files_found: int = 0
        self.total_files_indexed: int = 0
        self.skipped_sensitive_files: list[str] = []
        self.skipped_unindexed_files: list[str] = []

    def scan(self, compute_hash: bool = False) -> None:
        """Scan project files and build index.

        Args:
            compute_hash: If True, compute SHA256 hash for each file.
                         Only needed for refresh mode to detect changes.
                         Default: False (much faster)
        """
        total_files = 0

        for path in self._walk_files():
            total_files += 1
            self._scan_candidate(path, compute_hash=compute_hash)

        self.total_files_found = total_files
        self.total_files_indexed = len(self.indexed_files)
        self._sort_indexes()
        hash_mode = "with hashes" if compute_hash else "without hashes"
        logger.info(
            f"Scan complete ({hash_mode}): {self.total_files_indexed}/{self.total_files_found} files indexed"
        )

    def scan_selected(
        self, relative_paths: set[str], compute_hash: bool = False
    ) -> None:
        """Scan only explicitly selected relative paths."""
        total_files = 0

        for relative_path in sorted(self.expand_selected_paths(relative_paths)):
            path = self.root / Path(relative_path)
            total_files += 1
            self._scan_candidate(path, compute_hash=compute_hash)

        self.total_files_found = total_files
        self.total_files_indexed = len(self.indexed_files)
        self._sort_indexes()
        hash_mode = "with hashes" if compute_hash else "without hashes"
        logger.info(
            f"Selected scan complete ({hash_mode}): {self.total_files_indexed}/{self.total_files_found} files indexed"
        )

    def expand_selected_paths(self, relative_paths: set[str]) -> set[str]:
        """Expand a set of file/folder relative paths into concrete file paths."""
        selected_files: set[str] = set()

        for relative_path in sorted(relative_paths):
            normalized = relative_path.replace("\\", "/").lstrip("./")
            if not normalized:
                continue

            path = (self.root / Path(normalized)).resolve()
            try:
                path.relative_to(self.root)
            except ValueError:
                continue

            if not path.exists():
                continue

            if path.is_file():
                if not self.ignore_matcher.is_ignored(path, is_dir=False):
                    selected_files.add(normalize_path(path.relative_to(self.root)))
                continue

            if path.is_dir():
                selected_files.update(self._walk_selected_dir(path))

        return selected_files

    def _walk_files(self) -> Iterator[Path]:
        """Walk through files with early directory filtering.

        Optimized to skip ignored directories early, avoiding
        unnecessary traversal and gitignore checks.
        Follows symlinked directories while preventing cycles.
        """
        seen_dirs: set[Path] = set()

        for dirpath, dirnames, filenames in os.walk(self.root, followlinks=True):
            current_dir = Path(dirpath)
            try:
                resolved_dir = current_dir.resolve()
            except OSError:
                resolved_dir = current_dir
            if resolved_dir in seen_dirs:
                dirnames.clear()
                continue
            seen_dirs.add(resolved_dir)

            # Early exit if current directory is ignored (except root)
            if current_dir != self.root:
                if self.ignore_matcher.is_ignored(current_dir, is_dir=True):
                    dirnames.clear()  # Stop os.walk from descending
                    continue

            # Filter subdirectories before os.walk descends into them
            filtered_dirs = []
            for dirname in dirnames:
                # Skip hard-ignored directories
                if dirname in HARD_IGNORED_DIRS:
                    continue

                # Check gitignore for this directory
                subdir = current_dir / dirname
                try:
                    resolved_subdir = subdir.resolve()
                except OSError:
                    resolved_subdir = subdir
                if resolved_subdir in seen_dirs:
                    continue
                if not self.ignore_matcher.is_ignored(subdir, is_dir=True):
                    filtered_dirs.append(dirname)

            # Update dirnames in-place to control os.walk traversal
            dirnames[:] = filtered_dirs

            # Yield files (still check individually for file-specific rules)
            for filename in filenames:
                file_path = current_dir / filename
                # Only yield if not ignored (will be checked again in scan())
                if not self.ignore_matcher.is_ignored(file_path, is_dir=False):
                    yield file_path

    def _walk_selected_dir(self, directory: Path) -> set[str]:
        selected: set[str] = set()
        for dirpath, dirnames, filenames in os.walk(directory, followlinks=True):
            current_dir = Path(dirpath)
            if self.ignore_matcher.is_ignored(current_dir, is_dir=True):
                dirnames.clear()
                continue

            filtered_dirs: list[str] = []
            for dirname in dirnames:
                if dirname in HARD_IGNORED_DIRS:
                    continue
                subdir = current_dir / dirname
                if self.ignore_matcher.is_ignored(subdir, is_dir=True):
                    continue
                filtered_dirs.append(dirname)
            dirnames[:] = filtered_dirs

            for filename in filenames:
                file_path = current_dir / filename
                if self.ignore_matcher.is_ignored(file_path, is_dir=False):
                    continue
                try:
                    selected.add(normalize_path(file_path.relative_to(self.root)))
                except ValueError:
                    continue
        return selected

    def _scan_candidate(self, path: Path, compute_hash: bool) -> None:
        relative_path = normalize_path(path.relative_to(self.root))
        if is_sensitive_file(path):
            self.skipped_sensitive_files.append(relative_path)
            self.skipped_unindexed_files.append(relative_path)
            return

        stat_info = self.cache.get_stat(path)
        if stat_info is None:
            return

        size, mtime = stat_info
        suffix = path.suffix.lower()
        language = LANGUAGE_BY_EXT.get(suffix, "unknown")

        if suffix in PYTHON_EXTS:
            self.python_files.append(path)
            self.all_code_files.append(path)
        elif suffix in JS_TS_EXTS:
            self.js_ts_files.append(path)
            self.all_code_files.append(path)
        elif suffix in CODE_EXTS:
            self.all_code_files.append(path)

        if path.name in CONFIG_FILES:
            self.config_files.append(path)

        if suffix in CODE_EXTS or path.name in CONFIG_FILES:
            kind = "config" if path.name in CONFIG_FILES else "code"
            if path.name in CONFIG_FILES:
                language = "config"
            meta = build_file_meta(
                self.root,
                path,
                size,
                mtime,
                language,
                kind,
                compute_hash=compute_hash,
                file_cache=self.cache,
            )
            if meta:
                self.indexed_files.append(meta)
            else:
                self.skipped_unindexed_files.append(relative_path)
            return

        self.skipped_unindexed_files.append(relative_path)

    def get_content(self, path: Path) -> str | None:
        return self.cache.get_content(path)

    @property
    def has_python(self) -> bool:
        return len(self.python_files) > 0

    @property
    def has_javascript(self) -> bool:
        return len(self.js_ts_files) > 0

    @property
    def has_code(self) -> bool:
        return len(self.all_code_files) > 0

    def _sort_indexes(self) -> None:
        self.python_files.sort(key=lambda p: normalize_path(p.relative_to(self.root)))
        self.js_ts_files.sort(key=lambda p: normalize_path(p.relative_to(self.root)))
        self.config_files.sort(key=lambda p: normalize_path(p.relative_to(self.root)))
        self.all_code_files.sort(key=lambda p: normalize_path(p.relative_to(self.root)))
        self.indexed_files.sort(key=lambda meta: meta.path)


def normalize_path(path: Path) -> str:
    value = path.as_posix()
    if value == ".":
        return ""
    if value.startswith("./"):
        return value[2:]
    return value


def matches_gitignore_rule(
    relative_path: str, rule: GitIgnoreRule, is_dir: bool
) -> bool:
    pattern = rule.pattern

    if rule.anchored:
        return Path(relative_path).match(pattern)

    if "/" in pattern:
        return Path(relative_path).match(pattern)

    parts = Path(relative_path).parts
    if not parts:
        return False
    return any(Path(part).match(pattern) for part in parts)


def is_sensitive_file(path: Path) -> bool:
    name = path.name

    if name in SENSITIVE_FILE_NAMES:
        return True

    if name.startswith(".env"):
        return True

    if path.suffix.lower() in SENSITIVE_FILE_EXTS:
        return True

    return False


def safe_read_text(path: Path) -> str | None:
    """Read text file safely with binary/encoding checks.

    Optimized to read file only once instead of twice.
    Handles UTF-8 BOM, UTF-16/UTF-32 where possible.
    """
    try:
        with path.open("rb") as handle:
            content_bytes = handle.read()
        return _decode_text_bytes(content_bytes)
    except OSError:
        return None


def _decode_text_bytes(content_bytes: bytes) -> str | None:
    if not content_bytes:
        return ""

    # BOM-aware decoding first
    if content_bytes.startswith(b"\xff\xfe\x00\x00") or content_bytes.startswith(
        b"\x00\x00\xfe\xff"
    ):
        return content_bytes.decode("utf-32", errors="ignore")
    if content_bytes.startswith(b"\xff\xfe") or content_bytes.startswith(b"\xfe\xff"):
        return content_bytes.decode("utf-16", errors="ignore")

    check_size = min(len(content_bytes), MAX_BINARY_CHECK_SIZE)
    sample = content_bytes[:check_size]
    if 0 in sample:
        guessed = _guess_utf_encoding(sample)
        if guessed:
            decoded = content_bytes.decode(guessed, errors="ignore")
            if decoded:
                return decoded
        return None

    return content_bytes.decode("utf-8-sig", errors="ignore")


def _guess_utf_encoding(sample: bytes) -> str | None:
    if len(sample) < 4:
        return None

    # UTF-32 heuristic: three out of four bytes are often zero for ASCII text
    mod_counts = [0, 0, 0, 0]
    mod_nulls = [0, 0, 0, 0]
    for idx, value in enumerate(sample):
        slot = idx % 4
        mod_counts[slot] += 1
        if value == 0:
            mod_nulls[slot] += 1
    null_ratios = [
        (mod_nulls[i] / mod_counts[i]) if mod_counts[i] else 0.0 for i in range(4)
    ]
    low_idx = min(range(4), key=lambda i: null_ratios[i])
    if all(null_ratios[i] > 0.7 for i in range(4) if i != low_idx):
        if low_idx == 0:
            return "utf-32-le"
        if low_idx == 3:
            return "utf-32-be"

    # UTF-16 heuristic: one of even/odd bytes often zero for ASCII text
    even_bytes = sample[0::2]
    odd_bytes = sample[1::2]
    even_nulls = even_bytes.count(0)
    odd_nulls = odd_bytes.count(0)
    if even_bytes and odd_bytes:
        even_ratio = even_nulls / len(even_bytes)
        odd_ratio = odd_nulls / len(odd_bytes)
        if odd_ratio > 0.5 and odd_ratio > even_ratio * 1.5:
            return "utf-16-le"
        if even_ratio > 0.5 and even_ratio > odd_ratio * 1.5:
            return "utf-16-be"

    return None


def build_file_meta(
    root: Path,
    path: Path,
    size: int,
    mtime: float,
    language: str,
    kind: str,
    compute_hash: bool = False,
    file_cache: FileCache | None = None,
) -> FileMeta | None:
    """Build file metadata, optionally computing hash.

    Args:
        root: Project root path
        path: File path
        size: File size in bytes
        mtime: File modification time
        language: Detected language
        kind: File kind (code/config)
        compute_hash: If True, compute SHA256 hash (default: False)
        file_cache: Optional file cache to avoid re-reading files

    Returns:
        FileMeta object or None on error
    """
    try:
        sha256 = None
        if compute_hash:
            # Try to use cached content bytes to avoid re-reading
            content_bytes = None
            if file_cache:
                content_bytes = file_cache.get_content_bytes(path)
            sha256 = hash_file(path, content_bytes=content_bytes)

        return FileMeta(
            path=normalize_path(path.relative_to(root)),
            size=size,
            mtime=mtime,
            sha256=sha256,
            language=language,
            kind=kind,
        )
    except Exception:
        return None


def hash_file(path: Path, content_bytes: bytes | None = None) -> str | None:
    """Compute SHA256 hash of file.

    Args:
        path: Path to file
        content_bytes: Optional pre-read file content (optimization)

    Returns:
        SHA256 hex digest or None on error
    """
    try:
        hasher = hashlib.sha256()

        # If we already have content in memory, use it
        if content_bytes is not None:
            hasher.update(content_bytes)
        else:
            # Otherwise read from file
            with path.open("rb") as handle:
                while True:
                    chunk = handle.read(HASH_CHUNK_SIZE)
                    if not chunk:
                        break
                    hasher.update(chunk)

        return hasher.hexdigest()
    except OSError:
        return None


def load_gitignore_files(root: Path) -> tuple[list[GitIgnoreFile], list[str]]:
    gitignore_files: list[GitIgnoreFile] = []
    raw_patterns: list[str] = []

    default_rules: list[GitIgnoreRule] = []
    for pattern in DEFAULT_IGNORED_PATTERNS:
        rule = parse_gitignore_line(pattern, source="default")
        if rule:
            default_rules.append(rule)
            raw_patterns.append(pattern)

    gitignore_files.append(
        GitIgnoreFile(
            base_path=root, rules=default_rules, raw_patterns=list(raw_patterns)
        )
    )

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in HARD_IGNORED_DIRS)
        if ".gitignore" not in filenames:
            continue

        gitignore_path = Path(dirpath) / ".gitignore"
        patterns: list[str] = []
        rules: list[GitIgnoreRule] = []

        try:
            lines = gitignore_path.read_text(
                encoding="utf-8", errors="ignore"
            ).splitlines()
        except OSError:
            continue

        for line in lines:
            rule = parse_gitignore_line(line, source=str(gitignore_path))
            if rule:
                patterns.append(line.strip())
                rules.append(rule)

        if rules:
            gitignore_files.append(
                GitIgnoreFile(
                    base_path=Path(dirpath), rules=rules, raw_patterns=patterns
                )
            )
            raw_patterns.extend(patterns)

    gitignore_files.sort(
        key=lambda gf: (
            len(gf.base_path.relative_to(root).parts),
            normalize_path(gf.base_path.relative_to(root)),
        )
    )
    return gitignore_files, raw_patterns


def parse_gitignore_line(line: str, source: str) -> GitIgnoreRule | None:
    stripped = line.strip()
    if not stripped:
        return None
    if stripped.startswith("\\#"):
        stripped = stripped[1:]
    elif stripped.startswith("#"):
        return None

    negated = False
    if stripped.startswith("\\!"):
        stripped = stripped[1:]
    elif stripped.startswith("!"):
        negated = True
        stripped = stripped[1:].strip()

    anchored = stripped.startswith("/")
    if anchored:
        stripped = stripped.lstrip("/")

    if stripped.endswith("/"):
        stripped = stripped.rstrip("/") + "/**"

    if not stripped:
        return None

    return GitIgnoreRule(
        pattern=stripped, negated=negated, anchored=anchored, source=source
    )
