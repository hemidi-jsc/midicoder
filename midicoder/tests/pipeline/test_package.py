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

    # === Tests cho new metadata (P1-000-A) ===

    def test_description_defined(self):
        """Kiểm tra __description__ metadata được định nghĩa."""
        from midicoder.pipeline import __description__

        assert __description__ is not None
        assert isinstance(__description__, str)
        assert len(__description__) > 0

    def test_package_name_defined(self):
        """Kiểm tra __package_name__ metadata được định nghĩa."""
        from midicoder.pipeline import __package_name__

        assert __package_name__ is not None
        assert isinstance(__package_name__, str)
        assert __package_name__ == "midicoder.pipeline"

    # === Tests cho constants (P1-000-A) ===

    def test_package_name_constant(self):
        """Kiểm tra PACKAGE_NAME constant."""
        from midicoder.pipeline import PACKAGE_NAME

        assert PACKAGE_NAME == "midicoder"

    def test_default_version_constant(self):
        """Kiểm tra DEFAULT_VERSION constant."""
        from midicoder.pipeline import DEFAULT_VERSION

        assert DEFAULT_VERSION == "v1.0.0"

    def test_default_config_file_constant(self):
        """Kiểm tra DEFAULT_CONFIG_FILE constant."""
        from midicoder.pipeline import DEFAULT_CONFIG_FILE

        assert DEFAULT_CONFIG_FILE == "midicoder.json"

    def test_default_workspace_dir_constant(self):
        """Kiểm tra DEFAULT_WORKSPACE_DIR constant."""
        from midicoder.pipeline import DEFAULT_WORKSPACE_DIR

        assert DEFAULT_WORKSPACE_DIR == ".midicoder"

    def test_brief_filename_constant(self):
        """Kiểm tra BRIEF_FILENAME constant."""
        from midicoder.pipeline import BRIEF_FILENAME

        assert BRIEF_FILENAME == "brief.md"

    # === Tests cho __all__ completeness ===

    def test_all_exports_contain_metadata(self):
        """Kiểm tra __all__ chứa đầy đủ metadata exports."""
        from midicoder.pipeline import __all__

        expected_metadata = [
            "__version__",
            "__author__",
            "__description__",
            "__package_name__",
        ]
        for meta in expected_metadata:
            assert meta in __all__, f"{meta} phải được export trong __all__"

    def test_all_exports_contain_constants(self):
        """Kiểm tra __all__ chứa đầy đủ constants exports."""
        from midicoder.pipeline import __all__

        expected_constants = [
            "PACKAGE_NAME",
            "DEFAULT_VERSION",
            "DEFAULT_CONFIG_FILE",
            "DEFAULT_WORKSPACE_DIR",
            "BRIEF_FILENAME",
        ]
        for const in expected_constants:
            assert const in __all__, f"{const} phải được export trong __all__"

    def test_all_exports_contain_main(self):
        """Kiểm tra __all__ chứa main function."""
        from midicoder.pipeline import __all__

        assert "main" in __all__

    def test_all_exports_count(self):
        """Kiểm tra số lượng exports trong __all__."""
        from midicoder.pipeline import __all__

        # 4 metadata + 5 constants + 1 main = 10
        assert len(__all__) == 10, f"__all__ phải chứa 10 exports, nhận được: {len(__all__)}"
