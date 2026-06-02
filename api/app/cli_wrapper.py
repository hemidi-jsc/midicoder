"""
CLI Wrapper cho Midicoder
Wrapper thuần túy - chỉ gọi CLI mà không thêm logic nào
Tất cả comment bằng tiếng Việt
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from app.config import settings, get_project_cwd
from app.i18n import i18n


class CLIWrapper:
    """
    Wrapper để gọi CLI commands của Midicoder
    Không thêm logic business, chỉ đóng vai trò cầu nối
    """
    
    def __init__(self):
        # Thêm đường dẫn đến midicoder vào sys.path
        # Đảm bảo có thể import midicoder
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))
    
    def _build_command_args(
        self,
        command: str,
        subcommand: Optional[str] = None,
        args: Optional[Dict[str, Any]] = None
    ) -> list[str]:
        """
        Xây dựng đối số cho CLI command
        
        Args:
            command: Tên command chính (init, config, brief, v.v.)
            subcommand: Subcommand (nếu có)
            args: Các đối số bổ sung
        
        Returns:
            Danh sách đối số cho CLI
        """
        cmd_args = [sys.executable, str(Path(__file__).parent / "run_cli.py")]

        # Thêm command
        cmd_args.append(command)

        # Thêm subcommand nếu có
        if subcommand:
            cmd_args.append(subcommand)

        # Thêm positional args trước flags
        if args:
            # Handle _positional: positional argument (sau subcommand, trước --flags)
            if "_positional" in args:
                pos_val = args["_positional"]
                if isinstance(pos_val, list):
                    cmd_args.extend(str(v) for v in pos_val)
                else:
                    cmd_args.append(str(pos_val))

            # Thêm các đối số từ args dict (skip _positional)
            for key, value in args.items():
                if key == "_positional":
                    continue

                # Chuyển underscore thành hyphen (--my_arg -> --my-arg)
                arg_name = f"--{key.replace('_', '-')}"

                # Xử lý giá trị boolean
                if isinstance(value, bool):
                    if value:
                        cmd_args.append(arg_name)
                elif isinstance(value, list):
                    # Xử lý danh sách
                    for item in value:
                        cmd_args.append(arg_name)
                        cmd_args.append(str(item))
                else:
                    # Giá trị thường
                    cmd_args.append(arg_name)
                    cmd_args.append(str(value))
        
        return cmd_args
    
    async def execute_command(
        self,
        command: str,
        subcommand: Optional[str] = None,
        args: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Thực thi một CLI command
        
        Args:
            command: Tên command (config, brief, contract, ir, code, runtime)
            subcommand: Subcommand (nếu có)
            args: Các đối số cho command
            timeout: Timeout tính bằng giây (mặc định từ settings)
        
        Returns:
            Dict chứa kết quả thực thi
        """
        if timeout is None:
            timeout = settings.cli_timeout
        
        # Xây dựng command args
        cmd_args = self._build_command_args(command, subcommand, args)
        
        # Thiết lập môi trường
        env = os.environ.copy()

        # Force UTF-8 encoding on Windows
        env["PYTHONUTF8"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        # Thiết lập thư mục làm việc từ global config
        cwd = get_project_cwd()
        
        try:
            # Tạo subprocess (stdin=PIPE để questionary không crash khi không có console)
            subprocess_kwargs: Dict[str, Any] = {
                "stdin": asyncio.subprocess.PIPE,
                "stdout": asyncio.subprocess.PIPE,
                "stderr": asyncio.subprocess.PIPE,
                "cwd": cwd,
                "env": env,
            }

            process = await asyncio.create_subprocess_exec(*cmd_args, **subprocess_kwargs)
            
            # Đọc output với timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                exit_code = process.returncode
                
                # Decode output
                stdout_text = stdout.decode('utf-8', errors='replace')
                stderr_text = stderr.decode('utf-8', errors='replace')
                
                # Parse output nếu là JSON
                stdout_data = None
                try:
                    stdout_data = json.loads(stdout_text) if stdout_text.strip() else None
                except json.JSONDecodeError:
                    pass
                
                return {
                    "success": exit_code == 0,
                    "exit_code": exit_code,
                    "stdout": stdout_text,
                    "stdout_data": stdout_data,
                    "stderr": stderr_text,
                    "command": cmd_args,
                }
                
            except asyncio.TimeoutError:
                # Kill process nếu timeout
                process.kill()
                await process.wait()
                
                return {
                    "success": False,
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": f"Command timed out after {timeout} seconds",
                    "command": cmd_args,
                    "timeout": True,
                }
                
        except FileNotFoundError:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "Midicoder command not found. Ensure midicoder is installed.",
                "command": cmd_args,
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "command": cmd_args,
            }
    
    # ==================== Config Commands ====================
    
    async def config_get(self, key: str) -> Dict[str, Any]:
        """Lấy giá trị config"""
        return await self.execute_command("config", "get", {key: None})
    
    async def config_set(self, key: str, value: str) -> Dict[str, Any]:
        """Đặt giá trị config"""
        return await self.execute_command("config", "set", {key: value})
    
    async def config_list(self) -> Dict[str, Any]:
        """Liệt kê tất cả config"""
        return await self.execute_command("config", "list")
    
    async def config_validate(self) -> Dict[str, Any]:
        """Validate config"""
        return await self.execute_command("config", "validate")
    
    async def config_reset(self) -> Dict[str, Any]:
        """Reset config về mặc định"""
        return await self.execute_command("config", "reset")
    
    # ==================== Index Commands ====================
    
    async def index_build(self) -> Dict[str, Any]:
        """Build index"""
        return await self.execute_command("index")
    
    async def index_reindex(self, paths: Optional[list[str]] = None) -> Dict[str, Any]:
        """Reindex các file đã thay đổi"""
        args = {"path": paths} if paths else {}
        return await self.execute_command("index", "reindex", args)
    
    # ==================== Version Commands ====================
    
    async def version_create(self, version: str) -> Dict[str, Any]:
        """Tạo phiên bản mới — positional argument, không phải --version flag"""
        # CLI: version create <name> [options]
        # Execute command builds args dict as --key value, but `name` is positional.
        # Workaround: pass as special `name` key that _build_command_args handles.
        return await self.execute_command("version", "create", {"_positional": version})
    
    # ==================== Brief Commands ====================
    
    async def brief_analyze(self) -> Dict[str, Any]:
        """Phân tích brief"""
        return await self.execute_command("brief", "analyze")
    
    async def brief_rewrite(self) -> Dict[str, Any]:
        """Viết lại brief"""
        return await self.execute_command("brief", "rewrite")
    
    # ==================== Contract Commands ====================
    
    async def contract_gen(self) -> Dict[str, Any]:
        """Generate contract"""
        return await self.execute_command("contract", "gen")
    
    async def contract_gen_resume(self) -> Dict[str, Any]:
        """Resume contract generation"""
        return await self.execute_command("contract", "gen", {"resume": None})
    
    async def contract_check(self) -> Dict[str, Any]:
        """Kiểm tra contract"""
        return await self.execute_command("contract", "check")
    
    async def contract_feedback(self) -> Dict[str, Any]:
        """Feedback cho contract"""
        return await self.execute_command("contract", "feedback")
    
    # ==================== IR Commands ====================
    
    async def ir_build(self, skip_diagrams: bool = False) -> Dict[str, Any]:
        """Build IR (MIR)"""
        return await self.execute_command("ir", "build", {"skip_diagrams": skip_diagrams})
    
    # ==================== Code Commands ====================
    
    async def code_build(self) -> Dict[str, Any]:
        """Build code plan"""
        return await self.execute_command("code", "build")
    
    async def code_plan(self) -> Dict[str, Any]:
        """Plan code (alias của build)"""
        return await self.execute_command("code", "plan")
    
    async def code_gen(self, runtime: bool = False) -> Dict[str, Any]:
        """Generate code"""
        return await self.execute_command("code", "gen", {"runtime": runtime})
    
    async def code_apply(
        self,
        force: bool = False,
        dry_run: bool = False,
        no_reindex: bool = False,
        patches_subdir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Apply code"""
        args = {
            "force": force,
            "dry_run": dry_run,
            "no_reindex": no_reindex,
        }
        if patches_subdir:
            args["patches_dir"] = patches_subdir
        return await self.execute_command("code", "apply", args)
    
    # ==================== Runtime Commands ====================
    
    async def runtime_test(
        self,
        timeout: int = 30,
        port: int = 8000,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """Test runtime"""
        return await self.execute_command("runtime", "test", {
            "timeout": timeout,
            "port": port,
            "verbose": verbose,
        })
    
    async def runtime_fix(
        self,
        log_timestamp: Optional[str] = None,
        dry_run: bool = False,
        auto_apply: bool = False,
        auto_fix_loop: bool = False,
        test_timeout: int = 30,
        test_port: int = 8000
    ) -> Dict[str, Any]:
        """Fix runtime errors"""
        args = {
            "dry_run": dry_run,
            "auto_apply": auto_apply,
            "auto_fix_loop": auto_fix_loop,
            "test_timeout": test_timeout,
            "test_port": test_port,
        }
        if log_timestamp:
            args["log_timestamp"] = log_timestamp
        return await self.execute_command("runtime", "fix", args)


# Instance toàn cục
cli_wrapper = CLIWrapper()