# costs-dashboard-carousel Specification

## Purpose

Define the hosted web UI **carousel presentation mode** for the costs dashboard: one primary block per slide (each `MiniTable` plus the Savings Plans summary card), configurable dwell time, accessibility, and forced expansion of collapsible sections so all primary blocks participate.

## ADDED Requirements

### Requirement: Carousel mode toggle

The hosted costs dashboard SHALL provide a **carousel mode** control (e.g. toggle or switch) that switches between the **default** multi-column grid layout and **carousel** layout. The default state SHALL be **carousel off** (existing layout).

#### Scenario: Default is grid layout

- **WHEN** the user opens the costs dashboard and has not enabled carousel mode
- **THEN** the dashboard SHALL render the standard grid (and existing collapsible sections) as today

#### Scenario: Enabling carousel switches layout

- **WHEN** the user enables carousel mode
- **THEN** the primary dashboard blocks SHALL be shown inside a carousel presentation instead of the default grid for those blocks

### Requirement: One slide per MiniTable and Savings Plans summary

In carousel mode, the system SHALL treat each **primary** `MiniTable` in the costs dashboard flow as **one slide**, and SHALL treat the **Savings Plans summary** panel (utilization/coverage card, not a `MiniTable`) as **one slide**. Slides SHALL follow this order: **By AWS service**, **By linked account**, **Marketplace**, **Optimization recommendations**, **Anomalies**, **Savings Plans summary**, **Cost category summary** table, then **one slide per cost category Details** `MiniTable` (in data order), then **Savings Plans purchase recommendations** `MiniTable`.

#### Scenario: Main grid tables map to distinct slides

- **WHEN** carousel mode is on and data is loaded for the main grid
- **THEN** each of the five `MiniTable` blocks in the main grid (service, account, marketplace, recommendations, anomalies) SHALL be addressable as its own slide in sequence

#### Scenario: Savings Plans summary is its own slide

- **WHEN** carousel mode is on
- **THEN** the Savings Plans utilization/coverage summary panel SHALL appear as its own slide separate from the adjacent `MiniTable` slides

### Requirement: Collapsible sections expanded in carousel mode

When carousel mode is **on**, the **By cost categories** and **Savings Plans purchase recommendations** sections SHALL be **expanded** so that all cost category summary and detail `MiniTable`s and the purchase recommendations `MiniTable` are present for the slide sequence. When carousel mode is **off**, expand/collapse behavior SHALL match existing user controls (collapsed state MAY persist when re-entering carousel mode per implementation, but carousel mode while on MUST show expanded content for rotation).

#### Scenario: Categories visible for rotation

- **WHEN** the user enables carousel mode
- **THEN** the By cost categories section SHALL be expanded and the cost category summary and each category Details `MiniTable` SHALL participate in the slide order

#### Scenario: Purchase recommendations visible for rotation

- **WHEN** the user enables carousel mode
- **THEN** the Savings Plans purchase recommendations section SHALL be expanded and the purchase recommendations `MiniTable` SHALL participate in the slide order

### Requirement: Auto-advance interval

The carousel SHALL **auto-advance** to the next slide on a fixed interval. The default interval SHALL be **15 seconds**. The UI SHALL provide a control (e.g. dropdown) to select **5**, **10**, **15**, or **30** seconds. Changing the interval SHALL apply to subsequent advances without requiring a page reload.

#### Scenario: Default 15 seconds

- **WHEN** the user enables carousel mode and does not change the interval
- **THEN** slides SHALL advance every 15 seconds

#### Scenario: User selects 30 seconds

- **WHEN** the user selects 30 seconds in the interval control
- **THEN** slides SHALL advance every 30 seconds

### Requirement: Pause and reduced motion

The UI SHALL provide a way to **pause** auto-advance (and resume). If the user has **`prefers-reduced-motion: reduce`**, the system SHALL **not** auto-advance slides; the user MAY still navigate slides manually if such navigation is implemented.

#### Scenario: Pause stops rotation

- **WHEN** the user activates pause
- **THEN** the carousel SHALL stop auto-advancing until resume

#### Scenario: Reduced motion disables auto-advance

- **WHEN** the user agent reports `prefers-reduced-motion: reduce`
- **THEN** the carousel SHALL not automatically advance on a timer

### Requirement: Drill-down overlays excluded from slide list

Ephemeral detail panels opened from row or card interactions (e.g. recommendation details, account/service drill-down `MiniTable`s, anomaly details, expanded Savings Plans details modal) SHALL **not** be added as carousel slides. They MAY continue to work outside carousel mode or when carousel is off; behavior when carousel is on SHOULD avoid trapping focus—exact interaction MAY be implementation-defined but MUST NOT contradict pause/reduced-motion rules.

#### Scenario: Detail panel is not a carousel slide

- **WHEN** the user opens a recommendation detail panel from the main dashboard
- **THEN** that detail panel SHALL not be inserted into the carousel slide sequence

### Requirement: Visual style

The carousel presentation SHALL use a **modern, depth-oriented** appearance (e.g. CSS perspective and transforms) consistent with the app theme (`finops-*` classes) and SHALL keep the active slide clearly readable.

#### Scenario: Active slide is emphasized

- **WHEN** carousel mode is on and a slide is active
- **THEN** the active slide SHALL be visually distinct from non-active content (e.g. focus, scale, or opacity treatment)
