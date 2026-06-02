"""
Main entrypoint cho FastAPI application
Midicoder WebGUI API Server
"""

import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Thêm đường dẫn đến midicoder vào sys.path
# Để đảm bảo có thể import midicoder module
midicoder_path = Path(__file__).parent.parent.parent.resolve()
if str(midicoder_path) not in sys.path:
    sys.path.insert(0, str(midicoder_path))

from app.config import settings
from app.i18n import i18n
from app.models import ApiResponse, ErrorResponse
from app.routers import (
    health, config, index, version, brief, contract, ir, code,
    runtime, websocket, pipeline, patches, init, projects,
)


# Tạo FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description="API Server cho Midicoder WebGUI - CLI Wrapper",
    openapi_tags=[
        {"name": "Health", "description": "Health check và thông tin hệ thống"},
        {"name": "Init", "description": "Khởi tạo dự án"},
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


# Thiết lập CORS cho frontend Angular trên cùng máy
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware để xử lý lỗi toàn cục
@app.exception_handler(Exception)
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
@app.get("/", response_model=ApiResponse)
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
app.openapi_url = "/openapi.json"
app.docs_url = "/docs"
app.redoc_url = "/redoc"


# Thêm các routers
# Health và system
app.include_router(health.router, prefix="/api")

# Init
app.include_router(init.router, prefix="/api")

# Projects (multi-project management)
app.include_router(projects.router, prefix="/api")

# Config
app.include_router(config.router, prefix="/api")

# Index
app.include_router(index.router, prefix="/api")

# Version
app.include_router(version.router, prefix="/api")

# Brief
app.include_router(brief.router, prefix="/api")

# Contract
app.include_router(contract.router, prefix="/api")

# IR
app.include_router(ir.router, prefix="/api")

# Code
app.include_router(code.router, prefix="/api")

# Runtime
app.include_router(runtime.router, prefix="/api")

# WebSocket (no prefix - WebSocket paths are absolute)
app.include_router(websocket.router, prefix="/api")

# Pipeline status
app.include_router(pipeline.router, prefix="/api")

# Patches
app.include_router(patches.router, prefix="/api")


# Endpoint để lấy OpenAPI schema với prefix /api
@app.get("/api/v1/openapi.json", include_in_schema=False)
async def get_openapi():
    """Trả về OpenAPI schema"""
    return app.openapi()


if __name__ == "__main__":
    import uvicorn
    
    # Chạy server với port 6868
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )