"""Midicoder CLI entrypoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from midicoder.config.defaults import LLM_PROVIDERS
from midicoder.commands import (
    brief as brief_commands,
    code as code_commands,
    config as config_commands,
    contract as contract_commands,
    index as index_commands,
    init as init_commands,
    ir as ir_commands,
    runtime as runtime_commands,
    version as version_commands,
)


def _find_midicoder_root() -> Path:
    """
    Find the Midicoder project root by looking for .midicoder directory.
    Searches up from current working directory.
    """
    current = Path.cwd()
    
    # Check current directory and all parent directories
    for path in [current] + list(current.parents):
        if (path / ".midicoder").exists():
            return path
    
    # If no .midicoder found, return current directory (for init command)
    return current


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="midicoder")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Init command with non-interactive support
    init_parser = subparsers.add_parser("init", help="Initialize .midicoder workspace and configuration")

    # Discovery
    init_parser.add_argument(
        "--config-list",
        action="store_true",
        help="Show all available configuration keywords and exit"
    )
    
    # Mode
    init_parser.add_argument(
        "--non-interactive", "-y",
        action="store_true",
        help="Run in non-interactive mode, use flags/env vars/defaults"
    )
    
    init_parser.add_argument(
        "--env-prefix",
        type=str,
        default="MIDICODER_",
        help="Environment variable prefix (default: MIDICODER_)"
    )
    init_parser.add_argument(
        "--rewrite-config",
        action="store_true",
        default=None,
        help="Allow overwriting existing .midicoder/config.json in non-interactive mode"
    )
    
    # Working directory
    init_parser.add_argument(
        "--working-dir",
        type=str,
        help="Working directory path"
    )
    
    # Stack
    init_parser.add_argument(
        "--stack",
        type=str,
        help="Comma-separated tech stack(s) (e.g., fastapi,nest,angular)"
    )
    
    # LLM High Tier
    init_parser.add_argument(
        "--llm-high-provider",
        type=str,
        choices=LLM_PROVIDERS,
        help="High-tier LLM provider"
    )
    init_parser.add_argument(
        "--llm-high-model",
        type=str,
        help="High-tier LLM model name (e.g., claude-sonnet-4-5)"
    )
    init_parser.add_argument(
        "--llm-high-url",
        type=str,
        help="High-tier LLM API base URL"
    )
    init_parser.add_argument(
        "--llm-high-key",
        type=str,
        help="High-tier API key (WARNING: visible in process list, use --llm-high-key-env instead)"
    )
    init_parser.add_argument(
        "--llm-high-key-env",
        type=str,
        help="Environment variable name containing high-tier API key (recommended)"
    )
    
    # LLM Cheap Tier
    init_parser.add_argument(
        "--llm-cheap-provider",
        type=str,
        choices=LLM_PROVIDERS,
        help="Cheap-tier LLM provider"
    )
    init_parser.add_argument(
        "--llm-cheap-model",
        type=str,
        help="Cheap-tier LLM model name (e.g., claude-3-5-haiku)"
    )
    init_parser.add_argument(
        "--llm-cheap-url",
        type=str,
        help="Cheap-tier LLM API base URL"
    )
    init_parser.add_argument(
        "--llm-cheap-key",
        type=str,
        help="Cheap-tier API key (WARNING: visible in process list, use --llm-cheap-key-env instead)"
    )
    init_parser.add_argument(
        "--llm-cheap-key-env",
        type=str,
        help="Environment variable name containing cheap-tier API key (recommended)"
    )

    # Provider-specific options (AWS Bedrock)
    init_parser.add_argument(
        "--llm-high-aws-bedrock-region",
        type=str,
        help="AWS Bedrock region for high-tier provider=aws_bedrock"
    )
    init_parser.add_argument(
        "--llm-cheap-aws-bedrock-region",
        type=str,
        help="AWS Bedrock region for cheap-tier provider=aws_bedrock"
    )

    # Provider-specific options (Azure OpenAI)
    init_parser.add_argument(
        "--llm-high-azure-openai-endpoint",
        type=str,
        help="Azure OpenAI endpoint for high-tier provider=azure_openai"
    )
    init_parser.add_argument(
        "--llm-high-azure-openai-api-version",
        type=str,
        help="Azure OpenAI API version for high-tier provider=azure_openai"
    )
    init_parser.add_argument(
        "--llm-high-azure-openai-deployment",
        type=str,
        help="Azure OpenAI deployment name for high-tier provider=azure_openai"
    )
    init_parser.add_argument(
        "--llm-cheap-azure-openai-endpoint",
        type=str,
        help="Azure OpenAI endpoint for cheap-tier provider=azure_openai"
    )
    init_parser.add_argument(
        "--llm-cheap-azure-openai-api-version",
        type=str,
        help="Azure OpenAI API version for cheap-tier provider=azure_openai"
    )
    init_parser.add_argument(
        "--llm-cheap-azure-openai-deployment",
        type=str,
        help="Azure OpenAI deployment name for cheap-tier provider=azure_openai"
    )

    # Provider-specific options (Google Vertex)
    init_parser.add_argument(
        "--llm-high-google-vertex-project",
        type=str,
        help="Google Vertex project id for high-tier provider=google_vertex"
    )
    init_parser.add_argument(
        "--llm-high-google-vertex-location",
        type=str,
        help="Google Vertex location for high-tier provider=google_vertex"
    )
    init_parser.add_argument(
        "--llm-cheap-google-vertex-project",
        type=str,
        help="Google Vertex project id for cheap-tier provider=google_vertex"
    )
    init_parser.add_argument(
        "--llm-cheap-google-vertex-location",
        type=str,
        help="Google Vertex location for cheap-tier provider=google_vertex"
    )
    
    
    index_parser = subparsers.add_parser("index")
    index_sub = index_parser.add_subparsers(dest="index_subcommand", required=False)
    reindex_parser = index_sub.add_parser("reindex")
    reindex_parser.add_argument(
        "--path",
        nargs="+",
        default=[],
        help="List of changed file paths (relative to working_dir).",
    )

    config_parser = subparsers.add_parser("config")
    config_sub = config_parser.add_subparsers(dest="subcommand", required=True)
    
    config_get = config_sub.add_parser("get")
    config_get.add_argument("key")
    
    config_set = config_sub.add_parser("set")
    config_set.add_argument("key")
    config_set.add_argument("value")
    
    config_sub.add_parser("list")
    config_sub.add_parser("validate")
    
    config_secrets = config_sub.add_parser("secrets")
    config_secrets_sub = config_secrets.add_subparsers(dest="secrets_subcommand", required=True)
    
    config_secrets_sub.add_parser("list")
    
    config_secrets_get = config_secrets_sub.add_parser("get")
    config_secrets_get.add_argument("category")
    config_secrets_get.add_argument("key")
    
    config_secrets_set = config_secrets_sub.add_parser("set")
    config_secrets_set.add_argument("category")
    config_secrets_set.add_argument("key")
    
    config_secrets_delete = config_secrets_sub.add_parser("delete")
    config_secrets_delete.add_argument("category")
    
    config_sub.add_parser("reset")

    version_parser = subparsers.add_parser("version")
    version_sub = version_parser.add_subparsers(dest="subcommand", required=True)
    version_create = version_sub.add_parser("create")
    version_create.add_argument("version")

    brief_parser = subparsers.add_parser("brief")
    brief_sub = brief_parser.add_subparsers(dest="subcommand", required=True)
    brief_sub.add_parser("analyze")
    brief_sub.add_parser("rewrite")

    contract_parser = subparsers.add_parser("contract")
    contract_sub = contract_parser.add_subparsers(dest="subcommand", required=True)
    
    contract_gen = contract_sub.add_parser("gen")
    contract_gen_sub = contract_gen.add_subparsers(dest="gen_subcommand", required=False)
    contract_gen_sub.add_parser("resume")
    
    contract_sub.add_parser("check")
    contract_sub.add_parser("feedback")
    
    contract_repair = contract_sub.add_parser("repair")
    contract_repair_sub = contract_repair.add_subparsers(dest="repair_subcommand", required=True)
    contract_repair_sub.add_parser("prepare")
    contract_repair_sub.add_parser("run")

    ir_parser = subparsers.add_parser("ir")
    ir_sub = ir_parser.add_subparsers(dest="subcommand", required=True)
    ir_build = ir_sub.add_parser("build")
    ir_build.add_argument("--skip-diagrams", action="store_true", help="Skip diagram generation")

    code_parser = subparsers.add_parser("code")
    code_sub = code_parser.add_subparsers(dest="subcommand", required=True)
    code_sub.add_parser("build", help="Build code-plan artifacts from IR")
    code_sub.add_parser("plan", help="Alias of code build")
    code_gen = code_sub.add_parser(
        "gen",
        help="Generate patch-plan artifacts (default) and optional runtime files with --runtime",
    )
    code_gen.add_argument(
        "--runtime",
        action="store_true",
        help="Also generate runtime source files into .midicoder/.../patches/runtime",
    )
    code_apply = code_sub.add_parser("apply", help="Apply generated patch-plans into working_dir")
    code_apply.add_argument("--force", action="store_true", help="Force apply when conflict is detected")
    code_apply.add_argument("--dry-run", action="store_true", help="Preview apply without writing files")
    code_apply.add_argument(
        "--no-reindex",
        action="store_true",
        help="Disable queue reindexing before/after apply (debug only)",
    )
    code_apply.add_argument(
        "--patches-dir",
        type=str,
        help="Custom patches directory (relative to version folder, e.g., 'patches/runtime-fix/20260313T120000Z')",
    )

    # Runtime commands
    runtime_parser = subparsers.add_parser(
        "runtime",
        help="Runtime testing and auto-fix commands"
    )
    runtime_sub = runtime_parser.add_subparsers(dest="subcommand", required=True)
    
    # Runtime test
    runtime_test = runtime_sub.add_parser(
        "test",
        help="Run FastAPI application and detect runtime errors"
    )
    runtime_test.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds for app startup (default: 30)"
    )
    runtime_test.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for FastAPI application (default: 8000)"
    )
    runtime_test.add_argument(
        "--verbose",
        action="store_true",
        help="Show verbose output during test"
    )
    
    # Runtime fix
    runtime_fix = runtime_sub.add_parser(
        "fix",
        help="Generate patch plans to fix runtime errors using LLM"
    )
    runtime_fix.add_argument(
        "--log-timestamp",
        type=str,
        help="Specific log timestamp to fix (default: latest error log)"
    )
    runtime_fix.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview fixes without saving patch plans"
    )
    runtime_fix.add_argument(
        "--auto-apply",
        action="store_true",
        help="Automatically apply generated runtime-fix patches via `midicoder code apply`",
    )
    runtime_fix.add_argument(
        "--auto-fix-loop",
        action="store_true",
        help=(
            "Run loop: `runtime test` -> `runtime fix` -> auto-apply until runtime test passes "
            "(includes auto-apply)"
        ),
    )
    runtime_fix.add_argument(
        "--test-timeout",
        type=int,
        default=30,
        help="Timeout in seconds for each runtime test when --auto-fix-loop is enabled (default: 30)",
    )
    runtime_fix.add_argument(
        "--test-port",
        type=int,
        default=8000,
        help="Port for each runtime test when --auto-fix-loop is enabled (default: 8000)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    root = _find_midicoder_root()

    if args.command == "init":
        init_commands.run(root, args)
    elif args.command == "index":
        if getattr(args, "index_subcommand", None) == "reindex":
            index_commands.reindex(root, changed_paths=args.path)
        else:
            index_commands.run(root)
    elif args.command == "config":
        if args.subcommand == "get":
            config_commands.get_value(root, args.key)
        elif args.subcommand == "set":
            config_commands.set_value(root, args.key, args.value)
        elif args.subcommand == "list":
            config_commands.list_config(root)
        elif args.subcommand == "validate":
            config_commands.validate_config(root)
        elif args.subcommand == "secrets":
            if args.secrets_subcommand == "list":
                config_commands.list_secrets(root)
            elif args.secrets_subcommand == "get":
                config_commands.get_secret(root, args.category, args.key)
            elif args.secrets_subcommand == "set":
                config_commands.set_secret(root, args.category, args.key)
            elif args.secrets_subcommand == "delete":
                config_commands.delete_secrets_category(root, args.category)
        elif args.subcommand == "reset":
            config_commands.reset_config(root)
    elif args.command == "version" and args.subcommand == "create":
        version_commands.create(root, args.version)
    elif args.command == "brief" and args.subcommand == "analyze":
        brief_commands.analyze(root)
    elif args.command == "brief" and args.subcommand == "rewrite":
        brief_commands.rewrite(root)
    elif args.command == "contract" and args.subcommand == "gen":
        if hasattr(args, 'gen_subcommand') and args.gen_subcommand == "resume":
            contract_commands.gen_resume(root)
        else:
            contract_commands.gen(root)
    elif args.command == "contract" and args.subcommand == "check":
        contract_commands.check(root)
    elif args.command == "contract" and args.subcommand == "feedback":
        contract_commands.feedback(root)
    elif args.command == "contract" and args.subcommand == "repair":
        if args.repair_subcommand == "prepare":
            contract_commands.repair_prepare(root)
        elif args.repair_subcommand == "run":
            contract_commands.repair_run(root)
        else:
            parser.error("Unknown contract repair subcommand")
    elif args.command == "ir" and args.subcommand == "build":
        skip_diagrams = getattr(args, 'skip_diagrams', False)
        ir_commands.build(root, skip_diagrams=skip_diagrams)
    elif args.command == "code" and args.subcommand == "build":
        code_commands.build(root)
    elif args.command == "code" and args.subcommand == "gen":
        code_commands.gen(root, runtime=bool(getattr(args, "runtime", False)))
    elif args.command == "code" and args.subcommand == "apply":
        code_commands.apply(
            root,
            force=bool(getattr(args, "force", False)),
            dry_run=bool(getattr(args, "dry_run", False)),
            reindex=not bool(getattr(args, "no_reindex", False)),
            patches_subdir=getattr(args, "patches_dir", None),
        )
    elif args.command == "runtime":
        if args.subcommand == "test":
            runtime_commands.test(root, args)
        elif args.subcommand == "fix":
            runtime_commands.fix(root, args)
        else:
            parser.error("Unknown runtime subcommand")
    else:
        parser.error("Unknown command")
    return 0


def app() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    app()
