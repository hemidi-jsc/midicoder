"""
Config router — reads/writes settings.db (SQLite) via SettingsManager.
"""

from typing import Any, Dict

from fastapi import APIRouter, Request

from midicoder.api.i18n import i18n
from midicoder.api.models import ApiResponse, ConfigSetRequest

router = APIRouter(prefix="/config", tags=["Config"])


def _settings():
    """Lazy-init SettingsManager."""
    from midicoder.storage.settings import SettingsManager
    mgr = SettingsManager()
    mgr.init()
    return mgr


def _read_all_settings() -> Dict[str, Any]:
    """Read all settings from SQLite."""
    return _settings().get_all()


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
    Lấy LLM config từ settings.db.
    """
    language = i18n.get_language_from_request(request)
    all_settings = _read_all_settings()

    # Extract llm.* keys
    llm = {
        k.replace("llm.", "", 1): v
        for k, v in all_settings.items()
        if k.startswith("llm.")
    }

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
    Ghi LLM config vào settings.db.

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

    # Write each LLM key to settings.db
    sm = _settings()
    for key, value in body.items():
        sm.set(f"llm.{key}", value)

    return ApiResponse(
        success=True,
        data={"saved": True},
        message="LLM config saved successfully",
        language=language,
    )


@router.post("/llm/test", response_model=ApiResponse)
async def test_llm_config(request: Request):
    """
    Test LLM connection với config hiện tại từ settings.db.
    """
    language = i18n.get_language_from_request(request)

    try:
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
    Liệt kê tất cả cấu hình từ settings.db.
    """
    language = i18n.get_language_from_request(request)
    config_data = _read_all_settings()
    return ApiResponse(
        success=True,
        data=config_data,
        message=i18n.translate("config.list_success", language),
        language=language,
    )


@router.get("/get/{key}", response_model=ApiResponse)
async def get_config(key: str, request: Request):
    """
    Lấy giá trị của một key config (từ SettingsManager + project config YAML).
    """
    language = i18n.get_language_from_request(request)
    from midicoder.pipeline.config import get_config
    cfg = get_config()
    value = cfg.get(key)
    return ApiResponse(
        success=True,
        data={"key": key, "value": value},
        message=i18n.translate("config.get_success", language),
        language=language,
    )


@router.post("/set", response_model=ApiResponse)
async def set_config(config: ConfigSetRequest, request: Request):
    """
    Đặt giá trị cho một key config (SettingsManager / project YAML).
    """
    language = i18n.get_language_from_request(request)
    from midicoder.pipeline.config import get_config
    cfg = get_config()
    cfg.set(config.key, config.value)
    return ApiResponse(
        success=True,
        data={"key": config.key, "value": config.value},
        message=i18n.translate("config.set_success", language),
        language=language,
    )


@router.post("/validate", response_model=ApiResponse)
async def validate_config(request: Request):
    """
    Validate cấu hình hiện tại — check LLM fields.
    """
    language = i18n.get_language_from_request(request)
    all_settings = _read_all_settings()

    llm = {
        k.replace("llm.", "", 1): v
        for k, v in all_settings.items()
        if k.startswith("llm.")
    }
    errors = _validate_llm_config(llm)

    if errors:
        return ApiResponse(
            success=False,
            data={"errors": errors},
            message="; ".join(errors),
            language=language,
        )

    return ApiResponse(
        success=True,
        data=None,
        message=i18n.translate("config.validate_success", language),
        language=language,
    )


@router.post("/reset", response_model=ApiResponse)
async def reset_config(request: Request):
    """
    Reset cấu hình về mặc định (settings.db).
    """
    language = i18n.get_language_from_request(request)
    _settings().reset(None)
    return ApiResponse(
        success=True,
        data=None,
        message=i18n.translate("config.reset_success", language),
        language=language,
    )