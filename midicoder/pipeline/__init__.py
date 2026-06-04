"""
Midicoder Pipeline Module.

Core pipeline functions for the Midicoder WebGUI:
- init: Initialize workspace (.midicoder/)
- brief: Brief analysis
- contract: Contract generation and validation
- ir: Build MIR from contracts
- code: Plan, gen, apply code
- preview: Docker preview
- version: Version management
- index: Codebase indexing

All functions are called via pipeline_bridge.py from the backend.
"""

# === Package Metadata ===
__version__ = "1.0.0"
__author__ = "Midicoder Team"
__description__ = "Midicoder Pipeline - WebGUI Backend"
__package_name__ = "midicoder.pipeline"

# === Package Constants ===
PACKAGE_NAME = "midicoder"
DEFAULT_VERSION = "v1.0.0"
DEFAULT_CONFIG_FILE = "midicoder.json"
DEFAULT_WORKSPACE_DIR = ".midicoder"
BRIEF_FILENAME = "brief.md"

__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "__package_name__",
    "PACKAGE_NAME",
    "DEFAULT_VERSION",
    "DEFAULT_CONFIG_FILE",
    "DEFAULT_WORKSPACE_DIR",
    "BRIEF_FILENAME",
]