"""Cost tools and export tools for the Strands agent."""

from __future__ import annotations

from decimal import Decimal

import boto3

from finops_buddy.agent.conversation_printer import (
    export_pdf,
    export_xlsx_from_table,
    get_output_path,
)
from finops_buddy.costs import (
    CostExplorerError,
    get_costs_by_service,
    get_costs_by_service_aws_only,
    get_costs_for_date_range,
)
from finops_buddy.dates import (
    MAX_COST_LOOKBACK_DAYS,
    clamp_cost_date_range,
    current_month_range,
    get_date_constraints_summary,
    is_range_within_cost_lookback,
    last_biweekly_range,
    last_month_range,
    last_week_range,
    previous_biweekly_range,
    previous_week_range,
)


def _format_costs(rows: list[tuple[str, Decimal]], period_label: str = "") -> str:
    """Format (service, cost) list as a string for the agent."""
    lines = [f"Period: {period_label}" if period_label else "Costs by service:"]
    total = sum(c for _, c in rows)
    for svc, cost in rows[:20]:  # top 20
        lines.append(f"  {svc}: {cost:.2f}")
    if len(rows) > 20:
        lines.append(f"  ... and {len(rows) - 20} more services")
    lines.append(f"Total: {total:.2f}")
    return "\n".join(lines)


def create_cost_tools(session: boto3.Session, include_cost_tools: bool = True) -> list:
    """
    Create Strands-compatible cost tools that use the given AWS session.
    Returns a list of tool functions to pass to Agent(tools=...).
    When include_cost_tools is False, returns only get_current_date (for use when
    cost queries are handled by an MCP server, e.g. AWS Billing and Cost Management).
    """
    from strands import tool

    @tool
    def get_current_date() -> str:
        """
        Get today's date and FinOps date constraints. Call this when you need the current
        date or to explain what date ranges are allowed. Cost data: only last 3 months.
        Resource-level data (e.g. by resource ID): only last 14 days in AWS.
        """
        return get_date_constraints_summary()

    @tool
    def current_period_costs() -> str:
        """
        Get AWS costs for the current month by service (UnblendedCost), AWS services only
        (excludes AWS Marketplace). Use when the user asks for current month, this month,
        or current period costs.
        """
        try:
            rows = get_costs_by_service_aws_only(session)
            return _format_costs(rows, "Current month (AWS services only)")
        except CostExplorerError as e:
            return f"Error retrieving costs: {e}"

    @tool
    def costs_for_date_range(start_date: str, end_date: str) -> str:
        """
        Get AWS costs by service for a custom date range. Do not query older than 3 months;
        start_date is clamped to the last 90 days if older.
        Args:
            start_date: Start date (YYYY-MM-DD), inclusive.
            end_date: End date (YYYY-MM-DD), exclusive (last day included is end_date - 1).
        """
        try:
            start_clamped, end_clamped = clamp_cost_date_range(start_date, end_date)
            if not is_range_within_cost_lookback(start_date, end_date):
                note = (
                    f" (Requested {start_date}–{end_date} was limited to last "
                    f"{MAX_COST_LOOKBACK_DAYS} days.)"
                )
            else:
                note = ""
            rows = get_costs_for_date_range(session, start_clamped, end_clamped)
            return _format_costs(rows, f"{start_clamped} to {end_clamped}{note}")
        except ValueError as e:
            return f"Invalid date format (use YYYY-MM-DD): {e}"
        except CostExplorerError as e:
            return f"Error retrieving costs: {e}"

    @tool
    def month_over_month_costs() -> str:
        """
        Get AWS costs for the previous month and the current month for comparison.
        Use when the user asks for month-over-month, MoM, or compare this month to last month.
        """
        try:
            prev_start, prev_end = last_month_range()
            curr_start, curr_end = current_month_range()
            prev_rows = get_costs_by_service(session, start=prev_start, end=prev_end)
            curr_rows = get_costs_by_service(session, start=curr_start, end=curr_end)
            prev_total = sum(c for _, c in prev_rows)
            curr_total = sum(c for _, c in curr_rows)
            diff = curr_total - prev_total
            pct = (float(diff) / float(prev_total) * 100) if prev_total else 0
            lines = [
                "Month-over-month comparison (UnblendedCost):",
                f"  Previous month ({prev_start} to {prev_end}): {prev_total:.2f}",
                f"  Current month ({curr_start} to {curr_end}): {curr_total:.2f}",
                f"  Change: {diff:+.2f} ({pct:+.1f}%)",
            ]
            return "\n".join(lines)
        except CostExplorerError as e:
            return f"Error retrieving costs: {e}"

    @tool
    def week_over_week_costs() -> str:
        """
        Get AWS costs for the last 7 days and the previous 7 days for comparison.
        Use when the user asks for week-over-week, WoW, or compare last week to this week.
        """
        try:
            last_start, last_end = last_week_range()
            prev_start, prev_end = previous_week_range()
            last_rows = get_costs_for_date_range(session, last_start, last_end)
            prev_rows = get_costs_for_date_range(session, prev_start, prev_end)
            last_total = sum(c for _, c in last_rows)
            prev_total = sum(c for _, c in prev_rows)
            diff = last_total - prev_total
            pct = (float(diff) / float(prev_total) * 100) if prev_total else 0
            lines = [
                "Week-over-week comparison (UnblendedCost):",
                f"  Previous 7 days ({prev_start} to {prev_end}): {prev_total:.2f}",
                f"  Last 7 days ({last_start} to {last_end}): {last_total:.2f}",
                f"  Change: {diff:+.2f} ({pct:+.1f}%)",
            ]
            return "\n".join(lines)
        except CostExplorerError as e:
            return f"Error retrieving costs: {e}"

    @tool
    def biweekly_over_biweekly_costs() -> str:
        """
        Get AWS costs for the last 14 days and the previous 14 days for comparison.
        Use when the user asks for biweekly comparison or last two weeks vs previous two weeks.
        """
        try:
            last_start, last_end = last_biweekly_range()
            prev_start, prev_end = previous_biweekly_range()
            last_rows = get_costs_for_date_range(session, last_start, last_end)
            prev_rows = get_costs_for_date_range(session, prev_start, prev_end)
            last_total = sum(c for _, c in last_rows)
            prev_total = sum(c for _, c in prev_rows)
            diff = last_total - prev_total
            pct = (float(diff) / float(prev_total) * 100) if prev_total else 0
            lines = [
                "Biweekly-over-biweekly comparison (UnblendedCost):",
                f"  Previous 14 days ({prev_start} to {prev_end}): {prev_total:.2f}",
                f"  Last 14 days ({last_start} to {last_end}): {last_total:.2f}",
                f"  Change: {diff:+.2f} ({pct:+.1f}%)",
            ]
            return "\n".join(lines)
        except CostExplorerError as e:
            return f"Error retrieving costs: {e}"

    if not include_cost_tools:
        return [get_current_date]
    return [
        get_current_date,
        current_period_costs,
        costs_for_date_range,
        month_over_month_costs,
        week_over_week_costs,
        biweekly_over_biweekly_costs,
    ]


def create_export_tools() -> list:
    """
    Create agent tools for exporting formatted content to PDF or Excel.
    Use when the user asks to save/export the conversation (or part of it):
    the agent formats the content and calls these tools.
    """
    from strands import tool

    @tool
    def export_to_pdf(markdown_content: str, filename: str) -> str:
        """
        Save markdown content as a PDF file. Use when the user asks to export or save
        the conversation (or a summary) as PDF. Format the conversation as clear
        markdown (sections, headings, bullet points) before calling. Filename should
        include .pdf (e.g. 20250311-summary.pdf). File is saved in the current
        working directory.
        """
        path = get_output_path(filename.strip())
        ok, msg = export_pdf(markdown_content.strip(), path)
        return msg if ok else f"PDF export failed: {msg}"

    @tool
    def export_to_excel(
        data: list[list],
        filename: str,
        sheet_name: str = "Export",
    ) -> str:
        """
        Save tabular data as an Excel file (.xlsx). Use when the user asks to export
        or save the conversation or cost/analysis as a spreadsheet. Pass a list of
        rows: first row = column headers, then one row per data point so users can
        filter and sort. Make the spreadsheet useful for analysis: for cost data use
        columns like Service, Region, Cost, Period; for Q&A use Question, Answer. Do
        NOT use a two-column Topic/Summary dump of key-value pairs (e.g. Request, Period,
        Metric as row labels)—that is not analyzable. Prefer one row per service, per
        region, or per Q&A with meaningful column headers. Filename should include
        .xlsx. File is saved in the current working directory.
        """
        path = get_output_path(filename.strip())
        try:
            export_xlsx_from_table(
                data,
                path,
                sheet_name=(sheet_name or "Export")[:31],
            )
            return str(path)
        except Exception as e:
            return f"Excel export failed: {e}"

    return [export_to_pdf, export_to_excel]
