"""
Pytest configuration cho unit tests
Cung cấp fixtures và hooks chung cho tất cả tests
"""

import pytest
import sys
from pathlib import Path

# Thêm đường dẫn project vào sys.path để có thể import các module
project_root = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(project_root))

# Thêm đường dẫn api vào sys.path để import 'app' module được
api_root = project_root / "api"
sys.path.insert(0, str(api_root))


# =============================================================================
# Pytest Hooks
# =============================================================================

def pytest_configure(config):
    """
    Cấu hình pytest khi khởi động
    """
    # Thêm markers cho tests
    config.addinivalue_line(
        "markers", "happy_path: Test cho các trường hợp thành công"
    )
    config.addinivalue_line(
        "markers", "negative_case: Test cho các trường hợp lỗi"
    )
    config.addinivalue_line(
        "markers", "edge_case: Test cho các trường hợp biên"
    )
    config.addinivalue_line(
        "markers", "boundary_case: Test cho các trường hợp boundary"
    )


def pytest_collection_modifyitems(config, items):
    """
    Sửa đổi items khi collection
    Sắp xếp tests theo thứ tự: happy_path -> negative_case -> edge_case -> boundary_case
    """
    order = {"happy_path": 0, "negative_case": 1, "edge_case": 2, "boundary_case": 3}
    
    def get_order(item):
        for marker in item.own_markers:
            if marker.name in order:
                return order[marker.name]
        return 4  # Default order for unmarked tests
    
    items.sort(key=get_order)


# =============================================================================
# Shared Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def project_root():
    """
    Fixture trả về đường dẫn root của project
    """
    return Path(__file__).parent.parent.parent.resolve()


@pytest.fixture(scope="session")
def api_root(project_root):
    """
    Fixture trả về đường dẫn root của API
    """
    return project_root / "api"


@pytest.fixture(scope="session")
def tests_root(project_root):
    """
    Fixture trả về đường dẫn root của tests
    """
    return project_root / "tests"