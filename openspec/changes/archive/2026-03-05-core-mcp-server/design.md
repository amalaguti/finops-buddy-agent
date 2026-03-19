# Design: Core MCP Server integration

## Context

The FinOps agent today attaches multiple MCP clients individually: Knowledge (remote HTTP), Billing/BCM, Documentation, Cost Explorer, and Pricing (local stdio via uvx). Each has its own enable flag and command in settings and env. The [AWS Core MCP Server](https://github.com/awslabs/mcp/tree/main/src/core-mcp-server) runs as a single stdio process and proxies other MCP servers based on role environment variables (e.g. `finops`, `aws-foundation`, `solutions-architect`). This change adds Core MCP as an optional client. When enabled with roles finops, aws-foundation, and solutions-architect, Core provides cost, knowledge/docs, and solution-architecture tooling in one process. To avoid duplicate tools, when Core is enabled the agent must not attach the standalone Billing, Cost Explorer, or Pricing MCP clients, and built-in cost tools must be disabled (same as when Billing MCP is enabled). Users see which MCP servers are loaded via Core in `/tooling` and `/status` by showing the Core MCP Server and its configured roles.

## Goals / Non-Goals

**Goals:**

- Add Core MCP Server as an optional stdio MCP client with enable/disable and configurable roles (default or recommended: finops, aws-foundation, solutions-architect).
- Resolve Core MCP settings (enabled, command, roles) from YAML and FINOPS_* env vars; document in README and config template.
- When Core MCP is enabled: attach only the Core client for cost/pricing/knowledge/docs (no standalone Billing, Cost Explorer, or Pricing clients); disable built-in cost tools.
- Expose Core MCP and its configured roles in `/tooling` and `/status` so users can see which proxied servers are loaded.
- Preserve existing behavior when Core is disabled; no breaking changes to current MCP or settings.

**Non-Goals:**

- Changing how the remote Knowledge MCP or Documentation MCP work when used standalone (they remain separate options; Core’s aws-foundation role may duplicate knowledge/docs via proxied servers—user choice).
- Implementing Core MCP server itself (we consume it as an external process).
- Supporting partial role enablement at runtime inside Core (we pass a fixed role set per session; Core’s docs allow multiple roles via env).

## Decisions

### 1. Single Core client with role list in env

**Decision:** Run one Core MCP process per chat session; pass roles as environment variables into the Core subprocess (e.g. `finops=true`, `aws-foundation=true`, `solutions-architect=true`). Core’s README documents role env vars (lowercase with hyphens or uppercase with underscores).

**Rationale:** Core is designed to be configured via env; no need for a separate config file. The app already passes AWS_PROFILE and AWS_REGION into stdio MCPs; we add Core-specific role env vars to the same env dict.

**Alternatives:** (A) One env var with comma-separated roles—parsed and expanded into multiple env vars for Core. (B) Fixed roles in code—rejected so users can tune roles without code change.

### 2. Mutual exclusion: Core vs Billing, Cost Explorer, Pricing

**Decision:** When Core MCP is enabled, the agent builder does not create or attach the Billing, Cost Explorer, or Pricing MCP clients. Built-in cost tools are not included when Core is enabled (same logic as when Billing MCP is enabled: `include_cost_tools = (billing_client is None)`, extended to `include_cost_tools = (billing_client is None and core_client is None)` or equivalent).

**Rationale:** Core’s finops role includes cost-explorer-server, pricing-server, billing-cost-management-server; attaching them again would duplicate tools and confuse the agent.

**Alternatives:** (A) Allow both and rely on tool names—would duplicate tools. (B) Warn and skip standalone only if roles include finops—adds complexity; simpler to skip whenever Core is enabled.

### 3. Role list format in settings and env

**Decision:** Store roles as a list of strings in YAML (e.g. `agent.core_mcp_roles: [finops, aws-foundation, solutions-architect]`) and as a comma-separated string in env (e.g. `FINOPS_MCP_CORE_ROLES=finops,aws-foundation,solutions-architect`). When building the Core subprocess env, set each role to `true` (e.g. `finops=true`, `aws-foundation=true`). Default when unset: use a default list (finops, aws-foundation, solutions-architect) so the proposal’s “default roles” are applied without user config.

**Rationale:** Comma-separated env is easy to override; YAML list is clear and consistent with other list settings. Core accepts both hyphenated and underscored names; we use the canonical names from Core’s README (e.g. `finops`, `aws-foundation`, `solutions-architect`).

### 4. /tooling and /status: show Core and roles

**Decision:** Treat the Core MCP client as a single MCP server for display. Set `_finops_mcp_server_name` on the Core client to a string that includes the configured roles, e.g. `"Core MCP Server (roles: finops, aws-foundation, solutions-architect)"`. Optionally attach a small attribute (e.g. `_finops_mcp_core_roles`) with the list of roles so /tooling and /status can format “which MCP servers are loaded due to Core” (e.g. by mapping roles to known proxied server names from Core’s README). /status already probes each MCP client and shows name + readiness; the same logic will show “Core MCP Server (roles: …): ready (N tools)”.

**Rationale:** Users asked that /tooling and /status indicate which MCP servers are loaded due to Core roles; a single display name with roles is minimal and clear. Optional role-to-proxied-server mapping can be a short list in code (e.g. finops → cost-explorer, pricing, cloudwatch, billing-cost-management; aws-foundation → aws-knowledge, aws-api; solutions-architect → diagram, pricing, cost-explorer, syntheticdata, aws-knowledge) for a richer line in /tooling if desired.

### 5. Command and package for Core MCP

**Decision:** Default command: `uvx awslabs.core-mcp-server@latest` with platform-specific handling (e.g. Windows may use `uv tool run --from awslabs.core-mcp-server@latest awslabs.core-mcp-server.exe` as in Core’s README). Overridable via `agent.core_mcp_command` in YAML and `FINOPS_MCP_CORE_COMMAND` in env (parsed with shlex into command + args), consistent with Billing/Documentation/Cost Explorer/Pricing.

**Rationale:** Same pattern as other stdio MCPs; no new package manager; uv/uvx is already required for existing MCPs.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-------------|
| Core requires Bedrock for `prompt_understanding` | Document in README; if user runs with OpenAI-only and Core enabled, Core may still expose proxied tools; prompt_understanding may fail—acceptable as doc’d limitation. |
| Role names or env format change in Core | Pin or document Core package version in README; if Core changes env semantics, we update env construction in one place. |
| Duplicate tools if user enables both Core and standalone Billing | We skip Billing/Cost Explorer/Pricing when Core is enabled; no duplicate. |
| /status timeout when Core loads many proxied servers | Reuse existing MCP probe timeout (e.g. 15s); Core startup may be slower—document that first run (uvx install) can take longer. |

## Migration Plan

- No migration of existing config: Core is opt-in. Users who want Core add `agent.core_mcp_enabled: true` and `agent.core_mcp_roles` (or env) and set `FINOPS_MCP_BILLING_ENABLED=false`, `FINOPS_MCP_PRICING_ENABLED=false` (and leave Cost Explorer disabled) when using Core.
- Rollback: Disable Core MCP and re-enable standalone Billing/Pricing/Cost Explorer as before; no data or schema change.

## Open Questions

- None blocking. Optional enhancement: in /tooling, show a short “Proxied servers (from roles): …” line for Core using the role-to-server mapping from Core’s README; can be added in implementation if time permits.
