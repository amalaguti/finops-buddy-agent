# MCP Billing and Cost Management — Design

## Context

The FinOps CLI has a Strands-based chat agent with in-process cost tools (current period, date range, MoM, WoW, biweekly) that call Cost Explorer via boto3. The agent cannot query by LINKED_ACCOUNT or Marketplace (PURCHASE_TYPE) because those are not implemented in our tools. AWS provides MCP servers for Billing and Cost Management and for Cost Explorer; they expose Cost Explorer and Billing capabilities as MCP tools. **Reference:** [AWS Billing and Cost Management MCP server](https://github.com/awslabs/mcp/tree/main/src/billing-cost-management-mcp-server) (uv/Docker, tools, permissions). Strands Agents supports MCP (model context protocol) for loading tools from MCP servers. We need to run these servers locally and attach them to the agent.

Constraints: FINOPS_ prefix for all new env vars; read-only AWS; CLI-only for this change.

## Goals / Non-Goals

**Goals:**

- Run the AWS Billing and Cost Management MCP server and the Cost Explorer MCP server locally via **uv/uvx** (local process, stdio); Docker is an optional alternative per AWS documentation.
- Connect these MCP servers to the Strands chat agent so the agent can call their tools (e.g. costs by linked account, marketplace costs).
- Make MCP optional via configuration (e.g. enabled only when user opts in or when local servers are configured).

**Non-Goals:**

- Implementing other AWS MCP servers (documentation, pricing, etc.) in this change; focus on billing and cost-explorer only.
- Changing the existing in-process cost tools; they remain as-is.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Which MCP servers** | Billing and Cost Management + Cost Explorer — [billing-cost-management-mcp-server](https://github.com/awslabs/mcp/tree/main/src/billing-cost-management-mcp-server) | They provide linked-account and marketplace-style queries; directly address the gap. |
| **Run locally** | Use **uv/uvx** to run the server as a local process (stdio); Docker optional per AWS MCP docs | uvx is simpler for the project (no Docker in the loop); credentials and traffic stay local. |
| **Strands MCP** | Use Strands' MCP client support to attach server tools to the agent | Strands already supports MCP; we configure the agent with both in-process tools and MCP-sourced tools. |
| **Config** | Optional FINOPS_MCP_* env or settings (e.g. enable, server URL/command) | Allows users to enable MCP only when they have the servers running; no breaking default. |

**Alternatives considered:**

- Adding our own tools for LINKED_ACCOUNT and Marketplace: would work but duplicates what the MCP servers already provide and requires maintaining more Cost Explorer API surface.
- Remote MCP servers: rejected for this change; local keeps control and credentials on the user's side.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| MCP server startup/availability | Document that user must have uv installed and start servers via uvx (or Docker) before chat; CLI may optionally spawn uvx when MCP is enabled; agent falls back to in-process tools if MCP is unavailable. |
| Credentials for MCP servers | MCP servers typically use the same AWS credentials (env or profile); document profile/credential flow. |
| Strands MCP API | Follow Strands docs for attaching MCP servers; if API differs, adjust in implementation. |

## Migration Plan

- Add configuration and MCP wiring; existing chat flow unchanged when MCP is disabled. Rollback: disable MCP config or remove MCP client code.

## Open Questions

- Exact Strands API for registering MCP server tools (command-based/stdio for uvx).
- Whether both servers (Billing and Cost Management + Cost Explorer) are run as one process or two; see [billing-cost-management-mcp-server](https://github.com/awslabs/mcp/tree/main/src/billing-cost-management-mcp-server) during implementation.
