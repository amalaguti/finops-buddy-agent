"""Interactive chat loop: prompt, agent call, slash commands, retries."""

from __future__ import annotations

import sys
import time
from collections.abc import Callable

from finops_buddy.agent.builder import build_agent
from finops_buddy.agent.chart_tools import create_chart_tools
from finops_buddy.agent.conversation_printer import run_print_flow
from finops_buddy.agent.format import (
    _format_context_output,
    _format_credentials_output,
    _format_tooling_output,
)
from finops_buddy.agent.guardrails import (
    MESSAGE_INPUT_BLOCKED,
    is_mutating_intent,
)
from finops_buddy.agent.mcp import (
    _KNOWLEDGE_MCP_TOOL_NAMES,
    _format_mcp_status,
    _mcp_server_names_from_tools,
    create_billing_mcp_client,
    create_core_mcp_client,
    create_cost_explorer_mcp_client,
    create_documentation_mcp_client,
    create_knowledge_mcp_client,
    create_pricing_mcp_client,
)
from finops_buddy.agent.tools import create_cost_tools, create_export_tools
from finops_buddy.settings import (
    get_agent_max_completion_tokens,
    get_agent_model_id,
    get_agent_temperature,
    get_excel_mcp_enabled,
    get_openai_api_key,
    get_pdf_mcp_enabled,
    get_read_only_guardrail_input_enabled,
)


def _agent_used_knowledge_mcp(result) -> bool:
    """Return True if the agent result indicates any tool from AWS Knowledge MCP was used this turn.
    Best-effort: inspects result for tool calls; returns False if shape is unknown."""
    if result is None:
        return False
    try:
        messages = getattr(result, "messages", None)
        if messages and isinstance(messages, list):
            for m in reversed(messages):
                tc = getattr(m, "tool_calls", None) or (
                    m.get("tool_calls") if isinstance(m, dict) else None
                )
                if tc:
                    for c in tc if isinstance(tc, list) else [tc]:
                        name = None
                        if isinstance(c, dict):
                            name = c.get("name") or (c.get("function", {}) or {}).get("name")
                        else:
                            fn = getattr(c, "function", None)
                            name = getattr(c, "name", None) or (
                                getattr(fn, "name", None) if fn else None
                            )
                        if name and name in _KNOWLEDGE_MCP_TOOL_NAMES:
                            return True
        return False
    except Exception:
        return False


def _is_rate_limit_error(e: BaseException) -> bool:
    """True if the exception looks like an OpenAI/API rate limit (429)."""
    name = type(e).__name__
    if name == "RateLimitError":
        return True
    msg = str(e).lower()
    return "rate limit" in msg or "429" in msg


def _cleanup_agent_tools(agent) -> None:
    """Call tool_registry.cleanup() so MCP clients shut down before interpreter exit.
    Avoids 'cannot join thread at interpreter shutdown' when Agent.__del__ would run at shutdown."""
    registry = getattr(agent, "tool_registry", None)
    if registry is None:
        return
    try:
        registry.cleanup()
    except Exception:
        pass  # avoid raising; shutdown should still exit 0


def _build_chat_system_prompt() -> str:
    """Build the system prompt for the chat agent. Used by run_chat_loop; exposed for tests."""
    return (
        "You are a helpful AWS FinOps assistant. Use get_current_date when you need "
        "today's date or to explain date limits. Cost/usage data: only last 3 months "
        "(90 days); do not query older. Resource-level data (e.g. by resource ID): "
        "only last 14 days in AWS. Use the cost tools for current month, date ranges, "
        "month-over-month, week-over-week, biweekly. Be concise. "
        "You must only perform read-only operations; do not create, update, or delete "
        "any AWS resources. If the user asks for that, explain in a friendly way that "
        "you are restricted to read-only and suggest alternatives (e.g. cost reports, "
        "AWS Console or CLI for changes). "
        "For listing linked or member accounts (with account IDs and names), use the "
        "cost-explorer tool; it returns account IDs and account names from the payer. "
        "Do not use the budgets tool for a simple list of accounts—use budgets only when "
        "the user asks about budgets (e.g. budget configurations, alerts, or amounts). "
        "For cost and usage queries, prefer cost-explorer and pricing; many roles have "
        "ce:* and budgets:* but not billingconductor:*. Use Billing Conductor tools "
        "(list-account-associations, list-billing-groups, etc.) only when the user "
        "explicitly asks for billing groups, custom line items, or pro forma costs. "
        "If a tool returns a permission or access-denied error (e.g. mentioning "
        "billingconductor), retry with cost-explorer or pricing where they can answer. "
        "When the Core MCP Server is available, if it does not produce a complete, "
        "satisfactory, or accurate result for the user's request, use the other MCP "
        "servers (e.g. AWS Billing and Cost Management, Cost Explorer, Pricing) to "
        "provide a complete response. "
        "When the user asks to save, export, or print the conversation (or part of it) "
        "to PDF or Excel, format the content in a useful way. For PDF: use clear "
        "sections and headings. For Excel: produce an analyzable table—one row per "
        "data point with columns that allow filtering and sorting (e.g. for cost data: "
        "Service, Region, Cost, Period; for Q&A: Question, Answer). Do not dump "
        "key-value pairs as Topic/Summary; use proper column headers and one row per "
        "item. Then call export_to_pdf or export_to_excel with that content and a "
        "filename (e.g. YYYYMMDD_HHMMSS-summary.pdf or .xlsx). No need for the user "
        "to run /print—you can do it when they ask. "
        "Format your replies in markdown: use - or * for bullet lists, ** for emphasis, "
        "## for section headers when summarizing, and markdown tables (| col | col |) when "
        "listing cost data, recommendations, or multiple items so the UI can render them. "
        "When showing account IDs (e.g. in recommendations, summaries, or quick steps), always "
        "show the account name or alias together with the ID so the user can identify accounts. "
        "Use cost-explorer or other tools to get the mapping of account ID to name; keep this "
        "mapping in mind for the conversation and use it in every response that mentions accounts. "
        "Display as 'Account Name (123456789012)' or '123456789012 (Account Name)'. "
        "Charts: When the user asks for a chart, graph, or visual (e.g. 'bar chart of top 5 services', "
        "'line chart of costs over time'), you MUST call the create_chart tool with the data—do not "
        "only describe the chart in text or show a table. Fetch the data with cost-explorer or other "
        "tools, then call create_chart so a real chart image is embedded. Use chart_type: line for "
        "time series, bar for top N or categories, pie for proportions. Data: list of dicts "
        '[{"label": "X", "value": n}, ...] for bar/pie, or [{"date": "...", "cost": n}, ...] '
        'or columnar {"labels": [...], "values": [...]}. Keys are flexible (label/name/service, '
        "value/cost/amount, date/dates)."
    )


def run_chat_loop(
    profile_name: str | None,
    *,
    progress: Callable[[str], None] | None = None,
) -> int:
    """
    Run the interactive chat loop: prompt for input, send to agent, print response, repeat.
    Exit on /quit or EOF. Returns exit code (0 on normal exit).

    progress: Optional callback for startup progress messages (e.g. to stderr).
    Defaults to printing to stderr with flush.
    """
    from finops_buddy.identity import get_session

    def _default_progress(msg: str) -> None:
        print(msg, file=sys.stderr, flush=True)

    if progress is None:
        progress = _default_progress

    try:
        progress("Resolving credentials...")
        session = get_session(profile_name=profile_name)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    progress("Loading Core MCP...")
    core_client = create_core_mcp_client(session)
    progress("Loading Billing MCP...")
    billing_client = create_billing_mcp_client(session)
    progress("Loading Cost Explorer MCP...")
    cost_explorer_client = create_cost_explorer_mcp_client(session)
    progress("Loading AWS Pricing MCP...")
    pricing_client = create_pricing_mcp_client(session)
    include_cost_tools = billing_client is None
    progress("Creating cost tools...")
    tools = list(create_cost_tools(session, include_cost_tools=include_cost_tools))
    tools.extend(create_chart_tools())
    tools.extend(create_export_tools())
    progress("Loading AWS Knowledge MCP...")
    knowledge_client = create_knowledge_mcp_client()
    if knowledge_client is not None:
        tools.append(knowledge_client)
    if billing_client is not None:
        tools.append(billing_client)
    progress("Loading AWS Documentation MCP...")
    documentation_client = create_documentation_mcp_client(session)
    if documentation_client is not None:
        tools.append(documentation_client)
    if cost_explorer_client is not None:
        tools.append(cost_explorer_client)
    if pricing_client is not None:
        tools.append(pricing_client)
    if core_client is not None:
        tools.append(core_client)
    pdf_print = get_pdf_mcp_enabled()
    excel_print = get_excel_mcp_enabled()
    if pdf_print or excel_print:
        parts = (["PDF MCP"] if pdf_print else []) + (["Excel MCP"] if excel_print else [])
        progress(f"Print export: {', '.join(parts)} enabled for /print.")
    progress("Building agent (loading MCP servers may take a few minutes—please wait)...")
    agent = build_agent(session, profile_name, tools=tools)
    progress("Ready.")
    system_prompt = _build_chat_system_prompt()
    conversation: list[str] = []
    token_usage: dict = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    model_id = get_agent_model_id()
    provider = "OpenAI" if get_openai_api_key() else "Bedrock"
    mcp_servers = _mcp_server_names_from_tools(tools)
    welcome_lines = [
        "FinOps chat. Commands: /quit, /tooling, /context, /status, /credentials, /print.",
        "Ctrl+Z to exit.",
    ]
    if mcp_servers:
        welcome_lines.append("MCP servers: " + ", ".join(mcp_servers))
        welcome_lines.append("Run /status to check MCP server readiness (e.g. after uvx install).")
    else:
        welcome_lines.append("MCP servers: (none)")
    if pdf_print or excel_print:
        parts = (["PDF MCP"] if pdf_print else []) + (["Excel MCP"] if excel_print else [])
        welcome_lines.append(f"Print export: {', '.join(parts)} available for /print.")
    print("\n".join(welcome_lines) + "\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except EOFError:
            print("\nGoodbye.")
            _cleanup_agent_tools(agent)
            return 0
        if not user_input:
            continue
        normalized = user_input.lower().strip()
        if normalized in ("/quit", "/exit", "quit", "exit"):
            print("Goodbye.")
            _cleanup_agent_tools(agent)
            return 0
        if normalized == "/tooling":
            tooling_out = _format_tooling_output(
                agent,
                tools_override=tools,
                pdf_mcp_enabled=pdf_print,
                excel_mcp_enabled=excel_print,
            )
            print(f"\n{tooling_out}\n")
            continue
        if normalized == "/status":
            temp = get_agent_temperature()
            max_tok = get_agent_max_completion_tokens()
            model_str = model_id or "default"
            agent_line = f"Agent: model {model_str}, temperature {temp}, max_tokens {max_tok}"
            mcp_block = _format_mcp_status(tools)
            print(f"\n{agent_line}\n\n{mcp_block}\n")
            continue
        if normalized == "/context":
            ctx_out = _format_context_output(
                conversation,
                profile_name,
                session,
                model_id,
                provider,
                token_usage=token_usage,
            )
            print(f"\n{ctx_out}\n")
            continue
        if normalized == "/credentials":
            print(f"\n{_format_credentials_output(session, profile_name)}\n")
            continue
        if normalized == "/print":
            run_print_flow(conversation, agent, profile_name=profile_name)
            print()
            continue
        if get_read_only_guardrail_input_enabled() and is_mutating_intent(user_input):
            print(f"\nAgent: {MESSAGE_INPUT_BLOCKED}\n")
            conversation.append(f"User: {user_input}")
            conversation.append(f"Agent: {MESSAGE_INPUT_BLOCKED}")
            continue
        conversation.append(f"User: {user_input}")
        full_prompt = system_prompt + "\n\n" + "\n\n".join(conversation)
        max_attempts = 3
        last_exception = None
        for attempt in range(max_attempts):
            try:
                result = agent(full_prompt)
                text = str(result).strip()
                conversation.append(f"Agent: {text}")
                # Accumulate token usage from Strands result.metrics when available
                try:
                    metrics = getattr(result, "metrics", None)
                    if metrics is not None:
                        usage = getattr(metrics, "accumulated_usage", None)
                        if isinstance(usage, dict):
                            token_usage["input_tokens"] = token_usage.get(
                                "input_tokens", 0
                            ) + usage.get("inputTokens", usage.get("input_tokens", 0))
                            token_usage["output_tokens"] = token_usage.get(
                                "output_tokens", 0
                            ) + usage.get("outputTokens", usage.get("output_tokens", 0))
                except Exception:
                    pass
                print(f"\nAgent: {text}\n")
                if _agent_used_knowledge_mcp(result):
                    print("Consulted AWS Knowledge for this response.\n")
                last_exception = None
                break
            except Exception as e:
                last_exception = e
                if _is_rate_limit_error(e) and attempt < max_attempts - 1:
                    wait_sec = 2 ** (attempt + 1)
                    print(
                        f"Rate limit hit; retrying in {wait_sec}s "
                        f"({attempt + 2}/{max_attempts})...",
                        file=sys.stderr,
                    )
                    time.sleep(wait_sec)
                else:
                    if _is_rate_limit_error(e):
                        print(
                            "Error: OpenAI rate limit. Wait a minute and try again, "
                            "or check your API tier.",
                            file=sys.stderr,
                        )
                    else:
                        print(f"Error: {e}", file=sys.stderr)
                    break
        if last_exception is not None and conversation[-1].startswith("User:"):
            conversation.pop()
    return 0
