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
    """Keywords for 'midicoder init' command."""
    
    KEYWORDS = [
        ConfigKeyword(
            flag="--working-dir",
            env_var="MIDICODER_WORKING_DIR",
            description="Working directory path",
            type="text",
            required=False,
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
            flag="--llm-high-model",
            env_var="MIDICODER_LLM_HIGH_MODEL",
            description="High-tier LLM model name",
            type="text",
            required=True,
            example="claude-sonnet-4-5",
        ),
        ConfigKeyword(
            flag="--llm-high-url",
            env_var="MIDICODER_LLM_HIGH_URL",
            description="High-tier LLM API base URL (optional, provider-dependent)",
            type="text",
            required=False,
            example="https://api.anthropic.com",
        ),
        ConfigKeyword(
            flag="--llm-high-key",
            env_var="MIDICODER_LLM_HIGH_API_KEY",
            description="High-tier API key (WARNING: use --llm-high-key-env instead)",
            type="secret",
            required=False,
            example="sk-ant-api03-...",
        ),
        ConfigKeyword(
            flag="--llm-high-key-env",
            env_var="",
            description="Environment variable name containing high-tier API key (recommended)",
            type="text",
            required=False,
            example="ANTHROPIC_API_KEY",
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
        ConfigKeyword(
            flag="--llm-cheap-model",
            env_var="MIDICODER_LLM_CHEAP_MODEL",
            description="Cheap-tier LLM model name",
            type="text",
            required=True,
            example="claude-3-5-haiku",
        ),
        ConfigKeyword(
            flag="--llm-cheap-url",
            env_var="MIDICODER_LLM_CHEAP_URL",
            description="Cheap-tier LLM API base URL (optional, provider-dependent)",
            type="text",
            required=False,
            example="https://api.anthropic.com",
        ),
        ConfigKeyword(
            flag="--llm-cheap-key",
            env_var="MIDICODER_LLM_CHEAP_API_KEY",
            description="Cheap-tier API key (WARNING: use --llm-cheap-key-env instead)",
            type="secret",
            required=False,
            example="sk-ant-api03-...",
        ),
        ConfigKeyword(
            flag="--llm-cheap-key-env",
            env_var="",
            description="Environment variable name containing cheap-tier API key (recommended)",
            type="text",
            required=False,
            example="ANTHROPIC_API_KEY",
        ),
        # Provider-specific (AWS Bedrock)
        ConfigKeyword(
            flag="--llm-high-aws-region-name",
            env_var="MIDICODER_LLM_HIGH_AWS_REGION_NAME",
            description="AWS region name for high-tier provider=bedrock",
            type="text",
            required=False,
            example="us-east-1",
        ),
        ConfigKeyword(
            flag="--llm-high-aws-access-key-id",
            env_var="MIDICODER_LLM_HIGH_AWS_ACCESS_KEY_ID",
            description="AWS access key id for high-tier provider=bedrock",
            type="secret",
            required=False,
            example="AKIA...",
        ),
        ConfigKeyword(
            flag="--llm-high-aws-access-key-id-env",
            env_var="",
            description="Environment variable name containing AWS access key id for high-tier provider=bedrock",
            type="text",
            required=False,
            example="AWS_ACCESS_KEY_ID",
        ),
        ConfigKeyword(
            flag="--llm-high-aws-secret-access-key",
            env_var="MIDICODER_LLM_HIGH_AWS_SECRET_ACCESS_KEY",
            description="AWS secret access key for high-tier provider=bedrock",
            type="secret",
            required=False,
            example="wJalrXUtnFEMI/K7MDENG/bPxRfiCY...",
        ),
        ConfigKeyword(
            flag="--llm-high-aws-secret-access-key-env",
            env_var="",
            description="Environment variable name containing AWS secret access key for high-tier provider=bedrock",
            type="text",
            required=False,
            example="AWS_SECRET_ACCESS_KEY",
        ),
        ConfigKeyword(
            flag="--llm-cheap-aws-region-name",
            env_var="MIDICODER_LLM_CHEAP_AWS_REGION_NAME",
            description="AWS region name for cheap-tier provider=bedrock",
            type="text",
            required=False,
            example="us-east-1",
        ),
        ConfigKeyword(
            flag="--llm-cheap-aws-access-key-id",
            env_var="MIDICODER_LLM_CHEAP_AWS_ACCESS_KEY_ID",
            description="AWS access key id for cheap-tier provider=bedrock",
            type="secret",
            required=False,
            example="AKIA...",
        ),
        ConfigKeyword(
            flag="--llm-cheap-aws-access-key-id-env",
            env_var="",
            description="Environment variable name containing AWS access key id for cheap-tier provider=bedrock",
            type="text",
            required=False,
            example="AWS_ACCESS_KEY_ID",
        ),
        ConfigKeyword(
            flag="--llm-cheap-aws-secret-access-key",
            env_var="MIDICODER_LLM_CHEAP_AWS_SECRET_ACCESS_KEY",
            description="AWS secret access key for cheap-tier provider=bedrock",
            type="secret",
            required=False,
            example="wJalrXUtnFEMI/K7MDENG/bPxRfiCY...",
        ),
        ConfigKeyword(
            flag="--llm-cheap-aws-secret-access-key-env",
            env_var="",
            description="Environment variable name containing AWS secret access key for cheap-tier provider=bedrock",
            type="text",
            required=False,
            example="AWS_SECRET_ACCESS_KEY",
        ),
        # Provider-specific (Azure OpenAI)
        ConfigKeyword(
            flag="--llm-high-azure-openai-endpoint",
            env_var="MIDICODER_LLM_HIGH_AZURE_OPENAI_ENDPOINT",
            description="Azure OpenAI endpoint for high-tier provider=azure",
            type="text",
            required=False,
            example="https://my-resource.openai.azure.com",
        ),
        ConfigKeyword(
            flag="--llm-high-azure-openai-api-version",
            env_var="MIDICODER_LLM_HIGH_AZURE_OPENAI_API_VERSION",
            description="Azure OpenAI API version for high-tier provider=azure",
            type="text",
            required=False,
            example="2024-10-21",
        ),
        ConfigKeyword(
            flag="--llm-high-azure-openai-deployment",
            env_var="MIDICODER_LLM_HIGH_AZURE_OPENAI_DEPLOYMENT",
            description="Azure OpenAI deployment name for high-tier provider=azure",
            type="text",
            required=False,
            example="gpt-4o-prod",
        ),
        ConfigKeyword(
            flag="--llm-cheap-azure-openai-endpoint",
            env_var="MIDICODER_LLM_CHEAP_AZURE_OPENAI_ENDPOINT",
            description="Azure OpenAI endpoint for cheap-tier provider=azure",
            type="text",
            required=False,
            example="https://my-resource.openai.azure.com",
        ),
        ConfigKeyword(
            flag="--llm-cheap-azure-openai-api-version",
            env_var="MIDICODER_LLM_CHEAP_AZURE_OPENAI_API_VERSION",
            description="Azure OpenAI API version for cheap-tier provider=azure",
            type="text",
            required=False,
            example="2024-10-21",
        ),
        ConfigKeyword(
            flag="--llm-cheap-azure-openai-deployment",
            env_var="MIDICODER_LLM_CHEAP_AZURE_OPENAI_DEPLOYMENT",
            description="Azure OpenAI deployment name for cheap-tier provider=azure",
            type="text",
            required=False,
            example="gpt-4o-mini-dev",
        ),
        # Provider-specific (Vertex Partner / Vertex AI)
        ConfigKeyword(
            flag="--llm-high-vertex-project",
            env_var="MIDICODER_LLM_HIGH_VERTEX_PROJECT",
            description="Vertex project id for high-tier provider=vertex_partner",
            type="text",
            required=False,
            example="my-gcp-project",
        ),
        ConfigKeyword(
            flag="--llm-high-vertex-location",
            env_var="MIDICODER_LLM_HIGH_VERTEX_LOCATION",
            description="Vertex location for high-tier provider=vertex_partner",
            type="text",
            required=False,
            example="us-central1",
        ),
        ConfigKeyword(
            flag="--llm-cheap-vertex-project",
            env_var="MIDICODER_LLM_CHEAP_VERTEX_PROJECT",
            description="Vertex project id for cheap-tier provider=vertex_partner",
            type="text",
            required=False,
            example="my-gcp-project",
        ),
        ConfigKeyword(
            flag="--llm-cheap-vertex-location",
            env_var="MIDICODER_LLM_CHEAP_VERTEX_LOCATION",
            description="Vertex location for cheap-tier provider=vertex_partner",
            type="text",
            required=False,
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
        from midicoder.io import print_normal, print_info
        
        print_info("Available configuration keywords for 'midicoder init':", title="Configuration Keywords")
        print_normal("")
        
        # Group by category
        categories = {
            "Working Directory": ["--working-dir"],
            "Stack Selection": ["--stack"],
            "LLM Configuration (High Tier)": [
                "--llm-high-provider",
                "--llm-high-model",
                "--llm-high-url",
                "--llm-high-key",
                "--llm-high-key-env",
            ],
            "LLM Configuration (Cheap Tier)": [
                "--llm-cheap-provider",
                "--llm-cheap-model",
                "--llm-cheap-url",
                "--llm-cheap-key",
                "--llm-cheap-key-env",
            ],
            "Provider-specific (AWS Bedrock)": [
                "--llm-high-aws-region-name",
                "--llm-high-aws-access-key-id",
                "--llm-high-aws-access-key-id-env",
                "--llm-high-aws-secret-access-key",
                "--llm-high-aws-secret-access-key-env",
                "--llm-cheap-aws-region-name",
                "--llm-cheap-aws-access-key-id",
                "--llm-cheap-aws-access-key-id-env",
                "--llm-cheap-aws-secret-access-key",
                "--llm-cheap-aws-secret-access-key-env",
            ],
            "Provider-specific (Azure OpenAI)": [
                "--llm-high-azure-openai-endpoint",
                "--llm-high-azure-openai-api-version",
                "--llm-high-azure-openai-deployment",
                "--llm-cheap-azure-openai-endpoint",
                "--llm-cheap-azure-openai-api-version",
                "--llm-cheap-azure-openai-deployment",
            ],
            "Provider-specific (Vertex Partner / Vertex AI)": [
                "--llm-high-vertex-project",
                "--llm-high-vertex-location",
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
                    # Format flag with type
                    flag_display = f"  {kw.flag} TEXT"
                    
                    # Add description
                    desc_parts = [kw.description]
                    
                    # Add choices if applicable
                    if kw.choices:
                        desc_parts.append(f"({', '.join(kw.choices)})")
                    
                    # Add required indicator
                    if kw.required:
                        desc_parts.append("[bold red]*required[/bold red]")
                    
                    # Add default if available
                    if kw.default and kw.default != "<current directory>":
                        desc_parts.append(f"[dim](default: {kw.default})[/dim]")
                    
                    print_normal(f"{flag_display:<30} {' '.join(desc_parts)}")
                    
                    # Add environment variable info
                    if kw.env_var:
                        print_normal(f"{'':30} [dim]Env: {kw.env_var}[/dim]")
                    
                    # Add example
                    if kw.example:
                        print_normal(f"{'':30} [dim]Example: {kw.example}[/dim]")
                    
                    print_normal("")
                elif flag == "--non-interactive":
                    print_normal(f"  {flag:<28} Run without prompts, use flags/env vars/defaults")
                    print_normal("")
                elif flag == "--env-prefix":
                    print_normal(f"  {flag} TEXT{'':15} Environment variable prefix (default: MIDICODER_)")
                    print_normal("")
                elif flag == "--rewrite-config":
                    print_normal(
                        f"  {flag:<28} Allow overwrite of existing config in non-interactive mode"
                    )
                    print_normal(f"{'':30} [dim]Env: MIDICODER_REWRITE_CONFIG=true[/dim]")
                    print_normal("")
            
            print_normal("")
        
        # Print examples
        print_info("Examples:", title="Usage")
        print_normal("")
        print_normal("[bold]Interactive mode (default):[/bold]")
        print_normal("  midicoder init")
        print_normal("")
        print_normal("[bold]List available keywords:[/bold]")
        print_normal("  midicoder init --config-list")
        print_normal("")
        print_normal("[bold]Non-interactive with flags:[/bold]")
        print_normal("  midicoder init --non-interactive \\")
        print_normal("    --working-dir /home/user/project \\")
        print_normal("    --stack fastapi,nest \\")
        print_normal("    --llm-high-provider anthropic \\")
        print_normal("    --llm-high-model anthropic/claude-3-7-sonnet-latest \\")
        print_normal("    --llm-high-url https://api.anthropic.com \\")
        print_normal("    --llm-high-key-env ANTHROPIC_API_KEY \\")
        print_normal("    --llm-cheap-provider anthropic \\")
        print_normal("    --llm-cheap-model anthropic/claude-3-5-haiku-latest \\")
        print_normal("    --llm-cheap-url https://api.anthropic.com \\")
        print_normal("    --llm-cheap-key-env ANTHROPIC_API_KEY")
        print_normal("")
        print_normal("[bold]Non-interactive with provider-specific Azure OpenAI fields:[/bold]")
        print_normal("  midicoder init --non-interactive \\")
        print_normal("    --working-dir /home/user/project \\")
        print_normal("    --stack fastapi \\")
        print_normal("    --llm-high-provider azure \\")
        print_normal("    --llm-high-model azure/gpt-4o \\")
        print_normal("    --llm-high-azure-openai-endpoint https://my-resource.openai.azure.com \\")
        print_normal("    --llm-high-azure-openai-api-version 2024-10-21 \\")
        print_normal("    --llm-high-azure-openai-deployment gpt-4o-prod \\")
        print_normal("    --llm-high-key-env AZURE_OPENAI_API_KEY")
        print_normal("")
        print_normal("[bold]Non-interactive with environment variables:[/bold]")
        print_normal("  export MIDICODER_WORKING_DIR=/home/user/project")
        print_normal("  export MIDICODER_STACK=fastapi,nest")
        print_normal("  export MIDICODER_LLM_HIGH_PROVIDER=anthropic")
        print_normal("  export MIDICODER_LLM_HIGH_MODEL=anthropic/claude-3-7-sonnet-latest")
        print_normal("  export MIDICODER_LLM_HIGH_URL=https://api.anthropic.com")
        print_normal("  export MIDICODER_LLM_HIGH_API_KEY=sk-ant-...")
        print_normal("  # ... set other env vars ...")
        print_normal("  midicoder init --non-interactive")
        print_normal("")
