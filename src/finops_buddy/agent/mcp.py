"""MCP client factories and status/name helpers for the FinOps agent."""

from __future__ import annotations

import concurrent.futures
import os

import boto3

from finops_buddy.settings import (
    get_billing_mcp_command,
    get_billing_mcp_enabled,
    get_core_mcp_command,
    get_core_mcp_enabled,
    get_core_mcp_roles,
    get_cost_explorer_mcp_command,
    get_cost_explorer_mcp_enabled,
    get_documentation_mcp_command,
    get_documentation_mcp_enabled,
    get_knowledge_mcp_enabled,
    get_knowledge_mcp_url,
    get_pricing_mcp_command,
    get_pricing_mcp_enabled,
    get_read_only_allowed_tools,
)

# Timeout (seconds) when probing MCP server readiness (e.g. uvx install on first run)
_MCP_STATUS_PROBE_TIMEOUT = 15

# MCP clients can be slow on first run (uvx install, multiple servers). Used for all MCPs.
_MCP_STARTUP_TIMEOUT = 180

# AWS Knowledge MCP tool names (for "Consulted AWS Knowledge" notification; used by chat_loop)
_KNOWLEDGE_MCP_TOOL_NAMES = frozenset(
    {
        "search_documentation",
        "read_documentation",
        "recommend",
        "list_regions",
        "get_regional_availability",
    }
)

# MCP server display name for tool-name lookup (tool invocations in callback)
_KNOWLEDGE_MCP_SERVER_NAME = "AWS Knowledge MCP Server"
_DOCUMENTATION_MCP_SERVER_NAME = "AWS Documentation MCP Server"
_COST_EXPLORER_MCP_SERVER_NAME = "AWS Cost Explorer MCP Server"
_PRICING_MCP_SERVER_NAME = "AWS Pricing MCP Server"


def _mcp_server_names_from_tools(tools: list) -> list[str]:
    """Return unique MCP server display names from tools that have _finops_mcp_server_name."""
    names: list[str] = []
    for t in tools or []:
        n = getattr(t, "_finops_mcp_server_name", None)
        if isinstance(n, str) and n.strip() and n not in names:
            names.append(n)
    return names


def _probe_mcp_client_readiness(
    client, timeout_sec: int = _MCP_STATUS_PROBE_TIMEOUT
) -> tuple[str, list]:
    """Probe one MCP client with list_tools_sync(); return (status string, tools list).
    Runs in a thread so we can timeout (e.g. while uvx is installing)."""
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(client.list_tools_sync)
            tools = future.result(timeout=timeout_sec)
        tools = tools if tools else []
        count = len(tools)
        return f"ready ({count} tools)", tools
    except concurrent.futures.TimeoutError:
        return (
            "not ready (timeout; uvx may still be installing - try again in a moment)",
            [],
        )
    except Exception as e:
        return f"not ready ({e!r})", []


def _is_tool_allowed_by_guardrail(tool_name: str) -> bool:
    """Return True if the tool is on the read-only allow-list (agent will run it)."""
    if not tool_name or not isinstance(tool_name, str):
        return False
    return tool_name.strip() in get_read_only_allowed_tools()


def _format_mcp_status(tools: list) -> str:
    """Format MCP server readiness for /status; shows allowed/blocked per tool."""
    mcp_tools = [t for t in (tools or []) if getattr(t, "_finops_mcp_server_name", None)]
    if not mcp_tools:
        return "MCP servers: (none)"
    lines = ["MCP server status:", ""]
    for t in mcp_tools:
        name = getattr(t, "_finops_mcp_server_name", "MCP server")
        status_str, mcp_tool_list = _probe_mcp_client_readiness(t)
        lines.append(f"  {name}: {status_str}")
        if mcp_tool_list:
            for mt in mcp_tool_list:
                mname = ""
                if isinstance(mt, dict):
                    mname = (mt.get("name") or "").strip()
                else:
                    mname = getattr(mt, "tool_name", None) or getattr(mt, "name", None) or ""
                if mname:
                    allowed = _is_tool_allowed_by_guardrail(mname)
                    status = "allowed" if allowed else "blocked (read-only guardrail)"
                    lines.append(f"    • {mname}: {status}")
        lines.append("")
    return "\n".join(lines).strip()


def _mcp_server_name_for_tool(tool_name: str) -> str | None:
    """Return MCP server display name if this tool is from a known MCP; else None.
    Used when printing 'Tool #N: name (MCP: ...)' in the callback."""
    if not tool_name:
        return None
    # AWS Knowledge MCP tools are exposed with aws___ prefix (e.g. aws___search_documentation)
    if tool_name.startswith("aws___"):
        return _KNOWLEDGE_MCP_SERVER_NAME
    # AWS Documentation MCP (stdio) may use doc___ prefix when namespaced
    if tool_name.startswith("doc___"):
        return _DOCUMENTATION_MCP_SERVER_NAME
    # Fallback: suffix after last ___ (e.g. search_documentation)
    if "___" in tool_name:
        suffix = tool_name.split("___")[-1]
        if suffix in _KNOWLEDGE_MCP_TOOL_NAMES:
            return _KNOWLEDGE_MCP_SERVER_NAME
    if tool_name in _KNOWLEDGE_MCP_TOOL_NAMES:
        return _KNOWLEDGE_MCP_SERVER_NAME
    return None


def create_knowledge_mcp_client():
    """Create AWS Knowledge MCP client when enabled; otherwise return None.
    Uses Streamable HTTP; URL and enable flag from settings/env."""
    if not get_knowledge_mcp_enabled():
        return None
    try:
        from mcp.client.streamable_http import streamablehttp_client
        from strands.tools.mcp import MCPClient

        url = get_knowledge_mcp_url()
        client = MCPClient(
            lambda: streamablehttp_client(url),
            startup_timeout=_MCP_STARTUP_TIMEOUT,
        )
        setattr(client, "_finops_mcp_server_name", "AWS Knowledge MCP Server")
        return client
    except Exception:
        return None


def create_billing_mcp_client(session: boto3.Session | None = None):
    """Create AWS Billing and Cost Management MCP client when enabled; otherwise return None.
    Uses stdio transport (uvx subprocess); enable and command from settings/env.
    When session is provided, passes AWS_PROFILE and AWS_REGION into the subprocess
    so the MCP server uses the same credentials as the chat."""
    if not get_billing_mcp_enabled():
        return None
    try:
        from mcp import StdioServerParameters, stdio_client
        from strands.tools.mcp import MCPClient

        command, args = get_billing_mcp_command()
        env = dict(os.environ)
        if session is not None:
            profile = getattr(session, "profile_name", None)
            if profile:
                env["AWS_PROFILE"] = profile
            region = getattr(session, "region_name", None)
            if region:
                env["AWS_REGION"] = region
        params = StdioServerParameters(command=command, args=args, env=env)
        client = MCPClient(
            lambda: stdio_client(params),
            startup_timeout=_MCP_STARTUP_TIMEOUT,
        )
        setattr(
            client,
            "_finops_mcp_server_name",
            "AWS Billing and Cost Management MCP Server",
        )
        return client
    except Exception:
        return None


def create_documentation_mcp_client(session: boto3.Session | None = None):
    """Create AWS Documentation MCP client when enabled; otherwise return None.
    Uses stdio transport (uvx subprocess); enable and command from settings/env.
    When session is provided, passes AWS_PROFILE and AWS_REGION into the subprocess."""
    if not get_documentation_mcp_enabled():
        return None
    try:
        from mcp import StdioServerParameters, stdio_client
        from strands.tools.mcp import MCPClient

        command, args = get_documentation_mcp_command()
        env = dict(os.environ)
        if session is not None:
            profile = getattr(session, "profile_name", None)
            if profile:
                env["AWS_PROFILE"] = profile
            region = getattr(session, "region_name", None)
            if region:
                env["AWS_REGION"] = region
        params = StdioServerParameters(command=command, args=args, env=env)
        client = MCPClient(
            lambda: stdio_client(params),
            startup_timeout=_MCP_STARTUP_TIMEOUT,
        )
        setattr(client, "_finops_mcp_server_name", "AWS Documentation MCP Server")
        return client
    except Exception:
        return None


def create_cost_explorer_mcp_client(session: boto3.Session | None = None):
    """Create AWS Cost Explorer MCP client when enabled; otherwise return None.
    Uses stdio transport (uvx subprocess); enable and command from settings/env.
    When session is provided, passes AWS_PROFILE and AWS_REGION into the subprocess.
    Disabled by default; BCM MCP covers Cost Explorer–style functionality."""
    if not get_cost_explorer_mcp_enabled():
        return None
    try:
        from mcp import StdioServerParameters, stdio_client
        from strands.tools.mcp import MCPClient

        command, args = get_cost_explorer_mcp_command()
        env = dict(os.environ)
        if session is not None:
            profile = getattr(session, "profile_name", None)
            if profile:
                env["AWS_PROFILE"] = profile
            region = getattr(session, "region_name", None)
            if region:
                env["AWS_REGION"] = region
        params = StdioServerParameters(command=command, args=args, env=env)
        client = MCPClient(
            lambda: stdio_client(params),
            startup_timeout=_MCP_STARTUP_TIMEOUT,
        )
        setattr(client, "_finops_mcp_server_name", _COST_EXPLORER_MCP_SERVER_NAME)
        return client
    except Exception:
        return None


def create_pricing_mcp_client(session: boto3.Session | None = None):
    """Create AWS Pricing MCP client when enabled; otherwise return None.
    Uses stdio transport (uvx subprocess); enable and command from settings/env.
    When session is provided, passes AWS_PROFILE and AWS_REGION into the subprocess.
    Disabled by default. Requires IAM pricing:* when enabled."""
    if not get_pricing_mcp_enabled():
        return None
    try:
        from mcp import StdioServerParameters, stdio_client
        from strands.tools.mcp import MCPClient

        command, args = get_pricing_mcp_command()
        env = dict(os.environ)
        if session is not None:
            profile = getattr(session, "profile_name", None)
            if profile:
                env["AWS_PROFILE"] = profile
            region = getattr(session, "region_name", None)
            if region:
                env["AWS_REGION"] = region
        params = StdioServerParameters(command=command, args=args, env=env)
        client = MCPClient(
            lambda: stdio_client(params),
            startup_timeout=_MCP_STARTUP_TIMEOUT,
        )
        setattr(client, "_finops_mcp_server_name", _PRICING_MCP_SERVER_NAME)
        return client
    except Exception:
        return None


def create_core_mcp_client(session: boto3.Session | None = None):
    """Create AWS Core MCP client when enabled; otherwise return None.
    Uses stdio transport; enable, command, and roles from settings/env.
    Passes AWS_PROFILE, AWS_REGION, and each role as role_name=true into the subprocess."""
    if not get_core_mcp_enabled():
        return None
    try:
        from mcp import StdioServerParameters, stdio_client
        from strands.tools.mcp import MCPClient

        command, args = get_core_mcp_command()
        env = dict(os.environ)
        if session is not None:
            profile = getattr(session, "profile_name", None)
            if profile:
                env["AWS_PROFILE"] = profile
            region = getattr(session, "region_name", None)
            if region:
                env["AWS_REGION"] = region
        for role in get_core_mcp_roles():
            env[role] = "true"
        params = StdioServerParameters(command=command, args=args, env=env)
        client = MCPClient(
            lambda: stdio_client(params),
            startup_timeout=_MCP_STARTUP_TIMEOUT,
        )
        roles_str = ", ".join(get_core_mcp_roles())
        setattr(
            client,
            "_finops_mcp_server_name",
            f"Core MCP Server (roles: {roles_str})",
        )
        return client
    except Exception:
        return None
