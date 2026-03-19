# conversation-printer Specification

## Purpose

Defines the save/export behavior for the chat conversation: the `/print` slash command, scope and format selection, output file naming, and use of PDF/XLSX MCP servers when available.

## ADDED Requirements

### Requirement: /print slash command

The chat loop SHALL recognize the slash command `/print` (normalized case-insensitively). When the user enters `/print`, the CLI SHALL NOT send the input to the agent and SHALL start the conversation save/export flow: prompt for scope, then for format, then produce the output file and confirm the path.

#### Scenario: /print is not sent to the agent

- **WHEN** the user enters `/print` at the chat prompt
- **THEN** the input is handled as a meta-command and is not appended to the conversation or sent to the agent

#### Scenario: /print starts save flow

- **WHEN** the user enters `/print`
- **THEN** the CLI prompts the user to choose what to save (scope) and then which format to use, and produces one output file accordingly

### Requirement: Scope selection

The save flow SHALL offer the user a choice of scope: (1) entire conversation (all User and Agent turns in the current session), (2) questions and answers only (same turns, optionally formatted as Q/A), (3) summarized conversation (one agent call to summarize the conversation, then save the summary), or (4) last response only (only the most recent Agent message). The chosen scope SHALL determine the content used for export.

#### Scenario: User selects entire conversation

- **WHEN** the user chooses "entire conversation" (or equivalent) and then a format
- **THEN** the exported file SHALL contain all User and Agent messages from the current session in order

#### Scenario: User selects questions and answers only

- **WHEN** the user chooses "questions and answers only" and then a format
- **THEN** the exported file SHALL contain the same turns as the full conversation, presented as questions and answers (no extra thinking/debug content)

#### Scenario: User selects summarized conversation

- **WHEN** the user chooses "summarized conversation" and then a format
- **THEN** the CLI SHALL request a summary from the agent (one call) and the exported file SHALL contain that summary only

#### Scenario: User selects last response only

- **WHEN** the user chooses "last response only" and then a format
- **THEN** the exported file SHALL contain only the most recent Agent message

### Requirement: Format selection

The save flow SHALL offer the user a choice of output format: `txt`, `pdf`, `csv`, or `xlsx`. The CLI SHALL produce exactly one file in the chosen format. For `csv` and `xlsx`, the content SHALL be structured for value (e.g. columns such as turn index, role, content; optional summary sheet when scope is summarized).

#### Scenario: User selects txt

- **WHEN** the user chooses format `txt`
- **THEN** the CLI SHALL write the chosen scope content as plain text to a file with extension `.txt`

#### Scenario: User selects pdf

- **WHEN** the user chooses format `pdf`
- **THEN** the CLI SHALL produce a PDF file (preferably via the configured PDF MCP when available) with extension `.pdf`

#### Scenario: User selects csv

- **WHEN** the user chooses format `csv`
- **THEN** the CLI SHALL write the content as CSV (e.g. columns turn, role, content) with extension `.csv`

#### Scenario: User selects xlsx

- **WHEN** the user chooses format `xlsx`
- **THEN** the CLI SHALL produce an Excel workbook (preferably via the configured Excel MCP when available) with structured rows/sheets and extension `.xlsx`

### Requirement: Output file naming

The exported file SHALL be saved with a name that follows the convention `timestamp-conversation_title.<ext>`, where timestamp is a deterministic format (e.g. `YYYYMMDD_HHMMSS`), conversation_title is derived from the first user message (slugified, truncated) or a default such as `conversation`, and `<ext>` is the correct extension for the chosen format (`txt`, `pdf`, `csv`, `xlsx`).

#### Scenario: Filename uses timestamp and title

- **WHEN** the user completes the save flow with a non-empty conversation
- **THEN** the output filename SHALL start with a timestamp and include a conversation title segment, and SHALL end with the correct extension for the selected format

#### Scenario: Filename uses default title when no first message

- **WHEN** the user completes the save flow and there is no usable first user message to derive a title
- **THEN** the output filename SHALL use a default title (e.g. `conversation`) and the correct extension

### Requirement: PDF and XLSX via MCP when available

When the user selects `pdf` or `xlsx`, the CLI SHALL prefer generating the file via the configured PDF MCP (e.g. @mcp-z/mcp-pdf) or Excel MCP (e.g. excel-mcp-server) when enabled and available. If the MCP is disabled or the tool call fails, the CLI SHALL surface a clear message to the user; a Python fallback for PDF or XLSX MAY be used when documented.

#### Scenario: PDF generated via MCP when enabled

- **WHEN** the user selects format `pdf` and the PDF MCP is enabled and the tool call succeeds
- **THEN** the PDF SHALL be produced using the PDF MCP and written to the target path

#### Scenario: XLSX generated via MCP when enabled

- **WHEN** the user selects format `xlsx` and the Excel MCP is enabled and the tool call succeeds
- **THEN** the workbook SHALL be produced using the Excel MCP and written to the target path

#### Scenario: Clear message when MCP unavailable

- **WHEN** the user selects `pdf` or `xlsx` and the corresponding MCP is disabled or the tool call fails
- **THEN** the CLI SHALL inform the user (e.g. suggest using another format or configuring the MCP) and SHALL NOT silently fail

### Requirement: Documentation of /print and settings

The README (or configuration documentation) SHALL describe the `/print` command, the scope and format options, and any new environment variables or settings (e.g. `FINOPS_MCP_PDF_COMMAND`, `FINOPS_MCP_EXCEL_COMMAND`, or enable flags) used for the conversation printer.

#### Scenario: README documents /print

- **WHEN** a user reads the documented configuration and commands
- **THEN** they SHALL find the `/print` command and its scope/format options described

#### Scenario: New MCP settings documented

- **WHEN** the implementation introduces new env vars or config keys for PDF or Excel MCP
- **THEN** those SHALL be documented (path, format, and precedence) in README or config docs
