# chat-agent Specification (delta: openai-max-completion-tokens)

## ADDED Requirements

### Requirement: OpenAI model parameter compatibility

When using the OpenAI provider (FINOPS_OPENAI_API_KEY set), the agent SHALL pass completion-token parameters in a format supported by the configured model. Newer OpenAI models (e.g. gpt-5.x, o1) require `max_completion_tokens` instead of `max_tokens`. The agent SHALL use `max_completion_tokens` (or the appropriate parameter for the model) so that users can configure any supported OpenAI model via `FINOPS_AGENT_MODEL_ID` without API parameter errors.

#### Scenario: Agent starts with newer OpenAI model requiring max_completion_tokens

- **WHEN** `FINOPS_OPENAI_API_KEY` is set, `FINOPS_AGENT_MODEL_ID` is set to a model that requires `max_completion_tokens` (e.g. gpt-5.4, o1), and the user starts a chat session
- **THEN** the agent starts successfully and can process at least one user message without a 400 "Unsupported parameter: max_tokens" error

#### Scenario: Agent starts with legacy OpenAI model

- **WHEN** `FINOPS_OPENAI_API_KEY` is set, `FINOPS_AGENT_MODEL_ID` is set to a legacy model (e.g. gpt-4o) or unset (default gpt-4o), and the user starts a chat session
- **THEN** the agent starts successfully and can process at least one user message
