# Conversation Printer — Proposal

## Why

Users need a way to save or export the current chat session for records, sharing, or offline review. Today there is no built-in way to persist a conversation; copying from the terminal is fragile and loses structure. A dedicated "print" (save/export) flow gives users control over what to export (full thread, Q&A only, summary, or last response) and in which format (txt, pdf, csv, xlsx), with output files named consistently (e.g. timestamp and conversation title) for easy filing and search.

## What Changes

- **New slash command `/print`** in the chat loop. Invoking it starts a save/export flow; the user is not sent to the agent.
- **Scope selection**: The agent (or chat loop) asks what to save: (1) entire conversation (all User/Agent turns; optional future: including thinking/reasoning when available), (2) questions and answers only, (3) summarized conversation (one agent call to summarize, then save), or (4) last response only.
- **Format selection**: User chooses output format: `txt`, `pdf`, `csv`, or `xlsx`. For csv/xlsx, content is structured for value (e.g. turn index, role, content; tables where useful).
- **Output file naming**: Saved file uses `timestamp-conversation_title.<ext>` (e.g. `20250311_143022-cost-review.pdf`) with the correct extension per format.
- **PDF and XLSX via MCP**: Prefer MCP servers for PDF and Excel generation where available (md-to-pdf-mcp for PDF, excel-mcp-server for xlsx); use Python only for txt/csv or as fallback.
- **Documentation**: README (or docs) updated to describe the `/print` command, scope and format options, and any new settings or env vars (e.g. MCP commands for document generation).

## Capabilities

### New Capabilities

- **conversation-printer**: Save/export the current chat conversation. Covers scope selection (full / Q&A / summary / last response), format selection (txt, pdf, csv, xlsx), structured output for tabular formats, output path convention (`timestamp-conversation_title.<ext>`), and integration with PDF/XLSX MCP servers when used.

### Modified Capabilities

- None. The chat loop gains a new slash command; behavior of existing chat-agent requirements is unchanged.

## Impact

- **Chat loop** (`src/finops_agent/agent/chat_loop.py`): New `/print` branch; prompt for scope and format; build content from `conversation` (and optional summary/last-only); call export path (Python for txt/csv, MCP clients for pdf/xlsx when enabled); write or receive file at target path.
- **Settings/config**: Optional MCP command overrides for document/PDF and Excel servers (e.g. `FINOPS_MCP_PDF_COMMAND`, `FINOPS_MCP_EXCEL_COMMAND`) and enable flags, following existing MCP pattern; config template in `config/settings.yaml` if new keys are added.
- **Dependencies**: No new Python runtime dependencies for txt/csv. PDF and XLSX may require adding MCP server config (e.g. md-to-pdf-mcp, excel-mcp-server) and, in the chat loop or a small helper, one-off MCP tool invocation to generate the file.
- **Docs**: README (or configuration doc) updated with `/print` usage, scope/format options, and any new env vars or settings.
- **Tests**: Pytest coverage for conversation-printer behavior (scope options, format selection, file naming, and that /print does not send input to the agent).
