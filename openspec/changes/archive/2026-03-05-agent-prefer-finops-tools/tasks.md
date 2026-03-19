## 1. Branch and system prompt

- [x] 1.1 Create a feature branch (e.g. `feature/agent-prefer-finops-tools` or `FT/agent-prefer-finops-tools`) and switch to it; do not implement on main.
- [x] 1.2 In `run_chat_loop` in `src/finops_agent/agent/runner.py`, extend the `system_prompt` string (around lines 605–612) with 3–5 concise sentences that: (a) prefer cost-explorer, budgets, and pricing tools for listing linked/member accounts and for cost and usage queries; (b) use Billing Conductor tools only when the user explicitly asks for billing groups, custom line items, or pro forma costs; (c) on permission/access-denied errors (e.g. mentioning billingconductor), retry the intent using cost-explorer, budgets, or pricing where they can answer the same question. Keep the new text short to avoid unnecessary token growth.

## 2. Documentation

- [x] 2.1 Optionally add a short note in README.md (under Chat or Configuration) that the agent is instructed to prefer Cost Explorer, Budgets, and Pricing tools over Billing Conductor for account lists and cost data to improve compatibility with roles that have ce:* / budgets:* but not billingconductor:*.

## 3. Lint and tests

- [x] 3.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues.
- [x] 3.2 Add or extend pytest tests in `tests/` that assert the chat agent's system prompt (as built in the runner) contains the required tool-preference and permission-awareness guidance (e.g. that the prompt string includes references to preferring cost-explorer/budgets/pricing and to retrying on permission errors). Map to the spec scenarios where practical (e.g. test that prompt instructs preference for cost-explorer for account lists, and retry with FinOps tools on permission error).
