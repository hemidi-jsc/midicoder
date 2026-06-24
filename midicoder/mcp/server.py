"""
MCP-A: Midicoder CE MCP Server.

Server chính cho Midicoder CE MCP — tự động phát hiện và đăng ký tất cả
tools từ midicoder.mcp.tools subpackage.

Hỗ trợ 2 chế độ vận hành:
1. **MCP SDK** ( ưu tiên): Sử dụng `mcp.server.fastmcp.FastMCP` nếu có
2. **HTTP+SSE fallback**: Sử dụng aiohttp/http.server nếu MCP SDK không có

Config:
- Port: 7878 (mặc định từ global config, có thể override bằng env MCP_PORT)
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
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

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

    def __init__(self, host: str = "localhost", port: int = 7878):
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
# MCP Fallback Server — uvicorn + Starlette
# ============================================================================


def _build_mcp_app():
    """Tạo Starlette app với các MCP endpoints."""
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse, Response
    from starlette.routing import Route
    from starlette.requests import Request

    starlette_app = Starlette(routes=[])

    # ── /health ──
    async def health(request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok", "server": "midicoder-ce-mcp"})

    # ── /tools ──
    async def list_tools(request: Request) -> JSONResponse:
        tools_list = []
        for name, info in TOOLS.items():
            tools_list.append({
                "name": name,
                "description": info["description"],
                "parameters": info.get("parameters", {}),
                "group": info.get("group", "unknown"),
            })
        return JSONResponse({"tools": tools_list, "total": len(tools_list)})

    # ── /tools/call (POST) ──
    async def call_tool(request: Request) -> JSONResponse:
        body = await request.json()
        tool_name = body.get("name", "")
        arguments = body.get("arguments", {})

        if tool_name not in TOOLS:
            return JSONResponse(
                {"error": f"Unknown tool: {tool_name}"},
                status_code=404,
            )

        func = TOOLS[tool_name]["function"]
        try:
            result = func(**arguments)
            return JSONResponse({"result": result})
        except Exception as e:
            return JSONResponse(
                {"error": str(e)},
                status_code=500,
            )

    # ── /sse (SSE stream) ──
    async def sse_endpoint(request: Request) -> Response:
        import asyncio

        async def event_generator():
            # Send initial connected event
            initial = {
                "server": "midicoder-ce-mcp",
                "version": "0.1.0",
                "tools": list(TOOLS.keys()),
            }
            yield f"event: connected\ndata: {json.dumps(initial, ensure_ascii=False)}\n\n"

            # Keep connection alive
            while True:
                try:
                    await asyncio.sleep(30)
                    yield ": heartbeat\n\n"
                except asyncio.CancelledError:
                    break

        return Response(content=event_generator(), media_type="text/event-stream")

    starlette_app.router.routes.append(Route("/health", health, methods=["GET"]))
    starlette_app.router.routes.append(Route("/tools", list_tools, methods=["GET"]))
    starlette_app.router.routes.append(Route("/tools/call", call_tool, methods=["POST"]))
    starlette_app.router.routes.append(Route("/sse", sse_endpoint, methods=["GET"]))

    return starlette_app


# Module-level app — để start bằng CLI: uvicorn midicoder.mcp.server:app --port 7878
app = _build_mcp_app()


class MCPFallbackServer:
    """
    MCP Server fallback — uvicorn + Starlette khi MCP SDK không có.

    Chạy uvicorn.Server (async) với clean shutdown qua should_exit.
    """

    def __init__(self, host: str = "localhost", port: int = 7878):
        self.host = host
        self.port = port
        self._server: Any = None

    def run(self) -> None:
        """Chạy uvicorn server với clean shutdown."""
        _setup_logging()

        import uvicorn
        config = uvicorn.Config(
            app,
            host=self.host,
            port=self.port,
            log_level="warning",
            loop="asyncio",
        )
        self._server = uvicorn.Server(config)

        logger.info(
            f"Starting Midicoder CE MCP Server (uvicorn fallback) "
            f"on {self.host}:{self.port}"
        )
        logger.info(f"Endpoints: SSE=/sse, Tools=/tools, Call=/tools/call, Health=/health")
        logger.info(f"Tổng số tools: {len(TOOLS)}")

        try:
            self._server.run()
        except KeyboardInterrupt:
            logger.info("Đã nhận tín hiệu dừng server")

    def stop(self) -> None:
        """Dừng server (uvicorn clean shutdown)."""
        if self._server:
            self._server.should_exit = True
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
        port = config.get("mcp.port", 7878)
    except Exception:
        host = os.environ.get("MCP_HOST", "localhost")
        port = int(os.environ.get("MCP_PORT", "7878"))

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
