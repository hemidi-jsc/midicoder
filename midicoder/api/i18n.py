"""
Hỗ trợ đa ngôn ngữ (i18n) cho API
Ngôn ngữ mặc định: Tiếng Việt (vi)
Ngôn ngữ thứ 2: Tiếng Anh (en)
"""

from typing import Dict, Any, Optional
from fastapi import Request
from fastapi.responses import JSONResponse


# Từ điển dịch cho Tiếng Việt (mặc định)
VI_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # Common messages
    "common.success": "Thành công",
    "common.error": "Lỗi",
    "common.loading": "Đang xử lý...",
    "common.processing": "Đang xử lý",
    "common.completed": "Hoàn thành",
    "common.failed": "Thất bại",
    "common.canceled": "Đã hủy",
    
    # API responses
    "api.cli_executing": "Đang thực thi lệnh CLI",
    "api.cli_completed": "Lệnh CLI đã hoàn thành",
    "api.cli_failed": "Lệnh CLI thất bại",
    "api.cli_timeout": "Lệnh CLI hết thời gian chờ",
    "api.cli_error": "Lỗi khi thực thi lệnh CLI",
    
    # Config commands
    "config.get_success": "Đã lấy cấu hình thành công",
    "config.set_success": "Đã cập nhật cấu hình thành công",
    "config.list_success": "Đã lấy danh sách cấu hình thành công",
    "config.validate_success": "Cấu hình hợp lệ",
    "config.validate_failed": "Cấu hình không hợp lệ",
    "config.reset_success": "Đã đặt lại cấu hình về mặc định",
    
    # Init commands
    "init.success": "Đã khởi tạo dự án thành công",
    "init.already_initialized": "Dự án đã được khởi tạo",
    
    # Version commands
    "version.create_success": "Đã tạo phiên bản thành công",
    "version.exists": "Phiên bản đã tồn tại",
    "version.not_found": "Không tìm thấy phiên bản",
    
    # Brief commands
    "brief.analyze_start": "Đang phân tích brief",
    "brief.analyze_success": "Đã phân tích brief thành công",
    "brief.analyze_failed": "Phân tích brief thất bại",
    "brief.analyze_blocked": "Brief status là '{status}', chỉ phân tích được khi status = draft",
    "brief.rewrite_start": "Đang viết lại brief",
    "brief.rewrite_success": "Đã viết lại brief thành công",
    "brief.saved": "Đã lưu brief thành công",
    "brief.updated": "Đã cập nhật brief thành công",
    "brief.saveFailed": "Không thể lưu brief",
    "brief.emptyContent": "Brief không được để trống",
    "brief.noActiveProject": "Không có project đang hoạt động",
    "brief.notFound": "Không tìm thấy brief cho version",
    "brief.freezeError": "Không thể đóng băng brief",
    "brief.freezedMsg": "Brief đã được đóng băng",
    "brief.freezedBlocked": "Brief đã được đóng băng, không thể chỉnh sửa",
    "brief.revisionNotFound": "Không tìm thấy revision",
    "brief.ok": "OK",
    "brief.llmFailed": "Phân tích LLM thất bại: {detail}",
    "brief.clarified": "Đã làm rõ yêu cầu (Round {round})",
    "brief.noAnswers": "Không có câu trả lời nào để lưu",
    "brief.maxRoundsReached": "Đã hết {max_rounds} vòng làm rõ, bạn vẫn có thể tiếp tục sang Contract",
    "brief.clarify_failed": "Không thể lưu clarifications",    
    # Contract commands
    "contract.gen_start": "Đang tạo hợp đồng DSL",
    "contract.gen_success": "Đã tạo hợp đồng DSL thành công",
    "contract.gen_failed": "Tạo hợp đồng DSL thất bại",
    "contract.check_start": "Đang kiểm tra hợp đồng",
    "contract.check_success": "Hợp đồng hợp lệ",
    "contract.check_failed": "Hợp đồng không hợp lệ",
    
    # IR commands
    "ir.build_start": "Đang xây dựng MIR",
    "ir.build_success": "Đã xây dựng MIR thành công",
    "ir.build_failed": "Xây dựng MIR thất bại",
    
    # Code commands
    "code.build_start": "Đang tạo kế hoạch code",
    "code.build_success": "Đã tạo kế hoạch code thành công",
    "code.gen_start": "Đang tạo code",
    "code.gen_success": "Đã tạo code thành công",
    "code.apply_start": "Đang áp dụng code",
    "code.apply_success": "Đã áp dụng code thành công",
    
    # Runtime commands
    "runtime.test_start": "Đang test runtime",
    "runtime.test_success": "Test runtime thành công",
    "runtime.test_failed": "Test runtime thất bại",
    "runtime.fix_start": "Đang sửa lỗi runtime",
    "runtime.fix_success": "Đã sửa lỗi runtime thành công",
    
    # Errors
    "error.not_found": "Không tìm thấy",
    "error.invalid_request": "Yêu cầu không hợp lệ",
    "error.internal_server": "Lỗi server bên trong",
    "error.unauthorized": "Chưa được xác thực",
    "error.forbidden": "Không có quyền",
    "error.timeout": "Hết thời gian chờ",
    "error.command_failed": "Lệnh thất bại",
    
    # Status
    "status.pending": "Đang chờ",
    "status.running": "Đang chạy",
    "status.completed": "Hoàn thành",
    "status.failed": "Thất bại",
}

# Từ điển dịch cho Tiếng Anh
EN_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # Common messages
    "common.success": "Success",
    "common.error": "Error",
    "common.loading": "Loading...",
    "common.processing": "Processing",
    "common.completed": "Completed",
    "common.failed": "Failed",
    "common.canceled": "Canceled",
    
    # API responses
    "api.cli_executing": "Executing CLI command",
    "api.cli_completed": "CLI command completed",
    "api.cli_failed": "CLI command failed",
    "api.cli_timeout": "CLI command timed out",
    "api.cli_error": "Error executing CLI command",
    
    # Config commands
    "config.get_success": "Configuration retrieved successfully",
    "config.set_success": "Configuration updated successfully",
    "config.list_success": "Configuration list retrieved successfully",
    "config.validate_success": "Configuration is valid",
    "config.validate_failed": "Configuration is invalid",
    "config.reset_success": "Configuration reset to defaults",
    
    # Init commands
    "init.success": "Project initialized successfully",
    "init.already_initialized": "Project already initialized",
    
    # Version commands
    "version.create_success": "Version created successfully",
    "version.exists": "Version already exists",
    "version.not_found": "Version not found",
    
    # Brief commands
    "brief.analyze_start": "Analyzing brief",
    "brief.analyze_success": "Brief analyzed successfully",
    "brief.analyze_failed": "Brief analysis failed",
    "brief.analyze_blocked": "Brief status is '{status}', can only analyze when status = draft",
    "brief.rewrite_start": "Rewriting brief",
    "brief.rewrite_success": "Brief rewritten successfully",
    "brief.saved": "Brief saved successfully",
    "brief.updated": "Brief updated successfully",
    "brief.saveFailed": "Failed to save brief",
    "brief.emptyContent": "Brief content cannot be empty",
    "brief.noActiveProject": "No active project",
    "brief.notFound": "Brief not found for version",
    "brief.freezeError": "Failed to freeze brief",
    "brief.freezedMsg": "Brief has been freezed",
    "brief.freezedBlocked": "Brief is already freezed, cannot edit",
    "brief.revisionNotFound": "Revision not found",
    "brief.ok": "OK",
    "brief.llmFailed": "LLM analysis failed: {detail}",
    "brief.clarified": "Requirements clarified (Round {round})",
    "brief.noAnswers": "No answers to save",
    "brief.maxRoundsReached": "Reached {max_rounds} clarification rounds, you can still proceed to Contract",
    "brief.clarify_failed": "Failed to save clarifications",

    # Contract commands
    "contract.gen_start": "Generating DSL contract",
    "contract.gen_success": "DSL contract generated successfully",
    "contract.gen_failed": "DSL contract generation failed",
    "contract.check_start": "Checking contract",
    "contract.check_success": "Contract is valid",
    "contract.check_failed": "Contract is invalid",
    
    # IR commands
    "ir.build_start": "Building MIR",
    "ir.build_success": "MIR built successfully",
    "ir.build_failed": "MIR build failed",
    
    # Code commands
    "code.build_start": "Building code plan",
    "code.build_success": "Code plan built successfully",
    "code.gen_start": "Generating code",
    "code.gen_success": "Code generated successfully",
    "code.apply_start": "Applying code",
    "code.apply_success": "Code applied successfully",
    
    # Runtime commands
    "runtime.test_start": "Testing runtime",
    "runtime.test_success": "Runtime test passed",
    "runtime.test_failed": "Runtime test failed",
    "runtime.fix_start": "Fixing runtime errors",
    "runtime.fix_success": "Runtime errors fixed successfully",
    
    # Errors
    "error.not_found": "Not found",
    "error.invalid_request": "Invalid request",
    "error.internal_server": "Internal server error",
    "error.unauthorized": "Unauthorized",
    "error.forbidden": "Forbidden",
    "error.timeout": "Timeout",
    "error.command_failed": "Command failed",
    
    # Status
    "status.pending": "Pending",
    "status.running": "Running",
    "status.completed": "Completed",
    "status.failed": "Failed",
}


class I18n:
    """
    Lớp hỗ trợ i18n
    Lưu trữ và lấy các bản dịch
    """
    
    def __init__(self):
        self.translations = {
            "vi": VI_TRANSLATIONS,
            "en": EN_TRANSLATIONS,
        }
        self.default_language = "vi"
    
    def get_language_from_request(self, request: Request) -> str:
        """
        Lấy ngôn ngữ từ request
        Ưu tiên: Header X-Lang > Header X-Language > Query param lang > Mặc định (vi)
        """
        # Lấy header từ request headers
        # FastAPI stores headers in lowercase
        x_lang = request.headers.get("x-lang") or request.headers.get("x-language")
        
        # Ưu tiên header
        if x_lang and x_lang in self.translations:
            return x_lang
        
        # Query param
        lang = request.query_params.get("lang")
        if lang and lang in self.translations:
            return lang
        
        # Mặc định
        return self.default_language
    
    def translate(self, key: str, language: str = "vi", **kwargs) -> str:
        """
        Dịch một key sang ngôn ngữ chỉ định

        Args:
            key: Key của message (ví dụ: "common.success")
            language: Ngôn ngữ đích (vi, en)
            **kwargs: Các tham số để format string

        Returns:
            Message đã dịch
        """
        if language not in self.translations:
            language = self.default_language

        message = self.translations[language].get(key, key)

        # Format string nếu có kwargs
        if kwargs:
            try:
                message = message.format(**kwargs)
            except (KeyError, ValueError):
                pass

        return message

    def t(self, key: str, language: str = None, **kwargs) -> str:
        """Alias ngắn của translate(). Nếu không truyền language, dùng mặc định."""
        return self.translate(key, language or self.default_language, **kwargs)

    def get_all_languages(self) -> list[str]:
        """Trả về danh sách ngôn ngữ được hỗ trợ"""
        return list(self.translations.keys())


# Instance toàn cục
i18n = I18n()