# Spec: Costs Table Output

## ADDED Requirements

### Requirement: Format costs as a readable table

The system SHALL format a list of (service name, cost amount) as a human-readable table suitable for terminal output. The table SHALL include at least: service name (or “Service”) and cost amount (e.g. “Cost” or “Amount”). The system MAY include an optional column for percentage of total cost. Column headers SHALL be clear and aligned with the data.

#### Scenario: Table has headers and aligned columns

- **WHEN** the user requests cost output in table form
- **THEN** the output shows a header row and one row per service with aligned columns (e.g. service name, cost)

#### Scenario: Optional percentage column

- **WHEN** the implementation supports a percentage-of-total column and it is enabled
- **THEN** each row shows the service’s share of total cost as a percentage

### Requirement: CLI prints the table

The CLI SHALL provide a command (e.g. `finops costs`) that fetches current-month costs by service and prints them in the table format. The command SHALL accept the same profile selection as other commands (e.g. `--profile`).

#### Scenario: User runs costs command

- **WHEN** the user runs the costs command (e.g. `finops costs`)
- **THEN** the CLI fetches current-month costs by service and prints the table to stdout

#### Scenario: User specifies profile for costs

- **WHEN** the user runs the costs command with `--profile <name>`
- **THEN** the CLI uses that profile for the Cost Explorer call and prints the table for that account
