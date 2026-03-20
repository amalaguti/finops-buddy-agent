# MCP servers (Model Context Protocol)

FinOps Buddy extends its capabilities through **MCP servers** — a plugin architecture that gives the AI agent access to specialized tools. Each server runs as a subprocess and communicates via stdio.

| MCP Server | What it provides | Example tools |
|------------|------------------|---------------|
| **AWS Knowledge** | AWS best practices, Well-Architected guidance | `search_knowledge`, `get_guidance` |
| **Billing & Cost Management** | Detailed cost queries, budgets, anomalies | `get_cost_and_usage`, `list_budgets`, `session_sql` |
| **AWS Documentation** | Official AWS docs search | `search_documentation`, `read_documentation` |
| **AWS Pricing** | Real-time pricing data | `get_products`, `get_price_list` |
| **Core MCP** | Unified access to multiple AWS services | Role-based tool aggregation |
| **PDF Export** | Conversation export | `export_to_pdf` |
| **Excel Export** | Data export | `export_to_excel` |

MCP servers are managed via **uv/uvx** (the fast Python package runner) and configured through environment variables or YAML settings. The agent dynamically discovers available tools and uses them to answer questions.

Enable flags, commands, and guardrail notes are documented in [Configuration](./CONFIGURATION.md).
