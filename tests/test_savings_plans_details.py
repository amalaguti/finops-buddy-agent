from __future__ import annotations

from unittest.mock import MagicMock

from finops_buddy.costs import get_savings_plans_per_plan_details


def test_get_savings_plans_per_plan_details_flattens_items():
    session = MagicMock()
    ce = session.client.return_value
    ce.get_savings_plans_utilization_details.side_effect = [
        {
            "SavingsPlansUtilizationDetails": [
                {
                    "SavingsPlanArn": "arn:aws:savingsplans::123456789012:savingsplan/sp-abc",
                    "Attributes": {"region": "us-east-1", "paymentOption": "All Upfront"},
                    "Utilization": {
                        "TotalCommitment": "100.0",
                        "UsedCommitment": "80.0",
                        "UnusedCommitment": "20.0",
                        "UtilizationPercentage": "80.0",
                    },
                    "Savings": {
                        "NetSavings": "10.0",
                        "OnDemandCostEquivalent": "90.0",
                    },
                    "AmortizedCommitment": {
                        "AmortizedRecurringCommitment": "0.0",
                        "AmortizedUpfrontCommitment": "100.0",
                        "TotalAmortizedCommitment": "100.0",
                    },
                }
            ],
            "NextToken": None,
        }
    ]

    details = get_savings_plans_per_plan_details(session, months=1)

    assert len(details) == 1
    item = details[0]
    assert item["savings_plan_arn"].endswith("sp-abc")
    assert item["total_commitment"] == "100.0"
    assert item["used_commitment"] == "80.0"
    assert item["utilization_percentage"] == "80.0"
