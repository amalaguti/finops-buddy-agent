"""Tests for Cost Explorer helpers."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

from finops_buddy.costs import (
    CostExplorerError,
    get_costs_by_linked_account,
    get_costs_by_service_aws_only,
    get_costs_marketplace,
    get_linked_account_ids,
    get_savings_plans_utilization_coverage,
)


def test_get_linked_account_ids_collects_all_pages():
    """Linked account helper returns account ids across paginated responses."""
    ce_client = Mock()
    ce_client.get_dimension_values.side_effect = [
        {
            "DimensionValues": [{"Value": "111122223333"}],
            "NextPageToken": "next",
        },
        {
            "DimensionValues": [{"Value": "444455556666"}],
        },
    ]
    session = Mock()
    session.client.return_value = ce_client

    account_ids = get_linked_account_ids(session)

    assert account_ids == {"111122223333", "444455556666"}
    assert ce_client.get_dimension_values.call_count == 2


def test_get_linked_account_ids_raises_friendly_error_on_access_denied():
    """Linked account helper wraps CE access denied in CostExplorerError."""
    ce_client = Mock()
    ce_client.get_dimension_values.side_effect = ClientError(
        {
            "Error": {
                "Code": "AccessDeniedException",
                "Message": "nope",
            },
        },
        "GetDimensionValues",
    )
    session = Mock()
    session.client.return_value = ce_client

    with pytest.raises(CostExplorerError) as exc_info:
        get_linked_account_ids(session)

    assert "ce:GetDimensionValues" in str(exc_info.value)


def test_get_costs_by_service_aws_only_uses_billing_entity_filter():
    """get_costs_by_service_aws_only calls CE with BILLING_ENTITY=AWS and GroupBy SERVICE."""
    ce = Mock()
    ce.get_cost_and_usage.return_value = {
        "ResultsByTime": [
            {
                "Groups": [
                    {"Keys": ["Amazon S3"], "Metrics": {"UnblendedCost": {"Amount": "10.5"}}},
                ],
            },
        ],
    }
    session = Mock()
    session.client.return_value = ce
    with patch(
        "finops_buddy.costs._current_month_range", return_value=("2025-03-01", "2025-04-01")
    ):
        rows = get_costs_by_service_aws_only(session)
    assert rows == [("Amazon S3", Decimal("10.5"))]
    call_kw = ce.get_cost_and_usage.call_args[1]
    assert call_kw["GroupBy"] == [{"Type": "DIMENSION", "Key": "SERVICE"}]
    assert call_kw["Filter"] == {"Dimensions": {"Key": "BILLING_ENTITY", "Values": ["AWS"]}}


def test_get_costs_by_linked_account_returns_account_costs():
    """get_costs_by_linked_account returns list of (account_id, cost) sorted descending."""
    ce = Mock()
    ce.get_cost_and_usage.return_value = {
        "ResultsByTime": [
            {
                "Groups": [
                    {"Keys": ["123456789012"], "Metrics": {"UnblendedCost": {"Amount": "100"}}},
                    {"Keys": ["111111111111"], "Metrics": {"UnblendedCost": {"Amount": "50"}}},
                ],
            },
        ],
    }
    session = Mock()
    session.client.return_value = ce
    with patch(
        "finops_buddy.costs._current_month_range", return_value=("2025-03-01", "2025-04-01")
    ):
        rows = get_costs_by_linked_account(session)
    assert rows == [("123456789012", Decimal("100")), ("111111111111", Decimal("50"))]
    call_kw = ce.get_cost_and_usage.call_args[1]
    assert call_kw["GroupBy"] == [{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}]


def test_get_costs_marketplace_uses_marketplace_filter():
    """get_costs_marketplace calls CE with BILLING_ENTITY=AWS Marketplace."""
    ce = Mock()
    ce.get_cost_and_usage.return_value = {"ResultsByTime": []}
    session = Mock()
    session.client.return_value = ce
    with patch(
        "finops_buddy.costs._current_month_range", return_value=("2025-03-01", "2025-04-01")
    ):
        rows = get_costs_marketplace(session)
    assert rows == []
    call_kw = ce.get_cost_and_usage.call_args[1]
    assert call_kw["Filter"] == {
        "Dimensions": {"Key": "BILLING_ENTITY", "Values": ["AWS Marketplace"]},
    }


def test_get_savings_plans_utilization_coverage_returns_default_on_error():
    """get_savings_plans_utilization_coverage returns zeroed dict on ClientError."""
    session = Mock()
    session.client.return_value.get_savings_plans_utilization.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "nope"}},
        "GetSavingsPlansUtilization",
    )
    result = get_savings_plans_utilization_coverage(session, months=1)
    assert result["utilization_percentage"] == 0.0
    assert result["coverage_percentage"] == 0.0
    assert result["period_months"] == 1
