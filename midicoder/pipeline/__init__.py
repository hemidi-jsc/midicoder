"""
Midicoder Pipeline Module.

Module này chứa các lệnh CLI chính cho pipeline biên dịch:
- init: Khởi tạo workspace
- brief: Phân tích yêu cầu
- contract: Tạo và kiểm tra contracts
- ir: Build MIR
- code: Plan, gen, apply code
- preview: Start local preview

E00-E07: Core Pipeline Commands
"""

__version__ = "1.0.0"
__author__ = "Midicoder Team"

from midicoder.pipeline.cli import main

__all__ = ["main"]