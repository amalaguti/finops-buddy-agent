"""Read-only guardrails: input intent check and tool allow-list hook."""

from __future__ import annotations

import re

from strands.hooks import BeforeToolCallEvent, HookRegistry

# Friendly message when the input guardrail blocks before calling the agent.
MESSAGE_INPUT_BLOCKED = (
    "I'm here to help with cost and usage questions only—I can't create, change, or delete "
    "anything in your AWS account. You can ask me for things like cost breakdowns, trends, or "
    "how to interpret billing; for making changes, please use the AWS Console or CLI."
)

# Message for the tool guardrail (passed to the agent when a non–read-only tool is blocked).
# Written for the end user; the agent typically relays it.
MESSAGE_TOOL_BLOCKED = (
    "I can't run that action—I'm set up for read-only cost and usage analysis only. "
    "I can still help with reports, comparisons, and explaining your costs; for any changes "
    "to your account, use the AWS Console or your own scripts."
)

# Built-in FinOps tools (all read-only: Cost Explorer GetCostAndUsage, date helpers, export).
BUILTIN_READ_ONLY_TOOLS = frozenset(
    {
        "get_current_date",
        "current_period_costs",
        "costs_for_date_range",
        "month_over_month_costs",
        "week_over_week_costs",
        "biweekly_over_biweekly_costs",
        "export_to_pdf",
        "export_to_excel",
        "create_chart",
    }
)

# Known read-only MCP tool names (as seen by the agent). May be namespaced (e.g. aws___*, doc___*).
# Extend this set when adding new read-only MCP tools.
#
# IMPORTANT — session-sql (AWS Billing and Cost Management MCP): This tool MUST NOT be blocked.
# It executes SQL on the MCP server's in-process SQLite session database only (no AWS mutations).
# It is required for cross-tool cost analysis (e.g. joining cost-explorer results) and uses
# server-side validation (no DROP/DELETE/TRUNCATE/ALTER). Always keep it in the allow-list.
MCP_READ_ONLY_TOOL_NAMES = frozenset(
    {
        # AWS Knowledge MCP (often prefixed aws___)
        "search_documentation",
        "read_documentation",
        "recommend",
        "list_regions",
        "get_regional_availability",
        "aws___search_documentation",
        "aws___read_documentation",
        "aws___recommend",
        "aws___list_regions",
        "aws___get_regional_availability",
        # AWS Documentation MCP (often doc___ or bare names)
        "doc___search_documentation",
        "doc___read_documentation",
        "doc___recommend",
        # Billing and Cost Management (BCM) MCP: Cost Explorer, Budgets, Billing Conductor list/read
        "cost-explorer",
        "budgets",
        "pricing",
        "list-account-associations",
        "list-billing-groups",
        "list-custom-line-items",
        "compute-optimizer",
        "cost-optimization",
        "storage-lens",
        "aws-pricing",
        "bcm-pricing-calc",
        "cost-anomaly",
        "cost-comparison",
        "free-tier-usage",
        "rec-details",
        "ri-performance",
        "sp-performance",
        # Required: safe, in-process SQL only; must not be blocked (see comment above).
        "session-sql",
        "list-billing-group-cost-reports",
        "get-billing-group-cost-report",
        "list-custom-line-item-versions",
        "list-resources-associated-to-custom-line-item",
        "list-pricing-rules",
        "list-pricing-plans",
        "list-pricing-rules-for-plan",
        "list-pricing-plans-for-rule",
        # Standalone Cost Explorer MCP (when enabled)
        "get_cost_and_usage",
        "get_cost_forecast",
        "get_dimension_values",
        # AWS Pricing MCP Server (read-only pricing and analysis)
        "analyze_cdk_project",
        "analyze_terraform_project",
        "get_pricing",
        "get_bedrock_patterns",
        "generate_cost_report",
        "get_pricing_service_codes",
        "get_pricing_service_attributes",
        "get_pricing_attribute_values",
        "get_price_list_urls",
        # Core MCP Server (proxied tools; namespaced by server, all read-only)
        "prompt_understanding",
        "aws_knowledge_aws___get_regional_availability",
        "aws_knowledge_aws___list_regions",
        "aws_knowledge_aws___read_documentation",
        "aws_knowledge_aws___recommend",
        "aws_knowledge_aws___search_documentation",
        "aws_api_suggest_aws_commands",
        "aws_api_call_aws",
        "diagram_generate_diagram",
        "diagram_get_diagram_examples",
        "diagram_list_icons",
        "pricing_analyze_cdk_project",
        "pricing_analyze_terraform_project",
        "pricing_get_pricing",
        "pricing_get_bedrock_patterns",
        "pricing_generate_cost_report",
        "pricing_get_pricing_service_codes",
        "pricing_get_pricing_service_attributes",
        "pricing_get_pricing_attribute_values",
        "pricing_get_price_list_urls",
        "cost_explorer_get_today_date",
        "cost_explorer_get_dimension_values",
        "cost_explorer_get_tag_values",
        "cost_explorer_get_cost_forecast",
        "cost_explorer_get_cost_and_usage_comparisons",
        "cost_explorer_get_cost_comparison_drivers",
        "cost_explorer_get_cost_and_usage",
        "syntheticdata_get_data_gen_instructions",
        "syntheticdata_validate_and_save_data",
        "syntheticdata_load_to_storage",
        "syntheticdata_execute_pandas_code",
        "cloudwatch_describe_log_groups",
        "cloudwatch_analyze_log_group",
        "cloudwatch_execute_log_insights_query",
        "cloudwatch_get_logs_insight_query_results",
        "cloudwatch_cancel_logs_insight_query",
        "cloudwatch_get_metric_data",
        "cloudwatch_get_metric_metadata",
        "cloudwatch_analyze_metric",
        "cloudwatch_get_recommended_metric_alarms",
        "cloudwatch_get_active_alarms",
        "cloudwatch_get_alarm_history",
    }
)

# Default allow-list: built-in + known MCP read-only tools.
DEFAULT_READ_ONLY_ALLOWED_TOOLS = BUILTIN_READ_ONLY_TOOLS | MCP_READ_ONLY_TOOL_NAMES

# Mutating verbs (word boundaries) for rule-based input classification.
_MUTATING_VERBS = re.compile(
    r"\b(create|delete|update|put|set|modify|remove|destroy|terminate|disable|enable)\b",
    re.IGNORECASE,
)
# Informational patterns: user is asking how/what happens, not requesting the action.
_INFORMATIONAL_PATTERNS = re.compile(
    r"\b(how\s+to|how\s+do\s+i|what\s+happens\s+if|can\s+you\s+explain|explain\s+how)\b",
    re.IGNORECASE,
)


def is_mutating_intent(text: str) -> bool:
    """
    Return True if the user message appears to request a mutating action (create, delete, etc.).

    Uses rule-based detection: mutating verbs; treats "how to...", "what happens if..." as
    informational (returns False). Normalizes input (lowercase, strip).
    """
    if not text or not isinstance(text, str):
        return False
    normalized = text.strip().lower()
    if not normalized:
        return False
    if _INFORMATIONAL_PATTERNS.search(normalized):
        return False
    return bool(_MUTATING_VERBS.search(normalized))


def get_default_allowed_tools() -> frozenset[str]:
    """Return the default read-only tool allow-list (built-in + known MCP tools)."""
    return DEFAULT_READ_ONLY_ALLOWED_TOOLS


class ReadOnlyToolGuardrail:
    """
    Strands HookProvider that blocks any tool not in the read-only allow-list.

    When a disallowed tool is about to run, sets event.cancel_tool to a friendly message.
    """

    def __init__(self, allowed_tools: frozenset[str] | None = None) -> None:
        self._allowed = allowed_tools if allowed_tools is not None else get_default_allowed_tools()

    def register_hooks(self, registry: HookRegistry, **kwargs: object) -> None:
        registry.add_callback(BeforeToolCallEvent, self._intercept_tool)

    def _intercept_tool(self, event: BeforeToolCallEvent) -> None:
        tool_use = getattr(event, "tool_use", None)
        if not isinstance(tool_use, dict):
            return
        name = tool_use.get("name")
        if name is None or name not in self._allowed:
            event.cancel_tool = MESSAGE_TOOL_BLOCKED
