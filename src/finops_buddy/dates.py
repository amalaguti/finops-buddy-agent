"""
Date helpers for FinOps: current date, ranges, and lookback limits.

- Cost data: do not query older than MAX_COST_LOOKBACK_DAYS (3 months); many accounts are new.
- Resource-level data (e.g. Cost Explorer resource dimension): AWS allows only last 14 days.
"""

from __future__ import annotations

from datetime import date, timedelta

# Cost and usage: max 3 months lookback (accounts may be new).
MAX_COST_LOOKBACK_DAYS = 90
# Resource-level granularity in Cost Explorer: only last 14 days.
MAX_RESOURCE_LOOKBACK_DAYS = 14


def today_iso() -> str:
    """Current date as YYYY-MM-DD."""
    return date.today().isoformat()


def parse_date(s: str) -> date:
    """Parse YYYY-MM-DD to date. Raises ValueError if invalid."""
    return date.fromisoformat(s.strip())


def current_month_range() -> tuple[str, str]:
    """(start, end) for current month. End is exclusive (first day of next month)."""
    today = date.today()
    start = today.replace(day=1)
    if today.month == 12:
        end = today.replace(year=today.year + 1, month=1, day=1)
    else:
        end = today.replace(month=today.month + 1, day=1)
    return start.isoformat(), end.isoformat()


def last_month_range() -> tuple[str, str]:
    """(start, end) for last calendar month. End is exclusive."""
    today = date.today()
    first_this = today.replace(day=1)
    end = first_this
    if first_this.month == 1:
        start = first_this.replace(year=first_this.year - 1, month=12)
    else:
        start = first_this.replace(month=first_this.month - 1)
    return start.isoformat(), end.isoformat()


def last_week_range() -> tuple[str, str]:
    """(start, end) for last 7 days. End is exclusive (tomorrow)."""
    today = date.today()
    end = today + timedelta(days=1)
    start = today - timedelta(days=7)
    return start.isoformat(), end.isoformat()


def previous_week_range() -> tuple[str, str]:
    """(start, end) for the 7 days before last_week_range."""
    today = date.today()
    end = today - timedelta(days=6)
    start = end - timedelta(days=7)
    return start.isoformat(), end.isoformat()


def last_biweekly_range() -> tuple[str, str]:
    """(start, end) for last 14 days. End is exclusive."""
    today = date.today()
    end = today + timedelta(days=1)
    start = today - timedelta(days=14)
    return start.isoformat(), end.isoformat()


def previous_biweekly_range() -> tuple[str, str]:
    """(start, end) for the 14 days before last_biweekly_range."""
    today = date.today()
    end = today - timedelta(days=13)
    start = end - timedelta(days=14)
    return start.isoformat(), end.isoformat()


def clamp_cost_date_range(start: str, end: str) -> tuple[str, str]:
    """
    Clamp a date range to at most MAX_COST_LOOKBACK_DAYS from today.
    Returns (start, end) in YYYY-MM-DD; end remains exclusive.
    If start is older than allowed, start is moved forward so the range
    is at most MAX_COST_LOOKBACK_DAYS and does not extend past today.
    """
    today = date.today()
    max_start = today - timedelta(days=MAX_COST_LOOKBACK_DAYS)
    start_d = parse_date(start)
    end_d = parse_date(end)
    if start_d < max_start:
        start_d = max_start
    if end_d > today + timedelta(days=1):
        end_d = today + timedelta(days=1)
    if start_d >= end_d:
        end_d = start_d + timedelta(days=1)
    return start_d.isoformat(), end_d.isoformat()


def is_range_within_cost_lookback(start: str, end: str) -> bool:
    """True if the range is entirely within the last MAX_COST_LOOKBACK_DAYS."""
    today = date.today()
    max_start = today - timedelta(days=MAX_COST_LOOKBACK_DAYS)
    start_d = parse_date(start)
    return start_d >= max_start


def is_range_within_resource_lookback(start: str, end: str) -> bool:
    """True if the range is within the last MAX_RESOURCE_LOOKBACK_DAYS (14 days)."""
    today = date.today()
    max_start = today - timedelta(days=MAX_RESOURCE_LOOKBACK_DAYS)
    start_d = parse_date(start)
    return start_d >= max_start


def get_date_constraints_summary() -> str:
    """Human-readable summary of date limits for the agent."""
    return (
        f"Today: {today_iso()}. "
        f"Cost/usage data: only last {MAX_COST_LOOKBACK_DAYS} days (3 months); "
        f"resource-level data: only last {MAX_RESOURCE_LOOKBACK_DAYS} days."
    )
