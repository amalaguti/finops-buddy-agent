## 1. Chat loop meta-command handling

- [x] 1.1 In `run_chat_loop` (runner.py), after reading user input and before calling the agent: normalize input (strip, case-insensitive) and if it equals `/tooling` or `/context`, handle the command and continue the loop without appending to conversation or calling the agent
- [x] 1.2 Implement `/tooling` handler: build the agent (or use existing agent reference), get tool list from `agent.tool_names` and `agent.tool_registry.get_all_tools_config()`, format a human-readable summary (name, description, when to use) and print it; then prompt for next input
- [x] 1.3 Implement `/context` handler: from the chat loop’s conversation list, session/profile, and agent runtime (when available), format context status (turn count, profile name, session/account, token counts, model ID/provider) and print it; then prompt for next input; show “N/A” or omit token/model info when the runtime does not expose it
- [x] 1.4 Update the chat welcome message (e.g. “FinOps chat… Type /quit or …”) to mention `/tooling` and `/context` alongside `/quit`

## 2. Documentation

- [x] 2.1 In README.md, document the chat reserved commands: `/quit`, `/tooling`, and `/context` (what each does), in the Configuration or CLI/chat section where the chat subcommand is described

## 3. Lint and format

- [x] 3.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues

## 4. Tests

- [x] 4.1 Add pytest tests for chat meta-commands: one test per spec scenario (user enters /tooling sees tools, user enters /context sees context, meta-commands not sent to agent, welcome or docs mention meta-commands); place in `tests/test_chat_cli.py` or `tests/test_agent.py` as appropriate; name tests after the scenario
