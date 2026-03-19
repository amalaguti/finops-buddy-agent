# Design: OpenAI max_completion_tokens compatibility

## Context

The FinOps chat agent uses Strands Agents with `OpenAIModel` when `FINOPS_OPENAI_API_KEY` is set. The agent passes `params={"max_tokens": 4096, "temperature": 0.2}` to `OpenAIModel`. Newer OpenAI models (gpt-5.x, o1, o3, o4-mini) require `max_completion_tokens` instead of `max_tokens`; passing `max_tokens` returns a 400 error. Users who set `FINOPS_AGENT_MODEL_ID` to a newer model cannot use the chat agent.

## Goals / Non-Goals

**Goals:**

- Support OpenAI models that require `max_completion_tokens` (e.g. gpt-5.x, o1) so users can use any supported model via `FINOPS_AGENT_MODEL_ID`.
- Preserve compatibility with older models (gpt-4o, gpt-4o-mini) that accept `max_tokens`.
- Minimal change surface: single file (`runner.py`), no new settings.

**Non-Goals:**

- Supporting the Responses API or `max_output_tokens` (different API surface; out of scope).
- Making max tokens configurable via settings (keep 4096 as default; can add later if needed).

## Decisions

### 1. Use `max_completion_tokens` for all OpenAI models

**Decision:** Pass `max_completion_tokens: 4096` instead of `max_tokens: 4096` when building `OpenAIModel`.

**Rationale:** OpenAI's Chat Completions API accepts `max_completion_tokens` for both legacy and newer models. Older models (gpt-4o) accept it; newer models (gpt-5.x, o1) require it. Using `max_completion_tokens` universally avoids model-specific branching and future-proofs for new models.

**Alternatives considered:**

- **Model detection:** Branch on `model_id` (e.g. if "o1" or "gpt-5" in id, use max_completion_tokens). Rejected: brittle, requires maintaining a list; new models would break until we update.
- **Try max_tokens, fallback to max_completion_tokens on 400:** Rejected: adds retry logic and latency; simpler to use the right param from the start.

### 2. Verify Strands OpenAIModel passes params through

**Decision:** Ensure `params` dict is passed to the underlying OpenAI client. Strands `OpenAIModel` typically forwards `params` to the API; we use `max_completion_tokens` as the key. If Strands uses a different param name internally, we may need to check Strands source or open an issue.

**Mitigation:** If Strands does not support `max_completion_tokens`, we may need to patch or wrap the model; document as open question until verified.

### 3. Keep temperature for compatible models

**Decision:** Continue passing `temperature: 0.2` for models that support it. Some reasoning models (o1) may not support temperature; if we encounter that, we can conditionally omit it. For now, keep it; the primary fix is the token param.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Strands does not forward `max_completion_tokens` | Inspect Strands OpenAIModel source; params are typically passed through. If not, file issue or patch. |
| Older models reject `max_completion_tokens` | OpenAI docs indicate Chat Completions accepts both; verify with gpt-4o if needed. |
| Reasoning models (o1) have different param needs | If o1 requires additional changes (e.g. no temperature), handle in a follow-up; this change focuses on token param. |

## Migration Plan

- No migration: code change only. Users on older models continue to work; users on newer models start working.
- Rollback: revert the param change if issues arise.
