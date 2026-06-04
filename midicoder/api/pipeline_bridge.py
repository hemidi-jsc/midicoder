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
            "contract": lambda: self._dispatch_contract(subcommand, kwargs),
            "ir": lambda: self._dispatch_ir(subcommand, kwargs),
            "code": lambda: self._dispatch_code(subcommand, kwargs),
            "version": lambda: self._dispatch_version(subcommand, kwargs),
            "index": lambda: self._dispatch_index(subcommand, kwargs),
            "runtime": lambda: self._dispatch_runtime(subcommand, kwargs),
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
            return _sync_wrap(lambda: delete_version(name))
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


def _sync_wrap(func) -> Dict[str, Any]:
    """Wrap a sync function call with click.echo capture."""
    with _ClickOutputCapture() as cap:
        try:
            func()
            return {
                "success": True,
                "stdout": cap.get_output(),
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


def _not_implemented(cmd: str, sub: str) -> Dict[str, Any]:
    return {
        "success": False,
        "stdout": "",
        "stderr": f"Command not implemented: {cmd} {sub}",
        "returncode": 1,
    }


# Singleton
pipeline_bridge = PipelineBridge()
