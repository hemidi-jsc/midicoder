"""Error codes for IR compiler."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# Schema errors (E1xx)
E101 = "MISSING_REQUIRED_FIELD"
E102 = "INVALID_FIELD_TYPE"
E103 = "EXTRA_FIELD_NOT_ALLOWED"
E104 = "INVALID_ENUM_VALUE"

# Lint errors (E2xx)
E201 = "DUPLICATE_ID"
E202 = "DUPLICATE_FIELD_NAME"
E203 = "INVALID_PRIMARY_KEY"
E204 = "INVALID_INDEX_FIELD"
E205 = "INVALID_CONSTRAINT_FIELD"
E206 = "INVALID_CATEGORY"
E207 = "INVALID_GUARD_ID"
E208 = "INVALID_EFFECT_ID"
E209 = "INVALID_STATE_REFERENCE"
E210 = "INVALID_TRANSITION_REFERENCE"
E211 = "INVALID_TENANT_SCOPE"
E212 = "INVALID_CONSTRAINT_TYPE"

# Cross-reference errors (E3xx)
E301 = "UNRESOLVED_ENTITY_REF"
E302 = "UNRESOLVED_COMMAND_REF"
E303 = "UNRESOLVED_ERROR_REF"
E304 = "UNRESOLVED_EVENT_REF"
E305 = "UNRESOLVED_WORKFLOW_REF"
E306 = "UNRESOLVED_QUERY_REF"
E307 = "INVALID_STATE_REF_IN_WORKFLOW"
E308 = "INVALID_TRANSITION_REF"
E309 = "UNRESOLVED_VALUE_OBJECT_REF"
E310 = "UNRESOLVED_ENUM_REF"
E311 = "UNRESOLVED_PROJECTION_REF"
E312 = "UNRESOLVED_ROLE_REF"
E313 = "UNRESOLVED_PERMISSION_REF"
E314 = "UNRESOLVED_POLICY_REF"
E315 = "UNRESOLVED_RULE_REF"
E316 = "UNRESOLVED_SCENARIO_REF"
E317 = "UNRESOLVED_FIELD_TYPE_REF"

# Intent errors (E32x)
E321 = "MISSING_INTENT_METADATA"

# Intent warnings/info (W/I3xx)
W302 = "LOW_INTENT_CONFIDENCE"
W303 = "INCONSISTENT_MODULES_IN_FILE"
W304 = "AMBIGUOUS_INTENT_MODULE"
I304 = "CROSS_MODULE_DEPENDENCY"
I305 = "ORPHAN_COMMAND"

# System errors (E9xx)
E901 = "FILE_NOT_FOUND"
E902 = "INVALID_YAML_SYNTAX"
E903 = "IO_ERROR"
E904 = "UNEXPECTED_EXCEPTION"


@dataclass
class CompilerError:
    """Represents a compilation error or warning."""

    stage: str  # "load", "schema", "lint", "cross_ref", "normalize", "build"
    severity: str  # "error" | "warning" | "info"
    code: str  # Error code (e.g., "E201")
    file: str  # Relative path to contract file
    line: int | None  # Line number if available
    path: str  # JSON path in file (e.g., "commands[0].fetches[1]")
    message: str  # Human-readable error message
    context: dict[str, Any]  # Additional context for debugging

    def __str__(self) -> str:
        """Format error for display."""
        location = f"{self.file}"
        if self.line is not None:
            location += f":{self.line}"
        if self.path:
            location += f" ({self.path})"

        if self.severity == "error":
            severity_marker = "ERR"
        elif self.severity == "info":
            severity_marker = "INF"
        else:
            severity_marker = "WRN"
        result = f"{severity_marker} {location}\n  [{self.code}] {self.message}"

        # Add suggestion if available in context
        if self.context.get("suggestion"):
            result += f"\n  Suggestion: {self.context['suggestion']}"

        return result


class ErrorReporter:
    """Collects and reports compilation errors, warnings, and info."""

    def __init__(self) -> None:
        self.errors: list[CompilerError] = []
        self.warnings: list[CompilerError] = []
        self.infos: list[CompilerError] = []

    def add_error(
        self,
        stage: str,
        code: str,
        file: str,
        message: str,
        line: int | None = None,
        path: str = "",
        context: dict[str, Any] | None = None,
        severity: str = "error",
    ) -> None:
        """Add an error or warning."""
        error = CompilerError(
            stage=stage,
            severity=severity,
            code=code,
            file=file,
            line=line,
            path=path,
            message=message,
            context=context or {},
        )

        if severity == "error":
            self.errors.append(error)
        elif severity == "info":
            self.infos.append(error)
        else:
            self.warnings.append(error)

    def add_exception(
        self,
        stage: str,
        file: str,
        exception: Exception,
        line: int | None = None,
    ) -> None:
        """Add an exception as an error."""
        self.add_error(
            stage=stage,
            code=E904,
            file=file,
            message=f"Unexpected error: {exception}",
            line=line,
            context={"exception_type": type(exception).__name__},
        )

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def format_report(
        self,
        show_warnings: bool = True,
        show_context: bool = True,
        contracts_root: str | None = None,
        show_infos: bool = True,
    ) -> str:
        """
        Format errors and warnings for console output.

        Args:
            show_warnings: Include warnings in output
            show_context: Show code context for errors with line numbers
            contracts_root: Root path for contract files (for context lookup)
        """
        lines: list[str] = []

        if self.errors:
            lines.append(f"Errors ({len(self.errors)})")
            lines.extend(self._format_group(self.errors, contracts_root, show_context))

        if show_warnings and self.warnings:
            if lines:
                lines.append("")
            lines.append(f"Warnings ({len(self.warnings)})")
            lines.extend(
                self._format_group(self.warnings, contracts_root, show_context)
            )

        if show_infos and self.infos:
            if lines:
                lines.append("")
            lines.append(f"Info ({len(self.infos)})")
            lines.extend(self._format_group(self.infos, contracts_root, show_context))

        if self.errors:
            lines.append(
                f"{len(self.errors)} error(s), {len(self.warnings)} warning(s), "
                f"{len(self.infos)} info(s)"
            )
        elif self.warnings or self.infos:
            lines.append(
                f"No errors, {len(self.warnings)} warning(s), {len(self.infos)} info(s)"
            )
        else:
            lines.append("No errors, warnings, or info")

        return "\n".join(lines)

    def _format_group(
        self,
        items: list[CompilerError],
        contracts_root: str | None,
        show_context: bool,
    ) -> list[str]:
        lines: list[str] = []
        by_file: dict[str, list[CompilerError]] = {}
        for item in items:
            by_file.setdefault(item.file, []).append(item)

        def sort_key(err: CompilerError) -> tuple[int, str, str]:
            line = err.line if err.line is not None else 1_000_000
            path = err.path or ""
            return (line, path, err.code)

        for file in sorted(by_file.keys()):
            group = sorted(by_file[file], key=sort_key)
            lines.append(f"{file} ({len(group)})")
            for idx, err in enumerate(group, start=1):
                location_bits: list[str] = []
                if err.path:
                    location_bits.append(err.path)
                if err.line is not None:
                    location_bits.append(f"line {err.line}")
                location = (
                    " @ ".join(location_bits) if location_bits else "location unknown"
                )

                lines.append(
                    f"  {idx:02d} {err.code} [{err.stage}] {location}: {err.message}"
                )

                suggestion = err.context.get("suggestion")
                if suggestion:
                    lines.append(f"     suggestion: {suggestion}")

                if show_context and err.line and contracts_root:
                    context_lines = self._format_code_context(
                        err,
                        contracts_root,
                        prefix="     ",
                    )
                    if context_lines:
                        lines.extend(context_lines)

            lines.append("")

        if lines and lines[-1] == "":
            lines.pop()
        return lines

    def _format_code_context(
        self,
        error: CompilerError,
        contracts_root: str,
        context_lines: int = 2,
        prefix: str = "  ",
    ) -> list[str]:
        """Format code context around error line."""
        try:
            from pathlib import Path

            file_path = Path(contracts_root) / error.file
            if not file_path.exists():
                return []

            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Calculate range
            start = max(0, error.line - context_lines - 1)
            end = min(len(lines), error.line + context_lines)

            # Format output
            result = [f"{prefix}context:"]
            for i in range(start, end):
                line_num = i + 1
                line_content = lines[i].rstrip()

                # Add arrow indicator for error line
                if line_num == error.line:
                    result.append(f"{prefix}{line_num:4d} | {line_content}  <- error")
                else:
                    result.append(f"{prefix}{line_num:4d} | {line_content}")

            return result

        except (FileNotFoundError, IOError, IndexError):
            return []

    def to_dict(self) -> dict[str, Any]:
        """Export errors and warnings for manifest.json."""
        return {
            "errors": [
                {
                    "stage": e.stage,
                    "code": e.code,
                    "file": e.file,
                    "line": e.line,
                    "path": e.path,
                    "message": e.message,
                    "context": e.context,
                }
                for e in self.errors
            ],
            "warnings": [
                {
                    "stage": w.stage,
                    "code": w.code,
                    "file": w.file,
                    "line": w.line,
                    "path": w.path,
                    "message": w.message,
                    "context": w.context,
                }
                for w in self.warnings
            ],
            "infos": [
                {
                    "stage": i.stage,
                    "code": i.code,
                    "file": i.file,
                    "line": i.line,
                    "path": i.path,
                    "message": i.message,
                    "context": i.context,
                }
                for i in self.infos
            ],
        }
