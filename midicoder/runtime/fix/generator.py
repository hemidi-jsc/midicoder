"""Generate patch plans to fix runtime errors."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from midicoder.commands.base import MidicoderPaths
from midicoder.config.manager import ConfigManager
from midicoder.llm.client import call_llm, load_llm_config

from .analyzer import ErrorAnalysis, analyze_error_logs
from .business_guard import validate_runtime_fix_operations
from .models import PatchPlanItem, RuntimeFixResult
from .prompter import build_fix_prompt


@dataclass
class FixConfig:
    """Configuration for runtime fix."""

    workspace_root: Path
    working_dir: Path
    version: str
    stack_hint: str = "generic"
    log_timestamp: Optional[str] = None
    dry_run: bool = False


class RuntimeFixGenerator:
    """Generate fixes for runtime errors using LLM."""

    def __init__(self, config: FixConfig):
        self.config = config
        self.paths = MidicoderPaths(root=config.workspace_root)
        self._files_with_errors: set[str] = set()
        self._detected_stack = config.stack_hint or "generic"
        self._import_pattern = re.compile(r"^(from\s+\S+\s+import\s+.+|import\s+.+)$")

    def generate(self) -> RuntimeFixResult:
        """Main fix generation pipeline."""
        log_timestamp = self.config.log_timestamp or self._find_latest_error_log()

        if not log_timestamp:
            return RuntimeFixResult(
                success=False,
                patch_plans=[],
                patches_dir="",
                errors=["No error logs found. Run 'midicoder runtime test' first."],
            )

        log_dir = self.config.workspace_root / ".midicoder" / "logs" / log_timestamp
        if not log_dir.exists():
            return RuntimeFixResult(
                success=False,
                patch_plans=[],
                patches_dir="",
                errors=[f"Log directory not found: {log_dir}"],
            )

        analysis = analyze_error_logs(log_dir, working_dir=self.config.working_dir)
        if not analysis.errors:
            return RuntimeFixResult(
                success=False,
                patch_plans=[],
                patches_dir="",
                errors=["No actionable errors found in logs."],
            )

        self._files_with_errors = {
            path
            for path in analysis.normalized_project_files
            if self._is_project_file(path)
        }
        if not self._files_with_errors:
            for category in analysis.errors:
                for file_path in category.file_context.keys():
                    if self._is_project_file(file_path):
                        self._files_with_errors.add(file_path)

        error_signature = self._compute_error_signature(analysis)
        if self._has_been_attempted(error_signature):
            return RuntimeFixResult(
                success=False,
                patch_plans=[],
                patches_dir="",
                errors=[
                    "This error has been attempted multiple times without success.",
                    "Possible causes:",
                    "1. The fix is being applied but not addressing the root cause",
                    "2. There's a structural issue that needs manual intervention",
                    "3. The error logs may not contain enough information",
                    "",
                    "Please review the error manually or run 'midicoder runtime test' to get fresh logs.",
                ],
            )

        project_context = self._load_project_context()
        business_context = self._load_business_context(analysis.runtime_keywords)
        runtime_context = self._build_runtime_context(
            analysis=analysis,
            project_context=project_context,
            business_context=business_context,
        )
        self._detected_stack = str(
            runtime_context.get("profile_summary", {}).get("stack")
            or self._detected_stack
        )

        prompt = build_fix_prompt(
            analysis=analysis,
            runtime_context=runtime_context,
            working_dir=self.config.working_dir,
        )

        try:
            llm_config = load_llm_config(self.paths, tier="high")
        except Exception as exc:
            return RuntimeFixResult(
                success=False,
                patch_plans=[],
                patches_dir="",
                errors=[f"Failed to load LLM config: {exc}"],
            )

        try:
            response = call_llm(
                llm_config,
                system=(
                    "You are an expert software engineer for multi-stack backend/frontend projects. "
                    "Generate patch-plan operations for runtime fixes while preserving business constraints from contracts and IR. "
                    "Return only valid JSON."
                ),
                context=prompt.context,
                prompt=prompt.user_prompt,
                temperature=0.1,
                max_tokens=8192,
            )
        except Exception as exc:
            return RuntimeFixResult(
                success=False,
                patch_plans=[],
                patches_dir="",
                errors=[f"LLM call failed: {exc}"],
            )

        operations, parse_errors = self._parse_llm_response(response.content)
        if not operations:
            error_msg = "LLM failed to generate valid operations."
            if parse_errors:
                error_msg += f" Errors: {'; '.join(parse_errors)}"
            return RuntimeFixResult(
                success=False,
                patch_plans=[],
                patches_dir="",
                errors=[error_msg],
            )

        guarded_operations, guard_issues = validate_runtime_fix_operations(
            operations,
            working_dir=self.config.working_dir,
            relevant_files=set(runtime_context.get("relevant_files", [])),
        )
        (
            guarded_operations,
            canonicalize_warnings,
        ) = self._canonicalize_runtime_operations(
            guarded_operations,
        )
        all_warnings = [*parse_errors, *guard_issues]
        all_warnings.extend(canonicalize_warnings)

        if not guarded_operations:
            return RuntimeFixResult(
                success=False,
                patch_plans=[],
                patches_dir="",
                errors=[
                    "All generated operations were rejected by runtime fix guardrails.",
                    *all_warnings,
                ],
            )

        fix_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        patches_dir = (
            self.config.workspace_root
            / ".midicoder"
            / "versions"
            / self.config.version
            / "patches"
            / "runtime-fix"
            / fix_timestamp
        )

        trace_payload = {
            "timestamp": fix_timestamp,
            "log_timestamp": log_timestamp,
            "runtime_keywords": analysis.runtime_keywords,
            "traceback_focus": analysis.traceback_focus,
            "selected_files": runtime_context.get("relevant_files", []),
            "selected_contracts": runtime_context.get("contracts_focus", []),
            "selected_ir": runtime_context.get("ir_focus", []),
            "warning_count": len(all_warnings),
            "warnings": all_warnings,
            "operation_count": len(guarded_operations),
            "stack": self._detected_stack,
        }

        if not self.config.dry_run:
            patches_dir.mkdir(parents=True, exist_ok=True)
            self._save_patch_plans(patches_dir, guarded_operations)
            self._record_attempt(error_signature, patches_dir)
            self._write_trace_artifact(trace_payload, fix_timestamp)

        patch_plan_summary = [
            PatchPlanItem(
                runtime_path=str(op.get("file_path", "unknown")),
                operation="upsert_region",
                ir_ref=str(op.get("ir_ref", "")),
                patches=[],
            )
            for op in guarded_operations
        ]

        return RuntimeFixResult(
            success=True,
            patch_plans=patch_plan_summary,
            patches_dir=str(patches_dir),
            errors=all_warnings,
        )

    def _compute_error_signature(self, analysis: ErrorAnalysis) -> str:
        """Compute a signature for error recurrence detection."""
        parts: list[str] = []
        for category in analysis.errors:
            parts.append(category.type)
            for error in category.errors[:3]:
                parts.append(str(error.get("message", ""))[:100])
        return hashlib.md5("|".join(parts).encode()).hexdigest()

    def _has_been_attempted(self, error_signature: str) -> bool:
        """Check if this error has been attempted repeatedly."""
        runtime_fix_dir = (
            self.config.workspace_root
            / ".midicoder"
            / "versions"
            / self.config.version
            / "patches"
            / "runtime-fix"
        )
        if not runtime_fix_dir.exists():
            return False

        attempts_file = runtime_fix_dir / ".attempts.json"
        if not attempts_file.exists():
            return False

        try:
            attempts = json.loads(attempts_file.read_text(encoding="utf-8"))
            return int(attempts.get(error_signature, 0)) >= 3
        except Exception:
            return False

    def _record_attempt(self, error_signature: str, patches_dir: Path) -> None:
        """Record a fix attempt."""
        runtime_fix_dir = patches_dir.parent
        attempts_file = runtime_fix_dir / ".attempts.json"
        try:
            attempts = {}
            if attempts_file.exists():
                attempts = json.loads(attempts_file.read_text(encoding="utf-8"))
            attempts[error_signature] = int(attempts.get(error_signature, 0)) + 1
            if len(attempts) > 10:
                attempts = dict(list(attempts.items())[-10:])
            attempts_file.write_text(json.dumps(attempts, indent=2), encoding="utf-8")
        except Exception:
            return

    def _find_latest_error_log(self) -> Optional[str]:
        """Find the most recent failed runtime log timestamp."""
        logs_dir = self.config.workspace_root / ".midicoder" / "logs"
        if not logs_dir.exists():
            return None

        for log_dir in sorted(logs_dir.iterdir(), reverse=True):
            if not log_dir.is_dir():
                continue
            summary_file = log_dir / "summary.json"
            if not summary_file.exists():
                continue
            try:
                summary = json.loads(summary_file.read_text(encoding="utf-8"))
                if not summary.get("success", True):
                    return log_dir.name
            except Exception:
                continue
        return None

    def _is_project_file(self, file_path: str) -> bool:
        normalized = file_path.replace("\\", "/").lower()
        skip_patterns = (
            "/venv/",
            "/.venv/",
            "/site-packages/",
            "/lib/python",
            "\\venv\\",
            "\\.venv\\",
            "\\site-packages\\",
        )
        if any(pattern in normalized for pattern in skip_patterns):
            return False

        # Relative paths are considered project files.
        if not (
            file_path.startswith("/") or (len(file_path) > 2 and file_path[1] == ":")
        ):
            return True

        try:
            Path(file_path).resolve().relative_to(self.config.working_dir.resolve())
            return True
        except Exception:
            return False

    def _load_project_context(self) -> dict[str, Any]:
        """Load context artifacts required for runtime fix retrieval."""
        context_dir = self.config.workspace_root / ".midicoder" / "context"
        context: dict[str, Any] = {}

        for key, filename in (
            ("symbols", "symbols.json"),
            ("profile", "profile.json"),
            ("seams", "seams.json"),
            ("entrypoints", "entrypoints.json"),
        ):
            path = context_dir / filename
            if not path.exists():
                continue
            try:
                context[key] = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                context[key] = [] if key != "profile" else {}

        if not isinstance(context.get("symbols"), list):
            context["symbols"] = []
        if not isinstance(context.get("seams"), list):
            context["seams"] = []
        if not isinstance(context.get("entrypoints"), list):
            context["entrypoints"] = []
        if not isinstance(context.get("profile"), dict):
            context["profile"] = {}
        return context

    def _load_business_context(self, runtime_keywords: list[str]) -> dict[str, Any]:
        """Load business artifacts and extract contract/IR focus snippets."""
        version_root = (
            self.config.workspace_root / ".midicoder" / "versions" / self.config.version
        )
        contracts_dir = version_root / "contracts"
        ir_path_candidates = [
            version_root / "irs" / "ir.json",
            version_root / "ir" / "ir.json",
        ]

        contracts_focus = self._extract_contract_focus(contracts_dir, runtime_keywords)

        ir_focus: list[str] = []
        for ir_path in ir_path_candidates:
            if not ir_path.exists():
                continue
            try:
                ir_payload = json.loads(ir_path.read_text(encoding="utf-8"))
                ir_focus = self._extract_ir_focus(ir_payload, runtime_keywords)
                if ir_focus:
                    break
            except Exception:
                continue

        return {
            "contracts_focus": contracts_focus,
            "ir_focus": ir_focus,
        }

    def _extract_contract_focus(
        self, contracts_dir: Path, runtime_keywords: list[str]
    ) -> list[str]:
        if not contracts_dir.exists():
            return []
        keywords = {k.lower() for k in runtime_keywords if k}
        if not keywords:
            keywords = {"error", "runtime"}

        scored: list[tuple[int, str]] = []
        for path in contracts_dir.rglob("*.y*ml"):
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                continue
            text_lc = text.lower()
            score = sum(1 for kw in keywords if kw in text_lc)
            if score <= 0:
                continue
            rel = path.relative_to(contracts_dir.parent).as_posix()
            snippet = self._first_matching_line(text, keywords)
            scored.append((score, f"{rel}: {snippet}"))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [item for _, item in scored[:20]]

    def _extract_ir_focus(
        self, ir_payload: Any, runtime_keywords: list[str]
    ) -> list[str]:
        keywords = {k.lower() for k in runtime_keywords if k}
        if not keywords:
            return []

        candidates: list[str] = []

        def walk(node: Any, path: str = "ir") -> None:
            if len(candidates) >= 400:
                return
            if isinstance(node, dict):
                marker_parts: list[str] = []
                for key in ("id", "name", "ref", "path", "method", "command", "entity"):
                    value = node.get(key)
                    if isinstance(value, str) and value.strip():
                        marker_parts.append(f"{key}={value.strip()}")
                if marker_parts:
                    candidates.append(f"{path}: " + ", ".join(marker_parts))
                for key, value in node.items():
                    walk(value, f"{path}.{key}")
            elif isinstance(node, list):
                for idx, item in enumerate(node[:100]):
                    walk(item, f"{path}[{idx}]")

        walk(ir_payload)

        scored: list[tuple[int, str]] = []
        for candidate in candidates:
            lc = candidate.lower()
            score = sum(1 for kw in keywords if kw in lc)
            if score > 0:
                scored.append((score, candidate))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [item for _, item in scored[:30]]

    def _first_matching_line(self, text: str, keywords: set[str]) -> str:
        for line in text.splitlines():
            cleaned = line.strip()
            if not cleaned:
                continue
            lc = cleaned.lower()
            if any(kw in lc for kw in keywords):
                return cleaned[:160]
        return text.splitlines()[0].strip()[:160] if text.splitlines() else "(empty)"

    def _build_runtime_context(
        self,
        *,
        analysis: ErrorAnalysis,
        project_context: dict[str, Any],
        business_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Build normalized runtime context schema for prompter."""
        profile_summary = self._build_profile_summary(
            project_context.get("profile", {})
        )
        symbols_by_file = self._map_symbols_by_file(
            project_context.get("symbols", []),
            runtime_keywords=analysis.runtime_keywords,
        )

        relevant_files = self._rank_relevant_files(
            analysis=analysis,
            symbols_by_file=symbols_by_file,
        )

        entrypoints = self._filter_context_lines(
            items=project_context.get("entrypoints", []),
            relevant_files=set(relevant_files),
            runtime_keywords=set(analysis.runtime_keywords),
            kind="entrypoint",
            limit=15,
        )
        seams = self._filter_context_lines(
            items=project_context.get("seams", []),
            relevant_files=set(relevant_files),
            runtime_keywords=set(analysis.runtime_keywords),
            kind="seam",
            limit=20,
        )

        return {
            "profile_summary": profile_summary,
            "traceback_focus": analysis.traceback_focus,
            "relevant_files": relevant_files,
            "symbols_by_file": symbols_by_file,
            "entrypoints": entrypoints,
            "seams": seams,
            "contracts_focus": business_context.get("contracts_focus", []),
            "ir_focus": business_context.get("ir_focus", []),
        }

    def _build_profile_summary(self, profile: dict[str, Any]) -> dict[str, str]:
        stack_value = profile.get("stack")
        framework_value = profile.get("framework")

        if isinstance(stack_value, list) and stack_value:
            stack = str(stack_value[0]).lower()
        elif isinstance(stack_value, str) and stack_value.strip():
            stack = stack_value.strip().lower()
        else:
            stack = (self.config.stack_hint or "generic").lower()

        framework = ""
        if isinstance(framework_value, str) and framework_value.strip():
            framework = framework_value.strip()
        elif isinstance(profile.get("frameworks"), list) and profile.get("frameworks"):
            framework = str(profile.get("frameworks")[0])
        else:
            framework = stack

        return {"stack": stack, "framework": framework}

    def _map_symbols_by_file(
        self,
        symbols: list[dict[str, Any]],
        *,
        runtime_keywords: list[str],
    ) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        keyword_set = {kw.lower() for kw in runtime_keywords if kw}

        for symbol in symbols:
            if not isinstance(symbol, dict):
                continue
            file_path = str(symbol.get("file") or "").replace("\\", "/")
            if not file_path or not self._is_project_file(file_path):
                continue

            name = str(symbol.get("name") or "")
            kind = str(symbol.get("kind") or "")
            line = symbol.get("line")
            label = f"{kind}:{name}@{line}" if line else f"{kind}:{name}"

            if keyword_set:
                searchable = f"{file_path} {name} {kind}".lower()
                if not any(kw in searchable for kw in keyword_set):
                    continue

            out.setdefault(file_path, [])
            if label not in out[file_path]:
                out[file_path].append(label)

        return out

    def _rank_relevant_files(
        self,
        *,
        analysis: ErrorAnalysis,
        symbols_by_file: dict[str, list[str]],
        limit: int = 15,
    ) -> list[str]:
        scores: dict[str, int] = {}

        for file_path in self._files_with_errors:
            scores[file_path] = scores.get(file_path, 0) + 10

        for item in analysis.traceback_focus:
            file_path = str(item.get("file") or "")
            if not file_path or not self._is_project_file(file_path):
                continue
            scores[file_path] = scores.get(file_path, 0) + 7

        for file_path, symbols in symbols_by_file.items():
            if not self._is_project_file(file_path):
                continue
            scores[file_path] = scores.get(file_path, 0) + min(5, len(symbols))

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return [file_path for file_path, _ in ranked[:limit]]

    def _filter_context_lines(
        self,
        *,
        items: list[dict[str, Any]],
        relevant_files: set[str],
        runtime_keywords: set[str],
        kind: str,
        limit: int,
    ) -> list[str]:
        lines: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            file_path = str(item.get("file") or "").replace("\\", "/")
            if file_path and relevant_files and file_path not in relevant_files:
                continue

            text = json.dumps(item, ensure_ascii=False)
            text_lc = text.lower()
            if runtime_keywords and not any(kw in text_lc for kw in runtime_keywords):
                continue

            preview = text.replace("\n", " ").strip()
            if len(preview) > 200:
                preview = preview[:200] + "..."
            lines.append(f"[{kind}] {preview}")
            if len(lines) >= limit:
                break
        return lines

    def _parse_llm_response(
        self, content: str
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Parse LLM response into operations."""
        errors: list[str] = []
        try:
            json_str = content.strip()
            if "```json" in json_str:
                start = json_str.find("```json") + 7
                end = json_str.find("```", start)
                if end > start:
                    json_str = json_str[start:end].strip()
            elif "```" in json_str:
                start = json_str.find("```") + 3
                end = json_str.find("```", start)
                if end > start:
                    json_str = json_str[start:end].strip()

            data = json.loads(json_str.strip())
            if isinstance(data, dict) and "operations" in data:
                operations = data["operations"]
            elif isinstance(data, list):
                operations = data
            else:
                errors.append(
                    "Unexpected JSON structure. Expected {'operations': [...]}."
                )
                return [], errors

            if not isinstance(operations, list):
                errors.append(f"'operations' must be an array, got {type(operations)}")
                return [], errors

            valid_operations: list[dict[str, Any]] = []
            for i, op in enumerate(operations):
                if not isinstance(op, dict):
                    errors.append(f"Operation {i} is not a dict: {type(op)}")
                    continue
                if op.get("operation_type") != "upsert_region":
                    errors.append(
                        f"Operation {i}: operation_type must be 'upsert_region', got {op.get('operation_type')}"
                    )
                    continue
                if not op.get("ir_ref"):
                    errors.append(f"Operation {i}: missing ir_ref")
                    continue
                if not op.get("region_start") or not op.get("region_end"):
                    errors.append(f"Operation {i}: missing region_start or region_end")
                    continue
                if not op.get("file_path"):
                    errors.append(
                        f"Operation {i} (ir_ref={op.get('ir_ref')}): missing required field 'file_path'"
                    )
                    continue
                merge_mode = op.get("merge_mode", "patch")
                if merge_mode not in {"patch", "create", "append"}:
                    errors.append(
                        f"Operation {i}: invalid merge_mode '{merge_mode}'. Must be 'patch', 'create', or 'append'"
                    )
                    continue
                valid_operations.append(op)

            return valid_operations, errors

        except json.JSONDecodeError as exc:
            return [], [f"JSON parsing failed: {exc}"]
        except Exception as exc:
            return [], [f"Unexpected error parsing response: {exc}"]

    def _canonicalize_runtime_operations(
        self,
        operations: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """
        Canonicalize LLM operations to follow code-gen/apply stable patterns:
        - stable ir_ref per file/topic (prevents region explosion across loops),
        - extract top-level imports from region_content into imports[],
        - ensure region markers match canonical ir_ref.
        """
        warnings: list[str] = []
        by_file: dict[str, list[dict[str, Any]]] = {}
        for op in operations:
            file_path = (
                str(op.get("file_path") or "").replace("\\", "/").lstrip("/").strip()
            )
            if not file_path:
                warnings.append(
                    f"Skipping operation without file_path (ir_ref={op.get('ir_ref', '?')})"
                )
                continue
            by_file.setdefault(file_path, []).append(op)

        canonical_ops: list[dict[str, Any]] = []
        for file_path, file_ops in by_file.items():
            merged_by_ref: dict[str, dict[str, Any]] = {}
            for op in file_ops:
                raw_ir_ref = str(op.get("ir_ref") or "").strip()
                topic = self._extract_ir_topic(raw_ir_ref)
                stable_ir_ref = self._build_stable_runtime_ir_ref(
                    file_path=file_path,
                    topic=topic,
                )

                imports_field = op.get("imports")
                imports_from_field = (
                    [
                        str(x).strip()
                        for x in imports_field
                        if isinstance(x, str) and str(x).strip()
                    ]
                    if isinstance(imports_field, list)
                    else []
                )

                region_content = (
                    str(op.get("region_content") or "").replace("\r\n", "\n").strip()
                )
                extracted_imports, cleaned_region = self._split_imports_from_region(
                    region_content
                )
                all_imports = self._dedupe_preserve_order(
                    imports_from_field + extracted_imports
                )

                canonical = dict(op)
                canonical["file_path"] = file_path
                canonical["ir_ref"] = stable_ir_ref
                canonical["region_start"] = f"# region {stable_ir_ref}"
                canonical["region_end"] = f"# endregion {stable_ir_ref}"
                canonical["imports"] = all_imports
                canonical["region_content"] = cleaned_region

                previous = merged_by_ref.get(stable_ir_ref)
                if previous is None:
                    merged_by_ref[stable_ir_ref] = canonical
                    continue

                # Merge behavior mirrors code-gen upsert-by-ir_ref: combine imports + append region if distinct.
                merged = dict(previous)
                merged["imports"] = self._dedupe_preserve_order(
                    list(previous.get("imports") or [])
                    + list(canonical.get("imports") or [])
                )
                old_region = str(previous.get("region_content") or "").strip()
                new_region = str(canonical.get("region_content") or "").strip()
                if (
                    old_region
                    and new_region
                    and old_region != new_region
                    and old_region not in new_region
                ):
                    merged["region_content"] = f"{old_region}\n\n{new_region}"
                else:
                    merged["region_content"] = new_region or old_region
                merged_by_ref[stable_ir_ref] = merged

            canonical_ops.extend(merged_by_ref.values())

        return canonical_ops, warnings

    def _extract_ir_topic(self, ir_ref: str) -> str:
        tokens = [tok for tok in ir_ref.split(":") if tok.strip()]
        if len(tokens) >= 2 and tokens[0] == "runtime_fix":
            return tokens[1]
        if len(tokens) >= 2:
            return tokens[0]
        if tokens:
            return tokens[0]
        return "fix"

    def _build_stable_runtime_ir_ref(
        self,
        *,
        file_path: str,
        topic: str,
    ) -> str:
        slug = file_path.replace("/", "_").replace("\\", "_").replace(".", "_")
        safe_topic = re.sub(r"[^a-zA-Z0-9_]+", "_", topic or "fix").strip("_") or "fix"
        return f"runtime_fix:{safe_topic}:{slug}"

    def _split_imports_from_region(self, region_content: str) -> tuple[list[str], str]:
        imports: list[str] = []
        body_lines: list[str] = []
        for line in region_content.split("\n"):
            stripped = line.strip()
            if self._import_pattern.match(stripped):
                imports.append(stripped)
                continue
            body_lines.append(line.rstrip())

        cleaned = "\n".join(body_lines).strip()
        if not cleaned:
            cleaned = "pass"
        return imports, cleaned

    def _dedupe_preserve_order(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for raw in values:
            value = str(raw).strip()
            if not value or value in seen:
                continue
            seen.add(value)
            out.append(value)
        return out

    def _save_patch_plans(
        self, patches_dir: Path, operations: list[dict[str, Any]]
    ) -> None:
        """Save operations as patch plans (code-gen compatible format)."""
        file_operations: dict[str, list[dict[str, Any]]] = {}

        for op in operations:
            file_path = str(op.get("file_path") or "")
            if not file_path:
                if len(self._files_with_errors) == 1:
                    file_path = next(iter(self._files_with_errors))
                else:
                    continue
            file_path = file_path.lstrip("/\\")
            file_operations.setdefault(file_path, []).append(op)

        patch_plan_targets: list[dict[str, Any]] = []

        for runtime_path, ops in file_operations.items():
            safe_path = runtime_path.replace("/", ".").replace("\\", ".")
            filename = f"{safe_path}.patch-plan.json"
            patch_file = patches_dir / filename

            patch_data = {
                "runtime_path": runtime_path,
                "operations": ops,
                "schema_version": "2.0.0",
                "stack": self._detected_stack,
                "version": self.config.version,
            }
            patch_file.write_text(json.dumps(patch_data, indent=2), encoding="utf-8")

            patch_plan_targets.append(
                {
                    "runtime_path": runtime_path,
                    "patch_plan_file": filename,
                    "operation_count": len(ops),
                    "ir_refs": [str(op.get("ir_ref", "")) for op in ops],
                }
            )

        index = {
            "version": self.config.version,
            "schema_version": "3.0.0",
            "stack": self._detected_stack,
            "patch_plan_targets": patch_plan_targets,
            "runtime_enabled": False,
            "generated_patch_plans": [
                target["patch_plan_file"] for target in patch_plan_targets
            ],
            "generated_runtime_files": [],
        }
        (patches_dir / "index.json").write_text(
            json.dumps(index, indent=2), encoding="utf-8"
        )

    def _write_trace_artifact(self, payload: dict[str, Any], timestamp: str) -> None:
        run_dir = (
            self.config.workspace_root
            / ".midicoder"
            / "runs"
            / "runtime_fix"
            / timestamp
        )
        run_dir.mkdir(parents=True, exist_ok=True)
        trace_file = run_dir / "context_trace.json"
        trace_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )


def generate_runtime_fixes(
    workspace_root: Path,
    log_timestamp: Optional[str] = None,
    dry_run: bool = False,
) -> RuntimeFixResult:
    """Generate runtime fixes with configuration."""
    paths = MidicoderPaths(root=workspace_root)
    config_mgr = ConfigManager(paths)
    config = config_mgr.load()

    working_dir_str = config.get("working_dir", ".")
    working_dir = Path(working_dir_str)
    if not working_dir.is_absolute():
        working_dir = (workspace_root / working_dir).resolve()

    state_file = workspace_root / ".midicoder" / "state.json"
    if not state_file.exists():
        return RuntimeFixResult(
            success=False,
            patch_plans=[],
            patches_dir="",
            errors=["No version found. Run 'midicoder version create' first."],
        )

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        version = state.get("current_version", "0.1.0")
    except Exception as exc:
        return RuntimeFixResult(
            success=False,
            patch_plans=[],
            patches_dir="",
            errors=[f"Failed to read state.json: {exc}"],
        )

    stack_value = config.get("stack", "generic")
    if isinstance(stack_value, list):
        stack_hint = str(stack_value[0]) if stack_value else "generic"
    else:
        stack_hint = str(stack_value or "generic")

    fix_config = FixConfig(
        workspace_root=workspace_root,
        working_dir=working_dir,
        version=version,
        stack_hint=stack_hint.lower(),
        log_timestamp=log_timestamp,
        dry_run=dry_run,
    )

    generator = RuntimeFixGenerator(fix_config)
    return generator.generate()
