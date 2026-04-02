from __future__ import annotations

from typing import Any, ClassVar, Optional

from pydantic import BaseModel, Field, constr

from .model_meta import ModelMeta
from .named_field_model import NamedField


INTEGRATION_TYPE_CATALOG = {
    "rest_api",
    "aws",
    "gcp",
    "azure",
    "aws_s3",
    "queue",
    "smtp",
    "webhook",
    "oauth2_introspection",
    "custom",
}

AUTH_TYPE_CATALOG = {
    "none",
    "api_key",
    "bearer",
    "basic",
    "oauth2_client_credentials",
    "oauth2_password",
    "oauth2_auth_code",
    "aws_sigv4",
}

WEBHOOK_SIGNATURE_ALG_CATALOG = {
    "hmac-sha256",
    "hmac-sha1",
    "rsa-sha256",
}

EMAIL_TRANSPORT_CATALOG = {
    "smtp",
    "ses",
    "sendgrid",
    "mailgun",
}

CLOUD_PROVIDER_CATALOG = {
    "aws",
    "gcp",
    "azure",
}

AWS_SERVICE_CATALOG = {
    "s3",
    "sqs",
    "sns",
    "lambda",
    "dynamodb",
    "rds",
    "eventbridge",
    "kinesis",
    "ses",
    "secret_manager",
    "cloudwatch",
    "ecs",
    "eks",
    "step_functions",
}

GCP_SERVICE_CATALOG = {
    "cloud_storage",
    "pubsub",
    "cloud_functions",
    "cloud_run",
    "bigquery",
    "spanner",
    "firestore",
    "memorystore",
    "secret_manager",
    "cloud_tasks",
    "cloud_scheduler",
}

AZURE_SERVICE_CATALOG = {
    "blob_storage",
    "service_bus",
    "event_hubs",
    "functions",
    "cosmosdb",
    "sql_database",
    "key_vault",
    "app_configuration",
    "logic_apps",
    "aks",
    "container_apps",
}


# Typed refs (string form) used across integrations contracts.
# Canonical form uses `Type:id`, while bare `id` is kept for backward compatibility.
IntegrationRefStr = constr(pattern=r"^(Integration:)?[A-Za-z_][A-Za-z0-9_]*$")
IntegrationOperationRefStr = constr(
    pattern=r"^(IntegrationOperation:)?[A-Za-z_][A-Za-z0-9_]*$"
)
SecretRefStr = constr(pattern=r"^(Secret:)?[A-Za-z_][A-Za-z0-9_]*$")


class TimeoutPolicy(BaseModel):
    connect_ms: Optional[int] = None
    read_ms: Optional[int] = None
    total_ms: Optional[int] = None

    model_config = {"extra": "forbid"}


class RetryPolicy(BaseModel):
    max_attempts: int = 1
    backoff_ms: int = 0
    max_backoff_ms: Optional[int] = None
    jitter: bool = False

    model_config = {"extra": "forbid"}


class RateLimitPolicy(BaseModel):
    requests: int
    per_seconds: int

    model_config = {"extra": "forbid"}


class CircuitBreakerPolicy(BaseModel):
    failure_threshold: int
    recovery_timeout_seconds: int

    model_config = {"extra": "forbid"}


class IntegrationAuth(BaseModel):
    type: str
    secret_ref: Optional[SecretRefStr] = None
    key_name: Optional[str] = None
    token_prefix: Optional[str] = None
    options: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class IntegrationTarget(BaseModel):
    id: str
    type: str
    provider: Optional[str] = None
    service: Optional[str] = None
    base_url: Optional[str] = None
    auth: Optional[IntegrationAuth] = None
    timeouts: Optional[TimeoutPolicy] = None
    retry: Optional[RetryPolicy] = None
    rate_limit: Optional[RateLimitPolicy] = None
    circuit_breaker: Optional[CircuitBreakerPolicy] = None
    headers: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ErrorMap(BaseModel):
    source_code: str
    target_error: str

    model_config = {"extra": "forbid"}


class RestApiOperation(BaseModel):
    id: str
    integration_id: IntegrationRefStr
    method: str
    path: str
    request_schema: list[NamedField] = Field(default_factory=list)
    response_schema: list[NamedField] = Field(default_factory=list)
    error_mapping: list[ErrorMap] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class S3Resource(BaseModel):
    integration_id: IntegrationRefStr
    bucket: str
    region: str
    operations: list[IntegrationOperationRefStr] = Field(default_factory=list)
    path_template: Optional[str] = None
    encryption: Optional[str] = None

    model_config = {"extra": "forbid"}


class EmailProvider(BaseModel):
    id: str
    transport: str
    host: Optional[str] = None
    port: Optional[int] = None
    username_secret: Optional[SecretRefStr] = None
    password_secret: Optional[SecretRefStr] = None
    from_email: str
    from_name: Optional[str] = None

    model_config = {"extra": "forbid"}


class OAuth2Provider(BaseModel):
    id: str
    issuer: str
    audience: Optional[str] = None
    jwks_url: Optional[str] = None
    introspection_url: Optional[str] = None
    client_id_secret: Optional[SecretRefStr] = None
    client_secret_secret: Optional[SecretRefStr] = None
    scopes: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class SignaturePolicy(BaseModel):
    alg: str
    secret_ref: SecretRefStr
    header_name: Optional[str] = None

    model_config = {"extra": "forbid"}


class WebhookEndpoint(BaseModel):
    id: str
    direction: str
    url_or_path: str
    method: str = "POST"
    signature: Optional[SignaturePolicy] = None
    retries: Optional[RetryPolicy] = None
    events: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class IntegrationsFile(BaseModel):
    integrations: list[IntegrationTarget]
    operations: list[RestApiOperation] = Field(default_factory=list)
    s3_resources: list[S3Resource] = Field(default_factory=list)
    oauth2_providers: list[OAuth2Provider] = Field(default_factory=list)
    webhooks: list[WebhookEndpoint] = Field(default_factory=list)
    email_providers: list[EmailProvider] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    model_meta: ClassVar[ModelMeta] = ModelMeta(
        kind="integration.file",
        usage_en=(
            "Third-party integration contract for outbound REST, cloud services, "
            "email, OAuth2 providers and webhooks."
        ),
    )
