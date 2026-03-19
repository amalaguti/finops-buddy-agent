"""CLI formatters for /tooling, /context, /credentials, /status."""

from __future__ import annotations

import os

import boto3

from finops_buddy.agent.builder import _tool_origin, _tool_source_type
from finops_buddy.agent.mcp import _is_tool_allowed_by_guardrail


def _format_tooling_output(
    agent,
    tools_override: list | None = None,
    *,
    pdf_mcp_enabled: bool = False,
    excel_mcp_enabled: bool = False,
) -> str:
    """Format available tools for /tooling: type, origin, description.
    Includes MCP servers by name and their tools when present.
    Blocked tools show (blocked) suffix; appends YAML example for agent.read_only_allowed_tools.
    Pass tools_override (e.g. the list passed to the agent) so Type/Source work.
    When pdf_mcp_enabled or excel_mcp_enabled, appends a section for /print-only MCPs."""
    lines = ["Available tools:", ""]
    all_tools: list[tuple[str, bool, str | None]] = []  # (name, allowed, mcp_server_name)
    try:
        raw_tools = (
            tools_override
            if tools_override and isinstance(tools_override, list)
            else getattr(agent, "tools", [])
        )
        tools = raw_tools if isinstance(raw_tools, list) and len(raw_tools) > 0 else []
        configs = None
        if getattr(agent, "tool_registry", None) is not None:
            try:
                configs = agent.tool_registry.get_all_tools_config()
            except Exception:
                configs = None

        def desc_for_name(name: str) -> str:
            if not configs:
                return ""
            if isinstance(configs, list):
                for c in configs:
                    if isinstance(c, dict) and c.get("name") == name:
                        return (c.get("description") or "").strip()
                return ""
            cfg = configs.get(name, configs.get("tools", []))
            return (cfg.get("description", "").strip()) if isinstance(cfg, dict) else ""

        if tools:
            for t in tools:
                mcp_server_name = getattr(t, "_finops_mcp_server_name", None)
                if mcp_server_name and isinstance(mcp_server_name, str):
                    lines.append(f"  MCP server: {mcp_server_name}")
                    try:
                        mcp_tools = t.list_tools_sync()
                        if mcp_tools:
                            for mt in mcp_tools:
                                if isinstance(mt, dict):
                                    mname = mt.get("name", "")
                                    mdesc = (mt.get("description") or "").strip()
                                else:
                                    mname = (
                                        getattr(mt, "tool_name", None)
                                        or getattr(mt, "name", None)
                                        or ""
                                    )
                                    mdesc = ""
                                    spec = getattr(mt, "tool_spec", None)
                                    if spec is not None:
                                        if isinstance(spec, dict):
                                            mdesc = (spec.get("description") or "").strip()
                                        else:
                                            mdesc = (
                                                getattr(spec, "description", None) or ""
                                            ).strip()
                                if not mname:
                                    continue
                                allowed = _is_tool_allowed_by_guardrail(mname)
                                all_tools.append((mname, allowed, mcp_server_name))
                                display_name = mname if allowed else f"{mname} (blocked)"
                                lines.append(f"    • {display_name}")
                                if mdesc:
                                    for d in str(mdesc).split("\n")[:2]:
                                        if d.strip():
                                            lines.append(f"      {d.strip()}")
                        else:
                            lines.append("    (tools loaded on first use)")
                    except Exception:
                        lines.append("    (tools available at runtime)")
                    lines.append("")
                    continue
                name = getattr(t, "__name__", str(t))
                if not name or name.startswith("<"):
                    name = str(t)
                tool_type = _tool_source_type(t)
                origin = _tool_origin(t)
                desc = desc_for_name(name)
                if not desc:
                    doc = (getattr(t, "__doc__") or "").strip()
                    desc = doc.split("\n")[0] if doc else ""

                allowed = _is_tool_allowed_by_guardrail(name)
                all_tools.append((name, allowed, None))  # built-in
                display_name = name if allowed else f"{name} (blocked)"
                lines.append(f"  • {display_name}")
                lines.append(f"    Type: {tool_type}")
                if origin:
                    lines.append(f"    Source: {origin}")
                if desc:
                    for d in desc.split("\n")[:4]:
                        lines.append(f"    {d.strip()}")
                lines.append("")
        else:
            names = getattr(agent, "tool_names", None) or []
            for name in names:
                desc = desc_for_name(name)
                allowed = _is_tool_allowed_by_guardrail(name)
                all_tools.append((name, allowed, None))
                display_name = name if allowed else f"{name} (blocked)"
                lines.append(f"  • {display_name}")
                lines.append("    Type: (unknown)")
                if desc:
                    for d in desc.split("\n")[:3]:
                        lines.append(f"    {d.strip()}")
                lines.append("")

        if all_tools:
            lines.append("")
            lines.append("Example for config/settings.yaml (agent.read_only_allowed_tools):")
            lines.append("agent:")
            lines.append("  read_only_allowed_tools:")
            _sentinel = object()
            prev_mcp: str | None | object = _sentinel
            for tname, tallowed, mcp_name in all_tools:
                if mcp_name != prev_mcp:
                    prev_mcp = mcp_name
                    group_label = mcp_name if mcp_name else "Built-in"
                    lines.append(f"    # {group_label}")
                yaml_name = tname if tallowed else f"{tname} (blocked)"
                lines.append(f"    - {yaml_name}")
        if pdf_mcp_enabled or excel_mcp_enabled:
            lines.append("")
            lines.append("  Used by /print only (not agent tools):")
            if pdf_mcp_enabled:
                lines.append("    • PDF MCP (md-to-pdf-mcp)")
            if excel_mcp_enabled:
                lines.append("    • Excel MCP (excel-mcp-server)")
    except Exception:
        lines.append("  (Unable to list tools)")
    return "\n".join(lines).strip() or "No tools loaded."


def _format_credentials_output(
    session: boto3.Session,
    profile_name: str | None,
) -> str:
    """Format credentials in use (profile, account, ARN, region) for /credentials command.
    Same info as finops verify; these are the credentials passed to MCP servers (e.g. Billing)."""
    from finops_buddy.identity import get_current_identity

    profile = profile_name or "(default)"
    region = getattr(session, "region_name", None) or os.environ.get("AWS_DEFAULT_REGION") or "N/A"
    lines = [
        "Credentials in use (same as finops verify; passed to MCP servers when enabled):",
        "",
        f"  Profile: {profile}",
        f"  Region:  {region}",
    ]
    try:
        identity = get_current_identity(session)
        lines.append(f"  Account: {identity.account_id}")
        lines.append(f"  ARN:     {identity.arn}")
    except Exception as e:
        lines.append(f"  Account: (error: {e})")
        lines.append("  ARN:     N/A")
    return "\n".join(lines)


def _format_context_output(
    conversation: list[str],
    profile_name: str | None,
    session: boto3.Session,
    model_id: str | None,
    provider: str,
    token_usage: dict | None = None,
) -> str:
    """Format conversation context status for /context command.
    token_usage may contain input_tokens, output_tokens, total_tokens (from Strands metrics)."""
    turns = len(conversation)
    profile = profile_name or "(default)"
    account = "N/A"
    try:
        sts = session.client("sts")
        identity = sts.get_caller_identity()
        account = identity.get("Account", "N/A")
    except Exception:
        pass
    model = model_id or "default"
    if token_usage and (
        (token_usage.get("input_tokens") or 0) > 0 or (token_usage.get("output_tokens") or 0) > 0
    ):
        inp = token_usage.get("input_tokens") or 0
        out = token_usage.get("output_tokens") or 0
        total = inp + out
        tokens = f"Input: {inp}, Output: {out}, Total: {total}"
    else:
        tokens = "N/A (not tracked this session)"
    lines = [
        "Conversation context:",
        f"  Turns: {turns}",
        f"  Profile: {profile}",
        f"  Account: {account}",
        f"  Model: {model}",
        f"  Provider: {provider}",
        f"  Token usage: {tokens}",
    ]
    return "\n".join(lines)
