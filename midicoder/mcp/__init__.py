"""
Midicoder CE MCP Server Package.

Cung cấp MCP (Model Context Protocol) server với 11 tools trong 6 groups:

Groups:
- MCP-B (DSL Schema): get_dsl_schema, get_dsl_section
- MCP-C (Packs): list_packs, get_pack
- MCP-D (Compiler): compile_contracts, validate_capability_graph
- MCP-E (SQLite): get_active_brief, get_clarifications, list_artifacts
- MCP-F (Context): get_project_context, list_symbols

Sử dụng:
    from midicoder.mcp import create_mcp_server, run_mcp_server

    # Tạo và chạy server
    server = create_mcp_server()  # Default port 2026
    server.run()

    # Hoặc chạy trực tiếp
    run_mcp_server(port=2026)
"""

from midicoder.mcp.server import (
    HAS_MCP,
    create_mcp_server,
    get_mcp_config,
    run_mcp_server,
)

__all__ = [
    "HAS_MCP",
    "create_mcp_server",
    "get_mcp_config",
    "run_mcp_server",
]
