"""Unit tests for init CLI parser provider support."""

from midicoder.cli import _build_parser


def test_init_parser_accepts_new_provider_choices() -> None:
    """Init parser should accept cloud providers in provider choices."""
    parser = _build_parser()
    args = parser.parse_args(
        [
            "init",
            "--non-interactive",
            "--stack",
            "fastapi",
            "--llm-high-provider",
            "azure_openai",
            "--llm-high-model",
            "azure/gpt-4o",
            "--llm-high-url",
            "https://example.com",
            "--llm-cheap-provider",
            "google_vertex",
            "--llm-cheap-model",
            "vertex_ai/gemini-1.5-flash",
            "--llm-cheap-url",
            "https://example.com",
        ]
    )

    assert args.command == "init"
    assert args.llm_high_provider == "azure_openai"
    assert args.llm_cheap_provider == "google_vertex"


def test_init_parser_accepts_provider_specific_flags() -> None:
    """Init parser should parse provider-specific cloud fields without error."""
    parser = _build_parser()
    args = parser.parse_args(
        [
            "init",
            "--non-interactive",
            "--stack",
            "fastapi",
            "--llm-high-provider",
            "aws_bedrock",
            "--llm-high-model",
            "bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0",
            "--llm-high-url",
            "https://example.com",
            "--llm-high-aws-bedrock-region",
            "us-east-1",
            "--llm-cheap-provider",
            "azure_openai",
            "--llm-cheap-model",
            "azure/gpt-4o-mini",
            "--llm-cheap-url",
            "https://example.com",
            "--llm-cheap-azure-openai-endpoint",
            "https://my-resource.openai.azure.com",
            "--llm-cheap-azure-openai-api-version",
            "2024-10-21",
            "--llm-cheap-azure-openai-deployment",
            "gpt-4o-mini-dev",
        ]
    )

    assert args.llm_high_aws_bedrock_region == "us-east-1"
    assert args.llm_cheap_azure_openai_endpoint == "https://my-resource.openai.azure.com"
    assert args.llm_cheap_azure_openai_api_version == "2024-10-21"
    assert args.llm_cheap_azure_openai_deployment == "gpt-4o-mini-dev"


def test_init_parser_accepts_rewrite_config_flag() -> None:
    """Init parser should parse explicit rewrite policy flag."""
    parser = _build_parser()
    args = parser.parse_args(["init", "--non-interactive", "--rewrite-config"])
    assert args.rewrite_config is True
