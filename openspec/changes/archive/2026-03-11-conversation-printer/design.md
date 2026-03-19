# Conversation Printer — Design

## Context

The chat loop in `chat_loop.py` already handles meta-commands (`/quit`, `/tooling`, `/context`, `/status`, `/credentials`) before sending input to the agent. Conversation state is a list of strings, `"User: ..."` and `"Agent: ..."`, with no persistent storage of thinking or tool-debug output. The project uses MCP clients (stdio) for Billing, Core, Documentation, etc.; the same pattern can be used to call document-generation MCPs from the chat loop for PDF and XLSX. User requirement: prefer MCPs for PDF and Excel; use Python only for txt/csv or as fallback. Output files must use a consistent naming convention: `timestamp-conversation_title.<ext>`.

## Goals / Non-Goals

**Goals:**

- Implement `/print` as a meta-command: prompt for scope (full / Q&A / summary / last response), then format (txt / pdf / csv / xlsx), then produce one file with the chosen content at `timestamp-conversation_title.<ext>`.
- Use MCP servers for PDF and XLSX when available: md-to-pdf-mcp (Python, Markdown→PDF via WeasyPrint) for PDF, excel-mcp-server (e.g. negokaz) for XLSX. TXT and CSV are written directly in Python.
- Structure csv/xlsx for value: e.g. columns Turn, Role, Content (and optional Summary sheet or tables when summarizing).
- Keep env/settings consistent: any new MCP commands use `FINOPS_`-prefixed env vars and optional YAML under `agent` (e.g. `pdf_mcp_command`, `excel_mcp_command`), following existing MCP configuration pattern.
- Document `/print` and any new settings in README (or config docs).

**Non-Goals:**

- Storing or exporting "thinking" or tool-debug content in this first version unless the agent framework exposes it in a consumable way; "full conversation" means all User/Agent turns. A future enhancement can add "with reasoning" when that data is available.
- Implementing a separate GUI or file picker; scope and format are chosen via prompts in the terminal.
- Supporting formats beyond txt, pdf, csv, xlsx in the initial implementation.

## Decisions

### 1. Where `/print` runs (chat loop, not agent)

**Decision:** Handle `/print` entirely in the chat loop (same as `/context`, `/tooling`). Do not send the user message to the agent.

**Rationale:** Scope and format are fixed choices; no need for the LLM. The loop has direct access to `conversation` and can call helpers or MCP clients to write the file. Keeps behavior predictable and avoids extra latency/cost.

**Alternative considered:** Let the user say "save this conversation" and have the agent use tools. Rejected because it would require passing full conversation into the agent and would be less consistent with other slash commands.

### 2. PDF generation: md-to-pdf-mcp

**Decision:** Use **md-to-pdf-mcp** (PyPI) as the preferred PDF MCP. Tool: `convert_markdown_to_pdf`. Input: Markdown content (conversation formatted as Markdown, e.g. `## User` / `## Agent` sections or plain paragraphs). Run via stdio (e.g. `uvx md-to-pdf-mcp`) or configurable command. No API key required. Uses WeasyPrint under the hood (pure Python PDF generation; optional system libs e.g. Pango/Cairo on macOS).

**Rationale:** Python-based, aligns with project stack; no Node.js required for PDF. Good for "conversation as document" with optional TOC and styling. Alternative Node-based option (@mcp-z/mcp-pdf) was considered; user chose Python stack consistency.

**Alternative considered:** @mcp-z/mcp-pdf (Node). Rejected in favor of md-to-pdf-mcp for a full-Python PDF path.

### 3. XLSX generation: excel-mcp-server (negokaz)

**Decision:** Use **excel-mcp-server** (e.g. `uvx excel-mcp-server stdio` or equivalent) for XLSX. Tools: e.g. `create_workbook`, `write_worksheet`. Structure: one sheet with columns such as Turn, Role, Content; optional second sheet for summary if "summarized" scope is chosen.

**Rationale:** Supports create/write without Microsoft Excel; fits existing pattern of optional MCPs and command overrides. Python version aligns with project stack.

**Alternative considered:** Python openpyxl. Use only as fallback if Excel MCP is disabled or unavailable.

### 4. Conversation title for filename

**Decision:** Derive `conversation_title` from the first user message: slugify (lowercase, replace spaces and invalid filename chars with `-` or `_`), truncate to a reasonable length (e.g. 40–60 chars). If no usable first message, use a default such as `conversation`.

**Rationale:** Gives recognizable, safe filenames without user input at print time. Timestamp ensures uniqueness.

**Alternative considered:** Always use `conversation`. Rejected to improve findability of saved files.

### 5. Invoking MCP from the chat loop (not from the agent)

**Decision:** For PDF and XLSX, the chat loop (or a small helper module) creates a short-lived MCP client to the PDF or Excel server, calls the appropriate tool with the built content and target filename/path, and then either uses the returned path or writes returned bytes to the desired path (`timestamp-conversation_title.<ext>`). For PDF, content is formatted as **Markdown** before calling md-to-pdf-mcp's `convert_markdown_to_pdf`. Reuse the same stdio/command pattern as existing MCP clients; add settings/getters for PDF and Excel MCP command (and enable flag) following the pattern of `get_billing_mcp_command`, etc.

**Rationale:** The agent does not need to know about printing; the loop has the conversation and can call MCP tools directly. Aligns with "meta-command" behavior and keeps PDF/Excel generation behind optional MCP config.

### 6. Summarized scope: one agent call

**Decision:** For "summarized conversation", perform a single agent call with a system-style prompt that asks for a concise summary of the provided conversation text. Use the returned summary string as the body to save in the chosen format (txt/pdf/csv/xlsx). No change to the main conversation history.

**Rationale:** Keeps summary logic in one place and reuses the same export pipeline. No new tools required.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| PDF or Excel MCP not installed / fails | Make PDF and XLSX optional; if MCP disabled or tool call fails, show a clear message and optionally suggest fallback (e.g. use txt or install MCP). Document required commands in README. |
| Very long conversations | Cap or paginate content sent to PDF tool; for xlsx, write all rows (Excel handles large sheets). Consider truncation warning in UI for "full" scope. |
| Conversation title from first message is ambiguous or empty | Fallback to `conversation`; ensure timestamp always present so files remain unique. |
| MCP returns path vs bytes | Design helper to accept either: if path, copy/move to target path; if base64 or bytes, write to target path. |

## Migration Plan

- No data migration. New command only.
- **Deploy:** Ship code with `/print`; PDF/XLSX require user to configure (or accept defaults) the MCP server commands if they want those formats.
- **Rollback:** Remove `/print` branch and any new helpers; no persisted state to revert.

## Open Questions

- Whether to add an explicit "with reasoning" scope later when the agent framework exposes thinking/reasoning in a structured way.
- Exact tool return shape for md-to-pdf-mcp `convert_markdown_to_pdf` (path vs bytes) to implement the file-write step; confirm from MCP docs or runtime and handle both if needed.
