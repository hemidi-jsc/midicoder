# coding: utf-8
"""
Mô-đun models cho API Routes Emitter (CP06).

Định nghĩa các dataclass biểu diễn:
- Route: HTTP REST route với method, path, handler, auth
- GraphQLResolver: GraphQL resolver với operation, type, field
- WebhookHandler: Webhook handler với path, event, auth config

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ===========================================================================
# HTTP Route Models
# ===========================================================================


class HttpMethod(str, Enum):
    """
    Enum các HTTP methods được hỗ trợ.
    """
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class AuthMode(str, Enum):
    """
    Enum các chế độ authentication cho routes.
    """
    NONE = "none"
    JWT = "jwt"
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    SESSION = "session"


@dataclass
class RouteParam:
    """
    Tham số đường dẫn route (path parameter).

    Attributes:
        name: Tên tham số
        param_type: Kiểu dữ liệu (str, int, uuid, etc.)
        required: Có bắt buộc không
        description: Mô tả tham số
    """
    name: str
    param_type: str = "str"
    required: bool = True
    description: str = ""


@dataclass
class QueryParam:
    """
    Query parameter cho route.

    Attributes:
        name: Tên tham số
        param_type: Kiểu dữ liệu
        required: Có bắt buộc không
        default: Giá trị mặc định
        description: Mô tả tham số
    """
    name: str
    param_type: str = "str"
    required: bool = False
    default: Any = None
    description: str = ""


@dataclass
class SchemaField:
    """
    Field trong request/response schema.

    Attributes:
        name: Tên field
        field_type: Kiểu dữ liệu (str, int, bool, etc.)
        required: Có bắt buộc không
        description: Mô tả field
        example: Ví dụ giá trị
    """
    name: str
    field_type: str = "str"
    required: bool = False
    description: str = ""
    example: Any = None


@dataclass
class RouteAuthConfig:
    """
    Cấu hình authentication cho route.

    Attributes:
        mode: Chế độ auth (JWT, OAuth2, API_KEY, ...)
        required_roles: Danh sách roles được phép
        required_permissions: Danh sách permissions được phép
        tenant_scoped: Có enforce tenant scope không (KPI-029)
    """
    mode: AuthMode = AuthMode.JWT
    required_roles: list[str] = field(default_factory=list)
    required_permissions: list[str] = field(default_factory=list)
    tenant_scoped: bool = True  # KPI-029: mặc định tenant_scoped


@dataclass
class Route:
    """
    HTTP REST Route model.

    Biểu diễn một HTTP route với đầy đủ thông tin:
    method, path, handler binding, auth config, schemas.

    Attributes:
        id: Định danh duy nhất của route
        description: Mô tả route (tiếng Việt)
        method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        path: URL path (ví dụ: /api/v1/orders/{order_id})
        handler_type: Loại handler (command hoặc query)
        handler_id: ID của command/query handler
        tags: Danh sách tags để group routes
        auth: Auth config cho route
        path_params: Các path parameters
        query_params: Các query parameters
        request_schema: Schema cho request body
        response_schema: Schema cho response body
        response_status: HTTP status code mặc định (200, 201, 204)
        deprecated: Route có deprecated không
    """
    id: str
    description: str = ""
    method: HttpMethod = HttpMethod.GET
    path: str = ""
    handler_type: str = "query"
    handler_id: str = ""
    tags: list[str] = field(default_factory=list)
    auth: Optional[RouteAuthConfig] = None
    path_params: list[RouteParam] = field(default_factory=list)
    query_params: list[QueryParam] = field(default_factory=list)
    request_schema: list[SchemaField] = field(default_factory=list)
    response_schema: list[SchemaField] = field(default_factory=list)
    response_status: int = 200
    deprecated: bool = False

    def is_write_operation(self) -> bool:
        """
        Kiểm tra route có phải là write operation không.

        Returns:
            True nếu method là POST, PUT, PATCH, DELETE
        """
        return self.method in (
            HttpMethod.POST,
            HttpMethod.PUT,
            HttpMethod.PATCH,
            HttpMethod.DELETE,
        )

    def is_read_operation(self) -> bool:
        """
        Kiểm tra route có phải là read operation không.

        Returns:
            True nếu method là GET, HEAD, OPTIONS
        """
        return self.method in (
            HttpMethod.GET,
            HttpMethod.HEAD,
            HttpMethod.OPTIONS,
        )

    def requires_auth(self) -> bool:
        """
        Kiểm tra route có cần authentication không.

        Returns:
            True nếu auth config tồn tại và mode != NONE
        """
        return self.auth is not None and self.auth.mode != AuthMode.NONE

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển route sang dict format (cho MIR metadata).

        Returns:
            Dictionary representation của route
        """
        return {
            "id": self.id,
            "description": self.description,
            "method": self.method.value,
            "path": self.path,
            "handler_type": self.handler_type,
            "handler_id": self.handler_id,
            "tags": self.tags,
            "auth": {
                "mode": self.auth.mode.value,
                "required_roles": self.auth.required_roles,
                "required_permissions": self.auth.required_permissions,
                "tenant_scoped": self.auth.tenant_scoped,
            }
            if self.auth
            else None,
            "path_params": [
                {"name": p.name, "type": p.param_type, "required": p.required}
                for p in self.path_params
            ],
            "query_params": [
                {"name": p.name, "type": p.param_type, "required": p.required}
                for p in self.query_params
            ],
            "request_schema": [
                {"name": f.name, "type": f.field_type, "required": f.required}
                for f in self.request_schema
            ],
            "response_schema": [
                {"name": f.name, "type": f.field_type, "required": f.required}
                for f in self.response_schema
            ],
            "response_status": self.response_status,
            "deprecated": self.deprecated,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Route":
        """
        Tạo Route từ dict (từ MIR metadata).

        Args:
            data: Dictionary chứa route data

        Returns:
            Route instance
        """
        auth_data = data.get("auth")
        auth = None
        if auth_data:
            auth = RouteAuthConfig(
                mode=AuthMode(auth_data.get("mode", "jwt")),
                required_roles=auth_data.get("required_roles", []),
                required_permissions=auth_data.get("required_permissions", []),
                tenant_scoped=auth_data.get("tenant_scoped", True),
            )

        return cls(
            id=data.get("id", ""),
            description=data.get("description", ""),
            method=HttpMethod(data.get("method", "GET")),
            path=data.get("path", ""),
            handler_type=data.get("handler_type", "query"),
            handler_id=data.get("handler_id", ""),
            tags=data.get("tags", []),
            auth=auth,
            path_params=[
                RouteParam(
                    name=p["name"],
                    param_type=p.get("type", p.get("param_type", "str")),
                    required=p.get("required", True),
                )
                for p in data.get("path_params", [])
            ],
            query_params=[
                QueryParam(
                    name=p["name"],
                    param_type=p.get("type", p.get("param_type", "str")),
                    required=p.get("required", False),
                )
                for p in data.get("query_params", [])
            ],
            request_schema=[
                SchemaField(
                    name=f["name"],
                    field_type=f.get("type", f.get("field_type", "str")),
                    required=f.get("required", False),
                )
                for f in data.get("request_schema", [])
            ],
            response_schema=[
                SchemaField(
                    name=f["name"],
                    field_type=f.get("type", f.get("field_type", "str")),
                    required=f.get("required", False),
                )
                for f in data.get("response_schema", [])
            ],
            response_status=data.get("response_status", 200),
            deprecated=data.get("deprecated", False),
        )


# ===========================================================================
# GraphQL Resolver Models
# ===========================================================================


class GraphQLOperation(str, Enum):
    """
    Enum các GraphQL operation types.
    """
    QUERY = "query"
    MUTATION = "mutation"
    SUBSCRIPTION = "subscription"


@dataclass
class GraphQLArg:
    """
    Argument cho GraphQL resolver.

    Attributes:
        name: Tên argument
        arg_type: Kiểu dữ liệu GraphQL (String, Int, Boolean, ID, ...)
        required: Có bắt buộc không
        description: Mô tả argument
    """
    name: str
    arg_type: str = "String"
    required: bool = False
    description: str = ""


@dataclass
class GraphQLField:
    """
    Field trong GraphQL return type.

    Attributes:
        name: Tên field
        field_type: Kiểu dữ liệu GraphQL
        description: Mô tả field
    """
    name: str
    field_type: str = "String"
    description: str = ""


@dataclass
class GraphQLResolver:
    """
    GraphQL Resolver model.

    Biểu diễn một GraphQL resolver (query/mutation/subscription).

    Attributes:
        id: Định danh duy nhất
        description: Mô tả resolver
        operation: Loại operation (query, mutation, subscription)
        type_name: Tên GraphQL type (Query, Mutation, ...)
        field_name: Tên field trong type
        handler_id: ID của command/query handler phía backend
        args: Danh sách arguments
        returns: Return schema (fields)
        auth_required: Có cần auth không
        tenant_scoped: Có enforce tenant scope không (KPI-029)
        tags: Danh sách tags
    """
    id: str
    description: str = ""
    operation: GraphQLOperation = GraphQLOperation.QUERY
    type_name: str = "Query"
    field_name: str = ""
    handler_id: str = ""
    args: list[GraphQLArg] = field(default_factory=list)
    returns: list[GraphQLField] = field(default_factory=list)
    auth_required: bool = True
    tenant_scoped: bool = True  # KPI-029
    tags: list[str] = field(default_factory=list)

    def is_mutation(self) -> bool:
        """
        Kiểm tra resolver có phải là mutation không.

        Returns:
            True nếu operation là MUTATION
        """
        return self.operation == GraphQLOperation.MUTATION

    def is_subscription(self) -> bool:
        """
        Kiểm tra resolver có phải là subscription không.

        Returns:
            True nếu operation là SUBSCRIPTION
        """
        return self.operation == GraphQLOperation.SUBSCRIPTION

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển resolver sang dict format.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "description": self.description,
            "operation": self.operation.value,
            "type_name": self.type_name,
            "field_name": self.field_name,
            "handler_id": self.handler_id,
            "args": [
                {"name": a.name, "type": a.arg_type, "required": a.required}
                for a in self.args
            ],
            "returns": [
                {"name": f.name, "type": f.field_type}
                for f in self.returns
            ],
            "auth_required": self.auth_required,
            "tenant_scoped": self.tenant_scoped,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraphQLResolver":
        """
        Tạo GraphQLResolver từ dict.

        Args:
            data: Dictionary chứa resolver data

        Returns:
            GraphQLResolver instance
        """
        return cls(
            id=data.get("id", ""),
            description=data.get("description", ""),
            operation=GraphQLOperation(data.get("operation", "query")),
            type_name=data.get("type_name", "Query"),
            field_name=data.get("field_name", ""),
            handler_id=data.get("handler_id", ""),
            args=[
                GraphQLArg(
                    name=a["name"],
                    arg_type=a.get("type", a.get("arg_type", "String")),
                    required=a.get("required", False),
                )
                for a in data.get("args", [])
            ],
            returns=[
                GraphQLField(
                    name=f["name"],
                    field_type=f.get("type", f.get("field_type", "String")),
                )
                for f in data.get("returns", [])
            ],
            auth_required=data.get("auth_required", True),
            tenant_scoped=data.get("tenant_scoped", True),
            tags=data.get("tags", []),
        )


# ===========================================================================
# Webhook Handler Models
# ===========================================================================


class WebhookAuthType(str, Enum):
    """
    Enum các loại authentication cho webhook.
    """
    NONE = "none"
    HMAC_SIGNATURE = "hmac_signature"
    BEARER_TOKEN = "bearer_token"
    CUSTOM_HEADER = "custom_header"


@dataclass
class WebhookAuthConfig:
    """
    Cấu hình authentication cho webhook.

    Attributes:
        auth_type: Loại auth
        header_name: Tên header chứa auth data
        secret_env: Tên env var chứa secret key
        algorithm: Algorithm cho HMAC signing
    """
    auth_type: WebhookAuthType = WebhookAuthType.HMAC_SIGNATURE
    header_name: str = "X-Signature"
    secret_env: str = "WEBHOOK_SECRET"
    algorithm: str = "sha256"


@dataclass
class WebhookPayloadField:
    """
    Field trong webhook payload schema.

    Attributes:
        name: Tên field
        field_type: Kiểu dữ liệu
        required: Có bắt buộc không
        description: Mô tả field
    """
    name: str
    field_type: str = "str"
    required: bool = False
    description: str = ""


@dataclass
class WebhookHandler:
    """
    Webhook Handler model.

    Biểu diễn một webhook endpoint để nhận incoming events từ external systems.

    Attributes:
        id: Định danh duy nhất
        description: Mô tả webhook
        path: URL path để receive webhook
        event_type: Loại event từ webhook
        handler_id: ID của command/handler để process webhook
        auth_config: Auth config cho webhook
        verify_signature: Có verify signature không
        payload_schema: Schema cho payload
        tags: Danh sách tags
    """
    id: str
    description: str = ""
    path: str = ""
    event_type: str = ""
    handler_id: str = ""
    auth_config: Optional[WebhookAuthConfig] = None
    verify_signature: bool = True
    payload_schema: list[WebhookPayloadField] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển webhook handler sang dict format.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "description": self.description,
            "path": self.path,
            "event_type": self.event_type,
            "handler_id": self.handler_id,
            "auth_config": {
                "auth_type": self.auth_config.auth_type.value,
                "header_name": self.auth_config.header_name,
                "secret_env": self.auth_config.secret_env,
                "algorithm": self.auth_config.algorithm,
            }
            if self.auth_config
            else None,
            "verify_signature": self.verify_signature,
            "payload_schema": [
                {"name": f.name, "type": f.field_type, "required": f.required}
                for f in self.payload_schema
            ],
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WebhookHandler":
        """
        Tạo WebhookHandler từ dict.

        Args:
            data: Dictionary chứa webhook data

        Returns:
            WebhookHandler instance
        """
        auth_data = data.get("auth_config")
        auth_config = None
        if auth_data:
            auth_config = WebhookAuthConfig(
                auth_type=WebhookAuthType(auth_data.get("auth_type", "hmac_signature")),
                header_name=auth_data.get("header_name", "X-Signature"),
                secret_env=auth_data.get("secret_env", "WEBHOOK_SECRET"),
                algorithm=auth_data.get("algorithm", "sha256"),
            )

        return cls(
            id=data.get("id", ""),
            description=data.get("description", ""),
            path=data.get("path", ""),
            event_type=data.get("event_type", ""),
            handler_id=data.get("handler_id", ""),
            auth_config=auth_config,
            verify_signature=data.get("verify_signature", True),
            payload_schema=[
                WebhookPayloadField(
                    name=f["name"],
                    field_type=f.get("type", f.get("field_type", "str")),
                    required=f.get("required", False),
                )
                for f in data.get("payload_schema", [])
            ],
            tags=data.get("tags", []),
        )


# ===========================================================================
# Route Collection
# ===========================================================================


@dataclass
class RouteCollection:
    """
    Collection chứa tất cả routes, resolvers, và webhooks.

    Dùng làm output của RouteParser và input cho Stack Emitters.

    Attributes:
        routes: Danh sách HTTP routes
        resolvers: Danh sách GraphQL resolvers
        webhooks: Danh sách webhook handlers
    """
    routes: list[Route] = field(default_factory=list)
    resolvers: list[GraphQLResolver] = field(default_factory=list)
    webhooks: list[WebhookHandler] = field(default_factory=list)

    def add_route(self, route: Route) -> None:
        """
        Thêm HTTP route vào collection.

        Args:
            route: Route instance
        """
        self.routes.append(route)

    def add_resolver(self, resolver: GraphQLResolver) -> None:
        """
        Thêm GraphQL resolver vào collection.

        Args:
            resolver: GraphQLResolver instance
        """
        self.resolvers.append(resolver)

    def add_webhook(self, webhook: WebhookHandler) -> None:
        """
        Thêm webhook handler vào collection.

        Args:
            webhook: WebhookHandler instance
        """
        self.webhooks.append(webhook)

    @property
    def total_count(self) -> int:
        """
        Tổng số items trong collection.

        Returns:
            Tổng số routes + resolvers + webhooks
        """
        return len(self.routes) + len(self.resolvers) + len(self.webhooks)

    def get_by_tag(self, tag: str) -> RouteCollection:
        """
        Lọc collection theo tag.

        Args:
            tag: Tag cần lọc

        Returns:
            RouteCollection chỉ chứa items có tag khớp
        """
        result = RouteCollection()
        result.routes = [r for r in self.routes if tag in r.tags]
        result.resolvers = [r for r in self.resolvers if tag in r.tags]
        result.webhooks = [w for w in self.webhooks if tag in w.tags]
        return result

    def group_routes_by_tag(self) -> dict[str, list[Route]]:
        """
        Nhóm routes theo tag.

        Returns:
            Dictionary {tag: [routes]}
        """
        groups: dict[str, list[Route]] = {}
        for route in self.routes:
            for tag in route.tags:
                if tag not in groups:
                    groups[tag] = []
                groups[tag].append(route)
        return groups

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển collection sang dict format.

        Returns:
            Dictionary representation
        """
        return {
            "routes": [r.to_dict() for r in self.routes],
            "resolvers": [r.to_dict() for r in self.resolvers],
            "webhooks": [w.to_dict() for w in self.webhooks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RouteCollection":
        """
        Tạo RouteCollection từ dict.

        Args:
            data: Dictionary chứa collection data

        Returns:
            RouteCollection instance
        """
        result = cls()
        result.routes = [Route.from_dict(r) for r in data.get("routes", [])]
        result.resolvers = [GraphQLResolver.from_dict(r) for r in data.get("resolvers", [])]
        result.webhooks = [WebhookHandler.from_dict(w) for w in data.get("webhooks", [])]
        return result