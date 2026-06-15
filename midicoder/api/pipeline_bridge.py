"""
PipelineBridge — bridge between backend routers and midicoder pipeline commands.

Calls functions from midicoder.pipeline.commands/ directly,
with click.echo capture for stdout output.
"""

from __future__ import annotations

import asyncio
import io
from typing import Any, Dict, List, Optional


class _ClickOutputCapture:
    """Capture click.echo output into a string buffer."""

    def __init__(self):
        self.buffer = io.StringIO()
        self._original_echo = None

    def __enter__(self):
        import click
        self._original_echo = click.echo
        def capturing_echo(message=None, **kwargs):
            text = str(message) if message is not None else ""
            nl = kwargs.get("nl", True)
            self.buffer.write(text + ("\n" if nl else ""))
        click.echo = capturing_echo
        return self

    def __exit__(self, *args):
        import click
        click.echo = self._original_echo

    def get_output(self) -> str:
        return self.buffer.getvalue()


async def _run_in_thread(func, *args, **kwargs) -> Dict[str, Any]:
    """Run a blocking CLI command function in a thread pool and capture output."""
    loop = asyncio.get_event_loop()

    def _execute():
        with _ClickOutputCapture() as cap:
            try:
                func(*args, **kwargs)
                stdout = cap.get_output()
                return {
                    "success": True,
                    "stdout": stdout,
                    "stderr": "",
                    "returncode": 0,
                }
            except SystemExit as e:
                code = e.code if isinstance(e.code, int) else 1
                return {
                    "success": code == 0,
                    "stdout": cap.get_output(),
                    "stderr": "",
                    "returncode": code,
                }
            except Exception as e:
                return {
                    "success": False,
                    "stdout": cap.get_output(),
                    "stderr": str(e),
                    "returncode": 1,
                }

    result = await loop.run_in_executor(None, _execute)
    return result


class PipelineBridge:
    """Bridge cho backend routers — gọi midicoder commands trực tiếp."""

    # ------------------------------------------------------------------ #
    #  Init
    # ------------------------------------------------------------------ #
    async def execute_command(self, *cmd_parts: str, **kwargs) -> Dict[str, Any]:
        """Generic command dispatcher — maps command name to function."""
        if not cmd_parts:
            return {"success": False, "stdout": "", "stderr": "No command specified", "returncode": 1}

        command = cmd_parts[0].lower()
        subcommand = cmd_parts[1].lower() if len(cmd_parts) > 1 else None

        dispatch = {
            "project": lambda: self._dispatch_project(subcommand, kwargs),
            "brief": lambda: self._dispatch_brief(subcommand, kwargs),
            "contract": lambda: self._dispatch_contract(subcommand, kwargs),
            "ir": lambda: self._dispatch_ir(subcommand, kwargs),
            "code": lambda: self._dispatch_code(subcommand, kwargs),
            "version": lambda: self._dispatch_version(subcommand, kwargs),
            "index": lambda: self._dispatch_index(subcommand, kwargs),
            "runtime": lambda: self._dispatch_runtime(subcommand, kwargs),
            "artifact": lambda: self._dispatch_artifact(subcommand, kwargs),
        }

        handler = dispatch.get(command)
        if handler is None:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Unknown command: {command}",
                "returncode": 1,
            }

        result = handler()
        # Result is a dict from _sync_wrap or _not_implemented (not a coroutine)
        return result

    # ------------------------------------------------------------------ #
    #  Convenience shortcuts (used by routers)
    # ------------------------------------------------------------------ #
    async def contract_gen(self) -> Dict[str, Any]:
        return await self.execute_command("contract", "gen")

    async def contract_gen_resume(self) -> Dict[str, Any]:
        return await self.execute_command("contract", "gen", force=True)

    async def contract_check(self) -> Dict[str, Any]:
        return await self.execute_command("contract", "check")

    async def contract_feedback(self) -> Dict[str, Any]:
        return await self.execute_command("contract", "check")

    async def ir_build(self, skip_diagrams: bool = False) -> Dict[str, Any]:
        return await self.execute_command("ir", "build")

    async def code_build(self) -> Dict[str, Any]:
        return await self.execute_command("code", "plan")

    async def code_plan(self) -> Dict[str, Any]:
        return await self.execute_command("code", "plan")

    async def code_gen(self, runtime: str = "all") -> Dict[str, Any]:
        return await self.execute_command("code", "gen", target=runtime)

    async def code_apply(
        self, target_dir: str = ".", dry_run: bool = False,
        backup: bool = False, force: bool = False,
    ) -> Dict[str, Any]:
        return await self.execute_command(
            "code", "apply",
            target_dir=target_dir, dry_run=dry_run,
            backup=backup, force=force,
        )

    async def index_build(self) -> Dict[str, Any]:
        return await self.execute_command("index", "build")

    async def index_reindex(self, paths: Optional[List[str]] = None) -> Dict[str, Any]:
        return await self.execute_command("index", "build")

    async def brief_analyze_stream(self, project_cwd: str, version: str, language: str = "vi"):
        """SSE streaming — returns async generator of {event, data} dicts."""
        from midicoder.pipeline.commands.brief import analyze_brief_stream_for_api
        return analyze_brief_stream_for_api(project_cwd, version, language)

    async def runtime_test(
        self, target: str = "all", timeout: int = 30
    ) -> Dict[str, Any]:
        return await self.execute_command("runtime", "test", target=target)

    async def runtime_fix(
        self, target: str = "all"
    ) -> Dict[str, Any]:
        return await self.execute_command("runtime", "fix", target=target)

    # ------------------------------------------------------------------ #
    #  Dispatchers
    # ------------------------------------------------------------------ #

    def _dispatch_project(self, sub: str, kwargs) -> Dict[str, Any]:
        if sub == "create":
            from midicoder.pipeline.commands.project import project_create
            name = kwargs.get("name")
            path = kwargs.get("path")
            tech_stack = kwargs.get("tech_stack", {})
            prompt_domain = kwargs.get("prompt_domain", "default")
            return _sync_wrap(
                lambda: project_create(name, path, tech_stack, prompt_domain)
            )
        elif sub == "list":
            from midicoder.pipeline.commands.project import project_list
            return _sync_wrap(lambda: project_list())
        elif sub == "active":
            from midicoder.pipeline.commands.project import project_get_active
            return _sync_wrap(lambda: project_get_active())
        elif sub == "activate":
            from midicoder.pipeline.commands.project import project_activate
            project_id = kwargs.get("project_id") or kwargs.get("_positional")
            return _sync_wrap(lambda: project_activate(project_id))
        elif sub == "delete":
            from midicoder.pipeline.commands.project import project_delete
            project_id = kwargs.get("project_id") or kwargs.get("_positional")
            return _sync_wrap(lambda: project_delete(project_id))
        elif sub == "techstacks":
            from midicoder.pipeline.commands.project import get_techstacks, get_prompt_domains
            return _sync_wrap(lambda: {"stacks": get_techstacks(), "prompt_domains": get_prompt_domains()})
        return _not_implemented("project", sub)

    def _dispatch_brief(self, sub: str, kwargs) -> Dict[str, Any]:
        project_cwd = kwargs.get("project_cwd", "")
        version = kwargs.get("version", "v1.0.0")

        if sub == "freeze":
            from midicoder.pipeline.commands.brief import freeze_brief
            return _sync_wrap(lambda: freeze_brief(version, project_cwd))
        elif sub == "save":
            from midicoder.pipeline.commands.brief import save_brief
            content = kwargs.get("brief_content", "")
            change_desc = kwargs.get("change_description", "Auto-save")
            return _sync_wrap(lambda: save_brief(project_cwd, version, content, change_desc))
        elif sub == "analyze":
            from midicoder.pipeline.commands.brief import analyze_brief_for_api
            language = kwargs.get("language", "vi")
            return _sync_wrap(lambda: analyze_brief_for_api(project_cwd, version, language))
        elif sub == "get":
            from midicoder.pipeline.commands.brief import get_brief_for_api
            return _sync_wrap(lambda: get_brief_for_api(project_cwd, version))
        elif sub == "clarifications":
            from midicoder.pipeline.commands.brief import get_clarifications_for_api
            return _sync_wrap(lambda: get_clarifications_for_api(project_cwd, version))
        elif sub == "revisions":
            from midicoder.pipeline.commands.brief import get_revisions_for_api
            return _sync_wrap(lambda: get_revisions_for_api(project_cwd, version))
        elif sub == "revision-diff":
            from midicoder.pipeline.commands.brief import get_revision_diff_for_api
            rev_num = kwargs.get("revision_number", 1)
            return _sync_wrap(lambda: get_revision_diff_for_api(project_cwd, version, rev_num))
        elif sub == "clarify":
            from midicoder.pipeline.commands.brief import clarify_brief_for_api
            answers = kwargs.get("answers", [])
            re_analyze = kwargs.get("re_analyze", True)
            language = kwargs.get("language", "vi")
            return _sync_wrap(
                lambda: clarify_brief_for_api(project_cwd, version, answers, re_analyze, language)
            )
        return _not_implemented("brief", sub)

    def _dispatch_contract(self, sub: str, kwargs) -> Dict[str, Any]:
        if sub == "gen":
            from midicoder.pipeline.commands.contract import generate_contracts
            force = kwargs.get("force", False)
            return _sync_wrap(lambda: generate_contracts(force=force))
        elif sub == "check":
            from midicoder.pipeline.commands.contract import check_contracts
            return _sync_wrap(lambda: check_contracts())
        elif sub == "repair":
            from midicoder.pipeline.commands.contract import repair_contracts
            return _sync_wrap(lambda: repair_contracts())
        return _not_implemented("contract", sub)

    def _dispatch_ir(self, sub: str, kwargs) -> Dict[str, Any]:
        if sub == "build":
            from midicoder.pipeline.commands.ir import build_mir
            return _sync_wrap(lambda: build_mir(verbose=True))
        return _not_implemented("ir", sub)

    def _dispatch_code(self, sub: str, kwargs) -> Dict[str, Any]:
        target = kwargs.get("target", "all")
        if sub == "plan":
            from midicoder.pipeline.commands.code import _execute_plan
            return _sync_wrap(
                lambda: _execute_plan(
                    target=target,
                    verbose=kwargs.get("verbose", False),
                    status_filter=kwargs.get("status_filter"),
                )
            )
        elif sub == "gen":
            from midicoder.pipeline.commands.code import _execute_gen
            return _sync_wrap(
                lambda: _execute_gen(
                    target=target,
                    dry_run=kwargs.get("dry_run", False),
                    status_filter=kwargs.get("status_filter"),
                    verify=kwargs.get("verify", False),
                )
            )
        elif sub == "apply":
            from midicoder.pipeline.commands.code import _execute_apply
            return _sync_wrap(
                lambda: _execute_apply(
                    target_dir=kwargs.get("target_dir", "."),
                    dry_run=kwargs.get("dry_run", False),
                    backup=kwargs.get("backup", False),
                    force=kwargs.get("force", False),
                )
            )
        return _not_implemented("code", sub)

    def _dispatch_version(self, sub: str, kwargs) -> Dict[str, Any]:
        if sub == "create":
            from midicoder.pipeline.commands.version import create_version
            name = kwargs.get("name") or kwargs.get("_positional", "v1.0.0")
            from_version = kwargs.get("from_version")
            return _sync_wrap(
                lambda: create_version(name=name, from_version=from_version)
            )
        elif sub == "use":
            from midicoder.pipeline.commands.version import use_version
            name = kwargs.get("name") or kwargs.get("_positional")
            return _sync_wrap(lambda: use_version(name))
        elif sub == "list":
            from midicoder.pipeline.commands.version import list_versions_command
            return _sync_wrap(lambda: list_versions_command())
        elif sub == "delete":
            from midicoder.pipeline.commands.version import delete_version
            name = kwargs.get("name") or kwargs.get("_positional")
            force = kwargs.get("force", False)
            return _sync_wrap(lambda: delete_version(name, force=force))
        elif sub == "check-create":
            from midicoder.pipeline.commands.version import check_create_version
            name = kwargs.get("name") or kwargs.get("_positional")
            return _sync_wrap(lambda: check_create_version(name))
        elif sub == "list-json":
            from midicoder.pipeline.commands.version import list_versions, get_active_version, _get_project_root
            from midicoder.pipeline.commands.git_helper import get_git_branch
            result = list_versions()
            active = get_active_version()
            # Detect current git branch for active version
            project_root = _get_project_root()
            current_branch = get_git_branch(str(project_root)) if project_root else None
            versions = []
            for v in result:
                meta = v["metadata"]
                vd = {
                    "version": v["name"],
                    "status": meta.get("status", "draft"),
                    "active": meta.get("active", False),
                    "parent_version": meta.get("parent_version"),
                    "created_at": meta.get("created_at", ""),
                    "pipeline": meta.get("pipeline"),
                }
                # Branch chỉ hiển thị cho version đang active
                if meta.get("active", False):
                    vd["branch"] = current_branch or "N/A"
                versions.append(vd)
            return {
                "success": True,
                "stdout": "",
                "stderr": "",
                "returncode": 0,
                "_data": {"versions": versions, "active_version": active},
            }
        return _not_implemented("version", sub)

    def _dispatch_index(self, sub: str, kwargs) -> Dict[str, Any]:
        if sub in (None, "build", "reindex"):
            from midicoder.pipeline.commands.index import build_index
            force = kwargs.get("force", False)
            watch = kwargs.get("watch", False)
            verbose = kwargs.get("verbose", False)
            returncode = build_index(force=force, watch=watch, verbose=verbose)
            return {
                "success": returncode == 0,
                "stdout": "",
                "stderr": "",
                "returncode": returncode,
            }
        return _not_implemented("index", sub)

    def _dispatch_runtime(self, sub: str, kwargs) -> Dict[str, Any]:
        target = kwargs.get("target", "all")
        return {
            "success": True,
            "stdout": f"Runtime {sub} not yet implemented (target={target})",
            "stderr": "",
            "returncode": 0,
        }

    def _dispatch_artifact(self, sub: str, kwargs) -> Dict[str, Any]:
        if sub == "stats":
            from midicoder.pipeline.commands.artifact_stats import get_artifact_stats
            return _sync_wrap(lambda: get_artifact_stats())
        return _not_implemented("artifact", sub)


def _sync_wrap(func) -> Dict[str, Any]:
    """Wrap a sync function call with click.echo capture + return data."""
    with _ClickOutputCapture() as cap:
        try:
            result = func()
            ret = {
                "success": True,
                "stdout": cap.get_output(),
                "stderr": "",
                "returncode": 0,
            }
            # If function returns a dict, include as _data for caller
            if isinstance(result, dict):
                ret["_data"] = result
            return ret
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
            return {
                "success": code == 0,
                "stdout": cap.get_output(),
                "stderr": "",
                "returncode": code,
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": cap.get_output(),
                "stderr": str(e),
                "returncode": 1,
            }


def _not_implemented(cmd: str, sub: str) -> Dict[str, Any]:
    return {
        "success": False,
        "stdout": "",
        "stderr": f"Command not implemented: {cmd} {sub}",
        "returncode": 1,
    }


# Singleton
pipeline_bridge = PipelineBridge()
