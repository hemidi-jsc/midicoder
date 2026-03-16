"""Data models for runtime testing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ErrorInfo:
    """Information about a runtime error."""
    
    type: str  # import_error, syntax_error, runtime_error, etc.
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    traceback: str = ""


@dataclass
class RuntimeTestResult:
    """Result of runtime test."""
    
    timestamp: str
    success: bool
    port: int
    errors: list[ErrorInfo] = field(default_factory=list)
    log_dir: str = ""
    debug_output: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "success": self.success,
            "port": self.port,
            "errors": [
                {
                    "type": e.type,
                    "message": e.message,
                    "file": e.file,
                    "line": e.line,
                    "traceback": e.traceback,
                }
                for e in self.errors
            ],
            "log_dir": self.log_dir,
            "total_errors": len(self.errors),
        }
