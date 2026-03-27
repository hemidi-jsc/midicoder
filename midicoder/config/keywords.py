"""Configuration keywords registry for non-interactive mode."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .defaults import LLM_PROVIDERS, SUPPORTED_STACKS


@dataclass
class ConfigKeyword:
    """Configuration keyword definition."""

    flag: str
    """Command-line flag (e.g., --working-dir)"""

    env_var: str
    """Environment variable name (e.g., MIDICODER_WORKING_DIR)"""

    description: str
    """Human-readable description"""

    type: str
    """Data type: text, choice, multichoice, secret"""

    required: bool = False
    """Whether this keyword is required"""

    default: Any = None
    """Default value if not provided"""

    choices: list[str] | None = None
    """Valid choices for choice/multichoice types"""

    example: str | None = None
    """Example value"""


class InitKeywords:
    """Keywords for `midicoder init` command."""

    KEYWORDS = [
        ConfigKeyword(
            flag="--working-dir",
            env_var="MIDICODER_WORKING_DIR",
            description="Working directory path",
            type="text",
            default="<current directory>",
            example="/home/user/my-project",
        ),
        ConfigKeyword(
            flag="--stack",
            env_var="MIDICODER_STACK",
            description="Comma-separated tech stack(s)",
            type="multichoice",
            required=True,
            choices=SUPPORTED_STACKS,
            example="fastapi,nest",
        ),
        ConfigKeyword(
            flag="--llm-high-provider",
            env_var="MIDICODER_LLM_HIGH_PROVIDER",
            description="High-tier LLM provider",
            type="choice",
            required=True,
            choices=LLM_PROVIDERS,
            example="anthropic",
        ),
        ConfigKeyword(
            flag="--llm-cheap-provider",
            env_var="MIDICODER_LLM_CHEAP_PROVIDER",
            description="Cheap-tier LLM provider",
            type="choice",
            required=True,
            choices=LLM_PROVIDERS,
            example="anthropic",
        ),
        # OpenAI Compatible
        ConfigKeyword(
            flag="--llm-high-model",
            env_var="MIDICODER_LLM_HIGH_MODEL",
            description="High-tier model for provider=openai_compatible",
            type="text",
            example="openai/gpt-4o",
        ),
        ConfigKeyword(
            flag="--llm-high-url",
            env_var="MIDICODER_LLM_HIGH_URL",
            description="High-tier API base URL for provider=openai_compatible",
            type="text",
            example="https://api.openai.com/v1",
        ),
        ConfigKeyword(
            flag="--llm-high-key",
            env_var="MIDICODER_LLM_HIGH_API_KEY",
            description="High-tier API key for provider=openai_compatible",
            type="secret",
            example="sk-...",
        ),
        ConfigKeyword(
            flag="--llm-high-key-env",
            env_var="MIDICODER_LLM_HIGH_API_KEY_ENV",
            description="Env var name containing high-tier API key for provider=openai_compatible",
            type="text",
            example="OPENAI_API_KEY",
        ),
        ConfigKeyword(
            flag="--llm-cheap-model",
            env_var="MIDICODER_LLM_CHEAP_MODEL",
            description="Cheap-tier model for provider=openai_compatible",
            type="text",
            example="openai/gpt-4o-mini",
        ),
        ConfigKeyword(
            flag="--llm-cheap-url",
            env_var="MIDICODER_LLM_CHEAP_URL",
            description="Cheap-tier API base URL for provider=openai_compatible",
            type="text",
            example="https://api.openai.com/v1",
        ),
        ConfigKeyword(
            flag="--llm-cheap-key",
            env_var="MIDICODER_LLM_CHEAP_API_KEY",
            description="Cheap-tier API key for provider=openai_compatible",
            type="secret",
            example="sk-...",
        ),
        ConfigKeyword(
            flag="--llm-cheap-key-env",
            env_var="MIDICODER_LLM_CHEAP_API_KEY_ENV",
            description="Env var name containing cheap-tier API key for provider=openai_compatible",
            type="text",
            example="OPENAI_API_KEY",
        ),
        # Anthropic
        ConfigKeyword(
            flag="--llm-high-anthropic-model",
            env_var="MIDICODER_LLM_HIGH_ANTHROPIC_MODEL",
            description="High-tier model for provider=anthropic",
            type="text",
            example="anthropic/claude-3-7-sonnet-latest",
        ),
        ConfigKeyword(
            flag="--llm-high-anthropic-key",
            env_var="MIDICODER_LLM_HIGH_ANTHROPIC_API_KEY",
            description="High-tier API key for provider=anthropic",
            type="secret",
            example="sk-ant-...",
        ),
        ConfigKeyword(
            flag="--llm-high-anthropic-key-env",
            env_var="MIDICODER_LLM_HIGH_ANTHROPIC_API_KEY_ENV",
            description="Env var name containing high-tier API key for provider=anthropic",
            type="text",
            example="ANTHROPIC_API_KEY",
        ),
        ConfigKeyword(
            flag="--llm-cheap-anthropic-model",
            env_var="MIDICODER_LLM_CHEAP_ANTHROPIC_MODEL",
            description="Cheap-tier model for provider=anthropic",
            type="text",
            example="anthropic/claude-3-5-haiku-latest",
        ),
        ConfigKeyword(
            flag="--llm-cheap-anthropic-key",
            env_var="MIDICODER_LLM_CHEAP_ANTHROPIC_API_KEY",
            description="Cheap-tier API key for provider=anthropic",
            type="secret",
            example="sk-ant-...",
        ),
        ConfigKeyword(
            flag="--llm-cheap-anthropic-key-env",
            env_var="MIDICODER_LLM_CHEAP_ANTHROPIC_API_KEY_ENV",
            description="Env var name containing cheap-tier API key for provider=anthropic",
            type="text",
            example="ANTHROPIC_API_KEY",
        ),
        # OpenAI
        ConfigKeyword(
            flag="--llm-high-openai-model",
            env_var="MIDICODER_LLM_HIGH_OPENAI_MODEL",
            description="High-tier model for provider=openai",
            type="text",
            example="gpt-4o",
        ),
        ConfigKeyword(
            flag="--llm-high-openai-key",
            env_var="MIDICODER_LLM_HIGH_OPENAI_API_KEY",
            description="High-tier API key for provider=openai",
            type="secret",
            example="sk-...",
        ),
        ConfigKeyword(
            flag="--llm-high-openai-key-env",
            env_var="MIDICODER_LLM_HIGH_OPENAI_API_KEY_ENV",
            description="Env var name containing high-tier API key for provider=openai",
            type="text",
            example="OPENAI_API_KEY",
        ),
        ConfigKeyword(
            flag="--llm-cheap-openai-model",
            env_var="MIDICODER_LLM_CHEAP_OPENAI_MODEL",
            description="Cheap-tier model for provider=openai",
            type="text",
            example="gpt-4o-mini",
        ),
        ConfigKeyword(
            flag="--llm-cheap-openai-key",
            env_var="MIDICODER_LLM_CHEAP_OPENAI_API_KEY",
            description="Cheap-tier API key for provider=openai",
            type="secret",
            example="sk-...",
        ),
        ConfigKeyword(
            flag="--llm-cheap-openai-key-env",
            env_var="MIDICODER_LLM_CHEAP_OPENAI_API_KEY_ENV",
            description="Env var name containing cheap-tier API key for provider=openai",
            type="text",
            example="OPENAI_API_KEY",
        ),
        # Bedrock
        ConfigKeyword(
            flag="--llm-high-bedrock-model",
            env_var="MIDICODER_LLM_HIGH_BEDROCK_MODEL",
            description="High-tier model for provider=bedrock",
            type="text",
            example="bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0",
        ),
        ConfigKeyword(
            flag="--llm-high-aws-region-name",
            env_var="MIDICODER_LLM_HIGH_AWS_REGION_NAME",
            description="AWS region name for high-tier provider=bedrock",
            type="text",
            example="us-east-1",
        ),
        ConfigKeyword(
            flag="--llm-high-aws-access-key-id",
            env_var="MIDICODER_LLM_HIGH_AWS_ACCESS_KEY_ID",
            description="AWS access key id for high-tier provider=bedrock",
            type="secret",
            example="AKIA...",
        ),
        ConfigKeyword(
            flag="--llm-high-aws-access-key-id-env",
            env_var="MIDICODER_LLM_HIGH_AWS_ACCESS_KEY_ID_ENV",
            description="Env var name containing AWS access key id for high-tier provider=bedrock",
            type="text",
            example="AWS_ACCESS_KEY_ID",
        ),
        ConfigKeyword(
            flag="--llm-high-aws-secret-access-key",
            env_var="MIDICODER_LLM_HIGH_AWS_SECRET_ACCESS_KEY",
            description="AWS secret access key for high-tier provider=bedrock",
            type="secret",
            example="wJalrXU...",
        ),
        ConfigKeyword(
            flag="--llm-high-aws-secret-access-key-env",
            env_var="MIDICODER_LLM_HIGH_AWS_SECRET_ACCESS_KEY_ENV",
            description="Env var name containing AWS secret access key for high-tier provider=bedrock",
            type="text",
            example="AWS_SECRET_ACCESS_KEY",
        ),
        ConfigKeyword(
            flag="--llm-cheap-bedrock-model",
            env_var="MIDICODER_LLM_CHEAP_BEDROCK_MODEL",
            description="Cheap-tier model for provider=bedrock",
            type="text",
            example="bedrock/anthropic.claude-3-5-haiku-20241022-v1:0",
        ),
        ConfigKeyword(
            flag="--llm-cheap-aws-region-name",
            env_var="MIDICODER_LLM_CHEAP_AWS_REGION_NAME",
            description="AWS region name for cheap-tier provider=bedrock",
            type="text",
            example="us-east-1",
        ),
        ConfigKeyword(
            flag="--llm-cheap-aws-access-key-id",
            env_var="MIDICODER_LLM_CHEAP_AWS_ACCESS_KEY_ID",
            description="AWS access key id for cheap-tier provider=bedrock",
            type="secret",
            example="AKIA...",
        ),
        ConfigKeyword(
            flag="--llm-cheap-aws-access-key-id-env",
            env_var="MIDICODER_LLM_CHEAP_AWS_ACCESS_KEY_ID_ENV",
            description="Env var name containing AWS access key id for cheap-tier provider=bedrock",
            type="text",
            example="AWS_ACCESS_KEY_ID",
        ),
        ConfigKeyword(
            flag="--llm-cheap-aws-secret-access-key",
            env_var="MIDICODER_LLM_CHEAP_AWS_SECRET_ACCESS_KEY",
            description="AWS secret access key for cheap-tier provider=bedrock",
            type="secret",
            example="wJalrXU...",
        ),
        ConfigKeyword(
            flag="--llm-cheap-aws-secret-access-key-env",
            env_var="MIDICODER_LLM_CHEAP_AWS_SECRET_ACCESS_KEY_ENV",
            description="Env var name containing AWS secret access key for cheap-tier provider=bedrock",
            type="text",
            example="AWS_SECRET_ACCESS_KEY",
        ),
        # Azure
        ConfigKeyword(
            flag="--llm-high-azure-model",
            env_var="MIDICODER_LLM_HIGH_AZURE_MODEL",
            description="High-tier model for provider=azure",
            type="text",
            example="azure/gpt-4o",
        ),
        ConfigKeyword(
            flag="--llm-high-azure-key",
            env_var="MIDICODER_LLM_HIGH_AZURE_API_KEY",
            description="High-tier API key for provider=azure",
            type="secret",
            example="sk-...",
        ),
        ConfigKeyword(
            flag="--llm-high-azure-key-env",
            env_var="MIDICODER_LLM_HIGH_AZURE_API_KEY_ENV",
            description="Env var name containing high-tier API key for provider=azure",
            type="text",
            example="AZURE_OPENAI_API_KEY",
        ),
        ConfigKeyword(
            flag="--llm-high-azure-openai-endpoint",
            env_var="MIDICODER_LLM_HIGH_AZURE_OPENAI_ENDPOINT",
            description="Azure OpenAI endpoint for high-tier provider=azure",
            type="text",
            example="https://my-resource.openai.azure.com",
        ),
        ConfigKeyword(
            flag="--llm-high-azure-openai-api-version",
            env_var="MIDICODER_LLM_HIGH_AZURE_OPENAI_API_VERSION",
            description="Azure OpenAI API version for high-tier provider=azure",
            type="text",
            example="2024-10-21",
        ),
        ConfigKeyword(
            flag="--llm-high-azure-openai-deployment",
            env_var="MIDICODER_LLM_HIGH_AZURE_OPENAI_DEPLOYMENT",
            description="Azure OpenAI deployment name for high-tier provider=azure",
            type="text",
            example="gpt-4o-prod",
        ),
        ConfigKeyword(
            flag="--llm-cheap-azure-model",
            env_var="MIDICODER_LLM_CHEAP_AZURE_MODEL",
            description="Cheap-tier model for provider=azure",
            type="text",
            example="azure/gpt-4o-mini",
        ),
        ConfigKeyword(
            flag="--llm-cheap-azure-key",
            env_var="MIDICODER_LLM_CHEAP_AZURE_API_KEY",
            description="Cheap-tier API key for provider=azure",
            type="secret",
            example="sk-...",
        ),
        ConfigKeyword(
            flag="--llm-cheap-azure-key-env",
            env_var="MIDICODER_LLM_CHEAP_AZURE_API_KEY_ENV",
            description="Env var name containing cheap-tier API key for provider=azure",
            type="text",
            example="AZURE_OPENAI_API_KEY",
        ),
        ConfigKeyword(
            flag="--llm-cheap-azure-openai-endpoint",
            env_var="MIDICODER_LLM_CHEAP_AZURE_OPENAI_ENDPOINT",
            description="Azure OpenAI endpoint for cheap-tier provider=azure",
            type="text",
            example="https://my-resource.openai.azure.com",
        ),
        ConfigKeyword(
            flag="--llm-cheap-azure-openai-api-version",
            env_var="MIDICODER_LLM_CHEAP_AZURE_OPENAI_API_VERSION",
            description="Azure OpenAI API version for cheap-tier provider=azure",
            type="text",
            example="2024-10-21",
        ),
        ConfigKeyword(
            flag="--llm-cheap-azure-openai-deployment",
            env_var="MIDICODER_LLM_CHEAP_AZURE_OPENAI_DEPLOYMENT",
            description="Azure OpenAI deployment name for cheap-tier provider=azure",
            type="text",
            example="gpt-4o-mini-dev",
        ),
        # Vertex Partner
        ConfigKeyword(
            flag="--llm-high-vertex-model",
            env_var="MIDICODER_LLM_HIGH_VERTEX_MODEL",
            description="High-tier model for provider=vertex_partner",
            type="text",
            example="vertex_ai/gemini-1.5-pro",
        ),
        ConfigKeyword(
            flag="--llm-high-vertex-key",
            env_var="MIDICODER_LLM_HIGH_VERTEX_API_KEY",
            description="High-tier API key for provider=vertex_partner",
            type="secret",
            example="AIza...",
        ),
        ConfigKeyword(
            flag="--llm-high-vertex-key-env",
            env_var="MIDICODER_LLM_HIGH_VERTEX_API_KEY_ENV",
            description="Env var name containing high-tier API key for provider=vertex_partner",
            type="text",
            example="VERTEX_API_KEY",
        ),
        ConfigKeyword(
            flag="--llm-high-vertex-project",
            env_var="MIDICODER_LLM_HIGH_VERTEX_PROJECT",
            description="Vertex project id for high-tier provider=vertex_partner",
            type="text",
            example="my-gcp-project",
        ),
        ConfigKeyword(
            flag="--llm-high-vertex-location",
            env_var="MIDICODER_LLM_HIGH_VERTEX_LOCATION",
            description="Vertex location for high-tier provider=vertex_partner",
            type="text",
            example="us-central1",
        ),
        ConfigKeyword(
            flag="--llm-cheap-vertex-model",
            env_var="MIDICODER_LLM_CHEAP_VERTEX_MODEL",
            description="Cheap-tier model for provider=vertex_partner",
            type="text",
            example="vertex_ai/gemini-1.5-flash",
        ),
        ConfigKeyword(
            flag="--llm-cheap-vertex-key",
            env_var="MIDICODER_LLM_CHEAP_VERTEX_API_KEY",
            description="Cheap-tier API key for provider=vertex_partner",
            type="secret",
            example="AIza...",
        ),
        ConfigKeyword(
            flag="--llm-cheap-vertex-key-env",
            env_var="MIDICODER_LLM_CHEAP_VERTEX_API_KEY_ENV",
            description="Env var name containing cheap-tier API key for provider=vertex_partner",
            type="text",
            example="VERTEX_API_KEY",
        ),
        ConfigKeyword(
            flag="--llm-cheap-vertex-project",
            env_var="MIDICODER_LLM_CHEAP_VERTEX_PROJECT",
            description="Vertex project id for cheap-tier provider=vertex_partner",
            type="text",
            example="my-gcp-project",
        ),
        ConfigKeyword(
            flag="--llm-cheap-vertex-location",
            env_var="MIDICODER_LLM_CHEAP_VERTEX_LOCATION",
            description="Vertex location for cheap-tier provider=vertex_partner",
            type="text",
            example="us-central1",
        ),
    ]

    @classmethod
    def get_by_flag(cls, flag: str) -> ConfigKeyword | None:
        """Get keyword by flag name."""
        for kw in cls.KEYWORDS:
            if kw.flag == flag:
                return kw
        return None

    @classmethod
    def get_by_env_var(cls, env_var: str) -> ConfigKeyword | None:
        """Get keyword by environment variable name."""
        for kw in cls.KEYWORDS:
            if kw.env_var == env_var:
                return kw
        return None

    @classmethod
    def print_help(cls) -> None:
        """Print formatted help for all keywords."""
        from midicoder.io import print_info, print_normal

        print_info("Available configuration keywords for 'midicoder init':", title="Configuration Keywords")
        print_normal("")

        categories = {
            "Working Directory": ["--working-dir"],
            "Stack Selection": ["--stack"],
            "Provider Selection": ["--llm-high-provider", "--llm-cheap-provider"],
            "Provider-specific (OpenAI Compatible)": [
                "--llm-high-model",
                "--llm-high-url",
                "--llm-high-key",
                "--llm-high-key-env",
                "--llm-cheap-model",
                "--llm-cheap-url",
                "--llm-cheap-key",
                "--llm-cheap-key-env",
            ],
            "Provider-specific (Anthropic)": [
                "--llm-high-anthropic-model",
                "--llm-high-anthropic-key",
                "--llm-high-anthropic-key-env",
                "--llm-cheap-anthropic-model",
                "--llm-cheap-anthropic-key",
                "--llm-cheap-anthropic-key-env",
            ],
            "Provider-specific (OpenAI)": [
                "--llm-high-openai-model",
                "--llm-high-openai-key",
                "--llm-high-openai-key-env",
                "--llm-cheap-openai-model",
                "--llm-cheap-openai-key",
                "--llm-cheap-openai-key-env",
            ],
            "Provider-specific (AWS Bedrock)": [
                "--llm-high-bedrock-model",
                "--llm-high-aws-region-name",
                "--llm-high-aws-access-key-id",
                "--llm-high-aws-access-key-id-env",
                "--llm-high-aws-secret-access-key",
                "--llm-high-aws-secret-access-key-env",
                "--llm-cheap-bedrock-model",
                "--llm-cheap-aws-region-name",
                "--llm-cheap-aws-access-key-id",
                "--llm-cheap-aws-access-key-id-env",
                "--llm-cheap-aws-secret-access-key",
                "--llm-cheap-aws-secret-access-key-env",
            ],
            "Provider-specific (Azure OpenAI)": [
                "--llm-high-azure-model",
                "--llm-high-azure-key",
                "--llm-high-azure-key-env",
                "--llm-high-azure-openai-endpoint",
                "--llm-high-azure-openai-api-version",
                "--llm-high-azure-openai-deployment",
                "--llm-cheap-azure-model",
                "--llm-cheap-azure-key",
                "--llm-cheap-azure-key-env",
                "--llm-cheap-azure-openai-endpoint",
                "--llm-cheap-azure-openai-api-version",
                "--llm-cheap-azure-openai-deployment",
            ],
            "Provider-specific (Vertex Partner / Vertex AI)": [
                "--llm-high-vertex-model",
                "--llm-high-vertex-key",
                "--llm-high-vertex-key-env",
                "--llm-high-vertex-project",
                "--llm-high-vertex-location",
                "--llm-cheap-vertex-model",
                "--llm-cheap-vertex-key",
                "--llm-cheap-vertex-key-env",
                "--llm-cheap-vertex-project",
                "--llm-cheap-vertex-location",
            ],
            "Mode": ["--non-interactive", "--env-prefix"],
            "Rewrite Policy": ["--rewrite-config"],
        }

        for category, flags in categories.items():
            print_normal(f"[bold]{category}:[/bold]")

            for flag in flags:
                kw = cls.get_by_flag(flag)
                if kw:
                    flag_display = f"  {kw.flag} TEXT"
                    desc_parts = [kw.description]

                    if kw.choices:
                        desc_parts.append(f"({', '.join(kw.choices)})")
                    if kw.required:
                        desc_parts.append("[bold red]*required[/bold red]")
                    if kw.default and kw.default != "<current directory>":
                        desc_parts.append(f"[dim](default: {kw.default})[/dim]")

                    print_normal(f"{flag_display:<40} {' '.join(desc_parts)}")
                    if kw.env_var:
                        print_normal(f"{'':40} [dim]Env: {kw.env_var}[/dim]")
                    if kw.example:
                        print_normal(f"{'':40} [dim]Example: {kw.example}[/dim]")
                    print_normal("")
                elif flag == "--non-interactive":
                    print_normal(f"  {flag:<38} Run without prompts, use flags/env vars/defaults")
                    print_normal("")
                elif flag == "--env-prefix":
                    print_normal(f"  {flag} TEXT{'':25} Environment variable prefix (default: MIDICODER_)")
                    print_normal("")
                elif flag == "--rewrite-config":
                    print_normal(f"  {flag:<38} Allow overwrite of existing config in non-interactive mode")
                    print_normal(f"{'':40} [dim]Env: MIDICODER_REWRITE_CONFIG=true[/dim]")
                    print_normal("")

            print_normal("")

        print_info("Examples:", title="Usage")
        print_normal("")
        print_normal("[bold]Interactive mode (default):[/bold]")
        print_normal("  midicoder init")
        print_normal("")
        print_normal("[bold]List available keywords:[/bold]")
        print_normal("  midicoder init --config-list")
        print_normal("")
        print_normal("[bold]Non-interactive with provider-specific flags:[/bold]")
        print_normal("  midicoder init --non-interactive \\")
        print_normal("    --working-dir /home/user/project \\")
        print_normal("    --stack fastapi,nest \\")
        print_normal("    --llm-high-provider anthropic \\")
        print_normal("    --llm-high-anthropic-model anthropic/claude-3-7-sonnet-latest \\")
        print_normal("    --llm-high-anthropic-key-env ANTHROPIC_API_KEY \\")
        print_normal("    --llm-cheap-provider openai_compatible \\")
        print_normal("    --llm-cheap-model openai/gpt-4o-mini \\")
        print_normal("    --llm-cheap-url https://api.openai.com/v1 \\")
        print_normal("    --llm-cheap-key-env OPENAI_API_KEY")
        print_normal("")
