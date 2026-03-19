# hosted-web-ui (delta)

## ADDED Requirements

### Requirement: Dashboard layout with cost, optimization, anomalies, and savings plans sections

The hosted web UI SHALL include a dashboard-style block that displays six sections: (1) current-month costs by AWS service only, (2) by linked account, (3) by marketplace only, (4) cost optimization recommendations (top 10 by savings opportunity), (5) cost anomalies detected in the last 3 days, and (6) Savings Plans utilization and coverage. The data SHALL be loaded from the costs dashboard API (e.g. GET /costs/dashboard or equivalent) using the selected profile. The UI SHALL show a loading state while the dashboard data is being fetched and an error state when the request fails. When a section has no data, the UI SHALL show an explicit empty state (e.g. "No recommendations", "No anomalies in the last 3 days", "No Savings Plans data") rather than an empty table or blank area. The layout SHALL accommodate all sections (e.g. in the sidebar or a dedicated dashboard area) using compact tables, cards, or collapsible sections so the dashboard remains usable.

#### Scenario: Dashboard displays all six sections when data loads

- **WHEN** the user has a profile selected and the dashboard API returns successfully with all sections (cost breakdowns, optimization_recommendations, anomalies, savings_plans)
- **THEN** the UI displays six sections: costs by AWS service, by account, by marketplace, optimization recommendations (top 10), anomalies (last 3 days), and Savings Plans utilization/coverage

#### Scenario: Dashboard shows loading state while fetching

- **WHEN** the user selects a profile and the dashboard data request is in progress
- **THEN** the dashboard block shows a loading indicator (or equivalent) until the response is received

#### Scenario: Dashboard shows error state when request fails

- **WHEN** the dashboard API request fails (e.g. network error or 4xx/5xx for the core endpoint)
- **THEN** the UI displays an error state with a clear message and does not show stale or partial data

#### Scenario: Empty sections show explicit empty message

- **WHEN** the dashboard API returns successfully but a section has no data (e.g. by_account empty, optimization_recommendations empty, anomalies empty)
- **THEN** the corresponding section displays an explicit empty-state message (e.g. "No linked account data", "No optimization recommendations", "No anomalies in the last 3 days") instead of an empty table with no explanation

### Requirement: Savings Plans period picker

The hosted web UI SHALL provide a way for the user to select the Savings Plans report period: 1, 2, or 3 months. When the user changes the selected period, the UI SHALL request the dashboard data again with the corresponding parameter (e.g. savings_plans_months=1, 2, or 3) and SHALL update the Savings Plans section with the new utilization and coverage data.

#### Scenario: User can select 1, 2, or 3 months for Savings Plans

- **WHEN** the user opens the dashboard and the Savings Plans section is visible
- **THEN** the UI shows a control (e.g. dropdown or tabs) to select 1 month, 2 months, or 3 months

#### Scenario: Changing period refetches and updates Savings Plans data

- **WHEN** the user changes the Savings Plans period from 1 month to 3 months
- **THEN** the frontend requests the dashboard (or a Savings Plans–specific endpoint) with savings_plans_months=3 and updates the Savings Plans section with the new utilization and coverage for the last 3 months
