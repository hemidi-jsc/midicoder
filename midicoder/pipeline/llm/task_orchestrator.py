"""
Task-Based LLM Orchestrator for Contract Generation.

Each task is a self-contained LLM call with its own fresh conversation.
Task results are summarized and passed to the next task's prompt — not accumulated in conversation.

This replaces the accumulating-conversation approach in call_llm_with_tools_stream
for contract generation specifically. The original client.py functions remain
untouched for use by brief analysis and other callers.

Architecture:
  Orchestrator (contract.py) defines tasks →
  TaskOrchestrator executes each task via call_llm_task →
  call_llm_task uses call_llm_with_tools_stream internally (single-shot or single-tool-loop) →
  Results are yielded as SSE events
"""

from __future__ import annotations

import json
import time
from typing import Any, AsyncIterator, Callable, Optional

from midicoder.pipeline.llm.client import (
    LlmConfig,
    call_llm_with_tools_stream,
    LlmStreamChunkWithTools,
)

logger = __import__("logging").getLogger(__name__)


# ============================================================================
# Task Definition
# ============================================================================

class TaskDefinition:
    """
    A self-contained LLM task.

    Each task has:
    - id: unique identifier (e.g. "learn_schema", "draft_yaml")
    - system: task-specific system prompt
    - user: task-specific user message
    - tools: list of tool definitions (can be empty — LLM just outputs text)
    - allow_tool_loop: if True, allows LLM to call tools in a loop within this task
    """

    def __init__(
        self,
        task_id: str,
        system: str,
        user: str,
        tools: Optional[list[dict]] = None,
        allow_tool_loop: bool = False,
    ):
        self.task_id = task_id
        self.system = system
        self.user = user
        self.tools = tools or []
        self.allow_tool_loop = allow_tool_loop


# ============================================================================
# call_llm_task — Single-task execution
# ============================================================================

async def call_llm_task(
    config: LlmConfig,
    task: TaskDefinition,
    tool_executor: Callable,
) -> AsyncIterator[LlmStreamChunkWithTools]:
    """
    Execute a single self-contained LLM task.

    - Creates a fresh conversation: [system] + [user]
    - If task has tools, allows the LLM to call them (with optional loop)
    - If task has NO tools, the LLM just outputs text (no function calling)

    The key difference from call_llm_with_tools_stream:
    - NO conversation accumulation across tasks
    - Each task starts fresh
    - When allow_tool_loop=False: only ONE round of tool calls, then text output
    - When allow_tool_loop=True: allows tool call loop within this task (for validate+fix)

    Args:
        config: LLM config
        task: TaskDefinition
        tool_executor: Async callable(tool_name, args) -> json_result_str

    Yields:
        LlmStreamChunkWithTools with content, tool_calls, tool_results
    """
    if not task.tools:
        # No tools — simple completion
        from midicoder.pipeline.llm.client import call_llm_stream
        async for chunk in call_llm_stream(
            config,
            system=task.system,
            messages=[{"role": "user", "content": task.user}],
        ):
            yield LlmStreamChunkWithTools(content=chunk.content, usage=chunk.usage)
        return

    # Has tools — use call_llm_with_tools_stream
    # max_rounds=1 means: call LLM once, execute tools once, then LLM outputs final text
    # max_rounds=5 means: up to 5 tool call cycles (for validate+fix loop)
    max_rounds = 5 if task.allow_tool_loop else 1

    async for chunk in call_llm_with_tools_stream(
        config,
        system=task.system,
        messages=[{"role": "user", "content": task.user}],
        tools=task.tools,
        tool_executor=tool_executor,
        max_rounds=max_rounds,
    ):
        yield chunk


# ============================================================================
# TaskOrchestrator — Multi-task flow
# ============================================================================

class TaskOrchestrator:
    """
    Orchestrates a sequence of LLM tasks for contract generation.

    Each task receives a fresh conversation. The orchestrator:
    1. Runs tasks sequentially
    2. Captures output from each task
    3. Summarizes results for the next task's prompt
    4. Yields SSE events for frontend display

    Example flow for contract generation:
    Task 1: "Learn Schema" — LLM calls get_dsl_section, returns schema summary
    Task 2: "Draft YAML" — LLM receives schema summary + brief, outputs YAML draft
    Task 3: "Validate & Fix" — LLM receives YAML draft, calls validate_contract_yaml
    Task 4: "Final Output" — LLM outputs final validated YAML
    """

    def __init__(
        self,
        config: LlmConfig,
        tasks: list[TaskDefinition],
        tool_executor: Callable,
    ):
        self.config = config
        self.tasks = tasks
        self.tool_executor = tool_executor
        # Captured outputs from each task, available for next task's prompt
        self.results: dict[str, dict[str, Any]] = {}

    async def execute(self) -> AsyncIterator[dict[str, Any]]:
        """
        Execute all tasks sequentially.

        Yields:
            SSE event dicts: {event: str, data: any}
        """
        for idx, task in enumerate(self.tasks):
            task_start = time.time()
            task_label = self._task_label(task.task_id)

            yield {
                "event": "task_started",
                "data": {
                    "task": task.task_id,
                    "task_name": task_label,
                    "stage": idx + 1,
                    "total": len(self.tasks),
                },
            }

            accumulated_text = ""
            tool_calls_in_task = []
            tool_results_in_task = []

            try:
                async for chunk in call_llm_task(
                    self.config, task, self.tool_executor
                ):
                    # Forward content
                    if chunk.content:
                        content = chunk.content
                        if content == "\n":
                            yield {"event": "heartbeat", "data": {"round": len(tool_calls_in_task)}}
                            continue

                        # Detect thinking
                        if "<antThinking>" in content or "<thinking>" in content or "<think>" in content:
                            yield {"event": "thinking", "data": {"text": content}}
                        elif content.strip() and len(content.strip()) > 1:
                            accumulated_text += content
                            yield {"event": "content", "data": {"text": content, "accumulated": accumulated_text}}

                        # Check for thinking end
                        if "</antThinking>" in content or "</thinking>" in content or "</think>" in content:
                            yield {"event": "thinking_end", "data": ""}

                    # Forward tool_calls
                    if chunk.tool_calls:
                        for tc in chunk.tool_calls:
                            tool_name = tc.get("function", {}).get("name", "unknown")
                            args_json = tc.get("function", {}).get("arguments", "{}")
                            try:
                                parsed_args = json.loads(args_json) if args_json else {}
                            except Exception:
                                parsed_args = {}
                            tool_calls_in_task.append({"name": tool_name, "arguments": parsed_args})
                            yield {"event": "tool_call", "data": {
                                "name": tool_name,
                                "arguments": parsed_args,
                                "duration_ms": 0,
                            }}

                    # Forward tool_results
                    if chunk.tool_results:
                        for tr in chunk.tool_results:
                            tool_name = tr.get("name", "unknown")
                            result_str = tr.get("result", "")
                            try:
                                result_obj = json.loads(result_str) if result_str else {}
                            except Exception:
                                result_obj = {"raw": str(result_str)[:200]}

                            is_error = "error" in result_obj if isinstance(result_obj, dict) else False
                            summary = self._result_summary(tool_name, result_obj, is_error)

                            tool_results_in_task.append({
                                "name": tool_name,
                                "result": result_obj,
                                "is_error": is_error,
                            })

                            yield {"event": "tool_result", "data": {
                                "name": tool_name,
                                "summary": summary,
                                "full_result": result_obj,
                                "duration_ms": 0,
                            }}

                task_duration = int((time.time() - task_start) * 1000)

                # Store task result
                self.results[task.task_id] = {
                    "accumulated_text": accumulated_text,
                    "tool_calls": tool_calls_in_task,
                    "tool_results": tool_results_in_task,
                    "duration_ms": task_duration,
                }

                # Task completion summary
                summary_text = self._task_completion_summary(task.task_id, self.results[task.task_id])
                yield {
                    "event": "task_completed",
                    "data": {
                        "task": task.task_id,
                        "task_name": task_label,
                        "summary": summary_text,
                        "duration_ms": task_duration,
                    },
                }

            except Exception as e:
                logger.error(f"[TASK-ORCHESTRATOR] Task {task.task_id} failed: {e}")
                yield {
                    "event": "error",
                    "data": f"Task '{task_label}' failed: {e}",
                }
                raise

    def get_result(self, task_id: str) -> dict[str, Any]:
        """Get captured result from a completed task."""
        return self.results.get(task_id, {})

    def get_accumulated_text(self, task_id: str) -> str:
        """Get accumulated text output from a completed task."""
        return self.results.get(task_id, {}).get("accumulated_text", "")

    def get_tool_result(self, task_id: str, tool_name: str) -> Optional[dict]:
        """Get a specific tool result from a completed task."""
        for tr in self.results.get(task_id, {}).get("tool_results", []):
            if tr["name"] == tool_name:
                return tr["result"]
        return None

    @staticmethod
    def _task_label(task_id: str) -> str:
        labels = {
            "learn_schema": "Học Schema",
            "schema": "Học Schema",
            "draft_yaml": "Viết YAML Draft",
            "draft": "Viết YAML Draft",
            "validate": "Validate & Sửa",
            "validate_and_fix": "Validate & Sửa",
            "cross_check": "Kiểm tra Cross-reference",
            "final_review": "Output Final",
            "final": "Output Final",
        }
        return labels.get(task_id, task_id.replace("_", " ").title())

    @staticmethod
    def _result_summary(tool_name: str, result_obj: dict, is_error: bool) -> dict:
        if is_error:
            return {"valid": False, "error": result_obj.get("error", "Unknown error")}
        if tool_name == "validate_contract_yaml":
            return {
                "valid": result_obj.get("is_valid", False),
                "errors": result_obj.get("total_errors", 0),
                "warnings": result_obj.get("total_warnings", 0),
            }
        if tool_name == "cross_check_category":
            return {
                "valid": result_obj.get("valid", True),
                "errors": len(result_obj.get("errors", [])),
                "warnings": len(result_obj.get("warnings", [])),
            }
        return {"found": bool(result_obj), "size": len(json.dumps(result_obj))}

    @staticmethod
    def _task_completion_summary(task_id: str, result: dict) -> str:
        if task_id in ("learn_schema", "schema"):
            return f"Schema đã tải ({result['duration_ms']}ms)"
        if task_id in ("draft_yaml", "draft"):
            text_len = len(result.get("accumulated_text", ""))
            return f"YAML draft ({text_len} chars)"
        if task_id in ("validate", "validate_and_fix"):
            validate_result = None
            for tr in result.get("tool_results", []):
                if tr["name"] == "validate_contract_yaml":
                    validate_result = tr.get("result", {})
                    break
            if validate_result and isinstance(validate_result, dict):
                if validate_result.get("is_valid"):
                    return "Validation passed ✓"
                else:
                    errs = validate_result.get("total_errors", 0)
                    return f"Validation: {errs} errors"
            return "Validation completed"
        if task_id in ("final_review", "final"):
            return "Final YAML ready"
        return f"{TaskOrchestrator._task_label(task_id)} completed"
