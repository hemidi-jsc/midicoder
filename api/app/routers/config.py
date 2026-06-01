"""
Router cho các commands về config
"""

import json
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Request

from app.cli_wrapper import cli_wrapper
from app.i18n import i18n
from app.models import ApiResponse, ConfigSetRequest

router = APIRouter(prefix="/config", tags=["Config"])

# Global config path
GLOBAL_CONFIG_DIR = Path.home() / ".midicoder"
GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "midicoder.json"


def _read_global_config() -> Dict[str, Any]:
    """Read global config from disk."""
    if GLOBAL_CONFIG_FILE.exists():
        return json.loads(GLOBAL_CONFIG_FILE.read_text(encoding="utf-8"))
    return {}


def _write_global_config(config: Dict[str, Any]) -> None:
    """Write global config to disk."""
    GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    GLOBAL_CONFIG_FILE.write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# Supported LLM providers
SUPPORTED_PROVIDERS = [
    "openai-compatible",
    "openai",
    "anthropic",
    "aws-bedrock",
    "azure",
    "vertex",
]


def _validate_llm_config(llm: Dict[str, Any]) -> list[str]:
    """Validate LLM config, return list of errors."""
    errors = []
    if not llm.get("provider"):
        errors.append("provider is required")
    elif llm["provider"] not in SUPPORTED_PROVIDERS:
        errors.append(f"provider must be one of: {', '.join(SUPPORTED_PROVIDERS)}")
    if not llm.get("model"):
        errors.append("model is required")
    if not llm.get("api_url"):
        errors.append("api_url is required")
    return errors


@router.get("/llm", response_model=ApiResponse)
async def get_llm_config(request: Request):
    """
    Lấy LLM config từ global config.

    Reads ~/.midicoder/midicoder.json llm section directly (no CLI subprocess).
    """
    language = i18n.get_language_from_request(request)
    config = _read_global_config()
    llm = config.get("llm", {})

    return ApiResponse(
        success=True,
        data={
            "llm": llm,
            "providers": SUPPORTED_PROVIDERS,
        },
        language=language,
    )


@router.post("/llm", response_model=ApiResponse)
async def set_llm_config(request: Request):
    """
    Ghi LLM config vào global config.

    Expects JSON body: {"provider": "...", "model": "...", "api_url": "...", ...}
    Validates required fields before writing.
    """
    language = i18n.get_language_from_request(request)
    try:
        body = await request.json()
    except Exception:
        return ApiResponse(
            success=False,
            message="Invalid JSON body",
            language=language,
        )

    errors = _validate_llm_config(body)
    if errors:
        return ApiResponse(
            success=False,
            message="; ".join(errors),
            language=language,
        )

    config = _read_global_config()
    # Merge llm config — keep existing keys not in body
    existing = config.get("llm", {})
    merged = {**existing, **body}
    config["llm"] = merged
    _write_global_config(config)

    return ApiResponse(
        success=True,
        data={"saved": True},
        message="LLM config saved successfully",
        language=language,
    )


@router.post("/llm/test", response_model=ApiResponse)
async def test_llm_config(request: Request):
    """
    Test LLM connection với config hiện tại.

    Force reloads config from disk first so the test uses the latest values,
    not the cached singleton from startup.
    """
    language = i18n.get_language_from_request(request)

    try:
        # Force reload config from disk — invalidate cached singleton
        from midicoder.pipeline.config import get_config
        config_mgr = get_config()
        config_mgr._global_loaded = False
        config_mgr._global_config = {}

        from midicoder.pipeline.llm import call_llm, load_llm_config

        config = load_llm_config()
        response = call_llm(
            config=config,
            messages=[{"role": "user", "content": "Reply with OK"}],
        )

        return ApiResponse(
            success=True,
            data={
                "connected": True,
                "provider": config.provider,
                "model": config.model,
                "response": response.content[:200],
                "usage": response.usage,
            },
            message="LLM connection successful",
            language=language,
        )
    except Exception as e:
        error_str = str(e)
        return ApiResponse(
            success=False,
            data={"connected": False, "error": error_str},
            message=f"LLM connection failed: {error_str}",
            language=language,
        )


@router.get("/list", response_model=ApiResponse)
async def list_config(request: Request):
    """
    Liệt kê tất cả cấu hình
    
    Args:
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Danh sách cấu hình
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để lấy config
    result = await cli_wrapper.config_list()
    
    if result["success"]:
        # Parse stdout để lấy config dict
        try:
            config_data = result.get("stdout_data") or {}
            return ApiResponse(
                success=True,
                data=config_data,
                message=i18n.translate("config.list_success", language),
                language=language,
            )
        except Exception as e:
            return ApiResponse(
                success=False,
                data=None,
                message=str(e),
                language=language,
            )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.get("/get/{key}", response_model=ApiResponse)
async def get_config(key: str, request: Request):
    """
    Lấy giá trị của một key config
    
    Args:
        key: Key của config
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Giá trị config
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để lấy config
    result = await cli_wrapper.config_get(key)
    
    if result["success"]:
        # Parse stdout để lấy giá trị
        stdout = result.get("stdout", "").strip()
        return ApiResponse(
            success=True,
            data={"key": key, "value": stdout},
            message=i18n.translate("config.get_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.post("/set", response_model=ApiResponse)
async def set_config(config: ConfigSetRequest, request: Request):
    """
    Đặt giá trị cho một key config
    
    Args:
        config: Request chứa key và value
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả đặt config
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để set config
    result = await cli_wrapper.config_set(config.key, config.value)
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data={"key": config.key, "value": config.value},
            message=i18n.translate("config.set_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.post("/validate", response_model=ApiResponse)
async def validate_config(request: Request):
    """
    Validate cấu hình hiện tại
    
    Args:
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả validate
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để validate config
    result = await cli_wrapper.config_validate()
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data=None,
            message=i18n.translate("config.validate_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )


@router.post("/reset", response_model=ApiResponse)
async def reset_config(request: Request):
    """
    Reset cấu hình về mặc định
    
    Args:
        request: Request object để lấy ngôn ngữ
    
    Returns:
        ApiResponse: Kết quả reset
    """
    language = i18n.get_language_from_request(request)
    
    # Gọi CLI wrapper để reset config
    result = await cli_wrapper.config_reset()
    
    if result["success"]:
        return ApiResponse(
            success=True,
            data=None,
            message=i18n.translate("config.reset_success", language),
            language=language,
        )
    
    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Unknown error"),
        language=language,
    )