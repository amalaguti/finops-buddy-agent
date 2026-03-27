"""One-turn chat for the API: build agent, run once, return reply and optional usage."""

from __future__ import annotations

import logging
import threading
import time

from finops_buddy.agent.artifacts import (
    parse_reply_data_uri_images,
    strip_non_data_uri_images,
)
from finops_buddy.agent.builder import build_agent
from finops_buddy.agent.chart_tools import create_chart_tools
from finops_buddy.agent.chat_loop import _build_chat_system_prompt
from finops_buddy.agent.mcp import (
    create_billing_mcp_client,
    create_core_mcp_client,
    create_cost_explorer_mcp_client,
    create_documentation_mcp_client,
    create_knowledge_mcp_client,
    create_pricing_mcp_client,
)
from finops_buddy.agent.tools import create_cost_tools, create_export_tools
from finops_buddy.config import get_master_profile
from finops_buddy.context import get_account_context
from finops_buddy.costs import get_linked_account_ids
from finops_buddy.identity import (
    get_profile_account_ids_from_local_files,
    get_session,
    list_profiles,
)
from finops_buddy.settings import get_demo_account_mapping

from .demo import get_demo_system_prompt_addition

logger = logging.getLogger(__name__)
# Ensure chat logger emits to console (same as app.py) so "Loading MCP…" appears in
# FastAPI/uvicorn logs
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(levelname)s [%(name)s] %(message)s"))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)

# Interval (seconds) for "Still loading MCP…" log and progress during long MCP startup.
_MCP_LOADING_HEARTBEAT_INTERVAL = 12

# TTL in seconds for profile→account_id mapping (accounts don't change often).
_PROFILE_ACCOUNT_CACHE_TTL = 3600  # 1 hour

_profile_account_cache: dict = {"mapping": {}, "expires_at": 0.0}
_profile_account_cache_lock = threading.Lock()
_profile_account_cache_refreshing = False

# Cache for long-lived agents and tools, keyed by agent profile (e.g. master profile).
_AGENT_CACHE: dict[str | None, tuple[object, list]] = {}


def resolve_agent_profile(request_profile: str | None) -> str | None:
    """
    Resolve which AWS profile to use for the agent session.

    When FINOPS_MASTER_PROFILE is set, always use that for the agent (single payer
    session shared across chats). Otherwise, fall back to the request profile.
    """
    master = get_master_profile()
    return master or request_profile


def warm_chat_agent_on_startup() -> None:
    """
    Optional warm-up for the HTTP API: build a long-lived agent and account mapping.

    Uses FINOPS_MASTER_PROFILE when set; otherwise does nothing. Intended to be
    called once at process startup when an env flag enables warm-up.
    """
    agent_profile = get_master_profile()
    if agent_profile is None:
        return
    build_agent_and_tools(agent_profile)
    # Mapping is already refreshed in background at startup; touch cache so it’s warm
    _get_cached_profile_account_mapping(blocking=False)


def _populate_profile_account_mapping() -> dict[str, str]:
    """Build profile name -> account_id mapping with cheap local/CE sources first."""
    profile_names = list_profiles()
    mapping = get_profile_account_ids_from_local_files(profile_names)

    unresolved = [name for name in profile_names if name not in mapping]
    master_profile = get_master_profile()

    if unresolved and master_profile:
        try:
            master_session = get_session(profile_name=master_profile)
            get_linked_account_ids(master_session)
        except Exception:
            pass

    # STS is the slow fallback; use it only for profiles unresolved by local parsing.
    for name in unresolved:
        try:
            ctx = get_account_context(profile_name=name)
            # Keep the discovered mapping even if the account is not billing-linked; it may
            # still be useful for profile display. CE results are mainly used to avoid doing
            # account discovery by resolving every profile over the network.
            mapping[name] = ctx.account_id
        except Exception:
            continue

    return mapping


def _refresh_profile_account_mapping_background() -> None:
    """Populate profile/account cache in the background so chat is not blocked."""
    global _profile_account_cache_refreshing
    try:
        mapping = _populate_profile_account_mapping()
        now = time.monotonic()
        with _profile_account_cache_lock:
            _profile_account_cache["mapping"] = mapping
            _profile_account_cache["expires_at"] = now + _PROFILE_ACCOUNT_CACHE_TTL
    finally:
        _profile_account_cache_refreshing = False


def _start_profile_account_mapping_refresh() -> None:
    """Start a background refresh if one is not already running."""
    global _profile_account_cache_refreshing
    if _profile_account_cache_refreshing:
        return
    _profile_account_cache_refreshing = True
    thread = threading.Thread(
        target=_refresh_profile_account_mapping_background,
        name="finops-profile-account-cache",
        daemon=True,
    )
    thread.start()


def start_profile_account_mapping_refresh() -> None:
    """
    Start profile→account_id mapping refresh in the background (non-blocking).
    Call at app startup so the cache is often ready by the first chat request.
    """
    _start_profile_account_mapping_refresh()


def _get_cached_profile_account_mapping(*, blocking: bool = True) -> dict[str, str]:
    """
    Return profile name → account_id. Cached with TTL to avoid repeated STS/resolution.
    """
    now = time.monotonic()
    if now <= _profile_account_cache["expires_at"] and _profile_account_cache["mapping"]:
        return _profile_account_cache["mapping"]

    if not blocking:
        _start_profile_account_mapping_refresh()
        return dict(_profile_account_cache["mapping"])

    mapping = _populate_profile_account_mapping()
    with _profile_account_cache_lock:
        _profile_account_cache["mapping"] = mapping
        _profile_account_cache["expires_at"] = now + _PROFILE_ACCOUNT_CACHE_TTL
    return mapping


def _cleanup_agent_tools(agent) -> None:
    """Clean up MCP clients so they shut down cleanly."""
    registry = getattr(agent, "tool_registry", None)
    if registry is None:
        return
    try:
        registry.cleanup()
    except Exception:
        pass


def _run_mcp_creator_with_heartbeat(
    mcp_name: str,
    creator: callable,
    progress_callback=None,
):
    """
    Run creator() in a thread; while it runs, log and emit "Still loading <name>… (Ns)"
    every _MCP_LOADING_HEARTBEAT_INTERVAL seconds so the UI and FastAPI log stay verbose.
    Returns whatever creator() returns.
    """
    result_holder: list = []
    exc_holder: list = []

    def run():
        try:
            result_holder.append(creator())
        except Exception as e:
            exc_holder.append(e)

    thread = threading.Thread(target=run, name=f"mcp-{mcp_name}", daemon=True)
    start = time.monotonic()
    thread.start()

    def emit(message: str) -> None:
        if callable(progress_callback) and message:
            try:
                progress_callback("mcp_loading", message)
            except Exception:
                pass

    while thread.is_alive():
        thread.join(timeout=_MCP_LOADING_HEARTBEAT_INTERVAL)
        if not thread.is_alive():
            break
        elapsed = int(time.monotonic() - start)
        msg = f"Still loading {mcp_name} MCP server… ({elapsed}s)"
        logger.info("Still loading MCP: %s… (%ds)", mcp_name, elapsed)
        emit(msg)

    if exc_holder:
        raise exc_holder[0]
    return result_holder[0] if result_holder else None


def build_agent_and_tools(
    profile_name: str | None,
    progress_callback=None,
    chart_artifact_collector: list | None = None,
    file_export_artifact_collector: list | None = None,
) -> tuple:
    """
    Build session, tools (MCP + cost + export), and agent for the given profile.

    progress_callback: optional callable(event, tool_name) for tool_start/tool_end (API streaming).
    chart_artifact_collector: optional list to collect create_chart tool results as artifacts.
    file_export_artifact_collector: optional list for export_to_pdf/export_to_excel file artifacts.
    Returns (agent, tools). Results are cached per agent profile to avoid rebuilds.
    """
    cache_key = profile_name or "__default__"
    cached = _AGENT_CACHE.get(cache_key)

    # Chat requests require a per-request callback/queue. Reusing a cached agent
    # would keep an old callback and break progress updates. So reuse cached tools
    # but build a fresh lightweight agent wrapper for this request.
    if cached is not None and callable(progress_callback):
        logger.info(
            "Using cached agent and MCP tools for profile=%s (no MCP loading for this request)",
            profile_name,
        )
        _cached_agent, cached_tools = cached
        session = get_session(profile_name=profile_name)
        ephemeral_agent = build_agent(
            session,
            profile_name,
            tools=cached_tools,
            progress_callback=progress_callback,
            chart_artifact_collector=chart_artifact_collector,
            file_export_artifact_collector=file_export_artifact_collector,
        )
        return (ephemeral_agent, cached_tools)

    if cached is not None:
        return cached

    logger.info(
        "Building agent and MCP tools (cold build) for profile=%s; progress will be logged below",
        profile_name,
    )
    session = get_session(profile_name=profile_name)

    def _emit_mcp_progress(message: str) -> None:
        if callable(progress_callback) and message:
            try:
                progress_callback("mcp_loading", message)
            except Exception:
                # Progress is best-effort; ignore callback errors.
                pass

    logger.info("Building agent tools for profile=%s", profile_name)

    def _load_mcp(name: str, creator):
        logger.info("Loading MCP: %s…", name)
        _emit_mcp_progress(f"Starting {name} MCP server…")
        client = _run_mcp_creator_with_heartbeat(name, creator, progress_callback)
        logger.info("MCP %s %s", name, "ready" if client is not None else "skipped")
        _emit_mcp_progress(
            f"{name} MCP ready" if client is not None else f"{name} MCP skipped (not enabled)"
        )
        return client

    core_client = _load_mcp("Core", lambda: create_core_mcp_client(session))
    billing_client = _load_mcp("Billing", lambda: create_billing_mcp_client(session))
    cost_explorer_client = _load_mcp(
        "Cost Explorer", lambda: create_cost_explorer_mcp_client(session)
    )
    pricing_client = _load_mcp("Pricing", lambda: create_pricing_mcp_client(session))

    include_cost_tools = billing_client is None
    tools = list(create_cost_tools(session, include_cost_tools=include_cost_tools))
    tools.extend(create_chart_tools())
    tools.extend(create_export_tools())

    knowledge_client = _load_mcp("Knowledge", create_knowledge_mcp_client)

    if knowledge_client is not None:
        tools.append(knowledge_client)
    if billing_client is not None:
        tools.append(billing_client)
    documentation_client = _load_mcp(
        "Documentation", lambda: create_documentation_mcp_client(session)
    )
    if documentation_client is not None:
        tools.append(documentation_client)
    if cost_explorer_client is not None:
        tools.append(cost_explorer_client)
    if pricing_client is not None:
        tools.append(pricing_client)
    if core_client is not None:
        tools.append(core_client)
    cached_agent = build_agent(session, profile_name, tools=tools, progress_callback=None)
    pair = (cached_agent, tools)
    _AGENT_CACHE[cache_key] = pair

    if callable(progress_callback):
        ephemeral_agent = build_agent(
            session,
            profile_name,
            tools=tools,
            progress_callback=progress_callback,
            chart_artifact_collector=chart_artifact_collector,
            file_export_artifact_collector=file_export_artifact_collector,
        )
        return (ephemeral_agent, tools)
    return pair


def run_chat_turn(
    profile_name: str | None,
    message: str,
    messages: list[dict] | None = None,
    progress_callback=None,
    demo_mode: bool = False,
) -> tuple[str, dict | None, list[dict]]:
    """
    Build agent and tools, run one agent turn, return (reply_text, usage_dict | None, artifacts).

    messages: optional list of {"role": "user"|"assistant", "content": str} for conversation
    history. The new message is appended as a user turn.
    progress_callback: optional callable(event, tool_name) for tool_start/tool_end (API streaming).
    demo_mode: when True, append demo masking instructions to system prompt.
    artifacts: list of {type, title, content} parsed from embedded data URI images in the reply,
    plus chart tool results and export_to_pdf/export_to_excel files for the web UI basket.
    """
    agent_profile = resolve_agent_profile(profile_name)
    chart_artifacts: list = []
    file_export_artifacts: list = []
    if callable(progress_callback):
        progress_callback("phase", "Preparing agent session")
    agent, tools = build_agent_and_tools(
        agent_profile,
        progress_callback=progress_callback,
        chart_artifact_collector=chart_artifacts,
        file_export_artifact_collector=file_export_artifacts,
    )
    try:
        if callable(progress_callback):
            progress_callback("phase", "Preparing system prompt")
        system_prompt = _build_chat_system_prompt()
        if callable(progress_callback):
            progress_callback("phase", "Loading cached account mappings")
        mapping = _get_cached_profile_account_mapping(blocking=False)
        if mapping:
            parts = [f"{name} ({aid})" for name, aid in sorted(mapping.items())]
            system_prompt += (
                "\n\nKnown profile-to-account mappings (use these when showing account IDs; "
                "always show both name and ID): " + "; ".join(parts) + "."
            )
        elif callable(progress_callback):
            # Profile→account_id cache is filled in a background thread (AWS config + STS per
            # profile), so it can still be empty here. We don't block; this runs after MCP/agent
            # build, so the toast often appears after MCP loading. Informational only.
            progress_callback(
                "phase",
                "Account map is still warming in background; continuing without the full map",
            )
        if profile_name:
            account_id = mapping.get(profile_name)
            if account_id is None:
                try:
                    account_id = get_account_context(profile_name=profile_name).account_id
                except Exception:
                    pass
            if account_id:
                system_prompt += (
                    f"\n\nCurrent profile: {profile_name}, Account ID: {account_id}. "
                    "For other accounts, use tools to get names and show both name and ID."
                )
        if demo_mode:
            demo_mapping = get_demo_account_mapping()
            system_prompt += get_demo_system_prompt_addition(demo_mapping)
        conversation: list[str] = []
        if messages:
            for m in messages:
                role = (m.get("role") or "user").lower()
                content = (m.get("content") or "").strip()
                if not content:
                    continue
                if role == "user":
                    conversation.append(f"User: {content}")
                else:
                    conversation.append(f"Agent: {content}")
        conversation.append(f"User: {message}")
        full_prompt = system_prompt + "\n\n" + "\n\n".join(conversation)
        if callable(progress_callback):
            progress_callback("phase", "Invoking agent model")
        result = agent(full_prompt)
        text = str(result).strip()
        usage = None
        try:
            metrics = getattr(result, "metrics", None)
            if metrics is not None:
                acc = getattr(metrics, "accumulated_usage", None)
                if isinstance(acc, dict):
                    usage = {
                        "input_tokens": acc.get("inputTokens", acc.get("input_tokens", 0)),
                        "output_tokens": acc.get("outputTokens", acc.get("output_tokens", 0)),
                    }
        except Exception:
            pass
        artifacts = parse_reply_data_uri_images(text) + chart_artifacts + file_export_artifacts
        if chart_artifacts:
            # Remove model placeholders like ![Chart](url) so UI doesn't show "[image not shown]"
            text = strip_non_data_uri_images(text)
            if "data:image/" not in text:
                for art in chart_artifacts:
                    title = art.get("title") or "Chart"
                    content = art.get("content") or ""
                    if content:
                        text += "\n\n" + f"![{title}]({content})"
        return (text, usage, artifacts)
    finally:
        # Agents and MCP clients are cached for reuse; no per-request cleanup here.
        pass
