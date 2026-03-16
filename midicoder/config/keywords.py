"""Configuration keywords registry for non-interactive mode."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
            choices=["fastapi", "nest", "angular"],
            example="fastapi,nest",
        ),
        ConfigKeyword(
            flag="--llm-high-provider",
            env_var="MIDICODER_LLM_HIGH_PROVIDER",
            description="High-tier LLM provider",
            type="choice",
            required=True,
            choices=["anthropic", "openai"],
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
            description="High-tier LLM API base URL",
            type="text",
            required=True,
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
            choices=["anthropic", "openai"],
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
            description="Cheap-tier LLM API base URL",
            type="text",
            required=True,
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
            "Mode": ["--non-interactive", "--env-prefix"],
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
        print_normal("    --llm-high-model claude-sonnet-4-5 \\")
        print_normal("    --llm-high-url https://api.anthropic.com \\")
        print_normal("    --llm-high-key-env ANTHROPIC_API_KEY \\")
        print_normal("    --llm-cheap-provider anthropic \\")
        print_normal("    --llm-cheap-model claude-3-5-haiku \\")
        print_normal("    --llm-cheap-url https://api.anthropic.com \\")
        print_normal("    --llm-cheap-key-env ANTHROPIC_API_KEY")
        print_normal("")
        print_normal("[bold]Non-interactive with environment variables:[/bold]")
        print_normal("  export MIDICODER_WORKING_DIR=/home/user/project")
        print_normal("  export MIDICODER_STACK=fastapi,nest")
        print_normal("  export MIDICODER_LLM_HIGH_PROVIDER=anthropic")
        print_normal("  export MIDICODER_LLM_HIGH_MODEL=claude-sonnet-4-5")
        print_normal("  export MIDICODER_LLM_HIGH_URL=https://api.anthropic.com")
        print_normal("  export MIDICODER_LLM_HIGH_API_KEY=sk-ant-...")
        print_normal("  # ... set other env vars ...")
        print_normal("  midicoder init --non-interactive")
        print_normal("")
