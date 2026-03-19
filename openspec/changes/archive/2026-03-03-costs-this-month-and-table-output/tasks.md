# Tasks: Costs This Month and Table Output

## 1. Cost retrieval

- [x] 1.1 Implement current-month date range (first day of month to today or yesterday)
- [x] 1.2 Implement Cost Explorer GetCostAndUsage call: GROUP_BY SERVICE, metric UnblendedCost, use session from identity module
- [x] 1.3 Parse response into list of (service name, cost amount); handle pagination if needed
- [x] 1.4 Handle API errors (AccessDenied, no data) with clear user-facing messages

## 2. Table formatting

- [x] 2.1 Implement table formatter: columns Service and Cost (and optional % of total); aligned, terminal-friendly
- [x] 2.2 Accept list of (service, amount) and optional total for percentage; output formatted string or lines

## 3. CLI integration

- [x] 3.1 Add `costs` subcommand to CLI; accept `--profile` (reuse existing pattern)
- [x] 3.2 Wire costs module to table formatter and print result to stdout
