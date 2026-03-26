from __future__ import annotations

from typing import Any, TYPE_CHECKING

from midicoder.llm.adapters.base import BaseAdapter

if TYPE_CHECKING:
    from midicoder.llm.client import LlmConfig


class VertexPartnerAdapter(BaseAdapter):
    provider = "vertex_partner"

    def model_identifier(self, config: LlmConfig) -> str:
        return self._with_prefix(config.model, "vertex_ai")

    def completion_params(self, config: LlmConfig) -> dict[str, Any]:
        params: dict[str, Any] = {}

        project = config.vertex_project
        location = config.vertex_location

        if project:
            params["vertex_project"] = project
        if location:
            params["vertex_location"] = location

        return params
