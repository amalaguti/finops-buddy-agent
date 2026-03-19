"""Tests for the Strands chat agent (tools, builder, runner)."""

import io
import sys
from decimal import Decimal
from unittest.mock import MagicMock, patch

from finops_buddy.agent.runner import (
    _agent_used_knowledge_mcp,
    _build_chat_system_prompt,
    _create_finops_callback_handler,
    _format_context_output,
    _format_mcp_status,
    _format_tooling_output,
    _mcp_server_name_for_tool,
    _mcp_server_names_from_tools,
    build_agent,
    create_billing_mcp_client,
    create_core_mcp_client,
    create_cost_explorer_mcp_client,
    create_documentation_mcp_client,
    create_knowledge_mcp_client,
    create_pricing_mcp_client,
)
from finops_buddy.agent.tools import create_cost_tools


def test_create_cost_tools_returns_list_of_tools():
    """create_cost_tools(session) returns a list of callable tools."""
    session = MagicMock()
    tools = create_cost_tools(session)
    assert isinstance(tools, list)
    assert len(tools) >= 6  # get_current_date + 5 cost tools
    for t in tools:
        assert callable(t)


def test_create_cost_tools_date_only_when_include_cost_tools_false():
    """When include_cost_tools=False, only get_current_date is returned (for Billing MCP mode)."""
    session = MagicMock()
    tools = create_cost_tools(session, include_cost_tools=False)
    assert len(tools) == 1
    assert callable(tools[0])
    assert "current_date" in getattr(tools[0], "__name__", "")


def test_get_current_date_tool_returns_date_and_constraints():
    """get_current_date tool returns today and 3-month / 14-day limits."""
    session = MagicMock()
    tools = create_cost_tools(session)
    get_date_tool = next(
        (t for t in tools if "current_date" in getattr(t, "__name__", "")),
        None,
    )
    assert get_date_tool is not None
    result = get_date_tool()
    assert "Today:" in result
    assert "90" in result
    assert "14" in result


def test_agent_can_report_current_period_costs():
    """When user asks for current-period costs, the current_period_costs tool returns cost data."""
    session = MagicMock()
    tools = create_cost_tools(session)
    with patch("finops_buddy.agent.tools.get_costs_by_service_aws_only") as get_costs:
        get_costs.return_value = [("Amazon EC2", Decimal("10.50")), ("Amazon S3", Decimal("2.00"))]
        current_tool = next(
            t for t in tools if getattr(t, "__name__", "").startswith("current_period")
        )
        result = current_tool()
        assert "Current month" in result or "Costs by service" in result
        assert "10.50" in result
        assert "12.50" in result or "Total" in result


def test_agent_uses_tools_for_cost_queries():
    """Agent has tools that can be invoked for cost-related queries (e.g. month-over-month)."""
    session = MagicMock()
    tools = create_cost_tools(session)
    tool_names = [getattr(t, "__name__", str(t)) for t in tools]
    assert "month_over_month_costs" in tool_names or any("month" in n for n in tool_names)
    assert "current_period_costs" in tool_names or any("current" in n for n in tool_names)


def test_agent_can_report_month_over_month_comparison():
    """Month-over-month tool returns comparison data when invoked."""
    session = MagicMock()
    tools = create_cost_tools(session)
    with patch("finops_buddy.agent.tools.get_costs_by_service") as get_costs:
        get_costs.return_value = [("EC2", Decimal("100"))]
        mom_tool = next(
            (t for t in tools if "month_over_month" in getattr(t, "__name__", "")),
            None,
        )
        assert mom_tool is not None
        result = mom_tool()
        assert "Month-over-month" in result or "Change" in result


def test_agent_can_report_week_over_week_comparison():
    """Week-over-week tool returns comparison data when invoked."""
    session = MagicMock()
    tools = create_cost_tools(session)
    with patch("finops_buddy.agent.tools.get_costs_for_date_range") as get_costs:
        get_costs.return_value = [("EC2", Decimal("50"))]
        wow_tool = next(
            (t for t in tools if "week_over_week" in getattr(t, "__name__", "")),
            None,
        )
        assert wow_tool is not None
        result = wow_tool()
        assert "Week-over-week" in result or "7 days" in result or "Change" in result


def test_agent_can_report_biweekly_over_biweekly_comparison():
    """Biweekly-over-biweekly tool returns comparison data when invoked."""
    session = MagicMock()
    tools = create_cost_tools(session)
    with patch("finops_buddy.agent.tools.get_costs_for_date_range") as get_costs:
        get_costs.return_value = [("EC2", Decimal("100"))]
        biw_tool = next(
            (t for t in tools if "biweekly" in getattr(t, "__name__", "")),
            None,
        )
        assert biw_tool is not None
        result = biw_tool()
        assert "Biweekly" in result or "14 days" in result or "Change" in result


def test_format_tooling_output_shows_available_tools():
    """When user enters /tooling, CLI displays a summary of available tools (names/descriptions)."""
    agent = MagicMock()
    agent.tool_names = ["get_current_date", "current_period_costs"]
    agent.tool_registry = None
    out = _format_tooling_output(agent)
    assert "Available tools" in out
    assert "get_current_date" in out
    assert "current_period_costs" in out


def test_format_tooling_output_fallback_from_tools_list():
    """When tool_names is missing, formatter falls back to agent.tools and uses __name__/__doc__."""

    def _fake_tool():
        """Get the current date."""
        pass

    agent = MagicMock()
    agent.tool_names = None
    agent.tool_registry = None
    agent.tools = [_fake_tool]
    out = _format_tooling_output(agent)
    assert "Available tools" in out
    assert "_fake_tool" in out or "fake_tool" in out


def test_format_tooling_output_shows_type_and_source_for_builtin_tools():
    """finops_buddy tools show Type: Built-in and Source: module.function in /tooling."""
    session = MagicMock()
    tools = create_cost_tools(session)
    agent = MagicMock()
    agent.tools = tools
    agent.tool_registry = None
    out = _format_tooling_output(agent)
    assert "Type: Built-in" in out
    assert "Source: finops_buddy.agent.tools." in out
    assert "get_current_date" in out


def test_format_context_output_shows_conversation_context_status():
    """/context shows conversation context (turns, profile, account, model)."""
    session = MagicMock()
    session.client.return_value.get_caller_identity.return_value = {"Account": "123456789012"}
    out = _format_context_output(
        conversation=["User: hi", "Agent: hello"],
        profile_name="my-profile",
        session=session,
        model_id="gpt-4o",
        provider="OpenAI",
    )
    assert "Conversation context" in out
    assert "Turns: 2" in out
    assert "my-profile" in out
    assert "123456789012" in out
    assert "gpt-4o" in out
    assert "OpenAI" in out


def test_create_knowledge_mcp_client_returns_none_when_disabled():
    """When Knowledge MCP is disabled, create_knowledge_mcp_client returns None."""
    with patch("finops_buddy.agent.mcp.get_knowledge_mcp_enabled", return_value=False):
        assert create_knowledge_mcp_client() is None


def test_create_billing_mcp_client_returns_none_when_disabled():
    """When Billing MCP is disabled, create_billing_mcp_client returns None."""
    with patch("finops_buddy.agent.mcp.get_billing_mcp_enabled", return_value=False):
        assert create_billing_mcp_client() is None


def test_create_documentation_mcp_client_returns_none_when_disabled():
    """When Documentation MCP is disabled, create_documentation_mcp_client returns None."""
    with patch("finops_buddy.agent.mcp.get_documentation_mcp_enabled", return_value=False):
        assert create_documentation_mcp_client() is None


def test_create_cost_explorer_mcp_client_returns_none_when_disabled():
    """When Cost Explorer MCP is disabled, create_cost_explorer_mcp_client returns None."""
    with patch("finops_buddy.agent.mcp.get_cost_explorer_mcp_enabled", return_value=False):
        assert create_cost_explorer_mcp_client() is None


def test_create_pricing_mcp_client_returns_none_when_disabled():
    """When Pricing MCP is disabled, create_pricing_mcp_client returns None."""
    with patch("finops_buddy.agent.mcp.get_pricing_mcp_enabled", return_value=False):
        assert create_pricing_mcp_client() is None


def test_create_core_mcp_client_returns_none_when_disabled():
    """When Core MCP is disabled, create_core_mcp_client returns None."""
    with patch("finops_buddy.agent.mcp.get_core_mcp_enabled", return_value=False):
        assert create_core_mcp_client() is None


def test_build_agent_uses_only_in_process_tools_when_mcp_disabled():
    """When Knowledge and Billing MCP are disabled, build_agent gets only cost tools."""
    session = MagicMock()
    captured_kwargs = {}

    def capture_agent(*args, **kwargs):
        captured_kwargs.clear()
        captured_kwargs.update(kwargs)
        return MagicMock()

    with (
        patch("finops_buddy.agent.mcp.get_knowledge_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.mcp.get_billing_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.mcp.get_documentation_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.mcp.get_cost_explorer_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.mcp.get_pricing_mcp_enabled", return_value=False),
        patch("strands.Agent", side_effect=capture_agent),
    ):
        build_agent(session, tools=None)
    tools = captured_kwargs.get("tools") or []
    mcp_tools = [t for t in tools if getattr(t, "_finops_mcp_server_name", None)]
    assert len(mcp_tools) == 0


def test_build_agent_includes_documentation_mcp_client_when_enabled():
    """When Documentation MCP is enabled, build_agent includes documentation MCP client in tools."""
    session = MagicMock()
    documentation_client = MagicMock()
    documentation_client._finops_mcp_server_name = "AWS Documentation MCP Server"
    captured_kwargs = {}

    def capture_agent(*args, **kwargs):
        captured_kwargs.clear()
        captured_kwargs.update(kwargs)
        return MagicMock()

    with (
        patch("finops_buddy.agent.mcp.get_knowledge_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.mcp.get_billing_mcp_enabled", return_value=False),
        patch(
            "finops_buddy.agent.mcp.get_documentation_mcp_enabled",
            return_value=True,
        ),
        patch(
            "finops_buddy.agent.builder.create_documentation_mcp_client",
            return_value=documentation_client,
        ),
        patch("strands.Agent", side_effect=capture_agent),
    ):
        build_agent(session, tools=None)
    tools = captured_kwargs.get("tools") or []
    doc_tools = [
        t
        for t in tools
        if getattr(t, "_finops_mcp_server_name", None) == "AWS Documentation MCP Server"
    ]
    assert len(doc_tools) == 1


def test_build_agent_includes_billing_mcp_client_when_enabled():
    """When Billing MCP is enabled, build_agent includes billing MCP client in tools."""
    session = MagicMock()
    billing_client = MagicMock()
    billing_client._finops_mcp_server_name = "AWS Billing and Cost Management MCP Server"
    captured_kwargs = {}

    def capture_agent(*args, **kwargs):
        captured_kwargs.clear()
        captured_kwargs.update(kwargs)
        return MagicMock()

    with (
        patch("finops_buddy.agent.mcp.get_knowledge_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.mcp.get_documentation_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.mcp.get_billing_mcp_enabled", return_value=True),
        patch(
            "finops_buddy.agent.builder.create_billing_mcp_client",
            return_value=billing_client,
        ),
        patch("strands.Agent", side_effect=capture_agent),
    ):
        build_agent(session, tools=None)
    tools = captured_kwargs.get("tools") or []
    billing_tools = [
        t
        for t in tools
        if getattr(t, "_finops_mcp_server_name", None)
        == "AWS Billing and Cost Management MCP Server"
    ]
    assert len(billing_tools) == 1
    # When Billing MCP is enabled, in-process cost tools are omitted (only get_current_date)
    non_mcp = [t for t in tools if not getattr(t, "_finops_mcp_server_name", None)]
    assert len(non_mcp) == 2  # get_current_date + create_chart
    names = [getattr(t, "__name__", "") for t in non_mcp]
    assert any("current_date" in n for n in names)
    assert any("create_chart" in n for n in names)


def test_build_agent_includes_cost_explorer_mcp_client_when_enabled():
    """When Cost Explorer MCP is enabled, build_agent includes Cost Explorer MCP client in tools."""
    session = MagicMock()
    cost_explorer_client = MagicMock()
    cost_explorer_client._finops_mcp_server_name = "AWS Cost Explorer MCP Server"
    captured_kwargs = {}

    def capture_agent(*args, **kwargs):
        captured_kwargs.clear()
        captured_kwargs.update(kwargs)
        return MagicMock()

    with (
        patch("finops_buddy.agent.mcp.get_knowledge_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.mcp.get_billing_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.mcp.get_documentation_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.mcp.get_cost_explorer_mcp_enabled", return_value=True),
        patch(
            "finops_buddy.agent.builder.create_cost_explorer_mcp_client",
            return_value=cost_explorer_client,
        ),
        patch("strands.Agent", side_effect=capture_agent),
    ):
        build_agent(session, tools=None)
    tools = captured_kwargs.get("tools") or []
    cost_explorer_tools = [
        t
        for t in tools
        if getattr(t, "_finops_mcp_server_name", None) == "AWS Cost Explorer MCP Server"
    ]
    assert len(cost_explorer_tools) == 1


def test_build_agent_includes_pricing_mcp_client_when_enabled():
    """When Pricing MCP is enabled, build_agent includes Pricing MCP client in tools."""
    session = MagicMock()
    pricing_client = MagicMock()
    pricing_client._finops_mcp_server_name = "AWS Pricing MCP Server"
    captured_kwargs = {}

    def capture_agent(*args, **kwargs):
        captured_kwargs.clear()
        captured_kwargs.update(kwargs)
        return MagicMock()

    with (
        patch("finops_buddy.agent.mcp.get_knowledge_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.mcp.get_core_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.mcp.get_billing_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.mcp.get_documentation_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.mcp.get_cost_explorer_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.mcp.get_pricing_mcp_enabled", return_value=True),
        patch(
            "finops_buddy.agent.builder.create_pricing_mcp_client",
            return_value=pricing_client,
        ),
        patch("strands.Agent", side_effect=capture_agent),
    ):
        build_agent(session, tools=None)
    tools = captured_kwargs.get("tools") or []
    pricing_tools = [
        t for t in tools if getattr(t, "_finops_mcp_server_name", None) == "AWS Pricing MCP Server"
    ]
    assert len(pricing_tools) == 1


def test_build_agent_includes_core_mcp_client_when_enabled():
    """When Core MCP is enabled, build_agent includes Core MCP client with roles in display name."""
    session = MagicMock()
    core_client = MagicMock()
    core_client._finops_mcp_server_name = (
        "Core MCP Server (roles: finops, aws-foundation, solutions-architect)"
    )
    captured_kwargs = {}

    def capture_agent(*args, **kwargs):
        captured_kwargs.clear()
        captured_kwargs.update(kwargs)
        return MagicMock()

    with (
        patch("finops_buddy.agent.mcp.get_knowledge_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.mcp.get_core_mcp_enabled", return_value=True),
        patch(
            "finops_buddy.agent.builder.create_core_mcp_client",
            return_value=core_client,
        ),
        patch("strands.Agent", side_effect=capture_agent),
    ):
        build_agent(session, tools=None)
    tools = captured_kwargs.get("tools") or []
    core_tools = [
        t
        for t in tools
        if getattr(t, "_finops_mcp_server_name", None)
        and "Core MCP Server" in getattr(t, "_finops_mcp_server_name", "")
    ]
    assert len(core_tools) == 1
    assert "roles:" in core_tools[0]._finops_mcp_server_name


def test_build_agent_includes_billing_cost_explorer_pricing_when_disabled_even_with_core():
    """Core enabled but Billing/Cost Explorer/Pricing disabled: those MCPs are not attached."""
    session = MagicMock()
    core_client = MagicMock()
    core_client._finops_mcp_server_name = "Core MCP Server (roles: finops)"
    captured_kwargs = {}

    def capture_agent(*args, **kwargs):
        captured_kwargs.clear()
        captured_kwargs.update(kwargs)
        return MagicMock()

    with (
        patch("finops_buddy.agent.mcp.get_knowledge_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.mcp.get_core_mcp_enabled", return_value=True),
        patch(
            "finops_buddy.agent.builder.create_core_mcp_client",
            return_value=core_client,
        ),
        patch("finops_buddy.agent.builder.create_billing_mcp_client", return_value=None),
        patch("finops_buddy.agent.builder.create_cost_explorer_mcp_client", return_value=None),
        patch("finops_buddy.agent.builder.create_pricing_mcp_client", return_value=None),
        patch("strands.Agent", side_effect=capture_agent),
    ):
        build_agent(session, tools=None)
    tools = captured_kwargs.get("tools") or []
    names = [getattr(t, "_finops_mcp_server_name", "") for t in tools]
    assert "AWS Billing and Cost Management MCP Server" not in names
    assert "AWS Cost Explorer MCP Server" not in names
    assert "AWS Pricing MCP Server" not in names


def test_build_agent_omits_built_in_cost_tools_when_billing_mcp_present():
    """When Billing MCP is present, built-in cost tools omitted; only get_current_date kept."""
    session = MagicMock()
    billing_client = MagicMock()
    billing_client._finops_mcp_server_name = "AWS Billing and Cost Management MCP Server"
    captured_kwargs = {}

    def capture_agent(*args, **kwargs):
        captured_kwargs.clear()
        captured_kwargs.update(kwargs)
        return MagicMock()

    with (
        patch("finops_buddy.agent.mcp.get_knowledge_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.mcp.get_core_mcp_enabled", return_value=False),
        patch(
            "finops_buddy.agent.builder.create_billing_mcp_client",
            return_value=billing_client,
        ),
        patch("strands.Agent", side_effect=capture_agent),
    ):
        build_agent(session, tools=None)
    tools = captured_kwargs.get("tools") or []
    tool_names = [getattr(t, "__name__", str(t)) for t in tools]
    assert not any("current_period_costs" in n for n in tool_names)
    assert not any("month_over_month" in n for n in tool_names)
    assert any("current_date" in n for n in tool_names)


def test_openai_model_uses_max_completion_tokens():
    """OpenAI provider: OpenAIModel is constructed with max_completion_tokens (not max_tokens)."""
    session = MagicMock()
    openai_model_mock = MagicMock()

    with (
        patch("finops_buddy.agent.builder.get_openai_api_key", return_value="sk-test"),
        patch(
            "finops_buddy.agent.builder.get_agent_max_completion_tokens",
            return_value=4096,
        ),
        patch("finops_buddy.agent.mcp.get_knowledge_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.mcp.get_core_mcp_enabled", return_value=False),
        patch("finops_buddy.agent.builder.create_billing_mcp_client", return_value=None),
        patch("finops_buddy.agent.builder.create_cost_explorer_mcp_client", return_value=None),
        patch("finops_buddy.agent.builder.create_pricing_mcp_client", return_value=None),
        patch(
            "strands.models.openai.OpenAIModel",
            side_effect=lambda **kw: openai_model_mock,
        ) as openai_model_cls,
    ):
        build_agent(session, tools=None)

    openai_model_cls.assert_called_once()
    call_kwargs = openai_model_cls.call_args.kwargs
    params = call_kwargs.get("params", {})
    assert "max_completion_tokens" in params
    assert params["max_completion_tokens"] == 4096
    assert "max_tokens" not in params


def test_format_tooling_output_includes_core_mcp_server_with_roles():
    """When Core MCP client is in tools, /tooling lists Core MCP Server with roles."""
    core_client = MagicMock()
    core_client._finops_mcp_server_name = (
        "Core MCP Server (roles: finops, aws-foundation, solutions-architect)"
    )
    core_client.list_tools_sync.return_value = [
        {"name": "prompt_understanding", "description": "Planning support"},
    ]
    agent = MagicMock()
    agent.tools = [core_client]
    agent.tool_registry = None
    out = _format_tooling_output(agent, tools_override=[core_client])
    assert "Core MCP Server" in out
    assert "roles:" in out
    assert "prompt_understanding" in out


def test_format_mcp_status_returns_none_when_no_mcp_tools():
    """When tools have no MCP clients, _format_mcp_status returns (none)."""
    out = _format_mcp_status([])
    assert "MCP servers: (none)" in out
    # Plain object has no _finops_mcp_server_name, so not treated as MCP
    out = _format_mcp_status([object()])
    assert "MCP servers: (none)" in out


def test_format_mcp_status_shows_ready_when_list_tools_sync_succeeds():
    """When MCP client list_tools_sync returns, _format_mcp_status shows ready and tool count."""
    mcp_client = MagicMock()
    mcp_client._finops_mcp_server_name = "AWS Billing and Cost Management MCP Server"
    mcp_client.list_tools_sync.return_value = [
        {"name": "get_cost_and_usage"},
        {"name": "get_cost_forecast"},
    ]
    out = _format_mcp_status([mcp_client])
    assert "MCP server status" in out
    assert "AWS Billing and Cost Management MCP Server" in out
    assert "ready (2 tools)" in out


def test_format_mcp_status_shows_allowed_or_blocked_per_tool():
    """/status lists each MCP tool with 'allowed' or 'blocked (read-only guardrail)'."""
    mcp_client = MagicMock()
    mcp_client._finops_mcp_server_name = "Test MCP Server"
    mcp_client.list_tools_sync.return_value = [
        {"name": "cost-explorer"},
        {"name": "create_budget"},
    ]
    out = _format_mcp_status([mcp_client])
    assert "cost-explorer" in out and "allowed" in out
    assert "create_budget" in out and "blocked" in out


def test_format_tooling_output_includes_mcp_server_section_when_client_present():
    """When tools include an MCP client with _finops_mcp_server_name, /tooling lists that server."""
    mcp_client = MagicMock()
    mcp_client._finops_mcp_server_name = "AWS Knowledge MCP Server"
    mcp_client.list_tools_sync.return_value = [
        {"name": "search_documentation", "description": "Search AWS docs"},
    ]
    agent = MagicMock()
    agent.tools = [mcp_client]
    agent.tool_registry = None
    out = _format_tooling_output(agent, tools_override=[mcp_client])
    assert "MCP server: AWS Knowledge MCP Server" in out
    assert "search_documentation" in out


def test_format_tooling_output_shows_blocked_suffix_for_blocked_tools():
    """/tooling appends (blocked) to blocked tool names in the listing."""
    session = MagicMock()
    tools = create_cost_tools(session)
    agent = MagicMock()
    agent.tools = tools
    agent.tool_registry = None
    out = _format_tooling_output(agent)
    assert "get_current_date" in out
    # Blocked tool: use an MCP client that exposes a tool not on the allow-list
    mcp_client = MagicMock()
    mcp_client._finops_mcp_server_name = "Test MCP"
    mcp_client.list_tools_sync.return_value = [{"name": "delete_account"}]
    agent.tools = [mcp_client]
    out2 = _format_tooling_output(agent, tools_override=[mcp_client])
    assert "delete_account (blocked)" in out2


def test_format_tooling_output_displays_yaml_example_for_read_only_allowed_tools():
    """/tooling displays a YAML example block for agent.read_only_allowed_tools."""
    session = MagicMock()
    tools = create_cost_tools(session)
    agent = MagicMock()
    agent.tools = tools
    agent.tool_registry = None
    out = _format_tooling_output(agent)
    assert "Example for config/settings.yaml (agent.read_only_allowed_tools):" in out
    assert "read_only_allowed_tools:" in out
    assert "get_current_date" in out
    assert "# Built-in" in out
    # With an MCP client, YAML should include MCP server comment and (blocked) for blocked tools
    mcp_client = MagicMock()
    mcp_client._finops_mcp_server_name = "Test MCP"
    mcp_client.list_tools_sync.return_value = [{"name": "create_budget"}]
    out2 = _format_tooling_output(agent, tools_override=[mcp_client])
    assert "create_budget (blocked)" in out2
    assert "# Test MCP" in out2


def test_agent_used_knowledge_mcp_returns_true_when_result_has_knowledge_tool_call():
    """Result with search_documentation tool call makes _agent_used_knowledge_mcp return True."""
    msg = MagicMock()
    msg.tool_calls = [MagicMock(name="search_documentation")]
    msg.tool_calls[0].name = "search_documentation"
    result = MagicMock()
    result.messages = [msg]
    assert _agent_used_knowledge_mcp(result) is True


def test_agent_used_knowledge_mcp_returns_false_when_no_tool_calls():
    """When result has no tool calls, _agent_used_knowledge_mcp returns False."""
    result = MagicMock()
    result.messages = []
    assert _agent_used_knowledge_mcp(result) is False


def test_agent_used_knowledge_mcp_returns_false_when_result_none():
    """When result is None, _agent_used_knowledge_mcp returns False."""
    assert _agent_used_knowledge_mcp(None) is False


def test_mcp_server_names_from_tools_returns_names_from_mcp_clients():
    """_mcp_server_names_from_tools returns display names for tools with _finops_mcp_server_name."""
    no_mcp = object()  # no _finops_mcp_server_name
    mcp_client = MagicMock()
    mcp_client._finops_mcp_server_name = "AWS Knowledge MCP Server"
    assert _mcp_server_names_from_tools([no_mcp, mcp_client]) == ["AWS Knowledge MCP Server"]
    assert _mcp_server_names_from_tools([no_mcp]) == []
    assert _mcp_server_names_from_tools([]) == []


def test_mcp_server_name_for_tool_returns_knowledge_mcp_for_aws_prefixed():
    """_mcp_server_name_for_tool returns AWS Knowledge MCP Server for aws___* tools."""
    assert _mcp_server_name_for_tool("aws___search_documentation") == "AWS Knowledge MCP Server"
    assert _mcp_server_name_for_tool("aws___read_documentation") == "AWS Knowledge MCP Server"
    assert _mcp_server_name_for_tool("aws___list_regions") == "AWS Knowledge MCP Server"


def test_mcp_server_name_for_tool_returns_none_for_builtin_tools():
    """_mcp_server_name_for_tool returns None for non-MCP tool names."""
    assert _mcp_server_name_for_tool("current_period_costs") is None
    assert _mcp_server_name_for_tool("get_current_date") is None
    assert _mcp_server_name_for_tool("") is None


def test_mcp_server_name_for_tool_returns_documentation_mcp_for_doc_prefixed():
    """_mcp_server_name_for_tool returns AWS Documentation MCP Server for doc___* tools."""
    assert _mcp_server_name_for_tool("doc___read_documentation") == "AWS Documentation MCP Server"
    assert _mcp_server_name_for_tool("doc___search_documentation") == "AWS Documentation MCP Server"
    assert _mcp_server_name_for_tool("doc___recommend") == "AWS Documentation MCP Server"


def test_finops_callback_handler_prints_mcp_name_for_knowledge_tool():
    """FinOps callback prints tool line with (MCP: AWS Knowledge MCP Server) for aws___ tools."""
    handler = _create_finops_callback_handler()
    buf = io.StringIO()
    with patch.object(sys, "stdout", buf):
        handler(
            event={
                "contentBlockStart": {
                    "start": {"toolUse": {"name": "aws___search_documentation"}},
                },
            },
        )
    out = buf.getvalue()
    assert "Tool #1:" in out
    assert "aws___search_documentation" in out
    assert "(MCP: AWS Knowledge MCP Server)" in out


def test_system_prompt_prefers_cost_explorer_for_list_accounts():
    """Agent system prompt instructs using cost-explorer for listing linked/member accounts."""
    prompt = _build_chat_system_prompt()
    assert "cost-explorer" in prompt
    assert "linked" in prompt or "member accounts" in prompt
    assert "billingconductor" in prompt.lower() or "Billing Conductor" in prompt


def test_system_prompt_uses_cost_explorer_not_budgets_for_account_list():
    """Agent system prompt says to use cost-explorer for account list, not budgets."""
    prompt = _build_chat_system_prompt()
    assert "cost-explorer" in prompt and "account" in prompt.lower()
    assert "Do not use the budgets tool for a simple list of accounts" in prompt
    assert "budgets only when" in prompt or "use budgets only when" in prompt


def test_system_prompt_restricts_billing_conductor_to_explicit_use():
    """System prompt restricts Billing Conductor to explicit billing groups / custom line items."""
    prompt = _build_chat_system_prompt()
    assert "list-account-associations" in prompt or "list-billing-groups" in prompt
    assert "billing groups" in prompt or "custom line items" in prompt or "pro forma" in prompt
    assert "only when" in prompt or "explicitly" in prompt


def test_system_prompt_instructs_retry_with_finops_tools_on_permission_error():
    """System prompt instructs retry with cost-explorer/budgets/pricing on permission error."""
    prompt = _build_chat_system_prompt()
    assert "retry" in prompt.lower()
    assert "permission" in prompt.lower() or "access-denied" in prompt.lower()
    assert "cost-explorer" in prompt or "budgets" in prompt or "pricing" in prompt


def test_system_prompt_includes_read_only_restriction():
    """System prompt states agent must only perform read-only operations."""
    prompt = _build_chat_system_prompt()
    assert "read-only" in prompt.lower()
    assert "create" in prompt.lower() or "delete" in prompt.lower() or "update" in prompt.lower()
    assert "Console" in prompt or "CLI" in prompt
