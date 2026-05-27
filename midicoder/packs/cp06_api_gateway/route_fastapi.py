# coding: utf-8
"""
FastAPI Route Emitter - Sinh route files cho FastAPI backend.

Module nay chua cac emitter de generate:
- FastAPIRouteEmitter: HTTP REST routes (Jinja2 templates)
- FastAPIGraphQLResolverEmitter: GraphQL
- FastAPIWebhookEmitter: Webhooks

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from jinja2 import Environment, DictLoader

from midicoder.packs.cp06_api_gateway.models import (
    Route,
    RouteCollection,
    RouteAuthConfig,
    GraphQLResolver,
    WebhookHandler,
    HttpMethod,
)

# Jinja2 template cho HTTP routes
_HTTP_ROUTE_TEMPLATE = '''\
"""
Route module cho {{ tag }} endpoints.

Tu dong sinh boi Midicoder CE - KHONG chinh sua thu con.

CP06: API Gateway & Service Mesh
KPI-029: Tenant Isolation
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Request, status
from pydantic import BaseModel

# KPI-029: Import tenant context
from app.core.security.tenant_context import get_tenant_id

{% if has_auth %}
from app.core.security.auth import get_current_user
from app.models.user import User
{% endif %}

# Import command/query handlers
{% for route in routes %}
{% if route.handler_type == "command" %}
from app.commands.{{ route.handler_id | replace("-", "_") | lower }}.{{ route.handler_id | replace("-", "_") | lower }}_handler import {{ route.handler_id }}Handler as {{ route.handler_id }}CmdHandler
{% elif route.handler_type == "query" %}
from app.queries.{{ route.handler_id | replace("-", "_") | lower }}.{{ route.handler_id | replace("-", "_") | lower }}_handler import {{ route.handler_id }}Handler as {{ route.handler_id }}QryHandler
{% endif %}
{% endfor %}

router = APIRouter(
    prefix="{{ prefix }}",
    tags=["{{ tag }}"],
)

{% for route in routes %}


# {{ route.method }} {{ route.path }}
{% if route.is_write_operation %}

class {{ route.id }}Request(BaseModel):
    """Request schema cho {{ route.description or route.id }}."""
{% for fld in route.request_schema %}
    {{ fld.name }}: {{ fld.field_type }}{% if not fld.required %} = None{% endif %}
{% endfor %}

{% endif %}

class {{ route.id }}Response(BaseModel):
    """Response schema cho {{ route.description or route.id }}."""
{% for fld in route.response_schema %}
    {{ fld.name }}: {{ fld.field_type }}{% if not fld.required %} = None{% endif %}
{% endfor %}
    tenant_id: Optional[str] = None  # KPI-029


@router.{{ route.method | lower }}(
    "{{ route.path }}",
    response_model={{ route.id }}Response,
    status_code={{ route.response_status }},
    summary="{{ route.description or (route.method ~ " " ~ route.path) }}",
)
async def {{ route.id | replace("-", "_") | lower }}(
{% for param in route.path_params %}
    {{ param.name }}: {{ param.param_type }} = Path(...),
{% endfor %}
{% for param in route.query_params %}
    {{ param.name }}: Optional[{{ param.param_type }}] = Query(None),
{% endfor %}
{% if route.is_write_operation %}
    body: {{ route.id }}Request = Body(...),
{% endif %}
{% if route.requires_auth %}
    current_user: User = Depends(get_current_user),
{% endif %}
    tenant_id: Optional[str] = Depends(get_tenant_id),
    request: Request = None,
) -> {{ route.id }}Response:
    """
    {{ route.description or (route.method ~ " " ~ route.path) }}

    KPI-029: Tenant isolation qua tenant_id dependency.
    """
    try:
        {% if route.requires_auth and route.auth and route.auth.tenant_scoped %}
        # KPI-029: Validate tenant scope
        if tenant_id and current_user.tenant_id and tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="KPI-029: Tenant mismatch",
            )
        {% endif %}

        # Build handler kwargs
        handler_kwargs: Dict[str, Any] = {
{% for param in route.path_params %}
            "{{ param.name }}": {{ param.name }},
{% endfor %}
{% for param in route.query_params %}
            "{{ param.name }}": {{ param.name }},
{% endfor %}
            "tenant_id": tenant_id,
{% if route.requires_auth %}
            "user_id": current_user.id,
{% endif %}
        }

        # Call command/query handler
{% if route.handler_type == "command" %}
        # Command handler - write operation voi side effects
        handler = {{ route.handler_id }}CmdHandler()
        result = await handler.handle(
            command_body=body.dict() if body else {},
            **handler_kwargs,
        )
{% elif route.handler_type == "query" %}
        # Query handler - read operation
        handler = {{ route.handler_id }}QryHandler()
        result = await handler.execute(**handler_kwargs)
{% else %}
        # Side effect trigger - goi event handler
        from app.core.event.event_bus import get_event_bus
        event_bus = get_event_bus()
        result = await event_bus.publish("{{ route.handler_id }}", handler_kwargs)
{% endif %}

        return {{ route.id }}Response(
{% for fld in route.response_schema %}
            {{ fld.name }}=result.get("{{ fld.name }}"),
{% endfor %}
            tenant_id=tenant_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Loi xu ly {{ route.id }}: {str(e)}",
        )

{% endfor %}
'''


# ===========================================================================
# Helper: convert Route dataclass to dict for Jinja2 access
# ===========================================================================

def _route_to_template_dict(route: Route) -> dict[str, Any]:
    """Chuyen Route sang dict de Jinja2 co the truy cap duoc methods."""
    d = asdict(route)
    # Add computed properties
    d["is_write_operation"] = route.is_write_operation()
    d["requires_auth"] = route.requires_auth()
    # HttpMethod enum → string
    d["method"] = route.method.value if isinstance(route.method, HttpMethod) else route.method
    return d


# ===========================================================================
# FastAPI Route Emitter
# ===========================================================================


@dataclass
class FastAPIRouteEmitter:
    """Emitter de sinh FastAPI route files tu RouteCollection su dung Jinja2 templates."""

    def emit(
        self,
        collection: RouteCollection,
        output_dir: Path,
    ) -> dict[str, str]:
        """Emit FastAPI route files tu RouteCollection."""
        files: dict[str, str] = {}
        routes_dir = output_dir / "routes"
        routes_dir.mkdir(parents=True, exist_ok=True)

        if not collection.routes:
            return files

        groups = collection.group_routes_by_tag()
        if not groups:
            groups = {"default": collection.routes}

        tags_list: list[str] = []

        for tag, routes in groups.items():
            tags_list.append(tag)
            router_filename = f"{tag}_routes.py"
            router_path = routes_dir / router_filename

            # Convert routes to dicts for Jinja2
            route_dicts = [_route_to_template_dict(r) for r in routes]
            has_auth = any(r["requires_auth"] for r in route_dicts)

            template_env = Environment(loader=DictLoader({"http_route": _HTTP_ROUTE_TEMPLATE}))
            template = template_env.get_template("http_route")
            content = template.render(
                tag=tag,
                routes=route_dicts,
                has_auth=has_auth,
                prefix="/api",
            )

            # Normalize path separators for cross-platform consistency
            file_key = str(router_path.relative_to(output_dir)).replace("\\", "/")
            files[file_key] = content

        # Sinh __init__.py (normalize path cho cross-platform)
        init_rel = (routes_dir / "__init__.py").relative_to(output_dir)
        init_key = str(init_rel).replace("\\", "/")
        files[init_key] = self._emit_routes_init(tags_list)
        return files

    def _emit_routes_init(self, tags: list[str]) -> str:
        """Sinh __init__.py cho routes directory."""
        lines = ['"""Routes package - auto-generated by Midicoder CE."""', ""]
        for tag in tags:
            lines.append(f"from . import {tag}_routes")
        lines.append("")
        lines.append("routers = [")
        for tag in tags:
            lines.append(f"    {tag}_routes.router,")
        lines.append("]")
        return "\n".join(lines)


# ===========================================================================
# FastAPI GraphQL Resolver Emitter
# ===========================================================================


@dataclass
class FastAPIGraphQLResolverEmitter:
    """Emitter de sinh GraphQL resolver files cho FastAPI (Strawberry)."""

    def emit(
        self,
        collection: RouteCollection,
        output_dir: Path,
    ) -> dict[str, str]:
        """Emit GraphQL resolver files."""
        files: dict[str, str] = {}
        if not collection.resolvers:
            return files

        resolvers_dir = output_dir / "graphql" / "resolvers"
        resolvers_dir.mkdir(parents=True, exist_ok=True)

        for resolver in collection.resolvers:
            filename = f"{self._to_snake_case(resolver.id)}_resolver.py"
            content = self._emit_resolver_file(resolver)
            files[str(resolvers_dir / filename)] = content

        files[str(output_dir / "graphql" / "schema.py")] = self._emit_schema(collection.resolvers)
        return files

    def _emit_resolver_file(self, resolver: GraphQLResolver) -> str:
        """Sinh resolver file cho mot GraphQL resolver."""
        type_name = self._to_pascal_case(resolver.id)
        lines = [
            '"""',
            f"GraphQL Resolver: {resolver.id}",
            "Auto-generated by Midicoder CE.",
            '"""',
            "",
            "import strawberry",
            "from typing import Optional, List",
            "",
            f"@strawberry.type",
            f"class {type_name}Result:",
            f'    """Result type for {resolver.id}."""',
        ]

        for rf in resolver.returns:
            lines.append(f"    {rf.name}: {rf.field_type}")

        lines.extend(["", ""])

        op_type = resolver.operation.value
        decorator = f"@strawberry.{op_type}"
        lines.append(decorator)

        args_str = ", ".join(
            f"{a.name}: {a.arg_type}" for a in resolver.args
        ) or "info: strawberry.types.Info"

        lines.append(f"async def {self._to_snake_case(resolver.id)}({args_str}) -> {type_name}Result:")
        lines.append(f'    """{resolver.description or resolver.id}"""')

        if resolver.tenant_scoped:
            lines.append("    # KPI-029: Tenant scope enforced in handler")

        handler_func = f"handle_{self._to_snake_case(resolver.handler_id)}"
        lines.append(f"    from app.queries.handler import {handler_func}")
        lines.append("    result = await handler_func()")
        lines.append(f"    return {type_name}Result(**result)")
        lines.extend(["", ""])

        return "\n".join(lines)

    def _emit_schema(self, resolvers: list[GraphQLResolver]) -> str:
        """Sinh schema.py cho GraphQL."""
        lines = [
            '"""GraphQL Schema - auto-generated by Midicoder CE."""',
            "",
            "import strawberry",
            "",
        ]

        query_resolvers = [r for r in resolvers if r.operation.value == "query"]
        mutation_resolvers = [r for r in resolvers if r.operation.value == "mutation"]

        if query_resolvers:
            lines.append("@strawberry.type")
            lines.append("class Query:")
            for r in query_resolvers:
                lines.append(f"    {self._to_snake_case(r.id)}: strawberry.types.UnionType  # TODO: wire resolver")
            lines.append("")

        if mutation_resolvers:
            lines.append("@strawberry.type")
            lines.append("class Mutation:")
            for r in mutation_resolvers:
                lines.append(f"    {self._to_snake_case(r.id)}: strawberry.types.UnionType  # TODO: wire resolver")
            lines.append("")

        lines.extend(["", "schema = strawberry.Schema(query=Query, mutation=Mutation if 'Mutation' in dir() else None)"])
        return "\n".join(lines)

    @staticmethod
    def _to_snake_case(name: str) -> str:
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    @staticmethod
    def _to_pascal_case(name: str) -> str:
        return "".join(word.capitalize() for word in name.replace("_", " ").split())


# ===========================================================================
# FastAPI Webhook Emitter
# ===========================================================================


@dataclass
class FastAPIWebhookEmitter:
    """Emitter de sinh webhook handler files cho FastAPI."""

    def emit(
        self,
        collection: RouteCollection,
        output_dir: Path,
    ) -> dict[str, str]:
        """Emit webhook handler files."""
        files: dict[str, str] = {}
        if not collection.webhooks:
            return files

        webhooks_dir = output_dir / "webhooks"
        webhooks_dir.mkdir(parents=True, exist_ok=True)

        for webhook in collection.webhooks:
            filename = f"{self._to_snake_case(webhook.event_type)}_handler.py"
            content = self._emit_webhook_file(webhook)
            files[str(webhooks_dir / filename)] = content

        files[str(webhooks_dir / "__init__.py")] = '"""Webhooks package - auto-generated by Midicoder CE."""\n'
        return files

    def _emit_webhook_file(self, webhook: WebhookHandler) -> str:
        """Sinh webhook handler file."""
        lines = [
            '"""',
            f"Webhook Handler: {webhook.event_type}",
            f"Path: {webhook.path}",
            "Auto-generated by Midicoder CE.",
            '"""',
            "",
            "import hashlib",
            "import hmac",
            "import os",
            "from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request",
            "",
            "",
            f"router = APIRouter(tags=['webhooks', '{webhook.event_type}'])",
            "",
            "",
            f"async def handle_{self._to_snake_case(webhook.event_type)}(payload: dict) -> dict:",
            f'    """Process {webhook.event_type} webhook event."""',
            f"    # Handler_id: {webhook.handler_id}",
            f'    return {{"status": "processed", "event": "{webhook.event_type}"}}',
            "",
            "",
            f"@router.post('{webhook.path}')",
            "async def webhook_endpoint(",
            "    request: Request,",
            "    background_tasks: BackgroundTasks,",
        ]

        if webhook.auth_config and webhook.verify_signature:
            lines.append(f'    signature: str = Header(None, alias="{webhook.auth_config.header_name}"),')

        lines.append(") -> dict:")
        lines.append(f'    """Receive {webhook.event_type} webhook."""')

        if webhook.verify_signature:
            lines.extend([
                "    # Verify HMAC signature",
                "    body = await request.body()",
                "    secret = os.environ.get(os.environ.get('WEBHOOK_SECRET_ENV', 'WEBHOOK_SECRET'), '')",
                "    expected = hmac.new(",
                "        secret.encode(), body, hashlib.sha256",
                "    ).hexdigest()",
                "    if not hmac.compare_digest(expected, signature or ''):",
                '        raise HTTPException(status_code=401, detail="Invalid signature")',
                "",
                "    import json",
                "    payload = json.loads(body)",
            ])
        else:
            lines.append("    payload = await request.json()")

        lines.extend([
            "",
            f"    result = await handle_{self._to_snake_case(webhook.event_type)}(payload)",
            '    return {"status": "ok"}',
            "",
            "",
        ])

        return "\n".join(lines)

    @staticmethod
    def _to_snake_case(name: str) -> str:
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()