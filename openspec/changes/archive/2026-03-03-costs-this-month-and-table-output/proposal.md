# Proposal: Costs This Month and Table Output

## Why

Users need to see current-month AWS costs per service in a readable form from the CLI. This is the first cost visibility feature and depends on the foundation and AWS identity from Change 1. Delivering costs in a table format makes the CLI immediately useful for day-to-day FinOps use.

## What Changes

- **Current-month costs by service**: Fetch cost and usage data for the current calendar month, grouped by service (e.g. Cost Explorer–style), using the resolved AWS session (profile/identity from Change 1).
- **Table output**: Format the cost data as a readable table in the terminal (e.g. service name, cost amount, optional percentage).
- **CLI command**: Add a `finops costs` (or similar) command that prints the table; support `--profile` for account selection.

## Capabilities

### New Capabilities

- `costs-this-month`: Retrieve current calendar month costs grouped by service (e.g. AWS Cost Explorer API or equivalent); support for default metric (e.g. UnblendedCost) and date range (month-to-date).
- `costs-table-output`: Format cost data as a human-readable table (columns: service, cost, optionally % of total); suitable for terminal output.

### Modified Capabilities

- None.

## Impact

- **Codebase**: New module(s) for cost fetching (boto3 Cost Explorer or use of existing identity/session); table formatting (e.g. string alignment or a minimal table library); CLI subcommand.
- **Dependencies**: boto3 (already present); optional: a small table formatter or stdlib-only formatting.
- **AWS**: Read-only Cost Explorer GetCostAndUsage (or equivalent) API calls; cost per API request applies.
