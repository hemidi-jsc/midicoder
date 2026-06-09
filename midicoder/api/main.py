"""
Main entrypoint cho FastAPI application
Midicoder WebGUI API Server

Usage from launcher:
    uvicorn midicoder.api.main:server --host 0.0.0.0 --port 6868
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from midicoder.api.config import settings
from midicoder.api.i18n import i18n
from midicoder.api.models import ApiResponse, ErrorResponse
from midicoder.api.routers import (
    health, config, index, version, brief, contract, ir, code,
    runtime, websocket, pipeline, patches, projects,
)


# Tạo FastAPI application
server = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description="API Server cho Midicoder WebGUI",
    openapi_tags=[
        {"name": "Health", "description": "Health check và thông tin hệ thống"},
        {"name": "Projects", "description": "Quản lý multi-projects"},
        {"name": "Config", "description": "Quản lý cấu hình"},
        {"name": "Index", "description": "Quản lý index"},
        {"name": "Version", "description": "Quản lý phiên bản"},
        {"name": "Brief", "description": "Xử lý brief"},
        {"name": "Contract", "description": "Quản lý DSL contracts"},
        {"name": "IR", "description": "Build và quản lý MIR"},
        {"name": "Code", "description": "Generate và apply code"},
        {"name": "Runtime", "description": "Test và fix runtime"},
    ],
)

# Alias for uvicorn CLI
app = server


# Startup hook — auto-activate active project from projects.db
@server.on_event("startup")
async def _auto_activate_active_project():
    """Load active project path from projects.db into ConfigManager on startup.

    This ensures ConfigManager always knows the correct project path after backend restart,
    so endpoints like /version/create don't fail with MDC-CONFIG-001.
    """
    try:
        from midicoder.storage.projects import ProjectsManager
        from midicoder.pipeline.config import get_config

        mgr = ProjectsManager()
        mgr.init()
        active = mgr.get_active()
        if active and active.get("path"):
            cfg = get_config()
            cfg.set_project_path(active["path"])
    except Exception:
        pass  # Non-fatal — endpoints will still work, just no auto-activated project


# Thiết lập CORS cho frontend Angular trên cùng máy
server.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware để xử lý lỗi toàn cục
@server.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Xử lý lỗi toàn cục với i18n"""
    language = i18n.get_language_from_request(request)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": i18n.translate("error.internal_server", language),
                "details": str(exc),
            },
            "timestamp": "2026-04-10T12:00:00Z",  # Will be set by response model
            "language": language,
        },
    )


# Route root
@server.get("/", response_model=ApiResponse)
async def root(request: Request):
    """
    Root endpoint - Thông tin API

    Returns:
        ApiResponse: Thông tin cơ bản về API
    """
    language = i18n.get_language_from_request(request)

    return ApiResponse(
        success=True,
        data={
            "app_name": settings.app_name,
            "api_version": settings.api_version,
            "documentation": "/docs",
        },
        message=i18n.translate("common.success", language),
        language=language,
    )


# Override default docs URLs để đặt tại /docs
server.openapi_url = "/openapi.json"
server.docs_url = "/docs"
server.redoc_url = "/redoc"


# Thêm các routers
# Health và system
server.include_router(health.router, prefix="/api")

# Projects (multi-project management)
server.include_router(projects.router, prefix="/api")

# Config
server.include_router(config.router, prefix="/api")

# Index
server.include_router(index.router, prefix="/api")

# Version
server.include_router(version.router, prefix="/api")

# Brief
server.include_router(brief.router, prefix="/api")

# Contract
server.include_router(contract.router, prefix="/api")

# IR
server.include_router(ir.router, prefix="/api")

# Code
server.include_router(code.router, prefix="/api")

# Runtime
server.include_router(runtime.router, prefix="/api")

# WebSocket (no prefix - WebSocket paths are absolute)
server.include_router(websocket.router, prefix="/api")

# Pipeline status
server.include_router(pipeline.router, prefix="/api")

# Patches
server.include_router(patches.router, prefix="/api")


# Endpoint để lấy OpenAPI schema với prefix /api
@server.get("/api/v1/openapi.json", include_in_schema=False)
async def get_openapi():
    """Trả về OpenAPI schema"""
    return server.openapi()


if __name__ == "__main__":
    import uvicorn

    # Chạy server với port 6868
    uvicorn.run(
        "midicoder.api.main:server",
        host=settings.host,
        port=settings.port,
        reload=False,
    )