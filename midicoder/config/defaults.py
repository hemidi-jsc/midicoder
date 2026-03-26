"""Default configuration values and constants."""

from __future__ import annotations

# Tech stack defaults
DEFAULT_STACK = [
    "fastapi"
]

SUPPORTED_STACKS = [
    "fastapi",
    "nest",
    "angular"
]


# LLM provider defaults
LLM_PROVIDERS = [
    "anthropic",
    "openai",
    "openai_compatible",
    "bedrock",
    "azure",
    "vertex_partner",
    # Backward-compatible aliases
    "aws_bedrock",
    "azure_openai",
]

PROVIDER_BASE_URLS = {
    "anthropic": "https://api.anthropic.com",
    "openai": "https://api.openai.com/v1",
    "openai_compatible": "https://api.openai.com/v1",
    # Cloud providers typically derive endpoint/base routing from provider-specific options.
    "bedrock": None,
    "azure": None,
    "vertex_partner": None,
    # Backward-compatible aliases
    "aws_bedrock": None,
    "azure_openai": None,
}

PROVIDER_DEFAULT_MODELS = {
    "anthropic": {
        "high": "anthropic/claude-3-7-sonnet-latest",
        "cheap": "anthropic/claude-3-5-haiku-latest",
    },
    "openai": {
        "high": "gpt-4o",
        "cheap": "gpt-4o-mini",
    },
    "openai_compatible": {
        "high": "openai/gpt-4o",
        "cheap": "openai/gpt-4o-mini",
    },
    "bedrock": {
        "high": "bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0",
        "cheap": "bedrock/anthropic.claude-3-5-haiku-20241022-v1:0",
    },
    "azure": {
        "high": "azure/gpt-4o",
        "cheap": "azure/gpt-4o-mini",
    },
    "vertex_partner": {
        "high": "vertex_ai/gemini-1.5-pro",
        "cheap": "vertex_ai/gemini-1.5-flash",
    },
    # Backward-compatible aliases
    "aws_bedrock": {
        "high": "bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0",
        "cheap": "bedrock/anthropic.claude-3-5-haiku-20241022-v1:0",
    },
    "azure_openai": {
        "high": "azure/gpt-4o",
        "cheap": "azure/gpt-4o-mini",
    },
}

# Common LLM model names for reference/autocomplete
COMMON_MODEL_NAMES = [
    "anthropic/claude-3-7-sonnet-latest",
    "anthropic/claude-3-5-haiku-latest",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0",
    "bedrock/anthropic.claude-3-5-haiku-20241022-v1:0",
    "azure/gpt-4o",
    "azure/gpt-4o-mini",
    "vertex_ai/gemini-1.5-pro",
    "vertex_ai/gemini-1.5-flash",
]

# Configuration field management
# These are the top-level fields expected in config.json
CONFIG_FIELDS = [
    "working_dir",    # Working directory path
    "stack",          # Target tech stack (array)
    "commands",       # Command definitions
    "llm",            # LLM configuration
    "cache",          # Cache configuration
    "snapshot_whitelist",  # Glob patterns for snapshot
]

# Secrets configuration
SECRET_CATEGORIES = [
    "llm",
    "database",
    "external_api"
]

SECRETS_FILE_NAME = "secrets.json"
