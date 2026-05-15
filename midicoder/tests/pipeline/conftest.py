"""Conftest for pipeline tests — prevent real LLM calls.

Autouse fixture patches load_llm_config to raise, forcing
_generate_contracts_to_sqlite() into its placeholder fallback path.
This avoids 300s timeout × 10 retries × 7 categories hangs when
no LLM server is reachable.

Tests that need LLM integration override with @patch locally and
also mock call_llm to prevent actual HTTP requests.
"""

import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def _mock_no_llm_config():
    """Force placeholder fallback for all pipeline tests (no real LLM calls)."""
    with patch("midicoder.pipeline.commands.contract.load_llm_config", side_effect=Exception("No LLM config")):
        yield
