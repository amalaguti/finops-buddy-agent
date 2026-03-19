# costs-this-month Specification

## Purpose
TBD - created by archiving change costs-this-month-and-table-output. Update Purpose after archive.
## Requirements
### Requirement: Fetch current month costs by service

The system SHALL retrieve cost and usage data for the current calendar month, grouped by AWS service. The system SHALL use the AWS Cost Explorer API (GetCostAndUsage or equivalent) with the resolved session (from Change 1). The time range SHALL be from the first day of the current month to the current date (or yesterday if the API does not yet include today). The default metric SHALL be UnblendedCost.

#### Scenario: Costs retrieved for default profile

- **WHEN** the user requests current-month costs and no profile is specified (or default profile is used)
- **THEN** the system uses the default credential chain to create a session and calls Cost Explorer for the current month, grouped by service

#### Scenario: Costs retrieved for named profile

- **WHEN** the user requests current-month costs with a specific profile (e.g. `--profile my-account`)
- **THEN** the system uses that profile’s session and calls Cost Explorer for the current month, grouped by service

### Requirement: Return structured cost data

The system SHALL return a list of (service name, cost amount) (or equivalent structure) for use by the CLI. Amounts SHALL be in the account’s currency (e.g. USD). The system SHALL handle API errors (e.g. AccessDenied, no Cost Explorer data) and surface a clear error to the user.

#### Scenario: Success returns list of services and costs

- **WHEN** the Cost Explorer call succeeds
- **THEN** the system returns a list of service names and corresponding cost values for the period

#### Scenario: Access denied or disabled Cost Explorer

- **WHEN** the Cost Explorer API returns an error (e.g. AccessDenied or subscription not enabled)
- **THEN** the system does not crash and reports an understandable error to the user

