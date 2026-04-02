"""Cache for storing line information from YAML files.

This module provides a centralized cache for storing and retrieving
line number information for objects parsed from YAML files.
"""

from __future__ import annotations

from typing import Any

from .line_tracker import extract_line_info


class LineInfoCache:
    """Cache for storing line information from YAML files."""

    def __init__(self) -> None:
        """Initialize empty cache."""
        self._cache: dict[str, Any] = {}
        self._line_info: dict[str, dict[str, dict[str, int | None]]] = {}

    def store_raw_yaml(self, file_path: str, raw_yaml: Any) -> None:
        """
        Store raw YAML data with line information.

        Args:
            file_path: Relative path to the file
            raw_yaml: Raw YAML data from ruamel.yaml
        """
        self._cache[file_path] = raw_yaml
        self._extract_line_info(file_path, raw_yaml)

    def _extract_line_info(self, file_path: str, raw_yaml: Any) -> None:
        """Extract line information from raw YAML."""
        if file_path not in self._line_info:
            self._line_info[file_path] = {}

        # Extract line info for top-level collections
        if isinstance(raw_yaml, dict):
            for key in [
                "entities",
                "value_objects",
                "enums",
                "errors",
                "events",
                "commands",
                "queries",
                "projections",
                "workflows",
                "routes",
                "rules",
                "scenarios",
                "policies",
            ]:
                if key in raw_yaml:
                    collection = raw_yaml[key]
                    if isinstance(collection, list):
                        for idx, item in enumerate(collection):
                            if isinstance(item, dict) and "id" in item:
                                item_id = item["id"]
                                line_info = extract_line_info(collection, idx)
                                self._line_info[file_path][item_id] = line_info
                            elif key == "routes" and isinstance(item, dict):
                                route_id = self._route_id_from_item(item)
                                if route_id:
                                    line_info = extract_line_info(collection, idx)
                                    self._line_info[file_path][route_id] = line_info
                                path = item.get("path")
                                if path:
                                    line_info = extract_line_info(collection, idx)
                                    self._line_info[file_path][str(path)] = line_info

            # Handle nested Access Policy structures under "access"
            access = raw_yaml.get("access")
            if isinstance(access, dict):
                for access_key in ["roles", "permissions", "bindings"]:
                    access_collection = access.get(access_key)
                    if not isinstance(access_collection, list):
                        continue
                    for idx, item in enumerate(access_collection):
                        if not isinstance(item, dict):
                            continue
                        item_id = item.get("id")
                        if not item_id:
                            continue
                        line_info = extract_line_info(access_collection, idx)
                        self._line_info[file_path][item_id] = line_info

            # Handle nested GraphQL API structures under "api"
            api = raw_yaml.get("api")
            if isinstance(api, dict):
                for gql_key in ["types", "queries", "mutations"]:
                    gql_collection = api.get(gql_key)
                    if isinstance(gql_collection, list):
                        for idx, item in enumerate(gql_collection):
                            if isinstance(item, dict):
                                item_id = item.get("name") or item.get("id")
                                if not item_id:
                                    continue
                                line_info = extract_line_info(gql_collection, idx)
                                self._line_info[file_path][item_id] = line_info

    def get_line_info(self, file_path: str, item_id: str) -> dict[str, int | None]:
        """
        Get line information for an item.

        Args:
            file_path: Relative path to the file
            item_id: ID of the item

        Returns:
            Dictionary with 'start', 'end', 'single' keys, or empty dict if not found
        """
        if file_path in self._line_info:
            return self._line_info[file_path].get(item_id, {})
        return {}

    def _route_id_from_item(self, item: dict[str, Any]) -> str | None:
        method = item.get("method")
        path = item.get("path")
        if not method or not path:
            return None
        route_id = f"{str(method).lower()}_{str(path).replace('/', '_').replace('{', '').replace('}', '').strip('_')}"
        return route_id or None

    def get_raw_yaml(self, file_path: str) -> Any | None:
        """Get raw YAML data for a file."""
        return self._cache.get(file_path)

    def has_file(self, file_path: str) -> bool:
        """Check if file is in cache."""
        return file_path in self._cache


# Global cache instance
_global_cache = LineInfoCache()


def get_cache() -> LineInfoCache:
    """Get the global line info cache instance."""
    return _global_cache


def store_raw_yaml(file_path: str, raw_yaml: Any) -> None:
    """Store raw YAML data in global cache."""
    _global_cache.store_raw_yaml(file_path, raw_yaml)


def get_line_info(file_path: str, item_id: str) -> dict[str, int | None]:
    """Get line information from global cache."""
    return _global_cache.get_line_info(file_path, item_id)


__all__ = [
    "LineInfoCache",
    "get_cache",
    "store_raw_yaml",
    "get_line_info",
]
