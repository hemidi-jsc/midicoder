"""FastAPI runtime test runner."""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .logger import RuntimeLogger
from .models import ErrorInfo, RuntimeTestResult


@dataclass
class TestConfig:
    """Configuration for runtime test."""

    workspace_root: Path
    working_dir: Path
    timeout: int = 30  # seconds
    port: int = 8000
    verbose: bool = False


class FastAPIRunner:
    """Run FastAPI application and capture output."""

    def __init__(self, config: TestConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.logger = RuntimeLogger(config.workspace_root)

    def start(self) -> RuntimeTestResult:
        """Start FastAPI app and monitor for errors."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        log_dir = self.config.workspace_root / ".midicoder" / "logs" / timestamp
        log_dir.mkdir(parents=True, exist_ok=True)

        # Detect Python executable from working_dir venv or use system python
        python_executable = self._find_python_executable()

        # Command to run FastAPI with uvicorn
        cmd = [
            str(python_executable),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(self.config.port),
            "--log-level",
            "debug",
        ]

        errors: list[ErrorInfo] = []
        debug_lines: list[str] = []
        success = False

        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=str(self.config.working_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            start_time = time.time()
            startup_detected = False
            current_traceback: list[str] = []
            in_traceback = False

            # Monitor output for startup or errors
            while time.time() - start_time < self.config.timeout:
                if self.process.poll() is not None:
                    # Process exited, read remaining output
                    if self.process.stdout:
                        remaining = self.process.stdout.read()
                        if remaining:
                            for line in remaining.splitlines():
                                line = line.rstrip()
                                debug_lines.append(line)
                                error_info = self._parse_error_line(
                                    line,
                                    current_traceback,
                                    in_traceback,
                                )
                                if error_info:
                                    errors.append(error_info)
                                    current_traceback = []
                                    in_traceback = False
                    break

                line = self.process.stdout.readline() if self.process.stdout else ""
                if not line:
                    time.sleep(0.1)
                    continue

                line = line.rstrip()
                debug_lines.append(line)

                if self.config.verbose:
                    print(line)

                # Check for successful startup
                if (
                    "Uvicorn running on" in line
                    or "Application startup complete" in line
                ):
                    startup_detected = True
                    success = True
                    break

                # Track traceback
                if "Traceback (most recent call last):" in line:
                    in_traceback = True
                    current_traceback = [line]
                    continue

                if in_traceback:
                    current_traceback.append(line)
                    # Check if traceback ended (error line like "ImportError: ...")
                    if line and not line.startswith(" ") and not line.startswith("\t"):
                        if any(
                            err_type in line for err_type in ["Error:", "Exception:"]
                        ):
                            # Traceback complete, create error
                            error_info = ErrorInfo(
                                type=self._classify_error_type(line),
                                message=line,
                                file=self._extract_file_from_traceback(
                                    current_traceback
                                ),
                                line=self._extract_line_from_traceback(
                                    current_traceback
                                ),
                                traceback="\n".join(current_traceback),
                            )
                            errors.append(error_info)
                            current_traceback = []
                            in_traceback = False
                    continue

                # Check for errors outside traceback
                error_info = self._parse_error_line(
                    line, current_traceback, in_traceback
                )
                if error_info and not in_traceback:
                    errors.append(error_info)

            # If timeout or no startup detected
            if not startup_detected and self.process.poll() is None:
                if not errors:
                    errors.append(
                        ErrorInfo(
                            type="timeout",
                            message=f"App failed to start within {self.config.timeout}s",
                            file=None,
                            line=None,
                            traceback="\n".join(debug_lines[-20:])
                            if debug_lines
                            else "",
                        )
                    )

        except Exception as exc:
            errors.append(
                ErrorInfo(
                    type="runner_error",
                    message=str(exc),
                    file=None,
                    line=None,
                    traceback="",
                )
            )

        finally:
            # Cleanup: stop the process
            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()

        # Save logs
        result = RuntimeTestResult(
            timestamp=timestamp,
            success=success,
            port=self.config.port,
            errors=errors,
            log_dir=str(log_dir),
            debug_output=debug_lines,
        )

        self.logger.save_logs(log_dir, result)

        return result

    def _parse_error_line(
        self,
        line: str,
        current_traceback: list[str],
        in_traceback: bool,
    ) -> Optional[ErrorInfo]:
        """Parse error from log line."""
        # Skip if in traceback (handled separately)
        if in_traceback:
            return None

        # Import error patterns
        if "ImportError:" in line or "ModuleNotFoundError:" in line:
            return ErrorInfo(
                type="import_error",
                message=line,
                file=None,
                line=None,
                traceback="",
            )

        # Syntax error patterns
        if "SyntaxError:" in line:
            return ErrorInfo(
                type="syntax_error",
                message=line,
                file=None,
                line=None,
                traceback="",
            )

        # FastAPI specific errors
        if "ERROR:" in line or "CRITICAL:" in line:
            return ErrorInfo(
                type="application_error",
                message=line,
                file=None,
                line=None,
                traceback="",
            )

        return None

    def _classify_error_type(self, error_line: str) -> str:
        """Classify error type from error line."""
        if "ImportError" in error_line or "ModuleNotFoundError" in error_line:
            return "import_error"
        elif "SyntaxError" in error_line:
            return "syntax_error"
        elif "AttributeError" in error_line:
            return "attribute_error"
        elif "TypeError" in error_line:
            return "type_error"
        elif "NameError" in error_line:
            return "name_error"
        elif "ValueError" in error_line:
            return "value_error"
        else:
            return "runtime_error"

    def _extract_file_from_traceback(self, traceback: list[str]) -> Optional[str]:
        """Extract file path from traceback."""
        import re

        for line in traceback:
            match = re.search(r'File "([^"]+)"', line)
            if match:
                return match.group(1)
        return None

    def _extract_line_from_traceback(self, traceback: list[str]) -> Optional[int]:
        """Extract line number from traceback."""
        import re

        for line in traceback:
            match = re.search(r"line (\d+)", line)
            if match:
                return int(match.group(1))
        return None

    def _find_python_executable(self) -> Path:
        """Find Python executable from working_dir venv or use system python."""
        # Check for venv in working_dir
        venv_paths = [
            self.config.working_dir / "venv" / "Scripts" / "python.exe",  # Windows
            self.config.working_dir / "venv" / "bin" / "python",  # Unix
            self.config.working_dir / ".venv" / "Scripts" / "python.exe",  # Windows
            self.config.working_dir / ".venv" / "bin" / "python",  # Unix
        ]

        for venv_python in venv_paths:
            if venv_python.exists():
                return venv_python

        # Fallback to system python
        return Path(sys.executable)


def run_runtime_test(
    workspace_root: Path,
    timeout: int = 30,
    port: int = 8000,
    verbose: bool = False,
) -> RuntimeTestResult:
    """Run runtime test with configuration."""
    from midicoder.commands.base import MidicoderPaths
    from midicoder.config.manager import ConfigManager

    paths = MidicoderPaths(root=workspace_root)
    config_mgr = ConfigManager(paths)
    config = config_mgr.load()

    working_dir_str = config.get("working_dir", ".")
    working_dir = Path(working_dir_str)
    if not working_dir.is_absolute():
        working_dir = (workspace_root / working_dir).resolve()

    test_config = TestConfig(
        workspace_root=workspace_root,
        working_dir=working_dir,
        timeout=timeout,
        port=port,
        verbose=verbose,
    )

    runner = FastAPIRunner(test_config)
    return runner.start()
