# Chat Agent (Strands) — Proposal

## Why

The FinOps CLI today exposes fixed commands (whoami, costs, context, etc.) but does not support conversational, exploratory cost analysis. Users need to ask questions in natural language (e.g. “How did EC2 costs change month over month?” or “Compare last two weeks”) and get answers that combine current and historical cost data with comparisons (month-over-month, week-over-week, biweekly-over-biweekly). Implementing a chat agent using the Strands Agents library aligns with the project’s Phase 1 goal of an “Agent (Strands) integrated for assistant-style interaction” and sets the foundation for later wiring in local AWS MCP servers (Cost Explorer, Billing & Cost Management, etc.) so the agent can query cost data through standard tools.

## What Changes

- Add a **chat** (or **agent**) subcommand to the CLI that starts an interactive conversation loop powered by Strands Agents.
- Integrate the **strands-agents** library so the agent can hold multi-turn conversations, use tools, and call an LLM (e.g. Bedrock).
- Design the agent to **analyze and investigate costs**: past costs, current costs, and comparisons (month-over-month, week-over-week, biweekly-over-biweekly) using existing cost logic and/or tool-calling patterns that can later be backed by MCP.
- Keep the implementation **MCP-ready**: agent architecture and tool interfaces should allow swapping or adding local AWS MCP servers in a follow-up change (this change does not implement MCP servers; it delivers the Strands-based chat agent and cost-analysis capabilities).
- Add any **FINOPS_**-prefixed configuration or environment variables needed for the agent (e.g. model id, profile).

## Capabilities

### New Capabilities

- **chat-agent**: A Strands-based chat agent exposed via a CLI subcommand. It supports multi-turn conversations, can analyze and investigate costs (past, current, month-over-month, week-over-week, biweekly-over-biweekly), and is structured so that tools can later be backed by local AWS MCP servers. Includes agent lifecycle (start session, send user input, stream or print responses, exit).

### Modified Capabilities

- None. This change does not alter existing spec-level requirements for aws-identity, costs-this-month, app-settings, etc.

## Impact

- **Dependencies**: New Poetry dependency on `strands-agents` (and any runtime deps it requires; Bedrock/default model may require boto3/credentials).
- **Code**: New agent module(s) under `src/finops_agent/` (e.g. `agent/` or `chat.py`), CLI subparser and handler for the chat/agent command, reuse of existing cost and identity/session logic where applicable.
- **Configuration**: Optional agent-related settings (e.g. model id, default profile) in `config/settings.yaml` and env (e.g. `FINOPS_AGENT_MODEL_ID`), documented in README.
- **Testing**: New tests for agent initialization and for cost-analysis behavior (conversation flow and comparison types) as per spec scenarios.
- **Future**: Follow-up change will introduce local AWS MCP servers and connect them to this agent.
