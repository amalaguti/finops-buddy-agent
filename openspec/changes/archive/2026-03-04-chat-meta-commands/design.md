# Chat Meta-Commands — Design

## Context

The FinOps CLI chat subcommand runs an interactive loop in `runner.py`: it reads user input, optionally handles reserved commands (e.g. `/quit`), then sends the remaining input to a Strands `Agent` and prints the response. The agent is built with `build_agent(session)` and receives a list of tools from `create_cost_tools(session)`. Strands exposes `agent.tool_names` and `agent.tool_registry.get_all_tools_config()` for tool metadata. Conversation state is maintained in the loop as a list of strings (user/agent message pairs). There is no existing way for the user to inspect available tools or conversation context from within the chat.

## Goals / Non-Goals

**Goals:**

- Intercept `/tooling` and `/context` in the chat loop (same layer as `/quit`) and respond without calling the LLM.
- For `/tooling`: Show a human-readable summary of available tools (names, descriptions, when to use). Optionally include “skills” if the implementation later exposes skill-like metadata.
- For `/context`: Show conversation context status: turn count, profile, session identity, token counts (input/output or total when available from the model/runtime), and model-specific state or info (e.g. model ID, provider) from the chat loop and agent runtime.
- Keep implementation localized to the chat runner and small helpers; no new env vars or settings unless we later add optional formatting toggles.

**Non-Goals:**

- Persisting tool-usage history or “when each tool was last used” in this change (can be added later).
- Exposing internal state to the LLM or as agent tools; meta-commands are CLI-only.
- Changing how the agent selects or invokes tools; only surfacing existing tool metadata to the user.

## Decisions

1. **Handle meta-commands in the chat loop (runner)**  
   Intercept `/tooling` and `/context` in `run_chat_loop` before building or calling the agent for that turn. Rationale: Same pattern as `/quit`; no LLM cost; simple and predictable. Alternative: Implement as agent tools—rejected to avoid extra tool-call roundtrips and to keep meta-info independent of model behavior.

2. **Tool list source: Strands tool registry**  
   Use the existing Strands agent’s tool registry (e.g. `agent.tool_names`, `agent.tool_registry.get_all_tools_config()`) to build the `/tooling` output. Rationale: Single source of truth; includes names, descriptions, and parameter schemas. “When they are used” can be derived from tool docstrings/descriptions already present in the registry.

3. **Context content: turns, profile, session, tokens, model info**  
   For `/context`, display: number of conversation turns (user + agent messages), current AWS profile name (if any), session/account identifier (e.g. from `get_session`), token counts (input/output or total when exposed by Strands or the model provider), and model-specific state or info (e.g. model ID, provider name). Rationale: Gives users full visibility into conversation length, identity, and usage (tokens) and which model is in use. Token and model info SHALL be included when the Strands agent or runtime exposes them (e.g. via usage metadata or agent config); if not available, show “N/A” or omit and document the limitation.

4. **Normalization of command trigger**  
   Treat `/tooling` and `/context` as case-insensitive and strip surrounding whitespace so `/Tooling` and `  /context  ` are recognized. Rationale: Better UX; consistent with common chat conventions.

5. **Do not append meta-command turns to conversation**  
   When the user types `/tooling` or `/context`, print the response and prompt again without appending that user message or a synthetic agent reply to the conversation list. Rationale: Keeps conversation history focused on real Q&A; meta-commands are inspection only.

## Risks / Trade-offs

- **Risk**: Tool registry format may change in future Strands versions.  
  **Mitigation**: Use the documented public API (`tool_names`, `get_all_tools_config()`); if the API changes, we only adapt the formatter.

- **Trade-off**: We do not show “last time each tool was used” in this change.  
  **Mitigation**: Document as future enhancement; current scope is “what is available and when to use” from descriptions only.

- **Risk**: Strands or the model provider may not expose token counts or model metadata in the same way across providers (Bedrock vs OpenAI).  
  **Mitigation**: When token counts or model-specific state are available (e.g. from response metadata or agent config), include them in `/context`; otherwise show “N/A” or a short note so users know what is and isn’t available.
