# savings-plans-purchase-recommendations Specification

## Purpose

Hosted costs dashboard support for **AWS Savings Plans purchase recommendations** via `GetSavingsPlansPurchaseRecommendation`: run the full parameter matrix (all supported Savings Plans types—including Compute, EC2 Instance, SageMaker, and Database where the API exposes them—× term × payment option), **payer** scope, **no region filter**, lazy HTTP slice, and UI below **By cost categories**.

## Requirements

### Requirement: Full matrix of purchase recommendation queries

The system SHALL invoke AWS Cost Explorer **`GetSavingsPlansPurchaseRecommendation`** (or boto3 equivalent) for **each** combination of supported **`SavingsPlansType`**, **`TermInYears`**, and **`PaymentOption`** values (full matrix: all types the implementation supports × one- and three-year terms × NO_UPFRONT / PARTIAL_UPFRONT / ALL_UPFRONT—typically on the order of **twenty-four** calls when four plan types are supported). The system SHALL use a single **`LookbackPeriodInDays`** (default **thirty days**) for all calls. The system SHALL **not** restrict results by **region** in the request when the API allows an unfiltered request, so recommendations are as complete as AWS returns for the account. The system SHALL use **`AccountScope` `PAYER`** when querying from the management account context so recommendations are not limited to a single linked account.

#### Scenario: Matrix covers all plan types and terms

- **WHEN** the backend aggregates purchase recommendations for the dashboard
- **THEN** the implementation SHALL query every supported `SavingsPlansType` × `TermInYears` × `PaymentOption` combination in the matrix, not a subset filtered by region

#### Scenario: Consistent lookback

- **WHEN** purchase recommendations are fetched
- **THEN** all matrix calls SHALL use the same lookback period (e.g. THIRTY_DAYS) unless documented otherwise

### Requirement: HTTP lazy slice for purchase recommendations

The system SHALL expose **`GET /costs/dashboard/savings-plans-purchase-recommendations`** with JSON containing **`lookback_period_in_days`**, **`recommendations`** (list of rows), and optionally **`errors`** for per-cell failures. The endpoint SHALL use the **same profile resolution and demo-mode behavior** as other **`/costs/dashboard/*`** lazy endpoints. On **permission denied** for Cost Explorer for **all** matrix calls, the response SHALL be an error with a clear message consistent with other cost endpoints.

#### Scenario: Successful response

- **WHEN** a client requests the purchase-recommendations slice with a valid profile and Cost Explorer returns data for at least one matrix cell
- **THEN** the response status is **200** and the body includes recommendation entries suitable for tabular display

#### Scenario: Access denied

- **WHEN** Cost Explorer denies `GetSavingsPlansPurchaseRecommendation` for every matrix cell
- **THEN** the response is an error status with a message the UI can display

### Requirement: Partial results when some matrix calls fail

If individual matrix calls fail with **non-fatal** errors (e.g. throttling), the system SHALL return **200** with **`recommendations`** built from successful cells and **`errors`** listing failed parameter combinations when applicable.

#### Scenario: One cell fails others succeed

- **WHEN** some matrix calls fail and others return recommendations
- **THEN** the successful recommendations are still returned and the client can render them

### Requirement: Costs dashboard UI shows purchase recommendations below by-cost-categories

The hosted web UI **costs dashboard** SHALL include a **Savings Plans purchase recommendations** section **below** the **By cost categories** section. The section SHALL load data from the lazy endpoint, support a **collapsible** header consistent with adjacent sections, and show **loading**, **empty**, and **error** states. The section SHALL display **tabular** data with key financial metrics from the API (e.g. savings amounts, commitment, ROI).

#### Scenario: Panel placement

- **WHEN** a user views the costs dashboard with a valid profile
- **THEN** the purchase recommendations panel appears **after** the by-cost-categories block in the layout order

#### Scenario: Collapsible section

- **WHEN** the purchase recommendations block is rendered
- **THEN** the user can expand or collapse it with a control consistent with other collapsible dashboard sections

### Requirement: Demo mode masks sensitive strings

When **demo mode** is active (`X-Demo-Mode: true`), the backend SHALL apply the same **identifier masking** approach as other dashboard cost payloads to **string fields** in the purchase-recommendation response that may contain account or resource identifiers.

#### Scenario: Demo header triggers masking

- **WHEN** a request includes demo mode and the response includes recommendation strings
- **THEN** those strings SHALL be masked according to the demo transformation rules used elsewhere for the dashboard
