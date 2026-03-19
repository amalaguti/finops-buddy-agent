# Chat Meta-Commands — Proposal

## Why

Users in a FinOps chat session have no built-in way to inspect what the agent can do (available tools, skills) or to see the current conversation context (e.g. turn count, session state). This makes it harder to debug, onboard, and understand agent behavior. Adding reserved commands `/tooling` and `/context` lets users request this internal information on demand without leaving the chat.

## What Changes

- **Reserved command `/tooling`**: When the user enters `/tooling` at the chat prompt, the CLI SHALL display internal tooling information: list of available tools (and skills, if any), their purpose, and when they are used. No LLM call is required for this; the response is generated from the agent’s loaded tools (and any skill metadata the implementation exposes).
- **Reserved command `/context`**: When the user enters `/context` at the chat prompt, the CLI SHALL display conversation context status: number of turns, current session/profile, token counts (when available from the model/runtime), and model-specific state or info (e.g. model ID, provider). No LLM call is required; the response is generated from the chat loop’s conversation state and from agent/runtime metadata when available.
- **Behavior**: Both commands SHALL be handled in the chat loop before sending input to the agent (similar to existing `/quit`). The agent SHALL NOT receive `/tooling` or `/context` as user messages.
- **Documentation**: Document `/tooling` and `/context` in the chat welcome message or README so users know they are available.

## Capabilities

### New Capabilities

- None. This change extends the existing chat agent with new reserved commands.

### Modified Capabilities

- **chat-agent**: Add requirements for reserved commands `/tooling` (show available tools/skills and when they are used) and `/context` (show conversation context status, including token counts and model-specific state when available). Chat loop SHALL intercept these commands and respond without invoking the LLM.

## Impact

- **Code**: `src/finops_agent/agent/runner.py` (chat loop) — intercept `/tooling` and `/context`, format and print tool list and context summary (including token counts and model info when Strands/runtime expose them); optionally expose tool-registry or session state for formatting. May need a small helper to format “when tools are used” (e.g. from tool docstrings or a fixed description).
- **Spec**: `openspec/specs/chat-agent/spec.md` — new requirement and scenarios for meta-commands.
- **Docs**: README or in-app prompt — mention `/tooling` and `/context` along with `/quit`.
- **Dependencies**: None. Uses existing Strands agent and tool registry (e.g. `agent.tool_names`, `agent.tool_registry.get_all_tools_config()` per Strands docs).
