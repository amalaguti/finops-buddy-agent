"""Tests for agent-module-structure spec: module layout and importability."""

import sys


def test_public_api_importable_from_runner():
    """Public API remains importable from runner (build_agent, run_chat_loop)."""
    from finops_buddy.agent.runner import build_agent, run_chat_loop

    assert callable(build_agent)
    assert callable(run_chat_loop)


def test_mcp_logic_in_mcp_module():
    """MCP client creation and helpers live in mcp.py."""
    from finops_buddy.agent import mcp

    assert hasattr(mcp, "create_knowledge_mcp_client")
    assert hasattr(mcp, "create_billing_mcp_client")
    assert hasattr(mcp, "create_documentation_mcp_client")
    assert hasattr(mcp, "create_cost_explorer_mcp_client")
    assert hasattr(mcp, "create_pricing_mcp_client")
    assert hasattr(mcp, "create_core_mcp_client")
    assert hasattr(mcp, "_format_mcp_status")
    assert hasattr(mcp, "_mcp_server_names_from_tools")


def test_builder_importable_without_chat_loop():
    """Agent building is in builder.py; import builder without loading chat_loop."""
    # Ensure chat_loop is not already loaded (e.g. from a previous test)
    mods_before = set(sys.modules)
    from finops_buddy.agent import builder

    assert hasattr(builder, "build_agent")
    assert callable(builder.build_agent)
    # builder must not depend on chat_loop for normal import
    chat_loaded = "finops_buddy.agent.chat_loop" in sys.modules
    chat_was_loaded_before = "finops_buddy.agent.chat_loop" in mods_before
    assert not chat_loaded or chat_was_loaded_before


def test_format_module_has_cli_formatters():
    """CLI formatting lives in format.py."""
    from finops_buddy.agent import format as format_mod

    assert hasattr(format_mod, "_format_tooling_output")
    assert hasattr(format_mod, "_format_context_output")
    assert hasattr(format_mod, "_format_credentials_output")
    assert callable(format_mod._format_tooling_output)
    assert callable(format_mod._format_context_output)
    assert callable(format_mod._format_credentials_output)


def test_chat_loop_has_run_chat_loop_and_uses_builder():
    """Chat loop lives in chat_loop.py and uses builder/format."""
    from finops_buddy.agent import chat_loop

    assert hasattr(chat_loop, "run_chat_loop")
    assert callable(chat_loop.run_chat_loop)
    assert hasattr(chat_loop, "_build_chat_system_prompt")
    # chat_loop imports build_agent from builder (used by run_chat_loop)
    assert "build_agent" in dir(chat_loop)
