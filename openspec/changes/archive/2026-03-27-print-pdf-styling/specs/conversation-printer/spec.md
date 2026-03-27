# conversation-printer — Delta (print-pdf-styling)

## MODIFIED Requirements

### Requirement: Format selection

The save flow SHALL offer the user a choice of output format: `txt`, `pdf`, `csv`, or `xlsx`. The CLI SHALL produce exactly one file in the chosen format. For `csv` and `xlsx`, the content SHALL be structured for value (e.g. columns such as turn index, role, content; optional summary sheet when scope is summarized).

#### Scenario: User selects txt

- **WHEN** the user chooses format `txt`
- **THEN** the CLI SHALL write the chosen scope content as plain text to a file with extension `.txt`

#### Scenario: User selects pdf

- **WHEN** the user chooses format `pdf`
- **THEN** the CLI SHALL produce a PDF file with extension `.pdf` using a **print-oriented** rendering path: Markdown content SHALL be converted to HTML with **pipe-table** support enabled, wrapped in a **full HTML document** with an **embedded default stylesheet** (see **PDF document presentation** requirement), and rendered **in-process** (WeasyPrint, then xhtml2pdf, then reportlab as documented fallbacks) before any PDF MCP attempt; if all in-process paths fail and the PDF MCP is enabled and succeeds, a PDF MAY be produced via MCP

#### Scenario: User selects csv

- **WHEN** the user chooses format `csv`
- **THEN** the CLI SHALL write the content as CSV (e.g. columns turn, role, content) with extension `.csv`

#### Scenario: User selects xlsx

- **WHEN** the user chooses format `xlsx`
- **THEN** the CLI SHALL produce an Excel workbook (preferably via the configured Excel MCP when available) with structured rows/sheets and extension `.xlsx`

### Requirement: PDF and XLSX via MCP when available

When the user selects `pdf`, the implementation SHALL **prefer** the **in-process** styled PDF pipeline when it succeeds. The **PDF MCP** (e.g. md-to-pdf-mcp) SHALL be used when in-process generation fails or is unavailable, as documented. When the user selects `xlsx`, the CLI SHALL prefer the configured **Excel MCP** when enabled and available. If the MCP is disabled or the tool call fails, the CLI SHALL surface a clear message to the user; a Python fallback for PDF or XLSX SHALL be used when implemented.

#### Scenario: PDF generated in-process when styled pipeline succeeds

- **WHEN** the user selects format `pdf` and the in-process PDF pipeline (Markdown with tables → styled HTML → renderer) succeeds
- **THEN** the PDF SHALL be written to the target path without requiring the PDF MCP

#### Scenario: PDF MCP used when in-process fails

- **WHEN** the user selects format `pdf` and the in-process PDF pipeline fails and the PDF MCP is enabled and the tool call succeeds
- **THEN** the PDF SHALL be produced using the PDF MCP and written to the target path

#### Scenario: XLSX generated via MCP when enabled

- **WHEN** the user selects format `xlsx` and the Excel MCP is enabled and the tool call succeeds
- **THEN** the workbook SHALL be produced using the Excel MCP and written to the target path

#### Scenario: Clear message when MCP unavailable

- **WHEN** the user selects `pdf` or `xlsx` and the corresponding MCP is disabled or the tool call fails after fallbacks
- **THEN** the CLI SHALL inform the user (e.g. suggest using another format or configuring the MCP) and SHALL NOT silently fail

## ADDED Requirements

### Requirement: PDF document presentation

PDF output from `/print` (and any shared export path using the same pipeline) SHALL use a **document-level** default stylesheet embedded in the HTML shell: **A4** (or equivalent) page size with **explicit margins**; **sans-serif** body text with **controlled font sizes**; **headings** with visible hierarchy (e.g. weight, size, borders or spacing); **`table` elements** SHALL use **collapsed borders**, **header row** styling distinct from body rows, and **readable** cell padding; **`code`**, **`blockquote`**, **`hr`**, and **`a`** elements SHALL have styles consistent with a professional report. The default appearance SHALL align with the project reference **`markdown-to-pdf-guide.md`** unless superseded by explicit product branding decisions.

#### Scenario: Styled HTML contains print CSS

- **WHEN** PDF is generated via the primary in-process path that uses the shared HTML wrapper
- **THEN** the HTML document SHALL include an embedded `<style>` block defining `@page` (or equivalent margin rules) and rules for `body`, `h1`–`h3`, `table`, `th`, `td`, and `tr` (or equivalent table readability)

#### Scenario: Pipe tables render as HTML tables in PDF

- **WHEN** the exported Markdown contains a GitHub-flavored **pipe table** in a turn
- **THEN** the PDF rendering pipeline SHALL produce `<table>` markup with header and body cells (not plain preformatted pipe text) for that table when using WeasyPrint or xhtml2pdf

### Requirement: PDF spacing and markdown extensions

The PDF pipeline SHALL avoid **excessive vertical whitespace** in typical multi-turn exports: implementation SHALL **normalize** redundant blank-line runs in the Markdown source before conversion (without destroying intentional single paragraph breaks), and SHALL **not** enable **nl2br** by default if it worsens spacing for conversation exports. The Markdown converter SHALL enable the **`tables`** extension for PDF generation.

#### Scenario: Multi-turn Q&A does not produce runaway vertical gaps

- **WHEN** the export contains several User and Agent turns separated by blank lines in the Markdown source
- **THEN** the rendered PDF SHALL not exhibit **excessive** empty vertical space between consecutive sections compared to a single blank line between major blocks (asserted by tests on HTML or structure, not pixel diffs)

#### Scenario: Tables extension enabled for PDF markdown

- **WHEN** PDF is generated from Markdown that includes a pipe table
- **THEN** the Markdown conversion step SHALL use an extension set that includes **tables** so pipe syntax becomes `<table>` elements

### Requirement: Optional PDF cover metadata

When generating PDF, the implementation SHALL support prepending a **short metadata block** (e.g. title line “FinOps Buddy — conversation export”, export **timestamp**, optional **AWS profile** name) before the conversation body, using only information already available to the save flow **without** additional AWS API calls.

#### Scenario: Cover block uses only available context

- **WHEN** optional PDF cover metadata is enabled
- **THEN** the cover SHALL not invent account IDs, costs, or other data not already supplied by the chat session or CLI context

### Requirement: Documentation for PDF quality and fallbacks

The configuration documentation SHALL describe **PDF export behavior**: in-process styled pipeline first, **fallback order**, the role of **PDF MCP**, **WeasyPrint** system dependencies where relevant, and that **reportlab** fallback is **simplified** and may not match full Markdown+CSS parity.

#### Scenario: CONFIGURATION documents PDF pipeline

- **WHEN** a user reads `docs/CONFIGURATION.md` for conversation export
- **THEN** they SHALL find expectations for PDF appearance, fallback order, and MCP vs in-process behavior
