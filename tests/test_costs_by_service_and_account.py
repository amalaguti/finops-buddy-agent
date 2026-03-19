from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

from finops_buddy.costs import get_costs_by_service_and_account


def test_get_costs_by_service_and_account_groups_by_linked_account():
    session = MagicMock()
    ce = session.client.return_value
    ce.get_cost_and_usage.side_effect = [
        {
            "ResultsByTime": [
                {
                    "Groups": [
                        {
                            "Keys": ["111111111111"],
                            "Metrics": {"UnblendedCost": {"Amount": "10.0"}},
                        },
                        {
                            "Keys": ["222222222222"],
                            "Metrics": {"UnblendedCost": {"Amount": "5.0"}},
                        },
                    ]
                }
            ],
            "NextPageToken": None,
        }
    ]

    rows = get_costs_by_service_and_account(
        session, service_name="Amazon EC2", start="2026-03-01", end="2026-04-01"
    )

    assert rows == [("111111111111", Decimal("10.0")), ("222222222222", Decimal("5.0"))]
