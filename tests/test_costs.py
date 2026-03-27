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
    get_savings_plans_purchase_recommendations_dashboard,
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


def test_get_savings_plans_purchase_recommendations_uses_payer_and_lookback():
    """Matrix call uses THIRTY_DAYS lookback and PAYER scope (no region filter)."""
    ce = Mock()
    ce.get_savings_plans_purchase_recommendation.return_value = {
        "SavingsPlansPurchaseRecommendation": {
            "SavingsPlansPurchaseRecommendationDetails": [
                {
                    "AccountId": "123456789012",
                    "HourlyCommitmentToPurchase": "0.1",
                    "EstimatedMonthlySavingsAmount": "50",
                    "CurrencyCode": "USD",
                    "SavingsPlansDetails": {"Region": "us-east-1"},
                }
            ],
        },
    }
    session = Mock()
    session.client.return_value = ce
    with patch("finops_buddy.costs._SAVINGS_PLANS_PURCHASE_TYPES", ("COMPUTE_SP",)):
        with patch("finops_buddy.costs._TERM_IN_YEARS_SP_PURCHASE", ("ONE_YEAR",)):
            with patch("finops_buddy.costs._PAYMENT_OPTIONS_SP_PURCHASE", ("NO_UPFRONT",)):
                out = get_savings_plans_purchase_recommendations_dashboard(session)
    assert out["lookback_period_in_days"] == "THIRTY_DAYS"
    assert out["account_scope"] == "PAYER"
    assert out["matrix_term_in_years"] is None
    assert out["matrix_payment_option"] is None
    assert len(out["recommendations"]) == 1
    assert out["recommendations"][0]["hourly_commitment_to_purchase"] == 0.1
    kwargs = ce.get_savings_plans_purchase_recommendation.call_args[1]
    assert kwargs["AccountScope"] == "PAYER"
    assert kwargs["LookbackPeriodInDays"] == "THIRTY_DAYS"
    assert "Filter" not in kwargs


def test_get_savings_plans_purchase_recommendations_respects_lookback_parameter():
    """WHEN lookback_period_in_days is SIXTY_DAYS THEN CE uses it."""
    ce = Mock()
    ce.get_savings_plans_purchase_recommendation.return_value = {
        "SavingsPlansPurchaseRecommendation": {
            "SavingsPlansPurchaseRecommendationDetails": [
                {
                    "HourlyCommitmentToPurchase": "0.1",
                    "EstimatedMonthlySavingsAmount": "50",
                    "CurrencyCode": "USD",
                }
            ],
        },
    }
    session = Mock()
    session.client.return_value = ce
    with patch("finops_buddy.costs._SAVINGS_PLANS_PURCHASE_TYPES", ("COMPUTE_SP",)):
        with patch("finops_buddy.costs._TERM_IN_YEARS_SP_PURCHASE", ("ONE_YEAR",)):
            with patch("finops_buddy.costs._PAYMENT_OPTIONS_SP_PURCHASE", ("NO_UPFRONT",)):
                out = get_savings_plans_purchase_recommendations_dashboard(
                    session, lookback_period_in_days="SIXTY_DAYS"
                )
    assert out["lookback_period_in_days"] == "SIXTY_DAYS"
    assert (
        ce.get_savings_plans_purchase_recommendation.call_args[1]["LookbackPeriodInDays"]
        == "SIXTY_DAYS"
    )


def test_get_savings_plans_purchase_recommendations_rejects_invalid_lookback():
    """WHEN lookback_period_in_days is invalid THEN ValueError."""
    session = Mock()
    with pytest.raises(ValueError, match="Invalid lookback"):
        get_savings_plans_purchase_recommendations_dashboard(
            session, lookback_period_in_days="NINETY_DAYS"
        )


def test_get_savings_plans_purchase_recommendations_uses_linked_when_account_scope_linked():
    """WHEN account_scope is LINKED THEN CE calls use AccountScope LINKED."""
    ce = Mock()
    ce.get_savings_plans_purchase_recommendation.return_value = {
        "SavingsPlansPurchaseRecommendation": {
            "SavingsPlansPurchaseRecommendationDetails": [
                {
                    "HourlyCommitmentToPurchase": "0.1",
                    "EstimatedMonthlySavingsAmount": "50",
                    "CurrencyCode": "USD",
                }
            ],
        },
    }
    session = Mock()
    session.client.return_value = ce
    with patch("finops_buddy.costs._SAVINGS_PLANS_PURCHASE_TYPES", ("COMPUTE_SP",)):
        with patch("finops_buddy.costs._TERM_IN_YEARS_SP_PURCHASE", ("ONE_YEAR",)):
            with patch("finops_buddy.costs._PAYMENT_OPTIONS_SP_PURCHASE", ("NO_UPFRONT",)):
                out = get_savings_plans_purchase_recommendations_dashboard(
                    session, account_scope="LINKED"
                )
    assert out["account_scope"] == "LINKED"
    kwargs = ce.get_savings_plans_purchase_recommendation.call_args[1]
    assert kwargs["AccountScope"] == "LINKED"


def test_get_savings_plans_purchase_recommendations_filtered_term_payment():
    """WHEN term_in_years and payment_option set THEN only that slice of the matrix is requested."""
    ce = Mock()
    ce.get_savings_plans_purchase_recommendation.return_value = {
        "SavingsPlansPurchaseRecommendation": {
            "SavingsPlansPurchaseRecommendationDetails": [
                {
                    "HourlyCommitmentToPurchase": "0.1",
                    "EstimatedMonthlySavingsAmount": "50",
                    "CurrencyCode": "USD",
                }
            ],
        },
    }
    session = Mock()
    session.client.return_value = ce
    with patch("finops_buddy.costs._SAVINGS_PLANS_PURCHASE_TYPES", ("COMPUTE_SP",)):
        out = get_savings_plans_purchase_recommendations_dashboard(
            session,
            term_in_years="THREE_YEARS",
            payment_option="ALL_UPFRONT",
        )
    assert out["matrix_term_in_years"] == "THREE_YEARS"
    assert out["matrix_payment_option"] == "ALL_UPFRONT"
    assert ce.get_savings_plans_purchase_recommendation.call_count == 1
    kwargs = ce.get_savings_plans_purchase_recommendation.call_args[1]
    assert kwargs["TermInYears"] == "THREE_YEARS"
    assert kwargs["PaymentOption"] == "ALL_UPFRONT"


def test_get_savings_plans_purchase_recommendations_rejects_partial_matrix_filter():
    """WHEN only one of term_in_years / payment_option is set THEN ValueError."""
    session = Mock()
    with pytest.raises(ValueError, match="both"):
        get_savings_plans_purchase_recommendations_dashboard(
            session, term_in_years="ONE_YEAR", payment_option=None
        )


def test_get_savings_plans_purchase_recommendations_partial_when_one_cell_fails():
    """WHEN some matrix calls fail and others succeed THEN partial rows and errors."""
    ce = Mock()
    ce.get_savings_plans_purchase_recommendation.side_effect = [
        ClientError({"Error": {"Code": "Throttling", "Message": "slow"}}, "GetSPPurchase"),
        {
            "SavingsPlansPurchaseRecommendation": {
                "SavingsPlansPurchaseRecommendationDetails": [
                    {
                        "HourlyCommitmentToPurchase": "1",
                        "EstimatedMonthlySavingsAmount": "10",
                        "CurrencyCode": "USD",
                    }
                ],
            },
        },
    ]
    session = Mock()
    session.client.return_value = ce
    with patch(
        "finops_buddy.costs._SAVINGS_PLANS_PURCHASE_TYPES",
        ("COMPUTE_SP", "EC2_INSTANCE_SP"),
    ):
        with patch("finops_buddy.costs._TERM_IN_YEARS_SP_PURCHASE", ("ONE_YEAR",)):
            with patch("finops_buddy.costs._PAYMENT_OPTIONS_SP_PURCHASE", ("NO_UPFRONT",)):
                out = get_savings_plans_purchase_recommendations_dashboard(session)
    assert len(out["recommendations"]) == 1
    assert len(out["errors"]) == 1
    assert out["errors"][0]["error_code"] == "Throttling"


def test_get_savings_plans_purchase_recommendations_raises_when_all_access_denied():
    """WHEN every matrix cell is access denied THEN CostExplorerError."""
    ce = Mock()
    ce.get_savings_plans_purchase_recommendation.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "nope"}},
        "GetSPPurchase",
    )
    session = Mock()
    session.client.return_value = ce
    with patch("finops_buddy.costs._SAVINGS_PLANS_PURCHASE_TYPES", ("COMPUTE_SP",)):
        with patch("finops_buddy.costs._TERM_IN_YEARS_SP_PURCHASE", ("ONE_YEAR",)):
            with patch("finops_buddy.costs._PAYMENT_OPTIONS_SP_PURCHASE", ("NO_UPFRONT",)):
                with pytest.raises(CostExplorerError) as exc_info:
                    get_savings_plans_purchase_recommendations_dashboard(session)
    assert "GetSavingsPlansPurchaseRecommendation" in str(exc_info.value)
