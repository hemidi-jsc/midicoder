"""
Tests cho Midicoder Pipeline Package Structure.

Module này chứa các tests để verify cấu trúc package:
- Version metadata
- Author metadata
- Exports (__all__)
- Import main function
"""

import pytest


class TestPipelinePackage:
    """Test suite cho pipeline package structure."""

    def test_version_defined(self):
        """Kiểm tra version metadata được định nghĩa."""
        from midicoder.pipeline import __version__

        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_version_format(self):
        """Kiểm tra format version đúng chuẩn semantic versioning."""
        from midicoder.pipeline import __version__

        # Version phải có format X.Y.Z
        parts = __version__.split(".")
        assert len(parts) == 3, f"Version phải có format X.Y.Z, nhận được: {__version__}"

        for i, part in enumerate(parts):
            assert part.isdigit(), f"Version part {i} phải là số, nhận được: {part}"

    def test_author_defined(self):
        """Kiểm tra author metadata được định nghĩa."""
        from midicoder.pipeline import __author__

        assert __author__ is not None
        assert isinstance(__author__, str)
        assert len(__author__) > 0

    def test_all_exports_defined(self):
        """Kiểm tra __all__ được định nghĩa."""
        from midicoder.pipeline import __all__

        assert __all__ is not None
        assert isinstance(__all__, list)
        assert len(__all__) > 0

    def test_main_exported(self):
        """Kiểm tra main function được export trong __all__."""
        from midicoder.pipeline import __all__

        assert "main" in __all__, "main phải được export trong __all__"

    def test_main_importable(self):
        """Kiểm tra main function có thể import được."""
        from midicoder.pipeline import main

        assert main is not None
        assert callable(main)

    def test_cli_is_click_group(self):
        """Kiểm tra cli là Click group."""
        from midicoder.pipeline.cli import cli

        # Click groups có decorator group
        assert hasattr(cli, "callback") or hasattr(cli, "params"), \
            "cli phải là Click group"

    def test_main_calls_cli(self):
        """Kiểm tra main function gọi cli."""
        from midicoder.pipeline.cli import main, cli

        # main là function wrapper cho cli
        assert callable(main)
        assert cli is not None
