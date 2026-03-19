"""Tests for table formatting."""

from decimal import Decimal

from finops_buddy.table import format_costs_table


def test_format_costs_table_empty():
    """Empty rows return a message."""
    assert "No cost data" in format_costs_table([])


def test_format_costs_table_with_pct():
    """Table includes Service, Cost, and % columns."""
    rows = [
        ("Amazon EC2", Decimal("100.50")),
        ("Amazon S3", Decimal("25.25")),
    ]
    out = format_costs_table(rows, include_pct=True)
    assert "Service" in out
    assert "Cost" in out
    assert "Amazon EC2" in out
    assert "100.50" in out
    assert "25.25" in out
    assert "Total" in out
    assert "100.0%" in out
