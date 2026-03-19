# backend-api (delta)

## ADDED Requirements

### Requirement: HTTP API returns costs dashboard

The system SHALL expose an HTTP endpoint that returns the full costs dashboard for a given or default profile. The profile SHALL be specified via the same optional query parameter or header as the existing costs endpoint (e.g. `profile` or `X-AWS-Profile`). The response body SHALL contain: by_service_aws_only (list of objects with service and cost), by_account (list of objects with account_id and cost), by_marketplace (list of objects with product and cost), optimization_recommendations (list of up to 10 recommendation objects, e.g. id, resource_type, estimated_savings), anomalies (list of anomaly objects for the last 3 days, e.g. id, date_interval, impact), and savings_plans (object with utilization and coverage for the requested period, e.g. utilization_percentage, coverage_percentage, period_months). The endpoint SHALL accept an optional query parameter (e.g. savings_plans_months) with values 1, 2, or 3; default SHALL be 1. When the request includes the demo-mode header (e.g. X-Demo-Mode: true), account identifiers in by_account and in optimization_recommendations and anomalies SHALL be masked. The endpoint SHALL use the same profile resolution and error handling patterns as GET /costs (e.g. 400 when no profile, 403 on Cost Explorer access denied for core cost data). If Cost Optimization Hub, GetAnomalies, or Savings Plans APIs fail (e.g. access denied), the endpoint SHALL still return 200 with empty or default values for those sections rather than failing the entire response.

#### Scenario: GET costs dashboard returns all sections for profile

- **WHEN** a client sends a GET request to the costs dashboard endpoint with a valid profile (or default)
- **THEN** the response status is 200 and the body contains by_service_aws_only, by_account, by_marketplace, optimization_recommendations, anomalies, and savings_plans with the appropriate structure

#### Scenario: GET costs dashboard respects savings_plans_months parameter

- **WHEN** a client sends a GET request to the costs dashboard endpoint with savings_plans_months=3 (or equivalent)
- **THEN** the response status is 200 and savings_plans reflects utilization and coverage for the last 3 months

#### Scenario: GET costs dashboard fails when no profile

- **WHEN** a client sends a GET request to the costs dashboard endpoint without a profile and no default profile is available
- **THEN** the response status is 400 (or equivalent) and the body includes a clear message that a profile is required

#### Scenario: GET costs dashboard fails when Cost Explorer access denied for core costs

- **WHEN** a client sends a GET request to the costs dashboard endpoint and the resolved session does not have Cost Explorer permissions for GetCostAndUsage (or the API returns an error)
- **THEN** the response status is an error (4xx or 5xx) and the body includes a clear error message

#### Scenario: GET costs dashboard masks account IDs in demo mode

- **WHEN** a client sends a GET request to the costs dashboard endpoint with X-Demo-Mode: true and the response includes by_account or recommendation/anomaly entries with account identifiers
- **THEN** those account_id values are masked (e.g. replaced with fake IDs) consistent with other demo-mode masking

#### Scenario: GET costs dashboard returns partial data when optional APIs fail

- **WHEN** a client sends a GET request to the costs dashboard endpoint and Cost Optimization Hub or GetAnomalies returns access denied (or similar)
- **THEN** the response status is 200 and optimization_recommendations or anomalies is an empty list (or savings_plans has default/zero values if that API fails); core cost breakdowns are still present
