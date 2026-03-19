# Conversation Printer — Tasks

## 1. Branch and settings

- [x] 1.1 Create or switch to a feature branch (e.g. `feature/conversation-printer`); do not implement on main
- [x] 1.2 Add optional PDF MCP and Excel MCP config: enable flags and command overrides in `config/settings.yaml` and settings module; support `FINOPS_MCP_PDF_COMMAND` and `FINOPS_MCP_EXCEL_COMMAND` (and enable env vars if needed), following the pattern of existing MCP getters
- [x] 1.3 Update `config/settings.yaml` template with any new keys (e.g. `agent.pdf_mcp_command`, `agent.excel_mcp_command`) using placeholder values; keep file safe to commit

## 2. Chat loop /print command

- [x] 2.1 In `chat_loop.py`, add handling for normalized input `/print`: do not send to agent; branch into the save/export flow
- [x] 2.2 Implement scope prompt: ask user to choose entire conversation, Q&A only, summarized, or last response only; parse response (e.g. 1–4 or keywords)
- [x] 2.3 Implement format prompt: ask user to choose txt, pdf, csv, or xlsx; parse response and validate
- [x] 2.4 Build content from `conversation` (and optional agent call for summary) according to selected scope; expose a small helper or module for content building so it can be tested

## 3. Output file naming and path

- [x] 3.1 Implement filename generator: timestamp (e.g. `YYYYMMDD_HHMMSS`) + conversation title derived from first user message (slugified, truncated) or default `conversation`; correct extension per format
- [x] 3.2 Decide and document output directory (e.g. current working directory or configurable path); write the file to that path with the generated name

## 4. Export implementations

- [x] 4.1 Implement TXT export: write chosen content as plain text to the target path (Python only)
- [x] 4.2 Implement CSV export: write content with structured columns (e.g. turn, role, content) using Python `csv` module
- [x] 4.3 Add PDF MCP client factory (or reuse pattern) and helper to call `convert_markdown_to_pdf` (md-to-pdf-mcp) with conversation content as Markdown and output filename; write returned file (path or bytes) to target path; handle disabled/failure with clear user message
- [x] 4.4 Add Excel MCP client factory (or reuse pattern) and helper to create workbook and write worksheet (e.g. excel-mcp-server) with turn/role/content (and optional summary sheet); write to target path; handle disabled/failure with clear user message
- [x] 4.5 Wire /print flow: after scope and format selection, call the appropriate exporter (txt/csv direct, pdf/xlsx via MCP when available) and print confirmation with output path

## 5. Documentation and tests

- [x] 5.1 Update README (or config docs): document `/print` command, scope and format options, and any new env vars or settings (e.g. `FINOPS_MCP_PDF_COMMAND`, `FINOPS_MCP_EXCEL_COMMAND`)
- [x] 5.2 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues
- [x] 5.3 Add or extend pytest tests for conversation-printer: /print not sent to agent, scope options, format selection, filename convention (timestamp + title + ext), and behavior when PDF/Excel MCP disabled or failing; place tests in `tests/` (e.g. `test_chat_loop.py` or `test_conversation_printer.py`); name tests after spec scenarios where practical
