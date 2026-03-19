# mcp-billing-cost Specification

## Purpose

Define how the FinOps chat agent gains access to AWS Billing and Cost Management and Cost Explorer MCP server tools when those servers are run locally, enabling queries such as costs by linked account and marketplace costs.

## Requirements

### Requirement: Local MCP servers for billing and cost

The system SHALL support running the AWS Billing and Cost Management MCP server and the Cost Explorer MCP server locally (e.g. via Docker or local process as documented at [awslabs.github.io/mcp](https://awslabs.github.io/mcp)). The system SHALL document how to start and configure these servers so they are reachable by the FinOps agent.

#### Scenario: Documentation describes how to run MCP servers locally

- **WHEN** a user reads the project documentation for MCP
- **THEN** they find instructions or references for running the Billing and Cost Management and Cost Explorer MCP servers locally (e.g. Docker command or process)

### Requirement: Agent has access to MCP tools when MCP is enabled

When MCP is enabled and the local MCP servers are available, the Strands chat agent SHALL have access to the tools exposed by those servers (e.g. cost by linked account, marketplace costs, cost optimization) in addition to the existing in-process cost tools. The agent SHALL be able to invoke these tools during a chat session to answer user questions.

#### Scenario: Agent can use MCP tools when configured and servers are up

- **WHEN** MCP is enabled in configuration and the Billing/Cost Explorer MCP servers are running and reachable
- **THEN** the agent is built with both in-process tools and MCP server tools, and can answer queries that require linked-account or marketplace cost data

#### Scenario: Agent works without MCP when MCP is disabled or unavailable

- **WHEN** MCP is disabled or the MCP servers are not reachable
- **THEN** the agent still starts and works with the existing in-process cost tools only; no failure or crash

### Requirement: MCP configuration

The system SHALL provide optional configuration to enable or disable MCP and to point to the local MCP server(s). Any new environment variables SHALL use the FINOPS_ prefix. Configuration SHALL be documented in README and, if applicable, reflected in config/settings.yaml.

#### Scenario: MCP can be enabled via configuration

- **WHEN** the user sets the appropriate FINOPS_ configuration (e.g. FINOPS_MCP_BILLING_ENABLED or equivalent)
- **THEN** the agent attempts to connect to and use the configured MCP server(s) when starting the chat session

#### Scenario: Default behavior without MCP config

- **WHEN** no MCP-related configuration is set
- **THEN** the agent runs with in-process tools only (current behavior); MCP is not required for chat to work
