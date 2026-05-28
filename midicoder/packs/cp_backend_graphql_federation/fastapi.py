# coding: utf-8
"""
FastAPI Emitter cho CP57: GraphQL Schema Federation.

Module này render Jinja2 templates để sinh GraphQL Federation code
cho FastAPI stack, bao gồm schema SDL, resolvers, federation service,
và gateway aggregation configuration.

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_backend_graphql_federation.parser import GraphQLIR
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


__all__ = [
    "FastAPIFederationEmitter",
    "GeneratedFile",
]


@dataclass
class GeneratedFile:
    """File đã generate.

    Attributes:
        path: Đường dẫn relative của file.
        content: Nội dung file.
    """
    path: str
    content: str


class FastAPIFederationEmitter:
    """Emitter cho FastAPI stack — CP57 GraphQL Schema Federation.

    Render templates từ `stacks/fastapi/cp_backend_graphql_federation/`
    để sinh GraphQL Federation code.
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến `stacks/fastapi/`.

        Raises:
            MidicoderError: Nếu template directory không tồn tại.
        """
        self.stack_dir = Path(stack_dir)
        self.template_dir = self.stack_dir / "cp_backend_graphql_federation"

        if not self.template_dir.exists():
            raise EM.raise_error(
                ErrorCode.MDC-BE04_FEDERATION_SERVICE_NOT_FOUND,
                reason=f"Template directory không tìm thấy: {self.template_dir}",
            )

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def emit(
        self,
        ir: GraphQLIR,
        output_dir: str | Path,
    ) -> list[GeneratedFile]:
        """Emit GraphQL Federation code cho FastAPI.

        Sinh các files:
        - graphql_schema.py (SDL schema definitions)
        - graphql_resolvers.py (resolver functions)
        - graphql_federation.py (federation service setup)
        - graphql_gateway.py (gateway aggregation config)

        Args:
            ir: GraphQLIR chứa federation config.
            output_dir: Đường dẫn output directory.

        Returns:
            Danh sách GeneratedFile.
        """
        output_dir = Path(output_dir)
        context = self._build_context(ir)
        files: list[GeneratedFile] = []

        templates = [
            ("graphql_schema.py.jinja2", "app/graphql/graphql_schema.py"),
            ("graphql_resolvers.py.jinja2", "app/graphql/graphql_resolvers.py"),
            ("graphql_federation.py.jinja2", "app/graphql/graphql_federation.py"),
            ("graphql_gateway.py.jinja2", "app/graphql/graphql_gateway.py"),
        ]

        for template_name, output_path in templates:
            if self._template_exists(template_name):
                content = self._render(template_name, context)
                files.append(GeneratedFile(path=output_path, content=content))

        return files

    def _build_context(self, ir: GraphQLIR) -> dict[str, Any]:
        """Xây dựng template context từ GraphQLIR."""
        services_list = [s.to_dict() for s in ir.services]
        types_list = [t.to_dict() for t in ir.types]
        resolvers_list = [r.to_dict() for r in ir.resolvers]
        gateway = ir.gateway_config.to_dict() if ir.gateway_config else None
        return {
            "services": services_list,
            "types": types_list,
            "resolvers": resolvers_list,
            "service_count": len(ir.services),
            "type_count": len(ir.types),
            "resolver_count": len(ir.resolvers),
            "gateway_config": gateway,
            "persisted_queries_enabled": (
                ir.gateway_config.persisted_queries_enabled if ir.gateway_config else False
            ),
            "introspection_enabled": (
                ir.gateway_config.introspection_enabled if ir.gateway_config else True
            ),
            "cors_origins": (
                ir.gateway_config.cors_origins if ir.gateway_config else []
            ),
            "rate_limit_rps": (
                ir.gateway_config.rate_limit_rps if ir.gateway_config else 100
            ),
        }

    def _template_exists(self, name: str) -> bool:
        return (self.template_dir / name).exists()

    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise EM.raise_error(
                ErrorCode.MDC-BE04_FEDERATION_SERVICE_NOT_FOUND,
                reason=f"Jinja2 template không tìm thấy: {template_name}",
            )
        except Exception as e:
            raise EM.raise_error(
                ErrorCode.MDC-BE04_INVALID_GATEWAY_CONFIG,
                reason=f"Render template thất bại {template_name}: {e}",
            )
