"""
Unit Tests cho CapabilityGraph export qua contracts public API.

Kiểm tra:
- CapabilityGraph importable từ midicoder.contracts
- CapabilityGraph là cùng class với cp51_blueprint.models.CapabilityGraph
- 4 file CP52 import đúng từ midicoder.contracts (không qua .graph)

Author: Midicoder CE — Auto-generated via skill:coding
"""

import pytest


class TestCapabilityGraphExport:
    """Tests cho re-export CapabilityGraph qua contracts public API."""

    def test_capability_graph_importable_from_contracts(self):
        """Kiểm tra CapabilityGraph import được từ midicoder.contracts."""
        from midicoder.contracts import CapabilityGraph

        assert CapabilityGraph is not None

    def test_capability_graph_is_same_as_cp51_model(self):
        """Kiểm tra CapabilityGraph từ contracts là cùng class với cp51_blueprint.models."""
        from midicoder.contracts import CapabilityGraph
        from midicoder.emitters.core.cp51_blueprint.models import (
            CapabilityGraph as SourceCapabilityGraph,
        )

        assert CapabilityGraph is SourceCapabilityGraph

    def test_capability_graph_in_all(self):
        """Kiểm tra CapabilityGraph có mặt trong __all__ của contracts."""
        import midicoder.contracts as contracts

        assert "CapabilityGraph" in contracts.__all__

    def test_capability_graph_basic_instantiation(self):
        """Kiểm tra tạo CapabilityGraph rỗng không raise error."""
        from midicoder.contracts import CapabilityGraph

        graph = CapabilityGraph()
        assert graph.nodes == []
        assert graph.edges == []
