"""
CLI Runner - wrapper để chạy midicoder CLI từ WebGUI backend.
Patch prompt_toolkit để không crash khi không có Windows console.
"""
import sys

# Patch sys.platform TRƯỚC KHI bất kỳ import nào
# prompt_toolkit.output kiểm tra sys.platform == "win32" và cố đọc console handle
sys.platform = "linux"

import os
os.environ["PYTHONUTF8"] = "1"
os.environ["NO_COLOR"] = "1"

# Thêm PYTHONPATH để tìm module midicoder
midicoder_root = str(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if midicoder_root not in sys.path:
    sys.path.insert(0, midicoder_root)

# Import và chạy CLI
from midicoder.pipeline.cli import cli

if __name__ == "__main__":
    cli(sys.argv[1:])
