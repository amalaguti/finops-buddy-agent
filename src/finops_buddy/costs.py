"""Current-month cost retrieval by service (Cost Explorer)."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from itertools import product

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


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
            # Avoids infinite loop when mocks return a truthy NextToken.
            if not (isinstance(token, str) and token.strip()):
                break
        return details
    except ClientError:
        return []
    except Exception:
        return []


# Max cost category rules to query per dashboard request (avoid throttling / long latency).
_MAX_COST_CATEGORIES_PER_REQUEST = 25

# Dimension value labels treated as uncategorized for coverage (case-insensitive).
_UNCATEGORIZED_VALUE_KEYS = frozenset(
    {
        "",
        "untagged",
        "not tagged",
        "untagged resources",
        "no cost category",
        "nocostcategory",
        "no_cost_category",
        "no category",
        "not allocated",
        "no tag",
        "notag",
    }
)


def _is_uncategorized_cost_category_value(value_key: str) -> bool:
    """Return True if the CE cost-category dimension value counts as uncategorized."""
    raw = (value_key or "").strip()
    if not raw:
        return True
    norm = raw.lower()
    compact = norm.replace(" ", "").replace("_", "")
    if norm in _UNCATEGORIZED_VALUE_KEYS or compact in _UNCATEGORIZED_VALUE_KEYS:
        return True
    if "untagged" in norm or "nocostcategory" in compact:
        return True
    if norm.startswith("no ") and "cost" in norm and "categor" in norm:
        return True
    return False


def _client_error_to_cost_explorer(e: ClientError, *, operation: str) -> CostExplorerError:
    code = e.response.get("Error", {}).get("Code", "")
    msg = e.response.get("Error", {}).get("Message", str(e))
    if code == "AccessDeniedException":
        return CostExplorerError(
            f"Access denied to Cost Explorer ({operation}). Ensure your credentials have "
            "the required Cost Explorer permissions and Cost Explorer is enabled."
        )
    return CostExplorerError(f"Cost Explorer error ({code}) in {operation}: {msg}")


def _list_cost_category_names(ce, start: str, end: str) -> tuple[list[str], bool]:
    """Return sorted category rule names for the period, capped; truncated if more exist."""
    names: set[str] = set()
    token = None
    while True:
        # Do not pass MaxResults without SortBy — CE returns ValidationException:
        # "MaxResult parameter is not supported if you don't want to get sorted result".
        kwargs: dict = {"TimePeriod": {"Start": start, "End": end}}
        if token:
            kwargs["NextPageToken"] = token
        resp = ce.get_cost_categories(**kwargs)
        for n in resp.get("CostCategoryNames") or []:
            if n:
                names.add(n)
        token = resp.get("NextPageToken")
        if not token:
            break
    sorted_names = sorted(names)
    if len(sorted_names) <= _MAX_COST_CATEGORIES_PER_REQUEST:
        return sorted_names, False
    return sorted_names[:_MAX_COST_CATEGORIES_PER_REQUEST], True


def _fetch_cost_category_usage(ce, start: str, end: str, category_name: str) -> dict[str, Decimal]:
    """Aggregate UnblendedCost by cost category dimension value."""
    totals: dict[str, Decimal] = {}
    token = None
    while True:
        kwargs = {
            "TimePeriod": {"Start": start, "End": end},
            "Granularity": "MONTHLY",
            "Metrics": ["UnblendedCost"],
            "GroupBy": [{"Type": "COST_CATEGORY", "Key": category_name}],
        }
        if token:
            kwargs["NextPageToken"] = token
        resp = ce.get_cost_and_usage(**kwargs)
        for result in resp.get("ResultsByTime", []):
            for group in result.get("Groups", []):
                keys = group.get("Keys", [])
                metrics = group.get("Metrics", {})
                value_key = keys[0] if keys else ""
                amt = Decimal(metrics.get("UnblendedCost", {}).get("Amount", "0") or "0")
                totals[value_key] = totals.get(value_key, Decimal("0")) + amt
        token = resp.get("NextPageToken")
        if not token:
            break
    return totals


def _build_category_payload(
    *,
    name: str,
    value_to_cost: dict[str, Decimal],
) -> dict:
    """Build one category object with rows, total, and coverage."""
    total = sum(value_to_cost.values(), Decimal("0"))
    rows_out: list[dict] = []
    for value_key, cost in sorted(value_to_cost.items(), key=lambda x: x[1], reverse=True):
        pct = (float(cost) / float(total) * 100.0) if total > 0 else 0.0
        rows_out.append(
            {
                "value_key": value_key,
                "cost": float(cost),
                "pct_of_category_total": round(pct, 4),
            }
        )
    uncategorized = sum(
        (amt for vk, amt in value_to_cost.items() if _is_uncategorized_cost_category_value(vk)),
        Decimal("0"),
    )
    categorized = total - uncategorized
    if uncategorized == 0 or total == 0:
        coverage_pct = 100.0
    else:
        coverage_pct = round(float(categorized) / float(total) * 100.0, 4)
    return {
        "name": name,
        "total_cost": float(total),
        "rows": rows_out,
        "coverage": {
            "categorized_cost": float(categorized),
            "uncategorized_cost": float(uncategorized),
            "coverage_pct": coverage_pct,
        },
    }


def get_cost_categories_dashboard(
    session: boto3.Session,
    *,
    start: str | None = None,
    end: str | None = None,
) -> dict:
    """
    Return MTD cost-categories breakdown for the hosted dashboard.

    Uses GetCostCategories for rule names, then GetCostAndUsage grouped by COST_CATEGORY
    per name. Raises CostExplorerError on permission/API failures.
    """
    if start is None or end is None:
        start, end = _current_month_range()
    ce = session.client("ce")
    try:
        names, truncated = _list_cost_category_names(ce, start, end)
    except ClientError as e:
        raise _client_error_to_cost_explorer(e, operation="GetCostCategories") from e

    categories: list[dict] = []
    for name in names:
        try:
            value_to_cost = _fetch_cost_category_usage(ce, start, end, name)
        except ClientError as e:
            raise _client_error_to_cost_explorer(
                e,
                operation="GetCostAndUsage (cost categories)",
            ) from e
        categories.append(_build_category_payload(name=name, value_to_cost=value_to_cost))

    out: dict = {
        "period": {"start": start, "end": end},
        "categories": categories,
    }
    if truncated:
        out["truncated"] = True
    return out


# GetSavingsPlansPurchaseRecommendation: one type/term/payment per call; full matrix covers
# all supported SavingsPlansType values (incl. DATABASE_SP) × terms × upfront payment options.
_SAVINGS_PLANS_PURCHASE_TYPES = (
    "COMPUTE_SP",
    "EC2_INSTANCE_SP",
    "SAGEMAKER_SP",
    "DATABASE_SP",
)
_TERM_IN_YEARS_SP_PURCHASE = ("ONE_YEAR", "THREE_YEARS")
_PAYMENT_OPTIONS_SP_PURCHASE = ("NO_UPFRONT", "PARTIAL_UPFRONT", "ALL_UPFRONT")
# Cost Explorer GetSavingsPlansPurchaseRecommendation — botocore enum (no NINETY_DAYS).
_LOOKBACK_SP_PURCHASE_ALLOWED = ("SEVEN_DAYS", "THIRTY_DAYS", "SIXTY_DAYS")


def _sp_purchase_float(val: object) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _sp_purchase_detail_to_row(
    d: dict,
    *,
    sp_type: str,
    term: str,
    payment: str,
) -> dict:
    svd = d.get("SavingsPlansDetails") or {}
    return {
        "savings_plans_type": sp_type,
        "term_in_years": term,
        "payment_option": payment,
        "account_id": d.get("AccountId") or None,
        "hourly_commitment_to_purchase": _sp_purchase_float(d.get("HourlyCommitmentToPurchase")),
        "estimated_monthly_savings_amount": _sp_purchase_float(
            d.get("EstimatedMonthlySavingsAmount")
        ),
        "estimated_savings_amount": _sp_purchase_float(d.get("EstimatedSavingsAmount")),
        "estimated_savings_percentage": _sp_purchase_float(d.get("EstimatedSavingsPercentage")),
        "estimated_roi": _sp_purchase_float(d.get("EstimatedROI")),
        "estimated_average_utilization": _sp_purchase_float(d.get("EstimatedAverageUtilization")),
        "estimated_sp_cost": _sp_purchase_float(d.get("EstimatedSPCost")),
        "currency_code": d.get("CurrencyCode"),
        "region": svd.get("Region"),
        "instance_family": svd.get("InstanceFamily"),
        "recommendation_detail_id": d.get("RecommendationDetailId"),
    }


def _sp_purchase_summary_has_data(summary: dict) -> bool:
    if not summary:
        return False
    cnt = summary.get("TotalRecommendationCount")
    if cnt not in (None, "", "0"):
        return True
    return any(
        summary.get(k) not in (None, "")
        for k in (
            "HourlyCommitmentToPurchase",
            "EstimatedMonthlySavingsAmount",
            "EstimatedSavingsAmount",
        )
    )


def _sp_purchase_summary_to_row(
    summary: dict,
    *,
    sp_type: str,
    term: str,
    payment: str,
) -> dict:
    return {
        "savings_plans_type": sp_type,
        "term_in_years": term,
        "payment_option": payment,
        "account_id": None,
        "hourly_commitment_to_purchase": _sp_purchase_float(
            summary.get("HourlyCommitmentToPurchase")
        ),
        "estimated_monthly_savings_amount": _sp_purchase_float(
            summary.get("EstimatedMonthlySavingsAmount")
        ),
        "estimated_savings_amount": _sp_purchase_float(summary.get("EstimatedSavingsAmount")),
        "estimated_savings_percentage": _sp_purchase_float(
            summary.get("EstimatedSavingsPercentage")
        ),
        "estimated_roi": _sp_purchase_float(summary.get("EstimatedROI")),
        "estimated_average_utilization": None,
        "estimated_sp_cost": _sp_purchase_float(summary.get("EstimatedTotalCost")),
        "currency_code": summary.get("CurrencyCode"),
        "region": None,
        "instance_family": None,
        "recommendation_detail_id": None,
        "aggregate_summary": True,
    }


def _fetch_savings_plans_purchase_one_cell(
    ce,
    *,
    sp_type: str,
    term: str,
    payment: str,
    account_scope: str,
    lookback_period_in_days: str,
) -> list[dict]:
    """Paginated GetSavingsPlansPurchaseRecommendation for one (type, term, payment)."""
    rows_out: list[dict] = []
    token = None
    while True:
        kwargs: dict = {
            "SavingsPlansType": sp_type,
            "TermInYears": term,
            "PaymentOption": payment,
            "LookbackPeriodInDays": lookback_period_in_days,
            "AccountScope": account_scope,
        }
        if token:
            kwargs["NextPageToken"] = token
        resp = ce.get_savings_plans_purchase_recommendation(**kwargs)
        spr = resp.get("SavingsPlansPurchaseRecommendation") or {}
        details = spr.get("SavingsPlansPurchaseRecommendationDetails") or []
        summary = spr.get("SavingsPlansPurchaseRecommendationSummary") or {}
        if details:
            for d in details:
                rows_out.append(
                    _sp_purchase_detail_to_row(d, sp_type=sp_type, term=term, payment=payment)
                )
        elif _sp_purchase_summary_has_data(summary):
            rows_out.append(
                _sp_purchase_summary_to_row(summary, sp_type=sp_type, term=term, payment=payment)
            )
        token = resp.get("NextPageToken")
        if not token:
            break
    return rows_out


def get_savings_plans_purchase_recommendations_dashboard(
    session: boto3.Session,
    *,
    account_scope: str = "PAYER",
    lookback_period_in_days: str = "THIRTY_DAYS",
    term_in_years: str | None = None,
    payment_option: str | None = None,
) -> dict:
    """
    Call GetSavingsPlansPurchaseRecommendation for the parameter matrix (no region Filter;
    AccountScope from ``account_scope`` — use PAYER for payer-wide or LINKED for the current
    account).

    ``lookback_period_in_days`` must be one of ``_LOOKBACK_SP_PURCHASE_ALLOWED`` (AWS documents
    SEVEN_DAYS, THIRTY_DAYS, SIXTY_DAYS for this API).

    When ``term_in_years`` and ``payment_option`` are both set, only that term × payment is
    combined with all ``SavingsPlansType`` values (4 API calls). When both are omitted, the full
    matrix is used (all terms × all payments × all types). If only one of the two is set,
    raises ``ValueError``.

    Merges rows from all cells; records per-cell errors without failing the whole request unless
    every cell is access-denied.

    Raises CostExplorerError if all matrix calls fail with access denied and no rows were built.
    """
    if lookback_period_in_days not in _LOOKBACK_SP_PURCHASE_ALLOWED:
        raise ValueError(
            f"Invalid lookback_period_in_days {lookback_period_in_days!r}; "
            f"expected one of {_LOOKBACK_SP_PURCHASE_ALLOWED}"
        )
    if (term_in_years is None) ^ (payment_option is None):
        raise ValueError("term_in_years and payment_option must both be set or both omitted")
    if term_in_years is not None:
        if term_in_years not in _TERM_IN_YEARS_SP_PURCHASE:
            raise ValueError(
                f"Invalid term_in_years {term_in_years!r}; "
                f"expected one of {_TERM_IN_YEARS_SP_PURCHASE}"
            )
        if payment_option not in _PAYMENT_OPTIONS_SP_PURCHASE:
            raise ValueError(
                f"Invalid payment_option {payment_option!r}; "
                f"expected one of {_PAYMENT_OPTIONS_SP_PURCHASE}"
            )
        terms_iter: tuple[str, ...] = (term_in_years,)
        payments_iter: tuple[str, ...] = (payment_option,)
    else:
        terms_iter = _TERM_IN_YEARS_SP_PURCHASE
        payments_iter = _PAYMENT_OPTIONS_SP_PURCHASE

    ce = session.client("ce")
    recommendations: list[dict] = []
    errors: list[dict] = []
    access_denied_cells = 0
    matrix_cells = 0

    for sp_type, term, payment in product(
        _SAVINGS_PLANS_PURCHASE_TYPES,
        terms_iter,
        payments_iter,
    ):
        matrix_cells += 1
        try:
            recommendations.extend(
                _fetch_savings_plans_purchase_one_cell(
                    ce,
                    sp_type=sp_type,
                    term=term,
                    payment=payment,
                    account_scope=account_scope,
                    lookback_period_in_days=lookback_period_in_days,
                )
            )
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            msg = e.response.get("Error", {}).get("Message", str(e))
            if code == "AccessDeniedException":
                access_denied_cells += 1
            errors.append(
                {
                    "savings_plans_type": sp_type,
                    "term_in_years": term,
                    "payment_option": payment,
                    "error_code": code,
                    "message": msg,
                }
            )
            logger.debug(
                "GetSavingsPlansPurchaseRecommendation failed for %s/%s/%s: %s",
                sp_type,
                term,
                payment,
                code,
            )

    if not recommendations and access_denied_cells == matrix_cells and matrix_cells > 0:
        raise CostExplorerError(
            "Access denied to Cost Explorer (GetSavingsPlansPurchaseRecommendation). "
            "Ensure your credentials have ce:GetSavingsPlansPurchaseRecommendation."
        )

    out: dict = {
        "lookback_period_in_days": lookback_period_in_days,
        "account_scope": account_scope,
        "matrix_term_in_years": term_in_years,
        "matrix_payment_option": payment_option,
        "recommendations": recommendations,
    }
    if errors:
        out["errors"] = errors
    return out
