"""
MCP-A: Midicoder CE MCP Server.

Server chính cho Midicoder CE MCP — tự động phát hiện và đăng ký tất cả
tools từ midicoder.mcp.tools subpackage.

Hỗ trợ 2 chế độ vận hành:
1. **MCP SDK** ( ưu tiên): Sử dụng `mcp.server.fastmcp.FastMCP` nếu có
2. **HTTP+SSE fallback**: Sử dụng aiohttp/http.server nếu MCP SDK không có

Config:
- Port: 2026 (mặc định từ global config, có thể override bằng env MCP_PORT)
- Host: localhost (từ global config)

Sử dụng:
    from midicoder.mcp.server import create_mcp_server
    server = create_mcp_server()
    server.run()

Hoặc qua CLI:
    midicoder mcp-server
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import time
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from midicoder.errors import MidicoderErrorManager as EM, ErrorCode
from midicoder.mcp.tools import TOOLS
from midicoder.pipeline.config import get_config

logger = logging.getLogger(__name__)

# ============================================================================
# MCP SDK integration
# ============================================================================

try:
    from mcp.server.fastmcp import FastMCP
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

# ============================================================================
# Logging setup
# ============================================================================


def _setup_logging():
    """Setup logging cho MCP server."""
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [MCP] %(levelname)s: %(message)s"
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# ============================================================================
# MCP SDK Server (chế độ chính)
# ============================================================================


class MCPSDKServer:
    """
    MCP Server sử dụng MCP SDK (FastMCP).

    Tự động đăng ký tất cả tools từ TOOLS registry.
    """

    def __init__(self, host: str = "localhost", port: int = 2026):
        self.host = host
        self.port = port
        self._mcp: Optional[FastMCP] = None

    def _create_mcp(self) -> FastMCP:
        """Tạo FastMCP instance và đăng ký tất cả tools."""
        mcp = FastMCP(
            name="midicoder-ce",
            version="0.1.0",
            instructions="Midicoder CE MCP Server — cung cấp 11 tools cho DSL schema, "
                         "pack management, contract compilation, SQLite query, "
                         "và project context.",
        )

        # Tự động đăng ký tất cả tools từ registry
        for tool_name, tool_info in TOOLS.items():
            func = tool_info["function"]
            description = tool_info["description"]
            parameters = tool_info.get("parameters", {})

            mcp.tool(description)(func)
            logger.info(f"Đã đăng ký tool: {tool_name}")

        self._mcp = mcp
        return mcp

    def run(self) -> None:
        """Chạy MCP server với SSE transport."""
        mcp = self._create_mcp()
        _setup_logging()

        logger.info(f"Starting Midicoder CE MCP Server (SDK mode) on {self.host}:{self.port}")

        # FastMCP hỗ trợ SSE transport
        try:
            mcp.run(
                host=self.host,
                port=self.port,
                transport="sse",
            )
        except Exception as e:
            logger.error(f"Lỗi khi khởi động MCP server: {e}")
            raise


# ============================================================================
# HTTP+SSE Fallback Server (khi MCP SDK không có)
# ============================================================================


class MCPFallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler cho MCP fallback với SSE transport."""

    server_instance: "MCPFallbackServer" = None  # type: ignore

    def log_message(self, format: str, *args: Any) -> None:  # type: ignore
        logger.info(f"[MCP] {format % args}")

    def do_GET(self):
        """Xử lý GET request — SSE endpoint."""
        parsed = urlparse(self.path)

        if parsed.path == "/sse":
            self._handle_sse()
        elif parsed.path == "/health":
            self._send_json(200, {"status": "ok", "server": "midicoder-ce-mcp"})
        elif parsed.path == "/tools":
            self._list_tools()
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        """Xử lý POST request — tool call endpoint."""
        parsed = urlparse(self.path)

        if parsed.path == "/tools/call":
            self._handle_tool_call()
        else:
            self._send_json(404, {"error": "Not found"})

    def _handle_sse(self):
        """Xử lý SSE connection."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        # Gửi initial event
        self._write_sse_event(
            "connected",
            {
                "server": "midicoder-ce-mcp",
                "version": "0.1.0",
                "tools": list(TOOLS.keys()),
            }
        )
        self.flush_headers()

    def _write_sse_event(self, event: str, data: Any):
        """Gửi SSE event."""
        self.wfile.write(f"event: {event}\n".encode())
        self.wfile.write(f"data: {json.dumps(data, ensure_ascii=False)}\n\n".encode())
        self.flush_headers()

    def _handle_tool_call(self):
        """Xử lý tool call request."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            request = json.loads(body)

            tool_name = request.get("name") or request.get("tool")
            arguments = request.get("arguments", {})

            if not tool_name:
                self._send_json(400, {"error": "Thiếu tool name"})
                return

            if tool_name not in TOOLS:
                self._send_json(404, {
                    "error": f"Tool '{tool_name}' không tồn tại",
                    "available_tools": list(TOOLS.keys()),
                })
                return

            # Gọi tool function
            start_time = time.time()
            tool_info = TOOLS[tool_name]
            func = tool_info["function"]

            try:
                result = func(**arguments)
                duration_ms = int((time.time() - start_time) * 1000)

                logger.info(
                    f"Tool call: {tool_name} "
                    f"(args={json.dumps(arguments)}, duration={duration_ms}ms)"
                )

                self._send_json(200, {
                    "tool": tool_name,
                    "result": result,
                    "duration_ms": duration_ms,
                })

            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                error_msg = f"{type(e).__name__}: {str(e)}"
                logger.error(f"Tool call error: {tool_name} — {error_msg}")

                self._send_json(500, {
                    "tool": tool_name,
                    "error": error_msg,
                    "traceback": traceback.format_exc(),
                    "duration_ms": duration_ms,
                })

        except json.JSONDecodeError:
            self._send_json(400, {"error": "JSON không hợp lệ"})
        except Exception as e:
            logger.error(f"Lỗi khi xử lý tool call: {e}")
            self._send_json(500, {"error": str(e)})

    def _list_tools(self):
        """Trả về danh sách tools."""
        tools_list = []
        for name, info in TOOLS.items():
            tools_list.append({
                "name": name,
                "description": info["description"],
                "parameters": info.get("parameters", {}),
                "group": info.get("group", "unknown"),
            })

        self._send_json(200, {
            "tools": tools_list,
            "total": len(tools_list),
            "groups": list(set(info.get("group", "") for info in TOOLS.values())),
        })

    def _send_json(self, status: int, data: Any):
        """Gửi JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def flush_headers(self):
        """Flush response."""
        self.wfile.flush()


class MCPFallbackServer:
    """
    MCP Server fallback — HTTP+SSE server khi MCP SDK không có.

    Chạy HTTPServer trong background thread.
    """

    def __init__(self, host: str = "localhost", port: int = 2026):
        self.host = host
        self.port = port
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[Thread] = None

    def run(self) -> None:
        """Chạy HTTP+SSE server."""
        _setup_logging()
        MCPFallbackHandler.server_instance = self

        self._server = HTTPServer((self.host, self.port), MCPFallbackHandler)

        logger.info(
            f"Starting Midicoder CE MCP Server (HTTP+SSE fallback) "
            f"on {self.host}:{self.port}"
        )
        logger.info(f"Endpoints: SSE=/sse, Tools=/tools, Call=/tools/call, Health=/health")
        logger.info(f"Tổng số tools: {len(TOOLS)}")

        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Đã nhận tín hiệu dừng server")
        finally:
            self.stop()

    def stop(self) -> None:
        """Dừng server."""
        if self._server:
            self._server.shutdown()
            logger.info("MCP Server đã dừng")


# ============================================================================
# Public API
# ============================================================================


def get_mcp_config() -> tuple[str, int]:
    """
    Lấy MCP config từ global config.

    Returns:
        Tuple (host, port)
    """
    try:
        config = get_config()
        host = config.get("mcp.host", "localhost")
        port = config.get("mcp.port", 2026)
    except Exception:
        host = os.environ.get("MCP_HOST", "localhost")
        port = int(os.environ.get("MCP_PORT", "2026"))

    return host, port


def create_mcp_server(
    host: Optional[str] = None,
    port: Optional[int] = None,
    use_fallback: bool = False,
) -> Any:
    """
    Tạo MCP server instance.

    Tự động chọn chế độ vận hành:
    - Nếu `mcp` package có sẵn và `use_fallback=False`: dùng MCP SDK (FastMCP)
    - Ngược lại: dùng HTTP+SSE fallback

    Args:
        host: Host address (override config)
        port: Port number (override config)
        use_fallback: Force sử dụng HTTP+SSE fallback

    Returns:
        MCP server instance (MCPSDKServer hoặc MCPFallbackServer)

    Example:
        >>> server = create_mcp_server()
        >>> server.run()  # Chạy blocking
    """
    if host is None or port is None:
        config_host, config_port = get_mcp_config()
        host = host or config_host
        port = port or config_port

    if not use_fallback and HAS_MCP:
        logger.info("Sử dụng MCP SDK (FastMCP) cho server")
        return MCPSDKServer(host=host, port=port)
    else:
        if not HAS_MCP:
            logger.info("MCP SDK không có sẵn — sử dụng HTTP+SSE fallback")
        else:
            logger.info("Sử dụng HTTP+SSE fallback (force mode)")
        return MCPFallbackServer(host=host, port=port)


def run_mcp_server(
    host: Optional[str] = None,
    port: Optional[int] = None,
    use_fallback: bool = False,
) -> None:
    """
    Tạo và chạy MCP server (blocking).

    Args:
        host: Host address
        port: Port number
        use_fallback: Force sử dụng HTTP+SSE fallback
    """
    server = create_mcp_server(host=host, port=port, use_fallback=use_fallback)
    server.run()


# ============================================================================
# CLI entry point
# ============================================================================


def main():
    """CLI entry point cho MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="Midicoder CE MCP Server")
    parser.add_argument("--host", default=None, help="Host address")
    parser.add_argument("--port", type=int, default=None, help="Port number")
    parser.add_argument("--fallback", action="store_true", help="Sử dụng HTTP+SSE fallback")
    parser.add_argument("--list-tools", action="store_true", help="Liệt kê tools và exit")

    args = parser.parse_args()

    if args.list_tools:
        print("Midicoder CE MCP Tools:")
        print("=" * 60)
        for name, info in sorted(TOOLS.items()):
            group = info.get("group", "unknown").upper()
            print(f"  [{group}] {name}")
            print(f"    {info['description']}")
            params = info.get("parameters", {})
            if params:
                props = params.get("properties", {})
                required = params.get("required", [])
                for pname, pdata in props.items():
                    req = " (required)" if pname in required else ""
                    print(f"    - {pname}: {pdata.get('description', '')}{req}")
            print()
        print(f"Tổng: {len(TOOLS)} tools")
        return

    run_mcp_server(
        host=args.host,
        port=args.port,
        use_fallback=args.fallback,
    )


if __name__ == "__main__":
    main()
