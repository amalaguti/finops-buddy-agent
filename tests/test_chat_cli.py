"""Tests for the chat CLI subcommand (spec scenarios)."""

from unittest.mock import MagicMock, patch


def test_chat_starts_with_default_profile():
    """When user runs finops chat with no profile, CLI starts agent with default credentials."""
    with patch("finops_buddy.cli.run_chat_loop") as run_chat:
        run_chat.return_value = 0
        from finops_buddy.cli import main

        with patch("sys.argv", ["finops", "chat"]):
            exit_code = main()
    assert exit_code == 0
    run_chat.assert_called_once()
    call_kw = run_chat.call_args[1]
    assert call_kw.get("profile_name") is None


def test_chat_starts_with_named_profile():
    """When user runs finops chat --profile my-account, CLI starts agent with that profile."""
    with patch("finops_buddy.cli.run_chat_loop") as run_chat:
        run_chat.return_value = 0
        from finops_buddy.cli import main

        with patch("sys.argv", ["finops", "chat", "--profile", "my-account"]):
            exit_code = main()
    assert exit_code == 0
    run_chat.assert_called_once()
    call_kw = run_chat.call_args[1]
    assert call_kw.get("profile_name") == "my-account"


def test_chat_session_accepts_input_and_returns_response():
    """When user enters a message at the chat prompt, CLI displays agent response (mocked loop)."""
    with patch("finops_buddy.cli.run_chat_loop") as run_chat:
        run_chat.return_value = 0
        from finops_buddy.cli import main

        with patch("sys.argv", ["finops", "chat"]):
            exit_code = main()
    assert exit_code == 0
    run_chat.assert_called_once()


def test_chat_profile_from_root_parser():
    """When user runs finops --profile my-account chat, profile is passed to the agent."""
    with patch("finops_buddy.cli.run_chat_loop") as run_chat:
        run_chat.return_value = 0
        from finops_buddy.cli import main

        with patch("sys.argv", ["finops", "--profile", "my-account", "chat"]):
            exit_code = main()
    assert exit_code == 0
    run_chat.assert_called_once()
    call_kw = run_chat.call_args[1]
    assert call_kw.get("profile_name") == "my-account"


def test_user_enters_tooling_sees_available_tools(capsys):
    """When user enters /tooling at the chat prompt, CLI shows available tools and prompts again."""
    from finops_buddy.agent.runner import run_chat_loop

    mock_session = MagicMock()
    mock_session.client.return_value.get_caller_identity.return_value = {"Account": "111111111111"}
    mock_agent = MagicMock()
    mock_agent.tool_names = ["get_current_date", "current_period_costs"]
    mock_agent.tool_registry = None

    with patch("finops_buddy.identity.get_session", return_value=mock_session):
        with patch("finops_buddy.agent.chat_loop.build_agent", return_value=mock_agent):
            with patch("builtins.input", side_effect=["/tooling", "/quit"]):
                run_chat_loop(profile_name=None)

    out = capsys.readouterr().out
    assert "Available tools" in out
    assert "get_current_date" in out or "current_period_costs" in out


def test_user_enters_tooling_sees_mcp_servers_and_tools(capsys):
    """When Knowledge MCP is enabled and user enters /tooling, CLI shows MCP server and tools."""
    from finops_buddy.agent.runner import run_chat_loop

    mock_session = MagicMock()
    mock_session.client.return_value.get_caller_identity.return_value = {"Account": "111111111111"}
    mock_mcp = MagicMock()
    mock_mcp._finops_mcp_server_name = "AWS Knowledge MCP Server"
    mock_mcp.list_tools_sync.return_value = [
        {"name": "search_documentation", "description": "Search AWS docs"},
    ]
    mock_agent = MagicMock()
    mock_agent.tool_names = []

    with patch("finops_buddy.identity.get_session", return_value=mock_session):
        with patch("finops_buddy.agent.chat_loop.build_agent", return_value=mock_agent):
            with patch(
                "finops_buddy.agent.chat_loop.create_knowledge_mcp_client",
                return_value=mock_mcp,
            ):
                with patch("builtins.input", side_effect=["/tooling", "/quit"]):
                    run_chat_loop(profile_name=None)

    out = capsys.readouterr().out
    assert "MCP server: AWS Knowledge MCP Server" in out
    assert "search_documentation" in out


def test_user_enters_status_sees_mcp_readiness(capsys):
    """When user enters /status and an MCP client is present, CLI shows MCP server status."""
    from finops_buddy.agent.runner import run_chat_loop

    mock_session = MagicMock()
    mock_session.client.return_value.get_caller_identity.return_value = {"Account": "111111111111"}
    mock_mcp = MagicMock()
    mock_mcp._finops_mcp_server_name = "AWS Knowledge MCP Server"
    mock_mcp.list_tools_sync.return_value = [{"name": "search_documentation"}]
    mock_agent = MagicMock()
    mock_agent.tool_names = []

    with patch("finops_buddy.identity.get_session", return_value=mock_session):
        with patch("finops_buddy.agent.chat_loop.build_agent", return_value=mock_agent):
            with patch(
                "finops_buddy.agent.chat_loop.create_knowledge_mcp_client",
                return_value=mock_mcp,
            ):
                with patch("builtins.input", side_effect=["/status", "/quit"]):
                    run_chat_loop(profile_name=None)

    out = capsys.readouterr().out
    assert "MCP server status" in out
    assert "ready" in out
    assert "AWS Knowledge MCP Server" in out


def test_tooling_shows_documentation_mcp_when_enabled(capsys):
    """When Documentation MCP is enabled and user enters /tooling, CLI shows server and tools."""
    from finops_buddy.agent.runner import run_chat_loop

    mock_session = MagicMock()
    mock_session.client.return_value.get_caller_identity.return_value = {"Account": "111111111111"}
    doc_mcp = MagicMock()
    doc_mcp._finops_mcp_server_name = "AWS Documentation MCP Server"
    doc_mcp.list_tools_sync.return_value = [
        {"name": "read_documentation", "description": "Read AWS docs"},
        {"name": "search_documentation", "description": "Search AWS docs"},
    ]
    mock_agent = MagicMock()
    mock_agent.tool_names = []

    with patch("finops_buddy.identity.get_session", return_value=mock_session):
        with patch("finops_buddy.agent.chat_loop.build_agent", return_value=mock_agent):
            with patch(
                "finops_buddy.agent.mcp.get_documentation_mcp_enabled",
                return_value=True,
            ):
                with patch(
                    "finops_buddy.agent.chat_loop.create_documentation_mcp_client",
                    return_value=doc_mcp,
                ):
                    with patch(
                        "finops_buddy.agent.mcp.get_knowledge_mcp_enabled",
                        return_value=False,
                    ):
                        with patch(
                            "finops_buddy.agent.mcp.get_billing_mcp_enabled",
                            return_value=False,
                        ):
                            with patch("builtins.input", side_effect=["/tooling", "/quit"]):
                                run_chat_loop(profile_name=None)

    out = capsys.readouterr().out
    assert "AWS Documentation MCP Server" in out
    assert "read_documentation" in out or "search_documentation" in out


def test_status_shows_documentation_mcp_when_enabled(capsys):
    """When Documentation MCP is enabled and user enters /status, CLI includes it in status."""
    from finops_buddy.agent.runner import run_chat_loop

    mock_session = MagicMock()
    mock_session.client.return_value.get_caller_identity.return_value = {"Account": "111111111111"}
    doc_mcp = MagicMock()
    doc_mcp._finops_mcp_server_name = "AWS Documentation MCP Server"
    doc_mcp.list_tools_sync.return_value = [{"name": "read_documentation"}]
    mock_agent = MagicMock()
    mock_agent.tool_names = []

    with patch("finops_buddy.identity.get_session", return_value=mock_session):
        with patch("finops_buddy.agent.chat_loop.build_agent", return_value=mock_agent):
            with patch(
                "finops_buddy.agent.mcp.get_documentation_mcp_enabled",
                return_value=True,
            ):
                with patch(
                    "finops_buddy.agent.chat_loop.create_documentation_mcp_client",
                    return_value=doc_mcp,
                ):
                    with patch(
                        "finops_buddy.agent.mcp.get_knowledge_mcp_enabled",
                        return_value=False,
                    ):
                        with patch(
                            "finops_buddy.agent.mcp.get_billing_mcp_enabled",
                            return_value=False,
                        ):
                            with patch("builtins.input", side_effect=["/status", "/quit"]):
                                run_chat_loop(profile_name=None)

    out = capsys.readouterr().out
    assert "MCP server status" in out
    assert "AWS Documentation MCP Server" in out


def test_tooling_shows_cost_explorer_mcp_when_enabled(capsys):
    """When Cost Explorer MCP is enabled and user enters /tooling, CLI shows server and tools."""
    from finops_buddy.agent.runner import run_chat_loop

    mock_session = MagicMock()
    mock_session.client.return_value.get_caller_identity.return_value = {"Account": "111111111111"}
    ce_mcp = MagicMock()
    ce_mcp._finops_mcp_server_name = "AWS Cost Explorer MCP Server"
    ce_mcp.list_tools_sync.return_value = [
        {"name": "get_cost_and_usage", "description": "Get cost and usage"},
        {"name": "get_cost_forecast", "description": "Get cost forecast"},
    ]
    mock_agent = MagicMock()
    mock_agent.tool_names = []

    with patch("finops_buddy.identity.get_session", return_value=mock_session):
        with patch("finops_buddy.agent.chat_loop.build_agent", return_value=mock_agent):
            with patch(
                "finops_buddy.agent.mcp.get_cost_explorer_mcp_enabled",
                return_value=True,
            ):
                with patch(
                    "finops_buddy.agent.chat_loop.create_cost_explorer_mcp_client",
                    return_value=ce_mcp,
                ):
                    with patch(
                        "finops_buddy.agent.mcp.get_knowledge_mcp_enabled",
                        return_value=False,
                    ):
                        with patch(
                            "finops_buddy.agent.mcp.get_billing_mcp_enabled",
                            return_value=False,
                        ):
                            with patch(
                                "finops_buddy.agent.mcp.get_documentation_mcp_enabled",
                                return_value=False,
                            ):
                                with patch("builtins.input", side_effect=["/tooling", "/quit"]):
                                    run_chat_loop(profile_name=None)

    out = capsys.readouterr().out
    assert "AWS Cost Explorer MCP Server" in out
    assert "get_cost_and_usage" in out or "get_cost_forecast" in out


def test_status_shows_cost_explorer_mcp_when_enabled(capsys):
    """When Cost Explorer MCP is enabled and user enters /status, CLI includes it in status."""
    from finops_buddy.agent.runner import run_chat_loop

    mock_session = MagicMock()
    mock_session.client.return_value.get_caller_identity.return_value = {"Account": "111111111111"}
    ce_mcp = MagicMock()
    ce_mcp._finops_mcp_server_name = "AWS Cost Explorer MCP Server"
    ce_mcp.list_tools_sync.return_value = [{"name": "get_cost_and_usage"}]
    mock_agent = MagicMock()
    mock_agent.tool_names = []

    with patch("finops_buddy.identity.get_session", return_value=mock_session):
        with patch("finops_buddy.agent.chat_loop.build_agent", return_value=mock_agent):
            with patch(
                "finops_buddy.agent.mcp.get_cost_explorer_mcp_enabled",
                return_value=True,
            ):
                with patch(
                    "finops_buddy.agent.chat_loop.create_cost_explorer_mcp_client",
                    return_value=ce_mcp,
                ):
                    with patch(
                        "finops_buddy.agent.mcp.get_knowledge_mcp_enabled",
                        return_value=False,
                    ):
                        with patch(
                            "finops_buddy.agent.mcp.get_billing_mcp_enabled",
                            return_value=False,
                        ):
                            with patch(
                                "finops_buddy.agent.mcp.get_documentation_mcp_enabled",
                                return_value=False,
                            ):
                                with patch("builtins.input", side_effect=["/status", "/quit"]):
                                    run_chat_loop(profile_name=None)

    out = capsys.readouterr().out
    assert "MCP server status" in out
    assert "AWS Cost Explorer MCP Server" in out


def test_tooling_shows_pricing_mcp_when_enabled(capsys):
    """When Pricing MCP is enabled and user enters /tooling, CLI shows server and tools."""
    from finops_buddy.agent.runner import run_chat_loop

    mock_session = MagicMock()
    mock_session.client.return_value.get_caller_identity.return_value = {"Account": "111111111111"}
    pricing_mcp = MagicMock()
    pricing_mcp._finops_mcp_server_name = "AWS Pricing MCP Server"
    pricing_mcp.list_tools_sync.return_value = [
        {"name": "get_products", "description": "Get pricing products"},
        {"name": "get_attribute_values", "description": "Get attribute values"},
    ]
    mock_agent = MagicMock()
    mock_agent.tool_names = []

    with patch("finops_buddy.identity.get_session", return_value=mock_session):
        with patch("finops_buddy.agent.chat_loop.build_agent", return_value=mock_agent):
            with patch(
                "finops_buddy.agent.mcp.get_pricing_mcp_enabled",
                return_value=True,
            ):
                with patch(
                    "finops_buddy.agent.chat_loop.create_pricing_mcp_client",
                    return_value=pricing_mcp,
                ):
                    with patch(
                        "finops_buddy.agent.mcp.get_knowledge_mcp_enabled",
                        return_value=False,
                    ):
                        with patch(
                            "finops_buddy.agent.mcp.get_billing_mcp_enabled",
                            return_value=False,
                        ):
                            with patch(
                                "finops_buddy.agent.mcp.get_documentation_mcp_enabled",
                                return_value=False,
                            ):
                                with patch(
                                    "finops_buddy.agent.mcp.get_cost_explorer_mcp_enabled",
                                    return_value=False,
                                ):
                                    with patch(
                                        "builtins.input",
                                        side_effect=["/tooling", "/quit"],
                                    ):
                                        run_chat_loop(profile_name=None)

    out = capsys.readouterr().out
    assert "AWS Pricing MCP Server" in out
    assert "get_products" in out or "get_attribute_values" in out


def test_status_shows_pricing_mcp_when_enabled(capsys):
    """When Pricing MCP is enabled and user enters /status, CLI includes it in status."""
    from finops_buddy.agent.runner import run_chat_loop

    mock_session = MagicMock()
    mock_session.client.return_value.get_caller_identity.return_value = {"Account": "111111111111"}
    pricing_mcp = MagicMock()
    pricing_mcp._finops_mcp_server_name = "AWS Pricing MCP Server"
    pricing_mcp.list_tools_sync.return_value = [{"name": "get_products"}]
    mock_agent = MagicMock()
    mock_agent.tool_names = []

    with patch("finops_buddy.identity.get_session", return_value=mock_session):
        with patch("finops_buddy.agent.chat_loop.build_agent", return_value=mock_agent):
            with patch(
                "finops_buddy.agent.mcp.get_pricing_mcp_enabled",
                return_value=True,
            ):
                with patch(
                    "finops_buddy.agent.chat_loop.create_pricing_mcp_client",
                    return_value=pricing_mcp,
                ):
                    with patch(
                        "finops_buddy.agent.mcp.get_knowledge_mcp_enabled",
                        return_value=False,
                    ):
                        with patch(
                            "finops_buddy.agent.mcp.get_billing_mcp_enabled",
                            return_value=False,
                        ):
                            with patch(
                                "finops_buddy.agent.mcp.get_documentation_mcp_enabled",
                                return_value=False,
                            ):
                                with patch(
                                    "finops_buddy.agent.mcp.get_cost_explorer_mcp_enabled",
                                    return_value=False,
                                ):
                                    with patch(
                                        "builtins.input",
                                        side_effect=["/status", "/quit"],
                                    ):
                                        run_chat_loop(profile_name=None)

    out = capsys.readouterr().out
    assert "MCP server status" in out
    assert "AWS Pricing MCP Server" in out


def test_user_enters_credentials_sees_profile_and_account(capsys):
    """When user enters /credentials, CLI shows profile, account, ARN (like finops verify)."""
    from finops_buddy.agent.runner import run_chat_loop

    mock_identity = MagicMock()
    mock_identity.account_id = "123456789012"
    mock_identity.arn = "arn:aws:iam::123456789012:user/test"
    mock_session = MagicMock()
    mock_session.profile_name = "my-profile"
    mock_session.region_name = "us-east-1"
    mock_agent = MagicMock()
    mock_agent.tool_names = []

    with patch("finops_buddy.identity.get_session", return_value=mock_session):
        with patch("finops_buddy.agent.chat_loop.build_agent", return_value=mock_agent):
            with patch(
                "finops_buddy.identity.get_current_identity",
                return_value=mock_identity,
            ):
                with patch("builtins.input", side_effect=["/credentials", "/quit"]):
                    run_chat_loop(profile_name="my-profile")

    out = capsys.readouterr().out
    assert "Credentials in use" in out
    assert "Profile: my-profile" in out
    assert "123456789012" in out
    assert "MCP" in out


def test_user_enters_context_sees_conversation_context_status(capsys):
    """When user enters /context at the chat prompt, CLI shows context status and prompts again."""
    from finops_buddy.agent.runner import run_chat_loop

    mock_session = MagicMock()
    mock_session.client.return_value.get_caller_identity.return_value = {"Account": "222222222222"}
    mock_agent = MagicMock()
    mock_agent.tool_names = []

    with patch("finops_buddy.identity.get_session", return_value=mock_session):
        with patch("finops_buddy.agent.chat_loop.build_agent", return_value=mock_agent):
            with patch("finops_buddy.agent.chat_loop.get_agent_model_id", return_value=None):
                with patch("finops_buddy.agent.chat_loop.get_openai_api_key", return_value=None):
                    with patch("builtins.input", side_effect=["/context", "/quit"]):
                        run_chat_loop(profile_name="test-profile")

    out = capsys.readouterr().out
    assert "Conversation context" in out
    assert "Turns:" in out
    assert "test-profile" in out
    assert "222222222222" in out


def test_meta_commands_not_sent_to_agent():
    """Meta commands (/tooling, /context, /status, /credentials, /print) not sent to agent."""
    from finops_buddy.agent.runner import run_chat_loop

    mock_session = MagicMock()
    mock_session.client.return_value.get_caller_identity.return_value = {"Account": "333333333333"}
    mock_agent = MagicMock()
    mock_agent.tool_names = []

    with patch("finops_buddy.identity.get_session", return_value=mock_session):
        with patch("finops_buddy.agent.chat_loop.build_agent", return_value=mock_agent):
            with patch("finops_buddy.agent.chat_loop.run_print_flow"):
                with patch(
                    "builtins.input",
                    side_effect=[
                        "/tooling",
                        "/context",
                        "/status",
                        "/credentials",
                        "/print",
                        "/quit",
                    ],
                ):
                    run_chat_loop(profile_name=None)

    # Agent must never be invoked for meta commands
    mock_agent.assert_not_called()


def test_input_guardrail_blocks_mutating_request_and_shows_friendly_message(capsys):
    """When input guardrail is enabled and user message is mutating, agent is not called."""
    from finops_buddy.agent.runner import run_chat_loop

    mock_session = MagicMock()
    mock_session.client.return_value.get_caller_identity.return_value = {"Account": "555555555555"}
    mock_agent = MagicMock()
    mock_agent.tool_names = []

    with patch("finops_buddy.identity.get_session", return_value=mock_session):
        with patch("finops_buddy.agent.chat_loop.build_agent", return_value=mock_agent):
            with patch(
                "finops_buddy.agent.chat_loop.get_read_only_guardrail_input_enabled",
                return_value=True,
            ):
                with patch(
                    "finops_buddy.agent.chat_loop.is_mutating_intent",
                    return_value=True,
                ):
                    with patch(
                        "builtins.input",
                        side_effect=["create a budget for my account", "/quit"],
                    ):
                        run_chat_loop(profile_name=None)

    mock_agent.assert_not_called()
    out = capsys.readouterr().out
    assert "read-only" in out.lower() or "cost and usage" in out.lower()
    assert "Console" in out or "CLI" in out


def test_input_guardrail_allows_read_only_request_to_reach_agent():
    """When input guardrail is enabled and message is not mutating, agent is called."""
    from finops_buddy.agent.runner import run_chat_loop

    mock_session = MagicMock()
    mock_session.client.return_value.get_caller_identity.return_value = {"Account": "666666666666"}
    mock_agent = MagicMock()
    mock_agent.tool_names = []
    mock_agent.return_value = "Here are your costs for last month."

    with patch("finops_buddy.identity.get_session", return_value=mock_session):
        with patch("finops_buddy.agent.chat_loop.build_agent", return_value=mock_agent):
            with patch(
                "finops_buddy.agent.chat_loop.get_read_only_guardrail_input_enabled",
                return_value=True,
            ):
                with patch(
                    "finops_buddy.agent.chat_loop.is_mutating_intent",
                    return_value=False,
                ):
                    with patch(
                        "builtins.input",
                        side_effect=["What did we spend last month?", "/quit"],
                    ):
                        run_chat_loop(profile_name=None)

    mock_agent.assert_called()


def test_chat_welcome_mentions_tooling_context_and_status(capsys):
    """When user starts a chat session, /tooling, /context and /status are in the welcome."""
    from finops_buddy.agent.runner import run_chat_loop

    mock_session = MagicMock()
    mock_session.client.return_value.get_caller_identity.return_value = {"Account": "444444444444"}
    mock_agent = MagicMock()
    mock_agent.tool_names = []

    with patch("finops_buddy.identity.get_session", return_value=mock_session):
        with patch("finops_buddy.agent.chat_loop.build_agent", return_value=mock_agent):
            with patch("builtins.input", side_effect=["/quit"]):
                run_chat_loop(profile_name=None)

    out = capsys.readouterr().out
    assert "/tooling" in out
    assert "/context" in out
    assert "/status" in out
    assert "/credentials" in out
    assert "/print" in out
    assert "Commands:" in out or "commands" in out.lower()
    assert "MCP servers:" in out


def test_progress_shown_during_chat_startup():
    """When user runs finops chat (without --quiet), progress messages are emitted for each step."""
    from finops_buddy.agent.runner import run_chat_loop

    messages: list[str] = []

    def capture(msg: str) -> None:
        messages.append(msg)

    mock_session = MagicMock()
    mock_session.client.return_value.get_caller_identity.return_value = {"Account": "111111111111"}
    mock_agent = MagicMock()
    mock_agent.tool_names = []

    with patch("finops_buddy.identity.get_session", return_value=mock_session):
        with patch("finops_buddy.agent.chat_loop.build_agent", return_value=mock_agent):
            with patch("builtins.input", side_effect=["/quit"]):
                run_chat_loop(profile_name=None, progress=capture)

    assert "Resolving credentials..." in messages
    assert "Creating cost tools..." in messages
    assert any("Building agent" in m and "please wait" in m for m in messages), messages
    assert "Ready." in messages


def test_progress_includes_mcp_server_names():
    """When MCP servers are enabled, progress shows each MCP server name as it loads."""
    from finops_buddy.agent.runner import run_chat_loop

    messages: list[str] = []

    def capture(msg: str) -> None:
        messages.append(msg)

    mock_session = MagicMock()
    mock_session.client.return_value.get_caller_identity.return_value = {"Account": "111111111111"}
    mock_mcp = MagicMock()
    mock_mcp._finops_mcp_server_name = "AWS Knowledge MCP Server"
    mock_mcp.list_tools_sync.return_value = [{"name": "search_documentation"}]
    mock_agent = MagicMock()
    mock_agent.tool_names = []

    with patch("finops_buddy.identity.get_session", return_value=mock_session):
        with patch("finops_buddy.agent.chat_loop.build_agent", return_value=mock_agent):
            with patch(
                "finops_buddy.agent.chat_loop.create_knowledge_mcp_client",
                return_value=mock_mcp,
            ):
                with patch("builtins.input", side_effect=["/quit"]):
                    run_chat_loop(profile_name=None, progress=capture)

    assert any("Knowledge" in m for m in messages)
    assert any("Billing" in m for m in messages)
    assert any("Documentation" in m for m in messages)


def test_chat_quiet_passes_noop_progress():
    """With finops chat --quiet, run_chat_loop is called with a no-op progress callback."""
    with patch("finops_buddy.cli.run_chat_loop") as run_chat:
        run_chat.return_value = 0
        from finops_buddy.cli import main

        with patch("sys.argv", ["finops", "chat", "--quiet"]):
            exit_code = main()
    assert exit_code == 0
    run_chat.assert_called_once()
    call_kw = run_chat.call_args[1]
    progress = call_kw.get("progress")
    assert progress is not None
    # No-op callback does nothing when called
    progress("test")


def test_quiet_mode_suppresses_startup_progress(capsys):
    """When user runs finops chat with progress=noop, no startup progress is emitted to stderr."""
    from finops_buddy.agent.runner import run_chat_loop

    mock_session = MagicMock()
    mock_session.client.return_value.get_caller_identity.return_value = {"Account": "111111111111"}
    mock_agent = MagicMock()
    mock_agent.tool_names = []

    with patch("finops_buddy.identity.get_session", return_value=mock_session):
        with patch("finops_buddy.agent.chat_loop.build_agent", return_value=mock_agent):
            with patch("builtins.input", side_effect=["/quit"]):
                run_chat_loop(profile_name=None, progress=lambda m: None)

    err = capsys.readouterr().err
    assert "Resolving credentials" not in err
    assert "Ready." not in err
