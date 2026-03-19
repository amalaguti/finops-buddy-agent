"""Strands agent builder, callback handler, and tool metadata helpers."""

from __future__ import annotations

import copy
import json

import boto3

from finops_buddy.agent.artifacts import parse_reply_data_uri_images
from finops_buddy.agent.chart_tools import create_chart_tools
from finops_buddy.agent.guardrails import ReadOnlyToolGuardrail
from finops_buddy.agent.mcp import (
    _mcp_server_name_for_tool,
    create_billing_mcp_client,
    create_core_mcp_client,
    create_cost_explorer_mcp_client,
    create_documentation_mcp_client,
    create_knowledge_mcp_client,
    create_pricing_mcp_client,
)
from finops_buddy.agent.tools import create_cost_tools
from finops_buddy.settings import (
    get_agent_max_completion_tokens,
    get_agent_model_id,
    get_agent_temperature,
    get_openai_api_key,
    get_read_only_allowed_tools,
    get_verbose_tool_debug,
)

# Max characters to show for tool result in verbose debug (avoid flooding the console).
_VERBOSE_TOOL_RESULT_MAX_CHARS = 4000


def _tool_result_as_string(result: object) -> str | None:
    """Extract a single string from a Strands tool result (may be dict with content list or plain str)."""
    if result is None:
        return None
    if isinstance(result, str):
        return result
    content = None
    if isinstance(result, dict):
        content = result.get("content")
        text = result.get("text")
        if isinstance(text, str):
            return text
    else:
        content = getattr(result, "content", None)
    if isinstance(content, list) and content:
        for block in content:
            if isinstance(block, dict):
                text = block.get("text") or block.get("content")
                if isinstance(text, str):
                    return text
            elif isinstance(block, str):
                return block
    if isinstance(result, dict):
        text = result.get("text") or result.get("content")
        if isinstance(text, list) and text and isinstance(text[0], dict):
            return text[0].get("text") or text[0].get("content") or None
        for v in result.values():
            if isinstance(v, str) and "data:image/" in v:
                return v
            if isinstance(v, list) and v and isinstance(v[0], dict):
                for block in v:
                    s = block.get("text") or block.get("content")
                    if isinstance(s, str) and "data:image/" in s:
                        return s
    return None


def _format_tool_result_for_debug(result: object) -> str:
    """Format tool result or exception for verbose debug output. Truncates long content."""
    if result is None:
        return "(no result)"
    if isinstance(result, BaseException):
        return f"Exception: {type(result).__name__}: {result!s}"
    content = getattr(result, "content", None)
    status = getattr(result, "status", None)
    if content is not None and isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                text = block.get("text") or block.get("content") or str(block)
            else:
                text = str(block)
            parts.append(text)
        out = "\n".join(parts)
    else:
        out = str(result)
    if status is not None:
        out = f"[{status}]\n{out}"
    if len(out) > _VERBOSE_TOOL_RESULT_MAX_CHARS:
        out = out[:_VERBOSE_TOOL_RESULT_MAX_CHARS] + "\n... (truncated)"
    return out


class _ProgressCallbackHook:
    """Hook that invokes progress_callback on tool start/end for API streaming."""

    def __init__(self, progress_callback) -> None:
        self._cb = progress_callback

    def register_hooks(self, registry: object, **kwargs: object) -> None:
        if not callable(self._cb):
            return
        from strands.hooks import AfterToolCallEvent, BeforeToolCallEvent

        registry.add_callback(BeforeToolCallEvent, self._on_before_tool)
        registry.add_callback(AfterToolCallEvent, self._on_after_tool)

    def _on_before_tool(self, event: object) -> None:
        tool_use = getattr(event, "tool_use", None)
        if isinstance(tool_use, dict):
            name = tool_use.get("name") or "?"
            try:
                self._cb("tool_start", name)
            except Exception:
                pass

    def _on_after_tool(self, event: object) -> None:
        tool_use = getattr(event, "tool_use", None)
        if isinstance(tool_use, dict):
            name = tool_use.get("name") or "?"
            try:
                self._cb("tool_end", name)
            except Exception:
                pass


class _ChartArtifactCollectorHook:
    """Hook that collects create_chart tool results so they can be used as artifacts even if the model omits them from the reply."""

    def __init__(self, collector: list) -> None:
        self._collector = collector

    def register_hooks(self, registry: object, **kwargs: object) -> None:
        from strands.hooks import AfterToolCallEvent

        registry.add_callback(AfterToolCallEvent, self._on_after_tool)

    def _on_after_tool(self, event: object) -> None:
        tool_use = getattr(event, "tool_use", None)
        result = getattr(event, "result", None)
        if not isinstance(tool_use, dict) or tool_use.get("name") != "create_chart":
            return
        result_str = _tool_result_as_string(result)
        if not isinstance(result_str, str) or "data:image/" not in result_str:
            return
        parsed = parse_reply_data_uri_images(result_str)
        self._collector.extend(parsed)


class _VerboseToolDebugHook:
    """Hook that prints tool name, input, and result when verbose_tool_debug is enabled."""

    def __init__(self, enabled: bool) -> None:
        self._enabled = enabled

    def register_hooks(self, registry: object, **kwargs: object) -> None:
        if not self._enabled:
            return
        from strands.hooks import AfterToolCallEvent, BeforeToolCallEvent

        registry.add_callback(BeforeToolCallEvent, self._on_before_tool)
        registry.add_callback(AfterToolCallEvent, self._on_after_tool)

    def _on_before_tool(self, event: object) -> None:
        tool_use = getattr(event, "tool_use", None)
        if not isinstance(tool_use, dict):
            return
        name = tool_use.get("name", "?")
        inp = tool_use.get("input") or tool_use.get("arguments")
        if inp:
            try:
                inp_str = json.dumps(inp, indent=2) if isinstance(inp, dict) else str(inp)
            except (TypeError, ValueError):
                inp_str = str(inp)
            if len(inp_str) > 1500:
                inp_str = inp_str[:1500] + "\n... (truncated)"
            print(f"\n  [tool input] {name}:\n{inp_str}")
        else:
            print(f"\n  [tool input] {name}: (no arguments)")

    def _on_after_tool(self, event: object) -> None:
        tool_use = getattr(event, "tool_use", None)
        result = getattr(event, "result", None)
        cancel_message = getattr(event, "cancel_message", None)
        exception = getattr(event, "exception", None)
        name = "?"
        if isinstance(tool_use, dict):
            name = tool_use.get("name", "?")
        if cancel_message:
            print(f"\n  [tool result] {name}: (cancelled) {cancel_message}")
        elif exception is not None:
            print(f"\n  [tool result] {name}: {_format_tool_result_for_debug(exception)}")
        else:
            print(f"\n  [tool result] {name}:\n{_format_tool_result_for_debug(result)}")


def _create_finops_callback_handler():
    """Create a callback handler that prints tool use with MCP server name when known."""
    from strands.handlers.callback_handler import PrintingCallbackHandler

    class FinOpsCallbackHandler(PrintingCallbackHandler):
        """Print tool use as 'Tool #N: name (MCP: server)' when from a known MCP."""

        def __call__(self, **kwargs: object) -> None:
            event = kwargs.get("event")
            tool_use = None
            if isinstance(event, dict):
                cb = event.get("contentBlockStart")
                if isinstance(cb, dict):
                    start = cb.get("start")
                    if isinstance(start, dict):
                        tool_use = start.get("toolUse")

            if tool_use and isinstance(tool_use, dict):
                self.tool_count += 1
                tool_name = tool_use.get("name", "")
                mcp = _mcp_server_name_for_tool(tool_name)
                if self._verbose_tool_use:
                    suffix = f" (MCP: {mcp})" if mcp else ""
                    print(f"\nTool #{self.tool_count}: {tool_name}{suffix}")
                # Strip toolUse from event so parent does not print again
                kwargs = dict(kwargs)
                event_copy = copy.deepcopy(event)
                cb = event_copy.get("contentBlockStart")
                if isinstance(cb, dict) and "start" in cb:
                    start_copy = dict(cb["start"])
                    if "toolUse" in start_copy:
                        del start_copy["toolUse"]
                        event_copy["contentBlockStart"] = {
                            **cb,
                            "start": start_copy,
                        }
                        kwargs["event"] = event_copy
            super().__call__(**kwargs)

    return FinOpsCallbackHandler()


def _tool_source_type(tool_obj) -> str:
    """Infer tool type: MCP, Skill, Built-in, or Custom. Uses _finops_tool_source if set."""
    source = getattr(tool_obj, "_finops_tool_source", None)
    if isinstance(source, str) and source:
        return source.strip().lower().capitalize()
    mod = (getattr(tool_obj, "__module__", "") or "").lower()
    if "mcp" in mod or "strands.tools.mcp" in mod:
        return "MCP"
    if mod.startswith("finops_buddy"):
        return "Built-in"
    return "Custom"


def _tool_origin(tool_obj) -> str:
    """Return module.function origin when available."""
    mod = getattr(tool_obj, "__module__", None)
    name = getattr(tool_obj, "__name__", None)
    if mod and name and not name.startswith("<"):
        return f"{mod}.{name}"
    return ""


def build_agent(
    session: boto3.Session,
    profile_name: str | None = None,
    tools: list | None = None,
    progress_callback=None,
    chart_artifact_collector: list | None = None,
):
    """Build agent with cost tools and optional Knowledge + Billing MCP.
    Uses OpenAI if FINOPS_OPENAI_API_KEY set, else Bedrock.
    If tools is provided, use it; else create_cost_tools(session) + MCP when enabled.
    When Billing MCP is enabled, in-process cost tools are omitted so the MCP server
    handles cost queries (only get_current_date is kept)."""
    from strands import Agent

    if tools is None:
        core_client = create_core_mcp_client(session)
        billing_client = create_billing_mcp_client(session)
        cost_explorer_client = create_cost_explorer_mcp_client(session)
        pricing_client = create_pricing_mcp_client(session)
        include_cost_tools = billing_client is None
        tools = list(create_cost_tools(session, include_cost_tools=include_cost_tools))
        tools.extend(create_chart_tools())
        knowledge_client = create_knowledge_mcp_client()
        if knowledge_client is not None:
            tools.append(knowledge_client)
        if billing_client is not None:
            tools.append(billing_client)
        documentation_client = create_documentation_mcp_client(session)
        if documentation_client is not None:
            tools.append(documentation_client)
        if cost_explorer_client is not None:
            tools.append(cost_explorer_client)
        if pricing_client is not None:
            tools.append(pricing_client)
        if core_client is not None:
            tools.append(core_client)
    hooks_list: list = [ReadOnlyToolGuardrail(get_read_only_allowed_tools())]
    if callable(progress_callback):
        hooks_list.append(_ProgressCallbackHook(progress_callback))
    if chart_artifact_collector is not None:
        hooks_list.append(_ChartArtifactCollectorHook(chart_artifact_collector))
    if get_verbose_tool_debug():
        hooks_list.append(_VerboseToolDebugHook(enabled=True))
    kwargs = {
        "tools": tools,
        "callback_handler": _create_finops_callback_handler(),
        "hooks": hooks_list,
    }

    openai_key = get_openai_api_key()
    if openai_key:
        from strands.models.openai import OpenAIModel

        model_id = get_agent_model_id() or "gpt-4o"
        temperature = get_agent_temperature()
        max_tokens = get_agent_max_completion_tokens()
        model = OpenAIModel(
            client_args={"api_key": openai_key},
            model_id=model_id,
            params={"max_completion_tokens": max_tokens, "temperature": temperature},
        )
        kwargs["model"] = model
    else:
        model_id = get_agent_model_id()
        if model_id:
            kwargs["model"] = model_id
    return Agent(**kwargs)
