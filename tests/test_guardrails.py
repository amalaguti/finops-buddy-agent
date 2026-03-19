"""Tests for read-only guardrails (input classifier and tool hook)."""

from unittest.mock import MagicMock

from finops_buddy.agent.guardrails import (
    MESSAGE_INPUT_BLOCKED,
    MESSAGE_TOOL_BLOCKED,
    ReadOnlyToolGuardrail,
    get_default_allowed_tools,
    is_mutating_intent,
)


def test_is_mutating_intent_returns_true_for_create():
    """When user says create X, is_mutating_intent returns True."""
    assert is_mutating_intent("create a budget for my account") is True
    assert is_mutating_intent("Create an S3 bucket") is True


def test_is_mutating_intent_returns_true_for_delete_update_remove():
    """When user says delete/update/remove, is_mutating_intent returns True."""
    assert is_mutating_intent("delete this resource") is True
    assert is_mutating_intent("update the cost allocation tags") is True
    assert is_mutating_intent("remove the budget") is True


def test_is_mutating_intent_returns_false_for_read_only():
    """When user asks read-only (costs, reports), is_mutating_intent returns False."""
    assert is_mutating_intent("What did we spend last month?") is False
    assert is_mutating_intent("Compare this week to last week") is False
    assert is_mutating_intent("show me costs by service") is False


def test_is_mutating_intent_returns_false_for_how_to_informational():
    """When user asks how to / what happens if, treat as informational (not mutating)."""
    assert is_mutating_intent("how do I create a budget?") is False
    assert is_mutating_intent("what happens if I delete this?") is False
    assert is_mutating_intent("can you explain how to update tags?") is False


def test_tool_guardrail_allows_tool_on_allow_list():
    """When tool name is on allow-list, cancel_tool is not set."""
    allowed = get_default_allowed_tools()
    guardrail = ReadOnlyToolGuardrail(allowed_tools=allowed)
    event = type("Event", (), {"tool_use": {"name": "get_current_date", "input": {}}})()
    guardrail._intercept_tool(event)
    assert not hasattr(event, "cancel_tool") or getattr(event, "cancel_tool", None) is None


def test_tool_guardrail_allows_cost_explorer_and_bcm_read_only():
    """BCM read-only tools (cost-explorer, budgets, etc.) are on default allow-list."""
    allowed = get_default_allowed_tools()
    guardrail = ReadOnlyToolGuardrail(allowed_tools=allowed)
    for tool_name in ("cost-explorer", "budgets", "pricing", "list-account-associations"):
        event = type("Event", (), {"tool_use": {"name": tool_name, "input": {}}})()
        guardrail._intercept_tool(event)
        assert not hasattr(event, "cancel_tool") or getattr(event, "cancel_tool", None) is None, (
            f"Expected {tool_name!r} to be allowed"
        )


def test_tool_guardrail_allows_all_bcm_mcp_tools():
    """All BCM MCP tools (compute-optimizer, cost-anomaly, list-pricing-rules, etc.) are allowed."""
    allowed = get_default_allowed_tools()
    guardrail = ReadOnlyToolGuardrail(allowed_tools=allowed)
    for tool_name in (
        "compute-optimizer",
        "cost-anomaly",
        "list-billing-group-cost-reports",
        "list-pricing-rules",
        "session-sql",
    ):
        event = type("Event", (), {"tool_use": {"name": tool_name, "input": {}}})()
        guardrail._intercept_tool(event)
        assert not hasattr(event, "cancel_tool") or getattr(event, "cancel_tool", None) is None, (
            f"Expected {tool_name!r} to be allowed"
        )


def test_tool_guardrail_allows_aws_pricing_mcp_tools():
    """AWS Pricing MCP Server tools (get_pricing, etc.) are on default allow-list."""
    allowed = get_default_allowed_tools()
    guardrail = ReadOnlyToolGuardrail(allowed_tools=allowed)
    for tool_name in (
        "get_pricing",
        "get_pricing_service_codes",
        "generate_cost_report",
        "analyze_terraform_project",
    ):
        event = type("Event", (), {"tool_use": {"name": tool_name, "input": {}}})()
        guardrail._intercept_tool(event)
        assert not hasattr(event, "cancel_tool") or getattr(event, "cancel_tool", None) is None, (
            f"Expected {tool_name!r} to be allowed"
        )


def test_tool_guardrail_blocks_tool_not_on_allow_list():
    """When tool name is not on allow-list, cancel_tool is set to friendly message."""
    allowed = frozenset({"get_current_date"})
    guardrail = ReadOnlyToolGuardrail(allowed_tools=allowed)
    event = type("Event", (), {"tool_use": {"name": "create_budget", "input": {}}})()
    guardrail._intercept_tool(event)
    assert getattr(event, "cancel_tool", None) == MESSAGE_TOOL_BLOCKED


def test_tool_guardrail_blocked_message_is_friendly():
    """Tool-blocked message mentions read-only and suggests alternatives."""
    assert "read-only" in MESSAGE_TOOL_BLOCKED.lower()
    assert "reports" in MESSAGE_TOOL_BLOCKED or "comparisons" in MESSAGE_TOOL_BLOCKED
    assert "Console" in MESSAGE_TOOL_BLOCKED or "scripts" in MESSAGE_TOOL_BLOCKED


def test_input_blocked_message_is_friendly():
    """Input-blocked message mentions read-only and suggests alternatives."""
    assert "read-only" in MESSAGE_INPUT_BLOCKED.lower() or "cost and usage" in MESSAGE_INPUT_BLOCKED
    assert "Console" in MESSAGE_INPUT_BLOCKED or "CLI" in MESSAGE_INPUT_BLOCKED


def test_guardrail_register_hooks_adds_before_tool_call():
    """ReadOnlyToolGuardrail registers a callback for BeforeToolCallEvent."""
    from strands.hooks import BeforeToolCallEvent

    registry = MagicMock()
    guardrail = ReadOnlyToolGuardrail()
    guardrail.register_hooks(registry)
    registry.add_callback.assert_called_once()
    args = registry.add_callback.call_args[0]
    assert args[0] is BeforeToolCallEvent
    assert callable(args[1])


def test_tool_guardrail_uses_configured_allow_list_when_set(tmp_path, monkeypatch):
    """When settings set agent.read_only_allowed_tools, guardrail allows only those tools."""
    from finops_buddy.settings import get_read_only_allowed_tools, reset_settings_cache

    reset_settings_cache()
    cfg = tmp_path / "settings.yaml"
    cfg.write_text(
        "agent:\n  read_only_allowed_tools:\n    - get_current_date\n    - current_period_costs\n"
    )
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(cfg))
    allowed = get_read_only_allowed_tools()
    guardrail = ReadOnlyToolGuardrail(allowed_tools=allowed)
    event_allowed = type("Event", (), {"tool_use": {"name": "get_current_date", "input": {}}})()
    guardrail._intercept_tool(event_allowed)
    assert not getattr(event_allowed, "cancel_tool", None)
    event_blocked = type(
        "Event",
        (),
        {"tool_use": {"name": "session-sql", "input": {}}},  # not in list
    )()
    guardrail._intercept_tool(event_blocked)
    assert getattr(event_blocked, "cancel_tool", None) == MESSAGE_TOOL_BLOCKED
    reset_settings_cache()
