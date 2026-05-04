"""Default configuration values and constants."""

from __future__ import annotations

# Tech stack defaults
DEFAULT_STACK = ["fastapi"]

SUPPORTED_STACKS = ["fastapi", "nest", "angular"]


# LLM provider defaults
LLM_PROVIDERS = ["anthropic", "openai"]

PROVIDER_BASE_URLS = {
    "anthropic": "https://api.anthropic.com",
    "openai": "https://api.openai.com/v1",
}

PROVIDER_DEFAULT_MODELS = {
    "anthropic": {"high": "claude-4-5-sonnet", "cheap": "claude-3-5-haiku"},
    "openai": {"high": "gpt-4", "cheap": "gpt-3.5-turbo"},
}

# Common LLM model names for reference/autocomplete
COMMON_MODEL_NAMES = [
    "sonnet4-5",
    "claude-3-5-haiku",
    "gpt-4",
    "gpt-3.5-turbo",
]

# Configuration field management
# These are the top-level fields expected in config.json
CONFIG_FIELDS = [
    "working_dir",  # Working directory path
    "stack",  # Target tech stack (array)
    "commands",  # Command definitions
    "llm",  # LLM configuration
    "cache",  # Cache configuration
    "snapshot_whitelist",  # Glob patterns for snapshot
]

# Secrets configuration
SECRET_CATEGORIES = ["llm", "database", "external_api"]

SECRETS_FILE_NAME = "secrets.json"
