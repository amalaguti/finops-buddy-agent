## MODIFIED Requirements

### Requirement: Costs dashboard UI shows cost categories panel

The hosted web UI **costs dashboard** SHALL include a **Cost categories** section that loads data from the lazy endpoint, displays a **loading** state while fetching, and renders **tables**: at minimum a **summary** of categories (name + coverage or total) and **detail** rows (value, cost, % of total) per category. The summary table SHALL be visible whenever the **By cost categories** parent section is expanded. For each category rule that has detail rows, the UI SHALL present the **per-rule detail** table inside a **collapsible** sub-panel that the user can expand or collapse; those sub-panels SHALL be **collapsed by default** when the parent section is first shown. The UI SHALL show an **empty** or **no data** state when the **categories** array is empty.

#### Scenario: Panel visible on dashboard

- **WHEN** a user opens the costs dashboard with a valid profile
- **THEN** a **Cost categories** panel is visible and triggers fetch of the lazy endpoint

#### Scenario: Error state

- **WHEN** the lazy endpoint returns an error
- **THEN** the panel SHALL show an error message without breaking the rest of the dashboard

#### Scenario: Collapsible outer section

- **WHEN** the costs dashboard shows the by-cost-categories block
- **THEN** the user MAY expand or collapse that block with a control consistent with other collapsible sidebar sections (e.g. account context)

#### Scenario: Summary visible when parent expanded

- **WHEN** the **By cost categories** section is expanded and data has loaded successfully
- **THEN** the **summary by cost category rule** table is visible without expanding any per-rule sub-panel

#### Scenario: Per-rule detail collapsed by default

- **WHEN** the **By cost categories** section is expanded and multiple category rules have detail rows
- **THEN** each per-rule detail table is hidden until the user expands that rule’s sub-panel

#### Scenario: User expands a rule detail

- **WHEN** the user activates the expand control for a given cost category rule
- **THEN** the detail table for that rule (value, cost, % of category total) is shown, and the user MAY collapse it again without affecting other rules

#### Scenario: Composite value keys

- **WHEN** a dimension value uses a composite key that includes a `$` separator (e.g. rule prefix and value)
- **THEN** the UI MAY show only the segment after the last `$` for readability, while still allowing access to the full string where appropriate (e.g. tooltip)
