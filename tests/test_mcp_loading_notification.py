from __future__ import annotations

import logging

from finops_buddy.api import chat as chat_mod


def test_build_agent_and_tools_emits_mcp_loading_progress_and_logs(caplog, monkeypatch):
    """build_agent_and_tools logs before/after MCP client creation and emits mcp_loading events."""

    def fake_session(profile_name=None):
        return object()

    def fake_client(_session=None):
        return object()

    monkeypatch.setattr(chat_mod, "get_session", fake_session)
    monkeypatch.setattr(chat_mod, "create_core_mcp_client", fake_client)
    monkeypatch.setattr(chat_mod, "create_billing_mcp_client", fake_client)
    monkeypatch.setattr(chat_mod, "create_cost_explorer_mcp_client", fake_client)
    monkeypatch.setattr(chat_mod, "create_pricing_mcp_client", fake_client)
    monkeypatch.setattr(chat_mod, "create_knowledge_mcp_client", fake_client)
    monkeypatch.setattr(chat_mod, "create_documentation_mcp_client", fake_client)
    monkeypatch.setattr(
        chat_mod,
        "create_cost_tools",
        lambda session, include_cost_tools=True: [],
    )
    monkeypatch.setattr(chat_mod, "create_chart_tools", lambda: [])
    monkeypatch.setattr(chat_mod, "create_export_tools", lambda: [])
    monkeypatch.setattr(
        chat_mod,
        "build_agent",
        lambda session,
        profile_name,
        tools,
        progress_callback=None,
        chart_artifact_collector=None,
        file_export_artifact_collector=None: object(),
    )

    events: list[tuple[str, str]] = []

    def progress_cb(event, message):
        events.append((event, message))

    with caplog.at_level(logging.INFO, logger=chat_mod.logger.name):
        chat_mod.build_agent_and_tools("p", progress_callback=progress_cb)

    mcp_events = [e for e in events if e[0] == "mcp_loading"]
    assert mcp_events, "expected at least one mcp_loading progress event"

    log_text = "\n".join(caplog.messages)
    assert "Loading MCP:" in log_text
    assert "MCP " in log_text and "ready" in log_text
