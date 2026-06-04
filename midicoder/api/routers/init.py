"""
Router cho init — khởi tạo dự án mới
"""

from fastapi import APIRouter, Request

from midicoder.api.pipeline_bridge import pipeline_bridge
from midicoder.api.i18n import i18n
from midicoder.api.models import ApiResponse, InitRequest

router = APIRouter(prefix="/init", tags=["Init"])


@router.post("/", response_model=ApiResponse)
async def init_project(request_data: InitRequest, request: Request):
    """
    Khởi tạo dự án Midicoder mới.

    Creates .midicoder directory structure, sets up config files,
    and optionally configures LLM provider settings.

    Args:
        request_data: Init config (stack, LLM provider, working_dir, etc.)
        request: Request object để lấy ngôn ngữ

    Returns:
        ApiResponse: Kết quả init
    """
    language = i18n.get_language_from_request(request)

    # Build CLI args from request
    cli_args = []
    if request_data.non_interactive:
        cli_args.append("--non-interactive")
    if request_data.working_dir:
        cli_args.extend(["--working-dir", request_data.working_dir])
    if request_data.stack:
        cli_args.extend(["--stack", request_data.stack])
    if request_data.llm_high_provider:
        cli_args.extend(["--llm-high-provider", request_data.llm_high_provider])
    if request_data.llm_high_model:
        cli_args.extend(["--llm-high-model", request_data.llm_high_model])
    if request_data.llm_high_url:
        cli_args.extend(["--llm-high-url", request_data.llm_high_url])
    if request_data.llm_high_key_env:
        cli_args.extend(["--llm-high-key-env", request_data.llm_high_key_env])
    if request_data.llm_cheap_provider:
        cli_args.extend(["--llm-cheap-provider", request_data.llm_cheap_provider])
    if request_data.llm_cheap_model:
        cli_args.extend(["--llm-cheap-model", request_data.llm_cheap_model])
    if request_data.llm_cheap_url:
        cli_args.extend(["--llm-cheap-url", request_data.llm_cheap_url])
    if request_data.llm_cheap_key_env:
        cli_args.extend(["--llm-cheap-key-env", request_data.llm_cheap_key_env])

    # Call CLI wrapper — note: init doesn't have a dedicated wrapper method,
    # so we execute it directly via the CLI
    result = await pipeline_bridge.execute_command("init", cli_args)

    if result["success"]:
        return ApiResponse(
            success=True,
            data={
                "initialized": True,
                "working_dir": request_data.working_dir or None,
            },
            message=i18n.translate("init.success", language),
            language=language,
        )

    return ApiResponse(
        success=False,
        data=None,
        message=result.get("stderr", "Init failed"),
        language=language,
    )
