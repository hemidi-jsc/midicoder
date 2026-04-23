"""
Midicoder Pipeline Module - Core CLI Pipeline.

Module này chứa các lệnh CLI chính cho pipeline biên dịch midicoder v1:
- init: Khởi tạo workspace (.midicoder/)
- brief: Phân tích yêu cầu (analyze, clarify, list, library)
- contract: Tạo và kiểm tra contracts (gen, check, repair)
- ir: Build MIR từ contracts
- code: Plan, gen, apply code (backend/frontend)
- preview: Start local preview (Docker)
- version: Quản lý versions
- index: Index codebase

E00-E07: Core Pipeline Commands
E18-E19: Infrastructure & Preview Support
"""

# === Package Metadata ===
__version__ = "1.0.0"
__author__ = "Midicoder Team"
__description__ = "Midicoder CLI Pipeline - Compiler for Software Requirements"
__package_name__ = "midicoder.pipeline"

# === Package Constants ===
PACKAGE_NAME = "midicoder"
DEFAULT_VERSION = "v1.0.0"
DEFAULT_CONFIG_FILE = "midicoder.json"
DEFAULT_WORKSPACE_DIR = ".midicoder"
BRIEF_FILENAME = "brief.md"

# === Public API ===
from midicoder.pipeline.cli import main

__all__ = [
    # Metadata
    "__version__",
    "__author__",
    "__description__",
    "__package_name__",
    # Constants
    "PACKAGE_NAME",
    "DEFAULT_VERSION",
    "DEFAULT_CONFIG_FILE",
    "DEFAULT_WORKSPACE_DIR",
    "BRIEF_FILENAME",
    # Public API
    "main",
]