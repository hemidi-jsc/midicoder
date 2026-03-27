"""Unit tests for init CLI parser."""

from midicoder.cli import _build_parser


def test_init_parser_supports_core_non_interactive_flags() -> None:
    parser = _build_parser()
    args = parser.parse_args(
        [
            "init",
            "--non-interactive",
            "--config-list",
            "--env-prefix",
            "MC_",
            "--rewrite-config",
            "--working-dir",
            "/tmp/project",
            "--stack",
            "fastapi,nest",
        ]
    )

    assert args.command == "init"
    assert args.non_interactive is True
    assert args.config_list is True
    assert args.env_prefix == "MC_"
    assert args.rewrite_config is True
    assert args.working_dir == "/tmp/project"
    assert args.stack == "fastapi,nest"


def test_init_parser_supports_openai_compatible_flags() -> None:
    parser = _build_parser()
    args = parser.parse_args(
        [
            "init",
            "--non-interactive",
            "--llm-high-provider",
            "openai_compatible",
            "--llm-high-model",
            "openai/gpt-4o",
            "--llm-high-url",
            "https://example.com/v1",
            "--llm-cheap-provider",
            "openai_compatible",
            "--llm-cheap-model",
            "openai/gpt-4o-mini",
            "--llm-cheap-url",
            "https://example.com/v1",
        ]
    )

    assert args.llm_high_provider == "openai_compatible"
    assert args.llm_high_model == "openai/gpt-4o"
    assert args.llm_high_url == "https://example.com/v1"
    assert args.llm_cheap_provider == "openai_compatible"
    assert args.llm_cheap_model == "openai/gpt-4o-mini"
    assert args.llm_cheap_url == "https://example.com/v1"


def test_init_parser_supports_provider_specific_flags() -> None:
    parser = _build_parser()
    args = parser.parse_args(
        [
            "init",
            "--non-interactive",
            "--llm-high-provider",
            "azure",
            "--llm-high-azure-model",
            "azure/gpt-4o",
            "--llm-high-azure-openai-endpoint",
            "https://my-resource.openai.azure.com",
            "--llm-high-azure-openai-api-version",
            "2024-10-21",
            "--llm-high-azure-openai-deployment",
            "gpt-4o-prod",
            "--llm-cheap-provider",
            "vertex_partner",
            "--llm-cheap-vertex-model",
            "vertex_ai/gemini-1.5-flash",
            "--llm-cheap-vertex-project",
            "demo-project",
            "--llm-cheap-vertex-location",
            "us-central1",
        ]
    )

    assert args.llm_high_provider == "azure"
    assert args.llm_high_azure_model == "azure/gpt-4o"
    assert args.llm_high_azure_openai_endpoint == "https://my-resource.openai.azure.com"
    assert args.llm_cheap_provider == "vertex_partner"
    assert args.llm_cheap_vertex_model == "vertex_ai/gemini-1.5-flash"
    assert args.llm_cheap_vertex_project == "demo-project"


def test_init_parser_rejects_unknown_init_flag() -> None:
    parser = _build_parser()

    try:
        parser.parse_args(["init", "--force"])
    except SystemExit as exc:
        assert exc.code != 0
    else:
        raise AssertionError("Expected parser to reject --force for init")
