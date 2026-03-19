"""Cost optimization recommendations and cost anomalies for the dashboard."""

from __future__ import annotations

from datetime import date, timedelta

import boto3
from botocore.exceptions import ClientError


def get_optimization_recommendations_top10(
    session: boto3.Session,
    *,
    max_items: int = 10,
) -> list[dict]:
    """
    Fetch cost optimization recommendations from Cost Optimization Hub, sorted by
    estimated savings, returning the top max_items (default 10).
    On access denied or API error, returns an empty list without raising.
    """
    try:
        client = session.client("cost-optimization-hub")
        all_items: list[dict] = []
        token = None
        while True:
            kwargs = {"includeAllRecommendations": False, "maxResults": 100}
            if token:
                kwargs["nextToken"] = token
            resp = client.list_recommendations(**kwargs)
            all_items.extend(resp.get("items", []))
            token = resp.get("nextToken")
            if not token:
                break

        # Sort by estimated monthly savings descending (handle missing/zero)
        def savings_key(item: dict) -> float:
            est = item.get("estimatedMonthlySavings") or "0"
            if isinstance(est, str):
                try:
                    return float(est)
                except ValueError:
                    return 0.0
            return float(est)

        all_items.sort(key=savings_key, reverse=True)
        top = all_items[:max_items]
        # Return full item from AWS so the UI can show or use any field
        # (recommendationId, accountId, region, resourceId, resourceArn, actionType,
        #  estimatedMonthlySavings, currentResourceSummary, tags, etc.)
        return list(top)
    except ClientError:
        return []
    except Exception:
        return []


def get_anomalies_last_3_days(session: boto3.Session) -> list[dict]:
    """
    Fetch cost anomalies detected in the last 3 days via Cost Explorer GetAnomalies.
    Returns list of anomaly objects (anomalyId, dateInterval, impact, etc.).
    On access denied or no data, returns an empty list without raising.
    """
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=3)
        ce = session.client("ce")
        anomalies: list[dict] = []
        token = None
        while True:
            kwargs = {
                "DateInterval": {
                    "StartDate": start_date.isoformat(),
                    "EndDate": end_date.isoformat(),
                },
                "MaxResults": 20,
            }
            if token:
                kwargs["NextPageToken"] = token
            resp = ce.get_anomalies(**kwargs)
            anomalies.extend(resp.get("Anomalies", []))
            token = resp.get("NextPageToken")
            if not token:
                break
        # Normalize for API: id, date range, impact. AWS uses AnomalyStartDate/AnomalyEndDate.
        return [
            {
                "anomalyId": a.get("AnomalyId", ""),
                "anomalyScore": a.get("AnomalyScore"),
                "impact": a.get("Impact", {}),
                "startDate": a.get("AnomalyStartDate"),
                "endDate": a.get("AnomalyEndDate"),
                "dimensionValue": a.get("DimensionValue"),
            }
            for a in anomalies
        ]
    except ClientError:
        return []
    except Exception:
        return []
