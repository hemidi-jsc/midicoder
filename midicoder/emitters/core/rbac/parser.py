"""
CP04: RBAC & Policy Engine — DSL Parser.

Parser cho RBAC DSL nodes (Roles + Guards/Policies) từ ProjectionTree.
Tất cả comments bằng tiếng Việt.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any, List, Optional

from midicoder.emitters.core.rbac.models import Role, PolicyRule, RBACConfig


class RBACParser:
    """
    RBAC Parser — Parse DSL YAML nodes thành RBAC models.

    Parser chuyển đổi DSL YAML (Role nodes + Guard nodes) thành:
    - Role objects (từ emitters.core.rbac.models)
    - PolicyRule objects (từ emitters.core.rbac.models)
    - RBACConfig (tổng hợp roles + policies)
    """

    def parse(self, raw: str) -> list[Role | PolicyRule]:
        """
        Parse DSL YAML string thành danh sách Role/PolicyRule.

        Args:
            raw: DSL YAML string raw

        Returns:
            Danh sách Role hoặc PolicyRule instances
        """
        import yaml

        data = yaml.safe_load(raw)
        if not data:
            return []

        result: list[Role | PolicyRule] = []

        # Parse roles
        for role_data in data.get("roles", []):
            role = self._parse_role(role_data)
            result.append(role)

        # Parse policies (guards)
        for policy_data in data.get("guards", []):
            if policy_data.get("type") in ("rbac", "policy"):
                rule = self._parse_policy(policy_data)
                result.append(rule)

        return result

    def parse_config(self, raw: str) -> RBACConfig:
        """
        Parse DSL YAML thành RBACConfig hoàn chỉnh.

        Args:
            raw: DSL YAML string raw

        Returns:
            RBACConfig với roles và policies
        """
        items = self.parse(raw)
        roles = [item for item in items if isinstance(item, Role)]
        policies = [item for item in items if isinstance(item, PolicyRule)]
        return RBACConfig(roles=roles, policies=policies)

    def _parse_role(self, data: dict[str, Any]) -> Role:
        """
        Parse một role node thành Role object.

        Args:
            data: Dict data của role

        Returns:
            Role instance
        """
        return Role(
            name=data.get("id", data.get("name", "")),
            description=data.get("description"),
            permissions=data.get("permissions", []),
            parent_roles=data.get("parent_roles", data.get("parent_role", [])),
        )

    def _parse_policy(self, data: dict[str, Any]) -> PolicyRule:
        """
        Parse một guard node thành PolicyRule.

        Args:
            data: Dict data của guard

        Returns:
            PolicyRule instance
        """
        return PolicyRule(
            id=data.get("id", ""),
            effect=data.get("effect", "allow"),
            condition=data.get("condition", ""),
            resource_type=data.get("resource_type"),
            actions=data.get("actions", []),
        )