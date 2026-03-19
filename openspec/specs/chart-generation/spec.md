# Capability: chart-generation

## Requirements

### Requirement: Agent chart generation tool

The agent SHALL have access to a `create_chart` tool that generates static charts (line, bar, pie, scatter) from structured data using matplotlib. The tool SHALL run entirely in-process with no external HTTP calls. The tool SHALL return a markdown string containing an embedded base64 data URI image (`![title](data:image/png;base64,...)`) that the agent can include in its response.

#### Scenario: Agent generates line chart from cost data

- **WHEN** the agent invokes `create_chart` with `chart_type="line"` and data suitable for a line chart (e.g. time-series cost data)
- **THEN** the tool returns a markdown string with an embedded PNG image as a data URI
- **AND** the agent can include that string in its reply so the user sees the chart inline

#### Scenario: Agent generates bar chart for service breakdown

- **WHEN** the agent invokes `create_chart` with `chart_type="bar"` and data with labels and values (e.g. service names and costs)
- **THEN** the tool returns a markdown string with an embedded PNG image as a data URI
- **AND** the chart displays the data as a bar chart

#### Scenario: Agent generates pie chart for proportion

- **WHEN** the agent invokes `create_chart` with `chart_type="pie"` and data with labels and values
- **THEN** the tool returns a markdown string with an embedded PNG image as a data URI
- **AND** the chart displays the data as a pie chart

#### Scenario: Chart tool supports scatter plots

- **WHEN** the agent invokes `create_chart` with `chart_type="scatter"` and data with x and y values
- **THEN** the tool returns a markdown string with an embedded PNG image as a data URI
- **AND** the chart displays the data as a scatter plot

#### Scenario: Chart tool is on read-only allow-list

- **WHEN** the read-only guardrail is active
- **THEN** `create_chart` is on the default read-only allow-list and executes when the agent invokes it

#### Scenario: Chart tool handles invalid data gracefully

- **WHEN** the agent invokes `create_chart` with malformed or empty data
- **THEN** the tool returns an error message string (not markdown with image) that the agent can relay to the user
- **AND** no exception propagates to the agent

### Requirement: Chart generation uses matplotlib locally

Chart generation SHALL use the matplotlib library. Charts SHALL be rendered to an in-memory buffer (e.g. BytesIO) and encoded as base64. No chart data SHALL be sent to any external service or URL.

#### Scenario: No network calls during chart generation

- **WHEN** the agent invokes `create_chart` with valid data
- **THEN** the tool completes without making any HTTP or network requests
- **AND** all processing occurs within the Python process
