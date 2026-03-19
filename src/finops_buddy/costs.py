"""Current-month cost retrieval by service (Cost Explorer)."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError


class CostExplorerError(Exception):
    """Cost Explorer API or access error."""


def _current_month_range() -> tuple[str, str]:
    """
    Return (start, end) for current month to date (MTD).

    Start = first day of current month. End = tomorrow (exclusive), so Cost Explorer
    includes all costs through today. Used by dashboard and cost-by-service/account APIs.
    """
    today = date.today()
    start = today.replace(day=1)
    end = today + timedelta(days=1)
    return start.isoformat(), end.isoformat()


def get_linked_account_ids(
    session: boto3.Session,
    *,
    start: str | None = None,
    end: str | None = None,
) -> set[str]:
    """
    Return linked account IDs visible to the caller via Cost Explorer.

    Uses the `LINKED_ACCOUNT` dimension from Cost Explorer. Best used from the
    payer/master profile, where one call can discover many linked accounts.
    """
    if start is None or end is None:
        start, end = _current_month_range()
    ce = session.client("ce")
    account_ids: set[str] = set()
    token = None
    try:
        while True:
            kwargs = {
                "TimePeriod": {"Start": start, "End": end},
                "Context": "COST_AND_USAGE",
                "Dimension": "LINKED_ACCOUNT",
            }
            if token:
                kwargs["NextPageToken"] = token
            resp = ce.get_dimension_values(**kwargs)
            for item in resp.get("DimensionValues", []):
                value = (item.get("Value") or "").strip()
                if value:
                    account_ids.add(value)
            token = resp.get("NextPageToken")
            if not token:
                break
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        msg = e.response.get("Error", {}).get("Message", str(e))
        if code == "AccessDeniedException":
            raise CostExplorerError(
                "Access denied to Cost Explorer linked account discovery. Ensure your "
                "credentials have ce:GetDimensionValues permission."
            ) from e
        raise CostExplorerError(f"Cost Explorer error ({code}): {msg}") from e
    return account_ids


def get_costs_by_service(
    session: boto3.Session,
    *,
    start: str | None = None,
    end: str | None = None,
) -> list[tuple[str, Decimal]]:
    """
    Call Cost Explorer GetCostAndUsage for the given (or current) month, grouped by SERVICE.

    Returns list of (service_name, cost) sorted by cost descending.
    Uses UnblendedCost. Raises on API errors; caller can catch and show user message.
    """
    if start is None or end is None:
        start, end = _current_month_range()
    ce = session.client("ce")
    results: list[tuple[str, Decimal]] = []
    try:
        _fetch_all_pages(ce, start, end, results)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        msg = e.response.get("Error", {}).get("Message", str(e))
        if code == "AccessDeniedException":
            raise CostExplorerError(
                "Access denied to Cost Explorer. Ensure the account has Cost Explorer "
                "enabled and your credentials have ce:GetCostAndUsage permission."
            ) from e
        raise CostExplorerError(f"Cost Explorer error ({code}): {msg}") from e
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def _fetch_all_pages(
    ce,
    start: str,
    end: str,
    results: list,
    *,
    group_by_key: str = "SERVICE",
    filter_expr: dict | None = None,
) -> None:
    """
    Fetch cost and usage with optional Filter and GroupBy; append (key, cost) to results.
    group_by_key: dimension key (e.g. SERVICE, LINKED_ACCOUNT). filter_expr: optional
    Cost Explorer Filter expression (e.g. BILLING_ENTITY = "AWS").
    """
    token = None
    while True:
        kwargs = {
            "TimePeriod": {"Start": start, "End": end},
            "Granularity": "MONTHLY",
            "Metrics": ["UnblendedCost"],
            "GroupBy": [{"Type": "DIMENSION", "Key": group_by_key}],
        }
        if filter_expr is not None:
            kwargs["Filter"] = filter_expr
        if token:
            kwargs["NextPageToken"] = token
        resp = ce.get_cost_and_usage(**kwargs)
        for result in resp.get("ResultsByTime", []):
            for group in result.get("Groups", []):
                keys = group.get("Keys", [])
                metrics = group.get("Metrics", {})
                if keys and "UnblendedCost" in metrics:
                    dim_value = keys[0]
                    amount = metrics["UnblendedCost"].get("Amount", "0")
                    results.append((dim_value, Decimal(amount)))
        token = resp.get("NextPageToken")
        if not token:
            break


def get_costs_by_service_aws_only(
    session: boto3.Session,
    *,
    start: str | None = None,
    end: str | None = None,
) -> list[tuple[str, Decimal]]:
    """
    Current-month costs grouped by SERVICE, excluding AWS Marketplace (BILLING_ENTITY = "AWS" only).
    Returns list of (service_name, cost) sorted by cost descending.
    """
    if start is None or end is None:
        start, end = _current_month_range()
    ce = session.client("ce")
    results: list[tuple[str, Decimal]] = []
    filter_aws_only = {"Dimensions": {"Key": "BILLING_ENTITY", "Values": ["AWS"]}}
    try:
        _fetch_all_pages(
            ce,
            start,
            end,
            results,
            group_by_key="SERVICE",
            filter_expr=filter_aws_only,
        )
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        msg = e.response.get("Error", {}).get("Message", str(e))
        if code == "AccessDeniedException":
            raise CostExplorerError(
                "Access denied to Cost Explorer. Ensure the account has Cost Explorer "
                "enabled and your credentials have ce:GetCostAndUsage permission."
            ) from e
        raise CostExplorerError(f"Cost Explorer error ({code}): {msg}") from e
    # Aggregate by service (MONTHLY can still have multiple rows per service across pages)
    by_key: dict[str, Decimal] = {}
    for k, v in results:
        by_key[k] = by_key.get(k, Decimal("0")) + v
    aggregated = sorted(by_key.items(), key=lambda x: x[1], reverse=True)
    return aggregated


def get_costs_by_linked_account(
    session: boto3.Session,
    *,
    start: str | None = None,
    end: str | None = None,
) -> list[tuple[str, Decimal]]:
    """
    Current-month costs grouped by LINKED_ACCOUNT.
    Returns list of (account_id, cost) sorted by cost descending.
    """
    if start is None or end is None:
        start, end = _current_month_range()
    ce = session.client("ce")
    results: list[tuple[str, Decimal]] = []
    try:
        _fetch_all_pages(ce, start, end, results, group_by_key="LINKED_ACCOUNT")
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        msg = e.response.get("Error", {}).get("Message", str(e))
        if code == "AccessDeniedException":
            raise CostExplorerError(
                "Access denied to Cost Explorer. Ensure the account has Cost Explorer "
                "enabled and your credentials have ce:GetCostAndUsage permission."
            ) from e
        raise CostExplorerError(f"Cost Explorer error ({code}): {msg}") from e
    by_key: dict[str, Decimal] = {}
    for k, v in results:
        by_key[k] = by_key.get(k, Decimal("0")) + v
    return sorted(by_key.items(), key=lambda x: x[1], reverse=True)


def get_costs_by_service_and_account(
    session: boto3.Session,
    service_name: str,
    *,
    start: str | None = None,
    end: str | None = None,
) -> list[tuple[str, Decimal]]:
    """
    Current-month costs for a single AWS service, grouped by linked account.

    Uses Cost Explorer with a filter on SERVICE = service_name and GROUP BY LINKED_ACCOUNT.
    Returns list of (account_id, cost) sorted by cost descending.
    """
    if start is None or end is None:
        start, end = _current_month_range()
    ce = session.client("ce")
    results: list[tuple[str, Decimal]] = []
    filter_expr = {"Dimensions": {"Key": "SERVICE", "Values": [service_name]}}
    try:
        _fetch_all_pages(
            ce,
            start,
            end,
            results,
            group_by_key="LINKED_ACCOUNT",
            filter_expr=filter_expr,
        )
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        msg = e.response.get("Error", {}).get("Message", str(e))
        if code == "AccessDeniedException":
            raise CostExplorerError(
                "Access denied to Cost Explorer. Ensure the account has Cost Explorer "
                "enabled and your credentials have ce:GetCostAndUsage permission."
            ) from e
        raise CostExplorerError(f"Cost Explorer error ({code}): {msg}") from e
    by_account: dict[str, Decimal] = {}
    for account_id, amount in results:
        by_account[account_id] = by_account.get(account_id, Decimal("0")) + amount
    return sorted(by_account.items(), key=lambda x: x[1], reverse=True)


def get_costs_by_account_and_service(
    session: boto3.Session,
    account_id: str,
    *,
    start: str | None = None,
    end: str | None = None,
) -> list[tuple[str, Decimal]]:
    """
    Current-month costs for a single linked account, grouped by AWS service.

    Uses Cost Explorer with a filter on LINKED_ACCOUNT = account_id and GROUP BY SERVICE.
    Returns list of (service_name, cost) sorted by cost descending.
    """
    if start is None or end is None:
        start, end = _current_month_range()
    ce = session.client("ce")
    results: list[tuple[str, Decimal]] = []
    filter_expr = {"Dimensions": {"Key": "LINKED_ACCOUNT", "Values": [account_id]}}
    try:
        _fetch_all_pages(
            ce,
            start,
            end,
            results,
            group_by_key="SERVICE",
            filter_expr=filter_expr,
        )
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        msg = e.response.get("Error", {}).get("Message", str(e))
        if code == "AccessDeniedException":
            raise CostExplorerError(
                "Access denied to Cost Explorer. Ensure the account has Cost Explorer "
                "enabled and your credentials have ce:GetCostAndUsage permission."
            ) from e
        raise CostExplorerError(f"Cost Explorer error ({code}): {msg}") from e
    by_service: dict[str, Decimal] = {}
    for service_name, amount in results:
        by_service[service_name] = by_service.get(service_name, Decimal("0")) + amount
    return sorted(by_service.items(), key=lambda x: x[1], reverse=True)


def get_costs_marketplace(
    session: boto3.Session,
    *,
    start: str | None = None,
    end: str | None = None,
) -> list[tuple[str, Decimal]]:
    """
    Current-month costs for AWS Marketplace only (BILLING_ENTITY = "AWS Marketplace"),
    grouped by SERVICE (product). Returns list of (product/service, cost) sorted descending.
    """
    if start is None or end is None:
        start, end = _current_month_range()
    ce = session.client("ce")
    results: list[tuple[str, Decimal]] = []
    filter_marketplace = {"Dimensions": {"Key": "BILLING_ENTITY", "Values": ["AWS Marketplace"]}}
    try:
        _fetch_all_pages(
            ce,
            start,
            end,
            results,
            group_by_key="SERVICE",
            filter_expr=filter_marketplace,
        )
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        msg = e.response.get("Error", {}).get("Message", str(e))
        if code == "AccessDeniedException":
            raise CostExplorerError(
                "Access denied to Cost Explorer. Ensure the account has Cost Explorer "
                "enabled and your credentials have ce:GetCostAndUsage permission."
            ) from e
        raise CostExplorerError(f"Cost Explorer error ({code}): {msg}") from e
    by_key: dict[str, Decimal] = {}
    for k, v in results:
        by_key[k] = by_key.get(k, Decimal("0")) + v
    return sorted(by_key.items(), key=lambda x: x[1], reverse=True)


def _fetch_all_pages_daily(ce, start: str, end: str, results: list) -> None:
    """Fetch cost by service with DAILY granularity; aggregated in-place per (service, amount)."""
    token = None
    while True:
        kwargs = {
            "TimePeriod": {"Start": start, "End": end},
            "Granularity": "DAILY",
            "Metrics": ["UnblendedCost"],
            "GroupBy": [{"Type": "DIMENSION", "Key": "SERVICE"}],
        }
        if token:
            kwargs["NextPageToken"] = token
        resp = ce.get_cost_and_usage(**kwargs)
        for result in resp.get("ResultsByTime", []):
            for group in result.get("Groups", []):
                keys = group.get("Keys", [])
                metrics = group.get("Metrics", {})
                if keys and "UnblendedCost" in metrics:
                    svc = keys[0]
                    amount = metrics["UnblendedCost"].get("Amount", "0")
                    results.append((svc, Decimal(amount)))
        token = resp.get("NextPageToken")
        if not token:
            break


def get_costs_for_date_range(
    session: boto3.Session,
    start: str,
    end: str,
) -> list[tuple[str, Decimal]]:
    """
    Get costs by service for a date range (start inclusive, end exclusive).
    DAILY granularity, aggregated. Returns (service_name, cost) list sorted by cost descending.
    """
    ce = session.client("ce")
    results: list[tuple[str, Decimal]] = []
    try:
        _fetch_all_pages_daily(ce, start, end, results)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        msg = e.response.get("Error", {}).get("Message", str(e))
        if code == "AccessDeniedException":
            raise CostExplorerError(
                "Access denied to Cost Explorer. Ensure the account has Cost Explorer "
                "enabled and your credentials have ce:GetCostAndUsage permission."
            ) from e
        raise CostExplorerError(f"Cost Explorer error ({code}): {msg}") from e
    # Aggregate by service (DAILY returns one row per service per day)
    by_service: dict[str, Decimal] = {}
    for svc, amount in results:
        by_service[svc] = by_service.get(svc, Decimal("0")) + amount
    aggregated = sorted(by_service.items(), key=lambda x: x[1], reverse=True)
    return aggregated


def _trailing_months_range(months: int) -> tuple[str, str]:
    """Return (start, end) for the last N calendar months. End is exclusive."""
    today = date.today()
    # End: first day of current month (so we cover full past months) or tomorrow for "through today"
    # Cost Explorer Savings Plans typically use end = first day of next month for "last full month"
    if months <= 0:
        months = 1
    # Start: go back N months from today
    year, month = today.year, today.month
    for _ in range(months - 1):
        month -= 1
        if month <= 0:
            month += 12
            year -= 1
    start = date(year, month, 1)
    # End: first day after the period; use today + 1 so we include today
    end = today + timedelta(days=1)
    return start.isoformat(), end.isoformat()


def _parse_utilization_pct(util_amt: dict) -> float | None:
    """Extract utilization percentage from Utilization dict; return None if missing.

    AWS returns UtilizationPercentage as a string (e.g. "78.7"); also handle number/dict.
    """
    pct = util_amt.get("UtilizationPercentage")
    if pct is None:
        return None
    if isinstance(pct, (int, float)):
        return float(pct)
    if isinstance(pct, dict) and "Value" in pct:
        return float(pct.get("Value") or 0)
    if isinstance(pct, str) and pct.strip():
        try:
            return float(pct)
        except ValueError:
            pass
    return None


def get_savings_plans_utilization_coverage(
    session: boto3.Session,
    *,
    months: int = 1,
) -> dict:
    """
    Get Savings Plans utilization and coverage for the last 1, 2, or 3 months.

    When months > 1, returns the average utilization and average coverage over
    that period (each month from the API is averaged). When months == 1,
    returns the single month's values.

    Returns dict with utilization_percentage, coverage_percentage, period_months.
    On no Savings Plans or API error, returns zeroed structure without raising.
    """
    if months not in (1, 2, 3):
        months = 1
    start, end = _trailing_months_range(months)
    result = {
        "utilization_percentage": 0.0,
        "coverage_percentage": 0.0,
        "period_months": months,
    }
    try:
        ce = session.client("ce")
        util_resp = ce.get_savings_plans_utilization(
            TimePeriod={"Start": start, "End": end},
            Granularity="MONTHLY",
        )
        by_time_list = util_resp.get("SavingsPlansUtilizationsByTime", [])
        util_values: list[float] = []
        for by_time in by_time_list:
            util_amt = by_time.get("Utilization", {})
            pct = _parse_utilization_pct(util_amt)
            if pct is not None:
                util_values.append(pct)
        if util_values:
            result["utilization_percentage"] = sum(util_values) / len(util_values)

        cov_resp = ce.get_savings_plans_coverage(
            TimePeriod={"Start": start, "End": end},
            Granularity="MONTHLY",
        )
        cov_by_time_list = cov_resp.get("SavingsPlansCoverages", [])
        cov_values: list[float] = []
        for by_time in cov_by_time_list:
            cov_pct = by_time.get("Coverage", {}).get("CoveragePercentage")
            if cov_pct is not None and cov_pct != "":
                try:
                    cov_values.append(float(cov_pct))
                except (TypeError, ValueError):
                    pass
        if cov_values:
            result["coverage_percentage"] = sum(cov_values) / len(cov_values)
    except ClientError:
        pass
    except Exception:
        pass
    return result


def get_savings_plans_per_plan_details(
    session: boto3.Session,
    *,
    months: int = 1,
) -> list[dict]:
    """
    Return per-plan Savings Plans utilization details for the last N months.

    Uses GetSavingsPlansUtilizationDetails grouped by SavingsPlansArn and returns
    a simplified list with key fields for each plan. On access denied or error,
    returns an empty list.
    """
    if months not in (1, 2, 3):
        months = 1
    start, end = _trailing_months_range(months)
    try:
        ce = session.client("ce")
        details: list[dict] = []
        token = None
        while True:
            kwargs = {
                "TimePeriod": {"Start": start, "End": end},
                "DataType": ["ATTRIBUTES", "UTILIZATION", "AMORTIZED_COMMITMENT", "SAVINGS"],
                "MaxResults": 20,
            }
            if token:
                kwargs["NextToken"] = token
            resp = ce.get_savings_plans_utilization_details(**kwargs)
            for item in resp.get("SavingsPlansUtilizationDetails", []):
                arn = item.get("SavingsPlanArn", "")
                attrs = item.get("Attributes", {}) or {}
                util = item.get("Utilization", {}) or {}
                savings = item.get("Savings", {}) or {}
                amort = item.get("AmortizedCommitment", {}) or {}
                details.append(
                    {
                        "savings_plan_arn": arn,
                        "attributes": attrs,
                        "total_commitment": util.get("TotalCommitment"),
                        "used_commitment": util.get("UsedCommitment"),
                        "unused_commitment": util.get("UnusedCommitment"),
                        "utilization_percentage": util.get("UtilizationPercentage"),
                        "net_savings": savings.get("NetSavings"),
                        "on_demand_cost_equivalent": savings.get("OnDemandCostEquivalent"),
                        "amortized_recurring_commitment": amort.get("AmortizedRecurringCommitment"),
                        "amortized_upfront_commitment": amort.get("AmortizedUpfrontCommitment"),
                        "total_amortized_commitment": amort.get("TotalAmortizedCommitment"),
                    }
                )
            token = resp.get("NextToken")
            # Only continue pagination when NextToken is a non-empty string (AWS API).
            # Avoids infinite loop when response is a mock (e.g. MagicMock) with truthy .get("NextToken").
            if not (isinstance(token, str) and token.strip()):
                break
        return details
    except ClientError:
        return []
    except Exception:
        return []
