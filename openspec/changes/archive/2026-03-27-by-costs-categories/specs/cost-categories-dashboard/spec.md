# cost-categories-dashboard — Delta

## ADDED Requirements

### Requirement: Cost Explorer discovers cost category names

The system SHALL call AWS Cost Explorer to list **cost category** names available for the account context (e.g. **`GetCostCategories`**) using the **same month-to-date date range** as the existing dashboard cost helpers. The result SHALL drive which categories are queried for grouped spend.

#### Scenario: Category names feed grouped queries

- **WHEN** the backend prepares the cost-categories dashboard payload for a valid profile with Cost Explorer access
- **THEN** the implementation SHALL obtain a list of cost category names before requesting per-category grouped usage

### Requirement: Spend grouped by cost category dimension

For **each** discovered cost category name, the system SHALL call **`GetCostAndUsage`** (or equivalent) with **`UnblendedCost`**, granularity appropriate for month-to-date reporting, and **grouping by** the **Cost Category** dimension for that name (`COST_CATEGORY` with the category key). The system SHALL parse rows into **value keys** (e.g. environment labels, `untagged`) and **amounts**, and SHALL compute each row’s **percentage of** that category’s **total** spend for the period.

#### Scenario: Per-category rows include cost and percent of category total

- **WHEN** Cost Explorer returns grouped results for a cost category
- **THEN** the API response SHALL include each dimension value with **cost** and **pct_of_category_total** (or equivalent field names in the documented JSON contract)

### Requirement: Coverage summary per cost category

The system SHALL compute **coverage** for each cost category where possible: **categorized** spend (sum of rows designated as tagged/categorized) and **uncategorized** spend (rows whose value key matches known “untagged” / default / empty patterns documented in code). The system SHALL expose **coverage_pct** as categorized spend divided by total category spend for the period, expressed as a percentage, when uncategorized rows exist; when no uncategorized row exists, coverage MAY be **100%**.

#### Scenario: Untagged spend lowers coverage

- **WHEN** grouped results include an uncategorized or untagged bucket for a category
- **THEN** the response SHALL include **uncategorized_cost** and **coverage_pct** reflecting that bucket

### Requirement: HTTP lazy slice for cost categories

The system SHALL expose **`GET /costs/dashboard/cost-categories`** (or the path documented in implementation) with the **same profile resolution and demo-mode behavior** as other **`/costs/dashboard/*`** lazy endpoints. The response status SHALL be **200** with a JSON body on success. The response SHALL include **period** bounds and a **categories** array. On Cost Explorer **permission denied**, the response SHALL be an error with a clear message consistent with other cost endpoints.

#### Scenario: Successful response shape

- **WHEN** a client requests the cost-categories dashboard slice with a valid profile and Cost Explorer returns data
- **THEN** the response status is **200** and the body includes **period** and **categories** with per-category breakdown and coverage fields

#### Scenario: Access denied

- **WHEN** Cost Explorer denies access to cost categories or usage for the profile
- **THEN** the response is an error status with a message the UI can display

### Requirement: Costs dashboard UI shows cost categories panel

The hosted web UI **costs dashboard** SHALL include a **Cost categories** section that loads data from the lazy endpoint, displays a **loading** state while fetching, and renders **tables**: at minimum a **summary** of categories (name + coverage or total) and **detail** rows (value, cost, % of total) per category. The UI SHALL show an **empty** or **no data** state when the **categories** array is empty.

#### Scenario: Panel visible on dashboard

- **WHEN** a user opens the costs dashboard with a valid profile
- **THEN** a **Cost categories** panel is visible and triggers fetch of the lazy endpoint

#### Scenario: Error state

- **WHEN** the lazy endpoint returns an error
- **THEN** the panel SHALL show an error message without breaking the rest of the dashboard

### Requirement: Demo mode masks sensitive category values

When **demo mode** is active (`X-Demo-Mode: true`), the backend SHALL apply the same class of **identifier masking** to cost category **value** strings as used for other dashboard cost data, so real account names or IDs in category values are not exposed.

#### Scenario: Demo header triggers masking

- **WHEN** a request includes demo mode and the response includes cost category value labels
- **THEN** those labels SHALL be masked according to the demo transformation rules used elsewhere for the dashboard
