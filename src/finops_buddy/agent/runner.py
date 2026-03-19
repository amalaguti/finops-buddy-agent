"""Strands agent builder and interactive chat loop — facade re-exporting public API."""

from __future__ import annotations

from finops_buddy.agent.builder import (
    _create_finops_callback_handler,
    build_agent,
)
from finops_buddy.agent.chat_loop import (
    _agent_used_knowledge_mcp,
    _build_chat_system_prompt,
    run_chat_loop,
)
from finops_buddy.agent.format import (
    _format_context_output,
    _format_credentials_output,
    _format_tooling_output,  # noqa: F401 (re-export for tests)
)
from finops_buddy.agent.mcp import (
    _format_mcp_status,
    _mcp_server_name_for_tool,
    _mcp_server_names_from_tools,
    create_billing_mcp_client,
    create_core_mcp_client,
    create_cost_explorer_mcp_client,
    create_documentation_mcp_client,
    create_knowledge_mcp_client,
    create_pricing_mcp_client,
)

__all__ = [
    "_agent_used_knowledge_mcp",
    "_build_chat_system_prompt",
    "_create_finops_callback_handler",
    "_format_context_output",
    "_format_credentials_output",
    "_format_mcp_status",
    "_format_tooling_output",
    "_mcp_server_name_for_tool",
    "_mcp_server_names_from_tools",
    "build_agent",
    "create_billing_mcp_client",
    "create_core_mcp_client",
    "create_cost_explorer_mcp_client",
    "create_documentation_mcp_client",
    "create_knowledge_mcp_client",
    "create_pricing_mcp_client",
    "run_chat_loop",
]
