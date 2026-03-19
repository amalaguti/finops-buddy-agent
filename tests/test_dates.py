"""Tests for date helpers (cost 3-month and resource 14-day limits)."""

from datetime import date, timedelta

from finops_buddy.dates import (
    MAX_COST_LOOKBACK_DAYS,
    MAX_RESOURCE_LOOKBACK_DAYS,
    clamp_cost_date_range,
    current_month_range,
    get_date_constraints_summary,
    is_range_within_cost_lookback,
    is_range_within_resource_lookback,
    last_month_range,
    parse_date,
    today_iso,
)


def test_today_iso_format():
    """today_iso returns YYYY-MM-DD."""
    s = today_iso()
    assert len(s) == 10
    assert s[4] == "-" and s[7] == "-"
    assert parse_date(s) == date.today()


def test_current_month_range():
    """current_month_range returns (first day, first day next month)."""
    start, end = current_month_range()
    assert parse_date(start).day == 1
    assert parse_date(end).day == 1
    assert parse_date(end) > parse_date(start)


def test_last_month_range():
    """last_month_range returns previous calendar month."""
    start, end = last_month_range()
    assert parse_date(end) <= date.today()
    assert parse_date(end) > parse_date(start)


def test_clamp_cost_date_range_old_start_clamped():
    """Range starting before 90 days is clamped to 90 days ago."""
    today = date.today()
    old_start = (today - timedelta(days=200)).isoformat()
    end = (today - timedelta(days=1)).isoformat()
    start_c, end_c = clamp_cost_date_range(old_start, end)
    start_d = parse_date(start_c)
    assert start_d >= today - timedelta(days=MAX_COST_LOOKBACK_DAYS)


def test_is_range_within_cost_lookback_true():
    """Range within last 90 days returns True."""
    today = date.today()
    start = (today - timedelta(days=30)).isoformat()
    end = today.isoformat()
    assert is_range_within_cost_lookback(start, end) is True


def test_is_range_within_cost_lookback_false():
    """Range starting before 90 days returns False."""
    today = date.today()
    start = (today - timedelta(days=100)).isoformat()
    end = (today - timedelta(days=50)).isoformat()
    assert is_range_within_cost_lookback(start, end) is False


def test_is_range_within_resource_lookback():
    """Resource lookback is 14 days."""
    today = date.today()
    assert (
        is_range_within_resource_lookback(
            (today - timedelta(days=7)).isoformat(), today.isoformat()
        )
        is True
    )
    assert (
        is_range_within_resource_lookback(
            (today - timedelta(days=20)).isoformat(), today.isoformat()
        )
        is False
    )


def test_get_date_constraints_summary_includes_today_and_limits():
    """Summary includes today and 90 / 14 day limits."""
    s = get_date_constraints_summary()
    assert "Today:" in s
    assert str(MAX_COST_LOOKBACK_DAYS) in s
    assert str(MAX_RESOURCE_LOOKBACK_DAYS) in s
