"""Core data models for context indexing."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FileMeta:
    path: str
    size: int
    mtime: float
    sha256: str | None
    language: str
    kind: str


@dataclass(frozen=True)
class Symbol:
    name: str
    kind: str
    language: str
    file: str
    line: int
    scope: str | None = None
    signature: str | None = None
    
    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "kind": self.kind,
            "language": self.language,
            "file": self.file,
            "line": self.line,
            "scope": self.scope,
            "signature": self.signature,
        }


@dataclass(frozen=True)
class EntryPoint:
    kind: str
    file: str
    line: int
    detail: str
    
    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "file": self.file,
            "line": self.line,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class Seam:
    kind: str  # "begin" | "end"
    file: str
    line: int
    detail: str
    group_id: str
    paired: bool
    
    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "file": self.file,
            "line": self.line,
            "detail": self.detail,
            "group_id": self.group_id,
            "paired": self.paired,
        }


@dataclass(frozen=True)
class Exemplar:
    kind: str
    language: str
    file: str
    line: int
    snippet: str
    score: float
    source_symbol: str | None = None
    
    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "language": self.language,
            "file": self.file,
            "line": self.line,
            "snippet": self.snippet,
            "score": self.score,
            "source_symbol": self.source_symbol,
        }


@dataclass
class ProjectProfile:
    root: str
    language: str
    stack: list[str]
    orm: str | None = None
    di_style: str | None = None
    error_handling: str | None = None
    conventions: dict[str, object] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "language": self.language,
            "stack": self.stack,
            "conventions": self.conventions,
        }
        if self.orm:
            result["orm"] = self.orm
        if self.di_style:
            result["di_style"] = self.di_style
        if self.error_handling:
            result["error_handling"] = self.error_handling
        return result


@dataclass
class IndexManifest:
    indexed_at: str
    repo_hash: str | None
    tool_version: str
    file_count: int
    ignored_patterns: list[str]
    file_hashes: dict[str, str]
    output_stats: dict[str, object] | None = None
    project_summary: dict[str, object] | None = None
    
    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "indexed_at": self.indexed_at,
            "repo_hash": self.repo_hash,
            "tool_version": self.tool_version,
            "file_count": self.file_count,
            "ignored_patterns": self.ignored_patterns,
            "file_hashes": self.file_hashes,
        }
        if self.output_stats is not None:
            result["output_stats"] = self.output_stats
        if self.project_summary is not None:
            result["project_summary"] = self.project_summary
        return result


@dataclass(frozen=True)
class ErrorRecord:
    kind: str
    file: str | None
    detail: str
    
    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "file": self.file,
            "detail": self.detail,
        }


@dataclass
class ContextArtifacts:
    """Container for all context artifacts (in-memory only)."""
    profile: ProjectProfile
    files: list[FileMeta]
    symbols: list[Symbol]
    entrypoints: list[EntryPoint]
    seams: list[Seam]
    exemplars: list[Exemplar]
    manifest: IndexManifest
    stats: dict[str, object]
    errors: list[ErrorRecord]
