# savings-plans-purchase-recommendations — Delta

## ADDED Requirements

### Requirement: Full matrix of purchase recommendation queries

The system SHALL invoke AWS Cost Explorer **`GetSavingsPlansPurchaseRecommendation`** (or boto3 equivalent) for **each** combination of supported **`SavingsPlansType`**, **`TermInYears`**, and **`PaymentOption`** values required to cover **Compute**, **EC2 Instance**, and **SageMaker** Savings Plans types with **one-** and **three-year** terms and **all** payment options supported by the API (full matrix, typically 18 calls). The system SHALL use a single **`LookbackPeriodInDays`** (default **thirty days**) for all calls. The system SHALL **not** restrict results by **region** in the request when the API allows an unfiltered request, so recommendations are as complete as AWS returns for the account.

#### Scenario: Matrix covers all plan types and terms

- **WHEN** the backend aggregates purchase recommendations for the dashboard
- **THEN** the implementation SHALL query every supported `SavingsPlansType` × `TermInYears` × `PaymentOption` combination in the matrix, not a subset filtered by region

#### Scenario: Consistent lookback

- **WHEN** purchase recommendations are fetched
- **THEN** all matrix calls SHALL use the same lookback period (e.g. THIRTY_DAYS) unless documented otherwise

### Requirement: HTTP lazy slice for purchase recommendations

The system SHALL expose a **`GET`** path under **`/costs/dashboard/`** (documented in implementation) that returns JSON with a **list of normalized recommendation rows** (or empty list) and metadata (e.g. lookback period). The endpoint SHALL use the **same profile resolution and demo-mode behavior** as other **`/costs/dashboard/*`** lazy endpoints. On **permission denied** for Cost Explorer, the response SHALL be an error with a clear message consistent with other cost endpoints.

#### Scenario: Successful response

- **WHEN** a client requests the purchase-recommendations slice with a valid profile and Cost Explorer returns data for at least one matrix cell
- **THEN** the response status is **200** and the body includes recommendation entries suitable for tabular display

#### Scenario: Access denied

- **WHEN** Cost Explorer denies `GetSavingsPlansPurchaseRecommendation`
- **THEN** the response is an error status with a message the UI can display

### Requirement: Partial results when some matrix calls fail

If individual matrix calls fail with **non-fatal** errors (e.g. throttling, empty recommendation for that cell), the system SHALL either include successful rows only and surface optional error detail, or document a single failure mode—**at minimum** the API SHALL not crash and SHALL return **200** with available rows when at least one cell succeeds, unless a global permission error applies.

#### Scenario: One cell fails others succeed

- **WHEN** some matrix calls fail and others return recommendations
- **THEN** the successful recommendations are still returned and the client can render them

### Requirement: Costs dashboard UI shows purchase recommendations below by-cost-categories

The hosted web UI **costs dashboard** SHALL include a **Savings Plans purchase recommendations** (or equivalently named) section **below** the **By cost categories** section. The section SHALL load data from the lazy endpoint, support a **collapsible** header consistent with adjacent sections, and show **loading**, **empty**, and **error** states. The section SHALL display **tabular** data with at least the key financial metrics available from the API (e.g. savings amounts, commitment, utilization, ROI where present).

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
