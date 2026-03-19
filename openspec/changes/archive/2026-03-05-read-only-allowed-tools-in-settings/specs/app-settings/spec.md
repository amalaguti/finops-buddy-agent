## ADDED Requirements

### Requirement: Resolve read-only allowed tools from YAML

The system SHALL resolve the read-only tool allow-list from the application settings file under `agent.read_only_allowed_tools` (YAML list of strings, each a tool name). When this key is present and is a non-empty list, the resolved allow-list SHALL be exactly that list (as a set) and SHALL be exposed to the read-only tool guardrail. When the key is absent, not a list, or an empty list, the system SHALL use the application default allow-list (built-in FinOps tools plus known MCP read-only tool names). No environment variable SHALL override this setting; configuration is file-only for the allow-list.

#### Scenario: Default allow-list when key is absent

- **WHEN** the settings file has no `agent.read_only_allowed_tools` (or the key is missing)
- **THEN** the resolved allow-list is the application default (built-in + known MCP read-only tools)

#### Scenario: Default allow-list when key is empty list

- **WHEN** the settings file sets `agent.read_only_allowed_tools: []`
- **THEN** the resolved allow-list is the application default (built-in + known MCP read-only tools)

#### Scenario: Custom allow-list when key is non-empty list

- **WHEN** the settings file sets `agent.read_only_allowed_tools` to a non-empty list of tool names (e.g. `["get_current_date", "current_period_costs", "session-sql"]`)
- **THEN** the resolved allow-list is exactly that set of names and is used by the read-only tool guardrail
