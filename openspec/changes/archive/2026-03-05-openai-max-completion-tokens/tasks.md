# Tasks: openai-max-completion-tokens

## 1. Branch and setup

- [x] 1.1 Create a feature branch (e.g. `feature/openai-max-completion-tokens`) and do not implement on `main`. Switch to the branch before implementing.

## 2. Implementation

- [x] 2.1 In `src/finops_agent/agent/runner.py`, change the `OpenAIModel` params from `max_tokens` to `max_completion_tokens` when building the agent (line ~706). Use `params={"max_completion_tokens": 4096, "temperature": 0.2}` so that newer OpenAI models (gpt-5.x, o1) work without 400 errors.

## 3. Lint and format

- [x] 3.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues.

## 4. Tests

- [x] 4.1 Add or extend pytest tests in `tests/test_agent.py` for the OpenAI model param: when `build_agent` is called with OpenAI provider and a model that requires `max_completion_tokens`, the OpenAIModel is constructed with `max_completion_tokens` (not `max_tokens`). Name tests after spec scenarios where practical (e.g. `test_openai_model_uses_max_completion_tokens`).
