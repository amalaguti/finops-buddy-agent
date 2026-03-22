# chart-generation Specification Delta

## ADDED Requirements

### Requirement: Chart default styling and raster export

The `create_chart` tool SHALL apply a **project-defined matplotlib stylesheet** (built-in `matplotlib.style`) before plotting so charts have consistent grid, typography, and color cycle. Raster export SHALL use a **default DPI of at least 120** and a **documented default figure size** appropriate for inline chat display. Saving to PNG SHALL use **tight bounding** (e.g. `bbox_inches="tight"` with modest padding) so margins are trimmed without routinely clipping titles or axis labels.

#### Scenario: Chart render uses elevated DPI

- **WHEN** the agent invokes `create_chart` with valid data for any supported `chart_type`
- **THEN** the PNG is encoded at the configured default DPI **not less than 120**

#### Scenario: Chart render applies configured stylesheet

- **WHEN** the agent invokes `create_chart` with valid data
- **THEN** matplotlib has the project default stylesheet active for that render so appearance is consistent across chart types

### Requirement: Bar chart categories sorted by value

For `chart_type="bar"`, the tool SHALL **sort** label/value pairs by numeric value in **descending** order before plotting. When values tie, ordering SHALL be **stable** relative to the input order.

#### Scenario: Unsorted bar data displays descending

- **WHEN** the agent invokes `create_chart` with `chart_type="bar"` and rows that are not sorted by value
- **THEN** the rendered bars appear in **descending** order of value

#### Scenario: Non-bar chart types preserve series order

- **WHEN** the agent invokes `create_chart` with `chart_type` of `line`, `pie`, or `scatter` and ordered input rows
- **THEN** the tool does **not** reorder rows solely to change display order (existing semantics preserved)
