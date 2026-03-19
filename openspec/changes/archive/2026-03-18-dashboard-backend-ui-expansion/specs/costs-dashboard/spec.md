# costs-dashboard Specification

## Purpose

Defines the full dashboard data: current-month cost retrieval in three breakdowns (by AWS service only, by linked account, by marketplace); cost optimization recommendations (top 10 by savings); cost anomalies (last 3 days); and Savings Plans utilization and coverage (1/2/3 months). Covers Cost Explorer, Cost Optimization Hub, and Cost Anomaly Detection APIs and the dashboard API payload. Used by the backend API and the hosted web UI dashboard.

## Requirements

### Requirement: Retrieve current-month costs by AWS service only

The system SHALL provide a function (or equivalent) that retrieves cost and usage data for the current calendar month grouped by AWS service, excluding AWS Marketplace. The system SHALL use the AWS Cost Explorer API (GetCostAndUsage) with a Filter on the BILLING_ENTITY dimension set to "AWS". The time range SHALL be the current month (first day through end of month); the metric SHALL be UnblendedCost. The result SHALL be a list of (service name, cost amount) sorted by cost descending.

#### Scenario: AWS-only costs returned for current month

- **WHEN** the function is called with a valid session and default (current) month
- **THEN** the system calls Cost Explorer with Filter BILLING_ENTITY = "AWS" and GroupBy SERVICE, and returns a list of service and cost pairs with no AWS Marketplace row

#### Scenario: Empty list when no AWS costs in period

- **WHEN** the function is called and Cost Explorer returns no groups for the filtered period
- **THEN** the system returns an empty list and does not raise

### Requirement: Retrieve current-month costs by linked account

The system SHALL provide a function that retrieves cost and usage data for the current calendar month grouped by linked account (LINKED_ACCOUNT dimension). The system SHALL use Cost Explorer GetCostAndUsage with GroupBy LINKED_ACCOUNT and the same time range and metric as other current-month cost functions. The result SHALL be a list of (account_id, cost amount) sorted by cost descending.

#### Scenario: By-account costs returned for current month

- **WHEN** the function is called with a valid session (e.g. payer account) and default month
- **THEN** the system calls Cost Explorer with GroupBy LINKED_ACCOUNT and returns a list of account ID and cost pairs

#### Scenario: Access denied for Cost Explorer

- **WHEN** the function is called and Cost Explorer returns AccessDeniedException (or equivalent)
- **THEN** the system raises a clear cost-explorer error and does not return partial data

### Requirement: Retrieve current-month costs for marketplace only

The system SHALL provide a function that retrieves cost and usage data for the current calendar month for AWS Marketplace only. The system SHALL use Cost Explorer with a Filter on BILLING_ENTITY set to "AWS Marketplace" and GroupBy SERVICE so that marketplace products appear as service names. The time range and metric SHALL match the other current-month cost functions. The result SHALL be a list of (product/service name, cost amount) sorted by cost descending. If there is no marketplace usage, the function SHALL return an empty list.

#### Scenario: Marketplace costs returned when present

- **WHEN** the function is called with a valid session and there is marketplace usage in the current month
- **THEN** the system calls Cost Explorer with Filter BILLING_ENTITY = "AWS Marketplace" and GroupBy SERVICE, and returns a list of product and cost pairs

#### Scenario: Empty list when no marketplace usage

- **WHEN** the function is called and there is no marketplace usage in the period
- **THEN** the system returns an empty list and does not raise

### Requirement: Cost optimization recommendations (top 10 by savings)

The system SHALL provide a function (or equivalent) that retrieves cost optimization recommendations from AWS Cost Optimization Hub. The system SHALL use the ListRecommendations API (or equivalent) and return the top 10 recommendations ordered by estimated savings opportunity (e.g. estimated monthly savings or impact). The result SHALL include at least recommendation identifier, resource type or action type, and estimated savings (or equivalent fields exposed by the API). If the API is not available or returns an error (e.g. access denied), the function SHALL return an empty list and SHALL NOT fail the caller.

#### Scenario: Top 10 recommendations returned when Cost Optimization Hub succeeds

- **WHEN** the function is called with a valid session and Cost Optimization Hub returns recommendations
- **THEN** the system returns up to 10 recommendations sorted by savings opportunity (e.g. estimated monthly savings descending)

#### Scenario: Empty list when Cost Optimization Hub unavailable or access denied

- **WHEN** the function is called and the Cost Optimization Hub API returns an error (e.g. access denied or service not enabled)
- **THEN** the system returns an empty list and does not raise

### Requirement: Cost anomalies (last 3 days)

The system SHALL provide a function that retrieves cost anomalies detected in the last 3 days. The system SHALL use the Cost Explorer GetAnomalies API (or equivalent) with a date interval covering the last 3 days. The result SHALL be a list of anomalies (e.g. anomaly ID, date range, impact, root cause or summary as exposed by the API). If the API is not available or returns an error (e.g. access denied or no anomaly monitors), the function SHALL return an empty list and SHALL NOT raise.

#### Scenario: Anomalies returned when GetAnomalies succeeds

- **WHEN** the function is called with a valid session and GetAnomalies returns one or more anomalies for the last 3 days
- **THEN** the system returns a list of anomaly entries with the appropriate fields (e.g. date range, impact)

#### Scenario: Empty list when no anomalies or API error

- **WHEN** the function is called and GetAnomalies returns no anomalies or an error (e.g. access denied)
- **THEN** the system returns an empty list and does not raise

### Requirement: Savings Plans utilization and coverage (selectable period)

The system SHALL provide a function that retrieves Savings Plans utilization and coverage for a given period of 1, 2, or 3 months. The system SHALL use Cost Explorer get_savings_plans_utilization and get_savings_plans_coverage (or equivalent) for the specified number of months (e.g. trailing months from today). The result SHALL include utilization and coverage metrics (e.g. utilization percentage, coverage percentage, totals as exposed by the API). If the account has no Savings Plans or the API returns an error, the function SHALL return a structure indicating no data or zero utilization/coverage and SHALL NOT raise so the dashboard can still render.

#### Scenario: Utilization and coverage returned for selected period

- **WHEN** the function is called with a valid session and a period of 1, 2, or 3 months and the account has Savings Plans data
- **THEN** the system returns utilization and coverage data for that period (e.g. utilization percentage, coverage percentage)

#### Scenario: No data or zero when no Savings Plans or API error

- **WHEN** the function is called and there are no Savings Plans or the Cost Explorer Savings Plans API returns an error
- **THEN** the system returns a safe default (e.g. zero utilization/coverage or empty structure) and does not raise

### Requirement: Dashboard payload structure

The system SHALL expose a dashboard payload that combines all dashboard data in one structure. The payload SHALL include: (1) by_service_aws_only: list of objects with service and cost; (2) by_account: list of objects with account_id and cost; (3) by_marketplace: list of objects with product (or service) and cost; (4) optimization_recommendations: list of up to 10 recommendation objects (e.g. id, resource_type, estimated_savings); (5) anomalies: list of anomaly objects for the last 3 days (e.g. id, date_interval, impact); (6) savings_plans: object with utilization and coverage for the requested period (e.g. utilization_percentage, coverage_percentage, period_months). When demo mode is active, account identifiers in by_account and in recommendations/anomalies SHALL be masked using the same rules as other demo-masked endpoints. The dashboard endpoint SHALL accept an optional parameter (e.g. savings_plans_months) with values 1, 2, or 3 to select the Savings Plans lookback period; default SHALL be 1.

#### Scenario: Dashboard payload contains all sections

- **WHEN** the dashboard is requested with a valid profile and all underlying APIs succeed (or return empty where applicable)
- **THEN** the response contains by_service_aws_only, by_account, by_marketplace, optimization_recommendations, anomalies, and savings_plans with the appropriate keys and types

#### Scenario: Dashboard masks account IDs in demo mode

- **WHEN** the dashboard is requested with X-Demo-Mode: true (or equivalent)
- **THEN** account_id values in by_account and any account identifiers in optimization_recommendations and anomalies are replaced with masked/fake identifiers consistent with other demo-mode responses

#### Scenario: Savings Plans period is selectable

- **WHEN** the dashboard is requested with savings_plans_months=2 (or equivalent query parameter)
- **THEN** the savings_plans object in the response reflects utilization and coverage for the last 2 months
