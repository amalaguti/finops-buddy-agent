# Proposal: AWS Pricing MCP Server integration

## Why

PROJECT_CONTEXT.md calls out the **AWS Pricing MCP Server** ([awslabs.aws-pricing-mcp-server](https://github.com/awslabs/mcp/tree/main/src/aws-pricing-mcp-server)) for bulk pricing, project scan, and architecture patterns. The agent currently has Knowledge, Billing/Cost Management, Documentation, and Cost Explorer MCPs; adding the Pricing MCP gives the FinOps assistant real-time AWS pricing discovery, cost reports, multi-region comparisons, and optional CDK/Terraform project analysis—complementing cost data with list-price and planning capabilities.

## What Changes

- Add support for the **AWS Pricing MCP Server** ([awslabs/mcp aws-pricing-mcp-server](https://github.com/awslabs/mcp/tree/main/src/aws-pricing-mcp-server)), run locally via `uvx` (same pattern as Billing, Documentation, Cost Explorer MCP).
- **Default: disabled.** New settings and env vars SHALL default to off so the server is not started unless explicitly enabled.
- Settings: add `agent.pricing_mcp_enabled` (default false) and optional `agent.pricing_mcp_command`; env: `FINOPS_MCP_PRICING_ENABLED`, `FINOPS_MCP_PRICING_COMMAND`.
- Wire the Pricing MCP client into the agent builder and chat loop when enabled: stdio transport, pass AWS profile/region from session (Pricing API uses `pricing:*` and benefits from region for endpoint locality).
- Update `config/settings.yaml` template and README with the new options; document that the server provides real-time pricing, cost reports, and optional project/architecture analysis.

## Capabilities

### New Capabilities

- **mcp-aws-pricing**: Optional integration with the AWS Pricing MCP server. When enabled via settings/env, the agent can use Pricing MCP tools (e.g. service catalog exploration, pricing attribute discovery, real-time pricing queries, multi-region comparisons, cost report generation, CDK/Terraform project scan, cost optimization recommendations). Default is disabled; YAML and env use the same pattern as other stdio MCPs (enabled flag + optional command).

### Modified Capabilities

- **app-settings**: Add resolution for Pricing MCP: `agent.pricing_mcp_enabled` (default false), `agent.pricing_mcp_command` (optional), and env vars `FINOPS_MCP_PRICING_ENABLED`, `FINOPS_MCP_PRICING_COMMAND`. Same precedence as existing MCP settings (env overrides file).

## Impact

- **Code**: `src/finops_agent/settings.py` (new getters and caches), `src/finops_agent/agent/runner.py` (create_pricing_mcp_client, wire into build_agent and run_chat_loop; include in MCP status/tooling).
- **Config**: `config/settings.yaml` template gains commented Pricing MCP block.
- **Docs**: README Configuration section documents the new env vars and YAML keys; note that Pricing MCP is optional and disabled by default, and requires IAM `pricing:*` and optional AWS credentials.
- **Tests**: New/updated tests in `tests/test_settings.py`, `tests/test_agent.py`, and any chat CLI tests that assert MCP listing.
