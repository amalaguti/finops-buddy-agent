# Design: AWS Pricing MCP Server integration

## Context

The chat agent already integrates optional MCP servers: Knowledge (remote), Billing/Cost Management (local uvx), Documentation (local uvx), and Cost Explorer (local uvx). Each is controlled by settings (`agent.<name>_mcp_enabled`, `agent.<name>_mcp_command`) and env vars (`FINOPS_MCP_*_ENABLED`, `FINOPS_MCP_*_COMMAND`). The **AWS Pricing MCP Server** ([awslabs.aws-pricing-mcp-server](https://github.com/awslabs/mcp/tree/main/src/aws-pricing-mcp-server)) provides real-time AWS Pricing API access: service catalog exploration, pricing attribute discovery, real-time pricing queries, multi-region comparisons, cost report generation, CDK/Terraform project scan, and cost optimization recommendations. It runs via stdio (e.g. `uvx awslabs.aws-pricing-mcp-server@latest`), uses env vars such as `AWS_PROFILE`, `AWS_REGION`, and `FASTMCP_LOG_LEVEL`, and requires IAM `pricing:*` permissions. PROJECT_CONTEXT lists it for bulk pricing, project scan, and architecture patterns. This change adds it as an optional, **disabled-by-default** integration following the same pattern as Documentation and Cost Explorer MCP.

## Goals / Non-Goals

**Goals:**

- Add AWS Pricing MCP server as an optional tool source, disabled by default.
- Reuse the same configuration and runtime pattern as Billing, Documentation, and Cost Explorer MCP (YAML + env, stdio transport via uvx, session env for AWS profile/region).
- Expose the new server in `/tooling` and `/status` when enabled.
- Document the new settings and that IAM `pricing:*` (and optionally AWS credentials) are required when enabled.

**Non-Goals:**

- Changing default behavior for existing MCPs or in-process cost tools.
- Supporting a different transport (e.g. remote URL) for Pricing MCP in this change.
- Implementing Pricing MCP–specific user notifications (e.g. "Consulted AWS Pricing") in this change; can be added later if desired.

## Decisions

1. **Default: disabled.** Pricing MCP SHALL default to off (`pricing_mcp_enabled` false, `FINOPS_MCP_PRICING_ENABLED` not set → false). Rationale: Avoid extra subprocess and uvx dependency unless the user opts in; consistent with other optional stdio MCPs; Pricing API calls are free but still require IAM and optional credentials.

2. **Same pattern as Documentation/Cost Explorer.** Use `get_pricing_mcp_enabled()` and `get_pricing_mcp_command()` in settings; `create_pricing_mcp_client(session)` in runner; append client to tools when enabled; pass session env (AWS_PROFILE, AWS_REGION) into the subprocess. Rationale: Consistency and minimal new concepts; reuse of platform-specific uvx defaults (e.g. Windows `--from` + `.exe` as used for other awslabs MCP servers).

3. **Default command.** Default uvx package: `awslabs.aws-pricing-mcp-server@latest`. Command parsing via `shlex.split` and same Windows vs non-Windows handling as Documentation/Billing/Cost Explorer. Rationale: Package name is `awslabs.aws-pricing-mcp-server`; uvx follows the same pattern as other awslabs MCP servers.

4. **Display name.** Use a single display name for tool attribution and status (e.g. "AWS Pricing MCP Server"). Rationale: Matches how other MCPs are presented in `/tooling` and `/status`.

5. **No tool-name mapping in callback.** If Pricing MCP tools use a distinct prefix or naming, we can add a small mapping in `_mcp_server_name_for_tool` (or equivalent) later; otherwise rely on the existing `_finops_mcp_server_name` attribute on the client. Rationale: Implement once we see actual tool names; optional polish.

## Risks / Trade-offs

- **Extra process when enabled:** One more subprocess when enabled. Mitigation: Same as other stdio MCPs; no change to behavior when disabled.
- **Package/version:** We depend on `awslabs.aws-pricing-mcp-server` from PyPI/uvx. Mitigation: Document `@latest`; same approach as Billing/Documentation/Cost Explorer.
- **IAM and credentials:** Pricing MCP needs `pricing:*` and benefits from AWS_PROFILE/AWS_REGION. Mitigation: Document in README and settings template; agent already passes session env to other stdio MCPs.

## Migration Plan

- No data migration. Add new settings and code paths; existing configs unchanged.
- Rollback: Remove Pricing MCP wiring and settings; no persisted state to migrate back.

## Open Questions

- None. Tool-name-to-server display mapping can be refined after implementation if the Pricing MCP uses a specific naming convention.
