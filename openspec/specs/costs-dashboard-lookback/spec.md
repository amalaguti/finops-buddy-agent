# costs-dashboard-lookback Specification

## Purpose

Hosted costs dashboard support for **aligning the “by AWS service” and “by linked account”** lazy slices with a **shared period preset** (month-to-date or rolling days), **HTTP query parameter**, **session-scoped frontend caching**, and **one UI control** for both tables.

## Requirements

### Requirement: Dashboard slice period presets for by-service and by-account

The system SHALL support a **`period`** query parameter on **`GET /costs/dashboard/by-service`** and **`GET /costs/dashboard/by-account`** with the same allowed values on both routes. Allowed values SHALL be: **`mtd`** (month to date), **`7d`**, **`30d`**, **`60d`**, **`90d`**. When **`period`** is omitted, the server SHALL behave as **`mtd`**. The server SHALL use Cost Explorer date ranges consistent with **`mtd`** for month-to-date and a rolling **N**-day window ending **today** (inclusive of today) for **`7d`** / **`30d`** / **`60d`** / **`90d`**, with **start** and **end** (exclusive) passed into the existing cost aggregation helpers. **Invalid** `period` values SHALL result in **`400`** with an error message.

#### Scenario: Default is month to date

- **WHEN** a client requests either slice **without** a `period` query parameter
- **THEN** the implementation SHALL use the same month-to-date range as before this feature and return **200** with a JSON array body

#### Scenario: Rolling last 30 days

- **WHEN** a client requests either slice with `period=30d`
- **THEN** the implementation SHALL query costs for a rolling 30-day window ending today and return **200** with a JSON array body

#### Scenario: Invalid period

- **WHEN** a client requests either slice with an unsupported `period` value
- **THEN** the response status SHALL be **400**

### Requirement: Hosted UI single lookback selector for service and account tables

The hosted web UI costs dashboard SHALL provide **one** control to select the lookback period **Month to date**, **Last 7 days**, **Last 30 days**, **Last 60 days**, or **Last 90 days**. The default selection SHALL be **Month to date**. Changing the selection SHALL update **both** the **By AWS service** and **By linked account** tables to use the same period. Table labels or nearby copy SHALL reflect the selected period (not only “month to date” when another period is selected).

#### Scenario: One control updates both tables

- **WHEN** the user selects a non-default rolling period
- **THEN** both the by-service and by-account dashboard fetches SHALL use the corresponding `period` query parameter value

#### Scenario: Default view

- **WHEN** the user opens the costs dashboard and has not changed the control
- **THEN** the UI SHALL request month-to-date data for both tables (equivalent to `period=mtd` or omitting `period`)

### Requirement: Session-scoped cache includes period

The frontend SHALL cache responses for the by-service and by-account dashboard slices **per profile** and **per selected period preset** so that revisiting the same preset in the same session does not trigger repeated network requests unless the cache is invalidated by existing rules (e.g. profile change).

#### Scenario: Repeat selection uses cache

- **WHEN** the user selects period A, then B, then A again in the same session
- **THEN** the second time period A is selected, the client SHALL NOT repeat the same HTTP GET for slices already cached for period A (unless the implementation explicitly invalidates cache)
