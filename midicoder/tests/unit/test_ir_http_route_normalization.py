from __future__ import annotations

from midicoder.ir.diagnostics.error_codes import ErrorReporter
from midicoder.ir.validation.validator import Validator


def test_normalize_http_routes_keeps_query_without_injecting_command() -> None:
    validator = Validator(ErrorReporter())
    payload = {
        "routes": [
            {
                "method": "GET",
                "path": "/api/v1/items",
                "query": "ListItems",
            }
        ]
    }

    normalized = validator._normalize_http_routes(payload)
    route = normalized["routes"][0]

    assert route.get("query") == "ListItems"
    assert "command" not in route

