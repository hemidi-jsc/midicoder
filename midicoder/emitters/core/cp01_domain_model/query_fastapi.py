"""
FastAPI Query Emitter cho Code Generation.

Emitter class để generate FastAPI query code từ Query definition:
- Generate query dataclass
- Generate handler
- Generate validator
- Generate guards
- Generate effects
- Generate output schema (Pydantic)
- Generate aggregation query (nếu có)

Theo SoT E07, template-based code generation với Jinja2.
Theo clarification Q6, rebuild templates để match Commands pattern.

Usage:
    from midicoder.emitters.core.cp01_domain_model import FastAPIQueryEmitter

    emitter = FastAPIQueryEmitter(stack_dir=Path("midicoder/stacks/fastapi/templates"))
    files = emitter.emit(query, output_dir=Path("app/queries/get_order"))

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from .query_models import Query, AggregationQuery


def _to_snake_case(name: str) -> str:
    """
    Chuyển PascalCase sang snake_case.
    
    Args:
        name: Tên cần chuyển
        
    Returns:
        Snake case string
    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class FastAPIQueryEmitter:
    """
    Emitter cho FastAPI Query code generation.

    Generate code cho:
    - Query class (dataclass)
    - Query handler
    - Query validator
    - Query guards
    - Query effects
    - Query output schema (Pydantic)
    - Aggregation query (nếu có)

    Usage:
        emitter = FastAPIQueryEmitter(stack_dir=Path("midicoder/stacks/fastapi/templates"))
        files = emitter.emit(query, output_dir=Path("app/queries/get_order"))
    """

    def __init__(self, stack_dir: Path) -> None:
        """
        Khởi tạo FastAPIQueryEmitter.

        Args:
            stack_dir: Đường dẫn đến templates directory
        """
        self._stack_dir = stack_dir
        self._env = Environment(
            loader=FileSystemLoader(str(stack_dir / "queries")),
            autoescape=True,
        )

    def emit(
        self,
        query: Query,
        output_dir: Path,
    ) -> dict[str, str]:
        """
        Emit query code files.

        Args:
            query: Query definition
            output_dir: Output directory

        Returns:
            Dict của file path -> content
        """
        files: dict[str, str] = {}

        # Prepare context
        context = self._prepare_context(query)

        # Generate files (snake_case naming)
        query_snake = _to_snake_case(query.id)

        files[f"{query_snake}.py"] = self._render(
            "query.py.jinja2", context
        )
        files[f"{query_snake}_handler.py"] = self._render(
            "query_handler.py.jinja2", context
        )
        files[f"{query_snake}_validator.py"] = self._render(
            "query_validator.py.jinja2", context
        )
        files[f"{query_snake}_guards.py"] = self._render(
            "query_guards.py.jinja2", context
        )
        files[f"{query_snake}_effects.py"] = self._render(
            "query_effects.py.jinja2", context
        )
        files[f"{query_snake}_output.py"] = self._render(
            "query_output.py.jinja2", context
        )
        files["__init__.py"] = self._render("__init__.py.jinja2", context)

        return files

    def emit_aggregation(
        self,
        query: AggregationQuery,
        output_dir: Path,
    ) -> dict[str, str]:
        """
        Emit aggregation query code files.

        Args:
            query: AggregationQuery definition
            output_dir: Output directory

        Returns:
            Dict của file path -> content
        """
        files: dict[str, str] = {}

        # Prepare context
        context = self._prepare_aggregation_context(query)

        # Generate files (snake_case naming)
        query_snake = _to_snake_case(query.id)

        files[f"{query_snake}.py"] = self._render(
            "query_aggregation.py.jinja2", context
        )
        files[f"{query_snake}_handler.py"] = self._render(
            "query_handler.py.jinja2", context
        )
        files[f"{query_snake}_guards.py"] = self._render(
            "query_guards.py.jinja2", context
        )
        files[f"{query_snake}_output.py"] = self._render(
            "query_output.py.jinja2", context
        )
        files["__init__.py"] = self._render("__init__.py.jinja2", context)

        return files

    def _prepare_context(self, query: Query) -> dict[str, Any]:
        """
        Prepare template context từ Query.

        Args:
            query: Query definition

        Returns:
            Context dict
        """
        return {
            "query": query,
            "query_id": query.id,
            "query_id_snake": _to_snake_case(query.id),
            "query_description": query.description,
            "reads_from": query.reads_from,
            "input_fields": query.input,
            "filters": query.filters,
            "pagination": query.pagination,
            "projection": query.projection,
            "sort": query.sort,
            "guards": query.guards,
            "effects": query.effects,
            "has_auth_guard": query.has_auth_guard(),
            "has_tenant_guard": query.has_tenant_guard(),
            "has_audit_effects": query.has_audit_effects(),
            "required_permissions": query.get_required_permissions(),
            "audit_actions": query.get_audit_actions(),
            "FilterOp": "FilterOp",
            "PaginationType": "PaginationType",
            "SortDirection": "SortDirection",
            "QueryGuardType": "QueryGuardType",
            "QueryEffectType": "QueryEffectType",
        }

    def _prepare_aggregation_context(self, query: AggregationQuery) -> dict[str, Any]:
        """
        Prepare template context từ AggregationQuery.

        Args:
            query: AggregationQuery definition

        Returns:
            Context dict
        """
        return {
            "query": query,
            "query_id": query.id,
            "query_id_snake": _to_snake_case(query.id),
            "query_description": query.description,
            "reads_from": query.reads_from,
            "aggregation": query.aggregation,
            "filters": query.filters,
            "pagination": query.pagination,
            "guards": query.guards,
            "effects": query.effects,
            "has_auth_guard": query.has_auth_guard(),
            "has_tenant_guard": query.has_tenant_guard(),
            "FilterOp": "FilterOp",
            "AggFunction": "AggFunction",
            "QueryGuardType": "QueryGuardType",
        }

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Render Jinja2 template.

        Args:
            template_name: Template name
            context: Template context

        Returns:
            Rendered content
        """
        template = self._env.get_template(template_name)
        return template.render(**context)

    def write_files(
        self,
        files: dict[str, str],
        output_dir: Path,
    ) -> None:
        """
        Write generated files to disk.

        Args:
            files: Dict of file path -> content
            output_dir: Output directory
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        for filename, content in files.items():
            file_path = output_dir / filename
            file_path.write_text(content, encoding="utf-8")