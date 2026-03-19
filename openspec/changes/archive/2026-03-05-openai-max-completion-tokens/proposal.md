# Proposal: OpenAI max_completion_tokens compatibility

## Why

Newer OpenAI models (e.g. gpt-5.x, o1) require `max_completion_tokens` instead of `max_tokens` when invoking the API. The agent currently passes `max_tokens` in the OpenAI model params, causing a 400 error: "Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead." Users who set `FINOPS_AGENT_MODEL_ID` to a newer model cannot use the chat agent until this is fixed.

## What Changes

- Use `max_completion_tokens` (or the appropriate parameter) when building the OpenAI model for the Strands agent, so that newer models (gpt-5.x, o1, etc.) work correctly.
- Preserve compatibility with older models (gpt-4o, gpt-4o-mini) that accept `max_tokens`—either by detecting model type and choosing the right param, or by using a param that both accept (if the API supports it).
- No new settings or env vars; the fix is internal to how we pass params to the Strands OpenAIModel.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `chat-agent`: Add requirement that the agent SHALL support OpenAI models that require `max_completion_tokens` (e.g. gpt-5.x, o1) when using the OpenAI provider, so that users can configure any supported OpenAI model via `FINOPS_AGENT_MODEL_ID` without API parameter errors.

## Impact

- **Code**: `src/finops_agent/agent/runner.py` — the `build_agent()` function where `OpenAIModel` is instantiated with `params={"max_tokens": 4096, "temperature": 0.2}`.
- **Dependencies**: Strands Agents / OpenAIModel — we pass params through; need to verify Strands accepts `max_completion_tokens` or how to adapt.
- **Testing**: Add or extend pytest to cover OpenAI model param selection (e.g. when using a model that requires max_completion_tokens, the agent starts without error).
